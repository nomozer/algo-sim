# HANDOFF — cuboid-merge (duyệt hình và tích hợp nhánh cuboid vào main)

Cho người dùng và phiên agent kế tiếp. Gói duyệt: [`REVIEW.md`](REVIEW.md).

## Trường bắt buộc

```text
TASK = CUBOID_ACCEPTANCE_AND_DIRECT_MAIN_INTEGRATION (run cuboid-merge; không đánh số wave)
START_HEAD = 37b23f04ce07a1e57a1c974af56316447205c571
END_HEAD = SELF — commit cuối của run trên nhánh (tra bằng git log -1)
BRANCH = fix/cuboid-visual-semantic-closure
PRODUCT_COMMIT_SHA = 284a9bfad7e815f7a2228eca89736f714b53c26c (không đổi trong run này)
CANDIDATE_HASH = b2d4187a78ed8bf6df15118edc7e4e251c5f22df536e50b73ac043f108f3b7af
VISUAL_EVIDENCE_TRANSFER_RESULT = TRANSFERRED — fixture W18 tái sinh offline trùng từng byte bản đã đo (manifest 10dbe2de…); 32/32 fixture ở 37b23f04 chỉ khác product_commit_sha/product_tree_sha; frontend chỉ đổi trong UnsupportedNotice (mã từ chối không fixture W18 nào mang) + một trường kiểu; viewport/camera/kỳ vọng không đổi (results/logs/TRANSFER.log, results/FIXTURE_TRANSFER.json)
NEW_CAPTURES_IF_ANY = NONE
HUMAN_VISUAL_REVIEW = APPROVED_BY_USER — A–E ACCEPTED, F ACCEPTED (F1–F5 hoãn, vẫn mở), lời người dùng 2026-10-05
APPROVAL_REFERENCE = APPROVAL.md (nguyên văn + phạm vi; gói REVIEW.md @ 1e03ef82, candidate b2d4187a)
LOCAL_MAIN_SHA = a9492ee98ff9dc3302d1ff64465f1c06e9001bce
REMOTE_MAIN_SHA = a9492ee98ff9dc3302d1ff64465f1c06e9001bce (git fetch --prune + ls-remote đầu run)
CANDIDATE_VERIFY = PASS (b2d4187a…, 110 file; worktree tách rời sạch D:/tmp/cmerge-verify tại 1e03ef82, đã gỡ) — results/logs/GATES_FINAL.log
CACHE_VERIFY = PASS (CACHE_VERSION 111, môi trường b1714b566e25c912); DEFAULT_MODE LLM_ONLY; bề mặt mô hình 0 file đổi; byte sản phẩm 0 đổi so với 37b23f04 và 284a9bfa
DOCS_VERIFICATION = PASS — audit tài liệu PASS (0 link chết); pytest tài liệu 110 passed; vitest tài liệu 22/22; git diff --check exit 0; git status 0 trước/sau. Danh tính lịch sử: docs/legacy 0 đổi, 0/180 báo cáo lịch sử đổi, ngoài run chỉ docs/evaluation/README.md (điều hướng sống). split_history_cfr.py --verify giữ nguyên kết quả FAIL (mệnh đề 3); phạm vi: đúng 25 dòng cuboid-acceptance cố ý thay, khối + hash nguyên vẹn (split_scope_cacc.py OK)
PUSH_RESULT = NOT_ATTEMPTED
MERGE_RESULT = NOT_ATTEMPTED
BRANCH_DELETION_RESULT = NOT_ATTEMPTED
CI_RESULT = NOT_APPLICABLE (kho không có cấu hình CI)
USER_FAVICON_DELETION_PRESERVED = YES
LIVE_GEMINI_REQUESTS = 0
FINAL_DECISION = APPROVED_INTEGRATION_IN_PROGRESS (kết quả merge/push/xoá nhánh ghi ở commit sau trên main)
NEXT_ACTION = fast-forward main, kiểm cây tích hợp, push main, xoá nhánh local
```

## Khi có phê duyệt tường minh

Ghi nguyên văn lời phê duyệt, phạm vi (nhóm nào, gói bằng chứng nào) và tham chiếu vào một lớp tài liệu mới; rồi:
fetch lại; xác minh `main` và nhánh không có commit chưa đánh giá; chuyển sang `main` giữ nguyên việc xoá favicon;
fast-forward (lịch sử tuyến tính: `main` = `a9492ee9` là tổ tiên của nhánh); kiểm cây tích hợp (candidate, cache,
`LLM_ONLY`, tài liệu); `git push origin main` không force; kiểm SHA remote và HEAD nhánh là tổ tiên của `origin/main`;
`git branch -d` nhánh local; nhánh remote không tồn tại nên không có gì để xoá. Không PR. Sau đó
`FINAL_DECISION = MERGED_AND_PUSHED`, `NEXT_ACTION = SELECT_AND_START_NEXT_FAMILY_W01` (việc mới rẽ từ `main` đã
cập nhật, bắt đầu W1; đề xuất chóp tứ giác đều, chưa chọn).

Nếu có NEEDS_CHANGES: ghi lý do, không merge; chỉnh sửa thuộc một việc riêng.
