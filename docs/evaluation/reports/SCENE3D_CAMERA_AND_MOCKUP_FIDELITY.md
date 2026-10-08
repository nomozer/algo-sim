# SCENE3D_CAMERA_AND_MOCKUP_FIDELITY

**Ngày:** 2026-09-11 · **Nhánh:** `main` · **Gốc:** `56350f7` → **Đỉnh:** `ceb6854`
**Trạng thái:** mã đã xong, **chờ người dùng duyệt bằng mắt**.

---

## 0. Bốn lỗi thật đã tìm ra, và mỗi lỗi được sửa bằng gì

| # | Lỗi | Bằng chứng nó có thật | Bản sửa |
|---|---|---|---|
| ① | **Trục quay trôi.** `OrbitControls` chụp `camera.up` **một lần trong hàm dựng**; `scene3d-view.tsx` đặt `cam.up = (0,0,1)` sau đó ⇒ controls quay quanh Y còn `lookAt` dựng tư thế theo Z | chuẩn trục trung bình **0,608–0,680** (bàn xoay = 1,000); một cú kéo chỉ đi được ~60 % biên độ | `HUONG_LEN_HINH_HOC` thành nguồn duy nhất; đặt `cam.up` **trước** `new OrbitControls` (`8c4bad6`) |
| ② | **Xanh tự động.** Nơi gọi `buildObject3D` rơi về `highlightedAt(scene, buoc)` khi không có `selected_id`, tức tô `MAU.highlight` cho mọi vật *vừa dựng ở bước này* | ảnh «trước» của p2/p4/p5: **cả khối màu xanh** khi người học chưa bấm gì | `MAU.highlight` chỉ bật khi có `selected_id` thật (`19b5ab0`) |
| ③ | **Nét không có bề dày.** WebGL **bỏ qua** `LineBasicMaterial.linewidth`, nên token khai 2,8 / 1,6 / 3,5 px mà màn hình vẽ 1 px cho tất cả | bề dày trung vị đo trên ảnh sản phẩm: **1,89 px cho mọi vai** | `Line2`/`LineSegments2` + `LineMaterial`, bề dày theo pixel CSS (`30af867`) |
| ④ | **Khối cong không có nét nào.** Mặt trơn không có cạnh thật nên `EdgesGeometry` vô dụng | ảnh «trước» của p4/p5: một **vệt xám không vành, không đường sinh, không trục** | đường bao phụ thuộc camera, dạng đóng (`3e322a7`) |

Ba bản sửa kèm theo, mỗi bản cũng là một lỗi đo được — chi tiết ở §4.

---

## 1. Bằng chứng video

