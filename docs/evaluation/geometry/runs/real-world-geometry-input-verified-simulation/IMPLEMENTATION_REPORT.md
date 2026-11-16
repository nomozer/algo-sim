# IMPLEMENTATION_REPORT — Nâng Cấp OCR Thực Tế, Hợp Đồng Xác Nhận & Cổng Nguồn (`CACHE_VERSION = 144`)

- **Run ID:** `real-world-geometry-input-verified-simulation`
- **Branch:** `feat/local-first-geometry-understanding`
- **Product Commits:** `6de23b196b711674b2610c8436ef617195947fa7`, `0dcc3840a5e7ff88989911d76a14e3b17e1a4821` (cộng thêm điều kiện truyền `source_provenance` ở `_analyze_once` giữ tương thích 4 tham số cho stub cũ)
- **Measured System:** `120` file đo, `measured_system = 14fb41dbb6c5bbc032c57302be9cc6e0c09023da1f763f16f01f8df5fae28028` (cây sạch trước khi đóng băng ứng viên chính thức)
- **Cache Policy:** `CACHE_VERSION = "144"` · `ROUTE_D_CACHE_POLICY = "144:route-d"` · `semantic_environment_hash = 6233c43c395c9b493d31d3dbb5d0ca952604730f6185cf541d2f179c077f955b`

---

## 1. Các Thay Đổi Mã Nguồn Theo Từng Mô-đun

| Mô-đun | Phiên bản / Thành phần | Thay đổi kỹ thuật cốt lõi | Kiểm chứng khóa |
|---|---|---|---|
| `backend/app/ingestion/local_ocr_worker.py` | `LOCAL_OCR_WORKER_VERSION = "local-ocr-worker/3"` | Giữ padding đối xứng `pad_x` khi crop đọc lại; cập nhật `_strip_edge_bleed` bảo vệ nét phẩy nhỏ góc trên phải (`c["y1"] <= int(0.55 * h)` và `c["w"] <= max(4, int(0.16 * w))` và `(c["x0"] - core_x1) <= max(2, int(0.10 * h))`) trong khi cắt sạch CC nhiễu cao sát biên; bổ sung `has_equals_bars` vào `_analyze_crop_glyph_topology` (tách biệt dấu `=` hai gạch ngang với dấu trừ `-`/`—`); xuất timing chi tiết từng chặng (`decode_ms`, `crop_ms`, `topology_ms`, `latin_rec_ms`, `tess_eng_ms`, `tess_vie_ms`). | `test_worker_edge_bleed_protects_upper_prime_and_detects_equals_bars` + `12/12` `glyph_topology` qua sidecar thật |
| `backend/app/ingestion/local_ocr.py` | `LOCAL_OCR_WORKER_VERSION = "local-ocr-worker/3"` | Đưa `worker_version` vào khóa `_RAW_OCR_CACHE` & `_REREAD_CACHE`; khử trùng lặp tọa độ box ngay trước khi gửi worker và cache từng box độc lập (`_REREAD_CACHE_MAX = 512`, tách biệt khỏi `_RAW_OCR_CACHE_MAX = 32`); truyền `decode_ms` từ worker lên route. | `test_reread_cache_deduplication_and_worker_version_isolation` + `test_local_ocr_worker_lifecycle.py` |
| `backend/app/ingestion/ocr_reconcile.py` | `OCR_RECONCILE_VERSION = "layout-aware-ocr-reconcile/3"` | `_detect_choice_bands` chạy trước `in_fig` và bắt buộc dấu câu rõ (`A.`, `B)`, ...) để nhãn đỉnh ngang `D/A/C/B` trong hình không mở nhầm dải đáp án; giữ dòng văn xuôi thường (`_has_prose_words`) và dòng trắc nghiệm (+ từ Tesseract căn gióng) ngoài `diagram_tokens`; mở rộng `_split_glued_words` (`phng(A'BC)`, `ABCD.A'B'C'D'có`, `⊥(ABCD)`, `AA'=`, `BC(`, `B,SA` trong khi bảo toàn bẫy `S,ABCD`) và `_format_unit_superscripts` (`12(cm2) -> 12(cm²)`); thêm `_compatible_horn_or_junk` (`tir -> từ`, `lλn -> lần`), đồng thuận có dấu (`đang`), `_verify_base_plus_glyph_topology` cho `=` (`has_equals_bars`), đối chiếu đồng hình serif chữ hoa (`4->A, 8->B, "->'`), kiểm số họ đúng trong `tie` (`(SBA)` vs `(S84)`), giữ cấu trúc span trên dòng chọn đáp án, mở rộng `_SHARED_CORRUPTION_RE_EXTENDED` (`(4BC)`, `S.4BC`, `S.A8CD`) và bẫy ngữ cảnh góc `4BC = 30°`. | `test_figure_prose_choice_separation_and_diagram_label_safety` + `test_equals_topology_upper_homoglyph_and_negative_safety_guards` + `0` false auto-accepts trên mọi tập |
| `backend/app/ingestion/local_ocr_route.py` | `LOCAL_OCR_ROUTE_VERSION = "local-ocr-route/2"` | Giải mã ảnh PIL một lần duy nhất trong `review_items` (`_crop_data_url_img`); đưa `decode_ms`, `tesseract_ms`, `rapidocr_ms`, `reconcile_only_ms`, và `reread_breakdown` vào `rec["timing"]`. | `test_image_first_local_ocr.py` |
| `backend/app/ingestion/unified_input.py` | `confirmation_contract_version = "ocr-confirmation-provenance/1"` | Bổ sung `confirmation_contract_version`, `raw_ocr_text_sha256`, `prepared_text_sha256`, `prepared_region_sha256` vào provenance của cả `_local_ocr_outcome` lẫn nhánh Vision `_process_normalized_visual_page`. | `test_image_first_local_ocr.py` + `REAL_WORLD_END_TO_END_EVALUATION.json` |
| `backend/app/main.py` | `verified-input-provenance/1`, `CACHE_VERSION = "144"` | Thêm `InputSourceProvenance` tùy chọn trên `InputPayload`, hàm `build_verified_input_provenance` tự động hạ cấp các khai báo đã chỉnh tay so với `raw_ocr_text_sha256` về `*_student_confirmed` với `counted_as_unmodified_auto_ocr = False`; đính `input_provenance` lên bản sao phản hồi HTTP của `_analyze_hybrid_route` (không ghi đè dòng cache DB chung); nâng `CACHE_VERSION = "144"` (`ROUTE_D_CACHE_POLICY = "144:route-d"`) vô hiệu hóa cache `143:route-d`. | `test_confirmation_provenance_edited_cache_key_and_144_invalidation` |
| `backend/app/simulation/geometry_functions/registry.py` | `_cac_moc_cau` (`@functools.lru_cache`) | Thêm `_KHUYET_CHAM_MO_CAU`, `_KHUYET_CHAM_TU_CHUI`, `_cac_moc_cau` và cập nhật `_cau_chua` / `_bien_cau` nhận diện ranh giới câu hỏi viết hoa khuyết dấu chấm (như `"... AB = 2 Khoảng cách từ ..."` ở `vmmu_r513`), đồng thời chặn tách nhầm sau gạch đầu dòng/tiêu đề (`a)`, `1)`, `Câu 4:`) hoặc mệnh đề điều kiện/chứng minh (`Nếu AB = 2 Khoảng cách ...`). | `test_source_gate_missing_period_alignment_and_vision_fallback_mock` + `test_local_geometry_parser.py` |

