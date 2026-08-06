# DECISION_GATE — W4B-0 tại `267aca5`

## A. Câu trả lời cho 15 câu hỏi của decision gate

| # | Câu hỏi | Trả lời |
|---|---|---|
| 1 | Bảy thư mục audit gồm những artifact nào? | 767 ảnh · 17 tài liệu Markdown · 23 tệp quan sát có cấu trúc · 43,5 MB. Chi tiết ở `AUDIT_ARTIFACT_MANIFEST.md` |
| 2 | Bao nhiêu artifact đã được bảo toàn trong Git? | **Toàn bộ.** Commit `267aca5`, 808 file. Không file nào bị loại |
| 3 | Bao nhiêu kết luận cũ vẫn đúng? | **4/9** đo được vẫn đúng nguyên (`STILL_PRESENT`) |
| 4 | Bao nhiêu kết luận đã được giải quyết? | **4/9** `RESOLVED` — cộng thêm `SA-5` (lỗ `learning_objective`) |
| 5 | Bao nhiêu kết luận chỉ cải thiện một phần? | **1** — `network.graph_traversal` |
| 6 | Target nào có bằng chứng trước–sau rõ nhất? | `tree.traversal` — ngăn xếp từ "dòng chữ" thành `.frontier-stack` 2 ô kèm giải thích LIFO |
| 7 | Có renderer nào vẫn lệch engine state? | **Không.** 9/9 ca không phát hiện lệch |
| 8 | Scan/search/sorting hiện có learner action nào? | scan: hai nút cơ chế · search: hành động không gian + chi phí · sorting: `compare-pair`/`select-candidate`/`shift-or-stop`. **Trừ `algorithm.scan`** — xem `EG-1` |
| 9 | Có vấn đề sư phạm nào thật sự mới không? | **Không có vấn đề mới.** Có một vấn đề bị **mô tả sai** trước đây — xem `CM-1` |
| 10 | Nút thắt hiện tại là interaction hay curriculum metadata? | **Không phải cả hai như đã hiểu.** Metadata `learning_objective` đã đủ 100/100. Nút thắt thật là **độ phủ eval theo target** (3 target không có ca nào) và **trạng thái cạnh trong đồ thị/mạng** |
| 11 | Ba family thiếu `learning_objective` chính xác ở đâu? | **Không còn thiếu.** 0/100 item thiếu. Kết luận cũ (30/113 thiếu, baseline `887ec10`) đã hết đúng |
| 12 | Patch metadata tối thiểu cần bao nhiêu file? | 1–2 file trong `backend/app/evaluation/datasets/` để thêm ca cho 3 target chưa phủ |
| 13 | Có cần chạy W4B-1 đầy đủ nữa không? | **Không.** 5/9 vấn đề của ma trận gốc đã đóng; 4 vấn đề còn lại đã được định vị chính xác tới file. Một lượt audit 22 target nữa sẽ đo lại phần lớn thứ vừa đo |
| 14 | Phần nào của W4A Tier A đã được hấp thụ? | `CONTRACT_RECHECK` (catalog matrix 22/11 PASS) · `ENGINE_REPLAY` (924 vitest + 1129 pytest) · `RUNTIME_MATRIX_EVIDENCE` (visual-mode: đúng 2 target khai 3D) · commitment-surface invariant (test khoá từ W3B). **Chưa** hấp thụ: `FROZEN_PIN_COMPARISON` cho artifact LLM cũ, và toàn bộ inventory bằng chứng LLM |
| 15 | Bước triển khai tiếp theo có giá trị cao nhất là gì? | Xem §B |

## B. Tối đa hai việc tiếp theo

### Việc 1 — `targeted correctness/renderer fix`: trạng thái cạnh cho đồ thị và mạng

