# SCENE3D_VISUAL_LANGUAGE_IMPLEMENTATION

> Triển khai ngôn ngữ hình học đã được user duyệt ở vòng mockup tĩnh
> (`USER_APPROVAL = APPROVED`, `APPROVAL_SCOPE = SCENE3D_VISUAL_LANGUAGE_AND_CAMERA_ONLY`,
> 2026-09-11). Chỉ chạm `frontend/src/simulations/domains/geometry/` và
> `frontend/src/styles/global.css`.
>
> ```
> APPLICATION_LLM_CALLS = 0     CANDIDATE  96a9368b… — KHÔNG đổi
> REAL_PROVIDER_CALLS   = 0     CACHE_VERSION 95 — KHÔNG bump
> BACKEND_CHANGED       = NO    MODEL_FACING_CHANGED = NO
> ```

## 1. Vì sao candidate không đổi

`MEASURED_SYSTEM_PATHS` đúng ba mục: `backend/app` ·
`frontend/src/simulations/domains/semantic` · schema mirror của nó.
`domains/geometry/` **không** nằm trong đó, nên bản vá này không phá bản đóng
băng. Kiểm bằng máy: `freeze_evaluation_candidate.py --verify` exit 0 (92 file,
`96a9368b…`) và `lock_cache_identity.py --verify` exit 0 @ v95 — chạy SAU khi
sửa.

`CACHE_VERSION` **không bump**: cache analyze khoá theo *text đã chuẩn hoá +
`CACHE_VERSION`*, và bản vá này không chạm prompt, thẻ văn phạm, lược đồ hay
policy định tuyến. Không có đường nào để một envelope cũ trở nên sai.

## 2. Ba thay đổi, mỗi cái gắn một lỗi ĐO ĐƯỢC

### 2.1. Camera — `scene3d-camera.ts` viết lại

| | trước | sau |
|---|---|---|
| fit theo | **cầu ngoại tiếp** hộp bao | **hình chiếu** của tám đỉnh hộp bao |
| `up` | `(0,1,0)` của three.js | **`(0,0,1)` — trục z của hình học** |
| hướng nhìn | hằng số `[6,5,8]` trong hệ three.js | phương vị `−55°`, độ cao `22°` trong hệ của hình |
| đo trên P1–P7 | **0/7 đạt** · occupancy 0,29–0,47 | **7/7 đạt** · occupancy 0,66–0,685 |

Hai lỗi tách rời, và lỗi thứ hai mới là lỗi nặng:

**① Cầu ngoại tiếp lớn hơn hình.** Cầu lấp 68 % khung ⇒ hình thật lấp
`0,68/√3 ≈ 39 %` chiều. Đây là lỗi đã biết từ vòng prototype.

**② `up` sai hệ — lỗi này KHÔNG có trong chẩn đoán ban đầu.** Toạ độ bài toán
dùng **z** làm chiều cao (`S(0;0;6)`, trụ `O→K` theo z) và `toVec3` là ánh xạ
đồng nhất, nhưng camera dùng `up = (0,1,0)`. Hệ quả: **mọi khối nằm nghiêng**.
Khối chóp `p1` đọc ra một tứ giác dẹt — và suốt vòng trước nó bị quy cho màu
sắc. Occupancy chỉ là hệ quả đi kèm; đây mới là thứ làm hình không đọc được.

### 2.2. Bảng màu — mỗi màu MỘT vai

Bản trước gán màu theo **nguồn gốc** vật: điểm tự do xanh `#2563eb`, điểm dẫn
xuất đỏ `#dc2626`. Phân biệt ấy đúng về kỹ thuật và vô nghĩa với người học —
nó tiêu hai màu mạnh nhất cho một câu hỏi không ai đặt. Nay gán theo **vai
trong hình**:

| vai | màu | ghi chú |
|---|---|---|
| cạnh thấy + điểm | `#1F1F1F` | một màu điểm duy nhất |
| cạnh khuất | `#7D7975` | **một vai riêng**, không phải bản mờ của cạnh thấy |
| thiết diện | `#D95A43` | tiêu điểm |
| đường dựng, trục khối | `#99948F` | vai phụ |
| mặt phẳng cắt | `#77736F` | vai phụ |
| vật đang chọn | `#0075DE` | |

