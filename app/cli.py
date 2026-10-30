"""DocuMind AI Command-Line Interface (CLI).

Supports:
- Asking questions with streaming answers
- Multi-document filtering (--doc-ids)
- File extension filtering (--extension)
- Semantic MMR, Hybrid search, and Cross-Encoder flags
- Interactive terminal chat sessions with topic persistence
- Uploading and listing documents
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional

from app.config import get_settings
from app.dependencies import (
    get_bm25_service,
    get_chunker,
    get_embedding_service,
    get_llm_service,
    get_reranker_service,
    get_retriever_service,
    get_sqlite_store,
    get_vector_store,
)
from app.models.document import DocumentMetadata
from app.services.parser import DocumentParser


def _init_services():
    """Initialize application services locally for CLI execution."""
    settings = get_settings()
    settings.ensure_directories()
    sqlite_store = get_sqlite_store(settings)
    vector_store = get_vector_store(settings)
    bm25_service = get_bm25_service(vector_store)
    embedding_service = get_embedding_service(settings)
    reranker = get_reranker_service(settings)
    retriever = get_retriever_service(
        embedding_service=embedding_service,
        vector_store=vector_store,
        bm25_service=bm25_service,
        reranker=reranker,
    )
    llm = get_llm_service(settings)
    chunker = get_chunker(settings)
    return settings, sqlite_store, vector_store, bm25_service, embedding_service, retriever, llm, chunker


def cli_list():
    """List all indexed documents."""
    _, _, vector_store, _, _, _, _, _ = _init_services()
    docs = vector_store.registry.list_documents()
    print("\n" + "=" * 70)
    print(f"INDEXED DOCUMENTS ({len(docs)} total):")
    print("=" * 70)
    if not docs:
        print("No documents indexed yet. Use 'python -m app.cli upload <file>' to upload.")
    for d in docs:
        ext = d.filename.split(".")[-1] if "." in d.filename else "unknown"
        print(f"• ID: {d.document_id}")
        print(f"  File: {d.filename} [{ext.upper()}] | {d.chunk_count} chunks | {d.size_bytes} bytes")
    print("=" * 70 + "\n")


def cli_upload(file_paths: List[str]):
    """Upload and index one or more documents from the command line with deduplication."""
    import hashlib
    import uuid

    settings, sqlite_store, vector_store, bm25_service, embedding_service, _, _, chunker = _init_services()

    print("\n" + "=" * 70)
    print(f"UPLOADING {len(file_paths)} FILE(S)...")
    print("=" * 70)

    for path_str in file_paths:
        p = Path(path_str)
        if not p.exists() or not p.is_file():
            print(f"✖ File not found: {path_str}")
            continue

        with open(p, "rb") as f:
            content = f.read()

        file_hash = hashlib.sha256(content).hexdigest()
        existing = sqlite_store.get_document_by_hash(file_hash)
        if existing:
            print(f"⚠ Skipping duplicate '{p.name}': exact content already indexed as document ID {existing['document_id']}.")
            continue

        try:
            parsed = DocumentParser.parse(content, p.name)
            doc_id = str(uuid.uuid4())
            chunks = chunker.chunk_document(doc_id, parsed)
            if not chunks:
                print(f"✖ No text chunks could be extracted from '{p.name}'.")
                continue

            chunk_texts = [c.text for c in chunks]
            embeddings = embedding_service.embed_documents(chunk_texts)
            vector_store.add_chunks(chunks, embeddings)
            bm25_service.add_chunks(
                [
                    {
                        "chunk_id": c.chunk_id,
                        "document_id": c.document_id,
                        "chunk_index": c.chunk_index,
                        "filename": c.filename,
                        "page_number": c.page_number,
                        "text": c.text,
                    }
                    for c in chunks
                ]
            )
            sqlite_store.register_document_hash(file_hash, doc_id, p.name)

            doc_metadata = DocumentMetadata(
                document_id=doc_id,
                filename=p.name,
                content_type=parsed.content_type,
                size_bytes=len(content),
                chunk_count=len(chunks),
                page_count=len(parsed.pages) if parsed.content_type == "application/pdf" else None,
                file_hash=file_hash,
            )
            vector_store.registry.register_document(doc_metadata)
            print(f"✓ Successfully indexed '{p.name}' ({len(chunks)} chunks, ID: {doc_id})")
        except Exception as e:
            print(f"✖ Error processing '{p.name}': {e}")

    print("=" * 70 + "\n")


async def cli_ask(
    question: str,
    doc_ids: Optional[List[str]] = None,
    extensions: Optional[List[str]] = None,
    enable_mmr: bool = True,
    enable_hybrid: bool = True,
    enable_rerank: bool = False,
    top_k: int = 5,
    session_id: Optional[str] = None,
    stream: bool = True,
):
    """Ask a question through the CLI and stream the response."""
    settings, sqlite_store, _, _, _, retriever, llm, _ = _init_services()

    recent_history = None
    if session_id:
        recent_history = sqlite_store.get_recent_context(session_id, max_turns=5)

    print(f"\nQuestion: {question}")
    if doc_ids:
        print(f"Filtered Documents: {', '.join(doc_ids)}")
    if extensions:
        print(f"Filtered Extensions: {', '.join(extensions)}")
    print("Retrieving context chunks...")

    chunks = retriever.retrieve(
        question=question,
        top_k=top_k,
        document_ids=doc_ids,
        file_extensions=extensions,
        enable_mmr=enable_mmr,
        enable_hybrid=enable_hybrid,
        enable_reranking=enable_rerank,
    )

    if not chunks:
        print("\n[!] No relevant document context found.")
        return

    print(f"Retrieved {len(chunks)} relevant chunks. Generating answer...\n")
    print("-" * 70)
    print("Answer: ", end="", flush=True)

    if session_id:
        sqlite_store.add_message(session_id, "user", question)

    full_answer = []
    final_citations = []

    if stream:
        async for event in llm.generate_answer_stream(
            question=question,
            chunks=chunks,
            recent_history=recent_history,
        ):
            if event["type"] == "token":
                print(event["delta"], end="", flush=True)
                full_answer.append(event["delta"])
            elif event["type"] == "done":
                final_citations = event.get("citations", [])
        print()
    else:
        answer, citations, evidence_sufficient, model_used = await llm.generate_answer(
            question=question,
            chunks=chunks,
            recent_history=recent_history,
        )
        print(answer)
        full_answer.append(answer)
        final_citations = [c.model_dump() for c in citations]

    print("-" * 70)

    if session_id and full_answer:
        sqlite_store.add_message(
            session_id,
            "assistant",
            "".join(full_answer).strip(),
            citations=final_citations,
        )

    if final_citations:
        print("\nEVIDENCE SOURCES & CITATIONS:")
        for i, cit in enumerate(final_citations, 1):
            pg = f" (Page {cit['page_number']})" if cit.get("page_number") else ""
            print(f" [{i}] {cit['filename']}{pg} | Chunk ID: {cit['chunk_id'][:8]}... | Score: {cit['relevance_score']:.2f}")
            print(f"     \"{cit['snippet'].replace(chr(10), ' ')[:140]}...\"\n")


def cli_interactive_chat(
    doc_ids: Optional[List[str]] = None,
    extensions: Optional[List[str]] = None,
    topic: Optional[str] = None,
):
    """Run an interactive conversational chat session in the terminal."""
    _, sqlite_store, _, _, _, _, _, _ = _init_services()

    session = sqlite_store.create_session(title=topic or "CLI Chat")
    session_id = session["session_id"]

    print("\n" + "=" * 70)
    print(f"DOCUMIND AI INTERACTIVE CLI CHAT")
    print(f"Topic: {session['title']} (Session ID: {session_id[:8]}...)")
    print("Type your question, or 'exit'/'quit' to finish.")
    print("=" * 70 + "\n")

    loop = asyncio.get_event_loop()

    while True:
        try:
            user_input = input("\nYou > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Ending chat session. Goodbye!")
                break

            loop.run_until_complete(
                cli_ask(
                    question=user_input,
                    doc_ids=doc_ids,
                    extensions=extensions,
                    session_id=session_id,
                    stream=True,
                )
            )
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat.")
            break


def main():
    parser = argparse.ArgumentParser(description="DocuMind AI CLI Tool")
    subparsers = parser.add_subparsers(dest="command")

    # 1. Ask
    ask_parser = subparsers.add_parser("ask", help="Ask a question")
    ask_parser.add_argument("question", type=str, help="Question to answer")
    ask_parser.add_argument("--doc-ids", type=str, default=None, help="Comma-separated document IDs to search")
    ask_parser.add_argument("--extension", type=str, default=None, help="Comma-separated extensions to filter (e.g. pdf,txt)")
    ask_parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve")
    ask_parser.add_argument("--hybrid", action="store_true", default=True, help="Enable hybrid dense + BM25 search")
    ask_parser.add_argument("--mmr", action="store_true", default=True, help="Enable MMR retrieval diversity")
    ask_parser.add_argument("--rerank", action="store_true", default=False, help="Enable cross-encoder reranking")
    ask_parser.add_argument("--no-stream", action="store_true", help="Disable streaming output")

    # 2. Chat
    chat_parser = subparsers.add_parser("chat", help="Start interactive terminal chat session")
    chat_parser.add_argument("--doc-ids", type=str, default=None, help="Comma-separated document IDs to search")
    chat_parser.add_argument("--extension", type=str, default=None, help="Comma-separated extensions to filter")
    chat_parser.add_argument("--topic", type=str, default=None, help="Chat topic title")

    # 3. Upload
    upload_parser = subparsers.add_parser("upload", help="Upload documents")
    upload_parser.add_argument("files", nargs="+", help="File paths to upload")

    # 4. List
    subparsers.add_parser("list", help="List all indexed documents")

    # 5. Eval
    subparsers.add_parser("eval", help="Run retrieval quality evaluations")

    args = parser.parse_args()

    if args.command == "list":
        cli_list()
    elif args.command == "upload":
        cli_upload(args.files)
    elif args.command == "ask":
        doc_ids = [d.strip() for d in args.doc_ids.split(",")] if args.doc_ids else None
        exts = [e.strip() for e in args.extension.split(",")] if args.extension else None
        asyncio.run(
            cli_ask(
                question=args.question,
                doc_ids=doc_ids,
                extensions=exts,
                enable_mmr=args.mmr,
                enable_hybrid=args.hybrid,
                enable_rerank=args.rerank,
                top_k=args.top_k,
                stream=not args.no_stream,
            )
        )
    elif args.command == "chat":
        doc_ids = [d.strip() for d in args.doc_ids.split(",")] if args.doc_ids else None
        exts = [e.strip() for e in args.extension.split(",")] if args.extension else None
        cli_interactive_chat(doc_ids=doc_ids, extensions=exts, topic=args.topic)
    elif args.command == "eval":
        from evals.run_evaluation import main as eval_main
        eval_main()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
