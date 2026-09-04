# CENTER_RADIUS_CURVED_CONSTRUCTION_FOUNDATION

> 2026-09-04. **`APPLICATION_LLM_CALLS = 0`** · `V3_EXECUTED = NO` ·
> pool V3 và `pool_hash` không đụng tới.

## ROOT_CAUSE

Khối cong khai bằng **ba điểm neo hữu tỉ**. Cách ấy đúng và phải giữ — nó là
thứ giữ mọi toạ độ trong ℚ³ kể cả khi bán kính vô tỉ. Nhưng nó **không diễn đạt
nổi** lớp bài phổ biến nhất về mặt cầu:

> *Cho mặt cầu tâm O bán kính 13.*

Tâm có. Bán kính có. Điểm trên mặt thì **không**, và không cách nào dựng ra nó.

## BEFORE_REPRODUCTION

Đo trên artifact thật, ca `ball_2`:

| lượt | `lop_loi` | lỗi |
|---|---|---|
| `curved-acceptance-v1` / sau_sua · cuoi | `grounding_khong_sua` | `[UNANCHORED_DERIVED_ASSUMPTION] P_rim_sphere: không có trong đề bài` |
| `curved-acceptance-v2` / one_shot · cuoi | `grounding_khong_sua` | `[UNANCHORED_DERIVED_ASSUMPTION] P_on_sphere: không có trong đề bài` |

Mô hình bịa một điểm vành (`P_rim_sphere`, `P_on_sphere`), grounding từ chối, và
**từ chối đúng**. Không phải mô hình kém — nó đang cố diễn đạt một thứ từ vựng
không có.

## SIGNATURE_GRAPH_PROOF

Dẫn từ **chữ ký runtime**, không từ danh sách chép tay. Mọi phép sinh ra một
`point3` và thứ nó ăn:

```
divide_segment       ← point3, point3     intersect_line_line  ← line3, line3
intersect_line_plane ← line3, plane3      midpoint             ← point3, point3
project_onto         ← point3, plane3|line3   translate        ← point3, vector3
```

```
Phép sinh ĐIỂM nhận một VÔ HƯỚNG làm độ dài:  KHÔNG CÓ
INPUTS = {one point3, one grounded scalar radius}
CURRENT_VALID_PATH_TO_BALL = NONE
```

`divide_segment.ratio` là **tỉ lệ trên một đoạn đã có**, không phải độ dài tuyệt
đối — nó vẫn cần điểm mút thứ hai. Đây là khoảng trống **GIÁ TRỊ**, không phải
kiểu: `construct_curved_solid` nhận ba `point3` nên bao đóng KIỂU vẫn "tới" được
`curved_solid`; thứ không tới được là một điểm **cách tâm đúng r**.

### Và một chặn cứng hơn — TOÁN HỌC

Ngay cả khi engine tự dựng điểm vành, nó phải tìm `v ∈ ℚ³` với `v·v = r²`. Định
lý ba bình phương hữu tỉ: `q > 0` là tổng ba bình phương hữu tỉ **⟺** `q` không
có dạng `4^a(8b+7)`. Đo bằng máy:

| `r²` | có điểm vành hữu tỉ? |
|---|---|
| 169 · 25/4 · 3 | có |
| **7 · 15 · 7/4 · 28** | **KHÔNG** |

Mặt cầu bán kính `√7` **không có một điểm vành hữu tỉ nào**. Bịt khoảng trống
bằng một điểm phụ là bịt bằng một thứ không tồn tại.

## DESIGN_CANDIDATES

| | MATH | R0 | SỐ | SSOT | ERGO | BC | TRACE | SCENE | REUSE | SCHEMA |
|---|---|---|---|---|---|---|---|---|---|---|
| **A** `construct_curved_solid` + tham số tâm/bán kính | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 1 ô |
| B primitive điểm từ (điểm, hướng, độ dài) | ❌ | ✅ | ❌ | ✅ | ○ | ✅ | ✅ | ✅ | ○ | 1 phép |
| C engine tự sinh witness point | ❌ | ○ | ❌ | ❌ | ✅ | ✅ | ○ | ✅ | ○ | 0 |
| **D** representation phân biệt theo `curved_kind` | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | 0 |

