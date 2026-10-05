# ROADMAP.md — Lộ trình nghiên cứu và phát triển AlgoSim

> **Tài liệu Canonical cho Roadmap của đề tài Khóa luận.**
> Mọi bước tiếp theo phải bám sát thứ tự ưu tiên P0 → P6.
> Bước hành động tiếp theo duy nhất (Single Canonical Next Action) được khai báo tại Mục 0.

---

## 0. Canonical Next Action

```text
CANONICAL_NEXT_ACTION = NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES
TARGET_NEXT_ACTION_AFTER_WAVE = NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES
```

- **Vì sao:** W19 (run [`w19-docs-organization`](evaluation/geometry/runs/w19-docs-organization/)) khép việc tổ
  chức tài liệu; W20 (run [`w20-cleanup-premerge`](evaluation/geometry/runs/w20-cleanup-premerge/)) đóng hai issue
  tính đúng còn chặn merge và dọn kho. Theo brief W19, việc kế tiếp là **một lát cắt hình học mới cùng các chỉnh sửa
  giao diện đã chốt** (§0.1), không phải thêm wave tài liệu nhỏ lẻ. Đề xuất của W20 (người dùng chưa chọn): chóp tứ
  giác đều (G03) — lý do và giới hạn ở `HANDOFF.md` §2 của run w20. Lượt chốt của việc này, run
  [`cuboid-final-review`](evaluation/geometry/runs/cuboid-final-review/) (2026-10-05, không đánh số wave), rà soát
  trọn tài liệu, đặt luật đánh số wave theo từng việc (`evaluation/RUN_NAMING.md`) và sửa thẻ từ chối của §17; nó
  không đổi việc kế tiếp. Run [`cuboid-acceptance`](evaluation/geometry/runs/cuboid-acceptance/) (2026-10-05, chỉ
  tài liệu) đối chiếu 24 bất biến có con trỏ chết (0 vi phạm, 0 lỗi chặn) và gom hồ sơ nghiệm thu của nhánh. Việc kế
  tiếp chạy trên nhánh mới rẽ từ `main` đã tích hợp, bắt đầu ở W1; đề xuất (chưa chọn): slug `regular-square-pyramid`,
  run đầu `regular-square-pyramid-w01`, cùng chín mục §0.1 — `HANDOFF.md` §4 của run `cuboid-acceptance`.
- **Điều kiện bắt đầu:** người dùng chọn họ hình từ bảng ứng viên §0.2 (W19 không chọn theo tên). Wave mở bằng tiền
  đăng ký: họ, các tầng phải đóng, corpus gắn nhãn trước, cổng trình duyệt desktop/mobile, hồi quy §0.3.
- **Chặn merge nhánh `fix/cuboid-visual-semantic-closure`** (không chặn phát triển): chỉ còn review người của W18 =
  `NOT_APPROVED` — duyệt bằng mắt theo `HANDOFF.md` của run w18 (W18-H1), gồm phần còn lại của W17-H1/W16-H1 (bốn
  cảnh W14 đổi, `ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`). `ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET`
  đã đóng ở W20. Cùng lượt duyệt: thẻ từ chối mới của §17 (nhãn "chưa kiểm chứng được phép dựng", desktop và mobile).
  Gói duyệt A–F — W18-H1, thẻ từ chối hiện hành, giới hạn đề nghị hoãn — ở
  [`REVIEW.md`](evaluation/geometry/runs/cuboid-merge/REVIEW.md) của run `cuboid-merge` (ảnh W18 đã chứng minh chuyển
  tiếp sang candidate `b2d4187a`); đối chiếu bất biến của run `cuboid-acceptance` không thêm lỗi chặn nào. Khi được duyệt: merge thẳng vào `main` (không PR), chạy cổng trên cây tích
  hợp, push, xoá nhánh đã merge (`AGENTS.md` §2).
- **Đã quyết (người dùng, brief `cuboid-acceptance`, 2026-10-05):** H-CFR-2 giữ chữ thường và "toạ độ" theo quy ước
  kho; H-CFR-1 là backlog giao diện (dưới §0.1), không sửa sản phẩm lúc này; H-CFR-3 `THESIS_DRAFT` §1.8 là bản chính
  đề xuất, chưa xoá `RELATED_WORK_DRAFT` khi chưa đối chiếu nội dung riêng; H-W20-3: 204 mục `D:/tmp` + 108 mục
  `.superpowers` giữ nguyên, không đòi dọn trước merge.
