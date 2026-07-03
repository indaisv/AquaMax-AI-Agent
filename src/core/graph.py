"""LangGraph state graph definition for the AquaMax AI Agent."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.config.settings import settings
from src.core.memory import memory_manager
from src.core.state import AgentState
from src.tools import ALL_TOOLS
from src.utils.helpers import extract_json
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _get_llm() -> ChatOpenAI:
    """Initialize the LLM with configured settings."""
    kwargs: dict[str, Any] = {
        "model": settings.model_name,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return ChatOpenAI(api_key=settings.openai_api_key, **kwargs)


# ───────────────────────────────────────────────────────────────
# Node: Intent Classification
# ───────────────────────────────────────────────────────────────

def classify_intent(state: AgentState) -> AgentState:
    """Classify the user's intent from their latest message."""
    try:
        messages = state["messages"]
        if not messages:
            return {**state, "intent": "general"}

        last_message = messages[-1]
        if not isinstance(last_message, HumanMessage):
            return {**state, "intent": "general"}

        llm = _get_llm()

        prompt = (
            "You are an intent classifier for a rehabilitation equipment sales assistant.\n"
            "Classify the user's intent into EXACTLY one of these categories:\n"
            "- search: Looking for specific equipment or browsing catalog\n"
            "- compare: Comparing multiple products or asking for differences\n"
            "- recommend: Asking for recommendations or suggestions\n"
            "- lead: Providing contact info or showing purchase intent\n"
            "- quote: Asking for price, quotation, or pricing details\n"
            "- email: Requesting a follow-up email or contact\n"
            "- general: General question, greeting, or small talk\n\n"
            "Respond ONLY with a JSON object like: {\"intent\": \"search\", \"confidence\": 0.9}\n\n"
            f"User message: {last_message.content}"
        )

        response = llm.invoke([HumanMessage(content=prompt)])
        parsed = extract_json(response.content)

        if parsed and "intent" in parsed:
            intent = parsed["intent"].lower().strip()
            valid_intents = {"search", "compare", "recommend", "lead", "quote", "email", "general"}
            intent = intent if intent in valid_intents else "general"
        else:
            intent = "general"

        logger.info("Intent classified: %s for session %s", intent, state["session_id"])
        return {**state, "intent": intent}

    except Exception as e:
        logger.error("Intent classification failed: %s", e)
        return {**state, "intent": "general", "error": str(e)}


# ───────────────────────────────────────────────────────────────
# Node: Entity Extraction
# ───────────────────────────────────────────────────────────────

def extract_entities(state: AgentState) -> AgentState:
    """Extract customer information and requirements from the conversation."""
    try:
        messages = state["messages"]
        if not messages:
            return {**state}

        conversation_text = "\n".join(
            f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
            for m in messages[-6:]
        )

        llm = _get_llm()
        prompt = (
            "Extract customer information from this conversation. "
            "Return ONLY a JSON object with these fields (use null if not found):\n"
            "{\n"
            '  "name": "customer name or null",\n'
            '  "email": "email or null",\n'
            '  "phone": "phone or null",\n'
            '  "organization": "clinic/hospital name or null",\n'
            '  "budget_range": "budget mentioned or null",\n'
            '  "condition": "medical condition or use case or null",\n'
            '  "requirements": "specific equipment needs or null",\n'
            '  "role": "physiotherapist, clinic owner, patient, etc. or null"\n'
            "}\n\n"
            f"Conversation:\n{conversation_text}"
        )

        response = llm.invoke([HumanMessage(content=prompt)])
        parsed = extract_json(response.content)

        if parsed:
            existing = state.get("customer_info", {})
            merged = {**existing, **{k: v for k, v in parsed.items() if v is not None}}
            return {**state, "customer_info": merged, "extracted_entities": parsed}

        return {**state}

    except Exception as e:
        logger.error("Entity extraction failed: %s", e)
        return {**state, "error": str(e)}


