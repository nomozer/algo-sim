# Shared ask-grammar safety (LOCAL, 2026-10-16)

**Trạng thái: `ASK_GRAMMAR_FINAL_REGRESSION_FIX_READY_FOR_REVIEW` (Full geometry gate: `PENDING FINAL CANDIDATE`).** Không merge, không push, 0 lượt gọi Gemini; `LLM_ONLY` và
`CACHE_VERSION = 125` giữ nguyên; Hybrid NO-GO.

- Ở mốc `9ce1298f`, review độc lập [`review-9ce1298f.md`](review-9ce1298f.md) ghi nhận BLOCK với 4 Critical (`C1`–`C4`) và 3 Important (`I1`–`I3`).
- Ở mốc `4acfc7316179e4ec7a9039dc654ea95fee8a9550`, đã triển khai Stage A (`C1`, `C4`, `I2`, `I3`) và Stage B (`C2`, `C3`).
- Ở mốc `34a04eaf7e9cbaf70d5c8741e3fb155fa7fd65e7`, đã xử lý `CR-1`, `CR-2`, `IM-1`, `IM-2` từ kiểm toán đối với `4acfc731`, nhưng làm phát sinh hồi quy `CR-A`, `CR-B` và chưa đóng `IM-A` + hai lỗi dẫn chiếu tài liệu.
- Đợt sửa hiện tại đóng triệt để `CR-A`, `CR-B`, `IM-A` và hai lỗi tài liệu đã xác nhận (§9).

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

## 5. Phân loại blocker ở `9ce1298f` (đã đóng ở `4acfc731`, `34a04eaf` và đợt hiện tại)

| phát hiện | root cause đã duyệt? | có từ trước? | trạng thái |
|---|---|---|---|
| C1 mệnh đề mục tiêu nuốt bổ ngữ | CRITICAL-1: có | không — do bản cài; G1/G7-line là **hồi quy** so với `8da9ae31` | Đóng (`4acfc731` + `CR-A`) |
| C4 ghi chú đơn vị khác đơn vị đề | CRITICAL-2: có | có | Đóng (`4acfc731` + `CR-1`/`CR-2`/`CR-B`) |
| I2/I3 false refusal mới (cụm dựng trước "và tính", vài dạng làm tròn) | CRITICAL-1/2: có | không — do bản cài | Đóng (`4acfc731` + chính sách §8–§9) |
| C2 câu sau câu hỏi đổi đại lượng | **đã duyệt Option (b) Stage B** | có | Đóng (`4acfc731` + `CR-B`) |
| C3 thiết diện mặt suy dẫn (P) | **đã duyệt Option (b) Stage B** | có | Đóng (`4acfc731` + `CR-A`/`CR-B`/`IM-A`) |

## 6. Candidate, T3, browser

| | |
|---|---|
| product commit (Stage A/B) | `4acfc7316179e4ec7a9039dc654ea95fee8a9550` (trước đó `5f1b576c62eb75293c800718dc200da45ff4934d`) |
| product commit (trước đợt sửa hiện tại) | `34a04eaf7e9cbaf70d5c8741e3fb155fa7fd65e7` |
| harness commit | `9ce1298f8f7cef090169c5ae5a64b0625a1ddbd4` |
| freeze commit (hiện hành) | `5fc1645c0fd5b98778f6f74337938d78ade89f54` — candidate `4b95dcc665f5930b74c849164122458ad070af9af24cb085bcfa9217063dee25` |
| divergence | [`inputs/candidate_divergence.json`](inputs/candidate_divergence.json) (`PENDING FINAL CANDIDATE` — chưa refreeze trước khi review độc lập đạt) |
| T3 | **NOT_RUN** — chờ review độc lập đạt rồi mới refreeze candidate và chạy T3 |
| browser | không chạy lại; cảnh xuất trùng byte (`177665cc…`), `frontend/src` không đổi |

## 7. Git

