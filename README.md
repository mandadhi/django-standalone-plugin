# Django Engineering Plugin (standalone)

A Claude Code plugin for Django and Django REST Framework engineering: a **Django Orchestrator** reached
through one slash command, nine **specialist agents**, eleven internal **skills**, twelve mandatory
**rules** the agents apply automatically, output **templates**, shared **references** and a fail-closed
**security guard**. It covers the lifecycle from requirements and design to a reviewed pull request.

This is the independent, self-contained distribution. It needs **no Python harness, no services, no
database and no Python packages**. The only runtime prerequisite besides Claude Code is a `python`
(3.8+) interpreter on `PATH`, which runs the security guard hook (standard library only).

## Quick start


```text
/plugin marketplace add mandadhi/django-standalone-plugin
/plugin install django-engineering@django-engineering-standalone
```

Start a new session (or `/reload-plugins`), open a Django project and run:

```text
/django-engineering:orchestrate Build a REST API for hospital appointments with models, permissions and tests
```

From a local clone, without installing:

```bash
cd django-standalone-plugin   # the folder that contains .claude-plugin/
claude --plugin-dir .
```

Full instructions: [docs/installation.md](docs/installation.md).

## What is in the box

| Component | Count | Where |
|---|---|---|
| Orchestrator | 1 | `agents/django-orchestrator.md` |
| Specialist agents | 9 | `agents/` |
| Slash command (entry skill) | 1 | `skills/orchestrate/` |
| Internal skills | 11 | `skills/` |
| Internal mandatory rules | 12 | `rules/` |
| Output templates | 12 | `templates/` |
| Shared references | 7 | `references/` |
| Security guard | PreToolUse/PostToolUse hook | `hooks/` |
| Orchestration policy | 1 | `config/orchestration-policy.yaml` |

Specialists: `django-project-analyzer`, `django-architecture-agent`, `django-model-agent`,
`django-api-agent`, `django-security-agent`, `django-testing-agent`, `django-performance-agent`,
`django-documentation-agent`, `django-code-review-agent`.

**One slash command.** `/django-engineering:orchestrate <request>` hands your request to the orchestrator. The orchestrator plans the
work, delegates to the specialists, stops at every approval point and reports what was verified. The
skills and rules are **internal** (`user-invocable: false`), so they never appear in the `/` menu. Each
agent preloads the ones its work needs and must meet their MUST requirements before it reports done.
You can still address a specialist directly (`@django-engineering:<agent id>`). See
[docs/usage.md](docs/usage.md).

Lifecycle the orchestrator covers: requirements and project analysis, architecture and implementation
plan, models and migrations, DRF APIs, tests, security validation, documentation, gate review, and on
request a branch, commit and pull request. Each commit, push and pull request needs your explicit
approval.

## Documentation

| Document | For |
|---|---|
| [docs/installation.md](docs/installation.md) | Installing, verifying, updating, uninstalling, local development |
| [docs/agents.md](docs/agents.md) | The ten agents, how to invoke them, write modes |
| [docs/usage.md](docs/usage.md) | The agents, approvals, the orchestrator, examples |
| [docs/architecture.md](docs/architecture.md) | How the pieces fit; what skills, rules, references and templates are for; orchestration model |
| [docs/security.md](docs/security.md) | What is enforced, what is not, limitations of standalone mode |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common problems |
| [TEAM_HANDOFF.md](TEAM_HANDOFF.md) | Everything a new owning team needs |
| [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [CHANGELOG.md](CHANGELOG.md) | Project policy |
| [CANONICAL-MANIFEST.json](CANONICAL-MANIFEST.json) | Source-to-distribution mapping with SHA-256 hashes |

## Scope and honesty

- Specialist work runs as ordinary Claude Code subagents. There is no workflow engine, run database,
  checkpoint/resume, audit log or approver service. Approval is Claude Code's own permission prompt.
- The guard narrows what the plugin's ten agents may do; it is **not** a sandbox and is not equivalent to
  the security of the separate Django Agentic Harness (a different product that is not part of this
  distribution). Read [docs/security.md](docs/security.md) before using it on sensitive code.
- Use it on a clean git working tree so every change is reviewable and reversible.

## License

UNLICENSED (internal; see `.claude-plugin/plugin.json`).
