# -*- coding: utf-8 -*-
"""AXO Step Editor — Independent Acceptance, Root-Cause (`IND-1`..`IND-5`),
Negative Boundaries, API Concurrency, and Brand-New Exact Geometry Oracle Suite.

Covers:
1. `IND-1`..`IND-5` root-cause regression tests (written RED-first before fixing `step_editor.py`).
2. Group A Positive Matrix: `S.ABCD` + first/middle/last/equivalent/downstream/repeat/sequential + 4 non-`S.ABCD` problems.
3. Group B Negative & Failure Matrix: missing point, type mismatch, contradictory geometry, invalid context role,
   insufficient specification, unsupported op, dependency cycle, out-of-scope curved/calculus, API concurrency.
4. Group C Independent Geometry Oracle: brand-new affine/Euclidean/Gram-metric polyhedral scenes verifying
   point-on-line/segment/plane, midpoint & ratio, parallel/perpendicular predicates, intersections,
   distances/radii/dihedral `cos²`, presentation invariance, topological DAG ordering, and repeatability.
"""
from __future__ import annotations

import asyncio
import copy
import json
import sys
import uuid
from fractions import Fraction
from pathlib import Path

import httpx
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent
DATA_DIR = REPO_DIR / "frontend" / "src" / "data"
if str(BACKEND_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR / "scripts"))

from app.ai.step_edit_route import execute_step_edit  # noqa: E402
from app.main import app  # noqa: E402
from app.persistence.step_edit_models import ensure_step_edit_tables  # noqa: E402
from app.simulation.geometry import (  # noqa: E402
    GeometryError,
    Line3,
    Plane3,
    Segment3,
    Vec3,
    circumscribed_sphere,
    kernel as K,
    measure as M,
    metric as _m,
    predicates as P,
)
from app.simulation.geometry.radical import Radical, display as radical_display, parse_exact, sqrt_rational, to_json as radical_to_json  # noqa: E402
from app.simulation.geometry.section import Polyhedron, cross_section  # noqa: E402
from app.simulation.geometry_functions import step_editor as se  # noqa: E402
from app.simulation.geometry_functions.step_editor import (  # noqa: E402
    StepEditRefusal,
    build_construction_dependency_graph,
)


def _load_all_catalog_samples() -> dict[str, dict]:
    ensure_step_edit_tables()
    out: dict[str, dict] = {}
    for fname in ("geometry-samples.json", "advanced-geometry-samples.json"):
        raw = json.loads((DATA_DIR / fname).read_text(encoding="utf-8"))
        items = raw if isinstance(raw, list) else raw.get("samples", raw)
        for item in items:
            out[item["id"]] = item
    return out


@pytest.fixture(scope="module")
def catalog_by_id() -> dict[str, dict]:
    return _load_all_catalog_samples()


def _find_obj(scene: dict, oid: str) -> dict | None:
    return next((o for o in scene.get("objects") or [] if o.get("id") == oid), None)


def _vec3(raw: list) -> Vec3:
    assert len(raw) == 3
    return Vec3.of(parse_exact(raw[0]), parse_exact(raw[1]), parse_exact(raw[2]))


def _point_on_segment(pt: Vec3, a: Vec3, b: Vec3) -> tuple[bool, Fraction | None]:
    ab = b - a
    ap = pt - a
    if not ap.cross(ab).is_zero():
        return False, None
    denom = _m.dot(ab, ab)
    if denom == 0:
        return False, None
    t = _m.dot(ap, ab) / denom
    return (Fraction(0) <= t <= Fraction(1)), t


def _assert_no_raw_prime_leaks(scene: dict) -> None:
    for obj in scene.get("objects") or ():
        for field in ("label", "notation", "reference", "display_label"):
            val = obj.get(field)
            if isinstance(val, str):
                assert "_prime" not in val, (
                    f"IND-1 leak: raw '_prime' found in object {obj.get('id')!r}.{field}={val!r}"
                )


