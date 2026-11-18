# AXO HYBRID /8 — System-Wide Resource, Concurrency & Latency Readiness Report (`RESOURCE_READINESS_REPORT.md`)

> **Status (`PHYSICAL_LOW_END`):** **`NOT_MEASURED`** (benchmarked on Windows 11 64-bit development host with `12` logical cores and `16,163.3 MiB` / `15.78 GiB` physical RAM; physical 4 GiB / 6 GiB laptops were not attached, so `LOW_END_HARDWARE_BENCHMARK.json` is omitted).  
> **Scope Disclosure:** `frontend_browser_footprint = NOT_MEASURED_BACKEND_ONLY` (`frontend/` is untouched under `BLOCKED_OWNERSHIP`). All Win32 process-tree and OS memory counters were collected via `GlobalMemoryStatusEx`, `GetPerformanceInfo`, `GetProcessMemoryInfo`, and `GetProcessTimes` (`python.exe` + child `llama-server.exe` process tree + whole-OS physical/commit totals).  
> **Machine Artifact:** [`SYSTEM_RESOURCE_AND_CONCURRENCY_BENCHMARK.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/independent-validation-local-ai-production-readiness/SYSTEM_RESOURCE_AND_CONCURRENCY_BENCHMARK.json) · **Generator:** [`benchmark_slm_v8_system_resources.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/scripts/benchmark_slm_v8_system_resources.py) · **`external_ai_calls = 0`**

---

## 1. Host Environment & Cold Start (`VERIFIED`)

| Property / Metric | Measured Value |
|---|---|
| OS / Machine / CPU | `Windows-11-10.0.26100-SP0` · `AMD64` · `Intel64 Family 6 Model 141 Stepping 1, GenuineIntel` (`12` logical cores) |
| Total Physical RAM | `16,163.30 MiB` (`15.78 GiB`) · Pagefile Limit `29,987.30 MiB` |
| Runtime & GGUF | `llama.cpp b12470 (win-cpu-x64)` · `qwen3-0.6b-axo-v7-q4_k_m` (`396,704,736` bytes, CPU-first, `threads = 6`) |
| Cold Start E2E (`1` uncached SLM request) | **`5,073.01 ms`** (`server_load_time = 1,055.34 ms`, `prompt_eval = 2,061.24 ms`, `token_gen = 917.15 ms`, status `REFUSED`) |
| Pre-load Backend RSS / Private Commit | Python `59.76 MiB` WS / `49.47 MiB` private · OS avail `5,669.96 MiB` (`64%` load) · Sys Commit `14,081.47 MiB` |
| Post-Cold-Load Backend + SLM Tree | Python `65.00 MiB` + `llama-server` `901.89 MiB` = **`966.89 MiB` combined WS** (`629.41 MiB` combined private commit) · OS avail `4,771.91 MiB` (`70%`) · Sys Commit `14,654.41 MiB` |

---

## 2. `n = 100` Consecutive Warm Uncached Stress Stability (`threads = 6`, `VERIFIED`)

Every one of the `100` distinct prompts triggered live CPU SLM extraction (`slm_invoked = True`, `cache_hit = False`, `cache_prompt = True`, `use_cache = False`), spanning three balanced structural complexity tiers (`34` short, `33` medium, `33` long; `27/100` `SERVED` with verified `Scene3D`, `mean = 30.37 tok/s`):

| Metric / Slice | Count | Min (ms) | `p50` (ms) | `p95` (ms) | Max (ms) | Mean (ms) |
|---|---:|---:|---:|---:|---:|---:|
| **E2E (`route_text_input_local_slm`)** | `100` | `862.68` | **`3,630.08`** | **`6,898.88`** | `8,708.64` | `3,512.17` |
| **SLM Inference Only (`llama-server`)** | `100` | `847.15` | **`3,593.94`** | **`6,868.30`** | `8,683.20` | `3,483.67` |
| Tier `short` (single-clause reordered/conversational) | `34` | `862.68` | `1,320.86` | **`1,961.88`** | `2,382.00` | `1,419.70` |
| Tier `medium` (multi-constraint quad pyramid + angle) | `33` | `3,306.41` | `3,769.20` | `6,045.45` | `6,965.38` | `4,208.19` |
| Tier `long` (multi-clause centroid/midpoint + angle) | `33` | `3,503.01` | `4,521.18` | `7,368.18` | `8,708.64` | `4,972.03` |
| **Deterministic Fast Path (parser-complete, `0` SLM)** | `30` | `39.15` | **`51.50`** | **`72.65`** | `97.09` | `53.37` |
| Separate Cache-Enabled Probe (`runtime=rt`, see note) | `25` | `1,168.71` | `4,315.38` | `5,786.44` | `6,677.63` | `3,764.05` |

