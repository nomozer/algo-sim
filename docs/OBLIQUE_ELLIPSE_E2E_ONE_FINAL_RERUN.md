# OBLIQUE_ELLIPSE_E2E_ONE_FINAL_RERUN

> 2026-09-07 · `RUN_ID = oblique-ellipse-final-card-rerun-20260907T141954Z`
>
> ```
> FIRST_ATTEMPT_SERVABLE = YES   ·   EVENTUAL_SERVABLE = YES
> CURRENT_PIPELINE_E2E   = PASS  ·   EXACT_ANSWER = 16π√5
> ELLIPSE_FOUNDATION_SEQUENCE = CLOSED
> ```
>
> Một ứng viên, **không lượt sửa nào**, `served`. Và lần đầu trong cả chuỗi,
> mô hình dùng ô `radius` thay vì tự tạo một `rim_point`.

## 1. Tiền kiểm danh tính (§3)

```
HEAD = 5e1a28c   WORKING_TREE = sạch   CACHE_VERSION = 91
CANDIDATE = adbb35144a82474c… (91 file)   PRODUCT_VARIANT = C
```

| thành phần | băm |
|---|---|
| `prompts` | `55ac1ca6a6df92ce…` |
| `grammar_card` | `cc105e4f1da84d23…` |
| `synthesis_schema` | `6ccef3230c003d61…` |
| `analyze_schema` | `515001b503af5c7c…` |
| `capability` | `72edf39f6c10220d…` |
| `semantic_environment` | `a483ced9fd7546df…` |
| Card hình học | `ed9ad641065b9d02…` · 6672 B |
| Card đầy đủ | `903bc80cd262b446…` · 6110 B |
| runner | `8003dc460325c392…` |
| scorer (trước lượt chạy) | `23b76967a0c1eb7e…` |

`freeze --verify` exit 0 · `lock_cache_identity --verify` exit 0 · **135 test**
của bốn wave trước xanh, xác nhận Card chứa đủ P1–P4.

## 2. Gold preflight — PASS (§4)

```
scope PASS · plane_from_equation PASS · plane_equation_source_invariant PASS
point_mode  = served · 16π√5
scalar_mode = served · 16π√5        (đường trung thực h = measure(distance,O,O′))
point_scalar_parity PASS · direct_radius_ellipse_path VALID
postconditions PASS · trace PASS · Scene3D PASS
```

**Sáu phản ví dụ, tất cả PASS**: `2x−z+11=0` bị bất biến nguồn bác · `height=20`
thiếu nguồn giữ verdict grounding · elip vượt đáy bị bác · mặt phẳng ∥ trục giữ
mã biên · `rim_point` tự tạo thiếu nguồn bị bác · **grounded named rim point
vẫn hợp lệ** (dòng Card mới không cấm lối đó).

## 3. Tiền kiểm BỘ CHẤM — PASS (§5)

Mới ở wave này, và nó tồn tại vì một lý do đo được: lượt
`OBLIQUE_ELLIPSE_E2E_AFTER_AXIS_SCALE_REPAIR` chấm `PLANE_CONSTRUCTION_CORRECT
= FAIL` cho một chương trình dựng mặt phẳng **đúng từng hệ số**. Chạy bộ chấm
trên fixture tổng hợp **trước** provider là cách rẻ nhất để chuyện ấy không lặp.

| # | fixture | kết quả |
|---|---|---|
| ① | `construct_plane_from_equation` | `PLANE_CONSTRUCTION_CORRECT = PASS` |
| ② | hệ số tỉ lệ `(−4,0,2,−20)` | `PLANE_COEFFICIENTS_CORRECT = PASS` |
| ③ | direct-radius cylinder | `DIRECT_RADIUS_USED` ✅ · `RIM_POINT_USED` ✗ |
| ④ | ungrounded `rim_point` | `RIM_POINT_GROUNDED = False` |
| ⑤ | exact result | `16π√5` |
| ⑥ | dừng ở grounding | `servable=False` · `stage=grounding` · đáp số `None` |
| ⑦ | trace + Scene3D của gold | 5 sự kiện · có `ellipse3` |

```
SCORER_RECOGNIZES_PLANE_FROM_EQUATION = YES
SCORER_DISTINGUISHES_RADIUS_AND_RIM   = YES
SCORER_STAGE_SEMANTICS                = PASS
```