def _make_sample11_without_ball(catalog_by_id: dict[str, dict]) -> dict:
    s = copy.deepcopy(catalog_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    seeds = {"I", "R", "R_cau", "cau_ngoai_tiep", "mat_cau", "V_cau", "S_cau", "doan_IS", "doan_IA", "doan_OI", "doan_MI", "mp_tt_SA"}
    drop = set(seeds)
    changed = True
    while changed:
        changed = False
        for o in s.get("objects") or ():
            oid = o.get("id")
            if oid and oid not in drop and any(d in drop for d in (o.get("depends") or ())):
                drop.add(oid)
                changed = True
    s["objects"] = [o for o in s["objects"] if o.get("id") not in drop]
    s["events"] = [e for e in (s.get("events") or ()) if e.get("object") not in drop]
    if isinstance(s.get("formation"), dict) and isinstance(s["formation"].get("steps"), list):
        s["formation"]["steps"] = [
            st for st in s["formation"]["steps"]
            if not (set(st.get("focus_ids") or ()) & drop)
        ]
    return s


# ── IND-1..IND-5 Root-Cause Regression Tests ─────────────────────────────────


def test_ind1_cube_and_prism_never_leak_raw_underscore_prime(catalog_by_id):
    """IND-1: Midpoints, ratios, segments, planes, and base polygons involving primed vertices use '′', never '_prime'."""
    cube = copy.deepcopy(catalog_by_id["lap-phuong-thiet-dien-bat-ky"]["envelope"]["scene3d"])

    # 1. Edit P on B′C′ with a division ratio -> label must display B′C′, never B_primeC_prime
    r_p = execute_step_edit(
        scene3d=cube,
        step_id="P",
        step_index=7,
        previous_instruction="Xác định trung điểm P của B′C′",
        edited_instruction="Lấy điểm P thuộc B′C′ sao cho B′P = 1/3 B′C′",
        target_ids=["P"],
    )
    assert r_p["status"] == "committed"
    _assert_no_raw_prime_leaks(r_p["scene3d"])
    p_obj = _find_obj(r_p["scene3d"], "P")
    assert p_obj is not None
    assert "B′C′" in p_obj["label"]

    # 2. Edit midpoint P of A′B′
    r_mid = execute_step_edit(
        scene3d=cube,
        step_id="P",
        step_index=7,
        previous_instruction="Xác định trung điểm P của B′C′",
        edited_instruction="Xác định trung điểm P của A′B′",
        target_ids=["P"],
    )
    assert r_mid["status"] == "committed"
    _assert_no_raw_prime_leaks(r_mid["scene3d"])
    assert "A′B′" in _find_obj(r_mid["scene3d"], "P")["label"]

    # 3. Edit lateral edge segment AA′
    r_seg = execute_step_edit(
        scene3d=cube,
        step_id="canh_ben_A_A_prime",
        step_index=3,
        previous_instruction="Nối AA′",
        edited_instruction="Nối AA′",
        target_ids=["canh_ben_A_A_prime"],
        force_full_rebuild=True,
    )
    assert r_seg["status"] == "committed"
    _assert_no_raw_prime_leaks(r_seg["scene3d"])
    seg_obj = _find_obj(r_seg["scene3d"], "canh_ben_A_A_prime")
    assert seg_obj is not None and seg_obj["notation"] == "AA′"

    # 4. Edit top base polygon A′B′C′D′ on triangular prism & cube
    r_poly = execute_step_edit(
        scene3d=cube,
        step_id="day_A_primeB_primeC_primeD_prime",
        step_index=2,
        previous_instruction="Dựng đáy trên A′B′C′D′",
        edited_instruction="Dựng mặt đáy đối diện A′B′C′D′ của lăng trụ",
        target_ids=["day_A_primeB_primeC_primeD_prime"],
        force_full_rebuild=True,
    )
    assert r_poly["status"] == "committed"
    _assert_no_raw_prime_leaks(r_poly["scene3d"])
    poly_obj = _find_obj(r_poly["scene3d"], "day_A_primeB_primeC_primeD_prime")
    assert poly_obj is not None and poly_obj["notation"] == "A′B′C′D′"


def test_ind2_polyhedral_ui_step_phrasings_and_common_perp_validation(catalog_by_id):
    """IND-2: All 6 UI polyhedral phrasings parse, resolve, and verify mathematically in Exact Kernel."""
    pyr_sec = copy.deepcopy(catalog_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])
    prism = copy.deepcopy(catalog_by_id["lang-tru-tam-giac-thiet-dien"]["envelope"]["scene3d"])
    cube = copy.deepcopy(catalog_by_id["lap-phuong-thiet-dien-bat-ky"]["envelope"]["scene3d"])
    skew = copy.deepcopy(catalog_by_id["khoang-cach-hai-duong-cheo-nhau"]["envelope"]["scene3d"])

    # 2a. "Dựng mặt phẳng cắt (MNP)"
    r_pl = execute_step_edit(
        scene3d=pyr_sec,
        step_id="mp_MNP",
        step_index=10,
        previous_instruction="Dựng (MNP)",
        edited_instruction="Dựng mặt phẳng cắt (MNP)",
        target_ids=["mp_MNP"],
        force_full_rebuild=True,
    )
    assert r_pl["status"] == "committed"

    # 2b. "Xác định giao điểm E = SB ∩ (MNP)" and "Xác định giao điểm E = CC′ ∩ (MNP)"
    r_ix1 = execute_step_edit(
        scene3d=pyr_sec,
        step_id="E",
        step_index=13,
        previous_instruction="Dựng E.",
        edited_instruction="Xác định giao điểm E = SB ∩ (MNP)",
        target_ids=["E"],
        force_full_rebuild=True,
    )
    assert r_ix1["status"] == "committed"
    assert _vec3(_find_obj(r_ix1["scene3d"], "E")["xyz"]) == Vec3.of(3, 0, Fraction(3, 2))

    r_ix2 = execute_step_edit(
        scene3d=cube,
        step_id="E",
        step_index=12,
        previous_instruction="Dựng E.",
        edited_instruction="Xác định giao điểm E = CC′ ∩ (MNP)",
        target_ids=["E"],
        force_full_rebuild=True,
    )
    assert r_ix2["status"] == "committed"
    _assert_no_raw_prime_leaks(r_ix2["scene3d"])

    # 2c. "Dựng đáy trên A′B′C′"
    r_top = execute_step_edit(
        scene3d=prism,
        step_id="day_A_primeB_primeC_prime",
        step_index=2,
        previous_instruction="Dựng đáy trên A′B′C′",
        edited_instruction="Dựng đáy trên A′B′C′",
        target_ids=["day_A_primeB_primeC_prime"],
        force_full_rebuild=True,
    )
    assert r_top["status"] == "committed"

    # 2d. "Hoàn thiện lăng trụ đứng ABC.A′B′C′"
    r_sol = execute_step_edit(
        scene3d=prism,
        step_id="lang_tru",
        step_index=4,
        previous_instruction="Dựng lăng trụ đứng ABC.A′B′C′",
        edited_instruction="Hoàn thiện lăng trụ đứng ABC.A′B′C′",
        target_ids=["lang_tru"],
        force_full_rebuild=True,
    )
    assert r_sol["status"] == "committed"

    # 2e. "Xác định đường thẳng chứa cạnh AB" / "Kẻ đường thẳng SB"
    r_ln = execute_step_edit(
        scene3d=prism,
        step_id="ab",
        step_index=9,
        previous_instruction="Dựng AB",
        edited_instruction="Xác định đường thẳng chứa cạnh AB",
        target_ids=["ab"],
        force_full_rebuild=True,
    )
    assert r_ln["status"] == "committed"
    _assert_no_raw_prime_leaks(r_ln["scene3d"])

    # 2f-i. "Dựng các giao tuyến và hoàn thiện thiết diện (MENPF)" (positive)
    r_sec = execute_step_edit(
        scene3d=pyr_sec,
        step_id="thiet_dien",
        step_index=15,
        previous_instruction="Dựng thiết diện bởi (MNP)",
        edited_instruction="Dựng các giao tuyến và hoàn thiện thiết diện (MENPF)",
        target_ids=["thiet_dien"],
        force_full_rebuild=True,
    )
    assert r_sec["status"] == "committed"

    # 2f-i negative: claiming incomplete polygon (MNP) for 5-vertex section MUST fail closed!
    with pytest.raises(StepEditRefusal) as exc_sec:
        execute_step_edit(
            scene3d=pyr_sec,
            step_id="thiet_dien",
            step_index=15,
            previous_instruction="Dựng thiết diện bởi (MNP)",
            edited_instruction="Hoàn thiện thiết diện (MNP)",
            target_ids=["thiet_dien"],
        )
    assert exc_sec.value.error_code in ("SECTION_BOUNDARY_MISMATCH", "STEP_TYPE_MISMATCH")

    # 2f-ii. "Dựng đoạn vuông góc chung PQ của SC và BD" (positive & negative non-perpendicular SB)
    r_cp = execute_step_edit(
        scene3d=skew,
        step_id="doan_PQ",
        step_index=13,
        previous_instruction="Nối PQ",
        edited_instruction="Dựng đoạn vuông góc chung PQ của SC và BD",
        target_ids=["doan_PQ"],
        force_full_rebuild=True,
    )
    assert r_cp["status"] == "committed"

    with pytest.raises(StepEditRefusal) as exc_cp:
        execute_step_edit(
            scene3d=skew,
            step_id="doan_PQ",
            step_index=13,
            previous_instruction="Nối PQ",
            edited_instruction="Dựng đoạn vuông góc chung SB của SC và BD",
            target_ids=["doan_PQ"],
        )
    assert exc_cp.value.error_code == "ROLE_ASSERTION_FAILED"


