# OPERATIONS.md — Vận hành: cơ sở dữ liệu, migration, dependency

Tài liệu này gom các chính sách vận hành mà **người đóng góp** cần, tách khỏi
README để README tập trung vào đề tài. Nếu tài liệu mâu thuẫn với code/test:
**code/test thắng** — sửa tài liệu.

## Vòng lặp sửa code — ĐỪNG chạy full suite sau mỗi lần sửa

Full suite là cổng **trước khi commit**, không phải phản hồi khi đang nghĩ. Chạy
nó sau mỗi lần sửa thì mỗi lần sửa mất hàng chục giây và mạch làm việc đứt —
đây là lỗi thói quen, không phải giới hạn của kho mã.

```bash
# --- FRONTEND: watch, chỉ chạy lại file liên quan (~1s) ---
cd frontend && npx vitest                       # để chạy nền, sửa tới đâu đỏ tới đó
cd frontend && npx vitest related src/simulations/domains/algorithm/ui.tsx
cd frontend && npx vitest run -t "<tên test>"   # lọc theo tên

# --- BACKEND: chỉ chạy cái vừa đỏ ---
cd backend && .venv/Scripts/python.exe -m pytest -q -x --lf
cd backend && .venv/Scripts/python.exe -m pytest -q tests/test_dsl.py

# --- CỔNG TRƯỚC COMMIT (chỗ DUY NHẤT cần full) ---
cd backend && .venv/Scripts/python.exe -m pytest -q
cd frontend && npx vitest run && npm run build
```

Bộ chọn theo tác động (T0, W8) trả lời "sửa file này thì phải chạy gì":

```bash
cd frontend && node scripts/impact.mjs --files src/styles/global.css
```

⚠️ Script trình duyệt (`certify-*.mjs`, `audit-*.mjs`) **không** thuộc vòng lặp
này — mỗi lượt vài phút và cần Chrome. Chạy khi cần **bằng chứng**, không chạy
để lấy phản hồi. Việc chúng hỏi mà vitest không hỏi được thì đã có cổng offline
tương ứng (vd `simulations/experience-gate.test.ts`).

## Cơ sở dữ liệu & migration

**PostgreSQL 16** chạy trong Docker (service `db`, dữ liệu bền trong volume
`pgdata`). Bảng: `simulation_cache` (cache envelope đã validate),
`simulation_patterns`, `reuse_metrics` — toàn dữ liệu server tự sinh, tái tạo
được. Code dùng SQLAlchemy nên chạy backend ngoài Docker mà không đặt
`DATABASE_URL` sẽ tự rơi về SQLite:

```bash
cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements-dev.txt
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
schema DUY NHẤT (bất biến #19 trong `ARCHITECTURE_MAP.md`).

**Kiểm tra (offline, không cần Docker):**

```bash
cd backend
.venv/Scripts/python -m pytest tests/test_migration_drift.py   # cổng chống trôi: model ↔ head migration
```

Cổng này cũng chạy trong suite mặc định `pytest` — đổi model mà quên tạo
migration là test ĐỎ. (Tương đương `alembic check`, chạy trên SQLite tạm.)

**Smoke Postgres thật (opt-in, cần Docker):** driver `psycopg2-binary` đã nằm
trong `requirements.txt` và được `requirements-dev.txt` kế thừa qua `-r`, nên
setup dev chuẩn (`pip install -r requirements-dev.txt`) đã đủ — không cần cài tay.

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

## Quyền sở hữu dependency (Python)

Hệ dependency **duy nhất** là pip + hai file requirements (không dùng
Poetry/uv/pipenv, không pyproject/lockfile). Mỗi dep khai **đúng một chỗ**:

| Manifest | Vai trò (nguồn chân lý) | Ai dùng |
|---|---|---|
| `backend/requirements.txt` | **runtime** — mọi dep chạy app (gồm `psycopg2-binary`) | `Dockerfile`, lệnh chạy app |
| `backend/requirements-dev.txt` | **dev/test** — kế thừa runtime qua `-r requirements.txt`, chỉ thêm tool test (`pytest`) | setup standalone `pip install -r requirements-dev.txt` |

**Luật cho người/agent đóng góp:** **Không** tạo file manifest hay lockfile
dependency mới theo kiểu tùy tiện. Trước khi thêm dep, **kiểm chính sách hiện có**
và dùng lại nguồn chân lý sẵn có (runtime → `requirements.txt`; chỉ-test →
`requirements-dev.txt`). Không nhân bản cùng một dep qua nhiều manifest. Dep chỉ
cần cho một lần kiểm thủ công thì **đừng commit** trừ khi nó thành workflow bền.
