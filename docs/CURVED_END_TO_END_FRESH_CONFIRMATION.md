# CURVED_END_TO_END_FRESH_CONFIRMATION

> 2026-09-07. **1 đề hình CONG mới, đi TRỌN đường sản phẩm.**
> `MEASUREMENT_CLASS = DEVELOPMENT_CURVED_END_TO_END_CONFIRMATION` ·
> `HELD_OUT_CLAIM = NO` · `EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED`.
>
> ```
> CURVED_END_TO_END_FRESH_CONFIRMATION = PASS
> CARD_C_OUTSIDE_SEGMENT_FAMILY        = CONFIRMED_ON_ONE_CASE
> CURVED_MODEL_DISCOVERABILITY         = DEVELOPMENT_SIGNAL
> STABILITY_UNDER_ACCEPTANCE           = NOT_MEASURED
> CARD_OPTIMIZATION_SEQUENCE           = CLOSED
> ```
>
> Khác mọi wave A/B trước ở **hai** điều, cả hai là chủ đích: `analyze` là một
> lượt LLM **thật** (hợp đồng do mô hình trích, không phải hợp đồng cố định),
> và **vòng sửa của sản phẩm không bị tắt**. Đổi lại, phép đo này **không
> tách** được đóng góp của từng tầng.

## 1. Trạng thái đầu — khớp bàn giao

HEAD `3c04018` · cây **sạch** · `CACHE_VERSION` **86** · candidate
`138db7b1…` (`--verify` exit 0, 90 file) · `PRODUCT_VARIANT` **C**.

Thẻ chạy live **không nạp từ file**: runner lấy `grammar_card("hinh_hoc")` —
thẻ sản phẩm hiện hành — rồi **từ chối chạy** nếu nó đã trôi khỏi
`ac07f716…`. Lượt chạy xác nhận trùng byte, 5855 B.

Sáu băm model-facing @ v86: `prompts 55ac1ca6…` · `grammar_card 9685b06a…` ·
`synthesis_schema 8c57c9de…` · `analyze_schema 515001b5…` ·
`capability 85bd3167…` · `semantic_environment 2178b6d4…`.

## 2. Đề và oracle

> Hình nón có đỉnh S, tâm đáy O, bán kính đáy bằng 12 và chiều cao SO bằng 18.
> Điểm T nằm trên đoạn SO sao cho ST:TO = 1:2. Mặt phẳng qua T và vuông góc
> với SO cắt hình nón theo đường tròn (c). Tính bán kính của đường tròn (c).

```
ST : TO = 1 : 2  ⇒  t(S→O) = 1/3
r(c) = 12 × 1/3  =  4
```

Đề **chưa từng xuất hiện** trong bất kỳ corpus nào (khoá bằng `test_D1`). Nó
buộc dùng **cả năm** mảnh mà ba wave gần đây dựng lên, mỗi mảnh đúng một lần —
nên một mảnh hỏng là cả bài hỏng, và chỗ hỏng chỉ đúng một chỗ.

**Oracle được kiểm chéo ba lối độc lập**, không phải một:

| lối | kết quả |
|---|---|
| tỉ lệ trên trục `r = R·(ST/SO)` | 4 |
| chiều cao còn lại từ đáy `r = R·(1 − OT/SO)` | 4 |
| **KERNEL** `intersect_plane_curved(cone, ⊥ qua T)` | 4 |

Và **bộ đọc đề của sản phẩm** tự dẫn ra `segment_division(S,O,T) = 1/3` ·
`segment_length(O,S) = 18` — khớp oracle mà không do ta gán.

## 3. `SYSTEM_EXPRESSIBLE = YES` — bảy câu, mỗi câu một chứng cứ

