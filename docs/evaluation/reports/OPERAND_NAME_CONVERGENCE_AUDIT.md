# OPERAND_NAME_CONVERGENCE_AUDIT — tên toán hạng KHÔNG nên hội tụ

> Thực hiện **2026-09-04**, HEAD `86eb2fb`, cây sạch.
> **SOURCE_CHANGES = 0 · APPLICATION_LLM_CALLS = 0.** Không đổi tên trường,
> không thêm alias, không đổi IR/runtime/lược đồ. V3 không chạy, pool niêm
> phong, seed chưa rút.

## 0. Kết luận trước — và nó bác chính tên của wave

```
OPERAND_NAMING_CONSISTENCY          = MIXED  (không phải WEAK như đã báo)
VECTOR_FROM_POINTS_ERROR_IS_NAMING_ONLY = YES
FIELD_ORDER_SEMANTICS_REQUIRED      = PARTIAL — 3 phép CÓ thứ tự, 2 phép KHÔNG
MODEL_FACING_ALIAS_SAFE             = NO
GENERATED_ROLE_HINT_SAFE            = YES
CANONICAL_RENAME_SAFE               = NO
SIGNATURE_AUTHORITIES               = 1
```

⚠️ **"Hội tụ tên toán hạng" là hướng SAI, và bằng chứng nói ngược lại.** Bốn
trong năm phép có tên **khớp đúng ngữ nghĩa** của chúng. Ép chúng về một quy ước
chung sẽ làm ba phép nói dối. Xem §3.

## 1. Năm phép, bốn quy ước — dẫn từ thẩm quyền (§2)

Đọc thẳng `_CHU_KY` + `_TOAN_HANG_LENH`, không kiểm kê tay:

| phép | loại | toán hạng `point3` |
|---|---|---|
| `divide_segment` | BIỂU THỨC | `a`, `b` |
| `midpoint` | BIỂU THỨC | `a`, `b` |
| `construct_line` | LỆNH | `through_a`, `through_b` |
| `vector_from_points` | BIỂU THỨC | `from_point`, `to_point` |
| `construct_curved_solid` | LỆNH | `anchor`, `apex_or_top`, `rim_point` |

```
TWO_POINT_OPERATIONS          = 5
TWO_POINT_OPERAND_CONVENTIONS = 4
```

## 2. `circumsphere` — lỗi là TÊN, và chứng minh được (§4)

Artifact `run2`, hai chặng, và chúng **khác nhau**:

| chặng | chỗ hỏng | dạng lỗi |
|---|---|---|
| one-shot | `construct_plane.through` ×3 · `construct_line.through_a`/`through_b` | `input_value=None` |
| sửa | `vector_from_points.from_point`/`to_point` ×2 cặp | `input_value=None` |

⚠️ **Lượt đầu KHÔNG hỏng ở `vector_from_points`** — nó hỏng ở `through*`. Báo
cáo trước gộp cả ca thành *"lỗi tên toán hạng `vector_from_points`"*; chính xác
hơn: **hai lượt, hai phép, cùng một hình dạng lỗi.**

### Chứng minh dạng lỗi ấy = "sai tên toán hạng"

Thí nghiệm tất định — cấp SAI tên cho `vector_from_points`:

| cấp vào | kết quả |
|---|---|
| `a`/`b` (quy ước đông nhất) | `Input should be a valid string, input_value=None` |
| `through_a`/`through_b` | **cùng lỗi** |
| `from`/`to` | **cùng lỗi** |
| `from_point`/`to_point` | **NHẬN** |

Trùng khít dạng lỗi trong artifact. Và tôi mắc **đúng** lỗi ấy khi viết
`certify_acceptance_runner.py` (gõ `{"a": …, "b": …}`), cùng ngày, với thẻ mở
trước mặt.

```
VECTOR_FROM_POINTS_ERROR_IS_NAMING_ONLY = YES
GEOMETRY_REASONING_REQUIRED_FOR_THIS_ERROR = NO
```

### ⚠️ Phát hiện phụ, và nó đắt hơn cả tên

`model_config` của mọi model là **mặc định** ⇒ Pydantic **bỏ qua khoá lạ**. Nên
khi mô hình gửi `a`/`b`, hai khoá ấy **biến mất trước khi thẩm định báo lỗi**,
và thông điệp chỉ nói được *"`from_point` là None"*.

**Thông điệp lỗi KHÔNG THỂ nói *"bạn dùng `a`/`b`, cần `from_point`/`to_point`"*
— vì tới lúc báo lỗi nó không còn biết mô hình đã dùng gì.**

Đây là lý do vòng sửa không cứu được ca: mảnh hợp đồng nay ĐÃ chứa chữ ký đúng
(`REPAIR_FRAGMENT_COMPLETENESS`), nhưng lời từ chối vẫn không nói mô hình sai ở
đâu — nó chỉ nói một ô rỗng.

## 3. Ngữ nghĩa cặp toán hạng — đo bằng kernel (§7)

