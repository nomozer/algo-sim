# OBLIQUE_ELLIPSE_E2E_AFTER_AXIS_SCALE_REPAIR

> 2026-09-07 · `RUN_ID = oblique-ellipse-after-axis-scale-repair-20260907T130935Z`
>
> ```
> GOLD_PREFLIGHT   = PASS (mọi ô §4, gồm cả 5 phản ví dụ)
> FIRST_ATTEMPT_SERVABLE = NO   ·   EVENTUAL_SERVABLE = NO
> BLOCKER = CYLINDER_RADIUS_OR_RIM
> CURVED_RIM_POINT_AFFORDANCE = REPLICATED
> ```
>
> Ứng viên duy nhất đúng **9/10 chiều** — kể cả `construct_plane_from_equation`
> với hệ số đúng từng con số, ngay lượt đầu. Nó hỏng đúng **một** chỗ: thêm một
> `rim_point` bịa để mã hoá bán kính, trong khi trục đã đủ hai điểm có tên.

## 1. Tiền kiểm danh tính (§3)

```
HEAD = a730984   WORKING_TREE = sạch   CACHE_VERSION = 90
CANDIDATE = 27f5c076b7c86aa1… (91 file)   PRODUCT_VARIANT = C
CURVED_OBLIQUE_SECTION = foundation_only
```

| thành phần | băm |
|---|---|
| `prompts` | `55ac1ca6a6df92ce…` |
| `grammar_card` | `2cc552807345fc65…` |
| `synthesis_schema` | `6ccef3230c003d61…` |
| `analyze_schema` | `515001b503af5c7c…` |
| `capability` | `72edf39f6c10220d…` |
| `semantic_environment` | `4d2a555abe0b183b…` |
| Card C (nội dung thẻ) | `22ab1224f986affa…` · 6386 B |
| runner | `690bcdd20c524747…` |
| scorer (trước lượt chạy) | `6f7d025134ee74e6…` |

`freeze --verify` exit 0 · `lock_cache_identity --verify` exit 0.

## 2. Tiền kiểm tất định — PASS, 0 lượt gọi (§4)

```
POINT_MODE   = served · 16π√5
SCALAR_MODE  = served · 16π√5      ← đường TRUNG THỰC (h = measure(distance,O,O′))
POINT_SCALAR_PARITY             = PASS
PLANE_EQUATION_SOURCE_INVARIANT = PASS
DIRECT_RADIUS_ELLIPSE_PATH      = VALID
TRACE = PASS · SCENE3D = PASS · SCALAR_MODE_HEIGHT_DEPENDS = PASS
```

Năm phản ví dụ giữ đúng: `2x−z+11=0` bị bất biến nguồn bác (đáp số **vẫn**
`16π√5`) · `height=20` khai thẳng thiếu nguồn giữ verdict grounding · elip vượt
đáy bị bác · mặt phẳng ∥ trục giữ mã biên · rim point tự tạo bị grounding bác.

⚠️ Ô `DIRECT_RADIUS_ELLIPSE_PATH = VALID` là **điều kiện để §10 đọc được**.
Lượt trước phải dừng vì chính ô này `FAIL`; nay nó đứng vững, nên lựa chọn của
mô hình phân loại được.

## 3. Lượt chạy (§7)

```
BO_DEM  logical=2  physical=2  candidate=2  retry=0
TOKENS  8 740 / 40 000
STAGE   semantic_program · servable=False · envelope=unsupported
ATTEMPT 1 ứng viên · 0 lượt sửa
```

## 4. Chấm analyze (§8)

