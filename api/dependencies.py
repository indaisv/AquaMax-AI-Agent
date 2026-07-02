"""FastAPI dependencies for dependency injection."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from src.core.agent import AquaMaxAgent, get_agent
from src.services.customer_service import CustomerService
from src.services.product_service import ProductService


async def get_agent_dependency() -> AquaMaxAgent:
    """Injectable AquaMaxAgent instance."""
    return get_agent()


async def get_customer_service() -> CustomerService:
    """Injectable CustomerService instance."""
    return CustomerService()


async def get_product_service() -> ProductService:
    """Injectable ProductService instance."""
    return ProductService()


# Typed dependencies for route injection
AgentDep = Annotated[AquaMaxAgent, Depends(get_agent_dependency)]
CustomerServiceDep = Annotated[CustomerService, Depends(get_customer_service)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
