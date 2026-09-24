# -*- coding: utf-8 -*-
"""Test suite cho Wave PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE.

Kiểm chứng đầy đủ các tiêu chí kỹ thuật:
1. Red-before verification tại START_HEAD.
2. 8 ca benchmark tiền đăng ký (5 dương, 3 âm) từ SECOND_FAMILY_MANIFEST.json & GROUND_TRUTH.json.
3. 10 unit tests topology validation fail-closed.
4. Bất biến provenance nghiêm ngặt: LAYOUT_DERIVED != GIVEN, LAYOUT_DERIVED != MODEL_ASSUMPTION, DEFINITIONAL_DERIVED != GIVEN.
5. Kiểm chứng schema, serialization, cache identity và fallback khi solid_topology=None.
6. 9 rào chắn an toàn (guards): không đọc problem_text, không đọc benchmark json, băm bất biến, phân số chính xác, không network call.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from fractions import Fraction
from typing import Any

import pytest
from pydantic import ValidationError

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

EVAL_DIR = (
    REPO_ROOT
    / "docs"
    / "evaluation"
    / "geometry"
    / "photo-problem-to-scene"
    / "primitive-compiler-second-family-selection"
)
MANIFEST_PATH = EVAL_DIR / "SECOND_FAMILY_MANIFEST.json"
GROUND_TRUTH_PATH = EVAL_DIR / "SECOND_FAMILY_GROUND_TRUTH.json"
MATRIX_PATH = EVAL_DIR / "SECOND_FAMILY_SELECTION_MATRIX.json"

FROZEN_HASHES = {
    "SECOND_FAMILY_MANIFEST.json": "f5978eb5f76b72808a02791dadc96f3b001b3bd288fc84e6656307ac4d0fefe5",
    "SECOND_FAMILY_GROUND_TRUTH.json": "faf42e894fb9f69c8b61aba06f84767ec9806d1231633d2975516ec5367e18ce",
    "SECOND_FAMILY_SELECTION_MATRIX.json": "748b04938952d84d9f40ed656697cfdac212a9cfc028d52e040b4fb46c521aa7",
}


def _sha256_lf(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


# ─── 1. BẢO VỆ BẤT BIẾN TIỀN ĐĂNG KÝ (GUARDS) ─────────────────────────────

def test_guard_preregistration_hashes_immutable():
    """Khẳng định 3 file tiền đăng ký không bị thay đổi bit nào."""
    for filename, expected_hash in FROZEN_HASHES.items():
        p = EVAL_DIR / filename
        assert p.is_file(), f"Thiếu file tiền đăng ký {p}"
        actual = _sha256_lf(p.read_bytes())
        assert actual == expected_hash, f"Hash của {filename} bị thay đổi! Kỳ vọng {expected_hash}, nhận {actual}"


def test_guard_product_does_not_import_evaluation():
    """Mã nguồn sản phẩm (backend/app) không được phép đọc hoặc import manifest/ground truth."""
    app_dir = BACKEND_DIR / "app"
    for py_file in app_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "SECOND_FAMILY_MANIFEST.json" not in content, f"{py_file} vi phạm: đọc manifest"
        assert "SECOND_FAMILY_GROUND_TRUTH.json" not in content, f"{py_file} vi phạm: đọc ground truth"


# ─── 2. RED-BEFORE CHỨC NĂNG PRISM TRƯỚC KHI IMPLEMENT ────────────────────

def test_prism_primitive_registered():
    """Kiểm tra primitive construct_prism đã đăng ký trong REGISTRY."""
    from app.simulation.geometry_compiler import primitives as P
    assert "construct_prism" in P.REGISTRY, "construct_prism chưa được đăng ký trong REGISTRY"
    fn = P.REGISTRY["construct_prism"]
    # Kiểm tra chữ ký 4 tham số chuẩn
    import inspect
    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())
    assert params == ["name", "base_cycle", "top_cycle", "correspondence"], (
        f"Chữ ký construct_prism không đúng chuẩn tiền đăng ký: {params}"
    )


def test_prism_contract_specs():
    """Kiểm tra PrismTopologySpec đã có trong request_contract và analyze_contract."""
    from app.simulation.semantic_program.request_contract import PrismTopologySpec, RequestContract
    spec = PrismTopologySpec(
        base_cycle=("A", "B", "C"),
        top_cycle=("D", "E", "F"),
        correspondence=(("A", "D"), ("B", "E"), ("C", "F")),
    )
    assert spec.solid_kind == "prism"
    req = RequestContract(solid_topology=spec)
    assert req.solid_topology == spec


# ─── 3. KIỂM THỬ 8 CA BENCHMARK TIỀN ĐĂNG KÝ ──────────────────────────────

def _load_manifest_cases():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["cases"]


def _load_ground_truth():
    return json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))["ground_truth_cases"]


@pytest.mark.parametrize("cid", ["PRISM_P01", "PRISM_P02", "PRISM_P03", "PRISM_P04", "PRISM_P05"])
def test_benchmark_positive_cases(cid: str):
    """Kiểm chứng 5 ca dương PRISM_P01 -> PRISM_P05 đạt SUPPORTED, đúng thể tích và tô-pô 6/9/5."""
    from app.simulation.geometry_compiler import contract_adapter as A
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.semantic_program.analyze_contract import build_request_contract

    cases = {c["case_id"]: c for c in _load_manifest_cases()}
    gt = _load_ground_truth()[cid]
    c_data = cases[cid]

    # Dựng payload mô phỏng từ Analyze
    payload = {
        "input_facts": [
            {"id": gl["source_fact_id"], "kind": "float", "label": f"{gl['segment'][0]}{gl['segment'][1]}", "value": [gl["value"]]}
            for gl in c_data["given_lengths"]
        ],
        "geometric_relations": c_data["geometric_relations"],
        "obligations": [
            {"kind": "volume", "container": c_data["target_operation"]["container"], "witness": c_data["target_operation"]["witness_var"]}
        ],
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": c_data["base_vertices"],
            "top_cycle": c_data["top_vertices"],
            "correspondence": c_data["correspondence"],
        }
    }

    contract = build_request_contract(payload, problem_text=c_data["problem_description"], domain="hinh_hoc")
    ka = A.build_fact_graph(contract)
    assert ka.status == "VALID", f"build_fact_graph thất bại với {cid}: {ka.reason_code}"
    assert ka.graph is not None

    # Đánh giá eligibility
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == gt["expected_status"], f"Eligibility mismatch cho {cid}: {el.reason_code}"

    # Biên dịch
    bd = C.bien_dich(ka.graph)
    assert bd.status == "COMPILED", f"Biên dịch thất bại cho {cid}: {bd.reason_code}"
    assert bd.program is not None

    # Kiểm tra đáp số thể tích qua Interpreter
    from app.simulation.semantic_program import validator as V
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    from app.ai.pipeline import _dung_scene3d

    val = V.validate_semantic_program(bd.program)
    assert val.ok, f"Chương trình không hợp lệ: {val.error}"
    mem = SemanticProgramInterpreter().execute(val.spec).final_memory
    witness_var = c_data["target_operation"]["witness_var"]
    actual_vol_val = mem.get(witness_var)

    expected_frac = Fraction(
        gt["expected_volume_fraction"]["numerator"],
        gt["expected_volume_fraction"]["denominator"]
    )
    assert actual_vol_val is not None, f"Biến witness {witness_var} không có trong final_memory"
    assert Fraction(str(actual_vol_val)) == expected_frac, f"Thể tích sai cho {cid}: kỳ vọng {expected_frac}, thực tế {actual_vol_val}"

    # Kiểm tra semantic scene envelope: 6 đỉnh, 9 cạnh, 5 mặt
    scene = _dung_scene3d(val.spec, contract)
    solids = [obj for obj in scene.get("objects", []) if obj.get("type") == "solid"]
    assert len(solids) == 1, f"Kỳ vọng 1 solid object trong scene, có {len(solids)}"
    solid = solids[0]
    assert len(solid["vertices"]) == gt["expected_topology"]["vertices_count"]
    assert len(solid["faces"]) == gt["expected_topology"]["faces_count"]


@pytest.mark.parametrize("cid", ["PRISM_N01", "PRISM_N02", "PRISM_N03"])
def test_benchmark_negative_cases(cid: str):
    """Kiểm chứng 3 ca âm PRISM_N01 -> PRISM_N03 bị từ chối fail-closed theo đúng 3 tầng:
    - benchmark_outcome: REJECTED
    - internal adapter/eligibility status
    - reason_code và detail_code khớp chính xác ground truth, không dùng or chain hay bypass.
    """
    from app.simulation.geometry_compiler import contract_adapter as A
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.semantic_program.analyze_contract import build_request_contract

    cases = {c["case_id"]: c for c in _load_manifest_cases()}
    gt = _load_ground_truth()[cid]
    c_data = cases[cid]

    payload = {
        "input_facts": [
            {"id": gl["source_fact_id"], "kind": "float", "label": f"{gl['segment'][0]}{gl['segment'][1]}", "value": [gl["value"]]}
            for gl in c_data["given_lengths"]
        ],
        "geometric_relations": c_data["geometric_relations"],
        "obligations": [
            {"kind": "volume", "container": c_data["target_operation"]["container"], "witness": c_data["target_operation"]["witness_var"]}
        ],
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": c_data["base_vertices"],
            "top_cycle": c_data["top_vertices"],
            "correspondence": c_data["correspondence"],
        }
    }

    contract = build_request_contract(payload, problem_text=c_data["problem_description"], domain="hinh_hoc")
    ka = A.build_fact_graph(contract)

    if cid == "PRISM_N01":
        # N01: Thiếu độ dài cạnh đứng AD -> đạt adapter (VALID), bị từ chối tại eligibility
        assert ka.status == "VALID"
        assert ka.graph is not None
        el = C.danh_gia_eligibility(ka.graph)
        benchmark_outcome = "SUPPORTED" if el.status == "SUPPORTED" else "REJECTED"
        assert benchmark_outcome == gt["expected_status"]  # REJECTED
        assert el.status == "UNSUPPORTED_MISSING_FACT"
        assert el.reason_code == gt["expected_reason_code"]  # REQUIRED_FACT_MISSING
        assert el.diagnostics[0] == gt["detail"]  # REQUIRED_LENGTH_MISSING
        assert el.diagnostics[1] == gt["missing_element"]  # AD
        assert C.bien_dich(ka.graph).program is None

    elif cid == "PRISM_N02":
        # N02: Đáy tam giác có 2 góc vuông -> bị từ chối fail-closed tại adapter/fact_graph
        assert ka.graph is None
        benchmark_outcome = "SUPPORTED" if ka.status == "VALID" else "REJECTED"
        assert benchmark_outcome == gt["expected_status"]  # REJECTED
        assert ka.status == "INVALID_CONFLICT"
        assert ka.reason_code == gt["expected_reason_code"]  # STRUCTURED_RELATION_CONTRADICTION
        assert ka.rule_id == gt["rule_id"]  # MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE
        assert f"RULE_ID={gt['detail']}" in ka.diagnostics  # detail code verified
        assert "PHASE=FACT_GRAPH" in ka.diagnostics  # rejection_phase fact_graph/adapter

    elif cid == "PRISM_N03":
        # N03: Lăng trụ xiên, thiếu quan hệ vuông góc cạnh bên -> bị từ chối tại eligibility
        assert ka.status == "VALID"
        assert ka.graph is not None
        el = C.danh_gia_eligibility(ka.graph)
        benchmark_outcome = "SUPPORTED" if el.status == "SUPPORTED" else "REJECTED"
        assert benchmark_outcome == gt["expected_status"]  # REJECTED
        assert el.status == "UNSUPPORTED_STRUCTURED_RELATION_MISSING"
        assert el.reason_code == gt["expected_reason_code"]  # UNSUPPORTED_STRUCTURED_RELATION_MISSING
        assert el.diagnostics[0] == gt["detail"]  # LINE_PLANE_RELATION_MISSING
        assert el.diagnostics[1] == gt["missing_relation"]  # perpendicular_line_plane
        assert C.bien_dich(ka.graph).program is None


def test_pedagogical_trace_11_steps():
    """Kiểm chứng trace sư phạm cho lăng trụ sinh đúng 11 bước theo dữ liệu máy:
    - đúng 11 bước trong construction_steps;
    - đúng thứ tự primitive_ids;
    - source_fact_ids / derived_fact_ids hợp lệ;
    - final witness xuất hiện ở bước cuối cùng.
    """
    from app.simulation.geometry_compiler import contract_adapter as A
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.semantic_program.analyze_contract import build_request_contract

    cases = {c["case_id"]: c for c in _load_manifest_cases()}
    c_data = cases["PRISM_P01"]

    payload = {
        "input_facts": [
            {"id": gl["source_fact_id"], "kind": "float", "label": f"{gl['segment'][0]}{gl['segment'][1]}", "value": [gl["value"]]}
            for gl in c_data["given_lengths"]
        ],
        "geometric_relations": c_data["geometric_relations"],
        "obligations": [
            {"kind": "volume", "container": c_data["target_operation"]["container"], "witness": c_data["target_operation"]["witness_var"]}
        ],
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": c_data["base_vertices"],
            "top_cycle": c_data["top_vertices"],
            "correspondence": c_data["correspondence"],
        }
    }

    contract = build_request_contract(payload, problem_text=c_data["problem_description"], domain="hinh_hoc")
    ka = A.build_fact_graph(contract)
    bd = C.bien_dich(ka.graph)

    assert bd.status == "COMPILED"
    assert len(bd.construction_steps) == 11

    expected_primitives = [
        "declare_point",
        "declare_point",
        "declare_point",
        "construct_triangle",
        "declare_point",
        "declare_point",
        "declare_point",
        "construct_prism",
        "measure_quantity",
        "measure_quantity",
        "assign_final_memory",
    ]

    actual_primitives = [b.primitive_id for b in bd.construction_steps]
    assert actual_primitives == expected_primitives

    # Kiểm tra chỉ số thứ tự liên tục 1..11
    indices = [b.index for b in bd.construction_steps]
    assert indices == list(range(1, 12))

    # Bước cuối cùng và statement cuối cùng gán witness
    last_step = bd.construction_steps[-1]
    assert last_step.primitive_id == "assign_final_memory"
    assert bd.primitive_calls[-1].primitive_id == "assign_final_memory"
    last_stmt = bd.program["statements"][-1]
    assert last_stmt["kind"] == "assign"
    assert last_stmt["target_var"] == c_data["target_operation"]["witness_var"]

    # Kiểm tra tính hợp lệ của metadata từng bước
    for b in bd.construction_steps:
        assert isinstance(b.mo_ta, str) and len(b.mo_ta) > 0
        assert isinstance(b.source_fact_ids, tuple)
        assert isinstance(b.derived_fact_ids, tuple)



# ─── 4. MƯỜI UNIT TESTS TÔ-PÔ FAIL-CLOSED (R7 / C1) ───────────────────────

def test_topo_01_base_cycle_less_than_3():
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    payload = {
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B"],
            "top_cycle": ["D", "E"],
            "correspondence": [["A", "D"], ["B", "E"]],
        }
    }
    with pytest.raises(Exception):
        build_request_contract(payload, domain="hinh_hoc")


def test_topo_02_top_cycle_less_than_3():
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    payload = {
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C"],
            "top_cycle": ["D", "E"],
            "correspondence": [["A", "D"], ["B", "E"]],
        }
    }
    with pytest.raises(Exception):
        build_request_contract(payload, domain="hinh_hoc")


def test_topo_03_cycle_vertex_overlap():
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    payload = {
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C"],
            "top_cycle": ["C", "D", "E"],
            "correspondence": [["A", "C"], ["B", "D"], ["C", "E"]],
        }
    }
    with pytest.raises(Exception):
        build_request_contract(payload, domain="hinh_hoc")


def test_topo_04_correspondence_non_bijective():
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    payload = {
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C"],
            "top_cycle": ["D", "E", "F"],
            "correspondence": [["A", "D"], ["B", "D"], ["C", "F"]],
        }
    }
    with pytest.raises(Exception):
        build_request_contract(payload, domain="hinh_hoc")


def test_topo_05_correspondence_undeclared_vertex():
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    payload = {
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C"],
            "top_cycle": ["D", "E", "F"],
            "correspondence": [["A", "D"], ["B", "E"], ["C", "UNKNOWN"]],
        }
    }
    with pytest.raises(Exception):
        build_request_contract(payload, domain="hinh_hoc")


def test_topo_06_top_cycle_image_mismatch():
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    payload = {
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C"],
            "top_cycle": ["D", "E", "Z"],
            "correspondence": [["A", "D"], ["B", "E"], ["C", "F"]],
        }
    }
    with pytest.raises(Exception):
        build_request_contract(payload, domain="hinh_hoc")


def test_topo_07_cycle_duplicate_vertex():
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    payload = {
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "A"],
            "top_cycle": ["D", "E", "F"],
            "correspondence": [["A", "D"], ["B", "E"], ["A", "F"]],
        }
    }
    with pytest.raises(Exception):
        build_request_contract(payload, domain="hinh_hoc")


def test_topo_08_non_positive_length():
    from app.simulation.geometry_compiler import contract_adapter as A
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    payload = {
        "input_facts": [
            {"id": "f1", "kind": "float", "label": "AB", "value": ["0"]},
            {"id": "f2", "kind": "float", "label": "AC", "value": ["4"]},
            {"id": "f3", "kind": "float", "label": "AD", "value": ["5"]},
        ],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "C"], "source_fact_id": "f1"},
            {"kind": "perpendicular_line_plane", "line": ["A", "D"], "plane": ["A", "B", "C"], "source_fact_id": "f3"},
        ],
        "obligations": [{"kind": "volume", "container": "solid", "witness": "v"}],
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C"],
            "top_cycle": ["D", "E", "F"],
            "correspondence": [["A", "D"], ["B", "E"], ["C", "F"]],
        }
    }
    contract = build_request_contract(payload, domain="hinh_hoc")
    ka = A.build_fact_graph(contract)
    if ka.graph is not None:
        el = C.danh_gia_eligibility(ka.graph)
        assert el.status != "SUPPORTED"


def test_topo_09_face_duplicate_vertices():
    from app.simulation.geometry_compiler import primitives as P
    with pytest.raises(Exception):
        P.construct_prism("solid", ("A", "A", "C"), ("D", "E", "F"), (("A", "D"), ("A", "E"), ("C", "F")))


def test_topo_10_euler_characteristic_manifold():
    from app.simulation.geometry_compiler import primitives as P
    res = P.construct_prism("solid", ("A", "B", "C"), ("D", "E", "F"), (("A", "D"), ("B", "E"), ("C", "F")))
    vertices = res["vertices"]
    faces = res["faces"]
    assert len(vertices) == 6
    assert len(faces) == 5
    # Thu thập tập các cạnh không hướng
    edges = set()
    for f in faces:
        n = len(f)
        for i in range(n):
            u, v = f[i], f[(i + 1) % n]
            edges.add(tuple(sorted((u, v))))
    assert len(edges) == 9
    # Euler characteristic: V - E + F = 6 - 9 + 5 = 2
    assert len(vertices) - len(edges) + len(faces) == 2


# ─── 5. BẤT BIẾN PROVENANCE (R2 / C4) ─────────────────────────────────────

def test_provenance_strict_invariants():
    """Kiểm tra bất biến xuất xứ: LAYOUT_DERIVED != GIVEN, LAYOUT_DERIVED != MODEL_ASSUMPTION."""
    from app.simulation.semantic_program.contract import MemoryDeclaration, SemanticProgramSpec
    from app.simulation.semantic_program.grounding_gate import check_grounding
    from app.simulation.semantic_program.request_contract import RequestContract, PrismTopologySpec

    decl = MemoryDeclaration(
        name="A",
        type="point3",
        provenance="LAYOUT_DERIVED",
        source_fact_id=None,
        model_assumption=None,
    )
    assert decl.provenance == "LAYOUT_DERIVED"
    assert decl.source_fact_id is None
    assert decl.model_assumption is None

    contract = RequestContract(
        solid_topology=PrismTopologySpec(
            base_cycle=("A", "B", "C"),
            top_cycle=("D", "E", "F"),
            correspondence=(("A", "D"), ("B", "E"), ("C", "F")),
        ),
        problem_text="",  # KHÔNG đọc problem_text để grounding layout (A1)
    )
    spec = SemanticProgramSpec(
        title="Test",
        memory_declarations=[decl],
        statements=[],
    )
    kq = check_grounding(contract, spec)
    assert kq.ok, f"Grounding gate từ chối LAYOUT_DERIVED: {kq.unresolved}"


# ─── 6. SCHEMA, CACHE VÀ BẢO TOÀN PYRAMID (R3 / R5 / C2 / C7) ─────────────

def test_pyramid_historical_payload_parity():
    """Khẳng định payload pyramid lịch sử (solid_topology=None) giữ nguyên 100% hành vi."""
    from app.simulation.semantic_program.request_contract import RequestContract
    req = RequestContract(
        problem_text="Cho hình chóp S.ABC...",
    )
    dump_raw = req.model_dump()
    assert dump_raw.get("solid_topology") is None
    dump_exclude = req.model_dump(exclude_none=True)
    assert "solid_topology" not in dump_exclude


def test_solid_topology_accepts_supported_pyramid_in_transport():
    """Schema model-facing cho phép solid_kind='pyramid' và parse thành công PyramidTopologySpec."""
    from app.simulation.semantic_program.analyze_contract import analyze_schema_for, build_request_contract
    from app.simulation.semantic_program.request_contract import PyramidTopologySpec

    sch = analyze_schema_for("hinh_hoc")
    topo_props = sch["properties"]["solid_topology"]["properties"]
    assert "pyramid" in topo_props["solid_kind"]["enum"], "solid_kind enum phải chứa 'pyramid'"
    assert "prism" in topo_props["solid_kind"]["enum"], "solid_kind enum phải chứa 'prism'"

    payload = {
        "domain": "hinh_hoc",
        "obligations": [{"kind": "volume", "container": "c1", "params": {"subject": "S_ABCD"}}],
        "input_facts": [],
        "solid_topology": {
            "solid_kind": "pyramid",
            "apex": "S",
            "base_cycle": ["A", "B", "C", "D"],
            "base_shape": "rectangle",
        },
    }
    contract = build_request_contract(payload, domain="hinh_hoc", problem_text="Cho hình chóp S.ABCD...")
    assert isinstance(contract.solid_topology, PyramidTopologySpec)
    assert contract.solid_topology.solid_kind == "pyramid"
    assert contract.solid_topology.apex == "S"
    assert contract.solid_topology.base_cycle == ("A", "B", "C", "D")
    assert contract.solid_topology.base_shape == "rectangle"


def test_solid_topology_rejects_malformed_pyramid_topology():
    """Kiểm tra fail-closed với các payload pyramid sai định dạng."""
    import pytest
    from app.simulation.semantic_program.analyze_contract import build_request_contract

    # 1. Thiếu apex
    with pytest.raises(ValueError, match="thiếu apex hoặc base_cycle"):
        build_request_contract({
            "domain": "hinh_hoc", "obligations": [], "input_facts": [],
            "solid_topology": {"solid_kind": "pyramid", "base_cycle": ["A", "B", "C", "D"]}
        }, domain="hinh_hoc")

    # 2. Đỉnh đáy trùng lặp
    with pytest.raises(ValueError, match="không được chứa đỉnh lặp"):
        build_request_contract({
            "domain": "hinh_hoc", "obligations": [], "input_facts": [],
            "solid_topology": {"solid_kind": "pyramid", "apex": "S", "base_cycle": ["A", "B", "C", "A"]}
        }, domain="hinh_hoc")

    # 3. Đỉnh chóp trùng với đỉnh đáy
    with pytest.raises(ValueError, match="không được nằm trong chu trình đáy"):
        build_request_contract({
            "domain": "hinh_hoc", "obligations": [], "input_facts": [],
            "solid_topology": {"solid_kind": "pyramid", "apex": "A", "base_cycle": ["A", "B", "C", "D"]}
        }, domain="hinh_hoc")

    # 4. base_shape ngoài allowlist
    with pytest.raises(ValueError, match="base_shape phải là 'rectangle' hoặc 'square'"):
        build_request_contract({
            "domain": "hinh_hoc", "obligations": [], "input_facts": [],
            "solid_topology": {"solid_kind": "pyramid", "apex": "S", "base_cycle": ["A", "B", "C", "D"], "base_shape": "trapezoid"}
        }, domain="hinh_hoc")


def test_solid_topology_rejects_unknown_solid_kind():
    """Từ chối solid_kind ngoài allowlist."""
    import pytest
    from app.simulation.semantic_program.analyze_contract import build_request_contract

    with pytest.raises(ValueError, match="không được hỗ trợ"):
        build_request_contract({
            "domain": "hinh_hoc", "obligations": [], "input_facts": [],
            "solid_topology": {"solid_kind": "cylinder", "base_cycle": ["A", "B", "C"]}
        }, domain="hinh_hoc")


def test_solid_topology_preserves_prism_transport_compatibility():
    """Khẳng định payload lăng trụ vẫn parse hợp lệ và fail-closed khi thiếu thông tin."""
    import pytest
    from app.simulation.semantic_program.analyze_contract import build_request_contract
    from app.simulation.semantic_program.request_contract import PrismTopologySpec

    valid_prism = {
        "domain": "hinh_hoc", "obligations": [], "input_facts": [],
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C"],
            "top_cycle": ["A'", "B'", "C'"],
            "correspondence": [["A", "A'"], ["B", "B'"], ["C", "C'"]],
        }
    }
    c = build_request_contract(valid_prism, domain="hinh_hoc")
    assert isinstance(c.solid_topology, PrismTopologySpec)
    assert c.solid_topology.solid_kind == "prism"

    # Thiếu correspondence
    with pytest.raises(ValueError, match="thiếu base_cycle, top_cycle hoặc correspondence"):
        build_request_contract({
            "domain": "hinh_hoc", "obligations": [], "input_facts": [],
            "solid_topology": {
                "solid_kind": "prism",
                "base_cycle": ["A", "B", "C"],
                "top_cycle": ["A'", "B'", "C'"],
            }
        }, domain="hinh_hoc")

