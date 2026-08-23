# OFFICIAL TASK 12 — kết quả trên SEALED `7e5df014…`

> **Đây là tầng bằng chứng 3 (OFFICIAL INDEPENDENT SEALED).** Chỉ tầng này được
> dùng làm held-out metrics của luận văn. Mọi lượt pilot trước đó
> (`pilot-results/` → `pilot-results-4/`, tập `34a10a9c…`) là **engineering
> evidence**, không phải số của luận văn.
>
> Lượt này chạy **ĐÚNG MỘT LẦN**, `2026-08-23T05:10:39Z`. Không vá, không chạy
> lại. Các case hỏng được ghi đúng như chúng hỏng.

## 0. Danh tính lượt đo

| | |
|---|---|
| Hệ được đo (candidate) | **`4e13e2b`** · tree hash `024f627b…` · 126 file |
| Bộ đo (harness) | `9d8e1a1` · cây làm việc sạch |
| `CACHE_VERSION` | 34 |
| SEALED fingerprint | `7e5df0145c50c43bba1ebc2e99c5af75761d35b8dec3e030e78d90afe0329348` |
| `N_planned` / `N_processed` | 40 / 40 |
| `evaluation_complete` | **true** — không dừng sớm, không đứt ngân sách |
| Ngân sách | logic **205/440** · HTTP **207/520** · retry **2** |

Chuỗi provenance bốn tầng (khớp tuyệt đối lúc preflight):

```
SOURCE UNIVERSE V2  4a9c3564…   189 bài, audit cả 5 SGK, 708 trang
  → SELECTION POOL  34d11adc…   89 bài đủ tư cách
  → EXTERNAL SEL.   6efe2450…   seed 23082026 do GVHD cấp, chọn tất định
  → SEALED          7e5df014…   40 case + ground truth độc lập
```

Ground truth do `custodian/sealed_ground_truth.py` tính bằng Python thuần,
**không import một dòng mã sản phẩm nào**.

## 1. Ba con số — và chúng KHÁC NHAU

| Chỉ số | Kết quả | Câu hỏi nó trả lời |
|---|---|---|
| **A** generative executability | **3/40 · 7,5 %** | Máy có tổng hợp được Semantic Program hợp lệ để interpreter tất định chạy xong không? |
| **B** internal servable | **1/40 · 2,5 %** | Cổng assurance nội bộ có cho phép phát không? |
| **Oracle độc lập** | PASS **2** · FAIL **0** · UNGRADED **9** · NO_RESULT **29** | Kết quả thực thi có đúng theo ground truth độc lập không? |

**A không phải correctness. B không phải accuracy.** B là quyết định assurance
nội bộ; cổng nội bộ không phải oracle.

Ba case executable:

| case | servable | oracle | số bước | ghi chú |
|---|---|---|---|---|
| `T10-C5-025` | **true** | **PASS** | 22 | case duy nhất đi hết đường |
| `T11CS-C6-041` | false | **PASS** | 14 | C₂ chặn — **false rejection**, xem §3 |
| `T11CS-C6-057` | false | UNGRADED | 2 | C₂ chặn; case không có `expected` |

## 2. Phân rã A − B

`A − B = 2`, và **cả hai đều KHÔNG phải `verification_gap`**:

| nguyên nhân | số case |
|---|---|
| `C2_postcondition_violated` | 2 |
| `verification_gap` (C₁a — thiếu checker) | **0** |
| `C1b` witness không hiện thực hoá | 0 |
| binding / compile | 0 |

Nghĩa là: trên tập SEALED này, khoảng cách A−B **không** đến từ việc hệ thiếu
cách kiểm chứng. Nó đến từ chương trình LLM sinh ra **tự mâu thuẫn với nghĩa vụ
nó tự khai**. Gọi khối này là `verification_gap` sẽ là báo cáo sai.

## 3. Biên assurance: không sai-chấp-nhận, nhưng có sai-từ-chối

- **`phat_nhung_oracle_noi_SAI` = 0.** Không một case nào hệ tự cho là phát được
  mà ground truth độc lập nói sai. Đây là con số đáng sợ nhất trong mọi báo cáo
  loại này, và ở đây nó bằng 0.
- **False rejection = 1: `T11CS-C6-041`.** Oracle độc lập nói **ĐÚNG**, nhưng
  cổng C₂ từ chối phát. Biên assurance **bảo thủ** theo hướng an toàn: nó thà
  không phát còn hơn phát sai.

Trên 2 case có kết quả và chấm được, tỉ lệ đúng là 2/2. **Con số này không có ý
nghĩa thống kê** ở n = 2 và không được viết như một tỉ lệ chính xác của hệ.

## 4. Phát hiện chi phối: 17/40 case chết vì MỘT lỗi kiểu dữ liệu

Phân bố thất bại toàn tập:

| mã lỗi | số case |
|---|---|
| `semantic_program_invalid` | **27** |
| `requested_operation_uncovered` | 6 |
| `gate_not_simulation_suitable` | 2 |
| `postcondition_violated` | 2 |
| `input_not_grounded` | 1 |
| `gate_out_of_scope` | 1 |

Bóc 27 case `semantic_program_invalid` theo nguyên nhân thật:

| nhóm nguyên nhân | số case |
|---|---|
| **`spec_version` là số JSON `1.0`, schema đòi chuỗi `"1.0"` — và KHÔNG có lỗi nào khác** | **17** |
| `spec_version` + primitive ngoài tập (`array`, `function_call`) | 2 |
| `spec_version` + `container` nhận biểu thức thay vì tên | 2 |
| `for_range.step` nhận biểu thức thay vì số nguyên | 2 |
| visual binding trỏ container kiểu `str` | 2 |
| `field` ngoài tập `left/right/val/data` | 1 |
| primitive ngoài tập (không kèm `spec_version`) | 1 |