- Nhánh `research/source-bound-result-planning`. `main` = `origin/main` = `2a3c0787`.
- Không push, không merge.
- `frontend/public/favicon.svg` không bị đụng. Receipt cũ không bị sửa. Worktree tạm đã gỡ hết.

---

## 8. Đóng phát hiện kiểm toán độc lập đối với `4acfc731` (`CR-1`, `CR-2`, `IM-1`, `IM-2` & Chính sách làm tròn / góc)

### 8.1. Bốn phát hiện kiểm toán ở `4acfc731`

1. **CR-1 — Đơn vị trong câu ghi chú đứng trước hoặc sau câu hỏi (`_kiem_ghi_chu`):**
   - Kiểm tra câu ghi chú ở cả `_kiem_vung_tien_de` (trước `first_request`) và `_kiem_du_kien_cau_hoi` (từ `first_request` trở đi) đối chiếu với chiều đại lượng (`length`/`area`/`volume`/`angle`) và cơ sở đơn vị của giả thiết (`don_vi_de`).
2. **CR-2 — Phân biệt tham số và đơn vị trong `theo X` (`_SAU_HOP_LE`, `_kiem_don_vi_hoi`):**
   - Chỉ cho phép tham số `theo a` khi chiều đại lượng là `length`/`area`/`volume`, `_co_tham_so_a(calls)` xác nhận mọi lời gọi mang giá trị khai báo tham số `a`, và đề không dùng đơn vị mét tường minh (`not don_vi_de`). Mọi `theo <unit>` phải khớp chiều đại lượng và `don_vi_de == {base}`.
3. **IM-1 — Khôi phục các mệnh đề mục tiêu hợp lệ trong `_than_muc_tieu_hop_le` và `_doc_muc_tieu_cau_hoi`:**
   - Hỗ trợ `"nhau"` (`"cách đều nhau"`), `"bằng hai cách"`, ký hiệu `"ΔSAB"`, mục tiêu nối bằng dấu phẩy dưới cùng động từ mục tiêu (`"Chứng minh SA ⊥ (ABC), SB = SC rồi tính SD."`), và kiểm `_DUOI_BANG` cho độ dài trong mục tiêu chứng minh.
   - *(Lưu ý: Cách mở rộng `_THAN_MUC_TIEU_CON` ở `34a04eaf` đã vô tình cho phép các từ bội số rời như `gấp đôi`, `một nửa`, `N lần` lọt qua mệnh đề nối bằng dấu phẩy; lỗi hồi quy này được đóng triệt để ở §9.1 `CR-A` bên dưới).*
4. **Chính sách fail-closed đối với làm tròn số thập phân và biểu diễn góc theo độ/radian:**
   - Từ chối fail-closed (`QUESTION_CONTEXT_UNSUPPORTED`) mọi yêu cầu làm tròn kết quả (`_LAM_TRON` khi đề có lệnh `ask_*`) và mọi yêu cầu đổi biểu diễn góc sang độ/radian (`theo độ`, `theo radian`, `(độ)`, `(radian)`).

### 8.2. Đối chiếu với `grammar_probe.py` (không sửa file lịch sử)

Theo quy tắc bảo toàn bằng chứng, [`grammar_probe.py`](grammar_probe.py) và các file JSON lịch sử (`red-baseline-8da9ae31.json`, `green-9ce1298f.json`) không bị chỉnh sửa. Kết quả chạy [`grammar_probe.py`](grammar_probe.py) (lưu tại [`verification/suite3-grammar-probe.json`](verification/suite3-grammar-probe.json)):

| Nhánh | `CORRECT_REFUSAL` | `CORRECT_SERVED` | `WRONG_SERVED` | `FALSE_REFUSAL` (so với nhãn cũ trong `grammar_probe.py`) |
|---|---:|---:|---:|---:|
| Route B | 84 | 33 | **0** | 6 (`P5-line`, `P7-line`, `P5-plane`, `P7-plane`, `P5-length`, `P7-length`) |
| Route A | 52 | 16 | **0** | 4 (`P5-plane`, `P7-plane`, `P5-length`, `P7-length`) |

