"""Sweep every served Route D scene of the DEVELOPMENT corpora through the independent causal audit, and record a
mathematical fingerprint (exact answers, point coordinates, section vertices, invariance certificate) so that a
before/after pair proves the presentation changes did not move any geometry (run `scene3d-causal-pedagogical-integrity`).
Never a locked W2/W3 row, never H-1. Offline (ALLOW_LIVE_AI=0).

  python scene_sweep.py <backend_dir> <out.json>        # from the worktree root, backend interpreter
  python scene_sweep.py --child                          # internal (reads texts on stdin)
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
RUNS = RUN.parent
sys.path[:0] = [str(Path(__file__).resolve().parent), str(RUNS / "semantic-failure-safe-image-segmentation/tools"),
                str(RUNS / "independent-geometry-plane-constraints/tools")]


def fingerprint(rd: dict, sc: dict) -> dict:
    objs = sc.get("objects") or []
    cfg = rd.get("scene_configuration") or {}
    cert = cfg.get("invariance_certificate") or {}
    return {"answer_exact": rd.get("answer_exact"),
            "points": {o["id"]: o.get("xyz") for o in objs if o.get("type") == "point3"},
            "sections": {o["id"]: o.get("vertex_ids") for o in objs if o.get("type") == "section"},
            "angle_constructions": {o["id"]: {k: o["angle_construction"].get(k) for k in ("relation", "vertex", "vertex_id")}
                                    for o in objs if o.get("angle_construction")},
            "certificate": {"schema": cert.get("schema_version"),
                            "verified": [g.get("independent_verification", {}).get("verified") for g in cert.get("goals") or []
                                         if isinstance(g, dict)]}}


def child() -> None:
    os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
    from causal_audit import audit
    from app.ai.adaptive_input_router import route_text_input
    out = {}
    for k, t in json.loads(sys.stdin.read()).items():
        r = route_text_input(t, allow_live_ai=False).response or {}
        rd, sc = r.get("route_d") or {}, (r.get("envelope") or {}).get("scene3d") or {}
        if rd.get("status") != "SERVED" or not sc:
            out[k] = {"status": rd.get("status")}
            continue
        a = audit(sc)
        out[k] = {"status": "SERVED", "audit": {x: a[x] for x in ("violations", "violation_count", "objects", "events", "steps",
                                                                  "orphans_independent", "unused_auxiliary_flagged", "orphans_not_flagged")},
                  "measures": a["measures"], "fingerprint": fingerprint(rd, sc),
                  "section_edges": [{"theorem": ((e.get("details") or {}).get("justification") or {}).get("theorem"),
                                     "learner_text": e.get("learner_text"), "justification_text": e.get("justification_text")}
                                    for e in sc.get("events") or () if e.get("action") == "EXTEND"],
                  "right_angle_drawn": {o["id"]: (o.get("angle_construction") or {}).get("relation")
                                        or ((o.get("annotation") or {}).get("witness") or {}).get("relation")
                                        for o in sc.get("objects") or () if (o.get("measured_quantity") or {}).get("certified_relation")
                                        in ("perpendicular_lines", "perpendicular_line_plane", "perpendicular_planes")},
                  "scene_sha256": hashlib.sha256(json.dumps(sc, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}
    print(json.dumps(out, ensure_ascii=False, default=str))


def corpora() -> dict[str, dict[str, dict]]:
    from compositional_dev_corpus import CORPUS as COMP
    from semantic_eval import corpora as prev
    c = prev()
    return {"COMP": COMP, "DEV37": c["DEV"], "REAL27": c["REAL27"], "PROBES": c["PROBES"]}


def main(backend: Path, out: Path) -> int:
    texts = {f"{n}:{k}": v["text"] for n, items in corpora().items() for k, v in items.items()}
    env = {**os.environ, "PYTHONPATH": str(backend), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "ALLOW_LIVE_AI": "0",
           "GEMINI_API_KEY": ""}
    res = subprocess.run([sys.executable, __file__, "--child"], input=json.dumps(texts, ensure_ascii=False), capture_output=True,
                         text=True, cwd=backend, env=env, encoding="utf-8")
    if res.returncode:
        raise SystemExit(res.stderr[-3000:])
    rows = json.loads(res.stdout.strip().splitlines()[-1])
    out.write_text(json.dumps({"backend": backend.name if backend.name != "backend" else str(backend.parent.name),
                               "texts": len(texts), "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    served = [r for r in rows.values() if r["status"] == "SERVED"]
    from collections import Counter
    kinds = Counter(k for r in served for k, v in r["audit"]["violations"].items() for _ in v)
    print(len(texts), "texts", len(served), "served", dict(kinds),
          "orphans_not_flagged", sum(len(r["audit"]["orphans_not_flagged"]) for r in served))
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        child()
    else:
        raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))
