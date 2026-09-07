# NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY

> 2026-09-08 · `MEASUREMENT_CLASS = DEVELOPMENT_DIAGNOSTIC` ·
> `HELD_OUT_CLAIM = NO` · `EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED`
>
> ```
> GOLD_PREFLIGHT = PASS          SCORER_PREFLIGHT = PASS
> APPLICATION_LLM_CALLS = 2      (analyze 1 · tổng hợp 1 · sửa 0)
> PHYSICAL_API_ATTEMPTS = 2      TRANSPORT_RETRIES = 0
> TOTAL_TOKENS = 11 388 / 25 000
>
> FIRST_ATTEMPT_DISCOVERABLE       = YES
> REPAIR_ASSISTED_DISCOVERABLE     = NOT_NEEDED
> MODEL_DISCOVERABLE_ON_THIS_PROBE = YES
> FACE_TABLE_VALID                 = PASS
> EXACT_VOLUME                     = PASS (45)
> SCENE3D_CONCAVITY_PRESERVED      = YES
> FIRST_ATTEMPT_SERVABLE = YES     EVENTUAL_SERVABLE = YES
> FAILURE_STAGE = —                FAILURE_ATTRIBUTION = NONE
>
> NONCONVEX_POLYHEDRON_SEQUENCE = CLOSED_AT_DEVELOPMENT_LEVEL
> CAPABILITY_STATUS = foundation_only   PRODUCT_PROMOTION_ELIGIBLE = NO
> STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
> ```
>
> Mô hình viết đúng bảng mặt của khối chóp đáy lõm ngay lượt đầu, không cần
> lượt sửa nào. **Và phép đo tìm ra một lỗ nặng hơn ở chỗ khác** — xem §7.

## 1. Câu hỏi, và vì sao đề không cho bảng mặt

`NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION` đóng phần hệ. Ô còn lại:

> Với một đề khối chóp đáy lõm **hoàn toàn mới**, mô hình có tự khai các đỉnh,
> viết **bảng mặt kín** bằng `construct_solid`, tính đúng thể tích và sinh
> Scene3D giữ nguyên phần lõm không?

Đề cho **thứ tự đỉnh quanh biên** — đúng như SGK phát biểu — và **không** cho
bảng mặt. Bảng mặt là thứ đang được đo; lọt vào prompt thì phép đo hỏi một câu
khác, dễ hơn, và `MODEL_DISCOVERABLE` sẽ nói về thứ không phải nó.
`test_04` khoá điều đó.

```
S.ABCDE · đáy z = 0 · A(0,0,0) B(6,0,0) C(6,4,0) D(3,1,0) E(0,4,0) · S(2,2,9)
```

Đỉnh lõm: `D`.

## 2. Oracle — bốn nguồn, kernel chỉ là một trong bốn

| Nguồn | Kết quả |
|---|---|
| shoelace đáy × h/3 (tay) | **45** |
| `ABC + ACE − CDE` × h/3 (tay) | **45** |
| signed-boundary **viết riêng**, không gọi kernel | **45** |
| kernel `the_tich_da_dien` | **45** |

Hai bẫy, và chúng cho **hai số phân biệt được** — nên bộ chấm nói được mô hình
hỏng *kiểu nào*:

```
quạt tam giác từ A (lấp chỗ lõm)   shoelace 21  ⇒  V = 63
bao lồi ABCE (bỏ hẳn D)            shoelace 24  ⇒  V = 72
```

⚠️ Ca đo phải nằm **trong** phạm vi đã chứng minh, nếu không `45` là con số
ngoài bảo hành. Mặt bên không xuyên nhau: mọi tia từ `S` cắt `z = 0` đúng một
lần, nên hai mặt bên chỉ gặp nhau ở đỉnh chung của hai cạnh đáy kề — và đáy
ĐƠN. `test_02` khoá.

## 3. Tiền kiểm — cổng chặn, chạy TRƯỚC provider

