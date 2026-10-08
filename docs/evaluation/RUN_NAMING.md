# Naming policy — runs, files, folders

> **Một tài liệu sống duy nhất cho mọi quy ước tên** (mở rộng 2026-10-07, run `exact-dimensions`; bảng thứ hai và danh sách giữ tên cập nhật 2026-10-08, run `repo-cleanup`; giữ đường dẫn cũ vì
> báo cáo lịch sử trỏ tới nó). Mục *Tên file và thư mục* ngay dưới là luật HIỆN HÀNH; các mục sau là luật run cũ, còn
> hiệu lực cho run đã đặt tên theo chúng.

## Tên file và thư mục (2026-10-07, run `exact-dimensions`)

- **Tiếng Anh, từ quen thuộc, đúng chức năng.** Folder là danh từ (`fixtures/formation_parity/`); script là động từ
  + đối tượng khi cần (`check-panels.mjs`, `capture-before-after.mjs`, `prune_evidence_images.py`).
- **Không mã lượt trong tên chính**: không `w10`, `m18`, `phase7`, `wave1`. Mã việc/lượt, ngày, commit nằm trong
  metadata (`run.json`, header file); khi phải phân biệt hai lần thực hiện của cùng một việc, thêm ngày giờ
  (`exact-dimensions-2026-10-09`), không thêm `-r2`/`-w02`.
- Không lặp điều đường dẫn đã nói (`domains/geometry/scene3d-chart.ts`, không `geometry-scene3d-chart.ts`); không tên
  mơ hồ (`misc`, `temp1`, `geo2`).
- Theo chuẩn của từng ngôn ngữ: Python `snake_case` (`test_<hành vi>.py`); TS/MJS `kebab-case`; component React
  `PascalCase`; tài liệu trong một run dùng tên ngắn chữ thường: `plan.md`, `report.md`, `review.md`, `handoff.md`,
  `run.json`, `labels.json`.
- **Không đổi**: tên framework/đặc biệt (`AGENTS.md`, `CLAUDE.md`, `package.json`, `conftest.py`), giao diện công
  khai, **run ID và schema ID đã phát hành** (`"w04-panels-probe/1"`, `W04_PANELS_PROBE.json`, thư mục run cũ) — đó là
  danh tính của bằng chứng, không phải nhãn trang trí.
- Đổi tên phần đang hoạt động bằng **commit riêng** không đổi logic: cập nhật import, script, CI, tài liệu sống và mọi
  nơi gọi; kiểm tham chiếu cũ còn sót (`git grep` ngoài `runs/` và `legacy/`); không chụp lại ảnh vì đổi tên.

### Đã đổi (run `exact-dimensions`)

| cũ | mới | chức năng |
|---|---|---|
| `frontend/scripts/w02-closure-probe.mjs` | `frontend/scripts/check-scene-controls.mjs` | đầu dò nhãn theo bước, hình phụ, lưới, bảng bước |
| `frontend/scripts/w04-panels-probe.mjs` | `frontend/scripts/check-panels.mjs` | đầu dò bảng nổi, bố cục, chọn trên hình |
| `frontend/scripts/w05-focus-probe.mjs` | `frontend/scripts/check-focus-mode.mjs` | đầu dò chế độ tập trung |
| `frontend/scripts/capture-phase-evidence.mjs` | `frontend/scripts/capture-before-after.mjs` | ảnh trước/sau một thay đổi — *gỡ ở `repo-cleanup`: nó chụp `.workspace-card` của target Tin học* |
| `backend/tests/geometry/w14_cases.py` | `backend/tests/geometry/route_cases.py` | ca dùng chung qua route sản phẩm |
| `backend/tests/geometry/test_regular_square_pyramid_w02.py` | `…/test_regular_square_pyramid_height.py` | đường cao SO, nguồn chiều cao |
| `backend/tests/geometry/test_regular_square_pyramid_w03.py` | `…/test_asked_segment_construction.py` | đoạn đề hỏi được dựng |
| `backend/tests/geometry/test_regular_square_pyramid_w04.py` | `…/test_segment_on_solid_edge.py` | đoạn trên cạnh khối không vẽ hai lần |
| `backend/tests/geometry/test_source_length_chain_w05.py` | `…/test_source_length_chain.py` | chuỗi độ dài bằng nhau |
| `backend/tests/geometry/fixtures/w14_parity/` | `…/fixtures/formation_parity/` | đặc tả dựng hình năm cấu hình |
| `backend/tests/geometry/fixtures/w14_phan_loai_khoi_truoc.json` | `…/fixtures/solid_classification_baseline.json` | phân loại khối trước đổi |

