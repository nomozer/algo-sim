# -*- coding: utf-8 -*-
"""Ô toán hạng TÊN: nâng an toàn, gỡ bọc `var`, và R0 sau chuẩn hoá.

Tám ca A–H của `NAMED_GEOMETRY_OPERAND_ERGONOMICS §20`, cộng các guard chống
trôi giữa ba thẩm quyền (`_CHU_KY` · Pydantic · thẻ văn phạm).

LUẬT ĐỌC CẢ FILE: mỗi test hỏi *"hệ có còn từ chối đúng thứ phải từ chối
không"* trước khi hỏi *"hệ có nhận thêm được gì không"*. Một lớp tiện dụng chỉ
đáng tồn tại khi nó không mở thêm một cửa nào.
"""
from __future__ import annotations

import typing

import pytest
from pydantic import ValidationError

from app.simulation.semantic_program import contract as C
from app.simulation.semantic_program.grammar_card import grammar_card
from app.simulation.semantic_program.hoisting import (
    O_TEN, TIEN_TO_TAM, nang_bieu_thuc_long,
)
from app.simulation.semantic_program.ir_static_check import (
    _CHU_KY, _KIEU_DO, _TOAN_HANG_LENH, kiem_tinh,
)
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import build_simulation_state


def _khung(stmts, khai=None):
    """Một chương trình tối thiểu quanh bốn điểm gốc của một hình vuông đáy."""
    return {
        "title": "Ca kiểm ô toán hạng tên",
        "memory_declarations": [
            {"name": "A", "type": "point3", "initial_value": [0, 0, 0]},
            {"name": "B", "type": "point3", "initial_value": [2, 0, 0]},
            {"name": "D", "type": "point3", "initial_value": [0, 3, 0]},
            {"name": "S", "type": "point3", "initial_value": [0, 0, 4]},
            *(khai or []),
        ],
        "statements": stmts,
    }


_LONG_VECTO = {"kind": "vector_from_points", "from_point": "A", "to_point": "D"}


# ── A. Nâng được ────────────────────────────────────────────────────────────
def test_A_bieu_thuc_dung_long_duoc_NANG_thanh_rang_buoc_co_ten():
    """`translate(B, vector_from_points(A,D))` — đúng khuôn đã giết 2/4 lượt
    tổng hợp đầu của `FRESH_TRANSLATION_COMPOSITION_PROBE`."""
    spec = C.SemanticProgramSpec.model_validate(_khung([
        {"kind": "construct_point", "target_var": "C",
         "expr": {"kind": "translate", "point": "B", "vector": _LONG_VECTO}},
    ]))
    tam = [d for d in spec.memory_declarations if d.name.startswith(TIEN_TO_TAM)]
    assert len(tam) == 1 and tam[0].type == "vector3"

    # Câu lệnh dựng temp phải đứng TRƯỚC câu lệnh dùng nó — không có nó thì
    # thứ tự tôpô sai và kernel nhận `None`.
    ten = tam[0].name
    vt = [i for i, s in enumerate(spec.statements) if s.target_var == ten]
    dung = [i for i, s in enumerate(spec.statements) if s.target_var == "C"]
    assert vt and dung and vt[0] < dung[0]
    assert spec.statements[dung[0]].expr.vector == ten
    assert kiem_tinh(spec).ok


# ── B. Toạ độ thô — VẪN CHẾT ────────────────────────────────────────────────
def test_B_mang_toa_do_tho_o_o_TEN_bi_TU_CHOI():
    with pytest.raises(ValidationError) as e:
        C.SemanticProgramSpec.model_validate(_khung([
            {"kind": "construct_point", "target_var": "C",
             "expr": {"kind": "translate", "point": "A", "vector": [1, 2, 3]}},
        ]))
    assert "TÊN" in str(e.value)


# ── C. Điểm dạng dict thô — VẪN CHẾT ────────────────────────────────────────
def test_C_dict_toa_do_tho_o_o_TEN_bi_TU_CHOI():
    with pytest.raises(ValidationError):
        C.SemanticProgramSpec.model_validate(_khung([
            {"kind": "construct_point", "target_var": "C",
             "expr": {"kind": "translate", "point": "A",
                      "vector": {"x": 1, "y": 2, "z": 3}}},
        ]))


