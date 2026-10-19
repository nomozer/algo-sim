# -*- coding: utf-8 -*-
"""Unit and integration tests for Hybrid Architecture Wave 1:
- Exact Gram-metric altitude certificates on segment3 objects (_gan_nhan_chung_duong_cao_chinh_xac).
- Preservation of witness annotations in _bam_doan_da_dung.
- Canonical topological call phase ordering in planner (lap_ke_hoach).
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from app.ai.function_route import _gan_nhan_chung_duong_cao_chinh_xac, run_function_route
from app.simulation.geometry_functions.planner import _thu_tu_pha_loi_goi, lap_ke_hoach
from app.simulation.semantic_program.quantity_annotations import _bam_doan_da_dung


from app.simulation.geometry.exact import Vec3


def test_thu_tu_pha_loi_goi():
    """Kiểm tra thứ tự 4 pha: khối đa diện (1) < giả thiết (2) < dựng phụ (3) < câu hỏi (4)."""
    assert _thu_tu_pha_loi_goi("prism") == 1
    assert _thu_tu_pha_loi_goi("pyramid") == 1
    assert _thu_tu_pha_loi_goi("regular_pyramid") == 1
    assert _thu_tu_pha_loi_goi("segment_length") == 2
    assert _thu_tu_pha_loi_goi("right_angle") == 2
    assert _thu_tu_pha_loi_goi("midpoint") == 3
    assert _thu_tu_pha_loi_goi("orthogonal_projection") == 3
    assert _thu_tu_pha_loi_goi("ask_distance_line_line") == 4
    assert _thu_tu_pha_loi_goi("ask_angle_line_plane") == 4


def test_bam_doan_da_dung_preserves_witness():
    """Kiểm tra _bam_doan_da_dung bảo toàn trường witness của khoảng cách trùng đoạn đã dựng."""
    w = {
        "from": "A",
        "foot": ["1", "0", "0"],
        "on": "canh_day_A_B",
        "marker": {"u": ["1", "0", "0"], "v": ["0", "1", "0"]},
    }
    kq = {"witness": w, "unit": "a"}
    loai = {"A": "point3", "B": "point3"}
    mem = {"A": Vec3.of(0, 0, 0), "B": Vec3.of(1, 0, 0)}
    doan = {frozenset(("A", "B"))}

    # Case where segment already exists:
    annot = _bam_doan_da_dung(kq, loai, mem, doan)
    assert annot["anchor"] == "segment"
    assert annot["subject_ids"] == ["A", "B"]
    assert annot.get("witness") == w


def test_gan_nhan_chung_duong_cao_chinh_xac_cube():
    """Kiểm tra hình lập phương gắn chứng chỉ vuông góc cho đúng 4 cạnh bên đứng."""
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
        assert witness["certificate"] == "exact-gram-line-plane-orthogonality/1"
        assert witness["on"] == "day_ABCD"
    assert "perpendicular_witness" not in seg_by_id["AB"]


def test_gan_nhan_chung_duong_cao_chinh_xac_rejects_oblique():
    """Kiểm tra chóp đáy vuông với cạnh bên xiên bị từ chối chứng chỉ vuông góc."""
    canh = {
        "objects": [
            {"id": "A", "type": "point3", "xyz": [0, 0, 0]},
            {"id": "B", "type": "point3", "xyz": [1, 0, 0]},
            {"id": "C", "type": "point3", "xyz": [1, 1, 0]},
            {"id": "D", "type": "point3", "xyz": [0, 1, 0]},
            # S nằm trên đường thẳng đứng qua tâm đáy (0.5, 0.5, 1)
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
    # SA, SB là cạnh xiên -> KHÔNG được mang chứng chỉ
    assert "perpendicular_witness" not in seg_by_id["SA"]
    assert "perpendicular_witness" not in seg_by_id["SB"]
    # SO là đường cao vuông góc -> PHẢI mang chứng chỉ
    assert "perpendicular_witness" in seg_by_id["SO"]
    witness = seg_by_id["SO"]["perpendicular_witness"]
    assert witness["certificate"] == "exact-gram-line-plane-orthogonality/1"
    assert witness["foot"] == ["1/2", "1/2", "0"]
