# -*- coding: utf-8 -*-
"""Paired LLM_ONLY vs Hybrid evaluation harness — protocol: `docs/evaluation/geometry/runs/hybrid-master-backend-replacement/
live-evaluation-protocol.md`.

ONE scorer for both arms: the learner-visible target quantities of the served envelope (`scene3d` objects of type
`quantity` in display group `target`), keyed by their producer kind and compared as multisets of exact squared values —
never by model-chosen names. Offline by default: `--dry-run` reads recorded arm outputs from the corpus and proves only
scoring, accounting and statistics (MEASUREMENT_CLASS = OFFLINE_DETERMINISTIC_FIXTURE_TEST). `--live` refuses before any
request unless ALLOW_LIVE_AI=1, GEMINI_API_KEY and an Owner approval file bound to the corpus hash and caps; then every
HTTP request of BOTH arms passes `CostCappedBudget` first (request count AND accounted spend + per-request ceiling).

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/run_paired_route_evaluation.py \
        --corpus <corpus.json> --out <rows.json> --dry-run          # or --manifest / --live --approval-file <owner.json>
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import re
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

#: scene3d producer → oracle kind. `measure.distance` covers lengths and distances (both are a distance of two objects).
KINDS = {"measure.distance": "distance", "measure.angle_cos_sq": "angle_cos_sq", "measure.volume": "volume",
         "measure.area": "area", "measure.lateral_area": "lateral_area", "measure.radius": "radius"}
PROMPT_FRAMING_RESERVE = 4096          # same conservative estimator as `run_hybrid_ab_pilot.reserve_payload`
MODEL_OUTPUT_LIMIT = 65536             # gemini-2.5-flash, thinking included (provider-facts.md, read 2026-10-31)
#: Hybrid's cooperative deadline in the live harness: all transport attempts × the per-attempt timeout. The offline
#: route's 15 s default was set for replay; a live extraction must not be cut short where LLM_ONLY is not.
HYBRID_LIVE_DEADLINE_S = 4 * 120.0
#: Offline-measured request payload sizes in characters (`live-evaluation-protocol.md` §3), excluding the problem text.
MEASURED_OVERHEAD_CHARS = {"hybrid_extraction": 8297, "llm_only_analyze": 11782, "llm_only_program": 13169}


class LiveRefused(RuntimeError):
    """The live path is not authorized or the corpus is invalid; raised BEFORE any request."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ── corpus and identity ──────────────────────────────────────────────────────────────────────────────────────────────

def validate_corpus(corpus: dict[str, Any]) -> None:
    """Refuse a corpus that cannot be scored fairly: duplicate ids or texts (a duplicate request), an expected-serve
    case without an exact oracle, an unknown oracle kind, or an expected-refuse case without acceptable codes."""
    cases = corpus.get("cases")
    if not isinstance(cases, list) or not cases:
        raise LiveRefused("corpus has no cases")
    ids = [c.get("id") for c in cases]
    texts = [c.get("problem_text") for c in cases]
    if len(set(ids)) != len(ids) or len(set(texts)) != len(texts):
        raise LiveRefused("duplicate case id or problem text")
    for c in cases:
        if not isinstance(c.get("problem_text"), str) or not c["problem_text"].strip():
            raise LiveRefused(f"{c.get('id')}: empty problem text")
        if c.get("expect") == "SERVE":
            oracle = c.get("oracle") or {}
            if not oracle or set(oracle) - set(KINDS.values()):
                raise LiveRefused(f"{c['id']}: expected-serve case needs an oracle over {sorted(set(KINDS.values()))}")
            for values in oracle.values():
                [Fraction(v) for v in values]
        elif c.get("expect") == "REFUSE":
            if not c.get("acceptable_refusal_codes"):
                raise LiveRefused(f"{c['id']}: expected-refuse case needs acceptable_refusal_codes")
        else:
            raise LiveRefused(f"{c.get('id')}: expect must be SERVE or REFUSE")


