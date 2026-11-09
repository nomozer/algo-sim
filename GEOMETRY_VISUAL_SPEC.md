# GEOMETRY_VISUAL_SPEC.md — Đặc Tả Trực Quan & Báo Cáo Kiểm Toán Thư Viện Hình Học 3D Axo

> **Nhánh kiểm chứng:** `feat/axo-geometry-library-verification`  
> **Worktree độc lập:** `D:/Documents/projects/axo-geometry-library`  
> **Phạm vi:** 11 bài mô phỏng trong `publicCatalog()` (`frontend/src/data/geometry-samples.json` & `frontend/src/components/SamplePreview.tsx`) + 6 bài toán hình học không gian THPT tổng hợp đề xuất mở rộng.

---

## 1. Tổng hợp kết quả kiểm toán 11 bài mẫu hiện có (§4)

| # | `sample_id` | Tên bài mô phỏng | Nhóm hình | Số bước dựng | Số đối tượng `Scene3D` | Phân loại trước khi sửa (`BEFORE`) | Nguyên nhân gốc (`Root Cause`) | Giải pháp đã áp dụng (`Fix`) | Trạng thái sau khi sửa (`AFTER`) |
| :-: | :--- | :--- | :--- | :-: | :-: | :--- | :--- | :--- | :-: |
| 1 | `thiet-dien-chop` | Thiết diện của hình chóp cắt bởi mặt phẳng | Hình chóp | 3 | 17 | `THUMBNAIL_MISMATCH` (`Scene3D`: `PASS`) | `SamplePreview.tsx` vẽ chóp tam giác $S.ABC$ với thiết diện tam giác $\triangle MNP$, trong khi `Scene3D` thật là chóp tứ giác $S.ABCD$ ($SA \perp (ABCD)$) với thiết diện tứ giác $MNPQ$. | Cập nhật `SamplePreview.tsx` vẽ đúng chóp tứ giác $S.ABCD$, $SA \perp (ABCD)$, mặt phẳng $(\alpha)$ và thiết diện tứ giác $MNPQ$ (`M, N, P, Q` trên $SA, SB, SC, SD$). | **`PASS`** |
| 2 | `mat-cheo-sac` | Mặt chéo $(SAC)$ của hình chóp tứ giác | Hình chóp | 3 | 9 | `THUMBNAIL_MISMATCH` (`Scene3D`: `PASS`) | `SamplePreview.tsx` vẽ chóp tứ giác đều có thiết diện tứ giác $MNPQ$ và đường cao tâm đáy thay vì mặt chéo $\triangle SAC$ của chóp $S.ABCD$. | Cập nhật `SamplePreview.tsx` vẽ đúng chóp tứ giác $S.ABCD$ ($SA \perp (ABCD)$), mặt phẳng chéo $(SAC)$ và miền tam giác chéo $\triangle SAC$. | **`PASS`** |
| 3 | `vuong-goc-chop` | Cạnh bên vuông góc với mặt đáy hình chóp | Hình chóp | 2 | 8 | `THUMBNAIL_MISMATCH` (`Scene3D`: `PASS`) | `SamplePreview.tsx` vẽ chóp tam giác $S.ABC$ có điểm $M \in BC$, trong khi `Scene3D` thật là chóp tứ giác $S.ABCD$ với $SA \perp (ABCD)$ tại $A$. | Cập nhật `SamplePreview.tsx` vẽ đúng chóp tứ giác $S.ABCD$, cạnh bên $SA \perp (ABCD)$ và hai dấu góc vuông tại chân $A$ theo $AB, AD$. | **`PASS`** |
| 4 | `mp-vuong-goc-duong` | Mặt phẳng qua một điểm và vuông góc với đường thẳng cho trước | Hình chóp | 7 | 10 | `SCENE_ERROR` (chồng nhãn `[(α)]`) + `THUMBNAIL_MISMATCH` | 1. Trong `scene3d-view.tsx` (`chieuNhan`), nhãn mặt phẳng `[(α)]` (`mpb`) chọn điểm neo gần trung điểm cạnh trong nên đè gần đoạn $BH$, nhãn `[H]` và dấu góc vuông tại $H$.<br>2. `SamplePreview.tsx` vẽ chóp tam giác $S.ABC$ cắt bởi mặt phẳng tại $M$, khác với `Scene3D` thật (chóp tứ giác $S.ABCD$, mặt phẳng $(\alpha)$ qua $B$ vuông góc với $SC$ tại $H$, $BH \perp SC$). | 1. Tinh chỉnh ứng viên neo nhãn `.geo3d-nhan-mp` trong `scene3d-view.tsx` ưu tiên góc ngoài của đa giác mặt phẳng và tăng khoảng cách tránh `gocVuongRects` + `hopDiem`.<br>2. Cập nhật `SamplePreview.tsx` vẽ đúng chóp $S.ABCD$, mặt phẳng $(\alpha)$ qua $B$ vuông góc $SC$ tại $H$, đoạn $BH \perp SC$ và góc vuông tại $H$. | **`PASS`** |
| 5 | `the-tich-chop` | Thể tích khối chóp và đường cao hạ từ đỉnh | Hình chóp | 2 | 12 | `THUMBNAIL_MISMATCH` (`Scene3D`: `PASS`) | `SamplePreview.tsx` vẽ chóp tam giác $S.ABC$, thiếu đỉnh $D$ của chóp tứ giác đều $S.ABCD$ trong `Scene3D` thật. | Cập nhật `SamplePreview.tsx` vẽ đúng chóp tứ giác đều $S.ABCD$, hai đường chéo đáy nét đứt giao tại tâm $H$, đường cao $SH \perp (ABCD)$ và góc vuông tại $H$. | **`PASS`** |
| 6 | `cau-cat-mat-phang` | Mặt phẳng cắt mặt cầu theo đường tròn giao tuyến | Mặt cầu | 5 | 13 | `THUMBNAIL_MISMATCH` (`Scene3D`: `PASS`) | `SamplePreview.tsx` ghi nhãn tâm mặt cầu là `O` thay vì `I` như trong đề bài và `Scene3D` thật ($I, H, M$). | Cập nhật `SamplePreview.tsx` đồng bộ nhãn tâm mặt cầu `I`, tâm đường tròn giao tuyến `H`, điểm `M` trên vành giao tuyến, mặt phẳng $(\alpha)$ và $\angle IHM = 90^\circ$. | **`PASS`** |
| 7 | `cau-the-tich` | Bán kính và cấu trúc khối cầu | Mặt cầu | 2 | 6 | `THUMBNAIL_MISMATCH` (`Scene3D`: `PASS`) | `SamplePreview.tsx` ghi nhãn tâm mặt cầu là `O` thay vì `I` như trong đề bài và `Scene3D` thật ($I, A$). | Cập nhật `SamplePreview.tsx` đồng bộ nhãn tâm mặt cầu `I`, điểm `A` trên mặt cầu và bán kính $IA = R$. | **`PASS`** |
| 8 | `tru-thiet-dien-tron` | Thiết diện vuông góc trục của hình trụ | Hình trụ | 4 | 9 | `THUMBNAIL_MISMATCH` (`Scene3D`: `PASS`) | `SamplePreview.tsx` ghi nhãn tâm thiết diện là `H` và thêm điểm vành dư, trong khi `Scene3D` thật chỉ có $O, O'$ và trung điểm $M \in OO'$ với mặt phẳng $(\alpha)$ qua $M$. | Cập nhật `SamplePreview.tsx` đồng bộ chính xác 3 điểm $O, O', M$, trục $OO'$, mặt phẳng $(\alpha)$ và thiết diện tròn qua $M$. | **`PASS`** |
| 9 | `tru-truc-xien` | Hình trụ và quan hệ giữa trục với bán kính đáy | Hình trụ | 2 | 6 | `CAMERA_ISSUE` + `SCENE_ERROR` + `THUMBNAIL_MISMATCH` | 1. Trong `scene3d-camera.ts` (`diemTachDayTru`), `tich(u, d)` lấy trị tuyệt đối nên `chonHuongNhin` chọn góc nhìn nghiêng ngược trục $\overrightarrow{OO'} = (1, 2, 2)$ ($\vec{u}\cdot\vec{d} = -0.47 < 0$), nhìn từ dưới đáy $(O)$ lên làm nắp trên $(O')$ bị nét đứt nửa dưới và hai elip đáy chồng lấn 40%.<br>2. `SamplePreview.tsx` vẽ hình trụ đứng có điểm $A'$ dư. | 1. Định hướng $\vec{u}$ hướng lên ($u_z \ge 0$) trong `diemTachDayTru` (`scene3d-camera.ts`), yêu cầu $\vec{u}\cdot\vec{d} \in [0.25, 0.56]$, $\min(\text{moDay}_0, \text{moDay}_1) \ge 0.22$ và $h_{\text{chiếu}} \ge 1.75\,b_{\text{nhỏ}}$, giúp nhìn từ phía trên nắp $(O')$ xuống, hai đáy tách rời rõ và nắp trên liền nét 100%.<br>2. Cập nhật `SamplePreview.tsx` vẽ đúng hình trụ trục xiên $OO'$, bán kính đáy $OA$ và góc vuông tại $O$. | **`PASS`** |
| 10 | `non-thiet-dien-truc` | Thiết diện qua trục của hình nón | Hình nón | 5 | 12 | `SCENE_ERROR` (đường sinh $SB$ bị đứt nét) + `THUMBNAIL_MISMATCH` | Trong phép chiếu phối cảnh hữu hạn, với hai điểm đối tâm $A, B$ trên đường tròn đáy hình nón, tổng $(A\cdot(C-A)) + (B\cdot(C-B)) = -2r_0^2 < 0$ khiến ít nhất một trong hai đường sinh $SA, SB$ của thiết diện qua trục $\triangle SAB$ bị hàm phân loại đoạn thẳng đánh dấu `HIDDEN` (nét đứt) nửa dưới. | Bổ sung điều kiện biên đường sinh mặt nón trong `classifyWorldSegmentVisibility` (`scene3d-edge-visibility.ts`): đoạn thẳng nối đỉnh nón `vol.top` với điểm trên đường tròn đáy ($z \approx 0, r \approx R$) ở nửa hướng về camera hoặc vùng biên thiết diện qua trục ($\vec{p}_\perp \cdot \vec{e}_\perp \ge -0.45\,R\|\vec{e}_\perp\|$) không bị chính mặt nón đó che khuất (`VISIBLE` nét liền), trong khi đường kính đáy $AB$ ($z = 0$) vẫn giữ nguyên nét đứt và `diemVanhCongBiChe` giữ nguyên chuẩn pháp tuyến. | **`PASS`** |
| 11 | `non-duong-sinh` | Đường sinh, đường cao và bán kính đáy hình nón | Hình nón | 2 | 8 | `THUMBNAIL_MISMATCH` (nhãn chữ dư) (`Scene3D`: `PASS`) | `Scene3D` đã chính xác 100%; `SamplePreview.tsx` tinh gọn để đồng bộ hoàn toàn với `Scene3D` ($S, O, A$, tam giác vuông $\triangle SOA$, góc vuông tại $O$). | Chuẩn hóa `SamplePreview.tsx` đồng bộ với `Scene3D` của `non-duong-sinh`. | **`PASS`** |

