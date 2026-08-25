# -*- coding: utf-8 -*-
"""PHASE 6.8 — ĐIỂM DẪN XUẤT chỉ nhận PHÉP DỰNG. **0 API call.**

─── HAI LOẠI ĐIỂM, VÀ RANH GIỚI GIỮA CHÚNG THUỘC VỀ R0 ────────────────────

    ĐIỂM DỮ KIỆN    khai ở `memory_declarations` + `initial_value`, kèm
                    `source_fact_id` (đề cho) hoặc `model_assumption` (mô hình
                    tự chọn hệ trục). Grounding gác kênh này.

    ĐIỂM DẪN XUẤT   sinh bởi `construct_point`. Toạ độ do KERNEL tính.

─── BẰNG CHỨNG DẪN TỚI THAY ĐỔI NÀY ───────────────────────────────────────

`expr: ValueExpr` cho phép cả `arith`, `literal`, `index`, `peek`…
`eval_geometry_expr` từ chối chúng — nhưng ở **lúc chạy**. Hợp đồng nói HỢP LỆ,
engine nói KHÔNG, và mô hình tin hợp đồng:

    construct_point C = arith(B + D)

Xuất hiện ở Phase 6.7 (`2-the-tich-lan5`) **và** Phase 6.7.2 (`2-the-tich-lan2`)
— hai vòng đo độc lập, hai bản mã, cùng một câu lệnh.

Nặng hơn cả việc trượt: lỗi nổ ở EXECUTION, tức **sau** vòng sửa. Lỗi validator
đi ngược cho mô hình sửa (≤3 lượt); lỗi runtime thì không — `thu_that_bai` của
cả hai lượt đều RỖNG.
"""
from __future__ import annotations

import glob
import json
import typing
from pathlib import Path

import pytest

from app.simulation.semantic_program import contract as C
from app.simulation.semantic_program.validator import validate_semantic_program

GOC = Path(__file__).resolve().parents[3]

_DIEM_GOC = [
    {"name": n, "type": "point3", "initial_value": v,
     "model_assumption": "chọn hệ trục"}
    for n, v in [("A", [0, 0, 0]), ("B", [3, 0, 0]), ("D", [0, 3, 0]),
                 ("S", [0, 0, 4])]
]


def _thu(expr: dict):
    return validate_semantic_program({
        "title": "diem dan xuat chi nhan phep dung",
        "memory_declarations": _DIEM_GOC + [
            {"name": "mp", "type": "plane3"},
            {"name": "ln", "type": "line3"},
            {"name": "C", "type": "point3"}],
        "statements": [
            {"kind": "construct_plane", "target_var": "mp",
             "through": ["A", "B", "D"]},
            {"kind": "construct_line", "target_var": "ln",
             "through_a": "S", "through_b": "A"},
            {"kind": "construct_point", "target_var": "C", "expr": expr},
        ],
    })


# ══ CẤM: TỰ TÍNH TOẠ ĐỘ ═════════════════════════════════════════════════
def test_ARITH_bi_chan_o_bien_PARSE_chu_khong_luc_chay():
    """Chỗ bị chặn quan trọng ngang việc bị chặn.

    Ở biên parse thì lỗi đi ngược cho mô hình sửa trong ≤3 lượt. Ở lúc chạy thì
    không — và cả hai lượt đã đo đều có `thu_that_bai` RỖNG, tức không một lần
    thử lại nào.
    """
    r = _thu({"kind": "arith", "op": "+",
              "left": {"kind": "var", "name": "B"},
              "right": {"kind": "var", "name": "D"}})
    assert not r.ok
    assert "schema" in r.error.lower(), "phải là lỗi SCHEMA, không phải lỗi chạy"
    # Thông điệp Pydantic liệt kê đúng năm tag hợp lệ ⇒ mô hình biết sửa thế nào.
    assert "midpoint" in r.error and "arith" in r.error


def test_LITERAL_bi_chan__toa_do_thuoc_ve_KHAI_BAO():
    """Toạ độ đề cho hoặc mình chọn thì khai ở `memory_declarations`, nơi
    grounding gác. Nhét vào `construct_point` là đi vòng qua cổng ấy."""
    assert not _thu({"kind": "literal", "value": [3, 3, 0]}).ok


@pytest.mark.parametrize("kind,expr", [
    ("index", {"kind": "index", "container": "A", "index": {"kind": "literal", "value": 0}}),
    ("length", {"kind": "length", "target": {"kind": "var", "name": "A"}}),
    ("var", {"kind": "var", "name": "A"}),
])
def test_bieu_thuc_KHONG_SINH_DIEM_deu_bi_chan(kind, expr):
    """`var` cũng bị chặn: sao chép một điểm đã có KHÔNG phải một phép dựng."""
    assert not _thu(expr).ok, kind


