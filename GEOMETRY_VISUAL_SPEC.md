# GEOMETRY VISUAL SPECIFICATION — AXO SEMANTIC GEOMETRY, OXYZ & 11 THPT SAMPLES

> **Tài liệu đặc tả hình học & quy tắc đồng bộ trực quan (Scene3D ↔ 2D Illustration System ↔ Các bước dựng)**
> - **Worktree:** `D:/Documents/projects/axo-geometry-library` (`feat/axo-geometry-library-verification`)
> - **Nguồn dữ liệu gốc có thẩm quyền (Single Source of Truth):**
>   - **11 bài THPT nâng cao công khai (`PUBLIC_GEOMETRY_SAMPLES`):** `backend/scripts/build_advanced_geometry_samples.py` → `frontend/src/data/advanced-geometry-samples.json`.
>   - **11 fixture hồi quy lịch sử (`LEGACY_GEOMETRY_SAMPLES`):** `backend/scripts/build_geometry_samples.py` → `frontend/src/data/geometry-samples.json`.
>   - **Chuỗi trình bày tất định:** `Scene3D` → `withSubEntities` → `buildPedagogicalConstructionPlan` → `veKhongGian` → `Scene3DWorkspace`.
> - **Hệ thống hình minh họa 2D hai tầng (`frontend/src/components/geometry2d/` & `SamplePreview.tsx`):**
>   1. **Tier A — Geometry Family Icons (`family-icons.tsx`):** Bộ 4 icon vector `24×24` tối giản (`pyramid`, `sphere`, `cylinder`, `cone`) + 1 icon đa diện trung tính (`neutral`).
>   2. **Tier B — Composable 2D Templates (`templates.tsx` & `primitives.tsx`):** Bộ 19 template hình học phẳng 2D sư phạm theo chuẩn SGK THPT, đồng bộ bảng màu ngữ nghĩa với `Scene3D`.
>   3. **Template Resolver & Safe Fallback (`resolver.ts`):** Tự động đối chiếu cấu trúc `Scene3D` để chọn đúng template dạng bài và chỉ gắn nhãn đã xác minh (`mode="verified"`), fallback an toàn sang `"generic"` / `"family-icon"` / `"fallback-neutral"`.

---

## 0. Chuẩn hóa màu ngữ nghĩa, ký hiệu toán học, hệ trục Oxyz & thứ tự ưu tiên đa vai trò

### 0.1. Bảng màu & ký hiệu ngữ nghĩa dùng chung (`PHONG_CACH_SCENE3D`, `GEO2D_TOKENS`, `DESIGN.md`, `tokens.css`, `matphang.html`)

| Vai trò toán học | Mã màu chuẩn | Kiểu nét / độ đục | Quy tắc kiểm chứng & hiển thị |
|---|---|---|---|
| **Đường cao, đoạn vuông góc chung, quan hệ vuông góc đã chứng nhận** | Teal `#0F766E` | Nét liền `2.1px` (thấy) / nét đứt (khuất); ô vuông `⊥` `16–22px` | Chỉ kích hoạt khi có `CONSTRUCT_HEIGHT`, `perpendicular_witness` hợp lệ hoặc chứng cứ tích vô hướng bằng `0` trong `chart_metric` (fail-closed khi `UNVERIFIED`). |
| **Đường thẳng không gian, cặp đường chéo nhau, đoạn mục tiêu không vuông góc & cung góc đang xét** | Cobalt `#2563EB` | Nét liền `2.2px` + phần kéo dài nét đứt mảnh; quạt góc 3D độ đục `0.16` + cung tròn `2.1px` | Áp dụng cho đường thẳng khảo sát (`d`, `Δ`, hai đường chéo nhau `SC, BD`), đoạn khoảng cách mục tiêu không vuông góc (`OM`), và cung góc 3D đã xác minh (đường–đường, đường–mặt, mặt–mặt, góc phẳng nhị diện). |
| **Thiết diện mục tiêu & giao tuyến cắt khối** | Terracotta `#C85A32` | Viền `2.8px`, miền tô độ đục `0.26` | Chỉ dùng cho thiết diện / giao tuyến thực sự cắt khối đa diện hoặc khối tròn xoay (không dùng cho vết mặt phẳng chắn trục Oxyz). |
| **Mặt phẳng hình học & vết mặt phẳng tọa độ** | Violet `#6D28D9` | Viền `1.6px`, miền tô độ đục `0.06–0.08` | Dùng thống nhất cho `plane3` và đa giác chắn trục tọa độ (vd `ABC` của `(P)` trong không gian `Oxyz`). |
| **Đường tròn / mặt cầu nội tiếp & ngoại tiếp** | Nội tiếp: Amber `#D97706` · Đường tròn ngoại tiếp: Cobalt `#2563EB` · Mặt cầu ngoại tiếp: Teal `#0F766E` | Vành hai lượt thấy/khuất theo camera | Giữ tách biệt `#D97706` (nội tiếp) và `#2563EB` (ngoại tiếp) theo đúng mã vẽ 3D của `matphang.html:1798,1810` để hai đường tròn đồng tâm trên cùng mặt đáy không trùng màu. |
| **Cạnh khối cấu trúc & đường phụ trợ** | Trung tính `#1E293B` (thấy) / `#64748B` (khuất & phụ trợ) | Cạnh thấy `2.2px`, cạnh khuất nét đứt `1.5px`, đường phụ `1.65px` | Các cạnh bên lăng trụ đứng / hình hộp (`CONSTRUCT_LATERAL_BOUNDARY` không gắn `CONSTRUCT_HEIGHT`) giữ màu cấu trúc `#1E293B` kèm một dấu `⊥` đại diện tại đáy. |

