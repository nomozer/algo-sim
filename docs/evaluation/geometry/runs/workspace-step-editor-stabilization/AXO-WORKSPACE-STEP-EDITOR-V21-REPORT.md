# AXO WORKSPACE V2.1 — Báo Cáo Nghiệm Thu Ổn Định Trình Chỉnh Sửa Bước Dựng & Phục Hồi Ngữ Nghĩa

> **Trạng thái nghiệm thu:** ĐÃ HOÀN TẤT KIỂM THỬ KỸ THUẬT · `OWNER_APPROVAL = PENDING_OWNER_REVIEW`
> **Khuyến nghị tích hợp:** **`GO`** (cho phép Owner review & quyết định merge từ `feat/axo-geometry-library-verification`; không tự ý merge `main` hay `git push`)

---

## 1. Nhánh Git, Commit Cơ Sở & Phân Loại Phạm Vi

| Thuộc tính | Giá trị xác minh thực tế |
|---|---|
| Repository | `D:\Documents\projects\axo-geometry-library` |
| Nhánh làm việc | `feat/axo-geometry-library-verification` |
| Commit cơ sở (V1) | `438fa69cab04bc266110937874051e8616d8ea37` (`feat(workspace): add editable construction steps, deterministic partial kernel rebuild, and verified feedback pipeline`) |
| Vite dev server port `3001` | Bảo toàn nguyên trạng (`task-87186`, PID `2272`, lắng nghe `[::1]:3001`, khởi chạy lúc `17:21:52`) |

### Phân loại phạm vi KEEP / FIX / REFINE / OWNERSHIP_BLOCKED

| Nhóm | Thành phần / File | Quyết định |
|---|---|---|
| **KEEP** | `backend/app/persistence/step_edit_models.py`, `backend/app/simulation/geometry_functions/feedback_dataset.py`, `backend/scripts/prepare_step_feedback_dataset.py`, toàn bộ Landing Page (`LandingView.tsx`, `components/landing/*`), Exact Kernel primitives (`backend/app/simulation/geometry/*`), pipeline `Hybrid /4` | Giữ nguyên hợp đồng & hành vi ổn định |
| **FIX** | `backend/app/simulation/geometry_functions/step_editor.py`, `backend/app/simulation/step_edit_router.py`, `backend/tests/geometry/test_editable_construction_steps.py` | Sửa semantic resolution điểm `O`, thứ tự bước sư phạm vs event DAG, `_find_pt` scope leak, equivalence check & bất biến mặt cầu ngoại tiếp |
| **REFINE** | `frontend/src/state/construction-step-edits.ts`, `frontend/src/components/ConstructionStepEditor.tsx`, `frontend/src/components/SimulationWorkspace.tsx`, `frontend/src/styles/global.css`, `frontend/src/components/construction-step-editor.test.tsx` | Khoảng thở hover `34px`, auto-grow `<textarea>`, focus-return, `Ctrl/Cmd+Enter`, guard chống stale-response, auto-focus bước vừa dựng & pill `"Đã cập nhật"`, sửa StrictMode render ref |
| **OWNERSHIP_BLOCKED** | Các thay đổi song song của chủ dự án trong working tree (`backend/app/accounts/*`, `classroom_models.py`, `backend/app/main.py` lines 74–96, `docs/EVIDENCE_INDEX.md`, `frontend/index.html`, `frontend/package*.json`, `Scene3DExplorer.tsx`, `store.ts`, `history.ts`, `learner-recovery-snapshot.ts`, các hunk classroom/tabs ngoài scope trong `SimulationWorkspace.tsx`) | Tuyệt đối không sửa, không revert, không stage, không commit |

---

## 2. Danh Sách Các Lỗi Đã Tái Hiện

