# AXO STEP EDITOR — INDEPENDENT ACCEPTANCE, ROOT-CAUSE VERIFICATION & MAIN RELEASE PREPARATION REPORT

**Ngày báo cáo:** 2026-11-19  
**Nhánh phát triển:** `feat/axo-geometry-library-verification`  
**Worktree phát triển:** `D:/Documents/projects/axo-geometry-library`  
**Clean Detached Release Candidate:** `D:/Documents/projects/algo-sim/.superpowers/worktrees/step-editor-release-candidate` (`27f2c98d2a0f7e9cbe4de8d23837db29e86f0aea`)  
**Protected Root Checkout:** `D:/Documents/projects/algo-sim` (`axo-ui-consistency` tại `bb046fa22aceff47abe22aa783aa64fc65caee13` — bảo toàn nguyên vẹn)  
**Trạng thái Model 2:** `MODEL_STATUS: MODEL_NOT_TRAINED`  
**Kết luận cuối cùng:** **`READY_FOR_MERGE`** *(Dừng ở cổng phê duyệt của Owner; **không** tự merge vào `main` và **không** tự `git push`)*

---

## 1. Kết luận cuối cùng (`FINAL_VERDICT`)

- **`FINAL_VERDICT = READY_FOR_MERGE`**
- Toàn bộ đường ống Step Editor (`UI → Zustand/Client Cache → FastAPI Router → Step Editor Kernel/Interpreter → PostgreSQL 16.6 Persistence → Scene3D & Construction Continuity`) đã được kiểm chứng độc lập lại từ đầu trên clean detached candidate, không phụ thuộc số liệu từ báo cáo trước.
- Đợt nghiệm thu độc lập lần này đã phát hiện **03 lỗi nguyên nhân gốc thực tế** (`IA-RC1`, `IA-RC2`, `IA-RC3`), đều đã được viết test TDD **RED → GREEN** trước khi sửa, re-seal clean candidate và xác minh lại toàn bộ qua kiểm thử tự động + trình duyệt sống + PostgreSQL 16.6 + REA MCP.
- **`MODEL_STATUS: MODEL_NOT_TRAINED`**: Hệ thống chưa huấn luyện Model 2 trên dữ liệu feedback người dùng (`model_trained: false`); dữ liệu chỉ được thu thập có cấu trúc và cô lập `INELIGIBLE` khỏi tập train tự động khi chưa qua phê duyệt.

---

## 2. Phạm vi kiểm chứng độc lập so với báo cáo Release Gate trước

Báo cáo trước (`docs/evaluation/geometry/runs/step-editor-release-gate/AXO-STEP-EDITOR-FINAL-INTEGRATION-RELEASE-GATE-REPORT.md` tại commit `194c0cca5`) chỉ đóng vai trò tài liệu tham chiếu đầu vào. Phiên nghiệm thu độc lập này trực tiếp thực thi lại:

1. **Kiểm toán mã nguồn & Git topology độc lập:** đối chiếu trực tiếp `git merge-base main HEAD`, phạm vi diff, ranh giới ownership (`Classroom`, `Attachment`, `Landing Page`), và các thay đổi trên nhánh phát triển.
2. **Tạo bộ test nghiệm thu độc lập mới:** `backend/tests/geometry/test_step_editor_main_release_acceptance.py` kiểm chứng sâu hơn về mặt toán học: mặt cầu ngoại tiếp & mặt phẳng trung trực `(α), (β), (γ)` (`det3 != 0`, `R = 2√3`, `V = 32π√3`), **tất cả 03 bài thiết diện trong thư viện** (`chop-thiet-dien-ba-diem`, `lang-tru-tam-giac-thiet-dien`, `lap-phuong-thiet-dien-bat-ky`) về đồng phẳng, nằm trên cạnh (`0 <= t <= 1`), đa giác đơn không tự cắt, winding tuần hoàn và khả kiến pháp tuyến trước/sau khi sửa bước đầu nguồn, cộng đủ **7 lớp input sai** HTTP 422 và race `409 STALE_REVISION_CONFLICT` / `409 EDIT_SUPERSEDED` + cô lập `owner_scope`.
3. **Chạy lại toàn bộ test Backend + Frontend + Seal + Docs Audit trên clean detached candidate.**
4. **Dựng host sống độc lập** (`algosim_acceptance` PostgreSQL 16.6 cổng `55432` + Uvicorn `:8000` + Vite `http://localhost:3001`), thực thi Playwright E2E 2 pha (trước và sau restart `:8000`), quét 7 viewport + tương tác chạm + bàn phím ảo mobile (`390x460`), và quan sát thụ động bằng **REA MCP** trên cổng CDP tạm `:9338`.

---

## 3. Trạng thái Git Graph, Branch, Clean Candidate, Merge-Base và Ownership

- **Bảo vệ `main` & Root Checkout:**
  - `main`: `bb046fa22aceff47abe22aa783aa64fc65caee13`
  - `git merge-base main HEAD`: `bb046fa22aceff47abe22aa783aa64fc65caee13`
  - Quan hệ nhánh `feat/axo-geometry-library-verification`: **`0 behind`, `112 ahead`** (trước commit báo cáo này) — **strictly fast-forwardable lên `main`** không xung đột.
  - `D:/Documents/projects/algo-sim`: giữ nguyên tại `bb046fa22aceff47abe22aa783aa64fc65caee13` (chỉ còn file untracked có sẵn `?? ocr_reconcile.py` của Owner).
