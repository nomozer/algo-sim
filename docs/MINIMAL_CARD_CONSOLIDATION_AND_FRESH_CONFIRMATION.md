# MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION

> 2026-09-07. **2 đề MỚI × 2 arm = 4 lượt synthesis.**
> `MEASUREMENT_CLASS = DEVELOPMENT_SYNTHESIS_AB` · `HELD_OUT_CLAIM = NO` ·
> `EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED` · `ANALYZE_CALLS = 0` ·
> `REPAIR_CALLS = 0`.
>
> ```
> CARD_C_ADOPTED = YES        (đủ SÁU điều kiện khoá trước lượt gọi đầu)
> PRODUCT_VARIANT   A → C     CACHE_VERSION 85 → 86
> ```
>
> Đây là wave đầu tiên trong chuỗi **đổi mã sản phẩm**. Ba wave trước đo từng
> mảnh rời và giữ nguyên thẻ; wave này hợp nhất phần đã có bằng chứng, xác
> nhận trên đề chưa từng đo, rồi áp dụng.

## 1. Trạng thái đầu — khớp bàn giao

HEAD `09f5e76` · cây **sạch** · `CACHE_VERSION` **85** · candidate
`36e81713…` (`--verify` exit 0, 90 file) · `PRODUCT_VARIANT` **A**
(`grammar_card("hinh_hoc")` == `card_A.txt`, `c7c001c4…`, 5472 B).

Sáu băm model-facing @ v85: `prompts 55ac1ca6…` · `grammar_card e0fbbc84…` ·
`synthesis_schema 8c57c9de…` · `analyze_schema 515001b5…` ·
`capability 85bd3167…` · `semantic_environment f7def620…`.

⚠️ **Băm thẻ trong báo cáo là bản LF.** File thẻ trên đĩa Windows lưu CRLF, nên
`sha256` của byte thô lệch 52–53 byte so với con số mọi wave công bố. Runner
đọc bằng `read_text` (universal newlines) nên nó luôn băm bản LF; thẻ của wave
này ghi thẳng LF để hai con số về làm một.

## 2. Hai đính chính bộ đo — làm xong TRƯỚC lượt gọi đầu

Cả hai tìm ra bằng **provider stub**, 0 lượt gọi. Artifact nguồn **giữ nguyên
từng byte**; đính chính là artifact riêng, liên kết bằng hash.

### 2a. `REPAIR_PROBE_COUNTER_DECOMPOSITION`

`POINT_INITIALIZATION_REPAIR_EFFICACY` công bố `PHYSICAL_ATTEMPTS = 2` cho một
lượt chỉ phát **một** request. Bộ đếm của probe tăng ở *mọi* lần provider
callable được gọi — kể cả nhánh `n == 0` trả thẳng raw candidate **đọc từ
artifact** (`ghi["physical"] += 1` đặt **trước** `if n == 0`).

Bằng chứng độc lập: telemetry đếm ở tầng transport, không qua bộ đếm probe, và
ghi `calls = 1` · `total_tokens = 3123`. Một ứng viên trả từ file không sinh
token nào.

| | công bố | đúng |
|---|---:|---:|
| `logical_application_calls` | 1 | **1** |
| `physical_api_attempts` | **2** ❌ | **1** |
| `candidate_attempts` | — | **2** |

Thẩm quyền đếm từ nay là **`app.ai.gemini.ApiBudget`** — nó đã tách sẵn
`logical_calls` ↔ `http_requests`, và là chỗ **duy nhất** nhìn thấy vòng retry
bên trong `call_gemini`. `backend/scripts/wave_counters.py` **dẫn xuất** hai
trường ấy bằng `@property` chứ không đếm song song, nên `physical_api_attempts`
**không còn đường nào** để tăng vì một ứng viên đọc từ file. Đó là bằng chứng
**cấu trúc**, không phải lời hứa.

⚠️ **Lỗi ĐẶT TÊN, không phải lỗi số liệu.** Mọi kết luận của wave nguồn —
`SLOT_REPAIRED`, `PROVENANCE_PRESERVED`, `RATIO_PRESERVED`,
`PERMANENT_SLOT_INSTRUCTION_NEEDED = NOT_PROVED` — **không đổi**.

Artifact: `docs/evaluation/geometry/point-initialization-repair-efficacy/COUNTER_CORRECTION.json`.
Khoá: `test_counter_decomposition.py` — **11 pass**, gồm phép tiêm `test_C3`
tái hiện đúng con số `2` đã công bố bằng cách đếm kiểu cũ.

