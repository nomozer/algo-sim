# CURVED_V3_LIVE_ACCEPTANCE

```text
EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED
MEASUREMENT_CLASS      = INTERNAL_ONE_SHOT_ACCEPTANCE
```

> 2026-09-05. Lượt đo held-out V3 **đã chạy**. `DRAW_COUNT = 1` ·
> `LOGICAL_APPLICATION_CALLS_USED = 26` · `RUN_VALIDITY = VALID`.
>
> ⚠️ **Giới hạn phải đọc trước mọi con số dưới đây.** Phiên chạy lượt đo này
> **cũng là phiên đã sửa bộ đo** (`c41e1ab` — `run_curved_acceptance.py` +
> `certify_acceptance_runner.py`). Điều kiện độc lập evaluator được **người vận
> hành miễn trừ tường minh**, không phải đạt được. Vì vậy con số ở đây là
> **nghiệm thu nội bộ một lượt**, không phải phép đo độc lập; nó mất một bậc
> giá trị so với `INDEPENDENT_CURVED_V3_LIVE_ACCEPTANCE`. Khai điều này ở đầu
> báo cáo là điều kiện để con số còn dùng được.

## 1. Kết quả một dòng

**Không family nào đạt.** 9/9 ca dương đều hỏng; 0/9 servable; 0/9 đáp số đúng.
Bốn ca âm đều fail-closed, nhưng chỉ **1/4** chạm đúng ranh giới cong.

```text
GENERAL_CURVED_SYNTHESIS_ACCEPTANCE  = FAIL
PRODUCT_PROMOTION_ELIGIBLE_BALL      = NO
PRODUCT_PROMOTION_ELIGIBLE_CYLINDER  = NO
PRODUCT_PROMOTION_ELIGIBLE_CONE      = NO
PRODUCT_CAPABILITY_CHANGED           = NO   (ball · cylinder · cone giữ foundation_only)
```

Và nút thắt **không** nằm ở chỗ đã dự đoán. Wave trước chuẩn bị cho khoảng
trống **derived-scalar** (đường kính → bán kính). Lượt đo này lộ ra một khoảng
trống khác, sâu hơn và ở tầng trước đó: **CONSTRUCTION-GROUNDING**.

## 2. Tiền kiểm (Bước 1)

| | đo được | |
|---|---|---|
| HEAD · cây | `2dd95e0` · **CLEAN** | ✅ |
| `git diff --check` | exit **0** | ✅ |
| candidate | `a696200e8f8c668c…` · **89 file** · verify exit 0 | ✅ |
| pool (tính lại) | `36c2153ecefd2dbf…` · 26 bài / 13 ô / mỗi ô 2 | ✅ |
| `seed` · `da_rut` trước rút | `null` · `null` | ✅ |
| `CACHE_VERSION` · `ARTIFACT_SCHEMA` | **78** · **1.2** | ✅ |
| runner | `6570b57bd6ac1fe4…` | ✅ |
| certifier | `070189b54af2b2ae…` | ✅ |
| scorer | `4f7cae906500e0b6…` | ✅ |
| threshold policy | `460e0ce57a304872…` · v**1.1.0** · `decided_before_live_run=true` | ✅ |
| attribution rubric | `d44f2b7c19b4904f…` · v1.0.0 | ✅ |
| policy loader | `b51e936f809bd314…` | ✅ |
| pytest cổng (6 file) | **194 passed**, exit 0 | ✅ |
| `GEMINI_API_KEY` | **PRESENT** (giá trị không in) | ✅ |
| out-dir | `curved-acceptance-v3` — mới, rỗng | ✅ |

```
RUNNER_CERTIFICATION            PASS
V3_RUNNER_INTEGRATION           PASS   (phạm vi: hàm `mo_luot_do_v3`)
V3_LIVE_ENTRYPOINT_INTEGRATION  PASS   (phạm vi: `main_async` — đường chạy THẬT)
READY_FOR_V3_LIVE               YES
PRE_DRAW_GUARD                  PASS
```

## 3. Draw (Bước 2)

```
EXTERNAL_SEED  5324284654432805119
DRAW_COUNT     1
rut_luc        2026-09-05T01:58:07+00:00
CASE_SET_HASH  eb1c402a71517553815270b3ee0198685d7797efca813d8db760e6087dff4674
```

