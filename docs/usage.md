# Usage

Open Claude Code in a Django project (a clean git working tree is recommended).

## How to call an agent

Use a slash command (`/django-engineering:orchestrate <request>`, `/django-engineering:django-model ...`) or name
an agent directly. Either way the agent loads the skills, rules, templates and references it needs by itself.

```text
@django-engineering:django-model-agent add an Invoice model with a unique number per tenant
@django-engineering:django-security-agent review the accounts app
have the Django code review agent check this branch against main        (plain language)
@django-engineering:django-orchestrator add an invoices API with its model and tests   (not sure who?)
```

`@` offers every `django-engineering:` agent as you type. In plain language Claude picks the agent itself
(not guaranteed; name the agent when it matters). For orchestration with no nesting limit, make the
orchestrator the main agent: `claude --agent django-engineering:django-orchestrator`.

## Which agent

| Agent | Use it to | Changes files |
|---|---|---|
| `django-orchestrator` | Anything you cannot assign yourself, or work that needs several specialists | never itself; only through specialists |
| `django-project-analyzer` | Profile an unfamiliar project | never |
| `django-architecture-agent` | Architecture, boundaries, ADRs, implementation plan | design docs in a directory you name; scaffolding after approval |
| `django-model-agent` | Models, constraints, indexes, migrations | after approval |
| `django-api-agent` | DRF endpoints, permissions, API tests | after approval (breaking changes always asked) |
| `django-security-agent` | Security assessment; fixes on request | only approved findings; every write asks |
| `django-testing-agent` | Write and run tests | test code only, after approval |
| `django-performance-agent` | Measure and fix performance | after approval |
| `django-documentation-agent` | SDLC documentation: registry, requirements, deployment, runbooks, maintenance, code-derived documents | documentation files only |
| `django-code-review-agent` | Pre-merge review with a verdict | never |

Reports follow the templates in [`templates/`](../templates/README.md).

## Approvals

Agents that can change code propose first. They reply with the plan (model design and migration risk,
endpoint contract, test plan, measured bottlenecks, findings to fix, paths to scaffold), end with
`AWAITING APPROVAL:` and change nothing. Answer "go ahead" (or name the findings to fix) and Claude
re-briefs the agent with your approval. To skip the round trip, say so in the request: "add an Invoice model
and apply it". These always ask regardless: breaking API changes, `migrate` and other destructive
operations, network use, and every write by the security agent.

The orchestrator never approves for you. If a step returns `AWAITING APPROVAL:`, the route stops there and the
report says what is waiting.

## The orchestrator

It classifies the request, picks the smallest set of specialists from
[`config/orchestration-policy.yaml`](../config/orchestration-policy.yaml), briefs them, reconciles their
results against your request and reports: outcome (complete / partial / not started), route and why, per-step
results, verification performed **and not performed**, assumptions, unresolved issues and who owns each
follow-up. Ask for "a plan only" to see the route without running anything.

When it runs as a subagent (an `@` mention) it cannot start subagents, so it returns a **ROUTING PLAN** and
Claude runs the plan from the main session under the same limits.

## Skills and rules

Skills (`django-engineering:django-orm`, ...) and rules (`django-engineering:django-security-standards`, ...)
are preloaded into the agents that need them. You can also ask Claude to load one directly in a session.

## Tips

- Work on a branch with a clean tree; review every diff.
- Agents never run `migrate`, `flush`, `dbshell` or SQL against a non-test database, and never use the
  network, without your explicit approval. Denied tool calls are final; the agent reports them.
- In non-interactive (`claude -p`) mode, approval prompts cannot be answered, so actions that need approval
  are refused.
