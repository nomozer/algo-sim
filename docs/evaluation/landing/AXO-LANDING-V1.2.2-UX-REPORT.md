# AXO Landing V1.2.2 — UX & Navigation Cleanup Report

**Ngày hoàn thành:** 2026-11-15  
**Nhánh làm việc:** `feat/axo-geometry-library-verification`  
**Worktree Frontend/Repo:** `D:\Documents\projects\axo-geometry-library`  
**Mốc nền trước đó:** [`AXO-LANDING-V1.2.1-REPORT.md`](./AXO-LANDING-V1.2.1-REPORT.md) (`916fa589b`)  
**Owner Approval:** `PENDING_OWNER_REVIEW`

---

## 1. Tóm tắt điều hành & Cô lập phạm vi (`VERIFIED`)

Pha A (**AXO Landing V1.2.2**) tinh gọn luồng xác thực, điều hướng, chuẩn hóa CTA, tách biệt nhận thức toán học giữa dữ kiện đề bài và kết quả suy luận trong Storytelling/Demo, và chỉnh sửa nội dung Final CTA/Footer trên trang `/gioi-thieu` (`/`), không thêm popup trung gian và không phá vỡ đồng bộ phiên Workspace.

**Cô lập phạm vi Git (`Scope Isolation`):** Commit Pha A (`fix(axo): streamline landing authentication and navigation`) chỉ stage đúng 15 tệp của Pha A qua `git add <file>` tường minh; toàn bộ các thay đổi chưa commit của phiên song song trong `backend/**`, `frontend/package*.json`, `frontend/index.html`, `frontend/public/**`, `AuthGate.tsx`, `AxoErrorExperience.tsx`, `HomeView.tsx`, `SimulationWorkspace.tsx`, `TopNav.tsx`, `frontend/src/state/*`, `docs/EVIDENCE_INDEX.md` và các tệp ngoài phạm vi Landing đều được giữ nguyên vẹn.

---

## 2. Nguyên nhân gốc & Thay đổi kỹ thuật đã triển khai (`VERIFIED`)

