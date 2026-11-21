# AXO HERO VISUAL RESEARCH — REDESIGN FROM FIRST PRINCIPLES

> **Phạm vi:** Nghiên cứu tiền triển khai cho quá trình thiết kế lại toàn bộ Hero Section trên Landing Page V1.4 (`LandingPreviewV14` — `http://localhost:3000/about?preview=landing-v14`) từ nguyên lý gốc (*First Principles*), tuân thủ cổng kiểm duyệt thiết kế (*Design-First Gate* — dừng trước Phase 6 WebGL).
> **Bằng chứng gốc:** Toàn bộ phân tích tham chiếu bên dưới căn cứ trực tiếp trên phiên thu thập **REA MCP (`capture_browser_scenario`)** ngày 20/11/2026 và ảnh chụp kiểm chứng thị giác lưu kèm theo phiên làm việc.

---

## 0. Bảng bằng chứng REA MCP trực tiếp

| Nguồn tham chiếu | Viewport / Trạng thái | REA `evidence_id` | Quan sát DOM & thị giác xác thực |
| :--- | :--- | :--- | :--- |
| `https://bundaumayo.top/` | Desktop `1440×900` (tải đầu) | `ev_422933a6252f955a221042679e6ca52384f207df4f1f8927572cde2b68c8c816` | DOM `65,738 B` · `0 <canvas>` · `34 <img>` · `19 <svg>`. Cây `<section id="home" class="c-hero">` dùng cấu trúc ngang hàng 3 khối anh em (`h1.c-hero-title`, `.c-hero-art`, `.c-hero-body`) đặt trên nền giấy sáng đồng nhất (`#faf8f5`), không đóng khung hộp cho phần hình ảnh. Cụm hình trung tâm (`#goat-stage`) tách thành từng lớp asset độc lập (`cloud`, `fish-bucket`, `goat-sleep`, `bun-dau`, `controller`, hai `<svg class="c-ticks">`). |
| `https://bundaumayo.top/` | Mobile `390×844` | `ev_c4966ba658d9a91d6298a33acd84490927f9cdf2e82f7a016ac4cdb42abfdc1e` | Chuyển đổi trật tự hiển thị trên mobile không cần nhân bản DOM: **Tiêu đề `h1` → Nghệ thuật trung tâm `.c-hero-art` → Mô tả & CTA `.c-hero-body`**, giúp người dùng nhìn thấy ngay chủ thể trước khi đọc đoạn mô tả. |
| `https://bundaumayo.top/` | Desktop `1440×900` (cuộn xuống 1 nhịp) | `ev_2f4e0bf917b344a7083148a69b1c4e24fe99e9ad374082b3705ef3b5c23170ed` | Nhịp chuyển xuống khu vực thứ 2 vẫn giữ đúng tinh thần không khung viền: vật thể điêu khắc bên trái đối trọng khối card thông tin bên phải trên cùng bề mặt ấm sáng. |
| `https://pmndrs.github.io/` | Desktop `1440×900` | `ev_5256e58cb15c0bcd81a4dee36e77c6477793e3ea4c2594cae3ec4abd7df12bbe` | Trang gốc `pmndrs.github.io` hiện trả về **HTTP 404 GitHub Pages**. Được bổ sung bằng đo trực tiếp trên `https://pmnd.rs/` và `https://pmndrs.github.io/examples/` cộng bằng chứng `enter-portals` trước đó. |
| `https://pmnd.rs/` | Desktop `1440×900` | `ev_d68a3e17ba67aca62753e5209838070303596f2a2fa5cf66942b885f763789c6` | Màn hình chính của Poimandres: thanh chọn demo bên trái, sân khấu lớn chiếm ~78% khung hình bên phải bo góc nhẹ trên nền sáng, thanh HUD nổi tối giản ở các góc và **một tâm điểm thị giác duy nhất** ở chính giữa sân khấu. |
| `https://pmndrs.github.io/examples/` | Desktop `1440×900` | `ev_c657e04f293a50b189ab73e733c828f7fd8dc643ae032d16bdcfacbde4c684ca` | Danh mục `208 examples` xác nhận kiến trúc tách danh sách mẫu sang rail phụ để nhường toàn bộ phần trung tâm cho vùng trình diễn 3D duy nhất. |
| `https://pmndrs.github.io/examples/enter-portals/` | Desktop `1440×900` (đã thu trước đó) | `ev_b4ea01ca22dd74f61f0b61dd24558fffede5e048c2abbf265b42399994330996` / `ev_f497c13ea690de4c9c1261a1ae086ae4e735a4ce6fb28adf04d91f3b6b4d2a81` | Xem chi tiết trong [`AXO-HERO-ENTER-PORTALS-REA-ANALYSIS.md`](./AXO-HERO-ENTER-PORTALS-REA-ANALYSIS.md): dùng R3F `<Canvas>` đơn nhất, FBO `MeshPortalMaterial`, `easing.damp`, không ánh sáng phức tạp khi dùng `KHR_materials_unlit`. |
| `https://www.lusion.co/` | Desktop `1440×900` (`reduced_motion=reduce` & `no-preference`) | `ev_b6f2de60bf3f3d35ed83e4e7c5ff10f7f7ab8ae530d3a52610e301db72deee75` / `ev_6123da25ad245898e21e1f5959cdf7e0d9e73f70679d428784aa6d2c50993908` | DOM `112,321 B` · Three.js `r158` (`<canvas id="canvas">`). Bố cục Hero phi đối xứng cực kỳ chặt: dải trên chỉ chứa **Logo trái + một phát ngôn 3 dòng căn giữa-trên (`h1#home-hero-title`) + nút CTA tối & Menu bên phải**; phía dưới là **sân khấu panorama toàn chiều rộng** chứa khối kiến trúc điêu khắc bóng gốm/sứ/cobalt có chiều sâu; mép dưới cùng đặt thanh định hướng tuyến tính `(+  +  SCROLL TO EXPLORE  +  +)`. |
| `https://www.lusion.co/` | Mobile `390×844` | `ev_1c26ca9a8527a34bef6a6ff812f690bced396feb74482177a6194ebaf9dd8b4a` | Khi co về `390×844`, dải tiêu đề rút gọn lên ngay dưới logo, sân khấu panorama chuyển tỷ lệ dọc làm khối trung tâm áp đảo màn hình, thanh `+ SCROLL TO EXPLORE +` giữ nguyên hai dấu cộng định vị ở hai mép. |

