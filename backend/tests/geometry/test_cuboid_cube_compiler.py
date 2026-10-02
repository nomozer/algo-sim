# -*- coding: utf-8 -*-
"""Test suite cho lát cắt dọc: CUBOID_CUBE_PRISM_SPECIALIZATION_VERTICAL_SLICE.

Kiểm chứng các yêu cầu:
- Contract & FactGraph có kiểu cho cuboid, cube, right square prism
- Positive Case CUBOID_P01 (3x4x5 -> V=60)
- Positive Case CUBE_P01 (edge=4 -> V=64 derived from single edge)
- Positive Case SQUARE_PRISM_CONTROL (base edge=3, height=7 -> V=63 != 27)
- Phân biệt rõ rệt cube và square prism
- 8 đỉnh, 12 cạnh, 6 mặt, Euler V - E + F = 8 - 12 + 6 = 2
- Xuất xứ: LAYOUT_DERIVED cho 8 điểm, GIVEN cho độ dài đề cho
- 10 ca âm bắt buộc fail-closed:
  1. Thiếu chiều cao
  2. Kích thước không dương
  3. Mâu thuẫn độ dài cạnh
  4. Sai khớp correspondence đáy-đỉnh
  5. Trùng đỉnh tô-pô
  6. Khối xiên (oblique) nhưng khai cuboid
  7. Đáy vuông nhưng thiếu bằng chứng cube
  8. Phân loại cube nhưng các cạnh mâu thuẫn
  9. Thừa obligation ngoài volume
  10. Nguồn text không hỗ trợ semantic classification
- Causal chain & Pedagogical trace
"""
from __future__ import annotations

from fractions import Fraction
import pytest

from app.simulation.geometry_compiler import compiler as C
from app.simulation.geometry_compiler import contract_adapter as A
from app.simulation.geometry_compiler import primitives as P
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import (
    InputFact,
    PrismTopologySpec,
    RequestContract,
    norm_value,
)
from app.simulation.semantic_program.scale_normalization import SourceInvariant
from app.simulation.semantic_program.structured_relations import GeometricRelation
from app.simulation.semantic_program.validator import validate_semantic_program


# ─── FIXTURES & BUILDERS ──────────────────────────────────────────────────

