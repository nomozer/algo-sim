# PHASE 7A.1 — EVALUATION INTEGRITY FIX (2026-08-26)

> Sửa **sai lệch đo lường**, không nâng năng lực sinh. Hai lỗi lộ ra ở pilot 7A,
> cả hai bóp méo số **theo hướng thấp hơn thực tế** và **đổ cho mô hình** cái lỗi
> thuộc về hệ.
>
> Bản sau sửa: `92d93be` · `CACHE_VERSION 46` · thẻ `446b0769` (**không đổi** —
> không đụng prompt) · `pytest 2905` · `vitest 1598` · cây sạch.

---

## 1. So trước / sau — 15 lượt, cùng năm đề, cùng `k = 3`

| Đề | served | | oracle | | obligation_match | |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| | **trước** | **sau** | trước | sau | trước | sau |
| trung điểm | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| thể tích | 2/3 | **3/3** | 2/3 | **3/3** | 3/3 | 3/3 |
| thiết diện PMN | 2/3 | 2/3 | 3/3 | 2/3 | 1/3 | 0/3 |
| khoảng cách | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| góc | 2/3 | **3/3** | 2/3 | **3/3** | 2/3 | **3/3** |
| **Tổng** | **12/15** | **14/15** | **13/15** | **14/15** | **12/15** | 12/15 |

### `construction_validity`

| | trước | sau |
|---|:-:|:-:|
| literal substitution | 0/73 = 0.0% | **0/86 = 0.0%** |
| dependency construction | 65/73 = 89.0% | **78/86 = 90.7%** |
| witness dẫn xuất | 12/13 | **15/15 = 100%** |
| chương trình đọc được | 14/15 | **15/15** |
| độ sâu chuỗi | 1 · 2 · 4 | 1 · 2 · 3 · 4 |

`15/15 chương trình đọc được` là hệ quả trực tiếp của bản vá ②: trước đó một lượt
**chết trước khi sinh**, nên `construction_validity` của nó không đo được.

### Taxonomy lỗi

| Nhóm | trước | sau |
|---|:-:|:-:|
| model generation | 1 | **1** |
| contract | 0 | 0 |
| **validator** | **1** | **0** |
| **routing** | **1** | **0** |

Hai nhóm được nhắm tới đã về **0**. Nhóm `model` giữ nguyên **1** — đúng như dự
kiến: pha này **không** nâng năng lực sinh.

---

## 2. Bản vá ① — `learner_surface`, cổng thứ tư của cùng một lớp lỗi

```
3-pmn-giao-tuyen-lan1 (7A):  executable = True
                             oracle     = True   (Q_point LÀ trung điểm AD)
                             servable   = FALSE
```

`check_learner_surface` tra witness `Q` — **tên hợp đồng** — trong `thay_duoc`,
một tập **toàn tên chương trình** (`Q_point`). Kết luận: *"học sinh không thấy
đáp án"*, trong khi đáp án **đang nằm trên cảnh**.

C₁a, C₁b, C₂ đã nhận `ten_da_hoa_giai` từ Phase 6.7.1. `learner_surface` là cổng
**thứ tư** và đứng ngoài suốt hai pha. Nay bốn cổng dùng **chung một ánh xạ**, và
thông điệp nêu cả hai tên khi có hoà giải.

**Chạy lại đúng IR ấy, không sửa một ký tự nào của chương trình**: `served`, và
`Q_point = (0, 2, 0)` — đúng trung điểm `AD`.

### Lớp lỗi rộng hơn tôi tưởng: **tham số nghĩa vụ**

Bất biến mở rộng tự tìm ra ca thứ sáu:

```
angle(container="SB", params={"witness": "goc_sb_sd", "wrt": "SD"})
                                                       ↑ tên đối tượng THỨ HAI
```

C₁a chưa bao giờ hoà giải `wrt`. C₂ tra nó bằng tên hợp đồng rồi báo *"cặp đối
tượng không hợp lệ cho góc"* — trong khi **cả hai đường đều nằm đó** dưới tên
khác.