13 ca · một ca mỗi ô · 9 dương (**ball 3 · cylinder 3 · cone 3**) · 4 âm.
`case_set_hash` tính lại khớp con dấu; `pool_hash` và candidate không đổi.

| ô | id | hình | loại | | ô | id | hình | loại |
|---|---|---|---|---|---|---|---|---|
| C1 | `c1a` | ball | dương | | C7 | `c7a` | cone | dương |
| C2 | `c2b` | ball | dương | | C8 | `c8b` | cone | dương |
| C3 | `c3b` | ball | dương | | C9 | `c9b` | cone | dương |
| C4 | `c4b` | cylinder | dương | | N1 | `n1a` | cylinder | âm |
| C5 | `c5b` | cylinder | dương | | N2 | `n2b` | cone | âm |
| C6 | `c6b` | cylinder | dương | | N3 | `n3a` | ball | âm |
| | | | | | N4 | `n4b` | ball | âm |

## 4. Manifest trước lượt gọi đầu (Bước 3)

`manifest.json` ghi lúc **01:58:45Z**, trước lượt gọi provider đầu tiên; đã đọc
lại từ đĩa và đối chiếu. Nó chở đủ: `run_id` · `case_set_hash` (khớp con dấu) ·
bốn băm bộ đo · `artifact_schema_version 1.2` · model identity + tham số giải mã
có kiểu · `repair_limit 3` · `application_call_budget 78` ·
`transport_retry_policy.max_attempts 4`.

```
MANIFEST_WRITTEN_BEFORE_FIRST_CALL = YES
```

## 5. Hạch toán lượt gọi

| | |
|---|---|
| `LOGICAL_APPLICATION_CALL_BUDGET` | **78** |
| `LOGICAL_APPLICATION_CALLS_USED` | **26** (`semantic_analyze` 13 + `semantic_program` 13) |
| `PHYSICAL_API_ATTEMPT_BUDGET` | **312** |
| `PHYSICAL_API_ATTEMPTS_USED` | **26** (suy ra: `TRANSPORT_RETRIES_USED = 0`) |
| `TRANSPORT_RETRY_LIMIT` | 4 / lượt logic |
| `dung_som` | `null` — không chạm trần nào |
| input / output / thought tokens | **60 643** / **16 607** / **49 235** |
| `TOTAL_TOKENS` | **126 485** |

⚠️ **8B không chạy: `REPAIR_ELIGIBLE_FAILURES = 0`.** `LOP_SUA_DUOC` chỉ gồm
`schema · ir_static · grounding` — lỗi ở tầng **sau biên dịch** mang
`lop_loi="runtime"`, và `grounding_khong_sua` nằm trong `KHONG_DUOC_SUA`. Chín
ca dương hỏng nhưng không ca nào repair-eligible, nên chỉ 26/78 lượt được dùng.

**Hệ quả về mẫu số, phải nói rõ:** `EVENTUAL_SERVABLE` ở lượt này **bằng**
`FIRST_ATTEMPT_SERVABLE` **theo cấu trúc**, không phải theo đo đạc. Lượt này đo
được năng lực **one-shot**; nó **chưa đo** năng lực tự sửa.

## 6. Chỉ số theo tầng

| tầng | dương (9 ca) |
|---|---|
| analyze → `RequestContract` | **9/9** |
| synthesis → schema hợp lệ | **8/9** |
| runtime executable | **1/9** |
| postconditions pass | **0/9** |
| exact answer match | **0/9** |
| Scene3D có đại lượng | **0/9** |
| `FIRST_ATTEMPT_SERVABLE` | **0/9** |
| `EVENTUAL_SERVABLE` | **0/9** |

Đọc bảng này theo chiều dọc: **analyze không phải nút thắt** — 13/13 ca dựng
được hợp đồng đúng, dữ kiện và nghĩa vụ đều khớp đề. Sụp đổ xảy ra ở
**runtime/grounding**: 8 chương trình hợp lệ về lược đồ, chỉ 1 chạy được.

### Theo family

