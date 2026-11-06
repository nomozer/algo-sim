# -*- coding: utf-8 -*-
"""Kiểm thử tích hợp IR/Engine -> Scene3D cho trình tự dựng hình sư phạm & tổng quát hóa thiết diện.

Chạy hoàn toàn offline (`ALLOW_LIVE_AI=0`) qua tuyến tất định thực:
`Vietnamese Problem + Typed Facts -> Planner -> Compiler/IR -> Engine/Kernel -> Formation -> Scene3D`

Kiểm chứng:
1. Đề chuẩn S.ABCD (đáy hình vuông cạnh 2, SA ⊥ (ABCD), SA = 4, M, N, P là trung điểm SA, SB, SC,
   dựng thiết diện bởi (MNP)):
   - Thỏa hợp đồng trình tự sư phạm O1–O4 (`CONSTRUCT_BASE < CONSTRUCT_HEIGHT < CONSTRUCT_LATERAL_BOUNDARY < CLOSE_SOLID`
     trước các điểm dựng M, N, P, Q, mặt phẳng cắt và thiết diện).
   - Mặt đáy mang `surface_role == "BASE_REGION"` và `boundary_edge_ids` tham chiếu đúng cạnh khối.
   - Đường cao SA mang `perpendicular_witness` chính xác tại chân A (`u ⊥ v`).
   - Đại số chính xác trên Q^3 (tôn trọng `chart_metric`):
     * MN ∥ AB, NP ∥ BC, PQ ∥ CD, QM ∥ DA.
     * Q = SD ∩ (MNP) là trung điểm chính xác của đoạn SD (`2*Q == S + D`, t = 1/2 ∈ [0, 1]).
     * |MN|^2 = |NP|^2 = |PQ|^2 = |QM|^2 = 1, MN ⊥ NP => MNPQ là hình vuông diện tích 1.
     * Bốn đoạn giao tuyến trong `section.steps` nằm đúng trên bốn mặt bên (SAB), (SBC), (SCD), (SAD).
2. Biến thể đổi tên đỉnh & đổi tỉ lệ kích thước (`T.EFGH`, cạnh đáy 6, đường cao TE = 10, trung điểm I, J, K):
   - Không phụ thuộc ký hiệu đỉnh hay tọa độ cứng; thiết diện là hình vuông cạnh 3 (`|IJ|^2 = 9`).
3. Biến thể đáy hình chữ nhật (`S.ABCD`, `AB = 4`, `BC = 2`, `SA = 5`, trung điểm M, N, P):
   - Thiết diện MNPQ là hình chữ nhật (`|MN|^2 = 4 != |NP|^2 = 1`, `MN ⊥ NP`), không phải hình vuông.
4. Biến thể không đối xứng (`(MAB)` cắt S.ABCD theo hình thang; mặt phẳng qua điểm cắt lăng trụ đứng `ABC.A'B'C'`):
   - Thỏa O1–O4, bảo toàn dependency graph và diện tích bình phương khớp oracle độc lập.
"""
from __future__ import annotations

import os
from fractions import Fraction as F

import pytest

from app.ai.function_route import run_fact_route
from tests.geometry import construction_sequencing as CS
from tests.geometry import hybrid_compiler_benchmark as HB


Vec3 = tuple[F, F, F]


def _vec(xyz: list[str] | tuple[str, ...]) -> Vec3:
    return (F(xyz[0]), F(xyz[1]), F(xyz[2]))


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _plain_dot(a: Vec3, b: Vec3) -> F:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _metric_dot(u: Vec3, v: Vec3, chart_metric: list[list[str]] | None) -> F:
    if not chart_metric:
        return _plain_dot(u, v)
    acc = F(0)
    for i in range(3):
        for j in range(3):
            acc += u[i] * F(chart_metric[i][j]) * v[j]
    return acc


def _parallel(u: Vec3, v: Vec3) -> bool:
    return u != (F(0), F(0), F(0)) and v != (F(0), F(0), F(0)) and _cross(u, v) == (F(0), F(0), F(0))