#: Opened material a held-out text must not come from (heldout-authoring/README.md).
CONTAMINATION_ROOTS = ("docs/evaluation", "backend/tests", "frontend/src/data")


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def contamination_scan(corpus: dict[str, Any], repo: Path = BACKEND.parent) -> dict[str, list[str]]:
    """`{case id: [files containing its normalized problem text]}` over opened material. JSON files are decoded first
    (many store Vietnamese as \\u escapes), so a copy is found whatever the escaping."""
    wanted = {c["id"]: _norm(c["problem_text"]) for c in corpus["cases"]}
    hits: dict[str, list[str]] = {}

    def strings(v: Any):
        if isinstance(v, str):
            yield v
        elif isinstance(v, dict):
            for x in v.values():
                yield from strings(x)
        elif isinstance(v, list):
            for x in v:
                yield from strings(x)

    for root in CONTAMINATION_ROOTS:
        for path in (repo / root).rglob("*"):
            if not path.is_file() or path.suffix not in (".json", ".md", ".py", ".ts", ".tsx", ".txt", ".jsonl"):
                continue
            try:
                raw = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            text = raw
            if path.suffix == ".json":
                try:
                    text = "\n".join(strings(json.loads(raw)))
                except ValueError:
                    pass
            haystack = _norm(text)
            for cid, needle in wanted.items():
                if needle and needle in haystack:
                    hits.setdefault(cid, []).append(path.relative_to(repo).as_posix())
    return hits


def runtime_identity() -> dict[str, str]:
    """What the measurement is OF: measured product hash, cache version, model, prompt files, this harness."""
    sys.path.insert(0, str(BACKEND / "scripts"))
    import freeze_evaluation_candidate as F

    from app.ai import gemini
    skills = hashlib.sha256()
    for p in sorted((BACKEND / "app" / "ai" / "skills").glob("*.md")):
        skills.update(p.name.encode() + b"\0" + p.read_bytes())
    cache = re.search(r'^CACHE_VERSION = "([^"]+)"', (BACKEND / "app" / "main.py").read_text(encoding="utf-8"), re.M)
    return {"measured_system": F.measured_system_hash()[0], "cache_version": cache.group(1) if cache else "UNKNOWN",
            "model": gemini.MODEL, "skills_sha256": skills.hexdigest(), "harness_sha256": sha256_file(Path(__file__))}


# ── scoring ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def exact_squared(exact: dict[str, Any]) -> Fraction:
    if exact.get("kind") == "rational":
        return Fraction(exact["value"]) ** 2
    if exact.get("kind") == "radical":
        return Fraction(exact["coefficient"]) ** 2 * Fraction(exact["radicand"])
    raise ValueError(f"unsupported exact form {exact!r}")


def served_quantities(envelope: dict[str, Any] | None) -> dict[str, list[Fraction]]:
    """Target quantities the learner sees, by kind, as sorted squared exact values (cos² is compared as is). An unknown
    producer is kept under its own name so it can never silently satisfy an oracle kind."""
    out: dict[str, list[Fraction]] = {}
    for o in ((envelope or {}).get("scene3d") or {}).get("objects", []):
        if o.get("type") == "quantity" and "target" in (o.get("display_group") or []) and o.get("exact"):
            kind = KINDS.get(o.get("producer"), str(o.get("producer")))
            value = Fraction(o["exact"]["value"]) if kind == "angle_cos_sq" else exact_squared(o["exact"])
            out.setdefault(kind, []).append(value)
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


def _quantile(xs: list[float], q: float) -> float | None:
    xs = sorted(x for x in xs if isinstance(x, (int, float)))
    if not xs:
        return None
    i = max(0, min(len(xs) - 1, math.ceil(q * len(xs)) - 1))
    return xs[i]


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    arms = sorted({r["arm"] for r in rows})
    out: dict[str, Any] = {}
    for arm in arms:
        rs = [r for r in rows if r["arm"] == arm]
        pos = [r for r in rs if r["expect"] == "SERVE"]
        neg = [r for r in rs if r["expect"] != "SERVE"]
        usd = [r["usd"] for r in rs]
        ok = sum(r["served_correct"] for r in rs)
        unknown = any(u == "UNKNOWN" for u in usd)
        out[arm] = {
            "n": len(rs), "served_correct": ok, "served_correct_ci95": wilson(ok, len(pos)),
            "wrong_served": sum(r["wrong_served"] for r in rs),
            "wrong_served_ci95": wilson(sum(r["wrong_served"] for r in rs), len(rs)),
            "false_refusal": sum(r["false_refusal"] for r in pos),
            "negatives_refused": sum(not r["served"] for r in neg), "negatives": len(neg),
            "refusal_reason_correct": sum(r["refusal_reason_correct"] for r in neg),
            "technical_failures": sum(r["technical_failure"] for r in rs),
            "latency_median_s": _quantile([r["latency_s"] for r in rs], 0.5),
            "latency_p90_s": _quantile([r["latency_s"] for r in rs], 0.9),
            "usd_total": "UNKNOWN" if unknown else sum(usd),
            "usd_upper_total": sum(r["usd_upper"] for r in rs if isinstance(r["usd_upper"], float)),
            "usd_per_served_correct": "UNKNOWN" if unknown or not ok else sum(usd) / ok,
        }
    if rows:                   # always reported, so a run stopped inside its first arm still names its unpaired cases
        a, b = "HYBRID", "LLM_ONLY"
        by = {(r["case_id"], r["arm"]): r for r in rows}
        ids = sorted({i for i, _ in by if (i, a) in by and (i, b) in by})    # a stopped run may leave one arm only
        only_a = sum(by[i, a]["served_correct"] and not by[i, b]["served_correct"] for i in ids)
        only_b = sum(by[i, b]["served_correct"] and not by[i, a]["served_correct"] for i in ids)
        out["paired"] = {"arms": [a, b], "complete_pairs": len(ids),
                         "unpaired_cases": sorted({r["case_id"] for r in rows} - set(ids)),
                         f"only_{a}": only_a, f"only_{b}": only_b, "mcnemar_p": mcnemar_exact(only_a, only_b)}
    return out


