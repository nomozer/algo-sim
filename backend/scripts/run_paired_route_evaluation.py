# -*- coding: utf-8 -*-
"""Paired LLM_ONLY vs Hybrid evaluation harness — protocol: `docs/evaluation/geometry/runs/hybrid-master-backend-replacement/
live-evaluation-protocol.md`.

ONE scorer for both arms: the learner-visible target quantities of the served envelope (`scene3d` objects of type
`quantity` in display group `target`), keyed by their producer kind and compared as multisets of exact squared values —
never by model-chosen names. Offline by default: `--dry-run` reads recorded arm outputs from the corpus and proves only
scoring, accounting and statistics (MEASUREMENT_CLASS = OFFLINE_DETERMINISTIC_FIXTURE_TEST). `--live` refuses before any
request unless ALLOW_LIVE_AI=1, GEMINI_API_KEY and an Owner approval file bound to the corpus/oracle hashes and caps.

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/run_paired_route_evaluation.py \
        --corpus <corpus.json> --out <rows.json> --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

#: scene3d producer → oracle kind. `measure.distance` covers lengths and distances (both are a distance of two objects).
KINDS = {"measure.distance": "distance", "measure.angle_cos_sq": "angle_cos_sq", "measure.volume": "volume",
         "measure.area": "area"}
PROMPT_FRAMING_RESERVE = 4096          # same conservative estimator as `run_hybrid_ab_pilot.reserve_payload`
HYBRID_OUTPUT_CAP = 3072               # `fact_extraction.MAX_OUTPUT_TOKENS` family: the Hybrid request's own cap


class LiveRefused(RuntimeError):
    """The live path is not authorized; raised BEFORE any request."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_squared(exact: dict[str, Any]) -> Fraction:
    if exact.get("kind") == "rational":
        return Fraction(exact["value"]) ** 2
    if exact.get("kind") == "radical":
        return Fraction(exact["coefficient"]) ** 2 * Fraction(exact["radicand"])
    raise ValueError(f"unsupported exact form {exact!r}")


def served_quantities(envelope: dict[str, Any] | None) -> dict[str, list[Fraction]]:
    """Target quantities the learner sees, by kind, as sorted squared exact values. An unknown producer is kept under
    its own name so it can never silently satisfy an oracle kind."""
    out: dict[str, list[Fraction]] = {}
    for o in ((envelope or {}).get("scene3d") or {}).get("objects", []):
        if o.get("type") == "quantity" and "target" in (o.get("display_group") or []) and o.get("exact"):
            kind = KINDS.get(o.get("producer"), str(o.get("producer")))
            value = exact_squared(o["exact"])
            out.setdefault(kind, []).append(value if kind != "angle_cos_sq" else Fraction(o["exact"]["value"]))
    return {k: sorted(v) for k, v in out.items()}


def score(case: dict[str, Any], envelope: dict[str, Any] | None) -> dict[str, Any]:
    served = bool(envelope) and envelope.get("status") == "ok" and bool((envelope.get("scene3d") or {}).get("objects"))
    got = served_quantities(envelope) if served else {}
    expect_serve = case["expect"] == "SERVE"
    oracle = {k: sorted(Fraction(v) for v in vs) for k, vs in (case.get("oracle") or {}).items()}
    correct = served and expect_serve and got == oracle          # an extra or missing served target is not correct
    code = (envelope or {}).get("error_code") or (envelope or {}).get("reason_code")
    return {"served": served, "served_correct": correct,
            "wrong_served": served and not correct,
            "false_refusal": expect_serve and not served,
            "refusal_reason_correct": (not expect_serve and not served
                                       and code in case.get("acceptable_refusal_codes", [])),
            "refusal_code": None if served else code,
            "served_quantities": {k: [str(x) for x in v] for k, v in got.items()}}


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float] | None:
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact binomial p-value on the discordant pairs (b: only arm 1 right, c: only arm 2 right)."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    arms = sorted({r["arm"] for r in rows})
    out: dict[str, Any] = {}
    for arm in arms:
        rs = [r for r in rows if r["arm"] == arm]
        pos = [r for r in rs if r["expect"] == "SERVE"]
        neg = [r for r in rs if r["expect"] != "SERVE"]
        usd = [r["usd"] for r in rs]
        ok = sum(r["served_correct"] for r in rs)
        out[arm] = {
            "n": len(rs), "served_correct": ok, "served_correct_ci95": wilson(ok, len(pos)),
            "wrong_served": sum(r["wrong_served"] for r in rs),
            "wrong_served_ci95": wilson(sum(r["wrong_served"] for r in rs), len(rs)),
            "false_refusal": sum(r["false_refusal"] for r in pos),
            "negatives_refused": sum(not r["served"] for r in neg), "negatives": len(neg),
            "refusal_reason_correct": sum(r["refusal_reason_correct"] for r in neg),
            "latency_median_s": _quantile([r["latency_s"] for r in rs], 0.5),
            "latency_p90_s": _quantile([r["latency_s"] for r in rs], 0.9),
            "usd_total": "UNKNOWN" if any(u == "UNKNOWN" for u in usd) else sum(usd),
            "usd_per_served_correct": "UNKNOWN" if any(u == "UNKNOWN" for u in usd) or not ok else sum(usd) / ok,
        }
    if len(arms) == 2:
        a, b = arms
        by = {(r["case_id"], r["arm"]): r for r in rows}
        ids = sorted({i for i, _ in by if (i, a) in by and (i, b) in by})    # a stopped run may leave one arm only
        only_a = sum(by[i, a]["served_correct"] and not by[i, b]["served_correct"] for i in ids)
        only_b = sum(by[i, b]["served_correct"] and not by[i, a]["served_correct"] for i in ids)
        out["paired"] = {"arms": [a, b], "complete_pairs": len(ids),
                         "unpaired_cases": sorted({r["case_id"] for r in rows} - set(ids)),
                         f"only_{a}": only_a, f"only_{b}": only_b, "mcnemar_p": mcnemar_exact(only_a, only_b)}
    return out