| Nhóm vấn đề | Nguyên nhân gốc ở V1.2.1 | Giải pháp V1.2.2 đã triển khai | Tệp liên quan |
|---|---|---|---|
| **Đăng nhập thừa ở Guest Header & Mobile Drawer** | Header Guest hiển thị nút `#btn-landing-header-login` (`Đăng nhập`) cạnh `Bắt đầu`; Mobile Drawer Guest lặp lại `#btn-landing-drawer-login` (`Đăng nhập tài khoản`). | Gỡ bỏ hoàn toàn `#btn-landing-header-login` và `#btn-landing-drawer-login` ở trạng thái Guest. Mobile Drawer Guest giữ đúng 5 mục: `Giới thiệu`, `Cách hoạt động`, `Trải nghiệm`, `Thư viện mẫu`, `Bắt đầu dựng hình`; khi mở drawer, ẩn CTA Header để tránh hai nút primary cạnh nhau; bổ sung `#btn-landing-drawer-logout` cho người dùng đã đăng nhập; thêm animation mở drawer mượt và tắt dưới `prefers-reduced-motion`. | `frontend/src/components/landing/LandingHeader.tsx`, `frontend/src/components/landing/landing.css` |
| **Intended Destination & Khôi phục bản nháp qua cold reload** | Người dùng Guest hết lượt thử hoặc bị yêu cầu xác thực đi qua `/login` không nhớ đích chính xác; khi reload ở `/gioi-thieu` rồi quay lại `/app`, `store.problemText` khởi tạo rỗng do `algosim.draft.v1` chưa được nạp lại nếu không có processing record. | Thêm hợp đồng `IntendedDestination` (`axo_intended_destination_v1`, TTL 30 phút, `consumeIntendedDestination` 1 lần, `applyIntendedDestination`) và `restoreSavedDraftIfEmpty()` đọc `historyStore.readDraftText()` (`algosim.draft.v1`) khi vào `home` với `problemText` rỗng. `App.tsx` theo dõi `lastNonAuthDestRef` (`library`/`sample`/`workspace`/`home`), tự tiêu thụ đích khi chuyển từ `null -> AuthUser`, dọn đích khi logout và rời trang bảo vệ `admin`/`account`. | `frontend/src/components/landing/landing-geometry-data.ts`, `frontend/src/App.tsx` |
| **Chuẩn hóa CTA & Closing Band / Footer** | `LandingView.tsx` chưa subscribe trực tiếp `useAuthStore((s) => s.user)` cho `#btn-landing-hero-start` và `#btn-landing-final-start`; Closing Band dùng câu từ thiên về CAD (`tệp CAD`, `mô phỏng kiểm chứng`); Footer lặp lại nút `Vào ứng dụng`. | Subscribe `useAuthStore((s) => s.user)` để thống nhất nhãn Guest (`Bắt đầu dựng hình` ở Hero/Final CTA/Drawer, `Bắt đầu` ở Header) và Authenticated (`Vào ứng dụng` ở cả 4 vị trí); cập nhật tiêu đề Closing CTA thành `"Từ đề toán đến mô hình hình học không gian."` cùng mô tả `.axo-sp-final-desc` trung thực theo sản phẩm; loại bỏ nút CTA dư thừa trong `#landing-footer`. | `frontend/src/components/LandingView.tsx` |
| **Lẫn dữ kiện đề bài và kết quả cuối ở các chặng đầu** | Chặng 0/1/2 của SVG Explainer lộ sẵn đáp án cuối dưới dạng badge mờ; mô tả Stage 02 ghi không khớp (`Mặt đáy mở rộng...`); Demo Tương tác hiển thị sẵn `S(MENPF) = 6√6` & `V(S.ABCD) = 32` ở Bước 01–03. | Thay thế chip mờ bằng `STORY_STAGE_FACTS` phân tách theo từng chặng (`Stage 0`: giả thiết `ABC.A′B′C′ (a = 4)` & `M, N, P`; `Stage 1`: `AA′, BB′, CC′ ⊥ (ABC)` & nét khuất; `Stage 2`: `(MNP)` cắt `BB′` tại `Q`; `Stage 3`: kết quả `MN = 2, PQ = 4, S(MNPQ) = 3√7`). Sửa mô tả `EXPLAINER_SCENES[1]` sát lăng trụ đứng. Trong `LandingInteractiveDemo`, khóa `sample.verifiedMetrics` chỉ mở ở chặng cuối (`isFinalVerifiedStage`); cho `.axo-sp-story-metric-group` tự xuống dòng (`flex-wrap: wrap`) để không cắt chữ `P ∈ CC′`. | `frontend/src/components/landing/LandingExplainerAnimation.tsx`, `frontend/src/components/landing/LandingInteractiveDemo.tsx`, `frontend/src/components/landing/landing.css` |

---

## 3. Kết quả kiểm chứng 16 kịch bản E2E Playwright (`VERIFIED`)

Nguồn artifact: `verify_v122_e2e.mjs` -> `landing_v1_2_2_audit/e2e-v122-results.json` (`passed: true`, `16/16` checks đạt, `0` console error, `0` page error, `0` native dialog).