**Không liệt kê khoá tham số bằng tay**: danh sách ấy sẽ thiếu ở lần thêm nghĩa
vụ tiếp theo, đúng như `container`/`witness` đã thiếu lần này. Thay vào đó hoà
giải **mọi giá trị chuỗi chưa khai**, cùng ba lưới, cùng luật fail-closed, và
**chỉ cho nghĩa vụ hình học** — tham số miền Tin học không bị đụng. An toàn vì
lưới vốn chặt: `pred="balanced_delimiters"`, `cmp="max"` không phân giải về đâu.

### ⚠️ Bất biến cũ thủng vì **corpus**, không vì logic

`test_DOI_TEN_KHONG_DOI_PHAN_QUYET` chỉ chạy trên hai lượt bài **thể tích**, nơi
witness (`V_S_ABCD`) sinh bằng `assign` nên **không bao giờ bị đổi tên** — tức
tên witness trong test không bao giờ khác tên hợp đồng. Bài thiết diện thì khác:
witness `Q` sinh bằng `construct_point`.

Nay bất biến đọc **mọi artifact từng `served` ở mọi vòng đo**, nên corpus không
tự thu hẹp được nữa. Chính nó ép ra cả hai bản sửa.

**Hai lần tôi suýt sửa nhầm, và cả hai đáng ghi lại:**

- Đổi tên cả `assign` target ⇒ bất biến đòi hoà giải `V_S_ABCD ≡ V_S_ABCD_x`.
  **Đỏ oan**: một `float` không có topology, danh tính của nó *chính là* cái
  tên, và đòi hoà giải ở đó là đòi **khớp mờ** — thứ Phase 6.6 đã cấm.
- Hậu tố `_pt` do tôi bịa, không nằm trong `_PHU_TO_KIEU`. Thêm nó vào là *"alias
  thủ công theo lỗi"*. Nay hậu tố **dẫn từ chính danh sách ấy**, có test khẳng
  định.

Bất biến kiểm **các cổng có nhất quán với nhau không**, không kiểm lưới phủ bao
nhiêu cách viết. Hai câu hỏi khác nhau; câu sau bị chặn bởi bằng chứng.

---

## 3. Bản vá ② — gap của DSL 2D không được chặn hình học

`known_gap_roles()` dẫn từ `manifest.py`: *"vai trò mà **không primitive thị
giác** nào cover"*. Câu ấy đúng **về DSL 2D**. Đường sinh hình học **không đi qua
DSL** — nó chạy trên kernel hữu tỉ. Áp danh sách ấy cho nó là áp giới hạn của một
engine lên một engine khác.

```
5-goc lượt 2 (7A):  12.5s · không chương trình
  "Bài cần cơ chế chưa có engine tất định sở hữu (geometric_perpendicular)"
```

…trong khi kernel có `P.perpendicular_lines` từ Wave 1. Và nó **không tất định**:
cùng một đề, lượt 1 và 3 qua, lượt 2 trượt — tuỳ `analyze` có khai vai trò ấy
không. Nên nó vào báo cáo như *"mô hình không làm được"*.

### **Không miễn trừ cả miền** — chỗ quan trọng nhất của bản vá

