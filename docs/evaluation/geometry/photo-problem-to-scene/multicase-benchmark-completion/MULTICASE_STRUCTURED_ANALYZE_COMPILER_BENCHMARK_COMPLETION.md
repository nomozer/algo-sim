# MULTICASE_STRUCTURED_ANALYZE_COMPILER_BENCHMARK_COMPLETION

**Wave:** `RETRY_REMAINING_PREREGISTERED_CASES_LATER` · 2026-09-21 ·
nhánh `feat/photo-problem-to-scene` · START_HEAD `bd37015` · worktree thực thi
`D:/tmp/mcb-completion-exec` (sạch, `bd37015`)

```text
CLASSIFICATION            = MEASUREMENT_TOOL_REPAIR_REQUIRED
NEXT_ACTION               = COMPLETION_RUNNER_REPAIR_OFFLINE
COMPLETION_ANALYZE_HTTP   = 0          (dừng ở §2, trước mọi request)
PRECHECK                  = PASS       (dataset trùng byte bản đăng ký trước)
REMAINING_CASES_RUN       = 0 / 6      P06 P07 P08 N02 N03 N04 — NOT_RUN
PRODUCT_CODE_CHANGED      = NO         CANDIDATE e7bae036… · CACHE_VERSION 99
```

## 1. Vì sao dừng

Runner đã chạy lượt lịch sử **chọn đúng ca và dừng đúng lúc** — phần ấy không có
vấn đề. Nó dừng vì **không đo được ba thứ đặc tả này đòi**, và cả ba đều phải
sửa **trước** khi tiêu request, không phải sau:

**G1 — thân request thật không được ghi lại (§3).** Transport `CongHttp` có tính
`body_sha256` và endpoint cho từng request, nhưng chỉ giữ trong
`cong.records` trong bộ nhớ. Runner chỉ xuất `tong_hop()` và
`bang_chung_danh_tinh()`: băm prompt, băm văn bản người dùng, **tên** khoá cấu
hình, nhiệt độ. Chạy thử offline xác nhận: `BODY_SHA256_PERSISTED = false`,
`ENDPOINT_OR_MODEL_PERSISTED = false`. Sau lượt live sẽ không còn gì để so byte
với request dự kiến. Model (nằm trong URL) cũng không quan sát được.

**G3 — bộ chấm ca âm đếm quan hệ đề NÓI THẲNG là bịa (§6–§8).** Ca âm được chấm
bằng `so_quan_he(hd, [], [])`, nên **mọi** quan hệ mô hình khai đều thành
`UNVERIFIED_EXTRA`. Đây là lỗi đã khai ở N01, nhưng đặc tả chỉ đăng ký đính chính
cho N01. Với ba ca còn lại, đọc **đúng** vẫn bị phạt:

| ca | quan hệ đề nói thẳng mà bộ chấm sẽ đếm là bịa |
|---|---|
| N02 | `RT ⊥ (TVX)` |
| N03 | `KM ⊥ KN` (từ *"vuông tại K"*) |
| N04 | `GH ⊥ GL`, `HG ⊥ HL`, `DG ⊥ (GHL)` — cả ba đều được đề nói |

`GROUND_TRUTH.negative` không có tập quan hệ đề nói, nên không dẫn được đính chính
từ dữ liệu đóng băng. Đặt luật đính chính **sau** khi thấy kết quả là chấm lại
điểm của chính mình. Hệ quả phụ: `phan_loai` đòi `HALLUCINATED == 0` cho
`STRONG`/`READY`, nên hai lớp ấy **không thể đạt** kể cả khi mô hình làm đúng
hết.

**G4 — chưa có công cụ tổng hợp tái lập được (§7–§9).** `phan_loai` của runner
không có lớp `UNSAFE` (gộp vào `NOT_READY`), không đòi accuracy 1.0 cho `STRONG`,
không có ngưỡng accuracy < 0.75, và dùng nhãn next khác đặc tả. Tách *attempts*
khỏi *unique cases*, áp đính chính N01, ghi `UNKNOWN` cho token thiếu, tách độ
trễ khỏi thời gian chờ lỗi — chưa có mã nào làm. Tổng hợp viết tay sau lượt live
rơi thẳng vào `MEASUREMENT_INVALID` (*"không tái tạo được phép tổng hợp"*).

## 2. Cái runner làm ĐÚNG, không cần sửa — đã chạy thử

`main()` của `run_multicase_benchmark.py` **nguyên trạng**, trong worktree
`bd37015`, với `--live --tiep-tuc <CASE_RESULTS lịch sử> --ra <thư mục tạm>`.
Chỉ thay hai thứ ở biên: `httpx.AsyncHTTPTransport` → `MockTransport` (thay **bên
trong** `ChanMangThat`) và `doc_khoa` → khoá giả.

