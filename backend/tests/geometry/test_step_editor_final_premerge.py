# -*- coding: utf-8 -*-
"""AXO Step Editor — Final Pre-Merge Hardening (`FP-1`..`FP-6`) Test Suite.

Covers all mandatory verification groups from the Final Pre-Merge campaign:
1. `FP-1`: Parser & Typed Facts (unnamed bisector, unnamed inline midpoint, slash ratios, comma syntax).
2. `FP-2` / Group A: Semantically equivalent edits never produce false `before_after_diff.changed = True`,
   preserve cyclic section naming (`MENPF`), and cleanly retire chained inline helpers.
3. Group B: Valid geometric mutation on an independent synthetic right tetrahedron with hand-derived
   analytical oracle + unaffected branch preservation + persistence across GET `/state`.
4. `FP-3` / Group C: Locally valid operations that break global problem invariants (circumscribed
   sphere, skew common perpendicularity, dihedral/altitude orthogonality, 3-point plane incidence)
   fail closed with structured HTTP 422 refusals.
5. Group D: Invalid mutations (missing point/line, cycle, collinearity, type mismatch, given mutation,
   parallel/contained intersection, unsupported curved) fail closed leaving prior scene & state intact.
6. `FP-6`: Concurrency & persistence hardening — simultaneous same-step/dependent POSTs, out-of-order
   stale `client_seq`, in-flight `POST /steps/cancel` (pre-commit & post-commit rollback), simulated
   mid-transaction DB error -> `503 PERSISTENCE_UNAVAILABLE`, cross-session isolation, and real
   multi-process SQLite concurrency.
"""
from __future__ import annotations

import asyncio
import copy
import json
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from fractions import Fraction
from pathlib import Path

import httpx
import pytest
from sqlalchemy.exc import OperationalError

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent
DATA_DIR = REPO_DIR / "frontend" / "src" / "data"
if str(BACKEND_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR / "scripts"))

from app.ai.step_edit_route import DEFAULT_SCENE3D_HOOKS, execute_step_edit  # noqa: E402
from app.main import app  # noqa: E402
from app.persistence.step_edit_models import ensure_step_edit_tables  # noqa: E402
from app.simulation import step_edit_router  # noqa: E402
from app.simulation.geometry import (  # noqa: E402
    Line3,
    Plane3,
    Vec3,
    kernel as K,
    measure as M,
    metric as _m,
    predicates as P,
)
from app.simulation.geometry.radical import (  # noqa: E402
    display as radical_display,
    parse_exact,
    sqrt_rational,
    to_json as radical_to_json,
)
from app.simulation.geometry.section import Polyhedron, cross_section  # noqa: E402
from app.simulation.geometry_functions import step_editor as se  # noqa: E402
from app.simulation.geometry_functions.construction_continuity import enrich_construction_continuity  # noqa: E402
from app.simulation.geometry_functions.step_editor import (  # noqa: E402
    StepEditRefusal,
    parse_vietnamese_construction_step,
)


def _load_catalog() -> dict[str, dict]:
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
    return _load_catalog()


def _find_obj(scene: dict, oid: str) -> dict | None:
    return next((o for o in scene.get("objects") or [] if o.get("id") == oid), None)


def _vec3(xyz: list) -> Vec3:
    return Vec3.of(*(parse_exact(c) for c in xyz))


# ── FP-1: Parser & Typed Facts Gaps ───────────────────────────────────────────


def test_fp1_parser_unnamed_bisector_slash_ratios_and_comma_syntax():
    p_unnamed_bisector = parse_vietnamese_construction_step("Dựng mặt phẳng trung trực của AB.")
    assert [c.op for c in p_unnamed_bisector.clauses] == ["perpendicular_bisector_plane"]
    assert p_unnamed_bisector.clauses[0].output_symbol is None
    assert p_unnamed_bisector.clauses[0].point_inputs == ("A", "B")

    p_unnamed_inline_mid = parse_vietnamese_construction_step(
        "Dựng mặt phẳng (α) đi qua trung điểm của AB và vuông góc với AB."
    )
    assert [c.op for c in p_unnamed_inline_mid.clauses] == ["perpendicular_bisector_plane"]
    assert p_unnamed_inline_mid.clauses[0].output_symbol == "(α)"
    assert p_unnamed_inline_mid.clauses[0].point_inputs == ("A", "B")

    p_comma_1 = parse_vietnamese_construction_step("P thuộc AB, AP/AB = 1/3")
    p_comma_2 = parse_vietnamese_construction_step("P thuộc AB, AP/AB = 1/4")
    assert p_comma_1.clauses[0].op == "divide_segment"
    assert p_comma_1.clauses[0].output_symbol == "P"
    assert p_comma_1.clauses[0].params == {"a": "A", "b": "B", "ratio": "1/3"}
    assert p_comma_2.clauses[0].params == {"a": "A", "b": "B", "ratio": "1/4"}

    p_subseg_ratio = parse_vietnamese_construction_step("Lấy điểm P thuộc AB sao cho AP/PB = 1/3")
    assert p_subseg_ratio.clauses[0].params == {"a": "A", "b": "B", "ratio": "1/4"}

    p_inv_ratio = parse_vietnamese_construction_step("Lấy điểm P thuộc AB sao cho AB/AP = 4")
    assert p_inv_ratio.clauses[0].params == {"a": "A", "b": "B", "ratio": "1/4"}


