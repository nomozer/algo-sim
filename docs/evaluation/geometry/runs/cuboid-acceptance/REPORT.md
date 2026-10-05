# REPORT — cuboid-acceptance

Run chốt hồ sơ nghiệm thu của việc `cuboid-visual-semantic-closure` (nhánh `fix/cuboid-visual-semantic-closure`),
2026-10-05, không đánh số wave. **Chỉ tài liệu**: không đổi mã sản phẩm, không đóng băng lại candidate, không bump
cache, 0 lượt gọi model. Bàn giao và checklist duyệt hình: [`HANDOFF.md`](HANDOFF.md).

## 1. Việc được giao và điều kiện dừng

1. Đối chiếu các bất biến ở `docs/ARCHITECTURE_MAP.md` §5 có con trỏ thực thi/test đã gỡ.
2. Sửa trạng thái và con trỏ tài liệu theo bằng chứng.
3. Chốt hồ sơ nghiệm thu của nhánh.
4. Merge thẳng vào `main`, push, xoá nhánh — **chỉ khi** có phê duyệt hình tường minh. Chưa có ⇒ bước 4 không chạy.

## 2. Phương pháp

- **Danh sách.** Kiểm lại từ chính bảng §5 (39 hàng), không từ con số của run trước. Inventory của
  `cuboid-final-review` so tên file nên bỏ sót "như trên": #9 và #12 thừa hưởng con trỏ chết của #8 và #11 ⇒ **24**
  hàng, không phải 22. Các hàng còn lại (#13, #17, #19, #27, #28, #30–#39) được kiểm từng file và từng symbol: đều
  còn sống.
- **Từng hàng:** yêu cầu nói gì · miền sản phẩm áp dụng · cài đặt hiện hành · test và **assertion** cụ thể · bằng
  chứng đã đo · đường cũ và commit đã gỡ nó (`git log --diff-filter=D`). Tên file, số test hay full suite xanh không
  được dùng thay assertion; "lịch sử" không suy từ chữ Tin học trong tên mà từ tuyến sản phẩm (registry chỉ có một
  module, `apply` đồng nhất, cảnh 3D trả về trước logic 2D, endpoint đã gỡ…).
- **Luật phân loại:** cùng yêu cầu, cơ chế mới ⇒ `CURRENT_*` với con trỏ mới; chủ thể không còn tới được sản phẩm
  hoặc một hàng sau đã thay ⇒ `HISTORICAL_NOT_APPLICABLE` kèm bằng chứng và hàng kế nhiệm.
- **Kiểm tra:** [`diagnostics/invariant_checks_cacc.sh`](diagnostics/invariant_checks_cacc.sh) — phần 1 con trỏ cũ
  (còn theo dõi, hay commit đã xoá), phần 2 con trỏ mới (file + symbol), phần 3 pytest tập trung, phần 4 vitest tập
  trung, phần 5 dò tĩnh opt-in của các script gọi model (#14). Lượt thử trên cây chính (log ngoài kho): phần 2 đủ,
  pytest 348 passed, vitest 9 file / 138 test passed. Lượt có thẩm quyền chạy trong worktree tách rời sạch tại commit
  tài liệu: `results/logs/INVARIANT_CHECKS_FINAL.log`.

## 3. Kết quả

| phân loại | số | hàng |
|---|---|---|
| `CURRENT_ENFORCED` | 9 | #1 R0 (lược đồ chỉ nhận TÊN, cấm literal hình học, executor không import AI, khung từ trace) · #2 kernel chính xác + oracle độc lập bắt được lỗi tiêm · #3 Scene3D chỉ đọc envelope tại một bước · #8 cổng fail-closed từng chặng · #9 đáp số qua checker, lời từ chối có cấu trúc và nói thật · #11 mọi phán đúng/sai là mã tất định, không còn bề mặt phán quyết · #21 cổng phủ C₁a/C₁b thay cổng tính toán M13 · #22 observer thụ động + runner nghiệm thu dùng chính chặng sản phẩm · #29 vai trò do server, điều hướng là hàng trên thanh trên |
| `CURRENT_UNVERIFIED` | 1 | #14 — xem §4 |
| `HISTORICAL_NOT_APPLICABLE` | 14 | #4 (kế nhiệm: IR một nguồn, `test_schema_sync.py`) · #5 · #6 · #7 (cache phản hồi là cơ chế riêng có từ trước) · #10 · #12 · #15 (`/api/edit` đã gỡ) · #16 (kế nhiệm #31, #35) · #18 (kế nhiệm: hợp đồng khuất/hiện + oracle) · #20 (kế nhiệm: kiểm IR có mã) · #23 · #24 · #25 · #26 |
| `VIOLATED` | 0 | — |

Từng hàng — yêu cầu, con trỏ cũ và trạng thái, cài đặt, test đến assertion, lệnh kiểm, lý do, ảnh hưởng merge, việc
theo sau: [`results/INVARIANT_RECONCILIATION.json`](results/INVARIANT_RECONCILIATION.json). Commit đã gỡ các file
cũ: `6d5f5fda`, `6703c48a`, `e664f683`, `f9a40935` (2026-09-02, gỡ miền Tin học), `eebc22a8` (2026-08-10),
`75b981d6` (2026-09-03).

## 4. Phát hiện

- **#14 (live là opt-in) — lỗ bằng chứng, chưa phải lỗi đã tái hiện.** 30 script kiểm `ALLOW_LIVE_AI`, 5 script đòi
  `--live` hoặc `--execute-live --confirm-live-execution`; không khoá nào phủ cả `backend/scripts`. Dò tĩnh (54 script
  nêu model hoặc pipeline) rồi đọc tay: `run_live_gemini_semantic_smoke.py` (2026-08-20, đề Tin học; nạp
  `backend/.env` lúc import, gọi Gemini khi có khoá) và `run_rectangular_pyramid_live_analyze.py` (2026-09-24; mặc định
  gửi một request Analyze thật, `--offline-eval` là cờ để TẮT). Lần dò đầu chỉ bắt được script thứ nhất; mẫu dò được
  mở rộng tới `stage_semantic_*` và `AsyncHTTPTransport` mới bắt được script thứ hai — mẫu dò là heuristic, 0 điểm
  gọi không chứng minh script sạch. Không chạy để tái hiện (cần lượt gọi thật và đọc `.env`, cả hai bị cấm). Ảnh hưởng:
  không chạm sản phẩm, học sinh, candidate hay phép đo nghiệm thu nào (đều 0 lượt gọi); cả hai đã có trên `main` ⇒
  **không chặn merge**. Đăng ký `ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM`.
- **Mã thời Tin học còn ngủ trong shell** (không tới được học sinh hình học): cờ và lối vào Khám phá, `specDrift`,
  hợp đồng `currentConfig?` và `threeD`, chính sách biểu diễn của `renderer.ts`, client `editViaServer` (backend
  `/api/edit` đã gỡ), `AIHelpPanel.tsx` + `explainViaServer` (không được gắn) với `/api/explain` (không người dùng UI),
  `AttemptObserver` (không ai dùng), trường `exploreOpen`/`challengeOpen` của lớp học, hai script nghiệm thu trình
  duyệt Tin học. Là bằng chứng cho quyết định còn chờ H-W20-4 — không mở issue mới, không sửa (task cấm đổi mã sản
  phẩm).
- **Ngoài phạm vi, chỉ ghi:** chữ của #27 vẫn nói "correctness thuộc về … `predict.check`" (đã gỡ ở W13) và #28 nêu
  `SimSpec.validate`; con trỏ của hai hàng còn sống. `test_postconditions.py` kiểm nghĩa vụ Tin học.
- **Con trỏ cũ của #25** ghi `spec-drift-w4b4d.test.ts`; file thật là `.tsx` (thêm `bd2c13ea`, gỡ `6703c48a`).

## 5. Tài liệu đã sửa

- `ARCHITECTURE_MAP.md` §5: ghi chú có ngày thay ghi chú cũ (24 hàng, số theo lớp); hai cột con trỏ của 24 hàng chỉ
  còn file sống; 14 hàng gắn **LỊCH SỬ**, #14 gắn **UNVERIFIED**; #21, #22 ghi dạng hiện hành; chữ cột yêu cầu giữ
  nguyên văn, số hàng giữ nguyên. Sau sửa: `invariant_pointers` báo 39/39 hàng, 0 file thiếu.
- `OPEN_ISSUES.md`: `ISSUE-DOCS-INVARIANT-ENFORCEMENT-POINTERS-STALE` → RESOLVED (tiêu chí nghiệm thu đạt); thêm
  `ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM`.
- `CODE_INDEX.md`: năm ghi chú có ngày ở các mục còn trỏ hàng đã đối chiếu hoặc mã nay ngủ (observer, pipeline,
  renderer, lối vào Khám phá/`specDrift`, client LLM).
- `CURRENT_STATE.md`, `AI_CONTEXT_BUNDLE.md`, `ROADMAP.md` §0 (quyết định H-CFR, điều kiện merge, đề xuất
  `regular-square-pyramid-w01`, backlog H-CFR-1 dưới §0.1 — chín mục giữ nguyên), `research/README.md` (H-CFR-3),
  `EVIDENCE_INDEX.md` và `STATUS_LEDGER.md` (mục mới; run trước nhận `CORRECTED_BY` cho con số 22 → 24).
- Không sửa artifact hay báo cáo lịch sử nào; đính chính nằm ở lớp mới của run này.

## 6. Kiểm chứng

Trong worktree tách rời sạch tại commit tài liệu (`git status` trước/sau ghi trong log):
[`diagnostics/cacc_gates.sh`](diagnostics/cacc_gates.sh) — byte sản phẩm so với `903e874c` và với `284a9bfa`,
candidate và cache `--verify`, `CACHE_VERSION`, `LLM_ONLY`, bề mặt mô hình, hai bản lược đồ, `docs/evaluation` ngoài
run, `docs/legacy`, báo cáo lịch sử trong catalog, tách lịch sử `--verify`, `git diff --check`, con trỏ §5, audit tài
liệu, test tài liệu (pytest + vitest) — và `invariant_checks_cacc.sh`. Kết quả: `results/logs/DOCS_GATES_FINAL.log`,
`results/logs/INVARIANT_CHECKS_FINAL.log`, tóm tắt ở `HANDOFF.md` (commit log cuối). Không chạy lại bộ trình duyệt và
T3: byte sản phẩm không đổi, bằng chứng sản phẩm gần nhất là T3 `FULL_PRODUCT_GATE_PASS` tại `a1c53cdb`.

Kết quả tại commit tài liệu `f93408b7` (worktree `D:/tmp/cacc-verify`, `git status` 0 trước và sau, đã gỡ):

| cổng | kết quả |
|---|---|
| byte sản phẩm (`backend/app`, `frontend/src`) so với `903e874c` · so với `284a9bfa` | 0 · 0 file đổi |
| candidate · khoá cache · `CACHE_VERSION` · chế độ mặc định | `b2d4187a` khớp (110 file) · khớp (môi trường `b1714b56`) · 111 · `LLM_ONLY` |
| bề mặt mô hình · hai bản lược đồ | 0 file đổi · trùng byte |
| `docs/evaluation` ngoài run · `docs/legacy` · báo cáo lịch sử trong catalog | 0 · 0 · 0/180 (link thứ 181 là `EVIDENCE_INDEX.md` sống) |
| tách lịch sử của `cuboid-final-review` | khối nguyên văn 0 lỗi, hash khớp; mệnh đề "mọi dòng BASE còn ở một trong hai nơi" báo 25 dòng — đúng 25 dòng run này thay (24 hàng §5, 1 hàng CODE_INDEX), 0 dòng khác (`diagnostics/split_scope_cacc.py`) |
| `git diff --check` · con trỏ §5 · audit tài liệu | exit 0 · 39/39 hàng, 0 file thiếu · PASS |
| test tài liệu | pytest 110 passed · vitest 22/22 |
| kiểm bất biến | con trỏ hiện hành đủ · pytest 349 passed · vitest 9 file / 138 test · dò #14: đúng hai script |

Mệnh đề thứ ba của `split_history_cfr.py --verify` là tính chất của lúc tách (tài liệu sống chưa ai sửa dòng nào từ
BASE); sửa đúng chỗ một con trỏ cũ tất yếu làm nó báo. Các lượt sau nên kiểm khối bằng hai mệnh đề đầu và giải thích
mệnh đề ba theo diff như `split_scope_cacc.py`, không coi nó là cổng bền.

## 7. Giới hạn của run này

- Đối chiếu là đọc mã và chạy test hiện có; không viết test mới (một test chỉ kiểm đường dẫn không chứng minh hành
  vi; thêm file dưới `frontend/src` còn làm cũ dấu vân tay nguồn của bằng chứng trình duyệt).
- #14 dựa trên dò tĩnh; hai script chưa được chạy.
- Ảnh cảnh phục vụ là ảnh w18 trên candidate `d3b4cab9`; khác biệt sản phẩm từ đó chỉ nằm ở đường từ chối (HANDOFF §1.1).
