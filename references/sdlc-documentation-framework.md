---
name: sdlc-documentation-framework
description: >-
  Shared reference for SDLC-wide documentation: the seven stages, the document types of each
  stage with owner agent and template, how applicability is decided (profile, facts, on-demand),
  what each stage consumes and produces, and which change updates which documents.
kind: shared-reference
agents: [django-project-analyzer, django-architecture-agent, django-model-agent, django-api-agent, django-security-agent, django-testing-agent, django-performance-agent, django-documentation-agent, django-code-review-agent]
project: django-agentic-engineering
abstract: >-
  Lookup tables from SDLC stage to document types, owners and templates, applicability rules and
  the change-to-document impact map, so every agent on either platform treats documentation the same way.
sdlc_phase: Architecture/Planning
tech_stack: [Python, Django, Django REST Framework, Markdown, Mermaid]
domain: [Software Engineering, Documentation]
---

# SDLC Documentation Framework

## Purpose

Documentation is shared project context, not a by-product. Every agent reads the documents that
exist before it works, and updates the documents it owns after it works. This reference says
which documents exist at each SDLC stage, who owns them, which template shapes them and when a
project needs them. The machine-readable form is
[`config/sdlc-documentation-catalog.json`](../config/sdlc-documentation-catalog.json); this page is its
human summary and the two must agree (`tests/test_sdlc_documentation.py` checks it).

## Scope

The seven stages, 50 document types (41 documents and 9 diagram types), applicability, stage
hand-offs and change impact. How a document is registered, versioned, approved or found stale is in
the [registry protocol](sdlc-documentation-registry.md); how diagrams are written is in the
[Mermaid guide](sdlc-mermaid-diagrams.md).

## How to use

1. Identify the stage of the current work (tables below) and look up the document types it
   consumes and produces.
2. Read the registry (`docs/sdlc/registry.json`) first; open only the documents the work needs.
3. Produce only documents that are applicable (see Applicability) and that your agent owns.
4. After the work, use the impact map to update only the documents the change affects.

## Stages, documents, owners and templates

Owner is the agent that writes and keeps the document current. Any agent may *propose* a change to a
document it does not own by handing the owner a recommendation; it never edits the owner's approved text.

### 1. Requirements and Analysis

| Type | Document | Owner | Template |
|---|---|---|---|
| BRD, SRS, FRD, NFR | Business, software and functional requirements, non-functional requirements | documentation | [requirements-specification](../templates/requirements-specification.template.md) |
| US, AC | User stories, acceptance criteria | documentation | requirements-specification |
| RTM | Requirements traceability matrix (testing adds the test columns) | documentation | [traceability-matrix](../templates/traceability-matrix.template.md) |

Requirements come from the user, stakeholders or existing documents, never from the code alone. The
code can only show what the system does today; present that as *current behaviour*, not as a requirement.

### 2. Architecture and High-Level Design

| Type | Document | Owner | Template |
|---|---|---|---|
| HLD, SAD, SOL | High-level, system and solution architecture | architecture | [architecture-design](../templates/architecture-design.template.md) |
| ADR, TDR | Architecture and technology decision records | architecture | [architecture-decision-record](../templates/architecture-decision-record.template.md) |
| CTX, C4, CMP | System context, C4 and component diagrams | architecture | architecture-design (diagram sources, see the Mermaid guide) |

### 3. Detailed Design

| Type | Document | Owner | Template |
|---|---|---|---|
| LLD, CD, INT | Low-level, component and integration design | architecture | [detailed-design](../templates/detailed-design.template.md) |
| DBD, ERD | Database design and entity-relationship diagram | model | [django-model-specification](../templates/django-model-specification.template.md) |
| API | API specification | api | [api-specification](../templates/api-specification.template.md) |
| SEC | Security design | security | detailed-design |
| SEQ, ACT, DFD, WFL | Sequence, activity, data-flow and workflow diagrams | architecture | detailed-design (diagram sources) |

### 4. Development

| Type | Document | Owner | Template |
|---|---|---|---|
| IMP | Implementation notes (api, testing and performance contribute their own changes) | model | [implementation-notes](../templates/implementation-notes.template.md) |
| MOD, CFG, CODE | Module documentation, configuration reference, code documentation | documentation | [technical-documentation](../templates/technical-documentation.template.md) |
| MIG | Migration documentation | model | [migration-plan](../templates/migration-plan.template.md) |

### 5. Testing and Quality Assurance

| Type | Document | Owner | Template |
|---|---|---|---|
| TST, TPL, TC | Test strategy, test plan, test cases | testing | [test-plan](../templates/test-plan.template.md) |
| TER, DEF | Test execution report, defect report | testing | [test-report](../templates/test-report.template.md) |
| PERF | Performance assessment | performance | [performance-assessment](../templates/performance-assessment.template.md) |

### 6. Deployment and Release

