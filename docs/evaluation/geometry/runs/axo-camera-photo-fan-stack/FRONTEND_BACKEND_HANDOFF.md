# FRONTEND & BACKEND HANDOFF — Camera-First & Photo Fan Stack

> **Phiên bản hồ sơ thiết kế:** `camera-photo-fan-stack-v1`  
> **Baseline mã sản phẩm đối chiếu:** `main` @ `bb4d6b55346bc35e42bf19796b9c1f2310b9c8c0`  
> **Đặc tả UX chuẩn:** [`../../../../architecture/CAMERA_FIRST_PHOTO_FAN_STACK_SPEC.md`](../../../../architecture/CAMERA_FIRST_PHOTO_FAN_STACK_SPEC.md)  
> **Prototype tham chiếu:** [`./prototype/axo_camera_first_ux_prototype.html`](./prototype/axo_camera_first_ux_prototype.html)  
> **Báo cáo kiểm toán:** [`./report.md`](./report.md)

> [!IMPORTANT]
> **Nguyên tắc bàn giao bắt buộc:**
> 1. Hồ sơ này phục vụ hai đợt triển khai độc lập (**Frontend** và **Backend**) sẽ mở sau khi thiết kế được phê duyệt và tích hợp lên `main`.
> 2. **Không thiết kế lại hay viết thay thế** Header, Logo Axo, Navigation, Trang chủ, `ProblemInput.tsx` tổng thể, Thư viện, Workspace hoặc `Scene3D` đang có trên `main`.
> 3. Mọi trường hợp đồng mở rộng cho đa ảnh ở Mục 2 là **đặc tả đề xuất cần thống nhất khi triển khai**, không phải API đã có sẵn trên `main`.

---

## 1. Frontend Handoff (Tích Hợp Gọn Vào `ProblemInput` Hiện Hữu)

### 1.1. Hiện trạng trên `main` cần kế thừa trực tiếp
Qua đối chiếu mã thực tế trên `main`:
- [`ProblemInput.tsx`](../../../../../frontend/src/components/ProblemInput.tsx) **đã có sẵn**:
  - State `attachments: ComposerAttachmentItem[]`, hàm `addFilesToComposer(files)` và dải hiển thị tệp đính kèm `#composer-files-row`.
  - Menu dấu cộng `#btn-composer-plus` với `#menu-item-upload-file` và `#menu-item-camera` mở `PhotoProblemDialog`.
  - Luồng hỗ trợ chuẩn bị đề bài `PhotoProblemPanel` (`unifiedAssistReducer`) cho `1` tệp đính kèm.
  - Chốt chặn tạm thời ở dòng `849–859` (`readyAttachments.length > 1` hiện thông báo *"Mỗi lượt dựng hình xử lý 1 tệp đề bài"* vì Backend `POST /api/input/prepare` hiện mới nhận `1` tệp).
- [`PhotoCameraView.tsx`](../../../../../frontend/src/components/PhotoCameraView.tsx) & [`PhotoProblemDialog.tsx`](../../../../../frontend/src/components/PhotoProblemDialog.tsx) **đã có sẵn**:
  - Các hàm nền tảng `cameraSupport()`, `cameraErrorMessage()`, `detectMobileCameraPreferred()`, `buildCameraConstraints()`, `canSwitchCamera()` và trích khung `video.videoWidth × video.videoHeight` ra `image/jpeg`.
  - **Điểm hạn chế hiện tại:** Bấm chụp `1` ảnh là dừng `MediaStream` và đóng hộp thoại ngay lập tức (`onCapture(file)`), chưa có phiên chụp nhiều ảnh, chưa có `PhotoFanStack`, chưa có `Toàn khung` / `Tràn màn`, chưa có xác nhận `Đóng` nội tuyến và chưa có Viewer `Zoom & Pan` / `Chụp lại` đúng vị trí / `Hoàn tác`.

### 1.2. Kiến trúc Component dự kiến (Không thay thế `ProblemInput.tsx`)
Giữ nguyên bố cục, giao diện và vòng đời ô nhập của `ProblemInput.tsx`; chỉ nâng cấp module camera qua chữ ký callback mảng tệp `onCommitCaptures(files: File[])`:

| Thành phần dự kiến | Vai trò & điểm nối vào mã hiện hữu |
| :--- | :--- |
| `PhotoProblemDialog.tsx` *(nâng cấp tại chỗ)* | Điều phối bề mặt hiển thị: Fullscreen `100dvh` trên thiết bị di động/tablet cảm ứng (`detectMobileCameraPreferred()` hoặc màn hẹp/thấp) và Dialog gọn `min(92vw, 576px)` trên Desktop; nhận `onCommitCaptures(files: File[]) => addFilesToComposer(files)`. |
| `useCameraSession.ts` *(mới)* | Quản lý state phiên chụp (`sessionCaptures`, `previewFitMode = "contain" | "cover"`, `retakeTargetIndex`, `lastDeletedPhoto`, `closeConfirmOpen`), tạo cặp `{ file, fullObjectUrl, thumbObjectUrl }` và thu hồi bộ nhớ tất định. |
| `PhotoCameraView.tsx` *(nâng cấp tại chỗ)* | Giữ luồng `MediaStream` sống xuyên suốt nhiều lần bấm Shutter liên tiếp (`0` modal chặn sau mỗi lần chụp), hỗ trợ `Toàn khung` mặc định + chuyển `Tràn màn`, chớp màn trập ngắn `≤ 150ms` và hiển thị `5` trạng thái lỗi sạch gọn không khung video đen. |
| `PhotoFanStack.tsx` *(mới)* | Hiển thị `1` thumbnail đơn (`N = 1`, không xòe) hoặc xếp chồng / xòe quạt tối đa `5` lá gần nhất (`N ≥ 2`) trên Desktop với cầu đệm hover hình chữ T + `:focus-within` + điều hướng `ArrowLeft/Right` + `prefers-reduced-motion`; trên Mobile render nút stack `1` chạm mở khay. |
| `CameraMobileTray.tsx` *(mới)* | Khay xem ảnh Master–Detail trên Mobile/Tablet (`Ảnh thứ k trong N ảnh`, thanh hành động chung `Chụp lại` + `Xóa ảnh` + `Hoàn tác` + mở phóng to gốc). |
| `AttachmentViewerModal.tsx` *(mới / mở rộng `#composer-single-file-modal`)* | Trình xem ảnh gốc dùng chung cho cả phiên chụp Camera (`scope = "session"`) và dải đính kèm Composer (`scope = "composer"`): `Zoom 100%–300%`, kéo `Pan` (chuột/cảm ứng/bàn phím), `Chụp lại` đúng vị trí, `Xóa` & `Hoàn tác`, đổi thứ tự ảnh ở Composer. |

Khi Backend hoàn tất mở rộng đa ảnh cho `POST /api/input/prepare`, chỉ cần gỡ chốt chặn `readyAttachments.length > 1` trong `ProblemInput.tsx` để truyền mảng `readyAttachments` theo đúng thứ tự mà không phải viết lại giao diện Composer.

