# -*- coding: utf-8 -*-
"""S-2 student-language pilot runner — protocol `docs/evaluation/geometry/runs/hybrid-master-backend-replacement/
s2-student-language-pilot-protocol.md` (§n). MEASUREMENT_CLASS of a live run: LIVE_DEVELOPMENT_PILOT (implementer-
authored development texts, never held-out, never the locked 60-case paired corpus).

ONE arm: the production opt-in Hybrid path (domain gate → `/4` extraction → Source Gate → planner → exact engine →
Adapter /4), one source-only request per case, ≤ 36 cases. The eight metrics are the unchanged scorer's
(`score_s2_student_language_pilot.py`); this runner only builds its records. Every compared field is projected by ONE
function (`project`) applied both to the decoded extraction and to the case's gold extraction, so gold and observed are
compared in the same form; served values are the learner-visible target quantities (`served_quantities`), never names.
`--dry-run` replays each gold extraction: the attribution baseline (a gold row that misses its expectation is a fault of
the deterministic layers, not of a live model). `--live` refuses before any request unless ALLOW_LIVE_AI=1,
GEMINI_API_KEY and an Owner approval file bound to the corpus, measured system, this runner, the paired harness, the
model and the caps. Budget, send guard and transport ARE the paired harness's (`run_paired_route_evaluation.py`).

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/run_s2_student_language_pilot.py \
        --corpus <corpus.json> --out <rows.jsonl> --dry-run          # or --manifest / --live --approval-file <owner.json>
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

import run_paired_route_evaluation as P  # noqa: E402
from score_s2_student_language_pilot import _rate_or_unknown, score_s2_pilot_records  # noqa: E402

LiveRefused = P.LiveRefused
MAX_CASES = 36                                       # §3/§4: hard request cap ≤ 36, one request per case
STRATA = ("S2-A", "S2-B", "S2-C", "S2-D", "S2-E", "S2-F")
#: C15: one runner, several pre-registered studies — each with its own closed strata and case cap (= request cap). A
#: corpus names its study; none ⇒ S-2, so the locked S-2 corpus is byte-identical. An approval binds exactly one study.
STUDIES = {"S-2": (STRATA, MAX_CASES),
           "R-1": (("R1-A", "R1-B", "R1-C", "R1-D", "R1-E", "R1-F", "R1-G"), 18)}   # unnamed described points (C14)
OUTCOMES = ("SERVED", "CLARIFY", "REFUSED_UNSUPPORTED", "REFUSED_INCONSISTENT")
#: `route-d-clarification/1` closed `nlu_class` vocabulary (server-built, never model prose) = the clarification code.
CLARIFICATION_CODES = ("AMBIGUOUS", "MISSING_DATA", "UNRECOGNIZED_WORDING")
#: Keys whose values are identifiers or source text, never facts: dropped before comparison.
_UNCOMPARED = {"quote", "problem_text", "schema_version", "goal_id", "relation_id", "unresolved_id", "described_id"}
#: Operands whose label ORDER carries no meaning: segment/line endpoints, a plane's labels (any 3+ name the same plane).
#: A polygon (`vertices`, `base`, `top`, `polygon`) keeps its order — it names the boundary — and so does the `segment`
#: of a ratio (`divide_segment`: P = (1−t)A + tB), see `_canon`.
_UNORDERED = {"segment", "line", "plane", "parallel_plane", "perpendicular_line", "parallel_line_a", "parallel_line_b",
              "edge", "line1", "line2", "plane1", "plane2", "segment_a", "segment_b"}
#: Pairs of operands that are interchangeable as a whole (distance/angle between two lines or two planes).
_SYMMETRIC_PAIRS = (("line1", "line2"), ("plane1", "plane2"))
_OPERAND = re.compile(r"^[A-Z][A-Z0-9']*(?:\.[A-Z0-9']+)?$|\d|√|π|^a$")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_identity() -> dict[str, str]:
    ident = P.runtime_identity()
    return {"measured_system": ident["measured_system"], "cache_version": ident["cache_version"],
            "model": ident["model"], "skills_sha256": ident["skills_sha256"],
            "paired_harness_sha256": ident["harness_sha256"], "runner_sha256": sha256_file(Path(__file__)),
            # C14 review: the scorer writes the summary's 8 metrics, so the approval binds it too
            "scorer_sha256": sha256_file(BACKEND / "scripts" / "score_s2_student_language_pilot.py")}


# ── corpus ───────────────────────────────────────────────────────────────────────────────────────────────────────────

def study_of(corpus: dict[str, Any]) -> str:
    study = corpus.get("study", "S-2")
    if study not in STUDIES:
        raise LiveRefused(f"unknown study {study!r}: one of {tuple(STUDIES)}")
    return study


def validate_corpus(corpus: dict[str, Any]) -> None:
    strata, cap = STUDIES[study_of(corpus)]
    cases = corpus.get("cases")
    if not isinstance(cases, list) or not 0 < len(cases) <= cap:
        raise LiveRefused(f"corpus needs 1..{cap} cases")
    ids = [c.get("id") for c in cases]
    texts = [P._norm(c.get("problem_text") or "") for c in cases]
    if len(set(ids)) != len(ids) or len(set(texts)) != len(texts) or not all(texts):
        raise LiveRefused("duplicate or empty case id / problem text")
    for c in cases:
        e = c.get("expected") or {}
        if c.get("stratum") not in strata or e.get("outcome") not in OUTCOMES:
            raise LiveRefused(f"{c.get('id')}: stratum must be in {strata} and expected.outcome in {OUTCOMES}")
        if (e["outcome"] == "CLARIFY") != bool(e.get("is_ambiguous")):
            raise LiveRefused(f"{c['id']}: exactly the CLARIFY cases are ambiguous")
        if e["outcome"] == "CLARIFY" and not set(e.get("allowed_clarification_codes") or ()) <= set(CLARIFICATION_CODES):
            raise LiveRefused(f"{c['id']}: clarification codes must be in {CLARIFICATION_CODES}")
        if e["outcome"] == "CLARIFY" and not e.get("allowed_clarification_codes"):
            raise LiveRefused(f"{c['id']}: a CLARIFY case needs allowed clarification codes")
        oracle = e.get("oracle")
        if e["outcome"] == "SERVED":
            if not isinstance(oracle, dict) or set(oracle) - set(P.KINDS.values()):
                raise LiveRefused(f"{c['id']}: a SERVED case needs an oracle (empty = simulation only) over known kinds")
            for values in oracle.values():
                [P.parse_oracle(v) for v in values]
        elif oracle:
            raise LiveRefused(f"{c['id']}: only SERVED cases carry an oracle")
        gold = c.get("gold_extraction")
        if gold is not None and (not isinstance(gold, dict) or gold.get("problem_text") != c["problem_text"]):
            raise LiveRefused(f"{c['id']}: the gold extraction must be for this exact problem text")


# ── projection: ONE function for gold and observed ───────────────────────────────────────────────────────────────────

def _canon(value: Any, names: dict[str, str]) -> Any:
    if isinstance(value, dict):
        out = {k: _canon(v, names) for k, v in sorted(value.items()) if k not in _UNCOMPARED and v is not None}
        for k in _UNORDERED & out.keys():
            if k == "segment" and "ratio" in out:                 # directed: the ratio is measured from the first label
                continue
            if isinstance(out[k], list) and all(isinstance(x, str) for x in out[k]):
                out[k] = sorted(out[k])
        for a, b in _SYMMETRIC_PAIRS:
            if a in out and b in out and _key(out[b]) < _key(out[a]):
                out[a], out[b] = out[b], out[a]
        return out
    if isinstance(value, (list, tuple)):
        return [_canon(v, names) for v in value]
    if isinstance(value, str):
        value = value.strip().replace("′", "'")
        return names.get(value, value)
    return value


def _key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _leaves(value: Any):
    if isinstance(value, dict):
        for v in value.values():
            yield from _leaves(v)
    elif isinstance(value, list):
        for v in value:
            yield from _leaves(v)
    elif isinstance(value, str):
        yield value


def project(payload: Any) -> dict[str, Any] | None:
    """Facts signature, goal list and operand list of an extraction, independent of ids, quotes and order: solid and
    section ids become their notation / plane name. `None` when the extraction is not a readable payload."""
    if not isinstance(payload, dict):
        return None
    try:
        names = {s["solid_id"]: f"solid:{s.get('notation')}" for s in payload.get("solids") or ()}
        names |= {s["section_id"]: f"section:{s.get('plane_name')}" for s in payload.get("derived_sections") or ()}
        for _ in range(2):                                    # R-1: `@id` → its canonical description (up to depth 2)
            for d in payload.get("described_points") or ():
                names[f"@{str(d['described_id']).strip()}"] = f"described:{_key(_canon(d, names))}"
        facts = {"length_unit": payload.get("length_unit"),
                 **{k: sorted(_key(_canon(x, names)) for x in payload.get(k) or ())
                    for k in ("solids", "premises", "derived_sections", "relations")}}
        goals = sorted([_key(["sim", _canon(g, names)]) for g in payload.get("simulation_goals") or ()]
                       + [_key(["math", _canon(g, names)]) for g in payload.get("math_goals") or ()])
        operands = sorted({x for x in _leaves(_canon({k: v for k, v in payload.items() if k != "unresolved"}, names))
                           if _OPERAND.search(x) and not x.startswith(("solid:", "section:", "described:", "@"))})
    except (KeyError, TypeError, AttributeError):
        return None
    return {"facts_signature": hashlib.sha256(_key(facts).encode("utf-8")).hexdigest()[:16],
            "goals": goals, "operands": operands}


def _quotes(value: Any):
    if isinstance(value, dict):
        for k, v in value.items():
            if k == "quote":
                yield v
            yield from _quotes(v)
    elif isinstance(value, list):
        for v in value:
            yield from _quotes(v)


def expected_record(case: dict[str, Any]) -> dict[str, Any]:
    """The scorer's `expected`. Extraction fields exist only where they are evaluable (§2): a gold extraction without an
    honest-exit entry — when any `unresolved` refuses the whole payload, which facts accompany it is not determined."""
    e = case["expected"]
    out = {"outcome": e["outcome"], "is_ambiguous": bool(e.get("is_ambiguous")),
           "allowed_clarification_codes": list(e.get("allowed_clarification_codes") or ())}
    if e["outcome"] == "SERVED":
        out["expected_answers"] = {k: sorted(str(P.parse_oracle(v)) for v in vs) for k, vs in e["oracle"].items()}
    gold = case.get("gold_extraction")
    proj = project(gold) if isinstance(gold, dict) and not gold.get("unresolved") else None
    if proj is not None:
        out.update(expected_facts_signature=proj["facts_signature"], expected_goals=proj["goals"],
                   expected_operands=proj["operands"])
    return out


# ── one case ─────────────────────────────────────────────────────────────────────────────────────────────────────────

class RecordingExtractor:
    """Keeps the decoded extraction the route consumed (authored texts only — protocol §4 data scope)."""

    def __init__(self, inner) -> None:
        self.inner, self.raw = inner, None

    def extract(self, source_text: str):
        self.raw = self.inner.extract(source_text)
        return self.raw


def observe(text: str, extractor, deadline_s: float = 15.0) -> tuple[dict[str, Any], dict[str, Any]]:
    """The scorer's `observed` record for one run of the production opt-in path, plus attribution facts."""
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    from app.ai.hybrid_preview import classify_refusal
    from app.main import _ngoai_pham_vi

    gate = _ngoai_pham_vi(text)
    if gate is not None:
        return ({"status": "REFUSED", "is_unsupported_code": True, "unresolved_flagged": False,
                 "quotes_verbatim_in_raw": False},
                {"hybrid_code": gate.get("error_code"), "failure_stage": "domain_gate", "raw_extraction": None})
    rec = RecordingExtractor(extractor)
    result = run_hybrid_offline(text, rec, policy=hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"}),
                                timeout_seconds=deadline_s)
    env, route, receipt = result.response["envelope"], result.response["route_d"], result.receipt
    code = receipt.get("code")
    extra = {"hybrid_code": code, "failure_stage": receipt.get("failure_stage"),
             "failure_kind": receipt.get("failure_kind"), "raw_extraction": rec.raw}
    if code in P.HYBRID_INFRASTRUCTURE:
        return {"status": "NOT_RECOVERABLE"}, extra
    raw = rec.raw if isinstance(rec.raw, dict) else None
    quotes = list(_quotes(raw)) if raw else []
    proj = project(raw) or {}
    obs: dict[str, Any] = {
        "facts_signature": proj.get("facts_signature"), "extracted_goals": proj.get("goals") or [],
        "operands": proj.get("operands"), "unresolved_flagged": bool(raw and raw.get("unresolved")),
        "quotes_verbatim_in_raw": bool(quotes) and all(isinstance(q, str) and q and q in text for q in quotes)}
    served = route.get("status") == "SERVED" and env.get("status") == "ok" and bool((env.get("scene3d") or {}).get("objects"))
    if served:
        obs.update(status="SERVED", certificate_verified=receipt["engine"]["status"] == "VERIFIED",
                   answers={k: sorted(map(str, v)) for k, v in P.served_quantities(env).items()})
        planner = route.get("planner") or {}                                 # C15: what the planner itself composed
        tel = planner.get("search_telemetry") or {}
        own = set(tel.get("planner_originated_steps") or ())
        extra["search"] = {"classification": tel.get("classification"),
                           "planner_steps": [{k: c.get(k) for k in ("id", "fn", "args")}
                                             for c in planner.get("calls") or () if c.get("id") in own]}
        return obs, extra
    clar = (route.get("refusal") or {}).get("clarification")
    if clar and clar.get("kind") != "unsupported":          # no learner answer can fix `unsupported` (server rule)
        obs.update(status="CLARIFY", clarification_code=clar.get("nlu_class"))
    else:
        group = classify_refusal(code or "").group
        obs.update(status="REFUSED", refusal_group=group, is_unsupported_code=bool(clar) or group == "CAPABILITY")
    extra["clarification"] = clar
    return obs, extra


