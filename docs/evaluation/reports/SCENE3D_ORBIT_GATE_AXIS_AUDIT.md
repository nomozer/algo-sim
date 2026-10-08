# SCENE3D_ORBIT_GATE_AXIS_AUDIT (2026-09-12)

Kiểm toán cổng quay. **Sản phẩm giữ nguyên tại `1a553b8`** — wave này không
chạm một dòng mã sản phẩm nào, không chạm camera.

Lý do: sau khi phục hồi về trước mockup, cổng quay báo `TRUC_TROI` cả ba ca.
Câu hỏi là phán quyết ấy có đúng không.

## 1. Phán quyết SAI. Trục cố định tuyệt đối.

Kéo **ngang thuần 300 px** (dy = 0), khung nhìn 1440×900, DPR 1, công thức trục
chép từ `SCENE3D_INTERACTION_SMOOTHNESS_REGRESSION_DIAGNOSIS`: `R = Aᵀ·B` giữa
hai ma trận liên tiếp, rút trục từ phần phản đối xứng, chuẩn hoá **dấu**, trung
bình vectơ đơn vị.

| | `e6c2330` | `1a553b8` | `56350f7` (chứng âm) |
|---|---|---|---|
| **① trục có cố định không** | **‖1,000‖ — có** | **‖1,000‖ — có** | ‖0,600–0,610‖ — **không** |
| **② trục là gì** | `[0, 1, 0]` → **Y** | `[0, 1, 0]` → **Y** | `[0,57; −0,05; 0,82]` → chéo |
| \|cos với Y\| / \|cos với Z\| | 1,000 / 0,000 | 1,000 / 0,000 | 0,03–0,07 / 0,82–0,83 |
| **③ tổng góc quay** | 149,3–154,0° | 149,8–153,0° | 109,1–109,7° |
| **④ `camera.up` nguyên bản** | `[0, 1, 0]` | `[0, 1, 0]` | `[0, 0, 1]` |
| **⑤ screen-up từ `viewMatrix`** | `(0,40; 0,894; 0,20)` | `(0,40; 0,894; 0,19)` | `(−0,05; −0,05; 0,998)` |
| cửa sổ đứng yên | 0° | 0° | 0° |

`camera.up` **đo được, không đọc từ mã nguồn**: three.js dựng khung sao cho
vectơ screen-right luôn ⟂ `camera.up`, nên vectơ vuông góc với MỌI screen-right
thu được chính là `camera.up`. Lấy tích có hướng từng cặp right-vector tách
nhau đủ xa, chuẩn hoá dấu rồi trung bình — ‖trung bình‖ = 1,000 ở cả ba bản,
tức phép suy nhất quán.

`e6c2330` và `1a553b8` khớp nhau tới từng chữ số vì mã sản phẩm của chúng
**trùng byte**. Đó là cửa sổ chứng: nếu hai cột ấy lệch nhau thì lỗi nằm ở bộ
đo, không ở sản phẩm.

`56350f7` là **chứng âm**: commit đã được `SCENE3D_INTERACTION_SMOOTHNESS_
REGRESSION_DIAGNOSIS` đo độc lập ra ‖trục‖ 0,608–0,680. Bộ đo ở đây trả
0,600–0,610 trên cùng commit ⇒ nó **phân biệt được** trục cố định với trục trôi.
Không có chứng âm thì "‖trục‖ = 1" là một khẳng định không thể bác.

## 2. Vì sao cổng nói sai: hai đại lượng cùng tên "trục"

Hàm `chuanTruc` của cổng lấy `dPv / (dPv + dCuc)`, với phương vị và góc cực
định nghĩa **quanh trục Z**. Nó trả lời *"có quay quanh Z không"*, không phải
*"trục có cố định không"*. Quay quanh Z ⇒ góc cực đứng yên ⇒ tỉ lệ → 1. Quay
quanh Y ⇒ cả hai cùng chạy ⇒ tỉ lệ → ~0,5.

Đặt cạnh nhau trên **cùng một cú kéo**:

| bản dựng | ‖trục‖ đúng | `chuanTruc` cũ |
|---|---|---|
| `e6c2330` — trục cố định | **1,000** | 0,525–0,532 |
| `1a553b8` — trục cố định | **1,000** | 0,526–0,531 |
| `56350f7` — **trục trôi thật** | 0,600–0,610 | **0,546–0,548** |

Hàm cũ chấm bản trục **trôi** cao hơn hai bản trục **cố định**. Trong dải này
nó **nghịch chiều** với thứ nó khai là đang đo. Nó chỉ trông đúng suốt thời
gian qua vì sản phẩm khi ấy tình cờ quay quanh Z, nên mọi bản "tốt" đều rơi vào
~1,0.

