# OBLIQUE_ELLIPSE_FRESH_E2E_RERUN

> 2026-09-07 · **DỪNG TRƯỚC PROVIDER** · `APPLICATION_LLM_CALLS = 0`
>
> ```
> GOLD_PREFLIGHT              = PASS
> CYLINDER_DIRECT_RADIUS_PATH = FAIL   ← điều kiện dừng của §4
> BLOCKER = CURVED_SCALAR_AXIS_SCALE_IN_ELLIPSE_CAP_CHECK · loại KERNEL
> ```
>
> Không tiêu một lượt quota nào, và đó là kết quả **đúng** chứ không phải một
> lượt hỏng. §4 đặt sẵn điều kiện dừng; nó đã bật, và nó bật vì một **lỗi trong
> mã sản phẩm**, không phải vì fixture.

## 1. Trạng thái đã xác minh (§2)

```
HEAD = 313ed17   WORKING_TREE = sạch   CACHE_VERSION = 89
CANDIDATE = 422a9e7b78811d96… (91 file)   PRODUCT_VARIANT = C
CURVED_OBLIQUE_SECTION = foundation_only
```

| thành phần | băm |
|---|---|
| `prompts` | `55ac1ca6a6df92ce…` |
| `grammar_card` | `285292feed07e603…` |
| `synthesis_schema` | `6ccef3230c003d61…` |
| `analyze_schema` | `515001b503af5c7c…` |
| `capability` / `stable_capability` | `4b1e2f80a5a4bf26…` |
| `semantic_environment` | `05b5c6bbb1852700…` |

`freeze --verify` exit 0 · `lock_cache_identity --verify` exit 0.

**Thẻ có đủ năm thứ §2 đòi**: `construct_plane_from_equation(a,b,c,d) → plane3`
· `intersect_plane_curved_ellipse` · `area(of: …|ellipse3)` · ô `radius`/
`height` của `construct_curved_solid` · hai affordance `t = m/(m+n)` và
`Xuất xứ:` của Card C.

⚠️ **Một bất đối xứng ghi lại, không sửa**: `radius?:tên<scalar|float|int>[ĐẠI
LƯỢNG bán kính…]` có vai trò in ra, còn `height?:tên` **không** — `height`
vắng trong `hoisting.O_TEN`, nên thẻ không nói được nó là gì. Wave không đụng
bề mặt mô hình (§14), nên đây là quan sát, không phải bản vá.

## 2. Gold preflight — PASS (§4)

Gold dựng mặt phẳng bằng **phép mới**, đi trọn `scope → analyze-fixture →
schema → static → grounding → source invariants → coverage → interpreter →
postconditions → exact → trace → Scene3D`:

```
SERVABLE = YES · stage = served · EXACT_AREA = 16π√5
SOURCE_INVARIANT checked=1 passed=1 violated=0
TRACE: 1 bước CREATE · depends [] · "…từ phương trình 2x - z + 10 = 0"
SCENE3D: alpha là plane3, producer construct_plane_from_equation, có ellipse3
```

### Bảy phản ví dụ

| # | ca | kết quả |
|---|---|---|
| ① | `2x − z + 11 = 0` — song song, **cùng diện tích** | `violated = 1`, từ chối ✅ |
| ② | mặt phẳng suy biến `(0,0,0)` | lược đồ từ chối ✅ |
| ③ | sai hệ số `a = 3` | từ chối ✅ |
| ④ | mặt phẳng ∥ trục (`x = 3`) | `CURVED_ELLIPSE_OUTSIDE_V1_CLOSURE` ✅ |
| ⑤ | elip vượt hai đáy (trụ cao 4) | `CURVED_ELLIPSE_CROSSES_CAP` ✅ |
| ⑥ | điểm vành không xuất xứ | `UNANCHORED_DERIVED_ASSUMPTION` ✅ |
| ⑦ | **trụ dùng trực tiếp `radius` + `height`** | ❌ **FAIL** — xem §3 |

Ca ① đáng nhắc lại: nó `served` được với **đáp số ĐÚNG** nếu bỏ bất biến nguồn.
Mặt phẳng song song cho elip bằng hệt, nên mọi cổng hỏi *đáp số* đều xanh.

## 3. Blocker — `CURVED_SCALAR_AXIS_SCALE_IN_ELLIPSE_CAP_CHECK`

