# THESIS_FINAL_ACCEPTANCE_EXECUTION

> **Lượt đánh giá cuối ĐÃ CHẠY, 2026-09-08.** Một lượt duy nhất, trên candidate
> đã đóng băng, bằng runner đã chứng nhận. `RUN_VALIDITY = VALID`.

```
PRE_LIVE_GUARD  = PASS   (8/8 điều kiện)
RUN_VALIDITY    = VALID
RUN_ID          = thesis-final-20260908T160224Z
APPLICATION_LLM_CALLS = 19   (analyze 9 · synthesis 9 · repair 1)

FIRST_ATTEMPT_SERVABLE        6/7
ONE_REPAIR_EVENTUAL_SERVABLE  1/1
FINAL_SERVABLE                7/7
EXACT_ANSWER_PASS             7/7
ORACLE_NUMERIC_AGREEMENT      7/7
NEGATIVE_FAIL_CLOSED          2/2
SILENT_WRONG_ANSWER_COUNT     0
UNHANDLED_EXCEPTION_COUNT     0
```

⚠️ **Con số đáp số ở trên là bản ĐÃ ĐÍNH CHÍNH.** Bộ chấm của lượt gốc tra sai
chỗ và báo `SILENT_WRONG_ANSWER_COUNT = 6` trên một hệ không phạm lỗi nào —
xem §5. Artifact thô giữ **nguyên byte**; đính chính nối bằng băm.

---

## 1. Tiền kiểm — 8/8, không lượt gọi provider nào

| | điều kiện | kết quả |
|---|---|---|
| 1 | working tree sạch | `5a525e8`, sạch, `git diff --check` sạch |
| 2 | API key tồn tại (không in giá trị) | có · 53 ký tự · tiền tố `AQ.A…` |
| 3 | mười giá trị danh tính khớp | **10/10** + 8 phép kiểm băm của loader |
| 4 | certifier chạy bằng provider stub | đã chạy |
| 5 | nhãn chứng nhận | **15/15 PASS**, `REAL_PROVIDER_CALLS = 0` |
| 6 | manifest ghi được trước lượt gọi đầu | `MANIFEST_BEFORE_FIRST_CALL PASS` |
| 7 | corpus cố định | **7 dương + 2 âm** |
| 8 | ngân sách | 25 logic · 100 vật lý · 196 000 token |

---

## 2. Kết quả từng ca

Chín cột **độc lập**, không cột nào suy từ cột khác.

| ca | họ | chặng | grounding | coverage | ir_static | nguồn | runtime | postcond | trace | scene3d | servable | đáp số |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `p1` | linear · section · lồi | A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `72` · `9` · `3√6` |
| `p2` | đa diện **lõm** | A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `96` |
| `p3` | cầu · thiết diện tròn | **B** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `4500π` · `144π` |
| `p4` | trụ | A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `360π` · `120π` |
| `p5` | nón | A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `100π` · `65π` |
| `p6` | elip xiên **trụ** | A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `25π√5` |
| `p7` | elip xiên **nón** | A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `2π√6` |

**12/12 đại lượng khớp CHÍNH XÁC** chuỗi hiển thị mong đợi (⚠️ đính chính
2026-09-09: bản gốc ghi 11), và cả 12 khớp
oracle độc lập trong dung sai đã khoá.

### Ca âm

| ca | ranh giới nhắm | fail-closed | chạm ranh giới | mã thật | phán quyết |
|---|---|---|---|---|---|
| `n1` | `solid_of_revolution_general` | ✓ | ✗ | `UNANCHORED_DERIVED_ASSUMPTION` (R0, trong `KHONG_DUOC_SUA`) | `UNRELATED_FAIL_CLOSED` |
| `n2` | `composite_boolean` | ✓ | ✓ | `requested_operation_uncovered` @ `structural_coverage` | `HONEST_UNSUPPORTED_REFUSAL` |

`NEGATIVE_FAIL_CLOSED = 2/2` — **ngưỡng bắt buộc, đạt**. Không ca âm nào được
phục vụ đáp số nào (`SERVED_ANY_QUANTITY = []` ở cả hai).

`TARGET_BOUNDARY_PASS = 1/2` — **được đo, KHÔNG phải ngưỡng**, đúng như đã
khoá trước. Xem §6 để biết vì sao `n1` không thể chạm mã đã pre-register.

### Chặng B — một lượt sửa, tiếp tục chứ không chạy lại

