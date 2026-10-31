# -*- coding: utf-8 -*-
"""Paired LLM_ONLY vs Hybrid evaluation harness — protocol: `docs/evaluation/geometry/runs/hybrid-master-backend-replacement/
live-evaluation-protocol.md` (pre-registered rules are cited as §n).

ONE scorer for both arms: the learner-visible target quantities of the served envelope (`scene3d` objects of type
`quantity` in display group `target`), keyed by producer kind, compared as EXACT numbers (`radical.from_json`, π kept)
against an oracle written with `radical.parse_exact` (e.g. "36π", "2√6/3") — never by model-chosen names.
Offline by default: `--dry-run` reads recorded arm outputs and proves only scoring, accounting and statistics
(MEASUREMENT_CLASS = OFFLINE_DETERMINISTIC_FIXTURE_TEST). `--live` refuses before any request unless ALLOW_LIVE_AI=1,
GEMINI_API_KEY and an Owner approval file bound to the corpus, measured-system and harness hashes and the caps; then every
HTTP request of BOTH arms first reserves the exact payload's provable ceiling in `CostCappedBudget`.

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/run_paired_route_evaluation.py \
        --corpus <corpus.json> --out <rows.jsonl> --dry-run          # or --manifest / --live --approval-file <owner.json>
"""
from __future__ import annotations

import argparse
import asyncio
import collections
import hashlib
import json
import math
import os
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

#: scene3d producer → oracle kind (§4). `measure.distance` covers lengths and distances.
KINDS = {"measure.distance": "distance", "measure.angle_cos_sq": "angle_cos_sq", "measure.angle_cos": "angle_cos",
         "measure.volume": "volume", "measure.area": "area", "measure.lateral_area": "lateral_area",
         "measure.radius": "radius", "assign.volume_ratio": "volume_ratio", "assign.residual_volume": "residual_volume"}
#: Pre-registered refusal classes (§2, §4). Not refusal classes, because LLM_ONLY serves them by design in production:
#: curved solids (served with π) and proof requests (`geometry_program_generator.md`: "Đề bảo CHỨNG MINH thì vẫn chỉ dựng
#: hình…"), which are out of this evaluation's scope altogether (§2).
REFUSAL_CLASSES = ("OUT_OF_DOMAIN", "CONTRADICTORY_DATA", "MISSING_DATA")
#: Hybrid outcomes that are not a model or geometry result (§4): transport/provider failures (an empty candidate list
#: included, as `call_gemini` raises on it for LLM_ONLY) and our own internal faults (LLM_ONLY's surface as exceptions,
#: Hybrid's are caught into these codes). Every other non-served outcome — a truncated or invalid model output
#: included — counts as "not served" in both arms (LLM_ONLY re-asks those and ends `geometry_generation_failed`).
HYBRID_INFRASTRUCTURE = {"PROVIDER_ERROR", "PROVIDER_BLOCKED", "PROVIDER_REFUSED", "LIVE_AI_DISABLED", "NO_CANDIDATE",
                         "HYBRID_DEADLINE_EXCEEDED", "HYBRID_CANCELLED", "EXTRACTOR_INTERNAL_ERROR",
                         "ROUTE_INTERNAL_ERROR", "ADAPTER_INTERNAL_ERROR"}
PROVIDER_BLOCK = {"PROVIDER_BLOCKED", "PROVIDER_REFUSED"}
ARM_ORDER_SEED = "hybrid-master-paired/2026-10-31"     # §3: per-case arm order, fixed before any corpus exists
PROMPT_FRAMING_RESERVE = 4096          # same conservative estimator as `run_hybrid_ab_pilot.reserve_payload`
MODEL_OUTPUT_LIMIT = 65536             # gemini-2.5-flash, thinking included (provider-facts.md, read 2026-10-31)
#: Hybrid's cooperative deadline in the live harness: all transport attempts × the per-attempt timeout. The offline
#: route's 15 s default was set for replay; a live extraction must not be cut short where LLM_ONLY is not.
HYBRID_LIVE_DEADLINE_S = 4 * 120.0
#: Offline-measured request payload sizes in characters (`live-evaluation-protocol.md` §3), excluding the problem text.
MEASURED_OVERHEAD_CHARS = {"hybrid_extraction": 8297, "llm_only_analyze": 11782, "llm_only_program": 13169}


