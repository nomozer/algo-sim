# OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION

> 2026-09-07. **`APPLICATION_LLM_CALLS = 0` — không tiêu một lượt quota nào.**
>
> ```
> OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION = BLOCKED_BEFORE_PROVIDER
> GOLD_PREFLIGHT            = PASS
> SYSTEM_EXPRESSIBLE        = YES
> MODEL_DISCOVERABILITY     = NOT_MEASURED  (cổng chặn trước analyze)
> BLOCKER = SCOPE_GATE_MISSING_QUANTITY_OBLIGATION_CLUES  ·  loại: SYSTEM_GAP
> ```
>
> Phép đo **dừng trước lượt gọi provider**, đúng §5 của brief. Lý do không phải
> gold preflight hỏng — nó **PASS**. Lý do là một cổng tất định đứng **trước**
> `analyze` từ chối đề, nên câu hỏi của wave (*mô hình có tự tìm ra phép elip
> không*) chưa có cách nào hỏi.

## 1. Trạng thái đầu — khớp bàn giao

```
HEAD          = 75cf3ec       WORKING_TREE = sạch
CACHE_VERSION = 87            CANDIDATE = e8c6150f… (--verify exit 0, 90 file)
PRODUCT_VARIANT = C + từ vựng elip   (58ae082c…, 6042 B)
CURVED_OBLIQUE_SECTION_CAPABILITY = foundation_only
```

Sáu băm model-facing @ v87: `prompts 55ac1ca6…` · `grammar_card 4b435fbb…` ·
`synthesis_schema d69661ce…` · `analyze_schema 515001b5…` ·
`capability e0214b77…` · `semantic_environment 9d0374a7…`.

**Năm điều kiện của thẻ, kiểm bằng máy — đủ cả năm:** `ellipse3` trong tập kiểu
hợp lệ ✓ · `intersect_plane_curved_ellipse` có mặt ✓ · `area` nhận `ellipse3` ✓ ·
affordance `ratio` của Card C còn nguyên ✓ · affordance `Xuất xứ:` còn nguyên ✓.

## 2. Đề đo và oracle

> Trong hệ trục Oxyz, cho hình trụ tròn xoay có tâm đáy dưới O(0,0,0), tâm đáy
> trên O'(0,0,20) và bán kính đáy bằng 4. Mặt phẳng (α): 2x − z + 10 = 0 cắt
> hình trụ theo một elip (E) nằm hoàn toàn giữa hai đáy. Tính diện tích elip (E).

```
center = (0, 0, 10) · b = 4 · a = 4√5 · S = 16√5π · z ∈ [2, 18]
```

Đề **chưa thuộc corpus hay artifact nào** (khoá bằng `test_D1`). Nó khác hai đề
elip/nón trước ở một điểm có chủ đích: cho **toạ độ tường minh** và cho mặt
phẳng bằng **phương trình** — IR không có `plane_from_equation`, nên đường duy
nhất là ba điểm thoả phương trình + `construct_plane`.

## 3. Gold preflight — 20 pass, `PASS`

`GOLD_PREFLIGHT = PASS`. Gold đi trọn: validator · `ir_static` · grounding ·
phủ · runtime · hậu điều kiện · **`16π√5` chính xác** · trace · Scene3D ·
`served`.

**Hai oracle độc lập** cho cùng một số:

| # | lối | kết quả |
|---|---|---|
| ① | công thức bán trục: `b² = 16`, `a² = 16·5·400/400 = 80`, `S = π√1280` | **`16π√5`** |
| ② | **thế thẳng**: bốn đầu mút trục vào `x²+y²=16` **và** `2x−z+10=0` | **`16π√5`** |

Oracle ② không dùng lại `a²`/`b²` của kernel: bốn đầu mút ra **hữu tỉ** —
`(4,0,18)`, `(−4,0,2)`, `(0,±4,10)` — cả bốn thoả **đồng thời** hai phương
trình, và biên dọc khớp `z ∈ [2, 18]`.

Bốn vật đúng producer và dependency; bao đóng từ `dien_tich_E` truy về đủ chín
vật.

### 3a. Bảy phản ví dụ

