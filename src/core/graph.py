"""LangGraph state graph definition for the AquaMax AI Agent."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.config.settings import settings
from src.core.exceptions import LLMError, ToolError
from src.core.memory import memory_manager
from src.core.state import AgentState, create_initial_state
from src.tools import ALL_TOOLS
from src.utils.helpers import extract_json, sanitize_input
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
            return {**state, "intent": "general", "next_node": "build_response"}

        last_message = messages[-1]
        if not isinstance(last_message, HumanMessage):
            return {**state, "intent": "general", "next_node": "build_response"}

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
        return {**state, "intent": intent, "next_node": None}

    except Exception as e:
        logger.error("Intent classification failed: %s", e)
        return {**state, "intent": "general", "error": str(e), "next_node": "error_handler"}


# ───────────────────────────────────────────────────────────────
# Node: Entity Extraction
# ───────────────────────────────────────────────────────────────

def extract_entities(state: AgentState) -> AgentState:
    """Extract customer information and requirements from the conversation."""
    try:
        messages = state["messages"]
        if not messages:
            return {**state, "next_node": None}

        # Combine recent messages for context
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
            # Merge with existing customer info
            existing = state.get("customer_info", {})
            merged = {**existing, **{k: v for k, v in parsed.items() if v is not None}}
            return {**state, "customer_info": merged, "extracted_entities": parsed}

        return {**state}

    except Exception as e:
        logger.error("Entity extraction failed: %s", e)
        return {**state, "error": str(e)}


# ───────────────────────────────────────────────────────────────
# Node: Build Response (final response to user)
# ───────────────────────────────────────────────────────────────

def build_response(state: AgentState) -> AgentState:
    """Build the final AI response to the user, incorporating tool results."""
    try:
        messages = state["messages"]
        llm = _get_llm()

        # Bind tools to the LLM for this final response
        llm_with_tools = llm.bind_tools(ALL_TOOLS)

        # Get system message + history + current user message
        system_msg = memory_manager.get_system_message()
        all_messages = [system_msg] + list(messages)

        response = llm_with_tools.invoke(all_messages)

        # Check if the LLM wants to call a tool
        if hasattr(response, "tool_calls") and response.tool_calls:
            # Return with tool call requests for the next step
            return {**state, "messages": messages + [response]}

        # Plain text response
        return {**state, "messages": messages + [AIMessage(content=response.content)]}

    except Exception as e:
        logger.error("Response building failed: %s", e)
        error_msg = (
            "I apologize, but I'm having trouble processing your request right now. "
            "Please try again or contact our support team at sales@aquamax-rehab.com."
        )
        return {**state, "messages": messages + [AIMessage(content=error_msg)], "error": str(e)}


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
    """Route to the appropriate node based on classified intent."""
    intent = state.get("intent", "general")
    error = state.get("error")
    if error:
        return "error_handler"

    routing_map = {
        "search": "tools",
        "compare": "tools",
        "recommend": "tools",
        "lead": "tools",
        "quote": "tools",
        "email": "tools",
        "general": "build_response",
    }
    return routing_map.get(intent, "build_response")


def route_after_tools(state: AgentState) -> str:
    """After tools execute, route back to response building or error handling."""
    if state.get("error"):
        return "error_handler"
    return "build_response"


def route_after_response(state: AgentState) -> str:
    """After response building, check if we need to extract entities or end."""
    if state.get("error"):
        return "error_handler"
    # Check if we need to extract entities from this turn
    return "extract_entities"


# ───────────────────────────────────────────────────────────────
# Build the Graph
# ───────────────────────────────────────────────────────────────

def build_agent_graph() -> StateGraph:
    """Construct and return the compiled LangGraph state graph."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("extract_entities", extract_entities)
    workflow.add_node("build_response", build_response)
    workflow.add_node("error_handler", error_handler)
    workflow.add_node("tools", tool_node)

    # Add edges
    workflow.set_entry_point("classify_intent")

    # After intent classification, route to tools or response building
    workflow.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {
            "tools": "tools",
            "build_response": "build_response",
            "error_handler": "error_handler",
        },
    )

    # After tools, route to response building or error handler
    workflow.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "build_response": "build_response",
            "error_handler": "error_handler",
        },
    )

    # After response, extract entities then end
    workflow.add_conditional_edges(
        "build_response",
        route_after_response,
        {
            "extract_entities": "extract_entities",
            "error_handler": "error_handler",
        },
    )

    # After entity extraction, end the turn
    workflow.add_edge("extract_entities", END)

    # Error handler always ends
    workflow.add_edge("error_handler", END)

    return workflow.compile()


# Singleton compiled graph
agent_graph = build_agent_graph()
