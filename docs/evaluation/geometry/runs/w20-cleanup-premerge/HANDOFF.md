# HANDOFF — W20 dọn kho và đóng tính đúng trước merge

Cho người dùng (chủ kho, người duyệt hình) và phiên agent kế tiếp. Chi tiết và số liệu: [`REPORT.md`](REPORT.md).

## Trường bắt buộc

```text
TASK = W20_REPOSITORY_CLEANUP_AND_PREMERGE_CORRECTNESS_CLOSURE
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW
CURRENT_BRANCH = fix/cuboid-visual-semantic-closure
START_HEAD = 2cb4ed8cfecca31d1807af9738aa23534287568e (END_HEAD của W19; tổ tiên của HEAD)
END_HEAD = SELF (commit tài liệu thêm file này; tra bằng git log -1)
ORIGIN_MAIN = a9492ee98ff9dc3302d1ff64465f1c06e9001bce (ref cục bộ = git ls-remote; không đổi suốt W20)
SKILLS_ACTUALLY_USED = gọi qua Skill tool cho W20: superpowers:systematic-debugging (nguyên nhân gốc của cả hai issue), superpowers:writing-plans (PLAN.md) · đã gọi qua Skill tool trước đó trong CÙNG phiên (W18/W19) và áp dụng cho W20, không gọi lại: superpowers:executing-plans (ledger + rulings), superpowers:test-driven-development (đỏ trước mọi sửa), superpowers:verification-before-completion, ponytail:ponytail-review (rà diff sản phẩm: không có gì cắt), andrej-karpathy-skills:karpathy-guidelines · áp dụng thủ công: code-reviewer.md của superpowers:requesting-code-review (tự rà toàn nhánh; brief cấm subagent)
AGENTS_RULES_UPDATED = YES (a36f3e97) — AGENTS.md §2 merge/push có điều kiện; §4 bốn luật (bằng chứng đông cứng · nháp agent · dọn có kiểm · test không ghi bằng chứng đông cứng · không ghi APPROVED_BY_USER); RULES.md §1 CODE/TESTS; luật bảo toàn thay đổi của người dùng không đổi
FILES_DELETED = 64 (inventory/DELETION_LOG.json): 46 gói review + 10 brief trong .superpowers/, 7 file + 1 bản clone trong D:/tmp
FILES_KEPT = 51 lớp KEEP_*: docs/legacy/superpowers 18/18 (13 KEEP_ARCHITECTURAL_HISTORY, 3 KEEP_RESEARCH_EVIDENCE, 2 KEEP_ACTIVE) · .superpowers 32 (29 brief W14, ledger W20, bản sao CLAUDE.md W19, .gitignore) · CLAUDE.md cục bộ 1
FILES_REVIEW_REQUIRED = 314 (giữ nguyên, chờ quyết định): .superpowers 108 + D:/tmp 204 (gồm hai backup settings, không mở) + mục W19 ngoài kho 2 (kế hoạch W19, HOLDOUT_ACQUISITION_LOG.md) — theo inventory/CLEANUP_INVENTORY.json
UNIQUE_INFORMATION_LOST = NONE — mỗi mục xoá tái tạo được từng byte từ git (gói review: lệnh ghi trong DELETION_LOG), trùng một blob reachable (đường dẫn + commit ghi lại), rỗng, hoặc là bản clone mà HEAD và mọi ref đều có trong kho
LITERAL_TARGET_PROBE_BEFORE = 20/27 khớp nhãn (results/LITERAL_TARGET_PROBE_before-r2_2cb4ed8c.json): L12–L14 và L16–L18 PHỤC VỤ (L14 sai: 2√14 thay vì 3√6; L17 phục vụ SA = 6 thay cho SH)
LITERAL_TARGET_PROBE_AFTER = 26/27 tại 65c90bde và 5fbb397b (results/LITERAL_TARGET_PROBE_{after_65c90bde,final_5fbb397b}.json, trùng nhau); hàng còn lại C7 bị cổng miền chặn — ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE, ghi ở amendment_1 TRƯỚC bản sửa; đối chứng thay thế C9 phục vụ
CONSTRUCTION_BINDING_RESULT = RESOLVED — DEFINED_BY_COORDINATES / CONSTRUCTION_REPLACED_BY_COORDINATES (amendment §17), từ chối mọi vùng, nguyên nhân CONSTRUCTION; census 179 hàng W14–W18 không đổi tuyến, AC2 18/18; quét 527 chương trình: 1 hàng (L16 của W20); tiêm lỗi FL1–FL7 bắt, FL8/FL9 phòng thủ nhiều lớp
TEST_WRITES_FROZEN_EVIDENCE_RESULT = RESOLVED — run_reconciliation(out_dir) bắt buộc thư mục ra, từ chối thư mục đông cứng và thư mục con; test tmp_path + hash + git status; lượt backend đầy đủ ở cây chính để git status y nguyên; FE1–FE3 bắt
HISTORICAL_ARTIFACTS_BYTE_IDENTICAL = YES — 2cb4ed8c..5fbb397b: ngoài run W20, docs/evaluation chỉ đổi hai registry sống (EVALUATION_CANDIDATE.json, CANDIDATE_DIVERGENCE.json); 0/181 báo cáo lịch sử trong catalog đổi; worktree kiểm chứng không đổi file đã theo dõi nào sau mọi lượt chạy
VERIFICATION_COMMANDS_AND_RESULTS = worktree tách rời sạch 'D:/tmp/w20 space/algo-sim' @ 5fbb397b: node frontend/scripts/full-gate.mjs → FULL_PRODUCT_GATE_PASS (pytest 7077/0, 1 skipped, 2 deselected · vitest 1058/1058 · typecheck + build · demo · bề mặt sập 6/6) · diagnostics/w20_gates.sh → candidate + cache verify exit 0, schema ×2 trùng byte d852b47c…, git status không đổi, LLM_ONLY, bề mặt mô hình 0 file, diff --check 0, audit tài liệu PASS, harness node 70 pass + 2 skip theo thiết kế · probe final 26/27 · run_fault_injections_w20.py _r3 @ aa036c42 (backend + frontend trùng 5fbb397b) → 10/10 phép tiêm cần bắt đều bắt, 2 phép phòng thủ nhiều lớp không đỏ
MEASUREMENT_COMMIT_SHA = 5fbb397b7d485de183526451ae9003631c395d94 (kiểm chứng có thẩm quyền) · probe/census/chứng minh cache đo ở 65c90bde880c80173f8f39be9ef2ef05e0116a04 (mã sản phẩm của bản sửa)
CANDIDATE_BEFORE = d3b4cab96c69a09f6ba1b82ac5ca1ee994abed3430d0f277fa30c6d7f328d57e
CANDIDATE_AFTER = 27c31de6dcd7708ee29bc1b94d7af29147281f991cc97bee7a5434f904564d38 (product commit a4f771b3)
CANDIDATE_REFROZEN_COUNT = 2 — bedb1040 → 2a15102b… (trung gian), rồi a4f771b3 → 27c31de6… sau tự rà soát (F1: chỉ comment); cả hai trong worktree sạch, khai ở inputs/CANDIDATE_DIVERGENCE_CORRECTION.json
CACHE_VERSION_BEFORE = 110
CACHE_VERSION_AFTER = 111
CACHE_VERSION_REASON = served → rejected: sáu yêu cầu W18 từng phục vụ vẫn HIT dưới 110 dù W20 từ chối (diagnostics/PROOF_CACHE_ROW_W20.json); bump làm cả sáu trượt; vân tay bề mặt mô hình b1714b566e25c912 không đổi
DEFAULT_MODE = LLM_ONLY
LIVE_GEMINI_REQUESTS = 0
LIVING_DOCS_UPDATED = AGENTS.md, docs/RULES.md, docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md (§17), docs/OPEN_ISSUES.md, docs/CODE_INDEX.md, docs/ARCHITECTURE_MAP.md, docs/research/CLAIM_EVIDENCE_MAP.md (C6), docs/CURRENT_STATE.md, docs/AI_CONTEXT_BUNDLE.md, docs/ROADMAP.md, docs/STATUS_LEDGER.md, docs/EVIDENCE_INDEX.md, README.md, docs/README.md, docs/evaluation/README.md · bản thảo khoá luận KHÔNG sửa
BROKEN_LINK_COUNT = 0 (audit tài liệu tại 5fbb397b; kiểm lại sau commit tài liệu — xem tin nhắn kết thúc phiên)
HUMAN_VISUAL_REVIEW = NOT_APPROVED (W18-H1; W20 không đổi giao diện)
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
BRANCH_DELETION_RESULT = NOT_ATTEMPTED (chưa có phê duyệt hình ảnh — điều kiện merge của brief và AGENTS.md §2)
USER_FAVICON_DELETION_PRESERVED = YES (không bao giờ stage, restore hay sửa)
NEXT_ACTION = người dùng duyệt hình W18-H1 (điều kiện merge còn lại) · song song: NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES (CANONICAL_NEXT_ACTION, ROADMAP §0)
```

