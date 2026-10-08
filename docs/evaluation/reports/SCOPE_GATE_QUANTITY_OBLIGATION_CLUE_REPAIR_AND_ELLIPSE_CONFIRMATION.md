# SCOPE_GATE_QUANTITY_OBLIGATION_CLUE_REPAIR_AND_ELLIPSE_CONFIRMATION

> 2026-09-07. Hai pha trong cùng phiên.
>
> ```
> Pha A — SỬA CỔNG PHẠM VI            = XONG, đủ cổng
> Pha B — XÁC NHẬN ELIP END-TO-END    = CHƯA `served`
> BLOCKER = PLANE_FROM_EQUATION_REPRESENTATION  ·  SYSTEM_GAP
> ```
>
> Pha A mở đúng thứ nó nhắm: đề đi từ `scope` tới `analyze` rồi tới ba lượt
> sinh. Pha B trả lời được câu hỏi thật, và câu trả lời **không** phải *"mô
> hình không làm được"* — nó chỉ ra một chỗ **hệ không biểu đạt được**.

## 1. Trạng thái đầu

```
HEAD = ceb5ed2   WORKING_TREE = sạch   CACHE_VERSION = 87
CANDIDATE = e8c6150f…   PRODUCT_VARIANT = C + từ vựng elip
CURVED_OBLIQUE_SECTION_CAPABILITY = foundation_only
```

---

# PHA A — SỬA CỔNG PHẠM VI

## 2. Tái hiện trước sửa — 0 lượt gọi

| nghĩa vụ | analyze phát được | có checker | có measure/path | **scope clue trước sửa** |
|---|:---:|:---:|:---:|:---:|
| `area` | ✅ | ✅ | `BANG_PHEP_DO["area"]` | ❌ |
| `lateral_area` | ✅ | ✅ | `BANG_PHEP_DO["lateral_area"]` | ❌ |
| `radius` | ✅ | ✅ | `BANG_PHEP_DO["radius"]` | ❌ |
| `section_matches` | ✅ | ✅ | `cross_section` + `same_section_cycle` | ❌ (mượn `coplanar`) |

```
co_duong_thuc_thi("Tính diện tích elip (E).")             = False   manh_moi = []
co_duong_thuc_thi("Tính diện tích xung quanh hình trụ.")  = False   manh_moi = []
co_duong_thuc_thi("Tính bán kính mặt cầu.")               = False   manh_moi = []
co_duong_thuc_thi("Xác định thiết diện … (MNP).")         = True    manh_moi = ['coplanar']  ← MƯỢN
```

**Ca nón lịch sử**, hai lượt đo:

```
nguyên bản (có "vuông góc")  → True,  manh_moi = ['perpendicular']   ← KHÔNG có `radius`
bỏ cụm "vuông góc với SO"    → False, manh_moi = []
```

Chứng minh xong điều cần chứng minh: câu nguyên bản được định tuyến **nhờ manh
mối quan hệ** ở phần *mô tả*, còn nghĩa vụ `radius` — thứ đề **thật sự hỏi** —
chưa tự mở được tuyến.

## 3. Ba tập thẩm quyền và bất biến

```
ANALYZE_EMITTABLE  = enum `obligations.kind` của `analyze_schema_for("hinh_hoc")`   (12)
CHECKER_BACKED     = GEOMETRY_CHECKERS                                             (12)
SCOPE_ROUTABLE     = khoá của `_MANH_MOI_NGHIA_VU`                                 (8)
```

> **Bất biến khoá:** mọi nghĩa vụ **vừa analyze-emittable vừa checker-backed**
> phải có ít nhất một manh mối scope hiệu lực.

`(EMIT ∩ CHECK) − ROUTE` = `{area, lateral_area, radius, section_matches}` —
đúng bốn, và chiều ngược lại **sạch** (không manh mối nào trỏ nghĩa vụ chết).

## 4. Bản sửa — một bảng, một thẩm quyền

```python
"area":            ("diện tích",)
"lateral_area":    ("diện tích xung quanh", "diện tích mặt bên", "diện tích mặt cong")
"radius":          ("bán kính",)
"section_matches": ("thiết diện",)
```

**`area` và `radius` dùng danh từ TRẦN**, không liệt kê từng lối hỏi. Cổng này
định tuyến **thô** có chủ đích — nó chỉ trả lời *"hệ có đường nào cho thứ đề
này hỏi không"*, còn đúng/sai hình học vẫn thuộc grounding, phủ, kernel và
checker. Bỏ sót một cách viết là **fail-closed một bài giải được**; nhận dư một
ứng viên chỉ tốn một phép giao tập.

