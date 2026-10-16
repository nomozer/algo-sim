# Result binding — final candidate refreeze và authoritative T3 (2026-10-16)

**Trạng thái: `FINAL_RESULT_BINDING_T3_PASS`.** T3 checkpoint `7f355a81`, product `55c657b8`, candidate `30808cb0…`
(110 file). `main` = `origin/main` = `2a3c0787`, không merge, không push, 0 lượt gọi model, `LLM_ONLY`,
`CACHE_VERSION = 125`, Hybrid OFF. `READY_FOR_REVIEW` không có nghĩa là được phép merge.

| trục | kết luận | căn cứ |
|---|---|---|
| CODE_REVIEW | kế thừa (product tree không đổi) | `backend/app` `5bb9a890…`, `backend/tests` `471bee5e…`, `frontend/src` `59dc9534…` trùng `55c657b8` |
| EVIDENCE_REVIEW | PASS | `INDEPENDENT_E1_CONSISTENCY_REVIEW_PASS` cho `7a583590` (báo cáo trong hội thoại, không phải artifact trong kho) |
| CANDIDATE_FREEZE | PASS | §2 |
| AUTHORITATIVE_T3 | PASS | §4 |
| INTEGRATION_READINESS | READY_FOR_REVIEW | §7 |

## 1. Preflight (trước mọi thay đổi)

- HEAD ban đầu `7a58359039edf1fa815813a26597a6f450fc2783` trên `research/source-bound-result-planning`; cây chính chỉ có
  `?? frontend/public/favicon.svg` (của user, giữ nguyên); không submodule; một worktree.
- `git diff --name-only 55c657b8 7a583590` ngoài `docs/`: rỗng. Ba tree sản phẩm trùng `55c657b8`.
- Candidate cũ: `measured_system.tree_hash` `4b95dcc665f5930b74c849164122458ad070af9af24cb085bcfa9217063dee25`, blob
  `033284ce9e17a17e1ca7af360b64b3bb27e0ee92`, đóng băng ở commit `9ce1298f…`, `product_commit_sha` `5f1b576c…`.
- Hash hệ đo tính lại bằng `freeze_evaluation_candidate.measured_system_hash()`: `30808cb0…`, 110 file;
  `product_commit()` = `55c657b8`.
- `--verify` trước refreeze: **exit 1**, lệch `product_commit_sha` và `measured_system.tree_hash`.
- Biên lai nguyên văn: [`preflight-and-freeze.txt`](preflight-and-freeze.txt).

## 2. Refreeze

- Hợp đồng đọc từ mã (`backend/scripts/freeze_evaluation_candidate.py`; script không có `--help`, gọi là chạy): không
  `--verify` ⇒ chỉ ghi `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json` (`write_text`, không ghi file khác);
  `MEASURED_SYSTEM_PATHS` và thuật toán băm không đổi; `commit` = HEAD lúc đóng băng; `cay_lam_viec_sach` tính trước khi ghi.
- Chạy trong worktree detached sạch `D:/tmp/rbfa freeze/algo-sim` tại `7a583590` (status rỗng trước khi chạy).
- Kết quả: `cay_lam_viec_sach: true`, `commit` `7a583590…`, `product_commit_sha` `55c657b8…`, `tree_hash` `30808cb0…`,
  110 file. Diff đúng 5 dòng (`dong_bang_luc`, `commit`, `commit_ngan`, `product_commit_sha`, `tree_hash`); taxonomy,
  primitive, schema, DEV, `cache_version` trùng bản cũ.
- `--verify` sau refreeze: **exit 0**. File copy sang cây chính (SHA-256 CRLF `d7a815e4…` trùng worktree); worktree
  freeze được trả file về rồi gỡ không dùng `--force`.
- Hội tụ: hệ đo chỉ gồm `backend/app` + module `domains/semantic`, không gồm `docs/` ⇒ commit candidate không đổi hash.

## 3. Divergence declaration và checkpoint

- Lớp mới, append-only: [`inputs/candidate_divergence.json`](inputs/candidate_divergence.json), `corrects` =
  `docs/evaluation/geometry/runs/shared-ask-grammar-safety/inputs/candidate_divergence.json` (giữ nguyên).
  `test_thesis_acceptance_matrix.py::_khai_lech_hien_hanh` đi chuỗi `corrects` tới lớp này; C2b PASS.
- Phát hiện khi đọc lớp cũ: nó ghi `current_product_commit` `34a04eaf` cạnh hash `4b95dcc6…`, trong khi candidate ở
  `5fc1645c` ghi `product_commit_sha` `5f1b576c`. Lớp mới lấy giá trị `previous_*` từ file candidate và ghi chú điều
  này ở `previous_layer_note`; lớp cũ không sửa.
- `historical_effect` của lớp mới không khẳng định trước kết quả đo; số đo nằm ở §5.
- **Checkpoint `7f355a81296e655f3b75b0dea345a8b6fc447ae4`** (tree `0a15b4f9…`): đúng 3 file (`EVALUATION_CANDIDATE.json`,
  divergence, preflight receipt); 0 file dưới `backend/` hoặc `frontend/`; không trailer `Co-Authored-By`.

## 4. Authoritative T3

Quy trình của kho: `node frontend/scripts/full-gate.mjs` (`docs/TEST_TIERS.md` T3), từ gốc một worktree detached sạch.