> **Important Disclosure on `warm_cached_separate_n25_hits` (`4,315.38 ms`):** Passing an explicit injected `runtime=rt` alongside `use_cache=True` hit the isolation guard `if use_cache and runtime is None:` at [`local_slm_extractor.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ai/local_slm_extractor.py#L3544-L3560), so those 25 probes ran as cache-miss uncached calls rather than hitting `get_shared_local_slm_extraction_cache()`. Under production defaults (`runtime=None`), singleton extraction-cache hits were previously verified at **`p50 = 36.45 ms` / `p95 = 49.50 ms`** in [`SLM_V7_PERFORMANCE.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_PERFORMANCE.json#L650-L670).

### `Q1` vs `Q4` Stability & Win32 Memory Leak Check (`n = 100`)

| Counter | First 25 (`Q1`) / After Cold | Last 25 (`Q4`) / After `n=100` | Peak Observed (`n=100`) | Verdict |
|---|---:|---:|---:|---|
| E2E Latency Mean | `3,307.02 ms` | `3,803.75 ms` (`+15.0%` thermal / tier mix) | `8,708.64 ms` | Stable within thermal bounds |
| Combined Backend + SLM Working Set | `970.02 MiB` mean | `971.91 MiB` mean (`971.63 MiB` at end) | **`973.29 MiB`** (`638.63 MiB` private) | **Zero memory leak** (`< 2 MiB` drift) |
| OS Physical RAM Available / Sys Commit | `4,771.91 MiB` / `14,654.41 MiB` | `4,101.04 MiB` / `15,097.05 MiB` | Min avail `3,596.22 MiB` / Commit `15,857.29 MiB` | Healthy on 16 GiB host |
| Page Fault Delta (`Q1 -> Q4`) | — | Python `+845` · `llama-server` `+395,484` | No crash, 0 timeouts | Bounded CPU execution |

### Registered Threshold Check (`/7` vs `/8` Mixed Stress)

| Threshold | Target | `/8` `n=100` Mixed Stress Result | Status |
|---|---:|---:|---|
| Combined Backend + SLM Working Set (`<= 2048 MiB`) | `<= 2,048 MiB` | **`973.29 MiB`** peak | **PASS** |
| Warm Uncached `p95 <= 5,000 ms` (Level 3 readiness target) | `<= 5,000 ms` | **`6,898.88 ms`** e2e / `6,868.30 ms` SLM | **FAIL** (passes Level 2 `<= 12,000 ms` and passes `<= 5,000 ms` on `short` tier `1,961.88 ms`) |

*Comparison Note:* `/7`'s `4,870.26 ms` warm `p95` (`n=30`) ran smaller homogeneous calibration items, whereas `/8`'s 100-item 3-tier workload contains `66%` medium/long multi-clause geometric descriptions, pushing uncached `p95` to `6,898.88 ms` (`max = 8,708.64 ms`).

---

## 3. Concurrency, Bounded Queue Saturation & Constrained-Thread Diagnostic (`VERIFIED`)

| Scenario | Requests | E2E `p50` (ms) | E2E `p95` (ms) | Max (ms) | Queue Wait `p50` (ms) | Combined WS (MiB) | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| `c = 2` parallel uncached | `8` (`4×2`) | `8,629.64` | `9,721.52` | `14,848.25` | `1,639.43` | `972.18` | Serialized single `llama-server` queue |
| `c = 4` parallel uncached | `8` (`2×4`) | `15,013.10` | `18,580.68` | `23,717.26` | `8,760.76` | `973.04` | Head-of-line queuing under single worker |
| `c = 6` saturation (`max_queue = 2`) | `6` burst | — | — | — | — | — | **`completed_ok = 2` · `rejected_busy = 4` · `other_errors = 0` · `post_saturation_recovery_ok = true`** |
| **Simulated Low-Thread** (`threads=2`, `ctx=1536`) | `20` | `5,656.77` | `6,093.38` | `6,426.49` | `~0` | `969.37` | Tagged **`SIMULATED_RESOURCE_CONSTRAINT_NOT_PHYSICAL_LOW_END`** (`slm_inf p50/p95 = 5,615.24 / 6,060.68 ms`) |

---

## 4. Analytical Windows 11 Memory Budget vs. Physical Host Classes (`INFERRED` + `NOT_MEASURED`)

Using measured backend+SLM footprint (`~973 MiB` working set, `~639 MiB` private commit; OS Windows 11 baseline + typical developer/browser background already consuming `~10.4 GiB` commit on the benchmark host before model load, plus unmeasured Chromium/WebGL SPA + optional `RapidOCR` overhead):

| Target Hardware Class | Physical Benchmark Status | Analytical Co-Residency Budget (OS + Browser + FastAPI + `AxoV7`) | Readiness Classification |
|---|---|---|---|
| **4 GiB RAM Windows Laptop** | `PHYSICAL_LOW_END = NOT_MEASURED` | Windows 11 + Chromium/WebGL (~2.5–3.2 GiB) + backend+SLM (`~0.97 GiB` WS) exceeds `4.0 GiB` physical RAM -> high pagefile thrashing & cold-load timeout risk | **UNSAFE / DO NOT DEPLOY** without physical measurement |
| **6 GiB RAM Windows Laptop** | `PHYSICAL_LOW_END = NOT_MEASURED` | Marginal headroom when running browser + backend + SLM + optional OCR simultaneously; unverified swap behavior | **UNVERIFIED / REQUIRES PHYSICAL TEST** |
| **`>= 8 GiB` RAM Desktop/Laptop (`6+` CPU threads)** | Development host (`15.78 GiB`) verified; `8 GiB` **inferred** | `< 1.0 GiB` backend+SLM WS leaves `>= 7 GiB` for Windows 11 + single browser tab | **ACCEPTABLE FOR SINGLE-USER OPT-IN `local-slm`** (subject to `6.9 s` uncached `p95` on multi-clause prompts and single-request serialization) |

## 5. Production Resource Readiness Conclusion

- Memory footprint (`973.29 MiB` peak combined WS, `0` leak across 100 consecutive uncached calls) and saturation safety (`c=6` bounded queue + recovery `100%`) are **production-grade for single-user `>= 8 GiB` devices**.
- However, CPU uncached tail latency under multi-clause load (`p95 = 6,898.88 ms`, `c=2 p95 = 9,721.52 ms`, `c=4 p95 = 18,580.68 ms`) and unmeasured 4–6 GiB physical hardware + frontend footprint **fail** Level 3's `<= 5,000 ms` latency & low-end verification gates. Local SLM is single-user sequential only, not multi-tenant server-scalable without concurrency workers or GPU offloading.
