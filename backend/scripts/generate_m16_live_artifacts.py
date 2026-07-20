# -*- coding: utf-8 -*-
"""M16 Bước 8 — sinh live artifact TỪ trace của một live run (không chạy lại AI).

Đầu vào: trace JSON do `python -m app.evaluation.live --out <trace>` ghi
(schema_version 1, cases[].record = asdict(M16CaseRecord)).
Đầu ra (docs/evaluation/m16/): m16-live-results-<label>.json ·
m16-live-metrics-<label>.json · m16-live-failure-ledger-<label>.json ·
m16-live-coverage-<label>.json (+ bản sao trace-<label>.json).

Mọi artifact sinh TỪ trace/run output — không viết tay (chuẩn M16 Wave 6).
Chạy tay:  .venv/Scripts/python scripts/generate_m16_live_artifacts.py trace-baseline.json
"""
from __future__ import annotations

import dataclasses
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evaluation.m16_artifacts import (  # noqa: E402
    _m16_by_case,
    build_failure_ledger,
    build_metrics_artifact,
)
from app.evaluation.m16_metrics import aggregate  # noqa: E402
from app.evaluation.m16_record import M16CaseRecord  # noqa: E402

_OUT_DIR = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "m16"


def _git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
        cwd=Path(__file__).resolve().parents[1],
    ).stdout.strip()


def _envelope(trace: dict, data, *, extra_meta: dict | None = None) -> dict:
    """Vỏ chung: provenance + usage THẬT từ trace (model/budget/label)."""
    budget = trace.get("budget_cumulative") or trace.get("budget") or {}
    cases = trace.get("cases") or []
    return {
        "schema_version": "1",
        "dataset_version": trace["dataset_version"],
        "run_label": trace["run_label"],  # "baseline" = pre-fix
        "prefix_label": "pre-fix" if trace["run_label"] == "baseline" else "post-fix",
        "model": trace.get("run_meta", {}).get("model"),
        "provider": "google-gemini",
        "run_meta": {
            "git_commit": _git_commit(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_trace_started_at": trace.get("run_meta", {}).get("started_at"),
            **(extra_meta or {}),
        },
        "usage": {
            "logical_cases_attempted": len(cases),
            "http_calls": budget.get("http_requests"),
            "logical_calls": budget.get("logical_calls"),
            "retry_requests": budget.get("retry_requests"),
            "transient_hits": budget.get("transient_hits"),
        },
        "data": data,
    }


def main(argv: list[str]) -> int:
    trace_path = Path(argv[1]) if len(argv) > 1 else Path("trace-baseline.json")
    label = trace_path.stem.replace("trace-", "") or "baseline"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))

    records = [M16CaseRecord(**c["record"]) for c in trace.get("cases", [])]
    m16_map = _m16_by_case()
    agg = aggregate(records, run_label=f"live_{label}", m16_by_case=m16_map)

    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        f"m16-live-results-{label}.json": _envelope(
            trace, [dataclasses.asdict(r) for r in records]
        ),
        f"m16-live-metrics-{label}.json": _envelope(trace, build_metrics_artifact(agg)),
        # live ledger: CHỈ failure của run thật — bỏ injected_proofs (đó là mô
        # tả fault-injection offline, không thuộc live run)
        f"m16-live-failure-ledger-{label}.json": _envelope(
            trace, {"cases": build_failure_ledger(records, m16_map)["cases"]}
        ),
        f"m16-live-coverage-{label}.json": _envelope(
            trace,
            {
                "attempted_case_ids": [c["case_id"] for c in trace.get("cases", [])],
                "status_final_counts": _count_status(trace),
            },
        ),
    }
    for name, payload in outputs.items():
        path = _OUT_DIR / name
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Đã sinh {path}")
    # bản sao trace nguyên vẹn (kể cả case fail) vào docs/evaluation/m16/
    dst = _OUT_DIR / f"trace-{label}.json"
    shutil.copyfile(trace_path, dst)
    print(f"Đã sao {dst}")
    return 0


def _count_status(trace: dict) -> dict:
    counts: dict[str, int] = {}
    for c in trace.get("cases", []):
        counts[c.get("status_final", "?")] = counts.get(c.get("status_final", "?"), 0) + 1
    return counts


if __name__ == "__main__":
    sys.exit(main(sys.argv))