## 4. Lượt chạy (§8)

```
BO_DEM  logical=2  physical=2  candidate=2  retry=0
TOKENS  7 927 / 40 000
STAGE   served · servable=True · envelope=ok
ATTEMPT 1 ứng viên · 0 lượt sửa
```

## 5. Chấm analyze — PASS toàn bộ (§9)

| chiều | kết quả |
|---|---|
| `O_COORDINATES` · `O_PRIME_COORDINATES` | **PASS** |
| `RADIUS_4` | **PASS** |
| `AXIS_OR_HEIGHT` | **PASS** |
| `PLANE_EQUATION` | **PASS** |
| `ELLIPSE_E` · `AREA_OBLIGATION` · `CONTAINER_BINDING` | **PASS** |

```
ANALYZE_CONTRACT = PASS   (6 fact, witness `dien_tich_e`)
```

⚠️ **Biến động analyze, ghi riêng theo đúng §9.** Lượt trước cùng đề, cùng
prompt, cùng schema cho `FAIL` với **bốn ô `NOT_CAPTURED`** (mất toạ độ, mất
phương trình). Lần này `PASS` toàn bộ. Nó **không** là blocker — nó giúp — nhưng
nó là **biến số thứ hai**, xem §7.

## 6. Chấm ứng viên (§10)

| Attempt | Stage cuối | Lỗi đầu tiên | Diagnostic | Repairable | Thay đổi tiếp theo |
|---|---|---|---|---|---|
| 0 | `served` | **không có** | — | — | **không cần** |

```
PLANE_OPERATION        = construct_plane_from_equation
PLANE_COEFFICIENTS     = (2, 0, −1, 10)          PASS (so TỈ LỆ)
PLANE_PROVENANCE       = source_fact_id · mat_phang_alpha
CYLINDER_MODE          = anchor + apex_or_top + radius
DIRECT_RADIUS_USED     = True     ← lần ĐẦU trong chuỗi
RADIUS_SOURCE          = `ban_kinh_day`, một vô hướng đã grounded
RIM_POINT_USED         = False
RIM_POINT_NAMED_IN_PROBLEM / RIM_POINT_GROUNDED = NOT_CAPTURED (không có rim)
ELLIPSE_OPERATION      = intersect_plane_curved_ellipse
RESULT_TYPE_ELLIPSE3   = PASS
AREA_MEASURE           = area, of = E            đúng chủ thể
STATIC · GROUNDING · SOURCE_INVARIANTS · COVERAGE · RUNTIME = PASS
EXACT_ANSWER           = 16π√5
POSTCONDITIONS · TRACE · SCENE3D · SERVABLE = PASS
```

**Đáp số xác nhận từ HAI nguồn độc lập:**

```
final_memory : Radical(he=Fraction(16, 1), can=5, mu=1)
trace        : "Gán dien_tich_e = 16π√5."
```

⚠️ **Một lỗi bộ chấm của tôi, sửa và ghi.** Bản đầu chỉ tra chuỗi `16π√5` trong
`FINAL_MEMORY` — nơi chỉ có `repr` của `Radical` — rồi trả `KHONG DOC DUOC` cho
một đáp số **đúng**. Bộ chấm hỏi sai chỗ, không phải chương trình sai. Nay nó
đòi **cả hai** nguồn đồng ý và nói thẳng nếu chúng lệch.

**Scene3D**: 7 vật · 5 sự kiện. `mat_phang_alpha_obj` là `plane3` với vai
*"Mặt phẳng cho bằng phương trình"*; `E` là `ellipse3`; trace kết bằng
`Gán dien_tich_e = 16π√5.`

## 7. Hiệu quả dòng Card (§11)

```
HISTORICAL_DIRECT_RADIUS         = 0/2      (hai raw khoá bằng băm)
HISTORICAL_RIM_POINT             = 2/2
CURRENT_DIRECT_RADIUS_CANDIDATES = 1
CURRENT_RIM_POINT_CANDIDATES     = 0
CURRENT_UNGROUNDED_RIM_FAILURES  = 0

CARD_LINE_ASSOCIATED_WITH_DESIRED_SELECTION = YES
CAUSAL_ATTRIBUTION                          = LIMITED
```

