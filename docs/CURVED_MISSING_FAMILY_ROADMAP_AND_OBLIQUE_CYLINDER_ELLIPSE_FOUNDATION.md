# CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_CYLINDER_ELLIPSE_FOUNDATION

> 2026-09-07. **`APPLICATION_LLM_CALLS = 0`.** Chuyển từ tối ưu khả năng sinh
> của Card C sang **mở rộng năng lực hình học thật**.
>
> ```
> ROADMAP_EVIDENCE_COMPLETE     = YES   (4/4 họ, đọc thẳng mã nguồn)
> FIRST_SELECTED_MISSING_FAMILY = curved_oblique_section (elip của HÌNH TRỤ)
> SYSTEM_EXPRESSIBLE            = YES
> DETERMINISTICALLY_CORRECT     = YES   (9√2π, hai oracle độc lập)
> MODEL_DISCOVERABLE            = NOT_MEASURED
> STABILITY_UNDER_ACCEPTANCE    = NOT_MEASURED
> ```
>
> Wave này chứng minh **hai mức đầu**, và chỉ hai. Không một lượt gọi model nào,
> nên không dòng nào ở đây được đọc như bằng chứng về hành vi mô hình.

## 1. Trạng thái đầu

HEAD `d4e56ed` · cây **sạch** · `CACHE_VERSION` **86** · candidate
`138db7b1…` (`--verify` exit 0, 90 file) · `PRODUCT_VARIANT` **C**
(`ac07f716…`, 5855 B, trùng byte `card_C.txt`).

Sáu băm model-facing @ v86: `prompts 55ac1ca6…` · `grammar_card 9685b06a…` ·
`synthesis_schema 8c57c9de…` · `analyze_schema 515001b5…` ·
`capability 85bd3167…` · `semantic_environment 2178b6d4…`.

**Hai affordance đã đo của Card C còn nguyên**, kiểm bằng máy:
`t = m/(m+n)` ✓ · dòng `Xuất xứ:` ✓.

Capability hình cong trước wave: `ball` · `cylinder` · `cone` =
**`foundation_only`** (giữ nguyên suốt wave này).

## 2. Bản đồ bốn họ còn thiếu — đọc thẳng mã nguồn

⚠️ **Ba trong bốn họ ĐÃ có trong bảng capability** với lý do ghi sẵn
(`product_capability.py`); wave này kiểm lại từng lý do trên cây hiện tại thay
vì tin dòng chữ.

| Họ | Kiểu hiện có | Phép dựng hiện có | Exact kernel | Checker | Trace | Scene3D | **Khoảng trống nhỏ nhất** |
|---|---|---|---|---|---|---|---|
| **Thiết diện cong xiên** | `curved_solid` · `plane3` · `circle3` — **không** conic | `construct_curved_solid` · `construct_plane` · `intersect_plane_curved` | ✅ đủ: `9√2π` = `he·√can·π¹`, **nằm trong** miền `Radical` | ✅ `check_area` **dẫn** kiểu từ `BANG_PHEP_DO` | ✅ `_BIEU_THUC_HINH_HOC` **dẫn** từ `_CHU_KY` | ➖ cần 1 hàng `RENDER_HINT` + 1 nhánh vẽ | **1 kiểu + 1 phép** |
| Khối tròn xoay tổng quát | `curved_solid` chở đúng ba hình (`KHOI_CONG` đóng) | — | ❌ thể tích cần **tích phân**; `Radical` chỉ chở `he·√can·π^mu`, `mu ∈ {0,1}` | — | — | — | **MIỀN SỐ** — không phải một kiểu hay một phép |
| Khối ghép · khối bù | `solid` (đỉnh + mặt) | `construct_solid` | ❌ `grep union\|difference\|subtract\|boolean` trong `geometry/` → **0 hit** | — | — | — | **cả một hệ con**: biên hỗn hợp + thuật toán boolean + checker |
| Đa diện KHÔNG lồi | ✅ `solid` đã có | ✅ `construct_solid` đã có | ⚠️ `volume_pyramid_fan` chia quạt: **kiểm phẳng, KHÔNG kiểm lồi** — đáy lõm cho số sai **im lặng** | dùng chung `check_volume` | ✅ | ✅ | **1 thuật toán thể tích không phụ thuộc lồi** + 1 checker |

