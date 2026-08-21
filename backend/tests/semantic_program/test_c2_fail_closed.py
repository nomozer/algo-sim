# -*- coding: utf-8 -*-
"""C₂ phải FAIL-CLOSED — hai lỗi lượt pilot 4 đo được, không được quay lại.

Lượt pilot 4 cho một kết quả đáng sợ: trên 40 case, **giao của "hệ tự cho là
phát được" và "hệ trả lời đúng" là RỖNG**. Tầng kiểm chứng nội bộ sai theo cả
hai chiều, và mỗi chiều là một lỗi riêng:

    4a  C₂ CHẤP NHẬN RÁC       — chương trình đẩy node biểu thức chưa tính vào
                                 mảng, mọi cổng đều cho qua
    4b  C₂ TỪ CHỐI CÂU ĐÚNG    — `_pred_of` mặc định `any` khi vị từ lạ, nên
                                 "đếm theo điều kiện" hoá "đếm tất cả"

Dữ liệu dưới đây dựng lại KỊCH BẢN, không dùng lại 40 case pilot — tập đó đã bị
đốt và chỉ còn giá trị như nhật ký kỹ thuật.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.postconditions import (
    KhongKiemChungDuoc,
    _co_ast_chua_tinh,
    _pred_of,
    check_postconditions,
)
from app.simulation.semantic_program.request_contract import RequestContract


class _Buoc:
    def __init__(self, snap):
        self.memory_snapshot = snap


class _Chay:
    def __init__(self, snap):
        self.trace = [_Buoc(snap)]


def _hd(*obs):
    return RequestContract(obligations=tuple(obs))


# ── 4b. Vị từ không biểu diễn được ⇒ mức yếu, KHÔNG phải vi phạm ──
def test_vi_tu_la_thi_NEM_chu_khong_doan():
    ob = Obligation(kind="aggregate_matching", container="a",
                    params={"witness": "w", "op": "count", "pred": "nghich_dao"})
    with pytest.raises(KhongKiemChungDuoc, match="nghich_dao"):
        _pred_of(ob)


def test_vang_vi_tu_KHAC_voi_vi_tu_la():
    """Đề chỉ nói 'đếm số phần tử' thì không có vị từ, và đếm tất cả là ĐÚNG."""
    ob = Obligation(kind="aggregate_matching", container="a",
                    params={"witness": "w", "op": "count"})
    loc = _pred_of(ob)
    assert loc(1) and loc("x") and loc(None)


def test_dem_cap_nghich_dao_KHONG_bi_ket_toi_oan():
    """Kịch bản `sealed_006`: hệ trả 4 (ĐÚNG), checker cũ đòi 5 = len(dãy)."""
    hd = _hd(Obligation(kind="aggregate_matching", container="day_so",
                        params={"witness": "so_cap", "op": "count",
                                "pred": "cap_nghich_dao"}))
    kq = check_postconditions(hd, None, _Chay({"day_so": [3, 2, 1, 5, 4],
                                               "so_cap": 4}))
    assert kq.violations == [], (
        "checker không biểu diễn được vị từ mà vẫn kết tội chương trình đúng"
    )
    assert kq.error_code == "SEMANTIC_VERIFICATION_UNAVAILABLE"
    assert kq.weak_kinds == ["aggregate_matching"]


def test_dem_theo_nguong_TINH_DUOC_thi_van_kiem_binh_thuong():
    """Không được nới tay: vị từ CÓ trong bảng thì vẫn phải bắt sai."""
    hd = _hd(Obligation(kind="aggregate_matching", container="a",
                        params={"witness": "w", "op": "count",
                                "pred": "gt", "threshold": 3}))
    sai = check_postconditions(hd, None, _Chay({"a": [1, 5, 7, 2], "w": 3}))
    assert sai.violations and sai.error_code == "POSTCONDITION_VIOLATED"

    dung = check_postconditions(hd, None, _Chay({"a": [1, 5, 7, 2], "w": 2}))
    assert dung.ok


# ── 4a. Trạng thái chứa AST chưa tính ⇒ VI PHẠM ──────────────────
def test_nhan_dien_node_bieu_thuc_chua_tinh():
    ast = {"kind": "index", "container": "a", "index": {"kind": "var", "name": "i"}}
    assert _co_ast_chua_tinh(ast)
    assert _co_ast_chua_tinh([1, 2, ast])
    assert _co_ast_chua_tinh({"x": [ast]})
    # Giá trị thật thì không được báo nhầm.
    assert not _co_ast_chua_tinh([1, 2, 3])
    assert not _co_ast_chua_tinh({"a": 1, "b": [2, 3]})
    assert not _co_ast_chua_tinh("kind")


def test_day_ket_qua_chua_AST_la_VI_PHAM_chu_khong_duoc_phat():
    """Kịch bản `sealed_038`: hệ TỰ CHO LÀ PHÁT ĐƯỢC một mảng toàn node biểu
    thức chưa được tính. Đây là case duy nhất qua hết cổng nội bộ trong cả lượt
    pilot 4, và oracle độc lập nói nó SAI."""
    rac = [{"kind": "index", "container": "day_so_a",
            "index": {"kind": "var", "name": "i"}}] * 6
    hd = _hd(Obligation(kind="derived_sequence", container="day_so_a",
                        params={"witness": "ket_qua", "transform": "filter"}))
    kq = check_postconditions(hd, None, _Chay({"day_so_a": [1, 2, 2, 3, 4, 5, 5],
                                               "ket_qua": rac}))
    assert not kq.ok
    assert kq.error_code == "POSTCONDITION_VIOLATED"
    assert any("CHƯA ĐƯỢC TÍNH" in v for v in kq.violations), kq.violations


def test_kiem_AST_ap_cho_MOI_nghia_vu_khong_chi_derived_sequence():
    """Để từng checker tự lo thì mỗi checker mới lại là một lỗ."""
    rac = {"kind": "var", "name": "i"}
    hd = _hd(Obligation(kind="extremum", container="a",
                        params={"witness": "w", "cmp": "max"}))
    kq = check_postconditions(hd, None, _Chay({"a": [1, 2], "w": rac}))
    assert any("CHƯA ĐƯỢC TÍNH" in v for v in kq.violations), kq.violations


# ── Nối vào route: mức yếu của C₂ phải thành verification_gap ────
def test_route_doi_muc_yeu_cua_C2_thanh_verification_gap():
    from app.simulation.semantic_program.route import verify_and_compile

    from .test_route_wiring import ANALYZE_PAYLOAD, _spec_co_provenance
    from app.simulation.semantic_program.analyze_contract import (
        build_request_contract,
    )

    payload = dict(ANALYZE_PAYLOAD)
    payload["obligations"] = [
        {"kind": "aggregate_matching", "container": "arr", "witness": "max_val",
         "op": "count", "pred": "mot_vi_tu_la"},
    ]
    kq = verify_and_compile(build_request_contract(payload),
                            _spec_co_provenance())
    assert kq.executable is True, "máy chạy xong rồi"
    assert kq.servable is False
    assert kq.failure_category == "verification_gap", (
        f"vị từ không kiểm được mà báo {kq.failure_category} — kết tội oan"
    )
    assert "aggregate_matching" in kq.weak_kinds