- **Đính chính về `P11` (`grammar_probe.py:89-95`):** Ba ca `P11-line`, `P11-plane`, `P11-length` trong `grammar_probe.py` có mẫu câu `"Gọi M là trung điểm SC, tính {phrase}."` (phép dựng trung điểm đứng cùng câu trước động từ hỏi). Ba ca này từng bị `FALSE_REFUSAL` ở `green-9ce1298f.json` và đã được phục hồi sang **`CORRECT_SERVED` từ Stage A (`I2` — `_doc_phep_dung_cau_hoi`)** tại `4acfc731`, **không phải** mẫu câu `"Chứng minh SA ⊥ (ABC) bằng hai cách, rồi tính {O}."` (mẫu `"bằng hai cách"` là kiểm thử positive control riêng của `IM-1` trong `test_shared_ask_grammar.py`).
- Mười ca được `grammar_probe.py` gắn nhãn `FALSE_REFUSAL` đều thuộc đúng 2 mẫu câu có yêu cầu làm tròn số thập phân:
  - `P5`: `"Tính {O} (làm tròn đến hàng phần trăm)."`
  - `P7`: `"Tính {O} (kết quả làm tròn đến hàng phần mười)."`
  Trong `grammar_probe.py` đăng ký trước, `P5` và `P7` có `expected = "SERVED"`. Theo chính sách fail-closed (§8.1 mục 4), hệ thống chủ động từ chối `P5` và `P7` với `QUESTION_CONTEXT_UNSUPPORTED`. Do đó 10 ca này là **từ chối đúng theo chính sách mới (policy-intended refusals)**, không phải lỗi văn phạm.

### 8.3. Đính chính số liệu và đường dẫn Benchmark 30 (`IM-2` Reconciliation)

Số liệu Benchmark 30 thực tế được xác minh trực tiếp từ hai file tồn tại thực trong kho:
- [`verification/benchmark-30-metrics.json`](verification/benchmark-30-metrics.json) (`docs/evaluation/geometry/runs/shared-ask-grammar-safety/verification/benchmark-30-metrics.json`)
- [`../source-bound-result-planning/verification/benchmark-30/metrics.json`](../source-bound-result-planning/verification/benchmark-30/metrics.json) (`docs/evaluation/geometry/runs/source-bound-result-planning/verification/benchmark-30/metrics.json`)
và lệnh `pytest backend/tests/geometry/test_hybrid_compiler_benchmark.py -q` ([`verification/suite4-hybrid-compiler-benchmark.txt`](verification/suite4-hybrid-compiler-benchmark.txt)):

1. **Phân bố 30 ca trong `benchmark-30-metrics.json` (`total = 30`):**
   - `correct_served`: **19** (`status == "SERVED"`, thuộc tập 21 ca có thể giải được trên compiler hiện tại)
   - `correct_refusal`: **9** (`status == "REFUSED"`, toàn bộ 9 ca ngoài phạm vi có lý do từ chối hợp lệ)
   - `wrong_served`: **0**
   - `false_refusal`: **2** (`status == "REFUSED"` trên 2 ca có thể giải nhưng chưa hỗ trợ: `B27` (`unsupported_shape: prism`), `B28` (`prism_or_cylinder_unsupported`))
   - Tổng theo `status`: **19 SERVED, 11 REFUSED**.
2. **Số lượng pytest items trong `test_hybrid_compiler_benchmark.py`:**
   - Tổng cộng **98 pytest items** = **94 passed, 4 xfailed**.

---

## 9. Đóng hồi quy kiểm toán độc lập đối với `34a04eaf` (`CR-A`, `CR-B`, `IM-A`, `IM-2`)

### 9.1. Ba phát hiện kỹ thuật và thiết kế sửa lỗi

