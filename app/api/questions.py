"""Question answering RAG endpoints supporting synchronous, streaming, multi-document, and hybrid search."""
import json
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.config import Settings, get_settings
from app.dependencies import get_llm_service, get_retriever_service, get_sqlite_store
from app.models.question import QuestionRequest, QuestionResponse
from app.services.llm import LLMService
from app.services.retriever import DocumentNotFoundError, RetrieverService
from app.services.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["Question Answering"])


@router.post(
    "/ask",
    response_model=QuestionResponse,
    summary="Ask a question against indexed documents",
)
async def ask_question(
    payload: QuestionRequest,
    settings: Settings = Depends(get_settings),
    retriever: RetrieverService = Depends(get_retriever_service),
    llm_service: LLMService = Depends(get_llm_service),
    sqlite_store: SQLiteStore = Depends(get_sqlite_store),
) -> QuestionResponse:
    """Answer questions grounded in ingested document chunks with source citations and conversation context."""
    top_k = payload.top_k or settings.top_k
    enable_mmr = payload.enable_mmr if payload.enable_mmr is not None else settings.enable_mmr
    enable_hybrid = payload.enable_hybrid if payload.enable_hybrid is not None else settings.enable_hybrid_search
    enable_rerank = payload.enable_reranking if payload.enable_reranking is not None else settings.enable_reranking

    # 1. Fetch recent conversation context from SQLite if session provided
    recent_history = None
    if payload.session_id:
        recent_history = sqlite_store.get_recent_context(payload.session_id, max_turns=5)

    # 2. Retrieve relevant chunks
    try:
        chunks = retriever.retrieve(
            question=payload.question,
            top_k=top_k,
            document_id=payload.document_id,
            document_ids=payload.document_ids,
            file_extensions=payload.file_extensions,
            enable_mmr=enable_mmr,
            mmr_lambda=settings.mmr_lambda,
            enable_hybrid=enable_hybrid,
            hybrid_dense_weight=settings.hybrid_dense_weight,
            hybrid_bm25_weight=settings.hybrid_bm25_weight,
            enable_reranking=enable_rerank,
        )
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error("Retrieval failed for question '%s': %s", payload.question, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred during retrieval: {e}",
        ) from e

    # 3. Generate grounded answer and citations via LLM
    try:
        answer, citations, evidence_sufficient, model_used = await llm_service.generate_answer(
            question=payload.question,
            chunks=chunks,
            recent_history=recent_history,
        )
    except Exception as e:
        logger.error("Answer generation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM generation failed: {e}",
        ) from e

    # 4. Save dialogue to SQLite if in a session
    if payload.session_id:
        sqlite_store.add_message(payload.session_id, "user", payload.question)
        sqlite_store.add_message(
            payload.session_id,
            "assistant",
            answer,
            citations=[c.model_dump() for c in citations] if citations else None,
        )

    return QuestionResponse(
        question=payload.question,
        answer=answer,
        citations=citations,
        evidence_sufficient=evidence_sufficient,
        document_id=payload.document_id,
        document_ids=payload.document_ids,
        session_id=payload.session_id,
        model_used=model_used,
    )


@router.post(
    "/ask-stream",
    summary="Ask a question and receive real-time streamed answer tokens via SSE",
)
async def ask_question_stream(
    payload: QuestionRequest,
    settings: Settings = Depends(get_settings),
    retriever: RetrieverService = Depends(get_retriever_service),
    llm_service: LLMService = Depends(get_llm_service),
    sqlite_store: SQLiteStore = Depends(get_sqlite_store),
):
    """Stream answer generation in real time using Server-Sent Events (SSE)."""
    top_k = payload.top_k or settings.top_k
    enable_mmr = payload.enable_mmr if payload.enable_mmr is not None else settings.enable_mmr
    enable_hybrid = payload.enable_hybrid if payload.enable_hybrid is not None else settings.enable_hybrid_search
    enable_rerank = payload.enable_reranking if payload.enable_reranking is not None else settings.enable_reranking

    # 1. Fetch recent conversation context from SQLite
    recent_history = None
    if payload.session_id:
        recent_history = sqlite_store.get_recent_context(payload.session_id, max_turns=5)

    # 2. Retrieve relevant chunks
    try:
        chunks = retriever.retrieve(
            question=payload.question,
            top_k=top_k,
            document_id=payload.document_id,
            document_ids=payload.document_ids,
            file_extensions=payload.file_extensions,
            enable_mmr=enable_mmr,
            mmr_lambda=settings.mmr_lambda,
            enable_hybrid=enable_hybrid,
            hybrid_dense_weight=settings.hybrid_dense_weight,
            hybrid_bm25_weight=settings.hybrid_bm25_weight,
            enable_reranking=enable_rerank,
        )
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error("Retrieval failed during streaming for '%s': %s", payload.question, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval error: {e}",
        ) from e

    # Record user message in SQLite immediately
    if payload.session_id:
        sqlite_store.add_message(payload.session_id, "user", payload.question)

    async def event_generator() -> AsyncGenerator[str, None]:
        full_answer = []
        final_citations = []

        try:
            async for event in llm_service.generate_answer_stream(
                question=payload.question,
                chunks=chunks,
                recent_history=recent_history,
            ):
                if event["type"] == "token":
                    full_answer.append(event["delta"])
                elif event["type"] == "done":
                    final_citations = event.get("citations", [])

                yield f"data: {json.dumps(event)}\n\n"

            # Save assistant answer to SQLite once completed
            if payload.session_id and full_answer:
                sqlite_store.add_message(
                    payload.session_id,
                    "assistant",
                    "".join(full_answer).strip(),
                    citations=final_citations,
                )

        except Exception as e:
            logger.error("SSE stream error: %s", e)
            error_data = json.dumps({"type": "error", "detail": str(e)})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
