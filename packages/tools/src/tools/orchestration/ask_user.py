from __future__ import annotations

from core.llm.types import ToolDefinition

from tools.context import ToolContext

DEFINITION = ToolDefinition(
    name="ask_user",
    description="Ask the user a question and wait for their answer.",
    parameters={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Question to present to the user",
            },
        },
        "required": ["question"],
    },
)


async def execute(args: dict, ctx: ToolContext) -> str:  # type: ignore[type-arg]
    from agents.gates.gate_service import init_ask_gate, register_ask_gate
    from agents.streaming.events import MainAskEvent

    question: str = str(args.get("question", "")).strip()
    if not question:
        return "[Error] question is required."

    call_id = ctx.current_call_id or str(ctx.task_id)
    task_id = str(ctx.task_id)

    await init_ask_gate(task_id, call_id)
    ctx.emit(MainAskEvent(call_id=call_id, question=question))

    answer = await register_ask_gate(task_id, call_id)
    if not answer:
        return "[Error] No answer received (gate expired or cancelled)."
    return answer
