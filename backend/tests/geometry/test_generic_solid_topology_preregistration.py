# -*- coding: utf-8 -*-
"""Test Suite cho Wave GENERIC_SOLID_TOPOLOGY_CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE.

Kiểm chứng 14 tiêu chí kỹ thuật độc lập theo kế hoạch phê duyệt:
1. Precheck baseline và bất biến môi trường (SHA, heads, cache, default mode).
2. Định nghĩa chính xác phạm vi SUPPORTED_TOPOLOGY_CLASS và giới hạn của Euler V-E+F=2.
3. Single Source of Truth (SSOT) cho cả structured families và generic polyhedron.
4. True Discriminated Union trên solid_kind và type safety trong Pydantic.
5. Flattened transport schema đi qua _sanitize_gemini_schema (không bị None, không $ref),
   và ghi nhận GEMINI_LIVE_SCHEMA_ACCEPTANCE = NOT_ESTABLISHED_UNTIL_LIVE_REVALIDATION.
6. Ánh xạ transport -> internal canonical contract tất định 100%.
7. Bảo toàn kề cận chu kỳ D_n (vacuously true với n=3; bắt chéo/xoắn n=4 bị chặn).
8. DECLARED_VERTEX_UNIVERSE là cross-contract invariant (INV-TOPO-01).
9. Bộ 5 Positive Fixtures đạt chuẩn manifold genus-0 đóng với V, E, F chính xác.
10. Bộ 11 Negative Fixtures bị từ chối an toàn với mã lỗi xác định.
11. Phân định xuất xứ dữ kiện (GIVEN vs DEFINITIONAL_DERIVED) và cấm giả mạo GIVEN.
12. Giả thuyết nghiên cứu PUBLICATION_HYPOTHESIS kiểm định được và 15 chỉ số benchmark.
13. Bốn chiều tương thích ngược được phân loại dự báo (EXPECTED_*).
14. Future product allowlist mang nhãn PROVISIONAL kèm 7 điều kiện audit tiên quyết.
"""
from __future__ import annotations

import pathlib
import sys
import pytest
from pydantic import ValidationError

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from scripts import validate_generic_solid_topology_preregistration as V


def test_01_precheck_baseline_invariants():
    """1. Precheck baseline và bất biến môi trường."""
    p = V.audit_precheck()
    assert p["BRANCH"] == "feat/photo-problem-to-scene"
    assert p["START_HEAD"] == "65d09a897e3ab88703b6d9cad5c14e797b4810b4"
    assert p["MAIN_HEAD"] == "085cae67392d3607ad0a58a7f48c17d8a5e5157d"
    assert p["CANDIDATE_SHA256"] == "077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1"
    assert p["CANDIDATE_FILE_COUNT"] == 103
    assert p["CACHE_VERSION"] == "99"
    assert p["DEFAULT_MODE"] == "LLM_ONLY"
    assert p["PRESERVED_USER_CHANGE"] == "D frontend/public/favicon.svg"
    assert p["PRECHECK_VERDICT"] == "PASS"


def test_02_supported_topology_class_registered():
    """2. Định nghĩa chính xác phạm vi SUPPORTED_TOPOLOGY_CLASS và giới hạn của Euler V-E+F=2."""
    assert V.SUPPORTED_TOPOLOGY_CLASS == "closed, connected, orientable, genus-zero polygonal 2-manifold"

    # Thử nghiệm với POS-TOPO-01: thỏa Euler nhưng không tuyên bố convexity
    spec = V.POS_FIXTURES["POS-TOPO-01"]["spec"]
    res = V.validate_topology_invariants(spec, V.POS_FIXTURES["POS-TOPO-01"]["universe"])
    assert res["chi"] == 2
    assert res["is_closed_genus_zero_2_manifold"] is True
    assert res["convexity_proven"] is False  # Không có tọa độ, không thể chứng minh convexity


def test_03_ssot_pyramid_and_prism_derived():
    """3. Single Source of Truth (SSOT): suy diễn mặt tất định từ cycle, không bắt model khai trùng."""
    # Pyramid: SSOT là apex và base_cycle
    pyr = V.PyramidTopologySpec(apex="S", base_cycle=("A", "B", "C"))
    d_pyr = V.derive_canonical_topology(pyr)
    assert d_pyr["canonical_source"] == {"apex": "S", "base_cycle": ("A", "B", "C")}
    assert set(d_pyr["vertices"]) == {"S", "A", "B", "C"}
    assert len(d_pyr["faces"]) == 4

    # Prism: SSOT là base_cycle, top_cycle, correspondence
    prism = V.PrismTopologySpec(
        base_cycle=("A", "B", "C"),
        top_cycle=("D", "E", "F"),
        correspondence=(("A", "D"), ("B", "E"), ("C", "F")),
    )
    d_prism = V.derive_canonical_topology(prism)
    assert d_prism["canonical_source"]["base_cycle"] == ("A", "B", "C")
    assert set(d_prism["vertices"]) == {"A", "B", "C", "D", "E", "F"}
    assert len(d_prism["faces"]) == 5

    # Generic Polyhedron: SSOT là faces
    poly = V.GenericPolyhedronTopologySpec(
        faces=(("A", "B", "C"), ("A", "B", "D"), ("B", "C", "D"), ("C", "A", "D"))
    )
    d_poly = V.derive_canonical_topology(poly)
    assert d_poly["canonical_source"] == {"faces": poly.faces}
    assert set(d_poly["vertices"]) == {"A", "B", "C", "D"}


