# -*- coding: utf-8 -*-
"""Write `protocol.json`: locked input hashes, model/config, caps derived from the runner's own reservation of every
scheduled payload, stop rules and pilot continuation criteria. 0 provider calls.

    cd backend && python ../docs/evaluation/geometry/runs/independent-nlu-extraction-evaluation/inputs/build_protocol.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / "backend"))
from app.ai import fact_extraction as fx  # noqa: E402
from scripts.run_hybrid_ab_pilot import _sha, reserve_payload  # noqa: E402

CORPUS_PATH = "corpus-authoring/corpus.json"
corpus = json.loads((HERE / CORPUS_PATH).read_text(encoding="utf-8"))
gold = json.loads((HERE / "gold_facts.json").read_text(encoding="utf-8"))
SPLITS = {"PILOT": ("dev", 2), "LOCKED": ("locked", 1)}


def caps(split: str, samples: int) -> dict:
    res = [reserve_payload(p, p["generationConfig"]["maxOutputTokens"])
           for c in corpus["cases"] if c["split"] == split for p in [fx.build_request(c["source_text"])]] * samples
    n = len(res)
    return {"logical_calls": n, "http_attempts": n, "samples": samples,
            "accounted_tokens": int(math.ceil(sum(r["tokens"] for r in res) / 1000) * 1000),
            "usd": math.ceil(sum(r["usd"] for r in res) * 100) / 100}


protocol = {
    "schema": "NLU_EVAL_PROTOCOL/1",
    "run": "independent-nlu-extraction-evaluation",
    "corpus_path": CORPUS_PATH,
    "locked_sha256": {"corpus": _sha(corpus), "gold_facts": _sha(gold)},
    "provider": "Gemini API REST v1beta models/{model}:generateContent via app.ai.function_calling.live_transport "
                "(key in x-goog-api-key header, one attempt, ALLOW_LIVE_AI re-checked per send)",
    "model": "gemini-2.5-flash",
    "model_version_accepted": "exactly gemini-2.5-flash or a numbered pin gemini-2.5-flash-NNN; anything else stops",
    "adapter": "app.ai.fact_extraction.build_request / parse_response / run_ai_fact_route, unchanged",
    "surface_sha256": fx.surface_fingerprint(),
    "generation_config": {"temperature": 0.0, "maxOutputTokens": 8192, "responseMimeType": "application/json",
                          "responseSchema": "facts_response_schema()", "thinkingConfig": "not set (provider default)"},
    "sent_to_provider": "system prompt + response schema + the case's source_text only; never context, labels, "
                        "gold facts, oracle values or any personal data (the corpus is synthetic)",
    "retries": 0,
    "timeout_seconds": 90,
    "caps": {mode: caps(split, n) for mode, (split, n) in SPLITS.items()},
    "reservation_rule": "per call: canonical payload bytes + 4096 framing as input tokens, plus maxOutputTokens as "
                        "output+thinking, priced 0.30 / 2.50 USD per 1M (ai.google.dev pricing, paid Standard tier, "
                        "checked 2026-10-17); conservative, not a provider-proven bound",
    "stop_rules": [
        "any cap (logical calls, HTTP attempts, accounted tokens, USD, context) would be exceeded: stop BEFORE sending",
        "HTTP 400/401/403/429: stop at once (bad request or key, auth, quota); no retry",
        "3 consecutive infrastructure failures (timeout, 5xx, transport error): stop",
        "a single infrastructure failure: record the row (cost UNKNOWN if no usage), continue with the next case",
        "secret detected in any response or artifact: stop",
        "modelVersion not accepted: stop",
        "persistence failure or an uncertain in-flight request on resume: stop; never re-send",
    ],
    "pilot_continue_to_locked_if_all": [
        "no stop rule fired and all 32 planned rows recorded",
        "parse OK (a JSON facts list) on >= 28 of the 32 planned rows",
        "RESPONSE_TRUNCATED on <= 2 rows (else the 8192 cap is inadequate: a different cap is a NEW protocol, a new "
        "approval and a restarted pilot, never an edit of this one)",
        "usage counters present on every answered row",
    ],
    "pilot_gate_implementation": "run_nlu_extraction_evaluation.pilot_gate, written by SCORE --out",
    "decision_rule_on_locked": "run_nlu_extraction_evaluation.decide: P1 PASS iff 0 unsafe rows (WRONG_SERVED, "
                               "PARTIAL_SERVED, OVER_SERVED); P2 on goal/entity agreement with expressible gold requests: "
                               "YES if >= 0.85 and exact 95% lower bound >= 0.70, NO if the upper bound < 0.85, else "
                               "INCONCLUSIVE; answer UNSAFE if P1 fails, else P2",
    "approval": "approval file is written by the human owner only; it must name the exact identity printed for the mode",
    "never": ["change the prompt, schema, model, cap or product between pilot and locked or during locked",
              "retry a request", "re-score with labels edited after seeing outputs (corrections go to a separate "
              "receipt and are reported beside, never instead of, the locked score)",
              "count a refusal as a completed simulation", "count REPLAY/GOLD rows as live"],
    "single_turn": "group-E cases with a prior context are scored with effective disposition clarification_required "
                   "(CONTEXT_NOT_SENT); the corpus label is kept unchanged",
}
(HERE / "protocol.json").write_text(json.dumps(protocol, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(json.dumps({"locked_sha256": protocol["locked_sha256"], "caps": protocol["caps"],
                  "surface": protocol["surface_sha256"]}, indent=1))