def _score(records: list[dict[str, Any]]) -> dict[str, Any]:
    """The unchanged scorer refuses to run under ALLOW_LIVE_AI=1 (test-locked). It is a pure function with no I/O and
    runs between sequential requests, so a live run scores with the flag cleared for the call only — otherwise the
    summary of a PAID run would be lost in `finally` (found by the mock live tests)."""
    flag = os.environ.pop("ALLOW_LIVE_AI", None)
    try:
        return score_s2_pilot_records(records)
    finally:
        if flag is not None:
            os.environ["ALLOW_LIVE_AI"] = flag


def end_to_end_correct(expected: dict[str, Any], observed: dict[str, Any]) -> bool | None:
    """The learner-visible outcome is the expected one (`None`: not recoverable). Not one of the §2 metrics — the scorer
    has no false-refusal count, so a refused expected-serve case is invisible in all eight; the Master directive §V
    requires it, so it is reported beside them, fixed here before any live run."""
    if observed.get("status") in (None, "UNKNOWN", "NOT_RECOVERABLE"):
        return None
    status, outcome = observed["status"], expected["outcome"]
    if outcome == "SERVED":
        rec = {"case_id": "-", "expected": expected, "observed": observed}
        return status == "SERVED" and not _score([rec])["per_case"][0]["wrong_served"]
    if outcome == "CLARIFY":
        return status == "CLARIFY" and observed.get("clarification_code") in expected["allowed_clarification_codes"]
    if outcome == "REFUSED_UNSUPPORTED":
        return status == "REFUSED" and bool(observed.get("is_unsupported_code"))
    # REFUSED_INCONSISTENT: refused BECAUSE the givens contradict (the paired harness's CONTRADICTORY_DATA rule) — a
    # refusal for an unread quote or a failed extraction is the right status for the wrong reason
    return status == "REFUSED" and observed.get("refusal_group") == "INVALID_DATA"


