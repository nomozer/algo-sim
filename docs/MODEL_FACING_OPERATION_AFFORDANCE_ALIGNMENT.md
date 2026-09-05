# MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT

> 2026-09-05. `MEASUREMENT_CLASS = DEVELOPMENT_AB` · `HELD_OUT_CLAIM = NO` ·
> `PRODUCT_CAPABILITY_CHANGED = NO`.
>
> **Tiêu quota thật**: 24 lượt gọi logic (trần 24), 24 lượt vật lý, 136 766 token.

## 0. Kết quả

Thẻ nói ra **kiểu kết quả** của từng phép. Chỉ vậy.

| lượt tổng hợp ĐẦU, 6 ca cong | A (thẻ hiện tại) | B (thẻ có kiểu ra) |
|---|--:|--:|
| chọn đúng toán tử cho **kết quả được hỏi** | **1/6** | **6/6** |
| `served` ngay lượt đầu | **0/6** | **3/6** |
| đáp số đúng trong các ca served | — | **3/3** |

Ghép cặp: **5 thắng · 0 thua · 1 cả hai đúng · 0 cả hai sai**.

```
SELECTOR_GAIN_OBSERVED = YES   (6 cặp · B 6/6 ≥ 4/6 · thắng−thua = 5 ≥ 2)
CHANGE_ACCEPTED = YES          PRODUCT_VARIANT_AFTER_WAVE = B
```

Ca đối chứng đa diện: **cả hai arm** chọn `construct_section` — B không khái
quát hoá quá tay.

## 1. Điểm xuất phát, đo lại từ kho

```
HEAD = 93de148 · WORKING_TREE = CLEAN
CACHE_VERSION = 81
CANDIDATE_HASH = a5b63aa3cb38e81f…  (89 file, verify exit 0)
BACKEND_BASELINE = 3779 passed · 1 skipped · 1 deselected
```

## 2. Bề mặt mô hình thực sự nhận — và hai điều nó không nói

Thẻ A: `c7c001c4df7c802a…`, **5472 byte**, đóng băng nguyên văn tại
[`card_A.txt`](evaluation/geometry/operation-affordance-ab-v1/card_A.txt).

Hai đường cắt được trình bày thế này:

```
[LỆNH]              construct_section:      target_var:tên solid:tên<solid>[khối] plane:tên<plane3>[mp cắt] label?:nhãn
[BIỂU THỨC→assign]  intersect_plane_curved: solid:tên<curved_solid>[khối cong] plane:tên<plane3>[mặt phẳng cắt]
```

**① Thẻ chưa bao giờ in kiểu KẾT QUẢ của bất kỳ phép nào.** Nó in toán hạng, và
chỉ toán hạng. Cả hai vế đã nằm sẵn trong thẩm quyền — `_CHU_KY` mang kiểu trả
về ở vế phải, `_KIEU_DUNG` mang kiểu vật mỗi `construct_*` sinh ra — và cả hai
chưa từng tới mắt mô hình. Nhãn `[BIỂU THỨC→assign]` (thêm ở
`CARD_CATEGORY_AFFORDANCE`) nói **cửa tiêu thụ**, không nói **kiểu ra**; hai câu
khác nhau.

**② Danh sách kiểu khai được đã trôi khỏi thẩm quyền.**
`grammar_card.py:592` giữ một danh sách **viết tay**; `MemoryType` thêm
`circle3` và `curved_solid` ở wave cong 2026-09-03 mà danh sách không được sửa.
Thẻ vì thế **tự mâu thuẫn**: nó viết `solid:tên<curved_solid>` và
`radius(of:tên<circle3|curved_solid>)` trong khi phần khai báo nói hai kiểu ấy
không tồn tại.

### Bằng chứng phân biệt hai điều ấy

Đọc lại raw candidate **lượt đầu** của `dev-v1`:

| | |
|---|---|
| khai `curved_solid` | **5/8** — mô hình DÙNG một kiểu thẻ không liệt kê |
| khai `circle3` | **0/8** — không lần nào |
| khai `section` | **8/8** |

