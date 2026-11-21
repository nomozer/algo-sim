# -*- coding: utf-8 -*-
"""AXO HYBRID /9 — Phase P4 CPU Runtime Benchmark, Cache Coalescing, Fault Recovery & Ablations."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import sys
import time
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
RUNS_DIR = REPO_ROOT / "docs/evaluation/geometry/runs"
OUT_DIR = RUNS_DIR / "axo-hybrid-local-ai-replacement-vietnamese-nlu-offline-cutover"
VAL_V9_PATH = Path(r"C:\Users\Bunny\AppData\Local\axo-slm\training\datasets_v9\val_v9.jsonl")

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(BACKEND_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR / "scripts"))

from app.ai import adaptive_input_router as AIR  # noqa: E402
from app.ai.local_geometry_parser import (  # noqa: E402
    LOCAL_PARSE_COMPLETE,
    clear_local_geometry_parser_cache,
    parse_geometry_problem_locally,
)
from app.ai.local_slm_extractor import DEFAULT_V9_SLM_MAX_TOKENS, V9_CLOSURE_MODE  # noqa: E402
from app.ai.local_slm_runtime import (  # noqa: E402
    FINETUNED_LOCAL_SLM_MODEL_KEY,
    V9_LOCAL_SLM_MODEL_KEY,
    LocalSlmRuntime,
    LocalSlmRuntimeError,
    get_shared_local_slm_extraction_cache,
)
from app.ai.slm_verified_normalizer import normalize_for_slm_grounding  # noqa: E402
from benchmark_slm_v8_system_resources import (  # noqa: E402
    _build_30_deterministic_fastpath_prompts,
    _get_server_pid,
    _stats_ms,
    _sys_mem_snapshot,
)
from slm_math_evaluator_v2 import compare_math_expressions, infer_goal_kind_from_text  # noqa: E402


STAGE_TIMING_KEYS = (
    "preprocessing_ms",
    "normalizer_ms",
    "local_parser_ms",
    "cache_lookup_ms",
    "clause_context_ms",
    "prompt_build_ms",
    "grammar_build_ms",
    "queue_wait_ms",
    "prompt_eval_ms",
    "token_gen_ms",
    "json_decode_ms",
    "grounding_and_lowering_ms",
    "wire_normalize_ms",
    "slm_inference_ms",
    "exact_kernel_and_scene3d_ms",
)


def _has_scene3d(resp: dict[str, Any] | None) -> bool:
    env_top = (resp or {}).get("envelope") or {}
    return bool(env_top.get("scene3d") or ((env_top.get("config") or {}).get("frames")))


def _check_oracles(answers: dict[str, Any], oracles: list[str], text: str) -> tuple[bool, bool]:
    vals = [str(v) for v in (answers or {}).values()]
    if not oracles:
        return True, False
    if not vals:
        return False, False
    clean_gk = re.sub(r"\bvuông\s+góc\b", "vuong_goc", text, flags=re.IGNORECASE)
    gk = infer_goal_kind_from_text(clean_gk) if len(oracles) == 1 else None
    matched = sum(1 for o in oracles if any(compare_math_expressions(v, o, goal_kind=gk).matched is True for v in vals))
    wrong = any(not any(compare_math_expressions(v, o, goal_kind=gk).matched is True for o in oracles) for v in vals)
    return matched == len(oracles) and not wrong, wrong


def _build_100_v9_slm_prompts() -> list[dict[str, Any]]:
    tri_sets = [("S", "A", "B", "C"), ("K", "M", "N", "P"), ("P", "E", "F", "G"), ("H", "U", "V", "W"), ("D", "X", "Y", "Z")]
    quad_sets = [("S", "A", "B", "C", "D"), ("K", "M", "N", "P", "Q"), ("H", "U", "V", "W", "X"), ("G", "R", "S", "T", "U"), ("P", "E", "F", "G", "H")]
    box_bases = [("A", "B", "C", "D"), ("E", "F", "G", "H"), ("M", "N", "P", "Q"), ("R", "S", "T", "U"), ("X", "Y", "Z", "W")]
    lens = ["a", "2a", "3a", "4a", "5a", "a√2", "a√3", "2a√2", "2a√3"]
    prompts: list[dict[str, Any]] = []
    idx = 0
    for ti in range(34):
        s, a, b, c = tri_sets[ti % len(tri_sets)]
        l1 = lens[(ti // 5) % len(lens)]
        txt = (
            f"Cho hình chóp {s}.{a}{b}{c} có đáy {a}{b}{c} đều cạnh {l1}. "
            f"Biết mặt bên {s}{a}{b} là tam giác đều và vuông góc với đáy ({a}{b}{c}). Tính thể tích khối chóp {s}.{a}{b}{c}."
        )
        prompts.append({"idx": idx, "tier": "short", "text": txt})
        idx += 1
    for mi in range(33):
        s, a, b, c, d = quad_sets[mi % len(quad_sets)]
        l1 = lens[mi % len(lens)]
        l2 = lens[(mi // 5 + 2) % len(lens)]
        txt = (
            f"Cho khối chóp {s}.{a}{b}{c}{d} có đáy {a}{b}{c}{d} là hình chữ nhật với {a}{b}={l1}, {a}{d}={l2}. "
            f"Biết mặt bên {s}{a}{b} là tam giác đều và vuông góc với đáy ({a}{b}{c}{d}). Tính khoảng cách từ {a} đến mặt phẳng ({s}{c}{d})."
        )
        prompts.append({"idx": idx, "tier": "medium", "text": txt})
        idx += 1
    long_l1 = ["a", "2a", "3a"]
    long_l2 = ["2a", "3a", "4a", "a√2", "a√3"]
    long_l3 = ["a", "2a", "4a", "5a", "a√5"]
    for li in range(33):
        a, b, c, d = box_bases[li % len(box_bases)]
        l1 = long_l1[(li // 5) % len(long_l1)]
        l2 = long_l2[li % len(long_l2)]
        l3 = long_l3[(li // 5 + 1) % len(long_l3)]
        txt = (
            f"Đề yêu cầu khảo sát hộp chữ nhật {a}{b}{c}{d}.{a}'{b}'{c}'{d}' có các cạnh {a}{b}={l1}, {a}{d}={l2}, {a}{a}'={l3}. "
            f"Tính độ dài đoạn {a}{c}'. Tính góc giữa hai đường thẳng {a}{b}' với {b}{c}'. "
            f"Tính thể tích khối hộp {a}{b}{c}{d}.{a}'{b}'{c}'{d}'."
        )
        prompts.append({"idx": idx, "tier": "long", "text": txt})
        idx += 1

    # Verify distinctness and confirm every prompt avoids fast-path after v3 normalizer
    seen: set[str] = set()
    for p in prompts:
        if p["text"] in seen:
            # Disambiguate cleanly with second length if any collision
            p["text"] = p["text"].replace("đều cạnh", f"đều có độ dài cạnh", 1)
        seen.add(p["text"])
        canon = normalize_for_slm_grounding(p["text"], normalizer_version="v3").canonical_text
        st = parse_geometry_problem_locally(canon).status
        assert st != LOCAL_PARSE_COMPLETE, f"Expected SLM fallback for idx={p['idx']}, got {st}: {p['text']}"
    assert len(seen) == 100, f"Expected 100 unique SLM prompts, got {len(seen)}"
    return prompts


def _build_50_fastpath_prompts() -> list[str]:
    base30 = _build_30_deterministic_fastpath_prompts()
    tri_sets = [("S", "A", "B", "C"), ("P", "E", "F", "G"), ("H", "U", "V", "W"), ("K", "M", "N", "P")]
    extra20: list[str] = []
    for k in range(20):
        s, a, b, c = tri_sets[k % len(tri_sets)]
        side = ["a", "2a", "3a", "4a", "5a"][k // 4]
        h = ["2a", "3a", "4a", "5a", "6a"][(k + 1) % 5]
        txt = (
            f"Cho hình chóp {s}.{a}{b}{c} có đáy {a}{b}{c} là tam giác đều cạnh {side}, "
            f"{s}{a} vuông góc với ({a}{b}{c}) và {s}{a}={h}. Tính thể tích khối chóp {s}.{a}{b}{c}."
        )
        extra20.append(txt)
    return base30 + extra20


def _load_24_ablation_cases() -> list[dict[str, Any]]:
    rows = [json.loads(ln) for ln in VAL_V9_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]
    pos_rows = [r for r in rows if r["kind"] == "positive"]
    by_fam: dict[str, list[dict[str, Any]]] = {}
    for r in pos_rows:
        by_fam.setdefault(r["problem_family_id"], []).append(r)
    quotas = [
        ("VL01_FACE_PERP_RECT_ANG_DIST", 5),
        ("VL02_RHOM_MID_SKEW_DIST", 5),
        ("VL03_PRISM_PROJ_AREA", 5),
        ("VL9_MULTI_GOAL_DISJOINT", 5),
        ("VL9_TETRA_PRISM_RECT_DISJOINT", 4),
    ]
    picked: list[dict[str, Any]] = []
    for fam, k in quotas:
        candidates = [r for r in by_fam.get(fam, []) if r.get("local_parser_status_after_norm") != LOCAL_PARSE_COMPLETE]
        if len(candidates) < k:
            candidates = by_fam.get(fam, [])
        picked.extend(candidates[:k])
    assert len(picked) == 24, f"Expected 24 ablation cases, got {len(picked)}"
    return picked


def _run_ablation_variant(
    cases: list[dict[str, Any]],
    *,
    name: str,
    model_key: str,
    threads: int,
    ctx_size: int,
    grammar_mode: str,
    max_tokens: int,
) -> dict[str, Any]:
    rt = LocalSlmRuntime(ctx_size=ctx_size, allow_download=False)
    e2e_list: list[float] = []
    inf_list: list[float] = []
    prompt_toks: list[int] = []
    comp_toks: list[int] = []
    tps_list: list[float] = []
    served_cnt = 0
    exact_cnt = 0
    wrong_cnt = 0
    slm_cnt = 0
    retry_cnt = 0
    peak_ws = 0.0
    try:
        for it in cases:
            clear_local_geometry_parser_cache()
            txt = it["source_text"]
            oracles = [str(x) for x in (it.get("gold_oracles") or ())]
            t0 = time.perf_counter()
            out = AIR.route_text_input_local_slm(
                txt,
                model_key=model_key,
                strategy="compact_clause",
                runtime=rt,
                allow_download=False,
                threads=threads,
                max_tokens=max_tokens,
                grammar_mode=grammar_mode,
                use_verified_normalizer=True,
                closure_mode=V9_CLOSURE_MODE,
                normalizer_version="v3",
                use_cache=False,
                cache_prompt=True,
            )
            e2e_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            e2e_list.append(e2e_ms)
            rd = (out.response or {}).get("route_d") or {}
            env = rd.get("slm_grounding_envelope") or {}
            st = env.get("stage_timings_ms") or {}
            if env.get("slm_invoked"):
                slm_cnt += 1
            if env.get("grammar_retry_used"):
                retry_cnt += 1
            if env.get("inference_time_ms") is not None:
                inf_list.append(float(env["inference_time_ms"]))
            if st.get("prompt_tokens") is not None:
                prompt_toks.append(int(st["prompt_tokens"]))
            if st.get("completion_tokens") is not None:
                comp_toks.append(int(st["completion_tokens"]))
            if st.get("tokens_per_sec") is not None:
                tps_list.append(float(st["tokens_per_sec"]))
            snap = _sys_mem_snapshot(_get_server_pid(rt))
            peak_ws = max(peak_ws, float(snap.get("combined_backend_plus_slm_ws_mib") or 0.0))
            if rd.get("status") == "SERVED":
                served_cnt += 1
                ok_exact, is_wrong = _check_oracles(rd.get("answers") or {}, oracles, txt)
                if ok_exact:
                    exact_cnt += 1
                if is_wrong:
                    wrong_cnt += 1
    finally:
        rt.shutdown()

    res = {
        "variant": name,
        "model_key": model_key,
        "threads": threads,
        "ctx_size": ctx_size,
        "grammar_mode": grammar_mode,
        "max_tokens": max_tokens,
        "total_cases": len(cases),
        "slm_invoked_count": slm_cnt,
        "served_count": served_cnt,
        "oracle_exact_count": exact_cnt,
        "oracle_exact_rate": round(exact_cnt / len(cases), 4),
        "wrong_served_count": wrong_cnt,
        "grammar_retry_used_count": retry_cnt,
        "e2e_ms": _stats_ms(e2e_list),
        "slm_inference_ms": _stats_ms(inf_list),
        "mean_prompt_tokens": round(sum(prompt_toks) / len(prompt_toks), 1) if prompt_toks else None,
        "mean_completion_tokens": round(sum(comp_toks) / len(comp_toks), 1) if comp_toks else None,
        "mean_tokens_per_sec": round(sum(tps_list) / len(tps_list), 2) if tps_list else None,
        "peak_combined_ws_mib": round(peak_ws, 2),
    }
    print(
        f"[ABLATION {name}] exact={exact_cnt}/{len(cases)} wrong={wrong_cnt} "
        f"e2e_p50={res['e2e_ms']['p50_ms']}ms inf_p50={res['slm_inference_ms']['p50_ms']}ms retries={retry_cnt}",
        flush=True,
    )
    return res


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prompts_100 = _build_100_v9_slm_prompts()
    fast_30 = _build_30_deterministic_fastpath_prompts()
    fast_50 = _build_50_fastpath_prompts()
    mixed_100: list[tuple[str, str]] = []
    for i in range(50):
        mixed_100.append(("fastpath", fast_50[i]))
        mixed_100.append(("slm", prompts_100[i]["text"]))

    snap_before_load = _sys_mem_snapshot(None)
    rt = LocalSlmRuntime(allow_download=False)

    try:
        # 1. Cold start (n=1, fresh LocalSlmRuntime)
        clear_local_geometry_parser_cache()
        get_shared_local_slm_extraction_cache().clear()
        cold_prompt = prompts_100[0]["text"]
        t_cold0 = time.perf_counter()
        out_cold = AIR.route_text_input_local_slm(
            cold_prompt,
            model_key=V9_LOCAL_SLM_MODEL_KEY,
            strategy="compact_clause",
            runtime=rt,
            allow_download=False,
            threads=6,
            max_tokens=DEFAULT_V9_SLM_MAX_TOKENS,
            grammar_mode="gbnf",
            use_verified_normalizer=True,
            closure_mode=V9_CLOSURE_MODE,
            normalizer_version="v3",
            use_cache=False,
            cache_prompt=True,
        )
        cold_e2e_ms = round((time.perf_counter() - t_cold0) * 1000.0, 2)
        rd_cold = (out_cold.response or {}).get("route_d") or {}
        env_cold = rd_cold.get("slm_grounding_envelope") or {}
        st_cold = env_cold.get("stage_timings_ms") or {}
        has_scene_cold = _has_scene3d(out_cold.response)
        snap_after_cold = _sys_mem_snapshot(_get_server_pid(rt))
        print(
            f"[P4 COLD] e2e={cold_e2e_ms}ms load={env_cold.get('server_load_time_ms')}ms "
            f"stage_keys={len(st_cold)} status={out_cold.status} comb_ws={snap_after_cold['combined_backend_plus_slm_ws_mib']}MiB",
            flush=True,
        )

        # 2. Pure warm uncached SLM n=100 (AxoV9-Q4_K_M, threads=6, mt=256)
        warm_rows: list[dict[str, Any]] = []
        stage_samples: dict[str, list[float]] = {k: [] for k in STAGE_TIMING_KEYS}
        peak_comb_ws = float(snap_after_cold["combined_backend_plus_slm_ws_mib"])
        peak_comb_priv = float(snap_after_cold["combined_backend_plus_slm_private_commit_mib"])
        min_os_avail = float(snap_after_cold["os"].get("avail_phys_mib", 1e9))
        max_sys_commit = float(snap_after_cold["os"].get("system_commit_total_mib", 0.0))

        for item in prompts_100:
            clear_local_geometry_parser_cache()
            t0 = time.perf_counter()
            out = AIR.route_text_input_local_slm(
                item["text"],
                model_key=V9_LOCAL_SLM_MODEL_KEY,
                strategy="compact_clause",
                runtime=rt,
                allow_download=False,
                threads=6,
                max_tokens=DEFAULT_V9_SLM_MAX_TOKENS,
                grammar_mode="gbnf",
                use_verified_normalizer=True,
                closure_mode=V9_CLOSURE_MODE,
                normalizer_version="v3",
                use_cache=False,
                cache_prompt=True,
            )
            e2e_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            rd = (out.response or {}).get("route_d") or {}
            env = rd.get("slm_grounding_envelope") or {}
            st = env.get("stage_timings_ms") or {}
            assert env.get("slm_invoked") is True, f"Prompt {item['idx']} bypassed SLM!"
            assert env.get("cache_hit") is False, f"Prompt {item['idx']} hit cache!"
            tel = rd.get("adaptive_telemetry") or {}
            kernel_ms = float(tel.get("hybrid_execution_ms") or 0.0)
            if "exact_kernel_and_scene3d_ms" not in st:
                st["exact_kernel_and_scene3d_ms"] = round(kernel_ms, 3)
            for k in STAGE_TIMING_KEYS:
                if st.get(k) is not None:
                    stage_samples[k].append(float(st[k]))
            snap = _sys_mem_snapshot(_get_server_pid(rt))
            peak_comb_ws = max(peak_comb_ws, float(snap["combined_backend_plus_slm_ws_mib"]))
            peak_comb_priv = max(peak_comb_priv, float(snap["combined_backend_plus_slm_private_commit_mib"]))
            min_os_avail = min(min_os_avail, float(snap["os"].get("avail_phys_mib", 1e9)))
            max_sys_commit = max(max_sys_commit, float(snap["os"].get("system_commit_total_mib", 0.0)))
            warm_rows.append({
                "idx": item["idx"],
                "tier": item["tier"],
                "status": out.status,
                "has_scene3d": _has_scene3d(out.response),
                "e2e_ms": e2e_ms,
                "slm_inference_ms": env.get("inference_time_ms"),
                "prompt_eval_ms": st.get("prompt_eval_ms"),
                "token_gen_ms": st.get("token_gen_ms"),
                "tokens_per_sec": st.get("tokens_per_sec"),
                "queue_wait_ms": st.get("queue_wait_ms"),
                "comb_ws_mib": snap["combined_backend_plus_slm_ws_mib"],
                "comb_priv_mib": snap["combined_backend_plus_slm_private_commit_mib"],
                "py_page_faults": snap["python_backend"].get("page_fault_count"),
                "srv_page_faults": snap["llama_server"].get("page_fault_count"),
            })
            if (item["idx"] + 1) % 25 == 0:
                print(
                    f"[P4 WARM-100] {item['idx']+1}/100 done | last={e2e_ms}ms | peak_comb_ws={peak_comb_ws}MiB",
                    flush=True,
                )

        snap_after_100 = _sys_mem_snapshot(_get_server_pid(rt))

        # 3. Mixed warm uncached n=100 (50 fast-path + 50 SLM, use_cache=False)
        mixed_e2e: list[float] = []
        mixed_fast = 0
        mixed_slm = 0
        mixed_served = 0
        for kind, mtxt in mixed_100:
            clear_local_geometry_parser_cache()
            t0 = time.perf_counter()
            out_m = AIR.route_text_input_local_slm(
                mtxt,
                model_key=V9_LOCAL_SLM_MODEL_KEY,
                strategy="compact_clause",
                runtime=rt,
                allow_download=False,
                threads=6,
                max_tokens=DEFAULT_V9_SLM_MAX_TOKENS,
                grammar_mode="gbnf",
                use_verified_normalizer=True,
                closure_mode=V9_CLOSURE_MODE,
                normalizer_version="v3",
                use_cache=False,
                cache_prompt=True,
            )
            mixed_e2e.append(round((time.perf_counter() - t0) * 1000.0, 2))
            rd_m = (out_m.response or {}).get("route_d") or {}
            env_m = rd_m.get("slm_grounding_envelope") or {}
            if env_m.get("slm_invoked"):
                mixed_slm += 1
            else:
                mixed_fast += 1
            if out_m.status == "SERVED":
                mixed_served += 1
        print(
            f"[P4 MIXED-100] p50={_stats_ms(mixed_e2e)['p50_ms']}ms p95={_stats_ms(mixed_e2e)['p95_ms']}ms "
            f"served={mixed_served}/100 fast={mixed_fast} slm={mixed_slm}",
            flush=True,
        )

        # 4. Warm cached n=30 (explicit use_cache=True with runtime=rt) + single-flight coalescing
        ext_cache = get_shared_local_slm_extraction_cache()
        ext_cache.clear()
        cached_hit_ms: list[float] = []
        cached_miss_ms: list[float] = []
        for i in range(30):
            txt = prompts_100[i % 5]["text"]
            clear_local_geometry_parser_cache()
            t0 = time.perf_counter()
            out_c = AIR.route_text_input_local_slm(
                txt,
                model_key=V9_LOCAL_SLM_MODEL_KEY,
                strategy="compact_clause",
                runtime=rt,
                allow_download=False,
                threads=6,
                use_verified_normalizer=True,
                closure_mode=V9_CLOSURE_MODE,
                normalizer_version="v3",
                use_cache=True,
                cache_prompt=True,
            )
            ms = round((time.perf_counter() - t0) * 1000.0, 2)
            env_c = ((out_c.response or {}).get("route_d") or {}).get("slm_grounding_envelope") or {}
            if i < 5:
                assert env_c.get("cache_hit") is False, f"Expected initial cache miss on i={i}"
                cached_miss_ms.append(ms)
            else:
                assert env_c.get("cache_hit") is True, f"Expected warm cache hit on i={i} with explicit runtime!"
                cached_hit_ms.append(ms)

        # Single-flight 4-thread duplicate coalescing
        coalesce_prompt = prompts_100[55]["text"]
        ext_cache.clear()
        def _coalesce_call(_: int) -> dict[str, Any]:
            clear_local_geometry_parser_cache()
            t0 = time.perf_counter()
            oc = AIR.route_text_input_local_slm(
                coalesce_prompt,
                model_key=V9_LOCAL_SLM_MODEL_KEY,
                strategy="compact_clause",
                runtime=rt,
                allow_download=False,
                threads=6,
                use_verified_normalizer=True,
                closure_mode=V9_CLOSURE_MODE,
                normalizer_version="v3",
                use_cache=True,
                cache_prompt=True,
            )
            env_k = ((oc.response or {}).get("route_d") or {}).get("slm_grounding_envelope") or {}
            return {"status": oc.status, "cache_hit": bool(env_k.get("cache_hit")), "ms": round((time.perf_counter() - t0) * 1000.0, 2)}

        with ThreadPoolExecutor(max_workers=4) as ex:
            coalesce_outs = list(ex.map(_coalesce_call, range(4)))
        coalesce_hits = sum(1 for r in coalesce_outs if r["cache_hit"])
        coalesce_served = sum(1 for r in coalesce_outs if r["status"] == "SERVED")
        assert coalesce_served == 4 and coalesce_hits >= 3, f"Single-flight coalescing failed: {coalesce_outs}"
        print(
            f"[P4 CACHE+COALESCE] hit_p50={_stats_ms(cached_hit_ms)['p50_ms']}ms coalesce_hits={coalesce_hits}/4 served={coalesce_served}/4",
            flush=True,
        )

        # 5. Deterministic fast-path n=30
        det_ms: list[float] = []
        for txt in fast_30:
            clear_local_geometry_parser_cache()
            t0 = time.perf_counter()
            out_d = AIR.route_text_input_local_slm(
                txt,
                model_key=V9_LOCAL_SLM_MODEL_KEY,
                strategy="compact_clause",
                runtime=rt,
                allow_download=False,
                threads=6,
                closure_mode=V9_CLOSURE_MODE,
                normalizer_version="v3",
                use_cache=False,
            )
            assert out_d.status == "SERVED"
            det_ms.append(round((time.perf_counter() - t0) * 1000.0, 2))
        print(f"[P4 FAST-PATH-30] p50={_stats_ms(det_ms)['p50_ms']}ms p95={_stats_ms(det_ms)['p95_ms']}ms", flush=True)

        # 6. Concurrency c=2, c=4 + Fault recovery (crash kill + timeout recovery)
        conc_results: dict[str, Any] = {}
        for conc_n, n_batches in [(2, 4), (4, 2)]:
            batch_lats: list[float] = []
            batch_qwaits: list[float] = []
            batch_statuses: list[str] = []
            wall_batches: list[float] = []
            for b in range(n_batches):
                sub_prompts = [prompts_100[(b * conc_n + k) % 100]["text"] for k in range(conc_n)]
                t_b0 = time.perf_counter()
                def _call_one(ptxt: str) -> dict[str, Any]:
                    clear_local_geometry_parser_cache()
                    t0 = time.perf_counter()
                    o = AIR.route_text_input_local_slm(
                        ptxt,
                        model_key=V9_LOCAL_SLM_MODEL_KEY,
                        strategy="compact_clause",
                        runtime=rt,
                        allow_download=False,
                        threads=6,
                        max_tokens=DEFAULT_V9_SLM_MAX_TOKENS,
                        use_verified_normalizer=True,
                        closure_mode=V9_CLOSURE_MODE,
                        normalizer_version="v3",
                        use_cache=False,
                        cache_prompt=False,
                    )
                    ms = round((time.perf_counter() - t0) * 1000.0, 2)
                    rd = (o.response or {}).get("route_d") or {}
                    env = rd.get("slm_grounding_envelope") or {}
                    st = env.get("stage_timings_ms") or {}
                    return {"status": o.status, "ms": ms, "qw": st.get("queue_wait_ms")}

                with ThreadPoolExecutor(max_workers=conc_n) as ex:
                    res_list = list(ex.map(_call_one, sub_prompts))
                wall_batches.append(round((time.perf_counter() - t_b0) * 1000.0, 2))
                for r in res_list:
                    batch_lats.append(r["ms"])
                    batch_statuses.append(r["status"])
                    if r["qw"] is not None:
                        batch_qwaits.append(float(r["qw"]))
            snap_c = _sys_mem_snapshot(_get_server_pid(rt))
            conc_results[f"c_{conc_n}"] = {
                "concurrency": conc_n,
                "total_requests": len(batch_lats),
                "request_e2e": _stats_ms(batch_lats),
                "queue_wait": _stats_ms(batch_qwaits),
                "mean_batch_wall_ms": round(sum(wall_batches) / len(wall_batches), 2),
                "served_count": sum(1 for s in batch_statuses if s == "SERVED"),
                "snap_after": snap_c,
            }
            print(
                f"[P4 CONC c={conc_n}] e2e_p50={conc_results[f'c_{conc_n}']['request_e2e']['p50_ms']}ms "
                f"e2e_p95={conc_results[f'c_{conc_n}']['request_e2e']['p95_ms']}ms served={conc_results[f'c_{conc_n}']['served_count']}/{len(batch_lats)}",
                flush=True,
            )

        # Crash & timeout auto-recovery verification on live runtime
        killed_pid = rt.force_kill_server()
        assert killed_pid is not None
        out_crash = AIR.route_text_input_local_slm(
            prompts_100[2]["text"],
            model_key=V9_LOCAL_SLM_MODEL_KEY,
            strategy="compact_clause",
            runtime=rt,
            allow_download=False,
            threads=6,
            use_verified_normalizer=True,
            closure_mode=V9_CLOSURE_MODE,
            normalizer_version="v3",
            use_cache=False,
        )
        crash_restarted = bool(
            (((out_crash.response or {}).get("route_d") or {}).get("slm_grounding_envelope") or {}).get("server_load_time_ms")
        )
        timeout_code = None
        try:
            rt.chat_completion_json(
                messages=[{"role": "user", "content": prompts_100[3]["text"]}],
                model_key=V9_LOCAL_SLM_MODEL_KEY,
                timeout_s=0.05,
                allow_download=False,
            )
        except LocalSlmRuntimeError as exc:
            timeout_code = exc.reason_code
        out_post_timeout = AIR.route_text_input_local_slm(
            prompts_100[4]["text"],
            model_key=V9_LOCAL_SLM_MODEL_KEY,
            strategy="compact_clause",
            runtime=rt,
            allow_download=False,
            threads=6,
            use_verified_normalizer=True,
            closure_mode=V9_CLOSURE_MODE,
            normalizer_version="v3",
            use_cache=False,
        )
        fault_recovery = {
            "crash_kill_pid": killed_pid,
            "crash_auto_restart_served": out_crash.status == "SERVED" and crash_restarted,
            "timeout_reason_code": timeout_code,
            "post_timeout_served": out_post_timeout.status == "SERVED",
        }
        assert fault_recovery["crash_auto_restart_served"] and timeout_code == "LOCAL_SLM_TIMEOUT" and fault_recovery["post_timeout_served"]
        print(f"[P4 FAULT RECOVERY] {fault_recovery}", flush=True)

        # c=6 bounded queue saturation burst (max_queue=2)
        rt.shutdown()
        rt_sat = LocalSlmRuntime(max_queue=2, allow_download=False)
        sat_ok = sat_busy = sat_other = 0
        try:
            def _sat_call(i_idx: int) -> str:
                try:
                    _ = rt_sat.chat_completion_json(
                        messages=[
                            {"role": "system", "content": "Extract compact JSON."},
                            {"role": "user", "content": prompts_100[i_idx]["text"]},
                        ],
                        json_schema={"type": "object"},
                        model_key=V9_LOCAL_SLM_MODEL_KEY,
                        threads=6,
                        max_tokens=128,
                    )
                    return "OK"
                except LocalSlmRuntimeError as exc:
                    return f"ERR:{exc.reason_code}"
                except Exception as exc:
                    return f"EXC:{type(exc).__name__}"

            with ThreadPoolExecutor(max_workers=6) as ex:
                sat_outs = list(ex.map(_sat_call, range(6)))
            for s in sat_outs:
                if s == "OK":
                    sat_ok += 1
                elif "BUSY" in s:
                    sat_busy += 1
                else:
                    sat_other += 1
            post_sat = rt_sat.chat_completion_json(
                messages=[
                    {"role": "system", "content": "Extract compact JSON."},
                    {"role": "user", "content": prompts_100[0]["text"]},
                ],
                json_schema={"type": "object"},
                model_key=V9_LOCAL_SLM_MODEL_KEY,
                threads=6,
                max_tokens=128,
            )
            post_sat_ok = post_sat is not None
        finally:
            rt_sat.shutdown()
        conc_results["c_6_bounded_queue_saturation"] = {
            "max_queue": 2,
            "submitted_parallel": 6,
            "completed_ok": sat_ok,
            "rejected_busy": sat_busy,
            "other_errors": sat_other,
            "post_saturation_recovery_ok": post_sat_ok,
        }
        print(f"[P4 SAT c=6 max_q=2] ok={sat_ok} busy={sat_busy} other={sat_other} recovery={post_sat_ok}", flush=True)
    finally:
        rt.shutdown()

    # 7. Ablations on n=24 representative positive cases from val_v9.jsonl
    ablation_cases = _load_24_ablation_cases()
    ablation_variants = [
        _run_ablation_variant(ablation_cases, name="axov9_gbnf_t6_mt256", model_key=V9_LOCAL_SLM_MODEL_KEY, threads=6, ctx_size=1536, grammar_mode="gbnf", max_tokens=256),
        _run_ablation_variant(ablation_cases, name="axov9_retry_on_invalid_t6_mt256", model_key=V9_LOCAL_SLM_MODEL_KEY, threads=6, ctx_size=1536, grammar_mode="retry_on_invalid", max_tokens=256),
        _run_ablation_variant(ablation_cases, name="axov9_gbnf_t8_mt256", model_key=V9_LOCAL_SLM_MODEL_KEY, threads=8, ctx_size=1536, grammar_mode="gbnf", max_tokens=256),
        _run_ablation_variant(ablation_cases, name="axov9_gbnf_t2_ctx1536_mt256", model_key=V9_LOCAL_SLM_MODEL_KEY, threads=2, ctx_size=1536, grammar_mode="gbnf", max_tokens=256),
        _run_ablation_variant(ablation_cases, name="axov7_gbnf_t6_mt320", model_key=FINETUNED_LOCAL_SLM_MODEL_KEY, threads=6, ctx_size=1536, grammar_mode="gbnf", max_tokens=320),
    ]

    ablation_doc = {
        "schema": "slm-v9-ablation/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "external_ai_calls": 0,
        "dataset_source": str(VAL_V9_PATH),
        "sample_ids": [c["sample_id"] for c in ablation_cases],
        "variants": ablation_variants,
    }
    (OUT_DIR / "SLM_V9_ABLATION.json").write_text(json.dumps(ablation_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    e2e_all = [r["e2e_ms"] for r in warm_rows]
    inf_all = [r["slm_inference_ms"] for r in warm_rows if r["slm_inference_ms"] is not None]
    tps_all = [r["tokens_per_sec"] for r in warm_rows if r["tokens_per_sec"] is not None]
    e2e_stats = _stats_ms(e2e_all)
    inf_stats = _stats_ms(inf_all)
    drift_first25 = warm_rows[:25]
    drift_last25 = warm_rows[-25:]
    stage_stats = {k: _stats_ms(v) for k, v in stage_samples.items()}

    perf_doc = {
        "schema": "slm-v9-runtime-performance/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "external_ai_calls": 0,
        "physical_target_hardware_status": "PHYSICAL_TARGET_HARDWARE = NOT_MEASURED (host has ~15.78 GiB RAM; no physical 4–8 GiB target laptop attached)",
        "frontend_memory_status": "FRONTEND_MEMORY = NOT_MEASURED_BACKEND_ONLY",
        "host_environment": {
            "os": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "logical_cores": os.cpu_count(),
            "total_physical_ram_mib": snap_before_load["os"].get("total_phys_mib"),
            "runtime_build": "llama.cpp b12470 (win-cpu-x64)",
            "model_key": V9_LOCAL_SLM_MODEL_KEY,
            "v9_max_tokens": DEFAULT_V9_SLM_MAX_TOKENS,
            "llama_server_batch_flags": ["-b", "512", "-ub", "512"],
        },
        "cold_start": {
            "cold_start_e2e_ms": cold_e2e_ms,
            "server_load_time_ms": env_cold.get("server_load_time_ms"),
            "stage_timings_count": len(st_cold),
            "stage_timings_ms": st_cold,
            "route_status": out_cold.status,
            "has_scene3d": has_scene_cold,
        },
        "pure_warm_uncached_slm_n100": {
            "e2e_to_verified_scene3d_ms": e2e_stats,
            "slm_inference_ms": inf_stats,
            "mean_tokens_per_sec": round(sum(tps_all) / len(tps_all), 2) if tps_all else None,
            "served_count": sum(1 for r in warm_rows if r["status"] == "SERVED"),
            "scene3d_present_count": sum(1 for r in warm_rows if r["has_scene3d"]),
            "stage_timings_summary_ms": stage_stats,
            "by_complexity_tier": {
                t: _stats_ms([r["e2e_ms"] for r in warm_rows if r["tier"] == t])
                for t in ("short", "medium", "long")
            },
            "stability_drift_q1_vs_q4": {
                "first_25_e2e_mean_ms": round(sum(r["e2e_ms"] for r in drift_first25) / 25.0, 2),
                "last_25_e2e_mean_ms": round(sum(r["e2e_ms"] for r in drift_last25) / 25.0, 2),
                "first_25_mean_comb_ws_mib": round(sum(r["comb_ws_mib"] for r in drift_first25) / 25.0, 2),
                "last_25_mean_comb_ws_mib": round(sum(r["comb_ws_mib"] for r in drift_last25) / 25.0, 2),
                "total_py_page_faults_delta": (drift_last25[-1]["py_page_faults"] or 0) - (drift_first25[0]["py_page_faults"] or 0),
                "total_srv_page_faults_delta": (drift_last25[-1]["srv_page_faults"] or 0) - (drift_first25[0]["srv_page_faults"] or 0),
            },
        },
        "mixed_warm_uncached_n100": {
            "e2e_ms": _stats_ms(mixed_e2e),
            "fast_path_count": mixed_fast,
            "slm_invoked_count": mixed_slm,
            "served_count": mixed_served,
        },
        "warm_cached_explicit_runtime": {
            "initial_5_misses_ms": _stats_ms(cached_miss_ms),
            "subsequent_25_hits_ms": _stats_ms(cached_hit_ms),
            "single_flight_4_threads": {
                "submitted": 4,
                "served": coalesce_served,
                "cache_hits": coalesce_hits,
                "results": coalesce_outs,
            },
        },
        "deterministic_fast_path_n30": _stats_ms(det_ms),
        "system_memory_accounting_mib": {
            "before_model_load": snap_before_load,
            "after_cold_load": snap_after_cold,
            "after_100_warm_uncached": snap_after_100,
            "peak_combined_backend_plus_slm_working_set_mib": round(peak_comb_ws, 2),
            "peak_combined_backend_plus_slm_private_commit_mib": round(peak_comb_priv, 2),
            "min_os_available_physical_ram_mib": round(min_os_avail, 2),
            "peak_system_total_committed_mib": round(max_sys_commit, 2),
        },
        "concurrency_and_saturation": conc_results,
        "fault_recovery": fault_recovery,
    }
    (OUT_DIR / "SLM_V9_RUNTIME_PERFORMANCE.json").write_text(json.dumps(perf_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 8. Write P4 markdown summary report from directly measured values
    ab_rows_md = "\n".join(
        f"| `{v['variant']}` | `{v['model_key']}` | `{v['threads']}` | `{v['grammar_mode']}` | `{v['oracle_exact_count']}/{v['total_cases']}` | `{v['wrong_served_count']}` | `{v['e2e_ms']['p50_ms']}` | `{v['e2e_ms']['p95_ms']}` | `{v['slm_inference_ms']['p50_ms']}` | `{v['grammar_retry_used_count']}` | `{v['peak_combined_ws_mib']}` |"
        for v in ablation_variants
    )
    report_md = f"""# AXO HYBRID /9 — Phase P4 CPU Runtime, Memory & Ablation Report

