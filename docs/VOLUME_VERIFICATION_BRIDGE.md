# VOLUME_VERIFICATION_BRIDGE — đóng khoảng safe-serve của thể tích khối cong

> Thực hiện **2026-09-03**, trên HEAD `2f3db49`, cây sạch lúc bắt đầu.
> **APPLICATION_LLM_CALLS = 0.** Không sửa prompt, không mở năng lực hình học.
> Artifact probe §18 (`curved-ergonomics-probe/`) **không bị viết lại** — số
> `ONE_SHOT_CORRECT = 0` của nó vẫn đúng cho bản hệ đã đo.

## 0. Kết luận trước

```
VOLUME_VERIFICATION_BRIDGE      = CLOSED
DEV_PROBE_BALL_1_SYSTEM_BLOCKER = CLOSED
MEASURE_CHECKER_SUBJECT_DRIFT   = 0   (1 ngoại lệ KHAI TƯỜNG MINH: angle/vector3)
MODEL_FACING_CONTRACT_CHANGED   = NO
APPLICATION_LLM_CALLS           = 0
```

Hai chỗ hỏng, không phải một. Chỗ thứ hai chỉ lộ ra khi viết ca thử **có răng**
cho chỗ thứ nhất — và nếu không viết ca ấy thì wave này đã đóng với một cổng
`volume` nhìn thì xanh mà không bao giờ mâu thuẫn nổi đáp số của đề.

## 1. Nguyên nhân gốc

### ① Lệch đúng một dòng giữa hai thẩm quyền

| nghĩa vụ | `BANG_PHEP_DO` nhận | `check_*` nhận (trước) |
|---|---|---|
| `distance` | line3 · plane3 · point3 | `Vec3` `Line3` `Plane3` |
| `radius` | circle3 · curved_solid | `CurvedSolid` `Circle3` |
| **`volume`** | **curved_solid** · solid | **`Polyhedron` — CHỈ THẾ** |

`CURVED_OBLIGATION_COVERAGE_BRIDGE` nới `volume` sang `curved_solid` ở **cổng
phủ**; `check_volume` không được nới theo. Hệ quả tất định, đo lại được:

```
ball_1   executable True · servable False · stage postconditions
         engine ra {'R': '6', 'V': '288π'}      ← ĐÚNG ĐÁP SỐ
         postcondition_violated: ['cần một `solid`']
```

Hệ tính xong rồi từ chối phục vụ chính con số nó vừa tính.

**Đây là lỗi hậu duệ trực tiếp của `RADIUS_VERIFICATION_BRIDGE`** (cùng ngày,
sớm hơn vài giờ): wave ấy đóng đúng chỗ hụt này cho `radius`, rồi không soát
dòng `volume` mà wave trước đó vừa nới. Sửa hàng đang nhìn, không soát bảng.

### ② `parse_exact` không đọc được π — cổng C₂ fail OPEN

Phát hiện khi ca thử đầu-cuối *"đáp số SAI phải bị bác"* lại **xanh**.

`_MAU_CAN` (văn phạm giá trị mong đợi) cố ý đóng với π, và chú thích nêu rõ tiền
đề của quyết định ấy:

> *"không tập đo nào có đại lượng chứa π — vì chưa phép đo nào sinh ra π
> (`CURVED_TYPES_ADDED = 0`)"*

Tiền đề đó **chết từ Phase 2**. `volume(curved_solid)`, `lateral_area` và
`area(circle3)` sinh π ở mọi ca. Không ai soát lại lời chú thích khi điều kiện
của nó đổi — **đúng một hình lỗi với ①, chỉ khác chỗ đứng.**

Hậu quả: `params["value"]` là ô STRING (`analyze_contract`), nên đáp số mong đợi
của mọi bài khối cong (`288π`, `15π`, `12π`) rơi vào nhánh `Fraction(s)`, ném,
trả `None` — mà `None` ở đây nghĩa là *"không có gì để so"*. Cổng C₂ không thể
mâu thuẫn với đáp số đề, dù nó sai thế nào.

## 2. Bảng sở hữu (§2)

| câu hỏi | chủ sở hữu |
|---|---|
| `MEASURE_SIGNATURE_OWNER` | `semantic_program/measure_contract.py::BANG_PHEP_DO` |
| `CHECKER_REGISTRY_OWNER` | `geometry_obligations.py::GEOMETRY_CHECKERS` → gộp vào `postconditions.CHECKERS` bằng `**GEOMETRY_CHECKERS` |
| `VOLUME_RUNTIME_OWNER` | `geometry_exec.py::_do` (`q == "volume"`) → **`volume_of`** |
| `VOLUME_CHECKER_OWNER` | `geometry_obligations.py::check_volume` |
| `MEASURE_OBLIGATION_MAPPING_OWNER` | `measure_contract.NGHIA_VU_DO` + `kieu_chu_the_nghia_vu()`, nạp vào `obligations.OBLIGATION_KINDS` qua `_nap_nghia_vu_do()` |

