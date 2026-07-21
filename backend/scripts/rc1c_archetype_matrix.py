# -*- coding: utf-8 -*-
"""M17-RC1 §C — sinh artifact archetype matrix / coverage / gap / ledger.

Chạy 73 case audit W0/W1 (TÁI DÙNG, không sửa) + 4 case §C qua production
``run_pipeline`` với provider kịch bản (0 network), rồi phân giải 8 slot cho
từng target trong 19 target AI-reachable.

    python scripts/rc1c_archetype_matrix.py --out docs/evaluation/m17/rc1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import pipeline  # noqa: E402
from app.evaluation.rc1c_matrix import (  # noqa: E402
    COVERAGE_GAP,
    COVERED_FAIL,
    COVERED_PASS,
    NOT_APPLICABLE,
    SLOTS,
    analyze_expressible_families,
    build_target_records,
    coverage_gaps,
    coverage_metrics,
    records_as_dicts,
    run_all_cases,
)
from app.runtime_identity import runtime_identity  # noqa: E402

_MARK = {COVERED_PASS: "✓", COVERED_FAIL: "✗", COVERAGE_GAP: "○", NOT_APPLICABLE: "–"}


def _set_provider(fake):
    pipeline.call_gemini = fake


def coverage_md(targets, metrics, gaps) -> str:
    m = metrics
    lines = [
        "# M17-RC1 §C — Catalog Archetype Matrix",
        "",
        "Coverage THẬT của toàn danh mục: mỗi target × 8 archetype slot. Case chạy",
        "qua **production `run_pipeline`** (bất biến #22) với provider kịch bản.",
        "",
        "> **Ranh giới claim.** Provider là kịch bản ⇒ mọi số dưới đây đo **tầng",
        "> quyết định phía server** (route handling / gate / validator / completeness)",
        "> khi analyze đã cho trước — KHÔNG đo năng lực classify của LLM thật.",
        "> Độ chính xác classify live đo riêng ở live smoke W1/W2A.",
        "",
        "## Số tổng",
        "",
        f"- Target: **{m['target_count']}** · family: **{m['family_count']}**",
        f"- Slot: **{m['total_archetype_slots']}** = "
        f"{_MARK[COVERED_PASS]} {m['covered_pass']} · "
        f"{_MARK[COVERED_FAIL]} {m['covered_fail']} · "
        f"{_MARK[COVERAGE_GAP]} {m['coverage_gap']} · "
        f"{_MARK[NOT_APPLICABLE]} {m['not_applicable']}",
        f"- Coverage = pass / (pass+fail+gap) = **{m['covered_pass']}/"
        f"{m['coverage_denominator']}** = **{m['coverage_ratio']}** "
        "(NOT_APPLICABLE KHÔNG nằm trong mẫu số)",
        f"- Target phủ đủ: **{m['targets_full_coverage']}** · phủ một phần: "
        f"**{m['targets_partial_coverage']}** · có gap chặn: "
        f"**{m['targets_with_blocking_gap']}**",
        f"- Case đã chạy: **{m['total_cases_executed']}** · route đúng: "
        f"**{m['route_accuracy']['numerator']}/{m['route_accuracy']['denominator']}**",
        "",
        "### Chỉ số an toàn (mọi số phải là 0)",
        "",
        "| Chỉ số | Giá trị |",
        "|---|---|",
        f"| generic_leak | **{m['generic_leak_count']}** |",
        f"| false_positive_simulation | **{m['false_positive_simulation_count']}** |",
        f"| false_refusal | **{m['false_refusal_count']}** |",
        f"| semantic_loss | **{m['semantic_loss_count']}** |",
        f"| result_leakage | **{m['result_leakage_count']}** |",
        "",
        f"Engine authenticity: REAL **{m['engine_REAL_count']}** · PARTIAL "
        f"**{m['engine_PARTIAL_count']}** · BROKEN **{m['engine_BROKEN_count']}**",
        "",
        "## Ma trận",
        "",
        f"Ký hiệu: {_MARK[COVERED_PASS]} COVERED_PASS · {_MARK[COVERED_FAIL]} "
        f"COVERED_FAIL · {_MARK[COVERAGE_GAP]} COVERAGE_GAP · {_MARK[NOT_APPLICABLE]} "
        "NOT_APPLICABLE",
        "",
        "| Target | Family | " + " | ".join(s[:4] + "…" for s in SLOTS) + " | engine | visual |",
        "|---" * (len(SLOTS) + 4) + "|",
    ]
    for t in targets:
        marks = " | ".join(_MARK[t["archetype_slots"][s]["status"]] for s in SLOTS)
        lines.append(
            f"| `{t['target_id']}` | {', '.join(t['family_id'])} | {marks} | "
            f"{t['engine_authenticity']} | {t['visual_authenticity']} |"
        )
    lines += ["", "Cột theo thứ tự: " + " · ".join(f"{s[:4]}… = `{s}`" for s in SLOTS), ""]

    lines += ["## Coverage gap", ""]
    if not gaps:
        lines.append("Không có gap.")
    else:
        lines += ["| Target | Slot | Loại | Chặn? | Lý do |", "|---|---|---|---|---|"]
        for g in gaps:
            lines.append(
                f"| `{g['target_id']}` | {g['slot']} | `{g['gap_kind']}` | "
                f"{'CÓ' if g['blocking'] else 'không'} | {g['reason']} |"
            )
    return "\n".join(lines) + "\n"


def ledger_md(records, targets, metrics) -> str:
    fails = [r for r in records if not r.matched]
    lines = [
        "# M17-RC1 §C — Failure ledger",
        "",
        f"Case chạy: **{len(records)}** · không khớp kỳ vọng: **{len(fails)}**",
        "",
    ]
    if not fails:
        lines.append("Không có case lệch kỳ vọng.")
    else:
        lines += [
            "| Case | Slot | Family | Kỳ vọng | Thực tế | error_code | Ghi chú |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in fails:
            lines.append(
                f"| `{r.case_id}` | {r.slot} | {r.family_id or '—'} | "
                f"{r.expected_status}"
                f"{'/' + r.expected_error_code if r.expected_error_code else ''} | "
                f"{r.actual_status}{'→' + r.route if r.route else ''} | "
                f"`{r.error_code or '—'}` | {r.reason or '—'} |"
            )
    broken = [t["target_id"] for t in targets if t["engine_authenticity"] == "BROKEN"]
    lines += [
        "",
        "## Điều kiện dừng (§C stop conditions)",
        "",
        "| Điều kiện | Giá trị | Kích hoạt? |",
        "|---|---|---|",
    ]
    for label, value in (
        ("COVERED_FAIL ở supported_canonical",
         sum(1 for t in targets
             if t["archetype_slots"]["supported_canonical"]["status"] == COVERED_FAIL)),
        ("generic_leak", metrics["generic_leak_count"]),
        ("false_positive_simulation", metrics["false_positive_simulation_count"]),
        ("semantic_loss", metrics["semantic_loss_count"]),
        ("result_leakage", metrics["result_leakage_count"]),
        ("executor ownership sai (engine BROKEN)", len(broken)),
    ):
        lines.append(f"| {label} | **{value}** | {'**CÓ**' if value else 'không'} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="docs/evaluation/m17/rc1")
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    original = pipeline.call_gemini
    try:
        records = run_all_cases(_set_provider)
    finally:
        pipeline.call_gemini = original

    targets = build_target_records(records)
    metrics = coverage_metrics(targets, records)
    gaps = coverage_gaps(targets)

    payload = {
        "schema_version": "1",
        "run_label": "rc1-c-archetype-matrix",
        "source_identity": runtime_identity(),
        "claim_boundary": (
            "Provider kịch bản: đo tầng quyết định phía server (route/gate/"
            "validator/completeness) khi analyze cho trước — KHÔNG đo classify "
            "của LLM thật."
        ),
        "slots": list(SLOTS),
        "analyze_expressible_families": sorted(analyze_expressible_families()),
        "metrics": metrics,
        "targets": targets,
        "cases": records_as_dicts(records),
    }
    (out / "catalog_archetype_matrix.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "coverage_gaps.json").write_text(
        json.dumps({"schema_version": "1", "gap_count": len(gaps), "gaps": gaps},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "catalog_coverage_report.md").write_text(
        coverage_md(targets, metrics, gaps), encoding="utf-8")
    (out / "rc1_c_failure_ledger.md").write_text(
        ledger_md(records, targets, metrics), encoding="utf-8")

    m = metrics
    print(f"Target {m['target_count']} · slot {m['total_archetype_slots']} "
          f"(pass {m['covered_pass']} / fail {m['covered_fail']} / gap "
          f"{m['coverage_gap']} / n-a {m['not_applicable']})")
    print(f"case {m['total_cases_executed']} · leak {m['generic_leak_count']} · "
          f"fp-sim {m['false_positive_simulation_count']} · false-refusal "
          f"{m['false_refusal_count']} · semantic-loss {m['semantic_loss_count']} · "
          f"result-leak {m['result_leakage_count']}")
    print(f"Artifacts → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