- **Lịch sử tích hợp & sửa lỗi từ `194c0cca5` đến clean candidate `27f2c98d2`:**
  - `9220fc635` (`I-1`): Attachment (`ScreenCaptureDialog`, `pdfjs-dist` manifest, resize test, evidence).
  - `bf1ee2a57` (`I-2`): Gỡ bỏ `Classroom`/`Live Session`, thống nhất chuỗi Alembic (`9c4d8e2b7a10 -> f8a2c41d9e05`), đồng bộ `CODE_INDEX.md`.
  - `a9a5d20b1` (`I-3`): Workspace tabs/history single-instance (`WorkspaceTabBar`, history, recovery snapshot).
  - `5d1da3cac .. 1eaa33fbb` (`I-4..I-10`): PostgreSQL 16.6 harness, sửa lỗi treo PIPE `pg_ctl` trên Win32 (`0b58654b0`), oracle C2 (`20cc7137f`, `546126013`, `194c0cca5`), đồng bộ seal và báo cáo release gate.
  - `5b013d16e`: **Sửa tận gốc `IA-RC1`** tại `backend/app/simulation/geometry_functions/step_editor.py` + `test_step_editor_main_release_acceptance.py`.
  - `ebacab9bd`: Đồng bộ `EVALUATION_CANDIDATE.json` và 3 mẫu pilot (`k1`, `r1`, `s2`); toàn bộ bộ test backend chạy xanh trên `ebacab9bd` (`tree_hash = e0ea792d71667f12911fa7b0425bc4761aabdc337ad605491bc06c33137076a4`, `109` files).
  - `2558f9fb5` / `a4022c600`: **Sửa tận gốc `IA-RC2`** tại `frontend/src/components/ConstructionStepEditor.tsx` + test; chạy lại drift/acceptance/postgres backend gates xanh.
  - `2ff70ce45` / `27f2c98d2`: **Sửa tận gốc `IA-RC3`** tại `ConstructionStepEditor.tsx` + `global.css` + test; re-seal sạch tại `27f2c98d2a0f7e9cbe4de8d23837db29e86f0aea` (`measured_system` vẫn giữ nguyên `e0ea792d71667f12911fa7b0425bc4761aabdc337ad605491bc06c33137076a4`, `backend/` hoàn toàn không đổi kể từ `ebacab9bd`).
- **Kiểm tra Ownership:** Mọi thay đổi mã nguồn trong đợt này chỉ giới hạn trong `backend/app/simulation/geometry_functions/step_editor.py`, `backend/tests/geometry/test_step_editor_main_release_acceptance.py`, `frontend/src/components/ConstructionStepEditor.tsx`, `frontend/src/components/construction-step-editor.test.tsx`, `frontend/src/styles/global.css`, và `EVALUATION_CANDIDATE.json`. Không đụng Landing Page, Hybrid AI không được duyệt, hay local model.

---

## 4. Xác minh lại nhóm Integration `I-1..I-10` và 03 Root-Cause Commits mới

| Nhóm / Commit | Nội dung xác minh | Kết quả kiểm chứng độc lập |
|---|---|---|
| `I-1` (`9220fc635`) | Attachment UI & PDF worker build artifact | `vite build` (`129` modules) & `attachment-fidelity.test.tsx` PASS |
| `I-2` (`bf1ee2a57`) | Gỡ Classroom/Live Session, thống nhất Alembic | `CODE_INDEX stale paths: 0`, `alembic check` PASS (`No new upgrade operations detected`) |
| `I-3` (`a9a5d20b1`) | Workspace tab đơn thể, đóng/mở tab, giữ nháp/override | Playwright Phase 1: đóng tab giữa 3 tab và mở lại giữ nguyên bước `1/4`; `workspace-single-instance-navigation` + `workspace-tab-close` PASS |
| `I-4..I-10` (`5d1da3cac..1eaa33fbb`) | PostgreSQL 16.6 Win32 harness & C2 oracle | `pytest -m postgres -v`: `4 passed, 0 skipped`; `12,000` geometry tests `0` failed |
| `IA-RC1` (`5b013d16e` / `ebacab9bd`) | Sửa rò rỉ helper ID `M_AB` vào nhãn mặt phẳng `(α)` khi sửa sang `SB` | `Mặt phẳng (α) qua «Trung điểm của S và B» và vuông góc với SB` (cả pytest & Playwright E2E) |
| `IA-RC2` (`2558f9fb5` / `a4022c600`) | Giữ form Step Editor + nút `Hủy`/`Chạy` hiển thị trọn trong `.dock-scroll` | `1024x768` multiline: `runClipped: false`, `controlsOccludeActions: false` |
| `IA-RC3` (`2ff70ce45` / `27f2c98d2`) | Cắt giảm chiều cao dock/stage khi mở bàn phím ảo mobile & neo theo `visualViewport` | `390x460`: `overflowX: 0`, `taInViewport: true`, `runInViewport: true`, `cancelInViewport: true` |

---

## 5. Kiểm chứng chi tiết Step Editor UI/UX trên `http://localhost:3001`

Kết quả đo trực tiếp từ `results/acceptance-e2e-phase1.json` và `results/rea-mcp-acceptance.json`:

- **Hiển thị mặc định & Hover:** Ở trạng thái bình thường, icon bút chì có `opacity: "0"`; khi hover dòng bước 8 trên `chop-mat-cau-ngoai-tiep`, `opacity: "1"` và **độ lệch chiều cao dòng = `0 px`** (`hoverHeightDeltaPx: 0`) nhờ reserved gutter. Không xuất hiện các nút lạc đề kiểu `"Lưu"` / `"Huấn luyện"`.
- **Trình soạn inline:** Một dòng ban đầu không có thanh cuộn dọc (`textareaSingleLineScrollable: false`), không tràn ngang (`textareaHorizontalOverflow: false`), con trỏ tập trung ngay khi mở. Nút `Chạy` bị disable khi chỉ có khoảng trắng (`runDisabledOnEmpty: true`, `httpSent: false`).
- **Tương tác thành công Bước 8 trên `chop-mat-cau-ngoai-tiep`:** Nhập `"Dựng mặt phẳng trung trực (α) của cạnh SB"` → `POST /api/simulation/steps/edit` trả HTTP `200`, counter chuyển đúng sang `Bước 8/17` (`steps` đồng bộ cùng Scene3D), mảng dependency tính lại gồm `["truc_day", "I", "doan_OI", "doan_MI", "doan_IS", "doan_IA", "cau_ngoai_tiep", "R", "V_cau"]`.
- **Cô lập cuộn Dock (`dockScrollIsolated: true`):** Cuộn wheel bên trong `#dock-scroll` cập nhật `scrollTop` độc lập mà không làm giật/cuộn canvas 3D hoặc document ngoài.

---

## 6. Kiểm chứng tái dựng hình học, Dependency Cascade & Bất biến Toán học / Scene3D

Xác minh cả bằng chứng minh biểu diễn chính xác (`test_step_editor_main_release_acceptance.py`) lẫn phản hồi runtime trực tiếp trên host PostgreSQL:

1. **Bài 11 — Mặt cầu ngoại tiếp & 3 mặt phẳng trung trực (`chop-mat-cau-ngoai-tiep`):**
   - Trước khi sửa Bước 8: 3 mặt phẳng trung trực `(α)` của `AB`, `(β)` của `AD`, `(γ)` của `AS` hợp thành ma trận pháp tuyến có `det3 != 0` ⇒ giao điểm tâm mặt cầu `I = (2, 2, 2)`, bán kính chính xác `R = 2√3` (`R² = 12`), thể tích `V = 32π√3`.
   - Sau khi sửa Bước 8 thành `"Dựng mặt phẳng trung trực (α) của cạnh SB"`: trung điểm phụ trợ chuyển từ `M_AB = (2,0,0)` sang `M_SB = (2,0,2)`, vector pháp tuyến đổi thành `[4, 0, -4]`, nhãn diễn giải đổi sạch thành `"Mặt phẳng (α) qua «Trung điểm của S và B» và vuông góc với SB"` (`leakedRawHelper: false`), đồng thời `I` vẫn là `(2, 2, 2)` (`R² = 12`) trên mặt cầu ngoại tiếp hình chóp `S.ABCD`.
2. **Toàn bộ 03 bài thiết diện thư viện (`chop-thiet-dien-ba-diem`, `lang-tru-tam-giac-thiet-dien`, `lap-phuong-thiet-dien-bat-ky`):**
   - Trước và sau khi sửa các bước định vị điểm đầu nguồn (ví dụ `SM/SA = 1/4`, `3/4`, `CP/CC' = 1/3`), kiểm chứng từng đỉnh thiết diện đều nằm đúng trên cạnh tương ứng với tham số đoạn `0 <= t <= 1`, toàn bộ đỉnh thiết diện thỏa phương trình đồng phẳng với sai số chính xác bằng `0`, đa giác 2D đơn không tự cắt, winding có thứ tự tuần hoàn chặt, và thứ tự chiều sâu theo pháp tuyến hướng ra ngoài hợp lệ cho dựng hình 3D.
   - Trên UI `chop-thiet-dien-ba-diem`, chuỗi sửa liên tiếp `SM/SA = 1/4 → 3/4 → 1/4` cập nhật chính xác tọa độ `M` thành `["0", "0", "9/2"]` và giữ nguyên qua `F5` reload lẫn restart backend `:8000`.

---

## 7. Negative Test Matrix, Rollback, Concurrency & Cross-Owner Isolation

Kết hợp giữa kiểm chứng đơn vị/API (`test_section3b_and_3c_invalid_classes_and_race_guards`) và Playwright trên host (`results/acceptance-e2e-phase1.json`):

| Hạng mục kiểm tra | Trường hợp thử nghiệm | HTTP / Mã lỗi | Bảo toàn trạng thái |
|---|---|---|---|
| **Rỗng / khoảng trắng** | `"   \n  "` tại Bước 8 | Không gửi HTTP (`Chạy` disabled) | Draft giữ nguyên, Scene3D sạch |
| **Điểm chưa tồn tại** | `"Dựng mặt phẳng trung trực (P) của cạnh SZ."` | `422 MISSING_DEPENDENCY` | Rollback DB, hiển thị thông báo tiếng Việt, draft & Scene3D cũ nguyên vẹn |
| **3 điểm thẳng hàng** | `"Dựng mặt phẳng đi qua 3 điểm A, O, C."` | `422 COLLINEAR_POINTS` | Rollback DB, draft & Scene3D cũ nguyên vẹn |
| **Đoạn/đối tượng chưa xác định** | `"Lấy trung điểm K của cạnh XZ."` | `422 MISSING_DEPENDENCY` | Rollback DB, draft & Scene3D cũ nguyên vẹn |
| **Ngoài phạm vi** | `"Vẽ đường xoắn ốc vàng quanh hình chóp."` | `422 UNSUPPORTED_STEP_SYNTAX` | Rollback DB, draft & Scene3D cũ nguyên vẹn |
| **Văn bản vô nghĩa** | `"asdf qwer zxcv 12345"` | `422 UNSUPPORTED_STEP_SYNTAX` | Rollback DB, draft & Scene3D cũ nguyên vẹn |
| **Chia đoạn sai tỉ số âm / >1 & Tự tham chiếu vòng** | Tỉ số âm / tỉ số > 1 / step tham chiếu chính kết quả của nó | `422` Fail-closed (`test_step_editor_main_release_acceptance.py`) | Không commit bản ghi hỏng |
| **Fake 200 chưa kiểm chứng & Đứt mạng** | Payload trả `UNVERIFIED` / `socket hang up` | Client rollback (`UNVERIFIED_REBUILD_REJECTED` / `network_error`) | Draft & Scene3D trước đó nguyên vẹn |
| **Phiên bản cũ (Stale Revision)** | Gửi `expected_committed_version: 0` sau khi đã commit v1..v3 | `409 STALE_REVISION_CONFLICT` | Chặn ghi đè bản mới |
| **Edit bị thay thế (`EDIT_SUPERSEDED`)** | Tranh chấp chuỗi chỉnh sửa cùng session | `409 EDIT_SUPERSEDED` | Bảo toàn revision hợp lệ sau cùng |
| **Cô lập chủ sở hữu (`Cross-Owner Isolation`)** | Caller khác `X-Axo-Client-Session` đọc `/state` hoặc `/feedback/status` | Khác `owner_scope` ⇒ `found: false` / `total_records: 0` | Không rò rỉ session hoặc feedback của người khác |

