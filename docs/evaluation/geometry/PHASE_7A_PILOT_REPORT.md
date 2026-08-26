# PHASE 7A — PILOT BENCHMARK (2026-08-26)

> **Mục tiêu duy nhất: kiểm BỘ ĐO.** Năm đề × 3 lượt là mẫu quá nhỏ để nói bất
> cứ điều gì về chất lượng mô hình, và báo cáo này **không** nói. Nó trả lời một
> câu khác: *năm chỉ số của `PHASE7_METRIC_CONTRACT.md` có phân biệt được các
> trường hợp không, và taxonomy bốn nhóm có phủ hết lỗi không?*
>
> Bản đo: `97a009e` · `CACHE_VERSION 46` · skill `6208fc2a` · thẻ `446b0769` ·
> `gemini-2.5-flash` · cây sạch. 15 lượt, không sửa gì giữa chừng.

---

## 1. Từng lượt sinh ra gì

| Lượt | served | scene3d | oracle | om | nv | dựng | sâu |
|---|:-:|---|:-:|:-:|:-:|:-:|:-:|
| trung-điểm 1 | ✅ | 7 đt · 3 bước | `True` | ✅ | 1 | 2/3 | 1 |
| trung-điểm 2 | ✅ | 7 đt · 3 bước | `True` | ✅ | 1 | 2/3 | 1 |
| trung-điểm 3 | ✅ | 9 đt · 5 bước | `True` | ✅ | 1 | 4/5 | 1 |
| thể-tích 1 | ❌ | — | `None` | ✅ | 1 | 3/3 | 2 |
| thể-tích 2 | ✅ | 8 đt · 4 bước | `True` | ✅ | 1 | 3/3 | 2 |
| thể-tích 3 | ✅ | 8 đt · 4 bước | `True` | ✅ | 1 | 3/3 | 2 |
| **PMN 1** | ❌ | — | **`True`** | ❌ | 1 | 8/9 | 4 |
| PMN 2 | ✅ | 13 đt · 9 bước | `True` | ✅ | 2 | 8/10 | 4 |
| PMN 3 | ✅ | 13 đt · 9 bước | `True` | ❌ | **0** | 8/8 | 4 |
| khoảng-cách 1 | ✅ | 10 đt · 6 bước | `True` | ✅ | 1 | 5/5 | 2 |
| khoảng-cách 2 | ✅ | 7 đt · 3 bước | `True` | ✅ | 1 | 2/2 | 2 |
| khoảng-cách 3 | ✅ | 16 đt · 12 bước | `True` | ✅ | 1 | 11/11 | 2 |
| góc 1 | ✅ | 8 đt · 4 bước | `True` | ✅ | 1 | 3/4 | 2 |
| **góc 2** | ❌ | — | `None` | ❌ | 0 | **không sinh** | — |
| góc 3 | ✅ | 8 đt · 4 bước | `True` | ✅ | 1 | 3/4 | 2 |

### Tổng theo đề

| Đề | served | oracle | obligation_match |
|---|:-:|:-:|:-:|
| trung điểm | 3/3 | 3/3 | 3/3 |
| thể tích | 2/3 | 2/3 | 3/3 |
| thiết diện PMN | 2/3 | **3/3** | 1/3 |
| khoảng cách | 3/3 | 3/3 | 3/3 |
| góc | 2/3 | 2/3 | 2/3 |
| **Tổng** | **12/15** | **13/15** | **12/15** |

### `construction_validity`

```
literal substitution     0/73   = 0.0%     ← mục tiêu 0%, đạt
dependency construction 65/73   = 89.0%
witness dẫn xuất        12/13   = 92.3%
độ sâu chuỗi            1 · 2 · 4
chương trình đọc được   14/15   (1 lượt chết trước khi sinh)
```

Hai đề mới cư xử đúng như ba đề cũ: `khoảng cách` đạt `11/11` dựng phụ thuộc ở
lượt 3, `góc` đạt `3/4` cả hai lượt thành công. **0% literal substitution** giữ
nguyên qua bốn vòng đo (Phase 6.7, 6.7.2, và pilot này) — tổng **0/304 vật**.

---

## 2. Bộ đo có phân biệt được không? — **CÓ, và pilot chứng minh bằng ba ca**

Đây là kết quả chính của pha này. Ba lượt trượt rơi vào **ba nhóm khác nhau**,
và mỗi nhóm bộc lộ một tính chất mà một chỉ số đơn lẻ **không** thấy được.

### ⚠️ Ca quan trọng nhất: `PMN 1` — **trượt nhưng ĐÚNG**

```
servable = False        (learner_surface)
oracle   = True         Q_point là trung điểm AD
scene3d  = KHÔNG
```

