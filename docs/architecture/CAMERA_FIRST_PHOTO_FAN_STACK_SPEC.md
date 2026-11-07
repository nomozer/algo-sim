# CAMERA_FIRST_PHOTO_FAN_STACK_SPEC — Đặc tả UX Camera-First & Photo Fan Stack

> **Phân loại tài liệu:** Đặc tả UX & hợp đồng tương tác giao diện đã đóng băng thiết kế (`camera-photo-fan-stack-v1`), làm chuẩn cho đợt triển khai Camera-First tiếp theo.  
> **Trạng thái triển khai sản phẩm hiện tại:** `CAMERA_IMPLEMENTATION_PENDING = YES` (mã sản phẩm trong `frontend/src/` và `backend/app/` chưa thay đổi ở bước đóng băng thiết kế này).  
> **Tài liệu liên kết:**
> - Hệ thống thiết kế gốc: [`../../DESIGN.md`](../../DESIGN.md) · [`../../frontend/src/styles/tokens.css`](../../frontend/src/styles/tokens.css)
> - Điểm tích hợp hiện hữu trên `main`: [`../../frontend/src/components/ProblemInput.tsx`](../../frontend/src/components/ProblemInput.tsx) · [`../../frontend/src/components/PhotoProblemDialog.tsx`](../../frontend/src/components/PhotoProblemDialog.tsx) · [`../../frontend/src/components/PhotoCameraView.tsx`](../../frontend/src/components/PhotoCameraView.tsx)
> - Prototype HTML tự chứa: [`../evaluation/geometry/runs/axo-camera-photo-fan-stack/prototype/axo_camera_first_ux_prototype.html`](../evaluation/geometry/runs/axo-camera-photo-fan-stack/prototype/axo_camera_first_ux_prototype.html)
> - Bàn giao kỹ thuật Frontend & Backend: [`../evaluation/geometry/runs/axo-camera-photo-fan-stack/FRONTEND_BACKEND_HANDOFF.md`](../evaluation/geometry/runs/axo-camera-photo-fan-stack/FRONTEND_BACKEND_HANDOFF.md)
> - Báo cáo kiểm toán Photo Fan Stack: [`../evaluation/geometry/runs/axo-camera-photo-fan-stack/report.md`](../evaluation/geometry/runs/axo-camera-photo-fan-stack/report.md)

---

## 1. Khóa Phạm Vi Thiết Kế & Ranh Giới Với Sản Phẩm Trên `main`

### 1.1. Phạm vi được chuẩn hóa bởi đặc tả này
Đặc tả này **chỉ** quy định trải nghiệm **Camera-First & quản lý ảnh chụp đề toán**:
- Màn hình chụp ảnh toàn màn hình trên thiết bị di động / máy tính bảng cảm ứng (**Mobile/Tablet Fullscreen Camera**).
- Hộp thoại chụp ảnh gọn trên máy tính (**Desktop Camera Dialog**).
- Khung xem trước mặc định **`Toàn khung`** (`contain`, bảo toàn `100%` khung cảm biến không cắt mất dữ kiện sát mép) và tùy chọn chuyển nhanh **`Tràn màn`** (`cover`).
- Luồng chụp liên tiếp nhiều ảnh trong một phiên không khóa thao tác.
- Thành phần **`Photo Fan Stack`** (thu gọn khi xếp chồng, xòe quạt mượt khi hover/focus trên Desktop, chạm `1` lần mở khay ảnh trên Mobile, loại bỏ các nhãn đếm số lượng lặp lại).
- Nút **`Xong`** cố định và sự phân tách rõ giữa **`Đóng`** và **`Xong`**.
- Màn xem ảnh độ phân giải gốc (**Viewer**: `Zoom 100%–300%`, kéo `Pan`, `Chụp lại` đúng vị trí, `Xóa ảnh` và `Hoàn tác` `1` chạm).
- `5` trạng thái lỗi camera thân thiện với học sinh kèm lối thoát chọn ảnh có sẵn.

