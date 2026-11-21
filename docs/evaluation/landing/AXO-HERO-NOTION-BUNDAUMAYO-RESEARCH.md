# AXO MINIMAL HERO RESEARCH — NOTION-INSPIRED DESIGN × BUNDAUMAYO COMPOSITION

> **Mục đích:** Xác lập quyết định thiết kế cho Hero Section trên `LandingPreviewV14` (`http://localhost:3000/about?preview=landing-v14`) dựa trên bằng chứng đo trực tiếp bằng **REA MCP** và kiểm tra sản phẩm thực tế tại `/app`.

---

## 0. Bằng chứng đo trực tiếp (REA MCP & Computed Metrics)

| Tham chiếu | Viewport | REA `evidence_id` | Chỉ số DOM & Layout đo thực tế |
| :--- | :--- | :--- | :--- |
| `https://www.notion.so/` (`notion.com`) | Desktop `1440×900` | `ev_42d43f25ab79276e08d1fce58a0efc6868347ae181a7c58a1186eb85b247328e` | Nền `rgb(255,255,255)`, `Inter`, H1 `96px / weight 600 / lh 100px / ls -4.6px` màu đen thuần `rgba(0,0,0,0.95)`, đoạn dẫn `20px / 28px`, CTA chính `rgb(0,117,222)` chữ trắng, CTA phụ `rgb(230,243,254)` chữ `#005bab`; ngay dưới CTA là khối giao diện sản phẩm thật thoáng sạch không viền rườm rà. |
| `https://www.notion.so/` (`notion.com`) | Mobile `390×844` | `ev_34e7f6e658790d8fe5d0914b834d877cb4e4ade8411e875c87931bb5d5b5d3ab` | Giữ header 1 nút chính + menu, dải chữ gọn 100% bề rộng và hai CTA xếp dọc dễ chạm; không hiển thị thừa widget trang trí. |
| `https://bundaumayo.top/` | Desktop `1440×900` | `ev_422933a6252f955a221042679e6ca52384f207df4f1f8927572cde2b68c8c816` | Lưới `.c-hero-grid` (`max-width: 1400px`, `gap: 24px`) chia hai vùng bất đối xứng **~45:55 (`583px : 713px`)**: nội dung trái (`h1 86.4px / weight 700 / ls -4.32px`, bio `22.4px`, CTA chính + liên kết), chủ thể phải (`artRect 713×613`) **đứng trực tiếp trên nền sáng không cần card bao quanh** nhờ đổ bóng tiếp xúc mềm. |
| `https://bundaumayo.top/` | Mobile `390×844` | `ev_c4966ba658d9a91d6298a33acd84490927f9cdf2e82f7a016ac4cdb42abfdc1e` | Dùng một cây DOM anh em (`h1`, `.c-hero-art`, `.c-hero-body`) để CSS tự chuyển trên mobile thành **`Tiêu đề → Chủ thể trực quan → Mô tả & CTA`**. |
| `http://localhost:3000/app` (Axo Workspace) | Desktop `1440×900` | Đối chiếu sản phẩm nội bộ | Sản phẩm lõi của Axo gồm 2 nhịp trực tiếp: nhập đề bài tiếng Việt tự nhiên (*"Em muốn dựng hình nào?"*) → quan sát mô hình 3D tô mặt sạch, đường khuất nét đứt, thiết diện và mạch từng bước dựng (`S.ABCD`, `ABCD.A′B′C′D′`). |

---

## 1. Nguyên tắc Notion phù hợp với Axo

1. **Nền sáng tinh khiết & tương phản chữ đen sắc nét:** Toàn bộ Hero nằm trên nền giấy trắng `--canvas` (`#ffffff`, đồng bộ Notion và `DESIGN.md`), chữ H1 màu mực đặc `--ink`, dùng duy nhất xanh thương hiệu `--primary` (`#0075de`) cho CTA chính thay vì nhồi nhiều màu nóng hoặc gradient.
2. **Typography tự tạo điểm nhấn:** Notion dùng cỡ chữ lớn, weight đậm chắc và letter-spacing âm (`-0.038em`), không cần viền neon hay hiệu ứng vẽ thêm. Theo đúng yêu cầu tối giản cho Axo, **loại bỏ vòng khoanh nét cam quanh chữ *"hình dung"*** ở Hero (chỉ giữ `AnnotatedPhrase` ở Storytelling/Demo nơi nó giải thích mạch bài toán).
3. **Product-first Visual thay cho vật thể trừu tượng:** Người dùng cần thấy ngay *Axo biến đề bài tiếng Việt thành hình học không gian rõ ràng từng bước*, chứ không phải khối điêu khắc trang trí tách rời sản phẩm.

