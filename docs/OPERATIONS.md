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
cd frontend && npx vitest related src/simulations/domains/geometry/scene3d-view.tsx
cd frontend && npx vitest run -t "<tên test>"   # lọc theo tên

# --- BACKEND: chỉ chạy cái vừa đỏ ---
cd backend && .venv/Scripts/python.exe -m pytest -q -x --lf
cd backend && .venv/Scripts/python.exe -m pytest -q tests/geometry/test_geometry_kernel.py

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
để lấy phản hồi. Ở giai đoạn Tin học, việc chúng hỏi mà vitest không hỏi được có cổng offline
tương ứng (`simulations/experience-gate.test.ts`, đã gỡ); ở miền hình học, phần thuần tính toán của
bộ đo trình duyệt có test node riêng (`frontend/scripts/compiler-scene-replay-lib.node-test.mjs`).

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

## Vòng phát triển backend — MỘT lệnh, và nó biết khi nào phải build lại

Tầng ① ở trên trả lời *"mã mới có chạy chưa"*. Câu còn lại đắt hơn và trước
2026-09-15 không có gì trả lời: **lúc nào PHẢI build lại image?** Đã cháy thật —
`pillow` được thêm vào `requirements.txt`, không ai build lại, và backend chết
với `ModuleNotFoundError: No module named 'PIL'` trong khi `backend/app` (bind
mount) vẫn mới tinh. Git HEAD không trả lời được câu ấy: commit tài liệu làm HEAD
đổi mà image không cần đụng, còn sửa `requirements.txt` chưa commit thì HEAD im.

```bash
backend/.venv/Scripts/python.exe backend/scripts/dev_backend.py up      # LỆNH CHUẨN
backend/.venv/Scripts/python.exe backend/scripts/dev_backend.py check   # chỉ đọc, MỘT quyết định
backend/.venv/Scripts/python.exe backend/scripts/dev_backend.py status  # danh tính image ↔ nguồn
```

`up` = check → (build backend nếu ĐẦU VÀO IMAGE đổi) → dựng lại container backend
với `docker-compose.dev.yml` (`DEV_RELOAD=1`) → chờ healthcheck. Không `--build`
thừa, không đụng service `db`, không `down`, không xoá volume, không thử lại khi
build hỏng.

**Thẩm quyền là `Dockerfile` + `.dockerignore` + khối `backend` của compose**, đọc
bằng máy chứ không phải danh sách viết tay:

| Sửa gì | Lớp | Launcher làm gì |
|---|---|---|
| `backend/app/**/*.py` | `SOURCE_HOT_RELOAD` | không gì cả — uvicorn `--reload` nạp lại |
| `requirements.txt` · `Dockerfile` · `.dockerignore` · `alembic/**` | `IMAGE_REBUILD_REQUIRED` | build **riêng** backend một lần, rồi dựng lại container |
| `docker-compose*.yml` · `backend/.env` | `CONTAINER_RECREATE_REQUIRED` | dựng lại container backend |
| file mới trong `alembic/versions/` (hoặc DB lệch head) | `MIGRATION_APPROVAL_REQUIRED` | **DỪNG trước build/start** |
| `docs/**` · `frontend/**` · `backend/tests/**` | `NO_ACTION` | không gì cả |

`backend/app` **không** nằm trong dấu vân tay rebuild vì bind mount che nó: mã ấy
đến từ đĩa host lúc chạy, không từ image. Xem danh sách đầy đủ bằng
`dev_backend.py fingerprint --files` (hiện 10 file), và phân loại cây làm việc
hiện tại bằng `dev_backend.py classify`.

⚠️ **Cổng migration KHÔNG tự mở.** `CMD` của image chạy `alembic upgrade head` lúc
khởi động, nên start một container trên image có revision mới là đủ để schema đổi
**âm thầm**. Launcher từ chối build/start khi DB khác head nguồn; duyệt migration
là việc của người, và sao lưu trước (`pg_dump -Fc`) là bước đầu tiên.

⚠️ `--reload` chỉ theo dõi `*.py`. Sửa `app/ai/skills/*.md` vẫn cần
`docker compose restart backend` (xem ② ở trên).