## 1. Việc chờ người dùng

| id | câu hỏi | làm thế nào |
|---|---|---|
| **W18-H1** (chặn merge) | Duyệt hình W18: hình mặc định gọn, chip "Hiện tất cả", chọn đại lượng kèm chuỗi số, ô soi là nơi giải thích duy nhất, lời giải thu gọn, nhân chứng khoảng cách, các thẻ từ chối W18; kèm W17-H1/W16-H1 (bốn cảnh W14 đổi). | Theo [`HANDOFF.md` của run w18](../w18-binding-focus/HANDOFF.md) và ảnh trong run ấy. Người ghi vào một lớp registry người mới; tự động hoá không bao giờ ghi `APPROVED_BY_USER`. |
| H-W20-1 | Câu chữ lời từ chối mới, ví dụ L14: *"Đề bài nêu "H là hình chiếu của S lên BD", nhưng chương trình của AlgoSim đặt H bằng toạ độ cho sẵn thay vì dựng điểm này từ quan hệ ấy, nên hệ chưa kiểm chứng được nó đúng là điểm đề nói. AlgoSim dừng lại thay vì đưa ra một đáp số chưa kiểm chứng. Đây là lỗi dựng hình của hệ, đề không cần sửa — em có thể gửi lại để hệ dựng lại."* Giữ hay sửa? | Sửa `backend/app/learner_messages.py::_msg_toa_do_thay_dung` ⇒ đóng băng lại candidate. |
| H-W20-2 | Thẻ từ chối hiện loại vấn đề "hệ dựng lệch với đề bài" cho mọi nguyên nhân CONSTRUCTION, kể cả mã mới (toạ độ có thể đúng). Cần nhãn loại riêng không? | Sửa `frontend/src/components/SimulationWorkspace.tsx` (`nhanLoai`) + test thẻ từ chối ⇒ đóng băng lại, cổng trình duyệt. |
| H-W20-3 | 204 mục còn lại ở `D:/tmp` và 108 mục `REVIEW_REQUIRED` trong `.superpowers/` (báo cáo subagent, ledger, log, brief M16, nháp brainstorm) không chứng minh được là trùng. Bỏ hay giữ? | Danh sách đầy đủ ở `inventory/CLEANUP_INVENTORY.json`; xoá theo đường dẫn chính xác khi có quyết định (`ISSUE-OPS-TMP-LEFTOVERS-UNVERIFIED`). |
| H-W20-4 | Tàn dư danh mục Tin học trong mã sản phẩm (ví dụ `tree_traversal.*` trong `obligations.py::SEMANTIC_PRESCRIBED_PROCEDURES`). Có mở một wave gỡ không? | Đụng taxonomy của candidate và bề mặt mô hình: cần đo lại; quan sát, chưa phải issue. |
| giữ từ trước | W18-H2 (ô soi lặp dòng giá trị), W18-H3 (`ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE` — cũng là lý do hàng C7), W17-H2, W15-H2, W15-H3, `ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT` | Không đổi bởi W20. |