def attribute(row: dict[str, Any], gold_observed: dict[str, Any], gold_code: str | None, gold_raw: Any) -> str | None:
    """First divergent layer of a failed row, by reproduction with the gold extraction (Master directive §VII). The
    deterministic layers are blamed only when the gold run ends in the SAME status and code, and a wrong serve only when
    the live extraction also carries the gold's facts — otherwise it got past the gate on its own reading."""
    if row["technical_failure"]:
        return "INFRASTRUCTURE"
    if row["end_to_end_correct"]:
        return None
    if row.get("failure_stage") == "domain_gate":
        return "DOMAIN_GATE"                                       # text-only gate: no extraction involved
    gold, got = project(gold_raw), project(row.get("raw_extraction"))
    same = (row["observed"].get("status"), row.get("hybrid_code")) == (gold_observed.get("status"), gold_code)
    if same and not end_to_end_correct(row["expected"], gold_observed) and (
            row["observed"].get("status") != "SERVED" or (gold is not None and gold == got)):
        # a refusal the gold run reproduces; or a wrong serve of the SAME facts as gold (engine / verification fault)
        return "DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD"
    if gold is None or got is None or gold != got or not row["observed"].get("quotes_verbatim_in_raw", True):
        return "LLM_EXTRACTION_DIFFERS_FROM_GOLD"                 # facts, goals or a non-verbatim quote
    return "UNATTRIBUTED"


