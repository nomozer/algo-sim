# W4B-4 — PHÁN QUYẾT SOÁT TRẢI NGHIỆM

## `ALGOSIM_EXPERIENCE_AUDIT_COMPLETE`

Phạm vi: **23/23 target** trong danh mục, soát bằng **hành vi thật** chứ không
bằng metadata. Câu hỏi nghiệm thu, hỏi cho từng target:

> *"Bỏ hết Play / Next / đúng-sai đi, học sinh còn thao tác được lên mô hình và
> quan sát hệ quả tất định không?"*

---

## Kết quả

| | |
|---|---|
| Thao tác trực tiếp được | **20 / 23** |
| Cố ý giữ dạng trace, có lý do CƠ CHẾ khoá bằng test | **3 / 23** |
| Không phân loại được / bỏ sót | **0** |

Diễn biến đo được từng bước (`probe.json` qua lịch sử git):
`211628c` **15** → `a49f951` **16** → `27c93d2` **20** → nay **20**.

Ba target giữ trace và lý do (`KEEP_TRACE`, `experience-audit-w4b4a.test.ts`):

- **`algorithm.bounded_control_flow`** — cơ chế LÀ luồng điều khiển theo thời
  gian. Thứ đáng đổi là chính chương trình; cho sửa chương trình thì đây thành
  một IDE, vượt ranh giới "không thực thi mã tuỳ ý" của đề tài.
- **`algorithm.scan`** — quét một lượt là bài học VỀ TRÌNH TỰ. Tham số duy nhất
  đáng đổi là dãy đầu vào, và dựng một trình soạn dãy tổng quát chỉ để tăng số
  tương tác là thứ đã bị cấm tường minh.
- **`network.protocol_encapsulation`** — đóng gói qua từng tầng là biến đổi tuần
  tự có hướng; cho kéo thả các lớp sẽ dựng ra trạng thái giao thức không tồn tại.

Đây là **quyết định**, không phải chỗ trống: guard hai chiều bắt cả trường hợp
thiếu lý do lẫn trường hợp lý do còn sót sau khi target đã có tương tác, và từ
chối lý do nói "chưa kịp" / "TODO".

---

## Bằng chứng

| Loại | Nơi |
|---|---|
| Ma trận 23 dòng (SINH từ phép đo) | `matrix-after.md` |
| Phép đo hành vi toàn danh mục | `probe.json` + `experience-audit-w4b4a.test.ts` |
| Nghiệm thu Chrome, 4 bề rộng | `../w4b4c-experience/acceptance.json` |
| Đo bố cục mạch logic, 4 bề rộng | `../w4b4d-composition/dag.json` |
| Ảnh trước/sau | `../w4b4d-composition/*.png` |
| Nhật ký tiêm lỗi | `../w4b4d-composition/fault-log.md` |

Cổng cuối: pytest **1148** (2 skip, 1 deselect) · vitest **1281 / 93 file** ·
`npm run build` sạch · `catalog_runtime_matrix` **23 target · conformance 0 ·
ownership 0 · parity 0 · PASS** · nghiệm thu Chrome **6 target × 4 viewport
SẠCH**.

---

## Ba điều phép đo tự bắt được mình

Ghi lại vì chúng đáng tin hơn con số 20/23:

1. **Bản đầu của phép đo ĐOÁN tên action** và cho ba âm tính giả — một phép đo
   sai im lặng đọc y hệt một phép đo sạch. Mồi hai chiều nay nằm trong file.
2. **`count_if`/`sum_if` là dương tính giả suốt từ baseline**: chúng "thao tác
   được" bằng `whatif_swap` mà chính sách của chúng TẮT, vì phép đo đọc cờ khai
   báo `!!mod.explore` thay vì CỬA thật `explore.entry()`. Nay đọc cửa — và hai
   bài có tương tác thật (đổi chính điều kiện).
3. **Đợt tiêm lỗi đầu tiên vô giá trị**: runner làm cả 92 file fail lúc collect
   nên mọi mutation đều "ĐỎ" vì lý do sai. Lượt đối chứng không tiêm gì cũng đỏ
   y hệt — đó là thứ lộ ra vấn đề. Chạy lại bằng bash với baseline xanh đã xác
   nhận: 8 bị bắt, **2 lỗ thật** (kẹp-thay-vì-từ-chối; sàn đo nuốt mất một
   target biến mất khỏi catalog), 1 mutant tương đương có ghi lại.

---

## KHÔNG claim

- **Chưa đo trên người học.** Toàn bộ phán quyết này là về CƠ CHẾ và BỀ MẶT, không
  phải về việc học sinh có học được hơn không.
- 3 target giữ trace là quyết định có lý do, **không phải "đã xong"** — điều kiện
  tái xét ghi ngay trong `KEEP_TRACE`.
- Nhãn lệch-đề chỉ nói **CÓ** lệch, không nói lệch ở đâu.
- `web` dời khối bằng hai nút mũi tên (bàn phím tới được), **chưa có kéo-thả**.
- 7 target vẫn `ENGINE_CONTRACT_MISSING` (nợ từ W4B-2R, ngoài phạm vi soát này).