- Môi trường: `D:/tmp/rbfa t3/algo-sim` tại `7f355a81` (đường dẫn có dấu cách). `git status --porcelain
  --untracked-files=all` rỗng trước và sau. `frontend/node_modules` là junction tới bản cài của cây chính (gitignored).
  Python: full-gate chọn `active_venv` = `backend/.venv` của cây chính, 3.12.10; Node v24.13.0, npm 11.6.2.
  Log ghi ngoài worktree rồi chép vào run này.
- `--verify` trong worktree trước T3: exit 0.
- Kết quả, 2026-10-16T02:21:03Z → 02:27:41Z, **exit 0, `FULL_PRODUCT_GATE_PASS`**:

| cổng con | kết quả |
|---|---|
| pytest (toàn bộ backend) | **10046 passed, 0 failed**, 1 skipped, 2 deselected, 6 xfailed (370.2 s) |
| vitest (toàn bộ frontend) | 68/68 file, **1055/1055** |
| typecheck + build | `tsc -b && vite build` exit 0 |
| tập demo khoá luận | `DEMO_REPLAY_PASS 5/5`, `REDUCED_CHAIN_CASES 1/1` |
| bề mặt sập của demo | 6/6 biên đúng kỳ vọng, 0 lần ném 500 |

- Biên lai: [`verification/t3-authoritative.log`](verification/t3-authoritative.log) (nguyên văn) và
  [`verification/t3-pass.json`](verification/t3-pass.json).

**Full geometry gate.** Chín failure từng ghi nhận ở `suite6` của `55c657b8` đều do candidate; chúng nằm trong pytest
toàn bộ backend trên. Đo bổ sung bằng `-rA` cùng worktree sau T3: 17/17 PASS, gồm `test_tien_kiem_kho`, cả 5 mục
`test_branch_independent_harness` từng đỏ (kèm các mục cùng file), `test_inv_20`, `test_inv_05`, `test_C2b`
([`verification/former-candidate-failures.txt`](verification/former-candidate-failures.txt)).

## 5. Đo bổ sung (KHÔNG thuộc chứng chỉ T3)

Cùng worktree, sau T3, output ra `D:/tmp/rbfa-supp` ngoài worktree, `ALLOW_LIVE_AI=0`; status rỗng trước và sau
([`verification/supplementary-measurements.txt`](verification/supplementary-measurements.txt)). So bằng byte (CRLF → LF)
với blob đã commit:

| phép đo | kết quả | so với baseline |
|---|---|---|
| Corpus khoá 18/18 (`export_result_binding_scenes.py`) | `scenes.json`, `corpus-results.json`, `manifest.json` | **trùng byte** với `source-bound-result-planning/visual/` |
| Benchmark 30 (`measure_hybrid_compiler_benchmark.py`) | correct_served 19 · correct_refusal 9 · wrong_served 0 · false_refusal 2 (`B27`, `B28`) | **trùng byte** với hai bản đã commit |
| Two-line development / heldout | 45 ca: 12 served / 33 refusal; 32 ca: 11 / 21; `failures: []` | chỉ khác `candidate` và `product_commit` (định danh); mọi dòng khác trùng ([`two-line-field-diff.txt`](verification/two-line-field-diff.txt)) |
| `grammar_probe.py` (gốc, không sửa) | B: 84 CR · 33 CS · **0 WS** · 6 FR; A: 52 CR · 16 CS · **0 WS** · 4 FR | **trùng byte** với `shared-ask-grammar-safety/verification/suite3-grammar-probe.json` |
| Provider fingerprints | A `7ea511a6…`, B `485d3834…`, khai báo hàm `5ceb0f99…` | trùng giá trị đã ghi cho `efb756aa` |

10 `FALSE_REFUSAL` của probe là nhãn oracle lịch sử cho hai mẫu câu làm tròn mà chính sách fail-closed từ chối có chủ
đích (`shared-ask-grammar-safety/report.md` §8.2); expected không bị đổi.

## 6. Giới hạn đã biết

- Cổng trình duyệt (`scene3d-orbit-gate`, kiểm nhân quả) không thuộc T3 và **không chạy** ở đây. `frontend/src` không
  đổi từ `efb756aa` tới `55c657b8` (0 file), nhưng biên lai trình duyệt gần nhất
  (`source-bound-result-planning-integration-readiness`, `PASS_CORE_CAUSAL_RENDERING`) buộc vào `backendSceneSha256`
  `177665cc…` của backend lúc đó; `registry.py` đã đổi sau đó nên biên lai ấy **không chuyển** sang candidate này.
- Node harness `frontend/scripts/*.node-test.mjs` nằm ngoài T3 và không chạy.
- Giới hạn sản phẩm từ code review vẫn giữ: mutation nguồn M5/M6 sống sót, yêu cầu làm tròn và số đo góc bị từ chối
  theo chính sách, bài nhiều câu hỏi trả lời một phần, `B27`/`B28` false refusal (strict xfail).
- Review độc lập E-1 và code review không có artifact trong kho.

## 7. Integration readiness

`READY_FOR_REVIEW` cho một integration review riêng. Bước đó cần user cho phép rõ ràng; phiên này không merge, không
push, không đổi production default, không bật Hybrid. Commit công bố bằng chứng (sau checkpoint) chỉ chạm `docs/`; hash
hệ đo được kiểm lại sau commit đó ([`handoff.md`](handoff.md)). Danh sách băm: [`hashes.json`](hashes.json).
