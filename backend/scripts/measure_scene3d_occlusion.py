# -*- coding: utf-8 -*-
"""Join browser product output to the independent occlusion oracle.

This runner is read-only with respect to frozen human expectations.  Identity
drift writes a proposed result to diagnostics and fails closed; it never
refreezes expectations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from fractions import Fraction
from pathlib import Path
from typing import Any

from scene3d_occlusion_oracle import CameraSnapshot, OracleFailure, _project, cross_check

PHYSICAL_PIXEL_TOLERANCE = 0.5


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_camera(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Pose/projection at 10 significant digits; ±0 and sub-1e-12 noise → 0.

    OrbitControls damping rewrites an idle pose in its last ULPs, so a raw-float
    hash is not a camera identity. 10 digits keep every change a learner could
    see (≫ 1e-6 px) and drop only float noise.
    """
    def q(value: float) -> float:
        value = float(value)
        return 0.0 if abs(value) < 1e-12 else float(f"{value:.9e}")

    return {
        "position": [q(v) for v in snapshot.get("position", [])],
        "view": [q(v) for v in snapshot["view_matrix_column_major"]],
        "projection": [q(v) for v in snapshot["projection_matrix_column_major"]],
        "viewport": [int(snapshot["viewport_width"]), int(snapshot["viewport_height"])],
        "device_pixel_ratio": float(snapshot["device_pixel_ratio"]),
    }


def canonical_camera_sha256(snapshot: dict[str, Any]) -> str:
    return _sha256(json.dumps(canonical_camera(snapshot), sort_keys=True,
                              separators=(",", ":")).encode())


def load_camera_preimages(path: Path, registry_path: Path) -> dict[str, dict[str, Any]]:
    """Registered hash → snapshot, only for strings whose sha256 IS that hash."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    # Hash the git blob content: a core.autocrlf checkout writes CRLF on disk.
    registry_blob = Path(registry_path).read_bytes().replace(b"\r\n", b"\n")
    if data["source_registry_sha256"] != _sha256(registry_blob):
        raise ValueError("PREIMAGE_REGISTRY_MISMATCH")
    out: dict[str, dict[str, Any]] = {}
    for item in data["preimages"]:
        if _sha256(item["snapshot_json"].encode("utf-8")) != item["camera_snapshot_sha256"]:
            raise ValueError(f"PREIMAGE_HASH_MISMATCH:{item.get('scenario_id')}")
        out[item["camera_snapshot_sha256"]] = json.loads(item["snapshot_json"])
    return out


def camera_identity(registered_sha: str, actual: dict[str, Any], scene: dict[str, Any],
                    preimages: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Is the measured camera the reviewed one? Exact hash, else projection-equivalent
    (same viewport/DPR, every solid vertex within 0.5 physical px)."""
    if actual["sha256"] == registered_sha:
        return {"status": "EXACT", "max_projected_delta_px": 0.0}
    registered = preimages.get(registered_sha)
    if registered is None:
        return {"status": "FROZEN_CAMERA_IDENTITY_MISMATCH",
                "reason": "REGISTERED_PREIMAGE_UNAVAILABLE", "max_projected_delta_px": None}
    a, b = _camera(registered), _camera(actual["snapshot"])
    if (a.viewport_width, a.viewport_height, a.device_pixel_ratio) != (
            b.viewport_width, b.viewport_height, b.device_pixel_ratio):
        return {"status": "FROZEN_CAMERA_IDENTITY_MISMATCH",
                "reason": "VIEWPORT_OR_DPR_CHANGED", "max_projected_delta_px": None}
    points = [tuple(float(Fraction(c)) for c in vertex) for obj in scene["objects"]
              if obj.get("type") == "solid" for vertex in obj["vertices"]]
    delta = max(math.dist(_project(p, a).screen, _project(p, b).screen) for p in points)
    return {
        "status": ("CANONICAL_EQUIVALENT" if delta < PHYSICAL_PIXEL_TOLERANCE
                   else "FROZEN_CAMERA_IDENTITY_MISMATCH"),
        "max_projected_delta_px": delta,
        "canonical_sha256_equal": canonical_camera_sha256(registered) == canonical_camera_sha256(actual["snapshot"]),
    }