#: C15 R-1 label of a row whose gold reproduction ends the same way, by the refusal group of its code. The public refusal
#: surface does not say which of bridge / Source Gate / planner refused, so only PLAN_TOO_LARGE is the planner's own.
_LAYER_BY_GROUP = {"EXTRACTION_FAILED": "REPRESENTATION_BLOCKED", "SOURCE_UNVERIFIED": "SOURCE_GROUNDING_FAILURE",
                   "CAPABILITY": "MISSING_PRIMITIVE", "RESULT_UNVERIFIED": "KERNEL_VERIFICATION_FAILURE",
                   "INCONCLUSIVE": "KERNEL_VERIFICATION_FAILURE"}


#: Output operand of each point constructor a `DescribedPointSpec` kind names (the rest are its inputs).
_OUTPUT_ARG = {"midpoint": "point", "centroid": "point", "intersect_line_line": "point", "intersect_line_plane": "point",
               "orthogonal_projection": "image", "orthogonal_projection_line": "image"}
_SPEC_OPERANDS = ("segment", "polygon", "point", "plane", "line", "line1", "line2")


def _inputs(kind: str, operands: dict[str, Any]) -> tuple:
    """Kind + its input operands, each label set sorted, the operands themselves sorted (AC∩BD = BD∩AC)."""
    vals = (v if isinstance(v, list) else [v] for v in operands.values())
    return kind, tuple(sorted(tuple(sorted(str(x).strip().replace("′", "'") for x in v)) for v in vals))