| # | câu hỏi | đáp | chứng cứ |
|---|---|---|---|
| ① | IR biểu đạt được nón `R=12`, `h=18`? | **YES** | `_KIEU_DUNG['construct_curved_solid'] → curved_solid`; ô `radius` nhận TÊN một đại lượng (`CENTER_RADIUS_…`); `MemoryType` có `curved_solid` |
| ② | S, O, T có provenance hợp lệ? | **YES** | `model_assumption` / `source_fact_id` trên khai báo; `test_B1`/`B5` |
| ③ | T dựng bằng `divide_segment` `t=1/3`? | **YES** | `_CHU_KY['divide_segment'] → point3`; `test_B3` |
| ④ | Mặt phẳng qua T ⊥ SO? | **YES** | `construct_line → line3`, rồi `plane_perpendicular_to_line(point, line) → plane3` |
| ⑤ | `intersect_plane_curved` nhận nón, trả `circle3`? | **YES** | `_CHU_KY: ((solid: curved_solid), (plane: plane3)) → circle3`; `test_B4` khẳng định kiểu THẬT là `circle3` |
| ⑥ | `measure(radius)` + checker xác nhận 4? | **YES** | `OBLIGATION_KINDS['radius'] = {curved_solid, circle3}`; `test_B1` cho `EXACT_ANSWER = 4`; `test_A3` kiểm chéo ở KERNEL |
| ⑦ | Trace và Scene3D biểu diễn được? | **YES** | `test_B3/B6/B7` — 6 vật có producer + depends đúng, 7 sự kiện, thứ tự phụ thuộc đúng, `T = (0,0,12)` |

⚠️ **Một lỗ được ghi ở đây, và nó KHÔNG phải lỗ năng lực.** Dòng
`type nhận đúng một trong` của thẻ liệt kê
`bool float point3 vector3 line3 plane3 polygon3 solid section` — **không có
`circle3`, không có `curved_solid`**, dù `MemoryType` có cả hai và mọi gold đều
**phải** khai chúng. Nguyên nhân là một bộ lọc viết tay trong `_the_hinh_hoc`.
Đây là lỗ **DISCOVERABILITY của thẻ**, và §6 cho thấy nó có giá đo được.

## 4. Gold preflight — 19 pass, 0 lượt gọi

`GOLD_PREFLIGHT_RESULT = PASS`. Gold đi trọn: schema · grounding · static ·
coverage · **cả hai** bất biến nguồn · runtime · postconditions ·
**`EXACT_ANSWER = 4`** · trace · Scene3D · `SERVABLE`.

Sáu vật, mỗi vật đúng producer và dependency:

```
non      curved_solid  construct_curved_solid.cone     ← O, S, r_day
truc_SO  line3         construct_line                  ← O, S
T        point3        construct_point.divide_segment  ← O, S
mp_cat   plane3        plane_perpendicular_to_line     ← T, truc_SO
c        circle3       intersect_plane_curved          ← mp_cat, non
ban_kinh_c quantity    measure.radius                  ← c
```

**Bảy phản ví dụ, mỗi cái chặn ở ĐÚNG tầng của nó** — không cái nào "đỏ nhờ
tầng khác":

| phản ví dụ | chặn ở | mã |
|---|---|---|
| ratio sai **nhưng trong đoạn** (`1/2`) | `source_invariant` | `NORMALIZED_SOURCE_VIOLATED` |
| T khai thẳng toạ độ, bỏ câu lệnh dựng | `grounding` | `DERIVED_ENTITY_WITHOUT_PRODUCER` |
| toạ độ S trái chiều cao đề cho (`99`) | `source_invariant` | `OS = 18: … có OS² = 9801 (cần 324)` |
| giao với **sai kiểu** (`line3`) | `ir_static` | `IR_OPERAND_TYPE` |
| điểm ngoài trục **bịa ra** | `grounding` | `UNANCHORED_DERIVED_ASSUMPTION` |
| đo bán kính **sai chủ thể** (khối nón thay vì `(c)`) | `structural_coverage` | `witness … không dẫn xuất từ '(c)'` |
| **KERNEL**: mặt phẳng không ⊥ trục | kernel | `CURVED_SECTION_OUTSIDE_V1_CLOSURE` |

⚠️ Phản ví dụ cuối phải hỏi **thẳng kernel**. Ở tầng IR, một mặt cắt xiên
**không dựng nổi** mà không bịa thêm một điểm ngoài trục — và `grounding` bắt
điểm bịa ấy **trước**. Hỏi qua IR thì câu trả lời sẽ đến từ một cổng KHÁC, tức
đúng kiểu "đỏ nhờ tầng khác" mà kho này cấm.