def _build_midpoint_section_case(
    names: str = "SABCD",
    mids: str = "MNP",
    q_name: str | None = "Q",
    base_shape: str = "square",
    ab_val: str = "2",
    bc_val: str | None = None,
    sa_val: str = "4",
):
    s, a, b, c, d = names
    m, n, p = mids
    base = f"{a}{b}{c}{d}"
    solid = f"{s}.{base}"

    sentences = [f"Cho hình chóp {solid}."]
    facts = [HB._f("f_solid", "solid", sentences[-1], solid=solid, solid_type="pyramid")]

    if base_shape == "square":
        s_base = f"Đáy {base} là hình vuông cạnh {ab_val}."
        sentences.append(s_base)
        facts.append(HB._f("f_base", "polygon_shape", s_base, points=list(base), shape="square", value=ab_val))
    else:
        assert bc_val is not None
        s_base = f"Đáy {base} là hình chữ nhật."
        s_ab = f"{a}{b} = {ab_val}."
        s_bc = f"{b}{c} = {bc_val}."
        sentences.extend([s_base, s_ab, s_bc])
        facts.extend([
            HB._f("f_base", "polygon_shape", s_base, points=list(base), shape="rectangle"),
            HB._f("f_ab", "length", s_ab, points=[a, b], measure="segment", value=ab_val),
            HB._f("f_bc", "length", s_bc, points=[b, c], measure="segment", value=bc_val),
        ])

    s_perp = f"{s}{a} vuông góc với ({base})."
    s_sa = f"{s}{a} = {sa_val}."
    sentences.extend([s_perp, s_sa])
    facts.extend([
        HB._f("f_perp", "perpendicular", s_perp, points_a=[s, a], points_b=list(base)),
        HB._f("f_sa", "length", s_sa, points=[s, a], measure="segment", value=sa_val),
    ])

    for idx, (pt, seg_end) in enumerate(((m, a), (n, b), (p, c)), start=1):
        mf = HB._mid(f"f_mid_{idx}", pt, s, seg_end)
        sentences.append(mf["quotes"][0])
        facts.append(mf)

    if q_name is not None:
        qf = HB._ilp("f_q", q_name, f"{s}{d}", f"{m}{n}{p}")
        sentences.append(qf["quotes"][0])
        facts.append(qf)

    s_sec = f"Dựng thiết diện của hình chóp {solid} cắt bởi mặt phẳng ({m}{n}{p})."
    sentences.append(s_sec)
    facts.append(HB._f("f_sec", "section", s_sec, role="question", solid=solid, points=[m, n, p]))

    return " ".join(sentences), {"facts": facts}


