# Quyết định xử lý 97 finding publication toàn HEAD

**Trạng thái: `PUBLICATION_HEAD = BLOCKED_PENDING_OWNER_REVIEW`.** Agent không ghi `APPROVED_BY_USER`, không sửa
`publication_exceptions.json`, không đổi luật quét. Số liệu lấy từ
[`publication_pending_classification.json`](publication_pending_classification.json). Bảng đó do
[`tools/classify_publication_findings.py`](tools/classify_publication_findings.py) sinh ra bằng cách import chính gate
`backend/scripts/check_publication_safety.py`, nên số finding ở đây là số của gate. Không lưu dòng hay giá trị bị bắt.

## 1. Phân loại

| nhóm | blob | finding | luật | rủi ro | trên `origin/main` |
|---|---:|---:|---|---|---|
| Log kiểm thử có khung traceback Python thô (`.log`, `.txt` trong `docs/evaluation/geometry/runs/*/diagnostics|results|verification`) | 16 | 95 | `PY_TRACEBACK` | Thấp về bảo mật. **Riêng tư:** 15/16 log lộ tên tài khoản Windows và bố cục thư mục local | 16/16 |
| Placeholder `Bearer` giả trong test và trong một receipt quét secret | 2 | 2 | `BEARER_TOKEN` | Dương tính giả theo hình dạng: 24 ký tự, có dấu hiệu placeholder, không ngẫu nhiên | 2/2 |
| **Tổng** | **18** | **97** | | | **18/18** |

Kiểm chứng thêm:

- **Không có blob nào mới:** cả 18 cặp (đường dẫn, blob) đã nằm trong cây của report HEAD `44807b13b`. Tất cả có entry
  `PENDING_OWNER_DECISION` trong registry; không finding nào thiếu entry.
- **Phạm vi range:** gate range của run này (`44807b13b..HEAD`) PASS, 0 vi phạm.
- **Log lỗi thuộc loại gì:** các log là output pytest/evidence builder từ 2026-10-03 đến 10-16. Kiểu exception đọc được:
  `AttributeError`, `PermissionError`, `FileNotFoundError`, cùng các khung cảnh báo luồng. Không có secret theo regex.
  Regex là giới hạn dưới, nên chủ repo nên tự mở xem ít nhất một log.
- **Registry còn 9 entry `PENDING` không còn ở tip** (gồm `backend/.env.example` và các test vector đã gỡ). Chúng chỉ
  có ý nghĩa với lịch sử được push, không làm đỏ `--head`.

## 2. Đã giải quyết thực sự: 0/97

Không mục nào đóng được trong quyền của agent:

| cách | vì sao agent không làm |
|---|---|
| Ghi `APPROVED_BY_USER` | AGENTS.md: chỉ Owner ghi giá trị này |
| Xoá 16 log khỏi tip bằng commit tiến | Log là bằng chứng của các run đã đóng băng và có báo cáo/manifest trích hash. Gỡ đi sẽ làm gãy link (docs IA đỏ) hoặc buộc sửa báo cáo bất biến. Log đã công khai trên `origin/main`, nên gỡ khỏi tip cũng không thu hồi được |
| Che tên tài khoản trong log | Đổi byte của bằng chứng đã trích hash, tức là sửa receipt lịch sử |
| Viết lại lịch sử | Bị cấm (AGENTS §2) và không làm remote sạch |
| Nới luật `PY_TRACEBACK` hay `BEARER_TOKEN` | Mở rộng miễn trừ cho nội dung tương lai. Phạm vi hẹp nhất là duyệt đúng 18 cặp (đường dẫn, blob), không đổi luật |

## 3. Phương án cho Owner

| phương án | tác động | khuyến nghị |
|---|---|---|
| **A. Duyệt đúng 18 entry** (đường dẫn + blob + SHA-256 + luật) | Gate HEAD PASS; nội dung mới hay byte đổi vẫn bị chặn; lịch sử nguyên vẹn | **Khuyến nghị** cho 2 placeholder `Bearer` và cho log nào Owner chấp nhận việc lộ tên tài khoản |
| B. Từ chối các log lộ tên tài khoản, rồi gỡ chúng khỏi tip | Cần quyết định kèm theo về link gãy trong báo cáo đóng băng (lớp đính chính mới, không sửa bản gốc). Không thu hồi được bản đã public | Chỉ chọn nếu Owner coi tên tài khoản là dữ liệu cá nhân cần hạn chế lan rộng thêm |
| C. Giữ chặn | Repo không đủ điều kiện công bố; test sản phẩm vẫn chạy được | Trạng thái mặc định hiện tại |

Ghi chú quy trình (từ phản hồi trước của Owner): phê duyệt nên bằng một lệnh do Owner tự chạy, khoá theo blob SHA,
thay vì sửa JSON bằng tay. Agent không chạy lệnh đó. Danh sách blob cần duyệt nằm ở `blobs` trong
[`publication_pending_classification.json`](publication_pending_classification.json).

## 4. Hệ quả cho các gate

- `PUBLICATION_RANGE`: PASS (range của run này).
- `PUBLICATION_HEAD`: `BLOCKED_PENDING_OWNER_REVIEW` (97 finding, 18 blob, 0 mới).
- `FULL_RELEASE_GATE`: `BLOCKED_GATES_REMAIN` cho đến khi Owner quyết định. Việc này không chặn đánh giá OCR nội bộ.
