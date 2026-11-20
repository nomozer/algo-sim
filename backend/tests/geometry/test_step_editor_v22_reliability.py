# -*- coding: utf-8 -*-
"""AXO Step Editor V2.2 — Reliability Hardening & Mathematical Oracle Regression Suite.

Phase B (RED) -> Phase C (GREEN):
1. Independent Exact Algebraic Oracle (§6):
   S.ABCD square base side 4, SA = 4 perp (ABCD):
   A=(0,0,0), B=(4,0,0), D=(0,4,0), C=(4,4,0), S=(0,0,4)
   -> I=(2,2,2), R=2*sqrt(3), V=32*pi*sqrt(3), |IA|=|IB|=|IC|=|ID|=|IS|=2*sqrt(3),
   plus exact plane equations, intersection lines, and 6 edit categories.
2. Reproducible bugs discovered in Phase A (BUG-1, BUG-4, BUG-5, BUG-6, BUG-7).
3. All backend special edge cases (§7): #1, #2, #3, #4, #10, #11, #12, #13, #18, #19, #20.
"""
from __future__ import annotations

import copy
import sys
import uuid
from fractions import Fraction
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR / "scripts"))

import build_advanced_geometry_samples as adv_samples  # noqa: E402
from app.main import app  # noqa: E402
from app.persistence.db import SessionLocal  # noqa: E402
from app.persistence.step_edit_models import StepEditSessionRecord, ensure_step_edit_tables  # noqa: E402
from app.simulation.geometry import (  # noqa: E402
    Vec3,
    circumscribed_sphere,
    metric as _m,
)
from app.simulation.geometry.radical import Radical, parse_exact, sqrt_rational  # noqa: E402
from app.ai.step_edit_route import execute_step_edit  # noqa: E402
from app.simulation.geometry_functions import step_editor as se  # noqa: E402
from app.simulation.geometry_functions.step_editor import (  # noqa: E402
    StepEditRefusal,
    build_construction_dependency_graph,
    parse_vietnamese_construction_step,
)


@pytest.fixture(scope="module")
def samples_by_id() -> dict[str, dict]:
    ensure_step_edit_tables()
    return {item["id"]: item for item in adv_samples.build_all_advanced_samples()}


def _find_obj(scene: dict, oid: str) -> dict | None:
    return next((o for o in scene.get("objects") or [] if o.get("id") == oid), None)


def _vec3(raw: list) -> Vec3:
    assert len(raw) == 3
    return Vec3.of(parse_exact(raw[0]), parse_exact(raw[1]), parse_exact(raw[2]))