# ── live authorization and cost containment ──────────────────────────────────────────────────────────────────────────

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
    if int(approval["llm_only_output_reservation_tokens"]) < MODEL_OUTPUT_LIMIT:
        raise LiveRefused("LLM_ONLY sets no output cap: the reservation must be at least the model output limit")
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    validate_corpus(corpus)
    worst = worst_case_request_usd(corpus, approval)
    if approval["max_requests"] * worst > approval["max_usd"]:
        raise LiveRefused(f"max_requests × worst-case request cost ({approval['max_requests']} × {worst:.4f} USD) "
                          f"exceeds max_usd {approval['max_usd']}")
    return approval


def worst_case_request_usd(corpus: dict[str, Any], approval: dict[str, Any]) -> float:
    """Conservative per-request ceiling: 1 char ≥ 1 token plus framing for input; output at the approved reservation,
    which must cover the model's own limit because the LLM_ONLY arm sets no `maxOutputTokens` (thinking included)."""
    from app.ai.function_calling import MAX_OUTPUT_TOKENS as HYBRID_OUTPUT_CAP

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


def request_ceiling_usd(payload: Any, approval: dict[str, Any]) -> float:
    """PROVABLE ceiling of ONE request, from the exact payload about to be sent: input tokens ≤ UTF-8 bytes of the
    request JSON (byte-fallback tokenization: every token covers ≥ 1 byte), output tokens ≤ the request's own
    `maxOutputTokens`, else the model limit (thinking included, provider-facts.md)."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    cap = ((payload or {}).get("generationConfig") or {}).get("maxOutputTokens") if isinstance(payload, dict) else None
    out = min(int(cap), MODEL_OUTPUT_LIMIT) if isinstance(cap, int) and cap > 0 else MODEL_OUTPUT_LIMIT
    return len(body) * approval["input_usd_per_million"] / 1e6 + out * approval["output_usd_per_million"] / 1e6


def _cost_capped_budget(approval: dict[str, Any]):
    """`gemini.ApiBudget` (the request cap `call_gemini` and `live_transport` already honour) plus a USD guard applied to
    the EXACT payload right before it is sent (`reserve`, called by the send interceptor of `evaluate`): spend of
    finished arms + this arm's reported usage + every sent request without reported usage at its own ceiling + the
    next request's ceiling must stay ≤ max_usd. A sent request cannot be un-billed; this bound makes that irrelevant."""
    from app.ai import gemini
    from app.ai.telemetry import usage_report

    class CostCappedBudget(gemini.ApiBudget):
        def __init__(self) -> None:
            super().__init__(max_api_calls=int(approval["max_requests"]))
            self.spent_before_arm = 0.0
            self.arm_ceilings: list[float] = []
            self.stop_reason: str | None = None

        def start_arm(self, spent: float) -> None:
            self.spent_before_arm, self.arm_ceilings = spent, []
            self.arm_start_requests = self.http_requests

        def arm_upper(self) -> float:
            usage = usage_report()
            known = usd(usage, approval) if usage else 0.0
            reported = sum(v.get("calls", 0) for v in usage.values())
            unreported = self.arm_ceilings[reported:]           # sent, billed-or-not, without usage yet: at ceiling
            return (known if isinstance(known, float) else 0.0) + sum(unreported)

        def reserve(self, ceiling: float) -> None:
            if self.spent_before_arm + self.arm_upper() + ceiling > approval["max_usd"]:
                self.aborted, self.stop_reason = True, "COST_CEILING"
                raise gemini.BudgetExceeded("the next request could exceed max_usd")
            self.arm_ceilings.append(ceiling)

        def note_request(self, is_retry: bool) -> None:
            try:
                super().note_request(is_retry)
            except gemini.BudgetExceeded:
                self.stop_reason = self.stop_reason or "REQUEST_CAP"
                raise

    return CostCappedBudget()


