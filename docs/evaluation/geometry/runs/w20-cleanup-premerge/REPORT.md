# REPORT — W20 dọn kho và đóng tính đúng trước merge

`W20_REPOSITORY_CLEANUP_AND_PREMERGE_CORRECTNESS_CLOSURE` · nhánh `fix/cuboid-visual-semantic-closure` · bắt đầu
`2cb4ed8c` (END_HEAD của W19) · 2026-10-04 → 2026-10-05 · 0 lượt gọi model. Kế hoạch: [`PLAN.md`](PLAN.md); bàn giao
và các trường bắt buộc: [`HANDOFF.md`](HANDOFF.md).

## 0. Kết luận

**`READY_FOR_HUMAN_VISUAL_REVIEW`.** Hai issue chặn đã đóng bằng bằng chứng, kiểm chứng có thẩm quyền trong worktree
tách rời sạch đều xanh, bằng chứng lịch sử không đổi một byte. Còn thiếu đúng một điều kiện merge: người dùng chưa
duyệt hình (W18-H1, trạng thái `NOT_APPROVED`). Vì vậy W20 không merge, không push, không xoá nhánh.

| việc | kết quả |
|---|---|
| `ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET` | **RESOLVED** — probe 20/27 → 26/27 (hàng còn lại không liên quan, ghi trước bản sửa); census 179 hàng không đổi |
| `ISSUE-OPS-TEST-SUITE-WRITES-FROZEN-EVIDENCE` | **RESOLVED** — chạy toàn bộ backend ở cây chính không còn đổi file đông cứng nào |
| AGENTS/RULES | sáu luật ngắn + làm rõ CODE/TESTS, không nhân đôi luật |
| Dọn dẹp | 64 mục xoá có bằng chứng cơ giới; `docs/legacy/superpowers/` giữ cả 18 (lý do từng file) |
| Kiểm chứng (`5fbb397b`) | T3 `FULL_PRODUCT_GATE_PASS`; cổng danh tính, audit tài liệu, harness node, probe, tiêm lỗi đều đạt |
| Candidate · cache | `d3b4cab9…` → `27c31de6…` (đóng băng hai lần, có khai) · 110 → **111** (có chứng minh hàng cache) |

## 1. Literal-target: đích của quan hệ đặt bằng toạ độ

**Nguyên nhân gốc.** Luật "điểm đề định nghĩa bằng quan hệ phải được dựng" bị chia rời rạc:
- grounding ⑦ chỉ phủ đích của `segment_division` (trung điểm, chia đoạn);
- grounding ⑥ chỉ phủ nhánh giả thiết mô hình không trích fact;
- cả hai bỏ qua mọi tên đã có câu lệnh ghi (`computed`);
- `construction_binding` (W18) chỉ nhìn thấy câu lệnh dựng, không nhìn khai báo hay bí danh.

**Probe trước bản sửa** (nhãn đăng ký trước, biên `run_pipeline`, `results/LITERAL_TARGET_PROBE_before-r2_2cb4ed8c.json`):
20/27 khớp. Ngoài vùng đa diện, hình chiếu đặt bằng toạ độ được phục vụ — L14 với đáp số **sai** 2√14 thay vì 3√6.
Toạ độ rồi mới dựng (L16), `assign H = var A` (L17: phục vụ SA = 6 thay cho SH) và bí danh của điểm đặt bằng toạ độ
(L18) cũng được phục vụ.

**Bản sửa — một thẩm quyền** (`65c90bde`, luật ở amendment §17). `construction_binding` lần theo chuỗi
`assign X = var Y` của mỗi tên mang đúng ký hiệu đích. Có toạ độ ở bất kỳ mắt nào ⇒ `DEFINED_BY_COORDINATES` ⇒ từ
chối ở mọi vùng với `CONSTRUCTION_REPLACED_BY_COORDINATES` (nguyên nhân CONSTRUCTION, không gửi đi sửa). Module không
đọc giá trị toạ độ nào. Lời người học nêu quan hệ của đề và việc chương trình đã làm, nói hệ **chưa kiểm chứng**
được, không nói đề sai.
- Không mở rộng grounding ⑦: cả hai mã đều không được gửi đi sửa, nên một cổng thứ hai không thêm cơ hội sửa nào mà
  lại nhân đôi từ vựng §16.1 (ruling trong ledger).
