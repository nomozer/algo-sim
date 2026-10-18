# -*- coding: utf-8 -*-
"""Semantic extraction evaluation /2. Reuse the frozen execution harness; score source obligations independently.

Each CLI invocation isolates one prompt arm in its own process. No live execution without an exact new identity GO.
The historical evaluator and its receipts are never rewritten. GOLD/REPLAY are authored-fact measurements, not NLU.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from scripts import run_nlu_extraction_evaluation as V1

RUN = ROOT / "docs/evaluation/geometry/runs/hybrid-semantic-extraction-v2"
SCORER_VERSION = "grounded-source-obligations/3"  # /3: point-point distance = segment length (I3), height owned by its apex (M2)
from app.ai.fact_extraction import SYSTEM_PROMPT as _PRODUCT_PROMPT  # noqa: E402 — the v2 arm is the product prompt


def _legacy_instance():
    spec = importlib.util.spec_from_file_location("_semantic_eval_legacy", Path(V1.__file__))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_SCORING = _legacy_instance()
_old_sig = _SCORING._sig


def _signature(f, by_id, depth=0):
    sig = _old_sig(f, by_id, depth)
    if sig.get("solid") is not None:
        sig["solid"] = _solid_key(f["solid"])
        # A height belongs to an apex: S.ABC and A.SBC are one tetrahedron (vertex set) but two different heights (review M2).
        if f.get("kind") == "length" and f.get("measure") == "height" and "." in f["solid"]:
            sig["solid"] = (sig["solid"], V1._norm(f["solid"]).replace(" ", "").split(".")[0])
    if f.get("kind") == "question" and f.get("quantity") == "area":
        sig["solid"] = _solid_key(f["solid"]) if f.get("solid") else None
        if not f.get("solid") and isinstance(f.get("points"), list) and f["points"]:
            sig["points"] = _cycle(f["points"])   # a polygon, not a label set (V1 sorted it)
    return sig


_SCORING._sig = _signature


def _labels(value):
    return tuple(sorted(V1._norm(x) for x in value))


def _cycle(value):
    """A polygon is its vertex cycle: rotations and reflections name it, any other order is another polygon."""
    v = [V1._norm(x) for x in value]
    return min(tuple(r[i:] + r[:i]) for r in (v, v[::-1]) for i in range(len(v)))


def _solid_key(symbol):
    """A solid is its vertex structure, as the planner reads the symbol: a tetrahedron is its vertex set (the planner
    renames OPQR to R.OPQ), a pyramid its apex plus base cycle, a prism its two corresponding base cycles (rotated or
    reflected together, either base first). Anything else compares as written."""
    from app.simulation.geometry_functions.planner import _nhan
    s = V1._norm(symbol).replace(" ", "")
    parts = [_nhan(p) for p in s.split(".")]
    if "".join("".join(p) for p in parts) != s.replace(".", ""):
        return ("raw", s)
    if len(parts) == 1 and len(parts[0]) == 4 or len(parts) == 2 and len(parts[0]) == 1 and len(parts[1]) == 3:
        return ("tetrahedron", frozenset(l for p in parts for l in p))
    if len(parts) == 2 and len(parts[0]) == 1:
        return ("pyramid", parts[0][0], _cycle(parts[1]))
    if len(parts) == 2 and len(parts[0]) == len(parts[1]) >= 3:
        pairs = list(zip(*parts))
        return ("prism", min(tuple(z[::k] for z in r[i:] + r[:i]) for r in (pairs, pairs[::-1]) for i in range(len(pairs))
                             for k in (1, -1)))
    return ("raw", s)


def _same_target(expected: dict, actual: dict, quantity: str | None = None) -> bool:
    """Operand equivalence per role: segment/line endpoints are unordered, a plane is a label set (containment),
    a polygon is cyclic. Positional slots (point vs image) and the two-object swap are not decided here."""
    if set(expected) != set(actual):
        return False
    polygon = quantity == "area" and "solid" not in expected
    for key, want in expected.items():
        got = actual[key]
        if isinstance(want, list):
            if not isinstance(got, list):
                return False
            if key == "points" and polygon:
                if len(want) != len(got) or _cycle(want) != _cycle(got):
                    return False
            # The served engine checks every written plane label for coplanarity; any three then name that plane.
            elif (key in {"points_a", "points_b"} or (key == "points" and quantity == "area")) and min(len(want), len(got)) >= 3:
                if not (set(_labels(want)) <= set(_labels(got)) or set(_labels(got)) <= set(_labels(want))):
                    return False
            elif _labels(want) != _labels(got):
                return False
        elif key == "solid":
            if _solid_key(want) != _solid_key(got):
                return False
        elif V1._norm(want) != V1._norm(got):
            return False
    return True


def _call_target(call: dict, route: dict) -> tuple[str, dict] | None:
    fn, a = call["fn"], call["args"]
    if any(not isinstance(x, dict) for x in route.get("auxiliary", [])):
        return None   # malformed certificate list: unscorable, never guessed
    aux = next((x for x in route.get("auxiliary", []) if x.get("ask") == call["id"]), None)
    if aux:
        # A certificate is not sufficient: its referenced construction must actually have executed.
        calls = {c["id"]: c for c in route["calls"] if c["id"] in route["executed_calls"]}
        if aux.get("rule") == "distance(point,line)":
            foot = calls.get(aux.get("construct"))
            if (not foot or foot["fn"] != "orthogonal_projection_line" or fn != "ask_length"
                    or set(a.get("segment", [])) != {foot["args"].get("point"), foot["args"].get("image")}):
                return None
            f = foot["args"]
            if "line_ref" in f:
                return None  # Explicitly unscorable until the two source planes have a recorded semantic oracle.
            return "distance", {"points_a": [f["point"]], "points_b": f["line"]}
        if aux.get("rule") == "effect-chain":
            op, target = aux.get("operand", {}), aux.get("target", {})
            if not isinstance(op, dict) or not isinstance(target, dict) or op.get("descriptor") not in {"midpoint", "centroid"}:
                return None
            producer = next((c for c in calls.values() if c["fn"] == op["descriptor"]
                             and c["args"].get("point") == op.get("label")), None)
            if not producer or _labels(producer["args"].get("segment", producer["args"].get("polygon", []))) != _labels(op.get("points", [])):
                return None
            if fn == "ask_distance_point_plane" and a.get("point") == op["label"] and "plane" in target:
                if _labels(a["plane"]) != _labels(target["plane"]):
                    return None
                return "distance", {"point_kind": op["descriptor"], "points": op["points"], "points_b": target["plane"]}
            if fn == "ask_length" and "point" in target and set(a["segment"]) == {op["label"], target["point"]}:
                return "length", {"point_kind": op["descriptor"], "points": op["points"], "points_b": [target["point"]]}
            if fn == "ask_length" and "line" in target:
                # Distance to a named line: the answer is the segment from the described point to its executed foot.
                foot = next((c for c in calls.values() if c["fn"] == "orthogonal_projection_line"
                             and c["args"].get("point") == op["label"] and _labels(c["args"].get("line", [])) == _labels(target["line"])
                             and set(a["segment"]) == {op["label"], c["args"].get("image")}), None)
                if foot:
                    return "distance", {"point_kind": op["descriptor"], "points": op["points"], "points_b": target["line"]}
            return None
    if fn == "ask_length":
        return "length", {"points": a["segment"]}
    if fn == "ask_distance_point_plane":
        return "distance", {"points_a": [a["point"]], "points_b": a["plane"]}
    if fn == "ask_distance_lines":
        return "distance", {"points_a": a["line1"], "points_b": a["line2"]}
    if fn == "ask_volume":
        return "volume", {"solid": a["solid"]}
    if fn == "ask_area":
        return "area", {"points": a["polygon"]}
    if fn == "ask_section_area":
        return "area", {"solid": a["solid"], "points": a["plane"]}
    if fn == "ask_angle_line_plane":
        return "angle", {"points_a": a["line"], "points_b": a["plane"]}
    if fn == "ask_angle_plane_plane":
        return "angle", {"points_a": a["plane1"], "points_b": a["plane2"]}
    if fn in {"orthogonal_projection", "orthogonal_projection_line"}:
        return "projection", {"point": a["point"], "at": a["image"], "points": a.get("plane", a.get("line"))}
    return None


def _request_view(req: dict) -> tuple[str, dict]:
    """One canonical object per request: the distance between two single points IS the length of that segment (the
    route serves it as `ask_length`), so both encodings match the same served answer (review I3, an L01-style artifact)."""
    t = req["target"]
    if (req["quantity"] == "distance" and set(t) == {"points_a", "points_b"}
            and len(t["points_a"]) == len(t["points_b"]) == 1 and t["points_a"] != t["points_b"]):
        return "length", {"points": [*t["points_a"], *t["points_b"]]}
    return req["quantity"], t


#: `answer` must be served; `capability_gap` (construct/prove/explain/…) is fulfilled only by matching executed evidence.
#: `unsupported`, `ambiguous`, `missing_source` must never be served.
SERVABLE = {"answer", "capability_gap"}


def score_served(requests: list[dict], route: dict, *, parse_ok: bool = True) -> dict:
    """No extraction-pair argument: numeric correctness depends on executed operands and the independent oracle."""
    result = {"classification": None, "matched": [], "missing": [], "extra": []}
    if route.get("status") != "SERVED":   # a served answer is judged whatever the parse status: it cannot hide as NO_PARSE
        result["classification"] = ("NO_PARSE" if not parse_ok else
                                    "SAFE_REFUSAL" if all(r["disposition"] != "answer" for r in requests) else "FALSE_REFUSAL")
        return result
    if not all(k in route for k in ("calls", "executed_calls", "values", "answers")):
        result["classification"] = "UNSCORABLE"
        return result
    calls = {c["id"]: c for c in route["calls"]}
    available = set(route["answers"])
    if any(q not in calls or q not in route["executed_calls"] or q not in route["values"] for q in available):
        result["classification"] = "UNSCORABLE"
        return result
    used_constructions, wrong, unknown, form_mismatch = set(), False, False, False
    for req in requests:
        if req["disposition"] not in SERVABLE:
            result["missing"].append(req["rid"])
            continue
        candidates = available if req.get("oracle") is not None else (set(route["executed_calls"]) - used_constructions)
        hit = None
        for qid in sorted(candidates):
            if qid not in calls:
                continue
            try:
                bound = _call_target(calls[qid], route)
            except (KeyError, TypeError, ValueError):
                bound = None
            if bound is None:
                unknown = unknown or qid in available
                continue
            quantity, target = bound
            req_quantity, req_target = _request_view(req)
            same = _same_target(req_target, target, quantity)
            # Distance and (unsigned) angle between two objects are symmetric; projection/effect slots are not.
            if not same and quantity in {"distance", "angle"} and set(target) == {"points_a", "points_b"}:
                same = _same_target(req_target, {"points_a": target["points_b"], "points_b": target["points_a"]}, quantity)
            if quantity != req_quantity or not same:
                continue
            hit = qid
            if req.get("oracle") is not None:
                form = route.get("value_forms", {}).get(qid, "value_squared")
                form_mismatch = form_mismatch or req.get("response_form") not in (None, form)
                want = req["oracle"].get(form)
                if want is None:
                    unknown = True
                else:
                    try:
                        wrong = wrong or Fraction(route["values"][qid]) != Fraction(want)
                    except (ValueError, TypeError, ZeroDivisionError):
                        unknown = True
                available.remove(qid)
            else:
                used_constructions.add(qid)
            result["matched"].append(req["rid"])
            break
        if hit is None:
            result["missing"].append(req["rid"])
    result["extra"] = sorted(available)
    if wrong or (requests and not result["matched"] and all(r["disposition"] not in SERVABLE for r in requests)):
        verdict = "WRONG_SERVED"
    elif unknown:
        verdict = "UNSCORABLE"
    elif available and result["missing"]:
        verdict = "WRONG_SERVED"
    elif form_mismatch:
        verdict = "FORM_MISMATCH"
    elif available:
        verdict = "OVER_SERVED"
    elif result["missing"]:
        verdict = "PARTIAL_SERVED"
    else:
        verdict = "CORRECT_COMPLETE"
    result["classification"] = verdict
    return result


def route_record(r):
    rec = V1.route_record(r)
    rec.update(calls=(r.planner or {}).get("calls", []), auxiliary=(r.planner or {}).get("auxiliary", []),
               executed_calls=sorted({c for step in r.trace for c in step.get("calls", [])}),
               value_forms={qid: "cos_squared" if str(v).startswith("cos²") else "value_squared" for qid, v in r.answers.items()})
    return rec


def _normal_fact(f):
    """Ignore slots the product does not consume for this kind, without changing the provider output."""
    f = deepcopy(f)
    if not isinstance(f, dict):
        return f
    common = {"id", "rid", "required", "alternatives", "kind", "role", "quotes", "negated", "ambiguous", "reason"}
    fields = {
        "solid": {"solid", "solid_type", "regular", "right"},
        "question": {"quantity", "points", "points_a", "points_b", "point_kind", "point", "plane_relation", "plane_name", "line_ref", "solid"},
    }
    allowed = fields.get(f.get("kind"))
    if f.get("kind") == "question" and f.get("quantity") in {"length", "distance", "angle"} and not f.get("plane_relation"):
        allowed = allowed - {"solid"}
    if f.get("kind") == "question" and f.get("quantity") == "area" and not any("thiết diện" in V1._norm(q) for q in f.get("quotes", [])):
        allowed = allowed - {"solid"}
    if f.get("kind") == "solid":
        # Rightness as planner.py derives it: pyramids never read it; a prism is right iff right/regular/cube/cuboid.
        if f.get("solid_type") in {"pyramid", "tetrahedron"}:
            allowed = allowed - {"right"}
        else:
            f["right"] = bool(f.get("right") or f.get("regular") or f.get("solid_type") in {"cube", "cuboid"})
    return {k: v for k, v in f.items() if allowed is None or k in common | allowed}


def _operand_goals(reqs, by_rid):
    """One population for numerator and denominator: expressible (gold kind ≠ unsupported) operand-bearing requests."""
    return [by_rid[r["rid"]] for r in reqs if r["rid"] in by_rid and by_rid[r["rid"]].get("kind") != "unsupported"
            and r["quantity"] not in {"unsupported", "volume"}]


_old_match = _SCORING.match_facts


def _match_facts(gold, live, src):
    """V1 never lets a gold `equal_lengths` premise match (it is skipped as a segment-length fact on both sides). Here it is
    satisfied by a live equal_lengths naming the same two segments in any order, or by live lengths giving both one value."""
    m = _old_match(gold, live, src)
    pair = lambda f: frozenset(frozenset(_labels(f.get(k) or [])) for k in ("points_a", "points_b"))
    live_d = [f for f in live if isinstance(f, dict)]
    closure = _SCORING._segment_lengths(live_d)
    for g in gold:
        if g.get("kind") == "equal_lengths" and _SCORING._is_seglen(g) and g["id"] not in m["satisfied"]:
            a, b = (frozenset(_labels(g.get(k) or [])) for k in ("points_a", "points_b"))
            if any(_SCORING._is_seglen(l) and l.get("kind") == "equal_lengths" and pair(l) == pair(g) for l in live_d) or \
                    (closure.get(a) is not None and closure.get(a) == closure.get(b)):
                m["satisfied"].add(g["id"])
    return m


_SCORING.match_facts = _match_facts


def extraction(case, gold, facts):
    """Source-request denominators include constructions even when represented as premise facts."""
    gf = [_normal_fact(f) for f in gold["facts"]]
    live = [_normal_fact(f) for f in (facts or [])]
    matches = _SCORING.match_facts(gf, live, V1._norm(case["source_text"]))
    pairs = matches["pairs"]
    by_rid = {f["rid"]: f for f in gf if f.get("rid")}
    out = _SCORING.extraction(case, {"facts": gf}, live)
    reqs = case["requests"]
    free, intents = set(range(len(live))), 0
    for r in reqs:
        g = by_rid.get(r["rid"], {})
        hit = next((i for i in sorted(free) if isinstance(live[i], dict) and
                    tuple(live[i].get(k) for k in ("kind", "role", "quantity")) == tuple(g.get(k) for k in ("kind", "role", "quantity"))), None)
        if hit is not None:
            free.remove(hit)
            intents += 1
    out.update(requests_gold=len(reqs),
               intent_match=intents,
               goal_match=sum(by_rid.get(r["rid"], {}).get("id") in pairs for r in reqs),
               requests_expressible=sum(by_rid.get(r["rid"], {}).get("kind") != "unsupported" for r in reqs),
               goal_match_expressible=sum(by_rid.get(r["rid"], {}).get("kind") != "unsupported" and by_rid.get(r["rid"], {}).get("id") in pairs for r in reqs),
               schema_gap_requests=sum(r["disposition"] == "unsupported" for r in reqs),
               schema_gap_flagged=sum(r["disposition"] == "unsupported" and by_rid.get(r["rid"], {}).get("id") in pairs for r in reqs))
    out["complete_goals"] = out["goal_match"] == len(reqs) and not out["extra_questions"]
    out["correct"] = out["correct"] and out["complete_goals"]
    from app.simulation.geometry_functions.planner import _nhan
    used = {V1._norm(x) for f in live if isinstance(f, dict)
            for key in ("points", "points_a", "points_b", "point", "at") for x in (f.get(key) if isinstance(f.get(key), list) else [f.get(key)]) if x}
    used |= {x for f in live if isinstance(f, dict) and isinstance(f.get("solid"), str) for x in _nhan(V1._norm(f["solid"]))}
    out["invented_entities"] = sorted(used - {V1._norm(x) for x in case["entities"]})
    operand_goals = _operand_goals(reqs, by_rid)
    out["operand_required"] = len(operand_goals)
    out["operand_correct"] = sum(f["id"] in pairs for f in operand_goals)
    owned = [f for f in gf if (f.get("kind") == "length" and f.get("measure") != "segment") or
             (f.get("kind") == "question" and f.get("quantity") == "volume")]
    out["solid_required"] = len(owned)
    out["solid_correct"] = sum(f["id"] in pairs for f in owned)
    return out


def load_inputs(inputs=RUN / "inputs"):
    inp = V1.load_inputs(Path(inputs))
    protocol = inp["protocol"]
    for name, want in protocol["file_sha256"].items():
        if V1._lf_sha(Path(inputs) / name) != want:
            raise V1.PilotStopped("INPUT_IDENTITY_MISMATCH")
    families = {}
    for c in inp["corpus"]["cases"]:
        if len(c["requests"]) != c["n_source_requests"] or len({r["rid"] for r in c["requests"]}) != len(c["requests"]):
            raise V1.PilotStopped("SOURCE_REQUEST_COVERAGE_MISMATCH")
        annotated = [f["rid"] for f in inp["gold"]["cases"][c["id"]]["facts"] if f.get("rid")]
        if set(annotated) != {r["rid"] for r in c["requests"]} or len(annotated) != len(c["requests"]):
            raise V1.PilotStopped("SOURCE_REQUEST_COVERAGE_MISMATCH")
        if c["structure_id"] in families and families[c["structure_id"]] != c["split"]:
            raise V1.PilotStopped("SPLIT_FAMILY_LEAK")
        families[c["structure_id"]] = c["split"]
        for r in c["requests"]:
            if r["source_quote"] not in c["source_text"]:
                raise V1.PilotStopped("SOURCE_QUOTE_MISMATCH")
    return inp


def harness(arm, inp):
    """Private copy of the historical executor: configure hooks without altering historical code or global V1."""
    from app.ai import fact_extraction as fx
    h = _legacy_instance()
    # Every call sets the arm's prompt explicitly, so a baseline harness never leaks into a later v2 one.
    fx.SYSTEM_PROMPT = ((Path(inp["dir"]) / "baseline_prompt.txt").read_text(encoding="utf-8") if arm == "baseline"
                        else _PRODUCT_PROMPT)
    h.MODES = {"PILOT": ("dev", 1), "LOCKED": ("heldout", 1)}
    h.route_record = route_record
    persist = h._persist

    def persist_checked(path, state, secrets):
        flag = (state.get("rows") or [{}])[-1].get("usage_flag")
        if flag:
            state["stop_reason"] = flag
        persist(path, state, secrets)
        if flag:
            raise V1.PilotStopped(flag)
    h._persist = persist_checked
    old_identity = h.identity

    def identity(data, mode):
        return {**old_identity(data, mode), "arm": arm, "scorer_version": SCORER_VERSION,
                "scorer_runner_sha256": V1._lf_sha(Path(__file__)), "oracle_sha256": data["protocol"]["file_sha256"]["oracle.py"]}
    h.identity = identity
    return h


_LABEL = re.compile(r"[A-Z][0-9]{0,2}[′'″]{0,2}")


def _published(ext):
    """Derived metrics only: model-chosen fact ids are dropped; a non-label 'entity' is reported by hash, not text."""
    out = {k: v for k, v in ext.items() if k != "pairs"}
    if "invented_entities" in out:
        out["invented_entities"] = [x if _LABEL.fullmatch(x) else "NON_LABEL:" + hashlib.sha256(x.encode()).hexdigest()[:12]
                                    for x in out["invented_entities"]]
    return out


def summarize(inp, rows, gold_rows=None):
    """`gold_rows` (authored facts through the same route) split a false refusal: the extraction-perfect route also
    refuses ⇒ capability/grounding gap; it serves ⇒ the extraction failed."""
    outcomes, totals, multi, codes = Counter(), Counter(), Counter(), Counter()
    gold_status = {r["case_id"]: (r["route"] or {}).get("status") for r in gold_rows or ()}
    detail = []
    for row in rows:
        case = inp["cases"][row["case_id"]]
        gold = inp["gold"]["cases"][case["id"]]
        parsed = isinstance(row.get("facts"), list) and not row.get("parse_code")
        ext = extraction(case, gold, row["facts"]) if parsed else {}
        if row.get("infra"):   # transport/provider failure: no model answer exists to score
            served = {"classification": "PROVIDER_OR_HARNESS_ERROR", "matched": [], "missing": [], "extra": []}
        else:
            served = score_served(case["requests"], row["route"] or {"status": "REFUSED"}, parse_ok=parsed)
        if served["classification"] == "FALSE_REFUSAL" and case["id"] in gold_status:
            served["classification"] += "_EXTRACTION" if gold_status[case["id"]] == "SERVED" else "_CAPABILITY_GAP"
        if (row["route"] or {}).get("status") != "SERVED":
            codes[(row["route"] or {}).get("code") or row.get("parse_code") or row.get("infra") or "UNKNOWN"] += 1
        outcomes[served["classification"]] += 1
        for key in ("goal_match", "goal_match_expressible", "premise_match", "premises_required", "premise_live_matched", "premises_live",
                    "schema_gap_flagged", "operand_correct", "solid_correct", "intent_match"):
            totals[key] += ext.get(key, 0)
        # Parse failure remains in every source-based denominator.
        totals["requests_gold"] += len(case["requests"])
        totals["requests_expressible"] += sum(f.get("rid") is not None and f["kind"] != "unsupported" for f in gold["facts"])
        totals["schema_gap_requests"] += sum(r["disposition"] == "unsupported" for r in case["requests"])
        by_rid = {f["rid"]: f for f in gold["facts"] if f.get("rid")}
        totals["operand_required"] += len(_operand_goals(case["requests"], by_rid))
        totals["solid_required"] += sum((f.get("kind") == "length" and f.get("measure") != "segment") or
                                        (f.get("kind") == "question" and f.get("quantity") == "volume") for f in gold["facts"])
        totals["rows"] += 1
        totals["parsed_rows"] += int(parsed)
        totals["hallucinated_entity_rows"] += bool(ext.get("invented_entities"))
        if len(case["requests"]) > 1:
            multi["total"] += 1
            multi["complete"] += bool(ext.get("complete_goals"))
        # Answer ids are model-chosen fact ids: publish the count of extra answers, not the ids.
        published = {k: v for k, v in served.items() if k != "extra"} | {"extra_count": len(served["extra"])}
        detail.append({"case_id": case["id"], "extraction": _published(ext), "served": published,
                       "route_code": (row["route"] or {}).get("code")})
    usage = [r["usage"] for r in rows if r.get("usage")]
    return {"schema": SCORER_VERSION, "e2e": dict(outcomes), "refusal_codes": dict(codes), "counts": dict(totals),
            "multi_goal": dict(multi), "rows": detail,
            "usage": {"rows_with_usage": len(usage), "rows": len(rows),
                      **{k: sum(u.get(k) or 0 for u in usage) for k in ("input_tokens", "output_tokens", "thinking_tokens")},
                      "usd_estimated_list_price": round(sum(u.get("usd") or 0 for u in usage), 6),
                      "latency_seconds": sorted(r["latency_seconds"] for r in rows if r.get("latency_seconds") is not None)},
            "interpretation": "Authored-fact GOLD/REPLAY are not model extraction accuracy. No population or human-validation claim."}


def validate_schedule(state, planned):
    observed = [{k: r.get(k) for k in ("case_id", "sample")} for r in state["rows"]]
    expected = [{**r, "sample": 0} for r in planned] if state.get("execution_class") == "GOLD" else planned
    if observed != expected[:len(observed)] or len(observed) > len(expected):
        raise V1.PilotStopped("SCHEDULE_MISMATCH")
    return {"status": "COMPLETE" if len(observed) == len(expected) and not state.get("stop_reason") else "INCOMPLETE",
            "observed_rows": len(observed), "planned_rows": len(expected), "stop_reason": state.get("stop_reason")}


def write_score(out, state, score):
    """Publishing derived metrics never copies raw manifests or model facts into a tracked location."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    # Audit by hash: the raw manifest stays in ignored `.superpowers/`; the receipt names the rows it scored.
    score = {**score, "source_manifest_rows_sha256": state.get("rows_sha256"),
             **{k: state.get(k) for k in ("execution_class", "identity", "stop_reason", "live_model_calls", "budget")}}
    V1._persist(out / "score.json", score, tuple(filter(None, [os.environ.get("GEMINI_API_KEY")])))


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("action", choices=["identity", "gold", "replay", "live", "score"])
    p.add_argument("--arm", choices=["baseline", "v2"], default="v2")
    p.add_argument("--mode", choices=["PILOT", "LOCKED"], default="PILOT")
    p.add_argument("--inputs", type=Path, default=RUN / "inputs")
    p.add_argument("--out", type=Path)
    p.add_argument("--manifest", type=Path)
    p.add_argument("--approval", type=Path)
    args = p.parse_args()
    inp = load_inputs(args.inputs)
    h = harness(args.arm, inp)
    if args.action == "identity":
        print(json.dumps(h.identity(inp, args.mode), indent=2))
        return
    if args.out is None or args.out.exists():
        raise V1.PilotStopped("OUTPUT_REQUIRED_OR_EXISTS")
    if args.action == "score":
        state = json.loads(args.manifest.read_bytes())
        if state["identity"] != h.identity(inp, args.mode) or state["rows_sha256"] != V1._sha(state["rows"]):
            raise V1.PilotStopped("IDENTITY_MISMATCH")
    elif args.action == "gold":
        rows = [r for r in h.run_gold(inp) if inp["cases"][r["case_id"]]["split"] == h.MODES[args.mode][0]]
        state = {"execution_class": "GOLD", "identity": h.identity(inp, args.mode), "rows": rows, "rows_sha256": V1._sha(rows), "live_model_calls": 0}
    else:
        if args.action == "live" and not args.out.resolve().is_relative_to(ROOT / ".superpowers"):
            raise V1.PilotStopped("LIVE_RAW_OUTPUT_REQUIRES_IGNORED_DIRECTORY")
        if args.action == "live":
            import app.persistence.db  # noqa: F401 — the product's own loader of backend/.env (key never printed), as V1
        provider = h.live_provider(inp, args.mode, args.approval) if args.action == "live" else h.ReplayProvider(inp)
        secrets = (os.environ["GEMINI_API_KEY"],) if args.action == "live" else ()
        state = h.run_eval(inp, args.mode, provider, args.out, secrets=secrets)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.action == "gold":
        V1._persist(args.out / "manifest.json", state, ())
    # The ceiling is recomputed from the locked gold on this same product (identity pins the product hash).
    gold_rows = state["rows"] if args.action == "gold" else h.run_gold(inp)
    score = summarize(inp, state["rows"], gold_rows)
    score["schedule"] = validate_schedule(state, h.schedule(inp, args.mode))
    write_score(args.out, state, score)
    print(json.dumps({"action": args.action, "rows": len(state["rows"]), "live_model_calls": state.get("live_model_calls", 0),
                      "e2e": score["e2e"], "refusal_codes": score["refusal_codes"]}))


if __name__ == "__main__":
    main()
