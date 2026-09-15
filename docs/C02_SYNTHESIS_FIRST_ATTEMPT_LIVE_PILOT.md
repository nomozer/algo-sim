# C02_SYNTHESIS_FIRST_ATTEMPT_LIVE_PILOT

> Nhánh `feat/photo-problem-to-scene` · 2026-09-15.
> START_HEAD `828180e` · `main` giữ `085cae6`.
> Worktree thực thi `D:\tmp\algo-sim-c03-live-worktree` tại `828180e`, sạch.
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/c02-synthesis-first-attempt-live-pilot/`.
> **1 request Gemini synthesis · 0 vision · 0 analyze · 0 retry.**

```text
C02_FIRST_ATTEMPT_LIVE_PILOT      = OTHER_MODEL_OUTPUT_REJECTION
FIRST_ATTEMPT_ACCEPTED            = NO   (PROGRAM_SCHEMA / SCHEMA_VALUE_ERROR)
MEMORY_DECLARATION_AT_PRESENT     = NO
SCHEMA_SILENTLY_DROPPED_KEY       = NO
TOKEN_OPTIMIZATION                = NOT_ESTABLISHED
```

## 1. Kết luận

Đây là pilot **một mẫu**, không phải bằng chứng thống kê.

**Lượt đầu synthesis của C02 bị loại**, nên không có cảnh, `final_memory` hay đáp số để kiểm.
- Pha / mã: `PROGRAM_SCHEMA` / `SCHEMA_VALUE_ERROR`. Đây là một lỗi giá trị của Pydantic, **không phải** lỗi mục tiêu của wave alignment trước.
- Phân loại chạy lại khớp lời nhắn pipeline phát ra.

**Riêng lỗi mục tiêu thì không tái diễn trong lượt này:**
- 10 khai báo, không mục nào có `at`;
- không khoá ngoài hợp đồng (3 tập khoá khác nhau, đều là tập con của 8 khoá hợp lệ);
- không khoá mang dữ liệu bị bác.

**Theo luật wave:**
- vòng sửa không được gửi — lượt sửa bị chặn **trước transport**;
- không vá gì;
- phân loại dừng ở đây.

## 2. Tiền kiểm — `PRECHECK.json` = PASS (0 request)

| mục | giá trị |
|---|---|
| HEAD cây nguồn · worktree · `main` | `828180e` · `828180e` · `085cae6` |
| cây nguồn / worktree | chỉ ` D frontend/public/favicon.svg` (của user) / sạch |
| candidate `--verify` | `37500cd92f134e44…` khớp |
| khoá danh tính cache | khớp · `CACHE_VERSION` 95 |
| khoá Gemini | có trong `backend/.env` của cây nguồn; không in, không chép vào worktree |
| `ALLOW_LIVE_AI` | vắng ở tiến trình cha, chỉ đặt trong tiến trình chạy |
| model | `gemini-2.5-flash`; không có biến ghi đè `GEMINI_MODEL` |
| thử lại | `ApiBudget(max_attempts=1)` ⇒ 0 retry |
| cổng offline | 203 passed |

**Cổng offline đã chạy:**
- hợp đồng memory_declarations (A–M), khởi tạo điểm, thẻ văn phạm, đồng bộ lược đồ;
- trace vòng sửa synthesis;
- runner ảnh (khử bí mật, ngân sách HTTP) và checkpoint vision;
- danh tính cache;
- candidate.

⚠️ **Timeout.** Brief ghi 60 giây, nhưng đường synthesis của sản phẩm không truyền `timeout_seconds`, nên `call_gemini` dùng trần **120 s** mặc định. 60 s là trần của đường đọc ảnh. Wave giữ nguyên giá trị sản phẩm và không đổi cấu hình. Request thật trả sau 9 672 ms.

## 3. Đầu vào đóng băng — checkpoint đã chứng minh

**Nguồn.** `D:\tmp\algo-sim-c02-controlled-capture\evidence\C02_SINGLE_RUN_CAPTURE.json`:
- SHA-256 `7c955655…6444`, 9 541 byte;
- run `20260914T141706Z-9a469909`, commit `d8ad614`, runner thoát 0.

Tệp được ghi bởi launcher của wave đo C02: nó bọc `pipeline.stage_semantic_analyze` **trong cùng tiến trình** của run và lưu `model_dump(mode="json")` của contract trả về.

**RequestContract** (canonical SHA-256 `767d5c94…6800`):
- dump → `model_validate` → dump trùng tuyệt đối;
- nghĩa vụ `volume(S.ABC)`, witness `V_SABC`;
- đủ năm dữ kiện then chốt:
  - AB = 3;
  - AC = 4;
  - SA = 5;
  - ABC vuông tại A;
  - SA ⟂ (ABC).

**Chứng minh bằng thân request** (0 mạng, MockTransport):
- Dựng lại request synthesis lượt đầu từ checkpoint, **bằng mã tại `d8ad614`**. SHA-256 thân = `0d46b6d2…da5`, **trùng đúng** `body_sha256` mà cổng HTTP của run đã ghi cho request synthesis #3.
- Nghĩa là mô hình lúc ấy nhận đúng contract này.
- Dựng bằng mã tại `828180e`, văn bản chỉ khác đúng mệnh đề thẻ `— mỗi mục có ĐÚNG các khoá này`. System prompt và `generationConfig` trùng: temperature 0.1, JSON mode, không `responseSchema`, không `thinkingConfig`.
- Thân request thật của pilot (`77c580df…`) **trùng** thân đích dựng offline.

**Lỗi bộ đo đã gặp.** Bản đầu so dữ kiện trên giá trị đã ép kiểu miền số (`values == [3]`) và báo sai ba dữ kiện. Đã sửa sang JSON đã chụp. Bản lỗi giữ ở `work/measurement_bug_fact_value_type/`.

## 4. Chạy thử bộ đo trước khi tiêu request (0 request)

Đường chạy giống hệt lượt thật, với transport giả và mạng thật bị chặn:

| biến thể | kỳ vọng | kết quả |
|---|---|---|
| chương trình C02 đã được nhận | PASS | PASS — topology, final_memory, đáp số đều PASS |
| `initial_value` → `at` tại `/memory_declarations/0` | ALIGNMENT_REJECTION | `SCHEMA_SILENTLY_DROPPED_KEY`, con trỏ `/memory_declarations/0/at`, lượt sửa bị chặn trước transport |
| thêm `label` trang trí | không PASS | `ignored_keys` = 1 ⇒ FAIL_QUALITY_CHECK |

## 5. Lượt thật — `C02_SYNTHESIS_FIRST_ATTEMPT_RESULT_REDACTED.json`

**Đường chạy:**
- `pipeline.run_pipeline(..., semantic_route="serve")` của sản phẩm; chỉ `stage_semantic_analyze` được thay bằng checkpoint.
- Cổng `CongHttp` của runner đặt trần tổng 1 và trần theo tầng: vision 0, analyze 0, synthesis 1.

| mục | giá trị |
|---|---|
| run | `20260915T061735Z-7b979fce` |
| request gửi / bị chặn | 1 / 1 — lượt logic 2 = lượt sửa, `STAGE_BUDGET_EXHAUSTED`, 0 byte gửi |
| HTTP · độ trễ | 200 · 9 671,8 ms |
| token | vào 3 854 · ra 1 058 · suy nghĩ 1 060 · tổng 5 972 |
| ứng viên | 3 026 byte · SHA-256 `1ab11a88…` · canonical `2dd3c9d5…` |
| parse JSON | được |
| pha / mã | `PROGRAM_SCHEMA` / `SCHEMA_VALUE_ERROR` (một lỗi) |
| con trỏ JSON | **NOT_RECORDED** — xem dưới |
| `ignored_keys` | không áp dụng: validator từ chối nên không có danh sách; 0 sự kiện |
| cảnh · topology · final_memory · đáp số | NOT_RUN (lượt đầu bị loại) |

⚠️ **Khoảng trống trace.** Bộ đo của pilot chỉ trích con trỏ cho `SCHEMA_SILENTLY_DROPPED_KEY`. Nó không ghi `loc` của lỗi Pydantic, và đầu ra thô cố ý không được lưu. Vì vậy vị trí của `SCHEMA_VALUE_ERROR` **không khôi phục được**, và wave **không gửi thêm request** để tìm lại.

## 6. Hợp đồng khai báo — `CONTRACT_VALIDATION.json`

| mục | giá trị |
|---|---|
| số khai báo | 10 |
| tập khoá | `{initial_value, model_assumption, name, type}` ×1 · `{initial_value, name, type}` ×3 · `{name, type}` ×6 |
| khoá ngoài 8 khoá hợp lệ | 0 |
| `at` trong khai báo | không |
| khoá lạ mang dữ liệu | 0 |

## 7. Token — `TOKEN_COMPARISON.json`

Mốc lịch sử (một run, không phải đối chứng): 2 lượt · 5 434 bị loại + 4 586 được nhận = **10 020**.

| | lượt này |
|---|---|
| tổng token synthesis | 5 972 |
| hiệu số thô với 10 020 | −4 048 (−40,4 %) |
| token lượt bị loại | 5 972 (tỉ trọng 1,0; lịch sử 0,5423) |
| token bị loại tránh được | 0 |
| lượt đầu bị loại: mới so với lịch sử | 5 972 so với 5 434 (+538) |

**Đính chính trong artifact.** Bộ đo ghi `TOKEN_SAVING_ON_THIS_C02_RUN = 4048` mà không xét kết cục. 10 020 token lịch sử mua được một chương trình được nhận; 5 972 token lượt này chỉ mua một lượt bị loại ⇒ `TOKEN_SAVING_ON_THIS_C02_RUN = NOT_COMPARABLE`. Số gốc của bộ đo giữ nguyên trong mục `CORRECTION`.

## 8. Cây nguồn và commit

- Không sửa mã sản phẩm, prompt, lược đồ hay validator. Candidate và `CACHE_VERSION` giữ nguyên.
- **Quét bí mật — `SECRET_SCAN.json` = 0.** Lượt quét đầu báo 3, cả ba nằm trong chính mã nguồn bộ quét (`pilot_live.py`, dòng khai ba mẫu đầu mục/query). Lượt ấy có 0 lần xuất hiện khoá thật và 0 chuỗi khớp mẫu khoá Google. Bản đầu giữ ở `work/SECRET_SCAN_first_run_scanner_source_self_match.json`. Lượt quét cuối chạy trên phạm vi commit (kể cả báo cáo này), bằng chứng và thư mục làm việc, không gồm mã bộ quét: 0. Các lượt trung gian giữ ở `work/`.
- Một commit gồm báo cáo và 5 artifact đã rút gọn: không prompt, không output thô, không chương trình, không checkpoint.
- Stage bằng đường dẫn tường minh; staged diff không có `frontend/public/favicon.svg`.
- Không merge, không push.
- Worktree thực thi sạch.
- Thay đổi favicon của user còn nguyên.

**Không tự ghi:** `TOKEN_OPTIMIZATION = PASS`, `FIRST_ATTEMPT_RATE_IMPROVED`, `EXPECTED_PRODUCTION_SAVING`, ý nghĩa thống kê, `MERGE_ALLOWED = YES`.

**Việc kế tiếp.** Kết cục OTHER_MODEL_OUTPUT_REJECTION không nằm trong ba nhánh brief đã định. Đề xuất: `SYNTHESIS_REJECTION_POINTER_TRACE_GAP` — offline, ghi con trỏ JSON (`loc` Pydantic) cho mọi mã từ chối, rồi mới quyết định có chạy lại pilot C02 hay không. Quyết định thuộc về user.
