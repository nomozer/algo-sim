# -*- coding: utf-8 -*-
"""Phân loại từng ô TÊN trong đầu ra THÔ của mô hình. **0 API call.**

§10 của `NAME_ONLY_CONTRACT_LIVE_PROBE`, và nó là metric chính của cả wave:
*ký hiệu `tên<T>` có đổi được cách mô hình VIẾT không* — câu ấy chỉ trả lời
được trên bản THÔ, trước mọi phép chuẩn hoá.

⚠️ **KHÔNG GỘP `WRAPPED_VAR` VỚI `NESTED_DERIVED_EXPR`.** Hai thứ khác hẳn
nhau: một cái là cái tên viết dài ra (gỡ bọc 1:1, không sinh gì), cái kia là
một phép dựng đặt nhầm chỗ (phải nâng thành một ràng buộc có tên). Gộp chúng
là mất đúng thứ phân biệt *"mô hình không biết cú pháp"* với *"mô hình không
biết phải tách câu lệnh"*.

─── "RAW_NAME" NGHĨA LÀ GÌ, VÀ NÓ KHÔNG NGHĨA LÀ GÌ ───────────────────────

`RAW_NAME` = đúng HÌNH DẠNG WIRE (một định danh trần) **và** kiểu tương thích
khi kiểu suy được từ chính chương trình thô. Kiểu **không** suy được ở mọi chỗ
— một tên ràng buộc bằng `assign … = arith(...)` không có kiểu tĩnh — nên ô ấy
vẫn tính `RAW_NAME`: nó đúng thứ metric này hỏi (cách viết), còn cái sai kiểu
đã có thẩm định tĩnh bắt và taxonomy ghi riêng. Không đếm một thứ hai lần.
"""
from __future__ import annotations

from typing import Any

from app.simulation.semantic_program.hoisting import O_TEN, _o_cua
from app.simulation.semantic_program.ir_static_check import (
    _CHU_KY, _KIEU_DUNG, SO_DO,
)

#: Năm kết cục, ĐÓNG. Thêm một loại là phải nghĩ xem nó có phải một loại thật.
LOAI = ("RAW_NAME", "WRAPPED_VAR", "NESTED_DERIVED_EXPR", "RAW_LITERAL",
        "WRONG_TYPE")


def _bang_kieu(spec: dict) -> dict[str, str]:
    """Tên → kiểu, suy từ CHÍNH chương trình thô. Không biết thì vắng mặt."""
    kieu: dict[str, str] = {}
    for d in (spec.get("memory_declarations") or ()):
        if isinstance(d, dict) and isinstance(d.get("name"), str):
            kieu[d["name"]] = d.get("type") or "unknown"

    def di(stmts) -> None:
        for st in stmts or ():
            if not isinstance(st, dict):
                continue
            k, ten = st.get("kind"), st.get("target_var")
            if isinstance(ten, str):
                if k in _KIEU_DUNG:
                    kieu[ten] = _KIEU_DUNG[k]
                elif k == "declare_point":
                    kieu[ten] = "point3"
                elif k == "assign":
                    e = st.get("expr")
                    ek = e.get("kind") if isinstance(e, dict) else None
                    if ek in _CHU_KY:
                        kieu[ten] = _CHU_KY[ek][1]
                    elif ek == "measure":
                        kieu[ten] = SO_DO
            for nhanh in ("body", "then_body", "else_body"):
                if isinstance(st.get(nhanh), list):
                    di(st[nhanh])

    di(spec.get("statements"))
    return kieu


def _loai_mot(gt: Any, nhan: tuple[str, ...], kieu: dict[str, str]) -> str:
    if isinstance(gt, str) and gt:
        that = kieu.get(gt)
        # Kiểu KHÔNG suy được ⇒ vẫn là `RAW_NAME`: xem docstring.
        if that and that != "unknown" and that not in nhan:
            return "WRONG_TYPE"
        return "RAW_NAME"
    if isinstance(gt, dict):
        k = gt.get("kind")
        if k == "var":
            return "WRAPPED_VAR"
        if k in _CHU_KY:
            return ("NESTED_DERIVED_EXPR" if _CHU_KY[k][1] in nhan
                    else "WRONG_TYPE")
        if k in (None, "literal"):
            return "RAW_LITERAL"
        return "WRONG_TYPE"          # `kind` ngoài văn phạm biểu thức
    return "RAW_LITERAL"             # mảng toạ độ, số, bool…


def phan_loai_o_ten(spec: dict) -> dict:
    """Mọi ô TÊN mô hình THẬT SỰ phát ra, kèm phán quyết từng ô."""
    if not isinstance(spec, dict):
        return {"tong": 0, "dem": {l: 0 for l in LOAI}, "chi_tiet": []}
    kieu = _bang_kieu(spec)
    chi_tiet: list[dict] = []

    def di(node: Any) -> None:
        if isinstance(node, list):
            for x in node:
                di(x)
            return
        if not isinstance(node, dict):
            return
        for truong, (nhan, la_ds) in _o_cua(node).items():
            gt = node.get(truong)
            if truong not in node:
                continue          # trường tuỳ chọn vắng mặt: KHÔNG phải một ô
            for x in (gt if la_ds and isinstance(gt, list) else [gt]):
                if x is None:
                    continue
                chi_tiet.append({
                    "chu": node.get("kind"), "truong": truong,
                    "nhan": list(nhan), "loai": _loai_mot(x, nhan, kieu),
                    "gia_tri": x if isinstance(x, str) else
                               (x.get("kind") if isinstance(x, dict)
                                else type(x).__name__),
                })
        for v in node.values():
            di(v)

    di(spec.get("statements") or [])
    dem = {l: sum(1 for c in chi_tiet if c["loai"] == l) for l in LOAI}
    return {"tong": len(chi_tiet), "dem": dem, "chi_tiet": chi_tiet}


def toa_do_ky_hieu(spec: dict) -> list[str]:
    """§14 — toạ độ KHÔNG hữu tỉ trong một khai báo điểm/vectơ."""
    from app.simulation.semantic_program.ir_static_check import _la_huu_ti

    ra = []
    for d in (spec.get("memory_declarations") or ()):
        if not isinstance(d, dict) or d.get("type") not in ("point3", "vector3"):
            continue
        gt = d.get("initial_value")
        if isinstance(gt, list):
            ra += [f"{d.get('name')}[{i}]" for i, x in enumerate(gt)
                   if not _la_huu_ti(x)]
    for st in (spec.get("statements") or ()):
        if isinstance(st, dict) and st.get("kind") == "declare_point":
            gt = st.get("at")
            if isinstance(gt, list):
                ra += [f"{st.get('target_var')}.at[{i}]"
                       for i, x in enumerate(gt) if not _la_huu_ti(x)]
    return ra


#: Guard: bảng ô của bộ phân loại phải LÀ bảng thẩm quyền, không phải bản chép.
assert set(O_TEN), "O_TEN rỗng — bộ phân loại đang nhìn một hợp đồng trống"
