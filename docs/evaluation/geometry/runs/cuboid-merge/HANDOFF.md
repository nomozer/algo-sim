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
HUMAN_VISUAL_REVIEW = NOT_APPROVED — chờ trả lời A–F của REVIEW.md
APPROVAL_REFERENCE = NONE
LOCAL_MAIN_SHA = a9492ee98ff9dc3302d1ff64465f1c06e9001bce
REMOTE_MAIN_SHA = a9492ee98ff9dc3302d1ff64465f1c06e9001bce (git fetch --prune + ls-remote đầu run)
CANDIDATE_VERIFY = xem results/logs/GATES_FINAL.log
CACHE_VERIFY = xem results/logs/GATES_FINAL.log
DOCS_VERIFICATION = xem results/logs/GATES_FINAL.log
PUSH_RESULT = NOT_ATTEMPTED
MERGE_RESULT = NOT_ATTEMPTED
BRANCH_DELETION_RESULT = NOT_ATTEMPTED
CI_RESULT = NOT_APPLICABLE (kho không có cấu hình CI)
USER_FAVICON_DELETION_PRESERVED = YES
LIVE_GEMINI_REQUESTS = 0
FINAL_DECISION = AWAITING_USER_VISUAL_APPROVAL
NEXT_ACTION = người dùng trả lời ACCEPTED hoặc NEEDS_CHANGES cho A–F của REVIEW.md
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
