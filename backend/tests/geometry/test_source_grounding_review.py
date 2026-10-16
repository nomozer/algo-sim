"""Supplemental development regressions from the independent handoff review; frozen corpus labels stay unchanged."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.ai.function_route import run_fact_route
from app.ai.function_route import run_function_route
from app.simulation.geometry_functions.planner import lap_ke_hoach

RUN = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-semantic-grounding-reliability"
CASES = json.loads((RUN / "corpus.json").read_text(encoding="utf-8"))["cases"]


def case(cid):
    return deepcopy(next(c for c in CASES if c["id"] == cid))


@pytest.mark.parametrize("target", ["(SABC)", "SABC", "mặt bên SABC", "mặt đáy SABC"])
def test_every_accepted_plane_spelling_preserves_all_source_labels(target):
    c = case("C02-four-label-nonplane-named")
    c["text"] = c["text"].replace("(SABC)", target)
    q = c["payload"]["facts"][-1]
    q["quotes"] = [s.replace("(SABC)", target) for s in q["quotes"]]
    r = run_fact_route(c["text"], c["payload"])
    assert (r.status, r.code) == ("REFUSED", "SOURCE_OBJECT_MISMATCH"), r.answers


@pytest.mark.parametrize("source_plane", ["ABMS", "ABM"])
def test_shared_collinear_labels_do_not_certify_plane_identity(source_plane):
    c = case("A01-desc-plane-imperative")
    premise = "Gọi M là trung điểm của AB."
    question = f"Tính góc giữa SC và ({source_plane})."
    c["text"] = c["text"][:c["text"].index("Tính")] + premise + " " + question
    c["payload"]["facts"] = c["payload"]["facts"][:-1] + [
        dict(id="fm", kind="point_def", role="premise", quotes=[premise], point="M", point_kind="midpoint", points=["A", "B"]),
        dict(id="q", kind="question", role="question", quotes=[question], quantity="angle", points_a=["S", "C"],
             points_b=["A", "C", "B", "M"]),
    ]
    r = run_fact_route(c["text"], c["payload"])
    assert (r.status, r.code) == ("REFUSED", "SOURCE_OBJECT_MISMATCH"), r.answers


@pytest.mark.parametrize("quantity,question,planes", [
    ("angle", "Tính góc giữa SC và (ABC).", [["S", "C"], ["S", "A", "B", "C"]]),
    ("angle", "Tính góc giữa (ABC) và (SAB).", [["S", "A", "B", "C"], ["S", "A", "B"]]),
])
def test_an_extra_call_label_cannot_change_the_source_plane(quantity, question, planes):
    c = case("A01-desc-plane-imperative")
    c["text"] = c["text"][:c["text"].index("Tính")] + question
    c["payload"]["facts"][-1] = dict(id="q", kind="question", role="question", quotes=[question], quantity=quantity,
                                     points_a=planes[0], points_b=planes[1])
    plan = lap_ke_hoach(c["payload"], c["text"])
    for r in (run_fact_route(c["text"], c["payload"]), run_function_route(c["text"], {"calls": plan.calls})):
        assert (r.status, r.code) == ("REFUSED", "SOURCE_OBJECT_MISMATCH"), r.answers


@pytest.mark.parametrize("source_edge,extracted_edge,serve", [("2a", "2a", True), ("2", "2a", False), ("2a", "2", False)])
def test_symbolic_cube_edge_is_compared_after_exact_source_binding(source_edge, extracted_edge, serve):
    c = case("C09-result-line-cube")
    c["text"] = c["text"].replace("cạnh 2", "cạnh " + source_edge)
    for f in c["payload"]["facts"]:
        f["quotes"] = [q.replace("cạnh 2", "cạnh " + source_edge) for q in f["quotes"]]
        if f["kind"] == "length":
            f["value"] = extracted_edge
    r = run_fact_route(c["text"], c["payload"])
    assert (r.status == "SERVED") == serve, (r.code, r.answers)
    if serve:
        assert r.answers == {"q": "a√2"}
    else:
        assert r.code == "UNGROUNDED_VALUE"
