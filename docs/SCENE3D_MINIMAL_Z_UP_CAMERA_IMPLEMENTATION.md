# SCENE3D_MINIMAL_Z_UP_CAMERA_IMPLEMENTATION (2026-09-12)

Bản vá camera Z-up **tối thiểu** trên sản phẩm đã phục hồi: **một dòng mã**.

```
START_HEAD = c6b6846      END_HEAD = (commit của wave này)
PRODUCT_FILES_CHANGED  = 1  — frontend/src/simulations/domains/geometry/scene3d-view.tsx
PRODUCT_DIFF_LINES     = +25 (1 dòng mã, 24 dòng chú thích)
CAMERA_UP_ASSIGNMENT   = cam.up.set(0, 0, 1)
CAMERA_UP_BEFORE_CONTROLS = YES — kiểm bằng AST của chính tệp sản phẩm
```

Đầu vào kiểm trước khi sửa: `HEAD = c6b6846`, cây sạch,
`git diff 1a553b8 HEAD -- domains/geometry styles` **rỗng**.

## 1. Thứ tự là toàn bộ vấn đề, không phải giá trị

`OrbitControls` chụp `camera.up` **ngay trong hàm dựng** để tạo quaternion đưa
trục ấy về Y nội bộ. Đặt `cam.up` sau khi tạo controls thì controls vẫn quay vị
trí quanh Y trong khi camera dựng khung theo Z — hợp của hai phép quay quanh
hai trục không trùng nhau là một phép quay có **trục đổi theo từng khung**. Đó
đúng là `56350f7`, và wave này giữ nó làm **chứng âm**.

## 2. Kiểm thử vòng đời — hai tầng

`scene3d-zup-lifecycle.test.tsx`, 9 test.

**Tầng hành vi.** Dựng camera + `OrbitControls` thật ở cả hai thứ tự rồi hỏi
bằng **API công khai**: đặt camera tại `target + (0,0,10)` và đọc
`getPolarAngle()`. Trục quỹ đạo là Z ⇒ camera ở đỉnh quỹ đạo ⇒ cực ≈ 0. Trục là
Y ⇒ camera ở xích đạo ⇒ cực ≈ π/2. Ba nền đỏ đi kèm: bỏ hẳn việc đặt `up` · đặt
`up` sau controls · đặt `(0,1,0)`.

**Tầng ràng buộc vào sản phẩm.** Đọc `scene3d-view.tsx` bằng **AST của
TypeScript**, không bằng `indexOf`: một phép so chuỗi sẽ xanh cả khi dòng ấy
nằm trong chú thích hoặc một nhánh chết. Kiểm: `.up.set` xuất hiện **đúng một
lần**, đối số đúng `0, 0, 1`, vị trí **trước** mọi `new OrbitControls`, và
controls chỉ được tạo **một lần**.

### Ba phép tiêm bắt buộc, đều đỏ

```
(1) bỏ hẳn dòng cam.up.set              → ĐỎ (2 test)
(2) chuyển xuống SAU new OrbitControls  → ĐỎ (1 test)
(3) đổi lại (0, 1, 0)                   → ĐỎ (1 test)
nền (không tiêm) và sau khi khôi phục   → XANH
```

## 3. Chuyển động — cùng trace, ba bản dựng

Kéo **ngang thuần 300 px**, 1440×900, DPR 1, ba lượt mỗi bản (p1, p6, p7),
công thức trục `R = Aᵀ·B` của `SCENE3D_ORBIT_GATE_AXIS_AUDIT`.

