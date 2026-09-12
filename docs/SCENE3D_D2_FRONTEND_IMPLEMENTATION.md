# SCENE3D_D2_FRONTEND_IMPLEMENTATION

Triển khai hướng thị giác D2 đã duyệt vào sản phẩm. Năm commit, `main`,
`eb6d7d5 → 0d9b67d`. Không đụng backend, không đụng bề mặt mô hình, không đổi
một toạ độ hay đáp số nào.

```
START_HEAD   = eb6d7d5      END_HEAD = 0d9b67d
BACKEND_CHANGED = NO        MODEL_FACING_CHANGED = NO
CANDIDATE_HASH  = 96a9368b50603c79… (trước = sau, 92 file)
CACHE_VERSION   = 95 → 95   APPLICATION_LLM_CALLS = 0
GEOMETRY_MODIFIED = false   P1_P7_FINAL_GEOMETRY_PARITY = 8/8 EXACT
```

Ảnh chụp hình học chuẩn hoá trước và sau wave cho **cùng một băm tổng**
`559d0e8eb275f8a4` trên tám ca (P1–P7 + bài mẫu), so từng envelope, từng vật,
từng chuỗi sự kiện và từng đồ thị phụ thuộc.

## 1. Thiết diện hiện dần — `3bdce97`

Trace mang bốn sự kiện `action: "EXTEND"` (mỗi sự kiện nối một cạnh, kèm
`face_index` trong `object.steps`) rồi mới tới `STEP` đóng hình. Renderer dựng
trọn `polygon` ngay từ sự kiện đầu, nên **năm bước cuối cho năm khung hình trùng
khít**. `EventAction` khai `"EXTEND"` từ đầu mà không dòng mã nào đọc nó.

- `tienTrinhDung` (`scene3d-model.ts`) — chỗ DUY NHẤT đọc `SceneEvent.action`;
- `canhThietDien` (`scene3d-subentities.ts`) — thẩm quyền DUY NHẤT cho *"miếng
  cắt gồm những cạnh nào"*; cây phân rã và renderer dùng chung, không dựng phép
  suy hình học thứ hai.

Đo trên sản phẩm, 1440×900: bước 7 → 10 cho **8606 → 8650 → 8695 → 8856** điểm
mực, bốn băm ảnh khác nhau.

```
STEP_7/8/9/10/11_SEGMENTS = 1 / 2 / 3 / 4 / 4        (19 test, 3 phép tiêm)
STEP_7_TO_10_FILL = 0        STEP_11_FILL = 1 ở tầng đối tượng
```

⚠️ **Chưa xong: bước 11 vẫn trùng BYTE với bước 10 trên khung.** Mảng tô được
dựng (test đơn vị xanh: đúng một mesh không phải vật nét) nhưng không ra điểm
ảnh nào. Hai ảnh giống nhau tới từng byte nên đây không phải chuyện tô quá nhạt.
Khuyết tật không do wave này tạo ra — mảng tô có từ wave trước — nhưng wave này
làm nó lộ ra, vì trước đây không ai so hai bước liền nhau. **Để xử riêng.**

## 2. DPR — `c024815`

`setPixelRatio` chưa bao giờ được gọi, nên màn retina nhận bản vẽ 1× phóng to.
Điểm ảnh thô cắt ngang một nét: `253 228 178 122 58 51 101 152 197 220` (dốc
thoải tám điểm ảnh, lõi chỉ tới 51) so với `253 254 253 83 58 26 123 220` khi vẽ
thẳng ở 2×.

```
DPR_POLICY = min(devicePixelRatio, 2)
DPR1  CSS 1318×610  → khung vẽ 1318×610
DPR2  CSS 1318×610  → khung vẽ 2636×1220
DPR2_EDGE_SHARPNESS: 1,506 → 0,748 px CSS (để bàn) · 1,523 → 0,750 (di động)
                     hẹp hơn 2,01× và 2,03×
```

⚠️ **Điều kiện đi kèm BẮT BUỘC:** `setSize(w, h, true)`. Thẻ `<canvas>` không có
luật CSS nào ràng cỡ, nên giữ `false` sẽ làm nó phình thành 2636×1220 px CSS
trong khung 1318×610 — và `overflow: hidden` của `.geo3d-canvas` **giấu chỗ vỡ
đi**, nên nó sẽ ship dưới dạng "hình bị cắt" chứ không dưới dạng một lỗi.

Bề dày px CSS bất biến theo DPR (lệch ≤ 0,03 px) vì `LineMaterial.resolution`
vẫn lấy cỡ CSS. Thêm phép theo dõi DPR đổi giữa phiên: kéo cửa sổ sang màn hình
khác không phát `resize` và không đổi cỡ CSS.

