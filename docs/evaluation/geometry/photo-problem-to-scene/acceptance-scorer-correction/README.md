# `acceptance-scorer-correction/` — bằng chứng trước/sau cho bộ chấm nghiệm thu ảnh đề bài

**0 request mạng · 0 lượt gọi provider thật · mọi bản duyệt ở đây là `SIMULATED_REVIEW`.**
Thư mục này chứng minh bộ chấm của `backend/scripts/run_photo_problem_live.py` đã được sửa
**trong phạm vi kiểm thử**. Nó không chứng minh Gemini đọc đúng ảnh thật, không chứng minh
mô phỏng dựng đúng từ ảnh, và không mang một chữ ký người duyệt nào.

```text
REAL_PROVIDER_EVIDENCE      = NOT_ESTABLISHED
HUMAN_CRITICAL_FACT_REVIEW  = PENDING
REAL_PHOTO_ACCEPTANCE       = NOT_RUN
```

"Trước" là runner ở `684420d`, nạp thẳng từ blob git (`runner_sha256.before = 599a1e47…`);
"sau" là runner ở commit sửa (`f72d744e…`). Cùng một đầu vào đi qua cả hai.

| tệp | sinh bởi | nói gì |
|---|---|---|
| `BEFORE_AFTER_TESTS.json` | `prove_photo_scorer_correction.py` từ hai JUnit XML | 69 test viết TRƯỚC bản sửa: trước 18 xanh / 51 đỏ, sau 69 xanh. 51 FIXED · 18 GUARD_ALREADY_PRESENT · 0 hồi quy. Tệp test runner cũ sau sửa 56/56. Liệt kê 4 thay đổi ở test cũ và lý do |
| `FACT_MATCHING_PROOF.json` | như trên | 19 hàng: `z = 3` / `z=3` · `z = 30` · `z = -3` · `z = 3.1` · `z = 3 + x`; `A` / `A1` · `A′`; `⊥` / `∥`; `∈` / `∉`; trường cấu trúc không che văn bản; mục thêm `SA ⊥ BD` chờ người. 13 FIXED · 6 đã có guard |
| `C03_REJECTION_PROOF.json` | như trên | 16 hàng: mã đăng ký đúng · hai mã ngoài danh sách · thiếu đăng ký · mã có thông báo mà không bao giờ được phát · HTTP 401/403/429/500/503 · timeout · lỗi kết nối · JSON hỏng · sai lược đồ · hết ngân sách · ngoại lệ chưa phân loại. 16 FIXED |
| `HUMAN_REVIEW_GATE_PROOF.json` | như trên | 12 hàng: PENDING mặc định · bản giả hợp lệ ⇒ `SIMULATED_REVIEW`, không bao giờ PASS · 5 ràng buộc lệch ⇒ `STALE_REVIEW` · đầu ra model đổi sau khi duyệt ⇒ `STALE_REVIEW` · 3 bản sai khuôn ⇒ `INVALID_REVIEW`. 12 FIXED |
| `FAULT_INJECTIONS.json` | ghi từ log | 4/4 phép tiêm đỏ đúng test, 4/4 hoàn lại trùng từng byte |
| `regression/` | `prove_photo_live_runner.py` trên runner đã sửa | chạy lại bằng chứng ngân sách + redaction: 12 lượt logic → gửi 11 · chặn 1 · transport giả 11 · mạng 0; 3 lỗi provider × 5 secret giả ⇒ 0 lần lộ. `regression/DRY_RUN_GROUND_TRUTH.json` = bản ground truth dry-run cũ THÊM đúng `expected_rejection_codes` cho C03 — bản cũ trong `live-runner-hardening/` giữ nguyên |
| `C01_GROUND_TRUTH_TEMPLATE.json` | viết tay | khuôn ground truth cho lượt ảnh thật C01, người dùng điền TRƯỚC khi chạy |

Mỗi hàng bằng chứng mang `input` · `expected` · `actual_before` · `actual_after` ·
`test_name` · `runner_sha256` · `evidence_class = OFFLINE_TEST`, và phán quyết theo từng khoá:
`FIXED` (trước sai, sau đúng) · `GUARD_ALREADY_PRESENT` (trước đã đúng) · `NOT_FIXED`.

## Giả thuyết 4 — trả lời bằng số

Lỗi provider, timeout hay lược đồ có bị tính là từ chối an toàn không? **Không, ở `684420d`
đã có guard:** 11/11 ca (5 mã HTTP, timeout, kết nối, JSON hỏng, sai lược đồ, hết ngân sách,
ngoại lệ) đều không được tính là từ chối an toàn. Cái thiếu là **phân biệt**: mọi thứ khác PASS
đều gộp là FAIL. Nay có PASS · FAIL · ERROR · BLOCKED, và cả ba trạng thái sau đều chặn nghiệm thu.

## Sinh lại

```bash
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest \
  tests/test_photo_problem_acceptance_scorer.py --junitxml=<tuyệt đối>/AFTER_junit.xml
# lượt "trước" phải chạy khi runner trùng blob 684420d (git hash-object = git rev-parse 684420d:<đường dẫn>)
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/prove_photo_scorer_correction.py \
  --before-junit <tuyệt đối> --after-junit <tuyệt đối> --after-old-junit <tuyệt đối> --out-dir <thư mục mới>
```

Script từ chối ghi đè.