| # | Mã kiểm tra (`e2e-v122-results.json`) | Kết quả thực tế quan sát | Trạng thái |
|---|---|---|---|
| 1 | `desktop_guest_header_no_login` | Header không có `#btn-landing-header-login` và chữ `"Đăng nhập"`; có `Thư viện` và `Bắt đầu`. | `PASS` |
| 2 | `canonical_closing_copy_and_footer` | Hero & Final CTA là `"Bắt đầu dựng hình"`; Final title là `"Từ đề toán đến mô hình hình học không gian."`; Footer chỉ giữ 4 link điều hướng. | `PASS` |
| 3 | `storytelling_stage_epistemics` | Stage 0 chỉ hiện `"Giả thiết: Lăng trụ đều ABC.A′B′C′ (a = 4)"` và `"Trung điểm M ∈ AB · N ∈ AC · P ∈ CC′"`, không chứa `S(MNPQ)`; Stage 1 không chứa `"Mặt đáy mở rộng"`; Stage 3 hiện `"S(MNPQ) = 3√7"`. | `PASS` |
| 4 | `demo_stage_epistemics` | Demo Step 0 hiển thị `"Đề bài & khối chóp"` + tọa độ đề, không chứa `"S(MENPF) = 6√6"`; Demo Step 3 hiển thị `"S(MENPF) = 6√6"` và `"V(S.ABCD) = 32"`. | `PASS` |
| 5 | `guest_public_library_access` | Guest bấm `#btn-landing-hero-library` vào thẳng `http://localhost:3001/library` (`#view-library`) không qua login. | `PASS` |
| 6 | `guest_start_trial_preserves_draft` | Nhập `"Cho hinh chop S.ABCD day hinh thang"` ở `/app`, về `/gioi-thieu`, bấm `#btn-landing-hero-start` -> `/app` với `#home-problem-input` giữ nguyên `"Cho hinh chop S.ABCD day hinh thang"`. | `PASS` |
| 7 | `guest_auth_required_routes_to_existing_login` | Guest hết lượt thử (`canRunSimulation: false`) bấm `#btn-landing-final-start` -> đi thẳng `/login` (`#login-email-input`). | `PASS` |
| 8 | `post_login_restores_workspace_and_draft` | Đăng nhập Student tại `/login` -> khôi phục đúng `/app` và giữ nguyên draft `"Cho hinh chop S.ABCD day hinh thang"`. | `PASS` |
| 9 | `authenticated_landing_ctas_and_account` | Header, Hero và Final CTA đồng loạt là `"Vào ứng dụng"`; tài khoản hiển thị `Nguyễn Minh Anh`. | `PASS` |
| 10 | `authenticated_admin_direct_route` | Admin bấm CTA Landing vào thẳng `http://localhost:3001/admin`. | `PASS` |
| 11 | `cross_tab_broadcast_logout_reconciles_to_guest` | Tab khác phát `BroadcastChannel("axo_auth_sync_v1")` `logout` -> `#btn-landing-header-start` cập nhật về `"Bắt đầu"`. | `PASS` |
| 12 | `cross_tab_broadcast_login_reconciles_to_user` | Tab khác phát `BroadcastChannel("axo_auth_sync_v1")` `login` -> `#btn-landing-header-start` cập nhật thành `"Vào ứng dụng"`. | `PASS` |
| 13 | `expired_session_401_reconciles_to_guest` | `/api/auth/me` trả `401` khi `window.focus` (sau throttle `1200ms`) -> Landing tự chuyển về trạng thái Guest (`"Bắt đầu"`). | `PASS` |
| 14 | `mobile_guest_drawer_exact_5_items_and_a11y` | Drawer Guest có đúng 5 mục (`#drawer-nav-landing-hero`, `#drawer-nav-cach-hoat-dong`, `#drawer-nav-trai-nghiem`, `#btn-landing-drawer-library`, `#btn-landing-drawer-primary`), không có nút Login, `body.overflow = "hidden"`, Tab xoay vòng focus trap, `Esc` đóng drawer và trả focus về `#btn-landing-mobile-menu`. | `PASS` |
| 15 | `all_8_viewports_zero_overflow` | Cả 8 viewport từ `1920×1080` xuống `320×568` đều có `scrollWidth === clientWidth` (`overflow: false`). | `PASS` |
| 16 | `zero_dialogs_zero_errors` | `dialogs: []`, `pageErrors: []`, `consoleErrors: []`. | `PASS` |

---

## 4. Ma trận Responsive 8 Viewport (`VERIFIED`)

| Tên Viewport | Kích thước (`W × H`) | `scrollWidth` | `clientWidth` | Hero hiển thị | Overflow ngang |
|---|---:|---:|---:|---|---|
| `desktop-1920` | `1920 × 1080` | `1920` | `1920` | `true` | Không (`0px`) |
| `desktop-1440` | `1440 × 900` | `1440` | `1440` | `true` | Không (`0px`) |
| `laptop-1366` | `1366 × 768` | `1366` | `1366` | `true` | Không (`0px`) |
| `tablet-landscape-1024` | `1024 × 768` | `1024` | `1024` | `true` | Không (`0px`) |
| `tablet-portrait-768` | `768 × 1024` | `768` | `768` | `true` | Không (`0px`) |
| `mobile-390` | `390 × 844` | `390` | `390` | `true` | Không (`0px`) |
| `mobile-360` | `360 × 800` | `360` | `360` | `true` | Không (`0px`) |
| `mobile-320` | `320 × 568` | `320` | `320` | `true` | Không (`0px`) |

