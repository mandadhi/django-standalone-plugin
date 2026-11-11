"""CANONICAL-MANIFEST.json: every file is accounted for, hashes match, adaptations are declared."""

from __future__ import annotations

import hashlib
import json
import re

from conftest import ROOT, all_files, read

MANIFEST = json.loads((ROOT / "CANONICAL-MANIFEST.json").read_text(encoding="utf-8"))


def sha(path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_every_file_is_listed_and_nothing_else() -> None:
    listed = {e["path"] for e in MANIFEST["files"]}
    actual = {p.relative_to(ROOT).as_posix() for p in all_files()
              if p.name != "CANONICAL-MANIFEST.json" and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts}
    assert listed == actual, (sorted(listed - actual)[:5], sorted(actual - listed)[:5])


def test_recorded_hashes_match_the_files() -> None:
    bad = [e["path"] for e in MANIFEST["files"] if sha(ROOT / e["path"]) != e["sha256"]]
    assert not bad, f"changed without updating CANONICAL-MANIFEST.json: {bad[:10]}"


def test_unadapted_canonical_files_equal_their_source_hash() -> None:
    for e in MANIFEST["files"]:
        if e["origin"] != "canonical":
            continue
        if e["adaptations"]:
            assert e["sha256"] != e["source_sha256"] and not e["identical"], e["path"]
        else:
            assert e["sha256"] == e["source_sha256"] and e["identical"], e["path"]


def test_adaptations_are_declared_with_a_reason_and_files() -> None:
    declared = {a["id"]: a for a in MANIFEST["adaptations"]}
    assert all(a["reason"].strip() and a["files"] for a in declared.values())
    used = {i for e in MANIFEST["files"] for i in e.get("adaptations", [])}
    assert used <= set(declared), used - set(declared)
    for e in MANIFEST["files"]:
        for aid in e.get("adaptations", []):
            assert e["path"] in declared[aid]["files"], (e["path"], aid)


def test_the_security_critical_canonical_files_are_unchanged_or_minimally_adapted() -> None:
    by_path = {e["path"]: e for e in MANIFEST["files"]}
    assert by_path["hooks/shell_syntax.py"]["identical"] is True
    assert by_path["hooks/hooks.json"]["identical"] is True
    for path in (f"agents/{a}.md" for a in ("django-project-analyzer", "django-code-review-agent")):
        assert set(by_path[path]["adaptations"]) <= {"AD-01", "AD-02"}


def test_manifest_records_exclusions_and_origin() -> None:
    assert re.fullmatch(r"[0-9a-f]{40}", MANIFEST["source_repository_commit"])
    text = " ".join(MANIFEST["excluded_harness_components"])
    for name in ("core/", "harness_bootstrap/", "setup-harness", "agent-task.prompt.md"):
        assert name in text
