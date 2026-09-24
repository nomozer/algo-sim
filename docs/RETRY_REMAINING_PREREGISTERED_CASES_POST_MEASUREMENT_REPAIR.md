# RETRY_REMAINING_PREREGISTERED_CASES_POST_MEASUREMENT_REPAIR

**2026-09-22** · nhánh `feat/photo-problem-to-scene` · START_HEAD `e76419f` · `main` giữ `085cae6` ·
execution worktree `D:/tmp/rrpmr-exec` (detached `e76419f`, sạch, không `.env`) ·
**6 request Analyze · 0 Vision · 0 Synthesis · 0 retry**

```text
FINAL_BENCHMARK_CLASSIFICATION = NOT_READY          (12/12 ca có kết cục · 0 unsafe · 0 lỗi đo)
TRẦN ĐÃ ĐĂNG KÝ  cụm MODEL_MALFORMED_RELATION = [P03, P05] (lịch sử) ⇒ cao nhất là NOT_READY
LƯỢT NÀY         P06 P07 P08 → FULL_PIPELINE_PASS · N02 N03 N04 → SAFE_REJECTION, targeted v2 = YES
NHẬT KÝ          6/6 SCORED · đặt chỗ 6/6 · ràng buộc 17/17 ghi và kiểm TRƯỚC transport
DATASET_CLASS    MIXED_DEVELOPMENT_EVIDENCE · UNTOUCHED_HOLDOUT_CLAIM = false (N04 là ca hồi quy)
```

## 1. Trước request đầu tiên

- **Tiền kiểm:**
  - đúng nhánh, HEAD, `main`; cây nguồn chỉ bẩn bởi favicon của user;
  - worktree thực thi sạch, không `.env`;
  - candidate `077dbc6b…` `--verify` PASS; cache identity PASS; `CACHE_VERSION` 99;
    `LLM_ONLY`;
  - manifest, ground truth, registry v1/v2 trùng băm đăng ký; lịch sử benchmark 0
    tệp trôi.
- **Test tập trung:** 214/214 xanh (ràng buộc 17 trường, trôi, registry v2, N04,
  nhật ký bền, nguyên tử, chết tiến trình, lỗi chấm, lỗi provider, ngân sách, quan
  sát request, bộ tổng hợp, token, độ trễ, candidate, cache).
- **Chứng minh lại bằng transport giả:**
  - chết ở P07 ⇒ P06 còn đủ; nối lại ⇒ 0 request, P07
    `TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH`;
  - lỗi chấm ⇒ `MEASUREMENT_ERROR`, không chạy ca kế;
  - lỗi provider ⇒ ghi ngay, token `UNKNOWN`;
  - 27 kiểu trôi ràng buộc ⇒ 0 request;
  - request thứ 7 ⇒ 0 byte.
- **Tương đương request:** sáu request dựng hai lần, trùng nhau và trùng băm đăng
  ký.
  - `gemini-2.5-flash` · 0.1 · JSON mode; generationConfig chỉ có `responseMimeType`,
    `responseSchema`, `temperature`.
  - Không `thinkingConfig`, không `maxOutputTokens`, không chuỗi registry trong thân
    request.

Khoá API chỉ được nạp vào **tiến trình live**, qua thay thế lệnh, không in ra và
không ghi xuống đĩa. `ALLOW_LIVE_AI` chỉ bật cho tiến trình ấy.

## 2. Lượt live

Runner ghi `REGISTRY_BINDING.json` (17/17 trường) nguyên tử, nạp lại, kiểm lại, rồi
mới mở transport. Tệp ràng buộc có trước tệp ca đầu tiên; sau lượt chạy, kiểm lại
offline tại cùng HEAD vẫn PASS. Sáu request đi đúng thứ tự
`P06 P07 P08 N02 N03 N04`, mỗi ca một lần. Cả sáu thân request `MATCH` băm đăng ký.
HTTP 200 × 6, không request nào bị chặn. Nhật ký kết thúc với **6/6 `SCORED`**.

| ca | vai trò | kết cục | quan hệ đúng | compiler · route | đáp số | token | Analyze ms |
|---|---|---|---|---|---|---|---|
| P06 | holdout pilot | FULL_PIPELINE_PASS | 2/2 | SUPPORTED/COMPILED · served | 7 ✔ | 2541 | 5265 |
| P07 | holdout pilot | FULL_PIPELINE_PASS | 2/2 | SUPPORTED/COMPILED · served | 15/2 ✔ | 2295 | 4667 |
| P08 | holdout pilot | FULL_PIPELINE_PASS | 2/2 | SUPPORTED/COMPILED · served | 60 ✔ | 2290 | 4247 |
| N02 | holdout pilot | SAFE_REJECTION · `BASE_PERPENDICULAR_RELATION_MISSING` | 1/1 | NOT_ELIGIBLE | — | 2342 | 4202 |
| N03 | holdout pilot | SAFE_REJECTION · `LINE_PLANE_RELATION_MISSING` | 1/1 | NOT_ELIGIBLE | — | 2093 | 3544 |
| N04 | **hồi quy** | SAFE_REJECTION · `STRUCTURED_RELATION_CONTRADICTION` | 3/3 | **không tới compiler** | — | 3340 | 9308 |

Ba ca dương: không thiếu, không trùng, không mâu thuẫn quan hệ; không extra chưa kiểm
chứng, không giả định mô hình. Mọi cổng sau Analyze đều đạt: FactGraph, compiler, kiểm
kiểu, IR static, grounding, route, cổng trực quan, topology, `final_memory`, đáp số.
Compiler mất ~0,1 ms và 0 token model.