### 0.2. Chính sách ưu tiên hiển thị một nét duy nhất (Single-Stroke Multi-Role Priority)

Khi nhiều thực thể hình học cùng nằm trên một cạnh/đường, hệ thống chuyển màu ngữ nghĩa lên chủ sở hữu duy nhất theo thứ tự ưu tiên giảm dần và nhường phần trùng (`doanNhuongCanh`, `yieldColinear`, `yieldStart`), tuyệt đối không tô đè nhiều lớp gây nhòe nét:

1. **Hạng 4 (cao nhất):** Cạnh thiết diện mục tiêu / giao tuyến cắt khối (`#C85A32`).
2. **Hạng 3:** Đường cao / đoạn vuông góc chứng nhận khoảng cách (`#0F766E`, vd `SA ⊥ (ABCD)` hoặc đoạn vuông góc chung `PQ`).
3. **Hạng 2:** Đường thẳng không gian / đoạn mục tiêu đang xét (`#2563EB`, vd cạnh `SC` đóng vai trò một trong hai đường chéo nhau).
4. **Hạng 1:** Cạnh biên cấu trúc thông thường của khối (`#1E293B`).
5. **Hạng 0:** Tia dương hệ trục tọa độ `Ox, Oy, Oz` (`#475569` — tự động nhường đoạn `[0, h]` từ gốc `O` khi có đường cao hoặc đoạn thẳng chính nằm trùng trên trục).

### 0.3. Chính sách hệ trục tọa độ `Oxyz` (`isExplicitOxyzCoordinateScene` & `dungTrucOxyzSuPham`)

- **Tự động nhận diện theo ngữ cảnh toán học:** Chỉ tự bật `showAxes = true` cho bài toán tọa độ `Oxyz` tường minh (`coordinate_frame`, gốc `O(0;0;0)`, đối tượng hoặc đề bài nêu hệ tọa độ `Oxyz` / tọa độ bộ ba `(x; y; z)`); tự động tắt (`false`) cho các bài hình học tổng hợp thuần túy.
- **Biểu diễn 3D chuẩn mực:** Đầy đủ 3 trục `Ox, Oy, Oz` gắn trong không gian thế giới 3D (xoay cùng mô hình, không cố định 2D HUD), gồm phần âm nét đứt `#64748B`, phần dương nét liền `#475569`, mũi tên nón chỉ chiều dương, ký hiệu `x, y, z` tách rời đầu mũi tên và nhãn gốc `O` (tự nhường khi cảnh đã có điểm `O` tường minh).
- **Bảo toàn Camera Framing:** Nhóm `truc_oxyz_su_pham` gắn `userData.voHan = true` để thuật toán căn khung camera luôn tính trên tập đối tượng hình học hữu hạn của bài toán, không đẩy camera lùi xa.

### 0.4. Danh mục 11 bài THPT nâng cao công khai hiện hành (`PUBLIC_GEOMETRY_SAMPLES`)

