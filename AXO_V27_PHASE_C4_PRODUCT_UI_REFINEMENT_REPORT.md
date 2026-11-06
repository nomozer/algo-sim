# AXO V2.7 — PHASE C.4: PRODUCT UI REFINEMENT & COMPOSER REPAIR REPORT

## 1. Môi trường & Baseline Xác minh

- **Project:** `d:/Documents/projects/algo-sim`
- **Worktree:** `d:/Documents/projects/algo-sim/.superpowers/worktrees/axo-v27-frontend-integration`
- **Branch:** `feat/axo-v27-frontend-integration`
- **Baseline HEAD (Phase C.3):** `73f51df36ee3a4285b9f66a2ed65ead3709b4099` (`feat(ui): complete Axo V2.7 Phase C.3 exact visual parity and composer attachment repair`)
- **HTML V2.7 Reference:** `axo-unified-ui-v2-7-composer-validation-divider-review.html`
- **SHA-256 Reference (Verified):** `EF6176C2DF5FE059B27B9BBEB6922891F78D1F6F97FD7D4E9BD992DBD0CCDF45`
- **Automated Test Suite:** `86 passed` test files (`1462 passed` tests via `npx vitest run`)
- **Production Build:** `tsc -b && vite build` (`0` errors, clean production bundle)
- **Playwright Multi-Viewport & Functional Verification:** `phaseC4_verification_summary.json` (`0px` horizontal overflow across all 7 required viewports)

---

## 2. Bảng Đối Chiếu Toàn Diện Phase C.4 (Mandatory Comparison Table)

