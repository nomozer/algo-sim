# -*- coding: utf-8 -*-
"""Port Python của scan-interpreter (M12) — mirror `frontend/src/core/scan.ts`.

Backend KHÔNG dựng timeline cho học sinh (đó là việc của engine frontend);
port này chỉ để (a) validator server-side chặn spec sai trước khi trả envelope,
(b) harness chấm HÀNH VI spec do LLM sinh. Phải giữ CÙNG LUẬT với scan.ts —
đổi một bên thì đổi cả hai (xem CODE_INDEX, mirror-obligation).

Không eval, không code sinh ra: spec là cấu hình enum ĐÓNG; interpreter sở hữu
vòng lặp, biên dừng (≤ n), thứ tự duyệt.
"""

from __future__ import annotations

SCAN_VERSION = "1.0"

_CONDITION_OPS = (">", ">=", "<", "<=", "==", "!=")
_UPDATE_KINDS = ("replace_with_current", "add_current", "increment", "none")
_MARKINGS = ("running_winner", "match_highlight")
_STOPS = ("end_of_array", "first_match")

_TOP_KEYS = ("scan_version", "array", "labels", "seed", "compare", "update", "marking", "stop")


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _unknown_key(obj: dict, allowed: tuple[str, ...]) -> str | None:
    for k in obj:
        if k not in allowed:
            return k
    return None


def validate_scan_spec(raw) -> tuple[dict | None, str | None]:
    """Trả (spec, None) hoặc (None, lỗi tiếng Việt cho LLM retry) — mirror validateScanSpec."""
    if not isinstance(raw, dict):
        return None, "Spec không phải đối tượng JSON."
    bad = _unknown_key(raw, _TOP_KEYS)
    if bad:
        return None, f'Khóa lạ ở cấp cao nhất: "{bad}".'
    if raw.get("scan_version") != SCAN_VERSION:
        return None, f'scan_version phải là "{SCAN_VERSION}".'

    arr = raw.get("array")
    if not isinstance(arr, list) or len(arr) < 1 or not all(_is_num(x) for x in arr):
        return None, "array phải là mảng số có ≥ 1 phần tử."
    n = len(arr)

    labels = raw.get("labels")
    if labels is not None:
        if not isinstance(labels, list) or len(labels) != n or not all(isinstance(x, str) for x in labels):
            return None, "labels (nếu có) phải là mảng chuỗi cùng độ dài với array."

    seed = raw.get("seed")
    if not isinstance(seed, dict):
        return None, "seed phải là object."
    if seed.get("from") == "first_element":
        bad = _unknown_key(seed, ("from", "varName", "trackIndexVar"))
        if bad:
            return None, f'Khóa lạ trong seed: "{bad}".'
        if not isinstance(seed.get("varName"), str) or not seed["varName"]:
            return None, "seed.varName phải là chuỗi không rỗng."
        tiv = seed.get("trackIndexVar")
        if tiv is not None and (not isinstance(tiv, str) or not tiv):
            return None, "seed.trackIndexVar (nếu có) phải là chuỗi không rỗng."
    elif seed.get("from") == "constant":
        bad = _unknown_key(seed, ("from", "varName", "value"))
        if bad:
            return None, f'Khóa lạ trong seed: "{bad}".'
        if not isinstance(seed.get("varName"), str) or not seed["varName"]:
            return None, "seed.varName phải là chuỗi không rỗng."
        if not _is_num(seed.get("value")):
            return None, "seed.value (constant) phải là số."
    else:
        return None, f"seed.from lạ: {seed.get('from')!r}."

    compare = raw.get("compare")
    if not isinstance(compare, dict):
        return None, "compare phải là object."
    if compare.get("op") not in _CONDITION_OPS:
        return None, f"compare.op lạ: {compare.get('op')!r}."
    if compare.get("kind") == "to_accumulator":
        bad = _unknown_key(compare, ("kind", "op"))
        if bad:
            return None, f'Khóa lạ trong compare: "{bad}".'
    elif compare.get("kind") == "to_constant":
        bad = _unknown_key(compare, ("kind", "op", "value"))
        if bad:
            return None, f'Khóa lạ trong compare: "{bad}".'
        if not _is_num(compare.get("value")):
            return None, "compare.value (to_constant) phải là số."
    else:
        return None, f"compare.kind lạ: {compare.get('kind')!r}."

    update = raw.get("update")
    if not isinstance(update, dict) or _unknown_key(update, ("kind",)):
        return None, "update phải là object chỉ có 'kind'."
    if update.get("kind") not in _UPDATE_KINDS:
        return None, f"update.kind lạ: {update.get('kind')!r}."
    if raw.get("marking") not in _MARKINGS:
        return None, f"marking lạ: {raw.get('marking')!r}."
    if raw.get("stop") not in _STOPS:
        return None, f"stop lạ: {raw.get('stop')!r}."

    # Coherence — mirror TS: giữ họ = quét trên GIÁ TRỊ phần tử
    if raw["marking"] == "running_winner" and update["kind"] != "replace_with_current":
        return None, "marking running_winner đòi update replace_with_current."
    if compare["kind"] == "to_accumulator" and update["kind"] != "replace_with_current":
        return None, "compare to_accumulator đòi update replace_with_current (so với hằng thì dùng to_constant)."

    return raw, None


