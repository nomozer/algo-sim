# Hồ sơ đề nghị ngoại lệ lịch sử: traceback thô và vector test

**Trạng thái: `PENDING_OWNER_DECISION`.** Agent không ghi phê duyệt. Mỗi entry của
[`publication_exceptions.json`](publication_exceptions.json) chỉ có hiệu lực khi **Owner** tự đổi
`owner_decision` thành `APPROVED_BY_USER`.

## 1. Blob chính được đề nghị

| trường | giá trị |
|---|---|
| blob (SHA-1 Git) | `8a515fef0e1537c03f8abcc2dc533e88704f164f` |
| SHA-256 nội dung | `3f7586fbf91d8d9b8d059c635fdfb858d7ade4950b5337d66a06bf5afaa9cf69` (khớp `suite-receipts.json` của `backend-hybrid-contract-unification`) |
| kích thước | 39,965 B, 597 dòng |
| đường dẫn | `docs/evaluation/geometry/runs/backend-hybrid-contract-unification/verification/geometry-dir-first-run-before-fixes.log` |
| commit đưa vào | `77f7aaf7ae027e2ff7b6bc9f14aee38a785ce6fb` (2026-10-23 11:43 +0700, "preserve Session 1/2 untracked verification logs") |
| trên `origin/main` | **chưa** (`origin/main` = `43247c9e9375a3dbf2b5223324a58e6f932ca596`; range push 48 commit gồm `76c6795c`) |
| tip tree | **đã gỡ** ở `76c6795c37569aebcf41c0d22ffbe0d8268872d9` (commit tiến; lịch sử không đổi) |
| phạm vi xin | `HISTORY_ONLY`: chỉ cho phép blob này nằm trong lịch sử được push, không ở tip |

**Đọc tay toàn bộ 597 dòng** (không chỉ regex): tiến trình pytest; 16 báo cáo test đỏ kèm trích mã test và giá trị assert;
địa chỉ bộ nhớ đối tượng; SHA git; một timestamp; khối traceback thô của cảnh báo `PytestUnhandledThreadExceptionWarning`
(`subprocess._readerthread` giải mã cp1252), các khung đều là thư viện chuẩn Python 3.12. Dữ liệu có thể coi là nhạy cảm:
**tên tài khoản Windows và bố cục thư mục local** (`C:\Users\<tài khoản>\AppData\Local\Programs\Python\Python312\…`,
`D:\Documents\projects\algo-sim\…`, `.superpowers\worktrees\hybrid-backend-s2`). Không thấy secret, token, email,
hostname, dữ liệu người học hay output mô hình. Quét regex (`check_publication_safety.py`) là giới hạn dưới, không phải
chứng minh "không có gì nhạy cảm"; kết luận ở đây dựa trên việc đọc tay của agent, Owner nên tự xem lại.

## 2. Vì sao giữ, không viết lại lịch sử

- Đây là **nền đỏ** của Session 2 (16 test đỏ trước khi sửa). Phương pháp của kho đòi test có nền đỏ. Receipt
  `suite-receipts.json` trích SHA-256 và danh sách test đỏ của log này. Receipt vẫn ở tip; log thô thì không cần nữa vì
  receipt đã giữ phần thông tin (`"raw_log_committed": false` là thiết kế gốc).
- Viết lại lịch sử để xoá blob sẽ đổi SHA của **10 commit** (`77f7aaf7` cùng 9 hậu duệ, gồm product `e090af1c`,
  candidate `9f06ed2b`, T3 target `478d50e8`). Hệ quả: 38 file tài liệu và receipt trích SHA cũ gãy; phải freeze lại
  candidate, chạy lại Full T3 và browser acceptance. AGENTS §2 cấm rewrite; CLAUDE.md §2 cấm viết lại commit mà evidence đã tham chiếu.
- Và viết lại **không làm remote sạch**: `origin/main` đã có 16 log cùng loại (§3).

## 3. Entry kế thừa đã công khai (cùng file miễn trừ)

Gate quét tip tree bắt thêm 26 blob, **tất cả đã có trên `origin/main`** (cột `already_public_on_origin_main`):

| loại | số | ghi chú |
|---|---|---|
| `RAW_PYTHON_TRACEBACK_IN_LOG` | 16 | log pre-freeze/attempt của các run cũ; cả 16 được thêm sau khi luật §4 ra đời (`34c36872`, 2026-09-22). Được tham chiếu bằng link trong report đã đóng băng và MANIFEST có hash, nên gỡ khỏi tip sẽ phải sửa báo cáo bất biến hoặc làm docs gate đỏ |
| `SYNTHETIC_TEST_VECTOR_OR_PLACEHOLDER` | 10 | `backend/.env.example` (placeholder "dán key vào đây"); test của chính các bộ quét secret (`KEY_GIA`, chuỗi `…Fake…Test…`, một chuỗi luân phiên `A9a9…` không ngẫu nhiên); `Bearer abcd…` giả; mật khẩu fixture của test auth. Đã kiểm hình dạng chuỗi, không in giá trị |

