---
name: django-security
description: >-
  Run a Django and DRF security assessment and report severity-ranked findings with evidence
  and remediation guidance. Review-only by default; fixes are applied only with --fix and the
  user's approval. Runs the django-security-agent.
argument-hint: "[scope: paths, app or endpoint] [--base <git ref>] [--fix [SEC-001,...]]"
project: django-agentic-engineering
abstract: >-
  Developer command that briefs django-security-agent for an evidence-backed security review,
  with remediation only on explicit request and approval of the findings to fix.
sdlc_phase: Security
tech_stack: [Python, Django, Django REST Framework, OWASP]
domain: [Software Engineering, Security]
---

# /django-security

## Purpose

Use before a release, after a risky change, or when `/django-analyze` or `/django-review`
flags a security concern. The default result is a report; nothing in the project changes
unless the user explicitly asks for fixes.

## Arguments

`$ARGUMENTS`

- Free text: the scope (paths, apps, endpoints) and any compliance needs or accepted risks.
  Default scope: the whole project in the current directory.
- `--base <git ref>`: assess only what changed since that ref.
- `--fix`: request remediation after the review. `--fix SEC-001,SEC-004` limits it to those
  findings from a report already in this conversation.
- `@file` mentions (prior findings, profiles) are passed as context.

## Agent

Delegate to the `django-security-agent` subagent. It owns the assessment method, the finding
format and remediation; this command supplies the brief and the authorization gate. The main
session does not assess or fix anything itself.

## Skills and rules

Tell the agent to apply these, by id. In the Django Engineering Pack they live at
`skills/<id>/SKILL.md` and `rules/<id>/SKILL.md`
(installed plugin: under `${CLAUDE_PLUGIN_ROOT}`, and preloaded into the agent).

- Skills: `django-security-engineering` · `django-rest-framework` · `django-integrations`
- Rules: `django-security-standards` · `django-configuration-standards` · `django-logging-standards` · `django-dependency-standards` · `django-api-standards` · `django-coding-standards` · `django-testing-standards` · `django-documentation-standards`

## Documentation context

Tell the agent to follow `DOC-M9` to `DOC-M16` and the registry protocol in the pack at `references/sdlc-documentation-registry.md`
(installed plugin: `${CLAUDE_PLUGIN_ROOT}/references/sdlc-documentation-registry.md`): read `docs/sdlc/registry.json` first, consume current
documents, review stale ones, never edit an `approved` document in place, report conflicts, and state assumptions
instead of inventing details. The workflow is defined once, in that reference; this command adds only the following.

- Consume the security design (SEC), HLD, API specification, configuration and deployment documents; report findings that contradict them.
- The security agent returns SEC content in its report and writes or changes SEC only with the user's approval (its confirm-writes mode); otherwise run
  `/django-document` to persist the content. No secret values or exploit details in any document.

## Authorization

- **Without `--fix`:** review mode. The agent must not change the workspace; the report is
  returned in its reply. Do not offer to apply fixes in the same run; suggest re-running with
  `--fix` instead.
- **With `--fix`:** run the review first (unless the named findings are already in this
  conversation), list the findings that would be fixed, and ask the user to approve that list.
  Then brief the agent in remediation mode for the approved findings only. Each fix comes with
  a test showing the issue is blocked.
- **Documents:** the security design (SEC) is written or changed only with the user's approval; in
  review mode its content is returned in the report.
- Never: exploits or requests against live systems, network calls, package installs, reading
  denied files, or printing secret values. A found secret is reported by location and type,
  with a rotation recommendation.

## Steps

1. Parse the scope, base ref and `--fix` selection.
2. Brief the agent for the review:
   - **Objective:** security assessment of the scope; review mode.
   - **Constraints:** paths, compliance needs and accepted risks from the user.
   - **Inputs:** project root, base ref, `@file` context.
   - **Expected outputs:** the security report with findings.
3. Relay the report, ordered by severity, with the overall risk verdict.
4. Only with `--fix`: apply the authorization gate above, then brief the agent in
   remediation mode with the approved finding ids, and relay the fixes and their tests.

## Expected output

The security report: summary and risk verdict, scope and attack surface, findings (id,
severity, category, `file:line`, evidence, impact, recommendation, status), configuration
checklist results, accepted risks and limitations. With `--fix`: the fixes applied and the
test proving each one.

Template: `security-assessment`. Templates are in the pack at `templates/<id>.template.md`
(installed plugin: `${CLAUDE_PLUGIN_ROOT}/templates/<id>.template.md`).
Name them in the brief's expected outputs so the agent's reply follows their structure.

## Completion criteria

- [ ] Every finding has severity, location, evidence, impact and a remediation.
- [ ] Without `--fix`, the workspace is unchanged.
- [ ] With `--fix`, only the approved findings were changed, each with a passing test.
- [ ] No secret value appears in any output.