---

## 8. Kiểm chứng PostgreSQL 16.6, Alembic Migration Chain, Restart Persistence & Bảo mật Redaction

Từ `results/postgres-acceptance-audit.json` và đầu ra lệnh `alembic` trực tiếp trên database `algosim_acceptance` (`PostgreSQL 16.6`, cổng `55432`):

- **Chuỗi Migration Alembic hợp nhất:**
  - `e437149641fa -> 9c4d8e2b7a10` (`add step edit tables`) `-> f8a2c41d9e05 (head)` (`remove classroom and live session tables`).
  - Lệnh `alembic check` trên `algosim_acceptance` xác nhận **`No new upgrade operations detected`** (`EXIT 0`).
- **Ràng buộc & Chỉ mục thực tế trên PostgreSQL 16.6:**
  - `step_edit_sessions`: khóa chính `step_edit_sessions_pkey`, ràng buộc duy nhất `uq_step_edit_session_owner_sid` trên `(owner_scope, session_id)`.
  - `step_edit_revisions`: khóa chính `step_edit_revisions_pkey`, chỉ mục duy nhất `ix_step_edit_revisions_revision_id`, ràng buộc duy nhất `uq_step_edit_revision_version` trên `(owner_scope, session_id, version_number)`.
  - `step_edit_feedback`: khóa chính `step_edit_feedback_pkey`, chỉ mục duy nhất `ix_step_edit_feedback_feedback_id` và các chỉ mục `session_id`, `revision_id`, `owner_scope`, `dataset_eligibility`, `user_acceptance_status`, `problem_group_key`.
- **Số liệu ghi nhận trực tiếp sau Playwright Phase 1 & Phase 2 (1 lần chạy sạch sau truncate):**
  - Tổng phiên: **`3` sessions** (`chop-mat-cau-ngoai-tiep`, `chop-thiet-dien-ba-diem`, `lang-tru-tam-giac-thiet-dien`).
  - Tổng revision: **`11` revisions** = **`6 COMMITTED`** (`PASSED` — `1` của `chop-mat-cau-ngoai-tiep`, `4` của `chop-thiet-dien-ba-diem`, `1` của `lang-tru-tam-giac-thiet-dien`) + **`5 ROLLED_BACK`** (`FAILED`: `1 COLLINEAR_POINTS`, `2 MISSING_DEPENDENCY`, `2 UNSUPPORTED_STEP_SYNTAX`).
  - Tổng feedback: **`11` rows** = **`6 GEOMETRY_VERIFIED`** + **`5 REJECTED`** (toàn bộ `dataset_eligibility = INELIGIBLE`, `schema_version = axo-step-feedback/1`, **`11/11` đầy đủ 7 trường dữ liệu JSON**).
- **Khôi phục qua Restart Backend (`:8000`):** Kill Uvicorn cũ và khởi động tiến trình mới (PID `6728`) nối vào `algosim_acceptance`, mở lại trình duyệt mới bằng Playwright Phase 2 ⇒ `GET /api/simulation/sessions/.../state` trả `200`, `found: true`, `committedVersion: 4`, `M = ["0", "0", "9/2"]`, và UI Step 6 hiển thị đúng `"Lấy điểm M thuộc SA sao cho SM/SA = 1/4"` (`images/acceptance-1920-post-restart.png`).
- **Kiểm toán Redaction:** Mọi file JSON và báo cáo đều không chứa DSN PostgreSQL, mật khẩu, cookie, hay token `owner_scope` / `session_id` thô (đã kiểm bằng regex scan `0` vi phạm).

---

## 9. Responsive Matrix, Multiline Auto-Grow, Bàn phím ảo Mobile, Touch & Accessibility

Đo trên trình duyệt Chromium thực qua `run-independent-acceptance-phase1.mjs` và REA MCP:

| Viewport | `overflowX` | Canvas W × H (px) | `textarea` Height / ScrollY / OverflowX | `Hủy` / `Chạy` Clipped hoặc Bị che | Điều hướng khả dụng |
|---|---:|---:|---:|---:|---|
| `1920x1080` | `0` | `1289 × 1042` | `85px` / `hidden` / `false` | `false` / `false` | `true` |
| `1440x900` | `0` | `809 × 862` | `85px` / `hidden` / `false` | `false` / `false` | `true` |
| `1366x768` | `0` | `735 × 730` | `85px` / `hidden` / `false` | `false` / `false` | `true` |
| `1024x768` *(từng lỗi `IA-RC2`, đã sửa)* | `0` | `704 × 730` | `85px` / `hidden` / `false` | `false` / `false` | `true` |
| `768x1024` | `0` | `472 × 986` | `85px` / `hidden` / `false` | `false` / `false` | `true` |
| `390x844` | `0` | `390 × 444` | `85px` / `hidden` / `false` | `false` / `false` | `true` |
| `320x568` | `0` | `320 × 293` | `85px` / `hidden` / `false` | `false` / `false` | `true` |

- **Touch `390x844` + Thu nhỏ bàn phím ảo `390x460` *(từng lỗi `IA-RC3`, đã sửa)*:** Chạm kích hoạt bước 8 làm hiện icon bút chì (`pencilVisibleOnTouchActive: true`); khi co viewport xuống `390x460` không cần gọi scroll cưỡng bức từ test, cả ô nhập lẫn hai nút `Hủy`/`Chạy` tự cuộn lọt hoàn toàn trong màn hình (`overflowX: 0`, `taInViewport: true`, `runInViewport: true`, `cancelInViewport: true` — kiểm chứng bằng mắt qua `images/acceptance-touch-390x460-vkb.png`).
- **Accessibility & REA MCP (`inspect_web_page`):** `dom_node_count: 783`, `accessibility_node_count: 445`, `console_error_count: 0`, nút bút chì có `aria-label`, trường nhập có `aria-label`, trạng thái chạy có vùng `aria-live="polite"`, thông báo lỗi có `role="alert"`. Phím `Escape` khôi phục focus bàn phím; `Ctrl/Cmd+Enter` nộp hợp lệ.

---

## 10. Tổng hợp kết quả kiểm thử tự động trên Clean Detached Candidate

| Hạng mục kiểm tra | Commit chạy | Lệnh thực thi | Kết quả quan sát thực tế | Thời gian |
|---|---|---|---|---:|
| Candidate Seal | `27f2c98d2` | `python scripts/freeze_evaluation_candidate.py --verify` | `PASS` (`109` files, `e0ea792d71667f12…`) | — |
| Docs Info Architecture | `27f2c98d2` | `python scripts/audit_docs_information_architecture.py` | `PASS` (`0` broken links, `0` stale CODE_INDEX, `0` leaks) | — |
| Frontend TypeScript | `27f2c98d2` | `node ./node_modules/typescript/bin/tsc -b` | `PASS` (`EXIT 0`) | — |
| Frontend Vite Build | `27f2c98d2` | `node ./node_modules/vite/bin/vite.js build` | `PASS` (`129 modules transformed`, `EXIT 0`) | `4.74s` |
| Frontend Vitest | `27f2c98d2` | `node ./node_modules/vitest/vitest.mjs run` | **`192/192` files, `2,274/2,274` tests PASS** | `102.23s` |
| Backend Geometry | `ebacab9bd` *(backend identical at `27f2c98d2`)* | `pytest tests/geometry -rsx -q` | **`12,000 passed`, `6 skipped`, `3 deselected`, `9 xfailed`, `0 failed`** | `338.80s` |
| Backend Semantic Program | `ebacab9bd` *(backend identical at `27f2c98d2`)* | `pytest tests/semantic_program -rsx -q` | **`1,192 passed`, `1 skipped`, `0 failed`** | `46.57s` |
| Backend Other Modules | `ebacab9bd` *(backend identical at `27f2c98d2`)* | `pytest tests --ignore=tests/geometry --ignore=tests/semantic_program -rsx -q` | **`793 passed`, `2 deselected`, `0 failed`** | `93.33s` |
| Migration Drift & Step Acceptance Re-Check | `a4022c600` *(backend identical at `27f2c98d2`)* | `pytest tests/test_migration_drift.py tests/geometry/test_step_editor_main_release_acceptance.py -v` | **`6 passed`, `0 failed`** | `7.43s` |
| PostgreSQL 16.6 Integration | `a4022c600` *(backend identical at `27f2c98d2`)* | `pytest -m postgres -v` | **`4 passed`, `14,002 deselected`, `0 skipped`** | `48.69s` |
| Demo Replay & Crash Audit | `ebacab9bd` | `replay_demo_cases.py` & `audit_demo_crash_surface.py` | `5/5 + 1/1` & `6/6` (`0` x `500`) | — |

*(Xác minh bằng `git diff --name-only ebacab9bd..27f2c98d2`: chỉ có 4 file thay đổi thuộc Frontend & Seal — `ConstructionStepEditor.tsx`, `construction-step-editor.test.tsx`, `global.css`, `EVALUATION_CANDIDATE.json`; 0 byte thay đổi trong `backend/` giữa `ebacab9bd`, `a4022c600` và `27f2c98d2`.)*

---

## 11. Danh sách đầy đủ toàn bộ `XFAIL` (9), `SKIPPED` (7) và `DESELECTED` (5) — Chứng minh không ảnh hưởng Step Editor

Không có bất kỳ `XFAIL`, `SKIPPED` hay `DESELECTED` nào nằm trong `frontend/**` (`2,274/2,274` pass hoàn toàn) hay trong bộ kiểm định Step Editor:

### A. `XFAIL` (`9` trong `tests/geometry`, toàn bộ là strict xfail thuộc biên NLU Hybrid `/4` / benchmark cũ)
1. `tests/geometry/test_generalized_goal_entry.py::test_length_goal_refusal[unread-second-ask]` — Khác mã từ chối `REQUEST_NOT_ANSWERED` vs `QUESTION_CONTEXT_UNSUPPORTED` ở ranh giới NLU Hybrid `/4`.
2. `tests/geometry/test_generalized_goal_entry.py::test_length_goal_refusal[contradictory-length]` — Khác mã `INCONSISTENT_FACTS` vs `INCONSISTENT_CONSTRAINTS` ở ranh giới NLU Hybrid `/4`.
3. `tests/geometry/test_hybrid_compiler_benchmark.py::test_case_outcome[B27-facts]` — `GAP B27`: toán hạng dẫn xuất chưa đặt tên trong benchmark Typed Facts v1 cũ.
4. `tests/geometry/test_hybrid_compiler_benchmark.py::test_case_outcome[B27-pipeline]` — `GAP B27` ở pha pipeline Typed Facts v1 cũ.
5. `tests/geometry/test_hybrid_compiler_benchmark.py::test_case_outcome[B28-facts]` — `GAP B28`: phân biệt `'tâm'` vs `'trọng tâm'` trong benchmark Typed Facts v1 cũ.
6. `tests/geometry/test_hybrid_compiler_benchmark.py::test_case_outcome[B28-pipeline]` — `GAP B28` ở pha pipeline Typed Facts v1 cũ.
7. `tests/geometry/test_hybrid_simulation_capability_probes.py::test_centre_label_exhaustion_is_a_coded_outcome` — `ISSUE-ARCH-ENGINE-CENTRE-LABEL-EXHAUSTION`: bài probe nhân tạo làm cạn hơn 26 nhãn tâm.
8. `tests/geometry/test_premise_source_coverage.py::test_goal_fact_quote_does_not_cover_a_hypothesis[...]` — Quy tắc có giới hạn của Source Gate với mệnh đề `'và'` (vẫn fail-closed an toàn).
9. `tests/geometry/test_source_grounding_reliability.py::test_targeted_case_meets_its_preregistered_label[E05-unsupported-second-quantity]` — Khác nhãn mã từ chối `NOT_ASKED_IN_SOURCE` trên ca nghiên cứu E05.

### B. `SKIPPED` (`6` trong `tests/geometry` + `1` trong `tests/semantic_program` = `7`)
1–6. `tests/geometry/test_unified_solid_scope.py:186` (3 ca `A3-DEV-02`, `A3-DEV-09`, `demo1-pyramid-derived-section` × 2 parameterization = `6`): ma trận bỏ qua vì các fixture này không có mục tiêu `residual_volume`.
7. `tests/semantic_program/test_scalar_obligations.py:95` (`1`): `thiếu 'term' mặc định về identity — đã có test riêng`.

### C. `DESELECTED` (`3` trong `tests/geometry` + `2` trong `tests/` = `5`)
1. `tests/geometry/test_evidence_identity_reconciliation.py::test_raw_response_identity_reproduced` (`@pytest.mark.external_evidence`) — đòi hỏi kho archive raw API nội bộ nằm ngoài repo Git công khai.
2–5. Bốn test `@pytest.mark.postgres` (`test_step_edit_postgres_migration_handoff_live_container`, `test_postgres_real_step_editor_end_to_end_persistence_restart_and_rollback`, `test_axo_migrations_and_history_api_on_postgres`, `test_postgres_migrate_persist_reconnect`) bị loại trừ khi chạy mặc định nhưng **đều đã chạy riêng bằng `pytest -m postgres -v` và ĐẠT `4 passed, 0 skipped` trên PostgreSQL 16.6 thật**.

---

## 12. Các lỗi phát hiện trong đợt nghiệm thu độc lập, Nguyên nhân gốc & Sửa chữa TDD

### 1. `IA-RC1` — Rò rỉ raw helper ID `M_AB` vào nhãn mặt phẳng khi sửa sang cạnh khác (`5b013d16e`)
- **Hiện tượng:** Sửa Bước 8 (`mp_tt_AB`, `absorbed_ids=["M_AB"]`) của `chop-mat-cau-ngoai-tiep` thành `"Dựng mặt phẳng trung trực (α) của cạnh SB"` dựng đúng hình học vuông góc với `SB`, nhưng chuỗi hiển thị Step 8 & giải thích lại ghi `"Mặt phẳng (α) qua M_AB và vuông góc với SB"`.
- **Nguyên nhân gốc (`backend/app/simulation/geometry_functions/step_editor.py`):** Khi đối tượng trung điểm được tạo mà người dùng không đặt tên đỉnh riêng (`notation = None`), `step_editor` tái sử dụng id nội bộ `M_AB` và đặt `mid_helper["display_label"] = None`, khiến phần tạo nhãn mặt phẳng tại `perpendicular_bisector_plane`, `plane_perpendicular_to_line` và `plane_parallel_to_plane` fallback trực tiếp về `pt_id` thô `"M_AB"`.
- **Sửa TDD & Xác minh:** Viết test RED `test_ia_rc1_unnamed_helper_never_leaks_into_plane_labels` (thất bại vì `+ Mặt phẳng (α) qua M_AB...`), thêm helper `_obj_display_ref(oid)` và gán `display_label = ab_phrase` ⇒ chuyển GREEN, re-verify cả trong Playwright Phase 1 (`leakedRawHelper: false`, nhãn đúng `"Mặt phẳng (α) qua «Trung điểm của S và B» và vuông góc với SB"`).

