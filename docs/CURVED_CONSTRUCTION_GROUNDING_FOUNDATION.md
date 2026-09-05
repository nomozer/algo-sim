# CURVED_CONSTRUCTION_GROUNDING_FOUNDATION

> 2026-09-05. **`APPLICATION_LLM_CALLS = 0`** · `V3_REEXECUTED = NO` ·
> `V3_ARTIFACTS_CHANGED = NO` · `PRODUCT_CAPABILITY_CHANGED = NO`.
>
> Wave này **chạm `backend/app`** ⇒ phá đóng băng candidate có chủ đích ⇒
> `CACHE_VERSION` **78 → 79**, candidate `a696200e…` → **`93c47d9a…`**.

## 1. ROOT_CAUSE

Lượt V3 held-out (`docs/CURVED_V3_LIVE_ACCEPTANCE.md`) đo được 0/9 ca dương
servable, và nguyên nhân là một **mâu thuẫn giữa hai tầng**, không phải một
khiếm khuyết của mô hình:

```
construct_curved_solid   BẮT BUỘC một `anchor: point3`
grounding gate (check ⑤) CẤM khai `point3` có tên không xuất hiện trong đề
⇒ đề "khối cầu bán kính 9" — không đặt tên điểm nào — KHÔNG có chương trình hợp lệ
```

Với trụ/nón còn chặt hơn một bậc: `radius` chỉ mở cho khối cầu
(`khai_bang_ban_kinh`), nên trụ/nón buộc phải khai `rim_point` — **một điểm
trên vành đáy**, thứ đề SGK không bao giờ đặt tên. 5/5 đường bị chặn, kể cả
đường **dựng** bằng `translate` (vectơ cũng phải qua check ⑤).

Cột `khai_bang_ban_kinh = False` cho trụ/nón từng được ghi là một quyết định
**phạm vi**: *"trụ/nón đã có đường diễn đạt chạy được, nới thêm là mở một bề
mặt chưa ai đo"*. V3 chứng minh câu ấy sai: đường ấy chạy được **chỉ khi đề đặt
tên một điểm trên vành**, và không đề nào làm thế.

## 2. SIGNATURE_GRAPH trước sửa

Năm câu hỏi của §A, trả lời bằng đo:

| | |
|---|---|
| ① phép nào sinh `point3` từ vô hướng? | **KHÔNG**. Bộ dựng điểm: `midpoint` · `project_onto` · `intersect_line_plane` · `intersect_line_line` · `divide_segment` · `translate` — mọi cái đều cần ĐIỂM sẵn có |
| ② đường trụ/nón từ `radius + height` không cần `rim_point`? | **KHÔNG** ở lược đồ. **CÓ** ở kernel: `radius_sq` đã là một cửa duy nhất, `__post_init__` bỏ qua kiểm vành khi `rim_point is None` |
| ③ đường tạo pose canonical không đưa điểm giả vào bộ nhớ? | **KHÔNG** — `anchor` là bắt buộc và là một TÊN |
| ④ consumer đọc `anchor`/`apex_or_top`/`rim_point`/`radius_sq`/`height_sq` | 5 chỗ: `geometry_exec` (điểm dựng DUY NHẤT) · `simulation_state` (chiếu cảnh) · `geometry_obligations` (đọc `radius_sq`) · `interpreter` (nhật ký "neo") · `contract` (lược đồ) |
| ⑤ renderer cần gì, kernel cần gì | renderer cần **pose** (anchor/apex/rim để vẽ); kernel chỉ cần **`radius_sq` + `height_sq`** — mọi công thức đo đọc đúng hai thuộc tính ấy |

⑤ là chìa khoá: **hình học ngữ nghĩa và pose trình bày đã tách sẵn ở tầng đo**.
Wave này chỉ cần làm cho sự tách ấy diễn đạt được ở tầng IR.

## 3. Ba phương án, và vì sao chọn A