class LiveRefused(RuntimeError):
    """The live path is not authorized or the corpus is invalid; raised BEFORE any request."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _norm(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).lower().split())


def parse_oracle(value: str):
    """Exact oracle values only: a string in the `radical.parse_exact` grammar. Decimals and non-strings are refused —
    an approximate oracle would score a correct exact answer as wrong-served."""
    from app.simulation.geometry.radical import parse_exact
    if not isinstance(value, str) or re.search(r"\d[.,]\d|[eE][-+]?\d", value):
        raise LiveRefused(f"oracle value {value!r} must be an exact string, not a decimal")
    x = parse_exact(value)
    if x is None:
        raise LiveRefused(f"oracle value {value!r} is not an exact number (radical.parse_exact grammar)")
    return x


# ── corpus and identity ──────────────────────────────────────────────────────────────────────────────────────────────

def validate_corpus(corpus: dict[str, Any]) -> None:
    """Refuse a corpus that cannot be scored fairly (§2): duplicate ids or (normalized) texts, an expected-serve case
    without an exact oracle over known kinds (construction-only problems are excluded), or an expected-refuse case
    without one pre-registered refusal class."""
    cases = corpus.get("cases")
    if not isinstance(cases, list) or not cases:
        raise LiveRefused("corpus has no cases")
    ids = [c.get("id") for c in cases]
    texts = [_norm(c["problem_text"]) for c in cases if isinstance(c.get("problem_text"), str)]
    if len(texts) != len(cases) or any(not t for t in texts):
        raise LiveRefused("every case needs a non-empty problem text")
    if len(set(ids)) != len(ids) or len(set(texts)) != len(texts):
        raise LiveRefused("duplicate case id or problem text")
    for c in cases:
        if c.get("expect") == "SERVE":
            oracle = c.get("oracle") or {}
            if not oracle or set(oracle) - set(KINDS.values()) or not all(oracle.values()):
                raise LiveRefused(f"{c['id']}: expected-serve case needs an oracle over {sorted(set(KINDS.values()))}")
            for values in oracle.values():
                [parse_oracle(v) for v in values]
        elif c.get("expect") == "REFUSE":
            if c.get("refusal_class") not in REFUSAL_CLASSES:
                raise LiveRefused(f"{c['id']}: expected-refuse case needs refusal_class in {REFUSAL_CLASSES}")
        else:
            raise LiveRefused(f"{c.get('id')}: expect must be SERVE or REFUSE")


#: Opened material a held-out text must not come from: the whole repository, minus build/vendor trees (§2).
_SKIP_DIRS = {".git", "node_modules", ".venv", "dist", "__pycache__", ".superpowers", ".playwright-mcp"}
_TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".py", ".ts", ".tsx", ".mjs", ".js", ".txt", ".html", ".csv"}
_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")


def contamination_scan(corpus: dict[str, Any], repo: Path = REPO, exclude: Path | None = None,
                       shingle: int = 8) -> dict[str, dict[str, list[str]]]:
    """`{case id: {"exact": [files], "near": [files sharing ≥ half of its 8-word shingles]}}` over the repository.
    Text is NFC-normalized, lower-cased, whitespace-collapsed, with `\\uXXXX` escapes decoded (JSON and source
    literals). LIMITS (stated, not hidden): a paraphrase, a changed number inside every shingle, or a literal split
    across source lines is NOT detected; independence still rests on the author."""
    exact = {c["id"]: _norm(c["problem_text"]) for c in corpus["cases"]}
    grams: dict[str, set[str]] = {}
    for cid, text in exact.items():
        words = text.split()
        grams[cid] = {" ".join(words[i:i + shingle]) for i in range(max(1, len(words) - shingle + 1))}
    hits: dict[str, dict[str, list[str]]] = {}
    for path in repo.rglob("*"):
        if (not path.is_file() or path.suffix not in _TEXT_SUFFIXES or _SKIP_DIRS & set(path.relative_to(repo).parts)
                or (exclude is not None and path.resolve() == exclude.resolve())):
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        haystack = _norm(_ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), raw))
        rel = path.relative_to(repo).as_posix()
        for cid, needle in exact.items():
            if needle in haystack:
                hits.setdefault(cid, {"exact": [], "near": []})["exact"].append(rel)
            elif sum(g in haystack for g in grams[cid]) * 2 >= len(grams[cid]):
                hits.setdefault(cid, {"exact": [], "near": []})["near"].append(rel)
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


# ── scoring (§4) ─────────────────────────────────────────────────────────────────────────────────────────────────────

def served_quantities(envelope: dict[str, Any] | None) -> dict[str, list]:
    """Target quantities the learner sees, by kind, as exact numbers (π kept). Unknown producers keep their own name
    so they can never satisfy an oracle kind; an unreadable exact form raises (→ SCORER_ERROR, never a guess)."""
    from app.simulation.geometry.radical import from_json
    out: dict[str, list] = {}
    for o in ((envelope or {}).get("scene3d") or {}).get("objects", []):
        if o.get("type") == "quantity" and "target" in (o.get("display_group") or []) and o.get("exact"):
            out.setdefault(KINDS.get(o.get("producer"), str(o.get("producer"))), []).append(from_json(o["exact"]))
    return out


def _contains(served: list, wanted: list) -> bool:
    left = collections.Counter(map(str, served))
    need = collections.Counter(map(str, wanted))
    return all(left[k] >= n for k, n in need.items())


def refusal_class(arm: str, envelope: dict[str, Any] | None, code: str | None) -> str:
    """Pre-registered arm → class map (§4). What an arm does not state is `UNSPECIFIC`, never a guess."""
    env = envelope or {}
    if env.get("failure_category") == "out_of_scope":
        return "OUT_OF_DOMAIN"
    if env.get("failure_category") == "not_simulation_suitable":       # in-domain text the product will not simulate
        return "NOT_SIMULATION_SUITABLE"
    if arm == "HYBRID" and code:
        from app.ai.hybrid_preview import classify_refusal
        return {"INVALID_DATA": "CONTRADICTORY_DATA",
                "MISSING_DATA": "MISSING_DATA"}.get(classify_refusal(code).group, "UNSPECIFIC")
    return "UNSPECIFIC"


def score(case: dict[str, Any], envelope: dict[str, Any] | None, arm: str = "HYBRID") -> dict[str, Any]:
    """Primary rule (§4): served-correct ⇔ served ∧ expected-serve ∧ for every asked kind the served target values are
    exactly the oracle's (each oracle value shown; no other value of that kind shown — a wrong value the learner sees
    is never "correct"). `served_correct_lenient` (oracle ⊆ shown) is reported as a sensitivity check only. Targets of
    kinds the oracle does not ask are reported as `unverified_extra_targets`; they are not scored (§4 limitation)."""
    served = bool(envelope) and envelope.get("status") == "ok" and bool((envelope.get("scene3d") or {}).get("objects"))
    got = served_quantities(envelope) if served else {}
    expect_serve = case["expect"] == "SERVE"
    oracle = {k: [parse_oracle(v) for v in vs] for k, vs in (case.get("oracle") or {}).items()}
    lenient = served and expect_serve and all(_contains(got.get(k, []), v) for k, v in oracle.items())
    extra = {k: [str(x) for x in got.get(k, []) if str(x) not in set(map(str, v))] for k, v in oracle.items()}
    extra = {k: v for k, v in extra.items() if v}
    correct = lenient and not extra
    code = (envelope or {}).get("error_code") or (envelope or {}).get("reason_code")
    klass = None if served else refusal_class(arm, envelope, code)
    return {"served": served, "served_correct": correct, "served_correct_lenient": lenient,
            "wrong_served": served and not correct, "false_refusal": expect_serve and not served,
            "refusal_reason_correct": not expect_serve and not served and klass == case.get("refusal_class"),
            "refusal_code": None if served else code, "refusal_class": klass, "extra_same_kind_values": extra,
            "unverified_extra_targets": {k: [str(x) for x in v] for k, v in got.items() if k not in oracle},
            "served_quantities": {k: [str(x) for x in v] for k, v in got.items()},
            "stage_reached": (envelope or {}).get("stage_reached")}


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float] | None:
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact binomial p-value on the discordant pairs (b: only arm 1 has it, c: only arm 2)."""
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
    """Denominators (§4): served-correct over expected-serve cases; wrong-served over all cases; technical failures
    count as not served-correct and are reported separately; refusals of negatives exclude technical failures."""
    out: dict[str, Any] = {}
    for arm in sorted({r["arm"] for r in rows}):
        rs = [r for r in rows if r["arm"] == arm]
        pos = [r for r in rs if r["expect"] == "SERVE"]
        neg = [r for r in rs if r["expect"] != "SERVE"]
        usd = [r["usd"] for r in rs]
        ok = sum(r["served_correct"] for r in rs)
        unknown = any(u == "UNKNOWN" for u in usd)
        out[arm] = {
            "n": len(rs), "expected_serve": len(pos), "served_correct": ok,
            "served_correct_ci95": wilson(ok, len(pos)),
            "served_correct_lenient": sum(r["served_correct_lenient"] for r in rs),
            "cases_with_unverified_extra_targets": sum(bool(r.get("unverified_extra_targets")) for r in rs),
            "wrong_served": sum(r["wrong_served"] for r in rs),
            "wrong_served_ci95": wilson(sum(r["wrong_served"] for r in rs), len(rs)),
            "false_refusal": sum(r["false_refusal"] for r in pos),
            "negatives": len(neg), "negatives_refused": sum(not r["served"] and not r["technical_failure"] for r in neg),
            "negatives_technical": sum(r["technical_failure"] for r in neg),
            "refusal_reason_correct": sum(r["refusal_reason_correct"] for r in neg),
            "technical_failures": sum(r["technical_failure"] for r in rs),
            "scorer_errors": sum(r.get("outcome") == "SCORER_ERROR" for r in rs),
            "repair_attempts": sum(r["repair_attempts"] for r in rs if isinstance(r["repair_attempts"], int)),
            "latency_median_s": _quantile([r["latency_s"] for r in rs], 0.5),
            "latency_p90_s": _quantile([r["latency_s"] for r in rs], 0.9),
            "usd_total": "UNKNOWN" if unknown else sum(usd),
            "usd_upper_total": sum(r["usd_upper"] for r in rs if isinstance(r["usd_upper"], float)),
            # §3 cost rule, the one criterion 5 reads: reported usage, plus every request sent without usage at its
            # ceiling; a 0-request row (the deterministic domain gate) costs a known 0.0 (review B1/M1)
            "usd_charged_total": (sum(r["usd_upper"] for r in rs)
                                  if all(isinstance(r["usd_upper"], (int, float)) for r in rs) else "UNKNOWN"),
            # lower bound: reported usage only (a request without usage, e.g. a retried 429, adds 0) — criterion 5
            # compares Hybrid's charged UPPER bound with the control's LOWER bound, so retry luck cannot pass it (N1)
            "usd_reported_total": sum(r["usd"] for r in rs if isinstance(r["usd"], (int, float))),
            "exercised": len(rs) - sum(r["technical_failure"] for r in rs),
            "usd_per_served_correct": "UNKNOWN" if unknown or not ok else sum(usd) / ok,
        }
    if rows:                   # always reported, so a run stopped inside its first arm still names its unpaired cases
        a, b = "HYBRID", "LLM_ONLY"
        by = {(r["case_id"], r["arm"]): r for r in rows}
        ids = sorted({i for i, _ in by if (i, a) in by and (i, b) in by})

        def disc(field):
            return (sum(by[i, a][field] and not by[i, b][field] for i in ids),
                    sum(by[i, b][field] and not by[i, a][field] for i in ids))

        (oa, ob), (wa, wb) = disc("served_correct"), disc("wrong_served")
        out["paired"] = {"arms": [a, b], "complete_pairs": len(ids), "paired_case_ids": ids,
                         "unpaired_cases": sorted({r["case_id"] for r in rows} - set(ids)),
                         f"served_correct_only_{a}": oa, f"served_correct_only_{b}": ob,
                         "served_correct_mcnemar_p": mcnemar_exact(oa, ob),
                         f"wrong_served_only_{a}": wa, f"wrong_served_only_{b}": wb,
                         "wrong_served_mcnemar_p": mcnemar_exact(wa, wb)}
    return out


