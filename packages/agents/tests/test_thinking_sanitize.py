from agents.orchestration.thinking_sanitize import sanitize_thinking_for_display


def test_sanitize_removes_memory_blocks_keeps_reasoning() -> None:
    raw = (
        "The user asked for a creative essay about their mother.\n"
        "# MEMORY\nphase: create-chat\n"
        "I should decline because this is outside dashboard scope."
    )
    safe = sanitize_thinking_for_display(raw)
    assert "create-chat" not in safe
    assert "creative essay" in safe
    assert "decline" in safe


def test_sanitize_redacts_files_and_phases() -> None:
    raw = "Planning a chart. Reading workflows/create-dashboard/foo.md next."
    safe = sanitize_thinking_for_display(raw)
    assert "create-dashboard" not in safe
    assert ".md" not in safe
    assert "Planning a chart" in safe


def test_sanitize_allows_benign_reasoning() -> None:
    raw = "The user is asking for my name. I should answer briefly."
    assert sanitize_thinking_for_display(raw) == raw
