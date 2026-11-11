# Changelog

All notable changes to the standalone Django Engineering Plugin. Versions follow semantic versioning.

## 3.0.0

The `/` menu now shows one workflow entry instead of every internal skill and rule. The agent architecture
is unchanged.

### Added
- `/django-engineering:orchestrate <request>`: the entry skill `skills/orchestrate/SKILL.md`
  (`disable-model-invocation: true`). It hands the request to `django-orchestrator` and carries out what the
  orchestrator returns. It holds no routing, approval or engineering logic. There is no `commands/` folder.
- Orchestrator: a *Reconcile* mode (the main session returns the step results of a routing plan for the final
  report), a *Delivery* section (read-only preparation of branch, staged files, commit message and PR
  description; the caller runs each commit, push and pull request only after the user approves it; no force
  push; unrelated changes are never staged), and a reconciliation check that writing steps report
  mandatory-rule compliance.
- Policy 1.2.0: `supplementary_skills` with a `when` condition, so `django-frontend`, `django-integrations`,
  `django-data-processing` and `django-report-generation` reach specialists only when a request needs them.
  `feature-delivery` gains optional `django-security-agent` (review mode) and `django-documentation-agent`
  steps; `max_delegations` rises from 6 to 8 to cover the full lifecycle. Architecture-design also matches
  requirements and specification requests.
- Writing agents: a completion criterion requiring every applicable MUST of their preloaded rules to be met,
  or reported by id. `django-model-agent` also preloads `django-performance-standards` (index decisions);
  `django-architecture-agent` also preloads `django-coding-standards` (where logic lives).
- Tests: internal skills and rules are not user-invocable; `orchestrate` is the only user-invocable skill and
  names no specialist; agents' declared rules match their preloads; rule requirement text is not copied into
  agents or skills; PostgreSQL-specific components stay removed; supplementary skills render into the
  orchestrator; the live test checks that the session exposes only the entry skill as a slash command.

### Fixed
- The guard denied `SubagentHandback`, the tool Claude Code 2.1.x subagents use to return their report, because
  no agent declares it. Every specialist's report was blocked. The new required policy key `runtime_tools`
  (`["SubagentHandback"]`) lets it through for all agents; every other undeclared tool is still denied.

### Changed
- All eleven knowledge skills and twelve rules carry `user-invocable: false`. They no longer appear as
  slash commands. Agents still preload them through their `skills:` frontmatter.

### Removed
- **Breaking:** the `postgresql-engineering` skill and its references, its preload in `django-model-agent` and
  `django-performance-agent`, and every link to it. PostgreSQL remains a supported database in examples, and
  the generic ORM, migration, SQL and database-performance knowledge is unchanged.

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
