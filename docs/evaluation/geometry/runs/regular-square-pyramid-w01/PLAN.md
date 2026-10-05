# PLAN — regular-square-pyramid-w01

Việc `regular-square-pyramid` (nhánh `feat/regular-square-pyramid`, rẽ từ `main` =
`38d4158826cbbffd013d971a9484b9f0fd2a6130`), wave đầu W1. Brief: `REGULAR_SQUARE_PYRAMID_AND_PEDAGOGICAL_UI`.
Ràng buộc chung: `LLM_ONLY`; 0 lượt gọi Gemini; giữ deletion `frontend/public/favicon.svg` ngoài staging; stage theo
danh sách; không push/merge; không sửa artifact lịch sử. Thực thi inline, một agent, ledger
`.superpowers/sdd/regular-square-pyramid-w01/progress.md`.

## 0. Phase 1 — tái hiện (trước mọi sửa)

Chương trình kiểu LLM cho *"Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, chiều cao bằng 3. Tính thể tích"*
(điểm `LAYOUT_DERIVED`, `O = intersect_line_line(AC, BD)`, khối, `measure volume`) chạy qua `verify_and_compile`:
thực thi đúng `V = 16` nhưng bị **từ chối ở chặng `assumption`** — `TEMPLATE_NOT_MATCHED pyramid: no apex edge stated
perpendicular to the base`. Nguyên nhân gốc:

| # | nơi | sự thật |
|---|---|---|
| RC1 | `shape_constraint.doc_rang_buoc` | đọc ký hiệu `S.ABCD` nhưng **nuốt** chữ "đều" (không phát ràng buộc; `phan_chua_doc` liệt kê nó là chưa đọc); không đọc "cạnh đáy", "cạnh bên", "trung đoạn" |
| RC2 | `assumption_gate._khuon_chop` | chỉ có khuôn T1/T2 (một cạnh bên ⊥ đáy); không có khuôn chóp đều (chân đường cao ở tâm đáy) |
| RC3 | `construction_binding` | "O là giao điểm của AC và BD" / "O là tâm đáy" rơi vào `OUT_OF_SCOPE` — dựng O sai danh tính vẫn được phục vụ |
| RC4 | `simulation_state` (luật nguồn số của thể tích) + `scene3d._attach_formulas` | chỉ `*_length` nối hai đỉnh của khối được nhận là chiều cao ⇒ chóp đều (chiều cao SO hoặc khoảng cách từ đỉnh tới mặt đáy) không có công thức `V = 1/3 × S × h` |

## 1. Kiểm kê năng lực (đang chạy, không theo snapshot W13)

| tầng | chóp tứ giác đều — trước W1 | W1 làm |
|---|---|---|
| đọc đề / RequestContract | `solid_topology` có `base_shape: square`; không có trường "đều" (không cần: trên tuyến `LLM_ONLY` server đọc tính đều từ CÂU ĐỀ) | không đổi lược đồ/prompt |
| ràng buộc "đều" | nuốt, không phát (RC1) | đọc theo từ vựng đóng |
| dựng hình / kernel | đủ: điểm hữu tỉ, `intersect_line_line`, khối, `measure volume/area/distance` chính xác (căn) | không đổi |
| grounding nguồn / chứng chỉ giả định | không khuôn (RC2) | khuôn T7 + chiều cao suy từ trung đoạn/cạnh bên khi h ∈ ℚ |
| construction binding | tâm/giao điểm ngoài từ vựng (RC3) | thêm `giao điểm của XY và ZT`, `tâm của đáy/hình vuông` theo danh tính |
| đại lượng / công thức / causal | không công thức thể tích (RC4) | luật chiều cao chung: khoảng cách từ đỉnh (đỉnh khối ngoài đáy) tới mặt phẳng qua đáy |
| formation | `PYRAMID_LIKE` dùng chung | không mã theo họ; kiểm bằng test |
| renderer / trình duyệt / oracle | họ chưa đo | thêm kịch bản trình duyệt, fixture qua ranh giới sản phẩm |
| compiler (`LLM_ONLY` không dùng) | không có họ này | **DEFERRED** — không nằm trên tuyến mặc định |

