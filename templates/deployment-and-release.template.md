---
name: deployment-and-release
description: >-
  Output template for deployment documents of one registry type: deployment architecture,
  infrastructure design, CI/CD design, environment configuration reference, release plan, rollback
  plan and deployment diagram, derived from the actual implementation.
kind: output-template
agents: [django-documentation-agent]
project: django-agentic-engineering
abstract: >-
  Standard structure for deployment and release documents in which every statement cites a
  repository file or a user statement and unknown environment facts are listed as gaps.
sdlc_phase: Development
tech_stack: [Python, Django, Markdown, Mermaid]
domain: [Software Engineering, Documentation]
---

# Deployment and Release Template

## Purpose

Describe how the system is built, deployed, configured and released, and how to go back, based on what the repository actually contains and what the user states.

## When to use

- Deployment, pipeline or infrastructure files exist, or the user describes the environment.
- Preparing a release or a rollback procedure.
- Not for run-time operating procedures; use the [operational runbook](operational-runbook.template.md).

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
| `{{deployment_basis}}` | Repository files and user statements the document rests on | repository, user |

## Sections

| Section | Required | Content | Verifiable by |
|---|---|---|---|
| Basis and gaps | required | Evidence used ({{deployment_basis}}) and what could not be established | file paths |
| Architecture | optional | Runtime topology: processes, services, data stores, networking; embedded deployment diagram | Dockerfile, compose, infrastructure code |
| Infrastructure | optional | Resources and how they are provisioned | infrastructure code |
| CI/CD pipeline | optional | Stages, triggers, gates, artifacts, approvals | pipeline files |
| Environment configuration | optional | Per environment: setting or variable name, purpose, required, differences; never values | settings modules |
| Release plan | optional | Scope, preconditions, ordered steps, migrations, verification, communication, owners | change set, migrations |
| Rollback plan | optional | Triggers, ordered steps, data and migration reversibility, verification | migration reversibility |
| Assumptions and open questions | required | Environment facts to confirm | — |

## Filling rules

- Apply the [filling conventions](README.md#filling-conventions).
- Register the document and keep it consistent with its registry entry: [registry protocol](../references/sdlc-documentation-registry.md).
- State only facts that are in a source document or in the code; otherwise write `Assumption A<n>:` with what would confirm it, or an open question. Never invent requirements, environments, metrics or decisions (`DOC-M1`, `DOC-M15`).
- Never include secret values, real hostnames or personal data (`DOC-M3`).
- Cite the file for each fact (`Dockerfile:3`); user statements are labelled `stated by user`.
- Where no deployment evidence exists write `not established` and ask; never describe a typical environment as if it were this one.
- A rollback plan states which migrations are irreversible and what that means for data.
- Setting and variable names and purposes only; no values, hostnames or credentials.

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

## Basis and gaps
<Evidence: {{deployment_basis}}. Gaps: <list>.>

## Architecture
<!-- mermaid-source: docs/diagrams/<file>.mmd -->
```mermaid
<diagram>
```

## Infrastructure
| Resource | Purpose | Defined in |
|---|---|---|

## CI/CD pipeline
| Stage | Trigger | Does | Gate |
|---|---|---|---|

## Environment configuration
| Name | Purpose | Required | Dev | Staging | Production |
|---|---|---|---|---|---|

## Release plan
1. <step> - verify: <check>

## Rollback plan
| Trigger | Action | Data impact | Verification |
|---|---|---|---|

## Assumptions and open questions
- A1: <assumption>
````

## Completion checklist

- [ ] Every statement is traced to a file or the user.
- [ ] Gaps are listed; rollback covers migrations.
- [ ] Diagrams validated and registered; registry entry created or updated.
