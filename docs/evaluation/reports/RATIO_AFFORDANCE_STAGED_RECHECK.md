# RATIO_AFFORDANCE_STAGED_RECHECK

> 2026-09-06. Phép đo phát triển nhỏ: **2 đề × 2 arm = 4 lượt synthesis**.
> `MEASUREMENT_CLASS = DEVELOPMENT_SYNTHESIS_AB` · `HELD_OUT_CLAIM = NO`.
> Thẻ sản phẩm giữ **A** trong suốt phép đo; **không đụng một dòng mã sản
> phẩm nào**.
>
> ```
> B_RATIO_SIGNAL = POSITIVE   (B 2/2 · A 0/2 · thắng 2 · thua 0)
> B_SERVABLE_SIGNAL = NEUTRAL (cả 4 lượt, cả HAI arm, chết ở grounding)
> ```

## 1. Trạng thái đầu — khớp bàn giao

| | |
|---|---|
| HEAD · cây | `432baff` · **sạch** |
| `CACHE_VERSION` | **83** |
| candidate | `179793db…` · `--verify` **exit 0** (90 file) |
| `PRODUCT_VARIANT` | **A** — `grammar_card("hinh_hoc")` == `card_A.txt`, băm `c7c001c4…` |
| test quan hệ chia đoạn | **86 pass** (coverage 27 · consistency 36 · runner 23) |

Sáu băm model-facing, đọc từ `cache_identity.lock.json` @ `CACHE_VERSION 83`:
`prompts 55ac1ca6…` · `grammar_card e0fbbc84…` · `synthesis_schema 8c57c9de…` ·
`analyze_schema 515001b5…` · `capability 85bd3167…` ·
`semantic_environment f7def620…`.

Artifact: `card_A c7c001c4…` (5472 B) · `card_B 25d43370…` (5532 B) ·
runner `8e812239…` · gold `d53b23f6…` (băm trước khi wave sửa runner).

**Không có sai khác nào với báo cáo bàn giao.**

## 2. Thiết kế, chốt trước lượt gọi đầu

`docs/evaluation/geometry/ratio-affordance-staged-recheck/registration.json`

| phép đo | ca | đề | `t` đúng | đáp số |
|---|---|---|---|---|
| **RATIO** | `r2` | `CD = 10`, `N ∈ CD`, `CN:ND = 2:3` | `t(C→D) = 2/5` | `ND = 6` |
| **MULTIPLE** | `r3` | `EF = 10`, `P ∈ EF`, `FP = 4·PE` | `t(E→F) = 1/5` | `PF = 8` |

Hợp đồng **cố định**, hai arm dùng **cùng** contract · cùng model · cùng tham
số. Chỉ thẻ khác: **arm A** = thẻ sản phẩm; **arm B** = A + **đúng một dòng**

```
- ratio:tên
+ ratio:t trong M = a + t(b−a); chia trong đoạn m:n ⇒ t = m/(m+n)
```

`Δ = +60 byte`, `responseSchema` **không đổi** (`_VAN_XUOI` không đi vào JSON
schema) — hai arm dùng lược đồ y hệt.

**Thứ tự luân phiên** theo chỉ số ca (`r2` → B trước, `r3` → A trước), khoá
trong registration trước lượt gọi. §4 của brief liệt kê bốn lượt chứ không áp
thứ tự; luân phiên là yêu cầu §2 và là bản đã đăng ký.

**Ngân sách, đặt từ telemetry lịch sử** (47 303 token / 8 lượt ≈ 5 913/lượt):
`TOKEN_PER_CALL = 7 500` ⇒ trần lượt chạy `30 000`, và guard **dự trữ đủ cho
cả cặp** (2 × 7 500) trước khi bắt đầu nó — sửa đúng giới hạn mà
`DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB` §6 đã ghi (guard cũ kiểm tổng nên không
cắt được giữa cặp và vượt trần 47 303/40 000).

⚠️ Runner nay **gắn `source_invariants`** vào hợp đồng cố định như
`build_request_contract` làm — không gắn thì cổng bất biến nguồn mà
`SEGMENT_RELATION_*` vừa dựng **sẽ không chạy**, và phép đo sẽ báo `served`
cho đúng lớp chương trình mà sản phẩm đang từ chối.

## 3. Tiền kiểm tất định — 11 pass, 0 lượt gọi

`backend/tests/geometry/test_ratio_staged_recheck_preflight.py`