| chiều | kết quả | ghi chú |
|---|---|---|
| `O = (0,0,0)` | **NOT_CAPTURED** | fact `tam_day_duoi` mang value `["O"]` — chỉ TÊN, không toạ độ |
| `O′ = (0,0,20)` | **NOT_CAPTURED** | value `["O'"]` |
| `RADIUS = 4` | **PASS** | value `["4"]` |
| `AXIS_OR_HEIGHT` | **NOT_CAPTURED** | không fact nào mang `20` như một độ dài |
| `PLANE = 2x−z+10=0` | **NOT_CAPTURED** | value `["(α)"]` — **mất phương trình** |
| `ELLIPSE = E` | **PASS** | |
| `OBLIGATION = area(E)` | **PASS** | `witness = dien_tich_e` |
| `CONTAINER_BINDING` | **PASS** | |

```
ANALYZE_CONTRACT = FAIL (7 fact, nhưng bốn ô nội dung NOT_CAPTURED)
```

⚠️ **Không phải nguyên nhân hỏng, nhưng phải ghi.** Lượt trước analyze giữ
`["O(0,0,0)"]` và `["(α): 2x - z + 10 = 0"]`; lượt này chỉ giữ nhãn. Cùng đề,
cùng prompt, cùng schema — nên đây là **biến động giữa hai lượt**, không phải
một thay đổi của hệ.

Nó **không** chặn gì: mô hình đọc thẳng đề nên vẫn viết đúng hệ số, và bất biến
`plane_equation` do **server** phát từ `problem_text` chứ không từ fact. Đó
chính là lý do bất biến ấy được thiết kế đọc câu văn của đề. `n = 1` mỗi bên ⇒
**`OBSERVATION`**, không đủ để nói analyze bất ổn.

## 5. Chấm ứng viên (§9)

| Attempt | Stage cuối | Lỗi đầu tiên | Diagnostic | Thay đổi ở attempt sau |
|---|---|---|---|---|
| 0 | `grounding` | `UNANCHORED_DERIVED_ASSUMPTION: P_rim` | *"`model_assumption` chỉ nói về CÁCH ĐẶT một đối tượng đề đã nêu; một điểm suy ra phải được DỰNG…"* | **không có** — `repairable = false` |

```
PLANE_OPERATION        = construct_plane_from_equation   ✅ ngay lượt ĐẦU
PLANE_COEFFICIENTS     = (2, 0, −1, 10)                  ✅ PASS (so TỈ LỆ)
PLANE_PROVENANCE       = source_fact_id: mat_phang_alpha ✅
CYLINDER_MODE          = anchor + apex_or_top (+ rim_point THỪA)
AXIS_TWO_POINTS        = True    ← trục ĐÃ ĐỦ bằng hai điểm có tên
DIRECT_RADIUS_USED     = False
RIM_POINT_USED         = True
RIM_POINT_GROUNDED     = False   ← chỉ `model_assumption`
HEIGHT_SOURCE          = không dùng
ELLIPSE_OPERATION      = intersect_plane_curved_ellipse  ✅
RESULT_TYPE_ELLIPSE3   = PASS
AREA_MEASURE           = area, of = E                    ✅ đúng chủ thể
STATIC                 = PASS
GROUNDING              = FAIL                            ← chỗ DUY NHẤT hỏng
SOURCE_INVARIANTS · COVERAGE · RUNTIME · EXACT_ANSWER
POSTCONDITIONS · TRACE · SCENE3D · SERVABLE = NOT_REACHED
```

**9 trên 10 chiều quan sát được đều PASS.** Hỏng đúng một chỗ.

### ⚠️ Đính chính bộ chấm — khai trước khi dùng số

Artifact lượt chạy ghi `PLANE_CONSTRUCTION_CORRECT = **FAIL**`. Đó là **lỗi của
bộ đo, không phải của mô hình**: bộ chấm chỉ biết `construct_plane` qua ba
điểm, nên nó chấm FAIL cho một chương trình dựng mặt phẳng **đúng từng hệ số**.
Bộ đo **tụt lại sau hệ đúng một wave** — `PLANE_FROM_EQUATION_REPRESENTATION`
thêm phép ấy mà bộ chấm không được cập nhật theo.

