# SCALAR_FACT_VISIBILITY — đóng một cổng KHÔNG THOẢ MÃN ĐƯỢC

> Thực hiện **2026-09-04**, trên HEAD `b567cba`, cây sạch.
> **APPLICATION_LLM_CALLS = 0.** Không đổi prompt, thẻ văn phạm, lược đồ, IR,
> kernel, checker, taxonomy nghĩa vụ.

## 0. Kết luận trước

```
SCALAR_FACT_VISIBILITY        = CLOSED
BALL_1_LEARNER_SURFACE        = PASS  ·  BALL_1_SERVABLE = TRUE
GENERAL_SCALAR_FACT_TESTS     = PASS  (24 ca, có ca KHÔNG dính hình cong)
VISUAL_BINDINGS_MODEL_OWNED   = NO    (và thẻ hình học vẫn KHÔNG phơi trường ấy)
SCALAR_FAKE_3D_OBJECTS        = 0
R0_POLICY_CHANGED             = NO
MODEL_FACING_CONTRACT_CHANGED = NO
CACHE_VERSION                 71 → 72
STABLE_CAPABILITY_HASH        không đổi
```

## 1. Nguyên nhân gốc

`learner_surface` luật (2) đòi **mọi khai báo có `source_fact_id` phải nhìn thấy
được**. Nhìn thấy được = có `visual_bindings` **hoặc** có mặt trên cảnh 3D.

Trong miền hình học cả ba lối đều bị bịt:

| lối | vì sao bịt |
|---|---|
| khai `visual_bindings` | thẻ hình học **cấm**: *"Cảnh 3D dựng TỰ ĐỘNG… không khai gì thêm để hiển thị"* |
| biết tên trường ấy | `grammar_card("hinh_hoc")` **không phơi** `visual_bindings` |
| lên cảnh như **đại lượng** | interpreter nạp `initial_value` **nguyên văn** ⇒ `IA = 6` là `str "6"`, mà `la_dai_luong_do` chỉ nhận `Fraction \| Radical` |

Đo cả bốn dạng:

| giá trị trong bộ nhớ | `la_dai_luong_do(·, "float")` |
|---|---|
| `str "6"` (thực tế) | **False** |
| `int 6` | **False** |
| `float 6.0` | **False** |
| `Fraction(6)` | True |

⇒ **Không một dữ kiện đề vô hướng nào** qua được cổng, bất kể mô hình viết gì.
Và cổng nằm **ngoài vòng sửa**, nên mô hình không bao giờ được biết.

`SCALAR_VALUE_REPRESENTATION_BEFORE` = `str "6"` ·
`SCALAR_VALUE_REPRESENTATION_AFTER` = `Fraction(6, 1)`.

## 2. Chọn thiết kế — chứng minh từ mã, không từ sở thích

Đề bài nêu hai thiết kế. Bằng chứng quyết định nằm ở
`simulation_state.build_scene:337`:

```python
if not la_dai_luong_do(gt, kieu.get(ten)):
    continue                      # ← KHÔNG lên cảnh
tho.append((ten, "quantity", _dai_luong(gt)))
```

**Hai người đọc dùng CHUNG một vị từ**: cổng và cảnh. Nghĩa là cổng **đang nói
thật** — giá trị ấy thật sự không có trên cảnh.

⇒ Thiết kế **B (dạy `learner_surface` đọc chuỗi thô) là SAI**: nó cho cổng xanh
trong khi `build_scene` vẫn bỏ qua, tức một cổng **fail-open**, và học sinh vẫn
không thấy dữ kiện. Đó đúng hình lỗi mà `la_doi_tuong_hinh_hoc` viết ra để tránh:
*"cổng bảo 'có trên hình', cảnh thì không vẽ"*.

⇒ Chọn **A**: chuẩn hoá MỘT lần ở biên nạp bộ nhớ. Hai người đọc vốn đã chung
một vị từ nay cùng thấy sự thật; không ai phải học cách diễn giải lại chuỗi thô.

| | |
|---|---|
| `SCALAR_NORMALIZATION_OWNER` | `geometry_exec.chuan_hoa_dai_luong` — cạnh chính `la_dai_luong_do` và `KIEU_DAI_LUONG` |
| `LEARNER_SURFACE_VISIBILITY_OWNER` | không đổi: `learner_surface` + `la_dai_luong_do` |
| người gọi | `interpreter._reset`, đúng biên mà kiểu hình học đi qua `build_initial` |

## 3. Ba ranh giới, và một ranh giới thứ tư phải trả giá mới tìm ra