### 1.2. Phạm vi nghiêm cấm thay đổi
Tuyệt đối **không** dùng HTML prototype làm mẫu thay thế cho các thành phần sản phẩm đang vận hành trên `main`:
- Header, Logo Axo (`IconAxoLogo`), Navigation (`TopNav`).
- Trang chủ, bố cục tổng thể của `ProblemInput.tsx` (Composer), các thẻ gợi ý bài mẫu.
- Thư viện hình mẫu, Lịch sử, Workspace, `Scene3D`, bảng điều khiển mô phỏng và các bước dựng hình sư phạm.

Phần Header và Composer xuất hiện trong tệp prototype HTML chỉ đóng vai trò **ngữ cảnh mô phỏng điểm kết nối** (seam minh họa việc mở camera và nhận ảnh đính kèm về lại Composer).

---

## 2. Máy Trạng Thái Camera & Luồng Chụp Nhiều Ảnh Liên Tiếp

### 2.1. Quy tắc luồng đơn nhất (Single Canonical Flow)
```
Composer hiện có trên main
  └─ Bấm "Chụp ảnh"
       ├─ [Nếu thiết bị / quyền lỗi] → Trạng thái lỗi gọn + nút "Chọn ảnh có sẵn" (+ "Thử lại" khi khả thi)
       └─ [Luồng video sẵn sàng] → Khung "Toàn khung" mặc định (0 ảnh mới)
             ├─ Bấm Shutter lần 1 → Chớp nhẹ ≤ 150ms, hiện 1 thumbnail đơn + nút "Xong"
             ├─ Bấm Shutter lần 2..N → Chụp liên tiếp tức thì, cập nhật Photo Fan Stack (không bật modal/toast chặn)
             ├─ (Tùy chọn) Mở ảnh từ quạt (Desktop) hoặc khay ảnh (Mobile) → Zoom/Pan, Chụp lại tại chỗ, Xóa, Hoàn tác
             └─ Bấm "Xong" → Đưa toàn bộ ảnh phiên chụp về dải đính kèm của Composer theo đúng thứ tự chụp
                             (KHÔNG tự động gọi AI / KHÔNG tự chạy "Dựng hình")
```

### 2.2. Các trạng thái theo số lượng ảnh trong phiên (`N = sessionCaptures.length`)

| Số ảnh `N` | Hiển thị nhóm ảnh | Nút hành động chốt | Hành vi khi bấm `Đóng` (`✕` / `Escape`) |
| :---: | :--- | :--- | :--- |
| **`N = 0`** | Ẩn hoàn toàn `Photo Fan Stack` | Ẩn nút `Xong` | Đóng camera ngay lập tức, không hỏi xác nhận, bảo toàn nguyên vẹn ảnh đã có trong Composer |
| **`N = 1`** | `1` thumbnail tờ đề thật, không nghiêng, **không xòe quạt** khi hover/focus (`data-fan-capable="false"`), không đè chữ số `1` | Hiện nút **`Xong`** cố định | Hiện thẻ xác nhận nội tuyến (`Giữ ảnh` / `Bỏ ảnh mới` / `Tiếp tục chụp`) |
| **`2 ≤ N ≤ 5`** | Xếp chồng vật lý `N` thumbnail thật; Desktop hover/focus xòe quạt `N` lá; Mobile chạm `1` lần mở khay `N` ảnh | Hiện nút **`Xong`** cố định | Hiện thẻ xác nhận nội tuyến; bảo toàn các ảnh đã đính kèm trước đó trong Composer |
| **`N > 5`** | Xếp chồng / xòe quạt tối đa **`5` ảnh gần nhất** (`indices N-5 .. N-1`) để tránh tràn khung; mỗi lá vẫn giữ đúng `sessionIndex` gốc | Hiện nút **`Xong`** cố định | Viewer (Desktop/Mobile) và Khay ảnh (Mobile) vẫn duyệt, phóng to, chụp lại, xóa đủ toàn bộ `1..N` ảnh (`indices 0 .. N-1`) |

### 2.3. Quy tắc chống lặp nhãn số lượng
Trên bề mặt camera đang chụp, **loại bỏ hoàn toàn** các chuỗi đếm lặp lại như `Đã chụp N ảnh`, chip `N ảnh`, `Khay ảnh`, hay `Xong (N)`:
- Trạng thái đã chụp được truyền đạt trực tiếp bằng hình ảnh thật của **`Photo Fan Stack`** + nút **`Xong`** cố định.
- Chỉ hiển thị nhãn trạng thái ngắn trên thanh đầu camera khi đang ở chế độ đặc biệt **`Đang chụp lại ảnh`** (`Thay thế ảnh #k — bấm Hủy để giữ ảnh cũ`).
- Số lượng và thứ tự ảnh vẫn được cung cấp đầy đủ qua thuộc tính tiếp cận (`aria-label`, `aria-live="polite"`) và tiêu đề bên trong Viewer / Khay xem ảnh (`Ảnh thứ k trong N ảnh`).