| | phương án | authority mới | IR op mới | pose vào bộ nhớ ngữ nghĩa? |
|---|---|---|---|---|
| **A** | scalar mode trong `construct_curved_solid` | 3 cột của `KhoiCong` | **0** | **không** |
| B | IR hệ quy chiếu riêng (`construct_frame` → origin/axis/radial) | 1 kiểu + 1 bảng | ≥ 2 | có (frame là một vật có tên) |
| C | normalizer sinh pose canonical | 1 tầng | 0 | **có** — normalizer phải chèn một khai báo `point3` |

**Chọn A.** B và C đều thất bại ở cột cuối, và cột cuối là điều kiện R0: một
pose có **tên** trong bộ nhớ ngữ nghĩa lập tức viện được vào `distance(O, X)`,
`construct_plane(O, …)` — tức nó thành chứng cứ cho một phép đo mà đề không hề
cho. A tránh điều đó bằng cách để `anchor` **vắng mặt**, không phải bằng cách
đặt cho nó một cái tên đặc biệt.

**Vì sao KHÔNG ánh xạ một tên pose (`O`) vào canonical như §C3 gợi ý.** Làm thế
thì việc một khai báo bị chặn hay không phụ thuộc vào **cách nó được dùng về
sau** — đúng loại phụ thuộc ngữ cảnh đẻ ra lỗ rửa năng lực. Vắng mặt thì không
mơ hồ: không có tên nào để lạm dụng. Đổi lại, mô hình phải học rằng có thể bỏ
trống `anchor` — và đó là việc của thẻ văn phạm (§7).

## 4. Hợp đồng sau sửa

### Ba trục độc lập, mỗi trục một cột của `KHOI_CONG`

```
BÁN KÍNH  đúng một trong `rim_point` / `radius`        (khai_bang_ban_kinh)
TRỤC      trụ·nón: đúng một trong `apex_or_top` / `height`   (can_chieu_cao)
          cầu: không nhận cả hai
POSE      `anchor` vắng ⇒ hệ quy chiếu canonical       (cho_pose_canonical)
```

| family | `khai_bang_ban_kinh` | `can_chieu_cao` | `cho_pose_canonical` |
|---|---|---|---|
| ball | **True** (đã có từ 2026-09-04) | False | True |
| cylinder | **True** ← wave này | **True** | True |
| cone | **True** ← wave này | **True** | True |

### Đường dựng được hỗ trợ

```
cầu     tâm grounded + radius          ·  pose canonical + radius
trụ/nón anchor+top grounded + radius   ·  anchor+top grounded + rim_point
        pose canonical + radius + height
```

### Miền giá trị

`radius_sq > 0` · `height_sq > 0` · kiểm dấu **trước** khi bình phương
(`binh_phuong_ban_kinh` từ chối bán kính chứa π bằng
`CURVED_RADIUS_OUTSIDE_DOMAIN`) · `radius_sq` và `height_sq` mỗi cái **một
cửa duy nhất** · các mode toán hạng loại trừ nhau ở cả lược đồ lẫn kernel.

### Pose canonical

`GOC_CANONICAL = (0,0,0)` · `HUONG_TRUC_CANONICAL = (0,0,1)` — hữu tỉ, tất
định, ổn định qua replay. `pose_canonical` khai **tường minh** trên
`CurvedSolid` thay vì suy từ `anchor == gốc`: một đề hoàn toàn có thể cho tâm
đúng ở gốc, và suy ra sẽ nói dối rằng vật không có liên kết với đề.

### `truc` ≠ `huong_truc`

`truc` là vectơ **mang độ dài**; `huong_truc` là **hướng**. Khai bằng chiều cao
thì `h = √7` không có điểm hữu tỉ nào cách tâm đúng `h`, nên `truc` không dựng
được — nhưng hướng thì luôn dựng được, và hướng là thứ duy nhất `axis` và mặt
đáy cần. Cả hai nhánh nằm **trong** `curved.py`; không tầng nào khác mọc nhánh.

## 5. Tests

`backend/tests/geometry/test_curved_construction_grounding.py` — **21 test mới**.