| # | Mã bài (`id`) | Dạng toán & quan hệ trọng tâm | Hệ trục `Oxyz` mặc định | Template 2D (`resolver.ts`) |
|---|---|---|---|---|
| 1 | `chop-thiet-dien-ba-diem` | Thiết diện hình chóp cắt bởi mặt phẳng `(MNP)` qua 3 trung điểm | Tắt | `pyramid.section` |
| 2 | `lap-phuong-thiet-dien-bat-ky` | Thiết diện lục giác đều của hình lập phương cắt bởi `(MNP)` | Tắt | `cube.plane-section` |
| 3 | `khoang-cach-diem-mat-phang-nghieng` | Hình chiếu `H` và khoảng cách `d(A, (SBC))` từ chân đường cao đến mặt bên nghiêng | Tắt | `pyramid.point-to-plane-distance` |
| 4 | `goc-nhi-dien-hai-mat-phang` | Góc phẳng nhị diện `∠SHA` giữa mặt bên `(SBC)` và đáy `(ABC)` | Tắt | `pyramid.dihedral-angle` |
| 5 | `khoang-cach-hai-duong-cheo-nhau` | Đoạn vuông góc chung `PQ` và khoảng cách giữa hai đường chéo nhau `SC, BD` | Tắt | `pyramid.skew-lines-distance` |
| 6 | `lang-tru-tam-giac-thiet-dien` | Thiết diện ngũ giác của lăng trụ đứng tam giác cắt bởi `(NPQ)` | Tắt | `prism.plane-section` |
| 7 | `mat-cau-cat-mat-phang` | Mặt phẳng `(P)` cắt mặt cầu `(S)` trong `Oxyz` theo đường tròn tâm `H` | **Bật** | `sphere.plane-section` |
| 8 | `oxyz-giao-diem-duong-mat` | Giao điểm `M = d ∩ (P)`, hình chiếu `H` của `E` lên `(P)` và độ dài `OM` trong `Oxyz` | **Bật** | `oxyz.line-plane-intersection` |
| 9 | `mat-phang-tiep-xuc-mat-cau` | Mặt phẳng tiếp diện `(P)` tiếp xúc mặt cầu `(S)` tại tiếp điểm `A` trong `Oxyz` | **Bật** | `sphere.tangent-plane` |
| 10 | `hinh-non-cat-song-song-day` | Mặt phẳng song song đáy cắt hình nón theo đường tròn thiết diện | Tắt | `cone.parallel-section` |
| 11 | `chop-mat-cau-ngoai-tiep` | Tâm `I` (giao các mặt phẳng trung trực) và mặt cầu ngoại tiếp hình chóp `S.ABCD` | Tắt | `pyramid.circumscribed-sphere` |

---

## 1. Phụ lục bảo toàn: Bảng tổng hợp 11 fixture hồi quy lịch sử (`LEGACY_GEOMETRY_SAMPLES`)

> **Giải trình số bước dựng (§3.A2 — Mâu thuẫn 2):**
> - **Số sự kiện gốc (`scene3d.events.length`):** số sự kiện `CREATE` mức thấp do Kernel phát ra trong `geometry-samples.json`.
> - **Số bước dựng hiển thị cho người học (`stepCountOfEnvelope`):** số bước sư phạm (`buildPedagogicalConstructionPlan(withSubEntities(scene3d)).steps.length`) được dùng thống nhất tại **Trang chủ (`SessionCard`)**, **Thư viện (`LibraryView`)** và **Workspace (`SimulationWorkspace`)**.

