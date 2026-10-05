# HANDOFF — cuboid-final-review (lượt chốt của việc cuboid)

Cho người dùng (chủ kho, người duyệt hình) và phiên agent kế tiếp. Chi tiết và số liệu: [`REPORT.md`](REPORT.md).

## Trường bắt buộc

```text
TASK = COMPLETE_DOCS_CLEANUP_AND_CUBOID_BRANCH_ACCEPTANCE (run cuboid-final-review; không đánh số wave)
START_HEAD = 4048ff83d14ad2a1fcd940d127590ca777dbc7cf (END_HEAD của W20)
END_HEAD = SELF — commit cuối của run, thêm results/logs/DOCS_GATES_FINAL.log (cổng tài liệu tại commit tài liệu f4e5b318, worktree sạch: audit PASS, 97 + 22 test tài liệu, tách lịch sử --verify OK, 180 báo cáo lịch sử không đổi); tra bằng git log -1
BRANCH = fix/cuboid-visual-semantic-closure (task slug cuboid-visual-semantic-closure)
ORIGIN_MAIN = a9492ee98ff9dc3302d1ff64465f1c06e9001bce (git ls-remote đầu và cuối run: không đổi; tổ tiên của HEAD; nhánh chưa có trên remote)
DOCS_FILES_REVIEWED = 8812 file (mọi file đã theo dõi dưới docs/ + AGENTS.md, README.md, DESIGN.md): 342 hàng theo file + 146 nhóm bằng chứng (8470 file) — inventory/DOCS_INVENTORY_BEFORE_4048ff83.json; sau run 8819 (thêm 7 file đồng hành) — inventory/DOCS_INVENTORY.json
FILES_KEPT = 8812/8812 file đã theo dõi; sau rà soát 238 FROZEN_KEEP · 41 KEEP_ARCHITECTURAL_HISTORY · 31 KEEP_CURRENT · 38 KEEP_RESEARCH (tính theo hàng file) + 146 nhóm FROZEN_KEEP
FILES_MERGED = 0 file; 119 khối (2960 dòng) của 7 tài liệu sống tách nguyên văn sang 7 file mới trong docs/legacy/ (inventory/HISTORY_SPLIT.json)
FILES_MOVED = 0 (không đường dẫn nào đổi)
FILES_DELETED = 0 file đã theo dõi; 3 file .pyc bị gitignore trong 2 thư mục __pycache__ dưới docs/ (inventory/CLEANUP_LOG.json); ngoài kho 0
FILES_REVIEW_REQUIRED = 1 trong kho (docs/research/thesis/RELATED_WORK_DRAFT.md); ngoài kho giữ nguyên 204 mục D:/tmp + 108 mục .superpowers đã đăng ký ở W20
UNIQUE_INFORMATION_LOST = NONE — mọi khối tách nằm nguyên văn trong file đồng hành (split_history_cfr.py --verify: sha256 từng khối, mọi dòng gốc còn ở một trong hai nơi); sửa tại chỗ chỉ thay con trỏ hỏng hay câu đã cũ, có ghi chú; xoá chỉ là cache sinh lại được
HISTORICAL_ARTIFACTS_BYTE_IDENTICAL = YES — 4048ff83..a1c53cdb: 0/181 báo cáo trong catalog đổi; ngoài run này docs/evaluation chỉ đổi RUN_NAMING.md và hai registry sống (EVALUATION_CANDIDATE.json, CANDIDATE_DIVERGENCE.json); docs/legacy: 7 file thêm + README sửa; PLAN/REPORT của W20 không đổi
DOCS_ROOT_REMAINING_EXCEPTION = 180 báo cáo wave cũ vẫn ở gốc docs/ (catalog đóng docs/evaluation/HISTORICAL_REPORTS.md; luật bất biến của bằng chứng) — giới hạn có chủ đích, ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT = INTENDED_LIMITATION
RUN_NAMING_UPDATED = YES (3f8127fd) — docs/evaluation/RUN_NAMING.md: wave đánh số trong từng việc, việc mới nhánh mới bắt đầu ở W1, định danh đầy đủ <task-slug>-wNN (không W1/W2 trần trong manifest hay chỉ mục), tên thư mục ngắn, ngày/nhánh/commit/candidate trong RUN.json, slug ổn định sau khi xoá nhánh, W1–W20 giữ tên, việc mới chỉ rẽ từ main đã tích hợp và cập nhật; con trỏ ở AGENTS.md §2 và RULES.md §2
LEARNER_REFUSAL_BEFORE = "Đề bài nêu "H là hình chiếu của S lên BD", nhưng chương trình của AlgoSim đặt H bằng toạ độ cho sẵn thay vì dựng điểm này từ quan hệ ấy, nên hệ chưa kiểm chứng được nó đúng là điểm đề nói. AlgoSim dừng lại thay vì đưa ra một đáp số chưa kiểm chứng. Đây là lỗi dựng hình của hệ, đề không cần sửa — em có thể gửi lại để hệ dựng lại." · loại vấn đề "hệ dựng lệch với đề bài"
LEARNER_REFUSAL_AFTER = "Hệ chưa kiểm chứng được H là hình chiếu của S lên BD, vì điểm này được đặt bằng toạ độ thay vì dựng từ quan hệ trong đề. Hệ tạm dừng để tránh đưa ra kết quả chưa kiểm chứng." · loại vấn đề "chưa kiểm chứng được phép dựng" (284a9bfa; tên và quan hệ đọc từ reason_subjects; nhãn chọn bằng reason_code, mã không hiển thị)
BROWSER_REFUSAL_DESKTOP = PASS 6/6 ở 1440×900 (3 ca mã mới + lệch + chưa đối chiếu + phục vụ) — results/BROWSER_REFUSAL_CFR.json, ảnh images/<ca>/desktop/
BROWSER_REFUSAL_MOBILE = PASS 6/6 ở 390×844 — ảnh images/<ca>/mobile/
VERIFICATION_COMMANDS_AND_RESULTS = worktree tách rời sạch 'D:/tmp/cfr space/algo-sim' @ a1c53cdb: node frontend/scripts/full-gate.mjs → FULL_PRODUCT_GATE_PASS (pytest 7079/0, 1 skipped, 2 deselected · vitest 1061/1061 · typecheck + build · demo 5/5 · bề mặt sập 6/6) · diagnostics/cfr_gates.sh a1c53cdb 4048ff83 → candidate + cache verify exit 0, schema ×2 trùng byte d852b47c…, LLM_ONLY, bề mặt mô hình 0 file, catalog 0/181, tách lịch sử --verify OK, diff --check 0, audit tài liệu PASS, harness node 70 pass + 2 skip theo thiết kế · refusal_fixtures_cfr.py + browser_refusal_cfr.mjs → 12/12 (lần 1 bị DIST_CU chặn, build lại) · kiểm kê trước/sau · git status của worktree: file theo dõi không đổi
CANDIDATE_BEFORE = 27c31de6dcd7708ee29bc1b94d7af29147281f991cc97bee7a5434f904564d38 (product commit a4f771b3)
CANDIDATE_AFTER = b2d4187a78ed8bf6df15118edc7e4e251c5f22df536e50b73ac043f108f3b7af (product commit 284a9bfa)
CANDIDATE_REFROZEN_COUNT = 1 — trong worktree sạch D:/tmp/cfr-freeze tại 284a9bfa; không có candidate trung gian; khai ở inputs/CANDIDATE_DIVERGENCE_CORRECTION.json (commit a1c53cdb)
CACHE_VERSION_BEFORE = 111
CACHE_VERSION_AFTER = 111
CACHE_VERSION_REASON = NO_BUMP — 27 hàng corpus W20 qua run_pipeline với mã 4048ff83 và 284a9bfa: 8 envelope được phục vụ trùng byte, 8 envelope từ chối chỉ khác reason_subjects; main.py chỉ cache status "ok" (test_api.py::test_khong_cache_ket_qua_unsupported); lời và nhãn dựng lại ở mỗi phản hồi (diagnostics/cache_proof/CACHE_DECISION_CFR.json, commit 6ec40806)
DEFAULT_MODE = LLM_ONLY
LIVE_GEMINI_REQUESTS = 0
HUMAN_VISUAL_REVIEW = NOT_APPROVED — W18-H1 còn chờ, cộng các thẻ từ chối mới của run này (checklist §1); tự động hoá không ghi APPROVED_BY_USER
PUSH = NO
MERGE = NO
BRANCH_DELETION = NOT_ATTEMPTED (chưa có phê duyệt hình — điều kiện merge của brief và AGENTS.md §2)
USER_FAVICON_DELETION_PRESERVED = YES (không bao giờ stage, restore hay sửa)
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW
NEXT_ACTION = người dùng duyệt hình (§1); khi duyệt: fetch, merge thẳng nhánh vào main, chạy cổng trên cây đã tích hợp, push main và kiểm SHA trên remote, kiểm HEAD nhánh là tổ tiên của origin/main, xoá nhánh đã merge (không xoá ép, không PR, giữ việc xoá favicon). Việc kế tiếp: nhánh mới rẽ từ main đã cập nhật, bắt đầu ở W1 — NEXT_FAMILY_SLICE_WITH_DECIDED_UI_CHANGES (ROADMAP §0)
```

