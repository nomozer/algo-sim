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
import shutil
import subprocess
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
           "R-1": (("R1-A", "R1-B", "R1-C", "R1-D", "R1-E", "R1-F", "R1-G"), 18),   # unnamed described points (C14)
           # C19: what C17/C18 opened — planes given by constraints, points named by a property (orthocenter, circumcenter)
           "K-1": (("K-A", "K-B", "K-C", "K-D", "K-E"), 16),
           # C19 `hybrid-only-independent-evaluation/1`: the held-out benchmark groups; live needs Owner-attested authorship
           "H-1": (("H-POLY", "H-CURVED", "H-COMPOSITE", "H-SECTION", "H-DESCRIBED", "H-CONSTRAINT", "H-DEFINITION",
                    "H-MULTI", "H-MISSING", "H-CONTRA", "H-AMBIG", "H-OUT", "H-NONUNIQUE"), 60)}
#: C19: end-to-end outcome of one row, Hybrid-only taxonomy (`hybrid-only-independent-evaluation-protocol.md` §4).
HYBRID_OUTCOMES = ("SERVED_CORRECT", "SERVED_WRONG", "CORRECT_REFUSAL", "FALSE_REFUSAL", "WRONG_REASON_REFUSAL",
                   "CORRECT_CLARIFICATION", "WRONG_REASON_CLARIFICATION", "FALSE_CLARIFICATION", "REASON_NOT_VERIFIED",
                   "INFRASTRUCTURE_FAILURE")
#: C19: REFUSED_UNDERDETERMINED — refused because the stated givens fix no unique object (refusal group MISSING_DATA), e.g. a
#: plane the stated constraints leave free; only the engine can see it, so no model clarification is expected.
OUTCOMES = ("SERVED", "CLARIFY", "REFUSED_UNSUPPORTED", "REFUSED_INCONSISTENT", "REFUSED_UNDERDETERMINED")
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


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
        # C19 review MAJOR-2: goal and operand matching exists only against a gold, so in H-1 a SERVED case without one
        # could be "correct" with a dropped goal; the gold is part of the frozen expectation, confirmed by the author
        # review round 2 MAJOR-C: the gold also fixes the RIGHT reason of a refusal or clarification — every H-1 case needs one
        if study_of(corpus) == "H-1" and gold is None:
            raise LiveRefused(f"{c['id']}: every H-1 case needs its author-confirmed gold extraction")
        if study_of(corpus) == "H-1" and e["outcome"] == "CLARIFY" and not gold.get("unresolved"):
            raise LiveRefused(f"{c['id']}: an H-1 CLARIFY gold names its ambiguous wording in `unresolved`")
    if study_of(corpus) == "H-1":
        if set(strata) - {c.get("stratum") for c in cases}:       # review MINOR-4: no stratum is dropped
            raise LiveRefused(f"an H-1 corpus covers every stratum: missing {sorted(set(strata) - {c.get('stratum') for c in cases})}")
        if (corpus.get("authoring") or {}).get("gold_confirmed_by_author") is not True:
            raise LiveRefused("an H-1 corpus needs its gold extractions confirmed by the author before the freeze")


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
    if outcome == "REFUSED_UNDERDETERMINED":
        return status == "REFUSED" and observed.get("refusal_group") == "MISSING_DATA"
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
    """Kind + its input operands, each label set sorted, the operands themselves sorted (AC∩BD = BD∩AC); a scope
    qualifier `s1::B` is the label `B` (review round 2, MINOR-A)."""
    vals = (v if isinstance(v, list) else [v] for v in operands.values())
    return kind, tuple(sorted(tuple(sorted(str(x).split("::")[-1].strip().replace("′", "'") for x in v)) for v in vals))


def _beyond_description(steps: list[dict[str, Any]], raw: Any) -> list[dict[str, Any]]:
    """Planner-made steps that do more than build a point the extraction itself described, or restate a definition the
    source's solid word carries (`planner.DEFINITION_FUNCTIONS`: the regular base of "hình lập phương" — review MINOR-3)."""
    from app.simulation.geometry_functions.planner import DEFINITION_FUNCTIONS

    steps = [s for s in steps if s.get("fn") not in DEFINITION_FUNCTIONS]
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
        # C16 review MAJOR: the rule runs on EVERY served row — the planner's own label is recorded, never trusted
        steps = (row.get("search") or {}).get("planner_steps")
        if steps is None:
            return "NOT_ESTABLISHED"
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


def _constrained(payload: Any) -> list[tuple[str, tuple[str, ...]]]:
    if not isinstance(payload, dict):
        return []
    return sorted((str(c.get("kind")), tuple(sorted(str(x).split("::")[-1].strip() for x in c.get("operands") or ())))
                  for s in payload.get("derived_sections") or () if isinstance(s, dict) and s.get("plane_kind") == "constrained"
                  for c in s.get("constraints") or () if isinstance(c, dict))


def constraint_check(gold: Any, raw: Any, text: str) -> dict[str, bool] | None:
    """C19 K-1: the model's OWN plane constraints against the gold's, fixed before any live run. `None` where the gold
    states no constrained plane. A plane named by another correct triple of labels counts as different (lower bound).
    `no_invented_construction`: no described point and no section beyond the gold's — a foot, a translate or a witness the
    source never states is a construction the model must not write."""
    want = _constrained(gold)
    if not want:
        return None
    got = _constrained(raw)
    sections = [s for s in (raw.get("derived_sections") or []) if isinstance(s, dict)] if isinstance(raw, dict) else []
    return {"emitted": bool(got),
            "kinds_match": sorted(k for k, _ in got) == sorted(k for k, _ in want),
            "operands_match": got == want,
            "quotes_verbatim": bool(sections) and all(isinstance(s.get("quote"), str) and s["quote"].strip()
                                                      and s["quote"] in text for s in sections),
            "no_invented_construction": isinstance(raw, dict)
            and len(raw.get("described_points") or []) <= len((gold or {}).get("described_points") or [])
            and len(sections) <= len((gold or {}).get("derived_sections") or [])}


def _spans(text: str, quote: str) -> list[tuple[int, int]]:
    return [(m.start(), m.start() + len(quote)) for m in re.finditer(re.escape(quote), text)] if quote else []


def _same_wording(text: str, got: str, want: str) -> bool:
    """Review round 2 MAJOR-B: the live quote sits where the gold's does in the text (located spans intersect), covers MORE
    than half of the gold's words, and is at most twice as long — a shared function word ("với") or the shared relation
    ("vuông góc với") is not the same wording. Conservative: a quote naming only half of it counts as another wording."""
    words = lambda s: re.findall(r"\w+", s.lower())  # noqa: E731
    w, g = words(want), words(got)
    return (any(a < d and c < b for a, b in _spans(text, got) for c, d in _spans(text, want))
            and len(set(w) & set(g)) * 2 > len(set(w)) and len(got) <= 2 * len(want))


def reason_verified(row: dict[str, Any], gold_code: str | None, gold_raw: Any, text: str = "") -> bool | None:
    """C19 review MAJOR-1: a refusal or clarification is right for the RIGHT reason — the same refusal code AND the same
    facts as the gold replay, or EVERY `unresolved` entry on the gold's ambiguous wording (`_same_wording`). `None` where
    nothing can be compared (a SERVED expectation; no gold; a gold without `unresolved`) — and None is never counted as
    right (`hybrid_outcome`: REASON_NOT_VERIFIED; review round 2 MAJOR-C)."""
    exp = row["expected"]["outcome"]
    if exp == "SERVED":
        return None
    if row.get("failure_stage") == "domain_gate":           # refused on the text alone, before any extraction
        return row.get("hybrid_code") == gold_code
    if not isinstance(gold_raw, dict):
        return None
    if exp == "CLARIFY":
        want = [str(u.get("quote") or "").strip() for u in gold_raw.get("unresolved") or () if isinstance(u, dict)]
        raw = row.get("raw_extraction") if isinstance(row.get("raw_extraction"), dict) else {}
        got = [str(u.get("quote") or "").strip() for u in raw.get("unresolved") or () if isinstance(u, dict)]
        if not want:
            return None
        return bool(got) and all(any(_same_wording(text, g, w) for w in want) for g in got)
    # the same code is not enough: a model that drops the constraint fixing a plane gets the gold's PLANE_NOT_UNIQUE too
    # (review MAJOR-1) — the refusal must come from the gold's own facts (conservative: an equivalent but different
    # extraction counts as the wrong reason)
    return row.get("hybrid_code") == gold_code and project(gold_raw) == project(row.get("raw_extraction"))


