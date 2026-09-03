# -*- coding: utf-8 -*-
"""CHECKER `radius` — đóng khoảng safe-serve. **0 lượt gọi model.**

    `RADIUS_VERIFICATION_BRIDGE`, 2026-09-03.

─── LỖ NÓ BỊT ─────────────────────────────────────────────────────────────

`RADIUS_OBLIGATION_COVERAGE` mở nghĩa vụ `radius` và cố ý **không** thêm
checker — vì thêm checker là một tuyên bố năng lực khác, và nó phải là một
quyết định riêng. Hệ quả đúng nhưng khó chịu:

    đề hỏi bán kính  →  executable = True   ·   servable = False

Hệ tính ra đúng `√3` rồi **không dám phục vụ** con số ấy. Wave này đóng đúng
khoảng đó, và không đóng gì khác.

─── ĐIỀU FILE NÀY CANH, NGOÀI VIỆC CHECKER CHẠY ───────────────────────────

**Checker phải CÓ RĂNG.** Một checker chỉ biết nói PASS là một checker chưa
được chứng minh — `test_T4_*` cho nó một giá trị sai và đòi nó bác.

**Và nó phải chính xác trên miền căn thức**, không chỉ trên `Fraction`:
`test_T3_*` dùng `R² = 3 ⇒ R = √3`, đúng ca mà một bộ chấm dùng float sẽ nói
dối.
"""
from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.simulation.geometry.curved import Circle3, CurvedSolid
from app.simulation.geometry.exact import Vec3
from app.simulation.geometry.radical import radical
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.geometry_obligations import (
    GEOMETRY_CHECKERS,
    check_radius,
)
from app.simulation.semantic_program.obligations import (
    Obligation,
    has_server_owned_checker,
)
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

v = Vec3.of
V1 = (Path(__file__).resolve().parents[3]
      / "docs/evaluation/geometry/curved-acceptance-v1/stage_8a_one_shot.json")


def _ob(container: str, witness: str, **params) -> Obligation:
    return Obligation(kind="radius", container=container,
                      params={"witness": witness, **params})


# ══ T1–T3 · CHECKER ĐÚNG TRÊN CẢ HAI CHỦ THỂ, CẢ HAI MIỀN SỐ ═════════════
def test_T1_radius_circle3_huu_ti():
    c = Circle3(v(0, 0, 0), v(0, 0, 1), F(16))
    assert check_radius({"C": c, "r": F(4)}, _ob("C", "r")) is None


def test_T2_radius_curved_solid_huu_ti():
    s = CurvedSolid("ball", v(0, 0, 0), None, v(6, 0, 0))
    assert check_radius({"S": s, "R": F(6)}, _ob("S", "R")) is None


def test_T3_radius_VO_TI_van_chinh_xac():
    """`R² = 3 ⇒ R = √3`. Đây là ca mà một bộ chấm dùng float sẽ nói dối:
    `1.7320508…² != 3` trong số thực máy."""
    s = CurvedSolid("ball", v(0, 0, 0), None, v(1, 1, 1))
    assert s.radius_sq == 3
    assert check_radius({"S": s, "R": radical(1, 3)}, _ob("S", "R")) is None


@pytest.mark.parametrize("loai,neo,vanh,r2", [
    ("ball", None, v(1, 1, 1), 3),
    ("cylinder", v(0, 0, 2), v(1, 0, 0), 1),
    ("cone", v(0, 0, 2), v(3, 0, 0), 9),
    # Trục XIÊN, bán kính vô tỉ — chống giả định hình dựng đứng theo `z`.
    ("cylinder", v(1, 2, 2), v(2, -1, 0), 5),
])
def test_T2b_MOT_checker_cho_ca_ba_hinh(loai, neo, vanh, r2):
    """`SHAPE_SPECIFIC_RADIUS_CHECKERS = 0` — chứng minh bằng cách chạy cùng
    một hàm trên cả ba `curved_kind`."""
    from app.simulation.geometry.radical import sqrt_rational

    s = CurvedSolid(loai, v(0, 0, 0), neo, vanh)
    assert s.radius_sq == r2
    assert check_radius({"S": s, "R": sqrt_rational(F(r2))},
                        _ob("S", "R")) is None


