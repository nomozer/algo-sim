# POINT_INITIALIZATION_CONTRACT_ALIGNMENT

> 2026-09-06. **`APPLICATION_LLM_CALLS = 0`** · `PRODUCT_CAPABILITY_CHANGED = NO`
> · `CACHE_VERSION = 81` (không bump) · `HISTORICAL_ARTIFACTS_CHANGED = NO`.

## 1. Điểm xuất phát

Mốc bàn giao **khớp hoàn toàn** với đo lại:

```
HEAD = 9fef0a7 · WORKING_TREE = CLEAN
CANDIDATE_HASH = 67ad7f4ffb1a97ee…  (89 file, verify exit 0)
CACHE_VERSION  = 81
BACKEND        = 3821 passed · 1 skipped · 1 deselected
```

Không khác biệt nào so với bàn giao.

## 2. `ROOT_CAUSE` — đã chứng minh

IR có **hai** ô chở toạ độ một điểm gốc, ở hai chỗ khác nhau:

```
memory_declarations[].initial_value    — KHAI BÁO
statements[declare_point].at           — CÂU LỆNH
```

Trong A/B `ab-v1-20260905T164514Z`, hai ca `e2` và `e6` gửi ô của **câu lệnh**
đặt trong **khai báo**:

```json
{"name": "X", "type": "point3", "at": [0, 0, 0]}
```

`MemoryDeclaration` không khai `model_config`, nên Pydantic dùng mặc định
`extra="ignore"` và **`at` biến mất không dấu vết**. Sau chuẩn hoá:

```json
{"name": "X", "type": "point3", "initial_value": null, "source_fact_id": null}
```

Lời từ chối cuối cùng mô hình nhận được:

```
#1 IR_USE_BEFORE_CONSTRUCTION: 'X' — cần point3, có khai báo nhưng chưa có giá trị
```

**Đúng sự thật, sai chỗ.** Mô hình ĐÃ cho toạ độ; nó chỉ để nhầm ô, và không
có cách nào biết. Một lượt sửa dưới câu ấy sẽ đi tìm một câu lệnh dựng cho một
điểm GỐC — thứ không tồn tại.

Nối đủ ba mắt cho từng ca: raw candidate → bước xử lý → lỗi quan sát được.

| ca | raw | bước xử lý | lỗi |
|---|---|---|---|
| `e2`/B | `X`,`Y`,`Z` mang `at` | `extra="ignore"` bỏ `at` | `IR_USE_BEFORE_CONSTRUCTION` ×3 |
| `e6`/B | `D`,`C` mang `at` | như trên | `IR_USE_BEFORE_CONSTRUCTION` ×2 |

### Bốn nguyên nhân, phân biệt rõ

| ca | tầng | nguyên nhân | thuộc wave này? |
|---|---|---|---|
| `e2`, `e6` | schema (im lặng) → `ir_static` | **nhầm ô khai báo** | **CÓ** |
| `e7` | `grounding` | `declare_point.at` hợp lệ nhưng thiếu `source_fact_id` | không — xuất xứ |
| `e4` | `structural_coverage` | container `(t)` không phải định danh | không — liên kết tên |
| `e8` | `semantic_program` | `A₁` (chỉ số dưới) ↔ `A1` (ASCII) | không — hợp đồng tên |

`e7`/`e4`/`e8` giữ vai **đối chứng**: chúng chứng minh chẩn đoán mới không nuốt
mất các tầng khác.

⚠️ **`e8` — quy trách nhiệm.** Đề (do tôi viết ở wave trước) dùng `A₁`/`A₂`
Unicode; mô hình khai `A1`/`A2` ASCII; `la_ten_nguon` không khớp. Hợp đồng tên
hiện hành so **chuỗi**, không chuẩn hoá chỉ số dưới. Trách nhiệm chia: corpus
đưa vào một ký hiệu mà hợp đồng không hứa xử lý, và hợp đồng không nói ra điều
đó. Không phải lỗi chọn ô, nên nằm ngoài wave này.

## 3. Delta tối thiểu — replay qua đúng đường sản phẩm

Artifact: [`point-initialization-replay-v1/replay.json`](evaluation/geometry/point-initialization-replay-v1/replay.json).
Artifact gốc của mô hình **không bị đụng**.