**Cùng một hình trụ, hai cách khai, hai kết quả khác nhau.**

```
(A) hai điểm   anchor=(0,0,0) · apex=(0,0,20) · r²=16   → ELIP, 16π√5
(B) vô hướng   anchor=(0,0,0) · r²=16 · h²=400          → TỪ CHỐI
```

Hai khối **bằng nhau về hình**, kiểm bằng máy: `radius_sq` 16 = 16 ·
`height_sq` 400 = 400 · trục cùng phương Oz.

### Gốc lỗi: một biểu thức

`curved.py::intersect_plane_curved_ellipse`:

```python
L    = (tâm − anchor)·u / (u·u)
tren = 1 − L                      # chỉ đúng khi |u| = h
```

`huong_truc` trả **hai thứ khác nhau về THANG**:

| khai bằng | `u` | `|u|` | `L` là |
|---|---|---|---|
| hai điểm | `truc` | `h` | **tỉ lệ** `0…1` |
| vô hướng | `HUONG_TRUC_CANONICAL` | `1` | **khoảng cách tuyệt đối** `0…h` |

Đo được:

```
(A) u=(0,0,20)  |u|²=400  L = 1/2   tren = 1 − 1/2 = 1/2   ✅
(B) u=(0,0,1)   |u|²=1    L = 10    tren = 1 − 10  = −9    ⇒ tren < 0
                                    ⇒ CURVED_ELLIPSE_CROSSES_CAP
```

`duoi_sq = L²·|u|²` **đúng ở cả hai nhánh** (= 100), nên chỉ phép kiểm đáy
**TRÊN** hỏng.

⚠️ **Đây đúng lớp lỗi mà chính file ấy đã cảnh báo.** Docstring `_ti_le_truc`
viết: *"khai bằng ĐIỂM `|u| = h` ⇒ `L` đã LÀ tỉ lệ; khai bằng VÔ HƯỚNG
`|u| = 1` ⇒ `L` là KHOẢNG CÁCH tuyệt đối […] Bỏ qua khác biệt ấy thì hình trụ
vẫn đúng — bán kính nó không phụ thuộc vị trí"*. Cảnh báo ấy viết cho đường
**ĐƯỜNG TRÒN**, nơi kết quả không phụ thuộc vị trí dọc trục. Phép **ELIP**
thêm sau lại có một phép kiểm **phụ thuộc vị trí** (elip nằm trọn giữa hai
đáy) và **không áp phép đổi thang**.

### Khoanh vùng

- **Đường tròn đúng ở cả hai nhánh** — `intersect_plane_curved(A/B, z=10)` đều
  cho `radius_sq = 16`. Chỉ phép elip hỏng.
- **Fail-closed** — từ chối oan, **không bao giờ** trả đáp số sai. Đó là hướng
  hỏng đỡ tệ hơn, nhưng nó đóng hoàn toàn một cách khai.
- **Không phải một ca xui**: đo với `h² ∈ {100, 400, 1600, 2500}` — **mọi**
  chiều cao đều bị từ chối. `L > 1` ⇒ `tren < 0`; `L < 1` ⇒ `tren_sq = tren²·1`
  quá nhỏ so với `h_half_sq`. Nhánh vô hướng **không bao giờ** cắt ra elip.

### Hai phát hiện ở ca ⑦, đừng trộn

**(a) `h = 20` khai thẳng, ghim về `tam_day_tren` → grounding từ chối. KHÔNG
phải lỗi.** Đề cho tâm đáy trên là một **ĐIỂM** `(0,0,20)`, không cho một
chiều cao. Grounding hỏi đúng câu *"anh lấy số 20 ở đâu ra"*, và một toạ độ
không phải một độ dài đề cho. Ca ⑦ của brief giả định đề có `height = 20` như
một dữ kiện — với đề này, giả định ấy không đứng.

**(b) Đường height TRUNG THỰC — `h = measure(distance, O, O′)` — mới lộ ra lỗi
thật.** Vô hướng ấy do chương trình **tính**, nên grounding bỏ qua đúng luật;
nó đi tới `execution` rồi chết ở kernel. Đó là đường đo được lỗi.

## 4. Vì sao dừng là đúng, không phải quá cẩn thận (§10)

§10 bắt **chứng minh bằng chữ ký** rằng hình trụ có đường hợp lệ
`radius + height + pose` **trước** khi rút ca — vì chỉ khi ấy mới đọc được việc
mô hình tự bịa `rim_point` là *"lựa chọn của chương trình, không phải yêu cầu
của hệ"*.

