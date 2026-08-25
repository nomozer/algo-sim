# WAVE 3 — AUDIT TRƯỚC KHI SỬA

Nguồn: `PHASE5_GEOMETRY_RESULT.md` + `dev-results/geometry_dev_results.json`
(commit đo `027c9e1`, cây sạch). Mọi khẳng định dưới đây **đọc từ artifact**,
không suy diễn — chỗ nào phải suy thì ghi rõ.

---

## 1. Bốn lỗi — xác nhận

| # | Lỗi | Bài | Tầng | File liên quan | Phạm vi sửa |
|---|---|---|---|---|---|
| 1 | `input_not_grounded` | geo_03 · 05 · 06 · 07 · 08 · 09 | 6 · grounding | `grounding_gate.py` | **PRODUCT** |
| 2 | `requested_operation_uncovered` | geo_01 · geo_02 | 6 · C₁a | `coverage_gate.py` · `route.py` | **PRODUCT (chỉ chẩn đoán)** |
| 3 | `semantic_program_invalid` | geo_10 | 2 · schema | `contract.py` | *không sửa wave này* |
| 4 | thiếu `RequestContract` trong artifact | mọi bài | harness | `run_geometry_dev_evaluation.py` | **HARNESS** |

Cộng hai lỗi harness đã tự khai ở §6 báo cáo Phase 5: `chi_phi.do_tre = {so_luot: 0}`
và `failure_reason` là chuỗi trần, mất `details`.

## 2. Lỗi 1 — nguyên nhân đọc được từ vật chứng

Chạy lại `check_grounding` **offline, 0 API call**, trên IR đã lưu:

```
geo_09  7 khai báo · 5 có model_assumption · giả thiết ĐƯỢC NHẬN: 1
  B: source_fact_id 'canh_day'        không có trong RequestContract
  D: source_fact_id 'canh_day'        không có trong RequestContract
  C: source_fact_id 'abcd_hinh_vuong' không có trong RequestContract
```

Mô hình **dùng `model_assumption` đúng** (5/5 điểm gốc), rồi gắn *thêm*
`source_fact_id`. Luật Wave 2 — *"`source_fact_id` VẪN THẮNG khi khai cả hai"* —
biến một trích dẫn không giải được thành **lỗi chí mạng**, dù bản thân khai báo
đã được biện minh bằng một cơ chế độc lập và đã kiểm.

**Mức chắc chắn: CAO.** Đây là đọc trực tiếp từ `generated_program`.

## 3. Lỗi 2 — nguyên nhân **CHƯA xác nhận được**

```
geo_02  khai: A B C D S a b giao_tuyen_sab_abcd plane_abcd plane_sab
        tạo : a b giao_tuyen_sab_abcd plane_abcd plane_sab
```

Chương trình tạo ra **mọi thứ nó khai mà không phải điểm gốc**, C₁a vẫn từ chối.
Suy ra: tên `witness` do lượt `analyze` chọn không nằm trong chương trình.

**Mức chắc chắn: TRUNG BÌNH — và đây là lý do TASK 4 bị hoãn.** Artifact không
lưu `RequestContract`, nên **không đọc được tên witness thật**. Kết luận trên là
suy từ dấu vết.

---

## 4. Ba phản biện — nói trước khi sửa

### ① TASK 2 như đặc tả sẽ **mở lại đúng cái lỗ P2 sinh ra để bịt**

