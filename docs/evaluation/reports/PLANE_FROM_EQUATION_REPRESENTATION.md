# PLANE_FROM_EQUATION_REPRESENTATION

> 2026-09-07 · `APPLICATION_LLM_CALLS = 0`
>
> ```
> NEW_IR_OPERATIONS = 1 · NEW_MEMORY_TYPES = 0 · NEW_PER_PROBLEM_MODULES = 0
> PLANE_FROM_EQUATION_FOUNDATION = CLOSED
> ELLIPSE_MODEL_GENERATED_CANDIDATE_REPLAY = PASS (minimal delta)
> ```
>
> Ứng viên attempt 1 — **do mô hình tự viết ở một lượt trước**, không ai gợi ý
> tên phép — nay qua schema và qua `ir_static`. Với một delta **hai trường
> không chạm câu lệnh mặt phẳng**, nó đi trọn đường tới `served` với `16π√5`.

## 1. Đo lại §2 từ raw artifact, trước khi sửa

Đọc `ung_vien_tho[i].raw` — chuỗi mô hình trả về, chưa qua chuẩn hoá nào.

| attempt | byte | statements | tầng bác | lý do |
|---|---:|---|---|---|
| 0 | 1935 | `construct_curved_solid` · 2×`assign` | `ir_static` | `IR_USE_BEFORE_CONSTRUCTION: alpha_plane` |
| 1 | 2125 | **`construct_plane_from_equation`** · … | **schema** | `Input tag … does not match any of the expected tags` |
| 2 | 2764 | `construct_plane` · … | `grounding` | `UNANCHORED_DERIVED_ASSUMPTION` |

**Attempt 1 đúng những trường nào** — đọc thẳng raw:

```json
{"kind": "construct_plane_from_equation", "target_var": "alpha_plane",
 "a": 2, "b": 0, "c": -1, "d": 10, "label": "Mặt phẳng alpha"}
```

Đúng **tên phép**, đúng **bốn hệ số**, đúng **chữ ký**, đúng **kiểu đích**
(`alpha_plane` khai `plane3`). Bốn hệ số viết bằng **số nguyên inline**, không
bằng tên biến — chi tiết ấy quyết định thiết kế ô hệ số ở §5.

Kênh xuất xứ mô hình dùng: `source_fact_id: "mat_phang_alpha"` **trên khai
báo**, không trên câu lệnh — cả ba attempt đều vậy.

## 2. Khoảng trống, tái hiện tất định

```
"construct_plane_from_equation" in _KIEU_DUNG       = False
"construct_plane_from_equation" in _TOAN_HANG_LENH  = False
"construct_plane_from_equation" in _CHU_KY          = False
[k for k in _KIEU_DUNG|_CHU_KY if "equation" in k]  = []
```

| Câu hỏi | Thẩm quyền | Consumer |
|---|---|---|
| Operation sinh kiểu gì | `ir_static_check._KIEU_DUNG` | schema · static · thẻ · `_producers` |
| Hệ số nhận kiểu gì | `contract.HeSoPhuongTrinh` | lược đồ · `grammar_card._kieu` |
| Ai dựng `Plane3` | `geometry.exact.Plane3.from_equation` | `geometry_exec` → interpreter |
| Ai xác minh hệ số đúng đề | `plane_equation` → `SourceInvariant` | `check_source_invariants` |
| Ai tạo trace | interpreter | Scene3D |

Chín consumer đã cập nhật: `contract` · `ir_static_check` · `geometry_exec` ·
`interpreter` · `validator` · `simulation_state` · `display_names` ·
`grammar_card` (dẫn xuất) · `postconditions`.

## 3. Phép dựng — kernel giữ biểu diễn

`Plane3.from_equation(a,b,c,d)` đặt **cạnh `Plane3.through`**, không ở tầng IR:
đây là phép dựng mặt phẳng thứ hai và nó phải sinh ra **cùng một biểu diễn**
`(point, normal)`. Để tầng IR tự chọn điểm neo là dựng thẩm quyền thứ hai về
*"mặt phẳng là gì"*.

```
n = (a, b, c)
a ≠ 0        → P = (−d/a, 0, 0)
a = 0, b ≠ 0 → P = (0, −d/b, 0)
a = b = 0    → P = (0, 0, −d/c)
```