**Khi W18-H1 được duyệt** (AGENTS.md §2): kiểm lại `origin/main`, merge thẳng nhánh vào `main`, push `main`, xoá nhánh đã
merge; không force-push, không rebase.

## 2. Lát cắt kế tiếp đề xuất (đối chiếu với mã hiện tại)

**Đề xuất: G03 — chóp tứ giác đều**, làm cùng chín chỉnh sửa giao diện đã chốt.
- **Vì sao.** Đây là dạng đề rất phổ biến, nay bị từ chối trong vùng đa diện khi đề không cho toạ độ:
  - bộ đọc ràng buộc nuốt chữ "đều" mà không phát ràng buộc nào
    (`backend/app/simulation/semantic_program/shape_constraint.py`, `_TU_BI_BO`);
  - bảng xác định C1 của chứng chỉ giả định không có chóp đều;
  - chứng chỉ trả `UNDETERMINED`.
- **Phép dựng có sẵn.** Chân đường cao ở tâm đáy dựng được bằng `intersect_line_line` của hai đường chéo.
- **Giới hạn phải nói thẳng.** Toạ độ kernel là ℚ³ (`geometry/exact.py`; căn chỉ dùng cho đại lượng đo):
  - biến thể cho chiều cao hữu tỉ làm được;
  - "cạnh bên b, cạnh đáy a" với chiều cao vô tỉ phải bị từ chối trung thực, hoặc mở L06 bằng một quyết định riêng.