⚠️ **`LIMITED` không phải một lời rào đón — có một biến số thứ hai đo được.**
Hợp đồng analyze của lượt này **tốt hơn hẳn** lượt trước: `PASS` toàn bộ so với
`FAIL` bốn ô, và trong bốn ô ấy có **phương trình mặt phẳng** cùng **toạ độ hai
tâm**. Một hợp đồng đầy đủ hơn tự nó đã làm bài dễ hơn.

Nên hai thứ đổi cùng lúc:

```
① dòng Card mới  ② hợp đồng analyze đầy đủ hơn
```

Không tách được đóng góp của từng cái với `n = 1`. Đó đúng lý do §2 cấm ghi
thành kết luận A/B, và `test_07` khoá chính lời thú nhận này — xoá nó khỏi
artifact là đỏ, và nó còn **kiểm lại** rằng lượt trước thật sự `FAIL` ở analyze.

## 8. Kế toán (§12)

```
ANALYZE_LOGICAL_CALLS           = 1
INITIAL_SYNTHESIS_LOGICAL_CALLS = 1
REPAIR_LOGICAL_CALLS            = 0
TOTAL_LOGICAL_APPLICATION_CALLS = 2 / 5
PHYSICAL_API_ATTEMPTS = 2   ·   TRANSPORT_RETRIES = 0
CANDIDATE_PROGRAM_ATTEMPTS = 1
INPUT 5 166 · OUTPUT 1 118 · THOUGHT 1 643 · CACHED 0
TOTAL_TOKENS = 7 927 / 40 000
```

`analyze` 2 696 · `semantic_program` 5 231. Kiểm cộng khớp (2 696 + 5 231 = 7 927).

## 9. Danh tính (§14)

Mọi thành phần thuộc lượt đo **không trôi**: `CACHE_VERSION 91` · candidate
`adbb3514…` · năm băm model-facing · `semantic_environment` · Card
(`ed9ad641…`, 6672 B — manifest ghi đúng thẻ ấy) · runner `8003dc46…`.

```
RUN_IDENTITY_STABLE = YES
```

⚠️ `scorer` đổi **sau** lượt chạy (`23b76967…` → bản có `EXACT_ANSWER` hai
nguồn và `nguon="RAW_ANALYZE"`). Đó là bộ đo, thuộc phạm vi wave, và artifact
lượt chạy **nguyên byte**.

⚠️ **Một đính chính lan sang wave trước, khai ra chứ không giấu.**
`cham_analyze` cần `nguon="RAW_ANALYZE"`; thiếu nó nó mặc định `"KHONG_CO"` và
trả `NOT_CAPTURED` cho **mọi** chiều fact — đúng hợp đồng của nó, sai với thực
tế. `SCORING.json` của `oblique-ellipse-after-axis-scale-repair` dính lỗi ấy và
đã chấm lại: nay `FAIL` với bốn ô cụ thể, **khớp đúng** báo cáo wave ấy (báo
cáo trích từ `cham` của artifact chứ không từ `SCORING.json`), nên **không kết
luận nào phải sửa**. Artifact lượt chạy của cả hai wave không đụng một byte.

## 10. Báo cuối (§16)

