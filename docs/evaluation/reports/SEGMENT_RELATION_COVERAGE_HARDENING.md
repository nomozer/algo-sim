# SEGMENT_RELATION_COVERAGE_HARDENING

> 2026-09-06. **`APPLICATION_LLM_CALLS = 0`** — replay, fixture và phép tiêm.
> Không mở năng lực toán học, không đổi kernel, không đổi bề mặt mô hình.
>
> ```
> e4 t=1/2  TRƯỚC: served, bán kính 21/2   SAU: từ chối ở source_invariant
> CACHE_VERSION 82 → 83 (BUMP)             CANDIDATE 1151bc6f… → 179793db…
> ```

## 0. Đính chính hai điều trong bàn giao

**① Con số test.** Bàn giao ghi *"tài liệu đính kèm ghi 3922 passed"*. Không
còn đúng: commit `22b4b4e` đã sửa cả ba chỗ về **3923**, và `grep` xác nhận
không còn `3922` nào trong `docs/`. Đo lại ở mốc bàn giao: **3923 passed**.
Từ wave này trở đi tài liệu chỉ ghi **một** con số, đo trên cây **cuối cùng**.

**② Từ vựng.** Wave trước viết *"fail-closed theo hướng bỏ sót"* cho lối nói
mà bộ đọc không hiểu. Cách nói ấy **sai**, vì hệ không hề chặn gì cả. Từ vựng
dùng thống nhất từ đây, và ba trạng thái **không được gộp**:

| trạng thái | nghĩa | hệ có chặn `served` không |
|---|---|---|
| **COVERED** | phát được bất biến, checker phán trên hình | có, khi **VIOLATED** |
| **VIOLATED** | tính được `t`, hình dựng không khớp | **CÓ** |
| **NOT_CHECKABLE** | thấy quan hệ nhưng không giải được `t` | **CÓ** (mới, §4) |
| **NOT_EXTRACTED** | không đủ tín hiệu để nói có quan hệ | **KHÔNG** — giữ hành vi cũ |

*"Fail-closed"* chỉ được dùng cho hai hàng giữa.

## 1. Vì sao `e4` chưa phát invariant

Đề `e4`, nguyên văn phần liên quan:

> *"… chiều cao **PQ bằng 28** … Một mặt phẳng vuông góc với PQ **cắt PQ tại
> điểm T** sao cho **PT bằng 20**, tính từ đỉnh P."*

Bộ đọc bản đầu gộp neo và quan hệ vào **một** mẫu — *"M nằm trên đoạn AB **sao
cho** ‹quan hệ›"*. Ba thứ lệch cùng lúc:

| | `r1`–`r4` (đọc được) | `e4` (trượt) |
|---|---|---|
| neo | *"M nằm trên đoạn AB"* | *"**cắt** PQ **tại** điểm T"* |
| từ nối | `=` | **"bằng"** |
| độ dài cả đoạn | cùng câu (*"đoạn AB có độ dài 12"*) | **câu khác** (*"chiều cao PQ bằng 28"*) |

Gộp một mẫu thì mỗi lối nói mới lại phải thêm một mẫu — đúng thứ *"bảng liệt
kê tay sẽ lặng lẽ bỏ sót lớp mới"* mà kho này đã dọn ba lần. Nên **tách hai
pha** thay vì thêm mẫu.

## 2. Ba replay — trước và sau

`docs/evaluation/geometry/segment-relation-coverage/REPLAY_E4_{TRUOC,SAU}.json`
(chương trình **nguyên văn** của `e4`, `sha256` nguồn ghi trong artifact).

| replay | TRƯỚC | SAU |
|---|---|---|
| ① `divide_segment(P,Q,5/7)` | `served` · **15** · scene 12 | `served` · **15** · scene 12 |
| ② `divide_segment(P,Q,1/2)` | **`served`** · **21/2** · scene 12 | **`source_invariant`** · `VIOLATED` |
| ③ `divide_segment(Q,P,2/7)` | `served` · 15 · scene 12 | `served` · 15 · scene 12 |

**Replay ② là phản ví dụ chính.** `t = 1/2` đặt `T` **bên trong** khối, nên
kernel dựng được thiết diện thật và checker đo đúng bán kính `21/2` của nó —
mọi tầng làm đúng việc của mình, và đáp số vẫn sai. Lời từ chối mới:

```
cắt PQ tại điểm T — PT = 20: đề cho PT:TQ = 5:2 (t = 5/7),
hình dựng có 1:1 (t = 1/2); điểm sai: T (nguồn: mat_phang_cat_pq_tai_t)
```

Replay ③ chứng minh chiều ngược lại: `(Q,P,2/7)` dựng **đúng cùng một `T`**
(`z = 8`), và nó **không** bị bác — phép kiểm đọc **hình**, không đọc chuỗi
`ratio`.

## 3. Bộ phát hai pha

Thẩm quyền vẫn là `segment_relation.bat_bien_chia_doan`; không dựng cái thứ hai.

```
① NEO      → bộ ba (A, B, M)
② QUAN HỆ  → tìm trên TOÀN BỘ đề + mọi InputFact, chỉ nhận mảnh nói đúng
             hai đoạn con của bộ ba ấy
③ ĐỘ DÀI   → |AB| tìm cùng cách, khi quan hệ là độ dài một nhánh
```

Luật ghép là **"cùng xác định một bộ ba"**, không phải *"cùng một câu"* — đó
là điều làm `e4` đọc được, và cũng làm ca dữ kiện tách dòng đọc được.

**Neo** (③ lối nói) · **quan hệ** (④ dạng):

| neo | ví dụ |
|---|---|
| nằm trên / thuộc | *"Điểm P nằm trên đoạn EF"* · *"P thuộc EF"* |
| **cắt … tại** | *"mặt phẳng … cắt PQ tại điểm T"* · *"đường thẳng d cắt AB tại M"* |
| trung điểm | *"I là trung điểm của GH"* |

| quan hệ | ví dụ | `t` |
|---|---|---|
| tỉ số | `CN : ND = 2 : 3` | `2/5` |
| bội số | `FP = 4·PE` (`·` `×` `*` hoặc không dấu) | `1/5` |
| độ dài một nhánh | `AM = 9` + `|AB| = 12` | `3/4` |
| trung điểm | — | `1/2` |

Chuẩn hoá **lối viết**, không chuẩn hoá ngữ nghĩa: `bằng` → `=`, `·×*` → `*`,
gộp khoảng trắng. Ba phép này chỉ đổi cách viết của cùng một quan hệ.

**Ghép nhãn với giá trị của `InputFact`** là đọc đúng hợp đồng, không phải suy
thêm: mục *"Độ dài đoạn AM"* + `9` **nói** `AM = 9`, nhưng hai nửa nằm ở hai
trường nên chuỗi ấy không tồn tại ở đâu cả. Chỉ ghép với giá trị **SỐ** — giá
trị văn xuôi đã tự là một câu, dán nhãn vào trước sẽ đẻ ra một quan hệ không
ai viết.

Biểu diễn **không đổi**, vẫn `points=(A,B,M)` + `expected=t`, hướng A→B lấy từ
**đề**. `source_text` nay giữ **cả hai vế** — neo nói *chia đoạn nào*, mảnh nói
*theo tỉ lệ nào* — vì bản đầu chỉ giữ neo, nên lời từ chối mất chính vế học
sinh cần đọc.

## 4. `NOT_CHECKABLE` — trạng thái CHẶN mới

`SourceInvariantResult` thêm trường **`unresolved`**, tách hẳn khỏi
`not_checkable` sẵn có. Ba câu khác nhau, và chỉ hai câu đầu an toàn khi im lặng:

| | nghĩa | chặn? |
|---|---|---|
| `not_checkable` | bất biến có, trạng thái cuối thiếu vật để đo | **không** |
| **`unresolved`** | **ĐỀ CÓ** nói về phép chia — neo được bộ ba, có mảnh quan hệ nói đúng hai nhánh, có nguồn — mà hệ **không tính ra `t`** | **CÓ** |
| `violated` | tính ra `t`, hình không khớp | **CÓ** |

Mã lỗi mới, ổn định: **`SOURCE_INVARIANT_NOT_CHECKABLE`**. Vi phạm **thắng**
khi có cả hai — *"hình sai"* là kết luận mạnh hơn *"chưa đọc hiểu"*.

Ngưỡng là **"có tín hiệu chắc chắn"**, không phải *"có nghi ngờ"*: phải neo
được bộ ba **và** thấy mảnh quan hệ nói đúng hai đoạn con. Hai ca đạt ngưỡng:

- **thiếu độ dài cả đoạn** — *"Điểm P nằm trên đoạn EF sao cho PE = 2"* không
  cho `|EF|`;