### Đã đổi (run `repo-cleanup`, 2026-10-08, commit `67e11671`)

| cũ | mới | chức năng |
|---|---|---|
| `backend/scripts/run_phase7a_pilot.py` | `run_holdout_pilot.py` | pilot run that checks the measurement apparatus before the held-out run |
| `backend/scripts/run_phase7b_data_pipeline.py` | `run_holdout_data_pipeline.py` | one command for the held-out data line: validate packet → ingest → … → readiness |
| `backend/scripts/run_phase7b_official.py` | `run_holdout_official.py` | the official held-out run (20 sealed problems × k=3) |
| `backend/scripts/score_phase7b_official.py` | `score_holdout_official.py` | scores the official held-out run from its artifacts |
| `backend/scripts/finalize_phase7b_holdout.py` | `finalize_holdout_intake.py` | after the human copy packet: candidates / accepted / rejected and what is missing |
| `backend/scripts/run_m1_pipeline.py` | `run_holdout_ingest_chain.py` | ingest → pool → scaffold expectation → freeze check → coverage → readiness |
| `backend/scripts/run_wave1_dev_stability.py` | `run_dev_stability.py` | live stability run on DEV problems after the held-out run |
| `backend/scripts/verify_v2_expressibility.py` | `verify_baseline_v2_expressibility.py` | CANONICAL_EXECUTABLE for the clean baseline V2 set (pairs with verify_baseline_expressibility) |
| `backend/tests/geometry/test_construction_bridge_g4.py` | `test_construction_through_point.py` | the four kernel constructions "through a point, parallel/perpendicular to …" |
| `backend/tests/geometry/test_geometry_wave2.py` | `test_dev_failure_regressions.py` | one lock per failure cause of the first DEV run |
| `backend/tests/geometry/test_n04_targeted_registry_v2.py` | `test_targeted_rejection_registry.py` | targeted rejection registry v2 (case N04 scored after the safety repair) |
| `backend/tests/geometry/test_phase5_harness.py` | `test_dev_run_preflight.py` | gate before spending quota on a DEV run (prompt leaks, report axes) |
| `backend/tests/geometry/test_phase66_stabilization.py` | `test_polygon_and_topology_names.py` | construct_polygon contract + vertex-name resolver by topology |
| `backend/tests/geometry/test_phase7b_baseline_immutable.py` | `test_holdout_baseline_immutable.py` | the official held-out evidence is immutable and not DEV data |
| `backend/tests/geometry/test_wave1_grounding_ky_hieu.py` | `test_prime_notation_grounding.py` | prime notation (A′) and grounding agree |
| `backend/tests/geometry/test_wave1_oracle_connectivity.py` | `test_obligation_oracle_connectivity.py` | every obligation kind connects to an oracle key |
| `backend/tests/geometry/test_wave1_scope_goc.py` | `test_angle_scope_gate.py` | angle problems pass the scope gate |
| `backend/tests/geometry/test_wave2_simulatability_va_scorer.py` | `test_scope_gate_and_claim_scorer.py` | both halves of the scope gate + claim scorer asks the checker |
| `backend/tests/geometry/test_wave3_cue_va_thang_do.py` | `test_scope_cues_and_scale_invariance.py` | scope cue table covers the set; oracle is scale-invariant |
| `backend/tests/geometry/test_evaluation_integrity_7a1.py` | `test_evaluation_integrity.py` | evaluation integrity of the held-out apparatus |
| `backend/tests/geometry/test_expectation_contract_7a2.py` | `test_expectation_contract.py` | obligation expectations separate from the measuring code |
| `backend/tests/geometry/test_holdout_readiness_7b.py` | `test_holdout_readiness.py` | held-out pool readiness report and data line |
| `backend/tests/test_v3_live_entrypoint_wiring.py` | `test_curved_acceptance_entrypoint.py` | the live curved acceptance entry point uses the sealed pool |
| `backend/tests/test_v3_product_path_parity.py` | `test_curved_acceptance_product_path.py` | curved acceptance scores on the product layer |
| `backend/tests/test_v3_runner_manifest_integration.py` | `test_curved_acceptance_manifest.py` | curved acceptance runner goes through the integrity layer |
| `backend/tests/test_v3_threshold_and_run_identity.py` | `test_curved_acceptance_threshold.py` | thresholds and run identity locked before results |
| `frontend/scripts/certify-construction-bridge-g4.mjs` | `certify-construction-through-point.mjs` | browser check of the through-point constructions |
| `frontend/src/components/transport-w7.test.tsx` | `transport-policy.test.tsx` | transport tray policy of registered simulations |
| `frontend/src/components/control-layout-w4b3e.test.ts` | `control-layout.test.ts` | layout of the player control strip |
| `backend/tests/test_m17_wave0_artifacts.py` + `test_m17_wave1_artifacts.py` | `test_informatics_evidence_pins.py` | pin SHA-256 bằng chứng catalog Tin học `m17/wave0`, `m17/wave1` (gộp, khẳng định giữ nguyên) |
| `Phase8LiveTransport` (lớp trong `run_rectangular_pyramid_live_analyze.py`) | `LiveAnalyzeTransport` | transport của lượt live analyze một request |

