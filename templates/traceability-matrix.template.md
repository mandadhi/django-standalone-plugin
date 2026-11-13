---
name: traceability-matrix
description: >-
  Output template for the requirements traceability matrix: each requirement traced forward to
  design, code and tests and backward to its source, with coverage gaps.
kind: output-template
agents: [django-documentation-agent, django-testing-agent]
project: django-agentic-engineering
abstract: >-
  Standard structure for the matrix that links requirements to design elements, implementation and
  test cases and makes uncovered requirements visible.
sdlc_phase: Development
tech_stack: [Python, Django, Markdown, Mermaid]
domain: [Software Engineering, Documentation]
---

# Traceability Matrix Template

## Purpose

Show, for every requirement, where it is designed, implemented and tested, and show the gaps. The documentation agent creates the matrix from requirements and design; the testing agent fills the test columns.

## When to use

- Requirements exist and design, code or tests must be traced to them.
- After requirements, design or test cases change, to refresh affected rows only.
- Not as a substitute for requirements; link to them.

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

## Sections

| Section | Required | Content | Verifiable by |
|---|---|---|---|
| Traceability matrix | required | One row per requirement id with design reference, implementation (`file`), test case ids and status | ids resolve to registered documents and files |
| Coverage summary | required | Counts of requirements designed, implemented and tested; list of uncovered ones | counts match the matrix |
| Orphans | required | Design elements or tests that trace to no requirement | — |
| Open questions | required | Unclear or conflicting requirements | — |

## Filling rules

- Apply the [filling conventions](README.md#filling-conventions).
- Register the document and keep it consistent with its registry entry: [registry protocol](../references/sdlc-documentation-registry.md).
- State only facts that are in a source document or in the code; otherwise write `Assumption A<n>:` with what would confirm it, or an open question. Never invent requirements, environments, metrics or decisions (`DOC-M1`, `DOC-M15`).
- Never include secret values, real hostnames or personal data (`DOC-M3`).
- Rows reference requirement ids exactly as in the requirements document; implementation cells hold file paths, test cells hold test case ids or test names.
- A blank cell means *not covered*; never fill it with a guess. Status is one of `covered`, `partial`, `gap`.
- The testing agent writes only the test columns and the coverage summary; it never edits requirement text.

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

## Traceability matrix
| Requirement | Source | Design (doc id) | Implementation | Test cases | Status |
|---|---|---|---|---|---|

## Coverage summary
| Measure | Count |
|---|---|
| Requirements | |
| Without design | |
| Without implementation | |
| Without tests | |

## Orphans
<Items, or none.>

## Open questions
- <question>
````

## Completion checklist

- [ ] Every requirement appears once; every cell is a verified reference or blank.
- [ ] Gaps and orphans are listed, not hidden.
- [ ] Registry `depends_on` lists the requirements and test documents.