| # | yêu cầu | kết quả |
|---|---|---|
| ① | RATIO `t=2/5` dựng đúng `N`, `ND = 6`, qua bất biến nguồn | **served**, scene dựng được |
| ② | MULTIPLE `t=1/5` dựng đúng `P`, `PF = 8`, qua bất biến nguồn | **served** |
| ③ | tỉ lệ sai **nhưng trong đoạn** | **`NORMALIZED_SOURCE_VIOLATED`** (`1/2` cho RATIO, `1/4` cho MULTIPLE) |
| ④ | đảo toán hạng, tỉ lệ tương đương | **served**, cùng đáp số (`D→C 3/5`, `F→E 4/5`, và `2/10 ≡ 1/5`) |
| ⑤ | `InputFact` mâu thuẫn với đề | **không biến hình sai thành hình đúng** — xem dưới |

**⑤ THẨM QUYỀN KHI HAI NGUỒN MÂU THUẪN — đo được, không suy.** Đề nói
`FP = 4·PE` (`t = 1/5`); thêm một `InputFact` nói `PE = 5` (`t = 1/2`):

```
chỉ đề                        → segment_division, t = 1/5
đề + fact ĐỒNG THUẬN (PE = 2) → segment_division, t = 1/5
đề + fact MÂU THUẪN (PE = 5)  → segment_division_unresolved  ⇒ CHẶN
```

**Không nguồn nào thắng.** Chương trình theo dữ kiện (`t = 1/2`) bị chặn, **và**
chương trình theo đề (`t = 1/5`) cũng bị chặn — hệ không giả vờ đã phân xử
được. Đó là cái giá của fail-closed, và nó nói ra được.
Ranh giới: chỉ mâu thuẫn **đọc được** mới chặn; `FP = PE` (không có số) không
khớp mẫu nào nên bị bỏ qua (`test_5c`).

## 4. Bốn lượt live

`ratio_ab_ratio-ab-20260906T164733Z.json` · `RUN_STATUS = COMPLETE` ·
`LOGICAL 4/4` · `PHYSICAL 4/32` · `TOKENS 20 198/30 000`.

| ca | arm | chiều | `t` viết | `t` đúng | `t` OK | stage | grounding | servable | token |
|---|---|---|---|---|---|---|---|---|---|
| RATIO | **B** | `C→D` | **`2/5`** | `2/5` | **PASS** | `grounding` | FAIL | False | 5342 |
| RATIO | A | `C→D` | `2/3` ✗ | `2/5` | FAIL | `grounding` | FAIL | False | 4939 |
| MULTIPLE | A | `E→F` | `1/4` ✗ | `1/5` | FAIL | `grounding` | FAIL | False | 5324 |
| MULTIPLE | **B** | `E→F` | **`1/5`** | `1/5` | **PASS** | `grounding` | FAIL | False | 4593 |

### 4.1 Ratio correctness

**A 0/2 · B 2/2. Ghép cặp: thắng 2 · thua 0 · hoà 0.**

Cả hai arm chọn đúng chiều `A→B` và đều dùng `divide_segment`; khác nhau **chỉ
ở `t`**. A viết `2/3` cho `CN:ND = 2:3` và `1/4` cho `FP = 4·PE` — cả hai đúng
là **quy ước chia đoạn `m:n`**, đúng thứ delta B đi sửa. Đây là lần tái hiện
**thứ ba** của cùng hiểu nhầm (`c9b`, `r3/A` lượt trước, và ở đây).

### 4.2 Program correctness — cả bốn dừng ở `grounding`

`SOURCE_INVARIANT`, `POSTCONDITIONS`, `SCENE3D`, `SERVABLE` đều
**`NOT_REACHED`** cho cả bốn lượt: chưa lượt nào đi tới tầng ấy.

### 4.3 Token

Công thức: **tổng = `total_tokens`** (`totalTokenCount` của API, **đã gồm**
thoughts). Không cộng `prompt + candidates + thoughts`; `cached_content` là
**tập con** của prompt.

| | A | B |
|---|---:|---:|
| prompt | 6 833 | 6 883 |
| candidates | 1 145 | 1 028 |
| thoughts | 2 285 | 2 024 |
| **cached_content** | **2 989** | **0** |
| **tổng** | **10 263** | **9 935** |
| ca `t` đúng | 0/2 | **2/2** |
| ca served đúng | 0/2 | 0/2 |
| **token / `t` đúng** | **UNDEFINED** (0 ca đúng; tổng 10 263) | **4 968** |
| **token / served đúng** | **UNDEFINED** (0; tổng 10 263) | **UNDEFINED** (0; tổng 9 935) |

