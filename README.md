# Nghiên cứu và xây dựng hệ thống mô phỏng 3D hình học không gian

Khoá luận. Học sinh nhập một bài hình học không gian bằng **tiếng Việt**; hệ
thống dựng lại hình trong không gian ba chiều, chạy từng bước dựng, và trả lời
bằng **số chính xác tuyệt đối** — không làm tròn ở bất kỳ đâu.

**[Hệ thống làm gì](#1-hệ-thống-làm-gì) · [Chức năng](#2-chức-năng-chính) ·
[Giới hạn](#3-giới-hạn-chính) · [Chạy nhanh](#4-chạy-nhanh) · [Tài liệu](#5-tài-liệu)**

---

## 1. Hệ thống làm gì

**LLM đọc đề, engine tất định diễn hoạt.** Đây là *luận điểm* của đề tài chứ
không phải một chi tiết kĩ thuật. Mục tiêu của sản phẩm là **mô phỏng 3D hình học
không gian tương tác**, không phải hệ thống tự động giải và chứng minh mọi bài toán.

Kiến trúc giải toán và mô phỏng chính thức của sản phẩm trên `POST /api/analyze` là **Hybrid `/4`** (`HYBRID_ROUTE_MODE = live` mặc định; `staging-replay` cho replay offline trong phát triển/kiểm thử; tuyến `LLM_ONLY`, `Adapter /3` và `Compiler C` cũ đã gỡ bỏ, không có fallback ngầm):

```
đề tiếng Việt
   → Gemini: trích xuất → TypedFactNext /2 (dữ kiện, quan hệ, mục tiêu + trích dẫn nguyên văn câu đề)
   ─────────────────── từ đây trở đi KHÔNG có LLM ───────────────────
   → Source Gate (xác minh trích dẫn nguồn, vai trò mệnh đề, phủ định, số đo; cần làm rõ ⇒ route-d-clarification/1)
   → FactGraph & Planner /26 (tất định tự chọn và phối hợp hàm từ Registry /33)
   → Exact Kernel /24 (khung affine + metric Gram chính xác Fraction / Radical + chứng chỉ hình học)
   → Adapter /4 (kiểm định IR/Scene3D + bước dựng tích lũy liên tục + kết quả chính xác)
   → Scene3D + Construction Steps + Results
```

*(Chi tiết kiến trúc và trạng thái các cổng kiểm chứng xem tại [`docs/ARCHITECTURE_MAP.md`](docs/ARCHITECTURE_MAP.md), [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md) và [`docs/MIGRATION_CHECKLIST.md`](docs/MIGRATION_CHECKLIST.md).)*

Gemini **không bao giờ** phát toạ độ kết quả và **không** sinh chương trình giải riêng cho từng đề bài. Nó chỉ trích xuất dữ kiện, quan hệ và mục tiêu hình học theo hợp đồng đóng `TypedFactNext /2` kèm trích dẫn nguyên văn câu đề; toàn bộ việc kiểm nguồn, chọn hàm dựng, tính toạ độ/metric Gram, kiểm chứng và xuất hoạt cảnh `Scene3D` đều do engine tất định thực hiện.

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
- Tuyến mặc định **Hybrid `/4`** hỗ trợ các lớp đa diện, thiết diện, khoảng cách/góc/thể tích và các lát cắt khối tròn xoay/nhiều khối đã đăng ký trong `Registry /33`, nhưng **không** tuyên bố giải mọi bài hình học không gian bất kỳ; đề từ ảnh chụp chỉ đi tiếp sau bước người học kiểm tra và xác nhận văn bản.
- **Giới hạn kiểm chứng hiện hành:** Kiểm định độc lập trên bộ 60 đề tiếng Việt mới `H-1` (`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`), live smoke sau cutover (`NEW_LIVE_SMOKE_NOT_MEASURED`) và xác minh triển khai production (`PRODUCTION_DEPLOYMENT_VERIFIED = NO`) vẫn chưa thực hiện.
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
