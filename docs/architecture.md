# Architecture

The plugin root **is** the Claude Code plugin root. Claude Code loads every component in place from the
folders declared in `.claude-plugin/plugin.json`; nothing is copied, generated or injected at run time.

```text
user ──/django-engineering:orchestrate──▶ command (thin entry point)
                                              │ briefs
                                              ▼
                                    django-orchestrator  (read-only)
                    classify ▸ select route ▸ brief ▸ sequence ▸ reconcile ▸ report
                                              │ Agent tool, only to the nine specialists
              ┌───────────────┬───────────────┼────────────────┬───────────────┐
              ▼               ▼               ▼                ▼               ▼
        project-analyzer  architecture     model / api    security / testing   documentation /
        (read-only)       (workspace)      (workspace)    / performance        code-review
                                                                              (docs-only / read-only)
   every tool call of every plugin agent ──▶ hooks/django_pack_guard.py (PreToolUse / PostToolUse)
   each specialist preloads its skills and rules; reads templates/ and references/ on demand
```

## Components

| Folder | Role |
|---|---|
| `agents/` | Orchestrator and nine specialists: *who* does the work and within which limits |
| `commands/` | Slash commands: entry points that brief one agent and apply approval gates |
| `skills/` | Twelve knowledge bundles: *how* Django work is done well |
| `rules/` | Twelve mandatory rule sets with numbered requirements (`SEC-M4`, `PRF-M1`, ...) |
| `templates/` | Twelve report structures agents fill in |
| `references/` | Seven checklists and lookup tables shared by several agents |
| `hooks/` | The fail-closed security guard and its policy |
| `config/orchestration-policy.yaml` | The one place that says how specialists are selected and coordinated |

Separation of concerns: an agent owns its responsibilities, tools and boundaries; skills own knowledge;
rules own requirements; templates own report shape; references own checklists; the orchestration policy
owns routing. None of them repeats another.

## Orchestration model

`config/orchestration-policy.yaml` defines the orchestrator, its limits (at most 6 delegations, 2 attempts
per step, 3 clarifying questions), the nine delegable specialists, the task categories with signals and
routes (ordered steps with `after` dependencies and optional steps with a `when` condition), step
constraints, clarification triggers, failure policy, completion criteria and security boundaries.

Its routing section is rendered into `agents/django-orchestrator.md` (between the `GENERATED` markers) and
its specialist list into the guard policy's `delegates` allowlist. `tests/test_orchestration_policy.py`
keeps the three in step.

The orchestrator: (1) reads the request and repository context; (2) classifies the category and the risk;
(3) asks only when the policy says it matters; (4) selects the smallest route; (5) briefs each specialist
with objective, inputs, constraints and expected output; (6) runs steps in order (independent read-only
steps may run in parallel, writing steps never); (7) applies the failure policy (one retry, no dependent
step after a failure); (8) reconciles against the original request; (9) reports honestly.

Two ways it runs:

- **Main agent** (`claude --agent django-engineering:django-orchestrator`): it has the `Agent` tool and
  delegates itself.
- **Subagent** (via `/django-engineering:orchestrate`): Claude Code subagents usually cannot spawn
  subagents. The orchestrator then returns a **ROUTING PLAN** and the command executes it from the main
  session with the same limits.

Delegation limits and the retry rule are instructions the orchestrator follows; only the **target
allowlist** is enforced by the guard.

## What is deliberately absent

No Python runtime services, workflow engine, execution database, checkpoints, run records, approver or
audit log. Those belong to the separate Django Agentic Harness product, which this distribution neither
contains nor depends on.