def hybrid_outcome(row: dict[str, Any]) -> str:
    """C19: the Hybrid-only end-to-end outcome. A technical failure is never a refusal; a serve is correct only as
    `end_to_end_correct` says (every goal, exact answers, verified certificate); a refusal or clarification of a case the
    protocol expects SERVED is FALSE, of a refused case for another reason WRONG_REASON."""
    obs, exp = row["observed"].get("status"), row["expected"]["outcome"]
    status_ok = row.get("end_to_end_status_only", row["end_to_end_correct"])
    if row["technical_failure"] or status_ok is None:
        return "INFRASTRUCTURE_FAILURE"
    if obs == "SERVED":
        return "SERVED_CORRECT" if status_ok else "SERVED_WRONG"
    if exp == "SERVED":
        return "FALSE_CLARIFICATION" if obs == "CLARIFY" else "FALSE_REFUSAL"
    if not status_ok:
        return "FALSE_CLARIFICATION" if obs == "CLARIFY" else "WRONG_REASON_REFUSAL"
    if row.get("reason_verified") is None:                  # nothing to verify the reason against: never "correct"
        return "REASON_NOT_VERIFIED"
    if obs == "CLARIFY":
        return "CORRECT_CLARIFICATION" if row["reason_verified"] else "WRONG_REASON_CLARIFICATION"
    return "CORRECT_REFUSAL" if row["reason_verified"] else "WRONG_REASON_REFUSAL"


def supplementary(rows: list[dict[str, Any]], study: str = "S-2") -> dict[str, Any]:
    scored = [r for r in rows if r["end_to_end_correct"] is not None]
    serve = [r for r in scored if r["expected"]["outcome"] == "SERVED"]
    strata = {s: [r for r in scored if r["stratum"] == s] for s in STUDIES[study][0]}
    checked = [r["described_check"] for r in rows if not r["technical_failure"] and r.get("described_check")]
    extra = {} if study == "S-2" else {
        "composition_labels": dict(sorted(collections.Counter(r["composition_label"] for r in rows).items())),
        "planner_label_disagreements": [r["case_id"] for r in rows if r.get("search")
                                        and r["search"].get("classification") != r["composition_label"]],
        "described_points": {k: _rate_or_unknown(sum(c[k] for c in checked), len(checked))
                             for k in ("emitted", "kinds_match", "refs_resolve", "quotes_verbatim")}}
    if study not in ("S-2", "R-1"):                       # C19: constraint extraction (K-1, H-1)
        cons = [r["constraint_check"] for r in rows if not r["technical_failure"] and r.get("constraint_check")]
        extra["constraints"] = {k: _rate_or_unknown(sum(c[k] for c in cons), len(cons))
                                for k in ("emitted", "kinds_match", "operands_match", "quotes_verbatim",
                                          "no_invented_construction")}
    extra["hybrid_outcomes"] = {k: sum(r.get("hybrid_outcome") == k for r in rows) for k in HYBRID_OUTCOMES}
    return {**extra, "note": "not a protocol §2 metric; reported beside them (Master directive §V)",
            "end_to_end_correct": _rate_or_unknown(sum(r["end_to_end_correct"] for r in scored), len(scored)),
            "gold_replay_ceiling": _rate_or_unknown(sum(bool(r["gold_replay_end_to_end_correct"]) for r in scored),
                                                    len(scored)),
            "false_refusal": _rate_or_unknown(sum(r["observed"]["status"] != "SERVED" for r in serve), len(serve)),
            "by_stratum": {s: _rate_or_unknown(sum(r["end_to_end_correct"] for r in v), len(v)) for s, v in strata.items()},
            "attribution": dict(sorted(collections.Counter(
                r["attribution"] for r in rows if r["attribution"]).items()))}


# ── live authorization (§4 & C21 EXPLICIT_OWNER_DELEGATED_EXECUTION) ────────────────────────────────────────────────

#: The six §4 gates as approval fields (plus the identity bindings). Direct approvals are Owner-written (`APPROVED_BY_USER`
#: is never written by automation); C21 adds `EXPLICIT_OWNER_DELEGATED_EXECUTION` (`DELEGATED_DECISION`) for K-1, S-2, R-1.
APPROVAL_FIELDS = ("pilot", "model", "paid_project_confirmed", "max_requests", "max_usd", "input_usd_per_million",
                   "output_usd_per_million", "corpus_sha256", "measured_system", "runner_sha256",
                   "paired_harness_sha256", "scorer_sha256")
DELEGATED_MODE = "EXPLICIT_OWNER_DELEGATED_EXECUTION"
DELEGATED_DECISION = "DELEGATED_BY_EXPLICIT_OWNER_INSTRUCTION"
DELEGATED_AUTHORIZED_MODEL = "gemini-2.5-flash"
DELEGATED_PILOT_CAPS: dict[str, tuple[int, float]] = {"K-1": (16, 1.0), "S-2": (36, 2.0), "R-1": (18, 1.0)}
DELEGATED_SUITE_ORDER = ("K-1", "S-2", "R-1")
DELEGATED_GLOBAL_MAX_REQUESTS = 70
DELEGATED_GLOBAL_MAX_USD = 4.0
#: Owner-authorized live campaigns: id -> (max HTTP requests incl. retries, max ledger USD). C21 = 70 / 4.00 (spent 70/70
#: over runs 79bbc053, 48372208, 8853c4b0). C26 is a NEW, separate 80 / 1.00 authorization; it never resets C21.
DELEGATED_CAMPAIGNS: dict[str, tuple[int, float]] = {"C21": (DELEGATED_GLOBAL_MAX_REQUESTS, DELEGATED_GLOBAL_MAX_USD),
                                                     "C26": (80, 1.0)}
PAID_VERIFICATION_SOURCES = ("CLOUD_BILLING_API", "EXPLICIT_OWNER_PAID_ATTESTATION")
SUITE_FATAL_STOPS = {"PROVIDER_MODEL_UNAVAILABLE", "PROVIDER_AUTH_ERROR", "PROVIDER_BLOCK", "INFRASTRUCTURE_STREAK",
                     "UNAUTHORIZED_ENDPOINT_OR_MODEL", "IDENTITY_CHANGED", "CORPUS_CHANGED", "APPROVAL_CHANGED",
                     "GLOBAL_REQUEST_CAP", "GLOBAL_COST_CEILING"}
_SECRET_RE = re.compile(
    r"AIza[0-9A-Za-z_\-]{20,}|\bAQ\.[0-9A-Za-z_.\-]{16,}|\bya29\.[0-9A-Za-z_.\-]{16,}|Bearer\s+[A-Za-z0-9_.\-~+/=]{12,}"
)
_GCP_PROJECT_RE = re.compile(r"[a-z][a-z0-9\-]{4,28}[a-z0-9]")


def redact_secrets(text: str, extra_secrets: tuple[str, ...] = ()) -> str:
    out = str(text)
    for sec in extra_secrets:
        if isinstance(sec, str) and len(sec.strip()) >= 8:
            out = out.replace(sec, "[REDACTED_SECRET]").replace(sec.strip(), "[REDACTED_SECRET]")
    return _SECRET_RE.sub("[REDACTED_SECRET]", out)


def resolve_root_dotenv(repo_cwd: Path | None = None) -> Path:
    cwd = repo_cwd or BACKEND.parent
    try:
        common = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=cwd, capture_output=True, check=True,
                                text=True).stdout.strip()
        git_dir = (cwd / common).resolve()
        if git_dir.name == ".git":
            return git_dir.parent / "backend" / ".env"
    except (OSError, subprocess.CalledProcessError):
        pass
    return cwd / "backend" / ".env"


def _parse_dotenv_memory(dotenv_path: Path | None, keys: tuple[str, ...]) -> dict[str, str]:
    if dotenv_path is None or not dotenv_path.is_file():
        return {}
    found: dict[str, str] = {}
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.removeprefix("export ").strip()
        if k not in keys:
            continue
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
            v = v[1:-1]
        if v:
            found[k] = v
    return found


