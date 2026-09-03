# ACCEPTANCE_RUNNER_INTEGRITY — làm bộ đo đủ tư cách làm bằng chứng

> Thực hiện **2026-09-04**, trên HEAD `3b61e9b`, cây sạch lúc bắt đầu.
> **APPLICATION_LLM_CALLS = 0.** Không đổi prompt, lược đồ, IR, kernel, checker.
> **V3 KHÔNG chạy, seed KHÔNG rút, pool giữ nguyên niêm phong** (§26).
> Số của probe §18 **không hồi tố** (§27).

## 0. Kết luận trước

```
ACCEPTANCE_RUNNER_INTEGRITY = CLOSED
RUNNER_CERTIFICATION        = PASS   (5 kịch bản, 0 lượt gọi model)
HISTORICAL_INCIDENT_RED_TESTS = PASS (8 sự cố, mỗi cái tiêm lại rồi đòi đỏ)
RESULT_EXTRACTION_FROM_SCENE3D = 0
STABLE_CAPABILITY_HASH_CHANGED = NO  ·  CACHE_VERSION_CHANGED = NO
```

Toàn bộ wave nằm trong `backend/scripts/` và `backend/tests/` — **không thuộc
`MEASURED_SYSTEM_PATHS`**, nên candidate không phải đóng băng lại và danh tính
sản phẩm không nhúc nhích. Đó là kiểm chứng của §29, không phải may mắn: bộ đo
được phép cứng cáp thêm mà hệ được đo giữ nguyên.

## 1. Vì sao một tầng chung, không phải vá từng runner

Kho có ~20 script `run_*`/`probe_*`, mỗi cái **tự viết lấy** phần ghi artifact,
đếm token, phân loại lỗi. Bảy sự cố đề bài liệt kê là bảy bản sao của cùng một
thiếu sót, và vá từng nơi là hẹn lần thứ tám ở nơi thứ hai mươi mốt.

Hai sự cố **vẫn còn sống trong mã** lúc wave này mở, tôi kiểm bằng máy chứ không
tin báo cáo cũ:

| | chỗ | tình trạng khi mở wave |
|---|---|---|
| ③ | `run_curved_acceptance.py:215` — `canh = (env.get("scene3d") or {}).get("objects")`, rồi `dap_so_khop` tính từ đó | **CÒN**. Phán quyết đúng/sai của cả bộ đo dựng trên tầng VẼ |
| ⑦ | `_phan_lop_loi()` khớp chuỗi tiếng Việt (`"validation error" in err`) | **CÒN**. Đổi một chữ trong thông điệp là đổi con số `REPAIR_ELIGIBLE` |

Runner lịch sử **không bị viết lại** (§21) — bằng chứng lịch sử giữ nguyên hình
dạng của nó. Runner MỚI đi qua tầng chung.

## 2. Sở hữu (§2)

| câu hỏi | trước wave | sau wave |
|---|---|---|
| `RUNNER_OWNER` | mỗi script tự lo | script gọi, tầng chung cưỡng chế |
| `ARTIFACT_WRITER_OWNER` | `Path.write_text` rải rác | `acceptance_integrity.ghi_artifact` |
| `TELEMETRY_OWNER` | mỗi runner tự đoán tên trường | `acceptance_integrity.chuan_hoa_telemetry` (đọc `app.ai.telemetry`, **không sửa** nó) |
| `RESULT_EXTRACTION_OWNER` | `envelope["scene3d"]` | `acceptance_verdict.trich_ket_qua` → `outcome.final_memory` |
| `FAILURE_CLASSIFICATION_OWNER` | `_phan_lop_loi` khớp chuỗi | `acceptance_verdict.phan_loai` đọc `stage_reached` + `error_code` |

`ARTIFACT_SCHEMA_VERSION = "1.0"`, **tách khỏi `CACHE_VERSION`** (§20): cache là
chính sách sản phẩm, đây là hình dạng file bộ đo; trộn hai thứ là buộc bump cache
mỗi lần thêm một trường báo cáo.

## 3. Tám sự cố, tiêm lại từng cái (§24)

`tests/test_acceptance_runner_integrity.py` — 36 ca, **0 lượt gọi model**.

