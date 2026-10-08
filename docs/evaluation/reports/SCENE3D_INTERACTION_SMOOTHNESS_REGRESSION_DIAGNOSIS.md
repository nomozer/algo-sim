# SCENE3D_INTERACTION_SMOOTHNESS_REGRESSION_DIAGNOSIS

**Loại wave:** CHẨN ĐOÁN. Không sửa mã sản phẩm, không commit, không triển khai
wide-line hay bản vá tương tác.
**Ngày:** 2026-09-11 · **Nhánh:** `main` · **Đỉnh khi đo:** `56350f7`

---

## 0. Kết luận trong bốn câu

1. **Có hồi quy thật, và nó KHÔNG phải hồi quy hiệu năng.** Thời gian khung
   trước và sau gần như bằng nhau; không có khung nào biến mất.
2. Thứ hỏng là **TRỤC QUAY**. Trước `7f34286`, một cú kéo ngang quay hình quanh
   **một trục cố định**; sau `7f34286`, trục quay **đổi theo từng khung** — hình
   *lộn* thay vì *xoay bàn xoay*. Cảm giác "kém mượt" là cảm giác đó.
3. **Gốc rễ:** `OrbitControls` chụp `object.up` **một lần trong hàm dựng**
   (`_quat`), trong khi `scene3d-view.tsx` đặt `cam.up = (0,0,1)` **sau đó**.
   Controls tiếp tục quay quanh trục Y thế giới trong khi camera dựng khung theo
   trục Z — hai hệ quy chiếu lệch nhau, hợp của chúng là một trục trôi.
4. **Bản vá tối thiểu đã được ĐO, không phải suy đoán:** dời đúng một dòng
   `cam.up.set(0,0,1)` lên **trước** `new OrbitControls(...)` đưa trục quay về
   `[0, 0, 1]` cố định và biên độ quay khớp baseline.

---

## 1. Triệu chứng và cách tái hiện

Người dùng báo "xoay hình kém mượt" sau `7f34286`
(*feat(geometry): đưa ngôn ngữ hình học đã duyệt vào renderer*).

Bộ đo: `frontend/scripts/scene3d-interaction-probe.mjs` — tiêm móc bằng
`Page.addScriptToEvaluateOnNewDocument` **trước mọi script của trang**, bọc
`requestAnimationFrame`, `HTMLCanvasElement.getContext` (rồi `drawElements`,
`drawArrays`, `createBuffer`, `createProgram`, `uniformMatrix4fv`) và
`Document.createElement`. Mỗi ca gồm ba cửa sổ liên tiếp: **đứng yên 1 s**
(cửa sổ chứng), **kéo 300 px trong 1 s** qua 60 bước `Input.dispatchMouseEvent`,
rồi **thả và theo dõi damping 1 s**.

Chạy từ **bản build sản phẩm** (`npm run build` → `dist/`, phục vụ tĩnh), không
qua dev server. Ba ca `p1`, `p6`, `p7` × hai khung nhìn `1440x900` và `390x844`
× 5 lần lặp = 30 lượt mỗi cấu hình.

---

## 2. Hiệu năng: KHÔNG có hồi quy

Gộp 30 lượt mỗi cấu hình (`BASELINE_INTERACTION.json`,
`CANDIDATE_INTERACTION.json`). Số dưới là trung bình của các phân vị theo lượt.

| | khung nhìn | khung đo | p50 (ms) | p95 (ms) | max (ms) | khung > 33,3 ms |
|---|---|---|---|---|---|---|
| baseline `e6c2330` | 1440×900 | 973 | 14,4 | **20,9** | 48,5 | 1 |
| candidate `56350f7` | 1440×900 | 930 | 16,7 | **21,4** | 27,9 | **0** |
| baseline `e6c2330` | 390×844 | 2126 | 6,9 | **7,9** | 34,7 | 1 |
| candidate `56350f7` | 390×844 | 2076 | 6,9 | **8,8** | 48,6 | 2 |

Chênh p95 là 0,5 ms (desktop) và 0,9 ms (mobile) — dưới một khung ở mọi nhịp
làm tươi. Tổng số khung rơi trên toàn bộ 60 lượt: **2 baseline / 2 candidate**.
Độ trễ con trỏ → khung vẽ: trung vị **0,20–0,21 ms**, không đổi.

Trong suốt cửa sổ kéo, ở **mọi** lượt của **cả hai** cấu hình:

```
capPhatBuffer = 0    capPhatProgram = 0    canvasTao = 0    glContext = 1
```

