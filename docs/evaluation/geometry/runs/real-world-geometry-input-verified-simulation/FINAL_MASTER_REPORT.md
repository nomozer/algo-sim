# FINAL_MASTER_REPORT — Chiến Dịch Đưa Quy Trình Đầu Vào Thực Tế & Mô Phỏng Kiểm Chứng Vào Sử Dụng (`real-world-geometry-input-verified-simulation`)

- **Run ID:** `real-world-geometry-input-verified-simulation`
- **Branch:** `feat/local-first-geometry-understanding` (`ALLOW_LIVE_AI = 0`, `GEMINI_API_KEY = ""`, `0` lời gọi Gemini/Vision trả phí, `0` hàng `H-1` / `W2` / `W3` niêm phong được mở; chưa merge vào `main` / chưa push)
- **Chuỗi Commit Chiến Dịch (từ `start_head = ce280140bf89ad72e8724993f75f98edcce01e55`):**
  - **Product Stage 1 & 2 (`6de23b196b711674b2610c8436ef617195947fa7`, `0dcc3840a5e7ff88989911d76a14e3b17e1a4821`):** `layout-aware-ocr-reconcile/3`, `local-ocr-route/2`, `ocr-confirmation-provenance/1`, `verified-input-provenance/1`, Source Gate `_cac_moc_cau`, `CACHE_VERSION = "144"`.
  - **Product Stage 3 & Evaluator (`b806e359fcceb268c065013d5cf7fb2ff278f1c1`):** `local-ocr-worker/4` (`pad_x` đối xứng khi crop lại + `_strip_edge_bleed` giữ nét phẩy trên phải), chặn crop-reread overvote (`primary_agrees`), bỏ bypass non-ASCII để `_restore_prose` phục hồi/gắn cờ dấu tiếng Việt, `600º` / `º -> °`, `_CAU_NGAT` ngắt câu dính dấu chấm (`.Tính`), `_MO_DAU_MUC_DE` đầu mục đề (`43. Cho...`), C21 templates đồng bộ, bổ sung chẩn đoán `§4.1`, `§6.2` (Gold `TypedFactNext /2`), `§6.3`, `§9.3`, `§10`.
  - **Clean Frozen Candidate:** `003104fd5a116f38f05fe200d013b7e9ba93a05a` (`product_commit = b806e359fcceb268c065013d5cf7fb2ff278f1c1`, `measured_system = e1c6428ed558a722442e0f32b362fb41d053795a81cf92a4c267d48e2bbd7a04`, `120` file, `cay_lam_viec_sach = true`, `SEALED = DA_NIEM_PHONG`, `CACHE_VERSION = "144"`, `ROUTE_D_CACHE_POLICY = "144:route-d"`).

---

## Trả Lời 10 Câu Hỏi Nghiệm Thu Bắt Buộc (`§14.5`)

### 1. OCR đã đọc ảnh thực tế tốt hơn ở đâu?
- **Chính xác ký tự & giảm nhiễu tranh chấp trên `REAL27` (`27` ảnh `anvo25/vmmu`):**
  - Median CER giảm từ **`0.0944`** xuống **`0.0533`** (**`-43.5%` tương đối**, `mean = 0.0624`). Theo phân vùng: `development (6)` `0.0973 → 0.0474`; `frozen_external_evaluation (19)` `0.0944 → 0.0535`; `fresh_external_evaluation (2)` `0.1167 → 0.0310`.
  - Tổng `blocking_uncertain_spans` giảm từ **`81`** xuống **`44`** (**`-45.7%`**); tỷ lệ khôi phục dữ kiện quan trọng (`critical_facts`) đạt **`175 / 188`** ở bản thô và tăng lên **`182 / 188` (`96.81%`)** sau xác nhận span; `math_token_recall_draft = 0.8658`.
- **An toàn trên đọc lại vùng toán & dấu tiếng Việt:**
  - Khử lỗi cắt biên nét phẩy trên phải & mở `pad_x` (`local-ocr-worker/4`), kiểm tra hình học thuần bitmap đạt **`12 / 12`** (`a²/a³/√/⊥/∥/=/−`).
  - Quy tắc `primary_agrees` chặn hoàn toàn hiện tượng reread crop hẹp tự xác minh đè nhiễu lên `rapidocr` chính xác (`ABCE`, `ABCL`, `4M`, `1B`, `4`), giúp các ca như `vmmu_r247`, `ext_prt_03 #2`, `ext_prt_06`, `ext_prt_07` giữ đúng chữ gốc hoặc cờ rõ cho học sinh xác nhận.
  - Bỏ bypass non-ASCII giúp `_restore_prose` tự sửa lỗi có dấu ngoài từ điển (`"khói" → "khối"`) và gắn cờ mơ hồ dấu (`"cậu"` → `AMBIGUOUS_DIACRITIC_RESTORATION`) thay vì cho lọt.