Container backend nay có **healthcheck** gọi `GET /api/health` bằng Python của
chính image (không `curl`): `docker compose ps` phân biệt được *đang chạy* với
*phục vụ được*.

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

**Migration (Alembic) & Cổng an toàn dữ liệu (`DB-SAFETY-CLOSURE`).** Trên DB bền (Postgres), schema tiến hoá qua Alembic — container tự chạy cổng kiểm tra `python alembic/migration_preflight.py --startup` rồi mới chạy `alembic upgrade head` (và `env.py` tiếp tục khóa kiểm tra trước mọi `upgrade`/`downgrade` trực tuyến):
- Mọi thao tác phá hủy (`op.drop_table`, `op.drop_column`, `DROP TABLE`, `TRUNCATE`, `DELETE FROM`) **bị chặn tuyệt đối lúc khởi động** (`ALGOSIM_STARTUP_MODE=1` -> exit `23`).
- DB có dữ liệu sẵn nhưng chưa có bảng/bản ghi `alembic_version` (`UNSTAMPED_EXISTING_DATABASE`) **bị từ chối nâng cấp tự động** để tránh lệch hoặc ghi đè schema ngoài kiểm soát — bắt buộc sao lưu + kiểm chứng restore độc lập trước khi xử lý thủ công.
- Revision `f8a2c41d9e05` giữ nguyên trạng 5 bảng Classroom cũ (`classrooms`, `class_memberships`, `assignments`, `practice_sessions`, `classroom_sessions`) nếu đã tồn tại, và `env.py` loại trừ 5 bảng di sản này khỏi phép so `alembic check`.
Khi đổi model trong `app/persistence/`:

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

## Triển khai Frontend trên Vercel (`hoclieu.tech`)

- Cấu hình triển khai chính thức đặt duy nhất tại [`frontend/vercel.json`](../frontend/vercel.json) (Root Directory trên Vercel là `frontend`). Vercel **chỉ** chạy Frontend SPA (React, TypeScript, Vite, Landing, Workspace, Library, Admin UI, Scene3D trên trình duyệt) — không triển khai FastAPI hay database trên Vercel.
- Hướng dẫn cấu hình Dashboard, SPA rewrite loại trừ `/api/*` & `/assets/*`, cache, security headers, điều tra lỗi 404 và rollback xem tại [`docs/architecture/VERCEL_FRONTEND_DEPLOYMENT_RUNBOOK.md`](architecture/VERCEL_FRONTEND_DEPLOYMENT_RUNBOOK.md).

## Triển khai Backend & PostgreSQL trên VPS riêng (Production Runbook)

> **Trạng thái hiện tại:** `BACKEND_DEPLOYMENT_PENDING` (chỉ áp dụng khi Owner triển khai VPS Ubuntu/Linux và cấu hình DNS/TLS thật; không tự tạo VPS hay sửa DNS tự động).  
> **Integrated Backend Release / Code Candidate SHA:** `473cb68ded13d35f413032e9c45aea36960928ea` (đã bao gồm C5 Auth/Cookie/CORS/DB hardening + xác thực Reverse Proxy peer & CSRF middleware; `CACHE_VERSION = "158"`, `EVALUATION_CANDIDATE.json` đăng ký tại `ebe257fbf`).

