"""Main agent orchestrator — high-level interface for running the AquaMax AI Agent."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from src.config.settings import settings
from src.core.exceptions import ConfigurationError
from src.core.graph import agent_graph
from src.core.memory import memory_manager
from src.core.state import AgentState, create_initial_state
from src.utils.helpers import generate_session_id, sanitize_input
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AquaMaxAgent:
    """High-level agent interface for the AquaMax Sales & Support AI.

    Usage:
        agent = AquaMaxAgent()
        response = agent.chat("I need a TENS unit for back pain", session_id="abc-123")
    """

    def __init__(self) -> None:
        self._graph = agent_graph
        self._validate_config()

    def _validate_config(self) -> None:
        """Ensure required configuration is present."""
        try:
            settings.validate()
        except ValueError as e:
            raise ConfigurationError(str(e)) from e

    def chat(
        self,
        user_input: str,
        session_id: str | None = None,
        customer_info: dict | None = None,
    ) -> dict[str, Any]:
        """Process a single user message and return the agent response.

        Args:
            user_input: The user's message text
            session_id: Optional existing session ID; generates new if None
            customer_info: Optional pre-filled customer info

        Returns:
            Dict with 'response', 'session_id', 'intent', 'tools_used', 'error'
        """
        user_input = sanitize_input(user_input)
        if not user_input:
            return {
                "response": "Hello! How can I help you with rehabilitation equipment today?",
                "session_id": session_id or generate_session_id(),
                "intent": None,
                "tools_used": [],
                "error": None,
            }

        session_id = session_id or generate_session_id()
        logger.info("Processing message for session %s: %s", session_id, user_input[:80])

        # Build initial state
        state = create_initial_state(session_id)
        state["messages"] = [HumanMessage(content=user_input)]
        if customer_info:
            state["customer_info"] = {**state.get("customer_info", {}), **customer_info}

        # Load previous history if available
        history = memory_manager.get_history(session_id, limit=10)
        if history:
            state["messages"] = history + state["messages"]

        # Track which tools were used
        tools_used: list[str] = []

        try:
            # Run the graph
            result = self._graph.invoke(state)

            # Extract tool usage from messages
            for msg in result.get("messages", []):
                if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tools_used.append(tc.get("name", "unknown"))

            # Find the final AI response
            final_response = "I'm not sure how to respond to that. Could you rephrase?"
            for msg in reversed(result.get("messages", [])):
                if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
                    final_response = msg.content
                    break

            # Persist conversation
            memory_manager.add_message(session_id, "user", user_input)
            memory_manager.add_message(session_id, "assistant", final_response)

            return {
                "response": final_response,
                "session_id": session_id,
                "intent": result.get("intent"),
                "tools_used": list(set(tools_used)),
                "error": result.get("error"),
                "requires_human": result.get("requires_human", False),
                "customer_info": result.get("customer_info", {}),
            }

        except Exception as e:
            logger.error("Agent execution failed for session %s: %s", session_id, e)
            return {
                "response": (
                    "I apologize, but I'm experiencing a technical issue. "
                    "Please try again in a moment or contact support."
                ),
                "session_id": session_id,
                "intent": None,
                "tools_used": [],
                "error": str(e),
                "requires_human": True,
            }

    def get_history(self, session_id: str) -> list[dict[str, Any]]:
        """Retrieve conversation history for a session."""
        rows = memory_manager.get_history(session_id, limit=100)
        return [
            {"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content}
            for m in rows
        ]

    def reset_session(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        memory_manager.clear_session(session_id)
        logger.info("Session %s cleared", session_id)


# Singleton agent instance
_agent_instance: AquaMaxAgent | None = None


def get_agent() -> AquaMaxAgent:
    """Get or create the singleton AquaMaxAgent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AquaMaxAgent()
    return _agent_instance
