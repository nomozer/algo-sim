# FINAL_MASTER_REPORT — Chiến Dịch Đưa Quy Trình Đầu Vào Thực Tế & Mô Phỏng Kiểm Chứng Vào Sử Dụng (`real-world-geometry-input-verified-simulation`)

- **Run ID:** `real-world-geometry-input-verified-simulation`
- **Branch:** `feat/local-first-geometry-understanding` (`ALLOW_LIVE_AI = 0`, `0` lời gọi Gemini/Vision trả phí, `0` hàng `H-1` / `W2` / `W3` niêm phong được mở; chưa merge vào `main` / chưa push)
- **Chuỗi Commit Chiến Dịch (từ `start_head = ce280140bf89ad72e8724993f75f98edcce01e55`):**
  - **Product Stage 1:** `6de23b196b711674b2610c8436ef617195947fa7` (`local-ocr-worker/3`, `layout-aware-ocr-reconcile/3`, `local-ocr-route/2`, `ocr-confirmation-provenance/1`, `verified-input-provenance/1`, Source Gate `_cac_moc_cau`, `CACHE_VERSION = "144"`)
  - **Product Stage 2 (Forward Fix):** `0dcc3840a5e7ff88989911d76a14e3b17e1a4821` (truyền `source_provenance` có điều kiện tại `_analyze_once` giữ tương thích 4 tham số + đồng bộ test pins `144` & C21 templates)
  - **Harness / Eval Commits:** `5e054ce66465fd0eb81b06f8f53d19594e383f21`, `492b8ab29532cd597ed5fd0070486070c88aa886`, `45331efb1ea2c24309bc5124391c03e9fd058f91`
  - **Clean Frozen Candidate:** `d7243a7e544b513a4c24b2c7667b0b50a5ba2943` (`measured_system = 14fb41dbb6c5bbc032c57302be9cc6e0c09023da1f763f16f01f8df5fae28028`, `120` file, `cay_lam_viec_sach = true`, `SEALED = DA_NIEM_PHONG`, `CACHE_VERSION = "144"`, `ROUTE_D_CACHE_POLICY = "144:route-d"`)

---

## Trả Lời 10 Câu Hỏi Nghiệm Thu Bắt Buộc (§14.5)

### 1. Độ chính xác & an toàn OCR thực tế trước / sau can thiệp ra sao?
- **Kiểm chứng nét chữ thuần bitmap (`_analyze_crop_glyph_topology`):** **`12 / 12` ĐẠT** (gồm `10` đầu dò `a²,`/`a2,`/`a³.`/`a3.`/`a√3.`/`aV3.`/`4cm²,`/`⊥`/`L`/`∥` cộng `=` `has_equals_bars=True` và `-` `has_equals_bars=False`), kèm bảo vệ nét phẩy trên phải trong `_strip_edge_bleed`.
- **Ảnh chuẩn tổng hợp (`rendered_positive`):** **`4 / 4` `LOCAL_OCR_ACCEPT -> SERVED`** (`a√6/3`, `4a³√3/3`, `a³/6`, `√6`), `0` lỗi liên tục `Scene3D`.
- **Mẫu đối kháng (`adversarial_negative`):** **`3 / 3` bị chặn (`false_auto_accepts = 0`)** (`neg_inline_a2`, `neg_blurry_crop`, `neg_diagram_ref`).
- **Tập ảnh thực tế `REAL27` (`27` ảnh `anvo25/vmmu`):**
  - Median CER giảm từ **`0.0944`** xuống **`0.0492`** (**giảm `47.9%` tương đối**; `mean CER = 0.0635`); tổng `blocking_uncertain_spans` giảm từ **`81`** xuống **`52`** (**`-35.8%`**).
  - Tách theo phân vùng: `development` (`6` ảnh): median CER `0.0973 -> 0.0495`, blocking `22 -> 16`, `6/6 LOCAL_OCR_REVIEW_REQUIRED`; `frozen_external_evaluation` (`19` ảnh): median CER `0.0944 -> 0.0494`, blocking `58 -> 36`, `19/19 LOCAL_OCR_REVIEW_REQUIRED`; `fresh_external_evaluation` (`2` ảnh): median CER `0.1167 -> 0.0310`, blocking `1 -> 0`, **`1` `LOCAL_OCR_ACCEPT`** (`vmmu_r559`: `CER 0.1929 -> 0.0214`, tự động phục vụ đúng `cos²=1/12` khớp đáp án `B. √3/6`) + **`1` `LOCAL_OCR_REVIEW_REQUIRED`** (`vmmu_r695`: phục vụ đúng `2/3` sau 1 thao tác xác nhận).
  - **`false_auto_accepts = 0`**, **`auto_served_wrong = 0`**.
