"""Customer information business logic service."""

from __future__ import annotations

from typing import Any

from src.database.connection import get_session
from src.database.models import Lead
from src.database.repository import LeadRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CustomerService:
    """Business logic for customer and lead management."""

    def get_lead_by_session(self, session_id: str) -> dict | None:
        """Retrieve a lead by session ID."""
        try:
            with get_session() as session:
                repo = LeadRepository(session)
                lead = repo.get_by_session(session_id)
                return lead.to_dict() if lead else None
        except Exception as e:
            logger.error("Failed to get lead by session: %s", e)
            return None

    def get_lead_by_email(self, email: str) -> dict | None:
        """Retrieve a lead by email."""
        try:
            with get_session() as session:
                repo = LeadRepository(session)
                lead = repo.get_by_email(email)
                return lead.to_dict() if lead else None
        except Exception as e:
            logger.error("Failed to get lead by email: %s", e)
            return None

    def list_leads(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """List all leads with pagination."""
        try:
            with get_session() as session:
                repo = LeadRepository(session)
                leads = repo.list_all(limit=limit, offset=offset)
                return [l.to_dict() for l in leads]
        except Exception as e:
            logger.error("Failed to list leads: %s", e)
            return []

    def create_lead(self, data: dict[str, Any]) -> dict:
        """Create a new lead manually."""
        try:
            with get_session() as session:
                repo = LeadRepository(session)
                lead = Lead(
                    session_id=data.get("session_id", ""),
                    name=data.get("name"),
                    email=data.get("email"),
                    phone=data.get("phone"),
                    organization=data.get("organization"),
                    budget_range=data.get("budget_range"),
                    condition=data.get("condition"),
                    requirements=data.get("requirements"),
                    status=data.get("status", "new"),
                )
                repo.create(lead)
                return lead.to_dict()
        except Exception as e:
            logger.error("Failed to create lead: %s", e)
            raise
