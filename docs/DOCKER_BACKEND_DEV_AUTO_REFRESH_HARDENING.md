# DOCKER_BACKEND_DEV_AUTO_REFRESH_HARDENING

> Nhánh `feat/photo-problem-to-scene` · START_HEAD `6989e9e` · `main` `085cae6` (không đổi).
> **0 request Gemini.** Không `down`, không `-v`, không `prune`, không xoá volume, không đụng service `db`.

```text
DOCKER_BACKEND_DEV_AUTO_REFRESH_HARDENING = PASS
SOURCE_CHANGE_ACTION                      = SOURCE_HOT_RELOAD (0 build, 0 dựng lại container)
REQUIREMENTS/DOCKERFILE_CHANGE_ACTION     = IMAGE_REBUILD_REQUIRED
MIGRATION_CHANGE_ACTION                   = MIGRATION_APPROVAL_REQUIRED (dừng TRƯỚC build/start)
FAVICON_CHANGE_ACTION                     = NO_ACTION
PRODUCTION_BEHAVIOR_PARITY                = PASS (CMD trùng từng byte, DEV_RELOAD mặc định 0)
DOCKER_BUILDS_IN_PROOF                    = 1 · BACKEND_RECREATES = 1 · DATABASE_RECREATES = 0
DB_REVISION                               = a1c7e4b90d52 → a1c7e4b90d52 · row-count parity PASS
HEALTHCHECK                               = healthy · GET /api/health = 200
```

## 1. Bệnh đã đo, không phải bệnh suy diễn

`backend/app` được bind mount nên mã trên đĩa **luôn mới**, còn dependency nằm **trong image**.
`pillow` được thêm vào `requirements.txt` (`8bb94ce`), image dựng 2026-08-29 không ai build lại, và
uvicorn chết với `ModuleNotFoundError: No module named 'PIL'` — triệu chứng ở một tầng, nguyên nhân ở
tầng khác. Không lệnh nào trong kho trả lời được câu *"lúc nào PHẢI build lại?"*.

**Git HEAD không trả lời được câu ấy, và sai theo cả hai chiều**: commit tài liệu làm HEAD đổi trong khi
image không cần đụng; sửa `requirements.txt` chưa commit thì HEAD im lặng. Nên điều kiện rebuild phải là
**nội dung những file thật sự đi vào image**, không phải danh tính commit.

## 2. Thiết kế tối thiểu — không watcher, không cơ chế đồng bộ thứ hai

Kho đã có sẵn hai nửa: compose mount `./backend/app:/app/app`, và `CMD` của image có nhánh
`DEV_RELOAD=1` chạy `uvicorn --reload --reload-dir /app/app` kèm `WATCHFILES_FORCE_POLLING=1`. Wave này
**không thêm cơ chế đồng bộ nào** — chỉ thêm thứ còn thiếu:

| Thành phần | Vai trò |
|---|---|
| `docker-compose.dev.yml` | đè **đúng một** biến `DEV_RELOAD: "1"` |
| `backend/Dockerfile` | 4 nhãn danh tính (`git-sha`, `build-time`, `requirements-sha256`, `image-inputs-sha256`) |
| `docker-compose.yml` | build arg cho hai dấu vân tay + **healthcheck** gọi `/api/health` bằng Python của chính image |
| `backend/scripts/dev_backend.py` | phân loại thay đổi · dấu vân tay đầu vào · cổng migration · một lệnh chuẩn |

Lớp dev **không** khai thêm mount, cổng, nguồn biến môi trường, chính sách tự khởi động lại hay cơ chế
đồng bộ file của Docker — mỗi thứ ấy hoặc đã có, hoặc sẽ che lỗi khởi động.

## 3. Hợp đồng năm lớp — suy từ cấu hình build, không từ danh sách viết tay

`doc_mo_hinh()` đọc `Dockerfile` (COPY/WORKDIR), `.dockerignore` và khối `backend` của compose, rồi
`phan_loai_thay_doi()` chấm từng đường dẫn. Ưu tiên: **migration > rebuild > recreate > reload > không làm gì**.

| Sửa gì | Lớp | Hành động |
|---|---|---|
| `backend/app` — tệp `.py` | `SOURCE_HOT_RELOAD` | không lệnh Docker nào |
| `requirements.txt` · `Dockerfile` · `.dockerignore` · `alembic/` · `alembic.ini` | `IMAGE_REBUILD_REQUIRED` | build **riêng** backend một lần |
| compose · `backend/.env` · tệp **không-Python** dưới mount | `CONTAINER_RECREATE_REQUIRED` | dựng lại container backend |
| tệp mới trong `alembic/versions/` | `MIGRATION_APPROVAL_REQUIRED` | **dừng trước build/start** |
| `docs/` · `frontend/` · `backend/tests/` · `backend/scripts/` · bytecode | `NO_ACTION` | không gì cả |

Bằng chứng: `CHANGE_CLASSIFICATION_CONTRACT.json` (20 đường dẫn chấm bằng máy).

