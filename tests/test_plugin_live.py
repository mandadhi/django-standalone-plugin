"""Opt-in checks that load the plugin through the installed Claude Code CLI (`pytest -m live`).

`validate` tests need only the CLI. The discovery test starts a one-turn session and needs a login; it makes
no model-driven tool calls it does not have to.
"""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from conftest import AGENTS, ENTRY_SKILLS, PLUGIN, ROOT, RULES, SKILLS

pytestmark = pytest.mark.live
CLAUDE = shutil.which("claude")


def _run(*args: str, timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run([CLAUDE, *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


@pytest.fixture(scope="module", autouse=True)
def _need_cli():
    if CLAUDE is None:
        pytest.skip("claude CLI not on PATH")


def test_plugin_manifest_validates() -> None:
    proc = _run("plugin", "validate", ".")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_marketplace_manifest_validates() -> None:
    proc = _run("plugin", "validate", ".claude-plugin/marketplace.json")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_session_discovers_every_component() -> None:
    proc = _run("--plugin-dir", ".", "-p", "reply with the single word ok", "--output-format", "stream-json",
                "--verbose", "--max-turns", "1", timeout=240)
    init = None
    for line in proc.stdout.splitlines():
        try:
            frame = json.loads(line)
        except ValueError:
            continue
        if frame.get("type") == "system" and frame.get("subtype") == "init":
            init = frame
            break
    assert init, proc.stdout[:500] + proc.stderr[:500]
    agents = set(init.get("agents", []))
    assert {f"{PLUGIN}:{a}" for a in AGENTS} <= agents, sorted(agents)
    commands = set(init.get("slash_commands", []))
    ours = {c.split(":", 1)[1] for c in commands if c.startswith(f"{PLUGIN}:")}
    assert ours == set(ENTRY_SKILLS), f"only the entry skills may be slash commands, got {sorted(ours)}"
    assert not ({f"{PLUGIN}:{s}" for s in SKILLS + RULES} & commands), "internal skills or rules leaked into /"
    assert not any("harness" in c or c.endswith(":doctor") for c in commands if c.startswith(PLUGIN))
