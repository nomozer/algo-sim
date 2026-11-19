# AXO HYBRID /9 — Phase P7 Local-Only Production Routing Architecture

> **Campaign:** `AXO HYBRID /9 — Local AI Replacement, Vietnamese NLU Generalization & Offline Production Cutover`  
> **Cache Identity Preservation:** `CACHE_VERSION = "145"` unchanged · Default `HYBRID_ROUTE_MODE = "live"` unchanged until owner cutover

---

## 1. Supported Route Modes (`HYBRID_ROUTE_MODES` in `backend/app/main.py`)

| Mode (`HYBRID_ROUTE_MODE`) | Purpose | Network / Key Requirement | Extraction Backend | Notes |
| --- | --- | --- | --- | --- |
| `live` (default) | Official cloud-backed Hybrid `/4` | Requires `GEMINI_API_KEY`, `ALLOW_LIVE_AI != 0` | `live_gemini` (`typed-fact-next/2`) | Unchanged production default |
| `staging-replay` | Deterministic offline replay | None | `staging_replay` (`HYBRID_REPLAY_CORPUS`) | Simulated test replay |
| `local-first` | Deterministic local parser w/ Gemini fallback | Gemini only when local parser incomplete | `local_first_with_cloud_fallback` | Legacy `/4` opt-in |
| `local-slm` | `/6`–`/7` compatible local SLM route | None | `local_slm_v7` | `closure_mode="v7"`, `HYBRID_V7_LOCAL_SLM` |
| **`offline-lab`** | Offline controlled lab evaluation | **None (`api_key=None`)** | **`local_slm_v9`** (`AxoV9-Q4_K_M`, `v9`/`v3`) | Zero cloud fallback; full Source Gate & Kernel `/24` |
| **`local-only-scoped`** | Scoped production local-only operation (P0–P8) | **None (`api_key=None`)** | **`local_slm_v9`** (`v9-active` -> `qwen3-0.6b-axo-v9-q4_k_m`) | Cloud Vision blocked (`503 LOCAL_ONLY_CLOUD_VISION_DISABLED`); DOCX/PDF-text local |
| **`local-only-general`** | General keyless local cutover (gated) | None **+ requires `AXO_ALLOW_GENERAL_LOCAL_CUTOVER=1`** | **`local_slm_v9`** | Fails closed `503 LOCAL_ONLY_GENERAL_NOT_APPROVED` unless flag set |
| **`local-shadow`** | Dual shadow telemetry mode | Live Gemini authoritative + best-effort local SLM | `live_gemini_with_local_shadow` | Attaches non-blocking `route_d["local_shadow"]` (`slm_status`, `agreed_with_live`, `slm_ms`) |

Unrecognized values (including `off`) fail closed with HTTP `503 INVALID_HYBRID_ROUTE_MODE` (`Cache-Control: no-store`).

---

## 2. Two-Tier Local Execution & Cache Namespace Isolation

1. **Tier 1 — Deterministic Vietnamese Closure + Local Parser (`0` SLM calls):**
   - Verified Normalizer `v3` (`slm-verified-normalizer/3`, span-audited rules `VN01`–`VN11`) + `local_geometry_parser` (`LOCAL_PARSE_COMPLETE`).
   - Serves directly through Exact Kernel `/24` (`LOCAL_DETERMINISTIC_PARSER` or `LOCAL_PARSER_AFTER_V3_NORMALIZER`), bypassing SLM inference (`p50 ~34 ms`).
2. **Tier 2 — Grounded Compact Clause Extraction (`AxoV9-Q4_K_M`):**
   - Executed by `prepare_local_slm_v9_hybrid` (`hybrid_offline.py`) -> `route_text_input_local_slm(..., closure_mode="v9", normalizer_version="v3")` (`adaptive_input_router.py`) -> `run_local_slm_extraction` (`local_slm_extractor.py`).
   - Enforces GBNF clause-scoped grammar, `max_tokens = 256`, `-b 512 -ub 512`, Source Gate (`registry.kiem_nguon`), `multi_goal_status` completeness (`REQUEST_NOT_ANSWERED`), Exact Kernel `/24`, and `Adapter /4`.
3. **Cache Isolation (`HYBRID_V9_LOCAL_SLM`):**
   - `/9` cache keys use `LOCAL_SLM_CACHE_V9_NAMESPACE = "HYBRID_V9_LOCAL_SLM"` and `LOCAL_SLM_RUNTIME_V9_VERSION = "local-slm-runtime/4"`, preventing cross-contamination with `/7` (`HYBRID_V7_LOCAL_SLM`), while keeping global `CACHE_VERSION = "145"` intact and deduplicating concurrent identical requests via `_V9_INFLIGHT_EVENTS`.

---

## 3. Cloud Vision & Ingestion Boundaries in Local-Only Modes

- In `main.py` (`LOCAL_ONLY_HYBRID_MODES`): `_analyze_once` and `/api/input/prepare` force `api_key = None` regardless of `GEMINI_API_KEY` or `ALLOW_LIVE_AI`.
- Text input, `.docx` documents (`_extract_docx_text`), text-layer PDFs (`extract_pdf_structured`), and verified local OCR (`extraction_verified=True`) operate with `vlm_calls = 0`.
- `/api/image/extract` and image/scanned-PDF fallbacks requiring cloud VLM fail closed via `LocalOnlyCloudVisionDisabledError` -> HTTP `503 LOCAL_ONLY_CLOUD_VISION_DISABLED` (`local_ai_ux.ux_state = "CLOUD_OCR_DISABLED_OFFLINE"`).

---

## 4. Health Contract Extension (`/api/health`)

- Preserves legacy `hasKey: bool(os.getenv("GEMINI_API_KEY"))` truthfully (`test_api.py` compatibility).
- Adds additive readiness fields: `routeMode`, `localOnlyMode`, `localSlmReady`, `localSlmModel`, `extractionBackend`, `aiAvailable`, and `local_ai_ux` (when `localOnlyMode=True`).
