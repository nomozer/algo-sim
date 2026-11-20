# AXO WORKSPACE V2.2 — Báo Cáo Nghiệm Thu Tinh Gọn Trình Chỉnh Sửa Bước Dựng & UX Ưu Tiên Dựng Lại

> **Trạng thái:** ĐÃ HOÀN TẤT KIỂM THỬ · `OWNER_APPROVAL = PENDING_OWNER_REVIEW`
> **Nhánh Git:** `feat/axo-geometry-library-verification` · **Commit cơ sở:** `7607f0d6e5e846d97c393e7876f7fa4cf389ad35`

---

## 1. Baseline Trước Sửa (V2.1)

Ở commit cơ sở `7607f0d6e5e846d97c393e7876f7fa4cf389ad35` (V2.1), logic backend (`step_editor.py` với phân giải điểm `O`, kiểm tra vai trò hình học, `prior_step_ids` DAG và phản ví dụ `DOWNSTREAM_CIRCUMSCRIBED_SPHERE_BROKEN`) đã chạy đúng, nhưng phần UX hiển thị ở Study Dock còn nặng so với baseline Hình 1 & Hình 2 theo phản hồi review của Owner:

- Khối bước đang sửa (`.step-row.is-editing`) dùng viền xanh dày `--primary`, `<textarea rows={3}>` tối thiểu `68px` (`71px` thực tế), tạo cảm giác như mở một biểu mẫu lớn trong sidebar thay vì sửa một dòng trong danh sách.
- Sau khi bấm `Chạy` thành công, UI giữ lớp `.is-just-updated` tô nền xanh nhạt và gắn badge/pill `"Đã cập nhật"` trong `2.4s`, kéo dài trạng thái success thay vì trả ngay về nhịp danh sách gọn và để mô hình 3D + nội dung bước tự chứng minh kết quả.
- Trên màn hình chạm (`768×1024`, `390×844`, `320×568`), chiều cao textarea và tap highlight làm hàng bước bị giãn cao hơn nhịp đọc tự nhiên.
- Khi đổi ký hiệu mặt phẳng ở bước 8 (ví dụ `(α)` → `(P)`), nhãn của các bước phụ thuộc phía sau (`truc_day`, `I`) cần tự đồng bộ trực tiếp trong danh sách bước.

---

## 2. Diff Thiết Kế Giữa V2.1 và V2.2

| Thành phần | V2.1 (`7607f0d6e`) | V2.2 (Cleanup & Rebuild-First) |
|---|---|---|
| Trạng thái bình thường `.step-row` | `padding: 7px 34px 7px 9px` (compact `8px 34px 8px 10px`) | `padding: 7px 30px 7px 9px` (compact `8px 30px 8px 10px`), `-webkit-tap-highlight-color: transparent`, khoảng hở text–bút chì **`+9.8px`** |
| Nút bút chì `.step-edit-pencil-btn` | Desktop `24×24`, touch `28×28` | Desktop `22×22` (`top: 6px; right: 5px`), touch `26×26`; ẩn `opacity: 0` khi idle, hiện khi hover/focus (desktop) hoặc active trên mobile |
| Khung sửa `.step-row.is-editing` | Nền `--surface`, viền xanh nổi `var(--primary)` | Nền `--canvas-soft`, viền mảnh trung tính `#d5d2cc` đồng nhất với hàng active của baseline |
| `<textarea>` inline | `rows={3}`, `min-height: 68px..220px`, viền focus xanh 2px dày | `rows={1}`, `min-height: 32px..112px` (`32px` 1 dòng desktop, `32–46px` mobile), viền `#d5d2cc` mảnh, focus ring nhẹ `rgba(0, 117, 222, 0.08)` |
| Nút hành động `Hủy` / `Chạy` | `4px 10px` | Desktop `min-height: 25px` (`padding: 3px 9px`), mobile/touch `min-height: 30px` (`4px 11px`) dễ chạm; chỉ giữ spinner tròn `10×10` kín đáo khi `running` |
| Trạng thái UI sau thành công | Giữ trạng thái `justUpdatedStepTargetId` + `.is-just-updated` + pill `"Đã cập nhật"` (`2.4s`) | **Loại bỏ hoàn toàn state/badge success**; chỉ còn 5 trạng thái (`normal`, `hover`, `editing`, `running`, `error`), đóng editor về compact row ngay khi rebuild xong |
| Đồng bộ bước phụ thuộc | Chủ yếu cập nhật hình học + step đang sửa | Bổ sung `_apply_notation_renames` cập nhật đồng thời `by_id[did]`, `events` và `step_overrides` của mọi bước phụ thuộc xuôi dòng |

---

## 3. Phần Đã Khôi Phục Theo Hình 1 và Hình 2