def _quantile(xs: list[float], q: float) -> float | None:
    xs = sorted(x for x in xs if isinstance(x, (int, float)))
    if not xs:
        return None
    i = max(0, min(len(xs) - 1, math.ceil(q * len(xs)) - 1))
    return xs[i]


# ── arms ─────────────────────────────────────────────────────────────────────────────────────────────────────────────

def run_hybrid(text: str, extractor) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    result = run_hybrid_offline(text, extractor, policy=hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"}))
    return result.response.get("envelope"), {"source_references": result.receipt["source_references"],
                                              "failure_kind": result.receipt["failure_kind"]}


async def run_llm_only(text: str, api_key: str) -> dict[str, Any]:
    from app.ai.pipeline import route_policy_snapshot, run_pipeline
    return await run_pipeline(text, api_key, route_policy=route_policy_snapshot({}))


def gemini_transport(api_key: str):
    """Live Hybrid transport: one generateContent request, usage recorded under `hybrid_extraction`."""
    import httpx

    from app.ai import gemini
    from app.ai.telemetry import record_usage

    def send(request: dict[str, Any]) -> dict[str, Any]:
        if gemini.BUDGET is not None:          # the SAME pre-request caps the LLM_ONLY arm's `call_gemini` honours
            gemini.BUDGET.note_call()
            gemini.BUDGET.note_request(is_retry=False)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini.MODEL}:generateContent"
        r = httpx.post(url, params={"key": api_key}, json=request, timeout=60.0)
        r.raise_for_status()
        body = r.json()
        record_usage("hybrid_extraction", body.get("usageMetadata"))
        return body
    return send


def authorize_live(corpus_path: Path, approval_path: Path | None) -> dict[str, Any]:
    """Every check happens before the first request. The approval file is Owner-written; this harness never writes it."""
    if os.environ.get("ALLOW_LIVE_AI") != "1" or not os.environ.get("GEMINI_API_KEY"):
        raise LiveRefused("ALLOW_LIVE_AI=1 and GEMINI_API_KEY are required")
    if approval_path is None or not approval_path.is_file():
        raise LiveRefused("an Owner approval file is required")
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    if approval.get("owner_decision") != "APPROVED_BY_USER":
        raise LiveRefused("approval is not APPROVED_BY_USER")
    return check_approval_terms(corpus_path, approval)


def check_approval_terms(corpus_path: Path, approval: dict[str, Any]) -> dict[str, Any]:
    """The approved terms themselves (tests exercise this directly — automation never writes an approval value)."""
    if approval.get("corpus_sha256") != sha256_file(corpus_path):
        raise LiveRefused("corpus hash differs from the approved one")
    for key in ("max_requests", "max_usd", "input_usd_per_million", "output_usd_per_million", "model",
                "llm_only_output_reservation_tokens"):
        if key not in approval:
            raise LiveRefused(f"approval lacks {key}")
    from app.ai import gemini
    if approval["model"] != gemini.MODEL:
        raise LiveRefused("model differs from the approved one")
    worst = worst_case_request_usd(json.loads(corpus_path.read_text(encoding="utf-8")), approval)
    if approval["max_requests"] * worst > approval["max_usd"]:
        raise LiveRefused(f"max_requests × worst-case request cost ({approval['max_requests']} × {worst:.4f} USD) "
                          f"exceeds max_usd {approval['max_usd']}")
    return approval


#: Offline-measured request payload sizes in characters (`live-evaluation-protocol.md` §3), excluding the problem text.
#: The LLM_ONLY program request also repeats the extracted contract; it is bounded by two problem lengths plus framing.
MEASURED_OVERHEAD_CHARS = {"hybrid_extraction": 8297, "llm_only_analyze": 11782, "llm_only_program": 13169}


def worst_case_request_usd(corpus: dict[str, Any], approval: dict[str, Any]) -> float:
    """Conservative per-request ceiling (1 char ≥ 1 token, + framing; output at its cap or the approved reservation).
    Containment is by request COUNT before each request (`gemini.ApiBudget`); a provider cannot be stopped from billing
    a request already sent, so this is the residual risk bound, not a guarantee (hybrid-ab-pilot-readiness)."""
    longest = max(len(c["problem_text"]) for c in corpus["cases"])
    prompt = max(MEASURED_OVERHEAD_CHARS.values()) + 3 * longest + PROMPT_FRAMING_RESERVE
    output = max(HYBRID_OUTPUT_CAP, int(approval["llm_only_output_reservation_tokens"]))
    return prompt * approval["input_usd_per_million"] / 1e6 + output * approval["output_usd_per_million"] / 1e6


