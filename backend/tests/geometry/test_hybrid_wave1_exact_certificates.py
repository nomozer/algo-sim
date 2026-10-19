# -*- coding: utf-8 -*-
"""Unit and integration tests for Hybrid Architecture Wave 1A:
Exact Geometry Certificates (`ISSUE-ARCH-SCENE3D-ALTITUDE-CERTIFICATE-MISSING`).

Covers:
1. Positive certificates:
   - SA perpendicular to pyramid base (GIVEN / ENGINE_VERIFIED)
   - Regular pyramid altitude SO and quantity annotation coinciding with SO (_bam_doan_da_dung)
   - Right prism / cube / cuboid vertical edges (AA', BB', CC', DD')
   - SH perpendicular to (ABC) when justified by orthogonal_projection / face_perpendicular_base + midpoint
   - BC ⊥ (SAB) deductive certificate under valid premises in H07 (PROVEN vs DERIVED)
2. Epistemic status distinction:
   - GIVEN, ENGINE_VERIFIED, DERIVED, UNVERIFIABLE, PROVEN
3. Negative & tamper tests (8 vectors):
   - Oblique lateral edges in pyramid/prism rejected
   - Degenerate line/plane directions rejected fail-closed
   - Non-SPD Gram metric rejected fail-closed
   - Fake or tampered witness rejected fail-closed
   - Mismatched operands rejected fail-closed
   - Wrong construction step rejected fail-closed
   - Unsupported assumptions rejected fail-closed
   - Missing provenance / layout-only coordinate coincidence rejected (UNVERIFIABLE, no witness emitted)
"""
from __future__ import annotations

import copy
from fractions import Fraction

import pytest

from app.ai.function_route import _gan_nhan_chung_duong_cao_chinh_xac, run_fact_route, run_function_route
from app.simulation.geometry.exact import Vec3
from app.simulation.geometry_functions.certificates import (
    CERTIFICATE_SCHEMA,
    CertificateError,
    certify_deductive_line_plane_perpendicularity,
    certify_line_plane_perpendicularity,
    validate_gram_metric_spd,
    verify_perpendicular_witness,
)
from app.simulation.semantic_program.quantity_annotations import _bam_doan_da_dung


def test_bam_doan_da_dung_preserves_witness():
    """Kiểm tra _bam_doan_da_dung bảo toàn trường witness của khoảng cách trùng đoạn đã dựng."""
    w = {
        "from": "S",
        "foot": ["1/2", "1/2", "0"],
        "on": "day_ABCD",
        "marker": {"u": ["1", "0", "0"], "v": ["0", "0", "1"]},
    }
    kq = {"witness": w, "unit": "a"}
    loai = {"S": "point3", "O": "point3"}
    mem = {"S": Vec3.of(Fraction(1, 2), Fraction(1, 2), 1), "O": Vec3.of(Fraction(1, 2), Fraction(1, 2), 0)}
    doan = {frozenset(("S", "O"))}

    annot = _bam_doan_da_dung(kq, loai, mem, doan)
    assert annot["anchor"] == "segment"
    assert annot["subject_ids"] == ["S", "O"]
    assert annot.get("witness") == w


def test_positive_sa_perpendicular_to_pyramid_base():
    """Positive 1: SA ⊥ (ABC) trên hình chóp có cạnh bên SA vuông góc đáy."""
    text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, "
        "AB = 3, BC = 4. Cạnh bên SA vuông góc với mặt phẳng (ABC) và SA = 5. "
        "Tính thể tích khối chóp S.ABC."
    )
    facts = {
        "facts": [
            {"id": "f1", "kind": "solid", "role": "premise", "solid": "S.ABC", "solid_type": "pyramid",
             "quotes": ["Cho hình chóp S.ABC"]},
            {"id": "f2", "kind": "right_angle", "role": "premise", "at": "B", "points": ["A", "C"],
             "quotes": ["đáy ABC là tam giác vuông tại B"]},
            {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "3",
             "quotes": ["AB = 3"]},
            {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["B", "C"], "value": "4",
             "quotes": ["BC = 4"]},
            {"id": "f5", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": ["A", "B", "C"],
             "quotes": ["Cạnh bên SA vuông góc với mặt phẳng (ABC)"]},
            {"id": "f6", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "5",
             "quotes": ["SA = 5"]},
            {"id": "f7", "kind": "question", "role": "question", "quantity": "volume", "solid": "S.ABC",
             "quotes": ["Tính thể tích khối chóp S.ABC"]},
        ]
    }
    r = run_fact_route(text, facts)
    assert r.status == "SERVED"
    segs = {o["id"]: o for o in r.scene3d["objects"] if o["type"] == "segment3"}
    assert "perpendicular_witness" in segs["canh_ben_S_A"]
    w = segs["canh_ben_S_A"]["perpendicular_witness"]
    assert w["certificate"] == CERTIFICATE_SCHEMA
    assert w["from"] == "S"
    assert w["on"] == "day_ABC"
    assert w["status"] in ("GIVEN", "ENGINE_VERIFIED")
    assert len(w["plane_directions"]) == 2
    ok, code = verify_perpendicular_witness(w, r.scene3d, r.chart_metric, segment_obj=segs["canh_ben_S_A"])
    assert ok is True, code
    # Oblique lateral edges SB, SC must NOT receive perpendicular certificates
    assert "perpendicular_witness" not in segs["canh_ben_S_B"]
    assert "perpendicular_witness" not in segs["canh_ben_S_C"]