---

## 3. Đặc Tả Chi Tiết Thành Phần `Photo Fan Stack`

### 3.1. Bố cục không dịch chuyển (`0px` Layout Shift)
- Hộp chứa `.photo-fan-stack` trên Desktop giữ kích thước khung bố cục cố định (`56 × 42px`, `position: relative`, `flex-shrink: 0`) nằm bên trái nút `Xong`.
- Mọi thẻ ảnh `.fan-card-btn` (`44 × 44px`, bo góc `8px`, viền trắng `#ffffff` `1.5px`, bóng tách lớp mảnh) được định vị `position: absolute` bên trong hộp chứa và chỉ biến đổi qua `transform: translate3d(...) rotate(...) scale(...)`.
- Khi quạt mở hoặc thu gọn: kích thước Dialog, vị trí nút `Chụp ảnh`, nút `Xong` và nút `✕` dịch chuyển **`0px`**.

### 3.2. Tương tác mở quạt trên Desktop (`pointerType === 'mouse' | 'pen'` & Bàn phím)
- **Trạng thái xếp chồng (mặc định):** Các lá lệch nhẹ (`dx` từ `-9px` đến `+8px`, góc nghiêng `-10°` đến `+8°`, tỉ lệ `0.90 → 1.00` từ ảnh cũ hơn đến ảnh mới nhất nằm trên cùng).
- **Trạng thái mở quạt (`.is-fan-open`):**
  - Kích hoạt khi con trỏ chuột đi vào `.photo-fan-stack` (`pointerType !== 'touch'`) hoặc khi một nút bên trong nhận focus bàn phím (`focusin` / `:focus-within`).
  - Các lá xòe thành hình cung hướng lên phía trên thanh đáy (`fanY` từ `-46px` đến `-60px`, biên độ ngang tự co theo hệ số `--fan-spread-scale` khi cửa sổ hẹp hơn `576px`) với chuyển động `200ms cubic-bezier(0.22, 1, 0.36, 1)` (không nảy lò xo quá đà).
  - Lá đang được trỏ chuột hoặc `:focus-visible` nâng nhẹ thêm `-6px`, phóng `scale(1.11)`, đổi viền sang xanh học thuật Axo `#0075de` (`--color-accent-primary`) và nhận `z-index` cao nhất trong nhóm quạt.
- **Vùng đệm hover liên tục hình chữ T (Chống nhấp nháy / tự cụp quạt):**
  - Kết hợp lớp đệm chân `.fan-hover-bridge-base` và lớp đệm cung xòe `.fan-hover-bridge-arc` chồng khít nhau `6px` theo phương dọc + độ trễ thu quạt `95ms` khi `pointerleave`.
  - Việc đóng/mở quạt chỉ bật/tắt class `.is-fan-open` trên nút DOM hiện hữu, không dựng lại danh sách phần tử con khi di chuột, đảm bảo rê chuột chéo qua lại giữa cả `5` ảnh mượt tuyệt đối (`0` lần tự thu quạt sớm).
  - Các nút điều khiển quan trọng ở thanh đáy (`#btn-cam-shutter`, `#btn-cam-done`) giữ ưu tiên vùng nhấn độc lập (`z-index` cao hơn cầu đệm hover), không bao giờ bị quạt hoặc cầu đệm che khuất.
- **Chọn ảnh:** Nhấn chuột hoặc phím `Enter` / `Space` trực tiếp vào lá thứ `k` mở ngay **Viewer** đúng tại `sessionIndex` gốc của ảnh đó.

