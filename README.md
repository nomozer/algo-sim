# AlgoSim — Hệ thống mô phỏng tương tác 2D/3D kết hợp LLM phân tích bài toán bằng ngôn ngữ tự nhiên

Hỗ trợ dạy học môn Tin học THPT (Chương trình GDPT 2018).
Quy tắc hệ thống: [docs/RULES.md](docs/RULES.md).

## Cấu trúc

```
algo-sim/
├─ docs/        Tài liệu (RULES.md)
├─ frontend/    React + TypeScript + Vite; simulation registry, renderer SVG 2D (3D Three.js — dự kiến M8)
└─ backend/     Python FastAPI + Gemini API + SQLAlchemy (PostgreSQL/SQLite), cổng 8000
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
cd frontend && npm run dev     # mở http://localhost:3000
```

Lệnh hay dùng: `docker compose logs -f backend` (xem log) ·
`docker compose down` (dừng) · `docker compose up -d --build` (chạy lại sau khi sửa backend).

## Cơ sở dữ liệu & migration

**PostgreSQL 16** chạy trong Docker (service `db`, dữ liệu bền trong volume `pgdata`).
Bảng: `simulation_cache` (cache envelope đã validate), `simulation_patterns`,
`reuse_metrics` — toàn dữ liệu server tự sinh, tái tạo được. Code dùng SQLAlchemy
nên chạy backend ngoài Docker mà không đặt `DATABASE_URL` sẽ tự rơi về SQLite:

```bash
cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --port 8000
```

**Migration (Alembic).** Trên DB bền (Postgres), schema tiến hoá qua Alembic —
container tự chạy `alembic upgrade head` ở entrypoint trước khi phục vụ. Khi đổi
model trong `app/persistence/db.py`:

```bash
cd backend
.venv/Scripts/alembic revision --autogenerate -m "mô tả thay đổi"   # sinh migration
.venv/Scripts/alembic upgrade head                                   # áp dụng
```

**Quyền sở hữu schema (DB-HARDEN-2).** Hai dialect là *lựa chọn thay thế* theo
môi trường, không phải bản sao ghi song song:

| | SQLite | PostgreSQL |
|---|---|---|
| Vai trò | test offline, dev nhanh, DB ephemeral | DB triển khai BỀN |
| Tạo/tiến hoá schema | `create_all()` được phép (lưới an toàn) | **CHỈ Alembic** (`alembic upgrade head`) |
| Runtime `create_all()` | có | **không** — thiếu schema phải hỏng thật, không tự vá |

Quyết định dựa trên **dialect metadata thật** (`engine.dialect.name`), không
string-check URL. `init_db()` là no-op trên Postgres — Alembic là nguồn tiến hoá
schema DUY NHẤT.

**Kiểm tra (offline, không cần Docker):**

```bash
cd backend
.venv/Scripts/python -m pytest tests/test_migration_drift.py   # cổng chống trôi: model ↔ head migration
```

Cổng này cũng chạy trong suite mặc định `pytest` — đổi model mà quên tạo
migration là test ĐỎ. (Tương đương `alembic check`, chạy trên SQLite tạm.)

**Smoke Postgres thật (opt-in, cần Docker + `pip install psycopg2-binary`):**

```bash
cd backend
.venv/Scripts/python -m pytest -m postgres   # spin container throwaway (KHÔNG đụng pgdata), migrate+ghi/đọc+restart+alembic check
```

> Lần ĐẦU chuyển một volume Postgres cũ (tạo bằng `create_all`, chưa có
> `alembic_version`) sang Alembic có HAI đường AN TOÀN:
> **(A)** dữ liệu bỏ được (chỉ là cache) → `docker compose down -v` rồi rebuild
> cho volume mới sạch; **(B)** muốn giữ dữ liệu → `alembic stamp head` **chỉ khi**
> operator đã xác nhận schema hiện có KHỚP head migration. Tuyệt đối **không**
> tự động stamp một DB lạ — làm vậy sẽ giấu drift.

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
