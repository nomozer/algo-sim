# B02_STRUCTURAL_COVERAGE_LIVE_REVALIDATION

> Nhánh `feat/photo-problem-to-scene` · 2026-09-15.
> START_HEAD `77ab45c` · `main` giữ `085cae6`.
> Worktree thực thi `D:\tmp\algo-sim-c03-live-worktree` tại `77ab45c`, sạch trước và sau lượt chạy.
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/b02-structural-coverage-live-revalidation/`.
> **1 request Gemini synthesis · 0 vision · 0 analyze · 0 retry · 0 sửa.**
> `dataset_split = DEVELOPMENT_PILOT_FOLLOWUP` — không thuộc holdout, không vào mẫu số độ chính xác cuối.

```text
B02_STRUCTURAL_COVERAGE_LIVE_REVALIDATION = SILENT_QUALITY_FAILURE
FIRST_ATTEMPT_ACCEPTED                    = YES
SCENE_TOPOLOGY_RESULT                     = FAIL   (cảnh không có vật section)
FINAL_MEMORY_RESULT / ANSWER_RESULT       = PASS / PASS
CURRENT_RUN_UNCOVERED_OBLIGATIONS         = NONE   (structural coverage không từ chối lượt này)
HISTORICAL_B02_UNCOVERED_OBLIGATION       = NOT_RECOVERABLE
TOKEN_OPTIMIZATION                        = NOT_ESTABLISHED
```

## 1. Kết luận

Đây là **một mẫu** follow-up, không phải bằng chứng thống kê.

- Lượt mới **được nhận ngay lượt đầu**; route phục vụ. final_memory đúng cả 3 nghĩa vụ và đáp số đúng cả 3 (`72` · `9` · `3√6`); quan hệ 7/7, nhãn điểm 5/5; vệ sinh hợp đồng sạch.
- Nhưng cảnh **không có vật `section` nào** (0 thay vì ≥ 1), nên phép kiểm đa giác thiết diện ở tầng topology FAIL. Theo tiêu chí đăng ký trước, kết cục là `SILENT_QUALITY_FAILURE`: hệ phục vụ một lời giải tính đúng diện tích thiết diện mà cảnh không dựng thiết diện.
- Structural coverage không từ chối lượt này, nên `route_coverage_diagnostic = null` và lượt mới không có nghĩa vụ nào chưa phủ.
- Lượt benchmark cũ (`20260915T110322Z-8a7be506`) bị loại ở `ROUTE_STRUCTURAL_COVERAGE`. Cùng một thân request, hai kết cục khác nhau ⇒ đầu ra của mô hình **không tất định** ở `temperature = 0.1`.
- Lượt này **không** cho biết nghĩa vụ nào thiếu trong output lịch sử: `HISTORICAL_B02_UNCOVERED_OBLIGATION = NOT_RECOVERABLE`.
- Mô hình dùng thứ gì thay cho thiết diện thì **không xác định được** từ bằng chứng đã rút gọn: output, chương trình và cảnh không được lưu, theo luật của wave.

## 2. Tiền kiểm — `PRECHECK.json` = PASS (0 request)

| mục | kết quả |
|---|---|
| nhánh · HEAD · `main` | `feat/photo-problem-to-scene` · `77ab45c` · `085cae6` |
| cây nguồn / worktree | chỉ ` D frontend/public/favicon.svg` / sạch tại `77ab45c` |
| candidate · khoá cache | `544a0b56a40c6107…` khớp · khớp, `CACHE_VERSION` 95 |
| bề mặt mô hình từ benchmark (`de9fe4c`) tới nay | skills, `gemini.py`, thẻ văn phạm, contract, analyze contract, validator, khoá cache, schema: 0 thay đổi |
| mã sản phẩm từ benchmark tới nay | đúng 3 file của wave chẩn đoán cổng phủ (`pipeline.py` · `coverage_gate.py` · `route.py`) |
| model · temperature · thử lại · timeout | `gemini-2.5-flash` · 0.1 · `ApiBudget(max_attempts=1)` · trần 120 s, lời gọi synthesis không hạ trần |
| trace | `synthesis-repair-trace/2`, có trường `route_coverage_diagnostic` |
| khoá Gemini | có trong `backend/.env` cây nguồn, không in; worktree không có `.env`; `ALLOW_LIVE_AI` không có ở tiến trình cha |
| test tập trung (worktree sạch) | **255 xanh** — chẩn đoán cổng phủ, trace v2 (hai file), runner (ngân sách HTTP, khử bí mật), checkpoint, căn hợp đồng khai báo, candidate, khoá cache, ma trận nghiệm thu |

**Manifest benchmark** — mọi hash đọc đủ độ dài từ manifest đã commit:
- `MANIFEST_SHA256 = 803ff1ad5934b978853a4ceed1b4a2d56e66e662c2e2f3f8459e0323a6eb14c4` (tệp ở cây nguồn và worktree; trùng blob `HEAD` sau chuẩn hoá xuống dòng).
- checkpoint `ef2ca6e92ea5507ea73c29bf4c2aa63d711c09ccd123be4236f0f801929e9970` · RequestContract `fd8880c45c8714df70c2bf3e89141f42ebef96decbafa8613d4eff919c58644e` · thân request `e604ec720d530a6434b933248b2671a4b611e2cd47f5485348ee66713255095f`.
- Đề, 3 nghĩa vụ (`/obligations/0` volume · `/1` area · `/2` distance), ground truth và tệp oracle đều trùng manifest.

**Launcher:** hàm chạy và chấm lấy nguyên từ `bench.py` của benchmark; tệp chỉ được nạp khi SHA-256 (`2616d209…`) trùng `launcher_sha256` trong proof đã commit.

## 3. Đăng ký trước — `B02_LIVE_PREREGISTRATION.json`

Ghi **trước mọi request** (`1d9a929e…`):
- ca, split, `include_in_final_holdout_metrics = false`, lý do không phải holdout;
- mọi hash, model, `generationConfig`, 3 nghĩa vụ kèm con trỏ;
- ground truth: băm kỳ vọng đã đăng ký và đáp số theo từng nghĩa vụ;
- trần 1 request · 0 retry · 0 sửa;
- tiêu chí sáu kết cục và luật token.

## 4. Launcher offline — `LAUNCHER_OFFLINE_PROOF.json` = PASS (0 request)

Chạy **đúng hàm của lượt live** với provider giả trong `ChanMangThat`. Mọi fixture: 1 request, 0 vision/analyze, 0 retry, 0 sửa, thân request trùng manifest, 0 mạng thật.

| fixture | kết cục | kiểm |
|---|---|---|
| A · chương trình đủ nghĩa vụ (đã được nhận lịch sử) | PASS | không chẩn đoán; cảnh, final_memory, đáp số, vệ sinh hợp đồng đạt |
| B · thiếu volume | DIAGNOSTIC_REJECTION | chỉ `/obligations/0` · `WITNESS_WITHOUT_PRODUCER` |
| C · thiếu area | DIAGNOSTIC_REJECTION | chỉ `/obligations/1` |
| D · thiếu distance | DIAGNOSTIC_REJECTION | chỉ `/obligations/2` |
| E · thiếu hai | DIAGNOSTIC_REJECTION | `/obligations/0`, `/obligations/2`, đúng thứ tự |
| F · khoá giả KHÔNG đăng ký với bộ che | DIAGNOSTIC_REJECTION | chẩn đoán, trace, dòng kết quả: không tên chương trình, không output thô, không prompt, không khoá |
| G · lỗi lược đồ | OTHER_MODEL_OUTPUT_REJECTION | request thứ hai bị chặn trước transport (`STAGE_BUDGET_EXHAUSTED`) |
| H · provider 503 | PROVIDER_ERROR | 1 request, không request thứ hai |

Chẩn đoán ở B–F đạt đủ các kiểm:
- một hàng mỗi nghĩa vụ; requested = 3; covered + uncovered = requested;
- con trỏ EXACT theo thứ tự nguồn; loại khớp hợp đồng;
- mã thuộc từ vựng và khớp trạng thái; mọi chuỗi trong từ vựng đóng;
- trùng bản rút gọn kiểm trên hợp đồng checkpoint; trùng số `missing` và mã `chan_doan_nghia_vu` cũ;
- chạy lại offline hai lần cho kết quả trùng.

⚠️ **Lỗi bộ đo, sửa trước mọi request.**
- Lần proof đầu FAIL ở A. Kiểm riêng tư của dòng kết quả đòi không có tên nào của chương trình, nhưng hàng chất lượng ghi nhãn điểm và tên witness **đã đăng ký công khai trong manifest**.
- Sửa: dòng kết quả chỉ được chứa tên có trong manifest; chẩn đoán và trace vẫn đòi rỗng tuyệt đối.
- Bản FAIL giữ local, không commit. Tương đương request chạy lại cho sha launcher mới.

## 5. Tương đương request — `REQUEST_EQUIVALENCE.json` = YES

| trường | kết quả |
|---|---|
| checkpoint · RequestContract | trùng manifest |
| model · `generationConfig` | `gemini-2.5-flash` · `temperature = 0.1`, `responseMimeType = application/json`; không `responseSchema`, `thinkingConfig`, `maxOutputTokens` |
| system prompt | `0d370e11…`, trùng manifest |
| thẻ văn phạm | có trong văn bản người dùng (`9bb2b64d…`); nguồn không đổi từ benchmark |
| **thân request** | dựng offline `e604ec72…` = manifest = bản ghi live của benchmark |
| khoá API | nằm ở query của URL, không trong thân |

## 6. Lượt thật — `B02_LIVE_RESULT_REDACTED.json`

| mục | giá trị |
|---|---|
| run | `20260915T151549Z-632a4c1a` |
| HTTP · độ trễ | 200 · 17 367,6 ms |
| request gửi / chặn · lượt logic · retry | 1 / 0 · 1 · 0 |
| thân request | `e604ec72…` = manifest |
| parse JSON · Pydantic/validator · vòng synthesis · route | PASS · PASS · PASSED · PASS (`served`) |
| trace | v2 · lượt 0 `ACCEPTED`, nguồn `SEMANTIC_ROUTE_EVENT` |
| `memory_declarations[].at` · khoá chặn lạ · `ignored_keys` | 0 · 0 · `[]` |
| khoá trong output | 0 lần |

## 7. Chất lượng — `QUALITY_RESULT.json`

Chấm trên toạ độ chính xác của cảnh, theo kỳ vọng đã đăng ký trong manifest benchmark.

| nhóm | kết quả |
|---|---|
| cảnh | không rỗng, 21 vật |
| nhãn điểm A, B, C, D, S | 5/5 |
| vật tối thiểu | 7/8 — **`section` ≥ 1: FAIL** (điểm, khối, mặt phẳng, đường thẳng, ba đại lượng đo: PASS) |
| quan hệ (toạ độ 5 điểm, mặt phẳng z = 3, đường BD) | 7/7 |
| topology | 1/2 — khối chóp S.ABCD PASS; **đa giác thiết diện (0;0;3)(3;0;3)(3;3;3)(0;3;3): FAIL** |
| final_memory theo witness | 3/3 (`72` · `9` · `3√6`) |
| đáp số theo phép đo | 3/3 |

Phụ loại launcher ghi `SCENE_OR_ANSWER` (nhánh gộp cảnh/đáp số); thực tế chỉ topology hỏng.

## 8. Structural coverage — `ROUTE_COVERAGE_DIAGNOSTIC.json`

- Không áp dụng: route không dừng ở `structural_coverage`, nên `route_coverage_diagnostic = null` (đúng thiết kế, không có chẩn đoán giả).
- RequestContract có 3 nghĩa vụ; route phục vụ ⇒ cổng phủ cấu trúc đã qua cả 3. Chẩn đoán từng hàng chỉ phát khi cổng từ chối.
- `CURRENT_RUN_UNCOVERED_OBLIGATIONS = NONE`.
- `HISTORICAL_B02_UNCOVERED_OBLIGATION = NOT_RECOVERABLE`.

## 9. Token — `TOKEN_USAGE.json`

| | vào | ra | suy nghĩ | tổng |
|---|---|---|---|---|
| lượt này (1 lượt, được nhận, chất lượng FAIL) | 4046 | 2155 | 1494 | **7695** |
| B02 benchmark (1 lượt, bị loại) | 4046 | 1699 | 3445 | 9190 |

- Kết cục không phải PASS ⇒ `TOKEN_DELTA` và `TOKEN_SAVING_ON_THIS_RUN` = `NOT_COMPARABLE`.
- Hiệu số thô −1495 chỉ để tham khảo, không phải tiết kiệm.
- `TOKEN_OPTIMIZATION = NOT_ESTABLISHED`. Lượt này không gộp vào tỉ lệ 3/4 của benchmark; benchmark lịch sử vẫn `PARTIAL`.

## 10. Dữ liệu khoá luận — `THESIS_EVALUATION_ROW.json`

Một hàng `DEVELOPMENT_PILOT_FOLLOWUP`, mục đích `ERROR_ANALYSIS_AND_RELIABILITY`, `include_in_final_accuracy_denominator = false`.

Nội dung: danh tính (candidate, prompt, thẻ, thân request, hợp đồng, checkpoint, manifest), số request, chấp nhận, chất lượng, độ trễ, token, liên kết benchmark.

Dùng được cho phần phân tích lỗi (một output được phục vụ nhưng thiếu thiết diện), **không** phải kết quả holdout.

## 11. Bảo mật — `SECRET_SCAN.json`

- Quét evidence, work, báo cáo và thư mục artifact: khoá API 0 lần, 0 mẫu khoá Google, 0 mẫu header/query.
- Không commit output thô, prompt, chương trình, checkpoint riêng tư, JUnit.

## 12. Cây nguồn và commit

- Không sửa mã sản phẩm, prompt, lược đồ, validator, route hay model. Candidate và `CACHE_VERSION` giữ nguyên (verify sau live: khớp).
- Một commit gồm báo cáo và 10 artifact JSON đã rút gọn. Stage bằng đường dẫn tường minh; staged diff không có `frontend/public/favicon.svg`.
- Không merge, không push. `main` không đổi. Worktree thực thi sạch; thay đổi favicon của user còn nguyên.

`NEXT_ACTION = SYNTHESIS_ACCEPTED_OUTPUT_QUALITY_DIAGNOSIS`
