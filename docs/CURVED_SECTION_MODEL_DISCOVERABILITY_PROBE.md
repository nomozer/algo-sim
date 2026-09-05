# CURVED_SECTION_MODEL_DISCOVERABILITY_PROBE

> 2026-09-05. `MEASUREMENT_CLASS = DEVELOPMENT_DIAGNOSTIC` · `HELD_OUT_CLAIM = NO`
> · `V4_POOL_CONSUMED = NO` · `PRODUCT_PROMOTION_ALLOWED = NO`.
>
> **Tiêu quota thật**: 26 lượt gọi logic, 150 854 token. V3 không bị đụng tới ở
> bất kỳ đường nào; mã sản phẩm · lược đồ · thẻ văn phạm · prompt ·
> `CACHE_VERSION` · candidate đều **byte-identical** suốt lượt đo.

## 0. Câu trả lời

**Mô hình KHÔNG tự tìm ra `intersect_plane_curved`. Không một lần nào.**

Nhưng nó học được ngay lập tức từ một câu báo lỗi:

| | |
|---|---|
| lượt đầu chọn đúng toán tử (6 ca cong) | **0/6** |
| lượt đầu chọn `construct_section` (**cả 8 ca**) | **8/8** |
| sau **một** lượt sửa, chuyển sang `intersect_plane_curved` | **6/6** |
| phục vụ được trọn vẹn (6 ca cong) | **0/6** |
| đối chứng đa diện `d7` | **1/1 PASS** — `served`, `8√3` chính xác, một lượt |

Quỹ đạo toán tử của từng ca, đọc từ **văn bản chương trình** của từng attempt:

```
d1  CS → IPC          d5  CS → IPC
d2  CS → IPC → IPC    d6  CS → IPC
d3  CS → CS  → IPC    d7  CS                (đúng — ca đa diện)
d4  CS → IPC          d8  CS → CS  → CS
```

`CS` = `construct_section` · `IPC` = `intersect_plane_curved`.

Nói gọn: **`construct_section` là mặc định phổ quát của mô hình.** Nó áp phép ấy
cho mọi bài có chữ *"cắt … theo thiết diện"*, bất kể khối là đa diện hay khối
cong. Đúng lỗi đã giết `c5b`/`c9b` trong V3 — nay tái lập trên **tám đề hoàn
toàn mới, ký hiệu hoàn toàn khác**, nên nó không phải một sự cố của hai ca ấy mà
là một **thiên lệch bền vững**.

Câu báo lỗi làm nó đổi ý là câu này, và nó hiệu quả 6/6:

```
IR_OPERAND_TYPE: 'hinh_non' — cần solid, có curved_solid
IR_OPERAND_TYPE: 'sigma'    — cần circle3 hoặc curved_solid, có section
```

## 1. Baseline đã xác minh

```
WORKING_TREE     = CLEAN @ d6a8399
CACHE_VERSION    = 81
CANDIDATE_HASH   = d105f83e5f7de0cc…  (89 file, verify exit 0)
BACKEND_BASELINE = 3703 passed · 1 skipped · 1 deselected
FRONTEND_BASELINE= 698 passed / 51 file
V3_REEXECUTED    = NO      · V3_ARTIFACTS = byte-identical
PRODUCT_CAPABILITY = ball/cylinder/cone foundation_only
```

Băm ghi **trước** lượt gọi đầu tiên:

| | |
|---|---|
| `ANALYZE_SCHEMA_HASH` | `515001b503af5c7c…` |
| `SYNTHESIS_SCHEMA_HASH` | `8c57c9de49824d61…` |
| `GRAMMAR_CARD_HASH` | `e0fbbc8456da57ae…` |
| `PROMPT_HASH` | `55ac1ca6a6df92ce…` |
| `STABLE_CAPABILITY_HASH` | `85bd316781b86576…` |
| `SEMANTIC_ENVIRONMENT_HASH` | `f7def6207f5741d9…` |
| `RUNNER_HASH` | xem §9 (có một delta giữa hai lượt, khai đầy đủ) |
| `MODEL_PROVIDER` | `google-generativelanguage-v1beta` |
| `MODEL_NAME` | `gemini-2.5-flash` |
| `MODEL_VERSION_OR_SNAPSHOT` | **trống** — alias trôi, không phải snapshot |
| `TEMPERATURE` | `0.1` (cả analyze lẫn tổng hợp) |
| `TOP_P` / `MAX_OUTPUT_TOKENS` | không đặt — mặc định của provider |
| `REPAIR_LIMIT` | `3` (`MAX_SEMANTIC_PROGRAM_ATTEMPTS`) |