---

## 2. Đặc tả hình minh họa (`Visual Specification`) cho 11 bài trong Thư viện (§5)

### 2.1. `thiet-dien-chop`
- **`sample_id`:** `thiet-dien-chop`
- **`title`:** Thiết diện của hình chóp cắt bởi mặt phẳng
- **`problem_text`:** Cho hình chóp tứ giác $S.ABCD$. Mặt phẳng $(\alpha)$ cắt bốn cạnh bên $SA, SB, SC, SD$ lần lượt tại các điểm $M, N, P, Q$. Dựng thiết diện $MNPQ$ của hình chóp cắt bởi mặt phẳng $(\alpha)$.
- **`main_solid`:** Hình chóp tứ giác $S.ABCD$ (`chop`, `PYRAMID_LIKE`, $A=(0,0,0), B=(4,0,0), C=(4,4,0), D=(0,4,0), S=(0,0,4)$).
- **`required_points`:** `A`, `B`, `C`, `D` (đáy), `S` (đỉnh), `M`, `N`, `P`, `Q` (giao điểm của $(\alpha)$ với $SA, SB, SC, SD$).
- **`required_segments`:** Các cạnh đáy `AB`, `BC`, `CD`, `DA`; các cạnh bên `SA`, `SB`, `SC`, `SD`; các cạnh biên thiết diện `MN`, `NP`, `PQ`, `QM`.
- **`required_planes`:** Mặt phẳng cắt $(\alpha)$ (`mp`, `point = [0, 0, 2]`, `normal = [0, 0, 1]`).
- **`required_sections`:** Thiết diện tứ giác `MNPQ` (`td`, `polygon3` / `section` tại cao độ $z = 2$).
- **`required_witnesses`:** Quan hệ liên thuộc điểm trên cạnh bên ($M \in SA, N \in SB, P \in SC, Q \in SD$) và giao tuyến mặt phẳng $(\alpha)$ với 4 mặt bên.
- **`camera_orientation`:** Góc nhìn sư phạm nghiêng từ phía trước-phải-trên, tách rõ 9 nhãn `S, A, B, C, D, M, N, P, Q` và mở rộng rõ miền thiết diện `MNPQ` cùng tấm mặt phẳng $(\alpha)$.
- **`step_expectations`:**
  - **Bước 1:** Dựng khối chóp tứ giác $S.ABCD$ và mặt phẳng đáy $(ABCD)$.
  - **Bước 2:** Dựng mặt phẳng cắt $(\alpha)$ đi qua tầng giữa của khối chóp.
  - **Bước 3:** Xác định các giao điểm $M, N, P, Q$ trên $SA, SB, SC, SD$ và khép kín miền thiết diện tứ giác $MNPQ$ (tô màu terracotta, phân biệt rõ cạnh thấy nét liền `NP, PQ` và cạnh khuất nét đứt `MN, MQ`).
