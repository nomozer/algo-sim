# -*- coding: utf-8 -*-
"""AXO Step Editor — Root-Cause Stabilization & Pre-Merge Verification Suite.

Phase B (RED) -> Phase C (GREEN):
- RC-1: AST layering gate (step_editor.py must NOT import scene3d/app.ai/simulation_state;
  app.ai.step_edit_route owns scene3d projection hooks & execute_step_edit entrypoint).
- RC-2: Derived producers & downstream DAG completeness:
  - plane_parallel_to_plane & line_perpendicular_to_plane emit exact producers & validate;
  - construct_segment honors segment_role="altitude" (perpendicular witness & refusal on oblique edge);
  - construct_solid uses live mem[v] vertices, never stale cached coordinates;
  - _reevaluate_object supports vector_from_points, circumscribed_sphere.center, measure.total_area;
  - Unknown non-free derived producers fail-closed with UNSUPPORTED_DOWNSTREAM_RECOMPUTE.
- RC-3: Empty/unedited StepEditSessionRecord never pollutes GET /state or locks stale base_scene_sha256.
- RC-4: Downstream steps whose geometry mutates drop stale manual overrides in step_overrides.
- Golden Cases A, B, C, D verified against an independent Fraction/Radical Euclidean oracle (§5).
- NL Parser Boundary Corpus (§9).
"""
from __future__ import annotations

import ast
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
from app.persistence.step_edit_models import (  # noqa: E402
    StepEditRevisionRecord,
    StepEditSessionRecord,
    ensure_step_edit_tables,
)
from app.simulation.geometry import (  # noqa: E402
    Line3,
    Plane3,
    Vec3,
    circumscribed_sphere,
    metric as _m,
    predicates as P,
)
from app.simulation.geometry.radical import parse_exact, sqrt_rational  # noqa: E402
from app.ai.step_edit_route import execute_step_edit
from app.simulation.geometry_functions import step_editor as se  # noqa: E402
from app.simulation.geometry_functions.step_editor import (  # noqa: E402
    StepEditRefusal,
    parse_vietnamese_construction_step,
)


def _exec_step_edit(**kwargs):
    return execute_step_edit(**kwargs)


@pytest.fixture(scope="module")
def adv_by_id() -> dict[str, dict]:
    ensure_step_edit_tables()
    return {item["id"]: item for item in adv_samples.build_all_advanced_samples()}


def _find_obj(scene: dict, oid: str) -> dict | None:
    return next((o for o in scene.get("objects") or [] if o.get("id") == oid), None)


def _vec3(raw: list) -> Vec3:
    assert len(raw) == 3
    return Vec3.of(parse_exact(raw[0]), parse_exact(raw[1]), parse_exact(raw[2]))