Trục đầu tiên có hệ số khác 0 nhận toàn bộ `−d`. Luôn hữu tỉ ⇒ **toạ độ ở lại
ℚ³**, không phép chia nào cho một căn. Không chuẩn hoá độ dài (rời ℚ) và không
chuẩn hoá dấu (một quy ước không tầng nào cần).

`(a,b,c) = (0,0,0)` ⇒ `PLANE_EQUATION_DEGENERATE`, **hai tầng**: lược đồ (lỗi
đi ngược về mô hình qua vòng sửa) và kernel (tiền điều kiện của một hàm công
khai phải do chính nó giữ). Phép tiêm ②đo được là hai tầng chứ không nhân đôi.

**Hệ số là SỐ, không phải TÊN** — khác `construct_curved_solid.radius` có chủ
đích. Bán kính là một ĐỘ LỚN nên grounding đòi nó truy về đề; bốn hệ số là
**nguyên văn con số trong câu đề**, và cùng nhau chúng xác định một VỊ TRÍ.
Miền số: `int` hoặc chuỗi phân số — cùng miền `divide_segment.ratio`, và `int`
có mặt vì **đó là thứ mô hình thật sự viết**.

## 4. Ai gác bốn hệ số — và vì sao không thể là grounding

`check_grounding` chỉ soi `memory_declarations`. Bốn hệ số nằm trong **câu
lệnh**, nên chúng đi qua nó mà không bị hỏi câu nào.

Nên phép gác là `SourceInvariant kind="plane_equation"`: **server tự đọc phương
trình từ câu văn của đề**, rồi so **tỉ lệ chính xác** với mặt phẳng có thật
trong trạng thái cuối. Nguyên văn lập luận `check_source_invariants` đã dựng
cho `segment_length` — *"cổng chạy trên dữ liệu server tự phát, nên không có
đường nào để một chương trình tránh bị kiểm bằng cách im lặng."*

⚠️ **Ca đắt nhất của cả wave, và nó là lý do tầng này không bỏ được.**
`2x − z + 11 = 0` **song song** với mặt phẳng đề cho, nên thiết diện elip
**bằng hệt**:

```
sai d = 11 → đáp số 16π√5  ✅ ĐÚNG
           → servable      ❌ postcondition_violated, violated = 1
```

Mọi cổng hỏi *đáp số* đều xanh. Hình thì sai chỗ. Phép tiêm ③ đo thẳng cái giá:
gỡ bất biến ⇒ ca ấy `served` với đáp số đúng, và **không cổng nào kêu**.

Bất biến hỏi **trên HÌNH, không trên câu lệnh**, nên nó phủ luôn đường dựng ba
điểm cũ: gold ba điểm cũng `checked=1 passed=1`, và ba điểm dựng sai mặt phẳng
thì `violated=1`. Không có cửa sau.

### Bộ đọc — hai lỗi THẬT, bắt được trước khi nhập

Bản đầu chỉ nở theo tập ký tự quanh dấu `=`, không hỏi **biên từ**:

| đề | bản đầu đọc ra | đúng ra phải |
|---|---|---|
| *"Diện tích mặt phẳng **đáy** = 12"* | mặt phẳng `y − 12 = 0` | im lặng |
| *"(α): 2x + **m**y − z + 10 = 0"* | mặt phẳng `y − z + 10 = 0` | **chặn** |

Ca thứ hai nặng hơn hẳn: không phải một cảnh báo thừa mà **một mặt phẳng SAI
được đem đi đối chiếu** — chữ `y` bị cắt khỏi tham số `my`.

Bản sửa: biên bẩn (chữ cái dính liền) ⇒ **nuốt trọn cụm chữ cái** để chuỗi mang
theo thứ làm nó không đọc nổi, rồi phân xử bằng **biến độc lập** (`x`/`y`/`z`
không dính chữ cái hai bên):

```
có biến độc lập + không đọc được  → plane_equation_unresolved  (CHẶN)
không có biến độc lập             → im lặng
```

Chặn oan một lớp đề còn tệ hơn bỏ sót một phép kiểm, nên *"diện tích mặt phẳng
đáy"* phải im lặng chứ không chặn.

Ngưỡng còn hẹp ở hai chỗ nữa: chỉ tuyến tính Cartesian theo `x,y,z` hệ số hữu
tỉ, và phải có **cụm chỉ mặt phẳng** trong 48 ký tự trước dấu `=`.

## 5. Replay §11 — nguyên byte, 0 lượt gọi