Credential kiểm bằng đường không in giá trị: `GEMINI_API_KEY: PRESENT`.
`kiem_moi_truong` chạy **trước mỗi ca**; không lệch lần nào.

## 2. Corpus đã đăng ký trước kết quả

8 ca, ký hiệu cố ý khác V3 hoàn toàn (`I·J·P`, `E·F·G·H`, `D·T·U·V`, `A·B·C·K`,
`N·Q`, `W·Z`, `O₁·O₂·R·T`, `(ω)(γ)(σ)(δ)(κ)(λ)`).

```
CORPUS_HASH           = 54264bd57e2b32829a2a72916cbbf03ba3b2f3b75d4271cda0e496e85eff4e83
EXPECTED_RESULTS_HASH = 9c964f8c95e1f7cadb9c3d84df8c0dac5c40866f9e71c8f1ab0bf8fdadd4b761
```

| ca | họ | hỏi | lớp toán tử đúng | đáp số đúng |
|---|---|---|---|---|
| `d1` | cylinder | bán kính + diện tích | `intersect_plane_curved` | `12` · `144π` |
| `d2` | cylinder | bán kính (cắt lệch trung điểm) | `intersect_plane_curved` | `7` |
| `d3` | cone | bán kính (vị trí theo `DV = 8`) | `intersect_plane_curved` | `6` |
| `d4` | cone | bán kính (`AK = ⅔·AB`) | `intersect_plane_curved` | `6` |
| `d5` | ball | bán kính giao tuyến | `intersect_plane_curved` | `24` |
| `d6` | ball | bán kính + diện tích | `intersect_plane_curved` | `15` · `225π` |
| `d7` | **đa diện** | diện tích thiết diện | **`construct_section`** | `8√3` |
| `d8` | cylinder | mặt phẳng **xiên** | **`refusal`** | `CURVED_SECTION_OUTSIDE_V1_CLOSURE` |

Bốn ca dùng bộ ba Pythagoras (15-20-25 · 9-12-15 · 7-24-25 · 8-15-17); `d7` trả
**Radical** `8√3`. Ràng buộc kiểm bằng test, không bằng lời hứa
(`test_corpus_co_du_Pythagoras_va_mot_ca_Radical`).

Runner gửi cho mô hình **đúng `problem_text`**; hai test quét AST-văn-bản của
runner để chứng minh không trường kỳ vọng nào lọt vào đường gửi
(`test_TIEM_9`, `test_TIEM_10`).

## 3. Gold preflight — mở lượt đo

```
GOLD_POSITIVE_CASES_SERVABLE = 7/7
GOLD_EXACT_RESULTS           = 7/7   (kể cả 8√3)
GOLD_SCENE3D                 = 7/7
GOLD_NEGATIVE_BOUNDARY       = PASS
RUNNER_INTEGRITY             = PASS  (31 test, 10 phép tiêm)
PRE_LIVE_GUARD               = OPEN
```

Gold dùng đúng primitive tổng quát, chạy qua đúng đường sản phẩm
(`normalize → static → grounding → coverage → interpreter → postconditions →
exact → Scene3D → servable`).

### 3b. Một lỗi hệ đã tìm ra TRONG preflight — đăng ký trước, không sửa

Preflight làm lộ một khiếm khuyết thật, **trước** mọi lượt gọi provider:

> **`CURVED_SCALAR_DECLARED_SOLID_CANNOT_BE_CUT`** — trụ/nón khai bằng `height`
> (vô hướng) thay vì `apex_or_top` (điểm có tên) **không cắt được**.
> `_giao_tron_xoay` đọc `s.truc` — vectơ trục, **bằng vectơ không** khi khai
> bằng chiều cao — thay vì `s.huong_truc`, đúng thuộc tính được thêm cho ca này
> và mang docstring *"hướng là thứ duy nhất mà mặt phẳng đáy và trục cần"*.

Tái lập qua **đúng đường sản phẩm**, chương trình grounded + hợp lệ tĩnh:

```
stage      = execution
error_code = semantic_program_invalid  |  capability_gap
details    = ['[ZeroDivisionError]', 'Fraction(1, 0)']
```

Phạm vi đo được, không suy đoán:

| khai | trụ/nón | cầu |
|---|---|---|
| `apex_or_top` (điểm) | OK | — |
| `height` (vô hướng) | **`ZeroDivisionError`** 4/4 tổ hợp | — |
| `radius` (vô hướng) | — | OK |
| `volume` · `lateral_area` | OK ở mọi cách khai | OK |

Ba hệ quả, không chỉ một: **phân loại sai** thành `capability_gap` trong khi
năng lực **có**; **tên ngoại lệ Python rò vào `details`**, tức lên bề mặt học
sinh; và **thông điệp gửi vào lượt sửa là vô nghĩa**, nên nó đầu độc luôn chiều
`REPAIR_CONVERGENCE` mà chính wave này đo.

Đây là lại đúng hình dạng lỗi mà cả loạt wave vừa rồi đuổi theo: Wave
`CURVED_CONSTRUCTION_GROUNDING_FOUNDATION` **thêm** `huong_truc`, và consumer
duy nhất cần nó **không bao giờ chuyển sang dùng**.

**Vì sao không chặn lượt đo.** §3 đặt điều kiện mở là gold chạy trọn; gold đạt
7/7 ở cả bốn chiều. §8 nhánh E vốn đã dự trù việc phát hiện lỗi hệ trong lượt
đo. Nên hazard được **đăng ký trước cùng luật quy kết của nó**
(`measurement_policy.json`, băm trong manifest) thay vì bị bỏ qua: nếu một ca
chết vì nó, ca ấy tính cho `SYSTEM` và **không** bị trừ ở chiều chọn toán tử.

**Và nó đã không xảy ra lần nào.** Mô hình khai khối bằng `apex_or_top` ở
**8/8** ca; `SCALAR_DECLARED_SOLID_CRASH = 0`. Hazard không nhiễm vào phép đo —
điều này chỉ khẳng định được vì luật đã đặt trước.

**Vì sao không sửa ở đây.** §9 giữ `backend/app` nguyên trạng. Sửa là wave riêng.

## 4. Ngân sách

Dẫn xuất từ 8 ca và giới hạn sản phẩm thật:

```
ANALYZE_CALLS_MAX             = 8      (1/ca, KHÔNG có vòng sửa)
INITIAL_SYNTHESIS_CALLS_MAX   = 8
REPAIR_CALLS_MAX              = 16     (MAX_SEMANTIC_PROGRAM_ATTEMPTS = 3)
LOGICAL_APPLICATION_CALL_BUDGET  = 32
PHYSICAL_API_ATTEMPT_BUDGET      = 128
```

Đã dùng: **26 lượt logic** (analyze 8 · tổng hợp 18), **26 lượt vật lý** —
không có retry vận chuyển nào. Trong ngân sách.

⚠️ **Bộ đếm của runner đếm THIẾU, telemetry sản phẩm là thẩm quyền.** Runner báo
21, telemetry báo 26. Nguyên nhân: `repair_count` suy từ sự kiện
`semantic_program_attempt`, mà sự kiện ấy **chỉ phát khi một lượt hỏng** — lượt
cuối thành công không phát gì. Đã sửa để đọc `telemetry.calls` và **giữ cả hai
số** trong artifact để lần sau còn đối chiếu (`test_TIEM_8b`). Con số trong báo
cáo này là con số telemetry.

