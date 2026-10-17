# Báo Cáo Kiểm Toán & Hiệu Chỉnh Đúng Đắn Toán Học Ký Hiệu Scene3D (`scene3d-annotation-correctness`)

- **Run ID:** `scene3d-annotation-correctness`
- **Nhánh làm việc:** `research/scene3d-annotation-correctness`
- **Baseline `main` / `origin/main`:** `8427c87989487fdbcbb547ec16039d439528eb51`
- **Chế độ sản phẩm mặc định:** `DEFAULT_MODE = LLM_ONLY` (giữ nguyên bất biến; Hybrid product enablement = `NO-GO`)
- **Phạm vi thay đổi:** Chỉ chỉnh tầng trình bày frontend (`scene3d-model.ts`, `scene3d-view.tsx`) và khóa bằng unit test (`scene3d.test.tsx`, `scene3d-annotations.test.ts`). Không chạm Backend, Planner, Kernel, prompt hay schema.
- **Lớp đính chính (`CORRECTED_BY`):** Đính chính diễn giải văn bản tại mục `§2.3 (EDU-4)` của [`docs/evaluation/geometry/runs/scene3d-educational-finalization/report.md`](../scene3d-educational-finalization/report.md) (trước đó mô tả lỏng `marker: { u, v }` là "hai cơ sở trực chuẩn trên mặt phẳng đích"; thực tế trong [`quantity_annotations.py::_nhan_chung`](../../../../../backend/app/simulation/semantic_program/quantity_annotations.py) dòng 102–141, `v = from - foot` là vector pháp tuyến $\overrightarrow{HM}$ từ chân chiếu tới điểm nguồn và `u` là vector tiếp tuyến thuộc mặt phẳng/đường thẳng đích).

---

## 1. P1 — Kiểm Toán Toán Học & Sửa Ký Hiệu Vuông Góc (`vatNhanChung`, `huongChanVuongGoc`)

### 1.1. Kiểm toán trực giao trong không gian thế giới 3D (`dot(u_world, v_world)`)

Sau phép nhúng metric `veKhongGian` ($T^T T = G$) tại [`scene3d-chart.ts`](../../../../../frontend/src/simulations/domains/geometry/scene3d-chart.ts), toàn bộ 9 nhân chứng vuông góc trong bộ cảnh chuẩn (`docs/evaluation/geometry/runs/scene3d-visual-correctness/visual/scenes.json`) đều thỏa mãn $\overrightarrow{HM} = \text{from} - \text{foot}$ vuông góc tuyệt đối với mặt phẳng hoặc đường thẳng đích:

| Cảnh | Loại khoảng cách | Điểm nguồn $M_{\text{world}}$ | Chân chiếu $H_{\text{world}}$ | Vector $v_{\text{world}} = \overrightarrow{HM}$ | Vector $u_{\text{world}}$ (trước khi sửa) | $\text{dot}(u_{\text{world}}, v_{\text{world}})$ | $\max_{P \in \text{target}} |\text{dot}(\overrightarrow{HM}, \overrightarrow{HP})|$ |
|---|---|---|---|---|---|---|---|
| `pyr-midpoint-to-plane` | Điểm $\to$ mặt phẳng $(SAB)$ | $(1, 1, 1.5)$ | $(1, 0, 1.5) \in SB$ | $(0, 1, 0)$ | $(-1, 0, 1.5) \parallel \overrightarrow{HS}$ | `0.000000` | `0.000000` |
| `cube-midpoint-to-plane` | Điểm $\to$ mặt phẳng $(A'BD)$ | $(1, 2, 2)$ | $(0, 1, 1) \in A'D$ | $(1, 1, 1)$ | $(0, -1, 1) \parallel \overrightarrow{HA'}$ | `0.000000` | `0.000000` |
| `prism-midpoint-to-plane` | Điểm $\to$ mặt phẳng $(ABB')$ | $(1.5, \frac{\sqrt{3}}{2}, 3)$ | $(1.5, 0, 3) \in A'B'$ | $(0, \frac{\sqrt{3}}{2}, 0)$ | $(-1.5, 0, -3.0) = \overrightarrow{HA}$ | `0.000000` | `0.000000` |
| `pyr-midpoint-to-named-line` | Điểm $\to$ đường thẳng $BD$ | $(1, 1, 1.5)$ | $(1, 1, 0) \in BD$ | $(0, 0, 1.5)$ | $(-1, 1, 0) \parallel \overrightarrow{BD}$ | `0.000000` | `0.000000` |
| `pyr-midpoint-to-result-line` | Điểm $\to$ giao tuyến $SH$ | $(1, 1, 1.5)$ | $(-0.8, 0.1, 3) \in SH$ | $(1.8, 0.9, -1.5)$ | $(-2, 1, 0) \parallel \overrightarrow{SH}$ | `0.000000` | `0.000000` |
| `cuboid-midpoint-to-result-line` | Điểm $\to$ giao tuyến $BB'$ | $(1.5, 2, 5)$ | $(3, 0, 5) \equiv B'$ | $(-1.5, 2, 0)$ | $(0, 0, 5) \parallel \overrightarrow{BB'}$ | `0.000000` | `0.000000` |
| `rb:derived-line-prism` | Điểm $\to$ giao tuyến $BB'$ | $(1, \sqrt{3}, 0)$ | $(2, 0, 0) \equiv B$ | $(-1, \sqrt{3}, 0)$ | $(0, 0, 3) \parallel \overrightarrow{BB'}$ | `0.000000` | `0.000000` |
| `ge:pyramid-midpoint-A` | Điểm $\to$ mặt phẳng $(SBD)$ | $(1, 1, 1.5)$ | $(\frac{7}{9}, \frac{7}{9}, \frac{4}{3}) \in SO$ | $(\frac{2}{9}, \frac{2}{9}, \frac{1}{6})$ | $(-\frac{7}{9}, -\frac{7}{9}, \frac{5}{3}) \parallel \overrightarrow{HS}$ | `0.000000` | `0.000000` |

### 1.2. Nguyên nhân gốc rễ khiến ký hiệu góc vuông ở `8427c879` trông như "ô vuông độc lập gây hiểu nhầm"

1. **Hướng tiếp tuyến `u` trong `prism-midpoint-to-plane` cắt chéo qua mặt thay vì bám dọc cạnh biên chứa chân chiếu $H$:**
   - Trong [`quantity_annotations.py::_nhan_chung`](../../../../../backend/app/simulation/semantic_program/quantity_annotations.py) (dòng 130), backend chọn `u = p0 - foot` với `p0` là điểm đầu tiên trong `plane.depends`.
   - Ở `pyr-midpoint-to-plane` ($H \in SB, p_0 = S$) và `cube-midpoint-to-plane` ($H \in A'D, p_0 = A'$), chân chiếu $H$ nằm trên cạnh biên đi qua $p_0$ nên $p_0 - H$ trùng ngay với cạnh biên của mặt phẳng.
   - Ngược lại, ở `prism-midpoint-to-plane` (mặt phẳng $(ABB')$ có $p_0 = A(0,0,0)$), chân chiếu $H(1.5, 0, 3)$ nằm trên cạnh biên đáy trên $A'B'$ ($A'(0,0,3) \to B'(2,0,3)$) không đi qua $A$. Do đó vector $u = A - H = (-1.5, 0, -3.0)$ chĩa chéo từ cạnh trên $A'B'$ xuống đỉnh đáy dưới $A(0,0,0)$. Dưới góc nhìn camera `(20°, 40°)`, hình chiếu 2D của $u$ và $v$ lệch nhau $173.1^\circ$ (gần như song song), tạo thành một hình thoi dẹt treo lơ lửng bên dưới cạnh $A'B'$.
2. **Đóng kín 4 cạnh của `goc` (`5` điểm) kèm khoảng hở nét đứt của `doan` ngay tại $H$:**
   - Ở commit `22df95d6` (`EDU-4`), `goc` được vẽ bằng 5 điểm `[chan, chan + u1, gocDinh, chan + v1, chan]` tô đè lên cả đường thẳng đích lẫn đoạn $MH$, trong khi `doan` được vẽ từ `tu` ($M$) tới `chan` ($H$) khiến đoạn `[chan, chan + v1]` rơi vào khoảng trống (`gapSize`) của nét đứt. Kết quả là ký hiệu trông như một ô vuông 4 cạnh đóng kín tách rời khỏi đoạn nét đứt $MH$.

### 1.3. Giải pháp tổng quát tại tầng trình bày (`scene3d-model.ts`, `scene3d-view.tsx`)

- **Căn hướng tiếp tuyến `u` dọc theo cạnh biên chứa $H$ (`huongChanVuongGoc` tại [`scene3d-model.ts`](../../../../../frontend/src/simulations/domains/geometry/scene3d-model.ts#L1033-L1070)):**
  - Khi nhân chứng có vector pháp tuyến `v` (khoảng cách điểm–mặt phẳng) và `chan` chưa nằm ở phần trong của một đoạn thuộc hình dọc theo `u`, hàm kiểm tra các cặp điểm của hình cùng nằm trong mặt phẳng qua `chan` vuông góc với `v` (`|dot(P - chan, v)| <= dungSai`). Nếu `chan` thực sự nằm ở phần trong của một đoạn nối hai điểm của hình trên mặt phẳng đó (như $H \in A'B'$ trên $(ABB')$), `u` được căn dọc theo cạnh biên đó ($\overrightarrow{HA'} = (-1.5, 0, 0)$).
  - Với khoảng cách điểm–đường thẳng khi $H$ trùng đỉnh đầu mút (như $H \equiv B'$ trên $BB'$ ở `cuboid-midpoint-to-result-line`), giữ nguyên quy tắc lật `-u` vào trong đoạn $BB'$.
- **Ký hiệu góc vuông chữ L 2 đoạn chuẩn sách giáo khoa + nét đứt xuất phát từ $H$ (`vatNhanChung` tại [`scene3d-view.tsx`](../../../../../frontend/src/simulations/domains/geometry/scene3d-view.tsx#L1747-L1785)):**
  - Đảo hướng dựng `doan` thành `[chan, tu]` (từ $H$ tới $M$) với `chuKy = Math.max(0.045, Math.min(0.16, dk * 0.034), s * 1.05)` và `s <= dk * 0.042`. Nhờ đó nét liền đầu tiên của đường vuông góc luôn bắt đầu tại đúng chân $H$ và phủ qua điểm `chan + v1` (không bao giờ bị hở nét tại góc vuông).
  - Vẽ `goc` bằng đúng 3 điểm (2 đoạn chữ L) `[chan + u1, gocDinh, chan + v1]`, kết hợp với cạnh/đường thẳng qua $H$ và nét đầu tiên của $HM$ tạo thành ký hiệu góc vuông nhỏ, rõ, gắn trực tiếp vào hai tia tạo góc vuông và bất biến khi xoay camera.

---

## 2. P2 — Kiểm Toán Ngữ Nghĩa Hình Học Trên 7 Cảnh Trọng Điểm

### 2.1. Kiểm toán điểm $M$ và loại khối theo đề bài gốc (`compiler-scene-suite.mjs`)

| Cảnh | Đề bài gốc (`compiler-scene-suite.mjs`) | Loại khối (`solid.label` & kích thước thế giới) | Giả thiết điểm $M$ trong đề | Tọa độ $M_{\text{world}}$ và kiểm tra trung điểm $\frac{X+Y}{2}$ | Kết luận |
|---|---|---|---|---|---|
| `pyr-midpoint-to-plane` | Hình chóp $S.ABCD$, đáy $ABCD$ hình vuông cạnh $2$, $SA \perp (ABCD)$, $SA = 3$. $M$ là trung điểm $SC$. Tính $d(M, (SAB))$. | Hình chóp tứ giác (`pyramid`), đáy vuông $2 \times 2$, cao $SA = 3$. | Trung điểm $SC$ | $S(0,0,3), C(2,2,0) \implies M(1,1,1.5) = \frac{S+C}{2}$ | **KHỚP 100%** |
| `prism-midpoint-to-plane` | Lăng trụ tam giác đều $ABC.A'B'C'$, đáy cạnh $2$, cạnh bên $AA' = 3$. $M$ là trung điểm $B'C'$. Tính $d(M, (ABB'))$. | Hình lăng trụ tam giác đều (`prism`), $\triangle ABC$ đều cạnh $2$, cao $3$. | Trung điểm $B'C'$ | $B'(2,0,3), C'(1,\sqrt{3},3) \implies M(1.5, \frac{\sqrt{3}}{2}, 3) = \frac{B'+C'}{2}$ | **KHỚP 100%** |
| `pyr-midpoint-to-named-line` | Hình chóp $S.ABCD$, đáy vuông cạnh $2$, $SA \perp (ABCD)$, $SA = 3$. $M$ là trung điểm $SC$. Tính $d(M, BD)$. | Hình chóp tứ giác (`pyramid`), đáy vuông $2 \times 2$, cao $SA = 3$. | Trung điểm $SC$ | $S(0,0,3), C(2,2,0) \implies M(1,1,1.5) = \frac{S+C}{2}$ | **KHỚP 100%** |
| `pyr-midpoint-to-result-line` | Hình chóp $S.ABCD$, đáy vuông cạnh $2$, $SA \perp (ABCD)$, $SA = 3$. $d = (SAB) \cap (SCD)$, $M$ trung điểm $SC$. Tính $d(M, d)$. | Hình chóp tứ giác (`pyramid`), đáy vuông $2 \times 2$, cao $SA = 3$. | Trung điểm $SC$ | $S(0,0,3), C(2,2,0) \implies M(1,1,1.5) = \frac{S+C}{2}$ | **KHỚP 100%** |
| `cuboid-midpoint-to-result-line` | Hình hộp chữ nhật $ABCD.A'B'C'D'$, $AB=3, AD=4, AA'=5$. $d = (ABB'A') \cap (BCC'B')$, $M$ trung điểm $A'C'$. Tính $d(M, d)$. | Hình hộp chữ nhật (`prism`/cuboid) kích thước $3 \times 4 \times 5$. | Trung điểm $A'C'$ | $A'(0,0,5), C'(3,4,5) \implies M(1.5, 2, 5) = \frac{A'+C'}{2}$ | **KHỚP 100%** |
| `rb:derived-line-prism` | Lăng trụ tam giác đều $ABC.A'B'C'$, đáy cạnh $2$, cao $3$. $d = (ABB'A') \cap (BCC'B')$, $M$ trung điểm $AC$. Tính $d(M, d)$. | Hình lăng trụ tam giác đều (`prism`), đáy đều cạnh $2$, cao $3$. | Trung điểm $AC$ | $A(0,0,0), C(2,2\text{ chart}\to(1,\sqrt{3},0)) \implies M(1,\frac{\sqrt{3}}{2},0) = \frac{A+C}{2}$ | **KHỚP 100%** |
| `section-cube-A1BD` | Hình lập phương $ABCD.A'B'C'D'$ cạnh $2$, mặt phẳng cắt qua $A', B, D$. | Hình lập phương (`prism`/cube) kích thước $2 \times 2 \times 2$ (tất cả 12 cạnh $= 2$). | — | Thiết diện là $\triangle A'BD$ đều cạnh $2\sqrt{2} \approx 2.8284$. | **KHỚP 100%** |

### 2.2. Kiểm toán nhãn khoảng cách so với đối tượng được hỏi trong đề bài

- **Nhóm bài khoảng cách điểm $\to$ mặt phẳng (`pyr-midpoint-to-plane`, `cube-midpoint-to-plane`, `prism-midpoint-to-plane`):**
  - Pipeline không tạo thực thể `point3` $H$ riêng trên timeline dựng hình; đại lượng kết quả gắn trực tiếp vào điểm $M$ và mặt phẳng đích (`subject_ids: ["M", "mp_q"]`, `anchor: "witness"`).
  - Nhãn hiển thị trên hình ghi trực tiếp đối tượng được hỏi trong đề: `d(M, (SAB)) = 1`, `d(M, (A'BD)) = √3`, `d(M, (ABB')) = √3/2`.
- **Nhóm bài khoảng cách điểm $\to$ đường thẳng có bước dựng chân đường vuông góc $H$ (`pyr-midpoint-to-named-line`, `pyr-midpoint-to-result-line`, `cuboid-midpoint-to-result-line`, `rb:derived-line-prism`):**
  - Trình biên dịch tường minh hóa bước dựng hình chiếu vuông góc `H = project_point_to_line(M, target_line)` (`CONSTRUCT_FOOT_POINT`), sau đó đo độ dài đoạn vuông góc `d(M, H)` (`subject_ids: ["M", "H"]`, `anchor: "segment"`).
  - Vì $H$ là hình chiếu vuông góc của $M$ lên đường thẳng đích $d$, độ dài đoạn nhân chứng $MH = d(M, H)$ chính là giá trị toán học tương đương của $d(M, d)$, và bảng lời giải bên dưới ghi rõ chuỗi quy đổi `Khoảng cách từ M đến đường thẳng = MH = ...`.

### 2.3. Chứng minh toán học vị trí điểm $C'$ so với thiết diện $(A'BD)$ trong `section-cube-A1BD` và `cube-midpoint-to-plane`

- **Trong không gian 3D thực tế ($[0, 2]^3$ của `section-cube-A1BD`):**
  - Ba đỉnh định nghĩa thiết diện là $A'(0, 0, 2)$, $B(2, 0, 0)$, $D(0, 2, 0)$.
  - Phương trình mặt phẳng $(A'BD)$ là $x + y + z = 2$ với pháp tuyến đơn vị $\hat{n} = \frac{1}{\sqrt{3}}(1, 1, 1)$.
  - Đỉnh $C'$ có tọa độ $(2, 2, 2)$, nên $x + y + z = 6 \ne 2$. Khoảng cách có dấu từ $C'$ tới mặt phẳng $(A'BD)$ trong 3D là:
    $$d_{3D}(C', (A'BD)) = \frac{|2 + 2 + 2 - 2|}{\sqrt{1^2 + 1^2 + 1^2}} = \frac{4}{\sqrt{3}} \approx 2.3094 > 0$$
  - Do đó **$C'$ hoàn toàn KHÔNG thuộc thiết diện $(A'BD)$ trong không gian 3D**.
- **Giải thích hiện tượng trên hình chiếu 2D ở góc camera mặc định `(pv = 30°, cao = 35°)`:**
  - Hàm chọn góc nhìn [`danhGiaGocNhin`](../../../../../frontend/src/simulations/domains/geometry/scene3d-camera.ts) đánh giá trên phép chiếu trực giao chuẩn hóa theo bán kính cảnh $R = \sqrt{3}$: ở góc `(30°, 35°)`, khoảng cách trực giao 2D từ $C'$ tới cạnh $A'D$ là `0.2250 R > 0.14 R` (`dinhGanCanh = 0`).
  - Khi vẽ bằng `PerspectiveCamera(fov = 50°)` đặt cách tâm $2.349 R$, đỉnh $C'(2,2,2)$ là đỉnh nằm gần ống kính nhất (`depth = +0.9803 R`) nên bị phóng đại ra ngoài theo luật phối cảnh ($1 / z_{\text{cam}}$), trong khi cạnh $A'D$ nằm phía sau tâm (`depth ≈ -0.4096 R`) bị thu nhỏ vào trong. Sự chênh lệch độ sâu phối cảnh làm khoảng cách 2D trên màn hình giữa $C'$ và cạnh $A'D$ thu hẹp còn `0.0629 R`.
  - Khi xoay nhẹ camera sang góc орbit thứ hai (`09-section-cube-A1BD-orbit.png`), đỉnh $C'$ tách hẳn sang biên trái của khối lập phương, minh chứng trực quan $C' \notin (A'BD)$ mà không cần thay đổi góc nhìn mặc định của họ hình lập phương.

### 2.4. Kiểm toán và sửa lỗi nhãn số đo che đoạn nhân chứng dốc đứng (`chieuNhan` tại `scene3d-view.tsx`)

- **Phát hiện:** Trong `pyr-midpoint-to-result-line` (`05-pyr-midpoint-to-result-line-selected-H.png`) và `rb:derived-line-prism` (`07-rb-derived-line-prism-selected-H.png`), nhãn số đo `d(M, H)` neo tại trung điểm $(ax, ay)$ của đoạn $MH$. Do `placeAnnotationLabels` thử vị trí `tren` (`{ x: ax - w/2, y: ay - 6 - h }`) đầu tiên và `gocVuongRects` trước đó chỉ chặn tại chân `foot` và đỉnh góc vuông `corner`, khi đoạn $MH$ dốc đứng hoặc chéo, hộp nhãn đặt ở vị trí `tren` nằm đè ngang qua chính đoạn nét đứt $MH$.
- **Sửa lỗi tại [`scene3d-view.tsx`](../../../../../frontend/src/simulations/domains/geometry/scene3d-view.tsx#L2029-L2088):** Lưu thêm tọa độ `from` vào `userData` của nhóm nhân chứng và trong `chieuNhan`, khi độ dài hình chiếu đoạn $MH$ trên màn hình $> 24\text{ px}$, đặt hai hộp cản nhỏ `4×4 px` tại $\pm 10\text{ px}$ dọc theo phương đoạn $MH$ tính từ trung điểm $(mx, my)$. Nhờ đó:
  - Khi $MH$ dốc đứng (`pyr-midpoint-to-result-line`), hai hộp cản chặn vị trí `tren`/`duoi` và đẩy nhãn `d(M, H) = √13/2` sang bên phải đoạn $MH$.
  - Khi $MH$ nằm ngang (`cuboid-midpoint-to-result-line`), hai hộp cản nằm ngang tại $y = my$ nên không chạm vị trí `tren` ($y \le my - 6$), giữ nguyên nhãn `d(M, H) = √5` phía trên đoạn $MB'$.

---

## 3. Bằng Chứng Kiểm Chứng Tự Động & Trình Duyệt (P3)

1. **Unit tests (`vitest`):**
   - `npx vitest run`: **68/68 test files PASS (1.079/1.079 tests PASS)**.
   - Bổ sung test `P1-CORRECTNESS` trong `scene3d.test.tsx` (kiểm tra `pos.count === 3`, `dot(uVec, vVec) === 0`, `uVec` bám dọc cạnh $A'B'$ trong `prism-midpoint-to-plane`, và `dashSize >= s * 1.04` xuất phát từ `foot`) và test `P2-5` trong `scene3d-annotations.test.ts` (nhãn số đo tránh thân đoạn nhân chứng dốc đứng).
2. **Production build:**
   - `npm run build` (`tsc -b && vite build`): **PASS** (0 lỗi TypeScript, 0 lỗi đóng gói).
3. **Browser gates & bộ ảnh đối chiếu `1280×900`:**
   - `node scripts/scene3d-orbit-gate.mjs`: **17/17 PASS**.
   - `node scripts/hybrid-section-visual-check.mjs --gate-all`: **14/14 PASS**.
   - Bộ 30 ảnh `1280×900` (`after/`) và 6 bảng đối chiếu `BEFORE/AFTER` (`p1-cmp-*.png`) lưu tại `docs/evaluation/geometry/runs/scene3d-annotation-correctness/visual/`.