1. **CR-A — Không cho mệnh đề mục tiêu che bổ ngữ đại lượng (`_than_muc_tieu_hop_le`, `_doc_muc_tieu_cau_hoi`):**
   - **Nguyên nhân gốc ở `34a04eaf`:** `_THAN_MUC_TIEU_CON` cho phép các từ bội số/tỉ lệ trần (`gấp đôi`, `gấp ba`, `một nửa`, `nửa`, `(?:một|...|sáu|\d+)\s+lần`) đứng tự do, trong khi `_doc_muc_tieu_cau_hoi` nối mệnh đề qua dấu phẩy mà không đòi hỏi mỗi vế phải có vị từ quan hệ hoàn chỉnh. Hệ quả là các câu như `"Chứng minh BD ⊥ SC, SC gấp đôi, tính độ dài SC."`, `"Chứng minh BD ⊥ SC, một nửa SC, tính độ dài SC."`, `"Chứng minh BD ⊥ SC, 2 lần SC, tính khoảng cách từ S đến (ABCD)."` hoặc `"Chứng minh BD ⊥ SC và gấp đôi, tính độ dài SC."` bị đọc nhầm thành mệnh đề chứng minh hợp lệ.
   - **Sửa trong `backend/app/simulation/geometry_functions/registry.py`:**
     - Loại bỏ toàn bộ các từ bội số/tỉ lệ rời (`gấp đôi`, `gấp ba`, `một nửa`, `nửa`, `lần`) khỏi `_THAN_MUC_TIEU_CON` và chỉ giữ `bằng (một|hai|ba|bốn|\d+) cách`.
     - Định nghĩa mẫu quan hệ bội số nhị nguyên đóng `_QUAN_HE_BOI_SO` giữa đúng hai toán hạng đoạn thẳng hợp lệ (`<đoạn_1> (=|bằng|là) (gấp đôi|gấp ba|một nửa|nửa|<N> lần) <đoạn_2>` hoặc `<đoạn_1> gấp (đôi|ba|<N> lần) <đoạn_2>` với mọi nhãn thuộc `dung`). Chỉ khi khớp trọn vẹn quan hệ nhị nguyên này, nó mới được rút gọn thành `<lhs> = <rhs>` trước khi kiểm tra `_THAN_MUC_TIEU_CON`.
     - Bắt buộc mỗi mệnh đề mục tiêu phải chứa ít nhất một vị từ quan hệ/tính chất hình học hợp lệ (`_VI_TU_MUC_TIEU`), không được kết thúc lửng bằng liên từ/vị từ (`và`, `hoặc`, `với`, `tại`, `của`, `bằng`, `là`, `vuông góc`, `song song`, `=`, ...), và mọi số tự nhiên trong mệnh đề mục tiêu (ngoài `bằng N cách`) phải đứng ngay sau toán tử so sánh/đẳng thức (`=`, `<`, `>`, `bằng`, `lớn hơn`, `nhỏ hơn`, `bé hơn`).
     - Trong `_doc_muc_tieu_cau_hoi`, cắt bỏ từ nối `và` đứng ngay cuối vùng mục tiêu trước động từ hỏi (`"Chứng minh BD ⊥ SC và tính SC."`) để `và` được đọc bởi `_DAN_CAU_HOI` mà không cho phép `"Chứng minh BD ⊥ SC và gấp đôi, tính SC."` lọt qua.