---

## 1. Phân tích layout Bundaumayo

Từ ảnh chụp thực nghiệm `ev_422933a6...` (Desktop `1440×900`) và `ev_c4966ba6...` (Mobile `390×844`), giá trị kiến trúc của Bundaumayo nằm ở **cấu trúc thị giác và tỷ trọng không gian**, hoàn toàn độc lập với phong cách nhân vật:

1. **Không đóng khung sân khấu (*Borderless Stage*):** Vùng minh họa bên phải hoàn toàn không có viền thẻ chữ nhật, không nền gradient xám-xanh tách biệt khỏi trang. Các vật thể đất nặn nổi trực tiếp lên nền giấy ấm sáng của toàn trang bằng **bóng đổ tiếp xúc mềm** (*contact ambient occlusion*), tạo cảm giác sân khấu hòa làm một với tờ giấy nền.
2. **Phân cấp khối Lớn – Vừa – Nhỏ rõ rệt (*Mass Hierarchy*):**
   - **Khối lớn (Anchor):** 1 chủ thể trung tâm chiếm khoảng 60% mật độ thị giác vùng art (`#goat-wrap`), đặt hơi lệch trục để tránh cứng nhắc.
   - **Khối vừa (Supporting):** 2 vật thể vệ tinh ở rìa dưới-trái và dưới-phải để neo mặt phẳng nền và mở rộng tam giác thị giác.
   - **Chi tiết nhỏ (Micro-beats):** Các phần tử nhẹ hơn (mây nền mờ ở tầng cao + nét vẽ tay SVG `c-ticks` ở rìa chủ thể) nối liền ngôn ngữ đồ họa với dòng chữ tiêu đề.
