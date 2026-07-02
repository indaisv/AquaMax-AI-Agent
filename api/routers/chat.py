"""Chat API router for agent conversations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.dependencies import AgentDep

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: str | None = Field(None, description="Existing session ID (optional)")
    customer_info: dict | None = Field(None, description="Pre-filled customer information")


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    response: str = Field(..., description="AI agent response")
    session_id: str = Field(..., description="Session ID for continuing conversation")
    intent: str | None = Field(None, description="Classified intent")
    tools_used: list[str] = Field(default_factory=list, description="Tools invoked during processing")
    error: str | None = Field(None, description="Error message if any")
    requires_human: bool = Field(False, description="Whether human handoff is needed")


class ChatHistoryItem(BaseModel):
    """Single item in chat history."""
    role: str
    content: str


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, agent: AgentDep) -> dict[str, Any]:
    """Send a message to the AI agent and receive a response.

    - **message**: The user's message text
    - **session_id**: Optional existing session ID for continuing a conversation
    - **customer_info**: Optional pre-filled customer data (name, email, etc.)
    """
    try:
        result = agent.chat(
            user_input=request.message,
            session_id=request.session_id,
            customer_info=request.customer_info,
        )
        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            intent=result.get("intent"),
            tools_used=result.get("tools_used", []),
            error=result.get("error"),
            requires_human=result.get("requires_human", False),
        ).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.get("/{session_id}/history", response_model=list[ChatHistoryItem])
async def get_history(session_id: str, agent: AgentDep) -> list[dict[str, Any]]:
    """Retrieve conversation history for a given session."""
    try:
        history = agent.get_history(session_id)
        return [ChatHistoryItem(role=h["role"], content=h["content"]).model_dump() for h in history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@router.delete("/{session_id}/reset")
async def reset_session(session_id: str, agent: AgentDep) -> dict[str, str]:
    """Clear conversation history for a session."""
    try:
        agent.reset_session(session_id)
        return {"status": "success", "message": f"Session {session_id} reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset session: {str(e)}")
