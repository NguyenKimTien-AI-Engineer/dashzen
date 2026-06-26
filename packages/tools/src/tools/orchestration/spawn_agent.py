from __future__ import annotations

from core.llm.types import ToolDefinition

from tools.context import ToolContext

DEFINITION = ToolDefinition(
    name="spawn_agent",
    description="Spawn a specialist agent to perform a focused task.",
    parameters={
        "type": "object",
        "properties": {
            "agent": {"type": "string", "description": "Agent name (e.g. dashboard-planner)"},
            "task": {"type": "string", "description": "Task description for the agent"},
        },
        "required": ["agent", "task"],
    },
)


async def execute(args: dict, ctx: ToolContext) -> str:  # type: ignore[type-arg]
    # Handled by orchestration layer directly in exec_parallel.py
    return "[Error] spawn_agent must be handled by the orchestration layer."
