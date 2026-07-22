# -*- coding: utf-8 -*-
"""M17-RC1 §E — HAI CHẾ ĐỘ chạy lại wave, KHÔNG được trộn.

Sai lầm ở §R1 bản đầu: gộp hai thứ khác bản chất vào một test "byte-identical"
rồi dán `xfail` lên nó. Hệ quả là "cổng hiện tại từ chối fixture cũ" bị ghi
nhận như lỗi *tái lập lịch sử*, trong khi đó là **thay đổi chính sách có chủ
đích**. Hai chế độ:

1. ``historical_reproduction`` — dựng lại BẰNG CHỨNG ĐÃ CÔNG BỐ.
   Đầu vào: worktree lịch sử + generator lịch sử + catalog lịch sử + fixture
   lịch sử. Kỳ vọng: **byte-identical**. Chỉ được xfail khi có lý do THẬT thuộc
   nhóm: nondeterminism của dependency, thiếu input bất biến, thiếu generator
   lịch sử, hoặc không lấy lại được output của model.

2. ``current_policy_replay`` — chạy ĐẦU VÀO lịch sử qua pipeline/cổng HIỆN TẠI.
   Kỳ vọng: **kết quả ĐƯỢC PHÉP đổi**. Sản phẩm là *migration report*, không
   phải byte-identical. Một case đổi kết quả vì cổng mới là DỮ LIỆU, không
   phải lỗi.

Module này lo chế độ 2 (chạy được trong pytest, không cần git/worktree). Chế độ
1 do `scripts/historical_reproduction.py` lo vì nó cần worktree.
"""

from __future__ import annotations

from app.evaluation.authenticity_artifacts import run_offline_audit
from app.evaluation.wave_snapshots import WaveSnapshot

# Vì sao một case đổi kết quả — vốn từ ĐÓNG.
CHANGE_KINDS = (
    "unchanged",
    "blocked_by_new_gate",       # cổng ra đời SAU wave chặn đầu vào cũ
    "route_now_supported",       # năng lực mới: đề từng gap nay chạy được
    "route_changed",             # đổi target (không phải do cổng)
    "status_changed_other",      # đổi status không thuộc các nhóm trên
)

# Cổng ra đời SAU từng wave — dùng để phân loại nguyên nhân, không để bào chữa.
_GATES_AFTER_WAVE = {
    "structure": "M17 W2A",
    "input_sufficiency": "M17-RC1 §C2",
    "completeness_requested": "M17-RC1 §D/§C1",
    "completeness_represented": "M17-RC1 §D/§C1",
}


def _fired_new_gates(record, snapshot: WaveSnapshot) -> list[str]:
    """Cổng ĐÃ BẮN mà wave đó chưa có. `record.gates` đã bị lọc theo snapshot
    khi ghi artifact, nên ở đây đọc `raw_gates` chưa lọc."""
    return sorted(
        g["gate"] for g in getattr(record, "raw_gates", []) or []
        if g.get("fired") and g.get("gate") not in snapshot.gate_names
    )


def classify_change(old: dict, record, snapshot: WaveSnapshot) -> tuple[str, list[str]]:
    """Vì sao kết quả case này đổi (hoặc không)? Trả (kind, cổng mới đã bắn)."""
    new_gates = _fired_new_gates(record, snapshot)
    if old["actual_status"] == record.actual_status and old["final_route"] == record.final_route:
        return "unchanged", new_gates
    if new_gates:
        return "blocked_by_new_gate", new_gates
    if old["actual_status"] == "unsupported" and record.actual_status == "ok":
        return "route_now_supported", new_gates
    if old["final_route"] != record.final_route and record.actual_status == "ok":
        return "route_changed", new_gates
    return "status_changed_other", new_gates


def build_migration_report(snapshot: WaveSnapshot, published: dict) -> dict:
    """Chạy ĐẦU VÀO lịch sử qua pipeline HIỆN TẠI rồi ghi cái gì đã đổi.

    ``published``: nội dung `authenticity_results.json` đã commit của wave.
    KHÔNG sửa artifact đã công bố — chỉ đọc để so."""
    records = run_offline_audit(snapshot)
    old_by_id = {r["case_id"]: r for r in published["data"]["case_records"]}

    entries, counts = [], {k: 0 for k in CHANGE_KINDS}
    for rec in records:
        old = old_by_id[rec.case_id]
        kind, new_gates = classify_change(old, rec, snapshot)
        counts[kind] += 1
        if kind == "unchanged":
            continue
        entries.append({
            "case_id": rec.case_id,
            "old_expected_outcome": {
                "status": old["actual_status"], "route": old["final_route"],
                "error_code": old["envelope_error_code"],
                "failure_category": old["failure_category"],
            },
            "current_outcome": {
                "status": rec.actual_status, "route": rec.final_route,
                "error_code": rec.envelope_error_code,
                "failure_category": rec.failure_category,
            },
            "changed_gate_or_policy": [
                {"gate": g, "introduced_by": _GATES_AFTER_WAVE.get(g, "?")}
                for g in new_gates
            ],
            "change_kind": kind,
            # Đổi vì CHÍNH SÁCH MỚI ⇒ có chủ đích. Đổi mà không cổng mới nào bắn
            # ⇒ CHƯA GIẢI THÍCH ĐƯỢC, phải điều tra.
            "intentional": kind in ("blocked_by_new_gate", "route_now_supported"),
            "historical_fixture_violates_current_contract": kind == "blocked_by_new_gate",
        })

    unexplained = [e["case_id"] for e in entries if not e["intentional"]]
    return {
        "schema_version": "1",
        "mode": "current_policy_replay",
        "wave_id": snapshot.wave_id,
        "input_snapshot_id": snapshot.input_snapshot_id,
        "note": (
            "Đầu vào lịch sử BẤT BIẾN chạy qua pipeline/cổng HIỆN TẠI. Kết quả "
            "ĐƯỢC PHÉP đổi — đây là báo cáo di trú, KHÔNG phải kiểm byte-identical. "
            "Không sửa artifact đã công bố."
        ),
        "case_count": len(records),
        "change_counts": counts,
        "changed_cases": entries,
        "unexplained_changes": unexplained,
    }


__all__ = ["CHANGE_KINDS", "build_migration_report", "classify_change"]
