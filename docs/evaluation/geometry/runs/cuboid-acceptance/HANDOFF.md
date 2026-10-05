# HANDOFF — cuboid-acceptance (hồ sơ nghiệm thu của việc cuboid)

Cho người dùng (chủ kho, người duyệt hình) và phiên agent kế tiếp. Chi tiết: [`REPORT.md`](REPORT.md); bảng đối
chiếu từng bất biến: [`results/INVARIANT_RECONCILIATION.json`](results/INVARIANT_RECONCILIATION.json).

## Trường bắt buộc

```text
TASK = CUBOID_INVARIANT_RECONCILIATION_AND_MERGE_HANDOFF (run cuboid-acceptance; không đánh số wave)
START_HEAD = 903e874c291aa99137074ddff2a6688bc5a84b42
END_HEAD = SELF — commit cuối của run, thêm results/logs/ (kiểm chứng tại commit tài liệu f93408b7, worktree sạch); tra bằng git log -1
BRANCH = fix/cuboid-visual-semantic-closure (task slug cuboid-visual-semantic-closure)
INVARIANTS_TOTAL = 24 (ARCHITECTURE_MAP §5: #1–#12, #14–#16, #18, #20–#26, #29 — đính chính số 22 của cuboid-final-review: #9, #12 thừa hưởng con trỏ chết qua "như trên")
HISTORICAL_NOT_APPLICABLE = 14 (#4, #5, #6, #7, #10, #12, #15, #16, #18, #20, #23, #24, #25, #26)
CURRENT_ENFORCED = 9 (#1, #2, #3, #8, #9, #11, #21, #22, #29)
CURRENT_UNVERIFIED = 1 (#14 live eval opt-in — dò tĩnh thấy hai script gọi live không cần opt-in; chưa tái hiện vì cần lượt gọi thật; ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM)
VIOLATED = 0
MERGE_BLOCKERS = NONE từ đối chiếu bất biến (#14 là công cụ dev đã có trên main, ngoài đường sản phẩm); điều kiện merge còn thiếu: phê duyệt hình tường minh (§1)
PRODUCT_BYTES_CHANGED = NO (backend/app, frontend/src: 0 file đổi so với 903e874c và so với 284a9bfa — commit sản phẩm của candidate)
CANDIDATE_VERIFY / CACHE_VERIFY = PASS (b2d4187a…, 110 file) / PASS (CACHE_VERSION 111, môi trường b1714b566e25c912) — worktree tách rời sạch D:/tmp/cacc-verify tại f93408b7; LLM_ONLY; bề mặt mô hình 0 file đổi; hai bản lược đồ trùng byte
DOCS_VERIFICATION = PASS — results/logs/DOCS_GATES_FINAL.log: audit tài liệu PASS (0 link chết, 0 đường dẫn cũ trong CODE_INDEX); pytest tài liệu 110 passed; vitest tài liệu 22/22; con trỏ §5 39/39 hàng, 0 file thiếu; git diff --check 903e874c..f93408b7 exit 0; git status 0 trước và sau. results/logs/INVARIANT_CHECKS_FINAL.log: con trỏ hiện hành đủ, pytest 349 passed, vitest 9 file / 138 test passed, dò #14 đúng hai script
HISTORICAL_ARTIFACTS_BYTE_IDENTICAL = YES — docs/evaluation ngoài run này 0 file đổi; docs/legacy 0; báo cáo lịch sử trong catalog 0/180 (link thứ 181 là docs/EVIDENCE_INDEX.md, tài liệu sống); khối tách lịch sử của cuboid-final-review vẫn nguyên văn, hash khớp HISTORY_SPLIT.json. split_history_cfr.py --verify báo FAIL ở mệnh đề "mọi dòng BASE còn ở một trong hai nơi": đúng 25 dòng do run này cố ý thay (24 hàng §5 + 1 hàng CODE_INDEX), 0 dòng khác — giải thích ở split_scope_cacc.py, ghi trong cùng log
HUMAN_VISUAL_REVIEW / APPROVAL_REFERENCE = NOT_APPROVED / NONE — tự động hoá không ghi APPROVED_BY_USER; việc gửi brief này không phải phê duyệt
LOCAL_MAIN_SHA / REMOTE_MAIN_SHA = a9492ee98ff9dc3302d1ff64465f1c06e9001bce / a9492ee98ff9dc3302d1ff64465f1c06e9001bce (fetch --prune + ls-remote đầu run; HEAD đi trước 269, sau 0)
PUSH_RESULT / MERGE_RESULT / CI_RESULT = NOT_ATTEMPTED / NOT_ATTEMPTED / NOT_APPLICABLE (kho không có cấu hình CI; không push)
BRANCH_DELETION_RESULT = NOT_ATTEMPTED (chưa merge)
USER_FAVICON_DELETION_PRESERVED = YES (không stage, restore hay sửa)
LIVE_GEMINI_REQUESTS = 0
SKILLS = gọi trong run: superpowers:verification-before-completion · áp dụng, không gọi lại (đã nạp trước trong phiên): systematic-debugging (code-index-sync đỏ; HISTORY_SPLIT FAIL), karpathy-guidelines · không dùng: ponytail-review (diff là tài liệu + script chẩn đoán chỉ đọc) · subagent: 0
TEMP_FILES = worktree D:/tmp/cacc-verify gỡ bằng git worktree remove (sạch, không --force); thư mục tạm của phiên: 4 log (bản có thẩm quyền chép vào results/logs/) + 2 script trợ giúp sửa/kiểm bảng §5 — xoá theo tên chính xác khi kết thúc; ledger .superpowers/sdd/cuboid-acceptance/progress.md (gitignore) giữ lại
FINAL_DECISION = READY_FOR_HUMAN_VISUAL_REVIEW
NEXT_ACTION = người dùng duyệt hình theo §1 và ghi ACCEPTED hoặc NEEDS_CHANGES; khi có phê duyệt tường minh: §3 (merge thẳng vào main, không PR); sau đó việc mới theo §4
```