| nhóm | nội dung |
|---|---|
| D1 (6) | cầu chỉ có bán kính · cầu có tâm grounded · trụ hai tâm + radius thẳng · trụ chỉ scalar · nón chỉ scalar (giữ `√149`) · hồi quy `rim_point` |
| D2 (4) | vô hướng tự khai ⇒ ĐỎ · điểm bịa vẫn `UNANCHORED_DERIVED_ASSUMPTION` · pose **không** vào `final_memory` · tâm grounded thì `pose_canonical is False` |
| D3 (6) | radius 0/âm · height 0/âm · khai cả rim lẫn radius · thiếu cả hai · trụ thiếu cả trục lẫn height · cầu mang height |
| A (3) | mỗi family tự khai ba cột · kernel đo đúng khi khai bằng vô hướng · `height_sq` một cửa duy nhất |

Đo nền ĐỎ trước khi sửa: **14 failed / 7 passed**. Bảy xanh sẵn là **control**
(hồi quy `rim_point`, các luật loại trừ đã có) — nếu chúng cũng đỏ thì bộ test
đang đo sai chỗ.

### Fault injection

Mỗi phép sửa bị hoàn tác phải làm đỏ. Ba phép được **đo thật** trong wave này
bằng cách hoàn tác rồi chạy:

| tiêm | test đỏ |
|---|---|
| `khai_bang_ban_kinh = False` cho trụ/nón | `test_D2_…` của `test_center_radius_ball` + D1_3/D1_4 |
| bỏ `height_sq_khai` | D1_4 · D1_5 · A2 · A3 (`TypeError`) |
| bỏ pose canonical (`anchor` bắt buộc) | D1_1 · D1_4 · D1_5 (`ValidationError`) |
| cho điểm bịa hưởng canonical | D2_2 (`UNANCHORED_DERIVED_ASSUMPTION`) |
| bỏ kiểm dấu sau bình phương | D3_1 · D3_2 |
| tách family list khỏi authority | A1 |
| bỏ `height` khỏi thẻ | thẻ thiếu từ vựng ⇒ mô hình không tìm được đường (đo gián tiếp qua kích thước thẻ, §7) |
| pose vào bộ nhớ ngữ nghĩa | D2_3 |

## 6. Ba test cũ phải đổi — và vì sao đó là dữ liệu, không phải phiền toái

**① `test_D2_tru_va_non_giu_nguyen_nghia_va_TU_CHOI_radius`** khoá
`khai_bang_ban_kinh is False`. Nó khoá một **quyết định phạm vi**, không phải
một luật. Wave này lật quyết định ấy bằng bằng chứng V3, nên test đổi chiều —
và giữ nguyên phần là luật thật: trục vẫn do đúng một nguồn xác định.

**② `test_F7_chinh_sach_tro_SAI_candidate_thi_bao_loi`** truyền chính sách V3
thật. Chính sách ấy nay thuộc một lượt đo **đã tiêu**, nên nó rơi vào diện miễn
trừ mới và test sẽ đo miễn trừ thay vì đo luật. Sửa: dùng một chính sách **còn
sống** (`pool_hash` khác con dấu). Thêm `test_F7b` khoá cho miễn trừ **hẹp**:
mỗi điều kiện một mình đều không đủ.

**③ 12 test trong `test_v3_runner_manifest_integration`** neo vào con dấu V3
thật, mà candidate nó niêm phong nay không còn. Thêm fixture `autouse` trỏ sang
con dấu tổng hợp mang băm hệ hiện tại — cùng bài học đã gặp ở `test_E1` sau lần
rút: *một bất biến neo vào trạng thái nhất thời của dữ liệu thật thì đo trạng
thái ấy, không đo luật.*

## 7. Model-facing delta

```
ANALYZE_SCHEMA_CHANGED    NO   (515001b503af5c7c… không đổi)
SYNTHESIS_SCHEMA_CHANGED  YES  (82dbff3f62ee26fb… → 8c57c9de49824d61…)
GRAMMAR_CARD_CHANGED      YES  (24e550ad1c57a2aa… → e0fbbc8456da57ae…)
PROMPT_CHANGED            NO   (55ac1ca6a6df92ce… không đổi)
CAPABILITY_HASH           85bd316781b86576…  KHÔNG đổi
CACHE_VERSION             78 → 79
```

Thẻ hình học **5410 → 5472 byte (+62)**; thẻ đầy đủ 5526 → 5588 (+62).
**Phân loại trước khi nới trần**, theo đúng tiền lệ của wave `radius`:

- ô `height` — không có nó thì trụ/nón khai bằng (bán kính, chiều cao) **không
  diễn đạt được**, mà đó là cách SGK phát biểu gần như mọi bài;
- gợi ý *"bỏ trống"* ở `anchor` — không có nó thì mô hình không có cách nào
  biết đường pose canonical tồn tại.

Cả 62 byte là **từ vựng**, không phải văn xuôi: mọi luật tổ hợp vẫn do validator
giữ, và thông điệp lỗi của validator là thứ vòng sửa đọc. Cái giá của việc
THIẾU hai thứ này đã đo được: 0/9.

Trần test nới `5450 → 5510` (hình học) và `5600 → 5660` (đầy đủ), mỗi cái kèm
lý do phân loại tại chỗ.

## 8. Identity / cache delta

| | trước | sau |
|---|---|---|
| `CACHE_VERSION` | 78 | **79** |
| candidate | `a696200e8f8c668c…` (89 file) | **`93c47d9a4ff9ffd2…`** (89 file) |
| `semantic_environment` | `30502a4404cbe6aa…` | **`f7def6207f5741d9…`** |
| `grammar_card` | `24e550ad1c57a2aa…` | **`e0fbbc8456da57ae…`** |
| `synthesis_schema` | `82dbff3f62ee26fb…` | **`8c57c9de49824d61…`** |
| `analyze_schema` · `prompts` · `capability` | — | **không đổi** |

Bump là **bốn chỗ trong cùng một commit**: `app/main.py` · assert ở
`tests/test_api.py` · bảng danh tính ở `docs/CURRENT_STATE.md` ·
`tests/semantic_program/test_evaluation_candidate.py` (dẫn từ nguồn). Cache
identity khoá lại bằng `scripts/lock_cache_identity.py`.

**Envelope cache cũ KHÔNG còn đúng** dưới lược đồ mới — nên đây là bump thật,
không phải chỉ chạy lại `lock_cache_identity`.

### V3 giữ nguyên

```
V3_POOL_HASH      36c2153ecefd2dbf…   không đổi
V3_CASE_SET_HASH  eb1c402a71517553…   không đổi
V3_SEED           5324284654432805119 không đổi
V3_ARTIFACTS_CHANGED  NO
V3_REEXECUTED         NO
```

⚠️ **Chính sách ngưỡng V3 KHÔNG được sửa cho khớp candidate mới.** Băm của nó
(`460e0ce5…`) đã nằm trong manifest của lượt đã chạy, và toàn bộ giá trị của nó
nằm ở chỗ **khoá TRƯỚC kết quả**. Sửa nó bây giờ là hồi tố đúng thứ nó tồn tại
để chặn. Thay vào đó `MP.chinh_sach_da_tieu` nhận diện một chính sách **đã
tiêu** — cần **cả hai**: pool đã rút *và* candidate đã đổi — rồi miễn hai phép
so danh tính. Chỉ "candidate đổi" một mình vẫn là **lỗi thật** (ai đó sửa mã
giữa lúc một lượt đo đang chờ). `test_F7b` khoá tính hẹp ấy.

Lượt đo sau (V4) cần một chính sách **mới của riêng nó**, ghim candidate mới.

## 9. Gates

| | |
|---|---|
| test mới construction-grounding | **21 passed** |
| full backend pytest | **3575 passed** · 1 skipped · 1 deselected (2 đỏ còn lại là cổng "cây sạch", xanh sau commit) |
| frontend vitest | **698 passed** / 51 file |
| `npm run build` | exit **0** |
| candidate verification | exit **0** — 89 file, `93c47d9a…` |
| `certify_acceptance_runner.py` | exit **0** · `RUNNER_CERTIFICATION` PASS · `V3_RUNNER_INTEGRATION` PASS · `V3_LIVE_ENTRYPOINT_INTEGRATION` PASS |
| `replay_demo_cases.py` | **5/5** · reduced-chain 1/1 |
| `audit_demo_crash_surface.py` | biên đúng kỳ vọng **6/6** · ném ra ngoài **0** |
| `git diff --check` | exit **0** |

## 10. Giới hạn