2. **CR-B — Đóng ngữ nghĩa câu ghi chú kết quả (`_GHI_CHU`, `_kiem_ghi_chu`):**
   - **Nguyên nhân gốc ở `34a04eaf`:** `_GHI_CHU` vẫn là biểu thức túi từ lặp (`*`) và `_kiem_ghi_chu` có nhánh `if not re.search(...): return True` cho qua mọi câu khớp `_GHI_CHU` nhưng không chứa từ `"đơn vị"`, khiến các câu ghi chú định dạng/làm tròn/biến đổi như `"Kết quả đến hàng phần trăm."`, `"Ghi đáp số ở hàng phần trăm."`, `"Viết kết quả dưới dạng phân số."`, `"Đáp số là phần mười của kết quả."`, `"Ghi kết quả theo hàng nghìn."` lọt qua.
   - **Sửa trong `backend/app/simulation/geometry_functions/registry.py`:**
     - Thay thế `_GHI_CHU` và `_kiem_ghi_chu` bằng 3 mẫu câu đóng, không có nhánh mặc định `return True`:
       1. `_GHI_CHU_TRINH_BAY`: câu hướng dẫn trình bày lời giải / vẽ hình minh hoạ (`"Trình bày lời giải chi tiết."`, `"Vẽ hình minh hoạ."`).
       2. `_GHI_CHU_THANG_DO`: câu khai báo thang đo độ dài cơ sở (`"Đơn vị (độ dài) là <mm|cm|dm|m>."`), hợp lệ khi và chỉ khi khớp `don_vi_de`.
       3. `_GHI_CHU_DON_VI_KET_QUA`: câu ghi chú đơn vị kết quả (`"Kết quả ghi/viết/để/tính ở/theo đơn vị <loại_đơn_vị|đơn_vị>."` hoặc `"Đơn vị (của) kết quả/đáp số là <loại_đơn_vị|đơn_vị>."`), hợp lệ khi và chỉ khi khớp chiều đại lượng của các lệnh `ask_*` và khớp cơ sở đơn vị `don_vi_de`.
     - Mọi câu ghi chú khác về định dạng kết quả, làm tròn (`hàng phần trăm`, `hàng phần mười`, `hàng nghìn`), dạng phân số, dạng căn thức, hoặc phần mười kết quả đều bị `_kiem_ghi_chu` trả `False` ⇒ từ chối `QUESTION_CONTEXT_UNSUPPORTED`.
     - Cập nhật kiểm thử lịch sử `backend/tests/geometry/test_premise_source_coverage.py` (chuyển `"Lưu ý: kết quả để ở dạng căn thức."` sang kiểm thử từ chối theo chính sách `test_unverified_radical_format_note_in_premise_is_refused_by_policy`).

3. **IM-A — Hợp đồng đầu ra của câu hỏi góc (`cos²` vs `số đo góc`):**
   - **Nguyên nhân gốc:** Engine hình học trả `cos²=...` cho `ask_angle_line_plane` và `ask_angle_plane_plane`. Trong khi `"Tính góc giữa ..."` quy ước nhận `cos²=...` theo hợp đồng hàm, câu hỏi `"Tính số đo (của) góc giữa ..."` đòi hỏi chính số đo góc (mà `cos²` không phải là số đo góc).
   - **Sửa trong `backend/app/simulation/geometry_functions/registry.py`:**
     - Trong `_kiem_don_vi_hoi`, khi `chieu == "angle"` và cụm được hỏi mở đầu bằng `số đo` (`re.match(r"số\s+đo\b", de[a:b], re.I)`), trả `False` ⇒ từ chối `QUESTION_CONTEXT_UNSUPPORTED` trên cả Route A và Route B.
     - Trong `_bo_cum`, không xoá cụm mở đầu bằng `số đo` để câu ghép như `"Tính số đo góc giữa SC và (ABCD) và tính độ dài SC."` không thể ẩn cụm hỏi `số đo góc` chưa được hỗ trợ.
     - Trong `_kiem_du_kien_cau_hoi`, chỉ đánh dấu `phrases` đã đọc khi `_kiem_don_vi_hoi` đạt.
     - Toàn bộ các bài toán hỏi `"Tính góc giữa ..."` trong corpus khoá 18/18 (`COMP1`, `DIH1`), holdout (`H07`, `H30`) và Benchmark 30 (`B29`) tiếp tục giữ nguyên hành vi.
     - Cập nhật kiểm thử lịch sử `backend/tests/geometry/test_hybrid_ask_operand_binding.py` (chuyển `"Tính số đo góc giữa SC và mặt đáy."` sang `test_angle_measure_so_do_goc_is_refused_by_output_contract_policy`).