**Nền đỏ đã chứng minh**: đặt oracle sai (`4 → 5`) ⇒ 2 test đỏ, gồm phép kiểm
số học độc lập. Thẻ trôi khỏi Card C ⇒ runner thoát `2`, **không ghi artifact**.

## 5. Lượt live — `curved-e2e-20260907T025742Z`

Gọi thẳng `pipeline.run_pipeline` (điểm vào sản phẩm, **không qua HTTP** — không
có cache nào để một kết quả cũ lẻn về).

```
STAGE = served    servable = True    envelope = ok
EXACT_ANSWER = 4                     (oracle 4)
LOGICAL 4/5 · PHYSICAL 4 · CANDIDATE 4 · RETRY 0 · TOKENS 19 263/37 500
```

**Ba ứng viên, hai lượt sửa.** `FIRST_ATTEMPT_SERVABLE = False` ·
`EVENTUAL_SERVABLE = True`.

| attempt | hỏng ở | chẩn đoán validator gửi ngược |
|---|---|---|
| 0 | schema | `memory_declarations[0].at`: `at` là trường của `declare_point`, chuyển sang `initial_value` |
| 1 | `ir_static` | `IR_OPERAND_TYPE: 'cone_S_O_A' — cần solid, có curved_solid`; `'c' — cần circle3 hoặc curved_solid, có section` |
| 2 | — | **`served`** |

**Hai lỗi ấy đều là lớp lỗi ĐÃ BIẾT, và cả hai đều tự đóng bằng vòng sửa:**

- **attempt 0** — đúng lớp `POINT_INITIALIZATION` mà
  `POINT_INITIALIZATION_REPAIR_EFFICACY` đo được là *"vòng sửa sẵn có tự đóng
  trong 1 lượt"*. Lần này nó tái hiện trên một bài **khác hẳn** và vẫn tự đóng.
  Đó là bằng chứng thứ hai cho `PERMANENT_SLOT_INSTRUCTION_NEEDED = NOT_PROVED`
  — quyết định **không** thêm dòng hướng dẫn về ô `at` vào Card C được giữ
  vững thêm một ca.
- **attempt 1** — mô hình với tay tìm `construct_section` cho một khối **cong**,
  rồi đo `radius` trên một `section`. Đây là **đúng lớp lỗi `c5b`/`c9b`** mà
  `CURVED_SECTION_RADIUS_PATH_ADJUDICATION` đã phân xử: hai đường khác nhau,
  `construct_section` nhận khối **đa diện** → `section`, còn
  `intersect_plane_curved` nhận `curved_solid` → `circle3`. Wave ấy kết luận
  `SYSTEM_IMPLEMENTATION_GAP = NO` và gọi đó là **lựa chọn của mô hình**. Lượt
  này cho thấy lựa chọn ấy **vẫn tái hiện**, và **vẫn sửa được** trong một lượt.

## 6. Chấm theo từng tầng

### 6a. Analyze — và một đính chính bộ chấm

```
ANALYZE_OBLIGATION_CORRECT = PASS   (kind `radius`, container `(c)`, witness `r_c`)
ANALYZE_FACTS_CORRECT      = NOT_CAPTURED
SO_FACT                    = 8      (quan sát từ sự kiện `semantic_contract`)
```

⚠️ **Đính chính, khai TRƯỚC khi dùng số.** Bản chấm inline của lượt chạy ghi
`ANALYZE_CONTRACT_CORRECT = FAIL` — trong khi runner **chưa hề giữ** raw của
tầng `analyze`, nên bộ chấm đọc rỗng rồi kết luận trượt. Đó là **chấm FAIL cho
một tầng nó không quan sát được**, cùng họ với lỗi mà
`PROVENANCE_AFFORDANCE_AB_4_LUOT §6` đã đính chính một lần (`GROUNDING = PASS`
cho tầng chưa chạy).