3. **Liên kết hữu cơ giữa Chữ và Hình (*Editorial Bridge*):** Cụm nhấn trong `<h1>` dùng nét khoanh SVG mảnh (`c-ring`, `pathLength="1"`) đồng màu/đồng chất với nét nhấn trên phần hình ảnh, khiến hai nửa màn hình nói chung một ngôn ngữ thị giác thay vì hai widget ghép cạnh nhau.
4. **Kỹ thuật đảo trật tự trên Mobile bằng một cây DOM duy nhất:** Đặt `h1`, `.c-hero-art`, `.c-hero-body` làm ba phần tử ngang cấp trong lưới Hero. Trên desktop, cột trái xếp `Title` + `Body` còn cột phải giữ `Art` kéo dài 2 hàng; trên mobile (`390×844`), CSS sắp lại theo trục dọc thành **`Title → Visual → Lead + CTA`**, giúp người dùng di động thấy ngay hình ảnh đắt giá trước khi trượt ngón tay xuống nút hành động.

---

## 2. Phân tích depth & interaction pmndrs

Từ hệ sinh thái `pmnd.rs` (`ev_d68a3e17...`), `pmndrs.github.io/examples/` (`ev_c657e04f...`) và bản nghiên cứu `enter-portals` (`ev_b4ea01ca...` / `AXO-HERO-ENTER-PORTALS-REA-ANALYSIS.md`):

1. **Một tâm điểm không gian duy nhất (*Single Spatial Focal Point*):** Những mẫu thuyết phục nhất (Shield VFX, khối khúc xạ thủy tinh nền sáng ở góc trái `pmnd.rs`, hoặc khung cảnh FBO sâu ở `enter-portals`) đều có **một sân khấu chính thống nhất**. Việc tách thành 3 khung chữ nhật nhỏ đặt ngang cạnh chữ Hero (`796d6d0f5`) làm gãy quy mô, thu hẹp khoảng thở xung quanh chủ thể và ép người xem phải đọc 3 nhãn phụ ngay ở màn hình đầu tiên.
2. **Thị sai theo con trỏ với quán tính giảm chấn (*Damped Pointer Parallax*):** Sự sống của scene đến từ chuyển động tinh tế giữa tiền cảnh, trung cảnh và hậu cảnh khi con trỏ di chuyển hoặc góc nhìn dịch nhẹ (`easing.damp`), tạo cảm giác vật thể thực sự chiếm chỗ trong không gian Z sâu chứ không phải ảnh bitmap dán phẳng.
3. **Vật liệu truyền sáng & chiều sâu mặt phẳng (*Optical Transmission & Depth Planes*):** Khối rắn gốm/sứ đặt giao cắt với mặt phẳng thủy tinh bán trong suốt tạo nên chiều sâu tức thì mà không cần nền tối hay hiệu ứng phát sáng neon thái quá.

---

## 3. Phân tích art direction Lusion

Từ REA capture trực tiếp `https://www.lusion.co/` (`ev_b6f2de60...`, `ev_6123da25...`, `ev_1c26ca9a...`):