Đây là lần thứ năm bộ đo của miền này nói dối, và là lần đầu nó nói dối theo
hướng **trông giống một lỗi sản phẩm có thật** — trục quay trôi đúng là con bọ
đã từng tồn tại, nên phán quyết sai đọc rất thuyết phục.

## 3. Đã sửa gì trong cổng

Chỉ công cụ đo. Không chạm sản phẩm.

- `chuanTruc` **gỡ**; thay bằng `trucQuay(tuThe) → { vec, chuan, soMau }` dùng
  `R = Aᵀ·B`. `TRUC_TROI` nay chỉ phát khi `chuan < 0,99`.
- `tenTruc(vec)` báo trục là **Y / Z / X / chéo** — **thông tin**, không phải
  phán quyết. Quay quanh Y không còn bị gọi là `TRUC_TROI`.
- `vongQuanhTruc` thay `thaoCuon(pv)`: vòng đo quanh **chính trục đã đo**. Cách
  cũ đọc 12° cho một cú kéo cả nghìn độ khi trục là Y.
- `tongGocKhung` cho cửa sổ đứng yên, thay phương vị quanh Z.
- Mốc đo ghi thêm **ma trận đầy đủ** (trước chỉ ghi phương vị/góc cực/cos).
- Cờ **`--dist`** để đo một bản dựng khác. Không có nó thì không đối chiếu được
  cùng một cổng qua nhiều mốc — và chính phép đối chiếu ấy đã lộ ra lỗi trên.

### Một chỗ tôi đoán sai giữa chừng, và phải sửa lại

Cửa sổ đứng yên của cổng đọc 1,6–2,9° ở p6/p7. Tôi ghi vào mã rằng đó là nhiễu
số học do phương vị quanh Z gần suy biến khi trục là Y. **Sai.** Phép thử: để
cảnh lắng thêm 2 giây rồi mới mở cửa sổ ⇒ thu được **0 khung**, vì renderer chỉ
vẽ khi có việc. Những khung ấy có thật — chúng là đuôi damping của
`OrbitControls` còn chạy nốt sau loạt bấm "Bước sau". Cổng nay đợi lắng trước
khi mở cửa sổ; số đọc về **0,0–0,3°** ở cả ba bản dựng.

## 4. Cổng nói gì sau khi sửa

```
e6c2330    THIEU_HUONG_NHIN   vòng=436–444°  trục=Y[0,1,0] ‖1,000‖  yên=0,0–0,3°
1a553b8    THIEU_HUONG_NHIN   vòng=432–442°  trục=Y[0,1,0] ‖1,000‖  yên=0,0–0,3°
56350f7    TRUC_TROI          vòng=50–65°    trục=chéo     ‖0,648–0,665‖
```

`TRUC_TROI` đã biến mất khỏi hai bản trục cố định, và vẫn phát đúng ở bản trôi
thật.

⚠️ **`THIEU_HUONG_NHIN` thì ĐÚNG, không được sửa đi.** `cos ∈ [−0,31; 0,00]`:
hướng nhìn không bao giờ tới gần ±1 theo trục Z. Toạ độ bài toán dùng **z làm
chiều cao**, nên với quỹ đạo quanh Y người học **không nhìn được khối từ trên
xuống hay từ dưới lên**. Đó là hệ quả thật của camera Y-up, không phải lỗi bộ
đo — và nó là một giới hạn của sản phẩm đang phục hồi, cần khai chứ không cần
vá.

```
PRODUCT_CHANGED        = NO (0 dòng mã sản phẩm, 0 dòng camera)
GATE_CHANGED           = scene3d-orbit-gate.mjs
AXIS_IS_FIXED          = e6c2330 ‖1,000‖ · 1a553b8 ‖1,000‖ · 56350f7 ‖0,600–0,610‖
AXIS_IDENTITY          = Y · Y · chéo
TOTAL_ROTATION_300PX   = 149,3–154,0° · 149,8–153,0° · 109,1–109,7°
CAMERA_UP_MEASURED     = [0,1,0] · [0,1,0] · [0,0,1]
SCREEN_UP_FROM_VIEW    = (0,40; 0,894; 0,20) · (0,40; 0,894; 0,19) · (−0,05; −0,05; 0,998)
FALSE_VERDICT_REMOVED  = TRUC_TROI trên bản quay quanh Y
TRUE_VERDICT_KEPT      = THIEU_HUONG_NHIN (không nhìn được từ trên/dưới)
```

`NEXT_ACTION = USER_REVIEWS_ORBIT_GATE_AUDIT`
