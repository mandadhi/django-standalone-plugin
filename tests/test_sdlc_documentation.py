"""SDLC documentation framework: catalog, references, templates, agents, commands, orchestration policy, guard and Copilot parity.

Structural checks only: they prove the pieces agree with each other and with the security guard. How an agent behaves when it
runs is outside an offline test (docs/testing.md).
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

from conftest import (COMMANDS, ORCHESTRATOR, PLUGIN, ROOT, RULES, SPECIALISTS, TEMPLATES, as_list, frontmatter, policy,
                      read)

CATALOG = json.loads(read(ROOT / "config" / "sdlc-documentation-catalog.json"))
POLICY = yaml.safe_load(read(ROOT / "config" / "orchestration-policy.yaml"))
FRAMEWORK = read(ROOT / "references" / "sdlc-documentation-framework.md")
SHORT = {"documentation": "django-documentation-agent", "architecture": "django-architecture-agent",
         "model": "django-model-agent", "api": "django-api-agent", "security": "django-security-agent",
         "testing": "django-testing-agent", "performance": "django-performance-agent"}
NEW_REFERENCES = ["sdlc-documentation-framework", "sdlc-documentation-registry", "sdlc-mermaid-diagrams"]
NEW_TEMPLATES = ["requirements-specification", "traceability-matrix", "detailed-design", "implementation-notes",
                 "test-report", "deployment-and-release", "operational-runbook", "maintenance-record"]


def _guard():
    spec = importlib.util.spec_from_file_location("django_pack_guard", ROOT / "hooks" / "django_pack_guard.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sync():
    spec = importlib.util.spec_from_file_location("sync_copilot_adapter", ROOT / "tools" / "sync_copilot_adapter.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["sync_copilot_adapter"] = module
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------------ framework reference mirrors the catalog

def test_framework_reference_lists_every_catalog_type_with_the_catalog_owner() -> None:
    owners: dict = {}
    for row in re.findall(r"^\| ([A-Z0-9, ]+) \| [^|]+ \| (\w+) \|", FRAMEWORK, re.M):
        for code in (c.strip() for c in row[0].split(",")):
            owners[code] = SHORT[row[1]]
    for t in CATALOG["types"]:
        assert t["type"] in owners, f"{t['type']} missing from the framework reference"
        assert owners[t["type"]] == t["owner"], (t["type"], owners[t["type"]], t["owner"])
    assert set(owners) == {t["type"] for t in CATALOG["types"]}


def test_framework_reference_names_every_stage_in_catalog_order() -> None:
    headings = re.findall(r"^### (\d)\. (.+)$", FRAMEWORK, re.M)
    names = [h[1] for h in headings][:7]
    assert names == [s["name"].replace(" and ", " and ") for s in CATALOG["stages"]]


def test_reference_templates_and_catalog_templates_exist_and_are_owned() -> None:
    for t in CATALOG["types"]:
        meta = frontmatter(ROOT / "templates" / f"{t['template']}.template.md")
        assert t["owner"] in as_list(meta["agents"]), (t["type"], t["template"], meta["agents"])
    assert set(NEW_TEMPLATES) <= set(TEMPLATES)
    used = {t["template"] for t in CATALOG["types"]}
    assert set(NEW_TEMPLATES) <= used, "every new template serves at least one catalog type"


def test_diagram_types_are_all_documented_in_the_mermaid_guide() -> None:
    guide = read(ROOT / "references" / "sdlc-mermaid-diagrams.md")
    for t in CATALOG["types"]:
        if t.get("diagram"):
            assert f"| {t['type']} " in guide, t["type"]
    for needed in ("system context", "C4", "component", "sequence", "activity", "ERD", "data flow", "deployment", "workflow"):
        assert needed.lower() in guide.lower(), needed


# ------------------------------------------------------------------ the shared rule

def test_documentation_rule_defines_the_documentation_first_requirements() -> None:
    rule = read(ROOT / "rules" / "django-documentation-standards" / "SKILL.md")
    for i in range(9, 17):
        assert f"**DOC-M{i}**" in rule, i
    for phrase in ("never edited in place", "Conflicting documents", "assumptions", "Mermaid", "registry"):
        assert phrase in rule, phrase
    assert "DOC-M8" in rule and "documentation only" in rule, "the original documentation-only rule is preserved"


# ------------------------------------------------------------------ agents consume and update documentation

def test_every_specialist_has_the_documentation_protocol() -> None:
    for agent in SPECIALISTS:
        path = ROOT / "agents" / f"{agent}.md"
        body = read(path)
        meta = frontmatter(path)
        assert f"{PLUGIN}:django-documentation-standards" in as_list(meta["skills"]), agent
        assert "## Documentation context" in body, agent
        assert "DOC-M9" in body and "sdlc-documentation-registry.md" in body, agent
        refs = re.search(r"^- References \([^)]*\): (.+)$", body, re.M).group(1)
        for ref in NEW_REFERENCES:
            assert f"`{ref}`" in refs, (agent, ref)
        assert "approved" in body.lower() and "## Documentation" in body, agent


def test_read_only_agents_report_but_never_write_documentation() -> None:
    for agent in ("django-project-analyzer", "django-code-review-agent"):
        body = read(ROOT / "agents" / f"{agent}.md")
        section = body.split("## Documentation context", 1)[1].split("\n## ", 1)[0]
        assert "You are read-only" in section and "Do not" in section, agent
    review = read(ROOT / "agents" / "django-code-review-agent.md")
    assert "impact assessment" in review and "contradicts" in review


def test_every_owner_agent_names_the_documents_it_owns() -> None:
    owned = {}
    for t in CATALOG["types"]:
        owned.setdefault(t["owner"], set()).add(t["type"])
    for agent, types in owned.items():
        if agent == "django-documentation-agent":
            continue
        section = read(ROOT / "agents" / f"{agent}.md").split("## Documentation context", 1)[1].split("\n## ", 1)[0]
        assert "You own" in section or "**You own:**" in section, agent
        for code in types:
            assert re.search(rf"\b{code}\b", section), f"{agent} does not name {code}"


def test_documentation_agent_coordinates_but_is_not_the_only_writer() -> None:
    body = read(ROOT / "agents" / "django-documentation-agent.md")
    assert "not the only agent that writes documents" in body
    for phrase in ("Registry coordination", "Cross-document consistency", "Documentation impact assessment", "pending_revision",
                   "never edited in place"):
        assert phrase in body or phrase.lower() in body.lower(), phrase
    owners = {t["owner"] for t in CATALOG["types"]}
    assert len(owners - {"django-documentation-agent"}) >= 6


def test_orchestrator_checks_documentation_context_and_reports_it() -> None:
    body = read(ROOT / "agents" / f"{ORCHESTRATOR}.md")
    assert f"{PLUGIN}:django-documentation-standards" in as_list(frontmatter(ROOT / "agents" / f"{ORCHESTRATOR}.md")["skills"])
    for phrase in ("docs/sdlc/registry.json", "**documentation context**", "**Documentation:**", "never settle it",
                   "cannot run the\n   registry validator"):
        assert phrase in body, phrase


# ------------------------------------------------------------------ orchestration policy

def test_policy_documentation_section_matches_the_catalog_and_the_routes() -> None:
    doc = POLICY["documentation"]
    assert doc["registry"] == "docs/sdlc/registry.json" and doc["catalog"] == "config/sdlc-documentation-catalog.json"
    assert [s["id"] for s in doc["stages"]] == [s["id"] for s in CATALOG["stages"]]
    categories = {c["id"] for c in POLICY["categories"]}
    for stage in doc["stages"]:
        assert set(stage["leads"]) <= set(SPECIALISTS) and set(stage["categories"]) <= categories, stage["id"]
    assert {p["id"] for p in doc["protocol"]} >= {"read-registry", "consume-current", "review-stale", "generate-missing",
                                                  "protect-approved", "report-conflicts", "no-invention", "update-owned",
                                                  "impact-assessment"}
    assert "django-documentation-standards" in POLICY["orchestrator"]["skills"]
    assert "documentation-first" in {c["id"] for c in POLICY["step_constraints"]}


def test_policy_documentation_category_routes_to_the_documentation_agent_only_where_it_owns_the_work() -> None:
    by_id = {c["id"]: c for c in POLICY["categories"]}
    assert [s["agent"] for s in by_id["documentation"]["route"]] == ["django-documentation-agent"]
    feature = by_id["feature-delivery"]["route"]
    docs = [s for s in feature if s["agent"] == "django-documentation-agent"]
    assert len(docs) == 1 and docs[0].get("optional"), "documentation sync is optional in feature delivery"
    assert feature[-1]["agent"] == "django-code-review-agent", "review gates the documentation too"
    assert len(feature) <= POLICY["limits"]["max_delegations"]


def test_no_second_orchestration_engine_or_runtime_dependency_was_added() -> None:
    names = {p.name for p in (ROOT / "tools").glob("*.py")}
    assert names == {"sync_copilot_adapter.py", "sdlc_registry.py"}
    imports = set(re.findall(r"^(?:from|import) ([a-zA-Z_]+)", read(ROOT / "tools" / "sdlc_registry.py"), re.M))
    assert imports <= {"__future__", "argparse", "hashlib", "json", "re", "subprocess", "sys", "datetime", "pathlib"}, imports
    assert not list(ROOT.glob("**/.mcp.json")) and "mcpServers" not in read(ROOT / ".claude-plugin" / "plugin.json")


# ------------------------------------------------------------------ the ten commands

@pytest.mark.parametrize("command", COMMANDS)
def test_every_command_carries_the_documentation_context(command: str) -> None:
    body = read(ROOT / "commands" / f"{command}.md")
    assert "## Documentation context" in body, command
    assert "DOC-M9" in body and "sdlc-documentation-registry.md" in body, command
    assert "docs/sdlc/registry.json" in body, command


def test_command_specific_documentation_roles() -> None:
    def section(name: str) -> str:
        return read(ROOT / "commands" / f"{name}.md").split("## Documentation context", 1)[1].split("\n## ", 1)[0]
    assert "inventory" in section("django-analyze").lower() and "Nothing is written" in section("django-analyze")
    assert "requirements" in section("django-design") and "--out" in section("django-design")
    assert "database design" in section("django-model") and "ERD" in section("django-model")
    assert "API specification" in section("django-api")
    assert "security design" in section("django-security") and "confirm-writes" in section("django-security")
    assert "traceability" in section("django-test") and "not from the code under test" in section("django-test")
    assert "performance assessment" in section("django-optimize")
    assert "lifecycle" in section("django-document") and "impact assessment" in section("django-document")
    assert "documentation outcome" in section("orchestrate") and "no second workflow" in section("orchestrate")
    assert "Nothing is written" in section("django-review") and "impact assessment" in section("django-review")
    doc = read(ROOT / "commands" / "django-document.md")
    for flag in ("--stage", "--profile", "--check", "--impact"):
        assert flag in doc, flag


def test_no_command_duplicates_the_protocol() -> None:
    """The protocol lives once, in the registry reference; commands only add their own deltas."""
    for command in COMMANDS:
        body = read(ROOT / "commands" / f"{command}.md")
        assert "pending_revision" not in body and "DOC-M11" not in body, command


# ------------------------------------------------------------------ security guard compatibility

def _decide(agent: str, tool: str, tool_input: dict, workspace: Path) -> "dict | None":
    guard = _guard()
    hook = {"tool_name": tool, "cwd": str(workspace), "tool_input": tool_input, "agent_type": f"{PLUGIN}:{agent}"}
    return guard.handle("pre", hook, policy(), ROOT)


def _verdict(result: "dict | None") -> str:
    return (result or {}).get("hookSpecificOutput", {}).get("permissionDecision", "no-opinion")


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    (tmp_path / "docs" / "sdlc").mkdir(parents=True)
    (tmp_path / "docs" / "diagrams").mkdir()
    (tmp_path / "shop").mkdir()
    return tmp_path


def test_documentation_agent_can_write_registry_diagrams_and_proposals_but_not_code(workspace: Path) -> None:
    for rel in ("docs/sdlc/registry.json", "docs/diagrams/erd-orders.mmd", "docs/requirements/srs.md",
                "docs/requirements/srs.proposed.md", "README.md"):
        result = _decide("django-documentation-agent", "Write", {"file_path": str(workspace / rel), "content": "x"}, workspace)
        assert _verdict(result) != "deny", rel
    for rel in ("shop/models.py", "shop/migrations/0001_initial.py", "config/settings.py"):
        result = _decide("django-documentation-agent", "Write", {"file_path": str(workspace / rel), "content": "x"}, workspace)
        assert _verdict(result) == "deny", rel


def test_read_only_agents_still_cannot_write_the_registry_or_run_plugin_scripts(workspace: Path) -> None:
    for agent in ("django-project-analyzer", "django-code-review-agent", ORCHESTRATOR):
        write = _decide(agent, "Write", {"file_path": str(workspace / "docs/sdlc/registry.json"), "content": "{}"}, workspace)
        assert _verdict(write) == "deny", agent
        run = _decide(agent, "Bash", {"command": f'python "{ROOT}/tools/sdlc_registry.py" check'}, workspace)
        assert _verdict(run) == "deny", f"{agent}: the guard stays closed; a person or CI runs the validator"


def test_secret_and_credential_paths_stay_denied_for_documentation_writes(workspace: Path) -> None:
    for rel in (".env", "docs/secrets/notes.md", "keys/server.pem"):
        result = _decide("django-documentation-agent", "Write", {"file_path": str(workspace / rel), "content": "x"}, workspace)
        assert _verdict(result) == "deny", rel


def test_security_policy_was_not_loosened() -> None:
    data = policy()
    assert data["write_modes"]["documentation-only"]["shell"] is False
    assert data["write_modes"]["read-only"]["allow"] == ["read"]
    assert data["agents"]["django-documentation-agent"]["tools"] == ["Read", "Write", "Edit", "Grep", "Glob"]
    assert data["agents"]["django-security-agent"]["mode"] == "confirm-writes"
    assert set(data["agents"][ORCHESTRATOR]["delegates"]) == {f"{PLUGIN}:{a}" for a in SPECIALISTS}


# ------------------------------------------------------------------ both platforms share one documentation system

def test_copilot_adapter_is_in_sync_and_documentation_parity_holds() -> None:
    assert _sync().check() == []


def test_copilot_agents_and_commands_carry_the_same_documentation_protocol() -> None:
    gh = ROOT / ".github"
    for agent in SPECIALISTS:
        canonical = read(ROOT / "agents" / f"{agent}.md")
        generated = read(gh / "agents" / f"{agent}.agent.md")
        assert "## Documentation context" in generated and "DOC-M9" in generated, agent
        assert "<plugin-root>/references/sdlc-documentation-registry.md" in generated, agent
        section_c = canonical.split("## Documentation context", 1)[1].split("\n## ", 1)[0]
        section_g = generated.split("## Documentation context", 1)[1].split("\n## ", 1)[0]
        assert section_c.replace("${CLAUDE_PLUGIN_ROOT}", "<plugin-root>") == section_g, agent
    for command in COMMANDS:
        generated = read(gh / "skills" / command / "SKILL.md")
        assert "## Documentation context" in generated and "docs/sdlc/registry.json" in generated, command
    orchestrator = read(gh / "agents" / f"{ORCHESTRATOR}.agent.md")
    assert "Documentation context (registry, protocol and SDLC stages)" in orchestrator


def test_copilot_adapter_has_no_separate_documentation_system() -> None:
    gh = ROOT / ".github"
    names = {p.name for p in gh.rglob("*") if p.is_file()}
    assert not {"sdlc-documentation-catalog.json", "sdlc_registry.py", "registry.json"} & names
    assert not [p for p in gh.rglob("*.template.md")]
    for rule in ("django-documentation-standards",):
        generated = read(gh / "skills" / rule / "SKILL.md")
        assert "../../../references/sdlc-documentation-registry.md" in generated
        assert (gh / "skills" / rule / ".." / ".." / ".." / "references" / "sdlc-documentation-registry.md").resolve().is_file()
    instructions = read(gh / "instructions" / "django-engineering.instructions.md")
    assert "docs/sdlc/registry.json" in instructions and "django-documentation-standards" in instructions


def test_manifest_records_the_shared_documentation_system() -> None:
    manifest = json.loads(read(ROOT / "CANONICAL-MANIFEST.json"))
    shared = manifest["sdlc_documentation"]
    assert shared["registry"] == "docs/sdlc/registry.json"
    assert set(shared["shared_assets"]) >= {"config/sdlc-documentation-catalog.json", "tools/sdlc_registry.py"}
    assert set(NEW_TEMPLATES) <= {n[: -len(".template.md")] for n in shared["templates"]}
    ad16 = next(a for a in manifest["adaptations"] if a["id"] == "AD-16")
    assert "agents/django-documentation-agent.md" in ad16["files"] and "commands/orchestrate.md" in ad16["files"]
    assert "rules/django-documentation-standards/SKILL.md" in ad16["files"]


def test_adapter_check_detects_documentation_drift() -> None:
    mod = _sync()
    target = ROOT / ".github" / "agents" / "django-api-agent.agent.md"
    original = target.read_bytes()
    try:
        target.write_bytes(original.replace(b"## Documentation context", b"## Notes"))
        problems = mod.check()
        assert any("stale" in p for p in problems)
    finally:
        target.write_bytes(original)
    assert mod.check() == []


def test_rule_inventory_is_unchanged() -> None:
    assert len(RULES) == 12
