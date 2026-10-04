# Ma trận tuyên bố ↔ bằng chứng

> Mọi ô **Bằng chứng** dưới đây truy được tới một artifact có băm hoặc một test
> chạy được. Không ô nào suy từ tên file hay từ trạng thái hiện tại của hệ.
> Đối chiếu: `docs/THESIS_OBJECTIVE_AND_CLAIM_ALIGNMENT_REVIEW.md`.

**Nguồn mục tiêu (`OBJECTIVE_SOURCE`):** `docs/THESIS_DRAFT.md` §3 *Mục tiêu
nghiên cứu*, §4 *Đối tượng và phạm vi*, §6 *Đóng góp chính*, §1.6–§1.7. Thứ tự
thẩm quyền theo đúng lệ: bản thảo chính thức → Chương 1 → ma trận acceptance đã
đăng ký → Chương 4–5 → ledger kỹ thuật.

**Sáu trạng thái, không có trạng thái thứ bảy:** `PROVED_ON_FROZEN_BENCHMARK` ·
`PARTIAL` · `NOT_MEASURED` · `OUT_OF_SCOPE` · `CONTRADICTED` · `NOT_LOCATED`.

⚠️ **Chín mức được tách riêng, không gộp thành một chữ "hỗ trợ":** hệ biểu đạt
được · kernel tính đúng · mô hình tự tìm ra phép · đúng ngay lượt đầu · đúng sau
vòng sửa · UI hiển thị được · hình học trình bày đúng · ổn định qua nhiều lượt ·
sẵn sàng triển khai. Bốn mức đầu và mức thứ sáu, bảy đã có bằng chứng; mức thứ
tám và thứ chín **chưa đo**.

---

## A. Mục tiêu cụ thể (MT1–MT5) — `THESIS_DRAFT §3`