## 5. Kết quả từng chiều

| ca | toán tử cuối | `circle3` | khai khối | stage | servable | sửa | quy kết |
|---|---|---|---|---|---|---|---|
| `d1` | *(không ra spec)* | — | `apex` | `semantic_program` | ✗ | 1 | MODEL |
| `d2` | `intersect_plane_curved` | ✓ | `apex` | `grounding` | ✗ | 2 | MODEL |
| `d3` | `intersect_plane_curved` | ✓ | `apex` | `structural_coverage` | ✗ | 2 | **xem §6** |
| `d4` | `intersect_plane_curved` | ✓ | `apex` | `structural_coverage` | ✗ | 1 | **xem §6** |
| `d5` | *(không ra spec)* | — | — | `semantic_program` | ✗ | 1 | MODEL |
| `d6` | `intersect_plane_curved` | ✓ | `ball` | `structural_coverage` | ✗ | 1 | **xem §6** |
| `d7` | `construct_section` | — | — | **`served`** | **✓** | 0 | — |
| `d8` | `construct_section` | — | `apex` | `grounding` | ✗ | 2 | MODEL |

Đọc theo cụm, chứ không theo từng ca:

```
① chọn construct_section cho khối cong   6/6 lượt đầu   → §6a
② tên container không phải định danh     3/6            → §6b
③ điểm phải-dựng-ra khai bằng toạ độ     2/6            → §6c
④ source_fact_id bịa hoặc thiếu          2/8            → §6d
```

## 6. Nguyên nhân — chỉ ghi `ROOT_CAUSE` khi đủ bằng chứng §7

### 6a. `ROOT_CAUSE` — `construct_section` là mặc định phổ quát

```
count 6 · denominator 6 ca cong · stage semantic_program (lượt đầu)
lặp lại: 6/6 ca, và 8/8 nếu tính cả ca đa diện lẫn ca âm
```

Không ca cong nào chọn đúng ở lượt đầu. Ca đối chứng `d7` chọn `construct_section`
và **đúng** — nên mô hình không "sai ngẫu nhiên", nó có **một** phép mặc định và
áp cho mọi bài thiết diện.

Đối chiếu với bề mặt gửi cho mô hình:

- thẻ văn phạm mô tả `construct_section` là *"dựng thiết diện"* — đúng chữ đề
  dùng; `intersect_plane_curved` đọc như một phép giao kỹ thuật;
- không chỗ nào trong `geometry_program_generator.md` nói **khối cong thì đi lối
  khác**;
- `intersect_plane_curved` là **biểu thức** (phải bọc trong `assign`), còn
  `construct_section` là **câu lệnh** — hai hình dạng cú pháp khác nhau cho hai
  phép cùng nghĩa với người đọc đề.

Đây là §8 **nhánh B**: `DOMINANT_FAILURE = STATEMENT_EXPR_OR_OPERATOR_AFFORDANCE`.

### 6b. `ROOT_CAUSE` — `analyze` phát tên container không phải định danh

```
count 3 · denominator 6 · stage structural_coverage (nổi lên), analyze (gốc)
ví dụ thô: container "(σ)" · "(δ)" · "(λ)"
```

Cả ba ca đi đúng toán tử, khai đúng `circle3`, dựng đúng chương trình — rồi bị
bác vì:

```
radius((σ)): container '(σ)' chưa khai báo
             (chương trình khai: [… 'sigma' …])
```

`analyze` lấy **nhãn trong ngoặc của đề** làm tên container; `synthesis` đặt tên
biến là `sigma`. Không gì buộc hai bên gặp nhau, và `analyze` chạy **trước**,
đóng băng hợp đồng khi chưa có chương trình nào tồn tại.

Quy kết là **MODEL**, và bằng chứng là chỉ dẫn mà nó tự vi phạm —
`app/ai/skills/geometry_analyze.md:38`:

> `container` là đối tượng bị hỏi tới, `witness` là tên thứ mang câu trả lời.
> Cả hai là **tên biến** snake_case, không dấu — không phải câu tiếng Việt.

