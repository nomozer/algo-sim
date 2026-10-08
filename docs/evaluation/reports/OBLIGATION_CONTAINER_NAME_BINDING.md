# OBLIGATION_CONTAINER_NAME_BINDING

> 2026-09-06. **`APPLICATION_LLM_CALLS = 0`** — toàn bộ bằng chứng là replay
> tất định, phép tiêm và phản ví dụ. Không mở năng lực toán học, không đổi
> kernel, không đổi bề mặt mô hình.
>
> Fixture là chương trình **mô hình thật sự sinh** trong lượt A/B
> `ab-v1-20260905T164514Z` (arm B), trích nguyên văn từ `raw_candidate` sang
> `docs/evaluation/geometry/obligation-container-binding/` — artifact A/B gốc
> **không đổi một byte**. Sản phẩm giữ baseline **A**.

## 0. Kết quả một dòng

Nghĩa vụ nay nối được với vật ngay cả khi đề gọi nó bằng **nhãn** còn chương
trình gọi nó bằng **tên mô tả** — nối bằng **xuất xứ dữ kiện**, không bằng
chính tả. Giả thuyết bàn giao *"container không phải định danh"* **bị bác**.

## 1. Giả thuyết bị bác, trước khi nói nguyên nhân

Bàn giao nghi dấu ngoặc trong `container` là nguyên nhân. Artifact bác ngay:

| ca | container | tên trong chương trình | kết quả |
|---|---|---|---|
| `e5` | `(j)` | `(j)` — chép thẳng nhãn | **served** |
| `e1` | `(u)` | `u` | **served** |
| `e4` | `(t)` | `duong_tron_t` | **bác ở coverage** |

`(j)` cũng có dấu ngoặc và ca ấy đi trọn. Dấu ngoặc không phân biệt được
thành công với thất bại, nên nó không phải nguyên nhân.
Khoá bằng `test_A2_gia_thuyet_container_khong_phai_dinh_danh_BI_BAC`.

## 2. ROOT_CAUSE — đo bằng máy, không suy luận

Ba ca trên đi qua **ba đường khác nhau**, và chỉ một đường trong đó là thiết kế:

```
e5  trúng thẳng      `(j)` có trong `declared`            → không cần lưới
e1  lưới ③           ten_loi('(u)') == ten_loi('u') == 'u'
e4  KHÔNG lưới nào   ten_loi('duong_tron_t') == 'tront'
```

`ten_loi` gỡ phụ tố kiểu `duong_` rồi dán phần còn lại: `tron` + `t` → `tront`.
`geometry_symbol_key('(t)')` trả `None` vì dấu ngoặc trượt mẫu ký hiệu. Net ⓪
(`_theo_witness_do`) **không chạy được**: nó đòi `container` phải CÓ MẶT trong
chương trình với kiểu sai, mà `(t)` vắng mặt hẳn.

> **ROOT_CAUSE.** Khi `obligation.container` là **nhãn đề đặt cho một vật dẫn
> xuất** và vật ấy vắng mặt khỏi chương trình dưới cái tên đó, việc nối nghĩa
> vụ với vật rơi **hoàn toàn** vào ba lưới CHÍNH TẢ. Không tầng nào hỏi câu
> đúng — *"chương trình có tự khai rằng nó dựng đúng cái vật đề đặt tên ấy
> không"*. `e1` qua được là **may rủi chính tả**, không phải năng lực.

Nguyên nhân ấy độc lập với bản vá, nên nó được khoá riêng:
`test_A1_ba_luoi_chinh_ta_deu_truot_tren_e4`.

### 2b. Lỗ thứ hai, tìm thấy khi đi tìm bằng chứng

Lời khai nối được hai bên **có tồn tại** — mô hình tự viết, dù lược đồ không mời:

```
assign duong_tron_t = intersect_plane_curved(non, mat_phang_cat)
source_fact_id = 'mat_phang_cat_non_theo_duong_tron_t'
   └─ dữ kiện ấy: "Mặt phẳng cắt hình nón theo đường tròn (t)"   ← đúng container
```

`AssignStmt` không có ô `source_fact_id`, Pydantic mặc định `extra="ignore"`,
nên lời khai **biến mất không dấu vết**. Đây đúng lớp lỗi mà
`POINT_INITIALIZATION_CONTRACT_ALIGNMENT` vừa đóng cho ô `at` hai ngày trước:
dữ liệu có nghĩa đặt vào ô hệ không công nhận thì hệ bỏ im lặng.

