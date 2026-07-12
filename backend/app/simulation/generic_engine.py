"""Port Python của generic engine (M7) — CHỈ để kiểm tra ngữ nghĩa server-side.

Cùng luật tất định với engine TS ở frontend (valuesOf + buildTimeline).
Không phải engine chạy giao diện (đó là TS); bản này để harness đánh giá
có thể THỰC THI spec đã compose mà kiểm hành vi (§6).
"""

from __future__ import annotations


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
    inputs = [values.get(i, 0) for i in rule.get("inputs", [])]
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
    return sum(v * (weights[i] if i < len(weights) else 0) for i, v in enumerate(inputs))


def values_of(spec: dict, base: dict[str, float]) -> dict[str, float]:
    """Giá trị đầy đủ = base + dẫn xuất (áp rule đến khi ổn định)."""
    values = dict(base)
    for t in rule_targets(spec):
        values.setdefault(t, 0)
    rules = spec.get("rules", [])
    for _ in range(len(rules) + 1):
        changed = False
        for rule in rules:
            v = _eval_rule(rule, values)
            if values.get(rule["target"]) != v:
                values[rule["target"]] = v
                changed = True
        if not changed:
            break
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