## 1. Checklist duyệt hình

Mỗi mục: ghi **ACCEPTED** hoặc **NEEDS_CHANGES** kèm lý do cụ thể (ảnh nào, chỗ nào, mong gì). Đường dẫn tính từ
`docs/evaluation/geometry/runs/`. Run này không chụp ảnh mới và không chép ảnh: mọi ảnh dưới đây là ảnh nguồn của
run đã đo, kèm commit đo và candidate của nó.

### 1.1 W18-H1 — cảnh phục vụ (đo ở `0ca3accf`, candidate `d3b4cab9`)

Sáu họ: `triangular-pyramid`, `rectangular-pyramid`, `triangular-prism`, `cuboid`, `cube`, `cross-section`, mỗi
họ hai khổ `desktop` (1440×900) và `mobile` (390×844), trong `w18-binding-focus/images/<họ>/`.

| # | xem gì | ảnh | ghi |
|---|---|---|---|
| a | **Mặc định gọn**: chỉ tên điểm + dữ kiện đề; một chip "Hiện tất cả" | `<khổ>/neutral_final.png`, `<khổ>/show_all.png` | |
| b | **Chọn đại lượng**: chọn độ dài/diện tích/thể tích thì hiện nhãn và chuỗi số của nó; ô soi là nơi giải thích duy nhất (công thức, dữ kiện, đầu vào trực tiếp) | `<khổ>/selected_<loại>.png` + `<khổ>/detail_<loại>.png` | |
| c | **Nhân chứng khoảng cách**: đoạn nét đứt tới chân chính xác + dấu góc vuông, chỉ khi nhãn khoảng cách hiện | `cross-section/<khổ>/selected_distance.png`, `detail_distance.png`; ca 3√6: `cuboid-final-review/images/w18_projection_line/<khổ>/served.png` | |
| d | **Lời giải**: thu gọn mặc định, mở thì ô soi bỏ công thức | `<khổ>/solution_neutral_final.png`, `<khổ>/solution_expanded.png` | |
| e | **Formation / phát lại**: hình dựng theo bước, tô sáng và trả lại | `<họ>/FILMSTRIP.png`, `desktop/formation/`, `mobile/formation/`, `<khổ>/causal_selected.png` → `causal_restored.png` | |
| f | **Desktop / mobile**: bố cục, không tràn, ô soi bên phải (desktop) hoặc dưới (mobile) | cặp `desktop/` · `mobile/` của từng ảnh trên | |
| g | **Bốn cảnh W14 đổi** (W17-H1/W16-H1, `HUMAN_REVIEW_PENDING`): cạnh khuất của chóp tam giác, lăng trụ tam giác, chóp đáy chữ nhật, thiết diện — sản phẩm khớp oracle độc lập ở mọi trạng thái, còn chờ mắt người | `<họ>/hidden-edges/desktop/` | |