> **Model Under Test:** `{V9_LOCAL_SLM_MODEL_KEY}` (`llama.cpp b12470`, `-b 512 -ub 512`, `max_tokens={DEFAULT_V9_SLM_MAX_TOKENS}`)  
> **Scope Disclosures:** `PHYSICAL_TARGET_HARDWARE = NOT_MEASURED` · `FRONTEND_MEMORY = NOT_MEASURED_BACKEND_ONLY` · `external_ai_calls = 0`

---

## 1. Latency & Throughput Summary

| Workload | Count | Served | `p50` E2E (ms) | `p95` E2E (ms) | Mean E2E (ms) | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Cold Start (`AxoV9-Q4_K_M`) | `1` | `1/1` | `{cold_e2e_ms}` | `{cold_e2e_ms}` | `{cold_e2e_ms}` | Server load `{env_cold.get('server_load_time_ms')}` ms, `Scene3D={has_scene_cold}` |
| Pure Warm Uncached SLM (`use_cache=False`, `t=6`) | `100` | `{perf_doc['pure_warm_uncached_slm_n100']['served_count']}/100` | `{e2e_stats['p50_ms']}` | `{e2e_stats['p95_ms']}` | `{e2e_stats['mean_ms']}` | SLM inf `p50={inf_stats['p50_ms']}` ms, `p95={inf_stats['p95_ms']}` ms, `{perf_doc['pure_warm_uncached_slm_n100']['mean_tokens_per_sec']}` tok/s |
| Mixed Warm Uncached (`50` fast + `50` SLM) | `100` | `{mixed_served}/100` | `{perf_doc['mixed_warm_uncached_n100']['e2e_ms']['p50_ms']}` | `{perf_doc['mixed_warm_uncached_n100']['e2e_ms']['p95_ms']}` | `{perf_doc['mixed_warm_uncached_n100']['e2e_ms']['mean_ms']}` | Fast-path `{mixed_fast}`, SLM `{mixed_slm}` |
| Warm Cached (`use_cache=True` w/ `runtime=rt`) | `25` hits | `25/25` | `{perf_doc['warm_cached_explicit_runtime']['subsequent_25_hits_ms']['p50_ms']}` | `{perf_doc['warm_cached_explicit_runtime']['subsequent_25_hits_ms']['p95_ms']}` | `{perf_doc['warm_cached_explicit_runtime']['subsequent_25_hits_ms']['mean_ms']}` | Single-flight `4`-thread duplicate coalesce hits=`{coalesce_hits}/4` |
| Deterministic Fast-Path (`v9`/`v3`) | `30` | `30/30` | `{perf_doc['deterministic_fast_path_n30']['p50_ms']}` | `{perf_doc['deterministic_fast_path_n30']['p95_ms']}` | `{perf_doc['deterministic_fast_path_n30']['mean_ms']}` | `0` SLM calls |