- **`External15` in & tập ngoài chưa đụng tới:**
  - `External15`: median CER giảm **`0.0333 → 0.0319`**; ảnh đa bài tách đúng dải (`ext_prt_03` `2` bài `text-p1-1..2`, `ext_prt_08` `4` dải `page~band-1..4`).
  - `new_external_12`: median CER **`0.0734`**; `new_image_corpus_8`: `dev = 0.1376`, `frozen = 0.0730` (`22/28` critical facts).
  - Ảnh viết tay `ext_hw_b1_01_hd_a_6043187` được cô lập riêng tại `external16_handwritten_diagnostic` (`cer_after = 2.1228`), không gộp vào OCR chữ in.

### 2. Có bao nhiêu ảnh được tự động chấp nhận đúng?
- **Ảnh chuẩn tổng hợp (`rendered_positive`):** **`4 / 4` (`100%`)** `LOCAL_OCR_ACCEPT → SERVED` (`a√6/3`, `4a³√3/3`, `a³/6`, `√6`), `0` lỗi liên tục `Scene3D`.
- **Ảnh đối kháng (`adversarial_negative`):** **`3 / 3`** bị chặn, **`false_auto_accepts = 0`**.
- **Ảnh in ngoài `External15`:** **`1 / 15`** tự động chấp nhận đúng (`ext_prt_01_hd_q_5259753`, `CER = 0.0`, `SERVED {'q1': 'a³√3/3', 'q2': 'a√21/21'}`, **`0` false auto-accepts**).
- **Ảnh chụp thực tế `REAL27`:** **`0 / 27`** tự động chấp nhận (**`false_auto_accepts = 0`**, `auto_served_correct = 0`). Lý do chủ đích: sau khi vá `_restore_prose` không bỏ qua ký tự có dấu và giữ chặt rào hình vẽ/dấu phẩy, mọi ảnh chụp thực tế có ít nhất `1` rủi ro (`DIAGRAM_FACTS_UNVERIFIED` hoặc `PRIME_DISAGREEMENT` trên `vmmu_r559`) đều được đưa qua bước xác nhận nhanh (`1` thao tác) thay vì chấp nhận mù.
- **Tập ngoài chưa đụng tới (`new_external_12`, `new_image_corpus_8`):** **`0`** tự động chấp nhận, **`0` false auto-accepts**.

### 3. Bao nhiêu ảnh cần xác nhận và vì sao?
- **`REAL27`: `27 / 27` ảnh vào `LOCAL_OCR_REVIEW_REQUIRED` (`§4.1` phân nhóm rõ nguyên nhân, không đánh đồng thành 27 lỗi OCR):**
  - **`20 / 27` (`RECOGNITION_ERROR_NEEDS_CONFIRMATION`):** có sai sót ký tự/ký hiệu toán thực sự (`CER > 0.03` hoặc thiếu dữ kiện quan trọng cần kiểm tra/sửa, vd `vmmu_r254`, `r256`, `r284`, `r460`, `r463`).
  - **`7 / 27` (`GENUINE_DIAGRAM_OR_AMBIGUITY_CONFIRMATION`):** bản OCR chữ tương đối sạch (`CER <= 0.03`), nhưng cần xác nhận hình vẽ (`DIAGRAM_FACTS_UNVERIFIED`: `r247`, `r277`, `r461`, `r476`, `r492`, `r520`) hoặc dấu phẩy đơn (`r559`: `PRIME_DISAGREEMENT`). (`0` ca rơi vào xô chỉ thiếu bằng chứng họ 2 đơn thuần).
- **`External15` (`15` ảnh in):** `1` tự chấp nhận (`AUTO_ACCEPTED_SAFE`), **`12` `needs_confirmation`** (`7` `RECOGNITION_ERROR_NEEDS_CONFIRMATION`, `4` `GENUINE_DIAGRAM_OR_AMBIGUITY_CONFIRMATION`, **`1` `INSUFFICIENT_ACCEPTANCE_EVIDENCE_TEXT_ACCURATE`** là `ext_prt_12` đã đọc đúng `CER = 0.0` nhưng chỉ có 1 họ engine đồng thuận ở 1 span), và **`2` `needs_selection`** (`MULTI_PROBLEM_NEEDS_SELECTION`: `ext_prt_03` và `ext_prt_08`).