| Khu vực | V2.7 / yêu cầu mới | React trước | React sau | Functional | Visual |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P0. Import Wizard — Dữ liệu Demo** | Loại bỏ hoàn toàn 3 bộ dữ liệu demo/test khỏi UI sản phẩm (`Tệp mẫu chuẩn (3 dòng)`, `Danh sách trường (100 dòng)`, `Tệp kiểm thử đủ 6 nhóm (8 dòng)`); giữ nút chính thức `Tải tệp mẫu (.csv)` chỉ chứa dòng tiêu đề cột. | Hiển thị cụm `.bulk-demo-presets` với 3 nút tự điền dữ liệu giả (`#btn-bulk-preset-sample3`, `#btn-bulk-preset-100rows`, `#btn-bulk-preset-mixed8`); tệp mẫu tải về chứa 2 dòng tài khoản mẫu; tải tệp `.xlsx` bất kỳ tự động điền `sampleXlsx` giả. | Đã gỡ bỏ hoàn toàn `.bulk-demo-presets` và 3 nút dữ liệu giả khỏi `AuthGate.tsx`; giữ nút chính thức `#btn-bulk-step1-download-template` (`Tải tệp mẫu (.csv)`) xuất đúng tiêu đề cột `Họ và tên,Email,Trường/Đơn vị\r\n`; đọc dữ liệu thật từ `.xlsx` (OpenXML `sharedStrings.xml` + `sheet1.xml`) và báo lỗi trung thực khi tệp `.xlsx` hỏng. | **PASS** | **PASS** |
| **P0. Import Wizard — Logic Bước 1–4 (`Trường/Đơn vị` trống)** | Nhất quán giữa cột bắt buộc ở Bước 1 (`Họ và tên`, `Email`, `Trường/Đơn vị`), phân loại ở Bước 2, bảng xem trước ở Bước 3, và danh sách tạo tài khoản ở Bước 4; thông báo lỗi trung thực khi backend lỗi. | Bước 1 ghi `Trường/Đơn vị` là cột bắt buộc nhưng `analyzeBulkInput` chỉ kiểm tra `!fullName \|\| !email`, dẫn đến dòng bỏ trống `Trường/Đơn vị` vẫn được tính là `Hợp lệ` và gán `"Chưa cập nhật"` khi tạo tài khoản ở Bước 4. | `analyzeBulkInput` kiểm tra `!fullName \|\| !email \|\| !school`; dòng thiếu `Trường/Đơn vị` được phân loại vào `missing_info` (`Thiếu thông tin: Chưa nhập Trường/Đơn vị`), hiển thị `(Trống)` + badge `Có lỗi` tại Bước 3, và bị loại khỏi danh sách tạo tài khoản tại Bước 4; hiển thị lỗi trung thực khi `/api/admin/users/bulk-import` trả lỗi (ví dụ HTTP 503). | **PASS** | **PASS** |
| **P1. Header & Điều hướng N1** | Header desktop cao `56–60px`; Logo (`24×24px`) + wordmark `Axo` (`16.5px`) cân đối trong cùng vùng nhấn `#btn-brand-home`; chữ điều hướng `14–15px`; nút `Đăng nhập`/`Đăng ký` cao tối thiểu `36px`, chữ `14px`. | Header cao `52px`; Logo `22×22px`, wordmark `15px`; chữ điều hướng `13px`; nút `Đăng nhập`/`Đăng ký` chữ `12.5px` (cao `~30px`). | Header desktop cao `56px` (`50px` ở `<=680px`, `46px` ở `<=480px`); Logo `24×24px` + wordmark `Axo` `16.5px` trong `#btn-brand-home`; `.nav-n1-item` chữ `14px`, cao tối thiểu `34px`; `.btn-auth-ghost` và `.btn-auth-primary` chữ `14px`, cao tối thiểu `36px`. | **PASS** | **PASS** |
| **P1. Trang chủ (Hero, Container, Starter Cards)** | Vùng nội dung chính `880–960px` trên desktop; tiêu đề trang chủ `30–34px`; Composer cân đối với chiều rộng nội dung; card gợi ý có hình minh họa và tiêu đề dễ đọc; khoảng cách hợp lý giữa Composer, Gợi ý khám phá và Tiếp tục học. | `.home-container` rộng `840px`; tiêu đề `.hero-title` `28px`; thumbnail card gợi ý cao `96px`, tiêu đề `13px`. | `.home-container` rộng `920px` trên desktop (`padding: 36px 24px 64px`); `.hero-title` `32px`; Composer rộng `872px`; `.starter-thumb` cao `106px`, `.starter-title` `13.5px` (`line-height: 1.42`); khoảng cách giữa Composer, Gợi ý khám phá và Tiếp tục học cân đối (`32px`). | **PASS** | **PASS** |
| **P1. Các phân hệ khác (Library, History, Workspace, Modals, Admin)** | Rà soát kích thước chữ và vùng nhấn của Thư viện, Lịch sử học, Header Workspace, Study Dock, Playback, Login/Register, Account Settings, Admin Dashboard, Import Wizard; không khôi phục tính năng đã loại bỏ. | Tiêu đề trang Thư viện/Lịch sử `22px`, tiêu đề card `13.5px`, nút `Tiếp tục →` cao `~30px`. | `.page-main-title` `24px`, `.page-sub-desc` `13.5px`, `.lib-card-title` / `.hist-title` `14px`, `.btn-hist-resume` `12.8px` (`min-height: 34px`); Header Workspace, Study Dock, Playback, Login/Register, Account Settings, Admin Dashboard và Import Wizard đồng bộ tỷ lệ; không khôi phục Lớp học / Bài đã giao / Tách hình. | **PASS** | **PASS** |
| **P2. Composer — Chiều cao tự mở rộng theo nội dung** | Mặc định thu gọn hiển thị ~3 dòng (`76px` textarea, `148px` card), không cao ~200px khi trống; giữ nguyên chiều cao ở 1–3 dòng (`Shift+Enter` lần 1 và 2); tự mở rộng ở dòng thứ 4 (`Shift+Enter` lần 3 hoặc soft-wrap) đến tối đa `220px` rồi cuộn nội dung; tự thu nhỏ khi xóa bớt; đính kèm file không làm tăng chiều cao textarea. | `.composer-textarea` có `min-height: 110px` (card cao `~182px` ngay khi trống) và không có cơ chế đo `scrollHeight` để tự mở rộng / thu gọn theo số dòng thực tế. | `.composer-textarea` mặc định cao `76px` desktop (`72px` mobile), card cao `148px`; giữ nguyên `76px` khi trống, nhập 1 dòng, `Shift+Enter` lần 1 (2 dòng) và `Shift+Enter` lần 2 (3 dòng); tự mở rộng lên `100px` ở `Shift+Enter` lần 3 (4 dòng) hoặc văn bản tự xuống dòng 4+ dòng; chạm trần `220px` (`overflow-y: auto`) khi dán 12 dòng; thu nhỏ về `76px` khi xóa; đính kèm tệp hiển thị ở `.composer-files-wrap` riêng và giữ nguyên textarea `76px`. | **PASS** | **PASS** |
| **P3. File Attachment — Visual States theo V2.7** | Đối chiếu đầy đủ 7 trạng thái (Default, Hover, Focus bàn phím, Đang tải, Tải thành công, Tải thất bại, Xóa tệp) theo HTML V2.7; hỗ trợ PNG/PDF/DOCX, rút gọn tên dài + tooltip đầy đủ không bị cắt, modal xem chi tiết từng tệp. | Card tệp thiếu trạng thái `is-loading`/`is-error`, thiếu bàn phím `:focus-visible`, thiếu `.file-full-tooltip`, thiếu modal xem trước từng tệp `#composer-single-file-modal`, và chưa phân biệt rõ `.badge-pdf` / `.badge-docx`. | Card `.file-preview-card` khớp hoàn toàn V2.7: Default (`#F7F6F2`, border `#E4E2DC`, radius `10px`), Hover (`#EFECE6`, border `#0075DE`, `var(--shadow-soft)`), Focus bàn phím (`outline: 2px solid var(--primary)`), Loading (`is-loading` + `.badge-loading`), Ready (PNG thumbnail, `.badge-pdf`, `.badge-docx`), Error (`is-error` `#FEF2F2`/`#FECACA` + `.badge-error`), nút xóa `×` (`hover` đỏ `#FEF2F2`/`#FECACA`/`#B91C1C`), `.file-full-tooltip` hiển thị đầy đủ không bị clip, và `#composer-single-file-modal`. | **PASS** | **PASS** |
| **P4. Bảo vệ Workspace & Scene3D** | Không chỉnh sửa Geometry Engine, Kernel, Planner, Compiler, Construction IR, contract hình học, thuật toán dựng/kiểm chứng, Camera/Scene3D renderer, `DESIGN.md`, hoặc worktree của Claude/backend. | Baseline Phase C.3 giữ nguyên toàn bộ pipeline hình học và Scene3D. | `0` thay đổi trên toàn bộ Geometry Engine, Kernel, Planner, Compiler, Construction IR, Scene3D renderer và `DESIGN.md`; Workspace 3D (`canvas`, Study Dock, Playback) hoạt động nguyên vẹn. | **PASS** | **PASS** |
| **P5. Kiểm chứng Playwright trên 7 Viewports** | Mở HTML V2.7 và React trong trình duyệt thật, kiểm chứng ở `1440×900`, `1366×768`, `1024×768`, `820×1180`, `600×900`, `390×844`, `360×800`. | Chưa có bộ đo kiểm tự động cho Composer auto-expand, P0 empty school validation, và 7 trạng thái File Attachment trên 7 viewports. | Đã chạy kiểm chứng Playwright tự động (`verify_phase_c4.mjs`) và đối chiếu hình ảnh trực tiếp trên cả 7 viewports: `horizontalOverflowPx = 0` trên toàn bộ 7 kích thước màn hình. | **PASS** | **PASS** |