### 2a. Xếp hạng theo bảy tiêu chí đo được

| tiêu chí | cong xiên | tròn xoay | ghép–bù | không lồi |
|---|---|---|---|---|
| tái sử dụng đường hiện tại | **cao nhất** — 3/3 phép đầu vào đã có | thấp | thấp | cao |
| biểu diễn chính xác ℚ/√/π | ✅ **chứng minh được** | ❌ ngoài miền | ❌ | ✅ |
| checker server-owned | ✅ tự nhận | ❌ | ❌ | ⚠️ phải sửa thẩm quyền dùng chung |
| trace theo bước | ✅ tự có | — | — | ✅ |
| trình bày Scene3D | ➖ 1 nhánh | — | — | ✅ |
| blast radius | **nhỏ nhất** | lớn | **lớn nhất** | trung bình — chạm `volume_polyhedron` |
| không cần module theo bài | ✅ | ✅ | ✅ | ✅ |

**`SELECTION_REASON`**: cong xiên thắng ở **năm trên bảy** tiêu chí và không
thua ở tiêu chí nào. Quyết định không dựa vào kỳ vọng trong brief mà vào ba
phép đo: ① miền số **đã** chở được `9√2π`; ② checker và trace **dẫn xuất**, nên
mở một kiểu là chúng tự nhận; ③ khoảng trống thu về **đúng hai thứ** — một kiểu
và một phép.

⚠️ **Ứng viên gần thứ hai là *đa diện không lồi*, không phải hai họ còn lại** —
và nó mang một khiếm khuyết **có sẵn, chưa ai ghi**: `volume_pyramid_fan` kiểm
đáy **phẳng** nhưng **không kiểm lồi**, nên một đáy lõm cho một con số trông
hợp lý mà vô nghĩa. Ghi vào đây làm việc kế tiếp có địa chỉ; wave này **không**
sửa nó (chạm thẩm quyền dùng chung với `check_volume`).

## 3. Tái hiện khoảng trống — TRƯỚC khi sửa

Chương trình gold cho `r = 3`, `h = 20`, trục `Oz`, mặt phẳng `z = 10 + x`,
chạy qua đường hiện tại:

```
stage      = execution
servable   = False
error_code = semantic_program_invalid
detail     = [CURVED_SECTION_OUTSIDE_V1_CLOSURE]
             "hình trụ: mặt phẳng không vuông góc với trục. Giao khi ấy là một
              elip (hoặc conic khác), thứ phiên bản này không biểu diễn được."
```

Nó **đi qua** schema · `ir_static` · grounding · phủ · **cả hai** bất biến
nguồn, rồi mới chết ở `execution`. Kết luận định vị: khoảng trống thuộc
**kernel + hệ kiểu**, KHÔNG thuộc checker, measure hay renderer — ba tầng ấy
chỉ thiếu một hàng vì chúng **dẫn xuất**.

⚠️ Bản tái hiện đầu bị `grounding` chặn trước (`UNANCHORED_DERIVED_ASSUMPTION`)
vì đề tổng hợp không đặt tên ba điểm mặt phẳng. Đó **không phải** khoảng trống
cần đo — neo chúng bằng `source_fact_id` rồi mới tới được tầng thật. Ghi ra để
lần sau không ai đọc lời từ chối ấy như một phát hiện.

Phép tái hiện giữ lại làm test (`test_16`): nếu ai đó "sửa" phép cũ để nó nhận
mặt phẳng xiên thì hai phép chồng nhau và kiểu trả về tĩnh mất nghĩa.

## 4. Biểu diễn — `NEW_MEMORY_TYPES = 1` · `NEW_IR_OPERATIONS = 1`

### `ellipse3` — mọi trường ở ℚ

```
center · normal · major_dir · minor_dir · semi_major_sq · semi_minor_sq
```

