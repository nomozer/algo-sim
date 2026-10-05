# Nghiên cứu và xây dựng hệ thống mô phỏng 3D hình học không gian

Khoá luận. Học sinh nhập một bài hình học không gian bằng **tiếng Việt**; hệ
thống dựng lại hình trong không gian ba chiều, chạy từng bước dựng, và trả lời
bằng **số chính xác tuyệt đối** — không làm tròn ở bất kỳ đâu.

**[Hệ thống làm gì](#1-hệ-thống-làm-gì) · [Chức năng](#2-chức-năng-chính) ·
[Giới hạn](#3-giới-hạn-chính) · [Chạy nhanh](#4-chạy-nhanh) · [Tài liệu](#5-tài-liệu)**

---

## 1. Hệ thống làm gì

**LLM đọc đề, engine tất định diễn hoạt.** Đây là *luận điểm* của đề tài chứ
không phải một chi tiết kĩ thuật.

```
đề tiếng Việt
   → LLM: đọc đề        → RequestContract  (dữ kiện + nghĩa vụ, ĐÓNG BĂNG)
   → LLM: tổng hợp      → Semantic Program (các BƯỚC DỰNG, không có toạ độ kết quả)
   ─────────────────── từ đây trở đi KHÔNG có LLM ───────────────────
   → thẩm định lược đồ · thẩm định tĩnh
   → đối chiếu dữ kiện với câu đề · chứng chỉ giả định · đối chiếu phép dựng
   → thực thi (số hữu tỉ + căn, CHÍNH XÁC)
   → checker (kiểm lại kết luận từ HÌNH, không tin con số chương trình khai)
   → trace + cảnh 3D
```

LLM **không bao giờ** phát một toạ độ kết quả. Nó nói *"giao tuyến của (SAB)
và (SCD)"*; toạ độ do nhân hình học tính. Mọi toán hạng hình học trong chương
trình là **TÊN** của một vật đã dựng — cưỡng chế ở lược đồ, không phải nhắc
trong prompt. LLM không sinh hoạt hình, không sinh toạ độ, không quyết đúng/sai.

Một bài mới trong phạm vi các bước dựng đã có **không cần mã riêng theo dạng
bài**; bài ngoài phạm vi ấy bị **từ chối có cấu trúc** (nói dừng ở chặng nào, vì
sao), không bị đoán.

## 2. Chức năng chính

- Dựng hình 3D từ đề: điểm, đoạn, mặt phẳng, đa giác, khối đa diện, thiết diện;
  trung điểm, chia đoạn, hình chiếu, giao điểm, giao tuyến.
- Đo chính xác: khoảng cách, góc (dưới dạng cos/cos²), diện tích, thể tích —
  đáp số dạng `3√89/5`, không phải `5.6603…`.
- Tua từng bước dựng; chọn một đại lượng để xem nhãn, công thức và dữ kiện nó
  dựa vào; nét khuất vẽ đứt, nét thấy vẽ liền.
- Từ chối khi đề thiếu dữ kiện, khi chương trình dùng giả thiết đề không cho,
  hoặc khi phép dựng không khớp câu đề.
- Lớp học trực tiếp: giáo viên chiếu, học sinh theo cùng bước.

Năng lực chính xác của sản phẩm (họ khối, phép dựng, phép đo):
`backend/app/simulation/product_capability.py`; trạng thái hiện hành:
[`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md).

## 3. Giới hạn chính

- Chỉ những bài **biểu diễn được bằng các bước dựng hiện có**; phủ chương trình
  Toán 11–12 là một phần, có chủ đích.
- Khối có mặt cong (cầu, trụ, nón), nhiều khối trong một đề và đề từ ảnh chụp
  **chưa** là năng lực sản phẩm đầy đủ.
- Kéo–thả liên tục kiểu GeoGebra nằm ngoài phạm vi: tương tác là chọn và tua bước.
- **Tác động lên người học chưa được đánh giá** — kiểm thử kỹ thuật không thay
  thực nghiệm sư phạm.

Điều hệ được phép tuyên bố, kèm bằng chứng và giới hạn:
[`docs/research/CLAIM_EVIDENCE_MAP.md`](docs/research/CLAIM_EVIDENCE_MAP.md).

## 4. Chạy nhanh

Yêu cầu: Python 3.12 + venv ở `backend/.venv`, Node 20+, Docker (chỉ khi cần
đường phân tích LLM).

```bash
# --- giao diện, KHÔNG cần backend, KHÔNG cần API key ---
cd frontend && npm install && npm run dev        # http://localhost:3000

# --- backend + Postgres ---
docker compose up -d --build

# --- kiểm thử (0 lượt gọi model) ---
cd backend  && .venv/Scripts/python.exe -m pytest -q
cd frontend && npx vitest run && npm run build

# --- demo tất định, 0 lượt gọi model ---
cd backend  && .venv/Scripts/python.exe scripts/replay_demo_cases.py
cd backend  && .venv/Scripts/python.exe scripts/audit_demo_crash_surface.py

# --- demo trong trình duyệt thật (cần `npm run dev` ở cửa sổ khác) ---
cd frontend && node scripts/spot-check-demo.mjs
```

Đường phân tích LLM là **opt-in và tiêu quota thật**; nó không cần cho demo,
kiểm thử hay phát triển giao diện.

## 5. Tài liệu

- [`docs/README.md`](docs/README.md) — cổng tài liệu: kiến trúc, phát triển,
  nghiên cứu, bằng chứng.
- [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md) — trạng thái hiện tại của kho
  mã và việc kế tiếp.