**B loại — MATHEMATICAL_COMPLETENESS.** Điểm cách `O` đúng `r` theo hướng `d` là
`O + (r/|d|)·d`; `r/|d|` nói chung vô tỉ, nên toạ độ rời ℚ³. Cùng vách đá đã
loại `(trục, bán kính)` từ Phase 2.

**C loại — MATHEMATICAL_COMPLETENESS.** `r² = 7` không có điểm vành hữu tỉ; engine
sẽ phải từ chối một mặt cầu hoàn toàn hợp lệ. Nó cũng phá SINGLE_SOURCE_OF_TRUTH:
bán kính thật nằm ở dữ kiện đề, còn hình lại mang một điểm engine bịa.

**A và D không phải hai lựa chọn** — chúng là hai đầu của cùng một thay đổi: A là
bề mặt IR, D là biểu diễn kernel. Triển khai cả hai, giữ **một**
`construct_curved_solid` diễn đạt rõ hai parameterization.

Chín điều kiện §4: **9/9 đạt** (xem TEST_RESULTS).

## SELECTED_REPRESENTATION

```python
CurvedSolid(kind, anchor, apex_or_top, rim_point=None, radius_sq_khai=None)
```

Đúng **một** trong `rim_point` / `radius_sq_khai`, cưỡng chế ở
`__post_init__`. `radius_sq` là `@property` — **một cửa duy nhất**, nên hai cách
khai không đẻ ra hai đường tính và không tầng nào mọc `if rim_point else`.

Kernel vốn chỉ đọc `anchor`, `radius_sq`, `truc`, `height_sq` — **chưa từng** đọc
`rim_point` trực tiếp. Nên `intersect_plane_curved`, thể tích, diện tích mặt cong
đều chạy nguyên vẹn, không sửa một dòng.

## AUTHORITY_OWNER

| câu hỏi | chủ sở hữu | đổi? |
|---|---|---|
| loại khối cong cần neo nào, đo bằng công thức nào | `curved.KHOI_CONG` | **+1 cột** `khai_bang_ban_kinh` |
| ô toán hạng của câu lệnh | `ir_static_check._TOAN_HANG_LENH` | **+1 ô** `radius` |
| luật hợp lệ của spec | `contract.ConstructCurvedSolidStmt` | +1 trường, +1 validator |
| `r → r²` | `curved.binh_phuong_ban_kinh` | **mới** |

Loại nào nhận cách khai bằng bán kính là **một cột của bảng**, không phải phép so
`kind == "ball"` ở tầng trên. `test_04c` cấm mọi tầng ngoài `curved.py` mọc nhánh
theo tên hình — và bản đầu của wave này **đã vi phạm**, test bắt được, đã sửa
bằng cách hỏi bảng.

Trụ/nón để `False` là quyết định **PHẠM VI**, không phải bất khả toán học.

## EXACT_NUMBER_CONTRACT

Miền số là `he·π^mu·√can`; `r² = he²·π^(2mu)·can` hữu tỉ **⟺ `mu = 0`**.

```
13    → 169     ✅        √3    → 3       ✅   (vô tỉ mà bình phương hữu tỉ)
5/2   → 25/4    ✅        2π    → TỪ CHỐI  CURVED_RADIUS_OUTSIDE_DOMAIN
0, −3 → TỪ CHỐI  CURVED_RADIUS_OUTSIDE_DOMAIN
```

**Dấu kiểm TRƯỚC khi bình phương.** Bản đầu kiểm `q <= 0` sau khi bình phương và
`−3` lọt thành `9` — test bắt, đã sửa. Bình phương xoá mất dấu, và một bán kính
âm đi qua im lặng là đúng lớp lỗi miền số này sinh ra để chặn.