| phản ví dụ | kết quả |
|---|---|
| `construct_section` cho khối cong | `ir_static` — *"cần solid, có curved_solid"* |
| khai kết quả là `section` | **KHÔNG bị chặn** — đáp số vẫn `16π√5` |
| khai kết quả là `circle3` | **KHÔNG bị chặn** — đáp số vẫn `16π√5` |
| mặt phẳng ∥ trục | `execution` — `CURVED_ELLIPSE_OUTSIDE_V1_CLOSURE` |
| elip vượt đáy | `execution` — `CURVED_ELLIPSE_CROSSES_CAP` |
| đo `radius` thay cho `area` | `ir_static` — `IR_OPERAND_TYPE`, *"có ellipse3"* |
| thiếu producer cho elip | `ir_static` — `IR_USE_BEFORE_CONSTRUCTION` |
| **sai hệ số góc** (`1x` thay `2x`) | **KHÔNG cổng nào chặn** — bắt bằng **đáp số**: `16π√2 ≠ 16π√5` |

⚠️ Hai ca không bị chặn, và **cả hai là đúng**:

- **Khai sai kiểu** — kiểu **dựng ra** thắng kiểu **khai** ở mọi tầng. Hành vi
  **có sẵn từ trước**, đã ghi ở `CURVED_MISSING_FAMILY_…§9`. Điều phải đúng và
  đã khoá: lời khai sai **không** làm sai đáp số, cảnh vẫn nhận `ellipse3`.
- **Sai hệ số góc** — mặt phẳng ấy hợp lệ về mọi mặt, chỉ **không phải mặt
  phẳng đề cho**. Không cổng nào bắt được, và không nên bắt. Tuyến phòng thủ
  duy nhất là **phép so đáp số** — nên test giá trị phải tồn tại, và nó tồn tại.

## 4. BLOCKER — `SCOPE_GATE_MISSING_QUANTITY_OBLIGATION_CLUES`

Tìm ra bằng **provider stub**, trước khi tiêu một lượt quota nào.

### 4a. Cơ chế

`co_duong_thuc_thi` là cổng **tất định** đứng trước `analyze`. Hợp đồng của nó,
theo chính docstring: *"hệ có đường biểu diễn nào cho thứ đề này hỏi không"*.
Nó trả lời bằng `nghia_vu_ung_vien(text) & GEOMETRY_CHECKERS`.

Bảng manh mối `_MANH_MOI_NGHIA_VU` **thiếu bốn nghĩa vụ CÓ CHECKER**:

```
area · lateral_area · radius · section_matches
```

Nên với đề chỉ hỏi *"tính diện tích …"*, cổng trả **`False`** trong khi hệ
**có** đủ đường — `BANG_PHEP_DO["area"]`, `check_area`, `OBLIGATION_KINDS`, và
cả kiểu `ellipse3` vừa dựng xong ở wave trước. Đề bị từ chối ở tầng `scope` với
`GATE_NOT_SIMULATION_SUITABLE`.

```
detect_domain      = hinh_hoc          ← ĐÚNG miền
nghia_vu_ung_vien  = frozenset()       ← KHÔNG manh mối nào
co_duong_thuc_thi  = False             ⇒ scope · unsupported · 0 lượt gọi
```

Không phải một cách viết xui — **cả lớp** câu hỏi ấy trượt:

```
"Tính diện tích elip (E)."               → []
"Tính diện tích của elip (E)."           → []
"Tính bán kính đường tròn (c)."          → []
"Tính diện tích xung quanh của hình trụ." → []
```

### 4b. Bằng chứng rằng cổng đang đọc CHỮ, không đọc thứ đề hỏi

Cùng câu hỏi ấy, thêm một cụm **mô tả** không liên quan gì tới đại lượng được
hỏi, và cổng **mở**:

```
co_duong_thuc_thi("Tính diện tích elip (E).")                        = False
co_duong_thuc_thi("Mặt phẳng vuông góc với trục. Tính diện tích …")  = True   ← khớp `perpendicular`
```

### 4c. ⚠️ Wave trước lọt qua cổng NHỜ MAY — đính chính cách đọc

`CURVED_END_TO_END_FRESH_CONFIRMATION` hỏi **`radius`** của một đường tròn. Manh
mối duy nhất khớp đề ấy là **`perpendicular`**, từ cụm *"vuông góc với SO"* nằm
ở phần **mô tả**, không phải phần hỏi:

```
nghia_vu_ung_vien(đề nón) = {"perpendicular"}      ← KHÔNG có `radius`
bỏ hai chữ "vuông góc"     ⇒ co_duong_thuc_thi = False
```

