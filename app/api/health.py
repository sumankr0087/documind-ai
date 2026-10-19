"""Health check API endpoint."""
from fastapi import APIRouter, Depends
from app.config import Settings, get_settings
from app.models.health import HealthResponse
from app.services.vector_store import VectorStoreService
from app.dependencies import get_vector_store

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Service Health and Status")
def health_check(
    settings: Settings = Depends(get_settings),
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> HealthResponse:
    """Return system health, deployment environment, and status of vector store and embedding engines."""
    try:
        chunk_count = vector_store.count()
        vector_store_status = "connected"
    except Exception as e:
        chunk_count = 0
        vector_store_status = f"degraded: {e}"

    llm_configured = bool(settings.openai_api_key and not settings.openai_api_key.startswith("your_")) or (settings.llm_provider == "mock")

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        app_env=settings.app_env,
        services={
            "vector_store": {
                "status": vector_store_status,
                "collection": settings.chroma_collection_name,
                "total_chunks": chunk_count,
            },
            "embedding": {
                "model": settings.embedding_model_name,
                "device": settings.embedding_device,
            },
            "llm": {
                "provider": settings.llm_provider,
                "model": settings.llm_model,
                "configured": llm_configured,
            },
        },
    )