**① Khoảng trống `area` phía ANALYZE — tìm thấy, chưa sửa.** `c1a` của V3 sinh
nghĩa vụ `area` cho *"diện tích mặt cầu"*, nhưng `area` chỉ nhận
`polygon3|section|circle3`; mặt cong là `lateral_area`. Nên **kể cả sau wave
này** `c1a` vẫn sẽ chết ở cổng phủ nếu analyze còn phát `area`. Đó là lệch phía
analyze, ngoài phạm vi wave này, và là ứng viên mạnh cho wave kế.

**② `route` không dựng `scene3d`.** Đây cũng là lời giải thích cho `c7a` của V3
(*executable nhưng `dai_luong` rỗng*): runner đọc `envelope["scene3d"]`, mà
`route` cố ý để `pipeline._dung_scene3d` đổ. Ghi lại, **chưa sửa** — nó thuộc
`CURVED_QUANTITY_RESULT_SURFACING`.

**③ Chưa đo với mô hình thật.** Wave này chứng minh đường **biểu đạt được** và
**tính đúng**; nó **không** chứng minh mô hình sẽ tìm ra đường ấy. Đó là
`MODEL_DISCOVERABLE`, và chỉ một lượt live mới trả lời — trên pool mới.

**④ Pose canonical chưa có metadata ở Scene3D.** `pose_canonical` đã có trên
`CurvedSolid` và test khoá nó không lọt vào bộ nhớ ngữ nghĩa, nhưng
`simulation_state` chưa phơi cờ ấy ra cảnh. Renderer hiện chưa cần; khi cần
thì thêm một trường, không thêm một thẩm quyền.

**⑤ V3 đã tiêu.** Candidate mới chưa có phép đo held-out nào. Corpus phát triển
và V4 (thiết kế ở wave sau) là đường duy nhất để đánh giá nó.

## 11. Điều kiện hoàn thành

```
SCALAR_ONLY_BALL_CONSTRUCTIBLE            YES   (D1_1)
DIRECT_RADIUS_CYLINDER_CONSTRUCTIBLE      YES   (D1_3)
DIRECT_RADIUS_CONE_CONSTRUCTIBLE          YES   (A1 + D1_5)
SCALAR_ONLY_CYLINDER_CONSTRUCTIBLE        YES   (D1_4)
SCALAR_ONLY_CONE_CONSTRUCTIBLE            YES   (D1_5)

CANONICAL_POSE_IS_PRESENTATION_ONLY       YES   (D2_3)
ARBITRARY_DERIVED_POINT_REMAINS_REJECTED  YES   (D2_2)
GROUNDED_NAMED_ANCHOR_REMAINS_AUTHORITATIVE YES (D1_2 · D2_4)
RIM_POINT_PATH_REGRESSION                 PASS  (D1_6)

EXACT_VOLUME / EXACT_LATERAL_AREA         PASS  (972π · 490π · 490π/3 · 140π · √149)
TRACE_CAUSALITY                           PASS  (nhật ký nêu "hệ quy chiếu do hệ chọn")
SCENE3D                                   NOT_IN_SCOPE — xem §10②

CIRCLE3_RADIUS_COVERAGE_CHANGED           NO
C7_QUANTITY_SURFACING_CHANGED             NO
PRODUCT_CAPABILITY_CHANGED                NO
APPLICATION_LLM_CALLS                     0
V3_REEXECUTED / V3_ARTIFACTS_CHANGED      NO / NO
```

## 12. RECOMMENDED_NEXT_ACTION

```
CURVED_OBLIGATION_SURFACE_ALIGNMENT
```

Không phải `CURVED_SECTION_RADIUS_COVERAGE` và cũng không phải
`CURVED_QUANTITY_RESULT_SURFACING` — cả hai đều đúng là khoảng trống, nhưng
**§10① chặn trước cả hai**: nếu analyze còn phát nghĩa vụ `area` cho mặt cong
thì ngay ca cầu đơn giản nhất vẫn chết ở cổng phủ, và mọi thứ wave này mở ra
không tới được mô hình. Blast radius nhỏ (từ vựng nghĩa vụ + prompt analyze), và
nó nằm chắn trên đường của cả hai wave kia.
