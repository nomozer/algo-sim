# Báo Cáo Kiểm Toán & Hiệu Chỉnh An Toàn Biểu Diễn Toán Học Scene3D (`scene3d-plane-grid-camera`)

- **Run ID:** `scene3d-plane-grid-camera`
- **Nhánh:** `research/scene3d-plane-grid-camera`
- **Base commit (`main`):** `4abc4afbb976babc4740bf22e42dc368a24c1b13`
- **Trạng thái nghiệm thu thị giác:** `HUMAN_VISUAL_REVIEW_PENDING` (chờ người dùng duyệt trực tiếp, **chưa tích hợp**)
- **Phạm vi thay đổi:** Chỉ frontend (`frontend/src/simulations/domains/geometry/*`, `frontend/src/styles/global.css`). Backend, Planner, Kernel, Registry, provider prompts không thay đổi (`DEFAULT_MODE = LLM_ONLY`, `Hybrid = NO-GO`).

---

## 1. Phân Loại Hạng Mục Kiểm Toán (`P0` & `P1`)

| Hạng mục | Phân loại | Tóm tắt nguyên nhân gốc & sửa đổi |
| --- | --- | --- |
| **P0 — Kiểm toán dấu vuông góc (`projectionWitnessesAt`)** | **`CONFIRMED_BUG`** | (1) Phát sinh ký hiệu vuông góc sớm ngay ở Bước 4/5 (`CREATE bc`) trước khi có bước kết luận ở Bước 5/5 (`MEASURE goc`). (2) Phép chiếu Gram-Schmidt `u = uRaw - (uRaw·v)v` tự tạo tính trực giao về mặt đại số cho cả vector gốc chưa vuông góc. (3) Vẽ 2 dấu góc vuông chồng chéo nhau tại `B` trên hình chiếu phối cảnh 2D. |
| **P1 — Kiểm toán đồng phẳng tấm mặt phẳng (`moRongDaGiacMatPhang`)** | **`CONFIRMED_BUG`** | Với mặt phẳng gần ngang nhưng nghiêng nhẹ (`0.98 < \|u_z\| < 1`, nên `ngang = true`), nhánh `if (ngang)` trả về đỉnh `[x + s, y + t, z0]` cố định cao độ `z = z0` theo mặt phẳng `XY`, vi phạm đồng phẳng với pháp tuyến thật `u` (`\|dot(vertex - origin, u)\| ≈ 0.0276 >> 1e-8`). |

---

## 2. Chi Tiết Kiểm Toán & Khắc Phục `P0` — Dấu Vuông Góc (`scene3d-annotations.ts`)

### 2.1. Ba lỗi đã xác nhận trong `projectionWitnessesAt` trước khi sửa
1. **Thiếu cổng chứng nhận quan hệ ở bước hiện tại (`chungNhanDuongMp`):**
   - Trước khi sửa, `projectionWitnessesAt` quét mọi cặp `(d, mp)` đang hiển thị (`present`) và sinh ngay marker vuông góc khi thấy `|v × np| ≈ 0`. Hệ quả: trong cảnh `vuong-goc-chop`, ngay tại **Bước 4/5** (mới dựng đường thẳng `BC`, chưa tới Bước 5/5 đo/kết luận `cos²(BC, (SAB)) = 0`), dấu góc vuông đã tự xuất hiện sớm.
2. **Phép chiếu đại số Gram-Schmidt tự hợp thức hóa hướng không vuông góc:**
   - Trước khi sửa, với mỗi đỉnh `pMp` trong `mp.depends`, hàm tính `uRaw = pMp - chan` rồi chiếu lên phần bù trực giao của `v`: `u = uRaw - (uRaw · v) * v`, sau đó mới kiểm tra `|dot(u, v)| <= 1e-3`. Vì `u` vừa được trừ thành phần dọc theo `v`, tích vô hướng `dot(u, v)` **luôn bằng `0` về mặt đại số** đối với mọi điểm `pMp` không nằm trên đường thẳng `d`, kể cả khi dữ liệu bị lệch khiến `uRaw` không hề vuông góc với `v` hay không nằm trong mặt phẳng `mp`.
3. **Hai dấu vuông góc chồng chéo nhau tại `B`:**
   - Việc vẽ đồng thời 2 ký hiệu góc vuông (`perpendicular:bc` theo hướng `BA` và `perpendicular:bc#2` theo hướng `BS`) chung đỉnh `B` và chung cạnh `BC` khiến hai khung chữ L cắt chồng lên nhau trên mặt phẳng chiếu 2D tại đỉnh `B`.

### 2.2. Cách sửa `P0` trong `projectionWitnessesAt` (`scene3d-annotations.ts`)
1. **Điều kiện kích hoạt có chứng chỉ (`chungNhanDuongMp`):**
   - Chỉ xét cặp `(d, mp)` khi tại bước hiện tại (`step`) có đối tượng kết luận/đo lường thuộc `present` và `daTinh`/`ketLuan` tham chiếu đồng thời `d.id` và `mp.id` trong `depends`, có ký hiệu/nhãn/giá trị xác nhận quan hệ vuông góc (`⊥`, `90°`, hoặc `cos... = 0`).