## 2. Corpus đăng ký trước

`diagnostics/corpus/LABELS.json` (17 ca: 7 `MUST_SERVE`, 7 `MUST_REFUSE`, 3 ngoài phạm vi W1) — viết sau Phase 1,
trước bản sửa; đáp số suy tay và kiểm lại bằng `diagnostics/oracle_rsp_w01.py` (oracle độc lập, đọc số bằng mẫu
riêng, không import sản phẩm): 17/17. Hồi quy: sáu họ đã đo (test backend, demo, bộ trình duyệt).

## 3. Thứ tự thực hiện

1. **README** — xong (`ab98a2df`).
2. **Đăng ký** — PLAN + LABELS + oracle (commit này).
3. **Backend (TDD)** — test đỏ theo nhãn (`backend/tests/geometry/test_regular_square_pyramid.py`) → RC1 bộ đọc →
   RC2 khuôn T7 → RC3 binding → RC4 luật chiều cao; hồi quy W14–W20 (assumption, binding, shape, grounding, formation,
   annotations).
4. **UI** — chín mục §0.1 (bảng dưới), áp chung cho mọi họ.
5. **Harness** — kịch bản chóp đều trong `generic-tier-a-scenarios.json`, fixture qua `_run_frozen_program`, trạng
   thái mới (panel bước, chọn đại lượng), coverage đăng ký trước khi đo, tiêm lỗi cho gate mới.
6. **Cache** — quyết bằng envelope cụ thể trước/sau (bắt đầu 111).
7. **Ponytail review** phạm vi thay đổi → **refreeze** một lần sau khi ổn định.
8. **Bằng chứng** — worktree tách rời sạch tại commit đo: fixture, bộ trình duyệt desktop/mobile, T3 từ đường dẫn
   có dấu cách, cổng danh tính.
9. **Tài liệu sống + REPORT/HANDOFF.**

## 4. Chín mục giao diện (ROADMAP §0.1) — đối chiếu mã trước khi làm

| # | mục | mã hiện tại | W1 |
|---|---|---|---|
| 1 | ẩn mặc định card Kết quả | `Scene3DSolution` luôn hiện mục Kết quả | ẩn mặc định; hiện khi mở lời giải |
| 2 | mọi kết quả qua nút chọn đại lượng + một ô chi tiết | chỉ qua nhãn trên hình (khi đã hiện) hoặc cây "Thành phần" | nút "Đại lượng" → danh sách chọn → ô soi |
| 3 | nút "Các bước dựng" mở danh sách bước (desktop) | không có | nút cạnh thanh điều khiển, panel cạnh khung |
| 4 | mobile: panel thu gọn, hình và điều khiển vẫn dùng được | không có panel | panel thu gọn dưới điều khiển, không che hình |
| 5 | chọn bước đồng bộ hình, dòng thời gian, phát lại | thanh trượt có; danh sách không | chọn bước ⇒ đặt bước + dừng phát; đóng/mở panel không reset |
| 6 | tách bước dựng khỏi bước tính | có (W12 `geometryTimeline`) | giữ, kiểm |
| 7 | chọn độ dài tô đoạn, chọn diện tích tô vùng | có (tầng nhân quả; vùng tô đậm hơn; nhân chứng khoảng cách W18) | giữ, kiểm trong trình duyệt |
| 8 | giảm dòng mô tả/phụ thuộc lặp | dải "Đang dựng / Dựa trên" lặp dòng thuyết minh và ô soi | gỡ dải lặp |
| 9 | tách cuộn bộ đo khỏi cuộn người học | bộ đo cuộn trang bằng `scrollIntoView` | bảng phụ cuộn bên trong; bộ đo ghi vị trí cuộn mỗi ảnh |

## 5. Kết luận cuối

Mọi cổng bắt buộc PASS ⇒ `READY_FOR_HUMAN_VISUAL_REVIEW`; không thì kết luận theo nguyên nhân và ghi cổng đỏ.
`PUSH_EXECUTED = NO`, `MERGE_EXECUTED = NO`, `LIVE_GEMINI_REQUESTS = 0`.
