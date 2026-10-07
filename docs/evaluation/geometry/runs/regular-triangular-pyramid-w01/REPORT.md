# regular-triangular-pyramid-w01 — REGULAR_TRIANGULAR_PYRAMID_AND_TETRAHEDRON_SLICE · báo cáo

Một lượt, máy local, `DEFAULT_MODE = LLM_ONLY`, 0 lượt gọi model, 0 subagent. Nhánh `feat/regular-square-pyramid` (giữ
theo lệnh người dùng; lệch `RUN_NAMING` có chủ ý — `RUN.json`), chưa push, chưa merge. Mốc nhận `e9435d67` (W5). Bằng
chứng đo tại `1bb11018` (lượt đo 3) — product `1e90ca0e`, candidate `92c9e198…`, `CACHE_VERSION` 116. Kế hoạch, PRE-FLIGHT
và bảng phạm vi: `PLAN.md`.

## 1. Họ được hỗ trợ — và miền đã khai

- **Chóp tam giác đều** S.ABC và **tứ diện đều** ABCD, trên route sản phẩm (LLM viết bước dựng, engine tất định chạy),
  chỉ trong **miền hẹp ℚ³** người dùng chọn (2026-10-07): cạnh đáy² ∈ {2k², 6k²} (đọc `k√2`, `k√6` từ đề), chiều cao² =
  3t²; đáy trên mặt phẳng nghiêng `x+y+z=k`, renderer xoay HIỂN THỊ cho đáy nằm ngang. Lý do: tam giác đều đỉnh hữu tỉ có
  cạnh² = 2N (N chuẩn Eisenstein) — không bao giờ là bình phương hữu tỉ — và chiều cao là bội hữu tỉ của √3 (`PLAN.md` §1).
- Ngoài miền ⇒ từ chối trung thực `TEMPLATE_NOT_REPRESENTABLE T8` (cạnh hữu tỉ "cạnh đáy bằng 3", N = 7, …), không làm tròn
  (`ISSUE-ARCH-REGULAR-TRIANGULAR-RATIONAL-EDGES`). Năng lực sản phẩm: `foundation_only`
  (`product_capability.regular_triangular_pyramid`) — mô hình chưa được đo là có chọn bố cục nghiêng
  (`ISSUE-ARCH-REGULAR-TRIANGULAR-MODEL-LAYOUT-UNMEASURED`).
- Chóp tam giác đều ≠ tứ diện đều (N9: bố cục tứ diện cho đề chỉ nói "chóp tam giác đều" ⇒ từ chối); ba cạnh bên bằng nhau
  KHÔNG suy ra đáy đều (N8 ⇒ từ chối); chân đường cao là trọng tâm SUY RA, không lấy từ bố cục (N5, N5b, N7 ⇒ từ chối).
- "Tứ diện ABCD" thường (không "đều") chưa vào vùng đa diện của cổng giả định (`ISSUE-ARCH-TETRAHEDRON-OUTSIDE-POLYHEDRAL-REGION`);
  thử đưa vào làm đỏ ba test tứ diện đã phục vụ — đính chính có ngày ở `ASSUMPTION_CERTIFICATE_AMENDMENT.md` §18.1.

## 2. Backend — đổi gì, ai gọi

