"""Fresh external evaluation after the candidate freeze, on VMMU rows no agent had downloaded or viewed.

The pool is the 142 rows that controlled-vision-real-image-validation reserved untouched (corpus_contamination_audit.json).
A seeded sample is drawn here; the rest of the pool stays reserved and is never downloaded by this tool.
This is an EXTERNAL DIAGNOSTIC: the same agent selects, transcribes and runs it, so it is not independent H-1.

Steps (run from backend/ with the backend interpreter; no AI provider is called anywhere):
  preregister  write fresh_external_preregistration.json (sample, metrics, stop rules) - committed before any download
  acquire      re-list only the sampled rows (signed URLs expire) and download them into the ignored cache
  sheets       contact sheets of EVERY sampled image (all are viewed, so selection is not keyword-biased)
  manifest     freeze fresh_external_manifest.json from tools/fresh_cases.py (agent transcriptions)
  text         agent transcription -> route_text_input (local-first, in-process)
  api          image -> /api/input/prepare -> (scripted span correction) -> /api/analyze on measured_app
  summarize    fresh_external_evaluation.json from the receipts above
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
PRIOR = RUN.parent / "controlled-vision-real-image-validation"
CACHE = ROOT / ".superpowers/external_image_cache/lsg-fresh-vmmu"
PREREG = RUN / "fresh_external_preregistration.json"
SEED, SAMPLE = 20261113, 48
SERVER = "https://datasets-server.huggingface.co"
AGENT = {"User-Agent": "python-httpx"}  # generic on purpose: no project or user identity leaves this machine


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def write(name: str, data: dict) -> None:
    (RUN / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pool() -> list[int]:
    audit = json.loads((PRIOR / "corpus_contamination_audit.json").read_text(encoding="utf-8"))["independent_h1_candidate_pool"]
    assert audit["status"] == "RESERVED_UNTOUCHED_NOT_AN_H1_RESULT" and audit["count"] == len(audit["rows"]) == 142
    return list(audit["rows"])


def preregister() -> None:
    assert not PREREG.exists(), "pre-registration is immutable; never rewrite it"
    rows = pool()
    sample = sorted(random.Random(SEED).sample(rows, SAMPLE))
    candidate = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
    write(PREREG.name, {
        "schema": "algosim-fresh-external-preregistration/1", "run_id": RUN.name, "registered_at_utc": now(), "head": git("rev-parse", "HEAD"),
        "frozen_candidate": {"commit": candidate["commit"], "product_commit": candidate["product_commit_sha"],
                             "measured_system": candidate["measured_system"]["tree_hash"], "cache_version": candidate["cache_version"]},
        "measurement_class": "EXTERNAL_DIAGNOSTIC_AGENT_TRANSCRIBED", "held_out_claim": "FRESH_TO_THIS_RUN_NOT_INDEPENDENT_H1",
        "evaluator_independence": "NONE: the agent that wrote the fixes selects, transcribes and scores", "live_ai_calls_ceiling": 0,
        "population": "the 142 VMMU Math rows reserved untouched by controlled-vision-real-image-validation",
        "sample": {"seed": SEED, "size": SAMPLE, "rule": "random.Random(seed).sample(pool, size), sorted", "rows": sample,
                   "remaining_reserved_rows": sorted(set(rows) - set(sample)), "remaining_reserved_count": len(rows) - SAMPLE},
        "scope_rule": "in scope iff a polyhedron problem (pyramid, prism, cuboid, cube, tetrahedron) whose question is a distance, angle, length, area or volume; decided from the image by the agent before any Axo output for it is seen; out-of-scope items are counted, not run",
        "oracle": "dataset answer key (letter in the dataset id and ground_truth column); agent hand derivation recorded separately",
        "metrics": {"primary_safety": "WRONG_SERVED count on text and image routes (served answer that differs from the key)",
                    "text_route": "outcome per in-scope item on the agent transcription: LOCAL_SOLVED / WRONG_SERVED / refusal class",
                    "image_route": "outcome per in-scope item: A_LOCAL_AUTO / C2 scripted correction of flagged spans only / D refusal, graded like the text route",
                    "recognition": "critical facts recovered by local OCR (same rule as the previous run)"},
        "stop_rules": ["each item is run once per route; no rerun to change an outcome",
                       "no product, parser, gate or test change in response to these items inside this run; gaps go to the backlog",
                       "no item is removed after its result is seen; an item found out of scope after the run is reported as such, with the reason"],
        "reporting": "counts with n; no percentage claims beyond the sample; labelled agent-transcribed, not human verified, not H-1"})
    print("sampled", SAMPLE, "rows; reserved", len(rows) - SAMPLE)


def sampled() -> list[int]:
    return json.loads(PREREG.read_text(encoding="utf-8"))["sample"]["rows"]


def acquire() -> None:
    import httpx
    CACHE.mkdir(parents=True, exist_ok=True)
    want, meta = set(sampled()), {}
    old = {r["row_idx"]: r["dataset_id"] for r in json.loads((ROOT / ".superpowers/external_image_cache/controlled-vision-vmmu/math_rows_metadata.json").read_text(encoding="utf-8"))["rows"]}
    with httpx.Client(timeout=60, headers=AGENT, trust_env=False, follow_redirects=True) as client:
        for offset in range(min(want) // 100 * 100, max(want) + 1, 100):  # only pages that contain sampled rows
            response = client.get(f"{SERVER}/rows", params={"dataset": "anvo25/vmmu", "config": "default", "split": "full_vqa", "offset": offset, "length": 100})
            if response.status_code != 200:
                raise SystemExit(f"listing stopped at offset {offset}: HTTP {response.status_code}")
            for record in response.json()["rows"]:
                if record["row_idx"] in want:
                    row = record["row"]
                    assert row["ID"] == old[record["row_idx"]], "dataset changed since the pool was reserved"
                    meta[record["row_idx"]] = {"row_idx": record["row_idx"], "dataset_id": row["ID"], "dataset_answer_key": row["ground_truth"],
                                               "multiple_question": row["multiple_question"], "width": row["image"]["width"],
                                               "height": row["image"]["height"], "signed_image_url": row["image"]["src"]}
            time.sleep(2.0)
        assert set(meta) == want, sorted(want - set(meta))
        for row_idx in sorted(meta):
            path = CACHE / f"r{row_idx}_{meta[row_idx]['dataset_id']}"
            if not path.exists():
                response = client.get(meta[row_idx]["signed_image_url"])
                if response.status_code != 200:
                    raise SystemExit(f"download stopped at row {row_idx}: HTTP {response.status_code}")
                path.write_bytes(response.content)
                time.sleep(0.6)
    (CACHE / "metadata.json").write_text(json.dumps({"listed_at_utc": now(), "rows": [meta[r] for r in sorted(meta)]}, indent=1), encoding="utf-8")
    print("downloaded", len(meta))


def sheets() -> None:
    from PIL import Image, ImageDraw
    meta = json.loads((CACHE / "metadata.json").read_text(encoding="utf-8"))["rows"]
    names = [(r["row_idx"], f"r{r['row_idx']}_{r['dataset_id']}") for r in meta]
    for start in range(0, len(names), 6):
        tiles = []
        for row_idx, name in names[start:start + 6]:
            with Image.open(CACHE / name) as original:
                tile = original.convert("RGB")
            tile.thumbnail((1000, 520))
            tiles.append((row_idx, tile))
        height = sum(max(t.height for _, t in tiles[i:i + 2]) + 34 for i in range(0, len(tiles), 2))
        sheet, y = Image.new("RGB", (2040, height), "#cccccc"), 0
        draw = ImageDraw.Draw(sheet)
        for i in range(0, len(tiles), 2):
            for column, (row_idx, tile) in enumerate(tiles[i:i + 2]):
                draw.text((column * 1020 + 6, y + 4), f"row {row_idx}", fill="black")
                sheet.paste(tile, (column * 1020 + 5, y + 26))
            y += max(t.height for _, t in tiles[i:i + 2]) + 34
        sheet.save(CACHE / f"sheet_{start // 6:02d}.jpg", quality=85)
    print("sheets", -(-len(names) // 6))


def manifest() -> None:
    sys.path[:0] = [str(Path(__file__).resolve().parent), str(PRIOR / "tools")]
    from build_corpus import fact_norm, reference_text
    from fresh_cases import AGENT_DERIVED_LETTER, CASES, NOT_IN_SCOPE
    meta = {r["row_idx"]: r for r in json.loads((CACHE / "metadata.json").read_text(encoding="utf-8"))["rows"]}
    assert set(CASES) | set(NOT_IN_SCOPE) == set(meta) and not set(CASES) & set(NOT_IN_SCOPE), "every sampled row must be classified"
    items = []
    for row_idx, case in sorted(CASES.items()):
        row, name = meta[row_idx], f"r{row_idx}_{meta[row_idx]['dataset_id']}"
        data, reference = (CACHE / name).read_bytes(), reference_text(case)
        for kind, forms in case["facts"]:
            assert any(fact_norm(f) in fact_norm(reference) for f in forms), (row_idx, kind, forms)
        key = row["dataset_answer_key"]
        assert key in case["choices"] and re.search(r"_key_([A-D])_", row["dataset_id"]).group(1) == key
        items.append({"case_id": f"vmmu_r{row_idx}", "row_idx": row_idx, "dataset": "anvo25/vmmu", "dataset_id": row["dataset_id"],
                      "cache_path": f".superpowers/external_image_cache/lsg-fresh-vmmu/{name}", "sha256": hashlib.sha256(data).hexdigest(),
                      "partition": "fresh_external_evaluation", "image_committed_to_git": False,
                      "ground_truth_text": reference, "statement": case["statement"], "choices": case["choices"],
                      "ground_truth_status": "AGENT_TRANSCRIBED_UNVERIFIED",
                      "critical_facts": [{"kind": k, "accepted_forms": f} for k, f in case["facts"]],
                      "diagram_description": case["diagram"], "diagram_embedded_facts": case.get("diagram_facts", []),
                      "diagram_dependency_by_agent_reading": case.get("diagram_dependency", "REFERENCE_FIGURE_ONLY_ALL_PREMISES_IN_TEXT"),
                      "source_notes": case["source_notes"], "tags": case["tags"],
                      "dataset_answer_key": key, "expected_answer": case["choices"][key],
                      "oracle": {"provenance": "DATASET_ANSWER_KEY", "agent_hand_derivation_letter": AGENT_DERIVED_LETTER.get(row_idx),
                                 "agent_derivation_agrees_with_key": (AGENT_DERIVED_LETTER[row_idx] == key) if row_idx in AGENT_DERIVED_LETTER else None}})
    write("fresh_external_manifest.json", {"schema": "algosim-fresh-external-corpus/1", "run_id": RUN.name, "frozen_at_utc": now(),
                                           "head": git("rev-parse", "HEAD"), "status": "FROZEN_BEFORE_ANY_AXO_RUN_ON_THESE_IMAGES",
                                           "ground_truth_authority": "AGENT_TRANSCRIBED_UNVERIFIED", "independent_h1": "NOT_MEASURED",
                                           "sampled_rows": len(meta), "in_scope_items": len(items),
                                           "not_in_scope": {f"r{k}": v for k, v in sorted(NOT_IN_SCOPE.items())}, "items": items})
    print("in scope", len(items), "| not in scope", len(NOT_IN_SCOPE))


def items() -> list[dict]:
    return json.loads((RUN / "fresh_external_manifest.json").read_text(encoding="utf-8"))["items"]


def text() -> None:
    os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
    sys.path[:0] = [str(ROOT / "backend"), str(Path(__file__).resolve().parent), str(PRIOR / "tools"),
                    str(RUN.parent / "real-image-ocr-vision-comparative-acceptance/tools")]
    from app.ai.adaptive_input_router import route_text_input
    import evaluate_images as EV
    from text_before_after import classify
    rows = []
    for item in items():
        t0 = time.perf_counter()
        out = route_text_input(item["statement"], allow_live_ai=False)
        rd, env = out.response.get("route_d") or {}, out.response.get("envelope") or {}
        kernel = {"status": rd.get("status"), "answers": rd.get("answers"),
                  "reason_code": out.response.get("reason_code") or env.get("reason_code") or rd.get("reason_code"),
                  "scene3d_objects": len((env.get("scene3d") or {}).get("objects", []))}
        grade = EV.grade(item, kernel)
        rows.append({"case_id": item["case_id"], "tags": item["tags"], "expected": item["expected_answer"], "kernel": kernel,
                     "verdict": grade["verdict"], "outcome": classify(kernel, grade, "IN_SCOPE"), "ms": (time.perf_counter() - t0) * 1000})
        print(item["case_id"], rows[-1]["outcome"], kernel["answers"], flush=True)
    write("fresh_external_text.json", {"run_id": RUN.name, "generated_at_utc": now(), "head": git("rev-parse", "HEAD"),
                                       "path": "route_text_input, local-first, ALLOW_LIVE_AI=0", "input": "agent transcription (statement only)",
                                       "outcomes": dict(Counter(r["outcome"] for r in rows)), "cases": rows})


def api() -> None:
    sys.path.insert(0, str(PRIOR / "tools"))
    import evaluate_images as EV
    EV.E.RUN = RUN
    EV.manifest = lambda partition=None: items()  # same evaluator, this run's frozen fresh manifest
    EV.api("fresh_external_evaluation")


def summarize() -> None:
    prereg, man = json.loads(PREREG.read_text(encoding="utf-8")), json.loads((RUN / "fresh_external_manifest.json").read_text(encoding="utf-8"))
    txt = json.loads((RUN / "fresh_external_text.json").read_text(encoding="utf-8"))
    img = json.loads((RUN / "api_acceptance_fresh_external_evaluation.json").read_text(encoding="utf-8"))
    route = {r["case_id"]: r for r in img["cases"]}
    write("fresh_external_evaluation.json", {
        "schema": "algosim-fresh-external-evaluation/1", "run_id": RUN.name, "generated_at_utc": now(), "head": git("rev-parse", "HEAD"),
        "measurement_class": prereg["measurement_class"], "held_out_claim": prereg["held_out_claim"],
        "evaluator_independence": prereg["evaluator_independence"], "independent_h1": "NOT_MEASURED",
        "frozen_candidate": prereg["frozen_candidate"], "sample": {k: prereg["sample"][k] for k in ("seed", "size", "remaining_reserved_count")},
        "sampled_rows": man["sampled_rows"], "in_scope_items": man["in_scope_items"], "not_in_scope": man["not_in_scope"],
        "text_route_outcomes": txt["outcomes"],
        "image_route": {"prepare_status": dict(Counter(r["prepare_status"] for r in img["cases"])),
                        "routes": dict(Counter(r["route"] for r in img["cases"])),
                        "verdicts": dict(Counter(r["grade"]["verdict"] for r in img["cases"])),
                        "all_critical_facts_in_prepared_text": sum(all(f["recovered"] for f in r["critical_facts_in_prepared_text"]) for r in img["cases"])},
        "wrong_served": {"text": [r["case_id"] for r in txt["cases"] if r["outcome"] == "WRONG_SERVED"],
                         "image": [r["case_id"] for r in img["cases"] if r["grade"]["verdict"] == "SERVED_DIFFERS_FROM_DATASET_KEY"]},
        "per_case": [{"case_id": r["case_id"], "tags": r["tags"], "text_outcome": r["outcome"], "text_reason": r["kernel"]["reason_code"],
                      "image_route": route[r["case_id"]]["route"], "image_verdict": route[r["case_id"]]["grade"]["verdict"],
                      "image_reason": (route[r["case_id"]].get("kernel") or {}).get("reason_code")} for r in txt["cases"]],
        "limits": ["agent transcription and agent scope decision, not human verified", "one dataset, printed exam crops, multiple choice",
                   "small n; counts only", "C2 correction is scripted from the agent transcription, not a real student"]})
    print("written fresh_external_evaluation.json")


if __name__ == "__main__":
    {"preregister": preregister, "acquire": acquire, "sheets": sheets, "manifest": manifest, "text": text, "api": api,
     "summarize": summarize}[sys.argv[1]]()
