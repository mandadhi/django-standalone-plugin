---
name: orchestrate
description: >-
  Hand a Django or DRF engineering request to the Django orchestrator, which plans it, delegates to
  the plugin's specialist agents, keeps the approval checkpoints and reports the result. Covers the
  whole lifecycle: requirements and design, implementation, tests, security, documentation, review
  and pull request preparation.
argument-hint: <what you want done, or a path to a requirements or design document>
disable-model-invocation: true
project: django-agentic-engineering
abstract: >-
  The plugin's single user-facing entry point. It only passes the request to the
  django-orchestrator agent and carries out what the orchestrator returns; all planning,
  routing, briefing and reconciliation rules live in the orchestrator agent.
sdlc_phase: Architecture/Planning
tech_stack: [Python, Django, Django REST Framework]
domain: [Software Engineering, AI Agents]
---

# Orchestrate a Django request

Request: $ARGUMENTS

This entry point owns no engineering or routing logic. The `django-engineering:django-orchestrator`
agent owns planning, specialist selection, briefs, ordering, approvals and the final report. Its
agent definition is the single source of those rules.

1. If the request is empty, ask the user what they want done and stop.
2. Start the `django-engineering:django-orchestrator` agent with the `Agent` tool. Pass the request
   verbatim, any files or documents the user attached, and anything already established in this
   conversation (an earlier project profile, design or approval).
3. Act on what it returns:
   - **A final report.** Show it to the user.
   - **A `ROUTING PLAN`** (it could not start subagents itself). Carry the plan out exactly as the
     orchestrator's *Routing plan (subagent mode)* section says: one `Agent` call per step, in order,
     with the brief the plan gives. Then start the orchestrator again in reconcile mode, passing the
     plan and every step result, and show the user its report.
   - **`AWAITING APPROVAL:`** from the orchestrator or from any step. Stop. Explain to the user what
     will happen if they approve and which steps have not run. Continue only on their explicit
     approval, quoting it in the next brief. Never approve on their behalf.
   - **A delivery proposal** (branch, commit, push or pull request). Follow the orchestrator's
     *Delivery* section. Each git action that changes history or a remote needs the user's own
     approval first.
4. Never report a step, test or check as done unless its result says so.