- **Tập `External16` (`15` ảnh in + `1` ảnh viết tay tách riêng):**
  - `15` ảnh in: median CER giảm từ **`0.0333`** xuống **`0.0270`**, blocking spans `72 -> 69`; **`1` `LOCAL_OCR_ACCEPT`** (`ext_prt_01`, `CER = 0.0`, `SERVED {'q1': 'a³√3/3', 'q2': 'a√21/21'}`), **`12` `LOCAL_OCR_REVIEW_REQUIRED`**, **`2` `needs_selection`**, **`0` `false_auto_accepts`**.
  - `1` ảnh viết tay (`ext_hw_b1_01_hd_a_6043187`): báo cáo riêng ở `external16_handwritten_diagnostic` (`needs_confirmation`, giữ tách biệt trung thực với OCR chữ in).

### 2. Tách vùng đề bài / hình vẽ / đáp án trắc nghiệm & chuyển bài trên ảnh nhiều bài hoạt động thế nào?
- Trong `ocr_reconcile.py` (`layout-aware-ocr-reconcile/3`), `_detect_choice_bands` chạy trước `in_fig` và đòi hỏi dấu câu tường minh (`[.,):]`) để nhãn đỉnh đơn ký tự xếp hàng ngang trong hình (`D/A/C/B`) không khởi tạo nhầm dải trắc nghiệm; dòng văn xuôi thường (`_has_prose_words`) và dòng đáp án (+ từ Tesseract căn gióng) được giữ khỏi `diagram_tokens`.
- Trên `REAL27`: `diagram_classification` đạt `18` `DIAGRAM_REFERENCED_BY_TEXT`, `7` `DIAGRAM_LABELS_ONLY_CONSISTENT`, `2` `DIAGRAM_LABELS_UNMATCHED`.
- Trên `External15`, cả `2` ảnh đa bài đều mở đúng giao diện chọn bài (`status = "needs_selection"`): `ext_prt_08` tách **`4`** dải `page~band-1..4` và `ext_prt_03` tách **`2`** dải `text-p1-1..2`. Giới hạn trung thực được ghi nhận: với `ext_prt_03` có watermark đè lên `ABCD -> ABCE` và `khối -> khói` khiến cả hai bộ OCR không gắn cờ uncertain span tại chữ đó, mô phỏng chỉ sửa span đánh dấu (`0/6` selection tự động giải qua span-only mock) vẫn dừng `REFUSED` an toàn (`0` wrong-served) cho tới khi học sinh sửa tự do ô văn bản.

### 3. Luồng xác nhận tối thiểu của học sinh cải thiện mức độ phục vụ & tiết kiệm thao tác ra sao?
- Trên `REAL27` (`26` ảnh qua `needs_confirmation`): mô phỏng `simulate_student` chỉ chạm đúng các span được hệ thống gắn cờ nâng tổng số critical facts khôi phục từ **`173 / 188` (`92.02%`)** lên **`180 / 188` (`95.74%`)**, giải đúng **`10 / 26`** ca bổ sung (`9` `SERVED_MATCHES_DATASET_KEY` + `1` `SERVED_MODE_A_ADJUDICATED`, **`confirmed_wrong_served = 0`**). Tính cả `1` ca tự chấp nhận (`vmmu_r559`), tổng số ảnh phục vụ cuối tuyến đạt **`11 / 27`** với chỉ **median `2.5` thao tác / ảnh** (`median 0.0` ký tự phải gõ mới nhờ chip chọn/chấp nhận) và tổng **`48` ký tự gõ** trên cả `26` ảnh so với **`5,958` ký tự** nếu phải gõ lại đề (**tiết kiệm `99.19%` lượng phím gõ**).
- Trên `External15`: ngoài `1` ca auto (`ext_prt_01`), xác nhận tối thiểu phục vụ đúng thêm **`4`** ảnh (`ext_prt_02`, `ext_prt_04`, `ext_prt_11`, `ext_prt_12`, **`confirmed_wrong_served = 0`**).

