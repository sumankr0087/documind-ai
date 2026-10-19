"""Question answering RAG endpoint."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.config import Settings, get_settings
from app.dependencies import get_retriever_service, get_llm_service
from app.models.question import QuestionRequest, QuestionResponse
from app.services.retriever import RetrieverService, DocumentNotFoundError
from app.services.llm import LLMService

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
) -> QuestionResponse:
    """Answer questions grounded in ingested document chunks with source citations."""
    top_k = payload.top_k or settings.top_k

    # 1. Retrieve relevant chunks
    try:
        chunks = retriever.retrieve(
            question=payload.question,
            top_k=top_k,
            document_id=payload.document_id,
        )
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error("Retrieval failed for question '%s': %s", payload.question, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred during retrieval: {e}",
        ) from e

    # 2. Generate grounded answer and citations via LLM
    try:
        answer, citations, evidence_sufficient, model_used = await llm_service.generate_answer(
            question=payload.question,
            chunks=chunks,
        )
    except Exception as e:
        logger.error("Answer generation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM generation failed: {e}",
        ) from e

    return QuestionResponse(
        question=payload.question,
        answer=answer,
        citations=citations,
        evidence_sufficient=evidence_sufficient,
        document_id=payload.document_id,
        model_used=model_used,
    )
