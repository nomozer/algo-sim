# AUDIT_MODEL_FACING_SCHEMA_SURFACE — lược đồ 111 KB KHÔNG hề được gửi đi

> Thực hiện **2026-09-04**, HEAD `e87fbc1`, cây sạch.
> **SOURCE_CHANGES = 0 · APPLICATION_LLM_CALLS = 0.** Không đổi lược đồ, prompt,
> thẻ, IR, runtime. V3 không chạy, pool niêm phong, seed chưa rút.

## 0. Kết luận trước — và nó lật tiền đề của chính wave này

```
SCHEMA_SURFACE_OVERBROAD          = YES  (nhưng KHÔNG theo cách ta tưởng)
MODEL_CONTRACT_ERGONOMICS_GAP     = YES  (nằm ở THẺ, không ở lược đồ)
NON_GEOMETRY_OPERATIONS_SELECTABLE = YES  ← lỗ thật, chưa ai thấy
STATEMENT_EXPR_DISCOVERABILITY    = WEAK
OPERAND_NAMING_CONSISTENCY        = WEAK
MODEL_SCHEMA_AUTHORITIES          = 1
BALL_2_SCHEMA_FIXABLE             = NO
```

⚠️ **ĐÍNH CHÍNH BÁO CÁO TRƯỚC — và tiền đề của đề bài wave này.**
`AUDIT_SYNTHESIS_BOTTLENECK §11` viết *"92% vật liệu gửi mô hình là lược đồ
111 KB"*. **Sai.** Tôi đo thứ được **tính ra**, không đo thứ được **gửi đi**.

```
generate_json_schema()   111.152 byte · 56 $defs · 794 `$ref`
_sanitize_gemini_schema  → None            ← có `$ref` ⇒ Gemini không diễn đạt được
responseSchema gửi đi    (không có)
```

`gemini.call_gemini` bỏ hẳn schema khi nó chứa `$ref`, giữ mỗi
`responseMimeType: application/json`. Chú thích tại chỗ nói rõ:
*"Gửi kèm là HTTP 400 cho MỌI lượt gọi. Bỏ schema, giữ JSON mode; ràng buộc
thật vẫn do validator phía server áp."*

**Mô hình chưa bao giờ nhìn thấy lược đồ ấy.**

## 1. Hợp đồng THẬT SỰ gửi cho mô hình

Dựng lại nguyên văn payload một lượt tổng hợp hình học (`cylinder_2`):

| thành phần | byte | tỉ lệ |
|---|---|---|
| `systemInstruction` — `geometry_program_generator.md` | 5 674 | **53.9%** |
| user · đề bài | 262 | 2.5% |
| user · dữ kiện | 142 | 1.3% |
| user · nghĩa vụ | 416 | 3.9% |
| user · **thẻ văn phạm** | 4 035 | **38.3%** |
| `responseSchema` | **0** | 0.0% — bị bỏ |
| **MODEL_CONTRACT_TOTAL_BYTES** | **10 535** | |

### Kiểm chéo bằng telemetry THẬT (§20)

`run2`, stage `semantic_program`: **13 lượt · 39 392 input token** ⇒ **3 030
token/lượt**. Hợp đồng dựng lại 10 535 byte ÷ 3.48 byte/token ≈ **3 027 token**.
Khớp.

Nếu lược đồ 111 KB thật sự được gửi, riêng nó đã ~**31 900 token/lượt** — gấp
hơn mười lần con số đo được. Dữ liệu sống xác nhận độc lập rằng nó không được gửi.

```
FULL_SCHEMA_ESTIMATED_TOKENS          ~31.900   (KHÔNG gửi)
MODEL_CONTRACT_ESTIMATED_TOKENS        ~3.030   (đo thật)
```

## 2. Lược đồ được dùng ở đâu (§4)

`generate_json_schema()` có đúng **hai** người gọi:

| nơi | dùng làm gì |
|---|---|
| `pipeline.py:371` | truyền vào `call_gemini` → **bị sanitizer bỏ** |
| `runtime_identity.py:250` | băm thành vân tay `synthesis_schema` |

