"""Health check response models."""
from typing import Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(default="healthy", description="Overall health status")
    version: str = Field(default="1.0.0", description="Application version")
    app_env: str = Field(default="development", description="Current deployment environment")
    services: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed status of dependent subsystems (vector store, embedding, llm)",
    )