| | eventual servable | ids |
|---|---|---|
| ball | **0/3** | `c1a` `c2b` `c3b` |
| cylinder | **0/3** | `c4b` `c5b` `c6b` |
| cone | **0/3** | `c7a` `c8b` `c9b` |

### Theo feature

| feature | ca | kết quả |
|---|---|---|
| center + radius (cầu, bán kính cho thẳng) | `c1a` | **FAIL** — không neo được tâm |
| volume | `c1a` `c4b` | 0/2 |
| area | `c1a` `c2b` `c5b` `c6b` `c8b` | 0/5 |
| lateral_area | `c4b` `c7a` | 0/2 |
| radius (thiết diện tròn) | `c2b` `c5b` `c9b` | 0/3 |
| derived radius (đường kính → bán kính) | **không ca nào rút trúng** | `NOT_MEASURED` |

⚠️ Đúng cái wave trước chuẩn bị để đo — **derived radius** — **không có ca nào
trong tập rút**. Khoảng trống ấy vẫn `NOT_MEASURED`.

### Ca âm

| id | fail_closed | chạm ranh giới | lý do |
|---|---|---|---|
| `n1a` | ✅ | ❌ | từ chối ở `runtime` (grounding), chưa tới ranh giới elip |
| `n2b` | ✅ | ❌ | `grounding_khong_sua` |
| `n3a` | ✅ | **✅** | `CURVED_PLANE_DOES_NOT_CUT` — chạm đúng ranh giới cong |
| `n4b` | ✅ | ❌ | từ chối ở `runtime` (grounding) |

```
NEGATIVE_HONEST_REFUSAL = 4/4   (đạt ngưỡng)
TARGET_BOUNDARY_PASS    = 1/4   (ngưỡng 4/4 — KHÔNG đạt)
```

Ba trong bốn ca âm chết ở **cùng cổng grounding** đã giết các ca dương — tức
chúng fail-closed **vì lý do sai**. Đây chính là điều `cham_ranh_gioi` được
dựng để tách, và nó tách đúng: 4/4 fail-closed **không** chứng minh hệ biết nói
"không" về mặt cong.

## 7. Bảng quy trách nhiệm

Rubric `d44f2b7c…` v1.0.0, ghim trước kết quả. Artifact:
`docs/evaluation/geometry/curved-acceptance-v3/attribution.json`
(`280a3fe1290305b5…`).

| id | verdict | bằng chứng |
|---|---|---|
| `c1a` | **ATTRIBUTION_UNRESOLVED** | `valid_path = NO` chứng minh ở mức chữ ký (§8) nhưng rubric không adjudicate được hình dạng này |
| `c2b` | MODEL_GROUNDING_FAILURE | đề đặt tên tâm `K`; mô hình khai thẳng toạ độ `H` thay vì `project_onto` |
| `c3b` | MODEL_GROUNDING_FAILURE | đề đặt tên O,M,N,P — có điểm neo được; tâm ngoại tiếp phải dựng |
| `c4b` | **ATTRIBUTION_UNRESOLVED** | `valid_path = NO` chứng minh ở mức lược đồ + 5 đường bị chặn (§8) |
| `c5b` | **SYSTEM_COVERAGE_FAILURE** | cổng phủ; `contract.py` khai thẳng: `radius` không suy ra được cho `circle3` sinh từ phép giao |
| `c6b` | MODEL_GROUNDING_FAILURE | đề đặt tên E,E′ |
| `c7a` | MODEL_COMPOSITION_FAILURE | ca DUY NHẤT executable; `dai_luong` rỗng, `dap_so_khop=False` |
| `c8b` | MODEL_GROUNDING_FAILURE | nghi cùng gốc `c1a`/`c4b` nhưng **chưa đo riêng** ⇒ không nâng thành lỗi hệ |
| `c9b` | **SYSTEM_COVERAGE_FAILURE** | cùng cổng phủ như `c5b` |
| `n1a`–`n4b` | HONEST_UNSUPPORTED_REFUSAL | ×4 |

```
SYSTEM_EXPRESSIVENESS_GAP_COUNT = 0
ATTRIBUTION_UNRESOLVED_COUNT    = 2
MODEL_FAILURE_COUNT             = 5
SYSTEM_FAILURE_COUNT            = 2   (đều SYSTEM_COVERAGE_FAILURE)
```

