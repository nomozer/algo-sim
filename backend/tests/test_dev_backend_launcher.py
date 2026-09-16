# -*- coding: utf-8 -*-
"""VÒNG PHÁT TRIỂN BACKEND DOCKER — hot reload source, rebuild CHỈ khi đầu vào image đổi, chặn migration. 0 mạng, 0 Docker.

`DOCKER_BACKEND_DEV_AUTO_REFRESH_HARDENING` (2026-09-15). Lỗi đã đo: `backend/app` được bind mount nên mã luôn mới, còn
dependency nằm trong image build ngày 2026-08-29 — `pillow` thêm vào `requirements.txt` mà image không build lại, và
uvicorn chết với `ModuleNotFoundError`. Không lệnh nào cho biết lúc nào PHẢI build lại.

Hợp đồng ở đây: phân loại thay đổi theo ĐÚNG những gì Dockerfile chép vào image (không theo Git HEAD), dấu vân tay tất
định của các đầu vào ấy, và một launcher gọi Docker qua transport tiêm được — nên toàn bộ file này chạy không cần Docker.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
SCRIPTS = GOC / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

KHOA_GIA = "AIzaSyFAKE-DEVBACKEND-0123456789"
MAT_KHAU_GIA = "postgresql+psycopg2://nguoi:MATKHAUGIA42@db:5432/x"


@pytest.fixture
def DB():
    import dev_backend as m  # noqa: PLC0415 — nạp trễ: mỗi test phải ĐỎ riêng trước khi launcher tồn tại

    return m


# ══ kho giả: một repository tối thiểu, nằm dưới đường dẫn CÓ KHOẢNG TRẮNG ══════════
def _kho_gia(tmp_path: Path, *, entrypoint: bool = False) -> Path:
    g = tmp_path / "kho co khoang trang" / "algo sim"
    (g / "backend" / "app" / "ai").mkdir(parents=True)
    (g / "backend" / "alembic" / "versions").mkdir(parents=True)
    (g / "backend" / "scripts").mkdir(parents=True)
    (g / "docs").mkdir()
    (g / "frontend" / "public").mkdir(parents=True)
    shutil.copy(GOC / "docker-compose.yml", g / "docker-compose.yml")
    if (GOC / "docker-compose.dev.yml").exists():
        shutil.copy(GOC / "docker-compose.dev.yml", g / "docker-compose.dev.yml")
    dockerfile = (GOC / "backend" / "Dockerfile").read_text(encoding="utf-8")
    if entrypoint:
        dockerfile = dockerfile.replace("COPY alembic.ini ./alembic.ini",
                                        "COPY alembic.ini ./alembic.ini\nCOPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh")
        (g / "backend" / "docker-entrypoint.sh").write_text("#!/bin/sh\nexec \"$@\"\n", encoding="utf-8")
    (g / "backend" / "Dockerfile").write_text(dockerfile, encoding="utf-8")
    shutil.copy(GOC / "backend" / ".dockerignore", g / "backend" / ".dockerignore")
    (g / "backend" / "requirements.txt").write_text("fastapi\npillow\n", encoding="utf-8")
    (g / "backend" / "alembic.ini").write_text("[alembic]\nscript_location = alembic\n", encoding="utf-8")
    (g / "backend" / "alembic" / "env.py").write_text("# env\n", encoding="utf-8")
    (g / "backend" / "alembic" / "versions" / "r1_goc.py").write_text(
        'revision: str = "r1"\ndown_revision = None\n', encoding="utf-8")
    (g / "backend" / "alembic" / "versions" / "r2_tiep.py").write_text(
        'revision: str = "r2"\ndown_revision: str = "r1"\n', encoding="utf-8")
    (g / "backend" / "app" / "main.py").write_text("app = None\n", encoding="utf-8")
    (g / "backend" / "app" / "ai" / "prompt.md").write_text("# prompt\n", encoding="utf-8")
    (g / "backend" / "scripts" / "cong_cu.py").write_text("print('x')\n", encoding="utf-8")
    (g / "backend" / ".env").write_text(f"GEMINI_API_KEY={KHOA_GIA}\n", encoding="utf-8")
    (g / "docs" / "GHI_CHU.md").write_text("# ghi chú\n", encoding="utf-8")
    (g / "frontend" / "public" / "favicon.svg").write_text("<svg/>\n", encoding="utf-8")
    return g


# ══ transport Docker/Git giả ═══════════════════════════════════════════════════
class DockerGia:
    """Trả lời lệnh theo token; ghi lại MỌI argv. Không mạng, không tiến trình con."""

    def __init__(self, goc: Path, *, db_revision="r2", image_labels=None, image_present=True, build_rc=0, up_rc=0,
                 container=True, container_hash="HASHDEV", container_dev="DEV_RELOAD=1", image_id="sha256:IMG",
                 container_image="sha256:IMG", suc_khoe=("starting", "healthy"), porcelain="", secret_out=""):
        self.goc, self.calls = goc, []
        self.db_revision, self.image_labels, self.image_present = db_revision, image_labels, image_present
        self.build_rc, self.up_rc, self.container = build_rc, up_rc, container
        self.container_hash, self.container_dev, self.image_id, self.container_image = container_hash, container_dev, image_id, container_image
        self.suc_khoe, self.porcelain, self.secret_out = list(suc_khoe), porcelain, secret_out
        self.built = False

    def __call__(self, argv, env=None):
        self.calls.append((list(argv), dict(env or {})))
        a = list(argv)
        noi = " ".join(a)
        if a[:1] == ["git"]:
            if "rev-parse" in a:
                return 0, "6989e9e7e3033144a0a00ae5bcbb3355fe4967a8\n", ""
            if "status" in a:
                return 0, self.porcelain, ""
            return 1, "", "git lạ"
        if "compose" in a and "config" in a and "--images" in a:
            return 0, "algo-sim-backend\n", ""
        if "compose" in a and "config" in a and "--hash" in a:
            return 0, "backend HASHDEV\n", ""
        if "compose" in a and "build" in a:
            self.built = self.build_rc == 0
            if self.built:  # image vừa build mang nhãn từ build arg — đúng như Dockerfile ghi
                e = env or {}
                self.image_labels = {"org.algosim.backend.image-inputs-sha256": e.get("IMAGE_INPUTS_SHA256"),
                                     "org.algosim.backend.git-sha": e.get("GIT_SHA")}
            return self.build_rc, "", f"lỗi build {self.secret_out}" if self.build_rc else ""
        if "compose" in a and "up" in a:
            if self.up_rc == 0:  # compose tạo lại container theo image + cấu hình dev hiện tại
                self.container, self.container_hash, self.container_dev = True, "HASHDEV", "DEV_RELOAD=1"
                self.container_image = self.image_id
            return self.up_rc, "", f"lỗi up {self.secret_out}" if self.up_rc else ""
        if "compose" in a and "ps" in a:
            svc = a[-1]
            if svc == "db":
                return 0, "dbid\n", ""
            return 0, ("cid\n" if self.container else ""), ""
        if "compose" in a and "exec" in a:
            return 0, f"{self.db_revision}\n", ""
        if a[1:3] == ["image", "inspect"]:
            if not self.image_present and not self.built:
                return 1, "", "No such image"
            if "Labels" in noi:
                return 0, json.dumps(self.image_labels or {}) + "\n", ""
            return 0, f"{self.image_id}\n", ""
        if a[1:2] == ["inspect"] and "dbid" in a:
            return 0, "running|healthy\n", ""
        if a[1:2] == ["inspect"] and "cid" in a:
            if "Health" in noi and "Image" not in noi:
                return 0, "running|" + (self.suc_khoe.pop(0) if len(self.suc_khoe) > 1 else self.suc_khoe[0]) + "\n", ""
            return 0, f"{self.container_image}|{self.container_hash}|running|healthy|{self.container_dev}\n", ""
        return 1, "", f"lệnh giả không biết: {noi}"


def _dieu_khien(DB, goc, docker, in_ra=None):
    ra = [] if in_ra is None else in_ra
    return DB.DieuKhien(goc, chay=docker, ngu=lambda s: None, dong_ho=iter(range(0, 10_000)).__next__, in_ra=ra.append), ra


def _nhan_khop(DB, goc):
    return {DB.NHAN_INPUTS: DB.dau_van_anh(goc)["sha256"], DB.NHAN_GIT: "6989e9e7e3033144a0a00ae5bcbb3355fe4967a8"}


def _lenh(docker, *tok):
    return [a for a, _ in docker.calls if all(t in a for t in tok)]


# ══ A–F · phân loại thay đổi ════════════════════════════════════════════════════
def test_A_sua_Python_duoc_mount__SOURCE_HOT_RELOAD__khong_rebuild(DB, tmp_path):
    g = _kho_gia(tmp_path)
    mh = DB.doc_mo_hinh(g)
    assert DB.phan_loai_thay_doi(["backend/app/main.py"], mh)["class"] == DB.SOURCE_HOT_RELOAD
    truoc = DB.dau_van_anh(g)["sha256"]
    (g / "backend" / "app" / "main.py").write_text("app = 1  # sửa\n", encoding="utf-8")
    assert DB.dau_van_anh(g)["sha256"] == truoc
    docker = DockerGia(g, image_labels={DB.NHAN_INPUTS: truoc})
    dk, _ = _dieu_khien(DB, g, docker)
    assert dk.kiem_tra()["decision"] == DB.REUSE_IMAGE


def test_B_doi_requirements__REBUILD_IMAGE(DB, tmp_path):
    g = _kho_gia(tmp_path)
    mh = DB.doc_mo_hinh(g)
    assert DB.phan_loai_thay_doi(["backend/requirements.txt"], mh)["class"] == DB.IMAGE_REBUILD_REQUIRED
    cu = _nhan_khop(DB, g)
    (g / "backend" / "requirements.txt").write_text("fastapi\npillow\nnumpy\n", encoding="utf-8")
    docker = DockerGia(g, image_labels=cu)
    dk, _ = _dieu_khien(DB, g, docker)
    kq = dk.kiem_tra()
    assert kq["decision"] == DB.REBUILD_IMAGE and "IMAGE_INPUTS_CHANGED" in kq["reasons"]


def test_C_doi_Dockerfile__REBUILD_IMAGE(DB, tmp_path):
    g = _kho_gia(tmp_path)
    mh = DB.doc_mo_hinh(g)
    assert DB.phan_loai_thay_doi(["backend/Dockerfile"], mh)["class"] == DB.IMAGE_REBUILD_REQUIRED
    truoc = DB.dau_van_anh(g)["sha256"]
    with (g / "backend" / "Dockerfile").open("a", encoding="utf-8") as f:
        f.write("\n# đổi\n")
    assert DB.dau_van_anh(g)["sha256"] != truoc


def test_D_doi_entrypoint_duoc_COPY__REBUILD_IMAGE(DB, tmp_path):
    g = _kho_gia(tmp_path, entrypoint=True)
    mh = DB.doc_mo_hinh(g)
    assert "backend/docker-entrypoint.sh" in DB.danh_sach_dau_vao_anh(g, mh)
    assert DB.phan_loai_thay_doi(["backend/docker-entrypoint.sh"], mh)["class"] == DB.IMAGE_REBUILD_REQUIRED


def test_E_doi_docs__NO_ACTION(DB, tmp_path):
    mh = DB.doc_mo_hinh(_kho_gia(tmp_path))
    kq = DB.phan_loai_thay_doi(["docs/GHI_CHU.md", "backend/tests/test_x.py", "README.md"], mh)
    assert kq["class"] == DB.NO_ACTION and {p["class"] for p in kq["paths"]} == {DB.NO_ACTION}


def test_F_xoa_favicon__NO_ACTION__va_KHONG_lam_backend_ban(DB, tmp_path):
    g = _kho_gia(tmp_path)
    mh = DB.doc_mo_hinh(g)
    assert DB.phan_loai_thay_doi(["frontend/public/favicon.svg"], mh)["class"] == DB.NO_ACTION
    docker = DockerGia(g, image_labels=_nhan_khop(DB, g), porcelain=" D frontend/public/favicon.svg\n")
    dk, _ = _dieu_khien(DB, g, docker)
    kq = dk.kiem_tra()
    assert kq["BACKEND_SOURCE_DIRTY"] is False and kq["decision"] == DB.REUSE_IMAGE
    docker2 = DockerGia(g, image_labels=_nhan_khop(DB, g), porcelain=" M backend/requirements.txt\n")
    assert _dieu_khien(DB, g, docker2)[0].kiem_tra()["BACKEND_SOURCE_DIRTY"] is True


def test_phan_loai_migration_moi_va_cau_hinh_runtime(DB, tmp_path):
    mh = DB.doc_mo_hinh(_kho_gia(tmp_path))
    assert DB.phan_loai_thay_doi(["backend/alembic/versions/r3_moi.py"], mh)["class"] == DB.MIGRATION_APPROVAL_REQUIRED
    assert DB.phan_loai_thay_doi(["docker-compose.yml"], mh)["class"] == DB.CONTAINER_RECREATE_REQUIRED
    assert DB.phan_loai_thay_doi(["backend/.env"], mh)["class"] == DB.CONTAINER_RECREATE_REQUIRED
    kq = DB.phan_loai_thay_doi(["docs/a.md", "backend/app/main.py", "backend/requirements.txt", "backend/alembic/versions/r3.py"], mh)
    assert kq["class"] == DB.MIGRATION_APPROVAL_REQUIRED  # ưu tiên: migration > rebuild > recreate > reload > không làm gì


# ══ G–J · quyết định và cổng migration ═════════════════════════════════════════
def test_G_image_KHONG_ton_tai__IMAGE_MISSING(DB, tmp_path):
    g = _kho_gia(tmp_path)
    dk, _ = _dieu_khien(DB, g, DockerGia(g, image_present=False))
    assert dk.kiem_tra()["decision"] == DB.IMAGE_MISSING


def test_H_dau_van_image_KHOP__REUSE_IMAGE__khong_build(DB, tmp_path):
    g = _kho_gia(tmp_path)
    docker = DockerGia(g, image_labels=_nhan_khop(DB, g))
    dk, _ = _dieu_khien(DB, g, docker)
    assert dk.kiem_tra()["decision"] == DB.REUSE_IMAGE
    assert dk.up() == 0 and _lenh(docker, "compose", "build") == []


def test_I_DB_revision_KHAC_head__MIGRATION_APPROVAL_REQUIRED(DB, tmp_path):
    g = _kho_gia(tmp_path)
    for rev, ly_do in (("r1", "MIGRATION_PENDING"), ("r9", "DB_REVISION_NOT_IN_SOURCE_CHAIN"), ("", "DB_REVISION_UNKNOWN")):
        dk, _ = _dieu_khien(DB, g, DockerGia(g, db_revision=rev, image_labels=_nhan_khop(DB, g)))
        kq = dk.kiem_tra()
        assert kq["decision"] == DB.MIGRATION_APPROVAL_REQUIRED and ly_do in kq["reasons"], (rev, kq)
    (g / "backend" / "alembic" / "versions" / "r2b_nhanh.py").write_text('revision = "r2b"\ndown_revision = "r1"\n', encoding="utf-8")
    kq = _dieu_khien(DB, g, DockerGia(g, db_revision="r2", image_labels=_nhan_khop(DB, g)))[0].kiem_tra()
    assert kq["decision"] == DB.MIGRATION_APPROVAL_REQUIRED and "MIGRATION_HEADS_NOT_SINGLE" in kq["reasons"]


def test_J_migration_cho__launcher_KHONG_goi_build_hay_start(DB, tmp_path):
    g = _kho_gia(tmp_path)
    docker = DockerGia(g, db_revision="r1", image_present=False)
    dk, _ = _dieu_khien(DB, g, docker)
    assert dk.up() != 0
    assert _lenh(docker, "compose", "build") == [] and _lenh(docker, "compose", "up") == []


# ══ K–M · dev reload, production, healthcheck (file thật của repository) ═════════
def _khoi_dich_vu(noi: str, ten: str) -> str:
    m = re.search(rf"(?ms)^  {ten}:\s*\n(.*?)(?=^  \S|^\S|\Z)", noi)
    assert m, ten
    return m.group(1)


def test_K_dev_override_bat_reload_dung_thu_muc_Python(DB):
    dev = (GOC / "docker-compose.dev.yml").read_text(encoding="utf-8")
    assert re.search(r'DEV_RELOAD:\s*"1"', _khoi_dich_vu(dev, "backend"))
    df = (GOC / "backend" / "Dockerfile").read_text(encoding="utf-8")
    assert re.search(r'DEV_RELOAD" = "1".*--reload --reload-dir /app/app', df, re.S)
    assert DB.doc_mo_hinh(GOC).compose_files[-1].endswith("docker-compose.dev.yml")
    for bo in ("volumes:", "ports:", "ALLOW_LIVE_AI", "env_file", "restart:", "develop:", "watch:"):
        assert bo not in dev, bo


def test_L_production_KHONG_reload__CMD_giu_nguyen(DB):
    df = (GOC / "backend" / "Dockerfile").read_text(encoding="utf-8")
    assert "ENV DEV_RELOAD=0" in df
    cmd = next(d for d in df.splitlines() if d.startswith("CMD "))
    assert cmd == ('CMD alembic upgrade head &&     if [ "$DEV_RELOAD" = "1" ]; then       WATCHFILES_FORCE_POLLING=1 exec uvicorn '
                   'app.main:app --host 0.0.0.0         --port 8000 --reload --reload-dir /app/app;     else       exec uvicorn '
                   'app.main:app --host 0.0.0.0 --port 8000;     fi')
    co_so = _khoi_dich_vu((GOC / "docker-compose.yml").read_text(encoding="utf-8"), "backend")
    assert re.search(r"DEV_RELOAD:\s*\$\{DEV_RELOAD:-0\}", co_so)
    assert '"8000:8000"' in co_so and "restart:" not in co_so


def test_M_healthcheck_dung_api_health__Python_stdlib(DB):
    co_so = _khoi_dich_vu((GOC / "docker-compose.yml").read_text(encoding="utf-8"), "backend")
    hc = re.search(r"(?ms)^    healthcheck:\s*\n(.*?)(?=^    \S|\Z)", co_so)
    assert hc, "backend thiếu healthcheck"
    khoi = hc.group(1)
    # ĐÚNG endpoint, không phải một endpoint BẮT ĐẦU BẰNG nó: `/api/healthz` chứa `/api/health` như
    # chuỗi con, và phép tiêm F6 đã chứng minh phiên bản `in` của cổng này không phân biệt được hai cái.
    assert re.search(r"http://localhost:8000/api/health(?![\w/])", khoi), khoi
    assert "urllib.request" in khoi and "curl" not in khoi
    for k in ("interval:", "timeout:", "start_period:", "retries:"):
        assert k in khoi, k


# ══ N–Q · dấu vân tay ══════════════════════════════════════════════════════════
def test_N_hash_tat_dinh_qua_hai_lan_chay(DB, tmp_path):
    g = _kho_gia(tmp_path)
    a, b = DB.dau_van_anh(g), DB.dau_van_anh(g)
    assert a == b and re.fullmatch(r"[0-9a-f]{64}", a["sha256"]) and a["file_count"] == len(a["files"])
    assert ".env" not in " ".join(a["files"]) and all(not f.startswith("backend/app/") for f in a["files"])


def test_O_thu_tu_file_KHONG_doi_hash__CRLF_theo_chinh_sach(DB, tmp_path):
    g = _kho_gia(tmp_path)
    tep = DB.danh_sach_dau_vao_anh(g, DB.doc_mo_hinh(g))
    assert DB.bam_dau_vao(g, tep) == DB.bam_dau_vao(g, list(reversed(tep))) == DB.dau_van_anh(g)["sha256"]
    p = g / "backend" / "requirements.txt"
    p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n"))  # LF thuần (kho trên POSIX, hoặc autocrlf=input)
    lf = DB.dau_van_anh(g)["sha256"]
    p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))  # CRLF thuần (checkout Windows, autocrlf=true)
    assert DB.dau_van_anh(g)["sha256"] == lf  # cùng chính sách với candidate: CRLF ≡ LF


def test_P_bi_mat_KHONG_xuat_hien_trong_output_hay_ngoai_le(DB, tmp_path, capsys):
    g = _kho_gia(tmp_path)
    docker = DockerGia(g, image_present=False, build_rc=1, secret_out=f"{KHOA_GIA} {MAT_KHAU_GIA} Authorization: Bearer abcdefghijklmnopqrstuvwx")
    dk, ra = _dieu_khien(DB, g, docker)
    ma = dk.up()
    noi = "\n".join(ra) + capsys.readouterr().out
    assert ma != 0 and KHOA_GIA not in noi and "MATKHAUGIA42" not in noi and "abcdefghijklmnopqrstuvwx" not in noi
    assert DB.che(f"x {KHOA_GIA} {MAT_KHAU_GIA}").count("[REDACTED") >= 2
    dump = json.dumps(DB.dau_van_anh(g), ensure_ascii=False)
    assert KHOA_GIA not in dump


def test_Q_duong_dan_Windows_co_khoang_trang(DB, tmp_path):
    g = _kho_gia(tmp_path)
    assert " " in str(g)
    docker = DockerGia(g, image_present=False)
    dk, _ = _dieu_khien(DB, g, docker)
    assert dk.up() == 0
    (build,) = _lenh(docker, "compose", "build")
    assert str(g / "docker-compose.yml") in build and str(g) in build  # một phần tử argv, không bị tách


# ══ R–T · phạm vi lệnh ═════════════════════════════════════════════════════════
def test_R_launcher_CHI_tac_dong_service_backend(DB, tmp_path):
    g = _kho_gia(tmp_path)
    docker = DockerGia(g, image_present=False, container=False)
    dk, _ = _dieu_khien(DB, g, docker)
    assert dk.up() == 0
    (build,) = _lenh(docker, "compose", "build")
    (up,) = _lenh(docker, "compose", "up")
    assert build[-1] == "backend" and up[-1] == "backend" and "--no-deps" in up and "--no-build" in up
    for a, _ in docker.calls:
        if "compose" in a and ("build" in a or "up" in a):
            assert "db" not in a[a.index("build" if "build" in a else "up"):] and "frontend" not in a
            assert str(g / "docker-compose.dev.yml") in a
    (_, env), = [(a, e) for a, e in docker.calls if "build" in a]
    assert env.get("IMAGE_INPUTS_SHA256") == DB.dau_van_anh(g)["sha256"] and env.get("GIT_SHA")
    assert "ALLOW_LIVE_AI" not in env


def test_S_KHONG_co_down_prune_hay_xoa_volume(DB, tmp_path):
    g = _kho_gia(tmp_path)
    for docker in (DockerGia(g, image_present=False), DockerGia(g, db_revision="r1"), DockerGia(g, image_present=False, build_rc=1)):
        dk, _ = _dieu_khien(DB, g, docker)
        dk.up()
        dk.kiem_tra()
        for a, _ in docker.calls:
            assert not {"down", "prune", "rm", "-v", "--volumes", "--force-recreate"} & set(a), a
            assert not ("volume" in a and "rm" in a)


def test_T_build_hong__MOT_lan_build__KHONG_start__KHONG_retry(DB, tmp_path):
    g = _kho_gia(tmp_path)
    docker = DockerGia(g, image_present=False, build_rc=1)
    dk, _ = _dieu_khien(DB, g, docker)
    assert dk.up() != 0
    assert len(_lenh(docker, "compose", "build")) == 1 and _lenh(docker, "compose", "up") == []
    docker2 = DockerGia(g, image_present=False, up_rc=1)
    dk2, _ = _dieu_khien(DB, g, docker2)
    assert dk2.up() != 0 and len(_lenh(docker2, "compose", "up")) == 1


# ══ danh tính runtime ══════════════════════════════════════════════════════════
def test_danh_tinh_IMAGE_va_HOST_tach_bach(DB, tmp_path):
    g = _kho_gia(tmp_path)
    docker = DockerGia(g, image_labels={DB.NHAN_INPUTS: "cu" * 32, DB.NHAN_GIT: "d5a3cfbcb49341e713e808b7f0b95b3cf0864425"})
    kq = _dieu_khien(DB, g, docker)[0].kiem_tra()
    assert kq["IMAGE_GIT_SHA"] == "d5a3cfbcb49341e713e808b7f0b95b3cf0864425"
    assert kq["HOST_SOURCE_HEAD"] == "6989e9e7e3033144a0a00ae5bcbb3355fe4967a8"
    assert kq["IMAGE_INPUTS_SHA256"] == "cu" * 32 and kq["HOST_IMAGE_INPUTS_SHA256"] == DB.dau_van_anh(g)["sha256"]
    assert kq["CODE_MODE"] == "bind_mount" and kq["decision"] == DB.REBUILD_IMAGE
    assert hashlib.sha256(b"").hexdigest() != kq["HOST_IMAGE_INPUTS_SHA256"]


def test_container_chua_o_che_do_dev__RECREATE_CONTAINER__khong_build(DB, tmp_path):
    g = _kho_gia(tmp_path)
    docker = DockerGia(g, image_labels=_nhan_khop(DB, g), container_hash="HASHCOSO", container_dev="DEV_RELOAD=0")
    dk, _ = _dieu_khien(DB, g, docker)
    assert dk.kiem_tra()["decision"] == DB.RECREATE_CONTAINER
    assert dk.up() == 0 and _lenh(docker, "compose", "build") == [] and len(_lenh(docker, "compose", "up")) == 1
