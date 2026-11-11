# rules/

The twelve mandatory engineering rules, one `<id>/SKILL.md` each, declared as a second skill folder
(`./rules/`) in `.claude-plugin/plugin.json`. Claude Code loads them natively as
`django-engineering:<id>` with `user-invocable: false`: rules are never slash commands. Agents preload the
rules listed in their frontmatter `skills:` line, treat every MUST as binding, and must meet each
applicable MUST, or report it by id, before they finish.

| Rule | Governs |
|---|---|
| `django-security-standards` | Security conduct of every agent (SEC-A*) and Django security requirements (SEC-M*) |
| `django-coding-standards` | Application code |
| `django-configuration-standards` | Settings and configuration |
| `django-database-standards` | Migrations, transactions, raw SQL |
| `django-model-standards` | Model definitions |
| `django-api-standards` | DRF endpoints |
| `django-dependency-standards` | Dependencies |
| `django-documentation-standards` | Documentation |
| `django-logging-standards` | Logging and error reporting |
| `django-performance-standards` | Performance |
| `django-project-structure` | Project and app layout |
| `django-testing-standards` | Tests |

Rules carry numbered requirements (for example `SEC-M4`) that agents cite in findings. Rules grant no
capabilities (`SEC-A4`): they never widen an agent's tools, paths or write mode.
