---
applyTo: "**/*.py"
description: "Pointer to the Django Engineering Plugin's mandatory standards for Python changes in a Django project."
---
<!-- Hand-written Copilot adapter. Contains no engineering content: the standards live in rules/<id>/SKILL.md (canonical) and are exposed to Copilot as internal skills in .github/skills/<id>/. -->

When you change Python code in a Django or DRF project, apply the Django Engineering Plugin standards that match the change by loading the internal skill of the same name from `.github/skills/`:

- always: `django-security-standards`, `django-coding-standards`
- layout and settings: `django-project-structure`, `django-configuration-standards`
- data: `django-model-standards`, `django-database-standards`
- APIs: `django-api-standards`
- behaviour and quality: `django-testing-standards`, `django-performance-standards`, `django-logging-standards`
- docs and dependencies: `django-documentation-standards`, `django-dependency-standards`

Documentation first: before engineering work read `docs/sdlc/registry.json` and the documents it lists for the task, follow `django-documentation-standards` (`DOC-M9` to `DOC-M16`), never edit an approved document in place, and update the documents your change affects. The registry format, catalog and templates are the same as in Claude Code (`references/sdlc-documentation-registry.md`).

For multi-step or multi-specialist work use the `/orchestrate` skill; it follows `config/orchestration-policy.yaml`. Do not copy the standards into answers; apply them.