Bộ chấm nay phân biệt **ba** giá trị — `PASS/FAIL` khi có dữ liệu ·
`NOT_CAPTURED` khi bộ đo không giữ thứ cần để phán · `NOT_REACHED` khi tầng ấy
chưa chạy. Runner đã sửa để giữ raw analyze (`test_C5`), và bộ chấm vẫn **FAIL
được** khi có dữ liệu và dữ liệu sai (`test_C7` — đính chính không được làm bộ
chấm mất răng). Artifact lượt chạy **giữ nguyên từng byte**; kết quả đúng nằm ở
`SCORING.json`.

Điều **biết chắc** về analyze ở lượt này: nó trích **8** dữ kiện, khai đúng
nghĩa vụ `radius` với container `(c)` — và chương trình sinh từ hợp đồng ấy đi
qua **cả hai** bất biến nguồn, tức các con số `12`, `18`, `1:2` đã tới được
hình dựng. Nội dung từng fact thì **lượt sau mới chấm được**.

### 6b. Synthesis — mọi chiều PASS

| chiều | kết quả |
|---|---|
| toán tử dựng khối cong | `construct_curved_solid`, `curved_kind = cone` ✅ |
| khai bằng | **`rim_point`** (mô hình tự dựng điểm `A` trên vành, không dùng ô `radius`) |
| toán tử thiết diện | `intersect_plane_curved` ✅ |
| kiểu kết quả giao | **`circle3`** ✅ |
| `ratio` | **`1/3`**, chiều `S->O` ✅ |
| T được TẠO bằng câu lệnh | **có** ✅ |
| đo đúng chủ thể | `measure(radius, of = c)` ✅ |
| xuất xứ điểm đầu vào | `O`, `S`, `A` — **cả ba** có `model_assumption` ✅ |

**Hai delta của Card C hiện rõ trên một bài hình cong**: `ratio 1/3` là con số
quy từ `m:n` (đúng thứ dòng `ratio` dạy), và cả ba điểm đầu vào đều đi kênh
`model_assumption` (đúng thứ dòng `Xuất xứ:` dạy). Không lượt nào trong ba
attempt hỏng ở hai trục ấy.

### 6c. Kết quả mô phỏng

```
GROUNDING · SOURCE_INVARIANTS · STATIC · COVERAGE · RUNTIME · POSTCONDITIONS = PASS
EXACT_ANSWER = 4   ·   TRACE_CONSTRUCTION = PASS   ·   SCENE3D = PASS (9 vật)
SERVABLE = True    ·   ENVELOPE = ok
```

## 7. Token

| | token |
|---|---:|
| analyze | **2 296** |
| synthesis + 2 repair (gộp theo TẦNG) | **16 967** — 3 lượt, TB **5 656**/lượt |
| tới first attempt | **≈ 7 952** (ước lượng) |
| tới eventual result | **19 263** |
| trên một mô phỏng `served` đúng | **19 263** |
| `cached_content` | **0** ở cả hai tầng ⇒ **không nhiễu cache** |

⚠️ Telemetry gộp theo **TẦNG**, không theo attempt — nên token của riêng lượt
đầu chỉ **ước lượng** được bằng trung bình, và nó được ghi là ước lượng chứ
không ghi như số đo.

## 8. Bộ đếm — và một chỗ dễ đọc nhầm, đã sửa

```
LOGICAL_APPLICATION_CALLS = 4      PHYSICAL_API_ATTEMPTS = 4
CANDIDATE_ATTEMPTS        = 4      TRANSPORT_RETRIES     = 0
  phân rã theo tầng: semantic_analyze 1 · semantic_program 3
```

⚠️ **`CANDIDATE_ATTEMPTS = 4` KHÔNG phải 4 ứng viên chương trình.** Một wave
end-to-end gọi model ở nhiều tầng: `analyze` trả một **hợp đồng**,
`semantic_program` trả một **chương trình**. Đọc tổng một mình là đúng lớp hiểu
nhầm mà `REPAIR_PROBE_COUNTER_DECOMPOSITION` đi sửa — nên `wave_counters` nay
phát **phân rã theo tầng** cùng với tổng, khoá bằng `test_C4`.

Số ứng viên **chương trình** là **3**, và số lượt sửa là **2**.

