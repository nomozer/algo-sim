# SYNTHESIS_MEMORY_DECLARATION_SCHEMA_PROMPT_ALIGNMENT

> Nhánh `feat/photo-problem-to-scene` · 2026-09-15.
> START_HEAD `e51901d` · `main` giữ `085cae6`.
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/synthesis-memory-declaration-schema-prompt-alignment/`.
> **0 request Gemini · 0 lượt gọi model · 0 request mạng.**

```text
AUDIT_CLASSIFICATION                 = INVALID_AND_UNUSED
AT_ADDED_TO_SCHEMA                   = NO
SILENT_EXTRA_KEY_DROP                = YES → NO
SCHEMA_PROMPT_VALIDATOR_KEYSET       = PASS   (một nguồn: MemoryDeclaration.model_fields)
C01_C02_BEHAVIOR_PARITY              = PASS   (final_memory + scene3d trùng START_HEAD)
C02_REJECTED_FIXTURE                 = DERIVED_FROM_TRACE_POINTER — fixture chính xác NOT_ESTABLISHED
TOKEN_OPTIMIZATION                   = NOT_RUN
```

## 1. Kết luận

Lượt C02 thật (run `20260914T141706Z-9a469909`) có synthesis lượt đầu đặt `at` trong `memory_declarations[0]`. Lượt ấy bị loại ở `PROGRAM_SCHEMA` / `SCHEMA_SILENTLY_DROPPED_KEY`, và lượt sửa được nhận (5434 + 4586 token).

**Cổng đã chặn đúng.** Thứ còn thiếu nằm ở hai chỗ:
- hợp đồng chưa nói rõ mỗi khai báo có đúng những khoá nào;
- lời từ chối chưa đọc được bằng máy: không có mã, không có con trỏ.

Ngoài ra, khoá trang trí (vd `label`) vẫn bị Pydantic **bỏ im lặng**.

**Wave này sửa đúng ba chỗ đó:**
- không thêm `at`;
- không đổi hình học, đáp số hay kết quả của chương trình hợp lệ.

## 2. Tiền kiểm — `PRECHECK.json` = PASS

| mục | giá trị |
|---|---|
| HEAD · `main` | `e51901d` · `085cae6` |
| cây nguồn | chỉ ` D frontend/public/favicon.svg` (của user) |
| worktree `D:\tmp\algo-sim-c03-live-worktree` | sạch, tại `e51901d` |
| candidate | `e946582fdacfecc5…` |
| candidate C02 thật (bị loại / được nhận) | **không được lưu** — runner chỉ ghi băm |

**Quyết định của user:** dùng fixture dẫn xuất có nhãn. Cổng *"fixture C02 bị loại chính xác"* = `NOT_ESTABLISHED`, không bao giờ PASS.

## 3. Audit — `MEMORY_DECLARATION_CONTRACT_AUDIT.json`

**Nơi `at` tồn tại:**
- `at` chỉ là trường của `DeclarePointStmt` (`list[Any]`).
- Hoisting `_nang_declare_point` chuyển `declare_point.at` sang `memory_declarations[].initial_value`.
- Trong `memory_declarations[]`, không model nào khai `at` và **không consumer nào đọc** nó. Ý nghĩa toạ độ khởi tạo đã có ô chính tắc `initial_value` ⇒ `INVALID_AND_UNUSED`.

**Chương trình AI lịch sử** (625 chương trình, 276 tệp có khai báo) mang khoá lạ trong khai báo:

| khoá | số lần |
|---|---|
| `label` | 288 |
| `at` | 101 |
| `description` | 26 |
| khác | 19 |

**Đo chính sách chặt** (plugin pytest, không sửa mã): bác **mọi** khoá lạ làm đỏ **11 test mới**.
- Có 6 test liên quan chính sách: replay đóng băng p4/p5, `test_MOI_chuong_trinh_AI_sinh_deu_serialize_duoc`, `gm10`×2, `A3`.
- Nên **không** dùng `extra="forbid"`. Detector trước Pydantic được giữ:
  - khoá **mang dữ liệu** vẫn bị **bác**;
  - khoá **trang trí** không bác nhưng được **báo**.

## 4. Thay đổi — commit 1 `50cf37b`

### `validator.py`

- **`khoa_la_trong_khai_bao(raw_spec)`** liệt kê từng khoá lạ: con trỏ RFC 6901, tên khoá, cờ `blocking`, chủ sở hữu hợp lệ. Nó không mang giá trị.
- **`_khoa_bi_bo_im_lang`** dựng lời từ chối từ danh sách đó, theo khuôn:
  ```text
  [SCHEMA_SILENTLY_DROPPED_KEY] /memory_declarations/0/at: `at` là trường của `declare_point` …; chuyển giá trị sang `initial_value`. Khoá hợp lệ: name, type, initial_value, element_type, key_type, val_type, source_fact_id, model_assumption
  ```
  - Danh sách khoá hợp lệ đọc thẳng từ `MemoryDeclaration.model_fields`.
  - Lời từ chối không chứa giá trị ứng viên, lược đồ hay stack trace.
- **`ValidationResult.ignored_keys`** mang `{pointer, key}` của khoá trang trí trong chương trình **được nhận**.

### `pipeline.py`

- Có `ignored_keys` ⇒ phát sự kiện observer `semantic_program_ignored_keys`, chỉ gồm con trỏ và tên khoá.
- Sự kiện thụ động (#22): không đổi luồng.

### `grammar_card.py`

- Dòng `memory_declarations[]` thêm `— mỗi mục có ĐÚNG các khoá này`.
- Thẻ hình học **6690 → 6733 byte** (+43; trần test 6750; trần wave +200).

### Test

- **Mới:** `tests/semantic_program/test_memory_declaration_contract_alignment.py` (A–M, 17 test) và `tests/grammar_card_identity.py`.
- **Cập nhật khuôn thông điệp:** `test_point_initialization_contract.py` (R1, C4, C5, D1, AB1, TIEM_2, TIEM_3) và `test_repair_probe_integrity.py::A3`.
- **Ghim `grammar_card`:** CA2 và preflight elip xiên, đổi thành `3fb8eeab…`.
- **Con dấu thesis-final** (`test_thesis_runner_alignment` B1_G1, F12/F13) dựng lại giá trị **trước wave** bằng máy qua `grammar_card_neu_chua_them_menh_de()`, không nới phép so.

### Đỏ trước khi sửa

16 test A–L chạy trên `e51901d`:
- **11 đỏ:** A, B×4, B2, C, D, E, K, L.
- **5 xanh:** F, G, H, I, J — cổng hành vi và thẻ phải xanh từ trước.

Test M (thẻ dựng lại) viết sau. Nó được chứng minh bằng F2/F3 ở §8.

## 5. Tập khoá — `SCHEMA_PROMPT_KEYSET_PARITY.json` = PASS

| bề mặt | tập khoá | cách giữ đồng bộ |
|---|---|---|
| Pydantic `MemoryDeclaration` | 8 khoá | nguồn sự thật |
| lược đồ xuất + mirror frontend | = model | sinh từ Pydantic, `test_schema_sync` |
| thẻ văn phạm | model − {element_type, key_type, val_type} | dựng từ `model_fields`; test E + ghim CA2 |
| `Khoá hợp lệ:` trong lời từ chối | = model | đọc `model_fields`; test E |
| skills `.md` | không nhắc `memory_declarations` | test F |

- `at` chỉ xuất hiện ở dòng `declare_point` của thẻ.
- Lược đồ synthesis **không** được gửi cho provider (`$ref` bị bỏ) ⇒ bề mặt khoá của mô hình là thẻ văn phạm.

## 6. Phản hồi sửa — `FEEDBACK_BEFORE_AFTER.json` = PASS

Đo trên fixture dẫn xuất:

| phần | trước | sau | Δ |
|---|---|---|---|
| lời từ chối | 331 | 296 | −35 |
| mảnh hợp đồng | 1587 (10 dòng) | 1017 (6 dòng) | −570 |
| lời từ chối + mảnh | 1918 | 1313 | −605 |
| prompt sửa (kể cả chương trình gửi lại) | 3818 | 3213 | −605 |
| thẻ văn phạm hình học | 6690 | 6733 | +43 |

**Lời từ chối trước:** không có mã, không có con trỏ.

**Lời từ chối sau:**
- có mã, con trỏ, khoá sai và tên các khoá hợp lệ;
- 0 giá trị ứng viên, 0 dấu lược đồ (`$defs`, `properties`…), 0 `statements`, 0 stack trace.

Đo lại sau khi gỡ mọi phép tiêm: trùng byte.

⚠️ `pipeline._prompt_sua` **vẫn gửi lại chương trình vừa viết** (≤6000 ký tự). Đó là thiết kế đo ngày 2026-08-31, không đổi ở wave này. Chỉ lời từ chối và mảnh hợp đồng không mang nội dung ứng viên.

**Byte không phải token.** Thẻ +43 byte trả ở **mọi** lượt synthesis, còn −605 byte chỉ có ở lượt **sửa**. Lỗ/lãi thật cần benchmark ⇒ `TOKEN_OPTIMIZATION = NOT_RUN`.

## 7. Fixture C02 và hành vi — `C02_REJECTED_ACCEPTED_COMPARISON.json`

**Fixture:**
- Nhãn `FIXTURE_CLASS = DERIVED_FROM_TRACE_POINTER`.
- Nền là chương trình synthesis đóng băng p6 (đề của C02). Phép nhầm ô đúng như trace thật: `initial_value` → `at` tại `/memory_declarations/0`.
- Băm dẫn xuất `a0394014…` **≠** candidate thật `12f3b31d…` ⇒ `EXACT_C02_REJECTED_FIXTURE = NOT_ESTABLISHED`.

| | START_HEAD | sau wave |
|---|---|---|
| fixture bị loại | `PROGRAM_SCHEMA` / `SCHEMA_SILENTLY_DROPPED_KEY`, lời không mã, không con trỏ | cùng pha/mã, lời mở bằng `[mã] /memory_declarations/0/at` |
| p6 (C02) | final_memory `79cf15e9…` · scene3d `db1e31ec…` · 7 vật | trùng · `ignored_keys = []` |
| p1 (C01) | final_memory `c934b023…` · scene3d `829f70b2…` · 13 vật | trùng · `ignored_keys = []` |

- **test_H:** sửa đúng ô cho ra **đúng** chương trình được nhận. Replay pipeline [bị loại, được nhận] trả final_memory và scene3d trùng START_HEAD.
- **test_J:** trace `synthesis-repair-trace/1` của runner liên kết lượt 3 → 4, đúng mã.

## 8. Tiêm lỗi — `FAULT_INJECTIONS.json`

| # | phép tiêm | đỏ | gỡ, trùng byte |
|---|---|---|---|
| F1 | detector không báo ⇒ khoá lạ bị bỏ im lặng | 16/47 | ✓ |
| F2 | thêm `at` vào dòng mẫu khai báo của thẻ | 4/60 (E, F, M, CA2) | ✓ |
| F3 | tập khoá thẻ lệch lược đồ (ẩn `model_assumption`) | 3/60 (E, M, CA2) | ✓ |
| F4 | validator tự gỡ khoá lạ trước khi kiểm | 20/47 | ✓ |
| F5 | đổi `initial_value` point3 của ứng viên **hợp lệ** | 8/47 (G, H, J, R2, R4, C1, P4, D2) | ✓ |

Cả ba tệp sản phẩm trùng byte snapshot chụp trước chuỗi tiêm; 0 dấu `TIÊM` còn lại.

## 9. Danh tính và cache — `IDENTITY_AND_CACHE_DECISION.json`

**Bề mặt mô hình: ĐỔI**, chỉ thẻ văn phạm.
- Khoá cache: `grammar_card` `6cbba188…` → `3fb8eeab…`; môi trường `5acd4a26…` → `28858c12…`.
- `prompts`, lược đồ synthesis/analyze, `capability` không đổi.

**`CACHE_VERSION` 95 → 95**, không bump:
- `main.py:910`, `:945` chỉ cache `status == "ok"`;
- chương trình hợp lệ cho cùng kết quả (§7), và mọi chương trình replay vẫn được nhận (test_B2);
- thay đổi chỉ tác động lượt synthesis mới và văn bản phản hồi sửa.

**Candidate** `e946582fdacfecc5…` → `37500cd92f134e44…` (94 file):
- đổi `pipeline.py`, `grammar_card.py`, `validator.py`;
- khớp giá trị khai trước trong `CANDIDATE_DIVERGENCE.json`;
- đóng băng trên worktree sạch tại `50cf37b`, rồi chép manifest sang cây nguồn; `--verify` khớp ở cả hai.

## 10. Cổng offline — `OFFLINE_GATES.json`

`APPLICATION_LLM_CALLS = REAL_PROVIDER_CALLS = NETWORK_REQUESTS = 0`.

**Toàn bộ backend, cây nguồn trước commit: 5169 passed, 2 failed.** Cả hai đúng dự kiến:
- `test_holdout_readiness_7b`: cây bẩn.
- `test_evaluation_candidate::test_ma_san_pham_khong_troi…`: candidate chưa đóng băng lại.

**Toàn bộ backend, worktree tại `50cf37b` kèm manifest vừa đóng băng: 5168 passed, 3 failed.**
1. `test_holdout_readiness_7b`: manifest chưa commit. Kiểm lại sau commit 2.
2. `test_thesis_runner_alignment::test_H6_…`: worktree checkout với `autocrlf=true` để artifact lịch sử ở dạng CRLF, còn test băm byte thô. Commit 1 không chạm các artifact đó. Cùng test **PASS** trong lượt cây nguồn.
3. `test_v3_product_path_parity::test_01_…[manifest.json]`: cùng nguyên nhân với mục 2.

**Backlog `CROSS_PLATFORM_ARTIFACT_HASH_TESTS`:** mục 2 và 3. Không sửa trong wave này.

Không chạy: Gemini, vision, analyze thật, trình duyệt live, camera, P1–P7 live, frontend (không đổi).

## 11. Cây nguồn và commit

Mỗi commit đều stage bằng đường dẫn tường minh, in `git diff --cached --name-status`, và dừng nếu có `frontend/public/favicon.svg`.

| commit | nội dung |
|---|---|
| `50cf37b` | validator + pipeline + thẻ + test + khoá danh tính cache + khai lệch candidate + `CODE_INDEX` |
| commit 2 | manifest candidate + báo cáo + artifact (chỉ băm/số byte/tên khoá/con trỏ; không chương trình, không prompt, không output provider) |

- Không merge, không push.
- `WAVE_CREATED_DIRTY_FILES = 0`.
- `USER_FAVICON_DELETION_PRESERVED = YES` — cây nguồn **không** sạch hoàn toàn: thay đổi favicon của user vẫn còn.
- JUnit của các phép tiêm và lượt toàn bộ **chỉ giữ ở máy** (`D:\tmp\algo-sim-synthesis-memory-declaration-alignment\evidence\`): traceback có thể chứa mảnh chương trình replay.

**Không tự ghi:** `TOKEN_OPTIMIZATION = PASS`, `FIRST_ATTEMPT_RATE_IMPROVED = YES`, `SYNTHESIS_TOKEN_SAVING` dương, `MERGE_ALLOWED = YES`.

`NEXT_ACTION = SYNTHESIS_FIRST_ATTEMPT_TOKEN_BENCHMARK`
