# Django Engineering Plugin (standalone)

A Claude Code plugin for Django and Django REST Framework engineering: a **Django Orchestrator**, nine
**specialist agents** you invoke by name, twelve **skills**, twelve mandatory **rules**, output
**templates**, shared **references** and a fail-closed **security guard**.

This is the independent, self-contained distribution. It needs **no Python harness, no services, no
database and no Python packages**. The only runtime prerequisite besides Claude Code is a `python`
(3.8+) interpreter on `PATH`, which runs the security guard hook (standard library only).

## Quick start

Inside Claude Code (replace `<owner>/<repository>` with the GitHub repository that hosts this folder):

```text
/plugin marketplace add <owner>/<repository>
/plugin install django-engineering@django-engineering-standalone
```

Start a new session (or `/reload-plugins`), open a Django project and run:

```text
@django-engineering:django-orchestrator Add an invoices API with its model and tests
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
| Skills | 12 | `skills/` |
| Rules | 12 | `rules/` |
| Output templates | 12 | `templates/` |
| Shared references | 7 | `references/` |
| Security guard | PreToolUse/PostToolUse hook | `hooks/` |
| Orchestration policy | 1 | `config/orchestration-policy.yaml` |

Specialists: `django-project-analyzer`, `django-architecture-agent`, `django-model-agent`,
`django-api-agent`, `django-security-agent`, `django-testing-agent`, `django-performance-agent`,
`django-documentation-agent`, `django-code-review-agent`.

There are **no slash commands**: you address an agent by name (`@django-engineering:<agent id>`) or in plain
language, and the agent loads its own skills, rules, templates and references. Not sure which agent? Use
`@django-engineering:django-orchestrator`. See [docs/usage.md](docs/usage.md).

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