| | `1a553b8` | **bản vá** | `56350f7` (chứng âm) |
|---|---|---|---|
| trục | `[0,1,0]` **Y** | **`[0,0,1]` Z** | chéo `[0,59;−0,09;0,80]` |
| ‖trục‖ | 1,000 | **1,000** | 0,587–0,615 |
| tổng góc 300 px | 148,6–151,9° | **151,8–154,5°** | 108,9–109,8° |
| `camera.up` **đo được** | `[0,1,0]` | **`[0,0,1]`** | `[0,0,1]` |
| screen-up | `(0,40; 0,894; 0,19)` | **`(0,27–0,31; 0,65–0,66; 0,699)`** | `(−0,04;−0,05;0,998)` |
| bán kính camera | 20,1 / 48,8 / 36,4 | 20,9 / 48,8 / 35,0 | — |
| bán kính trôi | **0 %** | **0 %** | — |
| tâm quỹ đạo trôi | 1,3e-4 … 4,8e-4 | 7e-5 … 2,1e-3 | — |

Tổng góc lệch **+1,65 %** so với nền (ngưỡng ≤ 5 %) — độ nhạy giữ nguyên.

**Cổng quay**: bản vá **ĐẠT** (`trục=Z[0,0,1] ‖1,000‖`), nền
`THIEU_HUONG_NHIN`, chứng âm vẫn **`TRUC_TROI`** (‖0,638–0,657‖). Chứng âm còn
đỏ ⇒ cổng còn đáng tin.

### Nhịp khung và cấp phát (probe, 30 lượt × 2 lần chạy)

| | `1a553b8` | bản vá |
|---|---|---|
| p50 / p95 / p99 | 10,45 / 17,45 / 20,90 ms | **10,45 / 17,40 / 20,90 ms** |
| khung > 16,7 ms | 930 | **853** |
| khung > 33,3 ms | 5 / ~5848 | **5 / ~5839** |
| khung gần lặp (góc/khung < 0,05°) | 3/30 lượt | 4/30 lượt |
| bước nhảy | 14 | 14 |
| cấp phát buffer / program / canvas khi kéo | 0 / 0 / 0 | **0 / 0 / 0** |
| pointer → paint (trung vị / p95) | 0,20 / 0,60 ms | 0,20 / 0,60 ms |
| đuôi damping sau khi thả | 197,5° / 78 khung | 196,7° / 91,5 khung |

⚠️ **`FRAMES_OVER_33_3_MS = 0` là ngưỡng DUY NHẤT không đạt, và nó không đạt ở
CẢ HAI bản.** Cả nền lẫn bản vá đều cho **đúng 5** khung > 33,3 ms trên ~5840
khung, lặp lại ở hai lần chạy độc lập; chúng rơi vào cú kéo **đầu tiên sau khi
đổi sang khung 390×844**, tức khung khởi động biên dịch shader của SwiftShader.
Bản vá không tạo thêm khung dài nào — nó nhỉnh hơn nền ở mọi cột khác. Ngưỡng
`= 0` như viết không đạt được ngay cả với bản đối chứng **chưa bị đụng**, nên
thứ sai ở đây là ngưỡng chứ không phải bản vá. Khai ra thay vì lặng lẽ cho qua.

## 4. Nhìn được từ trên và từ dưới

```
TOP_VIEW_COS_Z_MAX    = +1,000   (ngưỡng ≥ 0,75)
BOTTOM_VIEW_COS_Z_MIN = −1,000   (ngưỡng ≤ −0,75)
THIEU_HUONG_NHIN      = NO       (sáu hướng đều chạm)
```

Nền `1a553b8`: `cos z ∈ [−0,35; +0,005]`, `trên = False`, `dưới = False`. Đó là
giới hạn thật đã khai ở wave kiểm toán, và nó **biến mất** sau bản vá.

Xác nhận bằng ảnh (`ZUP_P1_P7_NAM_TU_THE.png`): p4 và p5 nhìn từ trên/dưới ra
**hình tròn** — tức nhìn dọc trục khối; trụ và nón nay **đứng thẳng** thay vì
nằm ngang; kéo ngang không làm đỉnh S lộn xuống; không có bước nhảy camera
(`snap = 0`, `cấp phát = 0`).

## 5. Hồi quy P1–P7

