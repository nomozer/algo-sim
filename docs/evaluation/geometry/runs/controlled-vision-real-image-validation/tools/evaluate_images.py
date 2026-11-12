"""Local OCR, verified-text solver diagnostic and real API acceptance on the frozen in-scope corpus.

Reuses the previous run's harness (HTTP helpers, CER/WER, scripted span correction, benchmarks) instead of
copying it; only the output directory is redirected to this run. ALLOW_LIVE_AI stays 0 and no provider is called.

Modes (run from backend/ with the backend interpreter; `transcription` and `api` need measured_app on the
loopback port with HYBRID_ROUTE_MODE=local-first):
  transcription  agent transcription -> /api/analyze. Separates solver capability from recognition. DIAGNOSTIC.
  local          image -> product OCR route in-process. Recognition, critical facts, acceptance gate.
  api            image -> /api/input/prepare -> (scripted correction) -> /api/analyze. Graded against the dataset key.
  summarize      counts from the receipts above; nothing is re-measured.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
PRIOR_TOOLS = ROOT / "docs/evaluation/geometry/runs/real-image-ocr-vision-comparative-acceptance/tools"
sys.path[:0] = [str(Path(__file__).resolve().parent), str(PRIOR_TOOLS)]
import evaluate_acceptance as E  # noqa: E402  (sets ALLOW_LIVE_AI=0, OCR interpreter paths, backend on sys.path)
from build_corpus import fact_norm  # noqa: E402

E.RUN = RUN  # receipts and headers of the reused harness belong to this run
SUPER = {"²": 2, "³": 3}


def manifest(partition: str | None = None) -> list[dict]:
    items = json.loads((RUN / "new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]
    return [i for i in items if partition in (None, "all", i["partition"])]


# ── answer comparison ───────────────────────────────────────────────────────────────────────────────────────────
def numeric(expr: str, a: float) -> float | None:
    """Value of a printed answer such as `a√15/5`, `2√5/5 a`, `V = 2√6a³`, `60°`, `0,5 dm³` with the symbol a = `a`.

    Grammar of the printed forms only: implicit products, one optional `/denominator`, √ binds the next number.
    Returns None when the text is not such an expression, so a mismatch is never produced by a parse guess.
    """
    text = expr.strip().rstrip(".")
    text = re.sub(r"^[A-Za-z]\s*=\s*", "", text)                  # "V = ..."
    text = re.sub(r"\s*(?:dm|cm|m)[²³]?$", "", text).replace("°", "").replace(",", ".").replace(" ", "")
    if not text or not re.fullmatch(r"[0-9a√/.²³()]+", text):
        return None

    def product(part: str) -> float | None:
        value, i = 1.0, 0
        while i < len(part):
            match = re.match(r"√?(\d+(?:\.\d+)?|a)([²³]?)", part[i:])
            if not match or not match.group(0):
                return None
            base = a if match.group(1) == "a" else float(match.group(1))
            if match.group(0).startswith("√"):
                base = math.sqrt(base)
            value *= base ** SUPER.get(match.group(2), 1)
            i += len(match.group(0))
        return value

    parts = text.split("/")
    if len(parts) > 2:
        return None
    head = re.match(r"^(.*?)(a[²³]?)?$", parts[-1]) if len(parts) == 2 else None
    top = product(parts[0])
    if len(parts) == 1:
        return top
    # "√21a/7" and "2√5/5a": a trailing symbol after the denominator multiplies the fraction.
    denominator, tail = product(head.group(1)), product(head.group(2) or "") if head.group(2) else 1.0
    if top is None or not denominator or tail is None:
        return None
    return top / denominator * tail


def same_value(left: str, right: str) -> bool | None:
    # The engine serves angles between lines/planes exactly as `cos²=<value>`; such angles lie in [0°, 90°],
    # where cos² determines the angle, so a printed `N°` is compared through cos²(N°).
    squared = re.fullmatch(r"cos²\s*=\s*(.+)", left.strip())
    degrees = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*°", right.strip())
    if squared:
        value = numeric(squared.group(1), 1.0)
        if value is None or not degrees:
            return None
        return math.isclose(math.cos(math.radians(float(degrees.group(1).replace(",", ".")))) ** 2, value, abs_tol=1e-9)
    values = [(numeric(left, a), numeric(right, a)) for a in (1.3, 2.1)]
    if any(x is None or y is None for x, y in values):
        return None
    return all(math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-9) for x, y in values)


def grade(item: dict, kernel: dict) -> dict:
    """Compare a served answer with the dataset key. Anything not comparable stays ungraded rather than guessed."""
    answers = kernel.get("answers") or {}
    if kernel.get("status") != "SERVED" or not answers:
        return {"verdict": "NOT_SERVED"}
    expected = item["expected_answer"]
    comparisons = {key: same_value(str(value), expected) for key, value in answers.items()}
    other = {letter: any(same_value(str(v), text) for v in answers.values()) for letter, text in item["choices"].items() if letter != item["dataset_answer_key"]}
    if any(c is True for c in comparisons.values()):
        verdict = "SERVED_MATCHES_DATASET_KEY"
    elif any(c is None for c in comparisons.values()):
        verdict = "SERVED_NOT_COMPARABLE_NEEDS_ADJUDICATION"
    else:
        verdict = "SERVED_DIFFERS_FROM_DATASET_KEY"
    return {"verdict": verdict, "expected": expected, "dataset_answer_key": item["dataset_answer_key"], "served": answers,
            "matches_a_wrong_choice": sorted(letter for letter, hit in other.items() if hit)}


# ── recognition scoring ─────────────────────────────────────────────────────────────────────────────────────────
def facts(item: dict, text: str) -> list[dict]:
    normal = fact_norm(text or "")
    return [{"kind": f["kind"], "reference": f["accepted_forms"][0], "recovered": any(fact_norm(form) in normal for form in f["accepted_forms"])}
            for f in item["critical_facts"]]




def transcription() -> None:
    server = E.route_mode()
    rows = []
    for item in manifest():
        variants = {}
        for name, text in (("statement", item["statement"]), ("statement_and_choices", item["ground_truth_text"])):
            kernel = E.analyze(text)
            variants[name] = {"kernel": kernel, "grade": grade(item, kernel)}
        best = variants["statement"]
        status, reason = best["kernel"].get("status"), best["kernel"].get("reason_code")
        if best["grade"]["verdict"] == "SERVED_MATCHES_DATASET_KEY":
            scope = "IN_SCOPE_SOLVABLE_WITH_VERIFIED_TEXT"
        elif item["solver_scope"] == "OUT_OF_SCOPE":
            scope = "OUT_OF_SCOPE"
        elif status == "SERVED":
            scope = "UNKNOWN_PENDING_ADJUDICATION"
        elif status in ("REFUSED", "unsupported"):
            scope = "IN_SCOPE_GEOMETRY_CAPABILITY_GAP"
        else:
            scope = "UNKNOWN_PENDING_ADJUDICATION"
        rows.append({"case_id": item["case_id"], "partition": item["partition"], "tags": item["tags"], "solver_scope": scope,
                     "scope_basis": f"statement -> {status or 'HTTP ' + str(best['kernel'].get('http_status'))} / {reason}; grade {best['grade']['verdict']}",
                     "variants": variants})
        E.write("transcription_solver_diagnostic.json", {
            **E.header(), "server": server, "classification": "DIAGNOSTIC_AGENT_TRANSCRIPTION_NOT_VERIFIED_TEXT",
            "meaning": "Solver capability on the agent's transcription, independent of any image recognition. A 503 LIVE_AI_DISABLED means the local parser did not finish and the live extractor is switched off: capability is then unknown, not refused.",
            "scope_counts": dict(Counter(r["solver_scope"] for r in rows)), "cases": rows})
        print(item["case_id"], scope, status, reason, best["grade"]["verdict"], flush=True)


def local(partition: str) -> None:
    from app.ingestion import local_ocr as ocr
    rows = []
    for item in manifest(partition):
        data = (ROOT / item["cache_path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
        ocr.clear_local_ocr_cache()
        started = time.perf_counter()
        regions = E.detect_problem_regions(E.normalize_image(data))
        rec = E.run_local_ocr_route(regions.prepared_image.data, regions.prepared_figure_bboxes())
        elapsed = (time.perf_counter() - started) * 1000
        draft = rec.get("solve_text", "")
        engines = (rec.get("raw_ocr") or {}).get("engines") or {}
        engine_text = {name: "\n".join(line.get("text", "") for line in e.get("lines", [])) for name, e in engines.items()}
        fact_rows = facts(item, draft)
        rows.append({
            "case_id": item["case_id"], "partition": item["partition"], "sha256": item["sha256"], "ocr_text": draft,
            "extraction_verified": bool(rec.get("extraction_verified")), "blocking_reasons": rec.get("blocking_reasons"),
            "low_quality": rec.get("low_quality"), "diagram_classification": (rec.get("diagram") or {}).get("classification"),
            "diagram_tokens": [(t.get("text")) for t in (rec.get("diagram") or {}).get("tokens", [])],
            "review_spans": [{k: s.get(k) for k in ("text", "reason", "kind", "blocking", "alternatives")} for s in rec.get("uncertain_spans", [])],
            "elapsed_ms": elapsed, "timing": rec.get("timing"),
            "scores": E.scores(draft, item["ground_truth_text"]),
            "engine_scores": {name: {k: v for k, v in E.scores(text, item["ground_truth_text"]).items() if k in ("cer", "wer", "math_token_precision", "math_token_recall")}
                              for name, text in engine_text.items()},
            "critical_facts": fact_rows,
            "engine_critical_facts_recovered": {name: sum(f["recovered"] for f in facts(item, text)) for name, text in engine_text.items()},
            "all_critical_facts_recovered": all(f["recovered"] for f in fact_rows)})
        E.write(f"local_ocr_{partition}.json", {**E.header(), "partition": partition, "ocr_engines": "tesseract vie (tessdata_fast) + rapidocr PP-OCR (sidecar), product reconciliation",
                                                "critical_fact_rule": "accepted surface form present after whitespace removal and prime/degree unification (build_corpus.fact_norm)",
                                                "cases": rows})
        print(item["case_id"], "verified", rows[-1]["extraction_verified"], "facts", sum(f["recovered"] for f in fact_rows), "/", len(fact_rows), "cer", rows[-1]["scores"]["cer"], flush=True)
    ocr.shutdown_local_ocr()


def api(partition: str) -> None:
    server = E.route_mode()
    rows = []
    for item in manifest(partition):
        path = ROOT / item["cache_path"]
        started = time.perf_counter()
        prep = E.request_prepare(path)
        out = prep["result"]
        text = out.get("problem_text") or ""
        row = {"case_id": item["case_id"], "partition": item["partition"], "sha256": item["sha256"], "prepare_http_status": prep["http_status"],
               "prepare_ms": prep["elapsed_ms"], "prepare_status": out.get("status"), "prepare_reason_code": out.get("reason_code"),
               "input_route": (out.get("provenance") or {}).get("input_route"), "provider_calls": (out.get("metrics") or {}).get("vlm_calls"),
               "ocr_text": text, "uncertain_tokens": len(out.get("uncertain_tokens") or []),
               "critical_facts_in_prepared_text": facts(item, text)}
        if out.get("status") == "ready":
            kernel = E.analyze(text)
            row.update(route="A_LOCAL_AUTO", kernel=kernel, grade=grade(item, kernel), final_text=text, scripted_edits=[])
        elif out.get("status") == "needs_confirmation":
            simulated = E.previous.simulate_student(text, out.get("uncertain_tokens", []), item["ground_truth_text"])
            kernel = E.analyze(simulated["text"])
            row.update(route="C2_USER_CORRECTED_SIMULATED", kernel=kernel, grade=grade(item, kernel), final_text=simulated["text"],
                       scripted_edits=simulated["edits"], scripted_confirms=simulated["confirms"], scripted_actions=simulated["actions"],
                       critical_facts_after_scripted_correction=facts(item, simulated["text"]))
        else:
            row.update(route="D_SAFE_REFUSAL_AT_PREPARE", kernel=None, grade={"verdict": "NOT_SERVED"})
        row["image_to_result_ms"] = (time.perf_counter() - started) * 1000
        kernel = row.get("kernel") or {}
        row["scene3d"] = {"objects": kernel.get("scene3d_objects"), "continuity_violations": kernel.get("continuity_violations")}
        rows.append(row)
        E.write(f"api_acceptance_{partition}.json", {**E.header(), "server": server, "partition": partition,
                "user_correction": "SCRIPTED_NOT_REAL_STUDENT: only flagged spans are edited, using the agent transcription; unflagged OCR errors stay",
                "grading": "served answer compared numerically with the dataset key choice; non-comparable answers stay ungraded",
                "cases": rows})
        print(item["case_id"], row["prepare_status"], row["route"], kernel.get("status"), kernel.get("reason_code"), row["grade"]["verdict"], flush=True)


LAYER = {  # which owner a refusal on the agent transcription belongs to; none of these is an OCR failure
    "UNPARSED_GOAL_CANDIDATE": "LOCAL_PARSER_COVERAGE", "UNPARSED_FACT_CANDIDATE": "LOCAL_PARSER_COVERAGE",
    "EMPTY_SOLIDS": "LOCAL_PARSER_COVERAGE", "NOT_ASKED_IN_SOURCE": "SOURCE_GATE", "UNGROUNDED_VALUE": "SOURCE_GATE",
    "SOURCE_PREMISE_UNREAD": "SOURCE_GATE", "EXACT_DOMAIN_EXCEEDED": "GEOMETRY_KERNEL", "AMBIGUOUS_FACT": "CLARIFICATION_POLICY"}


def backlog() -> None:
    """Case-level specification of every verified-text refusal, by owning layer. Writes no product change."""
    from app.ai.local_geometry_parser import parse_geometry_problem_locally
    diag = {c["case_id"]: c for c in json.loads((RUN / "transcription_solver_diagnostic.json").read_text(encoding="utf-8"))["cases"]}
    rows = []
    for item in manifest():
        case = diag[item["case_id"]]
        if case["solver_scope"] == "IN_SCOPE_SOLVABLE_WITH_VERIFIED_TEXT":
            continue
        parsed = parse_geometry_problem_locally(item["statement"])
        kernel = case["variants"]["statement"]["kernel"]
        code = kernel.get("reason_code") if kernel.get("status") in ("REFUSED", "unsupported") else parsed.reason_code
        coverage = parsed.source_coverage
        rows.append({"case_id": item["case_id"], "partition": item["partition"], "tags": item["tags"], "solver_scope": case["solver_scope"],
                     "local_parse_status": parsed.status, "reason_code": code,
                     "owning_layer": "OUT_OF_SCOPE_DOMAIN" if case["solver_scope"] == "OUT_OF_SCOPE" else LAYER.get(code, "UNCLASSIFIED"),
                     "api_result_on_transcription": f"{kernel.get('http_status')} {kernel.get('status')} {kernel.get('reason_code')}",
                     "unparsed_fact_candidates": list(getattr(coverage, "unparsed_fact_candidates", ()) or ()),
                     "unparsed_goal_candidates": list(getattr(coverage, "unparsed_goal_candidates", ()) or ()),
                     "fallback_reason": (parsed.fallback_reason or "")[:300],
                     "expected_answer_from_dataset_key": item["expected_answer"],
                     "evaluation_split_item": item["partition"] == "frozen_external_evaluation"})
    E.write("geometry_capability_gap_backlog.json", {**E.header(),
        "purpose": "Specification for later parser / Source Gate / kernel work. No geometry was expanded in this run.",
        "input": "agent transcription (statement only, choices excluded), local-first route, ALLOW_LIVE_AI=0",
        "meaning_of_503": "With ALLOW_LIVE_AI=1 the local-first route would hand an incomplete local parse to the live extractor. These cases are therefore NOT measured as unsolvable by the product; they are unsolvable WITHOUT any AI call.",
        "counts_by_layer": dict(Counter(r["owning_layer"] for r in rows)),
        "carried_over": [{"case_id": "new_vmmu_full_r446", "run": "real-image-ocr-vision-comparative-acceptance", "owning_layer": "GEOMETRY_KERNEL",
                          "reason_code": "MISSING_DIMENSION", "gap": "legs of a right isosceles triangle from its hypotenuse"}],
        "tuning_rule": "Items marked evaluation_split_item=true must move to development before any fix uses them.",
        "cases": rows})
    print(json.dumps(dict(Counter(r["owning_layer"] for r in rows))))


def summarize() -> None:
    load = lambda name: json.loads((RUN / name).read_text(encoding="utf-8"))
    scope = {c["case_id"]: c["solver_scope"] for c in load("transcription_solver_diagnostic.json")["cases"]}
    result = {}
    for partition in ("development", "frozen_external_evaluation"):
        ocr_rows, api_rows = load(f"local_ocr_{partition}.json")["cases"], load(f"api_acceptance_{partition}.json")["cases"]
        fact_rows = [f for c in ocr_rows for f in c["critical_facts"]]
        by_kind = {kind: {"recovered": sum(f["recovered"] for f in fact_rows if f["kind"] == kind), "total": sum(f["kind"] == kind for f in fact_rows)}
                   for kind in sorted({f["kind"] for f in fact_rows})}
        median = lambda key: statistics.median(c["scores"][key] for c in ocr_rows)
        engine_facts = {name: sum(c["engine_critical_facts_recovered"].get(name, 0) for c in ocr_rows) for name in ("tesseract", "rapidocr")}
        solvable = [c for c in api_rows if scope[c["case_id"]] == "IN_SCOPE_SOLVABLE_WITH_VERIFIED_TEXT"]
        routes = Counter(c["route"] for c in api_rows)
        verdicts = lambda rows, route: dict(Counter(c["grade"]["verdict"] for c in rows if c["route"] == route))
        result[partition] = {
            "images": len(ocr_rows),
            "solver_scope_counts": dict(Counter(scope[c["case_id"]] for c in ocr_rows)),
            "recognition": {"cer_median": median("cer"), "wer_median": median("wer"),
                            "cer_micro": sum(c["scores"]["character_edits"] for c in ocr_rows) / sum(c["scores"]["reference_characters"] for c in ocr_rows),
                            "exact_full_statement_images": sum(c["scores"]["full_statement_exact_fidelity"] for c in ocr_rows),
                            "exact_math_token_sequence_images": sum(c["scores"]["math_token_exact_sequence"] for c in ocr_rows),
                            "single_engine_cer_median": {name: statistics.median(c["engine_scores"][name]["cer"] for c in ocr_rows if name in c["engine_scores"])
                                                         for name in ("tesseract", "rapidocr")}},
            "critical_facts": {"recovered": sum(f["recovered"] for f in fact_rows), "total": len(fact_rows), "by_kind": by_kind,
                               "images_with_all_facts": sum(c["all_critical_facts_recovered"] for c in ocr_rows),
                               "single_engine_recovered": engine_facts,
                               "missing": [{"case_id": c["case_id"], "kind": f["kind"], "reference": f["reference"]} for c in ocr_rows for f in c["critical_facts"] if not f["recovered"]]},
            "routing": {"local_accepted_verified": sum(c["extraction_verified"] for c in ocr_rows),
                        "false_acceptance_verified_but_fact_missing": [c["case_id"] for c in ocr_rows if c["extraction_verified"] and not c["all_critical_facts_recovered"]],
                        "rejected_although_all_facts_recovered": [{"case_id": c["case_id"], "blocking_reasons": c["blocking_reasons"]} for c in ocr_rows
                                                                  if not c["extraction_verified"] and c["all_critical_facts_recovered"]],
                        "blocking_reason_counts": dict(Counter(r for c in ocr_rows for r in (c["blocking_reasons"] or []))),
                        "prepare_status_counts": dict(Counter(c["prepare_status"] for c in api_rows)),
                        "provider_calls": sum(c["provider_calls"] or 0 for c in api_rows)},
            "image_to_result": {"route_counts": dict(routes),
                                "A_LOCAL_AUTO": verdicts(api_rows, "A_LOCAL_AUTO"),
                                "C2_USER_CORRECTED_SIMULATED": verdicts(api_rows, "C2_USER_CORRECTED_SIMULATED"),
                                "B_VISION_LIVE": "NOT_MEASURED", "C_USER_CORRECTED_REAL": "NOT_MEASURED",
                                "wrong_served_against_dataset_key": [c["case_id"] for c in api_rows if c["grade"]["verdict"] == "SERVED_DIFFERS_FROM_DATASET_KEY"],
                                "needs_adjudication": [c["case_id"] for c in api_rows if c["grade"]["verdict"] == "SERVED_NOT_COMPARABLE_NEEDS_ADJUDICATION"],
                                "among_verified_text_solvable": {"images": len(solvable),
                                                                 "A_LOCAL_AUTO_correct": sum(c["route"] == "A_LOCAL_AUTO" and c["grade"]["verdict"] == "SERVED_MATCHES_DATASET_KEY" for c in solvable),
                                                                 "C2_SIMULATED_correct": sum(c["route"] == "C2_USER_CORRECTED_SIMULATED" and c["grade"]["verdict"] == "SERVED_MATCHES_DATASET_KEY" for c in solvable),
                                                                 "not_served": [c["case_id"] for c in solvable if c["grade"]["verdict"] == "NOT_SERVED"]},
                                "scene3d_served_with_objects": sum(bool((c["scene3d"] or {}).get("objects")) for c in api_rows),
                                "scene3d_continuity_violations": sum((c["scene3d"] or {}).get("continuity_violations") or 0 for c in api_rows),
                                "image_to_result_ms_median": statistics.median(c["image_to_result_ms"] for c in api_rows)}}
    E.write("image_evaluation_summary.json", {**E.header(), "generated_from": ["transcription_solver_diagnostic.json", "local_ocr_*.json", "api_acceptance_*.json"],
            "partitions": result,
            "claims_not_supported": ["population accuracy (one dataset, 25 rendered multiple-choice crops)", "blind generalisation (the evaluating agent transcribed the images)",
                                     "human correction effort (edits are scripted)", "any Vision result (no provider call)"]})
    print(json.dumps({p: {"facts": f"{v['critical_facts']['recovered']}/{v['critical_facts']['total']}", "routes": v["image_to_result"]["route_counts"],
                          "auto": v["image_to_result"]["A_LOCAL_AUTO"], "sim": v["image_to_result"]["C2_USER_CORRECTED_SIMULATED"]} for p, v in result.items()}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    assert same_value("a√15/5", "√15a/5") and same_value("2√5/5 a", "2a√5/5") and same_value("V = 2√6a³", "2a³√6")
    assert same_value("60°", "60") and same_value("a³√2/3", "√2a³/3") and same_value("√3/3", "1/√3") is not False
    assert same_value("cos²=3/4", "30°") is True and same_value("cos²=3/4", "60°") is False and same_value("cos²=1/4", "1/2") is None
    assert same_value("a√6/3", "a√6/6") is False and same_value("1/2", "30°") is False and numeric("0,5 dm³", 1.0) == 0.5
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["transcription", "local", "api", "summarize", "backlog"])
    parser.add_argument("--partition", default="development")
    args = parser.parse_args()
    {"transcription": transcription, "summarize": summarize, "backlog": backlog}.get(args.mode, lambda: {"local": local, "api": api}[args.mode](args.partition))()