- **`thumbnail_spec`:** SVG `viewBox="0 0 180 110"` vẽ hình chóp tứ giác $S.ABCD$ ($SA, AB, AD$ nét đứt; $BC, CD, SB, SC, SD$ nét liền), tấm mặt phẳng $(\alpha)$ tím nhạt, thiết diện tứ giác $MNPQ$ tô màu terracotta (`MN, MQ` nét đứt; `NP, PQ` nét liền) và đầy đủ 9 nhãn `S, A, B, C, D, M, N, P, Q`.

---

### 2.2. `mat-cheo-sac`
- **`sample_id`:** `mat-cheo-sac`
- **`title`:** Mặt chéo $(SAC)$ của hình chóp tứ giác
- **`problem_text`:** Cho hình chóp tứ giác $S.ABCD$ có đáy $ABCD$. Dựng mặt phẳng chéo $(SAC)$ đi qua đỉnh $S$ và hai đỉnh đối diện $A, C$ của mặt đáy.
- **`main_solid`:** Hình chóp tứ giác $S.ABCD$ (`chop`, `PYRAMID_LIKE`, $A=(0,0,0), B=(4,0,0), C=(4,3,0), D=(0,3,0), S=(0,0,4)$).
- **`required_points`:** `A`, `B`, `C`, `D`, `S`.
- **`required_segments`:** Các cạnh hình chóp `AB`, `BC`, `CD`, `DA`, `SA`, `SB`, `SC`, `SD` và đường chéo đáy `AC`.
- **`required_planes`:** Mặt phẳng chéo `(SAC)` (`mp`, `normal = [3, -4, 0]`).
- **`required_sections`:** Miền tam giác chéo $\triangle SAC$ (`sac`, `SECTION_REGION`, đỉnh `S, A, C`).
- **`required_witnesses`:** Đường chéo nội tiếp đáy $AC$ nối hai đỉnh đối diện $A, C$ và miền phẳng $(SAC)$ chia khối chóp thành hai khối chóp tam giác.
- **`camera_orientation`:** Hướng nhìn mở rộng mặt chéo $(SAC)$ (`|dir · n_SAC| >= 0.55`), không nhìn dọc theo đường chéo $AC$.
- **`step_expectations`:**
  - **Bước 1:** Dựng khối chóp tứ giác $S.ABCD$ với mặt đáy $ABCD$.
  - **Bước 2:** Dựng mặt phẳng $(SAC)$ đi qua đỉnh $S$ và đường chéo đáy $AC$.
  - **Bước 3:** Tô sáng miền tam giác chéo $\triangle SAC$ nằm bên trong khối chóp ($SA, AC$ nét đứt; $SC$ nét liền).
- **`thumbnail_spec`:** SVG `viewBox="0 0 180 110"` vẽ hình chóp tứ giác $S.ABCD$, tấm mặt phẳng $(SAC)$, miền tam giác chéo $\triangle SAC$ tô màu terracotta với đường chéo đáy $AC$ nét đứt và 5 nhãn `S, A, B, C, D`.

---

### 2.3. `vuong-goc-chop`
- **`sample_id`:** `vuong-goc-chop`
- **`title`:** Cạnh bên vuông góc với mặt đáy hình chóp
- **`problem_text`:** Cho hình chóp tứ giác $S.ABCD$ có cạnh bên $SA$ vuông góc với mặt phẳng đáy $(ABCD)$ tại $A$. Biểu diễn đường cao $SA$ và quan hệ vuông góc tại chân đường cao $A$.
- **`main_solid`:** Hình chóp tứ giác $S.ABCD$ (`chop`, `PYRAMID_LIKE`, $A=(0,0,0), B=(4,0,0), C=(4,3,0), D=(0,3,0), S=(0,0,4)$).
- **`required_points`:** `A` (chân đường cao), `B`, `C`, `D`, `S` (đỉnh).
- **`required_segments`:** Cạnh bên đường cao `SA` (`HEIGHT_SEGMENT`) và các cạnh của khối chóp `AB, BC, CD, DA, SB, SC, SD`.
- **`required_planes`:** Mặt phẳng đáy `(ABCD)` (`day`, `BASE_REGION`).
- **`required_sections`:** Không có thiết diện cắt (bài toán trọng tâm về quan hệ đường thẳng vuông góc mặt đáy).
- **`required_witnesses`:** Chứng chỉ vuông góc `perpendicular_witness` (`relation: "line_perp_plane"`, `from: "S"`, `foot_id: "A"`, `on: "day"`) kèm 2 ký hiệu góc vuông tại chân $A$ dọc theo $AB$ và $AD$.
- **`camera_orientation`:** Góc nhìn SGK giữ cạnh bên $SA$ thẳng đứng bên trái, mặt đáy $(ABCD)$ mở thoáng và hai dấu góc vuông tại $A$ tách rõ.
- **`step_expectations`:**
  - **Bước 1:** Dựng khối chóp tứ giác $S.ABCD$ với mặt đáy $(ABCD)$.
  - **Bước 2:** Nổi bật đường cao $SA \perp (ABCD)$ và hiển thị ký hiệu góc vuông tại chân đường cao $A$.
- **`thumbnail_spec`:** SVG `viewBox="0 0 180 110"` vẽ hình chóp tứ giác $S.ABCD$, mặt đáy tô nhẹ màu teal, cạnh đứng $SA$ tô nổi bật kèm 2 ký hiệu góc vuông tại $A$ và 5 nhãn `S, A, B, C, D`.

---

