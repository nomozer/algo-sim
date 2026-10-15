# Shared ask-grammar safety (LOCAL, 2026-10-16)

**Trạng thái: `SHARED_ASK_GRAMMAR_REVIEW_FINDINGS_CLOSED_PENDING_INDEPENDENT_REVIEW`.** Không merge, không push, 0 lượt gọi Gemini; `LLM_ONLY` và
`CACHE_VERSION = 125` giữ nguyên; Hybrid NO-GO.

- Ở mốc `9ce1298f`, review độc lập [`review-9ce1298f.md`](review-9ce1298f.md) ghi nhận BLOCK với 4 Critical (`C1`–`C4`) và 3 Important (`I1`–`I3`).
- Ở mốc `4acfc7316179e4ec7a9039dc654ea95fee8a9550`, đã triển khai Stage A (`C1`, `C4`, `I2`, `I3`) và Stage B (`C2`, `C3`).
- Đợt đóng lỗi hiện tại đóng toàn bộ phát hiện trong kiểm toán độc lập đối với `4acfc731` (`CR-1`, `CR-2`, `IM-1`, `IM-2`) và áp dụng chính sách fail-closed đối với yêu cầu làm tròn số thập phân và biểu diễn góc theo độ/radian (§8).

T3 chưa chạy lại (chờ review độc lập đạt trước khi refreeze candidate và chạy authoritative T3).

## 1. Nguyên nhân gốc và thiết kế

- **CRITICAL-1:** cổng ngữ cảnh câu hỏi (`_kiem_du_kien_cau_hoi`) chỉ đọc phần đầu câu khi phần đó chứa nhãn điểm.
  Văn phạm hỏi (`_hoi_dung_cum`) chỉ đọc từ động từ hỏi cuối cùng. Vì vậy "Nhân đôi kết quả, tính …" không ai đọc,
  trên mọi ask và cả Route A lẫn B.
  - Sửa (`5f1b576c`): trong câu có cụm được hỏi, mọi chữ phải thuộc một vùng đã đọc:
    - vùng của cụm hỏi (`_vung_hoi`, tách từ `_hoi_dung_cum`: động từ chi phối → hết đuôi đóng);
    - động từ hỏi;
    - fragment dữ kiện đã cover;
    - việc kế tiếp đã đọc;
    - mệnh đề mục tiêu.
  - Phần dư chỉ được khớp `_DAN_CAU_HOI` (dấu câu, từ nối, lời mở đầu, đánh mục), là allowlist đóng. Hai denylist
    "bình phương|nửa" bị gỡ.
- **CRITICAL-2:** ngoặc trong `_SAU_HOP_LE` chấp nhận `[^()]*` sau từ đầu tiên.
  - Sửa: `_GHI_CHU_NGOAC`/`_MUC_GHI_CHU` chỉ còn làm tròn và đơn vị. `_LAM_TRON` nay đọc trọn lời dặn làm tròn.
    "theo đơn vị" chỉ nhận một đơn vị.
- **IMPORTANT-1:** nhánh reused-foot của `_kiem_result_binding` đọc câu hỏi trên đề đã ghép quote AI.
  - Sửa: tìm cụm trên `de` trong vùng quote định vị, rồi đọc vai trò và câu hỏi trên `de`.
- **Harness (`9ce1298f`):** `report_holdout_readiness.py` dùng `git status --porcelain`. Git gộp file untracked được bảo
  vệ thành `?? frontend/public/`, nên phép loại trừ favicon không bao giờ khớp và cây chính luôn bị coi là bẩn.
  - Sửa: dùng `--untracked-files=all`.
  - RED → GREEN trong worktree cô lập: chỉ có favicon thì FAIL → PASS; có file lạ thật thì vẫn FAIL.

## 2. RED → GREEN (Giai đoạn đầu `8da9ae31` → `5f1b576c`)

| receipt | kết quả |
|---|---|
| [`red-baseline-8da9ae31.json`](red-baseline-8da9ae31.json) — harness đăng ký trước ([`grammar_probe.py`](grammar_probe.py)) | B: **47 WRONG_SERVED**, 4 FALSE_REFUSAL; A: **32 WRONG_SERVED** |
| [`green-9ce1298f.json`](green-9ce1298f.json) | B: **0 WRONG_SERVED**, 3 FALSE_REFUSAL (P11, có từ trước); A: **0 WRONG_SERVED** |
| [`red/red-8da9ae31.xml`](red/red-8da9ae31.xml) — `test_shared_ask_grammar.py` | 132 test, 79 đỏ ở `8da9ae31` |
| GREEN `5f1b576c`, 8 file liên quan | 737 passed |