Đúng lớp lỗi *"bộ đo không nằm trên đường chạy thật"* kho này đã trả giá ba
lần. Bộ chấm đã sửa (nhận cả hai lối, so hệ số theo **tỉ lệ chính xác** chứ
không so chữ) và artifact được chấm lại **0 lượt gọi**; **lượt chạy giữ nguyên
từng byte**, kết quả đúng nằm ở `SCORING.json` kèm `sha256` của artifact nguồn.
`test_09` khoá chính mối nối ấy: cùng `raw_sha256`, hai bản chấm, hai kết quả.

## 6. Rim-point affordance (§10)

```
DIRECT_RADIUS_CANDIDATES        = 0
RIM_POINT_CANDIDATES            = 1
UNGROUNDED_RIM_POINT_CANDIDATES = 1
REPAIRS_FROM_RIM_TO_RADIUS      = 0   (không có lượt sửa nào)
CURVED_RIM_POINT_AFFORDANCE     = REPLICATED
```

Một lần mới, **cùng hình dạng** với attempt 1 lịch sử (`P_rim`, `grounding`,
`UNANCHORED_DERIVED_ASSUMPTION`) ⇒ `REPLICATED` theo đúng luật §10.

⚠️ **Hình dạng lần này sắc hơn lần trước, và đó là điểm đáng đọc.** Mô hình
khai `anchor: O` **và** `apex_or_top: O_prime` — cả hai là điểm CÓ TÊN trong
đề, và **trục đã hoàn toàn xác định**. Nó thêm `rim_point` **chỉ để mã hoá bán
kính 4**, và nói thẳng điều ấy trong lời khai của mình:

> *"Chọn một điểm trên vành đáy dưới để xác định bán kính, tại (4,0,0) vì bán
> kính đáy bằng 4."*

Tức nó **dùng một ĐIỂM để chở một ĐỘ DÀI**, trong khi ô `radius` — nhận tên một
vô hướng — tồn tại sẵn và thẻ có in ra. Đây là affordance của **cách sinh
chương trình**, không phải kernel gap: tiền kiểm §4 đã chứng minh đường
`radius` hợp lệ, và §2 wave trước đã chứng minh đường `radius + height` cũng
hợp lệ.

## 7. Vì sao KHÔNG có lượt sửa nào

`UNANCHORED_DERIVED_ASSUMPTION` nằm trong `KHONG_DUOC_SUA` của
`pipeline.py` — một **chính sách có chủ đích**, không phải lỗi:

> *"Lỗi trung thực năng lực không phải một sai sót mô hình sửa được: nó nói mô
> hình đã tự giải rồi giấu kết luận vào toạ độ. Gửi đi sửa là trả tiền cho một
> lượt giấu khéo hơn."*

Nên `REPAIR_CALLS = 0` dù ngân sách cho 3, và runner dừng đúng luật.

⚠️ **Một quan sát về PHẠM VI của chính sách ấy, ghi lại chứ không sửa.** Lập
luận trên viết cho ca *"giấu ĐÁP SỐ vào toạ độ"*. Ở đây `P_rim = (4,0,0)` không
giấu đáp số — nó mã hoá một **dữ kiện đề CÓ NÊU** (`bán kính đáy bằng 4`), và
mô hình khai đúng như vậy. Hai ca cùng mã lỗi nhưng khác bệnh:

```
giấu đáp số vào toạ độ   → sửa là trả tiền cho một lượt giấu khéo hơn  ✅ chặn
mã hoá một dữ kiện bằng   → một lượt sửa có thể đổi sang ô `radius`
sai LOẠI Ô                   đúng loại
```

Phân loại **`OBSERVATION`**, `n = 1`. Chưa đủ để nới một cổng đang gác đúng, và
nới nó là việc của một wave có bằng chứng riêng — **không** phải blocker của
lượt này, vì blocker phải là lỗi ĐẦU TIÊN trên đường chạy.

## 8. Kế toán lượt gọi và token (§11)

