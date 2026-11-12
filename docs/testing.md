# Testing and validation

## Automated (offline)

`python -m pytest` runs the whole suite offline (live tests are opt-in).

| Area | Tests |
|---|---|
| Claude manifests, inventory, commands, agents, tools, skills, rules | `test_plugin_structure.py` |
| Guard, security policy, orchestration policy vs orchestrator | `test_guard.py`, `test_security_policy.py`, `test_orchestration_policy.py` |
| Manifest hashes, adaptations, generated-adapter mapping | `test_manifest.py` |
| Copilot adapter: ten command skills, hidden skills/standards, agent visibility, tool mapping, `agents:` = policy specialists, skills listed per agent, links, no Claude-only syntax, no second policy, drift detection | `test_copilot_adapter.py` |

`python tools/sync_copilot_adapter.py --check` is the synchronisation validator; it fails on missing, stale or orphaned
adapter files. `--matrix` prints the parity matrix below.

## Live (Claude Code)

`python -m pytest -m live` loads the plugin through the installed CLI. Verified with Claude Code 2.1.322:
`claude plugin validate .` passes (warnings: no icon, `commands/README.md` has no frontmatter); a session lists exactly
the ten commands `django-engineering:orchestrate` and `django-engineering:django-*`, the ten agents, and no skill or
rule. Delegation to specialists and the approval gates were not re-exercised with model calls in this change.

## Live (GitHub Copilot): NOT VERIFIED

No Copilot client was available. Nothing below is marked passed:

- the ten skills appearing in the `/` menu and each being invocable;
- hidden specialists absent from the picker but delegable;
- the orchestrator delegating to specialists (`agents:` honoured);
- internal skills loading on demand;
- security restrictions under Copilot.

To verify: open the repository in VS Code with Copilot Chat, type `/` and check for the ten names and no others, run
`/django-analyze` on a sample project, run `/orchestrate --plan-only ...`, and open the agent picker.

## Parity matrix

| Command | Claude Code | Copilot | Same workflow | Status |
|---|---|---|---|---|
| orchestrate | `/django-engineering:orchestrate` live-listed | `/orchestrate` structural | same body, same policy | Claude verified; Copilot structural only |
| django-analyze | live-listed | structural | same body | as above |
| django-design | live-listed | structural | same body | as above |
| django-model | live-listed | structural | same body | as above |
| django-api | live-listed | structural | same body | as above |
| django-security | live-listed | structural | same body | as above |
| django-test | live-listed | structural | same body | as above |
| django-optimize | live-listed | structural | same body | as above |
| django-document | live-listed | structural | same body | as above |
| django-review | live-listed | structural | same body | as above |

Other parity checked offline: agent responsibilities (bodies derived, headings compared), skill consumption (each
Copilot agent lists exactly the canonical `skills:`), standards (derived 1:1 from `rules/`), routing (one policy; the
orchestrator's `agents:` equals `specialists:`), tool ceilings. Security-control parity is **not** achieved: see
[copilot.md](copilot.md#security-model-on-copilot-honestly).

## Regression baseline

Before this change: 288 offline tests, all passing. After: 304 offline tests (16 new, in `test_copilot_adapter.py`), all
passing, plus the 3 opt-in live Claude Code tests. No test was deleted. Two expectations were deliberately changed
because the requirement changed: knowledge skills are now `user-invocable: false` (`test_plugin_structure.py`,
`test_plugin_live.py`).