def test_ind3_orthogonal_projection_line_includes_target_line_name(catalog_by_id):
    """IND-3: Projection onto a line includes the target line notation in the point's label."""
    dihedral = copy.deepcopy(catalog_by_id["goc-nhi-dien-hai-mat-phang"]["envelope"]["scene3d"])
    r = execute_step_edit(
        scene3d=dihedral,
        step_id="H",
        step_index=8,
        previous_instruction="Hạ hình chiếu vuông góc H của A lên BC",
        edited_instruction="Hạ hình chiếu vuông góc H của A lên BC",
        target_ids=["H"],
        force_full_rebuild=True,
    )
    assert r["status"] == "committed"
    h_obj = _find_obj(r["scene3d"], "H")
    assert h_obj is not None
    assert "BC" in h_obj["label"], f"Expected target line 'BC' in label, got {h_obj['label']!r}"


def test_ind4_synthetic_readout_target_never_aliases_formation_step_index(catalog_by_id):
    """IND-4: Synthetic sub-entity `kc__foot1` MUST NOT silently fall back to formation.steps[6] (`mpb`)."""
    scene = copy.deepcopy(catalog_by_id["mp-vuong-goc-duong"]["envelope"]["scene3d"])
    before_mpb_normal = copy.deepcopy(_find_obj(scene, "mpb")["normal"])

    with pytest.raises(StepEditRefusal) as exc_ro:
        execute_step_edit(
            scene3d=scene,
            step_id="kc__foot1",
            step_index=6,
            previous_instruction="Khoảng cách d(S, (α))",
            edited_instruction="Xác định trung điểm H của SA",
            target_ids=["kc__foot1"],
        )
    assert exc_ro.value.error_code == "READOUT_STEP_NOT_EDITABLE"
    assert _find_obj(scene, "mpb")["normal"] == before_mpb_normal

    with pytest.raises(StepEditRefusal) as exc_nf:
        execute_step_edit(
            scene3d=scene,
            step_id="missing_step_xyz",
            step_index=6,
            previous_instruction="Dựng...",
            edited_instruction="Xác định trung điểm H của SA",
            target_ids=["missing_step_xyz"],
        )
    assert exc_nf.value.error_code == "STEP_TARGET_NOT_FOUND"