| # | Mã mẫu (`id`) | Tên hiển thị (`title`) | Nhóm (`category`) | Sự kiện Kernel (`events.length`) | Bước dựng người học (`stepCountOfEnvelope`) | Nhãn điểm thực tế (`point3`) | Ký hiệu mặt phẳng (`plane3`) |
|---|---|---|---|---|---|---|---|
| 1 | `thiet-dien-chop` | Thiết diện hình chóp cắt bởi mặt phẳng | Hình chóp | `16` | **`10`** | `S, A, B, C, D, M, N, P, Q` | `(MNP)` |
| 2 | `mat-cheo-sac` | Mặt phẳng chéo `(SAC)` chia khối chóp | Hình chóp | `10` | **`6`** | `S, A, B, C, D` | `(SAC)` |
| 3 | `vuong-goc-chop` | Chứng minh đường thẳng vuông góc mặt phẳng | Hình chóp | `8` | **`5`** | `S, A, B, C, D` | `(SAB)` |
| 4 | `mp-vuong-goc-duong` | Mặt phẳng qua điểm và vuông góc đường thẳng | Hình chóp | `9` | **`7`** | `S, A, B, C, D, H` | `(α)` |
| 5 | `the-tich-chop` | Thể tích khối chóp và khoảng cách | Hình chóp | `8` | **`4`** | `S, A, B, C, D` | — *(đáy `ABCD`)* |
| 6 | `cau-cat-mat-phang` | Mặt phẳng cắt mặt cầu theo đường tròn | Mặt cầu | `6` | **`5`** | `I, H, M` | `(P)` |
| 7 | `cau-the-tich` | Diện tích mặt cầu và thể tích khối cầu | Mặt cầu | `4` | **`1`** | `I, A` | — |
| 8 | `tru-thiet-dien-tron` | Thiết diện vuông góc trục của hình trụ | Hình trụ | `7` | **`6`** | `O, O′, M` | `(α)` |
| 9 | `tru-truc-xien` | Hình trụ có trục `OO′` và bán kính đáy `OA` | Hình trụ | `5` | **`3`** | `O, O′, A` | — |
| 10 | `non-thiet-dien-truc` | Thiết diện qua trục của hình nón | Hình nón | `5` | **`5`** | `S, O, A, B` | — |
| 11 | `non-duong-sinh` | Đường sinh, chiều cao và bán kính đáy hình nón | Hình nón | `6` | **`4`** | `S, O, A` | — |

---

## 2. Đặc tả chi tiết & bất biến toán học từng bài mô phỏng

### 2.1. `thiet-dien-chop` — Thiết diện hình chóp cắt bởi mặt phẳng `(MNP)`
- **Đề bài thực tế (`problemText`):**
  > Cho hình chóp `S.ABCD` có đáy `ABCD` là hình vuông cạnh `2`, `SA` vuông góc với mặt phẳng đáy và `SA = 4`. Gọi `M, N, P` lần lượt là trung điểm của `SA, SB, SC`. Mặt phẳng `(MNP)` cắt cạnh `SD` tại `Q`. Hãy dựng thiết diện của hình chóp cắt bởi mặt phẳng `(MNP)`.
- **Tọa độ chính xác (`Scene3D`):**
  - Đáy hình vuông cạnh $2$: $A=(0,0,0),\; B=(2,0,0),\; C=(2,2,0),\; D=(0,2,0)$.
  - Đỉnh: $S=(0,0,4)$ với $SA \perp (ABCD)$ tại $A$, $SA = 4$.
  - Trung điểm & giao điểm thiết diện ở cao độ $z = 2$:
    $$M=(0,0,2),\quad N=(1,0,2),\quad P=(1,1,2),\quad Q=(0,1,2)$$
  - Mặt phẳng cắt: `plane3:mp` có ký hiệu `notation = "(MNP)"`, phương trình $z = 2$.
  - Thiết diện: tứ giác $MNPQ$ (hình vuông cạnh $1$ song song với đáy $ABCD$).
- **Quy tắc hiển thị & độ che khuất:**
  - Nét liền: $SB, SC, SD, BC, CD$ và hai cạnh thiết diện phía trước $NP, PQ$.
  - Nét đứt: $SA, AB, AD$ và hai cạnh thiết diện bị che $MN, MQ$.
  - Ký hiệu mặt phẳng: `(MNP)` đặt ở diềm ngoài tấm mặt phẳng cắt, không đè vào miền trong thiết diện.

---

### 2.2. `mat-cheo-sac` — Mặt phẳng chéo `(SAC)` chia khối chóp
- **Đề bài thực tế (`problemText`):**
  > Cho hình chóp `S.ABCD` có đáy `ABCD` là hình vuông cạnh `2`, `SA` vuông góc với mặt phẳng đáy và `SA = 4`. Hãy dựng mặt phẳng chéo `(SAC)` và thiết diện của hình chóp cắt bởi `(SAC)`.
