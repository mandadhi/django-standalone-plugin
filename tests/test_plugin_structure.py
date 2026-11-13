"""Structural validation: manifests, component inventory, names, paths, links."""

from __future__ import annotations

import re

import pytest

from conftest import (AGENTS, COMMANDS, EXPECTED_TOOLS, HARNESS_COMMANDS, MARKETPLACE, ORCHESTRATOR, PLUGIN, REFERENCES,
                      ROOT, ROOT_VAR, RULES, SKILLS, SPECIALISTS, TEMPLATES, all_files, as_list, frontmatter,
                      marketplace_json, plugin_json, read, text_files)


def test_plugin_manifest_is_valid() -> None:
    data = plugin_json()
    assert data["name"] == PLUGIN
    assert re.fullmatch(r"\d+\.\d+\.\d+", data["version"])
    assert data["description"].strip() and data["author"]["name"]
    assert data["skills"] == ["./skills/", "./rules/"]
    assert "hooks" not in data, "hooks/hooks.json is loaded by default; declaring it loads it twice"
    for forbidden in ("mcpServers", "lspServers", "settings", "permissions", "userConfig", "outputStyles"):
        assert forbidden not in data, f"plugin.json must not declare {forbidden}"
    assert data["agents"] == [f"./agents/{a}.md" for a in AGENTS]
    assert data["commands"] == [f"./commands/{c}.md" for c in COMMANDS]
    for path in data["agents"] + data["commands"]:
        assert (ROOT / path).is_file(), path


def test_marketplace_manifest_is_valid_and_independent() -> None:
    data = marketplace_json()
    assert data["name"] == MARKETPLACE
    assert data["name"] != "django-agentic-engineering", "must not reuse the integrated distribution's identifier"
    assert data["owner"]["name"]
    assert [p["name"] for p in data["plugins"]] == [PLUGIN]
    entry = data["plugins"][0]
    assert entry["source"] == "./" and (ROOT / ".claude-plugin" / "plugin.json").is_file()
    assert entry["version"] == plugin_json()["version"], "plugin.json and marketplace.json versions must agree"


def test_directory_structure() -> None:
    for folder in ("agents", "commands", "skills", "rules", "templates", "references", "hooks", "config", "docs",
                   "tests", ".claude-plugin"):
        assert (ROOT / folder).is_dir(), folder
    for name in ("README.md", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md", "TEAM_HANDOFF.md", ".gitignore",
                 "CANONICAL-MANIFEST.json", "config/orchestration-policy.yaml", "hooks/hooks.json",
                 "hooks/django_pack_guard.py", "hooks/shell_syntax.py", "hooks/security-policy.json",
                 "docs/installation.md", "docs/usage.md", "docs/architecture.md", "docs/security.md",
                 "docs/troubleshooting.md"):
        assert (ROOT / name).is_file(), name


def test_component_inventory_is_complete_and_exact() -> None:
    assert sorted(p.stem for p in (ROOT / "agents").glob("*.md")) == AGENTS, "agents/ holds agent files only"
    assert len(SPECIALISTS) == 9 and ORCHESTRATOR in AGENTS
    assert sorted(p.stem for p in (ROOT / "commands").glob("*.md") if p.stem != "README") == sorted(COMMANDS),         "commands/ holds the ten user-facing commands only"
    assert not (ROOT / "commands" / "commands").exists()
    assert sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")) == SKILLS
    assert sorted(p.parent.name for p in (ROOT / "rules").glob("*/SKILL.md")) == RULES
    assert sorted(p.name[: -len(".template.md")] for p in (ROOT / "templates").glob("*.template.md")) == TEMPLATES
    assert sorted(p.stem for p in (ROOT / "references").glob("*.md") if p.stem != "README") == REFERENCES
    assert (len(SKILLS), len(RULES), len(TEMPLATES), len(REFERENCES)) == (12, 12, 20, 10)
    # nothing else in the templates folder (the harness runtime prompt template is not distributed)
    assert sorted(p.name for p in (ROOT / "templates").iterdir()) == sorted(
        ["README.md"] + [f"{t}.template.md" for t in TEMPLATES])