**`lateral_area` có định ngữ** nên manh mối cũng có. **Không** thêm *"diện tích
toàn phần"*: `S_tp` của nón có hai căn thức khác nhau và miền số **cố ý** từ
chối tổng ấy.

**`section_matches` dùng chung cụm với `coplanar`**, và đó không phải trùng lặp
thừa — một đề thiết diện có thể cần cả hai nghĩa vụ. Trước bản này nó định
tuyến được là nhờ **mượn** manh mối của `coplanar`.

## 5. Kết quả Pha A

```
"Tính diện tích elip (E)."             → True   ['area']
"Tính diện tích xung quanh hình trụ."  → True   ['area', 'lateral_area']
"Tính bán kính mặt cầu."               → True   ['radius']
đề elip của wave                       → True   ['area', 'radius']
đề nón, bỏ "vuông góc"                 → True   ['radius']   ← tự mở tuyến
```

Tám manh mối cũ định tuyến **y như trước**; ngoài miền vẫn bị chặn; chuỗi rỗng
và *"Cho hình chóp S.ABCD."* vẫn fail-closed.

**43 test** — chính diện · dấu tiếng Việt · biến thể viết hoa · bài cong đầy
đủ · bảo toàn · parity · **bốn phép tiêm riêng**.

⚠️ **Phép tiêm chấm ở mức TẬP, không mức `bool`.** Bỏ `lateral_area` thì
*"diện tích xung quanh…"* **vẫn** mở cổng nhờ `area`, nên một khẳng định ở mức
boolean sẽ xanh và **không chứng minh gì**. Khẳng định đúng là *"nghĩa vụ ấy có
trong tập ứng viên"*.

## 6. Một lỗi PHÂN LOẠI có sẵn, sửa kèm

`NGOAI_NANG_LUC` của `test_wave2_simulatability_va_scorer` liệt kê:

> *"Cho hình nón có bán kính đáy 3 và đường sinh 5. Tính diện tích xung quanh
> của hình nón."*

Nó **chưa bao giờ** ngoài năng lực — hệ tính đúng `S_xq = πrl = 15π`, kiểm
bằng kernel. Nó nằm đó vì **cổng từ chối nó**, và cổng từ chối vì bảng manh
mối thiếu `lateral_area`.

> **Một danh sách *"ngoài năng lực"* dẫn từ hành vi của cổng là một vòng lặp:
> cổng sai thì danh sách sai theo, và cả hai cùng xanh.**

Hai mục còn lại đứng vững vì lý do **thật**: một hỏi *phương trình*, một hỏi
*hình chiếu để vẽ* — không mục nào hỏi một nghĩa vụ có checker.

Cũng đã xoá `test_scope_gate_quantity_obligation_gap.py`: nó khẳng định lỗ
**tồn tại**, và lỗ đã đóng — chính nó đã tự dự báo điều này. Chống tái phát nay
là `test_10_PARITY`, mạnh hơn vì **dẫn xuất** từ registry.

## 7. Cache và identity

**Kiểm cache thực tế, không suy:**

- **Lời từ chối ở `scope` KHÔNG được cache.** `main.py:746` và `:781` chỉ ghi
  khi `envelope["status"] == "ok"`; một refusal mang `"unsupported"`. Không có
  row stale nào để dọn.
- **Sáu băm model-facing KHÔNG đổi một byte** — `prompts` · `grammar_card` ·
  `synthesis_schema` · `analyze_schema` · `capability` · `semantic_environment`.
  Bề mặt mô hình đứng yên; thứ đổi là **đường vào**.

**Quyết định: BUMP 87 → 88.** Theo **luật** (`CLAUDE.md §3`: đổi policy định
tuyến ⇒ bump), đúng tiền lệ **bump 80** — lượt ấy cũng đổi policy định tuyến,
cũng không có row stale, và cũng bump theo luật chứ không để dọn rác. Lý do luật
tồn tại: một đề từng bị từ chối nay được phục vụ, và `CACHE_VERSION` là thứ duy
nhất nói được *"kết quả này sinh dưới luật định tuyến nào"*.

Bốn cổng cùng commit + làm mới `cache_identity.lock.json`. Candidate
`e8c6150f… → f48e768b…`.

## 8. Cổng chuyển pha — đủ sáu

