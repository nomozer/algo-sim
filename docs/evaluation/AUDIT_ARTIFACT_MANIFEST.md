# AUDIT_ARTIFACT_MANIFEST — nguồn gốc và phạm vi bằng chứng audit

**Lượt W4B-0 · READ-ONLY với production code.** Tài liệu này ghi nguồn gốc của
bảy bộ artifact audit vốn nằm **ngoài Git** cho tới commit bảo toàn dưới đây.

Vì sao có file này: bảy thư mục dưới đây chứa **767 ảnh và 40 tài liệu/dữ liệu**
là bằng chứng của năm lượt audit trước — nhưng chúng chưa từng được commit, nên
một `git clean` là mất trắng, và không ai ngoài bản làm việc này đọc được. Chúng
cũng mang **bốn baseline khác nhau**, không phải một; đọc chúng mà không biết mốc
nào thì rất dễ trích một kết luận đã hết đúng.

> **Artifact baseline giữ NGUYÊN VĂN.** Mọi cập nhật theo HEAD nằm ở tài liệu
> delta riêng (`m17/w4b0-delta/`), không sửa đè lên bản gốc — cùng luật với
> artifact live (`CLAUDE.md §4`: không sửa lại artifact của lượt cũ).

## 1. Bảng nguồn gốc

| Bộ audit | Baseline SHA | Ngày baseline | Thời điểm chạy | Ảnh | MD/JSON | Viewport | Phương pháp |
|---|---|---|---|---:|---:|---|---|
| `simulation-mechanism-audit/` | `cc449d5` | 2026-08-04 | 2026-08-04T15:07Z | 69 | 2/3 | — | Chrome thật, read-only |
| `viewmode-design-audit/` | `cc449d5` | 2026-08-04 | 2026-08-04T16:17Z | 170 | 3/3 | — | Chrome thật, read-only |
| `mechanism-fix/` | (không khai) | — | 2026-08-04T15:39Z | 27 | 0/1 | 1440×1000 · 1024×768 · 768×900 | Chrome thật, chuột thật |
| `frontier-fix/` | (không khai) | — | 2026-08-04T17:06Z | 54 | 0/1 | 1440×1000 · 1024×768 · 768×900 | Chrome thật, chuột thật |
| `ui-baseline/` | `b7ec7dc` | 2026-08-03 | 2026-08-04T10:12Z | 221 | 3/5 | 2 viewport | Chrome headless qua CDP |
| `curriculum-ui-admission/` | `722acea` | 2026-08-05 | 2026-08-05 | 226 | 7/9 | 6 chế độ hiển thị | Chrome + đối chiếu chương trình |
| `m17/pedagogical-alignment/` | `887ec10` | 2026-07-29 | 2026-07-29T09:45Z | 0 | 2/1 | — | Chỉ đọc repo, **không** Chrome |

**Tổng: 767 ảnh · 17 MD · 23 JSON · 43,5 MB.**

### Bốn baseline, không phải một

| Baseline | Bộ dùng nó | Cách HEAD (`2a78400`) |
|---|---|---|
| `887ec10` (2026-07-29) | pedagogical-alignment | xa nhất |
| `b7ec7dc` (2026-08-03) | ui-baseline | |
| `cc449d5` (2026-08-04) | simulation-mechanism-audit · viewmode-design-audit | = `origin/main`, **27 commit** sau |
| `722acea` (2026-08-05) | curriculum-ui-admission | gần nhất |

`mechanism-fix/` và `frontier-fix/` **không khai SHA** trong artifact; suy theo
`generated_at` thì chúng nằm giữa `cc449d5` và `722acea`. Ghi là **không xác
định** thay vì đoán — đoán SHA rồi trích như thật là đúng loại lỗi mà tài liệu
này sinh ra để chặn.

## 2. Checksum các tài liệu và dữ liệu chính

SHA-256, 16 ký tự đầu. Ảnh không liệt kê từng file (767 cái); số lượng và dung
lượng ở bảng trên là đủ để phát hiện mất mát.

### `simulation-mechanism-audit/`
```
65471ba70933781d  SIMULATION_QUALITY_MATRIX.md
8078c037aed3bd96  simulation_mechanism_quality_audit.md
c1c01fcfab0969b0  simulation_quality_summary.json
0e82a9cd68182d57  raw-observations.json
1b56e48ac85c0e1e  fixture-verify.json
```

### `viewmode-design-audit/`
```
127bc4ea0e386ada  DESIGN_CLARITY_MATRIX.md
36499df6c7d20716  SHARED_VISUAL_PRIMITIVES.md
2d560bdd1034a024  VIEW_MODE_DECISION_MATRIX.md
7f671d850d6a8165  viewmode_design_summary.json
b910a496760dcb51  raw-observations.json
2e4a3328f1cca48d  interaction-remeasure.json
```