### Đã đổi (run `docs-cleanup`, 2026-10-08)

| cũ | mới | chức năng |
|---|---|---|
| 123 hàm `test_w16_…`/`test_w17_…`/`test_w18_…`/`test_w20_…`/`test_w01_…`/`test_w05_…`/`test_w11_…`/`test_w12_…`/`test_w14_…`/`test_phase3_…` trong 17 file pytest | bỏ tiền tố mã (`test_w17_doc_quan_he_cat` → `test_doc_quan_he_cat`) | phần còn lại vốn đã là mô tả hành vi; không va tên, thu thập 7242 trước/sau |
| `test_nhan_cua_ca_dung_trong_ho_so_w02` | `test_ca_canh_ben_the_tich_mang_nhan_phuc_vu_16` | nhãn ca S1 (cạnh bên → thể tích) là `served:16` |
| `test_registered_scene_is_the_reviewed_one_and_w10_keeps_its_geometry` | `…_and_the_playback_fixture_keeps_its_geometry` | fixture `w10-pedagogical-playback` giữ hình học của cảnh đã duyệt |
| `test_w17_o_do_W17_co_mat_khi_bo_chay_da_do` · `test_w17_ho_khong_khai_loai_W17_khong_can_o_ay` | `test_o_tu_choi_them_ca_phuc_vu_va_cong_tac_co_mat_khi_bo_chay_da_do` · `test_ho_khong_khai_tu_choi_them_khong_can_o_ay` | ô từ chối thêm / ca phục vụ / công tắc của sheet bằng chứng |
| tiêu đề vitest (74) và node:test (44) mở đầu bằng thẻ (`W4 · `, `(M9-UX5) `, `W8 §10 — `, `regular-triangular-pyramid-w01 · D2: `, `W15 `) | bỏ thẻ; ghi chú xuất xứ nằm giữa tiêu đề giữ nguyên | tiêu đề nói hành vi |
| bộ chọn `-k w16`/`-k w17`/`-k w18` trong `CODE_INDEX`, `ARCHITECTURE_MAP`, `OPEN_ISSUES` | đường dẫn file test (tập lớn hơn, vẫn chứa các test ấy) | lệnh kiểm |
| `docs/legacy/superpowers/specs/2026-08-20-semantic-program-generative-route-design.md` · `…/plans/2026-08-20-semantic-program-generative-route.md` | `docs/legacy/architecture/SEMANTIC_PROGRAM_ROUTE_DESIGN.md` · `…/SEMANTIC_PROGRAM_ROUTE_PLAN.md` | thiết kế gốc + kế hoạch đã thực thi của route Semantic Program; thư mục mang tên công cụ (`superpowers/`) hết lý do tồn tại |
| `docs/legacy/architecture/CUBOID_CUBE_CONTRACT_DECISION.md` | `docs/architecture/CUBOID_CUBE_CONTRACT_DECISION.md` | contract hình hộp/lập phương/lăng trụ đáy vuông còn hiệu lực |

### Giữ tên có chủ đích (tra cứu, cập nhật ở run `repo-cleanup`, `docs-cleanup`)