⚠️ Tệp **không-Python** dưới mount (prompt trong `app/ai/skills/`) rơi vào lớp *dựng lại*, không phải
*hot reload*: bộ lọc mặc định của uvicorn là `*.py`. Chú thích cũ trong `docker-compose.yml` khai ngược
điều này (*"mọi lần lưu file đều nạp lại — kể cả skills"*) và đã được đính chính trong wave này.

## 4. Dấu vân tay đầu vào image — 10 tệp, và `backend/app` KHÔNG nằm trong đó

```text
IMAGE_INPUTS_SHA256     = 6ebcfdce80ea0040f1371617053b20f76e647a103920eebf67222992911aa93b
IMAGE_INPUTS_FILE_COUNT = 10
```

`.dockerignore` · `Dockerfile` · `alembic.ini` · ba tệp khung của `alembic/` · ba tệp revision ·
`requirements.txt`.

**`backend/app` bị loại có chủ đích**: bind mount `./backend/app:/app/app` che đích của `COPY app ./app`,
nên mã ứng dụng lúc chạy đến từ đĩa host chứ không từ image. Đó chính là lý do sửa `.py` không đòi build lại.

Chuẩn hoá: đường dẫn tương đối gốc repo, dấu `/`, sắp xếp, băm nội dung **sau CRLF sang LF** bằng đúng
helper của cơ chế candidate (`freeze_evaluation_candidate.bam_noi_dung`) — một chính sách cho mọi dấu vân
tay của kho, nên clone lại trên máy khác không làm lệch băm. Không mtime, không quyền, không thứ tự hệ
file. Không bao giờ băm: biến môi trường, `.env`, dump, artifact, Git HEAD.

Wave cũng vá một chỗ lệch giữa **nội dung image** và **dấu vân tay**: mẫu `.dockerignore` neo ở gốc build
context, nên dòng `__pycache__/` chỉ loại thư mục gốc còn bytecode trong `alembic/` vẫn lọt vào image. Đã
thêm hai mẫu bao mọi mức.

## 5. Cổng migration đứng TRƯỚC build/start

`CMD` của image chạy `alembic upgrade head` lúc khởi động. Nghĩa là **chỉ cần start một container trên
image có revision mới là schema đổi âm thầm** — không ai duyệt, không ai sao lưu. Launcher từ chối đi
đường đó: DB khác head nguồn · revision không có trong cây · nhiều head · không đọc được revision ⇒ dừng,
**0 lệnh build, 0 lệnh up** (`MIGRATION_GUARD_PROOF.json`, và fixture `::test_I`, `::test_J`).

Duyệt migration là việc của người, và bước đầu tiên là sao lưu (`pg_dump -Fc`) như wave
`DOCKER_BACKEND_IMAGE_REBUILD_VERIFICATION` đã làm.

## 6. Bằng chứng trên Docker thật

| # | Lệnh | Kết quả |
|---|---|---|
| 1 | `dev_backend.py check` | `REBUILD_IMAGE` · `IMAGE_INPUTS_LABEL_MISSING` (image cũ không mang nhãn) |
| 2 | `dev_backend.py up` | build backend **một lần** rồi dừng ở cổng nhãn (mã 31, xem §7) |
| 3 | `dev_backend.py up` | `RECREATE_CONTAINER` · **0 build** · 1 `up` · `healthy` sau 8 s |
| 4 | `dev_backend.py check` | `REUSE_IMAGE` · exit 0 |

Image `sha256:08f5674f` sang `sha256:099d42d0`, nhãn mang `image-inputs-sha256 = 6ebcfdce…` và
`git-sha = a532f96…`. Container backend dựng lại **một** lần; container `db` **không** bị đụng
(cùng ID, cùng `StartedAt`, vẫn `healthy`).

**Hot reload (`HOT_RELOAD_PROOF.json`)** — tạo tệp dò trong `backend/app` **từ host** (chỉ chú thích,
không import, không dữ liệu):

```text
WatchFiles detected changes in 'app/_dev_reload_probe.py'. Reloading...
Started server process [51]      (trước đó [9])
```

xoá tệp dò ⇒ đúng một lần nạp lại nữa (`[77]`). **Image ID không đổi · container ID không đổi ·
`StartedAt` không đổi · restart = 0 · `/api/health` = 200 · candidate vẫn khớp · tệp dò không còn trên
host lẫn trong container.**

**Dữ liệu (`DATABASE_PARITY.json`)**: revision `a1c7e4b90d52` trước và sau, 11 bảng, **mọi số hàng trùng
khít**, 0 dòng `Running upgrade` trong log container mới, `DATABASE_RECREATES = 0`.

**Production (`PRODUCTION_BEHAVIOR_PARITY.json`)**: render `docker compose -f docker-compose.yml config`
(KHÔNG kèm lớp dev) ở `6989e9e` và ở cây hiện tại — **không khác biệt nào** ngoài healthcheck mới thêm;
`CMD` trong `Dockerfile` **trùng từng byte**; `DEV_RELOAD` mặc định vẫn `0`; cổng vẫn `8000:8000`.

## 7. Một sự cố đã quan sát, chưa dựng lại được — và bản vá cho nó

