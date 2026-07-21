# M17-VR1 — Tree Renderer Browser Visual Review

> **Phương pháp:** Chrome headless qua CDP (tái dùng hạ tầng
> `scripts/audit-layout.mjs`, KHÔNG thêm framework E2E), Vite dev server, nạp
> fixture qua module graph (`import('/src/state/store.ts')` → `loadEnvelope`)
> nên **không sửa production code để chụp**. Ảnh PNG được **xem trực tiếp**
> khi chấm — **SSR không được dùng làm bằng chứng**.
> Runner: `frontend/scripts/capture-tree-visual.mjs` · dữ liệu thô:
> `visual/captures.json` · máy-đọc: `tree_visual_review.json`.

**7 fixture · 19 ảnh · 4 variant đều có initial/mid/final.**

> **Bổ sung sau khi người dùng test thật:** fixture thứ 7
> (`vr1-realworld-vietnamese-labels`) dựng đúng đề *"Mạng lưới truyền tin trong
> khu bảo tồn"* — 11 trạm, **tên tiếng Việt dài**, sâu **5 tầng (chạm biên)**.
> Nó lộ ra lỗi **VR1-4** mà 6 fixture chữ-cái-đơn không thấy.

## Kết luận: `REAL_VISUAL` — sau 3 sửa lỗi bounded

| Fixture | Variant | Checklist | Status |
|---|---|---|---|
| preorder — cây cân bằng | preorder | 6/6 PASS | REAL_VISUAL |
| inorder — cây khuyết | inorder | 6/6 PASS | REAL_VISUAL |
| postorder — cây lệch trái | postorder | 6/6 PASS | REAL_VISUAL |
| level_order — nhiều tầng | level_order | 6/6 PASS | REAL_VISUAL |
| single-node — biên | preorder | 6/6 PASS | REAL_VISUAL |
| insufficient — thông điệp | — | 6/6 PASS | REAL_VISUAL |

Checklist: STRUCTURE_CLEAR · STATE_CLEAR · MECHANISM_CLEAR · PANEL_CORRECT ·
TERMINOLOGY_CORRECT · LAYOUT_PASS.

## Ba lỗi PHÁT HIỆN NHỜ REVIEW TRÌNH DUYỆT (unit + SSR test đều xanh khi đó)

### VR1-1 · `BROKEN_VISUAL` → FIXED — cạnh cây **vô hình**
`var(--border)` là **token ma** (tên thật `--hairline`). CSS/SVG bỏ im lặng
thuộc tính không hợp lệ → `stroke` thành `none` → **toàn bộ cạnh cây biến
mất**, nút chưa thăm mất viền (chỉ còn chữ trơ trọi). Học sinh **không thấy cây**.

**Lan sang Wave 1:** `network.graph_traversal` dùng cùng token ma → cạnh đồ thị
cũng vô hình. Live smoke W1/W2A không bắt được vì chỉ kiểm routing/spec.

- Sửa: `stroke` → `var(--ink-faint)`; nhãn cạnh → `var(--ink-muted)`; nhãn
  `T/P` → `trái/phải` (thuật ngữ học sinh).
- **Nguyên nhân gốc đã vá:** `tokens.test.ts` **chỉ quét `.css`** — token ma
  trong thuộc tính SVG/JSX lọt lưới. Nay quét cả `.tsx/.ts` (bỏ file test để
  guard không tự bắt chính nó).
- Bằng chứng: `visual/before/vr1-preorder-balanced-mid-BEFORE.png` →
  `visual/vr1-preorder-balanced-mid.png`.

### VR1-2 · `PARTIAL_VISUAL` → FIXED — panel **lộ đáp án** từ bước 0
Inspector hiện **toàn bộ thứ tự duyệt cuối** ngay khi mở, phá mục tiêu sư phạm
(học sinh mất cơ hội tự suy luận). Nay hiện dần "Đã thăm k/n: …", chỉ công bố
thứ tự đầy đủ **khi duyệt xong**. Khoá bằng test hiện-dần.