```
RUN_VALIDITY               = HOP_LE (gold + scorer preflight cung PASS truoc
                             provider; tran 5 logical calls cuong che o BIEN
                             THAT cua call_gemini)
GOLD_PREFLIGHT             = PASS
SCORER_PREFLIGHT           = PASS
ANALYZE_CONTRACT           = PASS
FIRST_ATTEMPT_SERVABLE     = YES
EVENTUAL_SERVABLE          = YES
CURRENT_PIPELINE_E2E       = PASS
EXACT_ANSWER               = 16π√5  (xac nhan tu HAI nguon doc lap)
POSTCONDITIONS_PASS        = PASS
TRACE_PASS                 = PASS
SCENE3D_PASS               = PASS   (7 vat, 5 su kien)
MODEL_BEHAVIOR             = FIRST_ATTEMPT_POST_CARD_SIGNAL

HISTORICAL_DIRECT_RADIUS   = 0/2
HISTORICAL_RIM_POINT       = 2/2
CURRENT_DIRECT_RADIUS_CANDIDATES = 1
CURRENT_RIM_POINT_CANDIDATES     = 0
CURRENT_UNGROUNDED_RIM_FAILURES  = 0
CARD_LINE_ASSOCIATED_WITH_DESIRED_SELECTION = YES
CARD_LINE_SUFFICIENT_ON_REGISTERED_CASE     = YES
CAUSAL_ATTRIBUTION         = LIMITED

ANALYZE_CALLS              = 1
INITIAL_SYNTHESIS_CALLS    = 1
REPAIR_CALLS               = 0
LOGICAL_APPLICATION_CALLS  = 2 / 5
PHYSICAL_API_ATTEMPTS      = 2
TRANSPORT_RETRIES          = 0
CANDIDATE_PROGRAM_ATTEMPTS = 1
TOTAL_TOKENS               = 7927
TOKEN_CEILING              = 40000

RUN_IDENTITY_STABLE        = YES
CACHE_VERSION_BEFORE/AFTER  = 91 → 91
CANDIDATE_HASH_BEFORE/AFTER = adbb3514… → adbb3514…
PRODUCT_CAPABILITY_CHANGED = NO
TEST_RESULTS = wave 10 pass · pytest 4436 pass (cay SACH @ 7771bf9), 0 do · replay 5/5 ·
               crash 6/6 nem 0 · certify PASS · cache identity exit 0 @ v91 ·
               freeze --verify exit 0 (91 file) · diff --check sach ·
               frontend KE THUA (khong consumer nao doi)
COMMITS      = 2
WORKING_TREE = sach

ELLIPSE_FOUNDATION_SEQUENCE = CLOSED
CURVED_OBLIQUE_SECTION      = foundation_only
PRODUCT_PROMOTION_ELIGIBLE  = NO
RECOMMENDED_NEXT_ACTION     = NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION
```

## 11. Chuỗi elip đóng — và đóng ở đâu

Bảy wave, mỗi wave đóng đúng một thứ:

| wave | đóng gì |
|---|---|
| `CURVED_MISSING_FAMILY_…_ELLIPSE_FOUNDATION` | kiểu `ellipse3` + phép giao, `9√2π` chính xác |
| `SCOPE_GATE_QUANTITY_OBLIGATION_CLUE_REPAIR` | cổng phạm vi định tuyến bốn nghĩa vụ đại lượng |
| `PLANE_FROM_EQUATION_REPRESENTATION` | mặt phẳng từ phương trình + bất biến nguồn |
| `CURVED_SCALAR_AXIS_SCALE_REPAIR` | parity point/scalar của hình trụ |
| `CURVED_RADIUS_SLOT_AFFORDANCE_ADJUDICATION` | Card nói ra luật chọn ô đại lượng |
| **wave này** | **đường end-to-end tới `served`** |

⚠️ **Đóng cái gì, và KHÔNG đóng cái gì.** Đóng: *"pipeline sản phẩm hiện tại đi
trọn đường trên ca elip xiên này"*. **Không** đóng:

- `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED` — một lượt không nói gì về độ ổn
  định. Lượt trước cùng đề đã hỏng; lượt này chạy được.
- `CURVED_OBLIQUE_SECTION = foundation_only`, `PRODUCT_PROMOTION_ELIGIBLE = NO`
  — nút vẫn chưa hiện cho học sinh.
- **Không phải held-out acceptance.** Ca này đã được dùng để TÌM lỗi hệ thống
  suốt sáu wave, nên `DEVELOPMENT_REGRESSION_SIGNAL` là hạng cao nhất nó mang
  được.
- **Không khái quát sang hình khác.** Nón xiên vẫn ngoài bao đóng V1.

Theo §16, Card **đã chốt** cho ca elip: việc kế tiếp thuộc **hình học mới**
(`NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION`) hoặc repair policy, không thuộc
thêm hướng dẫn Card.

⚠️ Nợ còn treo, ghi để không mất: `CURVED_RIM_POINT_REPAIR_ELIGIBILITY` —
`DIAGNOSTIC_IDENTIFIES_RADIUS_SLOT = NO` và
`REPAIR_POLICY_DISTINGUISHES_SAFE_SUBCASE = NO` vẫn đúng, và sáu tín hiệu cấu
trúc để tách lớp con đã đo sẵn ở
`docs/CURVED_RADIUS_SLOT_AFFORDANCE_ADJUDICATION.md §6`. Nó không còn chặn ca
elip, nhưng lớp lỗi ấy sẽ gặp lại ở họ hình khác.