Không cấp phát buffer, không biên dịch shader, không tạo canvas mới, đúng một
ngữ cảnh WebGL. Số lệnh vẽ và số tam giác mỗi lượt cũng tương đương
(desktop ~1 742 → ~1 713 lệnh vẽ; ~167 915 → ~162 077 tam giác).

⇒ **`PERFORMANCE_REGRESSION = NO`.** Nếu wave sau đi tối ưu hiệu năng thì nó
đang chữa một bệnh không tồn tại.

---

## 3. Thứ thật sự hỏng: trục quay

### 3.1 Phép đo

Với hai ma trận model-view liên tiếp `A`, `B`, lấy `R = B · A⁻¹` rồi rút **trục**
của `R` (chuẩn hoá dấu để trục và trục đối không triệt tiêu nhau). Trung bình
các trục đơn vị qua cả cú kéo cho `trucQuayTrungBinh`.

Chỉ số quyết định là **‖trung bình‖**:

- **‖·‖ = 1** ⇔ mọi khung quay quanh **cùng một trục** → bàn xoay.
- **‖·‖ < 1** ⇔ trục **đổi giữa các khung** → lộn nhào. Càng nhỏ càng loạn.

### 3.2 Kết quả — ba cấu hình, cùng ca `p1`

| cấu hình | khung nhìn | trục trung bình | ‖trục‖ | tổng góc kéo |
|---|---|---|---|---|
| **A** baseline `e6c2330` | 1440×900 | `[0, 1, 0]` | **1,000** | 167,7° |
| **A** baseline `e6c2330` | 1440×900 | `[0, 1, 0]` | **1,000** | 336,2° |
| **A** baseline `e6c2330` | 390×844 | `[0, 1, 0]` | **1,000** | 248,7° |
| **A** baseline `e6c2330` | 390×844 | `[0, 1, 0]` | **1,000** | 254,4° |
| **E** candidate `56350f7` | 1440×900 | `[0,380, −0,062, 0,470]` | **0,608** | 121,9° |
| **E** candidate `56350f7` | 1440×900 | `[0,402, −0,052, 0,497]` | **0,641** | 203,8° |
| **E** candidate `56350f7` | 390×844 | `[0,375, −0,136, 0,537]` | **0,669** | 179,6° |
| **E** candidate `56350f7` | 390×844 | `[0,349, −0,124, 0,570]` | **0,680** | 188,2° |
| **D** biến thể (`up` đặt TRƯỚC) | 1440×900 | `[0, 0, 1]` | **1,000** | 168,6° |
| **D** biến thể (`up` đặt TRƯỚC) | 1440×900 | `[0, 0, 1]` | **1,000** | 336,3° |
| **D** biến thể (`up` đặt TRƯỚC) | 390×844 | `[0, 0, 1]` | **1,000** | 245,8° |
| **D** biến thể (`up` đặt TRƯỚC) | 390×844 | `[0, 0, 1]` | **1,000** | 254,8° |

Đọc bảng này theo hai chiều:

- **Cột ‖trục‖.** Baseline và biến thể D cho **đúng 1,000** ở cả bốn lượt — trục
  không nhúc nhích. Candidate cho **0,608 … 0,680** — trục trôi liên tục, và
  thành phần Y đổi lung tung (`−0,052 … −0,136`) trong khi X và Z cùng lớn. Đây
  là **chữ ký của một phép quay hợp từ hai trục không trùng nhau**.
- **Cột tổng góc.** Cùng một cú kéo 300 px, candidate quay được **~60 %** biên
  độ của baseline (ví dụ 179,6° so với 248,7° ở 390×844). Một phần chuyển động
  ngang bị đổ sang phương cực rồi bị chặn ở đó. Biến thể D trả biên độ về khớp
  baseline gần như tuyệt đối (245,8° / 248,7° và 336,3° / 336,2°).

Hai chiều đó cùng trỏ về một nguyên nhân, và biến thể D tắt **cả hai** cùng lúc.

---

## 4. Gốc rễ

`frontend/src/simulations/domains/geometry/scene3d-view.tsx`:

```
832    const cam = new THREE.PerspectiveCamera(50, 1, 0.1, 200);   // up = (0,1,0) mặc định
842    const dieuKhien = new OrbitControls(cam, renderer.domElement);
843    dieuKhien.enableDamping = true;
…
1016     const kn = khungNhinVua(hopBaoCuaDiem(diem), cam.fov, w / h, phuongViKhung());
1022     cam.up.set(...kn.huongLen);        // ← (0,0,1), ĐẶT SAU khi controls đã dựng
1025     dieuKhien.update();
```

