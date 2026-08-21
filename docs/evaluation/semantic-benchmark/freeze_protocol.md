# Freeze protocol

## Đóng băng TRƯỚC khi seal — không sửa về sau

- eligibility rubric (`eligibility_rubric.md`)
- **N** và cách lấy mẫu
- primary metrics — **A và B ĐỒNG-primary**
- assurance policy (thanh STRONG/WEAK cố định)
- ground-truth procedure
- cách tính refusal / success
- các trường hợp bị loại khỏi thống kê
- obligation taxonomy (chọn từ **DEV**)

## Không đặt pass mark tuỳ tiện

**KHÔNG** ghi kiểu *"≥80% thì luận văn thành công"* khi chưa có cơ sở nào để
chọn con số đó. Luận văn **báo kết quả như nó là**. Thứ phải đóng băng là **CÁCH
ĐO**, không phải mức điểm mong muốn.

## Release cho học sinh — tiêu chuẩn KHÁC

Canonical case **biết là sai** → **FAIL RELEASE**. Tuyệt đối **không** hạ thanh
assurance để tỉ lệ đẹp hơn.

## Hai chỉ số báo riêng

```
Generative executability rate   ≠   Safe serve rate
```

A hỏi *kiến trúc có thoát module-per-problem không*; B hỏi *bao nhiêu trong số
đó đủ bằng chứng để sản phẩm thật sự dùng được*. Khoảng cách A − B là chỗ đáng
phân tích, không phải chỗ để giấu.

## Chống rủi ro safe-serve ≈ 0 — làm trên DEV, TRƯỚC seal

Thống kê các **lớp nghĩa vụ thực tế** xuất hiện trong bài thuật toán THPT, chọn
một tập checker **nhỏ, đại diện**, rồi **đóng băng taxonomy trước SEALED**.
**Không** thêm checker để cứu từng held-out case.

---

# Bổ sung 2026-08-21 — KHOÁ TRƯỚC KHI MỞ SEALED

Ba luật dưới đây chốt **trước khi nhìn thấy bất kỳ kết quả nào**. Đó là toàn bộ
giá trị của chúng: một ngưỡng đặt sau khi biết số thì không còn là ngưỡng.

## 1. Evaluation candidate — danh tính bản được đo

`EVALUATION_CANDIDATE.json`, sinh bằng `backend/scripts/freeze_evaluation_candidate.py`.
Ghi: commit · `CACHE_VERSION` · hash taxonomy (9 nghĩa vụ) · hash tập primitive
(8, có `graph_view`) · hash schema IR · fingerprint DEV · thời điểm đóng băng.

Mọi giá trị **dẫn xuất từ nguồn**, không chép tay — chép tay thì manifest trôi
khỏi mã đúng như bảng danh tính từng trôi ở `CURRENT_STATE.md`.

> **KHÔNG sửa candidate vì kết quả SEALED.** Kiểm bằng
> `freeze_evaluation_candidate.py --verify`; lệch ⇒ thoát != 0.

### Hệ ĐƯỢC ĐO ≠ BỘ ĐO

Artifact Task 12 ghi riêng `measured_system_candidate` và
`evaluation_harness_commit`. Harness (runner · validator · test instrumentation)
được phép cứng cáp thêm **trước** SEALED mà **không** phải đóng băng lại
candidate, miễn thay đổi ấy không đụng vào **ngữ nghĩa** của hệ được đo — tức
không chạm prompt · schema · taxonomy · primitive · route · checker.

Ranh giới kiểm được: `--verify` chỉ so taxonomy · tập primitive · schema · DEV ·
`CACHE_VERSION`. Thêm một test hay siết một thông báo lỗi thì `--verify` vẫn
khớp; đổi một trong năm thứ trên thì nó đỏ. Đó chính là định nghĩa vận hành của
"không đụng ngữ nghĩa".

## 2. Ngân sách Task 12 — chốt cứng, không nâng sau khi thấy số

```
N (SEALED)                    = 40
Trần lượt logic               = 440    (= 11 × 40, CƯỠNG CHẾ không chỉ đếm)
Trần lần thử HTTP             = 520    (~18% headroom cho transient)
```

> **Chốt 2026-08-22, TRƯỚC khi custodian niêm phong và trước khi nhìn một case
> SEALED nào.** Hai trần này **không được nâng sau khi SEALED được mở**.

