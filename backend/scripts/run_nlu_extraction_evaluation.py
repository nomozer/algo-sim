# -*- coding: utf-8 -*-
"""Preregistered evaluation of Typed-Fact extraction (route D, branch B) — run `independent-nlu-extraction-evaluation`.

    raw Vietnamese text → fact_extraction.run_ai_fact_route (ONE provider call) → Typed Facts → run_fact_route
    (source grounding → planner → registry → engine) → scored per layer against the locked corpus/gold/oracle.

Modes (all but LIVE send 0 requests):
    GOLD    authored gold Typed Facts → deterministic route (the extraction-perfect ceiling)
    REPLAY  a fake provider returns the gold facts as a provider body → full harness/scorer path
    LIVE    real Gemini; only with ALLOW_LIVE_AI=1, GEMINI_API_KEY and an approval file matching the exact identity.
            The approval file is written by the human owner; no script, test or agent writes it.
    SCORE   re-score a recorded manifest against the recorded GOLD rows; PILOT adds the continuation gate,
            LOCKED adds the preregistered decision rule

Reuses the budget/redaction/persistence helpers of `run_hybrid_ab_pilot.py`; differs only in its loop: one arm,
no retries, a single failed request is recorded and the run continues; stop rules are STOP_HTTP, persistence failure,
secret, model version, caps and MAX_CONSECUTIVE_INFRA. Output files are never overwritten; resume re-sends nothing.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import time
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from scripts.run_hybrid_ab_pilot import (  # noqa: E402
    PilotBudget, PilotCaps, PilotStopped, _persist, _sha, _usage, canonical_json, redact, reserve_payload,
)

RUN = ROOT / "docs" / "evaluation" / "geometry" / "runs" / "independent-nlu-extraction-evaluation"
INPUTS = RUN / "inputs"
HELPERS = Path(__file__).resolve().with_name("run_hybrid_ab_pilot.py")
MODEL = "gemini-2.5-flash"
TIMEOUT_SECONDS = 90.0
MAX_CONSECUTIVE_INFRA = 3
#: End the run at once: retrying or continuing would only repeat an auth/quota/request failure (an invalid key is a 400).
STOP_HTTP = {400, 401, 403, 429}
MODES = {"PILOT": ("dev", 2), "LOCKED": ("locked", 1)}
GOLD_ONLY_KEYS = ("required", "alternatives", "rid")


def _lf_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest() if path.exists() else "ABSENT"


# ── locked inputs ────────────────────────────────────────────────────────────────────────────────────────────────
def load_inputs(inputs: Path = INPUTS) -> dict[str, Any]:
    protocol = json.loads((inputs / "protocol.json").read_text(encoding="utf-8"))
    corpus = json.loads((inputs / protocol.get("corpus_path", "corpus.json")).read_text(encoding="utf-8"))
    gold = json.loads((inputs / "gold_facts.json").read_text(encoding="utf-8"))
    locked = protocol["locked_sha256"]
    if _sha(corpus) != locked["corpus"] or _sha(gold) != locked["gold_facts"]:
        raise PilotStopped("INPUT_IDENTITY_MISMATCH")
    cases = {c["id"]: c for c in corpus["cases"]}
    if set(gold["cases"]) != set(cases):
        raise PilotStopped("GOLD_COVERAGE_MISMATCH")
    return {"corpus": corpus, "gold": gold, "protocol": protocol, "cases": cases, "dir": inputs}


def caps_for(protocol: dict[str, Any], mode: str) -> PilotCaps:
    return PilotCaps(**protocol["caps"][mode])


def schedule(inp: dict[str, Any], mode: str) -> list[dict[str, Any]]:
    split, samples = MODES[mode]
    return [{"case_id": c["id"], "sample": s} for c in inp["corpus"]["cases"] if c["split"] == split
            for s in range(1, samples + 1)]


def gold_payload(inp: dict[str, Any], case_id: str) -> dict[str, Any]:
    return {"facts": [{k: v for k, v in f.items() if k not in GOLD_ONLY_KEYS} for f in inp["gold"]["cases"][case_id]["facts"]]}


def identity(inp: dict[str, Any], mode: str) -> dict[str, Any]:
    from app.ai import fact_extraction as fx
    from scripts.freeze_evaluation_candidate import measured_system_hash
    product, _ = measured_system_hash()
    return {"mode": mode, "model": MODEL, "corpus_sha256": inp["protocol"]["locked_sha256"]["corpus"],
            "gold_sha256": inp["protocol"]["locked_sha256"]["gold_facts"], "protocol_sha256": _sha(inp["protocol"]),
            "preregistration_sha256": _lf_sha(Path(inp["dir"]).parent / "preregistration.md"),
            "surface_sha256": fx.surface_fingerprint(), "product_sha256": product,
            "runner_sha256": _lf_sha(Path(__file__).resolve()), "helpers_sha256": _lf_sha(HELPERS),
            "schedule_sha256": _sha(schedule(inp, mode)), "caps": asdict(caps_for(inp["protocol"], mode))}


# ── providers ────────────────────────────────────────────────────────────────────────────────────────────────────
class ReplayProvider:
    """Returns the authored gold facts as a well-formed provider body. Never live; usage counters are synthetic."""
    is_live = False

    def __init__(self, inp: dict[str, Any]):
        self.inp, self.current = inp, None

    def send(self, payload: dict[str, Any], timeout_seconds: float) -> dict[str, Any]:
        text = json.dumps(gold_payload(self.inp, self.current), ensure_ascii=False)
        return {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}],
                "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1, "totalTokenCount": 2},
                "modelVersion": MODEL, "responseId": f"replay-{self.current}"}


def live_provider(inp: dict[str, Any], mode: str, approval_file: Path | None) -> Any:
    """Network transport only after an explicit human approval naming this exact identity and mode."""
    if os.environ.get("ALLOW_LIVE_AI") != "1" or not os.environ.get("GEMINI_API_KEY") or approval_file is None:
        raise PilotStopped("LIVE_NOT_AUTHORIZED")
    approval = json.loads(Path(approval_file).read_bytes())
    if approval.get("decision") != "HUMAN_APPROVED_LIVE_EXECUTION" or approval.get("identities", {}).get(mode) != identity(inp, mode):
        raise PilotStopped("LIVE_NOT_AUTHORIZED")
    from app.ai.function_calling import live_transport

    class LiveProvider:
        is_live = True
        current = None

        def send(self, payload: dict[str, Any], timeout_seconds: float) -> dict[str, Any]:
            # Existing transport: key in header, ALLOW_LIVE_AI re-checked, one attempt, timeout owned here.
            return live_transport(os.environ["GEMINI_API_KEY"], model=MODEL, timeout_seconds=timeout_seconds)(payload)
    return LiveProvider()


def model_ok(version: Any) -> bool:
    """The locked model or a numbered pin of it (`gemini-2.5-flash-001`); never a sibling such as `-lite`."""
    return isinstance(version, str) and re.fullmatch(re.escape(MODEL) + r"(-\d{3})?", version) is not None


# ── execution ────────────────────────────────────────────────────────────────────────────────────────────────────
def _squared(v: Any) -> Fraction:
    from app.simulation.geometry.radical import Radical
    return Fraction(v.he) ** 2 * v.can if isinstance(v, Radical) else Fraction(v) ** 2


def route_record(r: Any) -> dict[str, Any]:
    """Status, code and every answered value as an exact rational: squared magnitude, or cos² when the route says so."""
    values = {}
    for qid, shown in r.answers.items():
        got = r.exec_result.final_memory.get(f"kq_{qid}") if r.exec_result is not None else None
        if got is not None:
            values[qid] = str(Fraction(got) if str(shown).startswith("cos²") else _squared(got))
    checks = ((r.planner or {}).get("goal_checks") or {}).values()
    return {"status": r.status, "code": r.code, "reason": r.reason, "answers": r.answers, "values": values,
            "has_scene3d": bool(r.scene3d), "planner_calls": len((r.planner or {}).get("calls") or []),
            "unproven_goals_flagged": sum(c.get("can_present_as_proven") is False for c in checks)}


def run_gold(inp: dict[str, Any]) -> list[dict[str, Any]]:
    from app.ai.function_route import run_fact_route
    rows = []
    for c in inp["corpus"]["cases"]:
        r = run_fact_route(c["source_text"], deepcopy(gold_payload(inp, c["id"])))
        rows.append({"case_id": c["id"], "sample": 0, "facts": gold_payload(inp, c["id"])["facts"],
                     "route": route_record(r), "infra": None})
    return rows


def run_eval(inp: dict[str, Any], mode: str, provider: Any, out_dir: Path, *, resume: bool = False,
             secrets: tuple[str, ...] = ()) -> dict[str, Any]:
    from app.ai import fact_extraction as fx
    from app.ai.function_calling import ProviderHTTPError
    live = bool(getattr(provider, "is_live", False))
    out_dir, limits, ident, planned = Path(out_dir).resolve(), caps_for(inp["protocol"], mode), identity(inp, mode), schedule(inp, mode)
    path = out_dir / "manifest.json"
    if path.exists():
        if not resume:
            raise PilotStopped("OUTPUT_EXISTS")
        state = json.loads(path.read_bytes())
        if state.get("identity") != ident or state.get("execution_class") != ("LIVE" if live else "FAKE"):
            raise PilotStopped("IDENTITY_MISMATCH")
        if state.get("pending") is not None:
            raise PilotStopped("REQUEST_STATE_UNKNOWN")
        if state.get("rows_sha256") != _sha(state["rows"]):
            raise PilotStopped("PARTIAL_ARTIFACT")
        if state["stop_reason"] is not None or len(state["rows"]) == len(planned):
            return state
    else:
        if out_dir.exists() and any(out_dir.iterdir()):
            raise PilotStopped("PARTIAL_ARTIFACT")
        out_dir.mkdir(parents=True, exist_ok=True)
        state = {"schema": "nlu_extraction_eval/1", "identity": ident, "execution_class": "LIVE" if live else "FAKE",
                 "rows": [], "rows_sha256": _sha([]), "pending": None, "stop_reason": None,
                 "budget": asdict(PilotBudget()), "live_model_calls": 0, "consecutive_infra": 0}
        _persist(path, state, secrets)
    budget = PilotBudget(**state["budget"])
    for position in range(len(state["rows"]), len(planned)):
        call = planned[position]
        case = inp["cases"][call["case_id"]]
        provider.current = call["case_id"]
        rec: dict[str, Any] = {**call, "position": position, "raw_response": None, "usage": None, "model_version": None,
                               "response_id": None, "finish_reason": None, "latency_seconds": None, "http_status": None,
                               "infra": None, "facts": None, "parse_code": None, "route": None}
        stop: str | None = None

        def transport(payload: dict[str, Any]) -> Any:
            nonlocal stop
            reservation = reserve_payload(payload, payload["generationConfig"]["maxOutputTokens"])
            rec.update(payload_sha256=_sha(payload), reservation=reservation)
            try:
                budget.reserve(reservation, limits)
                state.update(pending={"position": position, "payload_sha256": rec["payload_sha256"]}, budget=asdict(budget))
                _persist(path, state, secrets)
            except PilotStopped as e:   # cap or PERSISTENCE_FAILED: nothing was sent
                stop = str(e)
                raise
            if live:
                state["live_model_calls"] += 1
            t0 = time.perf_counter()
            try:
                body = provider.send(payload, TIMEOUT_SECONDS)
            except ProviderHTTPError as e:
                rec["http_status"], body = e.status_code, e.body
            except Exception as e:  # noqa: BLE001 — timeout/transport: recorded, never retried
                name = type(e).__name__
                rec["infra"] = "TIMEOUT" if "Timeout" in name else "LIVE_AI_DISABLED" if name == "LiveAIDisabled" else "PROVIDER_ERROR"
                if rec["infra"] == "LIVE_AI_DISABLED":
                    stop = rec["infra"]
                raise
            finally:
                rec["latency_seconds"] = round(time.perf_counter() - t0, 3)
            clean, leaked = redact(body, secrets)
            rec["raw_response"] = clean
            if leaked:
                stop = "SECRET_DETECTED"
                raise PilotStopped(stop)
            if rec["http_status"] is not None:
                rec["infra"] = f"HTTP_{rec['http_status']}"
                if rec["http_status"] in STOP_HTTP:
                    stop = rec["infra"]
                raise PilotStopped(rec["infra"])
            try:
                rec["usage"] = _usage(body, reservation)
            except PilotStopped as e:
                rec["usage"] = None if str(e) == "USAGE_UNKNOWN" else _usage(body, reservation, enforce_reservation=False)
                rec["usage_flag"] = str(e)
            rec["model_version"], rec["response_id"] = body.get("modelVersion"), body.get("responseId")
            if not model_ok(rec["model_version"]):
                stop = "MODEL_VERSION_MISMATCH"
                raise PilotStopped(stop)
            cands = body.get("candidates") or [{}]
            rec["finish_reason"] = cands[0].get("finishReason") if isinstance(cands[0], dict) else None
            return body

        try:
            r = fx.run_ai_fact_route(case["source_text"], transport)
        except Exception:  # noqa: BLE001 — adapter catches transport errors; anything else is a harness failure
            stop = stop or "POST_RESPONSE_FAILURE"
            r = None
        if stop in {"LOGICAL_CAP", "HTTP_CAP", "TOKEN_CAP", "USD_CAP", "CONTEXT_CAP", "PERSISTENCE_FAILED"}:
            state.update(stop_reason=stop, pending=None)   # pre-send stop: no request, no fabricated row
            try:
                _persist(path, state, secrets)
            except PilotStopped:
                pass
            break
        if stop and rec["infra"] is None:
            rec["infra"] = stop
        if r is not None:
            if r.code in {"PROVIDER_ERROR", "LIVE_AI_DISABLED"} and rec["infra"] is None:
                rec["infra"] = r.code
            rec["route"] = route_record(r)
            if rec["raw_response"] is not None and rec["infra"] is None:
                try:
                    rec["facts"] = fx.parse_response(rec["raw_response"], {}).get("facts")
                except Exception as e:  # noqa: BLE001 — the route already carries the refusal code
                    rec["parse_code"] = getattr(e, "code", type(e).__name__)
        state["consecutive_infra"] = state["consecutive_infra"] + 1 if rec["infra"] else 0
        if not stop and state["consecutive_infra"] >= MAX_CONSECUTIVE_INFRA:
            stop = "CONSECUTIVE_INFRA_ERRORS"
        rec, leaked = redact(json.loads(json.dumps(rec, ensure_ascii=False, default=str)), secrets)
        if leaked:
            stop = "SECRET_DETECTED"
        state["rows"].append(rec)
        state.update(pending=None, stop_reason=stop, budget=asdict(budget), rows_sha256=_sha(state["rows"]))
        _persist(path, state, secrets)
        if stop:
            break
    return state


# ── scoring (preregistered; reads only the locked inputs and the recorded rows) ──────────────────────────────────────
def _norm(s: Any) -> str:
    """The product's own source normaliser (NFC, primes, whitespace), so grounding is judged as the route judges it."""
    from app.simulation.geometry_functions.registry import chuan_hoa
    return chuan_hoa(str(s))