Luật đăng ký trước: `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §18. Nhãn ghi TRƯỚC (`diagnostics/corpus/LABELS.json`,
25 hàng: 11 phục vụ, 10 từ chối, 4 ngoài miền; hai sửa đổi có ngày sau thay đổi backend, trước mọi lượt đo trình duyệt).
**Đính chính:** commit nhãn `dc0a804b` ghi "26 rows"; lúc ấy có 24 hàng, sau sửa đổi 25.

| Thẩm quyền | Thay đổi | Nơi gọi trên route |
|---|---|---|
| `segment_relation` | độ dài nguồn đọc số hoặc căn thành `ExactNumber` (`_SO_DO_DAI`, `_phan_do_dai`, `viet_do_dai`) — một mẫu số, dùng chung | `grounding_gate`, `bat_bien_do_dai` (← `analyze_contract`, `assumption_gate`), `shape_constraint`, `quantity_annotations`, `refusal_cause` |
| `shape_constraint` | đọc `chóp tam giác đều`, `tứ diện đều`, `đáy … tam giác đều`, `tất cả các cạnh`, `trọng tâm tam giác`; `la_chop_tam_giac_deu` là thẩm quyền DUY NHẤT | `assumption_gate`, `formation`, `construction_binding` |
| `assumption_gate` | khuôn T8 (mâu thuẫn, suy biến, kiểm biểu diễn được, khung chính tắc N1/N3); T1–T7 chuyển sang `square` để nhận căn | `kiem_gia_dinh` trên route |
| `formation` | `phep_trong_tam`: trọng tâm qua hai trung tuyến hoặc `divide_segment` 2/3; chân đường cao đáy đều 3 đỉnh | dựng hình theo lớp (LLM + compiler) |
| `construction_binding` | quan hệ `centroid` (§16) — tên "trọng tâm" phải khớp phép dựng | cổng danh tính phép dựng |
| `grounding_gate`, `postconditions`, `quantity_annotations` | so khớp CHÍNH XÁC cho căn (`parse_exact`, `square`) | cổng GIVEN, hậu điều kiện, nhãn số đo |
| `scene3d` | bước nối cạnh thiết diện mang tên theo mặt ("Giao tuyến của … với mặt SAB") | sự kiện cảnh (D4) |
| `product_capability` | hàng `regular_triangular_pyramid`, `foundation_only` | bảng năng lực sản phẩm |

Không thêm module, không route song song, không compiler-first, không OCR. Bề mặt mô hình (prompt, thẻ văn phạm, lược đồ,
bảng năng lực băm) **không đổi** — môi trường ngữ nghĩa `b1714b56…`. Kiểm: `pytest tests/geometry/test_regular_triangular_pyramid.py`
(58 test; nền đỏ 30/56 trước sửa — `diagnostics/logs/RED_BASELINE.log`), oracle độc lập `diagnostics/oracle_rtp_w01.py` 15/15,
tiêm lỗi `diagnostics/fault_injection_rtp_w01.py` 6/6 bắt được.

## 3. Giao diện — sửa và giữ

| Mục | Kết quả |
|---|---|
| D1 thể tích thiết diện thân rỗng | ô soi luôn hiện giá trị (`laDaiLuong`) + «Đo trên» khi không có nguồn số |
| D2 chọn SO / S(đáy) | chủ thể của nhãn đại lượng vào tầng đích, kể cả đoạn trùng cặp đầu mút (`interaction-state`) |
| D3 icon trước/phát/sau | `.geo3d-btn` inline-flex, khe 6 px; bỏ khoảng trắng tay |
| D4 tên bước trùng, lời kể lặp | nhãn bước giao tuyến theo mặt (backend); lời kể ẩn khi trùng tiêu đề |
| D5 mobile khoảng trắng + cuộn | **chưa sửa** — tái hiện (hình chiếm 32–68 % chiều cao canvas mobile); mọi phương án hoặc làm hình nhỏ hoặc đảo quyết định đã duyệt ⇒ bốn phương án chờ người dùng (`ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL`) |
| D6 zoom W5 | giữ; đầu dò W05 kiểm góc nhìn giữ qua menu · đổi cỡ · toàn màn hình |
| Xoay hiển thị đáy nghiêng | quaternion trên nhóm gốc + nhóm nhân chứng; camera z-up giữ nguyên; snapshot camera = view × model (+ `model_matrix_column_major`) để oracle độc lập đọc đúng |
| **Khung nhìn (lượt đo 1)** | hộp bao dự phòng "cảnh chỉ mặt phẳng/đường" từng xét TRƯỚC khi gộp toàn cảnh ⇒ ở bước 0 hai góc hộp bao nở theo vùng bấm lọt vào khung: mọi họ lệch trái 65–100 px, tâm quỹ đạo lệch ~0,9 đơn vị, chóp tam giác đều văng khỏi khung 17 px sau cú xoay W4. Sửa `1e90ca0e` (`diemVuaKhung`, nền đỏ trước sửa). Hình nay ở giữa ở mọi họ — ảnh trung tính đổi so với W5 (dịch ngang), chiều cao hình không đổi |

## 4. Kiểm tra đã chạy

| Kiểm | Kết quả |
|---|---|
| **Lượt đo 3 `1bb11018`** (worktree tách rời sạch, CRLF, có dấu cách; đăng ký trước luật dừng) | suite 8/8 họ, 16/16 lượt dương, 31/31 ca âm · đầu dò W02 16/16 · W04 24/24 · W05 24/24 · occlusion pass (cảnh chờ người duyệt như W5) · phát lại 16/16 · 72 crop cạnh khuất, 0 bất đồng oracle, 0 owner trùng · họ mới trên desktop còn lề 109 / 95 / 34 px (trung tính / sau xoay W4 / sau đổi cỡ) |
| Hai bước chạy lại riêng trong lượt 3 | W02 treo trên `about:blank` (Chrome không điều hướng, ứng dụng chưa tải, không phép kiểm nào chạy) ⇒ chạy lại riêng 16/16; W04 `cross_section/desktop` hết giờ chờ trang khi máy 100 % CPU, 566 MB trống (ứng dụng của người dùng, không động tới) ⇒ chạy lại riêng `cross_section` 3/3. Không bước nào khác chạy lại |
| Khung nhìn thật (canvas) | desktop 1373×683, màn thấp 1299×433, mobile 356×517 |
| Lượt đo 1 `aa583ad9`, lượt 2 `1bb11018` | không dùng — `MEASUREMENT_ATTEMPTS.json` (1: khung nhìn, sản phẩm, đã sửa; 2: một trang mobile tải thiếu stylesheet, môi trường, 0/8 khi tái hiện riêng) |
| vitest / build / node harness | 1145/1145 · `tsc -b` + build xanh · 94/94 |
| T3 + cổng danh tính | `HANDOFF.md` §2 |

**Thay đổi bộ đo (không hạ ngưỡng):** họ thứ tám trong suite và các đầu dò; `cameraSauCuChi` đọc `model_matrix` khi cảnh có
phép xoay hiển thị; oracle tầng nhân quả theo luật D2; bước tỉa ảnh sau bộ dựng bằng chứng (mục E).

## 5. Ảnh — chụp để kiểm, lưu có chọn (mục E)

`backend/scripts/prune_evidence_images.py` chạy sau bộ dựng bằng chứng: giữ ảnh bộ dựng đọc (oracle thị giác, crop cạnh khuất,
sheet), ảnh nó sinh, ảnh trong tập duyệt chọn trước (`inputs/REVIEW_SET.json`) và mọi ảnh của họ có lượt thất bại; ảnh bỏ vẫn
ghi sha256 ở `results/IMAGE_POLICY.json` (yêu cầu → ca → trạng thái → commit/candidate → khung nhìn thật). Lượt đo 3: giữ **492** ảnh (117 MB) cho tám họ, bỏ 358 (66 MB) —
W5 lưu 767 ảnh (165 MB) cho bảy họ. Cross-section giữ trọn vì có một ca W04 hết giờ (luật "họ có lượt thất bại"); bốn ảnh tập
duyệt lấy từ lượt chạy lại W02 (`images/rerun/`), ảnh chạy lại khác không công bố (sha256 nằm trong JSON của đầu dò).
Luật cũ "chụp mọi thứ" không có văn bản sống; `TEST_TIERS.md` nay ghi luật mới.

## 6. Danh tính, cache, candidate

- `CACHE_VERSION` **115 → 116** (`diagnostics/cache_proof/CACHE_DECISION.json`): 37 fixture so sánh, 35 trùng, 2 envelope thiết
  diện ĐÃ phục vụ đổi nhãn bước ⇒ row cache cũ sẽ trả nhãn cũ.
- Candidate `5e1c0639…` → **`92c9e198…`** (110 file), đóng băng hai lần, cùng tree hash: `c6fd9996` (product `e7b92e49`), rồi
  `1e90ca0e` sau lượt đo 1 (chỉ `frontend/src`).
- Bản ghi W5: lớp đính chính `corrections/W05_RECORD_CORRECTION.json` (lượt đo 4 thiếu trong `MEASUREMENT_ATTEMPTS.json`;
  node harness 91 pass + 2 skip, không phải 93/93); tệp W5 không sửa.
- Dọn Tin học: `0d4c4f8b` (script/fixture render thời Tin học, danh sách tệp tường minh; `favicon.svg` của người dùng ngoài staging).

## 7. Còn mở / giới hạn

- **Duyệt hình (chặn merge):** `REVIEW.md` R1–R12. Chỉ người dùng ghi `APPROVED_BY_USER`.
- D5 chờ chọn phương án; cạnh hữu tỉ ngoài miền; mô hình chưa đo bố cục nghiêng; tứ diện thường ngoài vùng đa diện.
- Phát hiện từ lượt đo 2: không có stylesheet thì canvas mobile phình vô hạn (`renderer.setSize(w, h, false)` giao cỡ CSS cho
  stylesheet) — chỉ xảy ra khi trang tải hỏng, không sửa ở lượt này.
- Kỹ năng: Ponytail review đã áp dụng (`e7b92e49`, cùng bước rà `1e90ca0e`); Superpowers dùng ở mức quy trình (kế hoạch,
  nền đỏ, kiểm trước khi tuyên bố); Karpathy, UI UX Pro Max, Graphify **không gọi chính thức** — không tuyên bố đã dùng.

## 8. Khoảng trống kiến trúc

- Toạ độ ℚ³ là trần biểu diễn: họ có cạnh hữu tỉ của tam giác đều cần khung đồng dạng λ (chạm interpreter, hậu điều kiện,
  grounding, nhãn cảnh) — người dùng chưa chọn.
- Bộ đọc ràng buộc hình dạng vẫn là từ vựng đóng; compiler tất định (tầng C) vẫn chưa bật.
- Khung nhìn không tự khớp lại sau cú xoay tự do (giữ theo D6); sau sửa lượt này tâm quỹ đạo là tâm hình nên lề còn 85–92 px ở
  desktop với cú xoay W4.
