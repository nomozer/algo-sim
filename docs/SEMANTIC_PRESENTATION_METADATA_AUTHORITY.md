# SEMANTIC_PRESENTATION_METADATA_AUTHORITY — đóng G1 + G2

> Thực hiện **2026-09-02**. Đóng hai gap P0 duy nhất của
> `GEOMETRY_ARCHITECTURE_EXPRESSIVENESS_AUDIT`.
>
> **0 lượt gọi model.** Không năng lực hình học mới, không đổi lược đồ
> model-facing, không đổi một con số nào.

---

## 1. Vấn đề, nói cho hẹp

Hai gap là **một khoảng trống nhìn từ hai phía**: `simulation_state.build_scene`
đang cầm sẵn cả **kiểu khai** lẫn **tên vật** rồi vứt đi cả hai — hai biến cách
nhau bảy dòng trong cùng một hàm.

| | trước | hệ quả đo được |
|---|---|---|
| **G1** | `label` rơi về `id` khi mô hình không đặt tên; `quantity` **luôn** rơi | học sinh đọc `khoang_cach_hs √22`, `Đang dựng the_tich_sabcd` |
| **G2** | kiểu suy bằng `isinstance`, mà `point3` và `vector3` cùng là `Vec3` | vectơ vẽ thành một chấm ở toạ độ bằng **thành phần** của nó — một vật không có trong bài |

Và hệ quả chung, nặng hơn cả hai con số: **tầng trình bày phải suy lại ngữ
nghĩa.** `kyHieuNgan` đọc ngược `id` để rút ký hiệu; `laVectoDangDiem` đọc
`producer` để đoán kiểu. Đó là điều ranh giới R0 cấm, và cả hai chỉ tồn tại vì
backend không nói ra thứ nó biết.

---

## 2. Bản sửa

### 2.1 Thẩm quyền mới: `display_names.py`

Trả lời *"vật này gọi là gì trước mặt học sinh"* — câu hỏi trước đây **không có
chủ**. Bốn bậc, **không có bậc thứ năm**:

```
① nhãn mô hình đã đặt, nếu nó thật sự là một cái tên
② công thức gọi tên dẫn từ PHÉP DỰNG          (_CACH_GOI)
③ mô tả chung theo kiểu, kèm ký hiệu nếu có   ("Điểm A", "Mặt phẳng")
✗ id thô                                       — KHÔNG
```

Bậc ① có một chốt: nhãn **trùng byte với `id`** chỉ được tin khi `id` ấy vốn là
ký hiệu toán. `label = "A"` trên điểm `A` là mô hình nói đúng; `label =
"V_AMNP"` trên `V_AMNP` là **chưa ai đặt tên cả**.

`_CACH_GOI` khoá theo **producer** — một tập đóng gồm phép dựng và phép đo.
Tuyệt đối không theo dạng bài: một nhánh `if "chóp" in …` ở đây sẽ là
special-case theo họ hình, đúng thứ `§7` của audit chứng minh là hiện không có
chỗ nào.

### 2.2 Kiểu KHAI là thẩm quyền

`build_scene` tách làm hai việc từng bị trộn:

- `_than_hinh_hoc(gt)` — lớp runtime quyết **đọc trường nào ra** (`xyz`,
  `point`/`normal`, `vertices`/`faces`…);
- `_loai_ngu_nghia(mac_dinh, kieu_khai)` — kiểu **khai** quyết `type` của cảnh,
  khi nó tương thích với thứ bộ nhớ thật sự đang giữ.

Khai ngoài tập tương thích thì mặc định thắng: cảnh phải mô tả thứ bộ nhớ **thật
sự** giữ, không mô tả thứ chương trình *nói* là nó giữ.

### 2.3 `vector3` — có mặt, không vẽ

`RENDER_HINT["vector3"] = "non_visual"`. Đây là **quyết định kiến trúc được nói
ra**, không phải một ô bỏ trống:

- một vectơ tự do **không có vị trí** trong không gian, nên chọn điểm đặt cho nó
  — gốc toạ độ, hay điểm đầu suy từ `depends` — là renderer tự quyết một dữ kiện
  hình học;
- vật **vẫn đi trọn pipeline**: cây thành phần, ô soi, phép chọn đều thấy nó;
  `angle_cos` vẫn đo nó; ô soi hiện `xyz` là các **thành phần**.

Không thêm mũi tên. Không neo vào gốc. Không suy từ `depends`.

### 2.4 Hợp đồng cảnh: thêm đúng MỘT trường

`notation` — ký hiệu ngắn in cạnh vật trên khung. Ghép **đệ quy** từ ký hiệu
toán hạng, đáy ở các điểm gốc, và **fail-closed**: thiếu một toán hạng thì trả
`None`, vì `(M?P)` trông như một ký hiệu thật.

```
(MNP)   ← construct_plane(M, N, P)
AC      ← construct_line(A, C)
d(S, (ABC))   ← measure.distance(S, day)
V(S.ABCD)     ← measure.volume(chop)
cos²(BC, (SAB))
```

`None` là **câu trả lời hợp lệ** (`pyramid_S_ABCD`, `section_MNP`), và khung
không in gì cho vật ấy. Không bịa `M1`, `P2` để có chữ.

Câu hỏi *"chuỗi này có phải ký hiệu toán không"* thuộc
`source_entities.ky_hieu_toan` — thẩm quyền **đã có sẵn** cho *"một nhãn hình
học trông thế nào"*, nay dùng theo chiều ngược. Không bóc tiền tố lần thứ hai ở
nơi khác.

### 2.5 `events[].object` thôi chở sentinel

Bước `INIT` mang `created: "system"` — một sentinel của trace, không phải một
vật. Dải tiêu điểm tra ngược nó rồi in ra **"Đang dựng system"**. `object` nay
chỉ nhận id **có thật trong cảnh**, còn lại là `None`.

Phát hiện trong lượt đo trình duyệt của chính wave này, không phải suy đoán.

### 2.6 Frontend thành "ngu về ngữ nghĩa"

| gỡ | thay bằng |
|---|---|
| `kyHieuNgan(o)` — bóc `_prime`, cắt `vector_`/`point_`/`plane_`, cắt tới gạch dưới | `kyHieu(o)` — đọc `o.notation`, hết |
| `laVectoDangDiem(o)` — `producer === "vector_from_points"` | `veTrenKhung(o)` — đọc `o.render` |
| dải tiêu điểm in id thô | tra ngược sang `label` / `notation` |

Frontend còn được quyền: chọn dùng `label` hay `notation`, cắt chữ, bố cục, ẩn
nhãn chồng nhau, chọn/soi. **Không** còn được suy kiểu, suy quan hệ toán học,
hay dựng một cái tên.

---

## 3. Trước / sau, đo trên bài mẫu thật

```
TRƯỚC                              SAU
V        label='V'                 label='Thể tích S.ABCD'   notation='V(S.ABCD)'
d        label='d'                 label='Khoảng cách giữa S và (ABC)'
                                                             notation='d(S, (ABC))'
u  type=point3  (vẽ thành chấm)    type=vector3  render=non_visual
                                   label='Vectơ từ A đến B'  notation='AB'
A        label='A'  (= id)         label='Điểm A'            notation='A'
bước 0   "Đang dựng system"        "Đang dựng — (dữ kiện đề cho)"
```

Trong trình duyệt thật (`certify-display-metadata.mjs`, **4/4**, 0 lỗi bảng
điều khiển):

```
nhãn khung : ["A","B","C","D","S"]
dải kết quả: ["Thể tích S.ABCD16/3","Khoảng cách giữa S và (ABC)4"]
tiêu điểm  : "Đang dựng Khoảng cách giữa S và (ABC) · Dựa trên S, (ABC)"
```