def _beyond_description(steps: list[dict[str, Any]], raw: Any) -> list[dict[str, Any]]:
    """Planner-made steps that do more than build a point the extraction itself described."""
    specs = [d for d in (raw.get("described_points") or []) if isinstance(d, dict)] if isinstance(raw, dict) else []
    stated = {_inputs(str(d.get("kind")), {k: d[k] for k in _SPEC_OPERANDS if d.get(k) is not None}) for d in specs}
    return [s for s in steps if _inputs(str(s.get("fn")), {k: v for k, v in (s.get("args") or {}).items()
                                                            if k != _OUTPUT_ARG.get(s.get("fn"))}) not in stated]


def composition_label(row: dict[str, Any]) -> str:
    """R-1 (C15 directive §V): how a row was served, or the first layer that failed. The planner calls every step it
    adds its own — including the one that only builds a point the model described (review MAJOR-1) — so a served row is
    SOURCE_EXPLICIT_SEQUENCE when nothing goes beyond the description, REGISTERED_DECOMPOSITION when the rest uses only
    functions of the registered auxiliary rules, and DISCOVERED_FUNCTION_COMPOSITION only otherwise. Failures are
    labelled by layer only when the gold reproduction ends the same way."""
    from app.ai.hybrid_preview import classify_refusal
    from app.simulation.geometry_functions.registry import AUXILIARY_RULES

    if row["technical_failure"]:
        return "NOT_ESTABLISHED"
    if row["observed"].get("status") == "SERVED" and not row["end_to_end_correct"]:
        return "WRONG_SERVED"
    if row["end_to_end_correct"]:
        if row["expected"]["outcome"] != "SERVED":
            return "CORRECT_REFUSAL"
        search = row.get("search") or {}
        kind, steps = search.get("classification"), search.get("planner_steps") or []
        if kind != "DISCOVERED_FUNCTION_COMPOSITION":
            return kind or "NOT_ESTABLISHED"
        if not steps:
            return "NOT_ESTABLISHED"                            # the planner's own label alone is not evidence
        beyond = _beyond_description(steps, row.get("raw_extraction"))
        if not beyond:
            return "SOURCE_EXPLICIT_SEQUENCE"
        # ponytail: by function name — a registered-rule function used outside its rule is counted registered too
        # (undercounts discovery, never overcounts); match the rule's step pattern if that ever matters
        registered = {fn for fns in AUXILIARY_RULES.values() for fn in fns}
        return ("REGISTERED_DECOMPOSITION" if all(s.get("fn") in registered for s in beyond)
                else "DISCOVERED_FUNCTION_COMPOSITION")
    if row["attribution"] == "LLM_EXTRACTION_DIFFERS_FROM_GOLD":
        return "EXTRACTION_FAILURE"
    if row["attribution"] != "DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD":
        return "NOT_ESTABLISHED"
    code = row.get("hybrid_code") or ""
    if code == "BRIDGE_UNSUPPORTED_DESCRIBED_POINT":
        return "REPRESENTATION_BLOCKED"
    if code == "PLAN_TOO_LARGE":
        return "PLANNER_SEARCH_FAILURE"
    return _LAYER_BY_GROUP.get(classify_refusal(code).group, "NOT_ESTABLISHED")


