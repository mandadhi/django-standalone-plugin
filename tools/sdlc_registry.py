#!/usr/bin/env python3
"""SDLC documentation registry helper (standard library only).

The registry is one JSON file in the *project being documented* (default ``docs/sdlc/registry.json``). It is the
shared index of project documentation for the Orchestrator and every specialist agent, on both Claude Code and
GitHub Copilot.

Agents maintain the registry by reading and editing the JSON directly, following the protocol in
references/sdlc-documentation-registry.md. The plugin's security guard keeps agents from running scripts that live
outside the project, so this tool is NOT part of the agents' runtime: it is the deterministic validator that a person
(`! python <plugin>/tools/sdlc_registry.py check` in Claude Code, or a terminal) or CI runs to verify what the agents
wrote: schema, files, stale and silently-changed documents, which documents apply, the documentation impact of a code
change, and Mermaid sources. Hand-written registries (sources as plain paths, no hashes) are supported.

    python tools/sdlc_registry.py init  [--project NAME] [--profile minimal|standard|enterprise]
    python tools/sdlc_registry.py plan
    python tools/sdlc_registry.py check [--strict] [--mark-stale] [--json]
    python tools/sdlc_registry.py register --type SRS --name "..." [--id ID] [--path P] [--source P ...] [--depends-on ID ...]
    python tools/sdlc_registry.py update ID [--bump minor|major] [--propose PATH]
    python tools/sdlc_registry.py approve ID --by NAME
    python tools/sdlc_registry.py impact (--changed PATH ... | --git) [--category CAT ...] [--json]
    python tools/sdlc_registry.py mermaid PATH ...

Read-only commands: plan, check (without --mark-stale), impact, mermaid. Common option: --project-dir DIR (default .).
Exit status: 0 clean, 1 errors found (or warnings with --strict), 2 usage or I/O problem.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[1] / "config" / "sdlc-documentation-catalog.json"
REGISTRY_REL = "docs/sdlc/registry.json"
SCHEMA_VERSION = "1.0"
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".tox", ".mypy_cache", "site-packages"}
MERMAID_TYPES = {"flowchart", "graph", "sequenceDiagram", "classDiagram", "classDiagram-v2", "stateDiagram", "stateDiagram-v2",
                 "erDiagram", "journey", "gantt", "pie", "gitGraph", "mindmap", "timeline", "quadrantChart",
                 "requirementDiagram", "block-beta", "architecture-beta", "C4Context", "C4Container", "C4Component",
                 "C4Dynamic", "C4Deployment"}
REQUIRED_FIELDS = ("id", "name", "type", "stage", "path", "status", "version", "responsible_agent", "last_updated")


class Problem:
    def __init__(self, level: str, code: str, doc: str, message: str):
        self.level, self.code, self.doc, self.message = level, code, doc, message

    def as_dict(self) -> dict:
        return {"level": self.level, "code": self.code, "doc": self.doc, "message": self.message}

    def __str__(self) -> str:
        return f"{self.level.upper():7} {self.code:22} {self.doc or '-':10} {self.message}"


# ----------------------------------------------------------------------------- helpers

def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace").replace("\r\n", "\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def src_path(src) -> str:
    """A source is a path string (hand-written by an agent) or {"path", "sha256"} (stamped by this tool)."""
    return src if isinstance(src, str) else src["path"]


def src_hash(src) -> "str | None":
    return None if isinstance(src, str) else src.get("sha256")


def _git_time(project: Path, path: str) -> "datetime | None":
    try:
        res = subprocess.run(["git", "log", "-1", "--format=%cI", "--", path], cwd=project, capture_output=True,
                             text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return datetime.fromisoformat(res.stdout.strip()) if res.stdout.strip() else None


def source_changed(project: Path, doc: dict, src) -> bool:
    """True when a source changed after the document was written.

    Stamped sources compare SHA-256. Hand-written sources (no hash) compare the last git commit time of the file
    with the document's `last_updated`; outside a git repository the file modification time is used."""
    path = project / src_path(src)
    if src_hash(src):
        return sha(path) != src_hash(src)
    try:
        updated = datetime.fromisoformat(str(doc["last_updated"]).replace("Z", "+00:00"))
    except ValueError:
        return False
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    changed = _git_time(project, src_path(src))
    if changed is None:
        changed = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return changed > updated


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def glob_regex(pattern: str) -> "re.Pattern[str]":
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile(out + r"\Z", re.I)


def matches(path: str, patterns: list) -> bool:
    return any(glob_regex(p).match(path) for p in patterns)


def rel(project: Path, path: Path) -> str:
    return path.resolve().relative_to(project.resolve()).as_posix()


def walk(base: Path):
    for p in sorted(base.rglob("*")):
        if p.is_file() and not (set(p.relative_to(base).parts) & SKIP_DIRS):
            yield p