### 4. Học sinh phải thực hiện bao nhiêu thao tác để xác nhận?
- Trên **`REAL27` (`27` ảnh `needs_confirmation`):** mô phỏng `simulate_student` chỉ chạm vào các mục được hệ thống gắn cờ tốn **median `2` thao tác / ảnh** (`fresh_external = 1.0`, `dev = 2.0`, `frozen = 2.0`), **median `0` ký tự phải gõ mới** (chủ yếu bấm chip chọn/xác nhận), và tổng cộng chỉ **`48` ký tự gõ** trên cả `27` ảnh so với **`6,098` ký tự** nếu phải gõ lại đề (**tiết kiệm `99.21%` thao tác gõ phím**).
- Trên **`External15` (`12` ảnh `needs_confirmation`):** **median `3.0` thao tác / ảnh**, **median `0.0` ký tự gõ mới**.

### 5. Sau xác nhận, bao nhiêu đề tạo được Verified Scene3D?
- **`REAL27` (`27` ảnh):**
  - Qua xác nhận đúng các span hệ thống gắn cờ (`confirmed_ready_count = 27`): **`13 / 27` (`48.1%`)** phục vụ **`Verified Scene3D`** với **`0` wrong-served** và **`0` lỗi liên tục** (tăng từ `11/27` trước đợt sửa cuối nhờ giải cứu **`vmmu_r247`** [`18` obj, `0` edit] và **`vmmu_r270`** [`13` obj, `0` edit]). Phân rã: `development = 2/6`, `frozen_external = 9/19`, `fresh_external = 2/2`.
  - Tách riêng nhánh fallback chỉnh toàn văn bản (`whole_draft_confirmation_fallback`): có thêm **`5`** ảnh (`r258`, `r284`, `r375`, `r460`, `r463`) dựng được `Scene3D` nếu học sinh tự sửa các lỗi ngoài span đánh dấu (tổng `13 + 5 = 18/27`, khớp trần tuyến văn bản `REAL27_TEXT = 18/27`).
- **`External15` (`15` ảnh in):**
  - Ảnh đơn (`auto + span-confirmed`): **`1 / 15`** auto (`ext_prt_01`) + **`8 / 12`** span-confirmed (`ext_prt_02`, `04`, `05`, `06`, `07`, `09`, `11`, `12` — **gồm `+4` ca mới**: `ext_prt_05`, `06`, `07`, `09`) = **`9 / 15` ảnh đơn tạo được `Verified Scene3D` (`0` wrong)**; `whole_draft_fallback_served = 0`.
  - Chọn bài đa đề (`needs_selection`): **`2 / 6` dải** phục vụ đúng (`ext_prt_03 #1 -> a√2/2` [`0` edit], `ext_prt_03 #2 -> a³/4` [`1` edit], `0` wrong).
- **Tập ngoài chưa đụng tới & Vision offline mock:** `new_external_12` phục vụ `1/12` (`new_ext_05_vmmu_full_r411 -> cos²=1/2`); `new_image_corpus_8` (`frozen`) phục vụ `1/6` (`new_vmmu_full_r446 -> √3/3`); nhánh mock Vision (`extraction_method="vlm"`) đạt **`VISION_THEN_LOCAL_DETERMINISTIC -> SERVED {'q1': 'a³√3/3'}`** (`0` lượt Gemini TypedFact, `0` continuity errors).

### 6. Những đề nào vẫn chưa mô phỏng được?
- **`REAL27` — `9 / 27` không phục vụ ngay cả từ đề chuẩn (`REAL27_TEXT = 18/27 SERVED, 9/27 REFUSED`):**
  - `vmmu_r254`, `vmmu_r277`, `vmmu_r491` (`TYPED_FACT_GAP` — schema/bridge chưa nhận `@id` trong premise, `point_reflection`, điểm trượt tự do không tỉ số `I ∈ BC`);
  - `vmmu_r256` (`SOURCE_GROUNDING_GAP` — lỗi chính tả `"đên"` ở đề gốc; counterfactual `"đến"` phục vụ `a√15/5`);
  - `vmmu_r266` (`KERNEL_EXACT_DOMAIN_GAP` — căn lồng cosin ngoài miền Gram hữu tỉ `ℚ`);
  - `vmmu_r461`, `vmmu_r475` (`INTENTIONALLY_UNSUPPORTED` — quạt tròn gấp nón, nhiều khối cong lồng nhau);
  - `vmmu_r488` (`REGISTRY_GAP` — chưa đo thể tích chóp con `B'.ACC'A'` tách từ lăng trụ, dù lăng trụ gốc phục vụ đúng `a³/2`);
  - `vmmu_r513` (`INSUFFICIENT_SPECIFICATION` — thiếu cạnh `BC/AD`, đã đồng bộ từ chối `MISSING_DIMENSION` kèm `UNPROVED_DUE_TO_CAPABILITY_GAP`).