Đảo thứ tự hai toán hạng, kết quả có đổi không:

| phép | tên | đảo thứ tự | phân loại | tên có KHỚP ngữ nghĩa? |
|---|---|---|---|---|
| `midpoint` | `a`/`b` | **không đổi** | UNORDERED | ✅ |
| `construct_line` | `through_a`/`through_b` | **không đổi** (cùng đường) | UNORDERED | ✅ |
| `vector_from_points` | `from_point`/`to_point` | **đổi dấu** | **ORDERED** | ✅ |
| `construct_curved_solid` | `anchor`/`apex_or_top`/`rim_point` | vai trò khác hẳn | ROLE_DISTINCT | ✅ |
| **`divide_segment`** | **`a`/`b`** | **`(8,4,0)` ↔ `(−4,−2,0)`** | **ORDERED** | ❌ **tên NÓI DỐI** |

```
FIELD_ORDER_SEMANTICS_REQUIRED = PARTIAL
OPERAND_NAMING_CONSISTENCY     = MIXED   (không phải WEAK)
```

**Bốn trên năm phép đặt tên ĐÚNG theo ngữ nghĩa.** `from_point`/`to_point` là
tên **chính xác** cho một phép có thứ tự — đổi nó thành `a`/`b` là biến một tên
đúng thành một tên nói dối, đúng bệnh mà `divide_segment` đang mắc.

Chỗ hỏng thật, và nó ngược với giả thiết của wave: **`divide_segment` dùng tên
ĐỐI XỨNG cho một phép CÓ THỨ TỰ.**

## 4. Ba ứng viên

### CANDIDATE_A — alias ở biên model-facing · **KHÔNG AN TOÀN**

| | |
|---|---|
| ROOT_CAUSE_COVERAGE | 0 — xem dưới |
| IR_LANGUAGE_CHANGE | CÓ |
| COMPATIBILITY_RISK | **CAO** |
| CACHE_IMPACT | bump |
| IMPLEMENTATION_COMPLEXITY | trung bình |

Hai lý do giết nó, cả hai đo được:

**① Alias VÔ HÌNH với mô hình (§15).** `responseSchema` **không được gửi**, nên
thứ duy nhất truyền tên là **thẻ**. Mà `_truong` đọc `model_fields.items()` —
**tên trường**, không đọc `f.alias`. Thêm alias mà không sửa `_truong` thì mô
hình không bao giờ biết alias tồn tại ⇒ phủ 0 lỗi.

**② Alias mặc định THAY THẾ tên gốc.** Pydantic v2 chỉ nhận alias trừ khi bật
`populate_by_name`. Quên nó là **mọi chương trình lịch sử, fixture và artifact
dừng parse** — 26 file dưới `docs/evaluation/` chứa `from_point`; `through_a`
xuất hiện 71 lần trong `tests/`, 26 lần trong `scripts/`.

Và nếu thẻ in **cả hai** tên thì hợp đồng có hai cách nói một điều — đúng thứ
§8 gọi là "ambiguous duplicate inputs".

### CANDIDATE_B — gợi ý VAI TRÒ sinh từ `description` · **AN TOÀN, P0**

Thẻ hiện **bỏ qua** `Field(description=…)` (module docstring nói rõ). Nhưng mọi
ô toán hạng đã có mô tả, và chúng là thẩm quyền sẵn có:

```
VectorFromPointsExpr.from_point   'tên điểm gốc'
VectorFromPointsExpr.to_point     'tên điểm ngọn'
DivideSegmentExpr.a               'tên điểm đầu'
ConstructCurvedSolidStmt.anchor   'tên TÂM (cầu) hoặc TÂM ĐÁY (trụ, nón)'
```

Hình dạng khái niệm: `from_point:tên<point3>[điểm gốc]`.

| | |
|---|---|
| ROOT_CAUSE_COVERAGE | không sửa được lỗi gõ sai tên, nhưng **nói được vai trò** nên giảm lý do đoán tên |
| MODEL_SURFACE_DELTA | **+295 byte (+6.4%)** cho 11 ô của 5 phép |
| IR_LANGUAGE_CHANGE | **KHÔNG** |
| RUNTIME_CHANGE | **KHÔNG** |
| COMPATIBILITY_RISK | **THẤP** — chỉ đổi cách in thẻ |
| HISTORICAL_ARTIFACT_IMPACT | **KHÔNG** |
| CACHE_IMPACT | bump (bề mặt mô hình đổi, đúng tiền lệ 65/70/73) |
| SIGNATURE_AUTHORITIES | vẫn **1** — mô tả nằm cùng chỗ với tên trường |
| ⚠️ | **vượt trần thẻ hiện tại** (4 882 > 4 650) ⇒ phải nâng trần có lý do, hoặc rút ngắn mô tả tại nguồn |

### CANDIDATE_C — đổi tên chính tắc · **KHÔNG AN TOÀN**