- **Phiên bản của dữ liệu / chính sách / chỉ số** — danh tính của thứ được đo, không phải mã lượt: `clean_baseline_v2_cases.py`,
  `run_clean_baseline_v2.py`, `verify_baseline_v2_expressibility.py`, `spot-check-baseline-v2.mjs` (bộ đề V2), `seal_curved_v3.py`,
  `policies/curved_v3_*.json` (pool V3 hình cong), `run_curved_ergonomics_v2.py` (lượt V2 của probe), `reliability_v2.py` +
  `test_reliability_v2.py` (chỉ số Reliability V2), `synthesis_repair_trace_v1_c02_redacted.json` (lược đồ vết v1, ca c02),
  `c03_vision_extraction_replay_redacted.json` / `photo-c03-diagram-only.fixture.json` (ca c03 của bộ ảnh), `fixtures_coverage_18.py`.
- **Tên khái niệm trong mã**: `test_coverage_gate_c1a.py`, `test_coverage_gate_c1b.py`, `test_c2_fail_closed.py` (các vế C₁a/C₁b/C₂ của
  `coverage_gate`), `run_stability_k3.py` (`k = 3`), `wave_counters.py` ("wave" = một lượt đo, khái niệm của bộ đo).
- ~~Tên test có mã lượt theo sau là mô tả (`-k w17`)~~ — **hết hiệu lực ở run `docs-cleanup`**: bộ chọn không phải lý do
  giữ tên khó hiểu; các tên ấy đã đổi (bảng trên). Còn lại có lý do: `test_wave0_*`/`test_wave1_*` trong
  `test_informatics_evidence_pins.py` (gọi tên thư mục bằng chứng `m17/wave0`, `m17/wave1` mà chúng đọc), `test_gm10_*`
  (`GM10` là mã một đề, không phải mã lượt). Hằng nội bộ có mã lượt trong script (`TEN_TU_CHOI_W17`, `W17_STATES` của
  `build_scene3d_visual_evidence.py`) là định danh mã, chưa đổi — đổi thì cùng lượt chạm script ấy.
- **Revision Alembic** `backend/alembic/versions/f32f9b107b77_m18_accounts_and_classroom.py`: chuỗi migration là lịch sử
  của schema; tên file do Alembic sinh lúc tạo, DB ghi revision id chứ không ghi tên — đổi không lợi gì, giữ.
- **Bằng chứng đã phát hành**: mọi thư mục `docs/evaluation/**` cũ (gồm `m17/wave0`, `m17/wave1`, `semantic-benchmark/sealed/`), báo
  cáo lịch sử ở gốc `docs/` (`PHASE_*`, `W12_REMAINING.md`, …), tên artifact (`W02_CLOSURE_PROBE.json`, …) và schema id
  (`"w04-panels-probe/1"`): bất biến. Bằng chứng cũ trích đường dẫn script/test **tại commit của nó** — đổi tên ở HEAD không
  phá liên kết ấy (git giữ bản cũ).
- Script chứng nhận thời Tin học từng ghi ở đây (`certify-*-w12.mjs`, `*-w7.mjs`, `accept-classroom-m18.mjs`, `capture-w3-*.mjs`,
  `quiz-dominance-w12.mjs`, `measure-tool-first-w5.mjs`, `transport-w7.test.tsx`) — **đã xử lý ở `repo-cleanup`**: gỡ (miền đã
  bỏ) hoặc đổi tên (`transport-policy.test.tsx`); danh sách gỡ: `docs/evaluation/geometry/runs/repo-cleanup/inventory.json`.

## Run (luật trước 2026-10-07, giữ cho run đã đặt tên theo nó)

Mọi evaluation run mới dùng định danh ngắn, ổn định, **không có ngày**. Từ 2026-10-05 wave được đánh số **trong
từng việc** (mục *Đánh số wave theo từng việc* dưới đây):

```text
<task-slug>-wNN          wave thứ NN của việc <task-slug>; cũng là tên thư mục run
<task-slug>-<mục-đích>   run không đánh số của việc ấy (vd lượt chốt trước khi merge)
```

Run đặt tên trước đó dùng `wNN-short-slug` (ví dụ `w09-verify-cleanup`, `w10-pedagogical-playback`,
`w11-pedagogical-polish`) và giữ nguyên tên.

## Quy tắc

- Dùng `lower-kebab-case`; độ dài toàn bộ run ID nên không quá 40 ký tự.
- `short-slug` chỉ mô tả một mục tiêu chính. Không dùng nguyên câu hoặc toàn bộ
  task name làm tên thư mục.
- `wNN` là số wave trong chuỗi đánh giá liên quan. Khi phải lặp cùng một run,
  thêm hậu tố `-r1`, `-r2`, ...; không ghi đè artifact đã commit.
