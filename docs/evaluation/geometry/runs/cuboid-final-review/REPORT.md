# cuboid-final-review — rà soát trọn tài liệu và nghiệm thu nhánh cuboid

`COMPLETE_DOCS_CLEANUP_AND_CUBOID_BRANCH_ACCEPTANCE` · 2026-10-05 · nhánh `fix/cuboid-visual-semantic-closure` ·
lượt chốt của việc `cuboid-visual-semantic-closure` (không đánh số wave; W1–W20 giữ tên). Kế hoạch: [`PLAN.md`](PLAN.md).
Bàn giao và danh sách ảnh cần duyệt: [`HANDOFF.md`](HANDOFF.md).

## 1. Kết luận

**`READY_FOR_HUMAN_VISUAL_REVIEW`.**

- Mọi cổng tự động đạt trên candidate cuối `b2d4187a…`, kiểm trong worktree tách rời sạch tại `a1c53cdb`.
- Không ai đã duyệt hình. Điều kiện merge còn lại: review người W18-H1, cùng các thẻ từ chối mới của run này.
- Không push, không merge, không xoá nhánh.

| mục | kết quả |
|---|---|
| Rà soát tài liệu | 8812 file `docs/` + `AGENTS.md`/`README.md`/`DESIGN.md` được phân lớp (`inventory/DOCS_INVENTORY.json`); phần thời Tin học của 7 tài liệu sống tách **nguyên văn** sang `docs/legacy/` (119 khối, 2960 dòng, kiểm byte); 0 link chết và 0 link cố định theo máy trong tài liệu sống |
| Đánh số wave | theo từng việc: việc mới, nhánh mới bắt đầu ở W1; định danh đầy đủ `<task-slug>-wNN` (`docs/evaluation/RUN_NAMING.md`, con trỏ ở AGENTS §2 và RULES §2) |
| Thẻ từ chối §17 | lời ghép từ dữ liệu có cấu trúc, không hứa gửi lại sẽ được; nhãn "chưa kiểm chứng được phép dựng"; ca lệch và ca chưa đối chiếu giữ nhãn cũ; trình duyệt 12/12 (desktop + mobile) |
| Danh tính | candidate `27c31de6…` → `b2d4187a…` (một lần đóng băng, `284a9bfa`); `CACHE_VERSION` giữ 111 (có chứng minh); `LLM_ONLY`; bề mặt mô hình không đổi; 0 lượt gọi live |
| T3 tại `a1c53cdb` | `FULL_PRODUCT_GATE_PASS` — pytest 7079/0 (1 skipped, 2 deselected), vitest 1061/1061, typecheck + build, demo 5/5, bề mặt sập 6/6 |

## 2. Rà soát tài liệu

### 2.1 Cách làm

- **Kiểm kê:** `diagnostics/inventory_docs_cfr.py`.
  - Một hàng cho mỗi file ngoài các cây bằng chứng (342 hàng).
  - Một hàng cho mỗi cây bằng chứng `docs/evaluation/**`, kèm số file và git tree id (146 nhóm, 8470 file).
  - Script khẳng định mỗi file được phủ đúng một lần.
- **Người tham chiếu** của mỗi file được đọc từ mọi file văn bản đã theo dõi, gồm link, đường dẫn và tên viết hoa riêng.
  Tách "sống" (mã, tài liệu sống) với "đóng băng" (bằng chứng, legacy).
- **Đo hai lần, cùng một thước:**
  - trước, tại `4048ff83` → `inventory/DOCS_INVENTORY_BEFORE_4048ff83.json`;
  - sau, tại commit kiểm chứng `a1c53cdb` → `inventory/DOCS_INVENTORY.json`.