def described_check(gold: Any, raw: Any, text: str) -> dict[str, bool] | None:
    """R-1 (C15 directive §V 1–4): the model's OWN `DescribedPointSpec`s against the gold's, fixed before any live run.
    `None` where the gold describes no point. Operands and goals are the scorer's goal metric (`project` resolves each
    `@id` to its description), so they are not repeated here."""
    want = (gold or {}).get("described_points") or []
    if not want:
        return None
    got = [d for d in (raw.get("described_points") or []) if isinstance(d, dict)] if isinstance(raw, dict) else []
    refs = {x.strip() for x in _leaves(raw) if x.strip().startswith("@")} if isinstance(raw, dict) else set()
    return {"emitted": bool(got),
            "kinds_match": sorted(map(str, (d.get("kind") for d in got))) == sorted(d["kind"] for d in want),
            "refs_resolve": bool(refs) and refs <= {f"@{str(d.get('described_id')).strip()}" for d in got},
            "quotes_verbatim": bool(got) and all(isinstance(d.get("quote"), str) and d["quote"].strip()
                                                 and d["quote"] in text for d in got)}


def supplementary(rows: list[dict[str, Any]], study: str = "S-2") -> dict[str, Any]:
    scored = [r for r in rows if r["end_to_end_correct"] is not None]
    serve = [r for r in scored if r["expected"]["outcome"] == "SERVED"]
    strata = {s: [r for r in scored if r["stratum"] == s] for s in STUDIES[study][0]}
    checked = [r["described_check"] for r in rows if not r["technical_failure"] and r.get("described_check")]
    extra = {} if study == "S-2" else {
        "composition_labels": dict(sorted(collections.Counter(r["composition_label"] for r in rows).items())),
        "described_points": {k: _rate_or_unknown(sum(c[k] for c in checked), len(checked))
                             for k in ("emitted", "kinds_match", "refs_resolve", "quotes_verbatim")}}
    return {**extra, "note": "not a protocol §2 metric; reported beside them (Master directive §V)",
            "end_to_end_correct": _rate_or_unknown(sum(r["end_to_end_correct"] for r in scored), len(scored)),
            "gold_replay_ceiling": _rate_or_unknown(sum(bool(r["gold_replay_end_to_end_correct"]) for r in scored),
                                                    len(scored)),
            "false_refusal": _rate_or_unknown(sum(r["observed"]["status"] != "SERVED" for r in serve), len(serve)),
            "by_stratum": {s: _rate_or_unknown(sum(r["end_to_end_correct"] for r in v), len(v)) for s, v in strata.items()},
            "attribution": dict(sorted(collections.Counter(
                r["attribution"] for r in rows if r["attribution"]).items()))}


# ── live authorization (§4) ──────────────────────────────────────────────────────────────────────────────────────────

#: The six §4 gates as approval fields (plus the identity bindings). The Owner writes the file; this runner never does.
APPROVAL_FIELDS = ("pilot", "model", "paid_project_confirmed", "max_requests", "max_usd", "input_usd_per_million",
                   "output_usd_per_million", "corpus_sha256", "measured_system", "runner_sha256",
                   "paired_harness_sha256", "scorer_sha256")


def authorize_live(corpus_path: Path, approval_path: Path | None) -> dict[str, Any]:
    if os.environ.get("ALLOW_LIVE_AI") != "1" or not os.environ.get("GEMINI_API_KEY"):
        raise LiveRefused("ALLOW_LIVE_AI=1 and GEMINI_API_KEY are required")
    if approval_path is None or not approval_path.is_file():
        raise LiveRefused("an Owner approval file is required")
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    if approval.get("owner_decision") != "APPROVED_BY_USER":                   # §4.1 execution authorization
        raise LiveRefused("approval is not APPROVED_BY_USER")
    return check_approval_terms(corpus_path.read_bytes(), approval)