# ══ T4 · CHECKER CÓ RĂNG ═════════════════════════════════════════════════
@pytest.mark.parametrize("sai", [F(2), F(4), radical(1, 2), radical(2, 3)])
def test_T4_gia_tri_SAI_bi_bac(sai):
    """Một checker chỉ biết nói PASS là một checker chưa được chứng minh."""
    s = CurvedSolid("ball", v(0, 0, 0), None, v(1, 1, 1))   # R = √3
    loi = check_radius({"S": s, "R": sai}, _ob("S", "R"))
    assert loi and "không khớp" in loi, loi


def test_T4b_gia_tri_MONG_cua_de_sai_cung_bi_bac():
    """Hai đường vào đều phải có răng: giá trị chương trình KHAI, và giá trị
    ĐỀ MONG (`params.value`)."""
    s = CurvedSolid("ball", v(0, 0, 0), None, v(6, 0, 0))   # R = 6
    assert check_radius({"S": s, "R": F(6)},
                        _ob("S", "R", value="7")) is not None
    assert check_radius({"S": s, "R": F(6)},
                        _ob("S", "R", value="6")) is None


def test_T4c_can_thuc_viet_bang_CHU_doc_duoc():
    """Đề khai `sqrt(3)` — văn phạm hẹp của `parse_exact` là cửa DUY NHẤT căn
    thức đi vào hệ."""
    s = CurvedSolid("ball", v(0, 0, 0), None, v(1, 1, 1))
    assert check_radius({"S": s}, _ob("S", "", value="sqrt(3)")) is None
    assert check_radius({"S": s}, _ob("S", "", value="sqrt(5)")) is not None


# ══ T5 · CHỦ THỂ SAI ═════════════════════════════════════════════════════
@pytest.mark.parametrize("gt", [v(1, 2, 3), F(5), None, "x"])
def test_T5_chu_the_sai_bi_bac(gt):
    loi = check_radius({"X": gt, "R": F(1)}, _ob("X", "R"))
    assert loi and "circle3" in loi


def test_T5b_kieu_sai_bi_chan_TU_TANG_HOP_DONG_truoc_ca_checker():
    """Checker là lưới CUỐI. Cửa đầu vẫn là `BANG_PHEP_DO`, và nó không được
    nới ra chỉ vì nay đã có checker."""
    from app.simulation.semantic_program.obligations import (
        accepts_container_type,
    )

    for kieu in ("point3", "line3", "plane3", "polygon3", "solid"):
        assert not accepts_container_type("radius", kieu)


# ══ T6–T7 · ĐƯỜNG ĐẦY ĐỦ · SAFE-SERVE ════════════════════════════════════
def _chay(raw: dict, obs: tuple, de: str):
    return verify_and_compile(
        RequestContract(problem_text=de, obligations=obs),
        SemanticProgramSpec.model_validate(raw))


def test_T6_ball_1_V1_nay_SERVABLE():
    """`RADIUS_SAFE_SERVE`: `servable` False → True trên đúng chương trình mà
    `RADIUS_OBLIGATION_COVERAGE` đã dùng làm bằng chứng.

    Chương trình lấy nguyên văn từ artifact V1 (bất biến).
    """
    from app.simulation.geometry.radical import display

    r = next(x for x in json.loads(V1.read_text(encoding="utf-8"))["ca"]
             if x["id"] == "ball_1")
    raw = r["chuong_trinh"]
    st = next(s for s in raw["statements"]
              if s.get("kind") == "assign"
              and s.get("expr", {}).get("quantity") == "radius")
    kq = _chay(raw, (_ob(st["expr"]["of"], st["target_var"]),), r["de"])
    assert kq.executable, f"bị chặn ở '{kq.stage_reached}': {kq.reason}"
    assert kq.servable, f"vẫn không phục vụ được: {kq.reason} · {kq.weak_kinds}"
    so = {display(x) for x in (kq.final_memory or {}).values()
          if type(x).__name__ in ("Fraction", "Radical")}
    assert {"6", "288π"} <= so, so