# ── D. Kiểu trả về sai — KHÔNG nâng ────────────────────────────────────────
def test_D_bieu_thuc_long_SAI_KIEU_khong_duoc_nang():
    """`midpoint` trả `point3`, còn `translate.vector` cần `vector3`.

    Nâng nó là dựng một `point3` rồi đưa vào một ô đòi `vector3` — tức tự tạo
    ra đúng lỗi kiểu mà `_CHU_KY` tồn tại để chặn.
    """
    tho = _khung([
        {"kind": "construct_point", "target_var": "C",
         "expr": {"kind": "translate", "point": "A",
                  "vector": {"kind": "midpoint", "a": "A", "b": "D"}}},
    ])
    assert nang_bieu_thuc_long(tho)["statements"] == tho["statements"]
    with pytest.raises(ValidationError):
        C.SemanticProgramSpec.model_validate(tho)


# ── E. `kind` lạ — KHÔNG nâng ──────────────────────────────────────────────
def test_E_bieu_thuc_long_KHONG_CO_TRONG_VAN_PHAM_bi_TU_CHOI():
    tho = _khung([
        {"kind": "construct_point", "target_var": "C",
         "expr": {"kind": "translate", "point": "A",
                  "vector": {"kind": "cross_product", "a": "A", "b": "D"}}},
    ])
    assert nang_bieu_thuc_long(tho)["statements"] == tho["statements"]
    with pytest.raises(ValidationError):
        C.SemanticProgramSpec.model_validate(tho)


# ── F. Rửa năng lực qua biểu thức lồng — VẪN CHẾT ──────────────────────────
def test_F_bieu_thuc_long_MANG_model_assumption_khong_duoc_nang():
    """Cửa sau đáng sợ nhất của phép nâng, và nó phải đóng.

    Một giả định mô hình tự đặt phải được KHAI ở một điểm gốc, nơi
    `grounding_gate` hỏi nó. Chở nó lậu trong một biểu thức lồng rồi để phép
    nâng biến thành một thực thể hợp lệ là đúng định nghĩa rửa năng lực.
    """
    tho = _khung([
        {"kind": "construct_point", "target_var": "C",
         "expr": {"kind": "translate", "point": "A",
                  "vector": {**_LONG_VECTO,
                             "model_assumption": "lấy AD = 3 cho gọn"}}},
    ])
    assert nang_bieu_thuc_long(tho)["statements"] == tho["statements"]
    with pytest.raises(ValidationError):
        C.SemanticProgramSpec.model_validate(tho)


# ── G. Trong nhánh — temp ở ĐÚNG khối ──────────────────────────────────────
def test_G_long_trong_nhanh_temp_sinh_CUNG_KHOI_khong_ra_scope_ngoai():
    """§14 — không đẩy temp ra ngoài, và không mở definite-assignment.

    Nhánh không chạy thì cả temp lẫn câu lệnh dùng nó đều không chạy, nên câu
    hỏi *"tên này đã có giá trị chưa"* không hề mở ra.
    """
    tho = _khung([
        {"kind": "if",
         "condition": {"kind": "compare", "op": "==",
                       "left": {"kind": "literal", "value": 1},
                       "right": {"kind": "literal", "value": 1}},
         "then_body": [
             {"kind": "construct_point", "target_var": "C",
              "expr": {"kind": "translate", "point": "B",
                       "vector": _LONG_VECTO}},
         ]},
    ])
    ra = nang_bieu_thuc_long(tho)
    ngoai = [s for s in ra["statements"]
             if str(s.get("target_var", "")).startswith(TIEN_TO_TAM)]
    assert not ngoai, "temp KHÔNG được sinh ở scope ngoài nhánh"
    trong = [s for s in ra["statements"][0]["then_body"]
             if str(s.get("target_var", "")).startswith(TIEN_TO_TAM)]
    assert len(trong) == 1
    assert ra["statements"][0]["then_body"].index(trong[0]) == 0


# ── H. Xuất xứ đi qua temp ─────────────────────────────────────────────────
def test_H_xuat_xu_dong_kin_qua_temp():
    """§12 — `C` phải truy được về `A`, `B`, `D`, không đứt ở temp."""
    spec = C.SemanticProgramSpec.model_validate(_khung([
        {"kind": "construct_point", "target_var": "C",
         "expr": {"kind": "translate", "point": "B", "vector": _LONG_VECTO}},
    ]))
    kq = SemanticProgramInterpreter().execute(spec)
    tam = next(d.name for d in spec.memory_declarations
               if d.name.startswith(TIEN_TO_TAM))

    canh = build_scene3d(build_simulation_state(spec, kq))
    theo_id = {o["id"]: o for o in canh["objects"]}
    assert "C" in theo_id, "điểm tịnh tiến phải có mặt trong cảnh"
    assert theo_id["C"]["producer"], "mất `producer` là mất xuất xứ"

    # Bao đóng nguồn: đi ngược `depends` từ `C` phải chạm tới cả ba điểm gốc.
    dat, ngan = set(), ["C"]
    while ngan:
        x = ngan.pop()
        if x in dat:
            continue
        dat.add(x)
        ngan.extend(theo_id.get(x, {}).get("depends", []) or [])
    nguon = {n for n in dat if not n.startswith(TIEN_TO_TAM)}
    assert {"A", "B", "D"} <= nguon | {tam}, f"bao đóng nguồn thiếu: {nguon}"


