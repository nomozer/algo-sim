# CURVED_SYNTHESIS_ERGONOMICS — hợp thành dễ hơn, năng lực không đổi

> Thực hiện **2026-09-03**. Phần tất định: **0 lượt gọi model**.
> `SEALED_RESEARCH_BASELINE = a075e9f5…` không đổi, không chạy lại.
> `CURVED_ACCEPTANCE_V1`, `V2` bất biến — wave này **không sửa** artifact nào của chúng.
> §18 (probe 4 ca) và §20 **CHƯA CHẠY**: chờ user cho phép tiêu quota.

---

## 1. §16 — V1/V2 nay là DỮ LIỆU PHÁT TRIỂN

Tôi đã đọc chương trình sinh ra của cả 9+9 ca để tìm nguyên nhân. Sau khi đọc,
tập ấy **không còn là bằng chứng cuối** — nó đã tham gia vào việc thiết kế bản
sửa. Mọi con số dưới đây là số *phát triển*, và không được trích như kết quả
nghiệm thu.

## 2. §3 — tám ca hỏng thuộc mô hình, phân theo NGUYÊN NHÂN

Đã loại các ca hỏng vì lỗi HỆ (đã sửa ở `CURVED_OBLIGATION_COVERAGE_BRIDGE` và
`RADIUS_*`) — chúng không nói gì về ecgônômi.

| lớp | đếm | ca |
|---|---|---|
| **A · BỊA ĐIỂM PHỤ** — khai toạ độ cho điểm đề không nêu | **5** | V1 `cone_2`, V1 `circumsphere`, V2 `ball_2`, V2 `cylinder_1`, V2 `cone_2` |
| **D · SAI HÌNH DẠNG SCHEMA** — `construct_plane.through = None` | 3 | V1 `ball_2`, V1 `cylinder_2`, V2 `cylinder_2` |
| **B/C · KHAI MÀ KHÔNG DỰNG** | 1 | V2 `ball_1` (khai `I`,`S` kiểu `curved_solid`, không bao giờ dựng) |

Ba ca lớp D **thực chất cũng là một câu hỏi**: mô hình cần một mặt phẳng, chưa
có đủ ba tên điểm, và thay vì dựng điểm còn thiếu thì nó để trống ô `through`.
`cylinder_2` rõ nhất — `plane_perpendicular_to_line` **đã tồn tại** và giải
đúng bài ấy; mô hình không tìm ra nó.

Gộp lại: **8/8 ca hỏng là cùng một chỗ hụt** — *cần một vật chưa có thì làm gì?*
Mô hình chọn ba lối thoát (cho toạ độ · để trống · khai suông) thay vì lối thứ
tư (dựng nó).

### Vì sao chỗ hụt ấy đắt

Lớp A rơi vào mã grounding thuộc **`KHONG_DUOC_SUA`** — `pipeline` không gửi
ngược, nên **không có lượt sửa**. Một ca lớp A là hỏng hẳn ngay lượt đầu, trong
khi lớp D (schema) được sửa. Đây là lý do lớp A đáng trả giá byte hơn lớp D.

### Và prompt cũ hợp thức hoá đúng nước đi ấy

Prompt cũ, ở mục **toạ độ** — tách hẳn khỏi mục dựng hình:

> *"Toạ độ bạn chọn khai `model_assumption`; toạ độ đề cho khai `source_fact_id`."*

Đọc một mình, câu đó nói: *cần toạ độ gì cứ chọn, khai vào `model_assumption`.*
Nó **đúng** cho điểm gốc và **sai** cho mọi điểm dẫn xuất, nhưng chỗ đứng của
nó không phân biệt hai loại. Mô hình làm đúng thứ nó đọc được.

## 3. §5 — MỘT thẩm quyền prompt

```
SYNTHESIS_PROMPT_AUTHORITIES   1
  chủ sở hữu   domain_profile.program_skill_for(DOMAIN_HINH_HOC)
  file         app/ai/skills/geometry_program_generator.md
PARALLEL_CURVED_PROMPT         0
```

Hướng dẫn hình cong nằm **trong** chính sách tổng hợp đã có, không tách file.
Khoá bằng `test_E1`.

## 4. §13 — kích thước prompt

```
SYNTHESIS_PROMPT_BYTES_BEFORE   5612
SYNTHESIS_PROMPT_BYTES_AFTER    5674
DELTA                           +62      (trần 5700)
```

