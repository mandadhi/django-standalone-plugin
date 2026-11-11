# hooks/

The standalone plugin's security guard. Claude Code loads `hooks/hooks.json` by default
(`plugin.json` deliberately does not declare it again, which would load it twice).

| File | Purpose |
|---|---|
| `hooks.json` | Registers the guard for **PreToolUse** and **PostToolUse** on every tool, in exec form (`"command": "python"`, `"args": [...]`, no shell), `"timeout": 30`, `"onFailure": "block"` |
| `django_pack_guard.py` | The guard. Standard-library Python 3.8+, no packages, no network, no services |
| `shell_syntax.py` | Shell command analyser used by the guard (standard library only; unchanged from the canonical copy) |
| `security-policy.json` | The guard's policy: denied tools and paths, command rules, secret patterns, write modes, per-agent entries, the orchestrator's delegation allowlist |

## How the guard decides

It acts only on calls whose hook input `agent_type` is one of the plugin's ten agents
(`django-engineering:<id>`, or the bare id). The main session and other agents get no opinion from it and
stay under Claude Code's own permissions.

| Decision | When |
|---|---|
| deny | Tool not declared by the agent; globally or per-agent denied tool (`WebFetch`, `WebSearch`); denied or credential path; read outside the project and the plugin; write outside the project; any write by a read-only agent; a non-documentation write by the documentation agent; any shell use by the documentation agent; denied commands; a file redirection or any command not classified `read` from a read-only agent (default deny, so unrecognised commands too); a shell command that cannot be analysed, lists the environment, expands a credential variable, or names a path outside the project; an `Agent` call by anything but the orchestrator, or by the orchestrator to anything but the nine specialists (itself included) |
| ask | Every Write/Edit by `django-security-agent`, and every shell command or tool of it not classified `read`; shell commands matching `commands_require_approval` (destructive, network, history rewrite, privilege); file deletion; inline code the guard cannot analyse (`python -c`, ...) |
| allow | Only Read/Grep/Glob by a plugin agent whose paths all lie inside the plugin's own `templates/`, `references/`, `skills/` or `rules/` |
| PostToolUse | Secret patterns in tool output are masked (`updatedToolOutput`) |
| no opinion | Everything else |

The hook never answers `allow` for anything else, so it can only narrow Claude Code's permissions.

## Fail closed

A missing or unreadable policy, a missing `shell_syntax.py`, malformed input, an unknown agent in the
plugin's namespace or any internal error exits with code 2, which blocks the call. `onFailure: "block"`
also blocks on a crash, a timeout or a **missing `python` interpreter**. That means Python 3.8+ must be
installed and reachable as `python` for the plugin to work at all (see
[docs/troubleshooting.md](../docs/troubleshooting.md)). Python is needed only to run this guard; no
harness, package or service is involved.

## Limits

Command analysis is policy, not isolation. See [docs/security.md](../docs/security.md) for what the guard
enforces, what it cannot, and how it differs from the integrated harness. For an OS boundary enable Claude
Code's own sandbox (`/sandbox`).

`security-policy.json` is maintained in this distribution. `tests/test_security_policy.py` fails when it
disagrees with the agents' `tools` frontmatter or with `config/orchestration-policy.yaml`.
