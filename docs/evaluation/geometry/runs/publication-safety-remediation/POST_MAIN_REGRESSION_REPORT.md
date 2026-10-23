# Báo cáo hồi quy sau main

Nhánh `research/publication-safety-remediation` rẽ từ local `main` = `b4ac5e879b35ac3605ba75c51df5bb6b89352734`.
Thay đổi chỉ gồm tooling, test và docs. `backend/app` cùng measured system **không đổi**, nên không cần candidate mới
và `CACHE_VERSION` giữ `127` (NO_BUMP). Provider calls: 0.

## 1. Thay đổi

| commit | nội dung |
|---|---|
| `76c6795c` | `backend/scripts/check_publication_safety.py`; `backend/tests/test_publication_safety_gate.py`; `publication_exceptions.json` (27 entry, tất cả `PENDING_OWNER_DECISION`); `check_refusal_screens.mjs`; `CODE_INDEX`; **gỡ** `geometry-dir-first-run-before-fixes.log` khỏi tip |
| docs commit (sau T3) | 6 tài liệu của run, `run.json`, receipt và ảnh màn từ chối, log gate, `EVIDENCE_INDEX` (`PUBLICATION_SAFETY_REMEDIATION` + `CORRECTED_BY`) |

## 2. Kiểm tra

| kiểm | commit | kết quả |
|---|---|---|
| gate mechanism `test_publication_safety_gate.py` | trước commit | 12 passed |
| tiêm lỗi: miễn trừ `PENDING` được bỏ qua | scratch | đỏ (`test_pending_exception_still_blocks`) |
| tiêm lỗi: khoá theo path, bỏ SHA-256 | scratch | đỏ (`test_changed_content_of_exempt_blob_is_not_exempt`) |
| tiêm lỗi: in nội dung blob ra output | scratch | đỏ (2 test "no raw text") |
| docs IA + `test_current_state_identity` | trước commit | 45 passed |
| gate repo thật `--head` / `--range origin/main..HEAD` | `76c6795c` | BLOCKED; 105 / 5 dòng, **tất cả thuộc entry PENDING, 0 mới** |
| **Full T3** `full-gate.mjs` | `76c6795c` | **exit 0 `FULL_PRODUCT_GATE_PASS`**: pytest 11,586 passed / 1 skipped / 2 deselected / 15 xfailed; vitest 73 files / 1,238 passed; build PASS; demo 5/5; crash surface 6/6. Cây sạch trước và sau. [`verification/full-t3/execution.json`](verification/full-t3/execution.json) |
| chênh số test so với `main` | `b4ac5e87` → `76c6795c` | +14 collected (11,588 → 11,602): 12 của gate + 2 tham số hoá theo `backend/scripts` trong `test_domain_string.py`; 0 test mất |
| post-T3 freeze `--verify` | `76c6795c` | exit 0, MATCH (116 file, `413ee525…`) |
| màn từ chối `check_refusal_screens.mjs` | `76c6795c` | `REFUSAL_SCREEN_CHECK_PASS`: 50/50 hàng, `tree_clean: true`, 0 lỗi, 0 request bị chặn ([`refusal-screens/receipt.json`](refusal-screens/receipt.json)) |

Không chạy: live/provider, `frontend/scripts/*.node-test.mjs` (không harness nào trong số đó bị sửa), browser acceptance
của Session 5 (consumer không đổi; receipt `browser-final-9f06ed2b` vẫn áp dụng vì `frontend/src` trùng byte).

## 3. Lần T3 bị huỷ (khai minh bạch)

- Lượt 1: lệnh chạy nhầm thư mục (`cd ..` đưa lên `.superpowers/worktrees`), `full-gate.mjs` không tìm thấy, nên dừng ngay
  với `MODULE_NOT_FOUND`. Không đo gì; root checkout không bị ghi.
- Lượt 2: chạy đúng ở `76c6795c`, nhưng agent sửa `EVIDENCE_INDEX.md` và tạo file docs trong worktree **khi pytest đang chạy**
  (khoảng 62%). Cây không còn sạch giữa lượt đo, nên agent đã **dừng** lượt đó và không dùng kết quả.
- Lượt 3: lượt có thẩm quyền. Bản nháp được chuyển ra ngoài, cây sạch trước và sau, không ai ghi vào worktree trong khi chạy.

Ghi chú môi trường: một phiên khác (`scene3d-unified-visual-language`) chạy `tsc -b`/`vitest` song song trên máy. Nó không
đọc hay ghi worktree này, nhưng có thể làm thời gian chạy dài hơn.
