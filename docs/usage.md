# Usage

Open Claude Code in a Django project (a clean git working tree is recommended).

## The orchestrator

Give a request; the orchestrator classifies it, picks the smallest set of specialists, briefs them,
reconciles their results against your original request and reports.

```text
/django-engineering:orchestrate Add an invoices API with its model and tests
/django-engineering:orchestrate --plan-only Why is the orders list slow?
/django-engineering:orchestrate --category data-model Add a nullable archived_at to Order
```

| Argument | Meaning |
|---|---|
| `<request>` | Plain language; `@file` mentions are passed on as context |
| `--plan-only` | Return the routing plan without running any specialist |
| `--category <id>` | Skip classification; use this category of the routing policy |

Other ways to reach it: `claude --agent django-engineering:django-orchestrator` (orchestrator as the main
agent), or a plain request such as "have the Django orchestrator review this branch" (Claude Code chooses
agents itself; not guaranteed).

The report states: outcome (complete / partial / not started), the route and why, per-step results,
verification performed **and not performed**, assumptions, unresolved issues and follow-up commands.

If the orchestrator runs as a subagent that cannot start subagents, it returns a **ROUTING PLAN**; the
command then runs that plan from the main session under the same limits.

## Specialist commands

| Command | Arguments | Use it to | Changes files |
|---|---|---|---|
| `/django-engineering:django-analyze` | `[project path \| focus question] [--paths <glob,...>] [--exclude <glob,...>]` | Profile an unfamiliar project | never |
| `/django-engineering:django-design` | `<feature, refactoring or system> [--profile <file>] [--out <dir>] [--scaffold]` | Architecture, ADRs, plan | docs with `--out`; scaffold after approval |
| `/django-engineering:django-model` | `<entities and changes> [--app <label>] [--design <file>] [--apply]` | Models, constraints, migrations | after approval (or `--apply`) |
| `/django-engineering:django-api` | `<resources and operations> [--design <file>] [--version <v>] [--apply]` | DRF endpoints and API tests | after approval (or `--apply`) |
| `/django-engineering:django-security` | `[scope] [--base <git ref>] [--fix [SEC-001,...]]` | Security assessment | only with `--fix`; each write asks |
| `/django-engineering:django-test` | `<path, module, endpoint or change> [--base <git ref>] [--run-only] [--apply]` | Write and run tests | test code only |
| `/django-engineering:django-optimize` | `<slow endpoint, view, task or path> [--target <metric and goal>] [--apply]` | Measure and fix performance | after approval (or `--apply`) |
| `/django-engineering:django-document` | `<documents and audience> [--paths <code paths>] [--out <docs dir>] [--dry-run]` | Code-derived documentation | documentation files only |
| `/django-engineering:django-review` | `[--base <git ref>] [paths...] [--focus <areas>] [--threshold <severity>]` | Pre-merge review with a verdict | never |

Each command file in [`commands/`](../commands/README.md) documents its exact arguments, gate and expected
output. Reports follow the templates in [`templates/`](../templates/README.md).

## Skills and rules

Skills (`django-engineering:django-orm`, ...) and rules (`django-engineering:django-security-standards`, ...)
are preloaded into the agents that need them. You can also ask Claude to load one directly in a session.

## Tips

- Work on a branch with a clean tree; review every diff.
- Agents never run `migrate`, `flush`, `dbshell` or SQL against a non-test database, and never use the
  network, without your explicit approval. Denied tool calls are final; the agent reports them.
- In non-interactive (`claude -p`) mode, approval prompts cannot be answered, so actions that need approval
  are refused.
