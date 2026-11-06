"""Retired Axo module `tests/geometry/test_construction_integrity_audit.py` (Axo 67f780ca), restored on Hybrid /4 by the pre-merge
audit (run axo-hybrid4-final-premerge-hardening). The merge had deleted the whole module because it imported
Adapter /3; the tests below still hold on main's route. Not restored, and why:
- `test_mandatory_regression_5_2_oblique_or_unproven_cylinder_never_fabricates_15pi`: needs the `/1` `oblique_cylinder` fact main does not have (not added on purpose); ported as `test_hybrid4_cylinder_never_assumed_right.py`
- `test_certified_right_cylinder_sqrt5_radius_exact_rim_and_given_dimensions`: `/1` payload without sections ⇒ converter KeyError (see above); certified right cylinder served exactly: `test_hybrid4_cylinder_never_assumed_right.py::test_control_…`, `test_curved_foundation.py`
- `test_polyhedra_given_dimensions_and_renamed_families_adapter3_v2`: converter KeyError (no sections); renamed families covered by `test_source_gate_hardening.py`
- `test_curved_families_sphere_cut_and_renamed_cone_invariants`: sphere `plane_equation` section refused on /4 (`BRIDGE_UNSUPPORTED_CURVED`)
"""
"""Kiểm thử hồi quy toàn diện Backend cho nhiệm vụ:
AXO CONSTRUCTION INTEGRITY AUDIT & PEDAGOGICAL SEQUENCING (§3–§9).

Chạy hoàn toàn offline (`ALLOW_LIVE_AI=0`), kiểm chứng:
1. §5.2 Hồi quy bắt buộc — Hình trụ xiên / chưa chứng minh trục vuông góc đáy
   (`OO' = 3`, `OA = √5`, `OO'` không vuông góc `OA`, hoặc `OO'` chỉ vuông góc một bán kính đơn lẻ `OA`):
   - Từ chối an toàn (`CURVED_PRIMITIVE_BLOCKED_BY_KERNEL`), TUYỆT ĐỐI không áp dụng `V = πR²·OO' = 15π`.
   - Đối chứng: hình trụ đứng có chứng nhận `OO' ⊥ mặt đáy` (và biến thể đổi tên `I.J`, bán kính `IK = √5`, `IJ = 3`)
     dựng chính xác điểm vành hữu tỷ `(2, 1, 0)` thỏa `x² + y² = 5` và gắn nhãn `GIVEN` đã kiểm chứng.
2. §5.3 Hồi quy bắt buộc — Thiết diện `MNPQ` (`S.ABCD` đáy hình vuông & biến thể đổi tên `T.EFGH`, đối chứng đáy không vuông):
   - `Q = SD ∩ (MNP)` luôn mang `origin == "derived"`, không bao giờ bị mô tả là `GIVEN`.
   - Chứng minh đại số chính xác `2*Q == S + D` (`t = 1/2 ∈ [0, 1]`), 4 đoạn giao tuyến nằm trên 4 mặt bên,
     và chỉ đạt hình vuông khi đáy có chứng chỉ hình vuông (đáy hình chữ nhật lệch cạnh hoặc hình bình hành không suy ra hình vuông).
3. §7 & §9 Ma trận đa họ hình + đổi tên đỉnh + kiểm tra bất biến DAG, provenance, không rò rỉ đối tượng tương lai,
   nhân chứng đoạn vuông góc chung (`common_perpendicular`), và gắn nhãn thông số `GIVEN` trực tiếp từ đề.
"""


import os
from fractions import Fraction as F

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions.typed_fact_next import convert_v1_to_v2


def run_typed_fact_next_route(raw):
    """Retired Adapter /3 entry → the product route: `/1` payload converted with main's declared `adapter3` semantics
    (`convert_v1_to_v2`), then Adapter /4. Same engine, same certificates; only the envelope contract differs."""
    return run_typed_fact_next_v2_route(convert_v1_to_v2(raw, "adapter3"))
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_fact_route
from app.simulation.geometry_functions.typed_fact_next import TYPED_FACT_NEXT_SCHEMA_VERSION
from tests.geometry import construction_sequencing as CS
from tests.geometry import hybrid_compiler_benchmark as HB

Vec3 = tuple[F, F, F]


@pytest.fixture(autouse=True)
def _enforce_offline_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")


