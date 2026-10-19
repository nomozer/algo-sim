# Geometry capability expansion — báo cáo run (Hybrid Wave 2B)

- **Run:** `geometry-capability-expansion` · nhánh `research/hybrid-wave2b-geometry-expansion` từ `main` = `origin/main` = `224328a2`
- **Ủy quyền:** `GO_HYBRID_WAVE2B_LOCAL_IMPLEMENTATION` (không merge/push, không GO LIVE, không bật Hybrid, không Wave 2C)
- **Commit:** product `08596652` · corpus/oracle/harness `8090e8e8` · sửa sau review `e9ec0f40` · candidate freeze `b8e3f112` (112 file, `520d414423788f3e9eabfcc5813968a50209b155f560baad8994b1747444730c`; bản trước `56eff5c3` / `233de890…`)
- **Version:** `geometry-functions/8` · `geometry-fact-planner/9` · `geometry-function-engine/7`; TypedFact schema `aa9d93ee…`, `flat` `485d3834…`, v3 `4bff35bb…`, khai báo hàm tuyến A `5ceb0f99…` — **không đổi**
- **Live provider calls:** 0 · `CACHE_VERSION` 127 (không bump, §8) · `LLM_ONLY` · Hybrid product NO-GO
- **T3 / review độc lập:** `handoff.md` (ghi sau khi chạy)
- **Không dùng** bộ blind holdout BH2A-01..18 của Gemini (giữ cho đánh giá độc lập).

## 1. Bốn năng lực đã IMPLEMENTED (contract: `docs/architecture/GEOMETRY_CAPABILITY_EXPANSION_CONTRACT.md`)

| Slice | Thay đổi | Loại |
|---|---|---|
| A `divide_segment` | Hàm Registry mới (`construct`, chỉ tuyến B); quy ước duy nhất t = AP/AB trên đoạn có thứ tự; cổng nguồn **giải t** từ phương trình đề nêu ("SM = 2MA" ⇒ t = 2/3 từ S; "SA = 3SM" ⇒ 1/3; đọc được cả hai chiều); engine đặt chính xác, IR `divide_segment`, kiểm lại; `TypedFact.point_kind` nhận thêm `divide_segment` nhưng **lược đồ provider `flat` giữ nguyên** (owner quyết; một trích xuất live dưới `flat` chưa thể sinh điểm chia) | primitive mới + biểu diễn |
| B `MAT_VUONG_DUONG` | Mặt qua M ⊥ đường d: **luật phân rã khai báo** (cùng loại `MAT_SONG_SONG`) chỉ dùng primitive sẵn có — Fᵢ = hình chiếu đỉnh Zᵢ lên d, Xᵢ = M + Fᵢ→Zᵢ, thiết diện (M, X₁, X₂); Zᵢ chọn theo cấu trúc khối chóp; engine kiểm ⊥ bằng Gram và trùng `plane_through_point_perpendicular_to` của kernel; `points_b` ≥ 3 nhãn (⊥ mặt) vẫn `PLANE_NOT_UNIQUE` | composition từ primitive cũ |
| C `right_angle_chain_chart` | Đáy tứ giác có góc vuông tại hai đỉnh liên tiếp (hình thang vuông): khung chính xác, tỉ số hai cạnh bên vô tỉ ⇒ `UNSUPPORTED_IRRATIONAL_LAYOUT` | cấu hình mới |
| D lăng trụ xiên | Mọi lăng trụ có một đỉnh trên đã xác định ⇒ các đỉnh còn lại = đỉnh đáy + cùng vector cạnh bên; không chứng chỉ vuông góc trên cạnh xiên | cấu hình mới |

Kèm theo: cổng ngữ cảnh câu hỏi che các câu định nghĩa phép dựng đã kiểm trước khi đọc dấu dữ kiện ("sao **cho**" không mở một mảnh dữ kiện chưa đọc) — cùng họ với bản sửa N-1 của Wave 2A; `POINT_PRODUCERS` thay 4 danh sách chép tay trong planner; hai mã mới được phân loại cho preview (`INVALID_RATIO` → dữ kiện không hợp lệ, `UNSUPPORTED_IRRATIONAL_LAYOUT` → chưa hỗ trợ).

## 2. Composition thực sự được thực thi (`results/evaluation/arm-expansion.json`, trường `constructs`)