- **Lớp của từng file** do người phân (bảng `HAND` trong script, kèm lý do và việc đã làm).
  - Báo cáo trong catalog và cây bằng chứng là `FROZEN_KEEP` theo luật.
  - Sau rà soát: 238 `FROZEN_KEEP` · 41 `KEEP_ARCHITECTURAL_HISTORY` · 31 `KEEP_CURRENT` · 38 `KEEP_RESEARCH` · 1 `REVIEW_REQUIRED`
    (tính trên 349 hàng file; 7 hàng là file đồng hành mới trong `legacy/`).
  - Không file nào thuộc `MERGE_INTO_CANONICAL`, `DELETE_VERIFIED_DUPLICATE` hay `DELETE_ABANDONED_OUT_OF_SCOPE`:
    - ngoài `docs/evaluation` không có bản trùng byte;
    - 1814 bản trùng bên trong `docs/evaluation` là cố ý, vì mỗi wave tự chứa;
    - tài liệu hết phạm vi đã nằm trong `legacy/` từ W19 và vẫn có giá trị truy vết.

### 2.2 Tách lịch sử khỏi tài liệu sống — nguyên văn, kiểm được byte

Công cụ: `diagnostics/split_history_cfr.py`.
- Khối được cắt từ blob của `4048ff83`, không cắt từ bản làm việc.
- `--apply` từ chối ghi đè nếu tài liệu đã đổi.
- `--verify` kiểm bốn điều:
  - sha256 của từng khối;
  - khối có mặt nguyên văn trong file đồng hành;
  - khối không còn trong tài liệu sống, và dòng trỏ của nó vẫn ở đó;
  - mọi dòng không rỗng của bản gốc còn ở một trong hai file.
- Bản ghi: `inventory/HISTORY_SPLIT.json`.

| tài liệu sống | khối | dòng | sang | còn lại trong tài liệu sống |
|---|---|---|---|---|
| `CODE_INDEX.md` | 96 | 1467 | `legacy/CODE_INDEX_REMOVED_ENTRIES.md` | §0–§0g, chỉ mục truy vết §0j (kèm con trỏ), mọi mục của mã còn tồn tại |
| `STATUS_LEDGER.md` | 3 | 782 | `legacy/STATUS_LEDGER_INFORMATICS_ERA.md` | ghi chú điều hướng, §0-2026-08-24/20/23, §6 lịch sử wave |
| `COVERAGE.md` | 3 | 418 | `legacy/COVERAGE_INFORMATICS_ERA.md` | §1 mới trỏ tới độ phủ và câu bị cấm hiện hành; §2, §5 nguyên văn (mã trích theo số) |
| `CORRECTNESS.md` | 6 | 123 | `legacy/CORRECTNESS_INFORMATICS_ERA.md` | §1, §1a, §2, §2b, §4, §7 (luật live hiện hành thay runner `live.py`) |
| `DESIGN_BRIEF.md` | 5 | 63 | `legacy/DESIGN_BRIEF_INFORMATICS_ERA.md` | §1 mô tả sản phẩm hình học, banner giai đoạn, luật §3/§5–§7/§9 |
| `ARCHITECTURE_MAP.md` | 4 | 50 | `legacy/ARCHITECTURE_MAP_INFORMATICS_ERA.md` | §7 điểm mở rộng hiện hành (con trỏ), ghi chú §5 |
| `POST_THESIS_BACKLOG.md` | 2 | 57 | `legacy/POST_THESIS_BACKLOG_INFORMATICS_ERA.md` | nợ 2026-09-02, hướng 2026-09-09 |