def _independent_oracle_verify_sample11(scene: dict) -> None:
    """Verify Sample 11 against an independent Fraction/Radical Euclidean oracle (NOT Planner output)."""
    by_id = {o["id"]: o for o in scene["objects"]}

    # 1. Exact vertex coordinates A=(0,0,0), B=(4,0,0), D=(0,4,0), C=(4,4,0), S=(0,0,4)
    A = _vec3(by_id["A"]["xyz"])
    B = _vec3(by_id["B"]["xyz"])
    C = _vec3(by_id["C"]["xyz"])
    D = _vec3(by_id["D"]["xyz"])
    S = _vec3(by_id["S"]["xyz"])
    assert A == Vec3.of(0, 0, 0)
    assert B == Vec3.of(4, 0, 0)
    assert D == Vec3.of(0, 4, 0)
    assert C == Vec3.of(4, 4, 0)
    assert S == Vec3.of(0, 0, 4)

    # 2. Perpendicular bisector planes via independent normal/plane equations:
    # (alpha) of AB: x = 2; (beta) of AD: y = 2; (gamma) of SA: z = 2
    for pid, expected_pt, expected_axis in (
        ("mp_tt_AB", Vec3.of(2, 0, 0), B - A),
        ("mp_tt_AD", Vec3.of(0, 2, 0), D - A),
        ("mp_tt_SA", Vec3.of(0, 0, 2), S - A),
    ):
        po = by_id[pid]
        p0 = _vec3(po["point"])
        n = _vec3(po["normal"])
        # Normal parallel to segment vector AND point on plane eq (p0 - expected_pt) . n == 0
        assert n.cross(expected_axis).is_zero(), f"{pid} normal not parallel to bisected segment"
        assert (p0 - expected_pt).dot(n) == 0, f"{pid} does not pass through exact midpoint"
        assert (expected_pt - p0).dot(n) == 0

    # 3. Intersection line truc_day = (alpha) ∩ (beta): passes through (2,2,t), direction || (0,0,1)
    truc = by_id["truc_day"]
    t_pt = _vec3(truc["point"])
    t_dir = _vec3(truc["direction"])
    assert t_pt.x == Fraction(2) and t_pt.y == Fraction(2)
    assert t_dir.cross(Vec3.of(0, 0, 1)).is_zero()

    # 4. Circumcenter I = (2,2,2), R = 2*sqrt(3), V = 32*pi*sqrt(3)
    I_pt = _vec3(by_id["I"]["xyz"])
    oracle_center, oracle_r_sq = circumscribed_sphere([A, B, C, D, S])
    assert oracle_center == Vec3.of(2, 2, 2)
    assert oracle_r_sq == Fraction(12)
    assert I_pt == oracle_center

    # Exact equidistant check |IA|^2 = |IB|^2 = |IC|^2 = |ID|^2 = |IS|^2 = 12 => distance = 2*sqrt(3)
    for label, v in (("A", A), ("B", B), ("C", C), ("D", D), ("S", S)):
        dist_sq = _m.norm_sq(I_pt - v)
        assert dist_sq == Fraction(12), f"|I{label}|^2 expected 12, got {dist_sq}"
        assert sqrt_rational(dist_sq) == Radical(2, 3)

    r_obj = by_id["R"]
    assert r_obj["value"] == "2√3"
    assert r_obj["exact"] == {"kind": "radical", "coefficient": "2", "radicand": 3}

    v_obj = by_id["V_cau"]
    assert v_obj["value"] == "32π√3"
    assert v_obj["exact"] == {"kind": "radical", "coefficient": "32", "radicand": 3, "pi": 1}


# ── §6 Independent Mathematical Oracle & 6 Edit Categories ───────────────────────