```
ANALYZE_LOGICAL_CALLS            = 1
INITIAL_SYNTHESIS_LOGICAL_CALLS  = 1
REPAIR_LOGICAL_CALLS             = 0
TOTAL_LOGICAL_APPLICATION_CALLS  = 2 / 5
PHYSICAL_API_ATTEMPTS            = 2
TRANSPORT_RETRIES                = 0
CANDIDATE_PROGRAM_ATTEMPTS       = 1
INPUT_TOKENS   = 5 085      OUTPUT_TOKENS  = 1 428
THOUGHT_TOKENS = 2 227      CACHED_CONTENT = 0
TOTAL_TOKENS   = 8 740 / 40 000
```

`analyze` 3 289 · `semantic_program` 5 451. Tổng kiểm cộng khớp.

## 9. Danh tính sau lượt chạy (§13)

Mọi trường **phải ổn định** đều khớp trước/sau: `CACHE_VERSION 90` ·
`candidate 27f5c076…` · `grammar_card 2cc55280…` · `analyze_schema 515001b5…` ·
`synthesis_schema 6ccef323…` · `prompts 55ac1ca6…` · `capability 72edf39f…` ·
`semantic_environment 4d2a555a…` · Card C `22ab1224…` · runner `690bcdd2…`.

```
RUN_IDENTITY_STABLE = YES
```

⚠️ **Đúng một băm đổi, và nó CỐ Ý**: `scorer` `6f7d0251…` → `23b76967…`. Sửa
**sau** lượt chạy, thuộc phạm vi §14 (bộ đo), và artifact lượt chạy bất biến —
xem §5. Mã sản phẩm và model-facing contract **không đổi một dòng** trong phép
đo.

⚠️ Runner **không** đổi: manifest băm bằng `read_text` (LF) còn phép đo tay
dùng `read_bytes` (CRLF trên Windows) — `690bcdd2…` và `8003dc46…` là **hai quy
ước băm của cùng một file**, không phải hai phiên bản.

## 10. Báo cuối (§15)

```
RUN_VALIDITY               = HOP_LE (tien kiem PASS truoc provider; tran 5
                             logical calls cuong che o BIEN THAT cua call_gemini)
GOLD_PREFLIGHT             = PASS
POINT_SCALAR_PARITY        = PASS
ANALYZE_CONTRACT           = FAIL (4 o NOT_CAPTURED; KHONG phai nguyen nhan hong)
FIRST_ATTEMPT_SERVABLE     = NO
EVENTUAL_SERVABLE          = NO
CURRENT_PIPELINE_E2E       = FAIL
EXACT_ANSWER               = NOT_REACHED (mong doi 16√5π)
POSTCONDITIONS_PASS        = NOT_REACHED
TRACE_PASS                 = NOT_REACHED
SCENE3D_PASS               = NOT_REACHED
MODEL_BEHAVIOR             = DEVELOPMENT_RERUN_SIGNAL
STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED

DIRECT_RADIUS_CANDIDATES        = 0
RIM_POINT_CANDIDATES            = 1
UNGROUNDED_RIM_POINT_CANDIDATES = 1
CURVED_RIM_POINT_AFFORDANCE     = REPLICATED

ANALYZE_CALLS              = 1
INITIAL_SYNTHESIS_CALLS    = 1
REPAIR_CALLS               = 0   (chinh sach KHONG_DUOC_SUA, khong phai het ngan sach)
LOGICAL_APPLICATION_CALLS  = 2 / 5
PHYSICAL_API_ATTEMPTS      = 2
TRANSPORT_RETRIES          = 0
CANDIDATE_PROGRAM_ATTEMPTS = 1
TOTAL_TOKENS               = 8740
TOKEN_CEILING              = 40000

RUN_IDENTITY_STABLE        = YES (moi truong PHAI on dinh; scorer doi CO Y sau
                             luot chay, artifact bat bien)
CACHE_VERSION_BEFORE/AFTER = 90 → 90
CANDIDATE_HASH_BEFORE/AFTER = 27f5c076… → 27f5c076…
PRODUCT_CAPABILITY_CHANGED = NO
TEST_RESULTS = wave 12 pass · pytest 4400 pass, 0 do · replay 5/5 ·
               crash 6/6 nem 0 · certify PASS · cache identity exit 0 @ v90 ·
               freeze --verify exit 0 (91 file) · diff --check sach ·
               frontend KE THUA (khong dung mot dong nao)
COMMITS      = 2
WORKING_TREE = sach
RECOMMENDED_NEXT_ACTION = CURVED_RADIUS_SLOT_AFFORDANCE
```