def usd(usage: dict[str, dict[str, int]], approval: dict[str, Any] | None) -> float | str:
    if approval is None or not usage:
        return "UNKNOWN"
    tin = sum(v.get("prompt_tokens", 0) for v in usage.values())
    tout = sum(v.get("candidates_tokens", 0) + v.get("thoughts_tokens", 0) for v in usage.values())
    return tin * approval["input_usd_per_million"] / 1e6 + tout * approval["output_usd_per_million"] / 1e6


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--corpus", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--live", action="store_true")
    p.add_argument("--approval-file", type=Path)
    a = p.parse_args(argv)
    approval = authorize_live(a.corpus, a.approval_file) if a.live else None
    out = evaluate(a.corpus, a.out, approval)
    print(json.dumps(out["summary"], ensure_ascii=False, indent=1, default=str))
    return 0


def evaluate(corpus_path: Path, out_path: Path, approval: dict[str, Any] | None) -> dict[str, Any]:
    """`approval is None` ⇒ dry run from recorded arm outputs; otherwise live under the approved terms."""
    from app.ai import gemini
    from app.ai.telemetry import reset_usage, usage_report
    from app.ai.typed_fact_next_extraction import ReplayExtractor, TransportExtractor

    a = argparse.Namespace(dry_run=approval is None, live=approval is not None, corpus=corpus_path, out=out_path)
    corpus = json.loads(a.corpus.read_text(encoding="utf-8"))
    budget = gemini.ApiBudget(max_api_calls=int(approval["max_requests"])) if approval else None
    gemini.set_budget(budget)
    rows: list[dict[str, Any]] = []
    spent, technical_streak, stop_reason = 0.0, 0, None
    try:
        for case in corpus["cases"]:
            for arm in ("HYBRID", "LLM_ONLY"):
                reset_usage()
                start = time.perf_counter()
                extra: dict[str, Any] = {}
                envelope, technical = None, False
                try:
                    if a.dry_run:
                        if arm == "HYBRID":
                            rec = case["dry_run"]["hybrid_extraction"]
                            envelope, extra = run_hybrid(case["problem_text"], ReplayExtractor(
                                {case["problem_text"]: rec} if rec is not None else {}))
                        else:
                            envelope = case["dry_run"]["llm_only_envelope"]
                    elif arm == "HYBRID":
                        envelope, extra = run_hybrid(case["problem_text"],
                                                     TransportExtractor(gemini_transport(os.environ["GEMINI_API_KEY"])))
                    else:
                        envelope = asyncio.run(run_llm_only(case["problem_text"], os.environ["GEMINI_API_KEY"]))
                    technical = extra.get("failure_kind") == "TECHNICAL_FAILURE"
                except gemini.BudgetExceeded:
                    stop_reason = "REQUEST_CAP"
                except Exception as exc:  # noqa: BLE001 — recorded as infrastructure, never as a model/geometry result
                    technical, extra = True, {"exception": type(exc).__name__}
                usage = usage_report()
                row = {"case_id": case["id"], "arm": arm, "expect": case["expect"],
                       "latency_s": time.perf_counter() - start, "usage": usage or "UNKNOWN",
                       "requests_with_usage": sum(v.get("calls", 0) for v in usage.values()) if usage else "UNKNOWN",
                       "usd": usd(usage, approval), "technical_failure": technical, **score(case, envelope), **extra}
                rows.append(row)
                spent += row["usd"] if isinstance(row["usd"], float) else 0.0
                technical_streak = technical_streak + 1 if technical else 0
                if stop_reason is None and budget is not None and budget.aborted:
                    stop_reason = "REQUEST_CAP"    # TransportExtractor turns BudgetExceeded into PROVIDER_ERROR
                if stop_reason is None and row["served"] and case["expect"] != "SERVE":
                    stop_reason = "SERVED_EXPECTED_REFUSAL"
                if stop_reason is None and approval and spent >= 0.8 * approval["max_usd"]:
                    stop_reason = "USD_80_PERCENT"
                if stop_reason is None and technical_streak >= 3:
                    stop_reason = "INFRASTRUCTURE_STREAK"
                if stop_reason:
                    break
            if stop_reason:
                break
    finally:
        gemini.set_budget(None)
    out = {"measurement_class": "PREREGISTERED_LIVE_PAIRED_EVALUATION" if a.live
           else "OFFLINE_DETERMINISTIC_FIXTURE_TEST",
           "corpus_sha256": sha256_file(a.corpus), "stop_reason": stop_reason,
           "http_requests": budget.http_requests if budget else 0,
           "rows": rows, "summary": summarize(rows)}
    with a.out.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)
        f.write("\n")
    return out


if __name__ == "__main__":
    raise SystemExit(main())
