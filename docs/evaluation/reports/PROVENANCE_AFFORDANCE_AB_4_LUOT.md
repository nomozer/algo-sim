# PROVENANCE_AFFORDANCE_AB_4_LUOT

> 2026-09-07. **2 đề × 2 arm = 4 lượt synthesis.**
> `MEASUREMENT_CLASS = DEVELOPMENT_SYNTHESIS_AB` · `HELD_OUT_CLAIM = NO` ·
> `ANALYZE_CALLS = 0` · `REPAIR_CALLS = 0`. **Không đụng một dòng mã sản phẩm
> nào.** Thẻ sản phẩm giữ **A** trong suốt.
>
> ```
> P1_PROVENANCE_SIGNAL = POSITIVE   (P1 2/2 · P0 1/2, không ca nào P0 đúng/P1 sai)
> P1_SERVABLE_SIGNAL   = NEUTRAL    (1/2 mỗi arm, ghép cặp 1 thắng 1 thua)
> ```

## 1. Trạng thái đầu — khớp bàn giao

HEAD `4877db5` · cây **sạch** · `CACHE_VERSION` **85** · candidate
`36e81713…` (`--verify` exit 0, 90 file) · `PRODUCT_VARIANT` **A**
(`grammar_card` == `card_A.txt`, `c7c001c4…`).

Sáu băm model-facing @ v85: `prompts 55ac1ca6…` · `grammar_card e0fbbc84…` ·
`synthesis_schema 8c57c9de…` · `analyze_schema 515001b5…` ·
`capability 85bd3167…` · `semantic_environment f7def620…`.

Thẻ nền `card_B` của lượt ratio: `25d43370…` (5532 B) — bản đã đo **ratio đúng
2/2**. Runner `3d9eb9c8…` · gold `d53b23f6…` (băm trước khi wave sửa runner).

## 2. Tiền kiểm nền đo — 17 pass, 0 lượt gọi

`backend/tests/geometry/test_provenance_ab_preflight.py`

Hai gold viết **đúng đặc tả wave** (gốc toạ độ đi kênh `model_assumption`,
khác gold của corpus vốn dùng `source_fact_id`):

| gold | đi trọn |
|---|---|
| RATIO `divide_segment(C,D,2/5)` | `served` · **`ND = 6`** |
| MULTIPLE `divide_segment(E,F,1/5)` | `served` · **`PF = 8`** |

Cả hai đạt: grounding · source invariants · runtime · postconditions · exact ·
Scene3D · `served`; điểm dẫn xuất có `origin = derived`, producer
`construct_point.divide_segment`, `depends ⊇ {hai đầu mút}`, và **sự kiện sinh
điểm có trong trace**.

Bốn phản ví dụ — bốn cổng dựng qua ba wave trước — **đều còn chặt**:

| phản ví dụ | bị chặn ở |
|---|---|
| gốc toạ độ có `initial_value`, thiếu **cả hai** kênh xuất xứ | `grounding` |
| `model_assumption` gắn vào **điểm dẫn xuất** + khai thẳng toạ độ | `grounding` · `DERIVED_ENTITY_WITHOUT_PRODUCER` |
| toạ độ **trái độ dài đề cho** | `source_invariant` |
| ratio **sai trong đoạn** | `source_invariant` |

Thêm: đảo chiều toán hạng vẫn được nhận (`3/5`, `4/5`) — nếu nền đo không nhận
cách dựng tương đương thì nó sẽ chấm oan lượt live.

## 3. Hai arm — chỉ khác **một dòng**

| | |
|---|---|
| **P0** | `card_B` của lượt ratio, **nguyên byte** (`25d43370…`, 5532 B) |
| **P1** | P0 + **đúng một dòng** hướng dẫn provenance (`ac07f716…`, 5855 B) |
| delta | **+323 byte · 1 dòng** |

```
Xuất xứ: khi chọn hệ toạ độ, đặt MỘT điểm đầu vào làm gốc và ghi
`model_assumption` nêu lý do chọn; dùng `source_fact_id` cho giá trị lấy thẳng
từ đề; điểm mà đề xác định bằng một quan hệ thì phải TẠO bằng câu lệnh dựng,
không khai toạ độ.
```

Quy tắc **chung**: không tên điểm, không fact id, không đáp số, không cách giải
của hai ca đo. `responseSchema`, RequestContract, model và tham số sinh **y
hệt** giữa hai arm; payload chỉ khác đúng dòng này (`test_F2` khoá bằng stub).

