"""Chat session and conversation topic management API endpoints."""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_sqlite_store
from app.models.chat import (
    ChatMessageModel,
    ChatSessionDetailResponse,
    ChatSessionListResponse,
    ChatSessionModel,
    CreateSessionRequest,
)
from app.services.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat Topics"])


@router.get(
    "/sessions",
    response_model=ChatSessionListResponse,
    summary="List all chat session topics",
)
def list_sessions(
    sqlite_store: SQLiteStore = Depends(get_sqlite_store),
) -> ChatSessionListResponse:
    """Retrieve all chat sessions sorted by recent activity."""
    sessions = sqlite_store.list_sessions()
    session_models = [ChatSessionModel(**s) for s in sessions]
    return ChatSessionListResponse(total_sessions=len(session_models), sessions=session_models)


@router.post(
    "/sessions",
    response_model=ChatSessionModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session topic",
)
def create_session(
    payload: CreateSessionRequest,
    sqlite_store: SQLiteStore = Depends(get_sqlite_store),
) -> ChatSessionModel:
    """Create a new conversational topic thread."""
    session = sqlite_store.create_session(title=payload.title or "New Chat")
    return ChatSessionModel(**session)


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionDetailResponse,
    summary="Get chat topic details and message history",
)
def get_session(
    session_id: str,
    sqlite_store: SQLiteStore = Depends(get_sqlite_store),
) -> ChatSessionDetailResponse:
    """Load a chat session topic and its chronological message history."""
    session = sqlite_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{session_id}' not found.",
        )

    raw_messages = sqlite_store.get_session_messages(session_id)
    messages = [ChatMessageModel(**m) for m in raw_messages]

    return ChatSessionDetailResponse(
        session=ChatSessionModel(**session),
        messages=messages,
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a chat session topic",
)
def delete_session(
    session_id: str,
    sqlite_store: SQLiteStore = Depends(get_sqlite_store),
):
    """Delete a chat session topic and all its saved messages."""
    session = sqlite_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{session_id}' not found.",
        )

    sqlite_store.delete_session(session_id)
    return {"message": f"Chat session '{session_id}' successfully deleted.", "session_id": session_id}