| | kịch bản A: mọi request 200 | kịch bản B: timeout ở request đầu |
|---|---|---|
| ca transport thấy | P06 P07 P08 N02 N03 N04 | P06 |
| gộp từ lịch sử | N01 P01 P02 P03 P04 P05 | N01 P01 P02 P03 P04 P05 |
| request | 6 | 1, `STOP_REASON = PROVIDER_ERROR` |
| Vision / Synthesis / retry | 0 / 0 / 0 | 0 / 0 / 0 |
| 33 file lịch sử | không đổi byte nào | không đổi byte nào |
| kết nối mạng thật | 0 | 0 |
| khoá giả trong artifact | không | không |

Kết cục ca trong kịch bản A là **giả**: phản hồi mock là `{}`. Nó chỉ dùng để quan
sát runner chọn ca nào, gửi bao nhiêu và ghi gì — không phải kết quả đo.

## 3. Tương đương request — phía dự kiến đã có, phía thật thì không

Transport giả thấy đúng byte `call_gemini` dựng. Mỗi ca chỉ có một request nên
thân request không phụ thuộc phản hồi. Hai lượt độc lập cho cùng băm, nên phía
dự kiến là tất định. Với cả 6 ca:

```text
system prompt   50a076e15ed9…   (= prompt đóng băng)
responseSchema  0542161e56ec…   (= lược đồ đóng băng, dạng default_sorted)
model           gemini-2.5-flash       temperature 0.1
JSON mode       application/json       thinkingConfig KHÔNG có
khoá trong thân request   KHÔNG
chỉ khác nhau   văn bản đề (bọc 'Đề bài:\n"""…"""')
```

So **thành phần** với request P06 của lượt lịch sử (lượt ấy có ghi băm thành phần):
văn bản người dùng, prompt hệ thống, khoá cấu hình, nhiệt độ — **khớp cả bốn**.
Tức là bề mặt mô hình không trôi giữa hai lượt. Còn chứng minh **trùng byte với
request thật** thì phải đợi G1. `REQUEST_EQUIVALENCE_RESULT = NOT_REACHED`.

## 4. Tiền kiểm §1 — PASS

Nhánh, HEAD `bd37015`, `main` `085cae6`, cây nguồn chỉ bẩn favicon, worktree sạch.
Candidate `--verify` PASS (`e7bae036…`, 103 tệp). `CACHE_VERSION` 99 = khoá cache
99. `DEFAULT_MODE` = `LLM_ONLY` (hằng số **và** giá trị giải ra). Prompt
`50a076e1…` (5672 byte), lược đồ `0542161e…`. Model `gemini-2.5-flash` **và**
biến `GEMINI_MODEL` vắng — model đè được bằng biến môi trường, nên phải kiểm cả
hai. Nhiệt độ 0.1, timeout 120 s. Khoá có trong `.env` nguồn (không in).
`ALLOW_LIVE_AI` vắng.

`BENCHMARK_MANIFEST` `e0439038…`, `CASE_REGISTRY` `ab6e19af…`, `GROUND_TRUTH`
`115c0518…` — **trùng byte** bản ở commit đăng ký trước `1f0b645`. Băm dataset
chính tắc `b1f199f9…` khớp giá trị đã đăng ký. `MANIFEST_OR_GROUND_TRUTH_DRIFT =
false`.

Runner ở `bd37015` khác bản đã chạy live (`19d1a6d`). So AST: **mọi hàm chấm
trùng**. `chay_mot_ca` chỉ thêm nhãn `FAILURE_ATTRIBUTION` cho ca `BUILD_FAILED`
(lịch sử không có ca nào như vậy), còn `main` thêm cờ `--contact-sheet`.
`EVALUATOR_DEFINITION_DRIFT = LABEL_ONLY`.

## 5. Lỗ không chặn nhưng wave sửa nên đóng cùng lúc

- **G2** — trần transport là hằng số 12, không đặt được 6. Giới hạn 6 hiện chỉ
  đứng trên *hàng đợi × ngân sách từng ca*. Nó đã quan sát được là 6, nhưng không
  phải trần cứng ở transport.
- **G5** — `quy_ket_that_bai` được định nghĩa mà **không nơi nào gọi**, ở cả hai
  bản runner. Ca hỏng ở Analyze không mang quy kết, nên không phân cụm được *"lỗi
  lặp lại"* — thứ mà tiêu chí `NOT_READY` của §8 cần.
- **G6** — token thiếu bị cộng như 0, còn timeout bị tính vào p95. §9 cấm cả hai.
  Việc này thuộc công cụ tổng hợp của G4.
