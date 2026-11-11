"""hooks/security-policy.json agrees with the agents and keeps the standalone security model intact."""

from __future__ import annotations

import json
import re

from conftest import (AGENTS, EXPECTED_MODES, EXPECTED_TOOLS, ORCHESTRATOR, ROOT, SPECIALISTS, as_list, frontmatter,
                      policy, read)

MODE_ORDER = ("read-only", "documentation-only", "confirm-writes", "workspace-write")


def test_policy_has_an_entry_for_every_agent_and_nothing_else() -> None:
    assert sorted(policy()["agents"]) == AGENTS


def test_policy_tools_equal_the_agents_declared_tools() -> None:
    for agent in AGENTS:
        declared = tuple(as_list(frontmatter(ROOT / "agents" / f"{agent}.md")["tools"]))
        assert declared == EXPECTED_TOOLS[agent]
        assert tuple(policy()["agents"][agent]["tools"]) == declared, agent


def test_write_modes_are_the_documented_ones() -> None:
    for agent, mode in EXPECTED_MODES.items():
        assert policy()["agents"][agent]["mode"] == mode, agent


def test_network_tools_are_denied_and_never_declared() -> None:
    assert policy()["tools_deny"] == ["WebFetch", "WebSearch"]
    for agent in AGENTS:
        assert not {"WebFetch", "WebSearch"} & set(EXPECTED_TOOLS[agent]), agent


def test_global_security_rules_are_intact() -> None:
    data = policy()
    assert data["paths_deny"] == ["**/.env", "**/.env.*", "**/*.pem", "**/*.key", "**/secrets/**",
                                  "**/.django-engineering", "**/.django-engineering/**"]
    assert [r["id"] for r in data["commands_deny"]] == ["dump-environment", "read-credential-stores", "pipe-download-to-shell"]
    assert [r["id"] for r in data["commands_require_approval"]] == [
        "network-access", "recursive-delete", "git-history-rewrite", "database-destructive", "privilege-or-system"]
    assert data["secret_patterns"] and data["redaction"]["enabled"] is True
    assert set(data["write_modes"]) == set(MODE_ORDER)
    assert data["documentation_paths"] == ["docs/**", "doc/**", "**/*.md", "**/*.rst", "**/*.adoc", "**/README*",
                                           "**/CHANGELOG*", "mkdocs.yml", "mkdocs.yaml"]
    for rule in data["commands_deny"] + data["commands_require_approval"] + data["read_only_commands"]:
        re.compile(rule["regex"])
    for pattern in data["secret_patterns"]:
        re.compile(pattern["regex"])


def test_read_only_write_mode_grants_no_mutation() -> None:
    allow = set(policy()["write_modes"]["read-only"]["allow"])
    assert allow == {"read"} and policy()["write_modes"]["read-only"]["otherwise"] == "deny"
    assert policy()["write_modes"]["documentation-only"]["shell"] is False


def test_policy_holds_no_rule_or_skill_text() -> None:
    text = json.dumps(policy())
    assert "SEC-A1" not in text and "SKILL.md" not in text


def test_hooks_json_is_fail_closed() -> None:
    hooks = json.loads(read(ROOT / "hooks" / "hooks.json"))
    assert set(hooks["hooks"]) == {"PreToolUse", "PostToolUse"}
    for event in hooks["hooks"].values():
        for matcher in event:
            assert matcher["matcher"] == "*"
            for hook in matcher["hooks"]:
                assert hook["type"] == "command" and hook["onFailure"] == "block" and hook["timeout"] <= 60
                assert hook["command"] == "python"
                assert hook["args"][0] == "${CLAUDE_PLUGIN_ROOT}/hooks/django_pack_guard.py"


def test_specialists_cannot_delegate_and_orchestrator_is_read_only() -> None:
    assert policy()["agents"][ORCHESTRATOR]["mode"] == "read-only"
    assert all("delegates" not in policy()["agents"][a] for a in SPECIALISTS)
