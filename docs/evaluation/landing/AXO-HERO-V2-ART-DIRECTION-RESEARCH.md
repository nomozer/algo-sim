# AXO HERO REDESIGN V2 — BUNDAUMAYO COMPOSITION × NOTION MINIMALISM × DESIGN SKILLS

> **Mục tiêu:** Thiết kế lại từ gốc Hero Section của `LandingPreviewV14` (`http://localhost:3000/about?preview=landing-v14`) trên nhánh `feat/axo-hero-enter-portals`, tổng hợp bằng chứng đo trực tiếp qua **REA MCP** (`bundaumayo.top` & `notion.so`), 4 design/QA skills (`ui-ux-pro-max`, `taste-skill`, `impeccable` v4.8.0, `playwright-cli`), đánh giá đa góc nhìn Round 1 → Round 2 và kiểm chứng DOM/Vitest/Build đầy đủ trước khi trình Owner nghiệm thu.

---

## 1. Kiểm toán tiền lệ & Nhóm phương án bị bác bỏ (Không tái sử dụng)

Dựa trên kiểm toán hiện trạng mã nguồn tại baseline `5cbbb3c42` và các lần phản hồi của Owner, toàn bộ các hướng Hero trước đây đều bị từ chối vĩnh viễn và không được chỉnh sửa hay tái sử dụng dưới bất kỳ biến thể nào:

- **Static Atelier / Interactive 3D Section Lab / Hybrid Gallery / Single Geometric Cube / 3-Portal Gallery (`portals/`) / Spatial Prism Horizon (`hero-concept/`):** Bị loại bỏ.
- **Minimal SVG Cube + Pill Chips (`axo-v14-hero-minimal`):** Là trạng thái *Before* trong đợt đo V2 (`hero-v2/taste-before/report.json`), mắc **3 FAIL** (`[shadow]` từ pill card tĩnh `axo-v14-min-prompt-pill` và `axo-v14-min-step-rail`, `[few-pictures]` chỉ có `1` mảnh UI vì SVG không tính thành ảnh, `[small-text]` 4 khối chữ dưới `13px`) và **4 WARN** (`[no-footage]`, `[dev-server]`, `[off-centre]` @768px, `[size-count]` 10 cỡ chữ @390px).
- **Lớp bảo vệ kiểm thử:** `landing-hero-visual-lifecycle.test.tsx` khóa cứng việc cấm `.axo-v14-hero-minimal`, `12√3`, `<canvas>`, `.axo-v14-anno-circle`, `portals/`, `hero-concept/`, và `@react-three/fiber` / `@react-three/drei` / `maath`.

---

## 2. Bằng chứng nghiên cứu trực tiếp bằng REA MCP

| Tham chiếu | Viewport | REA `evidence_id` | Chỉ số DOM & Bố cục đo trực tiếp |
| :--- | :--- | :--- | :--- |
| `https://bundaumayo.top/` | Desktop `1440×900` | `ev_5e56511533071248c2a9c31f9c6d113f8776eabeb5be2e086b620780a3b93896` | Lưới `.c-hero-grid` (`1400px`, `gap: 24px`); cột trái gồm `H1` (`583px`, `86.4px`); sân khấu phải `.c-hero-art` (`713×613`) dùng **phân tầng kích thước Lớn → Vừa → Nhỏ**: chủ thể lớn giữa (`425×474`), 3 vật thể vừa tiền cảnh xếp cung ôm đế (`147×174`, `164×138` chồng nhẹ đáy, `177×163`), 2 vật thể nhỏ bay cao bên trên (`157×100`, `107×68`), 2 tia mực mảnh SVG (`50×50`), không card đóng khung. |
| `https://bundaumayo.top/` | Mobile `390×844` | `ev_a02bd7b664fe7230b393a3107251281a4c042ba56d52f64071f5d99862954880` | Một cây DOM duy nhất đổi thứ tự hiển thị thành **`H1 → Chủ thể trực quan → Mô tả & CTA`**. |
| `https://www.notion.so/` | Desktop `1440×900` | `ev_122037622432533e0f71929200fe0ffbcb08c3c67880e21f77bf3324e5e325ed` | Nền giấy trắng `rgb(255,255,255)`, typeface `Inter`, H1 `96px / 600 / tracking -4.6px`, nút CTA chính `#0075de`. |

---

## 3. Thực thi 4 Design & QA Skills