## 3. Bản vá

**Không** thêm bảng kiểu nào. `MEASURE_SUBJECT_COMPATIBILITY_AUTHORITIES = 1`
giữ nguyên: `BANG_PHEP_DO` vẫn là chỗ duy nhất trả lời *"chủ thể này có hợp
không"*, và nó **đã đúng từ trước** — chỉ bộ kiểm là chưa theo.

| chỗ | trước | sau |
|---|---|---|
| `geometry_exec.volume_of` | *(không có; điều phối nằm inline trong `_do`)* | cửa chung: `CurvedSolid → CV.the_tich`, còn lại `volume_polyhedron`. Không kiểm kiểu (người gọi kiểm), không phân nhánh theo `ball/cylinder/cone` |
| `check_volume` chủ thể | `isinstance(sol, Polyhedron)` | `isinstance(sol, (Polyhedron, CurvedSolid))` |
| `check_volume` phép tính | `volume_polyhedron(sol)` | `volume_of(sol)` — **cùng cửa với đường chạy** |
| `check_volume` nhân chứng | `Fraction(w)` | `w` (giữ `ExactNumber`) — `Fraction(Radical)` **ném**, nên dòng cũ giết mọi ca cong ngay cả sau khi đã nới kiểu |
| `radical._MAU_CAN` | `[-][k*]sqrt(n)[/m]` | thêm thừa số π tuỳ chọn; phải có ít nhất một trong π/căn, nếu không thì rơi về `Fraction` **y như trước** |

`SHAPE_SPECIFIC_VOLUME_CHECKERS = 0` · `CHECK_VOLUME_FAMILY_DISPATCH = 0` — ba
công thức `4/3·πR³`, `πr²h`, `1/3·πr²h` vẫn thuộc bảng `KHOI_CONG` và **chỉ**
thuộc nó; cả checker lẫn `volume_of` đều không biết hình nào là hình nào (khoá
bằng quét AST, `test_Z4`).

## 4. Bằng chứng — tất định, 0 lượt gọi model

### Ma trận thể tích cong (§10) — `tests/geometry/test_volume_verification.py` (26)

| | hình | dựng | đúng | sai |
|---|---|---|---|---|
| V1/V2 | cầu | `R = 6` | `288π` PASS | `1`, `999π`, `√2` REJECTED |
| V3/V4 | trụ | `r² = 5`, `h = 3` | `15π` PASS | REJECTED |
| V5/V6 | nón | `r² = 9`, `h = 4` | `12π` PASS | REJECTED |

Trụ cố ý lấy `r = √5` **vô tỉ** với toạ độ vẫn hữu tỉ — ca mà bộ chấm dùng float
sẽ nói dối. `test_V2b` đặt trụ và nón **cùng `r², h`** cạnh nhau: chúng lệch đúng
hệ số 3, và một checker *"miễn ra được một con số π"* sẽ nuốt cả hai.

### Hồi quy đa diện (§9)

`box(2,3,5)` → `V = 30` PASS · `31` REJECTED · không khai giá trị ⇒ mức yếu
(`None`), **không** phải PASS giả · chủ thể sai kiểu vẫn bị bác.

### Nhân chứng safe-serve (§8)

```
DEV_PROBE_BALL_1_REPLAY     chương trình + RequestContract lấy NGUYÊN VĂN
                            từ curved-ergonomics-probe/stage_8a_one_shot.json
TRƯỚC   executable True · servable False · postconditions · 'cần một `solid`'
SAU     executable True · servable True  · stage_reached served · weak_kinds []
        final_memory ⊇ {R: 6, V: 288π}
```

Cả **hai** nghĩa vụ (`radius`, `volume`) đi qua đúng cổng của chúng, và
`test_A2` chạy riêng `volume` để không lẫn công của `radius`.

⚠️ `test_A3` là vế răng của nhân chứng ấy: đổi `A` cho `R = 3`, giữ nguyên đáp
số đề `288π` → phải mất `servable`. **Chính ca này phơi ra lỗi ②** — nó xanh khi
đáng lẽ phải đỏ, vì `parse_exact("288π")` trả `None`.

> Bài học lặp lại lần thứ ba trong ba wave: *nhân chứng phải đi ĐÚNG đường sản
> phẩm với ĐÚNG bộ nghĩa vụ.* `RADIUS_VERIFICATION_BRIDGE::test_T6` khai
> `V1_BALL_CLEAN_ROUTE PASS · R = 6 · V = 288π` trong khi chỉ truyền nghĩa vụ
> `radius`; `288π` là số đọc từ `final_memory`, **chưa bao giờ** đi qua
> `check_volume`. Dòng ấy đọc như một lượt kiểm đầu-cuối cho thể tích. Nó không
> phải.