def test_T7_circumsphere_SACH_di_tron_duong_va_SERVABLE():
    """Nhân chứng mặt cầu ngoại tiếp **dựng bằng hợp thành đã có** — không một
    primitive nào thêm cho riêng bài toán này.

    Tâm = giao ba mặt trung trực (`plane_perpendicular_to_line` của G4). Tứ
    diện vuông `O(0,0,0) A(2,0,0) B(0,2,0) C(0,0,2)` ⇒ tâm `(1,1,1)`, `R = √3`.

    ⚠️ KHÔNG dùng chương trình V2 — nó hỏng vì lỗi mô hình (dựng `circumsphere`
    mà không khai), và một nhân chứng phải chứng minh HỆ, không chứng minh một
    lượt sinh cụ thể.
    """
    from app.simulation.geometry.radical import display

    def mtt(P: str, Q: str, i: int) -> list[dict]:
        return [
            {"kind": "construct_point", "target_var": f"M{i}",
             "expr": {"kind": "midpoint", "a": P, "b": Q}},
            {"kind": "construct_line", "target_var": f"d{i}",
             "through_a": P, "through_b": Q},
            {"kind": "assign", "target_var": f"p{i}",
             "expr": {"kind": "plane_perpendicular_to_line",
                      "point": f"M{i}", "line": f"d{i}"}}]

    raw = {
        "spec_version": "1.0",
        "title": "Bán kính mặt cầu ngoại tiếp tứ diện vuông",
        "description": ("Cho tứ diện OABC có OA, OB, OC đôi một vuông góc và "
                        "OA = OB = OC = 2. Tính bán kính mặt cầu ngoại tiếp."),
        "pedagogical_intent": "Thấy tâm mặt cầu là giao của ba mặt trung trực.",
        "memory_declarations": [
            *[{"name": n, "type": "point3", "initial_value": xy,
               "model_assumption": "hệ trục do đề chọn"}
              for n, xy in (("O", [0, 0, 0]), ("A", [2, 0, 0]),
                            ("B", [0, 2, 0]), ("C", [0, 0, 2]))],
            *[{"name": f"M{i}", "type": "point3"} for i in (1, 2, 3)],
            *[{"name": f"d{i}", "type": "line3"} for i in (1, 2, 3)],
            *[{"name": f"p{i}", "type": "plane3"} for i in (1, 2, 3)],
            {"name": "g", "type": "line3"}, {"name": "I", "type": "point3"},
            {"name": "cau", "type": "curved_solid"},
            {"name": "R", "type": "float"},
        ],
        "statements": [
            *mtt("O", "A", 1), *mtt("O", "B", 2), *mtt("O", "C", 3),
            {"kind": "assign", "target_var": "g",
             "expr": {"kind": "intersect_plane_plane", "plane_a": "p1",
                      "plane_b": "p2"}},
            {"kind": "construct_point", "target_var": "I",
             "expr": {"kind": "intersect_line_plane", "line": "g",
                      "plane": "p3"}},
            {"kind": "construct_curved_solid", "target_var": "cau",
             "curved_kind": "ball", "anchor": "I", "rim_point": "O",
             "label": "(S)"},
            {"kind": "assign", "target_var": "R",
             "expr": {"kind": "measure", "quantity": "radius", "of": "cau"}},
        ],
        "visual_bindings": {"containers": [], "pointers": [], "value_boxes": []},
    }
    kq = _chay(raw, (_ob("cau", "R"),),
               "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc và "
               "OA = OB = OC = 2. Tính bán kính mặt cầu ngoại tiếp tứ diện OABC.")
    assert kq.executable, f"bị chặn ở '{kq.stage_reached}': {kq.reason}"
    assert kq.servable, f"vẫn không phục vụ được: {kq.reason} · {kq.weak_kinds}"
    I = kq.final_memory["I"]
    assert (I.x, I.y, I.z) == (1, 1, 1), "tâm do KERNEL tính, không do khai"
    assert display(kq.final_memory["R"]) == "√3"