## 9. Kết luận theo luật đã đăng ký

Nhánh *"eventual `served` với đáp số 4"*:

```
CURVED_END_TO_END_FRESH_CONFIRMATION = PASS
CARD_C_OUTSIDE_SEGMENT_FAMILY        = CONFIRMED_ON_ONE_CASE
CURVED_MODEL_DISCOVERABILITY         = DEVELOPMENT_SIGNAL
STABILITY_UNDER_ACCEPTANCE           = NOT_MEASURED
CARD_OPTIMIZATION_SEQUENCE           = CLOSED
```

Product Card **C** giữ nguyên. **Không đụng một dòng mã sản phẩm nào**:
`CACHE_VERSION` 86 → 86, candidate `138db7b1…` không đóng băng lại, sáu băm
model-facing không đổi một byte, `PRODUCT_CAPABILITY_CHANGED = NO`.

## 10. Cổng đã chạy

| cổng | kết quả | mới / kế thừa |
|---|---|---|
| tiền kiểm wave | **19 pass**, 0 lượt gọi | **mới** |
| runner stub | **21 pass**, 0 lượt gọi | **mới** |
| bộ đếm ba trường | **12 pass** (thêm `test_C4`) | **mới** |
| curved foundation · curved section · derived-point · source-invariant | trong **192 pass** của lượt chọn lọc | **mới** |
| `pytest -q` (cây sạch sau commit) | **4141 pass**, 1 skip, 1 deselect, **0 đỏ** | **mới** |
| `vitest run` · `npm run build` | **698/51** · PASS | **mới** |
| `replay_demo_cases.py` | **5/5**, `REDUCED_CHAIN 1/1` | **mới** |
| `audit_demo_crash_surface.py` | **6/6 biên**, ném **0** | **mới** |
| `lock_cache_identity.py --verify` | **exit 0** @ v86 | **mới** |
| `freeze_evaluation_candidate --verify` | **exit 0**, 90 file, `138db7b1…` | **mới** |
| `git diff --check` | sạch | **mới** |

## 11. Báo cuối

```
SYSTEM_EXPRESSIBLE     = YES   (7/7 cau, moi cau tro chu ky hoac test)
GOLD_PREFLIGHT_RESULT  = PASS  (19 pass · 7 phan vi du · nen do da chung minh)

APPLICATION_LLM_CALLS  = 4     ANALYZE_CALLS = 1
SYNTHESIS_CALLS        = 1     REPAIR_CALLS  = 2
LOGICAL_APPLICATION_CALLS = 4  PHYSICAL_API_ATTEMPTS = 4
CANDIDATE_ATTEMPTS     = 4     (analyze 1 · semantic_program 3)
TRANSPORT_RETRIES      = 0     TOTAL_TOKENS = 19 263 / 37 500

ANALYZE_CONTRACT_CORRECT = obligation PASS · facts NOT_CAPTURED (8 fact quan sat)
FIRST_ATTEMPT_STAGE      = schema (`at` sai o)
FIRST_ATTEMPT_SERVABLE   = NO
REPAIR_ATTEMPTS          = 2   (attempt 1: IR_OPERAND_TYPE — construct_section
                                cho khoi CONG, do radius tren `section`)
EVENTUAL_STAGE           = served
EVENTUAL_SERVABLE        = YES

RATIO                        = 1/3  (chieu S->O)          PASS
CURVED_CONSTRUCTION_OPERATOR = construct_curved_solid.cone (khai bang rim_point)
SECTION_OPERATOR             = intersect_plane_curved -> circle3
EXACT_ANSWER                 = 4    (oracle 4)            PASS
POSTCONDITIONS               = PASS
TRACE_CONSTRUCTION           = PASS
SCENE3D                      = PASS (9 vat)

CARD_C_HASH                      = ac07f716c53d468e… (5855 B, trung byte the san pham)
MODEL_FACING_HASHES_BEFORE_AFTER = KHONG DOI ca sau
CACHE_VERSION_BEFORE_AFTER       = 86 → 86  (khong bump: khong doi be mat mo hinh)
CANDIDATE_HASH_BEFORE_AFTER      = 138db7b1… → 138db7b1…  (khong dong bang lai)
PRODUCT_CAPABILITY_CHANGED       = NO

TEST_RESULTS = pytest 4141 pass · 1 skip · 1 deselect · 0 do
               vitest 698/51 · build PASS · replay 5/5 · crash 6/6 nem 0
COMMITS      = 3        WORKING_TREE = sach
RECOMMENDED_NEXT_ACTION = CURVED_MISSING_FAMILY_ROADMAP_AND_FIRST_IMPLEMENTATION
```