| ID | Mục tiêu | Tuyên bố hiện tại | Bằng chứng trực tiếp | Artifact/test nguồn | Phạm vi ca đo | Trạng thái | Câu ĐƯỢC phép viết | Câu KHÔNG được phép viết | Khoảng trống | Hành động |
|---|---|---|---|---|---|---|---|---|---|---|
| **MT1** | Thiết kế IR (Semantic Program) đủ diễn đạt bước dựng và phép đo, đủ chặt để mô hình không nhúng kết quả | IR đã thiết kế và cưỡng chế bằng lược đồ | `NEW_IR_OPERATIONS = 0`, `NEW_MEMORY_TYPES = 0`, `NEW_PER_PROBLEM_MODULES = 0` trên 7 ca / 7 dạng; mọi toán hạng hình học là TÊN | `FINAL_SUMMARY.json`; `contract.py` + schema mirror; `test_schema_sync.py` | 7 ca dương, 7 dạng | **PROVED_ON_FROZEN_BENCHMARK** | "IR hiện có diễn đạt được bảy dạng bài mà không thêm phép nào" | "IR diễn đạt được mọi bài hình học không gian" | ràng buộc "không nhúng kết quả" chứng minh bằng **cấu trúc lược đồ**, không bằng phép đo hành vi trên nhiều đề | giữ nguyên |
| **MT2** | Nhân hình học tất định trên hữu tỉ + căn, không dùng `float` trong miền hình học | Đạt | 12/12 đại lượng khớp **từng ký tự** và khớp oracle cài độc lập; `3√6`, `25π√5`, `2π√6` giữ dạng chính xác | `SCORING_CORRECTION.json` (12 mục `quantities_SUA`, tất cả `exact_answer_match`); `doi_chieu_ket_qua_cuoi.py` → `DAP_SO_KHOP 12/12` | 12 đại lượng / 7 ca | **PROVED_ON_FROZEN_BENCHMARK** | "mọi đại lượng đo được tính trong `ℚ(√, π)`, không làm tròn" | "kernel đúng với mọi bài toán hình học" | bao đóng số là `ℚ(√, π)`; ngoài bao đóng ⇒ từ chối | giữ nguyên |
| **MT3** | Các tầng thẩm định fail-closed + khai báo trung thực khi thiếu năng lực | Đạt | 7/7 grounding · phủ · tĩnh · bất biến nguồn · hậu điều kiện; 2/2 ca âm fail-closed; `SILENT_WRONG_ANSWER = 0`, `UNHANDLED_EXCEPTION = 0` | `FINAL_SUMMARY.json`; `stage_a_first_attempt.json`; `audit_demo_crash_surface.py` 6/6 | 7 dương + 2 âm | **PROVED_ON_FROZEN_BENCHMARK** | "hệ từ chối có địa chỉ thay vì phục vụ một kết quả không chứng minh được" | "hệ từ chối đúng mọi bài ngoài năng lực" | `TARGET_BOUNDARY_PASS = 1/2` — `n1` bị chặn TRƯỚC khi có mã lỗi để so. ⚠️ **Ghi chú 2026-09-09 (`PRODUCT_RESPONSE_CONTRACT_ALIGNMENT`)**: con số **1/2 GIỮ NGUYÊN**. Bản vá làm `n1` mang mã (`semantic_program_invalid` @ `semantic_program`) thay vì `null`, nhưng mã ấy **không phải** ranh giới định đo (`solid_of_revolution_general` @ `structural_coverage`/`grounding`) — hệ vẫn dừng TRƯỚC cổng phủ, nên vẫn **không chứng minh** ranh giới ấy. Sửa cách BÁO CÁO một thất bại không đổi được thất bại ấy là gì. | ghi giới hạn ở Chương 4 §4.7 |
| **MT4** | Dẫn xuất cảnh 3D + dòng thời gian từ vết, giữ song ánh khung *k* ⇔ bước *k* | Đạt | 7/7 `TRACE_PASS` và `SCENE3D_PASS`; bước cuối dựng lại đủ mọi vật; đáp số chỉ hiện sau bước đo nó | `FINAL_SUMMARY.json`; `product-envelope-rendering.test.tsx` (70 test); `UI_ACCEPTANCE_MATRIX.json` 66/66 | 7 ca dương | **PROVED_ON_FROZEN_BENCHMARK** | "cảnh và dòng thời gian dẫn xuất từ trạng thái tất định, giữ song ánh khung ⇔ bước" | "cảnh 3D dễ hiểu với người học" | đo **cấu trúc** cảnh, không đo chất lượng sư phạm | giữ nguyên |
| **MT5** | Đánh giá thực nghiệm khả năng tổng hợp trên đề chưa từng thấy + đo tính tất định bằng hồi quy | Đạt **một phần** | 6/7 lần đầu · 7/7 sau ≤1 lượt sửa; hồi quy tất định: pytest 4781, vitest 798, 0 đỏ | `FINAL_SUMMARY.json`; `RECONCILIATION.json` | 7 ca dương, **n = 1 mỗi họ, một lượt** | **PARTIAL** | "trên bộ ca này, mô hình tự tìm được chương trình đúng ở 6/7 ca lần đầu" | "mô hình tổng hợp ổn định" · "tỉ lệ thành công của hệ là 85,7 %" | **không đo lặp lại**: `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED` | in kèm mẫu số ở mọi chỗ; không đặt ngưỡng |

---

## B. Đóng góp (ĐG1–ĐG7) — `THESIS_DRAFT §6`