def _labels(v: Any) -> tuple | None:
    # ponytail: vertex order is ignored (a crossed ACBD matches square ABCD); order-sensitive shapes are not scored here
    if v is None:
        return None
    return tuple(sorted(_norm(x) for x in (v if isinstance(v, list) else [v])))


def _num(v: Any) -> Any:
    if v is None:
        return None
    s = _norm(v).replace(" ", "")
    try:
        return str(Fraction(s))
    except (ValueError, ZeroDivisionError):
        return s


SYMMETRIC = {"perpendicular", "equal_lengths", "intersection_line"}
SCALAR = ("kind", "role", "quantity", "point", "at", "point_kind", "measure", "solid_type", "shape", "plane_relation")


def _sig(f: dict[str, Any], by_id: dict[str, Any], depth: int = 0) -> dict[str, Any]:
    """Content of a fact without id/quotes/ambiguous/reason. Plane operands (≥ 3 labels) compare by containment."""
    s = {k: (_norm(f[k]) if isinstance(f.get(k), (str, int)) and k in ("point", "at") else f.get(k)) for k in SCALAR}
    s.update(negated=bool(f.get("negated")), regular=bool(f.get("regular")), right=bool(f.get("right")),
             value=_num(f.get("value")), points=_labels(f.get("points")),
             a=_labels(f.get("points_a")), b=_labels(f.get("points_b")),
             solid=_norm(f["solid"]).replace(" ", "") if f.get("solid") is not None else None)
    if f.get("kind") == "question" and f.get("quantity") == "area" and s["points"]:
        s["solid"] = None    # the planner's triangle-area ask ignores `solid`; only section area needs it
    ref = f.get("line_ref")
    s["ref"] = _sig(by_id[ref], by_id, depth + 1) if ref is not None and depth < 2 and ref in by_id else ref
    return s


