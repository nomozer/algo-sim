# HỢP ĐỒNG CHỈ SỐ CHO PHASE 7 — chốt trước, không sửa sau khi thấy số

> Chốt ở Phase 6.8, **trước** khi tiêu call đầu tiên của benchmark. Đổi định
> nghĩa một chỉ số sau khi đã thấy kết quả là chọn thước theo điểm — nên mọi
> thay đổi sau mốc này phải nói ra trong báo cáo, kèm số cũ.

---

## 1. Năm chỉ số, và mỗi cái trả lời một câu hỏi KHÁC NHAU

| | Chỉ số | Câu hỏi nó trả lời | Đơn vị |
|---|---|---|---|
| ① | `served` | Hệ có phát ra một mô phỏng không? | `x/k` mỗi đề |
| ② | `oracle` | Mô phỏng ấy có **đúng** không? | `x/k` mỗi đề |
| ③ | `obligation_match` | Hệ có **tự biết** mình đúng không? | `x/k` mỗi đề |
| ④ | `construction_validity` | Nó **dựng hình** hay **khai kết quả**? | tỉ lệ trên tổng vật |
| ⑤ | `stability` | Lặp lại có ra cùng kết quả không? | `k` lượt / đề |

**KHÔNG GỘP.** Mỗi chỉ số đo một thứ khác nhau và chúng **đã đi ngược chiều
nhau** trong dữ liệu thật:

```
Phase 6.7.2, bài thiết diện:   served 5/5   ·   obligation_match 0/5
```

Báo `served` một mình ở đó là nói quá về năng lực hệ. Bốn trong năm lượt ấy dựng
đúng hình mà **không kiểm gì cả**.

---

## 2. Định nghĩa chính xác

### ① `served`

`SemanticRouteOutcome.servable == True` **và** envelope mang
`simulation_id == "generic.semantic_program"`.

Đây là chỉ số **yếu nhất** trong năm, và phải luôn đọc kèm ③.

### ② `oracle`

Đối chiếu với đáp án **độc lập**, so **QUAN HỆ / ĐẠI LƯỢNG**, không so toạ độ —
mô hình tự chọn hệ trục nên toạ độ không phải bất biến.

```
thể tích         phân số đúng bằng đáp án
khoảng cách      phân số (hoặc bình phương, khai rõ đơn vị)
góc              cos²
quan hệ          true / false
vị trí đặc biệt  bất biến tỉ lệ, vd "Q là trung điểm AD"
```

Ba trạng thái, **không phải hai**: `True` (đạt) · `False` (chấm được, trượt) ·
`None` (**không chấm được**). Gộp `None` vào `False` là ghi một lượt không đo
được thành một lượt sai.

### ③ `obligation_match`

Tập `kind` mà `RequestContract` khai **bằng đúng** tập kỳ vọng của đề. Bằng
**đúng**, không phải "có giao nhau": đề hỏi hai loại mà hợp đồng khai một thì
nửa còn lại không ai kiểm.

> ⚠️ **Kỳ vọng phải đến từ NGUỒN NGOÀI.** Điều kiện này lộ ra ở Phase 6.7.2: kỳ
> vọng tôi tự đặt cho bài thiết diện bị **5/5 lượt** bác bỏ theo một hướng nhất
> quán, và đọc lại đề thì mô hình có lý. Nếu tôi tự đặt kỳ vọng, mọi chỗ tôi đọc
> đề khác mô hình sẽ được ghi thành *"mô hình sai"*.
>
> Cùng lớp vấn đề với việc tự soạn held-out, và `HOLDOUT_PROTOCOL §2` đã có cơ
> chế: **đáp án và yêu cầu đến từ nguồn ngoài, người đo không sửa được**.

Kèm luôn `so_nghia_vu` thô. `so_nghia_vu = 0` là ca **đặc biệt phải nêu riêng**:
`served` khi ấy nghĩa là *"chạy trọn và mọi thứ lên được hình"*, **không** phải
*"đáp án đã được đối chiếu"*.

### ④ `construction_validity` — chỉ số MỚI, chốt ở Phase 6.8

Đo **cấu trúc chương trình**, không đo pass/fail. Ba số, không gộp:

```
literal_substitution   vật ĐÁNG LẼ PHẢI DỰNG mà khai sẵn:
                       · witness khai bằng `initial_value`  → khai ĐÁP ÁN
                       · line3/plane3/solid/polygon3 khai `initial_value`
                                                            → khai sẵn HÌNH
                       MỤC TIÊU: 0%

dependency_construction  vật sinh ra từ một phép dựng đọc TÊN vật khác

witness_derived        witness nằm trong tập vật được dựng/đo
                       MỤC TIÊU: 100%
```