---

## 3. Chi Tiết Triển Khai & Kết Quả Đo Lường Thực Tế

### 3.1. P0 — Import Wizard: Loại bỏ dữ liệu demo & chuẩn hóa logic kiểm tra Bước 1–4

1. **Loại bỏ dữ liệu demo khỏi giao diện sản phẩm ([`AuthGate.tsx`](frontend/src/components/AuthGate.tsx)):**
   - Đã xóa cụm nút `.bulk-demo-presets` (`#btn-bulk-preset-sample3`, `#btn-bulk-preset-100rows`, `#btn-bulk-preset-mixed8`), hàm `applyBulkPreset` và dữ liệu giả `sampleXlsx`.
   - Kiểm chứng DOM thực tế (`phaseC4_verification_summary.json`):
     - `sample3`: `0`
     - `rows100`: `0`
     - `mixed8`: `0`
     - `officialTemplateBtn` (`#btn-bulk-step1-download-template`): `1`
   - Nút **Tải tệp mẫu (.csv)** (`#btn-bulk-step1-download-template`) chỉ xuất dòng cấu trúc cột chính thức: `Họ và tên,Email,Trường/Đơn vị\r\n`, không chứa bất kỳ dòng tài khoản giả nào.
2. **Đọc tệp `.xlsx` thật và báo lỗi trung thực:**
   - Bổ sung bộ đọc OpenXML `.xlsx` (`parseXlsxBufferToCsvText`, giải nén `xl/sharedStrings.xml` và `xl/worksheets/sheet1.xml` qua `DecompressionStream("deflate-raw")`).
   - Khi người dùng chọn tệp `.xlsx` không hợp lệ hoặc bị hỏng, giao diện dừng lại tại Bước 1, khóa nút `Tiếp theo →` (`disabled = true`) và hiển thị thông báo lỗi trung thực:
     > `"Không thể đọc nội dung tệp .xlsx này. Vui lòng kiểm tra lại định dạng tệp Excel chuẩn (3 cột bắt buộc: Họ và tên, Email, Trường/Đơn vị) hoặc lưu dưới dạng .csv (UTF-8)."`
