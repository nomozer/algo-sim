# Kiểm toán cuối trước `main` — `scene3d-plane-grid-camera` (2026-10-18)

- **Candidate HEAD được đo:** `61668c9362c49df39f1ae948b0e7a7e1cad33f95` (`7495b7c3` test + refreeze). Bản ghi này và
  các biên nhận là commit tài liệu sau T3.
- **Bất biến:** `DEFAULT_MODE = LLM_ONLY`, Hybrid `NO-GO`, `CACHE_VERSION = 125` (không bump: chỉ đổi frontend + test,
  không đổi prompt/định tuyến/định danh cache của `/api/analyze`), 0 lượt gọi AI thật, không merge/push `main`, không dọn.
- **Duyệt thị giác của chủ sở hữu:** `HUMAN_VISUAL_REVIEW_PENDING`. Chủ sở hữu nói trong phiên rằng P0–P3 đạt trên cảnh
  mẫu nhưng **chưa cấp GO MAIN**; bản ghi này không ghi `APPROVED_BY_USER` (chỉ người ghi).

## 1. F5 — báo cáo sai, mã đúng

- Hợp đồng `docs/architecture/HYBRID_PREVIEW_FRONTEND_CONTRACT.md` §6/§9: `verification_gap` là **`failure_category`**;
  `reason_code` là mã chi tiết (9 fixture mang 9 mã khác nhau).
- Mã: `SimulationWorkspace.tsx::UnsupportedNotice` rẽ theo `unsupported.failure_category === "verification_gap"`.
  `report.md` và `review.md` ghi `reason_code: "verification_gap"` — **lỗi báo cáo**. Đã sửa dòng F5 của `report.md`
  (đánh dấu đính chính); `review.md` là bản ghi của reviewer, giữ nguyên, đính chính ở đây.
- Đường thật: `ProblemInput.onAnalyze → analyzeViaServer → store.loadUnsupported(result)` (nguyên object) →
  `SimulationWorkspace` trả `<UnsupportedNotice unsupported={store.unsupported}/>`. Test cũ dựng `UnsupportedNotice`
  thẳng từ fixture, bỏ qua store.
- Thêm test (`7495b7c3`, `hybrid-preview-contract.test.tsx` "F5/F6 qua store"): 12 fixture (9 `verification_gap`,
  3 `insufficient_specification`) qua `loadUnsupported` → `getState().unsupported` (deep-equal fixture) → đúng phần tử
  shell dựng; khẳng định nguyên văn tiêu đề và gợi ý. **Xanh ngay lần đầu** ⇒ không sửa mã sản phẩm.
- Phép tiêm lỗi (đã hoàn nguyên, `git diff` sạch): (a) đổi nhánh F5 sang `reason_code === "verification_gap"` ⇒ 2 test đỏ,
  tiêu đề rơi về "NGOÀI DANH MỤC MÔ PHỎNG"; (b) bỏ guard `SOURCE` của F6 ⇒ 3 test đỏ, hiện "Bổ sung dữ liệu còn thiếu
  vào đề…".

## 2. F4 — đính chính phạm vi

- `report.md` cũ mô tả trường `status === "verified_in_configuration"` và nhãn "Kiểm chứng trong cấu hình cụ thể…" —
  cả hai không có trong mã (mã rẽ theo `evidence_state`). Đã sửa dòng F4.
- **Chưa nối ở sản phẩm:** hợp đồng §2 đặt `route_d` NGOÀI envelope; `SimulationWorkspace` đọc `active.envelope.route_d`
  ⇒ với mọi phản hồi đúng hợp đồng, khối quan sát không bao giờ hiện. Bằng chứng DOM: `F4-product__served-H07…`
  `route_d_observation = []`. Chỉ chứng được ở mức component (`F4-component__served-H07…`, harness dựng
  `Scene3DExplorer(scene=envelope.scene3d, routeD=response.route_d)` từ fixture, SHA-256 khớp manifest).

## 3. T3 — trước đây CHƯA chạy

`run.json` cũ chỉ có vitest + build + orbit + 84 test hợp đồng/đồng bộ — không pytest toàn bộ, không demo replay, không
crash surface, không worktree detached sạch. Biên nhận orbit cũ (`visual/receipts/orbit-gate.json`) đo ở `4abc4afb`,
**trước** mọi sửa Scene3D và F1–F6.

| lượt | commit | kết quả |
|---|---|---|
| 1 | `7495b7c3` | `FULL_PRODUCT_GATE_FAIL` — 8 test đỏ: candidate lệch `product_commit_sha` (wave sửa `frontend/src` mà không đóng băng lại). `verification/t3-attempt-1.json` |
| refreeze | `61668c93` | đóng băng trong worktree detached sạch; `measured_system` không đổi (111 file, `1b7a6713…`), chỉ `product_commit_sha` `bce21d8b → ec72eda0`; lớp `candidate_divergence` của `hybrid-preview-contract-hardening` vẫn khai đúng băm |
| 2 | `61668c93` | **`FULL_PRODUCT_GATE_PASS`** — pytest 10828 passed / 1 skipped / 9 xfailed; vitest 69 file / 1117; build PASS; demo 5/5 + chuỗi rút gọn 1/1; crash surface 6/6, 0 lỗi 500. `verification/authoritative-t3.json` |

Cùng checkout, ngoài T3: orbit gate **ĐẠT** p1/p6/p7 (`visual/receipts/orbit-gate-61668c93.json`); node harness 112
test, 0 fail.

