# HANDOFF — cuboid-merge (duyệt hình và tích hợp nhánh cuboid vào main)

Cho người dùng và phiên agent kế tiếp. Gói duyệt: [`REVIEW.md`](REVIEW.md).

## Trường bắt buộc

```text
TASK = CUBOID_ACCEPTANCE_AND_DIRECT_MAIN_INTEGRATION (run cuboid-merge; không đánh số wave)
START_HEAD = 37b23f04ce07a1e57a1c974af56316447205c571
END_HEAD = SELF — commit ghi kết quả tích hợp trên main (tra bằng git log -1 origin/main); nhánh dừng ở c282a5f398ea5ed19e311dec10a8c5c2bc4d02ec
BRANCH = fix/cuboid-visual-semantic-closure
PRODUCT_COMMIT_SHA = 284a9bfad7e815f7a2228eca89736f714b53c26c (không đổi trong run này)
CANDIDATE_HASH = b2d4187a78ed8bf6df15118edc7e4e251c5f22df536e50b73ac043f108f3b7af
VISUAL_EVIDENCE_TRANSFER_RESULT = TRANSFERRED — fixture W18 tái sinh offline trùng từng byte bản đã đo (manifest 10dbe2de…); 32/32 fixture ở 37b23f04 chỉ khác product_commit_sha/product_tree_sha; frontend chỉ đổi trong UnsupportedNotice (mã từ chối không fixture W18 nào mang) + một trường kiểu; viewport/camera/kỳ vọng không đổi (results/logs/TRANSFER.log, results/FIXTURE_TRANSFER.json)
NEW_CAPTURES_IF_ANY = NONE
HUMAN_VISUAL_REVIEW = APPROVED_BY_USER — A–E ACCEPTED, F ACCEPTED (F1–F5 hoãn, vẫn mở), lời người dùng 2026-10-05
APPROVAL_REFERENCE = APPROVAL.md (nguyên văn + phạm vi; gói REVIEW.md @ 1e03ef82, candidate b2d4187a)
LOCAL_MAIN_SHA = c282a5f398ea5ed19e311dec10a8c5c2bc4d02ec sau fast-forward (trước: a9492ee9); rồi commit ghi kết quả này
REMOTE_MAIN_SHA = c282a5f398ea5ed19e311dec10a8c5c2bc4d02ec (ls-remote sau push; HEAD nhánh là tổ tiên của origin/main; origin/main...main = 0 0); commit ghi kết quả push tiếp
CANDIDATE_VERIFY = PASS (b2d4187a…, 110 file; worktree tách rời sạch D:/tmp/cmerge-verify tại 1e03ef82, đã gỡ) — results/logs/GATES_FINAL.log
CACHE_VERIFY = PASS (CACHE_VERSION 111, môi trường b1714b566e25c912); DEFAULT_MODE LLM_ONLY; bề mặt mô hình 0 file đổi; byte sản phẩm 0 đổi so với 37b23f04 và 284a9bfa
DOCS_VERIFICATION = PASS — audit tài liệu PASS (0 link chết); pytest tài liệu 110 passed; vitest tài liệu 22/22; git diff --check exit 0; git status 0 trước/sau. Danh tính lịch sử: docs/legacy 0 đổi, 0/180 báo cáo lịch sử đổi, ngoài run chỉ docs/evaluation/README.md (điều hướng sống). split_history_cfr.py --verify giữ nguyên kết quả FAIL (mệnh đề 3); phạm vi: đúng 25 dòng cuboid-acceptance cố ý thay, khối + hash nguyên vẹn (split_scope_cacc.py OK)
PUSH_RESULT = PUSHED — git push origin main: a9492ee9..c282a5f3 main -> main (không force)
MERGE_RESULT = FAST_FORWARD — main a9492ee9 → c282a5f3 (git update-ref với CAS a9492ee9, vì git switch để lại 61 file do tài khoản Windows CodexSandboxOffline sở hữu, xoá không được nhưng trùng blob của nhánh; không đổi quyền; index đồng bộ, working tree khôi phục từ HEAD trừ favicon, 64 file chỉ main có trùng blob a9492ee9 xoá theo đường dẫn chính xác); cổng cây tích hợp: results/logs/INTEGRATED_MAIN_GATES.log
BRANCH_DELETION_RESULT = LOCAL_DELETED (git branch -d, was c282a5f3; không worktree nào dùng) · REMOTE_NOT_PRESENT (nhánh chưa từng có trên origin)
CI_RESULT = NOT_APPLICABLE (kho không có cấu hình CI)
USER_FAVICON_DELETION_PRESERVED = YES
LIVE_GEMINI_REQUESTS = 0
FINAL_DECISION = MERGED_AND_PUSHED
NEXT_ACTION = SELECT_AND_START_NEXT_FAMILY_W01 (việc mới rẽ từ main đã cập nhật, task slug mới, bắt đầu W1; chóp tứ giác đều là đề xuất, chưa chọn)
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
