# ROADMAP.md — Lộ trình nghiên cứu và phát triển AlgoSim

> **Tài liệu Canonical cho Roadmap của đề tài Khóa luận.**
> Mọi bước tiếp theo phải bám sát thứ tự ưu tiên P0 → P6.
> Bước hành động tiếp theo duy nhất (Single Canonical Next Action) được khai báo tại Mục 0.

---

## 0. Canonical Next Action

```text
CANONICAL_NEXT_ACTION = PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION
TARGET_NEXT_ACTION_AFTER_WAVE = PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE
```

- **Mục tiêu:** Tiền đăng ký hoàn tất họ bài hình học thứ hai (`right_triangle_base_right_prism_volume`). Bước chuyển giao kế tiếp: Triển khai lát cắt dọc primitive compiler cho khối lăng trụ đứng đáy tam giác vuông.
- **Ràng buộc:** Giữ nguyên chế độ mặc định `LLM_ONLY`, không đổi default route.

---

## 1. Các Tầng Ưu Tiên (P0 – P6)

### P0 — Documentation & Handoff Hardening
- Chuẩn hóa toàn bộ hệ thống tài liệu theo 11 information domain.
- Loại bỏ xung đột sở hữu và các liên kết hỏng.
- Đối soát toàn diện bằng chứng kiểm thử máy và số lượng test.
- Đóng gói tài liệu bàn giao phiên (`AI_CONTEXT_BUNDLE.md`) và cổng điều hướng (`README.md`).

### P1 — Primitive Compiler Expansion (Mở Rộng Compiler Cơ Sở)
- **Họ bài thứ hai:** Đã chọn và tiền đăng ký họ Lăng trụ đứng có đáy là tam giác vuông (`right_triangle_base_right_prism_volume`) tại `docs/PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION.md`.
- **Preregistration:** Đã hoàn tất đăng ký trước 8 ca độc lập (5 dương, 3 âm), ground truth giải tích, gap audit (`construct_prism`, nút `prism` trong `FactGraph`).
- **Vertical Slice:** Mở rộng `FactGraph` và `primitive_compiler` để dẫn xuất `SemanticProgramSpec` tất định cho họ bài mới (wave kế tiếp: `PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE`).
- **Benchmark Đối Chứng:** Chạy benchmark đo token, độ trễ và tính đúng đắn so với đường LLM synthesis hiện tại.
- **Bảo toàn ranh giới:** Không thay đổi kiến trúc mặc định của sản phẩm.

### P2 — Geometry Generalization (Khái Quát Hóa Năng Lực Hình Học)
- Hình chóp với đáy đa giác tùy ý (tam giác thường, tứ giác, hình thang, hình bình hành, hình thoi, hình chữ nhật, hình vuông).
- Khối lăng trụ, khối hộp chữ nhật, hình lập phương.
- Các phép đo nâng cao: khoảng cách giữa hai đường thẳng chéo nhau, góc giữa đường thẳng và mặt phẳng, góc nhị diện.
- Thiết diện phức tạp cắt bởi mặt phẳng đi qua các điểm xác định.
- Khối tròn xoay (hình nón, hình trụ, mặt cầu) khi nền tảng đa diện đã hoàn thiện và ổn định.

### P3 — Visualization & Readability (Trực Quan Hóa và Khả Năng Đọc Cảnh 3D)
- Bộ giải bố cục không gian 3D tự động (spatial layout solver) đảm bảo tỉ lệ thẩm mỹ và hạn chế méo hình.
- Tối ưu hóa góc nhìn camera mặc định (auto-framing, fit-to-view).
- Giải thuật chống đè nhãn điểm và nhãn đoạn thẳng (label anti-collision / positioning solver).
- Nhận diện và diễn họa nét khuất động học (dynamic hidden-line detection & rendering) khi người dùng xoay quỹ đạo 3D.

### P4 — Image Acquisition & Problem Digitization (Đầu Vào Ảnh Chụp Đề Bài)
- Nhận diện vùng đề bài và tách hình vẽ khỏi văn bản từ ảnh chụp điện thoại.
- OCR bóc tách văn bản đề bài tiếng Việt kèm ký hiệu toán học.
- Benchmark đánh giá độ bền vững trước nhiễu ảnh thực tế (ánh sáng, độ nghiêng, độ mờ).

### P5 — Migration Architecture (Chuyển Giao Sang Compiler-First)
- Xây dựng cổng định tuyến `compiler-first`: ưu tiên chạy compiler nếu bài toán đủ điều kiện (`is_compiler_eligible`).
- Cơ chế chuyển tiếp an toàn sang LLM fallback khi bài toán chưa thuộc tập primitive hỗ trợ.
- Cơ chế triển khai canary (phân luồng tỉ lệ thực nghiệm) và rollback tự động khi phát hiện dị thường.
- Đánh giá toàn diện 20 cổng di chuyển tại [`docs/MIGRATION_CHECKLIST.md`](MIGRATION_CHECKLIST.md) trước khi chốt quyết định đổi default mode.

### P6 — Thesis Evaluation & Empirical Experiments (Đánh Giá Khóa Luận)
- Benchmark kỹ thuật toàn diện trên bộ dữ liệu kiểm thử độc lập (held-out test set).
- Đo lường định lượng: token tiêu thụ, thời gian phản hồi (latency), tỷ lệ từ chối an toàn, độ chính xác tọa độ và tính hợp lệ sư phạm.
- Khảo sát tính khả dụng (usability) và trải nghiệm người dùng trên học sinh/giáo viên.
- Phân tích các mối đe dọa đến tính hợp lệ (threats to validity) và đóng góp nghiên cứu của đề tài.
