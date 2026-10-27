"""Run `scene3d-plane-section-display-identity`: learner-facing names of a section plane and of a section with unnamed
vertices on the Adapter /4 route, read from the fields the frontend actually shows (`notation` on the canvas,
`reference` in the inspector, `label`/`display_label`, `role`, quantity `formula.text`, event and step text).

Cases are the locked `hybrid-contract-v2/grammar-set.json` payloads; the historical served envelopes
(`hybrid-disabled-integration/.../adapter4-frontend-fixtures.json`) are the "before" for the no-math-change guard.
"""
from __future__ import annotations

from itertools import permutations
import json
import re
from pathlib import Path

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route

ROOT = Path(__file__).resolve().parents[3]
LOCK = ROOT / "docs/evaluation/geometry/runs/hybrid-contract-v2/grammar-set.json"
BEFORE = (ROOT / "docs/evaluation/geometry/runs/hybrid-disabled-integration/results/adapter4-consumer-after-review"
          / "adapter4-frontend-fixtures.json")
CASES = {c["id"]: c for c in json.loads(LOCK.read_text(encoding="utf-8"))["cases"]}
OLD = {f["id"]: f for f in json.loads(BEFORE.read_text(encoding="utf-8"))["fixtures"]}
SERVED = sorted(OLD)


def _run(cid: str):
    r = run_typed_fact_next_v2_route(CASES[cid]["payload"])
    assert r.status == "SERVED", (r.code, r.reason)
    return r


def _learner(scene: dict) -> list[str]:
    """Every string the frontend renders for a learner from Scene3D."""
    out = [o.get(k) for o in scene["objects"] for k in ("label", "display_label", "reference", "notation", "role")]
    out += [(o.get("formula") or {}).get("text") for o in scene["objects"]]
    out += [e.get(k) for e in scene["events"] for k in ("display_label", "learner_text", "explanation")]
    out += [s.get("learner_text") for s in scene["formation"]["steps"]]
    return [t for t in out if isinstance(t, str)]


def _point_built_names(scene: dict, plane: dict) -> set[str]:
    """The planner's construction-point names of a plane, in ANY order ("(MHH1)", "qua M, H, H1"): `depends` is sorted,
    so the composed order cannot be read from it."""
    ky = {o["id"]: o.get("notation") or o["id"].replace("_prime", "′") for o in scene["objects"]}
    dau = [ky[d] or "" for d in plane["depends"]]
    return {f(p) for p in permutations(dau) for f in (lambda p: "(" + "".join(p) + ")", lambda p: "qua " + ", ".join(p))}


@pytest.mark.parametrize("cid", [c for c in SERVED if CASES[c]["payload"].get("derived_sections")])
def test_A_section_plane_shows_the_declared_source_name_in_every_learner_field(cid):
    r = _run(cid)
    sc = r.scene3d
    objs = {o["id"]: o for o in sc["objects"]}
    for sec in CASES[cid]["payload"]["derived_sections"]:
        name = f"({sec['plane_name']})"
        plane = objs[f"mp_td_{sec['section_id']}"]
        assert {k: plane.get(k) for k in ("label", "display_label", "reference", "notation")} == dict.fromkeys(
            ("label", "display_label", "reference", "notation"), name)
        built = _point_built_names(sc, plane)
        assert name not in built
        assert not [t for t in _learner(sc) if any(b in t for b in built)]
        # the role states the source relation, e.g. "qua M và song song với (ABCD)"; the related object is the one the
        # source quote names (review F2: a 3-point planner reference read "(ABC)" for a source "(ABCD)")
        qua = sec["through_point"].replace("'", "′")
        m = re.fullmatch(rf"Mặt phẳng qua {re.escape(qua)} và (?:song song với (\([^)]+\))|vuông góc với (\S+))",
                         plane["role"])
        assert m, plane["role"]
        assert (m[1] or m[2]).replace("′", "'") in sec["quote"], (plane["role"], sec["quote"])
        # internal construction untouched: the surface is still the plane through its construction points
        assert plane["depends"] == OLD[cid]["envelope"]["scene3d"]["objects"][
            [o["id"] for o in OLD[cid]["envelope"]["scene3d"]["objects"]].index(plane["id"])]["depends"]


