# Landing Page Design Backlog & Technical Baseline Declaration

- **Trạng thái hiện hành trên `main` (C-Landing):** `TECHNICAL_BASELINE_ONLY`
- **Nghiệm thu mỹ thuật/thiết kế (`DESIGN_APPROVAL`):** **CHƯA NGHIỆM THU (`NOT_DESIGN_APPROVED`)**
- **Nhánh phát triển tiếp theo:** `feat/axo-landing-page-design` (rẽ nhánh từ `main` sau push; chưa chỉnh sửa giao diện trong đợt tích hợp này)
- **Tài sản hiện có được giữ làm baseline tạm thời:** route `/` render `LandingView`, route `/app` mở `Workspace`, route `/library` mở `LibraryView`; `0` thuật ngữ Tin học cũ; tương thích auth/guest session và `0` vòng lặp redirect.

---

## Backlog Thiết Kế & Nghiệm Thu Giai Đoạn Tiếp Theo

1. **Tái thiết kế Hero Section & Visual Hierarchy:**
   - Rà soát lại bố cục phần mở đầu (Hero) để cân bằng tỷ lệ chữ, minh họa 3D (`LandingHeroScene3D` / `LandingHeroSculpture3D`), và khoảng thở trên màn hình laptop phổ thông (`1366x768`, `1440x900`).
2. **Typography, Annotated Heading & Nhịp đọc Storytelling:**
   - Đánh giá và chuẩn hóa hệ thống phân cấp chữ (`AnnotatedHeading`), độ tương phản, kích thước font mobile/tablet, và mạch kể chuyện (`LandingStorytelling`, `LandingStorytellingV14`).
3. **Interactive Preview & Explainer Animation (`LandingInteractiveDemo`, `LandingExplainerAnimation`, `LandingClosingScene3D`):**
   - Kiểm định UX tương tác thật trên trình duyệt (desktop/tablet/mobile), thời gian tải tài nguyên WebGL/animation, và thông điệp CTA dẫn từ `/` vào `/app`.
4. **Nghiệm thu thiết kế chính thức bởi Owner (`HUMAN_DESIGN_REVIEW`):**
   - Chụp full-page visual gallery trên các viewport `1920x1080`, `1440x900`, `1366x768`, `768x1024`, `390x844`, `320x568` cho nhánh `feat/axo-landing-page-design` để Owner duyệt thiết kế riêng trước khi hợp nhất giai đoạn Landing Page mới.
   - Ràng buộc kiến trúc: giữ nguyên Workspace/Scene3D/Step Editor baseline trên `main`, giữ nguyên **Option B** (không đưa Classroom/Live Session vào Landing Page), không huấn luyện model hay thay thế Gemini, không đổi kiến trúc Hybrid `/4` chưa được duyệt.
