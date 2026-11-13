---
name: detailed-design
description: >-
  Output template for detailed design documents of one registry type: LLD, component design,
  integration design, security design, and the sequence, activity, data-flow and workflow diagrams
  that belong to them.
kind: output-template
agents: [django-architecture-agent, django-security-agent]
project: django-agentic-engineering
abstract: >-
  Standard structure for low-level design where every element traces to the high-level design and
  to the code or the approved proposal, with diagrams as registered Mermaid sources.
sdlc_phase: Development
tech_stack: [Python, Django, Markdown, Mermaid]
domain: [Software Engineering, Documentation]
---

# Detailed Design Template

## Purpose

Specify how a part of the system works in enough detail to implement and test it: components, interfaces, data, flows, errors and security, derived from the HLD and the requirements.

## When to use

- Design below the HLD: an app, a feature, an integration, a security control or a workflow.
- Describing the as-built design of an existing component from the code.
- Not for model fields (use the model specification) or endpoint contracts (use the API specification); link to them.

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
| `{{design_mode}}` | `proposed` (design before code) or `as-built` (derived from existing code) | task |

## Sections

| Section | Required | Content | Verifiable by |
|---|---|---|---|
| Context | required | The HLD element this refines, requirements it serves, design mode ({{design_mode}}) | document ids |
| Components | required | Responsibilities, public interfaces and dependencies of each component | `file:line` for as-built |
| Interfaces and integrations | optional | Internal and external interfaces, protocols, timeouts, retries, idempotency, failure behaviour | client code or approved proposal |
| Data and state | optional | Data owned, state transitions, transactions; link to the database design | models, services |
| Flows | required | Sequence, activity, data-flow or workflow diagrams embedded from registered `.mmd` sources, each with a one-paragraph reading guide | diagram sources registered and linted |
| Security considerations | required | Authentication, authorisation, data protection and abuse cases for this design | security rules cited by id |
| Error handling and edge cases | required | What fails, how it is reported and recovered | code or proposal |
| Decisions | optional | Links to ADR/TDR ids; new hard-to-reverse decisions go to an ADR | ADR ids |
| Assumptions and open questions | required | Unknowns with who can confirm | — |

## Filling rules

- Apply the [filling conventions](README.md#filling-conventions).
- Register the document and keep it consistent with its registry entry: [registry protocol](../references/sdlc-documentation-registry.md).
- State only facts that are in a source document or in the code; otherwise write `Assumption A<n>:` with what would confirm it, or an open question. Never invent requirements, environments, metrics or decisions (`DOC-M1`, `DOC-M15`).
- Never include secret values, real hostnames or personal data (`DOC-M3`).
- Mark every statement `as-built` (cite `file:line`) or `proposed`; do not mix them without labels.
- Diagrams are Mermaid sources registered as their own documents and embedded unchanged ([Mermaid guide](../references/sdlc-mermaid-diagrams.md)).
- Link the database design, API specification and ADRs; do not repeat their content.
- Security design (type SEC) focuses on trust boundaries, authentication, authorisation, secrets and data protection and cites rule ids.

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

## Context
<HLD element, requirement ids, mode: {{design_mode}}>

## Components
| Component | Responsibility | Interface | Depends on |
|---|---|---|---|

## Interfaces and integrations
| Interface | Direction | Contract | Failure behaviour |
|---|---|---|---|

## Data and state
<Data ownership and state. See DBD/ERD ids.>

## Flows
<!-- mermaid-source: docs/diagrams/<file>.mmd -->
```mermaid
<diagram>
```

## Security considerations
<Controls and rule ids.>

## Error handling and edge cases
| Condition | Behaviour |
|---|---|

## Decisions
<ADR ids>

## Assumptions and open questions
- A1: <assumption>
````

## Completion checklist

- [ ] Every component and flow traces to the HLD and a requirement or to the code.
- [ ] Every embedded diagram is registered, validated and equals its source.
- [ ] Assumptions and open questions are listed; registry entry created or updated.
