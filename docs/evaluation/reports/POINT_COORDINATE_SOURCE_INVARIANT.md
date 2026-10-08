# POINT_COORDINATE_SOURCE_INVARIANT

> 2026-09-08 · `APPLICATION_LLM_CALLS = 0`
>
> ```
> ROOT_CAUSE = SOURCE_FACT_CONTENT_UNCHECKED
>   SOURCE_FACT_EXISTENCE_CHECKED            = YES
>   SOURCE_FACT_CONTENT_MATCHED              = NO
>   POINT_COORDINATE_SOURCE_INVARIANT_EXISTS = NO   (trước wave)
>
> CURRENT_CONTRACT_CAN_EXPRESS_POINT_COORDINATE = YES
> SELECTED_BRANCH            = A     (hợp đồng hiện tại đủ)
> NEW_SOURCE_INVARIANT_KINDS = 2     point_coordinate · *_unresolved
> NEW_IR_OPERATIONS = 0 · NEW_MEMORY_TYPES = 0 · NEW_PER_PROBLEM_MODULES = 0
>
> CACHE_DECISION = BUMP 92 → 93      (chứng minh bằng ROW THẬT)
> MODEL_FACING_CONTRACT_CHANGED = NO (sáu băm đứng yên TỪNG BYTE)
> ```
>
> Đề cho `B(6,0,0)`; chương trình khai `B(99,7,0)`; `source_fact_id` trỏ một
> fact **có thật**; hệ phục vụ `V = 540`. Wave này đóng lỗ ấy — và trên đường
> đi, chính bộ đo của nó vấp đúng cái bẫy mà kho gọi tên.

## 1. Chẩn — và điều đã BỊ BÁC trước khi triển khai

`NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY` để lại giả thuyết: *"analyze
không trích toạ độ vào fact nên grounding không có gì đối chiếu"*. Wave này
đo lại **một biến**, và giả thuyết ấy **sai**:

| Hợp đồng | Chương trình | Trước vá |
|---|---|---|
| fact **kể chuyện** (ba fact, không toạ độ) | toạ độ đúng | `served` · `45` |
| fact **kể chuyện** | `B → (99,7,0)` | `served` · **`540`** |
| fact **CÓ toạ độ** (mỗi điểm một fact) | toạ độ đúng | `served` · `45` |
| fact **CÓ toạ độ** | `B → (99,7,0)` | `served` · **`540`** |

Ba ca tái hiện thêm, cũng `served` trước vá:

```
D(3,1,0) → D(3,3,0)        served · V = 63   ← mất phần lõm
source_fact_id trỏ NHẦM    served · V = 540  ← fact có thật, sai nội dung
model_assumption che       served · V = 540  ← kênh tự do hệ trục
```

`ROOT_CAUSE = SOURCE_FACT_CONTENT_UNCHECKED`: `source_fact_id` được kiểm **sự
tồn tại**, không kiểm **sự khớp**. Kho có bất biến nguồn cho `segment_length` ·
`segment_division` · `plane_equation` · thang đo — **không có** cái nào cho toạ
độ điểm. Vì thế bản vá đặt ở **bất biến nguồn**, không ở grounding.

## 2. Nhánh A — hợp đồng hiện tại đã đủ

`SourceInvariant` có sẵn `points` và `coefficients: tuple[str, ...]`. Một toạ
độ điểm là `points=("B",)` + `coefficients=("6","0","0")`. **Không nới hợp
đồng, không thêm trường, không thêm kiểu.**

```
NEW_IR_OPERATIONS = 0   NEW_MEMORY_TYPES = 0   NEW_PER_PROBLEM_MODULES = 0
```

`point_coordinate.py` là **peer** của `plane_equation.py` và
`segment_relation.py` — một module theo *dạng dữ kiện*, không theo *bài*.

## 3. Bộ phát — đọc từ `problem_text`, không đọc từ fact

Cùng lý do `check_source_invariants` đã ghi: đọc từ fact là tin vào thứ
`analyze` chọn trích. Lượt live của wave trước trích ba fact kể chuyện, không
fact nào mang toạ độ — bộ phát phụ thuộc fact sẽ im lặng đúng lúc cần nhất.