**Vì sao đứng đầu.** `MV-1` và `MV-2` là hai biểu hiện của **một** thiếu sót:
cạnh không mang trạng thái. Với `graph_traversal`, đường đi chính là thứ thuật
toán đang quyết định — hàng đợi đã vẽ rồi mà cạnh vẫn phẳng thì học sinh thấy
node đổi màu nhưng không thấy *đi từ đâu tới đâu*. Với `packet_routing`, "đoạn đã
đi vs còn lại" là chính nội dung bài. Cả hai đã tồn tại từ `cc449d5` và không
commit nào chạm tới.

- Target: `network.graph_traversal` · `network.packet_routing`
- Primitive dùng chung: trạng thái cạnh (đã đi · đang đi · chưa xét) + chú giải
- Nghiệm thu: đếm cạnh mang lớp trạng thái ≠ 0; chú giải có mục cho từng trạng
  thái; đối chiếu cạnh được nhấn với `events` của bước hiện tại
- Ước lượng: 2–3 file production, 1 file test
- Rủi ro phạm vi: `packet_routing` có 3D — mọi thay đổi phải giữ 2D/3D cùng đọc
  một state

### Việc 2 — `learning_objective metadata patch` (đúng hình dạng thật)

**Không phải** thêm trường còn thiếu (không còn thiếu), mà **thêm ca đánh giá cho
3 target chưa được phủ**: `algorithm.selection_sort`, `binary.base_conversion`,
`network.graph_traversal`.

- Vì sao đáng làm: `live.py` chấm theo dataset. Target không có ca thì **không
  bao giờ được đánh giá live** — kể cả khi Tier B chạy đủ ngân sách
- Ước lượng: 1–2 file trong `backend/app/evaluation/datasets/`, mỗi target 1–2 ca
- Ràng buộc: `datasets/__init__.py` đã có validator bắt `learning_objective` ≥ 10
  ký tự, nên ca mới không thể thiếu trường đó
- Lợi ích kép: `network.graph_traversal` nằm ở **cả hai** việc, nên sửa renderer
  xong có ngay ca đánh giá đi kèm

**Không chọn:** `small verified literature review` (chưa chặn việc gì) ·
`LLM Tier A remainder` (nên chạy sau khi 3 target trên có ca, nếu không sẽ đo một
dataset đang khuyết) · `learner pilot preparation` (cần hai việc trên xong trước).

## C. Bằng chứng 0 production-AI call

| Mục | Kết quả |
|---|---|
| `GEMINI_API_KEY` | **không đặt** trong mọi tiến trình của lượt này |
| `ALLOW_LIVE_AI` | **không đặt** |
| production API attempted | **0** |
| production API completed | **0** |

Không tự khai — có **guard quan sát được**. Chạy đúng đường live mà không opt-in:

```
$ env -u GEMINI_API_KEY -u ALLOW_LIVE_AI python -m app.evaluation.live \
      --dataset m16_catalog --suite smoke --max-cases 1 --max-api-calls 1

TỪ CHỐI: live evaluation gọi Gemini THẬT (tốn quota).
Chạy lại với opt-in tường minh, ví dụ:
    ALLOW_LIVE_AI=1 python -m app.evaluation.live --suite smoke
exit 1
```

Mọi phần còn lại của lượt chạy qua `pytest`/`vitest` (guard offline ở biên mạng)
hoặc script chỉ đọc + Chrome trỏ vào `localhost:3000`.

## D. Giới hạn — điều lượt này KHÔNG kết luận

- **`LEARNER_IMPACT_NOT_EVALUATED` giữ nguyên.** Không có dữ liệu người học nào
  trong lượt này; `RESOLVED` chỉ nghĩa là dấu hiệu cơ chế có mặt và khớp state.
- **`CURRICULUM_SUPPORT_PARTIAL` giữ nguyên.** Việc 3 target chưa có ca đánh giá
  là một lý do cụ thể để nhãn này vẫn đúng.
- Delta chỉ đo **9/22 target**, một viewport, một checkpoint. Các dòng không đo
  giữ nguyên kết luận cũ, được ghi rõ ở §3 của ma trận delta.
- `EG-1` (`algorithm.scan`) và `EG-2` (tree: cạnh ↔ thuyết minh) là **chưa xác
  minh**, không phải "đã đạt".