#: Fields that carry geometry. Everything else in a scene object is presentation
#: (label, role, learner_text, …) and may change without moving a single edge.
GEOMETRY_FIELDS = ("type", "xyz", "vertices", "vertex_ids", "faces", "polygon", "point",
                   "direction", "normal", "point_a", "point_b", "endpoints", "endpoint_ids",
                   "center", "radius_sq", "anchor", "apex_or_top", "rim_point", "curved_kind",
                   "edge_ownership", "surfaces")
#: Object types that draw nothing (readout / non-visual quantities): adding one
#: moves no edge. Only known types are skipped, so an unknown type still counts.
NON_GEOMETRIC_TYPES = ("quantity",)


def scene_sha256(scene: dict[str, Any]) -> str:
    """Same bytes as the suite's `sha256(JSON.stringify(scene))`."""
    return _sha256(json.dumps(scene, ensure_ascii=False, separators=(",", ":")).encode())


def geometry_signature(scene: dict[str, Any]) -> list[tuple[str, str]]:
    return sorted((obj["id"], json.dumps({k: obj[k] for k in GEOMETRY_FIELDS if k in obj},
                                         sort_keys=True, ensure_ascii=False))
                  for obj in scene.get("objects", []) if obj.get("type") not in NON_GEOMETRIC_TYPES)