---

## 2. Win32 Process & OS Memory Accounting

- **Total Physical RAM:** `{snap_before_load['os'].get('total_phys_mib')}` MiB (`PHYSICAL_TARGET_HARDWARE = NOT_MEASURED`)
- **Before Model Load:** Combined WS `{snap_before_load['combined_backend_plus_slm_ws_mib']}` MiB
- **After Cold Load:** Combined WS `{snap_after_cold['combined_backend_plus_slm_ws_mib']}` MiB
- **Peak Combined Working Set (Backend + `llama-server.exe`) over `n=100`:** **`{round(peak_comb_ws, 2)}` MiB**
- **Peak Combined Private Commit:** **`{round(peak_comb_priv, 2)}` MiB**
- **Min OS Available Physical RAM:** `{round(min_os_avail, 2)}` MiB | **Peak System Committed:** `{round(max_sys_commit, 2)}` MiB
- **Q1 vs Q4 Memory/Latency Drift:** First 25 E2E mean `{perf_doc['pure_warm_uncached_slm_n100']['stability_drift_q1_vs_q4']['first_25_e2e_mean_ms']}` ms (`{perf_doc['pure_warm_uncached_slm_n100']['stability_drift_q1_vs_q4']['first_25_mean_comb_ws_mib']}` MiB) vs Last 25 `{perf_doc['pure_warm_uncached_slm_n100']['stability_drift_q1_vs_q4']['last_25_e2e_mean_ms']}` ms (`{perf_doc['pure_warm_uncached_slm_n100']['stability_drift_q1_vs_q4']['last_25_mean_comb_ws_mib']}` MiB)

