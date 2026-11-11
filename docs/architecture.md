# Architecture

The plugin root **is** the Claude Code plugin root. Claude Code loads every component in place from the
folders declared in `.claude-plugin/plugin.json`; nothing is copied, generated or injected at run time.

```text
user ──/django-engineering:orchestrate──▶ entry skill ──▶ django-orchestrator  (read-only)
        (or @django-engineering:<agent> directly)
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

## User-facing surface

The `/` menu shows exactly one entry: `/django-engineering:orchestrate`, the `skills/orchestrate/SKILL.md`
entry skill (`disable-model-invocation: true`, so only the user starts it). It passes the request to
`django-orchestrator` and carries out what the orchestrator returns. When the orchestrator runs as a subagent
and cannot start subagents, it returns a routing plan; the main session runs the plan and hands the results
back to the orchestrator in reconcile mode. All routing, approval and reporting rules stay in the
orchestrator agent and `config/orchestration-policy.yaml`. Every other skill and every rule carries
`user-invocable: false`. There is no `commands/` folder.

Git and pull requests: the orchestrator's *Delivery* section prepares the branch, the exact files to stage,
the commit message and the PR description, read-only. The main session runs each commit, push and
`gh pr create` only after the user approves that action. It never force-pushes and never stages unrelated
changes.

## Components

| Folder | Role |
|---|---|
| `agents/` | Orchestrator and nine specialists: *who* does the work and within which limits |
| `skills/` | Eleven internal knowledge bundles (*how* Django work is done well) and the `orchestrate` entry skill |
| `rules/` | Twelve internal mandatory rule sets with numbered requirements (`SEC-M4`, `PRF-M1`, ...) |
| `templates/` | Twelve report structures agents fill in |
| `references/` | Seven checklists and lookup tables shared by several agents |
| `hooks/` | The fail-closed security guard and its policy |
| `config/orchestration-policy.yaml` | The one place that says how specialists are selected and coordinated |

Separation of concerns: an agent owns its responsibilities, tools and boundaries; skills own knowledge;
rules own requirements; templates own report shape; references own checklists; the orchestration policy
owns routing. None of them repeats another.

## Orchestration model

`config/orchestration-policy.yaml` defines the orchestrator, its limits (at most 8 delegations, 2 attempts
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
- **Subagent** (an `@` mention): Claude Code subagents usually cannot spawn subagents. The orchestrator
  then returns a **ROUTING PLAN** and the main session executes it with the same limits.

## Why there is no `commands/` layer

Before 2.0.0, each command briefed one agent and applied that agent's approval gate. Agents are already invocable by
name, so the extra layer duplicated entry points and kept safety logic outside the agent: calling an agent
directly, or through the orchestrator, bypassed it. The gate (propose, wait for approval, then write) now
lives in each agent's `## Approval gate` section, so it holds on every path. The orchestrator passes
approvals through and never grants them. The single slash command added in 3.0.0 is an entry *skill*
(`skills/orchestrate/`), not a command layer: it holds no gate and no routing, and only hands the request to
the orchestrator.

Delegation limits and the retry rule are instructions the orchestrator follows; only the **target
allowlist** is enforced by the guard.

## What skills, rules, templates and the two kinds of references are for

Every file answers one question, so nothing is written twice:

| Component | Question | Scope | Loaded |
|---|---|---|---|
| Skill `skills/<id>/SKILL.md` | How does this work and how is it done well? | One topic area | Preloaded into the agents that list it |
| Skill references `skills/<id>/references/*.md` | The detail behind that skill, one file per sub-topic | **One skill** | On demand, one to three at a time, when a step needs them (keeps context small) |
| Rule `rules/<id>/SKILL.md` | What must every result satisfy? (numbered MUST/SHOULD ids) | Cross-cutting | Preloaded; ids are cited in findings |
| Shared reference `references/<id>.md` | What do I check, where, and how do I rate it? (checklists, search patterns, lookup tables) | **Several agents** | Read on demand by the agents that list them |
| Template `templates/<id>.template.md` | What shape does the report take? | One report kind | Read when the agent writes its report |

The split between the two reference kinds is ownership. A *skill reference* is the long-form depth of a
single skill: `skills/django-orm/references/query-optimization.md` explains how `select_related` works, and
only agents that preload `django-orm` ever need it. A *shared reference* belongs to no skill because several
agents run the same checklist: `references/django-security-checklist.md` is used by the security, API and
code-review agents, and points at rule ids and skill references instead of copying them. Shared references
keep those agents consistent and stop each from carrying its own copy of a checklist; skill references are
progressive disclosure, so an agent loads detail only when a step needs it.
`tests/test_templates_and_references.py` checks that shared references link instead of copy.

## What is deliberately absent

No Python runtime services, workflow engine, execution database, checkpoints, run records, approver or
audit log. Those belong to the separate Django Agentic Harness product, which this distribution neither
contains nor depends on.