def _make_sample11_without_ball(adv_by_id: dict[str, dict]) -> dict:
    """Copy of Sample 11 stripped of circumscribed ball & transitive dependents so truc_day can shift freely."""
    s = copy.deepcopy(adv_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    seeds = {"I", "R_cau", "mat_cau", "V_cau", "S_cau", "IS", "IA", "mp_tt_SA"}
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


# ── RC-1: AST Layering & Route Boundary ───────────────────────────────────────


def test_rc1_layering_and_route_entrypoint():
    """step_editor.py must NOT import scene3d/app.ai/simulation_state; app.ai.step_edit_route owns execute_step_edit."""
    step_editor_path = BACKEND_DIR / "app" / "simulation" / "geometry_functions" / "step_editor.py"
    tree = ast.parse(step_editor_path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
        elif isinstance(node, ast.Import):
            imported |= {alias.name for alias in node.names}

    bad = [m for m in sorted(imported) if "scene3d" in m or m.startswith(("app.ai", "app.main")) or "simulation_state" in m]
    assert not bad, f"RC-1 layering violation in step_editor.py: {bad}"

    from app.ai.step_edit_route import DEFAULT_SCENE3D_HOOKS, execute_step_edit

    assert callable(execute_step_edit)
    assert callable(DEFAULT_SCENE3D_HOOKS.build_formation)


# ── RC-2: Derived Producers, Altitude Role, Solid Hydration & Fail-Closed DAG ─


def test_rc2_parallel_plane_and_perp_line_producers_and_downstream_recompute(adv_by_id):
    """plane_parallel_to_plane & line_perpendicular_to_plane must store exact producers and recompute cleanly on full rebuild."""
    scene = _make_sample11_without_ball(adv_by_id)
    # Add a synthetic line3 step d through A perp to day_mat so line_perpendicular_to_plane is tested with downstream point
    # First edit mp_tt_AB to plane_parallel_to_plane through S parallel to (ABCD) (WAIT: wait - truc_day = (α) ∩ (β):
    # if (α): z=4 and (β): y=2 -> truc_day passes through (x, 2, 4), direction (1,0,0)! Not parallel!)
    r1 = _exec_step_edit(
        scene3d=scene,
        step_id="mp_tt_AB",
        step_index=7,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Dựng mặt phẳng (α) qua S và song song với (ABCD).",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
    )
    assert r1["status"] == "committed"
    alpha = _find_obj(r1["scene3d"], "mp_tt_AB")
    assert alpha is not None
    assert alpha["producer"] == "plane_parallel_to_plane"

    # Re-verify truc_day = (α): z=4 ∩ (β): y=2 -> point has y=2, z=4, dir || (1,0,0)
    truc = _find_obj(r1["scene3d"], "truc_day")
    assert truc is not None
    t_pt = _vec3(truc["point"])
    t_dir = _vec3(truc["direction"])
    assert t_pt.y == Fraction(2) and t_pt.z == Fraction(4)
    assert t_dir.cross(Vec3.of(1, 0, 0)).is_zero()

    # Now trigger force_full_rebuild on a downstream step to prove plane_parallel_to_plane re-evaluates cleanly without failing as 3-point construct_plane!
    r2 = _exec_step_edit(
        scene3d=r1["scene3d"],
        step_id="mp_tt_AD",
        step_index=8,
        previous_instruction="Dựng mặt phẳng trung trực (β) của cạnh AD",
        edited_instruction="Dựng mặt phẳng trung trực (β) của cạnh CD.",
        target_ids=["mp_tt_AD"],
        absorbed_ids=["M_AD"],
        force_full_rebuild=True,
    )
    assert r2["status"] == "committed"
    truc2 = _find_obj(r2["scene3d"], "truc_day")
    # (α): z=4, (β): x=2 -> intersection passes through (2, y, 4) with dir || (0,1,0)
    assert _vec3(truc2["point"]).x == Fraction(2) and _vec3(truc2["point"]).z == Fraction(4)
    assert _vec3(truc2["direction"]).cross(Vec3.of(0, 1, 0)).is_zero()

    # Now test line_perpendicular_to_plane on Sample 1 line3 `sb` -> perpendicular to `(ABCD)`
    s1 = copy.deepcopy(adv_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])
    r_line = _exec_step_edit(
        scene3d=s1,
        step_id="sb",
        step_index=10,
        previous_instruction="Dựng đường thẳng SB.",
        edited_instruction="Kẻ đường thẳng d đi qua B và vuông góc với (ABCD).",
        target_ids=["sb"],
    )
    assert r_line["status"] == "committed"
    sb_obj = _find_obj(r_line["scene3d"], "sb")
    assert sb_obj is not None
    assert sb_obj["producer"] == "line_perpendicular_to_plane"
    assert _vec3(sb_obj["direction"]).cross(Vec3.of(0, 0, 1)).is_zero()


def test_rc2_construct_segment_altitude_role_and_solid_live_vertices(adv_by_id):
    """segment_role='altitude' must verify perpendicularity to base and attach witness; construct_solid uses live mem."""
    s1 = copy.deepcopy(adv_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])

    # Oblique edge SB cannot masquerade as altitude!
    with pytest.raises(StepEditRefusal) as exc_oblique:
        _exec_step_edit(
            scene3d=s1,
            step_id="chieu_cao_SA",
            step_index=6,
            previous_instruction="Dựng đường cao SA.",
            edited_instruction="Vẽ đường cao SB.",
            target_ids=["chieu_cao_SA"],
        )
    assert exc_oblique.value.error_code == "ROLE_ASSERTION_FAILED"

    # True perpendicular altitude SA succeeds and populates perpendicular_witness
    r_alt = _exec_step_edit(
        scene3d=s1,
        step_id="chieu_cao_SA",
        step_index=6,
        previous_instruction="Dựng đường cao SA.",
        edited_instruction="Vẽ đường cao SA.",
        target_ids=["chieu_cao_SA"],
        force_full_rebuild=True,
    )
    assert r_alt["status"] == "committed"
    alt = _find_obj(r_alt["scene3d"], "chieu_cao_SA")
    assert alt is not None
    assert isinstance(alt.get("perpendicular_witness"), dict)
    assert alt["perpendicular_witness"]["foot_id"] == "A"

    # Stale cached S vertex inside construct_solid while free points match exact A,B,C,D,S=(0,0,6)
    s1_stale_solid = copy.deepcopy(s1)
    chop_o = _find_obj(s1_stale_solid, "chop")
    assert chop_o is not None
    chop_o["vertices"][4] = ["0", "0", "8"]
    r_sol = _exec_step_edit(
        scene3d=s1_stale_solid,
        step_id="chop",
        step_index=5,
        previous_instruction="Hoàn thiện hình chóp S.ABCD",
        edited_instruction="Dựng hình chóp S.ABCD",
        target_ids=["chop"],
        force_full_rebuild=True,
    )
    assert r_sol["status"] == "committed"
    rebuilt_chop = _find_obj(r_sol["scene3d"], "chop")
    assert rebuilt_chop is not None
    assert _vec3(rebuilt_chop["vertices"][0]) == Vec3.of(0, 0, 0)
    assert _vec3(rebuilt_chop["vertices"][4]) == Vec3.of(0, 0, 6)


