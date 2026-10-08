# FRAME_ORIGIN_PROVENANCE_AFFORDANCE

> 2026-09-07. **`APPLICATION_LLM_CALLS = 0`** — phần live **dừng theo luật
> §2**: replay tất định tìm ra một lỗ kiểm chứng nghiêm trọng hơn câu hỏi
> affordance mà wave định đo.
>
> ```
> Replay: kênh xuất xứ ĐÃ ĐỦ, không cần trường mới
> Replay: nhưng ĐỘ DÀI đề cho KHÔNG được kiểm ⇒ served 396/5 thay vì 8
> CACHE_VERSION 83 → 84 (BUMP)   CANDIDATE 179793db… → a9289410…
> ```

## 1. Trạng thái đầu — khớp bàn giao

HEAD `ec5c802` · cây **sạch** · `CACHE_VERSION` **83** · candidate
`179793db…` (`--verify` exit 0, 90 file) · `PRODUCT_VARIANT` **A**
(`grammar_card` == `card_A.txt`, `c7c001c4…`).

Sáu băm model-facing @ v83: `prompts 55ac1ca6…` · `grammar_card e0fbbc84…` ·
`synthesis_schema 8c57c9de…` · `analyze_schema 515001b5…` ·
`capability 85bd3167…` · `semantic_environment f7def620…`.

**Ba mức bằng chứng, tách rõ trước khi đo:**

| | |
|---|---|
| **quan sát** | cả bốn candidate của lượt trước thiếu provenance ở gốc toạ độ |
| **giả thuyết** | một hướng dẫn ngắn sẽ giúp AI khai đúng |
| **cần chứng minh** | **trường nào** thực sự đủ để grounding chấp nhận một lựa chọn hệ trục hợp lệ |

## 2. Replay tất định — và nó đổi hướng cả wave

`docs/evaluation/geometry/frame-origin-provenance-affordance/REPLAY_DELTA.json`
(4 raw candidate nguyên văn, `sha256` nguồn ghi trong artifact).

Delta tối thiểu tại **mọi** khai báo `point3` có `initial_value` mà thiếu cả
hai trường xuất xứ; gỡ từng trường để xác định cái nào cần:

| candidate | thiếu xuất xứ | ① nguyên văn | ② **chỉ** `model_assumption` | ③ **chỉ** `source_fact_id` | ④ cả hai |
|---|---|---|---|---|---|
| RATIO/ratioB | `C` | grounding | **served · 6** · scene 4 | **served · 6** | served · 6 |
| MULTIPLE/ratioB | `E` | grounding | **served · 8** · scene 4 | **served · 8** | served · 8 |
| MULTIPLE/ratioA | `E` | grounding | `source_invariant` · `15/2` | `source_invariant` | `source_invariant` |
| RATIO/ratioA | `C`, `D` | grounding | grounding | grounding | grounding |

> **KẾT LUẬN ①.** **Một trường là đủ** — `model_assumption` **hoặc**
> `source_fact_id`. Hợp đồng hiện tại **không thiếu gì**; không cần mở trường
> mới. Kênh giả thiết đi qua năm chốt của `grounding_gate` (có lý do · đúng
> kiểu · không phải witness · tên **có trong đề** · **không** phải tên đề giới
> thiệu như hệ quả), và một gốc toạ độ hợp lệ qua đủ cả năm.

**Ba trong bốn khớp kỳ vọng của brief.** Ca thứ tư lệch, và báo đúng như đo
được: **`RATIO/ratioA` thiếu xuất xứ ở HAI khai báo** (`C` *và* `D`), cộng một
khai báo **`float`** `ratio_CN` có `initial_value` mà thiếu `source_fact_id` —
kênh giả thiết chỉ nhận `point3`/`vector3`, nên nó không cứu được, và **đúng
như thế**: một `float` mang giá trị suy ra thì phải truy về đề. Ca ấy vì vậy
vẫn dừng ở `grounding` sau mọi delta.