Danh sách thiếu **không** phải rào chắn tuyệt đối. Nhưng `circle3` thì tuyệt
đối vắng mặt — và `circle3` chỉ tồn tại với tư cách **kiểu kết quả** của
`intersect_plane_curved`, tức đúng thứ ① giấu đi.

```
REGISTERED_HYPOTHESIS = Mô hình chọn `construct_section` cho khối cong vì thẻ
  không nói `intersect_plane_curved` SINH RA `circle3`. Khi cả bốn vế — kiểu
  vào → phép → kiểu ra → cửa tiêu thụ — cùng nằm trên MỘT dòng, việc chọn phép
  thành một phép khớp kiểu chứ không phải suy đoán từ tên.
EXPECTED_BEHAVIOR_CHANGE = 0/6 → ít nhất 4/6, và `circle3` xuất hiện trong khai
  báo. Không kỳ vọng gì về grounding hay liên kết tên.
```

Đăng ký đầy đủ (kèm luật quyết định, khoá trước kết quả):
[`registration.json`](evaluation/geometry/operation-affordance-ab-v1/registration.json).

## 3. Ứng viên B — `ACTUAL_MODEL_FACING_DELTA`

Thẻ B: `86134034116f9c07…`, **5675 byte** (**+203**).

| thành phần | thay đổi | thẩm quyền | byte |
|---|---|---|--:|
| B1 | mỗi dòng **biểu thức** thêm `→<kiểu>` | `_CHU_KY[kind][1]` | — |
| B2 | mỗi dòng **câu lệnh dựng** thêm `→<kiểu>` | `_KIEU_DUNG[kind]` | 178 (B1+B2, 17 dòng) |
| B3 | danh sách kiểu khai được **dẫn xuất** | `MemoryType ∩ (kiểu thẻ nhắc tới)` | 25 |

Sau delta:

```
[LỆNH]              construct_section:      … plane:tên<plane3>[mp cắt] label?:nhãn →section
[BIỂU THỨC→assign]  intersect_plane_curved: solid:tên<curved_solid>[khối cong] plane:tên<plane3>[mặt phẳng cắt] →circle3
  type nhận đúng một trong: int bool float point3 vector3 line3 plane3 polygon3 solid section circle3 curved_solid
```

`int` vào theo B3, và **đúng**: thẻ vẫn luôn nhận `tên<scalar|float|int>` —
dẫn xuất chỉ làm lộ thêm một mâu thuẫn cũ.

Không thêm một câu cấm đoán nào; toàn bộ delta là **khẳng định**. Ngôn ngữ IR,
nghĩa toán tử, schema, kernel, checker, grounding và chính sách repair sản phẩm
giữ nguyên. Thẻ **đầy đủ** (bản Tin học) không đổi: 5588 byte.

Trần byte thẻ hình học 5510 → **5720**, phân loại **NHÃN THIẾU** — cùng hạng
mục bốn lần nâng trần trước đã ghi là đáng, không phải từ vựng mới. Phân loại
viết tại chỗ trong `test_grammar_card.py`.

Khoá bởi
[`test_card_result_type_affordance.py`](../backend/tests/semantic_program/test_card_result_type_affordance.py)
— 20 test, 3 phép tiêm.

## 4. Corpus validation và preflight

8 đề **mới**, khác `dev-v1` cả đề lẫn ký hiệu lẫn số liệu (kiểm bằng
`test_corpus_KHONG_trung_de_cua_dev_v1`).

```
CORPUS_HASH           = a6d875e1637cfc95d0af5dc691536b87fc7b5c1529e03a9df6eea0d3e8664898
EXPECTED_RESULTS_HASH = e2d164f59838fa00a1a5056db018b30ee606edf0a2562b097375386e8a382919
```

