# HANDOFF — W19 docs reorganization and research evidence curation

```text
TASK = W19_DOCS_REORGANIZATION_AND_RESEARCH_EVIDENCE_CURATION
FINAL_DECISION = DOCS_REORGANIZED_AND_VERIFIED
BRANCH = fix/cuboid-visual-semantic-closure
BASE = 6d0e6321b70f89bd04473da4a458f7d8753eff6d
ORIGIN_MAIN = a9492ee98ff9dc3302d1ff64465f1c06e9001bce (git fetch --prune origin + ls-remote: unchanged)
COMMITS = a5c2e6f2 (structure + migration) · a44631a9 (claim map, hubs, closed docs root, cleanup) · documentation commit (this file)
PRODUCT_BEHAVIOR_CHANGED = NO
DEFAULT_MODE = LLM_ONLY
CACHE_VERSION = 110
CANDIDATE_REFROZEN = NO (d3b4cab96c69a09f…, --verify exit 0)
LIVE_GEMINI_REQUESTS = 0
HUMAN_VISUAL_REVIEW = NOT_APPROVED (W18; unchanged)
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
HISTORY_REWRITTEN = NO
USER_FAVICON_DELETION_PRESERVED = YES (never staged, restored or edited)
NEXT_ACTION = NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES
```

## 1. Cây `docs/` trước / sau

Đầy đủ (số file mỗi thư mục): [`verification/DOCS_TREE_BEFORE_AFTER.txt`](verification/DOCS_TREE_BEFORE_AFTER.txt).

| | trước (`6d0e6321`) | sau |
|---|---|---|
| gốc `docs/*.md` | 208 (lẫn: chuẩn tắc, dự án, báo cáo, bản thảo khoá luận) | 198 = 11 chuẩn tắc + 7 dự án + 180 báo cáo (catalog đóng) |
| `architecture/` | 9 | 8 (contract + snapshot + README; 2 quyết định đã thực thi sang `legacy/`) |
| `research/` | 13 (phẳng) | 14 + `thesis/` 12 + `thesis/figures/` 19 + `paper/` 1 |
| `thesis/`, `thesis_figures/` | 5, 19 | không còn (vào `research/thesis/`) |
| `superpowers/`, `geometry/` | 18, 9 | không còn (`legacy/`; độ phủ chương trình sang `research/`) |
| `legacy/` | 1 | 4 + `superpowers/` 18 + `geometry/` 8 + `architecture/` 2 + `research/` 3 |
| `evaluation/` | 8 439 file | + `README.md`, `HISTORICAL_REPORTS.md`, run `w19-docs-organization/` |

## 2. File đã di chuyển, gộp, lưu trữ, xoá

Từng cặp cũ → mới, blob trước/sau, lý do: [`inventory/MIGRATION_MAP.json`](inventory/MIGRATION_MAP.json) (65 file +
một khối nội dung). Quyết định của mọi tài liệu (kể cả KEEP): [`inventory/INVENTORY.json`](inventory/INVENTORY.json).

- **MOVE 33 → `docs/research/`**: 8 tài liệu khoá luận ở gốc (`THESIS_DRAFT`, `THESIS_ARCHITECTURE`, `THESIS_DEMO`,
  `THESIS_REFERENCES`, `THESIS_CITATION_MATRIX`, `THESIS_REFERENCE_NEEDS`, `THESIS_FIGURE_CAPTURE_PLAN`,
  `THESIS_SUBMISSION_CHECKLIST`) và 4 file của `thesis/` → `research/thesis/`; 19 file `thesis_figures/` →
  `research/thesis/figures/`; `PUBLICATION_READINESS_ASSESSMENT` → `research/paper/`;
  `geometry/GEOMETRY_CURRICULUM_COVERAGE` → `research/` (bằng chứng của tuyên bố phủ chương trình). Lý do: bản thảo
  và tài liệu nghiên cứu, không phải báo cáo wave (R5).
- **ARCHIVE 29 → `docs/legacy/`**: 18 kế hoạch/spec skill (`superpowers/`), 8 tài liệu giai đoạn chuyển đề
  (`geometry/`), 2 quyết định đã thực thi (`architecture/NEXT_VERTICAL_SLICE_DECISION`,
  `CUBOID_CUBE_CONTRACT_DECISION`), `REPOSITORY_MAP`. Lý do: hết hiệu lực, đáng giữ để truy vết (R4).