### `E2_REPLAY`

| bản | tầng đạt | lỗi còn lại | exact | postconditions | servable | scene3d |
|---|---|---|---|---|---|---|
| gốc | `validator` | `memory_declarations[0].at` … | NOT_REACHED | NOT_REACHED | ✗ | — |
| `at`→`initial_value` | `grounding` | `X: có initial_value nhưng thiếu source_fact_id` | NOT_REACHED | NOT_REACHED | ✗ | — |
| + xuất xứ cho `X` | **`served`** | — | **`121π` PASS** | PASS | **✓** | 12 |

### `E6_REPLAY`

| bản | tầng đạt | lỗi còn lại | exact | postconditions | servable | scene3d |
|---|---|---|---|---|---|---|
| gốc | `validator` | `memory_declarations[0].at` … | NOT_REACHED | NOT_REACHED | ✗ | — |
| `at`→`initial_value` | **`served`** | — | **`400π` PASS** | PASS | **✓** | 8 |
| + xuất xứ | `served` | — | PASS | PASS | ✓ | 8 |

**`e6`: nhầm ô là TOÀN BỘ rào cản** — một delta, không cần gì thêm.
**`e2`: nhầm ô mở tới `grounding`**, và cổng kế tiếp bác vì `X` không có xuất
xứ. Ghi riêng, không gộp.