**Vì sao `SYSTEM_EXPRESSIVENESS_GAP = 0` dù đã chứng minh được `valid_path = NO`
cho hai ca.** Rubric `valid_path_no` đòi **đủ sáu** điều kiện và nói thẳng
*"Thiếu một điều ⇒ không được kết luận NO"*. Điều ① là
`can_bien_doi = true` — ca đòi **biến đổi** một đại lượng. `c1a` và `c4b`
**không** đòi biến đổi gì: bán kính cho thẳng. Khoảng trống của chúng là
**CONSTRUCTION-GROUNDING**, không phải **DERIVED-SCALAR**.

Rubric được ghim trước kết quả và chỉ phủ hình dạng thứ hai. Nới nó ra sau khi
đã thấy kết quả là đúng thứ việc mà "khoá trước" tồn tại để chặn. Nên hai ca ấy
ghi `ATTRIBUTION_UNRESOLVED` — và khoảng trống được khai bằng bằng chứng ở §8,
để wave sau adjudicate bằng một rubric mở rộng, ghim trước lượt đo kế tiếp.

## 8. Chứng minh reachability — khoảng trống CONSTRUCTION-GROUNDING

Đây là phát hiện chính của lượt đo. Mọi phép đo dưới đây **tất định, 0 lượt gọi
model**, chạy trên route thật.

### 8a. `c1a` — cầu cho thẳng bán kính, đề không đặt tên điểm nào

Đề: *"Cho khối cầu (S) có bán kính bằng 9. Tính thể tích khối cầu và diện tích
mặt cầu (S)."*

Chương trình mô hình sinh ra **đúng về toán và đúng cấu trúc**: `ban_kinh_s`
neo vào dữ kiện, `construct_curved_solid(ball, anchor=O, radius=ban_kinh_s)` —
dùng đúng dạng `radius` mà wave `3ffebcd` mở ra — rồi đo `volume` và
`lateral_area`. Thứ **duy nhất** bị chặn: `O = [0,0,0]`, tâm, không neo được.

Đo bằng `check_grounding` trên 5 biến thể:

| biến thể | mã lỗi |
|---|---|
| ① trần (không fact, không assumption) | `INPUT_NOT_GROUNDED` |
| ② `model_assumption` có nêu lý do | `UNANCHORED_DERIVED_ASSUMPTION` |
| ③ `source_fact_id` trỏ dữ kiện bán kính | `INPUT_NOT_GROUNDED` |
| ④ đổi tên (`S_tam`) + assumption | `UNANCHORED_DERIVED_ASSUMPTION` |
| ⑤ `point3` không có `initial_value` | `INPUT_NOT_GROUNDED` |

Gốc rễ: check ⑤ của grounding gate đòi `la_ten_nguon(tên, đề)` — **tên biến
phải xuất hiện trong đề**. Đo trực tiếp: `la_ten_nguon` trả `False` cho `O`,
`I`, `tam`, `S_tam`, `(S)`. Đề **không đặt tên cho điểm nào**, nên không tên nào
đi qua được.

⇒ `construct_curved_solid` **bắt buộc** một `anchor: point3`; grounding gate
**cấm** khai bất kỳ `point3` nào cho đề không đặt tên điểm. **Hai đòi hỏi
loại trừ nhau.**

### 8b. `c4b` — trụ, và `radius` không dùng được cho trụ

Đo ở mức lược đồ:

```
`radius` không dùng cho hình trụ; hãy khai `rim_point` — một điểm trên vành
đáy, để engine biết mặt đáy nằm đâu
```

`contract.py` cho `radius` **chỉ** khi `KHOI_CONG[kind].khai_bang_ban_kinh` —
bật cho **ball**, tắt cho trụ và nón. Nên trụ/nón **bắt buộc** `rim_point`: một
điểm trên vành đáy. Đề SGK cho trụ/nón bằng (bán kính, chiều cao) và đặt tên
nhiều nhất là hai điểm trên **trục** — không bao giờ đặt tên điểm trên vành.

Đo 5 đường cho `c4b` (đề đặt tên `P`, `P′`):

