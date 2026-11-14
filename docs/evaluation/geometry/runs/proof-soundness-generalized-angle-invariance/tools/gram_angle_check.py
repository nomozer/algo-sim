"""Independent scene check of run `proof-soundness-generalized-angle-invariance`: for every served angle goal of this
run's corpus, recompute cos² from the SCENE's point coordinates and its `chart_metric` Gram matrix (never the kernel's
measure) and compare with the served exact answer. Covers the 90° goals, whose scenes draw no angle construction.

  python gram_angle_check.py      # from the worktree root, backend interpreter
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path[:0] = [str(ROOT / "backend"), str(Path(__file__).resolve().parent)]
os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""

PREFIX = ("pa_", "pp_", "lp_", "ll_", "ti_right_b", "ti_renamed")


def _sub(p, q):
    return [b - a for a, b in zip(p, q)]


def _mul(M, v):
    return [sum(M[i][j] * v[j] for j in range(3)) for i in range(3)]


def _dot(u, v):
    return sum(a * b for a, b in zip(u, v))


def _cross(u, v):
    return [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]


def _inv(G):
    adj = [[_cross(G[(j + 1) % 3], G[(j + 2) % 3])[i] for j in range(3)] for i in range(3)]   # columns = row cross products
    det = _dot(G[0], _cross(G[1], G[2]))
    return [[adj[i][j] / det for j in range(3)] for i in range(3)]


def cos_sq(kind, P, G, a, b):
    Gi = _inv(G)
    if kind == "lines":
        u, v = _sub(P[a[0]], P[a[1]]), _sub(P[b[0]], P[b[1]])
        return _dot(u, _mul(G, v)) ** 2 / (_dot(u, _mul(G, u)) * _dot(v, _mul(G, v)))
    nrm = lambda pl: _cross(_sub(P[pl[0]], P[pl[1]]), _sub(P[pl[0]], P[pl[2]]))   # a covector (annihilates the plane)
    if kind == "planes":
        n, m = nrm(a), nrm(b)
        return _dot(n, _mul(Gi, m)) ** 2 / (_dot(n, _mul(Gi, n)) * _dot(m, _mul(Gi, m)))
    u, n = _sub(P[a[0]], P[a[1]]), nrm(b)                                        # line–plane: sin² = (n·u)² / (|n|*² |u|²)
    return 1 - _dot(n, u) ** 2 / (_dot(n, _mul(Gi, n)) * _dot(u, _mul(G, u)))


def main() -> int:
    from app.ai.adaptive_input_router import route_text_input
    from app.ai.local_geometry_parser import parse_geometry_problem_locally
    from app.simulation.geometry_functions import planner
    from app.simulation.geometry_functions.registry import doc_ke_hoach
    from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2
    from compositional_dev_corpus import CORPUS
    rows = {}
    for k, c in CORPUS.items():
        if not k.startswith(PREFIX) or c["expect"] != "SERVE":
            continue
        resp = route_text_input(c["text"], allow_live_ai=False).response or {}
        rd, sc = resp.get("route_d") or {}, (resp.get("envelope") or {}).get("scene3d") or {}
        if rd.get("status") != "SERVED":
            rows[k] = {"status": rd.get("status"), "ok": False}
            continue
        lp = parse_geometry_problem_locally(c["text"], use_cache=False)
        calls = doc_ke_hoach({"calls": planner.lap_ke_hoach({"facts": bridge_v2(lp.parsed_contract)["facts"]}, c["text"]).calls})
        ask = next(x for x in calls if x.fn.startswith("ask_angle_"))
        a = ask.args.model_dump()
        kind, x, y = {"ask_angle_lines": ("lines", a.get("line1"), a.get("line2")),
                      "ask_angle_plane_plane": ("planes", a.get("plane1"), a.get("plane2")),
                      "ask_angle_line_plane": ("line_plane", a.get("line"), a.get("plane"))}[ask.fn]
        P = {o["id"]: [Fraction(v) for v in o["xyz"]] for o in sc["objects"] if o["type"] == "point3"}
        G = [[Fraction(v) for v in r] for r in sc["chart_metric"]]
        got = cos_sq(kind, P, G, list(x), list(y)[:3])
        served = Fraction(rd["answer_exact"][ask.id]["coef"])
        rows[k] = {"goal": ask.fn, "operands": [x, y], "chart_metric": sc["chart_metric"], "scene_cos_sq": str(got),
                   "served_cos_sq": str(served), "ok": got == served,
                   "scene_kind": (rd.get("scene_configuration") or {}).get("kind")}
    out = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
           "method": "cos² from scene point3 coordinates with the scene chart_metric Gram G (lines: uᵀGv; planes: covectors with G⁻¹; "
                     "line–plane: 1 − (n·u)²/(nᵀG⁻¹n · uᵀGu)); independent of the kernel's measure",
           "items": rows, "checked": len(rows), "agree": sum(r["ok"] for r in rows.values())}
    (RUN / "generalized_angle_scene_checks.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out["checked"], out["agree"], [k for k, r in rows.items() if not r["ok"]])
    return 0 if out["agree"] == out["checked"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