def _plane_ok(x: Any, y: Any) -> bool:
    if x == y:
        return True
    if isinstance(x, tuple) and isinstance(y, tuple) and min(len(x), len(y)) >= 3:
        return set(x) <= set(y) or set(y) <= set(x)
    return False


def _same(g: dict[str, Any], l: dict[str, Any]) -> bool:
    if any(g[k] != l[k] for k in (*SCALAR, "negated", "regular", "right", "value", "solid")):
        return False
    pts_plane = g["kind"] in ("projection", "section")
    if not (_plane_ok(g["points"], l["points"]) if pts_plane else g["points"] == l["points"]):
        return False
    if not ((g["ref"] == l["ref"]) or (isinstance(g["ref"], dict) and isinstance(l["ref"], dict) and _same(g["ref"], l["ref"]))):
        return False
    pairs = [(l["a"], l["b"])]
    if g["kind"] in SYMMETRIC or g["quantity"] in ("distance", "angle"):
        pairs.append((l["b"], l["a"]))
    return any(_plane_ok(g["a"], a) and _plane_ok(g["b"], b) for a, b in pairs)


def _spans(quotes: Any, src: str) -> list[tuple[int, int]]:
    out = []
    for q in quotes if isinstance(quotes, list) else []:
        q = _norm(q)
        i = src.find(q) if q else -1
        if i >= 0:
            out.append((i, i + len(q)))
    return out