Chương trình **dựng đúng hình và ra đúng đáp án** — oracle độc lập xác nhận —
nhưng học sinh **không nhận được gì**. Nếu báo cáo chỉ có `served`, ca này biến
mất; nếu chỉ có `oracle`, nó trông như thành công.

**Đây chính là lý do hợp đồng chỉ số cấm gộp**, và pilot vừa cho một mẫu thật.

### Ca thứ hai: `PMN 3` — **served với `nv = 0`**

`served ✅ · oracle True · 13 đối tượng · 9 bước` — nhưng hợp đồng khai **không
nghĩa vụ nào**, nên C₁a/C₁b/C₂ không có gì để đối chiếu. `servable = true` ở đây
nghĩa là *"chạy trọn và mọi thứ lên được hình"*, **không** phải *"đáp án đã được
kiểm"*.

Cột `nv` bắt được nó; cột `served` một mình thì không.

### Ca thứ ba: `góc 2` — **chết TRƯỚC khi sinh**

`12.5s`, không chương trình, `construction_validity` = *không đo được*. Bộ đo
phân biệt đúng ba trạng thái: `oracle = None` (không chấm được) khác hẳn
`oracle = False`.

---

## 3. Failure taxonomy — ba lượt, ba nhóm

| Lượt | Nhóm | Bằng chứng |
|---|:-:|---|
| thể-tích 1 | **model** | khai biến tên `volume` **có `initial_value`** mà thiếu xuất xứ |
| PMN 1 | **validator** | hợp đồng đòi witness `Q`, chương trình dựng `Q_point` |
| góc 2 | **routing** | cổng execution-authority từ chối trước khi sinh |

### ① `thể-tích 1` — **model generation**

```
volume: có initial_value nhưng thiếu source_fact_id — không truy được về đề bài
```

Biến tên `volume` (trùng tên nghĩa vụ) mang một giá trị khai sẵn. Cùng hành vi
*"khai một chỗ chứa cho nghĩa vụ"* đã thấy ở Phase 6.7.2 — khác ở chỗ lần này nó
kèm `initial_value`, nên grounding bắt được. **Grounding làm đúng việc.**

### ② `PMN 1` — **validator**, và là lần THỨ TƯ của cùng một lớp lỗi

```python
def check_learner_surface(contract, spec, exec_res, envelope):   # ← không có
    ...                                                          #   ánh xạ
    if witness and witness not in thay_duoc:                      # tên HỢP ĐỒNG
```

`thay_duoc` = `_bound_names(spec) | _tren_canh_3d(spec, exec_res)` — **toàn tên
chương trình**. `ob.witness` là **tên hợp đồng**. Chương trình dựng `Q_point`,
hợp đồng gọi `Q`, và cổng kết luận *"học sinh không thấy đáp án"* trong khi đáp
án **có mặt trên cảnh**.

Cùng lớp với ba lần trước (C₁a↔C₂ · `_semantic_shadow`↔cổng phạm vi · C₁a nửa
trong nửa ngoài + C₁b). Ba cổng đã nhận `ten_da_hoa_giai`; `learner_surface` là
cổng thứ tư và **chưa nhận**.

> ⚠️ **Bất biến tôi viết ở Phase 6.7.1 KHÔNG bắt được ca này, và đó là một lỗ
> của test chứ không phải của may rủi.**
>
> `test_DOI_TEN_KHONG_DOI_PHAN_QUYET` đổi tên mọi vật **được dựng bằng
> `construct_*`**. Nhưng witness của bài thể tích (`V_S_ABCD`) sinh ra bằng
> `assign`, nên nó **không bị đổi tên**, nên tên witness trong test **không bao
> giờ khác** tên hợp đồng. Bất biến ấy phủ container, không phủ witness.
>
> Một bất biến phủ thiếu một nửa vẫn là một bất biến — và nó đã cho tôi cảm giác
> an toàn sai suốt hai pha.

### ③ `góc 2` — **routing**

```
Bài cần cơ chế chưa có engine tất định sở hữu (geometric_perpendicular)
— hệ từ chối trung thực thay vì dựng cảnh xấp xỉ.
```

`check_execution_authority` từ chối khi
`plan.unsupported_capabilities ∩ known_gap_roles()` khác rỗng — **trước** khi
route sinh chạy. Và:

```
known_gap_roles() = 8 vai trò, gồm:
  geometric_circle · geometric_intersection · geometric_locus
  geometric_perpendicular · geometric_projection
```