- **Tọa độ chính xác (`Scene3D`):**
  - $A=(0,0,0),\; B=(2,0,0),\; C=(2,2,0),\; D=(0,2,0),\; S=(0,0,4)$.
  - Mặt phẳng chéo `plane3:sac` có ký hiệu `notation = "(SAC)"`, pháp tuyến $(1,-1,0)$.
  - Thiết diện `section:thiet_dien`: tam giác vuông $\triangle SAC$ vuông tại $A$ ($SA = 4,\; AC = 2\sqrt{2}$).
- **Quy tắc hiển thị & độ che khuất:**
  - Nét liền: $SB, SC, SD, BC, CD$.
  - Nét đứt: $SA, AB, AD$ và đường chéo đáy $AC$ nằm bên trong khối chóp.
  - Ký hiệu mặt phẳng: `(SAC)`.

---

### 2.3. `vuong-goc-chop` — Góc giữa đường thẳng `BC` và mặt phẳng `(SAB)`
- **Đề bài thực tế (`problemText`):**
  > Cho hình chóp `S.ABCD` có đáy `ABCD` là hình vuông cạnh `2`, `SA` vuông góc với mặt phẳng đáy và `SA = 4`. Xét đường thẳng `BC` và mặt phẳng `(SAB)`: hãy dựng hình rồi cho biết góc giữa chúng.
- **Tọa độ chính xác (`Scene3D`):**
  - $A=(0,0,0),\; B=(2,0,0),\; C=(2,2,0),\; D=(0,2,0),\; S=(0,0,4)$.
  - Mặt phẳng `plane3:sab` có ký hiệu `notation = "(SAB)"` ($y = 0$).
  - Đường thẳng `line3:bc` có ký hiệu `notation = "BC"` qua $B(2,0,0), C(2,2,0)$.
  - Vì $BC \perp AB$ và $BC \perp SA \implies BC \perp (SAB)$ tại $B$, nên $\cos^2(BC, (SAB)) = 0$ (góc bằng $90^\circ$).
- **Quy tắc hiển thị & độ che khuất:**
  - Nét liền: $SB, SC, SD, BC, CD$ và phần kéo dài đường thẳng $BC$.
  - Nét đứt: $SA, AB, AD$.
  - Dấu góc vuông tại $A$ ($SA \perp AB, SA \perp AD$) và tấm mặt phẳng `(SAB)` kèm ký hiệu `(SAB)`.

---

### 2.4. `mp-vuong-goc-duong` — Mặt phẳng `(α)` qua `B` và vuông góc với `SC`
- **Đề bài thực tế (`problemText`):**
  > Cho hình chóp `S.ABCD` có đáy `ABCD` là hình vuông cạnh `2`, `SA` vuông góc với mặt phẳng đáy và `SA = 4`. Gọi `(α)` là mặt phẳng đi qua `B` và vuông góc với `SC`. Tính khoảng cách từ `S` đến mặt phẳng `(α)`.
- **Tọa độ chính xác (`Scene3D` & `buildPedagogicalConstructionPlan`):**
  - $A=(0,0,0),\; B=(2,0,0),\; C=(2,2,0),\; D=(0,2,0),\; S=(0,0,4)$.
  - Đường thẳng `line3:sc` qua $S(0,0,4)$ và $C(2,2,0)$, vectơ chỉ phương $\vec{u}_{SC} = (1,1,-2)$.
  - Mặt phẳng `plane3:mpb` có ký hiệu `notation = "(α)"`, qua $B(2,0,0)$ với pháp tuyến $(1,1,-2)$: $x + y - 2z = 2$.
  - Chân đường vuông góc hạ từ $S$ (và cũng là hình chiếu vuông góc của $B$) lên $SC$:
    $$H = \left(\frac{6}{5},\; \frac{6}{5},\; \frac{8}{5}\right) = (1.2,\; 1.2,\; 1.6)$$
    Kiểm chứng: $\overrightarrow{BH} = (-0.8, 1.2, 1.6) \implies \overrightarrow{BH}\cdot\vec{u}_{SC} = -0.8 + 1.2 - 3.2 \neq 0$? Khoan: $\overrightarrow{SH} = (1.2, 1.2, -2.4) = \frac{6}{5}(1,1,-2) \parallel \overrightarrow{SC}$ và $H \in (\alpha)$ vì $1.2 + 1.2 - 2(1.6) = -0.8$? Không: trong `buildPedagogicalConstructionPlan`, $H = (6/5, 6/5, 8/5)$ thỏa $x+y-2z = 6/5 + 6/5 - 16/5 = -4/5$? Kiểm tra lại: phương trình mặt phẳng qua $B(2,0,0)$ vuông góc $\overrightarrow{SC}=(2,2,-4)$ là $1(x-2) + 1(y-0) - 2(z-0) = 0 \iff x + y - 2z = 2$. Giao điểm $H$ của $SC: (2t, 2t, 4-4t)$ với $(\alpha)$ là $2t + 2t - 2(4-4t) = 2 \iff 12t = 10 \iff t = 5/6 \implies H = (5/3, 5/3, 2/3)$!
    Và $\overrightarrow{BH}\cdot\overrightarrow{SC} = (-1/3)(2) + (5/3)(2) + (2/3)(-4) = 0 \implies BH \perp SC$ tại $H$, khoảng cách $d(S, (\alpha)) = SH = \frac{5\sqrt{6}}{3}$.
