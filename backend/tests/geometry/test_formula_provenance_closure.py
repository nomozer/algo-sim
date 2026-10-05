# -*- coding: utf-8 -*-
"""w11 — volume formula and numerical provenance, end to end, 0 model calls.

Human review W10-H1..H3: the triangular pyramid and prism causal cards had no
formula and no height. Root cause: their compilers declared no GIVEN length, so
`_provenance` could not attach the height and `_attach_formulas` skipped the
volume. Rectangular pyramid, cuboid, cube and cross-section are the controls.
"""
from __future__ import annotations

import pytest

from app.simulation.geometry_compiler.compiler import bien_dich
from app.simulation.geometry_compiler.contract_adapter import build_fact_graph
from app.simulation.geometry_compiler.routing import quyet_dinh_dinh_tuyen
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import build_simulation_state
from scripts import generate_generic_tier_a_fixtures as G

FACTORIES = {
    "triangular_pyramid": G._pyramid_control_contract,
    "triangular_prism": G._prism_p01_contract,
    "rectangular_pyramid": G._rect_pyramid_contract,
    "cuboid": G._cuboid_contract,
    "cube": G._cube_contract,
}

#: case → (base area, height, formula). Labels are the problem's own notation.
EXPECTED = {
    "triangular_pyramid": ("S(ABC)", "SA", "V = 1/3 × S(ABC) × SA = 10"),
    "triangular_prism": ("S(ABC)", "AD", "V = S(ABC) × AD = 30"),
    "rectangular_pyramid": ("S(ABCD)", "SA", "V = 1/3 × S(ABCD) × SA = 24"),
    "cuboid": ("S(ABCD)", "AA′", "V = S(ABCD) × AA′ = 60"),
    "cube": ("S(ABCD)", "AA′", "V = S(ABCD) × AA′ = 64"),
}


@pytest.fixture(scope="module")
def scenes() -> dict[str, dict]:
    out = {}
    for name, factory in FACTORIES.items():
        text, contract = factory()
        envelope = G.asyncio.run(G._run_compiler(text, contract))
        assert envelope["status"] == "ok", envelope
        out[name] = envelope["scene3d"]
    return out


def _by_id(scene: dict) -> dict[str, dict]:
    return {o["id"]: o for o in scene["objects"]}


def _volume(scene: dict) -> dict:
    return next(o for o in scene["objects"]
                if o.get("producer") == "measure.volume")


def _label(o: dict) -> str:
    return o.get("notation") or o.get("reference") or o["label"]


@pytest.mark.parametrize("case", ["triangular_pyramid", "triangular_prism"])
def test_triangular_compilers_declare_the_given_lengths(case):
    """Fails while `bien_dich` / `_bien_dich_prism` declare no `*_length` memory."""
    text, contract = FACTORIES[case]()
    graph = build_fact_graph(contract).graph
    program = bien_dich(graph).program
    lengths = {d["name"]: d for d in program["memory_declarations"]
               if d["name"].endswith("_length")}
    facts = {tuple(sorted(f.args)): f for f in graph.fact_theo_loai("length")}
    assert len(lengths) == 3 == len(facts)
    for decl in lengths.values():
        # Provenance and source are the FactGraph's, never chosen by the compiler.
        fact = next(f for f in facts.values()
                    if f.source_fact_id == decl["source_fact_id"])
        assert decl["provenance"] == fact.status == "GIVEN"
        assert decl["initial_value"] == fact.value


@pytest.mark.parametrize("case", sorted(EXPECTED))
def test_volume_numerical_edges_are_base_area_and_height(case, scenes):
    scene = scenes[case]
    by_id = _by_id(scene)
    area, height, _ = EXPECTED[case]
    numerical = [by_id[e["source_id"]] for e in _volume(scene)["dependency_edges"]
                 if e["relation"] == "numerical"]
    assert sorted(_label(o) for o in numerical) == sorted([area, height])
    assert sum(o["producer"] == "measure.area" for o in numerical) == 1


@pytest.mark.parametrize("case", sorted(EXPECTED))
def test_volume_formula_names_base_area_and_height(case, scenes):
    formula = _volume(scenes[case])["formula"]
    assert formula["text"] == EXPECTED[case][2]
    by_id = _by_id(scenes[case])
    assert sorted(r["display_label"] for r in formula["references"]) == sorted(EXPECTED[case][:2])
    assert all(r["entity_id"] in by_id for r in formula["references"])


@pytest.mark.parametrize("case", sorted(EXPECTED))
def test_every_formula_references_exactly_what_its_text_names(case, scenes):
    """`S(ABCD) = 12` mang tham chiếu AB, AD mà chữ không nhắc — frontend thấy
    không nhất quán và ẩn thẻ (w10). Tham chiếu = đúng các vật có trong chữ,
    theo thứ tự xuất hiện; `Dựa trên` đọc thứ tự ấy."""
    for o in scenes[case]["objects"]:
        formula = o.get("formula")
        if not formula:
            continue
        labels = [r["display_label"] for r in formula["references"]]
        assert all(label in formula["text"] for label in labels), (o["id"], formula)
        assert labels == sorted(labels, key=formula["text"].index), (o["id"], formula)