`ab.mp4` và `af.mp4` đọc được bằng **Google Chrome bản chính hãng** (máy không có
`ffmpeg`/`ffprobe`; Chrome có sẵn bộ giải mã H.264 nên nó là công cụ tương
đương). Trích 16 khung mỗi video ra `D:\tmp\algosim-oracle-frames\`, **không**
chép vào repository.

| | đọc được | cỡ | thời lượng | nó cho thấy gì |
|---|---|---|---|---|
| `ab.mp4` | có | 1500×562 | 14,98 s | Chuyển động ĐÚNG: xoay bàn xoay quanh trục đứng, đỉnh `S` luôn ở trên qua mọi khung. **Không phải AlgoSim** — thanh công cụ *"Mặc định · Đứng · Bằng · Cạnh"* và dòng *"Kéo để quay…"* không tồn tại trong kho này, kể cả ở commit prototype đã xoá. Dùng làm oracle **chuyển động**, không dùng làm oracle bố cục. |
| `af.mp4` | có | 1756×750 | 11,69 s | Chuyển động SAI, và đúng là AlgoSim (*"Hình dựng theo từng bước"*, *"Tách khối"*). Kéo chuột gần như **không xoay** hình; mặt phẳng và ba điểm hiện **màu xanh** dù chưa ai bấm. Tức nó chứa cả lỗi ① lẫn lỗi ②. |

---

## 2. Cổng đo, và chúng nói gì

Hai cổng mới, đều chạy trên **bản dựng sản phẩm** (`dist/`), 0 lượt gọi model.

### 2.1 `scene3d-orbit-gate.mjs` — quay

Đọc tư thế camera ngược từ `viewMatrix` (camera nằm trong closure, không có
đường nào chạm tới). Kết quả trên đỉnh `ceb6854`:

| ca | trạng thái | một cú kéo | ‖trục‖ | cos(cực) chạm | snap | cấp phát khi kéo | cửa sổ đứng yên |
|---|---|---|---|---|---|---|---|
| p1 | **DAT** | 438° | 1,000 | −1,00 … 1,00 | 0 | 0 | 0,0° |
| p6 | **DAT** | 437° | 0,999 | −1,00 … 1,00 | 0 | 0 | 0,0° |
| p7 | **DAT** | 443° | 1,000 | −1,00 … 1,00 | 0 | 0 | 0,0° |

`cos(cực)` chạm cả `−1` lẫn `+1` nghĩa là **cả đỉnh lẫn đáy** đều tới được.
Cửa sổ đứng yên `0,0°` là phép tự kiểm: không ai chạm chuột thì phép đo phải
đọc ra 0.

### 2.2 `scene3d-fidelity-gate.mjs` — trung thực thị giác

Chỉ tin **điểm ảnh của canvas sản phẩm**. Kết quả: **10/10 DAT**.

| ca | khung nhìn | chiếm (ngang/dọc) | tràn khung | bề dày trung vị | điểm cam | điểm xanh | điểm xám | nhãn (ngoài/đè) | Δ nét khuất |
|---|---|---|---|---|---|---|---|---|---|
| p1 | 1440×900 | 0,283 / 0,659 | không | 3,35 px | 714 | **0** | 2074 | 6 (0/0) | 0,988 |
| p2 | 1440×900 | 0,209 / 0,657 | không | 2,74 px | – | **0** | 1367 | 6 (0/0) | 0,988 |
| p3 | 1440×900 | 0,306 / 0,453 | không | 3,47 px | 413 | **0** | 508 | 3 (0/0) | 0,982 |
| p4 | 1440×900 | 0,221 / 0,565 | không | 2,97 px | – | **0** | 749 | 4 (0/0) | 0,969 |
| p5 | 1440×900 | 0,149 / 0,576 | không | 2,96 px | – | **0** | 469 | 4 (0/0) | 0,998 |
| p6 | 1440×900 | 0,243 / 0,670 | không | 2,74 px | 383 | **0** | 900 | 4 (0/0) | 0,990 |
| p7 | 1440×900 | 0,250 / 0,596 | không | 3,21 px | 378 | **0** | 912 | 5 (0/0) | 0,990 |
| p1 | 390×844 | 0,606 / 0,674 | không | 3,27 px | 508 | **0** | 1453 | 5 (0/0) | 0,985 |
| p6 | 390×844 | 0,517 / 0,685 | không | 2,74 px | 189 | **0** | 619 | 4 (0/0) | 0,992 |
| p7 | 390×844 | 0,533 / 0,594 | không | 3,41 px | 182 | **0** | 676 | 5 (0/0) | 0,973 |

*Điểm cam* = gần `#D95A43` (thiết diện) · *điểm xanh* = gần `#0075DE` · *điểm
xám* = gần `#7D7975` (nét khuất) · *Δ nét khuất* = tỉ lệ điểm ảnh xám **đổi
chỗ** sau một cú xoay.

Nhãn có đủ theo yêu cầu: `T` (p1) · `C` (p3) · `E` (p6, p7) · `OK` (p4, p6) ·
`OS` (p5, p7). Kiểu chữ đo từ DOM: **15 px / 600 / `#1f1f1f` / viền 3,2 px /
không ô nền**.

---

## 3. Mười phép tiêm lỗi — tất cả đều bị bắt

| # | Phép tiêm | Cổng bắt | Trạng thái phát ra |
|---|---|---|---|
| ① | đặt z-up **sau** constructor controls | quay | `TRUC_TROI` (‖trục‖ 0,537; vòng 50°) |
| ② | chặn phương vị ±45° | quay | `KHONG_DU_VONG` (vòng 79°) |
| ③ | bật auto-fit trong lúc xoay | quay | `CANH_KHONG_DUNG` (đệ quy fit→update→change) |
| ④ | cạnh thấy về `THREE.Line` 1 px | thị giác | `NET_QUA_MANH` (p1, cả hai khung nhìn) |
| ⑤ | để `target` kích hoạt highlight | thị giác | `XANH_TU_DONG` (p4: **3781** điểm xanh) |
| ⑥ | bỏ đường bao khối cong | thị giác | `CANH_RONG` (p4: mực tụt còn 0,0004) |
| ⑦ | nạp cảnh **rỗng** | thị giác | `KHONG_DUNG_DUOC` |
| ⑧ | chunk JS bị mất (404, không fallback) | thị giác | `KHONG_DUNG_DUOC` |
| ⑨ | `dist/` cũ hơn `src/` | cả hai | `DIST_CU` — xem §4.4 |
| ⑩ | *(nền đỏ đơn vị)* dựng controls trước khi đặt `up` | vitest | `scene3d-orbit-lifecycle.test.tsx` đỏ |

