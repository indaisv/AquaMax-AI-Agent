"""Lead capture tool for saving customer information to the database."""

from __future__ import annotations

from langchain_core.tools import tool

from src.database.connection import get_session
from src.database.models import Lead
from src.database.repository import LeadRepository
from src.utils.helpers import sanitize_input
from src.utils.logger import get_logger

logger = get_logger(__name__)


@tool
def capture_lead(
    session_id: str,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    organization: str | None = None,
    budget_range: str | None = None,
    condition: str | None = None,
    requirements: str | None = None,
) -> str:
    """Capture and save a customer lead to the AquaMax database.

    Use this tool when the customer provides their contact information, expresses interest in purchasing,
    or requests a quotation. The system will check for duplicates by email and update existing records.

    Args:
        session_id: The conversation session ID (required for tracking)
        name: Customer full name
        email: Customer email address
        phone: Customer phone number
        organization: Clinic, hospital, or company name
        budget_range: Budget range (e.g., "5000-10000", "under 50000")
        condition: Medical condition or use case
        requirements: Detailed requirements or notes
    """
    try:
        with get_session() as session:
            repo = LeadRepository(session)

            # Check for existing lead by email
            existing = None
            if email:
                existing = repo.get_by_email(email)
            if not existing and session_id:
                existing = repo.get_by_session(session_id)

            if existing:
                # Update existing lead with new info
                updated = False
                if name and not existing.name:
                    existing.name = sanitize_input(name)
                    updated = True
                if email and not existing.email:
                    existing.email = sanitize_input(email)
                    updated = True
                if phone and not existing.phone:
                    existing.phone = sanitize_input(phone)
                    updated = True
                if organization and not existing.organization:
                    existing.organization = sanitize_input(organization)
                    updated = True
                if budget_range and not existing.budget_range:
                    existing.budget_range = sanitize_input(budget_range)
                    updated = True
                if condition and not existing.condition:
                    existing.condition = sanitize_input(condition)
                    updated = True
                if requirements and not existing.requirements:
                    existing.requirements = sanitize_input(requirements)
                    updated = True

                repo.update(existing)
                return (
                    f"Lead updated successfully! (ID: {existing.id})\n"
                    f"Thank you, {existing.name or 'valued customer'}. AquaMax will contact you soon."
                )

            # Create new lead
            lead = Lead(
                session_id=session_id,
                name=sanitize_input(name) if name else None,
                email=sanitize_input(email) if email else None,
                phone=sanitize_input(phone) if phone else None,
                organization=sanitize_input(organization) if organization else None,
                budget_range=sanitize_input(budget_range) if budget_range else None,
                condition=sanitize_input(condition) if condition else None,
                requirements=sanitize_input(requirements) if requirements else None,
                status="new",
            )
            repo.create(lead)

            return (
                f"Lead captured successfully! (ID: {lead.id})\n"
                f"Thank you, {lead.name or 'valued customer'}. AquaMax will contact you at "
                f"{lead.email or lead.phone or 'your preferred contact'} soon."
            )

    except Exception as e:
        logger.error("Lead capture failed: %s", e)
        return f"Sorry, we couldn't save your information right now. Please try again. (Error: {type(e).__name__})"