⚠️ Đính chính bàn giao: câu *"cả bốn candidate thiếu provenance ở gốc toạ độ"*
đúng nhưng **chưa đủ** — một candidate thiếu ở nhiều hơn một chỗ.

### 2b. Phản ví dụ — và điều kiện dừng đã kích hoạt

| | phản ví dụ | trước wave |
|---|---|---|
| **ⓐ** | `model_assumption` gắn vào **điểm phải dựng ra** (`P`), khai thẳng toạ độ, **bỏ câu lệnh dựng** | **`served`**, đáp số **đúng** (`8`) |
| **ⓑ** | toạ độ **trái dữ kiện**: `F = [99,0,0]` cho đề `EF = 10`, kèm `model_assumption` hợp lệ | **`served`** với **`396/5`** thay vì `8` |

**ⓑ là một đáp số SAI được phục vụ im lặng** — lớp lỗi nặng nhất của kho này.
Theo §2 (*"nếu replay phát hiện lỗ kiểm chứng mới, kết thúc phần live với 0
lượt gọi"*), **phần A/B live không chạy**. `APPLICATION_LLM_CALLS = 0`.

## 3. Vì sao ⓑ lọt, và phạm vi sửa tối thiểu

| tầng | có hỏi câu này không |
|---|---|
| `segment_division` | **không** — nó kiểm **tỉ lệ** `t`, và `t = 1/5` vẫn đúng |
| `model_assumption` | **không** — nó là kênh hợp lệ cho *cách đặt* hình |
| `segment_length` | **CÓ** — và checker **đã tồn tại, chạy đúng**, so bình phương bằng `Fraction` |

Lỗ nằm ở **bộ phát**, không ở checker: bộ phát duy nhất của `segment_length`
là `scale_normalization.bat_bien_nguon`, chỉ chạy trên đường **chuẩn hoá
thang** — tức chỉ khi đề viết `AB = a` bằng **ký hiệu**. Đề cho **số** thì
không ai phát bất biến nào.

Đây đúng bệnh mà `check_source_invariants` sinh ra để chữa (*"hình đúng về
quan hệ, sai về THANG"*, `wave6-canary-b`); lần này nó lọt vì thiếu bộ phát.

**Sửa:** thêm `segment_relation.bat_bien_do_dai`, dùng lại **chính**
`_do_dai_doan` đã có trong module, phát ở **cùng biên**
`build_request_contract`. Không `kind` mới, không checker mới, không trường mới.

Hai chốt hẹp:
- **khử trùng với đường thang** — `chuan_hoa_thang` viết lại giá trị fact về
  `1`, mà `_van_ban` ghép nhãn với giá trị, nên `"AB" + "1"` cho ra `AB = 1` và
  tầng này sẽ phát bản thứ hai. Không sai về toán, nhưng nó **nhân đôi mẫu số
  telemetry** và làm hai tầng cùng nhận một trách nhiệm (`test_B5`);
- **hai độ dài mâu thuẫn cho cùng một đoạn ⇒ KHÔNG phát** (`test_B6`).

## 4. Kiểm chứng

`backend/tests/geometry/test_frame_origin_provenance.py` — **15 pass**, 0 lượt gọi.

| nhóm | nội dung |
|---|---|
| `A1`–`A4` | không khai gì ⇒ grounding bác · **chỉ** `model_assumption` là đủ · **chỉ** `source_fact_id` cũng đủ · **không cần trường mới** |
| `B1`–`B2` | phát bất biến độ dài cho đề cho số · **ⓑ nay bị bác** ở `source_invariant` |
| `B3` | **phép tiêm**: gỡ bộ phát ⇒ ⓑ **`served` trở lại** với `396/5` |
| `B4`–`B6` | độ dài đúng không bị cản · không phát trùng với đường thang · mâu thuẫn ⇒ không phát |
| `C1`–`C2` | **lỗ còn lại**, ghi bằng test ĐANG XANH (xem §6) |

**Regression:** `r1`–`r4` giữ nguyên; `r1` nay còn **mạnh hơn** (thêm
`|AB| = 12` và `|AM| = 9` bên cạnh `segment_division`). Toàn bộ suite
**3976 pass**, không test cũ nào vỡ ngoài một cái đổi kỳ vọng có chủ đích:

⚠️ `test_G_so_cu_the_khong_sinh_bat_bien` → `test_G_so_cu_the_khong_can_CHUAN_HOA_THANG`.
Nửa `scale_binding is None` **giữ nguyên**; nửa `source_invariants == ()` hết
đúng — câu ấy đúng **vì kiến trúc khi đó chỉ có một bộ phát**, không phải vì
có ai quyết rằng độ dài bằng số thì không đáng kiểm.

## 5. Identity, cache, candidate

**`MODEL_FACING_DELTA = NONE`** — sáu băm **byte-identical**, chỉ version lệch;
`lock_cache_identity.py` tự xác nhận *"môi trường không đổi"*.

**`CACHE_DECISION = 83 → 84, BUMP`** — cùng loại `81→82` và `82→83`. Chiều đổi
là `served → từ chối`, mà `served` **là** thứ được cache. Đo bằng **row thật**
trước khi bump: envelope `{"do_dai_pf": "396/5"}` ghi ở `policy_version 83`
vẫn **HIT** và được trả về nguyên vẹn, **không đi qua cổng mới**.

**`CANDIDATE_BEFORE_AFTER = 179793db… → a9289410…`** (90 file, verify exit 0).
`PRODUCT_VARIANT` **A → A**. `PRODUCT_CAPABILITY_CHANGED = NO`.

## 6. Lỗ còn lại — khai thẳng, có test đang xanh

**ⓐ chưa đóng.** Đề giới thiệu `P` như một điểm **phải dựng ra** (*"Điểm P nằm
trên đoạn EF sao cho FP = 4·PE"*), nhưng `source_entities.nhan_suy_ra` chỉ
nhận hai lối nói — `"gọi/lấy X là …"` và `"X là trung điểm|hình chiếu|giao
điểm|trọng tâm|chân đường|tâm|điểm đối xứng"`. Dạng *"nằm trên … sao cho"*
không khớp cái nào, nên **chốt ⑥ của `grounding_gate` không bắt được**.

Hệ quả đo được (`test_C1`): chương trình khai thẳng toạ độ `P`, **bỏ câu lệnh
dựng**, còn đúng **một** câu lệnh, và vẫn **`served`** với đáp số **đúng** —
vì bất biến `segment_division` xác nhận vị trí. **Thứ mất không phải đáp số mà
là BƯỚC DỰNG**, đúng thứ chốt ⑥ sinh ra để giữ, và đúng thứ đề tài hứa cho
học sinh (*"engine tất định thực thi từng bước"*).

Không sửa trong wave này: nó thuộc **thẩm quyền khác**
(`source_entities.nhan_suy_ra`), và nới nhận diện tên-suy-ra có rủi ro **bác
oan** — phải có phản ví dụ hai chiều và đo riêng. `test_C1` xanh nghĩa là lỗ
**vẫn còn**; wave sau đóng nó thì test ấy ĐỎ, và đỏ là đúng.

`test_C2` ghi sẵn đường sửa: **bộ neo của `segment_relation` đã nhận đúng lối
nói mà `nhan_suy_ra` thiếu** — dùng lại tín hiệu ấy, không dựng thẩm quyền
thứ ba.

## 7. Cổng đã chạy

| cổng | kết quả | mới / kế thừa |
|---|---|---|
| test wave | **15 pass**, 1 phép tiêm | **mới** |
| `test_source_invariant_gate` | **21 pass** (1 đổi kỳ vọng có chủ đích) | **mới** |
| test quan hệ chia đoạn | **63 pass** | **mới** |
| `pytest -q` (cây cuối) | **3976 pass**, 1 skip, 1 deselect, **0 đỏ** | **mới** |
| `test_api` · `test_cache_identity` · `test_current_state_identity` | **37 pass** | **mới** |
| `replay_demo_cases.py` | **5/5**, `REDUCED_CHAIN 1/1` | **mới** |
| `audit_demo_crash_surface.py` | **6/6 biên**, ném **0** | **mới** |
| `certify_acceptance_runner.py` | **PASS**, 0 lượt gọi | **mới** |
| `freeze_evaluation_candidate --verify` | **exit 0**, 90 file | **mới** |
| `git diff --check` | sạch | **mới** |
| vitest · `npm run build` | — | **kế thừa** (frontend không đụng) |

## 8. Báo cuối

```
REPLAY_PROVENANCE_FIELD_REQUIRED = MOT trong hai la DU
                       (`model_assumption` HOAC `source_fact_id`);
                       KHONG can truong moi, hop dong hien tai da du
P0_P1_GROUNDING_PASS   = KHONG DO — phan live dung theo luat §2
P0_P1_RATIO_CORRECT    = KHONG DO
P0_P1_SERVED_DUNG      = KHONG DO
TOKEN_MOI_ARM          = KHONG DO
TOKEN_TREN_MO_PHONG_DUNG = KHONG DO
LOGICAL_CALLS / PHYSICAL_CALLS = 0 / 0
APPLICATION_LLM_CALLS  = 0

LO_DA_DONG (ⓑ)        = toa do TRAI du kien: `F = [99,0,0]` cho de `EF = 10`
                         TRUOC: served, PF = 396/5 (dap so SAI, im lang)
                         SAU  : bac o `source_invariant`,
                                NORMALIZED_SOURCE_VIOLATED
LO_CON_LAI (ⓐ)        = diem PHAI DUNG RA van khai thang toa do duoc va bo
                         cau lenh dung; dap so dung, BUOC DUNG mat.
                         Goc: `nhan_suy_ra` khong nhan loi noi
                         "nam tren … sao cho". Test C1 dang XANH = lo con.

MA_THAY_DOI            = segment_relation.bat_bien_do_dai (moi) ·
                         analyze_contract hook (+1 dong) ·
                         test_source_invariant_gate test_G (doi ky vong)
MODEL_FACING_DELTA     = NONE (6 bam byte-identical)
CACHE_VERSION          = 83 → 84 (BUMP, do bang row that)
CANDIDATE              = 179793db… → a9289410…
PRODUCT_VARIANT        = A → A        PRODUCT_CAPABILITY_CHANGED = NO
WORKING_TREE           = sach         COMMITS = 2
TOKEN_EFFICIENCY       = NOT_MEASURED
RECOMMENDED_NEXT_ACTION = DERIVED_POINT_CONSTRUCTION_ENFORCEMENT
```

**Giới hạn bằng chứng.** Replay là tất định và mạnh cho câu *"trường nào đủ"* —
nó gỡ từng trường và đo. Nhưng câu **"AI có tự khai đúng không"** vẫn
**chưa đo**: wave này không gọi model lần nào, nên giả thuyết ở §1 vẫn là giả
thuyết. Bốn lượt live đã đăng ký **chưa dùng**, và nền đo nay vững hơn trước.

**Việc kế tiếp: `DERIVED_POINT_CONSTRUCTION_ENFORCEMENT`.** Chọn từ kết quả
thực tế — nó là lỗ **duy nhất** wave này tìm ra mà chưa đóng, nó chạm thẳng
luận điểm của đề tài (bước dựng phải do engine làm, không được làm sẵn ngoài
màn hình), và đường sửa đã có sẵn tín hiệu trong kho (`test_C2`). Đóng nó
xong mới quay lại bốn lượt A/B affordance — khi ấy `served` mới có nghĩa là
*"dựng đúng bằng các bước dựng"*, chứ không chỉ *"ra đúng số"*.

⚠️ Token của Claude Code **không** tính vào token vận hành AlgoSim; replay,
checker và Scene3D không dùng token Gemini.