def check_approval_terms(corpus_bytes: bytes, approval: dict[str, Any]) -> dict[str, Any]:
    for key in APPROVAL_FIELDS:
        if key not in approval:
            raise LiveRefused(f"approval lacks {key}")
    corpus = json.loads(corpus_bytes.decode("utf-8"))
    study = study_of(corpus)
    if approval["pilot"] != study:                                               # one approval, one study (C15)
        raise LiveRefused(f"approval is not for the {study} pilot")
    if approval["paid_project_confirmed"] is not True:                           # §4.3
        raise LiveRefused("the paid project / key is not confirmed")
    if approval["corpus_sha256"] != hashlib.sha256(corpus_bytes).hexdigest():   # §4.6 data scope
        raise LiveRefused("corpus hash differs from the approved data scope")
    identity = runtime_identity()
    for key in ("model", "measured_system", "runner_sha256", "paired_harness_sha256", "scorer_sha256"):   # §4.2
        if approval[key] != identity[key]:
            raise LiveRefused(f"{key} differs from the approved one")
    cap = STUDIES[study][1]
    if type(approval["max_requests"]) is not int or not 0 < approval["max_requests"] <= cap:   # §4.4
        raise LiveRefused(f"max_requests must be an integer in 1..{cap}")
    for key in ("max_usd", "input_usd_per_million", "output_usd_per_million"):   # NaN / ≤ 0 would disable the USD cap
        v = approval[key]
        if type(v) not in (int, float) or not math.isfinite(v) or v <= 0:
            raise LiveRefused(f"{key} must be a finite positive number")
    validate_corpus(corpus)
    worst = worst_case_request_usd(corpus, approval)
    if approval["max_requests"] * worst > approval["max_usd"]:                  # §4.5
        raise LiveRefused(f"max_requests × estimated request cost ({approval['max_requests']} × {worst:.4f} USD) "
                          f"exceeds max_usd {approval['max_usd']}")
    return approval


def worst_case_request_usd(corpus: dict[str, Any], approval: dict[str, Any]) -> float:
    """Planning ESTIMATE (the enforced bound is the paired harness's per-payload `request_ceiling_usd`)."""
    from app.ai.function_calling import MAX_OUTPUT_TOKENS

    longest = max(len(c["problem_text"]) for c in corpus["cases"])
    prompt = P.MEASURED_OVERHEAD_CHARS["hybrid_extraction"] + 3 * longest + P.PROMPT_FRAMING_RESERVE
    return prompt * approval["input_usd_per_million"] / 1e6 + MAX_OUTPUT_TOKENS * approval["output_usd_per_million"] / 1e6


# ── run ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

