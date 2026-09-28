# -*- coding: utf-8 -*-
"""Join browser product output to the independent occlusion oracle.

This runner is read-only with respect to frozen human expectations.  Identity
drift writes a proposed result to diagnostics and fails closed; it never
refreezes expectations.
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from scene3d_occlusion_oracle import CameraSnapshot, OracleFailure, cross_check


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


def run(fixture_root: Path, browser_path: Path, expectations_path: Path | None) -> dict[str, Any]:
    browser = json.loads(browser_path.read_text(encoding="utf-8"))
    registry = (json.loads(expectations_path.read_text(encoding="utf-8"))
                if expectations_path else {"scenarios": []})
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
                if frozen:
                    if (frozen.get("camera_snapshot_sha256") != snapshot_record["sha256"]
                            or frozen.get("scene3d_envelope_sha256")
                            != positive.get("scene3d_envelope_sha256")):
                        failures.append({
                            "code": "FROZEN_CAMERA_IDENTITY_MISMATCH",
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
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.fixture_root, args.browser, args.expectations)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