| ID | Đóng góp | Bằng chứng trực tiếp | Nguồn | Phạm vi | Trạng thái | Câu ĐƯỢC viết | Câu KHÔNG được viết | Hành động |
|---|---|---|---|---|---|---|---|---|
| **ĐG1** | Kiến trúc tách bạch; mô hình không phát toạ độ kết quả; cưỡng chế bằng **lược đồ** | `RAW_GEOMETRY_LITERAL_ATTEMPTS = 0`; mọi ô toán hạng là TÊN; `n1` cố bịa ba điểm và bị `UNANCHORED_DERIVED_ASSUMPTION` chặn | `stage_a_first_attempt.json` (`n1.synthesis_error`); `contract.py` | 9 ca | **PROVED_ON_FROZEN_BENCHMARK** | "ranh giới R0 được cưỡng chế trên đường chạy thật, và đã thật sự chặn một lần" | "mô hình không bao giờ thử vượt ranh giới" *(nó có thử — và bị chặn)* | giữ nguyên |
| **ĐG2** | Semantic Program — IR chạy được, toán hạng là tên, có xuất xứ, có kiểm chứng | 7/7 chương trình chạy trọn; `producer`/`depends` đủ trên mọi vật | fixture 9 ca; `FINAL_SUMMARY.json` | 7 ca dương | **PROVED_ON_FROZEN_BENCHMARK** | như đã viết | — | giữ nguyên |
| **ĐG3** | Biên thẩm định có kiểu, fail-closed, sáu tầng | 7/7 qua cả sáu tầng; `p3` bị chặn đúng ở `ir_static` rồi sửa được | `stage_a_first_attempt.json`, `stage_b_recovery.json` | 9 ca | **PROVED_ON_FROZEN_BENCHMARK** | như đã viết | — | giữ nguyên |
| **ĐG4** | Nhân hình học số học chính xác | xem **MT2** | như MT2 | 12 đại lượng | **PROVED_ON_FROZEN_BENCHMARK** | như MT2 | như MT2 | giữ nguyên |
| **ĐG5** | Cảnh 3D dẫn xuất từ vết, song ánh khung ⇔ bước | xem **MT4** | như MT4 | 7 ca | **PROVED_ON_FROZEN_BENCHMARK** | như MT4 | như MT4 | giữ nguyên |
| **ĐG6** | Trung thực năng lực: phân biệt *không làm được* với *làm được nhưng chưa kiểm chứng được* | `product_capability.py` giữ ba mức (`supported` · `foundation_only` · `unsupported`); `foundation_only` không hiện cho người học | `product_capability.py`; `test_missing_family_roadmap.py` | toàn hệ | **PROVED_ON_FROZEN_BENCHMARK** | như đã viết | — | ⚠️ **lý do** của ba dòng khối cong đã cũ — xem §D-3 |
| **ĐG7** | Bằng chứng thực nghiệm: bài mới trong IR tổng hợp được bằng **tổ hợp** primitive | 0 phép IR mới trên 7 dạng | `FINAL_SUMMARY.json` | 7 ca, n = 1 mỗi họ | **PARTIAL** | "bảy dạng bài khác nhau được phục vụ bằng cách ghép phép sẵn có" | "mọi bài mới đều tổng hợp được bằng tổ hợp" | in kèm cỡ mẫu; bản thảo đã tự khai điều này |

---

## C. Câu hỏi nghiên cứu (RQ1–RQ5) — ma trận đã ĐĂNG KÝ TRƯỚC

Nguồn: `docs/THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION.md` Bảng 2 +
`CLAIMS_MATRIX.json` (`created_before_live_run = true`).