class Registry:
    def __init__(self, project: Path, catalog: dict | None = None):
        self.project = project.resolve()
        self.catalog = catalog or load_catalog()
        self.path = self.project / REGISTRY_REL
        self.data: dict = {}
        self.types = {t["type"]: t for t in self.catalog["types"]}

    # --- io
    def load(self) -> None:
        if not self.path.is_file():
            raise SystemExit(f"no registry at {REGISTRY_REL}; run `init` first")
        try:
            self.data = json.loads(read_text(self.path))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{REGISTRY_REL} is not valid JSON: {exc}")

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes((json.dumps(self.data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))

    @property
    def docs(self) -> list:
        return self.data.get("documents", [])

    def get(self, doc_id: str) -> dict:
        for d in self.docs:
            if d.get("id") == doc_id:
                return d
        raise SystemExit(f"unknown document id: {doc_id}")

    def file_of(self, doc: dict) -> Path:
        return self.project / doc["path"]


# ----------------------------------------------------------------------------- mermaid lint

_SHAPES = {"[": "]", "(": ")", "{": "}"}


def _strip_quotes(line: str) -> str:
    return re.sub(r'"[^"]*"', '""', line)


def _balanced(line: str) -> bool:
    stack = []
    for ch in _strip_quotes(line):
        if ch in _SHAPES:
            stack.append(_SHAPES[ch])
        elif ch in ")]}":
            if not stack or stack.pop() != ch:
                return False
    return not stack


def _clean(text: str) -> list:
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    lines = []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line or line.startswith("%%"):
            continue
        lines.append(line)
    return lines


def mermaid_type(text: str) -> "str | None":
    lines = _clean(text)
    if not lines:
        return None
    head = lines[0].split()[0].rstrip(";")
    return head if head in MERMAID_TYPES else None


def lint_mermaid(text: str, allowed: "list | None" = None) -> list:
    """Structural lint of one Mermaid diagram. Not a renderer: it catches the errors that break rendering or
    point at things that do not exist (unbalanced brackets, wrong diagram type, unknown participants, dangling
    edges, unknown style targets, undefined C4 aliases, malformed ER relationships)."""
    lines = _clean(text)
    if not lines:
        return ["diagram is empty"]
    kind = mermaid_type(text)
    if kind is None:
        return [f"first line must declare a diagram type (found {lines[0].split()[0]!r})"]
    problems = []
    if allowed and kind not in allowed:
        problems.append(f"diagram type {kind} is not allowed here (expected one of {', '.join(allowed)})")
    body = lines[1:]
    first = lines[0].split()
    if kind in ("flowchart", "graph") and len(first) > 1 and first[1].rstrip(";") not in ("TD", "TB", "BT", "RL", "LR"):
        problems.append(f"unknown flowchart direction {first[1]!r}")
    if kind in ("flowchart", "graph"):
        problems += _lint_flowchart(body)
    elif kind == "sequenceDiagram":
        problems += _lint_sequence(body)
    elif kind == "erDiagram":
        problems += _lint_er(body)
    elif kind.startswith("C4"):
        problems += _lint_c4(body)
    elif kind.startswith(("classDiagram", "stateDiagram")):
        depth = sum(l.count("{") - l.count("}") for l in body)
        if depth:
            problems.append("unbalanced { } blocks")
    return problems


_ARROW = r"(?:<?-{2,}[>xo]?|<?={2,}[>xo]?|-\.+-?>?|~~~)"


def _lint_flowchart(body: list) -> list:
    problems, defined, depth = [], set(), 0
    refs = []
    for line in body:
        low = line.split()[0]
        if low == "subgraph":
            depth += 1
            continue
        if low == "end":
            depth -= 1
            if depth < 0:
                problems.append("`end` without a matching `subgraph`")
                depth = 0
            continue
        if low in ("direction", "classDef", "linkStyle", "accTitle", "accDescr"):
            continue
        if low in ("style", "class", "click"):
            parts = line.replace(",", " ").split()
            targets = parts[1:-1] if low == "class" else parts[1:2]
            refs += [(low, t) for t in targets]
            continue
        if not _balanced(line):
            problems.append(f"unbalanced brackets in: {line}")
            continue
        flat = line
        for _ in range(3):
            flat = re.sub(r'\[[^\[\]]*\]|\([^()]*\)|\{[^{}]*\}', "", _strip_quotes(flat))
        flat = re.sub(r"\|[^|]*\|", " ", flat)
        flat = re.sub(r"--\s[^-=>]+\s(?=-->|---)", "-- ", flat)
        parts = re.split(_ARROW, flat)
        has_edge = len(parts) > 1
        if has_edge and re.search(_ARROW + r"\s*;?\s*$", flat.strip()):
            problems.append(f"edge without a target: {line}")
        if has_edge and not parts[0].strip():
            problems.append(f"edge without a source: {line}")
        for part in parts:
            for token in re.split(r"[&;]", part):
                token = token.strip().split(":::")[0]
                if re.fullmatch(r"[A-Za-z_][\w-]*", token):
                    defined.add(token)
    if depth:
        problems.append("`subgraph` without a matching `end`")
    for kind, ref in refs:
        if ref not in defined and not ref.startswith(("default",)):
            problems.append(f"`{kind}` refers to undefined node {ref!r}")
    return problems


def _lint_sequence(body: list) -> list:
    problems, declared, blocks, active = [], set(), 0, {}
    msg = re.compile(r"^(.+?)\s*(?:-->>|->>|--x|-x|--\)|-\)|-->|->)\s*[+-]?(.+?)\s*:\s*(.*)$")
    decl = re.compile(r"^(?:participant|actor)\s+(\S+)(?:\s+as\s+.+)?$")
    for line in body:
        m = decl.match(line)
        if m:
            declared.add(m.group(1))
            continue
        word = line.split()[0]
        if word in ("alt", "opt", "loop", "par", "critical", "break", "rect"):
            blocks += 1
            continue
        if word in ("else", "and", "option"):
            continue
        if word == "end":
            blocks -= 1
            if blocks < 0:
                problems.append("`end` without an opening block")
                blocks = 0
            continue
        if word in ("activate", "deactivate"):
            who = line.split(None, 1)[1].strip() if len(line.split(None, 1)) > 1 else ""
            if declared and who not in declared:
                problems.append(f"{word} refers to undeclared participant {who!r}")
            active[who] = active.get(who, 0) + (1 if word == "activate" else -1)
            continue
        if word in ("Note", "note", "title", "autonumber", "box", "link", "links", "accTitle", "accDescr"):
            if word.lower() == "note":
                mm = re.match(r"(?i)note\s+(?:over|left of|right of)\s+([^:]+):", line)
                if mm and declared:
                    for who in re.split(r"\s*,\s*", mm.group(1).strip()):
                        if who not in declared:
                            problems.append(f"Note refers to undeclared participant {who!r}")
            continue
        mm = msg.match(line)
        if not mm:
            problems.append(f"unrecognised sequence statement: {line}")
            continue
        for who in (mm.group(1).strip(), mm.group(2).strip().lstrip("+-")):
            if declared and who not in declared:
                problems.append(f"message uses undeclared participant {who!r}: {line}")
    if blocks:
        problems.append("block (alt/opt/loop/par/critical/break/rect) without `end`")
    return problems


def _lint_er(body: list) -> list:
    problems, inside = [], False
    rel_re = re.compile(r"^(\w+)\s+([|}o]{1,2}(?:--|\.\.)[|{o]{1,2})\s+(\w+)\s*:\s*(.+)$")
    for line in body:
        if inside:
            if line == "}":
                inside = False
            elif len(line.split()) < 2:
                problems.append(f"attribute needs a type and a name: {line}")
            continue
        if re.match(r"^\w+\s*\{$", line):
            inside = True
        elif rel_re.match(line):
            continue
        elif re.match(r"^\w+$", line):
            continue
        else:
            problems.append(f"malformed ER statement: {line}")
    if inside:
        problems.append("entity block without closing }")
    return problems


def _lint_c4(body: list) -> list:
    problems, defined, uses = [], set(), []
    element = re.compile(r"^(?:Person|Person_Ext|System|System_Ext|SystemDb|SystemDb_Ext|Container|Container_Ext|ContainerDb|ContainerDb_Ext|"
                         r"ContainerQueue|Component|Component_Ext|ComponentDb|Deployment_Node|Node|System_Boundary|Container_Boundary|"
                         r"Enterprise_Boundary|Boundary)\s*\(\s*([\w-]+)")
    rel = re.compile(r"^(?:Rel|BiRel|Rel_[UDLRBack]+|RelIndex)\s*\(\s*([\w-]+)\s*,\s*([\w-]+)")
    depth = 0
    for line in body:
        if not _balanced(line.rstrip("{").rstrip()):
            problems.append(f"unbalanced parentheses in: {line}")
            continue
        depth += line.count("{") - line.count("}")
        m = element.match(line)
        if m:
            defined.add(m.group(1))
            continue
        m = rel.match(line)
        if m:
            uses.append((m.group(1), m.group(2), line))
    if depth:
        problems.append("unbalanced { } boundary blocks")
    for a, b, line in uses:
        for alias in (a, b):
            if alias not in defined:
                problems.append(f"relationship refers to undefined element {alias!r}: {line}")
    return problems


_FENCE = re.compile(r"(?:<!--\s*mermaid-source:\s*(\S+)\s*-->\s*\n)?```mermaid\n(.*?)\n```", re.S)


def embedded_diagrams(text: str) -> list:
    return [(m.group(1), m.group(2)) for m in _FENCE.finditer(text)]


def er_entities(text: str) -> set:
    names = set(re.findall(r"^\s*(\w+)\s*\{", text, re.M))
    for a, b in re.findall(r"^\s*(\w+)\s+[|}o]{1,2}(?:--|\.\.)[|{o]{1,2}\s+(\w+)", text, re.M):
        names |= {a, b}
    return names


def _norm(name: str) -> str:
    return name.replace("_", "").lower()


# ----------------------------------------------------------------------------- facts, plan

def detect_facts(project: Path) -> dict:
    facts = {k: False for k in ("has_models", "has_api", "has_integrations", "has_deployment", "has_ci")}
    manifest_text = ""
    for p in walk(project):
        r = p.relative_to(project).as_posix()
        name = p.name
        if name == "models.py" or "/models/" in "/" + r:
            facts["has_models"] = True
        if re.match(r"(?i)(requirements.*\.txt|pyproject\.toml|pipfile)$", name):
            manifest_text += read_text(p).lower()
        if name.startswith(("Dockerfile", "docker-compose")) or r.startswith(("k8s/", "helm/", "terraform/", "deploy/")):
            facts["has_deployment"] = True
        if r.startswith(".github/workflows/") or name in (".gitlab-ci.yml", "Jenkinsfile"):
            facts["has_ci"] = True
        if p.suffix == ".py" and name in ("urls.py", "serializers.py", "views.py") and "rest_framework" in read_text(p):
            facts["has_api"] = True
    if "djangorestframework" in manifest_text:
        facts["has_api"] = True
    if re.search(r"celery|requests|httpx|boto3|stripe|kombu|zeep|paramiko|twilio|sendgrid", manifest_text):
        facts["has_integrations"] = True
    return facts


PROFILE_ORDER = {"minimal": 0, "standard": 1, "enterprise": 2}


def applicable_types(reg: Registry) -> list:
    profile = PROFILE_ORDER[reg.data.get("profile", "standard")]
    facts = reg.data.get("facts", {})
    na = {n["type"] for n in reg.data.get("not_applicable", [])}
    out = []
    for t in reg.catalog["types"]:
        if t["type"] in na or t.get("on_demand"):
            continue
        if PROFILE_ORDER[t["min_profile"]] > profile:
            continue
        if t.get("requires_fact") and not facts.get(t["requires_fact"]):
            continue
        out.append(t)
    return out


def cmd_plan(reg: Registry, args) -> int:
    reg.load()
    registered: dict = {}
    for d in reg.docs:
        registered.setdefault(d["type"], []).append(d)
    result = []
    for stage in reg.catalog["stages"]:
        rows = []
        for t in applicable_types(reg):
            if t["stage"] != stage["id"]:
                continue
            docs = registered.get(t["type"], [])
            rows.append({"type": t["type"], "name": t["name"], "owner": t["owner"], "template": t["template"],
                         "registered": [f"{d['id']}:{d['status']}" for d in docs] or None,
                         "action": "ok" if docs and all(d["status"] != "missing" for d in docs)
                         else ("generate" if docs else "register-and-generate")})
        result.append({"stage": stage["id"], "documents": rows})
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"profile={reg.data.get('profile')} facts={json.dumps(reg.data.get('facts', {}))}")
        for s in result:
            print(f"\n[{s['stage']}]")
            for r in s["documents"]:
                print(f"  {r['type']:6} {r['action']:20} owner={r['owner']} registered={r['registered']}")
        print("\nOn-demand types (created only when the event happens): " +
              ", ".join(t["type"] for t in reg.catalog["types"] if t.get("on_demand")))
    return 0