## 3. Ngôn ngữ thị giác D2 — `721f736`

Token gom về MỘT nguồn `scene3d-tokens.ts`; renderer, test và mọi phép đo đọc
chung. Hai chỗ bảng cũ để hổng, cả hai đo được: thiết diện **thấy** và **khuất**
dùng chung một màu (Δ = 0) · cạnh khuất ↔ mặt phẳng Δ = 10,4. Δ nhỏ nhất giữa
sáu vai nay là **69,9**.

Mảng tô: chỗ mặt phẳng cắt khối từng là ba lớp cộng dồn 0,07 + 0,07 + 0,14; hạ
hai lớp nền xuống 0,035 / 0,022, giữ thiết diện 0,15.

Chấm điểm chuyển sang cỡ MÀN HÌNH (4,4 px). Dùng **độ sâu trong không gian
camera**, không dùng khoảng cách Euclid: cỡ chiếu phối cảnh tỉ lệ `1/(−z)`, lấy
khoảng cách Euclid sẽ phóng to chấm ở rìa khung.

Lấp khung 0,66 → 0,84. **Không bù `linewidth` bằng hằng số** — renderer đã được
chứng là tuân theo token đúng `1,001 × linewidth + 0,02`.

## 4. Bộ giải nhãn — `c375c41`

`STRICT_CLEARANCE_WITH_ADAPTIVE_REFIT`. Mười sáu hướng × bốn bán kính. Khoảng
cách tối thiểu là **ràng buộc cứng** (loại thẳng ứng viên vi phạm), "gần điểm
neo" chỉ còn là **giá mềm** xếp hạng ứng viên đã hợp lệ — gộp làm một tổng phạt
thì một vị trí đè lên cạnh vẫn thắng nếu nó gần neo hơn.

Không giấu chữ, không nới ngầm: hết chỗ hợp lệ thì lùi camera từng nấc 6 %, tới
sàn chiếm dọc 0,72 thì dừng và khai thiếu.

Sửa kèm **ba lệch THỨ TỰ** cùng lớp, đều đo được:
1. bố trí nhãn không chạy lại khi nội dung cảnh đổi — bước 2/11 báo 0 đoạn nét
   trong khi khối đã dựng;
2. nhãn hỏi `objectsAt` còn hình hỏi `entitiesPresentAt` — hai thẩm quyền cho
   cùng một câu hỏi;
3. neo nhãn nạp trong `useEffect` chạy sau lượt dựng, nên vật vừa xuất hiện mất
   tên đúng một bước: `(MNP)` từng chỉ hiện ở 7/11 dù mặt phẳng đã vẽ ở 6/11.

`plane3` nay có nhãn, neo ở góc cao nhất của miếng, chỉ in `notation`.

## 5. Cổng nghiệm thu — `0d9b67d`

`scene3d-d2-gate.mjs`: P1–P7 × {1440×900, 390×844} × DPR {1, 2} = 28 ô.

Cổng thị giác cũ phải sửa ba chỗ vì nó **đang đo sai**:

| chỗ sai | hệ quả |
|---|---|
| ghi cứng `#d95a43`/`#7d7975`/`#1f1f1f` | đổi bảng màu là đếm hụt và báo `THIEU_DUONG_BAO` cho bốn ca lành |
| lấy số điểm ảnh XÁM làm đại diện cho "có đường bao" | đường bao khối cong phần lớn là phần THẤY: p3 có 1829 điểm cạnh thấy mà chỉ 68 điểm xám — hỏng theo cả hai chiều |
| `doBeDayCucBo` quét theo hàng ngang | thổi phồng nét nghiêng: 2,8 px @20° đọc ra 7,46 px |

Tràn khung nay xét theo **hộp bao hình HỮU HẠN**: mặt phẳng và đường thẳng vô
hạn cố ý bị loại khỏi phép khớp khung nên mực của chúng chạm mép là hệ quả đã
chọn. Ba ca không có vật vô hạn cho 0/18 ảnh chạm mép; mười ảnh chạm mép đều
thuộc đúng bốn ca có vật vô hạn.

Cổng bắt được **hai lỗi bộ giải nhãn không tự thấy**, cả hai đã sửa: bộ giải đo
tới TIM nét trong khi mắt thấy MÉP nét (thiếu nửa bề dày; chấm điểm là một đĩa
chứ không phải một điểm) · vành thiết diện tròn/elip vẽ bằng `RingGeometry` nên
không có `instanceStart`, bộ giải mù trước đúng cái biên bài đang hỏi.