@pytest.mark.parametrize("cid", [c for c in SERVED if CASES[c]["payload"].get("derived_sections")])
def test_R1_plane_explanation_states_the_source_definition_then_the_real_construction(cid):
    """Review R1 (run `scene3d-section-inspector-c0`): "Dựng mặt phẳng (α) qua ba điểm M, H, H1." read as if H, H1 defined
    (α). The fallback explanation now gives the source relation first and names H, H1 as auxiliary construction points;
    the learner step text is unchanged."""
    r = _run(cid)
    sc = r.scene3d
    old = OLD[cid]["envelope"]["scene3d"]
    for sec in CASES[cid]["payload"]["derived_sections"]:
        plane = next(o for o in sc["objects"] if o["id"] == f"mp_td_{sec['section_id']}")
        ev = next(e for e in sc["events"] if e.get("object") == plane["id"] and e.get("action") == "CREATE")
        before = next(e for e in old["events"] if e.get("object") == plane["id"] and e.get("action") == "CREATE")
        assert "qua ba điểm" not in ev["explanation"]
        rel = plane["role"][:1].lower() + plane["role"][1:]
        assert ev["explanation"].startswith(f"Dựng {plane['display_label']}: {rel}; dựng qua ")
        assert "điểm dựng phụ" in ev["explanation"]
        assert (ev["learner_text"], ev["display_label"]) == (before["learner_text"], "(α)")


def test_A_a_section_without_stated_cut_edges_still_shows_the_declared_name():
    """Review F1: "Dựng thiết diện … bởi (α)" alone (no stated cut edges, no derived solid) has no cut certificate; the
    declared name must not depend on one."""
    p = json.loads(json.dumps(CASES["PLANE-ONLY-construct"]["payload"]))
    p["simulation_goals"] = [g for g in p["simulation_goals"] if g["kind"] == "construct_plane_section"]
    r = run_typed_fact_next_v2_route(p)
    assert r.status == "SERVED", (r.code, r.reason)
    sc = r.scene3d
    plane = next(o for o in sc["objects"] if o["id"] == "mp_td_sec")
    assert [plane[k] for k in ("label", "display_label", "reference", "notation")] == ["(α)"] * 4
    assert plane["role"] == "Mặt phẳng qua M và song song với (ABC)"
    built = _point_built_names(sc, plane)
    assert not [t for t in _learner(sc) if any(b in t for b in built)]


def _without_derived(monkeypatch):
    """Planner output with the derived-solid record removed from every cut: an internal inconsistency, since a solid
    named on unnamed section vertices only exists when the planner declared it."""
    import app.simulation.geometry_functions.planner as PL
    goc = PL.lap_ke_hoach

    def lap(*a, **k):
        kh = goc(*a, **k)
        for d in kh.auxiliary:
            d.pop("derived", None)
        return kh
    monkeypatch.setattr(PL, "lap_ke_hoach", lap)


def test_kd_is_required_by_contract_and_its_absence_is_refused_at_the_source_gate(monkeypatch):
    """Run `scene3d-section-inspector-c0` (review F3 residual): the derived pyramid call is admitted only through its
    cut's `derived` record, so a plan without it is refused by the existing gate before any scene is presented."""
    _without_derived(monkeypatch)
    r = run_typed_fact_next_v2_route(CASES["PLANE-ONLY-ratio-described"]["payload"])
    assert (r.status, r.code) == ("REFUSED", "AUXILIARY_RULE_MISMATCH")
    assert r.scene3d is None


