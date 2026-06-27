from __future__ import annotations

from pathlib import Path

import pytest
from core.schemas.dashboard_spec import parse_spec_md, validate_dashboard_html, validate_page_tsx

_FIXTURES = Path(__file__).resolve().parent.parent / "src" / "eval" / "fixtures"


def test_valid_spec_parses() -> None:
    content = (_FIXTURES / "valid_spec.md").read_text()
    spec = parse_spec_md(content)
    assert spec.name == "Revenue Dashboard"
    assert len(spec.widgets) >= 2
    assert len(spec.metrics) >= 2
    assert spec.widgets[0].type == "kpi"


def test_invalid_spec_missing_widgets() -> None:
    content = (_FIXTURES / "invalid_spec.md").read_text()
    with pytest.raises(ValueError, match="at least one widget"):
        parse_spec_md(content)


def test_valid_dashboard_html() -> None:
    content = (_FIXTURES / "valid_dashboard.html").read_text()
    validate_dashboard_html(content)


def test_invalid_dashboard_html_missing_marker() -> None:
    content = (
        '<!DOCTYPE html><html><head>'
        '<script src="https://cdn.tailwindcss.com"></script>'
        '<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>'
        '</head><body><h1>Hi</h1></body></html>'
    )
    with pytest.raises(ValueError, match="builder"):
        validate_dashboard_html(content)


def test_valid_page_tsx() -> None:
    content = (_FIXTURES / "valid_page.tsx").read_text()
    validate_page_tsx(content)


def test_invalid_page_tsx_unbalanced() -> None:
    content = (_FIXTURES / "invalid_page.tsx").read_text()
    with pytest.raises(ValueError):
        validate_page_tsx(content)


def test_spec_requires_metrics_glossary() -> None:
    content = """---
name: No Metrics
---
# Widgets
## w1
- **type:** kpi
- **title:** KPI
- **metric:** test
"""
    with pytest.raises(ValueError, match="at least one metric"):
        parse_spec_md(content)
