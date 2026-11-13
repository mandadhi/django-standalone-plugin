---
name: operational-runbook
description: >-
  Output template for an operational runbook: a task or failure scenario with trigger,
  prerequisites, ordered verified steps, verification, rollback and escalation, derived from the
  actual system.
kind: output-template
agents: [django-documentation-agent]
project: django-agentic-engineering
abstract: >-
  Standard structure for a runbook that an operator can follow without prior knowledge, with every
  command and path taken from the repository.
sdlc_phase: Development
tech_stack: [Python, Django, Markdown, Mermaid]
domain: [Software Engineering, Documentation]
---

# Operational Runbook Template

## Purpose

Give operators exact steps for a recurring task or a known failure, including how to check it worked and how to stop or undo.

## When to use

- A task operators perform (deploy, rotate, restore, scale) or a failure they must handle (worker stuck, queue backlog, failed migration).
- Not for architecture explanation; use the deployment documents.

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
| `{{runbook_title}}` | Task or scenario the runbook covers | task |

## Sections

| Section | Required | Content | Verifiable by |
|---|---|---|---|
| Overview | required | {{runbook_title}}: when it applies, who runs it, expected duration, risk | task |
| Prerequisites | required | Access, tools, backups, approvals needed before starting | repository, user |
| Procedure | required | Numbered steps, each with the exact command or action and the expected result | management commands, scripts |
| Verification | required | How to confirm success (health checks, queries, logs) | code, settings |
| Rollback and abort | required | How to stop safely and return to the previous state | migration reversibility |
| Escalation | optional | Who to contact and what to hand over; roles, not personal data | user |
| Assumptions and open questions | required | Unverified commands, unknown environment facts | — |

## Filling rules

- Apply the [filling conventions](README.md#filling-conventions).
- Register the document and keep it consistent with its registry entry: [registry protocol](../references/sdlc-documentation-registry.md).
- State only facts that are in a source document or in the code; otherwise write `Assumption A<n>:` with what would confirm it, or an open question. Never invent requirements, environments, metrics or decisions (`DOC-M1`, `DOC-M15`).
- Never include secret values, real hostnames or personal data (`DOC-M3`).
- Every command, management command and path exists in the repository; unverified ones are marked `unverified`.
- Destructive steps carry an explicit warning and a prior backup step.
- Use placeholders for hosts and credentials: `<db-host>`, `<your-api-token>`.

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

## Overview
{{runbook_title}}: <when, who, duration, risk>

## Prerequisites
- <prerequisite>

## Procedure
1. <action> - expect: <result>

## Verification
- <check>

## Rollback and abort
- <step>

## Escalation
- <role>

## Assumptions and open questions
- A1: <assumption>
````

## Completion checklist

- [ ] An operator can follow the steps in order; each has an expected result.
- [ ] Verification and rollback are present.
- [ ] Registry entry created or updated (RUN).
