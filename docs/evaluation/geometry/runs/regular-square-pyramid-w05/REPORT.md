# regular-square-pyramid-w05 — IMMERSIVE_SIMULATION_AND_ARCHITECTURE_SLICE · báo cáo

Một lượt, máy local, `DEFAULT_MODE = LLM_ONLY`, 0 lượt gọi model, 0 subagent. Nhánh `feat/regular-square-pyramid`
(chưa push, chưa merge). Mốc nhận `73bc404e` (W4). Bằng chứng đo tại `f01df0e5` (lần đo 4) — product `82225a7b`,
candidate `5e1c0639…`, `CACHE_VERSION` 115. Kế hoạch và bảng yêu cầu: `PLAN.md`.

## 1. Yêu cầu — đã làm / giữ

| Mục brief | Kết quả | Bằng chứng |
|---|---|---|
| A. Tiếp nhận | W3/W4 giữ nguyên (bảng nổi chung, nhãn theo bước, không bước chỉ-mặt-phẳng-đo, SM không vẽ hai lần, nét khuất, dữ kiện nguồn, danh tính phép dựng) — không đo lại riêng, các cổng W4 chạy lại ở lần đo 4 và xanh | `PLAN.md` §1, §3 |
| B. Skill + DESIGN.md | DESIGN.md (gốc kho) có và được dùng (token, nút tiện ích 8 px, một màu nhấn); không có PRODUCT.md — không bịa | `diagnostics/SKILL_NOTES.md` |
| C. Chế độ tập trung | mở cảnh 3D ⇒ trang lấp đầy, không thanh đăng nhập/điều hướng; nút «← <trang trước>» về đúng trang đã vào (store `returnView`/`roiXuong`); toàn màn hình là mục riêng trong «Thêm», chỉ khi trình duyệt hỗ trợ; bước, lựa chọn, ma trận nhìn giữ qua menu · đổi cỡ · toàn màn hình; desktop/màn thấp vừa đúng một màn (trang không cuộn), mobile cuộn được, không trần chiều cao canvas | đầu dò W05 21/21 |
| D. Nhóm công cụ | kiểm kê trước khi sửa; «Đề bài» (nút chính) · «Khám phá» (Thành phần, Đại lượng) · «Hiển thị» (Hiện tất cả số đo, Hình phụ, Lưới nền, chú giải màu) · «Thêm» (Cách máy dựng, Toàn màn hình); «Xem lại toàn hình» giữ nút nổi; «Tách khối» chỉ khi cảnh có mặt; «Chi tiết» còn chức năng riêng ⇒ vào «Thêm», không thường trực; menu bàn phím (↓/↑/Home/End, Escape trả tiêu điểm, bấm ngoài đóng); mobile lưới 2 × 2, vùng chạm 44 px | `diagnostics/TOOL_INVENTORY.md`, `scene3d-focus-mode.test.tsx`, đầu dò W05 |
| E. Bỏ trình bày lặp | thẻ lời giải dưới thanh phát gỡ (nó lặp đúng tập `quantityChoices`); mỗi đại lượng một mục ở «Đại lượng» (nhãn backend + `ký hiệu = giá trị` chính xác + vai trò chuỗi nhân quả); công thức + nguồn số ở ô soi; chú giải màu trong «Hiển thị» | suite 7/7 (bảng «Đại lượng» khớp oracle ở mọi bước), playback 14/14 |
| F. Lát cắt backend | §2 | §2 |
| G. Kiểm thật | §4 | `results/`, `diagnostics/logs/` |
| H. Cache/candidate/tài liệu | §5 | — |

## 2. Lát cắt kiến trúc backend: bộ đọc độ dài nguồn đọc chuỗi bằng nhau

- **Thiếu gì (đọc ở tiền đăng ký §4 + `ISSUE-ARCH-SOURCE-LENGTH-CHAINED-EQUALITY`):** `SA = SB = SC = SD = 3` chỉ gắn
  `SD = 3`; đề xác định được đáp số (`V = 16/3`) bị từ chối oan ở `grounding` (`SOURCE_EVIDENCE_CONFLICT`).
- **Đã đổi (`c15e6fab`):** `segment_relation.MAU_DO_DAI` đọc tiền tố chuỗi `X1 = X2 = … =` (nối bằng `=`/`bằng`, chỉ tên
  đoạn — `2AC` cắt chuỗi); mọi đoạn của chuỗi nhận cùng giá trị, đoạn có hai giá trị vẫn bị bỏ (luật cũ).
  `cac_doan_truoc` thay `nhan_doan_truoc` (trả cả chuỗi); `_do_dai_doan` dùng lại `_moi_doan_co_do_dai` (bỏ regex thứ hai).