Đặc tả đề nghị khớp theo `semantic_type` → `entities` → `attributes` → rồi mới
`source_fact_id`. Vấn đề: **ai sinh ra `semantic_type`?** LLM. Cả hai phía của
phép khớp đều do cùng một model đặt tên, nên "semantic match" là model tự đối
chiếu nhãn của chính nó — đúng chế độ hỏng mà `RequestContract` được dựng ra để
chặn (`request_contract.py` docstring: *"nó KHÔNG chặn được việc cùng một model
hiểu sai đề một cách nhất quán ở cả hai lượt"*).

`grounding_gate.py` còn từ chối tường minh chính hướng ấy:

> *"Cố ý KHÔNG làm kiểu 'tìm xem giá trị này có xuất hiện đâu đó trong hợp đồng
> không' — khớp theo giá trị đơn thuần dễ trùng ngẫu nhiên, và cho qua cả trường
> hợp khai sai nguồn."*

Rủi ro cụ thể, không trừu tượng: một biến `float` giữ `2/3` sẽ khớp một fact có
`semantic_type: volume` — tức **đường thẳng để tuồn đáp án vào**, đúng thứ TASK 3
cùng wave này yêu cầu chặn.

Thêm nữa, `semantic_type`/`entities`/`attributes` chưa tồn tại ở đâu cả. Muốn có
phải mở rộng schema `analyze` **và** thẻ văn phạm ⇒ đổi prompt ⇒ bump
`CACHE_VERSION` ⇒ và đẻ một bề mặt khớp mới **do LLM sở hữu**.

**Tôi làm bản AN TOÀN, giữ nguyên mục tiêu:**

1. Chuẩn hoá id **tất định** (bỏ dấu, thường hoá, gộp `-_ `) — `canh_day` ≡
   `CANH-DAY` ≡ `cạnh_đáy`. Không có phán đoán ngữ nghĩa nào.
2. **Trích dẫn không giải được KHÔNG chí mạng nếu khai báo đã có
   `model_assumption` hợp lệ** — vì kênh giả thiết đã có ba khoá riêng (chỉ
   `point3`/`vector3` · không bao giờ là witness · phải có lý do). Id ấy hạ
   xuống `unresolved_citation`, **ghi vào artifact**, không giết chương trình.
3. Không có `model_assumption` ⇒ **nghiêm ngặt y như cũ**. Một `float` với
   `source_fact_id` bịa vẫn chết.

Bản này gỡ đúng 6 ca đã đo mà **không** cho phép bất kỳ đường nào tuồn đáp án.

### ② TASK 4 **thiếu bằng chứng để thiết kế** — hoãn phần nới, làm phần đo

Không đọc được tên witness thật (§3). Thiết kế một bộ khớp "semantic producer"
dựa trên một suy đoán, mà lại là bộ khớp **làm yếu một cổng an toàn**, là đúng
thứ tự sai: *đoán → nới cổng → mất khả năng phát hiện*.

Ngoài ra `_obligations_for_prompt` **đã** truyền `container`/`witness` sang lượt
viết chương trình kèm câu *"cả hai tên phải có mặt, đúng từng chữ"*. Nếu mô hình
vẫn lệch thì có ba khả năng — model bỏ qua chỉ dẫn · analyze đặt tên không dùng
được làm định danh · một lỗi khác hẳn — và **ba khả năng ấy cần ba cách sửa khác
nhau**. Chọn bừa một là sửa nhầm bệnh.

**Tôi làm phần đo:** C₁a nay phát ra **tên witness + tập biến được tạo ra** vào
`details`. Lượt Phase 5.5 sẽ nói thẳng cái gì lệch, thay vì để suy. Không nới
cổng một milimét.

### ③ Lỗi 3 (geo_10) — **không sửa wave này**, và có lý do

Mô hình viết `through: {"kind":"literal","value":["A","B","C"]}` thay vì
`["A","B","C"]` — lớp lỗi *hình dạng wire*, cùng họ ba lớp `canonical_*` đã mở ở
miền Tin học. Vá được bằng một `BeforeValidator` mở gói.

Nhưng đó là **nới hợp đồng dựa trên MỘT quan sát**. `RULES §3c` gọi tên chế độ
hỏng ấy: vá theo từng ca đã thấy. Ghi vào `POST_THESIS_BACKLOG` và chờ xem
Phase 5.5 nó có lặp lại không — một lần là giai thoại, hai lần là lớp lỗi.

---

## 5. Phạm vi wave này

| Task | Việc | Loại |
|---|---|---|
| 1 | `request_contract` vào artifact | HARNESS |
| 2 | chuẩn hoá id + assumption fallback (**bản an toàn**) | PRODUCT |
| 3 | ranh giới giả thiết vs đáp án — đã có ở Wave 2, bổ sung test | TEST |
| 4 | C₁a phát `details` (**chỉ đo, không nới**) | PRODUCT |
| 5 | `failure` thành object `{code, reason, details, layer}` | HARNESS |
| 6 | `do_tre` cấp lượt | HARNESS |

**Không đụng:** dataset · oracle · taxonomy · primitive · renderer · prompt.