### 3.3. Tương tác cảm ứng trên Mobile & Tablet (`pointer: coarse`)
- Bỏ qua hoàn toàn hiệu ứng hover mở quạt trên cảm ứng (`pointerType === 'touch'`).
- Nhóm ảnh hiển thị dưới dạng một nút bấm xếp chồng gọn ở góc dưới bên trái (`.mobile-fan-stack-btn`, vùng chạm `58 × 48px`, `≥ 44 × 44px` ở màn hình thấp `≤ 600px`).
- **Chạm `1` lần duy nhất** mở thẳng **Khay xem ảnh phiên chụp** (`CameraMobileTray` dạng Master–Detail: khung xem ảnh đang chọn dùng `fullDataUrl`, hàng thumbnail chọn nhanh, và một thanh hành động chung duy nhất gồm `Chụp lại` + `Xóa ảnh` + nút `Phóng to` mở Viewer Zoom/Pan).

---

## 4. Phân Tách `Đóng` vs `Xong`, Chụp Lại, Xóa & Hoàn Tác

1. **Nút `Xong`:**
   - Nối toàn bộ `sessionCaptures` vào sau danh sách `composerAttachments` hiện có theo đúng thứ tự chụp (`[...existingAttachments, ...sessionCaptures]`), giữ nguyên văn bản học sinh đã gõ trong ô nhập, đóng camera và giải phóng luồng phần cứng.
2. **Nút `Đóng` (`✕`, nhấn nền ngoài Dialog, hoặc phím `Escape` ở cấp camera):**
   - Nếu `sessionCaptures.length === 0`: đóng ngay lập tức về Composer.
   - Nếu `sessionCaptures.length >= 1`: hiển thị thẻ xác nhận nội tuyến ngay trong khung camera (không mở chồng modal thứ hai) với 3 lựa chọn rõ nghĩa:
     - **`Giữ ảnh và đính kèm vào ô nhập`** (tương đương `Xong`).
     - **`Bỏ ảnh mới chụp`** (chỉ xóa `sessionCaptures` của phiên đang mở; **bảo toàn 100%** các ảnh đã đính kèm trước đó trong Composer).
     - **`Tiếp tục chụp`** (đóng thẻ hỏi, quay lại khung ngắm).
3. **Chụp lại đúng vị trí (`Retake-in-place`):**
   - Khởi phát từ Viewer hoặc Khay ảnh tại chỉ số `idx` → quay về khung ngắm với thanh trạng thái gọn `Đang chụp lại ảnh` (có nút `Hủy`).
   - Lần bấm Shutter kế tiếp ghi đè đúng phần tử tại `idx` mà không làm xáo trộn thứ tự các ảnh còn lại trong phiên hoặc trong Composer.
4. **Xóa & Hoàn tác `1` chạm (`Undo`):**
   - Xóa ảnh trong Viewer, Khay ảnh hoặc Composer thực thi tức thời không bật hộp thoại chặn luồng, đồng thời hiện thanh trạng thái gọn kèm nút **`Hoàn tác`** khôi phục đúng ảnh và đúng vị trí `oldIndex` vừa xóa.

---

## 5. Khung Ngắm Toàn Khung, Độ Phân Giải Ảnh Gốc & Viewer Zoom/Pan

- **Mặc định `Toàn khung` (`object-fit: contain`):** Hiển thị trọn vẹn `100%` khung hình nguồn (`4:3`, `16:9`, `3:4`) nằm giữa thanh trên và thanh dưới riêng biệt, đảm bảo công thức toán hoặc hình vẽ sát mép tờ giấy không bị giao diện cắt khuất. Học sinh có thể chuyển sang `Tràn màn` (`cover`) nếu muốn phóng đầy màn hình.
- **Tách bạch hiển thị preview và dữ liệu ảnh chụp:** Mọi lần bấm Shutter đều trích xuất `100%` khung cảm biến gốc (`videoWidth × videoHeight`), hoàn toàn độc lập với chế độ CSS `contain` hay `cover`.
- **Hai tầng dữ liệu ảnh:**
  - `thumbUrl` (ảnh thu nhỏ nhẹ `~320px`): chỉ dùng cho `Photo Fan Stack`, hàng chọn nhanh trong Khay ảnh và dải đính kèm nhỏ ở Composer.
  - Nguồn ảnh độ phân giải gốc (`fullDataUrl` / `Blob` gốc): bắt buộc dùng trong **Viewer** (`Zoom 100% → 175% → 250% → 300%`, kéo chuột/ngón tay hoặc phím mũi tên để `Pan` kiểm tra chỉ số dưới, căn thức, ký hiệu góc và nét đứt hình không gian) và dùng để gửi lên Backend khi bấm `Dựng hình`.