### 2b. `RUNNER_SOURCE_INVARIANT_UNDERBINDING` — cổng không nằm trên đường chạy

Runner A/B chỉ gắn `bat_bien_chia_doan`, **thiếu** `bat_bien_do_dai`; đường sản
phẩm ([analyze_contract.py:545](../backend/app/simulation/semantic_program/analyze_contract.py))
gắn **cả hai**. Nên cổng `segment_length` — cổng bắt toạ độ đầu mút **trái độ
dài đề cho** — **chưa từng chạy** trong hai wave A/B trước, dù đăng ký của
chúng khai là có.

Đúng lớp lỗi mà `CLAUDE.md §2b.1` gọi tên, và cùng họ với `check_volume`,
`s.truc` vs `s.huong_truc`, certifier gọi tắt.

**Tác động lên kết luận cũ: KHÔNG có.** Chấm lại toàn bộ artifact cũ, 0 lượt
gọi — mọi lượt đều khai toạ độ **đúng** độ dài đề cho:

| wave | ca | toạ độ | đề cho | khớp |
|---|---|---|---:|---|
| divide-segment-ratio-ab | r1 | `A=[0,0,0] B=[12,0,0]` | 12 | ✓ |
| divide-segment-ratio-ab | r2 | `C=[0,0,0] D=[10,0,0]` | 10 | ✓ |
| divide-segment-ratio-ab | r3 | `E=[0,0,0] F=[10,0,0]` | 10 | ✓ |
| divide-segment-ratio-ab | r4 | `G=[0,0,0] H=[8,0,0]` | 8 | ✓ |
| ratio-staged-recheck | r2·r3 | — | — | cả 4 lượt chết ở `grounding`, chưa tới tầng này |
| provenance-ab | r2/A · r3/B | `[0,0,0]`,`[10,0,0]` | 10 | ✓ |

Cổng thiếu, nếu có chạy, cũng **PASS** ở mọi lượt. `B_RATIO_SIGNAL` và
`P1_PROVENANCE_SIGNAL` đứng nguyên.

Phép tiêm chứng minh bản sửa (`test_D3`): chương trình đặt `B` tại `[99,0,0]`
trong khi đề nói `AB = 18`, bỏ `source_fact_id` để **grounding không bắt
trước** — trước khi sửa nó đi tới **`served`**; sau khi sửa bị chặn ở
`source_invariant`. Đã chạy cả hai chiều.

## 3. Hai thẻ — delta đúng HAI thay đổi

| | | |
|---|---|---|
| **A0** | thẻ SẢN PHẨM hiện tại, nguyên byte | `c7c001c4…` · 5472 B |
| **C** | A0 + đúng hai hướng dẫn đã có bằng chứng | `ac07f716…` · 5855 B |
| delta | **+383 B** · 1 dòng THÊM + 1 dòng SỬA | |

```diff
@@ memory_declarations[] @@
+  Xuất xứ: khi chọn hệ toạ độ, đặt MỘT điểm đầu vào làm gốc và ghi
+  `model_assumption` nêu lý do chọn; dùng `source_fact_id` cho giá trị lấy
+  thẳng từ đề; điểm mà đề xác định bằng một quan hệ thì phải TẠO bằng câu
+  lệnh dựng, không khai toạ độ.
@@ divide_segment @@
-  ratio:tên
+  ratio:t trong M = a + t(b−a); chia trong đoạn m:n ⇒ t = m/(m+n)
```

