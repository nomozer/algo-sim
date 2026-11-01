# -*- coding: utf-8 -*-
"""R-1 (thirteenth continuation): unnamed described points on Hybrid `/4`, end to end; SL-3 student shorthand; the bridge's
literal-BACKSPACE regex.

R-1 runs every row through the production opt-in path `run_hybrid_offline` — verbatim quotes, bridge, Source Gate,
planner, exact engine, Adapter /4 — on the hand-authored gold extractions frozen in `r1-described-point-probe.json`
(written by `tools/r1_described_point_probe.py`, whose docstring derives each oracle by hand). No flat-route call.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import ReplayExtractor
from app.simulation.geometry_functions import typed_fact_next as T
from app.simulation.geometry_functions.typed_fact_next_bridge import _v2_plane_def_quotes

RUN = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement"
CASES = {c["id"]: c for c in json.loads((RUN / "r1-described-point-probe.json").read_text(encoding="utf-8"))["cases"]}
POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
COMPOSED = ("C1a", "C1b", "C2", "C3", "C4", "C5", "C6a", "C6b", "C7")


def _run(text, payload):
    out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
    route = out.response["route_d"]
    answers = ({k: v.get("coef") for k, v in (route.get("answer_exact") or {}).items()}
               if route["status"] == "SERVED" else None)
    return route, out.response["envelope"], answers


# ── R-1: the eleventh-continuation compositions, now on `/4` ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("cid", COMPOSED)
def test_r1_composition_is_served_exactly_on_d4_by_the_same_planner(cid):
    c = CASES[cid]
    route, _env, answers = _run(c["text"], c["payload"])
    assert route["status"] == "SERVED" and answers == c["want"]
    assert route["planner"]["search_telemetry"]["classification"] == "DISCOVERED_FUNCTION_COMPOSITION"
    kinds = {d["kind"] for d in c["payload"]["described_points"]}
    assert kinds <= {p["fn"] for p in route["source_provenance"]}          # the described point is BUILT by its function


def test_r1_named_control_is_unchanged():
    c = CASES["N1"]
    route, _env, answers = _run(c["text"], c["payload"])
    assert answers == c["want"] and route["planner"]["search_telemetry"]["classification"] == "REGISTERED_DECOMPOSITION"


def test_r1_one_described_point_shared_by_two_goals_is_built_once():
    route, _env, answers = _run(CASES["C4"]["text"], CASES["C4"]["payload"])
    assert answers == {"q1": "3√34/5", "q2": "36/25"}
    assert [p["fn"] for p in route["source_provenance"]].count("orthogonal_projection_line") == 1


@pytest.mark.parametrize("cid", ["D1", "D2"])
def test_r1_nested_and_dual_described_points_are_representable_but_refused_typed(cid):
    c = CASES[cid]
    T._parse(T.TypedFactNextPayloadV2, c["payload"])                       # the contract represents them
    route, env, _a = _run(c["text"], c["payload"])
    assert route["status"] == "REFUSED" and env["reason_code"] == "BRIDGE_UNSUPPORTED_DESCRIBED_POINT"


@pytest.mark.parametrize("cid", [k for k in CASES if k.startswith("X")])
def test_r1_adversarial_extractions_are_never_served(cid):
    c = CASES[cid]
    route, env, _a = _run(c["text"], c["payload"])
    assert route["status"] == "REFUSED", (cid, env.get("reason_code"))


def test_r1_metamorphic_ids_and_premise_order_do_not_change_the_answer():
    c = copy.deepcopy(CASES["C2"])
    c["payload"]["premises"].reverse()
    c["payload"]["described_points"][0]["described_id"] = "giao_diem_O"
    c["payload"]["math_goals"][0]["target"]["point"] = "@giao_diem_O"
    _r, _e, answers = _run(c["text"], c["payload"])
    assert answers == CASES["C2"]["want"]


def test_r1_two_ids_for_the_same_description_are_one_point():
    c = copy.deepcopy(CASES["C4"])
    twin = dict(c["payload"]["described_points"][0], described_id="h2")
    c["payload"]["described_points"].append(twin)
    c["payload"]["math_goals"][1]["target"]["point"] = "@h2"
    route, _e, answers = _run(c["text"], c["payload"])
    assert answers == CASES["C4"]["want"]
    assert [p["fn"] for p in route["source_provenance"]].count("orthogonal_projection_line") == 1


def test_r1_a_degenerate_description_is_refused_by_the_engine_not_served():
    text = CASES["C2"]["text"].replace("giao điểm của AC và BD", "giao điểm của AB và CD")
    p = copy.deepcopy(CASES["C2"]["payload"])
    p["problem_text"] = text
    p["math_goals"][0]["quote"] = p["math_goals"][0]["quote"].replace("AC và BD", "AB và CD")
    p["described_points"][0].update(quote="giao điểm của AB và CD", line1=["A", "B"], line2=["C", "D"])
    route, env, _a = _run(text, p)
    assert route["status"] == "REFUSED", env.get("reason_code")          # AB ∥ CD: no intersection exists


def _with(base_id, **described):
    p = copy.deepcopy(CASES[base_id]["payload"])
    p["described_points"][0].update(described)
    return p


@pytest.mark.parametrize("mutate,code", [
    (lambda p: p["math_goals"][0]["target"].update(point="@nope"), "UNKNOWN_DERIVED_REFERENCE"),
    (lambda p: p["math_goals"][0]["target"].update(point="A"), "DANGLING_DEPENDENCY"),
    (lambda p: p["math_goals"][0]["target"].update(plane=["@o1", "B", "C"]), "INVALID_DESCRIBED_POINT"),
    (lambda p: p["premises"][0]["args"].update(vertices=["@o1", "B", "C", "D"]), "INVALID_DESCRIBED_POINT"),
    (lambda p: p["described_points"][0].update(line2=["@o1", "D"]), "INVALID_DESCRIBED_POINT"),       # self reference
    (lambda p: p["described_points"][0].update(point="A"), "INVALID_DESCRIBED_POINT"),               # foreign field
    (lambda p: p["described_points"][0].update(line1=["A", "A"]), "INVALID_DESCRIBED_POINT"),        # repeated operand
    (lambda p: p["described_points"].append(dict(p["described_points"][0])), "INVALID_DESCRIBED_POINT"),   # dup id
])
def test_r1_contract_refuses_malformed_described_points(mutate, code):
    p = copy.deepcopy(CASES["C2"]["payload"])
    mutate(p)
    with pytest.raises(T.TypedFactNextValidationError) as e:
        T._parse(T.TypedFactNextPayloadV2, p)
    assert e.value.code == code


def test_r1_cycles_and_depth_are_bounded():
    p = copy.deepcopy(CASES["D1"]["payload"])
    p["described_points"][1]["segment"] = ["S", "@h1"]                    # h1 → m1 → h1
    with pytest.raises(T.TypedFactNextValidationError) as e:
        T._parse(T.TypedFactNextPayloadV2, p)
    assert e.value.code == "DEPENDENCY_CYCLE"
    p = copy.deepcopy(CASES["D1"]["payload"])
    p["described_points"][1]["segment"] = ["S", "@n1"]
    p["described_points"].append({"described_id": "n1", "kind": "midpoint", "quote": "x", "segment": ["S", "C"]})
    with pytest.raises(T.TypedFactNextValidationError) as e:
        T._parse(T.TypedFactNextPayloadV2, p)
    assert e.value.code == "PLAN_TOO_LARGE"


def test_r1_typed_fact_next_1_still_refuses_a_described_ref():
    p = copy.deepcopy(CASES["C2"]["payload"])
    p["schema_version"] = "typed-fact-next/1"
    p.pop("described_points")
    with pytest.raises(T.TypedFactNextValidationError) as e:
        T._parse(T.TypedFactNextPayload, p)
    assert e.value.code == "INVALID_MATH_GOAL"


# ── SL-3: student shorthand ─────────────────────────────────────────────────────────────────────────────────────────

S2 = {c["id"]: c for c in json.loads((RUN / "s2-student-language-pilot-corpus.json").read_text(encoding="utf-8"))["cases"]}


@pytest.mark.parametrize("cid,want", [("S2-F-F05_kc_mp_shorthand", {"mg1": "√2"}),
                                      ("S2-F-F06_dt_mp_shorthand", {"mg1": "2/3"})])
def test_sl3_shorthand_is_read_where_its_object_follows(cid, want):
    c = S2[cid]
    route, env, answers = _run(c["problem_text"], c["gold_extraction"])
    assert route["status"] == "SERVED", env.get("reason_code")
    assert answers == want


def _kc(text, quote, target):
    c = copy.deepcopy(S2["S2-F-F05_kc_mp_shorthand"])
    p = c["gold_extraction"]
    p["problem_text"] = c["problem_text"].replace("Tính k/c từ A đến mp(SBC).", text)
    p["math_goals"][0].update(quote=quote, target=target)
    return p["problem_text"], p


@pytest.mark.parametrize("text,quote,target", [
    ("Tính k/c từ A đến mp(SBD).", "Tính k/c từ A đến mp(SBD)", {"point": "A", "plane": ["S", "B", "C"]}),   # wrong plane
    ("Tính kk/c từ A đến mp(SBC).", "Tính kk/c từ A đến mp(SBC)", {"point": "A", "plane": ["S", "B", "C"]}),  # not a token
    ("Tính k/c từ A đến mp.", "Tính k/c từ A đến mp", {"point": "A", "plane": ["S", "B", "C"]}),            # no operand
    ("Biết k/c từ A đến mp(SBC) bằng 3. Tính thể tích khối chóp.", "Biết k/c từ A đến mp(SBC) bằng 3",
     {"point": "A", "plane": ["S", "B", "C"]}),                                                         # a given, not asked
])
def test_sl3_shorthand_never_names_a_missing_or_different_object(text, quote, target):
    t, p = _kc(text, quote, target)
    route, env, _a = _run(t, p)
    assert route["status"] == "REFUSED", env.get("reason_code")


def test_sl3_dt_needs_a_line_of_two_labels():
    c = copy.deepcopy(S2["S2-F-F06_dt_mp_shorthand"])
    p = c["gold_extraction"]
    t = c["problem_text"].replace("đt SC", "đt S")
    p["problem_text"] = t
    p["math_goals"][0]["quote"] = p["math_goals"][0]["quote"].replace("đt SC", "đt S")
    route, env, _a = _run(t, p)
    assert route["status"] == "REFUSED", env.get("reason_code")


def test_sl3_a_tone_typo_in_the_solid_word_stays_refused():
    """"hình chop" is diacritic restoration (S-1, an Owner policy): not guessed here."""
    c = S2["S2-F-S07_typo_tone"]
    route, env, _a = _run(c["problem_text"], c["gold_extraction"])
    assert route["status"] == "REFUSED" and env["reason_code"] == "UNGROUNDED_VALUE"


# ── the literal BACKSPACE regex of `_v2_plane_def_quotes` ──────────────────────────────────────────────────────────

BASE = ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 2. "
        "Gọi M là trung điểm của SA. ")
DECL = "Mặt phẳng (P) đi qua M và song song với mặt phẳng (SBC)."
IMP = "Dựng mặt phẳng (P) đi qua M và song song với mặt phẳng (SBC)."
OTHER = "Dựng mặt phẳng (P) đi qua M và song song với mặt phẳng (SAD)."
ASK = "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (P)"


def _sec():
    return T.DerivedPlaneSectionSpecV2(section_id="sec1", plane_name="P", target_solid_id="s1",
                                       plane_kind="through_point_parallel_plane", through_point="M",
                                       parallel_plane=("S", "B", "C"), quote=ASK)


def test_bridge_source_holds_no_control_byte():
    src = (Path(__file__).resolve().parents[2] / "app/simulation/geometry_functions/typed_fact_next_bridge.py").read_bytes()
    assert not any(b < 0x20 and b not in (0x09, 0x0A, 0x0D) for b in src)


@pytest.mark.parametrize("text,want", [
    (BASE + DECL + " " + ASK + ".", [DECL]),
    (BASE + IMP + " " + ASK + ".", [IMP]),                     # the only definition: kept (skipping it would refuse)
    (BASE + DECL + " " + IMP + " " + ASK + ".", [DECL]),       # an imperative restating it: the same plane (RED before)
    (BASE + DECL + " " + OTHER + " " + ASK + ".", []),         # a different definition: ambiguous, none chosen
])
def test_plane_definition_quote_restatement_rule(text, want):
    assert _v2_plane_def_quotes(_sec(), text) == want