- **G7** — envelope chỉ ghi ra đĩa sau khi cả vòng lặp xong. Tiền lệ P01 cho
  thấy tiến trình chết giữa chừng là mất ảnh của ca đã thành công.
- **G8** — **phát hiện mới trong lượt chạy thử này.** Phản hồi rỗng `{}` cho ra
  một `RequestContract` rỗng hợp lệ. Compiler từ chối nó bằng mã
  `GIVEN_FACT_WITHOUT_SOURCE`, và N02/N03/N04 đều được chấm `SAFE_REJECTION` với
  mã *đã đăng ký* — danh sách mã chấp nhận có 11 mã, giống hệt nhau cho mọi ca âm.
  Nghĩa là chỉ số an toàn ca âm **không phân biệt** *"từ chối vì khiếm khuyết đã
  đăng ký"* với *"từ chối vì mô hình không đọc được gì"*. Theo `GROUND_TRUTH` đóng
  băng thì đó vẫn là an toàn, và `GROUND_TRUTH` không được sửa. Cần một chỉ số
  **phụ**, đăng ký trước.
- **G9** — runner khác bản đã chạy live, nhưng chỉ ở nhãn (§4). Không cần sửa.

Chi tiết, bằng chứng và gợi ý sửa từng mục: `RUNNER_READINESS_GAPS.json`.

## 6. Việc wave `COMPLETION_RUNNER_REPAIR_OFFLINE` phải giao

1. Xuất theo `case_id`: `body_sha256`, model lấy từ URL, băm `responseSchema`
   (G1), và so byte với `REQUEST_EQUIVALENCE.json → EXPECTED_REQUESTS`.
2. Trần transport = số ca còn thiếu, dẫn từ hàng đợi thật (G2).
3. Một artifact **đăng ký trước**, tách khỏi `GROUND_TRUTH`: quan hệ đề nói thẳng
   cho N01–N04, dẫn **chỉ** từ đề đã đóng băng. Bộ chấm ca âm dùng nó (G3).
4. Công cụ tổng hợp có test, cài đúng §7–§9 của đặc tả completion. Nó đọc artifact
   lịch sử theo băm ở `HISTORICAL_EVIDENCE_LINK.json` (G4, G6).
5. Nối `quy_ket_that_bai` (G5). Ghi envelope ngay khi mỗi ca xong (G7). Thêm chỉ
   số phụ cho G8.
6. Biến kịch bản chạy thử ở §2 thành **test commit được**: hàng đợi đúng 6 ca,
   dừng sau lỗi, lịch sử bất biến, và phép tiêm lỗi cho từng mục trên.

Sau đó mới chạy lại `RETRY_REMAINING_PREREGISTERED_CASES_LATER` — vẫn đúng 6 ca,
đúng thứ tự, tối đa 6 request.

## 7. Cái KHÔNG làm, và vì sao

- **0 request.** P06 không được gọi lại. Không có request thử provider.
- **Không sửa runner.** Đặc tả §2 và §11 cấm sửa trong wave này.
- **Không có lớp tổng hợp.** `COMPLETION_CASE_RESULTS_REDACTED`,
  `AGGREGATE_12_CASE_RESULTS`, `RELATION_QUALITY_BY_CASE`,
  `QUALITY_AND_SAFETY_COMPARISON`, `TOKEN_USAGE_BY_CASE`,
  `ACCEPTANCE_STATISTICS`, contact sheet: **NOT_RUN** (không có ca mới nào để
  tổng hợp). Đính chính N01 (unverified extra 1, hallucinated 1) vẫn đứng ở
  `multicase-benchmark/NEGATIVE_SAFETY_RESULTS.json` và sẽ vào lớp tổng hợp khi
  có công cụ.
- **Không commit harness chạy thử.** Đặc tả §11 giới hạn nội dung commit. Mẹo
  dựng harness nằm ở §2 — đủ để wave sửa dựng lại thành test.
- **Artifact lịch sử không đổi byte nào** — `HISTORICAL_EVIDENCE_LINK.json` giữ
  băm LF của cả 33 file.

## 8. Kiểm

Tập tập trung trong worktree thực thi: **416 passed**. Bộ ấy gồm benchmark,
compiler, quan hệ có cấu trúc, prompt Analyze, bộ chấm ghép cặp, grounding, cổng
trực quan, runner live ảnh, ngưỡng prompt và cache identity. Candidate `--verify`
PASS. Full backend chạy **trong wave này** ở worktree sạch `bd37015`: **5699 passed
· 1 skipped · 0 failed**, và worktree vẫn sạch sau khi chạy. Wave không đổi mã
nào, nên END_HEAD chỉ khác `bd37015` ở thư mục completion này.