1. **Thoát khỏi khuôn 50/50 *Text Trái — Hộp Hình Phải*:** Lusion giải phóng toàn bộ chiều ngang của màn hình bằng bố cục **Editorial Header Band ở phía trên + Sân khấu Panorama điêu khắc ở phía dưới**. Tiêu đề đứng trên nền sáng thoáng đạt nên không bao giờ phải tranh chấp chiều rộng với tác phẩm điêu khắc bên dưới; đồng thời sân khấu hình học được hưởng trọn chiều ngang thị giác (~1160–1240px thay vì bị bóp trong 480px cột phải).
2. **Ngôn ngữ vật liệu Studio Design đẳng cấp:** Chủ thể điêu khắc của Lusion dùng đúng 3 sắc độ tương phản tinh tế (trắng gốm lì, xanh cobalt kiến trúc bão hòa, đen obsidian phản xạ ánh sáng softbox từ góc trên-trái) — không nhiễu, không đường nét kỹ thuật chằng chịt, không nhãn chữ bay lơ lửng đè lên hình khối.
3. **Điểm định chuẩn thị giác (*Architectural Registration Crosshairs*):** Dải dưới cùng của Hero chỉ gồm bốn dấu `+` mảnh căn lưới đều hai bên dòng chữ dẫn cuộn ngắn gọn (`SCROLL TO EXPLORE`). Trên nền sáng của Axo, mô-típ dấu `+` kiến trúc đóng vai trò cực kỳ tự nhiên như tọa độ đo đạc của bản vẽ không gian, vừa giữ cân bằng đáy khung hình vừa dẫn mắt xuống phần Storytelling.

---

## 4. Những nguyên lý phù hợp với Axo

Đối chiếu chặt chẽ với [`DESIGN.md`](../../../DESIGN.md) ("Notion-calm: yên tĩnh, giấy trắng, tập trung tri thức, dùng chữ làm cấu trúc") và [`tokens.css`](../../../frontend/src/styles/tokens.css):

| Nguyên lý rút ra | Cách chuyển hóa sang bản sắc Axo | Token neo trong `tokens.css` |
| :--- | :--- | :--- |
| **Thoát khỏi 50/50 chật chội** (Lusion) | Dùng bố cục **"Spatial Prism Horizon"**: cụm tiêu đề & CTA biên tập gọn phía trên (`max-width: 720px`, căn giữa), nhường dải ngang rộng bên dưới cho quần thể khối đa diện kiến trúc không viền khung. | `--canvas`, `--canvas-soft`, `--ink`, `--ink-secondary` |
| **Sân khấu không viền trên nền sáng** (Bundaumayo) | Quần thể điêu khắc không nằm trong thẻ bo góc tối hay khung viền xám; phần đáy Hero chuyển sắc êm ái từ `--canvas` (`#ffffff`) sang `--canvas-soft` (`#f6f5f4`) để nối thẳng vào Storytelling V1.4 mà không tạo đường cắt ngang. | `--canvas`, `--canvas-soft`, `--hairline` |
| **Phân cấp Lớn – Vừa – Nhỏ & Tầng Z** (Bundaumayo + pmndrs) | **1 khối chính trung tâm** (khối đa diện sứ trắng/chàm bị mặt phẳng kính xanh sapphire cắt tạo thiết diện hổ phách) + **2 khối vệ tinh** ở hai tầng xa-gần trái/phải + hậu cảnh đường cung định chuẩn mờ cực nhẹ. | `--secondary` (`#213183`), `--primary` (`#0075de`), `--accent-sky` (`#62aef0`), `--accent-orange` (`#dd5b00`) |
| **Nối ngôn ngữ chữ & vật thể** (Bundaumayo) | Giữ nguyên khoanh nhấn SVG hữu cơ quanh cụm `"hình dung"` (`AnnotatedPhrase variant="circle"`), đồng điệu với quầng đường cung bản vẽ chạy mờ phía sau khối điêu khắc; hai nút CTA giữ pill `--rounded-full` và `--primary` xanh Axo duy nhất. | `--primary`, `--primary-active`, `--on-primary`, `--rounded-full` |
| **Chú trọng Mobile Interleaving** (Bundaumayo + Lusion) | Dưới `680px`, thứ tự hiển thị tự nhiên chuyển thành **`Tiêu đề H1 → Sân khấu khối 3D → Lead + CTA → Thanh kéo xuống`**, giữ CTA trong vùng chạm tay mà vẫn khoe trọn biểu tượng thị giác đầu trang. | Breakpoint `<= 680px`, target `>= 44px` |

