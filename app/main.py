"""FastAPI Application entrypoint for DocuMind AI."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.questions import router as questions_router
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("documind")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: initialize storage directories on startup."""
    settings = get_settings()
    settings.ensure_directories()
    logger.info("DocuMind AI started successfully in '%s' environment", settings.app_env)
    yield
    logger.info("DocuMind AI shutting down")


app = FastAPI(
    title="DocuMind AI - Intelligent Document RAG Engine",
    description=(
        "Production-grade Retrieval-Augmented Generation (RAG) API for document Q&A. "
        "Supports PDF (PyMuPDF), Markdown, and TXT parsing, semantic chunking, "
        "Sentence Transformers embeddings, ChromaDB vector indexing, and grounded LLM answers with citations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Enable CORS for cross-origin browser clients and dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(questions_router)


@app.get("/", summary="Root index", include_in_schema=False)
def root_redirect():
    """Return welcome message and documentation link."""
    return JSONResponse(
        content={
            "service": "DocuMind AI",
            "version": "1.0.0",
            "documentation": "/docs",
            "health": "/health",
            "description": "Visit /docs for interactive OpenAPI documentation and API testing.",
        }
    )


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
