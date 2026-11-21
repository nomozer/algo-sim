"""Real local OCR and HTTP acceptance. No provider transport, no oracle injection into auto arm.

Run `--mode local --partition development` before locking candidate, then evaluation.
API/benchmark modes require the loopback measured_app wrapper on port 8767.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import statistics
import sys
import time
import unicodedata

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
BASE_URL = os.environ.get("ALGOSIM_EVALUATION_URL", "http://127.0.0.1:8767")
OUTPUT_TAG = ""
os.environ["ALLOW_LIVE_AI"] = "0"
os.environ.setdefault("LOCAL_OCR_PYTHON", str(ROOT / ".superpowers/ocr-venv/Scripts/python.exe"))
os.environ.setdefault("LOCAL_OCR_TESSDATA", str(ROOT / ".superpowers/tessdata_fast"))
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "backend/scripts"),
               str(ROOT / "docs/evaluation/geometry/runs/real-world-printed-handwriting-acquisition/tools")]
import httpx
import freeze_evaluation_candidate as freeze
from ocr_scoring_helpers import compute_cer_wer, levenshtein_distance
from app.ingestion import local_ocr as ocr
from app.ingestion.local_ocr_route import run_local_ocr_route
from app.ingestion.image import normalize_image
from app.ingestion.region_detector import detect_problem_regions
from app.ai.adaptive_input_router import extract_structured_math_tokens

spec = importlib.util.spec_from_file_location("previous_image_evaluator", ROOT / "docs/evaluation/geometry/runs/image-first-ocr-verified-geometry/tools/evaluate_image_first_ocr.py")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)


def write(name, data):
    if OUTPUT_TAG:
        name = name.removesuffix(".json") + "_" + OUTPUT_TAG + ".json"
    (RUN / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm(text):
    return " ".join(unicodedata.normalize("NFC", text or "").split())


def summary(values):
    ordered = sorted(values)
    return {"n": len(ordered), "p50": statistics.median(ordered) if ordered else None,
            "p95_nearest_rank": ordered[max(0, __import__('math').ceil(.95 * len(ordered)) - 1)] if ordered else None}


def header():
    return {"run_id": RUN.name, "head": freeze._git("rev-parse", "HEAD"),
            "measured_system": freeze.measured_system_hash(), "allow_live_ai": 0,
            "ground_truth_authority": "AGENT_TRANSCRIBED_UNVERIFIED", "independent_h1": "NOT_MEASURED"}


def items(partition):
    manifest = json.loads((RUN / "new_image_corpus_manifest.json").read_text(encoding="utf-8"))
    rows = manifest.get("items", manifest.get("images", manifest.get("cases", [])))
    return [r for r in rows if not partition or r.get("partition", r.get("dataset_partition")) == partition]


def image_path(item):
    p = Path(item.get("cache_path", item.get("filename", "")))
    if p.is_absolute():
        return p
    return ROOT / p if str(p).startswith(".superpowers") else ROOT / ".superpowers/external_image_cache" / p


def scores(prediction, reference):
    # Token agreement is a recognition proxy, not proof of semantic fact correctness.
    hyp, ref = previous._math_tokens(prediction), previous._math_tokens(reference)
    hits = sum((Counter(hyp) & Counter(ref)).values())
    return {**compute_cer_wer(prediction, reference), "reference_characters": len(norm(reference)),
            "character_edits": levenshtein_distance(norm(prediction), norm(reference)),
            "math_token_exact_sequence": hyp == ref, "math_token_matches": hits,
            "math_token_precision": hits / len(hyp) if hyp else None,
            "math_token_recall": hits / len(ref) if ref else None,
            "math_token_reference_count": len(ref), "math_token_prediction_count": len(hyp),
            "full_statement_exact_fidelity": norm(prediction) == norm(reference)}


def local(partition):
    rows = []
    for item in items(partition):
        path = image_path(item)
        data = path.read_bytes()
        started = time.perf_counter()
        normal = normalize_image(data)
        regions = detect_problem_regions(normal)
        rec = run_local_ocr_route(regions.prepared_image.data, regions.prepared_figure_bboxes())
        draft = rec.get("solve_text", "")
        reference = item.get("ground_truth_text", "")
        row = {"case_id": item.get("case_id", item.get("image_id")), "partition": partition,
               "sha256": hashlib.sha256(data).hexdigest(), "ocr_text": draft,
               "extraction_verified": rec.get("extraction_verified"),
               "blocking_reasons": rec.get("blocking_reasons"), "diagram": rec.get("diagram"),
               "review_spans": [{k: s.get(k) for k in ("text", "start", "end", "reason", "kind", "status", "blocking", "alternatives")}
                                for s in rec.get("uncertain_spans", [])],
               "elapsed_ms": (time.perf_counter() - started) * 1000,
               "timing": rec.get("timing"), "low_quality": rec.get("low_quality"),
               "classification": item.get("printed_or_handwritten"),
               "reference_scope": item.get("reference_scope", "UNKNOWN")}
        if reference:
            row["scores_against_unverified_reference"] = scores(draft, reference)
            # Each engine alone, in its own reading order (no layout reconciliation, no reread).
            row["engine_scores_against_unverified_reference"] = {
                name: scores("\n".join(line.get("text", "") for line in engine.get("lines", [])), reference)
                for name, engine in ((rec.get("raw_ocr") or {}).get("engines") or {}).items()}
            facts = item.get("critical_fact_texts", [])
            row["critical_fact_recovery_proxy"] = [{"reference": fact, "found_exactly": re.sub(r"\s+", "", fact) in re.sub(r"\s+", "", draft)} for fact in facts]
        else:
            row["scores_against_unverified_reference"] = "NOT_MEASURED_NO_REFERENCE"
        rows.append(row)
        write(f"local_ocr_{partition}.json", {**header(), "partition": partition, "cases": rows})
        print(row["case_id"], "verified", row["extraction_verified"], "ms", round(row["elapsed_ms"]), flush=True)
    ocr.shutdown_local_ocr()


def payload(path):
    return {"content": base64.b64encode(path.read_bytes()).decode("ascii"), "filename": path.name}


def request_prepare(path, extra=None):
    with httpx.Client(base_url=BASE_URL, timeout=120, trust_env=False) as client:
        client.get("/api/auth/me")
        started = time.perf_counter()
        response = client.post("/api/input/prepare", json={**payload(path), **(extra or {})})
    return {"http_status": response.status_code, "elapsed_ms": (time.perf_counter() - started) * 1000,
            "result": body(response)}


def body(response):
    """An unhandled server error is plain text; keep the measurement instead of crashing the harness."""
    try:
        value = response.json()
    except ValueError:
        value = None
    return value if isinstance(value, dict) else {"status": "NON_JSON_RESPONSE"}


def analyze(text):
    with httpx.Client(base_url=BASE_URL, timeout=120, trust_env=False) as client:
        client.get("/api/auth/me")
        response = client.post("/api/analyze", json={"input": {"type": "text", "content": text}})
    result = response.json()
    env = result.get("envelope") or {}
    route = result.get("route_d") or {}
    scene = env.get("scene3d")
    from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity
    return {"http_status": response.status_code, "status": route.get("status", result.get("status")),
            "answers": route.get("answers"), "reason_code": result.get("reason_code", env.get("reason_code")),
            "failure_category": result.get("failure_category"), "scene3d_objects": len((scene or {}).get("objects", [])),
            "continuity_violations": len(validate_construction_continuity(scene)) if scene else None,
            "oracle_status": "UNGRADED_UNLESS_SEPARATELY_ADJUDICATED"}


def route_mode():
    """Solving without a provider needs the local-first route; in `live` mode every analyze is a 503, not a result."""
    with httpx.Client(base_url=BASE_URL, timeout=30, trust_env=False) as client:
        runtime = client.get("/api/health").json()["runtime"]
    mode = "local-first" if os.environ.get("HYBRID_LOCAL_FIRST") == "1" else runtime["hybrid_route_mode"]
    if runtime["hybrid_route_mode"] != "local-first":
        raise SystemExit("measured server must run with HYBRID_ROUTE_MODE=local-first (found %r)" % runtime["hybrid_route_mode"])
    return {"hybrid_route_mode": mode, "server_allow_live_ai": runtime["hybrid_route"]["allow_live_ai"], "cache_version": runtime["cache_version"]}


def api(partition):
    rows = []
    server = route_mode()
    for item in items(partition):
        path = image_path(item)
        prep = request_prepare(path)
        out = prep["result"]
        row = {"case_id": item.get("case_id", item.get("image_id")), "partition": partition,
               "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
               "prepare": {k: v for k, v in prep.items() if k != "result"},
               "prepare_status": out.get("status"), "reason_code": out.get("reason_code"),
               "ocr_text": out.get("problem_text"), "provenance": out.get("provenance"),
               "metrics": out.get("metrics"), "oracle_status": "UNVERIFIED_AGENT_REFERENCE"}
        variants = [out]
        if out.get("status") == "needs_selection":
            variants = [request_prepare(path, {"selected_candidate_id": c["candidate_id"]})["result"] for c in out.get("candidates", [])]
        outcomes = []
        for variant in variants:
            text = variant.get("problem_text", "")
            if variant.get("status") == "ready":
                outcomes.append({"category": "LOCAL_AUTO", "edited_spans": [], "kernel": analyze(text), "text": text})
            elif variant.get("status") == "needs_confirmation" and item.get("ground_truth_text"):
                simulated = previous.simulate_student(text, variant.get("uncertain_tokens", []), item["ground_truth_text"])
                outcomes.append({"category": "USER_CORRECTED_SIMULATED", "edited_spans": simulated["edits"],
                                 "confirmations": simulated["confirms"], "actions": simulated["actions"],
                                 "final_text": simulated["text"], "kernel": analyze(simulated["text"])})
            else:
                outcomes.append({"category": "NOT_SERVED", "reason_code": variant.get("reason_code")})
        row["outcomes"] = outcomes
        rows.append(row)
        write(f"api_acceptance_{partition}.json", {**header(), "server": server, "partition": partition, "cases": rows,
              "user_correction": "SCRIPTED_NOT_REAL_STUDENT: span edits are chosen from the agent-transcribed reference"})
        print(row["case_id"], row["prepare_status"], [o["category"] for o in outcomes], flush=True)


BENCH_IMAGES = ["hd_q_5259753.jpg", "vmmu_page_r11_Math_0303_test_059_question_39_page_4_key_B_vqa.png"]
SERVER_STATES = {
    "cold_model_cache_miss": "FastAPI process already serving; OCR worker stopped before the request (interpreter start + engine import + model load inside the request); all caches cleared",
    "warm_model_cache_miss": "FastAPI process and OCR worker with loaded models alive; OCR and parser caches cleared",
    "cache_hit": "same image bytes repeated; OCR result cache and parser cache populated; normalisation, region detection and reconciliation still execute",
}


def bench_paths():
    return [ROOT / ".superpowers/external_image_cache" / name for name in BENCH_IMAGES]


def peaks(samples):
    """Sampled peaks over one request window. `exe` distinguishes the venv launcher from the real interpreter."""
    by_pid = {}
    for s in samples:
        for p in s.get("descendants", []):
            cur = by_pid.setdefault(p["pid"], {"pid": p["pid"], "parent_pid": p["parent_pid"], "exe": p["exe"], "peak_rss_mib": 0.0})
            cur["peak_rss_mib"] = max(cur["peak_rss_mib"], p["rss_mib"])
    return {"sample_count": len(samples),
            "fastapi_peak_rss_mib": max((s["fastapi"]["rss_mib"] for s in samples if s.get("fastapi")), default=None),
            "ocr_process_tree_peak_rss_mib": max((s["descendant_rss_mib"] for s in samples), default=None),
            "combined_process_tree_peak_rss_mib": max((s["combined_rss_mib"] for s in samples if s["combined_rss_mib"] is not None), default=None),
            "descendant_processes": sorted(by_pid.values(), key=lambda p: -p["peak_rss_mib"])}


def timed_row(mode, sample, result):
    """One HTTP measurement. Server-reported stage times are NOT summed into the API number; they explain it."""
    out = result["result"]
    metrics = out.get("metrics") or {}
    timing = ((out.get("provenance") or {}).get("local_ocr") or {}).get("timing") or {}
    processing = metrics.get("processing_ms")
    return {"mode": mode, "sample": sample, "elapsed_ms": result["elapsed_ms"], "http_status": result["http_status"],
            "prepare_status": out.get("status"), "metrics": metrics, "server_ocr_route_timing": timing,
            "http_minus_server_processing_ms": result["elapsed_ms"] - processing if processing is not None else None}


def benchmark(repeats):
    paths = bench_paths()
    rows, resource_rows = [], []
    with httpx.Client(base_url=BASE_URL, timeout=120, trust_env=False) as client:
        machine_start = client.get("/__evaluation/resources").json()["machine"]

        # Each sample is taken twice, interleaved: sampler paused (latency of record) and running (memory of record).
        # The sampler shares the FastAPI process, so latency taken while it runs is reported only as harness cost.
        def measured(mode, sample, path, **reset):
            for sampler in (False, True):
                client.post("/__evaluation/sampler", params={"enabled": sampler})
                client.post("/__evaluation/reset", params=reset)
                result = request_prepare(path)
                rows.append({**timed_row(mode, sample, result), "image": path.name, "sampler_running": sampler})
                if sampler:
                    resources = client.get("/__evaluation/resources").json()
                    resource_rows.append({"mode": mode, "sample": sample, "image": path.name, **peaks(resources.pop("samples")),
                                          "ocr_cache_entries": resources["ocr_cache_entries"]})

        for i in range(repeats):
            measured("cold_model_cache_miss", i, paths[i % 2], cold=True)
        for i in range(repeats):
            measured("warm_model_cache_miss", i, paths[i % 2])
        client.post("/__evaluation/reset")
        for path in paths:  # prime both images once, then repeat without clearing anything
            request_prepare(path)
        for i in range(repeats):
            measured("cache_hit", i, paths[i % 2], keep_caches=True)

        # Two different uploads at once, each from a NEW guest session (request_prepare opens one).
        # The worker is serialised by one lock; SQLite session writes can collide (recorded, not hidden).
        rounds = []
        for i in range(repeats):
            client.post("/__evaluation/reset")
            start = time.perf_counter()
            with ThreadPoolExecutor(max_workers=2) as pool:
                concurrent = list(pool.map(request_prepare, paths))
            resources = client.get("/__evaluation/resources").json()
            rounds.append({"round": i, "wall_ms": (time.perf_counter() - start) * 1000,
                           "per_request_ms": [r["elapsed_ms"] for r in concurrent],
                           "statuses": [r["http_status"] for r in concurrent], **peaks(resources.pop("samples"))})
        flat = [status for r in rounds for status in r["statuses"]]
        concurrency = {"simultaneous_uploads": 2, "rounds": rounds, "requests": len(flat),
                       "http_200": flat.count(200), "http_5xx": sum(status >= 500 for status in flat),
                       "wall_ms_all_200_rounds": summary([r["wall_ms"] for r in rounds if set(r["statuses"]) == {200}]),
                       "database": "SQLite file (development default); PostgreSQL NOT_MEASURED",
                       # Sanitized exception metadata captured by measured_app for every unhandled error of this server process.
                       "server_exception_events": client.get("/__evaluation/failures").json()["events"]}
        locked = sum(bool(e.get("database_locked")) for e in concurrency["server_exception_events"])
        concurrency["failure_cause"] = ("NO_FAILURE_OBSERVED" if not concurrency["http_5xx"] else
                                        "SQLITE_DATABASE_LOCKED" if locked >= concurrency["http_5xx"] else
                                        "UNDETERMINED: fewer captured lock events than HTTP 5xx responses")

        # External crash of the launcher: no orphan interpreter, next request recovers with a new worker.
        crashed = client.post("/__evaluation/crash_worker").json()
        time.sleep(1.0)
        orphans = client.get("/__evaluation/alive", params={"pids": ",".join(map(str, crashed["descendant_pids_before"]))}).json()["alive"]
        after = request_prepare(paths[0])
        recovery = {"killed_launcher_pid": crashed["killed_pid"], "tree_pids_before_kill": crashed["descendant_pids_before"],
                    "orphan_python_pids_1s_after_kill": orphans, "next_request_http_status": after["http_status"],
                    "next_request_prepare_status": after["result"].get("status"), "next_request_ms": after["elapsed_ms"],
                    "next_request_cold_worker": (((after["result"].get("provenance") or {}).get("local_ocr") or {}).get("timing") or {}).get("cold_worker"),
                    "pass": bool(crashed["descendant_pids_before"]) and not orphans and after["http_status"] == 200}

        stopped = client.post("/__evaluation/reset", params={"cold": True}).json()
        time.sleep(1.0)
        cleanup = {"tree_pids_before_shutdown": stopped["descendant_pids_before"],
                   "orphan_python_pids_1s_after_shutdown": client.get("/__evaluation/alive", params={"pids": ",".join(map(str, stopped["descendant_pids_before"]))}).json()["alive"],
                   "current": client.get("/__evaluation/resources").json()["current"]}
        machine_end = client.get("/__evaluation/resources").json()["machine"]
    total = machine_end["cpu_total_ticks"] - machine_start["cpu_total_ticks"]
    host = {"logical_cpus": machine_start["logical_cpus"], "total_physical_mib": machine_start["total_physical_mib"],
            "available_physical_mib_at_start": machine_start["available_physical_mib"],
            "available_physical_mib_at_end": machine_end["available_physical_mib"],
            "whole_machine_cpu_busy_fraction_during_benchmark": 1 - (machine_end["cpu_idle_ticks"] - machine_start["cpu_idle_ticks"]) / total if total else None,
            "isolation": "SHARED_DEVELOPER_WORKSTATION_NOT_ISOLATED: other applications were running; figures describe this host under that load"}
    modes = list(SERVER_STATES)
    clean = [r for r in rows if not r["sampler_running"]]
    sampled = [r for r in rows if r["sampler_running"]]
    harness_ab = {mode: {"sampler_paused": summary([r["elapsed_ms"] for r in clean if r["mode"] == mode]),
                         "sampler_running": summary([r["elapsed_ms"] for r in sampled if r["mode"] == mode])} for mode in modes}
    rows_all, rows = rows, clean
    write("cold_warm_latency_benchmark.json", {**header(), "units": "ms", "repeats_per_mode": repeats,
          "images": BENCH_IMAGES, "server_states": SERVER_STATES, "rows": rows_all,
          "summary_basis": "rows with sampler_running=false; the paired sampler_running=true rows feed only harness_sampler_ab and the memory profile",
          "summary": {mode: summary([r["elapsed_ms"] for r in rows if r["mode"] == mode]) for mode in modes},
          "summary_by_image": {mode: {name: summary([r["elapsed_ms"] for r in rows if r["mode"] == mode and r["image"] == name])
                                      for name in BENCH_IMAGES} for mode in modes},
          "summary_http_minus_server_processing_ms": {mode: summary([r["http_minus_server_processing_ms"] for r in rows
                                      if r["mode"] == mode and r["http_minus_server_processing_ms"] is not None]) for mode in modes},
          "timing_boundary": "HTTP POST /api/input/prepare (loopback, new connection, session cookie obtained before the clock starts) through complete JSON body; excludes student dwell, /api/analyze and browser rendering",
          "not_measured_here": ["cold FastAPI process (see cold_process_benchmark.json)", "browser upload-to-result (see frontend_browser_confirmation_audit.json)"],
          "host": host, "harness_sampler_ab": harness_ab,
          "sampler_overhead": "the 25 ms process-tree sampler runs inside the FastAPI process; harness_sampler_ab compares the same workload with it paused and running"})
    write("ocr_worker_resource_profile.json", {**header(), "units": "MiB", "host": host, "rows": resource_rows,
          "summary_peak_by_mode": {mode: {key: summary([r[key] for r in resource_rows if r["mode"] == mode and r[key] is not None])
                                          for key in ("fastapi_peak_rss_mib", "ocr_process_tree_peak_rss_mib", "combined_process_tree_peak_rss_mib")}
                                   for mode in modes},
          "concurrent_uploads": concurrency, "worker_crash_recovery": recovery, "after_explicit_worker_shutdown": cleanup,
          "process_tree_note": "LOCAL_OCR_PYTHON is a Windows venv launcher; the interpreter holding the OCR models is its child. Every descendant of the FastAPI process is sampled and listed by exe name.",
          "combined_memory_note": "Sum of working sets (RSS); shared pages may be counted more than once. Sampled every 25 ms, so the peak is a lower bound. Includes FastAPI and all descendants, excludes the browser and this client.",
          "supersedes": "The first profile in this run sampled only Popen.pid (the 4 MiB launcher) and is not retained; its combined peak of ~135-163 MiB excluded the OCR interpreter.",
          "physical_low_end": "PHYSICAL_LOW_END_NOT_MEASURED"})


def cold_process(repeats):
    """Fresh FastAPI process per sample on port 8768: start-up, first image, second image. Nothing is reused."""
    import subprocess

    tools = Path(__file__).resolve().parent
    env = {**os.environ, "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": "", "PYTHONUTF8": "1",
           "DATABASE_URL": "sqlite:///" + (ROOT / ".superpowers/offline-logs/comparative-coldprocess.db").as_posix(),
           "PYTHONPATH": os.pathsep.join((str(ROOT / "backend"), str(tools)))}
    paths = bench_paths()
    rows = []
    for i in range(repeats):
        started = time.perf_counter()
        server = subprocess.Popen([sys.executable, "-m", "uvicorn", "measured_app:app", "--host", "127.0.0.1",
                                   "--port", "8768", "--log-level", "warning"], cwd=ROOT / "backend", env=env,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            with httpx.Client(base_url="http://127.0.0.1:8768", timeout=120, trust_env=False) as client:
                while True:
                    try:
                        if client.get("/api/health").status_code == 200:
                            break
                    except httpx.TransportError:
                        if server.poll() is not None or time.perf_counter() - started > 120:
                            raise RuntimeError("measured server did not start") from None
                        time.sleep(0.05)
                ready_ms = (time.perf_counter() - started) * 1000
                client.get("/api/auth/me")
                requests = []
                for label, path in (("first_request_cold_process_cold_model", paths[i % 2]),
                                    ("second_request_other_image_warm_model", paths[(i + 1) % 2]),
                                    ("third_request_repeat_first_image_cache_hit", paths[i % 2])):
                    t0 = time.perf_counter()
                    response = client.post("/api/input/prepare", json=payload(path))
                    result = {"http_status": response.status_code, "elapsed_ms": (time.perf_counter() - t0) * 1000, "result": body(response)}
                    requests.append({**timed_row(label, i, result), "image": path.name})
                resources = client.get("/__evaluation/resources").json()
                rows.append({"sample": i, "process_start_to_health_ready_ms": ready_ms, "requests": requests,
                             "resources_whole_lifetime": peaks(resources.pop("samples"))})
        finally:
            subprocess.run(["taskkill", "/PID", str(server.pid), "/T", "/F"], capture_output=True)
            server.wait(timeout=30)
        print("cold process", i, round(ready_ms), [round(r["elapsed_ms"]) for r in rows[-1]["requests"]], flush=True)
    labels = [r["mode"] for r in rows[0]["requests"]]
    write("cold_process_benchmark.json", {**header(), "units": "ms", "repeats": repeats, "images": BENCH_IMAGES, "rows": rows,
          "summary": {"process_start_to_health_ready_ms": summary([r["process_start_to_health_ready_ms"] for r in rows]),
                      **{label: summary([q["elapsed_ms"] for r in rows for q in r["requests"] if q["mode"] == label]) for label in labels}},
          "summary_combined_process_tree_peak_rss_mib": summary([r["resources_whole_lifetime"]["combined_process_tree_peak_rss_mib"] for r in rows]),
          "timing_boundary": "process_start_to_health_ready: Popen of uvicorn until GET /api/health answers 200 (interpreter start, app import, DB init). Requests: HTTP POST /api/input/prepare to complete JSON on an already open connection.",
          "os_file_cache": "NOT_CONTROLLED: model and DLL files stay in the Windows file cache between samples; a first run after reboot is NOT_MEASURED",
          "launch": "measured_app wrapper (25 ms process-tree sampler thread) via uvicorn, single worker, no reload"})


WORKER_PROFILE = r"""
import base64, io, json, sys, time
t_start = time.perf_counter()
sys.path.insert(0, sys.argv[1])
import local_ocr_worker as w
out = {"stdlib_and_worker_module_import_ms": (time.perf_counter() - t_start) * 1000}
def clock(key, fn):
    t = time.perf_counter(); value = fn(); out[key] = (time.perf_counter() - t) * 1000; return value
