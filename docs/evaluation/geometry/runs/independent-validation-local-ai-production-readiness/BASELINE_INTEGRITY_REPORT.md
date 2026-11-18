# AXO HYBRID /8 — BASELINE INTEGRITY REPORT (Phase P0 / Gate D0)

- **Campaign:** AXO HYBRID /8 — Independent Validation & Local AI Production Readiness
- **Run ID:** `independent-validation-local-ai-production-readiness`
- **Status:** `Gate D0 = PASS` (`VERIFIED`)
- **Generated On:** 2026-11-19 (UTC+07:00)

## 1. Repository, Branch & Working Tree Identity (`VERIFIED`)

| Item | Verified Value | Expected Baseline (/7 Closure) | Match |
|---|---|---|---|
| Repository | `D:\Documents\projects\algo-sim` | `D:\Documents\projects\algo-sim` | YES |
| Worktree | `D:\Documents\projects\algo-sim\.superpowers\worktrees\local-first-geometry-understanding` | `.superpowers/worktrees/local-first-geometry-understanding` | YES |
| Branch | `feat/local-first-geometry-understanding` | `feat/local-first-geometry-understanding` | YES |
| Starting `HEAD` | `ae20a9a6e02a00dea19c259c4e8d02350028e4d1` | `ae20a9a6e02a00dea19c259c4e8d02350028e4d1` | YES |
| Product Candidate Commit | `6310113f2202bc3a4919406b26fad08cb09b38c9` | `6310113f2202bc3a4919406b26fad08cb09b38c9` | YES |
| Candidate Freeze Commit | `9a9352d586caa360f82052ba1b76fe9b4227f26c` | `9a9352d586caa360f82052ba1b76fe9b4227f26c` | YES |
| Starting `git status --short` | Clean (`""`) | Clean | YES |

## 2. Frozen Candidate, Cache & Route Policy (`VERIFIED`)

- `backend/scripts/freeze_evaluation_candidate.py --verify`: **PASS** (`rc=0`, `123` files, `measured_system_sha256 = 113a6a7cf6bbc15ac23119150b805437e785d2b0714b26c2157d147514c2ef67`).
- `backend/scripts/lock_cache_identity.py --verify`: **PASS** (`rc=0`, `CACHE_VERSION = 145`, `ROUTE_D_CACHE_POLICY = 145:route-d`, environment fingerprint `6233c43c395c9b49...`, 4 locked Gemini surfaces unchanged).
- `backend/app/main.py` (`L950-965`) & `backend/app/ai/route_policy.py` (`L23-50`): `RoutePolicy.default_route_mode = "HYBRID"`, default live transport `HYBRID_ROUTE_MODE = "live"`, opt-in experimental mode `HYBRID_ROUTE_MODE = "local-slm"`.
- Invariant during `/8`: **`backend/app/**` and `frontend/**` remain unmodified** so `/8` audits the exact frozen `/7` product candidate (`123` files, SHA-256 `113a6a7cf6bb...`).

## 3. Active Contract Versions (`VERIFIED`)

| Layer / Component | Verified Contract Version | Module Anchor |
|---|---|---|
| Local SLM Runtime | `local-slm-runtime/3` | [`local_slm_runtime.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ai/local_slm_runtime.py) |
| Local SLM Extractor | `local-slm-extractor/3` | [`local_slm_extractor.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ai/local_slm_extractor.py) |
| Grounding Validator / Envelope | `slm-grounding-validator/3` · `slm-grounding-envelope/3` | [`local_slm_extractor.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ai/local_slm_extractor.py) |
| Compact Extraction Schema | `slm-compact-clause/1` | [`local_slm_extractor.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ai/local_slm_extractor.py) |
| Verified Normalizer | `slm-verified-normalizer/2` (`v1` retained for Config B) | [`slm_verified_normalizer.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ai/slm_verified_normalizer.py) |
| Local Geometry Parser | `local-geometry-parser/2` | [`local_geometry_parser.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ai/local_geometry_parser.py) |
| Typed Facts Contract | `typed-fact-next/2` | [`typed_fact_next.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/typed_fact_next.py) |
| Planner | `geometry-fact-planner/26` | [`planner.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/planner.py) |
| Registry | `geometry-functions/33` | [`registry.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/registry.py) |
| Exact Kernel | `geometry-function-engine/24` | [`engine.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/engine.py) |
| Adapter | `hybrid-simulation-adapter/4` (`hybrid-route-d-simulation/4`) | [`adapter4_route.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ai/adapter4_route.py) |
| Local Cache Namespace | `HYBRID_V7_LOCAL_SLM` | [`local_slm_runtime.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ai/local_slm_runtime.py) |