⚠️ **P0/P1 là biến thể THỬ NGHIỆM của wave**, không phải product variant.
Runner nay đọc `card_P0.txt`/`card_P1.txt` và ghi `arm_labels` vào manifest —
dùng lại chữ `A` khi sản phẩm cũng đang là biến thể `A` là cách chắc chắn để
người đọc sau hiểu nhầm.

## 4. Đăng ký và ngân sách

`docs/evaluation/geometry/provenance-affordance-ab-4-luot/registration.json`,
chốt **trước lượt gọi đầu tiên**: băm đề · contract · hai thẻ · runner · model
identity · `temperature 0.1` · `transport_max_attempts` · lịch · trần lượt ·
trần token · tiêu chí chấm · luật kết luận.

**Lịch đọc từ đăng ký, không từ `lich_chay`.** `lich_chay` luân phiên theo chỉ
số trong CORPUS đầy đủ; khi wave chỉ chạy một tập con thì chỉ số ấy không còn
là thứ tự thật. Runner nay đọc lịch từ `registration.json` (`test_F1`):

```
RATIO     P0 → P1
MULTIPLE  P1 → P0
```

Ngân sách: `TOKEN_PER_CALL = 7 500` ⇒ trần lượt chạy **30 000**, và guard **dự
trữ đủ cả cặp** trước khi bắt đầu ca. Thực dùng **22 982 / 30 000** ·
`LOGICAL 4/4` · `PHYSICAL 4/32` · `RUN_STATUS = COMPLETE`.

Runner đã chứng minh bằng stub trước lượt live (`test_runner_ratio_ab`,
**25 pass**, 0 lượt gọi): một synthesis mỗi arm · cùng contract · chỉ thay thẻ ·
gắn `source_invariants` như đường sản phẩm · đáp số từ `outcome.final_memory` ·
Scene3D qua `pipeline._dung_scene3d` · giữ raw candidate và telemetry trước khi
chấm · đếm cả logical lẫn physical · dừng đúng giới hạn.

## 5. Kết quả bốn lượt

`ratio_ab_ratio-ab-20260906T210900Z.json` · `SCORING.json`

| ca | arm | provenance | kênh gốc | ratio | grounding | src-inv | post | scene | served | stage | token |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RATIO | **P0** | **PASS** | `source_fact_id` | PASS | PASS | PASS | PASS | PASS | **True** | `served` | 5907 |
| RATIO | **P1** | **PASS** | `model_assumption` | PASS | NOT_REACHED | NOT_REACHED | NOT_REACHED | NOT_REACHED | False | **`semantic_program`** | 5023 |
| MULTIPLE | **P0** | **FAIL** | **THIẾU** | PASS | **FAIL** | NOT_REACHED | NOT_REACHED | NOT_REACHED | False | **`grounding`** | 5182 |
| MULTIPLE | **P1** | **PASS** | `model_assumption` | PASS | PASS | PASS | PASS | PASS | **True** | `served` | 6870 |

**Hai lượt hỏng, hai trục KHÁC NHAU** — đây là điểm đọc chính:

- **P0/MULTIPLE hỏng đúng trục wave đo.** Raw candidate:
  `declare_point E at=[0,0,0]` với **cả `source_fact_id` lẫn `model_assumption`
  đều trống** ⇒ `input_not_grounded`. Đúng lỗi mà hướng dẫn P1 nhắm tới.
- **P1/RATIO hỏng ở một trục KHÔNG liên quan.** Raw candidate đặt `at` vào
  **`memory_declarations`** thay vì `declare_point`:

  ```
  memory_declarations[0].at: khoá này không có trong `memory_declarations[]`
  — `at` là trường của `declare_point`…
  ```

  Đây là **lớp lỗi `at`** mà `POINT_INITIALIZATION_CONTRACT_ALIGNMENT` đã đóng,
  và chẩn đoán chính xác của wave ấy đã phát đúng. Về **provenance**, ứng viên
  ấy làm **đúng**: `C` có `model_assumption`, `D` có `source_fact_id`, `N` được
  **dựng** bằng `divide_segment(C,D,2/5)`.

## 6. Ba chiều chấm độc lập

| | P0 | P1 |
|---|---:|---:|
| **provenance đúng** | **1/2** | **2/2** |
| grounding pass | 1/2 | 1/2 *(ca kia `NOT_REACHED`)* |
| ratio đúng (`Fraction`) | **2/2** | **2/2** |
| điểm dẫn xuất **được dựng** | **2/2** | **2/2** |
| mô phỏng `served` đúng (đáp số + scene) | **1/2** | **1/2** |

Ghép cặp trên *`served` đúng*: **P1 thắng 1 · thua 1 · hoà 0**.

