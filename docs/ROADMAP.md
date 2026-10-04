# ROADMAP.md — Lộ trình nghiên cứu và phát triển AlgoSim

> **Tài liệu Canonical cho Roadmap của đề tài Khóa luận.**
> Mọi bước tiếp theo phải bám sát thứ tự ưu tiên P0 → P6.
> Bước hành động tiếp theo duy nhất (Single Canonical Next Action) được khai báo tại Mục 0.

---

## 0. Canonical Next Action

```text
CANONICAL_NEXT_ACTION = HUMAN_VISUAL_REVIEW_OF_OPERATION_ANNOTATION_EVIDENCE
TARGET_NEXT_ACTION_AFTER_WAVE = HUMAN_VISUAL_REVIEW_OF_OPERATION_ANNOTATION_EVIDENCE
```

- **Vì sao:** W17 (run
  [`w17-operation-annotations`](evaluation/geometry/runs/w17-operation-annotations/)) kết
  thúc `READY_FOR_HUMAN_VISUAL_REVIEW` trên candidate cuối `d63d6fd4`.
  - Giới hạn A′ của W16 đã đóng: phép cắt phải dùng đúng mặt phẳng và đúng khối của câu
    cắt trong đề, nếu không thì bị từ chối.
  - Giá trị chỉ nêu trong yêu cầu chứng minh không còn là dữ kiện.
  - Mỗi lời từ chối mang nguyên nhân có cấu trúc (đề / hệ dựng / chưa rõ).
  - Số đo đã kiểm hiện cạnh vật nó đo, có hai công tắc "Số đo" và "Kết quả".

  Tự rà soát cuối tìm ra ba lỗi; các lỗi đã được sửa, sau đó candidate được đóng băng lại
  và mọi phép đo được đo lại. Việc còn lại thuộc về NGƯỜI.
- **Điều kiện bắt đầu:** người dùng mở `HANDOFF.md` của run w17 và duyệt bằng mắt (W17-H1):
  - nhãn số đo trên hình và hai công tắc;
  - ô từ chối W17 (hệ dựng lệch với đề, lỗi của hệ) và mặt phẳng đúng được phục vụ;
  - tên bước nhóm cạnh;
  - phần còn lại của W16-H1: bốn cảnh W14 đổi, đang `HUMAN_REVIEW_PENDING`
    (`ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`), phần tô thiết diện dưới cạnh và
    các ô từ chối.

  Sau đó quyết định:
  - W17-H2: mặt phẳng "qua M và song song với (X)" nay bị từ chối "chưa chứng minh được" —
    `ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL`;
  - W15-H2: mở rộng vùng chặn ngoài đa diện;
  - W15-H3: mở rộng từ vựng, gồm phép dựng khác phép cắt —
    `ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT`.
- **Điều kiện dừng:** automation không tự ghi `APPROVED_BY_USER`, không sửa registry kỳ
  vọng người; không đổi bề mặt mô hình; không push/merge.
- **Ràng buộc phạm vi:** Giữ `DEFAULT_MODE = LLM_ONLY`; 0 live Gemini request;
  `CACHE_VERSION` quyết định bằng bằng chứng. Không mở họ mới, khối cong, nhiều
  khối hay image/OCR khi chưa có quyết định của người dùng.




---

## 1. Các Tầng Ưu Tiên (P0 – P6)

### P0 — Documentation & Handoff Hardening
- Chuẩn hóa toàn bộ hệ thống tài liệu theo 11 information domain.
- Loại bỏ xung đột sở hữu và các liên kết hỏng.
- Đối soát toàn diện bằng chứng kiểm thử máy và số lượng test.
- Đóng gói tài liệu bàn giao phiên (`AI_CONTEXT_BUNDLE.md`) và cổng điều hướng (`README.md`).

### P1 — Primitive Compiler Expansion (Mở Rộng Compiler Cơ Sở)
- **Họ bài thứ hai:** Đã chọn và tiền đăng ký họ Lăng trụ đứng có đáy là tam giác vuông (`right_triangle_base_right_prism_volume`) tại `docs/PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION.md`.
- **Evidence Repair:** Đã hoàn tất đính chính bằng chứng lựa chọn, phân loại `CURRICULUM_EVIDENCE = NOT_ESTABLISHED_OFFLINE`, tái thẩm định ma trận thực chứng (Candidate B đạt 94.375% chuẩn hóa, vượt qua 4 kịch bản robustness), vạch rõ 12 tầng kỹ thuật cho vertical slice tại `docs/SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE.md`.
- **Source Scope Reconciliation:** Đã hoàn tất đối soát danh tính mã nguồn tại `docs/SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE.md`. Xác định `primitives.py:REGISTRY` có đúng 6 hàm, `SourceInvariant` có 5 kind, `RELATION_KINDS` hiện có đủ biểu diễn, IR (`construct_solid`), kernel và frontend được tái sử dụng nguyên trạng.
- **Generic Solid Topology Contract Design & Preregistration:** Đã hoàn thành thiết kế và tiền đăng ký hợp đồng topology khối đa diện tổng quát tại `docs/GENERIC_SOLID_TOPOLOGY_CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE.md`. Phân tách 2 lớp Internal Contract (Pydantic discriminated union) vs Model Transport (flattened sanitize-safe), giải quyết Single Source of Truth (SSOT), xác lập supported topology class là closed polygonal 2-manifold genus-0 (Euler $V-E+F=2$), quy tắc bảo toàn chu kỳ $D_n$, 18 bất biến và 16 fixtures. Đạt `FINAL_DECISION = PASS`, gỡ bỏ bế tắc kỹ thuật về dữ liệu topology.
- **Vertical Slice:** Mở rộng `FactGraph` và `primitive_compiler` để dẫn xuất `SemanticProgramSpec` tất định cho họ bài mới dựa trên hợp đồng topology đã tiền đăng ký (đã hoàn tất trong wave `PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE`).
- **Benchmark Đối Chứng:** Chạy benchmark đo token, độ trễ và tính đúng đắn so với đường LLM synthesis hiện tại.
- **Bảo toàn ranh giới:** Không thay đổi kiến trúc mặc định của sản phẩm.

### P2 — Geometry Generalization (Khái Quát Hóa Năng Lực Hình Học)
- Hình chóp với đáy đa giác tùy ý (tam giác thường, tứ giác, hình thang, hình bình hành, hình thoi, hình chữ nhật, hình vuông).
- Khối lăng trụ, khối hộp chữ nhật, hình lập phương.
- Các phép đo nâng cao: khoảng cách giữa hai đường thẳng chéo nhau, góc giữa đường thẳng và mặt phẳng, góc nhị diện.
- Thiết diện phức tạp cắt bởi mặt phẳng đi qua các điểm xác định.
- Khối tròn xoay (hình nón, hình trụ, mặt cầu) khi nền tảng đa diện đã hoàn thiện và ổn định.
- Trạng thái theo từng tầng của mười bảy nhóm hình (gồm chóp đều, lăng trụ xiên, nón cụt, nhiều khối, tiếp xúc, góc nhị diện) và thứ tự sửa đề xuất: [`docs/architecture/geometry_capability_matrix_v2.json`](architecture/geometry_capability_matrix_v2.json), [`GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md`](architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md) §7 (W13).

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
