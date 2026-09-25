# -*- coding: utf-8 -*-
"""Test suite cho lát cắt dọc: RECTANGULAR_BASE_PYRAMID_COMPILER_VERTICAL_SLICE.

Kiểm chứng các yêu cầu:
- Schema PyramidTopologySpec trong RequestContract
- Positive Case A (Hình chữ nhật: AB=3, AD=4, SA=6 -> V=24)
- Positive Case B (Hình vuông: AB=3, SA=6 -> V=18)
- Cấu trúc tô-pô: 5 đỉnh, 8 cạnh, 5 mặt, Euler V-E+F=2
- Xuất xứ: LAYOUT_DERIVED cho 5 điểm
- 7 ca âm bắt buộc fail-closed:
  1. Thiếu chiều cao SA
  2. Thiếu một cạnh của đáy chữ nhật
  3. Mâu thuẫn độ dài cạnh đáy
  4. Đáy không đủ điều kiện hình chữ nhật
  5. SA không vuông góc mặt phẳng đáy
  6. Chu trình đáy sai hoặc trùng đỉnh
  7. Có thêm obligation ngoài volume
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
    PyramidTopologySpec,
    RequestContract,
    norm_value,
)
from app.simulation.semantic_program.scale_normalization import SourceInvariant
from app.simulation.semantic_program.structured_relations import GeometricRelation
from app.simulation.semantic_program.validator import validate_semantic_program


# ─── FIXTURES & BUILDERS ──────────────────────────────────────────────────

def _build_rect_pyramid_contract(
    apex: str = "S",
    base_cycle: tuple[str, ...] = ("A", "B", "C", "D"),
    base_shape: str = "rectangle",
    len_ab: str | None = "3",
    len_ad: str | None = "4",
    len_sa: str | None = "6",
    has_perp_base: bool = True,
    has_perp_lateral: bool = True,
    perp_line: tuple[str, str] = ("S", "A"),
    perp_plane: tuple[str, ...] = ("A", "B", "C"),
    extra_obligations: tuple[Obligation, ...] = (),
    extra_invariants: tuple[SourceInvariant, ...] = (),
) -> RequestContract:
    """Xây dựng RequestContract chuẩn cho chóp đáy chữ nhật/vuông."""
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

    # Cạnh AD (chỉ bắt buộc với hình chữ nhật)
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

    # Chiều cao SA
    if len_sa is not None:
        invs.append(SourceInvariant(
            points=(base_cycle[0], apex),
            expected=str(len_sa),
            source_fact_id="f_sa",
            scale_symbol="",
            source_text="",
        ))
        val_sa = norm_value(len_sa)
        facts.append(InputFact(
            fact_id="f_sa",
            label="chiều cao SA",
            values=(val_sa, str(len_sa), f"{apex}{base_cycle[0]} = {len_sa}"),
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
            label="đáy vuông tại A",
            values=(f"{base_cycle[0]}{base_cycle[1]} ⊥ {base_cycle[0]}{base_cycle[3]}",),
        ))

    # Quan hệ cạnh bên vuông góc đáy
    if has_perp_lateral:
        rels.append(GeometricRelation(
            kind="perpendicular_line_plane",
            line=perp_line,
            plane=perp_plane,
            source_fact_id="f_perp_lat",
            model_assumption=False,
        ))
        facts.append(InputFact(
            fact_id="f_perp_lat",
            label="SA vuông góc đáy",
            values=(f"{perp_line[0]}{perp_line[1]} ⊥ ({''.join(perp_plane)})",),
        ))

    obs = (Obligation(kind="volume", container="khoi_chop", params={"witness": "v"}),) + extra_obligations

    topo = PyramidTopologySpec(
        solid_kind="pyramid",
        apex=apex,
        base_cycle=base_cycle,
        base_shape=base_shape,
    )

    return RequestContract(
        obligations=obs,
        input_facts=tuple(facts),
        source_invariants=tuple(invs),
        geometric_relations=tuple(rels),
        solid_topology=topo,
        problem_text=f"Cho hình chóp {apex}.{''.join(base_cycle)}...",
    )


# ─── 1. TOPOLOGY SPEC & CONTRACT INTEGRATION ──────────────────────────────

def test_pyramid_topology_spec_creation():
    """Khẳng định PyramidTopologySpec hợp lệ với solid_kind='pyramid'."""
    spec = PyramidTopologySpec(
        solid_kind="pyramid",
        apex="S",
        base_cycle=("A", "B", "C", "D"),
        base_shape="rectangle",
    )
    assert spec.solid_kind == "pyramid"
    assert spec.apex == "S"
    assert spec.base_cycle == ("A", "B", "C", "D")
    assert spec.base_shape == "rectangle"


def test_build_request_contract_with_pyramid_topology():
    """build_request_contract phân tích đúng solid_topology kiểu pyramid."""
    payload = {
        "input_facts": [
            {"id": "f1", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "f2", "kind": "float", "label": "AD", "value": ["4"]},
            {"id": "f3", "kind": "float", "label": "SA", "value": ["6"]},
        ],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "D"], "source_fact_id": "f1"},
            {"kind": "perpendicular_line_plane", "line": ["S", "A"], "plane": ["A", "B", "C"], "source_fact_id": "f3"},
        ],
        "obligations": [{"kind": "volume", "container": "khoi_chop", "witness": "v"}],
        "solid_topology": {
            "solid_kind": "pyramid",
            "apex": "S",
            "base_cycle": ["A", "B", "C", "D"],
            "base_shape": "rectangle",
        },
    }
    contract = build_request_contract(payload, domain="hinh_hoc")
    assert contract.solid_topology is not None
    assert isinstance(contract.solid_topology, PyramidTopologySpec)
    assert contract.solid_topology.apex == "S"
    assert contract.solid_topology.base_cycle == ("A", "B", "C", "D")


# ─── 2. POSITIVE CASE A: HÌNH CHỮ NHẬT (AB=3, AD=4, SA=6 -> V=24) ────────

def test_positive_case_a_rectangle_volume_24():
    """Ca dương A: Đáy chữ nhật AB=3, AD=4, SA=6 -> V=24."""
    contract = _build_rect_pyramid_contract(
        apex="S", base_cycle=("A", "B", "C", "D"), base_shape="rectangle",
        len_ab="3", len_ad="4", len_sa="6"
    )

    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID", f"Adapter thất bại: {ka.reason_code} {ka.diagnostics}"
    assert ka.graph is not None

    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "SUPPORTED", f"Eligibility thất bại: {el.reason_code} {el.diagnostics}"
    assert el.binding is not None
    assert el.binding.family_id == "rectangular_base_pyramid_volume"
    assert el.binding.variant == "rectangle"
    assert el.binding.len_adj1 == Fraction(3)
    assert el.binding.len_adj2 == Fraction(4)
    assert el.binding.len_height == Fraction(6)

    # Biên dịch
    bd = C.bien_dich(ka.graph)
    assert bd.status == "COMPILED"
    assert bd.program is not None

    # Thẩm định ngữ nghĩa
    val = validate_semantic_program(bd.program)
    assert val.ok, f"Validator từ chối: {val.error}"
    assert val.spec is not None

    # Thực thi tất định
    interp = SemanticProgramInterpreter()
    res = interp.execute(val.spec)
    assert res.status == "completed"
    assert res.final_memory.get("v") == Fraction(24)

    # Kiểm tra cấu trúc đa diện trong câu lệnh construct_pyramid
    pyramid_stmts = [s for s in bd.program["statements"] if s.get("kind") == "construct_solid"]
    assert len(pyramid_stmts) == 1
    solid = pyramid_stmts[0]

    vertices = solid["vertices"]
    faces = solid["faces"]
    assert len(vertices) == 5, f"Kỳ vọng 5 đỉnh, nhận {len(vertices)}"
    assert len(faces) == 5, f"Kỳ vọng 5 mặt, nhận {len(faces)}"

    # Thu thập tập các cạnh không hướng
    edges = set()
    for f in faces:
        n = len(f)
        for i in range(n):
            u, v = f[i], f[(i + 1) % n]
            edges.add(tuple(sorted((u, v))))
    assert len(edges) == 8, f"Kỳ vọng 8 cạnh, nhận {len(edges)}"

    # Euler characteristic: V - E + F = 5 - 8 + 5 = 2
    assert len(vertices) - len(edges) + len(faces) == 2

    # Xuất xứ: LAYOUT_DERIVED cho các điểm, GIVEN cho các độ dài đề cho
    points_mem = [m for m in bd.program["memory_declarations"] if m.get("type") == "point3"]
    assert len(points_mem) == 5
    for m in points_mem:
        assert m.get("provenance") == "LAYOUT_DERIVED"

    lengths_mem = {m["name"]: m for m in bd.program["memory_declarations"] if m.get("name", "").endswith("_length")}
    assert "AB_length" in lengths_mem
    assert "AD_length" in lengths_mem
    assert "SA_length" in lengths_mem
    for l_name, l_mem in lengths_mem.items():
        assert l_mem.get("provenance") == "GIVEN"
        assert l_mem.get("source_fact_id") in ("f_ab", "f_ad", "f_sa")

    # Scene3D validation: Đối tượng, Quá trình dựng (8 bước) và Chuỗi nhân quả
    from app.ai.pipeline import _dung_scene3d
    scene = _dung_scene3d(val.spec, contract)
    assert scene is not None
    solids = [obj for obj in scene.get("objects", []) if obj.get("type") == "solid"]
    assert len(solids) == 1
    assert len(solids[0]["vertices"]) == 5
    assert len(solids[0]["faces"]) == 5
    points = [obj for obj in scene.get("objects", []) if obj.get("type") == "point3"]
    assert {p.get("id") for p in points} == {"A", "B", "C", "D", "S"}

    # 8 bước sư phạm (step_index 0 đến 7)
    events = scene.get("events", [])
    assert len(events) == 8, f"Kỳ vọng 8 sự kiện hình thành, nhận {len(events)}"
    assert events[0]["action"] == "INIT" and events[0]["object"] is None
    assert events[1]["action"] in ("CREATE", "STEP") and events[1]["object"] == "day_ABCD"
    assert events[2]["action"] == "CREATE" and events[2]["object"] == "chieu_cao_SA"
    assert events[3]["action"] == "CREATE" and events[3]["object"] in ("canh_ben", "canh_ben_SC")
    assert events[4]["action"] == "CREATE" and events[4]["object"] == "khoi_chop"
    assert events[5]["action"] == "MEASURE" and events[5]["object"] == "dien_tich_day_ABCD"
    assert events[6]["action"] == "MEASURE" and events[6]["object"] == "the_tich_khoi_chop"
    assert events[7]["action"] == "MEASURE" and events[7]["object"] == "v"

    # Chuỗi nhân quả liên kết từ đáp số tới dữ kiện đề cho
    obj_by_id = {o["id"]: o for o in scene.get("objects", [])}
    assert "khoi_chop" in obj_by_id["the_tich_khoi_chop"]["depends"]
    assert "dien_tich_day_ABCD" in obj_by_id["the_tich_khoi_chop"]["depends"]
    assert "SA_length" in obj_by_id["the_tich_khoi_chop"]["depends"]
    assert "day_ABCD" in obj_by_id["dien_tich_day_ABCD"]["depends"]
    assert "AB_length" in obj_by_id["dien_tich_day_ABCD"]["depends"]
    assert "AD_length" in obj_by_id["dien_tich_day_ABCD"]["depends"]
    assert obj_by_id["v"]["depends"] == ["the_tich_khoi_chop"]


# ─── 3. POSITIVE CASE B: HÌNH VUÔNG (AB=3, SA=6 -> V=18) ───────────────────

def test_positive_case_b_square_volume_18():
    """Ca dương B: Đáy vuông AB=3, SA=6 -> V=18 (không cần khai AD)."""
    contract = _build_rect_pyramid_contract(
        apex="S", base_cycle=("A", "B", "C", "D"), base_shape="square",
        len_ab="3", len_ad=None, len_sa="6"
    )

    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID", f"Adapter thất bại: {ka.reason_code}"
    assert ka.graph is not None

    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "SUPPORTED", f"Eligibility thất bại: {el.reason_code} {el.diagnostics}"
    assert el.binding is not None
    assert el.binding.family_id == "rectangular_base_pyramid_volume"
    assert el.binding.variant == "square"
    assert el.binding.len_adj1 == Fraction(3)
    assert el.binding.len_adj2 == Fraction(3)
    assert el.binding.len_height == Fraction(6)

    # Biên dịch & thực thi
    bd = C.bien_dich(ka.graph)
    assert bd.status == "COMPILED"
    val = validate_semantic_program(bd.program)
    assert val.ok, val.error
    res = SemanticProgramInterpreter().execute(val.spec)
    assert res.status == "completed"
    assert res.final_memory.get("v") == Fraction(18)

    # Kiểm tra cấu trúc đa diện trong câu lệnh construct_pyramid
    pyramid_stmts = [s for s in bd.program["statements"] if s.get("kind") == "construct_solid"]
    assert len(pyramid_stmts) == 1
    solid = pyramid_stmts[0]

    vertices = solid["vertices"]
    faces = solid["faces"]
    assert len(vertices) == 5, f"Kỳ vọng 5 đỉnh, nhận {len(vertices)}"
    assert len(faces) == 5, f"Kỳ vọng 5 mặt, nhận {len(faces)}"

    # Thu thập tập các cạnh không hướng
    edges = set()
    for f in faces:
        n = len(f)
        for i in range(n):
            u, v = f[i], f[(i + 1) % n]
            edges.add(tuple(sorted((u, v))))
    assert len(edges) == 8, f"Kỳ vọng 8 cạnh, nhận {len(edges)}"

    # Euler characteristic: V - E + F = 5 - 8 + 5 = 2
    assert len(vertices) - len(edges) + len(faces) == 2

    # Xuất xứ: LAYOUT_DERIVED cho các điểm, GIVEN cho các độ dài đề cho
    points_mem = [m for m in bd.program["memory_declarations"] if m.get("type") == "point3"]
    assert len(points_mem) == 5
    for m in points_mem:
        assert m.get("provenance") == "LAYOUT_DERIVED"

    lengths_mem = {m["name"]: m for m in bd.program["memory_declarations"] if m.get("name", "").endswith("_length")}
    assert "AB_length" in lengths_mem
    assert "SA_length" in lengths_mem
    for l_name, l_mem in lengths_mem.items():
        assert l_mem.get("provenance") == "GIVEN"
        assert l_mem.get("source_fact_id") in ("f_ab", "f_sa")

    # Scene3D validation: Đối tượng, Quá trình dựng (8 bước) và Chuỗi nhân quả
    from app.ai.pipeline import _dung_scene3d
    scene = _dung_scene3d(val.spec, contract)
    assert scene is not None
    solids = [obj for obj in scene.get("objects", []) if obj.get("type") == "solid"]
    assert len(solids) == 1
    assert len(solids[0]["vertices"]) == 5
    assert len(solids[0]["faces"]) == 5
    points = [obj for obj in scene.get("objects", []) if obj.get("type") == "point3"]
    assert {p.get("id") for p in points} == {"A", "B", "C", "D", "S"}

    # 8 bước sư phạm (step_index 0 đến 7)
    events = scene.get("events", [])
    assert len(events) == 8, f"Kỳ vọng 8 sự kiện hình thành, nhận {len(events)}"
    assert events[0]["action"] == "INIT" and events[0]["object"] is None
    assert events[1]["action"] in ("CREATE", "STEP") and events[1]["object"] == "day_ABCD"
    assert events[2]["action"] == "CREATE" and events[2]["object"] == "chieu_cao_SA"
    assert events[3]["action"] == "CREATE" and events[3]["object"] in ("canh_ben", "canh_ben_SC")
    assert events[4]["action"] == "CREATE" and events[4]["object"] == "khoi_chop"
    assert events[5]["action"] == "MEASURE" and events[5]["object"] == "dien_tich_day_ABCD"
    assert events[6]["action"] == "MEASURE" and events[6]["object"] == "the_tich_khoi_chop"
    assert events[7]["action"] == "MEASURE" and events[7]["object"] == "v"

    # Chuỗi nhân quả liên kết từ đáp số tới dữ kiện đề cho
    obj_by_id = {o["id"]: o for o in scene.get("objects", [])}
    assert "khoi_chop" in obj_by_id["the_tich_khoi_chop"]["depends"]
    assert "dien_tich_day_ABCD" in obj_by_id["the_tich_khoi_chop"]["depends"]
    assert "SA_length" in obj_by_id["the_tich_khoi_chop"]["depends"]
    assert "day_ABCD" in obj_by_id["dien_tich_day_ABCD"]["depends"]
    assert "AB_length" in obj_by_id["dien_tich_day_ABCD"]["depends"]
    assert obj_by_id["v"]["depends"] == ["the_tich_khoi_chop"]


# ─── 4. CA ÂM BẮT BUỘC (FAIL-CLOSED) ──────────────────────────────────────

def test_negative_01_missing_height_sa():
    """Ca âm 1: Thiếu chiều cao SA -> fail-closed REQUIRED_FACT_MISSING."""
    contract = _build_rect_pyramid_contract(len_sa=None)
    ka = A.build_fact_graph(contract)
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "UNSUPPORTED_MISSING_FACT"
    assert el.reason_code == "REQUIRED_FACT_MISSING"
    assert "REQUIRED_LENGTH_MISSING" in el.diagnostics


def test_negative_02_missing_base_side_rectangle():
    """Ca âm 2: Hình chữ nhật thiếu một cạnh đáy -> fail-closed REQUIRED_FACT_MISSING."""
    contract = _build_rect_pyramid_contract(base_shape="rectangle", len_ad=None)
    ka = A.build_fact_graph(contract)
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "UNSUPPORTED_MISSING_FACT"
    assert el.reason_code == "REQUIRED_FACT_MISSING"
    assert "REQUIRED_LENGTH_MISSING" in el.diagnostics


def test_negative_03_conflicting_lengths():
    """Ca âm 3: Mâu thuẫn độ dài cạnh đáy -> fail-closed INVALID_CONFLICT."""
    # Khai báo cạnh AB = 3 và CD = 5 (trong hình chữ nhật AB phải bằng CD)
    extra = (
        SourceInvariant(points=("C", "D"), expected="5", source_fact_id="f_cd", scale_symbol="", source_text=""),
    )
    contract = _build_rect_pyramid_contract(extra_invariants=extra)
    ka = A.build_fact_graph(contract)
    if ka.status == "VALID" and ka.graph is not None:
        el = C.danh_gia_eligibility(ka.graph)
        assert el.status == "INVALID_CONFLICT"
    else:
        assert ka.status == "INVALID_CONFLICT"


def test_negative_04_base_not_rectangle_missing_perp():
    """Ca âm 4: ABCD không đủ điều kiện hình chữ nhật (thiếu góc vuông đáy)."""
    contract = _build_rect_pyramid_contract(base_shape="general", has_perp_base=False)
    ka = A.build_fact_graph(contract)
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "UNSUPPORTED_STRUCTURED_RELATION_MISSING"
    assert el.reason_code == "BASE_NOT_RECTANGLE"


def test_negative_05_sa_not_perpendicular_to_base():
    """Ca âm 5: SA không vuông góc mặt phẳng đáy -> fail-closed."""
    contract = _build_rect_pyramid_contract(has_perp_lateral=False)
    ka = A.build_fact_graph(contract)
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "UNSUPPORTED_STRUCTURED_RELATION_MISSING"


def test_negative_06_base_cycle_invalid_duplicate():
    """Ca âm 6: Chu trình đáy sai hoặc trùng đỉnh."""
    # 1. Đáy trùng đỉnh ('A', 'B', 'C', 'B') với quan hệ hình học hợp lệ
    contract_dup = RequestContract(
        input_facts=(
            InputFact(fact_id="f_ab", label="AB", values=("3",)),
            InputFact(fact_id="f_bc", label="BC", values=("4",)),
            InputFact(fact_id="f_sa", label="SA", values=("6",)),
        ),
        source_invariants=(
            SourceInvariant(points=("A", "B"), expected="3", source_fact_id="f_ab", scale_symbol="", source_text=""),
            SourceInvariant(points=("B", "C"), expected="4", source_fact_id="f_bc", scale_symbol="", source_text=""),
            SourceInvariant(points=("A", "S"), expected="6", source_fact_id="f_sa", scale_symbol="", source_text=""),
        ),
        geometric_relations=(
            GeometricRelation(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"), source_fact_id="f_ab"),
            GeometricRelation(kind="perpendicular_line_plane", line=("S", "A"), plane=("A", "B", "C"), source_fact_id="f_sa"),
        ),
        obligations=(Obligation(kind="volume", container="khoi_chop", params={"witness": "v"}),),
        solid_topology=PyramidTopologySpec(
            solid_kind="pyramid",
            apex="S",
            base_cycle=("A", "B", "C", "B"),
            base_shape="rectangle",
        ),
        problem_text="Cho hình chóp S.ABCB...",
    )
    ka = A.build_fact_graph(contract_dup)
    assert ka.status == "VALID"
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "INVALID_CONFLICT"
    assert el.reason_code == "DUPLICATE_VERTICES"

    # 2. Đáy sai số đỉnh (tam giác thay vì tứ giác)
    contract_tri = RequestContract(
        input_facts=contract_dup.input_facts,
        source_invariants=contract_dup.source_invariants,
        geometric_relations=contract_dup.geometric_relations,
        obligations=contract_dup.obligations,
        solid_topology=PyramidTopologySpec(
            solid_kind="pyramid",
            apex="S",
            base_cycle=("A", "B", "C"),
            base_shape="rectangle",
        ),
        problem_text="Cho hình chóp S.ABC...",
    )
    ka_tri = A.build_fact_graph(contract_tri)
    assert ka_tri.status == "VALID"
    assert ka_tri.graph is not None
    el_tri = C.danh_gia_eligibility(ka_tri.graph)
    assert el_tri.status == "UNSUPPORTED_MISSING_FACT"
    assert el_tri.reason_code == "BASE_NOT_QUADRILATERAL"


def test_negative_07_extra_unsupported_obligation():
    """Ca âm 7: Có thêm obligation chưa được hỗ trợ (vd angle)."""
    extra_ob = (Obligation(kind="angle_cos_sq", container="edge_SA", params={"witness": "cos_val"}),)
    contract = _build_rect_pyramid_contract(extra_obligations=extra_ob)
    ka = A.build_fact_graph(contract)
    assert ka.graph is not None
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "UNSUPPORTED_EXTRA_OBLIGATION"


# ─── 4. NON-VACUOUS PHASE 5 ASSERTIONS: BOUNDED SEGMENTS & FRAME VISIBILITY ─

def test_bounded_geometry_and_no_unbounded_rays():
    """Phase 5: Kiểm chứng SA, SB, SC, SD dùng construct_segment hữu hạn, không có tia/đường vô hạn."""
    contract = _build_rect_pyramid_contract(
        apex="S", base_cycle=("A", "B", "C", "D"), base_shape="rectangle",
        len_ab="3", len_ad="4", len_sa="6"
    )
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID" and ka.graph is not None
    bd = C.bien_dich(ka.graph)
    assert bd.status == "COMPILED" and bd.program is not None

    # 1. Statements compiler sinh ra phải dùng construct_segment, không dùng construct_line cho cạnh chóp
    segment_stmts = [s for s in bd.program["statements"] if s.get("kind") == "construct_segment"]
    line_stmts = [s for s in bd.program["statements"] if s.get("kind") == "construct_line"]
    assert len(segment_stmts) == 2, f"Kỳ vọng 2 câu lệnh construct_segment (SA và nhóm cạnh bên), nhận {len(segment_stmts)}"
    assert len(line_stmts) == 0, f"Không được sinh construct_line cho chóp hữu hạn, nhận {len(line_stmts)}"

    # 2. Kiểm tra câu lệnh SA
    sa_stmt = next(s for s in segment_stmts if s.get("target_var") == "chieu_cao_SA")
    assert sa_stmt["endpoint_a"] == "S" and sa_stmt["endpoint_b"] == "A"
    assert sa_stmt.get("label") == "Chiều cao SA"

    # 3. Kiểm tra câu lệnh lateral edges SB, SC, SD
    lateral_stmt = next(s for s in segment_stmts if s.get("target_var") == "canh_ben")
    assert len(lateral_stmt.get("items", [])) == 3
    items = {it["name"]: it for it in lateral_stmt["items"]}
    assert "canh_ben_SB" in items and items["canh_ben_SB"]["endpoint_a"] == "S" and items["canh_ben_SB"]["endpoint_b"] == "B"
    assert "canh_ben_SC" in items and items["canh_ben_SC"]["endpoint_a"] == "S" and items["canh_ben_SC"]["endpoint_b"] == "C"
    assert "canh_ben_SD" in items and items["canh_ben_SD"]["endpoint_a"] == "S" and items["canh_ben_SD"]["endpoint_b"] == "D"

    # 4. Scene3D objects: SA, SB, SC, SD đều là segment3, render='segment', có endpoint_ids chính xác
    val = validate_semantic_program(bd.program)
    assert val.ok and val.spec is not None
    from app.ai.pipeline import _dung_scene3d
    scene = _dung_scene3d(val.spec, contract)
    assert scene is not None

    objs = {o["id"]: o for o in scene["objects"]}
    for edge_id, (ep1, ep2) in [
        ("chieu_cao_SA", ("S", "A")),
        ("canh_ben_SB", ("S", "B")),
        ("canh_ben_SC", ("S", "C")),
        ("canh_ben_SD", ("S", "D")),
    ]:
        assert edge_id in objs, f"Thiếu object {edge_id} trong scene3d"
        obj = objs[edge_id]
        assert obj.get("type") == "segment3", f"{edge_id} phải có type='segment3', nhận {obj.get('type')}"
        assert obj.get("render") == "segment", f"{edge_id} phải có render='segment', nhận {obj.get('render')}"
        assert obj.get("endpoint_ids") == [ep1, ep2], f"{edge_id} endpoint_ids sai: {obj.get('endpoint_ids')}"
        assert "point_a" in obj and "point_b" in obj, f"{edge_id} thiếu point_a/point_b"

    # 5. Tuyệt đối không có unbounded line nào mang role EDGE hoặc HEIGHT_SEGMENT
    for o in scene["objects"]:
        if o.get("render") == "line" or o.get("type") == "line3":
            assert o.get("role") not in ("EDGE", "HEIGHT_SEGMENT", "chiều cao", "cạnh bên"), \
                f"Phát hiện unbounded line trái phép: {o['id']}"


def test_frame_visibility_and_event_sequence():
    """Phase 5: Kiểm chứng 8 bước hình thành và tính rõ ràng của Step 3."""
    contract = _build_rect_pyramid_contract(
        apex="S", base_cycle=("A", "B", "C", "D"), base_shape="rectangle",
        len_ab="3", len_ad="4", len_sa="6"
    )
    ka = A.build_fact_graph(contract)
    bd = C.bien_dich(ka.graph)
    val = validate_semantic_program(bd.program)
    from app.ai.pipeline import _dung_scene3d
    scene = _dung_scene3d(val.spec, contract)
    assert scene is not None

    events = scene.get("events", [])
    assert len(events) == 8, f"Kỳ vọng 8 bước hình thành, nhận {len(events)}"

    # Step 0: INIT
    assert events[0]["action"] == "INIT"
    assert events[0]["step_index"] == 0

    # Step 1: Base ABCD
    assert events[1]["object"] == "day_ABCD"
    assert events[1]["step_index"] == 1

    # Step 2: Chiều cao SA (hữu hạn, SA perp ABCD)
    assert events[2]["object"] == "chieu_cao_SA"
    assert events[2]["step_index"] == 2

    # Step 3: Dựng đồng thời SB, SC, SD
    assert events[3]["step_index"] == 3
    step3_objects = events[3].get("objects", [])
    assert "canh_ben_SB" in step3_objects, f"Step 3 phải có canh_ben_SB: {step3_objects}"
    assert "canh_ben_SC" in step3_objects, f"Step 3 phải có canh_ben_SC: {step3_objects}"
    assert "canh_ben_SD" in step3_objects, f"Step 3 phải có canh_ben_SD: {step3_objects}"

    # Step 4: Khối chóp hoàn chỉnh
    assert events[4]["object"] == "khoi_chop"
    assert events[4]["step_index"] == 4

    # Step 5: Diện tích đáy
    assert events[5]["object"] == "dien_tich_day_ABCD"
    assert events[5]["step_index"] == 5

    # Step 6: Thể tích chóp
    assert events[6]["object"] == "the_tich_khoi_chop"
    assert events[6]["step_index"] == 6

    # Step 7: Gán đáp số v
    assert events[7]["object"] == "v"
    assert events[7]["step_index"] == 7

    # Causal dependency closure từ v tới các đại lượng ban đầu
    obj_by_id = {o["id"]: o for o in scene["objects"]}
    assert set(obj_by_id["dien_tich_day_ABCD"]["depends"]) == {"AB_length", "AD_length", "day_ABCD"}
    assert set(obj_by_id["the_tich_khoi_chop"]["depends"]) == {"SA_length", "dien_tich_day_ABCD", "khoi_chop"}
    assert obj_by_id["v"]["depends"] == ["the_tich_khoi_chop"]