`scripts/register_nonconvex_polyhedron.py` thoát khác 0 nếu một trong hai tiền
kiểm chưa đạt, nên không rút được ca khi bộ đo còn đỏ.

**GOLD** đi trọn đường: `served` · `V = 45` · `weak_kinds = []` (checker thật
sự chạy) · postconditions · trace · Scene3D giữ phần lõm. Sáu phản ví dụ đều
đỏ đúng chiều chúng bảo vệ:

| # | Phản ví dụ | Đo được |
|---|---|---|
| ① | đáy khai bằng **quạt tam giác** | `V = 45` **ĐÚNG**, nhưng bảng mặt FAIL và phần lõm **bị lấp** |
| ② | thiếu một mặt bên | `POLYHEDRON_BOUNDARY_OPEN` |
| ③ | đổi chu trình đáy | hình khác ⇒ `V = 54` |
| ④ | đáy tự cắt | `POLYHEDRON_FACE_NOT_SIMPLE` |
| ⑤ | bảng mặt hợp lệ, đáp số **khai thẳng** | `KHONG_DUONG_TAT = False` |
| ⑥ | control **LỒI** `S.ABCE` | vẫn `served`, `V = 72` |

> ⚠️ **Phản ví dụ ① là phát hiện ngược trực giác của wave**, và nó quyết định
> hình dạng bộ chấm. Khai đáy bằng ba tam giác `ABC · ACD · ADE` cho biên
> **KÍN** và cho **`V = 45` ĐÚNG** — đó chính là điều công thức có dấu hứa.
> Nhưng ba tam giác ấy là thứ renderer **VẼ**, và `A-C-D` nằm ngoài đáy ⇒ phần
> lõm bị lấp. Nên `EXACT_VOLUME` · `FACE_TABLE_VALID` ·
> `SCENE3D_CONCAVITY_PRESERVED` **không được gộp làm một**: một bộ chấm gộp
> chúng sẽ cho điểm tuyệt đối một chương trình vẽ sai hình.

**BỘ CHẤM** chấm theo **hình học, không theo chính tả**. `FACE_TABLE_VALID`
quyết bằng bốn bất biến tổ hợp, không bằng so chuỗi:

```
· đúng MỘT mặt gồm trọn năm đỉnh đáy, và chu trình của nó là chu trình đáy
· năm mặt còn lại: mỗi mặt = một CẠNH ĐÁY + đỉnh S
· mỗi cạnh vô hướng thuộc ĐÚNG hai mặt        (biên kín)
· không mặt nào lặp đỉnh
```

`SCORER_INVARIANT_TO_NOTATION = YES` — bảng mặt bằng **chỉ số** hay bằng tên ·
tên biến khác đề · đảo chiều **mọi** mặt · xoay vòng chu trình đáy: cùng một
khối thì cùng một phán quyết. Ghim chính tả là chấm sai một chương trình đúng,
và kho này đã trả giá đúng một lần cho lỗi ấy
(`PLANE_CONSTRUCTION_CORRECT = FAIL` cho mặt phẳng đúng từng hệ số).

**Điều đó hoá ra là quyết định đúng, không phải đề phòng thừa** — xem §5.

## 4. Lượt live — kế toán

```
LOGICAL_APPLICATION_CALLS  2/3      analyze 1 · tổng hợp 1 · sửa 0
PHYSICAL_API_ATTEMPTS      2        TRANSPORT_RETRIES 0
TOTAL_TOKENS               11 388 / 25 000
  semantic_analyze   2 406   (prompt 1 268 · out 233 · thought 905)
  semantic_program   8 982   (prompt 3 860 · out 764 · thought 4 358)
cached_content 0                    RUN_STATUS COMPLETE
CANDIDATE_PROGRAM_ATTEMPTS 1        REPAIR_CALLS 0
```

Ngân sách sửa **không được dùng**; trần 3 lượt logic chặn ở biên thật của
`call_gemini`.

## 5. Mô hình viết gì

