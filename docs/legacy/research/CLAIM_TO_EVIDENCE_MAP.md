# CLAIM_TO_EVIDENCE_MAP — ánh xạ tuyên bố ↔ bằng chứng nội bộ

> Nguồn máy đọc: `docs/evaluation/geometry/research-gap-formalization/CLAIM_AUDIT.json`.
> Mọi số đọc **trực tiếp từ artifact tại HEAD `df8ad21`**, ngày 2026-09-10.
> `APPLICATION_LLM_CALLS = 0`.
>
> Bảng này **không thay** `docs/thesis/CLAIM_EVIDENCE_MATRIX.md` (bảng chuẩn của
> khoá luận). Nó thêm đúng một thứ bảng kia không có: **lớp bằng chứng**.

## 0. Bốn lớp bằng chứng — không được trộn

| lớp | nghĩa | bản hệ được đo |
|---|---|---|
| `FINAL_LIVE_EVIDENCE` | lượt gọi model **thật**, đăng ký trước, chạy **đúng một lần**: `thesis-final-20260908T160224Z` | candidate `d72db7c3…` · `CACHE_VERSION 94` |
| `FROZEN_BENCHMARK_EVIDENCE` | lượt đo đã niêm phong, artifact **bất biến**, không chạy lại | tuỳ artifact |
| `DEVELOPMENT_EVIDENCE` | phép đo phát triển, không đăng ký trước | tuỳ |
| `CURRENT_REPLAY_EVIDENCE` | chạy lại được **hôm nay**, 0 lượt gọi model | candidate `96a9368b…` · `CACHE_VERSION 95` |

⛔ **Không được viết một số `CURRENT_REPLAY_EVIDENCE` như thể đó là số của lượt
live lịch sử.** Hai lớp đo **hai bản hệ khác nhau**.

### ⚠️ Trôi danh tính — đo lại hôm nay

| | lúc đo live | tại HEAD |
|---|---|---|
| candidate | `d72db7c3…` | **`96a9368b50603c79…`** |
| `CACHE_VERSION` | `94` | **`95`** |

Đo bằng `freeze_evaluation_candidate.py --verify` (exit 0, 92 file) và
`lock_cache_identity.py --verify` (exit 0). Nguyên nhân: `backend/app` đổi **sau**
lượt đo cuối — lần đầu ở `PRODUCT_RESPONSE_CONTRACT_ALIGNMENT` (`d72db7c3 →
e40de3b1`, đã khai ở `CANDIDATE_DIVERGENCE.json`), rồi tiếp ở các wave hoàn thiện.

⚠️ **`docs/thesis/CLAIM_EVIDENCE_MATRIX.md` §G đã trôi.** Nó ghi *"hai giá trị
hiện trùng nhau"* và *"`CACHE_VERSION = 94` ở cả hai thời điểm"*. Câu ấy **đúng
lúc viết** và **sai hôm nay**. Theo lệ kho: giữ nguyên bản gốc, ghi đính chính —
đây là đính chính.

## 1. Bảng ánh xạ

