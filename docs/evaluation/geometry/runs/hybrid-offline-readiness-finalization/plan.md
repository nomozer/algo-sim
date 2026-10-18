# hybrid-offline-readiness-finalization — plan và checkpoint

Quyền: `GO_HYBRID_OFFLINE_READINESS_IMPLEMENTATION_ONLY` (owner, 2026-10-18). Không merge/push `main`, không bật Hybrid,
không gọi AI thật, không xoá dữ liệu, không kiến trúc nghiên cứu mới.

## Baseline (P0, đã kiểm)

| mục | giá trị |
|---|---|
| `main` = `origin/main` = ls-remote | `f2b00ed3ec1e333e3b5c18c046ac5beec1f7b6fb` |
| baseline sản phẩm / product Scene3D / T3 | `551a3541` / `cb1f4954` / candidate `14c26f3f` |
| freeze | MATCH 111 file `045a8a628c7923d6…` |
| chính sách | `LLM_ONLY`, `flat`, Hybrid NO-GO, `ALLOW_LIVE_AI` không bật, preview OFF, cache 125, 0 caller `/api/preview/hybrid` |
| nhánh / worktree | `research/hybrid-offline-readiness-finalization` @ `.superpowers/worktrees/hybrid-offline-readiness-finalization` (sạch, từ `main`) |
| writer khác | không (Codex app-server nhàn rỗi từ 19:32) |

## Ma trận xuất phát

| hạng mục | trạng thái lúc bắt đầu |
|---|---|
| bộ đọc độ dài nguồn (vectơ/tổng/tích/giả định) | **lỗi** — `ISSUE-ARCH-SOURCE-LENGTH-READER-VECTOR-ZERO` |
| HFOI-F3 đáp số ký hiệu | **lỗi** — 6/7 fixture có `a`: cảnh/lời kể trình bày giá trị tại a = 1 như đáp số (`V = √3/3` thay `a³√3/3`) |
| HFOI-F4 `route_d` | **lỗi** — workspace đọc `envelope.route_d` (không bao giờ có); quan sát không neo bước; adapter `/2` KHÔNG mang đối số quan hệ |
| HFOI-F5 nhãn verification-gap | **lỗi** — "chạy được…" cho cả lời từ chối trước khi dựng |
| HFOI-F6 UNKNOWN/source | **lỗi** — tiêu đề/nhãn quy cho đề; "từ phản hồi cũ" cho phản hồi mới; thiếu fixture `insufficient_specification`+`SOURCE` (không producer nào phát cặp này) |
| F5/F6 cũ (Scene3D presentation) | ĐÃ RESOLVED — `ISSUE-ARCH-SCENE3D-VERIFICATION-GAP-PRESENTATION`, `ISSUE-ARCH-SCENE3D-INSUFFICIENT-SPEC-HINT`; không mở lại |
| offline E2E | chưa có harness đi qua biên sản phẩm cho Hybrid |

Tên phân biệt dùng trong run này: **HFOI-F3…F6** = các mục còn mở của `ISSUE-ARCH-HYBRID-FRONTEND-OFFLINE-INTEGRATION`.

## Kế hoạch (tuần tự)

P1 backend vector-zero → commit + bằng chứng · P2 adapter/frontend HFOI-F3…F6 → commit · P3 harness offline E2E →
commit · P4 đóng băng lại candidate (commit riêng) → T3 trên worktree detached sạch → reviewer · P5 docs + handoff.

## Checkpoint

- [x] P0 — baseline khớp.
- [x] P1 — `c55374cc`: một vị từ `loai_nhan_doan`; 80 test (RED tại phiên bản đầu 50 failed/18 passed — chỉ giữ dòng
  tổng kết; tiêm lỗi trên bộ cuối: 53 failed/27 passed, `p1-source-length/fault-injection.log`); parity 1889 đề, 0 hồi
  quy; `CACHE_VERSION` 125 → 126 (`cache/decision.json`). Hồi quy liên quan 1756 passed; backend đầy đủ: 11 đỏ đều do
  cây bẩn/candidate chưa đóng băng lại — phải xanh sau P4.