### 2.4. `mp-vuong-goc-duong`
- **`sample_id`:** `mp-vuong-goc-duong`
- **`title`:** Mặt phẳng qua một điểm và vuông góc với đường thẳng cho trước
- **`problem_text`:** Cho hình chóp $S.ABCD$ có đáy $ABCD$ là hình vuông cạnh $2$, $SA \perp (ABCD)$. Dựng mặt phẳng $(\alpha)$ đi qua đỉnh $B$ và vuông góc với cạnh bên $SC$ tại điểm $H \in SC$ ($BH \perp SC$ tại $H$).
- **`main_solid`:** Hình chóp tứ giác $S.ABCD$ (`khung`, `PYRAMID_LIKE`, $A=(0,0,0), B=(2,0,0), C=(2,2,0), D=(0,2,0), S=(0,0,4), H=(5/3, 5/3, 2/3)$).
- **`required_points`:** `S`, `A`, `B`, `C`, `D` (các đỉnh hình chóp) và `H` (giao điểm / chân đường vuông góc của $B$ trên $SC$).
- **`required_segments`:** Các cạnh hình chóp $S.ABCD$, cạnh bên trục vuông góc `SC` (`sc`) và đoạn vuông góc `BH` (`bh`, nối từ $B$ đến chân $H \in SC$).
- **`required_planes`:** Mặt phẳng $(\alpha)$ (`mpb`, đi qua $B, D, H$ và vuông góc với $SC$ tại $H$, thu gọn với đường chéo $< 4.3$).
- **`required_sections`:** Không có thiết diện đa giác khép kín (trọng tâm là dựng mặt phẳng qua điểm vuông góc với đường thẳng).
- **`required_witnesses`:** Chứng chỉ vuông góc `perpendicular_witness` tại $A$ ($SA \perp (ABCD)$) và tại $H$ (`from: "S"`, `foot_id: "H"`, `on: "mpb"`, `relation: "line_perp_plane"`, hiển thị đúng 1 ký hiệu góc vuông tại $H$ giữa $SC$ và $BH$, không sinh tia giả `perp_plane_ray:*`).
- **`camera_orientation`:** Góc nhìn chếch từ phía trước-phải nhìn rõ cạnh bên $SC$, đoạn vuông góc $BH \perp SC$ tại $H$, và nhãn `[(α)]` đặt ở góc ngoài bên phải của tấm mặt phẳng $(\alpha)$, tách biệt hoàn toàn khỏi `H`, `BH` và dấu góc vuông tại $H$.
- **`step_expectations`:**
  - **Bước 1–3:** Dựng khối chóp tứ giác $S.ABCD$ với đáy $ABCD$ và đường cao $SA \perp (ABCD)$.
  - **Bước 4–5:** Nổi bật cạnh bên $SC$ và xác định chân đường vuông góc $H \in SC$.
  - **Bước 6–7:** Dựng mặt phẳng $(\alpha)$ qua $B$ vuông góc với $SC$ tại $H$, nối $BH \perp SC$ và hiển thị ký hiệu góc vuông tại $H$.
- **`thumbnail_spec`:** SVG `viewBox="0 0 180 110"` vẽ hình chóp tứ giác $S.ABCD$, cạnh bên $SC$ màu teal đậm, tấm mặt phẳng $(\alpha)$ tím nhạt qua $B, H, D$ với nhãn `(α)` ở góc ngoài phải, đoạn vuông góc nét đứt $BH \perp SC$, dấu góc vuông tại $H$ và 6 nhãn `S, A, B, C, D, H`.

---

### 2.5. `the-tich-chop`
- **`sample_id`:** `the-tich-chop`
- **`title`:** Thể tích khối chóp và đường cao hạ từ đỉnh
- **`problem_text`:** Cho hình chóp tứ giác đều $S.ABCD$ có mặt đáy $ABCD$ và tâm đáy $H$. Hạ đường cao $SH$ vuông góc với mặt phẳng đáy $(ABCD)$ tại $H$ để xác định chiều cao và thể tích khối chóp.
- **`main_solid`:** Hình chóp tứ giác đều $S.ABCD$ (`chop`, `PYRAMID_LIKE`, $A=(0,0,0), B=(4,0,0), C=(4,4,0), D=(0,4,0), H=(2,2,0), S=(2,2,4)$).
- **`required_points`:** `A`, `B`, `C`, `D` (đỉnh đáy), `H` (tâm đáy / chân đường cao), `S` (đỉnh chóp).
- **`required_segments`:** Các cạnh đáy `AB, BC, CD, DA`; các cạnh bên `SA, SB, SC, SD`; đường cao `SH` (`sh`).
- **`required_planes`:** Mặt đáy `(ABCD)` (`day`, `BASE_REGION`).
- **`required_sections`:** Không có thiết diện cắt.
- **`required_witnesses`:** Chứng chỉ vuông góc `perpendicular_witness` trên `SH` (`from: "S"`, `foot_id: "H"`, `on: "day"`, `relation: "line_perp_plane"`) kèm ký hiệu góc vuông tại tâm đáy $H$.
- **`camera_orientation`:** Góc nhìn SGK đối xứng lệch nhẹ phương vị, tách rõ đỉnh $S$, tâm đáy $H$, 4 đỉnh đáy $A, B, C, D$ và đường cao nội tiếp $SH$.
- **`step_expectations`:**
  - **Bước 1:** Dựng khối chóp tứ giác đều $S.ABCD$, mặt đáy $(ABCD)$ và tâm đáy $H$.
  - **Bước 2:** Hạ đường cao $SH \perp (ABCD)$ tại $H$ và hiển thị chứng chỉ góc vuông tại $H$.
- **`thumbnail_spec`:** SVG `viewBox="0 0 180 110"` vẽ hình chóp tứ giác đều $S.ABCD$, mặt đáy tô màu amber nhạt, hai đường chéo đáy nét đứt giao tại tâm $H$, đường cao $SH$ nét đứt nổi bật kèm dấu góc vuông tại $H$ và 6 nhãn `S, A, B, C, D, H`.

---

