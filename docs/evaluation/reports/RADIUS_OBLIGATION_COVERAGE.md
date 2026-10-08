# RADIUS_OBLIGATION_COVERAGE — đóng lỗ ontology cuối

> Thực hiện **2026-09-03**. **0 lượt gọi model.**
> `CURVED_ACCEPTANCE_V1` và `V2` bất biến, không sửa một con số.

---

## 1. Gốc — hợp đồng không cho mô hình một cách hợp lệ để nói điều đúng

```
CURRENT_RADIUS_REQUEST_MAPPING (trước)   "tính bán kính"  →  distance
ROOT_CAUSE                                taxonomy không có `radius`
```

Hai chỗ, cùng một thiếu:

- `OBLIGATION_KINDS` không có `radius` ⇒ enum `analyze` chỉ có 9 nghĩa vụ.
- Bảng dịch trong `geometry_analyze.md` không có dòng nào cho *"tính bán kính"*.

Mô hình buộc phải chọn nghĩa vụ **gần nhất mà nó có từ để gọi** — `distance`
(bán kính *là* một khoảng cách). Rồi `container` rơi vào khối cong, và cổng phủ
bác đúng luật:

```
ball_1        distance(I)    → kiểu 'curved_solid' không hợp với nghĩa vụ này
circumsphere  distance(OABC) → kiểu 'solid' không hợp với nghĩa vụ này
```

**Cả hai sinh chương trình ĐÚNG** (dùng `measure radius`) và vẫn chết.

---

## 2. Sửa — một dòng, dẫn xuất

```
RADIUS_OBLIGATION_BEFORE   không tồn tại
RADIUS_OBLIGATION_AFTER    NGHIA_VU_DO["radius"] = ("radius",)
RADIUS_SUBJECT_TYPES       {circle3, curved_solid} — DẪN từ BANG_PHEP_DO["radius"]
MEASURE_SIGNATURE_OWNER    measure_contract.BANG_PHEP_DO
MEASURE_COMPATIBILITY_AUTHORITIES   1
PROBLEM_FAMILY_RADIUS_OBLIGATIONS   0
```

Không dòng nào viết `radius → [circle3, curved_solid]` lần thứ hai — cầu nối
của wave trước lo phần ấy, và `test_R10c` cấm nó quay lại vào literal.

```
RADIUS_REQUEST_MAPPING     "tính bán kính"          →  radius
DISTANCE_REQUEST_MAPPING   "khoảng cách từ A đến…"  →  distance  (KHÔNG đổi)
```

Prompt phân biệt bằng **số toán hạng**, không bằng chữ trong đề:

> `radius` khác `distance` ở **số toán hạng**, không ở chữ trong đề: bán kính
> là đại lượng của CHÍNH một vật (không có `wrt`); khoảng cách luôn đo giữa HAI
> vật (có `wrt`).

Dạy theo chữ là đúng cái bẫy `measure_contract §②` đã phải đi dọn với
`angle_cos` — tên phép đo chứa sẵn chữ *"cos"*, nên đề nào hỏi *"côsin"* là mô
hình chọn nó, kể cả khi sai.

```
LATERAL_AREA_TAXONOMY_CHANGED   NO
MEASURE_COVERAGE_DRIFT          0
```

---

## 3. `radius` là nghĩa vụ **mức yếu** — quyết định, không phải bỏ sót

Nó **chưa có checker**. Hệ quả đúng và phải khai:

```
đề hỏi bán kính  →  executable = True   ·   servable = False   (verification_gap)
```

Vì sao không thêm `check_radius` luôn: wave này đóng một lỗ ở **cổng phủ** — hệ
nay *biểu diễn được* câu hỏi. Nó **không** tuyên hệ *kiểm chứng lại được* con số
ấy. Thêm checker là một tuyên bố năng lực khác: nó đổi `GEOMETRY_CHECKERS` (nằm
trong vân tay năng lực) và đổi mọi con số *"safe serve rate"* của luận văn. Đó
phải là một quyết định riêng, không phải phần đuôi của một bản vá cổng phủ.

`test_co_that_it_nhat_mot_nghia_vu_muc_yeu` khoá tập yếu ở
`["structural_traversal", "radius"]`.

---

## 4. Replay — và cái nó KHÔNG chứng minh

```
V2_BALL_1_SYSTEM_BLOCKER        CLOSED
V2_CIRCUMSPHERE_SYSTEM_BLOCKER  CLOSED
V2_RADIUS_SYSTEM_BLOCKERS_FIXED 2/2  (tại CỔNG PHỦ — thứ wave này sửa)
```

⚠️ **Hai chương trình V2 vẫn không chạy được, và KHÔNG phải vì `radius`.** Đọc
chúng ra mới thấy:

| ca | hỏng ở đâu | thuộc về |
|---|---|---|
| V2 `ball_1` | khai `I` và `S` là `curved_solid` rồi **không dựng cái nào** ⇒ `AMBIGUOUS_FIRST_BINDING` | mô hình |
| V2 `circumsphere` | **dựng** `circumsphere` nhưng không **khai** nó ⇒ cổng phủ không hoà giải được tên | mô hình |

Nên bằng chứng đường đầy đủ dùng chương trình `ball_1` của **lượt V1** — nó
sạch (tĩnh OK, xuất xứ OK) và đo `radius` của một khối cong dựng đúng:

```
FULL_PRODUCTION_ROUTE   ball_1 (V1) · tĩnh → xuất xứ → phủ → interpreter → vết
                        executable=True · servable=False (chưa có checker)
                        R = 6 · V = 288π   ← kiểm tay
```

`test_R8` khoá luôn sự thật *"hai ca V2 hỏng vì lý do khác"*, để không ai đọc
*"2/2 fixed"* thành *"hai ca ấy nay chạy"*.

Ca `test_R7b` chạy chiều ngược lại: cùng chủ thể ấy với nghĩa vụ **`distance`**
thì cổng **vẫn** bác. Không có nó thì không chứng minh được lỗ từng tồn tại.

---

## 5. Ranh giới không nới

```
R0                           PASS
CURVED_GEOMETRY_LAUNDERING   0
_KIEU_DUOC_GIA_THIET         {point3, vector3}   không đổi
distance                     {point3, line3, plane3}   không rộng thêm một ly
```

`test_R9` dựng một chương trình bịa tâm (`I_bia`) rồi đo bán kính — cổng xuất
xứ vẫn bác. Thêm một nghĩa vụ **không** được thành một cửa cho toạ độ bịa.

---

## 6. Hợp đồng và phiên bản

```
MODEL_FACING_ANALYZE_SCHEMA_CHANGED   YES   2145 → 2155 byte (+10)
SYNTHESIS_SCHEMA_CHANGED              NO    111.152 byte
GRAMMAR_CARD_CHANGED                  NO    4035 byte
PROMPT_CHANGED                        YES   geometry_analyze.md 4196 → 4517 (trên đĩa)
```

⚠️ Ngân sách prompt đo `st_size`, tức **đã tính CRLF**. Đo bằng
`len(text.encode())` ra 4442 và lệch 75 byte so với thứ cổng thật sự so — ghi
rõ để lần sau không ai trừ nhầm. Trần 4200 → 4600.

Cổng danh tính cache **đỏ trước khi làm mới**, nêu đúng ba thành phần:

```
thành phần đổi: ['prompts', 'analyze_schema', 'capability']
CAPABILITY_HASH   100c71f0bd01ed1d… → 917c037ab5f7ad7c…
CACHE_VERSION     67 → 68
```

Lý do bump: một đề hỏi bán kính **từng** được phân tích thành `distance`, nay
thành `radius`. Envelope đã cache mang nghĩa vụ **sai** so với hệ hiện tại, và
cổng phủ phán quyết trên chính nghĩa vụ ấy.

---

## 7. Taxonomy niêm phong — §16

```
SEALED_RESEARCH_BASELINE   a075e9f5…   không đổi, không chạy lại
CURVED_ACCEPTANCE_V1 · V2  IMMUTABLE
```

`radius` là **mở rộng của sản phẩm hiện tại SAU baseline đã niêm phong**. Câu
hỏi bắt buộc của `test_taxonomy_frozen` — *"thay đổi đến từ DEV hay từ một ca
SEALED?"* — trả lời: **không từ đâu cả trong hai**. Nó đến từ
`CURVED_MODEL_ACCEPTANCE_V2`, một phép đo MỚI trên bộ ca MỚI
(`8c6a184f1c175964…`).

⚠️ Điểm số lịch sử vẫn gắn với taxonomy gốc của chúng. So số cũ với số mới mà
không nói rõ phiên bản là so hai hệ khác nhau.

**Ô held-out miễn trừ có lý do**: pool niêm phong trước khi nghĩa vụ này tồn
tại, và mở một ô sẽ đổi `pool_hash` — phá con dấu. Hệ quả khai thẳng: **held-out
KHÔNG đo câu hỏi bán kính**, nên mọi con số của nó không nói gì về năng lực ấy.

---

## 8. Cổng

| cổng | kết quả |
|---|---|
| `pytest` | **3031 passed**, 1 skipped (+20 ca mới) |
| `vitest` | **687 passed** (50 tệp) |
| `npm run build` | PASS |
| `replay` · `crash surface` | 5/5 · 1/1 · 6/6 ném 0 |
| `lock_cache_identity --verify` | exit 0 · version 68 |
| `freeze --verify` | 89 file · `abf67923e32a5aaa…` |
| chín phép đo trình duyệt | 21/21 · 8/8 · 7/7 · 7/7 · 9/9 · 4/4 · 13/13 · 11/11 · 21/21 · **CONSOLE_ERRORS 0** |

```
BALL_PRODUCT_ENABLED  NO   CYLINDER_PRODUCT_ENABLED  NO   CONE_PRODUCT_ENABLED  NO
APPLICATION_LLM_CALLS  0
RADIUS_OBLIGATION_COVERAGE   CLOSED
```

Replay tất định **không** là bằng chứng cho model discoverability. Ba dòng năng
lực sản phẩm không đổi.

---

## 9. Bài học đáng giữ hơn cả bản vá

Wave trước tôi kết luận `RADIUS_OBLIGATION_NEEDED = NO` với lý do *"chưa có
phép đo nào chứng minh là cần"*. Lập luận ấy **không sai về logic** — nó sai vì
tôi coi *"chưa có bằng chứng"* là bằng chứng cho chiều ngược lại, rồi ghi kết
luận ấy vào một bảng như một sự thật.

Cùng câu chữ ấy nay đang đứng cho `lateral_area` (§8 của wave này). Nó được
giữ, nhưng phải đọc kèm bài học: đó là *"chưa biết"*, không phải *"không cần"* —
và `test_08` ghi đúng câu ấy vào chỗ nó sẽ được đọc lại.
