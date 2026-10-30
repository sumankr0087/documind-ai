"""FastAPI Application entrypoint for DocuMind AI."""
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.questions import router as questions_router
from app.api.chat import router as chat_router
from app.config import get_settings
from app.dependencies import get_bm25_service, get_sqlite_store, get_vector_store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("documind")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: initialize storage directories, SQLite, and BM25 index on startup."""
    settings = get_settings()
    settings.ensure_directories()
    # Initialize SQLite Store
    get_sqlite_store(settings)
    # Warm up BM25 keyword index from stored chunks
    vstore = get_vector_store(settings)
    get_bm25_service(vstore)
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
app.include_router(chat_router)


# Mount static frontend build if it exists
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    if (frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/ui", summary="DocuMind AI Web UI", include_in_schema=False)
    @app.get("/app", include_in_schema=False)
    def serve_frontend_ui():
        """Serve the compiled React frontend application."""
        return FileResponse(frontend_dist / "index.html")


@app.get("/", summary="Root index", include_in_schema=False)
def root_redirect(request: Request):
    """Return React UI if requested by browser, or API service JSON for API clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and frontend_dist.exists():
        from fastapi.responses import FileResponse
        return FileResponse(frontend_dist / "index.html")

    return JSONResponse(
        content={
            "service": "DocuMind AI",
            "version": "1.0.0",
            "ui": "/ui",
            "documentation": "/docs",
            "health": "/health",
            "description": "Visit /ui for the Web Studio or /docs for interactive OpenAPI documentation.",
        }
    )


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
