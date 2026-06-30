from __future__ import annotations

from core.llm.types import ToolDefinition
from db.services.task_service import sync_task_type_if_upgrade

from tools.context import ToolContext

DEFINITION = ToolDefinition(
    name="set_memory",
    description=(
        "Transition the workflow to a new phase and receive the instructions for that phase. "
        "Call this when the current phase is complete and the next phase must begin — "
        "for example, moving from plan-dashboard to create-dashboard, "
        "or from create-dashboard to edit-dashboard. "
        "Only `phase` is required; `type` is inferred from the phase name if omitted."
    ),
    parameters={
        "type": "object",
        "properties": {
            "phase": {
                "type": "string",
                "description": (
                    "Target phase: 'plan-dashboard' | 'create-dashboard' | "
                    "'edit-dashboard' | 'repair-dashboard'"
                ),
            },
            "type": {
                "type": "string",
                "description": (
                    "Workflow type: 'dashboard' (optional — inferred from phase if omitted)"
                ),
            },
        },
        "required": ["phase"],
    },
)


def _infer_type(phase: str, current_type: str) -> str:
    """Derive workflow type from phase name; fall back to current type."""
    if "dashboard" in phase:
        return "dashboard"
    return current_type or "chat"


async def execute(args: dict, ctx: ToolContext) -> str:  # type: ignore[type-arg]
    from agents.memory.memory_file import read_memory, write_memory
    from agents.memory.state_machine import WorkflowFSM
    from agents.streaming.events import TaskMetaEvent

    phase: str = str(args.get("phase", "")).strip()
    if not phase:
        return "[Error] 'phase' is required."

    current = await read_memory(ctx.db, ctx.task_id, ctx.artifact_buffer)

    # type is optional — infer from phase name if not explicitly provided
    type_: str = str(args.get("type", "")).strip() or _infer_type(phase, current.type)

    try:
        WorkflowFSM.validate_transition(current.phase, phase)
    except ValueError as exc:
        return f"[Error] {exc}"

    workflow_content = await write_memory(ctx.db, ctx.task_id, type_, phase, ctx.artifact_buffer)
    ctx.read_cache.invalidate_workspace_listing()

    if current.type != type_:
        upgraded = await sync_task_type_if_upgrade(ctx.db, ctx.task_id, type_)
        if upgraded:
            ctx.emit(TaskMetaEvent(task_type=type_))

    return workflow_content or f"Memory updated to {type_}/{phase}."
