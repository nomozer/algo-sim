"""Performance impact of run `certified-scale-cache-safety` (tool copied from compositional-semantics-simulation-goals) (tool copied from semantic-failure-safe-image-segmentation) (host desktop; not a low-end device).

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
    res = {side: {kind: run(b, kind) for kind in ("text", "prepare")} for side, b in (("before", before), ("after", ROOT / "backend"))}

    def med(rows, pred):
        xs = [v["ms"] for k, v in rows.items() if not k.startswith("_") and pred(v)]
        return round(statistics.median(xs), 2) if xs else None

    summary = {side: {"text_refused_median_ms": med(r["text"], lambda v: v["status"] != "SERVED"),
                      "text_served_median_ms": med(r["text"], lambda v: v["status"] == "SERVED"),
                      "diagnose_call_ms": r["text"].get("_diagnose_ms"),
                      "prepare_single_median_ms": med(r["prepare"], lambda v: v["set"] == "REAL_SINGLE"),
                      "prepare_composite_median_ms": med(r["prepare"], lambda v: v["set"] != "REAL_SINGLE")} for side, r in res.items()}
    data = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
            "environment": {"ALLOW_LIVE_AI": "0", "host": "developer desktop, shared, not isolated"},
            "command": "python docs/evaluation/geometry/runs/compositional-semantics-simulation-goals/tools/perf.py <before_backend>",
            "summary": summary, "rows": res, "physical_low_end": "PHYSICAL_LOW_END_NOT_MEASURED"}
    (RUN / "performance_impact.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        child(sys.argv[sys.argv.index("--child") + 1])
        raise SystemExit(0)
    raise SystemExit(main(Path(sys.argv[1])))