Lưu ý về harness: ca Route A–điểm–đường đã bị loại khỏi harness trước khi chạy baseline, vì Route A không được tự đưa
vào điểm phụ (`test_route_a_cannot_introduce_an_auxiliary`). Đây là từ chối theo thiết kế, không phải false refusal.

## 3. Bất biến (worktree sạch `9ce1298f`)

- Corpus khoá 18/18: `scenes.json`, `corpus-results.json`, `manifest.json` trùng từng byte.
- Benchmark 30: trùng từng byte.
- Two-line 45 (12/33) và 32 (11/21): các dòng trùng. Receipt ở [`verification/`](verification/).
- Provider A `7ea511a6…`, B `485d3834…`, khai báo hàm `5ceb0f99…`: UNCHANGED.
- `tests/geometry` ở worktree sạch `9ce1298f` (theo reviewer): 7270 passed, 9 failed, 6 xfailed. Cả 9 đều do candidate
  chưa refreeze, nay đã refreeze ở `5fc1645c`. Lần chạy lại sau refreeze: xem
  [`verification/geometry-suite.txt`](verification/geometry-suite.txt).
- `test_holdout_readiness`: PASS ở worktree sạch có favicon.

## 4. Review độc lập `9ce1298f`

[`review-9ce1298f.md`](review-9ce1298f.md): **BLOCK**. Phiên tích hợp đã tự tái hiện C1–C4
([`probes/`](probes/)). IMPORTANT-1 của review trước đã đóng. CRITICAL-2 đã đóng, trừ C4.

## 5. Phân loại blocker ở `9ce1298f` (đã đóng ở `4acfc731` và đợt hiện tại)

| phát hiện | root cause đã duyệt? | có từ trước? | trạng thái |
|---|---|---|---|
| C1 mệnh đề mục tiêu nuốt bổ ngữ | CRITICAL-1: có | không — do bản cài; G1/G7-line là **hồi quy** so với `8da9ae31` | Đóng (`4acfc731` + IM-1) |
| C4 ghi chú đơn vị khác đơn vị đề | CRITICAL-2: có | có | Đóng (`4acfc731` + CR-1/CR-2) |
| I2/I3 false refusal mới (cụm dựng trước "và tính", vài dạng làm tròn) | CRITICAL-1/2: có | không — do bản cài | Đóng (`4acfc731` + chính sách §8) |
| C2 câu sau câu hỏi đổi đại lượng | **đã duyệt Option (b) Stage B** | có | Đóng (`4acfc731`) |
| C3 thiết diện mặt suy dẫn (P) | **đã duyệt Option (b) Stage B** | có | Đóng (`4acfc731`) |

## 6. Candidate, T3, browser

| | |
|---|---|
| product commit (Stage A/B) | `4acfc7316179e4ec7a9039dc654ea95fee8a9550` (trước đó `5f1b576c62eb75293c800718dc200da45ff4934d`) |
| harness commit | `9ce1298f8f7cef090169c5ae5a64b0625a1ddbd4` |
| freeze commit (trước `4acfc731`) | `5fc1645c0fd5b98778f6f74337938d78ade89f54` — candidate `4b95dcc665f5930b74c849164122458ad070af9af24cb085bcfa9217063dee25` |
| divergence | [`inputs/candidate_divergence.json`](inputs/candidate_divergence.json) (chưa refreeze trước khi review độc lập đạt) |
| T3 | **NOT_RUN** — chờ review độc lập đạt rồi mới refreeze candidate và chạy T3 |
| browser | không chạy lại; cảnh xuất trùng byte (`177665cc…`), `frontend/src` không đổi |

## 7. Git

- Nhánh `research/source-bound-result-planning`. `main` = `origin/main` = `2a3c0787`.
- Không push, không merge.
- `frontend/public/favicon.svg` không bị đụng. Receipt cũ không bị sửa. Worktree tạm đã gỡ hết.

---

## 8. Đóng phát hiện kiểm toán độc lập đối với `4acfc731` (`CR-1`, `CR-2`, `IM-1`, `IM-2` & Chính sách làm tròn / góc)