Giữ **bình phương** bán trục, cùng mẹo `Circle3.radius_sq`: bán trục có thể vô
tỉ (`3√2`), bình phương thì không. Hai **phương** trục cũng ở ℚ³, và điều ấy
không hiển nhiên — nó là hệ quả của cách dựng: `minor_dir = u × n` nằm trong
mặt phẳng và ⊥ trục; `major_dir = n × minor_dir` nằm trong mặt phẳng và ⊥
`minor_dir`. Cả hai là tích có hướng của vectơ hữu tỉ. **Chuẩn hoá độ dài —
thứ sẽ đá chúng khỏi ℚ³ — không làm ở kernel; renderer làm.**

Vì sao **không** gộp vào `circle3`: đường tròn có MỘT bán kính, elip có HAI bán
trục và HAI phương. Nhét vào thì `radius` mất nghĩa, `area` phải đoán `radius_sq`
là `a²` hay `b²`, renderer vẽ vòng tròn cho hình không tròn.
Vì sao **không** gộp vào `section`: `section` là ĐA GIÁC — nó mang dãy cạnh và
`section_matches` kiểm bằng đỉnh. Elip không có đỉnh nào.

### `intersect_plane_curved_ellipse` — phép RIÊNG

`intersect_plane_curved` khai `circle3` và **chỉ** trả `circle3`; đó là toàn bộ
giá trị của nó với thẩm định tĩnh. Cho nó trả *"tuỳ hình học lúc chạy"* là bỏ
đúng tính chất ấy — kiểu kết quả khi đó chỉ biết SAU khi chạy, nên
`ir_static_check` mất khả năng bắt lỗi **trước** một lượt chạy.

Hai phép, hai kiểu trả về xác định. Mô hình chọn theo NGỮ NGHĨA của đề, đúng
cách nó đã chọn giữa `construct_section` và `intersect_plane_curved`.

## 5. Đúng hình học và exact arithmetic

Dẫn từ vectơ trục `u` và pháp tuyến `n`:

```
b² = r²                                  (bán trục NHỎ = bán kính, luôn)
a² = r²/cos²θ = r²·|n|²|u|² / (n·u)²     (bán trục LỚN)
S  = π·a·b = π·√(a²·b²)
```

Cả hai hữu tỉ: `|n|²`, `|u|²`, `(n·u)²` đều là tích vô hướng của vectơ hữu tỉ.
Không phép chia nào cho một căn ⇒ **không float nào lọt vào**.

`S` tính bằng `√(a²b²)` chứ **không** bằng `√a²·√b²`: hai căn riêng rồi nhân là
hai hạng tử mà `radical.multiply` phải hợp nhất lại; nhân TRONG căn thì phép
rút thừa số chính phương chỉ chạy một lần.

### Hai oracle độc lập

| # | lối | kết quả |
|---|---|---|
| ① | giải tích: `a² = 9·2·400/400 = 18`, `b² = 9` ⇒ `S = π√162` | **`9π√2`** |
| ② | **thế thẳng**: bốn đầu mút trục vào `x²+y²=9` và `n·(P−C)=0` | **`9π√2`** |

Oracle ② không dùng lại `a²`/`b²` mà kernel vừa tính. Bốn đầu mút ra
**hữu tỉ**: `(±3, 0, 13/7)` và `(0, ±3, 10)` — cả bốn thoả **đồng thời** phương
trình mặt trụ và phương trình mặt phẳng. Một mình lối ① là kiểm công thức bằng
chính công thức.

## 6. Phạm vi V1 — năm biên, năm mã riêng

| ca | mã |
|---|---|
| mặt phẳng ∥ trục | `CURVED_ELLIPSE_OUTSIDE_V1_CLOSURE` |
| mặt phẳng ⊥ trục | `CURVED_ELLIPSE_OUTSIDE_V1_CLOSURE` — **nêu tên phép đúng**: `intersect_plane_curved` |
| elip bị một đáy cắt | `CURVED_ELLIPSE_CROSSES_CAP` |
| mặt phẳng ngoài khối | `CURVED_PLANE_DOES_NOT_CUT` |
| cầu · nón cắt xiên | `CURVED_ELLIPSE_OUTSIDE_V1_CLOSURE` |

Điều kiện "nằm trọn giữa hai đáy" so bằng **bình phương** ở cả hai đầu, nên
hình trụ chiều cao vô tỉ vẫn kiểm được:
`h_half² = r²·(|n|²|u|² − (n·u)²)/(n·u)²`.