⚠️ Phép tiêm ④ **không** làm p4 đỏ, và đó là đúng: nét của p4 đến từ
`scene3d-silhouette.ts` chứ không qua `duongHaiLuot`. Phép tiêm chỉ chạm một
đường mã, nên nó chỉ đỏ ở nơi đường mã ấy chạy.

⚠️ Phép tiêm ⑦ phát `KHONG_DUNG_DUOC` chứ không phải `CANH_RONG`: cảnh không có
vật nào thì `Scene3DExplorer` không dựng canvas nào cả. Vẫn là một trạng thái
**có tên**, đúng yêu cầu.

---

## 4. Bốn lỗi của CHÍNH BỘ ĐO, tìm ra trong lúc làm

Ghi lại vì mỗi lỗi đều đã cho một kết luận sai, và ba trong bốn đều "trông như
một lỗi sản phẩm".

**4.1 Cổng quay báo `TRUC_TROI` cho p6/p7 trong khi sản phẩm đúng.** Bản đầu
nhận dạng `viewMatrix` bằng cách đếm tần suất **giá trị**; p6/p7 có nhiều vành
cùng tâm nên các `modelViewMatrix` trùng nhau và áp đảo. Dấu hiệu bắt được:
**cửa sổ đứng yên khác 0** (1,6–1,9° khi không ai chạm chuột). Sửa bằng cách
nhóm theo **vị trí uniform**; cửa sổ ấy về đúng 0,0°.

**4.2 Cổng thị giác đọc `chiếm = 0,999` ở mọi ca.** Ngưỡng mực để ở 232, trong
khi nền khung là gradient `L ≈ 227…248` và mảng tô khối (opacity 0,07) rơi vào
`L ≈ 230` — **nền và mảng tô cùng một dải**. Cổng đang đo nền. Hạ ngưỡng xuống
200 (dưới hẳn dải nền, trên hẳn mọi nét).

**4.3 `Δ nét khuất` đọc 0,016 trong khi nét khuất đã dịch hẳn.** Bản đầu so
**số lượng** điểm ảnh xám trước/sau khi xoay; hai ảnh khác hẳn nhau vẫn có thể
cùng số điểm. Đổi sang hiệu đối xứng của hai **mặt nạ vị trí**: 0,98–0,99.

**4.4 Một phép tiêm lỗi đo phải `dist/` của phép tiêm TRƯỚC ĐÓ.** Phép tiêm ⑥
không biên dịch được, `npm run build` đỏ, `--bo-qua-build` bỏ qua, và cổng chạy
trên bản dựng cũ — trả về đúng một trạng thái lỗi nhưng của sai nguyên nhân.
Thêm `kiemDistMoi()` vào **cả hai** cổng; đã kiểm nó đỏ được. Đây chính là cổng
`build-freshness` đã đi theo nhánh prototype bị từ chối (`CLAUDE.md §3`).

Cùng loại, ở phía sản phẩm: một lượt chụp đọc ra p4 chiếm 0,22 khung thay vì
0,565 — hoá ra **khớp khung chạy trước khi canvas có kích thước cuối**, và nó
**chập chờn** giữa các lượt chạy. Sửa bằng `ResizeObserver`, chỉ khớp lại khi
người dùng chưa tương tác. Ba lượt chạy liên tiếp sau đó cho cùng một số.

---

## 5. Hiệu năng — có hồi quy ở khung nhìn nhỏ, khai thẳng

Đo bằng `scene3d-interaction-probe.mjs`, 5 lần lặp × 3 ca × 2 khung nhìn.
Ngưỡng khai **trước** khi đo: `p95 ≤ baseline × 1,15`; tỉ lệ khung rơi không
tăng quá 5 điểm phần trăm.

| bản | khung nhìn | p50 | **p95** | khung rơi | ‖trục‖ | góc/cú kéo |
|---|---|---|---|---|---|---|
| A baseline `e6c2330` | 1440×900 | 14,4 | **20,9** | 0,10 % | – | 324° |
| E hỏng `56350f7` | 1440×900 | 16,7 | **21,4** | 0,00 % | 0,61–0,68 | 202° |
| **F bản này** | 1440×900 | 19,4 | **20,9** | **0,00 %** | **1,000** | 342° |
| A baseline `e6c2330` | 390×844 | 6,9 | **7,9** | 0,05 % | – | 256° |
| E hỏng `56350f7` | 390×844 | 6,9 | **8,8** | 0,11 % | 0,61–0,68 | 187° |
| **F bản này** | 390×844 | 7,0 | **12,1** | **0,11 %** | **1,000** | 251° |

