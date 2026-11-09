# Báo cáo tổng hợp: hai luồng phát triển song song (OCR cục bộ · lập kế hoạch Hybrid)

- **Run:** `parallel-ingestion-reasoning` (2026-11-09). Nhánh tích hợp tạm `integration/parallel-ingestion-reasoning`.
  Chưa merge vào `main`, chưa push.
- **Thời điểm đo:** chế độ offline. `ALLOW_LIVE_AI=0`, **0** lượt gọi Gemini mạng thật.
  `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`.
- **Báo cáo từng luồng:**
  - A: [`../adaptive-local-ocr-fallback/ADAPTIVE_LOCAL_OCR_REPORT.md`](../adaptive-local-ocr-fallback/ADAPTIVE_LOCAL_OCR_REPORT.md)
  - B: [`../hybrid-reasoning-generalization/HYBRID_REASONING_GENERALIZATION_REPORT.md`](../hybrid-reasoning-generalization/HYBRID_REASONING_GENERALIZATION_REPORT.md)
- **Đính chính báo cáo trước:** [`receipt-correction.md`](receipt-correction.md).

## 1. Phán quyết

| Luồng | Phán quyết | Căn cứ chính |
|---|---|---|
| A — OCR cục bộ + Vision fallback | `LOCAL_OCR_DIAGNOSTIC_ONLY` | Không engine OCR nào vào sản phẩm (§3). Bản sửa duy nhất được đưa vào: bỏ lượt Vision thừa khi crop đã chứa trọn nội dung. |
| B — Lập kế hoạch Hybrid | `HYBRID_REASONING_IMPROVEMENT_VERIFIED` | Corpus phát triển 72 ca (không held-out). Phục vụ chính xác 47 → 56, từ chối sai 6 → 0, phục vụ sai 0 → 0 (§4). |
| Tích hợp | `PARALLEL_CANDIDATES_INTEGRATION_VERIFIED` (offline) | Candidate tích hợp qua Full T3 trên worktree detached sạch (§5), hợp đồng chung không trôi (§6). |

Cả ba phán quyết chỉ có giá trị **offline**. Chưa có kiểm định độc lập H-1, chưa có lượt live, chưa xác minh triển khai
production.

## 2. Baseline chung và pre-flight

- **`COMMON_BASE_SHA = d79565b52ec19a7b1a75be28c09bb43cc0f6d146`.** Đây là ngọn của chuỗi tuyến tính
  `main (bb046fa22) ⊂ feat/hybrid-backend-capabilities ⊂ feat/hybrid-production-composition ⊂ feat/hybrid-goal-driven-planner ⊂ feat/algosim-local-first-image-ingestion`.
  Không nhánh nào trong chuỗi đã vào `main`. Hai nhánh luồng đều rẽ từ commit này.
- **III.1 — ngữ nghĩa khoảng cách suy biến.** Không cần sửa sản phẩm.
  - `_kc2_do_dai` đo khoảng cách điểm–điểm, nên `distance(A, A) = 0` được phục vụ.
  - Phép cần một đường thẳng qua hai điểm thì từ chối: góc đường–mặt, góc hai đường, mặt ⊥ đường, trung điểm hay chia
    đoạn suy biến.
  - Báo cáo trước mô tả ngược lại; xem `receipt-correction.md` §1.
- **III.2 — receipt.** JSON là nguồn sự thật.
  - Có 9 ô ở bảng §4.2 của báo cáo trước lệch so với JSON. Chúng được sinh lại bằng `tools/reconcile_receipts.py`
    → `results/receipt_reconciliation.json`.
  - JSON gốc và báo cáo gốc giữ nguyên byte.
- **III.3 — Full T3 tại baseline.** Chạy trên worktree detached sạch tại `d79565b52`: `FULL_PRODUCT_GATE_PASS`.
  - pytest 13994 passed / 0 failed; vitest 2000/2000; build PASS; demo 5/5; bề mặt sập 6/6.
  - freeze `--verify` MATCH (`6290986d…`).
  - Báo cáo trước chưa từng chạy cổng này.

## 3. Luồng A — vì sao OCR cục bộ chỉ dừng ở chẩn đoán

Số liệu chi tiết nằm trong `ocr_benchmark.json`, `vision_calls_before_after.json` và các bảng do `tools/render_tables.py`
sinh ra.

**Kết quả đo:**
- **Tesseract 5.5.3 `vie`:**
  - Giữ dấu tiếng Việt: 97–98% từ đúng nguyên văn.
  - Đọc sai ký hiệu toán mà không báo: α β ⊥ ∥ ∠ √ ² ³ ₁ ₂ có recall 0; `(β)` thành `(B)`, `;` thành `:` trong toạ độ.
- **RapidOCR PP-OCRv5/v6:**
  - Đọc đúng ký hiệu.
  - Từ điển thiếu 40 chữ tiếng Việt dựng sẵn (ạ, ụ, ể, ộ…), nên không cho ra tiếng Việt đúng. Lỗi này chạm
    `ISSUE-ARCH-ROUTE-D-DIACRITIC-FREE-INPUT`.