Độ đục: mặt khối `0,22 → 0,07` · mặt phẳng `0,20 → 0,07` · mặt cong
`0,30 → 0,07`.

⚠️ `MAU.line` và `MAU.section` **từng là một**: đường tròn và elip thiết diện
dùng chung màu với đường thẳng dựng. Đó là lý do thiết diện của `p3`/`p6` đọc
ngang hàng với một đường phụ.

### 2.3. Thiết diện đa giác đi HAI LƯỢT

`o.type === "section"` trước đây vẽ bằng **một** `THREE.Line` liền, nên cạnh
sau của thiết diện `p1` hiện y hệt cạnh trước — hình mất đúng câu trả lời *"đoạn
này nằm trước hay sau khối"*. Nay đi qua `duongHaiLuot` như mọi đường nằm trên
khối. Đa giác **không** phải thiết diện (đáy, mặt được nêu tên) giữ vai phụ.

### 2.4. Nhãn — ký hiệu hình học, không phải chip giao diện

CSS `.geo3d-label`: bỏ ô nền bo góc, chữ `0,9375rem`/600 màu `--ink`, tách khỏi
nét hình bằng `-webkit-text-stroke` + `paint-order: stroke fill`. Vật đang chọn
đổi **màu + độ đậm** (vẫn hai kênh theo luật 3.5 của `DESIGN_BRIEF`), không
quay lại ô nền.

## 3. GUARD thiết diện bẹp — và lỗi nó tự lộ ra

Guard: khi hướng nhìn nằm gần trong mặt cắt, thiết diện chiếu ra một **đoạn
thẳng** và bài *"tính diện tích thiết diện"* mất chính cái hình nó đang hỏi.
Lúc ấy xoay phương vị về `55°` so với pháp tuyến.

**Bản đầu của guard SAI, và ca tổng hợp bắt được.** Nó so **hiệu phương vị**
với `90°`. Nhưng "nhìn nghiêng cạnh" là quan hệ **ba chiều**: với pháp tuyến
`(−0,705; 0; 1)` nhìn từ `−55°/22°`, thiết diện chiếu ra tỉ lệ trục **0** —
bẹp tuyệt đối — trong khi hiệu phương vị là **125°**, cách `90°` tới 35°, nên
guard đã **không nổ**. Hiệu phương vị chỉ đúng khi cả hướng nhìn lẫn pháp tuyến
đều nằm ngang.

Sửa: `matCatBet` so `|d̂·n̂| < 0,15` — tỉ lệ trục của hình chiếu xấp xỉ chính
`|d̂·n̂|`, nên ngưỡng đọc thẳng ra từ ngưỡng "bẹp" `0,12` dùng khi đo mockup.

```
GUARD_STATUS = VALIDATED_ON_SYNTHETIC_CASE
  ca tổng hợp: trụ r=5 h=24, pháp tuyến mặt cắt ⟂ hướng nhìn mặc định
  tỉ lệ trục thiết diện, góc mặc định −55°  : 0
  tỉ lệ trục thiết diện, guard az 125°      : 0,514
  GUARD_KICH_HOAT = YES · GUARD_CAI_THIEN = YES
  trên bảy ca THẬT P1–P7: guard KHÔNG nổ lần nào (đúng như dự kiến)
```

## 4. Test — nền đỏ và phép tiêm

`scene3d-visual-language.test.tsx`, **12 test**, tất cả mới.

⚠️ **Toàn bộ bản vá này chạy qua suite cũ mà không một test nào đỏ.** Nghĩa là
trước đó không có gì canh ngôn ngữ thị giác: đổi màu, đổi trục lên, đổi cách
fit đều lọt. Đó là lý do tệp test tồn tại.

**Sáu phép tiêm, 6/6 bị bắt:**

| # | tiêm | test đỏ |
|---|---|---|
| ① | `up` quay về `(0,1,0)` | ✓ |
| ② | fit quay về cầu ngoại tiếp | ✓ |
| ③ | cạnh khuất dùng lại màu cạnh thấy | ✓ |
| ④ | điểm đổi màu theo nguồn gốc vật | ✓ |
| ⑤ | thiết diện quay về một lượt liền | ✓ |
| ⑥ | mặt khối đặc trở lại | ✓ |

