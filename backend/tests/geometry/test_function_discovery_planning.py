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


#: Deviation D-1 (recorded in the run report, label NOT edited) was the cube premise outside the closed `line_ref` premise
#: grammar: refused SOURCE_PREMISE_UNREAD before the parallel planes were reached. Closed by M4 of run
#: `hybrid-semantic-grounding-reliability`; the row now meets its preregistered code, so no deviation remains.
_DEVIATION: dict[str, str] = {}


@pytest.mark.parametrize("case", [pytest.param(c, marks=pytest.mark.xfail(strict=True, reason=_DEVIATION[c["id"]]))
                                  if c["id"] in _DEVIATION else c for c in CORPUS["negative"]], ids=lambda c: c["id"])
def test_negative_is_refused_with_a_registered_code(case, monkeypatch):
    if case["id"] == "centroid-without-contract":    # its premise since Wave 2A ships the contract: remove it (data only)
        from app.simulation.geometry_functions import registry
        monkeypatch.setitem(registry.REGISTRY, "centroid", replace(registry.REGISTRY["centroid"], planning=None))
    r = run(case)
    assert r.status == "REFUSED", (case["id"], r.answers)
    assert not r.answers and r.scene3d is None
    assert r.code in case["expected_codes"], (case["id"], r.code, r.reason)


def test_deviation_d1_closed_cube_and_cuboid_parallel_planes_refuse_with_the_registered_code():
    """Post-registration supplement (not a corpus row): the same goal on a cuboid. Since M4 (run
    `hybrid-semantic-grounding-reliability`) the cube premise is read too, so both reach the parallel-planes refusal."""
    r = run(by_id("negative", "parallel-result-line"))
    assert r.status == "REFUSED" and r.code in ("PARALLEL_NO_INTERSECTION", "PARALLEL_PLANES"), (r.code, r.reason)
    c = by_id("positive", "cuboid-midpoint-to-result-line")
    old_gt, new_gt = "Tìm giao tuyến của (ABB') và (BCC').", "Tìm giao tuyến của (ABB') và (CDD')."
    old_q = "Tính khoảng cách từ trung điểm của A'C' đến giao tuyến của (ABB') và (BCC')."
    new_q = old_q.replace("(BCC')", "(CDD')")
    c["text"] = c["text"].replace(old_gt, new_gt).replace(old_q, new_q)
    for f in c["payload"]["facts"]:
        if f["id"] == "g":
            f.update(points_b=["C", "D", "D'"], quotes=[new_gt])
        if f["id"] == "q":
            f["quotes"] = [new_q]
    r = run(c)
    assert r.status == "REFUSED" and r.code in ("PARALLEL_NO_INTERSECTION", "PARALLEL_PLANES"), (r.code, r.reason)


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
    assert registry.REGISTRY["centroid"].planning == experimental_centroid_contract(registry).planning  # promoted as is
    with monkeypatch.context() as m:                                   # without it no effect produces a centroid
        m.setitem(registry.REGISTRY, "centroid", replace(registry.REGISTRY["centroid"], planning=None))
        assert run(case).code == "UNSUPPORTED_CAPABILITY"
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
    # the honest centroid contract (Wave 2A) would win the tie by name: remove it so the lie is the only producer
    monkeypatch.setitem(registry.REGISTRY, "centroid", replace(registry.REGISTRY["centroid"], planning=None))
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


@pytest.mark.parametrize("line", [["B", "D"], ["D", "B"]])
def test_supplied_foot_is_reused_whatever_order_the_line_is_written(line):
    """A line through B and D is the line through D and B: the available-binding match must not depend on writing order
    (the old resolver sorted the line; the template comparison must keep that)."""
    from tests.geometry import hybrid_compiler_benchmark as HB
    quote = f"Gọi J là hình chiếu vuông góc của S lên {''.join(line)}."
    ask_q = "Tính khoảng cách từ S đến BD."
    text = " ".join(HB._square()[0] + [quote, ask_q])
    facts = HB._square()[1] + [{"id": "foot", "kind": "projection", "role": "premise", "point": "S", "at": "J",
                                "points": line, "quotes": [quote]},
                               HB._ask("q", ask_q, "distance", points_a=["S"], points_b=["B", "D"])]
    r = run_fact_route(text, {"facts": facts})
    assert r.status == "SERVED", (r.code, r.reason)
    assert len([c for c in r.planner["calls"] if c["fn"] == "orthogonal_projection_line"]) == 1
    assert next(c for c in r.planner["calls"] if c["id"] == "q")["args"]["segment"] == ["S", "J"]


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


# ── independent review findings (RED before the fix) ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("cid,old,new", [
    ("pyr-midpoint-to-named-line", "đến BD.", "đến AC."),          # IMP-1: the source names another line
    ("pyr-midpoint-to-plane", "đến (SAB).", "đến (SAD)."),         # IMP-1: the source names another plane
    ("pyr-midpoint-to-plane", "đến (SAB).", "đến đáy."),
])
def test_target_named_by_the_source_must_be_the_target_of_the_facts(cid, old, new):
    c = by_id("positive", cid)
    c["text"] = c["text"].replace(old, new)
    c["payload"]["facts"][-1]["quotes"] = [q.replace(old, new) for q in c["payload"]["facts"][-1]["quotes"]]
    r = run(c)
    assert r.status == "REFUSED" and r.code == "SOURCE_OBJECT_MISMATCH", (r.code, r.answers)