---

## 6. Năm Trạng Thái Lỗi Camera Chuẩn Hóa

Khi không mở được luồng camera, **không hiển thị khung video đen rỗng** và **không lộ tên mã lỗi kỹ thuật** (`NotAllowedError`, `NotFoundError`, `NotReadableError`, stack trace) cho học sinh:

| Mã nội bộ | Thông điệp hiển thị cho học sinh | Hành động khả dụng |
| :--- | :--- | :--- |
| `permission_denied` | **Không mở được máy ảnh.** Trình duyệt đang chặn quyền máy ảnh cho trang này. Em có thể cho phép lại trên thanh địa chỉ hoặc chọn ảnh có sẵn. | `Thử lại` · **`Chọn ảnh có sẵn`** |
| `not_found` | **Không tìm thấy máy ảnh.** Thiết bị hiện không có máy ảnh khả dụng. Em hãy chọn ảnh đề bài có sẵn trong máy. | `Thử lại` · **`Chọn ảnh có sẵn`** |
| `temporarily_unavailable` | **Máy ảnh tạm thời không khả dụng.** Chưa nhận được tín hiệu hình ảnh lúc này. Em có thể thử lại hoặc chọn ảnh có sẵn. | `Thử lại` · **`Chọn ảnh có sẵn`** |
| `unsupported` | **Trình duyệt không hỗ trợ chụp trực tiếp.** Em vẫn có thể chọn ảnh đề bài có sẵn từ thiết bị để tiếp tục. | **`Chọn ảnh có sẵn`** |
| `unknown` | **Không mở được máy ảnh.** Em có thể thử lại hoặc chọn ảnh có sẵn. | `Thử lại` · **`Chọn ảnh có sẵn`** |

---

## 7. Đáp Ứng Đa Thiết Bị & Khả Năng Tiếp Cận (WCAG 2.2 AA)

- **Mobile & Tablet cảm ứng:** Fullscreen thật (`100dvh` + `env(safe-area-inset-*)`), nút Shutter tròn đặt chính tâm ngang tuyệt đối (`1fr auto 1fr`), tự thu gọn khoảng đệm hợp lý trên màn hình thấp (`390×560`, `390×500`) mà vẫn giữ mọi mục tiêu cảm ứng chính `≥ 44 × 44px` và `0` tràn dọc/ngang.
- **Desktop & Chrome Zoom `110%`:** Dialog gọn (`min(92vw, 576px)`, `max-height: calc(100dvh - 32px)`), khung video co giãn theo tỷ lệ nguồn thật, mở quạt 5 ảnh không cắt mép và không tràn khung ở cả `100%` lẫn Chrome Zoom `110%` (`DPR = 1.1`).
- **Điều hướng bàn phím & Quản lý Focus:**
  - Bẫy focus (`Focus Trap`) trong lớp đang mở trên cùng (`Viewer` → `Xác nhận Đóng` → `Khay ảnh Mobile` → `Camera Dialog`).
  - `Tab` đi vào `.photo-fan-stack` tự mở quạt; `ArrowLeft / ArrowRight` chuyển qua lại giữa các thẻ trong quạt (hoặc chuyển ảnh trước/sau khi ở mức `100%` trong Viewer; khi `Zoom > 100%` các phím mũi tên hỗ trợ `Pan` ảnh theo WCAG 2.5.7).
  - Phím `Escape` đóng theo đúng thứ tự phân tầng: `Viewer` → `Thẻ xác nhận Đóng` → `Khay ảnh Mobile` → `Thu gọn quạt đang mở` → `Yêu cầu Đóng Camera`, và luôn trả focus về đúng phần tử kích hoạt (kể cả khi đóng Viewer từ ảnh thứ `1` trong phiên có `> 5` ảnh).
- **Giảm chuyển động (`prefers-reduced-motion: reduce`):** Tắt toàn bộ hoạt ảnh bay/xoay (`transition-duration ≤ 0.01ms`, bỏ góc nghiêng khi xòe), giữ nguyên khả năng mở danh sách thẻ tức thì và chọn xem mọi ảnh.
