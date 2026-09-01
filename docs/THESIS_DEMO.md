# THESIS_DEMO — kịch bản trình bày

> **Đây là sổ tay TRÌNH BÀY.** Bằng chứng và diễn giải số liệu thuộc
> `docs/THESIS_READINESS.md` (§5 tập demo, §6 smoke trình duyệt) — ở đây không
> chép lại số. Kiến trúc: `docs/THESIS_ARCHITECTURE.md`.
>
> **Không có bài demo nào được dựng mới cho tài liệu này.** Cả sáu ca đều lấy
> từ artifact live đã commit, có xuất xứ rõ, và chạy lại được với **0 lượt gọi
> model**.

---

## 1. Demo phải chứng minh điều gì

Đúng **một** luận điểm, theo đúng thứ tự người xem tin được:

> Mô hình ngôn ngữ đọc đề và **viết ra một chương trình**; hệ tất định **kiểm,
> chạy, và tính chính xác**; hình 3D là **hệ quả** của lượt chạy đó chứ không
> phải một minh hoạ vẽ kèm.

Ba điều **không** demo: không trình diễn hết tính năng; không nói hệ giải được
mọi bài hình học THPT; không chạy live model trên sân khấu (rủi ro mạng và hạn
mức — bản replay tất định nói cùng một điều).

---

## 2. Chuẩn bị (5 phút trước giờ)

```bash
# cửa sổ 1 — giao diện, KHÔNG cần backend, KHÔNG cần API key
cd frontend && npm run dev            # http://localhost:3000

# cửa sổ 2 — bằng chứng tất định, chạy trước để chắc chắn xanh
cd backend && .venv/Scripts/python.exe scripts/replay_demo_cases.py
cd backend && .venv/Scripts/python.exe scripts/audit_demo_crash_surface.py
```

Muốn kiểm cả đường trình duyệt trước khi lên nói:

```bash
cd frontend && node scripts/spot-check-demo.mjs   # cần cửa sổ 1 đang chạy
```

Kỳ vọng: `DEMO_REPLAY 5/5` · `REDUCED_CHAIN 1/1` · `6/6` biên, **0** đường ném ·
`DEMO_BROWSER_SMOKE 12/12`, 0 lỗi console.

---

## 3. Thứ tự trình bày

### Ca 1 — `n1_thoi_dinh_thu_tu` · **mở bài, nói luận điểm**

| | |
|---|---|
| Vai trò | ca đầu tiên: cho thấy toàn bộ vòng đời trong một màn hình |
| Đáp số | `√3` — dạng **căn thức**, không phải số thập phân |
| Thao tác | mở bài → **Bước sau** vài lần → kéo thanh **Bước** về 0 rồi ra cuối |

**Chỉ vào:** ô số bước hiện `Bước 1/6` — hình có **6** bước, và mỗi bước là một
câu lệnh dựng thật, không phải sáu khung hoạt hình. Rồi chỉ vào đáp số: nó là
`√3`, tức hệ **không** làm tròn ở đâu cả.

**Câu nên nói:** *"Mô hình không vẽ gì. Nó viết ra sáu bước dựng; máy chạy sáu
bước ấy bằng số học chính xác, và hình là kết quả của lượt chạy."*

---

### Ca 2 — `n2_lang_tru_xien_hai_vecto` · **cấu trúc, không phải mẫu**

| | |
|---|---|
| Vai trò | lăng trụ **xiên** — hai vectơ dẫn xuất + trung điểm |
| Đáp số | `3√3` |
| Thao tác | bật **Chi tiết** → chọn một đỉnh → đọc ô soi bên phải |

**Chỉ vào:** với **Chi tiết** bật, mỗi vật nói **bước nào tạo ra nó** và **nó
phụ thuộc cái gì**. Đây là chỗ thấy được chương trình có *cấu trúc phụ thuộc*,
chứ không phải một danh sách toạ độ được khai thẳng.

**Câu nên nói:** *"Nếu mô hình chỉ đoán toạ độ rồi khai ra, cột phụ thuộc này
sẽ trống. Nó không trống."*

---

### Ca 3 — `t3_hop_tinh_tien_day_chuyen` · **chuỗi sâu**

| | |
|---|---|
| Vai trò | dây chuyền tịnh tiến 4 đỉnh — chuỗi phụ thuộc sâu nhất trong tập |
| Đáp số | `3√89/5` |
| Thao tác | **Tách khối** → xoay hình → **Ráp lại** |