### 2. `IA-RC2` — Ở viewport `1024x768`, nút `Hủy` / `Chạy` bị đẩy ra ngoài đáy `.dock-scroll` khi nhập nhiều dòng (`2558f9fb5`)
- **Hiện tượng:** Khi mở Step 8 (nằm gần đáy `.dock-scroll`) trên màn hình `1024x768` và nhập đoạn nhiều dòng, hai nút `Hủy` / `Chạy` trôi xuống dưới mép dưới `.dock-scroll` và bị che khỏi vùng nhìn (`elementFromPoint` không chạm nút).
- **Nguyên nhân gốc (`frontend/src/components/ConstructionStepEditor.tsx`):** `InlineConstructionStepEditor` gọi `el.focus({ preventScroll: true })`, còn `syncStepTextareaHeight` khôi phục `scrollHost.scrollTop = savedHostScrollTop` sau khi đo chiều cao, nên khi form giãn xuống hoặc hiện `.step-edit-error`, vùng cuộn không tự đưa trọn vẹn form vào vùng thấy.
- **Sửa TDD & Xác minh:** Viết unit test RED cho `ensureStepEditorFormVisible`, bổ sung `formRef` + `ensureStepEditorFormVisible` chạy trong `useIsomorphicLayoutEffect` (`[stepIndex]`, `[draft]`, `[errorText]`) và `ResizeObserver` ⇒ chuyển GREEN và `acceptance-vp-1024x768.png` pass sạch (`controlsOccludeActions: false`).

### 3. `IA-RC3` — Khi co chiều cao giả lập bàn phím ảo mobile (`390x460`), nút `Hủy` / `Chạy` bị cắt ~7.8px ở đáy viewport (`2ff70ce45`)
- **Hiện tượng:** Tại `390x460` trên thiết bị chạm, `.stage-3d` giữ `min-height: 230px` kết hợp `.axo-workspace-v62 { min-height: 480px; }` làm đáy `.study-dock` và `.dock-scroll` trồi xuống `y = 480` (vượt quá `vh = 460` hết 20px), trong khi `ensureStepEditorFormVisible` mới chỉ neo theo `hostRect.bottom` (`480`).
- **Nguyên nhân gốc (`global.css` + `ConstructionStepEditor.tsx`):** Quy tắc `@media (max-width: 680px) and (max-height: 520px)` chưa có để hạ `min-height` của `.axo-workspace-v62` và `.stage-3d`, đồng thời `ensureStepEditorFormVisible` chưa giao vùng nhìn của `.dock-scroll` với `window.visualViewport` / `window.innerHeight`.
- **Sửa TDD & Xác minh:** Thêm test RED `IA-RC3`, cập nhật `ensureStepEditorFormVisible` cắt giao theo `visualViewport` / `innerHeight` + lắng nghe `window` & `visualViewport` `resize`, và thêm `@media (max-width: 680px) and (max-height: 520px)` trong `global.css` ⇒ Vitest `2,274/2,274` pass và `390x460` VKB pass thực tế (`images/acceptance-touch-390x460-vkb.png`).

---

## 13. Trạng thái Model 2 (`MODEL_STATUS: MODEL_NOT_TRAINED`) & Cấu trúc dữ liệu Feedback

- **Trạng thái công khai API:** `GET /api/simulation/feedback/status` (có header sở hữu `X-Axo-Client-Session` của phiên test) trả về:
  - `schema_version`: `"axo-step-feedback/1"`
  - `dataset_schema_version`: `"axo-step-feedback-dataset/1"`
  - **`model_status`: `"MODEL_NOT_TRAINED"`**
  - **`model_trained`: `false`**
  - `total_records`: `11` (`GEOMETRY_VERIFIED: 6`, `REJECTED: 5`, `TRAINING_ELIGIBLE: 0`, `quarantined_count: 0`)
- **Tính đầy đủ của dataset chuẩn bị cho tương lai:** Truy vấn bảng `step_edit_feedback` trên `algosim_acceptance` cho thấy **11/11 bản ghi** chứa đầy đủ tất cả 7 cột JSON cốt lõi (`original_intent_json`, `corrected_intent_json`, `geometry_context_json`, `dependency_context_json`, `registry_operations_json`, `validation_result_json`, `execution_result_json`) và toàn bộ đều mang trạng thái `dataset_eligibility = INELIGIBLE` an toàn.

---

## 14. Danh mục Artifact, Ảnh chụp màn hình & Bằng chứng JSON

Thư mục run repo: `docs/evaluation/geometry/runs/step-editor-independent-acceptance-main-prep/`

- **Báo cáo & Metadata:**
  - `AXO-STEP-EDITOR-INDEPENDENT-ACCEPTANCE-REPORT.md` & `report.md`
  - `run.json`
- **Bằng chứng JSON (`results/`):**
  - `results/quality-gates-summary.json`
  - `results/acceptance-e2e-phase1.json`
  - `results/acceptance-e2e-phase2.json`
  - `results/postgres-acceptance-audit.json` *(strictly redacted)*
  - `results/rea-mcp-acceptance.json` *(strictly redacted; `ev_801a51ae...`, `ev_15267ec8...`, `ev_cf59d63b...`, SHA-256 `64513149a1cef8ea1d37aaf9bdbd5994a1507dbdacd32044807ac075fe3a4db4`)*
- **Ảnh chụp màn hình (`images/`):**
  - Chức năng & Cascade: `acceptance-1920-3a-s11-valid-sb.png`, `acceptance-1920-3b-invalid-422-sz.png`, `acceptance-1920-3c-s1-f5.png`, `acceptance-1920-3c-prism.png`, `acceptance-1920-post-restart.png`
  - 7 Viewport & VKB: `acceptance-vp-1920x1080.png`, `acceptance-vp-1440x900.png`, `acceptance-vp-1366x768.png`, `acceptance-vp-1024x768.png`, `acceptance-vp-768x1024.png`, `acceptance-vp-390x844.png`, `acceptance-vp-320x568.png`, `acceptance-touch-390x460-vkb.png`
  - REA MCP: `acceptance-rea-mcp.png`

