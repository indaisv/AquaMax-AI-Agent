"""Products API router for catalog operations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import ProductServiceDep

router = APIRouter()


@router.get("")
async def list_products(
    service: ProductServiceDep,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    category: str | None = Query(None, description="Filter by category"),
) -> dict[str, Any]:
    """List all products with optional category filter."""
    products = service.list_products(limit=limit, offset=offset)
    if category:
        products = [p for p in products if p.get("category", "").lower() == category.lower()]
    return {"products": products, "count": len(products)}


@router.get("/search")
async def search_products(
    query: str = Query(..., min_length=1, description="Search query"),
    category: str | None = Query(None, description="Category filter"),
    max_price: float | None = Query(None, description="Maximum price"),
    service: ProductServiceDep = None,
) -> dict[str, Any]:
    """Search products by query string."""
    products = service.search_products(query, category=category, max_price=max_price)
    return {"products": products, "count": len(products)}


@router.get("/{product_id}")
async def get_product(product_id: int, service: ProductServiceDep) -> dict[str, Any]:
    """Get a single product by ID."""
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return product


@router.get("/categories/list")
async def get_categories(service: ProductServiceDep) -> dict[str, Any]:
    """Get all distinct product categories."""
    categories = service.get_categories()
    return {"categories": categories}
