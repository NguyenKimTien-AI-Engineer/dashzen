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
        "or from create-dashboard to edit-dashboard."
    ),
    parameters={
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "description": "Workflow type: 'chat' or 'dashboard'",
            },
            "phase": {
                "type": "string",
                "description": (
                    "Target phase: 'plan-dashboard' | 'create-dashboard' | "
                    "'edit-dashboard' | 'repair-dashboard'"
                ),
            },
        },
        "required": ["type", "phase"],
    },
)


async def execute(args: dict, ctx: ToolContext) -> str:  # type: ignore[type-arg]
    from agents.memory.memory_file import read_memory, write_memory
    from agents.memory.state_machine import WorkflowFSM
    from agents.streaming.events import TaskMetaEvent

    type_: str = str(args.get("type", "")).strip()
    phase: str = str(args.get("phase", "")).strip()
    if not type_ or not phase:
        return "[Error] Both 'type' and 'phase' are required."

    current = await read_memory(ctx.db, ctx.task_id, ctx.artifact_buffer)
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
