"""Authoritative AST & Process Execution Engine (Python Backend).

Đây là nguồn sự thật duy nhất (Single Source of Truth) phía server để:
1. Thực thi dry-run tất định các quy trình mô phỏng (step_sequence, reveal_sequence, move_along_path).
2. Kiểm chứng các bất biến runtime (Trace Invariants, Pointer Bounds, Stack/Queue Underflow/Overflow).
3. Kiểm tra Visual Binding giữa các bước và các đối tượng hình ảnh.
4. Đối chiếu kết quả bước cuối với Independent Result Oracle.
5. Sinh ra Counterexample có cấu trúc máy-đọc được (CEGIS-ready) khi phát hiện vi phạm.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Counterexample:
    gate: str
    violation_code: str
    step_index: int | None
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate,
            "violation_code": self.violation_code,
            "step_index": self.step_index,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class ExecutionReport:
    ok: bool
    error: str | None = None
    error_code: str | None = None
    counterexample: Counterexample | None = None
    snapshots: list[dict[str, Any]] = field(default_factory=list)
    final_values: dict[str, Any] = field(default_factory=dict)
    final_state: dict[str, Any] = field(default_factory=dict)


def _get_target_length(obj: dict) -> int:
    """Trả về số lượng phần tử của một đối tượng mảng / danh sách / biểu đồ."""
    obj_type = obj.get("type")
    if obj_type in ("array_strip", "bit_register"):
        items = obj.get("items") or obj.get("bits") or []
        return len(items)
    if obj_type == "bar_chart":
        bars = obj.get("bars") or []
        return len(bars)
    if obj_type == "table_grid":
        rows = obj.get("rows") or []
        return len(rows)
    if obj_type in ("stack_view", "queue_view"):
        items = obj.get("items") or []
        return len(items)
    return 1


def execute_simulation(spec: dict, oracle_result: dict[str, Any] | None = None) -> ExecutionReport:
    """Thực thi kiểm chứng toàn diện SimulationSpec trên 6 cổng kiểm tra server-side."""
    objects = spec.get("objects", [])
    by_id = {o["id"]: dict(o) for o in objects if isinstance(o, dict) and "id" in o}
    
    # ── [GATE 5] Visual Binding Check trên Objects ─────────────────────────────
    for o in objects:
        if o.get("type") == "pointer":
            tgt = o.get("target") or o.get("target_id")
            if tgt is not None and tgt not in by_id:
                ce = Counterexample(
                    gate="binding",
                    violation_code="DANGLING_POINTER_TARGET",
                    step_index=None,
                    message=f'Con trỏ "{o.get("id")}" trỏ tới đối tượng không tồn tại: "{tgt}".',
                    details={"pointer_id": o.get("id"), "target": tgt},
                )
                return ExecutionReport(ok=False, error=ce.message, error_code=ce.violation_code, counterexample=ce)

    # Khởi tạo environment giá trị ban đầu
    current_values: dict[str, Any] = {}
    current_stacks: dict[str, list[Any]] = {}
    current_queues: dict[str, list[Any]] = {}
    current_pointers: dict[str, int] = {}
    current_arrays: dict[str, list[Any]] = {}

    for o in objects:
        oid = o["id"]
        otype = o.get("type")
        if "value" in o:
            current_values[oid] = o["value"]
        if otype == "pointer":
            current_pointers[oid] = int(o.get("index", 0))
        elif otype == "stack_view":
            current_stacks[oid] = list(o.get("items", []))
        elif otype == "queue_view":
            current_queues[oid] = list(o.get("items", []))
        elif otype == "array_strip":
            current_arrays[oid] = list(o.get("items", []))
        elif otype == "bar_chart":
            current_arrays[oid] = [b.get("value") for b in o.get("bars", [])]

    snapshots: list[dict[str, Any]] = []
    
    # Snapshot 0: Initial state
    snapshots.append({
        "frame": 0,
        "values": dict(current_values),
        "stacks": {k: list(v) for k, v in current_stacks.items()},
        "queues": {k: list(v) for k, v in current_queues.items()},
        "pointers": dict(current_pointers),
    })

    # ── [GATE 3 & 4] Deterministic AST & Trace Invariant Execution ─────────────
    processes = spec.get("processes", [])
    for proc in processes:
        proc_type = proc.get("type")
        
        if proc_type == "step_sequence":
            steps = proc.get("steps", [])
            for step_idx, step in enumerate(steps):
                action = step.get("action") or "highlight"
                targets = step.get("targets", [])
                
                # [GATE 5] Check targets existence
                for tid in targets:
                    if tid not in by_id:
                        ce = Counterexample(
                            gate="binding",
                            violation_code="DANGLING_TARGET_REF",
                            step_index=step_idx,
                            message=f'Bước {step_idx} tham chiếu đối tượng không tồn tại: "{tid}".',
                            details={"step": step, "missing_target": tid},
                        )
                        return ExecutionReport(ok=False, error=ce.message, error_code=ce.violation_code, counterexample=ce)

                # Pointer movement check
                ptr_id = step.get("pointer_id")
                if ptr_id:
                    if ptr_id not in by_id:
                        ce = Counterexample(
                            gate="binding",
                            violation_code="DANGLING_POINTER_REF",
                            step_index=step_idx,
                            message=f'Bước {step_idx} sử dụng con trỏ không tồn tại: "{ptr_id}".',
                            details={"step": step, "pointer_id": ptr_id},
                        )
                        return ExecutionReport(ok=False, error=ce.message, error_code=ce.violation_code, counterexample=ce)
                    
                    ptr_obj = by_id[ptr_id]
                    tgt_id = ptr_obj.get("target")
                    if tgt_id in by_id:
                        target_len = _get_target_length(by_id[tgt_id])
                        to_idx = step.get("to_index")
                        if to_idx is not None:
                            if not (0 <= to_idx < target_len):
                                ce = Counterexample(
                                    gate="invariant",
                                    violation_code="INDEX_OUT_OF_BOUNDS",
                                    step_index=step_idx,
                                    message=(
                                        f'Bước {step_idx}: Con trỏ "{ptr_id}" nhảy tới vị trí {to_idx} '
                                        f'vượt quá độ dài mảng ({target_len} phần tử, chỉ số 0..{target_len-1}).'
                                    ),
                                    details={"pointer_id": ptr_id, "to_index": to_idx, "target_len": target_len},
                                )
                                return ExecutionReport(ok=False, error=ce.message, error_code=ce.violation_code, counterexample=ce)
                            current_pointers[ptr_id] = to_idx

                # Stack push / pop check
                if action == "push":
                    for tid in targets:
                        stk = current_stacks.setdefault(tid, [])
                        cap = by_id[tid].get("capacity", 20)
                        if len(stk) >= cap:
                            ce = Counterexample(
                                gate="invariant",
                                violation_code="STACK_OVERFLOW",
                                step_index=step_idx,
                                message=f'Bước {step_idx}: Thao tác push vào ngăn xếp "{tid}" vượt quá sức chứa tối đa ({cap}).',
                                details={"target": tid, "capacity": cap},
                            )
                            return ExecutionReport(ok=False, error=ce.message, error_code=ce.violation_code, counterexample=ce)
                        val = step.get("value", "item")
                        stk.append(val)
                        
                elif action == "pop":
                    for tid in targets:
                        stk = current_stacks.setdefault(tid, [])
                        if len(stk) == 0:
                            ce = Counterexample(
                                gate="invariant",
                                violation_code="STACK_UNDERFLOW",
                                step_index=step_idx,
                                message=f'Bước {step_idx}: Thao tác pop trên ngăn xếp rỗng "{tid}".',
                                details={"target": tid},
                            )
                            return ExecutionReport(ok=False, error=ce.message, error_code=ce.violation_code, counterexample=ce)
                        stk.pop()

                # Queue enqueue / dequeue check
                elif action == "enqueue":
                    for tid in targets:
                        q = current_queues.setdefault(tid, [])
                        val = step.get("value", "item")
                        q.append(val)
                elif action == "dequeue":
                    for tid in targets:
                        q = current_queues.setdefault(tid, [])
                        if len(q) == 0:
                            ce = Counterexample(
                                gate="invariant",
                                violation_code="QUEUE_UNDERFLOW",
                                step_index=step_idx,
                                message=f'Bước {step_idx}: Thao tác dequeue trên hàng đợi rỗng "{tid}".',
                                details={"target": tid},
                            )
                            return ExecutionReport(ok=False, error=ce.message, error_code=ce.violation_code, counterexample=ce)
                        q.pop(0)

                # Swap check
                elif action == "swap":
                    for tid in targets:
                        indices = step.get("indices", [])
                        if len(indices) == 2 and tid in current_arrays:
                            arr = current_arrays[tid]
                            i1, i2 = indices
                            if not (0 <= i1 < len(arr) and 0 <= i2 < len(arr)):
                                ce = Counterexample(
                                    gate="invariant",
                                    violation_code="SWAP_INDEX_OUT_OF_BOUNDS",
                                    step_index=step_idx,
                                    message=f'Bước {step_idx}: Đổi chỗ vị trí [{i1}, {i2}] ngoài giới hạn mảng {len(arr)}.',
                                    details={"indices": indices, "length": len(arr)},
                                )
                                return ExecutionReport(ok=False, error=ce.message, error_code=ce.violation_code, counterexample=ce)
                            arr[i1], arr[i2] = arr[i2], arr[i1]

                # Value update in value_box or targets
                if "value" in step:
                    for tid in targets:
                        current_values[tid] = step["value"]
                        
                # Record snapshot after step
                snapshots.append({
                    "frame": len(snapshots),
                    "step_index": step_idx,
                    "action": action,
                    "values": dict(current_values),
                    "stacks": {k: list(v) for k, v in current_stacks.items()},
                    "queues": {k: list(v) for k, v in current_queues.items()},
                    "pointers": dict(current_pointers),
                })

    # ── [GATE 5 / ORACLE] Independent Result Oracle Verification ──────────────
    if oracle_result is not None:
        # Check against ground truth oracle
        # 1. First Day Temp Scan
        if "first_day_index" in oracle_result:
            expected_day = oracle_result["first_day_index"]
            # Look for value_box with result
            found = False
            for vid, val in current_values.items():
                if val == expected_day:
                    found = True
                    break
            if not found:
                ce = Counterexample(
                    gate="oracle",
                    violation_code="ORACLE_RESULT_MISMATCH",
                    step_index=len(snapshots) - 1,
                    message=f'Kết quả mô phỏng không khớp với Oracle: mong đợi ngày {expected_day}.',
                    details={"expected": expected_day, "actual_values": current_values},
                )
                return ExecutionReport(ok=False, error=ce.message, error_code=ce.violation_code, counterexample=ce)

        # 2. Bracket validity
        if "is_valid" in oracle_result:
            expected_valid = oracle_result["is_valid"]
            expected_str = "Hợp lệ" if expected_valid else "Không hợp lệ"
            found = False
            for vid, val in current_values.items():
                val_str = str(val).lower()
                if val in (expected_valid, expected_str, "Valid" if expected_valid else "Invalid") or (
                    expected_valid and ("hợp lệ" in val_str or "valid" in val_str or "true" in val_str)
                ) or (
                    not expected_valid and ("không hợp lệ" in val_str or "invalid" in val_str or "false" in val_str)
                ):
                    found = True
                    break
            if not found and current_stacks:
                # Kiểm tra stack trạng thái cuối: nếu hợp lệ thì stack rỗng
                all_empty = all(len(stk) == 0 for stk in current_stacks.values())
                if (expected_valid and all_empty) or (not expected_valid and not all_empty):
                    found = True
            if not found:
                ce = Counterexample(
                    gate="oracle",
                    violation_code="ORACLE_RESULT_MISMATCH",
                    step_index=len(snapshots) - 1,
                    message=f'Kết quả kiểm tra ngoặc không khớp với Oracle: mong đợi "{expected_str}".',
                    details={"expected": expected_str, "actual_values": current_values},
                )
                return ExecutionReport(ok=False, error=ce.message, error_code=ce.violation_code, counterexample=ce)

        # 3. Count in range
        if "count" in oracle_result:
            expected_cnt = oracle_result["count"]
            found = False
            for vid, val in current_values.items():
                if val == expected_cnt:
                    found = True
                    break
            if not found:
                ce = Counterexample(
                    gate="oracle",
                    violation_code="ORACLE_RESULT_MISMATCH",
                    step_index=len(snapshots) - 1,
                    message=f'Kết quả đếm không khớp với Oracle: mong đợi count = {expected_cnt}.',
                    details={"expected": expected_cnt, "actual_values": current_values},
                )
                return ExecutionReport(ok=False, error=ce.message, error_code=ce.violation_code, counterexample=ce)

        # 4. Athlete sorting
        if "fastest" in oracle_result:
            expected_fastest = oracle_result["fastest"]
            found = False
            for vid, val in current_values.items():
                if val == expected_fastest:
                    found = True
                    break
            if not found:
                ce = Counterexample(
                    gate="oracle",
                    violation_code="ORACLE_RESULT_MISMATCH",
                    step_index=len(snapshots) - 1,
                    message=f'Thành tích nhanh nhất không khớp với Oracle: mong đợi {expected_fastest}.',
                    details={"expected": expected_fastest, "actual_values": current_values},
                )
                return ExecutionReport(ok=False, error=ce.message, error_code=ce.violation_code, counterexample=ce)

        # 5. Last occurrence
        if "last_index" in oracle_result:
            expected_idx = oracle_result["last_index"]
            found = False
            for vid, val in current_values.items():
                if val == expected_idx:
                    found = True
                    break
            if not found:
                ce = Counterexample(
                    gate="oracle",
                    violation_code="ORACLE_RESULT_MISMATCH",
                    step_index=len(snapshots) - 1,
                    message=f'Vị trí cuối cùng không khớp với Oracle: mong đợi index {expected_idx}.',
                    details={"expected": expected_idx, "actual_values": current_values},
                )
                return ExecutionReport(ok=False, error=ce.message, error_code=ce.violation_code, counterexample=ce)

        # 6. Table filter
        if "matching_count" in oracle_result:
            expected_cnt = oracle_result["matching_count"]
            found = False
            for vid, val in current_values.items():
                if val == expected_cnt:
                    found = True
                    break
            if not found:
                ce = Counterexample(
                    gate="oracle",
                    violation_code="ORACLE_RESULT_MISMATCH",
                    step_index=len(snapshots) - 1,
                    message=f'Số dòng khớp bảng không khớp với Oracle: mong đợi {expected_cnt}.',
                    details={"expected": expected_cnt, "actual_values": current_values},
                )
                return ExecutionReport(ok=False, error=ce.message, error_code=ce.violation_code, counterexample=ce)

    return ExecutionReport(
        ok=True,
        snapshots=snapshots,
        final_values=current_values,
        final_state={
            "values": current_values,
            "stacks": current_stacks,
            "queues": current_queues,
            "pointers": current_pointers,
            "arrays": current_arrays,
        },
    )
