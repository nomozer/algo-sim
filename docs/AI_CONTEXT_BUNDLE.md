# AI_CONTEXT_BUNDLE.md — AlgoSim Session Handoff & Quick Context

> Handoff cô đọng cho session mới. Code/test thắng khi mâu thuẫn với docs.
> Không chứa secret hoặc raw model output; giới hạn 300 dòng.

## 1. Product và ranh giới

AlgoSim chuyển đề hình học không gian tiếng Việt thành Semantic Program và
Scene3D tương tác. LLM chỉ trích xuất/tổng hợp cấu trúc; engine tất định sở hữu
tọa độ, thực thi, đo lường, correctness và scene state.

- `DEFAULT_MODE = LLM_ONLY`; compiler-first vẫn opt-in.
- `CACHE_VERSION = 102`; provider-facing fingerprint
  `b1714b566e25c912…` không đổi trong wave gần nhất.
- Mọi test/repair gần nhất offline: `LIVE_GEMINI_REQUESTS = 0`.
- Không hardcode case/label/answer vào product; mâu thuẫn phải fail-closed.

## 2. Repository state hiện tại

```text
CURRENT_BRANCH = fix/cuboid-visual-semantic-closure
POST_REPAIR_HEAD = 075d484f761eb40474efc9f25e49ece3563003c7
ORIGIN_MAIN_AT_GATE = a9492ee98ff9dc3302d1ff64465f1c06e9001bce
FINAL_DECISION = VERIFICATION_NOT_CLEAN
USER_DIRTY_STATE = D frontend/public/favicon.svg
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
```

Deletion favicon là thay đổi của người dùng: không restore, sửa, stage hoặc
commit. Không amend/rebase/squash chuỗi commit đã được evidence tham chiếu.

## 3. Wave occlusion đã sửa được gì

- Canonical machine edge IDs dùng endpoint entity IDs (`A_prime`); display label
  (`A′`) là dữ liệu trình bày riêng.
- Mỗi logical edge có một visual owner. Solid phát edge ownership, canonical
  surfaces, `boundary_edge_ids`, `surface_role`, `occludes_edges`.
- Product classifier chia edge thành exact `VISIBLE`/`HIDDEN`/`MIXED` spans bằng
  world-space ray/triangle và adaptive refinement.
- Evidence oracle độc lập dùng projected interval + perspective-correct depth;
  synthetic reference dùng camera ray/triangle.
- Formation events typed ở backend; section endpoints giữ stable semantic
  identity/provenance.
- Năm temporary worktree đã inventory/recover/remove; required/unknown/unique
  commit risk đều 0.

Sáu family đã đo: `triangular_pyramid`, `rectangular_pyramid`,
`triangular_prism`, `cuboid`, `cube`, `cross_section` (mỗi family một fixture
dương + một âm, `inputs/FIXTURE_MANIFEST.json`). Browser authoritative 1/6 PASS;
năm family còn lại chỉ fail assertion mobile `immutable_120_frames`.

Các gate sau PASS: exact product↔oracle edge IDs/spans, perspective reference,
formation semantics, section identity và worktree recovery.

## 4. Còn đỏ — không được che

- `FROZEN_CAMERA_IDENTITY_MISMATCH`: 2 cases (`triangular_prism`, `cube`).
- Mobile `immutable_120_frames`: FAIL ở 5 families.
- Frontend full: 904 pass, 1 fail; legacy whole-source regex bắt nhầm
  `boundary_edge_ids`.
- Backend full: 6268 pass, 35 fail, 1 skip, 1 deselect; chưa phân loại hết.
- Full-gate runner chưa resolve Python environment độc lập worktree.
- Chưa có human visual acceptance; chưa merge.

## 5. Bước tiếp theo duy nhất

```text
CANONICAL_NEXT_ACTION = VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR
TARGET_NEXT_ACTION_AFTER_WAVE = VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR
```

Chỉ xử lý năm nhóm gate ở §4. Không mở family, image/OCR, composite geometry,
không refreeze candidate và không đổi cache/provider contract nếu chưa có bằng
chứng bắt buộc.

## 6. Evidence có thẩm quyền

- Correction report:
  `docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/REPORT.md`
- Machine summary:
  `.../results/VERIFICATION_SUMMARY.json`
- Run identity/manifests: `.../RUN.json`, `.../MANIFEST.json`, `.../HANDOFF.md`.
- Frozen human sets: `.../inputs/human_expected_visibility.json`.
- Recovery inventory:
  `docs/evaluation/geometry/worktree-recovery/WORKTREE_RECOVERY_INVENTORY.json`.
- Correction chain owner: `docs/EVIDENCE_INDEX.md`.
- Architecture amendment:
  `docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`.

Historical run artifacts are immutable. Run mới phải theo
`docs/evaluation/RUN_NAMING.md` (`YYYYMMDD-wNN-short-slug`).

## 7. Thứ tự đọc

1. `AGENTS.md`
2. `docs/RULES.md`
3. file này
4. `docs/CURRENT_STATE.md`
5. `docs/OPEN_ISSUES.md`
6. `docs/ROADMAP.md`
7. `docs/CODE_INDEX.md`
8. `docs/EVIDENCE_INDEX.md`
9. Code/test trực tiếp liên quan

## 8. Git và evidence safety

- Staging theo explicit file allowlist; kiểm `git diff --cached --name-only`.
- Không push/merge/rewrite history khi chưa được chỉ định.
- Authoritative measurement chạy từ detached clean worktree tại candidate.
- Product output và oracle output không tự sửa frozen human expectations.
- Historical report/artifact không sửa; sai lệch đi qua correction layer.