| Ca | Hàm dựng đã chạy | Ghi chú |
|---|---|---|
| W2-EXP-03 | `divide_segment`, `midpoint`, `orthogonal_projection_line` → `ask_length` ×2 | điểm chia có tên → chân vuông góc do search chọn (depth 2) |
| dev-ratio-angle | `divide_segment` → `ask_angle_line_plane` | luật trực tiếp, mọi đối tượng có tên |
| dev-ratio-midpoint-area | `divide_segment` → `midpoint` (điểm **không tên**) → `ask_area` | search Wave 2A dùng điểm chia làm toán hạng mô tả |
| dev-trapezoid-distances | đáy mới → `centroid` → `ask_distance_point_plane` | composition 2A trên cấu hình 2B |
| dev-trapezoid-AD | đáy mới → `orthogonal_projection_line` → `ask_length` | |
| dev-oblique-prism-compositions | lăng trụ xiên → `midpoint` → `ask_distance_point_plane`; `ask_angle_line_plane` | |
| W2-EXP-07, dev-perp-square-A-SC, dev-perp-square-S-BD | `orthogonal_projection_line` ×2 → `translate_point` ×2 → `ask_section_area` | luật B, 4 điểm phụ (2 chân + 2 điểm trên mặt) |
| dev-ratio-then-perp-section | `divide_segment` → (luật B) → `ask_section_area` | primitive mới A làm điểm đi qua của luật B |

Phân biệt trung thực: luật B là **phân rã khai báo trong planner** (needs = 0), không phải tổ hợp do search tìm; nó gọi tên hai primitive mà quan hệ hình học "mặt qua M ⊥ d" cần, không gọi tên dạng đề. Tổ hợp do search tìm (needs > 0) là các chuỗi `divide_segment`/cấu hình mới → `midpoint`/`centroid`/`orthogonal_projection_line` → hàm hỏi.

## 3. Đối chứng với `main` trước run (`results/evaluation/metrics.json`)

Cùng 20 ca TypedFact, cùng oracle độc lập; `pre-expansion-main` chạy mã `224328a2` (worktree tạm, đã gỡ).

| Chỉ số | Wave 2B | `main` trước run |
|---|---|---|
| Bài dương VERIFIED | **12/12** | 0/12 |
| Mục tiêu đúng | **16/16** | 0/16 |
| Từ chối đúng mã | **8/8** | 3/8 |
| Từ chối với mã khác | 0/8 | 5/8 (`SCHEMA_INVALID` cho dạng fact mới) |
| Phục vụ sai | **0/20** | 0/20 |
| Timeline Scene3D đóng phụ thuộc | 12/12 | — |
| Theo nguồn thành công | primitive mới 2/2 · composition mới 5/5 · cấu hình mới 5/5 | 0 · 0 · 0 |

"Biểu diễn ngữ nghĩa" không tách thành nhóm riêng: mọi ca có điểm chia cần cả primitive lẫn dạng fact mới; mọi ca B cần `points_b` hai nhãn được đọc là ĐƯỜNG — nhãn ghi theo năng lực chính.

## 4. Kiểm chứng toán học

Oracle `oracle.py` (không import `app.*`, dùng lại bộ Gram chỉ-đọc của run 2A): thể tích chóp đáy đa giác, thể tích lăng trụ, **thiết diện tự tính** (giao mặt với các cạnh khối, sắp xếp lồi, diện tích vectơ). Mọi giá trị đối chiếu tay: W2-EXP-03 9/4 · 9/5 (xác nhận đính chính Gemini), W2-EXP-06A V = 1/2 · cos² = 2/3, W2-EXP-06B V² = 3/64, W2-EXP-07 S² = 1/48 (xác nhận), thiết diện qua A ⊥ SC của chóp vuông cạnh 2 S² = 4/3 (đường chéo vuông góc), qua S ⊥ BD S² = 8 (tam giác SAC), qua trung điểm SA ⊥ SC S² = 1/12 (vị tự ½), d(S, BC) hình thang vuông tại A, D d² = 9/2.

## 5. Ca âm

8/8 từ chối đúng mã: tỉ số khác nguồn (`SOURCE_OBJECT_MISMATCH`), tỉ số ngoài (0, 1) (`INVALID_RATIO`), hình thang tỉ số vô tỉ (`UNSUPPORTED_IRRATIONAL_LAYOUT`), một góc vuông (`UNSUPPORTED_BASE_SHAPE`), lăng trụ xiên thiếu đỉnh trên (`UNDERDETERMINED_POINT`), mặt ⊥ một MẶT (`PLANE_NOT_UNIQUE`, giữ nguyên), mặt chỉ chạm đỉnh (`PLANE_TOUCHES_VERTEX`), sai đường so với nguồn. Test đích: `test_geometry_capability_expansion.py` **28/28**; trên `224328a2`: 18 ĐỎ / 10 xanh (10 xanh là chốt từ chối/tương thích; ba ca tỉ số không hợp lệ xanh vì TypedFact cũ từ chối luôn `divide_segment` = `SCHEMA_INVALID` nằm trong tập mã chấp nhận) — `results/red-on-base.log`.

## 6. Tương thích ngược