def test_positive_cube_and_right_prism_vertical_edges():
    """Positive 2: Hình lập phương / lăng trụ đứng gắn chứng chỉ vuông góc cho đúng các cạnh bên đứng."""
    canh = {
        "objects": [
            {"id": "A", "type": "point3", "xyz": [0, 0, 0]},
            {"id": "B", "type": "point3", "xyz": [1, 0, 0]},
            {"id": "C", "type": "point3", "xyz": [1, 1, 0]},
            {"id": "D", "type": "point3", "xyz": [0, 1, 0]},
            {"id": "A_prime", "type": "point3", "xyz": [0, 0, 1]},
            {"id": "B_prime", "type": "point3", "xyz": [1, 0, 1]},
            {"id": "C_prime", "type": "point3", "xyz": [1, 1, 1]},
            {"id": "D_prime", "type": "point3", "xyz": [0, 1, 1]},
            {
                "id": "day_ABCD",
                "type": "polygon3",
                "vertex_ids": ["A", "B", "C", "D"],
                "formation_roles": ["CONSTRUCT_BASE"],
            },
            {"id": "AA_p", "type": "segment3", "endpoint_ids": ["A", "A_prime"]},
            {"id": "BB_p", "type": "segment3", "endpoint_ids": ["B", "B_prime"]},
            {"id": "CC_p", "type": "segment3", "endpoint_ids": ["C", "C_prime"]},
            {"id": "DD_p", "type": "segment3", "endpoint_ids": ["D", "D_prime"]},
            {"id": "AB", "type": "segment3", "endpoint_ids": ["A", "B"]},
        ]
    }
    _gan_nhan_chung_duong_cao_chinh_xac(canh)
    seg_by_id = {o["id"]: o for o in canh["objects"] if o["type"] == "segment3"}
    for side_id in ["AA_p", "BB_p", "CC_p", "DD_p"]:
        assert "perpendicular_witness" in seg_by_id[side_id]
        witness = seg_by_id[side_id]["perpendicular_witness"]
        assert witness["certificate"] == CERTIFICATE_SCHEMA
        assert witness["on"] == "day_ABCD"
        assert len(witness["plane_directions"]) == 2
        ok, code = verify_perpendicular_witness(witness, canh, segment_obj=seg_by_id[side_id])
        assert ok is True, code
    assert "perpendicular_witness" not in seg_by_id["AB"]


def test_positive_regular_pyramid_altitude_and_oblique_rejection():
    """Positive 3 & Negative 1: Chóp đều gắn chứng chỉ cho đường cao SO và từ chối cạnh bên xiên SA, SB, SC, SD."""
    canh = {
        "objects": [
            {"id": "A", "type": "point3", "xyz": [0, 0, 0]},
            {"id": "B", "type": "point3", "xyz": [1, 0, 0]},
            {"id": "C", "type": "point3", "xyz": [1, 1, 0]},
            {"id": "D", "type": "point3", "xyz": [0, 1, 0]},
            {"id": "S", "type": "point3", "xyz": ["1/2", "1/2", 1]},
            {"id": "O", "type": "point3", "xyz": ["1/2", "1/2", 0]},
            {
                "id": "day_ABCD",
                "type": "polygon3",
                "vertex_ids": ["A", "B", "C", "D"],
                "formation_roles": ["CONSTRUCT_BASE"],
            },
            {"id": "SA", "type": "segment3", "endpoint_ids": ["S", "A"]},
            {"id": "SB", "type": "segment3", "endpoint_ids": ["S", "B"]},
            {"id": "SO", "type": "segment3", "endpoint_ids": ["S", "O"]},
        ]
    }
    _gan_nhan_chung_duong_cao_chinh_xac(canh)
    seg_by_id = {o["id"]: o for o in canh["objects"] if o["type"] == "segment3"}
    assert "perpendicular_witness" not in seg_by_id["SA"]
    assert "perpendicular_witness" not in seg_by_id["SB"]
    assert "perpendicular_witness" in seg_by_id["SO"]
    witness = seg_by_id["SO"]["perpendicular_witness"]
    assert witness["certificate"] == CERTIFICATE_SCHEMA
    assert witness["foot"] == ["1/2", "1/2", "0"]