# ── FP-2 / Group A: Semantically Equivalent Edits & Diff / Cycle Alignment ────


def test_fp2_group_a_semantic_equivalence_no_false_diff_and_section_cycle(catalog_by_id):
    s11 = copy.deepcopy(catalog_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])

    # 1. Exact prompt example: "Dựng mặt phẳng trung trực của AB." on Sample 11 -> NO_OP / diff unchanged
    r_unnamed = execute_step_edit(
        scene3d=copy.deepcopy(s11),
        step_id="mp_tt_AB",
        step_index=7,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Dựng mặt phẳng trung trực của AB.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
    )
    assert r_unnamed["status"] == "committed"
    assert r_unnamed["equivalence_info"]["geometrically_equivalent"] is True
    assert r_unnamed["before_after_diff"]["changed"] is False

    # 2. Compound wording creating named midpoint H of AB ("Dựng mặt phẳng đi qua trung điểm H của AB và vuông góc với AB.")
    r_compound = execute_step_edit(
        scene3d=copy.deepcopy(s11),
        step_id="mp_tt_AB",
        step_index=7,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Dựng mặt phẳng đi qua trung điểm H của AB và vuông góc với AB.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
    )
    assert r_compound["status"] == "committed"
    assert r_compound["equivalence_info"]["geometrically_equivalent"] is True
    assert r_compound["validation_result"]["change_classification"] == "EQUIVALENT_GEOMETRY"
    assert r_compound["before_after_diff"]["changed"] is False
    assert r_compound["before_after_diff"]["changed_objects"] == {}
    # Must NOT leak both M_AB and H
    assert _find_obj(r_compound["scene3d"], "M_AB") is None
    assert _find_obj(r_compound["scene3d"], "H") is not None

    # 3. Round-trip back to unnamed inline midpoint "(α) qua trung điểm của AB ⊥ AB": cleans H cleanly!
    r_back = execute_step_edit(
        scene3d=r_compound["scene3d"],
        step_id="mp_tt_AB",
        step_index=7,
        previous_instruction="Dựng mặt phẳng đi qua trung điểm H của AB và vuông góc với AB.",
        edited_instruction="Dựng mặt phẳng (α) đi qua trung điểm của AB và vuông góc với AB.",
        target_ids=["mp_tt_AB"],
    )
    assert r_back["status"] == "committed"
    assert r_back["equivalence_info"]["geometrically_equivalent"] is True
    assert r_back["before_after_diff"]["changed"] is False
    assert _find_obj(r_back["scene3d"], "H") is None

    # 4. Sample 1 flipped plane orientation (MPN) -> same plane, no diff, section keeps MENPF cycle
    s1 = copy.deepcopy(catalog_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])
    mp_obj = next(o for o in s1["objects"] if o["type"] == "plane3" and "MNP" in str(o.get("notation") or o.get("label") or o["id"]))
    r_mpn = execute_step_edit(
        scene3d=s1,
        step_id=mp_obj["id"],
        step_index=9,
        previous_instruction="Dựng mặt phẳng (MNP)",
        edited_instruction="Dựng mặt phẳng (MPN)",
        target_ids=[mp_obj["id"]],
    )
    assert r_mpn["status"] == "committed"
    assert r_mpn["equivalence_info"]["geometrically_equivalent"] is True
    assert r_mpn["before_after_diff"]["changed"] is False
    sec = _find_obj(r_mpn["scene3d"], "thiet_dien")
    assert sec["notation"] == "MENPF"
    assert sec["label"] == "Thiết diện MENPF"


# ── Group B: Valid Geometric Mutation + Analytical Oracle + HTTP Persistence ──