Kernel **không** sở hữu `geometric_circle` và `geometric_locus`: nó dựng trên
`Fraction` và đa diện, mặt cong không nằm trong mô hình
(`GEOMETRY_CURRICULUM_COVERAGE` #19, #20 đều ghi **KHÔNG**).

Miễn trừ cả gói thì một đề mặt cầu **đi thẳng vào sinh**, tiêu ~5 lượt LLM rồi
hỏng muộn — hoặc tệ hơn, dựng một khối đa diện *"gần giống"* và học sinh tin nó.
Từ chối sớm ở đó mới là hành vi trung thực.

```
GEOMETRY_OWNED_GAP_ROLES = {
    geometric_perpendicular   ← predicates.perpendicular_lines
    geometric_intersection    ← kernel.intersect_line_plane / _plane_plane / _line_line
    geometric_projection      ← kernel.project_point_onto_plane / _line
}
```

Mỗi vai trò có test **đối chiếu hàm kernel thật**; một test khẳng định tập miễn
trừ là **tập con thật sự** của tập gap (bằng nhau thì nó là *"tắt cổng cho hình
học"*, một câu khác hẳn); và `domain=None` giữ nguyên hành vi Tin học — có test
cho **từng** vai trò.

---

## 4. Lượt trượt còn lại — **model generation**

```
3-pmn-giao-tuyen lan3 · execution
GEOMETRY_OPERAND_TYPE: điểm 'P' là NoneType, cần Vec3
thu_that_bai = 0
```

Chương trình dùng `P` **trước khi dựng nó** — lỗi thứ tự, thuộc mô hình. Hợp
đồng có đường đúng đang mở và mô hình đã đi đúng ở hai lượt kia.

⚠️ **Quan trắc cấu trúc, KHÔNG sửa trong pha này** (đã ghi ở Phase 6.7.2, nay
tái hiện): lỗi nổ ở `execution`, tức **sau** vòng sửa. Lỗi validator đi ngược cho
mô hình sửa (≤3 lượt); lỗi runtime thì không — `thu_that_bai = 0`, không một lần
thử lại nào, dù thông báo đã nói đúng chỗ sai.

---

## 5. ⚠️ `obligation_match` của bài 3 — kỳ vọng của **tôi** sai, không phải mô hình

```
7A     nv = 1 · 2 · 0          om 1/3
7A.1   point_on_line(AD, Q)
       point_on_line(d,  Q)    om 0/3
       point_on_line(AD, Q)
```

Ba lượt sau sửa khai **một bộ nghĩa vụ nhất quán và hợp lý**. Kỳ vọng tôi đặt
trong bộ đo là `{point_on_line, point_on_plane}` — và nay đã có **8 lượt liên
tiếp** (5 ở Phase 6.7.2 + 3 ở đây) bác bỏ nó theo **cùng một hướng**.

Đọc lại đề thì mô hình có lý: *"Hãy dựng mặt phẳng (PMN)"* là một **mệnh lệnh
dựng**, không phải một **mệnh đề cần chứng minh**; `point_on_plane` cần một
witness mà đề không hỏi điểm nào thuộc `(PMN)`.

Đây chính là **điều kiện ⑨** đã nêu ở Phase 6.8: *kỳ vọng nghĩa vụ phải đến từ
nguồn ngoài, không do người đo tự đặt*. Con số `0/3` ở đây **không** được đọc
thành *"mô hình sai"* — nó là bằng chứng cho điều kiện ⑨, và nó là lý do Phase 7B
không được để tôi tự đặt kỳ vọng.

---

## 6. Kết luận

Hai bản vá làm đúng việc và **chỉ** việc ấy:

- nhóm **validator** và **routing** về **0**
- nhóm **model** giữ nguyên **1** — pha này không nâng năng lực sinh, và số cho
  thấy đúng như vậy
- `construction_validity` giữ **0% literal substitution** (nay **0/390 vật** qua
  năm vòng đo) và lên **100% witness dẫn xuất**

Điều còn lại trước Phase 7B **không nằm ở code**: kỳ vọng nghĩa vụ phải đến từ
nguồn ngoài. `HOLDOUT_PROTOCOL §2` đã có cơ chế, và nó vẫn **chặn cứng ở seed của
GVHD**.

**Không kết luận gì về chất lượng mô hình từ mẫu này** — 15 lượt trên năm đề tôi
tự chọn, ba trong số đó đã bị nhìn suốt tám wave.

---

## Chi phí

15 lượt × ~6 lượt LLM ≈ **90 lượt**. Hai bản vá được chứng minh **0 API call** —
tái hiện bằng chính IR đã lưu ở `phase7a-pilot/`.

Artifact: `phase7a-pilot-sau-71/` (15 file). Artifact trước sửa giữ nguyên ở
`phase7a-pilot/` — bộ đo **từ chối ghi đè** thư mục đã có bản ghi.