@pytest.mark.parametrize("case", sorted(EXPECTED))
def test_trace_panel_restates_the_frontend_basis_in_formula_order(case, scenes):
    """`trace_formula_provenance._panel` says it restates the frontend; since w11
    `numericalBasis` reads the coherent formula's references first, in text order."""
    from scripts import trace_formula_provenance as T
    scene = scenes[case]
    area, height, _ = EXPECTED[case]
    assert T._panel(scene, _volume(scene), None)["dua_tren"] == [area, height]


@pytest.mark.parametrize("case,init", [
    ("triangular_pyramid", "Dữ kiện đề cho: AB = 3, AC = 4, SA = 5."),
    ("triangular_prism", "Dữ kiện đề cho: AB = 3, AC = 4, AD = 5."),
])
def test_triangular_givens_are_read_out_and_narrated(case, init, scenes):
    scene = scenes[case]
    assert scene["events"][0]["learner_text"] == init
    measure = next(e for e in scene["events"]
                   if e.get("object") == _volume(scene)["id"]
                   and e["semantic_kind"] == "MEASUREMENT")
    assert measure["learner_text"].endswith(EXPECTED[case][2] + ".")


def test_cross_section_volume_keeps_structural_provenance_without_formula():
    """Control: the volume comes from given coordinates. No height quantity
    exists in the program, so no formula may be fabricated for it."""
    _, envelope = G._cross_section_positive()
    volume = _volume(envelope["scene3d"])
    assert [e["relation"] for e in volume["dependency_edges"]] == ["structural"]
    assert "formula" not in volume


@pytest.mark.parametrize("case,height", [
    ("triangular_pyramid", {"A", "S"}), ("triangular_prism", {"A", "D"}),
])
def test_missing_height_never_compiles_an_answer(case, height):
    """Insufficient data ⇒ the compiler route produces no program and no value."""
    text, contract = FACTORIES[case]()
    invariants = tuple(s for s in contract.source_invariants if set(s.points) != height)
    reduced = contract.model_copy(update={"source_invariants": invariants})
    decision = quyet_dinh_dinh_tuyen(reduced, {"GEOMETRY_COMPILER_MODE": "DETERMINISTIC_FIRST"})
    assert decision.decision != "USE_COMPILER"
    assert decision.program is None


def _chop_SA_SB(s: list[int]):
    decl = [
        {"name": n, "type": "point3", "initial_value": v, "provenance": "LAYOUT_DERIVED"}
        for n, v in (("A", [0, 0, 0]), ("B", [3, 0, 0]), ("C", [0, 4, 0]), ("S", s))
    ] + [
        {"name": n, "type": "float", "initial_value": v, "provenance": "GIVEN", "source_fact_id": f"f_{n}"}
        for n, v in (("AB_length", "3"), ("AC_length", "4"), ("SA_length", "4"), ("SB_length", "5"))
    ] + [{"name": "day_ABC", "type": "polygon3"}, {"name": "khoi", "type": "solid"},
         {"name": "dt", "type": "float"}, {"name": "tt", "type": "float"}]
    spec = SemanticProgramSpec.model_validate({
        "spec_version": "1.0", "title": "Thể tích khối chóp", "memory_declarations": decl,
        "visual_bindings": {},
        "statements": [
            {"kind": "construct_polygon", "target_var": "day_ABC", "vertices": ["A", "B", "C"]},
            {"kind": "construct_solid", "target_var": "khoi", "vertices": ["S", "A", "B", "C"],
             "faces": [["A", "B", "C"], ["S", "A", "B"], ["S", "B", "C"], ["S", "C", "A"]]},
            {"kind": "assign", "target_var": "dt",
             "expr": {"kind": "measure", "quantity": "area", "of": "day_ABC"}},
            {"kind": "assign", "target_var": "tt",
             "expr": {"kind": "measure", "quantity": "volume", "of": "khoi"}},
        ],
    })
    return _by_id(build_scene3d(build_simulation_state(spec, SemanticProgramInterpreter().execute(spec))))["tt"]


def test_two_named_lengths_height_is_the_perpendicular_one():
    """SA and SB both name an apex edge (both stay numerical sources). Before regular-square-pyramid-w02 this was
    'ambiguous ⇒ no card'; the height is now chosen by the exact relation — SA ⊥ (ABC) with A on the base, SB is
    slanted — so the card reads × SA. Value equality plays no part."""
    volume = _chop_SA_SB([0, 0, 4])
    heights = {e["source_id"] for e in volume["dependency_edges"]
               if e["relation"] == "numerical"} - {"dt"}
    assert heights == {"SA_length", "SB_length"}
    assert volume["formula"]["text"] == "V = 1/3 × S(ABC) × SA = 8"


def test_ambiguous_height_gets_no_formula():
    """Apex not above a named base vertex: neither SA nor SB is perpendicular to the base and no distance to the
    base plane is measured (the stated lengths do not even fit the figure) ⇒ no verified height ⇒ fail closed: no
    card (the old "two candidates" lock, kept)."""
    volume = _chop_SA_SB([0, 0, 4])
    assert volume.get("formula")  # control: the perpendicular case has a card
    volume = _chop_SA_SB([1, 0, 4])
    assert "formula" not in volume