- Hồi quy 174 dòng: **không dòng nào đổi** so với lớp delta Wave 2A; 41/41 fixture Adapter /2 qua chuỗi danh tính khai báo (/6 → /7 → /8 …); Wave 1 chứng chỉ, thứ tự phụ thuộc, composition 2A: test xanh.
- NLU gold: **1 dòng đổi**, D04 (hình thang vuông tại A và D) `UNSUPPORTED_BASE_SHAPE` → SERVED √6 = kỳ vọng đăng ký trước (`results/historical-gold-delta.json`, lớp thứ tư); phục vụ 10 → 11.
- Ma trận v3 (8 ô): không đổi so với lớp 2A. Một nhánh v3 cho điểm chia đã thử rồi **gỡ**: nó làm lượt replay `replay-v3-PILOT` chạm trần ngân sách token đăng ký trước (736k / 800k) và mất ca `dev12` — schema chỉ thêm khi thật sự cần.
- Bề mặt mô hình: TypedFact `aa9d93ee…`, `flat` `485d3834…`, v3 `4bff35bb…`, tuyến A `5ceb0f99…` / `7ea511a6…` — không đổi.

## 7. Scene3D / IR

Mọi bài phục vụ qua `validate_semantic_program`, kernel khớp bố cục engine, timeline đóng phụ thuộc 12/12; thiết diện là đối tượng `section`; lăng trụ xiên không mang dấu vuông góc trên cạnh bên (test khoá). Frontend không đổi.

## 8. Quyết định cache

Không bump (127): `/api/analyze` mặc định không nạp module nào run này sửa ở mức module (import lười `pipeline.py:89` chỉ khi preview bật; preview không ghi cache).

## 9. Khoảng trống còn lại → Wave 2C (PROPOSED)

Mặt ⊥ đường trên **lăng trụ** (cần luật chọn điểm neo theo mặt); điểm chia **không tên** ("điểm chia đoạn … theo tỉ số"); tỉ số viết dạng khác (`SM/SA = 2/3`, "chia theo tỉ số"); đáy hình thang không vuông / tỉ số vô tỉ; lăng trụ xiên với đỉnh trên cho bằng góc cạnh bên–đáy; khối con, khoảng cách đường–mặt, Adapter /3 (đã hoãn từ 2A); `flat` chưa có điểm chia (đo lại bề mặt trước mọi lượt live).

## 10. Review độc lập trên candidate `56eff5c3` → sửa → đóng băng lại

Reviewer chỉ-đọc (agent riêng, không sửa kho) ra **REQUEST_CHANGES**, tái hiện được cả ba:

| # | Mức | Phát hiện | Sửa (`e9ec0f40`) |
|---|---|---|---|
| 1 | MAJOR | Mặt qua M ⊥ d trùng **một mặt biên** (vd. qua B ⊥ SA = (ABC); qua A ⊥ BC = (SAB)) được PHỤC VỤ như thiết diện — `_kiem_mat_phu` trả về sớm cho `MAT_VUONG_DUONG`, bỏ qua kiểm `SECTION_PLANE_IS_FACE` mà luật ∥ có; oracle cũng nhận mọi đa giác ≥ 3 đỉnh nên corpus không bắt được | chứng chỉ ⊥ chạy trước, rồi kiểm mặt biên + bước trace `construct_plane` DÙNG CHUNG với luật ∥; 2 ca test mới ⇒ `SECTION_PLANE_IS_FACE` |
| 2 | MINOR | Tỉ số mẫu 0 (`"1/0"` ở tuyến A; "SM = 1/0MA" trong đề) ném `ZeroDivisionError` thay vì từ chối có mã | validator ⇒ `ValidationError` (`SCHEMA_INVALID`); cổng nguồn bỏ qua phương trình mẫu 0 ⇒ từ chối có mã |
| 3 | MINOR | Hai góc vuông nêu tại cùng một đỉnh (đáy DAB + "Góc SAB vuông") che góc đáy ⇒ `UNSUPPORTED_BASE_SHAPE` (fail-closed, mất phủ) | góc vuông khoá theo (đỉnh, hai tia) |

Test đích **32/32** (4 test mới, đỏ trên `56eff5c3`). Candidate đóng băng lại trong worktree tạm sạch (`b8e3f112`, lớp `inputs/candidate_divergence.json` đính chính lớp đầu). Đo lại nhánh `expansion` trên candidate mới: `results/evaluation-review-fix/` — `metrics.json` **trùng từng byte nội dung** với lần đo đầu (12/12 · 16/16 · 8/8 · 0/20), `arm-expansion.json` chỉ khác `route_ms` và `code_root_head`; nhánh `pre-expansion-main` là bản chép nguyên của lần đo đầu (cùng mã `224328a2`, cùng corpus — không chạy lại). Kết luận §3 không đổi; con số "0/20 phục vụ sai" chỉ nói về corpus — lớp lỗi #1 nằm ngoài nó, nay khoá bằng test.