def _build_cuboid_prism_contract(
    base_cycle: tuple[str, ...] = ("A", "B", "C", "D"),
    top_cycle: tuple[str, ...] = ("A'", "B'", "C'", "D'"),
    correspondence: tuple[tuple[str, str], ...] = (("A", "A'"), ("B", "B'"), ("C", "C'"), ("D", "D'")),
    base_shape: str | None = "rectangle",
    lateral_structure: str | None = "right",
    solid_subkind: str | None = "cuboid",
    source_grounding: str | None = "hình hộp chữ nhật",
    len_ab: str | None = "3",
    len_ad: str | None = "4",
    len_aa_prime: str | None = "5",
    has_perp_base: bool = True,
    has_perp_lateral: bool = True,
    extra_obligations: tuple[Obligation, ...] = (),
    extra_invariants: tuple[SourceInvariant, ...] = (),
    extra_relations: tuple[GeometricRelation, ...] = (),
    problem_text: str = "",
) -> RequestContract:
    """Xây dựng RequestContract chuẩn cho cuboid / cube / right square prism."""
    invs: list[SourceInvariant] = []
    facts: list[InputFact] = []
    rels: list[GeometricRelation] = []

    # Cạnh AB
    if len_ab is not None:
        invs.append(SourceInvariant(
            points=(base_cycle[0], base_cycle[1]),
            expected=str(len_ab),
            source_fact_id="f_ab",
            scale_symbol="",
            source_text="",
        ))
        val_ab = norm_value(len_ab)
        facts.append(InputFact(
            fact_id="f_ab",
            label="cạnh AB",
            values=(val_ab, str(len_ab), f"{base_cycle[0]}{base_cycle[1]} = {len_ab}"),
        ))

    # Cạnh AD
    if len_ad is not None:
        invs.append(SourceInvariant(
            points=(base_cycle[0], base_cycle[3]),
            expected=str(len_ad),
            source_fact_id="f_ad",
            scale_symbol="",
            source_text="",
        ))
        val_ad = norm_value(len_ad)
        facts.append(InputFact(
            fact_id="f_ad",
            label="cạnh AD",
            values=(val_ad, str(len_ad), f"{base_cycle[0]}{base_cycle[3]} = {len_ad}"),
        ))

    # Cạnh bên AA'
    if len_aa_prime is not None:
        corr_dict = dict(correspondence)
        top_a = corr_dict.get(base_cycle[0], top_cycle[0])
        invs.append(SourceInvariant(
            points=(base_cycle[0], top_a),
            expected=str(len_aa_prime),
            source_fact_id="f_aa_prime",
            scale_symbol="",
            source_text="",
        ))
        val_aa = norm_value(len_aa_prime)
        facts.append(InputFact(
            fact_id="f_aa_prime",
            label=f"cạnh bên {base_cycle[0]}{top_a}",
            values=(val_aa, str(len_aa_prime), f"{base_cycle[0]}{top_a} = {len_aa_prime}"),
        ))

    invs.extend(extra_invariants)

    # Quan hệ vuông góc đáy
    if has_perp_base:
        rels.append(GeometricRelation(
            kind="perpendicular_lines",
            line=(base_cycle[0], base_cycle[1]),
            other_line=(base_cycle[0], base_cycle[3]),
            source_fact_id="f_perp_base",
            model_assumption=False,
        ))
        facts.append(InputFact(
            fact_id="f_perp_base",
            label=f"đáy vuông tại {base_cycle[0]}",
            values=(f"{base_cycle[0]}{base_cycle[1]} ⊥ {base_cycle[0]}{base_cycle[3]}",),
        ))

    # Quan hệ cạnh bên vuông góc đáy
    if has_perp_lateral:
        corr_dict = dict(correspondence)
        top_a = corr_dict.get(base_cycle[0], top_cycle[0])
        rels.append(GeometricRelation(
            kind="perpendicular_line_plane",
            line=(top_a, base_cycle[0]),
            plane=(base_cycle[0], base_cycle[1], base_cycle[3]),
            source_fact_id="f_perp_lat",
            model_assumption=False,
        ))
        facts.append(InputFact(
            fact_id="f_perp_lat",
            label=f"{base_cycle[0]}{top_a} vuông góc đáy",
            values=(f"{base_cycle[0]}{top_a} ⊥ mặt đáy",),
        ))

    rels.extend(extra_relations)

    obligations = list(extra_obligations) or [
        Obligation(kind="volume", container="khoi_hop", params={"witness": "V"})
    ]

    topo = PrismTopologySpec(
        solid_kind="prism",
        base_cycle=base_cycle,
        top_cycle=top_cycle,
        correspondence=correspondence,
        base_shape=base_shape,
        lateral_structure=lateral_structure,
        solid_subkind=solid_subkind,
        source_grounding=source_grounding,
    )

    contract = RequestContract(
        problem_text=problem_text or f"Cho khối {source_grounding or 'lăng trụ'}.",
        domain="hinh_hoc",
        input_facts=tuple(facts),
        source_invariants=tuple(invs),
        geometric_relations=tuple(rels),
        obligations=tuple(obligations),
        solid_topology=topo,
    )
    return contract


# ─── POSITIVE CASES ────────────────────────────────────────────────────────