Bốn bất biến mới **gộp vào mục 2 đã có** (*"Dựng phần còn lại TỪ TÊN"*), không
mở mục mới — vì bản nháp đầu mở mục mới và phình **+1134 byte**: nó chồng lên
văn xuôi yếu sẵn có thay vì thay thế. Trả giá bằng bốn chỗ **thẻ văn phạm đã
nói**: ví dụ JSON `declare_point` · liệt kê ba lượng đo (đã cũ: nay có 7) · hai
câu trỏ ngược về thẻ. Kèm một sửa **byte trung tính**: ví dụ toạ độ in `a` trong
ô đòi số, đổi thành `1`.

### Một lỗi cổng lộ ra khi đo

Cổng ngân sách đọc `st_size`. Một số `.md` trên đĩa dùng **CRLF**, số khác dùng
**LF** — nên cổng so những thứ không cùng đơn vị: `geometry_program_generator.md`
đọc **5612** ở một nơi và **5707** ở nơi khác, **cùng một commit**. Trần 5700
đặt ở Phase 3 lấy từ số LF, nên nó **đã bị vượt ngay từ lúc đặt** và không ai
thấy. Nay `_byte_lf()` chuẩn hoá; mọi ngân sách quy đổi **giữ nguyên khoảng dôi
cũ**, không ai được nới.

## 5. §4 · §14 — không có năng lực nào mới

```
NEW_MEMORY_TYPES        0     NEW_IR_OPERATIONS   0
NEW_KERNEL_FUNCTIONS    0     NEW_CHECKERS        0
NEW_RENDER_KINDS        0     CURVED_PROBLEM_FAMILY_TEMPLATES   0
GROUNDING_WEAKENED      NO    R0                  PASS
```

Bằng chứng máy đối chiếu được — khoá danh tính nêu **đúng một** thành phần đổi:

```
prompts            c692df98… → 55ac1ca6…
grammar_card       2463652c…   KHÔNG ĐỔI
synthesis_schema   421e7aff…   KHÔNG ĐỔI
analyze_schema     a4d5ed7c…   KHÔNG ĐỔI
capability         024799b8…   KHÔNG ĐỔI   ← §4
```

## 6. §15 — bốn guard tĩnh, khoá BẤT BIẾN chứ không khoá câu chữ

`tests/semantic_program/test_synthesis_ergonomics.py`. Khoá câu chữ chỉ biến mỗi
lần sửa prompt thành một lượt cập nhật test máy móc, và người sửa sẽ học rằng
cách rẻ nhất để đi tiếp là chép câu mới vào test.

| guard | khoá điều gì | tiêm lỗi giả |
|---|---|---|
| `E1` | một thẩm quyền prompt, không có prompt cong song song | ĐỎ |
| `E2` | mọi định danh trong prompt tồn tại thật trong IR | ĐỎ |
| `E3` | `CURVED_PROBLEM_FAMILY_TEMPLATES = 0` (không lời giải mẫu) | ĐỎ |
| `E4` | 8 phép mà thẻ nhu cầu hứa còn nằm đúng union | ĐỎ |

`E2` chống **trôi một chiều**: đổi tên một phép trong `contract.py` thì test hợp
đồng đỏ, nhưng prompt vẫn nêu tên cũ và **không gì đỏ** — mô hình sinh ra tên đã
chết, `ir_static` bác, và lỗi đọc ra như *"mô hình kém"* chứ không như *"tài
liệu sai"*. Nó bắt được một chỗ ngay khi viết: thẻ nhu cầu hứa *"giao hai mặt"*
trong lúc `ConstructLineStmt` chỉ nhận hai điểm — phép ấy có thật, nhưng ở
`ValueExpr`, tới qua `assign`.

### Một quan sát ecgônômi KHÔNG sửa được ở wave này

`intersect_plane_plane`, `plane_perpendicular_to_line`, `intersect_plane_curved`
chỉ nằm trong `ValueExpr` — mô hình phải tới chúng qua `assign`, **hình dạng câu
lệnh khác** với `construct_*`. Ba trong số phép cần cho bài cong và bài ngoại
tiếp nằm sau một cú rẽ cú pháp. Sửa nó là đổi IR (`NEW_IR_OPERATIONS`), ngoài
phạm vi §2. Ghi lại để không phải tìm lại.

## 7. §21 — `CACHE_VERSION` 69 → 70

Cổng danh tính **đỏ trước khi làm mới** (exit 1), nêu đúng `prompts`. Bump là
bắt buộc và là loại kinh điển nhất: cache khoá theo *text chuẩn hoá +
CACHE_VERSION*, nên đề cũ sẽ trả về chương trình sinh bởi **prompt cũ** — tức đo
prompt mới bằng kết quả prompt cũ, rồi kết luận rằng sửa prompt chẳng thay đổi
gì. Bốn chỗ đã đồng bộ; candidate đã đóng băng lại (`4d8bfb51…`, 89 file).

