"""Conversation memory manager using SQLite and LangGraph checkpointing."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.database.connection import get_session
from src.database.models import Conversation
from src.database.repository import ConversationRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationMemory:
    """Manages conversation persistence and retrieval for agent sessions."""

    SYSTEM_PROMPT = (
        "You are AquaMax AI, the intelligent sales and customer support assistant for AquaMax Rehab Equipment. "
        "You help customers find the right rehabilitation and physiotherapy equipment.\n\n"
        "Your capabilities:\n"
        "- Search and recommend products from our catalog\n"
        "- Compare multiple products side-by-side\n"
        "- Capture customer leads and contact information\n"
        "- Generate formal quotations\n"
        "- Draft professional follow-up emails\n"
        "- Answer questions about equipment, conditions, and rehabilitation\n\n"
        "Guidelines:\n"
        "- Always be helpful, professional, and empathetic\n"
        "- Ask clarifying questions when requirements are unclear\n"
        "- Recommend products based on condition, budget, and use case\n"
        "- Capture leads when customers show purchase intent\n"
        "- Generate quotations when customers are ready to buy\n"
        "- If you don't know something, be honest and offer to connect with a human representative\n"
    )

    def __init__(self) -> None:
        self._cache: dict[str, list[Any]] = {}

    def get_history(self, session_id: str, limit: int = 20) -> list[Any]:
        """Retrieve conversation history from database."""
        try:
            with get_session() as session:
                repo = ConversationRepository(session)
                rows = repo.get_by_session(session_id, limit=limit)
                messages = []
                for row in rows:
                    if row.role == "user":
                        messages.append(HumanMessage(content=row.content))
                    elif row.role == "assistant":
                        messages.append(AIMessage(content=row.content))
                    elif row.role == "system":
                        messages.append(SystemMessage(content=row.content))
                    elif row.role == "tool":
                        messages.append(ToolMessage(content=row.content, tool_call_id=""))
                return messages
        except Exception as e:
            logger.error("Failed to load history for session %s: %s", session_id, e)
            return []

    def add_message(self, session_id: str, role: str, content: str, metadata: dict | None = None) -> None:
        """Persist a single message to the database."""
        try:
            with get_session() as session:
                repo = ConversationRepository(session)
                conv = Conversation(
                    session_id=session_id,
                    role=role,
                    content=content,
                    meta_data=metadata,
                )
                repo.create(conv)
        except Exception as e:
            logger.error("Failed to persist message for session %s: %s", session_id, e)

    def get_system_message(self) -> SystemMessage:
        """Return the system prompt message."""
        return SystemMessage(content=self.SYSTEM_PROMPT)

    def build_messages(self, session_id: str, user_input: str) -> list[Any]:
        """Build a complete message list for the LLM including system prompt and history."""
        messages = [self.get_system_message()]
        history = self.get_history(session_id, limit=10)
        messages.extend(history)
        messages.append(HumanMessage(content=user_input))
        return messages

    def clear_session(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        try:
            with get_session() as session:
                repo = ConversationRepository(session)
                repo.delete_by_session(session_id)
        except Exception as e:
            logger.error("Failed to clear session %s: %s", session_id, e)


# Singleton instance
memory_manager = ConversationMemory()