def evaluate(corpus_path: Path, out_path: Path, approval: dict[str, Any] | None, *, sleep=time.sleep) -> dict[str, Any]:
    """`approval is None` ⇒ gold replay; otherwise live under the approved terms, re-checked against the exact corpus
    bytes run (the Owner decision and the environment are checked by `authorize_live`, the CLI's only live entry, and
    `live_transport` refuses every send unless ALLOW_LIVE_AI=1). Rows are flushed as they complete into a new file (never overwritten); a stop is reported, never hidden."""
    from app.ai import gemini
    from app.ai.telemetry import reset_usage, usage_report
    from app.ai.typed_fact_next_extraction import ReplayExtractor, TransportExtractor

    live = approval is not None
    corpus_bytes = corpus_path.read_bytes()
    if live:
        check_approval_terms(corpus_bytes, approval)
    corpus = json.loads(corpus_bytes.decode("utf-8"))
    validate_corpus(corpus)
    study = study_of(corpus)
    identity = runtime_identity()
    sink = out_path.open("x", encoding="utf-8", newline="\n")

    def emit(record: dict[str, Any]) -> None:
        sink.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        sink.flush()

    klass = "LIVE_DEVELOPMENT_PILOT" if live else "OFFLINE_DETERMINISTIC_FIXTURE_TEST"
    emit({"type": "header", "study": study, "measurement_class": klass,
          "corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
          "runtime_identity": identity})
    budget = P._cost_capped_budget(approval) if live else None
    gemini.set_budget(budget)
    undo_guard = P._guard_sends(budget, approval) if live else (lambda: None)
    rows: list[dict[str, Any]] = []
    spent, streak, stop_reason = 0.0, 0, None
    try:
        for case in corpus["cases"]:
            if live and runtime_identity() != identity:
                stop_reason = "IDENTITY_CHANGED"
                break
            reset_usage()
            if budget is not None:
                budget.start_arm(spent)
            start = time.perf_counter()
            technical, extra = False, {}
            try:
                if live:
                    extractor = TransportExtractor(P.hybrid_transport(os.environ["GEMINI_API_KEY"], sleep=sleep))
                    observed, extra = observe(case["problem_text"], extractor, deadline_s=P.HYBRID_LIVE_DEADLINE_S)
                else:
                    gold = case.get("gold_extraction")
                    observed, extra = observe(case["problem_text"],
                                              ReplayExtractor({case["problem_text"]: gold} if gold else {}))
                technical = observed.get("status") == "NOT_RECOVERABLE"
            except Exception as exc:  # noqa: BLE001 — infrastructure, never a model or geometry result
                technical, observed, extra = True, {"status": "NOT_RECOVERABLE"}, {"exception": type(exc).__name__}
            usage = usage_report()
            upper = budget.arm_upper() if budget is not None else "UNKNOWN"
            row = {"type": "row", "case_id": case["id"], "stratum": case["stratum"],
                   "latency_s": time.perf_counter() - start, "usage": usage or "UNKNOWN",
                   "http_requests": (budget.http_requests - budget.arm_start_requests) if budget else 0,
                   "usd": (P.usd(usage, approval) if usage or not live
                           else 0.0 if budget.http_requests == budget.arm_start_requests else "UNKNOWN"),
                   "usd_upper": upper, "technical_failure": technical,
                   "expected": expected_record(case), "observed": observed, **extra}
            row["end_to_end_correct"] = end_to_end_correct(row["expected"], observed)
            gold = case.get("gold_extraction")              # offline reproduction, 0 requests (budget not involved)
            gold_observed, gold_extra = observe(case["problem_text"],
                                                ReplayExtractor({case["problem_text"]: gold} if gold else {}))
            row["gold_replay_status"] = gold_observed.get("status")
            row["gold_replay_end_to_end_correct"] = end_to_end_correct(row["expected"], gold_observed)
            row["attribution"] = attribute(row, gold_observed, gold_extra.get("hybrid_code"), gold)
            if study != "S-2":
                row["composition_label"] = composition_label(row)
                row["described_check"] = described_check(gold, row.get("raw_extraction"), case["problem_text"])
            rows.append(row)
            emit(row)
            spent += upper if isinstance(upper, float) else 0.0
            streak = streak + 1 if technical else 0
            if budget is not None and budget.aborted:
                stop_reason = budget.stop_reason or "REQUEST_CAP"
            elif extra.get("hybrid_code") in P.PROVIDER_BLOCK:
                stop_reason = "PROVIDER_BLOCK"
            elif streak >= 3:                                                    # §4.4 circuit breaker
                stop_reason = "INFRASTRUCTURE_STREAK"
            if stop_reason:
                break
    except BaseException as exc:
        stop_reason = f"INTERRUPTED:{type(exc).__name__}"
        raise
    finally:
        undo_guard()
        gemini.set_budget(None)
        score = _score([{"case_id": r["case_id"], "expected": r["expected"],
                                         "observed": r["observed"]} for r in rows])
        latencies = [r["latency_s"] for r in rows if not r["technical_failure"]]
        complete = stop_reason is None and len(rows) == len(corpus["cases"])
        out = {"type": "summary", "study": study, "measurement_class": klass, "stop_reason": stop_reason,
               "run_status": "COMPLETE" if complete else "INCOMPLETE",
               "completed": complete,
               "cases_run": len(rows), "cases_planned": len(corpus["cases"]),
               "http_requests": budget.http_requests if budget else 0,
               "spent_upper_usd": spent if live else 0.0,
               "spent_reported_usd": ("NOT_MEASURED" if not live else "UNKNOWN"
                                      if any(not isinstance(r["usd"], float) for r in rows)
                                      else sum(r["usd"] for r in rows)),
               "latency_median_s": P._quantile(latencies, 0.5) if live else "NOT_MEASURED",
               "latency_p90_s": P._quantile(latencies, 0.9) if live else "NOT_MEASURED",
               "score": score, "supplementary": supplementary(rows, study)}
        emit(out)
        sink.close()
    return {**out, "runtime_identity": identity, "rows": rows}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--corpus", type=Path, required=True)
    p.add_argument("--out", type=Path)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--manifest", action="store_true", help="validate the corpus, print the identity to bind; no run")
    p.add_argument("--approval-file", type=Path)
    a = p.parse_args(argv)
    if a.manifest:
        validate_corpus(json.loads(a.corpus.read_text(encoding="utf-8")))
        print(json.dumps({"corpus_sha256": sha256_file(a.corpus), "runtime_identity": runtime_identity(),
                          "approval_fields": ["owner_decision", *APPROVAL_FIELDS]}, ensure_ascii=False, indent=1))
        return 0
    if a.out is None:
        p.error("--out is required for a run")
    approval = authorize_live(a.corpus, a.approval_file) if a.live else None
    if approval is not None:
        P.claim_approval(a.approval_file, a.out)
    out = evaluate(a.corpus, a.out, approval)
    print(json.dumps({k: out[k] for k in ("measurement_class", "stop_reason", "completed", "cases_run",
                                          "http_requests", "spent_upper_usd")}
                     | {"metrics": out["score"]["metrics"], "supplementary": out["supplementary"]},
                     ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
