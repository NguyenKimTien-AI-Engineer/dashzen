from __future__ import annotations

from core.llm.types import ToolDefinition

from tools.context import ToolContext

DEFINITION = ToolDefinition(
    name="spawn_agent",
    description=(
        "Delegate a focused task to a specialist agent and wait for the result. "
        "The agent cannot see the conversation — the task description must be fully self-contained. "
        "Available agents: dashboard-planner (writes spec.md), data-binder (writes bindings.md), "
        "layout-designer (writes layout.md), dashboard-builder (writes dashboard.html), "
        "dashboard-critic (writes review.md). "
        "Call each agent at most once per user message."
    ),
    parameters={
        "type": "object",
        "properties": {
            "agent": {
                "type": "string",
                "description": "Agent name: dashboard-planner | data-binder | layout-designer | dashboard-builder | dashboard-critic",
            },
            "task": {
                "type": "string",
                "description": "Self-contained task description. Include the user brief, which files to read, and exactly what to produce. Do not reference the conversation.",
            },
        },
        "required": ["agent", "task"],
    },
)


async def execute(args: dict, ctx: ToolContext) -> str:  # type: ignore[type-arg]
    # Handled by orchestration layer directly in exec_parallel.py
    return "[Error] spawn_agent must be handled by the orchestration layer."