| # | Tuyên bố | Artifact | Test / lệnh kiểm | Kết quả | Mức bằng chứng | Giới hạn |
|---|---|---|---|---|---|---|
| E01 | 7/7 ca dương **eventual servable** | `FINAL_SUMMARY.json` | `thesis_final_acceptance_plan.py` | `FINAL_SERVABLE = 7/7` | `FINAL_LIVE_EVIDENCE` | n = 1 mỗi họ, một lượt; **không held-out** |
| E02 | 6/7 **first-attempt** servable | `FINAL_SUMMARY.json` | như trên | `FIRST_ATTEMPT = 6` · `ONE_REPAIR = 1` | `FINAL_LIVE_EVIDENCE` | **không ngưỡng** (`no_threshold_by_design`); cấm gọi 6/7 là *"độ chính xác của hệ"* |
| E03 | 2/2 ca âm **fail-closed** | `FINAL_SUMMARY.json` | như trên | `NEGATIVE_FAIL_CLOSED = 2` | `FINAL_LIVE_EVIDENCE` | `TARGET_BOUNDARY_PASS = 1/2` — `n1` dừng **trước** cổng phủ nên không chạm mã đã đăng ký |
| E04 | **12/12** đại lượng chính xác | `SCORING_CORRECTION.json` | `doi_chieu_ket_qua_cuoi.py` | `DAP_SO_KHOP 12/12` từng ký tự + khớp oracle | `FINAL_LIVE_EVIDENCE` | văn bản **đăng ký trước** ghi 11 → đính chính **D-1**, không hồi tố sửa |
| E05 | **0** silent wrong answer | `FINAL_SUMMARY.json` + `SCORING_CORRECTION.json` | `score_thesis_final_acceptance.py` | `SILENT_WRONG_ANSWER = 0` | `FINAL_LIVE_EVIDENCE` | ⚠️ bản gốc ghi **6** và **sai**: bộ đo tra đáp số bằng tên biến của GOLD trong khi tên biến do **mô hình tự đặt**. `MEASUREMENT_FAILURE_COUNT = 1` |
| E06 | trace + Scene3D **dẫn xuất** từ vết | `FINAL_SUMMARY.json`; artifact demo | `replay_demo_cases.py` | `TRACE 7/7` · `SCENE3D 7/7`; `producer`/`depends` đủ | `FINAL_LIVE` + `CURRENT_REPLAY` | đo **cấu trúc** cảnh, không đo chất lượng sư phạm |
| E07 | **hidden-line động** | `SCENE3D_DYNAMIC_HIDDEN_LINES_AND_READABILITY.md` | oracle che khuất độc lập + 6 phép tiêm | `OCCLUSION 3/3` · 6/6 tiêm bị bắt | `CURRENT_REPLAY_EVIDENCE` | **sau** lượt live, trên candidate khác. Trước bản vá: **không có hidden-line nào** |
| E08 | **khối lõm** thể tích đúng | `FINAL_SUMMARY.json` | oracle shoelace có dấu | `p2 = 96`, `CORRECT_SERVABLE_RESULT` | `FINAL_LIVE_EVIDENCE` | bao đóng v1 = biên **kín, một vỏ, mọi mặt phẳng và đơn**; trước bản vá hệ **phục vụ** số sai (`28` thay vì `20`) |
| E09 | **thiết diện elip** trụ và nón | `FINAL_SUMMARY.json` | ba oracle độc lập | `p6 = 25π√5` · `p7 = 2π√6` | `FINAL_LIVE_EVIDENCE` | n = 1 mỗi họ |
| E10 | **mặt phẳng từ phương trình** | `FINAL_SUMMARY.json`; `PLANE_FROM_EQUATION_REPRESENTATION.md` | bất biến nguồn | `p6` dùng `2x − z + 12 = 0` | `FINAL_LIVE_EVIDENCE` | chỉ qua được sau `chuan_hoa_dau_tru` (U+2212) — trước đó dấu trừ toán học phá bất biến nguồn **trên chương trình đúng** |
| E11 | **structured refusal** | `PRODUCT_RESPONSE_CONTRACT_ALIGNMENT.md` | 73/73 phép kiểm Chrome thật · 7/7 tiêm | `n1` = `semantic_program_invalid` @ `semantic_program`; `n2` = `requested_operation_uncovered` @ `structural_coverage` | `CURRENT_REPLAY_EVIDENCE` | `n1` **không** được khai là *"ngoài bao đóng"* — hệ dừng trước cổng phủ nên chỉ biết chương trình không hợp lệ |
| E12 | **số lượt gọi và token** | `TELEMETRY_BUDGET_LEDGER.json` | — | 19 lượt · 0 retry · **97 869** token · 13 981 token/ca đạt · 2,71 lượt/ca | `FINAL_LIVE_EVIDENCE` | vượt dự báo **+31 %** (`thoughts_tokens` 34 %); mẫu số 7 ca — **không** so được với lượt đo mẫu số khác |
| E13 | candidate **lịch sử** ↔ **hiện tại** | `thesis_final_acceptance_policy.json`; freeze/lock verify | hai lệnh `--verify` | lịch sử `d72db7c3` / v94 · hiện tại **`96a9368b`** / **v95** | `FINAL_LIVE` + `CURRENT_REPLAY` | hai khái niệm khác nhau, giữ **hai chỗ**; không cập nhật cái lịch sử cho khớp |
| E14 | `STABILITY_UNDER_ACCEPTANCE` | `FINAL_SUMMARY.json` | — | **`NOT_MEASURED`** | `FINAL_LIVE_EVIDENCE` | kết luận **đã biết trước** lượt đo, không suy từ kết quả |
| E15 | **bài mới ≠ mã mới** | `FINAL_SUMMARY.json` + quét AST | `test_missing_family_roadmap.py` | `NEW_IR_OPERATIONS = 0` · `NEW_MEMORY_TYPES = 0` · `NEW_PER_PROBLEM_MODULES = 0` | `FINAL_LIVE_EVIDENCE` | chỉ đúng **trong IR hiện có** |
| E16 | tập demo tất định | — | `replay_demo_cases.py` · `audit_demo_crash_surface.py` | 5/5 (`REDUCED_CHAIN 1/1`) · 6/6 biên, 0 đường ném | `CURRENT_REPLAY_EVIDENCE` | sáu biên **đã biết**, không phải fuzzing |
| E17 | UI hiển thị được kết quả | `PRODUCT_UI_RESULT_RENDERING_AND_DEMO_ACCEPTANCE.md` | 66 phép kiểm Chrome thật · 6 tiêm | 9/9 envelope · **12/12 đáp số đọc trên màn hình** · 0 ngoại lệ | `CURRENT_REPLAY_EVIDENCE` | `DEMO_READY_ON_FROZEN_CASES = YES` nhưng `PRODUCT_DEPLOYMENT_READY = NOT_CLAIMED` |
| E18 | nhãn hiển thị **12/12** | `DISPLAY_NAME_FINAL_POLISH_AND_RELEASE_REFRESH.md` | cổng nhãn | 10/12 → **12/12**, placeholder 2 → 0 | `CURRENT_REPLAY_EVIDENCE` | đóng góp **C4 sản phẩm**, không phải đóng góp khoa học |