def test_oracle_and_equivalent_bisector_round_trip_no_ghost_objects(samples_by_id):
    """BUG-5 & §4.1.A & §7 #19: Equivalent phrasings match mathematically & leave zero ghost named points."""
    base_scene = copy.deepcopy(samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    _independent_oracle_verify_sample11(base_scene)

    # A1: Single-clause bisector -> compound midpoint H + perp plane (α)
    r1 = execute_step_edit(
        scene3d=base_scene,
        step_id="mp_tt_AB",
        step_index=14,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Xác định trung điểm H của AB, dựng mặt phẳng (α) qua H và vuông góc với AB",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
    )
    assert r1["status"] == "committed"
    assert r1["equivalence_info"]["geometrically_equivalent"] is True
    assert r1["equivalence_info"]["change_classification"] == "EQUIVALENT_GEOMETRY"
    _independent_oracle_verify_sample11(r1["scene3d"])

    # A2: Reverse edit back to concise perpendicular bisector -> NO phantom named point H left!
    r2 = execute_step_edit(
        scene3d=r1["scene3d"],
        step_id="mp_tt_AB",
        step_index=14,
        previous_instruction="Xác định trung điểm H của AB, dựng mặt phẳng (α) qua H và vuông góc với AB",
        edited_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["H"],
        step_overrides=r1["step_overrides"],
    )
    assert r2["status"] == "committed"
    assert r2["equivalence_info"]["geometrically_equivalent"] is True
    _independent_oracle_verify_sample11(r2["scene3d"])

    # Ghost check: no surviving point3 may carry notation == "H" after reverting to unnamed bisector!
    named_points = {
        o.get("notation")
        for o in r2["scene3d"]["objects"]
        if o.get("type") == "point3" and o.get("notation")
    }
    assert "H" not in named_points, f"Ghost named point 'H' lingered after reverting to single-clause bisector: {named_points}"


def test_six_edit_categories_classification_and_crash_safety(samples_by_id):
    """§6 & BUG-1: Verify all 6 categories; step-type mismatch returns StepEditRefusal, NEVER KeyError/500."""
    s11 = copy.deepcopy(samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    s1 = copy.deepcopy(samples_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])

    # Category 6 / BUG-1: Editing a plane3 step with a midpoint instruction must refuse cleanly (NOT KeyError)
    with pytest.raises(StepEditRefusal) as exc_type:
        execute_step_edit(
            scene3d=s11,
            step_id="mp_tt_AB",
            step_index=14,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Xác định trung điểm H của AB.",
            target_ids=["mp_tt_AB"],
            absorbed_ids=["M_AB"],
        )
    assert exc_type.value.error_code == "STEP_TYPE_MISMATCH"

    # Category 3 (Missing Data): Missing operand -> MISSING_DEPENDENCY / INSUFFICIENT_POINTS
    with pytest.raises(StepEditRefusal) as exc_missing:
        execute_step_edit(
            scene3d=s11,
            step_id="mp_tt_AB",
            step_index=14,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
            target_ids=["mp_tt_AB"],
            absorbed_ids=["M_AB"],
        )
    assert exc_missing.value.error_code == "MISSING_DEPENDENCY"

    # Category 4 (Contradictory): Make (β) parallel to (α), breaking downstream truc_day = (α) ∩ (β)
    with pytest.raises(StepEditRefusal) as exc_contra:
        execute_step_edit(
            scene3d=s11,
            step_id="mp_tt_AD",
            step_index=15,
            previous_instruction="Gọi (β) là mặt phẳng qua M_AD và vuông góc với AD.",
            edited_instruction="Dựng mặt phẳng (β) đi qua D và song song với mặt phẳng (α).",
            target_ids=["mp_tt_AD"],
            absorbed_ids=["M_AD"],
        )
    assert exc_contra.value.error_code in {"PARALLEL_NO_INTERSECTION", "PARALLEL_PLANES", "NO_INTERSECTION"}

    # Category 5 (Unsupported): Outside supported capability -> clean refusal
    with pytest.raises(StepEditRefusal) as exc_unsupp:
        execute_step_edit(
            scene3d=s11,
            step_id="mp_tt_AB",
            step_index=14,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Tính tích phân mặt trên mặt phẳng (α).",
            target_ids=["mp_tt_AB"],
        )
    assert exc_unsupp.value.error_code in {"UNSUPPORTED_STEP_SYNTAX", "UNSUPPORTED_CURVED_OR_FREEFORM_STEP"}

    # Category 2 (Valid Geometry-Mutating): Sample 1 ratio SM:MA = 1:2 -> M, mp_MNP, E, F, S_td updated exactly
    r_mut = execute_step_edit(
        scene3d=s1,
        step_id="M",
        step_index=8,
        previous_instruction="Dựng M.",
        edited_instruction="Lấy điểm M trên cạnh SA sao cho SM:MA = 1:2",
        target_ids=["M"],
    )
    assert r_mut["status"] == "committed"
    assert r_mut["equivalence_info"]["change_classification"] == "GEOMETRY_MUTATED"
    assert _vec3(_find_obj(r_mut["scene3d"], "M")["xyz"]) == Vec3.of(0, 0, 4)
    assert _vec3(_find_obj(r_mut["scene3d"], "E")["xyz"]) == Vec3.of(Fraction(12, 5), 0, Fraction(12, 5))
    assert _vec3(_find_obj(r_mut["scene3d"], "F")["xyz"]) == Vec3.of(0, Fraction(12, 5), Fraction(12, 5))
    assert _find_obj(r_mut["scene3d"], "S_td")["value"] == "18√17/5"


# ── §7 Special Edge Cases (Backend & Multi-Consumer Section Metadata) ───────────


def test_edge_case_1_2_3_4_first_middle_last_and_sequential_edits(samples_by_id):
    """§7 #1, #2, #3, #4 & BUG-1/BUG-6/BUG-7: First (polygon/altitude), middle (3-plane I), last (IS/IA), sequential."""
    s11 = copy.deepcopy(samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])

    # #1 First step: cyclic valid base polygon reorder BCDA succeeds; bowtie ABDC MUST fail!
    r_first_ok = execute_step_edit(
        scene3d=s11,
        step_id="day_ABCD",
        step_index=1,
        previous_instruction="Dựng đáy ABCD.",
        edited_instruction="Dựng đáy BCDA",
        target_ids=["day_ABCD"],
        prior_step_ids=["A", "B", "C", "D", "S"],
    )
    assert r_first_ok["status"] == "committed"
    with pytest.raises(StepEditRefusal) as exc_bowtie:
        execute_step_edit(
            scene3d=s11,
            step_id="day_ABCD",
            step_index=1,
            previous_instruction="Dựng đáy ABCD.",
            edited_instruction="Dựng đáy ABDC",
            target_ids=["day_ABCD"],
            prior_step_ids=["A", "B", "C", "D", "S"],
        )
    assert exc_bowtie.value.error_code in {"SELF_INTERSECTING_POLYGON", "DEGENERATE_POLYGON", "NON_CONVEX_POLYGON"}

    # #1b Altitude step (chieu_cao_SA): valid SA ⊥ (ABCD) tại A succeeds (NOT KeyError!); false SB ⊥ (ABCD) tại B refuses!
    r_alt = execute_step_edit(
        scene3d=r_first_ok["scene3d"],
        step_id="chieu_cao_SA",
        step_index=2,
        previous_instruction="Dựng chiều cao SA.",
        edited_instruction="Kẻ đường cao SA ⊥ (ABCD) tại A",
        target_ids=["chieu_cao_SA"],
        prior_step_ids=["A", "B", "C", "D", "S", "day_ABCD"],
    )
    assert r_alt["status"] == "committed"
    with pytest.raises(StepEditRefusal) as exc_false_alt:
        execute_step_edit(
            scene3d=r_alt["scene3d"],
            step_id="chieu_cao_SA",
            step_index=2,
            previous_instruction="Dựng chiều cao SA.",
            edited_instruction="Kẻ đường cao SB ⊥ (ABCD) tại B",
            target_ids=["chieu_cao_SA"],
            prior_step_ids=["A", "B", "C", "D", "S", "day_ABCD"],
        )
    assert exc_false_alt.value.error_code == "ROLE_ASSERTION_FAILED"

    # #2 Middle step: Step 12 phrasing on I = Giao tuyến của (α) và (β) ∩ (γ) + ba mặt phẳng
    r_mid = execute_step_edit(
        scene3d=r_alt["scene3d"],
        step_id="I",
        step_index=18,
        previous_instruction="Dựng I.",
        edited_instruction="Xác định giao điểm I = Giao tuyến của (α) và (β) ∩ (γ)",
        target_ids=["I"],
    )
    assert r_mid["status"] == "committed"
    assert _vec3(_find_obj(r_mid["scene3d"], "I")["xyz"]) == Vec3.of(2, 2, 2)

    # #3 & #4 Last geometry step + sequential edits (v1 -> v2 -> v3 -> v4)
    r_last = execute_step_edit(
        scene3d=r_mid["scene3d"],
        step_id="doan_IA",
        step_index=22,
        previous_instruction="Nối bán kính IA của mặt cầu",
        edited_instruction="Nối bán kính IB của mặt cầu",
        target_ids=["doan_IA"],
        step_overrides=r_mid["step_overrides"],
    )
    assert r_last["status"] == "committed"
    seg_obj = _find_obj(r_last["scene3d"], "doan_IA")
    assert seg_obj["endpoint_ids"] == ["I", "B"]
    assert seg_obj["notation"] == "IB"
    _independent_oracle_verify_sample11(r_last["scene3d"])