def test_positive_sh_perpendicular_via_face_perpendicular_base():
    """Positive 4: SH ⊥ (ABC) khi (SAB) ⊥ (ABC), tam giác SAB cân tại S, H là trung điểm AB."""
    text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2. "
        "Mặt bên (SAB) vuông góc với mặt phẳng đáy, SA = 3, SB = 3. "
        "Gọi H là trung điểm của AB. Tính thể tích khối chóp S.ABC."
    )
    facts = {
        "facts": [
            {"id": "f1", "kind": "solid", "role": "premise", "solid": "S.ABC", "solid_type": "pyramid",
             "quotes": ["Cho hình chóp S.ABC"]},
            {"id": "f2", "kind": "polygon_shape", "role": "premise", "points": ["A", "B", "C"],
             "shape": "equilateral_triangle", "quotes": ["đáy ABC là tam giác đều"]},
            {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "2",
             "quotes": ["cạnh 2"]},
            {"id": "f4", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A", "B"],
             "points_b": ["A", "B", "C"], "quotes": ["Mặt bên (SAB) vuông góc với mặt phẳng đáy"]},
            {"id": "f5", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "3",
             "quotes": ["SA = 3"]},
            {"id": "f6", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "B"], "value": "3",
             "quotes": ["SB = 3"]},
            {"id": "f7", "kind": "point_def", "role": "premise", "point": "H", "point_kind": "midpoint",
             "points": ["A", "B"], "quotes": ["Gọi H là trung điểm của AB"]},
            {"id": "f8", "kind": "question", "role": "question", "quantity": "volume", "solid": "S.ABC",
             "quotes": ["Tính thể tích khối chóp S.ABC"]},
        ]
    }
    r = run_fact_route(text, facts)
    assert r.status == "SERVED"
    # Verify SH perpendicularity directly via certify_line_plane_perpendicularity
    pts = {o["id"]: [Fraction(str(x)) for x in o["xyz"]] for o in r.scene3d["objects"] if o["type"] == "point3"}
    cert = certify_line_plane_perpendicularity(
        from_id="S",
        foot_id="H",
        plane_id="day_ABC",
        plane_vertex_ids=["A", "B", "C"],
        points_by_id=pts,
        chart_metric=r.chart_metric,
        provenance_status="DERIVED",
        rule="face_perpendicular_base_midpoint_altitude",
        supporting_calls=["f4", "f5", "f6", "f7"],
    )
    assert cert["status"] == "DERIVED"
    assert cert["certificate"] == CERTIFICATE_SCHEMA
    assert cert["foot"] == ["1/2", "0", "0"]


def test_positive_h07_bc_perpendicular_sab_deductive_certificate():
    """Positive 5: H07 — BC ⊥ (SAB) được chứng nhận suy diễn (PROVEN) từ góc vuông tại B (BC ⊥ AB) và SA ⊥ (ABC) (BC ⊥ SA)."""
    pts = {
        "A": [Fraction(0), Fraction(0), Fraction(0)],
        "B": [Fraction(1), Fraction(0), Fraction(0)],
        "C": [Fraction(0), Fraction(1), Fraction(0)],
        "S": [Fraction(0), Fraction(0), Fraction(1)],
    }
    # In ΔABC right at B with AB=1, BC=1 => AC^2 = 2 => Gram_2D has g00=1, g11=2, g01=1
    chart_metric = [[Fraction(1), Fraction(1), Fraction(0)],
                    [Fraction(1), Fraction(2), Fraction(0)],
                    [Fraction(0), Fraction(0), Fraction(3)]]
    calls = [
        {"id": "f1", "fn": "right_angle", "args": {"vertex": "B", "rays": ["A", "C"]}},
        {"id": "f4", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]}},
    ]
    goal_call = {
        "id": "f7",
        "fn": "perpendicular_line_plane",
        "args": {"line": ["B", "C"], "plane": ["S", "A", "B"]},
        "role": "prove",
    }
    cert = certify_deductive_line_plane_perpendicularity(
        goal_call=goal_call,
        calls=calls,
        points_by_id=pts,
        chart_metric=chart_metric,
        supporting_step_index=2,
        conclusion_step_index=4,
    )
    assert cert["status"] == "PROVEN"
    assert cert["can_present_as_proven"] is True
    assert cert["from"] == "C"
    assert cert["foot_id"] == "B"
    assert cert["foot"] == ["1", "0", "0"]
    assert cert["supporting_calls"] == ["f1", "f4"]
    assert cert["supporting_step_index"] == 2
    assert cert["conclusion_step_index"] == 4
    assert len(cert["plane_directions"]) == 2