def _guard_sends(budget, approval: dict[str, Any]):
    """Wrap both HTTP send points (`httpx.post` of the Hybrid transport, `httpx.AsyncClient.post` of `call_gemini`) so
    every request reserves its exact ceiling first. Returns an undo function; behaviour is otherwise unchanged."""
    import httpx

    sync_post, async_post = httpx.post, httpx.AsyncClient.post

    def guarded_sync(url, *args, **kwargs):
        budget.reserve(request_ceiling_usd(kwargs.get("json"), approval))
        return sync_post(url, *args, **kwargs)

    async def guarded_async(self, url, *args, **kwargs):
        budget.reserve(request_ceiling_usd(kwargs.get("json"), approval))
        return await async_post(self, url, *args, **kwargs)

    httpx.post, httpx.AsyncClient.post = guarded_sync, guarded_async

    def undo() -> None:
        httpx.post, httpx.AsyncClient.post = sync_post, async_post
    return undo


# ── arms ─────────────────────────────────────────────────────────────────────────────────────────────────────────────

def run_hybrid(text: str, extractor, deadline_s: float = 15.0) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    result = run_hybrid_offline(text, extractor, policy=hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"}),
                                timeout_seconds=deadline_s)
    return result.response.get("envelope"), {"source_references": result.receipt["source_references"],
                                              "failure_kind": result.receipt["failure_kind"],
                                              "hybrid_code": result.receipt.get("code")}


async def run_llm_only(text: str, api_key: str) -> dict[str, Any]:
    from app.ai.pipeline import route_policy_snapshot, run_pipeline
    return await run_pipeline(text, api_key, route_policy=route_policy_snapshot({}))


