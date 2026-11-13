---
name: test-report
description: >-
  Output template for test execution reports and defect reports: what was run, the results,
  failures classified with evidence, defects with reproduction steps, and requirement coverage.
kind: output-template
agents: [django-testing-agent]
project: django-agentic-engineering
abstract: >-
  Standard structure for recording an actual test run or a defect, with real commands and results
  and no invented outcomes.
sdlc_phase: Development
tech_stack: [Python, Django, Markdown, Mermaid]
domain: [Software Engineering, Documentation]
---

# Test Report Template

## Purpose

Record the outcome of a test run (TER) or one defect (DEF) so that releases and maintenance can rely on it. Results come only from runs that happened.

## When to use

- Tests were run and the result must be kept (execution report).
- A defect was found (defect report).
- Not for planning tests; use the [test plan](test-plan.template.md).

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
| `{{report_kind}}` | `execution` or `defect` | task |

## Sections

| Section | Required | Content | Verifiable by |
|---|---|---|---|
| Run | required | Kind {{report_kind}}, commands run, environment (interpreter, database, settings), commit or state tested | command output |
| Results | required | Passed, failed, skipped, duration per command; `not-run` where not run | command output |
| Requirement coverage | optional | Requirements or acceptance criteria exercised, by id | traceability matrix |
| Failures | optional | Each failure classified (test, code, environment) with evidence and owner | output excerpts |
| Defects | optional | Defect id, severity, steps to reproduce, expected and actual result, affected requirement, suspected cause (labelled as suspicion) | reproduction |
| Follow-ups | required | Fixes, flaky tests, coverage gaps, documents to update | — |

## Filling rules

- Apply the [filling conventions](README.md#filling-conventions).
- Register the document and keep it consistent with its registry entry: [registry protocol](../references/sdlc-documentation-registry.md).
- State only facts that are in a source document or in the code; otherwise write `Assumption A<n>:` with what would confirm it, or an open question. Never invent requirements, environments, metrics or decisions (`DOC-M1`, `DOC-M15`).
- Never include secret values, real hostnames or personal data (`DOC-M3`).
- Report exactly what ran; a test not run is `not-run`, never passed. No pass claim without output.
- A defect report states reproduction steps that were actually followed; a suspected cause is labelled `suspected`.
- Use synthetic data in all examples.

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

## Run
<Kind: {{report_kind}}. Commands, environment, state tested.>

## Results
| Command | Passed | Failed | Skipped | Duration |
|---|---|---|---|---|

## Requirement coverage
| Requirement | Test cases | Result |
|---|---|---|

## Failures
| Test | Class | Evidence | Owner |
|---|---|---|---|

## Defects
| Id | Severity | Steps | Expected | Actual | Requirement |
|---|---|---|---|---|---|

## Follow-ups
- <follow-up and owner>
````

## Completion checklist

- [ ] Every result has its command; every failure has a class and an owner.
- [ ] Defects have reproduction steps and a severity.
- [ ] Registry entry created or updated (TER or DEF).
