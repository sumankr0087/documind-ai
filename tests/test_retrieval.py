"""Automated tests for retrieval service and document filtering."""
import io
import pytest
from app.services.retriever import DocumentNotFoundError


def test_retrieval_and_filtering(test_client, sample_pdf_bytes, sample_txt_bytes):
    """Test semantic retrieval and document-scoped filtering."""
    # Upload Document 1 (PDF)
    res1 = test_client.post(
        "/documents/upload",
        files={"file": ("doc_pdf.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    doc_id_pdf = res1.json()["document"]["document_id"]

    # Upload Document 2 (TXT)
    res2 = test_client.post(
        "/documents/upload",
        files={"file": ("doc_txt.txt", io.BytesIO(sample_txt_bytes), "text/plain")},
    )
    doc_id_txt = res2.json()["document"]["document_id"]

    # 1. Ask a question without filter -> should retrieve relevant chunks
    ask_all = test_client.post(
        "/questions/ask",
        json={"question": "How does Sentence Transformers create embeddings?", "top_k": 5},
    )
    assert ask_all.status_code == 200
    all_data = ask_all.json()
    assert len(all_data["citations"]) > 0

    # 2. Ask question scoped strictly to PDF document
    ask_scoped_pdf = test_client.post(
        "/questions/ask",
        json={
            "question": "What is the deployment method used?",
            "document_id": doc_id_pdf,
            "top_k": 3,
        },
    )
    assert ask_scoped_pdf.status_code == 200
    scoped_data = ask_scoped_pdf.json()
    assert scoped_data["document_id"] == doc_id_pdf
    for citation in scoped_data["citations"]:
        assert citation["document_id"] == doc_id_pdf
        assert citation["filename"] == "doc_pdf.pdf"

    # 3. Ask question scoped strictly to TXT document
    ask_scoped_txt = test_client.post(
        "/questions/ask",
        json={
            "question": "What does cosine similarity measure?",
            "document_id": doc_id_txt,
            "top_k": 3,
        },
    )
    assert ask_scoped_txt.status_code == 200
    scoped_txt_data = ask_scoped_txt.json()
    for citation in scoped_txt_data["citations"]:
        assert citation["document_id"] == doc_id_txt
        assert citation["filename"] == "doc_txt.txt"


def test_retrieval_with_nonexistent_document_filter(test_client):
    """Test that filtering on nonexistent document ID returns 404."""
    response = test_client.post(
        "/questions/ask",
        json={
            "question": "Any question here?",
            "document_id": "nonexistent-doc-id-0000",
        },
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
