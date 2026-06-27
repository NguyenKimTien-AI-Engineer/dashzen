from __future__ import annotations

import re

import yaml
from pydantic import BaseModel, Field

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_WIDGET_SECTION = re.compile(r"^##\s+(\S+)\s*$", re.MULTILINE)
_KV_LINE = re.compile(r"^-\s+\*\*(\w[\w\s]*?):\*\*\s*(.+)$", re.MULTILINE)
_TABLE_ROW = re.compile(r"^\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|")


class FilterSpec(BaseModel):
    id: str
    label: str
    type: str
    field: str
    default: str | None = None


class WidgetSpec(BaseModel):
    id: str
    type: str
    title: str
    metric: str
    fields: list[str] = Field(default_factory=list)
    aggregation: str | None = None
    format: str | None = None
    description: str | None = None


class MetricSpec(BaseModel):
    metric_id: str
    label: str
    definition: str
    source_field: str
    aggregation: str


class DashboardSpec(BaseModel):
    name: str
    language: str = "en"
    version: int = 1
    widgets: list[WidgetSpec] = Field(min_length=1)
    metrics: list[MetricSpec] = Field(min_length=1)
    filters: list[FilterSpec] = Field(default_factory=list)


def _parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    match = _FRONTMATTER.match(text)
    if not match:
        return {}, text
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return data, text[match.end() :]


def _section(body: str, heading: str) -> str:
    pattern = re.compile(rf"^#{{{1,4}}}\s+{re.escape(heading)}\s*$", re.MULTILINE | re.IGNORECASE)
    match = pattern.search(body)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^#{1,4}\s+", body[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(body)
    return body[start:end]


def _parse_table(section: str, min_cols: int) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < min_cols:
            continue
        if cells[0].lower() in ("id", "metric_id") or set(cells) <= {"-", ""}:
            continue
        rows.append(cells)
    return rows


def _parse_widgets(body: str) -> list[WidgetSpec]:
    widgets_section = _section(body, "Widgets")
    if not widgets_section:
        return []

    widgets: list[WidgetSpec] = []
    parts = _WIDGET_SECTION.split(widgets_section)
    if len(parts) < 2:
        return []

    for widget_id, block in zip(parts[1::2], parts[2::2], strict=False):
        fields: dict[str, str] = {}
        for key, value in _KV_LINE.findall(block):
            fields[key.strip().lower().replace(" ", "_")] = value.strip()
        widget_type = fields.get("type", "")
        title = fields.get("title", widget_id)
        metric = fields.get("metric", title)
        raw_fields = fields.get("field(s)", fields.get("fields", ""))
        field_list = [f.strip() for f in raw_fields.split(",") if f.strip()]
        widgets.append(
            WidgetSpec(
                id=widget_id.strip(),
                type=widget_type,
                title=title,
                metric=metric,
                fields=field_list,
                aggregation=fields.get("aggregation"),
                format=fields.get("format"),
                description=fields.get("description"),
            )
        )
    return [w for w in widgets if w.type]


def _parse_metrics(body: str) -> list[MetricSpec]:
    section = _section(body, "Metrics glossary")
    rows = _parse_table(section, 5)
    metrics: list[MetricSpec] = []
    for row in rows:
        metrics.append(
            MetricSpec(
                metric_id=row[0],
                label=row[1],
                definition=row[2],
                source_field=row[3],
                aggregation=row[4],
            )
        )
    return metrics


def _parse_filters(body: str) -> list[FilterSpec]:
    section = _section(body, "Filters")
    rows = _parse_table(section, 5)
    filters: list[FilterSpec] = []
    for row in rows:
        filters.append(
            FilterSpec(
                id=row[0],
                label=row[1],
                type=row[2],
                field=row[3],
                default=row[4] or None,
            )
        )
    return filters


def parse_spec_md(text: str) -> DashboardSpec:
    frontmatter, body = _parse_frontmatter(text)
    widgets = _parse_widgets(body)
    metrics = _parse_metrics(body)
    if not widgets:
        raise ValueError("spec.md must define at least one widget")
    if not metrics:
        raise ValueError("spec.md must define at least one metric in Metrics glossary")
    return DashboardSpec(
        name=str(frontmatter.get("name") or "Untitled"),
        language=str(frontmatter.get("language") or "en"),
        version=int(frontmatter.get("version") or 1),
        widgets=widgets,
        metrics=metrics,
        filters=_parse_filters(body),
    )


def validate_dashboard_html(content: str) -> None:
    stripped = content.strip()
    if not stripped:
        raise ValueError("dashboard.html is empty")
    lower = stripped.lower()
    if "<!doctype html" not in lower and "<html" not in lower:
        raise ValueError("dashboard.html must be valid HTML5 (<!DOCTYPE html>)")
    if "tailwindcss.com" not in lower and "tailwind" not in lower:
        raise ValueError("dashboard.html must include Tailwind CSS")
    if "echarts" not in lower:
        raise ValueError("dashboard.html must include ECharts for chart rendering")
    if "<!-- builder -->" not in stripped:
        raise ValueError("dashboard.html must contain <!-- builder --> marker")


def validate_page_tsx(content: str) -> None:
    """Legacy React output — still accepted for older tasks."""
    stripped = content.strip()
    if not stripped:
        raise ValueError("page.tsx is empty")
    if "export default" not in stripped and "export function" not in stripped:
        raise ValueError("page.tsx must export a default or named component")
    open_braces = stripped.count("{")
    close_braces = stripped.count("}")
    if open_braces != close_braces:
        raise ValueError("page.tsx has unbalanced braces")


def validate_export_files(files: dict[str, str]) -> None:
    """Fail-closed validation before zip export."""
    html_content = files.get("dashboard.html")
    tsx_content = files.get("page.tsx")
    if not html_content and not tsx_content:
        return
    spec_content = files.get("spec.md")
    if not spec_content:
        raise ValueError("Cannot export: dashboard output exists but spec.md is missing")
    parse_spec_md(spec_content)
    if html_content:
        validate_dashboard_html(html_content)
    elif tsx_content:
        validate_page_tsx(tsx_content)