def transfer_expectation(frozen: dict[str, Any], registered_scene: dict[str, Any],
                         scene: dict[str, Any], camera_now: dict[str, Any],
                         preimages: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """A DECLARED camera change (w10: the default camera is chosen from scene
    metrics) keeps a frozen human expectation only if (1) `registered_scene` is
    the scene that was reviewed, (2) the geometry is unchanged, and (3) the
    independent oracle reproduces the reviewed sets at BOTH the registered and
    the new camera. The registry itself is never edited."""
    expected = {
        "visible_edge_ids": sorted(frozen.get("expected_visible_ids", [])),
        "hidden_edge_ids": sorted(frozen.get("expected_hidden_ids", [])),
        "mixed_edge_ids": sorted(frozen.get("expected_mixed_ids", [])),
    }
    if scene_sha256(registered_scene) != frozen.get("scene3d_envelope_sha256"):
        return {"status": "REGISTERED_SCENE_MISMATCH"}
    if geometry_signature(registered_scene) != geometry_signature(scene):
        return {"status": "SCENE_GEOMETRY_CHANGED"}
    registered = preimages.get(frozen.get("camera_snapshot_sha256"))
    if registered is None:
        return {"status": "REGISTERED_PREIMAGE_UNAVAILABLE"}
    at_registered = _sets(cross_check(scene, _camera(registered))["analytic"])
    at_new = _sets(cross_check(scene, _camera(camera_now))["analytic"])
    holds = at_registered == expected and at_new == expected
    return {
        "status": ("EXPECTATION_HOLDS_AFTER_DECLARED_CAMERA_CHANGE" if holds
                   else "FROZEN_EXPECTATION_NOT_TRANSFERABLE"),
        "oracle_at_registered_camera": at_registered,
        "oracle_at_new_camera": at_new,
        "expected": expected,
    }


def _rows(column_major: list[float]) -> tuple[tuple[float, float, float, float], ...]:
    return tuple(tuple(float(column_major[column * 4 + row]) for column in range(4))
                 for row in range(4))


def _camera(snapshot: dict[str, Any]) -> CameraSnapshot:
    return CameraSnapshot(
        view=_rows(snapshot["view_matrix_column_major"]),
        projection=_rows(snapshot["projection_matrix_column_major"]),
        viewport_width=int(snapshot["viewport_width"]),
        viewport_height=int(snapshot["viewport_height"]),
        device_pixel_ratio=float(snapshot["device_pixel_ratio"]),
    )


def _sets(value: dict[str, Any]) -> dict[str, list[str]]:
    return {key: sorted(value.get(key, [])) for key in (
        "visible_edge_ids", "hidden_edge_ids", "mixed_edge_ids"
    )}


def _product_spans(value: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for span in value.get("edge_spans", []):
        result.setdefault(span["edge_id"], []).append(span)
    return result


def _compare_product_oracle(product: dict[str, Any], oracle: dict[str, Any]) -> list[dict[str, Any]]:
    failures = []
    if _sets(product) != _sets(oracle):
        failures.append({
            "code": "PRODUCT_ORACLE_EDGE_ID_SET_MISMATCH",
            "product": _sets(product), "oracle": _sets(oracle),
        })
    product_spans = _product_spans(product)
    for edge_id, expected in oracle.get("edge_spans", {}).items():
        actual = product_spans.get(edge_id, [])
        expected_transitions = [float(span["t1"]) for span in expected[:-1]]
        actual_transitions = [float(span["t1"]) for span in actual[:-1]]
        pixels = float(oracle["edge_projected_lengths_px"].get(edge_id, 0))
        if len(expected_transitions) != len(actual_transitions) or any(
            abs(left - right) * pixels > 0.5
            for left, right in zip(expected_transitions, actual_transitions)
        ):
            failures.append({
                "code": "PRODUCT_ORACLE_EDGE_SPAN_MISMATCH",
                "edge_id": edge_id,
                "product_transitions": actual_transitions,
                "oracle_transitions": expected_transitions,
                "physical_pixel_tolerance": 0.5,
            })
    return failures


def _frozen_record(registry: dict[str, Any], scenario_id: str, viewport: str,
                   state: str) -> dict[str, Any] | None:
    return next((record for record in registry.get("scenarios", [])
                 if record.get("scenario_id") == scenario_id
                 and record.get("viewport") == viewport
                 and record.get("state") == state), None)


def run(fixture_root: Path, browser_path: Path, expectations_path: Path | None,
        preimages_path: Path | None = None, declared_camera_change: str | None = None,
        registered_fixture_root: Path | None = None) -> dict[str, Any]:
    browser = json.loads(browser_path.read_text(encoding="utf-8"))
    registry = (json.loads(expectations_path.read_text(encoding="utf-8"))
                if expectations_path else {"scenarios": []})
    preimages = (load_camera_preimages(preimages_path, expectations_path)
                 if preimages_path and expectations_path else {})
    report: dict[str, Any] = {
        "schema_version": "scene3d-occlusion-measurement/1",
        "oracle_implementation": "analytic_projected_interval_clip_w",
        "reference_implementation": "camera_ray_triangle",
        "physical_pixel_tolerance": 0.5,
        "scenarios": {},
        "failures": [],
    }
    for scenario_id, browser_scenario in browser.get("scenarios", {}).items():
        fixture = json.loads((fixture_root / "fixtures" / f"{scenario_id}_positive.json")
                             .read_text(encoding="utf-8"))
        scene = fixture["envelope"]["scene3d"]
        scenario_result: dict[str, Any] = {}
        for viewport, positive in browser_scenario.get("positive", {}).items():
            viewport_result: dict[str, Any] = {}
            for state, product_key in (
                ("neutral_final", "edge_semantics_neutral_final"),
                ("rotated_neutral", "edge_semantics_rotated_neutral"),
            ):
                if product_key not in positive or state not in positive.get("camera_snapshots", {}):
                    continue
                snapshot_record = positive["camera_snapshots"][state]
                camera = _camera(snapshot_record["snapshot"])
                try:
                    checked = cross_check(scene, camera)
                    analytic = checked["analytic"]
                    failures = _compare_product_oracle(positive[product_key], analytic)
                except OracleFailure as error:
                    analytic = None
                    failures = [{"code": error.code, "detail": str(error)}]
                frozen = _frozen_record(registry, scenario_id, viewport, state)
                identity = None
                if frozen:
                    identity = camera_identity(frozen["camera_snapshot_sha256"], snapshot_record,
                                               scene, preimages or {})
                    drifted = (identity["status"] == "FROZEN_CAMERA_IDENTITY_MISMATCH"
                               or frozen.get("scene3d_envelope_sha256")
                               != positive.get("scene3d_envelope_sha256"))
                    if drifted and declared_camera_change and registered_fixture_root:
                        registered_scene = json.loads(
                            (registered_fixture_root / "fixtures" / f"{scenario_id}_positive.json")
                            .read_text(encoding="utf-8"))["envelope"]["scene3d"]
                        transfer = transfer_expectation(frozen, registered_scene, scene,
                                                        snapshot_record["snapshot"], preimages or {})
                        if transfer["status"] == "EXPECTATION_HOLDS_AFTER_DECLARED_CAMERA_CHANGE":
                            identity = {"status": "DECLARED_CAMERA_CHANGE",
                                        "declaration": declared_camera_change,
                                        "measured_identity": identity, "transfer": transfer}
                        else:
                            failures.append({"code": transfer["status"], "transfer": transfer,
                                             "declaration": declared_camera_change})
                    elif drifted:
                        failures.append({
                            "code": "FROZEN_CAMERA_IDENTITY_MISMATCH",
                            "identity": identity,
                            "registered_camera": frozen.get("camera_snapshot_sha256"),
                            "actual_camera": snapshot_record["sha256"],
                            "registered_scene": frozen.get("scene3d_envelope_sha256"),
                            "actual_scene": positive.get("scene3d_envelope_sha256"),
                            "proposed_oracle_result": _sets(analytic or {}),
                        })
                    elif _sets(analytic or {}) != {
                        "visible_edge_ids": sorted(frozen.get("expected_visible_ids", [])),
                        "hidden_edge_ids": sorted(frozen.get("expected_hidden_ids", [])),
                        "mixed_edge_ids": sorted(frozen.get("expected_mixed_ids", [])),
                    }:
                        failures.append({
                            "code": "FROZEN_EXPECTED_VISIBILITY_MISMATCH",
                            "frozen": frozen,
                            "oracle": _sets(analytic or {}),
                        })
                state_result = {
                    "frozen_camera_identity": identity,
                    "product": _sets(positive[product_key]),
                    "oracle": _sets(analytic or {}),
                    "witnesses": (analytic or {}).get("witnesses", []),
                    "failures": failures,
                    "pass": not failures,
                }
                viewport_result[state] = state_result
                report["failures"].extend({
                    "scenario_id": scenario_id, "viewport": viewport, "state": state, **failure,
                } for failure in failures)
            performance = positive.get("occlusion_performance", {})
            timings = performance.get("recomputation_times_ms", [])
            viewport_result["performance"] = {
                "edge_count": performance.get("edge_count", 0),
                "triangle_count": performance.get("triangle_count", 0),
                "sample_count": performance.get("sample_count", 0),
                "span_count": performance.get("span_count", 0),
                "median_recomputation_ms": statistics.median(timings) if timings else 0,
                "p95_recomputation_ms": (
                    sorted(timings)[int((len(timings) - 1) * .95)] if timings else 0
                ),
                "max_recomputation_ms": max(timings) if timings else 0,
                "recomputes_per_orbit": performance.get("recompute_count", 0),
                "immutable_120_frame_recomputations":
                    performance.get("immutable_frame_recomputations"),
            }
            scenario_result[viewport] = viewport_result
        report["scenarios"][scenario_id] = scenario_result
    report["pass"] = not report["failures"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-root", required=True, type=Path)
    parser.add_argument("--browser", required=True, type=Path)
    parser.add_argument("--expectations", type=Path)
    parser.add_argument("--camera-preimages", type=Path,
                        help="verified preimages of the registered camera hashes")
    parser.add_argument("--declared-camera-change",
                        help="id of an intended default-camera change (w10); requires "
                             "--registered-fixture-root")
    parser.add_argument("--registered-fixture-root", type=Path,
                        help="fixture root the frozen registry was reviewed on")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.fixture_root, args.browser, args.expectations, args.camera_preimages,
                 args.declared_camera_change, args.registered_fixture_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
