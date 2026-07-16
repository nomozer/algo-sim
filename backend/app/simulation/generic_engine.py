"""Port Python của generic engine (M7) — CHỈ để kiểm tra ngữ nghĩa server-side.

Cùng luật tất định với engine TS ở frontend (valuesOf + buildTimeline).
Không phải engine chạy giao diện (đó là TS); bản này để harness đánh giá
có thể THỰC THI spec đã compose mà kiểm hành vi (§6).
"""

from __future__ import annotations

import math


class GenericEvaluationError(Exception):
    """M13 §3.4 — typed failure tại ranh giới executor; KHÔNG bao giờ thành 0."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def rule_targets(spec: dict) -> set[str]:
    return {r["target"] for r in spec.get("rules", [])}


def initial_base(spec: dict) -> dict[str, float]:
    targets = rule_targets(spec)
    base: dict[str, float] = {}
    for o in spec.get("objects", []):
        if "value" in o and o["id"] not in targets:
            base[o["id"]] = o["value"]
    return base


def _eval_rule(rule: dict, values: dict[str, float]) -> float:
    inputs = []
    for i in rule.get("inputs", []):
        if i not in values:
            raise GenericEvaluationError("invalid_numeric_source", f'input "{i}" chưa có giá trị')
        inputs.append(values[i])
    if rule["type"] == "boolean":
        bits = [1 if v >= 1 else 0 for v in inputs]
        op = rule.get("op")
        if op == "and":
            return 1 if all(b == 1 for b in bits) else 0
        if op == "or":
            return 1 if any(b == 1 for b in bits) else 0
        if op == "xor":
            return sum(bits) % 2
        if op == "not":
            return 0 if bits and bits[0] == 1 else 1
        return 0
    weights = rule.get("weights", [])
    if len(weights) != len(inputs):
        raise GenericEvaluationError("missing_weight", f'rule "{rule["target"]}" thiếu weight')
    result = sum(v * w for v, w in zip(inputs, weights))
    if not math.isfinite(result):
        raise GenericEvaluationError("non_finite_numeric_value", f'rule "{rule["target"]}" ra {result}')
    return result


def values_of(spec: dict, base: dict[str, float]) -> dict[str, float]:
    """M13 ba trạng thái: KHÔNG seed target = 0 nữa — target chưa resolve là
    UNRESOLVED (vắng mặt trong values), rule chỉ chạy khi MỌI input resolved.
    DAG hợp lệ hội tụ trong ≤ len(rules) lượt; còn sót sau bound → typed error."""
    values = dict(base)
    rules = list(spec.get("rules", []))
    pending = list(rules)
    for _ in range(len(rules) + 1):
        still = []
        for rule in pending:
            if all(i in values for i in rule.get("inputs", [])):
                values[rule["target"]] = _eval_rule(rule, values)
            else:
                still.append(rule)
        progressed = len(still) < len(pending)
        pending = still          # PHẢI cập nhật TRƯỚC break/progress check
        if not pending:
            break
        if not progressed:
            missing = sorted({i for r in pending for i in r.get("inputs", []) if i not in values})
            raise GenericEvaluationError(
                "unresolved_dependency_after_bound",
                f'không resolve được: {", ".join(missing)}',
            )
    if pending:
        raise GenericEvaluationError("unresolved_dependency_after_bound", "vượt bound evaluation")
    return values


def _managed_by_reveal(spec: dict) -> set[str]:
    managed: set[str] = set()
    for proc in spec.get("processes", []):
        if proc.get("type") == "reveal_sequence":
            for step in proc.get("steps", []):
                managed.update(step.get("objects", []))
    return managed


def build_timeline(spec: dict) -> list[dict]:
    """Timeline từ processes (M7.7, song song bản TS).

    Không process → một khung TĨNH, mọi object visible.
    Có reveal_sequence → visibility tích lũy tất định theo thứ tự khai báo.
    visibleIds sắp theo thứ tự khai báo object (serializable, tất định).
    """
    all_ids = [o["id"] for o in spec.get("objects", [])]

    def order_visible(vis: set[str]) -> list[str]:
        return [i for i in all_ids if i in vis]

    procs = spec.get("processes", [])
    if not procs:
        return [{"visibleIds": list(all_ids), "entityPos": {}, "narration": spec.get("title", "")}]

    managed = _managed_by_reveal(spec)
    visible = set(all_ids) if not managed else {i for i in all_ids if i not in managed}
    entity_pos: dict[str, str] = {}
    frames: list[dict] = []

    for proc in procs:
        if proc.get("type") == "reveal_sequence":
            for step in proc.get("steps", []):
                visible.update(step.get("objects", []))
                frames.append({
                    "visibleIds": order_visible(visible),
                    "entityPos": dict(entity_pos),
                    "narration": step.get("narration", f"reveal:{','.join(step.get('objects', []))}"),
                })
        else:
            visible.add(proc["entity"])
            path = proc["path"]
            entity_pos[proc["entity"]] = path[0]
            frames.append({"visibleIds": order_visible(visible), "entityPos": dict(entity_pos), "narration": f"start:{path[0]}"})
            for k in range(1, len(path)):
                entity_pos[proc["entity"]] = path[k]
                frames.append({"visibleIds": order_visible(visible), "entityPos": dict(entity_pos), "narration": f"hop:{path[k]}"})
    return frames


def apply_toggle(spec: dict, base: dict[str, float], target: str) -> dict[str, float]:
    """Lật một base value (pure) — dùng để dò bảng chân trị trong semantic check."""
    if target not in base:
        return base
    new_base = dict(base)
    new_base[target] = 0 if new_base[target] >= 1 else 1
    return new_base