**Mẫu số là phần đáng lẽ phải dựng, KHÔNG phải tổng khai báo.** Chia cho tổng
thì chương trình khai nhiều **điểm gốc** tự động "tệ" đi — mà điểm gốc là **dữ
kiện**, không phải kết quả. Điểm gốc khai toạ độ kèm `model_assumption` là hành
vi **đúng**: đề hình học không cho toạ độ và prompt bảo mô hình tự đặt hệ trục.

Kèm `do_sau_max` (chuỗi phụ thuộc dài nhất) — nó phân biệt *"dựng một bước"* với
*"dựng theo dây"*, và Phase 5G từng đo trần 2 do hợp đồng.

Công cụ: `scripts/analyze_construction_dependency.py`, **0 API call**, chạy trên
artifact đã lưu.

### ⑤ `stability`

**Mỗi đề chạy `k ≥ 3` lượt độc lập.** Báo cáo là `x/k`, **không phải pass/fail**.

Lý do có điều kiện này, đo được: cùng một mã, cùng ba đề, hai lượt liên tiếp cho
**0/3 rồi 3/3** (Phase 6.6). Một lượt duy nhất sẽ cho một con số mà lượt sau bác
bỏ.

Kèm **phân bố**, không chỉ tỉ lệ: `so_nghia_vu` của bài thiết diện dao động
`0 · 1 · 2 · 3 · 4` trên cùng một đề, và chính phân bố ấy — chứ không phải trung
bình — là phát hiện.

---

## 3. Phân loại thất bại — bốn nhóm, ĐÓNG

| | Nhóm | Ghi vào đây khi |
|---|---|---|
| 1 | **model generation** | chương trình sai mà hợp đồng có đường đúng đang mở |
| 2 | **contract** | hợp đồng **không diễn đạt được**, hoặc **cho phép** thứ engine cấm |
| 3 | **validator** | chương trình đúng mà cổng từ chối |
| 4 | **routing** | không tới được route sinh |

**Nhóm 2 và 3 chỉ ghi khi CHỨNG MINH ĐƯỢC.** Cách chứng minh đã dùng hai lần và
là chuẩn cho Phase 7: **chạy lại chính IR đã lưu** sau khi sửa, không sửa một ký
tự nào của chương trình. Qua ⇒ lỗi thuộc hệ. Không qua ⇒ thuộc mô hình.

Phân biệt này không phải chữ nghĩa. Ghi một lỗi validator vào nhóm 1 thì luận
văn báo một con số **thấp hơn thực tế** *và* **kết tội mô hình ở đúng chỗ nó làm
đúng** — đã xảy ra một lần (Phase 6.7, 2/15 lượt).

---

## 4. Điều báo cáo Phase 7 KHÔNG được làm

- **Không** báo `served` mà thiếu `obligation_match`.
- **Không** gộp `oracle = None` vào `False`.
- **Không** báo pass/fail cho một đề chạy `k` lượt.
- **Không** dùng kỳ vọng nghĩa vụ do người đo tự đặt.
- **Không** đổi định nghĩa chỉ số sau khi thấy số; đổi thì phải nói ra kèm số cũ.
- **Không** suy tỉ lệ khi mẫu `< 20` (`RELIABILITY_EVALUATION_PLAN §3.3`) — dưới
  ngưỡng ấy con số đọc là **đếm thô**.

---

## 5. Trạng thái các chỉ số ở mốc chốt

Đo trên `stability-6.7` + `stability-6.7.2`, 30 chương trình:

| Chỉ số | Giá trị |
|---|---|
| `served` | 9/15 → **14/15** (sau Phase 6.7.1) |
| `oracle` | 9/15 → **14/15** |
| `obligation_match` | 11/15 → 10/15 |
| `construction_validity` · literal_substitution | **0/231 = 0.0%** |
| `construction_validity` · dependency_construction | **209/231 = 90.5%** |
| `construction_validity` · witness_derived | **27/27 = 100%** |
| `construction_validity` · do_sau_max | **1 – 4** |
| `stability` | k = 5, hai vòng độc lập |

Đây là **đường cơ sở**, không phải mục tiêu. Phase 7 đo trên tập held-out, và số
của tập DEV không bao giờ là số của luận văn.