`backend/scripts/replay_plane_from_equation.py` · artifact
`docs/evaluation/geometry/plane-from-equation/REPLAY.json`.

Hợp đồng dựng lại từ **raw `analyze` của lượt chạy thật** qua
`build_request_contract`, không dùng gold: `fact_id` của gold khác, và mọi
`source_fact_id` của mô hình sẽ trượt oan.

```
RAW_ATTEMPT_1_SCHEMA_VALID   = YES     (trước: schema TỪ CHỐI)
RAW_ATTEMPT_1_STATIC_VALID   = PASS    ← khẳng định trung tâm của wave
RAW_ATTEMPT_1_GROUNDING_PASS = NO      ← nhưng KHÔNG vì mặt phẳng
RAW_ATTEMPT_1_RUNTIME        = NOT_REACHED
RAW_ATTEMPT_1_EXACT_AREA     = NOT_REACHED
RAW_ATTEMPT_1_POSTCONDITIONS = NOT_REACHED
RAW_ATTEMPT_1_TRACE          = NOT_REACHED
RAW_ATTEMPT_1_SCENE3D        = NOT_REACHED
RAW_ATTEMPT_1_SERVABLE       = NO
```

⚠️ **`ir_static` hỏi RIÊNG, không đọc qua `verify_and_compile`** — hàm ấy chạy
grounding trước, nên một ứng viên chết ở grounding sẽ để `STATIC_VALID =
NOT_REACHED`. Mà đó đúng ô người đọc tới để xem, vì tầng phép mới gỡ tắc **chính
là `ir_static`**. Báo `NOT_REACHED` cho thứ đo được là giấu kết quả sau một thứ
tự gọi.

**Chỗ còn tắc là một lỗ KHÁC, có sẵn, không liên quan wave.** Grounding bác
`P_rim` — điểm vành mô hình bịa cho hình trụ, khai bằng `model_assumption`.
Đúng lớp lỗi `ball_2` mà `ConstructCurvedSolidStmt` đã ghi và đã có đường đi
đúng: ô `radius` nhận tên một vô hướng. Và mô hình **đã khai sẵn** `R` với
`source_fact_id: "ban_kinh_day"` — rồi vẫn bịa thêm một điểm vành.

### Minimal delta

```
MINIMAL_DELTA_SIZE = 2 trường · 2125 → 1964 byte (−161)
  ① bỏ khai báo `P_rim`
  ② `rim_point: "P_rim"` → `radius: "R"`
CAU_LENH_MAT_PHANG_KHONG_DOI = True   ← không một byte nào của phép mới bị sửa
```

```
SCHEMA PASS · STATIC PASS · GROUNDING PASS
SOURCE_INVARIANT checked=1 passed=1 violated=0
RUNTIME PASS · POSTCONDITIONS PASS · TRACE PASS · SCENE3D PASS
SERVABLE = True · stage = served · EXACT_AREA = 16π√5  ✅
```

Attempt 0 và attempt 2 **giữ nguyên phán quyết** — phép mới không nới lỏng gì
cho chúng.

## 6. Trace và Scene3D (§10)

```json
{"step_index": 1, "action": "CREATE", "object": "alpha_plane", "depends": [],
 "explanation": "Dựng mặt phẳng Mặt phẳng alpha từ phương trình 2x - z + 10 = 0."}
```

Đúng **một** producer, đúng **một** bước, `depends: []` (câu lệnh không đọc vật
nào), một `plane3` trong state, và mặt phẳng vào cảnh với
`point: ["-5","0","0"]` · `normal: ["2","0","-1"]` — **chuỗi phân số, không
`float` nào xuống renderer**.

⚠️ **Điểm neo canonical KHÔNG lọt vào lời kể** (`test_29`). Nó là chi tiết thực
thi; gọi tên nó cho học sinh là dạy một điểm hình học đề không có.

`action` dùng lại `construct_plane`: hai câu lệnh sinh cùng một loại vật, và
phát một action thứ hai bắt mọi tầng hiển thị mọc thêm một nhánh rồi trôi khỏi
nhau. Cách dựng nằm ở `details`, nơi nó thuộc về.

## 7. Thẻ văn phạm — dẫn xuất, và hẹp dần hai lần

```
[LỆNH] construct_plane_from_equation: target_var:tên a:số hữu tỉ THÔ[hệ số của x]
  b:số hữu tỉ THÔ[hệ số của y] c:số hữu tỉ THÔ[hệ số của z]
  d:số hữu tỉ THÔ[hạng tử tự do của ax+by+cz+d=0] label?:nhãn
```

