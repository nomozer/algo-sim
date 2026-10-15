# Result binding — sẵn sàng tích hợp vào main (LOCAL, 2026-10-15)

**Kết luận: `RESULT_BINDING_MAIN_INTEGRATION_GO_AWAITING_APPROVAL`.** Nhánh `research/source-bound-result-planning`
fast-forward được lên `main`. Chưa merge, chưa push, chưa gọi Gemini (0 lượt). Sản phẩm không đổi, không đóng băng lại
candidate, không bump `CACHE_VERSION`. **Tích hợp mã ≠ bật Hybrid**: `LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid trên
sản phẩm vẫn NO-GO.

## 1. Baseline Git và danh tính sản phẩm

| mục | giá trị | cách kiểm |
|---|---|---|
| nhánh / HEAD lúc bắt đầu | `research/source-bound-result-planning` / `11db61a14ae42fe2868882224170758d6a25a73c` | `git rev-parse` |
| `main` = `origin/main` | `2a3c0787cc35d2e5530d77658225039ab4c5991e` | `git rev-parse`; `git fetch --dry-run` không có cập nhật |
| product commit | `efb756aa166e8da18b20971338fece8adf80bc89` | `git diff efb756aa 11db61a1 -- backend frontend/src` rỗng |
| commit T3 | `7b14fe0453b45a3c87e2414ae44f6dc4058c9213` | `verification/t3-pass.json`; SHA log `29b09bf5…` tính lại khớp |
| candidate | `c0a8792f1c491ae40b41c6af5bbb00ed372e1bbc3b6b39c1093e14572b02b79e`, 110 file | `freeze_evaluation_candidate.py --verify` trong worktree sạch: khớp |
| `CACHE_VERSION` / mặc định | `"125"` (`main.py`) / `LLM_ONLY` (`routing.py::CHE_DO_MAC_DINH`) | đọc nguồn |

Main không tiến thêm, nên không có thay đổi ancestry nào phải báo.

## 2. Provider fingerprints

Tính lại bằng serializer chính tắc (`surface_fingerprint()` của tuyến A/B; SHA-256 của
`json.dumps(function_declarations(), ensure_ascii=False, sort_keys=True)`), mỗi commit trong một worktree tách rời sạch.
Chi tiết: [`provider-fingerprints.json`](provider-fingerprints.json).

| bề mặt | `19140e2f` (baseline) | `efb756aa` = `7b14fe04` = `11db61a1` | phân loại |
|---|---|---|---|
| Tuyến A | `912b22ef…` | `7ea511a6…` | CHANGED · INTENTIONALLY_CHANGED · BACKWARD_COMPATIBLE |
| Tuyến B | `145feb18…` | `485d3834…` | CHANGED · INTENTIONALLY_CHANGED · BACKWARD_COMPATIBLE |
| Khai báo hàm | `f2ec9698…` | `5ceb0f99…` | CHANGED · INTENTIONALLY_CHANGED · BACKWARD_COMPATIBLE |

- Tuyến A đổi vì fingerprint của nó bao cả khai báo hàm, mà `orthogonal_projection_line` có thêm `line_ref` tuỳ chọn.
  Lời gọi `line` tường minh cũ vẫn giữ nguyên. Tuyến A **không** nhận được kết quả suy diễn chưa kiểm chứng: gửi `line_ref`
  qua tuyến A sẽ bị từ chối `RESULT_BINDING_UNVERIFIED`
  (`test_route_a_cannot_claim_a_result_reference_certificate`, PASS).
- `PlanningContract`/`PlanningTerm` chỉ là metadata nội bộ: không có trong `function_declarations()` ở bất kỳ commit nào đã đo.
- `provider-surfaces.json` (old/current), các hash trong `reconciliation.json`, test ghim
  `test_provider_surfaces_are_pinned` và `report.md` hiện hành đều khớp số đo. Không đổi schema để ép hash.
- Sau `efb756aa` không còn thay đổi bề mặt nào (UNCHANGED).

## 3. Sai lệch và đính chính

Lớp đính chính nằm ở [`corrections.json`](corrections.json). Receipt gốc giữ nguyên từng byte.

| id | loại | nội dung | ảnh hưởng |
|---|---|---|---|
| C1 | chỉ văn bản | Bản nháp `report.md` tại `f7ae5421` ghi tuyến A "giữ nguyên" (sai) và trích `be38f55f…`/`442d1a0b…`. `reconciliation.json` giải thích hai hash này là "hash lịch sử two-line-plane-section", nhưng điều đó **không đúng**: run đó ghim `145feb18…`/`f2ec9698…`, còn hai chuỗi kia không xuất hiện ở đâu khác trong lịch sử ⇒ nguồn gốc `NOT_RECOVERABLE`. `report.md` đã được sửa đúng từ `c00a5462`. | không ảnh hưởng sản phẩm hay số đo |
| C2 | phạm vi review | Lượt kiểm lại độc lập trong `review.md` thực ra chạy trên `10dd6d6e`. `7b14fe04` sửa tại chỗ `review.md` để gọi `efb756aa` là "Final Re-Verified", trong khi delta 3 dòng của `efb756aa` chưa được ai review độc lập. Phiên này đã review delta đó (cùng phiên, **không** phải fresh-context): `_CHAN_TAN_NGU` dùng chung trở về đúng từng byte như `main`, còn phần từ chối `bình phương`/`nửa` chỉ áp trong `_kiem_phu` và `_kiem_result_binding`. Kết quả: NONBLOCKING, không có Critical/Important. | không phát hiện lỗi sản phẩm |
| C3 | living doc cũ | `TEXT_TO_GEOMETRY_FUNCTIONS_CONTRACT.md` §2 vẫn ghi `geometry-functions/3` và `f2ec9698…` là giá trị hiện hành. | đã sửa tối thiểu thành `/4` và `5ceb0f99…` |

Ghi chú NONBLOCKING từ C2: trên hai đường result-binding mới có test cho `bình phương` nhưng chưa có test cho `nửa`. Một
câu có cụm "nửa mặt phẳng" đứng trước khoảng cách được hỏi sẽ bị từ chối; đây là fail-closed, không phải phục vụ sai.

## 4. Locked corpus và T3

- `next-slice-corpus.json` (`6587fabf…`) và `next-slice-preregistration.md` (`14303fa0…`) chỉ có một commit duy nhất
  (`19140e2f`), SHA khớp: corpus và oracle không bị sửa sau tiền đăng ký.
- Xuất lại `export_result_binding_scenes.py` ở sản phẩm cuối vào một thư mục mới: `corpus-results.json` (`1ceed3f0…`,
  18/18 ca), `scenes.json` (`177665cc…`) và `manifest.json` trùng từng byte với bản đã commit.
- 18/18 `EXACT_MATCH` (6 `SERVED`, 12 `REFUSED`), được kiểm lại qua `test_result_binding_planning.py` trong cổng targeted.
- T3 `FULL_PRODUCT_GATE_PASS` tại `7b14fe04` (backend 9405 passed, frontend 1055, build, demo 5/5, crash 6/6) **được dùng
  lại, không chạy lại**: cây đo từ đó tới nay không đổi, chỉ docs và một dòng allow-list của script audit docs.
- Browser `PASS_CORE_CAUSAL_RENDERING` (SwiftShader + D3D11): receipt được buộc vào `backendSceneSha256 = 177665cc…`.
  Bằng chứng này được chụp ở `f7ae5421` (sản phẩm `b8112f35`). Nó vẫn đúng danh tính vì cảnh xuất lại trùng byte,
  `frontend/src` không có delta so với main, và `frontend/scripts` không đổi kể từ lúc chụp.

## 5. Phạm vi diff `main..research`

12 commit, 73 path, 0 xoá, 0 sửa/đổi tên artifact lịch sử. Lượt này cộng thêm một commit docs: thư mục run này, 7 living
doc/contract và một hằng allow-list.

| loại | path | ghi chú |
|---|---:|---|
| sản phẩm `backend/app` | 5 | `planner.py`, `registry.py`, `engine.py`, `function_route.py`, `fact_extraction.py` — chỉ tuyến D nghiên cứu |
| test | 3 | `test_result_binding_planning.py` (mới), pin bề mặt + mutant, taxonomy benchmark |
| harness | 5 | audit/export offline, visual check; không ảnh hưởng tới định tuyến API |
| evidence mới | 52 | hai thư mục run mới |
| living docs | 7 | chỉ mục/trạng thái |
| candidate | 1 | đóng băng lại `EVALUATION_CANDIDATE.json` |

Không đổi `requirements*.txt`/`package*.json`, không thêm skip/xfail, `frontend/src` không đổi. `main.py`, `ai/pipeline.py`,
`geometry_compiler/`, `semantic_program/` không có delta ⇒ `LLM_ONLY`, API mặc định và cache giữ nguyên.

## 6. Điều kiện fast-forward

`merge-base(main, research) = main`, research đi trước 12 commit, main đi trước 0 ⇒ **fast-forward được**, không có xung
đột và không cần merge thử. Nếu `main` tiến thêm trước khi tích hợp, phải kiểm lại ancestry và delta.

## 7. Kết quả cổng

| cổng | kết quả | receipt |
|---|---|---|
| candidate `--verify` (worktree sạch `7b14fe04`) | khớp, 110 file | [`gates.json`](gates.json) |
| provider fingerprints (4 commit, worktree sạch) | như §2 | [`provider-fingerprints.json`](provider-fingerprints.json) |
| backend targeted (worktree sạch `11db61a1`): result binding, goal decomposition + mutant, ask-operand, clause-role, import-closure, two-line, source grounding, evaluation candidate, API/cache | **616 passed**, 0 fail/skip | [`backend-targeted.xml`](backend-targeted.xml) |
| docs + identity (`test_docs_information_architecture.py`, `test_current_state_identity.py`) trên cây docs của lượt này | xem receipt | [`docs-identity.xml`](docs-identity.xml) |
| frontend | không chạy lại (không có delta `frontend/src`); kế thừa T3 1055 | — |

## 8. Dữ liệu được bảo vệ

- `frontend/public/` (untracked, của người dùng): không động tới, không stage.
- `docs/evaluation/geometry/runs/source-bound-result-planning/**` và `goal-directed-planner-generalization-audit/**`:
  0 byte thay đổi trong lượt này (`git diff` rỗng); đính chính nằm ở lớp mới.
- Không xoá nhánh, không rebase/amend/force, không bump cache, không gọi model. Worktree tạm (4 commit đo fingerprint
  + 1 commit chạy targeted) đều đã `git worktree remove`; `git worktree list` chỉ còn cây chính.

## 9. Hạn chế chưa giải quyết

- Corpus là tập phát triển `NOT_HELD_OUT`; chưa có held-out cho `line_ref`; chưa đo Gemini thật.
- Phạm vi đóng góp: result binding và compose có trần dựa trên effect, cho khoảng cách điểm–giao tuyến trong phạm vi đã
  kiểm. **Không** phải Planner tổng quát cho mọi bài hình học.
- Review của delta `efb756aa` là review trong phiên, không độc lập (C2).
- Scene3D: phát hiện của người dùng trên ảnh hình chóp, hộp và lăng trụ (nét khuất/thấy theo góc camera, đường chồng chéo,
  mặt phẳng lớn che hình, vai trò đoạn vuông góc và chân H, góc nhìn/nhãn/thứ bậc thị giác) đã ghi bổ sung vào
  `ISSUE-ARCH-SCENE3D-CONSTRUCTION-READABILITY`. Ảnh không chứng minh Kernel sai, và browser PASS không phải là
  nghiệm thu chất lượng hình ảnh. Lượt này không triển khai gì.
- Các blocker Hybrid sản phẩm, orbit gate và giới hạn grounding vẫn OPEN như trước.

## 10. Đề xuất

**GO cho fast-forward `main` → tip nhánh nghiên cứu**, với điều kiện người dùng chấp nhận các hạn chế ở §9.
**NO-GO cho việc bật Hybrid** hay chạy pilot live.

## 11. Phương án tích hợp (chỉ để người dùng duyệt, chưa chạy)

```bash
git fetch origin && git rev-parse main origin/main          # phải vẫn = 2a3c0787…
git merge-base --is-ancestor main research/source-bound-result-planning && echo FF_OK
git switch main
git merge --ff-only research/source-bound-result-planning
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/freeze_evaluation_candidate.py --verify
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_docs_information_architecture.py tests/test_current_state_identity.py -q
# chỉ khi được cho phép push riêng:
git push origin main && git ls-remote origin refs/heads/main  # phải khớp main local
```

Giữ nhánh nghiên cứu, không xoá trừ khi được yêu cầu. Kết quả tích hợp ghi ở một run riêng (`…-main-integration`).

## 12. Handoff

[`handoff.md`](handoff.md).