| ca | họ | hỏi | lớp đúng | đáp số |
|---|---|---|---|---|
| `e1` | cylinder | bán kính | `intersect_plane_curved` | `5` |
| `e2` | cylinder | diện tích | `intersect_plane_curved` | `121π` |
| `e3` | cone | bán kính (cắt tính từ **đáy**) | `intersect_plane_curved` | `9` |
| `e4` | cone | bán kính (cắt tính từ **đỉnh**) | `intersect_plane_curved` | `15` |
| `e5` | ball | bán kính | `intersect_plane_curved` | `40` |
| `e6` | ball | diện tích | `intersect_plane_curved` | `400π` |
| `e7` | **đa diện** | diện tích thiết diện | **`construct_section`** | `18√3` |
| `e8` | cylinder | mặt phẳng **xiên** | **`refusal`** | `CURVED_SECTION_OUTSIDE_V1_CLOSURE` |

Bốn bộ ba Pythagoras (12-16-20 · 21-28-35 · 9-40-41 · 20-21-29); `e7` trả
Radical `18√3`.

```
GOLD_POSITIVE_SERVABLE = 7/7   GOLD_EXACT_MATCH = 7/7
GOLD_SCENE3D_PASS      = 7/7   GOLD_NEGATIVE_BOUNDARY = PASS
PRE_LIVE_GUARD         = OPEN
```

## 5. Thiết kế phép đo

`analyze` chạy **đúng một lần** mỗi đề; `RequestContract` sinh ra dùng **y
nguyên** cho cả hai arm. Mỗi arm sinh **đúng một** raw candidate. Hai arm chỉ
khác thẻ — cùng đề, cùng hợp đồng, cùng system prompt, cùng tham số giải mã,
cùng engine.

Lịch chạy luân phiên, **khoá trước khi xem kết quả**:

```
e1 A→B   e2 B→A   e3 A→B   e4 B→A   e5 A→B   e6 B→A   e7 A→B   e8 B→A
```

One-shot là cấu hình của **runner thí nghiệm**: `MAX_SEMANTIC_PROGRAM_ATTEMPTS`
hạ xuống 1 trong tiến trình runner; hằng số sản phẩm giữ **3** và được kiểm lại
sau lượt chạy (`test_E5`).

Runner chứng minh bằng **provider stub trước lượt live** — 18 test
([`test_runner_affordance_ab.py`](../backend/tests/test_runner_affordance_ab.py)):
mỗi đề 1 analyze + 2 synthesis · hai arm cùng một `RequestContract` · payload
hai arm **chỉ khác thẻ** (kiểm bằng phép thay chuỗi: `a.replace(card_A,"<THẺ>")
== b.replace(card_B,"<THẺ>")`) · manifest có trước lượt gọi · raw candidate còn
nguyên khi grounding chặn · bộ chấm phân biệt `NOT_OBSERVED` với `FAIL` ở đúng
ca `d1`/`d5` từng bị đếm sai · trần vật lý ném khi vượt.

## 6. Chấm — truy từ KẾT QUẢ về producer

Nguồn chấm là **raw candidate của lượt đầu**, kể cả khi chương trình bị chặn ở
tầng sau.

Đường truy: nghĩa vụ → `witness` → câu lệnh sinh witness (một `measure`) → toán
hạng `of` → câu lệnh sinh toán hạng ấy → `kind`. **Không** đếm
`intersect_plane_curved` xuất hiện ở đâu đó trong chương trình: một phép giao
dựng ra vật phụ rồi đáp số lấy từ chỗ khác là *"có xuất hiện"*, không phải
*"chọn đúng phép cho kết quả"*. Phản ví dụ nằm trong
`test_cham_KHONG_tinh_diem_cho_mot_phep_giao_o_VAT_PHU`.

## 7. Bảng từng cặp

