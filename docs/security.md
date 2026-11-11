# Security

This is the security model of the **standalone** plugin. It is a separate implementation from the
integrated harness's security and is **not equivalent** to it.

## What is enforced

Enforcement is by `hooks/django_pack_guard.py` driven by `hooks/security-policy.json`, plus each agent's
frontmatter `tools` list. It applies to calls made by the plugin's ten agents.

| Control | Behaviour |
|---|---|
| Read-only agents | `django-project-analyzer`, `django-code-review-agent` and the orchestrator cannot write files; shell is limited to commands classified as reads (default deny, so unrecognised commands are refused); file redirections are refused |
| Documentation agent | Writes only to documentation paths inside the project (`docs/**`, `doc/**`, `*.md`, `*.rst`, `*.adoc`, `README*`, `CHANGELOG*`, `mkdocs.yml`); has no shell |
| Security-sensitive changes | `django-security-agent` asks for approval on **every** write and on every non-read shell command or tool |
| Undeclared tools | Denied, except Claude Code's own control-flow tools in `runtime_tools` (only `SubagentHandback`, which returns a subagent's report to its caller and reads, writes or runs nothing). The key is required: a policy without it fails closed |
| Destructive commands | Recursive/file deletion, git history rewrite, destructive database commands, privilege or system changes and network access ask for approval (`commands_require_approval`: `recursive-delete`, `git-history-rewrite`, `database-destructive`, `privilege-or-system`, `network-access`); inline code the guard cannot analyse asks too. Environment dumps, credential-store reads and pipe-download-to-shell are denied outright (`commands_deny`) |
| Network | `WebFetch` and `WebSearch` are denied for the plugin's agents; network-effect shell commands ask for approval |
| Secrets | `.env`, `.env.*`, `*.pem`, `*.key`, `secrets/**` are denied paths; environment listing and credential-variable expansion are denied; secret patterns in tool output are masked (PostToolUse) |
| Path restrictions | Reads allowed inside the project and the plugin; writes only inside the project; shell operands, redirections, globs, brace expansions and nested commands naming paths outside the project are denied |
| Fail closed | A missing or unreadable policy, a missing `shell_syntax.py`, malformed input, an internal error, a timeout or a missing `python` blocks the call (`exit 2` and `onFailure: "block"`) |
| Orchestrator | Cannot delegate to itself or to anything but the nine specialists; its own tools are read-only plus `Agent` |
| Specialists | Have no `Agent` tool, and the guard denies any `Agent`/`Task` call by a non-orchestrator |
| No widening | The hook never answers `allow` except for reading the plugin's own `templates/`, `references/`, `skills/`, `rules/`; so it only narrows Claude Code's permissions |

The protected-path list also denies `**/.django-engineering` and `**/.django-engineering/**`. The
standalone plugin never uses that directory; the entry is a deny-only safeguard so a standalone session
cannot alter a harness installation that may coexist in the same repository.

## Limitations of standalone mode

- **Not a sandbox.** Shell commands are statically analysed. A script an agent writes and then runs, or a
  plain `$var` operand, is not bounded. For an OS boundary enable Claude Code's sandbox (`/sandbox`).
- **Scope.** The guard acts only on the plugin's ten agents. Your main session and other plugins remain
  under Claude Code's own permissions.
- **Needs `python`.** Without a `python` (3.8+) on `PATH`, every tool call is blocked while the plugin is
  enabled (fail closed). The interpreter cannot be configured in the plugin.
- **Approval is Claude Code's permission prompt.** There is no approver service, no binding of an approval
  to an exact call, and no audit log. In `-p` mode approval prompts cannot be answered and are refused.
- **No persistence.** No execution records, checkpoints or resume.
- **Masking.** Secret masking applies to tool output of the plugin's agents, not to failed commands, and
  there are no redacted logs or artifacts (there are none).
- **Orchestration limits.** The delegation count and retry limits are instructions to the orchestrator, not
  enforced by code. Only the target allowlist is enforced.
- **Windows.** Claude Code has no OS sandbox on Windows; Bash needs Git Bash.
- **Unverified in this distribution.** Behaviour of the guard under macOS/Linux sandbox settings has been
  tested offline only.

## Reporting a vulnerability

See [SECURITY.md](../SECURITY.md).