- **Quyết định còn chờ người dùng:** W18-H2 (ô soi lặp dòng giá trị của đáp số không công thức — trùng mục 2 của
  §0.1); W17-H2 (`ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL`); W15-H2 (vùng chặn ngoài đa diện); W15-H3 (từ vựng —
  `ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`); W18-H3 (manh mối "độ dài" của cổng phạm vi,
  `ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE`); H-W20-4 (tàn dư Tin học trong mã — `HANDOFF.md` của run w20; run
  `cuboid-acceptance` liệt kê thêm phần còn ngủ ở shell). H-W20-1 (câu chữ) và H-W20-2 (nhãn) đã sửa ở run
  `cuboid-final-review`, còn chờ người xem ảnh.
- **Ràng buộc:** giữ `DEFAULT_MODE = LLM_ONLY`; 0 lượt gọi live khi chưa có quyết định ngân sách; `CACHE_VERSION`
  quyết bằng bằng chứng; automation không tự ghi `APPROVED_BY_USER`, không sửa registry kỳ vọng người; không
  push/merge.

### 0.1 Chỉnh sửa giao diện đã chốt (đăng ký sau W18; W19 và W20 không sửa giao diện; `cuboid-final-review` chỉ sửa thẻ từ chối của §17, không thuộc chín mục dưới)

1. Ẩn mặc định card **Kết quả** dưới mô phỏng.
2. Truy cập mọi kết quả qua nút chọn đại lượng và **một** ô chi tiết.
3. Nút **"Các bước dựng"** mở danh sách cạnh của hình trên desktop.
4. Mobile: panel thu gọn được, giữ hình và điều khiển truy cập được.
5. Chọn một bước thì đồng bộ trạng thái hình học, dòng thời gian và phát lại.
6. Tách bước dựng khỏi bước tính.
7. Chọn độ dài thì tô sáng đoạn; chọn diện tích thì tô sáng vùng.
8. Giảm các dòng mô tả/phụ thuộc lặp lại.
9. Phân biệt cuộn của bộ đo (runner) với cuộn của người học.

Nguồn: brief W19 (2026-10-04), phản hồi của người dùng sau W18. Mỗi mục cần test đơn vị và cổng trình duyệt
desktop + mobile khi làm; sửa `frontend/src` thì đóng băng lại candidate.

Backlog giao diện thêm, ngoài chín mục (H-CFR-1, người dùng 2026-10-05): các lời CONSTRUCTION khác (dựng lệch điểm
hay mặt phẳng, số liệu hệ dùng lệch đề) vẫn kết bằng câu mời gửi lại — xét bỏ cùng việc giao diện kế tiếp (lời ở
`backend/app/learner_messages.py`, đụng mã đo nên đóng băng lại candidate). Chưa sửa, không tuyên bố đã xong.

### 0.2 Ứng viên họ hình kế tiếp — khoảng trống theo tầng

Nguồn: [`architecture/geometry_capability_matrix_v2.json`](architecture/geometry_capability_matrix_v2.json) —
**snapshot W13 tại `bf5a7907`**; w14–w18 có thể đã đóng một phần ô L03 (grounding nguồn) và L09 (dựng hình theo lớp)
cho sáu họ hiện có. Năng lực sản phẩm: `backend/app/simulation/product_capability.py`. Tầng: L01 analyze · L02
contract · L03 grounding nguồn · L04 topology · L05 fact graph · L06 kernel chính xác · L07 IR · L08 luật compiler ·
L09 dựng hình · L10 đo + xuất xứ · L11 renderer · L12 occlusion · L13 tương tác · L14 nhân quả · L15 fail-closed ·
L16 bằng chứng trình duyệt · L17 đánh giá giáo dục.