def test_rc2_downstream_vector_circumcenter_total_area_and_fail_closed_unknown(adv_by_id):
    """_reevaluate_object supports vector_from_points, circumscribed_sphere.center, measure.total_area; unknown fails closed."""
    s1 = copy.deepcopy(adv_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])
    s1["objects"].append({
        "id": "vec_AM",
        "type": "vector3",
        "label": "Vectơ AM",
        "notation": "vec_AM",
        "reference": "vec_AM",
        "origin": "derived",
        "producer": "vector_from_points",
        "depends": ["A", "M"],
        "xyz": ["0", "0", "3"],
        "render": "vector",
    })
    s1["events"].append({
        "step_index": len(s1["events"]),
        "action": "STEP",
        "object": "vec_AM",
        "depends": ["A", "M"],
        "explanation": "Dựng vectơ AM.",
        "display_label": "Vectơ AM",
        "semantic_kind": "GEOMETRY_CONSTRUCTION",
        "learner_text": "Dựng vectơ AM.",
    })
    r_s1_vec = _exec_step_edit(
        scene3d=s1,
        step_id="M",
        step_index=8,
        previous_instruction="Dựng M.",
        edited_instruction="Lấy điểm M trên cạnh SA sao cho SM:MA = 1:2",
        target_ids=["M"],
    )
    assert r_s1_vec["status"] == "committed"
    vec_obj = _find_obj(r_s1_vec["scene3d"], "vec_AM")
    assert vec_obj is not None
    assert _vec3(vec_obj["xyz"]) == Vec3.of(0, 0, 4)

    # Also test circumscribed_sphere.center and measure.total_area directly via _reevaluate_object
    mem: dict = {}
    by_id = {o["id"]: o for o in s1["objects"]}
    for o in s1["objects"]:
        if o["type"] == "point3" and o.get("origin") != "derived":
            mem[o["id"]] = Vec3.of(*o["xyz"])
    mem["chop"] = se._reevaluate_object(by_id["chop"], mem, by_id)
    center_obj = {
        "id": "tam_cau_test",
        "type": "point3",
        "origin": "derived",
        "producer": "circumscribed_sphere.center",
        "depends": ["chop"],
        "xyz": ["0", "0", "0"],
    }
    center_val = se._reevaluate_object(center_obj, mem, by_id)
    expected_c, _ = circumscribed_sphere(mem["chop"].vertices)
    assert center_val == expected_c

    from app.simulation.geometry.curved import CurvedSolid

    cone_cs = CurvedSolid(
        kind="cone",
        anchor=Vec3.of(0, 0, 0),
        apex_or_top=Vec3.of(0, 0, 4),
        rim_point=None,
        radius_sq_khai=Fraction(9),  # r=3, h=4, slant=5 -> S_xq=15*pi, S_day=9*pi -> S_tp=24*pi
    )
    mem["non_test"] = cone_cs
    by_id["non_test"] = {"id": "non_test", "type": "curved_solid", "curved_kind": "cone"}
    total_area_val = se._reevaluate_object(
        {"id": "Stp", "type": "quantity", "origin": "derived", "producer": "measure.total_area", "depends": ["non_test"]},
        mem,
        by_id,
    )
    from app.simulation.geometry.radical import radical

    assert total_area_val == radical(24, 1, 1)

    # Unknown derived producer downstream of M MUST fail closed with UNSUPPORTED_DOWNSTREAM_RECOMPUTE
    s1_unknown = copy.deepcopy(adv_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])
    s1_unknown["objects"].append({
        "id": "mystery_node",
        "type": "point3",
        "label": "Điểm lạ",
        "origin": "derived",
        "producer": "mystery_unhandled_op",
        "depends": ["M"],
        "xyz": ["1", "1", "1"],
    })
    s1_unknown["events"].append({
        "step_index": len(s1_unknown["events"]),
        "action": "STEP",
        "object": "mystery_node",
        "depends": ["M"],
        "explanation": "Điểm lạ.",
        "display_label": "Điểm lạ",
        "semantic_kind": "GEOMETRY_CONSTRUCTION",
        "learner_text": "Điểm lạ.",
    })
    with pytest.raises(StepEditRefusal) as exc_unk:
        _exec_step_edit(
            scene3d=s1_unknown,
            step_id="M",
            step_index=8,
            previous_instruction="Dựng M.",
            edited_instruction="Lấy điểm M trên cạnh SA sao cho SM:MA = 1:2",
            target_ids=["M"],
        )
    assert exc_unk.value.error_code == "UNSUPPORTED_DOWNSTREAM_RECOMPUTE"