**① Kiểu KHAI không đổi** (§5). Đây là chuẩn hoá *biểu diễn runtime*;
`decl.type` vẫn `float`. Cùng nguyên tắc `point3` ↔ `vector3` — một `Vec3` ở
runtime, hai kiểu khai.

**② Không nới văn phạm** (§4). Dùng đúng `parse_exact` đang có, không viết bộ
đọc số thứ hai. `"6"`, `"3/2"`, `"-7/3"` đọc được vì hôm nay nó đã đọc được.

**③ Đọc không được thì GIỮ NGUYÊN — fail closed** (§12). `"abc"` nằm im dưới
dạng chuỗi, vẫn vô hình, cổng vẫn từ chối. Ép nó thành `0` là biến *"không đọc
được"* thành một con số.

**④ CHỈ MIỀN HÌNH HỌC** — ranh giới này tôi **không** thấy trước, và bản đầu
làm 14 ca Tin học đỏ:

```
INDEX_OUT_OF_RANGE: chars[Fraction(0, 1)] ngoài [0, 5)
```

`KIEU_DAI_LUONG` là `("float", "int")` và IR **dùng chung** với miền Tin học,
nơi một `int` là **chỉ số** hoặc **biến đếm**. Một chỉ số hữu tỉ không phải một
chỉ số. Toàn bộ lý do bản vá tồn tại — `la_dai_luong_do`, `build_scene` chiếu ra
`quantity` — thuộc miền hình học, nên phạm vi của nó cũng phải đúng miền ấy.
Cờ `mien_hinh_hoc` dẫn từ *"spec có khai kiểu hình học nào không"*, quyết một
lần cho cả chương trình.

## 4. Bằng chứng — `tests/geometry/test_scalar_fact_visibility.py` (24 ca)

### `ball_1`, đi trọn đường sản phẩm

```
TRƯỚC   executable True · postconditions_pass True · R = 6 · V = 288π
        learner_surface: 'IA_dist_val' mang dữ liệu đề … không có binding
        servable FALSE
SAU     stage_reached = served · servable TRUE · R = 6 · V = 288π
```

Chương trình và hợp đồng lấy **nguyên văn** từ artifact `curved-ergonomics-v2-run2`;
artifact không bị sửa, đây là một lượt chấm lại tất định.

### Cổng hồi quy KHÔNG dính hình cong (§20)

`test_S0` dùng **hai điểm và một khoảng cách** — không khối cầu, không mặt cong.
Chứng minh nó đỏ dưới hành vi trước wave bằng cách vô hiệu hoá bản vá:

```
bản vá bị vô hiệu → executable True · servable FALSE
                    learner_surface_incomplete: 'AB_len' … không có binding
```

Nếu bản vá chỉ cứu khối cầu thì nó là một miếng vá, không phải một bản sửa.

### Ma trận

| | ca | kết quả |
|---|---|---|
| S1/S2 | `IA=6` · `R=13` · `h=8` · `a=2` · `3/2` · `-7/3` | PASS, thành `Fraction` |
| S2b | kiểu khai `int` | PASS |
| S3 | `ball_1` trọn đường | PASS · `served` |
| S4 | **tứ diện vuông** cạnh `a = 2`, `V = 4/3` | PASS — không dính hình cong |
| S5 | vô hướng nội bộ (được TÍNH RA) | không bị luật (2) đòi |
| S5b | `chuan_hoa_dai_luong` mức đơn vị, gồm cả `mien_hinh_hoc=False` | PASS |
| S6 | `"abc"` · `""` · `"2x"` · `"6.5.1"` | **bị từ chối**, vẫn là `str` |
| S6b | `True`/`False` không bị nuốt thành số | PASS |
| S7 | nhãn hiển thị ≠ `AB_len_raw_id` | PASS |
| S8 | không ca nào cần `visual_bindings`; thẻ vẫn không phơi nó | PASS |
| S9 | vô hướng lên cảnh là `type="quantity"`, **không** `xyz`/`vertices`/`faces` | PASS |
| S10 | điểm bịa vẫn bị R0 bác; `source_fact_id` trỏ mục không tồn tại cũng bị bác | PASS |

⚠️ **Một quan sát, không phải thiếu sót:** biến thể `initial_value = "6"` viết
dạng chuỗi **không** ground được — cổng grounding chuẩn hoá giá trị của khai báo
nhưng không chuẩn hoá giá trị của mục dữ kiện. Hành vi ấy **có trước** wave này
(grounding đọc `spec`, không đọc bộ nhớ) và nằm ngoài phạm vi. Ghi lại để lần
sau không ai tưởng bản vá gây ra.

