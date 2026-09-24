# SYNTHESIS_REJECTION_POINTER_TRACE_GAP

> Nhánh `feat/photo-problem-to-scene` · 2026-09-15.
> START_HEAD `3bf7fa4` · `main` giữ `085cae6`.
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/synthesis-rejection-pointer-trace-gap/`.
> **0 request Gemini · 0 request mạng.**

```text
SYNTHESIS_REJECTION_POINTER_TRACE_GAP = PASS   (offline)
TRACE_VERSION                         = synthesis-repair-trace/1 → /2
PYDANTIC_LOC_PRESERVED                = YES    (dò trên JSON thô: EXACT | AMBIGUOUS)
PRODUCT_BEHAVIOR_CHANGED              = NO
HISTORICAL_C02_REJECTION_POINTER      = NOT_RECOVERABLE
```

## 1. Kết luận

Pilot C02 `20260915T061735Z-7b979fce` bị loại ở `PROGRAM_SCHEMA / SCHEMA_VALUE_ERROR`, nhưng trace không ghi được **chỗ** lỗi. Đầu ra thô cố ý không lưu, nên lỗi quá khứ **không khôi phục được**. Wave này không đoán và không dựng lại nó.

**Từ nay, mọi lượt synthesis bị Pydantic từ chối đều để lại chẩn đoán rút gọn:**
- con trỏ JSON RFC 6901 trên đầu ra **thô**, kèm trạng thái con trỏ;
- loại lỗi Pydantic;
- `rule_id` khi có mã ổn định;
- kiểu JSON nhận được;
- số lỗi.

Chẩn đoán không mang giá trị trường, thông điệp Pydantic, `ctx` hay `input`.

**Không đổi:** mã sản phẩm, prompt, lược đồ, model, lời phản hồi sửa, số lượt gọi.

## 2. Tiền kiểm — `PRECHECK.json` = PASS

| mục | giá trị |
|---|---|
| HEAD cây nguồn · `main` | `3bf7fa4` · `085cae6` |
| cây nguồn đầu wave | chỉ ` D frontend/public/favicon.svg` (của user) |
| worktree `D:\tmp\algo-sim-c03-live-worktree` | `828180e` sạch ⇒ `checkout --detach 3bf7fa4` (commit chỉ thêm docs) ⇒ sạch |
| candidate · khoá cache | `37500cd92f134e44…` khớp · khớp, `CACHE_VERSION` 95 |
| artifact pilot | `1ab11a88…` · `2dd3c9d5…` · `PROGRAM_SCHEMA` · `SCHEMA_VALUE_ERROR` · `rejection_pointers = []` |

⚠️ **Lỗi bộ đo.** Bản PRECHECK đầu báo `CANDIDATE_VERIFY` sai, vì công cụ đặt `PATH` rỗng cho tiến trình con. Chạy `--verify` trực tiếp thì khớp. Bản lỗi giữ ở `work/`.

## 3. Audit — `REJECTION_TRACE_GAP_AUDIT.json`

| bước | cấu trúc lỗi |
|---|---|
| `SemanticProgramSpec.model_validate` | có: `pydantic_core.ValidationError.errors()` |
| `validator.validate_semantic_program` | **bị làm phẳng** thành `f"Lỗi cú pháp schema …: {e}"` — chỗ cuối trong mã sản phẩm còn cấu trúc |
| `pipeline.stage_semantic_program` | chỉ chuỗi: sự kiện observer và `_prompt_sua` |
| `QuanTracVongSua` | thông điệp chuỗi + ứng viên thô trong bộ nhớ |
| runner `phan_loai_ung_vien` | chạy lại validation ⇒ **có lại cấu trúc**, nhưng v1 chỉ giữ `SCHEMA_<type>` |
| trace v1 | `rejection_summary_redacted` = thông điệp đã che bí mật |

**Hai sự thật đo được quyết định thiết kế.**

1. **`loc` trỏ vào dữ liệu SAU `model_validator(mode="before")`.**
   - `_nang_declare_point` gỡ `declare_point` khỏi `statements`, nên `statements[5]` thô hiện ra là `loc ('statements', 0, …)`.
   - Khi `memory_declarations` không phải mảng, Pydantic sinh `loc` không tồn tại trên JSON thô.
   - Đổi thẳng `loc` thành con trỏ là **bịa con trỏ**.
2. **`str(ValidationError)` chở `input_value`** (8/8 lỗi dò được). Tóm tắt tự do của trace v1 vì thế chở giá trị mô hình với mọi lỗi Pydantic — kể cả sau khi đã che bí mật.

**Nơi sửa:** `backend/scripts/run_photo_problem_live.py` — bộ đo, nằm ngoài `MEASURED_SYSTEM_PATHS`. Trace được dựng **sau** khi `run_pipeline` trả về, nên thêm trường không đổi hành vi.

## 4. Hợp đồng chẩn đoán

```json
{"phase": "PROGRAM_SCHEMA", "code": "SCHEMA_…", "error_count": 1,
 "details": [{"json_pointer": "/statements/5/vertices", "pointer_status": "EXACT",
              "pydantic_error_type": "list_type", "rule_id": null, "received_json_type": "integer"}]}
