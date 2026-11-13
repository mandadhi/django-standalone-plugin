---
name: django-model
description: >-
  Create or change Django models, relationships, constraints, indexes and the migrations that
  apply them, with a migration-risk assessment. Proposes first and writes only after approval.
  Runs the django-model-agent.
argument-hint: "<entities and changes> [--app <label>] [--design <file>] [--apply]"
project: django-agentic-engineering
abstract: >-
  Developer command that briefs django-model-agent to design and, once authorized, implement
  model and migration changes with constraints, indexes and a migration risk assessment.
sdlc_phase: Development
tech_stack: [Python, Django, PostgreSQL]
domain: [Software Engineering, Data]
---

# /django-model

## Purpose

Use to add or change the data layer: new models or fields, relationships, invariants as
database constraints, indexes for real queries, and data migrations. Every proposal states its
migration risk before any file changes.

## Arguments

`$ARGUMENTS`

- Free text (required): the entities, fields, relationships and rules to add or change.
- `--app <label>`: the owning app, if not obvious from the request.
- `--design <file>`: a `/django-design` result to follow.
- `--apply`: the user authorizes writing the proposed changes without a second confirmation.
- `@file` mentions (current models, requirements) are passed as context.

If cardinality, ownership or `on_delete` behaviour is ambiguous, ask before delegating.

## Agent

Delegate to the `django-model-agent` subagent. It owns model design, migration generation and
risk assessment; this command supplies the brief and the authorization gate. The main session
does not edit models or migrations itself.

## Skills and rules

Tell the agent to apply these, by id. In the Django Engineering Pack they live at
`skills/<id>/SKILL.md` and `rules/<id>/SKILL.md`
(installed plugin: under `${CLAUDE_PLUGIN_ROOT}`, and preloaded into the agent).

- Skills: `django-orm` · `postgresql-engineering` · `django-architecture`
- Rules: `django-security-standards` · `django-model-standards` · `django-database-standards` · `django-coding-standards` · `django-testing-standards` · `django-documentation-standards`

## Documentation context

Tell the agent to follow `DOC-M9` to `DOC-M16` and the registry protocol in the pack at `references/sdlc-documentation-registry.md`
(installed plugin: `${CLAUDE_PLUGIN_ROOT}/references/sdlc-documentation-registry.md`): read `docs/sdlc/registry.json` first, consume current
documents, review stale ones, never edit an `approved` document in place, report conflicts, and state assumptions
instead of inventing details. The workflow is defined once, in that reference; this command adds only the following.

- Consume the database design (DBD), ERD, HLD and LLD. A proposal that contradicts an approved document is reported before anything is written.
- After the user approves and the change is applied, the agent updates DBD, ERD (Mermaid) and migration documentation for risky migrations, and
  registers them. Documentation is written under the same approval as the code. LLD and API updates are recommended to their owners.

## Authorization

Code changes need explicit approval.

1. **Proposal (always first).** The agent reads the code and returns the model design and the
   migration plan with risks. It must not create or change files; only `--check --dry-run` and
   `sqlmigrate` of existing migrations are allowed.
2. **Approval.** Show the proposal and ask the user to approve it, unless `--apply` was given.
3. **Implementation.** Brief the agent with the approved proposal. It writes models,
   migrations and tests in the workspace, and updates the documents it owns (database design, ERD,
   migration documentation) under `docs/` and in the registry. An `approved` document is never edited in place.

Never, even with `--apply`: `migrate`, `flush`, `dbshell`, `loaddata` or SQL against a
non-test database, and never editing a migration that may already be applied. Give the user
the command to run instead.

## Steps

1. Parse the change request, app, design and `--apply`.
2. Brief the agent for the proposal:
   - **Objective:** the requested model change.
   - **Constraints:** proposal only; backend, downtime limits and compatibility from the user.
   - **Inputs:** design, profile and `@file` context.
   - **Expected outputs:** model design and migration plan with risks.
3. Apply the authorization gate above.
4. Brief the agent to implement the approved proposal and verify it.
5. Relay the report, including the deployment notes and any command a human must run.

## Expected output

Proposal: the changes, constraints, indexes and migration plan with lock, rewrite and backfill
risk. After implementation: the model change report (files, migrations, verification commands
and results, deployment notes, open questions).

Templates: `django-model-specification` for the proposal and the report; `migration-plan` when
the migration risk is medium or high. Templates are in the pack at
`templates/<id>.template.md`
(installed plugin: `${CLAUDE_PLUGIN_ROOT}/templates/<id>.template.md`). Name them in the brief's expected outputs so the agent's reply
follows their structure.

## Completion criteria

- [ ] The migration risk was shown before any file changed.
- [ ] Files changed only after the user's approval or `--apply`.
- [ ] `makemigrations --check --dry-run` is clean and the constraint tests pass, or the failure
      is reported verbatim.
- [ ] No migration or SQL ran against a non-test database.