---

## 5. Những yếu tố KHÔNG nên sao chép

1. **Từ Bundaumayo:**
   - KHÔNG sao chép nhân vật linh vật (dê đất nặn), món ăn đất nặn hay nét minh họa phong cách truyện tranh/giải trí cá nhân. Axo là công cụ tư duy toán học nghiêm túc nhưng hiện đại.
   - KHÔNG dùng nút viền đen dày 3px kiểu neo-brutalist (`box-shadow` đen đặc) hoặc dải 4 nút mạng xã hội trong Hero — chúng phá vỡ quy chuẩn "yên tĩnh, ít viền, độ cao bóng siêu nhẹ" của `DESIGN.md`.
2. **Từ pmndrs / `enter-portals`:**
   - KHÔNG dùng nền tối sci-fi với lưới neon xanh phát sáng (`pmnd.rs`), KHÔNG đặt bảng điều khiển Leva ở góc Hero, và KHÔNG lặp lại mô hình 3 khung thẻ dọc đặt cạnh khối chữ (`796d6d0f5`).
   - KHÔNG sao chép nguyên si phong cách tranh sơn dầu Low-poly hay các GLB mẫu không liên quan đến cấu trúc không gian của Axo.
3. **Từ Lusion:**
   - KHÔNG chuyển Hero Axo sang sân khấu tối đặc màu than chiếm toàn bộ chiều cao (`#14161a`), tránh tạo cảm giác "studio quảng cáo tối màu" đứt gãy hoàn toàn với phần Storytelling/Interactive Demo giấy trắng phía dưới.
   - KHÔNG dùng ngôn ngữ agency hoa mỹ hay hiệu ứng scroll-jacking cướp quyền cuộn tự nhiên của trình duyệt (`prefers-reduced-motion` phải được tôn trọng tuyệt đối).

---

## 6. Đánh giá vì sao các Hero trước của Axo thất bại

1. **Landing V1.4 bản ban đầu (hình chóp dây `S.ABCD` đơn lẻ bên phải):** Đặt trên nền trắng sạch nhưng **trông giống hình minh họa sách giáo khoa vector**: toàn bộ khối lượng thị giác chỉ gồm vài nét mảnh đen, hai mảng màu phẳng nhạt (`#dd5b00` và xanh nhạt) cùng nhãn đỉnh `S, B, C, D, M, E, F, N, P` rời rạc trôi bên phải cột chữ, thiếu hoàn toàn chất liệu, ánh sáng studio, bóng tiếp xúc và ấn tượng công nghệ hiện đại.
2. **Static Atelier (Phương án A):** Tự đóng khung mình trong cấu trúc bục trưng bày thạch cao cố định bên cột phải — nặng tính dàn dựng mô hình tĩnh và tạo khoảng trắng thừa trên/dưới khối chữ cột trái.
3. **Interactive 3D Section Lab (Phương án B):** Biến Hero ngay màn hình đầu thành một khung lab chằng chịt chip điều khiển và thông số kỹ thuật, trùng lặp trực diện với phần `LandingInteractiveDemo` ngay bên dưới thay vì làm nhiệm vụ mở màn định vị giá trị sản phẩm.
4. **Hybrid Gallery Poster (Phương án C):** Ép nhiều mảng poster/tấm card vào vùng nửa phải màn hình, khiến mắt bị phân tán giữa khung thẻ và văn bản.
5. **Hero 3 Portal trên V1.4 (`796d6d0f5` — `v14-after-hero-gallery-1440x900.png`):**
   - Nhốt ngược 3 khối hình học dây vào 3 thẻ bo góc đứng (`/01`, `/02`, `/03`) ngay bên cạnh cột chữ — thực chất lặp lại chính bố cục **chữ trái + hộp 50/50 phải** nhưng làm mỗi cảnh bên trong bị bóp nhỏ xuống còn ~170px bề rộng!
   - Vì mỗi Portal là một thế giới độc lập với khung thẻ xám/xanh đậm/xám cạnh nhau, tổng thể Hero bị chia làm 4 hộp tách rời (1 khối chữ + 3 thẻ portal) với các nét vẽ kỹ thuật nhỏ xíu lọt thỏm bên trong, không tạo được cú hích thị giác ở lần nhìn đầu tiên.

