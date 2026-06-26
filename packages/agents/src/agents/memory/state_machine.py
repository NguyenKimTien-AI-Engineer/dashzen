from __future__ import annotations

from dataclasses import dataclass

ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "": ["create-chat", "create-dashboard"],
    "create-chat": ["plan-dashboard", "create-dashboard"],
    "plan-dashboard": ["create-dashboard"],
    "create-dashboard": ["edit-dashboard", "repair-dashboard"],
    "repair-dashboard": ["create-dashboard", "edit-dashboard"],
    "edit-dashboard": ["edit-dashboard", "repair-dashboard"],
}


@dataclass(frozen=True)
class MemoryState:
    type: str
    phase: str


class WorkflowFSM:
    ALLOWED_TRANSITIONS = ALLOWED_TRANSITIONS

    @staticmethod
    def validate_transition(current_phase: str, new_phase: str) -> None:
        allowed = ALLOWED_TRANSITIONS.get(current_phase, [])
        if new_phase not in allowed:
            raise ValueError(
                f"Invalid workflow transition: '{current_phase}' -> '{new_phase}'. "
                f"Allowed: {allowed or 'none'}"
            )