Ba lượt end-to-end:

| r | R | V |
|---|---|---|
| 13 | `13` | `8788π/3` |
| 5/2 | `5/2` | `125π/6` |
| √3 | `√3` | `4π√3` |

## R0_PROVENANCE

`radius` nhận **TÊN một đại lượng**, không nhận một con số — `radius: 13` hỏng ở
lược đồ (`test_C5`). Vô hướng là **ĐỘ LỚN**, không phải **VỊ TRÍ**, nên nó không
mở cửa nào cho toạ độ.

Grounding không nới một dòng nào:

- `source_fact_id` không tồn tại → từ chối (`test_C2`);
- bán kính khai `99` khi đề cho `13` → từ chối (`test_C3`);
- điểm phụ bịa kèm `model_assumption` → **vẫn** `UNANCHORED_DERIVED_ASSUMPTION`
  (`test_C4`) — đúng lỗ cũ của `ball_2`, vẫn đóng.

## MODEL_FACING_DELTA

Một dòng thẻ, sinh từ lược đồ, không sửa prompt:

```
[LỆNH] construct_curved_solid: … rim_point?:tên<point3>[một ĐIỂM trên mặt cầu,
hoặc trên vành đáy] radius?:tên<scalar|float|int>[tên ĐẠI LƯỢNG bán kính, thay
cho điểm trên mặt] label?:nhãn
```

Mô tả chỉ nói **VAI TRÒ**; luật *"đúng một trong hai, và `radius` chỉ cho khối
cầu"* do validator giữ và nói bằng thông điệp lỗi — đúng doctrine của chính thẻ
(*"luật nào mã hoá được thì để validator giữ"*). Cắt được 45 byte nhờ thế.

Trần thẻ: `5400 → 5450` (hình học, 5320 → **5410**) và `5500 → 5600` (đầy đủ,
5436 → **5526**). **Đã phân loại trước khi nới**, theo luật `OPERAND_ROLE_HINTS`
đặt ra: đây là **từ vựng mới thật**, sinh từ lược đồ, không phải văn xuôi.

## TRACE_AND_SCENE_CONTRACT

- một `construct_curved_solid` = **đúng một** bước trace (`test_F1`);
- cảnh chở `anchor` + `radius_sq` dạng **chuỗi phân số chính xác** (`"169"`),
  `rim_point: null`; **không** `vertices`/`faces`/`mesh` (`test_F2`) —
  tessellation vẫn thuộc renderer;
- `depends` của quả cầu = `{tâm, biến bán kính}` ở **cả** `objects` và `events`
  (`test_F3`). `radius` được thêm vào `_NGUON_CUA_PHEP_DUNG`; thiếu nó thì quả
  cầu mất mắt xích bán kính — đúng lỗi wave trước vừa đóng;
- chọn `V` cho bao đóng đầy đủ tới `S`, `O`, `r` (`test_F4`).

## FAULT_INJECTION

| tiêm | kỳ vọng | thực tế |
|---|---|---|
| ① đổi tên ô `radius` → vô hiệu hoá parameterization | positive tests đỏ | **15 đỏ** — A1×3, A2, B, C1–C4, D4, E3, F1–F4 |
| ② grounding bỏ kiểm nguồn cho vô hướng | R0 tests đỏ | **2 đỏ** — `test_C2`, `test_C3` |

Khôi phục ⇒ **27/27 xanh** cả hai lần. Tiêm ① dựng lại đúng lỗi cũ: chương trình
tâm+bán kính không parse được nữa.

## CACHE_DECISION

```
grammar_card       e0790ba831c23718 → 24e550ad1c57a2aa   ĐỔI
synthesis_schema   8e47707d478f92c4 → 82dbff3f62ee26fb   ĐỔI
capability         5b61b9ea76d0c764 → 8cb3d5081bfcb7f7   ĐỔI
semantic_env       e6161b15ccef73ce → e9492e6354e0c813   ĐỔI
prompts            55ac1ca6a6df92ce                       không đổi
analyze_schema     a4d5ed7c65a68007                       không đổi
```

