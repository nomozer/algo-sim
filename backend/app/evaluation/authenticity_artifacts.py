# -*- coding: utf-8 -*-
"""M17-Lite W0 — builder THUẦN cho 6 artifact audit (docs/evaluation/m17/wave0/).

Theo tiền lệ m16_artifacts.py: mọi hàm trả dict/str JSON-serializable thuần,
KHÔNG side-effect file — `scripts/generate_m17_wave0_artifacts.py` (CLI) mới
ghi file + bơm 2 field volatile (git_commit, generated_at);
`tests/test_m17_wave0_artifacts.py` gọi lại CHÍNH các hàm này để sync-lock.

`run_offline_audit()` chạy TOÀN BỘ audit matrix qua production run_pipeline
(bất biến #22) với provider scripted per-case — monkeypatch thủ công
`pipeline.call_gemini` (gán + khôi phục trong finally), chạy được cả trong
pytest lẫn CLI.
"""

from __future__ import annotations

from app.ai import pipeline
from app.evaluation.authenticity_audit import (
    AuditRecord,
    audit_metrics,
    build_leak_ledger,
    classify_targets,
    records_as_dicts,
    run_audit,
)
from app.evaluation.authenticity_matrix import build_audit_cases
from app.simulation.catalog import CATALOG
from app.simulation.coverage import coverage_rows


def run_offline_audit() -> list[AuditRecord]:
    """Chạy matrix offline — an toàn trong pytest (guard mạng conftest vẫn
    bảo vệ: provider scripted chặn TRƯỚC network) lẫn ngoài pytest (CLI)."""
    original = pipeline.call_gemini
    try:
        return run_audit(lambda fake: setattr(pipeline, "call_gemini", fake))
    finally:
        pipeline.call_gemini = original


# ── 1. authenticity_results.json ──────────────────────────────
def build_authenticity_results(records: list[AuditRecord]) -> dict:
    cases = build_audit_cases()
    notes = {c.case_id: c.note for c in cases if c.note}
    prompts = {c.case_id: c.prompt_vi for c in cases}
    rows = []
    for d in records_as_dicts(records):
        d["prompt_vi"] = prompts.get(d["case_id"], "")
        if d["case_id"] in notes:
            d["note"] = notes[d["case_id"]]
        rows.append(d)
    return {
        "case_records": rows,
        "target_classifications": classify_targets(records),
    }


# ── 2. authenticity_metrics.json ──────────────────────────────
def build_authenticity_metrics(records: list[AuditRecord]) -> dict:
    return audit_metrics(records, classify_targets(records))


# ── 3. generic_leak_ledger.json ───────────────────────────────
def build_generic_leak_ledger_artifact(records: list[AuditRecord]) -> dict:
    cases = {c.case_id: c for c in build_audit_cases()}
    entries = []
    for e in build_leak_ledger(records):
        c = cases.get(e["case_id"])
        entries.append({**e, "prompt_vi": c.prompt_vi if c else "", "note": c.note if c else ""})
    return {"entries": entries}


# ── 4. curriculum_coverage.json ───────────────────────────────
def build_curriculum_coverage(records: list[AuditRecord]) -> dict:
    """Nền coverage TỰ ĐỘNG (W0): knowledge units (coverage.py) + phân loại
    authenticity per-target + verdict per intentional-gap + quan sát leak.
    Dashboard đầy đủ (join unit↔target theo knowledge_unit_id) là việc W3."""
    cls = classify_targets(records)
    evidence: dict[str, list[str]] = {}
    for r in records:
        if r.sim_id is not None:
            evidence.setdefault(r.sim_id, []).append(r.case_id)
    targets = {
        sid: {
            "classification": cls[sid],
            "families": sorted({m.family_id.value for m in CATALOG[sid].family_memberships}),
            "curriculum_anchor": CATALOG[sid].curriculum_anchor,
            "evidence_cases": evidence.get(sid, []),
        }
        for sid in sorted(cls)
    }
    gap_verdicts = {
        r.mechanism: {
            "verdict": "HONEST_GAP" if r.matched else "GAP_NOT_ENFORCED",
            "case_id": r.case_id,
        }
        for r in records
        if r.archetype == "near_miss" and r.mechanism
    }
    return {
        "knowledge_units": coverage_rows(),
        "targets": targets,
        "intentional_gap_verdicts": gap_verdicts,
        "leak_observations": build_leak_ledger(records),
    }


