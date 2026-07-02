"""Quotations API router."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.database.connection import get_session
from src.database.models import Quotation
from src.database.repository import QuotationRepository

router = APIRouter()


class QuotationCreate(BaseModel):
    """Request model for creating a quotation."""
    session_id: str = Field(..., description="Session ID")
    lead_id: int | None = Field(None, description="Associated lead ID")
    product_ids: list[int] = Field(..., description="List of product IDs")
    discount_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    validity_days: int = Field(default=30, ge=1, le=365)
    notes: str | None = Field(None, description="Additional notes")


@router.post("")
async def create_quotation(request: QuotationCreate) -> dict[str, Any]:
    """Create a new quotation (basic endpoint — full logic is in tools)."""
    # Note: Full quotation generation is handled by the agent tool.
    # This endpoint is for direct API access to saved quotations.
    try:
        with get_session() as session:
            repo = QuotationRepository(session)
            # Calculate pricing using the product repo
            from src.database.repository import ProductRepository
            product_repo = ProductRepository(session)
            products = product_repo.get_by_ids(request.product_ids)
            
            if not products:
                raise HTTPException(status_code=404, detail="No products found for quotation")
            
            import json
            subtotal = sum(p.price for p in products)
            discount = subtotal * (request.discount_percent / 100.0)
            tax = (subtotal - discount) * 0.18
            total = subtotal - discount + tax
            
            product_list = [{"id": p.id, "sku": p.sku, "name": p.name, "price": p.price, "quantity": 1} for p in products]
            
            quotation = Quotation(
                session_id=request.session_id,
                lead_id=request.lead_id,
                products=json.dumps(product_list),
                subtotal=subtotal,
                discount=discount,
                tax=tax,
                total=total,
                validity_days=request.validity_days,
                notes=request.notes or "",
                status="draft",
            )
            repo.create(quotation)
            return {
                "quotation": quotation.to_dict(),
                "message": "Quotation created successfully",
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create quotation: {str(e)}")


@router.get("/{quotation_id}")
async def get_quotation(quotation_id: int) -> dict[str, Any]:
    """Get a quotation by ID."""
    try:
        with get_session() as session:
            repo = QuotationRepository(session)
            quotation = repo.get_by_id(quotation_id)
            if not quotation:
                raise HTTPException(status_code=404, detail=f"Quotation {quotation_id} not found")
            return quotation.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve quotation: {str(e)}")


@router.get("/session/{session_id}")
async def get_quotations_by_session(session_id: str) -> dict[str, Any]:
    """Get all quotations for a session."""
    try:
        with get_session() as session:
            repo = QuotationRepository(session)
            quotations = repo.get_by_session(session_id)
            return {"quotations": [q.to_dict() for q in quotations], "count": len(quotations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve quotations: {str(e)}")
