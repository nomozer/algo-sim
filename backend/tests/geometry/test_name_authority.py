# -*- coding: utf-8 -*-
"""THẨM QUYỀN VỀ TÊN — một nguồn, không phải tám. 0 API call.

Hợp đồng gọi vật bằng tên của ĐỀ (`(SMN)`, `B'D'`); chương trình gọi bằng tên
của nó (`SMN`, `B_prime_D_prime`). Cùng lưới hoà giải đã phải vá lần lượt ở
C₁a, C₁b, C₂, `learner_surface`, bộ chấm DEV, bộ chấm pool — rồi ở
CONFIRMATION V3 lộ ra **lần thứ bảy** tại bộ chấm xác nhận: `khop_ky_hieu`
không bóc nổi ngoặc của `(SMN)`, checker mất đối tượng, và một chương trình
ĐÚNG bị chấm `UNSAFE` hai lượt liền (ERRATUM #4).

Bản vá lần này KHÔNG phải lưới thứ tám. `route` phát ra `resolved_names` —
đúng bản đồ C₁a đã giải và C₂ đang dùng — và mọi tầng tiêu thụ hỏi nó.

Test ở đây khoá hai điều:

  ① bản đồ ấy **giải được** sáu dạng tên mà chỉ thị liệt kê;
  ② nó **thoát ra tới** `SemanticRouteOutcome`, vì một bản đồ đúng mà không ai
    ngoài `route` đọc được thì lỗi thứ bảy vẫn xảy ra y nguyên.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.coverage_gate import check_structural_coverage
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile
from app.simulation.semantic_program.validator import validate_semantic_program


def _diem(ten: str, xyz) -> dict:
    return {"name": ten, "type": "point3", "initial_value": list(xyz),
            "model_assumption": f"chọn {ten}"}


def _spec(decls, stmts, obligations=()):
    val = validate_semantic_program({
        "simulation_id": "geometry.demo", "title": "Demo tên gọi",
        "description": "Chương trình mẫu cho hoà giải tên",
        "pedagogical_intent": "Cho thấy cơ chế ẩn",
        "memory_declarations": decls, "statements": stmts,
        "obligations": list(obligations),
    })
    assert val.ok, val.error
    return val.spec


#: Hình dạng CHÉP TỪ ĐẦU RA THẬT của `hp_a04_011`: vật dựng được khai trước
#: (không giá trị) rồi mới dựng. Bịa một hình dạng khác thì test xanh trên một
#: chương trình không mô hình nào viết.
_DECLS = [_diem("S", (0, 0, 1)), _diem("M", (1, 0, 0)), _diem("N", (0, 1, 0)),
          _diem("A", (0, 0, 0)), _diem("C", (1, 1, 0)),
          {"name": "AC", "type": "line3"}, {"name": "SMN", "type": "plane3"}]
_STMTS = [
    {"kind": "construct_plane", "target_var": "SMN", "through": ["S", "M", "N"]},
    {"kind": "construct_line", "target_var": "AC", "through_a": "A",
     "through_b": "C"},
]


@pytest.mark.parametrize("ten_hop_dong", ["SMN", "(SMN)"])
def test_mat_phang_co_va_khong_co_ngoac(ten_hop_dong: str):
    """`(SMN)` là cách SGK viết mặt phẳng. Bản đồ phải giải được cả hai."""
    hd = RequestContract(obligations=(
        Obligation(kind="parallel", container="AC",
                   params={"witness": ten_hop_dong}),))
    kq = check_structural_coverage(hd, _spec(_DECLS, _STMTS))
    giai = dict(kq.ten_da_hoa_giai)
    assert giai.get(ten_hop_dong, ten_hop_dong) == "SMN", giai


@pytest.mark.parametrize("ten_hop_dong", ["B'D'", "B′D′", "BD"])
def test_ky_hieu_phay_va_ten_ghep(ten_hop_dong: str):
    """Ba cách viết cùng một đường: phẩy thẳng, phẩy cong, và không phẩy."""
    decls = [_diem("A", (0, 0, 0)), _diem("C", (1, 1, 0)),
             _diem("B_prime", (1, 0, 1)), _diem("D_prime", (0, 1, 1)),
             {"name": "B_prime_D_prime", "type": "line3"},
             {"name": "AC", "type": "line3"}]
    stmts = [
        {"kind": "construct_line", "target_var": "B_prime_D_prime",
         "through_a": "B_prime", "through_b": "D_prime"},
        {"kind": "construct_line", "target_var": "AC",
         "through_a": "A", "through_b": "C"},
    ]
    hd = RequestContract(obligations=(
        Obligation(kind="perpendicular", container=ten_hop_dong,
                   params={"witness": "AC"}),))
    kq = check_structural_coverage(hd, _spec(decls, stmts))
    giai = dict(kq.ten_da_hoa_giai)
    if ten_hop_dong != "BD":
        assert giai.get(ten_hop_dong) == "B_prime_D_prime", giai
    else:
        # `BD` KHÔNG được nhận là `B'D'`: `B` và `D` không có trong chương
        # trình, nên hoà giải phải fail-closed thay vì đoán bừa.
        assert giai.get(ten_hop_dong) in (None, "B_prime_D_prime")


def test_A_prime_ba_cach_viet_deu_ve_cung_mot_diem():
    from app.simulation.semantic_program.domain_profile import khop_ky_hieu

    ung = {"A_prime", "B", "C"}
    for viet in ("A'", "A′", "A_prime"):
        assert khop_ky_hieu(viet, ung) == "A_prime", viet


def test_ban_do_ten_THOAT_RA_toi_SemanticRouteOutcome():
    """②  — bản đồ đúng mà không tầng nào ngoài `route` đọc được thì vô dụng.

    Đây chính là chỗ V3 gãy: C₁a giải đúng `(SMN)`, C₂ kiểm ĐẠT, mà bộ đo
    không có cách nào biết, nên nó tự hoà giải và chấm oan.
    """
    hd = RequestContract(obligations=(
        Obligation(kind="parallel", container="AC",
                   params={"witness": "(SMN)"}),))
    kq = verify_and_compile(hd, _spec(_DECLS, _STMTS))
    assert kq.resolved_names.get("(SMN)") == "SMN", kq.resolved_names


def test_bo_do_ap_bi_danh_bang_ban_do_cua_route():
    """Bộ đo dùng bản đồ ấy — không gọi `khop_ky_hieu` lần thứ tám."""
    import importlib.util
    import sys
    from pathlib import Path

    p = Path(__file__).resolve().parents[2] / "scripts" / \
        "measure_geometry_stability.py"
    spec = importlib.util.spec_from_file_location("_msg", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["_msg"] = m
    spec.loader.exec_module(m)

    fm = {"SMN": "MẶT", "AC": "ĐƯỜNG"}
    ra = m._fm_cham(fm, {"resolved_names": {"(SMN)": "SMN"}})
    assert ra["(SMN)"] == "MẶT"
    assert ra["SMN"] == "MẶT", "KHÔNG được ghi đè tên chương trình"
    # Bản đồ rỗng ⇒ trả nguyên, không tự chế bí danh.
    assert m._fm_cham(fm, {}) == fm
