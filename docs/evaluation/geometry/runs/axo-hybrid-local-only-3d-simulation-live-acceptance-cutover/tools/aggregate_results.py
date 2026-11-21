"""Aggregates raw evidence of this run into the result JSONs (no measurement happens here).

usage: python aggregate_results.py   (run from the run directory)
"""

import csv
import json
import math
from pathlib import Path

EV = Path("evidence")
man = json.loads(Path("LIVE_SIMULATION_ACCEPTANCE_MANIFEST.json").read_text(encoding="utf-8"))
CASES = {c["case_id"]: c for c in man["valid_cases"] + man["negative_cases"]}
jl = lambda p: [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def rate(k, n):
    return {"k": k, "n": n, "rate": round(k / n, 4) if n else None, "wilson95": wilson(k, n)}


def pct(xs, q):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    i = (len(xs) - 1) * q; lo = math.floor(i)
    return round(xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (i - lo), 1)


def dist(xs):
    xs = [x for x in xs if x is not None]
    return {"n": len(xs), "p50": pct(xs, .5), "p95": pct(xs, .95), "max": max(xs) if xs else None}


def score(tag, val_path):
    recs = {r["case_id"]: r for r in jl(EV / "browser" / f"browser_records_{tag}.jsonl")}
    val = {r["case_id"]: r for r in json.loads((EV / val_path).read_text(encoding="utf-8"))["results"]}
    rows = []
    for cid, c in CASES.items():
        r, v = recs.get(cid, {}), val.get(cid, {})
        served = r.get("route_status") == "SERVED" and r.get("surface") == "SCENE"
        lab = r.get("labels") or {}
        visual_ok = served and (r.get("canvas_pixels") or {}).get("ink_fraction", 0) >= 0.01 and not lab.get("gold_missing") \
            and not lab.get("outside_canvas") and not r.get("console_errors")
        inter = {"orbit": bool((r.get("orbit") or {}).get("frame_changed")) and (r.get("orbit") or {}).get("label_ids_stable", False),
                 "zoom": bool((r.get("zoom") or {}).get("frame_changed")),
                 "step": bool((r.get("step") or {}).get("after_prev")) and (r.get("step") or {}).get("after_next") == (r.get("step") or {}).get("initial"),
                 "no_reanalysis": r.get("analyze_calls_during_interaction") == 0} if served else None
        infra = r.get("http") in (502, 503, 504) or r.get("harness_error") is not None
        if c["simulation_intent"] == "NEGATIVE":
            verdict = "SAFE_REFUSAL" if not served else ("SERVED_CORRECT" if v.get("scene_validation") == "MATHEMATICALLY_VALID"
                                                         and (v.get("numeric") or {}).get("status", "CORRECT") == "CORRECT" else "UNSAFE_SERVE")
        elif served:
            ok_math = v.get("scene_validation") == "MATHEMATICALLY_VALID" and (v.get("numeric") or {}).get("status", "CORRECT") == "CORRECT"
            verdict = ("MATHEMATICALLY_CORRECT_VISUALLY_CORRECT" if ok_math and visual_ok else
                       "MATHEMATICALLY_CORRECT_VISUALLY_BROKEN" if ok_math else "MATHEMATICALLY_INVALID")
        else:
            verdict = "INFRASTRUCTURE_FAILURE" if infra else "SAFE_REFUSAL_OF_VALID_INPUT"
        rows.append({"case_id": cid, "intent": c["simulation_intent"], "family": c["geometric_family"], "pass": tag,
                     "http": r.get("http"), "route_status": r.get("route_status"), "surface": r.get("surface"),
                     "extraction_mode": r.get("extraction_mode"), "refusal_code": r.get("refusal_code"), "ux_state": r.get("ux_state"),
                     "scene_validation": v.get("scene_validation"), "oracle_issues": v.get("issues"), "oracle_findings": v.get("findings"),
                     "numeric": v.get("numeric"), "visual_ok": visual_ok if served else None, "interaction": inter,
                     "labels": lab or None, "canvas_ink_fraction": (r.get("canvas_pixels") or {}).get("ink_fraction"),
                     "backend_total_ms": r.get("backend_total_ms"), "http_round_trip_ms": r.get("http_round_trip_ms"),
                     "first_visible_scene_ms": r.get("first_visible_scene_ms"), "first_interactive_frame_ms": r.get("first_interactive_frame_ms"),
                     "console_errors": r.get("console_errors"), "external_requests": r.get("external_requests"),
                     "ui_token_leak": r.get("ui_token_leak"), "cloud_key_text": r.get("cloud_key_text"),
                     "learner_text": r.get("learner_text"), "screenshot": r.get("screenshot"), "response_sha256": r.get("response_sha256"),
                     "harness_error": r.get("harness_error"), "verdict": verdict})
    return rows


def rates(rows):
    valid = [r for r in rows if r["intent"] != "NEGATIVE"]
    neg = [r for r in rows if r["intent"] == "NEGATIVE"]
    served = [r for r in valid if r["route_status"] == "SERVED" and r["surface"] == "SCENE"]
    served_all = served + [r for r in neg if r["route_status"] == "SERVED"]
    inter_ops = [ok for r in served for ok in (r["interaction"] or {}).values()]
    numeric = [r for r in served if r["numeric"]]
    by_intent = {k: rate(sum(r["route_status"] == "SERVED" for r in valid if r["intent"] == k), sum(r["intent"] == k for r in valid))
                 for k in ("SIMULATE_ONLY", "SIMULATE_AND_QUERY", "QUERY_WITH_SCENE")}
    by_route = {}
    for r in valid:
        m = (r["extraction_mode"] or "NONE").split("_")[1] if r["extraction_mode"] else "NO_ROUTE"
        b = by_route.setdefault(m, [0, 0]); b[1] += 1; b[0] += r["route_status"] == "SERVED"
    return {"simulation_completion_rate": rate(len(served), len(valid)), "completion_by_intent": by_intent,
            "completion_by_extraction_route": {k: rate(*v) for k, v in by_route.items()},
            "geometry_correctness_rate": rate(sum(r["scene_validation"] == "MATHEMATICALLY_VALID" for r in served_all), len(served_all)),
            "visual_rendering_success_rate": rate(sum(bool(r["visual_ok"]) for r in served), len(served)),
            "interaction_success_rate": rate(sum(inter_ops), len(inter_ops)),
            "safe_refusal_rate": rate(sum(r["verdict"] in ("SAFE_REFUSAL", "SERVED_CORRECT") for r in neg), len(neg)),
            "numeric_answer_accuracy": rate(sum(r["numeric"]["status"] == "CORRECT" for r in numeric), len(numeric)),
            "infrastructure_failures": sum(r["verdict"] == "INFRASTRUCTURE_FAILURE" for r in valid + neg),
            "external_requests": sum(len(r["external_requests"] or []) for r in rows),
            "ui_token_leaks": sum(bool(r["ui_token_leak"]) for r in rows), "cloud_key_text": sum(bool(r["cloud_key_text"]) for r in rows),
            "console_errors_on_served": sum(len(r["console_errors"] or []) for r in served),
            "verdicts": {v: sum(r["verdict"] == v for r in rows) for v in sorted({r["verdict"] for r in rows})}}


def perf(rows):
    served = [r for r in rows if r["route_status"] == "SERVED"]
    slm = [r for r in rows if (r["extraction_mode"] or "").startswith("LOCAL_SLM")]
    det = [r for r in rows if r["extraction_mode"] == "LOCAL_DETERMINISTIC_PARSER"]
    return {"served_scenes": {k: dist([r[k] for r in served]) for k in
                              ("backend_total_ms", "http_round_trip_ms", "first_visible_scene_ms", "first_interactive_frame_ms")},
            "deterministic_route_backend_ms": dist([r["backend_total_ms"] for r in det]),
            "slm_route_backend_ms": dist([r["backend_total_ms"] for r in slm]),
            "slm_route_round_trip_ms": dist([r["http_round_trip_ms"] for r in slm]),
            "all_requests_round_trip_ms": dist([r["http_round_trip_ms"] for r in rows])}


def resource_stats(p):
    """cpu_mem_pass2.csv was written with PowerShell N0 (thousands separator ','), so a row is
    t, cpu%, available_MB thousands, available_MB units, llama_ws_MB  (5 fields; available >= 1000 MB on this host).
    Rows with another field count are reported as unparsed, not guessed."""
    if not Path(p).exists():
        return "NOT_MEASURED"
    rows = list(csv.reader(open(p, encoding="utf-8")))
    ok = [r for r in rows if len(r) == 5]
    cpu = [float(r[1]) for r in ok]; avail = [int(r[2]) * 1000 + int(r[3]) for r in ok]; llama = [int(r[4]) for r in ok]
    llama_up = [x for x in llama if x > 50]
    st = lambda xs: {"mean": round(sum(xs) / len(xs), 1), "p95": pct(xs, .95), "max": max(xs), "min": min(xs)} if xs else None
    return {"samples": len(ok), "unparsed_rows": len(rows) - len(ok), "interval_s": 2,
            "cpu_total_pct": st(cpu), "available_ram_mb": st(avail), "llama_server_ws_mb_while_loaded": st(llama_up),
            "not_measured": ["backend python RSS", "Chromium/renderer RSS", "WebGL memory", "page faults"]}


def sampler(p):
    if not Path(p).exists():
        return "NOT_MEASURED"
    rows = jl(p)
    hb = [r for r in rows if r.get("heartbeat")]
    span = (hb[-1]["t"] - hb[0]["t"]) / 1000 if len(hb) > 1 else 0
    return {"heartbeats": len(hb), "span_s": round(span, 1), "mean_interval_s": round(span / max(1, len(hb) - 1), 2),
            "non_loopback_records": sum("remote" in r for r in rows)}


if __name__ == "__main__":
    p1, p2 = score("acceptance", "scene_validation_pass1_oracle_v2.json"), score("pass2", "scene_validation_pass2.json")
    egress = {f: (len(jl(EV / f)) if (EV / f).exists() else "MISSING") for f in
              ("egress_proxy_selfcheck.jsonl", "egress_proxy_acceptance.jsonl", "egress_proxy_pass2.jsonl")}
    results = {
        "schema": "axo-live-simulation-acceptance-results/1",
        "manifest_sha256": json.loads(Path("ACCEPTANCE_FREEZE.json").read_text(encoding="utf-8"))["manifest"]["sha256"],
        "passes": {
            "pass1": {"candidate_backend_tree": "a7a6bc4157d02018d5a67e5ee408469f22795385f920444eafc39d4772fa8330", "commit": "451a59040",
                      "blind": True, "oracle": "v1 output kept (evidence/scene_validation_acceptance.json); re-scored with v2",
                      "rates": rates(p1), "performance": perf(p1)},
            "pass2": {"candidate_backend_tree": "ce3e3c4b5cc9e075bc260f50e64dc5647408d1a3a614db67bd6d17a3b1d1eb6a", "commit": "a0f979392",
                      "blind": False, "note": "same frozen manifest re-run after the keep-alive fix; the author had seen pass-1 results",
                      "rates": rates(p2), "performance": perf(p2)}},
        "network": {"egress_proxy_records": egress, "tcp_sampler_pass1": sampler(EV / "tcp_sampler_acceptance.jsonl"),
                    "tcp_sampler_pass2": sampler(EV / "tcp_sampler_pass2.jsonl"),
                    "tcp_sampler_witness_v1": sampler(EV / "tcp_sampler_witness.jsonl"), "tcp_sampler_witness_v2": sampler(EV / "tcp_sampler_v2_witness.jsonl")},
        "resources_pass2": resource_stats(EV / "cpu_mem_pass2.csv"),
        "cases": {"pass1": p1, "pass2": p2},
    }
    Path("LIVE_SIMULATION_ACCEPTANCE_RESULTS.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v["rates"] for k, v in results["passes"].items()}, ensure_ascii=False, indent=1)[:4000])
    print(json.dumps({k: v["performance"] for k, v in results["passes"].items()}, ensure_ascii=False)[:2000])
    print(json.dumps({"network": results["network"], "resources": results["resources_pass2"]}, ensure_ascii=False))
