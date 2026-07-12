"""Kiểm tra NGỮ NGHĨA spec generic (M7 §6, §8).

Validation cấu trúc (dsl.py) chỉ đảm bảo spec đúng cú pháp. Semantic check
THỰC THI spec bằng generic_engine rồi so hành vi với kỳ vọng của bài — để
một spec "đúng cú pháp nhưng sai hành vi" KHÔNG bị tính là thành công.

Kỳ vọng đọc từ CHÍNH cấu trúc spec (bất kể LLM đặt id gì) nên id-agnostic.
"""

from __future__ import annotations

from itertools import product

from app.simulation.dsl.manifest import all_coverable_roles, roles_of_primitive
from app.simulation.generic_engine import build_timeline, initial_base, values_of


# ── Semantic compatibility (M7.11) — kiểm TRƯỚC render ─────────

def roles_covered_by_spec(spec: dict) -> set[str]:
    """Hợp vai trò ngữ nghĩa của các primitive THỰC SỰ có trong spec."""
    covered: set[str] = set()
    for o in spec.get("objects", []):
        covered |= roles_of_primitive(o.get("type", ""))
    for r in spec.get("rules", []):
        covered |= roles_of_primitive(r.get("type", ""))
    for p in spec.get("processes", []):
        covered |= roles_of_primitive(p.get("type", ""))
    return covered


def check_semantic_compatibility(required: set[str], spec: dict) -> dict:
    """So vai trò đề CẦN với vai trò spec CUNG CẤP.

    - Vai trò không primitive nào cover được → capability_gap (không ép sai).
    - Spec KHÔNG chia sẻ vai trò cốt lõi nào với đề (biểu diễn SAI HỌ, vd đề cần
      quan hệ nút-cạnh nhưng spec ra công tắc/đèn) → mismatch (retry).
    - Còn lại → ok.

    LƯU Ý (chống dương tính giả): analyze có thể gắn thêm vai trò PHỤ (vd toạ độ
    → 'numeric') mà bản chất bài không cần primitive số. Nên KHÔNG đòi spec phủ
    TỪNG vai trò; chỉ từ chối khi spec và đề LỆCH HẲN HỌ (giao rỗng).
    """
    coverable = all_coverable_roles()
    gap = sorted(required - coverable)
    if gap:
        return {"ok": False, "kind": "capability_gap", "missing": gap}
    core = required & coverable  # == required khi không có gap
    if core and not (core & roles_covered_by_spec(spec)):
        return {"ok": False, "kind": "mismatch", "missing": sorted(core)}
    return {"ok": True, "kind": "ok", "missing": []}


_BOOL = {
    "and": lambda bits: 1 if all(bits) else 0,
    "or": lambda bits: 1 if any(bits) else 0,
    "xor": lambda bits: sum(bits) % 2,
    "not": lambda bits: 0 if bits and bits[0] else 1,
}


def check_semantic(spec: dict, expectation: dict) -> tuple[bool, str]:
    """Trả (ok, chi tiết). expectation = {"kind": ...}."""
    kind = expectation.get("kind", "none")
    if kind == "none":
        return _structural_ok(spec)
    if kind == "boolean_gate":
        return _check_boolean_gate(spec, expectation["op"])
    if kind == "weighted_sum":
        return _check_weighted_sum(spec, expectation["value"])
    if kind == "moving_path":
        return _check_moving_path(spec, expectation.get("min_len", 2))
    if kind == "progressive_reveal":
        return _check_progressive_reveal(spec, expectation.get("min_steps", 2))
    return False, f"Loại kỳ vọng lạ: {kind}"


