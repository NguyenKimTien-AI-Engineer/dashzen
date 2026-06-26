from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import yaml
from core.llm.types import ToolDefinition

from agents.registry.cache import get_cached
from agents.registry.schema import AgentDefinition

_PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts"


def _get_prompts_dir() -> Path:
    env_override = os.environ.get("DASHZEN_PROMPTS_DIR")
    if env_override:
        return Path(env_override)
    return _PROMPTS_DIR


def _parse_frontmatter(text: str) -> tuple[dict, str]:  # type: ignore[type-arg]
    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = pattern.match(text)
    if not match:
        return {}, text
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        data = {}
    body = text[match.end() :]
    return data, body


def _coerce_str_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _normalize_frontmatter(front: dict) -> dict:  # type: ignore[type-arg]
    for key in ("tools", "disallowedTools"):
        if key in front:
            front[key] = _coerce_str_list(front[key])
    return front


def _load_agent_file(path: str) -> AgentDefinition:
    content = Path(path).read_text(encoding="utf-8")
    front, body = _parse_frontmatter(content)
    front = _normalize_frontmatter(front)
    front["prompt"] = body.strip()
    if "displayName" not in front and "name" in front:
        front["displayName"] = front["name"]
    return AgentDefinition.model_validate(front)


def load_agent_registry() -> list[AgentDefinition]:
    agents_dir = _get_prompts_dir() / "agents"
    if not agents_dir.exists():
        return []
    definitions = []
    for md_file in sorted(agents_dir.glob("*.md")):
        path = str(md_file)
        defn = get_cached(path, _load_agent_file)
        if isinstance(defn, AgentDefinition):
            definitions.append(defn)
    return definitions


def get_agent(name: str) -> AgentDefinition | None:
    for defn in load_agent_registry():
        if defn.name == name:
            return defn
    return None


def load_system_prompt(variant: str = "main") -> str:
    path = _get_prompts_dir() / "system" / f"system-{variant}.md"
    if not path.exists():
        return ""
    _, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
    return body.strip()


def load_system_tools(variant: str = "main") -> list[str]:
    """Orchestrator tool names from system prompt frontmatter (single source of truth)."""
    path = _get_prompts_dir() / "system" / f"system-{variant}.md"
    if not path.exists():
        return []
    front, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
    front = _normalize_frontmatter(front)
    tools = front.get("tools", [])
    return tools if isinstance(tools, list) else _coerce_str_list(tools)


def build_orchestrator_tool_definitions(variant: str = "main") -> list[ToolDefinition]:
    from agents.tools.pipeline import get_tool_definition

    definitions: list[ToolDefinition] = []
    for name in load_system_tools(variant):
        definition = get_tool_definition(name)
        if definition is not None:
            definitions.append(definition)
    return definitions


def load_workflow(type_: str, phase: str) -> str:
    path = _get_prompts_dir() / "workflows" / type_ / f"{phase}.md"
    if not path.exists():
        return ""
    _, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
    return body.strip()


def load_prompt_file(*parts: str) -> str:
    path = _get_prompts_dir().joinpath(*parts)
    if not path.exists():
        return ""
    _, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
    return body.strip()


def load_widget_catalog() -> list[dict[str, Any]]:
    path = _get_prompts_dir() / "catalog" / "widgets.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]
