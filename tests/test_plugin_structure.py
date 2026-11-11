"""Structural validation: manifests, component inventory, names, paths, links."""

from __future__ import annotations

import re

import pytest

from conftest import (AGENTS, ENTRY_SKILLS, EXPECTED_TOOLS, HARNESS_COMMANDS, MARKETPLACE, ORCHESTRATOR, PLUGIN, REFERENCES,
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
    assert "commands" not in data, "agents are invoked by name; the plugin ships no slash commands"
    for path in data["agents"]:
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
    for folder in ("agents", "skills", "rules", "templates", "references", "hooks", "config", "docs",
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
    assert not (ROOT / "commands").exists(), "the plugin ships no commands folder"
    assert sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")) == sorted(SKILLS + ENTRY_SKILLS)
    assert sorted(p.parent.name for p in (ROOT / "rules").glob("*/SKILL.md")) == RULES
    assert sorted(p.name[: -len(".template.md")] for p in (ROOT / "templates").glob("*.template.md")) == TEMPLATES
    assert sorted(p.stem for p in (ROOT / "references").glob("*.md") if p.stem != "README") == REFERENCES
    assert (len(SKILLS), len(RULES), len(TEMPLATES), len(REFERENCES)) == (11, 12, 12, 7)
    # nothing else in the templates folder (the harness runtime prompt template is not distributed)
    assert sorted(p.name for p in (ROOT / "templates").iterdir()) == sorted(
        ["README.md"] + [f"{t}.template.md" for t in TEMPLATES])


def test_no_commands_anywhere() -> None:
    assert not (ROOT / "commands").exists()
    assert "commands" not in plugin_json()
    for name in HARNESS_COMMANDS:
        assert not list(ROOT.glob(f"**/{name}.md")), name


def test_component_names_are_unique_across_kinds() -> None:
    """Agents, skills and rules share one namespace in Claude Code; a duplicate would shadow another component."""
    seen: dict[str, str] = {}
    for kind, names in (("agent", AGENTS), ("skill", SKILLS + ENTRY_SKILLS), ("rule", RULES)):
        for name in names:
            assert name not in seen, f"{kind} '{name}' collides with {seen[name]}"
            seen[name] = kind


@pytest.mark.parametrize("kind,names", [("skills", SKILLS), ("rules", RULES)])
def test_skill_and_rule_frontmatter(kind: str, names: list[str]) -> None:
    for name in names:
        meta = frontmatter(ROOT / kind / name / "SKILL.md")
        assert meta["name"] == name and str(meta["description"]).strip(), name
        assert meta.get("user-invocable") is False, f"{kind}/{name} is internal knowledge and must not be a slash command"


def test_orchestrate_is_the_only_entry_point_and_holds_no_orchestration_logic() -> None:
    """`/django-engineering:orchestrate` hands the request to the orchestrator agent, which owns all routing."""
    path = ROOT / "skills" / "orchestrate" / "SKILL.md"
    meta = frontmatter(path)
    assert meta["name"] == "orchestrate" and str(meta["description"]).strip()
    assert meta.get("user-invocable", True) is not False, "the entry skill must stay in the / menu"
    assert meta.get("disable-model-invocation") is True, "the entry skill runs only when the user types it"
    assert not (ROOT / "skills" / "orchestrate" / "references").exists()
    body = read(path)
    assert "$ARGUMENTS" in body and f"{PLUGIN}:{ORCHESTRATOR}" in body
    for agent in SPECIALISTS:                     # routing belongs to the orchestrator and its policy
        assert agent not in body, f"entry skill names specialist {agent}"
    assert "Signals:" not in body and "max_delegations" not in body
    user_invocable = [p.parent.name for p in ROOT.glob("*/*/SKILL.md")
                      if frontmatter(p).get("user-invocable", True) is not False]
    assert user_invocable == ENTRY_SKILLS, user_invocable


def test_agents_preload_exactly_the_rules_they_declare_as_mandatory() -> None:
    for agent in SPECIALISTS:
        path = ROOT / "agents" / f"{agent}.md"
        preloaded = [s.split(":", 1)[1] for s in as_list(frontmatter(path).get("skills"))]
        rules_line = next(l for l in read(path).splitlines() if l.startswith("`django-security-standards`"))
        declared = re.findall(r"`([^`]+)`", rules_line)
        assert declared == [s for s in preloaded if s in RULES], agent
        assert "orchestrate" not in preloaded, agent


def test_writing_agents_verify_rule_compliance_before_completion() -> None:
    for agent in GATED:
        criteria = read(ROOT / "agents" / f"{agent}.md").split("## Completion criteria", 1)[1]
        assert "Every applicable MUST of the mandatory rules above is met" in criteria, agent


def test_rule_requirements_are_not_copied_into_agents_or_skills() -> None:
    """One canonical source per standard: agents and skills cite requirement ids, they never copy the text."""
    requirement = re.compile(r"^- \*\*([A-Z]+-[AMS]\d+)\*\* (.{40,})$", re.M)
    texts = [m.group(2) for name in RULES for m in requirement.finditer(read(ROOT / "rules" / name / "SKILL.md"))]
    assert texts, "rule requirement format changed; update this test"
    targets = [ROOT / "agents" / f"{a}.md" for a in AGENTS] + [ROOT / "skills" / s / "SKILL.md" for s in SKILLS + ENTRY_SKILLS]
    for path in targets:
        body = read(path)
        copied = [t[:50] for t in texts if t in body]
        assert not copied, (path.relative_to(ROOT).as_posix(), copied[:3])


def test_postgresql_specific_components_stay_removed() -> None:
    """The PostgreSQL-specific skill was removed; generic database knowledge (ORM, migrations, SQL) stays."""
    names = AGENTS + SKILLS + ENTRY_SKILLS + RULES
    assert not [n for n in names if "postgres" in n.lower()]
    assert not list(ROOT.glob("**/postgresql-engineering*")) and not (ROOT / "skills" / "postgresql-engineering").exists()
    for path in text_files():
        if path.name in ("CHANGELOG.md", "CANONICAL-MANIFEST.json") or "tests" in path.relative_to(ROOT).parts:
            continue
        assert "postgresql-engineering" not in read(path), path.relative_to(ROOT).as_posix()
    for keep in ("django-orm", "django-performance"):
        assert keep in SKILLS
    for rule in ("django-database-standards", "django-model-standards"):
        assert rule in RULES


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


def test_config_contains_only_the_orchestration_policy() -> None:
    assert sorted(p.name for p in (ROOT / "config").rglob("*") if p.is_file()) == ["orchestration-policy.yaml"]


def test_gitignore_covers_secrets_and_caches() -> None:
    text = read(ROOT / ".gitignore")
    for entry in (".env", "*.pem", "*.key", "__pycache__/", ".pytest_cache/"):
        assert entry in text, entry
