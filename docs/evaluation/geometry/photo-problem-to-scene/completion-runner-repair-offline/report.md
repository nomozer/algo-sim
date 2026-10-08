# COMPLETION_RUNNER_REPAIR_OFFLINE

**2026-09-21** · nhánh `feat/photo-problem-to-scene` · START_HEAD `a17d00c` ·
commit mã `25c3f5b` · `main` giữ `085cae6` · **0 request Gemini · 0 request mạng**

```text
COMPLETION_RUNNER_REPAIR_OFFLINE = PASS        (bộ đo; xem §1 về một phát hiện SẢN PHẨM)
MODEL_FACING_REQUEST_CHANGED     = NO          6/6 thân request trùng harness độc lập của a17d00c
PRODUCT_CODE_CHANGED             = NO          0 dòng backend/app · frontend/src
CANDIDATE e7bae036… → e7bae036…               CACHE_VERSION 99 → 99
NEXT_ACTION (theo đặc tả)        = RETRY_REMAINING_PREREGISTERED_CASES_LATER
```

Wave này chỉ làm cho phép đo đáng tin. Nó **không** cho phép kết luận kiến trúc
mới đủ tin cậy, và không đổi `DEFAULT_MODE = LLM_ONLY`.

## 1. Hai điều phải đọc trước khi tiêu 6 request tiếp theo

