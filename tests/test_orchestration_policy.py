"""config/orchestration-policy.yaml is valid and agrees with the orchestrator agent and the guard policy."""

from __future__ import annotations

import re

import yaml

from conftest import (ORCHESTRATOR, PLUGIN, ROOT, SKILLS, RULES, SPECIALISTS, as_list, frontmatter, policy, read)


def load() -> dict:
    return yaml.safe_load(read(ROOT / "config" / "orchestration-policy.yaml"))


def test_policy_header_and_orchestrator() -> None:
    doc = load()
    assert doc["kind"] == "OrchestrationPolicy" and doc["schema_version"] == "1.0"
    assert doc["orchestrator"]["id"] == ORCHESTRATOR
    assert doc["orchestrator"]["path"] == f"agents/{ORCHESTRATOR}.md" and (ROOT / doc["orchestrator"]["path"]).is_file()
    assert "command" not in doc["orchestrator"], "the orchestrator is invoked by name; there are no commands"
    assert set(doc["orchestrator"]["skills"]) <= set(SKILLS + RULES)


def test_limits_and_specialists() -> None:
    doc = load()
    assert doc["limits"] == {"max_delegations": 6, "max_attempts_per_step": 2, "max_clarifying_questions": 3}
    assert doc["specialists"] == SPECIALISTS
    assert ORCHESTRATOR not in doc["specialists"], "the orchestrator must never be delegable"


def test_categories_are_well_formed() -> None:
    doc = load()
    ids = [c["id"] for c in doc["categories"]]
    assert len(ids) == len(set(ids)) and ids
    for category in doc["categories"]:
        assert category["signals"] and category["route"], category["id"]
        seen: list[str] = []
        required = 0
        for step in category["route"]:
            assert step["agent"] in SPECIALISTS, (category["id"], step["agent"])
            assert step["agent"] != ORCHESTRATOR
            for earlier in step.get("after", []):
                assert earlier in seen, (category["id"], step["agent"], earlier)
            if step.get("optional"):
                assert step.get("when"), f"{category['id']}/{step['agent']}: optional step needs a `when`"
            else:
                required += 1
            seen.append(step["agent"])
        assert required >= 1 or category.get("requires_any"), category["id"]
        assert len(category["route"]) <= doc["limits"]["max_delegations"], category["id"]
        for skill in category.get("supplementary_skills", []):
            assert skill in SKILLS, (category["id"], skill)
        for agent in category.get("requires_any", []):
            assert agent in [s["agent"] for s in category["route"]]


def test_policy_sections_present() -> None:
    doc = load()
    for key in ("step_constraints", "completion_criteria", "clarify_when", "failure_policy", "security_boundaries"):
        assert doc[key], key
    assert {c["id"] for c in doc["step_constraints"]} >= {"stay-in-role", "honest-status", "no-secrets"}


def _generated_section() -> str:
    body = read(ROOT / "agents" / f"{ORCHESTRATOR}.md")
    match = re.search(r"<!-- BEGIN GENERATED: orchestration-policy.*?-->\n(.*?)\n<!-- END GENERATED: orchestration-policy -->", body, re.S)
    assert match and body.count("BEGIN GENERATED") == 1
    return match.group(1)


def test_orchestrator_routing_section_matches_the_policy() -> None:
    doc, section = load(), _generated_section()
    limits = doc["limits"]
    assert f"At most **{limits['max_delegations']}** specialist delegations" in section
    assert f"At most **{limits['max_attempts_per_step']}** attempts per step" in section
    assert f"At most **{limits['max_clarifying_questions']}** clarifying questions" in section
    delegates = re.search(r"Delegate only to: (.+?)\. Never to", section).group(1)
    assert re.findall(r"`([^`]+)`", delegates) == [f"{PLUGIN}:{a}" for a in doc["specialists"]]
    assert f"Never to `{PLUGIN}:{ORCHESTRATOR}`" in section
    assert re.findall(r"^#### `([^`]+)`", section, re.M) == [c["id"] for c in doc["categories"]]
    for category in doc["categories"]:
        block = section.split(f"#### `{category['id']}`", 1)[1].split("\n#### ", 1)[0]
        assert re.findall(r"^\d+\. (?:\*optional\* )?`([^`]+)`", block, re.M) == [s["agent"] for s in category["route"]], category["id"]
        assert "Signals: " + ", ".join(f"`{s}`" for s in category["signals"]) in block
    for key in ("clarify_when", "failure_policy", "completion_criteria", "security_boundaries"):
        for item in doc[key]:
            assert f"- {item}" in section, (key, item[:50])
    for constraint in doc["step_constraints"]:
        assert f"**{constraint['id']}**: {constraint['description']}" in section


def test_orchestrator_skills_line_matches_the_policy() -> None:
    meta = frontmatter(ROOT / "agents" / f"{ORCHESTRATOR}.md")
    assert as_list(meta["skills"]) == [f"{PLUGIN}:{s}" for s in load()["orchestrator"]["skills"]]


def test_guard_delegation_allowlist_matches_the_policy() -> None:
    entry = policy()["agents"][ORCHESTRATOR]
    assert entry["mode"] == "read-only"
    assert entry["delegates"] == [f"{PLUGIN}:{a}" for a in load()["specialists"]]
    for agent in SPECIALISTS:
        assert "delegates" not in policy()["agents"][agent]
