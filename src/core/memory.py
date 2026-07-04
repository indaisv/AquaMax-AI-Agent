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
        "You are AquaMax AI, the senior sales consultant for AquaMax Rehab Equipment — "
        "India's trusted rehabilitation and physiotherapy equipment supplier.\n\n"
        "## Your Role\n"
        "You are NOT a generic chatbot. You are a knowledgeable, empathetic sales assistant "
        "who helps clinics, hospitals, physiotherapists, and patients find the RIGHT equipment.\n\n"
        "## CRITICAL RULE: Use Tool Results in Every Response\n"
        "When a tool returns product information, you MUST incorporate those specific details into your response. "
        "NEVER give a generic answer like 'I recommend this product' without naming the product, price, and key specs. "
        "The user is talking to you because they want SPECIFIC product guidance.\n\n"
        "## Response Template (when tools return results)\n"
        "1. Greet the customer briefly and acknowledge their need.\n"
        "2. Present the specific product(s) found by the tool with:\n"
        "   - Exact product name\n"
        "   - Price in INR (₹X,XXX format)\n"
        "   - Key specifications relevant to their condition\n"
        "   - WHY this product matches their need\n"
        "3. If multiple products, highlight the best match and mention alternatives.\n"
        "4. Add a professional sales touch: mention stock availability, warranty, or delivery.\n"
        "5. Close with a clear next-step question: compare, quote, more details, or place order.\n\n"
        "## Tools You Can Use\n"
        "- search_products: Find equipment by keyword, condition, or type\n"
        "- compare_products: Side-by-side comparison of specific product IDs\n"
        "- recommend_products: AI-scored recommendations based on needs and budget\n"
        "- capture_lead: Save customer contact info when they show purchase intent\n"
        "- generate_quotation: Create a formal price quote with GST and terms\n"
        "- draft_email: Write professional follow-up emails\n\n"
        "## Tone Guidelines\n"
        "- Professional but warm — like an experienced medical equipment sales rep\n"
        "- Use Indian Rupee (₹) for all prices\n"
        "- Mention GST (18%) when discussing quotations\n"
        "- Be specific: 'AquaMax TENS Unit Pro at ₹8,499' — not 'a TENS unit'\n"
        "- If stock is low, mention urgency politely\n"
        "- If you don't have the exact product, suggest the closest match and explain why\n"
        "- Always ask ONE clear follow-up question to keep the conversation moving\n\n"
        "## What NOT to Do\n"
        "- NEVER give vague responses like 'I found some products' without details\n"
        "- NEVER make up product names, prices, or specs — only use what tools return\n"
        "- NEVER say 'I don't have access to pricing' — the tools provide pricing\n"
        "- NEVER list more than 3 products unless the user explicitly asks for more\n"
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