**Cổng chấp nhận local-only:**
- Không có ngưỡng an toàn nào cho một engine đơn lẻ: Tesseract fast cho qua 9 văn bản, trong đó 3 văn bản mang sai
  dữ kiện toán.
- Cổng hai engine (Tesseract đọc chữ, RapidOCR bỏ phiếu ký hiệu) có 0 lần chấp nhận sai, nhưng chỉ trên tập hiệu chỉnh
  22 ảnh **tổng hợp, không held-out**. Nó chấp nhận 3–5/22 ảnh, đổi lại thêm khoảng 0,75 GB RAM và khoảng 1,3 s CPU mỗi ảnh.

**Lý do không đưa vào sản phẩm:**
- Gói triển khai cần thêm một manifest apt mà kho chưa có.
- Độ chính xác của Vision chưa đo được (mọi số Vision đều từ mock), nên không có baseline để chứng minh OCR "không kém hơn".

**Bản sửa đã đưa vào:** `crop_holds_all_content` (`region_detector.py`, `unified_input.py`).
- Khi VLM báo `missing_regions` hoặc `MISSING_PROBLEM_TEXT` trên một crop đã chứa mọi khối bố cục và trang chưa bị cắt
  nền bàn, hệ không đọc lại toàn ảnh nữa.
- Trên cùng 22 ảnh, lượt Vision mock giảm 23 → 22. Hành trình nhiều ảnh (A, A trùng, ảnh chỉ có hình) giảm 3 → 2.
- Văn bản khớp ground truth ở cả hai lần: 21/21. Lượt gọi mạng thật: 0.

**Giới hạn đã khai:** bản sửa tin bộ tách khối. Văn bản mà bộ tách khối bỏ sót hoàn toàn trên trang chưa cắt nền sẽ
không được Vision đọc lại. Khi đó hệ từ chối (fail-closed), không phục vụ sai.

## 4. Luồng B — cải tiến có bằng chứng

Matrix 72 ca TypedFactNext /2 vàng đi qua `run_hybrid_offline`. Giá trị kỳ vọng lấy từ oracle độc lập
`custodian/geometry_oracle.py`. Receipt nằm trong `results/` của run B.

| Kết cục | Trước | Sau |
|---|---:|---:|
| Phục vụ chính xác | 47 | 56 |
| Từ chối đúng | 7 | 9 |
| Làm rõ đúng | 1 | 1 |
| Từ chối sai | 6 | 0 |
| Không tìm được kế hoạch dù đủ primitive | 8 | 5 |
| Vượt ngân sách tìm kiếm | 1 | 1 |
| Từ chối sai lớp | 2 | 0 |
| **Phục vụ sai** | **0** | **0** |
| Lỗi adapter / Scene3D | 0 | 0 |

**Ba bản sửa:**
- **G1a — `_tam_giac`.** Hai đoạn `perpendicular_lines` chung đầu mút V được tính là một góc vuông tại V:
  XY² = VX² + VY². Nếu đề cho XY khác giá trị đó thì từ chối `INCONSISTENT_FACTS`.
- **G1b — `_dinh_tu_ba_canh_ben`.** Luật cuối cùng: dựng đỉnh chóp từ ba cạnh bên bằng trilateration chính xác trong
  khung Gram. Nếu h² ≤ 0 thì từ chối `INCONSISTENT_FACTS`.
- **G5 — `_kiem_result_binding`.** Chain verifier nhận trích dẫn từ chứng chỉ `distance(point,line)` của chân đường
  vuông góc được tái dùng, đồng bộ với `_kiem_phu`. Chứng chỉ bị xoá hay trích dẫn bị giả vẫn bị từ chối (đã có test tiêm lỗi).

Coordinator đã soát lại toán của G1a/G1b:
- Hệ 2×2 `g(F−P0, u) = (|u|² + r0 − r1)/2` tính trong ℚ.
- Mọi cạnh bên còn lại vẫn là dữ kiện được kiểm lại trên hình đã dựng.
- Hai nghiệm gương (đỉnh ở trên hay dưới mặt đáy) cho cùng mọi độ đo.

**Những gì không đổi:**
- Không đổi chuỗi phiên bản: Planner /26, Registry /33, Engine /24.
- Không gán lại nhãn telemetry: không thêm tuyên bố `GOAL_DRIVEN_DISCOVERY`.
- Telemetry tìm kiếm trên 47 ca phục vụ trước đó giống hệt trước và sau.
- Hiệu năng không đổi đo được: A/B xen kẽ trên cùng corpus, planner p50 khoảng 0,85–0,9 ms, kernel p50 khoảng 12 ms.

**Chưa sửa, đã có test xfail strict:**
- G2, G3, G4, G7 thuộc tầng bridge hoặc Source Gate, tức là hợp đồng chung. Run B ghi đề xuất cho chúng, không triển khai.
- G6 vướng `MAX_MEMORY_DECLARATIONS = 32` của hợp đồng IR.