---

## 2. Bất Biến Kiến Trúc Được Bảo Toàn Tuyệt Đối

1. **Khóa 4 bề mặt trích xuất (`locked_surfaces.all_match = true`):**
   - `function_calling`: `7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25`
   - `fact_extraction_flat`: `485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a`
   - `fact_extraction_v3`: `4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f`
   - `typed_fact_next`: `33197a45e0620d94a669047b47907479d1e7f07b1dc76e7c6abd75ada7a6df14`
2. **Không AI chọn hàm / Không sinh mã riêng theo đề:** `Planner /26` (`geometry-fact-planner/26`), `Registry /33` (`geometry-functions/33`), `Exact Kernel /24` (`geometry-function-engine/24`) và `Adapter /4` giữ nguyên vai trò tất định; `MAX_MEMORY_DECLARATIONS = 32` giữ nguyên (`MG9` tiếp tục fail-closed `IR_MEMORY_BUDGET_EXCEEDED`).
3. **Không chạm sở hữu ngoài phạm vi:** Worktree `D:\Documents\projects\axo-geometry-library` (`FE-2/3/4/6`), `frontend/public/favicon.svg`, `H-1`, `W2`, và `W3` giữ nguyên `0` sửa đổi.
4. **Hồ sơ mẫu chờ C21 & khóa định danh:** `backend/cache_identity.lock.json` (`lock_cache_identity.py --verify` khớp `CACHE_VERSION = 144`) và `{k1,r1,s2}-owner-approval.template.json` đã đồng bộ sang `measured_system = 14fb41dbb6c5bbc032c57302be9cc6e0c09023da1f763f16f01f8df5fae28028` (`PENDING_OWNER_DECISION`, `paid_project_confirmed: false`).