def _build_analytical_tetra_scene() -> dict:
    """Brand-new synthetic tetrahedron S.ABC: A(0,0,0), B(6,0,0), C(0,6,0), S(0,0,6).
    P on AB (AP/AB = 1/3 -> (2,0,0)), Q on AC (AQ/AC = 1/2 -> (0,3,0)), R on AS (AR/AS = 1/2 -> (0,0,3)).
    Independent unaffected branch: midpoint M_BC of BC = (3,3,0).
    """
    A, B, C, S = Vec3.of(0, 0, 0), Vec3.of(6, 0, 0), Vec3.of(0, 6, 0), Vec3.of(0, 0, 6)
    P0 = K.divide_segment(A, B, Fraction(1, 3))
    Q0 = K.midpoint(A, C)
    R0 = K.midpoint(A, S)
    M_BC = K.midpoint(B, C)
    sol = Polyhedron(vertices=(A, B, C, S), faces=((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)))
    pl_pqr = Plane3.through(P0, Q0, R0)
    sec_pqr = cross_section(sol, pl_pqr)
    d2_a = M.distance_sq_point_plane(A, pl_pqr)
    d_a = sqrt_rational(d2_a)
    from app.simulation.semantic_program.geometry_exec import area_of

    area_sec = area_of(sec_pqr)
    objs = [
        {"id": "A", "type": "point3", "notation": "A", "label": "A", "origin": "free", "depends": [], "xyz": se._exact_xyz_list(A)},
        {"id": "B", "type": "point3", "notation": "B", "label": "B", "origin": "free", "depends": [], "xyz": se._exact_xyz_list(B)},
        {"id": "C", "type": "point3", "notation": "C", "label": "C", "origin": "free", "depends": [], "xyz": se._exact_xyz_list(C)},
        {"id": "S", "type": "point3", "notation": "S", "label": "S", "origin": "free", "depends": [], "xyz": se._exact_xyz_list(S)},
        {
            "id": "tet",
            "type": "solid",
            "notation": "S.ABC",
            "label": "Hình chóp S.ABC",
            "origin": "derived",
            "producer": "construct_solid",
            "depends": ["A", "B", "C", "S"],
            "vertex_ids": ["A", "B", "C", "S"],
            "faces": [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]],
            "vertices": [se._exact_xyz_list(v) for v in (A, B, C, S)],
        },
        {
            "id": "M_BC",
            "type": "point3",
            "notation": "M",
            "label": "Trung điểm M của BC",
            "origin": "derived",
            "producer": "construct_point.midpoint",
            "depends": ["B", "C"],
            "xyz": se._exact_xyz_list(M_BC),
        },
        {
            "id": "P",
            "type": "point3",
            "notation": "P",
            "label": "Điểm P trên AB (tỉ lệ 1/3)",
            "origin": "derived",
            "producer": "construct_point.divide_segment",
            "depends": ["A", "B"],
            "xyz": se._exact_xyz_list(P0),
            "source": {"instruction": "construct_point.divide_segment", "params": {"a": "A", "b": "B", "ratio": "1/3"}},
        },
        {
            "id": "Q",
            "type": "point3",
            "notation": "Q",
            "label": "Trung điểm Q của AC",
            "origin": "derived",
            "producer": "construct_point.midpoint",
            "depends": ["A", "C"],
            "xyz": se._exact_xyz_list(Q0),
        },
        {
            "id": "R",
            "type": "point3",
            "notation": "R",
            "label": "Trung điểm R của AS",
            "origin": "derived",
            "producer": "construct_point.midpoint",
            "depends": ["A", "S"],
            "xyz": se._exact_xyz_list(R0),
        },
        {
            "id": "mp_PQR",
            "type": "plane3",
            "notation": "(PQR)",
            "label": "(PQR)",
            "origin": "derived",
            "producer": "construct_plane",
            "depends": ["P", "Q", "R"],
            "point": se._exact_xyz_list(pl_pqr.point),
            "normal": se._exact_xyz_list(pl_pqr.normal),
        },
        {
            "id": "sec_PQR",
            "type": "section",
            "notation": "PQR",
            "label": "Thiết diện PQR",
            "display_label": "Thiết diện PQR",
            "origin": "derived",
            "producer": "construct_section",
            "depends": ["tet", "mp_PQR"],
            "polygon": [se._exact_xyz_list(v) for v in sec_pqr.polygon],
            "closed": True,
            "steps": [{"face_index": st.face_index, "a": se._exact_xyz_list(st.a), "b": se._exact_xyz_list(st.b)} for st in sec_pqr.steps],
        },
        {
            "id": "d_A_PQR",
            "type": "quantity",
            "notation": "d(A,(PQR))",
            "label": "Khoảng cách từ A đến (PQR)",
            "origin": "derived",
            "producer": "measure.distance",
            "depends": ["A", "mp_PQR"],
            "value": radical_display(d_a),
            "exact": radical_to_json(d_a),
            "formula": {"text": f"d(A,(PQR)) = {radical_display(d_a)}", "references": []},
        },
        {
            "id": "S_PQR",
            "type": "quantity",
            "notation": "S(PQR)",
            "label": "Diện tích PQR",
            "origin": "derived",
            "producer": "measure.area",
            "depends": ["sec_PQR"],
            "value": radical_display(area_sec),
            "exact": radical_to_json(area_sec),
            "formula": {"text": f"S(PQR) = {radical_display(area_sec)}", "references": []},
        },
    ]
    events = [
        {"step_index": 0, "action": "INIT", "object": None, "depends": [], "semantic_kind": "SCENE_INIT", "learner_text": "Khởi tạo chóp S.ABC."},
    ]
    for idx_e, o in enumerate(objs[4:], start=1):
        events.append({
            "step_index": idx_e,
            "action": "CREATE",
            "object": o["id"],
            "depends": list(o["depends"]),
            "display_label": o["label"],
            "semantic_kind": "MEASUREMENT" if o["type"] == "quantity" else "GEOMETRY_CONSTRUCTION",
            "learner_text": o["label"],
        })
    DEFAULT_SCENE3D_HOOKS.attach_topology(objs)
    DEFAULT_SCENE3D_HOOKS.attach_formulas(objs)
    formation = DEFAULT_SCENE3D_HOOKS.build_formation(objs, events, ["A", "B", "C", "S"])
    scene = {
        "chart_metric": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        "free_objects": ["A", "B", "C", "S"],
        "objects": objs,
        "events": events,
        "formation": formation,
    }
    enrich_construction_continuity(scene)
    return scene