def _overlap(a: list, b: list) -> bool:
    return any(x0 < y1 and y0 < x1 for x0, x1 in a for y0, y1 in b)


def _matches(g: dict[str, Any], l: dict[str, Any], gid: dict, lid: dict, src: str) -> bool:
    if g["kind"] == "unsupported" or l.get("kind") == "unsupported":
        # Content-free facts: same kind and role, and the quoted source region must overlap.
        return (g["kind"] == l.get("kind") and g["role"] == l.get("role")
                and _overlap(_spans(g["quotes"], src), _spans(l.get("quotes"), src)))
    cands = [g] + [{**g, **alt} for alt in g.get("alternatives") or ()]
    ls = _sig(l, lid)
    return any(_same(_sig(c, gid), ls) for c in cands)


def _segment_lengths(facts: list[dict[str, Any]]) -> dict[frozenset, str]:
    """Named-segment lengths closed under equal_lengths: `AB = AC = 2` as two lengths or as equal_lengths + one length."""
    val: dict[frozenset, str] = {}
    eq: list[tuple[frozenset, frozenset]] = []
    for f in facts:
        if f.get("role") != "premise" or f.get("negated"):
            continue
        if f.get("kind") == "length" and f.get("measure") == "segment" and isinstance(f.get("points"), list) and len(f["points"]) == 2:
            val[frozenset(_labels(f["points"]))] = _num(f.get("value"))
        elif f.get("kind") == "equal_lengths" and isinstance(f.get("points_a"), list) and isinstance(f.get("points_b"), list):
            eq.append((frozenset(_labels(f["points_a"])), frozenset(_labels(f["points_b"]))))
    for _ in range(len(eq) + 1):
        for x, y in eq:
            if x in val and y not in val:
                val[y] = val[x]
            elif y in val and x not in val:
                val[x] = val[y]
    return val