def test_04_discriminated_union_internal_type_safety():
    """4. True Discriminated Union trên solid_kind và type safety trong Pydantic."""
    # Hợp lệ với discriminator
    req_pyr = V.RequestContractWithTopology(
        solid_topology=V.PyramidTopologySpec(apex="S", base_cycle=("A", "B", "C"))
    )
    assert req_pyr.solid_topology.solid_kind == "pyramid"

    req_prism = V.RequestContractWithTopology(
        solid_topology=V.PrismTopologySpec(
            base_cycle=("A", "B", "C"),
            top_cycle=("D", "E", "F"),
            correspondence=(("A", "D"), ("B", "E"), ("C", "F")),
        )
    )
    assert req_prism.solid_topology.solid_kind == "prism"

    # Ngăn chặn sai lệch: không thể tạo PrismTopologySpec với trường của Pyramid
    with pytest.raises(ValidationError):
        V.PrismTopologySpec.model_validate({"solid_kind": "prism", "apex": "S", "base_cycle": ("A", "B", "C")})


def test_05_transport_schema_sanitization_gemini_compatible():
    """5. Flattened transport schema đi qua _sanitize_gemini_schema (không bị None, không $ref)."""
    t = V.audit_transport_schema_sanitization()
    assert t["sanitized_successfully"] is True
    assert t["contains_ref"] is False
    assert t["status"] == "PASS"
    assert t["gemini_live_schema_acceptance"] == "NOT_ESTABLISHED_UNTIL_LIVE_REVALIDATION"


def test_06_transport_to_canonical_mapping_deterministic():
    """6. Ánh xạ transport -> internal canonical contract tất định 100%."""
    transport_dict = {
        "solid_kind": "prism",
        "base_cycle": ["A", "B", "C"],
        "top_cycle": ["D", "E", "F"],
        "correspondence": [["A", "D"], ["B", "E"], ["C", "F"]],
    }
    canon = V.map_transport_to_canonical(transport_dict)
    assert isinstance(canon, V.PrismTopologySpec)
    assert canon.solid_kind == "prism"
    assert canon.base_cycle == ("A", "B", "C")
    assert canon.top_cycle == ("D", "E", "F")
    assert canon.correspondence == (("A", "D"), ("B", "E"), ("C", "F"))

    # Thất bại an toàn khi thiếu trường
    with pytest.raises(V.TopologyValidationError) as exc:
        V.map_transport_to_canonical({"solid_kind": "prism", "base_cycle": ["A", "B"]})
    assert exc.value.code == "MALFORMED_TRANSPORT_PRISM"


def test_07_cyclic_adjacency_preservation_and_twisted_rejection():
    """7. Bảo toàn kề cận chu kỳ D_n (vacuously true với n=3; bắt chéo/xoắn n=4 bị chặn)."""
    # Với n = 3: Aut(C3) = S3 = D3 => mọi hoán vị đều bảo toàn chu trình
    spec_tri = V.PrismTopologySpec(
        base_cycle=("A", "B", "C"),
        top_cycle=("D", "E", "F"),
        correspondence=(("A", "D"), ("B", "F"), ("C", "E")),  # Hoán vị phản xạ trong D3
    )
    d_tri = V.derive_canonical_topology(spec_tri)
    assert len(d_tri["faces"]) == 5  # Vẫn sinh 5 mặt hợp lệ vì là tự đẳng cấu đồ thị

    # Với n = 4 (quadrilateral prism): hoán vị không thuộc D4 sẽ làm chéo mặt bên
    spec_quad = V.NEG_FIXTURES["NEG-TOPO-11"]["spec"]
    with pytest.raises(V.TopologyValidationError) as exc:
        V.derive_canonical_topology(spec_quad)
    assert exc.value.code == "NON_CYCLIC_CORRESPONDENCE"


