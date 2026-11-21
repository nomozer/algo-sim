# AXO HYBRID /9 — Baseline Identity, Runtime & Ownership Audit (Phase A / Gate G0)

> **Campaign:** `AXO HYBRID /9 — Local AI Replacement, Vietnamese NLU Generalization & Offline Production Cutover`
> **Run ID:** `axo-hybrid-local-ai-replacement-vietnamese-nlu-offline-cutover`
> **Gate Status:** **`G0 = PASS`** (Verified offline, `external_ai_calls = 0`, `ALLOW_LIVE_AI = 0`)

---

## 1. Git, Worktree & Frozen Baseline Verification

| Item | Verified Value | Status |
|---|---|---|
| Repository | `D:\Documents\projects\algo-sim` | Verified |
| Active Worktree | `D:\Documents\projects\algo-sim\.superpowers\worktrees\local-first-geometry-understanding` | Verified |
| Active Branch | `feat/local-first-geometry-understanding` | Verified |
| Baseline `HEAD` | `c73506cb23b0b365d8e475c6b5386a31176a669b` (AXO CONSTRUCTION /2 docs sync) | Verified Match |
| Working Tree at Start | Clean (`git status --short` empty) | Verified |
| Frozen `/7` Product Commit | `6310113f2202bc3a4919406b26fad08cb09b38c9` (`measured_system = 113a6a7cf6bbc15ac23119150b805437e785d2b0714b26c2157d147514c2ef67`, `123` files) | Verified `freeze_evaluation_candidate.py --verify` MATCH |
| Cache Lock (`cache_identity.lock.json`) | `CACHE_VERSION = "145"`, `ROUTE_D_CACHE_POLICY = "145:route-d"`, `semantic_environment_hash = 6233c43c395c9b493d31d3dbb5d0ca952604730f6185cf541d2f179c077f955b` | Verified `lock_cache_identity.py --verify` MATCH |
| Docs Information Architecture | `audit_docs_information_architecture.py` (29 root docs, 167 catalogued, 0 broken links, 0 leaks) | Verified PASS |
| Locked Gemini Extraction Surfaces | `typed_fact_next_surface = 33197a45e0620d94a669047b47907479d1e7f07b1dc76e7c6abd75ada7a6df14`, `function_calling = 7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25`, `fact_extraction("flat") = 485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a`, `fact_extraction("v3") = 4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f` | Verified Immutable |
| `TypedFactNextPayloadV2` JSON Schema SHA-256 | `fc10ddabf7df49d534a1630d31f81fe60d24df57faffd7ae6239727050a7f983` | Verified Immutable |
| `AXO CONSTRUCTION /2` Prototype Package | `backend/experimental/construction_planner/` (`14` `.py` files, tree content digest `d4c4d3f184d27991ee6df64a357ddb98cf6bf4e37961f7469c59587f64ec7334`, `/2` run freeze `26c9b505fc7796ed9ff6a5c9578701978e92b9c1d6726a8208916a9ea3dca60c`, status `Level 2 — BACKEND_INTEGRATION_READY`) | Preserved Untouched |
| Frozen Historical Runs | `/5`, `/6`, `/7`, `/8`, `Construction /1`, `Construction /2`, `sealed_H1`, `locked_W2_W3` | Preserved Untouched |

---

## 2. Local Model, Runtime & GPU Training Environment Checksums