def load_env_credentials(dotenv_path: Path | None = None, env: dict[str, str] | None = None) -> dict[str, Any]:
    src_env = os.environ if env is None else env
    wanted = ("GEMINI_API_KEY", "GOOGLE_CLOUD_PROJECT", "GCP_PROJECT", "GOOGLE_OAUTH_ACCESS_TOKEN")
    file_vals = _parse_dotenv_memory(dotenv_path, wanted)

    def pick(*names: str) -> tuple[str | None, str]:
        for n in names:
            if val := (src_env.get(n) or "").strip():
                return val, "process_env"
        for n in names:
            if val := (file_vals.get(n) or "").strip():
                return val, "root_dotenv"
        return None, "missing"

    api_key, api_key_source = pick("GEMINI_API_KEY")
    project_id, project_source = pick("GOOGLE_CLOUD_PROJECT", "GCP_PROJECT")
    oauth_token, oauth_source = pick("GOOGLE_OAUTH_ACCESS_TOKEN")
    return {"api_key": api_key, "api_key_source": api_key_source, "project_id": project_id,
            "project_source": project_source, "oauth_token": oauth_token, "oauth_source": oauth_source}


def _default_billing_get(url: str, headers: dict[str, str], timeout: float) -> tuple[int, Any]:
    import httpx
    res = httpx.get(url, headers=headers, timeout=timeout)
    try:
        return res.status_code, res.json()
    except ValueError:
        return res.status_code, None


def verify_paid_project(*, project_id: str | None = None, oauth_token: str | None = None,
                        attestation_path: Path | None = None, repo_root: Path | None = None,
                        http_get=None) -> dict[str, Any]:
    """Trustworthy paid-project check (C21 §I/§IV). Presence of `GEMINI_API_KEY` or `.env` NEVER confirms paid billing."""
    if project_id and not _GCP_PROJECT_RE.fullmatch(project_id):
        return {"verified": False, "stop_reason": "PAID_PROJECT_NOT_VERIFIED",
                "detail": "invalid Google Cloud project_id format"}
    if attestation_path is not None:
        if not attestation_path.is_file():
            return {"verified": False, "stop_reason": "PAID_PROJECT_NOT_VERIFIED",
                    "detail": "paid-project attestation file does not exist"}
        try:
            att = json.loads(attestation_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"verified": False, "stop_reason": "PAID_PROJECT_NOT_VERIFIED",
                    "detail": "paid-project attestation file is unreadable"}
        att_proj = (att.get("project_id") or "").strip() if isinstance(att, dict) else ""
        stmt_ref = att.get("statement_ref", "").strip() if isinstance(att, dict) and isinstance(att.get("statement_ref"), str) else ""
        stmt_quote = att.get("statement_quote", "").strip() if isinstance(att, dict) and isinstance(att.get("statement_quote"), str) else ""
        if not (isinstance(att, dict)
                and att.get("schema") == "owner-paid-project-attestation/1"
                and att.get("authorization_source") == "EXPLICIT_OWNER_SEPARATE_STATEMENT"
                and att.get("paid_project_confirmed") is True
                and stmt_ref and stmt_ref != "CONTINUATION_21_MASTER_DIRECTIVE"
                and len(stmt_quote) >= 10
                and (not att_proj or _GCP_PROJECT_RE.fullmatch(att_proj))):
            return {"verified": False, "stop_reason": "PAID_PROJECT_NOT_VERIFIED",
                    "detail": "paid-project attestation lacks required separate explicit Owner confirmation fields"}
        if project_id and att_proj and project_id != att_proj:
            return {"verified": False, "stop_reason": "PAID_PROJECT_NOT_VERIFIED",
                    "detail": "project_id mismatch between environment and paid-project attestation"}
        resolved_att = attestation_path.resolve()
        root = (repo_root or BACKEND.parent).resolve()
        try:
            stored_att_path = resolved_att.relative_to(root).as_posix()
        except ValueError:
            stored_att_path = str(resolved_att)
        return {"verified": True, "source": "EXPLICIT_OWNER_PAID_ATTESTATION",
                "attestation_sha256": sha256_file(attestation_path),
                "attestation_path": stored_att_path,
                "statement_ref": stmt_ref,
                "project_id": att_proj or project_id}
    token = (oauth_token or "").strip() or None
    if token and token.startswith(("AIza", "AQ.")):
        return {"verified": False, "stop_reason": "PAID_PROJECT_NOT_VERIFIED",
                "detail": "Cloud Billing OAuth access token cannot be a Gemini API key"}
    if project_id and not token and http_get is None and shutil.which("gcloud"):
        try:
            proc = subprocess.run(["gcloud", "auth", "application-default", "print-access-token"],
                                  capture_output=True, text=True, timeout=10, check=False)
            if proc.returncode == 0 and proc.stdout.strip():
                token = proc.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            token = None
    if project_id and token:
        getter = http_get or _default_billing_get
        try:
            status, body = getter(f"https://cloudbilling.googleapis.com/v1/projects/{project_id}/billingInfo",
                                  {"Authorization": f"Bearer {token}"}, 15.0)
        except Exception as exc:  # noqa: BLE001
            return {"verified": False, "stop_reason": "PAID_PROJECT_NOT_VERIFIED",
                    "detail": redact_secrets(f"Cloud Billing API error: {type(exc).__name__}", (token,))}
        if (status == 200 and isinstance(body, dict) and body.get("billingEnabled") is True
                and body.get("projectId") == project_id):
            return {"verified": True, "source": "CLOUD_BILLING_API", "project_id": project_id, "billing_enabled": True}
        return {"verified": False, "stop_reason": "PAID_PROJECT_NOT_VERIFIED",
                "detail": f"Cloud Billing API did not confirm active billing (status={status}, "
                          f"billingEnabled={body.get('billingEnabled') if isinstance(body, dict) else None})"}
    return {"verified": False, "stop_reason": "PAID_PROJECT_NOT_VERIFIED",
            "detail": "No Cloud Billing API credentials/project_id and no separate explicit Owner paid-project "
                      "attestation; GEMINI_API_KEY/.env presence never implies paid billing."}


def _check_delegated_terms(study: str, approval: dict[str, Any]) -> None:
    if approval.get("authorization_mode") != DELEGATED_MODE or approval.get("owner_decision") != DELEGATED_DECISION:
        raise LiveRefused("delegated approval must pair EXPLICIT_OWNER_DELEGATED_EXECUTION with its delegated decision")
    if study not in DELEGATED_PILOT_CAPS:
        raise LiveRefused(f"{study} is outside EXPLICIT_OWNER_DELEGATED_EXECUTION scope; separate Owner approval needed")
    if approval["model"] != DELEGATED_AUTHORIZED_MODEL:
        raise LiveRefused(f"delegated model must be {DELEGATED_AUTHORIZED_MODEL}")
    req_cap, usd_cap = DELEGATED_PILOT_CAPS[study]
    if approval["max_requests"] > req_cap:
        raise LiveRefused(f"delegated max_requests exceeds {study} cap {req_cap}")
    if approval["max_usd"] > usd_cap:
        raise LiveRefused(f"delegated max_usd exceeds {study} cap {usd_cap}")
    d = approval.get("delegation")
    if not isinstance(d, dict) or d.get("authorization_source") != "EXPLICIT_OWNER_INSTRUCTION":
        raise LiveRefused("delegated approval lacks EXPLICIT_OWNER_INSTRUCTION provenance")
    for k in ("directive_id", "candidate_commit", "issued_at"):
        if not isinstance(d.get(k), str) or not d[k].strip():
            raise LiveRefused(f"delegation lacks {k}")
    if d.get("authorized_model") != DELEGATED_AUTHORIZED_MODEL:
        raise LiveRefused("delegation authorized_model invalid")
    pilots = d.get("authorized_pilots")
    if not (isinstance(pilots, list) and pilots and set(pilots) <= set(DELEGATED_PILOT_CAPS) and study in pilots):
        raise LiveRefused("delegation authorized_pilots invalid")
    campaign = d.get("campaign_id", "C21")
    if campaign not in DELEGATED_CAMPAIGNS:
        raise LiveRefused("delegation campaign_id is not an Owner-authorized campaign")
    camp_req, camp_usd = DELEGATED_CAMPAIGNS[campaign]
    g_req = d.get("global_max_requests")
    if type(g_req) is not int or not 0 < g_req <= camp_req or approval["max_requests"] > g_req:
        raise LiveRefused("delegation global_max_requests invalid")
    g_usd = d.get("global_max_usd")
    if (type(g_usd) not in (int, float) or not math.isfinite(g_usd)
            or not 0 < g_usd <= camp_usd or approval["max_usd"] > g_usd):
        raise LiveRefused("delegation global_max_usd invalid")
    if not re.fullmatch(r"[0-9a-f]{40}", str(d.get("template_git_blob") or "")):
        raise LiveRefused("delegation template_git_blob invalid")
    pv = d.get("paid_project_verification")
    if not isinstance(pv, dict) or pv.get("verified") is not True or pv.get("source") not in PAID_VERIFICATION_SOURCES:
        raise LiveRefused("delegation paid_project_verification invalid")
    if pv["source"] == "CLOUD_BILLING_API":
        if not (pv.get("billing_enabled") is True and isinstance(pv.get("project_id"), str)
                and _GCP_PROJECT_RE.fullmatch(pv["project_id"].strip())):
            raise LiveRefused("delegation paid_project_verification lacks Cloud Billing confirmation")
    elif not (re.fullmatch(r"[0-9a-f]{64}", str(pv.get("attestation_sha256") or ""))
              and isinstance(pv.get("attestation_path"), str) and pv["attestation_path"].strip()
              and isinstance(pv.get("statement_ref"), str) and pv["statement_ref"].strip()
              and pv["statement_ref"].strip() not in {d["directive_id"].strip(), "CONTINUATION_21_MASTER_DIRECTIVE"}):
        raise LiveRefused("delegation paid_project_verification lacks Owner attestation binding")
    cand_file = BACKEND.parent / "docs" / "evaluation" / "semantic-benchmark" / "EVALUATION_CANDIDATE.json"
    if cand_file.is_file():
        cand = json.loads(cand_file.read_text(encoding="utf-8"))
        if (cand.get("measured_system") or {}).get("tree_hash") != approval["measured_system"]:
            raise LiveRefused("delegated approval measured_system differs from frozen EVALUATION_CANDIDATE.json")