`440` **không** có nghĩa hệ được phép "thử 11 lần cho đẹp". Mỗi stage vẫn giữ
nguyên retry bound riêng đã định nghĩa trong production code từ trước
evaluation; 440 chỉ là **tổng trần** của những đường retry/reclassify đã tồn
tại, nhân với `N_planned`.

`520` cho ~18% headroom trên logical worst-case, **chỉ để chịu transient
HTTP** (429/5xx). Vượt vẫn là `BUDGET_EXHAUSTED`, `evaluation_complete=false`,
và **không chạy bù**.

### Upper bound thật — dẫn từ call graph, không ước lượng

```
stage_analyze            _call_json(retries=1)          → tối đa 2
stage_classify lần 1     _call_json(retries=1)          → tối đa 2
one-route recovery       thêm một stage_classify        → tối đa 2
stage_semantic_analyze   không retry                    → 1
stage_semantic_program   không retry                    → 1
stage_simulate*          for _attempt in range(3)       → tối đa 3
                                                          ─────────
                                                          tối đa 11
```

Đường **hạnh phúc** là 4 (`analyze` + `classify` + `semantic_analyze` +
`semantic_program`). Bốn **không phải bound** — 11 mới là.

> **Vì sao trần cũ 160 bị bỏ.** 4 × 40 = 160 đúng bằng trần, nên **một lần retry
> duy nhất ở bất kỳ đâu** cũng đủ làm lượt chạy dừng trước case thứ 40. Khi
> `N=40` đã là mục tiêu nghiên cứu khoá thì một ngân sách như thế **xung đột với
> protocol**, chứ không còn đơn thuần là tiết kiệm quota. Trần phải phủ **worst
> case**, không phải best case. Sửa ngày 2026-08-22, trước khi thấy bất kỳ kết
> quả SEALED nào — hợp lệ về phương pháp, và là lần cuối.

Cưỡng chế nằm ở `ApiBudget(max_api_calls=…, max_logical_calls=…)`. Trước
2026-08-21 chỉ có trần HTTP, nên số lượt logic có thể vượt xa ngân sách mà không
gì chặn: đếm mà không chặn thì con số ngân sách chỉ là lời chúc.

> **Vì sao đường hạnh phúc là 4 chứ không phải 3 (sửa 2026-08-21, TRƯỚC khi thấy
> bất kỳ kết quả nào).** Route cần `semantic_analyze` dựng `RequestContract`
> **và** `semantic_program` viết IR. Gộp hai lượt ấy làm một thì cùng một lượt
> sinh ra cả nghĩa vụ lẫn chương trình, nên mô hình chỉ việc khai nghĩa vụ nào mà
> chương trình nó vừa viết đã thoả — C₁a còn đúng hình thức nhưng không kiểm được
> gì. Đây là sửa **số học của thiết kế**, không phải nới trần vì số xấu: lúc sửa
> chưa có một case SEALED nào được chạy. Luật "không nâng sau khi thấy số" vẫn
> nguyên vẹn và từ đây trở đi là tuyệt đối.

Trần HTTP rộng hơn trần logic **chỉ để chịu lỗi tạm thời**, KHÔNG phải để dò
tìm kết quả tốt hơn.

> Vượt trần ⇒ **dừng evaluation** và ghi `BUDGET_EXHAUSTED`. **Không nâng trần
> sau khi đã thấy kết quả** — làm thế là mua thêm lượt cho tới khi số đẹp.

## 3. D2 — matched subset chọn TẤT ĐỊNH, không chọn theo kết quả

D2 (claim token thực nghiệm) chỉ đo trên các case **cả hai route đều phục vụ
thành công**. Quy tắc chọn, chốt tại đây:

1. Lấy tập giao (cả hai route đều `ok`).
2. Sắp theo `case_id` (thứ tự từ điển) — tất định, không phụ thuộc kết quả.
3. Nếu tập giao > 12: lấy **phân tầng đều** — chỉ số
   `round(i * (n - 1) / 11)` với `i = 0..11`, khử trùng.
4. Báo **RIÊNG** ba con số: semantic cost · legacy cost · shadow cost.

> Không có chuyện thấy case nào đẹp rồi mới chọn để so token. Ai đọc quy tắc này
> cũng dựng lại được đúng tập ấy mà không cần chạy hệ.

Nhắc lại từ §D1: claim **cấu trúc** (sau khi IR đã sinh, số bước runtime không
tiêu thêm token LLM) đúng theo cấu tạo và **không cần** matched subset. Chỉ D2
mới cần.