- **1440×900: ĐẠT.** p95 = 20,9 ms, **đúng bằng baseline**, trần 24,0 ms. 0 khung rơi.
- **390×844: VƯỢT TRẦN.** p95 = 12,1 ms so với trần 9,1 ms (×1,53). **p50 thì
  không đổi** (7,0 so với 6,9) — tức khung điển hình y như cũ, chỉ cái đuôi dày
  lên. Tỉ lệ khung rơi +0,06 điểm %, trong ngưỡng.

Hai tối ưu đã áp, mỗi cái đo lại: tắt `alphaToCoverage` và `VONG_CHIA_BAO`
96 → 48. Chúng kéo p95 desktop từ **27,4 xuống 20,9 ms**.

Một giả thuyết đã bị chính phép đo **bác**: bỏ `opacity: 0.75` của nét khuất
được cho là sẽ rẻ hơn (rút khỏi hàng đợi trong suốt); đo lại thì p95 mobile đi
từ 12,1 **lên** 12,6 ms. Thay đổi vẫn giữ vì lý do **thị giác** (mockup vẽ nét
khuất đặc), và chú thích trong mã ghi lại đúng điều này để lần sau không ai đi
lại hướng ấy.

⚠️ **Giới hạn của số đo:** cả ba bản đều đo dưới **SwiftShader** (GPU phần mềm,
`--use-angle=swiftshader`). Nét rộng là dải tam giác nên nặng ở khâu tô, và
rasteriser phần mềm phóng đại đúng khoản đó. So sánh **tương đối** giữa ba bản
là hợp lệ vì cùng điều kiện; **con số tuyệt đối không dự đoán được** hiệu năng
trên GPU thật. Chưa có phép đo nào trên GPU thật trong wave này.

---

## 6. Báo cáo cuối

