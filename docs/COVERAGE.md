# COVERAGE.md — Phủ chương trình, phủ năng lực, và GIÁ TRỊ SƯ PHẠM

Kết quả hai audit trước M8: **PRE-M8 Coverage Audit** và **PRE-M8 Pedagogical
Simulation Value Audit**. Đây là nơi ghi **được phép tuyên bố gì** và **cấm tuyên
bố gì** về độ phủ của AlgoSim.

Cập nhật khi phạm vi phủ / bộ đề / chính sách sư phạm đổi. Khi tài liệu này lệch
với code/test → **CODE/TEST THẮNG** (theo `ARCHITECTURE_MAP.md §0`).

---

## 1. Độ phủ và tuyên bố hiện hành — đọc trước khi viết một con số độ phủ

Từ đổi đề 2026-08-24 (`STATUS_LEDGER §0-2026-08-24`), độ phủ của sản phẩm và câu được/không được viết nằm ở:

- [`research/GEOMETRY_CURRICULUM_COVERAGE.md`](research/GEOMETRY_CURRICULUM_COVERAGE.md) — độ phủ chương
  trình hình học không gian THPT (`backend/tests/geometry/test_curriculum_coverage.py` đọc);
- [`research/CLAIM_EVIDENCE_MAP.md`](research/CLAIM_EVIDENCE_MAP.md) §3 — **câu không được viết**, và mỗi
  tuyên bố với bằng chứng, mức và giới hạn của nó;
- năng lực sản phẩm: `backend/app/simulation/product_capability.py`; họ hình:
  `docs/evaluation/geometry/missing-family-roadmap-refresh/CAPABILITY_MATRIX.json`.

§2 (nguyên tắc sư phạm) và §5 (mức L1–L4) dưới đây giữ **nguyên văn** vì mã và tài liệu trích chúng theo số
mục (§2.6, §2.7, §5). Phần của giai đoạn Tin học — nguồn SGK Tin học và tuyên bố cấm của nó (§1, §1b cũ),
ma trận giá trị theo chủ đề (§3), phủ năng lực theo miền (§4, §4b), `practice_activity`, chủ đề không mô
phỏng, 2D/3D, bộ đề, flagship, tái sử dụng liên miền và đóng băng (§6–§12) — chép nguyên văn ở
[`legacy/COVERAGE_INFORMATICS_ERA.md`](legacy/COVERAGE_INFORMATICS_ERA.md) (2026-10-05, `cuboid-final-review`).

---

## 2. Nguyên tắc sư phạm (chốt — ràng buộc mọi milestone sau)

> **Chỉ mô phỏng khi có: (a) CƠ CHẾ ẨN, (b) trạng thái biến thiên theo thời gian
> hoặc theo hành động, (c) lợi thế RÕ RÀNG so với text/ảnh/video/quiz.**
> Nếu học sinh đã thấy hết mọi thứ trong một hình tĩnh → mô phỏng chỉ thêm
> chuyển động, không thêm hiểu biết.

Hệ quả bắt buộc:

1. **Một chủ đề CÓ trong chương trình KHÔNG phải là lý do để mô phỏng nó.**
2. **KHÔNG** thêm module riêng cho mỗi bài học (ưu tiên: specialized có sẵn →
   generic DSL → mở rộng năng lực TÁI SỬ DỤNG được → `capability_gap`).
3. **KHÔNG** gọi một sơ đồ tĩnh là "executable simulation" (thực thi bằng code:
   `semantic._check_system_flow`, `moving=False` → cấm có process diễn biến).
4. **2D là mặc định.** 3D chỉ khi chiều sâu/phân tầng/không gian mang NGHĨA.
5. Dạng mạnh nhất là **phủ định dự đoán**: học sinh dự đoán → làm sai → engine
   tất định cho thấy hậu quả (`what-if branch`). Hiện **chỉ domain algorithm** có.
6. **(M9-S1) Mọi tương tác của người học phải CHẠM VÀO CƠ CHẾ ẨN và sinh hệ quả
   tất định.** Tương tác trang trí / gần-như-không-đổi-gì **không được admit** —
   phải gỡ, đóng khung (framed/challenge), hoặc ẩn. Tiền lệ thực thi:
   `frontend/.../algorithm/interaction-policy.ts` (free/framed/challenge/hidden,
   kèm `rationale` tự khai; khoá bằng `interaction-policy.test.ts`). Câu hỏi
   dự đoán phải nhắm ĐÚNG cơ chế của từng bài và KHÔNG được lộ đáp án sớm
   (narration bước quyết định là câu hỏi — `decision.test.ts`).
7. **(M9-UX2) Kiến trúc được phép TỔNG QUÁT, nhưng danh mục CÔNG KHAI hướng
   học sinh khoanh CÓ CHỦ ĐÍCH trong các trải nghiệm Tin học THPT đại diện.**
   Ví dụ liên miền (vd tam giác) có thể ở lại làm **fixture nội bộ** hoặc
   **case đánh giá** mà không được quảng bá cho học sinh. Hệ quả hai chiều:
   (a) gỡ một mẫu khỏi danh mục công khai **không** đồng nghĩa gỡ năng lực
   tái sử dụng đã nuôi nó; (b) phân loại bằng **metadata tường minh**
   (`OfflineSample.visibility`), cấm lọc theo chuỗi tiêu đề. Lịch sử học mở
   lại bằng envelope đã validate nên không phụ thuộc danh mục. Thực thi:
   `data/offline-catalog.ts` (`publicCatalog`); khoá bằng `catalog.test.tsx`.

---

## 3–4. (giai đoạn Tin học)

Ma trận giá trị theo chủ đề (§3) và phủ năng lực theo miền (§4, §4b): nguyên văn ở [`legacy/COVERAGE_INFORMATICS_ERA.md`](legacy/COVERAGE_INFORMATICS_ERA.md).

---

## 5. Mức độ phức tạp (L1–L4) và Result mode

- **L1 atomic** (một cổng AND, tìm max) · **L2 composed** (gói tin, tổng trọng số,
  dựng web) · **L3 multi-stage** (dựng cảnh RỒI chạy quá trình trên cảnh đó) ·
  **L4 boundary** (vượt năng lực → phải từ chối).

**Result mode** (`EvalItem.result_mode`):

| Mode | Nghĩa | Trạng thái |
|---|---|---|
| `executable_simulation` | có state/process/timeline tất định | ✅ |
| `interactive_visualization` | cấu trúc/quan hệ có nghĩa + khám phá được | ✅ |
| `practice_activity` | học sinh tự dựng/thao tác, engine kiểm được | ⚠️ **PARTIAL — chưa implement** |
| `unsupported` | năng lực chưa đủ → từ chối trung thực | ✅ |

> **Baseline lịch sử (30 case) gần như toàn L1/L2 và KHÔNG có case sắp xếp.** Đó
> chính là lý do có pool mới — không phải vì baseline sai.

---

## 6–12. (giai đoạn Tin học)

`practice_activity`, chủ đề không mô phỏng, Dijkstra, 2D/3D, bộ đề, flagship, tái sử dụng liên miền, ngân sách object, đóng băng: nguyên văn ở [`legacy/COVERAGE_INFORMATICS_ERA.md`](legacy/COVERAGE_INFORMATICS_ERA.md).