@pytest.fixture(autouse=True)
def _enforce_offline_env(monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")


def test_sabcd_pedagogical_pipeline_and_exact_square_section():
    assert os.environ.get("ALLOW_LIVE_AI") == "0"
    text, payload = _build_midpoint_section_case()
    r = run_fact_route(text, payload)
    assert r.status == "SERVED", (r.code, r.reason)

    scene = r.scene3d
    assert CS.check(scene) == {"O1": [], "O2": [], "O3": [], "O4": []}

    objs_by_id = {o["id"]: o for o in scene["objects"]}
    pts_by_sym = {
        o.get("notation") or o.get("label"): _vec(o["xyz"])
        for o in scene["objects"]
        if o["type"] == "point3" and o.get("xyz")
    }
    for sym in ("S", "A", "B", "C", "D", "M", "N", "P", "Q"):
        assert sym in pts_by_sym, f"Thiếu điểm {sym} trong Scene3D"

    # Kiểm chứng mặt đáy & chứng chỉ góc vuông 3D của đường cao SA
    base_polys = [o for o in scene["objects"] if o.get("surface_role") == "BASE_REGION"]
    assert len(base_polys) == 1
    assert len(base_polys[0].get("boundary_edge_ids") or []) == 4

    height_segs = [
        o for o in scene["objects"]
        if o["type"] == "segment3" and o.get("perpendicular_witness") is not None
    ]
    assert len(height_segs) == 1
    assert height_segs[0].get("notation") == "SA"
    pw = height_segs[0]["perpendicular_witness"]
    assert _vec(pw["foot"]) == pts_by_sym["A"]
    u_vec = _vec(pw["marker"]["u"])
    v_vec = _vec(pw["marker"]["v"])
    metric = scene.get("chart_metric")
    assert _metric_dot(u_vec, v_vec, metric) == F(0)

    # Kiểm chứng đại số chính xác trên Q^3:
    # 1. Q là trung điểm của SD (2*Q == S + D)
    S, A, B, C, D = (pts_by_sym[k] for k in ("S", "A", "B", "C", "D"))
    M, N, P, Q = (pts_by_sym[k] for k in ("M", "N", "P", "Q"))
    assert tuple(2 * c for c in Q) == _add(S, D)

    # 2. MN ∥ AB, NP ∥ BC, PQ ∥ CD, QM ∥ DA
    MN, NP, PQ, QM = _sub(N, M), _sub(P, N), _sub(Q, P), _sub(M, Q)
    AB, BC, CD, DA = _sub(B, A), _sub(C, B), _sub(D, C), _sub(A, D)
    assert _parallel(MN, AB)
    assert _parallel(NP, BC)
    assert _parallel(PQ, CD)
    assert _parallel(QM, DA)

    # 3. Bốn cạnh bằng nhau (= 1) và góc vuông MN ⊥ NP => MNPQ là hình vuông diện tích 1
    sq_lens = [_metric_dot(e, e, metric) for e in (MN, NP, PQ, QM)]
    assert sq_lens == [F(1), F(1), F(1), F(1)]
    assert _metric_dot(MN, NP, metric) == F(0)
    assert _metric_dot(NP, PQ, metric) == F(0)

    # 4. Bốn đoạn giao tuyến nằm chính xác trên bốn mặt bên của khối chóp, không có giao tuyến thừa
    (sec_obj,) = [o for o in scene["objects"] if o["type"] == "section"]
    (solid_obj,) = [o for o in scene["objects"] if o["type"] == "solid"]
    assert {_vec(p) for p in sec_obj["polygon"]} == {M, N, P, Q}
    steps = sec_obj.get("steps") or []
    assert len(steps) == 4

    solid_faces = solid_obj["faces"]
    solid_vids = solid_obj["vertex_ids"]
    seen_lateral_faces = set()
    for st in steps:
        fi = st["face_index"]
        assert fi is not None
        face_syms = frozenset(objs_by_id[solid_vids[vi]].get("notation") for vi in solid_faces[fi])
        assert "S" in face_syms and len(face_syms) == 3
        seen_lateral_faces.add(face_syms)
        f_pts = [_vec(solid_obj["vertices"][vi]) for vi in solid_faces[fi]]
        cov = _cross(_sub(f_pts[1], f_pts[0]), _sub(f_pts[2], f_pts[0]))
        for end_pt in (_vec(st["a"]), _vec(st["b"])):
            assert _plain_dot(_sub(end_pt, f_pts[0]), cov) == F(0)

    assert seen_lateral_faces == {
        frozenset(("S", "A", "B")),
        frozenset(("S", "B", "C")),
        frozenset(("S", "C", "D")),
        frozenset(("S", "D", "A")),
    }


def test_renamed_and_scaled_square_pyramid_generalizes_without_hardcoding():
    text, payload = _build_midpoint_section_case(
        names="TEFGH",
        mids="IJK",
        q_name="L",
        base_shape="square",
        ab_val="6",
        sa_val="10",
    )
    r = run_fact_route(text, payload)
    assert r.status == "SERVED", (r.code, r.reason)
    scene = r.scene3d
    assert CS.check(scene) == {"O1": [], "O2": [], "O3": [], "O4": []}

    pts = {
        o.get("notation") or o.get("label"): _vec(o["xyz"])
        for o in scene["objects"]
        if o["type"] == "point3" and o.get("xyz")
    }
    T, H = pts["T"], pts["H"]
    I, J, K, L = pts["I"], pts["J"], pts["K"], pts["L"]
    assert tuple(2 * c for c in L) == _add(T, H)

    metric = scene.get("chart_metric")
    IJ, JK, KL, LI = _sub(J, I), _sub(K, J), _sub(L, K), _sub(I, L)
    assert [_metric_dot(e, e, metric) for e in (IJ, JK, KL, LI)] == [F(9), F(9), F(9), F(9)]
    assert _metric_dot(IJ, JK, metric) == F(0)


def test_rectangular_base_pyramid_yields_exact_rectangle_not_square():
    text, payload = _build_midpoint_section_case(
        names="SABCD",
        mids="MNP",
        q_name="Q",
        base_shape="rectangle",
        ab_val="4",
        bc_val="2",
        sa_val="5",
    )
    r = run_fact_route(text, payload)
    assert r.status == "SERVED", (r.code, r.reason)
    scene = r.scene3d
    assert CS.check(scene) == {"O1": [], "O2": [], "O3": [], "O4": []}

    pts = {
        o.get("notation") or o.get("label"): _vec(o["xyz"])
        for o in scene["objects"]
        if o["type"] == "point3" and o.get("xyz")
    }
    M, N, P, Q = (pts[k] for k in ("M", "N", "P", "Q"))
    A, B, C, D = (pts[k] for k in ("A", "B", "C", "D"))
    metric = scene.get("chart_metric")
    MN, NP, PQ, QM = _sub(N, M), _sub(P, N), _sub(Q, P), _sub(M, Q)
    assert _parallel(MN, _sub(B, A))
    assert _parallel(NP, _sub(C, B))
    assert _parallel(PQ, _sub(D, C))
    assert _parallel(QM, _sub(A, D))
    # AB = 4 => |MN|^2 = 4; BC = 2 => |NP|^2 = 1 => hình chữ nhật không đều (không phải hình vuông)
    assert _metric_dot(MN, MN, metric) == F(4)
    assert _metric_dot(NP, NP, metric) == F(1)
    assert _metric_dot(PQ, PQ, metric) == F(4)
    assert _metric_dot(QM, QM, metric) == F(1)
    assert _metric_dot(MN, NP, metric) == F(0)


def test_asymmetric_trapezoid_and_prism_sections_preserve_pedagogical_order():
    # 1. Thiết diện hình thang (MAB) với M trung điểm SC trên S.ABCD (SA = 3, AB = 2)
    q, facts = HB._with(
        HB._square(),
        HB._mid("f_m", "M", "S", "C"),
        HB._f("f_sec", "section", "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB).",
              role="premise", solid="S.ABCD", points=["M", "A", "B"]),
        HB._ask("q", "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB).",
                "area", solid="S.ABCD", points=["M", "A", "B"]),
    )
    r_trap = run_fact_route(" ".join(q), {"facts": facts})
    assert r_trap.status == "SERVED"
    assert CS.check(r_trap.scene3d) == {"O1": [], "O2": [], "O3": [], "O4": []}
    (sec_trap,) = [o for o in r_trap.scene3d["objects"] if o["type"] == "section"]
    assert len(sec_trap["polygon"]) == 4

    # 2. Lăng trụ đứng ABC.A'B'C' cắt bởi mặt phẳng qua trung điểm M của AA' song song (ABC)
    prism_q = [
        "Cho lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều ABC cạnh 2.",
        "AA' = 3.",
        "Gọi M là trung điểm AA'.",
        "Dựng mặt phẳng (P) đi qua M và song song với (ABC).",
        "Tính diện tích thiết diện của hình lăng trụ ABC.A'B'C' với (P).",
    ]
    prism_facts = [
        HB._f("f1", "solid", prism_q[0], solid="ABC.A'B'C'", solid_type="prism", right=True),
        HB._f("f2", "polygon_shape", prism_q[0], points=["A", "B", "C"], shape="equilateral_triangle", value="2"),
        HB._f("f3", "length", prism_q[1], points=["A", "A'"], measure="segment", value="3"),
        HB._mid("f4", "M", "A", "A'"),
        {
            "id": "q",
            "kind": "question",
            "role": "question",
            "quantity": "area",
            "quotes": prism_q[3:],
            "solid": "ABC.A'B'C'",
            "point": "M",
            "points_b": ["A", "B", "C"],
            "plane_relation": "parallel",
        },
    ]
    r_prism = run_fact_route(" ".join(prism_q), {"facts": prism_facts})
    assert r_prism.status == "SERVED"
    assert CS.check(r_prism.scene3d) == {"O1": [], "O2": [], "O3": [], "O4": []}
    (sec_prism,) = [o for o in r_prism.scene3d["objects"] if o["type"] == "section"]
    assert len(sec_prism["polygon"]) == 3