def _op_holds(x: float, y: float, op: str) -> bool:
    return {
        ">": x > y,
        ">=": x >= y,
        "<": x < y,
        "<=": x <= y,
        "==": x == y,
        "!=": x != y,
    }[op]


def run_scan(spec: dict) -> dict:
    """Chạy spec ĐÃ hợp lệ → tóm tắt hành vi (mirror ngữ nghĩa runScan bản TS).

    Trả: decisions (chuỗi kết quả so sánh), final_vars, final_marks,
    found_index (first_match; None nếu không), steps (số bước ước theo luật TS).
    """
    arr = list(spec["array"])
    n = len(arr)
    seed, compare, update = spec["seed"], spec["compare"], spec["update"]
    marking, stop = spec["marking"], spec["stop"]

    vars_: dict[str, float] = {}
    marks: dict[int, str] = {}
    decisions: list[str] = []
    steps = 1  # bước seed

    if seed["from"] == "first_element":
        acc = arr[0]
        acc_index = 0
        vars_[seed["varName"]] = acc
        if seed.get("trackIndexVar"):
            vars_[seed["trackIndexVar"]] = 0
        if marking == "running_winner":
            marks[0] = "considering"
        start = 1
    else:
        acc = seed["value"]
        acc_index = 0
        vars_[seed["varName"]] = acc
        start = 0

    found_index: int | None = None
    for i in range(start, n):
        cur = arr[i]
        if compare["kind"] == "to_accumulator":
            hit = _op_holds(cur, acc, compare["op"])
            decisions.append(">" if cur > acc else "<" if cur < acc else "==")
        else:
            hit = _op_holds(cur, compare["value"], compare["op"])
            decisions.append("match" if hit else "no_match")
        steps += 1  # bước so sánh

        if not hit:
            marks[i] = "eliminated"
            continue

        if marking == "running_winner":
            marks[acc_index] = "eliminated"
        if update["kind"] == "replace_with_current":
            acc = cur
            acc_index = i
        elif update["kind"] == "add_current":
            acc += cur
        elif update["kind"] == "increment":
            acc += 1
        marks[i] = "considering" if marking == "running_winner" else "found"

        if update["kind"] != "none":
            vars_[seed["varName"]] = acc
            if seed["from"] == "first_element" and seed.get("trackIndexVar") and update["kind"] == "replace_with_current":
                vars_[seed["trackIndexVar"]] = i
            steps += 1  # bước cập nhật

        if stop == "first_match":
            found_index = i
            steps += 1  # bước done
            return {
                "decisions": decisions,
                "final_vars": vars_,
                "final_marks": marks,
                "found_index": found_index,
                "steps": steps,
            }

    if marking == "running_winner":
        marks = {acc_index: "found"}
    steps += 1  # bước done
    return {
        "decisions": decisions,
        "final_vars": vars_,
        "final_marks": marks,
        "found_index": None,
        "steps": steps,
    }
