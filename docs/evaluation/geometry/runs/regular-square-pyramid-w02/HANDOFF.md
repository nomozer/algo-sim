# HANDOFF — regular-square-pyramid-w02

Cho người dùng (chủ kho, người duyệt hình) và phiên local tiếp nhận. Số liệu và lý do: [`REPORT.md`](REPORT.md).

## Trường bắt buộc

```text
TASK = REGULAR_SQUARE_PYRAMID_PEDAGOGICAL_CLOSURE
TASK_SLUG = regular-square-pyramid
WAVE = W2
RUN_ID = regular-square-pyramid-w02
EXECUTION = CLOUD_IMPLEMENTATION_THEN_LOCAL_ACCEPTANCE
FINAL_DECISION = CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED
SOURCE_W1_HEAD = e821b9b5330480b791284548c3e49d683955682e
SOURCE_BRANCH = feat/regular-square-pyramid
CLOUD_WORKING_BRANCH = feat/regular-square-pyramid (phiên cloud khởi tạo sẵn trên nhánh này tại W1 head; không cần nhánh claude/*)
BASE_MAIN = 38d4158826cbbffd013d971a9484b9f0fd2a6130 (origin/main, không đổi; ref main không bị đụng)
FINAL_HEAD = SELF (commit chứa bản cuối của file này; tra bằng git log -1 origin/feat/regular-square-pyramid)
REMOTE_SHA = = FINAL_HEAD sau push (ghi lại trong trả lời của phiên cloud)
MEASUREMENT_COMMIT = 94200b50403bdf823eb49697d54c0cb53e8e4ccb (lượt đo 5, worktree tách rời sạch CRLF, đường dẫn có dấu cách); bằng chứng commit c5b39092
CANDIDATE_BEFORE = 5234c37e424c60bae4741e68170a0c95e5361cfbe71e2114b96c08d2310d44fa
CANDIDATE_AFTER = d3de9c446ef75b9b92b89e496f9b905349f4b30f3e5757849f46c6ce3c9d2098 (product commit 70665542; 110 file) — đóng băng 4 lần, cùng tree hash: c5142f07 → 527d642e → 75a0af9a → 70665542 (frontend/src đổi sau lần đo 1, lần đo 3 và T3 lần 1); bằng chứng trình duyệt đo ở product 75a0af9a chuyển sang 70665542 (results/EVIDENCE_TRANSFER_70665542.json)
CACHE_VERSION_BEFORE = 112
CACHE_VERSION_AFTER = 113
CACHE_VERSION_REASON = envelope phục vụ đổi nội dung; 13 row v112 vẫn HIT dù W2 dựng khác, bump làm cả 13 MISS; sáu họ cũ trùng byte (diagnostics/PROOF_CACHE_ROW_W02.json); môi trường ngữ nghĩa b1714b56 không đổi
MODEL_SURFACE_CHANGED = NO
DEFAULT_MODE = LLM_ONLY
LIVE_GEMINI_REQUESTS = 0
HUMAN_VISUAL_REVIEW = NOT_APPROVED
MAIN_PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
PR_CREATED = NO
WORKING_BRANCH_PUSH_RESULT = PUSHED bằng git push -u origin feat/regular-square-pyramid (không force); kiểm git ls-remote origin feat/regular-square-pyramid = FINAL_HEAD — SHA báo trong trả lời của phiên cloud
WORKING_TREE = sạch sau commit cuối (git status --porcelain rỗng ở cây cloud); trạng thái local của người dùng (deletion favicon) KHÔNG được kiểm từ cloud
FAVICON = frontend/public/favicon.svg không bị sửa, restore hay tái tạo deletion trên cloud
```

## 1. Yêu cầu đạt / chưa đạt