Từ `0ca3accf` tới nay, `frontend/src` chỉ đổi phần chọn nhãn của thẻ từ chối (`SimulationWorkspace.tsx`,
`core/types.ts`); mã vẽ cảnh phục vụ giữ nguyên byte. `backend/app` thêm một lời từ chối (W20 §17) và câu chữ của nó
(cuboid-final-review). Ảnh w18 vì thế vẫn là ảnh của đường vẽ hiện hành, nhưng **không** được chụp trên candidate
`b2d4187a`; muốn ảnh trên candidate hiện hành thì cần một lượt đo trình duyệt riêng (chưa làm, không bắt buộc).

### 1.2 Thẻ từ chối mới (đo ở `a1c53cdb`, commit sản phẩm `284a9bfa`, candidate `b2d4187a` — hiện hành)

Mỗi ảnh: lời "Hệ chưa kiểm chứng được ‹quan hệ›, vì điểm này ‹cách đặt› thay vì dựng từ quan hệ trong đề. Hệ tạm
dừng để tránh đưa ra kết quả chưa kiểm chứng.", dòng "Loại vấn đề: chưa kiểm chứng được phép dựng", không hình, không
đáp số, không câu mời gửi lại, không tràn.

| # | ca | desktop | mobile | ghi |
|---|---|---|---|---|
| h | hình chiếu đặt bằng toạ độ | `cuboid-final-review/images/cfr_projection_by_coordinates/desktop/refusal.png` | `…/mobile/refusal.png` | |
| i | hình chiếu lấy trùng đỉnh A | `cuboid-final-review/images/cfr_projection_alias_vertex/desktop/refusal.png` | `…/mobile/refusal.png` | |
| j | trung điểm đặt bằng toạ độ | `cuboid-final-review/images/cfr_midpoint_by_coordinates/desktop/refusal.png` | `…/mobile/refusal.png` | |
| k | đối chứng không được đổi: lệch đã chứng minh, chưa đối chiếu | `cuboid-final-review/images/w18_projection_mismatch/<khổ>/refusal.png`, `cuboid-final-review/images/w18_unverified/<khổ>/refusal.png` | (cùng thư mục) | |

Kết quả tự động của các ảnh này: `cuboid-final-review/results/BROWSER_REFUSAL_CFR.json` (12/12).

### 1.3 Giới hạn đã khai và việc chuyển sang task sau — xác nhận chấp nhận được để merge