**Ngưỡng đọc đã chứng minh** (`test_01`):

```
A(1,2,3) · A = (1, 2, 3) · A(1; 2; 3) · số âm · phân số · thập phân dấu CHẤM
nhiều điểm một câu · A1 · A_1 · A₁ · A'
```

**Không bắt nhầm** (`test_02`): phương trình mặt phẳng · vectơ không gắn tên ·
`n(1,2,3)` · `AB(1,2,3)` · độ dài · tỉ lệ · nhãn hình `S.ABCDE` · `(P)` · `(E)`.

Hai verdict, không phải một:

* đọc trọn, một giá trị → `point_coordinate`;
* cùng một tên, **hai bộ ba khác nhau** → `point_coordinate_unresolved`, và
  cổng **chặn**. Hệ không biết đề muốn điểm nào.
* cú pháp ngoài ngưỡng → **im lặng**, không chặn.

Chiều fail khác nhau là có chủ đích: fail-OPEN ở *"không đọc được"* (chặn nó là
chặn oan cả một lớp đề), fail-CLOSED ở *"đọc được mà mâu thuẫn"*.

## 4. Checker — hỏi trên TRẠNG THÁI CUỐI

Thêm một nhánh dispatch vào `check_source_invariants`. So từng thành phần bằng
`Fraction`, không dung sai. Điểm vắng ⇒ `not_checkable`, **không** phải
`violated` (*"đáng lẽ phải dựng"* là câu của cổng phủ).

Vì nó hỏi trên trạng thái cuối chứ không đọc `memory_declarations`, **mọi
đường biểu diễn chịu chung một luật**: khai thẳng · qua bí danh · dựng bằng một
phép — điểm nằm sai chỗ thì trượt, dùng lối nào cũng thế.

### 4b. `_diem` có nấc ③ — và nó dùng THẨM QUYỀN ĐÃ CÓ

Đo được ở ca elip: đề viết `O'(0,0,20)`, chương trình đặt biến `Oprime`, lưới
hoà giải C₁a không nối hai tên ấy ⇒ bất biến rơi vào `not_checkable` dù mọi thứ
cần để phán đều có mặt. Cổng **im lặng đúng lúc cần nói**.

Nấc ③ dùng `source_entities.chuan_hoa_ten` — thẩm quyền đã sở hữu đúng tri
thức ấy (`A_prime` → `A'`, `point_A` → `A`, `A_1` → `A1`). **Không** viết lưới
chính tả thứ chín.

⚠️ **DUY NHẤT-hoặc-KHÔNG**, không bao giờ *"chọn cái đầu tiên"*: hai biến cùng
quy về một nhãn là tình huống mơ hồ, và đoán giữa chúng đặt một phép đoán vào
giữa đường gác cửa. `test_J2` khoá.

Hệ quả đo được, và nó **đổi một khẳng định cũ**: `test_J` từng ghim *"không có
bản đồ C₁a ⇒ `not_checkable`"*. Đó là mô tả một **giới hạn**, không phải một
tính chất an toàn. Nay ô ấy ghim hành vi mạnh hơn — phân giải được, và vẫn
**kết tội đúng** khi hình sai.

## 5. Sau vá — cùng bộ đo, một biến

⚠️ **Bản đầu của replay đo nhầm đường, và đó là bài học của wave.** Nó dựng
`RequestContract` **thẳng**, nên không đi qua biên đóng băng, không thấy bất
biến nào, và báo *"bản vá không đổi gì"* cho một bản vá đúng — đúng lớp lỗi kho
gọi tên là *"một sửa chữa không nằm trên đường chạy thật"*.

Cách chữa **không** phải chép danh sách bộ phát sang bộ đo (bản thứ hai sẽ quên
bộ phát tiếp theo) mà là tách `analyze_contract.gan_bat_bien_nguon` thành một
thẩm quyền có tên, để **cả sản phẩm lẫn bộ đo gọi chung**.

Cột "trước" cũng được sinh lại bằng **chính bộ đo ấy** với cờ `--bo-bat-bien`
(gỡ đúng bất biến mới). Hai cột, một nhạc cụ, một biến.

