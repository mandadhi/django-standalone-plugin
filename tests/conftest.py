"""Shared helpers. The suite is offline, needs only pytest and PyYAML, and runs from this folder alone."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = "django-engineering"
MARKETPLACE = "django-engineering-standalone"
ROOT_VAR = "${CLAUDE_PLUGIN_ROOT}"

SPECIALISTS = ["django-project-analyzer", "django-architecture-agent", "django-model-agent", "django-api-agent",
               "django-security-agent", "django-testing-agent", "django-performance-agent",
               "django-documentation-agent", "django-code-review-agent"]
ORCHESTRATOR = "django-orchestrator"
AGENTS = sorted(SPECIALISTS + [ORCHESTRATOR])
COMMANDS = sorted(["django-analyze", "django-design", "django-model", "django-api", "django-security", "django-test",
                   "django-optimize", "django-document", "django-review", "orchestrate"])
SKILLS = sorted(["django-architecture", "django-core", "django-data-processing", "django-frontend",
                 "django-integrations", "django-orm", "django-performance", "django-report-generation",
                 "django-rest-framework", "django-security-engineering", "django-testing", "postgresql-engineering"])
RULES = sorted(["django-api-standards", "django-coding-standards", "django-configuration-standards",
                "django-database-standards", "django-dependency-standards", "django-documentation-standards",
                "django-logging-standards", "django-model-standards", "django-performance-standards",
                "django-project-structure", "django-security-standards", "django-testing-standards"])
TEMPLATES = sorted(["api-specification", "architecture-decision-record", "architecture-design", "code-review-report",
                    "django-model-specification", "implementation-plan", "migration-plan", "performance-assessment",
                    "project-analysis", "security-assessment", "technical-documentation", "test-plan"])
REFERENCES = sorted(["django-api-design-checklist", "django-migration-safety", "django-performance-checklist",
                     "django-project-discovery", "django-security-checklist", "django-testing-strategy",
                     "django-version-compatibility"])
HARNESS_COMMANDS = ["setup-harness", "harness-status", "enable-harness", "disable-harness", "doctor"]

#: Declared tools of every agent (the ceiling). Mirrors agents/<id>.md frontmatter; a change here must be deliberate.
EXPECTED_TOOLS = {
    "django-project-analyzer": ("Read", "Grep", "Glob", "Bash"),
    "django-code-review-agent": ("Read", "Grep", "Glob", "Bash"),
    "django-documentation-agent": ("Read", "Write", "Edit", "Grep", "Glob"),
    "django-security-agent": ("Read", "Write", "Edit", "Grep", "Glob", "Bash"),
    "django-architecture-agent": ("Read", "Write", "Edit", "Grep", "Glob", "Bash"),
    "django-model-agent": ("Read", "Write", "Edit", "Grep", "Glob", "Bash"),
    "django-api-agent": ("Read", "Write", "Edit", "Grep", "Glob", "Bash"),
    "django-testing-agent": ("Read", "Write", "Edit", "Grep", "Glob", "Bash"),
    "django-performance-agent": ("Read", "Write", "Edit", "Grep", "Glob", "Bash"),
    ORCHESTRATOR: ("Agent", "Read", "Grep", "Glob", "Bash"),
}
EXPECTED_MODES = {
    "django-project-analyzer": "read-only", "django-code-review-agent": "read-only", ORCHESTRATOR: "read-only",
    "django-documentation-agent": "documentation-only", "django-security-agent": "confirm-writes",
    "django-architecture-agent": "workspace-write", "django-model-agent": "workspace-write",
    "django-api-agent": "workspace-write", "django-testing-agent": "workspace-write",
    "django-performance-agent": "workspace-write",
}

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", ".venv", "venv"}


def read(path: Path) -> str:
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


def frontmatter(path: Path) -> dict:
    match = _FRONTMATTER.match(read(path))
    assert match, f"{path.relative_to(ROOT)}: no YAML frontmatter"
    return yaml.safe_load(match.group(1)) or {}


def as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(part).strip() for part in value]


def all_files() -> list[Path]:
    found = []
    for path in sorted(ROOT.rglob("*")):
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.is_file() or path.is_symlink():
            found.append(path)
    return found


def text_files() -> list[Path]:
    suffixes = {".md", ".json", ".yaml", ".yml", ".py", ".txt", ".ini", ".toml", ""}
    return [p for p in all_files() if p.suffix in suffixes and p.is_file()]


def plugin_json() -> dict:
    return json.loads(read(ROOT / ".claude-plugin" / "plugin.json"))


def marketplace_json() -> dict:
    return json.loads(read(ROOT / ".claude-plugin" / "marketplace.json"))


def policy() -> dict:
    return json.loads(read(ROOT / "hooks" / "security-policy.json"))


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT
