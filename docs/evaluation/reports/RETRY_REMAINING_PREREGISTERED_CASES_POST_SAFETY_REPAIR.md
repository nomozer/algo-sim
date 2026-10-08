# RETRY_REMAINING_PREREGISTERED_CASES_POST_SAFETY_REPAIR

**2026-09-21** · nhánh `feat/photo-problem-to-scene` · START_HEAD `d01254c` ·
`main` giữ `085cae6` · execution worktree `D:/tmp/rrpsr-exec` (detached `d01254c`, sạch) ·
**0 request Gemini · 0 request mạng**

```text
WAVE RESULT       = MEASUREMENT_INVALID     — dừng TRƯỚC request đầu tiên
LÝ DO             runner chưa đạt hai hợp đồng bắt buộc của đặc tả:
                  §2 REGISTRY_BINDING: 3/17 trường · §6 bản ghi từng ca: không bền vững
BENCHMARK STATE   không đổi — lịch sử: PROVIDER_INCOMPLETE, 6/12 ca có kết cục
NEXT_ACTION       COMPLETION_MEASUREMENT_REPAIR_OFFLINE
```

## 1. Cái đã đạt — mọi điều kiện ở §1, §3, §4

- **Kho:** đúng nhánh; HEAD `d01254c`; `main` `085cae6`; cây nguồn chỉ có
  ` D frontend/public/favicon.svg`; 0 tệp staged; không merge/rebase dở.
- **Danh tính:**
  - candidate `--verify` PASS (`077dbc6b…`, 103 tệp); cache identity PASS;
    `CACHE_VERSION` 99; mặc định `LLM_ONLY`;
  - registry v1 `52bc6379…` và v2 `03a87ba3…` khớp bản đã commit;
  - manifest `e0439038…` và ground truth `115c0518…` không đổi;
  - lịch sử benchmark khớp băm (0 tệp trôi).
- **Test tập trung:** 160/160 xanh, gồm registry v1/v2, ràng buộc runner, quan
  sát và tương đương request, trần transport, chấm ca âm, TARGETED, bộ tổng hợp,
  quy kết, token/độ trễ, N04, candidate, cache identity. Fixture A–F đạt: N04 tuple
  đúng ⇒ v1 NO / v2 YES; `{}` ⇒ v2 NO; sai mã/rule/pha hoặc có compiler/cảnh ⇒ NO;
  N01–N03 v2 = v1; request thứ 7 bị chặn ở transport với **0 byte** tới tầng trong.
- **Tương đương request:** 6 request `P06 P07 P08 N02 N03 N04`, dựng hai lần, cùng
  băm.
  - Mỗi request khớp `EXPECTED_REQUEST_HASHES.json` (14 trường) và thân request
    của wave registry v2.
  - `gemini-2.5-flash` · temperature 0.1 · `application/json`. `responseSchema`
    giữ đúng bản đã đăng ký.
  - Không `thinkingConfig`, không `maxOutputTokens`, không chuỗi registry nào
    trong thân request.
  - Timeout 120 s, retry 0.

## 2. Vì sao dừng

**R1 — ràng buộc registry thiếu 14/17 trường bắt buộc (§2).**
`kiem_rang_buoc_registry()` (đúng hàm runner chạy trước request đầu, gọi khô) ghi
đủ phần **ngữ nghĩa**: băm v1, băm v2, candidate, commit hành vi, vai trò dataset,
v2 đã commit. Nhưng thiếu các trường sau:

- danh tính kho, nhánh, execution HEAD;
- `CACHE_VERSION`;
- băm manifest và ground truth;
- băm runner và bộ tổng hợp;
- model, băm prompt, băm schema;
- danh sách ca + thứ tự, ngân sách request;
- mốc thời gian trước request đầu.

Model, prompt, schema và thứ tự **có** được ghi, nhưng chỉ ở
`COMPLETION_CASE_RESULTS`/`REQUEST_OBSERVATIONS`, **sau** vòng lặp. Ràng buộc
cũng không chứng minh hai điều đặc tả đòi:

