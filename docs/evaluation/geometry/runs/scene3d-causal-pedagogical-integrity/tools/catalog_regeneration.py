"""Catalog regeneration evidence of run `scene3d-causal-pedagogical-integrity`.

frontend/src/data/geometry-samples.json (generator backend/scripts/build_geometry_samples.py, this branch): the version at
the run start vs the committed one (geometry fingerprint + causal audit), and reproducibility (re-run the generator: the
committed bytes must come back). The advanced catalog's generator lives on the library branch only (BLOCKED_OWNERSHIP).

  python catalog_regeneration.py <out.json>        # from the worktree root, backend interpreter
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from causal_audit import audit  # noqa: E402

REL = "frontend/src/data/geometry-samples.json"


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT)


def fp(s):
    sc = s["envelope"]["scene3d"]
    return {"points": {o["id"]: o.get("xyz") for o in sc["objects"] if o["type"] == "point3"},
            "quantities": {o["id"]: [o.get("value"), o.get("exact")] for o in sc["objects"] if o["type"] == "quantity"},
            "sections": {o["id"]: o.get("polygon") for o in sc["objects"] if o["type"] == "section"},
            "object_ids": [o["id"] for o in sc["objects"]],
            "events": [[e["step_index"], e["action"], e.get("object")] for e in sc["events"]]}


def main(out: Path) -> int:
    start = json.loads(git("show", f"9d0949b09:{REL}").decode("utf-8"))
    now_raw = (ROOT / REL).read_bytes()
    now = json.loads(now_raw.decode("utf-8"))
    rows = {}
    for a, b in zip(start["samples"], now["samples"]):
        fa, fb = fp(a), fp(b)
        rows[a["id"]] = {"geometry_changed": [k for k in fa if fa[k] != fb[k]],
                         "audit_violations": {"start": audit(a["envelope"]["scene3d"])["violation_count"],
                                              "now": audit(b["envelope"]["scene3d"])["violation_count"]},
                         "section_edges_with_reason": {"start": sum(bool(e.get("justification_text")) for e in a["envelope"]["scene3d"]["events"]),
                                                       "now": sum(bool(e.get("justification_text")) for e in b["envelope"]["scene3d"]["events"])}}
    env = {**os.environ, "ALLOW_LIVE_AI": "0", "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, "scripts/build_geometry_samples.py"], cwd=ROOT / "backend", env=env, capture_output=True, text=True)
    again = (ROOT / REL).read_bytes()
    if again != now_raw:
        (ROOT / REL).write_bytes(now_raw)                 # never leave a modified source behind; the mismatch is reported
    data = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "geometry_samples": {"path": REL, "generator": "backend/scripts/build_geometry_samples.py",
                                 "start_sha256": hashlib.sha256(git("show", f"9d0949b09:{REL}")).hexdigest(),
                                 "now_sha256": hashlib.sha256(now_raw).hexdigest(), "samples": rows,
                                 "regenerated_identically": again == now_raw, "generator_exit": r.returncode},
            "advanced_geometry_samples": {"status": "BLOCKED_OWNERSHIP",
                                          "reason": "generator backend/scripts/build_advanced_geometry_samples.py exists only on the library "
                                                    "branch and imports `circumscribed_sphere`, absent from this branch's kernel; regenerating it here "
                                                    "would mix branches",
                                          "library_committed_audit": "see catalog_fixture_provenance.json"}}
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("identical:", data["geometry_samples"]["regenerated_identically"],
          {k: v["geometry_changed"] for k, v in rows.items() if v["geometry_changed"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