Danh sách ấy **dẫn xuất từ manifest DSL 2D** — *"vai trò mà không primitive thị
giác nào cover"*. Nhưng **nhân hình học sở hữu** vuông góc
(`P.perpendicular_lines`), giao (`K.intersect_*`) và hình chiếu
(`K.project_point_onto_*`) từ Wave 1. Đường sinh hình học **không đi qua DSL**,
nên cái gap ấy không còn đúng với nó.

Nó **không tất định**: cùng một đề, lượt 1 và 3 qua (analyze không khai vai trò
ấy), lượt 2 trượt (có khai). Đó là lý do nó chưa từng lộ ra ở 30 lượt trước —
ba đề cũ không dẫn analyze tới `geometric_perpendicular`.

**Cả hai lỗi ② và ③ đều KHÔNG sửa trong pha này** — 7A chỉ kiểm bộ đo.

---

## 4. Bộ đo có gì chưa phủ

| | Đã bộc lộ | |
|---|---|:-:|
| `served` phân biệt phát/không phát | ✅ | 12/15 |
| `oracle` ba trạng thái `True/False/None` | ✅ | có cả ba |
| `oracle` ĐỘC LẬP với `served` | ✅ | PMN 1: trượt mà đúng |
| `obligation_match` bắt `nv = 0` | ✅ | PMN 3 |
| `construction_validity` đo được khi có chương trình | ✅ | 14/15 |
| `construction_validity` khai "không đo được" | ✅ | góc 2 |
| taxonomy phủ 4 nhóm | ⚠️ **3/4** | thiếu **contract** |

**Chưa có mẫu nhóm `contract` trong pilot** — lỗi contract cuối cùng
(`arith` trong `construct_point`) đã đóng ở Phase 6.8, và không lượt nào trong
15 lượt này chạm một lỗ biểu đạt. Đó là tin tốt cho hệ nhưng có nghĩa taxonomy
nhóm 2 **chưa được kiểm bằng một ca thật** ở pilot.

`stability` đo được `k = 3`, và ba đề cho ba hình dạng khác nhau (`3/3`, `2/3`,
`2/3`) — đủ để thấy chỉ số hoạt động, **không** đủ để kết luận về mô hình.

---

## 5. Kết luận — **bộ đo dùng được cho Phase 7B**

Pilot đạt mục tiêu đã đặt: năm chỉ số **phân biệt được các trường hợp**, và
chúng **đi ngược chiều nhau** đúng như hợp đồng đã dự liệu — có lượt trượt mà
đúng, có lượt served mà không kiểm gì.

Hai việc phải làm **trước** Phase 7B, cả hai đều đã có bằng chứng:

1. **`learner_surface` nhận `ten_da_hoa_giai`** (nhóm validator, lần thứ tư của
   cùng lớp lỗi) — và **mở rộng bất biến** để nó phủ cả witness, không chỉ
   container. Không sửa thì Phase 7B sẽ ghi những lượt **đúng** thành **sai**,
   đúng cái đã xảy ra ở Phase 6.7 và đã phải sửa ở 6.7.1.
2. **`known_gap_roles` không được áp cho đường sinh hình học** (nhóm routing) —
   danh sách ấy dẫn từ manifest DSL 2D, mà đường hình học không đi qua DSL. Không
   sửa thì một phần đề hình học bị từ chối **trước khi sinh**, và tỉ lệ ấy sẽ
   vào báo cáo như thể mô hình không làm được.

Cả hai đều bóp méo số **theo hướng thấp hơn thực tế**, và cả hai đều đổ cho mô
hình cái lỗi thuộc về hệ. Với một đề tài mà luận điểm là *"AI sinh được chương
trình đáng tin cậy hay không"*, đó là loại sai lệch tệ nhất.

**Không kết luận gì về chất lượng mô hình từ mẫu này** — 15 lượt trên năm đề tôi
tự chọn, và ba trong số đó đã bị nhìn suốt tám wave.

---

## Ghi chú vận hành

Docker Desktop **không chạy** trong phiên này, nên `runtime_doctor` không đọc
được runtime. Pilot **không cần container**: bộ đo gọi `run_pipeline` trong tiến
trình trên cây làm việc. Danh tính được chốt phía **nguồn** thay cho doctor, và
đó là bảo đảm mạnh hơn — không có image nào để cũ:

```
commit 97a009e · cây sạch · CACHE_VERSION 46
catalog 128c33be · skill 6208fc2a · thẻ văn phạm 446b0769
```

`446b0769` khớp đúng bản đã cho smoke 3/3 ở Phase 6.8.

## Chi phí

15 lượt × ~6 lượt LLM ≈ **90 lượt**. Phân tích `construction_validity` chạy
**0 API call** trên artifact đã lưu. Artifact: `phase7a-pilot/` — 15 file kèm
`request_contract`, `generated_program`, `final_memory`.
