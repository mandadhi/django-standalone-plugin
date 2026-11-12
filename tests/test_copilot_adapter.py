"""GitHub Copilot adapter: structure, visibility, derivation from the canonical sources, and Claude/Copilot parity.

These are offline structural checks. They prove the files follow the documented Copilot formats and are derived
from the canonical content; they do not prove that a Copilot client discovers or invokes them (see docs/testing.md).
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys

import yaml

from conftest import (AGENTS, COMMANDS, EXPECTED_TOOLS, ORCHESTRATOR, ROOT, RULES, SKILLS, SPECIALISTS, as_list,
                      frontmatter, read)

GH = ROOT / ".github"
TOOL_MAP = {"Read": "read", "Grep": "search", "Glob": "search", "Write": "edit", "Edit": "edit", "Bash": "execute",
            "Agent": "agent"}


def _sync():
    spec = importlib.util.spec_from_file_location("sync_copilot_adapter", ROOT / "tools" / "sync_copilot_adapter.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sync_copilot_adapter"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_adapter_is_in_sync_with_the_canonical_sources() -> None:
    assert _sync().check() == []


def test_check_detects_stale_and_missing_adapters() -> None:
    mod = _sync()
    target = GH / "skills" / "django-api" / "SKILL.md"
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\ndrift\n")
        assert any("stale" in p for p in mod.check())
        target.unlink()
        assert any("missing" in p for p in mod.check())
    finally:
        target.write_bytes(original)
    assert mod.check() == []


def test_exactly_ten_user_invocable_command_skills() -> None:
    invocable = []
    for f in sorted((GH / "skills").glob("*/SKILL.md")):
        meta = frontmatter(f)
        assert meta["name"] == f.parent.name and re.fullmatch(r"[a-z0-9-]{1,64}", meta["name"])
        assert 0 < len(meta["description"]) <= 1024
        if meta.get("user-invocable", True) is not False:
            invocable.append(meta["name"])
        assert meta.get("disable-model-invocation") is False, f.parent.name
    assert sorted(invocable) == sorted(COMMANDS)


def test_internal_skills_and_standards_are_hidden_but_model_invocable() -> None:
    for name in SKILLS + RULES:
        meta = frontmatter(GH / "skills" / name / "SKILL.md")
        assert meta["user-invocable"] is False and meta["disable-model-invocation"] is False, name


def test_command_skills_keep_the_canonical_workflow() -> None:
    for c in COMMANDS:
        src = read(ROOT / "commands" / f"{c}.md").split("\n---\n", 1)[1]
        gen = read(GH / "skills" / c / "SKILL.md")
        meta, derived = frontmatter(ROOT / "commands" / f"{c}.md"), frontmatter(GH / "skills" / c / "SKILL.md")
        assert derived["description"] == " ".join(str(meta["description"]).split())
        assert derived.get("argument-hint") == meta.get("argument-hint")
        for heading in re.findall(r"^## .+$", src, re.M):
            assert heading in gen, (c, heading)
        assert "CLAUDE_PLUGIN_ROOT" not in gen and "$ARGUMENTS" not in gen and "django-engineering:" not in gen
        assert re.search(r"`django-(?:[a-z-]+-)?(?:agent|analyzer|orchestrator)`", gen), c


def test_agents_visibility_tools_and_delegation() -> None:
    assert sorted(p.name[: -len(".agent.md")] for p in (GH / "agents").glob("*.agent.md")) == AGENTS
    for a in AGENTS:
        meta = frontmatter(GH / "agents" / f"{a}.agent.md")
        assert meta["name"] == a and meta["description"].strip()
        assert meta["disable-model-invocation"] is False, f"{a}: must stay delegable"
        assert meta["user-invocable"] is (a == ORCHESTRATOR), a
        want = []
        for t in EXPECTED_TOOLS[a]:
            if TOOL_MAP[t] not in want:
                want.append(TOOL_MAP[t])
        assert meta["tools"] == want, a
        assert ("agent" in meta["tools"]) is (a == ORCHESTRATOR), "only the orchestrator may start agents"
    orch = frontmatter(GH / "agents" / f"{ORCHESTRATOR}.agent.md")
    policy = yaml.safe_load(read(ROOT / "config" / "orchestration-policy.yaml"))
    assert orch["agents"] == policy["specialists"] == SPECIALISTS
    assert ORCHESTRATOR not in orch["agents"], "no self-delegation"


def test_agents_list_the_same_skills_and_rules_as_the_canonical_agent() -> None:
    for a in AGENTS:
        canonical = [s.split(":", 1)[1] for s in as_list(frontmatter(ROOT / "agents" / f"{a}.md").get("skills"))]
        body = read(GH / "agents" / f"{a}.agent.md").split("## Skills and rules to load (GitHub Copilot)", 1)[1]
        listed = re.findall(r"^- `([a-z-]+)`$", body, re.M)
        assert listed == canonical, a
        assert "django-security-standards" in listed
        for name in listed:
            assert (GH / "skills" / name / "SKILL.md").is_file(), (a, name)


def test_agent_bodies_are_the_canonical_bodies() -> None:
    for a in AGENTS:
        canon = read(ROOT / "agents" / f"{a}.md").split("\n---\n", 1)[1]
        gen = read(GH / "agents" / f"{a}.agent.md")
        for heading in re.findall(r"^## .+$", canon, re.M):
            assert heading in gen, (a, heading)


def test_orchestrator_policy_section_matches_the_single_policy() -> None:
    policy = yaml.safe_load(read(ROOT / "config" / "orchestration-policy.yaml"))
    text = read(GH / "agents" / f"{ORCHESTRATOR}.agent.md")
    assert f"**{policy['limits']['max_delegations']}**" in text
    for cat in policy["categories"]:
        assert f"`{cat['id']}`" in text, cat["id"]
    assert "config/orchestration-policy.yaml" in text


def test_no_second_routing_policy_exists() -> None:
    names = [p.name for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and "orchestration-policy" in p.name]
    assert names == ["orchestration-policy.yaml"], names
    for f in GH.rglob("*"):
        if f.is_file():
            assert "categories:" not in read(f), f


def test_relative_links_in_generated_skills_resolve() -> None:
    bad = []
    for f in (GH / "skills").glob("*/SKILL.md"):
        for target in re.findall(r"\]\((\.\./[^)#]+)\)", read(f)):
            if not (f.parent / target).resolve().is_file():
                bad.append((f.parent.name, target))
    assert not bad, bad[:5]
    assert (GH / "skills" / "django-orm" / "../../../skills/django-orm/references/queryset-api.md").resolve().is_file()


def test_no_claude_only_syntax_leaks_into_copilot_files() -> None:
    for f in GH.rglob("*.md"):
        text = read(f)
        assert "CLAUDE_PLUGIN_ROOT" not in text and "django-engineering:" not in text, f
        head = text.split("\n---\n")[0]
        assert not re.search(r"^(skills|model|maxTurns|disallowedTools):", head, re.M), f


def test_standards_instruction_file_is_thin_and_points_to_real_rules() -> None:
    f = GH / "instructions" / "django-engineering.instructions.md"
    assert frontmatter(f)["applyTo"]
    named = set(re.findall(r"`(django-[a-z-]+-standards|django-project-structure)`", read(f)))
    assert named == set(RULES)
    assert len(read(f)) < 2500


def test_sync_tool_check_cli_passes() -> None:
    proc = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_copilot_adapter.py"), "--check"],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout


def test_parity_matrix_covers_all_ten_commands() -> None:
    table = _sync().matrix()
    for c in COMMANDS:
        assert f"| {c} |" in table
    assert "OUT OF SYNC" not in table


def test_manifest_records_every_generated_file_and_its_status() -> None:
    import json
    mod = _sync()
    manifest = json.loads(read(ROOT / "CANONICAL-MANIFEST.json"))
    assert manifest["copilot_adapter"]["mappings"] == mod.manifest_section(mod.expected())
    assert all(m["sync_status"] == "in-sync" and (ROOT / m["copilot_destination"]).is_file()
               and (ROOT / m["canonical_source"]).is_file() for m in manifest["copilot_adapter"]["mappings"])
    assert len(manifest["copilot_adapter"]["mappings"]) == 44