1. **`ui-ux-pro-max` (`C:\Users\Bunny\.gemini\config\skills\ui-ux-pro-max\SKILL.md`):** Chạy `search.py` với `--design-system --variance 6 --motion 4 --density 3 -p "Axo"`, truy vấn `Hero-Centric Design`, `Minimalism Editorial Tactile 3D`, và `hero typography hierarchy whitespace balance`. Định hướng hệ thống: giữ nền giấy `#ffffff`, mực `#111111`, xanh Axo `#0075de`, mật độ thoáng (whitespace-led), tối đa 2 nút CTA và thị giác 3D tactile làm neo trọng tâm.
2. **`taste-skill` (`C:\Users\Bunny\.claude\plugins\marketplaces\taste-skill\skills\taste-skill\SKILL.md`):** Tham khảo `critique.md`, `layout.md`, `imagery.md`; chạy `lint.mjs`, `draw.mjs --sector education --options 3`, và `inspect.mjs`:
   - *Before:* **3 FAIL** (`[shadow]`, `[few-pictures]`, `[small-text]`), **4 WARN** (`[no-footage]`, `[dev-server]`, `[off-centre]` @768px, `[size-count]`).
   - *Round 1:* **1 FAIL** (`[few-pictures]` do `hero-float-orbit.png` có diện tích dưới ngưỡng `160×120 = 19,200 px²`), **3 WARN** (`[no-footage]`, `[dev-server]`, `[off-centre]` @768px).
   - *Round 2 (sau edit cuối):* **0 FAIL, 3 WARN** (`realPictures: 3` + `uiPictures: 1` = `4`, xóa sạch mọi `FAIL`). *(3 WARN còn lại: `[no-footage]` vì Hero không dùng video trang trí, `[dev-server]` do kiểm định trên Vite dev `:3000`, `[off-centre]` @768px phát sinh từ chênh lệch lề giữa các section Storytelling/Demo ngoài Hero mà phạm vi tác vụ không cho phép sửa).*
3. **`impeccable` v4.8.0 (`C:\Users\Bunny\.agents\skills\impeccable\SKILL.md`):** Chạy `impeccable.cmd context`, `impeccable.cmd detect --json` (trả về `[]` trên `LandingHeroV14.tsx`), đọc `new-work.md`, `craft-floor.md`, `critique.md`, và triển khai **Dual-Agent Critique** độc lập trên Round 1:
   - *Assessment A (Design Director):* Chấm Round 1 mức **21/32 (Acceptable)**, chỉ ra các lỗi cần vá ở Round 2: (1) Hero lệch lề trái so với Header/Storytelling/Demo/Closing (`1360px` vs `1240px`), (2) `1920×1080` H1 rớt 3 dòng (`204px`), `1024×768` H1 nhỏ hơn `768×1024` (`37.9px < 49.2px`), (3) mồ côi từ `"quan."` ở câu dẫn, (4) `320×568` tràn dưới nếp gấp CTA, (5) tia mực bên phải nhấn vào mép bóng cắt bên phải đĩa sứ, và (6) phê bình thẳng thắn về mặt tạo hình: khối bậc thang (ziggurat) bên phải mặt cắt chưa phải thiết diện đa diện phẳng chuẩn SGK và đĩa-vòng bên trên gợi cảm giác hành tinh thiên văn.
   - *Assessment B (Deterministic Auditor):* Ghi nhận cảnh báo React `fetchPriority="high"` trong console trên 8/8 viewport, lỗi đồng bộ khi `prefers-reduced-motion` đổi động lúc con trỏ đang trỏ chuột, `transition: 260ms` xung đột với rAF pointer tracking, và mã màu/thời lượng thô chưa token hóa trong CSS.
4. **Playwright (`playwright` `1.62.1` + `playwright-cli` skill):** Kiểm thử tự động 8 viewport (`1920×1080`, `1440×900`, `1366×768`, `1024×768`, `768×1024`, `390×844`, `375×812`, `320×568`), tương tác pointer parallax, cuộn `#btn-landing-hero-story`, chuyển trang `/app`, cả `reducedMotion` tĩnh & động, và xác nhận `/about` baseline không bị ảnh hưởng. *(Công bố minh bạch: plugin `playwright` đã sync manifest tại máy nhưng không gắn làm MCP server hoạt động trong phiên này nên dùng Playwright `1.62.1` cục bộ + skill `playwright-cli`).*

---

## 4. Ý tưởng nghệ thuật & Tạo hình sản phẩm (*"Bàn Dựng Hình Không Gian Axo"*)

Thay thế hình khối rời rạc bằng một **Bàn Dựng Hình Không Gian Thu Nhỏ (Architectural Studio Diorama)** gồm 3 tấm PNG studio tách nền chuẩn sắc độ giấy trắng `#ffffff`:

1. `hero-studio-diorama.png` (`963 × 824 px`): Đế xoay sứ mờ đặt tổ hợp maquette gỗ sồi/thạch cao bị cắt chéo bởi tấm acrylic xanh thương hiệu `#0075de`, kèm 3 dụng cụ tiền cảnh (thẻ phác thảo nét xanh, thước ê-ke xanh băng mờ, com-pa gỗ sồi–đồng và khối bát diện đất nung).
2. `hero-float-plane.png` (`446 × 512 px`): Tấm mặt phẳng acrylic xanh vát cạnh xuyên trục đồng và cầu thạch cao, làm cầu nối thị giác từ vùng chữ H1 sang cụm trung tâm.
3. `hero-float-orbit.png` (`512 × 485 px`): Cầu thạch cao bọc vòng gỗ sồi/đồng cùng hạt acrylic xanh nổi ở góc trên phải (`width: 24.5%` trên desktop → `148×140 px = 20,720 px²` đạt chuẩn kích thước ảnh thật).

### Công bố trung thực (Mandatory Honesty Disclosure)

- **Bản chất tài sản đồ họa:** Ba file PNG tại `frontend/public/assets/landing/hero-studio/` là **tài sản minh họa studio tĩnh dạng layered concept presentation** kèm chuyển động pointer parallax nhẹ trên desktop, **không** phải cảnh WebGL 3D tương tác thời gian thực.
- **Bảo lưu phê bình tạo hình cho Owner quyết định:** Các nhận xét từ Assessment A về việc khối bậc thang trắng bên phải tấm acrylic gợi hình bậc kiến trúc thay vì một tiết diện đa diện phẳng thuần túy và vệ tinh vòng-cầu góc trên phải mang dáng dấp thiên văn được giữ nguyên trong hồ sơ này (Round 2 tập trung hoàn thiện xử lý viền bóng đổ, căn lề `1240px`, nhịp typography, truy cập và kiểm thử không tái tạo lại ảnh gốc trừ khi Owner yêu cầu đổi tạo hình ở vòng tiếp theo).

---

## 5. Cải tiến Round 1 → Round 2 & Chỉ số nghiệm thu cuối

- **Matting bóng đổ `matteDiorama` (`hero-studio-diorama.png` `989×827 → 963×824`):** Bổ sung bản đồ biên `5×5` (`range5`), chặn rò rỉ trên bề mặt sứ/thạch cao sáng (`l >= 215` giữ ngưỡng biên chặt), nới lỏng sắc ấm cho bóng đổ tối (`maxChroma` phân bậc đến `30`), làm mờ alpha 2 lượt `3×3` chỉ trên pixel sàn và vuốt `smoothstep` 118px mép phải → xóa sạch rãnh cắt 3 giờ trên `#ffffff` và `#f6f5f4`.
- **Đồng bộ hệ lưới & Typography:** Khóa `.axo-v14-hero-atelier-grid` về `max-width: 1240px`, `padding-inline: clamp(20px, 4vw, 48px)`, `background-color: var(--axo-sp-bg)` khớp `LandingHeader` (`leftRailDeltaPx === 0` từ `1920px` đến `375px`); ép `.axo-v14-hero-title-line { white-space: nowrap; }` (`>= 480px`) và thang font đơn điệu `56.8px → 52.56px → 49.86px → 42.50px → 39.94px → 31.2px → 30.0px → 26.4px` giữ vững **`titleLines === 2` trên cả 8/8 viewport**; thêm `trực\u00A0quan.` tránh từ mồ côi; bổ sung viền `1px solid var(--axo-sp-border-strong)` cho nút phụ.
- **Responsive fold & A11y:** Điều chỉnh `min-height: clamp(560px, calc(100svh - 118px), 958px)` giúp `1920×1080` đẩy `#cach-hoat-dong` xuống `1095px >= 1080px`; tinh chỉnh `@media (max-width: 960px)` xóa khoảng hở tablet và `@media (max-width: 360px)` đưa trọn 2 CTA vào trong `320×568` (`storyBtnBox.bottom: 547px <= 568px`); gỡ `fetchPriority="high"` (0 cảnh báo console); thêm `resetParallax` khi `reducedMotion` thay đổi động và `[data-pointer-active="true"]` tắt transition trong lúc trỏ chuột.

| Kiểm chứng sau chỉnh sửa cuối | Kết quả |
| :--- | :--- |
| Playwright 8 viewports (`results.json`) | `0` pageErrors, `0` nonApiConsoleErrors, `0` nonApiHttpFailures, `0` brokenImages, `0` horizontalOverflow, `titleLines === 2` (8/8), `/about` baseline `isV14OnBaseline: false`, `/app` điều hướng thành công |
| Taste-Skill (`taste-after/report.json`) | **0 FAIL**, 3 WARN (`realPictures: 3` + `uiPictures: 1`) |
| Impeccable (`impeccable detect --json`) | `[]` (`0` vi phạm mẫu AI slop) |
| TypeScript & Vite (`tsc -b && vite build`) | Exit `0`, built `4.91s` |
| Vitest Regression Suite | **42/42 test files passed · 169/169 tests passed** |