### Cổng chống trôi (§11–§12) — `test_measure_checker_subject_drift.py` (12)

Bất biến: *với mọi nghĩa vụ ĐO có checker server-owned, đường kiểm chứng phải
nhận mọi kiểu chủ thể mà `BANG_PHEP_DO` cho phép* — trừ ngoại lệ khai tường minh.

**KHÔNG** khẳng định *"mọi lượng đo phải có checker"*: `area`/`lateral_area` cố ý
chưa có, và ép chúng có là đẻ ra nghĩa vụ giả (§13).

Đo "nhận" bằng cách đưa nhân chứng **cố tình sai** rồi đòi đúng lời *"giá trị
không khớp"*: chỉ khi đã tính lại được đại lượng từ hình thì checker mới nói được
câu đó. Từ chối kiểu, hay ném vì không tính nổi, đều không phải câu đó — và đây
là chỗ một cổng ngây thơ sẽ xanh giả, vì với nghĩa vụ **không khai giá trị** thì
phần lớn checker trả `None` kể cả khi chủ thể sai kiểu.

`DRIFT_GUARD_RED_TEST` — cổng đỏ trong **năm** kiểu tiêm, không chỉ ca vừa vá:

| mũi tiêm | kết quả |
|---|---|
| `volume` + `circle3` | ĐỎ |
| `radius` + `solid` | ĐỎ |
| `distance` + `curved_solid` | ĐỎ |
| kiểu lạ chưa có mẫu (`hinh_xuyen`) | ĐỎ — *"KHÔNG CÓ MẪU"*, không phải lối thoát im lặng |
| **dựng lại `check_volume` bản CŨ** | ĐỎ, gọi đúng tên `volume/curved_solid` |

Mũi cuối là mũi thuyết phục nhất: cổng bắt được **đúng con bug đã sinh ra nó**,
nguyên hình dạng đã làm `ball_1` mất `servable`. Gỡ tiêm ⇒ xanh lại
(`test_cong_XANH_LAI_sau_khi_go_tiem`) — một cổng đỏ vĩnh viễn cũng vô dụng như
một cổng không bao giờ đỏ.

## 5. Ngoại lệ đã khai: `angle` / `vector3` — CHƯA ĐÓNG

Cổng tìm ra **một chỗ trôi thứ ba**, có sẵn từ trước, và wave này **cố ý không
vá**:

`angle` hiện thực hoá bởi HAI lượng đo — `angle_cos_sq` (line3|plane3, trả cos²)
và `angle_cos` (vector3, trả cos **có dấu**). `check_angle` chỉ tính lại cos²,
nên nó không kiểm được nhân chứng của `angle_cos`; ô giá trị mong đợi của nghĩa
vụ cũng chỉ có `cos_sq`.

Đóng khoảng này đòi một quyết định **ngữ nghĩa** (nghĩa vụ `angle` trỏ lượng đo
nào; đáp số có dấu viết vào đâu), không phải một phép nới kiểu — nên nó là một
wave riêng, không phải việc tiện tay của wave này (§13).

Ngoại lệ được khai ở `NGOAI_LE` kèm lý do, và **chỉ được ngắn đi**:
`test_ngoai_le_van_CON_THAT` khẳng định nó vẫn là chỗ trôi thật (vá xong mà quên
xoá dòng ⇒ ĐỎ), `test_ngoai_le_khong_duoc_phinh_ra` đóng băng danh sách ở đúng
một mục. Cùng cơ chế `KNOWN_GAPS` của `code-index-sync.test.ts`.

## 6. Danh tính (§16–§18)

| | trước | sau |
|---|---|---|
| `prompts` | `55ac1ca6a6df92ce…` | **không đổi** |
| `grammar_card` | `2463652cd8d328ad…` | **không đổi** |
| `synthesis_schema` | `421e7aff8557dc17…` | **không đổi** |
| `analyze_schema` | `a4d5ed7c65a68007…` | **không đổi** |
| `semantic_environment_hash` | `a4aa4d6eefa3e9a1…` | **không đổi** |
| `stable_capability_hash` | `024799b84cf528db…` | **KHÔNG ĐỔI** — xem dưới |
| `CACHE_VERSION` | `70` | **`71`** |
| candidate (mã sản phẩm) | `4d8bfb51692b7b84…` 89 file | `5debcf75ba49dd6e` 89 file |

`MODEL_FACING_CONTRACT_CHANGED = NO`, xác nhận bằng máy — bốn vân tay khớp
byte-đối-byte với môi trường ghi trong artifact probe §18.

