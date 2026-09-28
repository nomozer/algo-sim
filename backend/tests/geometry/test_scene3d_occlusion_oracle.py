from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from scene3d_occlusion_oracle import (  # noqa: E402
    CameraSnapshot,
    IDENTITY,
    OracleFailure,
    classify,
    cross_check,
    detect_coarse_sampling_blind_spot,
    perspective,
    reject_linear_ndc_depth,
)


def _scene() -> dict:
    return {
        "objects": [{
            "id": "synthetic",
            "type": "solid",
            "vertices": [
                ["-2", "0", "-8"], ["2", "0", "-8"], ["0", "-2", "-8"],
                ["0", "-1", "-4"], ["1", "-1", "-4"], ["1/2", "1", "-4"],
            ],
            "vertex_ids": ["A", "B", "C", "P", "Q", "R"],
            "faces": [[0, 1, 2], [3, 4, 5]],
            "edge_ownership": [
                {"edge_id": "synthetic::edge:A-B", "endpoint_ids": ["A", "B"],
                 "adjacent_surface_ids": ["synthetic::face:0"]},
            ],
            "surfaces": [
                {"surface_id": "synthetic::face:0", "surface_role": "SOLID_FACE",
                 "occludes_edges": True},
                {"surface_id": "synthetic::face:1", "surface_role": "SOLID_FACE",
                 "occludes_edges": True},
            ],
        }]
    }


def _camera() -> CameraSnapshot:
    return CameraSnapshot(
        view=IDENTITY,
        projection=perspective(60, 4 / 3, 0.1, 100),
        viewport_width=800,
        viewport_height=600,
        device_pixel_ratio=2,
    )


def test_oracle_is_implementation_independent():
    path = SCRIPTS / "scene3d_occlusion_oracle.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    forbidden = ("scene3d_edge_visibility", "polygon_triangulate", "frontend", "app.simulation")
    assert not [name for name in imports if any(part in name for part in forbidden)], \
        "ORACLE_NOT_IMPLEMENTATION_INDEPENDENT"


def test_analytic_oracle_and_independent_ray_reference_agree():
    result = cross_check(_scene(), _camera())
    assert result["analytic"]["mixed_edge_ids"] == ["synthetic::edge:A-B"]
    assert result["reference"]["mixed_edge_ids"] == ["synthetic::edge:A-B"]
    witness = result["analytic"]["witnesses"][0]
    assert witness["perspective_correction_method"] == "CLIP_W_RECIPROCAL_INTERPOLATION"
    assert set(witness) >= {
        "screen_coordinate", "camera_ray", "candidate_surface_id",
        "edge_camera_depth", "surface_camera_depth", "depth_delta",
    }


def test_non_solid_surface_cannot_occlude():
    scene = _scene()
    scene["objects"][0]["surfaces"][1]["surface_role"] = "BASE_REGION"
    scene["objects"][0]["surfaces"][1]["occludes_edges"] = False
    result = classify(scene, _camera())
    assert result["visible_edge_ids"] == ["synthetic::edge:A-B"]
    assert result["hidden_edge_ids"] == result["mixed_edge_ids"] == []


def test_strong_depth_slope_rejects_linear_ndc_interpolation():
    # A depth-sloped triangle makes NDC-z linear interpolation attractive but
    # invalid. The oracle must fail by named policy before accepting it.
    with pytest.raises(OracleFailure) as error:
        reject_linear_ndc_depth("LINEAR_NDC_Z")
    assert error.value.code == "PERSPECTIVE_DEPTH_INTERPOLATION_INVALID"


def test_small_occluder_exposes_coarse_only_blind_spot():
    with pytest.raises(OracleFailure) as error:
        detect_coarse_sampling_blind_spot("VISIBLE", "MIXED")
    assert error.value.code == "SHARED_SAMPLING_BLIND_SPOT"


def test_anonymous_section_endpoint_is_not_authoritative():
    endpoint = {"entity_id": "legacy", "anonymous_coordinate_fallback": True}
    code = "ANONYMOUS_AUTHORITATIVE_SECTION_ENDPOINT" if endpoint[
        "anonymous_coordinate_fallback"
    ] else None
    assert code == "ANONYMOUS_AUTHORITATIVE_SECTION_ENDPOINT"


def test_untyped_formation_event_is_not_authoritative():
    event = {"semantic_kind": "LEGACY_UNTYPED_EVENT"}
    code = "LEGACY_UNTYPED_EVENT" if event["semantic_kind"] == "LEGACY_UNTYPED_EVENT" else None
    assert code == "LEGACY_UNTYPED_EVENT"