## 2. Chín mức năng lực — trạng thái hôm nay

Giữ nguyên cách tách của `CLAIM_EVIDENCE_MATRIX.md §E`, thêm cột lớp bằng chứng:

| mức | trạng thái | lớp |
|---|---|---|
| hệ **biểu đạt** được | `PROVED` | `FINAL_LIVE` |
| **kernel tính đúng** | `PROVED` | `FINAL_LIVE` |
| mô hình **tự tìm ra phép** | `PARTIAL` | `FINAL_LIVE` |
| đúng **ngay lượt đầu** | `PARTIAL` (6/7) | `FINAL_LIVE` |
| đúng **sau vòng sửa** | `PARTIAL` (7/7, 1/1) | `FINAL_LIVE` |
| **UI hiển thị** được | `PROVED` | `CURRENT_REPLAY` |
| **hình học trình bày đúng** | `PARTIAL` | `CURRENT_REPLAY` |
| **ổn định** qua nhiều lượt | **`NOT_MEASURED`** | — |
| **sẵn sàng triển khai** | **`NOT_MEASURED`** | — |

## 3. Bằng chứng CÒN THIẾU cho một bài báo

Xếp theo chi phí tăng dần. Không mục nào bắt buộc cho **khoá luận**; ba mục đầu
gần như bắt buộc cho **bài báo**.

| # | thiếu gì | vì sao cần | chi phí ước lượng |
|---|---|---|---|
| A1 | **k ≥ 3 lượt lặp trên cùng bộ ca** | biến `STABILITY_UNDER_ACCEPTANCE` từ `NOT_MEASURED` thành một con số. Không có nó, mọi tỉ lệ chỉ là giai thoại | ~3× ngân sách lượt cuối (≈ 57 lượt gọi, ≈ 300 K token) |
| A2 | **bộ ca held-out do người ngoài soạn** | `EVALUATION_CLASS` hiện là `FROZEN_FINAL_DEVELOPMENT_BENCHMARK`; reviewer sẽ hỏi ngay | cần một người ngoài + một lượt niêm phong |
| A3 | **mẫu lớn hơn n = 1 mỗi họ** | 10 họ × 1 ca không đỡ được bất kỳ phát biểu nào về độ phủ thực tế | soạn ca + gold preflight |
| A4 | **so sánh trực tiếp với một baseline** | ma trận hiện so **định tính**. Một baseline chạy được (ví dụ: LLM sinh thẳng toạ độ, không có cổng) sẽ đo được giá trị của tầng kiểm chứng | vừa — baseline chạy offline được |
| A5 | **đọc toàn văn 5 công trình gần nhất** | ma trận có nhiều ô `NR` chỉ vì mới đọc tóm tắt; đặc biệt **VeriGeo** quyết định C1.1 giữ hạng hay bị hạ | thấp, không tốn quota |
| A6 | **nghiên cứu người dùng** | điều kiện bắt buộc nếu muốn nhắm bài về **hiệu quả giáo dục** | cao — thiết kế nghiên cứu riêng, không trộn vào kết quả kỹ thuật |
