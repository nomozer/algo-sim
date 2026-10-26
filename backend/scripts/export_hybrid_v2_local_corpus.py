# -*- coding: utf-8 -*-
"""Write the authored replay corpus the Stage 2 local Hybrid V2 route reads (`app.ai.hybrid_offline.run_local_replay`).

Source: the locked authored development corpus of run `hybrid-contract-v2` (`evaluate_grammar_set.load_lock`, reused
without edits). Only `problem_text → typed-fact-next/2 payload` is written — no expected disposition, no oracle answer —
so the route sees exactly what a provider would return for that text. DEVELOPMENT data: not a holdout, not provider
output, not a language-understanding measurement. 0 provider calls.

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/export_hybrid_v2_local_corpus.py --out <file>
    # then: HYBRID_V2_LOCAL=offline-replay HYBRID_V2_LOCAL_REPLAY_CORPUS=<file> (loopback clients only)
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def build() -> dict:
    from app.ai.hybrid_offline import LOCAL_REPLAY_SCHEMA

    evaluator = runpy.run_path(str(ROOT / "docs/evaluation/geometry/runs/hybrid-contract-v2/evaluate_grammar_set.py"))
    cases = evaluator["load_lock"]()
    by_text: dict[str, list[tuple[str, dict]]] = {}
    for case in cases:
        by_text.setdefault(case["payload"]["problem_text"], []).append((case["id"], case["payload"]))
    # A replay is keyed by the exact text, so a text the corpus records with two DIFFERENT payloads (deliberate
    # extraction variants of one problem) has no single answer: it is left out and listed, never picked arbitrarily.
    outputs, ambiguous = {}, {}
    for text, rows in by_text.items():
        payloads = {json.dumps(p, sort_keys=True, ensure_ascii=False) for _, p in rows}
        if len(payloads) == 1:
            outputs[text] = rows[0][1]
        else:
            ambiguous[hashlib.sha256(text.encode("utf-8")).hexdigest()] = sorted(cid for cid, _ in rows)
    return {"schema": LOCAL_REPLAY_SCHEMA, "classification": "AUTHORED_DEVELOPMENT_REPLAY_NOT_PROVIDER_NOT_HOLDOUT",
            "source": {"corpus": "docs/evaluation/geometry/runs/hybrid-contract-v2 (load_lock)",
                       "corpus_sha256_lf": evaluator["LOCK_SHA"], "cases": len(cases)},
            "excluded_texts_with_several_payloads": ambiguous,
            "outputs": outputs}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    data = build()
    text = json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    out.write_text(text, encoding="utf-8")
    print(json.dumps({"out": str(out), "texts": len(data["outputs"]), "cases": data["source"]["cases"],
                      "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
