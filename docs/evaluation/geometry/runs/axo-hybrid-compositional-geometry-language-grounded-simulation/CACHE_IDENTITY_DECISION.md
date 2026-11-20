# Cache Semantic Identity Decision (`CACHE_VERSION` 146 → 147)

**Quyết định:** Tăng `CACHE_VERSION` từ `"146"` lên `"147"` (`ROUTE_D_CACHE_POLICY = "147:route-d"`) tại `backend/app/main.py` và khóa lại `backend/cache_identity.lock.json` (`semantic_environment_hash = 16838af02af616f4…`).

## Lý do bắt buộc phải bump

1. **Thay đổi quyết định phân tích & phục vụ trên cùng văn bản đầu vào:**
   - **Parser cục bộ (`local-geometry-parser/3`, `compositional-clause-analyzer/1`):** xử lý câu mở bài phức hợp lồng ghép, tách đích nội tuyến và bổ sung đọc tiền đề (`S15`, `S21`, `S28`, hình thoi/bình hành `ABCD cạnh a`, `Q02`, `Q05`), cũng như phân loại sớm `LOCAL_PARSE_AMBIGUOUS` đối với yêu cầu mô phỏng mơ hồ không nêu `"tính"` (`A3`).
   - **SLM Extractor & Grounding Validator (`local-slm-extractor/6`, `slm-grounding-validator/6`):** phân đoạn mệnh đề phức hợp có dải tiêu đề/meta, GBNF khoảng cách/chiều cao hình khối & đỉnh lăng trụ/chóp/tứ diện, trích xuất mệnh đề `"Cho ..."` lồng và ánh xạ nguồn không dấu (`_orig_quote_slm`).
   - **Source Gate (`geometry-functions/33`):** lọc cụm không cần tính (`_CUM_KHONG_CAN_TINH`), tách meta cuối đề (`_kiem_vung_tien_de`), chấp nhận danh từ `"đáy"` và cụm không dấu khoảng cách (`_BU_DAU_PHRASE_MAP`).
   - **Cổng miền & Hiển thị Scene3D (`V11-VIS-1`):** phát hiện miền tiếng Việt không dấu tại `domain_profile.py` và sửa căn khung camera/nhãn ban đầu trong `frontend/src/simulations/domains/geometry/scene3d-view.tsx`.
2. **Bảo đảm cách ly hàng cache `146:route-d`:** Các bản ghi `SimulationCache` lưu dưới `146:route-d` được phát lại trước parser/Source Gate nếu không tăng `CACHE_VERSION`; nâng lên `147:route-d` buộc mọi hàng cũ `146:route-d` phải MISS và dựng lại dưới code /12. Ngoài ra `build_local_slm_cache_identity` tách khóa bộ nhớ SLM nhờ thay đổi `parser_version` (`local-geometry-parser/3`) và `grounding_policy_version` (`slm-grounding-validator/6`).

## Bằng chứng kiểm chứng

- **`backend/tests/geometry/test_cache_v12_compositional_invalidation.py`:**
  - Khẳng định `CACHE_VERSION == "147"`, `ROUTE_D_CACHE_POLICY == "147:route-d"`, `LOCAL_GEOMETRY_PARSER_VERSION == "local-geometry-parser/3"`, `LOCAL_SLM_EXTRACTOR_V9_VERSION == "local-slm-extractor/6"`, `SLM_GROUNDING_VALIDATOR_V9_VERSION == "slm-grounding-validator/6"`, `COMPOSITIONAL_CLAUSE_ANALYZER_VERSION == "compositional-clause-analyzer/1"`.
  - Kiểm chứng `build_local_slm_cache_identity` đổi hash 64 hex khi thay `parser_version` hoặc `grounding_policy_version` từ `/11` sang `/12`.
  - Kiểm chứng hàng sentinel giả mạo ghi dưới `"146:route-d"` bị MISS khi gọi `POST /api/analyze` (`HYBRID_ROUTE_MODE=local-only-scoped`) và được tính lại thành `"SERVED"` dưới `"147:route-d"`.
- **`backend/scripts/lock_cache_identity.py --verify`:** khớp `CACHE_VERSION 147`, `semantic_environment_hash = 16838af02af616f4…`.
- **`pytest`:** `backend/tests/test_cache_*.py`, `backend/tests/test_api.py`, `backend/tests/geometry/test_v12_*.py`, `backend/tests/geometry/test_cache_v12_compositional_invalidation.py`, `backend/tests/geometry/test_hybrid_cutover_verification.py`, `backend/tests/semantic_program/test_point_initialization_contract.py` → **160 passed, 0 failed**.
- **`docs/CURRENT_STATE.md`:** cập nhật bảng `DANH TÍNH KHO MÃ` lên `**147**`, khớp `backend/tests/test_current_state_identity.py`.