⚠️ **Một sai lầm của tôi, ghi lại vì nó suýt thành kết luận.** Bản đầu của
`delta_2` dò tự động *"mục nào có tên điểm trong nhãn"*. Với `X` nó chọn
`z_tren_day_x` — nhãn *"Điểm **Z** nằm trên đường tròn đáy tâm **X**"* — một
mục nói về **Z**. Kết quả `served` **đúng vì lý do sai**. Đã thay bằng bảng quy
kết tường minh kèm căn cứ: `tru_co_tru_xy` (*"Hình trụ có trục là đoạn thẳng
XY"*) là mục **giới thiệu X**, và toạ độ `(0,0,0)` là lựa chọn hệ quy chiếu nên
đi kèm `model_assumption` — đúng khuôn chính mô hình đã dùng cho `Y` và `Z`.
`test_R4` khoá cả hai vế: phải chọn mục giới thiệu, **không** được chọn mục kia.

## 4. Bản sửa

Một chỗ: [`validator.py`](../backend/app/simulation/semantic_program/validator.py)
— `validate_semantic_program`, **trước** `model_validate`, tức biên **cuối cùng
còn giữ đầu vào thô**.

```python
if (lac := _khoa_bi_bo_im_lang(raw_spec)):
    return ValidationResult(False, f"Lỗi cú pháp schema …: {lac}")
```

Chẩn đoán nêu đủ ba thứ §3 đòi:

```
memory_declarations[0].at: khoá này không có trong `memory_declarations[]`
  — `at` là trường của `declare_point`, chuyển giá trị ấy sang `initial_value`.
  Trường hợp lệ: element_type, initial_value, key_type, model_assumption,
  name, source_fact_id, type, val_type
```

### Mọi thứ dẫn xuất, không chép tay

| thông tin | nguồn |
|---|---|
| ô giá trị chính tắc (`initial_value`) | `_o_gia_tri_tho` — trường duy nhất khai `Any` |
| chủ sở hữu (`declare_point`) | `_chu_so_huu_truong` — quét model của `contract` |
| "là ô giá trị thô?" | `_la_o_gia_tri` — annotation là `Any` / `list[Any]` |
| trường hợp lệ | `MemoryDeclaration.model_fields` |

### Vì sao TỪ CHỐI, không quy đổi

Kho có tiền lệ quy đổi (`canonical_geometry_name`) cho ca **1:1 về tham
chiếu**. Ca này khác, và chính `DeclarePointStmt` đã chốt:

> *"Cách rẻ là: thấy `construct_point` mang toạ độ thì lặng lẽ coi như khai
> báo. KHÔNG làm, vì phép ánh xạ ấy không bảo toàn xuất xứ."*

Tự chuyển ô là **chọn hộ** giữa hai cách biểu đạt có hai đường xuất xứ khác
nhau. Nên: từ chối, và nói đủ để sửa. Khi có **cả hai** `at` và `initial_value`,
lời từ chối nói rõ ô nào chính tắc và yêu cầu bỏ ô kia — vẫn không chọn hộ giá
trị nào thắng (`test_C3`).

### Ranh giới hẹp có chủ đích — và nó được đo, không được đoán

Bản đầu bác **mọi** khoá lạ. Replay corpus lịch sử bác lại: chương trình AI
sinh trong `gm_03`, `gm_10` và corpus transport đặt `label` trong khai báo, và
**3/5 chương trình bị chặn oan**.

`label` là `Optional[str]` — chuỗi trang trí, bỏ đi không mất gì. `at` là
`list[Any]` — ô giá trị thô, bỏ đi là mất toạ độ. Luật thu hẹp theo đúng phân
biệt ấy, chỉ báo khi **có dữ liệu bị mất**:

- khoá là **ô giá trị thô** ở model sở hữu nó → báo (kể cả khi khai báo đã có
  `initial_value`, vì khi ấy có hai lời khai giá trị cho một vật);
- khoá **không ai sở hữu**, mang giá trị, và khai báo đang **không có** giá trị
  nào → báo (khoá bịa đã nuốt dữ kiện);
- còn lại → bỏ qua như trước.

`REPAIR_DIAGNOSTIC_DELIVERED`: `val.error` đi thẳng vào `_prompt_sua` — cùng
đường mà lỗi schema vẫn đi. `test_D1` chứng minh chẩn đoán nằm trong prompt của
lượt kế tiếp; `test_D2` chứng minh vòng sửa **khép được** (lượt 2 gửi bản đã
chuyển ô ⇒ `served`, `400π`).

## 5. Xuất xứ không bị nới — và ranh giới thật của nó

`POINT_PROVENANCE_GUARDS_PRESERVED = YES`. Bốn phản ví dụ giữ nguyên hành vi:
thiếu `source_fact_id` · mục không tồn tại · điểm không xuất xứ · điểm dẫn xuất
hợp lệ vẫn dựng và đo được (`d = 3`).

⚠️ **Hai test của tôi có tiền đề sai, và tôi ghi lại vì chúng suýt thành lời
tuyên bố sai:**

- `test_P3` bản đầu khẳng định *"điểm tự bịa bị bác"* bằng một điểm trỏ tới một
  mục **có thật**, và nó **được phục vụ**. Đo lại bằng máy cho ra luật thật:

  | khai | kết quả |
  |---|---|
  | không `source_fact_id` | **bác** |
  | mục mang TÊN (`["A","B"]`), toạ độ `[5,0,0]` | **phục vụ** — mục ấy không nói điểm ở đâu |
  | mục mang SỐ (`[6]`), toạ độ `[5,0,0]` | **bác** — giá trị bị đối chiếu thật |
  | mục mang SỐ, toạ độ `[0,0,0]` | **phục vụ** — gốc toạ độ không đóng góp thành phần nào |

- `test_P3b` bản đầu dùng `[0,0,0]`, tức đúng ca **miễn** đối chiếu, nên nó
  xanh vì lý do sai. Đã đổi sang toạ độ khác 0.

Cả hai hành vi **có từ trước wave** và không đổi: bản vá chỉ bác khoá lạ, mà
các khai báo ấy không có khoá lạ nào (`test_TIEM_4`).

## 6. Đính chính quyết định A/B

Luật đăng ký của `MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT` liệt **sáu**
điều kiện giữ B. Năm đạt. Điều kiện *"B trả đúng ranh giới ở ca âm"* **không
đạt** — `e8` không arm nào chạm tới bao đóng v1.

Báo cáo wave ấy ghi điều kiện này là "ghi riêng" và vẫn kết luận
`CHANGE_ACCEPTED = YES`. **Đó là đọc sai luật của chính nó**: luật nói rõ *"khi
chưa đạt, lưu B và kết quả như một ứng viên thử nghiệm, đưa phần sản phẩm của
wave về A"*.

Đã thực hiện nhánh ấy:

| | |
|---|---|
| lợi ích của B | **giữ nguyên kết luận** — 1/6 → 6/6, thắng 5 thua 0 |
| `registration.json`, `manifest`, `ab_*.json` | **byte-identical**, không sửa |
| thẻ sản phẩm | **về A**, khớp byte `card_A.txt` (`c7c001c4…`, 5472 B) |
| ứng viên B | đóng băng thành `card_B.txt` (`86134034…`, 5675 B) |
| runner A/B | hai arm nay đọc **cả hai** thẻ từ artifact ⇒ tái lập được bất kể sản phẩm chọn biến thể nào |
| trần byte thẻ | về **5510**; `test_card_result_type_affordance.py` gỡ |

Phục hồi **giới hạn đúng vào thay đổi của wave A/B**: `grammar_card.py` và
`test_grammar_card.py` checkout từ `93de148`. Bằng chứng khớp: `grammar_card`
hash trở lại `e0fbbc8456da57ae…` và `semantic_environment_hash` trở lại
`f7def6207f5741d9…` — đúng giá trị tiền-A/B.

`test_AB1`/`test_AB2` khoá kết quả này để không ai âm thầm nhận lại B.

**Quy kết**: lợi ích thuộc **toàn bộ gói B**. Đóng góp riêng của nhãn kiểu kết
quả (`→circle3`) và của danh sách `MemoryType` **vẫn chưa xác định** — confound
đã khai trước lượt đo và không có phép đo nào tách chúng.

## 7. Cache

`CACHE_DECISION = KHÔNG BUMP` · `CACHE_VERSION 81 → 81`.

Kiểm bằng **mã hiện tại**, không bằng suy luận:

- `_cache_key(text)` băm **văn bản đã chuẩn hoá**; version nằm ở **cột**.
- `_cache_lookup` miss khi `row.policy_version != CACHE_VERSION`.
- `test_CA1` dựng một **row baseline thật** (`policy_version = 81`, envelope
  `ok`) rồi gọi `_cache_lookup` **sau** bản vá: vẫn **hit**.
- `test_CA2` phân biệt hai thứ dễ lẫn: `semantic_environment_hash` nhận diện
  **bản đo**, còn cache sản phẩm so **`policy_version`**. Wave này không đụng
  cái nào — bản vá nằm ở validator (tầng engine), và thẻ đã về A.

Không envelope `ok` nào có thể sinh ra từ chương trình mà wave này bắt đầu bác:
một khai báo `point3` nuốt mất toạ độ luôn chết ở `ir_static`, mà `main.py` chỉ
cache khi `status == "ok"`.

## 8. Gates

| | mới chạy / kế thừa |
|---|---|
| `test_point_initialization_contract.py` (MỚI) — 30 passed, 4 phép tiêm | **mới chạy** |
| `test_runner_affordance_ab.py` — 18 passed (sửa: hai arm đọc artifact) | **mới chạy** |
| `test_grammar_card.py` — 11 passed (trần về 5510) | **mới chạy** |
| corpus lịch sử: `test_capability_honesty` · `test_transport_boundary` | **mới chạy** — xanh sau khi thu hẹp luật |
| full backend pytest — **3833 passed** · 1 skipped · 1 deselected | **mới chạy** (cây sạch) |
| `gold_affordance_ab.py` — 7/7 · exact 7/7 · Scene3D 7/7 · biên PASS | **mới chạy** |
| cache identity · candidate verification | **mới chạy** |
| `certify_acceptance_runner.py` — exit 0, 4 nhãn PASS, 2 readiness YES | **mới chạy** |
| `replay_demo_cases.py` 5/5 · `audit_demo_crash_surface.py` 6/6 · 0 | **mới chạy** |
| `git diff --check` exit 0 | **mới chạy** |
| frontend vitest **698/51** | **KẾ THỪA** từ 2026-09-05 — không file `frontend/**` nào đổi trong wave này, và hợp đồng cảnh (`RENDER_HINT`, `_TRUONG`) không đụng tới |

## 9. Giới hạn và giả thuyết còn mở

**①** Wave này chỉ đóng **nhầm ô khai báo**. `e4` (liên kết tên), `e7`/`e8`
(xuất xứ và hợp đồng tên) vẫn mở, và được ghi đúng tầng ở §2.

**②** `MODEL_DISCOVERABILITY = NOT_MEASURED` — 0 lượt gọi model. Replay chứng
minh **năng lực hệ**: chương trình sửa đúng ô thì đi trọn. Việc mô hình có tự
sửa được sau khi nhận chẩn đoán hay không là một phép đo khác, chưa làm.

**③** `HYPOTHESIS`: chẩn đoán mới sẽ cắt được lượt sửa đầu ở lớp bài này. Chưa
đo — cần một lượt live, và đó là việc riêng.

**④** Ranh giới "khoá không ai sở hữu + khai báo rỗng" bảo thủ có chủ đích: một
khoá bịa mang giá trị **trong khai báo đã có giá trị** vẫn im lặng. Chọn thế để
không lặp lại lần bác oan 3/5 ở §4.

**⑤** `e2`/`e6` là raw candidate sinh dưới **thẻ B**. Nhầm ô `at`/`initial_value`
không phụ thuộc thẻ — cả A lẫn B trình bày hai ô ấy giống hệt nhau — nên fixture
vẫn hợp lệ sau khi sản phẩm về A.

## 10. Khối kết quả

```
POINT_INITIALIZATION_CONTRACT_ALIGNED = YES
RAW_FIELD_MISMATCH_DIAGNOSED = YES — đường dẫn JSON · trường đã gửi ·
    chủ sở hữu · ô chính tắc, tất cả dẫn xuất từ model
REPAIR_DIAGNOSTIC_DELIVERED = YES — `val.error` → `_prompt_sua`; test_D1 chứng
    minh có mặt trong prompt lượt kế, test_D2 chứng minh vòng sửa khép được
POINT_PROVENANCE_GUARDS_PRESERVED = YES (4 phản ví dụ; ranh giới thật đo lại
    và khoá ở test_P3 / test_P3b)

E2_REPLAY = gốc `validator` → +ô `grounding` → +xuất xứ `served`, 121π, scene 12
E6_REPLAY = gốc `validator` → +ô `served`, 400π, scene 8   (một delta là đủ)

A_B_ADOPTION_STATUS = ĐÍNH CHÍNH — điều kiện ca âm KHÔNG đạt ⇒ nhánh đăng ký
    "chưa đạt" được thực hiện; SELECTOR_GAIN_OBSERVED = YES giữ nguyên
PRODUCT_VARIANT = A  (thẻ khớp byte `card_A.txt`, grammar_card e0fbbc84…)
CACHE_DECISION = KHÔNG BUMP — `_cache_lookup` so `policy_version`; row baseline
    vẫn hit sau bản vá (test_CA1); băm danh tính ≠ trường cache so (test_CA2)
CANDIDATE_BEFORE_AFTER = 67ad7f4ffb1a97ee… / 4f813a3842019d54…
APPLICATION_LLM_CALLS = 0
MODEL_DISCOVERABILITY = NOT_MEASURED
STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
PRODUCT_CAPABILITY_CHANGED = NO   (ball/cylinder/cone giữ foundation_only)
HISTORICAL_ARTIFACTS_CHANGED = NO
TEST_RESULTS = mục tiêu 30 · full backend 3833 passed · vitest 698/51 (kế thừa)
WORKING_TREE = CLEAN
COMMITS = 2
RECOMMENDED_NEXT_ACTION = OBLIGATION_CONTAINER_NAME_BINDING
```

## 11. Việc kế tiếp

Chọn theo lỗi còn lại có bằng chứng **mạnh nhất**, đếm qua hai lượt đo độc lập:

```
container không phải định danh   dev-v1 3/6  +  ab-v1 e4      = 4 ca
xuất xứ điểm (thiếu / không khớp) ab-v1 e7, e8                = 2 ca
```

`analyze` phát `container` là nhãn trong ngoặc của đề — `(σ)`, `(δ)`, `(λ)`,
`(t)` — trái chính chỉ dẫn của nó (`geometry_analyze.md:38`: *"tên biến
snake_case, không dấu"*), và luật ấy **không được cưỡng chế ở đâu cả**, nên vi
phạm nổi lên hai stage sau dưới dạng `requested_operation_uncovered`. Thêm nữa
`stage_semantic_analyze` **không có vòng sửa**, nên lỗi ấy không cứu được trong
phạm vi một ca.

Đó đúng hình dạng mà wave này vừa xử ở một tầng khác: **một luật được nói ở
prompt mà không có ai cưỡng chế, rồi nổi lên sai chỗ**.

```
RECOMMENDED_NEXT_ACTION = OBLIGATION_CONTAINER_NAME_BINDING
```