- **`REAL27` — `5` ảnh đọc được từ văn bản nhưng thất bại ở xác nhận chỉ-theo-span** (lọt ngoài span đánh dấu: `vmmu_r258` rớt `A.` giữ nguyên 4 đáp án, `r284` watermark ẩn chữ không đánh dấu, `r375` chữ `s` viết thường, `r460` mất biên `bằng→bán`, `r463` mất `°`).
- **`External15`:** `ext_prt_08` (`0/4` dải cột/chữ nhỏ sát mép vẫn từ chối `REFUSED`) và `4` ảnh `vmmu` đa điều kiện ngoài ngữ pháp cục bộ khi `ALLOW_LIVE_AI=0` (`ext_prt_10`, `13`, `14`, `15`).

### 7. Nguyên nhân còn lại thuộc OCR, Parser, Planner, Registry, Kernel hay Frontend?
- **OCR:** Các lỗi không nằm trong uncertain span do watermark/cột dày (`ext_prt_08`, `r284`), rớt `A.`/chữ nhỏ viết thường/mất `°` ngoài vùng tranh chấp (`r258`, `r375`, `r460`, `r463`).
- **Parser & `TypedFactNext /2` Bridge (`§6.2`):** Chưa hỗ trợ `@id` làm operand trong premise (`r254`), `point_reflection` (`r277`), locus trượt không tỉ số (`r491`), và các câu `ext_prt_10/13/14/15` đang dừng ở `LIVE_AI_DISABLED` khi tắt fallback AI. Source Gate giữ đúng chuẩn fail-closed (`r256`, `r513`).
- **Planner (`§9.3`):** **`PLANNER_GAP = 0`** trong toàn bộ 9 ca `REAL27` bị từ chối; trên `reasoning_matrix (72)`: `61/62 pos + 10/10 neg` (`33` `SOURCE_EXPLICIT_SEQUENCE`, `25` `REGISTERED_DECOMPOSITION`, `3` `DISCOVERED_FUNCTION_COMPOSITION`, `8` ca tái sử dụng trung gian), riêng `MG9` tự lập kế hoạch `33 <= 48` ứng viên thành công nhưng dừng đúng chuẩn ở lớp IR budget (`34 > MAX_MEMORY_DECLARATIONS = 32`).
- **Registry & Kernel:** `REGISTRY_GAP = 1` (`r488` đo thể tích chóp con trên lăng trụ); `KERNEL_EXACT_DOMAIN_GAP = 1` có chủ đích (`r266` căn lồng ngoài `ℚ`).
- **Frontend:** Không hỏng trên repo chính (`142` files / `2,062` tests PASS, `0` sửa đổi `frontend/`), nhưng việc tích hợp các trường provenance mới trên thư viện hình ngoài repo (`axo-geometry-library`) thuộc **`BLOCKED_OWNERSHIP` (`FE-2/3/4/6`)**.

### 8. Có xuất hiện mô phỏng sai hoặc dữ kiện không có nguồn không?
- **Không (`0`):**
  - **`false_auto_accepts = 0`** (trên `adversarial_negative`, `rendered_positive`, `REAL27`, `External15`, `new_external_12`, `new_image_corpus_8`).
  - **`wrong_scene_served_total = 0`** across text + auto OCR + span confirmation (`REAL27`, `External15`, `REAL27_TEXT`, `autonomous_negatives 11/11`, `reasoning_matrix 10/10 neg`, `r1_probe 6/6 neg`).
  - **`total_scene3d_continuity_errors = 0`** trên toàn bộ chiến dịch.
  - **`mode_a_trig_no_answer_leak = true`**: 3 ca adjudication `vmmu_r258`, `r498`, `r559` đều đạt `geometry_model_verified = True`, `visual_goal_satisfied = True`, `numeric_answer_hidden_mode_a = True` (`NOT_ANSWERED`, `0` lộ số đo).
  - **Provenance & Cache `144`:** `confirmed_provenance` tự động hạ cấp văn bản chỉnh tay (`counted_as_unmodified_auto_ocr = False`), tách `cache_key`, vô hiệu hóa cache `143:route-d` (`CACHE_VERSION = "144"`).