`(σ)` không snake_case, có ngoặc, có ký tự Hy Lạp.

Nhưng có một **tình tiết hệ** thật, và phải ghi: luật ấy **không được cưỡng chế
ở đâu cả**. Không validator nào từ chối một container không phải định danh, nên
vi phạm nổi lên **hai stage sau**, dưới dạng `requested_operation_uncovered` —
một câu không nói gì về nguyên nhân. Và `stage_semantic_analyze` **không có vòng
sửa** (chỉ `stage_semantic_program` có), nên lỗi analyze là **không cứu được**
trong phạm vi một ca.

Cầu nối đã tồn tại nhưng không với tới: cả ba ca đều có `params.witness` trỏ một
biến **có khai và có sinh ra** (`ban_kinh_sigma`, `ban_kinh_delta`,
`ban_kinh_lambda`), và `coverage_gate._theo_witness_do` chính là bộ phân giải cho
việc ấy. Nó không chạy vì điều kiện hẹp **có chủ đích**:

> Container **vắng mặt** thì KHÔNG chạy — dù witness có đo đúng lượng đo trên
> một vật đúng kiểu.

Lý do của điều kiện ấy là `test_C1a`: hợp đồng đòi `volume(hinh_lang_tru)` mà
chương trình chỉ dựng `chop`; nối chúng là **chọn hộ**. Điều kiện ấy đúng cho ca
đó và chặn oan ca này. Phân biệt hai ca cần một tiêu chí chưa có — ghi
`HYPOTHESIS`, không ghi `ROOT_CAUSE` (§6e).

### 6c. Cụm đã biết — điểm phải-dựng-ra khai bằng toạ độ

```
count 2 · denominator 6 · stage grounding
d1: "P: được ĐỀ giới thiệu như một điểm phải dựng ra, nên không được khai bằng toạ độ"
d5: "Q: …" + "N: có initial_value nhưng thiếu source_fact_id"
```

Đúng nút thắt **CONSTRUCTION-GROUNDING** mà V3 đã đo. Nó **chưa đóng**, và wave
này xác nhận lại trên đề mới. Không phải phát hiện mới, nên không tính là
nguyên nhân trội của lượt này.

### 6d. Cụm — xuất xứ dữ kiện

```
count 2 · denominator 8 · stage grounding
d2: source_fact_id 'diem_e_truc_ef' không có trong RequestContract   (bịa)
d8: O1, O2: có initial_value nhưng thiếu source_fact_id              (thiếu)
```

### 6e. `HYPOTHESIS` — chưa đủ bằng chứng, ghi đúng như thế

- **`H1`** — lượt sửa đầu bị tiêu cho việc dạy toán tử, nên không còn lượt cho
  grounding. Khớp với `d1`/`d5` (`CS → IPC` rồi chết ở grounding), nhưng phân
  tách nó cần một lượt đo có thẻ đã sửa; chưa đo.
- **`H2`** — nới `_theo_witness_do` cho ca "container vắng mặt nhưng witness đo
  đúng lượng trên vật đúng kiểu" sẽ cứu 3/6 ca mà không nhận nhầm ca
  `hinh_lang_tru`/`chop`. Chưa có tiêu chí phân biệt được kiểm chứng.
- **`H3`** — tên `construct_section` là nguyên nhân của §6a chứ không phải sự
  vắng mặt của tín hiệu định tuyến. Hai giả thuyết này **chưa tách được** bằng
  lượt đo hiện tại: cả hai cùng dự đoán 0/6.

## 7. Ngưỡng đăng ký trước — đối chiếu

| ngưỡng | yêu cầu | đo được | đạt |
|---|---|---|---|
| STRONG | toán tử ≥ 5/6 · servable ≥ 5/6 · đối chứng 1/1 · biên 1/1 | 0/6 · 0/6 · 1/1 · 0/1 | ✗ |
| PARTIAL | toán tử 3–4/6 **hoặc** servable 3–4/6 | 0/6 · 0/6 | ✗ |
| WEAK | toán tử ≤ 2/6 **hoặc** servable ≤ 2/6 | **0/6 · 0/6** | ✓ |

