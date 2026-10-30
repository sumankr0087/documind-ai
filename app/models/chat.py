"""Chat session and message data models."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.question import Citation


class CreateSessionRequest(BaseModel):
    """Payload to create a new chat session topic."""

    title: Optional[str] = Field("New Chat", max_length=120, description="Chat topic title")


class ChatSessionModel(BaseModel):
    """Metadata for a chat session / topic."""

    session_id: str = Field(..., description="Unique UUID for chat session")
    title: str = Field(..., description="Topic title")
    created_at: str = Field(..., description="ISO creation timestamp")
    updated_at: str = Field(..., description="ISO last activity timestamp")
    message_count: int = Field(0, description="Total messages in this topic")


class ChatMessageModel(BaseModel):
    """Individual message in a chat topic."""

    message_id: str = Field(..., description="Unique message UUID")
    session_id: str = Field(..., description="Associated chat session ID")
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text content")
    citations: List[Citation] = Field(default_factory=list, description="Evidence citations for assistant answers")
    created_at: str = Field(..., description="ISO timestamp")


class ChatSessionDetailResponse(BaseModel):
    """Complete session details including historical messages."""

    session: ChatSessionModel
    messages: List[ChatMessageModel] = Field(default_factory=list)


class ChatSessionListResponse(BaseModel):
    """List of all chat session topics."""

    total_sessions: int
    sessions: List[ChatSessionModel]