### 4. Hợp đồng xuất xứ đầu vào (`provenance`) & cô lập cache `144` có bảo đảm trung thực không?
- **Có:** `unified_input.py` gắn `confirmation_contract_version = "ocr-confirmation-provenance/1"` với `raw_ocr_text_sha256`, `prepared_text_sha256`, `prepared_region_sha256` ở cả nhánh local OCR và nhánh VLM.
- Tại `backend/app/main.py` (`InputSourceProvenance` & `build_verified_input_provenance` `"verified-input-provenance/1"`): khi văn bản gửi tới `/api/analyze` khác với `raw_ocr_text_sha256`, hệ thống tự động hạ cấp `origin` về `*_student_confirmed` và ép `counted_as_unmodified_auto_ocr = False`; khi không truyền `source_provenance`, `_analyze_once` giữ tương thích 4 đối số tuyệt đối. Phiên bản gốc và phiên bản đã chỉnh tạo `cache_key` Route D tách biệt, và `CACHE_VERSION = "144"` (`ROUTE_D_CACHE_POLICY = "144:route-d"`) vô hiệu hóa hoàn toàn mọi dòng `143:route-d` cũ (`test_confirmation_provenance_edited_cache_key_and_144_invalidation`).

### 5. Hiểu đề tiếng Việt & căn gióng biên `Source Gate` giải quyết vấn đề nào?
- Bổ sung `_cac_moc_cau` trong `registry.py` để `_cau_chua` / `_bien_cau` nhận diện ranh giới câu hỏi viết hoa khuyết dấu chấm (nhưng chặn tách sau bullet/tiêu đề `a)`, `1)`, `Câu 4:` và mệnh đề điều kiện/chứng minh `Nếu ...`).
- Kết quả trực tiếp trên **`vmmu_r513`**: trước đây bị kẹt ở `503 LIVE_AI_DISABLED` do mất ranh giới câu trước `Khoảng cách`; nay đạt **`LOCAL_PARSE_COMPLETE -> REFUSED MISSING_DIMENSION`** kèm chứng chỉ kiểm toán **`determinacy_audit.status = UNPROVED_DUE_TO_CAPABILITY_GAP`**!
- Toàn tập `REAL27_TEXT`: **`18 / 27` `SERVED` (`wrong_served = 0`)**, `3` ca Mode A (`vmmu_r258`, `vmmu_r498`, `vmmu_r559`), `9` ca từ chối minh bạch theo từng tầng (`6` parser/typed-fact, `2` kernel/source-gate `r266`/`r513`, `1` non-convex/out-of-scope `r475`).

### 6. Năng lực tự chọn & tổ hợp hàm hình học của `Planner /26` được giữ vững thế nào?
- Tất cả giữ nguyên **100% ở mức đỉnh** với **`0` lượt AI chọn hàm** và **4 bề mặt trích xuất khóa cứng khớp SHA-256**:
  - `NC-1..21` Gold `TypedFactNext /2`: **`21 / 21`** · `NC-1..21` Tiếng Việt tự nhiên (NL): **`21 / 21`** (`p50 = 28.949 ms`, `p95 = 71.206 ms`, `0` provider calls).
  - Ca phủ định tự hành (`autonomous_negatives`): **`11 / 11` (`0` false served)**.
  - `A4` `contains_points(@id)` & depth bound: **`6 / 6` ĐẠT**.
  - `reasoning_matrix` (72 ca): **`61 / 62` pos + `10 / 10` neg (`0` false served)** (`p50 = 147.331 ms`, `p95 = 590.719 ms`, peak `2027.56 KiB`), `MG9` planner `33 <= 48` (`21` pruned), fail-closed tại `IR_MEMORY_BUDGET_EXCEEDED` (`34 > MAX_MEMORY_DECLARATIONS = 32`).
  - `r1_probe` (19 ca): **`13 / 13` pos + `6 / 6` neg (`0` false served)**.
  - Bộ phát triển lộ thiên: `dev37 = 30 / 37`, `comp112 = 66 / 112`, `probes39 = 23 / 39`, `0` false served trên tập phủ định.