## 4. Ảnh DOM/UI thật (`visual/pre-main-audit/`)

Bản dựng sản phẩm (`dist/` do T3 dựng ở `61668c93`), Chromium headless, ô nhập + nút thật; `/api/analyze` trả
**nguyên văn** `response.envelope` của fixture Adapter /2 sau khi kiểm SHA-256 `response` khớp `manifest.json`
(17/17 khớp; không phản hồi nào viết tay). Biên nhận: `dom-receipts.json`; mã đo: `harness/`.

| tính năng | fixture | kết quả DOM |
|---|---|---|
| F5 | 9 `refusal-{source,result,inconclusive}-*` | tiêu đề "CHƯA ĐỦ BẰNG CHỨNG KIỂM CHỨNG", gợi ý "Hệ chỉ hiển thị mô phỏng khi đối chiếu và kiểm chứng được đầy đủ từ dữ kiện đến kết quả.", 0 mã kỹ thuật, 0 lỗi trang |
| F6 | 3 `refusal-missing-*` (`UNKNOWN`) | tiêu đề "CHƯA ĐỦ DỮ KIỆN", gợi ý có điều kiện, không mời sửa đề |
| F6 (SOURCE thật duy nhất) | `refusal-invalid-zero-length` (`geometry_generation_failed`) | "CHƯA DỰNG ĐƯỢC MÔ PHỎNG", không gợi ý |
| F3 | `served-H01_CUBE`, `served-H14_…` / `served-pyramid-midpoint-area-AB` | chip "Tỉ lệ dựng: a = 1 đơn vị dựng" / không chip |
| F4 | `served-H07…` sản phẩm / component | 0 quan sát / 1 quan sát, không chữ "đã chứng minh" |

**Không có fixture Adapter /2 nào là `insufficient_specification` + `SOURCE`**: nhánh mời bổ sung dữ kiện của F6 chỉ
được chứng bằng envelope sửa tay trong test, không bằng fixture đóng băng.

## 5. Reviewer độc lập (chỉ đọc, không chạy test)

F5 **CONFIRMED**; F6 **CONFIRMED (chỉ gợi ý)**; đường store **CONFIRMED**; trung thực toán học: **có vấn đề, không chặn
khi Hybrid NO-GO**:

1. `NHAN_LOAI_VAN_DE.verification_gap` = "chạy được nhưng chưa đủ bằng chứng để phát" — **sai** cho 4/9 mã dừng trước
   khi dựng (`SOURCE_OBJECT_MISMATCH`, `GOAL_CLAUSE_NOT_PREMISE`, `REQUEST_NOT_ANSWERED`, `FIGURE_NOT_UNIQUE`); thân thẻ
   nói "tạm dừng dựng hình" ngay trên nhãn "chạy được" (thấy trong ảnh `F5__refusal-source-*`).
2. F6 `UNKNOWN`: gợi ý đã trung lập nhưng tiêu đề "CHƯA ĐỦ DỮ KIỆN" và nhãn "đề chưa đủ dữ kiện" vẫn quy cho đề;
   `refusal-missing-ambiguous` là đề đủ dữ kiện (mô hình tự đánh dấu mơ hồ). Hành vi này có từ trước wave.
3. F4: câu quan sát không nêu quan hệ ("điều này" không có chỗ neo) và hiện từ bước 1/4, trước khi BC hay (SAB) được
   dựng (ảnh `F4-component__served-H07…`).
4. F3: H07 hiện "Thể tích S.ABC = √3/3" cạnh chip "a = 1"; đáp số theo `a` (`a³√3/3`, `route_d.answers`) không tới được
   sản phẩm (hệ quả của §2) — §4 hợp đồng chưa trọn.
5. "Dừng ở bước: Không xác định được từ phản hồi cũ" cho mọi lời từ chối Adapter /2 — phản hồi mới, không cũ.

Mục 1, 3, 4 và nối `route_d` (§2) phải sửa **trước bất kỳ GO Hybrid nào**.

## 6. Vấn đề kiến trúc do wave này đưa vào

- `frontend/src/state/store.ts:11` import `simulations/domains/geometry/scene3d-chart` — vi phạm "store MÙ DOMAIN
  (M2 #7)" do chính header của store và `ARCHITECTURE_MAP` §271 tuyên bố. Handoff F2 giao guard cho
  `scene3d-chart.ts`, không cho store; đường hiển thị đã fail-closed qua `hopLeScene3D` (`App.tsx:77`,
  `SimulationWorkspace.tsx:491`). Không test nào bắt.
- `hopLeChartMetric` có hai định nghĩa (`scene3d-chart.ts:79`, `scene3d-model.ts:30`) cộng bản ném lỗi trong
  `maTranKhung` — hơn một thẩm quyền.

Không sửa ở lượt này (ngoài quyền "sửa tối thiểu nếu F5 đỏ"); cần quyết định của chủ sở hữu.

## 7. Phán quyết

**Chưa `FINAL_SCENE3D_PRE_MAIN_READY`.** Cổng kỹ thuật đã đủ và xanh ở `61668c93`; còn hai điều kiện:

1. **BLOCKER-ARCH:** store import miền hình học (§6) — đảo luật mù domain mà kho coi là bất biến.
2. **Duyệt thị giác:** `HUMAN_VISUAL_REVIEW_PENDING` — chỉ chủ sở hữu ghi được.

Không chặn (Hybrid NO-GO): §5 mục 1–5, F4 chưa nối, F6-SOURCE không có fixture.