- N01–N03 giữ hành vi v1: chỉ có băm registry đã giải;
- tuple N04 khớp mã tại HEAD: bộ nạp chỉ kiểm hằng luật có mặt.

Theo §2: binding không PASS ⇒ dừng trước transport, `MEASUREMENT_INVALID`.

**R2 — bản ghi ca không bền vững sau từng ca (§6).**
`COMPLETION_CASE_RESULTS_REDACTED`, `REQUEST_OBSERVATIONS` và
`REQUEST_BUDGET_PROOF` chỉ được ghi **sau** vòng lặp. Sau từng ca, chỉ envelope
của ca dương dựng được mới ghi nguyên tử. Probe (transport giả): P06 đọc đúng,
rồi tiến trình chết khi P07 đang ở transport. Còn lại đúng
`REGISTRY_BINDING.json`, `STAGE_A_GATE.json` và `envelopes/P06.json`. Mất bản ghi
P06 (quan hệ, token, độ trễ, quy kết), quan sát request và bằng chứng ngân sách,
trong khi quota **đã tiêu**. Test G7 hiện chỉ khoá envelope, nên lỗ này không đỏ
ở đâu.

**R3 — phần chấm sau phản hồi không được bọc.** Các bước `so_quan_he`,
`chay_tang_dung` và nạp registry nằm ngoài `try`. Probe: tầng dựng của P07 ném
ngoại lệ ⇒ `main()` chết với đúng ba tệp như trên. Đây là cùng một hậu quả với
R2, qua một đường khác.

Cả ba đều là lỗi **công cụ**, không phải sản phẩm. Theo §13, tôi không vá chúng
trong wave này. Lịch sử benchmark vẫn trùng băm sau mọi probe.

## 3. Trạng thái benchmark — không đổi

Bộ tổng hợp đã commit, chạy trên lịch sử, hai lần trùng byte:

- `PROVIDER_INCOMPLETE`; 8 request Analyze lịch sử (1 void, 1 lỗi provider,
  6 phản hồi hợp lệ); 6/12 ca có kết cục.
- P06 = `PROVIDER_ERROR`; P07, P08, N02, N03, N04 = `NOT_RUN_AFTER_PROVIDER_ERROR`.
- Cụm `MODEL_MALFORMED_RELATION = [P03, P05]` còn nguyên, nên trần của lượt
  hoàn tất vẫn là `NOT_READY`.
- `EVIDENCE_CLASS = MIXED_DEVELOPMENT_EVIDENCE` · `UNTOUCHED_HOLDOUT_CLAIM = false`.

## 4. Không tạo — vì 0 request

`COMPLETION_CASE_RESULTS_REDACTED` · `MERGED_CASE_RESULTS_REDACTED` ·
`RELATION_QUALITY_BY_CASE` · `NEGATIVE_SAFETY_RESULTS` · `COMPILER_QUALITY_BY_CASE`
· `TOKEN_USAGE_BY_CASE` · `LATENCY_SUMMARY` · `BROWSER_REPLAY_RESULT` ·
`CONTACT_SHEET.png`. Không có output mới, không có envelope mới để phát lại.

## 5. Artifact

`docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark-completion-post-safety-repair/`:
`PRECHECK` · `REGISTRY_BINDING` (kết quả FAIL + bảng 17 trường) ·
`REQUEST_EQUIVALENCE` · `REQUEST_BUDGET_PROOF` · `OFFLINE_TESTS` ·
`RUNNER_READINESS_GAPS` · `AGGREGATE_RESULT` · `SECRET_SCAN`.

Khoá API **không được nạp** vào tiến trình nào của wave này: worktree không có
`backend/.env`, và mọi tiến trình chạy với `GEMINI_API_KEY` bị gỡ. Vì vậy quét
bí mật dùng mẫu hình dạng, không so khớp khoá thật.

```text
NEXT_ACTION = COMPLETION_MEASUREMENT_REPAIR_OFFLINE
  (R1 ràng buộc đủ 17 trường trước request đầu · R2 ghi + đọc lại bản ghi rút gọn
   sau MỖI ca · R3 bọc phần chấm để request đã tiêu luôn để lại bản ghi)
```
