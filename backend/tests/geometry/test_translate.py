# -*- coding: utf-8 -*-
"""TỊNH TIẾN ĐIỂM — phép affine `ĐIỂM + VECTƠ → ĐIỂM`. **0 API call.**

─── VÌ SAO PHÉP NÀY TỒN TẠI ───────────────────────────────────────────────

`SYNTHESIS_STABILITY_K3`: 9/9 lượt hỏng dừng ở schema, **10 lần cùng một hình
dạng** — `construct_point X = arith(+, var(P), vector_from_points(A,B))`.

`audit_translation_gap.py` chứng minh từ VĂN PHẠM rằng câu ấy không diễn đạt
được: không phép sinh điểm nào nhận vectơ, và không câu lệnh nào dựng đường/mặt
từ một điểm + một phương — nên cả đường vòng *"dựng đường qua P phương v rồi
chia đoạn"* cũng đóng (`construct_line` cần hai TÊN ĐIỂM, tức cần sẵn chính
điểm ta muốn dựng).

Trước phép này `vector3` là kiểu **chỉ-ghi**: dựng được, nhưng không phép dựng
nào tiêu thụ nó.

─── ĐIỀU BỘ TEST NÀY CỐ Ý LÀM ─────────────────────────────────────────────

Không chỉ kiểm đúng những hình dạng của bộ V2. Nếu chỉ thế thì ta đã thêm một
module theo dạng bài và gọi nó là primitive. Các ca dưới đây chứng minh phép
này **tổ hợp được**: lồng hai lần, đảo chiều, toạ độ phân số, và làm đầu vào
cho đường/mặt/giao/chiếu/đo.
"""
from __future__ import annotations

import typing
from fractions import Fraction

import pytest