# ----------------------------------------------------------------------------- check

def check_registry(reg: Registry) -> list:
    P: list = []
    d = reg.data
    cat = reg.catalog
    statuses, stages = set(cat["statuses"]), {s["id"] for s in cat["stages"]}
    if d.get("schema_version") != SCHEMA_VERSION:
        P.append(Problem("error", "schema", "", f"schema_version must be {SCHEMA_VERSION!r}"))
    if d.get("profile") not in cat["profiles"]:
        P.append(Problem("error", "schema", "", f"profile must be one of {cat['profiles']}"))
    ids = [x.get("id") for x in reg.docs]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        P.append(Problem("error", "duplicate-id", dup, "document id is used more than once"))
    by_id = {x["id"]: x for x in reg.docs if "id" in x}
    for n in d.get("not_applicable", []):
        if n.get("type") not in reg.types or not str(n.get("reason", "")).strip():
            P.append(Problem("error", "schema", n.get("type", ""), "not_applicable needs a catalog type and a reason"))
    registered_paths = set()
    for doc in reg.docs:
        did = doc.get("id", "?")
        missing_fields = [f for f in REQUIRED_FIELDS if f not in doc or doc[f] in (None, "")]
        if missing_fields:
            P.append(Problem("error", "schema", did, f"missing fields: {', '.join(missing_fields)}"))
            continue
        t = reg.types.get(doc["type"])
        if not t:
            P.append(Problem("error", "unknown-type", did, f"type {doc['type']!r} is not in the catalog"))
            continue
        if doc["stage"] not in stages or doc["stage"] != t["stage"]:
            P.append(Problem("error", "stage-mismatch", did, f"stage {doc['stage']!r} does not match catalog stage {t['stage']!r}"))
        if doc["status"] not in statuses:
            P.append(Problem("error", "invalid-status", did, f"status {doc['status']!r} not in {sorted(statuses)}"))
            continue
        for ref_field in ("related", "depends_on"):
            for ref in doc.get(ref_field, []):
                if ref not in by_id:
                    P.append(Problem("error", "bad-reference", did, f"{ref_field} names unknown document {ref!r}"))
        registered_paths.add(doc["path"])
        file = reg.file_of(doc)
        exists = file.is_file()
        if doc["status"] == "missing":
            if exists:
                P.append(Problem("error", "file-exists-but-missing", did, f"{doc['path']} exists but status is missing"))
            continue
        if not exists:
            P.append(Problem("error", "file-missing", did, f"{doc['path']} does not exist but status is {doc['status']}"))
            continue
        # silent overwrite of an approved document
        if doc["status"] == "approved" or doc.get("approved_hash"):
            if doc.get("approved_hash") and sha(file) != doc["approved_hash"]:
                P.append(Problem("error", "approved-modified", did,
                                 f"{doc['path']} changed after approval without re-approval; restore it or record a new approval"))
            if doc["status"] == "approved" and not (doc.get("approved_by") and doc.get("approved_at")):
                P.append(Problem("error", "approval-record", did, "approved documents need approved_by and approved_at"))
            elif doc["status"] == "approved" and not doc.get("approved_hash"):
                P.append(Problem("warning", "approval-unsealed", did,
                                 "approved without approved_hash, so silent edits cannot be detected; run `approve` to seal it"))
        # staleness: sources and dependencies
        stale_reasons = []
        for src in doc.get("sources", []):
            sp = reg.project / src_path(src)
            if not sp.is_file():
                P.append(Problem("warning", "source-missing", did, f"source {src_path(src)} no longer exists"))
                stale_reasons.append(f"{src_path(src)} removed")
            elif source_changed(reg.project, doc, src):
                stale_reasons.append(f"{src_path(src)} changed")
        for dep, ver in doc.get("dependency_versions", {}).items():
            if dep in by_id and by_id[dep].get("version") != ver:
                stale_reasons.append(f"{dep} is now v{by_id[dep].get('version')} (was v{ver})")
        if stale_reasons and doc["status"] != "stale":
            P.append(Problem("warning", "stale", did, f"{doc['status']} document is out of date: " + "; ".join(stale_reasons)))
            doc["_stale_reasons"] = stale_reasons
        elif doc["status"] == "stale":
            P.append(Problem("warning", "stale", did, "marked stale; review and update" + (": " + "; ".join(stale_reasons) if stale_reasons else "")))
        if doc.get("pending_revision") and not (reg.project / doc["pending_revision"]).is_file():
            P.append(Problem("error", "pending-revision", did, f"pending revision {doc['pending_revision']} does not exist"))
        P += _check_content(reg, doc, t, file)
    # unregistered documents
    docs_root = reg.project / d.get("docs_root", "docs")
    if docs_root.is_dir():
        for p in walk(docs_root):
            r = rel(reg.project, p)
            if r == REGISTRY_REL or p.suffix not in (".md", ".mmd") or p.name.lower().startswith("readme") or p.name.endswith(".proposed.md"):
                continue
            if r not in registered_paths and r not in {x.get("pending_revision") for x in reg.docs}:
                P.append(Problem("warning", "unregistered", "", f"{r} is not in the registry (adopt it or ignore it deliberately)"))
    return P