| đường | kết quả |
|---|---|
| A rim khai thẳng, không neo | bị chặn |
| B rim + `model_assumption` | bị chặn |
| C rim + `source_fact_id` = dữ kiện bán kính | bị chặn |
| D **DỰNG** rim = `translate(P, v)`, `v` là `vector3` mang assumption | bị chặn |
| E rim dùng lại tên `P` | bị chặn |

Đường D là đường quan trọng nhất: nó là cách "đúng" theo tinh thần R0 — **dựng**
thay vì **khai**. Nó vẫn bị chặn, vì `v` cũng phải qua check ⑤ và tên `v` không
có trong đề. Bộ toán tử dựng điểm hiện có (`midpoint` · `project_onto` ·
`intersect_*` · `divide_segment` · `translate`) **không có** phép nào sinh một
điểm cách tâm một khoảng cho trước theo phương vuông góc trục.

⇒ Với **6 ca trụ và nón**, không đường nào dựng được `rim_point` neo được.

### 8c. `c5b` · `c9b` — cổng phủ, giới hạn HỆ đã khai trong mã

Cả hai đòi `radius` của một `circle3` sinh từ phép giao mặt phẳng ∩ khối cong.
`contract.py` khai thẳng: *"`radius` thì KHÔNG suy ra được cho một `circle3`
sinh từ phép giao"*. Đây là `SYSTEM_COVERAGE_FAILURE` — giới hạn hệ đã biết,
không phải mô hình viết sai.

## 9. Ngưỡng (Bước 6)

Áp nguyên văn `curved_v3_threshold_policy.json` v1.1.0 (`460e0ce5…`):

| ngưỡng | yêu cầu | đo được | |
|---|---|---|---|
| `family.eventual_servable_rate` ball | 1.0 | 0/3 | **FAIL** |
| `family.eventual_servable_rate` cylinder | 1.0 | 0/3 | **FAIL** |
| `family.eventual_servable_rate` cone | 1.0 | 0/3 | **FAIL** |
| `positive_eventual_servable` | 9/9 | **0/9** | **FAIL** |
| `positive_exact_answer_match` | 9/9 | **0/9** | **FAIL** |
| `system_errors_allowed` | 0 | **2** | **FAIL** |
| `attribution_unresolved_allowed` | 0 | **2** | **FAIL** |
| `honest_unsupported_refusal` | 4/4 | 4/4 | ✅ |
| `target_boundary_demonstrated` | 4/4 | **1/4** | **FAIL** |

`run_validity`: 13/13 ca có artifact · mọi attempt trong mẫu số · 0 identity
drift · manifest đủ trường · 0 lỗi hạ tầng ⇒ `RUN_VALIDITY = VALID`.
Lượt đo hợp lệ; **kết quả** là FAIL.

## 10. Hậu kiểm danh tính

| | trước | sau |
|---|---|---|
| candidate | `a696200e8f8c668c…` (89) | `a696200e8f8c668c…` (89) · verify exit 0 |
| pool | `36c2153ecefd2dbf…` | `36c2153ecefd2dbf…` |
| runner | `6570b57bd6ac1fe4…` | `6570b57bd6ac1fe4…` |
| certifier | `070189b54af2b2ae…` | `070189b54af2b2ae…` |
| scorer | `4f7cae906500e0b6…` | `4f7cae906500e0b6…` |
| threshold | `460e0ce57a304872…` | `460e0ce57a304872…` |
| rubric | `d44f2b7c19b4904f…` | `d44f2b7c19b4904f…` |
| loader | `b51e936f809bd314…` | `b51e936f809bd314…` |

```
RUN_IDENTITY_STABLE = YES   (8/8 băm không đổi)
QUÉT BÍ MẬT         = KHÔNG CÓ
```

## 11. Artifact

| file | sha256 |
|---|---|
| `manifest.json` | `b2a454f0b285c5f1061798a52dc367efcba5ebb3d0a4f30da6eb0e38776c146a` |
| `stage_8a_one_shot.json` | `f3439fb6db1d568b3ac2723ad52b6a58358bc9786012dffdff4a0fc4122f53bb` |
| `curved_acceptance.json` | `70d47a9542561209ce5f4f0d50184e638866eca27f49f8594eb6b6e4e05a49b5` |
| `attribution.json` | `280a3fe1290305b5c21deea4c035bf0a423ce280cc975a9c34839df411d85610` |

