# -*- coding: utf-8 -*-
"""W14 Task 11 — what the frozen human hidden-line expectations say about the S4 scenes.

DIAGNOSTIC ONLY. `measure_scene3d_occlusion.transfer_expectation` refuses to carry a
reviewed expectation onto a scene whose drawn geometry changed
(`SCENE_GEOMETRY_CHANGED`), by design: a person reviewed that geometry, not this
one. W14's S4 pass adds drawn objects, so four records stop at that check. This
script runs the REST of the transfer for exactly those records — the independent
oracle at the registered camera and at the new camera, compared with the reviewed
sets — and lists the geometry that changed. It never edits the registry and never
turns the gate result into a pass; it tells the human re-review where to look.
0 model calls. Run from the repository root after the run's results are in place:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/occlusion_transfer_diagnostic.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
import measure_scene3d_occlusion as M  # noqa: E402

RUN = HERE.parents[1]
PRIOR = ROOT / "docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair"
REGISTRY = PRIOR / "inputs/human_expected_visibility.json"
PREIMAGES = ROOT / "docs/evaluation/geometry/runs/w09-verify-cleanup/inputs/REGISTERED_CAMERA_PREIMAGES.json"
OUT = HERE.with_name("OCCLUSION_TRANSFER_DIAGNOSTIC.json")


def _scene(root: Path, scenario_id: str) -> dict:
    p = root / "inputs" / "fixtures" / f"{scenario_id}_positive.json"
    return json.loads(p.read_text(encoding="utf-8"))["envelope"]["scene3d"]


def _drawn(scene: dict) -> dict[str, str]:
    return dict(M.geometry_signature(scene))


def main() -> None:
    measured = json.loads((RUN / "results/OCCLUSION_MEASUREMENT.json").read_text(encoding="utf-8"))
    browser = json.loads((RUN / "results/BROWSER_EVIDENCE.json").read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    preimages = M.load_camera_preimages(PREIMAGES, REGISTRY)
    rows = []
    for f in measured["failures"]:
        if f["code"] != "SCENE_GEOMETRY_CHANGED":
            continue
        sid, vp, state = f["scenario_id"], f["viewport"], f["state"]
        frozen = M._frozen_record(registry, sid, vp, state)
        before, after = _scene(PRIOR, sid), _scene(RUN, sid)
        a, b = _drawn(before), _drawn(after)
        expected = {"visible_edge_ids": sorted(frozen.get("expected_visible_ids", [])),
                    "hidden_edge_ids": sorted(frozen.get("expected_hidden_ids", [])),
                    "mixed_edge_ids": sorted(frozen.get("expected_mixed_ids", []))}
        snap = browser["scenarios"][sid]["positive"][vp]["camera_snapshots"][state]["snapshot"]
        at_registered = M._sets(M.cross_check(after, M._camera(preimages[frozen["camera_snapshot_sha256"]]))["analytic"])
        at_new = M._sets(M.cross_check(after, M._camera(snap))["analytic"])
        rows.append({
            "scenario_id": sid, "viewport": vp, "state": state, "gate": "SCENE_GEOMETRY_CHANGED",
            "drawn_objects_added": sorted(set(b) - set(a)),
            "drawn_objects_removed": sorted(set(a) - set(b)),
            "drawn_objects_changed": sorted(k for k in set(a) & set(b) if a[k] != b[k]),
            "registered_scene_is_the_reviewed_scene":
                M.scene_sha256(before) == frozen.get("scene3d_envelope_sha256"),
            "expected": expected, "oracle_at_registered_camera": at_registered,
            "oracle_at_new_camera": at_new,
            "verdict": ("REVIEWED_SETS_REPRODUCED" if at_registered == expected and at_new == expected
                        else "REVIEWED_SETS_DIFFER"),
        })
    OUT.write_text(json.dumps({
        "check": "W14_OCCLUSION_TRANSFER_DIAGNOSTIC", "model_calls": 0,
        "status": "DIAGNOSTIC_ONLY — the gate result stands; these records need human re-review",
        "registry": REGISTRY.relative_to(ROOT).as_posix(),
        "registry_edited": False, "rows": rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(OUT.name, [(r["scenario_id"], r["verdict"]) for r in rows])


if __name__ == "__main__":
    main()
