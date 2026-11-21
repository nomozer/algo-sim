"""Text-to-Simulation and Image-to-Simulation acceptance, by SIMULATION LEVEL rather than by answer.

Corpus: the 25 controlled-vision VMMU images and their agent transcriptions (all development/exposed by now) and the two
fresh items of the previous run (viewed there; r695's late-square-side wording is a rule of this run ⇒ exposed too).
Per item: outcome class (LOCAL_IMAGE_AUTO_SIMULATION / USER_CONFIRMED_SIMULATION / TEXT_INPUT_SIMULATION / SAFE_REFUSAL /
UNSUPPORTED / OUT_OF_SCOPE), simulation level (PARTIAL_BASE_GEOMETRY / GOAL_CONSTRUCTION_VERIFIED), the independent
invariant checks of `scene_invariants.check_scene`, the dataset-key grade, and the confirmation burden.
`text` runs in-process (route_text_input); `image` needs measured_app on the loopback port (local-first, no AI).
Run from backend/:  python <tools>/simulation_acceptance.py text|image
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

os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
CV = RUN.parent / "controlled-vision-real-image-validation"
LSG = RUN.parent / "local-semantic-source-gate-reliability"
sys.path[:0] = [str(ROOT / "backend"), str(Path(__file__).resolve().parent), str(CV / "tools"),
                str(RUN.parent / "real-image-ocr-vision-comparative-acceptance/tools")]
from scene_invariants import check_scene  # noqa: E402

GOAL_OF = {"measure.angle_cos_sq": "angle", "measure.angle_cos": "angle", "measure.distance": "distance",
           "measure.volume": "volume", "measure.area": "area"}


def corpus() -> list[dict]:
    items = json.loads((CV / "new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]
    fresh = json.loads((LSG / "fresh_external_manifest.json").read_text(encoding="utf-8"))["items"]
    for i in items:
        i["partition_now"] = "DEVELOPMENT_EXPOSED"
    for i in fresh:
        i["partition_now"] = "PREVIOUS_RUN_FRESH_VIEWED" + ("_AND_RULE_TARGETED" if i["case_id"] == "vmmu_r695" else "")
    return items + fresh


def level_of(scene: dict | None) -> dict:
    if not scene:
        return {"level": None}
    objs = scene.get("objects", [])
    q = next((o for o in objs if o.get("type") == "quantity" and "target" in (o.get("display_group") or [])), None)
    goal = GOAL_OF.get((q or {}).get("producer"), "other")
    ann = (q or {}).get("annotation") or {}
    built = {"angle": bool((q or {}).get("angle_construction")) or ann.get("anchor") == "witness",
             "distance": ann.get("anchor") in ("witness", "segment"), "volume": any(o["type"] == "solid" for o in objs),
             "area": ann.get("anchor") == "region"}.get(goal, False)
    checks = check_scene("scene", scene)
    return {"goal": goal, "level": "GOAL_CONSTRUCTION_VERIFIED" if built and all(c["ok"] for c in checks) else
            "PARTIAL_BASE_GEOMETRY", "invariant_checks": len(checks), "invariant_failures": sum(not c["ok"] for c in checks),
            "angle_construction": ((q or {}).get("angle_construction") or {}).get("relation"), "objects": len(objs)}


def outcome(status: str | None, reason: str | None, prefix: str) -> str:
    if status == "SERVED":
        return prefix
    if reason in ("OUT_OF_SCOPE", "GATE_OUT_OF_SCOPE"):
        return "OUT_OF_SCOPE"
    if reason in ("INCONSISTENT_FACTS", "MISSING_DIMENSION", "EXACT_DOMAIN_EXCEEDED", "UNDERDETERMINED_POINT"):
        return "SAFE_REFUSAL"
    return "UNSUPPORTED"


def write(name: str, rows: list[dict], extra: dict) -> None:
    graded = Counter(r["grade"] for r in rows)
    (RUN / name).write_text(json.dumps({
        "run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        "reference_status": "AGENT_TRANSCRIBED_UNVERIFIED; answer oracle = dataset key", **extra,
        "outcomes": dict(Counter(r["outcome"] for r in rows)), "levels": dict(Counter(str(r["simulation"].get("level")) for r in rows)),
        "grades": dict(graded), "wrong_scene_served": [r["case_id"] for r in rows if r["grade"] == "SERVED_DIFFERS_FROM_DATASET_KEY"],
        "broken_invariants": sum(r["simulation"].get("invariant_failures") or 0 for r in rows),
        "interactive_simulation_verified": "per-image browser interaction NOT_MEASURED; the browser E2E (scene3d_interaction_browser_e2e.json) covers the same scene types from text input",
        "rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(name, dict(Counter(r["outcome"] for r in rows)), dict(Counter(str(r["simulation"].get("level")) for r in rows)), dict(graded))


def text() -> None:
    from app.ai.adaptive_input_router import route_text_input
    import evaluate_images as EV
    rows = []
    for item in corpus():
        t0 = time.perf_counter()
        r = route_text_input(item["statement"], allow_live_ai=False).response
        ms = (time.perf_counter() - t0) * 1000
        rd, env = r.get("route_d") or {}, r.get("envelope") or {}
        reason = r.get("reason_code") or env.get("reason_code") or (rd.get("refusal") or {}).get("code")
        kernel = {"status": rd.get("status"), "answers": rd.get("answers")}
        rows.append({"case_id": item["case_id"], "partition_now": item["partition_now"], "tags": item["tags"],
                     "outcome": outcome(rd.get("status"), reason, "TEXT_INPUT_SIMULATION"), "reason": reason,
                     "simulation": level_of(env.get("scene3d")), "grade": EV.grade(item, kernel)["verdict"], "ms": ms})
    write("text_to_simulation_acceptance.json", rows, {"input": "agent transcription (statement only), route_text_input"})


def image() -> None:
    import evaluate_images as EV
    import httpx
    E = EV.E
    E.route_mode()
    rows = []
    for item in corpus():
        path = ROOT / item["cache_path"]
        t0 = time.perf_counter()
        prep = E.request_prepare(path)
        out = prep["result"]
        txt, burden = out.get("problem_text") or "", None
        if out.get("status") == "ready":
            prefix, final = "LOCAL_IMAGE_AUTO_SIMULATION", txt
        elif out.get("status") == "needs_confirmation":
            sim = E.previous.simulate_student(txt, out.get("uncertain_tokens", []), item["ground_truth_text"])
            prefix, final = "USER_CONFIRMED_SIMULATION", sim["text"]
            burden = {"flagged_spans": len(out.get("uncertain_tokens") or []), "edits": sim["edits"], "confirms": sim["confirms"]}
        else:
            rows.append({"case_id": item["case_id"], "partition_now": item["partition_now"], "outcome": "SAFE_REFUSAL",
                         "reason": out.get("reason_code"), "simulation": {"level": None}, "grade": "NOT_SERVED"})
            continue
        prep_ms = (time.perf_counter() - t0) * 1000
        with httpx.Client(base_url=E.BASE_URL, timeout=120, trust_env=False) as client:
            client.get("/api/auth/me")
            res = client.post("/api/analyze", json={"input": {"type": "text", "content": final}}).json()
        total_ms = (time.perf_counter() - t0) * 1000
        rd, env = res.get("route_d") or {}, res.get("envelope") or {}
        reason = res.get("reason_code") or env.get("reason_code") or (rd.get("refusal") or {}).get("code")
        kernel = {"status": rd.get("status"), "answers": rd.get("answers")}
        rows.append({"case_id": item["case_id"], "partition_now": item["partition_now"], "prepare_status": out.get("status"),
                     "outcome": outcome(rd.get("status"), reason, prefix), "reason": reason, "confirmation_burden": burden,
                     "simulation": level_of(env.get("scene3d")), "grade": EV.grade(item, kernel)["verdict"],
                     "upload_to_prepared_ms": prep_ms, "upload_to_first_model_ms": total_ms if rd.get("status") == "SERVED" else None})
        print(item["case_id"], rows[-1]["outcome"], rows[-1]["simulation"].get("level"), rows[-1]["grade"], flush=True)
    write("image_to_simulation_acceptance.json", rows, {"input": "image → /api/input/prepare (local OCR) → scripted confirmation of flagged spans only (SCRIPTED_NOT_REAL_STUDENT) → /api/analyze",
                                                         "upload_to_first_model_note": "server-side path only (prepare + analyze); browser render adds ~0.4 s (frontend_performance_profile.json)"})


if __name__ == "__main__":
    {"text": text, "image": image}[sys.argv[1]]()
