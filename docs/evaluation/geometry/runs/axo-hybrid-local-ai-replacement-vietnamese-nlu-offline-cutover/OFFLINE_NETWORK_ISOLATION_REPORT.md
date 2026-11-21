# AXO HYBRID /9 — Phase P8 Offline Network Isolation Audit Report

> **Verifier:** [`verify_offline_network_isolation_v9.py`](../../../../../backend/scripts/verify_offline_network_isolation_v9.py) + [`test_local_only_product_and_network_isolation.py`](../../../../../backend/tests/geometry/test_local_only_product_and_network_isolation.py)  
> **Hostile Test Environment:** `HYBRID_ROUTE_MODE=local-only-scoped`, `GEMINI_API_KEY="fake-key-unused"`, `ALLOW_LIVE_AI="1"`

---

## 1. Static AST Audit of Local AI Stack

Parsed AST of all 5 local AI runtime/NLU modules checking for cloud LLM SDK imports (`google.genai`, `google.generativeai`, `openai`, `anthropic`, `vertexai`):

| Module | Cloud SDK Imports Found |
| --- | --- |
| `backend/app/ai/local_slm_runtime.py` | `0` (`[]`) |
| `backend/app/ai/local_slm_extractor.py` | `0` (`[]`) |
| `backend/app/ai/adaptive_input_router.py` | `0` (`[]`) |
| `backend/app/ai/slm_verified_normalizer.py` | `0` (`[]`) |
| `backend/app/ai/local_geometry_parser.py` | `0` (`[]`) |

---

## 2. Dynamic Socket & HTTPX Egress Guard Results

With `socket.socket.connect`, `socket.create_connection`, `httpx.Client.request`, and `httpx.AsyncClient.request` patched to fail hard on any non-loopback host (`not in {"127.0.0.1", "::1", "localhost", "testserver"}`), even with a fake `GEMINI_API_KEY` and `ALLOW_LIVE_AI=1`:

- `non_loopback_egress_attempts = []` (`0` attempts)
- `external_ai_calls = 0`
- `gemini_invocations = 0`
- `silent_cloud_fallbacks = 0`

| Trace | Endpoint | HTTP | Route Status | Provider Calls | UX State |
| --- | --- | --- | --- | --- | --- |
| `fastpath` | `/api/analyze` | `200` | `SERVED` | `0` | `SERVED_OFFLINE_VERIFIED` |
| `slm_v9` (`AxoV9-Q4_K_M`) | `/api/analyze` | `200` | `SERVED` (`3a/2`) | `0` | `SERVED_OFFLINE_VERIFIED` |
| `neg_ambig` | `/api/analyze` | `200` | `REFUSED` | `0` | `CLARIFICATION_NEEDED` |
| `oos` | `/api/analyze` | `200` | `unsupported` | `0` | `OUT_OF_SUPPORTED_SCOPE` |
| Cloud Vision endpoints (`/api/image/extract`, image `/api/input/prepare`) | Vision | `503` | `LOCAL_ONLY_CLOUD_VISION_DISABLED` | `0` | `CLOUD_OCR_DISABLED_OFFLINE` |
| DOCX document (`/api/input/prepare`) | Document | `200` | `ready` (`vlm_calls=0`) | `0` | — |
