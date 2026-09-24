# MULTICASE_SYNTHESIS_TOKEN_BENCHMARK

> Nhánh `feat/photo-problem-to-scene` · 2026-09-15.
> START_HEAD `de9fe4c` (= `PRIOR_C02_REVALIDATION_EVIDENCE_COMMIT`) · `main` giữ `085cae6`.
> Worktree thực thi `D:\tmp\algo-sim-c03-live-worktree` tại `de9fe4c`, sạch.
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/multicase-synthesis-token-benchmark/`.
> **4 request Gemini synthesis · 0 vision · 0 analyze · 0 retry · 0 sửa.**

```text
MULTICASE_SYNTHESIS_FIRST_ATTEMPT = PARTIAL   (3/4 đạt đầy đủ; 1 ca bị cổng phủ của route loại)
FIRST_ATTEMPT_ACCEPTANCE_RATE     = 0.75      (Wilson 95 %: 0.3006 – 0.9544; n = 4)
TOKEN_EFFICIENCY_PROFILE          = ESTABLISHED
TOKEN_OPTIMIZATION                = NOT_ESTABLISHED
```

## 1. Kết luận

Bốn bài khác nhau thật, mỗi bài đúng **một** lượt synthesis đầu tiên, trên mã hiện tại:

- **3/4** được nhận ngay; cảnh, topology, `final_memory` và đáp số khớp ground truth đã đăng ký.
- **1/4 (B02)** bị loại ở `ROUTE_STRUCTURAL_COVERAGE / requested_operation_uncovered`:
  - chương trình qua parse, Pydantic/validator và mọi cổng của vòng synthesis;
  - cổng phủ nghĩa vụ của route chặn trước khi phục vụ;
  - không có output sai nào được nhận im lặng.

Đây là mẫu **rất nhỏ**. Tỉ lệ 0,75 có khoảng tin cậy 95 % trải từ 0,30 tới 0,95. Nó không phải ước lượng tỉ lệ sản xuất.

## 2. Tiền kiểm — `PRECHECK.json` = PASS (0 request)

| mục | giá trị |
|---|---|
| nhánh · HEAD · `main` | `feat/photo-problem-to-scene` · `de9fe4c` · `085cae6` |
| `PRIOR_C02_REVALIDATION_EVIDENCE_COMMIT` | `de9fe4c` — commit chứa `docs/C02_SYNTHESIS_FIRST_ATTEMPT_LIVE_REVALIDATION.md`; báo cáo cũ không bị sửa |
| cây nguồn / worktree | chỉ ` D frontend/public/favicon.svg` (của user) / sạch tại `de9fe4c` |
| candidate · khoá cache | `37500cd92f134e44…` khớp · khớp, `CACHE_VERSION` 95 |
| model · temperature · thử lại · trace | `gemini-2.5-flash` · 0.1 · `max_attempts = 1` · `synthesis-repair-trace/2` |
| khoá Gemini | có, không in; `ALLOW_LIVE_AI` chỉ đặt trong tiến trình live |
| test tập trung (worktree) | **216 xanh** — chẩn đoán từ chối, trace v2, hợp đồng khai báo, runner (ngân sách HTTP, khử bí mật), checkpoint vision, tích hợp ảnh → tầng B, danh tính cache, candidate, khởi tạo điểm |

⚠️ **Lỗi bộ đo, sửa trước khi đóng băng.** Bản tiền kiểm đầu báo đỏ `TEMPERATURE_0_1_IN_SYNTHESIS_CALL`. Nguyên nhân: nó cắt lời gọi `call_gemini(` tới dấu `)` đầu tiên, mà dấu đó thuộc `load_skill(skill)`, nên không thấy `0.1`. Bộ đo đã sửa bằng cách khớp cặp ngoặc; bản lỗi giữ ở `work/`.

## 3. Corpus — `MULTICASE_BENCHMARK_MANIFEST.json`

Đóng băng lúc `2026-09-15T11:02:55Z`, **trước mọi request thật**. SHA-256 `803ff1ad5934b978853a4ceed1b4a2d56e66e662c2e2f3f8459e0323a6eb14c4`.

| ca | nguồn | họ hình | nghĩa vụ | checkpoint · RequestContract |
|---|---|---|---|---|
| B01 | C02 (checkpoint run `…9a469909`) | convex_polyhedron | volume(S.ABC) | `7c955655…` · `767d5c94…` |
| B02 | thesis-final p1 (`raw/analyze_0.json`) | polygon_and_planar_section | volume · area · distance | `ef2ca6e9…` · `fd8880c4…` |
| B03 | thesis-final p3 | ball | volume · area | `9a29087d…` · `a64a4f5c…` |
| B04 | thesis-final p4 | cylinder | volume · lateral_area | `fb1150e3…` · `91e7449e…` |

**Ground truth chỉ lấy từ nguồn đăng ký trước:**
- đề bài: toạ độ, mặt phẳng, đường thẳng;
- `thesis-final-acceptance/EXPECTED_RESULTS.json`: oracle độc lập, không gửi cho mô hình;
- `RUN_GROUND_TRUTH.json#C02`.