| ca | thứ tự | A op | B op | A stage | B stage | A srv | B srv | B exact |
|---|---|---|---|---|---|---|---|---|
| `e1` | A→B | **PASS** | **PASS** | `structural_coverage` | **`served`** | ✗ | **✓** | PASS |
| `e2` | B→A | FAIL | **PASS** | `grounding` | `ir_static` | ✗ | ✗ | NOT_REACHED |
| `e3` | A→B | FAIL | **PASS** | `semantic_program` | **`served`** | ✗ | **✓** | PASS |
| `e4` | B→A | FAIL | **PASS** | `structural_coverage` | `structural_coverage` | ✗ | ✗ | NOT_REACHED |
| `e5` | A→B | FAIL | **PASS** | `structural_coverage` | **`served`** | ✗ | **✓** | PASS |
| `e6` | B→A | FAIL | **PASS** | `ir_static` | `ir_static` | ✗ | ✗ | NOT_REACHED |
| `e7` | A→B | PASS | PASS | `grounding` | `grounding` | ✗ | ✗ | NOT_REACHED |
| `e8` | B→A | NOT_OBSERVED | NOT_OBSERVED | `grounding` | `semantic_program` | ✗ | ✗ | NOT_OBSERVED |

`ASSIGN_WRAPPER_CORRECT = PASS` ở **cả 6** arm B — không ca nào viết
`intersect_plane_curved` như một câu lệnh. `DECLARED_RESULT_TYPE = ['circle3']`
ở cả 6.

## 8. Lỗi còn lại — và chúng KHÔNG ở tầng wave này đụng tới

Ba ca B chọn đúng phép mà vẫn không phục vụ được, mỗi ca chết ở một tầng khác:

| ca | tầng | lỗi |
|---|---|---|
| `e2`, `e6` | `ir_static` | `IR_USE_BEFORE_CONSTRUCTION: 'X'/'Y'/'D'/'C' — cần point3, có khai báo nhưng chưa có giá trị` |
| `e4` | `structural_coverage` | `radius((t)): container '(t)' chưa khai báo` |
| `e7` | `grounding` | `M/N/P: có initial_value nhưng thiếu source_fact_id` |
| `e8` | `semantic_program` | `UNANCHORED_DERIVED_ASSUMPTION: A1 không có trong đề bài` |

Bốn trên tám ca (`e2`, `e6`, `e7`, `e8`) hỏng ở **cùng một chỗ**: điểm có tên
lấy toạ độ và xuất xứ từ đâu. Khai mà không có giá trị · có giá trị mà không có
`source_fact_id` · có giá trị cho một tên grounding không khớp. `e4` là đúng
khiếm khuyết liên kết tên `analyze`/`synthesis` mà `dev-v1 §6b` đã đo.

⚠️ **`e8` có một phần lỗi thuộc về corpus của tôi**: đề viết `A₁`/`A₂` bằng ký
tự chỉ số dưới Unicode, mô hình khai `A1`/`A2` ASCII, và `la_ten_nguon` không
khớp. Nên `e8` **không** đo được ranh giới xiên. Ghi là giới hạn, không ghi là
kết quả về mô hình.

## 9. Luật quyết định — đối chiếu

| điều kiện giữ B | đo được | đạt |
|---|---|---|
| `SELECTOR_GAIN_OBSERVED` | 6 cặp · B 6/6 · thắng−thua 5 | ✓ |
| ca thành công dùng đúng cấu trúc + kiểu | `assign` 6/6 · `circle3` 6/6 | ✓ |
| B chọn đúng đường đa diện ở đối chứng | `construct_section` | ✓ |
| B trả đúng ranh giới ở ca âm | **NOT_REACHED** — cả hai arm chết ở lỗi khác | ghi riêng |
| mọi ca B served khớp đáp số | 3/3 | ✓ |
| gate hồi quy | xem §11 | ✓ |

Điều kiện ca âm **không đạt, và không phải một hồi quy do B gây ra**: arm A
cũng không chạm tới ranh giới, vì cùng một lỗi xuất xứ điểm. Luật đăng ký nói
*"từ chối tại một lỗi không liên quan được ghi riêng"* — đã ghi ở §8.

```
CHANGE_ACCEPTED = YES
```

## 10. Identity và cache

| | trước | sau |
|---|---|---|
| `grammar_card` | `e0fbbc8456da57ae…` | **`ea4f1dbcaeee9115…`** |
| `semantic_environment_hash` | `f7def6207f5741d9…` | **`9a2307944b459d6c…`** |
| `prompts` · `analyze_schema` · `synthesis_schema` · `capability` | — | **không đổi** |
| `CACHE_VERSION` | 81 | **81** |
| candidate | `a5b63aa3cb38e81f…` | **`67ad7f4ffb1a97ee…`** |

