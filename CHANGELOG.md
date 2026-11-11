# Changelog

All notable changes to the standalone Django Engineering Plugin. Versions follow semantic versioning.

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
