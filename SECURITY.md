# Security policy

## Reporting a vulnerability

Do not open a public issue for a vulnerability. Report it privately to the maintainers of this repository
(use the host's private vulnerability reporting, or contact the owning team directly). Include the plugin
version, what you did, what happened and what you expected. Never include real secrets.

## Scope

In scope: the guard (`hooks/`), the security policy, agent `tools` and write modes, and any way for the
plugin's agents to exceed them (write when read-only, escape the project, reach the network, reveal
secrets, delegate outside the nine specialists).

Out of scope: Claude Code itself, the model, and the behaviour of a project the plugin is used on.

## Known limitations

The guard is policy, not isolation, and acts only on the plugin's own agents. See
[docs/security.md](docs/security.md#limitations-of-standalone-mode).

## Handling

Maintainers acknowledge reports promptly, fix with a regression test in `tests/test_guard.py`, bump the
version (see [TEAM_HANDOFF.md](TEAM_HANDOFF.md#release-process)) and record the fix in
[CHANGELOG.md](CHANGELOG.md).
