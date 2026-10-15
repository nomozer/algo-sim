# Shared ask-grammar safety (LOCAL, 2026-10-15)

**Trạng thái: `SHARED_ASK_GRAMMAR_SAFETY_BLOCKED`.** Không merge, không push, 0 lượt gọi Gemini; `LLM_ONLY` và
`CACHE_VERSION = 125` giữ nguyên; Hybrid NO-GO. Review độc lập `9ce1298f` cho BLOCK với 4 Critical và 3 Important.
Có hai nhóm:
- **ngoài ba root cause đã duyệt** (C2 câu sau câu hỏi; C3 họ cổng thiết diện mặt suy dẫn): theo luật của task, dừng
  để chờ quyết định phạm vi mới, không vá tiếp;
- **trong phạm vi nhưng bản cài chưa đúng** (C1, C4, I2, I3): xem §5.

T3 chưa chạy.

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

## 2. RED → GREEN

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

## 4. Review độc lập

[`review-9ce1298f.md`](review-9ce1298f.md): **BLOCK**. Phiên tích hợp đã tự tái hiện C1–C4
([`probes/`](probes/)). IMPORTANT-1 của review trước đã đóng. CRITICAL-2 đã đóng, trừ C4.

## 5. Phân loại blocker

| phát hiện | root cause đã duyệt? | có từ trước? |
|---|---|---|
| C1 mệnh đề mục tiêu nuốt bổ ngữ | CRITICAL-1: có | không — do bản cài; G1/G7-line là **hồi quy** so với `8da9ae31` |
| C4 ghi chú đơn vị khác đơn vị đề | CRITICAL-2: có | có |
| I2/I3 false refusal mới (cụm dựng trước "và tính", vài dạng làm tròn) | CRITICAL-1/2: có | không — do bản cài |
| C2 câu sau câu hỏi đổi đại lượng | **không** — ngữ nghĩa nhiều câu | có |
| C3 thiết diện mặt suy dẫn (P) | **không** — họ cổng `mat_song_song_dung_nguon`/`_mat_hai_duong_dung_nguon` | có |

So với `8da9ae31`, cây sản phẩm hiện tại:
- đóng 79 false serve đã đăng ký trước;
- mở lại 2 ca (G1, G7 trên đường điểm–đường);
- thêm vài false refusal (I2, I3).

## 6. Candidate, T3, browser

| | |
|---|---|
| product commit | `5f1b576c62eb75293c800718dc200da45ff4934d` |
| harness commit | `9ce1298f8f7cef090169c5ae5a64b0625a1ddbd4` |
| freeze commit | `5fc1645c0fd5b98778f6f74337938d78ade89f54` — candidate `4b95dcc665f5930b74c849164122458ad070af9af24cb085bcfa9217063dee25`, 110 file, `--verify` khớp |
| divergence | [`inputs/candidate_divergence.json`](inputs/candidate_divergence.json) |
| T3 | **NOT_RUN** — BLOCKED. T3 `7b14fe04` không chứng nhận cây này |
| browser | không chạy lại; cảnh xuất trùng byte (`177665cc…`), `frontend/src` không đổi |

## 7. Git

- Nhánh `research/source-bound-result-planning`. `main` = `origin/main` = `2a3c0787`.
- Không push, không merge.
- `frontend/public/favicon.svg` không bị đụng. Receipt cũ không bị sửa. Worktree tạm đã gỡ hết.