### 9. Hiệu năng thực tế thay đổi thế nào?
Đo thực tế trên `REAL27` (`27` ảnh, 1 asyncio event loop trên CPU host, chạy sạch không tải song song):
- **Cold end-to-end:** **`p50 = 2,494.01 ms`**, **`p95 = 4,068.90 ms`** (`mean = 2,676.56 ms`), gồm `cold_prepare = 2,444.31 / 4,056.31 ms` + `solve = 39.98 / 114.85 ms`.
- **Phân rã từng chặng (`p50 / p95 ms`):**
  - Tiền xử lý & OCR worker: `normalize = 45.58 / 105.65`, `region_detect = 107.19 / 178.44`, `decode = 10.69 / 18.58`, `tesseract = 260.54 / 397.32`, **`rapidocr = 1,932.29 / 2,868.95`** (nút thắt chính ~`79%` `cold_prepare`), `reconcile_only = 55.32 / 149.82`, `reread = 400.48 / 879.87` (`crop = 27.34 / 58.47`, `topology = 52.65 / 121.81`, `latin_rec = 135.03 / 328.54`, `tess_eng = 67.33 / 139.22`, `tess_vie = 73.95 / 178.22`).
  - Hậu OCR: `simulate_student = 0.63 / 3.81`, `local_parse = 10.65 / 20.37`, `hybrid_execution = 24.34 / 101.55`, `continuity_check = 0.00 / 0.54`.
- **Warm end-to-end (trúng `_RAW_OCR_CACHE(32)` + `_REREAD_CACHE(512)`):** **`p50 = 281.99 ms`**, **`p95 = 449.10 ms`** (`warm_prepare = 224.74 / 374.52 ms`) — **tăng tốc `8.8x` ở `p50` end-to-end (`10.9x` ở chặng prepare)**.

