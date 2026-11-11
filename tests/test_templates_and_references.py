"""Output templates and shared references: format, placeholders, cross-links."""

from __future__ import annotations

import re

from conftest import REFERENCES, ROOT, SPECIALISTS, TEMPLATES, frontmatter, as_list, read

HEADER_PLACEHOLDERS = {"subject", "project_name", "scope", "prepared_by", "date", "document_status", "sources"}


def test_template_format() -> None:
    for name in TEMPLATES:
        path = ROOT / "templates" / f"{name}.template.md"
        meta = frontmatter(path)
        assert meta["name"] == name and meta["kind"] == "output-template", name
        assert set(as_list(meta["agents"])) <= set(SPECIALISTS), name
        body = read(path)
        for section in ("Purpose", "When to use", "Placeholders", "Sections", "Filling rules", "Output structure",
                        "Completion checklist"):
            assert f"## {section}" in body, (name, section)


def test_template_placeholders_are_declared_and_used() -> None:
    for name in TEMPLATES:
        body = read(ROOT / "templates" / f"{name}.template.md")
        skeleton = body.split("## Output structure", 1)[1]
        used = set(re.findall(r"\{\{([a-z_]+)\}\}", skeleton))
        declared_block = body.split("## Placeholders", 1)[1].split("\n## ", 1)[0]
        declared = set(re.findall(r"`\{\{([a-z_]+)\}\}`", declared_block))
        assert HEADER_PLACEHOLDERS <= used, (name, HEADER_PLACEHOLDERS - used)
        assert used <= declared, (name, used - declared)


def test_templates_name_existing_commands_and_agents() -> None:
    commands = {p.stem for p in (ROOT / "commands").glob("*.md")}
    for name in TEMPLATES:
        meta = frontmatter(ROOT / "templates" / f"{name}.template.md")
        assert set(as_list(meta["commands"])) <= commands, name


def test_every_template_is_used_by_one_of_its_agents() -> None:
    for name in TEMPLATES:
        meta = frontmatter(ROOT / "templates" / f"{name}.template.md")
        for agent in as_list(meta["agents"]):
            body = read(ROOT / "agents" / f"{agent}.md")
            line = re.search(r"^- Templates \([^)]*\): (.+)$", body, re.M).group(1)
            assert f"`{name}`" in line, (name, agent)


def test_template_readme_keeps_the_filling_conventions_and_no_runtime_prompt() -> None:
    body = read(ROOT / "templates" / "README.md")
    assert "## Filling conventions" in body
    assert "agent-task" not in body and "prompt.py" not in body


def test_reference_format() -> None:
    for name in REFERENCES:
        path = ROOT / "references" / f"{name}.md"
        meta = frontmatter(path)
        assert meta["name"] == name and meta["kind"] == "shared-reference", name
        assert set(as_list(meta["agents"])) <= set(SPECIALISTS), name
        body = read(path)
        for section in ("Purpose", "Scope", "How to use"):
            assert f"## {section}" in body, (name, section)
        assert re.search(r"\]\(\.\./skills/[^)]+\)", body) and re.search(r"\]\(\.\./rules/[^)]+\)", body), \
            f"{name}: must link at least one skill and one rule"


def test_every_reference_is_used_by_one_of_its_agents() -> None:
    for name in REFERENCES:
        for agent in as_list(frontmatter(ROOT / "references" / f"{name}.md")["agents"]):
            body = read(ROOT / "agents" / f"{agent}.md")
            line = re.search(r"^- References \([^)]*\): (.+)$", body, re.M).group(1)
            assert f"`{name}`" in line, (name, agent)