```
ALL_4_OBLIGATIONS_ROUTABLE = YES     OBLIGATION_SCOPE_PARITY   = PASS
ELLIPSE_GOLD_PREFLIGHT     = PASS    CACHE_IDENTITY            = PASS
CANDIDATE_VERIFICATION     = PASS    WORKING_TREE_STATE_FOR_RUN = sạch @ 5f4bb86
```

---

# PHA B — XÁC NHẬN ELIP END-TO-END

## 9. Lượt chạy `oblique-ellipse-after-scope-repair-20260907T050244Z`

Đề, oracle, gold, tiêu chí scoring, token ceiling **giữ nguyên từng byte**.
Artifact lượt bị chặn giữ nguyên làm bằng chứng lịch sử.

```
STAGE = semantic_program   servable = False   envelope = unsupported
ANALYZE 1 · INITIAL_SYNTHESIS 1 · REPAIR 2 · LOGICAL 4/5 · PHYSICAL 4
TRANSPORT_RETRIES 0 · CANDIDATE_PROGRAM_ATTEMPTS 3 · TOKENS 20 725/40 000
```

✅ **Cổng phạm vi đã mở đúng** — đề đi qua `scope`, tới `analyze`, rồi ba lượt
sinh. Pha A làm đúng thứ nó nhắm.

## 10. Analyze — `PASS` toàn bộ

```
SO_FACT = 5 · OBLIGATION_KINDS = ['area'] · CONTAINER = 'E' · WITNESS = 'dien_tich_E'
CO_HAI_TAM ✓ · CO_BAN_KINH_4 ✓ · CO_CHIEU_CAO_HOAC_TRUC ✓
CO_PHUONG_TRINH_MP ✓ · CO_VAT_DUOC_HOI_LA_ELIP ✓
ANALYZE_CONTRACT_CORRECT = PASS
```

Mô hình đọc đề **đúng hoàn toàn**, kể cả phương trình mặt phẳng.

## 11. Ba lượt sinh — **mọi thứ trừ mặt phẳng đều đúng**

| attempt | stage | lỗi chính | diagnostic | thay đổi ở attempt sau |
|---|---|---|---|---|
| 0 | `ir_static` | khai `alpha_plane` từ fact nhưng **không câu lệnh nào dựng nó** | `IR_USE_BEFORE_CONSTRUCTION: 'alpha_plane' — cần plane3, có khai báo nhưng chưa có giá trị` | thêm một câu lệnh dựng mặt phẳng |
| 1 | schema | **tự đặt tên phép còn thiếu**: `construct_plane_from_equation(a,b,c,d)` | `Input tag 'construct_plane_from_equation' … does not match any of the expected tags` | quay về `construct_plane` qua ba điểm |
| 2 | `grounding` | ba điểm `(0,0,10)`, `(1,0,12)`, `(0,1,10)` khai bằng `model_assumption` | `UNANCHORED_DERIVED_ASSUMPTION: P_alpha1 không có trong đề bài…` | — hết ngân sách sửa |

**Sáu chiều còn lại ĐÚNG ở cả ba attempt:**

```
OPERATOR         = intersect_plane_curved_ellipse   ✅ đúng NGAY attempt 0
RESULT_TYPE      = ellipse3                          ✅ cả ba
CYLINDER         = cylinder · anchor/apex/rim_point  ✅ cả ba
MEASURE          = area, of = E                      ✅ cả ba
PROVENANCE O/O′/R = source_fact_id                   ✅ cả ba
PLANE_POINTS_ON_EQUATION (attempt 2) = cả ba điểm THOẢ `2x − z + 10 = 0` ✅
```

Ba điểm mà mô hình chọn ở attempt 2 **đúng về hình học** — chúng thoả phương
trình. Thứ bị bác là **xuất xứ**, không phải toạ độ.

## 12. BLOCKER — `PLANE_FROM_EQUATION_REPRESENTATION`

`SYSTEM_GAP` (biểu đạt) + `OPERATOR_AFFORDANCE`. Đo tất định, 0 lượt gọi thêm:
một mặt phẳng cho bằng **phương trình** có đúng ba lối biểu đạt, và **chỉ một
lối chạy được**:

| lối | kết quả |
|---|---|
| **A** — khai `plane3` bằng `initial_value` + `source_fact_id` | `grounding` **từ chối**: *"giá trị […] không có trong mục `mat_phang_alpha`"* |
| **B** — ba `point3` chỉ có `model_assumption` | `grounding` **từ chối**: `UNANCHORED_DERIVED_ASSUMPTION` |
| **C** — ba `point3` mang `source_fact_id` trỏ fact phương trình | **chạy được** — đây là đường gold |