- **Desktop (Hình 1):** Danh sách bước trở lại nhịp compact chuẩn (`rowHeightPx = 56.9px`), `0` badge thừa, `0` textarea mở sẵn, không có viền/card xanh nặng; khi hover mới lộ icon bút chì `22×22` ở mép phải với `0px` dịch chuyển toàn danh sách.
- **Mobile & Tablet (Hình 2):** Bố cục Stage + Dock giữ nguyên; trên chạm, tap vào hàng bước sẽ hiện nút bút `26×26`; khi mở sửa chỉ tốn `32–46px` cho textarea, hàng liền kề trước/sau vẫn quét đọc mạch lạc, hai nút `Hủy` và `Chạy` đạt chiều cao `30px` gọn và dễ bấm, không wash màu tap cyan.

---

## 4. Phần Giữ Lại Từ V2.1

- Toàn bộ pipeline xác định (`llm_calls = 0`): `Edit → Parse → Resolve → Validate → Rebuild → Verify → Commit → Render`.
- Phân giải ngữ nghĩa điểm `O` (cả `"đi qua O"`, `"qua tâm O của hình vuông ABCD"`, `"trung điểm O của AC"`, `(alpha)`, chữ thường `ab`) có chứng minh vai trò hình học trên Exact Kernel.
- Cơ chế chặn fail-closed với phản ví dụ phá vỡ bất biến (như `M=(0,0,2)` làm hỏng mặt cầu ngoại tiếp → HTTP `422 DOWNSTREAM_CIRCUMSCRIBED_SPHERE_BROKEN`, giữ nguyên bản nháp + Scene3D gốc).
- DAG theo thứ tự bước sư phạm `prior_step_ids`, `HOIST` sự kiện `CREATE`, `NO_OP_EQUIVALENT` + `enrich_construction_continuity`, sửa StrictMode double-render, guard `editRequestSeqRef`, focus return về `.step-edit-pencil-btn` khi bấm `Escape`/`Hủy`, và giữ nguyên góc camera đã xoay.

---

## 5. Bằng Chứng Đã Bỏ Success Badge Thừa

1. **Mã nguồn & CSS:** Xóa hoàn toàn `justUpdatedStepTargetId`, `justUpdatedTimerRef`, `isJustUpdated`, `<span className="step-edit-updated-pill">` khỏi `frontend/src/components/SimulationWorkspace.tsx`; xóa `.step-row.is-just-updated` và `.step-edit-updated-pill` khỏi `frontend/src/styles/global.css`.
2. **Unit Test (`frontend/src/components/construction-step-editor.test.tsx`):** Khẳng định HTML render mặc định không chứa `step-edit-updated-pill`, `is-just-updated`, hay chuỗi `"Đã cập nhật"`.
3. **E2E DOM Check (`v22_qa_report.json`):** `assertZeroSuccessBadges` kiểm tra trước khi sửa, ngay sau khi `Chạy` bước `O` thành công (`zeroBadgesVerified: true`), sau khi đổi `(α)` → `(P)`, sau khi đổi lại `(α)`, và sau cold reload: toàn bộ đều trả `hasUpdatedPillClass = 0`, `hasJustUpdatedClass = 0`, `hasUpdatedText = false`.

---

## 6. Bằng Chứng `Chạy` Rebuild `Scene3D` Và Danh Sách Bước Phụ Thuộc

- **Lần sửa 1 (`"Dựng mặt phẳng (α) đi qua O và vuông góc với AB."`):** API trả HTTP `200`, `mode = "PARTIAL_TOPOLOGICAL_REBUILD"` (`total_ms = 46.918 ms`, `uiRoundTripMs = 1276 ms`), editor tự đóng về hàng compact, `Scene3D` nhảy spotlight đúng `Bước 8/17`, mặt phẳng `(α)` dựng lại đi qua tâm `O` vuông góc `AB`, giữ góc camera người dùng vừa xoay và `duplicateLabels = []`.
- **Lần sửa 2 liên tiếp (`"Dựng mặt phẳng (P) đi qua O và vuông góc với AB."`):** Đổi tên ký hiệu `(α)` → `(P)` cập nhật đồng loạt trên `Scene3D` lẫn `#dock-steps-ul`:
  - Bước 8: `Dựng mặt phẳng (P) đi qua O và vuông góc với AB.`
  - Bước 11 (`truc_day`): `Xác định giao tuyến của (P) và (β)`
  - Bước 12 (`I`): `Xác định giao điểm I = Giao tuyến của (P) và (β) ∩ (γ)`
- **Lần sửa 3 liên tiếp (`"Dựng mặt phẳng (α) qua tâm O của hình vuông ABCD và vuông góc với AB."`):** Bước 8, Bước 11 và Bước 12 cập nhật lại về `(α)` và giữ nguyên bền vững sau reload.