def hybrid_transport(api_key: str, sleep=time.sleep):
    """The existing `function_calling.live_transport` (key in a header, `ApiBudget` before each send, usage recorded),
    with the SAME transient-retry policy and per-attempt timeout as `gemini.call_gemini`, so both arms get the same
    reliability treatment. Each retry is a new budgeted request."""
    import httpx

    from app.ai import gemini
    from app.ai.function_calling import ProviderHTTPError, live_transport

    send_once = live_transport(api_key, timeout_seconds=120.0)

    def send(request: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(gemini.MAX_ATTEMPTS):
            try:
                return send_once(request)
            except ProviderHTTPError as e:
                if e.status_code not in gemini.TRANSIENT_STATUS or attempt == gemini.MAX_ATTEMPTS - 1:
                    raise
                if gemini.BUDGET is not None:
                    gemini.BUDGET.note_transient()
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt == gemini.MAX_ATTEMPTS - 1:
                    raise
            sleep(gemini.BACKOFF_BASE_SECONDS * (2 ** attempt))
        raise AssertionError("unreachable")
    return send


# ── run ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--corpus", type=Path, required=True)
    p.add_argument("--out", type=Path)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--manifest", action="store_true", help="validate the corpus and print its hash; no run")
    p.add_argument("--approval-file", type=Path)
    a = p.parse_args(argv)
    if a.manifest:
        corpus = json.loads(a.corpus.read_text(encoding="utf-8"))
        validate_corpus(corpus)
        hits = contamination_scan(corpus)
        print(json.dumps({"corpus_sha256": sha256_file(a.corpus), "runtime_identity": runtime_identity(),
                          "contaminated_cases": hits}, ensure_ascii=False, indent=1))
        return 1 if hits else 0
    if a.out is None:
        p.error("--out is required for a run")
    approval = authorize_live(a.corpus, a.approval_file) if a.live else None
    out = evaluate(a.corpus, a.out, approval)
    print(json.dumps(out["summary"], ensure_ascii=False, indent=1, default=str))
    return 0


def evaluate(corpus_path: Path, out_path: Path, approval: dict[str, Any] | None, *, sleep=time.sleep) -> dict[str, Any]:
    """`approval is None` ⇒ dry run from recorded arm outputs; otherwise live under the approved terms. A stopped run is
    final and reported as such; the output file is never overwritten."""
    from app.ai import gemini
    from app.ai.telemetry import reset_usage, usage_report
    from app.ai.typed_fact_next_extraction import ReplayExtractor, TransportExtractor

    live = approval is not None
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    validate_corpus(corpus)
    identity = runtime_identity()
    budget = _cost_capped_budget(approval) if live else None
    gemini.set_budget(budget)
    undo_guard = _guard_sends(budget, approval) if live else (lambda: None)
    rows: list[dict[str, Any]] = []
    spent, technical_streak, stop_reason = 0.0, 0, None
    try:
        for case in corpus["cases"]:
            if live and runtime_identity() != identity:
                stop_reason = "IDENTITY_CHANGED"
                break
            for arm in ("HYBRID", "LLM_ONLY"):
                reset_usage()
                if budget is not None:
                    budget.start_arm(spent)
                start = time.perf_counter()
                extra: dict[str, Any] = {}
                envelope, technical = None, False
                try:
                    if not live:
                        if arm == "HYBRID":
                            rec = case["dry_run"]["hybrid_extraction"]
                            envelope, extra = run_hybrid(case["problem_text"], ReplayExtractor(
                                {case["problem_text"]: rec} if rec is not None else {}))
                        else:
                            envelope = case["dry_run"]["llm_only_envelope"]
                    elif arm == "HYBRID":
                        envelope, extra = run_hybrid(
                            case["problem_text"],
                            TransportExtractor(hybrid_transport(os.environ["GEMINI_API_KEY"], sleep=sleep)),
                            deadline_s=HYBRID_LIVE_DEADLINE_S)
                    else:
                        envelope = asyncio.run(run_llm_only(case["problem_text"], os.environ["GEMINI_API_KEY"]))
                    technical = extra.get("failure_kind") == "TECHNICAL_FAILURE"
                except gemini.BudgetExceeded:
                    technical = True
                except Exception as exc:  # noqa: BLE001 — recorded as infrastructure, never as a model/geometry result
                    technical, extra = True, {"exception": type(exc).__name__}
                usage = usage_report()
                upper = budget.arm_upper() if budget is not None else "UNKNOWN"
                row = {"case_id": case["id"], "arm": arm, "expect": case["expect"],
                       "latency_s": time.perf_counter() - start, "usage": usage or "UNKNOWN",
                       "requests_with_usage": sum(v.get("calls", 0) for v in usage.values()) if usage else "UNKNOWN",
                       "http_requests": (budget.http_requests - budget.arm_start_requests) if budget else 0,
                       "usd": usd(usage, approval), "usd_upper": upper, "technical_failure": technical,
                       **score(case, envelope), **extra}
                if technical:          # an infrastructure failure is never scored as a model or geometry outcome
                    row.update(false_refusal=False, refusal_reason_correct=False)
                rows.append(row)
                spent += upper if isinstance(upper, float) else 0.0
                technical_streak = technical_streak + 1 if technical else 0
                if budget is not None and budget.aborted:
                    stop_reason = budget.stop_reason or "REQUEST_CAP"   # TransportExtractor wraps BudgetExceeded
                elif row["served"] and case["expect"] != "SERVE":
                    stop_reason = "SERVED_EXPECTED_REFUSAL"
                elif live and spent >= 0.8 * approval["max_usd"]:
                    stop_reason = "USD_80_PERCENT"
                elif technical_streak >= 3:
                    stop_reason = "INFRASTRUCTURE_STREAK"
                if stop_reason:
                    break
            if stop_reason:
                break
    finally:
        undo_guard()
        gemini.set_budget(None)
    out = {"measurement_class": "PREREGISTERED_LIVE_PAIRED_EVALUATION" if live
           else "OFFLINE_DETERMINISTIC_FIXTURE_TEST",
           "corpus_sha256": sha256_file(corpus_path), "runtime_identity": identity, "stop_reason": stop_reason,
           "completed": stop_reason is None, "http_requests": budget.http_requests if budget else 0,
           "spent_upper_usd": spent if live else 0.0, "rows": rows, "summary": summarize(rows)}
    with out_path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)
        f.write("\n")
    return out


if __name__ == "__main__":
    raise SystemExit(main())
