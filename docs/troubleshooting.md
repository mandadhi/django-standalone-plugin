# Troubleshooting

| Problem | Fix |
|---|---|
| `marketplace add` fails | Use the `owner/repo` form (or a full `https://` git URL). The repository must be reachable with your git credentials and `.claude-plugin/marketplace.json` must be on its default branch. Check locally: `claude plugin validate .claude-plugin/marketplace.json` |
| `plugin install` cannot find the plugin | The suffix is the **marketplace** name, not the repository: `django-engineering@django-engineering-standalone`. `claude plugin marketplace list` shows configured names; `claude plugin marketplace update django-engineering-standalone` refreshes |
| Plugin does not appear in `/agents` | Start a new session or run `/reload-plugins`; check `claude plugin list` shows it enabled. Agents appear as `django-engineering:<id>` |
| `claude plugin details` shows **Agents (0)** | Expected for agents listed file by file in `plugin.json`. Check `/agents` instead |
| Every tool call is blocked / "hook interpreter missing" | The guard could not start. Put a command named `python` (3.8+) on `PATH`. On systems with only `python3`, provide `python` (for example `python-is-python3`, a virtualenv or a symlink) |
| Everything is blocked after a plugin file edit | The guard failed closed: the policy or analyser is unreadable. Run `python -m pytest` in the plugin root and fix what `tests/test_security_policy.py` reports |
| Names collide / commands or agents appear twice | The integrated distribution (same plugin name `django-engineering`) is also enabled. Disable or uninstall one of them |
| Bash unavailable to agents on Windows | Install Git for Windows, or set `CLAUDE_CODE_GIT_BASH_PATH` to `...\Git\bin\bash.exe` |
| `/orchestrate` returns a ROUTING PLAN | The orchestrator could not spawn subagents where it ran. The command runs the plan from the main session; or start with `claude --agent django-engineering:django-orchestrator` |
| A write was refused or asked | Expected: read-only agents cannot write; the security agent asks every time; the documentation agent writes documentation only. See [security.md](security.md) |
| Approval prompts are refused | You are in non-interactive `-p` mode; run interactively |
| Plugin changes are not picked up | `/reload-plugins` or restart; for an installed plugin bump `version` in `plugin.json` and run `plugin update` |