⚠️ Với hình trụ, **tiếp xúc và song-song-trục là cùng một điều kiện hình học** —
ghi thành test riêng (`test_11`) chứ không gộp, để người đọc sau khỏi phải suy.

Đường cũ **không suy suyển**: ⊥ trục vẫn cho `circle3`, `radius`/`area` của
đường tròn giữ nguyên, cầu và nón giữ nguyên hành vi.

## 7. Một lỗ ĐÃ TRÔI HAI LẦN, sửa trong wave này

Dòng `type nhận đúng một trong` của thẻ là một danh sách **CHÉP TAY** liệt kê
kiểu ĐƯỢC PHÉP, và nó đã trôi hai lần: thiếu `circle3` + `curved_solid` (thêm
2026-09-03), rồi thiếu `ellipse3`.

Hậu quả **đo được**, không suy: `CURVED_END_TO_END_FRESH_CONFIRMATION` attempt 1
— mô hình khai thiết diện là **`section`**, kiểu mà thẻ CÓ liệt kê — rồi hỏng ở
`ir_static`, mất một lượt sửa. Wave ấy ghi nó là `HYPOTHESIS` vì `n = 1`.

Sửa: đảo chiều danh sách. Nay dẫn xuất bằng cách **LOẠI TRỪ** tập Tin học đã
đóng băng (`_KIEU_TIN_HOC`). Tập ấy chỉ co lại, tập hình học thì đang lớn — nên
thêm một kiểu hình học từ nay **tự hiện ra trong thẻ**. Khoá bằng
`test_the_liet_ke_DU_moi_kieu_hinh_hoc_khai_duoc`.

## 8. Measure · obligation · checker · trace · Scene3D

**Ba tầng tự nhận, không sửa một dòng logic nào** — đó là bằng chứng cho thiết
kế một-thẩm-quyền:

| tầng | cơ chế | phải sửa? |
|---|---|---|
| `OBLIGATION_KINDS["area"]` | **dẫn** từ `BANG_PHEP_DO` | ❌ tự có `ellipse3` |
| `check_area` | **dẫn** kiểu từ `BANG_PHEP_DO`, gọi `area_of` dùng chung với đường chạy | ❌ |
| `_BIEU_THUC_HINH_HOC` (trace/depends) | **dẫn** từ `_CHU_KY` | ❌ |
| `BANG_PHEP_DO["area"].kieu_of` | bảng thẩm quyền | ✅ +1 kiểu |
| `SURFACE_POLICY` | quyết định hiển thị, tường minh theo thiết kế | ✅ +1 dòng |
| `RENDER_HINT` · `_TRUONG` · TS `RENDER_KINDS` · view | trình bày | ✅ +1 loại vẽ |

Renderer là **tầng duy nhất** chuyển đại lượng chính xác sang float: nó lấy căn
`semi_*_sq` và chuẩn hoá hai phương ở biên hiển thị. Vành elip dựng bằng
`BufferGeometry` từ hai phương — **không** dùng `RingGeometry` + scale không
đều, phép ấy bóp méo cả bề rộng nét.

**Bao đóng phụ thuộc** (`test_19`): từ `dt_E` truy ngược tới đủ
`{E, tru, mp, O, O2, r, K, L, N}`.

## 9. Bộ test — 29 pass, ba phép tiêm chịu lực

`backend/tests/geometry/test_oblique_cylinder_ellipse.py`

Mười hai yêu cầu của brief đều có test; ba điểm chịu lực đều tiêm và đỏ được:

| phép tiêm | hệ quả khi gỡ chốt |
|---|---|
| **hệ số bán trục lớn** (`a² := b²`) | `S = 9π` thay vì `9√2π` — mọi test cấu trúc vẫn xanh, chỉ đáp số sai |
| **kiểm nằm trọn giữa hai đáy** | ca `z0 = 1` đi lọt, trả một elip **DỐI** cho hình không phải elip |
| **liên kết producer/dependency** | elip **biến mất khỏi cảnh** — mạnh hơn dự đoán ban đầu |

⚠️ **Hai giả định của chính bộ test đã sai và được sửa bằng phép đo**, ghi lại
vì chúng nói về hệ:

