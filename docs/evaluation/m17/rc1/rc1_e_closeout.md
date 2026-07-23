# M17-RC1 §E — CLOSEOUT (đã đóng)

Range: **`e9ec370..fa9c21d`** · đóng tại HEAD **`fa9c21d`**

---

## 1. Số cuối

| | |
|---|---|
| Renderer riêng biệt (auto-discovery từ registry) | **6** |
| Fixture | **25** (canonical · boundary · stress · 2 refusal) |
| Ảnh | **134** — desktop **67** / hẹp **67** |
| Cảnh báo assertion | **0 / 134** |
| REAL_VISUAL | **5** |
| PARTIAL_VISUAL | **1** |
| BROKEN_VISUAL | **0** |
| VISUAL_COVERAGE_GAP | **0** |
| Lỗi tìm / sửa / còn chặn | **4 / 3 / 0** |
| pytest | **891** (2 skip, 1 deselect) |
| vitest | **536** / **43** file |
| production build | sạch |
| catalog conformance | 19 target / **0** vi phạm |
| tracked tree | sạch |

### Trạng thái từng renderer

| Renderer | Trạng thái |
|---|---|
| `algorithm` | REAL_VISUAL |
| `binary` | REAL_VISUAL |
| `logic` | REAL_VISUAL |
| `network` | REAL_VISUAL |
| `tree` | REAL_VISUAL |
| `generic` | **PARTIAL_VISUAL** |

---

## 2. VIS-003 — `NOT_A_DEFECT_MEASUREMENT_ARTEFACT`

Giữ trong ledger, **không xoá**. Sáu điểm ghi nhận:

1. Audit runner **trước đây** đổi viewport **sau khi** trang đã dựng ở 1440px.
2. Vì vậy ảnh 768px **không phản ánh** layout responsive thật.
3. Chẩn đoán DOM chứng minh **không** page overflow, **không** clipping,
   **không** rigid min-width — trên cả 4 route dùng chung app shell × 2
   viewport, kết quả *before* và *after* giống hệt nhau
   (`scrollWidth 758 ≤ clientWidth 768`).
4. **Production CSS/layout không cần sửa** — không đổi một dòng nào.
5. Runner đã sửa thành **viewport-before-navigation + reload**.
6. Đã **bổ sung assertion responsive**: `page_overflow_x`, `clipped_content`
   (bị tổ tiên `overflow:hidden` cắt), `rigid_min_width`, `key_elements`.

> **Vì sao giữ lại:** đây là cảnh báo về chính phương pháp audit — ảnh chụp có
> thể phản ánh sai hiện thực nếu quy trình đo sai. Tôi đã báo VIS-003 là lỗi
> chặn và suýt sửa app shell theo một lỗi không tồn tại.

---

## 3. Provenance runtime

- Runtime parity **đã được xác minh ở baseline trước checkpoint**: commit
  `e9ec370` → **PASS**
  (`sha=b977a94923eb` · cache=17 · family=9 · target=19 · hash=`0adecafd0d49`).
- **Docker không khả dụng** khi đóng RC1-E ⇒ **không chạy lại** runtime doctor.
- `backend/app` và catalog **không đổi một dòng** trong range RC1-E
  (`git diff e9ec370..fa9c21d -- backend/app` rỗng); toàn bộ thay đổi là
  frontend + script đo + artifact.
- **Không** ghi kết quả runtime cũ thành một lần xác minh **mới** tại HEAD
  `fa9c21d`. Trường máy-đọc `runtime_provenance.revalidated_at_this_head` =
  `false` trong `visual_stress_review.json`.

---

## 4. Generic renderer

- Visual status: **PARTIAL_VISUAL**.
- Engine authenticity: **giữ PARTIAL** — audit thị giác không nâng hạng.
- Hạn chế: rất nhiều nhãn **cực dài** có thể vẫn chật khi vượt số hàng so le
  nhãn (hiện 3 hàng).
- Hạn chế này **không che state**, **không gây hiểu sai**, **không blocking**.

---

## 5. Bốn mục ledger

| ID | Renderer | Mức | Trạng thái |
|---|---|---|---|
| VIS-001 | network | BROKEN_VISUAL | **FIXED** — nhãn dài đè nút → vẽ dưới nút |
| VIS-002 | generic | BROKEN_VISUAL | **FIXED** — nhãn chồng + badge `GENERIC` |
| VIS-003 | *(dùng chung)* | NOT_A_DEFECT | **MEASUREMENT_ARTEFACT** |
| VIS-004 | generic | PARTIAL_VISUAL | **FIXED_PARTIAL** — so le 3 hàng |

Mọi bản sửa **chỉ chạm lớp trình bày**: không sửa engine state, trace, executor
hay candidate spec. `state.pos` của generic không đụng tới.

**Guard test** (`frontend/src/simulations/visual-guards.test.tsx`, 4 test) đã
**fault-inject**: hoàn tác bản sửa VIS-001 → test đỏ; khôi phục → xanh.

---

## 6. Backlog thị giác còn lại (không chặn)

- Nhãn cực dài trong `generic` khi số đối tượng vượt số hàng so le.
- Bố cục đồ thị tròn làm cạnh cắt chéo nhiều ở đồ thị dày — đọc được nhưng
  chưa tối ưu.

---

## 7. Ranh giới claim

- 134 ảnh chụp trên **Chrome thật** qua CDP; SSR **không** được dùng làm bằng
  chứng thị giác.
- Phán quyết REAL/PARTIAL/BROKEN do **người xem toàn bộ PNG** chấm; assertion
  tự động chỉ là bằng chứng hỗ trợ và **không tự nâng** lên REAL_VISUAL.
- Hai viewport (1440 · 768) không phải toàn bộ dải thiết bị thực tế.
- Audit này đánh giá **trình bày**; nó **không** thay đổi và **không** nâng
  engine authenticity của bất kỳ target nào.

**Wave 2B chưa mở. Không family mới trong checkpoint này.**
