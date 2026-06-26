from __future__ import annotations


def build_context_block(
    memory_content: str,
    workflow_content: str,
    user_instructions: str = "",
) -> str:
    parts = [f"# MEMORY\n{memory_content.strip() or '(empty)'}"]

    user = user_instructions.strip()
    if user:
        parts.append(f"# USER\n{user}")

    if workflow_content.strip():
        parts.append(f"# WORKFLOW\n{workflow_content.strip()}")

    return "\n\n".join(parts)