Tất cả ở `docs/evaluation/geometry/curved-acceptance-v3/`.

## 12. Giới hạn

**① Evaluator KHÔNG độc lập.** Phiên chạy lượt đo cũng là phiên viết
`radius_sq_khai`, `area`/`lateral_area`, scorer, runner và bản vá wiring. Miễn
trừ do người vận hành cấp. Con số này là **nghiệm thu nội bộ**; nó không thay
được một lượt đo độc lập, và khoá luận phải khai đúng như vậy.

**② Chỉ đo được one-shot.** `REPAIR_ELIGIBLE_FAILURES = 0` nên 8B không chạy;
`EVENTUAL` bằng `FIRST_ATTEMPT` theo cấu trúc. Năng lực **tự sửa** chưa đo.

**③ 26/78 lượt gọi được dùng.** Không phải vì tiết kiệm mà vì vòng sửa không
kích hoạt — xem ②.

**④ `derived radius` không có ca nào.** Đúng khoảng trống mà
`ACCEPTANCE_SCORER_EXPRESSIVENESS_CLASS` chuẩn bị để đo lại **không** rơi vào
tập rút. `NOT_MEASURED`.

**⑤ Rubric không adjudicate được khoảng trống tìm thấy.** Xem §7.

**⑥ `c8b` chưa đo riêng.** Nghi cùng gốc `c1a`/`c4b` nhưng không có probe
riêng, nên xếp theo stage chứ **không** nâng thành lỗi hệ.

**⑦ Tái lập ở mức `LIMITED`.** Alias `gemini-2.5-flash`, không snapshot;
`response_model_version = UNAVAILABLE_TO_RUNNER`. Không tuyên bố bit-for-bit.

**⑧ `PHYSICAL_API_ATTEMPTS` suy ra, không đo trực tiếp.** Telemetry ghi lượt
**logic**; runner không phơi bộ đếm `http_requests`. 26 = 26 và `dung_som=null`
⇒ suy ra 0 retry. Muốn đo thẳng thì phải phơi `ApiBudget.http_requests`.

## 13. Product promotion

```
PRODUCT_PROMOTION_ELIGIBLE_BALL     = NO
PRODUCT_PROMOTION_ELIGIBLE_CYLINDER = NO
PRODUCT_PROMOTION_ELIGIBLE_CONE     = NO
PRODUCT_CAPABILITY_CHANGED          = NO
```

`ball` · `cylinder` · `cone` giữ **`foundation_only`**. Năm mức của nhiệm vụ,
sau lượt đo này:

| mức | trạng thái |
|---|---|
| `EXPRESSIBLE` | **một phần** — cầu biểu đạt được khi đề đặt tên điểm; trụ/nón **không** khi đề không đặt tên điểm vành (§8b) |
| `DETERMINISTICALLY_CORRECT` | **CLOSED** — kernel đúng, không lượt nào cho số sai |
| `MODEL_DISCOVERABLE` | **NO** — 0/9 |
| `STABLE` | **NO** |
| `PRODUCT_SUPPORTED` | **NO** |

## 14. Việc tiếp theo

```
RECOMMENDED_NEXT_ACTION = CURVED_CONSTRUCTION_GROUNDING_FOUNDATION
```

Không phải `TARGETED_CURVED_SYNTHESIS_ERGONOMICS`: nút thắt **không** phải mô
hình chọn sai một đường đang có — với `c1a` và `c4b` **không có đường nào**
(§8). Không phải `DERIVED_SCALAR_EXPRESSIVENESS_FOUNDATION`: khoảng trống ấy
không có ca nào rút trúng nên vẫn `NOT_MEASURED`. Không phải
`MEASUREMENT_INVALIDATION_REVIEW`: lượt đo hợp lệ, danh tính không trôi.

Ba việc, theo thứ tự, **đều đụng `backend/app`** ⇒ phá đóng băng candidate ⇒
cần quyết định riêng và reseal sau đó:

1. **Cho trụ/nón khai bằng `radius`** — bật `khai_bang_ban_kinh` cho cylinder và
   cone, hoặc thêm một dạng dựng `(anchor, apex_or_top, radius)`. Đây là đường
   ngắn nhất và bịt đúng 6/9 ca.