| Type | Document | Owner | Template |
|---|---|---|---|
| DEP, INF, CICD, ENV, REL, RBK, DPL | Deployment architecture, infrastructure, CI/CD, environment configuration, release plan, rollback plan, deployment diagram | documentation | [deployment-and-release](../templates/deployment-and-release.template.md) |
| RUN | Operational runbooks | documentation | [operational-runbook](../templates/operational-runbook.template.md) |

Deployment documents describe the actual implementation: the Dockerfile, compose files, pipeline
definitions, settings and infrastructure code in the repository. Where none exists, the document records the
gap and asks the user; it does not invent an environment.

### 7. Maintenance and Evolution

| Type | Document | Owner | Template |
|---|---|---|---|
| CHG, INC, RCA, TDEBT | Changelog, incident report, root cause analysis, technical debt register | documentation | [maintenance-record](../templates/maintenance-record.template.md) |
| ARU | Architecture updates | architecture | maintenance-record |

## Applicability

A project does not need every document. Applicability comes from the registry's `profile`, `facts`
and `not_applicable` list, and is recorded there with a reason.

| Rule | Meaning |
|---|---|
| Profile `minimal` | Small or single-developer project: user stories, acceptance criteria, configuration reference, changelog, ADRs when a decision is made |
| Profile `standard` | Team project in production or heading there: adds SRS, NFR, HLD, LLD, database, API, test, deployment and runbook documents |
| Profile `enterprise` | Regulated or multi-team systems: adds BRD, FRD, system and solution architecture, activity, data-flow and workflow diagrams, component design, infrastructure, code documentation |
| Facts | A type with `requires_fact` applies only when the fact is true: `has_models`, `has_api`, `has_integrations`, `has_deployment`, `has_ci` |
| On demand | ADR, TDR, IMP, MIG, TER, DEF, PERF, REL, RBK, INC, RCA and ARU exist only when the event happened (a decision was made, tests were run, an incident occurred) |
| Not applicable | A type excluded on purpose, with a recorded reason; never reported as missing |

Choose the profile from the project's size and the user's wording; ask one question when unclear. Never
generate a document only because it is in the catalog.

## Stage hand-offs: consume, then produce

| Stage | Consumes | Produces | Leading agent |
|---|---|---|---|
| Requirements | User input, existing requirements, current-behaviour profile | BRD/SRS/FRD/NFR, US, AC, RTM rows | documentation |
| Architecture | Requirements, project profile | HLD, context/C4/component diagrams, ADR/TDR | architecture |
| Detailed design | HLD, requirements | LLD, DBD/ERD, API, SEC, SEQ/DFD, INT | architecture, model, api, security |
| Development | Approved design documents | IMP, CFG, MIG, MOD; DBD/API updated where the implementation legitimately differs | model, api, performance |
| Testing | Requirements, acceptance criteria, design | TST/TPL/TC, TER, DEF, RTM test columns | testing |
| Deployment | Actual implementation, settings, pipeline files | DEP, INF, CICD, ENV, REL, RBK, RUN | documentation |
| Maintenance | Registry, change set, incident facts | CHG, INC, RCA, TDEBT, ARU, impact assessment | documentation, architecture; code-review finds issues |

When approved design and the code disagree, the agent reports the conflict; it changes neither side
silently (see the protocol in the registry reference).

## Change impact map

Classify the change, update only the listed documents, leave the rest alone. The catalog's
`change_categories` hold the exact path patterns.

| Change | Documents to review |
|---|---|
| Requirements | BRD, SRS, FRD, NFR, US, AC, RTM, then dependents (HLD, TC) |
| Architecture (new app, boundary, entry point) | HLD, SAD, SOL, C4, CTX, CMP, ADR/TDR, ARU |
| Models, migrations | DBD, ERD, LLD, MIG |
| API (serializers, views, URLs, permissions) | API, LLD, INT, SEQ |
| Settings, environment | CFG, DEP, ENV |
| Dependencies | CFG, DEP, ENV, TDEBT |
| Tests | TPL, TC, TER |
| Container, pipeline, infrastructure | DEP, INF, CICD, DPL, ENV, REL, RBK, RUN |
| Authentication, middleware, security configuration | SEC |
| Tasks, signals, management commands | MOD, LLD, RUN, DFD |
| Other application code | MOD, CODE |

Documents that depend on an updated one (the registry's `depends_on`) are reviewed next. An approved
document is never edited in place; it gets a proposed revision.

## Related skills and rules

[django-architecture](../skills/django-architecture/SKILL.md) (decision records, architecture views) ·
[django-core](../skills/django-core/SKILL.md) (settings and project structure facts) ·
[django-documentation-standards](../rules/django-documentation-standards/SKILL.md) (`DOC-M1` to `DOC-M16`) ·
[django-project-discovery](django-project-discovery.md) (finding the facts).