# ══ T8–T9 · KHÔNG ĐỘNG CHẠM CHECKER CŨ ═══════════════════════════════════
def test_T8_T9_checker_cu_khong_doi_va_KHONG_them_cai_nao_khac():
    """§19 — wave này chỉ `radius`. Thêm tiện tay một checker khác là mở một
    tuyên bố năng lực không ai xin."""
    assert set(GEOMETRY_CHECKERS) == {
        "point_on_line", "point_on_plane", "parallel", "perpendicular",
        "coplanar", "section_matches", "distance", "angle", "volume",
        "radius"}
    for cam in ("lateral_area", "surface_area", "skew_lines", "line_in_plane"):
        assert cam not in GEOMETRY_CHECKERS


def test_T8b_distance_va_volume_van_chay_dung():
    from app.simulation.semantic_program.geometry_obligations import (
        check_distance,
        check_volume,
    )
    from app.simulation.geometry.section import box

    assert check_distance(
        {"A": v(0, 0, 0), "B": v(3, 0, 0), "d": F(3)},
        Obligation(kind="distance", container="A",
                   params={"witness": "d", "wrt": "B"})) is None
    kh = box(1, 1, 1)
    assert check_volume({"K": kh, "V": F(1)},
                        Obligation(kind="volume", container="K",
                                   params={"witness": "V"})) is None


# ══ T10 · R0 ═════════════════════════════════════════════════════════════
def test_T10_diem_BIA_van_bi_bac_TRUOC_khi_toi_verification():
    """Checker mới không được thành một cửa sau cho toạ độ bịa."""
    from app.simulation.semantic_program.grounding_gate import check_grounding

    raw = {
        "spec_version": "1.0", "title": "Bán kính mặt cầu ngoại tiếp",
        "description": "Chương trình bịa tâm rồi đo bán kính.",
        "pedagogical_intent": "Ca kiểm cổng xuất xứ.",
        "memory_declarations": [
            {"name": "A", "type": "point3", "initial_value": [0, 0, 0],
             "model_assumption": "hệ trục do đề chọn"},
            {"name": "I_bia", "type": "point3", "initial_value": [1, 1, 1],
             "model_assumption": "tâm mặt cầu ngoại tiếp"},
            {"name": "cau", "type": "curved_solid"},
            {"name": "R", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_curved_solid", "target_var": "cau",
             "curved_kind": "ball", "anchor": "I_bia", "rim_point": "A"},
            {"kind": "assign", "target_var": "R",
             "expr": {"kind": "measure", "quantity": "radius", "of": "cau"}},
        ],
        "visual_bindings": {"containers": [], "pointers": [], "value_boxes": []},
    }
    kq = check_grounding(
        RequestContract(problem_text="Cho tứ diện ABCD. Tính bán kính mặt cầu "
                                     "ngoại tiếp tứ diện."),
        SemanticProgramSpec.model_validate(raw))
    assert not kq.ok and any("I_bia" in x for x in kq.unresolved)


# ══ T11 · MỘT THẨM QUYỀN TƯƠNG THÍCH ═════════════════════════════════════
def test_T11_them_checker_KHONG_dung_toi_bang_tuong_thich():
    """`MEASURE_COMPATIBILITY_AUTHORITIES = 1` — vẫn đúng.

    Checker trả lời *"con số này có đúng không"*; `BANG_PHEP_DO` trả lời *"chủ
    thể này có hợp không"*. Trộn hai câu ấy là dựng lại đúng bản sao mà
    `CURVED_OBLIGATION_COVERAGE_BRIDGE` vừa gỡ.
    """
    import inspect

    from app.simulation.semantic_program.measure_contract import (
        BANG_PHEP_DO,
        kieu_chu_the_nghia_vu,
    )
    from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

    assert OBLIGATION_KINDS["radius"] == kieu_chu_the_nghia_vu("radius")
    assert OBLIGATION_KINDS["radius"] == frozenset(
        BANG_PHEP_DO["radius"].kieu_of)
    # Checker không được chép danh sách kiểu — nó `isinstance`, tức hỏi lớp
    # RUNTIME, không hỏi bảng khai.
    src = inspect.getsource(check_radius)
    assert '"circle3"' not in src and '"curved_solid"' not in src.split(
        "cần một")[0]


def test_T11b_has_server_owned_checker_nay_dung_cho_radius():
    assert has_server_owned_checker("radius")