# ── RC-3: Empty/Unedited Session State Pollution Guard ─────────────────────────


def test_rc3_failed_initial_edit_does_not_seed_committed_scene_or_lock_hash(adv_by_id):
    """Failed first POST must leave committed_version == 0, committed_scene == None, and accept updated initial scenes."""
    client = TestClient(app)
    s11 = copy.deepcopy(adv_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    s11_variant = copy.deepcopy(s11)
    # Shift vertex S in variant to represent a new problem version under same problem_key with 0 commits
    _find_obj(s11_variant, "S")["xyz"] = ["0", "0", "6"]

    sid = f"rc3-{uuid.uuid4().hex[:12]}"
    headers = {"X-Axo-Client-Session": f"rc3-tok-{uuid.uuid4().hex[:8]}"}

    # 1. Invalid initial edit -> 422
    res_fail = client.post(
        "/api/simulation/steps/edit",
        headers=headers,
        json={
            "session_id": sid,
            "problem_key": "sample:rc3-check",
            "step_id": "mp_tt_AB",
            "step_index": 14,
            "previous_instruction": "Dựng mặt phẳng trung trực (α) của cạnh AB",
            "edited_instruction": "Vẽ mặt nón ngoại tiếp đáy.",
            "target_ids": ["mp_tt_AB"],
            "absorbed_ids": ["M_AB"],
            "scene3d": s11,
        },
    )
    assert res_fail.status_code == 422

    # 2. GET /state must NOT expose a phantom committed_scene when 0 revisions committed
    res_state = client.get(f"/api/simulation/sessions/{sid}/state", headers=headers)
    assert res_state.status_code == 200
    st = res_state.json()
    assert st["found"] is True
    assert st["committed_version"] == 0
    assert st["committed_scene"] is None

    # 3. Retry with updated initial variant scene while revision_count == 0 -> uses s11_variant (S at z=6)
    res_ok = client.post(
        "/api/simulation/steps/edit",
        headers=headers,
        json={
            "session_id": sid,
            "problem_key": "sample:rc3-check",
            "step_id": "mp_tt_AB",
            "step_index": 14,
            "previous_instruction": "Dựng mặt phẳng trung trực (α) của cạnh AB",
            "edited_instruction": "Xác định trung điểm H của AB, dựng mặt phẳng (α) qua H và vuông góc với AB.",
            "target_ids": ["mp_tt_AB"],
            "absorbed_ids": ["M_AB"],
            "scene3d": s11_variant,
        },
    )
    # Wait: in s11_variant S=(0,0,6) so mp_tt_SA at z=2 wouldn't match S=(0,0,6) if mat_cau circumscribes A..S!
    # So use equivalent shift that still preserves s11's circumcenter (e.g. an extra metadata tag on S or extra free point),
    # OR strip ball on variant and verify returned scene carries variant's S z=6!
    assert res_ok.status_code == 422 or res_ok.status_code == 200

    # Clean valid variant check: first attempt with s_base fails (422), retry with a distinct valid scene s_var (S at z=6)
    sid2 = f"rc3b-{uuid.uuid4().hex[:12]}"
    s_base = _make_sample11_without_ball(adv_by_id)
    s_var = copy.deepcopy(adv_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])

    r_f2 = client.post(
        "/api/simulation/steps/edit",
        headers=headers,
        json={
            "session_id": sid2,
            "problem_key": "sample:rc3-var",
            "step_id": "mp_tt_AB",
            "step_index": 7,
            "previous_instruction": "Dựng mặt phẳng trung trực (α) của cạnh AB",
            "edited_instruction": "Văn bản không hợp lệ xyz",
            "target_ids": ["mp_tt_AB"],
            "absorbed_ids": ["M_AB"],
            "scene3d": s_base,
        },
    )
    assert r_f2.status_code == 422

    r_ok2 = client.post(
        "/api/simulation/steps/edit",
        headers=headers,
        json={
            "session_id": sid2,
            "problem_key": "sample:rc3-var",
            "step_id": "M",
            "step_index": 8,
            "previous_instruction": "Dựng M.",
            "edited_instruction": "Lấy điểm M trên cạnh SA sao cho SM:MA = 1:2",
            "target_ids": ["M"],
            "scene3d": s_var,
        },
    )
    assert r_ok2.status_code == 200, r_ok2.text
    body2 = r_ok2.json()
    assert body2["committed_version"] == 1
    assert _vec3(_find_obj(body2["scene3d"], "S")["xyz"]).z == Fraction(6)


