"""Performance impact of run `grounded-vietnamese-geometry-understanding` (tool copied from scene3d-causal-pedagogical-integrity) (tool copied from proof-soundness-generalized-angle-invariance) (tool copied from compositional-semantics-simulation-goals) (tool copied from semantic-failure-safe-image-segmentation) (host desktop; not a low-end device).

  python perf.py <before_backend_dir>            # from the worktree root
  python perf.py --child <kind>                  # internal: kind = text | prepare
Text: route_text_input median of 5 warm calls on refused and served development texts (diagnostics run on refusals
only) and the cost of diagnose() itself. Prepare: prepare_unified_input wall time per image (local OCR warm after the
first image; the option-group signal reuses the OCR of the same bytes).
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path[:0] = [str(Path(__file__).resolve().parent), str(RUN.parent / "semantic-failure-safe-image-segmentation/tools")]


def child(kind: str) -> None:
    os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
    os.environ.setdefault("LOCAL_OCR_PYTHON", str(ROOT / ".superpowers/ocr-venv/Scripts/python.exe"))
    os.environ.setdefault("LOCAL_OCR_TESSDATA", str(ROOT / ".superpowers/tessdata_fast"))
    out = {}
    if kind == "text":
        from compositional_dev_corpus import CORPUS
        from app.ai.adaptive_input_router import route_text_input
        for k, v in CORPUS.items():
            route_text_input(v["text"], allow_live_ai=False)
            xs = []
            for _ in range(5):
                t0 = time.perf_counter()
                r = route_text_input(v["text"], allow_live_ai=False)
                xs.append((time.perf_counter() - t0) * 1000)
            out[k] = {"ms": statistics.median(xs), "status": r.status}
        try:
            from app.ai.local_failure_diagnostics import diagnose
            from app.ai.local_geometry_parser import parse_geometry_problem_locally
            lp = parse_geometry_problem_locally(CORPUS["order_plane_never_defined"]["text"], use_cache=False)
            t0 = time.perf_counter()
            for _ in range(200):
                diagnose(parse_status=lp.status, parse_reason=lp.reason_code, fallback_reason=lp.fallback_reason,
                         source_coverage=lp.source_coverage.to_dict(), terminal_code="LIVE_AI_DISABLED", fallback_allowed=False)
            out["_diagnose_ms"] = (time.perf_counter() - t0) * 1000 / 200
        except ImportError:
            out["_diagnose_ms"] = None
        try:                                    # run `proof-soundness-generalized-angle-invariance`: proof search cost
            from app.simulation.geometry_functions import planner
            from app.simulation.geometry_functions.registry import doc_ke_hoach
            from app.simulation.geometry_functions.target_invariance import MAX_DERIVED, prove_angle_goal, verify_target_invariance_certificate
            from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2
            from app.ai.local_geometry_parser import parse_geometry_problem_locally as P
            proof = {}
            for k, v in CORPUS.items():
                lp = P(v["text"], use_cache=False)
                if lp.parsed_contract is None:
                    continue
                try:
                    calls = doc_ke_hoach({"calls": planner.lap_ke_hoach({"facts": bridge_v2(lp.parsed_contract)["facts"]}, v["text"]).calls})
                except Exception:  # noqa: BLE001 — a text the planner refuses has no proof to time
                    continue
                ask = next((c for c in calls if c.fn.startswith("ask_angle_")), None)
                if ask is None:
                    continue
                t0 = time.perf_counter()
                for _ in range(20):
                    cert = prove_angle_goal(calls, ask)
                prove_ms = (time.perf_counter() - t0) * 1000 / 20
                ver_ms = None
                if cert and cert.get("status") == "PROVEN":
                    t0 = time.perf_counter()
                    for _ in range(20):
                        verify_target_invariance_certificate(cert, calls, ask)
                    ver_ms = (time.perf_counter() - t0) * 1000 / 20
                proof[k] = {"prove_ms": prove_ms, "verify_ms": ver_ms, "status": (cert or {}).get("status"),
                            "steps": len((cert or {}).get("steps") or ())}
            out["_proof"] = {"max_derived": MAX_DERIVED, "rows": proof}
        except ImportError:
            out["_proof"] = None
    elif kind == "stages":
        # run `grounded-vietnamese-geometry-understanding`: per-stage inclusive time (cProfile cumtime, one warm call per
        # text; profiler overhead inflates absolute values, shares are comparable before/after). Entity resolution, goal
        # extraction and relation reading are the same clause rules (`_parse_clause_into_ast`): one stage, not three.
        import cProfile
        import pstats
        from compositional_dev_corpus import CORPUS
        from app.ai.adaptive_input_router import route_text_input
        stages = {"text_normalization": ("local_geometry_parser.py", "normalize_problem_text"),
                  "clause_segmentation": ("local_geometry_parser.py", "split_into_clauses"),
                  "clause_rules_entity_goal_relation": ("local_geometry_parser.py", "_parse_clause_into_ast"),
                  "local_parse_total": ("local_geometry_parser.py", "parse_geometry_problem_locally"),
                  "typed_fact_bridge": ("typed_fact_next_bridge.py", "bridge_v2"),
                  "planner": ("planner.py", "lap_ke_hoach"),
                  "source_gate": ("registry.py", "kiem_nguon"),
                  "engine_incl_source_gate": ("engine.py", "dung_tu_loi_goi"),
                  "scene3d_adapter": ("adapter4_route.py", "build_adapter4_response"),
                  "end_to_end": ("adaptive_input_router.py", "route_text_input")}
        capability = {"UNSUPPORTED_POINT_CONSTRUCTION", "PLANNER_COMPOSITION_UNSUPPORTED", "UNSUPPORTED_GOAL_FUNCTION",
                      "UNSUPPORTED_GOAL_KIND", "SHAPE_FREEDOM_UNCERTIFIED", "DIAGRAM_DEPENDENT_FACT"}
        for k, v in CORPUS.items():
            r = route_text_input(v["text"], allow_live_ai=False)
            pr = cProfile.Profile()
            pr.enable()
            r = route_text_input(v["text"], allow_live_ai=False)
            pr.disable()
            st = pstats.Stats(pr).stats
            cum = {}
            for (path, _line, name), val in st.items():
                for stage, (mod, fn) in stages.items():
                    if name == fn and path.replace("\\", "/").endswith("/" + mod):
                        cum[stage] = cum.get(stage, 0.0) + val[3] * 1000
            rd = (r.response or {}).get("route_d") or {}
            root = (rd.get("local_diagnostics") or {}).get("root_cause")
            cls = ("SERVED" if r.status == "SERVED" else
                   # understood = the local parse read every clause (COMPLETE) and a later layer refused, or a capability root
                   "UNDERSTOOD_CAPABILITY_UNSUPPORTED" if root in capability or (
                       ((rd.get("local_diagnostics") or {}).get("parse_status") or "").endswith("COMPLETE") and root) else
                   "REFUSED")
            # the route reuses the in-process parse cache, so its parser stages read ~0: profile one COLD parse as well
            from app.ai.local_geometry_parser import parse_geometry_problem_locally as P
            pr = cProfile.Profile()
            pr.enable()
            P(v["text"], use_cache=False)
            pr.disable()
            for (path, _line, name), val in pstats.Stats(pr).stats.items():
                for stage, (mod, fn) in stages.items():
                    if mod == "local_geometry_parser.py" and name == fn and path.replace("\\", "/").endswith("/" + mod):
                        cum["cold_" + stage] = cum.get("cold_" + stage, 0.0) + val[3] * 1000
            xs = []
            for _ in range(5):
                t0 = time.perf_counter()
                P(v["text"], use_cache=False)
                xs.append((time.perf_counter() - t0) * 1000)
            cum["cold_local_parse_wall"] = statistics.median(xs)
            keys = list(stages) + [f"cold_{s_}" for s_ in stages if stages[s_][0] == "local_geometry_parser.py"] + ["cold_local_parse_wall"]
            out[k] = {"class": cls, "status": r.status, "root_cause": root, "stages_ms": {s_: round(cum.get(s_, 0.0), 3) for s_ in keys}}
    else:
        from PIL import Image
        from app.ingestion.unified_input import prepare_unified_input
        from segmentation_eval import pages
        sel = [p for p in pages() if p["set"] == "REAL_SINGLE"][:6] + [p for p in pages() if p["set"].startswith("COMPOSITE")][:4]
        for pg in sel:
            buf = io.BytesIO()
            pg["img"].save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            t0 = time.perf_counter()
            r = asyncio.run(prepare_unified_input(content=b64, declared_mime="image/png", filename="p.png")).to_dict()
            out[pg["id"]] = {"ms": (time.perf_counter() - t0) * 1000, "status": r["status"], "set": pg["set"]}
    print(json.dumps(out))


def run(backend: Path, kind: str) -> dict:
    env = {**os.environ, "PYTHONPATH": str(backend), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": ""}
    res = subprocess.run([sys.executable, __file__, "--child", kind], capture_output=True, text=True, cwd=backend, env=env,
                         encoding="utf-8", check=True)
    return json.loads(res.stdout.strip().splitlines()[-1])


def main(before: Path) -> int:
    res = {side: {kind: run(b, kind) for kind in ("text", "prepare", "stages")} for side, b in (("before", before), ("after", ROOT / "backend"))}

    def med(rows, pred):
        xs = [v["ms"] for k, v in rows.items() if not k.startswith("_") and pred(v)]
        return round(statistics.median(xs), 2) if xs else None

    summary = {side: {"text_refused_median_ms": med(r["text"], lambda v: v["status"] != "SERVED"),
                      "text_served_median_ms": med(r["text"], lambda v: v["status"] == "SERVED"),
                      "diagnose_call_ms": r["text"].get("_diagnose_ms"),
                      "prepare_single_median_ms": med(r["prepare"], lambda v: v["set"] == "REAL_SINGLE"),
                      "prepare_composite_median_ms": med(r["prepare"], lambda v: v["set"] != "REAL_SINGLE"),
                      "proof": None if not r["text"].get("_proof") else {
                          "max_derived": r["text"]["_proof"]["max_derived"],
                          "goals_timed": len(r["text"]["_proof"]["rows"]),
                          "prove_ms_max": round(max(x["prove_ms"] for x in r["text"]["_proof"]["rows"].values()), 3),
                          "verify_ms_max": round(max((x["verify_ms"] or 0) for x in r["text"]["_proof"]["rows"].values()), 3),
                          "steps_max": max(x["steps"] for x in r["text"]["_proof"]["rows"].values()),
                          "budget_exceeded": sum(x["status"] == "PROOF_SEARCH_BUDGET_EXCEEDED" for x in r["text"]["_proof"]["rows"].values())}}
               for side, r in res.items()}
    for side, r in res.items():           # per-stage medians by outcome class; OCR confirmation = prepare rows by status
        by = {}
        for v in r["stages"].values():
            for st_, ms in v["stages_ms"].items():
                by.setdefault(v["class"], {}).setdefault(st_, []).append(ms)
        summary[side]["stages_median_ms_cprofile"] = {c: {"n": len(next(iter(d.values()))), **{st_: round(statistics.median(xs), 3) for st_, xs in d.items()}}
                                                      for c, d in sorted(by.items())}
        summary[side]["prepare_median_ms_by_status"] = {s_: med(r["prepare"], lambda v, s_=s_: v["status"] == s_)
                                                        for s_ in sorted({v["status"] for v in r["prepare"].values()})}
    data = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
            "environment": {"ALLOW_LIVE_AI": "0", "host": "developer desktop, shared, not isolated"},
            "command": f"python docs/evaluation/geometry/runs/{RUN.name}/tools/perf.py <archive of 83fdc3071>/backend",
            "summary": summary, "rows": res, "physical_low_end": "PHYSICAL_LOW_END_NOT_MEASURED"}
    (RUN / "performance_impact.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        child(sys.argv[sys.argv.index("--child") + 1])
        raise SystemExit(0)
    raise SystemExit(main(Path(sys.argv[1])))