| Ca | Trước | Sau |
|---|---|---|
| fact kể chuyện · toạ độ đúng | `served` · 45 | **`served` · 45** |
| fact kể chuyện · `B(99,7,0)` | `served` · 540 | **`source_invariant`** |
| fact có toạ độ · toạ độ đúng | `served` · 45 | **`served` · 45** |
| fact có toạ độ · `B(99,7,0)` | `served` · 540 | **`source_invariant`** |
| `D(3,3,0)` mất phần lõm | `served` · 63 | **`source_invariant`** |
| `source_fact_id` trỏ nhầm | `served` · 540 | **`source_invariant`** |
| `model_assumption` che | `served` · 540 | **`source_invariant`** |

Artifact: `REPLAY_TRUOC.json` · `REPLAY_SAU.json`.

## 6. Ranh giới đã giữ — chứng minh bằng test

**Đề CÓ cho toạ độ**: đúng → PASS (6 bất biến đạt) · sai một thành phần trong
mặt phẳng đáy → từ chối · sai kèm `source_fact_id` tồn tại → từ chối · sai kèm
`model_assumption` → từ chối · mất phần lõm → từ chối · nhân đôi toàn bộ đáy
(thể tích thành `180`, một con số "hợp lệ") → từ chối.

> ⚠️ `B(6,0,1)` cũng sai một thành phần nhưng bị **kernel** chặn trước bằng
> `POLYHEDRON_FACE_NOT_PLANAR` — nó nhấc `B` khỏi mặt phẳng đáy. Hai cổng độc
> lập cùng chặn một ca là chuyện tốt; ghim ca ấy vào `source_invariant` sẽ là
> ghim **sai tầng**. `test_07b` ghi đúng tầng đo được.

**Đề KHÔNG cho toạ độ**: không phát bất biến nào · gốc canonical `[0,0,0]` với
`model_assumption` vẫn hợp lệ · **tịnh tiến hệ trục** vẫn hợp lệ và vẫn ra đáp
số đúng.

**Điểm dẫn xuất**: bất biến toạ độ **không thay** producer proof — `M` khai
thẳng toạ độ ĐÚNG vẫn bị chốt `DERIVED_ENTITY_WITHOUT_PRODUCER`; `M` dựng bằng
`midpoint` thì cả ba bất biến (toạ độ `A` · toạ độ `B` · `segment_division`)
cùng đạt.

## 7. Bảy phép tiêm

| # | Tiêm | Đo được |
|---|---|---|
| ① | bỏ **bộ phát** | `B(99,7,0)` được phục vụ lại, `V = 540` |
| ② | bỏ **dispatch checker** (chỉ ở phía checker) | phục vụ lại; cổng khai `not_checkable ≥ 6` |
| ③ | chỉ kiểm `source_fact_id` **tồn tại** | tái hiện đúng lỗi gốc |
| ④ | so bằng **dung sai float** | `1/3` vs `333333333333/1000000000000` lệch `< 1e-12` — float không phân biệt nổi, `Fraction` thì có |
| ⑤ | bỏ **thẩm quyền tên** | ca `O'`/`Oprime` tụt xuống `not_checkable` |
| ⑥ | cho `model_assumption` **thắng** dữ kiện | ca sai lọt qua |
| ⑦ | bỏ chặn **unresolved** | đề tự mâu thuẫn vẫn ra một con số |

> ⚠️ Phép tiêm ② lúc đầu vá `PC.KIND` — **vô hiệu**, vì bộ phát và checker cùng
> đọc hằng ấy nên nó đổi cả hai vế và phép tiêm tự triệt tiêu. Guard xanh mà
> chẳng chứng minh gì. Phải vá đúng **một** vế, và route import
> `check_source_invariants` ở mức module nên phải vá `route`, không phải
> `postconditions`.

`test_21b` của wave trước — một test **xanh mô tả lỗ** — nay đảo chiều thành
khẳng định hành vi đúng, giữ nguyên docstring lịch sử.

## 8. Cache — bump 92 → 93, chứng minh bằng ROW THẬT

Chiều là **`served` (số SAI) → `rejected`**, chiều nguy hiểm nhất. Bằng chứng
không phải lập luận: `scripts/proof_cache_row_point_coordinate.py` chèn một row
`status = "ok"` mang `V = 540` rồi hỏi `_cache_lookup`.