### 2.6. `cau-cat-mat-phang`
- **`sample_id`:** `cau-cat-mat-phang`
- **`title`:** Mặt phẳng cắt mặt cầu theo đường tròn giao tuyến
- **`problem_text`:** Cho mặt cầu tâm $I$ bán kính $R = 5$ và mặt phẳng $(\alpha)$ cách tâm $I$ một khoảng $IH = 3$. Mặt phẳng $(\alpha)$ cắt mặt cầu theo đường tròn giao tuyến tâm $H$, bán kính $HM = 4$ với điểm $M$ nằm trên đường tròn giao tuyến.
- **`main_solid`:** Mặt cầu $(I, R)$ (`cau`, `curved_solid`, `curved_kind: "ball"`, $I=(0,0,0), R=5, H=(0,0,3), M=(4,0,3)$).
- **`required_points`:** `I` (tâm mặt cầu), `H` (hình chiếu của $I$ trên $(\alpha)$ / tâm đường tròn giao tuyến), `M` (điểm trên đường tròn giao tuyến); ở Bước 1 có điểm tham chiếu phụ `X` (`cau__ref_pt`) tự thu hồi khi hoàn tất.
- **`required_segments`:** Đoạn khoảng cách trục `IH` (`ih`), bán kính thiết diện `HM` (`hm`), bán kính mặt cầu `IM` (`im`).
- **`required_planes`:** Mặt phẳng cắt $(\alpha)$ (`mp`, $z = 3$).
- **`required_sections`:** Đường tròn giao tuyến $(H, r)$ (`giao`, `circle3`, `surface_role: "SECTION_REGION"`, $r = 4$).
- **`required_witnesses`:** Tam giác vuông đặc trưng $\triangle IHM$ vuông tại $H$ ($IH^2 + HM^2 = 3^2 + 4^2 = 5^2 = IM^2$) với chứng chỉ góc vuông `perpendicular_witness` tại $H$ (`from: "I"`, `foot_id: "H"`, `on: "mp"`).
- **`camera_orientation`:** Góc nhìn nghiêng mở rõ cả đường tròn xích đạo tham chiếu của mặt cầu, tấm mặt phẳng $(\alpha)$, elip phối cảnh của đường tròn giao tuyến $(H, r)$ và tam giác vuông $\triangle IHM$.
- **`step_expectations`:**
  - **Bước 1:** Dựng mặt cầu tâm $I$ bán kính $R$ (kèm bán kính tham chiếu ban đầu $IX$).
  - **Bước 2:** Dựng mặt phẳng $(\alpha)$ cắt mặt cầu.
  - **Bước 3:** Hạ đoạn vuông góc $IH \perp (\alpha)$ từ tâm $I$ đến tâm giao tuyến $H$.
  - **Bước 4:** Dựng đường tròn giao tuyến tâm $H$ trên mặt phẳng $(\alpha)$ và lấy điểm $M$ trên vành giao tuyến.
  - **Bước 5:** Nối bán kính thiết diện $HM$ và bán kính mặt cầu $IM$, khép kín tam giác vuông $\triangle IHM$ vuông tại $H$.
- **`thumbnail_spec`:** SVG `viewBox="0 0 180 110"` vẽ mặt cầu tâm `I`, mặt phẳng $(\alpha)$, đường tròn giao tuyến tô màu terracotta tâm `H`, điểm `M` trên vành, tam giác vuông $\triangle IHM$ vuông tại `H` và các nhãn `I, H, M, (α)`.

---

### 2.7. `cau-the-tich`
- **`sample_id`:** `cau-the-tich`
- **`title`:** Bán kính và cấu trúc khối cầu
- **`problem_text`:** Cho mặt cầu tâm $I$ và điểm $A$ nằm trên mặt cầu sao cho đoạn thẳng $IA$ biểu diễn bán kính $R$ của khối cầu. Quan sát tâm $I$, điểm $A$ trên mặt cầu và bán kính $IA$.
- **`main_solid`:** Khối cầu $(I, R)$ (`cau`, `curved_solid`, `curved_kind: "ball"`, $I=(0,0,0), A=(3,0,0), R=3$).
- **`required_points`:** `I` (tâm mặt cầu), `A` (điểm trên mặt cầu).
- **`required_segments`:** Bán kính `IA` (`ia`, độ dài $R = 3$).
- **`required_planes`:** Không có mặt phẳng cắt.
- **`required_sections`:** Đường tròn lớn tham chiếu (xích đạo / kinh tuyến) của mặt cầu.
- **`required_witnesses`:** Đoạn bán kính $IA$ nối từ tâm $I$ ra đúng điểm $A$ trên biên mặt cầu.
- **`camera_orientation`:** Góc nhìn SGK nhìn rõ đường tròn xích đạo, kinh tuyến và đoạn bán kính $IA$ không bị suy biến dọc tia nhìn.
- **`step_expectations`:**
  - **Bước 1:** Xác định tâm $I$, điểm $A$ trên mặt cầu và dựng khối cầu tâm $I$ bán kính $R = IA$.
  - **Bước 2:** Nối đoạn bán kính $IA$ từ tâm $I$ đến điểm $A$ trên mặt cầu.
- **`thumbnail_spec`:** SVG `viewBox="0 0 180 110"` vẽ mặt cầu tâm `I`, đường tròn lớn xích đạo + kinh tuyến, đoạn bán kính $IA = R$ màu terracotta và nhãn `I, A, R`.

---