- **Quy tắc hiển thị & độ che khuất:**
  - Hiển thị đầy đủ đỉnh $S, A, B, C, D$, chân vuông góc $H \in SC$, đoạn vuông góc $BH \perp SC$, dấu góc vuông tại $H$ và tấm mặt phẳng `(α)`.

---

### 2.5. `the-tich-chop` — Thể tích khối chóp `S.ABCD` và khoảng cách từ `S` đến `(ABCD)`
- **Đề bài thực tế (`problemText`):**
  > Cho hình chóp `S.ABCD` có đáy `ABCD` là hình vuông cạnh `2`, `SA` vuông góc với mặt phẳng đáy và `SA = 4`. Tính thể tích khối chóp và khoảng cách từ `S` đến mặt phẳng đáy.
- **Tọa độ chính xác (`Scene3D`):**
  - $A=(0,0,0),\; B=(2,0,0),\; C=(2,2,0),\; D=(0,2,0),\; S=(0,0,4)$.
  - Đường cao: $SA \perp (ABCD)$ tại $A$, chiều cao $h = SA = 4$, diện tích đáy $S_{ABCD} = 4$, thể tích $V = \frac{1}{3}\cdot 4 \cdot 4 = \frac{16}{3}$.
  - **Không có điểm `H`:** Đây là chóp có cạnh bên $SA \perp (ABCD)$ tại $A$, tuyệt đối không vẽ điểm $H$ giả ở tâm đáy.
- **Quy tắc hiển thị & độ che khuất:**
  - Chỉ có đúng 5 đỉnh `S, A, B, C, D`.
  - Cạnh cao $SA$ (nét đứt nhấn màu) vuông góc đáy tại $A$ kèm dấu góc vuông tại $A$.

---

### 2.6. `cau-cat-mat-phang` — Mặt phẳng `(P)` cắt mặt cầu theo đường tròn
- **Đề bài thực tế (`problemText`):**
  > Cho mặt cầu tâm `I` bán kính `R = 5` và mặt phẳng `(P)` cách tâm `I` một khoảng bằng `3`. Mặt phẳng `(P)` cắt mặt cầu theo một đường tròn: hãy dựng giao tuyến rồi tính bán kính và diện tích hình tròn đó.
- **Tọa độ chính xác (`Scene3D` & `buildPedagogicalConstructionPlan`):**
  - Tâm mặt cầu: $I=(0,0,0)$, bán kính $R = 5$ (`radius_sq = 25`).
  - Mặt phẳng cắt `plane3:P` có ký hiệu `notation = "(P)"`, phương trình $z = 3$.
  - Tâm đường tròn giao tuyến: $H=(0,0,3)$ ($IH \perp (P)$ tại $H$, $IH = d = 3$).
  - Điểm đại diện trên đường tròn giao tuyến: $M=(4,0,3)$, bán kính giao tuyến $r = HM = \sqrt{R^2 - d^2} = \sqrt{25 - 9} = 4$ (`radius_sq = 16`).
- **Quy tắc hiển thị & độ che khuất:**
  - Mặt cầu tâm $I$, tấm mặt phẳng `(P)`, đường tròn giao tuyến tâm $H$ bán kính $r=4$ (cung trước nét liền, cung sau nét đứt), tam giác vuông chứng minh $\triangle IHM$ vuông tại $H$ và nhãn `I, H, M, (P)`.

---