```
SCENE3D_CAMERA_AND_MOCKUP_FIDELITY = DONE_PENDING_VISUAL_APPROVAL
CAMERA_LIFECYCLE_FIX               = DONE — cam.up đặt trước new OrbitControls,
                                     nguồn duy nhất HUONG_LEN_HINH_HOC,
                                     khoá bằng scene3d-orbit-lifecycle.test.tsx
ROTATION_AXIS_STABILITY            = ‖trục‖ 0,999–1,000 (trước: 0,608–0,680)
HORIZONTAL_ORBIT_RANGE             = 437–443° cho MỘT cú kéo; phương vị không chặn
TOP_BOTTOM_VIEWS                   = REACHED — cos(cực) chạm cả −1,00 và +1,00;
                                     ảnh sáu hướng ở CONTACT_GOC_NHIN.png
AUTO_FIT_DURING_ORBIT              = 0 (cấp phát khi kéo = 0 ở mọi lượt; thêm cờ
                                     dangKeoRef để khớp khung nhường tương tác)
AB_VIDEO_MOTION_MATCH              = ĐẠT về ĐỊNH TÍNH — xoay bàn xoay quanh trục
                                     đứng, trục ổn định, damping tự tắt. ⚠️ ab.mp4
                                     KHÔNG phải AlgoSim (thanh "Mặc định · Đứng ·
                                     Bằng · Cạnh" không tồn tại trong kho), nên nó
                                     là oracle CHUYỂN ĐỘNG, không phải oracle bố cục.
AF_REGRESSION_REMOVED              = YES — hai lỗi af.mp4 cho thấy đều hết: kéo
                                     xoay đủ biên độ, và 0 điểm ảnh xanh khi chưa chọn
VISIBLE_EDGE_WIDTH_PX              = trung vị 2,74–3,47 px trên 10 cấu hình
                                     (token 2,8; trước bản này: 1,89 px cho mọi vai)
HIDDEN_EDGE_STATUS                 = #7D7975, nét đứt 7/5, GreaterDepth, xám đặc;
                                     đổi chỗ 0,969–0,998 sau một cú xoay
SECTION_COLOR_STATUS               = #D95A43 ở p1/p3/p6/p7 (182–714 điểm ảnh);
                                     p4/p5 không có thiết diện nên bằng 0, đúng
CURVED_SOLID_SILHOUETTES           = DONE — trụ: hai vành + hai đường sinh + trục OK;
                                     nón: vành đáy + hai đường sinh từ đỉnh + trục OS;
                                     cầu: đường bao ngoài + thiết diện C thấy/khuất.
                                     Toán dạng đóng, khoá bằng ĐIỀU KIỆN TIẾP TUYẾN
P1_P7_BROWSER_ACCEPTANCE           = 7/7 DAT tại 1440×900
ROTATED_CASES                      = 10/10 — mỗi ca chụp thêm một ảnh SAU KHI XOAY
RESPONSIVE_CASES                   = 3/3 DAT tại 390×844 (p1, p6, p7)
PERFORMANCE_REGRESSION             = 1440×900 KHÔNG (p95 20,9 = baseline 20,9,
                                     trần 24,0) · 390×844 CÓ, VƯỢT TRẦN
                                     (p95 12,1 so với trần 9,1; p50 không đổi
                                     7,0/6,9; khung rơi +0,06 điểm %).
                                     Đo dưới SwiftShader — xem §5.
FAULT_INJECTIONS                   = 10/10 bị bắt, mỗi cái một TRẠNG THÁI CÓ TÊN
BACKEND_CHANGED                    = NO (git diff 56350f7..HEAD -- backend: rỗng)
MODEL_FACING_CHANGED               = NO
CANDIDATE_HASH_BEFORE/AFTER        = 96a9368b50603c79… / 96a9368b50603c79… (không đổi;
                                     geometry/ không nằm trong MEASURED_SYSTEM_PATHS)
CACHE_VERSION_BEFORE/AFTER         = 95 / 95
APPLICATION_LLM_CALLS              = 0
REAL_PROVIDER_CALLS                = 0
HISTORICAL_ARTIFACTS_CHANGED       = NO — số đo mới ghi vào scene3d-fidelity/,
                                     scene3d-orbit-gate/; artifact chẩn đoán cũ
                                     trong scene3d-interaction-smoothness/ nguyên vẹn
TEST_RESULTS                       = vitest 873/873 · tsc -b + vite build xanh ·
                                     freeze --verify khớp · git diff --check sạch
COMMITS                            = 8 (7 commit mã + 1 commit báo cáo)
WORKING_TREE                       = sạch sau commit cuối
VIDEO_EVIDENCE_PATH                = D:\tmp\algosim-fidelity\after-camera-and-visual-fix.webm
                                     (5,96 MB · WebM/VP9 — máy không có ffmpeg, Chrome
                                     ghi thẳng canvas bằng MediaRecorder)
CONTACT_SHEET_PATH                 = D:\tmp\algosim-fidelity\CONTACT_P1_P7.png
                                     D:\tmp\algosim-fidelity\CONTACT_GOC_NHIN.png
USER_VISUAL_APPROVAL               = PENDING
NEXT_ACTION                        = USER_REVIEW_OF_MOTION_AND_CONTACT_SHEET
```

---

## 7. Giới hạn còn lại

1. **p95 ở 390×844 vượt trần** (§5). Chưa tối ưu thêm vì hai hướng còn lại đều
   đánh đổi thị giác: giảm bề dày nét, hoặc bỏ lượt vẽ nét khuất.
2. **Chưa đo trên GPU thật.** Mọi số hiệu năng đến từ SwiftShader.
3. **Nhãn `T`/`C`/`E` suy từ `id`**, vì backend không phát `notation` cho ba vai
   này. `kyHieuHinh` chỉ nhận `id` khi bản thân `id` đã là một ký hiệu toán học;
   nền đỏ của nó là chính những `id` từng gây lỗi cũ (`plane_MNP`, `V_AMNP`,
   `ABCD_base`, `S.ABCD`) — tất cả đều bị từ chối. Lối sạch là backend phát
   `notation`, và khi ấy đường này tự ngừng được dùng.
4. **Thiết diện tròn/elip chưa có mảng tô**, chỉ có vành. Đa giác (p1) thì đã có.
5. **p3 chiếm 0,453 khung theo chiều dọc**, dưới dải 0,50–0,80 một chút. Phép đo
   chỉ đếm NÉT (ngưỡng mực 200) nên mảng tô rất nhạt của mặt phẳng không được
   tính; con số thật cao hơn. Không nới ngưỡng để làm nó đạt.
6. **Guard thiết diện bẹp vẫn `IMPLEMENTED_NOT_VALIDATED`** trên bộ ca thật —
   wave này không đụng tới nó.
