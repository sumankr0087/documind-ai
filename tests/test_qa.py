"""Automated tests for Q&A, source citations, missing evidence, and LLM failures."""
import io
from unittest.mock import AsyncMock, patch
from app.dependencies import get_llm_service
from app.main import app
from app.services.llm import LLMService


def test_question_answering_with_citations(test_client, sample_pdf_bytes):
    """Test grounded answer generation with citations, filenames, page numbers, and chunk IDs."""
    # Upload PDF
    files = {"file": ("architecture_guide.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    upload_res = test_client.post("/documents/upload", files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document"]["document_id"]

    # Ask grounded question
    ask_res = test_client.post(
        "/questions/ask",
        json={
            "question": "What tools does DocuMind AI use for PDF extraction and embeddings?",
            "document_id": doc_id,
        },
    )
    assert ask_res.status_code == 200
    data = ask_res.json()

    assert data["evidence_sufficient"] is True
    assert len(data["answer"]) > 0
    assert len(data["citations"]) > 0

    # Verify citation attributes
    first_citation = data["citations"][0]
    assert first_citation["filename"] == "architecture_guide.pdf"
    assert first_citation["page_number"] in (1, 2)
    assert "chunk_id" in first_citation
    assert "snippet" in first_citation
    assert "relevance_score" in first_citation


def test_missing_evidence_handling(test_client, sample_pdf_bytes):
    """Test that unrelated questions correctly report insufficient evidence."""
    # Upload PDF about DocuMind AI
    files = {"file": ("manual.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    test_client.post("/documents/upload", files=files)

    # Ask question completely outside the scope of the document
    res = test_client.post(
        "/questions/ask",
        json={"question": "What is the boiling point of liquid nitrogen at standard pressure in Mars atmosphere?"},
    )
    assert res.status_code == 200
    data = res.json()

    # System should state insufficient evidence
    assert data["evidence_sufficient"] is False
    assert "insufficient evidence" in data["answer"].lower()
    assert len(data["citations"]) == 0


def test_llm_failure_handling(test_client, sample_txt_bytes):
    """Test that LLM provider failure returns 502 Bad Gateway."""
    # Upload document
    files = {"file": ("data.txt", io.BytesIO(sample_txt_bytes), "text/plain")}
    test_client.post("/documents/upload", files=files)

    # Mock LLMService to simulate API failure
    class FailingLLMService(LLMService):
        def __init__(self):
            pass

        async def generate_answer(self, question, chunks):
            raise RuntimeError("Upstream LLM Provider timed out or authentication failed")

    app.dependency_overrides[get_llm_service] = lambda: FailingLLMService()

    try:
        res = test_client.post(
            "/questions/ask",
            json={"question": "What is DocuMind AI?"},
        )
        assert res.status_code == 502
        assert "LLM generation failed" in res.json()["detail"]
    finally:
        if get_llm_service in app.dependency_overrides:
            del app.dependency_overrides[get_llm_service]