`p3` hỏng ở chặng A: `IR_OPERAND_TYPE: 'S' — cần solid, có curved_solid`. Lượt
sửa dùng lại **hợp đồng đã đóng băng** (`d2d7b46f…`), **raw candidate** của
chặng A (`445d7b45…`) và **chẩn đoán** (`a59bcc13…`); `analyze_calls_in_stage_b
= 0`. Kết quả: `served` với `4500π` và `144π`.

Đây là bằng chứng đường tiếp tục chạy được trên **đầu ra thật của mô hình**,
không chỉ trên stub.

---

## 3. Sổ lượt gọi và ngân sách

| | |
|---|---|
| `LOGICAL_CALLS` | **19** — analyze 9 · synthesis 9 · repair 1 |
| `PHYSICAL_API_ATTEMPTS` | **19** |
| `TRANSPORT_RETRIES` | **0** |
| input / output / thought / cached | 49 481 · 14 390 · 33 998 · 1 859 |
| `TOKENS_ACTUAL` | **97 869** |
| còn lại trong trần | 6 lượt logic · 81 lần thử · 98 131 token |
| `VUOT_NGAN_SACH` | **false** |

`TOKENS_PER_CORRECT_SERVABLE` = **13 981** · `CALLS_PER_CORRECT_SERVABLE` =
**2.71** (mẫu số 7 ca đạt — in kèm, và **không** so được với một lượt đo có mẫu
số khác).

⚠️ Token thực **97 869** so với dự kiến **74 763** (+31 %). Nguyên nhân đọc
được từ sổ: `thoughts_tokens` chiếm **34 %** tổng, và trung vị lịch sử dùng để
dẫn ngân sách không tách riêng phần ấy. Trần **196 000** vẫn thừa 50 %, nên
ngân sách đúng ở chỗ nó phải đúng — là một cái phanh, không phải một dự báo.

---

## 4. Trả lời câu hỏi nghiên cứu

Mỗi kết luận ghi kèm **mức bằng chứng**.

| RQ | kết quả | mức bằng chứng |
|---|---|---|
| **RQ1** độ phủ | 7 ca phủ **10/10 họ trong phạm vi**; `NEW_IR_OPERATIONS = 0`, `NEW_MEMORY_TYPES = 0`, `NEW_PER_PROBLEM_MODULES = 0` | **end-to-end** |
| **RQ2** tính đúng | `EXACT_ANSWER 7/7` · `ORACLE 7/7` · `SOURCE_INVARIANTS 7/7` · `POSTCONDITIONS 7/7` · `SCENE3D 7/7` | **end-to-end** + **đúng tất định** (oracle độc lập) |
| **RQ3** tự sinh | `FIRST_ATTEMPT 6/7` · `RECOVERY_WITHIN_ONE_REPAIR 1/1` ⇒ **7/7 sau ≤1 lượt sửa** | **model discoverability**, n = 1 mỗi họ |
| **RQ4** an toàn | `NEGATIVE_FAIL_CLOSED 2/2` · `SILENT_WRONG_ANSWER 0` · `UNHANDLED_EXCEPTION 0` | **end-to-end** |
| **RQ5** hiệu quả | 19 lượt · 97 869 token · 13 981 token/ca đạt | **end-to-end**, mô tả |

### Chín tuyên bố

| | kết quả | ghi chú |
|---|---|---|
| **C1** bài mới ≠ mã mới | ✅ | 0 phép IR mới, 0 kiểu mới, 0 module theo bài |
| **C2** tính chính xác tuyệt đối | ✅ | 12/12 đại lượng, gồm `3√6` · `25π√5` · `2π√6` |
| **C3** kiểm chứng nguồn | ✅ | 7/7 — và bản vá dấu trừ ở wave trước là điều kiện để `p6` qua được |
| **C4** trace + Scene3D dẫn xuất | ✅ | 7/7 đủ loại vật đã pre-register |
| **C5** đáp số ≠ hình | ✅ (phương pháp) | ba cột ghi riêng; §5 cho thấy vì sao điều đó quan trọng |
| **C6** tự sinh của AI | **PARTIAL** | 6/7 first-attempt, **mô tả, không ngưỡng** |
| **C7** fail-closed | ✅ | 2/2, 0 đáp số sai phát ra |
| **C8** hiệu quả token | ✅ (mô tả) | kèm mẫu số |
| **C9** giới hạn đề tài | **PARTIAL** | fail-closed 2/2; chạm đúng ranh giới 1/2 — xem §6 |