**Kỳ vọng từng ca:**
- tên điểm và các vật phải có;
- quan hệ trên toạ độ chính xác: độ dài², vuông góc, không thẳng hàng, điểm đúng toạ độ, mặt phẳng, đường qua hai điểm;
- topology: khối đa diện (tập đỉnh, số mặt, tập cạnh), đa giác thiết diện, khối cầu, đường tròn, hình trụ;
- `final_memory` theo witness của từng nghĩa vụ;
- đáp số hiển thị.

**Không chọn:**
- C01 — cùng đề với C02;
- p5 (nón) — hợp lệ, nhưng spec chỉ cần trụ *hoặc* nón;
- p2, p6, p7.

Mọi quyết định chọn ca đều có trước khi gửi request đầu tiên.

**Request đầu của từng ca** (dựng offline bằng MockTransport):
- thân `77c580df…` · `e604ec72…` · `504973a2…` · `5a31c7e8…`;
- `generationConfig` chỉ có `temperature = 0.1` và `responseMimeType`; không `responseSchema`, không `thinkingConfig`, không `maxOutputTokens`.

## 4. Launcher offline — `LAUNCHER_OFFLINE_PROOF.json` = PASS (0 request)

**Cách chạy:**
- Launcher (ngoài repo) chạy đường sản phẩm `run_pipeline(serve)`, chỉ thay tầng analyze bằng checkpoint.
- Mỗi ca một `CongHttp` mới: trần 1, theo tầng {vision 0, analyze 0, synthesis 1}.
- Trace dựng bằng chính `dung_trace_vong_sua`.
- Provider giả chạy bên trong `ChanMangThat`.

| fixture | kết quả |
|---|---|
| chương trình đã được nhận trong lịch sử của B01 · B02 · B03 | `ACCEPTED_QUALITY_PASS` — bộ chấm đúng trên cả ba họ hình |
| chương trình lịch sử B04 | `ACCEPTED_QUALITY_FAIL`: cảnh, `final_memory`, đáp số PASS nhưng 7 khai báo mang khoá trang trí `label` (bị bỏ qua, được báo) |
| lỗi lược đồ (B02, `type` sai) | `/memory_declarations/0/type` · EXACT · `literal_error`; request thứ hai bị chặn trước transport |
| `at` trong khai báo (B01) | `SCHEMA_SILENTLY_DROPPED_KEY` · `/memory_declarations/0/at` |
| khoá trang trí (B01) | `ignored_keys` được phát hiện |
| luật dừng | 2 lượt bị loại ⇒ dừng sau 2 request; lỗi provider ở ca đầu ⇒ dừng sau 1; khi mọi ca hợp lệ ⇒ đủ 4 ca, 4 request |

Ở mọi fixture:
- trace v2 không có khoá `input`/`msg`/`ctx`;
- không mốc giá trị, không bí mật giả (không đăng ký với bộ che), không prompt;
- thân request trùng manifest.

⚠️ **Lỗi kỳ vọng của bộ đo, sửa trước khi đóng băng.** Bản proof đầu đòi cả bốn chương trình lịch sử đều PASS, và trượt ở B04. Chương trình thesis-final p4 sinh ngày 2026-09-08, trước wave căn hợp đồng khai báo, nên mang `label`. Kỳ vọng được sửa; manifest và ground truth **không đổi**. Bản proof lỗi giữ ở `work/`.

## 5. Kết quả live — `CASE_RESULTS_REDACTED.json` · `QUALITY_COMPARISON.json`

| ca | HTTP · độ trễ | kết cục | topology · final_memory · đáp số |
|---|---|---|---|
| B01 | 200 · 8 767,5 ms | nhận ngay | PASS · PASS · PASS |
| B02 | 200 · 24 277,0 ms | **bị loại**: `ROUTE_STRUCTURAL_COVERAGE` / `requested_operation_uncovered` | không chạy |
| B03 | 200 · 11 259,7 ms | nhận ngay | PASS · PASS · PASS |
| B04 | 200 · 8 442,2 ms | nhận ngay | PASS · PASS · PASS |

- **Thân request:** cả 4 trùng manifest.
- **Hợp đồng khai báo (4 ca):** 0 khoá lạ mang dữ liệu, 0 `ignored_keys`, 0 `at`, 0 khoá ngoài 8 khoá hợp lệ.

**B02:**
- parse PASS, validator PASS, vòng synthesis `PASSED`;
- route dừng ở `structural_coverage`;
- trace v2 ghi pha và mã ổn định; không có chi tiết Pydantic, vì đây không phải lỗi lược đồ ⇒ `POINTER_STATUS = NOT_APPLICABLE`.

