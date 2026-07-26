# M17 W2C-LIVE — Live smoke `algorithm.bounded_control_flow`

Hai lượt live đã chạy. **Lượt 2 (W2C-C1) là lượt hiện hành.**

---

## Lượt 2 — sau W2C-C1 (2026-07-26, HEAD `238a8a0`)

> ## `W2C_LIVE_INCOMPLETE`
>
> Chạm trần **12/12 HTTP** trước khi chạy được case thứ tư. Theo §4/§14 → **dừng,
> KHÔNG nâng ngân sách, KHÔNG chạy lần hai.** **Wave 2C KHÔNG được đóng.**

### Runtime identity (§14)

| | |
|---|---|
| runtime doctor | **PASS** — `ok: true`, `findings: []` (`runtime_identity_w2c_c1.json`) |
| `CACHE_VERSION` | **22** (source ≡ runtime) · family/target **11 / 21** |
| catalog fingerprint | source ≡ runtime |
| `classify.md` | đã nạp bản mới (quy tắc `2h` có mặt) |
| Model | `gemini-2.5-flash` |

> **Doctor đã bắt được một ca stale thật:** lượt khởi động đầu, một tiến trình
> uvicorn từ checkpoint trước còn giữ cổng 8000 nên bản mới không lên được;
> doctor báo `CACHE_VERSION_MISMATCH` (runtime 21 ≠ source 22) và
> `CATALOG_HASH_MISMATCH`. Đã dọn tiến trình cũ, khởi động lại, doctor PASS rồi
> mới chạy live. **Không dùng kết quả từ tiến trình cũ.**
>
> Docker **không khả dụng** ⇒ **không claim container parity**.

### Kết quả

| Case | HTTP | Kết quả | Lỗi validator (lặp lại mọi lượt) |
|---|---|---|---|
| CF-1 gán + if/else | 5 | **FAIL_SAFE** | `Câu lệnh không nằm trong chương trình: s3.` |
| CF-2 while có biên | 5 | **FAIL_SAFE** | `Vòng lặp 'main_loop' phải có ít nhất một câu lệnh trong thân.` |
| CF-3 thiếu dữ kiện | 2 | **từ chối ĐÚNG** (assertion nhãn báo FAIL) | — |
| CF-4 hàm/đệ quy | 0 | **KHÔNG CHẠY** (cạn ngân sách) | — |

**An toàn giữ nguyên:** unsafe acceptance **0** · generic leak **0** · result leak
**0** · semantic loss **0**.

### L1 và L2 ĐÃ ĐẠT MỤC TIÊU — lỗi dịch sang tầng khác

Hai lỗi gốc của lượt 1 **biến mất hoàn toàn**:

- ~~`Biến 'y' khai kiểu số nguyên nên cần 'int_value'`~~ → **hết**. Gemini nay
  khai được biến chưa khởi tạo, không phải bịa giá trị đề không cho.
- ~~`Biểu thức 'e4_compare_x_lt_5' cần 'left' và 'right' là id`~~ → **hết**.
  Biểu thức inline được điền đúng.

Lỗi mới **cùng MỘT lớp, khác đối tượng**: model dựng câu lệnh trong
`statements[]` nhưng **không nối được vào cấu trúc khối** —
CF-1 để câu lệnh `s3` mồ côi (không nằm trong `main` hay khối nào),
CF-2 để `body: []` trong khi câu lệnh thân đã tồn tại.

> Nói thẳng: L2 gỡ gánh nặng "bảng + tham chiếu id" cho **biểu thức**, nhưng
> **câu lệnh vẫn dùng đúng cơ chế đó** (`main`, `then_body`, `else_body`,
> `body` đều là danh sách id). Đây chính là gánh nặng biểu diễn còn lại, và nó
> là **thiết kế hợp đồng**, không phải thứ vá bằng retry.

### L3 đúng thiết kế nhưng KHÔNG kích hoạt ở ca live này

CF-3 vẫn `failure_category = None`. Lý do đo được: `_refusal_category` suy nhãn
từ `prescribed_procedure` mà **analyze không khai cơ chế** cho đề này, nên không
có căn cứ → theo đúng luật đã đặt, hệ **để trống thay vì đoán**.

Bản vá vẫn đúng và có test khoá cả hai chiều (BE 3 test, FE 3 test); nó phủ ca
analyze CÓ khai cơ chế. Ca live này rơi ngoài vùng phủ đó. **Không nới luật để
ép đạt** — nới ra là quay lại gán nhãn theo phỏng đoán.

Thông điệp học sinh vẫn **tốt và đúng bản chất**:

> *"Đề bài yêu cầu mô phỏng vòng lặp while nhưng không cung cấp giá trị ban đầu,
> điều kiện lặp và thân vòng lặp cụ thể. Hệ thống không thể tự bịa ra một chương
> trình…"*

### Phát hiện còn mở (phân loại §9 — KHÔNG tự vá)

| # | Phát hiện | Phân loại |
|---|---|---|
| C1-1 | Câu lệnh vẫn nối khối bằng **danh sách id** (`main`/`then_body`/`body`); model để câu lệnh mồ côi hoặc `body` rỗng | **Contract ergonomics** — cùng lớp với L2, chưa xử lý |
| C1-2 | `_refusal_category` không phủ ca analyze **không khai cơ chế** | **Vùng phủ hẹp** của bản vá L3 |

---

## Lượt 1 — trước W2C-C1 (HEAD `2d17405`) — LƯU LÀM ĐỐI CHỨNG

`W2C_LIVE_INCOMPLETE`, 12/12 HTTP, 3/4 case. CF-1 hỏng ×3 vì
`Biến 'y' … cần 'int_value'`; CF-2 hỏng ×3 vì `e4_compare_x_lt_5 cần left/right`.
Chính hai lỗi này là đầu vào của checkpoint C1. An toàn khi đó cũng đã đạt:
unsafe acceptance 0 · generic leak 0 · result leak 0 · semantic loss 0.

---

## Trạng thái Wave 2C

- Offline deterministic execution: **verified** (pytest 1065 · vitest 638).
- Chrome visual review: **completed** (7 REAL_VISUAL · 1 PARTIAL · 0 BROKEN).
- Live Vietnamese NL smoke: **INCOMPLETE — chưa đạt** (2 lượt).

⇒ **Wave 2C KHÔNG CLOSED.** Claim đúng độ mạnh: *engine tất định và renderer đã
kiểm chứng; tích hợp ngôn ngữ tự nhiên **PARTIAL**; hệ **từ chối an toàn** khi
không dựng nổi spec.* Không được viết "live fully verified".

VR-O1 giữ nguyên limitation: chương trình một câu lệnh chưa có trạng thái
tiền-thực-thi; **không sửa `TraceBuilder`**.