def _check_content(reg: Registry, doc: dict, t: dict, file: Path) -> list:
    P = []
    did = doc["id"]
    text = read_text(file) if file.suffix in (".md", ".mmd") else ""
    if file.suffix == ".mmd" or t.get("diagram") and file.suffix == ".mmd":
        for problem in lint_mermaid(text, t.get("mermaid_kinds")):
            P.append(Problem("error", "mermaid", did, f"{doc['path']}: {problem}"))
        if t.get("diagram") and doc["type"] == "ERD":
            P += _check_er_against_sources(reg, doc, text)
    elif file.suffix == ".md":
        if did not in text:
            P.append(Problem("warning", "no-document-id", did, f"{doc['path']} does not mention its document id"))
        for source, block in embedded_diagrams(text):
            for problem in lint_mermaid(block):
                P.append(Problem("error", "mermaid", did, f"{doc['path']} (embedded): {problem}"))
            if source:
                sp = reg.project / source
                if not sp.is_file():
                    P.append(Problem("error", "diagram-source", did, f"embedded diagram source {source} does not exist"))
                elif read_text(sp).strip() != block.strip():
                    P.append(Problem("error", "diagram-drift", did, f"embedded diagram differs from its source {source}; re-embed it"))
        for target in re.findall(r"(?<!\!)\[[^\]]*\]\(([^)\s#]+)(?:#[^)]*)?\)", text):
            if re.match(r"[a-z][a-z0-9+.-]*:", target, re.I):
                continue
            if not (file.parent / target).resolve().exists():
                P.append(Problem("warning", "broken-link", did, f"{doc['path']} links to missing {target}"))
    return P