`node_modules/three/examples/jsm/controls/OrbitControls.js` (three **0.185.1**):

```
405    // so camera.up is the orbit axis
406    this._quat = new Quaternion().setFromUnitVectors( object.up, new Vector3( 0, 1, 0 ) );
407    this._quatInverse = this._quat.clone().invert();
…
695            _v.applyQuaternion( this._quat );        // dùng trong update()
784            _v.applyQuaternion( this._quatInverse );
```

`_quat` được gán **đúng một lần, trong hàm dựng** — `grep -n '_quat'` trên cả
file trả về bốn dòng: một gán ở 406, một dẫn xuất ở 407, hai lần **đọc** ở 695
và 784. **Không có đường làm tươi nào**: không setter, không `update()` nào tính
lại nó.

Nên chuỗi sự kiện là:

1. `cam` sinh ra với `up = (0,1,0)`.
2. `new OrbitControls(cam, …)` chụp `_quat = setFromUnitVectors((0,1,0), (0,1,0))`
   = **đơn vị**. Từ giờ controls tin rằng trục quỹ đạo là **Y thế giới**.
3. Hàm khớp khung đặt `cam.up = (0,0,1)`.
4. Mỗi khung, `update()` quay vị trí camera quanh **Y** (theo `_quat` cũ), rồi
   `lookAt` dựng lại tư thế camera theo `object.up` = **Z** (giá trị mới).

Vị trí quay quanh một trục, tư thế dựng theo một trục khác. Hợp của hai phép ấy
là một phép quay có **trục phụ thuộc vị trí hiện tại**, tức là đổi mỗi khung —
đúng bằng ‖trục‖ 0,61–0,68 đo được.

### 4.1 Diff nào đưa lỗi vào

Ở `e6c2330` (baseline), `scene3d-view.tsx` **không có dòng `cam.up` nào cả**:

```bash
git show e6c2330:frontend/src/simulations/domains/geometry/scene3d-view.tsx \
  | grep -n 'cam\.up'      # → không kết quả
```

`up` ở nguyên `(0,1,0)`, khớp với `_quat` đơn vị ⇒ nhất quán ⇒ bàn xoay quanh Y.
`7f34286` thêm `cam.up.set(...kn.huongLen)` để thực thi camera z-up đã duyệt
(`GEOMETRY_Z_UP_AZ55_EL22_WITH_SECTION_GUARD`) — **hướng nhìn tĩnh thì đúng**,
nhưng đặt sai vị trí trong vòng đời nên phá tương tác. Đây là dạng lỗi kinh điển
của kho này theo `CLAUDE.md §2b.1`: *"một sửa chữa không nằm trên đường chạy
thật"* — ở đây là một giá trị được đặt **sau** người tiêu thụ duy nhất của nó.

---

## 5. Bản vá tối thiểu (đã đo, CHƯA triển khai)

Dời đúng một dòng — đặt `up` **trước** khi dựng controls:

```
const cam = new THREE.PerspectiveCamera(50, 1, 0.1, 200);
cam.up.set(0, 0, 1);                                    // ← thêm ở đây
…
const dieuKhien = new OrbitControls(cam, renderer.domElement);
```

Đo trong worktree tạm `/d/tmp/asim-var` trên `7f34286`, **không commit**, đã gỡ
worktree sau khi đo. Kết quả là hàng **D** ở bảng §3.2: trục về `[0, 0, 1]` cố
định (‖trục‖ = 1,000 ở cả bốn lượt), biên độ quay khớp baseline.

Ba việc bản vá thật vẫn phải làm, wave này **không** làm:

- **Giữ z-up nhưng phải quay quanh Z**, không quay về y-up. Biến thể D cho trục
  `[0,0,1]` chứ không phải `[0,1,0]` — tức là hướng nhìn đã duyệt được giữ
  nguyên, chỉ tương tác được sửa.
- Nếu về sau `huongLen` thành **động** (đổi theo ca), một dòng đặt trước là chưa
  đủ — lúc đó phải **dựng lại controls** hoặc gán lại `_quat`/`_quatInverse` khi
  `up` đổi. Hiện `huongLen` là hằng `[0,0,1]` nên chưa cần.
- Cần một **test khoá** dựng `OrbitControls` thật rồi khẳng định `_quat` khớp
  `cam.up` — nếu không, lần tới ai đó dời `cam.up.set` xuống dưới thì không có
  gì đỏ.

---

## 6. Cái đã loại trừ, và một giới hạn phải khai

**Đã loại trừ bằng số:**