- **MERGE 3 → `docs/research/CLAIM_EVIDENCE_MAP.md`**, bản gốc lưu nguyên byte ở `legacy/research/`:
  `THESIS_READINESS`, `thesis/CLAIM_EVIDENCE_MATRIX`, `research/CLAIM_TO_EVIDENCE_MAP` (R6).
- **Khối nội dung**: `CURRENT_STATE.md` dòng 88–5475 → `legacy/CURRENT_STATE_HISTORY.md`, thân trùng từng byte (R7).
- **Trùng byte / đổi nội dung**: 55 file chuyển trùng blob; 10 file chuyển có link/con trỏ viết lại, mỗi chỗ ghi ở
  `inventory/REWRITE_LOG.json`, `REWRITE_LOG_MERGE.json`, `AUTHORITY_RETARGET.json`.
- **DELETE 0 trong kho.** Ngoài kho: xoá `D:/Documents/projects/docs/evaluation/geometry/holdout/COVERAGE_MATRIX.md`
  (trùng blob `f31a6c8c…` = bản đã commit tại `f4b6e734`) và thư mục `holdout/` rỗng sau đó. File W19 tự tạo: xem §5.

## 3. Ngoại lệ — đường dẫn giữ nguyên vì hợp đồng ngoài phạm vi

| đường dẫn | ai ghim | vì sao không chuyển |
|---|---|---|
| `docs/RULES.md`, `ARCHITECTURE_MAP.md`, `CURRENT_STATE.md`, `CORRECTNESS.md`, `COVERAGE.md`, `CODE_INDEX.md` | bootstrap SessionStart trong `.claude/settings.json` | settings không đọc, không sửa (luật phiên) |
| 11 tài liệu chuẩn tắc | `audit_docs_information_architecture.CANONICAL_DOMAINS`, test tài liệu, `AGENTS.md` | đổi đường dẫn = đổi hợp đồng của 11 domain |
| `docs/CODE_INDEX.md` | `.claude/hooks/code-index-guard.mjs`, `frontend/src/code-index-sync.test.ts` | hook + test frontend |
| `CORRECTNESS`, `DESIGN_BRIEF`, `RULES`, `STATUS_LEDGER`, `CLASSROOM_AUTH_CONTRACT`, `OBLIGATION_BINDING_CONTRACT`, `CURVED_GEOMETRY_FOUNDATION_DESIGN`, `CURVED_V3_RESEAL_PREFLIGHT`, `GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE`, `REACT_ERROR_BOUNDARY_HARDENING`, `architecture/ASSUMPTION_CERTIFICATE_AMENDMENT` | chú thích trong `backend/app` / `frontend/src` | sửa mã sản phẩm đổi candidate / `sourceFingerprint` (CANDIDATE_REFROZEN = NO) |
| `TEST_TIERS`, `W12_REMAINING`, `COVERAGE`, `legacy/RULES_v0.3` | test trong `frontend/src` và script `frontend/scripts` | không sửa `frontend/src` trong W19 |
| `docs/schemas/semantic_program.schema.json` | `freeze_evaluation_candidate.py`, `export_semantic_program_schema.py`, `test_map_view.py` | danh tính candidate |
| `research/llm_only_paired_baseline_registry.json` | `backend/scripts/collect_llm_only_paired_baseline.py` | giữ chỗ (đã ở `research/`) |
| 180 báo cáo ở gốc + snapshot/tiền đăng ký trong `architecture/` + `research/RECTANGULAR_BASE_PYRAMID_COMPILER_VERTICAL_SLICE.md` | artifact đóng băng, `EVIDENCE_INDEX`, AGENTS.md §4 | R1 — bằng chứng giữ nội dung và đường dẫn (`ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT`) |

Reader duy nhất đổi đường dẫn: `backend/tests/geometry/test_curriculum_coverage.py` (`docs/geometry/` →
`docs/research/`; assertion giữ nguyên).

## 4. Link hỏng và tham chiếu chưa xử lý

Trước / sau: [`verification/LINKS_BEFORE.json`](verification/LINKS_BEFORE.json) ·
[`verification/LINKS_FINAL.json`](verification/LINKS_FINAL.json). Ai còn nhắc đường cũ:
[`verification/OLD_PATH_CONSUMERS_FINAL.json`](verification/OLD_PATH_CONSUMERS_FINAL.json).

- **Tài liệu sống — do W19 gây ra: 0.** Lượt cuối (`LINKS_FINAL.json`): 0 link hỏng trong tài liệu sống; tham chiếu có sẵn ở OPEN_ISSUES (file chưa
  từng commit) đã được ghi lại thành chú thích `NOT_RECOVERABLE`, nên không còn là đường dẫn hỏng.