# ───────────────────────────────────────────────────────────────
# Node: LLM Response (with tools bound)
# ───────────────────────────────────────────────────────────────

def llm_response(state: AgentState) -> AgentState:
    """Invoke the LLM with tools bound. May return tool calls or plain text."""
    try:
        messages = state["messages"]
        llm = _get_llm()
        llm_with_tools = llm.bind_tools(ALL_TOOLS)

        system_msg = memory_manager.get_system_message()
        all_messages = [system_msg] + list(messages)

        response = llm_with_tools.invoke(all_messages)
        return {**state, "messages": messages + [response]}

    except Exception as e:
        logger.error("LLM response failed: %s", e)
        error_msg = (
            "I apologize, but I'm having trouble processing your request right now. "
            "Please try again or contact our support team."
        )
        return {
            **state,
            "messages": messages + [AIMessage(content=error_msg)],
            "error": str(e),
        }


# ───────────────────────────────────────────────────────────────
# Node: Error Handler
# ───────────────────────────────────────────────────────────────

def error_handler(state: AgentState) -> AgentState:
    """Handle errors gracefully and recover when possible."""
    error = state.get("error", "Unknown error")
    logger.error("Agent error in session %s: %s", state.get("session_id"), error)

    messages = state["messages"]
    recovery_msg = (
        "I encountered a technical issue while processing your request. "
        "I've logged the error for our team. In the meantime, could you rephrase your question? "
        "Or if you prefer, I can connect you with a human representative."
    )

    return {
        **state,
        "messages": messages + [AIMessage(content=recovery_msg)],
        "error": None,
        "requires_human": True,
    }


# ───────────────────────────────────────────────────────────────
# Tool Node
# ───────────────────────────────────────────────────────────────

tool_node = ToolNode(ALL_TOOLS)


# ───────────────────────────────────────────────────────────────
# Conditional Routing
# ───────────────────────────────────────────────────────────────

def route_after_intent(state: AgentState) -> str:
    """After intent classification, always go to LLM response."""
    if state.get("error"):
        return "error_handler"
    return "llm_response"


def route_after_llm(state: AgentState) -> str:
    """After LLM response, check if it wants to call tools or is done."""
    if state.get("error"):
        return "error_handler"

    messages = state.get("messages", [])
    if not messages:
        return "extract_entities"

    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and getattr(last_message, "tool_calls", None):
        return "tools"

    return "extract_entities"


def route_after_tools(state: AgentState) -> str:
    """After tools execute, route back to LLM to process tool results."""
    if state.get("error"):
        return "error_handler"
    return "llm_response"


# ───────────────────────────────────────────────────────────────
# Build the Graph
# ───────────────────────────────────────────────────────────────

def build_agent_graph() -> StateGraph:
    """Construct and return the compiled LangGraph state graph.

    Flow:
        classify_intent → llm_response → router
                          ↑                |
                          |           tools (if tool_calls)
                          |                |
                          └────────────────┘
                          |
                          v
                    extract_entities → END
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("extract_entities", extract_entities)
    workflow.add_node("llm_response", llm_response)
    workflow.add_node("error_handler", error_handler)
    workflow.add_node("tools", tool_node)

    # Entry point
    workflow.set_entry_point("classify_intent")

    # classify_intent → llm_response (always)
    workflow.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {
            "llm_response": "llm_response",
            "error_handler": "error_handler",
        },
    )

    # llm_response → tools (if tool_calls) OR extract_entities (if done)
    workflow.add_conditional_edges(
        "llm_response",
        route_after_llm,
        {
            "tools": "tools",
            "extract_entities": "extract_entities",
            "error_handler": "error_handler",
        },
    )

    # tools → llm_response (loop back to process tool results)
    workflow.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "llm_response": "llm_response",
            "error_handler": "error_handler",
        },
    )

    # extract_entities → END
    workflow.add_edge("extract_entities", END)

    # Error handler → END
    workflow.add_edge("error_handler", END)

    return workflow.compile()


# Singleton compiled graph
agent_graph = build_agent_graph()
