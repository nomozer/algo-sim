"""Port Python của generic engine (M7) — CHỈ để kiểm tra ngữ nghĩa server-side.

Cùng luật tất định với engine TS ở frontend (valuesOf + buildTimeline).
Không phải engine chạy giao diện (đó là TS); bản này để harness đánh giá
có thể THỰC THI spec đã compose mà kiểm hành vi (§6).
"""

from __future__ import annotations

import ast
import math
import operator as op


class GenericEvaluationError(Exception):
    """M13 §3.4 — typed failure tại ranh giới executor; KHÔNG bao giờ thành 0."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


_SAFE_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
    ast.Eq: op.eq,
    ast.NotEq: op.ne,
    ast.Lt: op.lt,
    ast.LtE: op.le,
    ast.Gt: op.gt,
    ast.GtE: op.ge,
}


def _rgb_to_hex(r: float, g: float, b: float) -> str:
    cr = max(0, min(255, int(round(r))))
    cg = max(0, min(255, int(round(g))))
    cb = max(0, min(255, int(round(b))))
    return f"#{cr:02x}{cg:02x}{cb:02x}"


_SAFE_FUNCS = {
    "rgb_to_hex": _rgb_to_hex,
    "clamp": lambda x, lo, hi: max(lo, min(hi, x)),
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "if_else": lambda cond, a, b: a if cond else b,
    # Bitwise
    "bit_and": lambda a, b: int(a) & int(b),
    "bit_or": lambda a, b: int(a) | int(b),
    "bit_xor": lambda a, b: int(a) ^ int(b),
    "bit_not": lambda a, bits=8: (~int(a)) & ((1 << int(bits)) - 1),
    "shift_left": lambda a, n: int(a) << int(n),
    "shift_right": lambda a, n: int(a) >> int(n),
    # Base conversions
    "bin": lambda x, bits=8: format(int(x) & ((1 << int(bits)) - 1), f"0{int(bits)}b"),
    "hex": lambda x: f"0x{int(x):x}",
    "dec": lambda s: int(str(s), 2) if isinstance(s, str) else int(s),
    # Array helpers
    "sum": lambda arr: sum(arr) if isinstance(arr, (list, tuple)) else arr,
    "len": lambda arr: len(arr) if isinstance(arr, (list, tuple, str)) else 0,
    "get": lambda arr, idx: arr[int(idx)] if isinstance(arr, (list, tuple)) and 0 <= int(idx) < len(arr) else 0,
}


def _eval_expr(node: ast.AST, env: dict[str, any]) -> any:
    if isinstance(node, ast.Expression):
        return _eval_expr(node.body, env)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise GenericEvaluationError("invalid_numeric_source", f'identifier lạ "{node.id}"')
    if isinstance(node, ast.UnaryOp):
        operand = _eval_expr(node.operand, env)
        op_func = _SAFE_OPS.get(type(node.op))
        if op_func:
            return op_func(operand)
        raise GenericEvaluationError("invalid_numeric_source", f"unary op không hỗ trợ {node.op}")
    if isinstance(node, ast.BinOp):
        left = _eval_expr(node.left, env)
        right = _eval_expr(node.right, env)
        op_func = _SAFE_OPS.get(type(node.op))
        if op_func:
            return op_func(left, right)
        raise GenericEvaluationError("invalid_numeric_source", f"binary op không hỗ trợ {node.op}")
    if isinstance(node, ast.Compare):
        left = _eval_expr(node.left, env)
        for cmp_op, comparator in zip(node.ops, node.comparators):
            right = _eval_expr(comparator, env)
            op_func = _SAFE_OPS.get(type(cmp_op))
            if not op_func or not op_func(left, right):
                return 0
            left = right
        return 1
    if isinstance(node, ast.IfExp):
        test = _eval_expr(node.test, env)
        return _eval_expr(node.body if test else node.orelse, env)
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in _SAFE_FUNCS:
            args = [_eval_expr(a, env) for a in node.args]
            return _SAFE_FUNCS[node.func.id](*args)
        func_name = node.func.id if isinstance(node.func, ast.Name) else "unknown"
        raise GenericEvaluationError("invalid_numeric_source", f'hàm không hỗ trợ "{func_name}"')
    raise GenericEvaluationError("invalid_numeric_source", f"cú pháp biểu thức không hỗ trợ {type(node)}")


def rule_targets(spec: dict) -> set[str]:
    return {r["target"] for r in spec.get("rules", [])}


def initial_base(spec: dict) -> dict[str, any]:
    targets = rule_targets(spec)
    base: dict[str, any] = {}
    for o in spec.get("objects", []):
        if o["id"] in targets:
            continue
        if "value" in o:
            base[o["id"]] = o["value"]
        elif o.get("type") == "slider":
            base[o["id"]] = o.get("min", 0)
        elif o.get("type") == "bit_register" and "bits" in o:
            bits = o["bits"]
            base[o["id"]] = sum(int(b) * (2 ** (len(bits) - 1 - i)) for i, b in enumerate(bits))
    return base


def _eval_rule(rule: dict, values: dict[str, any]) -> any:
    inputs = []
    for i in rule.get("inputs", []):
        if i not in values:
            raise GenericEvaluationError("invalid_numeric_source", f'input "{i}" chưa có giá trị')
        inputs.append(values[i])
    if rule["type"] == "boolean":
        bits = [1 if (isinstance(v, (int, float)) and v >= 1) else 0 for v in inputs]
        op_name = rule.get("op")
        if op_name == "and":
            return 1 if all(b == 1 for b in bits) else 0
        if op_name == "or":
            return 1 if any(b == 1 for b in bits) else 0
        if op_name == "xor":
            return sum(bits) % 2
        if op_name == "not":
            return 0 if bits and bits[0] == 1 else 1
        return 0
    if rule["type"] == "formula":
        expression = rule.get("expression", "")
        try:
            parsed = ast.parse(expression, mode="eval")
        except Exception as e:
            raise GenericEvaluationError("invalid_numeric_source", f"lỗi cú pháp biểu thức: {e}")
        env = dict(values)
        return _eval_expr(parsed, env)
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
                    "narration": step.get("narration") or spec.get("title", ""),
                })
        elif proc.get("type") == "step_sequence":
            for step in proc.get("steps", []):
                frames.append({
                    "visibleIds": list(all_ids),
                    "entityPos": dict(entity_pos),
                    "narration": step.get("narration") or spec.get("title", ""),
                    "stepAction": dict(step),
                })
        elif proc.get("type") == "move_along_path":
            entity = proc.get("entity")
            path = proc.get("path", [])
            for node_id in path:
                entity_pos[entity] = node_id
                frames.append({
                    "visibleIds": order_visible(visible),
                    "entityPos": dict(entity_pos),
                    "narration": f'{entity} đi tới {node_id}',
                })
    return frames or [{"visibleIds": list(all_ids), "entityPos": {}, "narration": spec.get("title", "")}]


def apply_toggle(spec: dict, base: dict[str, float], target: str) -> dict[str, float]:
    """Lật một base value (pure) — dùng để dò bảng chân trị trong semantic check."""
    if target not in base:
        return base
    new_base = dict(base)
    new_base[target] = 0 if new_base[target] >= 1 else 1
    return new_base