### 8.1. Bốn phát hiện kiểm toán và chính sách fail-closed

1. **CR-1 — Đơn vị trong câu ghi chú đứng trước hoặc sau câu hỏi (`_kiem_ghi_chu`):**
   - **Nguyên nhân gốc ở `4acfc731`:** `_kiem_vung_tien_de` và `_kiem_du_kien_cau_hoi` cho qua mọi câu khớp `_GHI_CHU` mà không đối chiếu đơn vị yêu cầu trong câu ghi chú với đơn vị cơ sở của giả thiết (`don_vi_de`) và chiều đại lượng (`length` / `area` / `volume` / `angle`) của các lệnh `ask_*`. Ngoài ra, câu ghi chú nằm sau `first_request` không có động từ yêu cầu bị đẩy vào `fragments` trước khi kiểm `_GHI_CHU`.
   - **Sửa trong `backend/app/simulation/geometry_functions/registry.py`:**
     - Thu hẹp `_GHI_CHU` thành mẫu cấu trúc đóng cho câu ghi chú kết quả (`Kết quả ...`, `(Kết quả ...)`) và câu khai báo thang đo độ dài toàn đề (`Đơn vị (độ dài) là <unit>`).
     - Bổ sung `_kiem_ghi_chu(note, calls, don_vi_de)` kiểm tra mọi câu ghi chú ở cả `_kiem_vung_tien_de` (trước `first_request`) và `_kiem_du_kien_cau_hoi` (từ `first_request` trở đi, đồng thời ngăn câu ghi chú hợp lệ rơi vào `fragments`).
     - Câu khai báo `"Đơn vị (độ dài) là <unit>"` chỉ hợp lệ khi `<unit>` là đơn vị độ dài cơ sở (`mm`, `cm`, `dm`, `m`) và nhất quán với `don_vi_de`.
     - Câu ghi chú đơn vị kết quả (`"Kết quả ghi ở đơn vị mm."`, `"Kết quả tính theo cm²."`) phải khớp chiều đại lượng của mọi lệnh `ask_*` và khớp cơ sở đơn vị đã khai báo trong giả thiết (`don_vi_de == {base}`); nếu yêu cầu đổi đơn vị (`cm -> mm`), lệch chiều (`cm` cho diện tích), hoặc giả thiết không có đơn vị mét mà ghi chú đòi đơn vị mét cụ thể → từ chối `QUESTION_CONTEXT_UNSUPPORTED`. Giữ nguyên các câu ghi chú chung không đổi đơn vị (`"Kết quả ghi ở đơn vị diện tích."` cho `area`).

2. **CR-2 — Phân biệt tham số và đơn vị trong `theo X` (`_SAU_HOP_LE`, `_kiem_don_vi_hoi`):**
   - **Nguyên nhân gốc ở `4acfc731`:** `_SAU_HOP_LE` chấp nhận `theo [a-zA-Z]` bất kỳ mà không kiểm tra ký hiệu đó là tham số đã khai báo trong đề hay là ký hiệu đơn vị (`m`), dẫn đến `"Tính độ dài SC theo m."` (khi giả thiết dùng `cm` hoặc chỉ dùng tham số `a`) được phục vụ sai.
   - **Sửa trong `backend/app/simulation/geometry_functions/registry.py`:**
     - Thu hẹp nhánh tham số trong `_SAU_HOP_LE` về `theo a` và kiểm chứng trong `_kiem_don_vi_hoi`: `theo a` chỉ được phép khi chiều đại lượng là `length`/`area`/`volume` **và** `_co_tham_so_a(calls)` xác nhận đề có khai báo tham số `a` trong biểu thức dữ kiện (`value_expr`/`length_expr`/`tan_expr`/`cos_expr`/`ratio_expr`) và đề không dùng đơn vị mét tường minh (`not don_vi_de`).
     - Bổ sung kiểm tra cho dạng `theo <unit>` không có chữ `đơn vị` (`theo mm`, `theo cm`, `theo dm`, `theo m`, `theo cm²`, `theo cm³`, ...): bắt buộc khớp chiều đại lượng và `don_vi_de == {base}` (phải có đơn vị mét tường minh trùng cơ sở trong giả thiết).
     - Thu hẹp `_DON_VI_MET_GIVEN_RE` чтобы chỉ trích xuất đơn vị mét gắn sau số trị giả thiết (`\d...\s*(mm|cm|dm|m)` hoặc khai báo `"Đơn vị (độ dài) là ..."`), tránh bắt nhầm tên đường thẳng hay điểm đặt tên `m` trong đề dùng tham số `a`.