Nên nó tốn CPU mỗi lượt gọi, tham gia **danh tính môi trường**, và **không tham
gia hợp đồng mô hình**. `SCHEMA_GENERATION_OWNER` = `contract.generate_json_schema`
(= `SemanticProgramSpec.model_json_schema()`), `MODEL_SCHEMA_AUTHORITIES = 1`.

## 3. Khả năng tới được (§3, §5, §6)

```
TOTAL_DEFS                      56
reachable từ gốc đầy đủ         56      ⇒ UNREACHABLE_DEFS = 0 (không có rác thuần)
GEOMETRY_REACHABLE_DEFS         35
NON_GEOMETRY_REACHABLE_DEFS     21      BreakStmt PushStmt PopStmt EnqueueStmt
                                        ForRangeStmt IfStmt MapSetStmt LogicCond …
SCHEMA_BYTES_FULL               111.152
SCHEMA_BYTES_GEOMETRY_REACHABLE  58.131
REDUCTION_IF_PRUNED               47.7%
```

⚠️ **Cắt 47.7% ấy giảm ĐÚNG 0 byte trên bề mặt mô hình**, vì lược đồ không được
gửi. Nó chỉ giảm CPU và làm vân tay `synthesis_schema` hẹp lại.

`SCHEMA_PRUNING_SEMANTICALLY_SAFE = PARTIAL`, và lý do là một phát hiện riêng:

> **Thu hẹp tập CÂU LỆNH không thu hẹp được tập BIỂU THỨC.**
> `AssignStmt.expr` trỏ **toàn bộ** union `ValueExpr` — 21 nhánh, trong đó
> **6 nhánh không thuộc từ vựng hình học** (`field`, `index`, `length`,
> `map_get`, `neighbors`, `peek`). Một phép chiếu thật sự phải viết lại cả
> trường ấy, tức sinh ra một **model Pydantic khác** — nguy cơ đúng thứ §21/§22
> cấm: một thẩm quyền lược đồ thứ hai.

Và ngay cả khi cắt xong, nó **vẫn không gửi được**: đồ thị con hình học **có
đệ quy** — 21 chu trình, qua `BinaryArithExpr`, `FieldRefExpr`, `IndexRefExpr`.
Nội suy hết `$ref` sẽ nổ như module đã ghi (296 KB ở độ sâu 2, 3 MB ở độ sâu 3).

⇒ **Cắt tỉa KHÔNG biến lược đồ thành ràng buộc giải mã được.** Đó là gạch tên
ứng viên A ở dạng ngây thơ nhất của nó.

## 4. Lỗ THẬT: ranh giới miền không có gì canh (§15, §16)

Vì không có `responseSchema`, thứ duy nhất giữ mô hình trong miền hình học là
**văn bản thẻ**. Kiểm bằng máy — một chương trình hình học có câu lệnh `push`:

| tầng | phán quyết |
|---|---|
| Pydantic (`SemanticProgramSpec`) | **NHẬN** — `push` là nhánh hợp lệ của union |
| `validate_semantic_program` | **NHẬN** |
| thẻ gửi mô hình có nhắc `push`? | **KHÔNG** |
| `verify_and_compile` (trọn route) | **`served` · executable · servable** |

```
NON_GEOMETRY_OPERATIONS_SELECTABLE = YES   (§15 phương án B, không phải A)
GEOMETRY_SCHEMA_ROOT               = SemanticProgramSpec (dùng chung mọi miền)
GEOMETRY_SCHEMA_ROOT_SPECIFICITY   = WEAK
```

Một chương trình trộn miền đi hết đường và được **phục vụ**. Chưa quan sát thấy
mô hình làm thế — vì thẻ không quảng cáo — nhưng đó là **kỷ luật bằng lời**,
không phải bằng cấu trúc. Đây là lỗ chưa có trong bất kỳ báo cáo nào trước.

## 5. Ranh giới CÂU LỆNH ↔ BIỂU THỨC — đo trong THẺ (§7, §8, §9, §12)

Vì thẻ *là* hợp đồng, mọi câu hỏi §7–§9 phải hỏi về thẻ.

`GRAMMAR_STRUCTURAL_GROUPING = MIXED`: thẻ **có** hai tiêu đề nhóm (9 câu lệnh ·
15 biểu thức), nhưng affordance ở mức từng dòng **bằng không**.