| ID | Câu hỏi | Metric đã đăng ký | Kết quả đo | Nguồn | Phạm vi | Trạng thái | Câu ĐƯỢC viết | Câu KHÔNG được viết | Khoảng trống |
|---|---|---|---|---|---|---|---|---|---|
| **RQ1** | độ phủ | `NEW_PER_PROBLEM_MODULES` = 0 · `ABSENCE_PROOF_PASS` 2/2 | 0 · 2/2 | `FINAL_SUMMARY.json`; `CAPABILITY_MATRIX.json` | 7 dương · 2 âm | **PROVED_ON_FROZEN_BENCHMARK** | "10/10 họ trong phạm vi được phủ, không thêm mã theo bài" | "phủ chương trình hình học THPT" | phủ **một phần**, có chủ đích |
| **RQ2** | tính đúng | mọi `*_MISMATCH_COUNT` = 0 | 12/12 đại lượng · 7/7 oracle · 7/7 bất biến nguồn · 7/7 cảnh 3D | `SCORING_CORRECTION.json`; `WORLD_SPACE_ORACLES.json` 7/7 | 12 đại lượng / 7 ca | **PROVED_ON_FROZEN_BENCHMARK** | "12/12 đại lượng khớp chuỗi hiển thị và oracle độc lập" | "hệ luôn cho đáp số đúng" | ⚠️ ma trận đăng ký ghi "11 đại lượng" — **đính chính**, xem §D-1 |
| **RQ3** | tự sinh | **KHÔNG NGƯỠNG** — mô tả kèm mẫu số | 6/7 lần đầu · 7/7 sau ≤1 sửa | `FINAL_SUMMARY.json` | 7 ca, n = 1 | **PARTIAL** | "6/7 ca lần đầu, trên bộ ca này" | "85,7 % là độ chính xác của hệ" · bất kỳ câu nào có chữ *ổn định* | `no_threshold_by_design` — cố ý, không phải chỗ trống |
| **RQ4** | an toàn | 2/2 · `SILENT_WRONG_ANSWER` = 0 | 2/2 · 0 · `UNHANDLED_EXCEPTION` 0 | `FINAL_SUMMARY.json` | 2 âm · 9 ca | **PROVED_ON_FROZEN_BENCHMARK** | "2/2 ca âm fail-closed, không phát ra một đại lượng nào" | "hệ chặn được mọi bài ngoài năng lực" | `TARGET_BOUNDARY_PASS = 1/2` |
| **RQ5** | hiệu quả | **KHÔNG NGƯỠNG** — mô tả kèm mẫu số | 19 lượt · 97 869 token · 13 981 token/ca đạt · 2,71 lượt/ca | `TELEMETRY_BUDGET_LEDGER.json` | 9 ca | **PARTIAL** | "13 981 token cho mỗi mô phỏng phục vụ đúng, trên 7 ca đạt" | so sánh liên lượt khi mẫu số khác nhau | dự báo lệch +31 % (`thought_tokens` 34 %) |

---

## D. Tuyên bố ĐÃ TRÔI — đính chính, giữ nguyên bản gốc

| ID | Tuyên bố trong tài liệu | Bằng chứng khiến nó chưa phù hợp | Trạng thái | Hành động |
|---|---|---|---|---|
| **D-1** | Ma trận đăng ký, Bảng 2: *"11 đại lượng / 7 ca"* | `SCORING_CORRECTION.json` có **12** mục `quantities_SUA`, tất cả khớp; cảnh 3D phát đúng 12 số đo | **CONTRADICTED** *(bởi chính artifact của lượt đo)* | **KHÔNG sửa** văn bản đăng ký trước. Đính chính đã ghi ở Chương 4 Bảng 4.6, `CURRENT_STATE`, `STATUS_LEDGER` và báo cáo thực thi (wave `PRODUCT_UI_RESULT_RENDERING`) |
| **D-2** | `THESIS_DRAFT §4`, bảng ngoài phạm vi: *"mặt cong (cầu, trụ, nón)"*, *"khối không lồi"*, *"phương trình mặt phẳng"* — và tóm tắt: *"chỉ khối đa diện lồi, không mặt cong"* | Lượt đo cuối **phục vụ** `p3` cầu, `p4` trụ, `p5` nón, `p6`/`p7` thiết diện elip xiên, `p2` đáy ngũ giác **lõm**; `p6` dùng phương trình mặt phẳng `2x − z + 12 = 0` | **CONTRADICTED** | Ghi **đính chính bên trên bảng gốc** trong `THESIS_DRAFT`; bảng gốc giữ nguyên làm bằng chứng lịch sử |
| **D-3** | `product_capability.py`, ba dòng khối cong: lý do *"MÔ HÌNH: chưa đo"* | Lượt đo cuối **đã đo** mô hình trên cầu/trụ/nón/lõm/thiết diện xiên: 5/5 phục vụ đúng | **CONTRADICTED** *(chỉ ở phần LÝ DO)* | ⚠️ **Trạng thái `foundation_only` vẫn ĐÚNG** — `n = 1` mỗi họ không đủ để bật. Chỉ chuỗi lý do đã cũ. Sửa nó chạm `backend/app` ⇒ đổi candidate ⇒ **ngoài phạm vi wave này**; chuyển thành nợ |
| **D-4** | `THESIS_DRAFT` tóm tắt và §1.7: *"cỡ mẫu mỗi lượt thực nghiệm nhỏ (4–6 đề)"*, *"bốn lượt thực nghiệm"* | Lượt đo cuối có **9 ca** (7 dương + 2 âm) và là lượt thứ **năm**; bản thảo không nhắc nó | **CONTRADICTED** | Đính chính trong `THESIS_DRAFT`; thân Chương 4 của bản thảo và `docs/thesis/CHAPTER_4` hiện là **hai thân rời nhau** — hợp nhất thuộc wave tích hợp bản thảo |