def test_edge_case_20_false_sphere_radius_role_refused(samples_by_id):
    """§7 #20 & BUG-6: Syntactically valid radius claim on non-radius segment IO (|IO|=2 != 2√3) MUST refuse."""
    s11 = copy.deepcopy(samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    with pytest.raises(StepEditRefusal) as exc:
        execute_step_edit(
            scene3d=s11,
            step_id="doan_IA",
            step_index=22,
            previous_instruction="Nối bán kính IA của mặt cầu",
            edited_instruction="Nối bán kính IO của mặt cầu",
            target_ids=["doan_IA"],
        )
    assert exc.value.error_code == "ROLE_ASSERTION_FAILED"


def test_edge_case_13_duplicate_identifiers_and_notations_refused(samples_by_id):
    """§7 #13 & BUG-4: Duplicate point/plane identifiers within a step or across surviving objects MUST refuse."""
    s11 = copy.deepcopy(samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])

    # 1. Compound step defining symbol H twice at distinct midpoints
    with pytest.raises(StepEditRefusal) as e1:
        execute_step_edit(
            scene3d=s11,
            step_id="mp_tt_AB",
            step_index=14,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Xác định trung điểm H của AB, xác định trung điểm H của AD, dựng mặt phẳng (α) qua H và vuông góc với AB",
            target_ids=["mp_tt_AB"],
            absorbed_ids=["M_AB"],
        )
    assert e1.value.error_code == "DUPLICATE_OBJECT_IDENTIFIER"

    # 2. Renaming point3 step O to M when M already exists on SA
    with pytest.raises(StepEditRefusal) as e2:
        execute_step_edit(
            scene3d=s11,
            step_id="O",
            step_index=7,
            previous_instruction="Dựng O.",
            edited_instruction="Xác định trung điểm M của BD",
            target_ids=["O"],
        )
    assert e2.value.error_code == "DUPLICATE_OBJECT_IDENTIFIER"

    # 3. Renaming plane (α) to (β) when (β) is already assigned to mp_tt_AD
    with pytest.raises(StepEditRefusal) as e3:
        execute_step_edit(
            scene3d=s11,
            step_id="mp_tt_AB",
            step_index=14,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Dựng mặt phẳng trung trực (β) của cạnh AB",
            target_ids=["mp_tt_AB"],
            absorbed_ids=["M_AB"],
        )
    assert e3.value.error_code == "DUPLICATE_OBJECT_IDENTIFIER"