| phép | dòng | cách tiêu đề nhóm | cách `assign` |
|---|---|---|---|
| `construct_point` | 15 | 5 | — |
| `construct_section` | 17 | 7 | — |
| `intersect_plane_curved` | 26 | 5 | **15** |
| `measure` | 29 | 8 | 18 |
| `midpoint` | 30 | 9 | 19 |
| `vector_from_points` | 36 | 15 | **25** |

### `INTERSECT_PLANE_CURVED_SCHEMA_PATH` (ca chấp nhận `cylinder_2`)

```
`kind` định nghĩa ở đâu   : dòng 26 của thẻ (chuỗi ký tự, không phải nút lược đồ)
chữ ký toán hạng          : cùng dòng ấy
"nó là BIỂU THỨC"         : suy từ TIÊU ĐỀ cách đó 5 dòng — không có dấu trên dòng
"biểu thức nằm trong assign": suy từ dòng 11, cách 15 dòng
số bước cấu trúc nối ba dữ kiện: 2 bước SUY LUẬN VỊ TRÍ, 0 bước tham chiếu
```

**Cặp bẫy, đo được:**

```
dòng 17  construct_section:      target_var  solid:tên<solid>        plane:tên<plane3>   ← CÂU LỆNH
dòng 26  intersect_plane_curved:             solid:tên<curved_solid> plane:tên<plane3>   ← BIỂU THỨC
```

Cùng tên toán hạng, hình dạng gần trùng, cách nhau 9 dòng, ranh giới nhóm ở
dòng 21 — và **không dấu hiệu nào trên chính dòng** nói nó thuộc nhóm nào. Suy
loại suy từ dòng 17 sang dòng 26 là con đường ngắn nhất tới đúng lỗi đã xảy ra.

```
STATEMENT_EXPR_DISCOVERABILITY = WEAK
```

## 6. Tên toán hạng (§10) — tính lại từ HEAD

`VECTOR_FROM_POINTS_SCHEMA_PATH`: dòng 36 của thẻ,
`from_point:tên<point3> to_point:tên<point3>`; trong lược đồ là
`$defs.VectorFromPointsExpr` — **nhưng lược đồ không được gửi**, nên biểu diễn
mô hình thấy chỉ có dòng thẻ ấy.

| quy ước | phép |
|---|---|
| `a` / `b` | `divide_segment`, `midpoint` |
| `through_a` / `through_b` | `construct_line` |
| `anchor` / `rim_point` | `construct_curved_solid` |
| `from_point` / `to_point` | **`vector_from_points`** |

```
TWO_POINT_OPERAND_CONVENTIONS = 4 quy ước / 5 phép
OPERAND_NAMING_CONSISTENCY    = WEAK
```

Quy ước đông nhất là `a`/`b` (2/5). `vector_from_points` là phép **duy nhất**
dùng `from_`/`to_`. Bằng chứng độc lập rằng đây là bẫy thật chứ không phải lỗi
mô hình: khi viết `certify_acceptance_runner.py` tôi gõ `{"a": …, "b": …}` cho
chính phép ấy và bị Pydantic bác — cùng lỗi, cùng ngày, với thẻ mở trước mặt.

## 7. Thẻ ↔ lược đồ (§13)

`SCHEMA_GRAMMAR_RELATION = KHÔNG PHẢI ĐỐI THỦ, vì chỉ một bên tồn tại với mô
hình.` Thẻ sinh từ chính `contract.py`, nên nó là **gương của lược đồ**, không
phải một biểu diễn cạnh tranh — và vì lược đồ không được gửi, mô hình **không
nhận cùng một chữ ký hai lần**. Không có trùng lặp nào để gỡ.

`PROVIDER_STRUCTURED_OUTPUT_MODE = JSON mode ONLY (không constrained decoding)`.

## 8. Đối chiếu lỗi ↔ tính chất hợp đồng (§17–§19)

| ca | nguyên nhân | lược đồ sửa được? |
|---|---|---|
| `cylinder_2` | nhầm CÂU LỆNH ↔ BIỂU THỨC | **có thể** — nhưng ở THẺ, không ở lược đồ |
| `circumsphere` | sai tên toán hạng | **có thể** — ở THẺ / thẩm quyền chữ ký |
| `ball_1` | lỗ HỆ ở `learner_surface` | đã đóng, không liên quan |
| `ball_2` | **thiếu đường dựng trong IR** | **KHÔNG** |