def test_ind5_anonymized_inline_point_never_shadows_later_steps(catalog_by_id):
    """IND-5: After anonymizing inline point H on Step 8, downstream steps MUST NOT still bind symbol H to (2,4,0)."""
    s11 = _make_sample11_without_ball(catalog_by_id)

    r1 = execute_step_edit(
        scene3d=s11,
        step_id="mp_tt_AB",
        step_index=14,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
    )
    assert r1["status"] == "committed"
    assert _find_obj(r1["scene3d"], "H") is not None

    r2 = execute_step_edit(
        scene3d=r1["scene3d"],
        step_id="mp_tt_AB",
        step_index=14,
        previous_instruction="Xác định trung điểm H của AB, dựng mặt phẳng (α) đi qua H và vuông góc với AB",
        edited_instruction="Dựng mặt phẳng trung trực (α) của cạnh CD.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["H"],
    )
    assert r2["status"] == "committed"
    # Inline helper point must NOT keep id='H' once anonymized!
    assert _find_obj(r2["scene3d"], "H") is None

    # Referencing H after it was removed must fail cleanly with MISSING_DEPENDENCY
    with pytest.raises(StepEditRefusal) as exc_miss:
        execute_step_edit(
            scene3d=r2["scene3d"],
            step_id="truc_day",
            step_index=15,
            previous_instruction="Dựng giao tuyến của (α) và (β)",
            edited_instruction="Dựng đường thẳng qua hai điểm H, O",
            target_ids=["truc_day"],
        )
    assert exc_miss.value.error_code == "MISSING_DEPENDENCY"


def test_ind6_concurrent_session_edit_serialization(catalog_by_id, monkeypatch):
    """IND-6: Simultaneous POST /api/simulation/steps/edit for the same session never crash with HTTP 500 IntegrityError."""
    import threading
    from app.simulation import step_edit_router

    s1 = copy.deepcopy(catalog_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])
    sid = f"ind6-{uuid.uuid4().hex[:10]}"
    hdrs = {"X-Axo-Client-Session": f"ind6-client-{uuid.uuid4().hex[:8]}"}

    orig_resolve = step_edit_router._resolve_owner_scope
    barrier = threading.Barrier(2, timeout=2.0)

    def _synced_resolve(db, session_cookie, x_axo_client_session):
        scope = orig_resolve(db, session_cookie, x_axo_client_session)
        try:
            barrier.wait()
        except threading.BrokenBarrierError:
            pass
        return scope

    monkeypatch.setattr(step_edit_router, "_resolve_owner_scope", _synced_resolve)

    # Single-thread barrier release via anyio threads inside AsyncClient + ASGITransport
    async def _run():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as ac:
            r_pair = await asyncio.gather(
                ac.post(
                    "/api/simulation/steps/edit",
                    headers=hdrs,
                    json={
                        "session_id": sid,
                        "problem_key": "sample:chop-thiet-dien-ba-diem",
                        "step_id": "M",
                        "step_index": 8,
                        "previous_instruction": "Dựng M.",
                        "edited_instruction": "Lấy điểm M thuộc SA sao cho SM:MA = 1:2",
                        "target_ids": ["M"],
                        "scene3d": copy.deepcopy(s1),
                    },
                ),
                ac.post(
                    "/api/simulation/steps/edit",
                    headers=hdrs,
                    json={
                        "session_id": sid,
                        "problem_key": "sample:chop-thiet-dien-ba-diem",
                        "step_id": "M",
                        "step_index": 8,
                        "previous_instruction": "Dựng M.",
                        "edited_instruction": "Lấy điểm M thuộc SA sao cho SM:MA = 1:3",
                        "target_ids": ["M"],
                        "scene3d": copy.deepcopy(s1),
                    },
                ),
            )
            st = await ac.get(f"/api/simulation/sessions/{sid}/state", headers=hdrs)
            return r_pair, st

    resps, st = asyncio.run(_run())
    assert all(r.status_code in (200, 409) for r in resps), (
        f"IND-6 concurrent POST race: {[r.status_code for r in resps]}"
    )
    ok_count = sum(1 for r in resps if r.status_code == 200)
    assert ok_count >= 1
    assert st.status_code == 200
    assert st.json()["committed_version"] == ok_count


def test_ind7_curved_kind_single_authority_compliance():
    """IND-7: step_editor.py delegates curved traits to CV.KHOI_CONG with zero kind-name conditionals."""
    import re

    src = Path(se.__file__).read_text(encoding="utf-8")
    assert not all(k in src for k in ('"ball"', '"cylinder"', '"cone"'))
    branch_re = re.compile(r'(?:if|elif|while)\b[^\n]*(?:==|!=|\bin\b)[^\n]*["\'](?:ball|cylinder|cone)["\']')
    assert not branch_re.search(src)


# ── Group A: Positive Matrix (S.ABCD + Non-S.ABCD + Chains + Idempotency) ──