```
PRODUCT_PROMOTION_ELIGIBLE = NO
STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
```

Cả hai là kết luận **đã biết trước lượt đo**: một ca mỗi họ, chạy một lần, nên
`requires_stability_measured` không thoả được. Không suy từ kết quả.

---

## 5. ⚠️ MỘT LỖI ĐO, và nó suýt tố cáo hệ

> Đây là phần quan trọng nhất của báo cáo này.

Lượt gốc báo `SILENT_WRONG_ANSWER_COUNT = **6**` — tức sáu lần hệ phát ra một
đáp số sai. Nếu con số ấy đúng, nó phá chính luận điểm của đề tài.

**Nó không đúng.** Bộ chấm tra đáp số bằng `final_memory[<tên biến của GOLD>]`,
trong khi tên biến là thứ **mô hình tự đặt**:

| ca | gold | mô hình viết |
|---|---|---|
| `p1` | `V` · `S_T` · `d` | `the_volume_sabcd` · `area_T` · `dist_S_BD` |
| `p2` | `V` | `V_S_MNPQR` |
| `p5` | `V` · `Sxq` | `the_tich_khoi_non` · `dien_tich_xung_quanh_hinh_non` |
| `p6` | `S_E` | `dien_tich_elip_e` |

Nên `actual_display = None` ở 6/7 ca **có đáp số hoàn toàn đúng**. Bộ đo tố cáo
hệ một tội nó không phạm — chiều sai đắt nhất trong cả tuyến này.

### Vì sao chứng nhận stub KHÔNG bắt được

Stub trả về **chính gold program**, nên tên witness của "mô hình" luôn **trùng**
tên gold, và phép tra sai không bao giờ lộ. *Một provider giả giống bản mẫu quá
mức thì không kiểm được thứ chỉ sai khi mô hình được tự do.*

### Sửa

- **Ánh xạ theo `kind` của nghĩa vụ** — thứ do `analyze` khai và taxonomy đóng
  băng quyết định, không do mô hình đặt tên. `kind` là khoá **duy nhất** trong
  mọi ca của corpus (đo trên cả 9); guard **ném** nếu điều đó thôi đúng.
- Thêm nhãn chứng nhận thứ **16**:
  `SCORING_SURVIVES_MODEL_CHOSEN_WITNESS_NAMES` — một ca stub **đổi tên** mọi
  witness. Kèm phép tiêm khôi phục hành vi cũ để chứng minh guard đỏ được.
- Đính chính offline (`score_thesis_final_acceptance.py`), **0 lượt gọi**,
  artifact thô **nguyên byte**, băm của ba file được đính chính ghi vào
  `SCORING_CORRECTION.json`.

```
SILENT_WRONG_ANSWER_COUNT   gốc 6  →  sửa 0
EXACT_ANSWER_PASS           gốc 1  →  sửa 7
```

`MEASUREMENT_FAILURE_COUNT = 1` · `MODEL_FAILURE_COUNT = 1` (p3 chặng A, đã
phục hồi) · `SYSTEM_FAILURE_COUNT = 0` · `ATTRIBUTION_UNRESOLVED_COUNT = 0`.

---

## 6. ⚠️ `n1` không chạm được mã đã pre-register — và điều đó đúng

`n1` khai `expected_codes = [requested_operation_uncovered, input_not_grounded]`.
Thực tế mô hình **bịa ba điểm** (`O`, `P_x2_y0`, `P_x2_y4`) để xấp xỉ khối tròn
xoay, và bị chặn bằng `UNANCHORED_DERIVED_ASSUMPTION` — một mã thuộc
`KHONG_DUOC_SUA`, nên `stage_semantic_program` trả `(None, …)` **trước** khi
tới `verify_and_compile`. Không có route outcome ⇒ **không có `error_code` nào
để so**.

Nên đây là một **giới hạn của phép pre-registration**, không phải của hệ:
đường từ chối R0 *bên trong* vòng tổng hợp không phát ra mã mà `cham_ca_am`
đọc được. Ghi nguyên trạng, **không** hồi tố sửa `expected_codes` cho khớp —
sửa kỳ vọng sau khi thấy kết quả là xoá đúng thứ pre-registration tồn tại để giữ.

