# -*- coding: utf-8 -*-
"""RÀNG BUỘC LẦN ĐẦU — một ngữ nghĩa, quyết TRƯỚC runtime. **0 API call.**

─── LỖ NÓ BỊT ─────────────────────────────────────────────────────────────

`CLEAN_BASELINE_V1` mất 4/6 ca vì `assign M = midpoint(B,C)` với `M` chưa khai:
schema ✓, thẩm định tĩnh ✓, **runtime NÉM `GEOMETRY_UNDECLARED`**.

Cơ chế: `_set_var` đưa tên chưa khai vào `scope_stack`, còn kernel hình học chỉ
đọc `self.memory`. Phép tính CHẠY, giá trị ĐÚNG, và câu lệnh kế tiếp mới chết —
một tiền điều kiện TĨNH bị canh ở tầng runtime, nơi vòng sửa không với tới.

─── HAI KHÁI NIỆM, TÁCH HẲN ───────────────────────────────────────────────

    RÀNG BUỘC LẦN ĐẦU   tên chưa tồn tại → tạo vật dẫn xuất
    GÁN LẠI             tên đã tồn tại → cập nhật giá trị

Không được để hai thứ ấy phân biệt nhau ở runtime bằng *"dict đã có khoá
chưa"* — đó chính là hình dạng của con bug.

─── BA THỨ HỢP ĐỒNG CỐ Ý KHÔNG LÀM ────────────────────────────────────────

① Không nâng trong nhánh (`if`/`while`) — nâng là khai một tên ở scope ngoài
  rồi để nó mang `None` khi nhánh không chạy, đúng món nợ
  `RUNTIME_NONE_OPERAND_REACHABLE` mà §4 cấm nới.
② Không đụng giá trị vô hướng — chúng không đi qua kernel hình học và vẫn
  chạy đúng.
③ Không tự đăng ký giá trị thô — nếu không thì đây là cửa sau của cổng trung
  thực năng lực.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.grounding_gate import (
    ERR_RUA_NANG_LUC,
    check_grounding,
)
from app.simulation.semantic_program.interpreter import (
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.ir_static_check import (
    ERR_RANG_BUOC_MO_HO,
    ERR_RANG_BUOC_TRONG_NHANH,
    kiem_tinh,
)
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.simulation_state import _provenance
from app.simulation.semantic_program.validator import validate_semantic_program

DE = ("Cho tứ diện ABCD có AB, AC, AD đôi một vuông góc và AB = AC = AD = 2. "
      "Gọi M là trung điểm của BC. Tính khoảng cách từ M đến A.")

_GOC = [
    {"kind": "declare_point", "target_var": "A", "at": [0, 0, 0],
     "model_assumption": "gốc"},
    {"kind": "declare_point", "target_var": "B", "at": [2, 0, 0],
     "model_assumption": "trục x"},
    {"kind": "declare_point", "target_var": "C", "at": [0, 2, 0],
     "model_assumption": "trục y"},
    {"kind": "declare_point", "target_var": "D", "at": [0, 0, 2],
     "model_assumption": "trục z"},
]


def ct(stmts: list, decls: list | None = None) -> dict:
    return {
        "spec_version": "1.0", "title": "Ràng buộc lần đầu",
        "description": "Một ngữ nghĩa cho ràng buộc lần đầu.",
        "pedagogical_intent": "Tên được tạo ra ở đâu và ai thấy nó.",
        "memory_declarations": decls or [], "statements": _GOC + stmts,
    }


def chay(spec):
    """`(validator, tĩnh, runtime)` — ba tầng, một lượt."""
    v = validate_semantic_program(spec)
    if not v.ok:
        return v, None, None
    t = kiem_tinh(v.spec)
    if not t.ok:
        return v, t, None
    try:
        return v, t, SemanticProgramInterpreter().execute(v.spec)
    except Exception as e:  # noqa: BLE001
        return v, t, e


# ══ ① RÀNG BUỘC LẦN ĐẦU — dạng chuẩn tắc ════════════════════════════════
@pytest.mark.parametrize("expr, kieu_mong", [
    ({"kind": "midpoint", "a": "B", "b": "C"}, "point3"),
    ({"kind": "divide_segment", "a": "B", "b": "C", "ratio": "1/3"}, "point3"),
])
def test_diem_chua_khai_thanh_construct_point(expr, kieu_mong):
    """`assign` sinh ra ĐIỂM được viết lại thành `construct_point` — dạng
    chuẩn tắc, có sẵn memory + provenance."""
    v, t, kq = chay(ct([{"kind": "assign", "target_var": "X", "expr": expr}]))
    assert v.ok and t.ok
    assert not isinstance(kq, Exception), kq
    assert "X" in kq.final_memory, "giá trị không vào memory — kernel sẽ mù"
    kinds = [s.kind for s in v.spec.statements]
    assert "construct_point" in kinds and "assign" not in kinds
    # KHÔNG có khai báo cho `X`, và đó là ĐÚNG: `construct_point` tự đăng ký
    # đích. Thêm một khai báo nữa là dựng dạng chuẩn tắc khác với chính nó.
    assert "X" not in {d.name for d in v.spec.memory_declarations}
    from app.simulation.geometry.exact import Vec3

    assert isinstance(kq.final_memory["X"], Vec3), kieu_mong


def test_vecto_chua_khai_GIU_assign_nhung_duoc_khai():
    """IR không có `construct_vector`, nên `assign` là lối DUY NHẤT — nó phải
    chạy, và tên phải vào memory."""
    v, t, kq = chay(ct([{"kind": "assign", "target_var": "u",
                         "expr": {"kind": "vector_from_points",
                                  "from_point": "A", "to_point": "B"}}]))
    assert v.ok and t.ok and not isinstance(kq, Exception)
    assert "u" in kq.final_memory
    assert [s.kind for s in v.spec.statements][-1] == "assign"
    assert {d.name: d.type for d in v.spec.memory_declarations}["u"] == "vector3"


def test_giao_hai_mat_chua_khai_cung_chay():
    v, t, kq = chay(ct(
        [{"kind": "construct_plane", "target_var": "P1",
          "through": ["A", "B", "C"]},
         {"kind": "construct_plane", "target_var": "P2",
          "through": ["A", "B", "D"]},
         {"kind": "assign", "target_var": "g",
          "expr": {"kind": "intersect_plane_plane",
                   "plane_a": "P1", "plane_b": "P2"}}]))
    assert v.ok and t.ok and not isinstance(kq, Exception)
    assert "g" in kq.final_memory


def test_vo_huong_chua_khai_VAN_nhu_cu():
    """§3② — giá trị vô hướng không đi qua kernel hình học, và `_record_step`
    chụp cả scope nên bộ chấm vẫn thấy. Sửa thứ không hỏng là mở một bề mặt
    hồi quy cho miền Tin học."""
    v, t, kq = chay(ct([{"kind": "assign", "target_var": "n",
                         "expr": {"kind": "literal", "value": 5}}]))
    assert v.ok and t.ok and not isinstance(kq, Exception)
    assert [s.kind for s in v.spec.statements][-1] == "assign"
    assert "n" not in {d.name for d in v.spec.memory_declarations}


# ══ ② GÁN LẠI — ngữ nghĩa KHÔNG đổi ═════════════════════════════════════
def test_gan_lai_diem_DA_KHAI_van_la_gan_lai():
    """Tên đã tồn tại ⇒ cập nhật, không tạo mới. Viết lại thành
    `construct_point` vẫn ghi đè đúng chỗ."""
    v, t, kq = chay(ct(
        [{"kind": "assign", "target_var": "X",
          "expr": {"kind": "midpoint", "a": "B", "b": "C"}},
         {"kind": "assign", "target_var": "X",
          "expr": {"kind": "midpoint", "a": "B", "b": "D"}}],
        [{"name": "X", "type": "point3"}]))
    assert v.ok and t.ok and not isinstance(kq, Exception)
    # midpoint(B(2,0,0), D(0,0,2)) = (1,0,1) — giá trị của lượt SAU.
    x = kq.final_memory["X"]
    assert (str(x.x), str(x.y), str(x.z)) == ("1", "0", "1")
    assert len([d for d in v.spec.memory_declarations if d.name == "X"]) == 1


# ══ ③ PROVENANCE — §5 ═══════════════════════════════════════════════════
@pytest.mark.parametrize("ten, expr, producer", [
    ("X", {"kind": "midpoint", "a": "B", "b": "C"},
     "construct_point.midpoint"),
    ("u", {"kind": "vector_from_points", "from_point": "A", "to_point": "B"},
     "vector_from_points"),
])
def test_vat_dan_xuat_GIU_producer(ten, expr, producer):
    """Mất producer là cảnh 3D thôi kể *nó được tạo ra thế nào* — tức mất đúng
    đóng góp của đề tài."""
    v, _, _ = chay(ct([{"kind": "assign", "target_var": ten, "expr": expr}]))
    p = _provenance(v.spec).get(ten)
    assert p and p["producer"] == producer, f"{ten}: {p}"
    assert set(p["sources"]) & {"A", "B", "C"}, "mất luôn danh sách nguồn"


def test_cong_TRUNG_THUC_van_chan_diem_bia():
    """§6 — chuẩn hoá KHÔNG được mở cửa sau. Một điểm tự bịa khai toạ độ thô
    vẫn phải bị chặn."""
    spec = ct([{"kind": "declare_point", "target_var": "K", "at": [9, 9, 9],
                "model_assumption": "điểm phụ tôi cần"}])
    v = validate_semantic_program(spec)
    assert v.ok
    g = check_grounding(RequestContract(problem_text=DE), v.spec)
    assert not g.ok and g.error_code == ERR_RUA_NANG_LUC


def test_KHONG_tu_dang_ky_gia_tri_tho():
    """`assign X = literal([1,2,3])` không được thành một điểm — nếu thành thì
    đây là đường vòng quanh cổng trung thực."""
    v, _, _ = chay(ct([{"kind": "assign", "target_var": "X",
                        "expr": {"kind": "literal", "value": [1, 2, 3]}}]))
    assert "X" not in {d.name for d in v.spec.memory_declarations}
    assert [s.kind for s in v.spec.statements][-1] == "assign"


# ══ ④ LUỒNG ĐIỀU KHIỂN — §4 ═════════════════════════════════════════════
def _trong_nhanh(sau: list | None = None) -> dict:
    return ct([
        {"kind": "if",
         "condition": {"kind": "compare", "op": "==",
                       "left": {"kind": "literal", "value": 1},
                       "right": {"kind": "literal", "value": 1}},
         "then_body": [{"kind": "assign", "target_var": "X",
                        "expr": {"kind": "midpoint", "a": "B", "b": "C"}}]},
    ] + (sau or []))


def test_rang_buoc_lan_dau_TRONG_NHANH_bi_TU_CHOI_TINH():
    """Nâng nó là khai một tên ở scope ngoài rồi để nó mang `None` khi nhánh
    không chạy — đúng món nợ §4 cấm nới. Từ chối ở tầng TĨNH, nơi còn sửa
    được, thay vì ở kernel."""
    v, t, _ = chay(_trong_nhanh())
    assert v.ok
    assert not t.ok
    assert any(i.error_code == ERR_RANG_BUOC_TRONG_NHANH for i in t.issues), \
        [i.error_code for i in t.issues]


def test_dung_SAU_nhanh_cung_bi_tu_choi():
    v, t, _ = chay(_trong_nhanh(
        [{"kind": "construct_line", "target_var": "L",
          "through_a": "A", "through_b": "X"}]))
    assert v.ok and not t.ok


def test_KHAI_TRUOC_roi_gan_trong_nhanh_thi_QUA():
    """Đường thoát ĐÚNG: khai ngoài, gán trong. Lúc ấy tên tồn tại ở mọi
    đường đi, và `None` là một giá trị khai báo chứ không phải một chỗ trống."""
    spec = _trong_nhanh()
    spec["memory_declarations"] = [{"name": "X", "type": "point3"}]
    v, t, _ = chay(spec)
    assert v.ok and t.ok, [i.error_code for i in (t.issues if t else [])]


# ══ ⑤ CA KHÔNG HỢP LỆ — §10, quyết TRƯỚC runtime ════════════════════════
def test_arith_lam_DIEM_bi_tu_choi_TINH_khong_phai_runtime():
    """`CLEAN_BASELINE_V1 cb_04`: mô hình viết `assign C = arith(...)` để tính
    một ĐIỂM. Kiểu không suy được ⇒ không nâng (§3A) ⇒ phải chết ở tầng tĩnh."""
    v, t, kq = chay(ct(
        [{"kind": "assign", "target_var": "C2",
          "expr": {"kind": "arith", "op": "+",
                   "left": {"kind": "literal", "value": 1},
                   "right": {"kind": "literal", "value": 1}}},
         {"kind": "construct_line", "target_var": "L",
          "through_a": "A", "through_b": "C2"}]))
    assert v.ok
    assert not t.ok, "lọt xuống runtime — đúng con bug wave này sửa"
    assert any(i.error_code == ERR_RANG_BUOC_MO_HO for i in t.issues), \
        [i.error_code for i in t.issues]
    assert kq is None


def test_KHONG_ca_nao_con_chet_o_runtime_vi_chua_khai():
    """§20 — bất biến trung tâm. Duyệt mọi dạng ràng buộc lần đầu hình học và
    đòi: hoặc tĩnh từ chối, hoặc runtime chạy. KHÔNG có ô thứ ba."""
    dang = [
        {"kind": "midpoint", "a": "B", "b": "C"},
        {"kind": "divide_segment", "a": "B", "b": "C", "ratio": "1/2"},
        {"kind": "vector_from_points", "from_point": "A", "to_point": "B"},
    ]
    for e in dang:
        v, t, kq = chay(ct(
            [{"kind": "assign", "target_var": "X", "expr": e},
             {"kind": "assign", "target_var": "d",
              "expr": {"kind": "measure", "quantity": "distance",
                       "of": "X", "wrt": "A"}}]))
        assert v.ok, e
        if not t.ok:
            continue                      # tĩnh từ chối — hợp lệ
        assert not isinstance(kq, Exception), (
            f"{e['kind']}: tĩnh cho qua rồi runtime ném {kq}")


# ══ ⑥ CHỐNG TRÔI — §15, tiêm lỗi thật ═══════════════════════════════════
def test_go_chuan_hoa_thi_bat_bien_DO():
    """Guard chưa từng đỏ là guard chưa được chứng minh.

    Tiêm lỗi bằng cách dựng CHÍNH chương trình mà chuẩn hoá tạo ra, nhưng bỏ
    bước nâng: `assign` giữ nguyên và `X` không được khai. Nó phải chết ở
    runtime — tức chứng minh chuẩn hoá là thứ đang giữ bất biến, chứ không
    phải một may mắn nào khác.

    Không soi chú thích hay docstring: một guard đọc văn bản chỉ chứng minh
    được rằng văn bản còn đó.
    """
    import copy

    from app.simulation.semantic_program.contract import (
        AssignStmt,
        SemanticProgramSpec,
    )

    spec = SemanticProgramSpec.model_validate(
        ct([{"kind": "assign", "target_var": "X",
             "expr": {"kind": "midpoint", "a": "B", "b": "C"}},
            {"kind": "construct_line", "target_var": "L",
             "through_a": "A", "through_b": "X"}]))
    # Chuẩn hoá đã biến câu lệnh ấy thành `construct_point` — kiểm trước, nếu
    # không thì phép tiêm dưới đây tiêm vào một chỗ không có gì.
    assert any(s.kind == "construct_point" and s.target_var == "X"
               for s in spec.statements), "không còn gì để hoàn nguyên"

    # HOÀN NGUYÊN đúng một bước: `construct_point X` → `assign X`, giữ nguyên
    # mọi thứ khác. Dựng thẳng đối tượng câu lệnh, KHÔNG đi qua
    # `model_validate` — đi qua thì chuẩn hoá lại chạy và phép tiêm bị hoàn
    # tác ngay lập tức.
    tho = copy.deepcopy(spec)
    tho.statements[:] = [
        AssignStmt(target_var=s.target_var, expr=s.expr)
        if s.kind == "construct_point" and s.target_var == "X" else s
        for s in tho.statements]

    with pytest.raises(Exception) as e:
        SemanticProgramInterpreter().execute(tho)
    assert "X" in str(e.value), (
        f"gỡ chuẩn hoá mà vẫn chạy — bất biến đang được giữ bởi thứ khác: {e}")