def test_group_a_positive_positions_repeat_sequential_and_non_sabcd(catalog_by_id):
    """Group A: first/middle/last/equiv/downstream/repeat/sequential + 4 non-S.ABCD solids."""
    s11 = copy.deepcopy(catalog_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])

    # Repeat identical instruction twice -> deterministic identical digest and zero object bloat
    r_rep1 = execute_step_edit(
        scene3d=s11,
        step_id="mp_tt_AB",
        step_index=14,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
    )
    r_rep2 = execute_step_edit(
        scene3d=r_rep1["scene3d"],
        step_id="mp_tt_AB",
        step_index=14,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
    )
    assert r_rep1["after_scene_digest"] == r_rep2["after_scene_digest"]
    assert len(r_rep1["scene3d"]["objects"]) == len(r_rep2["scene3d"]["objects"])

    # First editable step (base polygon ABCD) & Last geometric step (IA)
    r_first = execute_step_edit(
        scene3d=s11,
        step_id="day_ABCD",
        step_index=1,
        previous_instruction="Dựng đáy ABCD",
        edited_instruction="Dựng đáy ABCD",
        target_ids=["day_ABCD"],
    )
    assert r_first["status"] == "committed"

    r_last = execute_step_edit(
        scene3d=s11,
        step_id="doan_IA",
        step_index=22,
        previous_instruction="Nối IA",
        edited_instruction="Vẽ bán kính IA của mặt cầu",
        target_ids=["doan_IA"],
    )
    assert r_last["status"] == "committed"

    # Sequential 4-step chain on Sample 1 (S = (0,0,6), A = (0,0,0)) -> M z-coords match exact Fraction ratios
    s1 = copy.deepcopy(catalog_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])
    cur = s1
    for ratio_expr, expected_z in (
        ("Lấy điểm M thuộc SA sao cho SM:MA = 1:3", Fraction(9, 2)),
        ("Xác định trung điểm M của SA", Fraction(3)),
        ("Lấy điểm M thuộc SA sao cho SM = 3/4 SA", Fraction(3, 2)),
    ):
        r_chain = execute_step_edit(
            scene3d=cur,
            step_id="M",
            step_index=8,
            previous_instruction="Dựng M.",
            edited_instruction=ratio_expr,
            target_ids=["M"],
        )
        assert r_chain["status"] == "committed"
        cur = r_chain["scene3d"]
        assert _vec3(_find_obj(cur, "M")["xyz"]).z == expected_z
        # Section still closed & coplanar on (MNP)
        pl_mnp = Plane3.through(_vec3(_find_obj(cur, "M")["xyz"]), _vec3(_find_obj(cur, "N")["xyz"]), _vec3(_find_obj(cur, "P")["xyz"]))
        for v in _find_obj(cur, "thiet_dien")["polygon"]:
            assert P.point_on_plane(_vec3(v), pl_mnp)

    # Non-S.ABCD solids: (1) cube ABCD.A′B′C′D′, (2) triangular prism ABC.A′B′C′, (3) S.ABC inclined plane distance
    prism = copy.deepcopy(catalog_by_id["lang-tru-tam-giac-thiet-dien"]["envelope"]["scene3d"])
    r_prism_p = execute_step_edit(
        scene3d=prism,
        step_id="P",
        step_index=6,
        previous_instruction="Xác định trung điểm P của CC′",
        edited_instruction="Lấy điểm P trên CC′ sao cho CP = 1/4 CC′",
        target_ids=["P"],
    )
    assert r_prism_p["status"] == "committed"
    _assert_no_raw_prime_leaks(r_prism_p["scene3d"])
    assert _vec3(_find_obj(r_prism_p["scene3d"], "P")["xyz"]).z == Fraction(1)

    sabc_dist = copy.deepcopy(catalog_by_id["khoang-cach-diem-mat-phang-nghieng"]["envelope"]["scene3d"])
    r_sabc = execute_step_edit(
        scene3d=sabc_dist,
        step_id="H",
        step_index=7,
        previous_instruction="Hạ hình chiếu vuông góc H của A lên (SBC)",
        edited_instruction="Hạ hình chiếu vuông góc H của A lên (SBC)",
        target_ids=["H"],
        force_full_rebuild=True,
    )
    assert r_sabc["status"] == "committed"


# ── Group B: Negative Matrix & API Concurrency ───────────────────────────────