⚠️ **So token giữa hai arm BỊ NHIỄU, phải khai.** A nhận **2 989** token
`cached_content` còn B nhận **0** — prompt caching phía provider không được
kiểm soát trong thiết kế này, và nó đổi cả `total_tokens`. Nên chênh lệch tổng
(10 263 vs 9 935) **không** quy cho delta thẻ được. Con số dùng được là
**`4 968` token cho một `t` đúng của B**, đặt cạnh **`UNDEFINED` của A** —
tức A tiêu 10 263 token mà **không** cho kết quả đúng nào trên trục này.

## 5. Nguyên nhân chung — trỏ thẳng raw candidate

Cả bốn lượt hỏng vì **cùng một điều, ở cả hai arm**:

```
input_not_grounded — "E: có initial_value nhưng thiếu source_fact_id"
```

Raw candidate `r3`, **giống hệt nhau ở A và B**:

| khai báo | giá trị | `source_fact_id` | `model_assumption` |
|---|---|---|---|
| `E` | `[0,0,0]` | **thiếu** | **thiếu** |
| `F` | `[10,0,0]` | `do_dai_doan` ✓ | — |
| `P` | — | `vi_tri_diem` ✓ | — |

Mô hình ghim **đúng** cái đầu mút mang dữ kiện độ dài, và bỏ trống đầu mút
**gốc toạ độ**. Đặt `E` tại `[0,0,0]` là một **lựa chọn hệ trục**, không phải
dữ kiện đề cho — và hợp đồng có sẵn ô cho đúng việc ấy:
`MemoryDeclaration.model_assumption` (*"LÝ DO chọn giá trị này, khi nó là GIẢ
THIẾT MÔ HÌNH HOÁ chứ không phải dữ liệu đề cho — điển hình là toạ độ của một
đỉnh khi đặt hệ trục"*). Mô hình **không dùng ô ấy**.

Grounding **không sai**: nó đòi đúng thứ nó phải đòi, và chương trình gold có
ghim đủ nên đi trọn. Đây là lỗ **affordance**, cùng hình dạng với `ratio`:
một ô tồn tại, có nghĩa đúng, mà mô hình không được nói cho biết khi nào dùng.

⚠️ `HYPOTHESIS` — chưa có bằng chứng phân biệt: lượt
`DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB` thấy B hỏng grounding 3/4 còn A 0/4, và
kết luận khi ấy là *"không tách được delta khỏi nhiễu"*. Lượt này **cả hai arm
đều hỏng 2/2**, nghiêng về giả thuyết *"lỗi chung, không do thẻ"* — nhưng
`n = 2` cặp vẫn chưa đủ để bác hẳn giả thuyết còn lại.

## 6. Phạm vi

**Không đổi một dòng mã sản phẩm.** Grounding hành xử đúng, nên §6 của brief
không kích hoạt (*"mã sản phẩm chỉ thay đổi khi phép kiểm tất định phát hiện
một lỗi sai rõ ràng có phản ví dụ chạy được"*).

Thay đổi nằm ở **bộ đo** (`backend/scripts`, `backend/tests`) — ngoài
`MEASURED_SYSTEM_PATHS`: runner gắn `source_invariants`, ngân sách theo lượt
chạy, thêm chiều chấm `SOURCE_INVARIANT_RESULT`, thêm `--ra`.
`PRODUCT_CAPABILITY_CHANGED = NO`; kiến trúc `trace → Scene3D` không đụng.

⚠️ Một khiếm khuyết của runner đã sửa trong wave: hai dòng **in ra console**
còn đọc trần corpus (`logic 8 · token 40000`) trong khi **manifest** ghi đúng
trần lượt chạy (`logical_budget 4 · token_ceiling_observed 30000`). Artifact
của record luôn đúng; chỉ dòng in sai, và nó đã được sửa.

## 7. Cổng đã chạy

| cổng | kết quả | mới / kế thừa |
|---|---|---|
| tiền kiểm wave | **11 pass**, 0 lượt gọi | **mới** |
| test runner A/B | **23 pass** (stub, 0 lượt gọi) | **mới** |
| test quan hệ chia đoạn | **63 pass** | **mới** |
| `pytest -q` (cây cuối) | **3961 pass**, 1 skip, 1 deselect, **0 đỏ** | **mới** |
| `replay_demo_cases.py` | **5/5**, `REDUCED_CHAIN 1/1` | **mới** |
| `audit_demo_crash_surface.py` | **6/6 biên**, ném **0** | **mới** |
| `freeze_evaluation_candidate --verify` | **exit 0**, 90 file, `179793db…` | **mới** |
| `git diff --check` | sạch | **mới** |
| vitest · `npm run build` | — | **kế thừa** (frontend không đụng) |

## 8. Kết luận

```
APPLICATION_LLM_CALLS = 4      ANALYZE_CALLS = 0
SYNTHESIS_CALLS       = 4      REPAIR_CALLS  = 0

A_RATIO_CORRECT / B_RATIO_CORRECT         = 0/2  ·  2/2
A_POSITION_CORRECT / B_POSITION_CORRECT   = 0/2  ·  0/2   (NOT_REACHED ca 4 luot)
A_CORRECT_SERVABLE / B_CORRECT_SERVABLE   = 0/2  ·  0/2
PAIRED_WINS / LOSSES / TIES               = 2 · 0 · 0     (truc ratio)

A_TOTAL_TOKENS / B_TOTAL_TOKENS           = 10 263 · 9 935
A_TOKENS_PER_CORRECT_RATIO                = UNDEFINED (0 ca dung; tong 10 263)
B_TOKENS_PER_CORRECT_RATIO                = 4 968
A_TOKENS_PER_CORRECT_SERVABLE             = UNDEFINED (0 ca; tong 10 263)
B_TOKENS_PER_CORRECT_SERVABLE             = UNDEFINED (0 ca; tong 9 935)
  ⚠️ so token giua hai arm BI NHIEU: cached_content A 2 989 · B 0

GROUNDING_FAILURES_BY_ARM         = {A: 2, B: 2}
SOURCE_INVARIANT_FAILURES_BY_ARM  = {A: 0, B: 0}   (chua luot nao toi tang nay)
OTHER_FAILURES_BY_STAGE           = {grounding: 4}

B_RATIO_SIGNAL            = POSITIVE
B_SERVABLE_SIGNAL         = NEUTRAL   (ca hai arm 0/2, cung mot nguyen nhan)
B_TOKEN_SIGNAL            = POSITIVE-nhung-NHIEU: B co chi so xac dinh
                            (4 968/ket qua dung) trong khi A UNDEFINED;
                            chenh TONG khong quy cho delta duoc vi cache lech
CAUSAL_ATTRIBUTION        = LIMITED   (delta gop, n = 2 cap)
STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED

PRODUCT_VARIANT_BEFORE_AFTER  = A → A  (khong doi)
MODEL_FACING_HASHES_BEFORE_AFTER = KHONG DOI ca sau
                            (55ac1ca6 · e0fbbc84 · 8c57c9de · 515001b5 ·
                             85bd3167 · f7def620)
CACHE_VERSION_BEFORE_AFTER    = 83 → 83  (khong bump: khong doi phan quyet
                            san pham, khong doi be mat mo hinh)
CANDIDATE_HASH_BEFORE_AFTER   = 179793db… → 179793db…  (khong dong bang lai)
PRODUCT_CAPABILITY_CHANGED    = NO
WORKING_TREE                  = sach
COMMITS                       = 1 (eval-only; xem §7 cua bao cao)
RECOMMENDED_NEXT_ACTION       = FRAME_ORIGIN_PROVENANCE_AFFORDANCE
```

**Vì sao việc kế tiếp là thế.** Hai nhánh của luật quyết định cùng chỉ về một
chỗ: *"B cải thiện `ratio` nhưng tiếp tục gây lỗi grounding/provenance ⇒ thiết
kế một delta nhỏ chỉ làm rõ source binding, rồi đo riêng"*, và *"cả hai arm
cùng sai ⇒ định vị lỗi chung từ raw candidate trước khi sửa thẻ"*. Lỗi chung
**đã định vị**: gốc toạ độ khai bằng `initial_value` mà không dùng ô
`model_assumption` vốn có sẵn cho đúng việc ấy.

Delta kế tiếp vì thế là **một dòng, chỉ về provenance của gốc toạ độ**, đo
**riêng** (không gộp với delta `ratio`), lại theo bậc **2 ca × 2 arm**. Chỉ khi
end-to-end thông mới bàn tới `token trên một mô phỏng phục vụ đúng` — con số ấy
lượt này **`UNDEFINED` cho cả hai arm**, và nói khác đi là nói quá.

⚠️ Token của Claude Code **không** tính vào token vận hành AlgoSim; replay,
checker và Scene3D không dùng token Gemini.