**Phép đo bác chính tiền đề ấy** cho phép giao elip. Chạy lượt live với một
tiền đề sai thì mọi kết luận về `rim_point` mất giá trị: nếu mô hình bịa điểm
vành, tôi **không** nói được *"nó đã có đường trực tiếp"* — với phép elip, nó
không có.

Đó đúng lớp lỗi *"bộ đo không nằm trên đường chạy thật"* mà kho này đã trả giá
hai lần (certifier gọi tắt `mo_luot_do_v3`; runner đọc đáp số từ `scene3d` mà
`route` cố ý không dựng).

⚠️ Đường hợp lệ **không-bịa-điểm** cho bài này vẫn còn, và gold dùng nó: **hai
tâm CÓ TÊN (`O`, `O′`) + `radius`**. Nên bài vẫn giải được — thứ mất là **một
trong hai** cách khai, và là cách mà §10 cần để đọc kết quả.

## 5. Replay lịch sử (§5) — 0 lượt gọi

```
RAW_ATTEMPT_1_PLANE_OPERATION  = construct_plane_from_equation (mô hình TỰ đặt)
RAW_ATTEMPT_1_SCHEMA_VALID     = YES
RAW_ATTEMPT_1_STATIC_VALID     = PASS
RAW_ATTEMPT_1_RIM_POINT_FAILURE = YES — grounding, UNANCHORED_DERIVED_ASSUMPTION
RAW_ATTEMPT_1_SERVABLE         = NO
MINIMAL_DELTA_FIELDS           = 2 (bỏ `P_rim`; `rim_point` → `radius: "R"`)
MINIMAL_DELTA_SERVABLE         = YES
MINIMAL_DELTA_EXACT_AREA       = 16π√5
RAW_ATTEMPT_2_GROUNDING_VERDICT = REJECT — UNANCHORED_DERIVED_ASSUMPTION
```

Hai ô giữ phân biệt, không gộp: `RAW_ATTEMPT_1_SERVABLE = NO` ·
`MINIMAL_DELTA_SERVABLE = YES`.

## 6. Không có lượt chạy — mọi ô của §8–§9 là `NOT_REACHED`

```
ANALYZE: BOTTOM_CENTER_O · TOP_CENTER_O_PRIME · RADIUS_4 · HEIGHT_OR_AXIS_20
         PLANE_EQUATION · ELLIPSE_E · AREA_OBLIGATION · CONTAINER_BINDING
         → tất cả NOT_REACHED
CANDIDATE: cả 20 chiều → NOT_REACHED
```

Bảng attempt trống — **không có attempt nào**. Ghi ra để không ai đọc bảng rỗng
thành *"mô hình làm hỏng"*.

```
CANDIDATES_USING_DIRECT_RADIUS   = NOT_REACHED
CANDIDATES_USING_RIM_POINT       = NOT_REACHED
UNGROUNDED_RIM_POINT_FAILURES    = NOT_REACHED
REPAIRS_MOVING_RIM_TO_RADIUS     = NOT_REACHED
CURVED_RIM_POINT_AFFORDANCE      = NOT_REPLICATED (chưa có lượt mới)
```

Giữ nguyên phân loại cũ: quan sát `rim_point` của wave trước vẫn là
**`OBSERVATION`**, `n = 1`.

## 7. Báo cuối (§16)

