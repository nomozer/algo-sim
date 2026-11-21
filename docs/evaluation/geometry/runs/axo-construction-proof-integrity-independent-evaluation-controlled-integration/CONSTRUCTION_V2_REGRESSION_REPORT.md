# Construction /2 Regression Report (`AXO CONSTRUCTION /2`)

## 1. Phạm vi kiểm thử hồi quy (`0` chỉnh sửa sản phẩm `backend/app/**` & `frontend/**`)

- **Phiên bản ứng viên bị khóa:** `CANDIDATE_V2_FREEZE_SHA256 = 26c9b505fc7796ed9ff6a5c9578701978e92b9c1d6726a8208916a9ea3dca60c` (`14` files tại `backend/experimental/construction_planner/`).
- **Khóa sản phẩm & cache:** `freeze_evaluation_candidate.py --verify` PASS (`123` files, `113a6a7cf6bbc15a…`); `lock_cache_identity.py --verify` PASS (`CACHE_VERSION = 145`, `6233c43c395c9b49…`).
- **Tài nguyên mạng & AI ngoài:** `ALLOW_LIVE_AI = 0`, `GEMINI_API_KEY = ""`, `0` lời gọi AI live.

## 2. Kết quả các bộ kiểm thử trực tiếp

| Bộ kiểm thử | Lệnh chạy | Kết quả đo được | Ghi chú |
| --- | --- | --- | --- |
| Bộ `/1` + `/2` chuyên biệt (`test_verified_construction_graph_and_planner.py` + `test_axo_construction_v2_integrity_and_integration.py`) | `pytest -c backend/pytest.ini backend/tests/geometry/test_verified_construction_graph_and_planner.py backend/tests/geometry/test_axo_construction_v2_integrity_and_integration.py -q` | **`34 passed` in `13.78s` (`0` failed)** | `16` test `/1` §19 + `18` hạng mục `/2` §20 (`D02` 3 chiều, 12 đột biến, `A07`, 6 cờ, `N0`–`N5`, freeze SHA, 9 bất biến gồm `GL(3, Q)`, giới hạn tìm kiếm, `5/5` Group E switching, 6 bất biến trình bày, `VerifiedInputBridge`, `integration_adapter`, `DeterministicModel2BaselineSelector`, `freeze`, `lock_cache`, `git apply --check`, AST oracle, zero AI) |
| Kiểm thử bất biến đột biến & bất biến hình học (`audit_proof_integrity_and_invariance_v2.py`) | `python backend/scripts/audit_proof_integrity_and_invariance_v2.py` | **Exit 0 · `12/12` đột biến bị chặn · `9/9` bất biến PASS · Oracle Isolation `True`** | `11/12` ca từng lọt `/1` đều bị chặn ở `L1`–`L4` / `PresentationValidator` |
| Đối soát 40 ca & 4 nhánh công bằng (`reconcile_and_compare_construction_v2.py`) | `python backend/scripts/reconcile_and_compare_construction_v2.py` | **Exit 0 · `40/40 P_strict` · `40/40 P_metric` · `33/33` L0–L4 · `5/5` Group E · `16/16` `/1` intact** | `v1_immutability.intact = True` |
| Single-shot Holdout `N=60` & Stress (`evaluate_independent_construction_v2.py`) | `python backend/scripts/evaluate_independent_construction_v2.py` | **Exit 0 · `53/60` (`42/44` pos = `95.5%`, `0` đáp số sai, `11/16` exact neg label / `16/16` fail-closed)** | Freeze hash khớp trước & sau khi chạy; depth 2..20 PASS |
| Handoff Patch Dry-Apply (`git apply --check`) | `git apply --check handoff/*.patch` | **`2/2` PASS (`exit 0`)** | `0` chỉnh sửa thực tế trên `backend/app` hay `frontend` |
| **Toàn bộ backend `pytest`** | `pytest -c backend/pytest.ini backend/tests -q` | **`15070 passed, 7 skipped, 3 deselected, 12 xfailed, 0 failed` (`770.27s` / `12m 50s`)** | `0` hồi quy trên toàn kho backend |

## 3. Kiểm tra tài liệu & quản trị kho

- `audit_docs_information_architecture.py`: `PASS` (`0` broken links, `0` secret leaks, `0` unclassified root docs).
- Không có bất kỳ file nào trong `/1`, `/5`–`/8`, `sealed_H1`, `locked_W2_W3`, hay `backend/app/**` và `frontend/**` bị thay đổi ngoài phạm vi `/2`.