def test_commands_are_thin_delegates_to_one_agent_each() -> None:
    expected = {"orchestrate": ORCHESTRATOR, "django-analyze": "django-project-analyzer",
                "django-design": "django-architecture-agent", "django-model": "django-model-agent",
                "django-api": "django-api-agent", "django-security": "django-security-agent",
                "django-test": "django-testing-agent", "django-optimize": "django-performance-agent",
                "django-document": "django-documentation-agent", "django-review": "django-code-review-agent"}
    assert sorted(expected) == sorted(COMMANDS)
    for command, agent in expected.items():
        text = read(ROOT / "commands" / f"{command}.md")
        assert frontmatter(ROOT / "commands" / f"{command}.md")["name"] == command
        assert f"`{agent}` subagent" in text or (command == "orchestrate" and "`django-orchestrator`" in text), command
    for name in HARNESS_COMMANDS:
        assert not list(ROOT.glob(f"**/{name}.md")), name


def test_rules_are_internal_and_never_commands() -> None:
    assert "./rules/" in plugin_json()["skills"] and not any("rules" in c for c in plugin_json()["commands"])
    for rule in RULES:
        assert frontmatter(ROOT / "rules" / rule / "SKILL.md").get("user-invocable") is False, rule
    for skill in SKILLS:
        # knowledge skills are internal too: hidden from the slash menu, still model-invocable and preloadable
        meta = frontmatter(ROOT / "skills" / skill / "SKILL.md")
        assert meta.get("user-invocable") is False and meta.get("disable-model-invocation") is not True, skill


def test_component_names_are_unique_across_kinds() -> None:
    """Agents, skills and rules share one namespace in Claude Code; a duplicate would shadow another component."""
    seen: dict[str, str] = {}
    for kind, names in (("agent", AGENTS), ("skill", SKILLS), ("rule", RULES)):
        for name in names:
            assert name not in seen, f"{kind} '{name}' collides with {seen[name]}"
            seen[name] = kind


@pytest.mark.parametrize("kind,names", [("skills", SKILLS), ("rules", RULES)])
def test_skill_and_rule_frontmatter(kind: str, names: list[str]) -> None:
    for name in names:
        meta = frontmatter(ROOT / kind / name / "SKILL.md")
        assert meta["name"] == name and str(meta["description"]).strip(), name


def test_agent_frontmatter_tools_and_preloaded_skills() -> None:
    known = {f"{PLUGIN}:{n}" for n in SKILLS + RULES}
    for agent in AGENTS:
        meta = frontmatter(ROOT / "agents" / f"{agent}.md")
        assert meta["name"] == agent and str(meta["description"]).strip()
        assert tuple(as_list(meta["tools"])) == EXPECTED_TOOLS[agent], f"{agent}: tools changed"
        skills = as_list(meta.get("skills"))
        assert skills, f"{agent}: no preloaded skills"
        assert set(skills) <= known, f"{agent}: unknown skills {set(skills) - known}"
        assert f"{PLUGIN}:django-security-standards" in skills, f"{agent}: must preload the security conduct rules"


def test_only_the_orchestrator_can_start_agents() -> None:
    for agent in SPECIALISTS:
        tools = as_list(frontmatter(ROOT / "agents" / f"{agent}.md")["tools"])
        assert "Agent" not in tools and "Task" not in tools, agent
    assert "Agent" in as_list(frontmatter(ROOT / "agents" / f"{ORCHESTRATOR}.md")["tools"])


def test_read_only_and_documentation_boundaries_in_agent_tools() -> None:
    for agent in ("django-project-analyzer", "django-code-review-agent", ORCHESTRATOR):
        assert not {"Write", "Edit", "MultiEdit", "NotebookEdit"} & set(EXPECTED_TOOLS[agent]), agent
    assert "Bash" not in EXPECTED_TOOLS["django-documentation-agent"]