### 7. Tính đúng toán học, `Scene3D`, và fallback Vision ngoại tuyến được kiểm chứng ra sao?
- **`total_scene3d_continuity_errors = 0`** trên toàn bộ mọi cảnh phục vụ ở cả luồng text, OCR và xác nhận.
- **`mode_a_trig_no_answer_leak = true`**: `output-policy/1` Mode A giữ nguyên `numeric_answer_shown = false` và `numeric_source_goal = "NOT_ANSWERED"` cho mục tiêu dựng/lượng giác.
- **Fallback Vision mô phỏng offline:** `AIR.route_image_or_prepare_outcome` với mock `extraction_method="vlm"` đi qua `VISION_THEN_LOCAL_DETERMINISTIC -> SERVED {'q1': 'a³√3/3'}` (`0` lượt gọi `TypedFactNext`, `0` lỗi liên tục).

### 8. Độ trễ theo từng chặng (cold vs warm `p50` / `p95`) & tối ưu cache đạt mức nào?
Đo thực tế trên `REAL27` (`27` ảnh, 1 event loop chuẩn hóa trên CPU host):
- **Cold end-to-end:** **`p50 = 2220.49 ms`**, **`p95 = 4039.29 ms`** (`mean = 2371.86 ms`).
  - Phân rã từng chặng (`p50 / p95 ms`): `normalize = 38.08 / 85.67`, `region_detect = 73.30 / 176.89`, `decode = 7.46 / 14.33`, `tesseract = 225.46 / 402.98`, `rapidocr = 1379.16 / 3434.03`, `reconcile_only = 41.70 / 95.70`, `reread = 336.76 / 1151.84`, `cold_prepare = 2142.12 / 3996.71`, `solve = 8.01 / 171.65`. Nút thắt chủ yếu là `rapidocr` (~`62%` `cold_prepare`).
- **Warm end-to-end (khi chạm `_RAW_OCR_CACHE(32)` + `_REREAD_CACHE(512)` đã khử trùng box):** **`p50 = 209.69 ms`**, **`p95 = 433.43 ms`** (**tăng tốc `10.6x` ở p50**, với `warm_prepare = 176.49 / 354.54 ms`).

### 9. Kết quả trên các tập ảnh ngoài chưa đụng tới (tách biệt hoàn toàn khỏi tập tuned) ra sao?
- **`new_external_12` (`12` ảnh MIT `anvo25/vmmu`):** **`12 / 12` `LOCAL_OCR_REVIEW_REQUIRED`** (`median CER = 0.0686`, **`0` `false_auto_accepts`**); xác nhận tối thiểu phục vụ đúng **`new_ext_05_vmmu_full_r411 -> cos²=1/2`** (khớp exact key `45°` qua `EVI.same_value`), **`confirmed_wrong_served = 0`**, cold prepare `p50 = 1969.45 ms`.
- **`new_image_corpus_8` (`8` ảnh, tách riêng `development` [2] vs `frozen_external_evaluation` [6]):**
  - `development` (`2` ảnh): `2/2 REVIEW_REQUIRED`, `median CER = 0.1376`, `0` wrong-served, cold prepare `p50 = 2270.61 ms`.
  - `frozen_external_evaluation` (`6` ảnh): `6/6 REVIEW_REQUIRED`, `median CER = 0.0698`, `critical_facts = 21/28`, `0` wrong-served; qua xác nhận tối thiểu, **`new_vmmu_full_r446` được phục vụ `SERVED {'q1': '√3/3'}`** (`1` edit `4, -> A,`, `2` ký tự gõ, `12` đối tượng `Scene3D`, `0` lỗi liên tục), cold prepare `p50 = 1981.49 ms`.

