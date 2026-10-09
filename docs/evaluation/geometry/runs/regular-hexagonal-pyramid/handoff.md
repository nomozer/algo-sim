# regular-hexagonal-pyramid — bàn giao cho LOCAL

Nhánh `feat/g05-geometry-capability-expansion` (từ `f20caf8a`), đã push; không merge, không PR.

| commit | nội dung |
|---|---|
| `3357994` | khảo sát G05, tiền đăng ký: plan (ma trận năng lực), 17 nhãn, oracle, ca, probe baseline |
| `6c79243` | bộ đọc + T11 + metric lục giác + C0 lục giác, năng lực sản phẩm, `CACHE_VERSION` 124, khoá, test, ghim, đính chính N4 |
| (commit cuối) | report, handoff, bằng chứng cache, so sánh pytest, OPEN_ISSUES, CODE_INDEX, CURRENT_STATE, ROADMAP |

## Việc LOCAL

1. Toàn bộ pytest + T3 `full-gate.mjs` trên worktree sạch của nhánh (renderer: cảnh lục giác dùng `chart_metric`, đường
   frontend `scene3d-chart.ts` sẵn có — không đổi mã frontend; T3 xác nhận khung affine hiển thị đúng).
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py` — không có `--help`) — mã sản phẩm
   đổi (`shape_constraint.py`, `assumption_gate.py`, `product_capability.py`, `main.py`). Năm test danh tính candidate đỏ
   tới bước này (`results/pytest_compare.json` `new_red`). Không sửa hash tay.
3. Kiểm độc lập bump 124 (`cache/decision.json`, `diagnostics/probe_f20caf8a.log` ↔ `probe_candidate.log`).
4. Xem đính chính nhãn N4 (`label_corrections.json`). Người dùng duyệt; không mở việc mới trong lượt này.

## Kết quả LOCAL (2026-10-10, Windows, 0 lượt gọi model)

- Nhận nhánh: `feat/g05-geometry-capability-expansion` = `dc974a51` khớp `origin`, 4 commit trên `f20caf8a`. Product commit
  thực tế `6c792434`. Sản phẩm đổi `shape_constraint.py`, `assumption_gate.py`, `product_capability.py`, `main.py` (cache) +
  khoá danh tính + ghim test; không kernel/compiler/solver/frontend mới, không `solid_topology`, không logic theo ID ca.
  Không sửa mã sản phẩm LOCAL.

### A. Bằng chứng năng lực

- Probe chạy lại trên `f20caf8a` và nhánh — log TRÙNG BYTE log Cloud. 7 refused → served (H1–H4, H6–H8), H5 phục vụ sai
  1 → 6√3, N4 refused → served 6√3 (đính chính nhãn), 8 hàng biên vẫn từ chối (thiếu chiều cao, mâu thuẫn, suy biến, đáy
  không đều, đề không "đều", mệnh đề chứng minh, phủ định, ngũ giác).
- Toán độc lập (`diagnostics/local_verification/hex_independent.py`, không import sản phẩm): metric Gram dựng từ độ dài CỦA
  ĐỀ tại S, A, B, C, áp lên khung chương trình — mọi hàng phục vụ: sáu cạnh² = b², đỉnh trên pháp tuyến qua tâm O,
  |SO|² = h², V²/SA² = công thức sách V = (√3/2)a²h, l² = h² + a² ⇒ H1 6√3, H2 12, H3 √3, H4 6√3, H5 6√3, H6 3√3,
  H7 √13, H8 3√3/4, N4 6√3 — ALL_OK.
- **N4 CHẤP NHẬN** (chứng minh độc lập bằng metric): e1 = B−A, e2 = C−A, e3 = S−A (khung: S trên A); đề cho e1·e1 = 4,
  e2·e2 = 12, e3·e3 = 13, e1·e2 = 6, e1·e3 = 2, e2·e3 = 6; S − O = e3 + e1 − e2 ⇒ (S−O)·e1 = 0, (S−O)·e2 = 0,
  |S−O|² = 9. Theo metric từ đề, đỉnh NẰM ĐÚNG trên pháp tuyến tại tâm đáy, cao 3 — "trên một đỉnh đáy" chỉ là toạ độ khung;
  cùng hợp đồng với T8 N5 (không dùng tiền lệ làm bằng chứng duy nhất). Ghi chú: `oracle.py` vẫn giữ luật cũ ("chương trình
  phải đều") và chỉ đạt vì `labels.json` giữ nguyên byte; đính chính nằm ở `label_corrections.json`.
- C0: lục giác đều trên mặt x + y + z = 0 cạnh √2, đỉnh (1,1,1) ⇒ V = (√3/2)·2·√3 = 3 phục vụ C0; đỉnh (2,1,0) lệch trục ⇒
  `SOURCE_SHAPE_CONTRADICTS_COORDINATES` (bộ đọc của `main` không phát khẳng định lục giác nên trước đó phục vụ).

### B. Bằng chứng kỹ thuật

- Scene3D (`hex_scene_dump.py`): mọi hàng phục vụ — 1 khối, 7 đỉnh, 7 mặt (1 lục giác + 6 tam giác), Euler 2, không mặt suy
  biến, có `chart_metric`.
- Renderer — mức biến đổi (`hex_render_check.ts`, chính `veKhongGian` của frontend bundle bằng esbuild có sẵn, không sửa
  frontend): hình thế giới là lục giác đều cạnh b, phẳng, đỉnh ⊥ đáy qua tâm, cao h, cạnh bên √(b²+h²) — RENDER_TRANSFORM_OK
  cho cả 9 hàng, gồm H6 (cạnh √3) và H8 (cạnh 1/2).
- Renderer — mức hình thật: `openFixture` có sẵn (`compiler-scene-suite.mjs`) trên `vite preview` của bản build mới, envelope
  thật từ `run_pipeline` (mô hình thay bằng chương trình corpus): H6, H8, N4 ở bước 4/4 vẽ đúng chóp lục giác đều, đỉnh trên
  tâm, cạnh khuất nét đứt (ảnh `diagnostics/local_verification/*.png`). N4 vẽ GIỐNG HỆT chóp đều — renderer áp metric, không
  dùng toạ độ affine thô. Vị trí chữ đáp số trên giao diện không được kiểm trong lượt này.
- Hồi quy: probe C1 chóp đều (235 dòng, gồm Policy A) và probe C0 của ba run trước (29 + 27 + 11): TRÙNG BYTE `main` ↔ nhánh.
- `CACHE_VERSION` 124: H5 đổi giá trị và C0 served → refused tái hiện; `_cache_lookup` trượt hàng `policy_version` khác;
  `lock_cache_identity.py --verify` khớp 124; 0 file bề mặt mô hình đổi; 7 chỗ ghim = 124; `fixture_diff` 49/49 trùng.
- Đóng băng MỘT lần tại `dc974a51`: **`cf47dd61…`** (102 file, product `6c792434`, cache 124; `--verify` khớp —
  `diagnostics/freeze_6c792434.log`); năm đỏ danh tính hết; khai lệch + log tích luỹ + `KHAI_LECH` + manifest Tier-A —
  commit `0fe806ff`.
- Test: 38/38 mới; bộ liên quan (T7/T8, C0 §21–§25, Policy A, G04, G05, compiler, danh tính, tài liệu, `test_api`)
  1620/1620; năm oracle OK; node harness 102/102.
- T3 một lần tại `0fe806ff`: **`FULL_PRODUCT_GATE_PASS`** — pytest 7665 passed / 1 skipped / 2 deselected, vitest
  1040/1040, build, demo, bề mặt sập (`diagnostics/t3_0fe806ff.log`). T3 không chụp hình; kiểm hình thật ở mục trên.

### Giới hạn

`foundation_only`: route kiểm trên chương trình kiểu mô hình, chưa đo Gemini thật; compiler chưa có họ lục giác; chưa hỗ trợ
lăng trụ lục giác/tam giác đều, chóp lục giác đều không tên, ngũ giác đều, đáy theo góc, đáy lõm. Chưa merge `main`, không PR,
không xoá nhánh, không bắt đầu lát kế tiếp — chờ người dùng phê duyệt.
