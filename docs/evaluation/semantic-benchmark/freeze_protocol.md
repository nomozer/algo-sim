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

## 2. Ngân sách Task 12 — chốt cứng, không nâng sau khi thấy số

```
N (SEALED)                    = 40
Lượt LLM logic / case         ≤ 4      (analyze + classify + semantic_analyze
                                        + semantic_program)
Trần lượt logic               = 160
Trần lần thử HTTP             = 200    (chừa cho retry/transient)
```

> **Vì sao 3 → 4 (sửa 2026-08-21, TRƯỚC khi thấy bất kỳ kết quả nào).** Bản đầu
> đếm thiếu một lượt: route cần `semantic_analyze` dựng `RequestContract` **và**
> `semantic_program` viết IR. Gộp hai lượt ấy làm một thì cùng một lượt sinh ra
> cả nghĩa vụ lẫn chương trình, nên mô hình chỉ việc khai nghĩa vụ nào mà chương
> trình nó vừa viết đã thoả — C₁a còn đúng hình thức nhưng không kiểm được gì.
> Đây là sửa **số học của thiết kế**, không phải nới trần vì số xấu: lúc sửa
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