# ── §13 — temp có dấu, để tầng trình bày gộp được ──────────────────────────
def test_temp_diem_duoc_danh_dau_internal_tren_canh():
    """Vật do SERVER dựng vẫn nằm trong đồ thị, nhưng phải tự khai là nội bộ.

    Dùng biểu thức lồng SINH ĐIỂM (không phải vectơ): `vector3` không có trong
    `RENDER_HINT` nên temp vectơ không bao giờ chạm cảnh, và một test dựa vào
    điều đó sẽ xanh mà không chứng minh gì.
    """
    spec = C.SemanticProgramSpec.model_validate(_khung([
        {"kind": "construct_line", "target_var": "d",
         "through_a": "A",
         "through_b": {"kind": "midpoint", "a": "B", "b": "D"}},
    ]))
    tam = [d.name for d in spec.memory_declarations
           if d.name.startswith(TIEN_TO_TAM)]
    # Điểm ⇒ `construct_point`, tức KHÔNG cần khai báo (memory + xuất xứ sẵn).
    assert not tam
    ten = next(s.target_var for s in spec.statements
               if s.target_var.startswith(TIEN_TO_TAM))
    kq = SemanticProgramInterpreter().execute(spec)
    canh = build_scene3d(build_simulation_state(spec, kq))
    o = next(o for o in canh["objects"] if o["id"] == ten)
    assert "internal" in o["display_group"]
    assert "internal" not in next(
        x for x in canh["objects"] if x["id"] == "A")["display_group"]


# ── Gỡ bọc `var` — lớp ma sát ĐÔNG NHẤT trong lịch sử (16/23) ──────────────
def test_var_boc_quanh_mot_TEN_duoc_go_bọc_khong_sinh_temp():
    spec = C.SemanticProgramSpec.model_validate(_khung([
        {"kind": "construct_line", "target_var": "d",
         "through_a": {"kind": "var", "name": "A"},
         "through_b": {"kind": "var", "name": "B"}},
    ]))
    d = spec.statements[0]
    assert (d.through_a, d.through_b) == ("A", "B")
    assert not [x for x in spec.memory_declarations
                if x.name.startswith(TIEN_TO_TAM)], "gỡ bọc KHÔNG được đẻ temp"


def test_var_khong_co_ten_van_bi_TU_CHOI():
    """`{"kind":"var"}` rỗng không phải một tham chiếu — đừng gộp bừa."""
    with pytest.raises(ValidationError):
        C.SemanticProgramSpec.model_validate(_khung([
            {"kind": "construct_line", "target_var": "d",
             "through_a": {"kind": "var"}, "through_b": "B"},
        ]))


# ── §9 — R0 SAU chuẩn hoá ──────────────────────────────────────────────────
def test_R0_moi_toan_hang_hinh_hoc_van_la_TEN_sau_chuan_hoa():
    """Bất biến R0 áp lên chương trình ĐÃ chuẩn hoá, không lên bản thô.

    Đây là mệnh đề mà cả wave này đứng lên: lớp tiện dụng được phép nhận một
    hình dạng khác, nhưng thứ đi tiếp vào hệ phải là dạng chuẩn tắc — mọi ô
    toán hạng hình học là một chuỗi TÊN.
    """
    spec = C.SemanticProgramSpec.model_validate(_khung([
        {"kind": "construct_point", "target_var": "C",
         "expr": {"kind": "translate", "point": "B", "vector": _LONG_VECTO}},
        {"kind": "construct_line", "target_var": "d",
         "through_a": {"kind": "var", "name": "A"},
         "through_b": {"kind": "midpoint", "a": "B", "b": "D"}},
    ]))

    def _soi(node) -> None:
        for truong in O_TEN.get(getattr(node, "kind", None), {}):
            gt = getattr(node, truong, None)
            for x in (gt if isinstance(gt, list) else [gt]):
                assert x is None or isinstance(x, str), (
                    f"{node.kind}.{truong} còn là {type(x).__name__}")
        for con in ("expr", "body", "then_body", "else_body"):
            v = getattr(node, con, None)
            for x in (v if isinstance(v, list) else [v]):
                if x is not None and hasattr(x, "kind"):
                    _soi(x)

    for st in spec.statements:
        _soi(st)