| Nghi phạm | Bằng chứng loại trừ |
|---|---|
| Vẽ lại toàn cảnh khi kéo | `capPhatBuffer = 0`, `capPhatProgram = 0` ở cả 60 lượt |
| Dựng lại controls / canvas | `canvasTao = 0`, `glContext = 1` xuyên suốt cửa sổ kéo |
| `rotateSpeed` bị đổi | `grep 'rotateSpeed'` = 0 kết quả ở cả hai bản ⇒ mặc định 1,0 |
| `enableDamping` bị tắt | `true` ở cả `e6c2330:755` lẫn `56350f7:843` |
| Hàm khớp khung chạy giữa cú kéo | không cấp phát, và số bước nhảy > 12° **bằng nhau** ở mọi cấu hình (§6.1) |
| Guard thiết diện bẹp kích hoạt khi kéo | chỉ gọi trong nhánh khớp khung, mà nhánh đó không chạy |

### 6.1 Giới hạn: cửa sổ chứng ở 1440×900 bị nhiễu

Cửa sổ **đứng yên 1 s** tồn tại để chứng minh phép đo góc không tự bịa chuyển
động. Ở `390×844` nó sạch: tổng góc **0,84–1,81°** trên ~140 khung, so với
185–255° khi kéo — tỉ số tín/tạp ~150:1.

Ở `1440×900` nó **không sạch**: trung bình 175–291° (baseline) và 102–203°
(candidate) trên ~65 khung — cùng bậc với tín hiệu kéo. Nguyên nhân đã ghi sẵn
trong chú thích của bộ đo: ma trận đại diện mỗi khung là ma trận model-view
**đầu tiên**, nên khi thứ tự vẽ đổi giữa hai khung thì "góc" đo được là góc giữa
hai **vật khác nhau**. Nhiễu này xuất hiện lẻ tẻ (có lượt 0,00°, có lượt 254°),
tức phụ thuộc thứ tự vẽ chứ không phải chuyển động.

Ba lý do kết luận §3 vẫn đứng vững:

1. Kênh **sạch** `390×844` một mình đã tách đủ ba cấu hình: ‖trục‖ 1,000 /
   0,669–0,680 / 1,000.
2. Chỉ số quyết định là **hướng trung bình của trục**, lấy trung bình trên
   60–140 mẫu; vài khung nhiễu không kéo `[0,1,0]` thành `[0,38, −0,06, 0,47]`,
   và cũng không kéo ngược lại thành đúng `[0,0,1]` cho biến thể D.
3. Có lượt candidate ở 1440×900 với cửa sổ chứng **sạch** (1,02° / 54 khung) vẫn
   cho ‖trục‖ = 0,608.

Cùng lý do đó, **`buocNhay`** (bước nhảy góc > 12°) ≈ 1 lần/lượt ở 1440×900 và
**0** ở 390×844 — nhưng **giống hệt nhau ở cả ba cấu hình**, kể cả baseline. Nó
là cùng một hiện vật thứ tự vẽ, không phải một lần khớp khung xen giữa; và dù là
gì thì nó cũng không giải thích được hồi quy, vì nó có mặt cả trước lẫn sau.

**Chưa làm:** dải ảnh khung-theo-khung của cú kéo. Số đo trục đã đủ tính quyết
định nên wave dừng ở đây thay vì dựng lại worktree biến thể chỉ để chụp ảnh.

---

## 7. Trường báo cáo bắt buộc