- Mã mới thay vì dùng lại `CONSTRUCTION_NOT_TEXT_BOUND`: lời của mã cũ nói đáp số "tính trên một hình khác", sai khi
  toạ độ đúng.

**Đo sau bản sửa.**
- Probe `after_65c90bde` = `final_5fbb397b`: **26/27**. Hàng còn lại là C7: cổng miền của pipeline chặn manh mối
  "độ dài" (`ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE`, đã mở từ trước). Điều này ghi ở `amendment_1` của nhãn TRƯỚC bản
  sửa; đối chứng thay thế C9 được phục vụ.
- 72 test mới (`test_construction_binding_literal.py` 69, đối soát 3); đỏ đúng lý do trước khi sửa
  (`results/logs/RED_*.log`).
- Census W14–W18 (`diagnostics/CONSTRUCTION_BINDING_DECISION_W20.json`): SHIP, AC2 18/18, 179 hàng so với W18, không
  hàng nào đổi tuyến.
- Quét 527 chương trình đã lưu (`diagnostics/LITERAL_THEN_CONSTRUCT_SCAN.json`): mẫu "khai toạ độ rồi mới dựng" chỉ
  có ở hàng L16 của chính corpus W20 ⇒ không thấy rủi ro từ chối thừa trên dữ liệu đã có.
- Tiêm lỗi (`results/logs/FAULT_INJECTION_W20_r3.log`): FL1–FL7 bị bắt. FL8/FL9 gỡ guard ⑥/⑦ của grounding mà không
  test nào đỏ — các hàng ấy vẫn bị từ chối, nay ở chặng `construction_binding` (phòng thủ nhiều lớp, đúng thiết kế).

**Cache.** Sáu yêu cầu từng được phục vụ vẫn HIT dưới 110 dù W20 từ chối (`diagnostics/PROOF_CACHE_ROW_W20.json`) ⇒
bump **110 → 111** cùng mọi chỗ ghim; khoá danh tính tái sinh; vân tay bề mặt mô hình `b1714b566e25c912` không đổi.

## 2. Test không còn ghi vào bằng chứng đông cứng

**Nguyên nhân gốc** (`diagnostics/FROZEN_WRITER_REPRODUCTION.json`, tái hiện trên bản sao tạm).
`run_reconciliation()` luôn ghi bốn file vào thư mục đông cứng. Trường `note` của `SOURCE_EVIDENCE_INTEGRITY.json`
phụ thuộc một file ngoài kho (scratch của công cụ khác) — file ấy có lúc đóng băng, nay không còn. CRLF không phải
nguyên nhân.

**Bản sửa** (`4e647861`, `654beda3`): thư mục ra BẮT BUỘC; từ chối thư mục đông cứng và mọi thư mục con; CLI cần
`--out`; test dùng `tmp_path` và so hash + `git status` của thư mục đông cứng trước/sau. Tiêm lỗi FE1–FE3 bị bắt.
Bằng chứng ở mức toàn bộ: lượt backend đầy đủ ở cây chính (`8b6a1a3a`) để `git status` y nguyên. Trong worktree kiểm
chứng, sau T3 và mọi cổng, file đã theo dõi không đổi (`results/logs/WORKTREE_STATUS_AFTER_5fbb397b.log`).

## 3. AGENTS.md và RULES.md

`a36f3e97`. Mỗi luật nằm đúng một chỗ:
- `AGENTS.md` §2: mặc định không merge/push. Có phép rõ ràng VÀ đạt điều kiện nghiệm thu thì merge thẳng `main`,
  push, xoá nhánh đã merge.