### `IDENTITY_AND_CACHE_DECISION = KHÔNG BUMP, khoá lại identity`

Cổng `test_cache_identity` nêu đúng hai nhánh: *envelope đã cache CÒN đúng ⇒
chạy lại `lock_cache_identity.py`; KHÔNG còn ⇒ bump*. Ở đây là nhánh đầu, hai
căn cứ:

- Thẻ đổi thứ mô hình **viết ra**, không đổi nghĩa của bất kỳ chương trình nào
  và không lật phán quyết nào. Một envelope đã cache là một mô phỏng đã phục vụ
  với đáp số đúng — nó vẫn đúng dưới thẻ B.
- `main.py:713`/`:748` chỉ cache khi `status == "ok"`. Thẻ B làm **tăng** tỉ lệ
  sinh ra chương trình phục vụ được; nó không biến một `ok` thành một `ok`
  khác. Bản từ chối chưa bao giờ được cache.

`prompts` không đổi — thẻ ghép vào **user message**, không vào `skills/*.md`.

## 11. Gates

| | |
|---|---|
| `test_card_result_type_affordance.py` (MỚI) | **20 passed** · 3 phép tiêm |
| `test_runner_affordance_ab.py` (MỚI) | **18 passed** · provider stub |
| `test_grammar_card.py` | 11 passed (trần 5510 → 5720, phân loại tại chỗ) |
| gold preflight `gold_affordance_ab.py` | 7/7 · exact 7/7 · Scene3D 7/7 · biên PASS |
| full backend pytest | **3821 passed** · 1 skipped · 1 deselected, exit 0 (cây sạch) |
| frontend vitest | **698 passed** / 51 file |
| cache identity | passed · `CACHE_VERSION` 81 → 81 |
| candidate verification | exit **0** — `67ad7f4ffb1a97ee…` |
| `certify_acceptance_runner.py` | exit **0** · 4 nhãn PASS · 2 readiness YES |
| `replay_demo_cases.py` · `audit_demo_crash_surface.py` | 5/5 · 6/6 · ném ra ngoài 0 |
| `git diff --check` | exit **0** |

Frontend chạy dù không file frontend nào đổi: hợp đồng cảnh không đụng tới.

## 12. Giới hạn

**①** `n = 6` cặp. 6/6 so 1/6 và 5–0 là rất sắc, nhưng mẫu nhỏ; đây là tiêu chí
**lựa chọn thay đổi trong development**, **không** phải bằng chứng ổn định.
`STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`.

**②** B gộp ba thành phần (B1, B2, B3) thành **một** ứng viên, đúng theo giới
hạn "mỗi wave thử đúng một ứng viên B". Nên **không quy được** phần thắng cho
riêng thành phần nào. Bằng chứng `dev-v1` (curved_solid dùng được dù không
liệt kê) gợi ý B3 không phải thành phần hoạt động — đó là suy luận, không phải
số đo. Confound này đã khai **trước** lượt đo.

**③** Corpus do tôi viết và nay đã công bố ⇒ **không held-out**.

**④** `e8` không đo được ranh giới xiên vì lỗi ký hiệu chỉ số dưới trong chính
corpus của tôi (§8).

**⑤** Model gọi bằng **alias** `gemini-2.5-flash`, tái lập ở mức `LIMITED`.

**⑥** So sánh với `dev-v1` phải cẩn thận: `dev-v1` đo A trên **corpus khác** và
được 0/6; ở đây A được 1/6. Hai con số **không** cùng mẫu, nên đừng đọc thành
"A tốt lên". Chỉ cặp A/B **trong cùng lượt này** mới so được.

## 13. Khối kết quả