def _check_progressive_reveal(spec: dict, min_steps: int) -> tuple[bool, str]:
    """M7.7 §6: cảnh phải HÌNH THÀNH TỪNG BƯỚC — có reveal_sequence, visibleIds
    TÍCH LŨY (frame sau ⊇ frame trước) và KHÔNG hiện hết ngay frame đầu."""
    has_reveal = any(p.get("type") == "reveal_sequence" for p in spec.get("processes", []))
    if not has_reveal:
        return False, "Không có reveal_sequence — cảnh hiện toàn bộ ngay, không hình thành từng bước"
    frames = build_timeline(spec)
    if len(frames) < min_steps:
        return False, f"Chỉ có {len(frames)} khung, cần ≥ {min_steps} bước hình thành"
    all_ids = {o["id"] for o in spec.get("objects", [])}
    # frame đầu KHÔNG được hiện toàn bộ object (nếu không thì đâu phải progressive)
    if set(frames[0]["visibleIds"]) >= all_ids:
        return False, "Khung đầu đã hiện toàn bộ object — không phải hình thành từng bước"
    # tích lũy: mỗi khung ⊇ khung trước
    for i in range(1, len(frames)):
        if not set(frames[i]["visibleIds"]) >= set(frames[i - 1]["visibleIds"]):
            return False, f"visibleIds không tích lũy tại khung {i}"
    return True, f"Cảnh hình thành qua {len(frames)} bước, visibility tích lũy đúng"


def _structural_ok(spec: dict) -> tuple[bool, str]:
    """Bất biến ngữ nghĩa tối thiểu cho mọi spec: boolean target ra 0/1,
    path tham chiếu node hợp lệ."""
    node_ids = {o["id"] for o in spec.get("objects", []) if o.get("type") == "node"}
    for p in spec.get("processes", []):
        for nid in p.get("path", []):
            if nid not in node_ids:
                return False, f'path tham chiếu "{nid}" không phải node'
    values = values_of(spec, initial_base(spec))
    for r in spec.get("rules", []):
        if r["type"] == "boolean" and values.get(r["target"]) not in (0, 1):
            return False, f'boolean target "{r["target"]}" ra giá trị không phải 0/1'
    return True, "ok"


def _check_boolean_gate(spec: dict, op: str) -> tuple[bool, str]:
    """Tìm rule boolean đúng op và dò TOÀN BỘ bảng chân trị của nó."""
    rule = next((r for r in spec.get("rules", []) if r["type"] == "boolean" and r.get("op") == op), None)
    if rule is None:
        return False, f"Không có rule boolean op={op} (có thể LLM chọn sai phép logic)"
    inputs = rule.get("inputs", [])
    if not inputs:
        return False, "rule boolean không có inputs"
    base0 = initial_base(spec)
    for combo in product([0, 1], repeat=len(inputs)):
        base = dict(base0)
        for i, iid in enumerate(inputs):
            base[iid] = combo[i]
        got = values_of(spec, base).get(rule["target"])
        want = _BOOL[op](list(combo))
        if got != want:
            return False, f"Bảng chân trị sai tại {combo}: engine={got}, đúng={want}"
    return True, f"Bảng chân trị {op} đúng toàn bộ"


def _check_weighted_sum(spec: dict, expected: float) -> tuple[bool, str]:
    rule = next((r for r in spec.get("rules", []) if r["type"] == "weighted_sum"), None)
    if rule is None:
        return False, "Không có rule weighted_sum"
    got = values_of(spec, initial_base(spec)).get(rule["target"])
    if got != expected:
        return False, f"Tổng trọng số ban đầu = {got}, kỳ vọng {expected}"
    return True, f"Tổng trọng số = {expected} đúng"


def _check_moving_path(spec: dict, min_len: int) -> tuple[bool, str]:
    procs = spec.get("processes", [])
    proc = next((p for p in procs if p["type"] == "move_along_path"), None)
    if proc is None:
        return False, "Không có process move_along_path"
    if len(proc.get("path", [])) < min_len:
        return False, f"path ngắn hơn {min_len} nút"
    ok, detail = _structural_ok(spec)
    return (ok, "Đường đi hợp lệ" if ok else detail)
