# Team handoff: Django Engineering Plugin (standalone)

Read this first. It is written so a new team can start without asking the original team anything.

## 1. Product scope

**What it is.** A Claude Code plugin that gives a developer a Django/DRF engineering team inside Claude
Code: one orchestrator (slash command `/django-engineering:orchestrate`), nine specialist agents, eleven internal skills, twelve internal rules, twelve
output templates, seven shared references and a security guard hook.

**What it does.** Analyse a project; design architecture; create or change models and migrations; build
DRF APIs; assess and harden security; write and run tests; find and fix performance problems; write
documentation from code; review changes before merge; or let the orchestrator choose and sequence the
specialists for a request.

**What it does not do.**

- No workflow engine, execution database, run records, checkpoints/resume, approver service or audit log.
- No sandboxing: the guard is a policy layer (see [docs/security.md](docs/security.md)).
- No code that runs outside Claude Code except the guard hook (`python`, standard library only).
- No harness management commands (`setup-harness`, `harness-status`, `enable-harness`,
  `disable-harness`, `doctor`).

**Identity.** Plugin `django-engineering` (agents are `django-engineering:<agent id>`), marketplace
`django-engineering-standalone`, version in `.claude-plugin/plugin.json`. The plugin name is shared with the
integrated distribution on purpose (see [docs/installation.md](docs/installation.md#identity)); never enable
both in one scope.

## 2. Architecture

See [docs/architecture.md](docs/architecture.md). In short: the user runs `/django-engineering:orchestrate <request>` (or names an agent); the
orchestrator classifies the request, selects the smallest route from
[`config/orchestration-policy.yaml`](config/orchestration-policy.yaml), briefs each specialist, runs the
steps in order, applies the failure policy, reconciles against the original request and reports. Every
tool call of every plugin agent passes through `hooks/django_pack_guard.py`.

Repository layout:

```text
.claude-plugin/    plugin.json (component list, version), marketplace.json
agents/            orchestrator + 9 specialists
skills/  rules/    11 + 12 internal SKILL.md bundles (user-invocable: false) + skills/orchestrate entry skill
templates/         12 report templates      references/  7 shared references
hooks/             hooks.json, guard, shell analyser, security-policy.json
config/            orchestration-policy.yaml
docs/ tests/       documentation and the validation suite
CANONICAL-MANIFEST.json   source-to-distribution mapping with SHA-256 hashes
```

## 3. Agent responsibilities

| Agent | Responsible for | Must not |
|---|---|---|
| `django-orchestrator` | Classify, select, brief, sequence, reconcile, report | Do specialist work, write files, delegate to itself or outside the nine |
| `django-project-analyzer` | Project profile and ranked risks | Change anything |
| `django-architecture-agent` | App boundaries, layering, ADRs, implementation plan; scaffolding when asked | Implement models, APIs or business logic |
| `django-model-agent` | Models, constraints, indexes, migrations (with a risk assessment) | Write APIs or services; touch non-test databases |
| `django-api-agent` | DRF serializers, views, permissions, queryset scoping, API tests | Design models or architecture |
| `django-security-agent` | Evidence-backed security findings; minimal fixes with regression tests in remediation mode | Write without approval (every write asks) |
| `django-testing-agent` | Unit, integration and API tests; runs the suite on the test database | Change non-test code |
| `django-performance-agent` | Measure, optimise, re-measure | Optimise without measurements |
| `django-documentation-agent` | Documentation traced to code | Change application code; use a shell |
| `django-code-review-agent` | Severity-ranked review with a verdict | Change anything |

Each agent file is the source of truth for its own behaviour; do not restate it elsewhere.

## 4. Skills and rules

Knowledge is layered so nothing is duplicated:

- **Skills** (`skills/<id>/SKILL.md` + `references/`): *how* to do the work well.
- **Rules** (`rules/<id>/SKILL.md`): *what must hold*, as numbered requirements (`SEC-M4`, `PRF-M1`, ...)
  that agents cite in findings. `django-security-standards` also defines the conduct rules (`SEC-A*`) every
  agent follows: untrusted workspace content, secret handling, approvals, role and tool limits.
- **Templates**: report shape. **References**: checklists shared by several agents, linking (not copying)
  rule ids and skill references.
- Which skills and rules an agent preloads is its frontmatter `skills:` line (namespaced
  `django-engineering:<id>`).

## 5. Security

Enforced: read-only agents cannot write; documentation agent writes documentation paths only and has no
shell; security agent asks on every write; destructive, network and privileged commands ask; secrets paths
denied and output masked; paths confined to the project; guard failures block (fail closed); the
orchestrator cannot delegate to itself or outside the nine specialists; specialists cannot start agents.

Limitations (keep them in every external description): not a sandbox; acts only on the plugin's ten
agents; needs `python` on `PATH` or all tool calls are blocked; approvals are Claude Code's prompt (no
audit log, refused in `-p` mode); delegation count and retry limits are instructions, not enforced.
**Never claim parity with the harness's security.** Details: [docs/security.md](docs/security.md).

## 6. Development workflow

Setup: `python -m pip install -r requirements-dev.txt` (pytest and PyYAML are for tests only).
Try changes live: `claude --plugin-dir .` from the repository root, then `/reload-plugins`.

| To change | Edit | Also update | Then |
|---|---|---|---|
| An agent's behaviour | `agents/<id>.md` | If `tools` changed: `hooks/security-policy.json` entry (`tools`) | tests |
| Which skills/rules an agent preloads | frontmatter `skills:` of the agent | nothing else | tests |
| Routing (categories, routes, limits, specialists) | `config/orchestration-policy.yaml` | the `GENERATED` routing section of `agents/django-orchestrator.md`; `delegates` in `security-policy.json` | tests |
| A skill / a rule | `skills/<id>/...` / `rules/<id>/SKILL.md` | cross-links; rule ids cited by references | tests |
| A template / reference | `templates/..` / `references/..` | the agents' `## Templates and references` lines; the README tables | tests |
| Guard behaviour or policy | `hooks/django_pack_guard.py`, `hooks/security-policy.json` | `docs/security.md` | tests, add a regression test |
| Adding or removing a component | the file | `plugin.json` lists, README counts, `tests/test_plugin_structure.py` expected counts | tests |

Rules of the road:

1. Preserve **role, tools and write mode** of every agent. A change that widens a tool or a path needs a
   security review and a matching test. Policy can only take capability away.
2. Names must be unique across agents, skills and rules. Approval gates live in the agent files (`## Approval gate`). The only user-facing entry is the `orchestrate` entry skill, which holds no routing or safety logic. Every other skill and rule keeps `user-invocable: false`, and there is no `commands/` folder.
3. Keep `plugin.json` free of a `hooks` key (the default `hooks/hooks.json` is already loaded).
4. After intentional edits to canonical files, refresh the hashes: they are recorded in
   `CANONICAL-MANIFEST.json`; `tests/test_manifest.py` fails on any file changed without updating its
   recorded `sha256`. Record the reason in `CHANGELOG.md`. Files that originate in the main repository
   (`origin: canonical`) are *derived copies*; if you diverge from them, say so in the changelog so the
   owners of the main repository are not surprised on the next synchronisation.
5. Do not add network access, credentials or a Python dependency to any component.

## 7. Testing

```bash
python -m pytest                 # whole offline suite (no Claude Code needed)
python -m pytest -m live         # opt-in: loads the plugin through the installed Claude Code CLI
claude plugin validate .         # Claude Code's own manifest validation
claude plugin validate .claude-plugin/marketplace.json
```

The offline suite checks: manifests; every referenced file; component counts and names; no path or
symlink escapes the root; no harness dependency (audit patterns); markdown links resolve;
`${CLAUDE_PLUGIN_ROOT}` paths resolve; skill and rule frontmatter; agent frontmatter and write-mode
contracts; policy/agent/orchestrator consistency; the guard's decisions (read-only, documentation-only,
approvals, secrets, path confinement, fail-closed, delegation); the manifest hashes; and that the guard
runs with no packages beyond the standard library. Run it from a fresh clone before every release.

