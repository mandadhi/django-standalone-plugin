# Agents

The ten agents (in [`agents/`](../agents/)) of the Django Engineering Plugin: the **orchestrator** and nine **specialists**.
One `<agent-id>.md` per agent (YAML frontmatter + instructions). They are listed explicitly in
`.claude-plugin/plugin.json`.

| Agent | Role | Write mode (guard) |
|---|---|---|
| `django-orchestrator` | Classifies a request, selects specialists, briefs them, reconciles results, reports | read-only; may delegate only to the nine specialists |
| `django-project-analyzer` | Maps a project: versions, apps, models, interfaces, risks | read-only |
| `django-architecture-agent` | App boundaries, layering, ADRs, implementation plan; scaffolding on request | workspace-write |
| `django-model-agent` | Models, constraints, indexes, migrations | workspace-write |
| `django-api-agent` | DRF serializers, views, permissions, API tests | workspace-write |
| `django-security-agent` | Security review; remediation only when asked | confirm-writes (every write asks) |
| `django-testing-agent` | Writes and runs tests; changes test code only | workspace-write |
| `django-performance-agent` | Measures and fixes query, cache and throughput problems | workspace-write |
| `django-documentation-agent` | Code-derived documentation | documentation-only (no shell) |
| `django-code-review-agent` | Pre-merge review with a verdict | read-only |

The modes are enforced by `hooks/django_pack_guard.py` from `hooks/security-policy.json`
(see [docs/security.md](../docs/security.md)).

## Invoking an agent

Start with `/django-engineering:orchestrate <request>`, or address an agent by name:

- `@django-engineering:django-model-agent add an Invoice model with a unique number per tenant`
- Plain language ("have the Django security agent review the accounts app"); Claude picks the agent.
- **Not sure which agent?** `@django-engineering:django-orchestrator <request>`: it routes to the
  smallest set of specialists. For full orchestration run
  `claude --agent django-engineering:django-orchestrator`.

Agents that can change code (`model`, `api`, `testing`, `performance`, `architecture`, `security`) follow
an **approval gate** written in their own file: they reply with a proposal ending in `AWAITING APPROVAL:`
and change nothing until your request, or your follow-up, authorises it. Say "apply it" in the first
request to skip the second round trip (breaking API changes still ask).

## Conventions

- Agent files are **canonical** content copied from the main repository
  ([CANONICAL-MANIFEST.json](../CANONICAL-MANIFEST.json)). Change them only as described in
  [TEAM_HANDOFF.md](../TEAM_HANDOFF.md#development-workflow).
- Frontmatter `tools` is the ceiling of what the agent may use; the guard denies anything else.
  Frontmatter `skills:` lists the plugin-namespaced skills and rules Claude Code preloads into the
  subagent (`django-engineering:<id>`).
- The orchestrator's `## Routing policy` section is rendered from
  [config/orchestration-policy.yaml](../config/orchestration-policy.yaml); edit both together.
- Specialists have no `Agent` tool and cannot start other agents. The orchestrator cannot delegate to
  itself.
- Agents read `${CLAUDE_PLUGIN_ROOT}/templates/<id>.template.md` and
  `${CLAUDE_PLUGIN_ROOT}/references/<id>.md`; the guard lets plugin agents read those folders
  (and `skills/`, `rules/`) without a prompt.