1. **Tái hiện ca điểm `O` trên Sample 11 (Bước 8 — `mp_tt_AB`):** Câu chuẩn `"Dựng mặt phẳng (α) đi qua O và vuông góc với AB."` lẫn các biến thể tự nhiên có vai trò hình học (`"đi qua tâm O"`, `"qua tâm O của hình vuông ABCD"`, `"Dựng (α) đi qua O..."`, `"Mặt phẳng (α) đi qua O..."`, `(alpha)`, chữ thường `ab`) bị từ chối hoặc thiếu linh hoạt ngữ pháp.
2. **Lệch thứ tự sư phạm UI (`pedPlan.steps`) so với `scene3d.events`:** Một số bước hiển thị sớm hơn trong UI hoặc reorder theo dependency gây lỗi giả `CYCLE_DEPENDENCY` / `DEPENDENCY_BEFORE_CREATION`; đồng thời `_find_pt` truyền `mem` toàn cục vào `local_mem` của `_resolve_point_id` làm rò rỉ scope sang đối tượng bước sau.
3. **Sai sót kiểm tra tương đương & bước đầu:** `_semantic_equivalence_check` gộp nhầm mặt phẳng khi có ràng buộc vai trò điểm; nhánh `NO_OP_EQUIVALENT` thiếu `enrich_construction_continuity` và thiếu handler `construct_polygon` / `construct_solid` khi sửa bước sớm (`day_ABCD`).
4. **Phản ví dụ toán học lọt kiểm định:** Thay Bước 8 thành `"Dựng mặt phẳng (α) đi qua M và vuông góc với AB."` (với $M=(0,0,2)$ là trung điểm $SA$, không cách đều $A, B$) vẫn cho qua ở V1 và đẩy tâm cầu $I$ sang $(0,2,2)$ làm $IA^2 = IS^2 = 8 \neq IB^2 = 24$, phá vỡ mặt cầu ngoại tiếp `cau_ngoai_tiep`.
5. **Lỗi React `<StrictMode>` không focus đúng bước vừa dựng lại:** Trong dev mode (`StrictMode` render đôi), việc ghi đè `syncedRawSourceSceneRef.current` và xóa `pendingFocusTargetIdRef.current = null` ngay trong lúc render khiến lần render thứ 2 hiểu nhầm là đổi bài và reset `tt.current_step` về bước cuối cùng thay vì giữ spotlight tại Bước 8.
6. **Chạm chữ ở mép phải hàng bước khi hover (`padding-right: 10px`):** Nút bút chì hover xuất hiện đè sát phần text cuối của tiêu đề bước dài; ở pointer thô (`768×1024`, `390×844`, `320×568`), vùng chạm bút chì `22×22` nhỏ hơn mức thoải mái (`28×28`).

---

## 3. Nguyên Nhân Gốc Rễ Chính Xác Của Lỗi Điểm `O`