def _vec(xyz: list[str] | tuple[str, ...]) -> Vec3:
    return (F(str(xyz[0])), F(str(xyz[1])), F(str(xyz[2])))


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _metric_dot(u: Vec3, v: Vec3, chart_metric: list[list[str]] | None) -> F:
    if not chart_metric:
        return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]
    acc = F(0)
    for i in range(3):
        for j in range(3):
            acc += u[i] * F(str(chart_metric[i][j])) * v[j]
    return acc


def _assert_scene_core_invariants(scene: dict) -> None:
    """Kiểm tra tự động các bất biến cốt lõi (§9) trên Scene3D sinh từ Backend."""
    assert os.environ.get("ALLOW_LIVE_AI") == "0"
    objects = scene.get("objects") or []
    by_id = {o["id"]: o for o in objects}
    assert len(by_id) == len(objects), "Object ID phải duy nhất và ổn định"

    free_set = set(scene.get("free_objects") or [])
    for fid in free_set:
        assert fid in by_id, f"free_object {fid} không tồn tại trong objects"

    # Không nâng DERIVED hoặc AUXILIARY thành GIVEN
    for o in objects:
        roles = set(o.get("formation_roles") or [])
        groups = set(o.get("display_group") or [])
        if o.get("origin") == "derived":
            assert "given" not in groups, f"Đối tượng derived {o['id']} bị nâng sai thành given"
        if "CONSTRUCT_AUXILIARY_GEOMETRY" in roles:
            assert o.get("origin") != "free", f"Hình phụ {o['id']} không được mang origin='free'"

    # Kiểm tra DAG không chu trình và mọi dependency xuất hiện trước hoặc cùng bước sử dụng
    steps = (scene.get("formation") or {}).get("steps") or []
    assert len(steps) > 0
    seen_ever: set[str] = set(free_set)
    final_visible = set(steps[-1].get("visible_ids") or [])
    retired_ids: set[str] = set()
    for ev in scene.get("events") or []:
        for rid in ev.get("retires") or []:
            retired_ids.add(rid)

    for k, st in enumerate(steps):
        vis = set(st.get("visible_ids") or [])
        newly_added = vis - seen_ever
        seen_ever |= vis
        avail = seen_ever | set(st.get("readout_ids") or [])
        for oid in newly_added:
            obj = by_id.get(oid)
            if not obj:
                continue
            for dep in obj.get("depends") or []:
                if dep in by_id and by_id[dep].get("render") not in ("readout", "non_visual"):
                    assert dep in avail, (
                        f"Vi phạm DAG tại step {k}: {oid} xuất hiện trước dependency {dep}"
                    )

    # Không có đối tượng xuất hiện sớm rồi biến mất vô lý (trừ hình phụ đã retire có chủ đích)
    for k, st in enumerate(steps[:-1]):
        for oid in st.get("visible_ids") or []:
            if oid not in retired_ids:
                assert oid in final_visible, (
                    f"Rò rỉ / biến mất bất thường đối tượng {oid} ở step {k}"
                )


# ============================================================================
# 1. §5.2 HỒI QUY BẮT BUỘC: HÌNH TRỤ CÓ TRỤC XIÊN / CHƯA CHỨNG MINH CHIỀU CAO
# ============================================================================






# ============================================================================
# 2. §5.3 HỒI QUY BẮT BUỘC: THIẾT DIỆN MNPQ & ĐỐI CHỨNG ĐÁY KHÔNG VUÔNG
# ============================================================================