- **Nơi gọi trên route thật:** `grounding_gate._bang_chung` (bằng chứng GIVEN), `do_dai_trong_de` ← `refusal_cause`,
  `bat_bien_do_dai` ← `analyze_contract` + `assumption_gate` (bất biến nguồn, chứng chỉ giả định),
  `shape_constraint.phan_chua_doc` (cả chuỗi được đọc), `quantity_annotations._do_dai_de_cho` (nhãn số đề cho chọn đúng
  thành viên chuỗi). Không thêm module, không thêm lượt gọi model, không route song song, bề mặt mô hình không đổi.
- **Toạ độ bố cục vẫn không thành dữ kiện:** ca `W5_C` (chuỗi không có số, chiều cao do bố cục) bị từ chối ở `assumption`.
- **Nhãn ghi TRƯỚC bản sửa** (`diagnostics/corpus/LABELS_W05.json`, log đỏ `diagnostics/logs/RED_CHAIN_READER.log`):

| Ca | Kỳ vọng | Sau sửa |
|---|---|---|
| `R2_L1` (đính chính `product_limit` của lớp R2) | phục vụ `16/3` | phục vụ `16/3` |
| `W5_A` khai thành viên khác của chuỗi (`SC`) | phục vụ `16/3` | phục vụ `16/3` |
| `W5_B` hai chuỗi khác giá trị (3 và 5) | từ chối `source_invariant` | từ chối `source_invariant` |
| `W5_C` chuỗi không có số | từ chối `assumption` | từ chối `assumption` |
| `W5_D` khai `SA = 5` trái chuỗi | từ chối `SOURCE_EVIDENCE_CONFLICT` | đúng |
| `W5_E` khai đoạn ngoài chuỗi (`SO`) | từ chối `SOURCE_EVIDENCE_CONFLICT` | đúng |

  Hai hàng probe W13 cho `AB = AC = 5` (khoá hành vi cũ) chuyển sang tập đăng ký đổi, hành vi mới khoá bằng
  `test_w05_chuoi_bang_nhau_doi_dang_ky`; artifact W13 không sửa.
- **Họ sẽ dùng:** mọi họ đọc độ dài đoạn từ đề — chóp đều/chóp có cạnh bên bằng nhau, lăng trụ đều/đứng
  (`AA′ = BB′ = …`), đáy tam giác cân/đều (`AB = AC = a`), tứ diện đều.
- **Kiến trúc CHƯA làm (không tuyên bố hoàn tất):** trừu tượng #4 của tiền đăng ký (GIVEN/DERIVED/MODEL_ASSUMPTION/
  VISUAL_DEFAULT cho mọi giá trị) vẫn một phần; compiler tất định (tầng C) vẫn chưa bật; quan hệ ② (chia đoạn,
  `AM = MB = 3`) chưa đọc chuỗi; bộ đọc ràng buộc hình dạng vẫn là từ vựng đóng.

## 3. Giao diện — thay đổi và lý do

- `App.tsx`: cảnh 3D ⇒ không dựng `nav-bar`, gốc mang `la-tap-trung`; nút «Giải thích» (không tác dụng với cảnh 3D) không
  còn trong không gian mô phỏng; xưởng vỡ ⇒ thẻ lỗi có «Rời mô phỏng» (không thanh trên nào để thoát).
- `SimulationWorkspace.tsx` truyền vào xưởng: nút quay lại (tên trang đích từ `TopNav.TEN_TRANG`), tên bài, nhãn bài
  được giao, «Giao cho lớp» (giáo viên), dải lớp.
- `scene3d-tool-menu.tsx` (mới): `MenuCongCu` — menu-button ARIA; bảng vẫn là `BangNoi` của W4 (không hệ bảng thứ hai).
- `global.css`: chế độ tập trung một hàng lưới, cao ≥ 100dvh, trang sở hữu cuộn, không đệm đáy 140/190 px của khay 2D,
  xưởng hết trần 1320 px. **Lỗi bắt bởi lần đo 2 và đã sửa (`82225a7b`):** hàng lưới rỗng của khay 2D vẫn ăn 16 px khoảng
  cách hàng ⇒ trang dư đúng 16 px, cuộn được, cú bấm dời canvas. Đầu dò W05 thêm luật `PAGE_SCROLLS` (đỏ trước khi sửa).

## 4. Kiểm tra đã chạy

