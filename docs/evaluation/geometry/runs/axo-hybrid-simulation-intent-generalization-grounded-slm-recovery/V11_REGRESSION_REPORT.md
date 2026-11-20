# V11 regression report (P10, Gate J9)

T3 = `npm run test:full` (`frontend/scripts/full-gate.mjs`: pytest · vitest · build · `replay_demo_cases.py` ·
`audit_demo_crash_surface.py`). Chạy trong worktree **detached sạch** `v11-t3-tmp`, Python `ALGO_SIM_PYTHON` = venv của kho.
Log nằm ngoài cây (scratchpad), có ghi sha256.

| lượt | commit | pytest | vitest | build | demo | bề mặt từ chối | phán quyết |
|---|---|---|---|---|---|---|---|
| 1 | `18aadea7b` | 15173 passed / **2 failed** / 9 skipped / 12 xfailed (1180 s) | 145 file / 2075 | ✓ | 5/5 | 6/6 | FAIL — log `aa20d0e6…` |
| 2 | `5895b2c45` | 15174 passed / **1 failed** / 9 skipped / 12 xfailed (838 s) | 145 / 2075 | ✓ | 5/5 | 6/6 | FAIL — log `ece3b9c6…` |
| 3 | xem `run.json` (`t3_detail`) | | | | | | |

## Lỗi và xử lý

- **Lượt 1:** `test_s2_student_language_pilot_runner.py` (2 test). Ba template phê duyệt C21 đang **chờ** owner (K-1,
  S-2, R-1) vẫn ghi `measured_system = ce3e3c4b…`, là candidate của /10, trong khi candidate hiện là `13a32060…`. Đã gắn lại
  bằng `tools/refresh_pending_templates.py`, chép từ /10. Diff chỉ đổi 2 trường hash ở mỗi template; `owner_decision`
  vẫn `PENDING_OWNER_DECISION`, `paid_project_confirmed` vẫn `false`; bản cũ lưu ở `logs/`. Biên nhận:
  `pending_template_refresh.json`, commit `5895b2c45`. Đây là metadata, **không** phải phê duyệt của người.
- **Lượt 2:** `test_inv_08_code_index_paths_exist`. CODE_INDEX trỏ tới `run.json` của run này, khi đó chưa được ghi. Lỗi
  biến mất khi `run.json` được commit.

## Bất biến

- Construction /2 `backend/experimental/construction_planner/` giống từng byte với `03200886a`.
- Run đóng băng /5–/10 không bị sửa. Ba template C21 của `hybrid-master-backend-replacement` là template **đang chờ**,
  được thiết kế để gắn theo runtime hiện hành, giống cách /10 đã làm ở `5a07be9b4`.
- `freeze_evaluation_candidate.py --verify` khớp `13a32060…`. `lock_cache_identity` khớp (`test_cache_identity.py` xanh).
- Cổng tài liệu `test_docs_information_architecture.py` xanh sau khi có `run.json`.
- An toàn công bố: 0 trailer `Co-Authored-By`, 0 `APPROVED_BY_USER` được ghi, 0 khoá API trong cây.