Và `_KIEU_DUNG`/`_CHU_KY` **không có phép nào** chứa chữ `equation`.

⚠️ **Điểm đắt nhất của phép đo:** lối C — lối duy nhất chạy được — đòi gắn
`source_fact_id` vào **toạ độ mà đề không hề nêu**. Đề cho một *phương trình*,
không cho ba điểm. Mô hình chọn `model_assumption` là **ngữ nghĩa ĐÚNG** — nó
thật sự **tự chọn** ba điểm ấy, và lời khai của nó nói đúng như vậy:
*"Điểm thứ nhất được chọn để xác định mặt phẳng alpha (2x − z + 10 = 0)"*.
Grounding bác nó, và grounding **không sai** theo luật hiện có.

Nói cách khác: **hệ buộc mô hình phải khai xuất xứ không trung thực để đi
được.** Đó là một khoảng trống biểu đạt, không phải một lỗi của mô hình.

Bằng chứng mạnh nhất cho hướng sửa: ở attempt 1, mô hình **tự đặt tên đúng phép
còn thiếu** — `construct_plane_from_equation(a, b, c, d)`.

## 13. Phân loại từng phát hiện

| phát hiện | loại | vì sao |
|---|---|---|
| IR không có phép mặt-phẳng-từ-phương-trình; ba lối biểu đạt, một lối chạy | **`SYSTEM_GAP`** | tái hiện tất định, đọc thẳng `_KIEU_DUNG` + ba replay |
| lối chạy được đòi xuất xứ không trung thực | **`SYSTEM_GAP`** | tái hiện tất định (lối A/B/C) |
| mô hình tự đặt tên `construct_plane_from_equation` | **`OBSERVATION`** | 1 trong 3 attempt, `n = 1` |
| mô hình chọn `model_assumption` thay `source_fact_id` cho điểm tự chọn | **`HYPOTHESIS`** | `n = 1`; và lựa chọn ấy **hợp lý về ngữ nghĩa** |

## 14. Cổng đã chạy

> Đo lại sau khi commit bàn giao. Lượt quét giữa wave cho **4258 pass + 1
> đỏ** — cổng `test_holdout_readiness_7b` đỏ **đúng chức năng** vì cây còn
> bẩn. Trên cây sạch `2beb693` nó xanh, nên tổng là **4259 pass, 0 đỏ**.

| cổng | kết quả |
|---|---|
| scope-gate (Pha A) | **43 pass**, 4 phép tiêm |
| gold preflight elip | **20 pass** |
| runner/scorer stub | **18 pass** |
| `pytest -q` (cây sạch) | **4259 pass**, 1 skip, 1 deselect, **0 đỏ** |
| `replay_demo_cases.py` | **5/5**, `REDUCED_CHAIN 1/1` |
| `audit_demo_crash_surface.py` | **6/6 biên**, ném **0** |
| `certify_acceptance_runner.py` | **PASS**, 0 lượt gọi |
| `lock_cache_identity.py --verify` | **exit 0** @ v88 |
| `freeze_evaluation_candidate --verify` | **exit 0**, 90 file, `f48e768b…` |
| `git diff --check` | sạch |
| frontend | **kế thừa** — Scene3D không đụng |

## 15. Báo cuối