2. **Cho phép neo điểm-đặt hệ quy chiếu.** Một đề "khối cầu bán kính 9" không
   đặt tên tâm; hệ cần một lối hợp lệ để đặt gốc toạ độ mà không bị check ⑤ coi
   là rửa năng lực. Ranh giới phải giữ: điểm **suy ra** vẫn phải dựng.
3. **`radius` cho `circle3` sinh từ phép giao** — bịt `c5b`, `c9b`.

Sau đó mới đo lại, và lượt đo lại **phải** dùng pool mới: pool V3 đã tiêu.

---

```text
EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED
MEASUREMENT_CLASS = INTERNAL_ONE_SHOT_ACCEPTANCE
PRE_DRAW_GUARD = PASS
DRAW_COUNT = 1
EXTERNAL_SEED = 5324284654432805119
RUN_ID = curved-acceptance-v3
CASE_SET_HASH = eb1c402a71517553815270b3ee0198685d7797efca813d8db760e6087dff4674
RUN_VALIDITY = VALID

MANIFEST_WRITTEN_BEFORE_FIRST_CALL = YES
V3_LIVE_ENTRYPOINT_INTEGRATION = PASS
RUN_IDENTITY_STABLE = YES

TOTAL/POSITIVE/NEGATIVE_CASES = 13 / 9 / 4
BALL/CYLINDER/CONE_CASES = 3 / 3 / 3   (ca dương)

LOGICAL_APPLICATION_CALL_BUDGET = 78
PHYSICAL_API_ATTEMPT_BUDGET = 312
LOGICAL_APPLICATION_CALLS_USED = 26
PHYSICAL_API_ATTEMPTS_USED = 26   (suy ra)
TRANSPORT_RETRIES_USED = 0        (suy ra)

FIRST_ATTEMPT_SERVABLE = 0/9
EVENTUAL_SERVABLE = 0/9           (= first-attempt THEO CẤU TRÚC — 8B không chạy)
EXACT_ANSWER_MATCH = 0/9
POSTCONDITIONS_PASS = 0/9
SCENE3D_PASS = 0/9

SYSTEM_EXPRESSIVENESS_GAP_COUNT = 0
ATTRIBUTION_UNRESOLVED_COUNT = 2
MODEL_FAILURE_COUNT = 5
NEGATIVE_HONEST_REFUSAL = 4/4
TARGET_BOUNDARY_PASS = 1/4

GENERAL_CURVED_SYNTHESIS_ACCEPTANCE = FAIL
PRODUCT_PROMOTION_ELIGIBLE_BALL = NO
PRODUCT_PROMOTION_ELIGIBLE_CYLINDER = NO
PRODUCT_PROMOTION_ELIGIBLE_CONE = NO
PRODUCT_CAPABILITY_CHANGED = NO

CANDIDATE_HASH_BEFORE/AFTER = a696200e8f8c668c… / a696200e8f8c668c…
POOL_HASH_BEFORE/AFTER = 36c2153ecefd2dbf… / 36c2153ecefd2dbf…
RUNNER_HASH_BEFORE/AFTER = 6570b57bd6ac1fe4… / 6570b57bd6ac1fe4…
SCORER_HASH_BEFORE/AFTER = 4f7cae906500e0b6… / 4f7cae906500e0b6…
THRESHOLD_POLICY_HASH_BEFORE/AFTER = 460e0ce57a304872… / 460e0ce57a304872…
ATTRIBUTION_RUBRIC_HASH_BEFORE/AFTER = d44f2b7c19b4904f… / d44f2b7c19b4904f…
POLICY_LOADER_HASH_BEFORE/AFTER = b51e936f809bd314… / b51e936f809bd314…

RUN_ARTIFACT_HASH = curved_acceptance.json 70d47a9542561209… ·
                    stage_8a_one_shot.json f3439fb6db1d568b… ·
                    manifest.json b2a454f0b285c5f1… ·
                    attribution.json 280a3fe1290305b5…
REPORT = docs/CURVED_V3_LIVE_ACCEPTANCE.md
RECOMMENDED_NEXT_ACTION = CURVED_CONSTRUCTION_GROUNDING_FOUNDATION
```
