from agents.orchestration.title_normalize import normalize_task_title


def test_normalize_task_title_strips_markdown() -> None:
    assert normalize_task_title("**Đau bụng**") == "Đau bụng"


def test_normalize_task_title_rejects_too_short() -> None:
    assert normalize_task_title("Đ") is None
    assert normalize_task_title("ab") is None


def test_normalize_task_title_accepts_vietnamese() -> None:
    assert normalize_task_title("Đau bụng") == "Đau bụng"