- `AGENTS.md` §4:
  - bằng chứng đông cứng của wave trước bất biến;
  - nháp/ledger của công cụ agent không tự động là bằng chứng bất biến;
  - dọn có kiểm (đọc, kiểm tham chiếu, chuyển thông tin duy nhất, xoá theo đường dẫn chính xác);
  - test không ghi bằng chứng đông cứng;
  - tự động hoá không ghi `APPROVED_BY_USER`.
- `RULES.md` §1: CODE/TESTS thắng về việc hệ *đang làm gì*, nhưng là cơ sở tái hiện, không phải thẩm quyền về việc
  hệ *phải làm gì*.
- Luật bảo toàn thay đổi của người dùng giữ nguyên.

## 4. Dọn dẹp

Kiểm kê: `inventory/CLEANUP_INVENTORY.json` (script `diagnostics/inventory_cleanup_w20.py`). Nhật ký xoá:
`inventory/DELETION_LOG.json` — mỗi mục có lý do, bằng chứng, nơi tham chiếu, cách khôi phục.

| vùng | xoá | giữ |
|---|---|---|
| `docs/legacy/superpowers/` (18) | 0 | 18: trích bởi tài liệu sống, hoặc giải thích mã còn chạy (`ThreeDMeaning`, `SamplePreview`, kiểu nghĩa vụ `tree_traversal.*`, `no-verdict.test.ts`, `capability-descriptors.json`); M16 là bằng chứng nghiên cứu |
| `.superpowers/` (196 file) | 56: 46 gói review tái tạo từng byte từ git, 10 brief mà mọi dòng nằm trong plan đã commit | 140: 108 `REVIEW_REQUIRED` (báo cáo subagent, ledger, log, 7 brief M16 có dòng không nằm trong plan nào, nháp và trạng thái brainstorm — chưa chứng minh là trùng; thư mục git-ignore nên xoá là mất hẳn), 29 brief W14 (bản duy nhất còn lại của plan W14), ledger W20, bản sao CLAUDE.md của W19, `.gitignore` |
| `D:/tmp` (212) | 8: 6 file trùng blob reachable, 1 file rỗng, 1 bản clone sạch | 204 `REVIEW_REQUIRED` (gồm hai bản backup settings, không mở) |
| mục W19 đã đăng ký | 0 | kế hoạch W19, CLAUDE.md cục bộ, `HOLDOUT_ACQUISITION_LOG.md` ngoài kho (duy nhất) |

Không xoá theo tên thư mục, không ký tự đại diện, không ép xoá. Mỗi file xoá được kiểm lại SHA-256 ngay trước khi
xoá (`diagnostics/apply_cleanup_w20.ps1`). Mọi mục xoá chỉ được nhắc tên trong các bảng kiểm kê đông cứng của W19/W15.

**Quan sát (không mở issue, chưa đủ bằng chứng là lỗi).** Tàn dư của danh mục Tin học còn trong mã sản phẩm, ví dụ
tên thủ tục `tree_traversal.*` ở `semantic_program/obligations.py::SEMANTIC_PRESCRIBED_PROCEDURES`, và
`protocol_encapsulation` ở vài file frontend/prompt. Gỡ chúng đụng taxonomy của candidate và bề mặt mô hình, nên
cần một quyết định riêng.

**Issue mới.** `ISSUE-OPS-DOCS-FAULT-INJECTION-TESTS-WRITE-LIVING-DOCS`: năm test tiêm lỗi tài liệu ghi tạm vào
`AGENTS.md`, `docs/ROADMAP.md` hay gốc `docs/` rồi khôi phục. Đây không phải bằng chứng đông cứng, nên không phạm
luật §4.

## 5. Tự rà soát toàn nhánh (không subagent — brief cấm)

- **F1 (Important)** — 8 dòng comment sản phẩm trích luật là "§16.5", vốn là chính sách nhãn của W18. Sửa thành §17
  (`a4f771b3`, chỉ comment). Hash hệ đo đổi ⇒ đóng băng lần hai (`908a1f2c`), có khai; `2a15102b` là candidate
  trung gian.