```
CURVED_SECTION_MODEL_DISCOVERABILITY = WEAK
```

Phải nói rõ **WEAK về cái gì**: yếu ở **tự phát hiện**, không yếu ở **năng lực
dùng**. Sau một câu báo lỗi, 6/6 chuyển sang đúng toán tử và đúng kiểu kết quả.
Gộp hai điều ấy vào một chữ "WEAK" là làm mất đúng thông tin dùng được.

`STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED` — một development probe không thay
thế acceptance held-out.

## 8. Nhánh quyết định — §8 nhánh B

Điều kiện nhánh B là *"ít nhất hai ca curved cùng chọn `construct_section`"*.
Đo được **6/6**.

```
DOMINANT_FAILURE        = STATEMENT_EXPR_OR_OPERATOR_AFFORDANCE
RECOMMENDED_NEXT_ACTION = MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT
```

Wave hiện tại **chỉ ghi thiết kế dự kiến**; model-facing bytes giữ nguyên để
baseline còn giá trị. Thiết kế dự kiến, theo thứ tự bằng chứng ủng hộ:

1. **Nói ra luật định tuyến ở thẻ**: khối cong thì thiết diện ⊥ trục đi
   `intersect_plane_curved`, không đi `construct_section`. Đây là điều câu báo
   lỗi đang dạy 6/6 lần — dạy trước thì tiết kiệm đúng một lượt sửa mỗi ca.
2. **Cưỡng chế container là định danh ở biên hợp đồng analyze**, để §6b nổi lên
   ngay chỗ nó sinh ra thay vì hai stage sau. Lưu ý `stage_semantic_analyze`
   không có vòng sửa — nên hoặc thêm vòng, hoặc chuẩn hoá tại biên.
3. Chỉ sau khi (1) và (2) đóng mới đo lại; trước đó `H1` không tách được.

Nhánh **C** và **D** không kích hoạt: `WRONG_RESULT_TYPE_SECTION` chỉ xuất hiện
ở lượt **đầu** rồi tự khỏi sau sửa (4/4 ca ra spec đều khai `circle3`), và không
ca nào sai tỉ lệ — `d3`/`d4` chết trước khi tỉ lệ kịp có ảnh hưởng.

Nhánh **E** kích hoạt **một phần** và đã xử ở §3b: lỗi hệ có thật, tìm ra trong
preflight, đăng ký trước, và **không xảy ra** trong lượt đo.

## 9. Bảo toàn phạm vi

Không đổi: `backend/app` · analyze schema · synthesis schema · thẻ văn phạm ·
prompts · `CACHE_VERSION = 81` · candidate `d105f83e…` · năng lực sản phẩm
`foundation_only` · pool/seal/seed/artifact V3 · hợp đồng attachment vai trò
dựng · từ chối `radius(section)` · thiết diện xiên vẫn không hỗ trợ.

File mới đều là **bộ đo**, nằm ngoài `MEASURED_SYSTEM_PATHS`:
`backend/scripts/gold_section_discoverability.py` ·
`backend/scripts/run_section_discoverability_probe.py` ·
`backend/tests/test_section_discoverability_probe.py` ·
`docs/evaluation/geometry/curved-section-discoverability-dev-v1/`.

⚠️ **`RUNNER_HASH` delta giữa hai lượt — khai đầy đủ.** Ca `d1` chạy ở lượt
`151639Z`; `d2`–`d8` ở lượt `151813Z`. Giữa hai lượt runner đổi **đúng một
chỗ**: bộ đếm lượt vật lý vá `pipeline.call_gemini` thay vì chỉ
`gemini.call_gemini` (`pipeline` giữ tham chiếu đã bind lúc import, nên bộ đếm
cũ nằm ngoài đường chạy và luôn báo 0). Thay đổi **chỉ chạm quan trắc**, không
chạm nội dung gửi cho model, không chạm scorer. Manifest của cả hai lượt đều đã
ghi trước lượt gọi đầu tiên; môi trường, corpus và expected byte-identical giữa
hai lượt.

