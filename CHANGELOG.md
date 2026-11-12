# Changelog

All notable changes to the standalone Django Engineering Plugin. Versions follow semantic versioning.

## 2.0.1

Discovery fixes. Commands restored (unchanged from 1.x, one `commands/` folder): `/django-engineering:orchestrate`
and nine specialist commands, each delegating to its agent. The twelve rules now carry `user-invocable: false`, so
they are no longer listed as slash commands (they were exposed because `plugin.json` registers `./rules/` as skills,
which Claude Code also turns into `/` entries); agents still preload them. `plugin.json` lists the ten commands.

## 2.0.0

Agents are the only interface. **Breaking:** the ten slash commands (`/django-engineering:orchestrate` and the nine
`django-*` commands) are removed.

### Changed
- Invoke agents by name: `@django-engineering:<agent id>` or plain language. Unsure which? Use
  `@django-engineering:django-orchestrator`, or `claude --agent django-engineering:django-orchestrator`.
- The approval gates that lived in the commands now live in the agents (`## Approval gate`): model, API, testing,
  performance and architecture agents propose first and end with `AWAITING APPROVAL:`; the security agent defaults
  to review and fixes only approved findings; the documentation agent writes documentation only. The gate now holds
  however an agent is reached.
- The orchestrator passes approvals through and never grants them; policy 1.1.0 adds a completion criterion for
  steps awaiting approval and drops the `orchestrator.command` key.
- Removed harness vocabulary from agents (`AgentTask`, `AgentResult`, output directory). Agents return reports in
  their reply and list changed files.
- Templates no longer carry a `commands:` field.
- Docs rewritten for the agent-only model; `docs/architecture.md` explains skills, skill references, rules,
  shared references and templates.
- Tests: command checks replaced by checks that no commands exist and that every code-changing agent carries its
  gate. Manifest adaptation AD-13 records the changes.

### Migration
| Was | Now |
|---|---|
| `/django-engineering:orchestrate <request>` | `@django-engineering:django-orchestrator <request>` |
| `/django-engineering:django-model ...` | `@django-engineering:django-model-agent ...` |
| `--apply`, `--fix`, `--run-only`, `--dry-run` | Say it in the request: "apply it", "fix SEC-001", "just run the tests", "dry run" |

## 1.0.0

First independent standalone distribution.

### Contents
- Orchestrator, nine specialist agents, nine `django-*` commands plus `orchestrate`, twelve skills, twelve
  rules, twelve templates, seven shared references, the fail-closed security guard and the orchestration
  policy, derived from the canonical definitions of the Django Agentic Engineering main repository
  (plugin version 0.6.0; commit recorded in `CANONICAL-MANIFEST.json`).
- Independent marketplace `django-engineering-standalone`.
- Documentation (installation, usage, architecture, security, troubleshooting), `TEAM_HANDOFF.md`, and an
  offline validation suite.

### Intentional adaptations of canonical files
Twelve small, documented adaptations (AD-01 to AD-12 in `CANONICAL-MANIFEST.json`): removed references to the
Python harness and to the main repository's generator, fixed three dead links, removed the harness execution mode from
`/orchestrate`, reworded rules that named the harness's approval service. Agent responsibilities, tools,
write modes, routing policy content, guard logic and security policy rules are unchanged.

### Not included (by design)
The Python harness, harness bootstrap, harness management commands (`setup-harness`, `harness-status`,
`enable-harness`, `disable-harness`, `doctor`), the harness runtime prompt template, and every harness
configuration, schema and test.