```json
{"kind": "construct_solid", "target_var": "S.ABCDE",
 "vertices": ["S", "A", "B", "C", "D", "E"],
 "faces": [["A","B","C","D","E"], ["S","A","B"], ["S","B","C"],
           ["S","C","D"], ["S","D","E"], ["S","E","A"]]}
{"kind": "assign", "target_var": "V_S_ABCDE",
 "expr": {"kind": "measure", "quantity": "volume", "of": "S.ABCDE"}}
```

Đúng bảng mặt chuẩn: một đáy ngũ giác + năm mặt bên. `V = 45`, `served`,
envelope `ok`, Scene3D **8 vật · 3 sự kiện**, đáy giữ nguyên **năm** chỉ số với
đúng **một** đỉnh phản xạ.

⚠️ **Mô hình viết theo lối KHÁC gold**: gold khai đáy `E→D→C→B→A` và mặt bên
`[X, Y, S]`; mô hình khai đáy `A→B→C→D→E` và mặt bên `[S, X, Y]`, lại đặt `S`
đầu danh sách đỉnh. Cùng một khối. **Nếu bộ chấm ghim chính tả thì ô trung tâm
của cả wave đã ĐỎ cho một chương trình ĐÚNG** — `test_25` khoá cả điều đó lẫn
điều kiện `st["faces"] != GOLD.MAT`, để ô ấy không mất ý nghĩa nếu lần sau mô
hình tình cờ viết trùng gold.

Đáp số đọc từ **hai nguồn độc lập**: `Fraction(45, 1)` trong final memory, và
chuỗi `45` trong lời kể trace.

## 6. Chiều duy nhất không PASS: analyze không mang toạ độ

```
ANALYZE_OBLIGATION_CORRECT = PASS    (volume · container S.ABCDE · witness)
CO_TU_LOM                  = True
KHONG_TU_THEM_DU_KIEN      = True    (không bịa vuông góc/song song/đường cao)
CO_DU_SAU_DIEM             = False   ← DIEM_THIEU = [A,B,C,D,E,S]
ANALYZE_CONTRACT_CORRECT   = FAIL
```

Hợp đồng analyze có **ba fact kể chuyện**, không fact nào mang toạ độ:

```
khoi_chop         "S.ABCDE là khối chóp"
day_ngu_giac_lom  "ABCDE là một ngũ giác lõm"
day_trong_mp_z0   "Đáy ABCDE nằm trong mặt phẳng z = 0"
```

Thế mà chương trình khai đủ sáu điểm **đúng toạ độ**, trích dẫn
`source_fact_id: day_trong_mp_z0`, và **grounding cho qua**.

Đây **không** phải lý do hạ `MODEL_DISCOVERABLE`: mô hình ra đúng mọi chiều
được hỏi. Nó là **đầu mối**.

## 7. LỖ MỚI, đo được, một biến — và nó bác giả thuyết đầu tiên của tôi

Tôi ngờ nguyên nhân là **analyze không trích toạ độ**, nên grounding không có gì
để đối chiếu. Đo lại với **hợp đồng GOLD**, nơi mỗi điểm là một fact **có toạ
độ**. Kết quả **y hệt**:

| Hợp đồng | Chương trình | Kết quả |
|---|---|---|
| fact **kể chuyện** (như lượt live) | gold gốc | `served` · `V = 45` |
| fact **kể chuyện** | `B(6,0,0)` → `B(99,7,0)` | `served` · **`V = 540`** |
| fact **CÓ toạ độ** | gold gốc | `served` · `V = 45` |
| fact **CÓ toạ độ** | `B(6,0,0)` → `B(99,7,0)` | `served` · **`V = 540`** |

`unjustified_literals = []` ở cả bốn ô.

**Nên lỗ nằm ở `grounding`, không ở `analyze`**: `source_fact_id` được kiểm
**SỰ TỒN TẠI**, không kiểm **SỰ KHỚP**. Một trích dẫn nêu tên một fact; không
ai kiểm con số có đúng bằng fact ấy không.