Owner có thể duyệt riêng từng entry. Entry nào bị từ chối thì gate tiếp tục chặn, cho đến khi blob đó được xử lý.

## 4. Phạm vi ngoại lệ

- **Chỉ nội dung kế thừa**: đúng bộ (đường dẫn, blob SHA-1, SHA-256, luật) đã liệt kê. Gate khoá điều này bằng test:
  sửa một byte, chép sang đường dẫn khác, hay một luật khác thì không còn được miễn.
- **Không áp dụng cho nội dung mới**: blob mới trong range push luôn bị chặn, trừ khi có entry mới do Owner duyệt.
- Không miễn cho commit message. Không miễn theo tên file hay theo mẫu nội dung.

## 5. Chính sách AGENTS.md cần sửa (đề xuất văn bản, chưa áp dụng)

AGENTS.md §4 hiện ghi: *"Không lưu API key, token bí mật, traceback thô hoặc model output raw vào tài liệu hay git tree."*
Đề xuất thêm ngay sau dòng đó:

> - **Ngoại lệ kế thừa có danh sách đóng:** blob đã tồn tại trong lịch sử trước 2026-10-23 và được Owner ghi
>   `APPROVED_BY_USER` trong `docs/evaluation/geometry/runs/publication-safety-remediation/publication_exceptions.json`
>   (khớp chính xác đường dẫn, blob, SHA-256, luật) được phép nằm trong lịch sử, và nếu là bằng chứng còn tham chiếu thì
>   cả ở tip. Nội dung mới không bao giờ được miễn. Trước mỗi lần push:
>   `backend/scripts/check_publication_safety.py --head` và `--range origin/main..HEAD` phải exit 0.
> - **Định nghĩa "traceback thô":** khối ngoại lệ Python (dòng mở đầu và các dòng khung `File "…", line N`).
>   Báo cáo assert của pytest (dòng `E   …`, `path:line: AssertionError`) là chẩn đoán test, không phải traceback thô.
>   Log mới vẫn nên đi qua cơ chế giữ-local của `run_check.py`.

Nếu Owner không muốn sửa văn bản, có thể ghi một **diễn giải chính thức** cùng nội dung ở `docs/RULES.md` hoặc trong
quyết định của run này. Dù cách nào thì phải là Owner ghi.

## 6. Rủi ro khi push lịch sử còn chứa blob

1. Lộ tên tài khoản Windows và bố cục thư mục. Mức tăng thêm gần bằng 0: hơn 400 lượt cùng loại đã công khai.
2. Không thu hồi được sau khi push: fork, clone, cache và chỉ mục tìm kiếm có thể giữ lại.
3. Tạo tiền lệ. Gate với danh sách đóng là biện pháp giảm thiểu: không có miễn trừ chung.
4. Regex có thể sót dạng mã hoá secret lạ. Blob chính đã được đọc tay; 26 blob kế thừa chưa được đọc tay toàn văn
   (chúng đã công khai, nên rủi ro nếu có thì đã xảy ra rồi).

## 7. Nếu Owner từ chối

- **P-A (mặc định an toàn):** không push. Bản bảo toàn offline đã có (§8). Remote dừng ở `43247c9e`.
- **P-C:** tạo lịch sử xuất bản song song bằng `git filter-repo` chỉ trên `origin/main..main`. Bảo toàn bản gốc bằng tag
  local và bundle; lưu `commit-map` cũ→mới làm correction layer; freeze lại candidate, chạy lại Full T3 và browser
  acceptance trên HEAD mới. Không làm sạch 16 log đã công khai. Chi phí và rủi ro: xem
  `.superpowers/session5-go-main/REMOTE_PUBLICATION_REMEDIATION_PROPOSAL.md` §5.
- Từ chối riêng các entry kế thừa: cần một chiến dịch correction-layer riêng để thay log cũ ở tip (đụng report bất biến).

## 8. Bản bảo toàn offline

`D:\AlgoSim-Offline-Archive\2026-10-23-traceback-remediation\` (ngoài repo, ngoài OneDrive, file read-only):

| file | SHA-256 |
|---|---|
| `algo-sim-origin-main..main-b4ac5e87.bundle` (1,723,782 B; ref `main`, `research/hybrid-session5-offline-consumer` = `b4ac5e87`; prerequisite `43247c9e`; `git bundle verify` OK) | `f615dc8e692c3667e55afae34a07a25d026523c02765ecdf62b59a7b5c935725` |
| `blob-8a515fef0e1537c03f8abcc2dc533e88704f164f.log` | `3f7586fbf91d8d9b8d059c635fdfb858d7ade4950b5337d66a06bf5afaa9cf69` |

**Đây không phải backup chống hỏng ổ.** Máy chỉ có một SSD vật lý (NVMe Samsung 512 GB, C: và D: cùng đĩa 0). Muốn chống
hỏng ổ, Owner chép thư mục này ra thiết bị độc lập không công khai. Bundle chứa traceback, nên không được tải lên dịch vụ công khai.
