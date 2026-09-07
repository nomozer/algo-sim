# CURVED_RADIUS_SLOT_AFFORDANCE_ADJUDICATION

> 2026-09-07 · `APPLICATION_LLM_CALLS = 0`
>
> ```
> SELECTED_BRANCH = A   (Card thiếu mệnh đề)
> CARD_CONTRACT_COMPLETE = NO  →  MISSING = [P1, P3]
> RAW_FAILURES_MATCH = YES  ·  CURVED_RIM_POINT_AFFORDANCE = REPLICATED
> MINIMAL_DELTA = 2 trường (−343 B) → served · 16π√5
> ```
>
> Ba câu hỏi, ba câu trả lời đo được. Câu quan trọng nhất là câu đầu: **thẻ
> không hề cấm điều mô hình đã làm** — nó tả `rim_point` bằng một mô tả HÌNH
> HỌC mà `(4,0,0)` thật sự thoả.

## 1. Bằng chứng đầu vào (§2)

```
DIRECT_RADIUS_ELLIPSE_PATH                 = VALID
CURRENT_MODEL_CANDIDATE_DIMENSIONS_CORRECT = 9/10
CURRENT_FIRST_FAILURE                      = ungrounded rim_point
REPAIR_CALLS_AVAILABLE = 3   ·   REPAIR_CALLS_USED = 0
```

## 2. Ma trận hợp đồng THẬT (§3)

Bảng họ cong, đọc thẳng `KHOI_CONG`:

| Kind | `khai_bang_ban_kinh` | `co_truc` | `can_chieu_cao` | `vai_dinh` |
|---|:---:|:---:|:---:|---|
| `ball` | ✅ | ❌ | ❌ | — |
| `cylinder` | ✅ | ✅ | ✅ | tâm đáy trên |
| `cone` | ✅ | ✅ | ✅ | đỉnh |

Validator lược đồ, **đo bằng máy** trên chín tổ hợp × ba họ:

| Tổ hợp | ball | cylinder | cone |
|---|:---:|:---:|:---:|
| `radius` only | **OK** | ✗ trục chưa xác định | ✗ trục chưa xác định |
| `rim_point` only | **OK** | ✗ trục chưa xác định | ✗ trục chưa xác định |
| `radius` + `rim_point` | ✗ đúng-một | ✗ đúng-một | ✗ đúng-một |
| neither | ✗ đúng-một | ✗ đúng-một | ✗ đúng-một |
| `radius` + `height` | ✗ cầu không có chiều cao | **OK** | **OK** |
| `rim_point` + `height` | ✗ cầu không có chiều cao | **OK** | **OK** |
| `radius` + `apex` | ✗ cầu chỉ cần tâm + điểm | **OK** | **OK** |
| `rim_point` + `apex` | ✗ cầu chỉ cần tâm + điểm | **OK** | **OK** |
| `rim` + `apex` + `radius` | ✗ đúng-một | ✗ đúng-một | ✗ đúng-một |

**Hai cặp loại trừ**, cả hai là XOR bắt buộc:
`{rim_point, radius}` · `{apex_or_top, height}` (cặp sau chỉ cho trụ/nón).

## 3. Bốn mệnh đề trong Card (§4)

| | mệnh đề | schema/validator | Card | nguồn sinh |
|---|---|:---:|:---:|---|
| **P1** | `radius` dùng khi đề cho bán kính **bằng số** | ❌ không nơi nào | ❌ **THIẾU** | — (luật CHỌN) |
| **P2** | `rim_point` là một ĐIỂM hình học trên vành | ✅ `Field.description` | ✅ có | `contract.py` |
| **P3** | `radius`/`rim_point` **ĐÚNG MỘT** | ✅ `contract.py` ① | ❌ **THIẾU** | validator |
| **P4** | trụ/nón nhận `radius` + `height` | ✅ `contract.py` ② | ✅ có | `_TOAN_HANG_LENH` |

```
CARD_CONTRACT_COMPLETE = NO
MISSING_PROPOSITIONS   = [P1, P3]
```