✅ **Thẻ C TRÙNG BYTE với `provenance-affordance-ab-4-luot/card_P1.txt`.** Đó
không phải trùng hợp mà là **điều kiện**: thẻ hợp nhất = A0 + ratio +
provenance, và wave provenance đã đo đúng tổ hợp ấy. Dùng nguyên byte **giữ
liền chuỗi bằng chứng**; viết lại bằng chữ khác sẽ tạo một biến thể **thứ ba**
chưa từng đo. (Brief §3 chép dòng provenance có sai khác — mất mệnh đề *"không
khai toạ độ"* — và bản đo được chọn sau khi hỏi lại.)

`responseSchema` **không đổi**: thẻ là văn xuôi, không đi vào JSON schema. Hai
arm dùng cùng `RequestContract`, cùng model, cùng `temperature 0.1`, cùng
runner; payload **chỉ khác** đúng hai dòng trên (khoá bằng stub `test_C2`).

**Thẻ C KHÔNG thêm hướng dẫn về ô `at`** — có chủ đích.
`POINT_INITIALIZATION_REPAIR_EFFICACY` cho thấy vòng sửa **sẵn có** tự đóng lỗ
ấy trong 1 lượt (3123 token), nên `PERMANENT_SLOT_INSTRUCTION_NEEDED =
NOT_PROVED`; gắn một dòng vĩnh viễn vào **mọi** lượt sinh là chi phí chưa
chứng minh được là cần.

## 4. Hai đề MỚI

Chưa xuất hiện trong bất kỳ phép đo A/B nào trước đây (khoá bằng `test_D1`).

| | đề | `t` đúng | đáp số |
|---|---|---|---|
| **F1** | `AB = 18`, `M ∈ AB`, `AM : MB = 5 : 4`. Tính `MB`. | `t(A→B) = 5/9` | `MB = 8` |
| **F2** | `GH = 14`, `K ∈ GH`, `KH = 2·GK`. Tính `KH`. | `t(G→H) = 1/3` | `KH = 28/3` |

`F1` là lớp mà thẻ A **đã sai hai lần** (`2/3` cho `2:3`, `1/4` cho `4·`).
`F2` có **đáp số hữu tỉ không nguyên** — ca duy nhất trong cả chuỗi wave; một
phép làm tròn ẩn không thể đi qua mà không ai thấy.

Bất biến nguồn **dẫn xuất từ chính đường sản phẩm** khớp oracle một cách độc
lập: `segment_division(A,B,M) = 5/9` và `segment_division(G,H,K) = 1/3`.

## 5. Tiền kiểm — 21 pass, 0 lượt gọi

`backend/tests/geometry/test_minimal_card_confirmation_preflight.py` +
`PREFLIGHT.json`. Hai gold viết đúng đặc tả wave (gốc toạ độ đi kênh
`model_assumption`) đi trọn: schema · grounding · **cả hai** bất biến nguồn ·
runtime · postconditions · **đáp số chính xác** (`8` và `28/3`) · điểm dẫn
xuất `origin=derived` + `producer=construct_point.divide_segment` +
`depends ⊇ {hai đầu mút}` · sự kiện sinh điểm trong trace · Scene3D · `served`.

Bốn phản ví dụ đều bị chặn **đúng tầng**, không tầng nào "đỏ nhờ tầng khác":

| phản ví dụ | chặn ở |
|---|---|
| ratio SAI nhưng **trong đoạn** (`1/2` · `1/4`) | `source_invariant` |
| điểm dẫn xuất khai sẵn toạ độ | `grounding` · `DERIVED_ENTITY_WITHOUT_PRODUCER` |
| toạ độ đầu mút **trái** độ dài đề cho | `source_invariant` |
| gốc toạ độ thiếu **cả hai** kênh xuất xứ | `grounding` |
| đảo chiều toán hạng, tỉ lệ tương đương (`4/9` · `2/3`) | **được nhận**, cùng đáp số |

**Nền đỏ đã chứng minh**: đổi `t` của F1 thành `5/8` ⇒ 4 test đỏ, gồm phép kiểm
số học độc lập `test_D2` (`dap = (1−t)·dài`).

Runner chứng minh bằng stub trước lượt live: **23 pass** — một synthesis mỗi
arm · không analyze, không repair · cùng hợp đồng · payload chỉ khác thẻ · gắn
đủ hai bất biến · candidate giữ **trước** khi chấm · đáp số đọc từ
`final_memory` · Scene3D qua đường sản phẩm · lịch đọc từ đăng ký · ngân sách
dừng đúng chỗ · budget toàn cục được trả lại.

`test_F3` là cái đắt nhất: gọi **chính** `call_gemini` với transport giả để
chứng minh bộ đếm **nằm trên đường thật**. Không có nó, `test_F1` chỉ chứng
minh bộ đếm im lặng khi bị bỏ qua — đúng hình dạng của
`V3_LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL`. Lượt live xác nhận: dưới stub
bộ đếm đọc `0/0/4`, chạy thật đọc **`4/4/4`**.

## 6. Bốn lượt live

`ratio_ab_ratio-ab-20260907T021126Z.json` · `RUN_STATUS = COMPLETE` ·
`TOKENS 23 801/30 000`. Lịch xen kẽ đọc từ đăng ký: `f1` A0→C, `f2` C→A0.

| ca | arm | `t` viết | `t` đúng | xuất xứ gốc | stage | servable | đáp số | token |
|---|---|---|---|---|---|---|---|---|
| F1 | A0 | **`ratio_for_M`** | `5/9` | **THIẾU** | `grounding` | False | — | 6624 |
| F1 | **C** | **`5/9`** | `5/9` | `model_assumption` | **`served`** | **True** | **`8`** | 4950 |
| F2 | **C** | **`1/3`** | `1/3` | `model_assumption` | **`served`** | **True** | **`28/3`** | 5541 |
| F2 | A0 | **`1/2`** ✗ | `1/3` | `model_assumption` | `source_invariant` | False | — | 6686 |

**A0 mắc đúng hai lỗi mà hai dòng của C nhắm tới**, mỗi lỗi một ca:

- **F2/A0 — lỗi `ratio`, lần tái hiện THỨ TƯ.** Nhãn của chương trình ghi
  `"Điểm K chia đoạn GH theo tỉ lệ GK:KH = 1:2"` — **đọc đề đúng** — rồi viết
  `ratio: 1/2`. Đúng quy ước `m:n`, sai `t` (`1/(1+2) = 1/3`). Bất biến nguồn
  bắt đúng: *"đề cho GK:KH = 1:2 (t = 1/3), hình dựng có 1:1 (t = 1/2)"*.
- **F1/A0 — lỗi xuất xứ, kèm một đường vòng do chính nhãn cũ mời gọi.** `A` khai
  `[0,0,0]` với **cả hai** ô xuất xứ trống ⇒ `input_not_grounded`. Và nó không
  viết `t` thẳng: nó khai một biến `ratio_for_M = "5/9"` rồi truyền **TÊN** biến
  ấy — tức làm đúng thứ nhãn `ratio:tên` nói là được phép — nên grounding từ
  chối thêm lần nữa vì `5/9` không có trong dữ kiện đề.

Chi tiết thứ hai là bằng chứng **trực tiếp** rằng nhãn cũ không chỉ *thiếu* mà
đang **đánh lạc hướng**: mô hình tính đúng `5/9` rồi vẫn hỏng, vì nó đi theo
đúng thứ thẻ mô tả.

## 7. Ba chiều chấm ĐỘC LẬP

`SCORING.json` — 0 lượt gọi thêm. Provenance chấm từ **raw candidate**, nên nó
độc lập với tầng hỏng phía sau. Tầng chưa chạy ghi `NOT_REACHED`
(`semantic_program` **thuộc** tập này — đính chính của wave provenance).

| | A0 | C |
|---|---:|---:|
| **`t` đúng (Fraction)** | **0/2** | **2/2** |
| *— số học đúng, bỏ qua cách viết* | *1/2* | *2/2* |
| **xuất xứ đúng** | **1/2** | **2/2** |
| **điểm dẫn xuất ĐƯỢC DỰNG** | 2/2 | 2/2 |
| **mô phỏng `served` đúng** | **0/2** | **2/2** |

Ghép cặp trên *`served` đúng*: **C thắng 2 · thua 0 · hoà 0**.
`A0_CORRECT_AND_C_INCORRECT = 0`.

⚠️ Hàng *"số học đúng"* tách riêng vì nó trung thực hơn: F1/A0 **tính** ra
`5/9` nhưng **viết** qua một tham chiếu gián tiếp. Tiêu chí đăng ký là *"đúng
`t` bằng `Fraction`"*, nên nó FAIL — và bộ chấm ghi cả hai con số để người đọc
sau không phải đoán.

`FAILURES_BY_STAGE` = `{A0: {grounding: 1, source_invariant: 1}, C: {}}`.
Cả hai lượt `served` của C có điểm dẫn xuất `origin=derived` · producer
`construct_point.divide_segment` · `depends ⊇ {hai đầu mút}` · Scene3D PASS.

## 8. Token

`total_tokens` lấy **trực tiếp** từ telemetry và **đã gồm** thoughts;
`cached_content` là **thành phần của prompt**, không cộng hai lần.

| | A0 | C |
|---|---:|---:|
| prompt | 6 833 | 7 033 |
| candidates | 1 135 | 1 106 |
| thoughts | **5 342** | **2 352** |
| **cached_content** | **0** | **997** |
| **tổng** | **13 310** | **10 491** |
| token / mô phỏng `served` đúng | **UNDEFINED** (0 ca; tổng 13 310) | **5 246** |
| token / xuất xứ đúng | 13 310 | **5 246** |

⚠️ **So token giữa hai arm BỊ NHIỄU, phải khai.** C nhận **997** token
`cached_content`, A0 nhận **0** — prompt caching phía provider không được kiểm
soát trong thiết kế này. Nên chênh lệch tổng (13 310 vs 10 491) **không** quy
hết cho delta thẻ được, dù chiều của nó thuận. Phần chênh lớn nhất nằm ở
**thoughts** (`5 342` vs `2 352`): A0 "nghĩ" nhiều hơn gấp đôi và vẫn hỏng cả
hai ca. Kết luận ở **mức quan sát**; chưa có đơn giá provider ⇒ **không** nói
gì về tiền.

Con số dùng được là **`5 246` token cho một mô phỏng phục vụ đúng của C**, đặt
cạnh **`UNDEFINED` của A0** — tức A0 tiêu 13 310 token mà không cho mô phỏng
đúng nào.

## 9. Áp dụng — sáu điều kiện, khoá TRƯỚC lượt gọi đầu

```
C_RATIO_CORRECT            = 2/2   ✅
C_PROVENANCE_CORRECT       = 2/2   ✅
C_DERIVED_POINT_CONSTRUCTED= 2/2   ✅
C_CORRECT_SERVABLE         = 2/2   ✅
A0_CORRECT_AND_C_INCORRECT = 0     ✅
GOLD_AND_REGRESSION_GATES  = PASS  ✅
⇒ CARD_C_ADOPTED = YES
```

Bảy bước đã làm đủ:

1. **Hai dòng vào thẩm quyền sinh thẻ** — `grammar_card.py`: `ratio` vào
   `_VAN_XUOI`, và hằng `_DONG_XUAT_XU` chèn sau khối `memory_declarations[]`.
   ✅ Thẻ sản phẩm sinh ra **TRÙNG BYTE** với thẻ đã đo (`ac07f716…`, 5855 B) —
   bản áp dụng đúng bằng bản đo, không phải bản viết lại.
2. **Trần thẻ** `5510 → 5900`, kèm phân loại thẳng thắn: `+60` là **sửa nhãn
   sai** (cùng loại ba lần nâng trước), `+323` là **văn xuôi viết tay**.
3. **Sáu băm model-facing đo lại** — đúng **một** thành phần đổi:
   `grammar_card e0fbbc84… → 9685b06a…`, `semantic_environment f7def620… →
   2178b6d4…`. `prompts` · `synthesis_schema` · `analyze_schema` · `capability`
   **không đổi một byte**.
4. **`CACHE_VERSION` 85 → 86**, bốn cổng cùng commit (`main.py` ·
   `test_api.py` · bảng danh tính `CURRENT_STATE.md` ·
   `test_evaluation_candidate.py`) + làm mới `cache_identity.lock.json`.
5. **Đóng băng lại candidate** ở commit riêng: `36e81713… → 138db7b1…`, 90 file.
6. **Cổng bắt buộc** — §11.
7. `CARD_C_ADOPTED = YES`.

### 9a. Một dòng văn xuôi viết tay — ngoại lệ, và cái giá của nó

Mọi lần nâng trần thẻ trước đây đều tự khai *"không một câu văn xuôi viết tay
nào"*, vì thẻ sinh từ `contract.py` là thứ giữ nó khỏi trôi khỏi hợp đồng.
Dòng `Xuất xứ:` **phá lệ ấy**, và ghi ra đây để lần sau không ai coi là bình
thường.

Lý do nhận: ba ô liên quan (`initial_value`, `source_fact_id`,
`model_assumption`) **đều đã có tên** trong thẻ. Thứ thiếu không phải *tên ô*
mà là *quan hệ giữa chúng* — khi nào dùng ô nào — và quan hệ ấy không thuộc
`Field.description` của bất kỳ trường đơn lẻ nào, nên **không sinh được từ
nguồn**.

Cái giá: `test_dong_xuat_xu_la_quy_tac_CHUNG` cấm mọi tên điểm, fact id, đáp
số hay tên đoạn của bất kỳ ca đo nào lọt vào dòng ấy. Một dòng viết tay chỉ
được ở lại chừng nào nó còn là **luật**, không phải **ví dụ**.

### 9b. Nợ đã biết — bỏ nhãn `tên` của `ratio`

Nhãn mới thay hẳn `tên`, nên mô hình **không còn đọc thấy** rằng ô `ratio` cũng
nhận một tên biến. Đo được thì đường ấy đang **hại nhiều hơn lợi** — nó là
nguyên nhân duy nhất làm hỏng F1/A0 — nhưng `n = 2` chưa đủ để nói nó vô dụng.
Nếu sau này cần cả hai, chỗ sửa là **ghép `tên` vào chính dòng ấy**, không phải
dựng một bảng nhãn thứ hai (`grammar_card` đã ghi nợ này tại chỗ).

## 10. Bốn guard ghim `PRODUCT_VARIANT = A` — đỏ đúng chức năng

Đổi biến thể làm bốn guard đỏ. Chúng **làm đúng việc của mình**; bản cập nhật
giữ nguyên **ý định**, chỉ đổi bản tham chiếu:

| guard | ý định giữ nguyên |
|---|---|
| `test_I2_…` (obligation container) | thẻ sản phẩm phải trùng byte một bản ĐÃ ĐO |
| `test_AB1_…` (point init) | như trên, **và** bản A cũ vẫn tái lập được |
| `test_CA2_…` (point init) | băm môi trường khớp khoá; nay khoá luôn **bốn** thành phần không đổi |
| `test_E8_…` (runner affordance) | phép đo không phụ thuộc biến thể hiện hành |

⚠️ `test_E8` lộ ra một điều đáng ghi: nó kết bằng
`assert grammar_card("hinh_hoc") == a`, tức **khẳng định ngược chính docstring
của nó** (*"không phụ thuộc biến thể sản phẩm hiện hành"*). Nó buộc phép đo vào
biến thể đang chạy, và chỉ lộ ra khi biến thể đổi. Bản mới khẳng định đúng thứ
docstring nói: thẻ sản phẩm **không cần** trùng arm nào trong hai.

## 11. Cổng đã chạy

| cổng | kết quả | mới / kế thừa |
|---|---|---|
| tiền kiểm wave | **21 pass**, 0 lượt gọi | **mới** |
| bộ đếm ba trường | **11 pass**, 0 lượt gọi | **mới** |
| runner stub | **23 pass**, 0 lượt gọi | **mới** |
| thẻ văn phạm | **12 pass** (gồm guard quy-tắc-chung mới) | **mới** |
| `pytest -q` (cây sạch sau commit) | **4094 pass**, 1 skip, 1 deselect, **0 đỏ** | **mới** |
| `vitest run` | **698 pass / 51 file** | **mới** |
| `npm run build` (`tsc -b`) | **PASS** | **mới** |
| `replay_demo_cases.py` | **5/5**, `REDUCED_CHAIN 1/1` | **mới** |
| `audit_demo_crash_surface.py` | **6/6 biên**, ném **0** | **mới** |
| `lock_cache_identity.py --verify` | **exit 0** @ v86 | **mới** |
| `freeze_evaluation_candidate --verify` | **exit 0**, 90 file, `138db7b1…` | **mới** |
| `git diff --check` | sạch | **mới** |

⚠️ Trước commit có **2 đỏ**, cả hai là khoá **cây sạch**
(`test_holdout_readiness_7b`, `test_candidate_ghi_dung_commit_va_cay_sach`) —
`cay_sach: False`, đúng hiện tượng mà wave trước đã ghi lại. Cả hai tự xanh sau
commit; lượt chạy 4094 ở trên xác nhận.

## 12. Báo cuối

```
APPLICATION_LLM_CALLS = 4      ANALYZE_CALLS   = 0
SYNTHESIS_CALLS       = 4      REPAIR_CALLS    = 0
LOGICAL_APPLICATION_CALLS = 4  PHYSICAL_API_ATTEMPTS = 4  CANDIDATE_ATTEMPTS = 4
  (retry_requests 0 · tu_artifact 0 — chuan REPAIR_PROBE_COUNTER_DECOMPOSITION)
TOKEN_BUDGET / TOTAL_TOKENS_USED = 30 000 / 23 801

A0_RATIO_CORRECT / C_RATIO_CORRECT               = 0/2 · 2/2
  (so hoc, bo qua cach viet)                     = 1/2 · 2/2
A0_PROVENANCE_CORRECT / C_PROVENANCE_CORRECT     = 1/2 · 2/2
A0_DERIVED_POINT_CONSTRUCTED / C_…               = 2/2 · 2/2
A0_CORRECT_SERVABLE / C_CORRECT_SERVABLE         = 0/2 · 2/2
PAIRED_WINS / LOSSES / TIES  (C, truc served)    = 2 · 0 · 0
A0_CORRECT_AND_C_INCORRECT                       = 0

A0_TOTAL_TOKENS / C_TOTAL_TOKENS       = 13 310 · 10 491
TOKENS_PER_CORRECT_SERVABLE            = A0 UNDEFINED (0 ca) · C 5 246
CACHE_TOKEN_DISTRIBUTION               = A0 0 · C 997   ⚠️ CO NHIEU CACHE
FAILURES_BY_STAGE = {A0: {grounding: 1, source_invariant: 1}, C: {}}

CARD_C_ADOPTED                   = YES
PRODUCT_VARIANT_BEFORE_AFTER     = A → C
MODEL_FACING_HASHES_BEFORE_AFTER = grammar_card  e0fbbc84 → 9685b06a
                                   semantic_env  f7def620 → 2178b6d4
                                   prompts · synthesis_schema · analyze_schema
                                   · capability = KHONG DOI mot byte
CACHE_VERSION_BEFORE_AFTER       = 85 → 86  (bon cong cung commit)
CANDIDATE_HASH_BEFORE_AFTER      = 36e81713… → 138db7b1…  (dong bang lai)
PRODUCT_CAPABILITY_CHANGED       = NO
  (IR khong mo them phep nao; chi doi thu MO HINH DOC THAY)

TEST_RESULTS = pytest 4094 pass · 1 skip · 1 deselect · 0 do
               vitest 698/51 · build PASS · replay 5/5 · crash 6/6
COMMITS      = 3   WORKING_TREE = sach
RECOMMENDED_NEXT_ACTION = CURVED_END_TO_END_FRESH_CONFIRMATION
```

## 13. Giới hạn bằng chứng

- **`n = 2` cặp.** `DEVELOPMENT_SIGNAL`, không phải ước lượng tổng thể.
  `CAUSAL_ATTRIBUTION = LIMITED`.
- **Delta GỘP.** Thẻ C mang **hai** thay đổi cùng lúc, nên kết quả 2/2 **không
  tách được** dòng nào đóng góp bao nhiêu. Hai wave trước đã đo riêng từng dòng
  (`B_RATIO_SIGNAL = POSITIVE`, `P1_PROVENANCE_SIGNAL = POSITIVE`); wave này đo
  **bản hợp nhất**. Ghép ba lượt lại thì mỗi dòng có tín hiệu riêng của nó,
  nhưng đó là **ba phép đo nhỏ**, không phải một phép đo lớn.
- **Hai ca mới tạo `development confirmation`**, chúng **không** chứng minh
  `stability` hay đủ điều kiện chuyển họ hình sang `supported`.
  `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`.
- **Cả hai đề cùng một họ** — điểm chia đoạn thẳng, đáp số là một độ dài. Wave
  này **không** nói gì về hình cong, thiết diện, hay bất kỳ họ nào khác.
- `gemini-2.5-flash` là **alias, không phải snapshot** ⇒ `reproducibility =
  LIMITED`.
- **Token so ở mức quan sát**, và lượt này **có nhiễu cache** (§8).
- Ba mức bằng chứng **không trộn**: *"đáp số đúng"* · *"có bước dựng đúng"* ·
  *"AI tự sinh ổn định"* (**chưa đo**).

**Việc kế tiếp: `CURVED_END_TO_END_FRESH_CONFIRMATION`.** Chọn từ chính giới
hạn ở trên. Thẻ vừa đổi và `CACHE_VERSION` vừa bump, nên thứ chưa ai biết là
**thẻ mới cư xử thế nào ngoài họ đoạn thẳng** — và đường sản phẩm thật có
`analyze` cùng vòng sửa, hai tầng mà bốn lượt vừa rồi **cố ý** không chạy
(`ANALYZE_CALLS = 0`, `REPAIR_CALLS = 0`). Một phép xác nhận **nhỏ**,
end-to-end, trên bài hình **cong** mới, có analyze và repair như sản phẩm thật.
Sau đó mới tới việc bổ sung họ hình còn thiếu.

⚠️ Token của Claude Code **không** tính vào token vận hành AlgoSim; replay,
checker và Scene3D không dùng token Gemini.