def _is_seglen(f: dict[str, Any]) -> bool:
    return (f.get("role") == "premise" and not f.get("negated")
            and ((f.get("kind") == "length" and f.get("measure") == "segment") or f.get("kind") == "equal_lengths"))


def match_facts(gold: list[dict[str, Any]], live: list[Any], src: str) -> dict[str, Any]:
    """One-to-one greedy match of gold facts to live facts; named-segment lengths compare as a closed set."""
    live_d = [f for f in live if isinstance(f, dict)]
    gid = {f["id"]: f for f in gold}
    lid = {f.get("id"): f for f in live_d}
    gl, ll = _segment_lengths(gold), _segment_lengths(live_d)
    used, pairs, sat = set(), {}, set()
    for g in gold:
        if _is_seglen(g) and g["kind"] == "length" and ll.get(frozenset(_labels(g["points"]))) == _num(g.get("value")):
            sat.add(g["id"])
            continue
        for i, l in enumerate(live_d):
            if i not in used and not _is_seglen(l) and _matches(g, l, gid, lid, src):
                used.add(i)
                pairs[g["id"]] = i
                sat.add(g["id"])
                break
    consistent = set()
    for i, l in enumerate(live_d):
        if i in used or not _is_seglen(l):
            continue
        if l["kind"] == "length":
            ok = gl.get(frozenset(_labels(l.get("points")))) == _num(l.get("value"))
        else:
            x, y = frozenset(_labels(l.get("points_a"))), frozenset(_labels(l.get("points_b")))
            ok = x in gl and y in gl and gl[x] == gl[y]
        if ok:
            consistent.add(i)
    return {"pairs": pairs, "satisfied": sat, "live": live_d, "matched_live": used | consistent}


REFUSE_DISPOSITIONS = {"refuse_contradictory", "refuse_missing_info", "refuse_nonexistent_object", "refuse_ambiguous",
                       "clarification_required", "out_of_scope_request"}
REQUEST_ROLES = ("question", "prove")
UNSAFE = {"WRONG_SERVED", "PARTIAL_SERVED", "OVER_SERVED"}
SERVED_OK = {"CORRECT_COMPLETE", "CORRECT_PART_FLAGGED", "CORRECT_VALUE_COS2_FORM", "CONSTRUCTION_SERVED"}


def effective_disposition(case: dict[str, Any]) -> str:
    """The harness sends only the current turn (the product is single-turn): a case whose meaning needs its prior
    context cannot be answered from what is sent, so refusing/asking is the correct behaviour (CONTEXT_NOT_SENT)."""
    return "clarification_required" if case.get("context") else case["gold_disposition"]


def _oracle(ev: dict[str, Any]) -> Fraction | None:
    s = ev.get("cos_squared") or ev.get("value_squared")
    if s is None:
        return None
    s = re.sub(r"a(\^\d+|[²³⁴⁶])?", "", str(s)).replace("*", "").replace(" ", "")   # layout uses a = 1
    return Fraction("1" + s if s.startswith("/") or not s else s)


def extraction(case: dict[str, Any], gold: dict[str, Any], live: list[Any]) -> dict[str, Any]:
    src = _norm(case["source_text"])
    gf = gold["facts"]
    m = match_facts(gf, live, src)
    L = m["live"]
    q_gold = [g for g in gf if g["role"] in REQUEST_ROLES]
    p_gold = [g for g in gf if g["role"] not in REQUEST_ROLES and g.get("required", True)]
    q_live = [i for i, f in enumerate(L) if f.get("role") in REQUEST_ROLES]
    p_live = [i for i, f in enumerate(L) if f.get("role") not in REQUEST_ROLES]
    free, intent = set(q_live), 0
    for g in q_gold:   # one-to-one: one live request cannot satisfy two gold intents
        hit = next((i for i in sorted(free) if (L[i].get("role"), L[i].get("kind"), L[i].get("quantity"))
                    == (g["role"], g["kind"], g.get("quantity"))), None)
        if hit is not None:
            free.discard(hit)
            intent += 1
    q_expr = [g for g in q_gold if g["kind"] != "unsupported"]
    gaps = [g for g in q_gold if g["kind"] == "unsupported"]
    extra_q = [i for i in q_live if i not in m["matched_live"]]
    extra_p = [i for i in p_live if i not in m["matched_live"]]
    ungrounded = sum(not _spans(f.get("quotes"), src) or len(_spans(f.get("quotes"), src)) < len(f.get("quotes") or [None])
                     for f in L)
    approximated = sum(any(i not in m["matched_live"] and L[i].get("kind") != "unsupported"
                           and _overlap(_spans(g["quotes"], src), _spans(L[i].get("quotes"), src)) for i in q_live)
                       for g in gaps)
    ext = {"parse_ok": True, "n_live": len(L), "non_dict_facts": len(live) - len(L),
           "requests_gold": len(q_gold), "intent_match": intent,
           "goal_match": sum(g["id"] in m["pairs"] for g in q_gold),
           "requests_expressible": len(q_expr), "goal_match_expressible": sum(g["id"] in m["pairs"] for g in q_expr),
           "premises_required": len(p_gold), "premise_match": sum(g["id"] in m["satisfied"] for g in p_gold),
           "premises_live": len(p_live), "premise_live_matched": sum(i in m["matched_live"] for i in p_live),
           "extra_questions": len(extra_q), "extra_premises": len(extra_p), "ungrounded_quote_facts": ungrounded,
           "ambiguous_flags": sum(bool(f.get("ambiguous")) for f in L),
           "schema_gap_requests": len(gaps), "schema_gap_flagged": sum(g["id"] in m["pairs"] for g in gaps),
           "schema_gap_approximated": approximated}
    ext["complete_goals"] = ext["goal_match"] == len(q_gold) and not extra_q
    ext["correct"] = (ext["complete_goals"] and ext["premise_match"] == len(p_gold) and not extra_p and not ungrounded
                      and not ext["ambiguous_flags"] and not ext["non_dict_facts"])
    ext["pairs"] = {g: L[i].get("id") for g, i in m["pairs"].items()}
    return ext