#: §2 composition and §7 thresholds, fixed before any corpus exists (amendment A1 changes criterion 1 only).
COMPOSITION = {"SERVE": 45, "OUT_OF_DOMAIN": 5, "CONTRADICTORY_DATA": 5, "MISSING_DATA": 5}
ALPHA, MAX_SERVED_CORRECT_DROP, P90_FACTOR, MAX_TECHNICAL_RATE = 0.05, 0.05, 1.5, 0.05


def acceptance(corpus: dict[str, Any], record: dict[str, Any], approval: dict[str, Any] | None) -> dict[str, Any]:
    """§7 as code, applied once to a finished run record (`completed`, `stopped_arms`, `summary`). Each criterion is
    True, False, or None (not evaluable); only all-True is `HYBRID_CUTOVER_GO`. Criterion 1 (A1) is OBSERVED: Hybrid
    shows 0 wrong-served and no wrong-served the control does not also show. Its Wilson interval is reported as
    uncertainty and compared with nothing — 0/60 bounds the rate below ≈ 6 %, it does not show the rate is 0. A run
    that is incomplete or unpaired is never a GO; criterion 1 still decides a NO-GO on the rows it has."""
    s = record.get("summary") or {}
    h, l, p = s.get("HYBRID"), s.get("LLM_ONLY"), s.get("paired")
    cases = corpus.get("cases") or []
    got = collections.Counter("SERVE" if c.get("expect") == "SERVE" else c.get("refusal_class") for c in cases)
    complete = (bool(h and l and p) and record.get("completed") is True and record.get("stop_reason") is None
                and not record.get("stopped_arms") and h["n"] == l["n"] == p["complete_pairs"] == len(cases)
                and not p["unpaired_cases"] and set(p["paired_case_ids"]) == {x.get("id") for x in cases})
    c: dict[str, bool | None] = {
        "0_pre_registered_composition": dict(got) == COMPOSITION,
        "0_complete_paired_evaluation": complete,
        "1_hybrid_zero_wrong_served": h["wrong_served"] == 0 if h else None,
        "1_no_excess_wrong_served": p["wrong_served_only_HYBRID"] == 0 if p else None,
    }
    for key in ("2_served_correct_not_worse", "3_refusals", "4_latency", "5_usd_per_served_correct",
                "6_technical_and_scorer"):
        c[key] = None
    if complete:
        pos = h["expected_serve"]
        favours_llm = (p["served_correct_mcnemar_p"] < ALPHA
                       and p["served_correct_only_LLM_ONLY"] > p["served_correct_only_HYBRID"])
        c["2_served_correct_not_worse"] = (pos > 0 and not favours_llm
                                           and (h["served_correct"] - l["served_correct"]) / pos >= -MAX_SERVED_CORRECT_DROP)
        c["3_refusals"] = (h["negatives_refused"] == h["negatives"] - h["negatives_technical"]
                           and h["refusal_reason_correct"] >= l["refusal_reason_correct"])
        lat = (h["latency_median_s"], l["latency_median_s"], h["latency_p90_s"], l["latency_p90_s"])
        c["4_latency"] = None if None in lat else lat[0] <= lat[1] and lat[2] <= P90_FACTOR * lat[3]
        if h["usd_charged_total"] != "UNKNOWN" and h["served_correct"]:              # dry run or none correct ⇒ None
            llm = l["usd_reported_total"] / l["served_correct"] if l["served_correct"] else math.inf
            c["5_usd_per_served_correct"] = h["usd_charged_total"] / h["served_correct"] <= llm
        c["6_technical_and_scorer"] = all(a["technical_failures"] <= MAX_TECHNICAL_RATE * a["n"]
                                          and a["scorer_errors"] == 0 for a in (h, l))
    approval = approval or {}
    c["7_independence"] = (str(approval.get("corpus_author") or "").strip() != ""
                           and approval.get("authoring_independence") == "ESTABLISHED"
                           and approval.get("evaluator_independence") == "ESTABLISHED") or None
    failed = [k for k, v in c.items() if v is not True]
    flags = ["CONTROL_ARM_DEGENERATE"] if l and l["served_correct"] == 0 else []      # revision B m2: not a criterion
    return {"verdict": "HYBRID_CUTOVER_NO_GO" if failed else "HYBRID_CUTOVER_GO", "failed": failed, "criteria": c,
            "flags": flags,
            # over EXERCISED rows: a technical failure tested nothing, so it does not narrow the interval (review m3)
            "uncertainty": {f"{a}_wrong_served_ci95": wilson(s[a]["wrong_served"], s[a]["exercised"])
                            for a in ("HYBRID", "LLM_ONLY") if s.get(a)}}


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
    return check_approval_terms(corpus_path.read_bytes(), approval)