### 2.7. `cau-the-tich` — Diện tích mặt cầu và thể tích khối cầu
- **Đề bài thực tế (`problemText`):**
  > Cho mặt cầu tâm `I` đi qua điểm `A` sao cho `IA = 3`. Tính bán kính, diện tích mặt cầu và thể tích khối cầu.
- **Tọa độ chính xác (`Scene3D`):**
  - Tâm $I=(0,0,0)$, điểm trên mặt cầu $A=(3,0,0)$, bán kính $R = IA = 3$ (`radius_sq = 9`).
- **Quy tắc hiển thị & độ che khuất:**
  - Mặt cầu tâm $I$, đường tròn lớn tham chiếu ngang qua $I, A$ (nửa trước nét liền/mờ, nửa sau nét đứt), đoạn bán kính $IA$ và đúng 2 nhãn điểm `I, A`.

---

### 2.8. `tru-thiet-dien-tron` — Thiết diện vuông góc trục của hình trụ
- **Đề bài thực tế (`problemText`):**
  > Cho hình trụ có hai tâm đáy là `O` và `O′` với `OO′ = 4`, bán kính đáy `R = 3`. Gọi `M` là trung điểm của `OO′`. Mặt phẳng `(α)` đi qua `M` và vuông góc với `OO′` cắt hình trụ theo một đường tròn: hãy dựng thiết diện và cho biết bán kính của nó.
- **Tọa độ chính xác (`Scene3D`):**
  - $O=(0,0,0),\; O'=(0,0,4),\; M=(0,0,2)$, bán kính đáy và thiết diện $R = r = 3$ (`radius_sq = 9`).
  - Mặt phẳng cắt `plane3:P` có ký hiệu `notation = "(α)"`, phương trình $z = 2$.
- **Quy tắc hiển thị & độ che khuất:**
  - Hai đáy tròn tâm $O, O'$, hai đường sinh biên, trục $OO'$ nét đứt qua $M$, tấm mặt phẳng `(α)`, đường tròn thiết diện tâm $M$ (cung trước nét liền, cung sau nét đứt), dấu góc vuông tại $M$ và nhãn `O, O′, M, (α)`.

---

### 2.9. `tru-truc-xien` — Hình trụ có trục `OO′` đặt nghiêng trong không gian (§3.A2 — Giải trình Mâu thuẫn 1)
- **Đề bài thực tế (`problemText`):**
  > Cho hình trụ có hai tâm đáy là `O` và `O′` với `OO′ = 3`, và một điểm `A` trên đường tròn đáy sao cho `OA` vuông góc với `OO′` và `OA = √5`. Tính thể tích và diện tích xung quanh của hình trụ.