## 1. Checklist duyệt hình

Đường dẫn tính từ gốc kho (`docs/evaluation/geometry/runs/cuboid-final-review/`).

**Thẻ từ chối mới (§17) — mỗi ảnh: lời đúng như dòng LEARNER_REFUSAL_AFTER, dòng "Loại vấn đề: chưa kiểm chứng được
phép dựng", không hình, không đáp số, không câu mời gửi lại, không tràn.**

| | desktop 1440×900 | mobile 390×844 |
|---|---|---|
| hình chiếu đặt bằng toạ độ | `images/cfr_projection_by_coordinates/desktop/refusal.png` | `images/cfr_projection_by_coordinates/mobile/refusal.png` |
| hình chiếu lấy trùng đỉnh A | `images/cfr_projection_alias_vertex/desktop/refusal.png` | `images/cfr_projection_alias_vertex/mobile/refusal.png` |
| trung điểm đặt bằng toạ độ | `images/cfr_midpoint_by_coordinates/desktop/refusal.png` | `images/cfr_midpoint_by_coordinates/mobile/refusal.png` |

**Đối chứng — không được đổi.**

| | desktop | mobile |
|---|---|---|
| lệch đã chứng minh — "hệ dựng lệch với đề bài" | `images/w18_projection_mismatch/desktop/refusal.png` | `images/w18_projection_mismatch/mobile/refusal.png` |
| chưa đối chiếu — "hệ chưa đối chiếu được phép dựng với đề" | `images/w18_unverified/desktop/refusal.png` | `images/w18_unverified/mobile/refusal.png` |
| phục vụ — đáp số 3√6 | `images/w18_projection_line/desktop/served.png` | `images/w18_projection_line/mobile/served.png` |