**Chỉ vào:** `Bước 1/10`. Mười bước nối nhau; sai một mắt xích thì đáp số sai
hẳn, nên đáp số đúng ở đây là bằng chứng cả chuỗi đúng.

---

### Ca 4 — `t4_mat_xich_trong_chuoi_sau` · **bài khác, cùng bộ primitive**

| | |
|---|---|
| Vai trò | hình chiếu trong chuỗi phụ thuộc — **bài mới ≠ mã mới** |
| Đáp số | `2√2` |
| Thao tác | mở bài, tua tới bước cuối |

**Chỉ vào:** đây là bài **khác hẳn** ba bài trên, và **không dòng mã nào** được
thêm cho nó. Mô hình kết hợp cùng bộ primitive (8 biểu thức · 6 phép dựng · 4
phép đo) thành một chương trình khác.

**Nói đúng, đừng nói quá:** claim là *"bài mới không cần mã mới **nếu** biểu
diễn được bằng IR hiện có"*. Bài nằm ngoài IR bị **từ chối** — đó là ca 5.

---

### Ca 5 — `n4_giao_duong_mat_roi_do` · **hệ nói KHÔNG có địa chỉ**

| | |
|---|---|
| Vai trò | **cổng từ chối** — chương trình trích một dữ kiện không có trong hợp đồng |
| Kết quả mong đợi | chặn ở **grounding**, `INPUT_NOT_GROUNDED`, kèm danh sách trích dẫn không truy được |
| Thao tác | mở ca này ngay sau bốn ca xanh |

**Vì sao ca này bắt buộc có:** một demo chỉ toàn ca xanh giấu mất nửa luận điểm.
Hệ **không đoán**: khi dữ kiện không truy được về đề, nó dừng **trước khi thực
thi** và nói vì sao — thay vì dựng một cảnh đẹp cho một đáp án không chứng minh
được.

**Chỉ vào:** lời từ chối là tiếng Việt đọc được, không phải mã lỗi; và không có
cảnh 3D nào được dựng kèm.

---

### Ca 6 (tuỳ thời gian) — `v2_04_thiet_dien_goc_va_the_tich` · **thiết diện**

| | |
|---|---|
| Vai trò | thiết diện + góc + thể tích trong một bài — cảnh có `section` và `solid` |
| Chạy ở | **chế độ rút gọn**, đếm **riêng** |

**Phải nói rõ khi trình bày:** artifact nguồn (`clean-baseline-v2`) **không lưu
`RequestContract`**, nên ca này chạy được chuỗi dựng nhưng **không chạy được
cổng grounding**. Vì thế nó đếm riêng (`REDUCED_CHAIN`), không gộp vào
`DEMO_REPLAY` — gộp là báo cáo một chuỗi đủ trong khi thực ra thiếu một cổng.

---

## 4. Nếu bị hỏi

| câu hỏi | trả lời ngắn |
|---|---|
| *Mô hình có tính toạ độ không?* | Không. Mọi toán hạng hình học trong IR là một **tên**; lược đồ không nhận toạ độ thô. Số do nhân hình học tính bằng `Fraction` + `Radical`. |
| *Sao biết đáp số đúng?* | 9 checker tất định + hậu điều kiện server-owned, và một oracle **cài độc lập** với kernel (`geometry_oracle.py`) — cố ý dùng thuật toán khác. |
| *Hệ giải được mọi bài hình học THPT chứ?* | **Không**, và không claim thế. Phủ chương trình là **PARTIAL**, có chủ đích. Ngoài IR ⇒ từ chối. |
| *Có kéo được như GeoGebra không?* | Không, và là quyết định phạm vi: kéo liên tục phá song ánh `frame k ⇔ trace[k]`. Tương tác ở đây là **chọn, tách khối, tua bước**. |
| *Đã đo trên người học chưa?* | Chưa — `LEARNER_IMPACT_NOT_EVALUATED`, khai rõ là ngoài phạm vi. |
| *Còn khối cong, khối lõm?* | Ngoài phạm vi hiện tại: chỉ khối **lồi**, không mặt cong. |

---

## 5. Nhắc kỹ thuật

- Ba script ở §2 chạy **0 lượt gọi model**. Không cần `GEMINI_API_KEY` cho
  toàn bộ kịch bản này.
- `npm run dev` đủ cho phần giao diện — **không cần** Docker, không cần backend.
- Nếu smoke trình duyệt đỏ: kiểm cửa sổ `npm run dev` còn sống, và Chrome thật
  có mở được không (script dùng CDP). Nó đã được tiêm lỗi giả để chứng minh nó
  đỏ được, nên một lượt đỏ là tín hiệu thật.