def check_approval_terms(corpus_bytes: bytes, approval: dict[str, Any]) -> dict[str, Any]:
    """The approved terms themselves, against the EXACT corpus bytes that will be run (tests exercise this directly —
    automation never writes an approval value)."""
    if approval.get("corpus_sha256") != sha256_bytes(corpus_bytes):
        raise LiveRefused("corpus hash differs from the approved one")
    for key in ("max_requests", "max_usd", "input_usd_per_million", "output_usd_per_million", "model",
                "llm_only_output_reservation_tokens", "measured_system", "harness_sha256",
                # criterion 7 fields must be stated (any value): a paid run without them is a silent certain NO-GO
                "corpus_author", "authoring_independence", "evaluator_independence"):
        if key not in approval:
            raise LiveRefused(f"approval lacks {key}")
    identity = runtime_identity()
    for key in ("model", "measured_system", "harness_sha256"):
        if approval[key] != identity[key]:
            raise LiveRefused(f"{key} differs from the approved one")
    if int(approval["llm_only_output_reservation_tokens"]) < MODEL_OUTPUT_LIMIT:
        raise LiveRefused("LLM_ONLY sets no output cap: the reservation must be at least the model output limit")
    corpus = json.loads(corpus_bytes.decode("utf-8"))
    validate_corpus(corpus)
    worst = worst_case_request_usd(corpus, approval)
    if approval["max_requests"] * worst > approval["max_usd"]:
        raise LiveRefused(f"max_requests × estimated request cost ({approval['max_requests']} × {worst:.4f} USD) "
                          f"exceeds max_usd {approval['max_usd']}")
    return approval


