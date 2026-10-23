# Xuất bản: quyết định còn chờ Owner

**Trạng thái: `REMOTE_SECURITY_BLOCKED`.** Không push. Không viết lại lịch sử. Agent không ghi `APPROVED_BY_USER`.

## 1. Đếm hiện tại

`docs/evaluation/geometry/runs/publication-safety-remediation/publication_exceptions.json`: **27/27 entry
`PENDING_OWNER_DECISION`** (17 `RAW_PYTHON_TRACEBACK_IN_LOG`, 10 `SYNTHETIC_TEST_VECTOR_OR_PLACEHOLDER`), 0 duyệt.

Gate sau merge và sau bản sửa A/B (log metadata-only ở `verification/publication-gate/`, tại `57138dbb`):

| chế độ | kết quả | vi phạm mới ngoài danh sách |
|---|---|---|
| `--head` | BLOCKED, 105 dòng, tất cả PENDING | 0 |
| `--range origin/main..HEAD` | BLOCKED, 5 dòng (`8a515fef`), PENDING | 0 |
| `--range main..HEAD` (9 commit của bản sửa A/B, tới `57138dbb`) | **PASS**: 24 blob, 9 message, 0 vi phạm | 0 |

## 2. Mâu thuẫn trong hồ sơ ngoại lệ đã nộp (đính chính, không sửa bản gốc)

Văn bản đề xuất cho AGENTS.md ở `HISTORICAL_TRACEBACK_EXCEPTION_PROPOSAL.md` §5 viết: *"blob đã tồn tại trong lịch sử
**trước 2026-10-23**"*. Blob chính của chính hồ sơ đó, `8a515fef`, được đưa vào lịch sử bởi `77f7aaf7` lúc
**2026-10-23 11:43:40 +0700**, tức **không** "trước 2026-10-23". Văn bản ấy, nếu được ký, sẽ không miễn cho blob mà
nó sinh ra để miễn. Mốc ngày còn mơ hồ múi giờ và mở cửa cho bất kỳ blob cũ nào chưa được kiểm kê.

Hồ sơ gốc là bằng chứng đã commit ⇒ giữ nguyên byte; đính chính ở đây (`EVIDENCE_INDEX`: `CORRECTED_BY`).

## 3. Văn bản thay thế đề xuất (chưa áp dụng)

Thay mốc ngày bằng **danh sách đóng chính xác**:

> - **Ngoại lệ kế thừa, danh sách đóng:** chỉ các entry của
>   `docs/evaluation/geometry/runs/publication-safety-remediation/publication_exceptions.json` mà Owner tự ghi
>   `owner_decision: "APPROVED_BY_USER"`; mỗi entry khớp chính xác (đường dẫn, blob SHA-1, SHA-256 nội dung, luật).
>   Không có tiêu chí ngày, không miễn theo tên file hay mẫu nội dung, không miễn commit message. Nội dung mới không
>   bao giờ được miễn. Thêm entry cần quyết định mới của Owner. Trước mỗi lần push:
>   `backend/scripts/check_publication_safety.py --head` và `--range origin/main..HEAD` exit 0.

Gate đã cài đúng ngữ nghĩa này (khoá theo bộ bốn, không có tham số ngày), nên đổi văn bản không cần đổi mã.

## 4. Owner cần làm

1. Quyết từng entry (27). Từ chối entry nào thì gate tiếp tục chặn blob đó.
2. Chọn văn bản §3 (hoặc diễn giải chính thức tương đương), do Owner ghi vào AGENTS.md.
3. Chép bản bảo toàn offline (`D:\AlgoSim-Offline-Archive\2026-10-23-traceback-remediation\`) ra thiết bị độc lập; hiện cùng SSD.
4. GO push riêng, chỉ fast-forward.