---

## 2. Nguyên tắc bố cục Bundaumayo phù hợp với Axo

1. **Văn bản trái – Chủ thể phải bất đối xứng (~42% : 58%):** Cho vùng trình diễn sản phẩm bên phải đủ rộng để thở và áp đảo khoảng trắng chết từng gặp ở cột 50/50 hẹp.
2. **Sân khấu không đóng khung card nặng (`Borderless Presentation`):** Chủ thể chính bên phải nổi trực tiếp trên nền `--canvas` bằng bóng đổ tiếp xúc cực mềm và các lớp UI vệ tinh nhẹ (thay vì khung viền hộp chữ nhật cồng kềnh hay hiệu ứng thu nhỏ cả cửa sổ trình duyệt).
3. **Đảo trật tự một cây DOM trên mobile (`Title → Visual → Lead + CTAs`):** Trên màn hình nhỏ `<= 680px`, đặt hình ảnh sản phẩm ngay dưới tiêu đề H1 trước khi hiện mô tả và hai nút CTA, vừa giữ gọn chiều cao màn hình đầu tiên vừa đảm bảo nút CTA chạm tay dễ dàng (`>= 44px`).

---

## 3. Thành phần giữ lại từ Landing V1.4

- Logo Axo và `LandingHeader` (Navigation, Thư viện, Bắt đầu).
- Thông điệp cốt lõi Hero (`Hình học không gian, dễ hình dung hơn.`, đoạn mô tả tiếng Việt chuẩn của Axo).
- Hai nút CTA pill `--rounded-full` giữ nguyên ID và hành vi: `#btn-landing-hero-start` (`Bắt đầu dựng hình` / `Vào ứng dụng`) và `#btn-landing-hero-story` (`Xem cách hoạt động` cuộn tới `#cach-hoat-dong`).
- Dữ liệu hình học xác thực từ [`landing-geometry-data.ts`](../../../frontend/src/components/landing/landing-geometry-data.ts) (`LANDING_CUBE_SAMPLE`).
- Toàn bộ các section bên dưới (`LandingStorytellingV14`, `LandingInteractiveDemo`, `LandingClosingV14`, `LandingFooterV14`) giữ nguyên 100%.

---

## 4. Thành phần loại bỏ khỏi Hero

- Loại bỏ vòng khoanh SVG cam quanh từ `"hình dung"` trong Hero (`AnnotatedPhrase variant="circle"`).
- Loại bỏ phương án *Spatial Prism Horizon* (3 ảnh điêu khắc thủy tinh [`hero-concept/*.png`], dấu cộng trang trí, nền kéo gradient cũ).
- Loại bỏ hoàn toàn cụm 3 Portal Gallery và thư mục `frontend/src/components/landing/portals/` + dependency chỉ phục vụ Portal (`@react-three/fiber`, `@react-three/drei`, `maath`), bảo toàn lịch sử tại các commit `796d6d0f5` và `5d6064343`.
- Không sử dụng hình chóp nét dây sách giáo khoa đơn điệu hay mockup thu nhỏ cả ứng dụng nhiều thanh bên.

---

## 5. Thiết kế hình ảnh sản phẩm bên phải (*Product-First Minimal Visual*)