Nghĩa là cổng đã cho **đúng câu trả lời vì một lý do sai**, và điều đó chỉ lộ ra
khi gặp một đề không tình cờ mang chữ nào trong bảng. Kết luận của wave ấy
(`served`, đáp số `4`) **không đổi** — nó đo đúng thứ nó đo. Thứ phải sửa là
cách đọc: *"đề nón qua được cổng"* là một quan sát về **may mắn từ vựng**, không
phải về năng lực của cổng.

`SYSTEM_GAP` — tái hiện tất định, khoá bằng
`tests/geometry/test_scope_gate_quantity_obligation_gap.py` (**12 pass**).

### 4d. Đường sửa, ghi sẵn

Chỗ sửa đúng là **`_MANH_MOI_NGHIA_VU`** — thêm cụm cho bốn nghĩa vụ, **một
bảng, một thẩm quyền**. KHÔNG nới `co_duong_thuc_thi` thành *"cứ hình học thì
cho qua"*: cổng ấy tồn tại để từ chối đề hỏi thứ hệ không dựng được, và bỏ nó là
bỏ một lời từ chối đáng nói. Cũng KHÔNG dựng bảng manh mối thứ hai.
Khoá bằng `test_D1_sua_la_MOT_bang_MOT_tham_quyen`.

Wave này **không sửa**: đụng mã sản phẩm kéo theo nhịp bump/đóng băng lại, và
§11 của brief nói rõ mã sản phẩm giữ nguyên.

## 5. Vì sao lỗ này sống sót qua ba wave

| wave | đường đi | có chạm cổng không |
|---|---|---|
| `RATIO_*`, `PROVENANCE_*`, `MINIMAL_CARD_*` | runner A/B, **hợp đồng cố định** | ❌ |
| `CURVED_MISSING_FAMILY_…` (nền elip) | `verify_and_compile`, hợp đồng dựng tay | ❌ |
| `CURVED_END_TO_END_FRESH_CONFIRMATION` | `run_pipeline` — **có** chạm | ✅ nhưng lọt nhờ `perpendicular` |
| **wave này** | `run_pipeline`, đề **không** mang chữ may mắn nào | ✅ **và bị chặn** |

Bốn wave đi qua mà không thấy, vì ba wave đầu **không đi qua cổng** còn wave thứ
tư đi qua **nhờ một từ trong phần mô tả**.

## 6. Bộ đo — thay đổi, và một khoản tái dùng

**Runner nay chọn được gold module và scorer module theo đăng ký** (`gold_module`,
`scorer_module`), thay vì viết runner thứ hai. Cùng khuôn `corpus_module` đã áp
cho runner A/B. Lý do giữ module cũ nguyên: `PROBLEM_HASH`/`ORACLE_HASH`/
`GOLD_HASH` của nó đã nằm trong artifact **bất biến** của lượt trước.

Bộ chấm của wave (`score_oblique_ellipse_fresh`) là module riêng, không nới hai
bộ chấm mặc định — chúng hỏi những chiều của **bài nón**, và nới chúng để nhận
thêm bài elip là dựng một bộ chấm biết hai bài; bộ thứ ba sẽ nới lần nữa.

`test_runner_curved_end_to_end.py` của wave trước: **21 pass**, không hồi quy.

## 7. Cổng đã chạy

| cổng | kết quả |
|---|---|
| tiền kiểm gold | **20 pass**, 0 lượt gọi |
| tái hiện blocker | **12 pass**, 0 lượt gọi |
| runner stub | **14 pass**, 0 lượt gọi |
| runner wave trước (không hồi quy) | **21 pass** |
| `pytest -q` (cây sạch sau commit) | **4223 pass**, 1 skip, 1 deselect, **0 đỏ** |
| `replay_demo_cases.py` | **5/5**, `REDUCED_CHAIN 1/1` |
| `audit_demo_crash_surface.py` | **6/6 biên**, ném **0** |
| `certify_acceptance_runner.py` | **PASS**, 0 lượt gọi · 2 readiness YES |
| `lock_cache_identity.py --verify` | **exit 0** @ v87 |
| `freeze_evaluation_candidate --verify` | **exit 0**, 90 file, `e8c6150f…` |
| `git diff --check` | sạch |
| frontend | **kế thừa** — hợp đồng Scene3D không đụng |

## 8. Báo cuối