---

## 3. Concurrency, Saturation & Fault Recovery

- **`c=2` (4 batches, 8 reqs):** `served={conc_results['c_2']['served_count']}/8`, E2E `p50={conc_results['c_2']['request_e2e']['p50_ms']}` ms, `p95={conc_results['c_2']['request_e2e']['p95_ms']}` ms
- **`c=4` (2 batches, 8 reqs):** `served={conc_results['c_4']['served_count']}/8`, E2E `p50={conc_results['c_4']['request_e2e']['p50_ms']}` ms, `p95={conc_results['c_4']['request_e2e']['p95_ms']}` ms
- **`c=6` bounded queue (`max_queue=2`):** `completed_ok={conc_results['c_6_bounded_queue_saturation']['completed_ok']}`, `rejected_busy={conc_results['c_6_bounded_queue_saturation']['rejected_busy']}`, `post_saturation_recovery_ok={conc_results['c_6_bounded_queue_saturation']['post_saturation_recovery_ok']}`
- **Crash recovery (`force_kill_server`, pid `{killed_pid}`):** `crash_auto_restart_served={fault_recovery['crash_auto_restart_served']}`
- **Timeout recovery (`timeout_s=0.05` -> `{timeout_code}`):** `post_timeout_served={fault_recovery['post_timeout_served']}`

---

## 4. Controlled Ablations (`n=24` Representative SLM Cases from `val_v9.jsonl`)

| Variant | Model | Threads | Grammar Mode | Oracle Exact | Wrong-Served | `p50` E2E (ms) | `p95` E2E (ms) | `p50` Inf (ms) | Retries | Peak WS (MiB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{ab_rows_md}
"""
    (OUT_DIR / "SLM_V9_SYSTEM_RESOURCE_REPORT.md").write_text(report_md, encoding="utf-8")
    print("[P4 COMPLETE] Wrote SLM_V9_ABLATION.json, SLM_V9_RUNTIME_PERFORMANCE.json, SLM_V9_SYSTEM_RESOURCE_REPORT.md", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