---

## 7. Screenshot Desktop và Mobile

Danh sách ảnh chụp đối chiếu đầy đủ lưu tại thư mục artifact phiên (và nhúng trực tiếp trong bản artifact `AXO-WORKSPACE-V22-EDITABLE-STEPS-CLEANUP-REPORT.md`):

- **Desktop `1920×1080`:** `v22_qa/01_baseline_compact_1920.png`, `02_hover_pencil_1920.png`, `03_editor_compact_1920.png`, `04_error_inline_1920.png`, `05_rebuild_no_badge_1920.png`, `06_dependent_steps_P_1920.png`, `07_viewport_1920x1080.png`.
- **Desktop `1366×768` & `1024×768`:** `v22_qa/07_viewport_1366x768.png`, `07_viewport_1024x768.png`.
- **Tablet & Mobile Touch (`768×1024`, `390×844`, `320×568`):** `v22_qa/08_touch_768x1024.png`, `08_touch_390x844.png`, `08_touch_320x568.png`.

---

## 8. Video Thao Tác Edit Step

- **Video `1920×1080`:** `C:\Users\Bunny\.gemini\antigravity\brain\3ef24255-0976-432d-b0af-48ebb7f2067e\v22_qa\step8_v22_edit_rebuild_1920x1080.webm`
- **Log JSON kiểm chứng:** `C:\Users\Bunny\.gemini\antigravity\brain\3ef24255-0976-432d-b0af-48ebb7f2067e\v22_qa\v22_qa_report.json` (`status: "PASSED"`).

---

## 9. Test Result

| Bộ kiểm thử | Kết quả |
|---|---|
| Backend pytest (`test_editable_construction_steps.py` + `test_final_backend_product_completion.py` + `test_hybrid_cutover_verification.py`) | **`42 passed, 1 warning in 14.06s`** (exit `0`) |
| TypeScript check (`npx tsc -b`) | **`0 errors`** |
| Frontend Vitest (`construction-step-editor.test.tsx`, `class-coverage.test.ts`, `transition-semantics.test.ts`, `tokens.test.ts`, `code-index-sync.test.ts`, `problem-statement-source.test.tsx`, `attempt-identity.test.tsx`) | **`7 files, 42 passed`** (`5.50s`) |
| Frontend bundle (`npx vite build`) | **`built in 7.82s`** (exit `0`) |
| Playwright E2E 10 kịch bản & 6 viewport (`1920×1080`, `1366×768`, `1024×768`, `768×1024`, `390×844`, `320×568`) | **`status: "PASSED"`**, `scrollW == clientW` cả 6 viewport, `unexpectedConsoleErrors: []`, `pageErrors: []` |

---

## 10. Regression Note

- **Landing Page, Sidebar, TopNav, Palette & Scene3D Core:** Tuyệt đối không chỉnh sửa; cả 4 route `/`, `/gioi-thieu`, `/gioi-thieu?preview=v1.4`, `/app` đều trả HTTP `200`.
- **Cổng `3001`:** Tiến trình Vite dev server `task-87186` (PID `2272`, `[::1]:3001`) được bảo toàn nguyên vẹn (`HTTP 200`); tiến trình Vite tạm `4175` dùng cho QA cô lập đã được dọn sạch; `backend/app/main.py` và các hunk working-tree thuộc quyền chủ dự án (`OWNERSHIP_BLOCKED`) được giữ nguyên hoàn toàn.

---

## 11. Danh Sách File Sửa (Allowlist V2.2)

1. `backend/app/simulation/geometry_functions/step_editor.py`
2. `backend/tests/geometry/test_editable_construction_steps.py`
3. `frontend/src/components/ConstructionStepEditor.tsx`
4. `frontend/src/components/construction-step-editor.test.tsx`
5. `frontend/src/components/SimulationWorkspace.tsx` *(chỉ stage 5 hunk dọn V2.2 sạch trên `HEAD` để bảo toàn working tree)*
6. `frontend/src/styles/global.css`
7. `docs/evaluation/geometry/runs/workspace-step-editor-v22-cleanup/AXO-WORKSPACE-V22-EDITABLE-STEPS-CLEANUP-REPORT.md`

---

## 12. Commit Local

- **Nhánh:** `feat/axo-geometry-library-verification` (cha `7607f0d6e5e846d97c393e7876f7fa4cf389ad35`).
- Commit SHA V2.2 sẽ được tạo ngay sau kiểm tra `DOCS_LAYOUT` ở bước commit allowlist và ghi nhận nguyên văn trong bản artifact báo cáo trình Owner.
- Không merge vào `main`, không `git push`.

---

## 13. Quyền Phê Duyệt

- `OWNER_APPROVAL = PENDING_OWNER_REVIEW`
