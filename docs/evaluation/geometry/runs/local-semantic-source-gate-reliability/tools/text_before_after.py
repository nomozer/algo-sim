"""Text-to-Geometry before/after on the controlled-vision transcriptions, in-process (the local-first /api/analyze path).

BEFORE is the previous run's receipt (transcription_solver_diagnostic.json, same transcriptions, measured on
c53be83db through HTTP); AFTER is measured here on the working tree through route_text_input. Grading reuses the
previous run's comparator against the dataset key. No AI call (ALLOW_LIVE_AI=0, no key).  Run from backend/.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
PRIOR = RUN.parent / "controlled-vision-real-image-validation"
sys.path[:0] = [str(ROOT / "backend"), str(PRIOR / "tools"), str(RUN.parent / "real-image-ocr-vision-comparative-acceptance/tools")]
from app.ai.adaptive_input_router import route_text_input  # noqa: E402
import evaluate_images as EV  # noqa: E402  (grade(); its RUN is only read, nothing is written there)

OUTCOME = {"SERVED_MATCHES_DATASET_KEY": "LOCAL_SOLVED", "SERVED_DIFFERS_FROM_DATASET_KEY": "WRONG_SERVED",
           "SERVED_NOT_COMPARABLE_NEEDS_ADJUDICATION": "SERVED_UNGRADED"}


def classify(kernel: dict, grade: dict, solver_scope: str) -> str:
    if grade["verdict"] in OUTCOME:
        return OUTCOME[grade["verdict"]]
    if solver_scope == "OUT_OF_SCOPE":
        return "OUT_OF_SCOPE"
    reason = kernel.get("reason_code")
    if reason == "LIVE_AI_DISABLED":
        return "LIVE_AI_DISABLED (local parse incomplete)"
    if reason in ("MISSING_DIMENSION", "EXACT_DOMAIN_EXCEEDED"):
        return "EXACT_KERNEL_GAP"
    if reason in ("AMBIGUOUS_FACT",):
        return "NEEDS_CONFIRMATION"
    if reason in ("INCONSISTENT_FACTS",):
        return "LOCAL_SAFE_REFUSAL"
    return f"REFUSED:{reason}"


def main() -> int:
    items = json.loads((PRIOR / "new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]
    before = {c["case_id"]: c for c in json.loads((PRIOR / "transcription_solver_diagnostic.json").read_text(encoding="utf-8"))["cases"]}
    rows = []
    for item in items:
        b = before[item["case_id"]]
        b_kernel, b_grade = b["variants"]["statement"]["kernel"], b["variants"]["statement"]["grade"]
        t0 = time.perf_counter()
        out = route_text_input(item["statement"], allow_live_ai=False)
        ms = (time.perf_counter() - t0) * 1000
        rd = out.response.get("route_d") or {}
        env = out.response.get("envelope") or {}
        scene = env.get("scene3d") or {}
        kernel = {"status": rd.get("status"), "answers": rd.get("answers"),
                  "reason_code": out.response.get("reason_code") or env.get("reason_code") or rd.get("reason_code"),
                  "scene3d_objects": len(scene.get("objects", []))}
        grade = EV.grade(item, kernel)
        rows.append({"case_id": item["case_id"], "partition": item["partition"], "tags": item["tags"], "expected": item["expected_answer"],
                     "before": {"kernel": {k: b_kernel.get(k) for k in ("status", "answers", "reason_code")}, "verdict": b_grade["verdict"],
                                "outcome": classify(b_kernel, b_grade, b["solver_scope"])},
                     "after": {"kernel": kernel, "verdict": grade["verdict"], "outcome": classify(kernel, grade, b["solver_scope"]), "ms": ms}})
        print(item["case_id"], rows[-1]["before"]["outcome"], "->", rows[-1]["after"]["outcome"], kernel["answers"], flush=True)
    poly = [r for r in rows if "OUT_OF_SCOPE" not in (r["before"]["outcome"], r["after"]["outcome"])]
    count = lambda side, part=None: dict(Counter(r[side]["outcome"] for r in poly if part in (None, r["partition"])))
    (RUN / "text_to_geometry_before_after.json").write_text(json.dumps({
        "run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        "input": "agent transcriptions (statement only, choices excluded), AGENT_TRANSCRIBED_UNVERIFIED",
        "before_source": "controlled-vision-real-image-validation/transcription_solver_diagnostic.json (c53be83db)",
        "after_path": "route_text_input, local-first, ALLOW_LIVE_AI=0 (same code path as /api/analyze in local-first mode)",
        "grading": "served answer compared with the dataset answer key (cos² of an angle compared through cos²(N°))",
        "exposure": "ALL 23 polyhedron items were read while developing this run's rules: development/diagnostic evidence, NOT generalisation",
        "polyhedron_items": len(poly),
        "before_outcomes": count("before"), "after_outcomes": count("after"),
        "after_outcomes_by_partition": {p: count("after", p) for p in ("development", "frozen_external_evaluation")},
        "wrong_served_after": [r["case_id"] for r in poly if r["after"]["outcome"] == "WRONG_SERVED"],
        "cases": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
