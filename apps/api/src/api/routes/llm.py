from __future__ import annotations

from core.llm.budget import budget_response
from fastapi import APIRouter

router = APIRouter(prefix="/v1/llm", tags=["llm"])


@router.get("/budget")
async def get_budget() -> dict:  # type: ignore[type-arg]
    return budget_response()