def test_positive_01_cuboid_p01():
    """CUBOID_P01: Hình hộp chữ nhật ABCD.A'B'C'D' với AB=3, AD=4, AA'=5 -> V=60."""
    contract = _build_cuboid_prism_contract(
        base_shape="rectangle",
        solid_subkind="cuboid",
        source_grounding="hình hộp chữ nhật",
        len_ab="3",
        len_ad="4",
        len_aa_prime="5",
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None

    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "SUPPORTED"
    assert el.binding is not None
    assert isinstance(el.binding, C.RangBuocCuboid)
    assert el.binding.family_id == "rectangular_cuboid_volume"
    assert el.binding.solid_subkind == "cuboid"
    assert el.binding.len_adj1 == Fraction(3)
    assert el.binding.len_adj2 == Fraction(4)
    assert el.binding.len_height == Fraction(5)

    res = C.bien_dich(ka.graph)
    assert res.status == "COMPILED"
    assert res.program is not None

    # Validate program qua Pydantic & semantic validator
    val = validate_semantic_program(res.program)
    assert val.ok, val.error

    # Thực thi qua interpreter
    interp = SemanticProgramInterpreter()
    sim_res = interp.execute(val.spec)
    assert sim_res.status == "completed"

    # Biến witness V mang giá trị 60
    assert "V" in sim_res.final_memory
    vol = sim_res.final_memory["V"]
    assert vol == Fraction(60)

    # Kiểm tra Scene3D
    from app.ai.pipeline import _dung_scene3d
    scene = _dung_scene3d(val.spec, contract)
    assert scene is not None
    objects = scene.get("objects", [])

    # 8 đỉnh
    points = [o for o in objects if o.get("type") == "point3"]
    assert len(points) == 8
    p_ids = {p["id"] for p in points}
    assert p_ids == {"A", "B", "C", "D", "A_prime", "B_prime", "C_prime", "D_prime"}

    # 1 solid
    solids = [o for o in objects if o.get("type") == "solid"]
    assert len(solids) == 1
    solid = solids[0]
    assert len(solid["vertices"]) == 8
    assert len(solid["faces"]) == 6

    # Euler: 8 - 12 + 6 = 2
    edges = set()
    for face in solid["faces"]:
        n = len(face)
        for i in range(n):
            u, v = face[i], face[(i + 1) % n]
            edges.add(tuple(sorted((u, v))))
    assert len(edges) == 12
    assert len(points) - len(edges) + len(solid["faces"]) == 2


def test_positive_02_cube_p01():
    """CUBE_P01: Hình lập phương ABCD.A'B'C'D' với edge=4 -> V=64.
    Chỉ cho duy nhất cạnh AB=4, AD và AA' tự động dẫn xuất từ phân loại cube.
    """
    contract = _build_cuboid_prism_contract(
        base_shape="square",
        solid_subkind="cube",
        source_grounding="hình lập phương",
        len_ab="4",
        len_ad=None,        # KHÔNG cho AD
        len_aa_prime=None,  # KHÔNG cho AA'
        has_perp_lateral=False,
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None

    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "SUPPORTED"
    assert el.binding is not None
    assert isinstance(el.binding, C.RangBuocCuboid)
    assert el.binding.family_id == "cube_volume"
    assert el.binding.solid_subkind == "cube"
    assert el.binding.len_adj1 == Fraction(4)
    assert el.binding.len_adj2 == Fraction(4)
    assert el.binding.len_height == Fraction(4)

    res = C.bien_dich(ka.graph)
    assert res.status == "COMPILED"
    assert res.program is not None

    val = validate_semantic_program(res.program)
    assert val.ok, val.error

    interp = SemanticProgramInterpreter()
    sim_res = interp.execute(val.spec)
    assert sim_res.status == "completed"
    assert sim_res.final_memory["V"] == Fraction(64)


def test_positive_03_square_prism_control():
    """SQUARE_PRISM_CONTROL: Lăng trụ đứng đáy vuông AB=3, chiều cao AA'=7 -> V=63 != 27.
    Phải được phân loại là right_square_prism_volume, KHÔNG ĐƯỢC NHẬN LÀ CUBE.
    """
    contract = _build_cuboid_prism_contract(
        base_shape="square",
        solid_subkind="right_square_prism",
        source_grounding="lăng trụ đứng có đáy là hình vuông",
        len_ab="3",
        len_ad=None,  # Đáy vuông nên AD = AB = 3
        len_aa_prime="7",
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None

    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "SUPPORTED"
    assert el.binding is not None
    assert isinstance(el.binding, C.RangBuocCuboid)
    # Phân loại khác cube:
    assert el.binding.family_id == "right_square_prism_volume"
    assert el.binding.solid_subkind == "right_square_prism"
    assert el.binding.len_adj1 == Fraction(3)
    assert el.binding.len_adj2 == Fraction(3)
    assert el.binding.len_height == Fraction(7)

    res = C.bien_dich(ka.graph)
    assert res.status == "COMPILED"
    assert res.program is not None

    val = validate_semantic_program(res.program)
    assert val.ok, val.error

    interp = SemanticProgramInterpreter()
    sim_res = interp.execute(val.spec)
    assert sim_res.status == "completed"
    assert sim_res.final_memory["V"] == Fraction(63)


# ─── FAIL-CLOSED NEGATIVE CASES ───────────────────────────────────────────

def test_negative_01_missing_height():
    """Ca âm 1: Thiếu chiều cao trong hình hộp chữ nhật hoặc lăng trụ đứng -> fail-closed."""
    contract = _build_cuboid_prism_contract(
        base_shape="rectangle",
        solid_subkind="cuboid",
        len_ab="3",
        len_ad="4",
        len_aa_prime=None,  # Thiếu chiều cao
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "UNSUPPORTED_MISSING_FACT"
    assert el.reason_code == "REQUIRED_FACT_MISSING"
    assert "REQUIRED_LENGTH_MISSING" in el.diagnostics


def test_negative_02_non_positive_dimension():
    """Ca âm 2: Kích thước không dương (<= 0) -> fail-closed INVALID_NON_POSITIVE_LENGTH."""
    contract = _build_cuboid_prism_contract(
        base_shape="rectangle",
        solid_subkind="cuboid",
        len_ab="-3",  # Cạnh âm
        len_ad="4",
        len_aa_prime="5",
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "INVALID_NON_POSITIVE_LENGTH"
    assert el.reason_code == "NON_POSITIVE_LENGTH"


def test_negative_03_conflicting_lengths():
    """Ca âm 3: Mâu thuẫn độ dài hai cạnh đối của đáy chữ nhật -> fail-closed INVALID_CONFLICT."""
    extra = (
        SourceInvariant(points=("C", "D"), expected="5", source_fact_id="f_cd", scale_symbol="", source_text=""),
    )
    contract = _build_cuboid_prism_contract(
        base_shape="rectangle",
        solid_subkind="cuboid",
        len_ab="3",
        len_ad="4",
        len_aa_prime="5",
        extra_invariants=extra,
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "INVALID_CONFLICT"
    assert "RECTANGLE_OPPOSITE_EDGES_UNEQUAL" in el.diagnostics


def test_negative_04_malformed_correspondence():
    """Ca âm 4: Correspondence đáy-đỉnh sai lệch (chỉ có 3 cặp) -> fail-closed INVALID_CONFLICT."""
    bad_corr = (("A", "A'"), ("B", "B'"), ("C", "C'"))
    contract = _build_cuboid_prism_contract(correspondence=bad_corr)
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "INVALID_CONFLICT"
    assert "MALFORMED_BASE_TOP_CORRESPONDENCE" in el.diagnostics


def test_negative_05_repeated_topology_vertex():
    """Ca âm 5: Đáy hoặc đỉnh có đỉnh lặp lại hoặc đáy-đỉnh trùng nhau -> fail-closed INVALID_CONFLICT."""
    bad_top_cycle = ("A'", "B'", "C'", "B'")
    corr = (("A", "A'"), ("B", "B'"), ("C", "C'"), ("D", "B'"))
    contract = _build_cuboid_prism_contract(top_cycle=bad_top_cycle, correspondence=corr)
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "INVALID_CONFLICT"
    assert "REPEATED_TOPOLOGY_VERTEX" in el.diagnostics


def test_negative_06_oblique_lateral_structure():
    """Ca âm 6: Cấu trúc cạnh bên xiên (oblique) nhưng khai cuboid -> fail-closed INVALID_CONFLICT."""
    contract = _build_cuboid_prism_contract(
        lateral_structure="oblique",
        solid_subkind="cuboid",
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "INVALID_CONFLICT"
    assert "OBLIQUE_LATERAL_EDGE_FOR_CUBOID" in el.diagnostics


def test_negative_07_square_base_missing_cube_evidence():
    """Ca âm 7: Đáy vuông nhưng không có bằng chứng cube và thiếu chiều cao -> KHÔNG được tự nhận là cube."""
    contract = _build_cuboid_prism_contract(
        base_shape="square",
        solid_subkind=None,  # Không khai cube
        source_grounding="lăng trụ",  # Không chứa lập phương
        len_ab="4",
        len_ad=None,
        len_aa_prime=None,  # Không có chiều cao
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    # Vì không có căn cứ cube, nó coi là right_square_prism và thiếu chiều cao!
    assert el.status == "UNSUPPORTED_MISSING_FACT"
    assert el.reason_code == "REQUIRED_FACT_MISSING"


def test_negative_08_cube_conflicting_edges():
    """Ca âm 8: Phân loại cube nhưng các cạnh cho mâu thuẫn (AB=4, AA'=5) -> fail-closed INVALID_CONFLICT."""
    contract = _build_cuboid_prism_contract(
        base_shape="square",
        solid_subkind="cube",
        source_grounding="hình lập phương",
        len_ab="4",
        len_aa_prime="5",  # Mâu thuẫn với AB=4
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "INVALID_CONFLICT"
    assert "CUBE_EDGES_UNEQUAL" in el.diagnostics


def test_negative_09_extra_obligation():
    """Ca âm 9: Có thêm obligation ngoài volume (vd area) -> fail-closed UNSUPPORTED_EXTRA_OBLIGATION."""
    extra_ob = (
        Obligation(kind="volume", container="khoi_hop", params={"witness": "V"}),
        Obligation(kind="area", container="day_ABCD", params={"witness": "S"}),
    )
    contract = _build_cuboid_prism_contract(extra_obligations=extra_ob)
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "UNSUPPORTED_EXTRA_OBLIGATION"
    assert el.reason_code == "EXTRA_OBLIGATION"


def test_negative_10_ungrounded_semantic_classification():
    """Ca âm 10: Phân loại cube nhưng source_grounding rỗng hoặc không khớp -> fail-closed."""
    contract = _build_cuboid_prism_contract(
        base_shape="square",
        solid_subkind="cube",
        source_grounding="",  # Rỗng, không có căn cứ từ đề bài
        len_ab="4",
        len_ad=None,
        len_aa_prime=None,
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "UNSUPPORTED_MISSING_FACT"
    assert el.reason_code == "UNSUPPORTED_SEMANTIC_GROUNDING_MISSING"


# ─── PEDAGOGICAL TRACE & PROVENANCE ───────────────────────────────────────

def test_pedagogical_trace_and_causal_chain():
    """Kiểm tra trace sư phạm và chuỗi nhân quả causal chain.

    W14 moved formation to the shared pass: đáy trên và các cạnh bên không còn do
    compiler viết tay mà do `semantic_program.formation` bổ sung cho MỌI chương
    trình. Trace compiler chỉ còn đáy dưới (phép đo diện tích cần nó); độ phủ vai trò
    PRISM_LIKE được kiểm trên cảnh ĐÃ bổ sung — đúng cảnh học sinh thấy.
    """
    contract = _build_cuboid_prism_contract(
        base_shape="rectangle",
        solid_subkind="cuboid",
        source_grounding="hình hộp chữ nhật",
        len_ab="3",
        len_ad="4",
        len_aa_prime="5",
    )
    ka = A.build_fact_graph(contract)
    res = C.bien_dich(ka.graph)
    assert res.status == "COMPILED"

    steps = res.construction_steps
    assert len(steps) >= 9

    # Thứ tự các bước sư phạm
    # 1. Đặt các đỉnh đáy và đỉnh trên
    decl_steps = [s for s in steps if s.primitive_id == "declare_point"]
    assert len(decl_steps) == 8

    # 2. Dựng đáy dưới (đáy trên + cạnh bên: bước bổ sung, kiểm ở mục 3)
    poly_steps = [s for s in steps if s.primitive_id == "construct_polygon"]
    assert len(poly_steps) == 1
    assert "đáy dưới" in poly_steps[0].mo_ta.lower()

    # 3. Cảnh ĐÃ bổ sung: đáy → đáy trên → cạnh bên → khép khối, đúng thứ tự
    from app.ai.pipeline import _dung_scene3d

    scene = _dung_scene3d(validate_semantic_program(res.program).spec, contract)
    buoc = scene["formation"]["steps"]
    idx = [next(k for k, s in enumerate(buoc) if r in s["formation_roles"])
           for r in ("CONSTRUCT_BASE", "CONSTRUCT_TRANSLATED_FACE",
                     "CONSTRUCT_LATERAL_BOUNDARY", "CLOSE_SOLID")]
    assert idx == sorted(idx) and len(set(idx)) == 4, idx

    # 4. Bao đóng khối
    prism_steps = [s for s in steps if s.primitive_id == "construct_prism"]
    assert len(prism_steps) == 1

    # 5. Đo đạc & gán
    meas_steps = [s for s in steps if s.primitive_id == "measure_quantity"]
    assert len(meas_steps) == 3  # area, distance (height), volume

    assign_steps = [s for s in steps if s.primitive_id == "assign_final_memory"]
    assert len(assign_steps) == 1
    assert assign_steps[0].derived_fact_ids == ("V",)

    # Causal chain kiểm tra trong memory_declarations
    mem_decls = {d["name"]: d for d in res.program["memory_declarations"]}

    # Điểm mang provenance LAYOUT_DERIVED
    for pt in ("A", "B", "C", "D", "A_prime", "B_prime", "C_prime", "D_prime"):
        assert mem_decls[pt]["provenance"] == "LAYOUT_DERIVED"

    # Dữ kiện độ dài đề cho mang provenance GIVEN
    assert mem_decls["AB_length"]["provenance"] == "GIVEN"
    assert mem_decls["AD_length"]["provenance"] == "GIVEN"
    assert mem_decls["AA_prime_length"]["provenance"] == "GIVEN"


def test_cube_causal_chain_single_edge_reuse():
    """Cube: chỉ cạnh đề cho là GIVEN; hai kích thước còn lại phải được suy ra."""
    contract = _build_cuboid_prism_contract(
        base_shape="square",
        solid_subkind="cube",
        source_grounding="hình lập phương",
        len_ab="4",
        len_ad=None,
        len_aa_prime=None,
    )
    ka = A.build_fact_graph(contract)
    res = C.bien_dich(ka.graph)
    mem_decls = {d["name"]: d for d in res.program["memory_declarations"]}

    # Cạnh đề cho mang GIVEN
    assert mem_decls["AB_length"]["provenance"] == "GIVEN"
    assert mem_decls["AB_length"]["initial_value"] == "4"
    src_id = mem_decls["AB_length"]["source_fact_id"]
    assert src_id is not None

    # AD và AA′ không xuất hiện như dữ kiện số trong đề. Compiler phải biểu
    # diễn chúng bằng phép suy ra thực thi được, không sao chép provenance
    # GIVEN/source_fact_id của AB sang hai khai báo khác.
    for name in ("AD_length", "AA_prime_length"):
        assert mem_decls[name].get("provenance") != "GIVEN"
        assert mem_decls[name].get("source_fact_id") is None
        assert mem_decls[name].get("initial_value") is None

    assignments = {
        st["target_var"]: st
        for st in res.program["statements"]
        if st.get("kind") == "assign"
    }
    assert assignments["AD_length"]["expr"] == {"kind": "var", "name": "AB_length"}
    assert assignments["AA_prime_length"]["expr"] == {"kind": "var", "name": "AB_length"}


def test_square_prism_inferred_second_base_edge_is_derived_not_given():
    """Đáy vuông cho AB=3 không được biến AD=3 thành dữ kiện GIVEN giả."""
    contract = _build_cuboid_prism_contract(
        base_shape="square",
        solid_subkind="right_square_prism",
        source_grounding="lăng trụ đứng đáy vuông",
        len_ab="3",
        len_ad=None,
        len_aa_prime="7",
    )
    ka = A.build_fact_graph(contract)
    res = C.bien_dich(ka.graph)
    mem_decls = {d["name"]: d for d in res.program["memory_declarations"]}

    assert mem_decls["AB_length"]["provenance"] == "GIVEN"
    assert mem_decls["AA_prime_length"]["provenance"] == "GIVEN"
    assert mem_decls["AD_length"].get("provenance") != "GIVEN"
    assert mem_decls["AD_length"].get("source_fact_id") is None
    assert mem_decls["AD_length"].get("initial_value") is None

    derived = next(
        st for st in res.program["statements"]
        if st.get("kind") == "assign" and st.get("target_var") == "AD_length"
    )
    assert derived["expr"] == {"kind": "var", "name": "AB_length"}


def test_volume_narration_is_independent_from_localized_title():
    """Đổi prose của title không được đổi semantics/công thức của trace."""
    contract = _build_cuboid_prism_contract(
        base_shape="square",
        solid_subkind="cube",
        source_grounding="hình lập phương",
        len_ab="4",
        len_ad=None,
        len_aa_prime=None,
    )
    ka = A.build_fact_graph(contract)
    compiled = C.bien_dich(ka.graph)

    narrations = []
    for title in ("Thể tích khối lập phương", "Tiêu đề trung tính"):
        program = {**compiled.program, "title": title}
        valid = validate_semantic_program(program)
        assert valid.ok
        executed = SemanticProgramInterpreter().execute(valid.spec)
        volume_step = next(
            s for s in executed.trace
            if s.action == "assign" and s.target.startswith("the_tich_")
        )
        narrations.append(volume_step.tier1_narration)

    assert narrations[0] == narrations[1]
    assert narrations[0] == "Tính thể tích V = a³ = 64."


# ─── PHASE 3 ACCEPTANCE: DEDICATED FACT_GRAPH TESTS ────────────────────────

def test_phase3_build_fact_graph_cuboid_p01():
    """Phase 3 Gate: build_fact_graph cho CUBOID_P01 sinh graph hợp lệ với 8 nút điểm và stable IDs."""
    contract = _build_cuboid_prism_contract(
        base_shape="rectangle",
        solid_subkind="cuboid",
        source_grounding="hình hộp chữ nhật",
        len_ab="3",
        len_ad="4",
        len_aa_prime="5",
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None

    # 8 điểm với stable IDs
    point_nodes = {n.node_id: n for n in ka.graph.nut_theo_loai("point")}
    expected_pts = {"A", "B", "C", "D", "A_prime", "B_prime", "C_prime", "D_prime"}
    assert set(point_nodes.keys()) == expected_pts
    for pt in expected_pts:
        assert point_nodes[pt].provenance == "GIVEN"

    # AdaptedPrismTopology có kiểu
    topo = ka.graph.solid_topology
    assert topo is not None
    assert topo.solid_kind == "prism"
    assert topo.base_cycle == ("A", "B", "C", "D")
    assert topo.top_cycle == ("A_prime", "B_prime", "C_prime", "D_prime")
    assert topo.solid_subkind == "cuboid"
    assert topo.grounding_status == "VALID"
    assert topo.display_labels["A_prime"] == "A′"

    # Độ dài chuẩn tắc
    f_ab = ka.graph.do_dai("A", "B")
    f_ad = ka.graph.do_dai("A", "D")
    f_aa = ka.graph.do_dai("A", "A_prime")
    assert f_ab is not None and f_ab.value == "3" and f_ab.status == "GIVEN"
    assert f_ad is not None and f_ad.value == "4" and f_ad.status == "GIVEN"
    assert f_aa is not None and f_aa.value == "5" and f_aa.status == "GIVEN"


def test_phase3_build_fact_graph_cube_p01():
    """Phase 3 Gate: build_fact_graph cho CUBE_P01 sinh graph hợp lệ với 1 cạnh nguồn và subkind=cube."""
    contract = _build_cuboid_prism_contract(
        base_shape="square",
        solid_subkind="cube",
        source_grounding="hình lập phương",
        len_ab="4",
        len_ad=None,
        len_aa_prime=None,
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None

    topo = ka.graph.solid_topology
    assert topo is not None
    assert topo.solid_subkind == "cube"
    assert topo.grounding_status == "VALID"

    f_ab = ka.graph.do_dai("A", "B")
    assert f_ab is not None and f_ab.value == "4" and f_ab.source_fact_id == "f_ab"
    assert ka.graph.do_dai("A", "D") is None
    assert ka.graph.do_dai("A", "A_prime") is None


def test_phase3_build_fact_graph_square_prism_control():
    """Phase 3 Gate: build_fact_graph cho SQUARE_PRISM_CONTROL với cạnh đáy=3, chiều cao=7."""
    contract = _build_cuboid_prism_contract(
        base_shape="square",
        solid_subkind="right_square_prism",
        source_grounding="hình lăng trụ đứng có đáy là hình vuông",
        len_ab="3",
        len_ad=None,
        len_aa_prime="7",
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID"
    assert ka.graph is not None

    topo = ka.graph.solid_topology
    assert topo is not None
    assert topo.solid_subkind == "right_square_prism"
    assert topo.base_shape == "square"

    f_ab = ka.graph.do_dai("A", "B")
    f_aa = ka.graph.do_dai("A", "A_prime")
    assert f_ab is not None and f_ab.value == "3"
    assert f_aa is not None and f_aa.value == "7"


def test_phase3_build_fact_graph_fail_closed_contradiction():
    """Phase 3 Gate: build_fact_graph bác bỏ trực tiếp mâu thuẫn độ dài đoạn thẳng trên cùng 1 đoạn."""
    contract = _build_cuboid_prism_contract(
        base_shape="rectangle",
        solid_subkind="cuboid",
        len_ab="3",
        extra_invariants=(
            SourceInvariant(
                points=("A", "B"),
                expected="4",  # Cùng đoạn AB nhưng giá trị 4 != 3
                source_fact_id="f_ab_conflict",
                scale_symbol="",
                source_text="",
            ),
        ),
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "INVALID_CONFLICT"
    assert ka.graph is None


def test_trace_contract_coherence_and_provenance():
    """Kiểm tra trace mạch lạc, gồm cả bước suy dẫn kích thước có thật.

    W14 moved formation to the shared pass: chạy trên chương trình ĐÃ bổ sung
    (`formation.hoan_thien_dung_hinh`) — đúng chương trình route và cảnh chạy; đáy
    trên và nhóm cạnh bên nay là hai bước do bước bổ sung chèn, không do compiler.
    """
    from app.simulation.semantic_program.formation import hoan_thien_dung_hinh
    from app.simulation.semantic_program.simulation_state import build_simulation_state
    from app.simulation.semantic_program.scene3d import build_scene3d

    for case_kind, pfn in [
        ("cuboid", lambda: _build_cuboid_prism_contract(base_shape="rectangle", solid_subkind="cuboid", len_ab="3", len_ad="4", len_aa_prime="5")),
        ("cube", lambda: _build_cuboid_prism_contract(base_shape="square", solid_subkind="cube", source_grounding="hình lập phương", len_ab="4", len_ad=None, len_aa_prime=None)),
        ("square_prism", lambda: _build_cuboid_prism_contract(base_shape="square", solid_subkind="right_square_prism", source_grounding="lăng trụ đứng đáy vuông", len_ab="3", len_ad=None, len_aa_prime="7")),
    ]:
        contract = pfn()
        ka = A.build_fact_graph(contract)
        res = C.bien_dich(ka.graph)
        val = validate_semantic_program(res.program)
        assert val.ok
        spec = hoan_thien_dung_hinh(val.spec, contract).spec
        interp = SemanticProgramInterpreter()
        sim_res = interp.execute(spec)
        state = build_simulation_state(spec, sim_res, contract)
        scene = build_scene3d(state)

        # 1. Cuboid uses only explicit dimensions. Cube and square prism add
        # one executable step for each equality-derived dimension.
        expected_steps = {"cuboid": 9, "cube": 11, "square_prism": 10}[case_kind]
        assert len(sim_res.trace) == expected_steps
        assert len(scene["events"]) == expected_steps
        trace_indices = [s.step_index for s in sim_res.trace]
        event_indices = [e["step_index"] for e in scene["events"]]
        assert trace_indices == list(range(expected_steps))
        assert event_indices == list(range(expected_steps))

        # 2. Every event references existing object in scene3d.objects (or None for INIT)
        existing_obj_ids = {o["id"] for o in scene["objects"]}
        for evt in scene["events"]:
            if evt["action"] == "INIT":
                assert evt["object"] is None
            else:
                # Event object can be either a direct scene object ID or a
                # group name (e.g. 'canh_ben') whose sub-objects are listed
                # in evt["objects"] — consistent with pyramid event contract.
                sub_ids = evt.get("objects") or []
                if evt["object"] not in existing_obj_ids:
                    assert sub_ids and all(s in existing_obj_ids for s in sub_ids), (
                        f"Event references non-existent object {evt['object']} "
                        f"in {case_kind} without valid sub-objects"
                    )
            for sub_id in (evt.get("objects") or []):
                assert sub_id in existing_obj_ids

        # 3. Byte-consistent narration between trace and scene events
        for s, e in zip(sim_res.trace, scene["events"]):
            assert s.tier1_narration == e["explanation"]

        # 4. Zero machine IDs in narrations and display labels
        banned_tokens = ("_prime", "khoi_", "dien_tich_", "chieu_cao_", "the_tich_", "point3", "solid")
        for s in sim_res.trace:
            for token in banned_tokens:
                assert token not in s.tier1_narration, f"Token {token} leaked in narration: {s.tier1_narration}"
        for o in scene["objects"]:
            for token in ("_prime", "khoi_", "dien_tich_", "chieu_cao_", "the_tich_"):
                assert token not in str(o.get("label", "")), f"Token {token} leaked in label: {o.get('label')}"
                if o.get("notation"):
                    assert token not in str(o.get("notation")), f"Token {token} leaked in notation: {o.get('notation')}"

        # 5. Provenance: points are layout-derived; only explicit lengths are
        # GIVEN, while equality-derived dimensions are DERIVED by statements.
        points = [o for o in scene["objects"] if o["type"] == "point3"]
        assert len(points) == 8
        for pt in points:
            assert pt["source"].get("provenance") == "LAYOUT_DERIVED"
            assert pt["origin"] == "free"

        quantities = [o for o in scene["objects"] if o["type"] == "quantity"]
        lengths = {q["id"]: q for q in quantities if q["id"].endswith("_length")}
        expected = {
            "cuboid": {
                "AB_length": "GIVEN", "AD_length": "GIVEN",
                "AA_prime_length": "GIVEN",
            },
            "cube": {
                "AB_length": "GIVEN", "AD_length": None,
                "AA_prime_length": None,
            },
            "square_prism": {
                "AB_length": "GIVEN", "AD_length": None,
                "AA_prime_length": "GIVEN",
            },
        }[case_kind]
        assert set(lengths) == set(expected)
        for name, provenance in expected.items():
            assert lengths[name]["source"].get("provenance") == provenance
            if provenance == "GIVEN":
                assert lengths[name]["source"].get("fact_id") is not None
            else:
                assert lengths[name]["source"].get("instruction") == "assign"
