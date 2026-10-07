# Naming policy — runs, files, folders

> **Một tài liệu sống duy nhất cho mọi quy ước tên** (mở rộng 2026-10-07, run `exact-dimensions`; giữ đường dẫn cũ vì
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
| `frontend/scripts/capture-phase-evidence.mjs` | `frontend/scripts/capture-before-after.mjs` | ảnh trước/sau một thay đổi |
| `backend/tests/geometry/w14_cases.py` | `backend/tests/geometry/route_cases.py` | ca dùng chung qua route sản phẩm |
| `backend/tests/geometry/test_regular_square_pyramid_w02.py` | `…/test_regular_square_pyramid_height.py` | đường cao SO, nguồn chiều cao |
| `backend/tests/geometry/test_regular_square_pyramid_w03.py` | `…/test_asked_segment_construction.py` | đoạn đề hỏi được dựng |
| `backend/tests/geometry/test_regular_square_pyramid_w04.py` | `…/test_segment_on_solid_edge.py` | đoạn trên cạnh khối không vẽ hai lần |
| `backend/tests/geometry/test_source_length_chain_w05.py` | `…/test_source_length_chain.py` | chuỗi độ dài bằng nhau |
| `backend/tests/geometry/fixtures/w14_parity/` | `…/fixtures/formation_parity/` | đặc tả dựng hình năm cấu hình |
| `backend/tests/geometry/fixtures/w14_phan_loai_khoi_truoc.json` | `…/fixtures/solid_classification_baseline.json` | phân loại khối trước đổi |

### Giữ tên có chủ đích (tra cứu)

- Bằng chứng khoá luận cũ trích theo đường dẫn — **giữ**: `backend/scripts/{run_phase7a_pilot,run_phase7b_*,score_phase7b_official,finalize_phase7b_holdout,run_wave1_dev_stability,run_m1_pipeline,wave_counters}.py`, các test khoá chúng (`test_phase*`, `test_wave*`, `test_m17_wave*`, `test_geometry_wave2.py`), `backend/app/evaluation/wave_snapshots.py` ("wave" là khái niệm của miền đánh giá).
- Script chứng nhận thời Tin học (`frontend/scripts/certify-*-w12.mjs`, `*-w7.mjs`, `accept-classroom-m18.mjs`,
  `capture-w3-*.mjs`, `quiz-dominance-w12.mjs`, `measure-tool-first-w5.mjs`) và `frontend/src/components/transport-w7.test.tsx`: không thuộc luồng hình học đang chạy; gỡ hay đổi tên là một quyết định dọn kho riêng, chưa làm.
- Báo cáo lịch sử ở gốc `docs/` (`PHASE_*`, `W12_REMAINING.md`, …) và mọi thư mục `runs/` cũ: bất biến.

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