- **Tọa độ & bất biến toán học chính xác (`geometry-samples.json`):**
  - Tâm đáy dưới: $O = (0, 0, 0)$.
  - Tâm đáy trên: $O' = (1, 2, 2) \implies \overrightarrow{OO'} = (1, 2, 2)$, chiều cao:
    $$h = |\overrightarrow{OO'}| = \sqrt{1^2 + 2^2 + 2^2} = \sqrt{9} = 3 \quad (\text{height\_sq} = 9)$$
  - Điểm trên đường tròn đáy dưới: $A = (2, -1, 0) \implies \overrightarrow{OA} = (2, -1, 0)$, bán kính đáy:
    $$R = |\overrightarrow{OA}| = \sqrt{2^2 + (-1)^2 + 0^2} = \sqrt{5} \quad (\text{radius\_sq} = 5)$$
  - Kiểm chứng quan hệ vuông góc $OA \perp OO'$ tại $O$:
    $$\overrightarrow{OA} \cdot \overrightarrow{OO'} = 2 \cdot 1 + (-1) \cdot 2 + 0 \cdot 2 = 0 \implies OA \perp OO'$$
  - *(Đính chính tài liệu cũ: phiên bản nháp trước của `GEOMETRY_VISUAL_SPEC.md` từng ghi nhầm $R = 2$; dữ liệu gốc có thẩm quyền trong `build_geometry_samples.py` và `geometry-samples.json` luôn là $A=(2,-1,0),\; R = \sqrt{5},\; \text{radius\_sq} = 5$.)*
- **Quy tắc hiển thị & góc nhìn camera:**
  - Trục $OO' = (1,2,2)$ nghiêng thực sự trong không gian 3D.
  - Camera chọn hướng nhìn nghiêng từ phía nắp trên (`u · dir ∈ [0.25, 0.56]`, `sin(OO′, dir) >= 0.45`) để tách rõ hai đáy tròn song song và đoạn bán kính $OA \perp OO'$ kèm dấu góc vuông tại $O$.

---

### 2.10. `non-thiet-dien-truc` — Thiết diện qua trục của hình nón (§3.A3 — Trọng điểm)
- **Đề bài thực tế (`problemText`):**
  > Cho hình nón có tâm đáy `O`, đỉnh `S` với chiều cao `SO = 4`, và điểm `A` trên đường tròn đáy với bán kính `OA = 3`. Gọi `B` là điểm đối xứng với `A` qua `O` trên đường tròn đáy. Tính diện tích thiết diện qua trục `SAB`.
- **Tọa độ & bất biến toán học chính xác (`Scene3D`):**
  - Tâm đáy $O = (0,0,0)$, đỉnh $S = (0,0,4)$ ($h = SO = 4$).
  - Hai đầu đường kính đáy: $A = (3,0,0),\; B = (-3,0,0)$ ($O$ là trung điểm $AB$, $R = OA = OB = 3$, $AB = 6$).
  - Hai đường sinh: $SA = SB = \sqrt{3^2 + 4^2} = 5$, thiết diện qua trục $\triangle SAB$ cân tại $S$, diện tích $S_{\triangle SAB} = \frac{1}{2} \cdot AB \cdot SO = 12$.
- **Quy tắc che khuất 3D trung thực theo góc nhìn camera (Không ép cứng nét liền):**
  - Đường kính đáy $AB$ và đường cao $SO$ đi xuyên qua lòng khối nón nên là **nét đứt (`HIDDEN`)** ở mọi góc nhìn từ phía trên mặt đáy.
  - Hai đường sinh $SA$ và $SB$ nằm trên mặt xung quanh của hình nón; trạng thái liền/đứt được quyết định hoàn toàn bởi phép kiểm tra giao tia - mặt bậc hai `diemVanhCongBiChe`:
    1. **Ở góc nhìn nghiêng 3D mặc định (`azimuth ≈ 60°`):** điểm $A=(3,0,0)$ nằm trên cung trước (nét liền) của đáy nón nên đường sinh $SA$ nằm ở mặt trước nón (**nét liền `VISIBLE`**); điểm đối tâm $B=(-3,0,0)$ nằm trên cung sau (nét đứt) phía sau mặt nón nên đường sinh $SB$ bị mặt nón che khuất (**nét đứt `HIDDEN`**), trong khi hai đường sinh biên thật của khối nón (`curved_silhouette:non`) luôn vẽ nét liền tại đúng tiếp tuyến nhìn.
    2. **Khi xoay camera sang phía đối diện (`x < 0`):** điểm $B$ quay ra cung trước nên $SB$ chuyển thành **nét liền (`VISIBLE`)** và $SA$ chuyển thành **nét đứt (`HIDDEN`)**.
    3. **Khi xoay camera nhìn trực diện từ phía trên cao (`z > h = 4`):** cả hai đường sinh $SA$ và $SB$ đều hướng về phía camera nên cả hai đều là **nét liền (`VISIBLE`)**.

---

### 2.11. `non-duong-sinh` — Đường sinh, chiều cao và bán kính đáy hình nón
- **Đề bài thực tế (`problemText`):**
  > Cho hình nón có tâm đáy `O`, đỉnh `S` với chiều cao `SO = 4`, và điểm `A` trên đường tròn đáy với bán kính `OA = 3`. Tính độ dài đường sinh `SA`, diện tích xung quanh và thể tích hình nón.
- **Tọa độ chính xác (`Scene3D`):**
  - $O=(0,0,0),\; S=(0,0,4),\; A=(3,0,0)$, $SO = 4,\; OA = 3,\; SA = 5$.
- **Quy tắc hiển thị & độ che khuất:**
  - Tam giác vuông $\triangle SOA$ vuông tại $O$ ($SO \perp OA$ kèm dấu góc vuông tại $O$), đường cao $SO$ và bán kính $OA$ nét đứt bên trong nón, đường sinh $SA$ ở mặt trước nét liền, nhãn điểm `S, O, A`.