### ⚠️ `CAPABILITY_HASH_CHANGED = NO` — và đó là một lỗ, đã audit (§17)

Đo, không ép. `capability_fingerprint()` băm hai thứ liên quan:

- `nghia_vu` = `sorted(GEOMETRY_CHECKERS)` — **tên** checker. Wave này không
  thêm checker nào, nên không đổi.
- `nghia_vu_chu_the` = `OBLIGATION_KINDS` — kiểu chủ thể **cổng phủ cho phép**.
  Đã đúng từ `CURVED_OBLIGATION_COVERAGE_BRIDGE`, nên không đổi.

Thứ wave này đổi là **thứ ba**: *kiểu chủ thể mà checker thật sự KIỂM ĐƯỢC*. Nó
không nằm trong danh tính năng lực. Hệ quả đo được: hai container — một cái có
lỗi `ball_1`, một cái không — cho **cùng một `stable_capability_hash`**, nên
`runtime_doctor` không phân biệt nổi chúng.

Đây đúng loại lỗ mà `nghia_vu_chu_the` được thêm vào để bịt, chỉ sâu hơn một
tầng. **Không vá trong wave này**: cách biểu diễn "ngữ nghĩa kiểm chứng" trong
một băm ổn định là một quyết định thiết kế riêng (băm mã nguồn thì báo động giả
mỗi lần sửa chú thích — mà kho này đã ghi rõ *"báo động giả là cách nhanh nhất
để một cổng bị tắt"*). Xếp vào `NEXT_ACTION`.

### `CACHE_VERSION 70 → 71` — bắt buộc, theo đúng tiền lệ 69

Cache lưu **envelope đầy đủ**, khoá theo *text đã chuẩn hoá + `CACHE_VERSION`*.
Bump 69 (`check_radius`) ghi nguyên văn tình huống này cho `radius`; đây là cùng
tình huống cho `volume`: envelope đã cache cho đề hỏi thể tích khối cong mang
`servable=False`, trong khi hệ hiện tại kiểm chứng được và phục vụ được. Trả lại
envelope cũ là nói với học sinh rằng hệ không dám phát một đáp số nó đã kiểm
xong. Lỗi ② cộng thêm một lý do: envelope cũ sinh dưới một cổng C₂ fail-open.

Bump ở đủ **bốn** chỗ: `main.py` · `test_api.py` · `CURRENT_STATE.md` ·
`test_evaluation_candidate.py` (qua manifest), cộng `cache_identity.lock.json`.

## 7. Hồi quy (§20) — cây sạch, 0 API call

| cổng | kết quả |
|---|---|
| pytest | **3106 pass**, 1 skip, 1 deselect |
| vitest | **687 pass / 50 file** |
| `tsc -b && vite build` | PASS |
| `replay_demo_cases.py` | **DEMO_REPLAY 5/5** · **REDUCED_CHAIN 1/1** |
| `audit_demo_crash_surface.py` | **6/6 biên đúng kiểu**, ném ra ngoài **0** |
| `freeze_evaluation_candidate.py --verify` | PASS |
| R0 / grounding | không đụng; điểm bịa vẫn bị bác trước verification (`test_T10`) · `CURVED_GEOMETRY_LAUNDERING = 0` |
| `radius` | không đụng ngữ nghĩa; circle3 · curved_solid · bán kính vô tỉ đều PASS (`test_Z2`) |

Một test đổi theo kiến trúc, **mạnh thêm chứ không nới**:
`test_geometry_wave2::test_MOT_nguon_su_that_cho_the_tich` trước đòi
`check_volume` gọi `volume_polyhedron`; nay đòi **cả hai đường** đi qua
`volume_of`, **và** chỉ `volume_of` được chạm `the_tich`/`volume_polyhedron`.

## 8. Việc kế tiếp

```
NEXT_ACTION = ACCEPTANCE_RUNNER_INTEGRITY
```

Kèm hai món nợ wave này khai ra và cố ý không trả:

1. **`angle`/`vector3`** — chỗ trôi thứ ba, đã khai ở `NGOAI_LE` (§5).
2. **Danh tính năng lực chưa phủ ngữ nghĩa kiểm chứng** (§6) — `runtime_doctor`
   hiện không phân biệt được container có lỗi `ball_1` với container đã vá.

⚠️ `CURVED_SYNTHESIS_ERGONOMICS = PARTIAL` **không đổi**, và V3 vẫn **chưa được
chạy**. Wave này đóng lỗi HỆ đã chặn V3; nó không nói gì về ecgônômi tổng hợp.
Số của probe §18 giữ nguyên: `ONE_SHOT_CORRECT = 0`, `FINAL_CORRECT = 0`,
16 lượt gọi model — **không hồi tố**.
