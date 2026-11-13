---
name: django-document
description: >-
  Manage project documentation across the SDLC for a Django or DRF project: the documentation
  registry, requirements, deployment, runbook and maintenance documents, technical documentation from
  the actual code, stale and conflict detection, and documentation impact assessment. Changes
  documentation files only. Runs the django-documentation-agent.
argument-hint: "<documents and audience> [--stage <stage>] [--profile <minimal|standard|enterprise>] [--check] [--impact <changed files|git>] [--paths <code paths>] [--out <docs dir>] [--dry-run]"
project: django-agentic-engineering
abstract: >-
  Developer command that briefs django-documentation-agent to write code-derived documentation,
  restricted to documentation files and verified against the code.
sdlc_phase: Development
tech_stack: [Python, Django, Django REST Framework, Markdown, OpenAPI, Mermaid]
domain: [Software Engineering, Documentation]
---

# /django-document

## Purpose

Use to create and maintain documentation across the SDLC: documentation that matches the code, the
registry that indexes it, documents for each SDLC stage, and the review of what a change makes stale. Every
statement is traced to the code or to a stated source.

## Arguments

`$ARGUMENTS`

- Free text (required): which documents, for which audience (for example "API reference for
  the orders app, for frontend developers").
- `--paths <code paths>`: the code to document. Default: inferred from the request.
- `--out <docs dir>`: where documentation goes. Default: the project's existing docs layout.
- `--stage <stage>`: `requirements`, `architecture`, `detailed-design`, `development`, `testing`, `deployment`
  or `maintenance`: produce the applicable documents of that stage that are missing or stale. Default: inferred.
- `--profile <minimal|standard|enterprise>`: the registry profile to record on first use. Default: proposed from
  the project and confirmed with the user.
- `--check`: lifecycle check only. Report missing, stale, unregistered and conflicting documents and registry
  problems; write nothing.
- `--impact <changed files|git>`: documentation impact assessment of the named files (or the working-tree change set,
  from `git diff --name-only`); update the documents the documentation agent owns that are affected and recommend the
  rest to their owners.
- `--dry-run`: return the documents in the reply and write nothing.
- `@file` mentions (existing docs, change reports) are passed as context.

## Agent

Delegate to the `django-documentation-agent` subagent. It owns fact gathering, structure and
verification; this command supplies the brief and the documentation-only boundary. The main
session does not write documentation itself.

## Skills and rules

Tell the agent to apply these, by id. In the Django Engineering Pack they live at
`skills/<id>/SKILL.md` and `rules/<id>/SKILL.md`
(installed plugin: under `${CLAUDE_PLUGIN_ROOT}`, and preloaded into the agent).

- Skills: `django-core` · `django-architecture` · `django-rest-framework`
- Rules: `django-security-standards` · `django-documentation-standards`

## Documentation context

Tell the agent to follow `DOC-M9` to `DOC-M16` and the registry protocol in the pack at `references/sdlc-documentation-registry.md`
(installed plugin: `${CLAUDE_PLUGIN_ROOT}/references/sdlc-documentation-registry.md`): read `docs/sdlc/registry.json` first, consume current
documents, review stale ones, never edit an `approved` document in place, report conflicts, and state assumptions
instead of inventing details. The workflow is defined once, in that reference; this command adds only the following.

- This command manages the documentation lifecycle: registry creation or adoption, stage documents (requirements, deployment, runbooks, maintenance),
  stale and conflict detection, cross-document consistency and documentation impact assessment. It never duplicates another command's workflow: documents
  owned by another agent are recommended to it, or persisted here when that agent returned them.
- Applicability comes from the registry `profile`, `facts` and `not_applicable` list; the agent does not generate every document.

## Authorization

- **Documentation changes only.** The agent may create or edit documentation files
  (`docs/`, `README*`, other `*.md`, and the `--out` directory). It never changes application
  code, settings, migrations or tests. Docstrings change only if the user asks for them by name.
- **Approved documents are never edited in place.** A revision is written as a proposed file beside the
  document and recorded as a pending revision in the registry; the user approves it.
- `--check` and `--dry-run` write nothing.
- A request that needs a code change is out of scope: say so and point to the right command
  (`/django-model`, `/django-api`, `/django-test`).
- `--dry-run`: nothing is written.
- If the result lists any changed file that is not documentation, report it to the user as a
  boundary violation. Do not revert anything automatically.
- No secret values, real credentials, internal hostnames or personal data in any document.

## Steps

1. Parse the documents, audience, stage, profile, `--check`, `--impact`, code paths, output location and `--dry-run`.
   For `--impact git`, run `git diff --name-only` (read-only) and pass the file list, because the agent has no shell.
2. Brief the agent:
   - **Objective:** the documents to create or update, and the audience.
   - **Constraints:** documentation files only; location; `--check` or `--dry-run` if given.
   - **Inputs:** code paths, the change list, `@file` context, the stage and profile.
   - **Expected outputs:** the documents, the registry changes and a documentation report.
3. Check the reported file list against the documentation-only boundary.
4. Relay the documentation report.

## Expected output

The documentation report: each document with its action (created or updated), audience and
code sources; statements that could not be verified; open questions. With `--dry-run`, the
document content itself.

Template: `technical-documentation` for the report and code-derived documents; the stage templates
(`requirements-specification`, `traceability-matrix`, `deployment-and-release`, `operational-runbook`,
`maintenance-record`) for the documents of those types. Templates are in the pack
at `templates/<id>.template.md`
(installed plugin: `${CLAUDE_PLUGIN_ROOT}/templates/<id>.template.md`). Name them in the brief's expected outputs so the agent's reply
follows their structure.

## Completion criteria

- [ ] Every requested document exists (or is returned, with `--dry-run`).
- [ ] Only documentation files changed, and no approved document was edited in place.
- [ ] The registry matches the files; stale, missing and conflicting documents are reported with owners.
- [ ] Endpoints, settings, commands and paths in the documents were checked against the code.
- [ ] Unverified statements and open questions are listed.