**N04 — tuple hồi quy khớp chính xác overlay v2:**

- `INVALID_CONFLICT` · `STRUCTURED_RELATION_CONTRADICTION` ·
  `MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE` · pha `FACT_GRAPH`;
- compiler/chương trình/cảnh/`final_memory`/đáp số: **không**;
- targeted: v1 = NO (kỳ vọng gốc trước bản sửa, như đã đăng ký), v2 = **YES**.

**N02, N03:** targeted v1 = v2 = YES, đọc đủ thông tin tối thiểu, 0 fact bịa.
⚠️ Mã của N03 (`LINE_PLANE_RELATION_MISSING`) không có trong danh sách
`acceptable_rejection_codes` của ground truth (đăng ký sớm hơn). Registry targeted
v1 — thẩm quyền của chỉ số TARGETED — cho phép mã ấy. Phân loại không đổi.

## 3. Tổng hợp 12 ca

Bộ tổng hợp đã commit, chạy lại offline hai lần: **trùng byte**, và trùng bản runner
ghi.

- **Lịch sử:** P01–P05, N01 qua băm, 0 tệp trôi. **Completion:** P06–P08, N02–N04.
- **Ca dương:** full pipeline **6/8** (Wilson 95% [0,41; 0,93]); quan hệ tới hạn đúng
  6/8, độ chính xác 0,75; thiếu 4 quan hệ (P03, P05).
- **Ca âm:** từ chối an toàn **4/4**; unsafe **0**; targeted v2 YES 3 · NOT_MEASURED 1
  (N01 lịch sử, output đã khử thô).
- **Cụm lỗi lặp:** `MODEL_MALFORMED_RELATION = [P03, P05]` ⇒ **`NOT_READY`** — trần đã
  đăng ký, không đổi sau khi thấy kết quả.
- **Token completion:** in 9 204 · out 2 930 · thought 2 767 · **tổng 14 901**, 0
  UNKNOWN; mỗi lượt median 2 318,5, min 2 093, max 3 340. Tổng cả benchmark:
  **UNKNOWN** — hai lượt lịch sử (timeout P06, lượt void) không có usage. Phần đã
  biết là 30 718.
- **Độ trễ Analyze thành công:**
  - completion p50 4 246,5 ms · p95 9 308,0 ms (6 mẫu), 0 chờ lỗi provider;
  - cả benchmark p50 4 666,6 ms · p95 10 195,9 ms. Lượt timeout lịch sử 120 002,8 ms
    đứng riêng.
- **Không kết luận được:** `STATISTICAL_SIGNIFICANCE = NOT_ESTABLISHED` ·
  `TOKEN_OPTIMIZATION = NOT_PRODUCTION_ESTABLISHED`.

## 4. Phát lại trình duyệt

P06, P07, P08 — ba ca có envelope an toàn do compiler dựng — phát lại bằng
`compiler-scene-replay.mjs`: **0 request model**, `/api/*` chặn ở biên mạng. Cả
**1440×900: 3/3** và **390×844 DPR 2: 3/3** đều đạt 11/11 ô:

- canvas có mặt và có diện tích; đủ nhãn điểm;
- chuyển bước qua lại; đáp số hiển thị đúng;
- không tràn khung, nút bước không bị che;
- chỉ gọi API đã chặn, đúng một lần Analyze, không lỗi console nghiêm trọng.

N02–N04 không có envelope nên không phát lại. `CONTACT_SHEET.png` chỉ chứa ảnh giao
diện và chỉ số.

## 5. Khử thô

Nhật ký thô của lượt chạy ở ngoài kho và **không** được commit.

- Artifact commit chỉ còn băm, mã, số đếm, boolean, token, độ trễ.
- Định danh do mô hình chọn (`source_fact_id`, tên witness, tên container) được thay
  bằng SHA-256.
- Chuỗi lỗi chỉ giữ tên lớp; ở lượt này cả ba trường lỗi đều rỗng.
- Envelope (có thể chứa chương trình) **không** commit.
- Mọi chuỗi còn lại trong artifact đã được rà: chỉ là mã, băm, nhãn điểm, hằng số, hay
  ghi chú do tôi viết.
- Quét bí mật: 0 phát hiện; thư mục chạy thô cũng sạch theo mẫu hình dạng.

## 6. Artifact

`docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark-completion-live-post-measurement-repair/`:

- `PRECHECK` · `REGISTRY_BINDING` · `REQUEST_EQUIVALENCE` · `REQUEST_BUDGET_PROOF`
- `COMPLETION_JOURNAL_REDACTED` · `COMPLETION_CASE_RESULTS_REDACTED` ·
  `MERGED_CASE_RESULTS_REDACTED`
- `RELATION_QUALITY_BY_CASE` · `NEGATIVE_SAFETY_RESULTS` · `COMPILER_QUALITY_BY_CASE`
- `TOKEN_USAGE_BY_CASE` · `LATENCY_SUMMARY` · `AGGREGATE_RESULT`
- `BROWSER_REPLAY_RESULT` · `SECRET_SCAN` · `CONTACT_SHEET.png`

Không mã nào đổi: sản phẩm, prompt, schema, FactGraph, compiler, runner, bộ tổng hợp,
registry, candidate, cache.

```text
NEXT_ACTION = ANALYZE_FAILURE_CLUSTER_DIAGNOSIS
  (bộ tổng hợp mang nhãn cũ STRUCTURED_ANALYZE_GENERALIZATION_DIAGNOSIS — cùng trỏ vào cụm P03/P05)
```
