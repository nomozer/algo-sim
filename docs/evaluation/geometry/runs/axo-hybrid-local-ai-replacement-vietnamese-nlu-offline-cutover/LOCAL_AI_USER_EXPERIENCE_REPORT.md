# AXO HYBRID /9 — Phase P8 Local AI Learner UX Report

> **Implementation:** `build_local_ai_ux_descriptor(...)` in [`hybrid_offline.py`](../../../../../backend/app/ai/hybrid_offline.py) + `main.py` local-only responses  
> **Frontend Handoff:** [`frontend_local_ai_status_and_keyless_ux.patch`](./handoff/frontend_local_ai_status_and_keyless_ux.patch) (`git apply --check` passed; `0` direct edits to `frontend/**`)

---

## 1. Ten-State Clean Vietnamese UX Mapping

Verified by `test_all_10_vietnamese_ux_states_clean` (`backend/tests/geometry/test_local_only_product_and_network_isolation.py`) checking zero leakage of internal tokens (`GEMINI_API_KEY`, `ALLOW_LIVE_AI`, `REASON_CODE`, `LOCAL_`, `Traceback`, `.py`, `.gguf`, `http://`, `503`):

| `ux_state` | Trigger Condition | `learner_title` |
| --- | --- | --- |
| `READY_OFFLINE` | `/api/health` w/ `localOnlyMode=True` & `localSlmReady=True` | `Sẵn sàng dựng hình ngoại tuyến` |
| `WARMING_UP_MODEL` | `warming_up=True` or `LOCAL_SLM_WARMING_UP` | `Đang khởi động bộ đọc đề ngoại tuyến` |
| `SERVED_OFFLINE_VERIFIED` | HTTP `200` & `route_d.status == "SERVED"` | `Đã dựng hình và kiểm chứng thành công` |
| `CLARIFICATION_NEEDED` | Ambiguous/ungrounded refusal (`AMBIGUOUS_FACT`, etc.) | `Cần viết rõ hơn một phần diễn đạt trong đề` |
| `MISSING_GEOMETRY_DATA` | `insufficient_specification` / `MISSING_DIMENSION` / `UNDERDETERMINED_POINT` | `Đề bài còn thiếu dữ kiện để dựng hình duy nhất` |
| `CONTRADICTORY_GEOMETRY_DATA` | `geometry_generation_failed` / `INCONSISTENT_FACTS` / `DEGENERATE_SOLID` | `Giả thiết hình học có mâu thuẫn hoặc suy biến` |
| `OUT_OF_SUPPORTED_SCOPE` | `status == "unsupported"` / `out_of_scope` / `capability_gap` | `Đề bài nằm ngoài phạm vi hỗ trợ hiện tại` |
| `MODEL_NOT_PROVISIONED` | Missing/invalid GGUF, `MODEL_RUNTIME_UNAVAILABLE`, or unapproved `local-only-general` | `Bộ đọc đề ngoại tuyến chưa sẵn sàng` |
| `RUNTIME_BUSY_OR_TIMEOUT` | HTTP `502`/`503`/`504` / `LOCAL_SLM_BUSY` / `LOCAL_SLM_TIMEOUT` | `Hệ thống xử lý trên máy đang bận` |
| `CLOUD_OCR_DISABLED_OFFLINE` | `LOCAL_ONLY_CLOUD_VISION_DISABLED` (`/api/image/extract`, image `/api/input/prepare`) | `Chế độ ngoại tuyến không đọc ảnh trực tuyến` |
