# `live-runner-hardening/` — bằng chứng offline cho runner nghiệm thu ảnh đề bài

**0 request mạng · 0 lượt gọi provider thật.** Thư mục này chứng nhận **bộ đo**
(`backend/scripts/run_photo_problem_live.py`) trước khi ai đó tiêu quota thật. Nó
**không** nói gì về việc Gemini đọc được một ảnh chụp thật: `REAL_PROVIDER_EVIDENCE`
vẫn là `NOT_ESTABLISHED`. Báo cáo wave: `docs/PHOTO_PROBLEM_LIVE_RUNNER_HARDENING.md`.

| tệp | sinh bởi | nói gì |
|---|---|---|
| `DRY_RUN_GROUND_TRUTH.json` | viết tay, đăng ký TRƯỚC | C01 = `c01` (đề p1), C02 = `c05` (đề p6), C03 = `c11` — ảnh **TỔNG HỢP**. Văn bản đối chiếu từng byte với `thesis-final-acceptance/CORPUS.json` |
| `HTTP_BUDGET_PROOF.json` | `prove_photo_live_runner.py` | 12 lượt logic dưới trần 11 ⇒ ATTEMPTED 12 · SENT 11 · BLOCKED 1 · transport giả 11 · mạng 0. Đường xấu nhất mà ba ca vẫn đạt dùng đúng 11, RETRIES 0; trần 10 chặn ảnh C03. Trần cũ 38 → 11, dẫn từ hằng số |
| `CER_PROOF.json` | như trên | 13 cặp CER biết trước đáp số, 13/13 khớp. 5 ca dữ kiện: sai nhãn và sai công thức nằm dưới ngưỡng CER 0,02 mà vẫn FAIL; mục thừa trung thành với đề vẫn PASS |
| `REDACTION_PROOF.json` | như trên | 3 lỗi provider (vision 403 · đọc đề 403 · tổng hợp `ConnectError` chép URL có `?key=`) chở 5 secret GIẢ: 0 lần lộ ở stdout, stderr và mọi artifact. Chỉ ghi băm của secret |
| `RUNNER_DRY_RUN.json` | như trên | `--dry-run --case all`: 3/3 PASS · 7 request tới transport giả · 0 mạng · 0 provider thật · không tệp ảnh nào trong thư mục ra |
| `FAULT_INJECTIONS.json` | ghi từ log | 6 phép bắt buộc + 2 phép thêm: 8/8 đỏ đúng test, 8/8 hoàn lại trùng từng byte |

JSON sinh máy mang `git_head`, `runner_sha256` và `MEASURING_CODE_DIRTY_VS_GIT_HEAD`
(rỗng = runner ở `git_head` đúng là runner đã đo).

⚠️ Bốn artifact hiện tại mang `git_head = c351d95` và danh sách ấy **khác rỗng**: runner
đã đo (`runner_sha256 = 599a1e47…`) là bản trong commit bằng chứng kế tiếp, sau bản sửa
chấm dữ kiện bịa — không phải bản ở `c351d95`. Xem `FAULT_INJECTIONS.json` → `phases`.

## Sinh lại

```bash
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
  scripts/prove_photo_live_runner.py --out-dir <thư mục mới có DRY_RUN_GROUND_TRUTH.json>
```

Script từ chối ghi đè bốn tệp đã có.

## Hai lỗi bộ đo, bắt được ở đây

1. Cổng HTTP từng đoán "lần thử lại" theo băm thân request. Lượt đầu của
   `HTTP_BUDGET_PROOF` ghi `RETRIES = 2` cho đường xấu nhất, dù `call_gemini` không
   thử lại lần nào: hai lượt SỬA của tổng hợp gửi thân y hệt nhau. Nay cổng đọc
   `ApiBudget.retry_requests`. Khoá `test_10`, phép tiêm F7.
2. Bộ chấm từng coi MỌI mục thừa là dữ kiện bịa. `transcribe.md` dặn vision chép
   mọi thứ VIẾT trong đề, nên một lượt đọc trung thành sẽ bị đánh trượt. Nay mục thừa
   chỉ là bịa khi mang một nhãn hay con số không có trong đề gốc. Khoá `test_15`,
   phép tiêm F8.

## Chạy thật — chưa làm, cần người

```bash
cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
  scripts/run_photo_problem_live.py --case C01 \
  --input-dir <tuyệt đối> --ground-truth <tuyệt đối> --output-dir <tuyệt đối, thư mục mới>
```

Cần `GEMINI_API_KEY` trong môi trường, một ảnh `C01.*` thật, và ground truth của
**chính ảnh ấy** viết TRƯỚC khi chạy. Không dùng `DRY_RUN_GROUND_TRUTH.json` cho lượt
thật. Không commit ảnh thật.