3. **IM-1 — Khôi phục các mệnh đề mục tiêu hợp lệ trong `_than_muc_tieu_hop_le` và `_doc_muc_tieu_cau_hoi`:**
   - **Nguyên nhân gốc ở `4acfc731`:** `_THAN_MUC_TIEU_CON` quá hẹp, từ chối các mệnh đề mục tiêu hợp lệ có `"nhau"` (`"cách đều nhau"`), `"bằng hai cách"` (làm `P11-line`, `P11-plane`, `P11-length` trong `grammar_probe.py` bị `FALSE_REFUSAL`), `"gấp đôi"`, `"hai lần"`, `"một nửa"`, ký hiệu `"ΔSAB"`, mục tiêu nối bằng dấu phẩy dưới cùng động từ mục tiêu (`"Chứng minh SA ⊥ (ABC), SB = SC rồi tính SD."`), hoặc mục tiêu độ dài không có lượng từ đặt trước (`"Chứng minh SC = a√5 rồi tính ..."` bị `_muc_tieu_mau_thuan` chặn nhầm khi kiểm `_DUOI_BANG`).
   - **Sửa trong `backend/app/simulation/geometry_functions/registry.py`:**
     - Mở rộng có kiểm soát `_THAN_MUC_TIEU_CON` với `nhau`, `(?:một|hai|ba|bốn|\d+)\s+cách`, `(?:(?:một|hai|ba|bốn|năm|sáu|\d+)\s+)?lần`, `gấp\s+(?:đôi|ba)`, `một\s+nửa|nửa`, và chuẩn hoá `Δ` thành khoảng trắng trong `_than_muc_tieu_hop_le`.
     - Cho phép mệnh đề mục tiêu nối tiếp sau dấu phẩy khi đầu mệnh đề là chủ ngữ hình học/nhãn điểm và phần thân hợp lệ theo `_than_muc_tieu_hop_le`, trong khi vẫn dừng trước mọi bổ ngữ thay đổi đại lượng (`"Chứng minh SA ⊥ (ABC), nhân đôi kết quả rồi tính SC."` → `REFUSED`).
     - Trong `_muc_tieu_mau_thuan`, kiểm tra thêm `_DUOI_BANG.match(de[m.end():end])` cho mục tiêu độ dài cạnh để `"Chứng minh SC = a√2 rồi tính ..."` không bị coi là mâu thuẫn giả thiết.
     - Sửa ranh giới từ `(?!\w)` trong `_GAN_GIA_TRI` (`(?:(?:bằng|là|khác)(?!\w)|[=≠])`) để chuỗi `" rồi làm tròn kết quả"` không bị khớp nhầm `"rồi "` + `"là"` + `"m"`.

4. **Chính sách fail-closed đối với làm tròn số thập phân và biểu diễn góc theo độ/radian (§6 nhiệm vụ):**
   - Vì kernel hiện trả biểu thức chính xác (`√17`, `a√3/2`, ...) cho độ dài/khoảng cách/diện tích/thể tích và trả `cos²=...` / `sin²=...` / `tan²=...` cho góc, mọi yêu cầu:
     - làm tròn kết quả (`_LAM_TRON` trong đuôi câu hỏi, trong ngoặc, trong việc kế tiếp `"rồi làm tròn kết quả"`, hoặc trong câu ghi chú `"Kết quả làm tròn đến ..."` khi đề có lệnh `ask_*`),
     - đổi biểu diễn góc sang độ hoặc radian (`theo độ`, `theo radian`, `(độ)`, `(radian)`, `(đơn vị: độ)`, `"Kết quả ghi ở đơn vị độ."`)
     đều bị từ chối fail-closed với `QUESTION_CONTEXT_UNSUPPORTED`.
   - Các câu hỏi góc không kèm yêu cầu độ/radian (`"Tính góc giữa ..."` / `"Tính số đo góc giữa ..."`) và bài chỉ yêu cầu dựng hình (không có `ask_*`) vẫn hoạt động bình thường.
   - 4 file test lịch sử từng dùng câu mẫu kèm hậu tố làm tròn hoặc `(đơn vị: độ)` để test cơ chế câu ghép đã được cập nhật kèm chú thích ghi nhận thay đổi chính sách:
     - `backend/tests/geometry/test_hybrid_ask_operand_binding.py`
     - `backend/tests/geometry/test_source_gate_clause_role.py`
     - `backend/tests/geometry/test_premise_source_coverage.py`
     - `backend/tests/geometry/test_question_followup_context.py`

