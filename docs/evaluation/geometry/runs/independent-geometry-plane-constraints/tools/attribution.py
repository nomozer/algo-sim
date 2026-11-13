"""Layer-by-layer failure attribution of the 27 image items (run `independent-geometry-plane-constraints`): region (this
run's region_eval, product decision) → critical facts read by local OCR (controlled-vision receipt, unchanged OCR) →
Source Gate on the agent transcription (local_text acceptance) → goal construction from the image after scripted
confirmation (local_image acceptance). The first layer that fails is the attribution. Run from the worktree root."""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
CV = RUN.parent / "controlled-vision-real-image-validation/critical_mathematical_fact_evaluation.json"
L = lambda n: json.loads((RUN / n).read_text(encoding="utf-8"))  # noqa: E731

img, txt, reg = L("local_image_to_simulation_acceptance.json"), L("local_text_to_simulation_acceptance.json"), L("image_region_detection_evaluation.json")
cv = json.loads(CV.read_text(encoding="utf-8"))
missing = {}
for part in ("evaluation", "development"):
    for m in cv[part]["missing"]:
        missing.setdefault(m["case_id"], []).append(f"{m['kind']}: {m['reference']}")
region = {r["case"]: r for r in reg["rows"] if r["set"] == "REAL_SINGLE"}
text = {r["case_id"]: r for r in txt["rows"]}
rows, counts = [], {}
flagged = edits = 0
for r in img["rows"]:
    cid = r["case_id"]
    rg = region.get(cid)
    region_ok = None if rg is None else (rg["decision"] in ("SINGLE_REGION", "WHOLE_PAGE_KEPT") and rg["containment"] >= 0.95 and rg["has_associated_figure"])
    facts_ok = None if rg is None else cid not in missing
    gate_ok = text.get(cid, {}).get("outcome") == "TEXT_INPUT_SIMULATION"
    served = r["outcome"] == "USER_CONFIRMED_SIMULATION"
    cb = r.get("confirmation_burden") or {}
    flagged += cb.get("flagged_spans") or 0
    edits += len(cb.get("edits") or [])
    first = ("NONE" if served else "IMAGE_REGION" if region_ok is False else
             "LOCAL_PARSER_OR_SOURCE_GATE" if not gate_ok else "CRITICAL_FACTS_OCR" if facts_ok is False else "CONFIRMATION_OR_OTHER")
    counts[first] = counts.get(first, 0) + 1
    rows.append({"case_id": cid, "IMAGE_REGION_CORRECT": region_ok, "OCR_TEXT_CORRECT": "NOT_MEASURED_PER_IMAGE (aggregate CER in earlier runs)",
                 "CRITICAL_FACTS_CORRECT": facts_ok, "missing_facts": missing.get(cid, []),
                 "SOURCE_GATE_ACCEPTED_ON_TRANSCRIPTION": gate_ok, "text_reason": text.get(cid, {}).get("reason"),
                 "GOAL_CONSTRUCTION_VERIFIED": served, "INTERACTIVE_SCENE_VERIFIED": "NOT_MEASURED_PER_IMAGE (browser E2E covers the scene types from text)",
                 "first_failing_layer": first, "image_reason": r.get("reason"),
                 "confirmation": {"flagged_spans": cb.get("flagged_spans"), "edits": len(cb.get("edits") or []), "confirms": cb.get("confirms")}})
out = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
       "head": subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip(),
       "items": len(rows), "first_failing_layer_counts": counts,
       "learner_confirmation_burden": {"flagged_spans_total": flagged, "edits_total": edits, "class": "SCRIPTED_NOT_REAL_STUDENT"},
       "reading": "an item fails at the parser / Source Gate when even the agent's correct transcription is not served; OCR is blamed only when the transcription would serve and a critical fact is missing",
       "ground_truth": "AGENT_TRANSCRIBED_UNVERIFIED; region AGENT_ANNOTATED_UNVERIFIED", "rows": rows}
(RUN / "ocr_to_scene_failure_attribution.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(counts, flagged, edits)