## 10. Gates

| | |
|---|---|
| `tests/test_section_discoverability_probe.py` (MỚI) | **31 passed** · 10 phép tiêm + 2 test khoá lỗi §3b |
| gold preflight | 7/7 · exact 7/7 · Scene3D 7/7 · biên PASS |
| `tests/geometry/test_curved_section_radius_path.py` | 32 passed |
| curved foundation · obligation surface · distance witness · post-model path | passed (trong full suite) |
| full backend pytest | **3738 passed** · 1 skipped · 1 deselected, exit 0 (cây sạch) |
| frontend vitest | **698 passed** / 51 file |
| cache identity | passed · `CACHE_VERSION` 81 → 81 |
| candidate verification | exit **0** — `d105f83e…` **không đổi** |
| `certify_acceptance_runner.py` | exit **0** · 4 nhãn PASS · 2 readiness YES |
| `replay_demo_cases.py` · `audit_demo_crash_surface.py` | 5/5 · 6/6 · ném ra ngoài 0 |
| `git diff --check` · `git status --porcelain` | exit 0 · sạch |

## 11. Giới hạn

**①** `n = 6` ca cong. Kết quả 0/6 và 6/6 đều **rất sắc** nhưng mẫu nhỏ; nó đủ
để chỉ hướng cho wave sau, **không** đủ để làm một con số khoá luận.

**②** Corpus do tôi viết và nay đã công bố ⇒ **không held-out**. Mọi tuyên bố
`supported` vẫn thuộc V4.

**③** Mọi đề trong corpus **đặt tên** cho các điểm cần thiết để dựng khối — cố
ý, để cô lập biến "chọn toán tử". Nên probe này **không** đo lại nút thắt
construction-grounding; nó vẫn mở (§6c).

**④** Model gọi bằng **alias** `gemini-2.5-flash`, tái lập ở mức `LIMITED`.
Ghi đủ alias, thời điểm UTC, tham số gửi và raw output; **không** tuyên bố tái
lập bit-for-bit.

**⑤** `d8` chưa bao giờ chạm bao đóng v1 — nó chết ở grounding vì cùng lỗi §6a
(3/3 attempt giữ `construct_section`). Nên `BOUNDARY_DISCOVERABILITY` là
`NOT_MEASURED`, không phải `FAIL`.

**⑥** Một lỗi hệ (§3b) đã biết mà **chưa sửa**. Nó không nhiễm lượt đo này, và
điều đó khẳng định được vì luật quy kết đặt trước — nhưng nó vẫn nằm đó cho bất
kỳ đề nào không đặt tên hai đầu trục.

## 12. Khối kết quả