⚠️ `gemini.load_skill()` cache prompt **trong tiến trình** ⇒ **restart backend**
trước bất kỳ lượt live nào, nếu không sẽ đo phải prompt cũ.

## 8. §17 — cổng tất định

| cổng | kết quả |
|---|---|
| `pytest` | **3070 passed**, 1 skipped |
| `vitest` | **687 passed** (50 tệp) |
| `npm run build` | PASS |
| `replay_demo_cases` | 5/5 · chuỗi rút gọn 1/1 |
| `audit_demo_crash_surface` | biên đúng 6/6 · ném ra ngoài **0** |
| `freeze_evaluation_candidate --verify` | 89 file · `4d8bfb51…` |
| `lock_cache_identity --verify` | version 70 |

```
BALL_PRODUCT_ENABLED  NO   CYLINDER_PRODUCT_ENABLED  NO   CONE_PRODUCT_ENABLED  NO
APPLICATION_LLM_CALLS  0
```

Ba cờ sản phẩm **không đổi một chữ** — sửa prompt không phải bằng chứng
discoverability.

### Một số cũ đã có sẵn, đáng nhắc

`audit_named_operand_ergonomics.py`: `HISTORICAL_NESTED_EXPR_ATTEMPTS = 23`,
`NORMALIZED_SAFELY = 23`, `STILL_REJECTED = 0`. Tức friction **cú pháp** (mô
hình lồng biểu thức vào ô nhận tên) đã được hoisting đóng **100%**. Friction còn
lại là **ngữ nghĩa** — hoisting không chạm tới, và đó đúng là thứ wave này nhắm.

## 9. §23 — V3 đã niêm phong, CHƯA rút

```
V3_POOL           26 bài · 13 ô (9 dương C1–C9 · 4 từ chối N1–N4)
POOL_HASH         36c2153ecefd2dbf…
MEASURED_SYSTEM   4d8bfb51692b7b84…  (89 file)
SEED              CHƯA CÓ — cần người ngoài
TUNED_AGAINST_V3  NO
```

Số liệu không trùng bộ ca V1/V2. Kỳ vọng **không gõ tay**: script tính lại từ
công thức SGK và từ chối niêm phong khi lệch (đã tiêm một đáp số sai — dừng
đúng). Số chính xác cài lại tại chỗ, **không dùng `radical.py`**, vì sinh kỳ
vọng bằng mô-đun sắp bị đo là tự soi gương.

⚠️ **Khai điều mất**: pool do tôi soạn **sau khi** đọc hết 8 ca hỏng, nên tôi
không độc lập với nó. Tính độc lập chỉ còn ở hai thứ kiểm được — pool băm
**trước** khi có seed, và seed do **người khác** chọn. Nếu seed cũng do tôi chọn
thì con số mất một bậc giá trị, và phải khai. Con dấu mang sẵn câu này.

## 10. §18 · §20 — CHƯA CHẠY

Probe 4 ca, one-shot, tiêu quota thật. Runner đã sẵn sàng
(`--ca`, `CA_HASH` giữ nguyên `8c6a184f…`, trần **20 api / 17 logic** thay vì
40/32), nhưng **chưa gọi lượt nào**.

Tập con đề nghị — mỗi ca đại diện một lớp hỏng ở §2:

| ca | đại diện |
|---|---|
| `ball_2` | A · bịa điểm phụ |
| `cylinder_2` | D · để trống `through` **và** bỏ sót `plane_perpendicular_to_line` |
| `ball_1` | B/C · khai mà không dựng |
| `circumsphere` | hợp thành sâu nhất (tâm phải DỰNG) |

⚠️ **Probe này KHÔNG phủ hồi quy từ chối.** Hai ca `refuse_*` đã ĐẠT ở V2 và
§8 cấm chạy lại ca đã đạt, nên rủi ro *"dựng, đừng cho toạ độ"* đẩy mô hình sang
dựng một thứ đáng lẽ phải từ chối **không được đo ở đây**. Nó thuộc V3 (ô
`N1–N4`), và phải nói ra trước khi ai đó đọc kết quả probe như một lượt xác nhận
đầy đủ.

§20 nhắc sẵn: **không có cải thiện thì báo thật**, không sửa prompt tiếp cho tới
khi ca phát triển xanh hết — làm thế là tuning lên dữ liệu phát triển, và con số
V3 sau đó sẽ không nói gì.