| | tiêm lại | cổng phản ứng |
|---|---|---|
| A | telemetry tên Gemini (`prompt_tokens`/`candidates_tokens`) | in đúng 1200/340/900, **không** ra 0 |
| A2 | provider đổi lược đồ (`promptTokenCount`) | `IntegrityError: trường KHÔNG BIẾT` — kêu to, không im lặng |
| A3 | thiếu `total_tokens` | ghi `None` + `truong_thieu`; `MISSING_TELEMETRY != 0_TOKENS` |
| A4 | thiếu `calls` | ĐỎ — số lượt gọi phải ĐẾM được, không suy từ số stage |
| B | artifact thiếu `RequestContract` | `_du_de_replay` = False |
| C | `final_memory` có `R=6, V=288π`, `scene3d` **rỗng** | trích đúng `{R: "6", V: "288π"}` từ `final_memory` |
| C2 | quét mã: thân `trich_ket_qua` chạm `scene3d`/`envelope`/`objects` | ĐỎ |
| D | ghi đè artifact đã có | ĐỎ **trước khi** truncate; nội dung cũ còn nguyên |
| D2 | `os.replace` ném giữa chừng | file cũ nguyên vẹn, **không** JSON cụt, không sót file tạm |
| E | ca âm nhắm *"thiết diện cong xiên"* nhưng chết ở R0 | `fail_closed = YES` · `TARGET_BOUNDARY_DEMONSTRATED = NO` · lớp `UNRELATED_FAIL_CLOSED` |
| E3 | ca âm **không khai** ranh giới | ĐỎ — không khai thì mọi lượt chết đều trông như thành công |
| F | `ball_1` §18: đúng đáp số, checker không nhận chủ thể | `SYSTEM_VERIFICATION_FAILURE` |
| F3 | `postcondition_violated` **vì giá trị lệch** | `MODEL_COMPOSITION_FAILURE` — vá quá tay sẽ mất chiều này |
| G | đổi vân tay prompt giữa lượt | `ABORT` |
| G2 | sửa định nghĩa ca giữa lượt | `ABORT` |
| H | artifact cụt · phiên bản lạ · không khai phiên bản | reader NÉM cả ba, không bao giờ lặng lẽ bỏ qua |
| §7 | đọc một file rồi đem ghi lại chính nó | ĐỎ — đúng hình dạng sự cố ④ |

### Chỗ tinh nhất: `POSTCONDITION_VIOLATED` mang HAI nghĩa

Nó nổ khi bộ kiểm **không với tới** chủ thể (lỗi HỆ — `ball_1`), **và** khi
chương trình **khai sai số** (lỗi MÔ HÌNH). Vá theo hướng "mọi postcondition là
lỗi hệ" thì bộ đo mất hẳn khả năng bắt một chương trình khai sai đáp số.

Ranh giới đọc từ chính lời checker: `_LECH` (*"giá trị không khớp"*) nghĩa là nó
**đã tính lại được** đại lượng từ hình rồi thấy lệch ⇒ mô hình sai. Từ chối chủ
thể, hay không tính nổi ⇒ bộ kiểm hụt. Đây đúng tiêu chí
`test_measure_checker_subject_drift` dùng — một tiêu chí, hai người đọc.

## 4. Chứng nhận lắp ráp (§25)

`scripts/certify_acceptance_runner.py` — **0 lượt gọi model**.

Test từng nguyên hàm không bắt được bảy sự cố kia, vì chúng không nằm trong một
nguyên hàm nào: runner gọi đúng hàm ghi nhưng đọc sai trường; ghi đúng artifact
nhưng tổng kết từ bộ nhớ; phân loại đúng ca dương nhưng ca âm không ai chấm. Nên
chứng nhận chạy **trọn vòng đời**.

**Giả đúng một thứ: provider.** `verify_and_compile`, cổng phủ, checker,
`final_memory` đều thật — nếu chỉ dựng `FakeOutcome` thì bài kiểm chứng minh bộ
phân loại khớp với *giả định của tôi* về route, chứ không khớp với route.

| ca | kịch bản | lớp |
|---|---|---|
| `duong_1_dung` | mặt cầu `R=6` | `CORRECT_SERVABLE_RESULT`, đại lượng `{R: 6, V: 288π}` |
| `duong_2_schema_hong` | lược đồ hỏng | `MODEL_SCHEMA_FAILURE`, repair-eligible |
| `duong_3_bia_diem` | tâm bịa, không nguồn | `MODEL_GROUNDING_FAILURE` — R0 chạy đúng |
| `duong_4_he_hut_verification` | `angle` trên `vector3` | `SYSTEM_VERIFICATION_FAILURE` |
| `am_1_ngoai_pham_vi` | nghĩa vụ `volume` gắn vào `point3` | `HONEST_UNSUPPORTED_REFUSAL`, chạm đúng `requested_operation_uncovered` |

⚠️ **Hai ca cuối là lỗ ĐANG CÓ THẬT**, không phải tình huống bịa. `duong_4` dùng
đúng mục duy nhất trong `KHONG_KIEM_DUOC` (`angle`/`vector3`, khai ở
`VERIFICATION_CAPABILITY_IDENTITY`): chạy được, `executable=True`, và
`check_angle` trả *"không đo được góc: MEASURE_UNDEFINED"* — không phải `_LECH`,
nên phân loại đúng thành lỗi HỆ.

**Chứng nhận phải đỏ được**, ba phép tiêm:

| tiêm | kết quả |
|---|---|
| bộ phân loại gộp mọi thứ thành một lớp (đúng nết `dap_so_khop: bool` của runner cũ) | FAIL, ≥3 ca sai |
| trích kết quả từ `scene3d` — **sự cố ③ tiêm lại vào đường ráp** | FAIL ở `duong_1` (cảnh CÓ tồn tại, nhưng chở nhãn hiển thị chứ không chở `{R, V}`) |
| chạy lại lên thư mục cũ | `IntegrityError` — không resume ngầm, không đè |