---

## E. Chín mức năng lực — không gộp

| mức | trạng thái | bằng chứng | mẫu |
|---|---|---|---|
| hệ **biểu đạt** được | **PROVED** | 0 phép IR mới, 10/10 họ trong phạm vi | 7 ca |
| **kernel tính đúng** | **PROVED** | 12/12 đại lượng, oracle độc lập | 12 đại lượng |
| mô hình **tự tìm ra phép** | **PARTIAL** | 6/7 lần đầu | n = 1 mỗi họ |
| đúng **ngay lượt đầu** | **PARTIAL** | 6/7 | n = 1 |
| đúng **sau vòng sửa** | **PARTIAL** | 7/7 (1/1 lượt sửa thành công) | n = 1 |
| **UI hiển thị** được | **PROVED** | 66/66 phép kiểm, 7/7 dương, 2/2 âm, 0 ngoại lệ, 6/6 tiêm lỗi | 9 ca |
| **hình học trình bày đúng** | **PARTIAL** | hidden-line 23/23 PASS; visual fidelity 39/41 | 3–9 ca |
| **ổn định** qua nhiều lượt | **NOT_MEASURED** | `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`, khoá **trước** lượt chạy | — |
| **sẵn sàng triển khai** | **NOT_MEASURED** | `PRODUCT_PROMOTION_ELIGIBLE = NO`; `PRODUCT_DEPLOYMENT_READY = NOT_CLAIMED` | — |

---

## F. Phạm vi hình học — ba nhóm, không gộp thành "đã hỗ trợ đầy đủ"

**Đã chứng minh trên benchmark cuối** (mô hình tự sinh, hệ phục vụ, đáp số khớp
oracle): điểm–đường–vectơ–mặt · đa giác và thiết diện phẳng · đa diện lồi · đa
diện **lõm** · hình cầu · thiết diện tròn của khối cong · hình trụ · hình nón ·
thiết diện xiên (elip) của trụ · thiết diện xiên của nón — **10/10 họ trong
phạm vi**, mỗi họ **một ca, một lượt**.

**`foundation_only` ở tầng SẢN PHẨM** (hệ chạy được, nhưng chưa bật cho người
học vì `n = 1` chưa đủ): khối cong (cầu · trụ · nón), đa diện lõm, thiết diện
xiên. Thẩm quyền: `product_capability.py`.

**Ngoài phạm vi vì lý do KIẾN TRÚC đo được** (không phải "chưa kịp làm"): khối
tròn xoay tổng quát (không có tích phân ký hiệu; `Radical` không đóng) · khối
ghép/bù cần boolean (không có thẩm quyền boolean; điều kiện TOÀN CỤC mà
`kiem_mat_phang_don` khai là không kiểm được). Bằng chứng thuộc lớp **chứng minh
vắng mặt**, không phải một mã lỗi mang tên hai họ ấy.

---

## G. Danh tính phép đo — hai giá trị KHÁC NHAU

| | giá trị | ý nghĩa |
|---|---|---|
| candidate **lịch sử** (lúc đo) | `d72db7c3…` | ghim trong `thesis_final_acceptance_policy.json`, `created_before_live_run = true`. **Bất biến.** |
| candidate **hiện tại** của kho | `d72db7c3…` | đo lại bằng `freeze_evaluation_candidate.measured_system_hash()` |

Hai giá trị hiện **trùng nhau**, nhưng chúng là hai khái niệm khác nhau và phải
giữ hai chỗ. Không cập nhật candidate lịch sử để khớp mã hiện tại — làm vậy là
khiến hợp đồng khai rằng lượt đo đã đo một bản mã nó chưa từng đo.

`CACHE_VERSION = 94` ở cả hai thời điểm.