**W18-H1 (điều kiện merge còn lại từ trước).** Theo [`HANDOFF.md` của run w18](../w18-binding-focus/HANDOFF.md) và ảnh
trong run ấy, gồm W17-H1/W16-H1 (bốn cảnh W14 đổi, `ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`). Run này không đổi
hình hay tương tác nào ngoài thẻ từ chối của §17.

Người ghi kết quả duyệt vào một lớp registry người mới; tự động hoá không bao giờ ghi `APPROVED_BY_USER`.

## 2. Câu hỏi cho người dùng

| id | câu hỏi | làm thế nào nếu đổi |
|---|---|---|
| H-CFR-1 | Các lời CONSTRUCTION khác (dựng lệch điểm/mặt phẳng, số liệu hệ dùng lệch đề) vẫn kết bằng *"Đây là lỗi dựng hình của hệ, đề không cần sửa — em có thể gửi lại để hệ dựng lại."* Bỏ câu mời gửi lại ở đó luôn không? | `backend/app/learner_messages.py` (`_DUOI_LOI_HE`) + test ⇒ đóng băng lại candidate; `CACHE_VERSION` không cần đổi (lời từ chối không được cache). |
| H-CFR-2 | Nhãn viết "chưa kiểm chứng được phép dựng" (chữ thường như các nhãn cùng dòng) và lời viết "toạ độ" (cách viết của kho); brief đề xuất "Chưa…" và "tọa độ". Giữ hay đổi? | `frontend/src/components/SimulationWorkspace.tsx` / `backend/app/learner_messages.py` + test. |
| H-CFR-3 | `docs/research/thesis/RELATED_WORK_DRAFT.md` là bản "công trình liên quan" thứ hai bên cạnh `THESIS_DRAFT` §1.8. Bản nào ở lại? | Việc viết khoá luận — run này không chọn. |
| H-W20-3 | 204 mục `D:/tmp` và 108 mục `.superpowers` chưa chứng minh được là trùng (`ISSUE-OPS-TMP-LEFTOVERS-UNVERIFIED`). | Xoá theo đường dẫn khi có quyết định. |
| H-W20-4 | Tàn dư Tin học trong mã sản phẩm (taxonomy, bề mặt mô hình). | Wave riêng, cần đo lại. |
| giữ từ trước | W18-H2, W18-H3, W17-H2, W15-H2, W15-H3 | Không đổi bởi run này. |

