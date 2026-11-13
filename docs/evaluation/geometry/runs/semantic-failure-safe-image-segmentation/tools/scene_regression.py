"""Scene3D correctness regression after this run's changes: the earlier runs' development probes re-served by the current
product and re-checked by their independent exact checkers (read-only — nothing is written into those runs).

  python scene_regression.py     # from the worktree root
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path.insert(0, str(RUN.parent / "independent-geometry-plane-constraints/tools"))
import verify_plane_constraints as V  # noqa: E402

VC = V.VC


def main() -> int:
    plane_rows = V.evaluate(ROOT / "backend")
    probes = {k: t for k, (_g, t) in VC.PROBES.items()}
    raw = V.run(ROOT / "backend", probes)
    sec_rows = {}
    for k, r in raw.items():
        sc = r["scene"] if r["status"] == "SERVED" else None
        checks = VC.check("x", sc) if sc else []
        sec_rows[k] = {"status": r["status"] or "REFUSED", "reason": r["reason"], "checks": len(checks),
                       "failed": [c["check"] for c in checks if not c["ok"]]}
    out = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
           "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
           "environment": {"ALLOW_LIVE_AI": "0"}, "command": "python docs/evaluation/geometry/runs/semantic-failure-safe-image-segmentation/tools/scene_regression.py",
           "dataset_partition": "DEVELOPMENT_EXPOSED probes of independent-geometry-plane-constraints (39) and verified-section-intersection-dihedral-local",
           "oracle_status": "AGENT_DIAGNOSTIC exact checks (Fractions + envelope Gram G), independent of the construction code",
           "plane_constraint_probes": {"as_expected": sum(r["outcome"] == "AS_EXPECTED" for r in plane_rows.values()), "probes": len(plane_rows),
                                       "wrong_served": sum(r["outcome"] == "WRONG_SERVED" for r in plane_rows.values()),
                                       "failed_checks": sum(len(r.get("failed_checks") or []) for r in plane_rows.values()),
                                       "reference": "independent-geometry-plane-constraints: 35/39 as expected, 0 wrong served"},
           "section_intersection_dihedral_probes": {"served": sum(r["status"] == "SERVED" for r in sec_rows.values()), "probes": len(sec_rows),
                                                    "checks": sum(r["checks"] for r in sec_rows.values()),
                                                    "failed": sum(len(r["failed"]) for r in sec_rows.values()), "rows": sec_rows}}
    (RUN / "scene3d_correctness_regression.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out["plane_constraint_probes"], {k: v for k, v in out["section_intersection_dihedral_probes"].items() if k != "rows"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
