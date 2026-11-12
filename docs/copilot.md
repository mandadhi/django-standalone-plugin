# GitHub Copilot adapter

One plugin, one repository, two native adapters. The engineering content (agents, skills, rules, templates,
references, `config/orchestration-policy.yaml`) is canonical and shared. Claude Code reads it directly through
`.claude-plugin/`; GitHub Copilot reads thin files derived from it under `.github/`.

```text
canonical:   agents/  commands/  skills/  rules/  templates/  references/  config/orchestration-policy.yaml
Claude Code: .claude-plugin/plugin.json  hooks/hooks.json  (reads the canonical folders as they are)
Copilot:     .github/agents/*.agent.md   .github/skills/*/SKILL.md   .github/instructions/*.instructions.md
tooling:     tools/sync_copilot_adapter.py (render + --check + --matrix)   tests/test_copilot_adapter.py
```

## What Copilot gets

| Component | Copilot file | Visible to the user | Available to agents |
|---|---|---|---|
| 10 slash commands | `.github/skills/<command>/SKILL.md` (`user-invocable: true`) | yes, as `/orchestrate`, `/django-analyze`, ... | yes |
| Orchestrator | `.github/agents/django-orchestrator.agent.md` (`user-invocable: true`, `agents:` = the nine specialists) | yes, in the agent picker | n/a |
| 9 specialists | `.github/agents/<id>.agent.md` (`user-invocable: false`, `disable-model-invocation: false`) | hidden from the picker | yes, as subagents |
| 12 knowledge skills | `.github/skills/<skill>/SKILL.md` (`user-invocable: false`) | hidden from `/` | yes, auto-loaded by description |
| 12 standards | `.github/skills/<rule>/SKILL.md` (`user-invocable: false`) | hidden from `/` | yes |
| Standards pointer | `.github/instructions/django-engineering.instructions.md` (`applyTo: **/*.py`) | n/a | applied to Python files |

The knowledge skill for security is `django-security-engineering` (the name `django-security` is the command).

How each generated file differs from its source (all of it is done by `tools/sync_copilot_adapter.py`):

- **Frontmatter:** only the fields Copilot documents (`name`, `description`, `argument-hint`, `tools`, `agents`,
  `user-invocable`, `disable-model-invocation`). Claude-only fields (`skills:`, `model`, `maxTurns`, pack metadata)
  are not carried over. Claude tool names map to Copilot aliases: Read→`read`, Grep/Glob→`search`,
  Write/Edit→`edit`, Bash→`execute`, Agent→`agent`.
- **Body:** the canonical body, with `${CLAUDE_PLUGIN_ROOT}` → `<plugin-root>`, `$ARGUMENTS` → "the text typed after
  the slash command", and the `django-engineering:` namespace removed. Skill links to `references/` are re-based to
  the canonical `skills/<id>/references/`, so references are not duplicated.
- **Skill preloading:** Claude Code preloads an agent's `skills:`. Copilot has no such field, so each generated agent
  ends with a list of the same skills and rules and is told to load them by name.
- **Routing:** the orchestrator carries the same generated policy section as the Claude one and is told to read
  `config/orchestration-policy.yaml`. There is no Copilot-specific policy.

Every generated file starts with a `GENERATED ... from <source> (sha256 ...)` marker. Do not edit them: edit the
canonical source and run `python tools/sync_copilot_adapter.py`. `--check` (and the test suite) fails on missing,
stale or orphaned files.

## Installation

Requirements: VS Code with GitHub Copilot Chat (agent mode, Agent Skills and custom agents), or another Copilot
client that reads `.github/agents` and `.github/skills`; Python 3.10+ only if you run the sync tool or the tests.

1. Copy this repository's contents into the root of the Django project (or open this repository itself):
   `.github/`, `agents/`, `commands/`, `skills/`, `rules/`, `templates/`, `references/` and `config/`. The `.github/`
   files point at those folders by relative path (`../../../skills/<id>/references/...`, `<plugin-root>/templates/...`),
   so they must sit next to `.github/`. If the project already has `.github/agents` or `.github/skills`, merge; names
   here do not clash with the usual ones.
2. Reload the window. Type `/` in Copilot Chat: the ten commands appear. Pick **django-orchestrator** in the agent
   picker for free-form requests.
3. Optional: a personal install can put the `.github/skills` and `.github/agents` contents under `~/.copilot/`.
   Then also keep the canonical folders reachable, or the relative references will not resolve.

Not done on purpose: no `.prompt.md` files, no use of the deprecated Local harness handoffs, no MCP server, no
second plugin manifest. VS Code can also read this repository as a Claude-format plugin
(`.claude-plugin/plugin.json`), but that path is not the tested Copilot route and is not documented as supported here.

## Using it

`/django-security src/billing --fix` runs the same workflow as `/django-engineering:django-security` in Claude Code:
the command skill briefs the `django-security-agent` custom agent, which applies `django-security-engineering` and the
standards. `/orchestrate add an invoices API with its model and tests` makes the orchestrator classify the request with
the shared policy and delegate to specialists in order.

## Security model on Copilot, honestly

| Control | Claude Code | Copilot | Kind |
|---|---|---|---|
| Per-agent tool ceiling | `tools:` in agent file | `tools:` in `.agent.md` (mapped aliases) | platform-enforced by the client (not live-tested) |
| Only the orchestrator can start agents | no `Agent` tool on specialists | no `agent` tool on specialists | platform-enforced by the client (not live-tested) |
| Delegation allowlist, no self-delegation | guard hook + policy | `agents:` list = policy `specialists`, orchestrator not in it | client-enforced list; the guard hook has no Copilot port |
| Protected paths, secret files, command deny and approval rules | `hooks/django_pack_guard.py` + `hooks/security-policy.json`, fail-closed | **not enforced**: the same rules are only written in the agent/rule text | instruction-based |
| Write approval gates (propose, wait, apply) | agent text | same text | instruction-based |
| Workspace boundary | guard hook | client workspace trust and permission prompts | client behaviour; no OS sandbox from this plugin |
| OS-level isolation | none from this plugin | none from this plugin | not provided |

The Claude guard is a hook that reads Claude Code's tool-call JSON. Copilot's hook formats and tool names differ and
no port was written or tested, so the guard's deny rules do **not** protect Copilot sessions. Prompt instructions are
not a sandbox: on Copilot, rely on the client's tool permission prompts and workspace trust for the hard boundary.

## Known limitations

- Slash-command discovery and invocation, subagent delegation, hidden-agent behaviour and `agents:` enforcement on
  Copilot are **not live-tested** in this repository (no Copilot client was available to the author of this change).
  They follow the documented formats; see [testing.md](testing.md).
- `agents:` is documented for the Local harness sessions, which the VS Code docs mark as deprecated (removal
  announced for February 2027). Other Copilot clients may ignore it; then any custom agent can be delegated to.
- Subagents cannot start subagents by default in VS Code; the orchestrator is one level above the specialists, which
  is the supported shape. If a client forbids even that, the orchestrator's ROUTING PLAN fallback applies.
- Claude Code has no per-agent "hidden" flag, so the nine specialists remain visible in `/agents` and `@` mentions
  there; only commands and knowledge skills are hidden from `/`.