### 8.2. Đối chiếu với `grammar_probe.py` (không sửa file lịch sử)

Theo quy tắc bảo toàn bằng chứng, [`grammar_probe.py`](grammar_probe.py) và các file JSON lịch sử (`red-baseline-8da9ae31.json`, `green-9ce1298f.json`) không bị chỉnh sửa. Kết quả chạy [`grammar_probe.py`](grammar_probe.py) sau khi đóng lỗi (lưu tại [`verification/suite3-grammar-probe.json`](verification/suite3-grammar-probe.json)):

| Nhánh | `CORRECT_REFUSAL` | `CORRECT_SERVED` | `WRONG_SERVED` | `FALSE_REFUSAL` (so với nhãn cũ trong `grammar_probe.py`) |
|---|---:|---:|---:|---:|
| Route B | 84 | 33 | **0** | 6 (`P5-line`, `P7-line`, `P5-plane`, `P7-plane`, `P5-length`, `P7-length`) |
| Route A | 52 | 16 | **0** | 4 (`P5-plane`, `P7-plane`, `P5-length`, `P7-length`) |

- Ba ca `P11-line`, `P11-plane`, `P11-length` (`"Chứng minh SA ⊥ (ABC) bằng hai cách, rồi tính {O}."`) từng bị `FALSE_REFUSAL` ở `green-9ce1298f.json` nay đã **PASS (`CORRECT_SERVED`)** nhờ sửa `IM-1`.
- Mười ca được `grammar_probe.py` gắn nhãn `FALSE_REFUSAL` đều thuộc đúng 2 mẫu câu có yêu cầu làm tròn số thập phân:
  - `P5`: `"Tính {O} (làm tròn đến hàng phần trăm)."`
  - `P7`: `"Tính {O} (kết quả làm tròn đến hàng phần mười)."`
  Trong `grammar_probe.py` đăng ký trước, `P5` và `P7` có `expected = "SERVED"`. Theo chính sách fail-closed mới (§8.1 mục 4), hệ thống chủ động từ chối `P5` và `P7` với `QUESTION_CONTEXT_UNSUPPORTED`. Do đó 10 ca này là **từ chối đúng theo chính sách mới (policy-intended refusals)**, không phải lỗi văn phạm.

### 8.3. Đính chính số liệu báo cáo (`IM-2` Reconciliation)

Báo cáo miệng của phiên `4acfc731` trước đây đã ghi nhầm `"Benchmark 30 bài toán chuẩn: 27 SERVED, 3 REFUSED"`. Số liệu thực tế được xác minh trực tiếp từ [`docs/evaluation/geometry/benchmark-30-metrics.json`](../../benchmark-30-metrics.json) và `pytest backend/tests/geometry/test_hybrid_compiler_benchmark.py -q` ([`verification/suite4-hybrid-compiler-benchmark.txt`](verification/suite4-hybrid-compiler-benchmark.txt)) như sau:

1. **Phân bố 30 ca trong `benchmark-30-metrics.json` (`total = 30`):**
   - `correct_served`: **19** (`status == "SERVED"`, thuộc tập 21 ca có thể giải được trên compiler hiện tại)
   - `correct_refusal`: **9** (`status == "REFUSED"`, toàn bộ 9 ca ngoài phạm vi có lý do từ chối hợp lệ)
   - `wrong_served`: **0**
   - `false_refusal`: **2** (`status == "REFUSED"` trên 2 ca có thể giải nhưng chưa hỗ trợ: `B27` (`unsupported_shape: prism`), `B28` (`prism_or_cylinder_unsupported`))
   - Tổng theo `status`: **19 SERVED, 11 REFUSED** (không phải `27 SERVED, 3 REFUSED`).