## 4. GGUF Models & `llama.cpp` Runtime Identity (`VERIFIED`)

| Artifact | Location Outside Repo (`%LOCALAPPDATA%\axo-slm`) | Size (bytes) | SHA-256 | Match |
|---|---|---|---|---|
| `Qwen3-0.6B-AxoV7-Q4_K_M.gguf` (`qwen3-0.6b-axo-v7-q4_k_m`) | `models\qwen3-0.6b-axo-v7-q4_k_m\Qwen3-0.6B-AxoV7-Q4_K_M.gguf` | `396,704,736` | `36e784d135627225e0b9c11b097c9a36222ee1e0e3f6f1d6116cc3060ac5e148` | YES |
| `Qwen3-0.6B-Q4_K_M.gguf` (`qwen3-0.6b-q4_k_m`, rollback) | `models\qwen3-0.6b-q4_k_m\Qwen3-0.6B-Q4_K_M.gguf` | `396,705,472` | `ac2d97712095a558e31573f62f466a3f9d93990898b0ec79d7c974c1780d524a` | YES |
| `qwen2.5-0.5b-instruct-q4_k_m.gguf` (historical comparator) | `models\qwen2.5-0.5b-instruct-q4_k_m\qwen2.5-0.5b-instruct-q4_k_m.gguf` | `491,400,032` | `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db` | YES |
| `Qwen3-0.6B-AxoV7-F16.gguf` (quantization build intermediate) | `gguf_build\Qwen3-0.6B-AxoV7-F16.gguf` | `1,198,182,368` | `ee3b965b375d9e0fd4a2b643277ae24ccdd49298409abf9317015fdf1a3e9a56` | YES |
| `llama-server.exe` | `runtime\llama.cpp-b12470-win-cpu-x64\llama-server.exe` | — | `version: 1.0.0-dev (build 12470, commit dde9de82c)` | YES |

## 5. Historical Run Manifests (`/5`, `/6`, `/7`) & Sealed/Pending Governance (`VERIFIED`)

| Historical Run | Manifest | Files Checked | LF-Normalized SHA-256 Mismatches |
|---|---|---|---|
| AXO HYBRID /5 (`slm-local-geometry-understanding`) | [`run.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/slm-local-geometry-understanding/run.json) | `16` | `0` |
| AXO HYBRID /6 (`specialized-geometry-extraction-slm-optimization`) | [`run.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/specialized-geometry-extraction-slm-optimization/run.json) | `19` | `0` |
| AXO HYBRID /7 (`deterministic-geometry-language-closure-slm-finetuning`) | [`run.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/run.json) | `24` | `0` |

- **Sealed / Locked / Pending Surfaces Preserved (`VERIFIED`):**
  - `hybrid-independent-h1`: `H1_CORPUS_INTEGRITY.json` = `AWAITING_INDEPENDENT_CORPUS`, `h1-corpus-template.json` holds `2` unpopulated template stubs (`0` opened rows).
  - `hybrid-v2-independent-vietnamese-section-holdout-wave2` & `...-wave3`: untouched.
  - `hybrid-master-backend-replacement/{k1,r1,s2}-owner-approval.template.json`: all 3 at `owner_decision = "PENDING_OWNER_DECISION"`.
  - Cloud live AI switch: `ALLOW_LIVE_AI = 0`, `GEMINI_API_KEY = ""`, `external_ai_calls = 0`.