- **mơ hồ** — hai mảnh cho hai `t` khác nhau về cùng một bộ ba.

⚠️ Đây là **đổi hành vi có chủ đích**: ca thứ nhất trước đây trả `()` và đi
tiếp. Ba test của wave trước đã đổi kỳ vọng, mỗi chỗ ghi rõ lý do.

## 5. Bằng chứng không phụ thuộc tên bài

`backend/tests/geometry/test_segment_relation_coverage.py` — **27 pass**.

- `B1` đổi tên nhất quán `P,Q,T → A,B,M`: cùng cho `5/7`.
- `B2` đổi số `PQ = 35`, `PM = 15`: cho `3/7`.
- `B3` dữ kiện `MB = 3` trên `AB = 12`: quy đúng theo hướng A→B ⇒ `3/4`.
- `B4` tỉ số `m/(m+n)` · `B5` bội số hai chiều · `B6` bốn dấu nhân.
- `B7` `AM = 9` trên `12` ⇒ **`3/4`**, không phải chuỗi `9/12`.
- `B8` quan hệ nằm ở **hai `InputFact` khác nhau** vẫn ghép đúng.
- `B9` hai đoạn cùng xuất hiện vẫn phân biệt.

Không test nào đọc mã ca `e4` hay tên `P`/`Q`/`T` để quyết định.

## 6. Phép tiêm và regression

| tiêm | phải xảy ra | test |
|---|---|---|
| gỡ mẫu neo *"cắt AB tại M"* | `e4` mất bất biến, `t=1/2` **`served` trở lại** | `D1` |
| đảo hướng A→B của bất biến | chương trình ĐÚNG bị bác | `D2` |
| bỏ ghép `InputFact` | ca dữ kiện tách dòng thành `NOT_EXTRACTED` | `D3` |
| so bằng `float` | `t = 7142857/10000000` không còn bị bắt | `D4` |

**Regression:** `r1`–`r4` giữ nguyên `t` (`3/4`, `2/5`, `1/5`, `1/2`) ·
`r3/A` **vẫn bị bác** · toàn bộ 36 test của wave trước xanh (ba cái đổi kỳ
vọng theo hành vi mới) · binding container · point initialization · curved
distance witness · demo replay 5/5 · crash surface 6/6.

## 7. Identity, cache, candidate

**`MODEL_FACING_DELTA = NONE`** — sáu băm byte-identical:

| | |
|---|---|
| `prompts` | `55ac1ca6…` |
| `grammar_card` | `e0fbbc84…` — thẻ sản phẩm **== `card_A.txt`** |
| `synthesis_schema` | `8c57c9de…` |
| `analyze_schema` | `515001b5…` |
| `capability` | `85bd3167…` |
| `semantic_environment` | `f7def620…` |

`source_invariants` **không có trong lược đồ analyze** — server sở hữu, nên mở
rộng nó không chạm bề mặt mô hình.

**`CACHE_DECISION = 82 → 83, BUMP`** — cùng loại `81 → 82`. Chiều đổi là
`served → từ chối`, mà `served` **là** thứ được cache (`status == "ok"`). Đo
bằng **row `e4` thật** trước khi bump:

```
row policy_version=82, envelope {"ban_kinh_t": "21/2"}
  → _cache_lookup  HIT, trả về nguyên vẹn, KHÔNG đi qua cổng mới
```

Bốn chỗ đồng bộ đã sửa; `lock_cache_identity.py` chạy lại và tự xác nhận
*"môi trường không đổi, chỉ version lệch"*.

**`CANDIDATE_BEFORE_AFTER = 1151bc6f… → 179793db…`** (90 file, `--verify`
exit 0).

## 8. Cổng đã chạy

| cổng | kết quả | mới / kế thừa |
|---|---|---|
| `pytest -q` (cây sạch) | **3950 pass**, 1 skip, 1 deselect, **0 đỏ** | **mới** |
| wave suite | **27 pass**, 4 phép tiêm | **mới** |
| suite wave trước | **36 pass** | **mới** |
| `test_api` · `test_cache_identity` · `test_current_state_identity` | **37 pass** | **mới** |
| `replay_demo_cases.py` | **5/5**, `REDUCED_CHAIN 1/1` | **mới** |
| `audit_demo_crash_surface.py` | **6/6 biên**, ném **0** | **mới** |
| `certify_acceptance_runner.py` | **PASS**, 0 lượt gọi | **mới** |
| `freeze_evaluation_candidate --verify` | **exit 0**, 90 file | **mới** |
| `git diff --check` | sạch | **mới** |
| vitest · `npm run build` | — | **kế thừa** (frontend không đụng) |