2. **Số lượng pytest items trong `test_hybrid_compiler_benchmark.py`:**
   - Tổng cộng **98 pytest items** = **94 passed, 4 xfailed**:
     - `test_moi_de_benchmark_khop_ky_vong[B01..B30]`: 28 passed + 2 strict xfail (`B27`, `B28`) = 30 items
     - `test_khong_co_wrong_served_tren_9_de_ngoai_pham_vi[B20..B26, B29, B30]`: 9 passed
     - `test_21_de_trong_pham_vi_khong_sinh_wrong_served[B01..B19, B27, B28]`: 21 passed
     - `test_9_de_ngoai_pham_vi_tu_choi_co_ly_do_hop_le[...]`: 9 passed
     - `test_19_de_served_co_scene_hop_le[...]`: 19 passed
     - `test_2_de_false_refusal_da_biet_la_xfail_nghiem_ngat[B27, B28]`: 2 strict xfail
     - 8 bài test tổng hợp / bất biến cổng (`test_tong_hop_30_de_khop_nguong_benchmark`, `test_artifact_metrics_khop_ket_qua_chay_thuc_te`, ...): 8 passed.

### 8.4. Biên lai xác minh (`verification/` & `red/`)

| Biên lai | Lệnh thực thi | Kết quả | SHA-256 |
|---|---|---|---|
| [`red/red-review-4acfc731.txt`](red/red-review-4acfc731.txt) | `pytest backend/tests/geometry/test_shared_ask_grammar.py -q` (tại `4acfc731` trước khi sửa `registry.py`) | `158 failed, 275 passed` (`EXIT_CODE: 1`) | `40f0286f510bb5ea7b4304655955e58d8ddbe48077abc7ac8af3c6bd65b4a403` |
| [`verification/suite1-shared-ask-grammar.txt`](verification/suite1-shared-ask-grammar.txt) | `pytest backend/tests/geometry/test_shared_ask_grammar.py -q` | `433 passed in 4.05s` (`EXIT_CODE: 0`) | `3782bb8a199c118a775de35803262b23b2c3c20ce794fc194527ad96b5d903fd` |
| [`verification/suite2-result-binding-planning.txt`](verification/suite2-result-binding-planning.txt) | `pytest backend/tests/geometry/test_result_binding_planning.py -q` | `72 passed in 1.57s` (`EXIT_CODE: 0`) | `46faa5adbeacca045ed8575e100f9835993db26799a121f58ea8ce34448cf04e` |
| [`verification/suite3-grammar-probe.txt`](verification/suite3-grammar-probe.txt) | `PYTHONPATH=backend python .../grammar_probe.py .../suite3-grammar-probe.json` | B: `84 CR, 33 CS, 0 WS, 6 FR*`; A: `52 CR, 16 CS, 0 WS, 4 FR*` (`EXIT_CODE: 0`) | `93cbe85d8cd6a47dee5dd8777e09bd0f45724e2f4db51d9b344d105d16f6ae71` |
| [`verification/suite3-grammar-probe.json`](verification/suite3-grammar-probe.json) | JSON xuất từ `grammar_probe.py` | `0 WRONG_SERVED` trên cả Route A và Route B | `98c7dfd28f0ef7fea190c781736323bbdea9d3ef737fdb70610658fee3cff73e` |
| [`verification/suite4-hybrid-compiler-benchmark.txt`](verification/suite4-hybrid-compiler-benchmark.txt) | `pytest backend/tests/geometry/test_hybrid_compiler_benchmark.py -q` | `94 passed, 4 xfailed in 2.30s` (`EXIT_CODE: 0`) | `3ee7176ba8e71d2d8946ce24ed72014ccaed8f0dcb46ea0260debbb04bdab2ca` |
| [`verification/suite5-ask-context-section-suites.txt`](verification/suite5-ask-context-section-suites.txt) | `pytest` trên 7 file ask/context/section suites | `804 passed, 1 xfailed in 8.28s` (`EXIT_CODE: 0`) | `d3841ebb19c573e9e71dcf090094ce33b6dcfa945af0741d80b9c24983b8e4f8` |
| [`verification/suite6-full-geometry-regression.txt`](verification/suite6-full-geometry-regression.txt) | `pytest backend/tests/geometry -q` | `7573 passed, 6 xfailed, 10 failed` (cả 10 failed đều là guard kiểm candidate verify-only / working-tree chưa commit trước bước refreeze; **0 lỗi logic hình học**) | `cbfc1dc77b535cb4f483080bcf873e0c641d895ce651034611a64b1f09a9fac5` |

