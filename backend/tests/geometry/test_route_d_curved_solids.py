# -*- coding: utf-8 -*-
"""Curved solids on Route D /4 (run `hybrid-master-backend-replacement`, Owner option (b); registry /23, planner /19,
engine /15). 0 provider calls.

Cases and hand-written π oracles live in `tools/curved_probe.py` (written before the implementation, RED at `23c20679`
with `BRIDGE_UNSUPPORTED_CURVED`); this file locks them. One route: bridge → the one planner → Source Gate → engine (a
canonical-pose layout step beside the polygon chart) → the existing IR / interpreter / exact kernel → Adapter /4. Every
SERVED answer equals both the executed kernel value and an independent closed form.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry.radical import from_json, parse_exact, radical

_P = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/tools/curved_probe.py"
_spec = importlib.util.spec_from_file_location("curved_probe", _P)
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

POSITIVE = [x for x in C.CASES if x[4] != "REFUSE"]
#: The refusal code each negative must carry — the RIGHT reason, not just "refused".
NEGATIVE_CODES = {
    "n.bad_slant": "INCONSISTENT_FACTS", "n.overdetermined": "INCONSISTENT_FACTS", "n.swapped": "UNGROUNDED_VALUE",
    "n.wrong_value": "UNGROUNDED_VALUE", "n.wrong_kind": "SOURCE_OBJECT_MISMATCH", "n.missing_height": "MISSING_DIMENSION",
    "n.sphere_lateral": "CURVED_MEASURE_UNDEFINED", "n.area_unqualified": "PREDICATE_NOT_IN_QUOTE",
    "n.composite": "BRIDGE_UNSUPPORTED_CURVED_COMPOSITE", "n.foreign_segment": "SOURCE_OBJECT_MISMATCH",
    "n.no_height": "SOURCE_PREMISE_UNREAD", "n.foreign_solid": "UNKNOWN_SOLID_ID",
}


@pytest.mark.parametrize("cid,fig,goal,question,oracle", POSITIVE, ids=[x[0] for x in POSITIVE])
def test_curved_measurements_are_served_exactly(cid, fig, goal, question, oracle):
    r = run_typed_fact_next_v2_route(C.payload(fig, goal, question))
    assert r.status == "SERVED" and r.kernel_check is True, (r.code, r.reason)
    assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact(oracle)
    assert any(s["step"] == "certify_answer" and s["rule"] == "independent_closed_form" for s in r.trace)


def test_a_total_area_outside_the_exact_domain_is_a_typed_refusal():
    (case,) = [x for x in C.CASES if x[4] == "REFUSE"]          # 6π√2 + 4π: two unlike terms, never rounded
    r = run_typed_fact_next_v2_route(C.payload(*case[1:4]))
    assert r.status == "REFUSED" and r.code == "EXACT_DOMAIN_EXCEEDED" and not r.answer_exact


@pytest.mark.parametrize("cid,fig,goal,question,mutate", C.NEGATIVES, ids=[x[0] for x in C.NEGATIVES])
def test_curved_negatives_are_refused_for_the_right_reason(cid, fig, goal, question, mutate):
    r = run_typed_fact_next_v2_route(C.payload(fig, goal, question, mutate))
    assert r.status == "REFUSED" and not r.answer_exact and r.scene3d is None
    assert r.code == NEGATIVE_CODES[cid], (r.code, r.reason)


#: Independent review rounds 1–2: each of these SERVED a wrong exact value or insufficient data before its fix.
ADVERSARIAL_CODES = {cid: "UNKNOWN_LABEL" if cid == "r.invented_labels" else "SOURCE_OBJECT_MISMATCH"
                     for cid, *_ in C.ADVERSARIAL}     # a quote outside the closed clause grammar binds nothing


@pytest.mark.parametrize("cid,given,solid,premises,goal,question", C.ADVERSARIAL, ids=[x[0] for x in C.ADVERSARIAL])
def test_review_reproductions_are_refused_never_served(cid, given, solid, premises, goal, question):
    r = run_typed_fact_next_v2_route(C.payload((given, solid, premises), goal, question))
    assert r.status == "REFUSED" and not r.answer_exact and r.scene3d is None
    assert r.code == ADVERSARIAL_CODES[cid], (r.code, r.reason)


def test_a_source_naming_no_point_is_served_in_the_canonical_pose():
    r = run_typed_fact_next_v2_route(C.payload(C.UNLABELLED, "volume", "Tính thể tích khối nón."))
    assert r.status == "SERVED" and parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact("12π")
    assert r.points == {}                                     # no invented point, no coordinate presented as a given


def test_slant_given_height_is_derived_and_traced():
    fig = C.CONE_L
    r = run_typed_fact_next_v2_route(C.payload(fig, "volume", "Tính thể tích khối nón."))
    (step,) = [s for s in r.trace if s["step"] == "derive_dimension"]
    assert step["object"] == "height" and step["rule"] == "pythagoras_axis_rim" and step["value_sq"] == "16"


def test_the_full_hybrid_path_shows_only_the_asked_value_as_target():
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    from app.ai.typed_fact_next_extraction import ReplayExtractor

    for fig, goal, question, oracle in ((C.CYL, "area", "Tính diện tích toàn phần của hình trụ.", "48π"),
                                        (C.SPH, "area", "Tính diện tích mặt cầu.", "36π"),
                                        (C.CONE_R, "lateral_area", "Tính diện tích xung quanh của hình nón.", "4π√2")):
        p = C.payload(fig, goal, question)
        out = run_hybrid_offline(p["problem_text"], ReplayExtractor({p["problem_text"]: p}),
                                 policy=hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"}))
        assert out.response["route_d"]["status"] == "SERVED", out.response["envelope"].get("reason_code")
        targets = [from_json(o["exact"]) for o in out.response["envelope"]["scene3d"]["objects"]
                   if o.get("type") == "quantity" and "target" in (o.get("display_group") or [])]
        assert targets == [parse_exact(oracle)]


def test_a_symbolic_unit_keeps_pi_in_the_learner_answer_and_a_diameter_is_not_guessed():
    g = "Cho hình trụ có tâm hai đáy là O và O', điểm A thuộc đường tròn đáy tâm O, bán kính đáy bằng a và chiều cao bằng 2a."
    p = C.payload((g, C.solid("cylinder", "O.O'", "O", "O'", "A", "a", "2a", g[:-1]), []), "volume", "Tính thể tích khối trụ.")
    p["length_unit"] = "a"
    r = run_typed_fact_next_v2_route(p)                       # V = π·a²·2a = 2πa³ (found: the π was dropped as "2a³")
    assert r.status == "SERVED" and r.answer_exact["mg1"] == {"coef": "2π", "dim": 3, "unit": "a"}
    assert r.answers["mg1"] == "2πa³"
    g2 = "Cho mặt cầu tâm O, điểm A thuộc mặt cầu, đường kính bằng 6."   # no role clause reads a diameter as a radius
    r2 = run_typed_fact_next_v2_route(C.payload((g2, C.solid("sphere", "O", "O", None, "A", "3", None, g2[:-1]), []),
                                                "volume", "Tính thể tích khối cầu."))
    assert r2.status == "REFUSED" and r2.code == "SOURCE_OBJECT_MISMATCH"     # "đường kính" is no clause of the grammar


def test_a_tampered_certificate_is_never_served(monkeypatch):
    from app.simulation.geometry_functions import engine as E
    monkeypatch.setattr(E, "_chung_chi_cong", lambda kind, q, r2, h2: radical(1, 1, 1))     # wrong closed form
    r = run_typed_fact_next_v2_route(C.payload(C.CYL, "volume", "Tính thể tích khối trụ."))
    assert r.status == "REFUSED" and r.code == "ENGINE_SELF_CHECK_FAILED"


def test_route_a_provider_surface_is_unchanged():
    from app.simulation.geometry_functions.registry import PROVIDER_FUNCTIONS
    assert not {"curved_solid", "ask_curved_volume", "ask_lateral_area", "ask_surface_area", "ask_radius"} & set(PROVIDER_FUNCTIONS)


def test_pi_display_and_the_identity_chart_is_euclidean():
    from fractions import Fraction

    from app.simulation.geometry import metric
    from app.simulation.geometry_functions.engine import dinh_dang
    assert [dinh_dang(radical(45, 1, 1)), dinh_dang(radical(Fraction(8, 3), 1, 1)), dinh_dang(radical(4, 2, 1))] == \
        ["45π", "8π/3", "4π√2"]
    one, zero = Fraction(1), Fraction(0)
    with metric.using(metric.Metric(((one, zero, zero), (zero, one, zero), (zero, zero, one)))):
        metric.require_euclidean("a curved solid")                  # identity Gram matrix: no refusal
    with metric.using(metric.Metric(((one, zero, zero), (zero, one, zero), (zero, zero, Fraction(4))))):
        with pytest.raises(Exception):
            metric.require_euclidean("a curved solid")