### `RAW_ID_LEAK`

Vô hướng lên cảnh với `label = "Đại lượng đo"`, `type = "quantity"` — **không**
rò `IA_dist_val`. Quan sát kèm: nhãn ấy là nhãn CHUNG, chưa mang nghĩa của mục
dữ kiện (*"Khoảng cách IA"*). Đưa nhãn nguồn vào là việc của thẩm quyền hiển
thị, **không** làm trong wave này.

## 5. Danh tính (§17–§19)

| | trước | sau |
|---|---|---|
| `prompts` · `grammar_card` · `synthesis_schema` · `analyze_schema` | — | **không đổi** |
| `stable_capability_hash` | `5b61b9ea76d0c764…` | **không đổi** |
| `semantic_environment_hash` | `36be94cf2258e116…` | **không đổi** |
| `CACHE_VERSION` | `71` | **`72`** |
| candidate (mã sản phẩm) | `4897280e9fc3a9fd` | đóng băng lại |

`MODEL_FACING_CONTRACT_CHANGED = NO` · `CHECKER_SEMANTICS_CHANGED = NO` ·
`GEOMETRY_SEMANTICS_CHANGED = NO`. Không thêm phép IR, hàm kernel hay checker.

**Vì sao capability hash KHÔNG đổi mà cache VẪN bump:** năng lực hình học không
đổi một phép nào — `capability_fingerprint` băm chữ ký phép dựng/đo, kiểu chủ
thể cổng phủ và kiểu chứng thực được, cả ba giữ nguyên. Nhưng **phán quyết sản
phẩm** đổi: envelope đã cache mang `servable=False` cho đề mà hệ nay phục vụ
được. Đúng tiền lệ 69 và 71. Cổng khoá cache **đã đỏ** trước khi làm mới, đúng
quy trình (`test_khoa_gan_dung_CACHE_VERSION_voi_moi_truong_sinh`).

## 6. Đồng hành: bộ đo (§16) — **KHÔNG làm trong wave này**

```
SCHEMA_FAILURE_RAW_CANDIDATE_PERSISTED = NO
```

Lỗ đã biết: chương trình hỏng lược đồ không được lưu, nên với lớp lỗi phổ biến
nhất ta chỉ có thông điệp lỗi chứ không có văn bản mô hình thật sự viết.

Kiểm bằng máy: văn bản thô nằm trong biến cục bộ `raw` của
`pipeline._sinh_chuong_trinh`; observer chỉ nhận `message=loi`. Runner **không
có** đường lấy nó. Sửa được thì phải thêm dữ liệu vào kênh observer trong
`app/ai/pipeline.py` — tức mã sản phẩm, tức trộn một thay đổi quan trắc vào một
wave đổi hành vi và làm bẩn diff của candidate.

Theo đúng điều khoản thoát của §16 (*"nếu làm nó nới phạm vi sản phẩm thì để
wave riêng"*): **để wave riêng.**

## 7. Hồi quy — 0 API call

| cổng | kết quả |
|---|---|
| pytest | **3193 pass**, 1 skip, 1 deselect |
| vitest | **687 pass / 50 file** |
| `tsc -b && vite build` | PASS |
| `replay_demo_cases.py` | **DEMO_REPLAY 5/5** · **REDUCED_CHAIN 1/1** |
| `certify_acceptance_runner.py` | **RUNNER_CERTIFICATION PASS** |
| `freeze_evaluation_candidate.py --verify` | PASS |
| `lock_cache_identity.py --verify` | PASS |
| hình cong / phủ / radius / volume | không đụng, xanh |

## 8. Việc kế tiếp

```
NEXT_ACTION = REPAIR_FRAGMENT_COMPLETENESS
```

`manh_hop_dong` gửi cho `cylinder_2` danh sách CÂU LỆNH mà bỏ hẳn mục biểu thức
— che mất chỗ `intersect_plane_curved` thật sự sống, nên chín lượt sửa cứu 0 ca
(`AUDIT_SYNTHESIS_BOTTLENECK §4`). Kèm theo, nếu muốn: lưu văn bản thô của lượt
hỏng lược đồ (§6).

⚠️ V3 vẫn **chưa chạy**, pool giữ niêm phong, seed chưa rút.
`CURVED_SYNTHESIS_ERGONOMICS = NO_MEASURABLE_GAIN` không đổi — wave này sửa một
lỗ HỆ, không nói gì về ecgônômi tổng hợp.