⚠️ **Đính chính bộ chấm, khai trước khi dùng số.** Bản đầu chấm
`GROUNDING_RESULT = PASS` cho lượt dừng ở `semantic_program` — tức chấm PASS
cho một tầng **chưa bao giờ chạy**. Đã sửa (`semantic_program` nay thuộc tập
`NOT_REACHED`) và **chấm lại artifact cũ, 0 lượt gọi thêm**. Đính chính đổi
`P1 grounding` từ 2/2 xuống **1/2**; nó **không** đổi kết luận provenance, vì
provenance chấm từ raw candidate chứ không từ stage.

## 7. Token

`total_tokens` lấy **trực tiếp** từ telemetry và **đã gồm** thoughts;
`cached_content` là **thành phần của prompt**, không cộng hai lần.

| | P0 | P1 |
|---|---:|---:|
| prompt | 6 883 | 7 033 |
| candidates | 1 052 | 1 091 |
| thoughts | 3 154 | 3 769 |
| **cached_content** | **0** | **0** |
| **tổng** | **11 089** | **11 893** |
| token / provenance đúng | 11 089 | **5 946** |
| token / mô phỏng `served` đúng | **11 089** | **11 893** |

`CACHE_TOKEN_DISTRIBUTION`: **0 cho cả hai arm** — khác lượt trước (A nhận
2 989, B nhận 0), nên lần này **không có nhiễu cache** trong phép so tổng.

Chênh `+804` token của P1 nằm chủ yếu ở **thoughts** (`+615`), prompt chỉ
`+150` (khớp thẻ dài hơn 323 byte). Kết luận ở **mức quan sát**: phép đo này ưu
tiên **giảm số lượt sinh hỏng**, và bằng chứng về **tiền** cần thêm đơn giá
provider — chưa có.

## 8. Kết luận theo luật đã đăng ký

```
P1_PROVENANCE_SIGNAL = POSITIVE
   P1 2/2 · P0 1/2 · KHÔNG ca nào P0 đúng mà P1 sai  → thoả đúng luật
P1_GROUNDING_SIGNAL  = NEUTRAL   (1/2 mỗi arm; ca còn lại của P1 NOT_REACHED)
P1_SERVABLE_SIGNAL   = NEUTRAL   (1/2 mỗi arm; ghép cặp 1 thắng 1 thua)
P1_TOKEN_SIGNAL      = NEUTRAL-nghiêng-ÂM ở mức QUAN SÁT
   token/served đúng: P0 11 089 · P1 11 893 (cả hai mẫu số = 1, cache = 0)
   token/provenance đúng: P0 11 089 · P1 5 946
CAUSAL_ATTRIBUTION   = LIMITED (2 cặp)
STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
```

Nhánh áp dụng của §9 là nhánh thứ tư: **P1 giúp đúng trục provenance nhưng
lượt còn lại hỏng ở một TẦNG MỚI** (`semantic_program`, ô `at` đặt sai chỗ).
Ghi rõ tầng mới, và **giữ kết luận provenance độc lập** — đúng như luật đã
đăng ký.

**Không đóng băng P1 thành ứng viên.** Điều kiện là *2/2 provenance **và** 2/2
mô phỏng đúng*; P1 đạt vế đầu, **không** đạt vế sau. `PRODUCT_VARIANT` giữ
**A** tại cuối wave, đúng cam kết.

⚠️ **`HYPOTHESIS`** — chưa có phép đo phân biệt: dòng hướng dẫn nêu hai trường
**của khai báo** (`model_assumption`, `source_fact_id`), nên nó **có thể** đã
kéo mô hình đặt luôn `at` vào khai báo ở P1/RATIO. Bằng chứng ngược: P1/MULTIPLE
**không** mắc lỗi ấy. `n = 2` không tách được giả thuyết này khỏi nhiễu lấy mẫu.

## 9. Phạm vi và cổng

**Không đổi mã sản phẩm** — preflight không phát hiện lỗi sai nào cần sửa.
Thay đổi nằm ở **bộ đo** (`backend/scripts`, `backend/tests`, ngoài
`MEASURED_SYSTEM_PATHS`): nhãn arm đọc từ file · lịch đọc từ đăng ký · đính
chính tầng `NOT_REACHED` trong bộ chấm.

| cổng | kết quả | mới / kế thừa |
|---|---|---|
| tiền kiểm wave | **17 pass**, 0 lượt gọi | **mới** |
| test runner A/B (stub) | **25 pass**, 0 lượt gọi | **mới** |
| grounding · source invariant · derived-point | trong các suite trên | **mới** |
| `pytest -q` (cây cuối) | **4018 pass**, 1 skip, 1 deselect, **0 đỏ** | **mới** |
| `replay_demo_cases.py` | **5/5**, `REDUCED_CHAIN 1/1` | **mới** |
| `audit_demo_crash_surface.py` | **6/6 biên**, ném **0** | **mới** |
| `freeze_evaluation_candidate --verify` | **exit 0**, 90 file | **mới** |
| `git diff --check` | sạch | **mới** |
| vitest · `npm run build` | — | **kế thừa** (frontend không đụng) |

