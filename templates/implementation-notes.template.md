---
name: implementation-notes
description: >-
  Output template for implementation notes: what was built or changed, where it deviates from the
  approved design and why, decisions taken, configuration and migrations to know about, and the
  documents that must follow.
kind: output-template
agents: [django-model-agent, django-api-agent, django-testing-agent, django-performance-agent]
project: django-agentic-engineering
abstract: >-
  Standard structure for a short record, written after implementation, that links the code change
  to the design it implements and states every deviation and its reason.
sdlc_phase: Development
tech_stack: [Python, Django, Markdown, Mermaid]
domain: [Software Engineering, Documentation]
---

# Implementation Notes Template

## Purpose

Capture what is not obvious from the diff: the design it implements, the deviations, the decisions, operational impact and the documentation that changed with it.

## When to use

- After implementing a model, API, performance or test change that follows or departs from a design document.
- A change with non-obvious decisions, configuration or migration steps.
- Not a changelog entry or a code review; link to those.

## Placeholders

| Placeholder | Meaning | Source |
|---|---|---|
| `{{subject}}` | The document's subject | task objective |
| `{{project_name}}` | Name of the Django project | registry `project` or project profile |
| `{{scope}}` | What the document covers and does not cover | task |
| `{{prepared_by}}` | Agent or person producing the document | producer |
| `{{date}}` | Date (ISO 8601) | producer |
| `{{document_status}}` | `draft`, `approved` or `stale` (registry status; an agent writes `draft`) | registry entry |
| `{{sources}}` | Documents and code files the content is derived from | inputs, registry `sources` |
| `{{doc_id}}` | Registry document id, for example `SRS-001` | registry entry |
| `{{doc_type}}` | Catalog type code, for example `SRS` | catalog |
| `{{version}}` | Document version, `MAJOR.MINOR` | registry entry |
| `{{change_summary}}` | One-paragraph description of what changed | diff |

## Sections

| Section | Required | Content | Verifiable by |
|---|---|---|---|
| Summary | required | {{change_summary}} | diff |
| Design implemented | required | Design document ids and sections, or `none` | registry ids |
| Deviations | required | Each difference from the design: what, why, impact; `none` when identical | `file:line` and design section |
| Decisions | optional | Choices made while implementing; hard-to-reverse ones link an ADR | ADR ids |
| Configuration and migrations | optional | New settings or environment variables (name and purpose only), migrations and their risk | settings, migration files |
| Files changed | required | Files created or edited | diff |
| Documentation impact | required | Registry ids updated, ids recommended for update (with owner), ids unaffected | impact map |
| Open questions | required | Unresolved items | — |

## Filling rules

- Apply the [filling conventions](README.md#filling-conventions).
- Register the document and keep it consistent with its registry entry: [registry protocol](../references/sdlc-documentation-registry.md).
- State only facts that are in a source document or in the code; otherwise write `Assumption A<n>:` with what would confirm it, or an open question. Never invent requirements, environments, metrics or decisions (`DOC-M1`, `DOC-M15`).
- Never include secret values, real hostnames or personal data (`DOC-M3`).
- Contributors append their own section under *Deviations* and *Decisions*; they do not rewrite another agent's text.
- Describe settings by name and purpose only; never values.
- A deviation from an approved document is a reported conflict until the user decides; link it, do not resolve it here.

## Output structure

````markdown
# {{subject}}

| Field | Value |
|---|---|
| Document ID | {{doc_id}} |
| Type | {{doc_type}} |
| Version | {{version}} |
| Project | {{project_name}} |
| Scope | {{scope}} |
| Prepared by | {{prepared_by}} |
| Date | {{date}} |
| Status | {{document_status}} |
| Sources | {{sources}} |

## Summary
{{change_summary}}

## Design implemented
<Document ids and sections, or none.>

## Deviations
| Design says | Implementation does | Reason | Documents to update |
|---|---|---|---|

## Decisions
- <decision and reason>

## Configuration and migrations
| Item | Purpose | Reference |
|---|---|---|

## Files changed
- <path>

## Documentation impact
| Document | Action | Owner |
|---|---|---|

## Open questions
- <question>
````

## Completion checklist

- [ ] Every deviation from a design document is listed with a reason.
- [ ] Documentation impact lists updated, recommended and unaffected documents.
- [ ] Registry entry created or updated.
