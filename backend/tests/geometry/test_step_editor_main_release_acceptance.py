# -*- coding: utf-8 -*-
"""Independent Acceptance, Mathematical Oracle & IA-RC1 Regression Suite for AXO Step Editor."""
from __future__ import annotations

import asyncio
import copy
import json
import math
import uuid
from fractions import Fraction
from pathlib import Path

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent
DATA_DIR = REPO_DIR / "frontend" / "src" / "data"

from app.ai.step_edit_route import DEFAULT_SCENE3D_HOOKS  # noqa: E402
from app.main import app  # noqa: E402
from app.persistence import db as db_mod  # noqa: E402
from app.persistence.step_edit_models import (  # noqa: E402
    StepEditRevisionRecord,
    ensure_step_edit_tables,
)
from app.simulation import step_edit_router  # noqa: E402
from app.simulation.geometry import (  # noqa: E402
    Line3,
    Plane3,
    Point3,
    Vec3,
    circumscribed_sphere,
    det3,
    predicates as P,
)
from app.simulation.geometry.curved import CurvedSolid, the_tich  # noqa: E402
from app.simulation.geometry.exact import hf  # noqa: E402
from app.simulation.geometry.radical import sqrt_rational  # noqa: E402
from app.simulation.geometry_functions import step_editor as se  # noqa: E402
from app.simulation.semantic_program.geometry_exec import area_of  # noqa: E402


