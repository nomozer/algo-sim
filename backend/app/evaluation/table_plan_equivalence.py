# -*- coding: utf-8 -*-
"""M17 W2B-PATCH2 §F — TƯƠNG ĐƯƠNG NGỮ NGHĨA hai kế hoạch truy vấn bảng.

Lớp ĐÁNH GIÁ (audit/runner), KHÔNG phải production. Dùng khi chấm một live case
"supported": nếu LLM sinh MỘT tầng thừa DUY NHẤT là non-null check trên chính
cột tổng hợp, và mục tiêu là vô hướng, thì kết quả vô hướng bằng nhau ⇒ coi hai
kế hoạch tương đương thay vì báo LỆCH.

Quy tắc HẸP — sáu điều kiện đồng thời (§F). KHÔNG được nới thành tolerance chung
cho mọi operation bị thêm: chỉ đúng non-null-trên-cột-agg, không predicate khác,
không projection/sort/limit thừa, mục tiêu vô hướng, hàm bỏ qua null, giá trị +
counted khớp.

Hàm tổng hợp BỎ QUA NULL theo hợp đồng engine (`_accumulate`): avg/sum/min/max
skip ô None; count(cột) skip None; count(*) (column=None) KHÔNG skip. Vì vậy chỉ
count(*) là ngoại lệ không tương đương với non-null filter.
"""

from __future__ import annotations

_NULL_IGNORING_FUNCS = ("avg", "sum", "min", "max", "count")
_STAGES = ("filter", "projection", "sort", "limit", "aggregate")


def _is_non_null_check(pred: object, column: str | None) -> bool:
    """pred có phải ĐÚNG một non-null check trên `column` không (không AND/OR,
    không predicate khác)?"""
    if not isinstance(pred, dict) or column is None:
        return False
    if pred.get("op") in ("and", "or"):
        return False
    return (pred.get("op") in ("!=", "is not null", "not_null")
            and pred.get("column") == column
            and pred.get("value") in (None, "null", ""))


def _present_stages(plan: dict) -> list[str]:
    out = []
    for s in _STAGES:
        v = plan.get(s)
        if s == "projection":
            if v:
                out.append(s)
        elif v is not None:
            out.append(s)
    return out


def _extra_stages(requested: dict, represented: dict) -> list[str]:
    req = set(_present_stages(requested))
    return [s for s in _STAGES if s in set(_present_stages(represented)) and s not in req]


def plans_equivalent(requested: dict, represented: dict) -> dict:
    """Trả bằng chứng máy-đọc {equivalent, rule, requested_plan, represented_plan,
    structural_difference}. `rule='identical'` khi trùng khít; `rule=
    'aggregate_ignores_null_filter'` khi áp quy tắc hẹp; None khi không tương đương."""
    diff_extra = _extra_stages(requested, represented)
    dropped = [s for s in _present_stages(requested)
               if s not in _present_stages(represented)]
    structural = {"extra_stages": diff_extra, "dropped_stages": dropped}
    base = {
        "requested_plan": requested, "represented_plan": represented,
        "structural_difference": structural,
    }

    # trùng khít
    if all(requested.get(s) == represented.get(s) for s in _STAGES) \
            and requested.get("wants_rows") == represented.get("wants_rows"):
        return {**base, "equivalent": True, "rule": "identical"}

    agg = requested.get("aggregate")
    rep_agg = represented.get("aggregate")

    # điều kiện 4: mục tiêu vô hướng (aggregate), KHÔNG cần trả rows
    if not isinstance(agg, dict) or requested.get("wants_rows") or represented.get("wants_rows"):
        return {**base, "equivalent": False, "rule": None}
    # aggregate hai bên phải KHỚP (cùng hàm + cùng cột)
    if agg != rep_agg:
        return {**base, "equivalent": False, "rule": None}
    # điều kiện 5: hàm phải bỏ qua null; count(*) (column None) KHÔNG bỏ qua
    func, col = agg.get("func"), agg.get("column")
    if func not in _NULL_IGNORING_FUNCS or (func == "count" and col is None):
        return {**base, "equivalent": False, "rule": None}
    # điều kiện 1+2+3: tầng thừa DUY NHẤT là filter, và filter là non-null trên
    # chính cột tổng hợp; không dropped; không projection/sort/limit thừa.
    if diff_extra != ["filter"] or dropped:
        return {**base, "equivalent": False, "rule": None}
    if not _is_non_null_check(represented.get("filter"), col):
        return {**base, "equivalent": False, "rule": None}

    return {**base, "equivalent": True, "rule": "aggregate_ignores_null_filter"}


def final_result_accepted(expected_final: dict, actual_final: dict,
                          requested_plan: dict, represented_plan: dict) -> dict:
    """§F — kết quả live có được chấp nhận không, KÈM bằng chứng.

    Chấp nhận khi: (a) khớp khít; HOẶC (b) hai kế hoạch tương đương theo quy tắc
    HẸP `plans_equivalent` VÀ giá trị+counted tổng hợp KHỚP (điều kiện 6). Chỉ
    khác `rows` không tự chấp nhận nếu không có aggregate scalar khớp."""
    if expected_final == actual_final:
        return {"accepted": True, "rule": "identical", "equivalence": None}
    eq = plans_equivalent(requested_plan, represented_plan)
    exp_agg = expected_final.get("aggregate")
    act_agg = actual_final.get("aggregate")
    accepted = bool(
        eq["equivalent"] and eq["rule"] != "identical"
        and exp_agg is not None and exp_agg == act_agg)
    return {"accepted": accepted,
            "rule": eq["rule"] if accepted else None,
            "equivalence": eq}


# ── §I — chính sách DỪNG cho supported case ──────────────────────
def supported_stop_reason(status, *, grounding_perfect, result_leakage,
                          dropped_stages) -> str | None:
    """Với case SUPPORTED, MỌI status ≠ "ok" là lỗi và phải dừng (vá lỗ hổng
    runner cũ chỉ bắt "error"). status=ok vẫn dừng nếu rò rỉ kết quả, thiếu
    tầng, hay grounding hỏng."""
    if status != "ok":
        return f"supported case status={status!r} (mong 'ok')"
    if result_leakage:
        return "candidate spec chứa kết quả cuối"
    if dropped_stages:
        return f"status=ok nhưng THIẾU TẦNG: {dropped_stages}"
    if grounding_perfect is False:
        return "grounding không hoàn hảo"
    return None


__all__ = ["final_result_accepted", "plans_equivalent", "supported_stop_reason"]