Thẻ hình học **6042 → 6302 B (+260)**, toàn bộ trên một dòng. Hai khoản:

- **+182** từ vựng mới thật, sinh từ lược đồ.
- **+78** vai trò bốn ô số. `a`/`b`/`c`/`d` không tự nói được chúng là hệ số
  của gì — đúng lập luận `_vai_tro` đã dùng cho quy ước tên `a`/`b`.

⚠️ **Luật in vai trò hẹp dần HAI lần, và hai con số nói vì sao.** Bản đầu in cho
mọi ô: **+1791 B** (`target_var` và mọi ô `str` cũng mang mô tả). Bản hai in cho
cả ô *"giá trị thô"*: +132 B, nhưng 27 trong đó là
`initial_value?:…[Giá trị khởi tạo ban đầu]` — **nói lại đúng thứ tên ô đã
nói**, trên dòng `memory_declarations` mà mọi chương trình đều đọc. Bản chốt chỉ
in cho ô **số trần**: +78 B, và `memory_declarations` giữ nguyên từng byte.

Nhãn kiểu cũng rút: `giá trị thô, KHÔNG phải biểu thức` (34 B) → `số hữu tỉ
THÔ` (14 B), khớp theo **kiểu** (`int | str`) chứ không theo tên trường. Chữ
THÔ — phần đã trả giá bằng quota — được giữ.

Card C nguyên vẹn: hai affordance đã đo (`t = m/(m+n)`, dòng `Xuất xứ:`) còn
nguyên văn.

## 8. Tiêm lỗi (§12)

| # | tiêm | quan sát được |
|---|---|---|
| ① | `tuong_duong` chỉ so `(a,b,c)` | ca `d = 11` **lọt** ⇒ `test_11` có răng |
| ② | gỡ kiểm `(a,b,c)≠0` ở lược đồ | kernel **vẫn** ném `PLANE_EQUATION_DEGENERATE` — hàng phòng thủ thứ hai có thật |
| ③ | không phát bất biến nguồn | hình SAI được **`served`** kèm đáp số ĐÚNG |
| ④ | điểm neo dồn `−d` vào sai trục | `signed_eval(0,0,10) ≠ 0` — mặt phẳng lệch |
| ⑤ | gỡ lệnh khỏi `_KIEU_DUNG` | `_producers` mất `alpha` ⇒ cổng phủ kêu |

## 9. Cổng đã chạy

| cổng | kết quả |
|---|---|
| test riêng của wave | **67 pass**, 5 phép tiêm |
| `pytest -q` (cây sạch) | **4329 pass**, 1 skip, 1 deselect, **0 đỏ** |
| `vitest run` | **698 pass / 51 file** |
| `npm run build` | PASS |
| `replay_demo_cases.py` | **5/5**, `REDUCED_CHAIN 1/1` |
| `audit_demo_crash_surface.py` | **6/6 biên**, ném **0** |
| `certify_acceptance_runner.py` | PASS, 0 lượt gọi |
| `lock_cache_identity.py --verify` | exit 0 @ v89 |
| `freeze_evaluation_candidate --verify` | exit 0 (91 file, `422a9e7b…`) |
| `git diff --check` | sạch |

## 10. Báo cuối

