"""Data access layer (Repository pattern) for all database entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import desc, func, or_

from src.database.models import Conversation, Lead, Product, Quotation
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = get_logger(__name__)


class ProductRepository:
    """CRUD and search operations for Products."""

    def __init__(self, session: "Session") -> None:
        self._session = session

    def get_by_id(self, product_id: int) -> Product | None:
        return self._session.query(Product).filter(Product.id == product_id).first()

    def get_by_sku(self, sku: str) -> Product | None:
        return self._session.query(Product).filter(Product.sku == sku).first()

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Product]:
        return self._session.query(Product).offset(offset).limit(limit).all()

    def search(self, query: str, category: str | None = None, max_price: float | None = None) -> list[Product]:
        """Fuzzy search across name, description, category, and condition tags."""
        q = f"%{query}%"
        filters = [
            or_(
                Product.name.ilike(q),
                Product.description.ilike(q),
                Product.category.ilike(q),
                Product.condition_tags.ilike(q),
            )
        ]
        if category:
            filters.append(Product.category.ilike(f"%{category}%"))
        if max_price is not None:
            filters.append(Product.price <= max_price)

        return (
            self._session.query(Product)
            .filter(*filters)
            .order_by(desc(Product.rating))
            .all()
        )

    def filter_by_condition(self, condition: str) -> list[Product]:
        """Find products matching a medical condition tag."""
        return (
            self._session.query(Product)
            .filter(Product.condition_tags.ilike(f"%{condition}%"))
            .order_by(desc(Product.rating))
            .all()
        )

    def get_by_ids(self, ids: list[int]) -> list[Product]:
        if not ids:
            return []
        return self._session.query(Product).filter(Product.id.in_(ids)).all()

    def create(self, product: Product) -> Product:
        self._session.add(product)
        self._session.flush()
        return product

    def count(self) -> int:
        return self._session.query(func.count(Product.id)).scalar() or 0


class LeadRepository:
    """CRUD and query operations for Leads."""

    def __init__(self, session: "Session") -> None:
        self._session = session

    def get_by_id(self, lead_id: int) -> Lead | None:
        return self._session.query(Lead).filter(Lead.id == lead_id).first()

    def get_by_email(self, email: str) -> Lead | None:
        return self._session.query(Lead).filter(Lead.email == email).first()

    def get_by_session(self, session_id: str) -> Lead | None:
        return self._session.query(Lead).filter(Lead.session_id == session_id).first()

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Lead]:
        return (
            self._session.query(Lead)
            .order_by(desc(Lead.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def create(self, lead: Lead) -> Lead:
        self._session.add(lead)
        self._session.flush()
        return lead

    def update(self, lead: Lead) -> Lead:
        self._session.merge(lead)
        self._session.flush()
        return lead

    def count(self) -> int:
        return self._session.query(func.count(Lead.id)).scalar() or 0


class ConversationRepository:
    """CRUD operations for conversation history."""

    def __init__(self, session: "Session") -> None:
        self._session = session

    def get_by_session(self, session_id: str, limit: int = 100) -> list[Conversation]:
        return (
            self._session.query(Conversation)
            .filter(Conversation.session_id == session_id)
            .order_by(Conversation.timestamp)
            .limit(limit)
            .all()
        )

    def create(self, conversation: Conversation) -> Conversation:
        self._session.add(conversation)
        self._session.flush()
        return conversation

    def delete_by_session(self, session_id: str) -> int:
        result = self._session.query(Conversation).filter(Conversation.session_id == session_id).delete()
        return result


class QuotationRepository:
    """CRUD operations for Quotations."""

    def __init__(self, session: "Session") -> None:
        self._session = session

    def get_by_id(self, quotation_id: int) -> Quotation | None:
        return self._session.query(Quotation).filter(Quotation.id == quotation_id).first()

    def get_by_session(self, session_id: str) -> list[Quotation]:
        return (
            self._session.query(Quotation)
            .filter(Quotation.session_id == session_id)
            .order_by(desc(Quotation.created_at))
            .all()
        )

    def create(self, quotation: Quotation) -> Quotation:
        self._session.add(quotation)
        self._session.flush()
        return quotation

    def update(self, quotation: Quotation) -> Quotation:
        self._session.merge(quotation)
        self._session.flush()
        return quotation
