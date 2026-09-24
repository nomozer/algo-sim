# C02_SYNTHESIS_FIRST_ATTEMPT_LIVE_REVALIDATION

> Nhánh `feat/photo-problem-to-scene` · 2026-09-15.
> START_HEAD `685f7e8` · `main` giữ `085cae6`.
> Worktree thực thi `D:\tmp\algo-sim-c03-live-worktree` tại `685f7e8`, sạch.
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/c02-synthesis-first-attempt-live-revalidation/`.
> **1 request Gemini synthesis · 0 vision · 0 analyze · 0 retry · 0 sửa.**

```text
C02_SYNTHESIS_FIRST_ATTEMPT_LIVE_REVALIDATION = PASS
FIRST_ATTEMPT_ACCEPTED                        = YES
TOKEN_SAVING_ON_THIS_RUN                      = 2255   (SUPPORTED_ON_ONE_C02_RUN)
TOKEN_OPTIMIZATION                            = NOT_ESTABLISHED
```

## 1. Kết luận

Đây là **một mẫu**, không phải bằng chứng thống kê.

- Cùng checkpoint và **cùng thân request từng byte** với pilot bị loại (`77c580df…`), lượt này **được nhận ngay lượt đầu**.
- Cảnh, topology, `final_memory` và đáp số đều đúng.

Pilot trước (`20260915T061735Z-7b979fce`) bị loại ở `PROGRAM_SCHEMA / SCHEMA_VALUE_ERROR`. Hai kết cục khác nhau trên cùng một request, nên đầu ra của mô hình **không tất định** ở `temperature = 0.1`. Một cặp mẫu không đo được tỉ lệ nhận lượt đầu.

Lỗi của pilot cũ vẫn `NOT_RECOVERABLE`; lượt này không cung cấp thông tin gì về nguyên nhân của nó.

## 2. Tiền kiểm — `PRECHECK.json` = PASS (0 request)

| mục | giá trị |
|---|---|
| nhánh · HEAD · `main` | `feat/photo-problem-to-scene` · `685f7e8` · `085cae6` |
| cây nguồn / worktree | chỉ ` D frontend/public/favicon.svg` (của user) / sạch tại `685f7e8` |
| candidate · khoá cache | `37500cd92f134e44…` khớp · khớp, `CACHE_VERSION` 95 |
| mã sản phẩm từ pilot (`828180e`) tới nay | 0 thay đổi trong `backend/app`; khoá danh tính cache trùng từng byte |
| model · thử lại · timeout | `gemini-2.5-flash` · `ApiBudget(max_attempts=1)` · 120 s (mặc định sản phẩm, không đổi) |
| khoá Gemini | có trong `backend/.env` cây nguồn, không in, không chép; `ALLOW_LIVE_AI` chỉ đặt trong tiến trình live |
| test tập trung (worktree) | **208 xanh** — chẩn đoán từ chối, trace v2, hợp đồng khai báo, runner (ngân sách HTTP, khử bí mật), checkpoint, danh tính cache, candidate, khởi tạo điểm |

**Checkpoint** (dùng lại, không chạy vision hay analyze):
- `CHECKPOINT_SHA256 = 7c955655…6444`.
- `REQUEST_CONTRACT_SHA256 = 767d5c94…6800`.
- **Nguồn được chứng minh lại:** thân request dựng từ checkpoint bằng mã tại `d8ad614` trùng `body_sha256` của request synthesis #3 trong run `20260914T141706Z-9a469909`.
- Đủ 5 dữ kiện then chốt và nghĩa vụ `volume(S.ABC)`.

## 3. Launcher trace v2 — `TRACE_V2_LAUNCHER_PROOF.json` = PASS (0 request)

**Launcher** `rev_launcher.py` (ngoài repo, SHA-256 ghi trong artifact):
- Chạy đường sản phẩm `run_pipeline(serve)`; chỉ tầng analyze được thay bằng checkpoint.
- Cổng `CongHttp`: trần 1, theo tầng {vision 0, analyze 0, synthesis 1}.
- Trace dựng bằng chính `dung_trace_vong_sua` ⇒ `synthesis-repair-trace/2`.

Chạy **đúng cùng hàm** với provider giả, trong `ChanMangThat`:

| fixture | kết quả |
|---|---|
| chương trình C02 đã được nhận | PASS — topology, `final_memory`, đáp số PASS; 0 lượt sửa |
| `initial_value` mâu thuẫn với `declare_point` | `SCHEMA_VALUE_ERROR` · `""` EXACT · `value_error` · `SemanticProgramSpec._nang_declare_point` · `object` |
| `initial_value` số thực | `IR_STATIC_CHECK`, không có chi tiết Pydantic (đúng thiết kế v2) |
| `at` trong khai báo | `SCHEMA_SILENTLY_DROPPED_KEY` · `/memory_declarations/0/at` EXACT |

**Ở mọi fixture:**
- 1 request gửi, 0 vision/analyze, 0 retry; lượt bị loại thì lượt sửa bị chặn trước transport (`STAGE_BUDGET_EXHAUSTED`);
- thân request = `77c580df…`;
- trace không có khoá `input`/`msg`/`ctx`, không mốc giá trị, không bí mật giả (không đăng ký với bộ che), không văn bản chương trình, không prompt.

⚠️ `initial_value` là `Any` ở Pydantic. Vì vậy sai kiểu **không** tới lược đồ: nó hoặc được nhận, hoặc bị `IR_STATIC_CHECK` loại. Lỗi lược đồ gắn với `initial_value` là toạ độ mâu thuẫn với một `declare_point` cùng tên.

## 4. Tương đương request — `REQUEST_EQUIVALENCE.json` = YES

| trường | kết quả |
|---|---|
| checkpoint · RequestContract | trùng pilot |
| model | `gemini-2.5-flash` |
| `generationConfig` | `temperature = 0.1`, `responseMimeType = application/json`; không `responseSchema`, không `thinkingConfig`, không `maxOutputTokens` |
| system prompt | trùng commit của run lịch sử |
| **thân request** | dựng offline `77c580df…` = thân pilot = thân lượt live này |

Khoá API nằm ở query của URL, không nằm trong thân request.

## 5. Lượt thật — `C02_LIVE_RESULT_REDACTED.json`

| mục | giá trị |
|---|---|
| run | `20260915T102431Z-b036feae` |
| HTTP · độ trễ | 200 · 17 377,2 ms |
| request gửi / chặn · lượt logic · retry | 1 / 0 · 1 · 0 |
| trace | `synthesis-repair-trace/2` · lượt 0 `ACCEPTED` (`PASSED`, nguồn `SEMANTIC_ROUTE_EVENT`) |
| parse JSON · Pydantic/validator | PASS · PASS |
| lượt sửa gửi / bị chặn | 0 / 0 |

## 6. Hợp đồng và cảnh — `CONTRACT_AND_TOPOLOGY_RESULT.json`

| kiểm | kết quả |
|---|---|
| `memory_declarations` | 2 mục, 0 khoá ngoài 8 khoá hợp lệ |
| `at` trong khai báo | không |
| khoá lạ mang dữ liệu · `ignored_keys` · sự kiện observer | 0 · `[]` · 0 |
| cảnh | không rỗng, 6 vật; điểm đúng S, A, B, C |
| khối | 1 khối, 4 mặt tam giác, cạnh = {SA, SB, SC, AB, AC, BC} |
| trên toạ độ chính xác của cảnh | \|AB\|² = 9 · \|AC\|² = 16 · \|SA\|² = 25 · AB ⟂ AC · SA ⟂ AB · SA ⟂ AC · A, B, C không thẳng hàng — **7/7 PASS** |
| `final_memory` | `V_SABC` = 10 chính xác, hiển thị `10` |
| đáp số đọc từ cảnh | `measure.volume` = `10` (exact `10`) |

## 7. Token — `TOKEN_COMPARISON.json`

| | vào | ra | suy nghĩ | tổng |
|---|---|---|---|---|
| lượt này (1 lượt, được nhận) | 3854 | 630 | 3281 | **7765** |
| mốc lịch sử (2 lượt: 5434 bị loại + 4586 được nhận) | | | | 10020 |
| pilot trước (1 lượt, bị loại) | | | | 5972 |

- Chương trình hợp lệ, cảnh đúng, đáp số đúng ⇒ so được với mốc lịch sử: **−2255 token (−22,5 %)**, `SUPPORTED_ON_ONE_C02_RUN`.
- So với pilot bị loại: +1793 token, hiệu số thô — không cùng kết cục.
- Token suy nghĩ lượt này (3281) cao hơn lượt được nhận trong mốc lịch sử (295).

**Không khẳng định:** mức tiết kiệm sản xuất, tỉ lệ nhận lượt đầu, ý nghĩa thống kê. `TOKEN_OPTIMIZATION = NOT_ESTABLISHED`.

## 8. Cây nguồn và commit

- Không sửa mã sản phẩm, prompt, lược đồ, validator hay model. Candidate và `CACHE_VERSION` giữ nguyên.
- Một commit gồm báo cáo và 7 artifact JSON. Không có output thô, prompt, chương trình, checkpoint hay JUnit.
- Stage bằng đường dẫn tường minh; staged diff không có `frontend/public/favicon.svg`.
- Không merge, không push. `main` không đổi.
- Worktree thực thi sạch. Thay đổi favicon của user còn nguyên.

`NEXT_ACTION = MULTICASE_SYNTHESIS_TOKEN_BENCHMARK`