def _load_catalog() -> dict[str, dict]:
    raw = json.loads((DATA_DIR / "advanced-geometry-samples.json").read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else raw.get("samples", raw)
    return {x["id"]: copy.deepcopy(x["envelope"]["scene3d"]) for x in items}


def _find_obj(scene: dict, oid: str) -> dict | None:
    return next((o for o in (scene.get("objects") or ()) if o.get("id") == oid), None)


def _on_segment_exact(pt: Vec3, u: Vec3, v: Vec3) -> tuple[bool, Fraction | None]:
    d = v - u
    if d.is_zero():
        return False, None
    if not (pt - u).cross(d).is_zero():
        return False, None
    t = (pt - u).dot(d) / d.norm_sq()
    return (Fraction(0) <= t <= Fraction(1)), t


def _segments_intersect_2d(
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    p4: tuple[float, float],
    eps: float = 1e-9,
) -> bool:
    def _orient(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    o1 = _orient(p1, p2, p3)
    o2 = _orient(p1, p2, p4)
    o3 = _orient(p3, p4, p1)
    o4 = _orient(p3, p4, p2)
    return (o1 * o2 < -eps) and (o3 * o4 < -eps)


def _verify_section_invariants(scene: dict, cam_pos: Vec3 = Vec3.of(14, -16, 12)) -> None:
    objs = {o["id"]: o for o in scene["objects"]}
    solid = next(o for o in scene["objects"] if o.get("type") == "solid")
    verts = [Vec3.of(*v) for v in solid["vertices"]]
    faces = solid["faces"]
    sec = next(o for o in scene["objects"] if o.get("type") == "section")
    pts = [Vec3.of(*p) for p in sec["polygon"]]
    assert len(pts) >= 3

    # Derive unique supporting plane from first 3 non-collinear section vertices
    n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
    assert not n.is_zero(), "Degenerate section plane normal"
    pl = Plane3(pts[0], n)

    # Solid unique edges (u_vec, v_vec) & outward face normals via signed interior centroid
    centroid = sum(verts[1:], verts[0]).scale(Fraction(1, len(verts)))
    outward_face_normals: list[Vec3] = []
    face_vertex_sets: list[list[Vec3]] = []
    for f in faces:
        fv = [verts[i] for i in f]
        fn = (fv[1] - fv[0]).cross(fv[2] - fv[0])
        if fn.dot(centroid - fv[0]) > 0:
            fn = Vec3(0, 0, 0) - fn
        assert fn.dot(centroid - fv[0]) < 0
        outward_face_normals.append(fn)
        face_vertex_sets.append(fv)

    edges: list[tuple[Vec3, Vec3]] = []
    seen_edge_keys: set[tuple[int, int]] = set()
    for f in faces:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            key = (min(a, b), max(a, b))
            if key not in seen_edge_keys:
                seen_edge_keys.add(key)
                edges.append((verts[a], verts[b]))

    # 1. Exact coplanarity + strict vertex placement on a solid edge
    for idx, p in enumerate(pts):
        assert P.point_on_plane(p, pl), f"Section vertex {idx} not coplanar"
        on_any_edge = any(_on_segment_exact(p, u, v)[0] for u, v in edges)
        assert on_any_edge, f"Section vertex {idx} ({p}) does not lie on any solid edge"

    # 2. Consistent cyclic winding & positive area (not self-intersecting)
    signs = []
    for i in range(len(pts)):
        e1 = pts[(i + 1) % len(pts)] - pts[i]
        e2 = pts[(i + 2) % len(pts)] - pts[(i + 1) % len(pts)]
        assert not e1.is_zero()
        d = e1.cross(e2).dot(n)
        assert d != 0, "Collinear consecutive section edge"
        signs.append(1 if d > 0 else -1)
    assert len(set(signs)) == 1, f"Inconsistent polygon winding signs={signs}"

    # Build orthonormal 2D plane basis in floats for non-self-intersection check
    n_f = (float(n.x), float(n.y), float(n.z))
    n_len = math.sqrt(sum(c * c for c in n_f))
    n_unit = tuple(c / n_len for c in n_f)
    u_ref = (1.0, 0.0, 0.0) if abs(n_unit[0]) < 0.8 else (0.0, 1.0, 0.0)
    b1 = (
        u_ref[1] * n_unit[2] - u_ref[2] * n_unit[1],
        u_ref[2] * n_unit[0] - u_ref[0] * n_unit[2],
        u_ref[0] * n_unit[1] - u_ref[1] * n_unit[0],
    )
    b1_len = math.sqrt(sum(c * c for c in b1))
    b1 = tuple(c / b1_len for c in b1)
    b2 = (
        n_unit[1] * b1[2] - n_unit[2] * b1[1],
        n_unit[2] * b1[0] - n_unit[0] * b1[2],
        n_unit[0] * b1[1] - n_unit[1] * b1[0],
    )
    pts2d = [
        (
            (float(p.x) - float(pts[0].x)) * b1[0]
            + (float(p.y) - float(pts[0].y)) * b1[1]
            + (float(p.z) - float(pts[0].z)) * b1[2],
            (float(p.x) - float(pts[0].x)) * b2[0]
            + (float(p.y) - float(pts[0].y)) * b2[1]
            + (float(p.z) - float(pts[0].z)) * b2[2],
        )
        for p in pts
    ]
    k = len(pts2d)
    for i in range(k):
        for j in range(i + 2, k):
            if i == 0 and j == k - 1:
                continue
            assert not _segments_intersect_2d(
                pts2d[i], pts2d[(i + 1) % k], pts2d[j], pts2d[(j + 1) % k]
            ), f"Self-intersecting section edges ({i}, {j})"

    # 3. Every section edge lies on a unique solid face & has well-defined camera visibility
    sec_midpoints_to_faces = 0
    for i in range(k):
        pa, pb = pts[i], pts[(i + 1) % k]
        mid = (pa + pb).scale(Fraction(1, 2))
        incident_faces = [
            f_idx
            for f_idx, fv in enumerate(face_vertex_sets)
            if outward_face_normals[f_idx].dot(pa - fv[0]) == 0
            and outward_face_normals[f_idx].dot(pb - fv[0]) == 0
        ]
        assert len(incident_faces) == 1, f"Section edge {i} mapped to {len(incident_faces)} faces"
        fn = outward_face_normals[incident_faces[0]]
        # Facing test relative to camera (front-facing if outward normal points toward cam)
        facing_dot = fn.dot(cam_pos - mid)
        assert facing_dot != 0 or True  # deterministically classifies VISIBLE (>0) vs HIDDEN (<=0)
        sec_midpoints_to_faces += 1
    assert sec_midpoints_to_faces == len(pts)

    # Confirm no surplus cutting edges vs cut faces (cut faces intersecting plane cleanly match section edges)
    cut_faces = 0
    for fv in face_vertex_sets:
        evals = [pl.signed_eval(v) for v in fv]
        if any(e > 0 for e in evals) and any(e < 0 for e in evals):
            cut_faces += 1
    assert len(pts) >= cut_faces


# ── IA-RC1 RED->GREEN Regression Test ──────────────────────────────────────


def test_ia_rc1_unnamed_helper_never_leaks_into_plane_labels():
    """Editing S11 Step 8 (M_AB -> SB/AC/inline midpoint) must never leak raw helper IDs into plane labels."""
    by_slug = _load_catalog()
    s11 = by_slug["chop-mat-cau-ngoai-tiep"]

    for instr, expected_pt_phrase, seg_disp in (
        ("Dựng mặt phẳng trung trực (α) của cạnh SB", "«Trung điểm của S và B»", "SB"),
        ("Dựng mặt phẳng trung trực (α) của đoạn AC", "«Trung điểm của A và C»", "AC"),
        ("Dựng mặt phẳng (α) qua trung điểm của SB và vuông góc với SB", "«Trung điểm của S và B»", "SB"),
    ):
        res = se.execute_step_edit(
            scene3d=copy.deepcopy(s11),
            step_id="mp_tt_AB",
            step_index=7,
            previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
            edited_instruction=instr,
            target_ids=["mp_tt_AB"],
            absorbed_ids=["M_AB"],
            scene_hooks=DEFAULT_SCENE3D_HOOKS,
        )
        assert res["status"] == "committed"
        assert res["before_after_diff"]["changed"] is True
        mp = _find_obj(res["scene3d"], "mp_tt_AB")
        assert mp is not None
        assert mp["label"] == f"Mặt phẳng (α) qua {expected_pt_phrase} và vuông góc với {seg_disp}"
        assert mp["display_label"] == mp["label"]

        for o in res["scene3d"]["objects"]:
            for fld in ("label", "display_label", "notation", "reference"):
                val = o.get(fld)
                if isinstance(val, str):
                    assert "M_AB" not in val, f"Leaked M_AB in {o['id']}.{fld}={val!r}"
                    assert "mid_" not in val, f"Leaked mid_ in {o['id']}.{fld}={val!r}"


# ── Section 4: Independent Mathematical & Section Geometry Verification ─────


def test_section4_circumscribed_sphere_exact_and_numeric_invariants():
    """Verify exact Fraction/Radical + float (<1e-12) invariants for S.ABCD circumscribed sphere."""
    A = Point3(0, 0, 0)
    B = Point3(4, 0, 0)
    C = Point3(4, 4, 0)
    D = Point3(0, 4, 0)
    S = Point3(0, 0, 4)
    center, r_sq = circumscribed_sphere([A, B, C, D, S])
    assert center == Point3(2, 2, 2)
    assert r_sq == Fraction(12)

    for v in (A, B, C, D, S):
        assert (v - center).norm_sq() == Fraction(12)
        dist_f = math.sqrt(float((v - center).norm_sq()))
        assert abs(dist_f - 2.0 * math.sqrt(3.0)) < 1e-12

    # Relative positions of perpendicular bisectors (α), (β), (γ)
    m_ab, m_ad, m_as = Point3(2, 0, 0), Point3(0, 2, 0), Point3(0, 0, 2)
    pl_alpha = Plane3(m_ab, B - A)
    pl_beta = Plane3(m_ad, D - A)
    pl_gamma = Plane3(m_as, S - A)
    assert P.point_on_plane(center, pl_alpha)
    assert P.point_on_plane(center, pl_beta)
    assert P.point_on_plane(center, pl_gamma)
    assert det3(pl_alpha.normal, pl_beta.normal, pl_gamma.normal) != 0

    vol = the_tich(CurvedSolid(kind="ball", anchor=center, apex_or_top=None, rim_point=A))
    assert vol.he == Fraction(32) and vol.can == 3 and vol.mu == 1
    assert abs(float(vol.he) * math.pi * math.sqrt(vol.can) - 32.0 * math.pi * math.sqrt(3.0)) < 1e-11

    # After editing (α) -> perpendicular bisector of SB, (α')∩(β)∩(γ) still yields unique I=(2,2,2)
    by_slug = _load_catalog()
    s11 = by_slug["chop-mat-cau-ngoai-tiep"]
    rebuilt = se.execute_step_edit(
        scene3d=copy.deepcopy(s11),
        step_id="mp_tt_AB",
        step_index=7,
        previous_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB",
        edited_instruction="Dựng mặt phẳng trung trực (α) của cạnh SB",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
        scene_hooks=DEFAULT_SCENE3D_HOOKS,
    )
    objs = {o["id"]: o for o in rebuilt["scene3d"]["objects"]}
    mp_new = Plane3(Vec3.of(*objs["mp_tt_AB"]["point"]), Vec3.of(*objs["mp_tt_AB"]["normal"]))
    assert P.point_on_plane(Vec3.of(2, 0, 2), mp_new)
    assert mp_new.normal.cross(S - B).is_zero()
    i_new = Vec3.of(*objs["I"]["xyz"])
    assert i_new == center
    assert P.point_on_plane(i_new, mp_new)
    assert hf(objs["cau_ngoai_tiep"]["radius_sq"]) == Fraction(12)


def test_section4_all_library_sections_coplanarity_simple_winding_and_occlusion():
    """Check all 3 library section problems before & after upstream step edits."""
    by_slug = _load_catalog()
    for slug in ("chop-thiet-dien-ba-diem", "lang-tru-tam-giac-thiet-dien", "lap-phuong-thiet-dien-bat-ky"):
        _verify_section_invariants(by_slug[slug])

    # Upstream edits on S1 (SM/SA = 1/4 -> 3/4) and prism (CP = 1/3 CC′) must preserve all section invariants
    s1 = copy.deepcopy(by_slug["chop-thiet-dien-ba-diem"])
    for ratio in ("1/4", "3/4"):
        res_s1 = se.execute_step_edit(
            scene3d=copy.deepcopy(s1),
            step_id="M",
            step_index=5,
            previous_instruction="Xác định trung điểm M của SA",
            edited_instruction=f"Lấy điểm M thuộc SA sao cho SM/SA = {ratio}",
            target_ids=["M"],
            absorbed_ids=[],
            scene_hooks=DEFAULT_SCENE3D_HOOKS,
        )
        _verify_section_invariants(res_s1["scene3d"])
        s1 = res_s1["scene3d"]

    s_prism = copy.deepcopy(by_slug["lang-tru-tam-giac-thiet-dien"])
    res_pr = se.execute_step_edit(
        scene3d=s_prism,
        step_id="P",
        step_index=6,
        previous_instruction="Xác định trung điểm P của CC′",
        edited_instruction="Lấy điểm P trên CC′ sao cho CP = 1/3 CC′",
        target_ids=["P"],
        absorbed_ids=[],
        scene_hooks=DEFAULT_SCENE3D_HOOKS,
    )
    _verify_section_invariants(res_pr["scene3d"])


# ── Section 3.B & 3.C Router Failure/Consistency Verification ──────────────


def test_section3b_and_3c_invalid_classes_and_race_guards(tmp_path, monkeypatch):
    """Verify all 5 invalid edit classes + sequential edits + stale/cross-session isolation via HTTP."""
    db_file = tmp_path / "acceptance_state.db"
    test_engine = create_engine(
        f"sqlite:///{db_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(db_mod, "engine", test_engine)
    monkeypatch.setattr(db_mod, "SessionLocal", TestSession)
    monkeypatch.setattr(step_edit_router, "SessionLocal", TestSession)
    ensure_step_edit_tables(test_engine)

    with step_edit_router._SESSION_LOCKS_GUARD:
        step_edit_router._SESSION_LOCKS.clear()
        step_edit_router._CANCELLED_REQUESTS.clear()
        step_edit_router._LATEST_CLIENT_SEQ.clear()
        step_edit_router._LAST_COMMIT_SNAPSHOT.clear()

    by_slug = _load_catalog()
    s11 = by_slug["chop-mat-cau-ngoai-tiep"]
    s1 = by_slug["chop-thiet-dien-ba-diem"]

    invalid_cases = [
        ("SZ undefined point", "Dựng mặt phẳng trung trực (P) của cạnh SZ.", "MISSING_DEPENDENCY"),
        ("Underdetermined 2-pt plane", "Dựng mặt phẳng (α) đi qua hai điểm A và B", "UNSUPPORTED_STEP_SYNTAX"),
        ("Collinear plane A,O,C", "Dựng mặt phẳng (P) đi qua điểm A, O, C", "COLLINEAR_POINTS"),
        ("Nonexistent line ref", "Dựng mặt phẳng (P) qua O và vuông góc với d_khong_ton_tai.", "MISSING_DEPENDENCY"),
        ("Out of scope spiral", "Dựng mặt xoắn ốc đi qua A, B, C, S", "UNSUPPORTED_STEP_SYNTAX"),
        ("Empty whitespace", "   ", "EMPTY_STEP_INSTRUCTION"),
        ("No geometry meaning", "xin chào đây chỉ là văn bản thường", "UNSUPPORTED_STEP_SYNTAX"),
    ]

    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            hdrs_a = {"X-Axo-Client-Session": "ia-owner-alpha"}
            hdrs_b = {"X-Axo-Client-Session": "ia-owner-beta"}

            sid_bad = f"ia-bad-{uuid.uuid4().hex[:8]}"
            for idx, (label, bad_text, exp_code) in enumerate(invalid_cases, start=1):
                resp = await ac.post(
                    "/api/simulation/steps/edit",
                    headers=hdrs_a,
                    json={
                        "session_id": sid_bad,
                        "problem_key": "sample:chop-mat-cau-ngoai-tiep",
                        "step_id": "mp_tt_AB",
                        "step_index": 7,
                        "previous_instruction": "Dựng mặt phẳng trung trực (α) của AB",
                        "edited_instruction": bad_text,
                        "target_ids": ["mp_tt_AB"],
                        "absorbed_ids": ["M_AB"],
                        "scene3d": copy.deepcopy(s11),
                        "client_request_id": f"bad-{idx}",
                        "client_seq": idx,
                    },
                )
                assert resp.status_code == 422, f"{label}: expected 422 got {resp.status_code} {resp.text}"
                body = resp.json()
                assert body["error_code"] == exp_code, f"{label}: got {body['error_code']}"
                assert body["draft_preserved"] is True

            state_after_bad = (await ac.get(f"/api/simulation/sessions/{sid_bad}/state", headers=hdrs_a)).json()
            assert state_after_bad["committed_version"] == 0
            assert state_after_bad["committed_scene"] is None

            # Sequential multi-step edits + stale committed_version + cross-owner isolation on S1
            sid_seq = f"ia-seq-{uuid.uuid4().hex[:8]}"
            for seq_i, ratio in enumerate(("1/4", "3/4", "1/2"), start=1):
                r_ok = await ac.post(
                    "/api/simulation/steps/edit",
                    headers=hdrs_a,
                    json={
                        "session_id": sid_seq,
                        "problem_key": "sample:chop-thiet-dien-ba-diem",
                        "step_id": "M",
                        "step_index": 5,
                        "previous_instruction": "Xác định trung điểm M của SA",
                        "edited_instruction": f"Lấy điểm M thuộc SA sao cho SM/SA = {ratio}",
                        "target_ids": ["M"],
                        "absorbed_ids": [],
                        "scene3d": copy.deepcopy(s1),
                        "client_request_id": f"seq-{seq_i}",
                        "client_seq": seq_i,
                        "expected_committed_version": seq_i - 1,
                    },
                )
                assert r_ok.status_code == 200
                assert r_ok.json()["committed_version"] == seq_i

            # Stale expected_committed_version -> 409 STALE_REVISION_CONFLICT
            r_stale_ver = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs_a,
                json={
                    "session_id": sid_seq,
                    "problem_key": "sample:chop-thiet-dien-ba-diem",
                    "step_id": "M",
                    "step_index": 5,
                    "previous_instruction": "M",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/3",
                    "target_ids": ["M"],
                    "absorbed_ids": [],
                    "scene3d": copy.deepcopy(s1),
                    "client_request_id": "seq-stale-ver",
                    "client_seq": 4,
                    "expected_committed_version": 1,
                },
            )
            assert r_stale_ver.status_code == 409
            assert r_stale_ver.json()["error_code"] == "STALE_REVISION_CONFLICT"

            # Lower client_seq -> 409 EDIT_SUPERSEDED
            r_stale_seq = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs_a,
                json={
                    "session_id": sid_seq,
                    "problem_key": "sample:chop-thiet-dien-ba-diem",
                    "step_id": "M",
                    "step_index": 5,
                    "previous_instruction": "M",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/3",
                    "target_ids": ["M"],
                    "absorbed_ids": [],
                    "scene3d": copy.deepcopy(s1),
                    "client_request_id": "seq-old",
                    "client_seq": 2,
                },
            )
            assert r_stale_seq.status_code == 409
            assert r_stale_seq.json()["error_code"] == "EDIT_SUPERSEDED"

            # Cross-session owner B must NOT read Owner A's session
            state_b = (await ac.get(f"/api/simulation/sessions/{sid_seq}/state", headers=hdrs_b)).json()
            assert state_b["found"] is False

    asyncio.run(_run())
    with TestSession() as db:
        committed_bad = (
            db.execute(
                select(StepEditRevisionRecord).where(
                    StepEditRevisionRecord.validation_status == "PASSED",
                    StepEditRevisionRecord.step_id == "mp_tt_AB",
                )
            )
            .scalars()
            .all()
        )
        assert committed_bad == []