- **Các tầng phải đóng** (theo `docs/ROADMAP.md` §0.2):
  - L01–L05: ràng buộc `regular_pyramid` (đỉnh trên tâm đáy, cạnh bên bằng nhau);
  - L09: bước dựng tâm;
  - mục C1 có chứng minh tính duy nhất;
  - L16: bằng chứng trình duyệt desktop + mobile;
  - corpus gắn nhãn trước;
  - hồi quy §0.3.
- **Phương án thay thế: G16 dựng khoảng cách/góc.** Tuyến LLM đã phục vụ khoảng cách điểm → đường/mặt kèm nhân chứng
  chính xác (W18). Phần thiếu: góc theo độ không grounding (L03), chưa có cung góc (L11).
- **Chín chỉnh sửa giao diện** (`docs/ROADMAP.md` §0.1):
  1. ẩn mặc định card Kết quả;
  2. mọi kết quả qua nút chọn đại lượng + một ô chi tiết;
  3. nút "Các bước dựng" mở danh sách cạnh trên desktop;
  4. panel mobile thu gọn được;
  5. chọn bước đồng bộ hình, dòng thời gian và phát lại;
  6. tách bước dựng khỏi bước tính;
  7. chọn độ dài tô sáng đoạn, chọn diện tích tô sáng vùng;
  8. bớt dòng mô tả lặp;
  9. tách cuộn của bộ đo khỏi cuộn của người học.
- **Nhánh đề xuất:** `feat/regular-square-pyramid-and-ui-requests`. Tạo từ `main` sau khi nhánh này merge; nếu chưa
  merge, tạo từ END_HEAD của W20.
- **Người dùng chọn họ.** ROADMAP §0 không chọn thay.

## 3. Rulings (ledger `.superpowers/sdd/w20-cleanup-premerge/progress.md`)

1. **Một thẩm quyền.** Luật nằm ở `construction_binding`; không mở rộng grounding ⑦ — cả hai mã đều không gửi đi sửa.
   *Nếu sai:* hai lời khác nhau cho cùng một lớp lỗi (trung điểm bị grounding chặn, hình chiếu bị binding chặn).
2. **Mã mới** `CONSTRUCTION_REPLACED_BY_COORDINATES` thay vì dùng lại `CONSTRUCTION_NOT_TEXT_BOUND`. *Nếu sai:* thêm
   một mã ở bảng nguyên nhân, tập không sửa và lời người học.
3. **12 đỏ ở cây chính trước đóng băng** đều là candidate cũ hoặc cây bẩn; từng cái đã đọc. *Nếu sai:* một hồi quy thật
   bị che — đã loại trừ bằng T3 sạch ở `5fbb397b`.
4. **`docs/legacy/superpowers/` giữ 18/18.** Mỗi file được tài liệu sống trích hoặc giải thích mã còn chạy. *Nếu sai:*
   còn nhiễu grep.
5. **Đóng băng lần hai** thay vì để trích dẫn luật sai trong mã sản phẩm. *Nếu sai:* thêm một lần đóng băng có khai.
6. **Bảng tiêm lỗi hỏng cú pháp** (lỗi của W20), sửa ở `aa036c42`; r3 chạy ở commit có mã sản phẩm trùng `5fbb397b`.
   *Nếu sai:* không ảnh hưởng sản phẩm.

Deferred minors: không có.

## 4. File tạm

`diagnostics/TEMP_FILE_INVENTORY.json`: ba worktree đóng băng/"trước" và worktree kiểm chứng đã gỡ (không ép); file
tạm trong `%TEMP%` xoá sau khi chép phần cần giữ vào `results/`; ledger giữ trong vùng git-ignore.