`ARCHITECTURE_MAP.md` §5: ở 22 hàng bất biến (#1–#8, #10, #11, #14–#16, #18, #20–#26, #29), file được nêu ở cột
*thực thi*/*test* đã gỡ.
- Bảng giữ nguyên, vì số hàng được mã và test trích.
- Thêm một ghi chú có ngày, danh sách theo hàng (`architecture_map_invariant_pointers` trong `DOCS_INVENTORY.json`) và
  `ISSUE-DOCS-INVARIANT-ENFORCEMENT-POINTERS-STALE`.
- Đối chiếu lại từng bất biến là việc kiểm kiến trúc, không thuộc dọn tài liệu.

### 2.3 Sửa tại chỗ (13 file, `inventory/CLEANUP_LOG.json`)

- **Ví dụ trỏ tới file đã xoá:** ba ví dụ trong `OPERATIONS.md` được thay bằng file có thật.
- **`TEST_TIERS.md`:** ghi chú có ngày. 8/10 script T1 trỏ vào miền đã gỡ; miền hình học chưa có T1 và chưa có chủ sở hữu
  trong `impact.mjs` (`ISSUE-OPS-T1-DOMAIN-SCRIPTS-STALE`).
- **`MIGRATION_CHECKLIST.md`:**
  - GATE-02/03: sửa hai đường dẫn chứng cứ không tồn tại.
  - GATE-11/12: thêm dòng đối chiếu. Router và nhánh lùi về LLM có thật dưới dạng opt-in (`geometry_compiler/routing.py`,
    gọi ở `ai/pipeline.py`); STATUS để nguyên cho wave di chuyển chấm lại. Cùng nội dung ở hai issue `ISSUE-ARCH-…`.
- **Nghiên cứu:**
  - Bốn link `file:///` trong `SYSTEMATIC_LITERATURE_GAP_SYNTHESIS.md` thành link tương đối.
  - Một con trỏ trong `RELATED_WORK_SEARCH_PROTOCOL.md` tới vị trí W19 của `THESIS_REFERENCES.md`.
  - Hai tiền đăng ký niêm phong giữ nguyên byte; 9 link theo máy của chúng được ghi trong `research/README.md`.
- **RULES mục đọc 7** nói `COVERAGE.md` trỏ tới đâu. **`legacy/README.md`** có bảng bảy file đồng hành.

### 2.4 Xoá

- Không file đã theo dõi nào bị xoá.
- Hai thư mục `__pycache__` bị gitignore trong `docs/` (3 file `.pyc`) được xoá theo đường dẫn, kiểm sha256 ngay trước khi
  xoá; chúng sinh lại khi import.
- Ngoài kho:
  - `D:/tmp` vẫn đúng 204 mục mà W20 đã đăng ký; không mục nào được kiểm lại là trùng, nên không xoá gì.
  - `.superpowers/` không được liệt kê lại (vùng của kế hoạch khác).

### 2.5 Trước → sau (tài liệu sống, cùng bảng phân lớp)

| thước đo | trước `4048ff83` | sau `a1c53cdb` |
|---|---|---|
| link tương đối chết | 0 | 0 |
| link `file:///` theo máy | 4 | 0 |
| nhắc tới đường dẫn đã gỡ | 51 | 28 — đều cố ý: 8 trỏ file local bị gitignore (`backend/.venv`, `backend/.env`), 20 nằm trong ghi chú có ngày, chỉ mục §0j hay cột "vị trí cũ" |
| cache bị gitignore trong `docs/` | 2 thư mục (đo ở cây chính) | 0 |

- **Số dấu hiệu "Tin học" không phải thước đo.** Sau dọn, vài tài liệu có nhiều dấu hiệu hơn, vì chính các dòng trỏ mới ghi
  "giai đoạn Tin học". Thước đo đúng là 2960 dòng nội dung thời Tin học đã rời tài liệu sống mà không mất byte nào.
- **Link trong `legacy/`:** 20 link tương đối trỏ vị trí cũ. Đây là ngoại lệ đã ghi trong `legacy/README.md`; khối chép
  nguyên văn thì không được sửa.

### 2.6 Không làm, và vì sao

- **180 báo cáo vẫn ở gốc `docs/`.** Luật bất biến của bằng chứng giữ đường dẫn của chúng.
  `ISSUE-DOCS-HISTORICAL-REPORTS-AT-DOCS-ROOT` chuyển sang `INTENDED_LIMITATION`, đúng theo brief.
- **`research/thesis/RELATED_WORK_DRAFT.md` để `REVIEW_REQUIRED`.** File là một bản "công trình liên quan" thứ hai bên cạnh
  `THESIS_DRAFT` §1.8. Chọn bản nào là việc viết khoá luận, nên tác giả quyết.
- Không bổ sung kết quả nghiên cứu, không viết lại bản thảo.
- `CLAIM_EVIDENCE_MAP.md` vẫn là thẩm quyền tuyên bố duy nhất.

## 3. Đánh số wave theo từng việc

`docs/evaluation/RUN_NAMING.md` (commit `3f8127fd`) quy định:
- **Một việc:**
  - một nhánh và một `task-slug` ổn định, kể cả sau khi nhánh bị xoá;
  - việc mới trên nhánh mới bắt đầu ở W1.
- **Ghi định danh:**
  - chỉ mục và manifest ghi định danh đầy đủ `<task-slug>-wNN`, không bao giờ `W1` trần;
  - tên thư mục ngắn; ngày, nhánh, commit và candidate nằm trong `RUN.json`.
- **Rẽ nhánh:** việc mới chỉ rẽ từ `main` đã tích hợp và cập nhật.
- **Việc hiện tại:**
  - W1–W20 giữ tên;
  - việc này có slug `cuboid-visual-semantic-closure`, và run này là lượt chốt không đánh số của nó.

`AGENTS.md` §2 và `RULES.md` §2 trỏ về đó.

## 4. Thẻ từ chối của §17 (`CONSTRUCTION_REPLACED_BY_COORDINATES`)

| | trước (W20) | sau (`284a9bfa`) |
|---|---|---|
| lời (L14) | *Đề bài nêu "H là hình chiếu của S lên BD", nhưng chương trình của AlgoSim đặt H bằng toạ độ cho sẵn thay vì dựng điểm này từ quan hệ ấy, nên hệ chưa kiểm chứng được nó đúng là điểm đề nói. AlgoSim dừng lại thay vì đưa ra một đáp số chưa kiểm chứng. Đây là lỗi dựng hình của hệ, đề không cần sửa — em có thể gửi lại để hệ dựng lại.* | *Hệ chưa kiểm chứng được H là hình chiếu của S lên BD, vì điểm này được đặt bằng toạ độ thay vì dựng từ quan hệ trong đề. Hệ tạm dừng để tránh đưa ra kết quả chưa kiểm chứng.* |
| nhãn "Loại vấn đề" | hệ dựng lệch với đề bài | chưa kiểm chứng được phép dựng |
| `reason_subjects` (vế sau) | `đặt H bằng toạ độ cho sẵn` / `lấy H trùng với điểm A` | `được đặt bằng toạ độ` / `được lấy trùng với điểm A` |

- **Nguồn dữ liệu:** tên và quan hệ đọc từ `reason_subjects`, không viết cứng. Nhiều cặp được gộp; tên máy không bao giờ
  lên màn hình.
- **Nhãn:** frontend chọn bằng `reason_code` và không hiển thị mã.
- **Đối chứng:** ca lệch đã chứng minh giữ "hệ dựng lệch với đề bài"; ca chưa đối chiếu giữ "hệ chưa đối chiếu được phép
  dựng với đề".
- **Chính tả và viết hoa:**
  - Lời dùng "toạ độ" theo cách viết của kho; brief đề xuất "tọa độ".
  - Nhãn viết thường chữ đầu như mọi nhãn "Loại vấn đề" khác.
  - Cả hai là mục cho người duyệt.
- **Đỏ trước** (`results/logs/RED_*_REFUSAL.log`):
  - backend: 5 test đỏ — hai test W20 viết lại theo câu chữ mới, thêm ca L16 có tên và quan hệ khác, và một test ghép lời
    từ chủ thể tuỳ ý;
  - frontend: test nhãn đỏ, hai đối chứng xanh.
- **Xanh** (`GREEN_*`): backend 168 test liên quan, frontend 45.
- **Trình duyệt** (`diagnostics/browser_refusal_cfr.mjs`, `results/BROWSER_REFUSAL_CFR.json`):
  - Ca: ba ca mã mới (hình chiếu đặt bằng toạ độ, hình chiếu lấy trùng đỉnh A, trung điểm đặt bằng toạ độ) cùng ba
    đối chứng (lệch, chưa đối chiếu, được phục vụ "3√6").
  - Khổ: desktop 1440×900 và mobile 390×844.
  - Đường đi: bản dựng production; đề gõ vào ô nhập thật; `/api/analyze` trả envelope sinh qua `run_pipeline`
    (0 lượt gọi model).
  - **12/12.** Mỗi ca kiểm: mã có cấu trúc, lời hiện nguyên văn, nhãn, không canvas, không đáp số, không tràn, không token
    thô, không lỗi console hay exception.
  - Ảnh nằm trong `images/` (danh sách trong `HANDOFF.md`). Tôi đã mở và xem từng ảnh của thẻ mới.
  - Lần đo đầu bị cổng độ tươi của `dist/` chặn (`results/logs/BROWSER_REFUSAL_attempt1_DIST_CU_a1c53cdb.log`): xuất lại
    schema làm mtime của `src/` mới hơn bản dựng. Đã build lại rồi đo lại.

## 5. Danh tính

- **Candidate:**
  - đóng băng **một lần** trong worktree sạch `D:/tmp/cfr-freeze` tại `284a9bfa` (commit cuối chạm `backend/app` hoặc
    `frontend/src`);
  - `27c31de6…` → `b2d4187a78ed8bf6…`, 110 file; taxonomy, primitive, schema, DEV không đổi;
  - khai ở `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` (đính chính lớp W20); `KHAI_LECH`, bản khai sống và registry
    kịch bản trỏ theo.
- **Trước đóng băng:**
  - backend đầy đủ ở cây chính: 7067 passed, 12 failed;
  - 10 failed là phép kiểm danh tính của candidate cũ; 2 failed vì cây bẩn bởi file chưa theo dõi của chính run này;
  - đã phân loại ở đầu `results/logs/PRE_FREEZE_FULL_BACKEND_fac2769e.log`; sau đóng băng tất cả xanh.
- **`CACHE_VERSION` giữ 111** (`diagnostics/cache_proof/`):
  - 27 hàng corpus W20 chạy qua `run_pipeline` với mã `4048ff83` và `284a9bfa`;
  - 8 envelope được phục vụ trùng byte;
  - 8 envelope từ chối chỉ khác `reason_subjects`;
  - `main.py` chỉ cache `status == "ok"` (khoá bởi `test_api.py::test_khong_cache_ket_qua_unsupported`).
  - ⇒ không envelope cũ nào trả lời cũ hay nhãn cũ.
- **Bề mặt mô hình:** prompt, thẻ văn phạm, hai schema và bảng năng lực: 0 file đổi; vân tay `b1714b566e25c912`.
- **Chế độ và lượt gọi:** `LLM_ONLY`; 0 lượt gọi live.

## 6. Kiểm chứng có thẩm quyền

Worktree tách rời sạch `D:/tmp/cfr space/algo-sim` (đường dẫn có dấu cách) tại `a1c53cdb`; `npm ci --offline`.

| lệnh | kết quả |
|---|---|
| `node frontend/scripts/full-gate.mjs` (T3) | **`FULL_PRODUCT_GATE_PASS`** — pytest 7079 passed / 0 failed (1 skipped, 2 deselected), vitest 1061/1061, typecheck + build, demo 5/5, bề mặt sập 6/6 (`results/logs/T3_FULL_GATE_a1c53cdb.log`) |
| `diagnostics/cfr_gates.sh a1c53cdb 4048ff83` | candidate + cache `--verify` exit 0; schema ×2 trùng byte (`d852b47c…`); `LLM_ONLY`; bề mặt mô hình 0 file; mã sản phẩm đổi: 5 file (2 backend, 3 frontend); ngoài run, `docs/evaluation` chỉ đổi `RUN_NAMING.md` và hai registry sống; `docs/legacy`: 7 file thêm + README; báo cáo trong catalog đổi 0/181; tách lịch sử `--verify` OK; `diff --check` 0; audit tài liệu PASS; harness node 70 pass + 2 skip theo thiết kế (worktree không có `backend/.venv`) (`results/logs/GATES_a1c53cdb.log`) |
| fixture + trình duyệt | 6 fixture qua `run_pipeline` (mã và lời kiểm trước khi ghi), 12/12 (`results/logs/BROWSER_REFUSAL_a1c53cdb.log`) |
| kiểm kê | trước `4048ff83`, sau `a1c53cdb` (`inventory/`) |
| `git status` của worktree | file đã theo dõi không đổi sau T3 và các cổng; output chép nguyên byte vào run rồi xoá; worktree gỡ không ép (`results/logs/WORKTREE_STATUS_a1c53cdb.log`) |

Commit tài liệu cuối chỉ đổi tài liệu và bằng chứng. Cổng tài liệu của nó chạy lại trong worktree sạch, log ở
`results/logs/DOCS_GATES_FINAL.log` (commit kế tiếp).

## 7. Đính chính bổ sung cho W20

Báo cáo W20 gọi phần dọn kho của nó là dọn kho. Nói chính xác:
- W20 là **đóng tính đúng cộng một lượt dọn có giới hạn**: bản trùng có bằng chứng cơ giới, luật, tệp tạm.
- **Rà soát trọn tài liệu** làm ở run này.
- `PLAN.md`/`REPORT.md` của W20 không sửa. Đính chính nằm ở dòng `CORRECTED_BY` của W20 trong `docs/EVIDENCE_INDEX.md`
  và `docs/STATUS_LEDGER.md`.

## 8. Giới hạn và việc còn mở

- **Review người:** `NOT_APPROVED` (W18-H1, cùng các thẻ mới của run này). Tự động hoá không ghi `APPROVED_BY_USER`.
- **Lời CONSTRUCTION khác** (dựng lệch, số liệu lệch) vẫn kết bằng "em có thể gửi lại để hệ dựng lại". Run này chỉ sửa thẻ
  §17 (câu hỏi H-CFR-1 trong `HANDOFF.md`).
- **Không đóng ở run này:**
  - `ISSUE-DOCS-INVARIANT-ENFORCEMENT-POINTERS-STALE`;
  - `ISSUE-OPS-T1-DOMAIN-SCRIPTS-STALE`;
  - `ISSUE-OPS-DOCS-FAULT-INJECTION-TESTS-WRITE-LIVING-DOCS`;
  - `ISSUE-OPS-TMP-LEFTOVERS-UNVERIFIED` (204 + 108 mục chờ quyết định);
  - tàn dư Tin học trong mã sản phẩm (H-W20-4).
- **Bản dựng ở cây chính** vẫn bị chặn bởi ACL của `dist/` (`ISSUE-OPS-DIST-ACL-OWNERSHIP`), nên mọi bản dựng và phép
  đo trình duyệt chạy trong worktree.

## 9. Skill

- **Gọi qua Skill tool trong run này:** `ponytail:ponytail-audit` (hai script chẩn đoán).
  - 8 phát hiện; áp dụng 7, đảo lại 1 sau khi đo.
  - Phát hiện bị đảo: `exists()` chỉ kiểm trên đĩa làm việc xoá favicon của người dùng hiện thành con trỏ chết ở hơn 40
    tài liệu.
- **Đã gọi trước đó trong cùng phiên và áp dụng, không gọi lại:**
  - superpowers:systematic-debugging, superpowers:test-driven-development, superpowers:verification-before-completion,
    superpowers:writing-plans, superpowers:executing-plans (ledger + rulings);
  - ponytail:ponytail-review;
  - andrej-karpathy-skills:karpathy-guidelines.
- **Áp dụng thủ công:** checklist `code-reviewer.md` cho lượt tự rà toàn nhánh. Brief cấm subagent; lượt rà do chính tác
  giả làm thì yếu hơn một người rà độc lập.