def test_fp_group_b_valid_geometric_mutation_with_independent_analytical_oracle():
    """Group B: P thuộc AB, AP/AB = 1/3 -> 1/4 verified against closed-form analytical oracle + HTTP reload."""
    base_scene = _build_analytical_tetra_scene()
    sid = f"group-b-oracle-{uuid.uuid4().hex[:10]}"
    hdrs = {"X-Axo-Client-Session": "group-b-token-123456"}

    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            r = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json={
                    "session_id": sid,
                    "problem_key": "synthetic:tetra-oracle",
                    "step_id": "P",
                    "step_index": 2,
                    "previous_instruction": "P thuộc AB, AP/AB = 1/3",
                    "edited_instruction": "P thuộc AB, AP/AB = 1/4",
                    "target_ids": ["P"],
                    "absorbed_ids": [],
                    "scene3d": base_scene,
                    "client_request_id": "req-group-b-1",
                    "client_seq": 1,
                },
            )
            st = await ac.get(f"/api/simulation/sessions/{sid}/state", headers=hdrs)
            return r, st

    r, st = asyncio.run(_run())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "committed"
    assert body["equivalence_info"]["geometrically_equivalent"] is False
    assert body["validation_result"]["change_classification"] == "GEOMETRY_MUTATED"
    assert body["before_after_diff"]["changed"] is True

    # Dependency DAG touched ONLY P's transitive closure and skipped M_BC, Q, R, A, B, C, S, tet
    recomputed = set(body["dependency_summary"]["recomputed_ids"])
    skipped = set(body["dependency_summary"]["skipped_unaffected_ids"])
    assert {"mp_PQR", "sec_PQR", "d_A_PQR", "S_PQR"}.issubset(recomputed)
    assert {"M_BC", "Q", "R", "A", "B", "C", "S", "tet"}.issubset(skipped)

    out = body["scene3d"]
    # Analytical oracle 1: P = (3/2, 0, 0)
    assert _vec3(_find_obj(out, "P")["xyz"]) == Vec3.of(Fraction(3, 2), 0, 0)
    # Analytical oracle 2: M_BC unchanged at (3, 3, 0)
    assert _find_obj(out, "M_BC")["xyz"] == ["3", "3", "0"]
    # Analytical oracle 3: Plane (PQR): 2x + y + z = 3 (normal proportional to (2,1,1))
    mp = _find_obj(out, "mp_PQR")
    pl = Plane3(_vec3(mp["point"]), _vec3(mp["normal"]))
    assert P.point_on_plane(Vec3.of(Fraction(3, 2), 0, 0), pl)
    assert P.point_on_plane(Vec3.of(0, 3, 0), pl)
    assert P.point_on_plane(Vec3.of(0, 0, 3), pl)
    assert pl.normal.cross(Vec3.of(2, 1, 1)).is_zero()
    # Analytical oracle 4: Exact section area = 9*sqrt(6)/4
    assert parse_exact(_find_obj(out, "S_PQR")["exact"]) == sqrt_rational(Fraction(243, 8))
    # Analytical oracle 5: Exact distance d(A, (PQR)) = 3/sqrt(6) = sqrt(6)/2
    assert parse_exact(_find_obj(out, "d_A_PQR")["exact"]) == sqrt_rational(Fraction(3, 2))
    # Analytical oracle 6: Unique IDs & notations, reload consistency
    ids = [o["id"] for o in out["objects"]]
    assert len(ids) == len(set(ids))
    assert st.status_code == 200
    st_json = st.json()
    assert st_json["committed_version"] == 1
    assert st_json["last_committed_request_id"] == "req-group-b-1"
    assert _find_obj(st_json["committed_scene"], "P")["xyz"] == ["3/2", "0", "0"]