- **Có từ trước, không sửa (đóng băng / lưu trữ):** 12 link trong báo cáo đóng băng (10 trong
  `evaluation/m17/design-critique/IMPECCABLE_SIMULATION_FIRST_CRITIQUE.md` trỏ mã Tin học đã gỡ; một chữ giữ chỗ
  `path`; một file test không còn) và 16 link trong kế hoạch/spec `legacy/superpowers/` trỏ mã Tin học đã gỡ.
- **Tham chiếu không khôi phục được:** `ISSUE-EVAL-P03-P05-TOKEN-UNKNOWN` trỏ `MACHINE_RAW_OUTPUT.json` — file chưa
  từng được commit (output thô của model không vào git); đã ghi chú `NOT_RECOVERABLE` tại issue.
- **Đường cũ trong artifact đóng băng và bản lưu trữ:** được phép, không sửa; giải qua `MIGRATION_MAP.json`. Link
  tương đối trong file lưu trữ viết cho vị trí cũ (bộ kiểm link giải chúng theo vị trí gốc).

## 5. Unknown và file tạm còn lại

[`diagnostics/TEMP_FILE_INVENTORY.json`](diagnostics/TEMP_FILE_INVENTORY.json).

- File tạm do W19 tạo: 0 còn lại — mọi file W19 tạo ở `D:/tmp` và scratchpad đã xoá theo đường dẫn chính xác sau khi chép phần cần
  giữ vào run folder; worktree `D:/tmp/w19-verify` đã gỡ (`git worktree list` chỉ còn cây chính).
- Giữ: 212 mục `D:/tmp` của các wave trước — 210 `UNKNOWN` (một thư mục có `.git`) và hai bản sao lưu settings không mở —
  `ISSUE-OPS-TMP-LEFTOVERS-UNVERIFIED`; `D:/Documents/projects/docs/evaluation/geometry/HOLDOUT_ACQUISITION_LOG.md`
  (blob `f53864b1…` không khớp phiên bản nào đã commit).
- Giữ, `USED`: kế hoạch `C:/Users/Bunny/.claude/plans/w19-docs-organization.md`, ledger
  `.superpowers/sdd/w19-docs-organization/progress.md` (git-ignored).
- `CLAUDE.md` cục bộ (git-ignored, không commit) — sáu con trỏ đã sửa, hoàn tác được từng dòng:
  1. bảng §0 "tuyên bố khoá luận ↔ bằng chứng ↔ giới hạn": `docs/THESIS_READINESS.md` →
     `docs/research/CLAIM_EVIDENCE_MAP.md` (bảng cũ ở `docs/legacy/research/`);
  2. "Hệ đang chạy … `docs/THESIS_ARCHITECTURE.md`" → `docs/ARCHITECTURE_MAP.md` + `docs/architecture/`, kèm ghi chú
     ảnh chụp `docs/research/thesis/THESIS_ARCHITECTURE.md` và bốn vùng của `docs/`;
  3. dòng `docs/legacy/` + `docs/superpowers/` → `docs/legacy/` nay chứa kế hoạch skill cũ, giai đoạn chuyển đề,
     `CURRENT_STATE_HISTORY.md`, ba bảng tuyên bố cũ;
  4. dòng "CURRENT_STATE.md có nhiều bảng vận hành đã đông cứng" → chỉ giữ trạng thái + con trỏ; nhật ký ở
     `docs/legacy/CURRENT_STATE_HISTORY.md`;
  5. tiêu đề §7 "(`docs/THESIS_*`, `docs/thesis/`, `docs/research/`)" → "(`docs/research/`, gồm `thesis/` và
     `paper/`)";
  6. "Luật cứng ở `docs/THESIS_REFERENCES.md`" → `docs/research/thesis/THESIS_REFERENCES.md`.

## 6. Candidate và cache

`freeze_evaluation_candidate.py --verify` exit 0 — *"Candidate khớp bản đã đóng băng (mã sản phẩm: 110 file,
d3b4cab96c69a09f…)"*; `lock_cache_identity.py --verify` exit 0 — *"Khoá khớp · CACHE_VERSION 110 · môi trường
b1714b566e25c912…"* ([`verification/logs/`](verification/logs/)). `backend/app` và `frontend/src` không đổi trong
cả ba commit.

## 7. Danh tính bằng chứng lịch sử