## 5. Chính sách, khai thẳng

**`DIRTY_WORKTREE_POLICY` (§18)** — không đòi `git clean` toàn kho. Chỉ chặn khi
thay đổi chưa commit chạm `backend/app`, `backend/scripts`,
`frontend/src/simulations/domains/semantic`; đường không liên quan được **ghi vào
manifest** rồi cho chạy tiếp. Bắt user commit việc dở dang để một cổng xanh là
bắt sai người trả giá.

**`RESUME_POLICY` (§19)** — **KHÔNG resume.** `mo_run` từ chối thư mục đã tồn
tại. `run_id` mới thì rẻ; một artifact trộn hai lượt thì không cứu được.

**`REPAIR_POLICY_SOURCE` (§16)** — `sua_duoc()` đọc `stage_reached` +
`error_code`, chỉ nhận hai stage mà `pipeline._sinh_chuong_trinh` thật sự gửi
lỗi ngược (`ir_static`, `grounding`) cộng lỗi lược đồ. Lý do **không** repair
được cũng phải ghi lại, không chỉ kết luận.

**`APPLICATION_CALL_COUNT_OWNER` (§10)** — đếm từ bản ghi `calls` của từng stage,
cộng lại trong `tom_tat_tu_artifact`. Không suy từ số stage pipeline *dự kiến*
chạy.

## 6. Số dẫn xuất và tự kiểm (§22–§23)

`tom_tat_tu_artifact()` đọc **từ đĩa** và tính lại mọi con số; `tu_kiem_tom_tat()`
đọc lại lần nữa rồi so với `summary.json` đã ghi. Bắt được bốn thứ mắt không bắt
nổi: ghi trượt đường dẫn · đối tượng còn sót trong bộ nhớ · file ghi dở ·
telemetry lệch. Test tiêm một con số "nhập tay" (`APPLICATION_LLM_CALLS = 999`)
và một ca bị mất artifact — cả hai đều ĐỎ.

## 7. Danh tính — không nhiễm phạm vi (§28–§29)

| | trước | sau |
|---|---|---|
| `stable_capability_hash` | `5b61b9ea76d0c764…` | **không đổi** |
| `semantic_environment_hash` | `36be94cf2258e116…` | **không đổi** |
| bốn vân tay mô hình | — | **không đổi** |
| `CACHE_VERSION` | `71` | `71` |
| candidate (mã sản phẩm) | `4897280e9fc3a9fd` 89 file | **không đổi**, `--verify` PASS |

`NEW_IR_OPERATIONS = 0` · `NEW_KERNEL_FUNCTIONS = 0` · `NEW_CHECKERS = 0` ·
`PROMPT_CHANGED = NO` · `MODEL_SCHEMAS_CHANGED = NO` ·
`GEOMETRY_RUNTIME_CHANGED = NO`.

## 8. Hồi quy — 0 API call

| cổng | kết quả |
|---|---|
| pytest | **3163 pass**, 1 skip, 1 deselect |
| vitest | **687 pass / 50 file** |
| `tsc -b && vite build` | PASS |
| `certify_acceptance_runner.py` | **RUNNER_CERTIFICATION PASS** |
| `freeze_evaluation_candidate.py --verify` | PASS (không đổi) |
| `lock_cache_identity.py --verify` | PASS (không đổi) |

## 9. Giới hạn — khai thẳng

- **Runner lịch sử chưa chuyển sang tầng này.** `run_curved_acceptance.py` vẫn
  đọc `scene3d` và vẫn khớp chuỗi để phân loại. Cố ý (§2, §21): viết lại chúng
  là đụng vào thứ đã sinh ra bằng chứng lịch sử. **Hệ quả phải nhớ: lượt đo kế
  tiếp phải dùng runner ĐI QUA tầng này, nếu không cả wave này vô hiệu.**
- **Telemetry trong chứng nhận là giả** (đúng hình dạng `usage_report()`).
  Đường thật chỉ được chứng minh khi có một lượt sống chạy qua nó.
- **`kiem_bat_bien_token` chỉ khẳng định thứ lược đồ Gemini bảo đảm**
  (`total >= input`, `total >= thought`, `total >= input+output`). Bịa thêm bất
  biến sẽ đỏ ở lượt thật rồi bị tắt, và khi ấy mất cả cái đúng lẫn cái sai.

## 10. Việc kế tiếp

```
NEXT_ACTION = RERUN_CURVED_ERGONOMICS_DEVELOPMENT_PROBE (run_id MỚI)
V3          = VẪN CHƯA CHẠY · pool giữ niêm phong · seed chưa rút
```

Lượt probe kế tiếp phải mang `run_id` mới và danh tính môi trường **hiện tại**
(§27) — không nối vào artifact §18, không sửa số của nó.