H-W20-1 và H-W20-2 đã xử lý ở run này theo brief (lời và nhãn mới), còn chờ người xem ảnh ở §1.

## 3. Rulings (ledger `.superpowers/sdd/cuboid-final-review/progress.md`)

1. **Tách nguyên văn, không tóm tắt lại.** Phần thời Tin học của 7 tài liệu sống được cắt từ blob gốc, kèm dòng trỏ ở chỗ
   bị trích theo số mục. *Nếu sai:* người tìm mã đã gỡ trong CODE_INDEX phải theo con trỏ §0j sang `legacy/`.
2. **Tiền đăng ký giữ nguyên byte.** 9 link theo máy của hai tiền đăng ký được ghi ở `research/README.md`, không sửa.
   *Nếu sai:* link vẫn theo máy trong hai file niêm phong.
3. **22 bất biến có nơi khoá đã gỡ:** làm cho thấy được và mở issue, không đối chiếu lại. *Nếu sai:* các hàng ấy trông như
   chưa được khoá cho tới wave sau.
4. **GATE-11/12 và hai issue compiler:** ghi dòng đối chiếu, giữ STATUS cho wave di chuyển. *Nếu sai:* trạng thái bi quan
   hơn mã.
5. **Không xoá gì ngoài kho.** Không mục nào được chứng minh mới. *Nếu sai:* dung lượng đĩa còn đó.
6. **Nhãn chữ thường và "toạ độ"** theo quy ước của kho (H-CFR-2). *Nếu sai:* sửa một chuỗi.
7. **Hai test W20 viết lại theo câu chữ mới.** Brief đổi spec của lời người học; giữ phần cốt lõi (quan hệ của đề, việc
   chương trình đã làm, không đổ lỗi cho đề). *Nếu sai:* không — chữ cũ còn trong git.
8. **Đuôi "gửi lại" giữ ở các lời CONSTRUCTION khác** — ngoài thẻ §17 (H-CFR-1).
9. **`CACHE_VERSION` giữ 111** — có chứng minh theo hàng. *Nếu sai:* một envelope `ok` cũ có thể được trả lại, nhưng không
   cái nào khác bản mới.
10. **ponytail-audit:** 7/8 phát hiện được áp dụng. Phát hiện thứ 8 (`exists()` chỉ kiểm trên đĩa) bị đảo lại sau khi đo.

**Tự rà toàn nhánh** (không có subagent — brief cấm): không phát hiện Critical/Important. Deferred minors:
- đuôi "gửi lại" ở các lời CONSTRUCTION khác (H-CFR-1);
- eyebrow "CHƯA DỰNG ĐƯỢC MÔ PHỎNG" dùng chung cho mọi thẻ `geometry_generation_failed` (thuộc lượt duyệt hình);
- frontend so `reason_code` bằng chuỗi literal như các nhánh `error_code` sẵn có.

## 4. File tạm

`diagnostics/TEMP_FILE_INVENTORY.json`:
- năm worktree (trước, đóng băng, kiểm kê gốc, kiểm chứng, cổng tài liệu cuối) đã gỡ không ép;
- 35 file tạm trong `%TEMP%` xoá theo đường dẫn sau khi chép phần cần giữ;
- ledger giữ trong vùng git-ignore.