# ── 5+6. hai báo cáo markdown (tất định — không timestamp trong nội dung) ──
def build_authenticity_report_md(records: list[AuditRecord]) -> str:
    m = build_authenticity_metrics(records)
    cls = classify_targets(records)
    lines = [
        "# Báo cáo Authenticity Audit — M17-Lite Wave 0 (offline)",
        "",
        "Sinh tự động từ `app/evaluation/authenticity_*` — chạy TOÀN BỘ case",
        "matrix qua production `run_pipeline` (bất biến #22) với provider",
        "scripted per-case. KHÔNG sửa tay file này — chạy",
        "`python scripts/generate_m17_wave0_artifacts.py`.",
        "",
        "## Tổng quan",
        "",
        f"- Tổng case: **{m['total_cases']}**",
        f"- Near-miss gap recall: **{m['near_miss_gap_recall']['numerator']}/{m['near_miss_gap_recall']['denominator']}**",
        f"- Chặn oan trên ok-archetype: **{m['false_refusal_on_ok_archetypes']}**",
        f"- Envelope integrity (id concrete, không token): **{m['concrete_envelope_integrity']['numerator']}/{m['concrete_envelope_integrity']['denominator']}**",
        f"- Production parity (#22): **{m['production_parity']['numerator']}/{m['production_parity']['denominator']}**",
        f"- Generic leak vô điều kiện: **{m['generic_leak']['unconditional_leaks']}**",
        f"- Generic leak CÓ ĐIỀU KIỆN (probe adversarial): **{m['generic_leak']['conditional_leaks_confirmed']}**",
        "",
        "## Phân loại per-target",
        "",
        "| Target | Phân loại |",
        "|---|---|",
    ]
    for sid, v in sorted(cls.items()):
        lines.append(f"| `{sid}` | {v} |")
    lines += [
        "",
        "## Theo archetype",
        "",
        "| Archetype | Đạt/Tổng |",
        "|---|---|",
    ]
    for arch, b in sorted(m["by_archetype"].items()):
        shown = f"{b['matched']}/{b['total']}" + (" (probe)" if b["probe"] else "")
        lines.append(f"| {arch} | {shown} |")
    lines += [
        "",
        "## Phát hiện chính (W0)",
        "",
        "1. **Regression duyệt cây (honest):** analyze trung thực"
        " (`result_ownership=algorithmic`) → computation gate chặn fail-closed,"
        " KHÔNG dựng Điểm/Đoạn nối/Vật di chuyển. ✔",
        "2. **Probe adversarial duyệt cây:** khi analyze khai man"
        " (`ownership=provided` + scene staging roles), generic dựng cảnh và trả"
        " ok → **CONDITIONAL_LEAK_CONFIRMED** (pin bằng test"
        " `test_pin_adversarial_tree_probe_conditional_leak`). Gate hiện tại"
        " fail-closed THEO TÍN HIỆU CẤU TRÚC — bảo chứng phụ thuộc analyze"
        " trung thực (bằng chứng live M16: 24/24 analyze trung thực). Fix dài"
        " hạn = family `tree_traversal` (Wave 2); mọi siết gate thêm là"
        " production change cần user duyệt.",
        "3. **4/4 intentional gap** (selection/quick/unspecified sort, cơ số ≠ 2)"
        " bị chặn đúng mã `gate_mechanism_ownership`.",
        "4. **Đối chứng representation** (vẽ sơ đồ khai báo) KHÔNG bị chặn oan.",
        "",
    ]
    return "\n".join(lines)


def build_gap_report_md(records: list[AuditRecord]) -> str:
    cov = build_curriculum_coverage(records)
    lines = [
        "# Báo cáo Curriculum Gap — M17-Lite Wave 0",
        "",
        "Sinh tự động (xem authenticity report). Trạng thái coverage lấy từ",
        "`app/simulation/coverage.py` (M14 §O) + phán quyết audit W0.",
        "",
        "## Đơn vị kiến thức chưa được hỗ trợ (CAPABILITY_GAP)",
        "",
    ]
    for u in cov["knowledge_units"]:
        if u["status"] == "CAPABILITY_GAP":
            lines.append(f"- **{u['label']}** (`{u['unit_id']}`, {u['curriculum_anchor']}): {u['note']}")
    lines += [
        "",
        "## Đơn vị kiến thức PARTIAL",
        "",
    ]
    for u in cov["knowledge_units"]:
        if u["status"] == "PARTIAL":
            lines.append(f"- **{u['label']}** (`{u['unit_id']}`): {u['note']}")
    lines += [
        "",
        "## Cơ chế intentional-gap (audit W0 xác nhận chặn trung thực)",
        "",
    ]
    for mech, v in sorted(cov["intentional_gap_verdicts"].items()):
        lines.append(f"- `{mech}`: {v['verdict']} (case `{v['case_id']}`)")
    lines += [
        "",
        "## Gap sẽ đóng trong M17-Lite (theo proposal đã duyệt)",
        "",
        "- `positional_representation.non_binary_base` → Wave 1 (base conversion 2/8/10/16).",
        "- `comparison_sort.select_extreme_repeated` → Wave 1 (Selection Sort).",
        "- Duyệt cây (`tree_traversal`) → Wave 2 (family mới; regression W0 đang gap trung thực).",
        "- CSDL bảng/truy vấn (`database_table_query`) → Wave 2 (`relational_table_query`).",
        "",
        "## Gap giữ nguyên làm future work (KHÔNG trong M17-Lite)",
        "",
        "- `comparison_sort.partition_recursive` (Quick Sort) — contract chưa biểu diễn partition.",
        "- `dijkstra_weighted_shortest_path` — future family weighted_shortest_path.",
        "- `os_process_fsm` — chưa có FSM.",
        "- bounded_control_flow, dom_css_resolution — theo scope đã chốt.",
        "",
    ]
    return "\n".join(lines)