1. **Yêu cầu Linux runtime:** Ubuntu 22.04 LTS hoặc 24.04 LTS (`x86_64`), Python 3.12 (nếu chạy ngoài Docker) và bộ thư viện hệ thống chuẩn cho PyMuPDF/Pillow trong image `python:3.12-slim`. Lưu ý kỹ thuật: gói `llama-server.exe` nghiên cứu hiện là bản Windows-only; nếu bật Local SLM trên VPS Linux, phải biên dịch hoặc cung cấp `llama-server` Linux (`x86_64`) riêng.
2. **Yêu cầu Docker & Docker Compose:** Docker Engine >= 24 và Docker Compose v2 plugin (`docker compose version`); không dùng `docker-compose` v1.
3. **Tài nguyên CPU / RAM / Disk:** Phân biệt rạch ròi theo môi trường đo thực tế — (a) **Windows local (live server):** backend idle ~103 MiB RAM, served 1 ca offline ~110 MiB (`llama.cpp` 0.6B GGUF nạp model ~973–1,044 MiB RSS); (b) **Docker local (isolated test):** kiểm chứng trực tiếp bằng build image (`python:3.12-slim`, ~451.5 MiB) + PostgreSQL 16 + Alembic 8 revisions (`ExitCode=0`, healthcheck healthy sau ~6s); (c) **Linux VPS:** chưa đo thực tế trên hạ tầng đích (`NOT_MEASURED`), khuyến nghị đo tải thực tế trên VPS trước khi chốt cấu hình tối thiểu cho GGUF + Postgres + Nginx.
4. **Build & Khởi động Backend (production):** dùng `backend/Dockerfile` (`DEV_RELOAD=0`, `ALGOSIM_STARTUP_MODE=1`, 1 worker `uvicorn app.main:app --host 0.0.0.0 --port 8000`) với build command:
   ```bash
   docker build -t algosim-backend:473cb68de \
     --build-arg GIT_SHA=473cb68ded13d35f413032e9c45aea36960928ea \
     --build-arg BUILD_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ) ./backend
   ```
   Giữ `HYBRID_ROUTE_MODE=live` làm mặc định trừ khi Owner có quyết định khác. Lưu ý CVE build-time tool `pip 25.0.1` trong image gốc `python:3.12-slim` không được nạp lúc runtime (0 CVE trên cả 34 runtime packages), khuyến nghị quét OS image (`trivy`/`docker scout`) trong pipeline CI/VPS khi triển khai.
5. **Thiết lập PostgreSQL 16 nội bộ:** dùng service `db` (`postgres:16-alpine`) chỉ kết nối trên bridge network nội bộ Compose hoặc bind `127.0.0.1`; **tuyệt đối không** publish port `5432` ra Internet (`0.0.0.0:5432` bị cấm). Đặt mật khẩu mạnh trong tệp env bảo mật trên VPS (không dùng mật khẩu dev mặc định). Chuỗi `postgres://` / `postgresql://` được chuẩn hoá tự động sang `postgresql+psycopg2://` tại `backend/app/persistence/db.py`; khuyến nghị gắn `?connect_timeout=3` vào `DATABASE_URL` để `/api/health` trả `503` nhanh khi DB gián đoạn thay vì chờ timeout TCP mặc định (~8s).
6. **Persistent Volumes:** gắn volume bền `pgdata:/var/lib/postgresql/data` và thư mục backup ngoài container (`/var/backups/algosim`, quyền sở hữu hạn chế).
7. **Cung cấp Model Artifact (GGUF, nếu bật route local):** lưu tệp `.gguf` trên đĩa host/volume chỉ-đọc ở thư mục ngoài kho Git, xác minh checksum SHA-256 trước khi gắn biến môi trường model path; mặc định `live` sử dụng `GEMINI_API_KEY`.
8. **Biến môi trường production:** khởi tạo `/etc/algosim/backend.env` (hoặc tệp `.env` phân quyền `0600`) tham chiếu từ [`backend/.env.example`](../backend/.env.example) (`GEMINI_API_KEY`, `DATABASE_URL=postgresql+psycopg2://...`, `CORS_ALLOW_ORIGINS=https://hoclieu.tech,https://www.hoclieu.tech`, `COOKIE_SECURE=1`, `COOKIE_SAMESITE=lax`, `TRUST_PROXY_HEADERS=1`, `ALGOSIM_PUBLIC_APP_URL=https://hoclieu.tech`, SMTP nếu dùng khôi phục mật khẩu). Không commit tệp env thật vào Git.
9. **Quy trình Migration (Alembic):** trước khi `up -d` trên DB có sẵn dữ liệu, sao lưu `pg_dump -Fc`. Container tự chạy `python alembic/migration_preflight.py --startup && alembic upgrade head` (`ALGOSIM_STARTUP_MODE=1` chặn `DROP TABLE`/`DROP COLUMN`/`TRUNCATE`/`DELETE FROM` và chặn `UNSTAMPED_EXISTING_DATABASE`). Không tự chạy `alembic stamp` trên DB chưa kiểm tra.
10. **Quyền Non-root trong Container:** [`backend/Dockerfile`](../backend/Dockerfile) tạo và chuyển sang user `app`, đặt `ENV HOME=/tmp` (thư mục `/tmp` cho phép ghi file tạm bởi Python/Pillow/PyMuPDF), mount `./backend/scripts:/app/scripts:ro` khi dùng Compose; không dùng container `privileged`.
11. **Reverse Proxy (Nginx) & Ranh giới tin cậy `UVICORN_FORWARDED_ALLOW_IPS`:**
    - Trên VPS dùng Docker Compose override: **chỉ** publish backend ở `127.0.0.1:8000:8000` (không mở `8000` ra public) và thêm `restart: unless-stopped`.
    - Nếu Nginx chạy trực tiếp trên host VPS (`proxy_pass http://127.0.0.1:8000`), giữ `UVICORN_FORWARDED_ALLOW_IPS=127.0.0.1` và `TRUST_PROXY_HEADERS=1`; ứng dụng chỉ tin `X-Forwarded-For` / `X-Forwarded-Proto` khi peer TCP trực tiếp nằm trong `UVICORN_FORWARDED_ALLOW_IPS` và chọn IP hop ngoài cùng bên phải không thuộc dải proxy tin cậy (chặn giả mạo `X-Forwarded-For` chèn từ client). Nginx vẫn phải ghi đè `proxy_set_header X-Forwarded-Proto $scheme; proxy_set_header X-Forwarded-For $remote_addr;` (hoặc `$proxy_add_x_forwarded_for`).
    - Nếu Nginx chạy trong một container Compose riêng giao tiếp qua Docker bridge network, peer IP mà uvicorn nhìn thấy là IP của container/bridge Nginx chứ **không** phải `127.0.0.1`; khi đó phải đặt `UVICORN_FORWARDED_ALLOW_IPS=<IP-hoặc-subnet-bridge-nội-bộ-Nginx>` (tuyệt đối không đặt `*` nếu cổng backend còn mở ra ngoài).