def test_edge_case_11_and_12_cycle_and_missing_reference_in_dag(samples_by_id):
    """§7 #11 & #12: Explicit dependency cycle and dangling missing reference in Scene3D graph."""
    s11 = copy.deepcopy(samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])

    # #11 Inject explicit cycle A_c <-> B_c
    cyclic = copy.deepcopy(s11)
    by_id = {o["id"]: o for o in cyclic["objects"]}
    by_id["mp_tt_AB"]["depends"] = ["mp_tt_AD", "ab"]
    by_id["mp_tt_AD"]["depends"] = ["mp_tt_AB", "ad"]
    with pytest.raises(StepEditRefusal) as e_cyc:
        build_construction_dependency_graph(cyclic)
    assert e_cyc.value.error_code in {"CYCLE_DEPENDENCY", "DEPENDENCY_CYCLE"}

    # #12 Inject missing/non-existent object reference
    dangling = copy.deepcopy(s11)
    dangling_by_id = {o["id"]: o for o in dangling["objects"]}
    dangling_by_id["mp_tt_AB"]["depends"] = ["NON_EXISTENT_HELPER", "ab"]
    with pytest.raises(StepEditRefusal) as e_miss:
        build_construction_dependency_graph(dangling)
    assert e_miss.value.error_code == "MISSING_REFERENCE"


def test_edge_case_4_1d_multi_consumer_section_clears_stale_fields(samples_by_id):
    """§4.1.D & BUG-7: When upstream move changes a section from pentagon MENPF to a 4-gon, zero stale 'MENPF' remains."""
    s1 = copy.deepcopy(samples_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])
    # Moving P onto AD with AP = 1/3 AD yields a valid 4-gon cross-section instead of 5-gon MENPF
    r_p = execute_step_edit(
        scene3d=s1,
        step_id="P",
        step_index=9,
        previous_instruction="Dựng P.",
        edited_instruction="Lấy điểm P trên cạnh AD sao cho AP = 1/3 AD",
        target_ids=["P"],
    )
    assert r_p["status"] == "committed"
    sec_obj = _find_obj(r_p["scene3d"], "thiet_dien")
    assert len(sec_obj["polygon"]) == 4
    # Must NOT retain stale 5-gon "MENPF" identifiers or labels on sec_obj, S_td, or section step titles!
    assert "MENPF" not in str(sec_obj.get("label") or "")
    assert "NPFME" not in str(sec_obj.get("label") or "")
    assert "MENPF" not in str(sec_obj.get("notation") or "")
    assert "NPFME" not in str(sec_obj.get("notation") or "")
    assert len(sec_obj.get("ordered_vertex_ids") or []) == 4
    s_td = _find_obj(r_p["scene3d"], "S_td")
    assert "MENPF" not in str(s_td.get("notation") or "")
    assert "NPFME" not in str(s_td.get("notation") or "")
    assert "MENPF" not in str(s_td.get("label") or "")
    assert "NPFME" not in str(s_td.get("label") or "")
    assert "MENPF" not in str((s_td.get("formula") or {}).get("text") or "")
    assert "NPFME" not in str((s_td.get("formula") or {}).get("text") or "")
    assert "MENPF" not in str(s_td.get("annotation") or "")
    for st in r_p["scene3d"]["formation"]["steps"]:
        assert "MENPF" not in str(st.get("learner_text") or "")
        assert "NPFME" not in str(st.get("learner_text") or "")
        assert "MENPF" not in str((st.get("step_summary") or {}).get("inputs") or "")

    # Partial topological rebuild vs full topological rebuild must produce identical exact coordinates & quantities
    r_full = execute_step_edit(
        scene3d=copy.deepcopy(s1),
        step_id="P",
        step_index=9,
        previous_instruction="Dựng P.",
        edited_instruction="Lấy điểm P trên cạnh AD sao cho AP = 1/3 AD",
        target_ids=["P"],
        force_full_rebuild=True,
    )
    assert r_full["mode"] == "FULL_TOPOLOGICAL_REBUILD"
    assert r_full["dependency_summary"]["skipped_unaffected_ids"] == []
    assert _find_obj(r_full["scene3d"], "thiet_dien")["polygon"] == sec_obj["polygon"]
    assert _find_obj(r_full["scene3d"], "S_td")["exact"] == s_td["exact"]