2. **Kiểm tra trực tiếp trên vector gốc `uRaw` (không chiếu Gram-Schmidt):**
   - Với từng đỉnh `idMp` trong `mp.depends` (`idMp !== chungId`), lấy `uRaw = pMp - chan` và kiểm tra trực tiếp bằng dung sai tương đối theo chuẩn độ dài:
     - Thuộc mặt phẳng `mp`: `|dot(uRaw, np)| <= 1e-4 * ||uRaw|| * ||np||`
     - Vuông góc thật sự với `v` và `vd`: `|dot(uRaw, v)| <= 1e-4 * ||uRaw|| * ||v||` và `|dot(uRaw, vd)| <= 1e-4 * ||uRaw|| * ||vd||`
   - Đòi hỏi mặt phẳng có **ít nhất 2 hướng gốc không cùng phương** (`daHuong.length >= 2`, kiểm tra `||cross(u1, u2)|| > 1e-3`) cùng đi qua `chan` và cùng vuông góc thật sự với đường thẳng.
3. **Hiển thị 1 ký hiệu vuông góc đơn, rõ ràng tại `B`:**
   - Sau khi đã xác minh đủ 2 hướng gốc độc lập tuyến tính trong mặt phẳng (`BA ⊥ BC` và `BS ⊥ BC`), chỉ phát sinh **1 marker duy nhất** (`id: perpendicular:${d.id}`, `u: daHuong[0].raw`, `v`) tại `B`, kết hợp với nhãn/ô soi kết luận `cos²(BC, (SAB)) = 0`. Không còn 2 dấu vuông góc chồng nhau.

---

## 3. Chi Tiết Kiểm Toán & Khắc Phục `P1` — Đồng Phẳng Tuyệt Đối (`scene3d-model.ts`)

### 3.1. Lỗi đồng phẳng ở nhánh `ngang` (`0.98 < |u_z| < 1`)
- Trong `moRongDaGiacMatPhang` (`scene3d-model.ts`), biến `ngang` được định nghĩa là `Math.abs(u[2]) > 0.98`.
- Khi mặt phẳng gần ngang nhưng có độ nghiêng nhỏ (ví dụ `normal = [0.15, -0.08, 1]`, nên `|u_z| ≈ 0.985856 > 0.98`), nhánh `if (ngang)` trước đây trả về `[diemMp[0] + s, diemMp[1] + t, diemMp[2]]` (tức đặt trong mặt phẳng `z = const` thay vì mặt phẳng có pháp tuyến `u`), dẫn tới sai số đồng phẳng `|dot(vertex - origin, u)| ≈ 0.027604 >> 1e-8`.
- Ngoài ra, các ngưỡng kiểm tra suy biến cố định `1e-5` trong `daGiacMatPhang` và `catDaGiacTheoDay` chưa co giãn theo tỉ lệ tọa độ (`scale = 1e-3`).

### 3.2. Cách sửa `P1` trong `moRongDaGiacMatPhang`, `daGiacMatPhang`, `catDaGiacTheoDay`
- Trong nhánh `if (ngang)` của `moRongDaGiacMatPhang`, dựng hệ cơ sở trực chuẩn `(e1, e2)` **nằm chính xác trong mặt phẳng vuông góc với `u`**:
  - `e1 = normalize([1 - u_x^2, -u_x u_y, -u_x u_z])` (hình chiếu của trục `X` lên mặt phẳng, nên `dot(e1, u) = 0`),
  - `e2 = ±normalize(u × e1)` (chọn dấu sao cho `e2_y >= 0`, nên `dot(e2, u) = 0` và `dot(e1, e2) = 0`).
  - Khi `u = [0, 0, ±1]` (mặt phẳng ngang tuyệt đối), công thức này suy biến chính xác về `e1 = [1, 0, 0], e2 = [0, 1, 0]`.
  - Khi `0.98 < |u_z| < 1` (mặt phẳng gần ngang), mọi đỉnh `diemMp + s * e1 + t * e2` thỏa mãn `|dot(vertex - origin, u)| <= 1e-15 * scale`.
- Chuẩn hóa dung sai theo tỉ lệ tọa độ (`scale`) trong `daGiacMatPhang`, `catDaGiacTheoDay` và `moRongDaGiacMatPhang`, bảo đảm bất biến qua phép co giãn `scale ∈ {1e-3, 1, 1e3}`, thứ tự điểm, điểm gốc trên mặt phẳng và dấu pháp tuyến `±n`.

---

## 4. Kết Quả Kiểm Chứng (`P2` & `P3`)

- **Vitest (`npx vitest run`):** `68/68` file test PASS (`1.087/1.087` tests PASS).
- **Build sản phẩm (`npm run build`):** `tsc -b && vite build` thành công (`exit 0`).
- **Bộ ảnh đối chứng `BEFORE / AFTER`:**
  - `visual/comparisons/cmp-12-p0-sab-steps-3-4-5.png`: Bước 4/5 không lộ dấu vuông góc sớm (`witness_ids = []`).
  - `visual/comparisons/cmp-13-p0-closeup-vertex-B.png`: Cận cảnh 2× tại đỉnh `B` ở Bước 5/5 (Before 2 dấu chồng nhau vs After 1 dấu đơn sắc nét).
  - `visual/comparisons/cmp-14-p1-nearly-horizontal-plane.png`: Mặt phẳng gần ngang (`0.98 < |u_z| < 1`) đồng phẳng tuyệt đối (`max|dot| = 0`).
  - `visual/comparisons/cmp-15-p0-oblique-line-no-false-marker.png`: Đường nghiêng `SC` cắt mặt phẳng `(ABC)` tại `C` không sinh dấu vuông góc giả (`witness_ids = []`).
  - `visual/comparisons/cmp-01` .. `cmp-11`: Toàn bộ các cảnh `(SAB)`, `(MNP)`, thiết diện `MNP` màu hổ phách, `(ABC)`, lưới nền và camera orbit/reset đều giữ nguyên chất lượng.