### ⚠️ Vì sao P2 "có" mà vẫn không đủ

Thẻ tả `rim_point` là *"một ĐIỂM trên mặt cầu, hoặc trên vành đáy"* — một mô tả
**HÌNH HỌC thuần**, và `(4,0,0)` **thật sự** nằm trên vành đáy bán kính 4. Nên
**theo thẻ, mô hình không làm gì sai**; luật nó vi phạm (*"điểm phải truy được
về đề"*) sống ở `grounding_gate`, một tầng thẻ không nói tới.

### ⚠️ Và dòng `Xuất xứ:` phủ ba ca — không ca nào là ca này

> *"khi chọn hệ toạ độ, đặt MỘT điểm đầu vào làm gốc và ghi `model_assumption`;
> dùng `source_fact_id` cho giá trị lấy thẳng từ đề; điểm mà đề xác định bằng
> một QUAN HỆ thì phải TẠO bằng câu lệnh dựng."*

`P_rim` không phải gốc hệ toạ độ (`O` đã là), không lấy thẳng từ đề, không do
một quan hệ xác định. Ca thứ tư — **một điểm đề không hề nhắc tới** — thẻ im
lặng hoàn toàn.

### P3: thẻ nói THAY THẾ, không nói ĐÚNG MỘT

Thẻ có `radius?:…[ĐẠI LƯỢNG bán kính, **thay cho điểm trên mặt**]`. Đó là
*alternative*. Nhưng **cả hai ô đều mang `?`**, nên người đọc suy ra *"đều tuỳ
chọn"* — trong khi validator đòi **đúng một, bắt buộc**.

## 4. Hai raw candidate (§5)

| chiều | after-axis-scale-repair · attempt 0 | fresh-confirmation · attempt 1 |
|---|:---:|:---:|
| `radius` field present | ❌ | ❌ |
| `rim_point` field present | ✅ | ✅ |
| rim point named in problem | ❌ | ❌ |
| rim point has `source_fact_id` | ❌ | ❌ |
| rim point used elsewhere | không | không |
| axis already determined | ✅ | ✅ |
| height already determined | ❌ | ❌ |
| problem explicitly provides radius | ✅ | ✅ |
| direct-radius path valid for kind | ✅ | ✅ |

Lời khai của chính mô hình, hai lượt:

> *"Chọn một điểm trên vành đáy dưới để xác định bán kính, tại (4,0,0) vì bán
> kính đáy bằng 4."*
> *"Chọn một điểm trên vành đáy dưới để xác định bán kính của hình trụ."*

```
RAW_FAILURES_MATCH = YES
CURVED_RIM_POINT_AFFORDANCE = REPLICATED
```

Hai lượt độc lập cùng thoả **toàn bộ** điều kiện của mệnh đề:

> *Mô hình thêm một điểm đề không đặt tên, chỉ để mã hoá một độ dài đề đã cho
> trực tiếp.*

## 5. Minimal delta (§6)

```
FIELDS_CHANGED      = 2   (`rim_point` bỏ · `radius` thêm)
STATEMENTS_REMOVED  = 1   (`declare_point P_rim`)
STATEMENTS_ADDED    = 0
DECLARATIONS_SWAPPED = P_rim (point3, model_assumption) → r (float, source_fact_id)
BYTE_DELTA          = −343
```

Replay trọn đường:

```
schema PASS · static PASS · grounding PASS
source_invariants checked=1 passed=1 violated=0
runtime PASS · exact_answer 16π√5 · postconditions PASS
trace PASS · scene3d PASS · servable YES · stage served
```

⚠️ **Một đính chính bộ đo, khai trước khi dùng số.** Bản đầu của phép replay
chấm bằng `REQUEST_CONTRACT_GOLD` và trả `requested_operation_uncovered` cho
một chương trình **hoàn toàn đúng** — vì hợp đồng live đặt witness
`dien_tich_e` còn gold đặt `dien_tich_E`. Đó là chấm ứng viên của mô hình bằng
một **đề khác**, đúng bài học đã ghi ở `replay_plane_from_equation.py`. Nay
hợp đồng dựng lại từ raw `analyze` của lượt chạy thật, và witness cũng đọc từ
hợp đồng ấy.

## 6. Hai loại lỗi cùng một mã (§7)

| Trường hợp | Bán kính trong đề | Rim point trong đề | Direct-radius | Nguy cơ giấu đáp số | Hướng xử lý |
|---|:---:|:---:|:---:|---|---|
| **ca elip hiện tại** | **có** | không | **có** | thấp — đo được | gợi ý `radius` |
| điểm bịa mã hoá đại lượng đề KHÔNG cho | không | không | chưa có nguồn | **cao** | giữ fail-closed |
| rim point thật, đề đặt tên | có thể | **có** | có thể | thấp | cho phép nếu grounded |
| điểm dẫn xuất phải dựng | có quan hệ dựng | không trực tiếp | tuỳ | trung bình | đòi producer |

**Tín hiệu cấu trúc đủ để nhận riêng ca elip** — cả sáu đều đọc được từ
chương trình + hợp đồng, không cần đoán:

```
kind = construct_curved_solid
+ KHOI_CONG[kind].khai_bang_ban_kinh = True
+ hợp đồng CÓ fact bán kính
+ điểm gây lỗi CHỈ được dùng ở ô `rim_point`
+ điểm gây lỗi không được đề đặt tên
+ trục/pose đã xác định độc lập
```

Cả sáu tín hiệu **đã đo được** trên hai raw candidate (§4). Chúng là đầu vào
cho Nhánh B/C, **không** dùng ở wave này.

## 7. Diagnostic và repair policy (§8)

Thông điệp hiện tại:

> `P_rim: không có trong đề bài. model_assumption chỉ nói về CÁCH ĐẶT một đối
> tượng đề đã nêu; một điểm suy ra phải được DỰNG (trung điểm, giao, hình
> chiếu…) để engine tính toạ độ, không được khai thẳng toạ độ.`

| nêu được? | |
|---|:---:|
| biến gây lỗi (`P_rim`) | ✅ |
| nơi biến được dùng (`rim_point`) | ❌ |
| bán kính đã có trong đề | ❌ |
| `radius` đang là ô hợp lệ | ❌ |
| thao tác sửa dự kiến | ❌ (chỉ gợi "DỰNG", tức đường SAI cho ca này) |

```
DIAGNOSTIC_IDENTIFIES_RADIUS_SLOT        = NO
REPAIR_POLICY_DISTINGUISHES_SAFE_SUBCASE = NO
KHONG_DUOC_SUA = [DERIVED_ENTITY_WITHOUT_PRODUCER, UNANCHORED_DERIVED_ASSUMPTION]
```

⚠️ Thông điệp còn **chỉ sai đường**: nó bảo *"phải được DỰNG"*, nhưng với ca
này không phép dựng nào sinh ra một điểm vành hữu tỉ — đúng lý do ô `radius`
ra đời (`CURVED_CONSTRUCTION_GROUNDING_FOUNDATION`: định lý ba bình phương
hữu tỉ). Đây là **Nhánh B**, và wave này không đụng.

## 8. Nhánh A — bản sửa (§9)

Một dòng, đặt ngay sau khối lệnh:

```
  Khối cong: mỗi cặp `rim_point`/`radius` và `apex_or_top`/`height` chọn
  ĐÚNG MỘT. Đề cho bằng SỐ thì dùng ô đại lượng (`radius`, `height`); ô ĐIỂM
  dành cho điểm đề có nêu, đừng dựng thêm một điểm chỉ để chở một độ dài.
```

**+286 byte**, thẻ hình học 6386 → 6672. Thẻ ĐẦY ĐỦ **không đổi** (dòng chỉ
vào `_the_hinh_hoc`).

⚠️ **Dòng văn xuôi viết tay THỨ HAI của thẻ** — cùng bậc ngoại lệ với
`_DONG_XUAT_XU`, nên nó phải trả giá bằng bằng chứng, và bằng chứng là §4/§5:
hai lượt độc lập, cùng hình dạng, bản sửa hai trường.

**Vì sao không sinh được từ nguồn**, hai lý do khác nhau:

- *"ĐÚNG MỘT trong hai"* — validator CÓ, nhưng đó là quan hệ **giữa hai
  trường**, không thuộc `Field.description` của trường đơn lẻ nào. Y hệt lý do
  `_DONG_XUAT_XU` tồn tại.
- *"đề cho bằng SỐ thì dùng ô đại lượng"* — luật **CHỌN**, không phải luật
  **HỢP LỆ**. Cả hai lối đều hợp lệ; cái sai chỉ lộ ở `grounding` một tầng sau.
  Không validator nào encode được.

**Parity thì VẪN dẫn xuất.** `test_curved_radius_slot_card.py::_cap_loai_tru`
dò **TẬP CHẤP NHẬN** của validator (2⁴ phép thử mỗi họ) và kết luận `{a,b}` là
XOR ⇔ mọi tổ hợp được nhận chứa đúng một trong hai. Thêm một cặp XOR thứ ba mà
quên thẻ ⇒ đỏ.

⚠️ **Phép dò phải sửa một lần, và `test_02` là thứ bắt được.** Bản đầu dựng
nền bằng *"hai ô còn lại"* — mà hai ô ấy chính là cặp XOR kia, nên nền luôn bất
hợp lệ và phép dò trả **RỖNG**. Một `test_01` chạy trên tập rỗng thì xanh mà
không khẳng định gì. `test_02` neo phép dò vào hai cặp đã đọc tay từ
`contract.py`, nên ca xanh-giả ấy đỏ ngay.

Card C và hai affordance `ratio`/`Xuất xứ` **nguyên văn**.

## 9. Test và tiêm lỗi (§10)

**19 test.** Hợp đồng thật giữ nguyên (direct radius trụ ✅ · nón ✅ · rim point
✅ · `radius`+`rim_point` ✗ · không-ô-nào ✗ · cầu không nhận `height` ✗).
Grounding giữ nguyên độ chặt: rim point không neo vẫn `UNANCHORED_DERIVED_
ASSUMPTION`; rim point CÓ neo vẫn qua.

**Ba phép tiêm:**

| # | tiêm | quan sát |
|---|---|---|
| ① | xoá tên ô khỏi dòng thẻ | parity mất căn cứ ⇒ `test_01` có răng |
| ② | giữ luật loại trừ, bỏ *"bằng SỐ"* | P1 biến mất khỏi thẻ |
| ③ | `cone.khai_bang_ban_kinh = False` | `radius` hết hợp lệ cho nón; **tập chấp nhận co lại** |

⚠️ Kỳ vọng đầu của ③ **sai và đã sửa**: tôi tưởng cặp `{rim_point, radius}` sẽ
hết là XOR. Không — bỏ `radius` đi thì mọi tổ hợp được nhận đều chứa đúng
`rim_point`, nên tính "đúng một" thoả một cách **tầm thường**. Thứ thật sự đổi
là **tập chấp nhận**, và khẳng định đúng là *"không tổ hợp nào còn dùng
`radius`"*.

## 10. Identity và cache (§11)

| thành phần | trước | sau |
|---|---|---|
| `grammar_card` | `2cc55280…` | **`cc105e4f…`** |
| `prompts` · `analyze_schema` · `synthesis_schema` · `capability` | — | **không đổi một byte** |
| `semantic_environment` | `4d2a555a…` | **`a483ced9…`** |
| `CACHE_VERSION` | 90 | **91** |
| candidate | `27f5c076…` | **`adbb3514…`** (91 file) |

⚠️ **`capability` KHÔNG đổi** và đó là một khẳng định đáng ghi: wave này không
đụng `_CHU_KY`/`_KIEU_DUNG`/`_TOAN_HANG_LENH`. Nó **không thêm phép, không
thêm kiểu, không đổi luật hợp lệ** — nó chỉ **nói ra** một luật đã có.

Bump theo luật *"đầu vào của mô hình đổi"*, đúng lý do bump 70/73/86: cache giữ
CẢ envelope, nên đề đã phân tích sẽ trả lại chương trình sinh bởi **thẻ cũ**.
Kiểm cache: **không envelope `ok` nào hoá sai** — luật hợp lệ không đổi, nên
mọi chương trình từng `served` vẫn `served`.

## 11. Báo cuối (§13)

```
DIRECT_RADIUS_PATH        = VALID
CARD_CONTRACT_COMPLETE    = NO  (truoc wave) → YES (sau wave)
MISSING_PROPOSITIONS      = [P1, P3]  — ca hai da bo sung
RAW_FAILURES_MATCH        = YES
CURVED_RIM_POINT_AFFORDANCE = REPLICATED
MINIMAL_DELTA_FIELDS      = 2   (−343 byte, 1 cau lenh bo, 0 them)
MINIMAL_DELTA_SERVABLE    = YES
EXACT_ANSWER              = 16π√5
DIAGNOSTIC_IDENTIFIES_RADIUS_SLOT        = NO
REPAIR_POLICY_DISTINGUISHES_SAFE_SUBCASE = NO
SELECTED_BRANCH           = A

MODEL_FACING_CONTRACT_CHANGED = YES — DUNG MOT bam (`grammar_card`);
                            `capability` KHONG doi (khong them phep/kieu/luat)
APPLICATION_LLM_CALLS     = 0
CACHE_VERSION_BEFORE/AFTER  = 90 → 91
CANDIDATE_HASH_BEFORE/AFTER = 27f5c076… → adbb3514…
TEST_RESULTS = wave 19 pass (3 tiem) · pytest 4422 pass, 0 do · replay 5/5 ·
               crash 6/6 nem 0 · certify PASS · cache identity exit 0 @ v91 ·
               freeze --verify exit 0 (91 file) · diff --check sach ·
               frontend KE THUA (khong consumer nao doi)
COMMITS      = 3
WORKING_TREE = sach
RECOMMENDED_NEXT_ACTION = OBLIQUE_ELLIPSE_E2E_ONE_FINAL_RERUN
```

## 12. Giới hạn

- **Hiệu quả của dòng thẻ đối với mô hình giữ `NOT_MEASURED`.** Wave này sửa
  **tính đầy đủ của hợp đồng**, không đo hành vi. `APPLICATION_LLM_CALLS = 0`.
- `CURVED_RIM_POINT_AFFORDANCE = REPLICATED` là **hai lần**, không phải một
  khảo sát.
- **Nhánh B và C không bị bác, chỉ chưa tới lượt.** Diagnostic thật sự không
  chỉ đường (`NO`), và policy thật sự không tách lớp con (`NO`) — cả hai đã đo
  và ghi lại, `test_14`/`test_15` khoá chúng để một wave sau sửa thì phải cập
  nhật kết luận. §9 nói mỗi wave chỉ làm **một** nhánh, và bằng chứng chọn A:
  `CARD_CONTRACT_COMPLETE = NO`.
- Bản vá là **văn phạm**, không nới cổng: `test_12` khoá rằng rim point không
  neo vẫn bị bác y như trước.

**Việc kế tiếp: `OBLIQUE_ELLIPSE_E2E_ONE_FINAL_RERUN`** — đúng một lượt, trần
5 logical calls, để đo xem dòng thẻ có đổi được hành vi không. Nếu `served`,
đóng `ELLIPSE_FOUNDATION_SEQUENCE` và chuyển sang
`NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION`. Nếu vẫn `rim_point`, giả thuyết ①
(*thẻ chưa nói rõ*) bị **bác bằng đo**, và Nhánh B/C lên lịch với bằng chứng
đã sẵn ở §6/§7.