def test_edge_case_10_server_gate_rejects_incomplete_validation_and_18_recovers_state(
    samples_by_id,
    monkeypatch,
):
    """§7 #10 & #18 & BUG-2: API commit gate refuses incomplete validation_result (zero DB mutation) and GET /state recovers valid state."""
    s11 = copy.deepcopy(samples_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    client = TestClient(app)
    sid = f"se-v22-{uuid.uuid4().hex[:12]}"
    headers = {"X-Axo-Client-Session": f"tok-{uuid.uuid4().hex}"}

    # 1. Valid commit succeeds -> version_number = 1
    ok_resp = client.post(
        "/api/simulation/steps/edit",
        headers=headers,
        json={
            "session_id": sid,
            "problem_key": "sample:chop-mat-cau-ngoai-tiep",
            "step_id": "mp_tt_AB",
            "step_index": 14,
            "previous_instruction": "Dựng mặt phẳng trung trực (α) của cạnh AB",
            "edited_instruction": "Xác định trung điểm H của AB, dựng mặt phẳng (α) qua H và vuông góc với AB",
            "target_ids": ["mp_tt_AB"],
            "absorbed_ids": ["M_AB"],
            "prior_step_ids": ["A", "B", "C", "D", "S"],
            "scene3d": s11,
        },
    )
    assert ok_resp.status_code == 200
    v1_body = ok_resp.json()
    assert v1_body["version_number"] == 1
    assert v1_body["validation_result"]["passed"] is True
    assert v1_body["validation_result"]["continuity"]["passed"] is True
    assert v1_body["dependency_summary"]["cycle_detected"] is False

    # 2. Simulate backend bug producing incomplete validation_result (missing passed/continuity) -> router MUST reject!
    from app.ai import step_edit_route  # noqa: E402

    real_exec = step_edit_route.execute_step_edit

    def _corrupt_exec(**kwargs):
        out = real_exec(**kwargs)
        out["validation_result"] = {"valid": True}  # missing passed=True and continuity.passed=True!
        return out

    from app.simulation import step_edit_router  # noqa: E402

    monkeypatch.setattr(step_edit_router, "execute_step_edit", _corrupt_exec)
    bad_resp = client.post(
        "/api/simulation/steps/edit",
        headers=headers,
        json={
            "session_id": sid,
            "problem_key": "sample:chop-mat-cau-ngoai-tiep",
            "step_id": "mp_tt_AB",
            "step_index": 14,
            "previous_instruction": "Xác định trung điểm H của AB, dựng mặt phẳng (α) qua H và vuông góc với AB",
            "edited_instruction": "Dựng mặt phẳng trung trực (α) của cạnh AB",
            "target_ids": ["mp_tt_AB"],
            "absorbed_ids": ["H"],
            "scene3d": v1_body["scene3d"],
        },
    )
    assert bad_resp.status_code == 422
    assert bad_resp.json()["error_code"] == "VALIDATION_INCOMPLETE"

    # 3. #18 Session recovery GET /state still holds exact uncorrupted v1 committed scene
    state_resp = client.get(f"/api/simulation/sessions/{sid}/state", headers=headers)
    assert state_resp.status_code == 200
    st = state_resp.json()
    assert st["found"] is True
    assert st["revision_count"] >= 1
    assert _find_obj(st["committed_scene"], "H") is not None
    _independent_oracle_verify_sample11(st["committed_scene"])