- `test_17` ban đầu khẳng định `ir_static` chặn khi khai `E` là `circle3` rồi
  gán bằng phép elip. Chạy thử: **không chặn** — kiểu **dựng ra** thắng kiểu
  **khai** ở mọi tầng (`bang_ky_hieu` nói thẳng điều ấy), đáp số vẫn đúng, cảnh
  vẫn nhận `ellipse3`. Đây là hành vi **có sẵn từ trước**; test nay ghi đúng nó
  thay vì khẳng định một cổng không tồn tại.
- `test_21` ban đầu tiêm `_NGUON_CUA_PHEP_DUNG` và **vẫn xanh** — tức không gác
  gì. Bảng đúng là `validator._BIEU_THUC_HINH_HOC` (vật sinh bởi `assign` đi
  nhánh biểu thức), và nó được nhập **bên trong hàm** nên phải vá ở module sở
  hữu.

## 10. Model-facing và cache

```
prompts            55ac1ca6…  →  55ac1ca6…   KHÔNG đổi
analyze_schema     515001b5…  →  515001b5…   KHÔNG đổi
grammar_card       9685b06a…  →  4b435fbb…   ĐỔI
synthesis_schema   8c57c9de…  →  d69661ce…   ĐỔI
capability         85bd3167…  →  e0214b77…   ĐỔI
semantic_env       2178b6d4…  →  9d0374a7…
```

`analyze_schema` không đổi vì nghĩa vụ `area` đã có từ bump 78 — wave này chỉ
nới **tập kiểu chủ thể** của nó.

**`CACHE_VERSION` 86 → 87**, bốn cổng cùng commit. Lý do đúng tiền lệ bump
70/73: cache giữ **cả envelope**, nên đề đã phân tích sẽ trả lại chương trình
sinh bởi **thẻ cũ** — thẻ không có phép elip và không liệt kê `ellipse3`. Đo từ
vựng mới bằng đầu ra của thẻ cũ rồi kết luận *"thêm phép chẳng thay đổi gì"* là
đúng cái bẫy hai lần bump ấy đã ghi. Lý do độc lập thứ hai, cùng hạng với bump
68/78: **lược đồ gửi cho mô hình đổi**.

⚠️ Kiểm cache đã làm: **không envelope cũ nào hoá sai** — `main.py` chỉ cache
`status == "ok"`, và wave này chỉ biến từ-chối → phục-vụ.

**Card C giữ nguyên nghĩa**: hai affordance đã đo còn nguyên văn; phần chênh so
với `card_C.txt` **chỉ** là từ vựng (4 dòng: 1 thêm, 3 sửa danh sách kiểu/đo).
Guard byte-match cũ đổi sang kiểm **hai dòng ấy còn nguyên** thay vì so byte —
so byte từ nay chỉ nói *"thẻ đã đổi"*, câu vô ích vì thẻ SẼ đổi mỗi lần mở
năng lực.

Thẻ hình học `5855 → 6042` byte (`+187`): `+157` từ vựng mới, `+30` sửa nhãn
sai (§7). Trần `5900 → 6100`.

## 11. Capability

```
curved_oblique_section:  unsupported  →  foundation_only
```

Lý do cũ — *"giao là elip — không có kiểu conic trong IR"* — nay **SAI**, và
được thay bằng bằng chứng chạy được. **Không** lên `supported`: hệ diễn đạt và
tính đúng, nhưng **chưa ai đo** mô hình có tự tìm ra phép ấy không — cùng luật
đang áp cho ball/cylinder/cone, và cả ba **giữ nguyên** trạng thái trong wave
này.

Phạm vi khai thẳng trong bảng: chỉ **hình trụ**, mặt phẳng xiên, elip nằm trọn
giữa hai đáy. **Nón xiên vẫn ngoài phạm vi.**

## 12. Báo cuối

