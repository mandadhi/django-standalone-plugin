# Installation

## Requirements

| Requirement | Why |
|---|---|
| Claude Code with plugin marketplace support and `onFailure` on command hooks | Verified with 2.1.322 |
| `python` 3.8+ on `PATH` (the command must be named `python`) | The security guard runs as `python hooks/django_pack_guard.py`. Standard library only: install no packages. If `python` is missing, the guard fails closed and **every tool call is blocked** while the plugin is enabled |
| Git Bash (Windows only, optional) | Claude Code offers Bash on Windows only when it finds Git Bash; otherwise set `CLAUDE_CODE_GIT_BASH_PATH`, or agents run without Bash |

Nothing else: no harness, no database, no Agent SDK.

## Identity

| | Value |
|---|---|
| Plugin name | `django-engineering` (agents appear as `django-engineering:<agent id>`) |
| Marketplace name | `django-engineering-standalone` (declared in `.claude-plugin/marketplace.json`) |
| Install id | `django-engineering@django-engineering-standalone` |

The marketplace name differs from the integrated distribution's (`django-agentic-engineering`), so the
install ids never collide. The **plugin** name is the same on purpose: it gives the documented
`django-engineering:` agent namespace the canonical agents and guard policy rely on. Consequently, **do not enable both distributions in the same Claude Code scope**; they would
register the same agent and skill names. Uninstall one first.

## Install from GitHub

Nothing is published yet. After the team creates the repository (with this folder's contents at the
repository root, so that `.claude-plugin/marketplace.json` is at the root), run inside Claude Code:

```text
/plugin marketplace add <owner>/<repository>
/plugin install django-engineering@django-engineering-standalone
```

or from a terminal:

```bash
claude plugin marketplace add <owner>/<repository>
claude plugin install django-engineering@django-engineering-standalone
```

Start a new session or run `/reload-plugins`. If the plugin lives in a subfolder of a larger repository,
add that repository, then set the plugin `source` in `.claude-plugin/marketplace.json` to the subfolder.

## Local development (no installation)

From the distribution root (the folder that contains `.claude-plugin/`):

```bash
claude --plugin-dir .
```

The plugin loads for that session straight from the working copy. Use it while editing agents, skills,
rules. Install from the marketplace for normal use.

You can also register the local folder as a marketplace:

```bash
claude plugin marketplace add .
claude plugin install django-engineering@django-engineering-standalone
```

## Verify

```bash
claude plugin validate .
claude plugin validate .claude-plugin/marketplace.json
claude plugin list        # django-engineering@django-engineering-standalone, enabled
```

In a session:

- Typing `@django-engineering:` offers the ten agents for mention. Typing `/django-engineering:` shows one
  command, `orchestrate`. Skills and rules are internal (`user-invocable: false`) and are not listed.
- `claude plugin details ...` may report **Agents (0)**. This is a display quirk for agents listed file by
  file in `plugin.json`; the session loads all ten.

## Update

```bash
claude plugin marketplace update django-engineering-standalone
claude plugin update django-engineering@django-engineering-standalone
```

Restart the session afterwards. Maintainers bump `version` in `.claude-plugin/plugin.json` for every
release (see [TEAM_HANDOFF.md](../TEAM_HANDOFF.md#release-process)), otherwise `plugin update` sees no change.

## Disable or uninstall

```bash
claude plugin disable django-engineering@django-engineering-standalone
claude plugin uninstall django-engineering@django-engineering-standalone
claude plugin marketplace remove django-engineering-standalone
```