Khác một điểm quyết định: ở `at`, luật chọn **từ chối chứ không quy đổi**, vì
quy đổi toạ độ không bảo toàn xuất xứ. Ở đây ô ấy **chính là** xuất xứ, nên
chở nó về đúng chỗ là bảo toàn.

## 3. BINDING_AUTHORITY — sửa ở đâu, và vì sao không sửa chỗ khác

| câu hỏi | chủ sở hữu | trước | sau |
|---|---|---|---|
| lời khai xuất xứ ở câu lệnh đi đâu | *không ai* — bị vứt | — | `SemanticProgramSpec._nang_xuat_xu_cau_lenh` |
| nghĩa vụ nói về vật nào (tên CÓ, sai kiểu) | net ⓪ `_theo_witness_do` | có | **không đổi** |
| nghĩa vụ nói về vật nào (tên VẮNG MẶT) | ba lưới chính tả | chỉ chính tả | + net ⓪b `_theo_xuat_xu_du_kien` |
| witness đo vật nào, đúng kiểu không | ba bản lọc chép tay | 1 bản | `_ung_vien_theo_witness`, **dùng chung** |
| dữ kiện có nêu tên container không | — | — | `_xuat_xu_neu_ten` |

Không bảng thứ hai nào được dựng. Phép nâng đặt **ngay cạnh**
`_nang_declare_point` và dùng đúng luật của nó (*chỉ điền chỗ trống*); bộ lọc
witness của net ⓪ được **rút ra dùng chung** thay vì chép sang net ⓪b — hai bản
chép sẽ trôi khỏi nhau, đúng lớp lỗi `_producers`/`_phu_thuoc` đã trả giá.

### Bốn danh tính vẫn tách bạch

`target_var` (tên ngữ nghĩa mô hình đặt) · `obligation.container` (nhãn hợp
đồng mượn từ đề) · `label` (nhãn hiển thị, **không** tham gia nối, giữ nguyên
doctrine cũ) · **xuất xứ** (`source_fact_id` — mới được giữ lại). Net ⓪b đọc
danh tính thứ tư, không đọc ba cái kia.

### Net ⓪b hẹp đến đâu

| điều kiện | chặn cái gì |
|---|---|
| chỉ chạy khi cổng **sẽ bác** | không chương trình nào đang qua bị đổi phán quyết |
| chỉ chạy khi `container` **VẮNG MẶT** | tên đã có chủ là địa hạt net ⓪; không cướp danh tính đã đúng |
| chạy **SAU** ba lưới chính tả | `e1` vẫn nối bằng lưới ③, byte-đối-byte |
| witness đo đúng `ob.kind`, chủ thể đúng kiểu, phép đo **một toán hạng** | dùng chung bộ lọc net ⓪ |
| dữ kiện được viện phải **nêu đúng tên** container | phản ví dụ `hinh_lang_tru`/`chop` |
| khớp tên theo **token trọn vẹn**, không `in` | `(t)` không khớp `(t2)` |
| nhiều chủ thể có bằng chứng ⇒ `RANG_BUOC_MO_HO` | hệ không chọn hộ |

## 4. Đối chiếu e1 / e5 / e4 — trước và sau

| ca | trước | sau | lưới | đáp số |
|---|---|---|---|---|
| `e1` | served, lưới ③ | **served, lưới ③** | *phụ tố kiểu* — không đổi | `ban_kinh_u = 5` |
| `e5` | served, không lưới | **served, không lưới** | — | `ban_kinh_j = 40` |
| `e4` | `THIEU_KHAI_BAO` ở coverage | **coverage PASS**, dừng ở `execution` | *xuất xứ dữ kiện* | xem §5 |

`e1` và `e5` **không đổi một chút nào** — đó là điều kiện của thiết kế, không
phải may mắn: net ⓪b đứng cuối nên nó chỉ nói khi ba lưới kia im lặng.

## 5. E4 — bản vá gỡ tấm che, và thứ nằm dưới tấm che

`E4_ORIGINAL_CONTRACT_REPLAY`: hợp đồng **nguyên văn**, chương trình **nguyên
văn** ⇒ cổng phủ nay PASS, rồi ca dừng ở `execution`:

```
CURVED_PLANE_DOES_NOT_CUT: hình nón: mặt phẳng cắt trục NGOÀI khối
```

Đây **không phải** hồi quy — nó là khiếm khuyết **thứ hai**, của **mô hình**,
độc lập hẳn với việc nối tên, và trước đây bị cổng phủ che:

`divide_segment(a, b, ratio)` là `a + ratio·(b−a)`, tức `ratio` là **tham số
`t`**. Đề cho `PT = 20`, `PQ = 28` ⇒ `t = 20/28 = 5/7`. Mô hình viết `5/2` —
quy ước *"chia đoạn theo tỉ số 5:2"*. Với `5/2` thì `T = (0,0,−42)`, nằm ngoài
khối, và kernel bác **đúng**.

Sửa **đúng một token** trên hợp đồng nguyên văn, qua đúng đường sản phẩm:

```
ratio 5/2 → execution   CURVED_PLANE_DOES_NOT_CUT
ratio 5/7 → served      ban_kinh_t = 15        ← 21·(20/28)
```

`E4_EXACT_RADIUS = 15`, kernel tính lại từ **hình**, không tin số chương trình
khai. Và delta ấy **một mình không cứu được ca**: tắt net ⓪b rồi sửa `ratio`
thì vẫn bác ở `structural_coverage` (`test_B2b`). Hai nguyên nhân, tách bạch.

⚠️ Cùng lớp với khiếm khuyết đã ghi cho `c9b` ở
`CURVED_SECTION_RADIUS_PATH_ADJUDICATION` (*"`ratio 9/6` là `t`, đúng phải
`3/5`"*) — ở đó cổng phủ cũng che lỗi thứ hai. Đây là lần **tái hiện thứ hai**
của cùng một hiểu nhầm, nên nó là việc kế tiếp (§9).

## 6. Ca âm, phép tiêm, và cái gì chứng minh cái gì

`backend/tests/geometry/test_obligation_container_binding.py` — **27 test**,
**nền đỏ 11/27** (đo bằng cách lùi hai file mã về `69c76f0`, chạy chính bản
test cuối), **11 phép tiêm / phản ví dụ**, 0 lượt gọi model.

| test | tiêm gì | phải xảy ra |
|---|---|---|
| `A3` | monkeypatch `_xuat_xu_neu_ten → False` | e4 bác lại **đúng** `THIEU_KHAI_BAO` như artifact |
| `B2b` | tắt net ⓪b, chỉ sửa `ratio` | vẫn bác ở coverage — tách bạch hai nguyên nhân |
| `D2` | witness đo **nhầm** đường tròn | không nối, `ten_da_hoa_giai` rỗng |
| `D3` | vật viện **dữ kiện khác** | `THIEU_KHAI_BAO` |
| `D4` | gỡ hẳn xuất xứ | bác |
| `D5` | hai vật cùng viện một dữ kiện, cùng witness | `RANG_BUOC_MO_HO` |
| `E1` | container `hinh_lang_tru` — không dữ kiện nào nêu | bác (phản ví dụ gốc của net ⓪) |
| `E3` | witness đo `area`, nghĩa vụ hỏi `radius` | không nối |
| `E4` | witness đo `radius` trên một ĐIỂM | không nối |
| `I3` | khai báo đã có xuất xứ | **không** bị đè |
| `I4` | `assign` vào tên chưa khai | không đẻ khai báo mới |

**`AMBIGUOUS_BINDING_HANDLED = YES`** (`D5`) ·
**`WRONG_SUBJECT_WITNESS_REJECTED = YES`** (`D2`).

Phân biệt hai vật cùng kiểu (`D1`): thêm một đường tròn thứ hai cắt ở cao độ
khác, `(t)` vẫn trỏ đúng `duong_tron_t`. Nếu phép nối chỉ dựa vào *"có đúng
một vật đúng kiểu"* thì test này đỏ.

Ý nghĩa giữ nguyên ⇒ kết quả giữ nguyên (`H1`, `H2`): đổi tên nhất quán
`duong_tron_t → c_1` (xa nhãn `(t)` hơn nữa) và đảo thứ tự khai báo đều vẫn
`served` với `15`.

## 7. MULTI_OBLIGATION_ISOLATION và COVERAGE_POSTCONDITION_PARITY

`F1`: `radius((t))` và `volume(non)` cùng một chương trình ⇒ mỗi nghĩa vụ giữ
chủ thể của nó; `ten_da_hoa_giai == {"(t)": "duong_tron_t"}` (không rò sang
`non`), và cả hai đáp số đúng: `ban_kinh_t = 15`, `the_tich = 4116π`.
Bí danh rò sang nghĩa vụ anh em là lỗi `c7a` đã trả giá một lần.

`G1`: `check_postconditions` dùng lại **chính** `ten_da_hoa_giai` mà C₁a phát —
một thẩm quyền, hai consumer, không có bản phân giải thứ hai. `radius((t))` có
mặt trong cả `constraints_checked` lẫn `constraints_verified`.
`G2`: gỡ bằng chứng thì bác ở C₁a và **không** có đường vòng nào để C₂ chấm hộ.

**`MULTI_OBLIGATION_ISOLATION = YES` · `COVERAGE_POSTCONDITION_PARITY = YES`.**

## 8. Identity, cache, phạm vi — đo, không đoán

**`MODEL_FACING_DELTA = NONE`.** Đây là ràng buộc *thiết kế*, không phải kết
quả tình cờ. Bản triển khai đầu tiên thêm ô `source_fact_id` vào `AssignStmt`;
nó làm đỏ 9 test, trong đó có `test_AB1` và `test_E8` — hai khoá canh đúng
chỗ, vì `generate_json_schema()` (`contract:1658`) **là** `responseSchema` thật
của lượt tổng hợp và `grammar_card` dẫn xuất từ `model_fields`. Thêm ô là đổi
**affordance**, và theo lệ repo affordance phải được **đo bằng A/B** chứ không
tự nhận (`MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT`: 1/6 → 6/6). Wave này
có ngân sách 0 lượt gọi, nên nó làm đúng phần chứng minh được tất định — *thôi
vứt thứ mô hình đã viết* — và **không mời thêm thứ mới**.

| thành phần | trạng thái |
|---|---|
| `synthesis_schema` (`9b186828…`) | **không đổi** — hai bản sao byte-đối-byte |
| `grammar_card` | **không đổi** — `grammar_card("hinh_hoc") == card_A.txt` (`test_I2`) |
| `prompts`, `stable_capability_hash`, taxonomy | **không đổi** |
| `AssignStmt.model_fields` | `{kind, target_var, expr}` — khoá bởi `test_I1` |

**`CACHE_DECISION = 81 → 81, KHÔNG bump.`** Ba căn cứ đo được:

1. bề mặt mô hình không đổi (bảng trên);
2. chiều thay đổi **chỉ là** *từ chối → phục vụ*, mà `main.py` chỉ cache
   `status == "ok"` — bản từ chối chưa bao giờ được cache;
3. phép nâng **không** làm `grounding_gate` chặt thêm: cổng ấy chỉ kiểm
   `source_fact_id` khi khai báo có `initial_value`, còn vật dựng ra thì
   không có. Đo trực tiếp — bịa `source_fact_id` ở mọi `assign` của `e1` và
   `e5`: cả hai **vẫn `served`**. Nên không envelope đã cache nào hoá sai.

Cùng lớp `CURVED_SCALAR_AXIS_INTERSECTION_FIX` và
`POINT_INITIALIZATION_CONTRACT_ALIGNMENT`, cả hai cũng `81→81`.
`tests/test_cache_identity.py` (3 test) và `tests/test_api.py` xanh.

**`CANDIDATE_BEFORE_AFTER = 4f813a38… → c39f7358…`** (89 file, `--verify`
exit 0). Diff con dấu đúng **bốn dòng**: thời điểm · commit · commit ngắn ·
`tree_hash`. `cache_version`, băm lược đồ, taxonomy, pool, seal **không đổi**.

Phạm vi giữ nguyên: tập phép hình học, kernel, ranh giới hỗ trợ và
`product_capability` không đụng tới. **Ball/cylinder/cone vẫn
`foundation_only`.** Artifact V3 và A/B **không đổi một byte**; replay mới lưu
riêng ở `docs/evaluation/geometry/obligation-container-binding/`.

## 9. Cổng đã chạy

| cổng | kết quả | mới hay kế thừa |
|---|---|---|
| `pytest -q` (cây sạch @ `a0200d0`, sau đóng băng lại) | **3860 pass**, 1 skip, 1 deselect, **0 đỏ** | **chạy mới** |
| wave suite | **27 pass** (nền đỏ 11/27) | **chạy mới** |
| `vitest run` | **698 pass / 51 file** | **chạy mới** (frontend không đụng) |
| `replay_demo_cases.py` | **5/5**, `REDUCED_CHAIN 1/1` | **chạy mới** |
| `audit_demo_crash_surface.py` | **6/6 biên**, ném ra ngoài **0** | **chạy mới** |
| `freeze_evaluation_candidate.py --verify` | **exit 0**, 89 file | **chạy mới** |
| `npm run build`, lượt live V3, A/B | — | **kế thừa**, không chạy lại |

## 10. Giới hạn còn lại

- **`ratio` hiểu theo quy ước chia đoạn** — tái hiện **hai lần** (`c9b`, `e4`).
  Đây là lỗi mô hình còn lại mạnh nhất trên chính đường vừa mở, và nó chặn `e4`
  ở tầng ngay sau binding.
- **Bất đối xứng còn lại:** phép nâng xuất xứ chỉ chạy cho câu lệnh ghi vào một
  tên **đã khai**. Câu lệnh `construct_*` không có ô `source_fact_id` trong
  lược đồ, nên vật dựng bằng `construct_section` chưa có đường nối này. Chưa
  có phản ví dụ đi qua đường binding cho hình dạng ấy, nên **không mở rộng**
  theo luật §3c; sẽ mở khi có ca thật.
- **Affordance chưa đo:** hệ nay *nhận* `source_fact_id` ở `assign` nhưng
  **không nói** với mô hình rằng nó được nhận. Tỉ lệ mô hình tự viết ô ấy chưa
  đo — quan sát được 1/3 ca (`e4` có, `e1`/`e5` không).
- `MODEL_DISCOVERABILITY` và `STABILITY_UNDER_ACCEPTANCE` **không đo** trong
  wave này: cả hai đòi lượt gọi thật, mà ngân sách là 0.

## 11. Kết luận

```
ROOT_CAUSE                    = CONTAINER_LA_NHAN_DE_DAT_CHO_VAT_DAN_XUAT;
                                NOI_CHI_CON_BA_LUOI_CHINH_TA; XUAT_XU_BI_VUT_O_PARSE
GIA_THUYET_BI_BAC             = CONTAINER_KHONG_PHAI_DINH_DANH  (e5 `(j)` served)
BINDING_AUTHORITY             = coverage_gate._theo_xuat_xu_du_kien (net ⓪b)
                                + contract._nang_xuat_xu_cau_lenh
                                + _ung_vien_theo_witness (DÙNG CHUNG với net ⓪)
E4_ORIGINAL_CONTRACT_REPLAY   = COVERAGE_PASS · dừng ở execution vì lỗi MÔ HÌNH
                                độc lập (ratio 5/2 → CURVED_PLANE_DOES_NOT_CUT)
E4_EXACT_RADIUS               = 15   (hợp đồng nguyên văn + 1 token ratio 5/7)
AMBIGUOUS_BINDING_HANDLED     = YES  (RANG_BUOC_MO_HO, fail-closed)
WRONG_SUBJECT_WITNESS_REJECTED= YES
MULTI_OBLIGATION_ISOLATION    = YES  (radius 15 · volume 4116π, không rò bí danh)
COVERAGE_POSTCONDITION_PARITY = YES  (một `ten_da_hoa_giai`, hai consumer)
MODEL_FACING_DELTA            = NONE (schema · thẻ · prompt · capability nguyên)
CACHE_DECISION                = 81 → 81, KHÔNG bump (3 căn cứ đo được, §8)
CANDIDATE_BEFORE_AFTER        = 4f813a38… → c39f7358…  (89 file, verify exit 0)
APPLICATION_LLM_CALLS         = 0
PRODUCT_VARIANT               = A    (grammar_card == card_A.txt, byte-đối-byte)
MODEL_DISCOVERABILITY         = NOT_MEASURED
STABILITY_UNDER_ACCEPTANCE    = NOT_MEASURED
RECOMMENDED_NEXT_ACTION       = DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB
```

**Vì sao việc kế tiếp là thế.** Đường tất định của binding nay đã thông, nên
theo luật *"thông rồi thì đo tác động lên khả năng tự sinh"*, việc kế tiếp là
một **phép đo AI phát triển nhỏ (A/B ghép cặp)** trên đúng lỗi còn lại đã tái
hiện hai lần: `divide_segment.ratio`. Thẻ văn phạm hiện in nguyên văn

```
divide_segment: a:tên<point3>[điểm đầu] b:tên<point3>[điểm cuối] ratio:tên
```

— `a` và `b` đều có chú thích, còn **`ratio` không có chú thích nào**, nên thẻ
không nói nó là tham số `t` và mô hình mặc định hiểu theo quy ước chia đoạn
`m:n` của SGK. Cùng hình dạng với `MODEL_FACING_OPERATION_AFFORDANCE_
ALIGNMENT` (thẻ không nói kiểu kết quả → chọn sai toán tử 5/6), nên đo bằng
đúng khuôn ấy: `run_affordance_ab.py`, arm A = thẻ hiện tại, arm B = thẻ nói
rõ nghĩa `ratio`, có trần lượt gọi dẫn xuất và khai trước
`MEASUREMENT_CLASS = DEVELOPMENT_AB` · `HELD_OUT_CLAIM = NO`.