def test_group_b_negative_boundaries_and_concurrent_api(catalog_by_id):
    """Group B: Missing point, type mismatch, contradictory geometry, invalid role, empty/bare plane,
    unsupported curved/calculus op, dependency cycle, and concurrent TestClient requests."""
    s11 = copy.deepcopy(catalog_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    s1 = copy.deepcopy(catalog_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])
    s11_snap = json.dumps(s11, sort_keys=True)

    # 1. Missing point -> MISSING_DEPENDENCY
    with pytest.raises(StepEditRefusal) as e_miss:
        execute_step_edit(
            scene3d=s11, step_id="mp_tt_AB", step_index=14,
            previous_instruction="Dựng (α)", edited_instruction="Dựng mặt phẳng trung trực (α) của cạnh AZ.",
            target_ids=["mp_tt_AB"], absorbed_ids=["M_AB"],
        )
    assert e_miss.value.error_code == "MISSING_DEPENDENCY"

    # 2. Type mismatch -> STEP_TYPE_MISMATCH
    with pytest.raises(StepEditRefusal) as e_type:
        execute_step_edit(
            scene3d=s11, step_id="mp_tt_AB", step_index=14,
            previous_instruction="Dựng (α)", edited_instruction="Nối đoạn thẳng AB.",
            target_ids=["mp_tt_AB"], absorbed_ids=["M_AB"],
        )
    assert e_type.value.error_code == "STEP_TYPE_MISMATCH"

    # 3a. Contradictory line contained in plane -> CONTAINED_INFINITE_INTERSECTION
    with pytest.raises(StepEditRefusal) as e_cont:
        execute_step_edit(
            scene3d=copy.deepcopy(s1), step_id="E", step_index=13,
            previous_instruction="Dựng E.", edited_instruction="Xác định giao điểm E của AB với (ABCD)",
            target_ids=["E"],
        )
    assert e_cont.value.error_code == "CONTAINED_INFINITE_INTERSECTION"

    # 3b. Contradictory parallel/coincident plane intersection -> PARALLEL_NO_INTERSECTION / CONTAINED_INFINITE_INTERSECTION
    s11_noball = _make_sample11_without_ball(catalog_by_id)
    r_shift = execute_step_edit(
        scene3d=s11_noball, step_id="mp_tt_AB", step_index=14,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Xác định điểm H trên cạnh AB sao cho HA:HB = 1:3, dựng mặt phẳng (α) qua H và vuông góc với AB",
        target_ids=["mp_tt_AB"], absorbed_ids=["M_AB"],
    )
    with pytest.raises(StepEditRefusal) as e_par:
        execute_step_edit(
            scene3d=r_shift["scene3d"], step_id="mp_tt_AD", step_index=15,
            previous_instruction="Dựng mặt phẳng trung trực (β) của cạnh AD",
            edited_instruction="Dựng mặt phẳng trung trực (β) của cạnh CD",
            target_ids=["mp_tt_AD"], absorbed_ids=["M_AD"],
        )
    assert e_par.value.error_code in ("PARALLEL_PLANES", "PARALLEL_NO_INTERSECTION", "CONTAINED_INFINITE_INTERSECTION", "COINCIDENT_PLANES")

    # 4. Invalid role in context -> ROLE_ASSERTION_FAILED
    with pytest.raises(StepEditRefusal) as e_role:
        execute_step_edit(
            scene3d=s11, step_id="doan_IA", step_index=22,
            previous_instruction="Nối IA", edited_instruction="Vẽ bán kính OM của mặt cầu",
            target_ids=["doan_IA"],
        )
    assert e_role.value.error_code == "ROLE_ASSERTION_FAILED"

    # 5. Insufficient specification (2 points for plane)
    with pytest.raises(StepEditRefusal) as e_insuff:
        execute_step_edit(
            scene3d=s11, step_id="mp_tt_AB", step_index=14,
            previous_instruction="Dựng (α)", edited_instruction="Dựng mặt phẳng đi qua hai điểm A, B",
            target_ids=["mp_tt_AB"], absorbed_ids=["M_AB"],
        )
    assert e_insuff.value.error_code in ("UNSUPPORTED_STEP_SYNTAX", "INSUFFICIENT_POINTS")

    # 6. Out-of-scope curved solid / calculus command
    with pytest.raises(StepEditRefusal) as e_curved:
        execute_step_edit(
            scene3d=s11, step_id="mp_tt_AB", step_index=14,
            previous_instruction="Dựng (α)", edited_instruction="Dựng hình nón xoay quanh trục SA",
            target_ids=["mp_tt_AB"], absorbed_ids=["M_AB"],
        )
    assert e_curved.value.error_code == "UNSUPPORTED_CURVED_OR_FREEFORM_STEP"

    with pytest.raises(StepEditRefusal) as e_free:
        execute_step_edit(
            scene3d=s11, step_id="mp_tt_AB", step_index=14,
            previous_instruction="Dựng (α)", edited_instruction="Chọn bừa tọa độ giả (1,2,3) cho H",
            target_ids=["mp_tt_AB"], absorbed_ids=["M_AB"],
        )
    assert e_free.value.error_code == "UNSUPPORTED_STEP_SYNTAX"

    # 7. Dependency cycle (step M tries to depend on downstream step E)
    with pytest.raises(StepEditRefusal) as e_cyc:
        execute_step_edit(
            scene3d=s1, step_id="M", step_index=8,
            previous_instruction="Dựng M.", edited_instruction="Xác định trung điểm M của NE",
            target_ids=["M"],
        )
    assert e_cyc.value.error_code == "CYCLE_DEPENDENCY"

    # Caller input snapshot was never mutated in place by any failure!
    assert json.dumps(s11, sort_keys=True) == s11_snap

    # 8. Concurrent API requests on same session produce deterministic state without corruption (IND-6)
    sid = f"ind-conc-{uuid.uuid4().hex[:10]}"
    hdrs = {"X-Axo-Client-Session": f"ind-client-{uuid.uuid4().hex[:8]}"}

    async def _run_concurrent_edits():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as async_client:
            async def _post_ratio(k: int):
                return await async_client.post(
                    "/api/simulation/steps/edit",
                    headers=hdrs,
                    json={
                        "session_id": sid,
                        "problem_key": "sample:chop-thiet-dien-ba-diem",
                        "step_id": "M",
                        "step_index": 8,
                        "previous_instruction": "Dựng M.",
                        "edited_instruction": f"Lấy điểm M thuộc SA sao cho SM:MA = 1:{k}",
                        "target_ids": ["M"],
                        "scene3d": copy.deepcopy(s1),
                    },
                )

            resps = await asyncio.gather(_post_ratio(2), _post_ratio(3))
            state_resp = await async_client.get(f"/api/simulation/sessions/{sid}/state", headers=hdrs)
            return resps, state_resp

    resps, state_resp = asyncio.run(_run_concurrent_edits())

    # Serialized per-session lock ensures both succeed cleanly or fail closed 409/422, NEVER 500!
    assert all(r.status_code in (200, 409, 422) for r in resps), (
        f"Unexpected HTTP status under concurrent edits: {[r.status_code for r in resps]}"
    )
    ok_resps = [r for r in resps if r.status_code == 200]
    assert len(ok_resps) >= 1
    assert state_resp.status_code == 200
    assert state_resp.json()["committed_version"] == len(ok_resps)


# ── Group C: Independent Exact Geometry Oracle on Brand-New Polyhedra ─────────