```
GOLD_PREFLIGHT               = PASS
RUN_VALIDITY                 = KHONG_CHAY (dung truoc provider theo §4)
ANALYZE_CONTRACT             = NOT_REACHED
FIRST_ATTEMPT_SERVABLE       = NOT_REACHED
EVENTUAL_SERVABLE            = NOT_REACHED
EXACT_ANSWER                 = NOT_REACHED
POSTCONDITIONS_PASS          = NOT_REACHED
TRACE_PASS                   = NOT_REACHED
SCENE3D_PASS                 = NOT_REACHED
MODEL_DISCOVERABILITY        = NOT_MEASURED
STABILITY_UNDER_ACCEPTANCE   = NOT_MEASURED

PLANE_FROM_EQUATION_SELECTED_AT_ATTEMPT = NOT_REACHED
ELLIPSE_OPERATOR_SELECTED_AT_ATTEMPT    = NOT_REACHED
DIRECT_RADIUS_CANDIDATES     = NOT_REACHED
RIM_POINT_CANDIDATES         = NOT_REACHED
UNGROUNDED_RIM_POINT_FAILURES = NOT_REACHED
CURVED_RIM_POINT_AFFORDANCE  = NOT_REPLICATED

ANALYZE_CALLS                = 0
INITIAL_SYNTHESIS_CALLS      = 0
REPAIR_CALLS                 = 0
LOGICAL_APPLICATION_CALLS    = 0
PHYSICAL_API_ATTEMPTS        = 0
TRANSPORT_RETRIES            = 0
CANDIDATE_PROGRAM_ATTEMPTS   = 0
TOTAL_TOKENS                 = 0
TOKEN_CEILING                = 40000

CACHE_VERSION_BEFORE/AFTER   = 89 → 89
CANDIDATE_HASH_BEFORE/AFTER  = 422a9e7b… → 422a9e7b…  (KHONG doi)
MODEL_FACING_HASHES_BEFORE/AFTER = ca NAM khong doi mot byte
                               prompts 55ac1ca6 · grammar_card 285292fe ·
                               synthesis_schema 6ccef323 ·
                               analyze_schema 515001b5 · capability 4b1e2f80
PRODUCT_CAPABILITY_CHANGED   = NO
APPLICATION_LLM_CALLS        = 0
TEST_RESULTS = wave 17 pass · pytest 4347 pass, 0 do · replay 5/5 ·
               crash 6/6 nem 0 · certify PASS · cache identity exit 0 @ v89 ·
               freeze --verify exit 0 (91 file) · diff --check sach ·
               frontend KE THUA (khong dung mot dong nao)
COMMITS      = 2
WORKING_TREE = sach
RECOMMENDED_NEXT_ACTION = CURVED_SCALAR_AXIS_SCALE_REPAIR
```

⚠️ **`ELLIPSE_FOUNDATION_SEQUENCE` KHÔNG đóng.**
`CARD_C_CURVED_ELLIPSE_PATH_CONFIRMED` giữ **`NOT_MEASURED`** — điều kiện là
*eventual served* trong một lượt live, và chưa có lượt nào.

## 8. Giới hạn bằng chứng

- **Wave này không nói gì về mô hình.** 0 lượt gọi ⇒ không có dữ liệu theo
  hướng ấy. Nói *"mô hình không làm được"* là nói sai — chưa ai hỏi nó.
- **Blocker là `SYSTEM_GAP`, không phải `HYPOTHESIS`**: tái hiện tất định ở mức
  kernel, hai khối bằng nhau về hình cho hai kết quả khác nhau, bốn chiều cao
  đều hỏng, và đường tròn đối chứng vẫn đúng.
- Nó **fail-closed**: chưa có ca nào cho thấy nó trả đáp số sai. Rủi ro là
  **từ chối oan**, và phạm vi là `intersect_plane_curved_ellipse` khi khối khai
  bằng vô hướng.
- Ca ⑦ của brief giả định đề cho `height = 20` như một dữ kiện; với đề này
  không phải vậy. Hai phát hiện (a)/(b) ở §3 phải đọc rời.

**Việc kế tiếp: `CURVED_SCALAR_AXIS_SCALE_REPAIR`.** Sửa phép đổi thang ở
`intersect_plane_curved_ellipse` để `L` mang cùng nghĩa ở cả hai nhánh — dùng
lại `_ti_le_truc` (thẩm quyền đã có) thay vì viết phép quy đổi thứ hai. Cổng
chống tái phát đã sẵn: `test_10_pv7b…` trong
`tests/geometry/test_oblique_ellipse_e2e_rerun_preflight.py` **tự khai sẽ đỏ
khi lỗi được sửa**, và thông điệp assert của nó nói thẳng phải xoá nó rồi mở
lại lượt live này.

Đáng cân nhắc trong cùng wave ấy, đo được ở đây nhưng **không sửa**:
`height` vắng trong `_TOAN_HANG_LENH` (không kiểm kiểu tĩnh) · vắng trong
`_NGUON_CUA_PHEP_DUNG` (đồ thị phụ thuộc mất mắt xích chiều cao — đúng lập
luận chú thích đã dùng cho `radius`) · vắng trong `O_TEN` (thẻ không nói được
ô ấy là gì).