| mục brief | trạng thái cloud | bằng chứng |
|---|---|---|
| A nhãn theo formation state | ĐẠT (vitest + bộ đo + đầu dò) | REPORT §2 |
| B bảng nổi desktop / mobile | ĐẠT (đầu dò kéo thật 7 họ × 2 khổ) | REPORT §5, `results/W02_CLOSURE_PROBE.json` |
| C đoạn SO | ĐẠT | REPORT §3 |
| D hình phụ, nhóm bước con | ĐẠT | REPORT §6 |
| E chiều cao theo quan hệ | ĐẠT (ca trùng giá trị; sáu họ không đổi) | REPORT §4 |
| F lưới tuỳ chọn | ĐẠT | REPORT §7 |
| việc nhỏ (token máy, aria-controls, độ dài ≤ 0) | ĐẠT; độ dài ≤ 0 PARTIAL cho sáu họ cũ | REPORT §8 |
| gate repo đầy đủ | cloud: mọi cổng ngoài lớp môi trường xanh; T3 và hai cổng trình duyệt nghi môi trường ⇒ `LOCAL_VERIFICATION_REQUIRED` | REPORT §10 |

## 2. Việc phải làm ở máy local (LOCAL_VERIFICATION_REQUIRED)

Môi trường cloud: Linux, Python 3.12.3, Node 22.22, Chromium 141 headless + SwiftShader, không GPU; checkout
LF (khoá hash ghi trên Windows CRLF), không có ref `main` cục bộ. Đo có thẩm quyền chạy trong worktree tách rời
`core.autocrlf=true`, đường dẫn có dấu cách. Những gì không tái lập được ở đây:

1. **T3 `frontend/scripts/full-gate.mjs`** ở commit cuối, từ đường dẫn có dấu cách (như W1). Trên cloud pytest có lớp
   lỗi MÔI TRƯỜNG có trước W2 (cùng tập ở W1 head): thiếu ref `main` cục bộ (`test_branch_independent_harness`,
   `*_precheck_kho`, …) và Python Linux ghi LF vào cây CRLF làm cây "bẩn" (`test_exporter_idempotence`,
   `test_holdout_readiness_7b`). Ngoài tập ấy: 0 lỗi (REPORT §10).
2. **Hai cổng trình duyệt** đỏ cả ở W1 head + fixture W1 trên cloud (`diagnostics/ENV_CAMERA_SETTLE_BASELINE.json`):
   `camera_settled_rotated_neutral` (6 desktop) và `causal_restore` của thiết diện (mobile 3/3 cả hai phía; desktop
   không tất định: W2 2/3, W1 1/3 — pixel khác là độ đậm khử răng cưa của cùng một đường, không vật nào hiện/ẩn).
   Chạy lại bộ đo ở máy local; nếu vẫn đỏ ở đó thì là lỗi thật của W2, không phải môi trường.
3. **Node harness `full-gate.node-test.mjs`** "repo root keeps a Windows path with spaces" chỉ đúng trên Windows.
4. Duyệt hình (§3).

Lệnh (từ gốc một worktree tách rời sạch ở commit cuối, đường dẫn có dấu cách, `npm ci --offline`):

```bash
bash docs/evaluation/geometry/runs/regular-square-pyramid-w02/diagnostics/w02_measure.sh <python> <logs ngoài worktree>
node frontend/scripts/full-gate.mjs
bash docs/evaluation/geometry/runs/regular-square-pyramid-w02/diagnostics/w02_gates.sh <commit cuối> e821b9b5 <python>
```

## 3. Câu hỏi chờ người dùng