**Ảnh hưởng tới receipt lịch sử** (khai thành delta layer; receipt gốc giữ nguyên byte):
- NLU gold D08 chuyển `REFUSED → SERVED 18/7`, khớp giá trị độc lập đã đăng ký trước của corpus đó.
- v3-matrix dev02 và h16 chuyển FALSE_REFUSAL → CORRECT_COMPLETE.
- **h16 thuộc split LOCKED.** Nó chỉ lộ ra khi chạy full suite sau bản sửa, không được dùng để viết matrix hay bản sửa.
  Run này không đưa ra tuyên bố nào về tập LOCKED.

## 5. Candidate tích hợp

- **Chuỗi commit:**
  - `60bba4624` là merge `--no-ff` của A (`25a098602`) rồi B (`756697dc7`) trên `d79565b52`.
  - `d2d89376a` sửa chú thích của A: `crop_holds_all_content` tính cả khối nhiễu. Chỉ đổi chú thích, không đổi logic.
  - `452210a9c` đóng băng lại candidate: 106 file, tree hash `0e815f39c8d02203d73ce332faa7f167c8344ef925f6adc547bbe37bae472a7c`,
    `--verify` MATCH. Hash `measured_system` trong ba template K-1/R-1/S-2 được đồng bộ theo; `owner_decision` không đổi.
- **Xung đột merge:** chỉ ở `CODE_INDEX.md` (giữ cả hai mục), `EVALUATION_CANDIDATE.json` và ba template (sinh lại bằng
  bước đóng băng). Không có file sản phẩm nào bị xung đột.
- **`CACHE_VERSION = 132`, không bump.**
  - A không chạm bề mặt mô hình.
  - B chỉ biến từ chối thành phục vụ hoặc đổi mã từ chối, mà cache chỉ lưu hàng SERVED. 47 hàng đã phục vụ giữ nguyên
    đáp số và telemetry.
  - `test_cache_identity` và `test_current_state_identity` xanh.
- **Full T3 trên candidate tích hợp:** kết quả ghi ở `run.json` → `integration_t3`.

## 6. Kiểm tra hợp đồng chung

| Mục | Kết quả |
|---|---|
| File sản phẩm của hai luồng | Rời nhau: A ở `backend/app/ingestion/{region_detector,unified_input}.py`, B ở `backend/app/simulation/geometry_functions/{engine,registry}.py`. |
| TypedFactNext `/2`, `bridge_v2`, Source Gate | Không luồng nào sửa. |
| `/api/input/prepare`, `/api/image/extract`, `/api/analyze` | Không đổi hình dạng API, không thêm reason code. |
| Nguồn gốc dữ kiện | OCR không bao giờ sinh Verified Facts. Văn bản ảnh vẫn qua bước người học duyệt rồi mới vào TypedFactNext. |
| Scene3D | B: 0 lỗi construction continuity. A không chạm. |
| Cache | Không trôi (§5). |

Hai luồng gặp nhau ở đúng một điểm: chuỗi văn bản của đề. Luồng A không đổi văn bản nào đến được `/api/analyze`, nên ở
tầng sản phẩm không có tương tác chéo nào để thử thêm. Test cả hai luồng chạy trên cây tích hợp: 160 passed, 6 xfailed
(strict). Full T3 xem §5.

## 7. Bảy hành trình

| # | Hành trình | Trạng thái |
|---|---|---|
| 1 | Chỉ văn bản | Không đổi. Có trong T3. |
| 2 | Ảnh rõ, OCR cục bộ, 0 Vision | **Không triển khai** (A = diagnostic only). Vẫn là 1 Vision + 1 TypedFactNext. |
| 3 | Ảnh khó, Vision fallback | Không đổi. Lượt đọc lại `IMAGE_NOT_READABLE` vẫn giữ. |
| 4 | Nhiều ảnh | Khử trùng lặp và giữ thứ tự. Mock 3 → 2 lượt Vision (`test_image_crop_retry_dedup.py`). |
| 5 | Người học sửa văn bản | Không đọc lại ảnh, giữ bản sửa (test có sẵn). |
| 6 | Hình học nhiều bước | B: tứ diện vuông, chóp xác định bởi ba cạnh bên, chân đường vuông góc tái dùng (`test_hybrid_reasoning_generalization.py`). |
| 7 | Ca âm | Ca âm vẫn fail-closed: B có `test_g1_negatives_stay_fail_closed`; A giữ đường từ chối `IMAGE_NOT_READABLE`. |

Mọi hành trình chỉ được kiểm offline, bằng mock provider và fixture. Chưa chạy trình duyệt cho luồng ảnh ở run này, vì
frontend không đổi.

## 8. Điều kiện còn thiếu trước khi đưa vào `main`

1. Owner duyệt và ra lệnh merge, cho riêng task này. Chuỗi bốn nhánh cũ phía dưới `d79565b52` cũng chưa vào `main`.
2. Đo độ chính xác của Gemini Vision trên ảnh thật, trong một lượt live có ngân sách. Đây là điều kiện trước khi có thể
   tuyên bố OCR cục bộ tốt hơn hay kém hơn Vision. Corpus ảnh thật hiện chưa có.
3. H-1 độc lập: vẫn `NOT_MEASURED`.
4. G2, G3, G4, G7 cần một quyết định về hợp đồng bridge/Source Gate. G6 cần một quyết định về ngân sách IR.