```

- **`phase`/`code`** giữ đúng như trước. `diagnostics` chỉ có ở `PROGRAM_SCHEMA`; mọi pha khác và lỗi provider là `null`.
- **Con trỏ** (`_duong_ung_vien`) — dò trên JSON thô:
  - chỉ số không tin theo giá trị: mọi phần tử đều là ứng viên;
  - token thẻ union chỉ được bỏ qua khi `kind` thô bằng đúng nó;
  - lá phải bằng `input` của lỗi (`missing`: nút cha bằng `input` và thiếu đúng khoá). `input` chỉ dùng trong bộ nhớ.
  - Đúng **một** đường ⇒ `EXACT`. 0 hoặc ≥2 đường ⇒ `AMBIGUOUS`, `json_pointer = null`. `loc` rỗng ⇒ `""`.
- **Escape** `con_tro_json` dùng chung `validator._thoat_con_tro`: `~` → `~0` trước, `/` → `~1` sau.
- **`rule_id`:**
  - `value_error` ⇒ `co_qualname` của hàm trong `semantic_program/` đã ném, đọc từ **traceback**, không từ thông điệp (vd `SemanticProgramSpec._nang_declare_point`);
  - `SCHEMA_SILENTLY_DROPPED_KEY` ⇒ chính mã ấy, giữ con trỏ của validator;
  - lỗi Pydantic dựng sẵn ⇒ `null`.
- **Thứ tự** theo `khoa_sap_xep_chan_doan`, không theo thứ tự Pydantic.

## 5. Phiên bản trace — `TRACE_VERSION_DECISION.json`

**`/1` → `/2`, có bump.** v1 hứa `rejection_summary_redacted` khác rỗng cho mọi lượt bị loại (`test_synthesis_repair_trace::test_B`), mà với lỗi Pydantic tóm tắt ấy chở `input_value`. Muốn không ghi giá trị thì phải đổi **nghĩa** một trường đã hứa — đó không phải thêm trường tuỳ chọn.

**Trace v2:**
- thêm `rejection_diagnostics` và `rejection_summary_status` (`PRESENT` · `WITHHELD_PYDANTIC_MESSAGE`);
- tóm tắt `null` khi `PROGRAM_SCHEMA` và mã ≠ `SCHEMA_SILENTLY_DROPPED_KEY`;
- mọi trường hợp khác giữ như v1.

**Tương thích:**
- `doc_trace_vong_sua` đọc v1/v2 → khung v2 (`source_trace_version`, `rejection_diagnostics_status`), không sửa đầu vào, phiên bản lạ ⇒ `ValueError`.
- Fixture v1 là trace **thật** của run `20260914T141706Z-9a469909`; JSON chính tắc trùng bản gốc.
- Tóm tắt v1 không bị làm sạch hồi tố. Artifact lịch sử không bị sửa.

## 6. Thay đổi — commit 1 `e67bb20`

- **`run_photo_problem_live.py`:**
  - `phan_loai_ung_vien` trả thêm `diagnostics`;
  - thêm `con_tro_json`, `chan_doan_tu_loi`, `khoa_sap_xep_chan_doan`, `_duong_ung_vien`, `_ham_da_nem`, `_chan_doan_khoa_bi_bo`;
  - `dung_trace_vong_sua` ghi v2; thêm `doc_trace_vong_sua`.
- **Test mới** `tests/test_synthesis_rejection_diagnostics.py` (A–Q, 19 test) + fixture `tests/fixtures/synthesis_repair_trace_v1_c02_redacted.json`.
- **Test cập nhật** `test_synthesis_repair_trace.py`: A ghim `/2`; B đòi tóm tắt `PROGRAM_SCHEMA` bị giữ lại kèm chẩn đoán.
- **`CODE_INDEX.md`.**

**Đỏ trước khi sửa** (runner = `3bf7fa4`): 15/19 đỏ. 4 xanh là L · M · N · P — cổng parity tắt/bật trace, phải xanh từ trước.

## 7. Con trỏ và loại lỗi — `POINTER_ERROR_TYPE_PROOF.json` = PASS

Biến thể nhỏ của chương trình p1 đóng băng, đi qua validator và Pydantic thật:

| fixture | pha / mã | con trỏ · trạng thái | loại lỗi · `rule_id` · kiểu |
|---|---|---|---|
| `initial_value` sai kiểu (khối) | qua vòng sửa | — | — (Pydantic nhận `Any`) |
| `type` không hợp lệ | `SCHEMA_LITERAL_ERROR` | `/memory_declarations/0/type` · EXACT | literal_error · — · string |
| thiếu `name` | `SCHEMA_MISSING` | `/memory_declarations/1/name` · EXACT | missing · — · absent |
| `kind` câu lệnh sai | `SCHEMA_UNION_TAG_INVALID` | `/statements/5` · EXACT | union_tag_invalid · — · object |
| trường lồng sai kiểu | `SCHEMA_LIST_TYPE` | `/statements/5/vertices` · EXACT | list_type · — · integer |
| literal lồng sâu | `SCHEMA_LITERAL_ERROR` | `/statements/9/expr/quantity` · EXACT | literal_error · — · string |
| bốn lỗi cùng lúc | `SCHEMA_LITERAL_ERROR` | đủ 4, EXACT, thứ tự xác định | — |
| lỗi gốc (toạ độ mâu thuẫn) | `SCHEMA_VALUE_ERROR` | `""` · EXACT | value_error · `SemanticProgramSpec._nang_declare_point` · object |
| `memory_declarations` không phải mảng | `SCHEMA_MODEL_TYPE` | 15 × `null` · AMBIGUOUS | model_type · — · string |
| `at` trong khai báo | `SCHEMA_SILENTLY_DROPPED_KEY` | `/memory_declarations/0/at` · EXACT | — · `SCHEMA_SILENTLY_DROPPED_KEY` · array |
| khoá trang trí `label` | qua vòng sửa | — | — |

Ở cả 11 fixture:
- mọi con trỏ `EXACT` đều giải được trên JSON thô;
- giá trị mốc không xuất hiện trong chẩn đoán;
- dựng hai lần trùng từng byte.

## 8. Che dữ liệu — `REDACTION_PROOF.json` = PASS

`R.main` thật với ba lượt bị loại ở `PROGRAM_SCHEMA`:
- bí mật giả nằm trong **giá trị** trường;
- bí mật giả nằm trong **thông điệp** `ValueError`;
- nhiều lỗi mang giá trị mốc.

**Cửa sổ chứng:** bí mật thật sự nằm trong lời Pydantic.

**Kết quả,** chạy hai lần — có che và **tắt** che:
- 0 lần xuất hiện mốc, bí mật giả, `Input should`, `Value error`, `input_value`, mảnh thông điệp, `Đề bài:`;
- không có khoá `input`/`msg`/`ctx`/`url`;
- tóm tắt `null`.

⇒ `RAW_INPUT_STORED = NO` · `RAW_MESSAGE_STORED = NO`.

Lượt redaction đầu không ghi được artifact; nguyên nhân **không xác định**, vì đuôi output bị nhiễu destructor asyncio che. Lượt chạy lại ghi đầy đủ. Bản đầu dùng chính chuỗi mốc làm khoá JSON nên đã được sinh lại với nhãn mô tả.

## 9. Giữ nguyên hành vi — `BEHAVIOR_PARITY.json`

**Phương pháp:** cùng công cụ, cùng kịch bản, chạy trên cây nguồn **trước** (runner = `3bf7fa4`) và **sau** bản sửa.
- C01/C02 × {nhận ngay, từ chối Pydantic rồi nhận, hết lượt} × {tắt, bật trace}.
- Replay đóng băng p1/p6.

**Trùng hoàn toàn:**
- băm thân **mọi** request, kể cả lượt sửa ⇒ phản hồi sửa trùng từng byte;
- envelope, `scene3d` (`829f70b2…` · `db1e31ec…`), `final_memory` (`c934b023…` · `79cf15e9…`), đáp số đọc từ cảnh;
- bộ đếm HTTP, thử lại, lượt logic;
- byte phản hồi sửa của fixture dẫn xuất C02.

**Tắt/bật trace:** cùng request, cùng envelope. Trace không tự kích hoạt sửa.

**Không đổi:** khoá danh tính cache (prompts · lược đồ synthesis/analyze · thẻ văn phạm · capability) trùng `3bf7fa4`; model `gemini-2.5-flash`; `backend/app` 0 thay đổi.

## 10. Tiêm lỗi — `FAULT_INJECTIONS.json`

| # | phép tiêm vào runner | đỏ (trên 33) |
|---|---|---|
| F1 | bỏ `loc` trước khi dựng chẩn đoán | 7 — A×2 · B×2 · E · F · Q |
| F2 | ghi `msg`/`input` vào chi tiết | 7 — J · K · A×2 · B×2 · D |
| F3 | escape con trỏ sai thứ tự | 1 — C |
| F4 | bỏ sắp xếp, đảo thứ tự Pydantic | 1 — F |
| F5 | gắn chẩn đoán Pydantic giả cho lỗi provider | 1 — I |
| F6 | bật trace làm đổi phản hồi sửa | 8 — G · M · N + F · F2 · E · B2 · B[_grounding] (test cũ) |

Sau mỗi phép tiêm: gỡ bằng Edit, runner trùng byte snapshot, 0 dấu `TIÊM`.

⚠️ `test_L` **không** bắt được F6. Bản vá sống ở cấp module, nên sau lần khởi tạo đầu, cả lượt tắt lẫn bật trong cùng tiến trình đều nhận phản hồi đã đổi. M và N bắt được đúng lớp lỗi ấy.

## 11. Danh tính và cache

- **Candidate** `37500cd92f134e44…` → `37500cd92f134e44…`: `backend/scripts` và `backend/tests` nằm ngoài `MEASURED_SYSTEM_PATHS`; `--verify` khớp ở cây nguồn và worktree.
- **`CACHE_VERSION` 95 → 95.** Bề mặt mô hình và envelope phục vụ không đổi; khoá danh tính cache trùng từng thành phần.

## 12. Cổng offline — `OFFLINE_GATES.json`

`NEW_GEMINI_REQUESTS = NETWORK_REQUESTS = 0`.

**Có mục tiêu:**
- sau bản sửa: 50 xanh;
- sau khi gỡ mọi phép tiêm: **150 xanh** — chẩn đoán, trace vòng sửa, hợp đồng khai báo, runner (ngân sách HTTP, thử lại, khử bí mật), checkpoint vision.

**Toàn bộ backend, cây nguồn trước commit: 5189 xanh, 1 đỏ.** Test đỏ là holdout, vì cây bẩn; nó xanh trên worktree sạch.

**Toàn bộ backend, worktree tại `e67bb20`: 5188 xanh, 2 đỏ.** Hai test đỏ là băm byte thô artifact lịch sử CRLF của worktree (`test_H6_…`, `test_01_…[manifest.json]`); cùng test trên cây nguồn **xanh**.
- Backlog `CROSS_PLATFORM_ARTIFACT_HASH_TESTS`, không sửa trong wave này.
- Worktree sạch sau lượt chạy.

**Không chạy:** Gemini, vision, analyze thật, trình duyệt live, camera, P1–P7, frontend (không đổi).

## 13. Cây nguồn và commit

Mỗi commit stage bằng đường dẫn tường minh, in `git diff --cached --name-status`, dừng nếu có `frontend/public/favicon.svg`.

| commit | nội dung |
|---|---|
| `e67bb20` | runner (chẩn đoán + trace v2 + reader) · test mới + fixture v1 · test trace cập nhật · `CODE_INDEX` |
| commit 2 | báo cáo + 9 artifact JSON (chỉ băm, con trỏ, loại lỗi, số đếm; không JUnit, không prompt, không output thô, không chương trình) |

- Không merge, không push.
- `USER_FAVICON_DELETION_PRESERVED = YES`.

**Không tự ghi:**
- nguyên nhân cụ thể của lỗi C02 cũ đã xác định;
- `C02 pilot = PASS`;
- `TOKEN_OPTIMIZATION = PASS`;
- `FIRST_ATTEMPT_RATE_IMPROVED`;
- `MERGE_ALLOWED = YES`.

`NEXT_ACTION = C02_SYNTHESIS_FIRST_ATTEMPT_LIVE_REVALIDATION`