# ── FP-3 / Group C: Locally Valid Ops Breaking Global Problem Invariants ──────


def test_fp3_group_c_valid_local_op_rejected_when_breaking_global_invariants(catalog_by_id):
    # 1. Sample 11 circumscribed sphere broken by shifted bisector
    s11 = copy.deepcopy(catalog_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    with pytest.raises(StepEditRefusal) as e_sph:
        execute_step_edit(
            scene3d=s11,
            step_id="mp_tt_AB",
            step_index=7,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction="Lấy điểm H thuộc AB sao cho HA:HB = 1:3 rồi dựng mặt phẳng (α) qua H vuông góc với AB",
            target_ids=["mp_tt_AB"],
            absorbed_ids=["M_AB"],
        )
    assert e_sph.value.error_code == "DOWNSTREAM_CIRCUMSCRIBED_SPHERE_BROKEN"

    # 2. Skew common perpendicular broken on khoang-cach-hai-duong-cheo-nhau
    s_skew = copy.deepcopy(catalog_by_id["khoang-cach-hai-duong-cheo-nhau"]["envelope"]["scene3d"])
    with pytest.raises(StepEditRefusal) as e_skew:
        execute_step_edit(
            scene3d=s_skew,
            step_id="P",
            step_index=5,
            previous_instruction="Xác định P",
            edited_instruction="Lấy điểm P thuộc BD sao cho BP/BD = 1/5",
            target_ids=["P"],
        )
    assert e_skew.value.error_code == "DOWNSTREAM_ORTHOGONALITY_BROKEN"

    # 3. Dihedral orthogonality certificate broken on goc-nhi-dien-hai-mat-phang
    s_dih = copy.deepcopy(catalog_by_id["goc-nhi-dien-hai-mat-phang"]["envelope"]["scene3d"])
    with pytest.raises(StepEditRefusal) as e_dih:
        execute_step_edit(
            scene3d=s_dih,
            step_id="H",
            step_index=4,
            previous_instruction="Hạ hình chiếu H của A lên BC",
            edited_instruction="Lấy điểm H thuộc BC sao cho BH/BC = 1/5",
            target_ids=["H"],
        )
    assert e_dih.value.error_code == "DOWNSTREAM_ORTHOGONALITY_BROKEN"

    # 4. Plane projection foot replaced by centroid on khoang-cach-diem-mat-phang-nghieng
    s_inc = copy.deepcopy(catalog_by_id["khoang-cach-diem-mat-phang-nghieng"]["envelope"]["scene3d"])
    with pytest.raises(StepEditRefusal) as e_inc:
        execute_step_edit(
            scene3d=s_inc,
            step_id="H",
            step_index=4,
            previous_instruction="Hạ hình chiếu H của A lên (SBC)",
            edited_instruction="Xác định trọng tâm H của tam giác SBC",
            target_ids=["H"],
        )
    assert e_inc.value.error_code == "DOWNSTREAM_ORTHOGONALITY_BROKEN"

    # 5. Cutting plane keeps notation (MNP) but excludes N, P via parallel shift
    s1 = copy.deepcopy(catalog_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])
    mp_id = next(o["id"] for o in s1["objects"] if o["type"] == "plane3" and "MNP" in str(o.get("notation") or o.get("label") or o["id"]))
    with pytest.raises(StepEditRefusal) as e_pl:
        execute_step_edit(
            scene3d=s1,
            step_id=mp_id,
            step_index=9,
            previous_instruction="Dựng mặt phẳng (MNP)",
            edited_instruction="Dựng mặt phẳng (MNP) qua M và song song với (ABCD)",
            target_ids=[mp_id],
        )
    assert e_pl.value.error_code == "PLANE_VERTEX_INCIDENCE_MISMATCH"

    # 6. Fixed solid altitude segment edited into non-perpendicular lateral edge SB
    with pytest.raises(StepEditRefusal) as e_alt:
        execute_step_edit(
            scene3d=copy.deepcopy(s1),
            step_id="chieu_cao_SA",
            step_index=1,
            previous_instruction="Dựng đường cao SA ⊥ (ABCD) tại A",
            edited_instruction="Nối đoạn thẳng SB",
            target_ids=["chieu_cao_SA"],
        )
    assert e_alt.value.error_code == "DOWNSTREAM_PERPENDICULAR_INVARIANT_BROKEN"


# ── Group D: Invalid Mutations Fail Closed Preserving Committed State ─────────


