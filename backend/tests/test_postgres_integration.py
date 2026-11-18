# -*- coding: utf-8 -*-
"""DB-HARDEN-2 — smoke tích hợp PostgreSQL THẬT (opt-in).

Mục đích: bắt lỗi dialect/migration mà SQLite không đảm bảo được. Chạy:

    pytest -m postgres

Mặc định `pytest` KHÔNG chạy file này (marker `postgres` bị addopts loại ra),
nên workflow offline vẫn nhanh, không cần Docker.

CÔ LẬP TUYỆT ĐỐI: spin một container Postgres throwaway tên duy nhất, **KHÔNG
mount volume** — dữ liệu nằm ở lớp ghi ephemeral của container, `docker rm -f`
xoá sạch. Vì vậy test này KHÔNG BAO GIỜ đụng `pgdata` của dev. Tự skip (kèm
thông báo rõ) nếu thiếu psycopg2 hoặc Docker.

Dùng host port CỐ ĐỊNH (một free port chọn lúc setup) chứ không phải random:
Docker Desktop ĐỔI host port của publish-ngẫu-nhiên sau `docker restart`, làm
URL cũ trỏ nhầm. Cổng cố định thì bền qua restart.

Kiểm chứng trong một luồng: upgrade→head, `alembic_version` == head, ghi/đọc/
sửa qua MODEL THẬT, **restart container** rồi reconnect (dữ liệu bền qua lần DB
khởi động lại), cuối cùng `alembic check` sạch trên chính dialect Postgres.
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import pytest

pytestmark = pytest.mark.postgres

# Thiếu driver → skip cả module (không phải lỗi).
psycopg2 = pytest.importorskip(
    "psycopg2", reason="cần psycopg2-binary để chạy smoke Postgres"
)

BACKEND_DIR = Path(__file__).resolve().parents[1]
PG_IMAGE = "postgres:16-alpine"


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def _run_pg_ctl(cmd: list[str], out_path: Path) -> tuple[int, str]:
    """Run pg_ctl without PIPE handles so daemonized Windows postgres.exe never hangs communicate()."""
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(
        subprocess, "CREATE_NEW_PROCESS_GROUP", 0
    )
    with out_path.open("w", encoding="utf-8", errors="replace") as fh:
        res = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=fh,
            stderr=subprocess.STDOUT,
            close_fds=True,
            creationflags=flags,
        )
    text = out_path.read_text(encoding="utf-8", errors="replace") if out_path.exists() else ""
    return res.returncode, text


def _docker_ok() -> bool:
    try:
        return _run(["docker", "info"]).returncode == 0
    except FileNotFoundError:
        return False


def _local_pg_bin_dir() -> Path | None:
    """Locate isolated local PostgreSQL 16 binaries if Docker daemon is unavailable."""
    candidates: list[Path] = []
    env_bin = os.environ.get("ALGOSIM_PG16_BIN")
    if env_bin:
        candidates.append(Path(env_bin))
    for base in Path(__file__).resolve().parents:
        candidates.append(base / ".superpowers" / "pgsql16" / "pgsql" / "bin")
        candidates.append(base / "algo-sim" / ".superpowers" / "pgsql16" / "pgsql" / "bin")
    for cand in candidates:
        if (cand / "initdb.exe").is_file() and (cand / "pg_ctl.exe").is_file():
            return cand
        if (cand / "initdb").is_file() and (cand / "pg_ctl").is_file():
            return cand
    return None


def restart_pg(pg_info: dict) -> None:
    """Restart the isolated PostgreSQL 16 process across both Docker and local pg_ctl modes."""
    if pg_info.get("mode") == "local_pg_ctl":
        out_path = Path(pg_info["pgdata"]).parent / "pg_ctl_restart.out"
        rc, out_txt = _run_pg_ctl(
            [
                pg_info["pg_ctl"],
                "-D",
                pg_info["pgdata"],
                "-l",
                pg_info["pglog"],
                "-w",
                "-o",
                f"-p {pg_info['port']} -h 127.0.0.1",
                "restart",
            ],
            out_path,
        )
        assert rc == 0, out_txt
    else:
        res = _run(["docker", "restart", pg_info["name"]])
        assert res.returncode == 0, res.stderr
    assert _pg_ready(pg_info["port"], pg_info["pw"], pg_info["db"]), \
        "Postgres không sẵn sàng lại sau restart"


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _pg_ready(port: str, pw: str, dbname: str, timeout: int = 45) -> bool:
    """Poll tới khi Postgres nhận kết nối TCP (hoặc hết giờ). True nếu sẵn sàng."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            psycopg2.connect(
                host="127.0.0.1", port=port, user="postgres",
                password=pw, dbname=dbname, connect_timeout=3,
            ).close()
            return True
        except Exception:  # noqa: BLE001 — poll cho tới khi server lên
            time.sleep(1)
    return False