@pytest.mark.parametrize(
    ("verts", "mids", "inter_pt", "base_side", "height_val", "expected_edge_sq"),
    [
        ("SABCD", "MNP", "Q", "4", "6", F(4)),
        ("TEFGH", "IJK", "L", "6", "8", F(9)),
    ],
)
def test_mandatory_regression_5_3_midpoint_section_q_provenance_and_square_certificate(
    verts: str,
    mids: str,
    inter_pt: str,
    base_side: str,
    height_val: str,
    expected_edge_sq: F,
) -> None:
    """§5.3: Thiết diện qua 3 trung điểm cạnh bên hình chóp đáy vuông (cả bản chuẩn S.ABCD và đổi tên T.EFGH):
    - Giao điểm thứ tư Q = SD ∩ (MNP) có origin='derived' (không bao giờ mô tả là GIVEN).
    - 2*Q == S + D (trung điểm chính xác trên đoạn SD với t = 1/2 ∈ [0, 1]).
    - 4 cạnh thiết diện bằng nhau và vuông góc trên metric chính xác."""
    s, a, b, c, d = verts
    m, n, p = mids
    base = f"{a}{b}{c}{d}"
    solid = f"{s}.{base}"
    sentences = [
        f"Cho hình chóp {solid}.",
        f"Đáy {base} là hình vuông cạnh {base_side}.",
        f"{s}{a} vuông góc với ({base}).",
        f"{s}{a} = {height_val}.",
    ]
    facts = [
        HB._f("f_sol", "solid", sentences[0], solid=solid, solid_type="pyramid"),
        HB._f("f_base", "polygon_shape", sentences[1], points=list(base), shape="square", value=base_side),
        HB._f("f_perp", "perpendicular", sentences[2], points_a=[s, a], points_b=list(base)),
        HB._f("f_h", "length", sentences[3], points=[s, a], measure="segment", value=height_val),
    ]
    for idx, (mp, base_v) in enumerate(((m, a), (n, b), (p, c)), start=1):
        mf = HB._mid(f"f_m{idx}", mp, s, base_v)
        sentences.append(mf["quotes"][0])
        facts.append(mf)
    qf = HB._ilp("f_q", inter_pt, f"{s}{d}", f"{m}{n}{p}")
    sentences.append(qf["quotes"][0])
    facts.append(qf)
    s_sec = f"Dựng thiết diện của hình chóp {solid} cắt bởi mặt phẳng ({m}{n}{p})."
    sentences.append(s_sec)
    facts.append(HB._f("f_sec", "section", s_sec, role="question", solid=solid, points=[m, n, p]))

    res = run_fact_route(" ".join(sentences), {"facts": facts})
    assert res.status == "SERVED", (res.code, res.reason)
    scene = res.scene3d
    assert CS.check(scene) == {"O1": [], "O2": [], "O3": [], "O4": []}
    _assert_scene_core_invariants(scene)

    pts = {o.get("notation") or o["id"]: o for o in scene["objects"] if o["type"] == "point3"}
    q_obj = pts[inter_pt]
    assert q_obj["origin"] == "derived", f"{inter_pt} phải là điểm suy ra (derived), không được là GIVEN"
    assert q_obj["id"] not in scene["free_objects"]

    vs, vd, vq = _vec(pts[s]["xyz"]), _vec(pts[d]["xyz"]), _vec(q_obj["xyz"])
    assert (2 * vq[0], 2 * vq[1], 2 * vq[2]) == _add(vs, vd), f"{inter_pt} phải là trung điểm chính xác của {s}{d}"

    vm, vn, vp = _vec(pts[m]["xyz"]), _vec(pts[n]["xyz"]), _vec(pts[p]["xyz"])
    cm = scene.get("chart_metric")
    e_mn = _sub(vn, vm)
    e_np = _sub(vp, vn)
    e_pq = _sub(vq, vp)
    e_qm = _sub(vm, vq)
    for e_vec in (e_mn, e_np, e_pq, e_qm):
        assert _metric_dot(e_vec, e_vec, cm) == expected_edge_sq
    assert _metric_dot(e_mn, e_np, cm) == F(0)

    sec_obj = next(o for o in scene["objects"] if o["type"] == "section")
    assert len(sec_obj.get("steps") or []) == 4