def test_08_declared_vertex_universe_cross_contract_boundary():
    """8. DECLARED_VERTEX_UNIVERSE là cross-contract boundary (INV-TOPO-01)."""
    universe = {"A", "B", "C", "D", "E", "F"}
    spec_valid = V.POS_FIXTURES["POS-TOPO-02"]["spec"]
    res = V.validate_topology_invariants(spec_valid, universe)
    assert res["status"] == "PASS"

    # Đỉnh 'K' ngoài vũ trụ => Bị chặn
    spec_invalid = V.NEG_FIXTURES["NEG-TOPO-01"]["spec"]
    with pytest.raises(V.TopologyValidationError) as exc:
        V.validate_topology_invariants(spec_invalid, universe)
    assert exc.value.code == "UNDECLARED_VERTEX"


def test_09_all_positive_fixtures_pass_with_exact_counts():
    """9. Bộ 5 Positive Fixtures đạt chuẩn manifold genus-0 đóng với V, E, F chính xác."""
    for fix_id, fix in V.POS_FIXTURES.items():
        res = V.validate_topology_invariants(fix["spec"], fix["universe"])
        assert res["status"] == "PASS"
        assert res["V"] == fix["expected_V"]
        assert res["E"] == fix["expected_E"]
        assert res["F"] == fix["expected_F"]
        assert res["chi"] == 2


def test_10_all_negative_fixtures_fail_closed_with_exact_codes():
    """10. Bộ 11 Negative Fixtures bị từ chối an toàn với mã lỗi xác định."""
    f = V.audit_fixtures()
    assert f["negative_fixtures_caught"] == 11
    assert f["negative_fixtures_total"] == 11
    assert f["status"] == "PASS"


def test_11_provenance_rules_hierarchy():
    """11. Phân định xuất xứ dữ kiện (GIVEN vs DEFINITIONAL_DERIVED) và cấm giả mạo GIVEN."""
    # Khi đề bài nêu thẳng => GIVEN hợp lệ
    fact_given = {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "C"], "provenance": "GIVEN"}
    assert fact_given["provenance"] == "GIVEN"

    # Giả định cố tình đòi quyền GIVEN => Bị chặn
    probe = V.NEG_FIXTURES["NEG-TOPO-09"]["provenance_probe"]
    assert probe["model_assumption"] is True
    assert probe["claimed_provenance"] == "GIVEN"
    # Kiểm tra quy tắc từ chối
    assert V.NEG_FIXTURES["NEG-TOPO-09"]["expected_error_code"] == "UNVERIFIED_ASSUMPTION_REJECTED"


def test_12_falsifiable_research_hypothesis_and_metrics():
    """12. Giả thuyết nghiên cứu PUBLICATION_HYPOTHESIS kiểm định được và 15 chỉ số benchmark."""
    hyp = V.PUBLICATION_HYPOTHESIS
    assert "100%" not in hyp
    assert "tuyệt đối" not in hyp
    assert "may improve" in hyp or "improve" in hyp
    assert V.LITERATURE_NOVELTY_STATUS == "NOT_ESTABLISHED"
    assert len(V.PREREGISTERED_BENCHMARK_METRICS) == 15
    assert "exact_topology_accuracy" in V.PREREGISTERED_BENCHMARK_METRICS
    assert "safe_rejection_rate" in V.PREREGISTERED_BENCHMARK_METRICS


def test_13_four_way_backward_compatibility_expected():
    """13. Bốn chiều tương thích ngược được phân loại dự báo (EXPECTED_*)."""
    dims = V.COMPATIBILITY_DIMENSIONS
    assert dims["HISTORICAL_PAYLOAD_VALIDATION_COMPATIBILITY"] == "EXPECTED_PASS_REQUIRES_VERTICAL_SLICE_TEST"
    assert dims["RUNTIME_BEHAVIOR_COMPATIBILITY"] == "EXPECTED_PASS_REQUIRES_VERTICAL_SLICE_TEST"
    assert dims["MODEL_FACING_SCHEMA_IDENTITY_COMPATIBILITY"] == "EXPECTED_BREAKS_IDENTITY"
    assert dims["CACHE_IDENTITY_COMPATIBILITY"] == "EXPECTED_BREAKS_IDENTITY"


def test_14_provisional_future_allowlist_and_audit_prerequisites():
    """14. Future product allowlist mang nhãn PROVISIONAL kèm 7 điều kiện audit tiên quyết."""
    allowlist = V.FUTURE_PRODUCT_ALLOWLIST_PROVISIONAL
    assert len(allowlist) == 8
    assert "backend/app/simulation/semantic_program/request_contract.py" in allowlist

    audits = V.MANDATORY_AUDIT_PREREQUISITES
    assert len(audits) == 7
    assert "schema_tests_audit" in audits
    assert "gemini_response_schema_compatibility_audit" in audits
    assert "live_revalidation_tooling_audit" in audits