def _alembic(args: list[str], url: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "DATABASE_URL": url}
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="module")
def pg_container():
    """Isolated throwaway PostgreSQL 16 instance (Docker container or local pg_ctl data dir)."""
    if not _docker_ok():
        bin_dir = _local_pg_bin_dir()
        if bin_dir is None:
            pytest.skip("Docker không khả dụng và chưa có local PostgreSQL 16 binaries.")
        pw = "algosim_test_pw"
        dbname = "algosim_test"
        port = str(_free_port())
        tmp_root = Path(tempfile.mkdtemp(prefix="algosim-pg16-"))
        pgdata = tmp_root / "data"
        pglog = tmp_root / "postgres.log"
        pwfile = tmp_root / "pw.txt"
        pwfile.write_text(pw, encoding="utf-8")
        init_cmd = [
            str(bin_dir / ("initdb.exe" if (bin_dir / "initdb.exe").is_file() else "initdb")),
            "-D", str(pgdata),
            "-U", "postgres",
            f"--pwfile={pwfile}",
            "-A", "scram-sha-256",
            "-E", "UTF8",
            "--locale=C",
        ]
        init_res = _run(init_cmd)
        pwfile.unlink(missing_ok=True)
        if init_res.returncode != 0:
            shutil.rmtree(tmp_root, ignore_errors=True)
            pytest.skip(f"initdb PostgreSQL 16 thất bại: {init_res.stderr}")
        pg_ctl_bin = str(bin_dir / ("pg_ctl.exe" if (bin_dir / "pg_ctl.exe").is_file() else "pg_ctl"))
        start_rc, start_out = _run_pg_ctl(
            [
                pg_ctl_bin, "-D", str(pgdata), "-l", str(pglog),
                "-w", "-o", f"-p {port} -h 127.0.0.1", "start",
            ],
            tmp_root / "pg_ctl_start.out",
        )
        if start_rc != 0:
            log_tail = pglog.read_text(encoding="utf-8", errors="ignore") if pglog.exists() else ""
            shutil.rmtree(tmp_root, ignore_errors=True)
            pytest.skip(f"pg_ctl start thất bại: {start_out}\n{log_tail}")
        try:
            if not _pg_ready(port, pw, "postgres"):
                pytest.skip("Postgres cục bộ không sẵn sàng kịp khi khởi tạo.")
            conn = psycopg2.connect(host="127.0.0.1", port=port, user="postgres", password=pw, dbname="postgres")
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE {dbname};")
            conn.close()
            url = f"postgresql+psycopg2://postgres:{pw}@127.0.0.1:{port}/{dbname}"
            yield {
                "url": url,
                "name": f"local-pg16-{port}",
                "port": port,
                "pw": pw,
                "db": dbname,
                "mode": "local_pg_ctl",
                "pgdata": str(pgdata),
                "pg_ctl": pg_ctl_bin,
                "pglog": str(pglog),
            }
        finally:
            _run_pg_ctl(
                [pg_ctl_bin, "-D", str(pgdata), "-m", "immediate", "stop"],
                tmp_root / "pg_ctl_stop.out",
            )
            shutil.rmtree(tmp_root, ignore_errors=True)
        return

    # Pull tường minh trước: tách độ trễ tải image (lần đầu ~vài chục giây) khỏi
    # vòng chờ readiness, tránh skip oan trên máy chưa có image sẵn.
    pull = _run(["docker", "pull", PG_IMAGE])
    if pull.returncode != 0:
        pytest.skip(f"Không pull được image {PG_IMAGE}: {pull.stderr}")

    name = f"algosim-pgtest-{uuid.uuid4().hex[:8]}"
    pw = "algosim_test_pw"
    dbname = "algosim_test"
    port = str(_free_port())  # cố định → bền qua docker restart
    up = _run([
        "docker", "run", "-d", "--name", name,
        "-e", f"POSTGRES_PASSWORD={pw}",
        "-e", f"POSTGRES_DB={dbname}",
        "-p", f"127.0.0.1:{port}:5432",  # cổng cố định trên loopback; KHÔNG -v
        PG_IMAGE,
    ])
    if up.returncode != 0:
        pytest.skip(f"Không tạo được container Postgres: {up.stderr}")

    try:
        url = f"postgresql+psycopg2://postgres:{pw}@127.0.0.1:{port}/{dbname}"
        if not _pg_ready(port, pw, dbname):
            pytest.skip("Postgres không sẵn sàng kịp khi khởi tạo.")
        yield {"url": url, "name": name, "port": port, "pw": pw, "db": dbname, "mode": "docker"}
    finally:
        removed = _run(["docker", "rm", "-f", name])
        # dọn dẹp phải thành công (không để container rác)
        assert removed.returncode == 0, removed.stderr
        assert name not in _run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"]
        ).stdout