Hành vi của hệ vẫn đúng: nó **từ chối**, không phục vụ, và từ chối vì mô hình
định bịa dữ kiện — đúng ranh giới R0.

---

## 7. Danh tính trước/sau

| | |
|---|---|
| `CANDIDATE_HASH` | `d72db7c3…` — **không đổi** trước/sau |
| `CACHE_VERSION` | `94` — không đổi |
| `CORPUS_HASH` | `2eb3f24d…` — không đổi |
| `EXPECTED_RESULTS_HASH` | `1099924b…` — không đổi |
| `GOLD_PREFLIGHT_HASH` | `985c8922…` — không đổi |
| `POLICY_HASH` | `a44469b0…` (1.1.0) — không đổi |
| `SCORER_HASH` | `4f7cae90…` — không đổi |
| `IDENTITY_AFTER_RUN_STABLE` | **true** |
| `RUNNER_HASH` **lúc chạy** | `19c4c311…` (bất biến trong `manifest.json` của lượt) |
| `RUNNER_HASH` **hiện tại** | `7c77d0ac…` — đổi SAU lượt đo, do bản vá ánh xạ tên witness |

⚠️ Runner đổi **sau** lượt đo, nên khoá tự rơi về `PENDING` kèm băm trước/sau —
guard `_giu_khoa_runner_cu` làm đúng việc. Đã chứng nhận lại (**16/16**) rồi
khoá lại. `IDENTITY_LOCK.LUOT_DA_CHAY` giữ danh tính của lượt đã chạy để không
ai phải suy từ thời điểm commit.

---

## 8. Artifact

`docs/evaluation/geometry/thesis-final-acceptance/thesis-final-20260908T160224Z/`
— **26 file**, băm SHA-256 đầy đủ ở `ARTIFACT_HASHES.json`.

| tên trong kho | tên §9 gọi |
|---|---|
| `manifest.json` · `stage_a_first_attempt.json` | như nhau |
| `stage_b_recovery.json` | `stage_b_one_repair.json` |
| `final_scoring.json` | `scoring.json` |
| `FINAL_SUMMARY.json` · `ARTIFACT_HASHES.json` · `TELEMETRY_BUDGET_LEDGER.json` | như nhau |
| `raw/<ca>/<stage>_<n>.json` | raw analyze/provider/candidate |
| `SCORING_CORRECTION.json` | bản đính chính §8 |

Giữ **một** bộ file với tên của runner thay vì nhân đôi nội dung cho khớp tên
đặc tả: hai bản sao là hai nguồn sự thật, và bản thứ hai sẽ trôi.

---

## 9. Cổng kết thúc

| cổng | kết quả |
|---|---|
| danh tính trước/sau | khớp, `IDENTITY_AFTER_RUN_STABLE = true` |
| certifier (không provider) | **16/16 PASS**, `REAL_PROVIDER_CALLS = 0` |
| `freeze_evaluation_candidate --verify` | exit 0 — 92 file, `d72db7c3…` |
| `lock_cache_identity --verify` | exit 0 @ v94 |
| `git diff --check` | sạch |
| test runner/scorer/report | alignment **62** · matrix **49** |
| `pytest -q` | xem §10 |
| backend/frontend sản phẩm | **INHERITED** — 0 byte mã sản phẩm đổi trong wave này |

---

## 10. Kết luận

```
RUN_VALIDITY = VALID
NEXT_ACTION  = THESIS_RESULTS_ANALYSIS_AND_CHAPTER_DRAFTING
```

Hệ phục vụ **7/7** bài trong phạm vi với đáp số **chính xác tuyệt đối**, dựng
đúng hình, truy đúng nguồn, và **từ chối 2/2** bài ngoài bao đóng mà không phát
ra một con số nào. Trong 19 lượt gọi và 98 nghìn token.

Ba điều phải đi kèm mọi con số ở trên:

1. **Không phải held-out.** `EVALUATION_CLASS = FROZEN_FINAL_DEVELOPMENT_BENCHMARK`.
2. **n = 1 mỗi họ, một lượt.** Không nói được gì về độ ổn định;
   `PRODUCT_PROMOTION_ELIGIBLE = NO` là kết luận đã biết trước.
3. **Bộ đo đã sai một lần trong chính lượt này** (§5), và chỉ được phát hiện vì
   con số phi lý đủ lớn để buộc phải soi lại. Một sai lệch nhỏ hơn có thể đã đi
   thẳng vào khoá luận.