- [x] P2 — `479e04d5`: adapter `hybrid-preview-adapter.ts`, F3 `ghiChuGiaTriDung`, F5/F6 câu chữ, fixture tổng hợp;
  vitest 1140 → 1141 sau review, build PASS, tiêm lỗi frontend bắt được (neo bước, đối chiếu hệ số).
- [x] P3 — `c6693e1e`: 41/41 phản hồi sinh lại trùng byte; oracle độc lập 12/12 (a = 1 và a = 2, cửa sổ chứng 4/4);
  E2E trình duyệt 48/48, 0 lượt gọi `/api/preview/hybrid` hay `/api/analyze` (lượt đầu 38/48 do kỳ vọng bước của harness
  sai — giữ ở `receipts-superseded/`); tiêm lỗi "quan sát sớm" ⇒ 47/48.
- [x] Review độc lập P1/P2 — 1 BLOCKING (bump thiếu `cache_identity.lock.json` + danh sách phiên bản), 3 IMPORTANT
  (I1 hồi quy gạch đầu dòng, I2 `⋅`/`\cdot`/`x`/`:`, I3 giả định nới cổng), 4 MINOR; sửa ở `9d17557e` (backend) và
  `cc07f512` (frontend); E2E lại 48/48, 41 fixture lại trùng byte, hồi quy backend rộng 2641 passed.
- [ ] P4 — đóng băng lại candidate (commit riêng) → T3 trên worktree detached sạch · [ ] P5

## Codex continuation checkpoint — 2026-10-19

Owner continuation + minimal disclosure scope, same branch/run. Recovery: `recovery.md`.

- [x] Preserve Claude commits/uncommitted files; recover background run as NOT EXECUTED (`-n` unsupported,
  shell exit0 masked pytest status). No test/writer killed; no duplicate suite launched.
- [x] Commit preserved second-review fix `8bcb9d8e` (178 targeted passed).
- [x] Separate disclosure commit `531b7143`, witness preservation `2af99e0e`; RED/GREEN browser receipts in
  `p2b-disclosure/`. Final expanded browser4/4 includes cube, pyramid, cuboid distance, keyboard, show-all,
  actual orbit/reset, answer payload retained, same/different analysis and refusal/legacy replacement.
- [x] Independent review findings repaired: source coefficient/conditional fixes `794563cb`, anchor/null wrapper
  fixes `8ee9e3eb`. 185 targeted backend passed; adapter39 and annotations33 passed. Full Vitest first run had
  1141 passed/2 stale source-contract assertions failed; updated assertions in test-only `00b7bba4` (focus32 passed).
- [x] Final offline48/48; fixture41/41 responses identical; oracle12/12; parity1896 texts/22 intended changes,
  diff byte-semantically identical to the prior reviewed diff. Final review: `review.md`.
- [x] Freeze `96e2fe1e`: product `2af99e0eddb67da253adcf6dc0aa7ac4fd08b05d`, 111 files,
  `cb11bc7757466bd6c52cd063e975c4540514bac6c49acc70c4d4dfca7fff660c`, cache126, clean manifest.
- [ ] Authoritative T3 RUNNING on clean detached `.superpowers/worktrees/t3-hybrid-offline-readiness-final`
  at `96e2fe1e647ba3d7cb03f16082775219c7712a4f`. Do not edit that tree or launch another full suite.
  Command: `node frontend/scripts/full-gate.mjs --python D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe`.
  Live log in implementation worktree `.superpowers/verification/t3-96e2fe1e.log`, terminal session62334;
  wrapper writes `t3-96e2fe1e-exit.json` only after completion (actual exit code). Scoped pytest basetemp is
  `.superpowers/verification/pytest-t3-96e2fe1e`; no xdist, no global ACL changes.
- [ ] Read final exit/log; verify candidate and clean detached tree again; preserve successful receipt or
  sanitized failure, with hashes. Finish canonical docs, evidence index, run.json and one final handoff.

No product changes after `2af99e0e`. Only tests/harness/docs/evidence may still be completed. Hybrid stays NO-GO,
LLM_ONLY/flat/live0. HFOI-F4 exact relation operands and product transport remain absent; no Product E2E PASS.
No main merge/push, worktree deletion, data cleanup or user-approval assertion authorized.