def test_section_mnpq_on_non_square_bases_never_certifies_square() -> None:
    """Đối chứng âm §5.1 & §5.3:
    1) Đáy hình chữ nhật lệch cạnh (`AB = 6`, `BC = 4`): thiết diện `MNPQ` có `|MN|² = 9 != |NP|² = 4` (chỉ là hình chữ nhật).
    2) Đáy hình thoi không có góc vuông (`AB = 4`, góc `BAD = 60°`): thiết diện có 4 cạnh bằng 2 nhưng góc khác 90°."""
    # (1) Đáy hình chữ nhật AB = 6, BC = 4
    s_rect = [
        "Cho hình chóp S.ABCD.",
        "Đáy ABCD là hình chữ nhật.",
        "AB = 6.",
        "BC = 4.",
        "SA vuông góc với (ABCD).",
        "SA = 8.",
        "Gọi M là trung điểm SA.",
        "Gọi N là trung điểm SB.",
        "Gọi P là trung điểm SC.",
        "Gọi Q là giao điểm của SD và (MNP).",
        "Dựng thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MNP).",
    ]
    facts_rect = [
        HB._f("f1", "solid", s_rect[0], solid="S.ABCD", solid_type="pyramid"),
        HB._f("f2", "polygon_shape", s_rect[1], points=["A", "B", "C", "D"], shape="rectangle"),
        HB._f("f3", "length", s_rect[2], points=["A", "B"], measure="segment", value="6"),
        HB._f("f4", "length", s_rect[3], points=["B", "C"], measure="segment", value="4"),
        HB._f("f5", "perpendicular", s_rect[4], points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("f6", "length", s_rect[5], points=["S", "A"], measure="segment", value="8"),
        HB._mid("f7", "M", "S", "A"),
        HB._mid("f8", "N", "S", "B"),
        HB._mid("f9", "P", "S", "C"),
        HB._ilp("f10", "Q", "SD", "MNP"),
        HB._f("f11", "section", s_rect[10], role="question", solid="S.ABCD", points=["M", "N", "P"]),
    ]
    res_rect = run_fact_route(" ".join(s_rect), {"facts": facts_rect})
    assert res_rect.status == "SERVED", (res_rect.code, res_rect.reason)
    sc_rect = res_rect.scene3d
    _assert_scene_core_invariants(sc_rect)
    pts_r = {o.get("notation") or o["id"]: o for o in sc_rect["objects"] if o["type"] == "point3"}
    assert pts_r["Q"]["origin"] == "derived"
    e_mn = _sub(_vec(pts_r["N"]["xyz"]), _vec(pts_r["M"]["xyz"]))
    e_np = _sub(_vec(pts_r["P"]["xyz"]), _vec(pts_r["N"]["xyz"]))
    assert _metric_dot(e_mn, e_mn, sc_rect.get("chart_metric")) == F(9)
    assert _metric_dot(e_np, e_np, sc_rect.get("chart_metric")) == F(4)

    # (2) Đáy hình thoi cạnh 4, góc BAD = 60°
    s_rh = [
        "Cho hình chóp S.ABCD.",
        "Đáy ABCD là hình thoi cạnh 4.",
        "Góc BAD bằng 60 độ.",
        "SA vuông góc với (ABCD).",
        "SA = 6.",
        "Gọi M là trung điểm SA.",
        "Gọi N là trung điểm SB.",
        "Gọi P là trung điểm SC.",
        "Gọi Q là giao điểm của SD và (MNP).",
        "Dựng thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MNP).",
    ]
    facts_rh = [
        HB._f("r1", "solid", s_rh[0], solid="S.ABCD", solid_type="pyramid"),
        HB._f("r2", "polygon_shape", s_rh[1], points=["A", "B", "C", "D"], shape="rhombus", value="4"),
        HB._f("r3", "angle", s_rh[2], points=["B", "A", "D"], measure="angle", value="60"),
        HB._f("r4", "perpendicular", s_rh[3], points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("r5", "length", s_rh[4], points=["S", "A"], measure="segment", value="6"),
        HB._mid("r6", "M", "S", "A"),
        HB._mid("r7", "N", "S", "B"),
        HB._mid("r8", "P", "S", "C"),
        HB._ilp("r9", "Q", "SD", "MNP"),
        HB._f("r10", "section", s_rh[9], role="question", solid="S.ABCD", points=["M", "N", "P"]),
    ]
    res_rh = run_fact_route(" ".join(s_rh), {"facts": facts_rh})
    if res_rh.status == "SERVED" and res_rh.scene3d is not None:
        sc_rh = res_rh.scene3d
        _assert_scene_core_invariants(sc_rh)
        pts_h = {o.get("notation") or o["id"]: o for o in sc_rh["objects"] if o["type"] == "point3"}
        u_mn = _sub(_vec(pts_h["N"]["xyz"]), _vec(pts_h["M"]["xyz"]))
        u_np = _sub(_vec(pts_h["P"]["xyz"]), _vec(pts_h["N"]["xyz"]))
        assert _metric_dot(u_mn, u_np, sc_rh.get("chart_metric")) != F(0)


# ============================================================================
# 3. §7 & §9 ĐA HỌ HÌNH, ĐỔI TÊN ĐỈNH, QUAN HỆ HÌNH HỌC & CA BIÊN MÂU THUẪN
# ============================================================================






def test_skew_lines_common_perpendicular_and_adversarial_edge_refusals() -> None:
    """§5.4 & §9: Khoảng cách hai đường chéo nhau sinh chứng chỉ `common_perpendicular` hợp lệ,
    và các ca biên mâu thuẫn (mặt phẳng không cắt mặt cầu `d = 7 > R = 5`, tam giác vi phạm bất đẳng thức)
    bị từ chối minh bạch (fail-closed)."""
    skew_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": (
            "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 2. "
            "Tính khoảng cách giữa hai đường thẳng chéo nhau AB và SC."
        ),
        "length_unit": "1",
        "solids": [
            {"solid_id": "pyr_sk", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD."}
        ],
        "premises": [
            {"kind": "base_is_square", "args": {"vertices": ["A", "B", "C", "D"], "side": "2"}, "quote": "Đáy ABCD là hình vuông cạnh 2.", "solid_id": "pyr_sk"},
            {"kind": "line_perp_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "quote": "SA vuông góc với (ABCD).", "solid_id": "pyr_sk"},
            {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2"}, "quote": "SA = 2.", "solid_id": "pyr_sk"},
        ],
        "simulation_goals": [
            {"goal_id": "g_sk", "kind": "construct_object", "target_solid_id": "pyr_sk", "quote": "Cho hình chóp S.ABCD."}
        ],
        "math_goals": [
            {
                "goal_id": "m_skew",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"line1": ["A", "B"], "line2": ["S", "C"]},
                "quote": "Tính khoảng cách giữa hai đường thẳng chéo nhau AB và SC.",
            }
        ],
    }
    res_skew = run_typed_fact_next_v2_route(skew_payload)
    assert res_skew.status == "SERVED", (res_skew.code, res_skew.reason)
    sc_skew = res_skew.scene3d
    assert sc_skew is not None
    _assert_scene_core_invariants(sc_skew)
    skew_qs = [
        o for o in sc_skew["objects"]
        if o["type"] == "quantity" and ((o.get("annotation") or {}).get("witness") or {}).get("relation") == "common_perpendicular"
    ]
    assert len(skew_qs) == 1

    # Ca biên 1: Mặt phẳng z - 7 = 0 cách tâm mặt cầu R = 5 một khoảng d = 7 > R (không cắt mặt cầu) -> từ chối fail-closed
    non_inter_sphere = {
        "schema_version": TYPED_FACT_NEXT_SCHEMA_VERSION,
        "problem_text": "Cho mặt cầu tâm I bán kính R = 5 và mặt phẳng (α) có phương trình z - 7 = 0. Dựng giao tuyến.",
        "solids": [{"solid_id": "sph_bad", "solid_type": "sphere", "notation": "(I)", "center": "I", "radius": "5", "quote": "mặt cầu tâm I bán kính R = 5"}],
        "derived_sections": [
            {
                "section_id": "sec_bad",
                "plane_name": "α",
                "target_solid_id": "sph_bad",
                "plane_kind": "plane_equation",
                "equation_coeffs": ["0", "0", "1", "-7"],
                "section_shape": "circle",
                "quote": "mặt phẳng (α) có phương trình z - 7 = 0",
            }
        ],
        "simulation_goals": [{"goal_id": "s_bad", "kind": "construct_plane_section", "target_section_id": "sec_bad", "quote": "Dựng giao tuyến"}],
    }
    res_bad_sph = run_typed_fact_next_route(non_inter_sphere)
    assert res_bad_sph.status != "SERVED"
    assert res_bad_sph.scene3d is None

    # Ca biên 2: Độ dài ba cạnh đáy vi phạm bất đẳng thức tam giác (AB = 1, BC = 2, AC = 10) -> từ chối fail-closed
    bad_tri_text = "Cho hình chóp S.ABC. AB = 1. BC = 2. AC = 10. SA vuông góc với (ABC). SA = 3. Tính thể tích khối chóp S.ABC."
    bad_tri_facts = {
        "facts": [
            HB._f("f1", "solid", "Cho hình chóp S.ABC.", solid="S.ABC", solid_type="pyramid"),
            HB._f("f2", "length", "AB = 1.", points=["A", "B"], measure="segment", value="1"),
            HB._f("f3", "length", "BC = 2.", points=["B", "C"], measure="segment", value="2"),
            HB._f("f4", "length", "AC = 10.", points=["A", "C"], measure="segment", value="10"),
            HB._f("f5", "perpendicular", "SA vuông góc với (ABC).", points_a=["S", "A"], points_b=["A", "B", "C"]),
            HB._f("f6", "length", "SA = 3.", points=["S", "A"], measure="segment", value="3"),
            HB._ask("q_v", "Tính thể tích khối chóp S.ABC.", "volume", solid="S.ABC"),
        ]
    }
    res_bad_tri = run_fact_route(bad_tri_text, bad_tri_facts)
    assert res_bad_tri.status != "SERVED"
    assert res_bad_tri.scene3d is None
