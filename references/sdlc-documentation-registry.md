---
name: sdlc-documentation-registry
description: >-
  Shared reference for the SDLC documentation registry (docs/sdlc/registry.json): its fields, the
  four statuses, versioning, and the documentation-first protocol every agent follows - consume
  current documents, generate missing ones when the workflow needs them, review stale ones, protect
  approved ones, report conflicts, state assumptions - plus how to find and update entries and
  how the optional validator checks the result.
kind: shared-reference
agents: [django-project-analyzer, django-architecture-agent, django-model-agent, django-api-agent, django-security-agent, django-testing-agent, django-performance-agent, django-documentation-agent, django-code-review-agent]
project: django-agentic-engineering
abstract: >-
  File-based registry format and the documentation-first protocol shared by the Orchestrator and all
  specialists on Claude Code and GitHub Copilot, so documents are discovered without scanning the docs folder.
sdlc_phase: Architecture/Planning
tech_stack: [Python, Django, JSON, Markdown]
domain: [Software Engineering, Documentation]
---

# SDLC Documentation Registry

## Purpose

The registry is one small JSON file that lists the project's documents: what they are, where they
are, how current they are and what they depend on. Agents read it first, so they find the documents
they need without scanning the whole documentation folder, and they update it after they write. It
is the only index; there is no database and no service.

## Scope

The file format, the document lifecycle and the documentation-first protocol (`DOC-M9` to
`DOC-M16` in the [documentation standards](../rules/django-documentation-standards/SKILL.md)). Which
documents exist and who owns them is in the [framework](sdlc-documentation-framework.md); diagram
conventions are in the [Mermaid guide](sdlc-mermaid-diagrams.md).

## How to use

Before work: read the registry, select the entries relevant to your task, apply the protocol below. After
work: update the entries you changed. Without a registry: if the work needs documents, create one with
the minimal structure below (the documentation agent coordinates; any writing agent may create it
when it must register a document), and register the existing documents you find before adding new ones.
Read-only agents (analyzer, reviewer) never create or edit it; they report what they found.

## File and format

Fixed location `docs/sdlc/registry.json`; diagram sources live under `docs/diagrams/`. The plugin's guard lets
the documentation-only agent write documentation paths (`docs/**` and Markdown files), so these stay under
`docs/`. Markdown documents may live elsewhere if the project already keeps them there; set `docs_root` to the
folder the validator should scan for unregistered documents.