```
BALL_2_SCHEMA_FIXABLE      = NO
CIRCUMSPHERE_SCHEMA_FIXABLE = POSSIBLE (ecgônômi hợp đồng, không phải suy luận)
```

`ball_2` giữ vai **đối chứng âm**: `construct_curved_solid` đòi hai điểm CÓ TÊN,
đề chỉ cho tâm + một số, và không phép nào trong 15 biểu thức sinh được một điểm
từ *một điểm + một độ dài*. Không hợp đồng nào chữa được điều đó — giữ nó ở đây
để không ghi công quá tay cho việc sửa hợp đồng.

⚠️ `circumsphere` **đã có đủ ngữ cảnh sửa** sau `REPAIR_FRAGMENT_COMPLETENESS`
mà vẫn hỏng ba lượt cùng một lỗi tên toán hạng. Ngữ cảnh đủ là **điều kiện cần,
chưa đủ**.

## 9. Ba ứng viên (§25–§27, §32)

### CANDIDATE_1 — `CARD_CATEGORY_AFFORDANCE` (sinh, không phải văn xuôi)

Đánh dấu nhóm **ngay trên từng dòng** của thẻ và nêu cửa tiêu thụ ngay tại chỗ
— ví dụ mỗi biểu thức in kèm khuôn `assign(target_var, expr=…)` — tất cả **sinh
từ `_tap_hinh_hoc()`**, không thêm một dòng văn xuôi nào vào prompt.

| | |
|---|---|
| ROOT_CAUSE_COVERAGE | `cylinder_2` + mọi lỗi nhầm nhóm sau này |
| MODEL_SURFACE_REDUCTION | ~0 (có thể +vài trăm byte) |
| IR_LANGUAGE_CHANGE | **KHÔNG** |
| RUNTIME_CHANGE | **KHÔNG** |
| COMPATIBILITY_RISK | thấp — chỉ đổi cách in |
| IMPLEMENTATION_COMPLEXITY | thấp, một hàm sinh |
| TOKEN_IMPACT | +~5% một lượt |
| CACHE | **vân tay `grammar_card` ĐỔI** ⇒ phải cân nhắc bump |

### CANDIDATE_2 — `DOMAIN_ROOT_TIGHTENING`

Đóng lỗ §4: chương trình hình học không được chứa câu lệnh/biểu thức ngoài miền.
Thi hành **tất định phía server** (một cổng đọc `_tap_hinh_hoc()`), **không**
bằng lược đồ gửi đi.

| | |
|---|---|
| ROOT_CAUSE_COVERAGE | 0 lỗi ĐÃ quan sát — đây là phòng thủ, không phải chữa |
| IR_LANGUAGE_CHANGE | **CÓ** (hẹp lại tập chấp nhận) |
| RUNTIME_CHANGE | thêm một cổng |
| COMPATIBILITY_RISK | **trung bình** — có thể bác chương trình lịch sử từng hợp lệ |
| IMPLEMENTATION_COMPLEXITY | thấp–trung bình |
| CACHE | có thể bump (phán quyết đổi) |

### CANDIDATE_3 — `OPERAND_NAME_CONVERGENCE`

Bốn quy ước cho cặp điểm. **Không đổi tên** trong wave này (§11) — rủi ro phá
tương thích, artifact lịch sử, ca thử. Ba lối khả dĩ cho sau: alias ở biên
model-facing · đổi tên chính tắc · chỉ dẫn chữ ký sinh kèm.

| | |
|---|---|
| ROOT_CAUSE_COVERAGE | `circumsphere` |
| IR_LANGUAGE_CHANGE | **CÓ** nếu đổi tên; **KHÔNG** nếu chỉ alias |
| COMPATIBILITY_RISK | **cao** cho đổi tên |
| IMPLEMENTATION_COMPLEXITY | trung bình–cao |
| CACHE | bump chắc chắn |

### Xếp hạng

