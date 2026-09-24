# FACT_GRAPH_CONTRACT_EXTENSION

> Nhánh `feat/photo-problem-to-scene` · 2026-09-21.
> START_HEAD `e043ca6` · `main` giữ `085cae6`.
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/fact-graph-contract-extension/`.
> **0 request Gemini · 0 request mạng.**

```text
STRUCTURED_RELATION_KINDS = perpendicular_lines · perpendicular_line_plane
TEXT_RELATION_PARSING_ON_COMPILER_PATH = REMOVED
DEFAULT_MODE = LLM_ONLY        DEFAULT_ARCHITECTURE_CHANGED = NO
CANDIDATE f5d69a39… → aadda232…      CACHE_VERSION 97 → 98
FULL BACKEND (worktree sạch) = 5538 passed · 0 FAILED
```

## 1. Khoảng trống, đo trước khi sửa

Tại `e043ca6`, *"AB ⟂ AC"* và *"SA ⟂ (ABC)"* chỉ sống trong `InputFact.values`
dưới dạng **một câu tiếng Việt**. Chạy trên chính API lúc ấy:

| phép đo | kết quả tại `e043ca6` |
|---|---|
| `RequestContract` có trường quan hệ | **không** |
| *"vuông tại A"* vs *"góc A là góc vuông"* cho cùng FactGraph | **`False`** |
| chỉ có câu văn, không ai khai quan hệ ⇒ compiler | **`SUPPORTED`** |
| đề viết bằng tiếng Anh | quan hệ **biến mất** |

Ba dòng cuối là cùng một bệnh: tầng dựng tất định đang tin một chuỗi do mô hình
viết, và lời văn quyết định kết quả hình học.

## 2. Vì sao KHÔNG mở rộng `SourceInvariant`

Đây là phương án tài liệu gợi ý trước, và nó **sai vì một lý do đo được**.

`SourceInvariant` do **SERVER** phát từ câu văn của đề — bảy điểm phát, không
điểm nào do mô hình viết — và được tiêu thụ như **hậu điều kiện**
(`NormalizedSourceInvariantGate` kiểm nó trên trạng thái cuối).

Lập luận quyết định: wave đòi một trạng thái **đạt được** — *"đề có chữ vuông
góc nhưng không ai khai quan hệ ⇒ từ chối"*. Nếu quan hệ cũng sinh ra bằng cách
đọc câu văn như mọi `SourceInvariant` khác, thì trạng thái ấy **không bao giờ
tồn tại**, và phép kiểm nó thành bất khả.

Chọn **collection mới, có kiểu, do `analyze` khai**. Không tạo nguồn song song:
hai loại quan hệ này chưa từng có ở đâu khác trong hợp đồng, và bộ đọc từ vựng
văn bản — nguồn thứ hai thật sự — **bị gỡ trong cùng wave**.

## 3. Cái gì đổi

`structured_relations.py` mới: `GeometricRelation`, chuẩn hoá đường và mặt bằng
**sắp tên** (nên `AB ≡ BA`, và sáu hoán vị của `ABC` là một mặt phẳng), kiểm
tham chiếu điểm về `source_invariants`, khử trùng tất định, bốn mã từ chối ổn
định. `RequestContract` thêm trường **tuỳ chọn** `geometric_relations`.

Lược đồ `analyze` **của riêng miền hình học** thêm ô cùng tên — enum và arity
**dẫn từ module**, không chép tay; lược đồ Tin học không đổi một byte.

FactGraph lên `/2`: `perpendicular_lines` và `perpendicular_line_plane` **thay**
`perpendicular`/`right_angle`; `Fact.derived_from` chở chứng minh; `kiem_xuat_xu`
bác quan hệ suy ra không nêu được cha. Adapter lên `/2`: **bộ đọc từ vựng văn
bản gỡ hẳn**, không chuyển sang chế độ legacy.

## 4. Kết quả

| | |
|---|---|
| biến thể chuẩn hoá cho cùng `graph_hash` | **6/6** |
| ca dương `SUPPORTED` | **4/4** |
| ca âm bị từ chối, mỗi ca một mã riêng | **9/9** |
| phép tiêm lỗi bị bắt | **10/10** |
| test mới | **57** |

`AB ⟂ AC` và `SA ⟂ (ABC)` vào graph là **`GIVEN`**. `SA ⟂ AB`, `SA ⟂ AC` và
`SA ⟂ BC` là **`DERIVED`**, mỗi cái nêu **đúng hai cha**: quan hệ đường–mặt
nguồn, và fact `lies_in_plane` chứng minh cạnh nằm trong mặt ấy.

Compiler **chỉ nhận fact `GIVEN`** cho cả hai vai. Không có luật đó thì một
quan hệ đường–mặt duy nhất tự sinh ra một đáy vuông — một hệ quả hoá thành dữ
kiện thứ hai.

## 5. Tương thích ngược — và một điều phải khai thẳng

Hợp đồng cũ parse được, `exclude_defaults` không đổi một byte, và đường mặc
định cho **đầu ra trùng byte** giữa hai worktree sạch `e043ca6` ↔ `c25c4d2`
(`replay_demo_cases.py` 5/5 · `audit_demo_crash_surface.py` 6/6).

⚠️ Nhưng `model_dump` **đầy đủ** của `RequestContract` **có** thêm khoá
`geometric_relations: []`. Không giấu: đây là **thay đổi hợp đồng có chủ đích**.
Nó không phải hồi quy vì hợp đồng không bao giờ đi vào payload sản phẩm hay khoá
cache — thứ được cache là **envelope** — và hai nơi duy nhất đọc `model_dump`
đều đọc **theo khoá** (`coverage_gate.py:201`, `visual_obligations.py:185`).

## 6. Bump `CACHE_VERSION` 97 → 98

Hạng **"bề mặt mô hình đổi"**, đúng tiền lệ 78. Hai băm đổi và **đúng hai**:
`analyze_schema` `515001b5 → a1b9e20a` · `prompts` `c50c8c6b → d157c6e1`.
`grammar_card`, `synthesis_schema`, `capability` không đổi một byte.

Bắt buộc vì khoá cache là *text đã chuẩn hoá + `CACHE_VERSION`* — danh tính
lược đồ **không** nằm trong khoá — và `main.py` trả cache hit thẳng, không chạy
lại route. Envelope cũ chở một hợp đồng sinh dưới lược đồ **không có chỗ nào**
cho quan hệ vuông góc có cấu trúc.

Khai rõ chiều: **không envelope `ok` nào hoá sai**. Bump ở đây để mô hình không
tiếp tục được hỏi bằng một hợp đồng đã thay, chứ không phải để sửa một envelope
hỏng.

Độ lệch với con dấu `thesis-final`/V3 **được khai và dựng lại được**:
`analyze_schema_neu_chua_them_quan_he()` và `prompts_neu_chua_them_muc_quan_he()`
tái tạo đúng hai băm lịch sử. Không artifact nào bị sửa cho khớp.

## 7. Giới hạn

1. **Chưa có lượt live.** Wave chứng minh hệ *đọc được* ô mới, **không** chứng
   minh mô hình thật *khai đúng* ô ấy. Đó là `NEXT_ACTION`.
2. **Hai loại quan hệ, một họ hình.** Song song · thuộc đường · thuộc mặt ·
   thiết diện · quan hệ cong đều **chưa** có, có chủ đích.
3. **Compiler vẫn ngoài đường mặc định.** `DEFAULT_MODE = LLM_ONLY`, 0 tham
   chiếu trong `app/ai` và `main.py`; chưa consumer sản phẩm nào đọc trường mới.
4. **Một luật mới nghiêm hơn trước:** gỡ một độ dài cũng gỡ nhãn điểm khỏi hợp
   đồng, nên một quan hệ nhắc tới nhãn ấy bị bác là `STRUCTURED_RELATION_
   REFERENCE_UNKNOWN` chứ không phải *"thiếu độ dài"*. Phân biệt hai ca ấy được
   khoá bằng `test_H2` (điểm có giới thiệu, thiếu độ dài ⇒ `REQUIRED_LENGTH_MISSING`).
5. **Ngân sách prompt nới 4525 → 5350 byte.** Câu hỏi bắt buộc *"mã hoá xuống
   lược đồ được không"* đã hỏi trước: bốn luật xuống schema, ba luật còn lại
   không biểu diễn được nên ở lại prompt.

```text
TOKEN_OPTIMIZATION = NOT_PRODUCTION_ESTABLISHED
DEFAULT_ARCHITECTURE_CHANGED = NO
MERGE_ALLOWED = NO
NEXT_ACTION = STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_VALIDATION
```
