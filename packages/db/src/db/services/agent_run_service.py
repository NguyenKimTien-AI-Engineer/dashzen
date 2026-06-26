import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.agent_run import AgentRun

_ACTIVITY_RESULT_MAX = 2000
_ACTIVITY_COUNT_MAX = 200


def _truncate_activity(activity: dict) -> dict:  # type: ignore[type-arg]
    result = activity.get("result", "")
    if isinstance(result, str) and len(result) > _ACTIVITY_RESULT_MAX:
        activity = {**activity, "result": result[:_ACTIVITY_RESULT_MAX]}
    return activity


async def upsert_agent_run(
    db: AsyncSession,
    *,
    message_id: uuid.UUID,
    call_id: uuid.UUID,
    name: str,
    activities: list[dict],  # type: ignore[type-arg]
    status: str,
    summary: str | None = None,
) -> AgentRun:
    safe_activities = [_truncate_activity(a) for a in activities[:_ACTIVITY_COUNT_MAX]]
    stmt = (
        insert(AgentRun)
        .values(
            message_id=message_id,
            call_id=call_id,
            name=name,
            activities=safe_activities,
            status=status,
            summary=summary,
        )
        .on_conflict_do_update(
            constraint="uq_agent_runs_message_call",
            set_={"activities": safe_activities, "status": status, "summary": summary},
        )
        .returning(AgentRun)
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.scalar_one()


async def get_agent_runs(db: AsyncSession, message_id: uuid.UUID) -> Sequence[AgentRun]:
    result = await db.execute(select(AgentRun).where(AgentRun.message_id == message_id))
    return result.scalars().all()