def test_kd_presentation_fails_closed_instead_of_labelling_a_solid_as_a_segment():
    """Defence in depth: should the presentation ever see a solid on unnamed cut vertices without its derived record,
    it raises a dedicated error (no "Đoạn của thiết diện", no invented label or value)."""
    from app.ai.function_route import _KhoiKhongKhai, _an_dinh_thiet_dien_phu
    from app.simulation.geometry_functions.registry import DINH_CAT_CANH
    canh = {"objects": [
        {"id": "mp_td_sp", "type": "plane3", "label": "(α)", "display_label": "(α)", "notation": "(α)", "depends": []},
        {"id": "I", "type": "point3", "label": "I", "notation": "I", "depends": []},
        {"id": "khoi_S_MII1", "type": "solid", "label": "S.MII1", "notation": "S.MII1", "depends": []}],
        "events": [], "formation": {"steps": []}}
    aux = ({"rule": DINH_CAT_CANH, "goal": "sp", "vertices": [{"label": "I", "edge": ["B", "B'"],
                                                               "choice": "fresh_intersection"}]},)
    with pytest.raises(_KhoiKhongKhai):
        _an_dinh_thiet_dien_phu(canh, aux)
    assert not [o for o in canh["objects"] if o["label"] == "Đoạn của thiết diện"]


def test_kd_route_maps_the_presentation_inconsistency_to_a_structured_refusal(monkeypatch):
    import app.ai.function_route as FR

    def hong(canh, aux):
        raise FR._KhoiKhongKhai("khoi_x")
    monkeypatch.setattr(FR, "_an_dinh_thiet_dien_phu", hong)
    r = run_typed_fact_next_v2_route(CASES["PLANE-ONLY-ratio-described"]["payload"])
    assert (r.status, r.code) == ("REFUSED", "SCENE_BUILD_FAILED")
    assert "khối dẫn xuất" in r.reason and "khoi_x" in r.reason


@pytest.mark.parametrize("cid", [c for c in SERVED if any(
    g["kind"] == "construct_derived_solid" for g in CASES[c]["payload"].get("simulation_goals") or ())])
def test_kd_valid_scenes_with_a_derived_solid_are_still_served(cid):
    r = _run(cid)
    assert any(o["type"] == "solid" and o["label"].startswith("Khối chóp đỉnh") for o in r.scene3d["objects"]) or all(
        o.get("notation") for o in r.scene3d["objects"] if o["type"] == "solid")


@pytest.mark.parametrize("text, cu, expected", [
    ("V(S.MII1)/V(S.ABC)", [("MII1", "thiết diện bởi (α)")], "V(S.MII1)/V(S.ABC)"),   # inside a dotted name: untouched
    ("HMH1 có diện tích", [("HMH1", "thiết diện bởi (α)")], "Thiết diện bởi (α) có diện tích"),
    ("Tính diện tích HMH1.", [("HMH1", "thiết diện bởi (α)")], "Tính diện tích thiết diện bởi (α)."),
    ("Thiết diện HMH1", [("HMH1", "thiết diện bởi (α)")], "Thiết diện bởi (α)"),
])
def test_old_names_are_replaced_as_whole_names_keeping_sentence_case(text, cu, expected):
    from app.ai.function_route import _thay_ten
    assert _thay_ten(text, cu) == expected