### 10. Những ranh giới nào vẫn cần nghiên cứu hoặc Owner phê duyệt?
- **Cổng kiểm định độc lập & thiết bị (chưa đo — giữ nguyên trung thực):** `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (`0` hàng `H-1` mở), `INDEPENDENT_GENERALIZATION = NOT_MEASURED` (`W2`/`W3` không mở), `REAL_STUDENT_USABILITY = NOT_MEASURED`, `PHYSICAL_LOW_END = NOT_MEASURED`.
- **Cổng phê duyệt chi phí & phát hành của Owner:** `K-1 / S-2 / R-1 = PENDING_OWNER_DECISION` (`paid_project_confirmed: false`, `3` template C21 đã cập nhật sang `e1c6428ed558a722...`), `PUBLICATION_HEAD = BLOCKED_PENDING_OWNER_REVIEW`.
- **Sở hữu Frontend ngoài repo:** `FE-2 / FE-3 / FE-4 / FE-6 = BLOCKED_OWNERSHIP` (`D:\Documents\projects\axo-geometry-library` và `frontend/public/favicon.svg` nguyên vẹn `0` thay đổi).
- **Nghiên cứu kỹ thuật tiếp theo:** giảm độ trễ cold `rapidocr` trên CPU (`~1.93s`), mở rộng grammar/TypedFact cho đối xứng điểm (`r277`), góc phức hợp (`r254`), quỹ tích trượt (`r491`), chóp con trên lăng trụ (`r488`), và gắn cờ tốt hơn cho chữ rơi dấu chấm đáp án / watermark (`r258`, `r284`, `ext_prt_08`).

---

## Tổng Hợp Cổng Nghiệm Thu Gate A–G (Trên Candidate Đóng Băng `003104fd5`)

| Cổng | Trạng thái | Bằng chứng chính |
|---|---|---|
| Gate A — OCR Reliability | **PASS (Offline)** | `12/12` `glyph_topology`, `4/4` `rendered_pos`, `3/3` `adv_neg` chặn, `REAL27` CER `0.0944 → 0.0533` (blocking `81 → 44`), `0` false auto-accepts. |
| Gate B — Human Confirmation | **PASS (Backend Contract)** | `13/27` `REAL27` + `8/12` `External15` + `2/6` selection bands phục vụ `0` wrong; `ocr-confirmation-provenance/1` & `verified-input-provenance/1`; Frontend library `BLOCKED_OWNERSHIP`. |
| Gate C — Grounded Understanding | **PASS** | `REAL27_TEXT = 18/27 (0 wrong)`, `vmmu_r513` aligned (`MISSING_DIMENSION` + `UNPROVED_DUE_TO_CAPABILITY_GAP`), `NC-1..21` `21/21`, `autonomous_negatives = 11/11`, `§6.2` 9/9 Gold isolated. |
| Gate D — Autonomous Planner | **PASS** | `4` locked surfaces khớp SHA-256; `RM72 = 61/62 pos + 10/10 neg`, `3` discovered compositions, `8` reuses; `MG9` fail-closed `MAX_MEMORY_DECLARATIONS = 32`. |
| Gate E — Verified Simulation | **PASS** | `total_scene3d_continuity_errors = 0`; `mode_a_trig_no_answer_leak = true`; offline Vision mock `SERVED a³√3/3`. |
| Gate F — Evaluation Integrity | **PASS** | `0` hàng `H-1`/`W2`/`W3` mở; tách bạch `development` vs `frozen`/`fresh_external`, span-only vs `whole_draft_fallback`, chữ in vs viết tay, 100% failed/refused analyzed. |
| Gate G — Regression & Delivery | **PASS (Owner Gates Pending)** | Backend full pytest **`14,866 passed, 7 skipped, 3 deselected, 12 xfailed, 0 failed (806.08s)`**; `replay_demo_cases 5/5 (1/1)`; `audit_demo_crash_surface 6/6`; `export_hybrid_preview_fixtures 41/41`; `lock_cache_identity 144 MATCH`; `freeze_evaluation_candidate MATCH (120 files, e1c6428ed558a722...)`; Frontend zero diff (`142 files / 2,062 tests PASS, tsc -b PASS, vite build PASS`). |

---

## Bảng Chứng Từ & Hàm Băm SHA-256 (Các Tạo Tác Anh Em Trong Thư Mục Run)

> Quy ước chống vòng lặp tự tham chiếu: bảng dưới đây liệt kê byte và SHA-256 của mọi tệp anh em trong run (ngoại trừ chính `FINAL_MASTER_REPORT.md` và `run.json`); `run.json` ghi nhận đầy đủ SHA-256 & dung lượng cho toàn bộ tệp kể cả `FINAL_MASTER_REPORT.md`.

| Tệp (`docs/evaluation/geometry/runs/real-world-geometry-input-verified-simulation/...`) | Kích thước (bytes) | SHA-256 |
|---|---:|---|
| `REAL_WORLD_END_TO_END_EVALUATION.json` | 652,559 | `5a335ba51c3639faf5071153abec7799572c05f1fa9c30c21133e0cc18f847e9` |
| `REAL_WORLD_INPUT_BASELINE.md` | 19,507 | `4164b268695d8c6c3c6901a177c4294416db08efa7bed29817f5a71174ac50ce` |
| `IMPLEMENTATION_REPORT.md` | 7,510 | `b212ad7a1d4dc4a19a69ce89a8700585bb43f11a89041aeb8801af3cf5537f5e` |
| `SCENE3D_AND_FRONTEND_HANDOFF.md` | 6,558 | `598e70663cc318a0f17f1ab522783a0c1430fbb07f6c6f2e0b366eea634b3837` |
| `pending_template_refresh.json` | 3,359 | `3320f92a18020c68abb6eb8ce4252699d39832674dc60c5fc906b4657a1119c3` |
| `logs/prior-k1-owner-approval.template.json` | 782 | `8049ab57551e99d7e151d12f279dd1ce1cb7dcd36261bc519f4a305410bf93db` |
| `logs/prior-r1-owner-approval.template.json` | 782 | `bbb22f8b01e61efe880847aeea5e6401ea11f09680f5467b49ee1c3ece30cfa9` |
| `logs/prior-s2-owner-approval.template.json` | 782 | `68542854b25825929e2febbff408a9a095479e78caff2a28e8244fa23ddc5947` |
| `tools/evaluate_real_world_campaign.py` | 99,644 | `0a20e5ab233e08cffa3d66acbfbf0e4f5566bb6fc0d718f7eb51e7d195888cff` |