GATED = ("django-model-agent", "django-api-agent", "django-testing-agent", "django-performance-agent",
         "django-security-agent", "django-architecture-agent", "django-documentation-agent")
HARNESS_WORDING = ("AgentTask", "AgentResult", "output directory", "dae.output_content", "/django-engineering:")


def test_writing_specialists_carry_their_own_approval_gate() -> None:
    """Agents are the only entry point, so the gate that used to live in a command must live in the agent."""
    for agent in GATED:
        body = read(ROOT / "agents" / f"{agent}.md")
        assert "## Approval gate" in body, agent
        if agent not in ("django-documentation-agent", "django-security-agent"):
            assert "AWAITING APPROVAL:" in body, agent


def test_agents_use_no_harness_or_command_wording() -> None:
    for agent in AGENTS:
        body = read(ROOT / "agents" / f"{agent}.md")
        for word in HARNESS_WORDING:
            assert word not in body, (agent, word)
        assert not re.search(r"(?<![\w/-])/django-[a-z]+", body), agent


def test_orchestrator_never_approves_for_the_user() -> None:
    body = read(ROOT / "agents" / f"{ORCHESTRATOR}.md")
    assert "## Approvals pass through you" in body and "AWAITING APPROVAL:" in body


# ---------------------------------------------------------------------- paths


def test_no_symlinks_and_nothing_escapes_the_root() -> None:
    root = ROOT.resolve()
    for path in all_files():
        assert not path.is_symlink(), f"symlink: {path.relative_to(ROOT)}"
        assert root in path.resolve().parents, path


_LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def test_markdown_links_resolve_inside_the_distribution() -> None:
    root = ROOT.resolve()
    broken = []
    for path in text_files():
        if path.suffix != ".md":
            continue
        for number, line in enumerate(read(path).splitlines(), 1):
            for target in _LINK.findall(line):
                if re.match(r"[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                    continue
                file_part = target.split("#", 1)[0]
                if not file_part:
                    continue
                resolved = (path.parent / file_part).resolve()
                if not resolved.exists() or (root != resolved and root not in resolved.parents):
                    broken.append(f"{path.relative_to(ROOT)}:{number} -> {target}")
    assert not broken, broken


def test_plugin_root_paths_resolve() -> None:
    pattern = re.compile(re.escape(ROOT_VAR) + r"/([A-Za-z0-9_./-]+)")
    missing = []
    for path in text_files():
        if path.parts[-2] == "tests":
            continue
        for match in pattern.finditer(read(path)):
            rel = match.group(1).rstrip(".")
            if rel.endswith("/") or "<" in rel:
                continue
            if not (ROOT / rel).exists():
                missing.append(f"{path.relative_to(ROOT)}: {rel}")
    assert not missing, missing


def test_agent_template_and_reference_citations_exist() -> None:
    templates, references = set(TEMPLATES), set(REFERENCES)
    for agent in SPECIALISTS:
        body = read(ROOT / "agents" / f"{agent}.md")
        cited_t = re.search(r"^- Templates \([^)]*\): (.+)$", body, re.M)
        cited_r = re.search(r"^- References \([^)]*\): (.+)$", body, re.M)
        assert cited_t and cited_r, agent
        for line, universe in ((cited_t, templates), (cited_r, references)):
            ids = set(re.findall(r"`([a-z-]+)`", line.group(1)))
            assert ids and ids <= universe, (agent, ids - universe)


def test_config_contains_only_the_policy_and_the_documentation_catalog() -> None:
    assert sorted(p.name for p in (ROOT / "config").rglob("*") if p.is_file()) == [
        "orchestration-policy.yaml", "sdlc-documentation-catalog.json"]


def test_gitignore_covers_secrets_and_caches() -> None:
    text = read(ROOT / ".gitignore")
    for entry in (".env", "*.pem", "*.key", "__pycache__/", ".pytest_cache/"):
        assert entry in text, entry