def test_intersect_plane_plane_bi_chan__no_tra_DUONG_khong_tra_DIEM():
    """Vắng mặt CÓ CHỦ ĐÍCH trong `PointExpr`, không phải bỏ sót."""
    assert not _thu({"kind": "intersect_plane_plane",
                     "plane_a": "mp", "plane_b": "mp"}).ok


# ══ CHO: NĂM PHÉP DỰNG SINH RA ĐIỂM ═════════════════════════════════════
@pytest.mark.parametrize("expr", [
    {"kind": "midpoint", "a": "A", "b": "B"},
    {"kind": "divide_segment", "a": "A", "b": "B", "ratio": "1/3"},
    {"kind": "project_onto", "point": "S", "target": "mp"},
    {"kind": "intersect_line_plane", "line": "ln", "plane": "mp"},
    {"kind": "intersect_line_line", "line_a": "ln", "line_b": "ln"},
], ids=lambda e: e["kind"])
def test_moi_phep_dung_sinh_DIEM_van_hop_le(expr):
    """Thu hẹp KHÔNG được đóng một đường đúng nào."""
    r = _thu(expr)
    assert r.ok, r.error


def test_tap_PointExpr_DUNG_BANG_tap_kernel_tra_ve_Point3():
    """Đóng theo BẰNG CHỨNG, không theo suy đoán: năm biểu thức này là toàn bộ
    thứ `eval_geometry_expr` trả về một điểm."""
    tags = {a.__metadata__[0].tag
            for a in typing.get_args(typing.get_args(C.PointExpr)[0])}
    assert tags == {"intersect_line_plane", "intersect_line_line", "midpoint",
                    "project_onto", "divide_segment"}


def test_PointExpr_la_TAP_CON_THAT_SU_cua_ValueExpr():
    def tag(u):
        return {a.__metadata__[0].tag for a in typing.get_args(typing.get_args(u)[0])}

    assert tag(C.PointExpr) < tag(C.ValueExpr)


# ══ THẺ VĂN PHẠM PHẢI NÓI RA ════════════════════════════════════════════
def test_the_van_pham_GOI_DUNG_TEN_truong_nay():
    """Hợp đồng hẹp mà thẻ vẫn gọi là "biểu thức" thì mô hình vẫn hiểu là chỗ ấy
    nhận bất kỳ biểu thức nào — đúng cái hiểu đã đẻ ra `arith(B + D)`."""
    from app.simulation.semantic_program.grammar_card import grammar_card

    dong = [d for d in grammar_card().splitlines()
            if d.strip().startswith("construct_point:")]
    assert dong and "phép dựng ĐIỂM" in dong[0], dong
    # `assign` KHÔNG bị đổi nhãn — nó thật sự nhận mọi biểu thức.
    ga = [d for d in grammar_card().splitlines()
          if d.strip().startswith("assign:")]
    assert ga and "biểu thức" in ga[0]


# ══ KHÔNG PHÁ MỘT CHƯƠNG TRÌNH ĐÃ SINH NÀO ══════════════════════════════
def test_30_chuong_trinh_da_sinh_van_PARSE_duoc():
    """Bằng chứng thu hẹp không đóng đường đúng: đọc lại MỌI chương trình mô
    hình đã sinh ở hai vòng đo. Chỉ hai lượt `arith` được phép hỏng — và chúng
    vốn đã hỏng, chỉ hỏng muộn hơn."""
    hong, tong = [], 0
    for f in glob.glob(str(GOC / "docs/evaluation/geometry/stability-6.7*"
                           / "[0-9]*-lan*.json")):
        g = json.loads(Path(f).read_text(encoding="utf-8")).get("generated_program")
        if not g:
            continue
        tong += 1
        try:
            C.SemanticProgramSpec.model_validate(g)
        except Exception:  # noqa: BLE001
            hong.append(Path(f).stem)
    assert tong >= 25, f"chỉ đọc được {tong} chương trình"
    assert sorted(hong) == ["2-the-tich-lan2", "2-the-tich-lan5"], hong


# ══ ĐIỀU PHASE 6.8 CẤM ══════════════════════════════════════════════════
def test_KHONG_sua_kernel_va_KHONG_them_DSL_ngoai_hinh_hoc():
    from app.simulation.catalog import CATALOG
    from app.simulation.dsl.manifest import MANIFEST

    assert len(CATALOG) == 24, "không thêm target"
    # `PointExpr` KHÔNG thêm một `kind` nào vào `ValueExpr` — nó chỉ chọn ra một
    # tập con. Đó là khác biệt giữa "siết hợp đồng" và "mở rộng DSL".
    def tag(u):
        return {a.__metadata__[0].tag for a in typing.get_args(typing.get_args(u)[0])}

    assert tag(C.PointExpr) <= tag(C.ValueExpr)
    assert MANIFEST is not None
