# VISION_PROMPT_GUARD_SIMPLIFICATION

> Nhánh `feat/photo-problem-to-scene` · 2026-09-15.
> START_HEAD `f09c141` · `main` giữ `085cae6`.
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/vision-prompt-guard-simplification/`.
> **0 request Gemini.**

```text
VISION_PROMPT_GUARD_SIMPLIFICATION          = PASS
FINAL_PROMPT_SHA256                         = b499dc7a…  (đúng blob d8ad614)
TARGET_REQUEST_EQUALS_SUCCESSFUL_CONTROL    = YES        (02b2104d… = request đối chứng HTTP 200)
LOCAL_GUARD_EQUALS_LIVE_TESTED_GUARD        = YES        (blob 99dc986c…, băm ngữ nghĩa 32bbac92…)
MODEL_CONTRACT_ALIGNMENT                    = không tự ghi — mô hình vẫn có thể điền given_relations; an toàn đến từ guard
```

## 1. Kết luận

Wave `VISION_DIAGRAM_ONLY_PROVENANCE_GUARD_FIX` làm hai việc cùng lúc: thêm guard tất định, và thêm luật 4/9 vào prompt đọc ảnh.

**Dữ kiện đo được:**
- Prompt có luật 4/9 (`748dfd3b…`) ReadTimeout 2/2 ở trần 60 s.
- Prompt cũ (`b499dc7a…`) HTTP 200 2/2.
- Request đối chứng chỉ khác prompt. Nó cho phản hồi thật có 3 `given_relations`, và guard tại `f09c141` cách ly đủ 3.
- Liên hệ giữa luật 4/9 và timeout được hỗ trợ nhưng **chưa chứng minh nhân quả**.

**Wave này giữ thứ đã chứng minh, bỏ thứ không cần:**
- Prompt trở lại **đúng blob** `d8ad614`, qua `git restore` một đường dẫn, không viết tay.
- Guard **không đổi một byte**.
- Request mà mã sau sửa sẽ gửi **trùng từng byte** request đối chứng HTTP 200. Việc triển khai đúng cấu hình ấy không cần thêm request.

## 2. Tiền kiểm — `PRECHECK.json` = PASS

| mục | giá trị |
|---|---|
| HEAD · `main` | `f09c141` · `085cae6` |
| cây nguồn | chỉ ` D frontend/public/favicon.svg` (của user) |
| worktree `D:\tmp\algo-sim-c03-live-worktree` | sạch |
| prompt cũ (git `d8ad614`) | SHA-256 `b499dc7a29fec4a3…570d6` |
| prompt đang dùng | SHA-256 `748dfd3be03da8dc…2d980` |
| candidate `--verify` tại `f09c141` | `29720197a84ea1b3…` |
| lược đồ gửi | `46810954…` |
| kết quả đối chứng | PASS/PASS |
| `REQUEST_DIFF` | chỉ prompt khác |
| quét bí mật đối chứng | 0 |

## 3. Thay đổi (commit 1 `dfabf5e`)

**Prompt:** `transcribe.md` 1967 → 1874 byte. Blob hiện tại = blob `d8ad614` (`dc8029de…`), văn bản LF `b499dc7a…`.
- Kho đặt `core.autocrlf=true`: blob LF, ổ đĩa CRLF. Byte được so bằng blob git.

**Hợp đồng test — prompt là hướng dẫn, guard là thẩm quyền an toàn:**
- **Gỡ** test đòi câu luật 4/9 phải tồn tại.
- **Thêm** `test_A_prompt_doc_anh_TRUNG_BYTE_prompt_cua_request_doi_chung_HTTP_200`: SHA-256 đầy đủ.
- **Thêm** `test_B_guard_TRUNG_ban_da_xu_ly_phan_hoi_Gemini_that`: băm ngữ nghĩa đã đăng ký gồm nguồn `apply_diagram_only_provenance_guard`, `ProvenanceGuardReport`, `ExtractionResult`, `_rong`, `assess_extraction` cùng các hằng số. Đổi guard ⇒ phải đo lại trên phản hồi thật.
- **F bổ sung:** telemetry không mang dòng prompt nào, không mang khoá.
- **Hai ô ghim `prompts`** đổi `dceff16e` → `c50c8c6b`. Cả hai chiều dựng lại được chỉ bằng `transcribe.md` (`tests/photo_problem_identity.py`).

**Đỏ trước khi đổi prompt:**
- test guard: A đỏ, 34 xanh — B và F đã xanh;
- 3 ô danh tính đỏ.

**Sau khi đổi prompt:** 115 xanh.

**Không đổi:** `image_extraction.py`, lược đồ, model, timeout, cấu hình suy nghĩ, transport, analyze/synthesis/frontend.

## 4. Tương đương request — `TARGET_REQUEST_EQUIVALENCE.json` = PASS (0 mạng)

Request đích được dựng offline từ worktree tại commit 1 bằng đúng đường runner, **không tiêm prompt**. Kết quả so với request đối chứng HTTP 200 (run `20260914T192855Z-1f9b480d`):

| thứ so | kết quả |
|---|---|
| model / API version / method / non-streaming | trùng |
| byte ảnh JPEG | trùng |
| prompt | `b499dc7a…` |
| lược đồ | trùng (`46810954…`) |
| generationConfig | trùng |
| safety | NOT_SET = NOT_SET |
| thinking / maxOutputTokens | NOT_SET = NOT_SET |
| timeout | 60 s |
| **thân request** | `02b2104d…` = thân request thật HTTP 200 |

**Guard:**
- blob `image_extraction.py` tại `f09c141` = tại commit 1 (`99dc986c…`);
- băm ngữ nghĩa = `32bbac92…`;
- `MEASURED_SYSTEM_PATHS` từ `f09c141` chỉ đổi `transcribe.md`.

## 5. Phát lại đầu ra thật — `GUARD_REPLAY_PARITY.json`

- **C01, C02:** bản công khai và phán quyết trùng bản mô hình; 0 cách ly, 0 sự kiện ⇒ `C01_C02_BEHAVIOR_PARITY = PASS`.
- **C03** (lượt `…49ffa191` và lượt đối chứng `…1f9b480d`, cùng đầu ra), mỗi lượt:
  - 3 `given_relations` thô → cách ly 3;
  - bản công khai rỗng dữ kiện;
  - 7 quan sát giữ nguyên;
  - `MISSING_PROBLEM_TEXT`;
  - 0 nội dung thô trong log.

## 6. Danh tính và cache — `IDENTITY_AND_CACHE_DECISION.json`

**Candidate** `29720197a84ea1b3…` → `e946582fdacfecc5…` (94 file):
- Từ `f09c141` tới commit 1, mã được đo chỉ khác `transcribe.md` ⇒ băm đổi chỉ do prompt.
- **Không** trở về `b32887a9…`, vì guard vẫn là mã mới.
- Đóng băng trên worktree sạch tại `dfabf5e`, không phải trên cây nguồn đang có thay đổi favicon.
- Manifest chép sang cây nguồn; `--verify` khớp.

**Khoá danh tính cache:** `prompts` `dceff16e` → `c50c8c6b`. Tệp khoá trùng blob `d8ad614`.

**`CACHE_VERSION` 95 → 95**, không bump:
- cache `/api/analyze` khoá theo văn bản, envelope do skill tầng B sinh — không đổi;
- cache ảnh trong tiến trình đã khoá theo băm prompt.

## 7. Cổng offline — `OFFLINE_GATES.json`

`APPLICATION_LLM_CALLS = REAL_PROVIDER_CALLS = NETWORK_REQUESTS = 0`.

Toàn bộ backend chạy trong worktree tại commit 1, kèm manifest vừa đóng băng: **5151 passed, 3 failed, 1 skipped**. Cả ba đã có giải thích:

1. **`test_holdout_readiness_7b`:** cây bẩn vì manifest chưa commit. Kiểm lại sau commit 2.
2. **`test_H6_…` (thesis-final `stage_a_first_attempt.json`)** — lỗi môi trường, không phải hồi quy của wave: worktree checkout với `autocrlf=true` để artifact ở dạng CRLF, còn test băm byte thô. CRLF→LF cho đúng giá trị mong đợi, blob không đổi, và cùng test trên cây nguồn (LF) **PASS**.
3. **`test_01_artifact_V3_goc_KHONG_doi_mot_byte[manifest.json]`:** cùng nguyên nhân với mục 2.

Không chạy Gemini, trình duyệt live, camera, P1–P7, frontend — frontend không đổi.

## 8. Cây nguồn và commit

Mỗi commit đều stage bằng đường dẫn tường minh, in `git diff --cached --name-status`, và dừng nếu có `frontend/public/favicon.svg`.

| commit | nội dung |
|---|---|
| `dfabf5e` | prompt + test + khoá danh tính cache + khai lệch candidate + `CODE_INDEX` |
| commit 2 | manifest candidate + báo cáo + artifact (chỉ băm/số mục, không ảnh, không response thô) |

- Không merge, không push.
- `WAVE_CREATED_DIRTY_FILES = 0`.
- `USER_FAVICON_DELETION_PRESERVED = YES` — cây nguồn **không** sạch hoàn toàn: thay đổi favicon của user vẫn còn.

**Không tự ghi:** `MODEL_CONTRACT_ALIGNMENT = PASS`, `TOKEN_OPTIMIZATION = PASS`, `REAL_PHONE_PHOTO_EVIDENCE = ESTABLISHED`, `MERGE_ALLOWED = YES`.

`NEXT_ACTION = SYNTHESIS_MEMORY_DECLARATION_SCHEMA_PROMPT_ALIGNMENT`