### 1.3. Danh mục Kiểm Thử Phần Cứng & Trình Duyệt Thật Bắt Buộc (Real-Device Gate)
Vì prototype hiện tại kiểm chứng UX bằng nguồn `<canvas>` giả lập (`REAL_CAMERA_DEVICE_VERIFIED = NO`), phiên triển khai Frontend **bắt buộc** đo kiểm và nghiệm thu trên thiết bị thật các hạng mục sau:
1. **`navigator.mediaDevices.getUserMedia`:** Luồng cấp quyền lần đầu, từ chối quyền (`NotAllowedError`), thu hồi quyền giữa chừng, không có webcam (`NotFoundError`), camera đang bận bởi ứng dụng khác (`NotReadableError`) và ngữ cảnh không an toàn / trình duyệt không hỗ trợ.
2. **iOS Safari & Android Chrome thực tế:** Thanh địa chỉ co giãn động (`100dvh`), vùng tai thỏ / thanh gạt đáy (`safe-area-inset-*`), thuộc tính `playsInline` + `muted` chống tự nhảy fullscreen trình phát video hệ thống của iOS, và xoay ngang/dọc thiết bị.
3. **Đổi camera trước / sau (`facingMode` & `deviceId`):** Chuyển đổi giữa ống kính `environment` và `user` mượt mà, dừng track cũ trước khi mở track mới, tự ẩn nút đổi camera trên máy chỉ có `1` ống kính.
4. **Tỷ lệ khung nguồn thực tế (`4:3`, `16:9`, `3:4` dọc):** Đối chiếu khung preview `Toàn khung` với ảnh chụp thực tế để xác nhận `0%` chữ/hình sát mép bị cắt mất.
5. **Độ phân giải ảnh chụp thực tế:** Trích xuất từ `video.videoWidth × video.videoHeight` (hoặc `ImageCapture` nếu khả dụng ổn định) đạt độ nét đọc rõ chỉ số dưới / căn thức nhỏ khi `Zoom 250%–300%`, đồng thời nén hợp lý và tách riêng `thumbObjectUrl` `~320px` để không đưa ảnh `12MP` trực tiếp vào `5` thẻ của `PhotoFanStack`.
6. **Dọn dẹp `MediaStream` (`MediaStreamTrack.stop()`):** Xác minh đèn báo phần cứng camera trên trình duyệt/hệ điều hành tắt ngay lập tức khi bấm `Xong`, `Đóng`, `Escape`, chuyển trang hoặc unmount component.
7. **Dọn dẹp `ObjectURL` (`URL.revokeObjectURL`):** Thu hồi toàn bộ `fullObjectUrl` và `thumbObjectUrl` của ảnh bị xóa (sau khi hết hiệu lực hoàn tác hoặc đóng phiên), ảnh bị ghi đè khi `Chụp lại`, phiên bị chọn `Bỏ ảnh mới`, và khi rời Composer.
8. **Hồ sơ bộ nhớ khi chụp liên tiếp (`Memory Profile`):** Chụp liên tiếp `5–10` ảnh độ phân giải cao + mở quạt + mở Viewer Zoom/Pan trên điện thoại tầm trung mà không rò rỉ bộ nhớ, không giật khung hình và không làm sập tab trình duyệt.

---

## 2. Backend Handoff (Đề Xuất Mở Rộng Hợp Đồng Chuẩn Bị Đề Đa Ảnh)

### 2.1. Đối chiếu trực tiếp với API hiện có trên `main`

| Khía cạnh | Hiện trạng đã triển khai trên `main` (`bb4d6b553`) | Đặc tả đề xuất cần thống nhất cho đợt triển khai đa ảnh |
| :--- | :--- | :--- |
| **Endpoint chuẩn bị đề** | `POST /api/input/prepare` ([`backend/app/main.py`](../../../../../backend/app/main.py), [`unified_input.py`](../../../../../backend/app/ingestion/unified_input.py)), schema `"unified-input-prepare/1"` | Giữ tương thích ngược cho payload `1` tệp hiện hữu; bổ sung hỗ trợ mảng có thứ tự `attachments[]` trong phiên bản hợp đồng kế tiếp |
| **Đầu vào tệp hiện tại** | Đơn tệp: `content` (base64), `mime_type`, `filename`, `user_text`, `selected_candidate_id` (`MAX_ATTACHMENT_BYTES = 10 MB`) | Danh sách có thứ tự `attachments[]` gồm `attachment_id`, `order_index`, `source_type`, `content`/`mime_type` + `user_text` + `request_id` |
| **Tự phát hiện vùng đề** | Đã có [`region_detector.py`](../../../../../backend/app/ingestion/region_detector.py) (`detect_problem_regions`) kèm cơ chế fallback toàn ảnh cho `1` ảnh | Mở rộng áp dụng trên từng phần tử của `attachments[]` với quy tắc **fail-safe giữ nguyên ảnh gốc** khi độ tin cậy tách vùng thấp hoặc sát mép chữ |
| **Chọn bài khi có nhiều câu** | Đã có `status = "needs_selection"` + `candidates: UnifiedCandidateItem[]` (`candidate_id`, `label`, `text`, `Complete/Incomplete`, `bbox`) trên `1` tệp | Bổ sung ánh xạ `source_attachment_ids[]` trên từng ứng viên bài toán để biết câu đề được ghép từ ảnh nào hay nằm riêng ở ảnh nào |
| **Tuyến giải & dựng hình** | `POST /api/analyze` chạy tuyến chính thức **`Hybrid /4`** (`TypedFactNext /2 → Source Gate → Planner /26 → Registry /33 → Exact Kernel /24 → Adapter /4`) kèm `Idempotency-Key` & `AnalysisUsageLedger` | **Giữ nguyên 100%** kiến trúc `Hybrid /4` và mọi cổng fail-closed; bước đa ảnh chỉ chuẩn hóa văn bản đề đầu vào có kiểm chứng trước khi vào `Hybrid /4` |