```
BASELINE_CANDIDATE = a5b63aa3cb38e81f…
EXECUTION_CANDIDATE = 67ad7f4ffb1a97ee…
CARD_A_HASH = c7c001c4df7c802a84f52144564c640278b99dc07692f58d583460f52b1701e7  (5472 B)
CARD_B_HASH = 86134034116f9c07fdceccff4d91b4f54adb7f1df70e048dc1eafbd958f23860  (5675 B)
REGISTERED_HYPOTHESIS = thẻ không nói kiểu KẾT QUẢ ⇒ mô hình không nối được
  câu hỏi với `intersect_plane_curved`; nói ra kiểu ra biến việc chọn phép
  thành một phép khớp kiểu
ACTUAL_MODEL_FACING_DELTA = +203 byte: 178 cho `→<kiểu>` trên 17 dòng phép
  (dẫn từ `_CHU_KY` + `_KIEU_DUNG`), 25 cho danh sách kiểu khai được nay dẫn
  xuất (thêm int · circle3 · curved_solid). Thẻ đầy đủ KHÔNG đổi.
PAIRED_CURVED_CASES = 6
A_FIRST_ATTEMPT_OPERATOR_CORRECT = 1/6
B_FIRST_ATTEMPT_OPERATOR_CORRECT = 6/6
PAIRED_WINS = 5        PAIRED_LOSSES = 0
A_FIRST_ATTEMPT_SERVABLE = 0/6
B_FIRST_ATTEMPT_SERVABLE = 3/6   (e1 · e3 · e5)
B_EXACT_MATCH = 3/3 trong các ca served
POLYHEDRAL_CONTROL = PASS (cả hai arm chọn `construct_section`)
NEGATIVE_TARGET_BOUNDARY = NOT_REACHED (cả hai arm; lỗi xuất xứ điểm — §8, §12④)
SELECTOR_GAIN_OBSERVED = YES
CHANGE_ACCEPTED = YES
PRODUCT_VARIANT_AFTER_WAVE = B
MODEL_CALLS_USED = 24 logic / trần 24  (8 analyze + 16 tổng hợp, 0 repair)
TRANSPORT_ATTEMPTS_OBSERVED = 24 / trần 96  (không retry nào)
TOTAL_TOKENS = 136766
IDENTITY_AND_CACHE_DECISION = khoá lại identity, KHÔNG bump — thẻ đổi thứ mô
  hình VIẾT RA, không đổi nghĩa chương trình nào; `main.py` chỉ cache `ok`
CACHE_VERSION_BEFORE/AFTER = 81 / 81
FINAL_CANDIDATE = 67ad7f4ffb1a97ee…
TEST_RESULTS = thẻ 20 · runner 18 · full backend 3821 passed · vitest 698/51
HISTORICAL_ARTIFACTS_CHANGED = NO
PRODUCT_CAPABILITY_CHANGED = NO
STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
WORKING_TREE = CLEAN
COMMITS = 2
RECOMMENDED_NEXT_ACTION = NAMED_POINT_PROVENANCE_AFFORDANCE_ALIGNMENT
```

## 14. Việc kế tiếp

Chọn phép **đã hết là nút thắt** (6/6). Nút thắt nay đo được là **xuất xứ của
điểm có tên** — 4/8 ca hỏng ở đúng chỗ ấy, ba hình dạng khác nhau của cùng một
câu hỏi *"điểm này lấy toạ độ và xuất xứ từ đâu"*:

```
khai point3 mà KHÔNG có giá trị và KHÔNG có câu lệnh dựng   e2, e6
có initial_value mà thiếu source_fact_id                     e7
có initial_value cho một tên grounding không khớp            e8
```

Cộng thêm liên kết tên `analyze`/`synthesis` (`e4`, và `dev-v1` 3/6) — hai
tuyến này nên xử theo thứ tự ấy.

```
RECOMMENDED_NEXT_ACTION = NAMED_POINT_PROVENANCE_AFFORDANCE_ALIGNMENT
```

Chưa đề xuất thiết kế acceptance mới: đường sinh còn ba tầng chặn đã đo được,
và một acceptance chạy trước khi chúng đóng sẽ đo lại đúng chúng.