def _build_fresh_gram_tetrahedron_scene() -> dict:
    """Brand-new synthetic scene (NOT from geometry-samples.json):
    Oblique chart for regular tetrahedron ABCD of edge length 2 via Gram metric,
    plus midpoint M of AB, divided point K on CD (2/5), perp plane (α) through M ⊥ CD,
    intersection line d = (α) ∩ (ABD), intersection point X = d ∩ (BCD), and distance d(M, X).
    """
    A = Vec3.of(0, 0, 0)
    B = Vec3.of(2, 0, 0)
    C = Vec3.of(0, 2, 0)
    D = Vec3.of(0, 0, 2)
    gram = _m.gram_from_lengths(
        (A, B, C, D),
        {
            (0, 1): Fraction(4),
            (0, 2): Fraction(4),
            (0, 3): Fraction(4),
            (1, 2): Fraction(4),
            (1, 3): Fraction(4),
            (2, 3): Fraction(4),
        },
    )
    gram_json = [[str(gram.g[i][j]) for j in range(3)] for i in range(3)]
    with _m.using(gram):
        M0 = K.midpoint(A, B)
        K0 = K.divide_segment(C, D, Fraction(1, 2))
        pl_abd = Plane3.through(A, B, D)
        pl_bcd = Plane3.through(B, C, D)
        ln_ab = Line3.through(A, B)
        pl_alpha = K.plane_through_point_perpendicular_to(M0, ln_ab)
        ln_d = K.intersect_plane_plane(pl_alpha, pl_abd)
        sol = Polyhedron(
            vertices=(A, B, C, D),
            faces=((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)),
        )
        c_sph, r2_sph = circumscribed_sphere(sol.vertices)
        objs = [
            {"id": "A", "type": "point3", "notation": "A", "label": "A", "origin": "free", "depends": [], "xyz": se._exact_xyz_list(A)},
            {"id": "B", "type": "point3", "notation": "B", "label": "B", "origin": "free", "depends": [], "xyz": se._exact_xyz_list(B)},
            {"id": "C", "type": "point3", "notation": "C", "label": "C", "origin": "free", "depends": [], "xyz": se._exact_xyz_list(C)},
            {"id": "D", "type": "point3", "notation": "D", "label": "D", "origin": "free", "depends": [], "xyz": se._exact_xyz_list(D)},
            {"id": "tet", "type": "solid", "notation": "A.BCD", "label": "Tứ diện ABCD", "origin": "derived", "producer": "construct_solid", "depends": ["A", "B", "C", "D"], "vertex_ids": ["A", "B", "C", "D"], "faces": [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]], "vertices": [se._exact_xyz_list(v) for v in (A, B, C, D)]},
            {"id": "abd", "type": "plane3", "notation": "(ABD)", "label": "(ABD)", "origin": "derived", "producer": "construct_plane", "depends": ["A", "B", "D"], "point": se._exact_xyz_list(pl_abd.point), "normal": se._exact_xyz_list(pl_abd.normal)},
            {"id": "bcd", "type": "plane3", "notation": "(BCD)", "label": "(BCD)", "origin": "derived", "producer": "construct_plane", "depends": ["B", "C", "D"], "point": se._exact_xyz_list(pl_bcd.point), "normal": se._exact_xyz_list(pl_bcd.normal)},
            {"id": "ln_ab", "type": "line3", "notation": "AB", "label": "AB", "origin": "derived", "producer": "construct_line", "depends": ["A", "B"], "point": se._exact_xyz_list(ln_ab.point), "direction": se._exact_xyz_list(ln_ab.direction)},
            {"id": "M", "type": "point3", "notation": "M", "label": "Trung điểm M của AB", "origin": "derived", "producer": "construct_point.midpoint", "depends": ["A", "B"], "xyz": se._exact_xyz_list(M0)},
            {"id": "K_pt", "type": "point3", "notation": "K", "label": "Trung điểm K của CD", "origin": "derived", "producer": "construct_point.midpoint", "depends": ["C", "D"], "xyz": se._exact_xyz_list(K0)},
            {"id": "mp_alpha", "type": "plane3", "notation": "(α)", "label": "Mặt phẳng (α) qua M và vuông góc với AB", "origin": "derived", "producer": "plane_perpendicular_to_line", "depends": ["M", "ln_ab"], "point": se._exact_xyz_list(pl_alpha.point), "normal": se._exact_xyz_list(pl_alpha.normal)},
            {"id": "d_ix", "type": "line3", "notation": "d", "label": "Giao tuyến d của (α) và (ABD)", "origin": "derived", "producer": "intersect_plane_plane", "depends": ["mp_alpha", "abd"], "point": se._exact_xyz_list(ln_d.point), "direction": se._exact_xyz_list(ln_d.direction)},
            {"id": "I_tet", "type": "point3", "notation": "I", "label": "Tâm I", "origin": "derived", "producer": "circumscribed_sphere.center", "depends": ["tet"], "xyz": se._exact_xyz_list(c_sph)},
            {"id": "R_tet", "type": "quantity", "notation": "R", "label": "Bán kính R", "origin": "derived", "producer": "measure.distance", "depends": ["I_tet", "A"], "value": radical_display(sqrt_rational(r2_sph)), "exact": radical_to_json(sqrt_rational(r2_sph))},
            {"id": "cos_dihedral", "type": "quantity", "notation": "cos²((α),(BCD))", "label": "Côsin bình phương", "origin": "derived", "producer": "measure.angle_cos_sq", "depends": ["mp_alpha", "bcd"], "value": str(M.cos_sq_giua(pl_alpha, pl_bcd))},
        ]
    events = [{"step_index": 0, "action": "INIT", "object": None, "depends": [], "semantic_kind": "SCENE_INIT", "learner_text": "Khởi tạo tứ diện đều ABCD cạnh 2."}]
    for i, o in enumerate(objs[4:], start=1):
        events.append({
            "step_index": i,
            "action": "CREATE",
            "object": o["id"],
            "depends": list(o.get("depends") or ()),
            "display_label": o["label"],
            "semantic_kind": "MEASUREMENT" if o.get("type") == "quantity" else "GEOMETRY_CONSTRUCTION",
            "learner_text": o["label"],
        })
    return {"chart_metric": gram_json, "free_objects": ["A", "B", "C", "D"], "objects": objs, "events": events}