Phá: chương trình đã cache · 26 artifact lịch sử · 71+26 chỗ trong tests/scripts
· lược đồ đã export (hai bản mirror) · fixture · `_CHU_KY` · interpreter ·
grounding. Và **hướng đổi phổ biến nhất (về `a`/`b`) là hướng SAI** theo §3.

```
CANONICAL_RENAME_SAFE = NO
```

### Ma trận tương thích (§11)

| | A (alias) | B (gợi ý vai trò) | C (đổi tên) |
|---|---|---|---|
| chương trình CŨ → hệ MỚI | **FAIL** nếu quên `populate_by_name` | **PASS** | **FAIL** |
| chương trình MỚI → hệ CŨ | FAIL | **PASS** | FAIL |
| đọc artifact lịch sử | PARTIAL | **PASS** | FAIL |
| cache hit | bump | bump | bump |
| mẫu offline đã lưu | PARTIAL | **PASS** | FAIL |
| đường sửa | PARTIAL | **PASS** (mảnh cắt từ thẻ nên tự có) | FAIL |

### Xếp hạng

```
P0  CANDIDATE_B   gợi ý VAI TRÒ sinh từ `description`
P1  (mới, xem §5) thông điệp lỗi nêu được KHOÁ LẠ
P2  CANDIDATE_A / CANDIDATE_C — không khuyến nghị
```

## 5. Ứng viên nảy ra từ audit, và nó có thể mạnh hơn P0

§4② cho thấy vòng sửa mù vì Pydantic **nuốt khoá lạ**. Một cổng đọc khoá lạ
**trước** khi thẩm định (hoặc `extra="forbid"` ở biên model-facing) sẽ đổi lời
từ chối từ

> `from_point: Input should be a valid string, input_value=None`

thành

> *"`vector_from_points` nhận `from_point`/`to_point`; bạn gửi `a`/`b`."*

Đó là thứ **nói đúng lỗi mô hình vừa mắc**, và nó phủ **mọi** phép, không riêng
năm phép hai điểm. Nhưng `extra="forbid"` **hẹp tập chấp nhận** ⇒ có thể bác
chương trình lịch sử từng hợp lệ ⇒ rủi ro tương thích, phải audit riêng.

Ghi lại làm `STRICT_OPERAND_DIAGNOSTIC`, **không** làm ở đây.

## 6. Đối chứng (§17–§19)

```
BALL_2_AFFECTED            NO   — tâm + số vẫn không sinh được điểm vành;
                                  không tên nào chữa được điều đó
CYLINDER_2                 đã do CARD_CATEGORY_AFFORDANCE xử lý; audit này
                           KHÔNG nhận công
DOMAIN_ROOT_TIGHTENING     OPEN — `push` vẫn đi tới `served`
R0_RISK                    A: THẤP · B: **THẤP** · C: TRUNG BÌNH (đổi tên chạm
                           `source_fact_id`/first-binding ở nhiều chỗ)
```

## 7. Giới hạn — khai thẳng

- **Văn bản thô của `circumsphere` KHÔNG được lưu** (`raw_candidates: 0`) — bản
  vá lưu thô có sau lượt run2. Nên tôi **suy** "sai tên" từ dạng lỗi, không đọc
  được mô hình đã gõ gì. Dạng lỗi ấy chỉ sinh ra từ khoá sai/thiếu (chứng minh ở
  §2), nhưng một `"from_point": null` viết thẳng cũng cho cùng dạng. Lượt probe
  sau sẽ có văn bản thô và giải quyết dứt điểm.
- Một ca sống. Không suy tần suất.
- §5 chưa đo chi phí/rủi ro của `extra="forbid"` trên toàn bộ tập chương trình
  lịch sử.

## 8. Quyết định

```
OPERAND_NAMING_CONSISTENCY              MIXED
VECTOR_FROM_POINTS_ERROR_IS_NAMING_ONLY YES
FIELD_ORDER_SEMANTICS_REQUIRED          PARTIAL
MODEL_FACING_ALIAS_SAFE                 NO
GENERATED_ROLE_HINT_SAFE                YES
CANONICAL_RENAME_SAFE                   NO
SIGNATURE_AUTHORITIES                   1
HISTORICAL_ARTIFACT_COMPATIBILITY       B: PASS · A/C: FAIL
CACHE_IMPLICATIONS                      B: bump theo tiền lệ 65/70/73

NEXT_ACTION = OPERAND_ROLE_HINTS
              (sinh từ `Field(description=…)`, chỉ ô toán hạng; 0 lượt gọi
               model; không đổi IR/runtime/tên trường; kèm quyết định trần thẻ)
```

⚠️ **Không hội tụ tên.** Bốn trên năm phép đang đặt tên đúng ngữ nghĩa; việc cần
làm là **nói ra vai trò**, không phải xoá sự khác biệt. Nếu wave sau muốn sửa
một cái tên, cái duy nhất có căn cứ là `divide_segment` (`a`/`b` đối xứng cho
một phép có thứ tự) — và đó là một quyết định riêng, với chi phí tương thích
của chính nó.
