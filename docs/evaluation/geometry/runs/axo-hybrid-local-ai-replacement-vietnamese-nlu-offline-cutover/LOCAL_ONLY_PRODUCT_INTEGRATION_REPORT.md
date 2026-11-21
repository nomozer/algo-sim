# AXO HYBRID /9 — Phase P7 Local-Only Product Integration Report

> **Modules Modified:** [`hybrid_offline.py`](../../../../../backend/app/ai/hybrid_offline.py), [`main.py`](../../../../../backend/app/main.py), [`unified_input.py`](../../../../../backend/app/ingestion/unified_input.py)  
> **Blocked Paths Edited:** `0` (`frontend/**`, `registry.py`, `planner.py`, `engine.py`, `backend/experimental/construction_planner/**`, and all 4 locked Gemini surfaces unchanged)

---

## 1. Integrated Capabilities & Guarantees

1. **Preserved Cloud Default & Cache Identity:**
   - Unset `HYBRID_ROUTE_MODE` continues resolving to `"live"` (`CACHE_VERSION = "145"` unchanged).
   - Existing `test_api.py` passes **`14 / 14`** after all Step 4 edits.
2. **Product Local-Only & Shadow Modes (`HYBRID_ROUTE_MODES`):**
   - `offline-lab`, `local-only-scoped`, `local-only-general`, and `local-shadow` registered alongside existing `live`, `staging-replay`, `local-first`, and `local-slm`.
   - `local-only-general` fails closed with HTTP `503 LOCAL_ONLY_GENERAL_NOT_APPROVED` unless `AXO_ALLOW_GENERAL_LOCAL_CUTOVER=1` is set.
   - `local-shadow` executes `LiveHybridRun` authoritatively while attaching non-blocking `route_d["local_shadow"]` telemetry (`slm_status`, `agreed_with_live`, `slm_ms`).
3. **Keyless Readiness Endpoint (`GET /api/health`):**
   - Retains `"hasKey": bool(os.getenv("GEMINI_API_KEY"))` unchanged.
   - Adds `"routeMode"`, `"localOnlyMode"`, `"localSlmReady"`, `"localSlmModel"`, `"extractionBackend"`, `"aiAvailable"`, and `"local_ai_ux"`.
   - Under `local-only-scoped` with no `GEMINI_API_KEY`: `hasKey=False`, `localOnlyMode=True`, `localSlmReady=True`, `localSlmModel="qwen3-0.6b-axo-v9-q4_k_m"`, `extractionBackend="local_slm_v9"`, `aiAvailable=True`, `local_ai_ux.ux_state="READY_OFFLINE"`.
   - Under empty `LOCAL_SLM_CACHE_DIR`: `localSlmReady=False`, `aiAvailable=False`, `local_ai_ux.ux_state="MODEL_NOT_PROVISIONED"`.
4. **Unified Input & Vision Gating (`/api/image/extract`, `/api/input/prepare`):**
   - Text, `.docx`, and clean PDF text layers succeed locally with `vlm_calls = 0`, `used_vlm = False`.
   - `/api/image/extract` and image inputs requiring cloud VLM fail closed under local-only modes with HTTP `503 LOCAL_ONLY_CLOUD_VISION_DISABLED`.

---

## 2. Automated Test Verification

Executed `pytest backend\tests\geometry\test_local_only_product_and_network_isolation.py -q`:
- **`5 passed in 12.05s`**:
  1. `test_default_route_remains_live_and_general_cutover_is_gated` (`PASS`)
  2. `test_health_preserves_has_key_and_exposes_local_only_readiness` (`PASS`)
  3. `test_local_only_scoped_network_isolation_and_cloud_vision_block` (`PASS`)
  4. `test_local_shadow_mode_keeps_live_authoritative` (`PASS`)
  5. `test_all_10_vietnamese_ux_states_clean` (`PASS`)