| # | giới hạn | nơi ghi | ghi |
|---|---|---|---|
| l | Phép dựng điểm chỉ đối chiếu trung điểm và hình chiếu; tâm, giao điểm, cách nói ngoài từ vựng ⇒ từ chối "chưa đối chiếu được" trong vùng đa diện | `ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY` | |
| m | Chứng chỉ giả định chỉ thi hành trong vùng đa diện (từ vựng đóng); ngoài vùng chỉ ghi | `ARCHITECTURE_MAP.md` §5 #37, W15-H2 | |
| n | Chỉ phép cắt (thiết diện) được đối chiếu với câu đề; quan hệ dựng khác chưa | `ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT` | |
| o | Hình cong `foundation_only`; OCR mới là FIXTURE; nhiều khối trong một đề ngoài phạm vi | `ROADMAP.md` §0.4 | |
| p | Chín chỉnh sửa giao diện đã chốt + câu mời gửi lại ở các lời CONSTRUCTION khác (H-CFR-1): **chưa làm**, chuyển sang việc kế tiếp | `ROADMAP.md` §0.1 | |
| q | #14: hai script dev gọi live không cần opt-in (không đụng sản phẩm) | `ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM` | |

Người duyệt ghi kết quả vào một lớp registry người mới (không sửa registry cũ). Không cần duyệt lại điều đã được duyệt
và còn đúng phạm vi; tới nay chưa có mục nào của §1 được duyệt.

## 2. Quyết định đã có và câu hỏi còn mở

Đã quyết (brief của run này): H-CFR-2 giữ chữ thường và "toạ độ"; H-CFR-1 là backlog giao diện, không sửa sản phẩm
lúc này; H-CFR-3 `THESIS_DRAFT` §1.8 là bản chính đề xuất, chưa xoá `RELATED_WORK_DRAFT` khi chưa đối chiếu nội dung
riêng; 204 mục `D:/tmp` + 108 mục `.superpowers` giữ nguyên, không chặn merge.

Còn mở (không chặn merge): W18-H2, W18-H3, W17-H2, W15-H2, W15-H3 (`ROADMAP.md` §0); H-W20-4 (tàn dư Tin học trong
mã — run này liệt kê thêm phần còn ngủ ở shell trong `results/INVARIANT_RECONCILIATION.json`, mục
`dormant_code_observed`).

## 3. Khi có phê duyệt tường minh — merge thẳng, không PR

1. `git fetch --prune origin`; đối chiếu `origin/main` với `a9492ee9` (đổi thì đọc các commit mới trước).
2. Trên `main` cục bộ (đang trùng `origin/main`): `git merge --no-ff fix/cuboid-visual-semantic-closure` (hoặc
   fast-forward theo chính sách kho); không rebase, không squash chuỗi commit mà bằng chứng đã tham chiếu.
3. Kiểm cây tích hợp: candidate `--verify`, cache lock `--verify`, `LLM_ONLY`, audit tài liệu; nếu cây sản phẩm khác
   `284a9bfa` thì chạy lại phần bị ảnh hưởng (T3 trong worktree sạch).
4. `git push origin main` (không force); kiểm `git ls-remote origin main` = SHA cục bộ và HEAD nhánh là tổ tiên của
   `origin/main`.
5. CI: kho không có cấu hình CI — ghi `NOT_APPLICABLE`, không tuyên bố PASS.
6. Xoá nhánh đã merge (`git branch -d`, không `-D`; nhánh remote chỉ khi tồn tại) khi không còn worktree dùng nó.
7. Giữ việc xoá `frontend/public/favicon.svg` của người dùng suốt quá trình (không stage, không restore).

## 4. Việc kế tiếp — đề xuất, người dùng chưa chọn

Chóp tứ giác đều (G03 trong `ROADMAP.md` §0.2) cùng chín chỉnh sửa giao diện §0.1 và backlog H-CFR-1. Chỉ bắt đầu
sau khi `main` đã tích hợp và cập nhật: nhánh mới rẽ từ `main` (đề xuất `feat/regular-square-pyramid`), task slug
`regular-square-pyramid`, wave đầu **W1**, run đầu `regular-square-pyramid-w01`; không nối số W21/W22. Mở bằng tiền
đăng ký (họ, tầng phải đóng — "đều" và chân đường cao ở tâm, toạ độ trong ℚ³ —, corpus gắn nhãn trước, cổng trình
duyệt desktop/mobile, hồi quy §0.3). Run này không triển khai hình mới.