3. **Nhất quán quy tắc cột bắt buộc `Trường/Đơn vị` từ Bước 1 đến Bước 4:**
   - Khi dòng dữ liệu bỏ trống `Trường/Đơn vị` (ví dụ dòng `#3: Lê Văn C, c@truong.edu.vn, `):
     - **Bước 2:** Phân loại vào nhóm `Thiếu thông tin bắt buộc` (`missing_info`).
     - **Bước 3:** Hiển thị cột Trường/Đơn vị là `(Trống)`, trạng thái `Có lỗi`, chi tiết lỗi `Thiếu thông tin: Chưa nhập Trường/Đơn vị`.
     - **Bước 4:** Không đưa dòng thiếu `Trường/Đơn vị` vào danh sách tài khoản hợp lệ sẽ tạo (`validToCreate: 2`, `skipCount: 6` trên bộ kiểm thử 8 dòng).
     - **Khi Backend trả lỗi (ví dụ HTTP 503):** Hiển thị thông báo lỗi trung thực ngay trong Bước 4 (`Dịch vụ tạo tài khoản hàng loạt tạm thời gián đoạn (HTTP 503).`), tuyệt đối không giả lập thành công.

### 3.2. P1 — Chuẩn hóa tỷ lệ giao diện trên toàn hệ thống ([`global.css`](frontend/src/styles/global.css))

Số đo thực tế tại viewport desktop `1440×900` (`phaseC4_verification_summary.json`):
- **Header (`.nav-bar`):** cao `56px` trên desktop (`1440×900`, `1366×768`, `1024×768`, `820×1180`), `50px` trên tablet nhỏ (`600×900`), `46px` trên mobile (`390×844`, `360×800`).
- **Logo & Wordmark (`#btn-brand-home`):** Logo `24×24px` + chữ `Axo` `16.5px` nằm trong cùng một nút điều hướng về Trang chủ.
- **Điều hướng N1 (`.nav-n1-item`):** `font-size: 14px`, `min-height: 34px`.
- **Nút Đăng nhập / Đăng ký (`.btn-auth-ghost`, `.btn-auth-primary`):** `font-size: 14px`, `min-height: 36px`.
- **Vùng nội dung chính (`.home-container`):** rộng `920px` (nằm chính giữa khoảng mục tiêu `880–960px`).
- **Tiêu đề Trang chủ (`.hero-title`):** `font-size: 32px` (nằm chính giữa khoảng mục tiêu `30–34px`).
- **Composer (`.composer-card`):** rộng `872px`, cân đối với `.home-container` và lưới `.starter-grid`.
- **Card gợi ý khám phá (`.starter-card`):** cao `201px`, hình minh họa `.starter-thumb` cao `106px`, tiêu đề `.starter-title` `13.5px`.