### 2.2. Các trường hợp đồng đề xuất cần thống nhất (`PROPOSED — CHƯA TRIỂN KHAI`)
1. **`attachment_id` (`string`):** Định danh ổn định do client sinh cho từng ảnh trong Composer (ví dụ UUID/nanoid ngắn) để đồng bộ trạng thái trích xuất, chụp lại hoặc xóa từng ảnh.
2. **`order_index` (`int`, `0 .. N-1`):** Thứ tự tường minh của ảnh trong dải đính kèm Composer (mặc định theo thứ tự chụp trong phiên, cập nhật khi học sinh đổi vị trí `Lên trước / Ra sau` trong Viewer).
3. **`source_type` (`"camera_photo" | "uploaded_image" | "pdf_document"`):** Phân biệt ảnh chụp trực tiếp từ camera (thường có nền bàn học, bóng tay, nghiêng nhẹ) với ảnh chụp màn hình / tệp tải lên hoặc tài liệu PDF.
4. **`request_id` (`string`):** Mã yêu cầu chuẩn bị đề ở lượt bấm `Dựng hình` hiện hành, kết hợp `Idempotency-Key` và `AbortController` để loại bỏ phản hồi cũ (stale response) nếu học sinh sửa ảnh, chụp lại hoặc xóa ảnh rồi gửi lại.
5. **`problem_candidate_id` (`string`, kế thừa `candidate_id` hiện có):** Định danh bài toán ứng viên trả về từ bước chuẩn bị đề, kèm danh sách `source_attachment_ids: string[]` chỉ rõ những ảnh nào đóng góp vào bài toán đó.
6. **`extraction_status` (vòng đời trạng thái ở tầng chuẩn bị đề):**
   - Phía Client + API phối hợp rõ các chặng: `attached` (chỉ mới đính kèm ở Composer, **chưa gọi AI**) → `preparing` (đang đọc & ghép đề sau khi bấm `Dựng hình`) → `ready` | `needs_selection` | `needs_confirmation` | `rejected` / `failed`.