```
P1_P7_BROWSER_ACCEPTANCE = 22/28 ô ĐẠT   (trước khi sửa hai lỗi trên: 18/28)
LABELS_HIDDEN = 0        LABEL_OVERLAPS = 0        control overlay che nhãn = 0
```

`LABEL_LAYOUT_UNSATISFIABLE_CASES` — sáu ô, đã lùi tới sàn mà vẫn không có
nghiệm; **không nhãn nào bị giấu, không ngưỡng nào bị nới ngầm**:

| ca | khung | DPR | nhãn↔mực đo được | ngưỡng |
|---|---|---|---|---|
| p1 | 390×844 | 1 / 2 | 3,00 / 1,50 | 4 |
| p3 | 1440×900 | 2 | 5,83 | 6 |
| p6 | 1440×900 | 1 / 2 | 5,00 / 4,00 | 6 |
| p6 | 390×844 | 1 / 2 | 3,61 / 3,91 | 4 |

## 6. Hiệu năng — GPU thật, 3 lượt × 8 s xoay liên tục

| khung | DPR | điểm ảnh | khung TB | p50 (ba lượt) | p95 (ba lượt) | >32 ms |
|---|---|---|---|---|---|---|
| để bàn | 1 | 803 980 | 6,09 ms | 7 / 7 / 7 | 14 / 14 / 13,9 | 0 / 3945 |
| để bàn | 2 | 3 215 920 | 7,32 ms | 13,8 / 7 / 7,1 | **20,8** / 14 / 14 | 0 / 3280 |
| di động | 1 | 142 120 | 5,39 ms | 6,9 | 7 | 3 / 4452 |
| di động | 2 | 568 480 | 5,40 ms | 6,9 | 7 / 7 / 7,1 | 2 / 4443 |

⚠️ **Một lượt để bàn ở DPR 2 đọc p95 = 20,8 ms, vượt trần 16,7 ms**; hai lượt còn
lại đọc 14,0. Khai ra chứ không lấy trung bình che đi.

⚠️ `REAL_PHONE_GPU_NOT_ESTABLISHED` — "di động" là khung nhìn 390×844 chạy trên
GPU máy để bàn. Nó đo chi phí tô theo độ phân giải, **không** đo máy điện thoại
thật. Và `requestAnimationFrame` headless không khoá 60 Hz, nên khoảng cách giữa
hai khung là **chi phí dựng**, không phải nhịp màn hình.

## 7. Phép tiêm lỗi

| phép tiêm | bắt được bởi | kết quả |
|---|---|---|
| bỏ đọc `EXTEND` | `scene3d-progressive-section.test.ts` | ĐỎ (7/19) |
| vẽ đủ bốn cạnh từ bước 7 | như trên | ĐỎ (4/19) |
| tô thiết diện trước bước 11 | như trên | ĐỎ (9/19) |
| bỏ trần DPR | `scene3d-dpr.test.ts` | ĐỎ (3/15) |
| cảnh rỗng nhưng báo PASS | `scene3d-fidelity-gate.mjs --tiem canh-rong` | `KHONG_DUNG_DUOC` |
| thiếu chunk JS (nhận HTML fallback) | `--tiem thieu-chunk` | `KHONG_DUNG_DUOC` |
| `dist/` cũ hơn `src/` | `kiemDistMoi()` ở cả ba cổng | ném `DIST_CU` |

Hai phép tiêm còn lại — **bật DPR 2 nhưng giữ sai cỡ CSS** và **dùng cỡ khung vẽ
làm `resolution`** — chỉ tồn tại khi có GPU; `scene3d-d2-gate.mjs` có phép kiểm
tương ứng (`DPR_CSS_PHINH`, `DPR_BUFFER_SAI`) nhưng **chưa chạy phép tiêm để
chứng minh chúng đỏ được**. Nợ đã khai.

## 8. Còn lại

- `STEP_11_FILL` không ra điểm ảnh trên khung — khuyết tật mở, mục 1;
- sáu ô `LABEL_LAYOUT_UNSATISFIABLE`, mục 5 — cần người duyệt quyết: nới ngưỡng
  cho ca dày, cho phép giấu bớt nhãn, hay tăng bán kính thử;
- hai phép tiêm DPR chưa chạy, mục 7;
- `SECTION_NOTATION_DATA_CONTRACT = DEFERRED` — muốn thiết diện có tên thì backend
  phải phát `notation`; frontend không bịa được. Chữ `T` của P1 hiện cũng suy từ
  `id`, không từ dữ liệu.

`USER_VISUAL_APPROVAL = PENDING`. Không tự ghi `FINAL_VISUAL_APPROVAL`.