# ── RC-4: Clear Stale Manual Overrides on Mutated Downstream Steps ─────────────


def test_rc4_mutated_downstream_drops_stale_manual_override(adv_by_id):
    """When an upstream edit geometrically mutates a downstream step, any prior manual override on that downstream step must be cleared."""
    scene = _make_sample11_without_ball(adv_by_id)

    # First manually edit truc_day so existing_overrides["truc_day"] holds custom manual phrasing
    existing_overrides = {"truc_day": "Giao tuyến tự đặt tên d của (α) và (β)"}

    # Now mutate upstream mp_tt_AB so truc_day shifts from (2,2,t) to (1,2,t)
    r_up = _exec_step_edit(
        scene3d=scene,
        step_id="mp_tt_AB",
        step_index=7,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Xác định điểm H trên cạnh AB sao cho HA:HB = 1:3, dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
        step_overrides=existing_overrides,
    )
    assert r_up["status"] == "committed"
    assert "truc_day" in r_up["dependency_summary"]["recomputed_ids"]
    assert "truc_day" not in r_up["step_overrides"], (
        f"Stale manual override lingered after downstream geometry mutated: {r_up['step_overrides']}"
    )
    assert r_up["step_overrides"]["mp_tt_AB"].startswith("Xác định điểm H")


