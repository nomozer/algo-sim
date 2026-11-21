# -*- coding: utf-8 -*-
"""AXO HYBRID /8 Phase D / P4: System-Wide Resource, n=100 Uncached Stability & Concurrency Benchmark.

Measures full backend process-tree & OS memory via Win32 APIs (`GlobalMemoryStatusEx`,
`GetPerformanceInfo`, `GetProcessMemoryInfo`, `GetProcessTimes`), cold start, `n=100`
consecutive warm uncached inferences (`slm_invoked=True`, `cache_hit=False`), separate
warm cached (`n=30`) & deterministic fast-path (`n=30`) baselines, concurrency (`c=1,2,4`
and bounded-queue `c=6` saturation), and a simulated constrained diagnostic (`threads=2`,
explicitly tagged `SIMULATED_RESOURCE_CONSTRAINT_NOT_PHYSICAL_LOW_END`).
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
OUT_DIR = ROOT / "docs/evaluation/geometry/runs/independent-validation-local-ai-production-readiness"
OUT_DIR.mkdir(parents=True, exist_ok=True)
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.ai import adaptive_input_router as AIR  # noqa: E402
from app.ai.local_geometry_parser import clear_local_geometry_parser_cache  # noqa: E402
from app.ai.local_slm_runtime import (  # noqa: E402
    FINETUNED_LOCAL_SLM_MODEL_KEY,
    LocalSlmRuntime,
    LocalSlmRuntimeError,
    get_shared_local_slm_extraction_cache,
)

# ── Win32 Whole-System Memory & Process Counters ─────────────────────────────

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", wintypes.DWORD),
            ("dwMemoryLoad", wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_uint64),
            ("ullAvailPhys", ctypes.c_uint64),
            ("ullTotalPageFile", ctypes.c_uint64),
            ("ullAvailPageFile", ctypes.c_uint64),
            ("ullTotalVirtual", ctypes.c_uint64),
            ("ullAvailVirtual", ctypes.c_uint64),
            ("ullAvailExtendedVirtual", ctypes.c_uint64),
        ]

    class PERFORMANCE_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("CommitTotal", ctypes.c_size_t),
            ("CommitLimit", ctypes.c_size_t),
            ("CommitPeak", ctypes.c_size_t),
            ("PhysicalTotal", ctypes.c_size_t),
            ("PhysicalAvailable", ctypes.c_size_t),
            ("SystemCache", ctypes.c_size_t),
            ("KernelTotal", ctypes.c_size_t),
            ("KernelPaged", ctypes.c_size_t),
            ("KernelNonpaged", ctypes.c_size_t),
            ("PageSize", ctypes.c_size_t),
            ("HandleCount", wintypes.DWORD),
            ("ProcessCount", wintypes.DWORD),
            ("ThreadCount", wintypes.DWORD),
        ]

    class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
            ("PrivateUsage", ctypes.c_size_t),
        ]

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _psapi = ctypes.WinDLL("psapi", use_last_error=True)
    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    _PROCESS_VM_READ = 0x0010


def _proc_mem(pid: int | None) -> dict[str, Any] | None:
    if os.name != "nt" or not pid:
        return None
    h = _kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION | _PROCESS_VM_READ, False, int(pid))
    if not h:
        return None
    try:
        pmc = PROCESS_MEMORY_COUNTERS_EX()
        pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
        if not _psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb):
            return None
        ft_create, ft_exit, ft_kern, ft_user = wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME()
        cpu_ms = None
        if _kernel32.GetProcessTimes(h, ctypes.byref(ft_create), ctypes.byref(ft_exit), ctypes.byref(ft_kern), ctypes.byref(ft_user)):
            k100 = (ft_kern.dwHighDateTime << 32) | ft_kern.dwLowDateTime
            u100 = (ft_user.dwHighDateTime << 32) | ft_user.dwLowDateTime
            cpu_ms = round((k100 + u100) / 10_000.0, 2)
        return {
            "pid": int(pid),
            "working_set_mib": round(pmc.WorkingSetSize / (1024 ** 2), 2),
            "peak_working_set_mib": round(pmc.PeakWorkingSetSize / (1024 ** 2), 2),
            "private_commit_mib": round(pmc.PrivateUsage / (1024 ** 2), 2),
            "page_fault_count": int(pmc.PageFaultCount),
            "cpu_time_ms": cpu_ms,
        }
    finally:
        _kernel32.CloseHandle(h)


def _sys_mem_snapshot(server_pid: int | None) -> dict[str, Any]:
    py_mem = _proc_mem(os.getpid()) or {}
    srv_mem = _proc_mem(server_pid) or {}
    os_mem: dict[str, Any] = {}
    if os.name == "nt":
        ms = MEMORYSTATUSEX()
        ms.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if _kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
            os_mem["memory_load_pct"] = int(ms.dwMemoryLoad)
            os_mem["total_phys_mib"] = round(ms.ullTotalPhys / (1024 ** 2), 2)
            os_mem["avail_phys_mib"] = round(ms.ullAvailPhys / (1024 ** 2), 2)
            os_mem["total_pagefile_mib"] = round(ms.ullTotalPageFile / (1024 ** 2), 2)
            os_mem["avail_pagefile_mib"] = round(ms.ullAvailPageFile / (1024 ** 2), 2)
        pi = PERFORMANCE_INFORMATION()
        pi.cb = ctypes.sizeof(PERFORMANCE_INFORMATION)
        if _psapi.GetPerformanceInfo(ctypes.byref(pi), pi.cb):
            ps = int(pi.PageSize)
            os_mem["system_commit_total_mib"] = round(pi.CommitTotal * ps / (1024 ** 2), 2)
            os_mem["system_commit_limit_mib"] = round(pi.CommitLimit * ps / (1024 ** 2), 2)
            os_mem["system_commit_peak_mib"] = round(pi.CommitPeak * ps / (1024 ** 2), 2)
            os_mem["os_handle_count"] = int(pi.HandleCount)
            os_mem["os_process_count"] = int(pi.ProcessCount)
            os_mem["os_thread_count"] = int(pi.ThreadCount)
    comb_ws = round((py_mem.get("working_set_mib") or 0.0) + (srv_mem.get("working_set_mib") or 0.0), 2)
    comb_priv = round((py_mem.get("private_commit_mib") or 0.0) + (srv_mem.get("private_commit_mib") or 0.0), 2)
    return {
        "python_backend": py_mem,
        "llama_server": srv_mem,
        "combined_backend_plus_slm_ws_mib": comb_ws,
        "combined_backend_plus_slm_private_commit_mib": comb_priv,
        "os": os_mem,
    }


def _stats_ms(vals: list[float]) -> dict[str, Any]:
    if not vals:
        return {"count": 0, "min_ms": None, "p50_ms": None, "p95_ms": None, "max_ms": None, "mean_ms": None}
    sv = sorted(float(v) for v in vals)
    n = len(sv)
    p95_idx = min(n - 1, max(0, int(0.95 * (n - 1))))
    return {
        "count": n,
        "min_ms": round(sv[0], 2),
        "p50_ms": round(statistics.median(sv), 2),
        "p95_ms": round(sv[p95_idx], 2),
        "max_ms": round(sv[-1], 2),
        "mean_ms": round(sum(sv) / n, 2),
    }


def _build_100_uncached_prompts() -> list[dict[str, Any]]:
    """Build 100 distinct SLM-invoking prompts across short/medium/long complexity tiers."""
    tri_sets = [("S", "A", "B", "C"), ("K", "M", "N", "P"), ("P", "E", "F", "G"), ("H", "U", "V", "W"), ("D", "X", "Y", "Z")]
    quad_sets = [("S", "A", "B", "C", "D"), ("K", "M", "N", "P", "Q"), ("H", "U", "V", "W", "X"), ("G", "R", "S", "T", "U"), ("P", "E", "F", "G", "H")]
    items: list[dict[str, Any]] = []
    for idx in range(100):
        tier = ["short", "medium", "long"][idx % 3]
        lens = ["a", "2a", "3a", "a√2", "a√3", "2a√2", "4a", "5a", "6a", "a√5"][(idx // 3) % 10]
        hval = ["2a", "3a", "a√3", "a√6", "4a", "2a√3", "5a", "a√2", "3a√2", "2a√5"][(idx // 7 + idx) % 10]
        if tier == "short":
            ap, a, b, c = tri_sets[idx % len(tri_sets)]
            # Reordered/missing `hình` or conversational trigger ensures SLM invocation cleanly!
            txt = f"Đề bài {idx+1}: Cho khối chóp {ap}.{a}{b}{c} có đáy {a}{b}{c} vuông tại {a}, {a}{b}={lens}, {a}{c}={hval}, cạnh bên {ap}{a} thẳng đứng vuông góc với ({a}{b}{c}) và {ap}{a}={hval}. Tính thể tích {ap}.{a}{b}{c}."
        elif tier == "medium":
            ap, a, b, c, d0 = quad_sets[idx % len(quad_sets)]
            ang = ["30 độ", "45 độ", "60 độ"][idx % 3]
            txt = f"Bài toán {idx+1}: Xét chóp {ap}.{a}{b}{c}{d0} nhận {a}{b}{c}{d0} làm hình vuông cạnh {lens}. Cạnh {ap}{a} vuông góc với đáy ({a}{b}{c}{d0}), góc giữa ({ap}{b}{c}) và ({a}{b}{c}{d0}) đo được {ang}. Tính khoảng cách từ {a} đến ({ap}{b}{c})."
        else:
            ap, a, b, c = tri_sets[idx % len(tri_sets)]
            hp = next(p for p in ("I", "T", "E", "O") if p not in f"{ap}{a}{b}{c}")
            ang = ["30°", "45°", "60°"][idx % 3]
            txt = (
                f"Câu {idx+1}: Cho hình chóp {ap}.{a}{b}{c} có đáy {a}{b}{c} là tam giác đều cạnh {lens}. "
                f"Gọi {hp} là trung điểm của cạnh {a}{b}, hình chiếu vuông góc của {ap} lên ({a}{b}{c}) trùng với điểm {hp}. "
                f"Biết góc giữa {ap}{c} với mặt phẳng ({a}{b}{c}) bằng {ang}. Tìm thể tích khối chóp {ap}.{a}{b}{c}."
            )
        items.append({"idx": idx, "tier": tier, "text": txt})
    return items


def _build_30_deterministic_fastpath_prompts() -> list[str]:
    out = []
    for i in range(30):
        side = ["a", "2a", "3a", "4a", "5a", "6a"][i % 6]
        h = ["2a", "3a", "4a", "a√3", "2a√3"][i % 5]
        out.append(f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh {side}, SA vuông góc với (ABCD) và SA={h}. Tính thể tích khối chóp S.ABCD.")
    return out


def _get_server_pid(rt: LocalSlmRuntime) -> int | None:
    proc = getattr(rt, "_proc", None)
    return getattr(proc, "pid", None) if proc is not None else None


def main() -> int:
    prompts_100 = _build_100_uncached_prompts()
    fast_30 = _build_30_deterministic_fastpath_prompts()

    rt = LocalSlmRuntime()
    rt.shutdown()
    snap_before_load = _sys_mem_snapshot(None)
    print(f"[P4] OS Total Phys: {snap_before_load['os'].get('total_phys_mib')} MiB | Avail before load: {snap_before_load['os'].get('avail_phys_mib')} MiB", flush=True)

    try:
        # 1. Cold start (1 uncached request)
        clear_local_geometry_parser_cache()
        t_cold0 = time.perf_counter()
        out_cold = AIR.route_text_input_local_slm(
            prompts_100[0]["text"],
            model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
            strategy="compact_clause",
            runtime=rt,
            allow_download=False,
            threads=6,
            use_verified_normalizer=True,
            closure_mode="v7",
            normalizer_version="v2",
            use_cache=False,
            cache_prompt=True,
        )
        cold_e2e_ms = round((time.perf_counter() - t_cold0) * 1000.0, 2)
        rd_cold = out_cold.response.get("route_d") or {}
        env_cold = rd_cold.get("slm_grounding_envelope") or {}
        st_cold = env_cold.get("stage_timings_ms") or {}
        srv_pid = _get_server_pid(rt)
        snap_after_cold = _sys_mem_snapshot(srv_pid)
        has_scene_cold = bool((out_cold.response.get("envelope") or {}).get("scene3d"))
        print(f"[P4 COLD] e2e={cold_e2e_ms} ms load={env_cold.get('server_load_time_ms')} ms status={out_cold.status} scene3d={has_scene_cold} comb_ws={snap_after_cold['combined_backend_plus_slm_ws_mib']} MiB", flush=True)

        # 2. n=100 consecutive warm uncached requests (threads=6)
        warm_rows: list[dict[str, Any]] = []
        peak_comb_ws = snap_after_cold["combined_backend_plus_slm_ws_mib"]
        peak_comb_priv = snap_after_cold["combined_backend_plus_slm_private_commit_mib"]
        min_os_avail = snap_after_cold["os"].get("avail_phys_mib", 1e9)
        max_sys_commit = snap_after_cold["os"].get("system_commit_total_mib", 0.0)

        for item in prompts_100:
            clear_local_geometry_parser_cache()
            t0 = time.perf_counter()
            out = AIR.route_text_input_local_slm(
                item["text"],
                model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
                strategy="compact_clause",
                runtime=rt,
                allow_download=False,
                threads=6,
                use_verified_normalizer=True,
                closure_mode="v7",
                normalizer_version="v2",
                use_cache=False,
                cache_prompt=True,
            )
            e2e_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            rd = out.response.get("route_d") or {}
            env = rd.get("slm_grounding_envelope") or {}
            st = env.get("stage_timings_ms") or {}
            assert env.get("slm_invoked") is True, f"Prompt {item['idx']} bypassed SLM!"
            assert env.get("cache_hit") is False, f"Prompt {item['idx']} hit cache!"
            snap = _sys_mem_snapshot(_get_server_pid(rt))
            peak_comb_ws = max(peak_comb_ws, snap["combined_backend_plus_slm_ws_mib"])
            peak_comb_priv = max(peak_comb_priv, snap["combined_backend_plus_slm_private_commit_mib"])
            min_os_avail = min(min_os_avail, snap["os"].get("avail_phys_mib", 1e9))
            max_sys_commit = max(max_sys_commit, snap["os"].get("system_commit_total_mib", 0.0))
            warm_rows.append({
                "idx": item["idx"],
                "tier": item["tier"],
                "status": out.status,
                "has_scene3d": bool((out.response.get("envelope") or {}).get("scene3d")),
                "e2e_ms": e2e_ms,
                "slm_inference_ms": env.get("inference_time_ms"),
                "prompt_eval_ms": st.get("prompt_eval_ms"),
                "token_gen_ms": st.get("token_gen_ms"),
                "tokens_per_sec": st.get("tokens_per_sec"),
                "queue_wait_ms": st.get("queue_wait_ms"),
                "comb_ws_mib": snap["combined_backend_plus_slm_ws_mib"],
                "comb_priv_mib": snap["combined_backend_plus_slm_private_commit_mib"],
                "sys_commit_mib": snap["os"].get("system_commit_total_mib"),
                "py_page_faults": snap["python_backend"].get("page_fault_count"),
                "srv_page_faults": snap["llama_server"].get("page_fault_count"),
            })
            if (item["idx"] + 1) % 25 == 0:
                print(f"[P4 WARM-100] {item['idx']+1}/100 done | last e2e={e2e_ms} ms | peak_comb_ws={peak_comb_ws} MiB | sys_commit={snap['os'].get('system_commit_total_mib')} MiB", flush=True)

        snap_after_100 = _sys_mem_snapshot(_get_server_pid(rt))

        # 3. Separate Warm Cached (n=30, explicit use_cache=True) & Deterministic Fast Path (n=30)
        cached_times: list[float] = []
        ext_cache = get_shared_local_slm_extraction_cache()
        ext_cache.clear()
        for i in range(30):
            txt = prompts_100[i % 5]["text"]
            t0 = time.perf_counter()
            out_c = AIR.route_text_input_local_slm(
                txt,
                model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
                strategy="compact_clause",
                runtime=rt,
                allow_download=False,
                threads=6,
                use_verified_normalizer=True,
                closure_mode="v7",
                normalizer_version="v2",
                use_cache=True,
                cache_prompt=True,
            )
            ms = round((time.perf_counter() - t0) * 1000.0, 2)
            if i >= 5:  # first 5 populate the cache; next 25 measure pure warm cache hit
                cached_times.append(ms)

        det_times: list[float] = []
        for txt in fast_30:
            clear_local_geometry_parser_cache()
            t0 = time.perf_counter()
            out_d = AIR.route_text_input_local_slm(
                txt,
                model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
                strategy="compact_clause",
                runtime=rt,
                allow_download=False,
                threads=6,
                use_cache=False,
            )
            det_times.append(round((time.perf_counter() - t0) * 1000.0, 2))
        print(f"[P4 CACHED/FAST] warm_cached p50={_stats_ms(cached_times)['p50_ms']} ms | det_fast_path p50={_stats_ms(det_times)['p50_ms']} ms", flush=True)

        # 4. Concurrency (c=2, c=4 simultaneous uncached requests + c=6 bounded queue saturation)
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
                    t0 = time.perf_counter()
                    o = AIR.route_text_input_local_slm(
                        ptxt,
                        model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
                        strategy="compact_clause",
                        runtime=rt,
                        allow_download=False,
                        threads=6,
                        use_verified_normalizer=True,
                        closure_mode="v7",
                        normalizer_version="v2",
                        use_cache=False,
                        cache_prompt=False,
                    )
                    ms = round((time.perf_counter() - t0) * 1000.0, 2)
                    rd = o.response.get("route_d") or {}
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
            print(f"[P4 CONC c={conc_n}] e2e p50={conc_results[f'c_{conc_n}']['request_e2e']['p50_ms']} p95={conc_results[f'c_{conc_n}']['request_e2e']['p95_ms']} comb_ws={snap_c['combined_backend_plus_slm_ws_mib']} MiB", flush=True)

        # c=6 saturation burst testing bounded semaphore/queue (`max_queue=2`)
        rt.shutdown()
        rt_sat = LocalSlmRuntime(max_queue=2, allow_download=False)
        sat_ok = 0
        sat_busy = 0
        sat_other = 0
        try:
            def _sat_call(i_idx: int) -> str:
                try:
                    _ = rt_sat.chat_completion_json(
                        messages=[
                            {"role": "system", "content": "Extract compact JSON."},
                            {"role": "user", "content": prompts_100[i_idx]["text"]},
                        ],
                        json_schema={"type": "object"},
                        model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
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
            # Verify runtime stays healthy immediately after saturation burst
            post_sat = rt_sat.chat_completion_json(
                messages=[
                    {"role": "system", "content": "Extract compact JSON."},
                    {"role": "user", "content": prompts_100[0]["text"]},
                ],
                json_schema={"type": "object"},
                model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
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
        print(f"[P4 SAT c=6 max_q=2] ok={sat_ok} busy={sat_busy} other={sat_other} recovery_ok={post_sat_ok}", flush=True)

        # 5. Simulated Constrained-CPU/Context Diagnostic (threads=2, ctx=1536, n=20)
        rt.shutdown()
        rt_low = LocalSlmRuntime(ctx_size=1536)
        low_e2e: list[float] = []
        low_inf: list[float] = []
        try:
            for item in prompts_100[:20]:
                clear_local_geometry_parser_cache()
                t0 = time.perf_counter()
                out_l = AIR.route_text_input_local_slm(
                    item["text"],
                    model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
                    strategy="compact_clause",
                    runtime=rt_low,
                    allow_download=False,
                    threads=2,
                    use_verified_normalizer=True,
                    closure_mode="v7",
                    normalizer_version="v2",
                    use_cache=False,
                    cache_prompt=True,
                )
                ms = round((time.perf_counter() - t0) * 1000.0, 2)
                low_e2e.append(ms)
                env_l = (out_l.response.get("route_d") or {}).get("slm_grounding_envelope") or {}
                if env_l.get("inference_time_ms") is not None:
                    low_inf.append(float(env_l["inference_time_ms"]))
            snap_low = _sys_mem_snapshot(_get_server_pid(rt_low))
        finally:
            rt_low.shutdown()
        print(f"[P4 SIMULATED LOW-THREAD] threads=2 ctx=1536 n=20 e2e p50={_stats_ms(low_e2e)['p50_ms']} p95={_stats_ms(low_e2e)['p95_ms']} ms", flush=True)
    finally:
        rt.shutdown()

    e2e_all = [r["e2e_ms"] for r in warm_rows]
    inf_all = [r["slm_inference_ms"] for r in warm_rows if r["slm_inference_ms"] is not None]
    tps_all = [r["tokens_per_sec"] for r in warm_rows if r["tokens_per_sec"] is not None]
    e2e_stats = _stats_ms(e2e_all)
    inf_stats = _stats_ms(inf_all)

    drift_first25 = warm_rows[:25]
    drift_last25 = warm_rows[-25:]

    payload = {
        "schema": "slm-system-resource-concurrency-benchmark/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "external_ai_calls": 0,
        "physical_low_end_status": "PHYSICAL_LOW_END = NOT_MEASURED (host has 15.78 GiB physical RAM; no physical 4 GiB or 6 GiB Windows laptop attached)",
        "scope_disclosure": "Backend-only CPU benchmark (frontend browser / Vite / WebGL footprint NOT_MEASURED_BACKEND_ONLY because frontend/ is BLOCKED_OWNERSHIP).",
        "host_environment": {
            "os": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "logical_cores": os.cpu_count(),
            "total_physical_ram_mib": snap_before_load["os"].get("total_phys_mib"),
            "runtime_build": "llama.cpp b12470 (win-cpu-x64)",
            "model_key": FINETUNED_LOCAL_SLM_MODEL_KEY,
        },
        "cold_start": {
            "cold_start_e2e_ms": cold_e2e_ms,
            "server_load_time_ms": env_cold.get("server_load_time_ms"),
            "prompt_eval_ms": st_cold.get("prompt_eval_ms"),
            "token_gen_ms": st_cold.get("token_gen_ms"),
            "route_status": out_cold.status,
            "has_scene3d": has_scene_cold,
        },
        "warm_uncached_n100_threads6": {
            "e2e_to_verified_scene3d_ms": e2e_stats,
            "slm_inference_ms": inf_stats,
            "mean_tokens_per_sec": round(sum(tps_all) / len(tps_all), 2) if tps_all else None,
            "served_count": sum(1 for r in warm_rows if r["status"] == "SERVED"),
            "scene3d_present_count": sum(1 for r in warm_rows if r["has_scene3d"]),
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
        "warm_cached_separate_n25_hits": _stats_ms(cached_times),
        "deterministic_fast_path_n30": _stats_ms(det_times),
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
        "simulated_constrained_diagnostic": {
            "label": "SIMULATED_RESOURCE_CONSTRAINT_NOT_PHYSICAL_LOW_END",
            "config": {"threads": 2, "ctx_size": 1536, "n": 20},
            "e2e_ms": _stats_ms(low_e2e),
            "slm_inference_ms": _stats_ms(low_inf),
            "memory_snapshot": snap_low,
        },
        "registered_threshold_evaluation": {
            "warm_uncached_p95_le_5000ms": {
                "threshold_ms": 5000.0,
                "measured_e2e_p95_ms": e2e_stats["p95_ms"],
                "measured_slm_inf_p95_ms": inf_stats["p95_ms"],
                "pass": bool(e2e_stats["p95_ms"] is not None and e2e_stats["p95_ms"] <= 5000.0),
            },
            "combined_rss_le_2048_mib": {
                "threshold_mib": 2048.0,
                "measured_peak_combined_ws_mib": round(peak_comb_ws, 2),
                "pass": peak_comb_ws <= 2048.0,
            },
        },
    }
    out_path = OUT_DIR / "SYSTEM_RESOURCE_AND_CONCURRENCY_BENCHMARK.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[P4 COMPLETE] Written SYSTEM_RESOURCE_AND_CONCURRENCY_BENCHMARK.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