```
P0  CANDIDATE_1  CARD_CATEGORY_AFFORDANCE
P1  CANDIDATE_3  OPERAND_NAME_CONVERGENCE (dạng ALIAS, không đổi tên)
P2  CANDIDATE_2  DOMAIN_ROOT_TIGHTENING
```

P0 vì nó nhắm đúng lỗi **đã quan sát được**, không đổi ngôn ngữ IR, không đổi
runtime, rủi ro thấp nhất — và vì nó tác động lên **thứ mô hình thật sự đọc**.

P2 xếp sau dù là lỗ thật: nó chưa gây ra một thất bại nào đo được, và nó **hẹp
tập chấp nhận**, tức có rủi ro hồi quy mà không có lợi ích quan sát được.

## 10. Bác bỏ

| đề xuất | phán quyết |
|---|---|
| cắt tỉa lược đồ để giảm bề mặt mô hình | **REJECTED** — lược đồ không được gửi; giảm 0 byte |
| nhồi thêm văn xuôi vào prompt | **REJECTED** — `NO_MEASURABLE_GAIN` đã đo |
| một wave mảnh-sửa nữa | **REJECTED** — `REPAIR_FRAGMENT_COMPLETENESS` đã đóng, audit này không tìm thấy khuyết tật riêng nào của nó |
| giải `ball_2` ở đây | **REJECTED** — `BALL_CENTER_RADIUS_EXPRESSIVENESS` là wave riêng |
| chạy V3 | **REJECTED** — 0/4 ca phát triển phục vụ được |

## 11. Hệ quả phiên bản (§23, §24) — ghi cho wave sau

Ba trục **phải tách**, và audit này cho thấy vì sao:

| trục | đổi khi nào | ai băm |
|---|---|---|
| `MODEL_CONTRACT_VERSION` | thẻ / prompt đổi | `semantic_environment_hash` (thành phần `grammar_card`, `prompts`) |
| `IR_LANGUAGE_VERSION` | tập chấp nhận của Pydantic/validator đổi | `synthesis_schema` + candidate |
| `RUNTIME_CAPABILITY` | phép dựng/đo/checker đổi | `stable_capability_hash` |

Ứng viên 1 đụng **trục 1** (thẻ) mà **không** đụng trục 2 và 3 — nên bằng chứng
toán học lịch sử **không** bị vô hiệu, chỉ số tổng hợp mới cần đo lại. Đó chính
là phân biệt §23 đòi.

## 12. Giới hạn của audit này

- Bốn ca sống. Mọi phát biểu tần suất là mô tả.
- Chưa đo được **prompt skill 5 674 byte** (53.9% hợp đồng) nói gì về ranh giới
  nhóm — audit này soi thẻ và lược đồ, không soi nội dung prompt. Nếu ứng viên 1
  được làm, nên soi cả prompt trước, để không thêm một chỗ nói cùng một điều.
- `NON_GEOMETRY_OPERATIONS_SELECTABLE = YES` mới chỉ chứng minh trên `push`.
  Chưa quét toàn bộ 21 nhánh ngoài miền.

## 13. Quyết định

```
MODEL_SCHEMA_AUTHORITIES            1
GEOMETRY_SCHEMA_ROOT                SemanticProgramSpec (chung mọi miền)
GEOMETRY_SCHEMA_ROOT_SPECIFICITY    WEAK
NON_GEOMETRY_OPERATIONS_SELECTABLE  YES
SCHEMA_SURFACE_OVERBROAD            YES — nhưng KHÔNG tới mô hình
SCHEMA_PRUNING_SEMANTICALLY_SAFE    PARTIAL (và vô ích cho bề mặt mô hình)
STATEMENT_EXPR_DISCOVERABILITY      WEAK
OPERAND_NAMING_CONSISTENCY          WEAK
BALL_2_SCHEMA_FIXABLE               NO
MODEL_CONTRACT_ERGONOMICS_GAP       YES  (ở THẺ)
SYSTEM_FOUNDATION_GAP_REMAINING     YES  — BALL_CENTER_RADIUS_EXPRESSIVENESS

NEXT_ACTION = CARD_CATEGORY_AFFORDANCE
              (sinh từ `_tap_hinh_hoc()`, 0 lượt gọi model, không đổi IR/runtime;
               soi prompt skill trước để không nói cùng một điều hai chỗ)
```