clock("pillow_import_ms", lambda: __import__("PIL.Image"))
from PIL import Image
raw = open(sys.argv[3], "rb").read()
img = clock("pillow_decode_ms", lambda: Image.open(io.BytesIO(raw)).convert("RGB"))
clock("tesserocr_import_ms", lambda: __import__("tesserocr"))
import tesserocr
api = clock("tesseract_init_ms", lambda: tesserocr.PyTessBaseAPI(path=sys.argv[2], lang="vie", psm=tesserocr.PSM.AUTO))
w._STATE[("tess", sys.argv[2], "vie")] = api
out["tesseract_first_inference_ms"] = w._tesseract(img, sys.argv[2], "vie")["ms"]
out["tesseract_warm_inference_ms"] = w._tesseract(img, sys.argv[2], "vie")["ms"]
def import_rapid():
    from rapidocr import RapidOCR
    return RapidOCR
RapidOCR = clock("rapidocr_import_ms", import_rapid)
w._STATE["rapid"] = clock("rapidocr_constructor_ms", lambda: RapidOCR(params={"Global.log_level": "error"}))
out["onnxruntime_loaded_after_constructor"] = "onnxruntime" in sys.modules
out["rapidocr_first_call_ms"] = w._rapid(raw)["ms"]
out["rapidocr_warm_inference_ms"] = w._rapid(raw)["ms"]
out["rapidocr_lazy_model_load_estimate_ms"] = out["rapidocr_first_call_ms"] - out["rapidocr_warm_inference_ms"]
out["in_interpreter_total_ms"] = (time.perf_counter() - t_start) * 1000
print(json.dumps(out))
"""


def stages(repeats):
    """Per-stage timings, measured SEPARATELY from the HTTP benchmark. These are diagnostic, not an API latency."""
    import subprocess
    from app.ai.adaptive_input_router import verify_ocr_input_fidelity
    from app.ai.local_geometry_parser import clear_local_geometry_parser_cache, parse_geometry_problem_locally
    from app.ingestion.local_ocr import clear_local_ocr_cache, run_local_ocr
    from app.ingestion.ocr_reconcile import reconcile_with_adjudication
    from app.ingestion.local_ocr_route import MIN_AGREEING_FAMILIES

    def clock(fn):
        t = time.perf_counter()
        value = fn()
        return value, (time.perf_counter() - t) * 1000

    worker_rows, pipeline_rows = [], []
    for path in bench_paths():
        for i in range(repeats):
            t = time.perf_counter()
            done = subprocess.run([os.environ["LOCAL_OCR_PYTHON"], "-c", WORKER_PROFILE, str(ROOT / "backend/app/ingestion"),
                                   os.environ["LOCAL_OCR_TESSDATA"], str(path)], capture_output=True, text=True, timeout=300, check=True)
            wall = (time.perf_counter() - t) * 1000
            row = json.loads(done.stdout.strip().splitlines()[-1])
            worker_rows.append({"image": path.name, "sample": i, **row, "process_wall_ms": wall,
                                "interpreter_start_and_exit_ms": wall - row["in_interpreter_total_ms"]})
        for i in range(repeats):
            for state in ("cold_worker", "warm_worker"):
                if state == "cold_worker":
                    ocr.shutdown_local_ocr()
                clear_local_ocr_cache()
                clear_local_geometry_parser_cache()
                data = path.read_bytes()
                normal, normalize_ms = clock(lambda: normalize_image(data))
                regions, region_ms = clock(lambda: detect_problem_regions(normal))
                prepared = regions.prepared_image.data
                raw, ocr_ms = clock(lambda: run_local_ocr(prepared))
                rereads = []

                def reread(boxes):
                    value, ms = clock(lambda: ocr.reread_local_ocr_regions(prepared, boxes))
                    rereads.append(ms)
                    return value

                rec, reconcile_ms = clock(lambda: reconcile_with_adjudication(
                    raw, reread, figure_bboxes=regions.prepared_figure_bboxes(), min_agreeing_families=MIN_AGREEING_FAMILIES))
                text = rec.get("draft_text", "")
                _fid, fidelity_ms = clock(lambda: verify_ocr_input_fidelity(text))
                _parse, parse_ms = clock(lambda: parse_geometry_problem_locally(text))
                engines = raw.get("engines") or {}
                inference = {name: (engines.get(name) or {}).get("ms") for name in ("tesseract", "rapidocr")}
                pipeline_rows.append({"image": path.name, "sample": i, "worker_state": state, "normalize_decode_ms": normalize_ms,
                    "region_detection_ms": region_ms, "ocr_round_trip_ms": ocr_ms, "engine_inference_ms": inference,
                    "ocr_round_trip_minus_inference_ms": ocr_ms - sum(v for v in inference.values() if v),
                    "reconcile_including_reread_ms": reconcile_ms, "reread_round_trips_ms": rereads,
                    "reconcile_excluding_reread_ms": reconcile_ms - sum(rereads),
                    "input_fidelity_gate_ms": fidelity_ms, "local_parse_ms": parse_ms,
                    "extraction_verified": rec.get("extraction_verified")})
    ocr.shutdown_local_ocr()
    numeric = lambda rows, key: summary([r[key] for r in rows if isinstance(r.get(key), (int, float))])
    worker_keys = [k for k in worker_rows[0] if k not in ("image", "sample")]
    pipeline_keys = [k for k in pipeline_rows[0] if k.endswith("_ms") and isinstance(pipeline_rows[0][k], (int, float))]
    write("ocr_stage_profile.json", {**header(), "units": "ms", "repeats": repeats, "images": BENCH_IMAGES,
          "measurement_class": "DIAGNOSTIC_STAGE_TIMING_NOT_API_LATENCY",
          "worker_interpreter_profile": {"rows": worker_rows, "summary": {k: numeric(worker_rows, k) for k in worker_keys},
              "boundary": "one fresh OCR interpreter per sample running the product worker functions; imports and model construction timed individually; reread engines (Latin rec, eng line) are not loaded here",
              "rapidocr_lazy_load": "The RapidOCR constructor does not create ONNX sessions; onnxruntime import and model load happen inside the first call. first_call - warm_inference is therefore an ESTIMATE of model load, not a direct timing; the worker's own per-engine ms on a cold worker includes it."},
          "pipeline_stage_profile": {"rows": pipeline_rows,
              "summary": {state: {k: numeric([r for r in pipeline_rows if r["worker_state"] == state], k) for k in pipeline_keys}
                          for state in ("cold_worker", "warm_worker")},
              "boundary": "product functions called in this harness process with the real sidecar; cold_worker restarts the sidecar before the OCR call"},
          "input_fidelity_gate_note": "verify_ocr_input_fidelity is timed as a pure function on the OCR draft. The image prepare path decides with cross-family reconciliation (extraction_verified); this gate belongs to the adaptive router path.",
          "do_not_sum": "Stage numbers come from separate processes and runs; their sum is not an end-to-end API measurement."})


def prior():
    rows = []
    for item in previous.corpus_items("external16"):
        try:
            row = previous.evaluate_image(item, {}, False)
        except Exception as error:
            row = {"image_id": item["image_id"], "measurement_status": "FAILED",
                   "exception_type": type(error).__name__, "reason_code": getattr(error, "code", None)}
        rows.append(row)
        write("prior_corpus_actual_rerun.json", {**header(), "cases": rows,
              "recognition_reference": "EXPOSED_DEVELOPMENT_AGENT_TRANSCRIPTION",
              "oracle": "Prior independently derived mathematical values; not independent H1",
              "ocr_mode": "ACTUAL_ENGINES_NOT_RECORDED_REPLAY"})
        print(item["image_id"], "measured", row.get("user_facing", {}).get("status", row.get("measurement_status")), flush=True)
    ocr.shutdown_local_ocr()


def summarize():
    """Aggregate the receipts written by the other modes. Counts only; nothing is re-measured or re-graded here."""
    load = lambda name: json.loads((RUN / name).read_text(encoding="utf-8"))
    median = lambda values: statistics.median(values) if values else None
    partitions = {}
    for partition in ("development", "frozen_external_evaluation"):
        local_cases = load(f"local_ocr_{partition}.json")["cases"]
        api_doc = load(f"api_acceptance_{partition}.json")
        scored = [c for c in local_cases if isinstance(c.get("scores_against_unverified_reference"), dict)]
        pick = lambda key: [c["scores_against_unverified_reference"][key] for c in scored]
        engine = lambda name, key: [c["engine_scores_against_unverified_reference"][name][key] for c in scored
                                    if name in c.get("engine_scores_against_unverified_reference", {})]
        tokens = lambda field: sum(c["scores_against_unverified_reference"][field] for c in scored)
        facts = [f for c in scored for f in c.get("critical_fact_recovery_proxy", [])]
        outcomes = [(c["case_id"], o) for c in api_doc["cases"] for o in c["outcomes"]]
        kernel = Counter((o.get("kernel") or {}).get("status") or (o.get("kernel") or {}).get("reason_code") or o["category"] for _, o in outcomes)
        served = [o for _, o in outcomes if (o.get("kernel") or {}).get("status") == "SERVED"]
        partitions[partition] = {
            "images": len(local_cases),
            "recognition_against_unverified_reference": {
                "reconciled_draft": {"cer_median": median(pick("cer")), "cer_min": min(pick("cer")), "cer_max": max(pick("cer")),
                                     "wer_median": median(pick("wer")),
                                     "cer_micro": sum(pick("character_edits")) / sum(pick("reference_characters"))},
                "tesseract_vie_alone": {"cer_median": median(engine("tesseract", "cer")), "wer_median": median(engine("tesseract", "wer"))},
                "rapidocr_alone": {"cer_median": median(engine("rapidocr", "cer")), "wer_median": median(engine("rapidocr", "wer"))},
                "engine_alone_note": "engine reading order without layout reconciliation; diagram labels and footers count as insertions"},
            "math_tokens_reconciled_draft": {
                "micro_precision": tokens("math_token_matches") / tokens("math_token_prediction_count"),
                "micro_recall": tokens("math_token_matches") / tokens("math_token_reference_count"),
                "images_with_exact_token_sequence": sum(pick("math_token_exact_sequence")),
                "images_with_exact_full_statement": sum(pick("full_statement_exact_fidelity"))},
            "critical_fact_exact_substring_proxy": {"found": sum(f["found_exactly"] for f in facts), "total": len(facts)},
            "acceptance_gate": {
                "extraction_verified_images": sum(bool(c["extraction_verified"]) for c in local_cases),
                "false_acceptance_verified_but_math_tokens_differ": [c["case_id"] for c in scored if c["extraction_verified"]
                                                                     and not c["scores_against_unverified_reference"]["math_token_exact_sequence"]],
                "rejected_although_math_tokens_exact": [{"case_id": c["case_id"], "blocking_reasons": c["blocking_reasons"]} for c in scored
                                                        if not c["extraction_verified"] and c["scores_against_unverified_reference"]["math_token_exact_sequence"]],
                "blocking_reason_counts": dict(Counter(r for c in local_cases for r in (c["blocking_reasons"] or [])))},
            "diagram_dependency": dict(Counter((c.get("diagram") or {}).get("classification") for c in local_cases)),
            "prepare_status_counts": dict(Counter(c["prepare_status"] for c in api_doc["cases"])),
            "solve_outcomes": {
                "local_auto_served": sum(o["category"] == "LOCAL_AUTO" for o in served),
                "served_after_simulated_confirmation": sum(o["category"] == "USER_CORRECTED_SIMULATED" for o in served),
                "served_answers_graded_wrong": 0 if not served else "UNGRADED_SERVED_ANSWERS_PRESENT",
                "kernel_result_counts": dict(kernel),
                "per_case": [{"case_id": case_id, "category": o["category"], "kernel_status": (o.get("kernel") or {}).get("status"),
                              "reason_code": (o.get("kernel") or {}).get("reason_code") or o.get("reason_code"),
                              "simulated_edits": len(o.get("edited_spans") or [])} for case_id, o in outcomes]},
            "server": api_doc.get("server")}
    prior_doc = load("prior_corpus_actual_rerun.json")
    arms = [(c["image_id"], arm, o[arm]) for c in prior_doc["cases"] for o in c.get("outcomes", [])
            for arm in ("local_auto", "user_corrected_simulated") if arm in o]
    prior_summary = {
        "images": len(prior_doc["cases"]), "problem_variants": len(arms),
        "local_auto_served_correct": sum(arm == "local_auto" and o["grade"] == "SERVED_CORRECT" for _, arm, o in arms),
        "served_correct_after_simulated_confirmation": sum(arm == "user_corrected_simulated" and o["grade"] == "SERVED_CORRECT" for _, arm, o in arms),
        "not_served": sum(o["grade"] == "REFUSED_OR_NOT_SERVED" for _, _, o in arms),
        "served_wrong": [image for image, _, o in arms if o["grade"] not in ("SERVED_CORRECT", "REFUSED_OR_NOT_SERVED")],
        "needs_confirmation_variants": sum(arm == "user_corrected_simulated" for _, arm, _ in arms),
        "grade_counts": dict(Counter(o["grade"] for _, _, o in arms)),
        "measurement_failures": [c["image_id"] for c in prior_doc["cases"] if c.get("measurement_status") == "FAILED"],
        "exposure": "EXPOSED_DEVELOPMENT: these images drove the OCR/reconciliation design of the previous run"}
    write("image_acceptance_summary.json", {**header(), "generated_from": ["local_ocr_*.json", "api_acceptance_*.json", "prior_corpus_actual_rerun.json"],
          "new_corpus": partitions, "prior_corpus_actual_rerun": prior_summary,
          "claims_not_supported": ["blind generalisation rate (6 evaluation images, 1 inside the solver's named-polyhedron scope)",
                                   "human-verified transcription accuracy (references are agent transcriptions)",
                                   "student correction effort (edits are scripted from the reference)"]})
    print(json.dumps({"new": {k: v["solve_outcomes"]["kernel_result_counts"] for k, v in partitions.items()},
                      "prior": prior_summary["grade_counts"]}, ensure_ascii=False))


def failures():
    rows = []
    cases = [("invalid_image", b"not an image", "problem.png"),
             ("oversized_image", b"\xff\xd8" + b"0" * (11 * 1024 * 1024), "large.jpg")]
    with httpx.Client(base_url=BASE_URL, timeout=120, trust_env=False) as client:
        client.get("/api/auth/me")
        for case_id, data, name in cases:
            response = client.post("/api/input/prepare", json={"content": base64.b64encode(data).decode(), "filename": name})
            body = response.json()
            rows.append({"case_id": case_id, "status": response.status_code, "reason_code": body.get("reason_code"),
                         "controlled": response.status_code < 500, "traceback_leaked": "Traceback (most recent call last)" in response.text})
    write("failure_surface.json", {**header(), "actual_http_cases": rows,
          "worker_crash_timeout_and_invalid_protocol": "backend/tests/test_local_ocr_worker_lifecycle.py (real subprocess tests)",
          "provider_timeout": "OFFLINE_MOCK_REGRESSION_ONLY_NOT_LIVE",
          "unauthorized_provider_calls": "ALLOW_LIVE_AI=0; server key empty; tests use socket guard",
          "mid_inference_user_cancellation": "NOT_MEASURED"})


if __name__ == "__main__":
    assert levenshtein_distance("√3", "√8") == 1
    assert scores("AB' = √3/2", "AB' = √3/2")["full_statement_exact_fidelity"]
    assert not scores("AB = √8/2", "AB' = √3/2")["math_token_exact_sequence"]
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["local", "api", "benchmark", "coldprocess", "stages", "prior", "failures", "summarize"], required=True)
    parser.add_argument("--partition", default="development")
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--tag", choices=["final"], default="")
    args = parser.parse_args()
    OUTPUT_TAG = args.tag
    if args.mode == "benchmark":
        benchmark(args.repeats)
    elif args.mode == "coldprocess":
        cold_process(args.repeats)
    elif args.mode == "stages":
        stages(args.repeats)
    elif args.mode == "prior":
        prior()
    elif args.mode == "summarize":
        summarize()
    elif args.mode == "failures":
        failures()
    elif args.mode == "local":
        local(args.partition)
    else:
        api(args.partition)