**Phát hiện sản phẩm, offline, 0 request.** Một hợp đồng đọc **đúng** đề N04
(đáy vuông tại G *và* vuông tại H — hai dữ kiện đề nói, loại trừ nhau — cộng
`DG ⊥ (GHL)`) được adapter chấm `VALID`, compiler `SUPPORTED → COMPILED`, route
**`served`**. Hệ lặng lẽ bỏ một dữ kiện đề cho rồi dựng cảnh và trả đáp số.
`GROUND_TRUTH.N04.unsafe_if` đã đăng ký đúng tình huống này từ trước (*"chọn một
trong hai mệnh đề mâu thuẫn rồi dựng hình như thể không có mâu thuẫn"*).
Nguyên nhân gốc ở hai chỗ, đều trong mã sản phẩm mà wave này **cấm sửa**:

- `geometry_compiler/fact_graph.kiem_mau_thuan` chỉ bắt xung đột độ dài và
  "khẳng định–phủ định cùng một quan hệ", không bắt hai góc vuông trong một tam
  giác;
- vòng chọn góc vuông đáy trong `geometry_compiler/compiler.py` gặp góc vuông ở
  **đỉnh khác của cùng tam giác đáy** thì `continue` — bỏ qua, không báo.

Bộ đo đã sửa báo đúng: `UNSAFE_ACCEPTANCE`, `TARGETED_REJECTION_MATCH = NO`,
quy kết `PRODUCT_ACCEPTED_DEFECTIVE_INPUT`, **0** quan hệ bị tính là bịa (mô hình
không sai). Test `test_G8_E_N04_doc_dung_bi_he_PHUC_VU_va_bo_do_bao_UNSAFE` ghim
trạng thái này; khi sản phẩm được sửa, test ấy phải đổi sang kỳ vọng
`INVALID_CONFLICT`.

**Trần phân loại của lượt retry đã bị lịch sử khoá.** Chạy bộ tổng hợp trên kịch
bản **tốt nhất có thể** — cả 6 ca còn thiếu đều đạt, N04 bị từ chối:

| kịch bản | phân loại |
|---|---|
| 6/6 đạt, N04 từ chối | **`NOT_READY`** — 6/8 ca dương, accuracy 0,75, cụm lỗi lặp P03+P05 |
| như trên, nhưng mô hình đọc đúng N04 (và hệ phục vụ như §1) | **`UNSAFE`** |
| như dòng 1, nếu KHÔNG coi P03+P05 là cụm lỗi lặp | `MORE_EVIDENCE_NEEDED` |

Tức là lượt retry **không thể** ra `READY_FOR_CANARY_DESIGN` hay
`STRONG_PILOT_RESULT`, và kết cục có khả năng nhất khi mô hình đọc tốt lại là
`UNSAFE` — do lỗi sản phẩm ở trên, không phải do mô hình. ⚠️ Ngưỡng *"cụm lỗi lặp
= ≥ 2 ca dương cùng một mã quy kết chính"* là **định nghĩa của tôi**; đặc tả chỉ
viết *"có cụm lỗi lặp"*. Dòng thứ ba cho thấy định nghĩa ấy quyết định trần.

Nhãn next theo đặc tả vẫn là `RETRY_REMAINING_PREREGISTERED_CASES_LATER`. Việc có
chạy retry trước hay sửa sản phẩm (`STRUCTURED_RELATION_SAFETY_REPAIR`) trước là
quyết định của bạn; retry vẫn đo được độ chính xác quan hệ của 6 ca mới và hành
vi mô hình trên N02–N04.

## 2. Tám lỗ đã đóng

| lỗ | sửa | chứng minh |
|---|---|---|
| **G1** request thật | `CongQuanSat` ghi theo `case_id`: băm đúng byte thân gửi transport, model lấy từ URL, băm `responseSchema`, đường dẫn đã bỏ query. Request lệch kỳ vọng bị **chặn trước transport** (`LoiTuongDuongRequest`), không tiêu quota, lượt dừng, tổng hợp ⇒ `MEASUREMENT_INVALID`. Trước live: `dung_request_du_kien` dựng lại 6 request kỳ vọng qua **đúng** `stage_semantic_analyze`, đối chiếu `EXPECTED_REQUEST_HASHES.json` | 5 hàm test · F1 |
| **G2** trần | trần transport = độ dài hàng đợi thật (`hang_doi_con_lai` → 6), không phải hằng 12. Request thứ 7 bị chặn ở transport | 4 hàm test · F2 |
| **G3** ca âm | chấm theo `NEGATIVE_EXPLICIT_RELATION_REGISTRY.json` (đăng ký trước, dẫn **chỉ** từ đề đóng băng). Quan hệ đề nói thẳng không bị tính là bịa; quan hệ bịa vẫn bị bắt; giả định không thành GIVEN. Test viết tên **hoán vị** | 3 hàm / 6 lượt · F3 |
| **G4** tổng hợp | `aggregate_multicase_completion.py`: đọc 33 artifact lịch sử **qua băm**, mỗi ca một kết cục, tách lượt/ca/đính chính, lớp `UNSAFE`, nhãn next đúng đặc tả, tái lập trùng byte | 8 hàm test · F4 |
| **G5** quy kết | `quy_ket_that_bai` nay được **gọi** ở mọi nhánh của `chay_mot_ca`, trả mã ổn định. Bản cũ không bao giờ trả `MODEL_MALFORMED_RELATION` — chính mã P03/P05 phải mang | 4 hàm test · F5 |
| **G6** token/độ trễ | usage thiếu ⇒ `UNKNOWN`, không bao giờ 0; tổng chỉ là số khi mọi thành phần đều biết. p50/p95 chỉ lấy HTTP 200 có output hợp lệ; thời gian chờ lỗi provider đứng riêng | 6 hàm test · F6 |
| **G7** envelope | ghi **ngay** sau từng ca, nguyên tử (tệp tạm → fsync → replace) | 3 hàm test · F7 |
| **G8** từ chối đúng | `TARGETED_REJECTION_MATCH` tách khỏi `SAFE_REJECTION`, theo `NEGATIVE_TARGETED_REJECTION_REGISTRY.json` (mã riêng từng ca, chọn theo **ý nghĩa** của mã). `{}` có thể an toàn nhưng luôn `NO` | 4 hàm / 8 lượt · F8 |

**G9 — kiểm phiên bản runner.** `19d1a6d → a17d00c` chỉ đổi nhãn (mọi hàm chấm
trùng AST). Wave này **có** đổi evaluator, có chủ đích (G3, G4, G5, G6, G8), còn
chấm ca **dương** thì giữ nguyên (`so_quan_he` + `chay_tang_dung`, chỉ thêm trường
`UNBOUND_POINTS`). Thân request: 6/6 trùng harness **độc lập** của wave trước ⇒
`MODEL_FACING_REQUEST_CHANGED = NO`.

## 3. Bằng chứng

**Red-before / green-after.** Chạy bộ test cuối (45 test) trên runner ở
`a17d00c`: **43 đỏ, 2 xanh**. Hai test xanh là khoá registry — dữ liệu đăng ký
trước, không phải hành vi runner. Lý do đỏ đã soát từng dòng. Đỏ **theo hành vi**:
G1 (thiếu `REQUEST_OBSERVATIONS`), G2 (`12 == 6`), G3 (quan hệ đề nói bị đếm là
bịa), G5 (không gọi quy kết), G7 (mất envelope khi tiến trình chết), G8 (thiếu
trường targeted). Đỏ **vì thiếu năng lực**: G4, G6 — module chưa tồn tại. Sau
sửa: 45/45 xanh.

**MockTransport** — chạy `main()` **thật** của runner, chỉ thay transport và khoá
ở biên:

| kịch bản | kết quả |
|---|---|
| A · 6 × HTTP 200 | transport thấy đúng P06 P07 P08 N02 N03 N04 · 6 request · trần 6 · 0 Vision/Synthesis/repair/retry · 6/6 băm thân khớp kỳ vọng |
| B · timeout ở P06 | 1 request · dừng ngay · P07–N04 không chạy · quy kết `PROVIDER_ERROR` |
| C · P06 đạt, P07 timeout | 2 request · `envelopes/P06.json` còn · không có P07 · không tệp dở dang |
| D · `{}` cho N02–N04 | `SAFE_REJECTION` 3/3 · `TARGETED` **0/3** · `COMPLETENESS = FAIL` |
| E · đọc đúng N01–N04 (tên hoán vị) | 0 quan hệ bị tính là bịa · N01–N03 `TARGETED = YES` · N04 `UNSAFE` (§1) |

**Tiêm lỗi — 8/8 bị bắt**, hoàn nguyên trùng byte, worktree sạch sau đó. Tiêm
chạy ở một worktree riêng, tách khỏi lượt full backend. Chi tiết:
`FAULT_INJECTIONS.json`. Một điều đáng ghi: F7 (dời việc ghi envelope xuống cuối
vòng) chỉ bị **đúng một** test bắt — test tiến trình chết giữa chừng. Kịch bản C
(dừng bình thường) vẫn xanh dưới phép tiêm ấy.

**Full backend** (worktree sạch `25c3f5b`, chạy một mình): **5744 passed · 1
skipped · 0 failed** (143 s). Bộ tập trung: 472 passed. ⚠️ Hai lượt pytest chạy
**song song** trên hai worktree (full backend + green-after) đều **treo**: CPU đứng
yên hơn 30 phút. Dừng cả hai và chạy lại tuần tự thì mọi thứ xong bình thường.
Nguyên nhân chưa xác định; khả năng cao là tranh chấp tài nguyên giữa hai phiên
pytest. Chạy tuần tự.

**Parity.** Chọn ca không đổi · prompt `50a076e1…` · lược đồ `0542161e…` · model
`gemini-2.5-flash` · nhiệt độ 0.1 · diff sản phẩm `a17d00c → HEAD` rỗng · 33/33
artifact lịch sử trùng byte · candidate `e7bae036…` · `CACHE_VERSION` 99.

**Tổng hợp chỉ lịch sử**, chạy hai lần, trùng byte: `PROVIDER_INCOMPLETE` · 8
lần thử (1 void, 1 lỗi provider, 6 phản hồi hợp lệ) · 6 ca có kết cục · token đã
biết 15 817, `UNKNOWN_USAGE_COUNT = 2` ⇒ tổng `UNKNOWN` · độ trễ thành công
p50 5088,5 ms / p95 10 195,9 ms · thời gian chờ lỗi provider `[120 002,8]`.

## 4. Bộ đo của tôi sai hai lần trong wave này — cả hai đã bắt

1. **Tổng hợp tính nhầm lượt VOID thành chờ lỗi provider.** Lượt chứng minh đầu
   tiên trả `PROVIDER_ERROR_WAIT_MS = [2.9, 120002.8]`. Con số 2,9 ms là lượt void
   P02 (`Event loop is closed` — lỗi bộ đo), không phải provider. Nguyên nhân:
   `tong_hop_do_tre` dùng `_la_loi_provider` thay vì `trang_thai`. Đây đúng là
   bệnh đã đốt 2 request ở wave benchmark (sự cố bộ đo đội lốt lỗi provider), nay
   tái hiện ở tầng độ trễ. Đã viết test trên **dữ liệu lịch sử thật**, test đỏ
   trên bản chưa sửa (`[2.9, 120002.8] == [120002.8]`), rồi mới sửa. Commit mã
   được **amend** (chưa push) để giữ trần hai commit.
2. **Fixture "đọc đúng" của N03 thiếu `JK = 6`.** Bộ đối chiếu trả `TARGETED =
   NO` và nó **đúng**: đó là một bản đọc thiếu, bị từ chối vì
   `GIVEN_FACT_WITHOUT_SOURCE`, không phải vì khiếm khuyết đã đăng ký. Lỗi nằm ở
   fixture, không ở bộ đo. Mọi fixture ca âm nay khai đủ mọi độ dài đề cho.

## 5. Lựa chọn đã khai (không nằm sẵn trong đặc tả)

- **Hai mã quy kết thêm** ngoài 17 mã của đặc tả. `SERVER_POINT_BINDING_GAP` giữ
  phân biệt *"mô hình khai mà server chưa neo được điểm"*, mà các wave trước đã
  chứng minh là đắt. `PRODUCT_ACCEPTED_DEFECTIVE_INPUT` dùng cho trường hợp mô hình
  đọc đúng nhưng hệ vẫn phục vụ đầu vào hỏng (§1).
- **"Lượng thông tin tối thiểu" ở G8** đo bằng thứ **chỉ mô hình cung cấp**:
  nghĩa vụ `volume` và các quan hệ đề nói. Độ dài trong FactGraph do server đọc từ
  đề, nên nó có mặt cả khi mô hình trả `{}`; dùng nó là đo nhầm.
- **Mã từ chối đúng khiếm khuyết** chọn theo **ý nghĩa** của mã, không theo mã hệ
  hiện trả. N04 cần `INVALID_CONFLICT`; `BASE_RIGHT_ANGLE_VERTEX_MISMATCH` **không**
  tương đương.
- **Trường hợp đặc tả không nêu**: ≥ 7/8 mà accuracy ∈ [0,75; 0,90) ⇒
  `MORE_EVIDENCE_NEEDED`, phía thận trọng.
- **Thứ tự ưu tiên phân loại**: đo hỏng > không an toàn > thất bại im lặng > thiếu
  ca > ngưỡng.
- **`--live` nay bắt buộc `--tiep-tuc`**: chạy lại 12 ca từ đầu là gửi lại những
  ca đã có kết quả.
- **Runner không còn bộ phân loại riêng.** Ba test cũ khoá ngữ nghĩa mà đặc tả bác
  bỏ (`unsafe → NOT_READY`, thiếu ca → `MORE_EVIDENCE_NEEDED`) được thay bằng một
  test khoá "một thẩm quyền".

## 6. Chưa làm, có chủ đích

- 0 lượt live — đặc tả cấm, dù mọi cổng xanh.
- Không sửa sản phẩm (§1) — việc của `STRUCTURED_RELATION_SAFETY_REPAIR`.
- `CURRENT_STATE.md` / `STATUS_LEDGER.md` — đặc tả cấm; nợ ghi ngược vẫn thuộc
  một wave tài liệu riêng.
- Không trình duyệt / frontend — không có envelope live mới, không đổi frontend.

## 7. Artifact

`docs/evaluation/geometry/photo-problem-to-scene/completion-runner-repair-offline/`:
`PRECHECK` · `RUNNER_GAP_TO_TEST_MATRIX` · `REQUEST_OBSERVATION_CONTRACT` ·
`EXPECTED_REQUEST_HASHES` · `NEGATIVE_EXPLICIT_RELATION_REGISTRY` ·
`NEGATIVE_TARGETED_REJECTION_REGISTRY` · `AGGREGATOR_CONTRACT` ·
`RED_BEFORE_GREEN_AFTER` · `MOCK_TRANSPORT_PROOF` · `BEHAVIOR_PARITY` ·
`FAULT_INJECTIONS` · `OFFLINE_GATES` · `SECRET_SCAN`. Ba registry đầu vào vào
commit mã (đăng ký trước); phần còn lại vào commit báo cáo.