⚠️ **Khoảng trống chẩn đoán.** Launcher lưu pha, mã và trạng thái tóm tắt, **không** lưu nghĩa vụ nào chưa được phủ. Vì vậy báo cáo **không** nói được B02 thiếu thể tích, diện tích thiết diện hay khoảng cách. Không chạy lại ca.

## 6. Token — `TOKEN_USAGE_BY_CASE.json`

| ca | vào | ra | suy nghĩ | tổng | tỉ trọng suy nghĩ · ra | kết cục |
|---|---|---|---|---|---|---|
| B01 | 3854 | 905 | 850 | 5609 | 0,15 · 0,16 | hợp lệ |
| B02 | 4046 | 1699 | 3445 | 9190 | 0,37 · 0,18 | bị loại |
| B03 | 3906 | 902 | 1613 | 6421 | 0,25 · 0,14 | hợp lệ |
| B04 | 3856 | 823 | 560 | 5239 | 0,11 · 0,16 | hợp lệ |

| tổng hợp | giá trị |
|---|---|
| tổng vào · ra · suy nghĩ · tổng | 15 662 · 4 329 · 6 468 · **26 459** |
| trung bình · median · min/max | 6 614,8 · 6 015 · 5 239 / 9 190 |
| token bị loại · tỉ trọng | 9 190 · 0,3473 |
| p95 | không tính (≤ 4 mẫu) |

**Lịch sử:**
- **C02** — ghi riêng, không gộp vào mẫu bốn ca:
  - `HISTORICAL_C02_SUCCESSFUL_TOKENS = 10020`;
  - `CURRENT_C02_ACCEPTED_SAMPLE_TOKENS = 7765` (lượt revalidation trước);
  - B01 lượt này 5609.
- **B02–B04:** `BASELINE = NOT_AVAILABLE`. Lượt thesis-final dùng bề mặt mô hình khác: prompts `55ac1ca6…` ≠ `c50c8c6b…`, grammar card `6cbba188…` ≠ `3fb8eeab…`. Không ước lượng, không suy từ byte.

## 7. Thống kê và ngân sách — `ACCEPTANCE_STATISTICS.json` · `REQUEST_BUDGET_PROOF.json`

| mục | giá trị |
|---|---|
| ca đăng ký · đã chạy | 4 · 4 (không dừng sớm) |
| nhận lượt đầu · bị loại · lỗi provider | 3 · 1 · 0 |
| tỉ lệ nhận lượt đầu · Wilson 95 % | 0,75 · [0,3006; 0,9544] — mẫu nhỏ, khoảng rộng |
| đạt chất lượng · topology · đáp số | 3 · 3 · 3 |
| request synthesis · vision · analyze · sửa · retry | 4 · 0 · 0 · 0 · 0 |
| trong ngân sách (≤ 4) | có |

**Cổng:** 3/4 đạt đầy đủ; ca lỗi có pha/mã ổn định từ trace v2; không có topology hay đáp số sai bị nhận ⇒ **PARTIAL**.

**Kết luận token:**
- `TOKEN_EFFICIENCY_PROFILE = ESTABLISHED` — usageMetadata thật của provider cho cả 4 request.
- `TOKEN_OPTIMIZATION = NOT_ESTABLISHED` — thiếu ba baseline tương đương, và không đạt 4/4.

## 8. Cây nguồn và commit

- Không sửa mã sản phẩm, prompt, lược đồ, validator, model hay cấu hình suy luận. Candidate và `CACHE_VERSION` giữ nguyên.
- Một commit gồm báo cáo và artifact đã rút gọn. Không có output thô, prompt, chương trình, checkpoint hay JUnit.
- Stage bằng đường dẫn tường minh; staged diff không có `frontend/public/favicon.svg`.
- Không merge, không push. `main` không đổi.
- Worktree sạch. Thay đổi favicon của user còn nguyên.

**Không tự ghi:** tiết kiệm sản xuất, ý nghĩa thống kê, `TOKEN_OPTIMIZATION = SUPPORTED_ON_REGISTERED_CASES`, `MERGE_ALLOWED = YES`.

**Việc kế tiếp.** Nhánh brief định cho PARTIAL giả định con trỏ EXACT (`SYNTHESIS_TARGETED_RULE_ALIGNMENT`). Lỗi của B02 lại nằm ở cổng phủ nghĩa vụ của route, không có con trỏ. Đề xuất: `SYNTHESIS_STRUCTURAL_COVERAGE_REJECTION_DIAGNOSIS` — offline, ghi nghĩa vụ nào chưa được phủ cho lượt bị route loại — trước khi quyết định có chỉnh gì. Quyết định thuộc về user.