Vì sao đây là lỗ **mới**, không phải cái đã khai: kho có bất biến nguồn cho
`plane_equation` · `segment_length` · `segment_division` · thang đo —
**không có** cái nào cho **toạ độ điểm đề cho tường minh**. Đo bằng máy, không
suy: `bat_bien_do_dai` và `bat_bien_mat_phang` tồn tại; `bat_bien_toa_do`
không.

⚠️ Đổi `D(3,1,0)` thành `D(3,3,0)` — hết lõm — cho `V = 63`, đúng con số của
bẫy "quạt lấp lõm". Một chương trình làm phẳng chỗ lõm bằng cách khai sai toạ
độ sẽ **được phục vụ**.

`test_21b` khoá lỗ này **bằng một test ĐANG XANH**, theo lệ kho: xanh nghĩa là
lỗ còn; wave sau đóng nó thì test ĐỎ, và đó là tín hiệu đúng.

Wave này **giữ product bytes nguyên vẹn** theo §5 của brief, nên lỗ được ghi
thành kết quả đo và thành next action riêng, không sửa ở đây.

## 8. Danh tính — trước/sau

| | trước | sau |
|---|---|---|
| `CACHE_VERSION` | 92 | **92** |
| candidate (mã sản phẩm) | `6362674e957909d8` | **`6362674e957909d8`** |
| `prompts` | `55ac1ca6a6df92ce` | không đổi |
| `grammar_card` | `cc105e4f1da84d23` | không đổi |
| `synthesis_schema` | `6ccef3230c003d61` | không đổi |
| `analyze_schema` | `515001b503af5c7c` | không đổi |
| `capability` | `72edf39f6c10220d` | không đổi |
| `semantic_environment` | `a483ced9fd7546df` | không đổi |
| `nonconvex_polyhedron` | `foundation_only` | **`foundation_only`** |

```
PRODUCT_CODE_CHANGED          = NO   (git diff -- backend/app frontend/src rỗng)
MODEL_FACING_CONTRACT_CHANGED = NO
CACHE_VERSION_CHANGED         = NO
PRODUCT_CAPABILITY_CHANGED    = NO
```

Đổi duy nhất trong `backend/scripts/`: `run_curved_end_to_end.py` nay đọc khoá
đáp số chung `dap_so_hien_thi` trước hai khoá cũ đặt tên theo họ hình
(`radius_c`, `area_display`). Hai khoá cũ **giữ lại** vì `ORACLE_HASH` của
chúng đã nằm trong artifact bất biến của lượt trước.

## 9. Vì sao KHÔNG nâng năng lực

Một ca, một lượt. `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED` — lượt trước của
họ elip cùng một đề đã từng hỏng rồi lại chạy, nên một lượt không nói gì về ổn
định. `nonconvex_polyhedron` giữ `foundation_only`, `PRODUCT_PROMOTION_ELIGIBLE
= NO`; nút chưa hiện cho học sinh. Kết quả đóng đúng ở mức
`CLOSED_AT_DEVELOPMENT_LEVEL`.

Và §7 là một lý do độc lập để chưa nâng: *"grounded"* trên toạ độ điểm hiện
yếu hơn tên gọi của nó.

## 10. Cổng

```
wave suite       40 pass   (tests/geometry/test_nonconvex_polyhedron_discoverability.py)
pytest           4477 collected · 4476 chạy · 4475 pass + 1 skip (cây sạch)
replay_demo      5/5 · REDUCED_CHAIN 1/1
crash_surface    6/6 · ném ra ngoài 0
certify          RUNNER_CERTIFICATION PASS · APPLICATION_LLM_CALLS 0
cache identity   15 pass @ v92
freeze --verify  exit 0 (91 file, 6362674e…)
git diff --check sạch
frontend         INHERITED — 0 byte tracked frontend đổi
```

`RECOMMENDED_NEXT_ACTION` — xem `docs/CURRENT_STATE.md`.
