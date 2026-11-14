"""Provenance and causal status of the V9.4.15 fixtures / catalogs in BOTH worktrees (run
`scene3d-causal-pedagogical-integrity`). The frontend library worktree is read ONLY through `git show <commit>:<path>`
(its working tree belongs to another session and is never touched).

  python fixture_provenance.py <out.json>        # from the worktree root, backend interpreter
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
LIB = Path("D:/Documents/projects/axo-geometry-library")
HANDOFF = RUN.parent / "axo-backend-geometry-handoff"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from causal_audit import audit  # noqa: E402

FILES = {
    "GEO-BE-V9415-004": "frontend/src/simulations/domains/geometry/scene3d-regression-archetypes-fixtures.json",
    "GEO-BE-V9415-003": "frontend/src/simulations/domains/geometry/scene3d-circumsphere-fixture.json",
    "GEO-BE-V9415-001/002 (advanced catalog)": "frontend/src/data/advanced-geometry-samples.json",
    "offline samples (this branch's generator)": "frontend/src/data/geometry-samples.json",
}
GENERATORS = {
    "frontend/src/data/advanced-geometry-samples.json": "backend/scripts/build_advanced_geometry_samples.py (library branch only; imports "
                                                        "`circumscribed_sphere` absent from this branch's kernel)",
    "frontend/src/data/geometry-samples.json": "backend/scripts/build_geometry_samples.py (this branch; canonical, re-run here)",
    "frontend/src/simulations/domains/geometry/scene3d-circumsphere-fixture.json": "none (static fixture; backend-verified copy delivered in axo-backend-geometry-handoff)",
    "frontend/src/simulations/domains/geometry/scene3d-regression-archetypes-fixtures.json": "none (hand-authored frontend fixture)",
}


def git(cwd, *a):
    return subprocess.check_output(["git", *a], cwd=cwd)


def scenes(x, path=""):
    if isinstance(x, dict):
        if isinstance(x.get("objects"), list) and "events" in x:
            yield path, x
            return
        for k, y in x.items():
            yield from scenes(y, f"{path}/{k}")
    elif isinstance(x, list):
        for i, y in enumerate(x):
            yield from scenes(y, f"{path}[{i}]")


def summary(raw: bytes) -> dict:
    d = json.loads(raw.decode("utf-8"))
    rows = {}
    for p, sc in scenes(d):
        a = audit(sc)
        rows[p] = {"violations": {k: len(v) for k, v in a["violations"].items()},
                   "examples": {k: v[:2] for k, v in a["violations"].items()},
                   "orphans_not_flagged": a["orphans_not_flagged"], "unused_auxiliary_flagged": a["unused_auxiliary_flagged"]}
    return {"sha256_lf": hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(), "scenes": len(rows),
            "violation_total": sum(sum(r["violations"].values()) for r in rows.values()), "per_scene": rows}


def main(out: Path) -> int:
    lib_head = git(LIB, "rev-parse", "HEAD").decode().strip()
    here = git(ROOT, "rev-parse", "HEAD").decode().strip()
    data = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "this_worktree_head": here,
            "library_head": lib_head, "library_working_tree": "NOT READ (another session; read via git show HEAD only)",
            "items": {}}
    for ticket, rel in FILES.items():
        item = {"path": rel, "generator": GENERATORS[rel]}
        try:
            item["this_worktree_committed"] = summary(git(ROOT, "show", f"HEAD:{rel}"))
        except subprocess.CalledProcessError:
            item["this_worktree_committed"] = None                   # the file does not exist on this branch
        try:
            item["library_committed"] = summary(git(LIB, "show", f"{lib_head}:{rel}"))
        except subprocess.CalledProcessError:
            item["library_committed"] = None
        data["items"][ticket] = item
    for name in ("scene3d-circumsphere-fixture.verified.json", "coincident-elements-pyramid.verified.json",
                 "advanced-geometry-samples.backend-fixed.json", "advanced-geometry-samples.coplanar-sections.verified.json"):
        data.setdefault("owner_handoff_artifacts", {})[name] = summary((HANDOFF / name).read_bytes())
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for t, it in data["items"].items():
        print(t, "| here", (it["this_worktree_committed"] or {}).get("violation_total"), "| library",
              (it["library_committed"] or {}).get("violation_total"))
    print({k: v["violation_total"] for k, v in data["owner_handoff_artifacts"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