⚠️ **`ELLIPSE_FOUNDATION_SEQUENCE` KHÔNG đóng.**
`CARD_C_CURVED_ELLIPSE_PATH_CONFIRMED` giữ **`NOT_MEASURED`** — điều kiện là
*eventual served*, và nó chưa đạt.

## 11. Blocker và giới hạn

**`BLOCKER = CYLINDER_RADIUS_OR_RIM`** — lỗi ĐẦU TIÊN trên đường chạy, tái hiện
từ raw candidate: mô hình dùng một ĐIỂM bịa để chở một ĐỘ DÀI mà đề có nêu,
trong khi ô `radius` tồn tại và trục đã đủ hai điểm có tên.

- **Không phải kernel gap.** Tiền kiểm §4 chứng minh cả `radius` lẫn
  `radius + height` đều đi trọn đường tới `served` với `16π√5`.
- **Không phải `PLANE_FROM_EQUATION`.** Mô hình chọn đúng phép, đúng hệ số,
  ngay lượt đầu — hai wave trước đã trả xong món nợ ấy.
- **Không phải `MEASUREMENT_TOOLING`.** Lỗ bộ chấm có thật, nhưng đã sửa và
  chấm lại trong wave này; nó không còn là việc phải làm.

**Giới hạn bằng chứng, nói thẳng:**

- `n = 1` lượt, `n = 1` ứng viên. Đây là **ca regression phát triển** đã từng
  dùng để TÌM lỗi hệ thống — kết quả nói về đường end-to-end trên candidate
  hiện tại, **không** phải held-out acceptance, và chưa nói gì về ổn định hay
  khái quát.
- `CURVED_RIM_POINT_AFFORDANCE = REPLICATED` là **hai lần**, không phải một
  khảo sát. `REPEATED_IN_RUN` chưa đạt (chỉ có một attempt).
- Analyze yếu đi so với lượt trước là **`OBSERVATION`**, `n = 1` mỗi bên.
- Phạm vi chính sách `KHONG_DUOC_SUA` là **`OBSERVATION`**, `n = 1`.

**Việc kế tiếp: `CURVED_RADIUS_SLOT_AFFORDANCE`** — hỏi đúng một câu: *mô hình
có đọc thấy rằng bán kính khai bằng ô `radius` chứ không bằng một điểm vành
không*. Hai giả thuyết model-facing **cần phân biệt** và raw artifact đã chứng
minh cả hai đều đứng được, nên đây là ca §15 cho phép mở A/B:

1. **Thẻ chưa nói rõ ĐỦ** — `rim_point` và `radius` đứng cạnh nhau, không dòng
   nào nói *"đề cho bán kính bằng SỐ thì dùng `radius`"*.
2. **Mô hình mặc định nghĩ bằng ĐIỂM** — nó dựng hình bằng điểm ở mọi chỗ khác,
   nên với tay tìm một điểm ngay cả khi ô vô hướng có sẵn.

⚠️ Trước khi mở A/B, làm phép rẻ hơn trước — đúng lệ `CURVED_SECTION_RADIUS_
PATH_ADJUDICATION`: đọc thẻ hiện hành và hỏi *"một người đọc thẻ này có suy ra
được luật ấy không"*. Nếu suy ra được thì giả thuyết ① đã bị bác mà không tốn
lượt nào.