70 ảnh: 7 ca × 5 tư thế (mặc định · sau xoay ngang · nhìn trên · nhìn dưới ·
sau reset) × {1440×900, 390×844 thật}. **0 ảnh rỗng**, 35/35 băm khác nhau ở
mỗi khổ (không tư thế nào bị đóng băng).

Chạm mép khung: chỉ ở **p1**, 1–2 điểm ảnh — ca duy nhất có **mặt phẳng vô
hạn**; p2–p7 đều 0. Hình hữu hạn **không** clipping.

⚠️ **Nút "Xem lại toàn hình" khôi phục đúng HƯỚNG Z-up**, nhưng ở `p1` cỡ hình
sau reset nhỏ hơn lúc mặc định. Đây **không** phải do bản vá: đo cùng phép trên
nền `1a553b8` cho **53,09 %**, bản vá **52,63 %** — gần y hệt. Đó là hành vi có
sẵn của phép khớp khung khi cảnh có mặt phẳng vô hạn, và §1 buộc giữ nguyên
phép khớp ấy, nên wave này không đụng tới.

```
GEOMETRY_MODIFIED = false   TOPOLOGY_CHANGED = false   COORDINATES_CHANGED = false
ANSWERS_CHANGED   = false   TRACE_CHANGED    = false
BACKEND_CHANGED   = NO (0 byte)   MODEL_FACING_CHANGED = NO
CACHE_VERSION 95 → 95       CANDIDATE_HASH 96a9368b… không đổi (92 file)
```

## 6. Giới hạn còn lại, khai đủ

- **Cổng quay có chỗ chập chờn.** Phép đếm "sáu hướng nhìn" phụ thuộc số khung
  bắt được trong cú xoay nhanh: `p6` cho `THIEU_HUONG_NHIN` ở **1 trong 4** lượt
  dù `cos` vẫn chạm ±1,00 và trục vẫn `Z ‖1,000‖` — thiếu ba hướng NGANG, không
  phải trên/dưới. Ba lượt còn lại ĐẠT. Chưa sửa trong wave này (ngoài phạm vi),
  nhưng đừng đọc một lượt đơn lẻ của cổng như phán quyết cuối.
- **Nhịp khung đo trong lúc QUAY VIDEO không dùng được làm kết luận**:
  `MediaRecorder` + `captureStream` tự nó làm chậm ứng dụng (p50 25,6 ms ở nền
  và 28,3 ms ở bản vá, so với 10,45 ms khi đo không quay). Số hợp lệ là số của
  probe. Ngay cả trong phiên quay, bản vá vẫn ít khung > 33,3 ms hơn (28 so với
  50).
- **`STEP_8_EQUALS_STEP_11` không sửa** trong wave này, đúng như yêu cầu.

```
TEST_RESULTS      vitest 826/826 · tsc ✓ · build ✓ · pytest 4823 pass
FAULT_INJECTIONS  3/3 đã chứng ĐỎ (bỏ dòng · đặt sau controls · đổi (0,1,0))
COMMITS_CREATED   1
WORKING_TREE      sạch
USER_VISUAL_APPROVAL = PENDING
NEXT_ACTION = PHOTO_PROBLEM_TO_SCENE_END_TO_END
```

## 7. Kết luận, tách riêng

- **Camera quay ổn định?** Có — ‖trục‖ = 1,000, bằng đúng nền.
- **Trục quay là Y hay Z?** **Z** `[0,0,1]`. Nền là Y `[0,1,0]`.
- **Xem được trên và dưới?** **Được** — `cos z` chạm ±1,000; nền chỉ tới −0,35.
- **Chuyển động có mượt?** Bằng hoặc nhỉnh hơn nền ở mọi cột đo được; 0 cấp
  phát khi kéo; khung > 33,3 ms bằng đúng nền (5/5).
- **Hình học và đáp số?** **Không đổi** — 0 byte ở `backend/` và
  `frontend/src/data/`, candidate và `CACHE_VERSION` giữ nguyên.
