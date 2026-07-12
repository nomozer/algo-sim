# AlgoSim — Hệ thống mô phỏng tương tác 2D/3D kết hợp LLM phân tích bài toán bằng ngôn ngữ tự nhiên

Hỗ trợ dạy học môn Tin học THPT (Chương trình GDPT 2018).
Quy tắc hệ thống: [docs/RULES.md](docs/RULES.md).

## Cấu trúc

```
algo-sim/
├─ docs/        Tài liệu (RULES.md)
├─ frontend/    React + TypeScript + Vite; simulation registry, renderer SVG 2D (3D Three.js — dự kiến M8)
└─ backend/     Python FastAPI + Gemini API + SQLAlchemy (PostgreSQL/SQLite), cổng 8787
```

## Chạy lần đầu

```bash
# 1. Frontend (một lần)
cd frontend && npm install

# 2. Cấu hình key Gemini cho backend
#    Sao chép backend/.env.example → backend/.env, dán key thật vào
#    (lấy key miễn phí: https://aistudio.google.com/apikey)

# 3. Backend + PostgreSQL (Docker)
docker compose up -d --build

# 4. Frontend (cửa sổ lệnh riêng, giữ hot-reload khi dev)
cd frontend && npm run dev     # mở http://localhost:5173
```

Lệnh hay dùng: `docker compose logs -f backend` (xem log) ·
`docker compose down` (dừng) · `docker compose up -d --build` (chạy lại sau khi sửa backend).

## Cơ sở dữ liệu

**PostgreSQL 16** chạy trong Docker (service `db`, dữ liệu bền trong volume `pgdata`).
Ngân hàng bài nằm ở bảng `problems`. Code dùng SQLAlchemy nên khi chạy backend
ngoài Docker mà không đặt `DATABASE_URL` sẽ tự rơi về SQLite — tiện chạy nhanh:

```bash
cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --port 8787
```

Không có key vẫn dùng được: chọn **bài mẫu** trong giao diện — các mô phỏng
phân tích sẵn (thuật toán, logic, nhị phân, mạng, DSL generic) chạy offline,
không cần backend.

## Kiểm thử

```bash
cd frontend && npm test          # vitest: engine + simulation domains + generic DSL
cd backend  && python -m pytest  # pipeline, DSL validator, semantic checks
```

## Kiến trúc (tóm tắt)

Mô phỏng là **xương sống**; LLM chỉ phân tích/ánh xạ, không điều khiển engine.

```
Đầu vào ngôn ngữ tự nhiên (text / .docx / code / ảnh)
→ analyze          trích semantic requirements
→ representation    plan tất định (từ manifest năng lực DSL)
→ classify          định tuyến theo NĂNG LỰC: module chuyên biệt hoặc generic.rule_scene
→ simulate          LLM điền simulation_id + config
→ validation        kiểm cấu trúc + semantic compatibility (khớp vai trò ngữ nghĩa)
→ engine tất định   sinh trace / timeline
→ renderer 2D       (3D — M8)
```

- **LLM (Gemini)** chỉ sinh `simulation_id` + config đã kiểm (structured output + validate + retry); **không bao giờ** sinh bước/timeline/kết quả.
- **Engine tất định** (frontend) sinh diễn biến từng bước — module chuyên biệt (thuật toán, logic, nhị phân, mạng) hoặc **DSL generic** do LLM compose (`generic.rule_scene`), có progressive reveal và exploratory/hybrid.
- **Định tuyến theo năng lực**: khớp semantic requirements ↔ capability manifest; đề vượt năng lực DSL → `capability_gap` thay vì ép sai primitive.
- **Backend** giấu API key và cache ngân hàng bài — đề trùng không tốn thêm lượt gọi API.