```json
{
  "schema_version": "1.0",
  "project": "shop",
  "profile": "standard",
  "docs_root": "docs",
  "facts": {"has_models": true, "has_api": true, "has_integrations": false, "has_deployment": true, "has_ci": true},
  "not_applicable": [{"type": "BRD", "reason": "Internal tool, no separate business case"}],
  "documents": [
    {
      "id": "DBD-001",
      "name": "Database design",
      "type": "DBD",
      "stage": "detailed-design",
      "path": "docs/design/database.md",
      "status": "draft",
      "version": "0.2",
      "related": ["ERD-001"],
      "depends_on": ["HLD-001"],
      "sources": ["shop/models.py"],
      "last_updated": "2026-11-13T09:30:00+00:00",
      "responsible_agent": "django-model-agent"
    }
  ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | `<TYPE>-<NNN>`, unique, never reused |
| `name`, `type`, `stage` | yes | Human name; catalog type; catalog stage (must match the type) |
| `path` | yes | File relative to the project root. Diagrams are `.mmd` files under `docs/diagrams/` |
| `status` | yes | `missing`, `draft`, `approved` or `stale` (below) |
| `version` | yes | `MAJOR.MINOR`: `0.x` while draft, `1.0` at first approval, minor for edits, major for an approved revision |
| `related` | no | Ids of documents to read alongside (diagram of a design, the ERD of a database design) |
| `depends_on` | no | Ids this document is derived from; if one changes, this one is reviewed |
| `sources` | no | Code or configuration files the document describes. Paths, or `{"path", "sha256"}` when the validator sealed them |
| `last_updated` | yes | ISO 8601 timestamp of the last content change |
| `responsible_agent` | yes | The owning agent from the catalog |
| `approved_by`, `approved_at`, `approved_hash` | approved only | Who approved, when; the hash seals the text (set by the validator) |
| `pending_revision` | no | Path of a proposed revision to an approved document |
| `notes` | no | Open questions, assumptions, known gaps (short) |

Top-level `profile` is `minimal`, `standard` or `enterprise`; `facts` are booleans from discovery; `not_applicable`
lists excluded types with a reason. The full type list, owners and templates are in the
[catalog](../config/sdlc-documentation-catalog.json).

Every Markdown document starts with a *document control* table (`id`, type, stage, status, version, owner,
sources) that repeats its registry entry and contains the document id. The registry is authoritative if they differ.

## Statuses

| Status | Meaning | Who sets it |
|---|---|---|
| `missing` | Planned or required, file does not exist | The agent that identifies the gap |
| `draft` | Exists, written by an agent or person, not approved | The writing agent |
| `approved` | A person approved this exact text | The agent, only when the user explicitly said so in their own words |
| `stale` | An input changed after the text was written (a source, a dependency, or a conflict was found) | Any agent that detects it |

An agent never approves a document on its own initiative and the orchestrator never approves on the
user's behalf. `status` and the file must agree: `missing` means no file, any other status means the file exists.

## The documentation-first protocol

Apply it in this order before engineering work and again after it.

1. **Find.** Read the registry. Select entries by stage, type, `sources` that match the files you will touch, and
   `related`/`depends_on`. Open only those documents. If there is no registry, list the existing documents
   (`docs/`, `README*`, ADRs) and register them as `draft` without rewriting them.
2. **Consume current documents.** A `draft` or `approved` document whose sources have not changed is input.
   Cite it by id and section instead of re-deriving what it says.
3. **Review stale documents.** Decide staleness as below, set `status: stale`, and review before relying on it. Use its
   still-correct parts, name the parts that are not, and do not build on a stale statement without verifying it
   against the code.
4. **Generate missing documents when the workflow needs them.** If your task needs a document of a type you own and it
   is applicable and `missing` (or unregistered), write it from the template, then register it. If you do not own the
   type, ask the orchestrator or the owner. Never generate a document merely because the catalog lists it.
5. **Protect approved documents.** Do not edit an `approved` document, even to fix a typo. Write the revision to
   `<name>.proposed.<ext>` beside it, record `pending_revision`, and tell the user what changed and why. The
   user's approval replaces the file, raises the major version and refreshes `approved_*`.
6. **Report conflicts.** When two documents disagree, or a document disagrees with the code, do not silently pick one.
   Record the conflict as below, continue with the code as evidence of *current behaviour* and the approved document as
   *intended behaviour*, and put the decision to the user.
7. **State assumptions or ask.** If a fact needed for your document is in no document and no code, write it as an
   assumption (`Assumption A1: ...`, with what would confirm it) or ask a clarification question. Never invent
   undocumented implementation details, requirements, environments, metrics or decisions.
8. **Update what you own.** After your work, update the documents of the types you own that the change affects,
   using the [impact map](sdlc-documentation-framework.md#change-impact-map); leave the others untouched. Set `last_updated`,
   bump `version`, refresh `sources`, set `status: draft`, and register new files. Recommend (do not make) edits to
   documents you do not own.

### Deciding that a document is stale

Stale when any of these is true; check cheapest first.

- A file in `sources` has a newer commit than `last_updated`: `git log -1 --format=%cI -- <path>` (agents with a
  shell) or the change list the orchestrator supplied. Without git, a newer modification time.
- A `depends_on` document has a higher version than the one this document was last aligned to, or is itself stale.
- The document states something the code contradicts (found while reading).
- The validator reports it (below).

A newer source commit is a *suspicion*: read the change, and if the document is still correct set it back to
`draft` with a refreshed `last_updated` and no other edits, saying so in `notes`.

### Reporting a conflict

```markdown
CONFLICT C1: <short title>
- Document: <id> section <x> says <quote or paraphrase>
- Other evidence: <id or file:line> says <...>
- Which is current behaviour: <code, file:line>   Which is intended: <document id, status>
- Proposed reconciliation: <update document | change code (owner agent) | ask user>
```

A conflict is reconciled by the owner of the document or code in question after the user decides; the documentation
agent keeps the list of open conflicts in the entry's `notes` and in the documentation report.

## Updating the registry

Use Read to load it and Edit to change only the entry you own; keep the JSON valid and the entries in id order.
Registering a document: choose the next free `<TYPE>-<NNN>`, set `stage` from the type, `responsible_agent` from
the catalog, `status` to `draft` (file written) or `missing` (planned), `version` `0.1`, `last_updated` now.
Only one agent writes the registry at a time; the orchestrator never runs two writing agents in parallel.
The documentation agent additionally reconciles it: every file under the documentation root is registered or
deliberately ignored, every entry's file exists, dependencies and related ids resolve, statuses are true.

## Validating

`tools/sdlc_registry.py` checks everything above mechanically: schema, `status` versus files, unknown types and
references, stale sources and dependencies, approved documents changed without re-approval, unregistered
documents, embedded diagrams against their sources, Mermaid structure, and which applicable documents are missing. The
plugin's guard keeps agents from running scripts stored outside the project, so a person or CI runs it:

```text
! python <plugin-root>/tools/sdlc_registry.py check
! python <plugin-root>/tools/sdlc_registry.py impact --git
```

`!` runs the command in the session so the output reaches the agents. `plan` lists the applicable documents that
are missing; `check --mark-stale` records detected staleness; `approve ID --by NAME` seals an approval with a
hash; `mermaid FILE` lints a diagram. A validator error is a defect in the documentation, never something to
silence by editing the registry.

## Related skills and rules

[django-documentation-standards](../rules/django-documentation-standards/SKILL.md) (`DOC-M9` to `DOC-M16`) ·
[django-security-standards](../rules/django-security-standards/SKILL.md) (no secrets in documents) ·
[django-architecture](../skills/django-architecture/SKILL.md) (decision records) ·
[SDLC documentation framework](sdlc-documentation-framework.md).