def authorize_live(corpus_path: Path, approval_path: Path | None,
                   *, allow_delegated: bool = False,
                   trusted_paid_verification: dict[str, Any] | None = None,
                   repo_root: Path | None = None) -> dict[str, Any]:
    if os.environ.get("ALLOW_LIVE_AI") != "1" or not os.environ.get("GEMINI_API_KEY"):
        raise LiveRefused("ALLOW_LIVE_AI=1 and GEMINI_API_KEY are required")
    if approval_path is None or not approval_path.is_file():
        raise LiveRefused("an Owner approval file is required")
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    direct = approval.get("owner_decision") == "APPROVED_BY_USER" and "authorization_mode" not in approval
    delegated = (approval.get("authorization_mode") == DELEGATED_MODE
                 and approval.get("owner_decision") == DELEGATED_DECISION)
    if not (direct or delegated):                                                # §4.1 execution authorization
        raise LiveRefused("approval is neither APPROVED_BY_USER nor EXPLICIT_OWNER_DELEGATED_EXECUTION")
    if delegated and not allow_delegated:
        raise LiveRefused("delegated approvals must run via --delegated-c21 under the global budget ledger")
    checked = check_approval_terms(corpus_path.read_bytes(), approval)
    if delegated:
        pv = checked["delegation"]["paid_project_verification"]
        if pv["source"] == "EXPLICIT_OWNER_PAID_ATTESTATION":
            raw_att = Path(pv["attestation_path"])
            apath = raw_att if raw_att.is_absolute() else (repo_root or BACKEND.parent) / raw_att
            recheck = verify_paid_project(attestation_path=apath, repo_root=repo_root)
            if not recheck["verified"] or recheck.get("attestation_sha256") != pv["attestation_sha256"]:
                raise LiveRefused("delegated paid-project attestation file is missing, altered, or invalid")
        elif pv["source"] == "CLOUD_BILLING_API":
            if trusted_paid_verification != pv:
                recheck = verify_paid_project(project_id=pv["project_id"],
                                              oauth_token=os.environ.get("GOOGLE_OAUTH_ACCESS_TOKEN"))
                if not recheck["verified"] or recheck.get("project_id") != pv["project_id"]:
                    raise LiveRefused("delegated Cloud Billing verification could not be confirmed: PAID_PROJECT_NOT_VERIFIED")
    return checked


def check_approval_terms(corpus_bytes: bytes, approval: dict[str, Any]) -> dict[str, Any]:
    for key in APPROVAL_FIELDS:
        if key not in approval:
            raise LiveRefused(f"approval lacks {key}")
    corpus = json.loads(corpus_bytes.decode("utf-8"))
    study = study_of(corpus)
    if approval["pilot"] != study:                                               # one approval, one study (C15)
        raise LiveRefused(f"approval is not for the {study} pilot")
    if study == "H-1":                      # C19: held-out only when the Owner attests an author independent of the build
        a = corpus.get("authoring") or {}
        if not (isinstance(a.get("author"), str) and a["author"].strip() and a.get("independence_attested_by") == "OWNER"
                and a.get("independent_of_implementer") is True):
            raise LiveRefused("an H-1 corpus needs an Owner-attested author independent of the implementer")
    if approval["paid_project_confirmed"] is not True:                           # §4.3
        raise LiveRefused("the paid project / key is not confirmed")
    if approval["corpus_sha256"] != sha256_bytes(corpus_bytes):                 # §4.6 data scope
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
    if ("authorization_mode" in approval or "delegation" in approval
            or approval.get("owner_decision") == DELEGATED_DECISION):
        _check_delegated_terms(study, approval)
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


# ── two-tier budget & run ────────────────────────────────────────────────────────────────────────────────────────────

def _has_verified_usage(usage: dict[str, dict[str, int]] | None) -> bool:
    """A live response without positive prompt AND output tokens has unverified usage: never priced at 0.0 (C21 §VI)."""
    return (bool(usage)
            and sum(v.get("prompt_tokens", 0) for v in usage.values()) > 0
            and sum(v.get("candidates_tokens", 0) + v.get("thoughts_tokens", 0) for v in usage.values()) > 0)


