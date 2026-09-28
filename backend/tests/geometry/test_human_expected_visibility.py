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


# ── Camera identity (w09): the registry binds each review to a RAW snapshot
#    hash; OrbitControls damping rewrites the pose in its last ULPs, so the
#    reviewed camera is compared canonically through a verified preimage.
import copy  # noqa: E402
import hashlib  # noqa: E402
import sys  # noqa: E402

import pytest  # noqa: E402

sys.path.insert(0, str(ROOT / "backend" / "scripts"))
import measure_scene3d_occlusion as M  # noqa: E402

PRIOR_RUN = REGISTRY.parents[1]
PREIMAGES = (ROOT / "docs/evaluation/geometry/runs/20260928-w09-verify-cleanup"
             / "inputs/REGISTERED_CAMERA_PREIMAGES.json")
#: sha256 prefix of the registry as committed at 80766b90 — byte identity.
REGISTRY_SHA256 = "8fead2e6dbab3e66"


def _scene(scenario_id: str) -> dict:
    fixture = PRIOR_RUN / "inputs" / "fixtures" / f"{scenario_id}_positive.json"
    return json.loads(fixture.read_text(encoding="utf-8"))["envelope"]["scene3d"]


def _prior_snapshot(scenario_id: str) -> dict:
    evidence = json.loads((PRIOR_RUN / "results" / "BROWSER_EVIDENCE.json").read_text(encoding="utf-8"))
    return evidence["scenarios"][scenario_id]["positive"]["desktop"]["camera_snapshots"]["neutral_final"]


def _registered(scenario_id: str) -> dict:
    return next(item for item in _load()["scenarios"] if item["scenario_id"] == scenario_id)


def _record(snapshot: dict) -> dict:
    return {"snapshot": snapshot,
            "sha256": hashlib.sha256(json.dumps(snapshot).encode()).hexdigest()}


def test_registry_is_byte_identical_to_its_registration():
    # Blob content: a core.autocrlf checkout (fresh worktree) writes CRLF.
    blob = REGISTRY.read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(blob).hexdigest().startswith(REGISTRY_SHA256)


def test_preimages_verify_on_a_crlf_checkout(tmp_path):
    crlf = tmp_path / "human_expected_visibility.json"
    crlf.write_bytes(REGISTRY.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert len(M.load_camera_preimages(PREIMAGES, crlf)) == 6


@pytest.mark.parametrize("scenario_id", ["triangular_prism", "cube"])
def test_frozen_camera_matches_canonically_through_verified_preimage(scenario_id):
    preimages = M.load_camera_preimages(PREIMAGES, REGISTRY)
    frozen = _registered(scenario_id)
    actual = _prior_snapshot(scenario_id)
    assert actual["sha256"] != frozen["camera_snapshot_sha256"], "the historical mismatch is real"
    verdict = M.camera_identity(frozen["camera_snapshot_sha256"], actual, _scene(scenario_id), preimages)
    assert verdict["status"] == "CANONICAL_EQUIVALENT", verdict
    assert verdict["max_projected_delta_px"] < 1e-6


def test_all_six_registered_cameras_have_verified_preimages():
    preimages = M.load_camera_preimages(PREIMAGES, REGISTRY)
    assert {item["camera_snapshot_sha256"] for item in _load()["scenarios"]} == set(preimages)


def test_tampered_preimage_is_rejected(tmp_path):
    data = json.loads(PREIMAGES.read_text(encoding="utf-8"))
    data["preimages"][1]["snapshot_json"] = data["preimages"][1]["snapshot_json"].replace("5", "6", 1)
    bad = tmp_path / "preimages.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="PREIMAGE_HASH_MISMATCH"):
        M.load_camera_preimages(bad, REGISTRY)


def test_canonical_identity_absorbs_float_noise_but_not_real_changes():
    base = _prior_snapshot("cube")["snapshot"]
    scene = _scene("cube")
    preimages = {"reg": base}
    view = base["view_matrix_column_major"]
    proj = base["projection_matrix_column_major"]

    def changed(**fields) -> dict:
        return {**copy.deepcopy(base), **fields}

    def verdict(snapshot):
        return M.camera_identity("reg", _record(snapshot), scene, preimages)

    noise = changed(view_matrix_column_major=[v + 3e-15 for v in view],
                    position=[p - 2e-15 for p in base["position"]])
    assert M.canonical_camera_sha256(noise) == M.canonical_camera_sha256(base)
    assert verdict(noise)["status"] == "CANONICAL_EQUIVALENT"

    translated = changed(view_matrix_column_major=view[:12] + [view[12] + 0.05] + view[13:])
    rotated = changed(view_matrix_column_major=[view[0] + 0.02, view[1], view[2] - 0.02, *view[3:]])
    wider = changed(projection_matrix_column_major=[proj[0] * 1.01, *proj[1:]])
    resized = changed(viewport_width=base["viewport_width"] + 1)
    retina = changed(device_pixel_ratio=2)
    for other in (translated, rotated, wider, resized, retina):
        assert M.canonical_camera_sha256(other) != M.canonical_camera_sha256(base)
        assert verdict(other)["status"] == "FROZEN_CAMERA_IDENTITY_MISMATCH"
    assert verdict(translated)["max_projected_delta_px"] > 0.5
    assert verdict(wider)["max_projected_delta_px"] > 0.5