**Kết luận nguyên nhân gốc:** Mọi vòng thất bại trước đây đều bắt nguồn từ hai sai lầm cấu trúc: **(a)** giam khu vực thị giác trong một ô cột phải 50% chiều rộng và **(b)** dùng thẩm mỹ *"hình vẽ nét dây + nhãn chữ toán học"* thay vì thẩm mỹ *"sản phẩm điêu khắc kiến trúc có ánh sáng, vật liệu, tầng chiều sâu và không gian thở có chủ đích"*.

---

## 7. Nguyên tắc thiết kế mới cho Hero Axo — Concept *"Spatial Prism Horizon"*

1. **Kiến trúc bố cục 3 dải ngang có nhịp thở (Editorial Top + Panoramic Spatial Ensemble + Grounded Scroll Bar):**
   - **Dải 1 — Lời tuyên ngôn & CTA (Top Center Editorial Band):** Tiêu đề 2 dòng giữ nguyên nội dung tiếng Việt đã chốt (`Hình học không gian, dễ hình dung hơn.` với vòng khoanh nhấn quanh `hình dung`), đoạn dẫn súc tích tối đa 2 dòng và 2 nút CTA tiêu chuẩn của V1.4 (`Bắt đầu dựng hình` / `Vào ứng dụng` màu `--primary`, `Xem cách hoạt động` nền mềm `--canvas-soft`). Căn giữa tinh gọn giúp tổng chiều cao khối chữ chỉ ~215px trên desktop, mở khóa toàn bộ tầng dưới.
   - **Dải 2 — Quần thể điêu khắc không khung (Borderless Multi-Plane Stage):** Trải rộng đến ~1080px bề ngang, chứa 3 tác phẩm điêu khắc vật lý kỹ thuật số đồng bộ ánh sáng ban ngày studio softbox góc trên-trái:
     - **Tâm điểm (Big):** Khối chóp-lăng trụ kiến trúc bằng gốm trắng lì (`#ffffff`/`#f6f5f4`) có vát cạnh tinh xảo và lõi chàm sâu (`#213183`), bị một **mặt phẳng kính quang học sapphire (`#0075de`)** cắt ngang qua tâm, làm lộ rõ mặt thiết diện phát sáng ấm hổ phách (`#dd5b00`) bên trong chất kính.
     - **Vệ tinh trái (Medium, tầng trung-sâu):** Khối lập phương vát kiến trúc trắng sứ & chàm bị lát kính xanh sapphire xẻ chéo, lơ lửng lệch trái ở độ cao thấp hơn.
     - **Vệ tinh phải (Small-Medium, tầng cận-tiền cảnh):** Khối lăng kính tam giác kính sapphire trong suốt cài ngàm gốm lì lơ lửng đối trọng phía phải, nhẹ nhàng vươn cao để cân bằng bố cục đường chéo.
     - **Hậu cảnh bản vẽ tĩnh lặng:** Các đường cung kiến trúc cực mảnh (`opacity` rất thấp) gợi quỹ đạo không gian thuần túy — **tuyệt đối không có chữ A/B/C/S/M/N hay nhãn điểm làm rối khối**.
   - **Dải 3 — Neo mép kiến trúc (`+  +  Kéo xuống để xem cách dựng  +  +`):** Dấu cộng định vị khoảng cách tối giản theo tinh thần Lusion ở mép dưới, chuyển sắc êm sang `--canvas-soft` của phần Storytelling bên dưới.