| nhóm | ô SUPPORTED / PARTIAL / MISSING | tầng MISSING | chặn chính (ô PARTIAL) |
|---|---|---|---|
| G03 chóp tứ giác đều | 4 / 10 / 3 | L08, L16, L17 | "đều" và chân đường cao ở tâm chưa có trường (L01–L05); cạnh đáy + cạnh bên cho chiều cao thường vô tỉ, toạ độ phải ở ℚ³ (L06); cần bước dựng tâm (L09) |
| G04 lăng trụ xiên | 5 / 10 / 2 | L08, L17 | độ xiên cho bằng góc không được grounding (L03) và thường cho chiều cao vô tỉ (L06); tuyến LLM dựng khối nguyên tử (L09) |
| G05 lăng trụ/chóp đáy đa giác tổng quát | 10 / 6 / 1 | L17 | đa giác đều ngoài hình vuông cần toạ độ vô tỉ (L06); compiler chỉ đáy tam giác vuông/chữ nhật (L08); "lục giác đều" chưa grounding (L03) |
| G16 dựng khoảng cách/góc | 8 / 6 / 2 | L08, L17 | compiler chỉ tính thể tích (L08); góc theo độ không grounding (L03); chưa có cung đánh dấu góc (L11) |
| G06 khối đa diện lõm | 8 / 6 / 3 | L05, L08, L17 | sản phẩm `foundation_only`; tự cắt mặt–mặt (toàn cục) không kiểm (L04) |
| G17 góc nhị diện | 3 / 8 / 5 | L05, L08, L11, L16, L17 | chưa có primitive nhị diện; tổng hợp 0/4 trên probe (L07) |

Hình cong (G07 trụ, G08 nón, G10 cầu): sản phẩm `foundation_only`; lượt live V3 `FAIL` (nút thắt grounding phép
dựng) — hàng E3 của [`research/CLAIM_EVIDENCE_MAP.md`](research/CLAIM_EVIDENCE_MAP.md). Nhiều khối (G13), nội/ngoại
tiếp (G14), tiếp xúc (G15): phần lớn MISSING — để sau (§0.4).

### 0.3 Hồi quy bắt buộc cho mọi lát cắt mới

Sáu họ compiler hiện có (bộ trình duyệt desktop/mobile), corpus gold (AC2 18/18 trong vùng chứng chỉ), năm ca demo
(`replay_demo_cases.py`), bề mặt sập (`audit_demo_crash_surface.py`), T3 `full-gate.mjs`. Không hàng đang phục vụ nào
bị từ chối mới mà không có quyết định ghi trước.

### 0.4 Để sau, không tuyên bố đã hỗ trợ

OCR/đề từ ảnh (P4; bằng chứng hiện là FIXTURE), nhiều khối trong một đề (G13/G14), khối tròn xoay tổng quát và khối
ghép/bù (ngoài phạm vi vì kiến trúc). Mỗi việc mở bằng quyết định của người dùng và một wave riêng. Ý tưởng ngoài
khoá luận: [`POST_THESIS_BACKLOG.md`](POST_THESIS_BACKLOG.md) — phụ lục của ROADMAP này.

---

## 1. Các Tầng Ưu Tiên (P0 – P6)

### P0 — Documentation & Handoff Hardening
- Chuẩn hóa toàn bộ hệ thống tài liệu theo 11 information domain.
- Loại bỏ xung đột sở hữu và các liên kết hỏng.
- Đối soát toàn diện bằng chứng kiểm thử máy và số lượng test.
- Đóng gói tài liệu bàn giao phiên (`AI_CONTEXT_BUNDLE.md`) và cổng điều hướng (`README.md`).
- W19 (2026-10-04): `docs/` chia bốn vùng (dự án ở gốc · `research/` · `evaluation/` · `legacy/`), một bản đồ tuyên bố ↔ bằng chứng (`research/CLAIM_EVIDENCE_MAP.md`), gốc `docs/` là danh sách đóng (`audit_docs_layout`). Còn lại: báo cáo wave cũ vẫn nằm ở gốc theo AGENTS.md §4 (`ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT`).

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
- Hợp nhất bản thảo khoá luận với bằng chứng w09–w18 (hàng chưa có mục ở `research/CLAIM_EVIDENCE_MAP.md` §4) và hai thân Chương 4 rời nhau.