def test_negative_degenerate_directions_and_non_spd_metric():
    """Negative 2 & 3: Hướng đường/mặt suy biến và metric không SPD phải fail closed."""
    pts = {
        "A": [Fraction(0), Fraction(0), Fraction(0)],
        "B": [Fraction(1), Fraction(0), Fraction(0)],
        "C": [Fraction(2), Fraction(0), Fraction(0)],  # Collinear with A, B!
        "S": [Fraction(0), Fraction(0), Fraction(1)],
    }
    # 1. Degenerate line direction (from_id == foot_id)
    with pytest.raises(CertificateError) as exc_line:
        certify_line_plane_perpendicularity(
            from_id="A",
            foot_id="A",
            plane_id="day_ABC",
            plane_vertex_ids=["A", "B", "S"],
            points_by_id=pts,
            chart_metric=None,
            provenance_status="GIVEN",
            rule="perpendicular_line_plane",
        )
    assert exc_line.value.code == "DEGENERATE_LINE_DIRECTION"

    # 2. Degenerate plane directions (A, B, C collinear)
    with pytest.raises(CertificateError) as exc_plane:
        certify_line_plane_perpendicularity(
            from_id="S",
            foot_id="A",
            plane_id="day_ABC",
            plane_vertex_ids=["A", "B", "C"],
            points_by_id=pts,
            chart_metric=None,
            provenance_status="GIVEN",
            rule="perpendicular_line_plane",
        )
    assert exc_plane.value.code == "DEGENERATE_PLANE_DIRECTIONS"

    # 3. Non-SPD metric (negative determinant / non-positive principal minor / asymmetric)
    for bad_metric in (
        [[0, 0, 0], [0, 1, 0], [0, 0, 1]],
        [[1, 2, 0], [2, 1, 0], [0, 0, 1]],  # det_2 = 1 - 4 = -3 < 0
        [[1, 0, 0], [0, 1, 0], [0, 0, -1]],  # det_3 < 0
        [[1, 1, 0], [0, 1, 0], [0, 0, 1]],  # asymmetric
    ):
        with pytest.raises(CertificateError) as exc_spd:
            validate_gram_metric_spd(bad_metric)
        assert exc_spd.value.code == "NON_SPD_METRIC"


