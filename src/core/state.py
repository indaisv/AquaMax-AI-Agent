"""LangGraph state definitions using TypedDict with reducers."""

from __future__ import annotations

from typing import Annotated, Any

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class CustomerInfo(TypedDict, total=False):
    """Structured customer information extracted from conversation."""

    name: str | None
    email: str | None
    phone: str | None
    organization: str | None
    budget_range: str | None
    condition: str | None
    requirements: str | None
    role: str | None  # e.g., "physiotherapist", "clinic owner", "patient"


class ProductResult(TypedDict, total=False):
    """A product from the catalog search."""

    id: int
    sku: str
    name: str
    category: str
    subcategory: str
    price: float
    rating: float
    stock: int
    description: str
    features: list[str]
    condition_tags: list[str]
    match_score: float


class QuotationData(TypedDict, total=False):
    """Generated quotation details."""

    quotation_id: int
    products: list[dict[str, Any]]
    subtotal: float
    discount: float
    tax: float
    total: float
    validity_days: int
    terms: str
    notes: str


class AgentState(TypedDict, total=False):
    """Complete state schema for the LangGraph agent.

    Each field tracks a different aspect of the conversation and business logic.
    """

    # --- Conversation ---
    messages: Annotated[list[AnyMessage], add_messages]
    session_id: str

    # --- Intent & Understanding ---
    intent: str | None  # e.g., "search", "compare", "recommend", "quote", "lead", "email", "general"
    extracted_entities: dict[str, Any]

    # --- Customer ---
    customer_info: CustomerInfo
    lead_captured: bool
    lead_id: int | None

    # --- Products ---
    search_query: str | None
    search_filters: dict[str, Any]
    search_results: list[ProductResult]
    comparison_ids: list[int]
    comparison_data: dict[str, Any]
    recommendation: dict[str, Any]

    # --- Business Outputs ---
    quotation: QuotationData
    email_draft: str
    email_tone: str

    # --- Control & Error ---
    error: str | None
    requires_human: bool
    next_node: str | None
    clarification_needed: bool
    clarification_question: str | None


def create_initial_state(session_id: str) -> AgentState:
    """Factory for creating a fresh agent state."""
    return AgentState(
        messages=[],
        session_id=session_id,
        intent=None,
        extracted_entities={},
        customer_info=CustomerInfo(),
        lead_captured=False,
        lead_id=None,
        search_query=None,
        search_filters={},
        search_results=[],
        comparison_ids=[],
        comparison_data={},
        recommendation={},
        quotation=QuotationData(),
        email_draft="",
        email_tone="professional",
        error=None,
        requires_human=False,
        next_node=None,
        clarification_needed=False,
        clarification_question=None,
    )
