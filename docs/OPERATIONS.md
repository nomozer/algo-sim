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

## "Sửa rồi mà nó vẫn nhận bản cũ" — BỐN tầng, bốn cách gỡ

Triệu chứng: sửa mã hoặc prompt, gửi lại đề, nhận **y nguyên kết quả cũ**. Không
lỗi, không cảnh báo. Bốn thứ khác nhau có thể đang giữ bản cũ, và **restart chỉ
gỡ được hai**.

| | Tầng | Giữ gì | Sửa gì thì dính | Gỡ bằng |
|---|---|---|---|---|
| ① | uvicorn **không** `--reload` | module Python đã import | mọi sửa `backend/app/**` | `docker compose restart backend`, hoặc `DEV_RELOAD=1` |
| ② | `gemini._skill_cache` | nội dung `skills/*.md` | sửa prompt | như ① |
| ③ | **cache exact** (Postgres) | envelope theo *(text đề chuẩn hoá + `CACHE_VERSION`)* | sửa mã/prompt mà không bump | `scripts/cache_clear.py`, hoặc bump |
| ④ | history `localStorage` (FE) | envelope đã xem | — | mở phiên MỚI, đừng mở lại phiên cũ |

**① là tầng nặng nhất và cũng lặng nhất.** `docker-compose.yml` mount
`./backend/app:/app/app` nên file trên đĩa luôn mới — dễ tưởng là đã ăn. Nhưng
uvicorn giữ module đã import trong bộ nhớ, nên sửa mã **không có tác dụng gì**
cho tới khi khởi động lại tiến trình.

```bash
DEV_RELOAD=1 docker compose up -d --build backend   # --build: CMD nằm TRONG image
```

`--build` là bắt buộc ở lần đầu: `CMD` được nướng vào image, nên `up -d` không
kèm `--build` sẽ dựng lại container từ image cũ và cờ không có tác dụng. Xác
nhận bằng log — phải thấy `Started reloader process … using WatchFiles`; thấy
`Started server process [1]` là **chưa** bật.

`WATCHFILES_FORCE_POLLING=1` đi kèm và **bắt buộc** cho bind mount từ host
Windows: inotify không lan qua ranh giới ấy, nên thiếu nó thì `--reload` bật mà
không bao giờ nạp lại — đổi một lỗi im lặng lấy một lỗi im lặng khác.

⚠️ **Polling có giá, và nó không nhỏ.** Đo được 2026-08-25 trên máy này: với
`DEV_RELOAD=1` đang chạy, một lượt `pytest` đầy đủ **không xong trong 10 phút**;
tắt đi thì **27,7 giây**. Polling quét cả cây `/app/app` qua ranh giới
Windows↔container, và nó tranh I/O với mọi thứ khác. Nên bật khi đang sửa vòng
lặp ngắn, **tắt trước khi chạy suite hay chạy lượt đo**:

```bash
docker compose up -d backend        # DEV_RELOAD mặc định 0 — polling tắt
```

**③ là tầng lừa người nhất**: restart xong, mã mới đã chạy, gửi lại **đúng đề
cũ** vẫn nhận kết quả cũ — vì khoá cache không dính dáng gì tới mã nguồn.

```bash
docker compose exec backend python scripts/cache_clear.py --liet-ke
docker compose exec backend python scripts/cache_clear.py --de "<đề>"
docker compose exec backend python scripts/cache_clear.py --cu    # mọi row khác CACHE_VERSION
```

Chạy **trong** container: `DATABASE_URL` trỏ `db:5432`, tên ấy chỉ phân giải
được trong mạng compose (chạy từ host sẽ lặng lẽ đụng SQLite, không phải DB
thật). `scripts/` được mount chỉ-đọc riêng cho việc này.

⚠️ `CACHE_VERSION` vẫn là **đường chính thức** để vô hiệu hoá cache khi đổi
prompt hoặc chính sách định tuyến — bump là một tuyên bố về hợp đồng, đọc được
trong lịch sử. `cache_clear.py` dành cho việc khác: thử đi thử lại một đề trong
lúc đang sửa, nơi bump số cho mỗi lần lưu file là vô nghĩa.

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

**`pytest` KHÔNG chạy trên `backend/algosim.db`.** `conftest.py` trỏ
`DATABASE_URL` sang một file tạm đặt tên theo PID, nên mỗi lượt pytest có DB
riêng và DB dev của bạn không bao giờ bị test ghi vào. Hệ quả cần biết: dữ liệu
test **không** hiện ra trong `algosim.db`. Đặt `DATABASE_URL` tường minh thì
lượt đó thắng — `setdefault`, không gán đè. Khoá bởi
`tests/test_db_ownership.py`.

⚠️ **Suite treo mà không có test nào chậm?** Đếm tiến trình pytest trước khi đi
tìm test có lỗi:

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select ProcessId,CommandLine
```

Đo được 2026-08-25: một lượt full treo quá 600 giây (lượt trước đó 27 giây) khi
có **bốn** tiến trình pytest cùng chạy từ hai phiên làm việc song song. CPU gần
bằng không — chờ khoá. Bản vá DB riêng ở trên gỡ nguyên nhân *đã xác định được*
là tranh file SQLite; **chưa** đo được rằng chạy song song nay đã hoàn toàn an
toàn, vì lượt đo lại bị chính vòng lặp chờ bận của người đo làm nhiễu. Còn một
nghi phạm chưa chứng minh: `_windows_fixed_socketpair` trong `conftest.py` gọi
`connect()`/`accept()` **không đặt timeout**, nên dưới áp lực cổng ephemeral nó
có thể chờ vô hạn. Chưa dựng lại được một ca hỏng ổn định ⇒ chưa vá (sửa mù một
treo không tái hiện được là cách đẻ ra lỗi thứ hai).

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
