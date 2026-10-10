"""Offline branch evidence exporter. Never overwrites existing run evidence.

Uses preregistered independent assertions and BOTH real fake-provider adapters.
Not an A/B pilot, not a model-understanding evaluation. No network is permitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import socket
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def export(out: Path):
    if out.exists():
        raise RuntimeError("refusing to overwrite evidence directory")
    out.mkdir(parents=True)
    os.environ["ALLOW_LIVE_AI"] = "0"
    def forbidden(*args, **kwargs):
        raise RuntimeError("NETWORK_FORBIDDEN")
    socket.socket.connect = forbidden
    socket.create_connection = forbidden
    tests = runpy.run_path(str(ROOT / "backend/tests/geometry/test_geometry_library_expansion.py"))
    counts = {"A": 0, "B": 0}
    original = tests["run"]
    def counted(arm, *args, **kwargs):
        counts[arm] += 1
        return original(arm, *args, **kwargs)
    original.__globals__["run"] = counted
    rows, scenes = [], []
    for arm in ("A", "B"):
        for index, case in enumerate(tests["POSITIVE"]):
            r, payload = counted(arm, tests["item"](case))
            tests["point_oracle"](r, *case[4:])
            rows.append({"arm": arm, "case": index, "status": r.status, "point": case[4],
                         "xyz": list(map(str, r.points[case[4]])), "answers": r.answers,
                         "payload_sha256": hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()})
            if index < 4:
                scenes.append({"id": f"{arm}-{index}", "scene": r.scene3d})
        for values in tests["NEGATIVE"]:
            tests["test_intersection_fail_closed"](arm, *values)
        for fn, target, code in [("orthogonal_projection_line", "AA", "DEGENERATE_POINTS"),
                                 ("orthogonal_projection", "AAA", "COLLINEAR_POINTS"),
                                 ("orthogonal_projection", "SABC", "NON_COPLANAR_POINTS")]:
            tests["test_projection_degenerate"](arm, fn, target, code)
        for case in tests["POSITIVE"][:4]:
            tests["test_rename_scale_permutation"](arm, case)
            tests["test_wrong_source_roles_rejected"](arm, case)
        tests["test_composition_midpoint_intersection_projection_quantity"](arm)
        tests["test_derived_length_annotation_and_idempotence"](arm)
        tests["test_intersection_operand_swap"](arm)
        tests["test_inconsistent_two_definitions"](arm)
        tests["test_cycle_or_unresolved_operand_no_partial_scene"](arm)
        for prefix, code in [("Nếu ", "CONDITIONAL_CLAUSE"), ("Chứng minh ", "GOAL_CLAUSE_NOT_PREMISE"), ("Không phải ", "NEGATED_CLAUSE")]:
            tests["test_construction_not_borrowed_from_condition_goal_negation"](arm, prefix, code)
        for prefix in ("Nếu SA = 3 thì ", "Biết SA = 3; nếu "):
            tests["test_conditional_consequent_still_not_unconditional_premise"](arm, prefix)
    from scripts.freeze_evaluation_candidate import measured_system_hash
    from scripts.run_hybrid_ab_pilot import audit_reservations
    cert = {"schema": "geometry_library_offline_certification/1", "fake_provider_calls": counts,
            "total_fake_calls": sum(counts.values()), "live_gemini_calls": 0, "network_calls": 0,
            "product_hash": measured_system_hash()[0], "oracle_cases": rows,
            "interpretation": "Deterministic adapter/library certification only; no extraction-quality or safety-population claim",
            "new_surface_budget_audit": audit_reservations()}
    for name, data in (("certification.json", cert), ("scenes.json", scenes)):
        (out / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"calls": counts, "live": 0, "scenes": len(scenes)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    export(parser.parse_args().out.resolve())
