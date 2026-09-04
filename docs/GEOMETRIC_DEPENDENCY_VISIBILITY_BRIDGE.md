# GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE

> 2026-09-04. **`APPLICATION_LLM_CALLS = 0`** · `V3_EXECUTED = NO` ·
> pool V3 và `pool_hash` không đụng tới.
> Sửa mã sản phẩm: **đúng một hàm, đúng một dòng**.

## ROOT_CAUSE

Ba tầng trả lời khác nhau cho **cùng một câu hỏi** — *"chương trình này có
những vật nào?"*:

| tầng | nguồn | thấy vật dựng bằng `construct_*`? |
|---|---|---|
| runtime (`interpreter`) | `memory[target_var] = …` | **có** |
| kiểm tĩnh (`kiem_tinh`) | `co[target] = _KIEU_DUNG[k]` | **có** |
| **cảnh** (`dependency_graph`) | `memory_declarations` | **KHÔNG** |

`construct_*` ghi thẳng vào bộ nhớ, **không đòi khai báo**. Nên phép lọc chống
tên-ma của `dependency_graph` coi mọi vật dựng ra mà mô hình không khai là
"rác" rồi vứt — và **mọi cạnh trỏ tới một vật DẪN XUẤT biến mất**.

Đây là **consumer thứ ba** của cùng câu hỏi mà `OBLIGATION_BINDING_CONTRACT`
(cùng ngày) đã bịt cho cổng phủ bằng `bang_ky_hieu`. Wave đó sửa một consumer
và bỏ sót cái này — cái mà **học sinh nhìn thấy**.

Đo trên ca `circumsphere` (`probe-contract-waves-2`), 8 vật bị lọc mất, 4 cạnh
đứt — và cả 4 đều là mắt xích dẫn xuất:

```
object.depends  vs  event.depends       (LỆCH 4/16)
  D             ['vec_OC']              ['A_prime','vec_OC']
  M             ['O']                   ['D','O']
  circumsphere  ['O']                   ['M','O']
  R             []                      ['circumsphere']
```

Hậu quả ở đúng bề mặt học sinh, chạy bằng chính `dependencyClosure` của
frontend:

```
chọn 'R'            → THẤY []       (đúng ra 10 vật)
chọn 'circumsphere' → THẤY ['O']    (đúng ra 9 vật)
```

Bấm vào **đáp số** thì không sáng một vật nào. Vật chỉ phụ thuộc điểm tự do
(`face_*`, `OABC`, `vec_*`) thì nguyên vẹn — nên lỗi trông như "vài chỗ lẻ"
trong khi nó cắt đúng xương sống của chuỗi dựng.

**Chỉ *chọn* hỏng, *tua* thì đúng**: `objectsAt` và `highlightedAt` đọc
`events`, không đọc `objects[].depends`. Phân biệt này quan trọng — nó nói
đúng cái gì đã hỏng và cái gì chưa bao giờ hỏng.

## AUTHORITY_OWNER

| câu hỏi | chủ sở hữu | đổi? |
|---|---|---|
| câu lệnh sinh kiểu gì | `ir_static_check._KIEU_DUNG` | không |
| toán hạng TÊN của câu lệnh | `ir_static_check._TOAN_HANG_LENH` | không |
| **tên nào CÓ THẬT trong chương trình** | `ir_static_check.bang_ky_hieu` | không (đã có sẵn) |
| dẫn xuất cạnh phụ thuộc | `simulation_state.dependency_graph` | **chỉ đổi tập lọc** |

`NEW_AUTHORITIES = 0`. Hướng phụ thuộc `ir_static_check → simulation_state`
một chiều, không chu trình: `ir_static_check` không nhập `simulation_state` hay
`scene3d` (kiểm bằng grep + `test_scene3d.py` quét AST).

## CONTRACT_BEFORE → CONTRACT_AFTER

```diff
- khai = {d.name for d in spec.memory_declarations}
+ co_that = set(bang_ky_hieu(spec))
```

Bất biến **không đổi**: mọi cạnh phải là một tên có thật trong chương trình.
Chỉ **tập dùng để kiểm** đổi — từ *"chương trình KHAI những gì"* sang
*"chương trình CÓ những vật nào"*.

Thuật toán thu thập cạnh (`_phu_thuoc`), producer và thứ tự đều giữ nguyên;
`test_A2` khoá điều đó bằng cách đòi đồ thị sau lọc là **tập con** của đồ thị
thô — lớn hơn nghĩa là cạnh đến từ chỗ khác.

## SEMANTIC_VS_RENDERABLE_CLOSURE

Hai trường có **miền khác nhau**, nên kiểm bằng bao hàm chứ không bằng nhau:

| trường | nguồn | chứa |
|---|---|---|
| `event.depends` | `_provenance.sources` | toán hạng TRỰC TIẾP của câu lệnh |
| `object.depends` | `_phu_thuoc` | toán hạng **+** phụ thuộc ĐIỀU KHIỂN **+** cạnh BÍ DANH |

Đo trên **toàn corpus lịch sử**, 169 cặp vật/sự kiện:

```
event.depends ⊆ object.depends     169/169   (0 vi phạm)
bằng nhau chính xác                157/169
object ⊋ event                      12/169   — TẤT CẢ có producer = None
```

12 ngoại lệ đều là vật **bí danh** (`S ≡ S_apex`, `I ≡ sphere_obj`): tên hợp
đồng được hoà giải lên một vật chương trình, không có câu lệnh sinh nên sự
kiện của nó không mang toán hạng nào. Nên phép chiếu có tên rõ ràng:

- **mọi vật**: `event.depends ⊆ object.depends` (`test_B2`);
- **vật có `producer`**: hai trường khớp **chính xác** (`test_B3`).

Phía học sinh tách hai tập:

```
SEMANTIC_CLOSURE   = mọi vật chuỗi dựng đi qua, KỂ CẢ vật không vẽ được
RENDERABLE_CLOSURE = SEMANTIC_CLOSURE ∩ scene_object_ids
```

`vec_OB`/`vec_OC` mang `render: "non_visual"` — đòi renderer tô sáng một vectơ
là đòi một thứ không có hình. Nhưng chúng **phải** ở trong closure ngữ nghĩa:
lọc chúng ra thì chuỗi đứt tại `A_prime` và mất luôn `A`. `highlightSet` phủ
đủ `RENDERABLE_CLOSURE`; test dựng kỳ vọng **độc lập từ `events`**, nên không
thể xanh nhờ hai bên cùng sai một kiểu.

## FAULT_INJECTION

Khôi phục tập lọc cũ (`memory_declarations`), chạy, rồi khôi phục bản đúng.

**Backend — 6 đỏ:**

```
test_A_canh_dan_xuat_da_tro_lai[D-mong0]
test_A_canh_dan_xuat_da_tro_lai[M-mong1]
test_A_canh_dan_xuat_da_tro_lai[R-mong2]
test_A_canh_dan_xuat_da_tro_lai[circumsphere-mong3]
test_B2_scene_object_depends_khong_thieu_canh_cua_su_kien
test_B3_vat_co_PRODUCER_thi_hai_truong_khop_chinh_xac
```

**Frontend — 8 đỏ** (fixture sinh lại dưới bản tiêm): 4 ca `directDependencies`,
`khớp bao đóng dựng độc lập từ events`, `chọn R thì truy ngược tới tận điểm
gốc`, `chọn mặt cầu thì thấy tâm và điểm nó đi qua`, `vật KHÔNG VẼ ĐƯỢC vẫn ở
trong bao đóng ngữ nghĩa`.

Chênh lệch cạnh: đúng 4 cạnh ở bảng ROOT_CAUSE. Khôi phục ⇒ 42 backend + 11
frontend xanh.

`test_D_khoi_phuc_bo_loc_CU_thi_canh_dan_xuat_bien_mat` giữ phép tiêm ấy lại
trong suite bằng `monkeypatch`, nên nó không phải một lần thử tay rồi quên.

## CONSTRUCTION_DEPTH_CORRECTION

⚠️ **Đính chính một nghi vấn của chính tôi.** Lượt khảo sát trước nêu *"15
chương trình bị đo hụt, một ca 2 → 6, kết luận Phase 5G chưa chắc đúng"*. Đo
lại cho đúng phạm vi thì **nghi vấn ấy không đứng vững**.

Con số cũ quét **toàn bộ** `docs/evaluation/geometry`, gồm cả artifact hình
cong mà bộ đo **chưa bao giờ chạy trên đó**. Bộ đo chỉ đọc `*-lan*.json`.

Trên **mọi corpus bộ đo đọc được** (19 thư mục):

```
PROGRAMS_REMEASURED          189
PROGRAMS_WITH_CHANGED_DEPTH    4      (2,1%)
MAX_DEPTH_BEFORE               6
MAX_DEPTH_AFTER                6      ← không đổi
DEPTH_BEFORE   {1:40, 2:94, 3:21, 4:28, 5:5, 6:1}
DEPTH_AFTER    {1:37, 2:94, 3:24, 4:28, 5:5, 6:1}
```

Bốn ca đổi: `phase7a-pilot-sau-71/4-khoang-cach-lan3` 2→3 ·
`phase7b-official/hp_b03_034-lan2` 1→3 ·
`postfix-confirmation-v2/hp_a02_006-lan2` 1→3 ·
`postfix-confirmation-v3/hp_a05_012-lan1` 1→2.

Trên bốn thư mục đã có `phan_tich_phu_thuoc.json` (57 chương trình): **1** ca
đổi, phân bố `{1:15, 2:26, 3:1, 4:15}` → `{1:15, 2:25, 3:2, 4:15}`.

**Kết luận Phase 5G KHÔNG bị ảnh hưởng.** Corpus nó dẫn (`dev-results-w4`, 6
chương trình) đo lại ra **y hệt**: `{1:2, 2:4}`, max **2**, **0 ca đổi**. Câu
*"chuỗi nông vì HỢP ĐỒNG, không có phép nâng đáy thành khối"* vẫn đứng.

Ba con số phải tách bạch:

| | |
|---|---|
| số LỊCH SỬ (ghi trong artifact) | giữ nguyên, byte-identical |
| số TÁI TÍNH bằng thẩm quyền đã sửa | bảng trên |
| kết luận HIỆN TẠI | Phase 5G không đổi; ảnh hưởng thực tế lên chỉ số độ sâu là **nhỏ** |

Không artifact lịch sử nào bị ghi đè: bộ đo ghi
`phan_tich_phu_thuoc.json` vào thư mục nó quét, nên phép đo lại gọi thẳng
`phan_tich()` ngoài cây thay vì chạy CLI.

## CACHE_DECISION

Đo trực tiếp envelope `circumsphere` trước/sau:

```
scene3d payload         9710 → 9745 byte   (ĐỔI)
objects[].depends đổi   ['R','D','M','circumsphere']
trường KHÁC depends     (không có)
events                  không đổi
free_objects            không đổi
```

```
CACHED_PRODUCT_OUTPUT_CHANGED = YES
CACHE_VERSION = 75 → 76
```

Cùng loại **69/71/72/75**: hợp đồng gửi cho mô hình đứng yên, **phán quyết/đầu
ra sản phẩm đổi**. Khác loại 70/73/74 (bề mặt mô hình đổi). Envelope đã cache
chở một đồ thị đứt; trả lại nó là phục vụ mãi một cảnh không truy ngược được.

Năm cổng đồng bộ: `main.py` · `test_api.py` · `CURRENT_STATE.md` ·
`test_evaluation_candidate.py` · `cache_identity.lock.json`.

## IDENTITY

```
MODEL_FACING_CONTRACT_CHANGED    = NO   grammar_card   e0790ba831c23718…
PROMPT_CHANGED                   = NO   prompts        55ac1ca6a6df92ce…
IR_SCHEMA_CHANGED                = NO   synthesis      8e47707d478f92c4…
                                        analyze        a4d5ed7c65a68007…
CAPABILITY_HASH_CHANGED          = NO   capability     5b61b9ea76d0c764…
CHECKER_RUNTIME_BEHAVIOR_CHANGED = NO   checker không đụng
SCENE_DEPENDENCY_OUTPUT_CHANGED  = YES
semantic_environment_hash        = e6161b15ccef73ce…  (KHÔNG đổi)
```

`test_cache_identity` tự xác nhận *"thành phần đổi: (không — chỉ version
lệch)"* — bằng chứng độc lập rằng bề mặt mô hình đứng yên.

V3: `pool_hash 36c2153e…` và `seed = null` **không đụng**. Nhưng
`V3_SEAL.measured_system_hash = 4d8bfb51…` vốn đã lệch từ wave trước và nay
lệch thêm ⇒ **V3 cần niêm phong lại trên candidate mới trước khi chạy**.

## TEST_RESULTS

```
tests/geometry/test_dependency_visibility.py            14 pass  (mới)
scene3d-causal-selection.test.ts                        11 pass  (mới)
test_simulation_state.py                                28 pass  (1 test đổi tập đối chiếu)
pytest toàn bộ                                        3333 pass, 1 skip, 1 deselect
vitest toàn bộ                                         698 pass / 51 file
```

`test_do_thi_chi_chua_TEN_DA_KHAI` đổi tên thành
`test_do_thi_chi_chua_TEN_CO_THAT_TRONG_CHUONG_TRINH`. **Ý định giữ nguyên** —
nó vẫn cấm tên ma; chỉ đối chiếu với `bang_ky_hieu` thay vì
`memory_declarations`. Bản cũ **khoá luôn cái lỗi** này.

## LIMITATIONS

- `ten_da_hoa_giai` vẫn **phẳng**: hai nghĩa vụ ánh xạ cùng một tên hợp đồng
  sang hai vật thì cái sau đè cái trước. Có từ trước, chưa gặp ca thật.
- `object.depends` chở cả phụ thuộc **điều khiển**; chương trình hình học gần
  như không rẽ nhánh nên chưa quan sát được trên corpus.
- Vật **bí danh** (`producer = None`) có cạnh mà sự kiện của nó không có —
  đã khai ở `test_B3`, không phải lỗi.
- `area`/`lateral_area` **tính được nhưng không hỏi được** (ngoài
  `OBLIGATION_KINDS`) — nợ riêng, không thuộc wave này.

## NEXT_ACTION

Khoảng bằng chứng lớn nhất còn lại **không** phải phía tất định: đó là *mô hình
có tự tổng hợp được chương trình khối cong không* — hiện **0 lượt `servable`
trên mọi artifact**, và mọi số đó đo trên một hệ đã có ba lỗi nay đã sửa.

Trước khi chạy V3: **niêm phong lại V3 trên candidate mới** (`seal_curved_v3.py`),
vì `measured_system_hash` trong seal hiện tại trỏ một hệ không còn tồn tại.

```
GEOMETRIC_CONSTRUCTION_TRACE = PASS
LEARNER_CAUSAL_SELECTION     = PASS
CONTINUOUS_SHAPE_FORMATION   = OUTSIDE_CURRENT_MODEL
APPLICATION_LLM_CALLS        = 0
V3_EXECUTED                  = NO
```