Thay vì vật thể 3D trang trí ngẫu nhiên, vùng bên phải (`#landing-hero-sculpture`) trình diễn **một trạng thái sản phẩm Axo tinh lọc, chính xác toán học từ `LANDING_CUBE_SAMPLE` (lập phương ABCD.A′B′C′D′ cắt tạo lục giác đều MNEPFQ)**:
1. **Chủ thể trung tâm không đóng khung card:** Mô hình khối lập phương tô mặt đa sắc độ nhẹ kiểu Notion (sứ ấm & trắng tinh khôi phân rõ mặt sáng – mặt bên – mặt khuất, cạnh sau nét đứt mảnh, cạnh trước sắc nét, loại bỏ vẻ "khung dây đen khô cứng"), bên trong hiện rõ mặt phẳng cắt `(MNP)` nghiêng nhẹ và **thiết diện lục giác đều `MNEPFQ`** sắc xanh `--primary` cùng 6 điểm neo sạch sẽ.
2. **Chip đề bài tiếng Việt tối giản ở góc trên-trái:** Một dải nổi nhẹ (`--surface` + viền `--hairline` 1px + `--shadow-soft`) hiển thị cô đọng: *"Lập phương ABCD.A′B′C′D′ · cắt (MNP)"* — truyền đạt trực diện đầu vào tiếng Việt của Axo mà không kéo cả hộp soạn thảo lớn.
3. **Thanh bước dựng 3 nhịp tinh gọn ở góc dưới-phải:** Cho phép người xem bấm chuyển nhẹ nhàng 3 trạng thái dựng thật từ toán học (`1. Giả thiết` → `2. Mặt (MNP)` → `3. Thiết diện · Lục giác đều`, mặc định ở `3` để khung hình đầu tiên phô diễn trạng thái đẹp nhất; Landing V1.4 giữ nguyên quy tắc không hiển thị đáp án số trước theo `landing-product-integrity.test.tsx`) với tối đa 3 nút pill siêu gọn — không slider, không thanh công cụ rối rắm, không `<canvas>` WebGL trước khi duyệt.

---

## 6. Quy tắc Responsive (8 Viewport chuẩn)

- **Desktop (`1920×1080`, `1440×900`, `1366×768`) & Tablet ngang (`1024×768`):** Lưới 2 cột bất đối xứng (`0.84fr : 1.16fr`), văn bản căn trái gọn trong `34–42ch`, visual sản phẩm bên phải chiếm ưu thế không gian, chip prompt và thanh bước dựng đặt lệch hai góc chéo với khoảng hở rõ rệt so với khối lập phương trung tâm.
- **Tablet dọc (`768×1024`):** Xếp dọc thoáng: Tiêu đề & CTA ở trên, visual sản phẩm rộng rãi ở dưới trên cùng trục căn trái sạch sẽ.
- **Mobile (`390×844`, `375×812`, `320×568`):** Xếp `Tiêu đề H1 → Visual → Mô tả & 2 CTA`; trong vùng Visual, chip prompt đặt gọn phía trên khối 3D SVG (`width: 100%`) và thanh 3 bước nằm ngay dưới đáy khối (tuyệt đối không phủ chéo lên đỉnh `A′, B′, M, N, P, Q` trên màn `320px`). Tắt chuyển động khi `prefers-reduced-motion: reduce`.

---

## 7. Rủi ro triển khai cần kiểm soát

1. **Chồng lấn UI phụ lên nhãn đỉnh hình học:** Cần tính vị trí đặt chip prompt (góc trên-trái) và thanh bước dựng (góc dưới-phải) theo góc chiếu 3D sao cho các nhãn `M, N, E, P, F, Q` luôn thoáng 100% ở mọi kích thước.
2. **Độ sâu khối trên nền trắng:** Nếu dùng nét đen quá đậm trên nền trắng trơn sẽ quay về cảm giác "sách giáo khoa". Phải dùng tô mặt 3 bậc độ xám/trắng ấm siêu nhẹ + đường viền ẩn mảnh `--ink-faint` + bóng tiếp xúc elip mềm dưới đáy khối để hình khối có cảm giác nổi 3D ngay trong SVG thuần.
3. **Dọn dẹp toàn vẹn & giữ test xanh:** Xóa `portals/`, `hero-concept/`, và 3 gói `@react-three/fiber`, `@react-three/drei`, `maath` đồng thời cập nhật `vite.config.ts`, `landing.css` (0 hex thô, `class-coverage.test.ts`), và `landing-hero-visual-lifecycle.test.tsx`.
