"""Leads API router for CRUD operations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.dependencies import CustomerServiceDep

router = APIRouter()


class LeadCreate(BaseModel):
    """Request model for creating a lead."""
    session_id: str = Field(default="", description="Session ID")
    name: str | None = Field(None, description="Customer name")
    email: str | None = Field(None, description="Customer email")
    phone: str | None = Field(None, description="Customer phone")
    organization: str | None = Field(None, description="Clinic or company name")
    budget_range: str | None = Field(None, description="Budget range")
    condition: str | None = Field(None, description="Medical condition or use case")
    requirements: str | None = Field(None, description="Detailed requirements")
    status: str = Field(default="new", description="Lead status")


class LeadResponse(BaseModel):
    """Response model for a lead."""
    id: int
    session_id: str
    name: str
    email: str
    phone: str
    organization: str
    budget_range: str
    condition: str
    requirements: str
    status: str
    created_at: str | None


@router.get("", response_model=list[LeadResponse])
async def list_leads(
    service: CustomerServiceDep,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    """List all captured leads with pagination."""
    leads = service.list_leads(limit=limit, offset=offset)
    return leads


@router.post("", response_model=LeadResponse)
async def create_lead(request: LeadCreate, service: CustomerServiceDep) -> dict[str, Any]:
    """Create a new lead manually."""
    try:
        lead = service.create_lead(request.model_dump())
        return lead
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create lead: {str(e)}")


@router.get("/search")
async def search_leads(
    email: str | None = None,
    session_id: str | None = None,
    service: CustomerServiceDep = None,
) -> dict[str, Any]:
    """Search leads by email or session ID."""
    if email:
        lead = service.get_lead_by_email(email)
        if lead:
            return {"found": True, "lead": lead}
    if session_id:
        lead = service.get_lead_by_session(session_id)
        if lead:
            return {"found": True, "lead": lead}
    return {"found": False, "lead": None}