def test_a_second_ask_in_the_certified_quote_is_not_read_as_answered():
    """IMP-2: only the phrase the certificate bound is read; another descriptor ask in the same quote stays unread."""
    c = by_id("positive", "pyr-midpoint-to-plane")
    two = "Tính khoảng cách từ trung điểm của SC đến (SAB). Tính khoảng cách từ trung điểm của SC đến BD."
    c["text"] = c["text"].replace("Tính khoảng cách từ trung điểm của SC đến (SAB).", two)
    c["payload"]["facts"][-1]["quotes"] = [two]
    r = run(c)
    # was QUESTION_CONTEXT_UNSUPPORTED (unread words); request coverage (M1, run `hybrid-semantic-grounding-reliability`)
    # now names the dropped ask itself
    assert r.status == "REFUSED" and r.code == "REQUEST_NOT_ANSWERED", (r.code, r.answers)


def test_engine_answer_check_is_wired(monkeypatch):
    """MINOR-5: the engine compares the composed answer with a direct distance; a disagreement refuses."""
    from app.simulation.geometry_functions import engine
    monkeypatch.setattr(engine._Dung, "kc2_dich", lambda self, d: Fraction(-1))
    r = run(by_id("positive", "pyr-midpoint-to-plane"))
    assert r.status == "REFUSED" and r.code == "ENGINE_SELF_CHECK_FAILED", r.code


def test_fresh_label_equal_to_a_source_label_is_a_collision():
    """MINOR-5: a certificate whose calls AND bindings consistently use a source label as the fresh point."""
    from app.ai.function_route import run_function_route
    c, k = _plan("pyr-midpoint-to-plane")
    aux, calls = deepcopy(k.auxiliary), deepcopy(k.calls)
    cert = next(d for d in aux if d.get("rule") == "effect-chain")
    def swap(v):                                   # values only — the slot NAME "M" of the midpoint contract stays
        if isinstance(v, dict):
            return {k: swap(x) for k, x in v.items()}
        if isinstance(v, list):
            return [swap(x) for x in v]
        return "D" if v == "M" else v
    for x in calls:
        x["args"] = swap(x["args"])
    for key in ("chain", "labels", "operand"):
        cert[key] = swap(cert[key])
    r = run_function_route(c["text"], {"calls": calls}, tuple(aux))
    assert r.status == "REFUSED" and r.code == "AUXILIARY_LABEL_COLLISION", r.code


def test_kind_filter_excludes_candidates_before_they_are_counted():
    """MINOR-5: a plane target never counts the line-only foot producer; a line target never the plane ask."""
    from app.simulation.geometry_functions.planner import lap_ke_hoach
    for cid, want in (("pyr-midpoint-to-plane", 3), ("pyr-midpoint-to-named-line", 3)):
        c = by_id("positive", cid)
        assert lap_ke_hoach(c["payload"], c["text"]).resolver.candidates == want, cid


@pytest.mark.parametrize("edit", ["operand-str", "target-str", "chain-str", "line-none", "line-int", "quote-none"])
def test_malformed_certificate_is_refused_with_a_code(edit):
    """MINOR-4: a hand-made malformed certificate is a coded refusal, never an exception."""
    from app.ai.function_route import run_function_route
    c, k = _plan("pyr-midpoint-to-named-line")
    aux = deepcopy(k.auxiliary)
    cert = next(d for d in aux if d.get("rule") == "effect-chain")
    if edit == "operand-str":
        cert["operand"] = "x"
    elif edit == "target-str":
        cert["target"] = "x"
    elif edit == "chain-str":
        cert["chain"].append("x")
    elif edit == "line-none":
        cert["target"] = {"line": None}
    elif edit == "line-int":
        cert["target"] = {"line": ["B", 1]}
    else:
        cert["quotes"] = [None]
    r = run_function_route(c["text"], {"calls": k.calls}, tuple(aux))
    assert r.status == "REFUSED" and r.code == "AUXILIARY_RULE_MISMATCH", (edit, r.code)


def test_duplicate_target_labels_are_an_incomplete_fact():
    """MINOR-8 (MINOR-7, narration "CS" for "SC", is the pre-existing scene `depends` order, also for named midpoints)."""
    c = by_id("positive", "pyr-midpoint-to-named-line")
    c["payload"]["facts"][-1]["points_b"] = ["B", "B"]
    assert run(c).code == "FACT_INCOMPLETE"


# ── CONTRACT-BE-1 (scene3d-visual-correctness integration): the asked quantity is the result of route D ─────────────
def _obj(r, oid):
    return next(o for o in r.scene3d["objects"] if o["id"] == oid)


@pytest.mark.parametrize("cid", ["pyr-midpoint-to-plane", "cube-midpoint-to-plane", "prism-midpoint-to-plane"])
def test_asked_distance_to_a_plane_is_the_result_and_its_plane_is_a_target(cid):
    r = run(by_id("positive", cid))
    kq = _obj(r, "kq_q")
    assert kq["annotation"]["role"] == "result" and kq["annotation"]["category"] == "result"
    assert "target" in kq["display_group"]
    final = [e for e in r.scene3d["events"] if e.get("semantic_kind") == "FINAL_RESULT"]
    assert [e["object"] for e in final] == ["kq_q"]
    mp = _obj(r, "mp_q")                               # the plane the question names: not a measurement-only helper
    assert "target" in mp["display_group"]
    m = _obj(r, chain_certificates(r)[0]["operand"]["label"])
    assert "target" in m["display_group"]


def test_fresh_foot_is_never_a_target_and_named_operands_are():
    r = run(by_id("positive", "pyr-midpoint-to-named-line"))
    cert = chain_certificates(r)[0]
    foot = next(x for x in cert["labels"] if x != cert["operand"]["label"])
    assert "target" not in _obj(r, foot)["display_group"]      # an auxiliary construction, hidden like one
    assert "target" in _obj(r, cert["operand"]["label"])["display_group"]
    assert _obj(r, "kq_q")["annotation"]["role"] == "result"


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