class GlobalBudgetLedger:
    """Cross-pilot hard cap of ONE campaign (`DELEGATED_CAMPAIGNS`) guarded by an exclusive lock. `carry_from` continues
    the same campaign from an earlier ledger of it (e.g. a canary), so a campaign can never be spent twice."""

    def __init__(self, out_dir: Path, max_requests: int = DELEGATED_GLOBAL_MAX_REQUESTS,
                 max_usd: float = DELEGATED_GLOBAL_MAX_USD, *, campaign_id: str = "C21",
                 carry_from: Path | None = None) -> None:
        if campaign_id not in DELEGATED_CAMPAIGNS:
            raise LiveRefused(f"unknown campaign {campaign_id!r}")
        camp_req, camp_usd = DELEGATED_CAMPAIGNS[campaign_id]
        if type(max_requests) is not int or not 0 < max_requests <= camp_req:
            raise LiveRefused(f"global_max_requests must be in 1..{camp_req}")
        if type(max_usd) not in (int, float) or not math.isfinite(max_usd) or not 0 < max_usd <= camp_usd:
            raise LiveRefused(f"global_max_usd must be in (0, {camp_usd}]")
        out_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path = out_dir / f"{campaign_id.lower()}-global-budget-ledger.json"
        self.lock_path = out_dir / f"{campaign_id.lower()}-global-budget.lock"
        if self.ledger_path.exists() or self.lock_path.exists():
            raise LiveRefused("global budget ledger or lock already exists; refusing to share or re-spend global budget")
        self.campaign_id = campaign_id
        self.max_requests = max_requests
        self.max_usd = float(max_usd)
        self.requests_used = 0
        self.spent_upper_usd = 0.0
        self.carried_from: dict[str, Any] | None = None
        if carry_from is not None:
            prior = json.loads(carry_from.read_text(encoding="utf-8"))
            if (prior.get("campaign_id", "C21") != campaign_id or prior.get("max_requests") != max_requests
                    or prior.get("max_usd") != float(max_usd)):
                raise LiveRefused("carried ledger belongs to another campaign or other caps")
            self.requests_used = int(prior["requests_used"])
            self.spent_upper_usd = float(prior["spent_upper_usd"])
            self.carried_from = {"ledger": carry_from.name, "sha256": sha256_file(carry_from),
                                 "requests_used": self.requests_used, "spent_upper_usd": self.spent_upper_usd}
        self.pilots_recorded: list[dict[str, Any]] = []
        self._lock_held = False

    def acquire(self) -> None:
        try:
            with self.lock_path.open("x", encoding="utf-8", newline="\n") as f:
                json.dump({"pid": os.getpid(), "acquired_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, f)
        except FileExistsError as exc:
            raise LiveRefused("global budget lock already held; refusing concurrent live run") from exc
        self._lock_held = True
        if self.ledger_path.exists():
            self.release()
            raise LiveRefused("global budget ledger already exists; refusing to re-spend global budget")
        self._flush()

    def release(self) -> None:
        if self._lock_held and self.lock_path.exists():
            self.lock_path.unlink()
        self._lock_held = False

    def finish_pilot(self, study: str, http_requests: int, spent_upper: float) -> None:
        self.requests_used += int(http_requests)
        self.spent_upper_usd += float(spent_upper)
        self.pilots_recorded.append({"study": study, "http_requests": int(http_requests),
                                     "spent_upper_usd": float(spent_upper)})
        self._flush()

    def _flush(self) -> None:
        record = {"max_requests": self.max_requests, "max_usd": self.max_usd,
                  "requests_used": self.requests_used, "spent_upper_usd": self.spent_upper_usd,
                  "pilots": self.pilots_recorded}
        if self.campaign_id != "C21":                      # C21 ledgers keep their published shape
            record = {"campaign_id": self.campaign_id, **record, "carried_from": self.carried_from}
        self.ledger_path.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                                    newline="\n")


def _pilot_budget(approval: dict[str, Any], global_budget: GlobalBudgetLedger | None = None):
    from app.ai import gemini
    from app.ai.telemetry import usage_report

    class TwoTierBudget(gemini.ApiBudget):
        def __init__(self) -> None:
            super().__init__(max_api_calls=int(approval["max_requests"]))
            self.spent_before_arm = 0.0
            self.arm_ceilings: list[float] = []
            self.arm_start_requests = 0
            self.stop_reason: str | None = None
            self._pending_request_counted = False

        def start_arm(self, spent: float) -> None:
            self.spent_before_arm, self.arm_ceilings = spent, []
            self.arm_start_requests = self.http_requests
            self._pending_request_counted = False

        def arm_upper(self) -> float:
            usage = usage_report()
            verified = _has_verified_usage(usage)
            known = P.usd(usage, approval) if verified else 0.0
            reported = sum(v.get("calls", 0) for v in usage.values()) if verified else 0
            unreported = self.arm_ceilings[reported:]
            return (known if isinstance(known, float) else 0.0) + sum(unreported)

        def abort_before_send(self, reason: str, message: str) -> None:
            if self._pending_request_counted and self.http_requests > self.arm_start_requests:
                self.http_requests -= 1                     # blocked before wire send: 0 bytes left the process
                self._pending_request_counted = False
            self.aborted, self.stop_reason = True, reason
            raise gemini.BudgetExceeded(message)

        def reserve(self, ceiling: float) -> None:
            pilot_projected = self.spent_before_arm + self.arm_upper() + ceiling
            if pilot_projected > approval["max_usd"]:
                self.abort_before_send("COST_CEILING", "the next request could exceed pilot max_usd")
            if global_budget is not None and global_budget.spent_upper_usd + pilot_projected > global_budget.max_usd:
                self.abort_before_send("GLOBAL_COST_CEILING", "the next request could exceed global max_usd")
            self.arm_ceilings.append(ceiling)
            self._pending_request_counted = False

        def note_request(self, is_retry: bool) -> None:
            if global_budget is not None and global_budget.requests_used + self.http_requests + 1 > global_budget.max_requests:
                self.aborted, self.stop_reason = True, "GLOBAL_REQUEST_CAP"
                raise gemini.BudgetExceeded("the next request would exceed global max_requests")
            try:
                super().note_request(is_retry)
                self._pending_request_counted = True
            except gemini.BudgetExceeded:
                self.stop_reason = self.stop_reason or "REQUEST_CAP"
                raise

    return TwoTierBudget()


def _guard_pilot_sends(budget, approval: dict[str, Any], *, identity: dict[str, str], corpus_path: Path,
                       approval_path: Path | None = None, expected_approval_sha: str | None = None):
    import httpx
    from app.ai import gemini

    sync_post, async_post = httpx.post, httpx.AsyncClient.post
    expected_url = f"https://generativelanguage.googleapis.com/v1beta/models/{approval['model']}:generateContent"

    def preflight_each_request(url: str, payload: Any) -> None:
        if url != expected_url or gemini.MODEL != approval["model"]:
            budget.abort_before_send("UNAUTHORIZED_ENDPOINT_OR_MODEL", "endpoint or model differs from approved model")
        if runtime_identity() != identity:
            budget.abort_before_send("IDENTITY_CHANGED", "runtime identity changed before request")
        if not corpus_path.is_file() or sha256_file(corpus_path) != approval["corpus_sha256"]:
            budget.abort_before_send("CORPUS_CHANGED", "corpus bytes changed before request")
        if approval_path is not None:
            marker = approval_path.with_name(approval_path.name + ".consumed")
            if (not approval_path.is_file() or not marker.is_file()
                    or sha256_file(approval_path) != expected_approval_sha):
                budget.abort_before_send("APPROVAL_CHANGED", "approval or claim marker changed before request")
        budget.reserve(P.request_ceiling_usd(payload, approval))

    def guarded_sync(url, *args, **kwargs):
        preflight_each_request(str(url), kwargs.get("json"))
        return sync_post(url, *args, **kwargs)

    async def guarded_async(self, url, *args, **kwargs):
        preflight_each_request(str(url), kwargs.get("json"))
        return await async_post(self, url, *args, **kwargs)

    httpx.post, httpx.AsyncClient.post = guarded_sync, guarded_async

    def undo() -> None:
        httpx.post, httpx.AsyncClient.post = sync_post, async_post
    return undo


def _classify_provider_http_stop(status_code: int, error_body: Any) -> str | None:
    text = json.dumps(error_body or {}, ensure_ascii=False).lower()
    if status_code == 404 or (status_code in (400, 403)
                              and any(w in text for w in ("not found", "not supported", "model"))):
        return "PROVIDER_MODEL_UNAVAILABLE"
    if status_code in (401, 403):
        return "PROVIDER_AUTH_ERROR"
    return None


def load_reusable_rows(path: Path, corpus_path: Path, identity: dict[str, str]) -> dict[str, dict[str, Any]]:
    """Rows of an earlier LIVE run of the SAME campaign on the SAME runtime identity and corpus bytes (a canary), so a
    full run counts them instead of re-sending. Technical failures are never reused (they are re-measured)."""
    lines = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    header = lines[0] if lines and lines[0].get("type") == "header" else {}
    if header.get("measurement_class") != "LIVE_DEVELOPMENT_PILOT":
        raise LiveRefused("only live development-pilot rows can be reused")
    if header.get("runtime_identity") != identity or header.get("corpus_sha256") != sha256_file(corpus_path):
        raise LiveRefused("reused rows come from another runtime identity or corpus; a candidate change is a new run")
    return {r["case_id"]: r for r in lines if r.get("type") == "row" and not r.get("technical_failure")}


def evaluate(corpus_path: Path, out_path: Path, approval: dict[str, Any] | None, *, sleep=time.sleep,
             global_budget: GlobalBudgetLedger | None = None, approval_path: Path | None = None,
             only_case_ids: set[str] | None = None, reuse_rows: dict[str, dict[str, Any]] | None = None,
             reuse_source: str | None = None) -> dict[str, Any]:
    """`approval is None` ⇒ gold replay; otherwise live under the approved terms, re-checked against the exact corpus
    bytes run (the Owner decision and the environment are checked by `authorize_live`, the CLI's only live entry, and
    `live_transport` refuses every send unless ALLOW_LIVE_AI=1). Rows are flushed as they complete into a new file (never overwritten); a stop is reported, never hidden."""
    from app.ai import gemini
    from app.ai.function_calling import ProviderHTTPError
    from app.ai.telemetry import reset_usage, usage_report
    from app.ai.typed_fact_next_extraction import ReplayExtractor, TransportExtractor

    live = approval is not None
    corpus_bytes = corpus_path.read_bytes()
    if live:
        check_approval_terms(corpus_bytes, approval)
        if ("authorization_mode" in approval or "delegation" in approval
                or approval.get("owner_decision") == DELEGATED_DECISION) and global_budget is None:
            raise LiveRefused("delegated live execution requires GlobalBudgetLedger")
    corpus = json.loads(corpus_bytes.decode("utf-8"))
    validate_corpus(corpus)
    study = study_of(corpus)
    identity = runtime_identity()
    expected_approval_sha = sha256_file(approval_path) if (live and approval_path is not None) else None
    active_secrets = tuple(x for x in (os.environ.get("GEMINI_API_KEY"), os.environ.get("GOOGLE_OAUTH_ACCESS_TOKEN"))
                           if x)
    sink = out_path.open("x", encoding="utf-8", newline="\n")

    def emit(record: dict[str, Any]) -> None:
        sink.write(redact_secrets(json.dumps(record, ensure_ascii=False, default=str), active_secrets) + "\n")
        sink.flush()

    klass = ("OFFLINE_DETERMINISTIC_FIXTURE_TEST" if not live else "INDEPENDENT_HYBRID_EVALUATION" if study == "H-1"
             else "LIVE_DEVELOPMENT_PILOT")                                       # review MINOR-4: H-1 passed its gate
    emit({"type": "header", "study": study, "measurement_class": klass,
          "corpus_sha256": sha256_bytes(corpus_bytes),
          "runtime_identity": identity})
    budget = _pilot_budget(approval, global_budget) if live else None
    gemini.set_budget(budget)
    undo_guard = (_guard_pilot_sends(budget, approval, identity=identity, corpus_path=corpus_path,
                                     approval_path=approval_path, expected_approval_sha=expected_approval_sha)
                  if live else (lambda: None))
    rows: list[dict[str, Any]] = []
    spent, streak, stop_reason, in_arm = 0.0, 0, None, False
    planned = [c for c in corpus["cases"] if only_case_ids is None or c["id"] in only_case_ids]
    reused = 0
    try:
        for case in planned:
            if live and runtime_identity() != identity:
                stop_reason = "IDENTITY_CHANGED"
                break
            if reuse_rows and case["id"] in reuse_rows:    # measured live by this campaign's canary: never re-sent
                row = {**reuse_rows[case["id"]], "reused_from": reuse_source}
                rows.append(row)
                emit(row)
                reused += 1
                continue
            reset_usage()
            if budget is not None:
                budget.start_arm(spent)
                in_arm = True
            start = time.perf_counter()
            technical, extra, provider_http_stop = False, {}, None
            try:
                if live:
                    inner_send = P.hybrid_transport(os.environ["GEMINI_API_KEY"], sleep=sleep)

                    def tracked_send(req: dict[str, Any]) -> dict[str, Any]:
                        nonlocal provider_http_stop
                        try:
                            return inner_send(req)
                        except ProviderHTTPError as http_err:
                            provider_http_stop = _classify_provider_http_stop(http_err.status_code, http_err.body)
                            raise

                    extractor = TransportExtractor(tracked_send)
                    observed, extra = observe(case["problem_text"], extractor, deadline_s=P.HYBRID_LIVE_DEADLINE_S)
                else:
                    gold = case.get("gold_extraction")
                    observed, extra = observe(case["problem_text"],
                                              ReplayExtractor({case["problem_text"]: gold} if gold else {}))
                technical = observed.get("status") == "NOT_RECOVERABLE"
            except Exception as exc:  # noqa: BLE001 — infrastructure, never a model or geometry result
                technical, observed, extra = True, {"status": "NOT_RECOVERABLE"}, {"exception": type(exc).__name__}
            usage = usage_report()
            row_requests = (budget.http_requests - budget.arm_start_requests) if budget else 0
            reported_calls = sum(v.get("calls", 0) for v in usage.values()) if usage else 0
            verified_usage = _has_verified_usage(usage) and reported_calls == row_requests
            upper = budget.arm_upper() if budget is not None else "UNKNOWN"
            row = {"type": "row", "case_id": case["id"], "stratum": case["stratum"],
                   "latency_s": time.perf_counter() - start, "usage": usage if verified_usage else "UNKNOWN",
                   "http_requests": row_requests,
                   "usd": (P.usd(usage, approval) if (verified_usage or not live)
                           else 0.0 if row_requests == 0 else "UNKNOWN"),
                   "usd_upper": upper, "technical_failure": technical,
                   "expected": expected_record(case), "observed": observed, **extra}
            row["end_to_end_status_only"] = end_to_end_correct(row["expected"], observed)
            gold = case.get("gold_extraction")              # offline reproduction, 0 requests (budget not involved)
            gold_observed, gold_extra = observe(case["problem_text"],
                                                ReplayExtractor({case["problem_text"]: gold} if gold else {}))
            row["gold_replay_status"] = gold_observed.get("status")
            row["gold_replay_end_to_end_correct"] = end_to_end_correct(row["expected"], gold_observed)
            row["reason_verified"] = reason_verified(row, gold_extra.get("hybrid_code"), gold, case["problem_text"])
            # review round 2 MAJOR-A: ONE definition of "correct" for every summary rate, label and attribution — a
            # non-served expectation is correct only for the verified reason (the scorer's eight metrics stay status-only)
            row["end_to_end_correct"] = (row["end_to_end_status_only"]
                                         if row["expected"]["outcome"] == "SERVED" or not row["end_to_end_status_only"]
                                         else row["reason_verified"] is True)
            row["attribution"] = attribute(row, gold_observed, gold_extra.get("hybrid_code"), gold)
            if row["end_to_end_status_only"] and row["reason_verified"] is None and row["expected"]["outcome"] != "SERVED":
                row["attribution"] = "REASON_NOT_VERIFIED"           # no gold reason to compare with: not a model fault
            if study != "S-2":
                row["composition_label"] = composition_label(row)
                row["described_check"] = described_check(gold, row.get("raw_extraction"), case["problem_text"])
            if study not in ("S-2", "R-1"):
                row["constraint_check"] = constraint_check(gold, row.get("raw_extraction"), case["problem_text"])
            row["hybrid_outcome"] = hybrid_outcome(row)
            rows.append(row)
            emit(row)
            spent += upper if isinstance(upper, float) else 0.0
            in_arm = False
            streak = streak + 1 if technical else 0
            if budget is not None and budget.aborted:
                stop_reason = budget.stop_reason or "REQUEST_CAP"
            elif provider_http_stop:
                stop_reason = provider_http_stop
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
        if in_arm and budget is not None:
            spent += budget.arm_upper()
        undo_guard()
        gemini.set_budget(None)
        if global_budget is not None and budget is not None:
            global_budget.finish_pilot(study, budget.http_requests, spent)
        score = _score([{"case_id": r["case_id"], "expected": r["expected"],
                                         "observed": r["observed"]} for r in rows])
        latencies = [r["latency_s"] for r in rows if not r["technical_failure"]]
        complete = stop_reason is None and len(rows) == len(corpus["cases"])
        out = {"type": "summary", "study": study, "measurement_class": klass, "stop_reason": stop_reason,
               "run_status": "COMPLETE" if complete else "INCOMPLETE",
               "completed": complete,
               "cases_run": len(rows), "cases_planned": len(corpus["cases"]),
               "cases_not_measured": len(corpus["cases"]) - len(rows),        # C19: an unrun case is NOT_MEASURED, not 0
               "reused_rows": reused, "reused_from": reuse_source if reused else None,
               "http_requests": budget.http_requests if budget else 0,
               "spent_upper_usd": spent if live else 0.0,
               "spent_reported_usd": ("NOT_MEASURED" if not live else "UNKNOWN"
                                      if any(not isinstance(r["usd"], float) for r in rows if not r.get("reused_from"))
                                      else sum(r["usd"] for r in rows if not r.get("reused_from"))),
               "latency_median_s": P._quantile(latencies, 0.5) if live else "NOT_MEASURED",
               "latency_p90_s": P._quantile(latencies, 0.9) if live else "NOT_MEASURED",
               "score": score, "supplementary": supplementary(rows, study)}
        emit(out)
        sink.close()
    return {**out, "runtime_identity": identity, "rows": rows}


def default_c21_pilot_specs(run_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    base = run_dir or (BACKEND.parent / "docs" / "evaluation" / "geometry" / "runs"
                       / "hybrid-master-backend-replacement")
    return {
        "K-1": {"slug": "k1", "corpus_path": base / "k1-live-pilot-corpus.json",
                "template_path": base / "k1-owner-approval.template.json",
                "max_requests": 16, "max_usd": 1.0},
        "S-2": {"slug": "s2", "corpus_path": base / "s2-student-language-pilot-corpus.json",
                "template_path": base / "s2-owner-approval.template.json",
                "max_requests": 36, "max_usd": 2.0},
        "R-1": {"slug": "r1", "corpus_path": base / "r1-live-pilot-corpus.json",
                "template_path": base / "r1-owner-approval.template.json",
                "max_requests": 18, "max_usd": 1.0},
    }


def _git_blob_sha(path: Path, cwd: Path) -> str:
    return subprocess.run(["git", "hash-object", str(path)], cwd=cwd, capture_output=True, check=True,
                          text=True).stdout.strip()


def issue_delegated_approval(*, study: str, spec: dict[str, Any], out_dir: Path, git_cwd: Path,
                             directive_id: str, candidate_commit: str, global_max_requests: int,
                             global_max_usd: float, paid_verification: dict[str, Any],
                             campaign_id: str = "C21") -> tuple[Path, dict[str, Any]]:
    if paid_verification.get("verified") is not True:
        raise LiveRefused("cannot issue a delegated approval without verified paid project status")
    tpath, cpath = Path(spec["template_path"]), Path(spec["corpus_path"])
    blob = _git_blob_sha(tpath, git_cwd)
    if spec.get("expected_template_blob") and blob != spec["expected_template_blob"]:
        raise LiveRefused(f"{study} template git blob {blob} differs from expected {spec['expected_template_blob']}")
    tmpl = json.loads(tpath.read_text(encoding="utf-8"))
    if tmpl.get("owner_decision") != "PENDING_OWNER_DECISION" or tmpl.get("paid_project_confirmed") is not False:
        raise LiveRefused(f"{study} template is not in clean PENDING_OWNER_DECISION / paid=false state")
    issued_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    approval = {
        **tmpl,
        "authorization_mode": DELEGATED_MODE,
        "owner_decision": DELEGATED_DECISION,
        "paid_project_confirmed": True,
        "max_requests": min(int(spec["max_requests"]), int(global_max_requests)),
        "max_usd": min(float(spec["max_usd"]), float(global_max_usd)),
        "delegation": {
            "authorization_source": "EXPLICIT_OWNER_INSTRUCTION",
            "directive_id": directive_id,
            "authorized_pilots": list(DELEGATED_SUITE_ORDER),
            "authorized_model": DELEGATED_AUTHORIZED_MODEL,
            "candidate_commit": candidate_commit,
            "global_max_requests": int(global_max_requests),
            "global_max_usd": float(global_max_usd),
            "issued_at": issued_at,
            "template_path": str(tpath.name),
            "template_git_blob": blob,
            "paid_project_verification": paid_verification,
            **({"campaign_id": campaign_id} if campaign_id != "C21" else {}),
        },
    }
    check_approval_terms(cpath.read_bytes(), approval)
    out_dir.mkdir(parents=True, exist_ok=True)
    apath = out_dir / f"{spec['slug']}-delegated-approval.json"
    with apath.open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(approval, ensure_ascii=False, indent=1) + "\n")
    return apath, approval


def _write_sanitized_json(path: Path, payload: dict[str, Any], secrets: tuple[str, ...]) -> None:
    text = redact_secrets(json.dumps(payload, ensure_ascii=False, indent=1, default=str) + "\n", secrets)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def run_delegated_c21_suite(
    *,
    out_dir: Path,
    ledger_dir: Path | None = None,
    dotenv_path: Path | None = None,
    paid_attestation_path: Path | None = None,
    pilot_specs: dict[str, dict[str, Any]] | None = None,
    git_cwd: Path | None = None,
    directive_id: str = "CONTINUATION_21_MASTER_DIRECTIVE",
    candidate_commit: str = "15d236eb",
    global_max_requests: int = DELEGATED_GLOBAL_MAX_REQUESTS,
    global_max_usd: float = DELEGATED_GLOBAL_MAX_USD,
    billing_http_get=None,
    sleep=time.sleep,
    campaign_id: str = "C21",
    carry_ledger: Path | None = None,
    only_case_ids: dict[str, set[str]] | None = None,
    reuse_rows_from: dict[str, Path] | None = None,
) -> dict[str, Any]:
    """C21 automatic sequence: Preflight -> Paid-Project Gate -> K-1 -> S-2 -> R-1 under two-tier caps. A later
    campaign (`campaign_id`) may run a canary (`only_case_ids`) and then the full suite reusing the canary rows
    (`reuse_rows_from`) under the canary's carried ledger (`carry_ledger`)."""
    from app.ai import gemini
    from app.ai.route_policy import route_policy_snapshot

    repo_cwd = git_cwd or BACKEND.parent
    specs = pilot_specs or default_c21_pilot_specs()
    if tuple(specs) != DELEGATED_SUITE_ORDER:
        raise LiveRefused(f"delegated suite order must be {DELEGATED_SUITE_ORDER}")
    ident = runtime_identity()
    if ident["model"] != DELEGATED_AUTHORIZED_MODEL or gemini.MODEL != DELEGATED_AUTHORIZED_MODEL:
        raise LiveRefused(f"runtime model is not {DELEGATED_AUTHORIZED_MODEL}")
    if route_policy_snapshot({}).default_route_mode != "HYBRID":
        raise LiveRefused("production default mode is not HYBRID")
    cand_file = BACKEND.parent / "docs" / "evaluation" / "semantic-benchmark" / "EVALUATION_CANDIDATE.json"
    if cand_file.is_file():
        cand = json.loads(cand_file.read_text(encoding="utf-8"))
        if (cand.get("measured_system") or {}).get("tree_hash") != ident["measured_system"]:
            raise LiveRefused("measured_system differs from frozen EVALUATION_CANDIDATE.json")
        if cand.get("cache_version") != ident["cache_version"]:
            raise LiveRefused("cache_version differs from frozen EVALUATION_CANDIDATE.json")

    verified_templates: dict[str, dict[str, Any]] = {}
    for study in DELEGATED_SUITE_ORDER:
        sp = specs[study]
        cpath, tpath = Path(sp["corpus_path"]), Path(sp["template_path"])
        cbytes = cpath.read_bytes()
        corpus = json.loads(cbytes.decode("utf-8"))
        if study_of(corpus) != study:
            raise LiveRefused(f"corpus study mismatch for {study}")
        validate_corpus(corpus)
        csha = hashlib.sha256(cbytes).hexdigest()
        blob = _git_blob_sha(tpath, repo_cwd)
        if sp.get("expected_template_blob") and blob != sp["expected_template_blob"]:
            raise LiveRefused(f"{study} template blob {blob} != expected {sp['expected_template_blob']}")
        tmpl = json.loads(tpath.read_text(encoding="utf-8"))
        if tmpl.get("pilot") != study:
            raise LiveRefused(f"{study} template pilot mismatch")
        if tmpl.get("owner_decision") != "PENDING_OWNER_DECISION" or tmpl.get("paid_project_confirmed") is not False:
            raise LiveRefused(f"{study} template must have PENDING_OWNER_DECISION and paid_project_confirmed=false")
        if tmpl.get("max_requests") != int(sp["max_requests"]) or tmpl.get("max_usd") != float(sp["max_usd"]):
            raise LiveRefused(f"{study} template cap mismatch")
        if tmpl.get("corpus_sha256") != csha:
            raise LiveRefused(f"{study} template corpus_sha256 does not match corpus")
        for k in ("model", "measured_system", "runner_sha256", "paired_harness_sha256", "scorer_sha256"):
            if tmpl.get(k) != ident[k]:
                raise LiveRefused(f"{study} template {k} does not match current runtime identity")
        verified_templates[study] = {"template_name": tpath.name, "template_git_blob": blob, "corpus_sha256": csha,
                                     "cases": len(corpus["cases"]), "max_requests": int(sp["max_requests"]),
                                     "max_usd": float(sp["max_usd"])}

    resolved_dotenv = dotenv_path if dotenv_path is not None else resolve_root_dotenv(repo_cwd)
    creds = load_env_credentials(resolved_dotenv)
    secrets = tuple(x for x in (creds.get("api_key"), creds.get("oauth_token")) if x)
    paid_check = verify_paid_project(project_id=creds["project_id"], oauth_token=creds["oauth_token"],
                                     attestation_path=paid_attestation_path, repo_root=repo_cwd,
                                     http_get=billing_http_get)

    verified_conditions = [
        "candidate_product_freeze_matched",
        "default_mode_llm_only_preserved",
        "authorized_model_gemini_2_5_flash_pinned_no_fallback",
        "corpora_k1_s2_r1_validated",
        "approval_templates_k1_s2_r1_bound_to_runtime_identity",
    ]
    unverified_conditions: list[str] = []
    if creds["api_key"]:
        verified_conditions.append(f"gemini_api_key_present_via_{creds['api_key_source']}")
    else:
        unverified_conditions.append("gemini_api_key_missing")
    if paid_check["verified"]:
        verified_conditions.append(f"paid_project_verified_via_{paid_check['source'].lower()}")
    else:
        unverified_conditions.append("paid_project_billing_status_unverified")

    receipt_path = out_dir / "c21-delegated-execution-receipt.json"
    base_receipt: dict[str, Any] = {
        "schema": "c21-delegated-execution-receipt/1",
        "authorization_mode": DELEGATED_MODE,
        "authorization_source": "EXPLICIT_OWNER_INSTRUCTION",
        "directive_id": directive_id,
        "authorized_scope": list(DELEGATED_SUITE_ORDER),
        "excluded_scope": ["H-1", "PRODUCTION_CUTOVER", "MERGE_PUSH"],
        "authorized_model": DELEGATED_AUTHORIZED_MODEL,
        "candidate_commit": candidate_commit,
        "runtime_identity": ident,
        "per_pilot_caps": {k: {"max_requests": v[0], "max_usd": v[1]} for k, v in DELEGATED_PILOT_CAPS.items()},
        "global_caps": {"max_requests": int(global_max_requests), "max_usd": float(global_max_usd)},
        **({"campaign_id": campaign_id} if campaign_id != "C21" else {}),
        "executed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "credentials_summary": {"api_key_present": bool(creds["api_key"]), "api_key_source": creds["api_key_source"],
                                "project_id_present": bool(creds["project_id"]),
                                "project_source": creds["project_source"],
                                "oauth_token_present": bool(creds["oauth_token"])},
        "paid_project_verification": paid_check,
        "templates_verified": verified_templates,
        "verified_conditions": verified_conditions,
        "unverified_conditions": unverified_conditions,
    }

    if not creds["api_key"] or not paid_check["verified"]:
        blocker = "MISSING_API_KEY" if not creds["api_key"] else paid_check["stop_reason"]
        out_dir.mkdir(parents=True, exist_ok=True)
        receipt = {
            **base_receipt,
            "status": "BLOCKED_PREFLIGHT",
            "stop_reason": blocker,
            "model_availability": "NOT_MEASURED_PRE_REQUEST_GATE_BLOCKED",
            "approvals_created": [],
            "total_http_requests": 0,
            "total_spent_upper_usd": 0.0,
            "total_spent_reported_usd": "NOT_MEASURED",
            "pilots": [],
        }
        _write_sanitized_json(receipt_path, receipt, secrets)
        return receipt

    campaign_ledger_dir = ledger_dir or Path(next(iter(specs.values()))["template_path"]).parent
    ledger = GlobalBudgetLedger(campaign_ledger_dir, max_requests=global_max_requests, max_usd=global_max_usd,
                                campaign_id=campaign_id, carry_from=carry_ledger)
    prev_allow = os.environ.get("ALLOW_LIVE_AI")
    prev_key = os.environ.get("GEMINI_API_KEY")
    approvals_created: list[dict[str, Any]] = []
    pilot_summaries: list[dict[str, Any]] = []
    suite_stop: str | None = None
    interrupted = False
    receipt: dict[str, Any] = {}
    ledger.acquire()
    try:
        os.environ["ALLOW_LIVE_AI"] = "1"
        os.environ["GEMINI_API_KEY"] = creds["api_key"]
        for study in DELEGATED_SUITE_ORDER:
            sp = specs[study]
            apath, _ = issue_delegated_approval(
                study=study, spec=sp, out_dir=out_dir, git_cwd=repo_cwd, directive_id=directive_id,
                candidate_commit=candidate_commit, global_max_requests=global_max_requests,
                global_max_usd=global_max_usd, paid_verification=paid_check, campaign_id=campaign_id,
            )
            approvals_created.append({"study": study, "file": apath.name, "sha256": sha256_file(apath)})
            verified_approval = authorize_live(Path(sp["corpus_path"]), apath, allow_delegated=True,
                                               trusted_paid_verification=paid_check, repo_root=repo_cwd)
            p_out = out_dir / f"{sp['slug']}-live.jsonl"
            P.claim_approval(apath, p_out)
            reuse_path = (reuse_rows_from or {}).get(study)
            reuse = load_reusable_rows(reuse_path, Path(sp["corpus_path"]), ident) if reuse_path else None
            res = evaluate(Path(sp["corpus_path"]), p_out, verified_approval, sleep=sleep,
                           global_budget=ledger, approval_path=apath,
                           only_case_ids=only_case_ids.get(study, set()) if only_case_ids is not None else None,
                           reuse_rows=reuse, reuse_source=(reuse_path.parent.name + "/" + reuse_path.name)
                           if reuse_path else None)
            pilot_summaries.append({
                "study": study, "output_file": p_out.name, "output_sha256": sha256_file(p_out),
                "completed": res["completed"], "stop_reason": res["stop_reason"],
                "cases_run": res["cases_run"], "cases_planned": res["cases_planned"],
                "cases_not_measured": res["cases_not_measured"],
                "reused_rows": res["reused_rows"], "reused_from": res["reused_from"],
                "http_requests": res["http_requests"],
                "live_answered_rows": sum(r["http_requests"] > 0 and not r["technical_failure"] for r in res["rows"]),
                "spent_upper_usd": res["spent_upper_usd"], "spent_reported_usd": res["spent_reported_usd"],
                "latency_median_s": res["latency_median_s"], "latency_p90_s": res["latency_p90_s"],
                "metrics": res["score"]["metrics"], "supplementary": res["supplementary"],
            })
            if res["stop_reason"] in SUITE_FATAL_STOPS:
                suite_stop = res["stop_reason"]
                break
    except BaseException as exc:
        interrupted = True
        suite_stop = f"INTERRUPTED:{type(exc).__name__}"
        raise
    finally:
        if prev_allow is None:
            os.environ.pop("ALLOW_LIVE_AI", None)
        else:
            os.environ["ALLOW_LIVE_AI"] = prev_allow
        if prev_key is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = prev_key
        ledger.release()
        reported_vals = [p["spent_reported_usd"] for p in pilot_summaries]
        total_reported = ("UNKNOWN" if interrupted or not pilot_summaries
                          or any(not isinstance(v, float) for v in reported_vals)
                          else sum(reported_vals))
        complete = (not interrupted and suite_stop is None and len(pilot_summaries) == len(DELEGATED_SUITE_ORDER)
                    and all(p["completed"] for p in pilot_summaries))
        model_avail = ("PROVIDER_MODEL_UNAVAILABLE" if suite_stop == "PROVIDER_MODEL_UNAVAILABLE"
                       else "VERIFIED_LIVE" if any(p.get("live_answered_rows", 0) > 0 for p in pilot_summaries)
                       else "UNKNOWN")
        receipt = {
            **base_receipt,
            "status": "INTERRUPTED" if interrupted else "COMPLETE" if complete else "INCOMPLETE",
            "stop_reason": suite_stop or next((p["stop_reason"] for p in pilot_summaries if p["stop_reason"]), None),
            "model_availability": model_avail,
            "approvals_created": approvals_created,
            "total_http_requests": ledger.requests_used,
            "total_spent_upper_usd": ledger.spent_upper_usd,
            "total_spent_reported_usd": total_reported,
            **({"carried_ledger": ledger.carried_from} if ledger.carried_from else {}),
            "pilots": pilot_summaries,
        }
        _write_sanitized_json(receipt_path, receipt, secrets)
    return receipt


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--corpus", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--out-dir", type=Path)
    p.add_argument("--dotenv", type=Path)
    p.add_argument("--paid-attestation", type=Path)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--manifest", action="store_true", help="validate the corpus, print the identity to bind; no run")
    mode.add_argument("--delegated-c21", action="store_true",
                      help="run Continuation 21 automatic K-1 -> S-2 -> R-1 suite under EXPLICIT_OWNER_DELEGATED_EXECUTION")
    p.add_argument("--approval-file", type=Path)
    a = p.parse_args(argv)
    if a.delegated_c21:
        if a.out_dir is None:
            p.error("--out-dir is required for --delegated-c21")
        rec = run_delegated_c21_suite(out_dir=a.out_dir, dotenv_path=a.dotenv, paid_attestation_path=a.paid_attestation)
        print(json.dumps({k: rec[k] for k in ("status", "stop_reason", "model_availability", "total_http_requests",
                                              "total_spent_upper_usd", "approvals_created", "unverified_conditions")},
                         ensure_ascii=False, indent=1, default=str))
        return 0 if rec["status"] == "COMPLETE" else 2
    if a.corpus is None:
        p.error("--corpus is required unless --delegated-c21 is used")
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
    out = evaluate(a.corpus, a.out, approval, approval_path=a.approval_file if a.live else None)
    print(json.dumps({k: out[k] for k in ("measurement_class", "stop_reason", "completed", "cases_run",
                                          "http_requests", "spent_upper_usd")}
                     | {"metrics": out["score"]["metrics"], "supplementary": out["supplementary"]},
                     ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