| id | câu hỏi | xem ở |
|---|---|---|
| **H-W2-1** (chặn merge) | Duyệt hình W1 + W2: bảng nổi (desktop) và bảng thu gọn (mobile); nhãn theo bước; đoạn SO và "V = 1/3 × S(ABCD) × SO"; hình phụ ẩn/hiện; lưới. | bảng: `images/<họ>/desktop/steps_panel_floating.png`, `steps_panel_dragged.png`; mobile: `images/<họ>/mobile/steps_sheet_open.png`, `steps_sheet_collapsed.png`; nhãn theo bước: `images/triangular-pyramid/desktop/labels_showall_step_0..3.png`, `images/triangular-prism/desktop/labels_showall_step_*.png`, `images/<họ>/desktop/formation/`; SO: `images/regular-square-pyramid/desktop/final_neutral.png`, `selected_volume.png`; hình phụ: `auxiliary_shown.png`; lưới: `grid_on.png`; tổng quan: `images/<họ>/SHEET.png` |
| H-W2-2 | Đáp số là độ dài một đoạn KHÔNG được dựng ("Tính độ dài đoạn SH") nay không có nhãn trên hình (luật A); vẫn chọn được qua ngăn. Có muốn bước bổ sung dựng luôn đoạn được hỏi? | `diagnostics/PREREGISTRATION_CORRECTIONS.json` PC1-W2 |
| H-W2-3 | Ô soi vẫn là CỘT ở ≥ 1100 px (chọn vật làm canvas co lại). Giữ, hay cho nổi bằng cùng cơ chế bảng nổi? | `ISSUE-ARCH-INSPECTOR-COLUMN-RESIZES-CANVAS` |
| H-W2-4 | Bước «Mặt phẳng qua A, B, C» (chỉ để đo) nay không vẽ gì khi hình phụ tắt; danh sách ghi "hình phụ, đang ẩn". Chấp nhận? | `images/regular-square-pyramid/desktop/` |
| H-W2-5 | Nhóm bước con lấy tên bước chính ("Giao điểm của AC và BD"), không phải "Dựng tâm đáy". Đủ chưa? | ảnh bảng bước |
| giữ từ W1 | H-W1-1 (chặn merge, gộp vào H-W2-1); H-W1-2…H-W1-5 được W2 trả lời bằng thay đổi (SO; mặt phẳng phụ ẩn; nhóm bước; độ dài ≤ 0) — cần người xem | `../regular-square-pyramid-w01/HANDOFF.md` §1 |

Chỉ người dùng ghi `APPROVED_BY_USER`.

## 4. Hướng dẫn tiếp nhận ở máy local

Không tự chạy, không merge thay người dùng. Không reset để ghi đè thay đổi local.

```bash
git fetch origin feat/regular-square-pyramid
git merge-base --is-ancestor e821b9b5330480b791284548c3e49d683955682e origin/feat/regular-square-pyramid && echo "W1 nằm trong nhánh cloud"
git log --oneline e821b9b5..origin/feat/regular-square-pyramid
git diff --stat e821b9b5 origin/feat/regular-square-pyramid
# nhánh local đang ở W1 head và không có commit riêng ⇒ fast-forward:
git merge --ff-only origin/feat/regular-square-pyramid
```

Nếu nhánh local có commit riêng: dừng, so `git log feat/regular-square-pyramid..origin/feat/regular-square-pyramid`
và ngược lại, rồi quyết; không force, không rebase. Deletion `frontend/public/favicon.svg` ở máy local không bị nhánh
cloud chạm tới.

Sau khi người dùng duyệt (AGENTS.md §2): kiểm lại `origin/main`, merge thẳng vào `main`, push `main`, xoá nhánh đã
merge; không PR.

## 5. Cho phiên agent kế tiếp

- Mã mới: `scene3d-floating-panel.tsx`, `scene3d-auxiliary.ts`, `formation._tam_day_deu`,
  `quantity_annotations.chieu_cao_the_tich` / `_bam_doan_da_dung`, `refusal_cause.do_dai_de_ghi_khong_duong`
  (`docs/CODE_INDEX.md`, các mục w02).
- Bộ đo: `frontend/scripts/w02-closure-probe.mjs`; cổng `assessFloatingPanel`, `assessStepsSheet`,
  `assessAuxiliary`, `assessGridToggle`; oracle `builtSegmentPairs`, `expectedAuxiliaryHidden`.
- Bẫy đã gặp:
  - `freeze_evaluation_candidate.py`: mọi đối số khác `--verify` là ĐÓNG BĂNG; `product_commit_sha` = commit cuối
    chạm `backend/app` HOẶC `frontend/src` ⇒ sửa frontend nào cũng phải đóng băng lại (tree hash có thể không đổi).
  - Hai nút cùng `aria-label="Đóng"` làm bộ đo bấm nhầm (và mơ hồ với trình đọc màn hình).
  - Lớp phủ có `z-index` phải xếp dưới ngăn/ô soi.
  - Script `.sh` trong worktree CRLF: chạy qua `tr -d '\r' | bash -s --`.
  - `pkill -f <mẫu>` trên cloud tự giết chính lệnh chứa mẫu ấy.