| Kiểm | Kết quả |
|---|---|
| pytest (cây làm việc trước commit giao diện) | 7172 pass, 1 skip; 15 đỏ đều thuộc candidate cũ/cây bẩn (đóng băng lại, cây bẩn của người khác) — T3 sạch ở `HANDOFF.md` §2 |
| vitest | 1136/1136 (74 tệp) · `tsc -b` + build xanh |
| node harness | 93/93 (gồm `assessFocusMode` với ca tiêm lỗi từng lý do, `PAGE_SCROLLS`, `toolbar_styled`) |
| **Lần đo 4 `f01df0e5`** (worktree tách rời sạch, CRLF, đường dẫn có dấu cách) | suite 7/7 họ, 14/14 lượt dương · đầu dò W02 14/14 · đầu dò W04 21/21 · **đầu dò W05 21/21** · occlusion pass (4 cảnh chờ duyệt, U2) · phát lại 14/14 · 68 crop cạnh khuất, 0 bất đồng oracle, 0 owner trùng |
| Khung nhìn thật đo | desktop 1422×804 (xin 1440×900), màn thấp 1348×554 (xin 1366×650), mobile 390×844 |
| Ba lần đo trước | không dùng, ghi đủ ở `MEASUREMENT_ATTEMPTS.json` — lần 1: phép kiểm CSS hàng trên của tôi sai (màu `--ink` trùng mặc định); lần 2: lỗi sản phẩm 16 px + playback còn đọc thẻ đã gỡ + ngân sách chờ lắng camera + một đầu dò chạy song song do tôi; lần 3: cú xoay pixel cố định của đầu dò W4 thành tư thế khác trên canvas cao hơn |

**Thay đổi bộ đo (không hạ ngưỡng):** suite/playback/đầu dò W2·W4 đọc bảng «Đại lượng» và mở công cụ qua menu; kiểm CSS
hàng trên đọc phông tên bài; ngân sách chờ lắng camera 10 s → 20 s (dung sai 1e-9, 5 mẫu ổn định, 30 khung giữ nguyên —
canvas rộng hơn làm mọi họ chậm lắng 5–15 %); cú xoay của đầu dò W4 theo góc W4 đã chấm (tỉ lệ chiều cao canvas).

## 5. Danh tính, cache, candidate

- `CACHE_VERSION` **giữ 115** (`diagnostics/cache_proof/CACHE_DECISION_W05.json`): mọi hàng corpus chóp đều được phục
  vụ ở cả hai cây có cảnh trùng băm (11 hàng, gồm một hàng chẩn đoán có chuỗi đã phục vụ trước); khác biệt duy nhất của kết
  cục là `source_invariant_stats` — chỉ vào sự kiện quan trắc, không vào envelope; 37/37 fixture bảy họ trùng byte với W4.
- Candidate `8a27a58b…` → **`5e1c0639…`** (110 file), đóng băng **hai lần** trong worktree sạch: `470adc3a`, rồi
  `82225a7b` sau khi lần đo 2 bắt lỗi 16 px (chỉ `frontend/src`, cùng tree hash).
- Bề mặt mô hình không đổi (prompt, thẻ văn phạm, lược đồ, bảng năng lực); môi trường ngữ nghĩa `b1714b56…`.

## 6. Còn mở / giới hạn bằng chứng

- **Duyệt hình (chặn merge):** `REVIEW.md`. Chỉ người dùng ghi `APPROVED_BY_USER`.
- Nút «Quay lại» theo trang trước TRONG ứng dụng; nút Back của trình duyệt không đổi (ứng dụng không có route URL —
  thêm lịch sử trình duyệt là ngoài phạm vi).
- Toàn màn hình đo trong Chrome headless qua CDP (vào/ra được ở mọi khổ); trình duyệt khác chưa đo.
- Một cú xoay tự do có thể đưa một đỉnh sát mép canvas (lần đo 3: B cách đáy 3 px với tư thế chưa từng được chấm); không
  tự khớp lại sau khi xoay — «Xem lại toàn hình» khớp lại. Không đổi trong W05.
- Cây làm việc có thay đổi chưa commit KHÔNG phải của lượt này (xoá vài script/fixture Tin học cũ, sửa `AI_CONTEXT_BUNDLE`,
  `ARCHITECTURE_MAP`, `OPEN_ISSUES`, `CODE_INDEX`): giữ nguyên, không stage — mọi commit W05 chỉ chứa hunk của W05.

## 7. Đề xuất việc kế tiếp (không làm trong lượt này)

Mở rộng họ trên bộ đọc mới: **chóp tam giác đều + tứ diện đều** (`SA = SB = SC = a`, `AB = BC = CA = b`) qua đúng route
sản phẩm — dùng chuỗi bằng nhau cho cạnh bên và cạnh đáy, chứng chỉ giả định thêm khuôn "chóp đều đáy tam giác đều" (chân
đường cao = trọng tâm), nhãn corpus ghi trước, đo bảy + một họ trong chế độ tập trung.
