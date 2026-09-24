# PHOTO_PROBLEM_ACCEPTANCE_SCORER_CORRECTION

> Nhánh `feat/photo-problem-to-scene` · 2026-09-14 · bắt đầu từ `684420d` · **0 request mạng ·
> 0 lượt gọi provider thật.** Wave này sửa **bộ chấm** của lượt nghiệm thu ảnh đề bài. Nó chỉ
> chứng minh bộ chấm đúng trong phạm vi kiểm thử — không chứng minh Gemini đọc đúng ảnh thật
> hay mô phỏng dựng đúng từ ảnh.

```text
SCORER_CORRECTION           = PASS
PRODUCT_CODE_CHANGED        = NO   (git diff 684420d -- backend/app, frontend/src, skills, schema: rỗng)
MODEL_FACING_CHANGED        = NO
CANDIDATE_HASH              = 13e2aaaac929672e… → 13e2aaaac929672e…
CACHE_VERSION               = 95 → 95
REAL_PROVIDER_EVIDENCE      = NOT_ESTABLISHED
HUMAN_CRITICAL_FACT_REVIEW  = PENDING
REAL_PHOTO_ACCEPTANCE       = NOT_RUN
MERGE_ALLOWED               = NO
```

Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/acceptance-scorer-correction/`.

## 1. Tái hiện trước khi sửa

`backend/tests/test_photo_problem_acceptance_scorer.py` (69 test) được viết TRƯỚC bản sửa
và chạy khi runner trong cây trùng blob `684420d`: **18 xanh, 51 đỏ**. Sau bản sửa: 69 xanh.
Không test nào đổi đáp án để xanh.

| câu hỏi | ở `684420d` | bằng chứng |
|---|---|---|
| `z = 3` có lọt khi đọc ra `z = 30`? | **CÓ** — khớp chuỗi con; cũng lọt `z = 3.1`, `z = 3 + x`. `z = -3` thì không (guard có sẵn) | `FACT_MATCHING_PROOF` |
| …và một lỗ chưa khai | **CÓ** — `math_expressions` khai `z = 3` là đủ để tính ĐÚNG dù văn bản ghi `z = 30`; mà tầng B chỉ nhận văn bản | `test_S1b` |
| `A′` có đọc thành `A`? | **CÓ** — biểu thức nhãn không nhận `′` (U+2032). `A1` thì đã đúng | `test_S1c` |
| Quan hệ dùng toàn nhãn thật mà đề không nói (`SA ⊥ BD`) có lọt? | **CÓ** — suy luận "nhãn và số có trong đề ⇒ không bịa" cho qua, không một dấu hiệu | `test_S2a`, `S2b` |
| C03 có nhận mã từ chối ngoài đăng ký? | **CÓ** — `status == "rejected"` là đủ; ground truth không có chỗ đăng ký mã | `C03_REJECTION_PROOF` |
| Lỗi provider / timeout / lược đồ có bị tính là từ chối an toàn? (giả thuyết) | **KHÔNG — đã có guard**, 11/11 ca. Thiếu là phân biệt FAIL / ERROR / BLOCKED | `C03_REJECTION_PROOF.HYPOTHESIS_4_…` |
| Nghiệm thu có đạt khi chưa người duyệt? | **CÓ** — `ACCEPTANCE = PASS` ngay khi kiểm tự động xanh | `HUMAN_REVIEW_GATE_PROOF` |

## 2. Sửa

**Khớp dữ kiện theo token.** `tach_token` tách văn bản thành nhãn điểm (giữ chỉ số và dấu phẩy
trên), số, biến, từ, toán tử, ngoặc, dấu ngắt. Dữ kiện phải xuất hiện như một **biểu thức hoàn
chỉnh** — hai bên là ranh giới (từ, dấu ngắt, đầu/cuối, ngoặc mở bên trái, ngoặc đóng bên phải)
— trong **cả** bản nguyên văn (thứ CER khoá) **lẫn** bản chuẩn hoá (thứ đi xuống tầng B). Trường
cấu trúc của model không bao giờ là nguồn khớp; `named_points` chỉ còn là điều kiện THÊM cho
nhãn. Tương đương ký hiệu khai rõ trong `TUONG_DUONG_DA_KHAI`: khoảng trắng · `−` ≡ `-` · `′` ≡
`'` · `⟂` ≡ `⊥` · `‖` ≡ `//` ≡ `∥` · `≦ <=` ≡ `≤` · `≧ >=` ≡ `≥` · `!=` ≡ `≠` · `A₁` ≡ `A1` ·
`x²` ≡ `x^2` · `3,5` ≡ `3.5` · hoa/thường của TỪ. Ký hiệu ngoài bảng (√, °, …) hoặc kề ký hiệu lạ
⇒ `UNVERIFIABLE_AUTOMATICALLY`: không tính đúng, không tính sai, vào danh sách người xem. CER giữ
nguyên, đo độc lập.