```
OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION = BLOCKED_BEFORE_PROVIDER
GOLD_PREFLIGHT            = PASS   (20 test · 2 oracle doc lap · 7 phan vi du)
SYSTEM_EXPRESSIBLE        = YES
ANALYZE_CONTRACT          = NOT_REACHED   (cong chan TRUOC analyze)
FIRST_ATTEMPT_SERVABLE    = NOT_REACHED
EVENTUAL_SERVABLE         = NOT_REACHED
EXACT_ANSWER              = NOT_REACHED   (gold: 16π√5 PASS)
POSTCONDITIONS_PASS       = NOT_REACHED   (gold: PASS)
TRACE_PASS                = NOT_REACHED   (gold: PASS)
SCENE3D_PASS              = NOT_REACHED   (gold: PASS)
MODEL_DISCOVERABILITY     = NOT_MEASURED
STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED

ANALYZE_CALLS             = 0     INITIAL_SYNTHESIS_CALLS  = 0
REPAIR_CALLS              = 0     LOGICAL_APPLICATION_CALLS = 0
PHYSICAL_API_ATTEMPTS     = 0     TRANSPORT_RETRIES        = 0
CANDIDATE_PROGRAM_ATTEMPTS = 0    TOTAL_TOKENS = 0 / 40 000
APPLICATION_LLM_CALLS     = 0

CACHE_VERSION_BEFORE/AFTER   = 87 → 87   (khong bump: khong doi be mat mo hinh)
CANDIDATE_HASH_BEFORE/AFTER  = e8c6150f… → e8c6150f…  (khong dong bang lai)
MODEL_FACING_HASHES_CHANGED  = KHONG, ca sau
PRODUCT_CAPABILITY_CHANGED   = NO   (curved_oblique_section giu foundation_only)
PRODUCT_PROMOTION_ELIGIBLE   = NO

BLOCKER = SCOPE_GATE_MISSING_QUANTITY_OBLIGATION_CLUES  (SYSTEM_GAP)
  tang    = scope · `co_duong_thuc_thi`, TRUOC analyze
  nguyen  = `_MANH_MOI_NGHIA_VU` thieu 4 nghia vu CO CHECKER:
            area · lateral_area · radius · section_matches
  sua     = them cum manh moi cho bon nghia vu — MOT bang, MOT tham quyen

TEST_RESULTS = pytest 4223 pass · 1 skip · 1 deselect · 0 do
               replay 5/5 · crash 6/6 nem 0 · certify PASS 0 luot goi
               cache identity exit 0 · freeze --verify exit 0 · diff --check sach
COMMITS      = 2        WORKING_TREE = sach
RECOMMENDED_NEXT_ACTION = SCOPE_GATE_QUANTITY_OBLIGATION_CLUE_REPAIR
```

⚠️ **`ELLIPSE_FOUNDATION_SEQUENCE` KHÔNG đóng.** Điều kiện đóng là *eventual
served*, và nó **chưa đạt** — không phải vì mô hình sai, mà vì phép đo chưa chạy
được. `CARD_C_CURVED_ELLIPSE_PATH_CONFIRMED` giữ **`NOT_MEASURED`**.

## 9. Giới hạn bằng chứng

- **Wave này không nói gì về hành vi mô hình.** `MODEL_DISCOVERABILITY =
  NOT_MEASURED`, và 0 lượt gọi nghĩa là **không có dữ liệu nào** theo hướng ấy.
  Nói *"mô hình không làm được bài elip"* là nói sai — chưa ai hỏi nó.
- **Blocker là `SYSTEM_GAP`, không phải `HYPOTHESIS`**: tái hiện tất định, 12
  test, hai bảng thẩm quyền đối chiếu được, không phụ thuộc một lượt sinh nào.
- **Đính chính ở §4c là về CÁCH ĐỌC, không về số liệu.** Mọi con số của
  `CURVED_END_TO_END_FRESH_CONFIRMATION` giữ nguyên.
- Hai hành vi đã ghi, **chưa siết**, và cả hai có sẵn từ trước: kiểu khai của
  vật dựng ra là trang trí; mặt phẳng sai hệ số không có cổng nào bắt.

**Việc kế tiếp: `SCOPE_GATE_QUANTITY_OBLIGATION_CLUE_REPAIR`** — một wave hẹp,
sửa đúng một bảng, kèm phép tiêm chứng minh cổng đỏ được cho cả bốn nghĩa vụ.
Sau đó **chạy lại chính wave này** (registration và gold đã sẵn, đề chưa tiêu
lượt nào) để lấy câu trả lời về `MODEL_DISCOVERABILITY`.

⚠️ Token của Claude Code **không** tính vào token vận hành AlgoSim.