def _check_er_against_sources(reg: Registry, doc: dict, text: str) -> list:
    classes = set()
    for src in doc.get("sources", []):
        sp = reg.project / src_path(src)
        if sp.is_file() and sp.suffix == ".py":
            classes |= {_norm(c) for c in re.findall(r"^class\s+(\w+)\s*\(", read_text(sp), re.M)}
    if not classes:
        return []
    return [Problem("error", "diagram-misrepresents", doc["id"],
                    f"ERD entity {e!r} has no matching model class in the registered sources")
            for e in sorted(er_entities(text)) if _norm(e) not in classes]


def cmd_check(reg: Registry, args) -> int:
    reg.load()
    problems = check_registry(reg)
    if args.mark_stale:
        changed = []
        for doc in reg.docs:
            if doc.pop("_stale_reasons", None) and doc["status"] in ("draft", "approved"):
                doc["status"] = "stale"
                doc["last_updated"] = now()
                changed.append(doc["id"])
        for doc in reg.docs:
            doc.pop("_stale_reasons", None)
        if changed:
            reg.save()
            print("marked stale: " + ", ".join(changed))
    else:
        for doc in reg.docs:
            doc.pop("_stale_reasons", None)
    errors = [p for p in problems if p.level == "error"]
    warnings = [p for p in problems if p.level == "warning"]
    if args.json:
        counts: dict = {}
        for doc in reg.docs:
            counts[doc["status"]] = counts.get(doc["status"], 0) + 1
        print(json.dumps({"errors": len(errors), "warnings": len(warnings), "status_counts": counts,
                          "problems": [p.as_dict() for p in problems]}, indent=2))
    else:
        for p in problems:
            print(p)
        print(f"{len(reg.docs)} documents, {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors or (args.strict and warnings) else 0


# ----------------------------------------------------------------------------- write commands

def cmd_init(reg: Registry, args) -> int:
    if reg.path.is_file():
        print(f"{REGISTRY_REL} already exists; nothing changed")
        return 0
    reg.data = {"schema_version": SCHEMA_VERSION, "project": args.project or reg.project.name, "profile": args.profile,
                "docs_root": "docs", "facts": detect_facts(reg.project), "not_applicable": [], "documents": []}
    reg.save()
    print(f"created {REGISTRY_REL} (profile={args.profile}; facts detected: " +
          ", ".join(k for k, v in reg.data["facts"].items() if v) + ")")
    return 0


def _stamp(reg: Registry, doc: dict, sources: list) -> None:
    stamped = []
    for s in sources:
        sp = reg.project / s
        if not sp.is_file():
            raise SystemExit(f"source does not exist: {s}")
        stamped.append({"path": Path(s).as_posix(), "sha256": sha(sp)})
    if sources or "sources" not in doc:
        doc["sources"] = stamped
    doc["dependency_versions"] = {i: reg.get(i)["version"] for i in doc.get("depends_on", [])}


def cmd_register(reg: Registry, args) -> int:
    reg.load()
    t = reg.types.get(args.type)
    if not t:
        raise SystemExit(f"unknown type {args.type}; see config/sdlc-documentation-catalog.json")
    doc_id = args.id or f"{args.type}-{1 + sum(1 for d in reg.docs if d['type'] == args.type):03d}"
    if any(d["id"] == doc_id for d in reg.docs):
        raise SystemExit(f"{doc_id} is already registered")
    slug = re.sub(r"[^a-z0-9]+", "-", args.name.lower()).strip("-") or args.type.lower()
    ext = ".mmd" if t.get("diagram") else ".md"
    default = f"docs/{t.get('default_dir', t['stage'])}/{slug}{ext}"
    path = args.path or default
    exists = (reg.project / path).is_file()
    doc = {"id": doc_id, "name": args.name, "type": args.type, "stage": t["stage"], "path": Path(path).as_posix(),
           "status": "draft" if exists else "missing", "version": "0.1", "related": args.related or [],
           "depends_on": args.depends_on or [], "sources": [], "last_updated": now(),
           "responsible_agent": args.owner or t["owner"]}
    for ref in doc["related"] + doc["depends_on"]:
        reg.get(ref)
    _stamp(reg, doc, args.source or [])
    reg.docs.append(doc)
    reg.save()
    print(f"registered {doc_id} -> {doc['path']} ({doc['status']})")
    return 0


def cmd_update(reg: Registry, args) -> int:
    reg.load()
    doc = reg.get(args.id)
    if doc["status"] == "approved" and not args.propose:
        print(f"{args.id} is approved and is not changed silently. Write the revision to a proposed file and run "
              f"`update {args.id} --propose <path>`, or ask the user to withdraw the approval.", file=sys.stderr)
        return 1
    if args.propose:
        if not (reg.project / args.propose).is_file():
            raise SystemExit(f"proposed revision does not exist: {args.propose}")
        doc["pending_revision"] = Path(args.propose).as_posix()
        doc["last_updated"] = now()
        reg.save()
        print(f"recorded pending revision for {args.id}; the approved text is untouched until the user approves it")
        return 0
    if not reg.file_of(doc).is_file():
        raise SystemExit(f"{doc['path']} does not exist; write the document first")
    major, minor = (int(x) for x in str(doc["version"]).split(".")[:2])
    doc["version"] = f"{major + 1}.0" if args.bump == "major" else f"{major}.{minor + 1}"
    old_sources = [src_path(s) for s in doc.get("sources", [])]
    _stamp(reg, doc, args.source or old_sources)
    doc["status"] = "draft"
    doc["last_updated"] = now()
    reg.save()
    print(f"updated {args.id} to v{doc['version']} (draft); sources and dependency versions re-stamped")
    return 0


def cmd_approve(reg: Registry, args) -> int:
    reg.load()
    doc = reg.get(args.id)
    if doc.get("pending_revision"):
        proposed = reg.project / doc["pending_revision"]
        target = reg.file_of(doc)
        target.write_bytes(proposed.read_bytes())
        proposed.unlink()
        doc.pop("pending_revision")
        major, _ = (int(x) for x in str(doc["version"]).split(".")[:2])
        doc["version"] = f"{major + 1}.0"
        old_sources = [src_path(s) for s in doc.get("sources", [])]
        _stamp(reg, doc, old_sources)
    if not reg.file_of(doc).is_file():
        raise SystemExit(f"{doc['path']} does not exist")
    for src in doc.get("sources", []):
        if (reg.project / src_path(src)).is_file() and source_changed(reg.project, doc, src):
            raise SystemExit(f"{args.id} is stale ({src_path(src)} changed); update it before approval")
    major, minor = (int(x) for x in str(doc["version"]).split(".")[:2])
    if major == 0:
        doc["version"] = "1.0"
    doc.update(status="approved", approved_by=args.by, approved_at=now(), approved_hash=sha(reg.file_of(doc)), last_updated=now())
    reg.save()
    print(f"approved {args.id} v{doc['version']} by {args.by}")
    return 0


# ----------------------------------------------------------------------------- impact

def classify(reg: Registry, path: str) -> list:
    cats = []
    for c in reg.catalog["change_categories"]:
        if c["id"] == "code":
            continue
        if matches(path, c["path_globs"]):
            cats.append(c["id"])
    if not cats and matches(path, next(c for c in reg.catalog["change_categories"] if c["id"] == "code")["path_globs"]) \
            and "/tests/" not in "/" + path:
        cats.append("code")
    return cats


def assess_impact(reg: Registry, changed: list, extra_categories: list) -> dict:
    cats_by_file = {p: classify(reg, p) for p in changed}
    for c in extra_categories:
        cats_by_file.setdefault(f"(declared) {c}", []).append(c)
    cat_def = {c["id"]: c for c in reg.catalog["change_categories"]}
    rows: dict = {}

    def add(doc: dict, reason: str) -> None:
        r = rows.setdefault(doc["id"], {"id": doc["id"], "type": doc["type"], "path": doc["path"], "status": doc["status"],
                                        "owner": doc["responsible_agent"], "reasons": []})
        if reason not in r["reasons"]:
            r["reasons"].append(reason)

    affected_types: dict = {}
    for f, cats in cats_by_file.items():
        for c in cats:
            for t in cat_def[c]["affects"]:
                affected_types.setdefault(t, []).append(f"{c} change ({f})")
    for doc in reg.docs:
        for t, reasons in affected_types.items():
            if doc["type"] == t:
                for r in reasons[:3]:
                    add(doc, r)
        for src in doc.get("sources", []):
            if src_path(src) in changed:
                add(doc, f"source file {src_path(src)} changed")
    changed_ids = set(rows)
    queue = list(changed_ids)
    while queue:                                    # dependents of affected documents
        cur = queue.pop()
        for doc in reg.docs:
            if cur in doc.get("depends_on", []) and doc["id"] not in rows:
                add(doc, f"depends on {cur}")
                queue.append(doc["id"])
    for r in rows.values():
        r["action"] = {"approved": "propose-revision (approved: never overwrite silently)",
                       "missing": "generate if applicable",
                       "stale": "review and update", "draft": "update"}[r["status"]]
    registered_types = {d["type"] for d in reg.docs}
    applicable = {t["type"] for t in applicable_types(reg)}
    unregistered = [{"type": t, "name": reg.types[t]["name"], "applicable": t in applicable or bool(reg.types[t].get("on_demand")),
                     "reasons": reasons[:2]} for t, reasons in sorted(affected_types.items()) if t not in registered_types]
    return {"changed": changed, "categories": {f: c for f, c in cats_by_file.items() if c},
            "affected": sorted(rows.values(), key=lambda r: r["id"]), "unregistered_types": unregistered,
            "unaffected_count": len(reg.docs) - len(rows)}


def git_changed(project: Path) -> list:
    out = []
    for cmd in (["git", "diff", "--name-only", "HEAD"], ["git", "ls-files", "--others", "--exclude-standard"]):
        try:
            res = subprocess.run(cmd, cwd=project, capture_output=True, text=True, check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise SystemExit(f"git is required for --git: {exc}")
        out += [l.strip() for l in res.stdout.splitlines() if l.strip()]
    return sorted(set(out))


def cmd_impact(reg: Registry, args) -> int:
    reg.load()
    changed = [Path(p).as_posix().lstrip("./") for p in (args.changed or [])]
    if args.git:
        changed += git_changed(reg.project)
    if not changed and not args.category:
        raise SystemExit("give --changed PATH ..., --git or --category CAT")
    for c in args.category or []:
        if c not in {x["id"] for x in reg.catalog["change_categories"]}:
            raise SystemExit(f"unknown category {c}")
    result = assess_impact(reg, changed, args.category or [])
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print("Change categories: " + (", ".join(f"{f} -> {'/'.join(c)}" for f, c in result["categories"].items()) or "none"))
    print(f"\nAffected registered documents ({len(result['affected'])}; {result['unaffected_count']} untouched):")
    for r in result["affected"]:
        print(f"  {r['id']:10} [{r['status']}] {r['action']}  owner={r['owner']}\n             {r['path']}  because: {'; '.join(r['reasons'])}")
    if result["unregistered_types"]:
        print("\nAffected types with no registered document:")
        for u in result["unregistered_types"]:
            print(f"  {u['type']:6} {'(applicable? decide per profile)' if u['applicable'] else '(not applicable to this profile)'}  {u['name']}")
    return 0


def cmd_mermaid(reg: Registry, args) -> int:
    bad = 0
    for p in args.paths:
        file = Path(p)
        text = read_text(file)
        blocks = [(None, text)] if file.suffix == ".mmd" else embedded_diagrams(text)
        if not blocks:
            print(f"{p}: no Mermaid diagram found")
            bad += 1
        for _src, block in blocks:
            problems = lint_mermaid(block)
            for problem in problems:
                print(f"{p}: {problem}")
            bad += bool(problems)
            if not problems:
                print(f"{p}: ok ({mermaid_type(block)})")
    return 1 if bad else 0


# ----------------------------------------------------------------------------- cli

def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--project-dir", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("init")
    s.add_argument("--project")
    s.add_argument("--profile", default="standard", choices=["minimal", "standard", "enterprise"])
    sub.add_parser("plan").add_argument("--json", action="store_true")
    s = sub.add_parser("check")
    s.add_argument("--strict", action="store_true")
    s.add_argument("--mark-stale", action="store_true")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("register")
    s.add_argument("--type", required=True)
    s.add_argument("--name", required=True)
    s.add_argument("--id")
    s.add_argument("--path")
    s.add_argument("--owner")
    s.add_argument("--source", action="append")
    s.add_argument("--depends-on", action="append")
    s.add_argument("--related", action="append")
    s = sub.add_parser("update")
    s.add_argument("id")
    s.add_argument("--bump", choices=["minor", "major"], default="minor")
    s.add_argument("--source", action="append")
    s.add_argument("--propose")
    s = sub.add_parser("approve")
    s.add_argument("id")
    s.add_argument("--by", required=True)
    s = sub.add_parser("impact")
    s.add_argument("--changed", nargs="*")
    s.add_argument("--git", action="store_true")
    s.add_argument("--category", action="append")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("mermaid")
    s.add_argument("paths", nargs="+")
    args = ap.parse_args(argv)
    reg = Registry(Path(args.project_dir))
    handler = {"init": cmd_init, "plan": cmd_plan, "check": cmd_check, "register": cmd_register, "update": cmd_update,
               "approve": cmd_approve, "impact": cmd_impact, "mermaid": cmd_mermaid}[args.cmd]
    try:
        return handler(reg, args)
    except OSError as exc:
        print(f"I/O problem: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