### VR1-3 · `PARTIAL_VISUAL` → FIXED — trang chủ rò **văn bản kỹ thuật**
`HomeView` có **bản sao riêng** của thông báo từ chối, đọc thẳng
`unsupported.reason` (kỹ thuật) và **bỏ qua `learner_reason`** mà M17 W0 gắn ở
biên API → học sinh có thể thấy chuỗi như `arbitrary_algorithm`. Ngoài ra tiêu
đề "NGOÀI DANH MỤC MÔ PHỎNG" **sai bản chất** với case thiếu dữ kiện (duyệt cây
**có** trong danh mục).

- Sửa: `HomeView` dùng chung `UnsupportedNotice` (**một nguồn**); thêm
  `failure_category` → tiêu đề **"CHƯA ĐỦ DỮ KIỆN"** + gợi ý "Bổ sung dữ liệu
  còn thiếu vào đề rồi gửi lại — dạng bài này hệ có mô phỏng."
- Khoá bằng 2 test tiêu đề theo `failure_category`.

## Đối chiếu checklist bắt buộc

- **A. Cấu trúc cây** — gốc viền `--primary` phân biệt rõ; cạnh có nhãn
  `trái`/`phải`; cây cân bằng / khuyết / lệch / 4 tầng đều **không chồng nút,
  nhãn hay cạnh**, không co/tràn khung.
- **B. Trạng thái duyệt** — current (cam) / đã thăm (xanh) / chưa thăm (trắng
  viền xám) phân biệt bằng **cả màu lẫn viền/nền** (không chỉ màu); active path
  cam đậm nét dày; Next/Prev đổi trạng thái đúng authoritative trace (state
  được ghi kèm từng ảnh trong `captures.json`).
- **C. Ý nghĩa duyệt** — preorder: gốc xanh trước, cây con trái xong mới sang
  phải; inorder: gốc **còn trắng** khi đang ở cây con trái; postorder: lá xanh
  trước, **gốc trắng tới cuối**; level_order: thăm theo tầng. Bốn variant phân
  biệt được **không cần đọc tiêu đề**.
- **D. Panel hỗ trợ** — DFS: "Ngăn xếp: …"; level_order: "Hàng đợi: …" (đúng
  variant, đồng bộ trace event); dải thứ tự **hiện dần**, chỉ chốt ở bước cuối;
  câu thuyết minh nêu **hành động/nguyên nhân** ("Đi xuống con PHẢI của A → C
  (đẩy vào ngăn xếp)", "Xong nhánh của B — lấy ra khỏi ngăn xếp"), không phải
  "đang ở nút X".
- **E. Thuật ngữ** — dùng *nút gốc, con trái, con phải, đã thăm, ngăn xếp, hàng
  đợi, thứ tự duyệt*. **Không** có Điểm/Đoạn nối/Vật di chuyển/GENERIC/JSON/
  schema/id nội bộ.
- **F. Bố cục & tiếp cận** — không tràn chữ, không chồng nhãn; trạng thái có
  **viền + nền + chữ** bổ trợ ngoài màu; nút điều khiển (Tự chạy / tiến / lùi /
  Đặt lại) rõ, có phím tắt; thông điệp thiếu dữ kiện nêu rõ **cách cung cấp cây**.

### VR1-4 · `BROKEN_VISUAL` → FIXED — nhãn tiếng Việt **tràn khỏi nút**

Phát hiện khi người dùng test đề thật. Sáu fixture đầu dùng nhãn **1 ký tự**
(A–G) nên vấn đề bị che. Đề đời thực có nhãn như **"Trăng Khuyết", "Sương
Mai"** vẽ **trong** vòng tròn `r=16` trên khung **cố định 460×300** → chữ tràn
ra ngoài, **đè nút và cạnh bên cạnh**, không đọc được.

Engine **vẫn đúng** (thứ tự preorder chuẩn) — chỉ phần trình bày hỏng.

- Sửa: khung vẽ **co giãn** (rộng theo số nút — 86px/làn; cao theo độ sâu —
  78px/tầng); nhãn **>2 ký tự vẽ DƯỚI nút** thay vì trong vòng tròn.
- Guard: fixture `vr1-realworld-vietnamese-labels` vào **bộ chụp thường trực**.
- Phụ thu: cây 1 nút hết khoảng trắng thừa (chiều cao nay theo độ sâu) — xoá
  luôn một mục backlog cũ.

## Backlog visual còn lại (không chặn)

- Nhãn quá ~12 ký tự trong cây >11 nút chưa đo — cần fixture mới nếu nới giới
  hạn số nút.
