"""The standalone distribution has no operational dependency on the Python Agentic Harness.

Documentation that explains what is excluded (TEAM_HANDOFF.md, CHANGELOG.md, CANONICAL-MANIFEST.json) may name
harness components. Nothing else may reference them, import them or call them.
"""

from __future__ import annotations

import ast
import re

from conftest import ROOT, all_files, policy, read, text_files

#: Files that legitimately name harness components in order to exclude them.
CONTEXT_FILES = {"TEAM_HANDOFF.md", "CHANGELOG.md", "CANONICAL-MANIFEST.json", "README.md", "commands/README.md",
                 "hooks/README.md"}
#: Harness-only identifiers: forbidden everywhere except the context files and this test.
STRICT = [r"core\.cli", r"ExecutionManager", r"AgentRunner", r"harness_bootstrap", r"django_harness",
          r"python -m core", r"python -m plugin_packaging", r"plugin_packaging", r"DJANGO_HARNESS", r"scripts/harness",
          r"setup-harness", r"harness-status", r"enable-harness", r"disable-harness", r"/django-engineering:doctor",
          r"agent-registry", r"framework-config", r"security-config", r"skill-registry", r"sqlite_store",
          r"\.setup\.lock", r"installation\.json"]
#: Harness product terms: forbidden in every functional file (docs may explain what is absent).
SOFT = [r"execution database", r"\bRunRecord", r"approver service"]
#: Harness module names that no Python file may import.
HARNESS_MODULES = {"core", "runtime", "agent_runtime", "harness_bootstrap", "plugin_packaging", "contracts"}
#: The only places the directory name `.django-engineering` may appear (a deny-only path safeguard, no dependency).
RUNTIME_DIR_ALLOWED = {"hooks/security-policy.json", "docs/security.md"}
#: Guard/analyser docstrings may name the harness's guard for architectural context (comments, not code).
DOCSTRING_CONTEXT = {"hooks/django_pack_guard.py", "hooks/shell_syntax.py"}
#: Harness terms the guard's docstrings may use to explain what the guard is not (comments only).
DOCSTRING_TERMS = {"hooks/django_pack_guard.py": {"security-config", "approver service"}}
ABSOLUTE = [r"(?<![A-Za-z])[A-Za-z]:[\\/](?!\\)[\w .-]+[\\/]", r"(?<![\w.])/(?:Users|home|c|mnt|tmp)/[\w.-]+", r"POD-11", r"hmandadhi",
            r"django-agentic-engineering/"]


def _rel(path) -> str:
    return path.relative_to(ROOT).as_posix()


def _scannable():
    return [p for p in text_files() if not _rel(p).startswith("tests/")]


def test_no_harness_identifiers_outside_context_files() -> None:
    hits = []
    for path in _scannable():
        if _rel(path) in CONTEXT_FILES:
            continue
        text = read(path)
        for pattern in STRICT + ([] if _rel(path).startswith("docs/") else SOFT):
            for match in re.finditer(pattern, text):
                if match.group(0) in DOCSTRING_TERMS.get(_rel(path), ()):
                    continue
                hits.append(f"{_rel(path)}: {match.group(0)}")
    assert not hits, hits


def test_no_python_file_imports_the_harness() -> None:
    for path in all_files():
        if path.suffix != ".py":
            continue
        for node in ast.walk(ast.parse(read(path))):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            for name in names:
                assert name.split(".")[0] not in HARNESS_MODULES, f"{_rel(path)} imports {name}"


def test_harness_runtime_directory_is_only_a_denied_path() -> None:
    mentions = [_rel(p) for p in _scannable() if ".django-engineering" in read(p) and _rel(p) not in CONTEXT_FILES]
    assert set(mentions) <= RUNTIME_DIR_ALLOWED, mentions
    data = policy()
    assert "**/.django-engineering" in data["paths_deny"] and "**/.django-engineering/**" in data["paths_deny"]


def test_the_word_harness_is_absent_from_every_functional_file() -> None:
    """Agents, commands, skills, rules, templates, references, config and manifests never mention the harness.

    Allowed: documentation (it explains the separate product), the guard docstrings, and one unrelated
    engineering term ("benchmark harness") inside a skill reference.
    """
    hits = []
    for path in _scannable():
        rel = _rel(path)
        top = rel.split("/")[0]
        root_doc = "/" not in rel and path.suffix == ".md"
        if top == "docs" or root_doc or rel in CONTEXT_FILES or rel in DOCSTRING_CONTEXT \
                or path.name == "README.md" or rel in {".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"}:
            continue
        for number, line in enumerate(read(path).splitlines(), 1):
            if re.search(r"harness", line, re.I) and "benchmark harness" not in line.lower() and "no Python harness" not in line:
                hits.append(f"{rel}:{number}: {line.strip()[:80]}")
    assert not hits, hits


def test_no_absolute_or_external_repository_paths() -> None:
    hits = []
    for path in _scannable():
        if path.name == "CANONICAL-MANIFEST.json":
            continue
        for pattern in ABSOLUTE:
            for match in re.finditer(pattern, read(path)):
                text = match.group(0)
                if "/tmp/" in text or text.startswith("/tmp"):      # shell examples in skills/references
                    continue
                hits.append(f"{_rel(path)}: {text}")
    assert not hits, hits[:20]


def test_hooks_json_uses_only_the_plugin_root() -> None:
    text = read(ROOT / "hooks" / "hooks.json")
    paths = re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}[^\"]*", text)
    assert paths and all(p.startswith("${CLAUDE_PLUGIN_ROOT}/hooks/") for p in paths)
    assert not re.search(r"core|runtime|harness|\.venv", text)


def test_orchestrate_command_has_no_execution_mode_resolver() -> None:
    body = read(ROOT / "commands" / "orchestrate.md")
    assert "## Agent" in body and "Harness mode" not in body and "Execution mode" not in body
    assert not re.search(r"^\s*python3?", body, re.M) and "CLAUDE_PLUGIN_ROOT}/harness" not in body


def test_guard_runs_without_any_package_but_the_standard_library() -> None:
    imports = set()
    for name in ("django_pack_guard.py", "shell_syntax.py"):
        imports |= set(re.findall(r"^(?:from|import) ([a-zA-Z_]+)", read(ROOT / "hooks" / name), flags=re.M))
    assert imports <= {"__future__", "json", "os", "re", "shlex", "sys", "fnmatch", "pathlib", "shell_syntax", "glob",
                       "dataclasses", "typing"}, imports
