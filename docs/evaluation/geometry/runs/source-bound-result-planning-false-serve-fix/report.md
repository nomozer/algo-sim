# Result binding — sửa hai false serve Important (LOCAL, 2026-10-15)

**Trạng thái: `RESULT_BINDING_FALSE_SERVE_FIX_BLOCKED`.** IMPORTANT-1/2 của review `efb756aa` đã đóng: reviewer độc lập
xác nhận, có RED → GREEN. Nhưng cũng reviewer đó tìm ra CRITICAL-1/2 trong **văn phạm hỏi dùng chung** (ask thường,
đường điểm–đường phụ và Route A). Theo luật của task, nguyên nhân thuộc kiến trúc rộng hơn ⇒ dừng và báo, không mở rộng.
Không merge, không push, 0 lượt gọi Gemini, `LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid NO-GO.

## 1. Nguyên nhân gốc

- **IMPORTANT-1:** `_kiem_phu` tìm cụm "khoảng cách từ P đến XY" **trong quote của AI**, rồi ghép quote vào đề
  (`s = de[:vt0] + quote + de[vt1:]`). `_vi_tri` bỏ qua khoảng trắng, nên một quote như "bìnhphương" vẫn định vị được
  câu nguồn, nhưng regex bổ ngữ không còn thấy chữ "bình phương" nữa. Kết quả: quote quyết định ngữ nghĩa câu hỏi.
- **IMPORTANT-2:** đường hỏi phụ dùng `_duoc_hoi` (văn phạm mở) cộng denylist hai từ, trong khi mọi ask thường dùng
  văn phạm đóng `_hoi_dung_cum` (`_GIUA_HOP_LE`/`_SAU_HOP_LE`).

## 2. Sửa (`registry.py::_kiem_phu`, 2 commit sản phẩm)

- `2427289a`: tìm cụm trên **đề gốc**, chỉ nhận match nằm trong vùng quote định vị (quote chỉ còn là locator). Vai trò
  mệnh đề và câu hỏi được đọc trên `de` bằng `_hoi_dung_cum`, đúng văn phạm của ask thường. Không parser hay DSL mới.
- `8da9ae31`: review độc lập chỉ ra `2427289a` làm lọt 5 ca mà efb đã từ chối ("bình phương/nửa" ở mệnh đề trước hoặc
  trước động từ hỏi), vì văn phạm đóng chỉ đọc từ động từ hỏi cuối cùng. Commit này giữ lại kiểm tra toàn câu của efb,
  nay đọc trên `de`, có ghi chú `ponytail:` về giới hạn. Đây là denylist mở có chủ đích, không phải lời giải cho
  CRITICAL-1.
- Test: 12 cách diễn đạt đại lượng biến đổi, 6 ca quote bị thay thế, 5 ca bổ ngữ ở đầu câu, 2 ca khoanh vùng quote,
  các control dương ("Hơn nữa", quote khác khoảng trắng của câu không bổ ngữ), một ca parity "và nửa chu vi đáy"
  (fail-closed giống ask thường) và một ca "nửa mặt phẳng" ở câu tiền đề.
- 3 mutant `_duoc_hoi`/`_GAN_GIA_TRI` thành tương đương dưới văn phạm đóng. Chúng được chuyển thành test "vẫn bị từ chối
  dưới mutant", và reviewer xác nhận việc này hợp lệ. Mutant asserted-value được trỏ sang ghi chú trong ngoặc, nơi kiểm
  tra đó vẫn có tác dụng.

## 3. RED → GREEN

| bước | receipt | kết quả |
|---|---|---|
| RED trên cây `bcf0f95b` + test mới | [`red/red.xml`](red/red.xml) | 20 test, **13 đỏ**: 11 phục vụ sai `√11`, 1 từ chối sai lý do, 1 control bị từ chối sai |
| RED cho 5 ca đầu câu trên `2427289a` | [`red/red-earlier-in-sentence.xml`](red/red-earlier-in-sentence.xml) | 7 test, 5 đỏ; mutant bỏ khoanh vùng bị 2 test mới diệt |
| GREEN `8da9ae31` | 7 file liên quan | 605 passed |
| `tests/geometry` sau refreeze (`f25f2deb`) | — | 7146 passed, 1 failed (`test_holdout_readiness::test_bao_cao_da_sinh_va_KHONG_TROI`, môi trường cây chính; reviewer `efb756aa` đã ghi lỗi này là NONBLOCKING-4), 6 xfailed, 1 deselected |

Probe của reviewer trước đó: [`probes/probe_2427289a.txt`](probes/probe_2427289a.txt), [`probes/probe_8da9ae31.txt`](probes/probe_8da9ae31.txt).
Cả 10 false serve của efb đều chuyển sang REFUSED. Ca phục vụ đúng giữ nguyên.

## 4. Corpus khoá và bất biến

- 18/18 ca khoá giữ nguyên: `corpus-results.json`, `scenes.json`, `manifest.json` xuất lại ở `8da9ae31` trùng từng byte.
  Corpus và tiền đăng ký không bị sửa.
- Benchmark 30: `metrics.json` trùng từng byte (`19/9/0/2`). Two-line 45 (12/33) và 32 (11/21): các dòng trùng, chỉ khác
  trường danh tính ([`verification/`](verification/)).
- Provider A `7ea511a6…`, B `485d3834…`, khai báo hàm `5ceb0f99…`: **UNCHANGED**.

## 5. Review độc lập

[`review-2427289a.md`](review-2427289a.md): **BLOCK**, gồm CRITICAL 2 · IMPORTANT 1 · NONBLOCKING 6.
`8da9ae31` sửa phần hồi quy của CRITICAL-1 và NONBLOCKING-1 sau review, và **chưa được review độc lập lại**.

## 6. False serve còn lại (đo ở `8da9ae31`, [`probes/residual_8da9ae31.txt`](probes/residual_8da9ae31.txt))

Đường điểm–đường phụ còn 8 ca phục vụ sai `√11`. Cả 8 ca đều có từ trước (efb cũng phục vụ):

- 2 ca bổ ngữ trước động từ: "Hai lần của đại lượng sau bằng bao nhiêu: …", "Nhân đôi kết quả, tính …";
- 6 ca ghi chú trong ngoặc mở: "(kết quả nhân đôi)", "(kết quả lấy bình phương)" …

Ngoài ra, theo reviewer, cùng lớp lỗi này có trên `ask_distance_point_plane`, `ask_length` và Route A. Nhánh chân chiếu
tái sử dụng (`_kiem_result_binding`) còn đọc văn bản đã ghép quote (IMPORTANT-1 mới, cần đề sai định dạng).
Tất cả nằm ở tuyến nghiên cứu, không nối vào `/api/analyze`.

## 7. Candidate và T3

| | |
|---|---|
| product commit | `8da9ae3170f8129ca88bbc390668e4e249323ff0` |
| freeze commit | `f25f2debae4e0a2788b3415a794ffd2c606d1e24` |
| candidate | `7e993f8d1f9578cbb601ace02a972844d5516ca51da5c5e4357877c976f334d7`, 110 file, `--verify` khớp |
| trung gian | `2427289a` / `a6ba6f32…` (freeze `55fa87e7`) |
| divergence | [`inputs/candidate_divergence.json`](inputs/candidate_divergence.json), đính chính chuỗi của run `source-bound-result-planning` |
| T3 | **NOT_RUN**: task BLOCKED. Lượt sửa văn phạm dùng chung kế tiếp sẽ đổi cây sản phẩm và làm mọi T3 lúc này cũ đi. T3 `7b14fe04` cũ **không** chứng nhận cây này. |
| browser | không chạy lại: cảnh xuất trùng từng byte với receipt (`backendSceneSha256 = 177665cc…`) và `frontend/src` không đổi |

## 8. Git và bằng chứng

- Nhánh `research/source-bound-result-planning`. `main` = `origin/main` = `2a3c0787`, không đổi.
- Không push, không merge, không rebase/amend.
- `frontend/public/favicon.svg` vẫn ở dạng untracked, sha256 `c5172af1…`.
- Receipt RED/T3/review cũ không bị sửa. Run này là lớp mới.
- Worktree tạm đã gỡ hết.
