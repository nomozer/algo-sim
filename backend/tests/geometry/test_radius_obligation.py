# -*- coding: utf-8 -*-
"""NGHĨA VỤ `radius` — đóng lỗ ontology cuối mà V2 tìm ra. **0 lượt gọi model.**

    `RADIUS_OBLIGATION_COVERAGE`, 2026-09-03.

─── LỖ NÓ BỊT ─────────────────────────────────────────────────────────────

`CURVED_MODEL_ACCEPTANCE_V2`, đo bằng quota thật: taxonomy nghĩa vụ **không có
`radius`**, nên `analyze` buộc phải ép *"tính bán kính"* vào nghĩa vụ gần nhất
mà nó có từ để gọi — `distance`. Rồi `container` rơi vào khối cong:

    ball_1        distance(I)    → kiểu 'curved_solid' không hợp
    circumsphere  distance(OABC) → kiểu 'solid' không hợp

Cả hai sinh chương trình **ĐÚNG** (dùng `measure radius`) và vẫn chết. Không
phải lỗi mô hình: hợp đồng không cho nó một cách hợp lệ nào để nói điều đúng.

─── VÌ SAO ĐÂY LÀ MỘT WAVE RIÊNG, KHÔNG PHẢI PHẦN ĐUÔI ────────────────────

Wave trước (`CURVED_OBLIGATION_COVERAGE_BRIDGE`) kết luận
`RADIUS_OBLIGATION_NEEDED = NO` với lý do *"chưa có phép đo nào chứng minh là
cần"*. V2 **là** phép đo ấy. Lập luận cũ coi *"chưa có bằng chứng"* là bằng
chứng cho chiều ngược lại — và file này là chỗ sự sửa sai ấy được khoá lại.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.coverage_gate import check_structural_coverage
from app.simulation.semantic_program.measure_contract import (
    BANG_PHEP_DO,
    NGHIA_VU_DO,
    kieu_chu_the_nghia_vu,
)
from app.simulation.semantic_program.obligations import (
    OBLIGATION_KINDS,
    Obligation,
    accepts_container_type,
)
from app.simulation.semantic_program.request_contract import (
    InputFact,
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile

V2 = (Path(__file__).resolve().parents[3]
      / "docs/evaluation/geometry/curved-acceptance-v2/stage_8a_one_shot.json")


def _v2(case_id: str) -> dict:
    return next(x for x in json.loads(V2.read_text(encoding="utf-8"))["ca"]
                if x["id"] == case_id)


def _duong_san_pham(r: dict):
    """ĐÚNG đường sản phẩm, và **dùng hợp đồng THẬT của lượt V2**.

    V2 lưu `RequestContract` (thiếu sót của runner V1 đã sửa), nên ở đây không
    phải tái dựng gì — nghĩa vụ, dữ kiện và đề đều là thứ `analyze` thật sự
    phát ra. Đó là điều làm phép replay này thành bằng chứng, không phải một
    bài tập dựng lại.
    """
    hd = r["request_contract"]
    return verify_and_compile(
        RequestContract(
            problem_text=hd["problem_text"],
            input_facts=tuple(InputFact(**f) for f in hd["input_facts"]),
            obligations=tuple(Obligation(**o) for o in hd["obligations"])),
        SemanticProgramSpec.model_validate(r["chuong_trinh"]))


# ══ R10 · MỘT THẨM QUYỀN ═════════════════════════════════════════════════
def test_R10_radius_dan_xuat_tu_BANG_PHEP_DO_khong_viet_tay():
    """`MEASURE_COMPATIBILITY_AUTHORITIES = 1` — vẫn đúng sau khi thêm."""
    assert NGHIA_VU_DO["radius"] == ("radius",)
    assert OBLIGATION_KINDS["radius"] == kieu_chu_the_nghia_vu("radius")
    assert OBLIGATION_KINDS["radius"] == frozenset(BANG_PHEP_DO["radius"].kieu_of)


def test_R10b_KHONG_co_nghia_vu_radius_theo_tung_hinh():
    """`PROBLEM_FAMILY_RADIUS_OBLIGATIONS = 0`."""
    for cam in ("sphere_radius", "circle_radius", "cylinder_radius",
                "cone_radius", "ball_radius"):
        assert cam not in OBLIGATION_KINDS


def test_R10c_literal_bang_KHONG_chep_lai_radius():
    """Cùng cổng chống tái phát mà cầu nối đã dựng, nay phủ cả `radius`."""
    from app.simulation.semantic_program import obligations as O
    import inspect

    src = Path(inspect.getfile(O)).read_text(encoding="utf-8")
    dau = src.index("OBLIGATION_KINDS: dict[str, frozenset[str]] = {")
    than = src[dau:src.index("\n}", dau)]
    assert '"radius":' not in than


# ══ R4–R6 · CHỦ THỂ ══════════════════════════════════════════════════════
@pytest.mark.parametrize("kieu,mong", [
    ("circle3", True),        # R4
    ("curved_solid", True),   # R5
    ("solid", False),         # R6 — khối đa diện không có bán kính
    ("point3", False),
    ("plane3", False),
    ("polygon3", False),
])
def test_R4_R6_chu_the_cua_radius(kieu, mong):
    assert accepts_container_type("radius", kieu) is mong


# ══ R3 · `distance` KHÔNG BỊ NỚI ═════════════════════════════════════════
def test_R3_distance_giu_nguyen_ngu_nghia():
    """§6 — thêm `radius` không được làm `distance` rộng ra một ly."""
    assert OBLIGATION_KINDS["distance"] == frozenset(
        {"point3", "line3", "plane3"})
    for kieu in ("curved_solid", "circle3", "solid"):
        assert not accepts_container_type("distance", kieu)


def test_R3b_hai_nghia_vu_phan_biet_bang_SO_TOAN_HANG():
    """Prompt dạy phân biệt bằng **số toán hạng**, không bằng chữ trong đề.

    Dạy theo chữ là đúng cái bẫy `measure_contract §②` đã phải đi dọn với
    `angle_cos`: tên phép đo chứa sẵn chữ "cos" nên đề nào hỏi "côsin" là mô
    hình chọn nó, kể cả khi sai.
    """
    from app.ai import gemini

    md = (Path(gemini.SKILLS_DIR) / "geometry_analyze.md").read_text(
        encoding="utf-8")
    assert "`radius`" in md and "Tính bán kính" in md
    assert "số toán hạng" in md
    # `distance` vẫn phải được dạy là có `wrt`.
    assert "`wrt`" in md


# ══ R1–R2 · CÂU HỎI BÁN KÍNH CÓ TỪ ĐỂ GỌI ════════════════════════════════
def test_R1_R2_radius_co_trong_enum_analyze_hinh_hoc():
    """Không có dòng này thì mô hình **không có cách hợp lệ nào** để nói đúng —
    và nó sẽ ép vào `distance`, đúng như V2 đo được."""
    from app.simulation.semantic_program.domain_profile import (
        geometry_obligation_kinds,
    )

    assert "radius" in geometry_obligation_kinds()


def test_R1b_radius_thuoc_nhom_DAI_LUONG_khong_phai_QUAN_HE():
    """Witness của nó là một CON SỐ, không phải đối tượng thứ hai."""
    from app.simulation.semantic_program.coverage_gate import _QUAN_HE_HINH_HOC
    from app.simulation.semantic_program.obligations import WITNESS_FREE_KINDS

    assert "radius" not in _QUAN_HE_HINH_HOC
    assert "radius" not in WITNESS_FREE_KINDS


# ══ R7–R8 · REPLAY — PHÉP THỬ CHÍNH ═════════════════════════════════════
#
# ⚠️ **Hai chương trình V2 bị chặn đều hỏng vì lý do KHÔNG liên quan tới
# `radius`.** Đọc chúng ra mới thấy, và phải nói ra thay vì lặng lẽ đổi sang
# một ca dễ hơn:
#
#   V2 ball_1        khai `I` và `S` là `curved_solid` rồi không dựng cái nào
#                    ⇒ `AMBIGUOUS_FIRST_BINDING` ở thẩm định TĨNH
#   V2 circumsphere  dựng `circumsphere` nhưng KHÔNG khai nó trong
#                    `memory_declarations` ⇒ cổng phủ không hoà giải được tên
#
# Chương trình `ball_1` của **lượt V1** thì sạch (tĩnh OK, xuất xứ OK) và đo
# `radius` của một khối cong dựng đúng — nên nó là bằng chứng THẬT cho bản sửa
# này. Hai artifact đều bất biến; ta chỉ chọn cái nói được điều đang hỏi.
V1 = (Path(__file__).resolve().parents[3]
      / "docs/evaluation/geometry/curved-acceptance-v1/stage_8a_one_shot.json")


def _v1(case_id: str) -> dict:
    return next(x for x in json.loads(V1.read_text(encoding="utf-8"))["ca"]
                if x["id"] == case_id)


def _nghia_vu_radius(raw: dict) -> Obligation:
    """Nghĩa vụ `radius` trỏ đúng vật mà chương trình THẬT SỰ đo."""
    st = next(s for s in raw["statements"]
              if s.get("kind") == "assign"
              and s.get("expr", {}).get("quantity") == "radius")
    return Obligation(kind="radius", container=st["expr"]["of"],
                      params={"witness": st["target_var"]})


def test_R7_ball_1_nghia_vu_radius_KHONG_con_bi_cong_phu_chan():
    """`V2_BALL_1_SYSTEM_BLOCKER = CLOSED`.

    ⚠️ *"Không bị chặn"* ≠ *"ok=True"*. Cổng phủ trả `ok=False` cho **hai** mức
    khác hẳn nhau, và `route` chỉ CHẶN một:

        REQUESTED_OPERATION_UNCOVERED      không có đường tạo witness ⇒ CHẶN
        SEMANTIC_VERIFICATION_UNAVAILABLE  có đường, thiếu checker   ⇒ ĐI TIẾP

    `radius` chưa có checker (quyết định có chủ ý — xem `test_08`), nên nó rơi
    mức yếu. Đòi `ok=True` ở đây là đòi một thứ chính `route` không đòi.
    """
    raw = _v1("ball_1")["chuong_trinh"]
    kq = check_structural_coverage(
        RequestContract(problem_text=_v1("ball_1")["de"],
                        obligations=(_nghia_vu_radius(raw),)),
        SemanticProgramSpec.model_validate(raw))
    assert kq.error_code != "REQUESTED_OPERATION_UNCOVERED", list(kq.missing)
    assert kq.weak_kinds == ["radius"], kq.weak_kinds


def test_R7b_nghia_vu_CU_van_bac__chung_minh_lo_la_that():
    """Nửa còn lại: `distance` trên cùng chủ thể ấy VẪN bị chặn.

    Không có ca này thì không chứng minh được lỗ từng tồn tại — và mọi lời kể
    về nó chỉ là lời kể.
    """
    raw = _v1("ball_1")["chuong_trinh"]
    bk = _nghia_vu_radius(raw)
    kq = check_structural_coverage(
        RequestContract(problem_text=_v1("ball_1")["de"],
                        obligations=(Obligation(
                            kind="distance", container=bk.container,
                            params={"witness": bk.witness}),)),
        SemanticProgramSpec.model_validate(raw))
    assert kq.error_code == "REQUESTED_OPERATION_UNCOVERED"
    assert any("không hợp với nghĩa vụ" in m for m in kq.missing), list(kq.missing)


def test_R7c_ball_1_di_TRON_duong_san_pham_voi_nghia_vu_radius():
    """Không dừng ở cổng phủ: chạy tới cùng và để lại số ĐÚNG."""
    from app.simulation.geometry.radical import display

    r = _v1("ball_1")
    raw = r["chuong_trinh"]
    kq = verify_and_compile(
        RequestContract(problem_text=r["de"],
                        obligations=(_nghia_vu_radius(raw),)),
        SemanticProgramSpec.model_validate(raw))
    assert kq.executable, f"bị chặn ở '{kq.stage_reached}': {kq.reason}"
    # `servable=False` là ĐÚNG: `radius` chưa có checker.
    assert not kq.servable
    so = {display(v) for v in (kq.final_memory or {}).values()
          if type(v).__name__ in ("Fraction", "Radical")}
    # Đề V1: mặt cầu tâm I qua A, IA = 6 ⇒ R = 6, V = 288π. Kiểm tay.
    assert {"6", "288π"} <= so, so


def test_R8_hai_chuong_trinh_V2_hong_vi_LY_DO_KHAC__khoa_lai_su_that_ay():
    """`V2_RADIUS_SYSTEM_BLOCKERS_FIXED` phải đọc kèm ca này.

    Bản sửa gỡ đúng vật cản của HỆ. Hai chương trình V2 vẫn không chạy được, và
    **không phải vì `radius`** — chúng hỏng ở hai chỗ khác, cả hai thuộc mô
    hình. Khoá lại để không ai đọc "2/2 fixed" thành "hai ca ấy nay chạy".
    """
    from app.simulation.semantic_program.ir_static_check import kiem_tinh

    b = kiem_tinh(SemanticProgramSpec.model_validate(
        _v2("ball_1")["chuong_trinh"]))
    assert not b.ok and any("AMBIGUOUS_FIRST_BINDING" in i.dong()
                            for i in b.issues), [i.dong() for i in b.issues]

    raw = _v2("circumsphere")["chuong_trinh"]
    khai = {m["name"] for m in raw["memory_declarations"]}
    dung = {s["target_var"] for s in raw["statements"]
            if s.get("kind") == "construct_curved_solid"}
    assert dung and not (dung <= khai), (
        "chương trình V2 circumsphere lẽ ra dựng một khối cong KHÔNG khai")


# ══ R9 · R0 KHÔNG ĐƯỢC NỚI ═══════════════════════════════════════════════
def test_R9_radius_KHONG_mo_duong_khai_toa_do():
    """§11 — thêm một nghĩa vụ không được thành một cửa cho toạ độ bịa."""
    from app.simulation.semantic_program.grounding_gate import (
        _KIEU_DUOC_GIA_THIET,
        check_grounding,
    )

    assert _KIEU_DUOC_GIA_THIET == frozenset({"point3", "vector3"})
    raw = {
        "spec_version": "1.0", "title": "Bán kính mặt cầu",
        "description": "Một chương trình bịa tâm rồi đo bán kính.",
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
    assert not kq.ok
    assert any("I_bia" in x for x in kq.unresolved), kq.unresolved


# ══ §8 · KHÔNG THÊM `lateral_area` ═══════════════════════════════════════
def test_08_KHONG_them_lateral_area():
    """`LATERAL_AREA_TAXONOMY_CHANGED = NO` — chưa có phép đo nào chứng minh
    `analyze` gán nhầm nghĩa vụ cho câu *"diện tích xung quanh"*.

    ⚠️ Và lần này lập luận ấy phải đọc kèm bài học: cùng câu chữ đã dùng cho
    `radius` và ĐÃ SAI. Khác biệt là ở bằng chứng — V2 đo được `radius` bị ép
    vào `distance`; chưa lượt nào đo `lateral_area`. Nên đây là *"chưa biết"*,
    không phải *"không cần"*.
    """
    assert "lateral_area" not in OBLIGATION_KINDS
    assert "lateral_area" not in NGHIA_VU_DO
    assert "lateral_area" in BANG_PHEP_DO


# ══ §12 · KHÔNG TRÔI ═════════════════════════════════════════════════════
def test_12_MEASURE_COVERAGE_DRIFT_van_bang_0():
    lech = [f"{nv} ⊅ {q}.{k}"
            for nv, qs in NGHIA_VU_DO.items() for q in qs
            for k in BANG_PHEP_DO[q].kieu_of
            if not accepts_container_type(nv, k)]
    assert not lech, lech