- Ngày, giờ, full task name, phase, branch, product/candidate/measurement commit
  SHA và môi trường chạy thuộc về `RUN.json`, không thuộc tên thư mục.
- Các run đã commit trước policy này giữ tên cũ (`LEGACY_DATED_RUN_ID` /
  `LEGACY_LONG_RUN_ID`): không đổi tên, không di chuyển, không sửa liên kết lịch
  sử — trừ các ngoại lệ do người dùng quyết ở bảng dưới. Run
  `20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair` là
  một ví dụ được giữ nguyên.

## Đánh số wave theo từng việc (2026-10-05, run `cuboid-final-review`)

- **Việc** = một mục tiêu làm trên một nhánh riêng. `task-slug` là `lower-kebab-case`, ngắn (định danh đầy đủ
  `<task-slug>-wNN` không quá 40 ký tự), đặt khi tạo nhánh và **không đổi** — kể cả sau khi nhánh đã merge và bị xoá.
  `RUN.json` ghi `task_slug` và `branch`.
- Việc mới trên nhánh mới **bắt đầu ở W1**, rồi W2, W3…; số wave không nối tiếp từ việc trước.
- **Định danh đầy đủ** `<task-slug>-wNN` (hai chữ số, `-w01`) là thứ được ghi vào manifest, `RUN.json`,
  `EVIDENCE_INDEX`, `STATUS_LEDGER`, `CURRENT_STATE`, `OPEN_ISSUES` và mọi chỉ mục — **không bao giờ** `W1`/`W2` trần,
  vì việc nào cũng có W1. Văn xuôi bên trong chính run được viết tắt khi không thể nhầm.
- Tên thư mục run là định danh đầy đủ (ngắn); ngày, nhánh, commit đo, candidate và môi trường ghi trong `RUN.json`,
  không ghi vào tên. Chạy lại cùng một wave: hậu tố `-r1`, `-r2` như trên.
- Nhánh của việc mới **chỉ rẽ từ `main` đã tích hợp và cập nhật**: `git fetch`, `main` trùng `origin/main`, việc trước
  đã merge (hoặc được ghi rõ là bỏ) — không rẽ từ một nhánh tính năng khác.
- Các wave đặt tên trước quy tắc này — **W1–W20**, gồm các thư mục `w09-…` … `w20-…` và các `WAVE_ID` đã commit — giữ
  nguyên tên. Việc đang làm khi quy tắc ra đời có slug `cuboid-visual-semantic-closure` (nhánh
  `fix/cuboid-visual-semantic-closure`); trích các wave của nó ở mục mới bằng `cuboid-visual-semantic-closure-w20` hoặc
  bằng tên thư mục run. Lượt chốt của việc ấy là run `cuboid-final-review` (tên do brief đặt trước quy tắc này, viết tắt
  slug — không theo mẫu `<task-slug>-<mục-đích>`): không đánh số, không bắt đầu lại W1. Việc kế tiếp, trên nhánh mới từ
  `main` đã cập nhật, bắt đầu ở W1.

## Đổi tên do người dùng quyết (2026-09-29, wave w11)

| thư mục hiện tại | tên cũ (vẫn là `run_id` trong `RUN.json` của run) |
|---|---|
| `runs/w09-verify-cleanup/` | `20260928-w09-verify-cleanup` |
| `runs/w10-pedagogical-playback/` | `20260928-w10-pedagogical-playback` |

Nội dung hai run giữ nguyên từng byte (534/534 tệp); chỉ đường dẫn đổi. Test và
tài liệu sống trỏ tên mới; báo cáo lịch sử bên trong các run có thể còn nhắc
tên cũ — tra bảng này.

## Cấu trúc chuẩn

```text
<run-id>/
  README.md
  REPORT.md
  HANDOFF.md
  RUN.json
  MANIFEST.json
  inputs/
  results/
  images/
    overview/          # chỉ mục lục, không thay ảnh của từng họ
    <family>/          # contact sheet riêng + ảnh nguồn full-resolution
  diagnostics/         # không bao giờ nằm trong contact sheet nghiệm thu
```

Run không phải run ảnh có thể bỏ `images/`. Nếu một nhánh không có artifact
(ví dụ không có diagnostics), manifest phải ghi rõ `NOT_APPLICABLE`; không tạo
dữ liệu giả chỉ để lấp thư mục.