---

## 15. Đánh giá rủi ro tồn đọng (`LOW` — Không chặn phát hành)

| Hạng mục | Mức rủi ro | Đánh giá & Biện pháp kiểm soát |
|---|---|---|
| Cú pháp toán học ngoài phạm vi thư viện deterministic (vd đường cong xoắn) | Thấp | Chủ động từ chối `422 UNSUPPORTED_STEP_SYNTAX`, bảo toàn nháp và Scene3D cũ — đúng thiết kế fail-closed. |
| Model 2 chưa huấn luyện (`MODEL_NOT_TRAINED`) | Thấp (theo thiết kế) | Hệ thống không suy đoán bằng model chưa kiểm chứng; dữ liệu đã tách riêng với `dataset_eligibility = INELIGIBLE`. |
| Môi trường dev Windows có junction `node_modules` ngoài Git ở `.superpowers/` | Không ảnh hưởng sản phẩm | Chỉ phục vụ chạy Vitest/Vite trên worktree detached sạch; không nằm trong cây Git theo dõi. |

---

## 16. Hướng dẫn từng bước để Owner tự mở `http://localhost:3001` kiểm tra trực tiếp

Ba tiến trình dịch vụ sạch từ release candidate vẫn đang chạy sẵn trên localhost:
- **Frontend (Vite):** `http://localhost:3001` (nên mở `http://localhost:3001/app` hoặc `http://localhost:3001/simulation/chop-mat-cau-ngoai-tiep`)
- **Backend (FastAPI + Uvicorn):** `http://127.0.0.1:8000` (`/api/health` kết nối PostgreSQL thật)
- **PostgreSQL 16.6 (`algosim_acceptance`):** `127.0.0.1:55432`

**Kịch bản thử nhanh cho Owner (2–3 phút):**
1. Mở `http://localhost:3001/simulation/chop-mat-cau-ngoai-tiep` trên trình duyệt.
2. Rê chuột vào **Bước 8** (`Dựng mặt phẳng trung trực (α) của cạnh AB`) → bấm biểu tượng **bút chì**.
3. Thử sửa thành `"Dựng mặt phẳng trung trực (α) của cạnh SB"` → nhấn `Chạy` (hoặc `Ctrl+Enter`): xác nhận mặt phẳng `(α)` dựng lại vuông góc với `SB`, nhãn diễn giải không rò rỉ `M_AB`, mặt cầu `I` giữ đúng bán kính ngoại tiếp `S.ABCD`.
4. Thử nhập sai như `"Dựng mặt phẳng trung trực (P) của cạnh SZ."` → bấm `Chạy`: xác nhận báo lỗi tiếng Việt màu đỏ tại bước đang sửa, giữ nguyên văn bản để sửa tiếp và Scene3D phía trước không bị vỡ.
5. Mở bài `"Thiết diện hình chóp S.ABCD cắt bởi mặt phẳng (MNP)"` (`/simulation/chop-thiet-dien-ba-diem`), sửa **Bước 6** thành `"Lấy điểm M thuộc SA sao cho SM/SA = 1/3"`, nhấn `Chạy`, rồi bấm **`F5`** tải lại trang để kiểm chứng phục hồi từ PostgreSQL.
6. Kéo hẹp cửa sổ xuống khoảng `390x460` (hoặc bật DevTools Device Mode) để xác nhận vùng soạn thảo + `Hủy`/`Chạy` vẫn nằm gọn trong màn hình.

---

## 17. Quy trình đề xuất Merge `feat/axo-geometry-library-verification` lên `main` và Push an toàn (Chờ Owner phê duyệt)

Sau khi Owner hoàn tất nghiệm thu trên `http://localhost:3001` và **cho phép rõ ràng**, thực hiện theo thứ tự an toàn sau từ repo chính `D:\Documents\projects\algo-sim`:

```powershell
# 1. Bảo đảm đang ở main mới nhất, không đụng file untracked cá nhân (ocr_reconcile.py)
Set-Location "D:\Documents\projects\algo-sim"
git switch main

# 2. Merge fast-forward (vì feat/axo-geometry-library-verification đang 0 behind, fast-forwardable hoàn toàn)
git merge --ff-only feat/axo-geometry-library-verification

# 3. Kiểm tra lại seal và docs audit ngay trên main trước khi push
Set-Location "D:\Documents\projects\algo-sim\backend"
& ".\.venv\Scripts\python.exe" scripts/freeze_evaluation_candidate.py --verify
& ".\.venv\Scripts\python.exe" scripts/audit_docs_information_architecture.py

# 4. Push main lên remote khi kiểm tra xong
Set-Location "D:\Documents\projects\algo-sim"
git push origin main
```

---

## 18. Cam kết an toàn Working Tree & Không tự ý Merge / Push

- Không sửa đổi bất kỳ file nào đang được theo dõi trong `D:/Documents/projects/algo-sim`.
- Mọi thao tác stage đều thực hiện allowlist tường minh từng đường dẫn (`git add <file>`), không dùng `git add .` hay `git add -A`.
- Kết thúc phiên kiểm chứng, cả `D:/Documents/projects/axo-geometry-library` lẫn `D:/Documents/projects/algo-sim/.superpowers/worktrees/step-editor-release-candidate` đều sạch `git status --porcelain`.
- **Không** thực hiện `git merge` vào `main` và **không** thực hiện `git push` trong phiên này theo đúng cổng phê duyệt của Owner.