### 2.3. Quy tắc quan hệ giữa nhiều ảnh & Fail-Safe bảo toàn dữ kiện
- **Không giới hạn cứng ở con số `5` ảnh trong API:** Trần `5` lá chỉ là quy tắc hiển thị gọn của `PhotoFanStack` trên giao diện camera; trần số lượng và tổng dung lượng của `attachments[]` ở Backend sẽ được xác lập theo ngân sách bộ nhớ, độ trễ và quota thực tế (kế thừa trần `MAX_ATTACHMENTS = 10` ở [`frontend/src/llm/input.ts`](../../../../../frontend/src/llm/input.ts) hoặc điều chỉnh theo kết quả đo).
- **Phương án giữ nguyên ảnh gốc khi tự phát hiện vùng đề không chắc chắn:** Nếu bộ tách vùng (`region_detector.py`) gặp ánh sáng yếu, giấy vở cong, công thức sát mép hoặc hình vẽ 3D tách rời phần chữ ở cột bên phải khiến độ tin cậy khung bao không chắc chắn, hệ thống **bắt buộc giữ nguyên toàn bộ khung ảnh gốc**, tuyệt đối không tự cắt bỏ mép ảnh có nguy cơ làm mất giả thiết dẫn tới lỗi thiếu dữ kiện giả tạo ở `Source Gate`.
- **Phân biệt hai kịch bản đa ảnh cốt lõi:**
  1. **Nhiều ảnh thuộc cùng một bài toán** (ví dụ Ảnh `#1` chụp phần lời đề dài, Ảnh `#2` chụp hình vẽ biểu diễn hoặc câu hỏi phụ `b, c`, cộng thêm ghi chú gõ tay trong `user_text`): hợp nhất ngữ cảnh theo đúng `order_index` thành một văn bản đề chuẩn hóa duy nhất (hoặc yêu cầu xác nhận `needs_confirmation` nếu chữ mờ/mâu thuẫn giữa ảnh và ghi chú gõ tay).
  2. **Nhiều bài toán độc lập nằm trong một hoặc nhiều ảnh** (ví dụ chụp cả trang đề kiểm tra có Câu 1, Câu 2, Câu 3): trả về `status = "needs_selection"` kèm danh sách `candidates[]` gắn `problem_candidate_id` và `source_attachment_ids[]` để học sinh chọn đúng `1` bài toán cần dựng hình 3D.

---

## 3. Phân Định Ranh Giới Kiểm Chứng Trung Thực (Epistemic Matrix)

| Nhóm phân loại | Các hạng mục cụ thể |
| :--- | :--- |
| **1. Đã được kiểm chứng thực tế trên `main` hoặc trên Google Chrome** | • Bố cục, tương tác, bàn phím, `Escape`, `prefers-reduced-motion`, không che nút điều khiển, không tự thu quạt khi rê chuột của **Photo Fan Stack** trên Google Chrome (`10/10` rủi ro kiểm toán, `20/20` kịch bản × `6/6` viewport gồm cả Chrome Zoom `110%` thật và màn thấp `390×500`).<br>• Đơn tệp `POST /api/input/prepare` (`unified-input-prepare/1`) và tuyến chính thức `POST /api/analyze` (`Hybrid /4`) hiện hữu trên `main`. |
| **2. Mới được mô phỏng trong Prototype (`Simulated Only`)** | • Luồng hình ảnh camera và việc bấm chụp tạo tờ đề toán hình học không gian độ phân giải cao (`1600×1200`, `1920×1080`, `1200×1600`) đang được dựng bằng `<canvas>` 2D tự chứa, **chưa lấy từ cảm biến camera vật lý** (`REAL_CAMERA_DEVICE_VERIFIED = NO`).<br>• Nút `Dựng hình` trong prototype chỉ mô phỏng thông báo sẵn sàng gửi dữ liệu, không gọi Backend hay Gemini. |
| **3. Mới là đặc tả thiết kế & hợp đồng đề xuất (`Specification Only`)** | • Kiến trúc tách component React (`PhotoFanStack.tsx`, `CameraMobileTray.tsx`, `AttachmentViewerModal.tsx`, `useCameraSession.ts`).<br>• Các trường mở rộng đa ảnh `attachments[]` (`attachment_id`, `order_index`, `source_type`, `request_id`, `problem_candidate_id`, `extraction_status`) và thuật toán hợp nhất ngữ cảnh liên ảnh (`LIVE_AI_MULTI_IMAGE_VERIFIED = NO`). |
| **4. Còn chờ Frontend / Backend triển khai & nghiệm thu thiết bị thật** | • Triển khai React trong `frontend/src/` và mở rộng `POST /api/input/prepare` trong `backend/app/ingestion/`.<br>• Kiểm thử phần cứng camera thật trên iOS Safari, Android Chrome, webcam laptop, dọn dẹp `MediaStreamTrack` / `ObjectURL`, bộ nhớ chụp liên tiếp và kiểm thử trích xuất đa ảnh có trần ngân sách với Gemini thật. |
