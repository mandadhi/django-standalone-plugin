---
name: maintenance-record
description: >-
  Output template for maintenance documents of one registry type: changelog, incident report, root
  cause analysis, technical debt register and architecture updates, from facts that were provided
  or found.
kind: output-template
agents: [django-documentation-agent, django-architecture-agent]
project: django-agentic-engineering
abstract: >-
  Standard structure for records of change and learning after release, in which incident facts
  come from people or logs and causes are separated from suspicions.
sdlc_phase: Development
tech_stack: [Python, Django, Markdown, Mermaid]
domain: [Software Engineering, Documentation]
---

# Maintenance Record Template

## Purpose

Keep an honest, searchable record of what changed, what went wrong and why, what debt exists and how the architecture moved away from its approved design.

## When to use

- A release was made (changelog), an incident or defect occurred (incident report, RCA), debt was found (register), the architecture changed after approval (architecture update).
- Not for blame: records describe systems and decisions.

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
| `{{record_kind}}` | `changelog`, `incident`, `rca`, `debt-register` or `architecture-update` | task |

## Sections

| Section | Required | Content | Verifiable by |
|---|---|---|---|
| Record | required | Kind {{record_kind}}, period or incident window, affected components and documents | task |
| Entries | required | Changelog: version, date, added/changed/fixed/removed, breaking marked. Incident: timeline, impact, detection, response. Debt: item, location, impact, effort, priority. Architecture update: what changed against which approved document | commits, logs, user statements |
| Root cause analysis | optional | Causal chain from evidence, contributing factors, what was ruled out; suspicion labelled | logs, code, tests |
| Actions | required | Corrective and preventive actions with owner and the documents or tests they update | — |
| Assumptions and open questions | required | What is not yet known | — |

## Filling rules

- Apply the [filling conventions](README.md#filling-conventions).
- Register the document and keep it consistent with its registry entry: [registry protocol](../references/sdlc-documentation-registry.md).
- State only facts that are in a source document or in the code; otherwise write `Assumption A<n>:` with what would confirm it, or an open question. Never invent requirements, environments, metrics or decisions (`DOC-M1`, `DOC-M15`).
- Never include secret values, real hostnames or personal data (`DOC-M3`).
- Incident facts (timeline, impact) come from the user or logs they provided; do not reconstruct them.
- Separate *cause* (evidenced) from *suspected cause*. State what was ruled out.
- Changelog entries follow the project's convention and mark breaking changes; derive them from the change set and commit messages, not from memory.
- No secrets, customer data or personal data in any record.

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

## Record
<Kind: {{record_kind}}. Period or window, components, document ids.>

## Entries
| Item | Detail | Evidence |
|---|---|---|

## Root cause analysis
<Causes with evidence; suspected causes labelled.>

## Actions
| Action | Owner | Document or test |
|---|---|---|

## Assumptions and open questions
- A1: <assumption>
````

## Completion checklist

- [ ] Every entry has evidence or a stated source.
- [ ] Actions reference owners and the documents or tests that change.
- [ ] Registry entry created or updated.
