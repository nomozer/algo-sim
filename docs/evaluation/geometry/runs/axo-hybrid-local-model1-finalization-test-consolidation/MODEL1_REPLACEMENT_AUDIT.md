# AXO HYBRID /13 — Model 1 Replacement Audit (§6.H)

**Branch:** `feat/local-model1-finalization-test-consolidation`  
**Verified at commit:** `787be5445`  
**Mode audited:** `HYBRID_ROUTE_MODE=local-only-scoped`, `ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`  
**Verification suite:** `backend/tests/test_model1_replacement_audit.py` (`1 passed in 3.80s`, `gemini_mod.call_gemini` patched to fail immediately if ever reached)

## 1. Summary Verdict

| Capability / Modality | Endpoint(s) | Local Offline Status | HTTP / Route Result | External Calls | Honest Boundary |
|---|---|---|---|---:|---|
| Vietnamese text NLU (Model 1) | `POST /api/analyze` | **Replaced locally** (`Local Geometry Parser` + `Qwen3-0.6B-AxoV9-Q4_K_M`) | `200`, `route_d.status = SERVED`, `answers.q1 = "4"` | 0 | Scoped 3D solid geometry within `local-only-scoped` |
| Digital DOCX (+ OMML) | `POST /api/input/prepare` -> `POST /api/analyze` | **Local deterministic** (`extract_docx_structured`) | `200`, `prepare = ready` -> `SERVED`, `answers.q1 = "16"` | 0 | Embedded raster diagrams still need Vision outside local-only if OCR is required |
| Digital PDF (text layer) | `POST /api/input/prepare` -> `POST /api/analyze` | **Local deterministic** (`extract_pdf_structured`) | `200`, `prepare = ready` -> `SERVED`, `answers.q1 = "36"` | 0 | Digital text layer only; scanned image-only pages are fail-closed below |
| Raster image / Scanned PDF OCR | `POST /api/input/prepare`, `POST /api/image/extract` | **Fail-closed offline (NOT replaced by local VLM)** | `503 LOCAL_ONLY_CLOUD_VISION_DISABLED`, `Cache-Control: no-store` | 0 | Dual local OCR remains `LOCAL_OCR_DIAGNOSTIC_ONLY`; cloud Gemini Vision is still required outside `local-only-scoped` |
| Runtime health check | `GET /api/health` | **Local metadata** | `200`, `ok = true`, `localOnlyMode = true` | 0 | Reports `localSlmReady` accurately without cloud API key |

## 2. Code Audit Findings

1. **`backend/app/ai/hybrid_offline.py` & `backend/app/ai/adaptive_input_router.py`:** In `local-only-scoped`, `POST /api/analyze` executes `route_text_input_local_slm` (`parse_geometry_problem_locally` -> `slm_verified_normalizer` v3 -> `Qwen3-0.6B-AxoV9-Q4_K_M` via `llama.cpp` -> `Source Gate -> Planner -> Exact Kernel -> Adapter /4`) with zero calls to `app.ai.gemini`.
2. **`backend/app/ingestion/document_reader.py` & `backend/app/ingestion/unified_input.py`:** Clean digital DOCX and digital text-layer PDF extraction run deterministically with `metrics.vlm_calls = 0`.
3. **`backend/app/main.py` & `backend/app/ingestion/image_extraction.py`:** Raster image upload (`POST /api/image/extract`) and image/scan fallback inside `POST /api/input/prepare` still call `app.ai.gemini.call_gemini` in live mode (`gemini-2.5-flash`). Under `local-only-scoped`, both fail closed deterministically with HTTP `503 LOCAL_ONLY_CLOUD_VISION_DISABLED` (`Cache-Control: no-store`) and zero external requests.
