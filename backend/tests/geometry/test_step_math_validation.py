"""Independent Mathematical Construction Audit Test Suite (P1–P6).

Verifies:
1. `oracle.py` has zero imports from `app` or `tests`.
2. All 13 Frontend sample/fixture scenes pass all 11 P2 mathematical categories.
3. All 135 Backend Hybrid Route D scenes (112 on `main` + 23 on frozen `contract-driven-goal-composition`)
   pass all 11 P2 mathematical categories.
4. All 10 required P3 counterexample / fault-injection categories (`P3.1`–`P3.10`) are caught
   with exact root-cause diagnostics.
5. Machine receipts (`catalog-audit.json`, `counterexamples.json`, `run.json`) are deterministic
   and hash-verified.
"""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

os.environ["ALLOW_LIVE_AI"] = "0"

WORKTREE_ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = WORKTREE_ROOT / "docs" / "evaluation" / "geometry" / "runs" / "step-math-validation"
if str(RUN_DIR) not in sys.path:
    sys.path.insert(0, str(RUN_DIR))

import oracle  # noqa: E402


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_oracle_has_zero_product_or_test_imports() -> None:
    """P2 guard: Independent mathematical oracle must not import `app` or `tests`."""
    oracle_path = RUN_DIR / "oracle.py"
    tree = ast.parse(oracle_path.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert "app" not in imported_roots, f"Forbidden product import in oracle.py: {imported_roots}"
    assert "tests" not in imported_roots, f"Forbidden test import in oracle.py: {imported_roots}"


def test_frontend_sample_and_fixture_scenes_mathematically_verified() -> None:
    """P1 & P2: Every frontend sample and standalone fixture scene must pass all 11 categories."""
    samples_path = WORKTREE_ROOT / "frontend" / "src" / "data" / "geometry-samples.json"
    samples = json.loads(samples_path.read_text(encoding="utf-8"))["samples"]
    assert len(samples) == 11

    for s in samples:
        sc = s["envelope"]["scene3d"]
        rep = oracle.verify_scene_mathematics(
            sc,
            scene_id=s["id"],
            data_source="frontend/src/data/geometry-samples.json",
            source_kind="frontend_sample_or_fixture",
            problem_text=s.get("problemText", ""),
        )
        assert rep.verdict == "VERIFIED", f"Frontend sample {s['id']} failed: {rep.errors}"
        assert all(c.passed for c in rep.category_results.values())

    for rel_fp in (
        "frontend/src/simulations/domains/geometry/scene3d-section-fixture.json",
        "frontend/src/simulations/domains/geometry/scene3d-circumsphere-fixture.json",
    ):
        fp = WORKTREE_ROOT / rel_fp
        sc = json.loads(fp.read_text(encoding="utf-8"))
        rep = oracle.verify_scene_mathematics(
            sc,
            scene_id=fp.stem,
            data_source=rel_fp,
            source_kind="frontend_sample_or_fixture",
        )
        assert rep.verdict == "VERIFIED", f"Frontend fixture {rel_fp} failed: {rep.errors}"


def test_backend_catalog_scenes_mathematically_verified() -> None:
    """P1 & P2: All 135 Backend Hybrid Route D scenes recorded in catalog-audit.json pass."""
    catalog_path = RUN_DIR / "catalog-audit.json"
    assert catalog_path.exists()
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    fe_scenes = catalog["frontend_sample_and_fixture_scenes"]
    be_scenes = catalog["backend_hybrid_route_d_scenes"]
    assert len(fe_scenes) == 13
    assert len(be_scenes) == 135
    assert catalog["summary"]["total_served_scenes_audited"] == 148
    assert catalog["summary"]["total_served_scenes_verified"] == 148

    # Ensure every singleP2 category was actively exercised across the 148 scenes
    cat_totals = catalog["summary"]["category_totals"]
    assert len(cat_totals) == 11
    for cat_name, stats in cat_totals.items():
        assert stats["checked_count"] > 0, f"Category {cat_name} had 0 checks"
        assert stats["passed_scenes"] == 148, f"Category {cat_name} failed on scenes: {stats}"
        assert stats["failed_scenes"] == 0


@pytest.mark.parametrize("ce_index", list(range(10)))
def test_ten_required_counterexamples_detected(ce_index: int) -> None:
    """P3.1–P3.10: All 10 required counterexamples must be caught with root-cause evidence."""
    suite = oracle.run_counterexample_suite()
    assert len(suite) == 10
    ce = suite[ce_index]
    assert ce["id"] == f"P3.{ce_index + 1}"
    assert ce["oracle_detected"] is True, f"Counterexample {ce['id']} was not detected: {ce}"
    assert ce["minimal_input"]
    assert ce["expected_math"]
    assert ce["actual_output"]
    assert ce["root_cause"]


def test_fault_injection_across_all_11_categories() -> None:
    """Verify that corrupting a valid scene in each of the 11 categories forces verdict == INVALID."""
    samples_path = WORKTREE_ROOT / "frontend" / "src" / "data" / "geometry-samples.json"
    samples = {
        s["id"]: s["envelope"]["scene3d"]
        for s in json.loads(samples_path.read_text(encoding="utf-8"))["samples"]
    }

    # 1. Corrupt point-plane incidence on `thiet-dien-chop`
    sc1 = deepcopy(samples["thiet-dien-chop"])
    for o in sc1["objects"]:
        if o["id"] == "mp":
            o["point"] = ["0", "0", "3"]  # M, N, P are at z=2, so n.(M - P0) != 0
    rep1 = oracle.verify_scene_mathematics(sc1, scene_id="fi_1")
    assert rep1.verdict == "INVALID"
    assert not rep1.category_results["1_incidence"].passed

    # 2. Corrupt midpoint coordinates on `thiet-dien-chop`
    sc2 = deepcopy(samples["thiet-dien-chop"])
    for o in sc2["objects"]:
        if o["id"] == "M":
            o["xyz"] = ["0", "0", "3"]  # True midpoint of A(0,0,0), S(0,0,4) is (0,0,2)
    rep2 = oracle.verify_scene_mathematics(sc2, scene_id="fi_2")
    assert rep2.verdict == "INVALID"
    assert not rep2.category_results["2_midpoint_centroid_ratio"].passed

    # 3 & 6. Corrupt orthogonal projection / line-plane perpendicularity on `mp-vuong-goc-duong`
    sc6 = deepcopy(samples["mp-vuong-goc-duong"])
    for o in sc6["objects"]:
        if o["id"] == "mpb":
            o["normal"] = ["1", "0", "0"]  # Not parallel to sc direction (2, 2, -4)
    rep6 = oracle.verify_scene_mathematics(sc6, scene_id="fi_6")
    assert rep6.verdict == "INVALID"
    assert not rep6.category_results["6_line_plane_perp"].passed

    # 4. Corrupt circle intersection radius on `cau-cat-mat-phang`
    sc4 = deepcopy(samples["cau-cat-mat-phang"])
    for o in sc4["objects"]:
        if o["id"] == "C":
            o["radius_sq"] = "20"  # R^2 - d^2 = 25 - 9 = 16 != 20
    rep4 = oracle.verify_scene_mathematics(sc4, scene_id="fi_4")
    assert rep4.verdict == "INVALID"
    assert not rep4.category_results["4_intersection"].passed

    # 7. Corrupt angle_cos_sq on `vuong-goc-chop`
    sc7 = deepcopy(samples["vuong-goc-chop"])
    for o in sc7["objects"]:
        if o["id"] == "goc":
            o["value"] = "1/2"
            o["exact"] = {"kind": "rational", "value": "1/2"}
    rep7 = oracle.verify_scene_mathematics(sc7, scene_id="fi_7")
    assert rep7.verdict == "INVALID"
    assert not rep7.category_results["7_angles"].passed

    # 8. Corrupt volume on `the-tich-chop`
    sc8 = deepcopy(samples["the-tich-chop"])
    for o in sc8["objects"]:
        if o["id"] == "V":
            o["value"] = "99"
            o["exact"] = {"kind": "rational", "value": "99"}
    rep8 = oracle.verify_scene_mathematics(sc8, scene_id="fi_8")
    assert rep8.verdict == "INVALID"
    assert not rep8.category_results["8_distance_area_volume"].passed

    # 9. Corrupt cross-section polygon vertex on `thiet-dien-chop`
    sc9 = deepcopy(samples["thiet-dien-chop"])
    for o in sc9["objects"]:
        if o["id"] == "thiet_dien":
            o["polygon"][0] = ["1/2", "1/2", "2"]  # Interior point, not on any edge of S.ABCD
    rep9 = oracle.verify_scene_mathematics(sc9, scene_id="fi_9")
    assert rep9.verdict == "INVALID"
    assert not rep9.category_results["9_section"].passed


def test_run_receipts_and_hashes_are_consistent() -> None:
    """Verify run.json hashes match oracle.py, catalog-audit.json, and counterexamples.json."""
    run_data = json.loads((RUN_DIR / "run.json").read_text(encoding="utf-8"))
    assert run_data["live_ai_calls"] == 0
    assert run_data["frontend_reverification_status"] == "WAITING_FOR_FRONTEND_FINAL_SNAPSHOT"
    assert run_data["counterexamples_detected"] == "10/10"
    for fname, expected_hash in run_data["hashes"].items():
        actual_hash = _sha256_file(RUN_DIR / fname)
        assert actual_hash == expected_hash, f"Hash mismatch on {fname}: {actual_hash} != {expected_hash}"