```
PRODUCT_REGRESSION_REPRODUCED  = YES
REGRESSION_TYPE                = ROTATION_AXIS_INSTABILITY  ⚠️ không thuộc tập
                                 liệt kê trong đặc tả wave. Gần nhất là
                                 CAMERA_SNAP nhưng SAI: không có bước nhảy tức
                                 thời nào; trục quay trôi LIÊN TỤC mỗi khung.
                                 Đề nghị bổ sung nhãn này vào tập.
ROOT_CAUSE                     = ORBIT_CONTROLS_UP_FRAME_STALE
                                 OrbitControls chụp object.up một lần trong hàm
                                 dựng (OrbitControls.js:406, three 0.185.1);
                                 scene3d-view.tsx dựng controls ở :842 nhưng đặt
                                 cam.up ở :1022 → controls quay quanh Y, camera
                                 dựng khung theo Z.
PERFORMANCE_REGRESSION         = NO
INTERACTION_FEEL_REGRESSION    = YES

BASELINE_FRAME_TIME_P95        = 20,9 ms (1440×900) · 7,9 ms (390×844)
CANDIDATE_FRAME_TIME_P95       = 21,4 ms (1440×900) · 8,8 ms (390×844)
DROPPED_FRAMES_GT_33_3MS       = baseline 2 / candidate 2  (trên 60 lượt mỗi bên)
POINTER_TO_RENDER_LATENCY_P50  = 0,20–0,21 ms, không đổi

CAMERA_FIT_CALLS_DURING_DRAG   = 0  (suy ra: 0 cấp phát buffer/program khi kéo,
                                 và buocNhay giống hệt nhau ở cả ba cấu hình.
                                 Không đo trực tiếp được — hàm nằm trong closure
                                 của effect, không có bề mặt để móc.)
GUARD_ACTIVATIONS_DURING_DRAG  = 0  (guard chỉ gọi trong nhánh khớp khung)
CONTROLS_RECREATIONS           = NOT_MEASURED_DIRECTLY → suy ra 0: controls dựng
                                 cùng effect với renderer, mà canvasTao = 0 và
                                 glContext = 1 suốt cửa sổ kéo ⇒ effect không
                                 chạy lại.
SCENE_REBUILDS                 = 0  (capPhatBuffer = 0, capPhatProgram = 0)

ROTATE_SPEED_BEFORE / AFTER    = 1,0 / 1,0  (không khai ở bản nào ⇒ mặc định)
DAMPING_BEFORE / AFTER         = enableDamping true / true

MINIMAL_FIX_RECOMMENDATION     = dời `cam.up.set(0, 0, 1)` lên TRƯỚC
                                 `new OrbitControls(...)` trong scene3d-view.tsx.
                                 Đã đo (biến thể D): trục về [0,0,1] cố định,
                                 ‖trục‖ = 1,000, biên độ quay khớp baseline
                                 (245,8° / 248,7° và 336,3° / 336,2°).
                                 Kèm test khoá `_quat` ↔ `cam.up`.

PRODUCT_CODE_CHANGED           = NO
BACKEND_CHANGE                 = NO
MODEL_FACING_CHANGED           = NO
CACHE_VERSION_CHANGED          = NO
COMMITS                        = 0
NEXT_ACTION                    = SCENE3D_ORBIT_UP_FRAME_FIX   (chờ user chuẩn y)
```

---

## 8. Hiện vật

```
docs/evaluation/geometry/scene3d-interaction-smoothness/
  BASELINE_INTERACTION.json      30 lượt @ e6c2330  (p1,p6,p7 × 2 khung nhìn × 5 lặp)
  CANDIDATE_INTERACTION.json     30 lượt @ 56350f7
  truc/BASELINE_INTERACTION.json     4 lượt đo TRỤC @ e6c2330
  truc/CANDIDATE_INTERACTION.json    4 lượt đo TRỤC @ 56350f7
  bien-the/CANDIDATE_INTERACTION.json  4 lượt đo TRỤC, biến thể D @ 7f34286 + 1 dòng chưa commit
  bien-the/README.md             ⚠️ đọc trước: file trên mang nhãn "candidate" nhưng KHÔNG phải candidate
frontend/scripts/scene3d-interaction-probe.mjs    bộ đo (CHƯA COMMIT — xem §9)
```

## 9. Nợ để lại, cần user quyết

1. **`COMMITS = 0` xung đột với cổng đồng bộ chỉ mục.**
   `frontend/scripts/scene3d-interaction-probe.mjs` và các hiện vật đang **chưa
   commit**. `frontend/src/code-index-sync.test.ts` quét mọi `.mjs` trong
   `frontend/scripts/` nên **sẽ ĐỎ** cho tới khi `docs/CODE_INDEX.md` có mục mô
   tả bộ đo này. Wave cấm commit, nên nợ này để nguyên và khai ở đây thay vì tự
   xử. Chọn một: (a) commit riêng bộ đo + mục CODE_INDEX ngay; (b) gộp vào wave
   sửa lỗi kế tiếp.
2. **Chưa ghi ngược `STATUS_LEDGER` / `CURRENT_STATE`.** Cố ý: wave dừng trước
   bản vá nên chưa có dòng DONE nào để ghi, và ghi mà không commit chỉ làm cây
   bẩn khó đọc.
3. **Thư mục thừa `/d/tmp/algosim-baseline`** (3,5 MB) — xoá bị từ chối quyền,
   metadata git đã tỉa. Cần user xoá tay. Các worktree tạm đã gỡ sạch:
   `git worktree list` chỉ còn checkout chính, và
   `frontend/node_modules/.bin` còn nguyên 54 mục / `node_modules` 68 mục.
