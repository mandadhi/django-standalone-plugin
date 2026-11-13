---
project: django-agentic-engineering
abstract: >-
  The Django Engineering Plugin's output templates that standardise agent reports.
sdlc_phase: Architecture/Planning
tech_stack: [Python, Django, Markdown]
domain: [Software Engineering, AI Agents]
---

# templates/

This folder holds the plugin's output templates, one `<id>.template.md` per report kind.

## Django output templates

An output template fixes the structure of one kind of report, so that every agent
producing it returns the same sections in the same order. Templates hold structure only. Django
knowledge stays in the [skills](../skills/README.md), mandatory requirements in the
[rules](../rules/README.md), and reusable checklists in the [shared references](../references/README.md).

| Template | Purpose | Agent |
|---|---|---|
| [project-analysis](project-analysis.template.md) | Evidence-backed profile of an existing project | django-project-analyzer |
| [architecture-design](architecture-design.template.md) | App boundaries, layering, boundaries, plan | django-architecture-agent |
| [architecture-decision-record](architecture-decision-record.template.md) | One hard-to-reverse decision with options | django-architecture-agent |
| [django-model-specification](django-model-specification.template.md) | Model, constraint, index and migration proposal or report | django-model-agent |
| [api-specification](api-specification.template.md) | DRF endpoint contract, access matrix, compatibility | django-api-agent |
| [security-assessment](security-assessment.template.md) | Security findings, configuration checks, fixes | django-security-agent |
| [test-plan](test-plan.template.md) | Test plan, run results, classified failures | django-testing-agent |
| [performance-assessment](performance-assessment.template.md) | Measured findings, before/after changes | django-performance-agent |
| [technical-documentation](technical-documentation.template.md) | Code-derived documents and the documentation report | django-documentation-agent |
| [code-review-report](code-review-report.template.md) | Merge verdict and severity-ranked findings | django-code-review-agent |
| [implementation-plan](implementation-plan.template.md) | Dependency-ordered work items with owners | django-architecture-agent |
| [migration-plan](migration-plan.template.md) | Phased, verifiable, reversible risky migration | django-model-agent |
| [requirements-specification](requirements-specification.template.md) | BRD, SRS, FRD, NFR, user stories, acceptance criteria | django-documentation-agent |
| [traceability-matrix](traceability-matrix.template.md) | Requirement to design, code and test trace, with gaps | django-documentation-agent, django-testing-agent |
| [detailed-design](detailed-design.template.md) | LLD, component, integration and security design with diagrams | django-architecture-agent, django-security-agent |
| [implementation-notes](implementation-notes.template.md) | What was built, deviations from design, documentation impact | model, api, testing, performance agents |
| [test-report](test-report.template.md) | Test execution report and defect report | django-testing-agent |
| [deployment-and-release](deployment-and-release.template.md) | Deployment, infrastructure, CI/CD, environments, release and rollback | django-documentation-agent |
| [operational-runbook](operational-runbook.template.md) | Operator procedure with verification and rollback | django-documentation-agent |
| [maintenance-record](maintenance-record.template.md) | Changelog, incident, RCA, debt register, architecture update | django-documentation-agent, django-architecture-agent |

### Format

- **Frontmatter:** `name` (= file name without `.template.md`), `description`,
  `kind: output-template`, `agents` (the producers), and the inventory fields
  used across this plugin (`project`, `abstract`, `sdlc_phase`, `tech_stack`, `domain`).
- **Body sections, in this order:** Purpose, When to use, Placeholders, Sections, Filling rules,
  Output structure, Completion checklist.
- **Output structure** is one fenced Markdown skeleton. It starts with an H1 title and the
  standard header table (Project, Scope, Prepared by, Date, Status, Sources).
- **Sections** lists every `##` heading of the skeleton, in order, as `required` or `optional`,
  with what goes in it and how it can be verified.
- **Placeholders** are `{{snake_case}}`. Each one used in the skeleton is declared in the
  Placeholders table with its meaning and source, and each declared one is used. Every template
  uses the six header placeholders `{{subject}}`, `{{project_name}}`, `{{scope}}`,
  `{{prepared_by}}`, `{{date}}` and `{{document_status}}`, plus `{{sources}}`.

### Relation to the agents' Output sections

Each agent's own Output section keeps its short inline skeleton. That skeleton is the minimum the
agent can always produce, including when a template cannot be read. The agents read templates
at `${CLAUDE_PLUGIN_ROOT}/templates/<id>.template.md`. The template is the full standard: its `##`
headings include every heading of the agent's inline skeleton, and it adds optional sections,
placeholders and verification guidance. `tests/test_templates_and_references.py` enforces that the two
stay consistent. The machine-readable JSON blocks some agents append are defined only in those
agents; templates refer to them and do not repeat them.

## Filling conventions

These apply to every output template.

- **Evidence, not assumption.** Each fact cites its source: `path/file.py:42`, a command and its
  result, or a named input. Never invent versions, counts, sizes, timings, dates or names.
- **Markers for what is not known.** Use `unknown` (could not be established, say why),
  `inferred` (derived from indirect evidence, say from what), `not-run` (a check that did not run,
  with the reason; never reported as passed), `estimated` (not measured), `unverified` (a
  statement that could not be traced to code) and `n/a` (does not apply, with the reason).
- **Required sections are never dropped.** If a required section has no content, write `None`
  or a marker with the reason. Optional sections are omitted when they do not apply.
- **Placeholders are replaced or removed.** A finished report contains no `{{...}}` text. Table
  header rows stay; empty tables are replaced by `None`.
- **No secrets.** Settings, variables and credentials appear by name and location only. Example
  values are obviously fake (`<your-api-token>`).
- **Rule ids.** Cite the requirement id (for example `SEC-M4`) for any finding or decision that a
  rule governs. Ids are defined in [`rules/`](../rules/README.md).
- **Severity scale.** `critical`, `high`, `medium`, `low`, `info`; code reviews add `nit`.

## Adding a template

1. Create `templates/<id>.template.md` with the frontmatter and sections above.
2. Name its producers in `agents`, and add the id to the `Templates` line of each
   of those agents' `## Templates and references` section.
3. Add it to the table above and to `EXPECTED_TEMPLATES` in `tests/test_templates_and_references.py`,
   then run the tests.
