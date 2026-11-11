# skills/

The twelve Django engineering skills (`<id>/SKILL.md` plus `<id>/references/*.md`). Claude Code
discovers them natively from `./skills/` (declared in `.claude-plugin/plugin.json`) and exposes them as
`django-engineering:<id>`. Each agent preloads the skills named in its frontmatter `skills:` line;
nothing is injected by any external service.

| Skill | Topic |
|---|---|
| `django-core` | Framework architecture, settings, request lifecycle, middleware, auth, caching, async |
| `django-orm` | QuerySets, models, migrations, transactions, query optimisation |
| `django-rest-framework` | Serializers, views, permissions, throttling, pagination, OpenAPI |
| `django-architecture` | App boundaries, layering, service layer, ADRs |
| `django-security-engineering` | Threat modelling, hardening, authz, CSRF/CORS/CSP, secrets |
| `django-testing` | Test strategy, Django and pytest-django, DRF tests, CI |
| `django-performance` | Profiling, ORM and cache performance, capacity |
| `django-integrations` | Outbound/inbound integrations, webhooks, brokers, resilience |
| `django-data-processing` | Imports, ETL, bulk data, file formats, reconciliation |
| `django-report-generation` | PDF/Excel/CSV reports, scheduled and background generation |
| `django-frontend` | Templates, HTMX, Alpine.js, React islands, accessibility |
| `postgresql-engineering` | Indexes, EXPLAIN, locking, connections, full-text search |

A skill teaches *how*; a [rule](../rules/README.md) states what every result *must* satisfy. Names must be
unique across skills, rules and agents (a duplicate would shadow another component), which is why the
`django-security-agent` agent and the `django-security-engineering` skill have different names.
`tests/test_plugin_structure.py` enforces this.