def classify_e2e(case: dict[str, Any], gold: dict[str, Any], row: dict[str, Any], gold_row: dict[str, Any] | None,
                 ext: dict[str, Any]) -> str:
    rt, disp = row["route"], effective_disposition(case)
    if rt["status"] != "SERVED":
        if not ext.get("parse_ok"):
            return "NO_PARSE"
        if disp in REFUSE_DISPOSITIONS:
            return "SAFE_REFUSAL"
        if gold_row is None:
            raise ValueError("scoring a refusal needs the recorded GOLD rows")
        if gold_row["route"]["status"] != "SERVED":
            return "FALSE_REFUSAL_CAPABILITY_GAP"
        return "FALSE_REFUSAL_GROUNDING" if ext.get("correct") else "FALSE_REFUSAL_EXTRACTION"
    if disp in REFUSE_DISPOSITIONS:
        return "WRONG_SERVED"
    by_rid = {g["rid"]: g["id"] for g in gold["facts"] if g.get("rid")}
    wanted = {rid: _oracle(ev) for rid, ev in (case.get("expected_values") or {}).items()}
    mapped = {ext["pairs"].get(by_rid.get(rid)) for rid in wanted} - {None}
    missing = 0
    for rid, want in wanted.items():
        qid = ext["pairs"].get(by_rid.get(rid, ""))
        got = rt["values"].get(qid) if qid else None
        if got is None:
            missing += 1
        elif want is not None and Fraction(got) != want:
            return "WRONG_SERVED"
    unasked = [q for q in rt["answers"] if q not in mapped]
    if unasked:
        return "WRONG_SERVED" if missing else "OVER_SERVED"   # answered another question, or an extra one
    if not wanted:
        return "CONSTRUCTION_SERVED"
    if missing:
        return "PARTIAL_SERVED"
    if disp == "answer_supported_part_and_flag_rest":
        # The unsupported part (a proof) must be visibly marked as not proven, not silently passed as done.
        return "CORRECT_PART_FLAGGED" if rt.get("unproven_goals_flagged") else "PARTIAL_SERVED"
    if gold.get("asks_degrees"):
        return "CORRECT_VALUE_COS2_FORM"   # value right, but shown as cos² while the wording asks for degrees
    return "CORRECT_COMPLETE"