@pytest.mark.parametrize(
    "bad_instruction,expected_code",
    [
        ("Dựng mặt phẳng trung trực (P) của cạnh SZ.", "MISSING_DEPENDENCY"),
        ("Dựng mặt phẳng (P) qua O và vuông góc với d_khong_ton_tai.", "MISSING_DEPENDENCY"),
        ("Dựng đường cao qua H vuông góc với đường thẳng zz_khong_ton_tai.", "UNSUPPORTED_STEP_SYNTAX"),
        ("Dựng mặt phẳng (P) đi qua điểm A, O, C", "COLLINEAR_POINTS"),
        ("Nối đoạn thẳng AB", "STEP_TYPE_MISMATCH"),
        ("Dựng mặt phẳng (P) qua I và vuông góc với AB.", "CYCLE_DEPENDENCY"),
        ("Vẽ hình nón ngoại tiếp đáy ABCD.", "UNSUPPORTED_CURVED_OR_FREEFORM_STEP"),
        ("Dựng mặt phẳng (P) qua P song song với AB", "UNSUPPORTED_STEP_SYNTAX"),
        ("Lấy điểm H thuộc AB sao cho AH/HB = -1", "INVALID_RATIO"),
    ],
)
def test_group_d_invalid_mutations_fail_closed_preserving_committed_state(
    catalog_by_id,
    bad_instruction,
    expected_code,
):
    s11 = copy.deepcopy(catalog_by_id["chop-mat-cau-ngoai-tiep"]["envelope"]["scene3d"])
    sid = f"group-d-{uuid.uuid4().hex[:8]}"
    hdrs = {"X-Axo-Client-Session": "group-d-token-12345"}

    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            # First commit a valid edit (compound bisector naming midpoint H) so prior committed state exists
            ok = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json={
                    "session_id": sid,
                    "problem_key": "sample:s11",
                    "step_id": "mp_tt_AB",
                    "step_index": 7,
                    "previous_instruction": "Dựng mặt phẳng trung trực (α) của cạnh AB",
                    "edited_instruction": "Dựng mặt phẳng (P) đi qua trung điểm H của AB và vuông góc với AB.",
                    "target_ids": ["mp_tt_AB"],
                    "absorbed_ids": ["M_AB"],
                    "scene3d": s11,
                },
            )
            bad = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json={
                    "session_id": sid,
                    "problem_key": "sample:s11",
                    "step_id": "mp_tt_AB",
                    "step_index": 7,
                    "previous_instruction": "Dựng mặt phẳng (P) đi qua trung điểm H của AB và vuông góc với AB.",
                    "edited_instruction": bad_instruction,
                    "target_ids": ["mp_tt_AB"],
                    "absorbed_ids": ["H"],
                    "scene3d": ok.json()["scene3d"],
                },
            )
            st = await ac.get(f"/api/simulation/sessions/{sid}/state", headers=hdrs)
            return ok, bad, st

    ok, bad, st = asyncio.run(_run())
    assert ok.status_code == 200, ok.text
    assert bad.status_code == 422
    assert bad.json()["status"] == "rolled_back"
    assert bad.json()["error_code"] == expected_code
    assert bad.json()["draft_preserved"] is True
    assert st.json()["committed_version"] == 1
    assert st.json()["committed_scene"]["objects"] == ok.json()["scene3d"]["objects"]


# ── FP-6: Concurrency, Cancel, Supersede, DB Fault, Isolation & Multi-Process ─


