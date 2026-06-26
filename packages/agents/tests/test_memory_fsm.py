import pytest
from agents.memory.state_machine import WorkflowFSM


def test_valid_transitions() -> None:
    WorkflowFSM.validate_transition("", "create-chat")
    WorkflowFSM.validate_transition("", "create-dashboard")
    WorkflowFSM.validate_transition("create-chat", "plan-dashboard")
    WorkflowFSM.validate_transition("create-chat", "create-dashboard")
    WorkflowFSM.validate_transition("plan-dashboard", "create-dashboard")
    WorkflowFSM.validate_transition("create-dashboard", "edit-dashboard")
    WorkflowFSM.validate_transition("create-dashboard", "repair-dashboard")
    WorkflowFSM.validate_transition("repair-dashboard", "create-dashboard")
    WorkflowFSM.validate_transition("edit-dashboard", "edit-dashboard")


def test_invalid_transitions() -> None:
    with pytest.raises(ValueError, match="Invalid workflow transition"):
        WorkflowFSM.validate_transition("edit-dashboard", "create-chat")
    with pytest.raises(ValueError, match="Invalid workflow transition"):
        WorkflowFSM.validate_transition("create-chat", "repair-dashboard")
    with pytest.raises(ValueError, match="Invalid workflow transition"):
        WorkflowFSM.validate_transition("repair-dashboard", "create-chat")