## 8. Release process

1. Work on a branch; `python -m pytest`; `claude plugin validate .` and the marketplace validation.
2. Run `python -m pytest -m live` (needs Claude Code and a login) and smoke-test `@django-engineering:django-orchestrator
   plan only: <request>` in a real Django project.
3. Bump `version` in `.claude-plugin/plugin.json` **and** `.claude-plugin/marketplace.json` (semantic
   versioning: breaking change of an agent contract or entry point or a security regression fix = major; new
   capability = minor; fixes and wording = patch). `tests/test_plugin_structure.py` requires both to agree.
4. Update `CHANGELOG.md`; refresh `CANONICAL-MANIFEST.json` hashes for changed files.
5. Merge, tag `v<version>`, publish the repository. Users run `claude plugin marketplace update
   django-engineering-standalone` then `claude plugin update django-engineering@django-engineering-standalone`.

## 9. Explicit exclusions: what this team must NOT do

- **You do not own the Python harness** (`core/`, `runtime/`, `agent_runtime/`, `harness_bootstrap/`,
  provisioning scripts, execution database, workflow engine). It is a different product maintained in the
  main repository.
- **Do not introduce a Python harness dependency** of any kind: no imports from it, no calls to it, no
  `.django-engineering/` runtime, no environment variables or services it provides.
- **Do not duplicate the harness engine** (workflow execution, run records, approvers, checkpoints) here.
- **Do not modify the main repository's harness implementation** from this repository, and do not vendor
  its files.
- **Preserve the standalone execution model:** Claude Code subagents plus the guard hook; the orchestrator
  coordinates, specialists work, nothing else runs.
- Do not add harness-management commands (`setup-harness`, `harness-status`, `enable-harness`,
  `disable-harness`, `doctor`).
- Do not reference paths outside this repository, and do not use symlinks.

`tests/test_no_harness_dependency.py` enforces most of this mechanically.

## 10. Provenance and known gaps

- `CANONICAL-MANIFEST.json` maps every canonical file to its source path in the main repository, with
  SHA-256 hashes of source and copy (LF-normalised), the list of intentional standalone adaptations
  (AD-01 ... AD-12, with reasons) and the excluded harness components.
- Known gaps: `/agents` display quirk (Agents (0) in `plugin details`); `python` must be on `PATH`;
  macOS/Linux sandbox configuration untested; live (CLI) behaviour of specialist delegation depends on
  Claude Code's subagent model (a subagent orchestrator may return a ROUTING PLAN).