```
ROADMAP_EVIDENCE_COMPLETE     = YES  (4/4 ho, moi o tro chu ky hoac grep tren cay hien tai)
FIRST_SELECTED_MISSING_FAMILY = curved_oblique_section — elip cua HINH TRU
SELECTION_REASON              = thang 5/7 tieu chi, khong thua o tieu chi nao;
                                mien so DA cho duoc 9√2π · checker+trace DAN XUAT
                                nen tu nhan kieu moi · khoang trong = 1 kieu + 1 phep
BEFORE_REPRODUCTION           = stage `execution` · CURVED_SECTION_OUTSIDE_V1_CLOSURE
                                (qua schema · ir_static · grounding · phu · bat bien nguon)

NEW_MEMORY_TYPES              = 1   (`ellipse3`)
NEW_IR_OPERATIONS             = 1   (`intersect_plane_curved_ellipse`)
SYSTEM_EXPRESSIBLE            = YES
DETERMINISTICALLY_CORRECT     = YES
EXACT_AREA_ORACLE             = 9√2π  — HAI oracle doc lap (giai tich · the thang)
TRACE_PASS                    = YES  (1 buoc sinh elip · depends {tru, mp} ·
                                      bao dong tu dt_E ve du 9 vat)
SCENE3D_PASS                  = YES  (render `ellipse` · 6 truong exact, khong float)
MODEL_DISCOVERABLE            = NOT_MEASURED
STABILITY_UNDER_ACCEPTANCE    = NOT_MEASURED
APPLICATION_LLM_CALLS         = 0

CACHE_VERSION_BEFORE/AFTER    = 86 → 87
CANDIDATE_HASH_BEFORE/AFTER   = 138db7b1… → e8c6150f…
MODEL_FACING_BEFORE/AFTER     = grammar_card 9685b06a→4b435fbb ·
                                synthesis_schema 8c57c9de→d69661ce ·
                                capability 85bd3167→e0214b77 ;
                                prompts va analyze_schema KHONG doi mot byte
PRODUCT_CAPABILITY_CHANGED    = YES — curved_oblique_section unsupported →
                                foundation_only (ball/cylinder/cone GIU NGUYEN)

TEST_RESULTS = test elip 29 pass (3 phep tiem) · pytest 4172 pass, 1 skip,
               1 deselect, 0 do · vitest 698/51 · build PASS · replay 5/5
               (REDUCED_CHAIN 1/1) · crash 6/6 nem 0 · certify_acceptance_runner
               PASS 0 luot goi · cache identity exit 0 · freeze --verify exit 0 ·
               git diff --check sach
WORKING_TREE = sach
RECOMMENDED_NEXT_ACTION = OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION
```

## 13. Giới hạn bằng chứng

- **Wave này KHÔNG đo hành vi mô hình.** `MODEL_DISCOVERABLE` và
  `STABILITY_UNDER_ACCEPTANCE` = `NOT_MEASURED`, và không con số nào ở đây được
  đọc theo hướng ấy. Nói *"hệ làm được elip"* là đúng; nói *"AI sinh được bài
  elip"* là nói quá.
- **Bao đóng V1 hẹp có chủ đích**: chỉ hình trụ, chỉ elip **đầy đủ**, chỉ mặt
  phẳng xiên. Nón xiên (elip/parabol/hyperbol tuỳ độ dốc) **chưa phân xử**.
- **Một ca chuẩn**, kèm bốn ca biên. Không phải một khảo sát trên lớp bài.
- **Khiếm khuyết đã ghi, chưa sửa**: `volume_pyramid_fan` không kiểm **lồi** —
  đáy lõm cho số sai im lặng. Có sẵn từ trước, ngoài phạm vi wave này, và là
  điểm vào có địa chỉ cho họ *đa diện không lồi*.
- **Hành vi đã ghi, chưa siết**: kiểu **khai** của một vật dựng ra là trang trí
  — kiểu **dựng ra** thắng ở mọi tầng (§9). Đúng theo thiết kế hiện có; siết
  lại là một lượt riêng chạm mọi chương trình đang khai lỏng.

**Việc kế tiếp: `OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION`** — đúng một
phép xác nhận end-to-end trên một đề elip **mới**, có `analyze` và vòng sửa như
sản phẩm thật, theo khuôn `CURVED_END_TO_END_FRESH_CONFIRMATION`. Nó là thứ
duy nhất trả lời được câu wave này cố ý không hỏi: **mô hình có tự tìm ra phép
mới không** — và §7 vừa gỡ một chướng ngại đã đo được cho đúng câu ấy.