**21/40 case chứa lỗi `spec_version`; 17 trong số đó KHÔNG có lỗi nào khác.**

```
spec_version
  Input should be '1.0' [type=literal_error, input_value=1.0, input_type=float]
```

LLM phát ra `"spec_version": 1.0` (số JSON). `SemanticProgramSpec` khai
`Literal["1.0"]` (chuỗi). Pydantic fail-closed, cả chương trình bị vứt **trước
khi** bất kỳ nghĩa vụ ngữ nghĩa nào được xét.

Hệ quả phải nói thẳng: **A = 3/40 KHÔNG đo được năng lực ngữ nghĩa của hệ.** Nó
đo một hệ trong đó 17/40 case bị chặn ở cổng cú pháp ngoài cùng vì một khác biệt
`1.0` với `"1.0"`. Năng lực ngữ nghĩa thật của candidate `4e13e2b` **chưa được
tập SEALED này đo tới**.

**Điều đó KHÔNG cho phép sửa rồi chạy lại.** Theo luật con dấu (`freeze_protocol.md`
§7.4), một lần vá là con dấu mất hiệu lực. Muốn đo lại phải **niêm phong tập
SEALED MỚI**. Con số ở trên đứng nguyên như kết quả chính thức của `4e13e2b`.

## 5. D1 — claim CẤU TRÚC về token

**D1 giữ được.** Sau khi IR đã sinh, interpreter chạy thêm bước **không** phát
sinh lượt LLM nào:

| case | số bước interpreter | lượt LLM |
|---|---|---|
| `T10-C5-025` | 22 | 7 |
| `T11CS-C6-041` | 14 | 7 |
| `T11CS-C6-057` | 2 | 4 |

Số bước biến thiên **11 lần** (2 → 22) trong khi lượt LLM không đi theo. Phân bố
lượt LLM toàn tập: `[2, 4, 5, 6, 7, 8]` — bị chặn trên bởi call graph, độc lập
với độ dài trace. Đây là claim **cấu trúc**, kiểm bằng call graph, không phải
claim thực nghiệm về giá.

## 6. Token telemetry (HỖ TRỢ — không phải D1)

| stage | tổng token | lượt gọi |
|---|---|---|
| `classify` | 294 695 | 47 |
| `simulate` | 289 419 | 44 |
| `semantic_program` | 181 134 | 37 |
| `analyze` | 122 569 | 40 |
| `semantic_analyze` | 61 530 | 37 |
| **tổng** | **949 347** | **205** |

Trung bình: **23 733,7 token/case** toàn stage · **6 066,6 token/case** chỉ hai
stage ngữ nghĩa.

## 7. D2 — `D2_NOT_ESTIMABLE_ON_THIS_SEALED`

`matched_N = 0`. Quy tắc giao đã khoá trước ở `freeze_protocol.md §3`: chỉ nhận
case **cả hai route đều phục vụ thành công**.

- Route ngữ nghĩa phục vụ được đúng 1 case: `T10-C5-025`.
- Route module (legacy) trên chính case đó: **`error`**.
- Giao = ∅.

Route legacy trên toàn tập: `ok` 16 · `unsupported` 16 · `error` 8. Không case
nào vừa `legacy=ok` vừa `semantic servable`.

**Không được** suy D2 từ các case không khớp. Ghi đúng: không ước lượng được
trên tập SEALED này.

## 8. Phủ chương trình & tác động người học — giữ nguyên

- `CURRICULUM_SUPPORT_PARTIAL` — 3 SGK bổ sung chỉ cho 5/189 bài eligible; corpus
  bài toán thuật toán tập trung ở TH10 CĐ5 và TH11-KHMT CĐ6.
- `LEARNER_IMPACT_NOT_EVALUATED` — lượt này không đo gì về người học.

Claim thị giác giữ đúng mức: **trace → semantic frame được dẫn xuất tất định và
kiểm bằng invariant**. Không suy rộng thành hiệu quả học tập.

## 9. Đọc kết quả này thế nào

Ba câu hỏi tách hẳn nhau, và lượt đo cho ba câu trả lời khác nhau:

1. **AI tự tổng hợp được chương trình mô phỏng cho bài mới không?** — 3/40 như
   đo được, nhưng con số bị chi phối bởi một lỗi cú pháp ngoài cùng (§4), nên nó
   là **cận dưới của cận dưới**, không phải ước lượng năng lực.
2. **Kết quả có đúng theo oracle độc lập không?** — 2/2 case ra kết quả và chấm
   được đều ĐÚNG; 0 case sai. n quá nhỏ để kết luận.
3. **Assurance nội bộ có cho phát không?** — 1/40, và nó **bảo thủ**: 0
   sai-chấp-nhận, 1 sai-từ-chối.

Ba con số lệch nhau đáng kể, và theo protocol đó là **kết quả nghiên cứu cần
phân tích**, không phải lỗi cần vá trong lượt này.

Phát hiện kỹ thuật số một cho vòng sau (**cần SEALED mới để đo lại**):
`spec_version` phải chấp nhận cả `1.0` và `"1.0"`, hoặc prompt/schema phải ép
LLM phát chuỗi. Một dòng coercion đang chặn 17/40 case trước mọi tầng ngữ nghĩa.