```
MEASUREMENT_CLASS = DEVELOPMENT_DIAGNOSTIC
PRE_LIVE_GUARD = OPEN
CORPUS_HASH = 54264bd57e2b32829a2a72916cbbf03ba3b2f3b75d4271cda0e496e85eff4e83
EXPECTED_RESULTS_HASH = 9c964f8c95e1f7cadb9c3d84df8c0dac5c40866f9e71c8f1ab0bf8fdadd4b761
RUN_ID = dev-v1-20260905T151639Z (d1) + dev-v1-20260905T151813Z (d2–d8)
MODEL_IDENTITY = google-generativelanguage-v1beta · gemini-2.5-flash · snapshot TRỐNG (alias)
APPLICATION_LLM_CALL_BUDGET = 32 logic / 128 vật lý
APPLICATION_LLM_CALLS_USED = 26 logic / 26 vật lý   (telemetry sản phẩm)
ANALYZE_CALLS = 8
SYNTHESIS_CALLS = 18   (8 lượt đầu + 10 lượt sửa)
REPAIR_CALLS = 10
TOTAL_INPUT_TOKENS = 70083
TOTAL_OUTPUT_TOKENS = 24332
TOTAL_THOUGHT_TOKENS = 56439

GOLD_POSITIVE_CASES_SERVABLE = 7/7
CURVED_POSITIVE_CASES = 6
POLYHEDRAL_CONTROL_CASES = 1
NEGATIVE_BOUNDARY_CASES = 1

ANALYZE_CONTRACT_CORRECT = 8/8        (hợp đồng sinh ra ở mọi ca)
OBLIGATIONS_COMPLETE = 8/8
OPERATOR_CLASS_CORRECT (lượt đầu) = 0/6
OPERATOR_CLASS_CORRECT (bất kỳ lượt nào) = 6/6
ASSIGN_WRAPPER_CORRECT = 4/4          (trong các ca có spec cuối)
CIRCLE3_RESULT_TYPE_CORRECT = 4/4     (trong các ca có spec cuối)
RATIO_CONSTRUCTION_CORRECT = NOT_REACHED
FIRST_ATTEMPT_SERVABLE = 1/8          (chỉ d7, ca đa diện)
EVENTUAL_SERVABLE = 0/6 cong · 1/1 đa diện
EXACT_ANSWER_MATCH = 0/6 cong · 1/1 đa diện (8√3)
SCENE3D_PASS = 1/1 trong các ca servable
POLYHEDRAL_CONTROL_PASS = YES
NEGATIVE_BOUNDARY_PASS = NO  (không chạm tới biên — xem giới hạn ⑤)

SELECTED_CONSTRUCT_SECTION_FOR_CURVED = 6/6 lượt đầu · 8/8 nếu tính cả ca
INTERSECT_USED_AS_STATEMENT = 0
WRONG_RESULT_TYPE_SECTION = 6/6 lượt đầu → 0/4 sau sửa
INVENTED_POINT = 2   (d1 P · d5 Q)
GROUNDING_FAILURE = 4   (d1, d2, d5, d8)
COVERAGE_FAILURE = 3    (d3, d4, d6)
RUNTIME_FAILURE = 0
MODEL_FAILURE_COUNT = 7
SYSTEM_FAILURE_COUNT = 0     (hazard đã đăng ký KHÔNG kích hoạt)
ATTRIBUTION_UNRESOLVED_COUNT = 0
SCALAR_DECLARED_SOLID_CRASH = 0

CURVED_SECTION_MODEL_DISCOVERABILITY = WEAK
  ├ tự phát hiện       = 0/6
  └ dùng được sau sửa  = 6/6
STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
DOMINANT_FAILURE = STATEMENT_EXPR_OR_OPERATOR_AFFORDANCE
ROOT_CAUSE = ① construct_section là mặc định phổ quát (6/6)
             ② analyze phát container không phải định danh (3/6)
HYPOTHESES_REMAINING = H1 lượt sửa bị tiêu cho toán tử
                       H2 nới _theo_witness_do khi container vắng mặt
                       H3 tên gọi vs thiếu tín hiệu định tuyến — chưa tách được

SYSTEM_DEFECT_FOUND_IN_PREFLIGHT = CURVED_SCALAR_DECLARED_SOLID_CANNOT_BE_CUT
SYSTEM_DEFECT_FIXED = NO   (ngoài charter §9)

PRODUCT_CODE_CHANGED = NO
MODEL_FACING_CONTRACT_CHANGED = NO
CACHE_VERSION_BEFORE/AFTER = 81/81
CANDIDATE_HASH_BEFORE/AFTER = d105f83e5f7de0cc… / d105f83e5f7de0cc…
V3_REEXECUTED = NO
V3_ARTIFACTS_CHANGED = NO
V4_CREATED = NO
PRODUCT_CAPABILITY_CHANGED = NO
WORKING_TREE = CLEAN
COMMITS = 1
RECOMMENDED_NEXT_ACTION = MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT
```

Kết luận của wave chỉ trả lời khả năng mô hình **tự phát hiện và sử dụng** đường
thiết diện tròn đã tồn tại. Tuyên bố ổn định và nâng `supported` thuộc phép đo
held-out V4, sau khi mọi failure cluster đã được xử lý.