def test_B_a_section_with_unnamed_vertices_is_not_named_through_a_coincident_construction_point():
    """Prism: the planner's translates H = M + AB, H1 = M + AC land exactly on the stated-unnamed cuts I (BB′), I1 (CC′).
    The cycle "HMH1" named those unnamed vertices; the section is "Thiết diện bởi (α)" like every other unnamed one."""
    r = _run("CORPUS-DEV10-prism-area")
    sc = r.scene3d
    objs = {o["id"]: o for o in sc["objects"]}
    sec = objs["td_sp"]
    assert (sec["label"], sec["display_label"], sec["notation"]) == ("Thiết diện bởi (α)", "Thiết diện bởi (α)", None)
    assert not [t for t in _learner(sc) if "HMH1" in t]
    # renaming the section keeps its pedagogical event text (an earlier draft overwrote it with "Dựng thiết diện …")
    assert "Thiết diện khép lại thành tam giác: (α) cắt lăng trụ đứng ABC.A′B′C′." in [
        s["learner_text"] for s in sc["formation"]["steps"]]
    # the coincidence is real and stays: two semantic points per vertex, ids and coordinates unchanged
    assert objs["H"]["xyz"] == objs["I"]["xyz"] and objs["H1"]["xyz"] == objs["I1"]["xyz"]
    assert (objs["H"]["notation"], objs["H1"]["notation"]) == (None, None)
    assert (objs["H"]["role"], objs["H1"]["role"]) == ("Điểm dựng phụ", "Điểm dựng phụ")
    # review N2 (run `scene3d-section-inspector-c0`): the descriptive label, now shown by the inspector, writes primes
    # as the rest of the UI does (BB′, not BB')
    assert (objs["I"]["label"], objs["I1"]["label"]) == ("Giao điểm của BB′ và (α)", "Giao điểm của CC′ và (α)")
    # review P1: the per-cut step built by the second text builder writes primes too
    steps = [s["learner_text"] for s in sc["formation"]["steps"]]
    assert "Xét mặt phẳng (α) để tìm giao điểm với BB′." in steps
    assert not [t for t in steps if "BB'" in t or "CC'" in t]
    for p in ("I", "I1"):    # STATED_UNNAMED stays unnamed and auxiliary, never a given
        assert objs[p]["notation"] is None and objs[p]["role"] == "Điểm dựng phụ"
        assert "given" not in (objs[p].get("display_group") or [])
    assert [v["provenance"] for v in r.route_d["sections"][0]["vertices"]] == [
        "THROUGH_POINT_REUSE", "STATED_UNNAMED", "STATED_UNNAMED"]
    area = objs["kq_g_area"]
    assert area["notation"] is None and area["label"] == "Diện tích thiết diện bởi (α)"
    assert area["formula"]["text"].endswith("= √3/4") and "HMH1" not in area["formula"]["text"]


def test_B_a_quantity_on_an_unnamed_derived_solid_keeps_its_kind_and_hides_planner_labels():
    """Plane-only ratio: the volume ratio was relabelled "Đoạn của thiết diện" and its formula read V(S.MII1)."""
    r = _run("PLANE-ONLY-ratio-described")
    sc = r.scene3d
    q = next(o for o in sc["objects"] if o["id"] == "kq_g_ratio")
    assert q["label"].startswith("Tỉ số") and q["label"] != "Đoạn của thiết diện"
    fresh = {v["label"] for s in r.route_d["sections"] for v in s["vertices"]
             if v["provenance"] in ("STATED_UNNAMED", "DERIVED_FRESH")}
    token = re.compile(r"(?<![\w'])[A-Z0-9'.]*(?:" + "|".join(sorted(fresh, key=len, reverse=True)) + r")[A-Z0-9'.]*(?![\w'])")
    assert not [t for t in _learner(sc) if token.search(t)]
    assert q["formula"]["text"].endswith("= 1/8")


@pytest.mark.parametrize("cid", SERVED)
def test_presentation_fix_moves_no_geometry_provenance_answer_or_order(cid):
    """Guard: only names may differ from the historical served envelope."""
    r = _run(cid)
    old = OLD[cid]
    new_sc, old_sc = r.scene3d, old["envelope"]["scene3d"]
    shape = lambda sc: [(o["id"], o["type"], o.get("xyz"), o.get("depends"), o.get("polygon"), o.get("origin"),
                         o.get("render"), (o.get("formula") or {}).get("value"), o.get("value"))
                        for o in sc["objects"]]
    assert shape(new_sc) == shape(old_sc)
    assert [(e.get("object"), e.get("action"), e.get("step_index")) for e in new_sc["events"]] == [
        (e.get("object"), e.get("action"), e.get("step_index")) for e in old_sc["events"]]
    assert [s.get("visible_ids") for s in new_sc["formation"]["steps"]] == [
        s.get("visible_ids") for s in old_sc["formation"]["steps"]]
    assert r.route_d["sections"] == old["route_d"]["sections"]
    assert (r.route_d["answers"], r.route_d["answer_exact"]) == (old["route_d"]["answers"], old["route_d"]["answer_exact"])