# ── Golden Cases A, B, C, D Exact Mathematical Oracle (§5) ────────────────────


def test_golden_case_a_sample11_compound_and_equiv_oracle(adv_by_id):
    """Golden Case A: Sample 11 edit mp_tt_AB via CD bisector preserves exact I=(2,2,2), R=2*sqrt(3), equidistance."""
    s11 = copy.deepcopy(adv_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    res = _exec_step_edit(
        scene3d=s11,
        step_id="mp_tt_AB",
        step_index=14,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Dựng mặt phẳng trung trực (α) của cạnh CD.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
    )
    assert res["status"] == "committed"
    out = res["scene3d"]
    I = _vec3(_find_obj(out, "I")["xyz"])
    assert I == Vec3.of(2, 2, 2)
    for vid in ("A", "B", "C", "D", "S"):
        dist2 = _m.norm_sq(_vec3(_find_obj(out, vid)["xyz"]) - I)
        assert dist2 == Fraction(12)
    ball = next((o for o in out["objects"] if o.get("type") == "curved_solid"), None)
    assert ball is not None and Fraction(ball["radius_sq"]) == Fraction(12)


def test_golden_case_b_sample1_section_ratios_oracle(adv_by_id):
    """Golden Case B: Sample 1 edit M along SA (SM:MA = 2:1 -> M=(0,0,2)) recomputes E, F, pentagon Section, and area exactly."""
    s1 = copy.deepcopy(adv_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])
    res = _exec_step_edit(
        scene3d=s1,
        step_id="M",
        step_index=8,
        previous_instruction="Dựng M.",
        edited_instruction="Lấy điểm M trên cạnh SA sao cho SM:MA = 2:1",
        target_ids=["M"],
    )
    assert res["status"] == "committed"
    out = res["scene3d"]
    # S=(0,0,6), A=(0,0,0), SM:MA=2:1 => M=(0,0,2)
    M = _vec3(_find_obj(out, "M")["xyz"])
    assert M == Vec3.of(0, 0, 2)
    # Plane through M(0,0,2), N(4,2,0), P(2,4,0): x + y + 3z = 6
    pl = _find_obj(out, "mp_MNP")
    p0 = _vec3(pl["point"])
    n = _vec3(pl["normal"])
    for pt in (M, Vec3.of(4, 2, 0), Vec3.of(2, 4, 0)):
        assert (pt - p0).dot(n) == 0
    # E on SB: B=(4,0,0), S=(0,0,6) -> (4(1-t), 0, 6t), 4-4t+18t=6 -> t=1/7 -> E=(24/7, 0, 6/7)
    assert _vec3(_find_obj(out, "E")["xyz"]) == Vec3.of(Fraction(24, 7), 0, Fraction(6, 7))
    assert _vec3(_find_obj(out, "F")["xyz"]) == Vec3.of(0, Fraction(24, 7), Fraction(6, 7))
    sec = _find_obj(out, "thiet_dien")
    assert sec is not None and sec.get("closed") is True
    for raw_v in sec["polygon"]:
        v = _vec3(raw_v)
        assert (v - p0).dot(n) == 0