from app.simulation.geometry.exact import Vec3
from app.simulation.geometry.kernel import translate
from app.simulation.semantic_program import contract as C
from app.simulation.semantic_program.interpreter import (
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.ir_static_check import (
    _CHU_KY,
    DIEM,
    VECTO,
    kiem_tinh,
)
from app.simulation.semantic_program.simulation_state import _provenance
from app.simulation.semantic_program.validator import validate_semantic_program


def v(x, y, z) -> Vec3:
    return Vec3(Fraction(x), Fraction(y), Fraction(z))


_GOC = [
    {"kind": "declare_point", "target_var": "A", "at": [0, 0, 0],
     "model_assumption": "gốc"},
    {"kind": "declare_point", "target_var": "B", "at": [2, 0, 0],
     "model_assumption": "trục x"},
    {"kind": "declare_point", "target_var": "D", "at": [0, 3, 0],
     "model_assumption": "trục y"},
    {"kind": "declare_point", "target_var": "E", "at": [0, 0, 5],
     "model_assumption": "trục z"},
]


def ct(stmts: list, decls: list | None = None) -> dict:
    return {
        "spec_version": "1.0", "title": "Tịnh tiến điểm theo vectơ",
        "description": "Phép affine ĐIỂM + VECTƠ → ĐIỂM.",
        "pedagogical_intent": "Một điểm dựng ra bằng phép tịnh tiến.",
        "memory_declarations": decls or [], "statements": _GOC + stmts}


def chay(spec: dict):
    r = validate_semantic_program(spec)
    if not r.ok:
        return r, None, None
    t = kiem_tinh(r.spec)
    if not t.ok:
        return r, t, None
    return r, t, SemanticProgramInterpreter().execute(r.spec)


def toa_do(mem, ten) -> tuple[str, str, str]:
    p = mem[ten]
    return (str(p.x), str(p.y), str(p.z))


_VECTO_AB = {"kind": "assign", "target_var": "u",
             "expr": {"kind": "vector_from_points",
                      "from_point": "A", "to_point": "B"}}


# ══ ① NHÂN — chính xác, không float ═════════════════════════════════════
def test_nhan_chinh_xac_voi_toa_do_phan_so():
    """§7 — `P = (1/2, -2/3, 3)`, `v = (2/5, 5/3, -1)` ⇒ `(9/10, 1, 2)`."""
    q = translate(v(Fraction(1, 2), Fraction(-2, 3), 3),
                  v(Fraction(2, 5), Fraction(5, 3), -1))
    assert (q.x, q.y, q.z) == (Fraction(9, 10), Fraction(1), Fraction(2))
    assert all(isinstance(c, Fraction) for c in (q.x, q.y, q.z)), \
        "float đã lọt vào miền số chính xác"


def test_tinh_tien_theo_vecto_KHONG_giu_nguyen_diem():
    """Vectơ không là phép đồng nhất — ca suy biến, nhưng nó hợp lệ."""
    p = v(1, 2, 3)
    assert translate(p, v(0, 0, 0)) == p


# ══ ② THẨM QUYỀN KIỂU — dẫn xuất, không bảng thứ hai ════════════════════
def test_chu_ky_khai_dung_DIEM_VECTO_ra_DIEM():
    toan_hang, tra_ve = _CHU_KY["translate"]
    assert tra_ve == DIEM
    assert dict((t, kieu) for t, kieu in toan_hang) == {
        "point": (DIEM,), "vector": (VECTO,)}


def test_translate_co_trong_CA_HAI_union():
    """`PointExpr` là thứ `construct_point` nhận; `ValueExpr` là thứ thẻ văn
    phạm render. Thêm vào một union mà quên union kia thì mô hình KHÔNG BAO
    GIỜ THẤY nó — đúng con bug đã giết 4/6 ca của CLEAN_BASELINE_V1."""
    def tags(u):
        return {a.__metadata__[0].tag
                for a in typing.get_args(typing.get_args(u)[0])}

    assert "translate" in tags(C.PointExpr)
    assert "translate" in tags(C.ValueExpr)


def test_the_van_pham_QUANG_CAO_translate():
    from app.simulation.semantic_program.grammar_card import grammar_card

    for mien in (None, "hinh_hoc"):
        the = grammar_card(mien)
        # Ký hiệu `tên<T>` — xem `test_named_operand_slots.py`. Ở ĐÚNG phép này
        # nó đáng giá nhất: `vector:tên` từng để mô hình lồng thẳng
        # `vector_from_points` vào 5 lần trong 4 đề.
        assert "translate: point:tên<point3> vector:tên<vector3>" in the, mien


def test_runtime_co_nhanh_thuc_thi():
    """Schema quảng cáo mà kernel không xử là một cửa mở ra lỗi runtime —
    tầng mô hình không sửa được."""
    import inspect

    from app.simulation.semantic_program import geometry_exec as GX
    from tests.source_scan import than_ma
    from pathlib import Path

    than = than_ma(Path(inspect.getfile(GX)))
    assert "K.translate(" in than


# ══ ③ TỔNG QUÁT — §18, phải TỔ HỢP được ═════════════════════════════════
def test_A_diem_bat_ky_cong_vecto_khai_thang():
    r, t, kq = chay(ct(
        [{"kind": "construct_point", "target_var": "Q",
          "expr": {"kind": "translate", "point": "B", "vector": "w"}}],
        [{"name": "w", "type": "vector3", "initial_value": [1, 1, 1],
          "model_assumption": "vectơ tịnh tiến chọn theo hệ trục"}]))
    assert r.ok and t.ok
    assert toa_do(kq.final_memory, "Q") == ("3", "1", "1")


def test_B_diem_cong_vector_from_points():
    """`C = B + AD` — hoàn thành hình bình hành. Đây là HỆ QUẢ của phép, không
    phải định nghĩa của nó."""
    r, t, kq = chay(ct(
        [{"kind": "assign", "target_var": "AD",
          "expr": {"kind": "vector_from_points",
                   "from_point": "A", "to_point": "D"}},
         {"kind": "construct_point", "target_var": "C",
          "expr": {"kind": "translate", "point": "B", "vector": "AD"}}]))
    assert r.ok, r.error
    assert t.ok, t.phan_hoi()
    assert toa_do(kq.final_memory, "C") == ("2", "3", "0")


def test_C_tinh_tien_HAI_LAN():
    r, t, kq = chay(ct(
        [dict(_VECTO_AB),
         {"kind": "assign", "target_var": "z",
          "expr": {"kind": "vector_from_points",
                   "from_point": "A", "to_point": "E"}},
         {"kind": "construct_point", "target_var": "Q",
          "expr": {"kind": "translate", "point": "D", "vector": "u"}},
         {"kind": "construct_point", "target_var": "R",
          "expr": {"kind": "translate", "point": "Q", "vector": "z"}}]))
    assert r.ok and t.ok
    assert toa_do(kq.final_memory, "R") == ("2", "3", "5")


def test_D_tinh_tien_NGUOC_tra_ve_diem_cu():
    """Vectơ ngược biểu diễn bằng `vector_from_points(B, A)` — IR không có
    phép phủ định vectơ, và ca này chứng minh nó KHÔNG CẦN có."""
    r, t, kq = chay(ct(
        [dict(_VECTO_AB),
         {"kind": "assign", "target_var": "u_nguoc",
          "expr": {"kind": "vector_from_points",
                   "from_point": "B", "to_point": "A"}},
         {"kind": "construct_point", "target_var": "Q",
          "expr": {"kind": "translate", "point": "D", "vector": "u"}},
         {"kind": "construct_point", "target_var": "R",
          "expr": {"kind": "translate", "point": "Q", "vector": "u_nguoc"}}]))
    assert r.ok and t.ok
    assert toa_do(kq.final_memory, "R") == toa_do(kq.final_memory, "D")


def test_E_toa_do_phan_so_di_het_duong_IR():
    r, t, kq = chay(ct(
        [{"kind": "declare_point", "target_var": "P", "at": ["1/2", "-2/3", 3],
          "model_assumption": "toạ độ phân số"},
         {"kind": "construct_point", "target_var": "Q",
          "expr": {"kind": "translate", "point": "P", "vector": "w"}}],
        [{"name": "w", "type": "vector3",
          "initial_value": ["2/5", "5/3", -1],
          "model_assumption": "vectơ phân số"}]))
    assert r.ok, r.error
    assert t.ok, t.phan_hoi()
    assert toa_do(kq.final_memory, "Q") == ("9/10", "1", "2")


@pytest.mark.parametrize("sau, kiem", [
    ({"kind": "construct_line", "target_var": "L",
      "through_a": "A", "through_b": "Q"}, "L"),
    ({"kind": "construct_plane", "target_var": "P3",
      "through": ["A", "B", "Q"]}, "P3"),
])
def test_FG_diem_tinh_tien_lam_dau_vao_cho_duong_va_mat(sau, kiem):
    r, t, kq = chay(ct(
        [{"kind": "assign", "target_var": "AD",
          "expr": {"kind": "vector_from_points",
                   "from_point": "A", "to_point": "D"}},
         {"kind": "construct_point", "target_var": "Q",
          "expr": {"kind": "translate", "point": "B", "vector": "AD"}},
         sau]))
    assert r.ok, r.error
    assert t.ok, t.phan_hoi()
    assert kq.final_memory.get(kiem) is not None


def test_H_diem_tinh_tien_di_tiep_vao_CHIEU_va_ĐO():
    r, t, kq = chay(ct(
        [{"kind": "assign", "target_var": "AD",
          "expr": {"kind": "vector_from_points",
                   "from_point": "A", "to_point": "D"}},
         {"kind": "construct_point", "target_var": "C",
          "expr": {"kind": "translate", "point": "B", "vector": "AD"}},
         {"kind": "construct_plane", "target_var": "day",
          "through": ["A", "B", "D"]},
         {"kind": "construct_point", "target_var": "H",
          "expr": {"kind": "project_onto", "point": "E", "target": "day"}},
         {"kind": "assign", "target_var": "d",
          "expr": {"kind": "measure", "quantity": "distance",
                   "of": "C", "wrt": "day"}}],
        # `d` là VÔ HƯỚNG nên phải khai: `assign` vào một tên chưa khai đưa
        # giá trị vào scope chứ không vào memory, và hợp đồng ràng buộc lần
        # đầu CỐ Ý không đụng vô hướng (chúng không qua kernel hình học).
        [{"name": "d", "type": "float"}]))
    assert r.ok, r.error
    assert t.ok, t.phan_hoi()
    # C nằm TRONG mặt đáy (z=0) ⇒ khoảng cách 0; H là chân chiếu của E.
    assert str(kq.final_memory["d"]) == "0"
    assert toa_do(kq.final_memory, "H") == ("0", "0", "0")


# ══ ④ BẤT BIẾN HÌNH HỌC — §19 ═══════════════════════════════════════════
def test_vecto_PQ_BANG_vecto_tinh_tien():
    """`Q = translate(P, AB)` ⇒ `PQ = AB`. Kiểm bằng toạ độ chính xác, không
    thêm một checker mới chỉ để có một test đẹp."""
    r, _, kq = chay(ct(
        [dict(_VECTO_AB),
         {"kind": "construct_point", "target_var": "Q",
          "expr": {"kind": "translate", "point": "D", "vector": "u"}},
         {"kind": "assign", "target_var": "DQ",
          "expr": {"kind": "vector_from_points",
                   "from_point": "D", "to_point": "Q"}}]))
    assert r.ok
    assert kq.final_memory["DQ"] == kq.final_memory["u"]


def test_khoang_cach_PQ_BANG_do_dai_vecto():
    r, _, kq = chay(ct(
        [dict(_VECTO_AB),
         {"kind": "construct_point", "target_var": "Q",
          "expr": {"kind": "translate", "point": "D", "vector": "u"}},
         {"kind": "assign", "target_var": "d",
          "expr": {"kind": "measure", "quantity": "distance",
                   "of": "D", "wrt": "Q"}}],
        # `d` VÔ HƯỚNG ⇒ phải khai; hợp đồng ràng buộc lần đầu cố ý không
        # đụng vô hướng, nên tên chưa khai vào scope chứ không vào memory.
        [{"name": "d", "type": "float"}]))
    assert r.ok
    # |AB| = 2 vì B = (2,0,0), A = gốc.
    assert str(kq.final_memory["d"]) == "2"


# ══ ⑤ XUẤT XỨ — §8 ══════════════════════════════════════════════════════
def test_provenance_giu_producer_VA_bao_dong_nguon():
    r, _, _ = chay(ct(
        [{"kind": "assign", "target_var": "AD",
          "expr": {"kind": "vector_from_points",
                   "from_point": "A", "to_point": "D"}},
         {"kind": "construct_point", "target_var": "C",
          "expr": {"kind": "translate", "point": "B", "vector": "AD"}}]))
    prov = _provenance(r.spec)
    assert prov["C"]["producer"] == "construct_point.translate"
    assert set(prov["C"]["sources"]) == {"B", "AD"}
    # Bao đóng phải với tới A và D qua `AD`.
    assert prov["AD"]["producer"] == "vector_from_points"
    assert set(prov["AD"]["sources"]) == {"A", "D"}


# ══ ⑥ TỪ CHỐI TĨNH — §12 ════════════════════════════════════════════════
@pytest.mark.parametrize("point, vector, vi_sao", [
    ("B", "D", "vectơ là một ĐIỂM"),
    ("u", "u", "điểm là một VECTƠ"),
    ("d_so", "u", "điểm là một SỐ"),
    ("B", "d_so", "vectơ là một SỐ"),
    ("KHONG_CO", "u", "tên chưa định nghĩa"),
])
def test_toan_hang_SAI_KIEU_chet_o_tang_TINH(point, vector, vi_sao):
    """Không để kiểu sai tới kernel: lỗi runtime KHÔNG được gửi ngược cho mô
    hình sửa, nên nó giết cả ca."""
    r, t, _ = chay(ct(
        [dict(_VECTO_AB),
         {"kind": "assign", "target_var": "d_so",
          "expr": {"kind": "literal", "value": 5}},
         {"kind": "construct_point", "target_var": "Q",
          "expr": {"kind": "translate", "point": point, "vector": vector}}]))
    assert not r.ok or (t is not None and not t.ok), (
        f"lọt xuống runtime: {vi_sao}")


# ══ ⑦ HỢP ĐỒNG RÀNG BUỘC LẦN ĐẦU — §11 ═════════════════════════════════
def test_khong_can_khai_truoc_dich():
    """`construct_point` tự đăng ký đích, và `translate` không phải ngoại lệ."""
    r, t, kq = chay(ct(
        [dict(_VECTO_AB),
         {"kind": "construct_point", "target_var": "Q",
          "expr": {"kind": "translate", "point": "D", "vector": "u"}}]))
    assert r.ok and t.ok
    assert "Q" not in {d.name for d in r.spec.memory_declarations}
    assert "Q" in kq.final_memory


def test_assign_sinh_diem_bang_translate_duoc_CHUAN_HOA():
    """`assign Q = translate(...)` sinh ra một ĐIỂM, nên hợp đồng ràng buộc
    lần đầu viết lại nó thành `construct_point` như mọi phép sinh điểm khác."""
    r, t, kq = chay(ct(
        [dict(_VECTO_AB),
         {"kind": "assign", "target_var": "Q",
          "expr": {"kind": "translate", "point": "D", "vector": "u"}}]))
    assert r.ok and t.ok
    assert [s.kind for s in r.spec.statements].count("construct_point") == 1
    assert "Q" in kq.final_memory


# ══ ⑧ TRUNG THỰC NĂNG LỰC — §9 ══════════════════════════════════════════
def test_van_CHAN_diem_bia_khai_toa_do_tho():
    """Phép mới tăng khả năng DỰNG, không được nới R0."""
    from app.simulation.semantic_program.grounding_gate import (
        ERR_RUA_NANG_LUC,
        check_grounding,
    )
    from app.simulation.semantic_program.request_contract import RequestContract

    de = ("Cho hình bình hành ABDE. Gọi Q là điểm sao cho BQ song song AD. "
          "Tính khoảng cách từ Q đến A.")
    r, _, _ = chay(ct(
        [{"kind": "declare_point", "target_var": "K", "at": [9, 9, 9],
          "model_assumption": "điểm phụ tôi cần"}]))
    g = check_grounding(RequestContract(problem_text=de), r.spec)
    assert not g.ok and g.error_code == ERR_RUA_NANG_LUC


def test_diem_TINH_TIEN_khong_bi_doi_source_fact_id():
    """§10 — điểm DỰNG RA có producer, nên grounding không đòi nó có trong đề."""
    from app.simulation.semantic_program.grounding_gate import check_grounding
    from app.simulation.semantic_program.request_contract import RequestContract

    de = "Cho hình bình hành ABDE. Tính khoảng cách từ đỉnh thứ tư đến A."
    r, _, _ = chay(ct(
        [{"kind": "assign", "target_var": "AD",
          "expr": {"kind": "vector_from_points",
                   "from_point": "A", "to_point": "D"}},
         {"kind": "construct_point", "target_var": "Q_moi",
          "expr": {"kind": "translate", "point": "B", "vector": "AD"}}]))
    g = check_grounding(RequestContract(problem_text=de), r.spec)
    assert g.ok, g.unresolved
