from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REGISTRY = (
    ROOT
    / "docs/evaluation/geometry/runs"
    / "20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair"
    / "inputs/human_expected_visibility.json"
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _load() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_frozen_expectations_register_exactly_six_approved_fixed_cameras():
    registry = _load()
    assert registry["schema_version"] == "human-expected-visibility/1"
    assert registry["registration_policy"] == {
        "identity": (
            "Canonical machine edge IDs use semantic endpoint entity IDs "
            "ordered by stable vertex ordinal."
        ),
        "display_labels_are_non_authoritative": True,
        "coordinate_fallback_allowed": False,
        "product_or_oracle_may_modify": False,
        "reviewed_status": "APPROVED_BY_USER",
    }
    scenarios = registry["scenarios"]
    assert {item["scenario_id"] for item in scenarios} == {
        "triangular_pyramid", "triangular_prism", "rectangular_pyramid",
        "cuboid", "cube", "cross_section",
    }
    assert all(item["viewport"] == "desktop" for item in scenarios)
    assert all(item["state"] == "neutral_final" for item in scenarios)
    assert all(item["reviewed_status"] == "APPROVED_BY_USER" for item in scenarios)
    assert all(SHA256.fullmatch(item["camera_snapshot_sha256"]) for item in scenarios)
    assert all(SHA256.fullmatch(item["scene3d_envelope_sha256"]) for item in scenarios)


def test_frozen_machine_ids_are_disjoint_stable_and_not_display_labels():
    registry = _load()
    assert registry["display_labels"]["A_prime"] == "A′"
    for scenario in registry["scenarios"]:
        visible = set(scenario["expected_visible_ids"])
        hidden = set(scenario["expected_hidden_ids"])
        mixed = set(scenario["expected_mixed_ids"])
        assert visible
        assert hidden
        assert not mixed
        assert not (visible & hidden or visible & mixed or hidden & mixed)
        machine_ids = visible | hidden | mixed
        assert all("::edge:" in edge_id for edge_id in machine_ids)
        assert all("′" not in edge_id for edge_id in machine_ids)
        assert all("anonymous" not in edge_id.lower() for edge_id in machine_ids)
        assert scenario["reasoning"]["far_vertex"]
        assert scenario["reasoning"]["occluding_surface_ids"]


def test_cuboid_family_uses_canonical_prime_entity_ids():
    scenarios = {item["scenario_id"]: item for item in _load()["scenarios"]}
    for scenario_id in ("cuboid", "cube"):
        machine_ids = (
            scenarios[scenario_id]["expected_visible_ids"]
            + scenarios[scenario_id]["expected_hidden_ids"]
        )
        assert "khoi_hop::edge:A-A_prime" in machine_ids
        assert "khoi_hop::edge:A_prime-B_prime" in machine_ids