**Mục thêm.** Bỏ suy luận "nhãn thật ⇒ không bịa". `phan_loai_muc_them` xét trên **ground truth**,
không trên văn bản của chính model:

| lớp | khi nào | hệ quả |
|---|---|---|
| `CONFIRMED` | có nguyên biểu thức trong ground truth | không phải ảo giác |
| `CONTRADICTED` | mang nhãn/số ground truth không có, hoặc khác đúng MỘT số hay MỘT toán tử quan hệ so với một đoạn ground truth | `HALLUCINATED_CRITICAL_FACTS`, ca FAIL |
| `UNVERIFIED` | còn lại | chờ người; `SILENT_HALLUCINATION_COUNT = UNKNOWN_PENDING_HUMAN_REVIEW` — không bao giờ báo 0 khi còn mục chờ |

Mục chờ người **không** dừng lượt và không chặn tầng B: người duyệt xem trên artifact sau lượt
chạy, đúng như luồng sản phẩm (người học xác nhận văn bản rồi mới dựng).

**C03.** Ground truth phải đăng ký trước `expected_rejection_codes`, và mọi mã phải thuộc
`ma_tu_choi_san_pham()` — đọc AST của `assess_extraction`, ra `IMAGE_NOT_READABLE ·
MISSING_PROBLEM_TEXT · UNSUPPORTED_PROBLEM`. Không đọc `REJECTION_MESSAGES`: nó có thêm
`AMBIGUOUS_DIAGRAM` và `INSUFFICIENT_GEOMETRIC_CONSTRAINTS`, hai mã có câu thông báo nhưng tầng
đọc ảnh không bao giờ phát. C03 đạt khi: phản hồi hợp lệ theo lược đồ · mã thật ∈ danh sách ·
cổng HTTP thấy 0 request analyze/synthesis của C03 (`STAGE_B_HTTP_ATTEMPTS`, đo ở cổng chứ không
lấy từ việc runner tự bỏ qua) · không có cảnh.

**Trạng thái.** Mỗi ca `status` ∈ `PASS` · `FAIL` (model trả lời và sai, kể cả JSON/lược đồ) ·
`ERROR` (HTTP 4xx/5xx, timeout, kết nối, ngoại lệ chưa phân loại) · `BLOCKED` (cổng chặn). `result`
nhị phân giữ lại. `all` dừng ở ca đầu tiên không PASS.

**Duyệt thủ công.** Tóm tắt tách `AUTOMATED_CHECKS` · `HUMAN_CRITICAL_FACT_REVIEW` (runner luôn
ghi `PENDING`) · `REAL_PHOTO_ACCEPTANCE` (`NOT_RUN` cho mọi lượt không phải provider thật);
`ACCEPTANCE` = `PENDING_HUMAN_REVIEW` hoặc `FAIL`, không bao giờ `PASS` lúc chạy. Mã thoát 0 nay
nghĩa là *kiểm tự động đạt*. Mỗi lượt ghi `HUMAN_REVIEW_PACKET.json`: dữ kiện thiếu/đọc sai ·
mục thêm bịa · mục thêm chờ người · dữ kiện không kiểm được · khác biệt bản model đọc với bản người
dùng sửa · cảnh; kèm ràng buộc `run_id` · `ground_truth_sha256` · `image_sha256` ·
`raw_extraction_sha256` · `confirmed_input_sha256` và một khuôn bản duyệt `PENDING`.
`--verify-review --run-dir <abs> --human-review <abs>` đọc lại băm từ TỆP hiện tại:

| kết quả | khi nào |
|---|---|
| `PENDING` | không có bản duyệt |
| `INVALID_REVIEW` | sai khuôn · thiếu người duyệt · thời điểm không phải ISO · quyết định lạ · thiếu ca · bản `HUMAN` cho lượt không phải provider thật |
| `STALE_REVIEW` | bất kỳ ràng buộc nào lệch tệp hiện tại — đổi ảnh, ground truth, đầu ra model, bản xác nhận, hay tệp của lượt bị sửa sau khi đóng gói |
| `SIMULATED_REVIEW` | bản giả hợp lệ — không bao giờ thành `PASS` |
| `FAIL` / `PASS` | bản `HUMAN` trên lượt `REAL_PROVIDER`; `REAL_PHOTO_ACCEPTANCE = PASS` còn cần `AUTOMATED_CHECKS = PASS` và `REAL_PROVIDER_EVIDENCE = ESTABLISHED` |

Nhánh `PASS` chỉ kiểm được bằng hàm thuần (`test_S5h`, dữ liệu trong bộ nhớ). Không artifact nào
của wave mang `PASS` hay chữ ký người.

## 3. Bằng chứng