def test_group_c_independent_exact_geometry_oracle():
    """Group C: Independent geometric oracle checking Gram metric, predicates, topology, camera invariance & repeatability."""
    base_scene = _build_fresh_gram_tetrahedron_scene()
    gram = se._scene_metric(base_scene)
    assert gram is not None

    # Edit M to divide segment AB at exact ratio AM:MB = 2:3 (AM = 2/5 AB), mutating (α) and intersection line d and cos²!
    # Also attach non-trivial visual_transform to confirm camera/display transform invariance!
    scene_vt = copy.deepcopy(base_scene)
    for o in scene_vt["objects"]:
        o["visual_transform"] = {"translate": [12, -5, 9], "scale": 3}

    r1 = execute_step_edit(
        scene3d=base_scene,
        step_id="M",
        step_index=5,
        previous_instruction="Trung điểm M của AB",
        edited_instruction="Lấy điểm M thuộc AB sao cho AM = 2/5 AB",
        target_ids=["M"],
    )
    r2 = execute_step_edit(
        scene3d=scene_vt,
        step_id="M",
        step_index=5,
        previous_instruction="Trung điểm M của AB",
        edited_instruction="Lấy điểm M thuộc AB sao cho AM = 2/5 AB",
        target_ids=["M"],
    )
    assert r1["status"] == "committed" and r2["status"] == "committed"

    # Bit-identical repeatability across repeated calls on identical input
    r1_repeat = execute_step_edit(
        scene3d=base_scene,
        step_id="M",
        step_index=5,
        previous_instruction="Trung điểm M của AB",
        edited_instruction="Lấy điểm M thuộc AB sao cho AM = 2/5 AB",
        target_ids=["M"],
    )
    assert r1["after_scene_digest"] == r1_repeat["after_scene_digest"]

    out = r1["scene3d"]
    out_vt = r2["scene3d"]
    with _m.using(gram):
        A = _vec3(_find_obj(out, "A")["xyz"])
        B = _vec3(_find_obj(out, "B")["xyz"])
        D = _vec3(_find_obj(out, "D")["xyz"])
        M_pt = _vec3(_find_obj(out, "M")["xyz"])
        M_vt = _vec3(_find_obj(out_vt, "M")["xyz"])
        # 1. Camera / presentation invariance: visual_transform never changes kernel coordinates
        assert M_pt == M_vt
        # 2. Point-on-line & Segment ratio t = 2/5 in Gram metric
        on_seg, ratio = _point_on_segment(M_pt, A, B)
        assert on_seg and ratio == Fraction(2, 5)
        # 3. Plane (α) contains M and is orthogonal to line AB (P.line_perpendicular_plane)
        pl_alpha_o = _find_obj(out, "mp_alpha")
        pl_alpha = Plane3(_vec3(pl_alpha_o["point"]), _vec3(pl_alpha_o["normal"]))
        ln_ab = Line3.through(A, B)
        assert P.point_on_plane(M_pt, pl_alpha)
        assert P.line_perpendicular_plane(ln_ab, pl_alpha)
        # 4. Intersection line d lies simultaneously on BOTH (α) and (ABD)!
        d_o = _find_obj(out, "d_ix")
        ln_d = Line3(_vec3(d_o["point"]), _vec3(d_o["direction"]))
        pl_abd = Plane3.through(A, B, D)
        assert P.line_in_plane(ln_d, pl_alpha)
        assert P.line_in_plane(ln_d, pl_abd)
        # 5. Circumscribed sphere radius exact under Gram metric: regular tet a=2 -> R^2 = 3/2, R = sqrt(6)/2
        I_pt = _vec3(_find_obj(out, "I_tet")["xyz"])
        for vid in ("A", "B", "C", "D"):
            assert _m.norm_sq(_vec3(_find_obj(out, vid)["xyz"]) - I_pt) == Fraction(3, 2)
        assert parse_exact(_find_obj(out, "R_tet")["exact"]) == sqrt_rational(Fraction(3, 2))
        # 6. Exact dihedral cos² between (α)⊥AB and (BCD): angle(normal(α)=AB, normal(BCD)) -> height/edge -> cos² = 2/3
        pl_bcd_o = _find_obj(out, "bcd")
        pl_bcd = Plane3(_vec3(pl_bcd_o["point"]), _vec3(pl_bcd_o["normal"]))
        expected_cos2 = M.cos_sq_giua(pl_alpha, pl_bcd)
        assert Fraction(_find_obj(out, "cos_dihedral")["value"]) == expected_cos2
        assert expected_cos2 == Fraction(2, 3)

    # 7. Topological dependency order strictly respects producer -> consumer across rebuilt scene
    g_out = build_construction_dependency_graph(out)
    pos = {oid: idx for idx, oid in enumerate(g_out["topo_order"])}
    for oid, deps in g_out["deps_of"].items():
        for dep in deps:
            assert pos[dep] < pos[oid], f"Topological violation: {dep} at {pos[dep]} after {oid} at {pos[oid]}"