## 10. Báo cuối

```
APPLICATION_LLM_CALLS = 4    ANALYZE_CALLS = 0
SYNTHESIS_CALLS       = 4    REPAIR_CALLS  = 0
LOGICAL_CALLS / PHYSICAL_ATTEMPTS = 4 / 4
TOKEN_BUDGET / TOTAL_TOKENS_USED  = 30 000 / 22 982

P0_PROVENANCE_CORRECT / P1_PROVENANCE_CORRECT       = 1/2 · 2/2
P0_GROUNDING_PASS / P1_GROUNDING_PASS               = 1/2 · 1/2
P0_RATIO_CORRECT / P1_RATIO_CORRECT                 = 2/2 · 2/2
P0_DERIVED_POINT_CONSTRUCTED / P1_…                 = 2/2 · 2/2
P0_CORRECT_SERVABLE / P1_CORRECT_SERVABLE           = 1/2 · 1/2
PAIRED_WINS / LOSSES / TIES  (P1, trục served đúng) = 1 · 1 · 0

P0_TOTAL_TOKENS / P1_TOTAL_TOKENS      = 11 089 · 11 893
P0_TOKENS_PER_CORRECT_SERVABLE         = 11 089
P1_TOKENS_PER_CORRECT_SERVABLE         = 11 893
CACHE_TOKEN_DISTRIBUTION               = P0 0 · P1 0  (khong nhieu cache)

FAILURES_BY_STAGE_AND_ARM = {P0: {grounding: 1}, P1: {semantic_program: 1}}
TRACE_AND_SCENE_RESULTS   = ca `served` cua ca hai arm deu co diem dan xuat
                            origin=derived · producer=construct_point.
                            divide_segment · depends ⊇ hai dau mut · Scene3D PASS

PRODUCT_VARIANT_BEFORE_AFTER    = A → A
MODEL_FACING_HASHES_BEFORE_AFTER= KHONG DOI ca sau
CACHE_VERSION_BEFORE_AFTER      = 85 → 85 (khong bump: khong doi phan quyet)
CANDIDATE_HASH_BEFORE_AFTER     = 36e81713… → 36e81713… (khong dong bang lai)
PRODUCT_CAPABILITY_CHANGED      = NO
TEST_RESULTS = 4018 pass · 1 skip · 1 deselect · 0 do
COMMITS = 1        WORKING_TREE = sach
RECOMMENDED_NEXT_ACTION = PROVENANCE_INSTRUCTION_SLOT_DISAMBIGUATION
```

## 11. Giới hạn bằng chứng

- **`n = 2` cặp.** Mọi tín hiệu là **development signal**, không phải ước
  lượng tổng thể. `CAUSAL_ATTRIBUTION = LIMITED`.
- **Provenance chấm từ raw candidate**, nên nó **độc lập** với tầng hỏng phía
  sau — đó là chủ đích, và cũng là lý do `P1_PROVENANCE_SIGNAL` đứng vững dù
  P1/RATIO không `served`.
- Ba mức bằng chứng **không trộn**: *"đáp số đúng"* · *"có bước dựng đúng"* ·
  *"AI tự sinh ổn định"* (**chưa đo** — `STABILITY_UNDER_ACCEPTANCE`).
- Token so ở **mức quan sát**; chưa có đơn giá provider nên **không** kết luận
  gì về tiền.

**Việc kế tiếp: `PROVENANCE_INSTRUCTION_SLOT_DISAMBIGUATION`.** Chọn từ kết
quả thực tế: hướng dẫn provenance **đạt** mục tiêu của nó (2/2), nhưng lượt
hỏng duy nhất của P1 là **đặt `at` sai ô** — và dòng hướng dẫn hiện nói về hai
trường *của khai báo* mà **không** nói toạ độ thuộc ô nào. Delta kế tiếp vì thế
là **một dòng, chỉ làm rõ ô chứa toạ độ**, đo **riêng**, lại theo bậc 2 ca × 2
arm. Nếu nó đóng được lỗ `at` thì P1 mới có cơ hội đạt **2/2 mô phỏng đúng** —
điều kiện để đóng băng ứng viên.

⚠️ Token của Claude Code **không** tính vào token vận hành AlgoSim; replay,
checker và Scene3D không dùng token Gemini.