Ở bước 2, `docker compose build` chạy xong và image trên đĩa **mang đủ bốn nhãn**, nhưng lượt
`docker image inspect` ngay sau đó trả về nhãn **cũ**, nên launcher từ chối start (mã 31). Sáu lượt build
đối chứng trên một project dùng-một-lần (có và không có lớp thật) **không dựng lại được** hiện tượng: 6/6
đọc thấy nhãn mới ngay lập tức.

Bản vá **không** đoán nguyên nhân: nó biến một lượt đọc thành **đọc lại có giới hạn** (tối đa 5 lượt, cách
1 s) và **in ra giá trị đọc được** khi thất bại. Đây là đọc lại, **không phải build lại** — build hỏng vẫn
chỉ chạy đúng một lần (`::test_T`). Hai cổng mới khoá cả hai chiều: `::test_U` (hụt một nhịp ⇒ vẫn start,
đúng 1 build) và `::test_V` (không bao giờ khớp ⇒ **không** start, vẫn đúng 1 build).

## 8. Cổng offline và phép tiêm lỗi

Nền đỏ **23/23** trước khi viết một dòng mã (module và tệp override chưa tồn tại). Nay **25 pass**.
Suite backend đầy đủ: **5261 pass**, một ca đỏ **từ trước và do môi trường** —
`test_holdout_readiness_7b` đòi `git status` rỗng, trong khi cây mang sẵn xoá favicon của user.
Candidate `544a0b56…` và khoá cache `CACHE_VERSION 95` đều khớp (wave không chạm `backend/app`).

Mười phép tiêm, **10/10 đỏ đúng cổng**, khôi phục **trùng từng byte**, không để lại dấu:

| | Tiêm | Cổng đỏ |
|---|---|---|
| F1 | bỏ `requirements.txt` khỏi dấu vân tay | `::test_B` |
| F2 | sửa `.py` của app lại đòi build | `::test_A`, `::test_N` |
| F3 | gỡ cổng migration | `::test_I`, `::test_J` |
| F4 | production bật reload | `::test_L` |
| F5 | favicon kích hoạt build | `::test_F` |
| F6 | healthcheck gọi sai endpoint | `::test_M` |
| F7 | launcher in bí mật | `::test_P` |
| F8 | build cả stack | `::test_R` |
| F9 | băm phụ thuộc thứ tự tệp | `::test_O` |
| F10 | build hỏng bị thử lại | `::test_T`, `::test_V` |

⚠️ **F6 bắt được chính cổng của nó đang nói dối.** Bản đầu của `::test_M` kiểm bằng `in`, mà đường dẫn
`/api/healthz` **chứa** `/api/health` như chuỗi con — cổng xanh cho một healthcheck sai endpoint. Nay so
bằng regex có biên. Đây đúng là bài học `CLAUDE.md §2b 3b`: *guard đang đỏ cũng có thể đang nói dối*, và
chỉ phép tiêm mới lộ ra.

## 9. Giới hạn — đọc trước khi trích

- **KHÔNG tuyên bố "production deployment automation đã hoàn tất".** Wave này là **vòng phát triển trên
  một máy**. Không đụng CI, không đụng triển khai, không đụng nhiều máy hay nhiều môi trường.
- Sự cố ở §7 **chưa có nguyên nhân gốc**, chỉ có bản vá chịu được nó và nói ra khi nó xảy ra.
- Dấu vân tay phủ *tệp* đi vào image; đổi **khối `build:` của compose** (context, thêm build arg) không tự
  đổi dấu vân tay — nó rơi vào lớp *dựng lại container*.
- `--reload` chỉ theo dõi `*.py`. Prompt trong `app/ai/skills/` vẫn cần `docker compose restart backend`.
- Polling của WatchFiles có giá (`OPERATIONS.md`: một lượt pytest đầy đủ không xong trong 10 phút khi
  `DEV_RELOAD=1`). Lệnh chuẩn là **cho vòng sửa mã**, không cho lượt đo.
- Healthcheck thêm một dòng truy cập vào log mỗi 30 s. Đó là giá của việc `docker ps` nói thật.
- Cổng migration đóng luôn khi DB **chưa từng migrate** (chưa có bảng `alembic_version`) hoặc khi không
  đọc được revision. Đó là chủ đích: im lặng ở chỗ này đắt hơn một lần dừng thừa.

## 10. Dùng nó

```bash
backend/.venv/Scripts/python.exe backend/scripts/dev_backend.py up          # lệnh chuẩn
backend/.venv/Scripts/python.exe backend/scripts/dev_backend.py check       # chỉ đọc, MỘT quyết định
backend/.venv/Scripts/python.exe backend/scripts/dev_backend.py classify    # cây làm việc rơi vào lớp nào
backend/.venv/Scripts/python.exe backend/scripts/dev_backend.py fingerprint --files
```

Artifact: `docs/evaluation/geometry/photo-problem-to-scene/docker-backend-dev-auto-refresh/` (12 tệp).
Tài liệu vận hành: `docs/OPERATIONS.md` (mục *"Vòng phát triển backend"*).

`NEXT_ACTION = SYNTHESIS_VISUAL_OBLIGATION_COVERAGE_GATE`
