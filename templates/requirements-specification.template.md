---
name: requirements-specification
description: >-
  Output template for requirements documents of one registry type: BRD, SRS, FRD, NFR, user
  stories or acceptance criteria, with identified, testable requirements, priorities, sources and
  open questions.
kind: output-template
agents: [django-documentation-agent]
project: django-agentic-engineering
abstract: >-
  Standard structure for requirements documents in which every requirement has an id, a source, a
  priority and a verification method, and nothing is inferred from code alone.
sdlc_phase: Development
tech_stack: [Python, Django, Markdown, Mermaid]
domain: [Software Engineering, Documentation]
---

# Requirements Specification Template

## Purpose

Record what the system must do and the qualities it must have, in identified, testable statements that design, code and tests can trace to. One structure serves BRD, SRS, FRD, NFR, user stories and acceptance criteria; the document type decides which sections are filled.

## When to use

- The user, stakeholders or an existing document provide requirements to record or restructure.
- Writing or revising a BRD, SRS, FRD, NFR, user stories or acceptance criteria.
- Not for describing what the code does today; use [technical documentation](technical-documentation.template.md).

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
| `{{requirements_basis}}` | Where the requirements come from (interviews, tickets, existing documents) | user input |

## Sections

| Section | Required | Content | Verifiable by |
|---|---|---|---|
| Context and stakeholders | required | Goal, users and stakeholders, constraints; business case for a BRD | user input or source document |
| Requirements | required | One row per requirement: id (`REQ-n`, `NFR-n`, `US-n`), statement, priority (MoSCoW), source, verification method | source document per row |
| User stories | optional | `As a <role> I want <capability> so that <benefit>`, each linked to requirements | requirement ids |
| Acceptance criteria | optional | Given/When/Then per story or requirement, observable and testable | test cases later trace to these |
| Non-functional requirements | optional | Measurable targets: performance, security, availability, compliance, with the measuring method | stated target values |
| Current behaviour (informational) | optional | What the existing system does, from the code, clearly labelled as not a requirement | `file:line` |
| Assumptions and open questions | required | Everything assumed or unknown, with the person who can confirm it | — |

## Filling rules

- Apply the [filling conventions](README.md#filling-conventions).
- Register the document and keep it consistent with its registry entry: [registry protocol](../references/sdlc-documentation-registry.md).
- State only facts that are in a source document or in the code; otherwise write `Assumption A<n>:` with what would confirm it, or an open question. Never invent requirements, environments, metrics or decisions (`DOC-M1`, `DOC-M15`).
- Never include secret values, real hostnames or personal data (`DOC-M3`).
- Requirements are testable: a statement that cannot be verified is rewritten or listed as an open question.
- Use stable ids; never renumber. A removed requirement is marked `withdrawn`, not deleted.
- A BRD states business goals and scope, an SRS software behaviour, an FRD functions in detail, an NFR measurable qualities.
- Do not derive requirements from code. Code facts go to *Current behaviour* and are confirmed with the user before they become requirements.

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

## Context and stakeholders
<Goal, stakeholders and constraints. Basis: {{requirements_basis}}>

## Requirements
| Id | Requirement | Priority | Source | Verification |
|---|---|---|---|---|

## User stories
| Id | Story | Requirements |
|---|---|---|

## Acceptance criteria
| Id | Applies to | Given | When | Then |
|---|---|---|---|---|

## Non-functional requirements
| Id | Quality | Target | How measured |
|---|---|---|---|

## Current behaviour (informational)
<Observed behaviour with file:line.>

## Assumptions and open questions
- A1: <assumption> (confirm with <role>)
````

## Completion checklist

- [ ] Every requirement has an id, a source, a priority and a verification method.
- [ ] Acceptance criteria exist for every must-have story or requirement.
- [ ] Nothing from the code is presented as a requirement without confirmation.
- [ ] Assumptions and open questions are listed; registry entry created or updated.