**Số không đổi:** `16/3` và `4` là đúng những giá trị trước bản sửa. Ca
`test_gia_tri_CHINH_XAC_khong_bi_ten_goi_dong_toi` khoá điều đó.

---

## 4. Điều KHÔNG làm, có chủ đích

| | vì sao |
|---|---|
| Không thêm `label` vào `AssignStmt` | sẽ đổi lược đồ model-facing và bắt mô hình sinh thêm token cho một thứ backend **dẫn xuất được tất định**. `MODEL_FACING_SCHEMA_CHANGED = NO` |
| Không thêm loại vẽ mũi tên | vectơ tự do không có vị trí; vẽ nó ở đâu cũng là renderer tự quyết một dữ kiện hình học |
| Không xử G7 (`events[].action` không ai đọc) | ngoài phạm vi wave |
| Không sửa runtime G3 (`SECTION_COPLANAR_EDGE_GAP`) | ngoài phạm vi; ghi backlog |
| Không đổi `exact`, checker, thứ tự trace, toạ độ | `GEOMETRY_RESULTS_CHANGED = NO` |

---

## 5. Hai điều lượt soát trước nói SAI, nay sửa

1. **`G6` không tồn tại.** Audit ghi `RENDER_HINT` ‖ `RENDER_KINDS` *"không có
   khoá đồng bộ liên ngôn ngữ"*. Sai — `tests/geometry/test_scene3d_ts_sync.py`
   đọc thẳng `scene3d-model.ts` rồi so hai bảng, và nó **bắt được thật**: thêm
   `non_visual` làm nó đỏ ngay. Lượt soát chỉ nhìn phía TS (`scene3d.test.tsx`,
   một danh sách chữ viết tay) rồi kết luận cho cả hai phía.

2. **`SECTION_VERTEX_INTERSECTION_GAP` mô tả sai điều kiện.** Đổi tên canonical
   thành **`SECTION_COPLANAR_EDGE_GAP`** ở `STATUS_LEDGER`, `CODE_INDEX`,
   `THESIS_ARCHITECTURE`, `THESIS_DRAFT`, `THESIS_READINESS`. Bằng chứng lịch
   sử (`docs/evaluation/**`) **giữ nguyên tên cũ**, không viết lại.

⚠️ Trong lúc sửa, guard đọc TS bằng regex đã đỏ vì nuốt một chuỗi **trong chú
thích** (`Không phải "chưa hỗ trợ": …`). Sửa bộ đọc để bỏ chú thích, thay vì bắt
lời giải thích im — mỗi mục trong một bảng đóng xứng đáng được giải thích ngay
tại chỗ.

---

## 6. Cổng và bằng chứng

| cổng | kết quả |
|---|---|
| `pytest` | **2779 passed**, 1 skipped (+19 ca mới ở `test_display_names.py`) |
| `vitest` | **668 passed** (48 tệp) |
| `npm run build` | PASS |
| `replay_demo_cases.py` | **5/5**, chuỗi rút gọn **1/1** |
| `audit_demo_crash_surface.py` | biên **6/6**, ném ra ngoài **0** |
| `certify-display-metadata.mjs` | **4/4**, 0 lỗi bảng điều khiển |
| `certify-journey-integration.mjs` | **13/13** |
| `certify-offline-journey.mjs` | **11/11** |
| `certify-refusal-surface.mjs` | **21/21** |

`CACHE_VERSION` **60 → 61** — bắt buộc, không phải theo thói quen: cache giữ
**nguyên cả envelope**, nên một đề đã phân tích sẽ được trả lại với
`label = "khoang_cach_hs"` và vectơ vẽ thành chấm. Bốn cổng đã bump đồng thời
(`main.py` · `test_api.py` · `CURRENT_STATE.md` · manifest candidate).

`stable_capability_hash()` **không đổi** — và đó là điều đúng: năng lực không
đổi, chỉ cách gọi tên đổi.