### `curriculum-ui-admission/`
```
36026d33769c3e13  CURRICULUM_ADMISSION_MATRIX.md
0ed92616f967dd6a  CURRICULUM_SOURCE_LOG.md
6eca8c44d612a486  PILOT_IMPLEMENTATION_REPORT.md
f7fc586d027a858a  PILOT_SELECTION_RATIONALE.md
318382d74284cd79  SIMULATION_UI_BENCHMARK.md
4bb3ecb1f8d926d4  UI_COMPLEXITY_MATRIX.md
cbeccd7fb676bd94  VIEW_MODE_DECISION_MATRIX.md
53b1df36231ac8cb  curriculum_ui_summary.json
6eae91f5810c2248  raw-observations.json
```

### `ui-baseline/`
```
76b425bb29239164  UI_INTERACTION_BASELINE.md
9601eb87dccc18ad  ui_interaction_baseline_audit.md
cff62b9b1847e388  shell_usability_patch_report.md
67206391ba492303  captures.json
b9e062dfc324af2a  captures-after.json
65ba506a9b93ad34  dag-acceptance.json
```

### `m17/pedagogical-alignment/`
```
a1a18b6fcbffe08a  pedagogical_alignment_audit.md
a989fce283449282  family_scope_decision.md
8eed809d126b71de  pedagogical_alignment_matrix.json
```

### `mechanism-fix/` · `frontier-fix/`
```
f9639383f4356992  mechanism-fix/acceptance.json
0860cdff9c137e43  frontier-fix/acceptance.json
```

## 3. Phân loại file

| Loại | Số file | Xử lý |
|---|---:|---|
| `EVIDENCE_DOCUMENT` (`.md`) | 17 | commit |
| `STRUCTURED_OBSERVATION` (`.json`) | 23 | commit |
| `SCREENSHOT_EVIDENCE` (`.png`) | 767 | commit |
| `REPRODUCTION_SCRIPT` | 0 | — (script nằm ở `frontend/scripts/`, đã trong Git) |
| `TEMPORARY_BROWSER_DATA` | 0 | — |
| `GENERATED_CACHE` | 0 | — |
| `SENSITIVE_OR_ENVIRONMENTAL_DATA` | **0** | xem cổng quét dưới |
| `UNKNOWN` | 0 | — |

**Không có file nào bị loại khỏi bộ commit.** Toàn bộ 807 file đều thuộc ba loại
bằng chứng đầu.

### Cổng quét trước khi commit

Chạy trên cả bảy thư mục, trước `git add`:

| Mẫu tìm | Kết quả |
|---|---|
| `C:\Users` · `/home/<user>` · tên người dùng · `AppData` | **0 file** |
| `AIza…` (khoá Google) · `sk-…` (OpenAI) · `GEMINI_API_KEY=` · `"api_key": "…"` | **0 file** |

Ảnh là ảnh chụp `localhost` ở chế độ headless, không có khung trình duyệt hay dữ
liệu cá nhân.

## 4. Giới hạn của từng bộ (trích nguyên từ artifact)

- **`simulation-mechanism-audit`** — phân loại A/B/C/D theo *mức độ cơ chế nhìn
  thấy được*, không phải theo đúng/sai canonical. Không đo tác động học tập.
- **`viewmode-design-audit`** — `viewmode_design_summary.json` tự ghi:
  *"Có patch cơ chế CHƯA COMMIT (bounded_control_flow, insertion_sort, quy ước
  màu)"*. Nghĩa là ảnh của bộ này **không** phản ánh đúng `cc449d5` thuần; đây là
  giới hạn phải nêu khi trích.
- **`pedagogical-alignment`** — `mode = READ_ONLY, không chạy LLM, không chạy
  Chrome, 0 ảnh mới`. Mọi kết luận suy từ repo, không từ quan sát trình duyệt.
- **`curriculum-ui-admission`** — `live_model_calls = 0`, `committed = false`,
  `pushed = false`.
- **`mechanism-fix` · `frontier-fix`** — không có tài liệu tường thuật, chỉ
  `acceptance.json` + ảnh; `frontier-fix` ghi `mismatches: []`.

## 5. Trạng thái tại HEAD

Trạng thái từng kết luận **không** ghi ở đây. Chúng nằm ở
`m17/w4b0-delta/SIMULATION_QUALITY_MATRIX_DELTA_<sha>.md`, để bản gốc giữ nguyên
giá trị lịch sử và phần cập nhật có thể đọc riêng.

Con số đáng chú ý lấy từ `pedagogical_alignment_matrix.json` (baseline `887ec10`):

- `eval_items_total = 113`
- `eval_items_with_learning_objective = 83`
- → **30 eval item chưa khai `learning_objective`**
- `learner_impact = NOT_EVALUATED`
- `family_count = 11` · `target_count = 22`

Ba con số đầu là điểm khởi hành cho việc định vị lỗ metadata ở lượt sau; chúng
thuộc baseline `887ec10` nên phải xác minh lại tại HEAD trước khi dùng.