# ── §21 — thẻ và schema KHÔNG được trôi khỏi nhau ─────────────────────────
def test_moi_o_TEN_cua_tham_quyen_la_mot_truong_GeometryName():
    """Dẫn danh sách ô từ `ir_static_check`, rồi soi lại từng trường Pydantic.

    Không chép tay: thêm một biểu thức vào `_CHU_KY` mà quên đánh
    `GeometryName` cho trường của nó là ĐỎ ngay — và cái quên ấy im lặng mở
    lại đúng cửa mà wave này vừa đóng.
    """
    theo_kind = {n: m for n, m in
                 [*_lay(C.ValueExpr), *_lay(C.SemanticStatement)]}
    thieu = []
    for kind, truongs in O_TEN.items():
        model = theo_kind.get(kind)
        assert model is not None, f"`{kind}` có trong thẩm quyền mà không có model"
        for truong in truongs:
            if not _la_geometry_name(model.model_fields[truong]):
                thieu.append(f"{kind}.{truong}")
    assert not thieu, (
        "các ô TÊN sau chưa dùng `GeometryName`, nên `{\"kind\":\"var\"}` và "
        f"toạ độ thô đi qua chúng bằng lời từ chối câm: {thieu}")


def test_measure_of_wrt_cung_la_GeometryName():
    """`measure` không nằm trong `O_TEN` (kiểu tuỳ `quantity`) nên phải soi riêng."""
    for truong in ("of", "wrt"):
        assert _la_geometry_name(C.MeasureExpr.model_fields[truong])
    assert set(_KIEU_DO) == set(
        typing.get_args(C.MeasureExpr.model_fields["quantity"].annotation))


def test_the_van_pham_in_kieu_cau_truc_cho_moi_o_TEN():
    """§3 — mô hình phải ĐỌC THẤY `tên<T>`, không phải `tên` trần."""
    the = grammar_card("hinh_hoc")
    for kind, truongs in O_TEN.items():
        if kind not in the:
            continue
        for truong, (kieu, _) in truongs.items():
            assert f"{truong}:tên<{'|'.join(kieu)}>" in the or \
                   f"{truong}:[tên<{'|'.join(kieu)}>" in the, (
                f"thẻ không in kiểu cấu trúc cho `{kind}.{truong}`")


def test_bang_o_TEN_phu_het_hai_bang_tham_quyen():
    """`O_TEN` là DẪN XUẤT — nếu nó lệch `_CHU_KY`/`_TOAN_HANG_LENH` thì bộ
    nâng và thẻ đang nói về một hợp đồng khác thứ hệ cưỡng chế."""
    assert set(O_TEN) == set(_CHU_KY) | set(_TOAN_HANG_LENH)
    for k, (thamso, _) in _CHU_KY.items():
        assert {t for t, _ in thamso} == set(O_TEN[k])
    for k, ts in _TOAN_HANG_LENH.items():
        assert {t for t, _, _ in ts} == set(O_TEN[k])


# ── phụ trợ ────────────────────────────────────────────────────────────────
def _lay(alias):
    ra = []
    for arg in typing.get_args(typing.get_args(alias)[0]):
        model = typing.get_args(arg)[0] if typing.get_args(arg) else arg
        if isinstance(model, type):
            k = model.model_fields.get("kind")
            if k:
                ra.append((typing.get_args(k.annotation)[0], model))
    return ra


def _co_bien(x) -> bool:
    """`Annotated[..., BeforeValidator(canonical_geometry_name)]` ở BẤT KỲ đâu."""
    for m in getattr(x, "__metadata__", ()) or ():
        if getattr(m, "func", None) is C.canonical_geometry_name:
            return True
    return any(_co_bien(c) for c in typing.get_args(x))


def _la_geometry_name(f) -> bool:
    """Trường này có đi qua `canonical_geometry_name` không?

    So bằng HÀM, không bằng tên kiểu — và phải soi HAI chỗ, vì Pydantic để
    metadata ở hai nơi khác nhau tuỳ hình dạng trường:

      · trường TRẦN (`a: GeometryName`) — Pydantic bóc `Annotated`, đẩy
        `BeforeValidator` sang `FieldInfo.metadata`, còn `.annotation` là `str`;
      · trong union hay list (`Optional[GeometryName]`, `list[GeometryName]`) —
        không bóc được, `Annotated` còn nguyên trong `.annotation`.

    Chỉ soi một chỗ thì guard xanh ở nửa số trường và mù ở nửa kia — đúng lớp
    lỗi mà `grammar_card._la_ten` vừa dính ở cùng bản vá này.
    """
    for m in getattr(f, "metadata", ()) or ():
        if getattr(m, "func", None) is C.canonical_geometry_name:
            return True
    return _co_bien(f.annotation)