def test_postgres_migrate_persist_reconnect(pg_container):
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    from app.persistence import db  # model THẬT của app (dialect-neutral)

    url = pg_container["url"]
    name = pg_container["name"]

    # 1. migrate DB Postgres mới tinh tới head
    up = _alembic(["upgrade", "head"], url)
    assert up.returncode == 0, up.stderr

    # 2. alembic_version khớp head thật của migration scripts
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    head = ScriptDirectory.from_config(cfg).get_current_head()
    eng = create_engine(url)
    with eng.connect() as c:
        ver = c.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert ver == head, f"alembic_version={ver} != head={head}"

    Session = sessionmaker(bind=eng)

    # 3. GHI qua model thật
    with Session() as s:
        s.add(db.SimulationCache(
            key="pgsmoke", problem_text="đề smoke Postgres",
            simulation_id="algorithm.bubble_sort", envelope_json="{}",
            dsl_version="1", policy_version="6",
        ))
        s.commit()

    # 4. ĐỌC lại
    with Session() as s:
        row = s.query(db.SimulationCache).filter_by(key="pgsmoke").one()
        assert row.simulation_id == "algorithm.bubble_sort"
        assert row.hit_count == 0

    # 5. SỬA + verify
    with Session() as s:
        s.query(db.SimulationCache).filter_by(key="pgsmoke").one().hit_count = 7
        s.commit()
    with Session() as s:
        assert s.query(db.SimulationCache).filter_by(key="pgsmoke").one().hit_count == 7
    eng.dispose()

    # 6. RESTART PostgreSQL process (Docker hoặc local pg_ctl) → dữ liệu vẫn bền
    restart_pg(pg_container)

    eng2 = create_engine(url)
    Session2 = sessionmaker(bind=eng2)
    with Session2() as s:  # reconnect vẫn dùng được + dữ liệu sống sót restart
        assert s.query(db.SimulationCache).filter_by(key="pgsmoke").one().hit_count == 7

    # 7. alembic check sạch trên chính dialect Postgres (độ tin cậy dialect)
    chk = _alembic(["check"], url)
    assert chk.returncode == 0, chk.stdout + chk.stderr
    assert "No new upgrade operations detected" in (chk.stdout + chk.stderr)
    eng2.dispose()