12. **Chứng chỉ HTTPS / TLS:** cấp chứng chỉ Let's Encrypt qua Certbot cho subdomain API (ví dụ `api.hoclieu.tech`) với auto-renew systemd timer và chuyển hướng HTTP `:80` → HTTPS `:443`, bật `Strict-Transport-Security`.
13. **Cấu hình DNS / Subdomain:** tạo bản ghi `A` (hoặc `AAAA`) cho subdomain đề xuất `api.hoclieu.tech` trỏ về IP công khai của VPS khi triển khai; không giả định DNS đã trỏ trước khi VPS sẵn sàng.
14. **CORS:** đặt `CORS_ALLOW_ORIGINS=https://hoclieu.tech,https://www.hoclieu.tech` (`allow_credentials=True`). Tuyệt đối không đặt wildcard `*` khi cho phép gửi cookie phiên.
15. **Cookie & Phiên đăng nhập (`hoclieu.tech` ↔ `api.hoclieu.tech`):** hai tên miền này là **cross-origin nhưng same-site** (cùng site `hoclieu.tech`, cùng HTTPS). Với `COOKIE_SECURE=1`, `HttpOnly=True`, `COOKIE_SAMESITE=lax`, trình duyệt vẫn gửi cookie phiên `algosim_session` cho `fetch(..., { credentials: "include" })` từ `https://hoclieu.tech` tới `https://api.hoclieu.tech`. Không chuyển session token sang `localStorage`.
16. **Bảo vệ CSRF:** lớp bảo vệ kép gồm `SameSite=Lax` + CORS allowlist tường minh + middleware kiểm tra `Origin` / `Referer` / `Sec-Fetch-Site` trên mọi phương thức ghi trạng thái `/api/*` (trừ `/api/preview/hybrid` vốn có cổng từ chối mọi `Origin` riêng); mọi `Origin` lạ hoặc `null` hoặc `Sec-Fetch-Site: cross-site` bị chặn `403`. Không tắt cookie `HttpOnly`/`SameSite`.
17. **Rate Limiting:** lớp ứng dụng chặn brute-force đăng nhập/đăng ký/khôi phục mật khẩu (`AUTH_RATE_LIMIT_MAX_ATTEMPTS=15`, `AUTH_RATE_LIMIT_IP_MAX_ATTEMPTS=240`, cửa sổ `60s`, trả `429` + `Retry-After`, tự đẩy các bucket cũ nhất khi chạm ngưỡng `_AUTH_RATE_MAX_BUCKETS=4096`); đăng nhập thành công hoàn trả 1 slot bucket IP chung để tránh khóa nhầm cả lớp học dùng chung NAT trường học. **Giới hạn kiến trúc:** bộ đếm nằm trong bộ nhớ tiến trình (`per-worker`) — chỉ dùng **1 worker Uvicorn** hoặc gắn thêm store dùng chung / `limit_req_zone` ở Nginx trước khi mở rộng đa worker.
18. **Health vs Readiness (tránh restart loop):** phân tách `/api/diagnostics/runtime` (liveness — không phụ thuộc DB, luôn trả `200` khi tiến trình sống) và `/api/health` (readiness — kiểm tra DB, trả `503 {"ok": false, "dbConnected": false}` khi mất kết nối DB mà không lộ traceback/connection string). Trên VPS/orchestrator, gắn liveness probe vào `/api/diagnostics/runtime` và readiness probe vào `/api/health` để mất kết nối DB thoáng qua không gây vòng lặp restart container.
19. **Logging:** thu log stdout/stderr của Nginx và container backend qua `journald` / Docker json-file với giới hạn xoay vòng (`max-size: 50m`, `max-file: 5`); không in mật khẩu thô, JWT/session token, API key hoặc traceback xuống response HTTP.
20. **Sao lưu & Khôi phục DB:** lên lịch `docker compose exec -T db pg_dump -U algosim -d algosim -Fc > /var/backups/algosim/algosim_$(date +%F_%H%M).dump`, đồng bộ bản sao mã hóa ra ngoài VPS, và diễn tập `pg_restore` vào DB thử nghiệm định kỳ trước mọi lần nâng cấp lớn.
21. **Khởi động lại (Restart):** dùng `docker compose up -d` (với `DEV_RELOAD=0` ở production) hoặc `docker compose restart backend` khi cập nhật config/prompt; không bật `--reload` trên VPS.
22. **Rollback:** giữ tag image ổn định trước đó; nếu gặp lỗi runtime không kèm migration phá hủy, chạy lại image tag cũ hoặc `git revert <commit>` (chỉ tiến tới trên `main`). Nếu có thay đổi schema, khôi phục bản `pg_dump -Fc` đã kiểm chứng trước khi quay lại code cũ.
23. **Firewall VPS (`ufw` / nftables):** chỉ mở `22/tcp` (khuyến nghị giới hạn IP SSH/key-only), `80/tcp`, `443/tcp`; chặn hoàn toàn `5432/tcp` và `8000/tcp` từ bên ngoài.
24. **Kết nối từ Vercel Frontend:** không hardcode `localhost` hay origin giả vào `frontend/vercel.json`. Khi `https://api.hoclieu.tech` đã hoạt động và đóng gói frontend/API base hoặc rewrite phù hợp: lưu ý nếu đi qua Vercel External Rewrite `/api/:path*` có trần nền tảng **120s timeout** và **4.5 MB request body**, còn gọi trực tiếp `https://api.hoclieu.tech` qua CORS + same-site cookie tránh được trần 4.5 MB/120s này khi tải ảnh/PDF bài toán lớn.
25. **Smoke test trên VPS sau triển khai:**
    ```bash
    curl -sS -i https://api.hoclieu.tech/api/diagnostics/runtime
    curl -sS -i https://api.hoclieu.tech/api/health
    curl -sS -i -X OPTIONS https://api.hoclieu.tech/api/auth/login -H "Origin: https://hoclieu.tech" -H "Access-Control-Request-Method: POST"
    curl -sS -i -X POST https://api.hoclieu.tech/api/auth/logout -H "Origin: https://evil.example"   # phải trả 403 (CSRF guard)
    # Kiểm tra đăng nhập sai lặp lại trả 429 + Retry-After, cookie trả HttpOnly; Secure; SameSite=Lax, và x-content-type-options: nosniff
    ```
