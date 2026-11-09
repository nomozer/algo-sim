"""Reconcile LOCAL_FIRST_IMAGE_INGESTION_REPORT.md §4 tables against the machine receipts (before/after_metrics.json).

Usage: python -I reconcile_receipts.py <run_dir> <out.json>
The JSON receipts are the tool's output (source of truth); the report tables were transcribed by hand.
"""
import json
import re
import sys
from pathlib import Path

run = Path(sys.argv[1])
b = json.loads((run / "before_metrics.json").read_text(encoding="utf-8"))
a = json.loads((run / "after_metrics.json").read_text(encoding="utf-8"))
report = (run / "LOCAL_FIRST_IMAGE_INGESTION_REPORT.md").read_text(encoding="utf-8")

by_b = {c["class_id"]: c for c in b["classes"]}
by_a = {c["class_id"]: c for c in a["classes"]}
num = r"([0-9]+(?:\.[0-9]+)?)"
rows, mismatches = [], []
for line in report.splitlines():
    m = re.match(r"\| `(class_\d+_[a-z_]+)` \|", line)
    if not m:
        continue
    cid = m.group(1)
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    calls = re.search(r"`(\d+) \+ (\d+) = (\d+)`", cells[5])
    prep = re.search(num + r" → " + num + r" ms", cells[7])
    recall = re.search(num + r" → " + num, cells[3])
    reported = {
        "vlm_calls": int(calls.group(1)), "typed_fact_calls": int(calls.group(2)),
        "before_prepare_ms": float(prep.group(1)), "after_prepare_ms": float(prep.group(2)),
        "before_recall": float(recall.group(1)), "after_recall": float(recall.group(2)),
    }
    receipt = {
        "vlm_calls": by_a[cid]["vlm_calls"], "typed_fact_calls": by_a[cid]["typed_fact_calls"],
        "before_prepare_ms": by_b[cid]["prepare_ms"], "after_prepare_ms": by_a[cid]["prepare_ms"],
        "before_recall": by_b[cid]["region_containment_recall"], "after_recall": by_a[cid]["region_containment_recall"],
    }
    for k in reported:
        if abs(reported[k] - receipt[k]) > 1e-6:
            mismatches.append({"class_id": cid, "field": k, "report": reported[k], "receipt": receipt[k]})
    rows.append(cid)

# global summary rows
for key in ("median_preprocess_ms", "median_prepare_ms", "median_e2e_ms", "max_peak_ram_kb"):
    for side, data in (("before", b), ("after", a)):
        if f"{data[key]:.2f}".rstrip("0").rstrip(".") not in report.replace(",", ""):
            mismatches.append({"summary": key, "side": side, "receipt": data[key], "report": "NOT_FOUND"})

out = {"schema": "receipt-reconciliation/1", "rows_checked": len(rows), "source_of_truth": "before_metrics.json + after_metrics.json",
       "mismatches": mismatches}
Path(sys.argv[2]).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
assert len(rows) == 11, rows