### 10. Toàn bộ cổng hồi quy Gate G và giới hạn trung thực hiện hành là gì?
- **Full Backend Pytest (`ALLOW_LIVE_AI=0`, OCR vars unset):** **`14,866 passed, 7 skipped, 3 deselected, 12 xfailed, 0 failed in 654.48s (0:10:54)`**.
- **Frontend Wave (`npm --prefix frontend run test:wave`):** **`142` files / `2,062` tests PASSED (`69.53s`), `tsc -b OK`, `vite build OK (4.70s)`**.
- **Các script kiểm chuẩn trên `d7243a7e5`:**
  - `replay_demo_cases.py`: **`5/5`** (`REDUCED_CHAIN_CASES = 1/1`)
  - `audit_demo_crash_surface.py`: **`6/6`** (`khop = true`, `nem = false`)
  - `export_hybrid_preview_fixtures.py --verify docs/evaluation/geometry/runs/dimension-aware-verified-construction/fixtures-dimension-aware`: **`41` verified, `problems = []`**
  - `lock_cache_identity.py --verify`: **MATCH** (`CACHE_VERSION = 144`, `6233c43c395c9b49...`)
  - `freeze_evaluation_candidate.py --verify`: **MATCH** (`120` file, `14fb41dbb6c5bbc032c57302be9cc6e0c09023da1f763f16f01f8df5fae28028`, `cay_lam_viec_sach = True`, `SEALED = DA_NIEM_PHONG`)
- **Giới hạn & Trạng thái Cổng Trung Thực (bảo toàn 100%):**
  - `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (`0` hàng H-1 niêm phong mở)
  - `INDEPENDENT_GENERALIZATION = NOT_MEASURED` (`W2`/`W3` không mở)
  - `REAL_STUDENT_USABILITY = NOT_MEASURED`
  - `PHYSICAL_LOW_END = NOT_MEASURED`
  - `K-1 / S-2 / R-1 = PENDING_OWNER_DECISION` (`paid_project_confirmed: false`, template đã cập nhật sang `14fb41dbb6c5bbc0...`)
  - `FE-2 / FE-3 / FE-4 / FE-6 = BLOCKED_OWNERSHIP` (`D:\Documents\projects\axo-geometry-library` nguyên vẹn `0` thay đổi)
  - `PUBLICATION_HEAD = BLOCKED_PENDING_OWNER_REVIEW`

---

## Bảng Chứng Từ & Hàm Băm SHA-256 (Các Tạo Tác Anh Em Trong Thư Mục Run)

> Quy ước chống vòng lặp tự tham chiếu: bảng dưới đây liệt kê byte và SHA-256 của mọi tệp anh em trong run (ngoại trừ chính `FINAL_MASTER_REPORT.md` và `run.json`); `run.json` ghi nhận đầy đủ SHA-256 & dung lượng cho toàn bộ tệp kể cả `FINAL_MASTER_REPORT.md`.

| Tệp (`docs/evaluation/geometry/runs/real-world-geometry-input-verified-simulation/...`) | Kích thước (bytes) | SHA-256 |
|---|---:|---|
| `REAL_WORLD_END_TO_END_EVALUATION.json` | 504,834 | `b8f60a701391b1a195e1962e4342453c3ed33a3bfbf9d5d6d21788f114ce23f9` |
| `REAL_WORLD_INPUT_BASELINE.md` | 6,059 | `631d73cb58276db466e4b1695b7883141e04abca36b8f6166e5dda0a5d5fe60a` |
| `IMPLEMENTATION_REPORT.md` | 7,095 | `b3574e99e5d865816ecda127e1767cec90a6e8c8853586dbd18bfa460fccb1f5` |
| `SCENE3D_AND_FRONTEND_HANDOFF.md` | 6,159 | `cd357911062615fe9e5a0850431d8d0369be587cf85b1871723a946546192836` |
| `pending_template_refresh.json` | 3,300 | `715ddaf657bb816f9b41aea680138882602e7cd9302e7972ac93504cf4d925a9` |
| `logs/prior-k1-owner-approval.template.json` | 782 | `8049ab57551e99d7e151d12f279dd1ce1cb7dcd36261bc519f4a305410bf93db` |
| `logs/prior-r1-owner-approval.template.json` | 782 | `bbb22f8b01e61efe880847aeea5e6401ea11f09680f5467b49ee1c3ece30cfa9` |
| `logs/prior-s2-owner-approval.template.json` | 782 | `68542854b25825929e2febbff408a9a095479e78caff2a28e8244fa23ddc5947` |
| `tools/evaluate_real_world_campaign.py` | 62,360 | `22197267bb1aad6b1a640a1ec5a98711b3e27c93d843c48602b0b5cb77139c45` |