def test_negative_tampered_witness_and_mismatched_operands():
    """Negative 4, 5, 6, 7, 8: Kiểm tra từ chối chứng chỉ giả mạo, sai toán hạng, sai bước dựng, giả thiết không hỗ trợ, thiếu xuất xứ."""
    canh = {
        "objects": [
            {"id": "A", "type": "point3", "xyz": ["0", "0", "0"]},
            {"id": "B", "type": "point3", "xyz": ["1", "0", "0"]},
            {"id": "C", "type": "point3", "xyz": ["0", "1", "0"]},
            {"id": "S", "type": "point3", "xyz": ["0", "0", "1"]},
            {"id": "day_ABC", "type": "polygon3", "vertex_ids": ["A", "B", "C"], "formation_roles": ["CONSTRUCT_BASE"]},
            {"id": "SA", "type": "segment3", "endpoint_ids": ["S", "A"]},
            {"id": "SB", "type": "segment3", "endpoint_ids": ["S", "B"]},
        ]
    }
    _gan_nhan_chung_duong_cao_chinh_xac(canh)
    sa = next(o for o in canh["objects"] if o["id"] == "SA")
    valid_w = copy.deepcopy(sa["perpendicular_witness"])
    assert verify_perpendicular_witness(valid_w, canh, segment_obj=sa) == (True, "OK")

    # 4a. Tampered foot coordinates
    bad_foot = copy.deepcopy(valid_w)
    bad_foot["foot"] = ["1", "0", "0"]
    ok, code = verify_perpendicular_witness(bad_foot, canh, segment_obj=sa)
    assert ok is False and code == "TAMPERED_WITNESS_FOOT"

    # 4b. Tampered non-orthogonal marker vector u
    bad_marker = copy.deepcopy(valid_w)
    bad_marker["marker"]["u"] = ["1", "0", "1"]  # dot with v=(0,0,1) is 1 != 0
    ok, code = verify_perpendicular_witness(bad_marker, canh, segment_obj=sa)
    assert ok is False and code == "TAMPERED_WITNESS_MARKER"

    # 5. Mismatched operands (witness attached to oblique segment SB or referencing unknown plane)
    sb = next(o for o in canh["objects"] if o["id"] == "SB")
    ok, code = verify_perpendicular_witness(valid_w, canh, segment_obj=sb)
    assert ok is False and code in ("MISMATCHED_OPERANDS", "TAMPERED_WITNESS_FOOT")

    bad_on = copy.deepcopy(valid_w)
    bad_on["on"] = "nonexistent_plane"
    ok, code = verify_perpendicular_witness(bad_on, canh, segment_obj=sa)
    assert ok is False and code == "MISMATCHED_OPERANDS"

    # 6. Wrong construction step (supporting_step_index >= conclusion_step_index)
    bad_step = copy.deepcopy(valid_w)
    bad_step["supporting_step_index"] = 5
    bad_step["conclusion_step_index"] = 3
    ok, code = verify_perpendicular_witness(bad_step, canh, segment_obj=sa)
    assert ok is False and code == "WRONG_CONSTRUCTION_STEP"

    # 7. Unsupported assumption
    bad_assumed = copy.deepcopy(valid_w)
    bad_assumed["rule"] = "unsupported_heuristic_guess"
    ok, code = verify_perpendicular_witness(bad_assumed, canh, segment_obj=sa)
    assert ok is False and code == "UNSUPPORTED_ASSUMPTION"

    # 8. Missing provenance / layout-derived only (UNVERIFIABLE)
    bad_prov = copy.deepcopy(valid_w)
    bad_prov["status"] = "UNVERIFIABLE"
    ok, code = verify_perpendicular_witness(bad_prov, canh, segment_obj=sa)
    assert ok is False and code == "MISSING_PROVENANCE"


def test_negative_layout_derived_without_premise_is_unverifiable():
    """Negative 8 (Coordinate-only inference forbidden):
    Một đoạn có toạ độ tình cờ vuông góc do bố cục (LAYOUT_DERIVED) nhưng không có tiền đề/phép dựng
    chứng minh vuông góc phải bị phân loại UNVERIFIABLE và KHÔNG được gắn perpendicular_witness."""
    pts = {
        "A": [Fraction(0), Fraction(0), Fraction(0)],
        "B": [Fraction(1), Fraction(0), Fraction(0)],
        "C": [Fraction(0), Fraction(1), Fraction(0)],
        "S": [Fraction(0), Fraction(0), Fraction(1)],
    }
    with pytest.raises(CertificateError) as exc_layout:
        certify_line_plane_perpendicularity(
            from_id="S",
            foot_id="A",
            plane_id="day_ABC",
            plane_vertex_ids=["A", "B", "C"],
            points_by_id=pts,
            chart_metric=None,
            provenance_status="LAYOUT_DERIVED",
            rule="layout_sample_only",
        )
    assert exc_layout.value.code == "MISSING_PROVENANCE"

    # Scene where segment SA is explicitly marked layout-only without premise justification
    canh_layout = {
        "objects": [
            {"id": "A", "type": "point3", "xyz": ["0", "0", "0"]},
            {"id": "B", "type": "point3", "xyz": ["1", "0", "0"]},
            {"id": "C", "type": "point3", "xyz": ["0", "1", "0"]},
            {"id": "S", "type": "point3", "xyz": ["0", "0", "1"], "source": {"provenance": "LAYOUT_DERIVED", "unjustified_layout": True}},
            {"id": "day_ABC", "type": "polygon3", "vertex_ids": ["A", "B", "C"], "formation_roles": ["CONSTRUCT_BASE"]},
            {"id": "SA", "type": "segment3", "endpoint_ids": ["S", "A"], "source": {"provenance": "LAYOUT_DERIVED", "unjustified_layout": True}},
        ]
    }
    _gan_nhan_chung_duong_cao_chinh_xac(canh_layout)
    sa = next(o for o in canh_layout["objects"] if o["id"] == "SA")
    assert "perpendicular_witness" not in sa