def worst_case_request_usd(corpus: dict[str, Any], approval: dict[str, Any]) -> float:
    """Planning ESTIMATE only (the enforced bound is `request_ceiling_usd` of each exact payload)."""
    from app.ai.function_calling import MAX_OUTPUT_TOKENS as HYBRID_OUTPUT_CAP

    longest = max(len(c["problem_text"]) for c in corpus["cases"])
    prompt = max(MEASURED_OVERHEAD_CHARS.values()) + 3 * longest + PROMPT_FRAMING_RESERVE
    output = max(HYBRID_OUTPUT_CAP, int(approval["llm_only_output_reservation_tokens"]))
    return prompt * approval["input_usd_per_million"] / 1e6 + output * approval["output_usd_per_million"] / 1e6


def request_ceiling_usd(payload: Any, approval: dict[str, Any]) -> float:
    """Ceiling of ONE request from the exact payload about to be sent: input tokens ≤ UTF-8 bytes of the whole request
    JSON (system instruction and schema included; byte-fallback tokenization — an assumption, stated in the protocol),
    output tokens ≤ the request's own `maxOutputTokens`, else the model limit (thinking included)."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    cap = ((payload or {}).get("generationConfig") or {}).get("maxOutputTokens") if isinstance(payload, dict) else None
    out = min(int(cap), MODEL_OUTPUT_LIMIT) if isinstance(cap, int) and cap > 0 else MODEL_OUTPUT_LIMIT
    return len(body) * approval["input_usd_per_million"] / 1e6 + out * approval["output_usd_per_million"] / 1e6


def usd(usage: dict[str, dict[str, int]], approval: dict[str, Any] | None) -> float | str:
    if approval is None or not usage:
        return "UNKNOWN"
    tin = sum(v.get("prompt_tokens", 0) for v in usage.values())
    tout = sum(v.get("candidates_tokens", 0) + v.get("thoughts_tokens", 0) for v in usage.values())
    return tin * approval["input_usd_per_million"] / 1e6 + tout * approval["output_usd_per_million"] / 1e6


def _cost_capped_budget(approval: dict[str, Any]):
    """`gemini.ApiBudget` (the request cap `call_gemini` and `live_transport` already honour) plus a USD guard applied to
    the EXACT payload right before it is sent (`reserve`, called by `_guard_sends`): spend of finished arms + this arm's
    reported usage + every sent request without reported usage at its own ceiling + the next request's ceiling must stay
    ≤ max_usd. Requests are sequential (one arm at a time, `run_pipeline` awaits each call)."""
    from app.ai import gemini
    from app.ai.telemetry import usage_report

    class CostCappedBudget(gemini.ApiBudget):
        def __init__(self) -> None:
            super().__init__(max_api_calls=int(approval["max_requests"]))
            self.spent_before_arm = 0.0
            self.arm_ceilings: list[float] = []
            self.arm_start_requests = 0
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
    """Wrap the only two send points in `app` (`httpx.post` of `live_transport`, `httpx.AsyncClient.post` of
    `call_gemini`) so every request reserves its exact ceiling first. Returns an undo function."""
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
    """The production opt-in path minus HTTP: the same domain gate as `/api/analyze` (`main._ngoai_pham_vi`), then
    `run_hybrid_offline`."""
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    from app.main import _ngoai_pham_vi

    out_of_scope = _ngoai_pham_vi(text)
    if out_of_scope is not None:
        return out_of_scope, {"hybrid_code": out_of_scope.get("error_code"), "source_references": []}
    result = run_hybrid_offline(text, extractor, policy=hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"}),
                                timeout_seconds=deadline_s)
    stages = {s["name"]: s for s in result.receipt["stages"]}
    return result.response.get("envelope"), {
        "source_references": result.receipt["source_references"], "hybrid_code": result.receipt.get("code"),
        "extraction_valid": "extraction" in stages and stages["extraction"]["code"] is None,
        "source_grounding": result.receipt["source_gate"]["status"]}


async def run_llm_only(text: str, api_key: str) -> dict[str, Any]:
    from app.ai.pipeline import route_policy_snapshot, run_pipeline
    return await run_pipeline(text, api_key, route_policy=route_policy_snapshot({}))


def hybrid_transport(api_key: str, sleep=time.sleep):
    """The existing `function_calling.live_transport` (key in a header, `ApiBudget` before each send, usage recorded),
    with the SAME transient-retry policy and per-attempt timeout as `gemini.call_gemini`."""
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


def arm_order(case_id: str) -> tuple[str, str]:
    first = int(hashlib.sha256(f"{ARM_ORDER_SEED}:{case_id}".encode()).hexdigest(), 16) % 2
    return ("HYBRID", "LLM_ONLY") if first == 0 else ("LLM_ONLY", "HYBRID")


# ── run ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--corpus", type=Path, required=True)
    p.add_argument("--out", type=Path)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--manifest", action="store_true", help="validate the corpus, scan for contamination; no run")
    p.add_argument("--approval-file", type=Path)
    a = p.parse_args(argv)
    if a.manifest:
        corpus = json.loads(a.corpus.read_text(encoding="utf-8"))
        validate_corpus(corpus)
        hits = contamination_scan(corpus, exclude=a.corpus)
        print(json.dumps({"corpus_sha256": sha256_file(a.corpus), "runtime_identity": runtime_identity(),
                          "contamination": hits}, ensure_ascii=False, indent=1))
        return 1 if any(h["exact"] for h in hits.values()) else 0
    if a.out is None:
        p.error("--out is required for a run")
    approval = authorize_live(a.corpus, a.approval_file) if a.live else None
    out = evaluate(a.corpus, a.out, approval)
    print(json.dumps(out["summary"], ensure_ascii=False, indent=1, default=str))
    return 0


def evaluate(corpus_path: Path, out_path: Path, approval: dict[str, Any] | None, *, sleep=time.sleep) -> dict[str, Any]:
    """`approval is None` ⇒ dry run from recorded arm outputs; otherwise live under the approved terms, re-checked here
    against the exact corpus bytes that are run. The JSONL output is created BEFORE the first request and every row is
    flushed as it completes, so a crash or a stop never loses a paid result; it is never overwritten."""
    from app.ai import gemini
    from app.ai.telemetry import reset_usage, usage_report
    from app.ai.typed_fact_next_extraction import ReplayExtractor, TransportExtractor

    live = approval is not None
    corpus_bytes = corpus_path.read_bytes()
    if live:
        check_approval_terms(corpus_bytes, approval)
    corpus = json.loads(corpus_bytes.decode("utf-8"))
    validate_corpus(corpus)
    identity = runtime_identity()
    sink = out_path.open("x", encoding="utf-8", newline="\n")

    def emit(record: dict[str, Any]) -> None:
        sink.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        sink.flush()

    emit({"type": "header", "measurement_class": "PREREGISTERED_LIVE_PAIRED_EVALUATION" if live
          else "OFFLINE_DETERMINISTIC_FIXTURE_TEST", "corpus_sha256": sha256_bytes(corpus_bytes),
          "runtime_identity": identity, "arm_order_seed": ARM_ORDER_SEED})
    budget = _cost_capped_budget(approval) if live else None
    gemini.set_budget(budget)
    undo_guard = _guard_sends(budget, approval) if live else (lambda: None)
    rows: list[dict[str, Any]] = []
    spent, technical_streak, stop_reason, stopped_arms = 0.0, 0, None, {}
    try:
        for case in corpus["cases"]:
            if live and runtime_identity() != identity:
                stop_reason = "IDENTITY_CHANGED"
                break
            for arm in arm_order(case["id"]):
                if arm in stopped_arms:
                    continue
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
                    technical = arm == "HYBRID" and extra.get("hybrid_code") in HYBRID_INFRASTRUCTURE
                except gemini.BudgetExceeded:
                    technical = True
                except Exception as exc:  # noqa: BLE001 — recorded as infrastructure, never as a model/geometry result
                    technical, extra = True, {"exception": type(exc).__name__}
                usage = usage_report()
                upper = budget.arm_upper() if budget is not None else "UNKNOWN"
                program_calls = (usage.get("semantic_program") or {}).get("calls") if usage else None
                row = {"type": "row", "case_id": case["id"], "arm": arm, "expect": case["expect"],
                       "latency_s": time.perf_counter() - start, "usage": usage or "UNKNOWN",
                       "requests_with_usage": sum(v.get("calls", 0) for v in usage.values()) if usage else "UNKNOWN",
                       "http_requests": (budget.http_requests - budget.arm_start_requests) if budget else 0,
                       "repair_attempts": 0 if arm == "HYBRID" else (max(0, program_calls - 1)
                                                                     if isinstance(program_calls, int) else "UNKNOWN"),
                       "usd": usd(usage, approval), "usd_upper": upper, "technical_failure": technical, **extra}
                try:
                    row.update(score(case, envelope, arm), outcome="SCORED")
                except Exception as exc:  # noqa: BLE001 — never lose a paid row to a scorer bug
                    row.update(served=False, served_correct=False, served_correct_lenient=False, wrong_served=False,
                               false_refusal=False, refusal_reason_correct=False, outcome="SCORER_ERROR",
                               scorer_error=type(exc).__name__)
                if technical:          # an infrastructure failure is never scored as a model or geometry outcome
                    row.update(false_refusal=False, refusal_reason_correct=False)
                rows.append(row)
                emit(row)
                spent += upper if isinstance(upper, float) else 0.0
                technical_streak = technical_streak + 1 if technical else 0
                if row["served"] and case["expect"] != "SERVE" and arm == "HYBRID":
                    # §5.1 (A2): Hybrid alone stops — criterion 1 has already failed. The control arm goes on, its
                    # wrong-serve recorded: stopping it would leave the pairs incomplete and make a GO unreachable.
                    stopped_arms[arm] = "SERVED_EXPECTED_REFUSAL"
                if budget is not None and budget.aborted:
                    stop_reason = budget.stop_reason or "REQUEST_CAP"       # TransportExtractor wraps BudgetExceeded
                elif extra.get("hybrid_code") in PROVIDER_BLOCK:
                    stop_reason = "PROVIDER_BLOCK"
                elif live and spent >= 0.8 * approval["max_usd"]:
                    stop_reason = "USD_80_PERCENT"
                elif technical_streak >= 3:
                    stop_reason = "INFRASTRUCTURE_STREAK"
                if stop_reason:
                    break
            if stop_reason:
                break
    except BaseException as exc:          # an interrupted run is reported as such, then the interruption propagates
        stop_reason = f"INTERRUPTED:{type(exc).__name__}"
        raise
    finally:
        undo_guard()
        gemini.set_budget(None)
        out = {"type": "summary", "stop_reason": stop_reason, "stopped_arms": stopped_arms,
               "completed": stop_reason is None and not stopped_arms,
               "http_requests": budget.http_requests if budget else 0, "spent_upper_usd": spent if live else 0.0,
               "summary": summarize(rows)}
        out["acceptance"] = acceptance(corpus, out, approval)
        emit(out)
        sink.close()
    return {**out, "measurement_class": "PREREGISTERED_LIVE_PAIRED_EVALUATION" if live
            else "OFFLINE_DETERMINISTIC_FIXTURE_TEST", "runtime_identity": identity, "rows": rows}


if __name__ == "__main__":
    raise SystemExit(main())