```
ENVELOPE_SAI_VAN_HIT_DUOI_VERSION_CU = true
BUMP_LAM_ROW_CU_MISS                 = true
```

Artifact: `PROOF_CACHE_ROW.json`.

```
CACHE_VERSION_BEFORE/AFTER   92 → 93
MODEL_FACING_CONTRACT_CHANGED = NO
  ANALYZE_SCHEMA_CHANGED      = NO   515001b503af5c7c
  SYNTHESIS_SCHEMA_CHANGED    = NO   6ccef3230c003d61
  GRAMMAR_CARD_CHANGED        = NO   cc105e4f1da84d23
  PROMPT_CHANGED              = NO   55ac1ca6a6df92ce
  CAPABILITY_HASH_CHANGED     = NO   72edf39f6c10220d
  SEMANTIC_ENVIRONMENT        = NO   a483ced9fd7546df
CANDIDATE_HASH_BEFORE/AFTER  6362674e957909d8 → 9bb796e9eb5e96a8
PRODUCT_CAPABILITY_CHANGED    = NO
```

Đây là **lần thứ hai liên tiếp** bump vì *phán quyết* đổi chứ không vì *đầu vào
của mô hình* đổi — trước wave 92, mọi bump từ 68 đều thuộc loại sau.

**Cổng thứ năm, lại lần nữa**: ba test ghim danh tính lượt đo live cũ
(`test_20` của wave trước, hai test elip). Sửa **test**, giữ artifact — tách
*"số đo đông cứng"* khỏi *"version hệ hiện tại"*, và giữ nguyên phần ghim sáu
băm model-facing, vì đó mới là thứ các ô ấy bảo vệ.

## 9. Giới hạn — khai bằng test, không hứa bao phủ

`test_90` liệt kê thứ bộ phát **chưa** đọc, và nó **xanh nghĩa là giới hạn
còn**:

```
NOT_EXTRACTED:
  · thập phân dấu PHẨY        A(1,5, 2, 3)  — đọc được hai cách, cố ý không đoán
  · tên đứng SAU bộ ba        "toạ độ (1,2,3) là A"
  · toạ độ tách thành ba pt   "x_A = 1, y_A = 2, z_A = 3"
  · toạ độ 2D                 A(1, 2)
  · toạ độ VÔ TỈ              A(√2, 0, 0)   — ngoài `Fraction`
```

`test_91` khoá rằng giới hạn ấy **không bao giờ thành lời kết tội oan**: đề
ngoài ngưỡng ⇒ không phát bất biến ⇒ cổng im lặng, không `violated`.

## 10. Cổng

```
targeted        test_point_coordinate_invariant.py        51 pass
                test_source_invariant_gate.py             22 pass
                test_nonconvex_polyhedron_discoverability 40 pass
pytest          4581 collected · 4580 chạy · 4579 pass + 1 skip (cây sạch @ 00f127b)
replay_demo     5/5 · REDUCED_CHAIN 1/1
crash_surface   6/6 · ném ra ngoài 0
certify         RUNNER_CERTIFICATION PASS · APPLICATION_LLM_CALLS 0
cache identity  15 pass @ v93
freeze --verify exit 0 sau commit đóng băng lại
git diff --check sạch
FRONTEND_RESULT = INHERITED · BUILD_RESULT = INHERITED
FRONTEND_TRACKED_BYTES_CHANGED = NO
```

## 11. Phạm vi kết luận

```
POINT_COORDINATE_SOURCE_INVARIANT = PASS
NONCONVEX_POLYHEDRON_SEQUENCE = CLOSED_AT_DEVELOPMENT_FOUNDATION
CAPABILITY_STATUS = foundation_only   PRODUCT_PROMOTION_ELIGIBLE = NO
STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
```

Kết luận chỉ đúng **trong grammar toạ độ đã test** (§9). Bất biến này bảo vệ
toạ độ điểm; nó **không** nói gì về những dữ kiện khác chưa có bất biến nguồn.

`RECOMMENDED_NEXT_ACTION` — xem `docs/CURRENT_STATE.md`.
