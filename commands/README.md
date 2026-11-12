# commands/

Slash commands of the Django Engineering Plugin. A command is a thin entry point: it turns your
arguments into a brief for one agent, applies an approval gate where the agent can change code, and
relays the result. Commands are invoked as `/django-engineering:<command>`.

| Command | Agent | Changes the workspace | Gate |
|---|---|---|---|
| [/django-engineering:orchestrate](orchestrate.md) | `django-orchestrator`, then the specialists it selects | only through those specialists | each specialist's own gate |
| [/django-engineering:django-analyze](django-analyze.md) | `django-project-analyzer` | never | read-only |
| [/django-engineering:django-design](django-design.md) | `django-architecture-agent` | design docs with `--out`; scaffolding with `--scaffold` | approval before scaffolding |
| [/django-engineering:django-model](django-model.md) | `django-model-agent` | models, migrations, tests | proposal, then approval (or `--apply`) |
| [/django-engineering:django-api](django-api.md) | `django-api-agent` | API code and tests | proposal, then approval (or `--apply`); breaking changes always asked |
| [/django-engineering:django-security](django-security.md) | `django-security-agent` | only with `--fix` | review, then approval of the findings to fix |
| [/django-engineering:django-test](django-test.md) | `django-testing-agent` | test code only | plan, then approval (or `--apply`); none with `--run-only` |
| [/django-engineering:django-optimize](django-optimize.md) | `django-performance-agent` | targeted optimisations and tests | baseline, approval (or `--apply`), re-measure |
| [/django-engineering:django-document](django-document.md) | `django-documentation-agent` | documentation files only | none with `--dry-run` |
| [/django-engineering:django-review](django-review.md) | `django-code-review-agent` | never | read-only |

`/django-engineering:orchestrate` is the deterministic entry point to the orchestrator. If the
orchestrator cannot spawn subagents where it runs, it returns a ROUTING PLAN and the command has the
main session run that plan with the same limits (see [docs/architecture.md](../docs/architecture.md)).

Only these ten files are commands. Engineering standards (`rules/`) and skills (`skills/`) are never
commands: standards are marked `user-invocable: false` and are preloaded into the agents that need them.
