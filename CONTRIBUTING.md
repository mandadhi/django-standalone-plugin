# Contributing

Start with [TEAM_HANDOFF.md](TEAM_HANDOFF.md): scope, architecture, the edit table and the explicit
exclusions.

## Workflow

1. Branch from the default branch. Keep one concern per branch.
2. `python -m pip install -r requirements-dev.txt`, then edit. Try changes with `claude --plugin-dir .`
   and `/reload-plugins`.
3. Run `python -m pytest` and `claude plugin validate .` before every push.
4. If you change a file recorded in `CANONICAL-MANIFEST.json`, update its `sha256` and add a changelog
   entry stating why it diverges from the main repository.
5. Open a pull request. Security-relevant changes (guard, `security-policy.json`, an agent's `tools`, a
   write mode, `SEC-*` rules) need a second reviewer and a regression test.

## Standards

- Agents keep their role, tools and write mode. Capability may be removed freely and added only with review.
- Component names are unique across agents, skills and rules.
- Markdown links are relative and resolve inside this repository; no symlinks; no absolute paths.
- No dependency on the Python harness, no network access, no secrets or personal data in any file.
- Commit messages: imperative, one line summary, body explaining why.