2. **Thiết kế chuyển động (*Motion Storyboard* — kích hoạt sau khi Owner duyệt sang Phase 6):**
   - **Giai đoạn Design-First hiện tại (trước duyệt):** Áp dụng thị sai con trỏ đa lớp siêu nhẹ (`--axo-hx`, `--axo-hy` nội suy giảm chấn qua `requestAnimationFrame` trong CSS transform; vệ tinh lơ lửng biên độ rất nhỏ `±6px`; tắt hoàn toàn khi `prefers-reduced-motion: reduce`). **Chưa dựng WebGL Three.js đầy đủ (`FULL_3D_IMPLEMENTATION = NOT_STARTED`).**
   - **Lộ trình Phase 6 sau khi Owner duyệt:** Chuyển thẳng 3 tầng bố cục này sang 1 `<Canvas>` R3F thống nhất (nền trong suốt đồng bộ giấy sáng, camera `fov=38` đáp ứng theo tỷ lệ khung hình, `MeshPhysicalMaterial`/`MeshTransmissionMaterial` cho mặt cắt kính sapphire, lõi hổ phách phản quang bên trong khối, 1–2 nguồn sáng softbox có bóng tiếp xúc thật, xoay nhẹ theo con trỏ với giới hạn góc cực an toàn và fallback tĩnh giữ nguyên chất lượng).

---

## 8. Rủi ro kỹ thuật & rủi ro thiết kế cần quản trị

| Loại rủi ro | Mô tả rủi ro | Phương án kiểm soát ngay từ bước Design-First & sang Phase 6 |
| :--- | :--- | :--- |
| **Ngân sách chiều cao màn hình `1366×768`** | Bố cục xếp dọc (Chữ trên — Cảnh 3D dưới) nếu giữ padding lớn sẽ đẩy đáy sân khấu hoặc nút CTA lệch nhịp trên laptop `1366×768`. | Tối ưu chiều cao khối chữ (~210px) và co giãn sân khấu theo `clamp(250px, 37svh, 390px)` trên desktop để **toàn bộ H1 + CTA + 3 khối điêu khắc + Scroll cue nằm gọn trên màn hình đầu tiên ở cả `1920×1080`, `1440×900` và `1366×768`**. |
| **Viền hộp / Halo quanh ảnh concept tĩnh** | Nếu render vật thể 3D trên nền trắng nhưng không tách nền thật chuẩn, đặt trên nền chuyển sắc `--canvas -> --canvas-soft` hoặc gần chữ có thể lộ viền chữ nhật. | Render trên nền trắng tinh khiết với lề rộng 4 phía, tách nền thành RGBA trong suốt tinh sạch (khử quầng trắng mép và chỉ giữ bóng tiếp xúc trung tính), kiểm tra trực quan từng viewport bằng mắt qua ảnh chụp thật. |
| **Chi phí GPU khi lên Phase 6 WebGL** | `MeshTransmissionMaterial` trên 3 khối cùng lúc có thể tụt FPS trên máy học sinh / mobile cấu hình thấp. | Ở Phase 6 chỉ dùng pass khúc xạ FBO cho mặt cắt trung tâm (`dpr={[1, 1.75]}`), các vệ tinh dùng `MeshPhysicalMaterial` nhẹ hoặc tắt render khi cuộn khỏi viewport (`IntersectionObserver`), tôn trọng `prefers-reduced-motion`. |
| **Lệch nhịp hệ thống Token & Test hiện hành** | Thêm màu hex thô vào `landing.css` hoặc đưa `var(--` vào `LandingHeroV14.tsx` sẽ làm đỏ các test kiểm toán hệ thống thiết kế và trợ năng đang bảo vệ V1.4. | Tuân thủ tuyệt đối: mọi màu trong `landing.css` đi qua biến `tokens.css` / `rgba(...)`; `LandingHeroV14.tsx` không chứa `var(--` và xử lý `prefers-reduced-motion: reduce`. |