| Component | Path / Identifier | Size (Bytes) | SHA-256 / Verification |
|---|---|---:|---|
| Fine-Tuned Local SLM (`/7`, preserved untouched) | `C:\Users\Bunny\AppData\Local\axo-slm\models\qwen3-0.6b-axo-v7-q4_k_m\Qwen3-0.6B-AxoV7-Q4_K_M.gguf` | `396,704,736` | `36e784d135627225e0b9c11b097c9a36222ee1e0e3f6f1d6116cc3060ac5e148` (MATCH) |
| Rollback Original SLM (preserved untouched) | `C:\Users\Bunny\AppData\Local\axo-slm\models\qwen3-0.6b-q4_k_m\Qwen3-0.6B-Q4_K_M.gguf` | `396,705,472` | `ac2d97712095a558e31573f62f466a3f9d93990898b0ec79d7c974c1780d524a` (MATCH) |
| Comparator 0.5B Model | `C:\Users\Bunny\AppData\Local\axo-slm\models\qwen2.5-0.5b-instruct-q4_k_m\qwen2.5-0.5b-instruct-q4_k_m.gguf` | `491,400,032` | Registered in `LOCAL_SLM_MODELS` |
| `llama.cpp` Runtime (`b12470`) | `llama-b12470-bin-win-cpu-x64.zip` (`fc833716…`) -> `llama-server.exe` | `9,728` (launcher + bundled DLLs) | `d59a9c5eea74381b43317cd3fda2d0bc85632ff641091c73c1ab82527a94e089` (provision manifest SHA `fc83371644b501647c253ca1e42277795eca7ed15851a218b20294275b45d67f`, MIT) |
| HF Base Checkpoint (if P3 GPU LoRA needed) | `C:\Users\Bunny\AppData\Local\axo-slm\base_hf\Qwen3-0.6B` (`c1899de289a04d12100db370d81485cdf75e47ca`) | Present | Offline cached locally |
| GPU Training Venv | `C:\Users\Bunny\AppData\Local\axo-slm\training\.venv\Scripts\python.exe` | `torch 2.6.0+cu124` | `CUDA = True` (`NVIDIA GeForce GTX 1650`, `4095.7 MiB` VRAM) |

---

## 3. Ownership Audit Matrix (Respecting Strict Repository Boundaries)

| Region / File Group | Ownership in `AXO HYBRID /9` | Rationale & Permitted Action |
|---|---|---|
| `backend/app/ai/{slm_verified_normalizer.py, local_slm_extractor.py, local_slm_runtime.py, adaptive_input_router.py, hybrid_offline.py}` | **OWNED_EDITABLE** (established across `/5`–`/7`) | Implement safe `/9` Vietnamese closure (`v3`), runtime/GBNF-retry optimizations (`local-slm-runtime/4`, `HYBRID_V9_LOCAL_SLM`), local-only route helpers (`offline-lab`, `local-shadow`, `local-only-scoped`, `local-only-general`). |
| `backend/app/main.py` & `backend/app/ingestion/unified_input.py` | **OWNED_FOR_LOCAL_ONLY_OPT_IN** (proven in `/5`, `/6`, real-world OCR waves) | Add opt-in local-only route modes (`offline-lab`, `local-shadow`, `local-only-scoped`, `local-only-general`), ensure keyless/no-vision path when local-only mode is active, keep default `HYBRID_ROUTE_MODE = "live"` and `CACHE_VERSION = "145"` intact unless owner approves default switch. |
| `backend/app/ai/{typed_fact_next_extraction.py, function_calling.py, fact_extraction.py, gemini.py}` & `TypedFactNextPayloadV2` schema | **LOCKED_SURFACE** (`BLOCKED_OWNERSHIP` to mutate) | Audit read-only in Phase G (`GEMINI_DEPENDENCY_INVENTORY.json`); preserve bit-identical SHA-256 fingerprints (`33197a45…`, `7ea511a6…`, `485d3834…`, `4bff35bb…`, `fc10ddab…`). |
| `backend/app/simulation/geometry_functions/{registry.py, planner.py, engine.py}` (`Source Gate`, `Planner /26`, `Registry /33`, `Exact Kernel /24`) | **BLOCKED_OWNERSHIP** (established in `/7`–`/8`) | Read-only verification only; never relax `Source Gate` or modify Kernel/Registry/Planner. Any optional Source Gate grammar enhancement goes into `handoff/*.patch` (`git apply --check`). |
| `frontend/**` & external worktree `axo-geometry-library` | **BLOCKED_OWNERSHIP** (separate UI worktree `0fe3873a4`) | Zero edits to `frontend/**`; audit UX/endpoint dependencies read-only and deliver verified `git apply --check` handoff patches + contract tests in `handoff/`. |
| Default Production `HYBRID_ROUTE_MODE` Switch (`"live"` -> `"local-only-*"`) | **REQUIRES_OWNER_APPROVAL_AND_GATES** | Implement genuine opt-in `local-only-scoped` product path on backend; keep default `HYBRID_ROUTE_MODE = "live"` intact unless all G1–G9 gates pass **and** owner cutover sign-off exists (`default_cutover_local_only_scoped.patch` prepared for owner if still `BLOCKED_OWNERSHIP`). |
| `backend/experimental/construction_planner/**` & `/1`–`/8` frozen artifacts | **FROZEN_DO_NOT_TOUCH** | Zero edits; `AXO CONSTRUCTION /2` stays at `Level 2 — BACKEND_INTEGRATION_READY`. |