### 3.3. P2 — Composer: Chiều cao tự mở rộng theo nội dung ([`ProblemInput.tsx`](frontend/src/components/ProblemInput.tsx), [`global.css`](frontend/src/styles/global.css))

Đã triển khai hàm `syncTextareaHeight()` đo `scrollHeight` thực tế kết hợp `useEffect([problemText])` và `ResizeObserver`. Kết quả đo thực tế trên Chromium (`phaseC4_verification_summary.json`):

| Trạng thái nhập liệu | Chiều cao `<textarea>` | Chiều cao `.composer-card` | `overflow-y` | Ghi chú |
| :--- | :---: | :---: | :---: | :--- |
| **1. Trống (Empty)** | `76px` | `148px` | `hidden` | Thu gọn ~3 dòng, không dùng chiều cao lớn ~200px |
| **2. Nhập 1 dòng** | `76px` | `148px` | `hidden` | Giữ nguyên chiều cao thu gọn |
| **3. `Shift + Enter` lần 1 (2 dòng)** | `76px` | `148px` | `hidden` | Chưa mở rộng |
| **4. `Shift + Enter` lần 2 (3 dòng)** | `76px` | `148px` | `hidden` | Chưa mở rộng |
| **5. `Shift + Enter` lần 3 (4 dòng)** | `100px` | `172px` | `hidden` | Tự động mở rộng thêm 1 dòng (`+24px`) |
| **6. Văn bản dài tự xuống dòng (4+ dòng)** | `100px` | `172px` | `hidden` | Mở rộng theo `scrollHeight` thực tế (không đếm phím) |
| **7. Dán văn bản dài (12 dòng)** | `220px` | `292px` | `auto` | Chạm trần `220px`, cho phép cuộn nội dung bên trong (`scrollHeight = 292px`) |
| **8. Xóa bớt về 1 dòng** | `76px` | `148px` | `hidden` | Tự động thu nhỏ về kích thước mặc định |
| **9. Đính kèm 5 tệp + 1 dòng văn bản** | `76px` | `248px` | `hidden` | Danh sách tệp nằm ở `.composer-files-wrap` riêng; `<textarea>` giữ nguyên `76px` |

### 3.4. P3 — File Attachment: Visual States khớp HTML V2.7 ([`ProblemInput.tsx`](frontend/src/components/ProblemInput.tsx), [`global.css`](frontend/src/styles/global.css))

- **Default:** `background: #F7F6F2`, `border: 1px solid #E4E2DC`, `border-radius: 10px`, `width: 214px`, `padding: 7px 26px 7px 8px`.
- **Hover:** `background: rgb(239, 236, 230)` (`#EFECE6`), `border-color: rgb(0, 117, 222)` (`var(--primary)`), `box-shadow: var(--shadow-soft)`, hiển thị `.file-full-tooltip` (`opacity: 1`) không bị cắt bởi khung cuộn ngang.
- **Keyboard Focus (`:focus-visible` / `:focus-within`):** `outline: 2px solid var(--primary)`, `outline-offset: 2px`, hiển thị `.file-full-tooltip`.
- **Loading (`is-loading`):** `border-style: dashed`, `background: #FAF9F5`, icon `.badge-loading` với spinner quay mượt và trạng thái `"Đang tải lên..."`.
- **Ready:** Hiển thị thumbnail thực tế cho ảnh (`PNG`/`JPG`), `.badge-pdf` (`#FEF2F2` / `#DC2626`) cho `PDF`, `.badge-docx` (`#EBF5FF` / `#0075DE`) cho `DOCX`, kèm định dạng và dung lượng.
- **Error (`is-error`):** `background: #FEF2F2`, `border-color: #FECACA`, icon `.badge-error` và thông báo lỗi màu `#B91C1C`.
- **Nút xóa `×` (`.file-remove-mini`):** Hover chuyển sang `background: rgb(254, 242, 242)` (`#FEF2F2`), `border-color: rgb(254, 202, 202)` (`#FECACA`), `color: rgb(185, 28, 28)` (`#B91C1C`), xóa đúng tệp được chọn mà không mở nhầm modal.
- **Modal xem chi tiết 1 tệp (`#composer-single-file-modal`) & tất cả tệp (`#composer-all-files-modal`):** Hỗ trợ mở xem chi tiết, xóa tệp từ trong modal và đóng bằng phím `Escape`.