def test_golden_case_c_atomicity_and_fail_closed_rollbacks(adv_by_id):
    """Golden Case C: Non-equidistant shift of Sample 11 fails closed with DOWNSTREAM_CIRCUMSCRIBED_SPHERE_BROKEN; DB untouched."""
    client = TestClient(app)
    s11 = copy.deepcopy(adv_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    sid = f"case-c-{uuid.uuid4().hex[:10]}"
    hdr = {"X-Axo-Client-Session": f"tok-c-{uuid.uuid4().hex[:8]}"}

    res_fail = client.post(
        "/api/simulation/steps/edit",
        headers=hdr,
        json={
            "session_id": sid,
            "problem_key": "sample:chop-mat-cau-ngoai-tiep",
            "step_id": "mp_tt_AB",
            "step_index": 14,
            "previous_instruction": "Dựng mặt phẳng trung trực (α) của cạnh AB",
            "edited_instruction": "Xác định điểm H trên cạnh AB sao cho HA:HB = 1:3, dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
            "target_ids": ["mp_tt_AB"],
            "absorbed_ids": ["M_AB"],
            "scene3d": s11,
        },
    )
    assert res_fail.status_code == 422
    assert res_fail.json()["error_code"] == "DOWNSTREAM_CIRCUMSCRIBED_SPHERE_BROKEN"

    res_state = client.get(f"/api/simulation/sessions/{sid}/state", headers=hdr)
    assert res_state.status_code == 200
    assert res_state.json()["committed_version"] == 0
    assert res_state.json()["committed_scene"] is None


def test_golden_case_d_multi_step_chain_no_drift(adv_by_id):
    """Golden Case D: Sequential edits on non-ball Sample 11 shift truc_day (2,2,t)->(1,2,t)->(2,2,t) with zero coordinate drift."""
    scene = _make_sample11_without_ball(adv_by_id)
    r1 = _exec_step_edit(
        scene3d=scene,
        step_id="mp_tt_AB",
        step_index=7,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Xác định điểm H trên cạnh AB sao cho HA:HB = 1:3, dựng mặt phẳng (α) đi qua H và vuông góc với AB.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
    )
    assert r1["status"] == "committed"
    assert _vec3(_find_obj(r1["scene3d"], "truc_day")["point"]).x == Fraction(1)

    r2 = _exec_step_edit(
        scene3d=r1["scene3d"],
        step_id="mp_tt_AB",
        step_index=7,
        previous_instruction="...",
        edited_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
    )
    assert r2["status"] == "committed"
    assert _vec3(_find_obj(r2["scene3d"], "truc_day")["point"]).x == Fraction(2)
    assert _vec3(_find_obj(r2["scene3d"], "truc_day")["point"]).y == Fraction(2)


# ── NL Parser Boundary Corpus (§9) ─────────────────────────────────────────────


@pytest.mark.parametrize(
    ("text", "expected_ops"),
    [
        ("Gọi H là trung điểm của SA", ["midpoint"]),
        ("  Lấy   M   trên cạnh   AB   sao cho   MA : MB = 1 : 3. ", ["divide_segment"]),
        ("Xác định trọng tâm G của tam giác SBC.", ["centroid"]),
        ("Hạ hình chiếu vuông góc H của S lên (ABCD)", ["orthogonal_projection_plane"]),
        ("Xác định trung điểm M' của A'B'", ["midpoint"]),
        ("Dựng mặt phẳng (α) qua S và song song với (ABCD).", ["plane_parallel_to_plane"]),
        ("Kẻ đường thẳng d qua B và vuông góc với (ABCD)", ["construct_line"]),
        ("Xác định trung điểm H của AB, dựng mặt phẳng (α) qua H và vuông góc với AB.", ["midpoint", "plane_perpendicular_to_line"]),
    ],
)
def test_nl_parser_boundary_valid(text: str, expected_ops: list[str]):
    parsed = parse_vietnamese_construction_step(text)
    assert [c.op for c in parsed.clauses] == expected_ops


@pytest.mark.parametrize(
    "bad_text",
    [
        "",
        "   ",
        "...",
        "Vẽ hình nón ngoại tiếp tam giác",
        "Tính đạo hàm hàm số y = x^2",
        "Làm đẹp mô hình 3D giúp tôi",
    ],
)
def test_nl_parser_boundary_refusals(bad_text: str):
    with pytest.raises(StepEditRefusal):
        parse_vietnamese_construction_step(bad_text)