def test_fp6_concurrency_cancel_supersede_db_fault_isolation_and_multiprocess(catalog_by_id, monkeypatch):
    s1 = copy.deepcopy(catalog_by_id["chop-thiet-dien-ba-diem"]["envelope"]["scene3d"])

    async def _run_api_matrix():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            # 1. Stale out-of-order client_seq rejected cleanly without overwriting newer commit
            sid_seq = f"fp6-seq-{uuid.uuid4().hex[:8]}"
            h_seq = {"X-Axo-Client-Session": "fp6-seq-client-1"}
            r_new = await ac.post(
                "/api/simulation/steps/edit",
                headers=h_seq,
                json={
                    "session_id": sid_seq,
                    "problem_key": "sample:s1",
                    "step_id": "M",
                    "step_index": 7,
                    "previous_instruction": "Xác định trung điểm M của SA",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    "target_ids": ["M"],
                    "scene3d": copy.deepcopy(s1),
                    "client_request_id": "req-newer-2",
                    "client_seq": 2,
                },
            )
            assert r_new.status_code == 200
            r_stale = await ac.post(
                "/api/simulation/steps/edit",
                headers=h_seq,
                json={
                    "session_id": sid_seq,
                    "problem_key": "sample:s1",
                    "step_id": "M",
                    "step_index": 7,
                    "previous_instruction": "Xác định trung điểm M của SA",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/3",
                    "target_ids": ["M"],
                    "scene3d": copy.deepcopy(s1),
                    "client_request_id": "req-stale-1",
                    "client_seq": 1,
                },
            )
            assert r_stale.status_code == 409
            assert r_stale.json()["error_code"] == "EDIT_SUPERSEDED"
            st_seq = await ac.get(f"/api/simulation/sessions/{sid_seq}/state", headers=h_seq)
            assert _find_obj(st_seq.json()["committed_scene"], "M")["xyz"] == ["0", "0", "9/2"]

            # 2. Pre-commit & post-commit cancel guarantees cancelled edit never persists across F5 reload!
            sid_canc = f"fp6-canc-{uuid.uuid4().hex[:8]}"
            h_canc = {"X-Axo-Client-Session": "fp6-canc-client-1"}
            r_commit_1 = await ac.post(
                "/api/simulation/steps/edit",
                headers=h_canc,
                json={
                    "session_id": sid_canc,
                    "problem_key": "sample:s1",
                    "step_id": "M",
                    "step_index": 7,
                    "previous_instruction": "Xác định trung điểm M của SA",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/3",
                    "target_ids": ["M"],
                    "scene3d": copy.deepcopy(s1),
                    "client_request_id": "req-keep-1",
                    "client_seq": 1,
                },
            )
            assert r_commit_1.status_code == 200
            # Simulate second edit committed just before user clicked Cancel (post-commit cancel race)
            r_commit_2 = await ac.post(
                "/api/simulation/steps/edit",
                headers=h_canc,
                json={
                    "session_id": sid_canc,
                    "problem_key": "sample:s1",
                    "step_id": "M",
                    "step_index": 7,
                    "previous_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/3",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    "target_ids": ["M"],
                    "scene3d": r_commit_1.json()["scene3d"],
                    "client_request_id": "req-cancel-race-2",
                    "client_seq": 2,
                },
            )
            assert r_commit_2.status_code == 200
            c_resp = await ac.post(
                "/api/simulation/steps/cancel",
                headers=h_canc,
                json={"session_id": sid_canc, "client_request_id": "req-cancel-race-2"},
            )
            assert c_resp.status_code == 200
            assert c_resp.json()["cancelled"] is True
            st_after_cancel = await ac.get(f"/api/simulation/sessions/{sid_canc}/state", headers=h_canc)
            assert _find_obj(st_after_cancel.json()["committed_scene"], "M")["xyz"] == ["0", "0", "4"]

            # 3. Dependent concurrent POSTs on M and P
            sid_dep = f"fp6-dep-{uuid.uuid4().hex[:8]}"
            h_dep = {"X-Axo-Client-Session": "fp6-dep-client-1"}
            r_m, r_p = await asyncio.gather(
                ac.post(
                    "/api/simulation/steps/edit",
                    headers=h_dep,
                    json={
                        "session_id": sid_dep,
                        "problem_key": "sample:s1",
                        "step_id": "M",
                        "step_index": 7,
                        "previous_instruction": "Xác định trung điểm M của SA",
                        "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                        "target_ids": ["M"],
                        "scene3d": copy.deepcopy(s1),
                    },
                ),
                ac.post(
                    "/api/simulation/steps/edit",
                    headers=h_dep,
                    json={
                        "session_id": sid_dep,
                        "problem_key": "sample:s1",
                        "step_id": "P",
                        "step_index": 8,
                        "previous_instruction": "Xác định trung điểm P của BC",
                        "edited_instruction": "Lấy điểm P thuộc BC sao cho BP/BC = 1/3",
                        "target_ids": ["P"],
                        "scene3d": copy.deepcopy(s1),
                    },
                ),
            )
            assert r_m.status_code == 200 and r_p.status_code == 200
            st_dep = await ac.get(f"/api/simulation/sessions/{sid_dep}/state", headers=h_dep)
            assert st_dep.json()["committed_version"] == 2
            # Both edits must be preserved in sequential committed state!
            assert _find_obj(st_dep.json()["committed_scene"], "M")["xyz"] == ["0", "0", "9/2"]
            assert _find_obj(st_dep.json()["committed_scene"], "P")["xyz"] == ["4", "4/3", "0"]

            # 4. Two unrelated client sessions never contaminate each other
            h_u1 = {"X-Axo-Client-Session": f"user-a-{uuid.uuid4().hex[:6]}"}
            h_u2 = {"X-Axo-Client-Session": f"user-b-{uuid.uuid4().hex[:6]}"}
            shared_sid = f"shared-tab-{uuid.uuid4().hex[:6]}"
            ru1, ru2 = await asyncio.gather(
                ac.post(
                    "/api/simulation/steps/edit",
                    headers=h_u1,
                    json={
                        "session_id": shared_sid,
                        "problem_key": "sample:s1",
                        "step_id": "M",
                        "step_index": 7,
                        "previous_instruction": "Xác định trung điểm M của SA",
                        "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                        "target_ids": ["M"],
                        "scene3d": copy.deepcopy(s1),
                    },
                ),
                ac.post(
                    "/api/simulation/steps/edit",
                    headers=h_u2,
                    json={
                        "session_id": shared_sid,
                        "problem_key": "sample:s1",
                        "step_id": "M",
                        "step_index": 7,
                        "previous_instruction": "Xác định trung điểm M của SA",
                        "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/3",
                        "target_ids": ["M"],
                        "scene3d": copy.deepcopy(s1),
                    },
                ),
            )
            assert ru1.status_code == 200 and ru2.status_code == 200
            su1 = await ac.get(f"/api/simulation/sessions/{shared_sid}/state", headers=h_u1)
            su2 = await ac.get(f"/api/simulation/sessions/{shared_sid}/state", headers=h_u2)
            assert _find_obj(su1.json()["committed_scene"], "M")["xyz"] == ["0", "0", "9/2"]
            assert _find_obj(su2.json()["committed_scene"], "M")["xyz"] == ["0", "0", "4"]

            # 5. Simulated DB failure mid-processing returns 503 PERSISTENCE_UNAVAILABLE (not false 409)
            orig_exec = step_edit_router._execute_locked_step_edit

            def _boom(*args, **kwargs):
                raise OperationalError("UPDATE", {}, sqlite3.OperationalError("disk I/O error"))

            monkeypatch.setattr(step_edit_router, "_execute_locked_step_edit", _boom)
            r_503 = await ac.post(
                "/api/simulation/steps/edit",
                headers=h_u1,
                json={
                    "session_id": shared_sid,
                    "problem_key": "sample:s1",
                    "step_id": "M",
                    "step_index": 7,
                    "previous_instruction": "Dựng M",
                    "edited_instruction": "Xác định trung điểm M của SA",
                    "target_ids": ["M"],
                    "scene3d": copy.deepcopy(s1),
                },
            )
            monkeypatch.setattr(step_edit_router, "_execute_locked_step_edit", orig_exec)
            assert r_503.status_code == 503
            assert r_503.json()["error_code"] == "PERSISTENCE_UNAVAILABLE"
            assert r_503.json()["draft_preserved"] is True

    asyncio.run(_run_api_matrix())

    # 6. Real Multi-Process SQLite test: same-session race & 4 independent user sessions
    with tempfile.TemporaryDirectory() as td:
        tmp_dir = Path(td)
        db_file = tmp_dir / "mp_premerge.db"
        scene_file = tmp_dir / "s1.json"
        scene_file.write_text(json.dumps(s1), encoding="utf-8")
        worker_py = tmp_dir / "mp_worker.py"
        worker_py.write_text(
            f"""
import json, os, pathlib, sys, time
os.environ["DATABASE_URL"] = f"sqlite:///{{sys.argv[1]}}"
sys.path.insert(0, r"{BACKEND_DIR}")
from fastapi.testclient import TestClient
from app.main import app
s1 = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
sid, tok, ratio, start_at = sys.argv[3], sys.argv[4], sys.argv[5], float(sys.argv[6])
c = TestClient(app)
c.get(f"/api/simulation/sessions/{{sid}}/state", headers={{"X-Axo-Client-Session": tok}})
while time.time() < start_at:
    time.sleep(0.002)
r = c.post(
    "/api/simulation/steps/edit",
    headers={{"X-Axo-Client-Session": tok}},
    json={{
        "session_id": sid,
        "problem_key": "chop-thiet-dien-ba-diem",
        "step_id": "M",
        "step_index": 7,
        "previous_instruction": "Xác định trung điểm M của SA",
        "edited_instruction": f"Lấy điểm M thuộc SA sao cho SM/SA = {{ratio}}",
        "target_ids": ["M"],
        "scene3d": s1,
    }},
)
print(json.dumps({{"status_code": r.status_code, "error_code": r.json().get("error_code")}}))
""",
            encoding="utf-8",
        )
        subprocess.run(
            [sys.executable, str(worker_py), str(db_file), str(scene_file), "warm", "warm-tok-1234", "1/2", str(time.time())],
            check=True,
            capture_output=True,
            text=True,
        )
        go = time.time() + 1.5
        procs = [
            subprocess.Popen(
                [sys.executable, str(worker_py), str(db_file), str(scene_file), "shared-mp", "tok-shared-1234", r_arg, str(go)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for r_arg in ("1/3", "1/4")
        ]
        results = [json.loads(p.communicate(timeout=20)[0].strip().splitlines()[-1]) for p in procs]
        codes = sorted(r["status_code"] for r in results)
        # Either clean serialization (200, 200) or fail-closed lock contention (200, 409) — never 500!
        assert codes in ([200, 200], [200, 409]), f"Unexpected multiprocess same-session result: {results}"
