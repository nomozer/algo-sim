# -*- coding: utf-8 -*-
"""Vietnamese NL → TypedFacts V2 evaluation: dataset protocol checks, layer scorers and the offline replay runner core.
offline · **0 provider calls** · the module has no transport and never reads a key.

Run `hybrid-v2-nl-certificates-e2e`. Protocol: `docs/evaluation/geometry/runs/hybrid-v2-nl-certificates-e2e/protocol/`.

What it measures — each layer on its own, NEVER summed into one accuracy:

  entity      labels the extraction names (solid notation + every label of facts/goals) vs the gold entity set
  facts       canonical premise multiset vs gold (precision / recall; order-free vertex lists, undirected segments)
  provenance  every extracted quote is verbatim in the source and supports the labels of its own fact
  goal        canonical (goal_type, target) of the asked quantity vs gold
  outcome     CORRECT_SERVED · INCORRECT_SERVED · CORRECT_REFUSED · INCORRECT_REFUSED (+ EXTRACTION_FAILURE, which is
              never a correct refusal: a schema / provider failure is not a verdict of the deterministic gate)
  contradiction  gold-contradictory items: refused by the gate (any allowed code) vs served
  e2e         correct_served / gold-SERVE items and correct_served / served items, reported as two ratios

Reuse from the historical G05 tooling (`471a2c79`, read only, not merged): the exact-value key (rational / radical
compared by `(sign, square)`, never by float or string) and the rule "a provider/schema failure is never a correct
refusal". Everything else is rewritten for TypedFacts V2, the current engine/planner and cache 130.

Independence is a property of the dataset, not of the score: `claim_ceiling` says what the data allows to be claimed.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from fractions import Fraction
from typing import Any, Callable, Iterable

DATASET_SCHEMA = "nl-eval-dataset/1"
SPLITS = ("DEV_AUTHORED", "EXPOSED_PRIOR", "HOLDOUT")
AUTHOR_KINDS = ("SAME_AGENT", "BLIND_AGENT", "HUMAN")
OUTCOMES = ("CORRECT_SERVED", "INCORRECT_SERVED", "CORRECT_REFUSED", "INCORRECT_REFUSED", "EXTRACTION_FAILURE")
REFUSAL_CATEGORIES = ("INSUFFICIENT", "CONTRADICTORY", "UNSUPPORTED", "NOT_A_PREMISE", "AMBIGUOUS", "UNPROVEN_RELATION")
#: Codes that mean OUR fault or the provider's, never a gate verdict (same list the offline route uses).
TECHNICAL_CODES = frozenset({"EXTRACTOR_INTERNAL_ERROR", "PROVIDER_ERROR", "PROVIDER_RESPONSE_INVALID", "PROVIDER_BLOCKED",
                             "PROVIDER_REFUSED", "NO_CANDIDATE", "MALFORMED_RESPONSE_PART", "JSON_INVALID",
                             "RESPONSE_TRUNCATED", "MAX_TOKENS", "ROUTE_INTERNAL_ERROR", "HYBRID_CANCELLED",
                             "HYBRID_DEADLINE_EXCEEDED", "PREVIEW_IDENTITY_CHANGED", "PREVIEW_DISABLED"})
#: Failures BEFORE any gate verdict: the extraction was unusable (absent, wrong schema, another source, provider/technical).
#: The deterministic role/quote checks of the extraction validator (QUOTE_NOT_IN_SOURCE, CONDITIONAL_CLAUSE, NEGATED_CLAUSE,
#: GOAL_CLAUSE_NOT_PREMISE, …) are VERDICTS about the content, not failures: they count as a refusal by the gate.
EXTRACTION_CODES = frozenset({"NO_RECORDED_EXTRACTION", "SCHEMA_VERSION_MISMATCH", "REPLAY_SOURCE_IDENTITY_MISMATCH",
                              "INVALID_TYPED_FACT_NEXT"}) | TECHNICAL_CODES


# ── exact values (G05 idea: compare `(power of π, sign, value²)`, never floats or strings) ────────────────────────────

_SO = re.compile(r"^(?P<dau>[-−])?(?P<he>\d+(?:/\d+)?)?(?P<pi>π)?(?:√(?P<can>\d+))?(?:/(?P<mau>\d+))?$")


def exact_key(label: str) -> tuple[int, int, Fraction]:
    """`√17`, `24/5`, `12√29/5`, `cos²=32/41`, `2π` → `(mu_pi, sign, value²)`. A non-exact string raises `ValueError`."""
    s = label.strip().replace(" ", "")
    s = re.sub(r"^cos²=", "", s)                       # the route states an angle as its exact cos²; the key is of that number
    m = _SO.match(s)
    if not m or not (m["he"] or m["can"] or m["pi"]):
        raise ValueError(f"not an exact number: {label!r}")
    coef = Fraction(m["he"] or 1) / Fraction(m["mau"] or 1)
    sq = coef * coef * int(m["can"] or 1)
    return (1 if m["pi"] else 0), (0 if sq == 0 else (-1 if m["dau"] else 1)), sq


def same_value(served: str, gold: str) -> bool | None:
    """`True`/`False` when both are exact numbers; `None` when the served string is not one (ungradable, never a pass)."""
    try:
        return exact_key(served) == exact_key(gold)
    except ValueError:
        return None


# ── canonical forms ───────────────────────────────────────────────────────────────────────────────────────────────────

_ORDER_FREE = frozenset({"vertices", "plane", "plane1", "plane2", "segment", "line", "line1", "line2", "points", "base",
                         "rays", "lines"})
_LABEL = re.compile(r"[A-Z][0-9]*['′’]?")
_PLANE_KEYS = frozenset({"plane", "plane1", "plane2", "base", "vertices"})


def _norm_label(x: str) -> str:
    return x.replace("′", "'").replace("’", "'")


def _num(x: str) -> str:
    try:
        return str(Fraction(x.replace(",", ".")))
    except (ValueError, ZeroDivisionError):
        return x


def canon(value: Any, key: str = "") -> Any:
    """Order-free where geometry is (a plane is its vertex SET, a segment its two endpoints), exact for numbers; quotes
    and ids are not part of the meaning and never enter a canonical form."""
    if isinstance(value, dict):
        return tuple(sorted((k, canon(v, k)) for k, v in value.items() if k not in ("quote", "quotes") and not k.endswith("_id")))
    if isinstance(value, (list, tuple)):
        inner = [canon(v, key) for v in value]
        if all(isinstance(v, str) for v in inner):
            inner = [_norm_label(v) for v in inner]
            return tuple(sorted(inner)) if key in _ORDER_FREE else tuple(inner)
        return tuple(sorted(inner, key=repr)) if key in _ORDER_FREE else tuple(inner)
    if isinstance(value, str):
        return _num(value) if re.fullmatch(r"-?\d+(?:[.,]\d+)?(?:/\d+)?", value) else _norm_label(value)
    return value


def _facts(payload: dict) -> list[tuple]:
    return [(p.get("kind"), canon(p.get("args", {}))) for p in payload.get("premises", [])]


def _goals(payload: dict) -> list[tuple]:
    return [(g.get("goal_type"), canon(g.get("target", {}))) for g in payload.get("math_goals", [])]


def _entities(payload: dict) -> set[str]:
    out = {_norm_label(s.get("notation", "")) for s in payload.get("solids", []) if s.get("notation")}
    for blob in (payload.get("premises", []), payload.get("math_goals", [])):
        for item in blob:
            for part in (item.get("args"), item.get("target")):
                out |= {_norm_label(t) for t in _LABEL.findall(json.dumps(part, ensure_ascii=False))}
    return out


# ── layer scorers (pure; payload dicts only) ──────────────────────────────────────────────────────────────────────────

def _prf(extracted: list, gold: list) -> dict[str, int]:
    e, g = Counter(extracted), Counter(gold)
    tp = sum((e & g).values())
    return {"tp": tp, "fp": sum(e.values()) - tp, "fn": sum(g.values()) - tp}


def score_extraction(payload: dict | None, gold_payload: dict) -> dict[str, Any]:
    """Entity / fact / goal / provenance layers of ONE extraction against its gold. `payload=None` ⇒ all layers empty."""
    if payload is None:
        return {"entity": {"exact": False}, "facts": _prf([], _facts(gold_payload)),
                "goal": {"exact": False}, "provenance": {"ok": False, "bad_quotes": ["<no extraction>"]}}
    ge, ee = _entities(gold_payload), _entities(payload)
    source = payload.get("problem_text", "")
    bad = []
    for item in (*payload.get("premises", []), *payload.get("math_goals", []), *payload.get("solids", [])):
        q = item.get("quote")
        body = item.get("args") or item.get("target") or {}
        if isinstance(q, str) and re.search(r"đáy|mặt chéo|mặt bên", q, re.IGNORECASE) and isinstance(body, dict):
            body = {k: v for k, v in body.items() if k not in _PLANE_KEYS}   # a plane may be named by a word ("đáy")
        labels = {_norm_label(x) for x in _LABEL.findall(json.dumps(body, ensure_ascii=False))}
        if not isinstance(q, str) or q not in source:
            bad.append(str(q))
        elif not labels <= {_norm_label(x) for x in _LABEL.findall(q)}:
            bad.append(q)                                  # the quote does not carry the labels the fact asserts
    return {"entity": {"exact": ee == ge, "missing": sorted(ge - ee), "extra": sorted(ee - ge)},
            "facts": _prf(_facts(payload), _facts(gold_payload)),
            "goal": {"exact": sorted(_goals(payload), key=repr) == sorted(_goals(gold_payload), key=repr)},
            "provenance": {"ok": not bad, "bad_quotes": bad}}


def classify_outcome(expectation: dict, route: dict) -> dict[str, Any]:
    """ONE item → one outcome. `route` = `{"status": "SERVED"|"REFUSED", "code": str|None, "answers": {id: str}}`.

    Gold SERVE: served with the exact gold value ⇒ CORRECT_SERVED; served with another value ⇒ INCORRECT_SERVED;
    refused by the gate ⇒ INCORRECT_REFUSED. Gold REFUSE: served ⇒ INCORRECT_SERVED; refused by the gate ⇒
    CORRECT_REFUSED. A refusal that is not a gate verdict (extraction/provider/technical) is EXTRACTION_FAILURE for
    either gold: it can neither prove the system safe nor wrong.
    """
    serve = expectation["disposition"] == "SERVE"
    out: dict[str, Any] = {"outcome": None, "detail": None}
    if route["status"] == "SERVED":
        if not serve:
            out.update(outcome="INCORRECT_SERVED", detail="gold REFUSE but served")
        else:
            want = expectation["values"]
            got = route.get("answers") or {}
            eq = {k: same_value(got.get(k, ""), v) for k, v in want.items()}
            ok = all(v is True for v in eq.values()) and set(got) >= set(want)
            out.update(outcome="CORRECT_SERVED" if ok else "INCORRECT_SERVED", detail=json.dumps(eq, sort_keys=True))
        return out
    code = route.get("code") or ""
    if code in EXTRACTION_CODES:
        out.update(outcome="EXTRACTION_FAILURE", detail=code)
    elif serve:
        out.update(outcome="INCORRECT_REFUSED", detail=code)
    else:
        allowed = expectation.get("allowed_codes") or []
        out.update(outcome="CORRECT_REFUSED", detail=code, code_in_allowed=(code in allowed) if allowed else None)
    return out


# ── dataset protocol ──────────────────────────────────────────────────────────────────────────────────────────────────

def dataset_sha256(items: list[dict]) -> str:
    return hashlib.sha256(json.dumps(items, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def validate_dataset(items: list[dict]) -> list[str]:
    """Structural errors (empty list = valid). No item may be both gold-SERVE without values and unlabelled in exposure."""
    errs, ids = [], set()
    for it in items:
        i = it.get("id", "<no id>")
        if i in ids:
            errs.append(f"{i}: duplicate id")
        ids.add(i)
        if it.get("split") not in SPLITS:
            errs.append(f"{i}: split {it.get('split')!r}")
        pv, ex, gd = it.get("provenance") or {}, it.get("exposure") or {}, it.get("gold") or {}
        if pv.get("author_kind") not in AUTHOR_KINDS or not pv.get("origin"):
            errs.append(f"{i}: provenance needs author_kind in {AUTHOR_KINDS} and origin")
        if ex.get("label") not in ("FRESH", "EXPOSED") or not isinstance(ex.get("in_tests"), bool) or not isinstance(ex.get("in_prompt"), bool):
            errs.append(f"{i}: exposure needs label FRESH|EXPOSED, in_tests, in_prompt")
        if it.get("split") == "HOLDOUT" and (pv.get("author_kind") == "SAME_AGENT" or ex.get("label") != "FRESH"):
            errs.append(f"{i}: a HOLDOUT item must be FRESH and not authored by the implementing agent")
        e = gd.get("expectation") or {}
        if e.get("disposition") == "SERVE":
            if not e.get("values"):
                errs.append(f"{i}: gold SERVE without exact values")
        elif e.get("disposition") == "REFUSE":
            if e.get("category") not in REFUSAL_CATEGORIES:
                errs.append(f"{i}: gold REFUSE needs category in {REFUSAL_CATEGORIES}")
        else:
            errs.append(f"{i}: expectation.disposition")
        if not isinstance(gd.get("payload"), dict) or gd["payload"].get("problem_text") != it.get("problem_text"):
            errs.append(f"{i}: gold payload must carry the item's own problem_text")
    return errs


def claim_ceiling(items: list[dict], manifest: dict | None = None) -> str:
    """What the data permits to be claimed. A hash registered BEFORE implementation work is required for HOLDOUT."""
    splits = {it["split"] for it in items}
    if splits == {"HOLDOUT"}:
        ok = manifest and manifest.get("dataset_sha256") == dataset_sha256(items) and manifest.get("registered_before_tuning") is True
        return "INDEPENDENT_HOLDOUT" if ok else "HOLDOUT_UNREGISTERED_TREAT_AS_DEV"
    if all(it["provenance"]["author_kind"] == "SAME_AGENT" for it in items):
        return "DEV_AUTHORED_NOT_INDEPENDENT"
    return "DEV_OR_EXPOSED_NOT_INDEPENDENT"


# ── runner core (offline; the extractor is injected — a fake provider, a replay, or the gold itself) ─────────────────

def route_summary(response: dict, receipt: dict) -> dict[str, Any]:
    """Flatten a `run_hybrid_offline` result to what `classify_outcome` reads; the route owns every verdict."""
    rd = response.get("route_d") or {}
    code = (rd.get("refusal") or {}).get("code") or receipt.get("code")
    return {"status": rd.get("status", "REFUSED"), "code": code, "answers": dict(rd.get("answers") or {}),
            "failure_stage": receipt.get("failure_stage"), "failure_kind": receipt.get("failure_kind")}


def run_item(item: dict, extractor: Any) -> dict[str, Any]:
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    from app.ai.typed_fact_next_extraction import extract_typed_fact_next_v2

    text = item["problem_text"]
    ext = extract_typed_fact_next_v2(text, extractor)
    payload = ext.payload.model_dump(mode="json") if ext.payload is not None else None
    res = run_hybrid_offline(text, extractor, policy=hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"}))
    route = route_summary(res.response, res.receipt)
    gold = item["gold"]
    return {"id": item["id"], "split": item["split"], "route": route, "gold_disposition": gold["expectation"]["disposition"],
            **classify_outcome(gold["expectation"], route),
            "layers": score_extraction(payload, gold["payload"]),
            "contradiction_gold": bool(gold.get("contradiction"))}


class StopPolicy:
    """Budget / stop rules shared by offline replay and (later, only under an Owner GO) a live run. A live run is
    stopped at the first INCORRECT_SERVED — a false serve is the one outcome the system must never produce."""

    def __init__(self, max_items: int, stop_on_incorrect_served: bool = True, max_extraction_failures: int = 5) -> None:
        self.max_items, self.stop_incorrect, self.max_fail = max_items, stop_on_incorrect_served, max_extraction_failures
        self.n = self.fail = 0
        self.stopped: str | None = None

    def allow_next(self) -> bool:
        if self.stopped:
            return False
        if self.n >= self.max_items:
            self.stopped = "BUDGET_EXHAUSTED"
            return False
        return True

    def record(self, row: dict) -> None:
        self.n += 1
        self.fail += row["outcome"] == "EXTRACTION_FAILURE"
        if self.stop_incorrect and row["outcome"] == "INCORRECT_SERVED":
            self.stopped = "STOP_INCORRECT_SERVED"
        elif self.fail > self.max_fail:
            self.stopped = "STOP_EXTRACTION_FAILURES"


def summarize(rows: list[dict]) -> dict[str, Any]:
    """Per-layer counts and the outcome table. Layers are reported separately; no blended accuracy exists here."""
    outcome = Counter(r["outcome"] for r in rows)
    served = outcome["CORRECT_SERVED"] + outcome["INCORRECT_SERVED"]
    gold_serve = sum(r["gold_disposition"] == "SERVE" for r in rows)
    lay = [r["layers"] for r in rows]
    facts = Counter()
    for x in lay:
        facts.update(x["facts"])
    contra = [r for r in rows if r["contradiction_gold"]]
    return {
        "n": len(rows), "outcomes": {k: outcome[k] for k in OUTCOMES},
        "entity_exact": sum(x["entity"]["exact"] for x in lay), "goal_exact": sum(x["goal"]["exact"] for x in lay),
        "provenance_ok": sum(x["provenance"]["ok"] for x in lay),
        "facts": {"tp": facts["tp"], "fp": facts["fp"], "fn": facts["fn"]},
        "contradiction": {"n": len(contra), "refused_by_gate": sum(r["outcome"] == "CORRECT_REFUSED" for r in contra),
                          "served": sum(r["outcome"] == "INCORRECT_SERVED" for r in contra)},
        "e2e": {"correct_served": outcome["CORRECT_SERVED"], "gold_serve_items": gold_serve, "served": served},
    }


def run_dataset(items: list[dict], extractor_for: Callable[[dict], Any], policy: StopPolicy | None = None) -> dict[str, Any]:
    policy = policy or StopPolicy(len(items))
    rows = []
    for it in items:
        if not policy.allow_next():
            break
        row = run_item(it, extractor_for(it))
        rows.append(row)
        policy.record(row)
    return {"rows": rows, "summary": summarize(rows), "stopped": policy.stopped, "provider_calls": 0}


def gold_extractor(item: dict) -> Any:
    """The GOLD arm: the extraction is the gold payload itself — measures the deterministic stages alone."""
    from app.ai.typed_fact_next_extraction import ReplayExtractor

    return ReplayExtractor({item["problem_text"]: item["gold"]["payload"]})


LIVE_PROVIDER_GO_REQUIRED = "LIVE_PROVIDER_GO_REQUIRED"