- **F2 (Important)** — chốt chặn của script đối soát vẫn cho ghi vào thư mục con của thư mục đông cứng. Đã sửa theo
  TDD (`654beda3`; đỏ: "did not raise").
- **F3 (đo rủi ro)** — từ chối thừa: xem §1, quét 527 chương trình.
- **Lỗi bộ đo của chính W20.** Bảng tiêm lỗi sửa ở `654beda3` mang ký tự xuống hàng thật trong chuỗi nên không biên
  dịch. Phát hiện khi chạy r3 trong worktree, sửa ở `aa036c42` (chỉ chẩn đoán). r3 chạy ở commit có backend +
  frontend trùng `5fbb397b`.

## 6. Kiểm chứng có thẩm quyền

Worktree tách rời sạch `D:/tmp/w20 space/algo-sim` (đường dẫn có dấu cách) tại `5fbb397b`.

| lệnh | kết quả |
|---|---|
| `node frontend/scripts/full-gate.mjs` (T3) | **`FULL_PRODUCT_GATE_PASS`** — pytest 7077 passed / 0 failed (1 skipped, 2 deselected), vitest 1058/1058, typecheck + build, demo, bề mặt sập 6/6 (`results/logs/T3_FULL_GATE_5fbb397b.log`) |
| `diagnostics/w20_gates.sh 5fbb397b 2cb4ed8c` | candidate `27c31de6…` và cache 111 `--verify` exit 0; schema ×2 trùng byte (`d852b47c…`), `git status` không đổi; `CHE_DO_MAC_DINH = "LLM_ONLY"`, compiler chưa nối; bề mặt mô hình 0 file đổi; `diff --check` exit 0; audit tài liệu PASS; harness node 70 pass + 2 skip theo thiết kế, 0 fail (`results/logs/GATES_5fbb397b.log`) |
| bất biến bằng chứng | ngoài run W20, `docs/evaluation` chỉ đổi hai registry sống (`EVALUATION_CANDIDATE.json`, `CANDIDATE_DIVERGENCE.json`); 0/181 báo cáo lịch sử trong catalog đổi |
| `probe_literal_target.py --tag final` | 26/27, trùng `after` (`results/LITERAL_TARGET_PROBE_final_5fbb397b.json`) |
| `run_fault_injections_w20.py _r3` (tại `aa036c42`) | FL1–FL7, FE1–FE3 bắt; FL8/FL9 không đỏ đúng thiết kế; nền xanh trước/sau |
| `git status` của worktree sau mọi lượt | file đã theo dõi không đổi; chỉ có output của probe/tiêm lỗi (đã chép và xoá) |

Lượt chạy ở cây chính (không phải thẩm quyền, giữ để truy vết): 12 đỏ = candidate cũ + cây bẩn trước đóng băng
(`results/logs/PYTEST_INTERIM_MAIN_TREE.log`, `PRE_FREEZE_FULL_BACKEND_8b6a1a3a.log`; từng cái đã đọc và phân loại).

## 7. Đính chính và giới hạn

- Commit, log và output trước `a4f771b3` gọi luật W20 là "§16.5" (ví dụ thông điệp commit `65c90bde`,
  `FAULT_INJECTION_W20{,_r2}.log`, trường `rule` của `CONSTRUCTION_BINDING_DECISION_W20.json`). Luật là §17; các bản
  ghi đã commit giữ nguyên chữ cũ, đính chính ở amendment §17.
- Từ vựng §16.1 giữ nguyên (không mở rộng âm thầm). Đích định nghĩa bằng phép khác (giao, tịnh tiến) đi theo §16.3
  như trước.
- Thẻ từ chối ở frontend dùng nhãn loại "hệ dựng lệch với đề bài" cho mọi nguyên nhân CONSTRUCTION, kể cả mã mới;
  lời chi tiết nói đúng giới hạn kiểm chứng. Đây là mục người duyệt (HANDOFF H-W20-2), không sửa giao diện ở W20.
- Không có bằng chứng trình duyệt mới: W20 không đổi giao diện; trạng thái hình ảnh vẫn là của W18 (chờ người duyệt).
