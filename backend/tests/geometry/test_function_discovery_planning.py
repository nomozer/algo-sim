"""Run `goal-directed-function-discovery`: unnamed derived operands planned from Registry effects, real fact route only.

Corpus and squared answers are preregistered by an independent oracle (`runs/goal-directed-function-discovery/oracle.py`,
no `app` import). Registry variants change catalog DATA only — planner, gate and engine code are the same objects.
"""
from __future__ import annotations

import json
import re
import sys
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from app.ai.function_route import run_fact_route

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "docs/evaluation/geometry/runs/goal-directed-function-discovery"
CORPUS = json.loads((RUN / "corpus.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(ROOT / "backend/scripts"))
from measure_function_discovery import experimental_centroid_contract  # noqa: E402


def squared(value):
    from app.simulation.geometry.radical import Radical
    return Fraction(value.he) ** 2 * value.can if isinstance(value, Radical) else Fraction(value) ** 2


def run(case):
    return run_fact_route(case["text"], deepcopy(case["payload"]))


def by_id(split, cid):
    return deepcopy(next(c for c in CORPUS[split] if c["id"] == cid))


def assert_served_exactly(r, case):
    assert r.status == "SERVED", (case["id"], r.code, r.reason)
    assert set(r.answers) == set(case["expected_squared"])
    for q, want in case["expected_squared"].items():
        assert squared(r.exec_result.final_memory[f"kq_{q}"]) == Fraction(want), q
    assert r.kernel_check and r.scene3d["objects"]


def chain_certificates(r):
    return [d for d in r.planner["auxiliary"] if d.get("rule") == "effect-chain"]


# ── preregistered corpus ─────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("case", CORPUS["positive"], ids=lambda c: c["id"])
def test_positive_unnamed_operand_is_served_exactly(case):
    r = run(case)
    assert_served_exactly(r, case)
    certs = chain_certificates(r)
    assert certs and all(d["operand"]["descriptor"] == "midpoint" for d in certs)
    fresh = {x for d in certs for x in d["labels"]}
    if "expected_new_points" in case:
        assert not fresh                                           # the source already names that midpoint: reuse it
    midpoints = [c for c in r.planner["calls"] if c["fn"] == "midpoint"]
    if "expected_midpoint_constructions" in case:
        assert len(midpoints) == case["expected_midpoint_constructions"]
    # descriptor semantics on the built figure, independently of the chosen function: 2·X = P + Q
    for d in certs:
        x = d["operand"]["label"]
        p, q = d["operand"]["points"]
        assert all(2 * r.points[x][i] == r.points[p][i] + r.points[q][i] for i in range(3))


@pytest.mark.parametrize("case", CORPUS["negative"], ids=lambda c: c["id"])
def test_negative_is_refused_with_a_registered_code(case):
    r = run(case)
    assert r.status == "REFUSED", (case["id"], r.answers)
    assert r.code in case["expected_codes"], (case["id"], r.code, r.reason)
    assert not r.answers and r.scene3d is None


def test_scene_shows_the_unnamed_point_before_its_witness_and_after_the_solid():
    from app.simulation.geometry_functions.engine import ir_name
    for cid in ("pyr-midpoint-to-plane", "pyr-midpoint-to-named-line", "pyr-midpoint-to-result-line"):
        r = run(by_id("positive", cid))
        cert = chain_certificates(r)[0]
        created = {e["object"]: e["step_index"] for e in r.scene3d["events"] if e.get("action") == "CREATE"}
        m = ir_name(cert["operand"]["label"])
        solid = next(o["id"] for o in r.scene3d["objects"] if o["type"] == "solid")
        assert created[solid] < created[m]
        obj = next(o for o in r.scene3d["objects"] if o["id"] == m)
        assert obj["role"] == "Điểm dựng phụ" and obj["source"].get("binding") == "AUXILIARY"
        narration = next(e["learner_text"] for e in r.scene3d["events"] if e.get("object") == m and e.get("action") == "CREATE")
        assert "trung điểm" in narration
        if cid != "pyr-midpoint-to-plane":                         # a line target needs the constructed foot H
            foot = next(o for o in r.scene3d["objects"] if o.get("perpendicular_witness"))
            assert created[m] < created[foot["id"]]
            assert m in foot["depends"]
        if cid == "pyr-midpoint-to-result-line":
            assert created["gt_g"] < created[foot["id"]]


# ── discovery: one contract added as DATA ────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("case", CORPUS["discovery"], ids=lambda c: c["id"])
def test_new_contract_is_discovered_without_planner_change(case, monkeypatch):
    from app.simulation.geometry_functions import engine, planner, registry
    code = {m.__name__: Path(m.__file__).read_bytes() for m in (planner, registry, engine)}
    assert run(case).code == "UNSUPPORTED_CAPABILITY"              # production catalog: no effect produces a centroid
    monkeypatch.setitem(registry.REGISTRY, "centroid", experimental_centroid_contract(registry))
    r = run(case)
    assert_served_exactly(r, case)
    assert {Path(m.__file__).read_bytes() for m in (planner, registry, engine)} == set(code.values())
    cert = chain_certificates(r)[0]
    g, (a, b, c) = cert["operand"]["label"], cert["operand"]["points"]
    assert all(3 * r.points[g][i] == r.points[a][i] + r.points[b][i] + r.points[c][i] for i in range(3))


def test_lying_contract_is_caught_by_engine_semantics_not_trusted(monkeypatch):
    from app.simulation.geometry_functions import registry
    lie = replace(experimental_centroid_contract(registry).planning, call=(("point", "G"), ("segment", ("A", "B"))))
    monkeypatch.setitem(registry.REGISTRY, "midpoint", replace(registry.REGISTRY["midpoint"], planning=lie))
    r = run(by_id("discovery", "centroid-to-plane"))
    assert r.status == "REFUSED" and r.code == "ENGINE_SELF_CHECK_FAILED", (r.code, r.reason)


@pytest.mark.parametrize("removed,cases", [
    ("midpoint", [c["id"] for c in CORPUS["positive"] if c["id"] != "pyr-reuse-named-midpoint"]),
    ("ask_distance_point_plane", [c["id"] for c in CORPUS["positive"] if c["target"] == "plane"]),
])
def test_registry_ablation_removes_exactly_the_dependent_capability(removed, cases, monkeypatch):
    from app.simulation.geometry_functions import registry
    monkeypatch.setitem(registry.REGISTRY, removed, replace(registry.REGISTRY[removed], planning=None))
    for case in CORPUS["positive"]:
        r = run(case)
        if case["id"] in cases:
            assert r.status == "REFUSED" and r.code == "UNSUPPORTED_CAPABILITY", (case["id"], r.code)
        elif removed == "ask_distance_point_plane" and case["target"] in ("named_line", "result_line"):
            assert_served_exactly(r, case)


def test_registry_order_does_not_change_the_plan(monkeypatch):
    from app.simulation.geometry_functions import planner, registry
    plans = {}
    for order in ("forward", "reversed"):
        if order == "reversed":
            monkeypatch.setattr(registry, "REGISTRY", dict(reversed(list(registry.REGISTRY.items()))))
            monkeypatch.setattr(planner, "REGISTRY", registry.REGISTRY)
        plans[order] = [run(c).planner["calls"] for c in CORPUS["positive"]]
    assert plans["forward"] == plans["reversed"]


# ── metamorphic ──────────────────────────────────────────────────────────────────────────────────────────────────
def _rename(case, names):
    def sub(v):
        if isinstance(v, dict):
            return {k: (x if k in ("id", "kind", "role", "measure", "shape", "solid_type", "point_kind", "quantity",
                                   "line_ref") else sub(x)) for k, x in v.items()}
        if isinstance(v, list):
            return [sub(x) for x in v]
        if isinstance(v, str):
            return re.sub(r"[A-Z]+(?![a-z])", lambda m: "".join(names.get(x, x) for x in m[0]), v)
        return v
    case["text"] = sub(case["text"])
    case["payload"] = sub(case["payload"])
    return case


@pytest.mark.parametrize("variant", ["rename", "facts-order", "operand-order", "scale", "label-collision"])
def test_metamorphic_variants_keep_the_answer(variant):
    for cid in ("pyr-midpoint-to-plane", "pyr-midpoint-to-named-line", "pyr-midpoint-to-result-line"):
        c = by_id("positive", cid)
        want = Fraction(c["expected_squared"]["q"])
        if variant == "rename":
            c = _rename(c, {"S": "V", "A": "E", "B": "F", "C": "G", "D": "K"})
        elif variant == "facts-order":
            c["payload"]["facts"].reverse()
        elif variant == "operand-order":
            q = c["payload"]["facts"][-1]
            q["points"].reverse()
            c["text"] = c["text"].replace("trung điểm của SC", "trung điểm của CS")
            q["quotes"] = [x.replace("trung điểm của SC", "trung điểm của CS") for x in q["quotes"]]
        elif variant == "scale":
            for f in c["payload"]["facts"]:
                if f.get("value"):
                    f["value"] = str(2 * int(f["value"]))
                    f["quotes"] = [re.sub(r"\d+", lambda m: str(2 * int(m[0])), x) for x in f["quotes"]]
            c["text"] = re.sub(r"(cạnh |= )(\d+)", lambda m: m[1] + str(2 * int(m[2])), c["text"])
            want *= 4
        else:
            quote = "Gọi M là trung điểm AB."
            c["text"] = c["text"].replace("SA = 3.", "SA = 3. " + quote)
            c["payload"]["facts"].insert(4, {"id": "fm", "kind": "point_def", "role": "premise", "quotes": [quote],
                                             "point": "M", "point_kind": "midpoint", "points": ["A", "B"]})
        r = run(c)
        assert r.status == "SERVED", (variant, cid, r.code, r.reason)
        assert squared(r.exec_result.final_memory["kq_q"]) == want, (variant, cid)
        if variant == "label-collision":
            assert chain_certificates(r)[0]["operand"]["label"] == "M1"


@pytest.mark.parametrize("bound,value", [("MAX_EFFECT_DEPTH", 1), ("MAX_EFFECT_NEEDS", 2), ("MAX_EFFECT_CANDIDATES", 1),
                                         ("MAX_RESULT_FEET", 0), ("MAX_CALLS", 3)])
def test_budgets_refuse_without_partial_result(bound, value, monkeypatch):
    from app.simulation.geometry_functions import planner
    monkeypatch.setattr(planner, bound, value)
    r = run(by_id("positive", "pyr-midpoint-to-result-line"))
    assert r.status == "REFUSED" and r.code == "PLAN_TOO_LARGE", (bound, r.code)
    assert not r.answers and r.scene3d is None


# ── gate: the certificate is checked, never trusted ──────────────────────────────────────────────────────────────
def _plan(cid):
    from app.simulation.geometry_functions.planner import lap_ke_hoach
    c = by_id("positive", cid)
    return c, lap_ke_hoach(c["payload"], c["text"])


@pytest.mark.parametrize("tamper", ["env-operand", "descriptor-points", "drop-certificate", "fresh-label-in-source",
                                    "quotes", "target"])
def test_tampered_certificate_or_calls_fail_closed(tamper):
    from app.ai.function_route import run_function_route
    cid = "pyr-midpoint-to-named-line"
    c, k = _plan(cid)
    aux = deepcopy(k.auxiliary)
    calls = deepcopy(k.calls)
    cert = next(d for d in aux if d.get("rule") == "effect-chain")
    if tamper == "env-operand":
        cert["chain"][0]["env"]["A"] = "B"
    elif tamper == "descriptor-points":
        cert["operand"]["points"] = ["S", "B"]
    elif tamper == "drop-certificate":
        aux.remove(cert)
    elif tamper == "fresh-label-in-source":
        mid = next(x for x in calls if x["fn"] == "midpoint")
        old = mid["args"]["point"]
        for x in calls:
            x["args"] = json.loads(json.dumps(x["args"]).replace(f'"{old}"', '"S"'))
        cert["labels"] = ["S" if x == old else x for x in cert["labels"]]
    elif tamper == "quotes":
        for x in calls:
            if x["id"] in {e["call"] for e in cert["chain"]}:
                x["source"]["quotes"] = ["SA = 3."]
    else:
        cert["target"] = {"line": ["A", "C"]}
    r = run_function_route(c["text"], {"calls": calls}, tuple(aux))
    assert r.status == "REFUSED", tamper


def test_route_a_cannot_use_an_unnamed_point_without_a_planner_certificate():
    from app.ai.function_route import run_function_route
    c, k = _plan("pyr-midpoint-to-plane")
    r = run_function_route(c["text"], {"calls": k.calls})
    assert r.status == "REFUSED" and r.code in ("UNKNOWN_LABEL", "SOURCE_OBJECT_MISMATCH", "QUESTION_CONTEXT_UNSUPPORTED")


def test_provider_surfaces_are_unchanged():
    import hashlib
    from app.ai import fact_extraction, function_calling
    from app.simulation.geometry_functions.registry import function_declarations
    assert function_calling.surface_fingerprint().startswith("7ea511a6e3828c9a")
    assert fact_extraction.surface_fingerprint().startswith("485d3834db8b18cf")
    decl = json.dumps(function_declarations(), ensure_ascii=False, sort_keys=True).encode()
    assert hashlib.sha256(decl).hexdigest().startswith("5ceb0f999d4d7c1e")
    assert "PlanningContract" not in json.dumps(fact_extraction.facts_response_schema())
