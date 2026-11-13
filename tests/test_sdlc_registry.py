"""SDLC documentation registry: catalog, registry tool, staleness, approval protection, impact assessment, Mermaid.

Runs the stdlib-only tool against a copy of a representative Django project (tests/fixtures/shop_project).
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import sys
from pathlib import Path

import pytest

from conftest import ROOT, SPECIALISTS, read

FIXTURE = ROOT / "tests" / "fixtures" / "shop_project"
ERD_OK = """erDiagram
    Customer ||--o{ Order : places
    Order ||--|{ OrderLine : contains
    Order {
        int id PK
        string status
    }
"""


def _tool():
    spec = importlib.util.spec_from_file_location("sdlc_registry", ROOT / "tools" / "sdlc_registry.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sdlc_registry"] = mod
    spec.loader.exec_module(mod)
    return mod


sdlc = _tool()
CATALOG = json.loads(read(ROOT / "config" / "sdlc-documentation-catalog.json"))


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    target = tmp_path / "shop"
    shutil.copytree(FIXTURE, target)
    return target


def run(project: Path, *args: str, capsys=None) -> tuple[int, str]:
    """Run the tool in-process; returns (exit code, everything it printed). `capsys` is accepted for readability."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = sdlc.main(["--project-dir", str(project), *args])
    return code, buffer.getvalue()


def codes(project: Path) -> set:
    return {p["code"] for p in json.loads(run(project, "check", "--json")[1])["problems"]}


def registry(project: Path) -> dict:
    return json.loads(read(project / "docs" / "sdlc" / "registry.json"))


def entry(project: Path, doc_id: str) -> dict:
    return next(d for d in registry(project)["documents"] if d["id"] == doc_id)


# ------------------------------------------------------------------------------ catalog

def test_catalog_covers_every_required_document_type_and_stage() -> None:
    types = {t["type"] for t in CATALOG["types"]}
    assert len(types) == len(CATALOG["types"])
    required = {"BRD", "SRS", "FRD", "NFR", "US", "AC", "RTM", "HLD", "SAD", "SOL", "C4", "ADR", "TDR", "CTX", "CMP",
                "LLD", "DBD", "ERD", "API", "SEQ", "DFD", "INT", "CD", "IMP", "MOD", "CFG", "MIG", "CODE", "TST", "TPL",
                "TC", "TER", "DEF", "DEP", "INF", "CICD", "ENV", "REL", "RBK", "RUN", "CHG", "INC", "RCA", "TDEBT", "ARU"}
    assert required <= types
    assert [s["id"] for s in CATALOG["stages"]] == ["requirements", "architecture", "detailed-design", "development",
                                                    "testing", "deployment", "maintenance"]
    assert {t["stage"] for t in CATALOG["types"]} == {s["id"] for s in CATALOG["stages"]}


def test_catalog_references_are_consistent() -> None:
    types = {t["type"]: t for t in CATALOG["types"]}
    for t in CATALOG["types"]:
        assert t["owner"] in SPECIALISTS, t["type"]
        assert t["min_profile"] in CATALOG["profiles"] and t["applies_when"].strip()
        assert (ROOT / "templates" / f"{t['template']}.template.md").is_file(), (t["type"], t["template"])
        assert set(t.get("depends_on", [])) <= set(types), t["type"]
        assert t.get("requires_fact", CATALOG["facts"][0]) in CATALOG["facts"]
        assert set(t.get("contributors", [])) <= set(SPECIALISTS)
        if t.get("diagram"):
            assert set(t["mermaid_kinds"]) <= sdlc.MERMAID_TYPES, t["type"]
    for c in CATALOG["change_categories"]:
        assert set(c["affects"]) <= set(types), c["id"]


def test_the_documentation_agent_is_not_the_only_owner() -> None:
    owners = {t["owner"] for t in CATALOG["types"]}
    assert {"django-architecture-agent", "django-model-agent", "django-api-agent", "django-testing-agent",
            "django-performance-agent", "django-security-agent", "django-documentation-agent"} <= owners


# ------------------------------------------------------------------------------ init, plan: missing docs

def test_init_detects_facts_and_is_idempotent(project: Path, capsys) -> None:
    assert run(project, "init", "--project", "shop", "--profile", "standard", capsys=capsys)[0] == 0
    first = registry(project)
    assert all(first["facts"].values()), first["facts"]
    assert run(project, "init", capsys=capsys)[1].startswith("docs/sdlc/registry.json already exists")
    assert registry(project) == first


def test_plan_detects_missing_documents_and_respects_profile_and_facts(project: Path, capsys) -> None:
    run(project, "init", "--profile", "minimal")
    _, out = run(project, "plan", "--json", capsys=capsys)
    minimal = {r["type"] for s in json.loads(out) for r in s["documents"]}
    assert {"US", "AC", "CFG", "CHG"} <= minimal and not {"BRD", "SAD", "HLD", "DFD"} & minimal
    data = registry(project)
    data["profile"] = "standard"
    data["facts"]["has_api"] = False
    data["not_applicable"] = [{"type": "RUN", "reason": "Single-developer internal tool"}]
    (project / "docs" / "sdlc" / "registry.json").write_text(json.dumps(data), encoding="utf-8")
    _, out = run(project, "plan", "--json", capsys=capsys)
    standard = {r["type"]: r for s in json.loads(out) for r in s["documents"]}
    assert {"SRS", "HLD", "DBD", "TPL"} <= set(standard)
    assert "API" not in standard, "no API fact: not applicable"
    assert "RUN" not in standard, "explicitly not applicable"
    assert "ADR" not in standard and "INC" not in standard, "on-demand types are never forced"
    assert all(r["action"] == "register-and-generate" for r in standard.values())


# ------------------------------------------------------------------------------ existing docs are consumed

def test_existing_documents_are_discovered_and_registered_without_rewriting(project: Path, capsys) -> None:
    run(project, "init")
    before = (project / "docs" / "srs.md").read_bytes()
    code, out = run(project, "check", capsys=capsys)
    assert code == 0 and "unregistered" in out and "docs/srs.md" in out and "legacy-notes.md" in out
    code, _ = run(project, "register", "--type", "SRS", "--id", "SRS-001", "--name", "SRS", "--path", "docs/srs.md",
                  "--owner", "django-documentation-agent")
    assert code == 0
    doc = entry(project, "SRS-001")
    assert doc["status"] == "draft" and doc["stage"] == "requirements" and doc["version"] == "0.1"
    assert (project / "docs" / "srs.md").read_bytes() == before, "registering never rewrites a document"
    _, out = run(project, "check", capsys=capsys)
    assert "docs/srs.md" not in out and "legacy-notes.md" in out


def test_registry_accurately_reflects_files(project: Path, capsys) -> None:
    run(project, "init")
    run(project, "register", "--type", "SRS", "--id", "SRS-001", "--name", "SRS", "--path", "docs/srs.md")
    run(project, "register", "--type", "HLD", "--name", "High level design")          # file does not exist yet
    assert entry(project, "HLD-001")["status"] == "missing"
    code, out = run(project, "check", "--json", capsys=capsys)
    assert code == 0 and json.loads(out)["status_counts"] == {"draft": 1, "missing": 1}
    # a registry that lies about files is an error
    data = registry(project)
    data["documents"][1]["status"] = "draft"
    (project / "docs" / "sdlc" / "registry.json").write_text(json.dumps(data), encoding="utf-8")
    assert "file-missing" in run(project, "check", capsys=capsys)[1]
    (project / "docs" / "architecture").mkdir(parents=True)
    (project / "docs" / "architecture" / "high-level-design.md").write_text("# HLD-001\n", encoding="utf-8")
    data["documents"][1]["status"] = "missing"
    (project / "docs" / "sdlc" / "registry.json").write_text(json.dumps(data), encoding="utf-8")
    assert "file-exists-but-missing" in run(project, "check", capsys=capsys)[1]


def test_registry_rejects_bad_references_unknown_types_and_duplicates(project: Path, capsys) -> None:
    run(project, "init")
    with pytest.raises(SystemExit):
        run(project, "register", "--type", "NOPE", "--name", "x")
    run(project, "register", "--type", "HLD", "--id", "HLD-001", "--name", "HLD")
    with pytest.raises(SystemExit):
        run(project, "register", "--type", "HLD", "--id", "HLD-001", "--name", "again")
    data = registry(project)
    data["documents"][0]["depends_on"] = ["SRS-404"]
    (project / "docs" / "sdlc" / "registry.json").write_text(json.dumps(data), encoding="utf-8")
    code, out = run(project, "check", capsys=capsys)
    assert code == 1 and "bad-reference" in out
    data["documents"][0]["responsible_agent"] = ""
    (project / "docs" / "sdlc" / "registry.json").write_text(json.dumps(data), encoding="utf-8")
    assert "missing fields: responsible_agent" in run(project, "check", capsys=capsys)[1]


# ------------------------------------------------------------------------------ staleness

def _api_spec(project: Path) -> None:
    (project / "docs" / "api").mkdir(parents=True, exist_ok=True)
    (project / "docs" / "api" / "orders.md").write_text("# API-001 Orders API\n`GET /api/orders/`\n", encoding="utf-8")
    run(project, "register", "--type", "API", "--id", "API-001", "--name", "Orders API", "--path", "docs/api/orders.md",
        "--source", "shop/views.py", "--source", "shop/serializers.py")


def test_stale_documents_are_identified_and_marked(project: Path, capsys) -> None:
    run(project, "init")
    _api_spec(project)
    assert "stale" not in codes(project)
    views = project / "shop" / "views.py"
    views.write_text(read(views) + "\n# new behaviour\n", encoding="utf-8")
    code, out = run(project, "check", capsys=capsys)
    assert code == 0 and "stale" in out and "shop/views.py changed" in out
    assert run(project, "check", "--strict", capsys=capsys)[0] == 1, "--strict turns warnings into failures"
    run(project, "check", "--mark-stale", capsys=capsys)
    assert entry(project, "API-001")["status"] == "stale"
    # refreshing the document re-stamps hashes and clears staleness
    run(project, "update", "API-001")
    assert entry(project, "API-001")["status"] == "draft" and entry(project, "API-001")["version"] == "0.2"
    assert "stale" not in codes(project)


def test_upstream_requirement_change_makes_dependents_stale(project: Path, capsys) -> None:
    run(project, "init")
    run(project, "register", "--type", "SRS", "--id", "SRS-001", "--name", "SRS", "--path", "docs/srs.md")
    (project / "docs" / "architecture").mkdir(parents=True)
    (project / "docs" / "architecture" / "hld.md").write_text("# HLD-001\n", encoding="utf-8")
    run(project, "register", "--type", "HLD", "--id", "HLD-001", "--name", "HLD", "--path", "docs/architecture/hld.md",
        "--depends-on", "SRS-001")
    assert "stale" not in run(project, "check", capsys=capsys)[1]
    run(project, "update", "SRS-001")                                      # requirements changed: SRS v0.2
    _, out = run(project, "check", capsys=capsys)
    assert "HLD-001" in out and "SRS-001 is now v0.2 (was v0.1)" in out


# ------------------------------------------------------------------------------ approved documents are protected

def test_approved_documents_cannot_be_silently_overwritten(project: Path, capsys) -> None:
    run(project, "init")
    run(project, "register", "--type", "SRS", "--id", "SRS-001", "--name", "SRS", "--path", "docs/srs.md")
    assert run(project, "approve", "SRS-001", "--by", "product-owner", capsys=capsys)[0] == 0
    doc = entry(project, "SRS-001")
    assert doc["status"] == "approved" and doc["version"] == "1.0" and doc["approved_by"] == "product-owner"
    # the tool refuses an in-place update ...
    code, _ = run(project, "update", "SRS-001", capsys=capsys)
    assert code == 1 and entry(project, "SRS-001")["version"] == "1.0"
    # ... and any edit that bypasses it is detected
    srs = project / "docs" / "srs.md"
    original = srs.read_text(encoding="utf-8")
    srs.write_text(original + "- REQ-3: silently added\n", encoding="utf-8")
    code, out = run(project, "check", capsys=capsys)
    assert code == 1 and "approved-modified" in out
    srs.write_text(original, encoding="utf-8")
    assert run(project, "check", capsys=capsys)[0] == 0


def test_approved_document_revision_goes_through_a_proposal(project: Path, capsys) -> None:
    run(project, "init")
    run(project, "register", "--type", "SRS", "--id", "SRS-001", "--name", "SRS", "--path", "docs/srs.md")
    run(project, "approve", "SRS-001", "--by", "product-owner")
    approved_text = (project / "docs" / "srs.md").read_text(encoding="utf-8")
    proposal = project / "docs" / "srs.proposed.md"
    proposal.write_text(approved_text + "- REQ-3: customers can cancel an order (SRS-001)\n", encoding="utf-8")
    assert run(project, "update", "SRS-001", "--propose", "docs/srs.proposed.md")[0] == 0
    assert (project / "docs" / "srs.md").read_text(encoding="utf-8") == approved_text
    code, out = run(project, "check", capsys=capsys)
    assert code == 0 and "srs.proposed.md" not in out, "a recorded proposal is not an unregistered document"
    run(project, "approve", "SRS-001", "--by", "product-owner")            # the user accepts the proposal
    assert "REQ-3" in (project / "docs" / "srs.md").read_text(encoding="utf-8") and not proposal.exists()
    assert entry(project, "SRS-001")["version"] == "2.0"
    assert run(project, "check", capsys=capsys)[0] == 0


def test_a_stale_document_cannot_be_approved(project: Path) -> None:
    run(project, "init")
    _api_spec(project)
    (project / "shop" / "views.py").write_text("# changed\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        sdlc.main(["--project-dir", str(project), "approve", "API-001", "--by", "lead"])


# ------------------------------------------------------------------------------ impact assessment

def _populate(project: Path) -> None:
    run(project, "init")
    for d, name in (("requirements", "srs.md"),):
        pass
    run(project, "register", "--type", "SRS", "--id", "SRS-001", "--name", "SRS", "--path", "docs/srs.md")
    for did, typ, path, text, src in (
        ("DBD-001", "DBD", "docs/design/database.md", "# DBD-001\n", ["shop/models.py"]),
        ("API-001", "API", "docs/api/orders.md", "# API-001\n", ["shop/views.py"]),
        ("LLD-001", "LLD", "docs/design/lld.md", "# LLD-001\n", []),
        ("CFG-001", "CFG", "docs/dev/config.md", "# CFG-001\n", ["config/settings.py"]),
        ("TPL-001", "TPL", "docs/testing/test-plan.md", "# TPL-001\n", []),
    ):
        (project / path).parent.mkdir(parents=True, exist_ok=True)
        (project / path).write_text(text, encoding="utf-8")
        args = ["register", "--type", typ, "--id", did, "--name", did, "--path", path]
        for s in src:
            args += ["--source", s]
        run(project, *args)


def test_impact_assessment_selects_only_affected_documents(project: Path, capsys) -> None:
    _populate(project)
    _, out = run(project, "impact", "--changed", "shop/models.py", "--json", capsys=capsys)
    result = json.loads(out)
    ids = {r["id"] for r in result["affected"]}
    assert ids == {"DBD-001", "LLD-001"}, "model change: Database Design and LLD, not API, config or tests"
    assert result["unaffected_count"] == 4
    assert {u["type"] for u in result["unregistered_types"]} >= {"ERD", "MIG"}
    _, out = run(project, "impact", "--changed", "shop/views.py", "--json", capsys=capsys)
    assert {r["id"] for r in json.loads(out)["affected"]} == {"API-001", "LLD-001"}
    _, out = run(project, "impact", "--changed", "config/settings.py", "requirements.txt", "--json", capsys=capsys)
    assert {r["id"] for r in json.loads(out)["affected"]} == {"CFG-001"}
    _, out = run(project, "impact", "--changed", "shop/tests/test_orders.py", "--json", capsys=capsys)
    assert {r["id"] for r in json.loads(out)["affected"]} == {"TPL-001"}
    _, out = run(project, "impact", "--changed", "Dockerfile", "--json", capsys=capsys)
    assert json.loads(out)["affected"] == []


def test_requirement_change_cascades_through_dependencies_and_flags_approved_docs(project: Path, capsys) -> None:
    _populate(project)
    (project / "docs" / "architecture").mkdir(parents=True)
    (project / "docs" / "architecture" / "hld.md").write_text("# HLD-001\n", encoding="utf-8")
    run(project, "register", "--type", "HLD", "--id", "HLD-001", "--name", "HLD", "--path", "docs/architecture/hld.md",
        "--depends-on", "SRS-001")
    run(project, "approve", "SRS-001", "--by", "owner")
    _, out = run(project, "impact", "--category", "requirements", "--json", capsys=capsys)
    result = json.loads(out)
    srs = next(r for r in result["affected"] if r["id"] == "SRS-001")
    assert srs["action"].startswith("propose-revision")
    hld = next(r for r in result["affected"] if r["id"] == "HLD-001")
    assert "depends on SRS-001" in hld["reasons"], "downstream design is reviewed when requirements change"
    assert {u["type"] for u in result["unregistered_types"]} >= {"US", "AC", "RTM"}


def test_impact_text_report_lists_actions(project: Path, capsys) -> None:
    _populate(project)
    code, out = run(project, "impact", "--changed", "shop/models.py", capsys=capsys)
    assert code == 0 and "DBD-001" in out and "update" in out and "docs/design/database.md" in out


# ------------------------------------------------------------------------------ Mermaid

GOOD = {
    "erd": ERD_OK,
    "flow": "flowchart TD\n    A[Client] --> B{Auth?}\n    B -->|yes| C[(DB)]\n    B -- no --> D((Reject))\n    subgraph svc\n      C\n    end\n",
    "seq": "sequenceDiagram\n    participant Client\n    participant API\n    Client->>API: GET /orders\n    activate API\n    API-->>Client: 200\n    deactivate API\n",
    "c4": 'C4Context\n    Person(user, "Customer")\n    System(shop, "Shop")\n    Rel(user, shop, "Uses")\n',
}
BAD = {
    "no-type": "A --> B\n",
    "brackets": "flowchart TD\n    A[Client --> B\n",
    "dangling": "flowchart TD\n    A -->\n",
    "end": "flowchart TD\n    A --> B\n    end\n",
    "style-ref": "flowchart TD\n    A --> B\n    style Z fill:#f00\n",
    "participant": "sequenceDiagram\n    participant Client\n    Client->>Server: hi\n",
    "alt": "sequenceDiagram\n    A->>B: x\n    alt ok\n    B-->>A: y\n",
    "er": "erDiagram\n    Order ||-- OrderLine contains\n",
    "er-attr": "erDiagram\n    Order {\n        id\n    }\n",
    "c4": 'C4Context\n    Person(user, "Customer")\n    Rel(user, ghost, "Uses")\n',
}


@pytest.mark.parametrize("name", sorted(GOOD))
def test_valid_mermaid_passes(name: str) -> None:
    assert sdlc.lint_mermaid(GOOD[name]) == [], name


@pytest.mark.parametrize("name", sorted(BAD))
def test_invalid_mermaid_is_reported(name: str) -> None:
    assert sdlc.lint_mermaid(BAD[name]), name


def test_diagram_type_must_match_the_registered_document_type() -> None:
    assert sdlc.lint_mermaid(GOOD["flow"], ["erDiagram"])


def _diagram(project: Path, text: str = ERD_OK) -> None:
    run(project, "init")
    (project / "docs" / "diagrams").mkdir(parents=True, exist_ok=True)
    (project / "docs" / "diagrams" / "erd.mmd").write_text(text, encoding="utf-8")
    run(project, "register", "--type", "ERD", "--id", "ERD-001", "--name", "erd", "--path", "docs/diagrams/erd.mmd",
        "--source", "shop/models.py")


def test_erd_is_validated_against_the_models_it_claims_to_describe(project: Path, capsys) -> None:
    _diagram(project)
    assert run(project, "check", capsys=capsys)[0] == 0
    _diagram_bad = ERD_OK + "    Customer ||--o{ Invoice : bills\n"
    (project / "docs" / "diagrams" / "erd.mmd").write_text(_diagram_bad, encoding="utf-8")
    code, out = run(project, "check", capsys=capsys)
    assert code == 1 and "diagram-misrepresents" in out and "Invoice" in out


def test_embedded_diagrams_are_linted_and_must_match_their_source(project: Path, capsys) -> None:
    _diagram(project)
    (project / "docs" / "design").mkdir(parents=True)
    doc = project / "docs" / "design" / "database.md"
    doc.write_text(f"# DBD-001 Database design\n\n<!-- mermaid-source: docs/diagrams/erd.mmd -->\n```mermaid\n{ERD_OK.strip()}\n```\n",
                   encoding="utf-8")
    run(project, "register", "--type", "DBD", "--id", "DBD-001", "--name", "db", "--path", "docs/design/database.md",
        "--related", "ERD-001")
    assert run(project, "check", capsys=capsys)[0] == 0
    doc.write_text(read(doc).replace("string status", "string state"), encoding="utf-8")
    code, out = run(project, "check", capsys=capsys)
    assert code == 1 and "diagram-drift" in out
    doc.write_text(read(doc).replace("```mermaid\nerDiagram", "```mermaid\nnotADiagram"), encoding="utf-8")
    assert "mermaid" in run(project, "check", capsys=capsys)[1]


def test_mermaid_command_validates_files(project: Path, capsys) -> None:
    good, bad = project / "good.mmd", project / "bad.mmd"
    good.write_text(GOOD["seq"], encoding="utf-8")
    bad.write_text(BAD["participant"], encoding="utf-8")
    assert run(project, "mermaid", str(good), capsys=capsys)[0] == 0
    code, out = run(project, "mermaid", str(bad), capsys=capsys)
    assert code == 1 and "undeclared participant" in out


# ------------------------------------------------------------------------------ incremental workflow

def test_incremental_workflow_updates_only_affected_documents(project: Path, capsys) -> None:
    _populate(project)
    stamps = {d["id"]: (d["version"], d["last_updated"]) for d in registry(project)["documents"]}
    models = project / "shop" / "models.py"
    models.write_text(read(models) + "\n\nclass Coupon(models.Model):\n    code = models.CharField(max_length=20)\n", encoding="utf-8")
    _, out = run(project, "check", capsys=capsys)
    assert "DBD-001" in out and "API-001" not in out and "TPL-001" not in out
    _, out = run(project, "impact", "--git" if False else "--changed", "shop/models.py", "--json", capsys=capsys)
    for r in json.loads(out)["affected"]:
        if r["id"] != "LLD-001":
            run(project, "update", r["id"])
    after = {d["id"]: (d["version"], d["last_updated"]) for d in registry(project)["documents"]}
    assert after["DBD-001"][0] == "0.2"
    assert {i for i in stamps if stamps[i] != after[i]} == {"DBD-001"}, "unrelated documents are not regenerated"
    assert "DBD-001" not in run(project, "check", capsys=capsys)[1]


# ------------------------------------------------------------------------------ hand-written registries (agent mode)

def _hand_written(project: Path, **overrides) -> None:
    """What an agent without a shell writes: plain-path sources, no hashes."""
    (project / "docs" / "sdlc").mkdir(parents=True, exist_ok=True)
    (project / "docs" / "design").mkdir(parents=True, exist_ok=True)
    (project / "docs" / "design" / "database.md").write_text("# DBD-001 Database design\n", encoding="utf-8")
    doc = {"id": "DBD-001", "name": "Database design", "type": "DBD", "stage": "detailed-design",
           "path": "docs/design/database.md", "status": "draft", "version": "0.1", "related": [], "depends_on": [],
           "sources": ["shop/models.py"], "last_updated": "2999-01-01T00:00:00+00:00",
           "responsible_agent": "django-model-agent"}
    doc.update(overrides)
    registry_data = {"schema_version": "1.0", "project": "shop", "profile": "standard", "docs_root": "docs",
                     "facts": {}, "not_applicable": [], "documents": [doc]}
    (project / "docs" / "sdlc" / "registry.json").write_text(json.dumps(registry_data), encoding="utf-8")


def test_hand_written_registry_is_valid_and_staleness_uses_timestamps(project: Path) -> None:
    _hand_written(project)
    assert "stale" not in codes(project), "source older than last_updated: current"
    _hand_written(project, last_updated="2000-01-01T00:00:00+00:00")
    assert "stale" in codes(project), "source newer than last_updated: stale"


def test_approval_without_a_seal_is_reported(project: Path) -> None:
    _hand_written(project, status="approved", approved_by="owner", approved_at="2999-01-01T00:00:00+00:00")
    assert "approval-unsealed" in codes(project)
    _hand_written(project, status="approved")
    assert "approval-record" in codes(project)