---

## 5. Kiểm tra trực quan Before / After (`VERIFIED`)

Đã chụp và đối chiếu trực quan qua tệp ảnh trong thư mục artifact `landing_v1_2_2_audit/before/` (7 ảnh V1.2.1) và `landing_v1_2_2_audit/after/` (8 ảnh V1.2.2):
- `after_01_desktop_hero_header.png`: Header Guest chỉ còn điều hướng 3 mục, `Thư viện` và `Bắt đầu`; Hero giữ nguyên điêu khắc chóp cắt 3D sạch sẽ.
- `after_02_desktop_story_stage0.png`: Stage 01 chỉ hiện chip giả thiết đề bài (`Giả thiết: Lăng trụ đều ABC.A'B'C' (a = 4)` và `Trung điểm M ∈ AB · N ∈ AC · P ∈ CC'`) đã xuống dòng gọn, không bị cắt chữ và không lộ đáp án `S(MNPQ)`.
- `after_05_desktop_closing_footer.png`: Closing Band dùng câu từ hình học tự nhiên (`"Từ đề toán đến mô hình hình học không gian."`), Footer gọn 4 liên kết, không còn nút primary lặp.
- `after_06_mobile_hero.png` & `after_07_mobile_drawer.png`: Header mobile chỉ có nút `Bắt đầu` và menu; khi mở drawer, CTA Header ẩn và drawer chứa đúng 5 mục điều hướng + CTA, không có `"Đăng nhập tài khoản"`.
- `after_08_desktop_authenticated_header.png`: Khi đăng nhập, Hero/Header đồng bộ nhãn `"Vào ứng dụng"` cùng menu tài khoản `Nguyễn Minh Anh`.

---

## 6. Kiểm tra tự động & Tệp thay đổi (`VERIFIED`)

- `npx tsc -b`: thoát mã `0`.
- `npm run build`: thoát mã `0` (`120 modules transformed`).
- `npx vitest run --maxWorkers=2 code-index-sync class-coverage landing-`: **12/12 file test pass, 45/45 test pass** (bao gồm 3 file test mới `landing-auth-navigation.test.tsx`, `landing-mobile-drawer.test.tsx`, `landing-cta-flow.test.tsx`, `code-index-sync.test.ts`, `class-coverage.test.ts` và các suite Landing sẵn có).
- `python backend/scripts/audit_docs_information_architecture.py --json`: kiểm định kiến trúc tài liệu & liên kết sau khi ghi báo cáo.

**Danh sách 15 tệp của commit Pha A (`fix(axo): streamline landing authentication and navigation`):**
1. `frontend/src/App.tsx`
2. `frontend/src/components/LandingView.tsx`
3. `frontend/src/components/landing/LandingHeader.tsx`
4. `frontend/src/components/landing/LandingExplainerAnimation.tsx`
5. `frontend/src/components/landing/LandingInteractiveDemo.tsx`
6. `frontend/src/components/landing/landing-geometry-data.ts`
7. `frontend/src/components/landing/landing.css`
8. `frontend/src/components/__tests__/landing-header-navigation.test.tsx`
9. `frontend/src/components/__tests__/landing-auth-sync.test.tsx`
10. `frontend/src/components/__tests__/landing-storytelling-interaction.test.tsx`
11. `frontend/src/components/__tests__/landing-auth-navigation.test.tsx`
12. `frontend/src/components/__tests__/landing-mobile-drawer.test.tsx`
13. `frontend/src/components/__tests__/landing-cta-flow.test.tsx`
14. `docs/CODE_INDEX.md`
15. `docs/evaluation/landing/AXO-LANDING-V1.2.2-UX-REPORT.md`