def score_row(case: dict[str, Any], gold: dict[str, Any], row: dict[str, Any], gold_row: dict[str, Any] | None) -> dict[str, Any]:
    """Per-layer classification of one execution row; the required outcome cells are `cell`."""
    if row.get("infra"):
        return {"e2e": "PROVIDER_OR_HARNESS_ERROR", "extraction": None, "cell": None}
    live = row.get("facts")
    ext = extraction(case, gold, live) if isinstance(live, list) else {"parse_ok": False}
    e2e = classify_e2e(case, gold, row, gold_row, ext)
    cell = None
    if ext.get("parse_ok"):
        ok = ext["correct"]
        cell = ("LLM_CORRECT_SERVED_CORRECT" if ok and e2e in SERVED_OK else
                "LLM_CORRECT_SAFE_REFUSAL" if ok and e2e == "SAFE_REFUSAL" else
                "LLM_CORRECT_PIPELINE_UNSUPPORTED" if ok and e2e.startswith("FALSE_REFUSAL") else
                "LLM_CORRECT_UNSAFE_SERVED" if ok else
                "LLM_WRONG_UNSAFE_ACCEPTED" if e2e in UNSAFE else
                "LLM_WRONG_REFUSED" if row["route"]["status"] != "SERVED" else "LLM_WRONG_BENIGN_SERVED")
    return {"e2e": e2e, "extraction": ext, "cell": cell}


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact binomial interval by bisection on the CDF (stdlib only)."""
    if n == 0:
        return (0.0, 1.0)
    cdf = lambda p, x: sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(x + 1))

    def solve(f):
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if f(mid) else (lo, mid)
        return (lo + hi) / 2
    lower = 0.0 if k == 0 else solve(lambda p: 1 - cdf(p, k - 1) < alpha / 2)
    upper = 1.0 if k == n else solve(lambda p: cdf(p, k) > alpha / 2)
    return (round(lower, 4), round(upper, 4))


def summarize(inp: dict[str, Any], rows: list[dict[str, Any]], gold_rows: list[dict[str, Any]]) -> dict[str, Any]:
    g_by = {r["case_id"]: r for r in gold_rows}
    scored = [{**score_row(inp["cases"][r["case_id"]], inp["gold"]["cases"][r["case_id"]], r, g_by.get(r["case_id"])),
               "case_id": r["case_id"], "sample": r["sample"]} for r in rows]
    exts = [s["extraction"] for s in scored if s["extraction"] and s["extraction"].get("parse_ok")]
    tot = lambda k: sum(e[k] for e in exts)
    frac = lambda a, b: f"{a}/{b}"
    usage = [r["usage"] for r in rows if r.get("usage")]
    by_structure: dict[str, list[str]] = {}
    for s in scored:
        by_structure.setdefault(inp["cases"][s["case_id"]]["structure_id"], []).append(s["e2e"])
    return {
        "rows": len(rows), "e2e": dict(Counter(s["e2e"] for s in scored)),
        "e2e_by_group": {g: dict(Counter(s["e2e"] for s in scored if inp["cases"][s["case_id"]]["group"] == g))
                         for g in sorted({c["group"] for c in inp["cases"].values()})},
        "cells": dict(Counter(s["cell"] for s in scored if s["cell"])),
        "refusal_codes": dict(Counter(r["route"]["code"] for r in rows if r.get("route") and r["route"]["status"] != "SERVED")),
        "always_refuse_baseline": sum(effective_disposition(inp["cases"][r["case_id"]]) in REFUSE_DISPOSITIONS for r in rows),
        "structures": len(by_structure),
        "extraction": {"parsed": frac(len(exts), len(rows)),
                       "intent": frac(tot("intent_match"), tot("requests_gold")),
                       "goal_entity": frac(tot("goal_match"), tot("requests_gold")),
                       "goal_entity_expressible": frac(tot("goal_match_expressible"), tot("requests_expressible")),
                       "premise_recall": frac(tot("premise_match"), tot("premises_required")),
                       "premise_precision": frac(tot("premise_live_matched"), tot("premises_live")),
                       "multi_goal_complete": frac(sum(e["complete_goals"] for e in exts if e["requests_gold"] >= 2),
                                                   sum(e["requests_gold"] >= 2 for e in exts)),
                       "extra_questions": tot("extra_questions"), "unmatched_premises": tot("extra_premises"),
                       "ungrounded_quote_facts": tot("ungrounded_quote_facts"), "ambiguous_flags": tot("ambiguous_flags"),
                       "schema_gap_flagged": frac(tot("schema_gap_flagged"), tot("schema_gap_requests")),
                       "schema_gap_approximated": tot("schema_gap_approximated"),
                       "extraction_correct": frac(sum(e["correct"] for e in exts), len(exts))},
        "usage": {"rows_with_usage": len(usage), "input_tokens": sum(u["input_tokens"] for u in usage),
                  "output_tokens": sum(u["output_tokens"] for u in usage),
                  "thinking_tokens": sum(u["thinking_tokens"] for u in usage),
                  "usd_estimated_list_price": round(sum(u["usd"] for u in usage), 6),
                  "latency_seconds": sorted(r["latency_seconds"] for r in rows if r.get("latency_seconds") is not None)},
        "scored": scored,
    }


def pilot_gate(state: dict[str, Any], summary: dict[str, Any], planned: int) -> dict[str, Any]:
    """The preregistered continuation criteria, mechanically (denominator = the planned 32 rows)."""
    rows = state["rows"]
    parsed = sum(isinstance(r.get("facts"), list) for r in rows)
    truncated = sum((r.get("route") or {}).get("code") == "RESPONSE_TRUNCATED" for r in rows)
    answered = [r for r in rows if r.get("raw_response") is not None and not r.get("http_status") and not r.get("infra")]
    crit = {"no_stop_rule_fired": state["stop_reason"] is None and len(rows) == planned,
            "parse_ok_at_least_28_of_32": parsed >= 28, "truncated_at_most_2": truncated <= 2,
            "usage_present_on_every_answered_row": all(r.get("usage") for r in answered)}
    return {"criteria": crit, "parsed": parsed, "truncated": truncated, "planned": planned,
            "verdict": "CONTINUE_TO_LOCKED" if all(crit.values()) else "STOP"}


def decide(summary: dict[str, Any]) -> dict[str, Any]:
    """Preregistered decision on LOCKED. P1 safety: no unsafe acceptance. P2: goal/entity agreement on expressible
    requests — YES if point ≥ 0.85 and exact 95 % lower bound ≥ 0.70; NO if the upper bound < 0.85; else INCONCLUSIVE."""
    unsafe = sum(v for k, v in summary["e2e"].items() if k in UNSAFE)
    k, n = (int(x) for x in summary["extraction"]["goal_entity_expressible"].split("/"))
    lo, hi = clopper_pearson(k, n)
    p2 = "YES" if n and k / n >= 0.85 and lo >= 0.70 else "NO" if hi < 0.85 else "INCONCLUSIVE"
    kc, nc = (int(x) for x in summary["extraction"]["extraction_correct"].split("/"))
    return {"P1_unsafe_rows": unsafe, "P1": "PASS" if unsafe == 0 else "FAIL",
            "P1_unsafe_rate_upper_95": clopper_pearson(unsafe, summary["rows"])[1],
            "P2_goal_entity_expressible": f"{k}/{n}", "P2_ci95": [lo, hi], "P2": p2,
            "case_extraction_correct": f"{kc}/{nc}", "case_extraction_correct_ci95": list(clopper_pearson(kc, nc)),
            "answer": ("UNSAFE" if unsafe else "YES_ON_THIS_CORPUS" if p2 == "YES" else "NO" if p2 == "NO" else "INCONCLUSIVE")}


def score_manifest(inp: dict[str, Any], manifest: dict[str, Any], gold_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if manifest.get("rows_sha256") != _sha(manifest["rows"]):
        raise PilotStopped("PARTIAL_ARTIFACT")
    ident = manifest["identity"]
    if (ident["corpus_sha256"], ident["gold_sha256"]) != (inp["protocol"]["locked_sha256"]["corpus"],
                                                        inp["protocol"]["locked_sha256"]["gold_facts"]):
        raise PilotStopped("INPUT_IDENTITY_MISMATCH")
    s = summarize(inp, manifest["rows"], gold_rows)
    out = {"execution_class": manifest["execution_class"], "mode": ident["mode"], "stop_reason": manifest["stop_reason"],
           "live_model_calls": manifest["live_model_calls"], "identity": ident, **s}
    if ident["mode"] == "PILOT":
        out["pilot_gate"] = pilot_gate(manifest, s, len(schedule(inp, "PILOT")))
    else:
        out["decision"] = decide(s)
        if manifest["execution_class"] != "LIVE":   # gold replayed through the harness: perfect by construction
            out["decision"]["answer"] = "NOT_A_MEASUREMENT_FAKE_PROVIDER"
    return out


def _write_new(path: Path, value: Any) -> None:
    if path.exists():
        raise PilotStopped("OUTPUT_EXISTS")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value))


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=["GOLD", "REPLAY_PILOT", "REPLAY_LOCKED", "LIVE_PILOT", "LIVE_LOCKED", "SCORE"],
                    required=True)
    ap.add_argument("--out-dir", type=Path)
    ap.add_argument("--approval-file", type=Path)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--manifest", type=Path, help="SCORE: a recorded manifest.json")
    ap.add_argument("--gold-rows", type=Path, help="SCORE: the recorded GOLD rows file (required)")
    ap.add_argument("--out", type=Path, help="SCORE: write the score receipt here (never overwritten)")
    a = ap.parse_args()
    inp = load_inputs()
    if a.mode == "GOLD":
        rows = run_gold(inp)
        _write_new(a.out_dir / "gold_rows.json", {"identity_product": identity(inp, "LOCKED")["product_sha256"], "rows": rows})
        print(json.dumps({k: v for k, v in summarize(inp, rows, rows).items() if k != "scored"}, ensure_ascii=False, indent=1))
        return 0
    if a.mode == "SCORE":
        if a.gold_rows is None:
            raise SystemExit("--gold-rows is required")
        result = score_manifest(inp, json.loads(a.manifest.read_bytes()), json.loads(a.gold_rows.read_bytes())["rows"])
        if a.out:
            _write_new(a.out, result)
        print(json.dumps({k: v for k, v in result.items() if k not in ("scored", "identity")}, ensure_ascii=False, indent=1))
        return 0
    kind, mode = a.mode.split("_")
    if kind == "LIVE":
        import app.persistence.db  # noqa: F401 — the product's own loader of backend/.env (key never printed)
    provider = ReplayProvider(inp) if kind == "REPLAY" else live_provider(inp, mode, a.approval_file)
    secrets = (os.environ["GEMINI_API_KEY"],) if kind == "LIVE" else ()
    state = run_eval(inp, mode, provider, a.out_dir, resume=a.resume, secrets=secrets)
    print(json.dumps({"rows": len(state["rows"]), "stop_reason": state["stop_reason"],
                      "live_model_calls": state["live_model_calls"], "budget": state["budget"]}))
    return int(state["stop_reason"] is not None)


if __name__ == "__main__":
    raise SystemExit(main())