## 9. Giới hạn còn lại

- **`NOT_EXTRACTED` vẫn còn thật.** Bộ đọc phủ **ba neo × bốn quan hệ**; lối
  nói ngoài đó không sinh bất biến và **không bị chặn**. Đây là giới hạn phủ,
  **không phải fail-closed** — §0 đã sửa cách gọi.
- Chỉ mở quan hệ **chia đoạn**. Song song, vuông góc, thuộc mặt phẳng, tỉ số
  thể tích chưa có ca sai đi qua cùng đường ⇒ backlog.
- Bất biến gắn theo **tên điểm của đề**; chương trình đặt tên khác thì nhờ lưới
  hoà giải. Không hoà giải được ⇒ `not_checkable`, **không** chặn.
- Ngưỡng `unresolved` là một **lựa chọn**: chặt hơn thì bắt được nhiều lối nói
  hơn nhưng có thể chặn nhầm; lỏng hơn thì lọt. Chưa đo tỉ lệ chặn nhầm trên
  một corpus lớn.

## 10. Kết luận

```
E4_SEGMENT_RELATION_EXTRACTED   = YES — points=(P,Q,T), nguon=mat_phang_cat_pq_tai_t
E4_EXPECTED_T                   = 5/7   (PT/PQ = 20/28)
E4_CORRECT_REPLAY               = served · ban kinh 15 · scene 12 ·
                                  postconditions radius((t)) verified
E4_IN_RANGE_WRONG_RATIO_REJECTED= YES — t=1/2 dat T TRONG khoi, kernel dung
                                  duoc thiet dien, checker do dung 21/2, VA
                                  van bi bac o `source_invariant` (VIOLATED).
                                  TRUOC wave: served voi 21/2
REVERSED_OPERAND_EQUIVALENCE    = YES — divide_segment(Q,P,2/7) dung dung
                                  cung mot T ⇒ served, 15
AMBIGUOUS_RELATION_HANDLED      = YES — hai `t` khac nhau cho cung bo ba ⇒
                                  NOT_CHECKABLE, CHAN, khong chon ho
UNRESOLVED_RELATION_POLICY      = BLOCK_SERVED, ma `SOURCE_INVARIANT_NOT_CHECKABLE`
                                  truong `unresolved` tach han khoi `not_checkable`;
                                  VIOLATED thang khi co ca hai
SILENT_WRONG_ANSWER_COVERAGE    = 3 neo × 4 quan he, cong 2 ca NOT_CHECKABLE.
                                  Ngoai do van la NOT_EXTRACTED — KHONG chan,
                                  va do la gioi han PHU chu khong phai fail-closed
MODEL_FACING_DELTA              = NONE (6 bam byte-identical)
CACHE_DECISION                  = 82 → 83, BUMP — do bang row `e4` that:
                                  envelope 21/2 o v82 van HIT, khong qua cong moi
CANDIDATE_BEFORE_AFTER          = 1151bc6f… → 179793db…  (90 file, verify exit 0)
APPLICATION_LLM_CALLS           = 0
TOKEN_EFFICIENCY                = NOT_MEASURED
PRODUCT_CAPABILITY_CHANGED      = NO (ball/cylinder/cone van foundation_only)
RECOMMENDED_NEXT_ACTION         = RATIO_AFFORDANCE_STAGED_RECHECK
```

**Việc kế tiếp.** `e4` và lớp câu tổng quát đã được bảo vệ, nên quay lại phép
đo đang treo — nhưng **theo bậc**: bắt đầu **2 ca × 2 arm = 4 lượt tổng hợp**,
chỉ mở thêm cặp khi **cả** tín hiệu chất lượng **và** ngân sách đều đạt. Phép
đo ấy nay báo được ba con số mà lượt trước không tách nổi: tỉ lệ sinh đúng ·
tỉ lệ `served` **đúng** (nay `served` đã có nghĩa là đúng dữ kiện trong phạm vi
đã phủ) · token trên một kết quả đúng.

⚠️ Token của Claude Code **không** tính vào token vận hành AlgoSim; replay,
checker và Scene3D không dùng token Gemini.