```
ROOT_CAUSE = IR khong co phep dung mat phang tu PHUONG TRINH; ba loi bieu dat,
             mot loi chay duoc, va loi ay doi gan `source_fact_id` vao toa do
             de KHONG HE NEU ⇒ he buoc mo hinh khai xuat xu khong trung thuc
NEW_MEMORY_TYPES              = 0
NEW_IR_OPERATIONS             = 1
NEW_PER_PROBLEM_MODULES       = 0
PLANE_FROM_EQUATION_EXPRESSIBLE = YES
EXACT_COEFFICIENTS            = YES  (int | chuoi phan so; toa do o lai ℚ³)
PROPORTIONAL_EQUATION_EQUIVALENCE = PASS (dinh thuc con 2×2, khong dung sai)
SOURCE_EQUATION_VERIFIED      = PASS (SourceInvariant `plane_equation`,
                                server doc tu de; phu CA loi dung ba diem)
GROUNDING_STRENGTH_PRESERVED  = YES  (duong ba diem giu nguyen phan quyet;
                                attempt 0 va 2 khong doi)
TRACE_PASS                    = PASS (1 producer · 1 buoc · depends [] ·
                                loi ke noi phuong trinh, KHONG noi diem neo)
SCENE3D_PASS                  = PASS (plane3 · render surface · so huu ti)

RAW_MODEL_ATTEMPT_1_REPLAY    = SCHEMA PASS · STATIC PASS · SERVABLE NO
                                (chan boi `P_rim`, MOT LO KHAC co san)
MINIMAL_DELTA_SIZE            = 2 truong · 2125 → 1964 byte
                                (cau lenh mat phang KHONG doi mot byte)
ELLIPSE_EXACT_AREA            = 16π√5
ELLIPSE_SERVABLE_REPLAY       = PASS (minimal delta)
MODEL_GENERATED_OPERATION_EVIDENCE = attempt 1 tu dat DUNG ten va DUNG chu ky
                                `construct_plane_from_equation(a,b,c,d)`,
                                khong ai goi y — raw sha256 da8e60af…

APPLICATION_LLM_CALLS         = 0
CACHE_VERSION_BEFORE/AFTER    = 88 → 89
CANDIDATE_HASH_BEFORE/AFTER   = f48e768b… → 422a9e7b…  (90 → 91 file)
MODEL_FACING_HASHES_CHANGED   = BA: grammar_card 4b435fbb→285292fe ·
                                synthesis_schema d69661ce→6ccef323 ·
                                capability e0214b77→4b1e2f80.
                                prompts va analyze_schema KHONG doi mot byte
PRODUCT_CAPABILITY_CHANGED    = NO  (curved_oblique_section giu foundation_only,
                                PRODUCT_PROMOTION_ELIGIBLE = NO)
TEST_RESULTS = wave 67 · pytest 4329 pass 0 do · vitest 698/51 · build PASS
               replay 5/5 · crash 6/6 nem 0 · certify PASS
               cache identity exit 0 · freeze --verify exit 0 · diff sach
COMMITS      = 3
WORKING_TREE = sach
RECOMMENDED_NEXT_ACTION = OBLIQUE_ELLIPSE_FRESH_E2E_RERUN
```

## 11. Giới hạn bằng chứng

- **Wave này KHÔNG đo hành vi mô hình.** `APPLICATION_LLM_CALLS = 0`. Nó chứng
  minh **hệ** biểu đạt và kiểm được; câu *"mô hình có tự viết lại được không"*
  chưa ai hỏi. Replay nói về một ứng viên mô hình **đã** viết, không nói về lượt
  sinh kế tiếp.
- **`ELLIPSE_SERVABLE_REPLAY = PASS` là của MINIMAL DELTA, không phải raw.** Raw
  attempt 1 vẫn `NO`. Trích số này mà bỏ chữ *"minimal delta"* là nói quá.
- **Delta hai trường ấy sửa một lỗ KHÁC** — `rim_point` vs `radius`. Nó có sẵn
  từ trước wave, và wave này không đụng tới.
- `n = 1` đề, `n = 3` ứng viên. `DEVELOPMENT_SIGNAL`.
- Bộ đọc phương trình hẹp có chủ đích: tuyến tính Cartesian `x,y,z`, hệ số hữu
  tỉ, và phải có cụm chỉ mặt phẳng đứng trước. Một đề nêu mặt phẳng bằng cách
  hệ không đọc ra thì **không bất biến nào kiểm** — giới hạn của tầng đọc đề,
  không phải một cửa mở trong cổng.

**Việc kế tiếp: `OBLIQUE_ELLIPSE_FRESH_E2E_RERUN`.** Đề · oracle · gold ·
registration đã sẵn; lượt chạy chỉ để xác nhận đường sản phẩm với lược đồ mới,
trần **5 logical calls**. Nó cũng đo miễn phí một câu thứ hai đáng hỏi:

⚠️ **`CURVED_RIM_POINT_AFFORDANCE`** — mô hình khai `R` với `source_fact_id`
rồi **vẫn** bịa `P_rim`. Ô `radius` đã tồn tại từ 2026-09-04 và giải đúng lớp
bài này. `n = 1`, phân loại **`HYPOTHESIS`**: chưa đủ để nói thẻ giới thiệu ô
`radius` chưa đủ rõ. Lượt rerun cho quan sát thứ hai mà không tốn thêm lượt gọi
nào.