### 3.5. P5 — Kiểm chứng Đa Viewport (7 Viewports)

| Viewport | `horizontalOverflowPx` | Chiều cao Header | Chiều cao `<textarea>` | Chiều cao `.composer-card` | Ảnh chụp kiểm chứng |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`1440×900`** | `0px` | `56px` | `76px` | `148px` | `phaseC4_viewport_1440x900.png` |
| **`1366×768`** | `0px` | `56px` | `76px` | `148px` | `phaseC4_viewport_1366x768.png` |
| **`1024×768`** | `0px` | `56px` | `76px` | `148px` | `phaseC4_viewport_1024x768.png` |
| **`820×1180`** | `0px` | `56px` | `76px` | `148px` | `phaseC4_viewport_820x1180.png` |
| **`600×900`** | `0px` | `50px` | `76px` | `148px` | `phaseC4_viewport_600x900.png` |
| **`390×844`** | `0px` | `46px` | `72px` | `143px` | `phaseC4_viewport_390x844.png` |
| **`360×800`** | `0px` | `46px` | `72px` | `143px` | `phaseC4_viewport_360x800.png` |

---

## 4. Danh Sách Tệp Đã Thay Đổi

1. [`frontend/src/components/AuthGate.tsx`](frontend/src/components/AuthGate.tsx) — Loại bỏ 3 bộ dữ liệu demo trong Import Wizard, giữ nút tải mẫu `.csv` chỉ gồm tiêu đề cột, bổ sung đọc tệp `.xlsx` thật + báo lỗi tệp hỏng, và đồng bộ kiểm tra cột bắt buộc `Trường/Đơn vị` từ Bước 1 đến Bước 4.
2. [`frontend/src/llm/input.ts`](frontend/src/llm/input.ts) — Mở rộng `ComposerAttachmentItem` hỗ trợ loại `"pdf"` và trạng thái `"loading" | "ready" | "error"` cùng `errorMessage`.
3. [`frontend/src/components/ProblemInput.tsx`](frontend/src/components/ProblemInput.tsx) — Triển khai cơ chế tự mở rộng chiều cao `<textarea>` từ mốc 3 dòng (`76px` desktop / `72px` mobile) đến `220px`, hoàn thiện 7 trạng thái hiển thị của `.file-preview-card`, `.file-full-tooltip` và `#composer-single-file-modal`.
4. [`frontend/src/styles/global.css`](frontend/src/styles/global.css) — Chuẩn hóa tỷ lệ giao diện toàn hệ thống (P1), chiều cao thu gọn/mở rộng của `.composer-textarea` (P2), các trạng thái `.file-preview-card` + `.file-full-tooltip` không bị cắt (P3), và responsive header ở `<=680px` / `<=480px` (P5).
5. [`frontend/src/components/phase-b-views.test.tsx`](frontend/src/components/phase-b-views.test.tsx) — Cập nhật và bổ sung kiểm thử đơn vị cho Import Wizard Phase C.4 (không còn nút demo, kiểm tra dòng trống `Trường/Đơn vị` bị gắn `missing_info`, từ chối tệp `.xlsx` lỗi).
6. [`frontend/src/components/slice2-composer.test.tsx`](frontend/src/components/slice2-composer.test.tsx) — Bổ sung kiểm thử đơn vị cho cơ chế tự mở rộng Composer theo dòng và 7 trạng thái File Attachment + modal xem trước.

---

## 5. Deferred Issues (Ngoài phạm vi Phase C.4)

- Không phát sinh lỗi Scene3D hoặc Geometry Engine mới trong phạm vi kiểm chứng Phase C.4. Toàn bộ quy tắc bảo vệ P4 được giữ nguyên 100%.