[`verification/FROZEN_IDENTITY.json`](verification/FROZEN_IDENTITY.json) — **PASS**: 8 439 file `docs/evaluation/**`
và 192 tài liệu đóng băng giữ chỗ trùng blob với `6d0e6321` (digest danh sách đường + blob: trước = sau =
`03447263502a1c18…`); 55 file chuyển trùng blob, 10 đổi có nhật ký, 0 vấn đề; 18 file của
`FROZEN_HISTORICAL_HASHES` khớp (36 file của bộ telemetry: test `test_docs_test_telemetry` trong lượt pytest).

**Sự cố đã xử lý:** lượt pytest toàn bộ ở cây chính đã ghi đè một artifact đóng băng —
`docs/evaluation/geometry/photo-problem-to-scene/second-family-live-measurement-reconciliation/SOURCE_EVIDENCE_INTEGRITY.json`
(trường `note`), qua `backend/scripts/reconcile_second_family_live_measurement.py` do
`test_second_family_live_measurement_reconciliation.py` gọi. W19 phát hiện nó khi stage, khôi phục đúng file ấy về
blob đã commit `4d9fad55`, không commit thay đổi, và đăng ký `ISSUE-OPS-TEST-SUITE-WRITES-FROZEN-EVIDENCE`. Sau đó
`git status --porcelain -- docs/evaluation` (ngoài run W19) rỗng.

## 8. Kiểm chứng

| kiểm | kết quả |
|---|---|
| bộ kiểm tài liệu | PASS (`verification/logs/DOCS_AUDIT.log`) |
| test tài liệu | backend 85/85 (có 4 test guard mới) · frontend 52/52 (6 file đọc tài liệu) · guard DEFAULT_MODE/CACHE_VERSION 8/8
(`verification/logs/DOCS_TESTS.log`, `GUARDS.log`) |
| backend toàn bộ, worktree detached sạch của cây cuối | **7005 passed / 0 failed** (1 skipped, 2 deselected) trên cây `6b926494…` (commit object tạm `3de7bda0`, không thuộc nhánh nào); bản ghi kiểm (log, MANIFEST, kết quả kiểm cuối, số điền vào tài liệu) thêm sau lượt này, không chứa mã (`verification/logs/PYTEST_FULL_DETACHED_CLEAN.log`). Lượt này lại ghi đè `SOURCE_EVIDENCE_INTEGRITY.json` trong worktree bỏ đi — tái lập `ISSUE-OPS-TEST-SUITE-WRITES-FROZEN-EVIDENCE` (`DETACHED_WORKTREE_STATUS_AFTER.log`) |
| backend toàn bộ, cây chính (còn sửa đổi W19 chưa commit) | 7003 qua / 2 đỏ: `test_holdout_readiness_7b::test_bao_cao_da_sinh_va_KHONG_TROI` và `test_second_family_preregistration_evidence_repair::test_10_…` — cả hai đọc `git status` và chỉ chấp nhận favicon bẩn (`verification/logs/PYTEST_FULL_MAIN_TREE_DIRTY.log`) |
| vitest toàn bộ | 1058/1058 |
| `git diff --check` | sạch ở mọi commit |
| staging | danh sách tường minh; favicon không bao giờ được stage |

## 9. Việc kế tiếp đã đăng ký

- `docs/ROADMAP.md` §0 — `NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES`: người dùng chọn họ hình từ bảng ứng viên §0.2
  (G03 chóp tứ giác đều · G04 lăng trụ xiên · G05 đáy đa giác tổng quát · G16 dựng khoảng cách/góc · G06 khối lõm ·
  G17 góc nhị diện, kèm tầng MISSING và chặn chính — snapshot W13); chín chỉnh sửa giao diện §0.1; hồi quy §0.3;
  OCR và nhiều khối để sau (§0.4).
- **Chặn merge:** review người W18 (`NOT_APPROVED`) và `ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET` (đóng bằng
  probe ở biên sản phẩm + bằng chứng backstop chặn đúng danh tính; không coi là minor).
- Quyết định chờ người dùng: W18-H2, W18-H3, W17-H2, W15-H2, W15-H3; và việc sửa AGENTS.md §4 nếu muốn chuyển 180
  báo cáo khỏi gốc `docs/`.

## 10. Trạng thái cây

Sau commit tài liệu: `git status` chỉ còn ` D frontend/public/favicon.svg` (thay đổi của người dùng, giữ nguyên).
Không push, không merge, không amend/rebase.