### 9.2. Biên lai xác minh (`verification/` & `red/`)

| Biên lai | Lệnh thực thi | Kết quả | SHA-256 |
|---|---|---|---|
| [`red/red-review-4acfc731.txt`](red/red-review-4acfc731.txt) | `pytest backend/tests/geometry/test_shared_ask_grammar.py -q` (tại `4acfc731` trước khi sửa `registry.py`) | `158 failed, 275 passed` (`EXIT_CODE: 1`) | `40f0286f510bb5ea7b4304655955e58d8ddbe48077abc7ac8af3c6bd65b4a403` |
| [`red/red-review-34a04eaf.txt`](red/red-review-34a04eaf.txt) | `pytest backend/tests/geometry/test_shared_ask_grammar.py -q` (tại `34a04eaf` trước khi sửa `registry.py`) | `146 failed, 459 passed in 10.82s` (`EXIT_CODE: 1`) | `12f9f0f50460ac425d7cf08d9445367c90a6a1e684e7516ad81039a73ff484d0` |
| [`verification/suite1-shared-ask-grammar.txt`](verification/suite1-shared-ask-grammar.txt) | `pytest backend/tests/geometry/test_shared_ask_grammar.py -q` | `609 passed in 7.63s` (`EXIT_CODE: 0`) | `d6a918cac8ff2614f6357eb537473608b7c775a73392c93307b621734b0059aa` |
| [`verification/suite2-result-binding-planning.txt`](verification/suite2-result-binding-planning.txt) | `pytest backend/tests/geometry/test_result_binding_planning.py -q` | `72 passed in 1.37s` (`EXIT_CODE: 0`) | `f307a27421a678de10ed64c07e5ca2e81870fbbd8701701a7defa1c6de2d5a51` |
| [`verification/suite3-grammar-probe.txt`](verification/suite3-grammar-probe.txt) | `PYTHONPATH=backend python .../grammar_probe.py .../suite3-grammar-probe.json` | B: `84 CR, 33 CS, 0 WS, 6 FR*`; A: `52 CR, 16 CS, 0 WS, 4 FR*` (`EXIT_CODE: 0`) | `6832bde101470623d0b0e62757baa643b9ee234e18275a3a3bce3efe9549bafe` |
| [`verification/suite3-grammar-probe.json`](verification/suite3-grammar-probe.json) | JSON xuất từ `grammar_probe.py` | `0 WRONG_SERVED` trên cả Route A và Route B | `98c7dfd28f0ef7fea190c781736323bbdea9d3ef737fdb70610658fee3cff73e` |
| [`verification/suite4-hybrid-compiler-benchmark.txt`](verification/suite4-hybrid-compiler-benchmark.txt) | `pytest backend/tests/geometry/test_hybrid_compiler_benchmark.py -q` | `94 passed, 4 xfailed in 2.16s` (`EXIT_CODE: 0`) | `d64a584c6e6bca24177322ded321e49ae4634bfcaea1c77f95d27942998ada66` |
| [`verification/suite5-ask-context-section-suites.txt`](verification/suite5-ask-context-section-suites.txt) | `pytest` trên 8 file ask/context/section suites | `868 passed, 1 xfailed in 10.74s` (`EXIT_CODE: 0`) | `69e4e099073fbc198ea032f51ef612fec41f28da450b135810a92cbdba39095a` |
| [`verification/suite6-full-geometry-regression.txt`](verification/suite6-full-geometry-regression.txt) | `pytest backend/tests/geometry -q` | `7749 passed, 6 xfailed, 1 deselected, 10 failed` (`PENDING FINAL CANDIDATE`: 9 guard kiểm candidate verify-only + 1 guard working-tree chưa commit trước bước refreeze; **0 lỗi logic hình học**) | `dc027695a5b66f24020a52a5f04e5452c6159fc19d79efb350cb0f76d16a8892` |