Phép kiểm occupancy đo bằng **camera three.js thật** (`PerspectiveCamera` +
`project`), không dùng lại phép chiếu của chính module đang kiểm.

## 5. Cổng đã chạy

```
vitest            829 pass / 56 file   (trước bản vá: 828 / 56)
npm run build     PASS (tsc -b + vite)
tiêm lỗi          6/6 bị bắt
guard tổng hợp    KICH_HOAT YES · CAI_THIEN YES (0 → 0,514)
freeze --verify   exit 0 · 92 file · 96a9368b…
lock_cache        exit 0 @ v95
```

⚠️ **`tsc -b` bắt một lỗi mà `vitest` bỏ qua** (kiểu `number[]` vs
`[number,number,number]` trong test mới). Vitest không typecheck — build mới là
cổng kiểu duy nhất, và nó đã làm đúng việc.

## 6. ⚠️ BẰNG CHỨNG TRÌNH DUYỆT — CHƯA LẬP ĐƯỢC

```
BROWSER_EVIDENCE = NOT_ESTABLISHED
```

`spot-check-demo.mjs` chạy trong phiên này cho **4/12**, nhưng chạy lại **trên
mã CHƯA sửa** (git stash) cũng chỉ **6/12** với đúng một kiểu hỏng
(`xuong=false canvas=0`). Nền tài liệu là **12/12**. Không lập được nền thì
cổng ấy không chứng minh được gì — không cho bản vá, cũng không chống lại nó.

Nguyên nhân **không** phải WebGL: probe riêng cho `WEBGL=OK · ANGLE (SwiftShader
Device (Subzero)), SwiftShader driver`. Nguyên nhân thật chưa định vị.

⚠️ Nghĩa là **chưa có một điểm ảnh nào của sản phẩm được nhìn** với bản vá này.
Guard đơn vị chứng minh các QUYẾT ĐỊNH (trục lên, cách fit, bảng màu, hai
lượt); nó không chứng minh hình lên màn hình đẹp. Việc còn lại:
`SCENE3D_VISUAL_LANGUAGE_BROWSER_ACCEPTANCE`.

Một artifact đã commit bị hai lượt chạy ghi đè và **đã trả về nguyên trạng**:
`docs/evaluation/geometry/DEMO_SPOT_CHECK.json` (bản 2026-09-02, `git checkout`).

## 7. Nợ mở, khai rõ

| nợ | nội dung |
|---|---|
| `EDGE_WIDTH_IN_PIXELS` | Token duyệt ghi cạnh thấy **2,8 px**, khuất **1,6 px**, thiết diện **3,5 px**. Renderer vẫn vẽ cạnh khối bằng `THREE.Line` — WebGL **bỏ qua `linewidth`**, nên mọi cạnh dày đúng **1 px**. Đạt bề dày thật cần thay bằng `LineSegments2`/`LineMaterial` (có sẵn trong three 0.185), và việc ấy chạm cơ chế hai lượt `depthFunc` đang được `scene3d-hidden-lines.test.tsx` khoá ⇒ **wave riêng**. Thiết diện thì đã là DẢI có bề dày theo tỉ lệ cảnh nên đúng vai. |
| `BROWSER_EVIDENCE` | §6 |
| nét khuất: đứt hay mảnh mờ | Ảnh tham chiếu của user vẽ nét khuất bằng **nét mảnh mờ LIỀN**; token đã chốt dùng **nét đứt 7/5**. Giữ token theo §2 của yêu cầu; ghi lại để vòng sau quyết. |

## 8. Ngoài phạm vi, theo đúng quyết định của user

`OCCLUSION_SCOPE`: Möller–Trumbore trong bộ mockup **chỉ** phục vụ dựng và đo
ảnh tĩnh. Cơ chế hidden-line động của renderer (hai lượt `depthFunc`) **không
đụng tới**. Thay lõi ấy cần một wave riêng tái hiện lỗi, đo tác động và chứng
minh bản vá.

```
NEXT_ACTION = SCENE3D_VISUAL_LANGUAGE_BROWSER_ACCEPTANCE
```
