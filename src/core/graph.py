"""LangGraph state graph definition for the AquaMax AI Agent.

Hybrid approach: rule-based tool dispatch + LLM response generation.
We ALWAYS call relevant tools for product queries, then pass real results
to the LLM for a sales-quality response. No model-dependent tool calling.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from src.config.settings import settings
from src.core.memory import memory_manager
from src.core.state import AgentState
from src.tools import (
    capture_lead,
    compare_products,
    draft_email,
    generate_quotation,
    recommend_products,
    search_products,
)
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
# Node: Dispatch Tools (rule-based — always calls relevant tools)
# ───────────────────────────────────────────────────────────────

def dispatch_tools(state: AgentState) -> AgentState:
    """Always call relevant tools based on the user's message, then add results to state.

    This avoids model-dependent tool calling. We extract keywords from the user's
    message and call the appropriate tools directly. The LLM only handles the
    final response generation using real tool results.
    """
    try:
        messages = list(state.get("messages", []))
        session_id = state.get("session_id", "")
        if not messages:
            return {**state}

        # Get the last user message
        user_msgs = [m for m in messages if isinstance(m, HumanMessage)]
        if not user_msgs:
            return {**state}
        user_text = user_msgs[-1].content.lower()

        tools_called: list[str] = []
        tool_results: list[str] = []

        # Always call search_products for product-related queries
        if any(kw in user_text for kw in [
            "need", "want", "looking", "tens", "ultrasound", "wheelchair", "walker",
            "equipment", "device", "machine", "unit", "rehab", "therapy", "pain",
            "back", "knee", "shoulder", "clinic", "hospital", "recommend", "suggest",
            "best", "good", "which", "what", "show", "find", "search", "catalog"
        ]):
            result = search_products.invoke({"query": user_text, "category": None, "max_price": None})
            tools_called.append("search_products")
            tool_results.append(f"[SEARCH RESULTS]\n{result}")

            # Also call recommend_products for richer recommendations
            result2 = recommend_products.invoke({"requirements": user_text, "budget": None, "top_k": 3})
            tools_called.append("recommend_products")
            tool_results.append(f"[RECOMMENDATION RESULTS]\n{result2}")

        # Call compare_products if user asks to compare
        if any(kw in user_text for kw in ["compare", "vs", "versus", "difference", "better"]):
            # Try to extract product IDs from the message (naive approach)
            # For now, compare first two products from search results
            # This will be improved by passing IDs from previous results
            pass  # Requires product IDs from previous context

        # Call capture_lead if user provides contact info
        if any(kw in user_text for kw in ["name is", "my name", "email", "phone", "contact", "call me", "reach me"]):
            # Extract entities
            name = None
            email = None
            phone = None
            org = None
            for line in user_text.split("\n"):
                if "name is" in line or "my name" in line:
                    name = line.split("is")[-1].strip() if "is" in line else line.split("name")[-1].strip()
                    name = name.strip(".")
                if "email" in line:
                    import re
                    emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", line)
                    if emails:
                        email = emails[0]
                if "phone" in line or "number" in line:
                    import re
                    phones = re.findall(r"[\d\s\-+()]{10,}", line)
                    if phones:
                        phone = phones[0]

            if name or email or phone:
                result = capture_lead.invoke({
                    "session_id": session_id,
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "organization": org,
                })
                tools_called.append("capture_lead")
                tool_results.append(f"[LEAD CAPTURE]\n{result}")

        # Call generate_quotation if user asks for quote/price
        if any(kw in user_text for kw in ["quote", "quotation", "price", "pricing", "cost", "how much"]):
            # Extract product IDs from message if possible
            import re
            ids = re.findall(r"(?:product\s*id|id)\s*[:=]?\s*(\d+)", user_text)
            if ids:
                result = generate_quotation.invoke({
                    "session_id": session_id,
                    "product_ids": ",".join(ids),
                    "discount_percent": 0.0,
                    "validity_days": 30,
                })
                tools_called.append("generate_quotation")
                tool_results.append(f"[QUOTATION]\n{result}")

        # Format results into a clean context message (NOT ToolMessage — Groq doesn't render them well)
        if tool_results:
            context = "## REAL PRODUCTS FROM THE AQUAMAX DATABASE\n\n" + "\n\n---\n\n".join(tool_results)
            messages.append(SystemMessage(content=context))

        return {**state, "messages": messages, "tools_called": tools_called}

    except Exception as e:
        logger.error("Tool dispatch failed: %s", e)
        return {**state, "error": str(e)}


# ───────────────────────────────────────────────────────────────
# Node: LLM Respond (generates final sales response using tool results)
# ───────────────────────────────────────────────────────────────

def llm_respond(state: AgentState) -> AgentState:
    """Generate the final sales-quality response using the tool results in messages."""
    try:
        messages = list(state.get("messages", []))
        if not messages:
            return {**state}

        llm = _get_llm()

        # Check if we have database results in the conversation
        has_tool_results = any(
            "REAL PRODUCTS FROM THE AQUAMAX DATABASE" in (m.content or "")
            for m in messages
        )

        if has_tool_results:
            # Full sales response with product recommendations
            system_msg = SystemMessage(
                content=(
                    "You are AquaMax AI, a senior sales consultant for AquaMax Rehab Equipment.\n\n"
                    "## CRITICAL RULE: Use ONLY Database Products\n"
                    "The conversation contains a message starting with '## REAL PRODUCTS FROM THE AQUAMAX DATABASE'. "
                    "You MUST use ONLY the exact product names, prices, and specs listed there. "
                    "If you cannot find a specific product mentioned by the customer, say so honestly and suggest the closest match from the database.\n\n"
                    "## Response Format (mandatory)\n"
                    "1. Opening: 1 sentence acknowledging their need\n"
                    "2. Top Pick: Name the BEST product from the database with price (₹X,XXX.00) and why it fits\n"
                    "3. Alternative: Name ONE backup option with price and brief reason\n"
                    "4. Practical note: Mention stock, delivery, or warranty if available\n"
                    "5. Next step: Ask ONE clear question (compare, quote, more details?)\n\n"
                    "## NEVER Do This\n"
                    "- Say 'I couldn't find products' when the database section shows products\n"
                    "- Make up product names like 'Omron' or 'Beurer' — only use AquaMax branded products from the database\n"
                    "- Give vague responses without specific prices and names\n"
                )
            )
        else:
            # No tools called — greeting, small talk, or general question
            system_msg = SystemMessage(
                content=(
                    "You are AquaMax AI, a senior sales consultant for AquaMax Rehab Equipment.\n\n"
                    "The user has NOT asked about specific products yet. "
                    "Give a warm, brief greeting and ask what kind of rehabilitation equipment they're looking for. "
                    "DO NOT mention specific products or prices unless the user asks. "
                    "Keep it under 3 sentences.\n\n"
                    "Example: 'Hello! I'm here to help you find the right rehabilitation equipment. "
                    "What condition or body part are you looking to address?'"
                )
            )

        all_messages = [system_msg] + messages
        response = llm.invoke(all_messages)
        return {**state, "messages": messages + [response]}

    except Exception as e:
        logger.error("Response generation failed: %s", e)
        return {**state, "error": str(e)}


# ───────────────────────────────────────────────────────────────
# Node: Extract Entities
# ───────────────────────────────────────────────────────────────

def extract_entities(state: AgentState) -> AgentState:
    """Extract customer information from user messages for future turns."""
    try:
        messages = state.get("messages", [])
        if not messages:
            return {**state}

        user_texts = [m.content for m in messages if isinstance(m, HumanMessage)][-3:]
        if not user_texts:
            return {**state}

        conversation_text = "\n".join(f"User: {t}" for t in user_texts)

        llm = _get_llm()
        prompt = (
            "Extract customer information from the user's messages. "
            "Return ONLY a JSON object with these fields (use null if not found):\n"
            '{"name": null, "email": null, "phone": null, "organization": null, '
            '"budget_range": null, "condition": null, "requirements": null, "role": null}\n\n'
            f"Messages:\n{conversation_text}"
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
# Node: Error Handler
# ───────────────────────────────────────────────────────────────

def error_handler(state: AgentState) -> AgentState:
    """Handle errors gracefully."""
    error = state.get("error", "Unknown error")
    logger.error("Agent error in session %s: %s", state.get("session_id"), error)

    messages = state.get("messages", [])
    recovery_msg = (
        "I encountered a technical issue while processing your request. "
        "I've logged the error for our team. Could you rephrase your question? "
        "Or if you prefer, I can connect you with a human representative."
    )

    return {
        **state,
        "messages": messages + [AIMessage(content=recovery_msg)],
        "error": None,
        "requires_human": True,
    }


# ───────────────────────────────────────────────────────────────
# Conditional Routing
# ───────────────────────────────────────────────────────────────

def route_after_dispatch(state: AgentState) -> str:
    """After tool dispatch, always go to response generation."""
    if state.get("error"):
        return "error_handler"
    return "llm_respond"


def route_after_respond(state: AgentState) -> str:
    """After response generation, go to entity extraction."""
    if state.get("error"):
        return "error_handler"
    return "extract_entities"


# ───────────────────────────────────────────────────────────────
# Build the Graph
# ───────────────────────────────────────────────────────────────

def build_agent_graph() -> StateGraph:
    """Construct the compiled LangGraph state graph.

    Flow:
        entry → dispatch_tools → llm_respond → extract_entities → END
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("dispatch_tools", dispatch_tools)
    workflow.add_node("llm_respond", llm_respond)
    workflow.add_node("extract_entities", extract_entities)
    workflow.add_node("error_handler", error_handler)

    # Entry point
    workflow.set_entry_point("dispatch_tools")

    # dispatch_tools → llm_respond (always)
    workflow.add_conditional_edges(
        "dispatch_tools",
        route_after_dispatch,
        {
            "llm_respond": "llm_respond",
            "error_handler": "error_handler",
        },
    )

    # llm_respond → extract_entities
    workflow.add_conditional_edges(
        "llm_respond",
        route_after_respond,
        {
            "extract_entities": "extract_entities",
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