### 2.8. `tru-thiet-dien-tron`
- **`sample_id`:** `tru-thiet-dien-tron`
- **`title`:** Thiết diện vuông góc trục của hình trụ
- **`problem_text`:** Cho hình trụ có trục $OO'$ và trung điểm $M$ của $OO'$. Mặt phẳng $(\alpha)$ đi qua $M$ và vuông góc với trục $OO'$ cắt hình trụ theo một đường tròn thiết diện tâm $M$.
- **`main_solid`:** Hình trụ đứng (`tru`, `curved_solid`, `curved_kind: "cylinder"`, $O=(0,0,0), O'=(0,0,4), R=2$).
- **`required_points`:** `O` (tâm đáy dưới), `O′` (tâm đáy trên), `M` (trung điểm trục $OO'$ / tâm thiết diện).
- **`required_segments`:** Trục hình trụ `OO′` (`truc`, đi qua $O, M, O'$).
- **`required_planes`:** Mặt phẳng cắt $(\alpha)$ (`mp`, $z = 2$, vuông góc với $OO'$ tại $M$).
- **`required_sections`:** Đường tròn thiết diện tâm $M$ (`giao`, `circle3`, `surface_role: "SECTION_REGION"`, $r = 2$).
- **`required_witnesses`:** Chứng chỉ vuông góc `perpendicular_witness` giữa trục $OO'$ và mặt phẳng $(\alpha)$ tại tâm $M$.
- **`camera_orientation`:** Góc nhìn nghiêng ($\approx 20^\circ$ so với mặt ngang) mở rõ 3 elip song song: đáy dưới $(O)$, thiết diện tròn $(M)$ ở chính giữa và đáy trên $(O')$ tách rời hoàn toàn.
- **`step_expectations`:**
  - **Bước 1:** Dựng hình trụ có hai tâm đáy $O, O'$ và trục $OO'$.
  - **Bước 2:** Xác định trung điểm $M$ trên trục $OO'$.
  - **Bước 3:** Dựng mặt phẳng $(\alpha)$ qua $M$ vuông góc với trục $OO'$ kèm ký hiệu góc vuông tại $M$.
  - **Bước 4:** Dựng đường tròn thiết diện tâm $M$ là giao của $(\alpha)$ với hình trụ.
- **`thumbnail_spec`:** SVG `viewBox="0 0 180 110"` vẽ hình trụ đứng với hai đáy tâm `O`, `O′`, trục `OO′`, tấm mặt phẳng $(\alpha)$ qua trung điểm `M`, thiết diện tròn tâm `M` tô màu terracotta, dấu góc vuông tại `M` và nhãn `O, O′, M, (α)`.

---

### 2.9. `tru-truc-xien`
- **`sample_id`:** `tru-truc-xien`
- **`title`:** Hình trụ và quan hệ giữa trục với bán kính đáy
- **`problem_text`:** Cho hình trụ có tâm hai đáy là $O$ và $O'$, điểm $A$ nằm trên đường tròn đáy tâm $O$. Biểu diễn trục $OO'$, bán kính đáy $OA$ và quan hệ vuông góc giữa trục $OO'$ với bán kính đáy $OA$ tại $O$.
- **`main_solid`:** Hình trụ trục xiên (`tru`, `curved_solid`, `curved_kind: "cylinder"`, $O=(0,0,0), O'=(1,2,2), A=(2,-1,0), R=2, h=3$).
- **`required_points`:** `O` (tâm đáy dưới), `O′` (tâm đáy trên), `A` (điểm trên đường tròn đáy dưới).
- **`required_segments`:** Trục hình trụ `OO′` (`oo`, $\overrightarrow{OO'} = (1,2,2)$) và bán kính đáy `OA` (`oa`, $\overrightarrow{OA} = (2,-1,0)$).
- **`required_planes`:** Hai mặt đáy tròn vuông góc với trục $OO'$ tại $O$ và $O'$.
- **`required_sections`:** Không có thiết diện cắt.
- **`required_witnesses`:** Chứng chỉ vuông góc `perpendicular_witness` (`relation: "perpendicular_lines"`, $\overrightarrow{OO'}\cdot\overrightarrow{OA} = 1\cdot 2 + 2\cdot(-1) + 2\cdot 0 = 0$) kèm ký hiệu góc vuông tại tâm đáy $O$.
- **`camera_orientation`:** Hướng nhìn từ phía trên nắp $(O')$ ($\vec{u}\cdot\vec{d} \in [0.25, 0.56]$ và $\min(\text{moDay}_0, \text{moDay}_1) \ge 0.22$, $h_{\text{chiếu}} \ge 1.75\,b_{\text{nhỏ}}$): nắp trên $(O')$ thấy toàn bộ bằng nét liền, đáy dưới $(O)$ có cung trước nét liền / cung sau nét đứt, hai elip đáy tách rời hoàn toàn và tam giác vuông tại $O$ giữa $OO'$ và $OA$ mở rõ.
- **`step_expectations`:**
  - **Bước 1:** Dựng khối trụ có hai tâm đáy $O, O'$ và điểm $A$ trên đường tròn đáy tâm $O$.
  - **Bước 2:** Nối trục $OO'$, bán kính đáy $OA$ và hiển thị ký hiệu góc vuông tại $O$.
- **`thumbnail_spec`:** SVG `viewBox="0 0 180 110"` vẽ hình trụ trục xiên với đáy dưới tâm `O`, đáy trên tâm `O′` lệch phải theo phương trục xiên, hai đường sinh biên song song, trục `OO′`, bán kính đáy `OA`, dấu góc vuông tại `O` và nhãn `O, O′, A`.

---

### 2.10. `non-thiet-dien-truc`
- **`sample_id`:** `non-thiet-dien-truc`
- **`title`:** Thiết diện qua trục của hình nón
- **`problem_text`:** Cho hình nón đỉnh $S$, tâm đáy $O$. Mặt phẳng $(\alpha)$ đi qua trục $SO$ cắt hình nón theo thiết diện là tam giác cân $SAB$, với $AB$ là đường kính của đường tròn đáy.
- **`main_solid`:** Hình nón tròn xoay (`non`, `curved_solid`, `curved_kind: "cone"`, $O=(0,0,0), S=(0,0,4), A=(3,0,0), B=(-3,0,0), R=3, h=4$).
- **`required_points`:** `S` (đỉnh nón), `O` (tâm đáy), `A`, `B` (hai đầu đường kính đáy).
- **`required_segments`:** Đường cao / trục `SO` (`so`), hai đường sinh biên của thiết diện `SA`, `SB`, đường kính đáy `AB` (gồm hai bán kính `OA`, `OB`).
- **`required_planes`:** Mặt phẳng qua trục $(\alpha)$ (`mp`, $y = 0$).
- **`required_sections`:** Thiết diện qua trục $\triangle SAB$ (`td`, `section` / `polygon3`, đỉnh `S, A, B`).
- **`required_witnesses`:** Chứng chỉ góc vuông tại tâm đáy $O$ giữa đường cao $SO$ và đường kính đáy $AB$.
- **`camera_orientation`:** Hướng nhìn trực diện rộng vào mặt phẳng thiết diện qua trục (`|dir_y| >= 0.72`), sao cho tam giác cân $\triangle SAB$ mở rộng tối đa, **cả hai đường sinh bên $SA, SB$ hiển thị bằng nét liền**, còn đường kính đáy $AB$ bên trong khối nón hiển thị bằng nét đứt.
- **`step_expectations`:**
  - **Bước 1:** Dựng hình nón đỉnh $S$, tâm đáy $O$ và đường cao $SO$.
  - **Bước 2:** Dựng mặt phẳng $(\alpha)$ đi qua trục $SO$ và cắt đường tròn đáy tại hai điểm đối tâm $A, B$.
  - **Bước 3:** Dựng thiết diện tam giác cân $\triangle SAB$ (hai cạnh bên $SA, SB$ nét liền, cạnh đáy $AB$ nét đứt, miền $\triangle SAB$ tô màu terracotta).
- **`thumbnail_spec`:** SVG `viewBox="0 0 180 110"` vẽ hình nón đỉnh `S` tâm đáy `O`, mặt phẳng qua trục $(\alpha)$, thiết diện tam giác cân $\triangle SAB$ tô màu terracotta với hai đường sinh `SA, SB` nét liền, đường kính đáy `AB` nét đứt, đường cao `SO` nét đứt kèm dấu góc vuông tại `O` và nhãn `S, O, A, B, (α)`.

---

### 2.11. `non-duong-sinh`
- **`sample_id`:** `non-duong-sinh`
- **`title`:** Đường sinh, đường cao và bán kính đáy hình nón
- **`problem_text`:** Cho hình nón đỉnh $S$, tâm đáy $O$ và điểm $A$ trên đường tròn đáy. Biểu diễn tam giác vuông $SOA$ vuông tại $O$ tạo bởi đường cao $SO$, bán kính đáy $OA$ và đường sinh $SA$.
- **`main_solid`:** Hình nón tròn xoay (`non`, `curved_solid`, `curved_kind: "cone"`, $O=(0,0,0), S=(0,0,4), A=(3,0,0), R=3, h=4$).
- **`required_points`:** `S` (đỉnh nón), `O` (tâm đáy), `A` (điểm trên đường tròn đáy).
- **`required_segments`:** Đường cao `SO` (`so`, $h = 4$), bán kính đáy `OA` (`oa`, $R = 3$), đường sinh `SA` (`sa`, $l = 5$).
- **`required_planes`:** Mặt phẳng đáy chứa đường tròn $(O, R)$.
- **`required_sections`:** Miền tam giác vuông đặc trưng $\triangle SOA$ (`soa`).
- **`required_witnesses`:** Chứng chỉ vuông góc `perpendicular_witness` tại tâm đáy $O$ (`from: "S"`, `foot_id: "O"`, `on: "oa"`, $\angle SOA = 90^\circ$, hệ thức $SA^2 = SO^2 + OA^2$).
- **`camera_orientation`:** Hướng nhìn mở rộng mặt phẳng tam giác vuông $\triangle SOA$ (`|dir_y| >= 0.65`), đặt điểm $A$ về phía bên phải để đường sinh $SA$ trùng/tách rõ bên sườn phải và góc vuông tại $O$ không bị biến dạng.
- **`step_expectations`:**
  - **Bước 1:** Dựng hình nón đỉnh $S$, tâm đáy $O$ và điểm $A$ trên đường tròn đáy.
  - **Bước 2:** Nối đường cao $SO$, bán kính đáy $OA$, đường sinh $SA$ và hiển thị tam giác vuông $\triangle SOA$ vuông tại $O$.
- **`thumbnail_spec`:** SVG `viewBox="0 0 180 110"` vẽ hình nón đỉnh `S`, tâm đáy `O`, điểm `A` trên vành phải, miền tam giác vuông $\triangle SOA$ tô màu teal nhạt, đường cao `SO` nét đứt, bán kính `OA`, đường sinh `SA` tô màu terracotta, dấu góc vuông tại `O` và nhãn `S, O, A`.

---

## 3. Đề xuất 6 bài toán hình học không gian THPT tổng hợp (§9)

> **Lưu ý phạm vi (§9):** Các bài toán dưới đây được thiết kế và phân loại khả năng hỗ trợ của hệ thống để chuẩn bị mở rộng thư viện ở giai đoạn tiếp theo, **chưa thay thế 11 bài hiện có khi chưa có phê duyệt của người dùng**.

### 3.1. Bài đề xuất 1: Thiết diện hình thang vuông song song cạnh bên đường cao (`chop-thiet-dien-song-song-sa`)
- **Phân loại kỹ thuật:** `SUPPORTED_BY_CURRENT_KERNEL`
- **Đề bài chuẩn THPT:** Cho hình chóp $S.ABCD$ có đáy $ABCD$ là hình chữ nhật ($AB = 4a, BC = 3a$), cạnh bên $SA \perp (ABCD)$ và $SA = 4a$. Điểm $M$ nằm trên cạnh $AB$ sao cho $AM = \frac{1}{2}AB$. Mặt phẳng $(\alpha)$ đi qua $M$, song song với $SA$ và $BC$, cắt $CD, SD, SB$ lần lượt tại $N, P, Q$. Dựng thiết diện $MNPQ$ và tính diện tích thiết diện.
- **Đặc tả đối tượng 3D:**
  - `main_solid`: Hình chóp $S.ABCD$ (`PYRAMID_LIKE`).
  - `required_points`: $S, A, B, C, D$ và 4 đỉnh thiết diện $M \in AB, N \in CD, P \in SD, Q \in SB$.
  - `required_segments`: Các cạnh chóp + 4 cạnh thiết diện $MN, NP, PQ, QM$ (trong đó $QM \parallel SA \Rightarrow QM \perp (ABCD)$ và $MN \parallel BC \perp AB \Rightarrow QM \perp MN$).
  - `required_planes`: Mặt phẳng cắt $(\alpha)$ đứng ($x = 2$).
  - `required_sections`: Thiết diện hình thang vuông $MNPQ$ vuông tại $M$ và $N$.
  - `required_witnesses`: Ký hiệu góc vuông tại $A$ ($SA \perp (ABCD)$) và tại $M, N$ trên thiết diện hình thang vuông $MNPQ$.

### 3.2. Bài đề xuất 2: Thiết diện chéo và khoảng cách từ đỉnh đáy trong lăng trụ đứng (`lang-tru-tam-giac-thiet-dien-cheo`)
- **Phân loại kỹ thuật:** `SUPPORTED_BY_CURRENT_KERNEL`
- **Đề bài chuẩn THPT:** Cho hình lăng trụ đứng $ABC.A'B'C'$ có đáy $ABC$ là tam giác vuông tại $A$ ($AB = 3a, AC = 4a$) và cạnh bên $AA' = 4a$. Dựng mặt phẳng $(A'BC)$ cắt lăng trụ theo thiết diện $\triangle A'BC$, hạ $AK \perp BC$ tại $K$ và $AH \perp A'K$ tại $H$ để biểu diễn khoảng cách từ $A$ đến mặt phẳng $(A'BC)$.
- **Đặc tả đối tượng 3D:**
  - `main_solid`: Hình lăng trụ đứng $ABC.A'B'C'$ (`PRISM_LIKE`).
  - `required_points`: $A, B, C, A', B', C'$, chân đường cao đáy $K \in BC$ và chân khoảng cách $H \in A'K$.
  - `required_segments`: Các cạnh lăng trụ, cạnh thiết diện $A'B, A'C, BC$, đoạn trung gian $AK, A'K$ và đoạn khoảng cách $AH$.
  - `required_planes`: Mặt phẳng $(A'BC)$.
  - `required_sections`: Thiết diện tam giác $\triangle A'BC$.
  - `required_witnesses`: Ba chứng chỉ góc vuông: $\angle BAC = 90^\circ$, $AK \perp BC$ tại $K$, và $AH \perp (A'BC)$ tại $H$ (`two-step orthogonal projection`).

### 3.3. Bài đề xuất 3: Thiết diện lục giác đều của hình lập phương (`lap-phuong-thiet-dien-luc-giac-deu`)
- **Phân loại kỹ thuật:** `SUPPORTED_BY_CURRENT_KERNEL`
- **Đề bài chuẩn THPT:** Cho hình lập phương $ABCD.A'B'C'D'$ cạnh $2a$. Mặt phẳng $(\alpha)$ đi qua trung điểm $M, N, P$ của các cạnh $AB, BC, DD'$ cắt hình lập phương theo một thiết diện lục giác đều $MNPQRS$ vuông góc với đường chéo chính $B'D$.
- **Đặc tả đối tượng 3D:**
  - `main_solid`: Hình lập phương $ABCD.A'B'C'D'$ (`PRISM_LIKE`).
  - `required_points`: 8 đỉnh hình lập phương + 6 trung điểm $M \in AB, N \in BC, Q \in CC', R \in C'D', P \in DD', S \in AA'$ + giao điểm tâm $I = B'D \cap (\alpha)$.
  - `required_segments`: 12 cạnh hình lập phương, 6 cạnh thiết diện lục giác đều và đường chéo chính $B'D$.
  - `required_planes`: Mặt phẳng $(\alpha)$ có pháp tuyến $\vec{n} = (1, -1, 1)$.
  - `required_sections`: Thiết diện lục giác đều 6 đỉnh trên 6 mặt của hình lập phương (đã được kiểm chứng trong `axo-cross-family-scene3d-acceptance.test.tsx`).
  - `required_witnesses`: Quan hệ vuông góc $B'D \perp (\alpha)$ tại tâm đối xứng $I$ của lục giác đều.

### 3.4. Bài đề xuất 4: Mặt cầu ngoại tiếp hình chóp có cạnh bên vuông góc với đáy vuông (`chop-noi-tiep-mat-cau-tam-ngoai-tiep`)
- **Phân loại kỹ thuật:** `SUPPORTED_BY_CURRENT_KERNEL`
- **Đề bài chuẩn THPT:** Cho hình chóp $S.ABC$ có $SA \perp (ABC)$ và tam giác đáy $ABC$ vuông tại $B$. Xác định tâm $I$ là trung điểm cạnh bên $SC$ và dựng mặt cầu ngoại tiếp hình chóp $S.ABC$ bán kính $R = IA = IB = IC = IS = \frac{SC}{2}$.
- **Đặc tả đối tượng 3D:**
  - `main_solid`: Hình chóp $S.ABC$ nội tiếp trong khối cầu ngoại tiếp $(I, R)$ (`curved_solid` `ball` không che khuất cạnh đa diện bên trong nhờ `curvedSilhouetteVolume`).
  - `required_points`: $S, A, B, C$, tâm mặt cầu ngoại tiếp $I$ (trung điểm $SC$) và tâm đường tròn ngoại tiếp đáy $O$ (trung điểm $AC$).
  - `required_segments`: Các cạnh chóp $SA, SB, SC, AB, BC, AC$, trục đối xứng $IO \parallel SA$ và các bán kính $IS, IA, IB, IC$.
  - `required_planes`: Mặt phẳng đáy $(ABC)$.
  - `required_sections`: Đường tròn ngoại tiếp đáy $(O, r)$ đi qua $A, B, C$.
  - `required_witnesses`: Ký hiệu góc vuông tại $A$ ($SA \perp (ABC)$), tại $B$ ($\angle ABC = 90^\circ$) và tại $O$ ($IO \perp (ABC)$).

### 3.5. Bài đề xuất 5: Thiết diện qua đỉnh hình nón không đi qua trục (`non-thiet-dien-qua-dinh-day-cung`)
- **Phân loại kỹ thuật:** `NEEDS_REPRESENTATION_EXTENSION`
- **Đề bài chuẩn THPT:** Cho hình nón đỉnh $S$, tâm đáy $O$, bán kính đáy $R = 3a$ và đường cao $SO = 4a$. Một mặt phẳng $(\alpha)$ đi qua đỉnh $S$ cắt đường tròn đáy theo dây cung $AB = 2a\sqrt{5}$. Hạ $OH \perp AB$ tại trung điểm $H$ của dây cung $AB$ và nối đường cao $SH$ của thiết diện cân $\triangle SAB$.
- **Đặc tả đối tượng 3D & lý do phân loại:**
  - `main_solid`: Hình nón đỉnh $S$, tâm đáy $O$.
  - `required_points`: $S, O, A, B$ và trung điểm dây cung $H \in AB$ ($H \neq O$).
  - `required_sections`: Tam giác cân $\triangle SAB$ có hai cạnh bên là đường sinh $SA, SB$ và cạnh đáy là dây cung $AB$ không qua tâm $O$.
  - `required_witnesses`: Tam giác vuông $\triangle SOH$ vuông tại $O$ và $OH \perp AB, SH \perp AB$ tại $H$ (góc nhị diện $\angle SHO$ giữa $(\alpha)$ và đáy).
  - **Yêu cầu mở rộng biểu diễn (`NEEDS_REPRESENTATION_EXTENSION`):** Kernel hiện tại tính được tọa độ chính xác của $S, O, A, B, H$, nhưng bộ phân tách nét khuất của mặt phẳng cắt xiên qua đỉnh nón cần bổ sung quy tắc ưu tiên hiển thị đồng thời tam giác nhân chứng $\triangle SOH$ bên trong nón và miền thiết diện $\triangle SAB$ mà không làm rối nhãn quanh cặp điểm gần nhau $(O, H)$.

### 3.6. Bài đề xuất 6: Thiết diện elip của hình trụ cắt bởi mặt phẳng nghiêng (`tru-cat-mat-phang-nghieng-elip`)
- **Phân loại kỹ thuật:** `NEEDS_KERNEL_EXTENSION`
- **Đề bài chuẩn THPT:** Cho hình trụ đứng có trục $OO' = 6a$ và bán kính đáy $R = 2a$. Mặt phẳng $(\alpha)$ đi qua tâm $I$ của trục $OO'$ và tạo với mặt phẳng đáy một góc $30^\circ$, cắt toàn bộ mặt xung quanh hình trụ theo một thiết diện hình elip $(E)$. Xác định độ dài trục lớn $AB$, trục nhỏ $CD$ và diện tích thiết diện elip $(E)$.
- **Đặc tả đối tượng 3D & lý do phân loại:**
  - `main_solid`: Hình trụ đứng trục $OO'$.
  - `required_points`: $O, O'$, tâm thiết diện $I$, hai đỉnh trục lớn $A, B$ và hai đỉnh trục nhỏ $C, D$ trên mặt bên hình trụ.
  - `required_sections`: Đối tượng `ellipse3` (`render: "ellipse"`, `surface_role: "SECTION_REGION"`).
  - **Yêu cầu mở rộng Kernel (`NEEDS_KERNEL_EXTENSION`):** Tầng hiển thị `Scene3D` đã hỗ trợ render `ellipse3` (`buildObject3D` + `dongBoNetDayManHinh`), nhưng `TypedFactNext /2` và `Planner /26` trong Backend cần mở rộng hàm lập kế hoạch tự động từ câu đề tiếng Việt cho bài toán tính diện tích và bán trục của giao tuyến elip giữa mặt phẳng nghiêng và mặt trụ.