| thứ | kết quả |
|---|---|
| test mới `test_photo_problem_acceptance_scorer.py` | trước 18/69 · sau **69/69** · 51 FIXED · 18 đã có guard · 0 hồi quy |
| test runner cũ `test_photo_problem_live_runner.py` | **56/56** |
| `FACT_MATCHING_PROOF` | 19 hàng — 13 FIXED · 6 đã có guard (`z = -3` · đối chứng `A` khớp · `A1` ×2 · `A′` khi cả hai trường đều `A′` · mục thêm mang số lạ `SA = 7`) |
| `C03_REJECTION_PROOF` | 16 hàng — 16 FIXED; khoá `counted_as_safe_rejection` đã có guard ở 11/11 ca lỗi |
| `HUMAN_REVIEW_GATE_PROOF` | 12 hàng — 12 FIXED |
| `FAULT_INJECTIONS` | 4/4 đỏ, 4/4 hoàn lại trùng từng byte (sha `f72d744e…`) |
| ngân sách (`regression/`) | `MAX_HTTP_REQUESTS = 11` · 12 lượt logic → gửi 11 · chặn 1 **trước transport** · transport giả 11 · mạng 0 · một lần thử mỗi lượt gọi (dò 1/1/1) |
| redaction (`regression/`) | 3 lỗi provider × 5 secret giả ⇒ **0 lần lộ** |
| hai test từng chập chờn, 10 lượt tuần tự mỗi test | `test_luot_1_hong_luot_2_sua_duoc_thi_TRA_VE_SPEC` **10/10** · `test_D2_sua_dung_o_thi_luot_ke_tiep_DI_TRON` **10/10** — không tái hiện |
| pytest backend | 5040 pass trước commit (1 đỏ: `test_holdout_readiness_7b`, cố ý đỏ khi cây bẩn); chạy lại trên cây sạch sau commit |
| `freeze_evaluation_candidate.py --verify` | khớp `13e2aaaa…`, 94 file |
| `code-index-sync.test.ts` | 3/3 |

## 4. Thay đổi ở test cũ — khai đủ

| test | trước | sau | vì sao |
|---|---|---|---|
| fixture `_gt` | C03 không có `expected_rejection_codes` | có `["MISSING_PROBLEM_TEXT"]` | trường bắt buộc mới; đầu vào đổi, không assertion nào dựa vào nó đổi đáp án |
| `test_01`, `test_02`, `test_07` | `ACCEPTANCE == "PASS"` | `AUTOMATED_CHECKS == "PASS"` và `ACCEPTANCE == "PENDING_HUMAN_REVIEW"` | đáp án cũ **chính là** lỗi §5 — nghiệm thu đạt khi chưa người duyệt; đáp án mới chặt hơn |

`prove_photo_live_runner.py` đổi tương ứng (đòi `AUTOMATED_CHECKS = PASS` + `ACCEPTANCE =
PENDING_HUMAN_REVIEW` ở dry-run). `live-runner-hardening/` giữ nguyên từng byte; báo cáo wave trước
được thêm một khối đính chính ở đầu, thân không đổi.

## 5. Giới hạn còn lại

- **Không phân biệt ngữ cảnh "cho" với "chứng minh".** `AB ⊥ SC` trong "Chứng minh AB ⊥ SC" vẫn
  khớp như một dữ kiện đề cho. CER và `REQUEST_ACCURACY` là hai phép chặn gián tiếp.
- **Một biểu thức giống hệt ở chỗ khác vẫn thoả.** Ground truth nên kèm tên: `(α): z = 3`.
- **Mâu thuẫn tự động chỉ bắt hai dạng** (nhãn/số lạ; khác đúng một số hoặc một toán tử quan hệ).
  Quan hệ sai kiểu khác rơi vào `UNVERIFIED` — chờ người, không bị đánh là đúng.
- **Từ tiếng Việt một chữ cái thường** được coi là biến; **từ viết hoa toàn chữ Latin** (`OK`) được
  coi là chuỗi nhãn.
- **JSON/lược đồ hỏng xếp `FAIL`**, không `ERROR` — model đã trả lời.
- **Công cụ không xác minh được ai ký bản duyệt.** Luật cưỡng chế được: runner không bao giờ tự ghi
  khác `PENDING`; bản `HUMAN` bị từ chối cho mọi lượt không phải provider thật.

## 6. Việc của người

1. Đặt `GEMINI_API_KEY` và `ALLOW_LIVE_AI=1` **ở máy cục bộ**, không gửi vào hội thoại hay commit.
2. Chụp ảnh C01, viết ground truth theo `acceptance-scorer-correction/C01_GROUND_TRUTH_TEMPLATE.json`
   **trước** khi chạy, giữ cả hai ngoài kho.
3. Chạy `run_photo_problem_live.py --case C01 --input-dir … --ground-truth … --output-dir …`.
4. Mở `HUMAN_REVIEW_PACKET.json`, điền `review_template` (`review_kind = HUMAN`), rồi
   `--verify-review --run-dir … --human-review …`.

`NEXT_ACTION = USER_CONFIGURES_KEY_LOCALLY_AND_PROVIDES_C01_WITH_GROUND_TRUTH`