Điều tra pháp y qua toàn bộ 6 điểm kiểm tra (§2.1 #1–#6) cho thấy **hai lớp nguyên nhân song song**:

1. **Bằng chứng V1 chụp điểm `Q` không tồn tại:** Trong ảnh V1 `editable_steps_qa/04_error_inline_1920.png` và QA script V1 (`verify_editable_steps_live.mjs`), input gửi xuống API thực chất là `"Dựng mặt phẳng (α) đi qua Q và vuông góc với AB."` → thông báo lỗi `"Không thể dựng mặt phẳng (α) vì chưa xác định được điểm Q."`; ở cỡ chữ Inter `12px`, đuôi `1px` của chữ `Q` dễ nhìn nhầm thành `O`.
2. **4 lỗi code thật bị phơi bày khi kiểm thử điểm `O` toàn diện:**
   - Parser chưa tách cụm vai trò điểm (`tâm O`, `tâm O của hình vuông ABCD`, `trung điểm O của AC`, `giao điểm O của AC và BD`), dạng rút gọn (`Dựng (α)...`, `Mặt phẳng (α)...`), tên Hy Lạp ASCII `(alpha)` và ký hiệu đoạn viết thường `ab`.
   - `_find_pt` truyền `mem` thay vì `{}` vào `_resolve_point_id(..., local_mem=...)`, khiến `post_step_ids` bị che khuất khỏi kiểm tra thứ tự; đồng thời `step_editor.py` chưa nhận `prior_step_ids` từ `pedPlan.steps` để hoist sự kiện `CREATE` hợp lệ khi bước dựng nằm trước theo thứ tự hiển thị.
   - `_semantic_equivalence_check` đối chiếu `perp_plane` cần giới hạn chặt theo `cand_pt["id"] == pt_dep["id"]` khi không có role assertion để chuyển `M_AB`/`H` về `O` luôn chạy full `PARTIAL_TOPOLOGICAL_REBUILD`.
   - `verify_rebuilt_geometry` chưa kiểm tra lại bất biến khoảng cách đều tới mọi đỉnh của đa diện ngoại tiếp sau khi tính lại tâm mặt cầu `I` và bán kính `R`.

---

## 4. Khắc Phục Parser, Symbol Resolver & Dependency DAG

Các thay đổi xác định (deterministic, `llm_calls = 0`) tại `backend/app/simulation/geometry_functions/step_editor.py` và `backend/app/simulation/step_edit_router.py`:

- **`_normalize_vi_math` & `_extract_segment_endpoints`:** Chuẩn hóa `(alpha)/(beta)/(gamma)/(delta)/(phi)` → ký hiệu chuẩn và nhận diện tên đoạn thẳng `AB` lẫn `ab`.
- **`_parse_point_ref_phrase` & `_verify_point_role_assertion`:** Tách cụm vai trò (`center`, `midpoint`, `intersection`) khỏi tên điểm mục tiêu và chứng minh bằng **Exact Kernel** (`Fraction` / tọa độ chính xác) trước khi cho phép dùng điểm `O`; từ chối fail-closed nếu vai trò sai (`"tâm A của hình vuông ABCD"` → `ROLE_ASSERTION_FAILED`, `"trung điểm O của AB"` → `ROLE_ASSERTION_FAILED` hoặc `SYMBOL_CONFLICT`).
- **Sửa scope `_find_pt` & DAG theo `prior_step_ids`:** `_find_pt` truyền `{}` làm `local_mem` để không rò rỉ đối tượng bước sau; `StepEditRequest.prior_step_ids` truyền tập ID có mặt trước bước đang sửa trên `pedPlan.steps`, phục vụ `_symbol_index_before_step` và hoist các `CREATE` event phụ thuộc lên đúng vị trí trong `new_events`.
- **Hoàn thiện nhánh early-step & `NO_OP_EQUIVALENT`:** Bổ sung `construct_polygon` / `construct_solid` và gọi `enrich_construction_continuity` trước `verify_rebuilt_geometry` ở nhánh `NO_OP_EQUIVALENT`.

---

## 5. Kiểm Chứng Hình Học Exact Kernel & Phản Ví Dụ

Trên Sample 11 (`chop-mat-cau-ngoai-tiep`, hình chóp $S.ABCD$ đáy vuông cạnh $4$, $SA \perp (ABCD)$, $SA = 4$):

- Tọa độ Exact Kernel gốc: $A=(0,0,0)$, $B=(4,0,0)$, $C=(4,4,0)$, $D=(0,4,0)$, $S=(0,0,4)$, tâm đáy $O=(2,2,0)$, trung điểm $SA$ là $M=(0,0,2)$.
- **Ca hợp lệ (`"Dựng mặt phẳng (α) đi qua O và vuông góc với AB."`):**
  - $O=(2,2,0)$ thỏa $OA^2 = 8 = OB^2$ (thuộc trung trực `AB`, phương trình $x=2$).
  - Bước dựng chạy `PARTIAL_TOPOLOGICAL_REBUILD`: tái sử dụng `O`, thu hồi (`retired_ids`) nút cũ `M_AB`, tính lại 9 nút xuôi dòng (`truc_day`, `I`, `doan_OI`, `doan_MI`, `doan_IS`, `doan_IA`, `cau_ngoai_tiep`, `R`, `V_cau`), bỏ qua 21 nút không ảnh hưởng (`skipped_unaffected_ids`), không chu trình (`cycle_detected = false`).
  - Kết quả Exact Kernel: $I = (2,2,2)$, kiểm tra đẳng thức bình phương khoảng cách tới 5 đỉnh $IA^2 = IB^2 = IC^2 = ID^2 = IS^2 = 12 \Rightarrow R = 2\sqrt{3}$.
- **Các phản ví dụ đều fail-closed an toàn (`llm_calls = 0`, rollback nguyên trạng `Scene3D`):**
  - `"Dựng mặt phẳng (α) đi qua M và vuông góc với AB."`: $M=(0,0,2)$ khiến tâm $I$ dịch sang $(0,2,2)$ với $IA^2=8 \neq IB^2=24$ → HTTP `422` (`DOWNSTREAM_CIRCUMSCRIBED_SPHERE_BROKEN`), thông báo tiếng Việt rõ ràng và giữ nguyên bản nháp + mô hình 3D gốc.
  - `"Dựng mặt phẳng (α) qua tâm A của hình vuông ABCD và vuông góc với AB."` → bị chặn (`ROLE_ASSERTION_FAILED`).
  - Điểm `O` chưa tồn tại trước bước đang sửa → bị chặn (`MISSING_DEPENDENCY`).

---

## 6. Tinh Chỉnh UI/UX & Khả Năng Quan Sát

- **Ổn định bố cục & khoảng thở (`frontend/src/styles/global.css`):** Đặt `padding: 7px 34px 7px 9px` (desktop) và `8px 34px 8px 10px` (compact panel) trên `.step-row:not(.is-editing)`, giữ `0px` dịch chuyển khi hover/focus và tạo khoảng hở đo được **`+6.8px`** giữa mép phải văn bản (`1866.3px`) và mép trái nút bút chì (`1873px`). Trên `.step-row.is-editing`, khôi phục `padding-right: 10px`.
- **Nút chạm & trải nghiệm inline (`frontend/src/components/ConstructionStepEditor.tsx`):** Tăng vùng chạm `@media (hover: none), (pointer: coarse)` của `.step-edit-pencil-btn` lên `28×28`; `<textarea>` tự co giãn chiều cao theo nội dung (`68px` đến `220px`), `Enter` xuống dòng bình thường, `Ctrl+Enter`/`Cmd+Enter` gửi `Chạy`, `Escape` hoặc nút `Hủy` đóng editor và trả focus bàn phím về chính `.step-edit-pencil-btn` của bước đó; chỉ hiển thị đúng 2 nút `Hủy` và `Chạy` (không có `Lưu` hay `Huấn luyện`).
- **Phản hồi trạng thái & chống race-condition (`frontend/src/components/SimulationWorkspace.tsx`):**
  - `editRequestSeqRef` + `activeEditSessionIdRef` loại bỏ phản hồi lỗi thời khi chuyển bài/phiên; khóa nút trong lúc đang chạy (`Đang chạy...`).
  - Khắc phục triệt để lỗi `<StrictMode>` render đôi bằng cách chuyển `rawScene` vào React state `syncedSceneProblem` và xóa `pendingFocusTargetIdRef` sau commit trong `useEffect`.
  - Khi thành công: đóng editor, **giữ nguyên góc camera người dùng đã xoay**, tự động đưa bước active (`is-active`) về đúng bước vừa dựng lại (`Bước 8/17`), và hiển thị pill `"Đã cập nhật"` (`aria-live="polite"`) trong `2.4s`.

---

## 7. Ảnh Chụp Trước / Sau (Playwright Chromium Live)

Bản báo cáo artifact đi kèm (`AXO-WORKSPACE-STEP-EDITOR-V21-REPORT.md` trong thư mục artifact phiên) nhúng trực tiếp đầy đủ ảnh Before (`editable_steps_qa/*`) và After (`v21_qa/*`) ở các đường dẫn sau:

| Trạng thái | Trước (V1 — `editable_steps_qa/`) | Sau (V2.1 — `v21_qa/`) |
|---|---|---|
| Hover bước 8 & khoảng thở bút chì | `02_hover_pencil_1920.png` | `02_hover_pencil_1920.png` (`0px` shift, `+6.8px` clearance) |
| Mở trình chỉnh sửa inline | `03_editor_open_1920.png` | `03_editor_open_1920.png` (`Hủy` & `Chạy`, auto-grow) |
| Phản ví dụ sai bị từ chối HTTP 422 | `04_error_inline_1920.png` (test dùng `Q`) | `04_error_M_counterexample_1920.png` (`M` bị chặn `DOWNSTREAM_CIRCUMSCRIBED_SPHERE_BROKEN`) |
| Thành công với `O` & dựng lại `Scene3D` | `05_rebuilt_H_alpha_1920.png` (phải đổi sang `H`) | `05_success_O_alpha_1920.png` (`(α)` đi qua `O`, active `Bước 8/17`, pill `"Đã cập nhật"`, giữ camera đã xoay) |
| Kiểm tra mặt cầu cuối & đa màn hình | — | `06_final_step_sphere_1920.png`, `07_viewport_1024x768.png`, `08_touch_768x1024.png`, `08_touch_390x844.png`, `08_touch_320x568.png` |

---

## 8. Video Nghiệm Thu Step 8 & Cập Nhật Scene3D

- **Video ghi hình 1920×1080:** `C:\Users\Bunny\.gemini\antigravity\brain\3ef24255-0976-432d-b0af-48ebb7f2067e\v21_qa\step8_edit_O_rebuild_1920x1080.webm`
- **Hiệu năng đo trực tiếp trên phiên E2E (`v21_qa_report.json`):**
  - Parser: `0.316 ms` · Registry: `0.008 ms` · Planner: `3.903 ms` · Dependency Rebuild: `0.404 ms` · Exact Kernel: `0.647 ms` · Scene3D Build: `6.291 ms` · Geometric Validation: `10.220 ms`
  - **Tổng thời gian server:** `25.638 ms` · **Round-trip UI end-to-end:** `1402 ms` · `llm_calls = 0` · `quota_charged = false`

---

## 9. Ma Trận Kiểm Thử 6 Viewport (Desktop / Tablet / Mobile)

| Viewport | Loại tương tác | Overflow ngang (`scrollW / clientW`) | Kích thước & hiển thị bút chì chạm | Trạng thái |
|---|---|---|---|---|
| `1920×1080` | Desktop chuột + phím | `1920 / 1920` (không tràn) | Hover `opacity: 1`, `0px` dịch chuyển, `+6.8px` hở mép | **PASS** |
| `1366×768` | Laptop desktop | `1366 / 1366` (không tràn) | Hover ổn định | **PASS** |
| `1024×768` | Màn hình nhỏ desktop | `1024 / 1024` (không tràn) | Thanh bước & 3D rõ ràng | **PASS** |
| `768×1024` | Tablet (`hasTouch`, `isMobile`) | `768 / 768` (không tràn) | `28×28`, `opacity: "1"` | **PASS** |
| `390×844` | Mobile (`hasTouch`, `isMobile`) | `390 / 390` (không tràn) | `28×28`, `opacity: "1"`, `<textarea>` vừa khung (`taRight: 363`) | **PASS** |
| `320×568` | Mobile tối thiểu (`hasTouch`, `isMobile`) | `320 / 320` (không tràn) | `28×28`, `opacity: "1"`, `<textarea>` vừa khung (`taRight: 293`) | **PASS** |

- **Bàn phím & A11y:** Focus bút chì → `Enter` mở editor → `Enter` thuần chèn ký tự xuống dòng không submit → `Escape` hủy và trả `document.activeElement` về đúng `.step-edit-pencil-btn`; `Ctrl+Enter` gửi dựng lại thành công.
- **Bền vững sau F5 (`page.reload()`):** Nội dung bước 8 sau sửa role (`"...qua tâm O của hình vuông ABCD và vuông góc với AB."`) và hình học dựng lại được khôi phục nguyên vẹn sau khi tải lại trang.

---

## 10. Kết Quả Kiểm Thử Hồi Quy

| Hạng mục kiểm thử | Lệnh chạy / Tuyến kiểm tra | Kết quả thực tế |
|---|---|---|
| Backend Unit + Integration + Counterexamples | `pytest tests/geometry/test_editable_construction_steps.py tests/geometry/test_final_backend_product_completion.py tests/geometry/test_hybrid_cutover_verification.py -q` | **`41 passed, 1 warning in 14.84s`** (exit `0`) |
| TypeScript Build Check | `npx tsc -b` | **`0 errors`** (exit `0`) |
| Frontend Unit & Design-System Tests | `npx vitest run src/components/construction-step-editor.test.tsx src/styles/class-coverage.test.ts src/styles/tokens.test.ts src/code-index-sync.test.ts src/components/problem-statement-source.test.tsx src/components/attempt-identity.test.tsx` | **`6 files, 37 passed`** (`5.39s`) |
| Frontend Production Bundle | `npx vite build` | **`built in 9.78s`** (exit `0`) |
| Regression các tuyến Landing & App | `/`, `/gioi-thieu`, `/gioi-thieu?preview=v1.4`, `/app` trên Playwright Chrome | Toàn bộ trả HTTP **`200`**, `unexpectedConsoleErrors = []`, `pageErrors = []` |

---

## 11. Trạng Thái Mô Hình Trung Thực

- `MODEL_STATUS = "MODEL_NOT_TRAINED"` (báo cáo tường minh qua `/api/simulation/feedback/status`, không suy diễn hoặc gắn nhãn mô hình đã huấn luyện).
- Quá trình chỉnh sửa bước dựng chạy **100% deterministic tại địa phương** (`llm_calls = 0`, `quota_charged = false`).
- Dữ liệu phản hồi chỉ đi vào `TRAINING_ELIGIBLE` sau khi vượt qua Exact Kernel verification **và** được phê duyệt tường minh; mọi cặp mâu thuẫn ngữ nghĩa tự động cách ly ở trạng thái `CONFLICT_QUARANTINED`.

---

## 12. Giới Hạn Kỹ Thuật Còn Lại

1. Bộ phân giải bước dựng tiếng Việt hiện dựa trên văn phạm deterministic của các mẫu dựng hình cốt lõi trong thư viện; diễn đạt tự do ngoài catalog mẫu sẽ bị từ chối fail-closed thay vì gọi LLM suy đoán.
2. `CODE_INDEX` trong `audit_docs_information_architecture.py` vẫn báo 4 đường dẫn stale có sẵn từ các xóa bỏ classroom trước đó trong working tree thuộc phạm vi `OWNERSHIP_BLOCKED` (không do V2.1 gây ra); cấu trúc `DOCS_LAYOUT` đạt `valid: true`.
3. Mạng nội tuyến loopback trên Windows ràng buộc Vite vào `[::1]:3001`, nên các trình duyệt/automation trên máy cục bộ cần truy cập qua hostname `localhost` được browser resolve ổn định sang `[::1]`.

---

## 13. Xác Nhận Bảo Toàn Port `3001`

- Tiến trình Vite dev server trên port `3001` (`task-87186`, PID `2272`, khởi chạy từ `11/17/2026 5:21:52 PM`) được giữ nguyên hoàn toàn trong suốt phiên V2.1 (không kill, không restart, không đổi PID).
- Mọi ảnh chụp, video và kiểm tra E2E 6 viewport đều chạy trực tiếp trên server đang sống này.

---

## 14. Danh Sách File Đã Chạm (Allowlist V2.1) & Commit SHA

1. `backend/app/simulation/geometry_functions/step_editor.py`
2. `backend/app/simulation/step_edit_router.py`
3. `backend/tests/geometry/test_editable_construction_steps.py`
4. `frontend/src/state/construction-step-edits.ts`
5. `frontend/src/components/ConstructionStepEditor.tsx`
6. `frontend/src/components/construction-step-editor.test.tsx`
7. `frontend/src/components/SimulationWorkspace.tsx` *(commit chỉ stage đúng 3 hunk V2.1 ghép sạch trên `HEAD` để bảo toàn 100% thay đổi song song ở working tree)*
8. `frontend/src/styles/global.css`
9. `docs/evaluation/geometry/runs/workspace-step-editor-stabilization/AXO-WORKSPACE-STEP-EDITOR-V21-REPORT.md`

- **Base Commit (trước V2.1):** `438fa69cab04bc266110937874051e8616d8ea37`
- **V2.1 Commit:** Sẽ được ghi nhận ngay sau lệnh commit allowlist trên `feat/axo-geometry-library-verification` và cập nhật chính xác SHA tại bản artifact báo cáo trình Owner.

---

## 15. Khuyến Nghị `GO / NO-GO` & Quyền Phê Duyệt

- **Khuyến nghị kỹ thuật:** **`GO`** — toàn bộ lỗi semantic resolution điểm `O`, thứ tự bước sư phạm vs event DAG, phản ví dụ phá vỡ mặt cầu ngoại tiếp (`M`), lỗi `<StrictMode>` focus bước sau rebuild, hover clearance `+6.8px`, 6 viewport responsive và hồi quy backend/frontend đều đã được chứng minh bằng test & QA trình duyệt sống.
- **Trạng thái phê duyệt:** `OWNER_APPROVAL = PENDING_OWNER_REVIEW`
- **Cam kết an toàn Git:** Không merge vào `main`, không `git push`, toàn bộ thay đổi ngoài phạm vi của chủ dự án trong working tree được giữ nguyên vẹn 100%.