```
ROOT_CAUSE = `_MANH_MOI_NGHIA_VU` thieu 4 nghia vu vua analyze-emittable vua
             checker-backed ⇒ `co_duong_thuc_thi` fail-closed mot LOP bai
OBLIGATION_SCOPE_PARITY        = PASS   (dan tu `analyze enum ∩ GEOMETRY_CHECKERS`)
AREA_ROUTABLE                  = YES
LATERAL_AREA_ROUTABLE          = YES
RADIUS_ROUTABLE                = YES
SECTION_MATCHES_ROUTABLE       = YES    (truoc day MUON manh moi cua `coplanar`)
SCOPE_FALSE_POSITIVE_REGRESSION = KHONG — 8 manh moi cu dinh tuyen y nhu truoc;
             ngoai mien, chuoi rong va de khong hoi gi van fail-closed
FAULT_INJECTION_COUNT          = 4 (moi nghia vu mot phep, cham o muc TAP)

ELLIPSE_GOLD_PREFLIGHT   = PASS
BLOCKED_BEFORE_PROVIDER  = NO    (Pha A da mo cong; luot live DA chay)
FIRST_ATTEMPT_SERVABLE   = NO
EVENTUAL_SERVABLE        = NO
EXACT_ANSWER             = NOT_REACHED   (mong doi 16√5π; gold PASS)
POSTCONDITIONS_PASS      = NOT_REACHED
TRACE_PASS               = NOT_REACHED
SCENE3D_PASS             = NOT_REACHED
ANALYZE_CONTRACT         = PASS  (toan bo 7 chieu)
MODEL_DISCOVERABILITY    = NOT_CONFIRMED_ONE_CASE
STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED

ANALYZE_CALLS = 1     INITIAL_SYNTHESIS_CALLS = 1    REPAIR_CALLS = 2
LOGICAL_APPLICATION_CALLS = 4/5     PHYSICAL_API_ATTEMPTS = 4
TRANSPORT_RETRIES = 0               CANDIDATE_PROGRAM_ATTEMPTS = 3
TOTAL_TOKENS = 20 725 / 40 000      CACHED_CONTENT_TOKENS = 0
APPLICATION_LLM_CALLS = 4

CACHE_VERSION_BEFORE/AFTER   = 87 → 88   (bump theo LUAT, tien le 80)
CANDIDATE_HASH_BEFORE/AFTER  = e8c6150f… → f48e768b…
MODEL_FACING_HASHES_CHANGED  = KHONG, ca sau — Pha A chi sua DUONG VAO
PRODUCT_CAPABILITY_CHANGED   = NO   (curved_oblique_section giu foundation_only)
PRODUCT_PROMOTION_ELIGIBLE   = NO

TEST_RESULTS = pytest 4259 pass · 1 skip · 1 deselect · 0 do (cay SACH @ 2beb693)
               replay 5/5 · crash 6/6 nem 0 · certify PASS · cache identity exit 0
               freeze --verify exit 0 · diff --check sach
COMMITS = 4        WORKING_TREE = sach
RECOMMENDED_NEXT_ACTION = PLANE_FROM_EQUATION_REPRESENTATION
```

⚠️ **`ELLIPSE_FOUNDATION_SEQUENCE` KHÔNG đóng** —
`CARD_C_CURVED_ELLIPSE_PATH_CONFIRMED` giữ **`NOT_MEASURED`**. Điều kiện là
*eventual served*, và nó chưa đạt.

## 16. Giới hạn bằng chứng

- **`n = 1` lượt chạy, 3 attempt.** `DEVELOPMENT_SIGNAL`, không phải ước lượng
  tổng thể.
- **Không được đọc thành *"mô hình không làm được bài elip"*.** Nó chọn đúng
  toán tử ngay attempt 0, khai đúng kiểu, dựng đúng hình trụ, đo đúng đại
  lượng, và ba điểm nó chọn **thoả đúng phương trình**. Thứ chặn nó là một
  khoảng trống biểu đạt của **hệ**.
- **Pha A đã được xác nhận trên đường sản phẩm**, không chỉ ở mức hàm: lượt
  live đi qua `scope` → `analyze` → 3 lượt sinh.
- Blocker phân loại `SYSTEM_GAP` vì tái hiện tất định (ba lối A/B/C đo được,
  `_KIEU_DUNG` đọc được), **không** phụ thuộc một lượt sinh nào.

**Việc kế tiếp: `PLANE_FROM_EQUATION_REPRESENTATION`.** Hai đường, chọn bằng
kiểm toán chữ ký như wave nền elip đã làm:

1. **Một phép dựng mới** — `construct_plane_from_equation(a, b, c, d) → plane3`.
   Mô hình đã tự đặt đúng tên và đúng chữ ký. Toạ độ ở lại ℚ³ (hệ số hữu tỉ ⇒
   pháp tuyến và một điểm trên mặt phẳng đều hữu tỉ). Xuất xứ trung thực: mặt
   phẳng dẫn **thẳng** từ fact phương trình, không qua ba điểm bịa.
2. **Một luật grounding** — chấp nhận điểm *dẫn xuất từ* một fact phương trình.
   Rẻ hơn nhưng nới một cổng đang gác đúng, và vẫn để mô hình phải tự chọn ba
   điểm.

Bằng chứng nghiêng về **(1)**: nó đóng cả hai `SYSTEM_GAP` cùng lúc, và đó là
lối duy nhất giữ được lời khai xuất xứ trung thực.

⚠️ Token của Claude Code **không** tính vào token vận hành AlgoSim.