## 12. Giới hạn bằng chứng

- **`n = 1` ca.** `DEVELOPMENT_SIGNAL`, không phải ước lượng tổng thể.
  `CAUSAL_ATTRIBUTION = LIMITED`.
- **Một ca thành công chứng minh đường end-to-end TỒN TẠI.** Nó **chưa đủ** để
  chuyển `ball`/`cylinder`/`cone` sang `supported` — `product_capability.py`
  vẫn là thẩm quyền, và nó không đổi.
- **Không tách được đóng góp từng tầng.** Đó là cái giá của việc đo cả đường:
  analyze, synthesis và vòng sửa cùng nằm trong một con số.
- **Không phải lượt sinh ĐÚNG NGAY.** `FIRST_ATTEMPT_SERVABLE = NO`; kết quả
  đạt được **nhờ** vòng sửa. Nói *"mô hình tự sinh đúng bài hình cong"* là nói
  quá; câu đúng là *"đường sản phẩm — gồm cả vòng sửa — phục vụ được bài này"*.
- **Nội dung fact của analyze `NOT_CAPTURED`** ở lượt này (§6a). Runner đã sửa;
  lượt sau chấm được.
- `gemini-2.5-flash` là **alias, không phải snapshot** ⇒ `reproducibility =
  LIMITED`.
- Ba mức bằng chứng **không trộn**: *"đáp số đúng"* · *"có bước dựng đúng"* ·
  *"AI tự sinh ổn định"* (**chưa đo**).

### 12a. Hai `HYPOTHESIS` — chưa có phép đo phân biệt

- **Thẻ không liệt kê `circle3`/`curved_solid` trong các kiểu khai được** (§3),
  và attempt 1 hỏng đúng ở chỗ khai `c` là **`section`**. Hai điều ấy **khớp
  nhau**, nhưng `n = 1` không tách được *"thẻ thiếu kiểu"* khỏi *"mô hình quen
  tay với `construct_section`"* — lớp lỗi `c5b`/`c9b` đã tái hiện nhiều lần
  **trước** khi có Card C. `HYPOTHESIS`, và là ứng viên blocker rẻ nhất nếu
  lượt sau hỏng lại đúng chỗ này.
- **Mô hình chọn `rim_point` thay vì ô `radius`**, dù đề cho bán kính bằng
  **số** và ô `radius` tồn tại đúng cho lớp bài ấy
  (`CENTER_RADIUS_CURVED_CONSTRUCTION_FOUNDATION`). Nó **không gây lỗi** —
  dựng thêm một điểm vành là cách hợp lệ. Nhưng nó nói rằng affordance của ô
  `radius` **chưa được chọn** khi có đường thay thế. `HYPOTHESIS`, `n = 1`.

**Việc kế tiếp: `CURVED_MISSING_FAMILY_ROADMAP_AND_FIRST_IMPLEMENTATION.**
Chuỗi tối ưu thẻ **đóng** ở đây theo đúng luật đã đăng ký. Chọn họ hình mới đầu
tiên bằng **kiểm toán chữ ký + mức tái sử dụng kernel**, ưu tiên **thiết diện
cong xiên** nếu bằng chứng xác nhận đây là phần mở rộng nhỏ nhất — lưu ý rằng
`CURVED_SECTION_OUTSIDE_V1_CLOSURE` (§4) là **đúng đoạn chữ ký** phải mở, và
kernel đã nói ra ranh giới ấy bằng một mã ổn định thay vì một số sai im lặng.

⚠️ Token của Claude Code **không** tính vào token vận hành AlgoSim; replay,
checker và Scene3D không dùng token Gemini.
