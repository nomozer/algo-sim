# -*- coding: utf-8 -*-
"""Render the report's Markdown tables from the two JSON receipts (no hand-typed numbers).

    python render_tables.py > tables.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    b = json.loads((RUN / "ocr_benchmark.json").read_text(encoding="utf-8"))
    v = json.loads((RUN / "vision_calls_before_after.json").read_text(encoding="utf-8"))
    E = b["engines"]
    print("### Table 1 — accuracy (scored items with ground truth)\n")
    print("| engine | items | CER strict full (median) | CER lenient body (median / max) | VN words exact | VN base letters ok | math tokens exact | text exact (lenient) |")
    print("|---|---|---|---|---|---|---|---|")
    for n, s in E.items():
        if "error" in s:
            print(f"| {n} | ERROR {s['error']} | | | | | | |")
            continue
        print(f"| {n} | {s['items_scored']} | {s['cer_strict_full_median']} | {s['cer_lenient_body_median']} / {s['cer_lenient_body_max']} | "
              f"{s['vi_word_exact_accuracy']} ({s['vi_words_total']} words) | {s['vi_word_base_letter_accuracy']} | "
              f"{s['math_tokens_exact_items']}/{s['items_scored']} | {s['text_exact_lenient_items']}/{s['items_scored']} |")
    syms = sorted({k for s in E.values() if "symbol_recall" in s for k in s["symbol_recall"]})
    print("\n### Table 2 — math symbol recall strict (lenient: − ≡ -, ′ ≡ ')\n")
    print("| symbol | GT count | " + " | ".join(E) + " |")
    print("|---|---|" + "---|" * len(E))
    for k in syms:
        gt = next(s["symbol_recall"][k]["gt"] for s in E.values() if "symbol_recall" in s and k in s["symbol_recall"])
        cells = []
        for s in E.values():
            r = s.get("symbol_recall", {}).get(k)
            cells.append(f"{r['strict_rate']} ({r['lenient_rate']})" if r else "NOT_MEASURED")
        print(f"| `{k}` | {gt} | " + " | ".join(cells) + " |")
    print("\n### Table 3 — cost (this host, CPU only)\n")
    print("| engine | version | cold ms (init + first item) | warm ms median / max | peak RSS MB | model bytes |")
    print("|---|---|---|---|---|---|")
    for n, s in E.items():
        if "error" in s:
            continue
        print(f"| {n} | {s['engine_version']} | {s['cold_ms_init_plus_first_item']} | {s['warm_ms_median']} / {s['warm_ms_max']} | "
              f"{s['peak_rss_mb']} | {sum(s['model_files_bytes'].values())} |")
    print("\n### Table 4 — local-only gate (calibrated on the same labelled set; NOT held out)\n")
    print("| engine / variant | rule-only accepts | rule-only unsafe | rule-only wrong math fact | calibrated (t_conf, t_uncovered) | calibrated accepts (0 unsafe) | accepted ids |")
    print("|---|---|---|---|---|---|---|")
    for n, s in E.items():
        if "error" in s:
            continue
        sel = s["gate_calibration"]["selected"]
        print(f"| {n} | {s['gate_rule_only_accepts']} | {s['gate_rule_only_unsafe_accepts']} | {s['gate_rule_only_wrong_math_fact_accepts']} | "
              f"{(sel['t_conf'], sel['t_uncovered']) if sel else 'NONE'} | {sel['accepted'] if sel else 0} | {', '.join(s.get('gate_local_accept_ids', [])) or '—'} |")
    for n, c in b.get("cross_engine_gate_variants", {}).items():
        sel = c["selected"]
        print(f"| {n} (cross-engine) | {c['rule_only_accepts']} | {c['rule_only_unsafe']} | — | "
              f"{(sel['t_conf'], sel['t_uncovered']) if sel else 'NONE'} | {sel['accepted'] if sel else 0} | {', '.join(c['accepted_ids']) or '—'} |")
    diag = {it["item_id"]: it["diagram"] for it in b["items"]}
    print("\n### Table 4b — what the gate let through (rule-only, no thresholds)\n")
    print("| engine | accepted item | text exact (lenient) | math-token edit distance | has diagram | OCR body (as accepted) |")
    print("|---|---|---|---|---|---|")
    for n, rows in b["per_item"].items():
        for r in rows:
            if not r["gate"]["reasons"]:
                print(f"| {n} | `{r['item_id']}` | {r['score'].get('text_exact_lenient')} | {r['score'].get('math_token_edit_distance')} | "
                      f"{diag[r['item_id']] or '—'} | {r['gate']['body_text']} |")
    missed = {n: [i for i in c["accepted_ids"] if diag[i]] for n, c in b.get("cross_engine_gate_variants", {}).items()}
    print("\nCross-engine calibrated accepts whose image HAS a diagram (Vision diagram observations would be skipped): "
          + "; ".join(f"{n}: {', '.join(v) or 'none'}" for n, v in missed.items()))
    print("\n### Table 5 — gate reason counts (items flagged per rule)\n")
    reasons = sorted({k for s in E.values() for k in s.get("gate_reason_counts", {})})
    print("| reason | " + " | ".join(E) + " |")
    print("|---|" + "---|" * len(E))
    for r in reasons:
        print(f"| {r} | " + " | ".join(str(s.get("gate_reason_counts", {}).get(r, 0)) for s in E.values()) + " |")
    print("\n### Table 6 — Vision provider calls, same image set (offline MOCK provider; real network calls = 0)\n")
    print("| mode | images | pass 1 calls | pass 2 calls (same images) | pass 2 cache hits | pass 1 text == GT | multi-image journey calls (3 attachments: A, A dup, diagram-only) |")
    print("|---|---|---|---|---|---|---|")
    for m in ("before", "after"):
        r = v[m]
        print(f"| {m} | {r['items']} | {r['pass1_mock_provider_calls']} | {r['pass2_mock_provider_calls_same_images']} | {r['pass2_cache_hits']} | "
              f"{r['pass1_text_equals_gt']} | {r['multi_image_journey']['mock_provider_calls']} |")
    diff = [(a["item_id"], a["mock_provider_calls"], c["mock_provider_calls"]) for a, c in zip(v["before"]["rows"], v["after"]["rows"])
            if a["pass"] == 1 and a["mock_provider_calls"] != c["mock_provider_calls"]]
    print("\nItems whose call count changed (before → after): " + (", ".join(f"`{i}` {x} → {y}" for i, x, y in diff) or "none"))
    after_rows = {r["item_id"]: r["mock_provider_calls"] for r in v["after"]["rows"] if r["pass"] == 1}
    total = len(after_rows)
    print("\n### Table 7 — PREDICTED (not shipped, in-sample) Vision calls if a cross-engine gate ran before Vision\n")
    print("| variant | local-only accepts | local-only rate | fallback rate | predicted Vision calls (after-fix baseline "
          f"{sum(after_rows.values())}) |")
    print("|---|---|---|---|---|")
    for n, c in b.get("cross_engine_gate_variants", {}).items():
        acc = c["accepted_ids"]
        pred = sum(k for i, k in after_rows.items() if i not in acc)
        print(f"| {n} | {len(acc)} | {len(acc) / total:.1%} | {1 - len(acc) / total:.1%} | {pred} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