```
MODEL_FACING_CONTRACT_CHANGED = YES     ANALYZE_SCHEMA_CHANGED = NO
SYNTHESIS_SCHEMA_CHANGED      = YES     PROMPT_CHANGED         = NO
GRAMMAR_CARD_CHANGED          = YES     CAPABILITY_HASH_CHANGED= YES
CACHE_VERSION 76 → 77                   HISTORICAL_ARTIFACTS_CHANGED = NO
```

Bump loại **65/70/73/74** (bề mặt mô hình đổi), khác 75/76 (đầu ra đổi, hợp đồng
đứng yên). Đề đã cache sẽ trả lại chương trình sinh bởi **thẻ cũ** — thẻ không có
ô `radius` — nên không bump là đo thẻ mới bằng kết quả thẻ cũ.

Năm cổng đã đồng bộ: `main.py` · `test_api.py` · `CURRENT_STATE.md` ·
`test_evaluation_candidate.py` · `cache_identity.lock.json`.

## TEST_RESULTS

```
tests/geometry/test_center_radius_ball.py      27 pass  (mới)
pytest toàn bộ                               3358 pass, 1 skip, 1 deselect
vitest toàn bộ                                698 pass / 51 file
tsc -b && vite build                          PASS
replay_demo_cases                             5/5 · REDUCED_CHAIN 1/1
audit_demo_crash_surface                      6/6 biên, 0 ném ra ngoài
certify_acceptance_runner                     PASS, 0 lượt gọi
```

Chín điều kiện §4:

| # | điều kiện | bằng chứng |
|---|---|---|
| 1 | mặt cầu xác định duy nhất bởi tâm + bán kính | `CurvedSolid.radius_sq` một cửa |
| 2 | bán kính truy về source fact | `test_C1`–`C3` |
| 3 | kernel lưu MỘT representation chính xác | `radius_sq_khai: Fraction` |
| 4 | renderer nhận dữ liệu dẫn từ kernel | `test_F2` |
| 5 | chương trình anchor/rim cũ vẫn chạy | `test_D1`, `test_D4` (42 chương trình) |
| 6 | trụ/nón giữ nguyên nghĩa | `test_D2` |
| 7 | `PROBLEM_FAMILY_SPECIAL_CASES = 0` | `test_A3` (AST) |
| 8 | `CURVED_PROBLEM_TEMPLATES = 0` | `test_A4` |
| 9 | R0 vẫn chặn toạ độ phụ | `test_C4`, `test_C5` |

## LIMITATIONS

- `radius` **chỉ** cho khối cầu — quyết định phạm vi, không phải bất khả toán học.
- Bán kính phải là **vô hướng đã có kiểu tĩnh** (`scalar`/`float`/`int`); một
  `assign r = arith(d, "/", 2)` cho kiểu tĩnh `unknown` và **bị từ chối**. Lớp
  bài *"đường kính 26"* vì thế chưa đi được — nợ riêng, chưa mở.
- Bán kính chứa π bị từ chối bằng mã có cấu trúc, không xấp xỉ.
- `area`/`lateral_area` vẫn **tính được nhưng không hỏi được** (ngoài
  `OBLIGATION_KINDS`) — không thuộc wave này.

## NEXT_ACTION

Re-seal candidate hiện tại rồi dùng acceptance mới đo **AI_DISCOVERABILITY**: mô
hình có tự tìm ra ô `radius` không. Wave này mở đường; nó **không** đo được mô
hình có đi vào đường ấy.

```
CENTER_RADIUS_BALL_EXPRESSIBLE   = YES
BALL_2_SYSTEM_EXPRESSIVENESS_GAP = CLOSED
AI_DISCOVERABILITY               = NOT_MEASURED
BALL_PRODUCT_ENABLED             = NO
APPLICATION_LLM_CALLS            = 0
V3_EXECUTED                      = NO
```
