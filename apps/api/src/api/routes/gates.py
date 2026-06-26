from __future__ import annotations

import uuid

from agents.gates.gate_service import resolve_ask_gate, resolve_gate
from db.models.user import User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, require_task
from api.schemas.gates import AskGateRequest, GateResolveResponse, ToolGateRequest

router = APIRouter(prefix="/v1/tasks", tags=["gates"])


@router.post("/{task_id}/gates/tool", response_model=GateResolveResponse)
async def resolve_tool_gate(
    task_id: uuid.UUID,
    body: ToolGateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GateResolveResponse:
    await require_task(task_id, user, db)
    decision = "approved" if body.approved else "rejected"
    resolved = await resolve_gate(
        str(task_id),
        body.call_id,
        decision,
        body.feedback or "",
    )
    if not resolved:
        raise HTTPException(status_code=404, detail="Gate not found or already resolved")
    return GateResolveResponse(resolved=True)


@router.post("/{task_id}/gates/ask", response_model=GateResolveResponse)
async def resolve_ask_gate_endpoint(
    task_id: uuid.UUID,
    body: AskGateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GateResolveResponse:
    await require_task(task_id, user, db)
    resolved = await resolve_ask_gate(str(task_id), body.call_id, body.answer)
    if not resolved:
        raise HTTPException(status_code=404, detail="Ask gate not found or already resolved")
    return GateResolveResponse(resolved=True)
