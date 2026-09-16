# -*- coding: utf-8 -*-
"""VÒNG PHÁT TRIỂN BACKEND DOCKER — sửa Python thì nạp lại tại chỗ, build lại CHỈ khi đầu vào image đổi,
và DỪNG trước mọi build/start khi DB lệch chuỗi migration. Chỉ thư viện chuẩn, không cần Docker để test.

    backend/.venv/Scripts/python.exe backend/scripts/dev_backend.py up          # LỆNH CHUẨN cho máy lập trình
    backend/.venv/Scripts/python.exe backend/scripts/dev_backend.py check       # chỉ đọc, in ĐÚNG MỘT quyết định
    backend/.venv/Scripts/python.exe backend/scripts/dev_backend.py status      # danh tính image so với nguồn host
    backend/.venv/Scripts/python.exe backend/scripts/dev_backend.py classify …  # lớp thay đổi, 0 Docker
    backend/.venv/Scripts/python.exe backend/scripts/dev_backend.py fingerprint # dấu vân tay đầu vào, 0 Docker

VÌ SAO (`DOCKER_BACKEND_DEV_AUTO_REFRESH_HARDENING`, 2026-09-15). `backend/app` được bind mount nên mã
trên đĩa luôn mới, còn dependency nằm TRONG image. Image dựng 2026-08-29 thiếu `pillow` — thêm vào
`requirements.txt` sau đó mà không ai build lại — và uvicorn chết với `ModuleNotFoundError`. Không lệnh nào
cho biết lúc nào PHẢI build lại. Lấy Git HEAD làm điều kiện thì sai theo CẢ HAI chiều: commit tài liệu đòi
build thừa, còn sửa `requirements.txt` chưa commit thì không đòi gì.

Năm lớp thay đổi, suy từ CHÍNH `Dockerfile`, `.dockerignore` và khối `backend` của compose — không từ một
danh sách viết tay (danh sách viết tay là thứ đã trôi khỏi thực tế và gây ra chính sự cố trên):

    SOURCE_HOT_RELOAD            `.py` dưới bind mount che đích COPY (`backend/app`) — uvicorn `--reload` lo
    IMAGE_REBUILD_REQUIRED       file được COPY vào image mà mount KHÔNG che, `Dockerfile`, `.dockerignore`
    CONTAINER_RECREATE_REQUIRED  file compose, env_file, file không-Python dưới mount (tiến trình phải chạy lại)
    MIGRATION_APPROVAL_REQUIRED  file trong thư mục revision của Alembic
    NO_ACTION                    còn lại: tài liệu, artifact, frontend, test — không thứ nào vào image

Cổng migration đứng TRƯỚC build/start/recreate. `CMD` của image chạy `alembic upgrade head` lúc khởi động,
nên chỉ cần start một container trên image có revision mới là schema bị đổi ÂM THẦM. Launcher không bao giờ
đi đường đó: DB khác head nguồn · revision lạ · nhiều head · không đọc được revision ⇒ dừng, không build,
không start. Duyệt migration là việc của NGƯỜI (sao lưu trước — xem
`docs/DOCKER_BACKEND_DEV_AUTO_REFRESH_HARDENING.md`).

Launcher KHÔNG BAO GIỜ: `down` · `-v` · `prune` · xoá volume · `--force-recreate` · đụng service `db` ·
build lần hai sau khi build hỏng · in biến môi trường · chuyển `ALLOW_LIVE_AI` xuống lệnh con.
"""
from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_THU_MUC_SCRIPTS = str(Path(__file__).resolve().parent)
if _THU_MUC_SCRIPTS not in sys.path:
    sys.path.insert(0, _THU_MUC_SCRIPTS)
from freeze_evaluation_candidate import bam_noi_dung  # noqa: E402 — MỘT chính sách CRLF cho mọi dấu vân tay

GOC = Path(__file__).resolve().parents[2]
DICH_VU = "backend"
DICH_VU_DB = "db"
COMPOSE_CO_SO = "docker-compose.yml"
COMPOSE_DEV = "docker-compose.dev.yml"

# ── lớp thay đổi, theo thứ tự ƯU TIÊN (một tập đường dẫn lấy lớp NẶNG nhất) ──
MIGRATION_APPROVAL_REQUIRED = "MIGRATION_APPROVAL_REQUIRED"
IMAGE_REBUILD_REQUIRED = "IMAGE_REBUILD_REQUIRED"
CONTAINER_RECREATE_REQUIRED = "CONTAINER_RECREATE_REQUIRED"
SOURCE_HOT_RELOAD = "SOURCE_HOT_RELOAD"
NO_ACTION = "NO_ACTION"
UU_TIEN_LOP = (MIGRATION_APPROVAL_REQUIRED, IMAGE_REBUILD_REQUIRED, CONTAINER_RECREATE_REQUIRED,
               SOURCE_HOT_RELOAD, NO_ACTION)

# ── quyết định của `check` — đúng MỘT ──
REUSE_IMAGE = "REUSE_IMAGE"
REBUILD_IMAGE = "REBUILD_IMAGE"
RECREATE_CONTAINER = "RECREATE_CONTAINER"
IMAGE_MISSING = "IMAGE_MISSING"
CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
QUYET_DINH_HOP_LE = (REUSE_IMAGE, REBUILD_IMAGE, RECREATE_CONTAINER, MIGRATION_APPROVAL_REQUIRED,
                     IMAGE_MISSING, CONFIGURATION_ERROR)
MA_THOAT = {REUSE_IMAGE: 0, CONFIGURATION_ERROR: 2, REBUILD_IMAGE: 10, RECREATE_CONTAINER: 11,
            IMAGE_MISSING: 12, MIGRATION_APPROVAL_REQUIRED: 20}
MA_BUILD_HONG, MA_NHAN_SAI, MA_UP_HONG, MA_KHONG_HEALTHY, MA_SAU_UP_LECH = 30, 31, 40, 50, 60

# ── nhãn danh tính image: Dockerfile ghi, launcher đọc ──
NHAN_GIT = "org.algosim.backend.git-sha"
NHAN_BUILD_TIME = "org.algosim.backend.build-time"
NHAN_REQ = "org.algosim.backend.requirements-sha256"
NHAN_INPUTS = "org.algosim.backend.image-inputs-sha256"
NHAN_CONFIG_HASH = "com.docker.compose.config-hash"

HAN_CHO_HEALTHY_GIAY = 240
NHIP_CHO_GIAY = 2
GIOI_HAN_LENH_GIAY = 1800
BIEN_KHONG_CHUYEN = ("ALLOW_LIVE_AI",)

SQL_REVISION = 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "select version_num from alembic_version"'
FMT_ID_ANH = "{{.Id}}"
FMT_NHAN_ANH = "{{json .Config.Labels}}"
FMT_CONTAINER = ('{{.Image}}|{{index .Config.Labels "com.docker.compose.config-hash"}}|{{.State.Status}}'
                 '|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}'
                 '|{{range .Config.Env}}{{if eq (index (split . "=") 0) "DEV_RELOAD"}}{{.}}{{end}}{{end}}')
FMT_SUC_KHOE = '{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}'

CHINH_SACH_DAU_VAN = {
    "nguon": "đúng những file lệnh COPY/ADD trong Dockerfile chép từ build context vào image",
    "loai_tru": ["nguồn bị bind mount của compose che (mã đến từ đĩa host lúc chạy, không từ image)",
                 "mẫu trong .dockerignore", "__pycache__/ và *.pyc (dẫn xuất từ .py đã băm)"],
    "chuan_hoa": "đường dẫn tương đối gốc repository, dấu '/', sắp xếp; băm nội dung sau CRLF sang LF "
                 "(freeze_evaluation_candidate.bam_noi_dung) — không mtime, không quyền, không thứ tự hệ file",
    "khong_bao_gio_bam": ["biến môi trường", ".env", "database dump", "artifact", "Git HEAD"],
}


# ══ CHE BÍ MẬT ════════════════════════════════════════════════════════════════
_MAU_CHE = (
    (re.compile(r"AIza[0-9A-Za-z_\-]{20,}"), "[REDACTED_GOOGLE_API_KEY]"),
    (re.compile(r"(?i)\b([a-z][a-z0-9+.\-]*://)[^\s:/@]+:[^\s@/]+@"), r"\1[REDACTED_CREDENTIALS]@"),
    (re.compile(r"(?i)\b(authorization\s*[:=]\s*)(?:bearer|basic|token)?\s*[^\s,;]+"),
     r"\1[REDACTED_AUTHORIZATION]"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=\-]{8,}"), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"(?i)\b(set-cookie|cookie)\s*:\s*[^\r\n]+"), r"\1: [REDACTED_COOKIE]"),
    (re.compile(r"(?i)\b([A-Za-z0-9_]*(?:API_KEY|APIKEY|TOKEN|SECRET|PASSWORD|PASSWD|PRIVATE_KEY)"
                r"[A-Za-z0-9_]*)\s*([=:])\s*[^\s,;]+"), r"\1\2[REDACTED]"),
)


def che(s) -> str:
    """Che bí mật trong MỌI chuỗi trước khi nó rời launcher. Thà che thừa còn hơn lọt một lần."""
    s = "" if s is None else str(s)
    for rx, thay in _MAU_CHE:
        s = rx.sub(thay, s)
    return s


# ══ MÔ HÌNH ẢNH — đọc thẳng Dockerfile + .dockerignore + khối backend của compose ══
@dataclass
class MoHinhAnh:
    goc: Path
    compose_files: list = field(default_factory=list)
    context: str = ""
    dockerfile: str = ""
    dockerignore: str = ""
    copies: list = field(default_factory=list)   # {"source": repo-rel, "dest": /container, "kind": file|dir}
    mounts: list = field(default_factory=list)   # {"host": repo-rel, "target": /container, "read_only": bool}
    env_files: list = field(default_factory=list)
    build_args: list = field(default_factory=list)
    migrations_dir: str = ""
    mau_bo_qua: list = field(default_factory=list)
    loi: list = field(default_factory=list)


def _rel(goc, p) -> str:
    return Path(p).resolve().relative_to(Path(goc).resolve()).as_posix()


def _chuan_duong(p) -> str:
    s = str(p).replace("\\", "/").strip()
    while s.startswith("./"):
        s = s[2:]
    return posixpath.normpath(s) if s else s


def _duoi(p: str, thu_muc: str) -> bool:
    if not thu_muc:
        return False
    thu_muc = thu_muc.rstrip("/")
    return p == thu_muc or p.startswith(thu_muc + "/")


def _gia_tri(v: str) -> str:
    v = re.split(r"\s+#", v, 1)[0].strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v


def _dong_yaml(text: str) -> list:
    ra = []
    for dong in text.splitlines():
        s = dong.rstrip()
        if not s.strip() or s.lstrip().startswith("#"):
            continue
        ra.append((len(s) - len(s.lstrip(" ")), s.strip()))
    return ra


def _con(dong: list, i: int) -> list:
    t = dong[i][0]
    j = i + 1
    while j < len(dong) and dong[j][0] > t:
        j += 1
    return dong[i + 1:j]


def _khoa(dong: list, ten: str):
    """(giá trị cùng dòng, các dòng con) của khoá `ten` ở mức thụt NÔNG nhất — YAML tối giản, đủ cho compose."""
    if not dong:
        return None
    muc = min(t for t, _ in dong)
    for i, (t, s) in enumerate(dong):
        if t == muc and (s == ten + ":" or s.startswith(ten + ": ")):
            return _gia_tri(s[len(ten) + 1:]), _con(dong, i)
    return None


def _muc_con(con: list) -> list:
    """Các phần tử danh sách ở mức thụt nông nhất của một khối con."""
    if not con:
        return []
    muc = min(t for t, _ in con)
    return [s for t, s in con if t == muc and s.startswith("- ")]


def _doc_compose(mh: MoHinhAnh, van_ban: str) -> None:
    dong = _dong_yaml(van_ban)
    sv = _khoa(dong, "services")
    if sv is None:
        mh.loi.append("COMPOSE_SERVICES_MISSING")
        return
    be = _khoa(sv[1], DICH_VU)
    if be is None:
        mh.loi.append("COMPOSE_BACKEND_SERVICE_MISSING")
        return
    khoi = be[1]
    ten_dockerfile = "Dockerfile"
    build = _khoa(khoi, "build")
    if build is None:
        mh.loi.append("COMPOSE_BACKEND_BUILD_MISSING")
    elif build[0]:
        mh.context = _chuan_duong(build[0])
    else:
        ctx = _khoa(build[1], "context")
        mh.context = _chuan_duong(ctx[0]) if ctx and ctx[0] else ""
        df = _khoa(build[1], "dockerfile")
        ten_dockerfile = df[0] if df and df[0] else "Dockerfile"
        args = _khoa(build[1], "args")
        if args and args[1]:
            muc = min(t for t, _ in args[1])
            mh.build_args = [s.split(":", 1)[0].lstrip("- ").split("=", 1)[0].strip()
                             for t, s in args[1] if t == muc]
    if not mh.context:
        mh.loi.append("COMPOSE_BUILD_CONTEXT_MISSING")
        return
    mh.dockerfile = posixpath.join(mh.context, ten_dockerfile)
    mh.dockerignore = posixpath.join(mh.context, ".dockerignore")
    vol = _khoa(khoi, "volumes")
    if vol:
        for s in _muc_con(vol[1]):
            phan = _gia_tri(s[2:]).split(":")
            if len(phan) < 2 or not (phan[0].startswith(".") or "/" in phan[0]):
                continue  # volume CÓ TÊN (vd pgdata) — không phải bind mount từ cây nguồn
            mh.mounts.append({"host": _chuan_duong(phan[0]), "target": posixpath.normpath(phan[1]),
                              "read_only": len(phan) > 2 and "ro" in phan[2].split(",")})
    ef = _khoa(khoi, "env_file")
    if ef:
        if ef[0]:
            mh.env_files.append(_chuan_duong(ef[0]))
        for s in _muc_con(ef[1]):
            than = s[2:].strip()
            if than.startswith("path:"):
                mh.env_files.append(_chuan_duong(_gia_tri(than[5:])))
            elif than and not than.endswith(":"):
                mh.env_files.append(_chuan_duong(_gia_tri(than)))


def _tach_copy(phan_con_lai: str):
    s = phan_con_lai.strip()
    if s.startswith("["):
        try:
            tu = json.loads(s)
        except ValueError:
            return None
    else:
        tu = s.split()
    co = [t for t in tu if not str(t).startswith("--")]
    if any(str(t).lower().startswith("--from") for t in tu) or len(co) < 2:
        return None  # COPY --from=<stage>: không đọc build context, không phải đầu vào từ cây nguồn
    return co


def _mo_rong_nguon(mh: MoHinhAnh, n: str) -> list:
    n = str(n).replace("\\", "/").lstrip("/")
    if any(k in n for k in "*?["):
        return sorted(_rel(mh.goc, q) for q in (mh.goc / mh.context).glob(n))
    rel = _chuan_duong(posixpath.join(mh.context, n))
    if not (mh.goc / rel).exists():
        mh.loi.append("COPY_SOURCE_MISSING:" + rel)
        return []
    return [rel]


def _doc_dockerfile(mh: MoHinhAnh, van_ban: str) -> None:
    lenh, dem = [], ""
    for dong in van_ban.splitlines():
        s = dong.strip()
        if not dem and (not s or s.startswith("#")):
            continue
        if s.endswith("\\"):
            dem += s[:-1] + " "
            continue
        lenh.append(dem + s)
        dem = ""
    if dem:
        lenh.append(dem)
    workdir = "/"
    for c in lenh:
        tu, _, con_lai = c.partition(" ")
        tu = tu.upper()
        if tu == "WORKDIR":
            d = con_lai.strip()
            workdir = posixpath.normpath(d if d.startswith("/") else posixpath.join(workdir, d))
        elif tu in ("COPY", "ADD"):
            phan = _tach_copy(con_lai)
            if not phan:
                continue
            nguon, dich = phan[:-1], phan[-1]
            dich_abs = dich if dich.startswith("/") else posixpath.join(workdir, dich)
            dich_la_thu_muc = dich.endswith("/") or dich in (".", "./") or len(nguon) > 1
            for n in nguon:
                for src in _mo_rong_nguon(mh, n):
                    if (mh.goc / src).is_dir():
                        mh.copies.append({"source": src, "dest": posixpath.normpath(dich_abs), "kind": "dir"})
                    else:
                        d = posixpath.join(dich_abs, posixpath.basename(src)) if dich_la_thu_muc else dich_abs
                        mh.copies.append({"source": src, "dest": posixpath.normpath(d), "kind": "file"})


def _mau_regex(mau: str):
    """.dockerignore: mẫu neo ở GỐC build context, `**` đi qua nhiều mức, khớp cả thứ nằm dưới."""
    mau = posixpath.normpath(mau.strip().lstrip("/"))
    ra, i = "", 0
    while i < len(mau):
        c = mau[i]
        if c == "*":
            if mau[i:i + 3] == "**/":
                ra += "(?:.*/)?"
                i += 3
                continue
            if mau[i:i + 2] == "**":
                ra += ".*"
                i += 2
                continue
            ra += "[^/]*"
        elif c == "?":
            ra += "[^/]"
        else:
            ra += re.escape(c)
        i += 1
    return re.compile("^" + ra + "(?:/.*)?$")


def _doc_dockerignore(mh: MoHinhAnh, van_ban: str) -> None:
    for dong in van_ban.splitlines():
        s = dong.strip()
        if not s or s.startswith("#"):
            continue
        phu_dinh = s.startswith("!")
        mh.mau_bo_qua.append((phu_dinh, _mau_regex(s[1:] if phu_dinh else s)))


def _doc_migrations_dir(mh: MoHinhAnh) -> None:
    ini = mh.goc / mh.context / "alembic.ini"
    loc = "alembic"
    if ini.is_file():
        m = re.search(r"(?m)^\s*script_location\s*=\s*(.+?)\s*$",
                      ini.read_text(encoding="utf-8", errors="replace"))
        if m:
            loc = m.group(1).replace("%(here)s", "").strip().lstrip("/") or "alembic"
    mh.migrations_dir = posixpath.join(mh.context, loc, "versions")


def doc_mo_hinh(goc=GOC) -> MoHinhAnh:
    """Mô hình ĐẦU VÀO ẢNH, đọc từ chính cấu hình build — không từ danh sách viết tay."""
    goc = Path(goc)
    mh = MoHinhAnh(goc=goc, compose_files=[str(goc / COMPOSE_CO_SO), str(goc / COMPOSE_DEV)])
    for f in mh.compose_files:
        if not Path(f).is_file():
            mh.loi.append("COMPOSE_FILE_MISSING:" + Path(f).name)
    co_so = goc / COMPOSE_CO_SO
    if co_so.is_file():
        _doc_compose(mh, co_so.read_text(encoding="utf-8"))
    dev = goc / COMPOSE_DEV
    if dev.is_file() and not re.search(r"(?m)^\s+DEV_RELOAD:\s*[\"']?1[\"']?\s*$",
                                       dev.read_text(encoding="utf-8")):
        mh.loi.append("DEV_OVERRIDE_WITHOUT_RELOAD")
    if not mh.context:
        return mh
    df = goc / mh.dockerfile
    if df.is_file():
        van = df.read_text(encoding="utf-8")
        _doc_dockerfile(mh, van)
        if NHAN_INPUTS not in van:
            mh.loi.append("DOCKERFILE_INPUTS_LABEL_MISSING")
    else:
        mh.loi.append("DOCKERFILE_MISSING:" + mh.dockerfile)
    di = goc / mh.dockerignore
    if di.is_file():
        _doc_dockerignore(mh, di.read_text(encoding="utf-8"))
    if "IMAGE_INPUTS_SHA256" not in mh.build_args:
        mh.loi.append("COMPOSE_BUILD_ARG_MISSING:IMAGE_INPUTS_SHA256")
    _doc_migrations_dir(mh)
    return mh


# ══ DẤU VÂN TAY ĐẦU VÀO ẢNH ═══════════════════════════════════════════════════
def _la_bytecode(rel: str) -> bool:
    return "__pycache__" in rel.split("/") or rel.endswith((".pyc", ".pyo"))


def _bi_bo_qua(mh: MoHinhAnh, rel: str) -> bool:
    if mh.context and not _duoi(rel, mh.context):
        return True
    trong = rel[len(mh.context) + 1:] if mh.context else rel
    ket = False
    for phu_dinh, rx in mh.mau_bo_qua:
        if rx.match(trong):
            ket = not phu_dinh
    return ket


def _dich_cua(c: dict, rel: str) -> str:
    if c["kind"] == "file":
        return c["dest"]
    return posixpath.normpath(posixpath.join(c["dest"], rel[len(c["source"]) + 1:]))


def _mount_che(mh: MoHinhAnh, dich: str):
    for m in mh.mounts:
        if _duoi(dich, m["target"]):
            return m
    return None


def _mount_host(mh: MoHinhAnh, rel: str):
    for m in mh.mounts:
        if _duoi(rel, m["host"]):
            return m
    return None


def danh_sach_dau_vao_anh(goc=GOC, mh: MoHinhAnh = None) -> list:
    """Đúng những file build chép vào image mà bind mount KHÔNG che."""
    goc = Path(goc)
    mh = mh or doc_mo_hinh(goc)
    tep = set()
    for ten in (mh.dockerfile, mh.dockerignore):
        if ten and (goc / ten).is_file():
            tep.add(ten)
    for c in mh.copies:
        p = goc / c["source"]
        ung_vien = [c["source"]] if c["kind"] == "file" else sorted(
            _rel(goc, q) for q in p.rglob("*") if q.is_file())
        for rel in ung_vien:
            if _la_bytecode(rel) or _bi_bo_qua(mh, rel):
                continue
            if _mount_che(mh, _dich_cua(c, rel)) is not None:
                continue  # bị bind mount che — mã ấy đến từ đĩa host lúc chạy, KHÔNG từ image
            tep.add(rel)
    return sorted(tep)


def bam_dau_vao(goc, tep) -> str:
    """Băm (đường dẫn + nội dung) từng file theo thứ tự CHUẨN — không phụ thuộc thứ tự liệt kê."""
    goc = Path(goc)
    tep = list(tep)
    if len(set(tep)) != len(tep):
        raise ValueError("danh sách đầu vào ảnh có đường dẫn trùng")
    h = hashlib.sha256()
    for rel in sorted(tep):
        noi = hashlib.sha256(bam_noi_dung(goc / rel)).hexdigest()
        h.update(rel.encode("utf-8") + b"\0" + noi.encode("ascii") + b"\n")
    return h.hexdigest()


def dau_van_anh(goc=GOC, mh: MoHinhAnh = None) -> dict:
    goc = Path(goc)
    mh = mh or doc_mo_hinh(goc)
    tep = danh_sach_dau_vao_anh(goc, mh)
    req = next((c["source"] for c in mh.copies
                if c["kind"] == "file" and posixpath.basename(c["source"]) == "requirements.txt"), None)
    return {
        "schema": "backend-image-inputs/1",
        "sha256": bam_dau_vao(goc, tep),
        "file_count": len(tep),
        "files": tep,
        "file_sha256": {rel: hashlib.sha256(bam_noi_dung(goc / rel)).hexdigest() for rel in tep},
        "requirements_file": req,
        "requirements_sha256": (hashlib.sha256(bam_noi_dung(goc / req)).hexdigest()
                                if req and (goc / req).is_file() else None),
        "shadowed_copy_sources": sorted({c["source"] for c in mh.copies if _mount_che(mh, c["dest"])}),
        "policy": CHINH_SACH_DAU_VAN,
    }


# ══ PHÂN LOẠI THAY ĐỔI ════════════════════════════════════════════════════════
def _phan_loai_mot(duong, mh: MoHinhAnh) -> dict:
    rel = _chuan_duong(duong)
    ten_compose = [Path(f).name for f in mh.compose_files]
    if _duoi(rel, mh.migrations_dir) and rel.endswith(".py") and not _la_bytecode(rel):
        return {"path": rel, "class": MIGRATION_APPROVAL_REQUIRED, "reason": "ALEMBIC_REVISION_FILE"}
    if rel in ten_compose:
        return {"path": rel, "class": CONTAINER_RECREATE_REQUIRED, "reason": "COMPOSE_RUNTIME_CONFIG"}
    if rel in mh.env_files:
        return {"path": rel, "class": CONTAINER_RECREATE_REQUIRED, "reason": "ENV_FILE_STARTUP_ENVIRONMENT"}
    if rel in (mh.dockerfile, mh.dockerignore):
        return {"path": rel, "class": IMAGE_REBUILD_REQUIRED, "reason": "BUILD_DEFINITION"}
    if _la_bytecode(rel):
        return {"path": rel, "class": NO_ACTION, "reason": "DERIVED_BYTECODE"}
    for c in mh.copies:
        thuoc = rel == c["source"] if c["kind"] == "file" else _duoi(rel, c["source"])
        if not thuoc or _bi_bo_qua(mh, rel):
            continue
        if _mount_che(mh, _dich_cua(c, rel)) is None:
            return {"path": rel, "class": IMAGE_REBUILD_REQUIRED, "reason": "COPIED_INTO_IMAGE"}
        if rel.endswith(".py"):
            return {"path": rel, "class": SOURCE_HOT_RELOAD, "reason": "BIND_MOUNT_PYTHON_WATCHED_BY_RELOAD"}
        return {"path": rel, "class": CONTAINER_RECREATE_REQUIRED,
                "reason": "BIND_MOUNT_NON_PYTHON_PROCESS_RESTART"}  # uvicorn --reload chỉ theo dõi *.py
    if _mount_host(mh, rel) is not None:
        return {"path": rel, "class": NO_ACTION, "reason": "LIVE_TOOL_MOUNT_NOT_AN_IMAGE_INPUT"}
    return {"path": rel, "class": NO_ACTION, "reason": "NOT_AN_IMAGE_OR_RUNTIME_INPUT"}


def phan_loai_thay_doi(duong_dan, mh: MoHinhAnh = None) -> dict:
    mh = mh or doc_mo_hinh()
    hang = [_phan_loai_mot(p, mh) for p in duong_dan]
    lop = next((c for c in UU_TIEN_LOP if any(h["class"] == c for h in hang)), NO_ACTION)
    return {"class": lop, "paths": hang}


# ══ CHUỖI MIGRATION ═══════════════════════════════════════════════════════════
_RE_REV = re.compile(r"(?m)^revision\s*(?::[^=\n]*)?=\s*[\"']([^\"']+)[\"']")
_RE_DOWN = re.compile(r"(?m)^down_revision\s*(?::[^=\n]*)?=\s*(.+?)\s*$")


def doc_chuoi_migration(thu_muc) -> dict:
    thu_muc = Path(thu_muc)
    if not thu_muc.is_dir():
        return {"revisions": [], "heads": [], "errors": ["MIGRATIONS_DIR_MISSING"]}
    revs, loi = {}, []
    for p in sorted(thu_muc.glob("*.py")):
        t = p.read_text(encoding="utf-8", errors="replace")
        r, d = _RE_REV.search(t), _RE_DOWN.search(t)
        if not r or not d:
            loi.append("REVISION_UNREADABLE:" + p.name)
            continue
        if r.group(1) in revs:
            loi.append("REVISION_DUPLICATE:" + r.group(1))
        revs[r.group(1)] = re.findall(r"[\"']([^\"']+)[\"']", d.group(1))
    tro_toi = {x for ds in revs.values() for x in ds}
    for x in sorted(tro_toi - set(revs)):
        loi.append("DOWN_REVISION_UNKNOWN:" + x)
    return {"revisions": sorted(revs), "heads": sorted(set(revs) - tro_toi), "errors": loi}


def cong_migration(chuoi: dict, db_revisions) -> list:
    """Lý do PHẢI dừng trước build/start. Rỗng = DB đang ở đúng head của cây nguồn."""
    if chuoi["errors"]:
        return ["MIGRATION_CHAIN_UNREADABLE"] + list(chuoi["errors"])
    if len(chuoi["heads"]) != 1:
        return ["MIGRATION_HEADS_NOT_SINGLE"]
    db_revisions = list(db_revisions)
    if not db_revisions:
        return ["DB_REVISION_UNKNOWN"]
    if len(db_revisions) != 1:
        return ["DB_REVISION_NOT_SINGLE"]
    if db_revisions[0] not in chuoi["revisions"]:
        return ["DB_REVISION_NOT_IN_SOURCE_CHAIN"]
    if db_revisions[0] != chuoi["heads"][0]:
        return ["MIGRATION_PENDING"]
    return []


# ══ QUYẾT ĐỊNH — đúng MỘT, thứ tự cổng là HỢP ĐỒNG ════════════════════════════
def quyet_dinh(tt: dict):
    if tt["config_errors"]:
        return CONFIGURATION_ERROR, list(dict.fromkeys(tt["config_errors"]))
    ly_do_mig = cong_migration(tt["migration_chain"], tt["db_revisions"])
    if ly_do_mig:
        return MIGRATION_APPROVAL_REQUIRED, ly_do_mig
    if not tt["image_present"]:
        return IMAGE_MISSING, ["IMAGE_NOT_FOUND"]
    nhan = (tt["image_labels"] or {}).get(NHAN_INPUTS)
    if not nhan or nhan == "unknown":
        return REBUILD_IMAGE, ["IMAGE_INPUTS_LABEL_MISSING"]
    if nhan != tt["host_inputs_sha256"]:
        return REBUILD_IMAGE, ["IMAGE_INPUTS_CHANGED"]
    ct = tt["container"]
    if not ct:
        return RECREATE_CONTAINER, ["CONTAINER_MISSING"]
    ly_do = []
    if ct.get("status") != "running":
        ly_do.append("CONTAINER_NOT_RUNNING")
    if tt.get("image_id") and ct.get("image") and ct["image"] != tt["image_id"]:
        ly_do.append("CONTAINER_IMAGE_OUTDATED")
    if tt.get("config_hash") and ct.get("config_hash") != tt["config_hash"]:
        ly_do.append("CONTAINER_CONFIG_CHANGED")
    if ct.get("dev_reload") != "1":
        ly_do.append("CONTAINER_NOT_IN_DEV_RELOAD_MODE")
    if ly_do:
        return RECREATE_CONTAINER, ly_do
    return REUSE_IMAGE, ["IMAGE_INPUTS_MATCH", "CONTAINER_MATCHES_DEV_CONFIG"]


# ══ TRANSPORT ═════════════════════════════════════════════════════════════════
def chay_that(argv, env=None):
    """Transport THẬT: argv dạng danh sách, KHÔNG shell — đường dẫn có khoảng trắng đi qua nguyên vẹn."""
    try:
        p = subprocess.run(list(argv), capture_output=True, env=env, timeout=GIOI_HAN_LENH_GIAY)
    except FileNotFoundError:
        return 127, "", "không tìm thấy lệnh: " + str(argv[0])
    except subprocess.TimeoutExpired:
        return 124, "", "hết thời gian: " + str(argv[0])
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def _dong_dau(s):
    for d in (s or "").splitlines():
        if d.strip():
            return d.strip()
    return None


def _doc_porcelain(out: str) -> list:
    muc = out.split("\0") if "\0" in (out or "") else (out or "").splitlines()
    duong, i = [], 0
    while i < len(muc):
        m = muc[i]
        i += 1
        if len(m) < 4:
            continue
        ma, p = m[:2], m[3:]
        if "\0" in (out or "") and ma[0] in "RC":
            duong.append(p)
            if i < len(muc):
                duong.append(muc[i])
                i += 1
            continue
        if " -> " in p:
            duong.extend(p.split(" -> ", 1))
            continue
        duong.append(p)
    return [d.strip().strip('"') for d in duong if d.strip()]


# ══ ĐIỀU KHIỂN ════════════════════════════════════════════════════════════════
class DieuKhien:
    """Gọi Docker qua transport TIÊM ĐƯỢC — nên mọi quyết định test được offline, 0 Docker, 0 mạng."""

    def __init__(self, goc=GOC, *, chay=None, ngu=time.sleep, dong_ho=time.monotonic, in_ra=print):
        self.goc = Path(goc)
        self.chay = chay or chay_that
        self.ngu, self.dong_ho, self.in_ra = ngu, dong_ho, in_ra
        self.tep_compose = [str(self.goc / COMPOSE_CO_SO), str(self.goc / COMPOSE_DEV)]

    def _in(self, dong=""):
        self.in_ra(che(dong))

    def _in_duoi(self, van, so_dong=20):
        for d in (van or "").splitlines()[-so_dong:]:
            if d.strip():
                self._in("  | " + d.rstrip())

    def _moi_truong(self, them=None):
        e = {k: v for k, v in os.environ.items() if k not in BIEN_KHONG_CHUYEN}
        e.update(them or {})
        return e

    def _compose(self, *doi):
        argv = ["docker", "compose", "--project-directory", str(self.goc)]
        for f in self.tep_compose:
            argv += ["-f", f]
        return argv + list(doi)

    def _goi(self, argv, them=None):
        return self.chay(list(argv), env=self._moi_truong(them))

    def _doc_container(self, dich_vu):
        rc, out, _e = self._goi(self._compose("ps", "-a", "-q", dich_vu))
        cid = _dong_dau(out) if rc == 0 else None
        if not cid:
            return None
        if dich_vu != DICH_VU:
            rc, out, _e = self._goi(["docker", "inspect", "--format", FMT_SUC_KHOE, cid])
            tt, _, sk = (out or "").strip().partition("|")
            return {"id": cid, "status": tt, "health": sk}
        rc, out, _e = self._goi(["docker", "inspect", "--format", FMT_CONTAINER, cid])
        phan = (out or "").strip().split("|")
        if rc != 0 or len(phan) < 5:
            return {"id": cid, "image": "", "config_hash": "", "status": "unknown", "health": "",
                    "dev_reload": None}
        return {"id": cid, "image": phan[0], "config_hash": phan[1], "status": phan[2], "health": phan[3],
                "dev_reload": phan[4].partition("=")[2] or None}

    # ── ĐỌC: không đổi gì, trả về đúng MỘT quyết định ──
    def kiem_tra(self) -> dict:
        mh = doc_mo_hinh(self.goc)
        loi = list(mh.loi)
        try:
            dv = dau_van_anh(self.goc, mh)
        except OSError as e:
            dv = {"sha256": None, "file_count": 0, "files": [], "requirements_sha256": None}
            loi.append("IMAGE_INPUTS_UNREADABLE:" + type(e).__name__)
        rc, out, _e = self._goi(["git", "-C", str(self.goc), "rev-parse", "HEAD"])
        head = _dong_dau(out) if rc == 0 else None
        rc, out, _e = self._goi(["git", "-C", str(self.goc), "status", "--porcelain=v1", "-z",
                                 "--untracked-files=all"])
        pl = phan_loai_thay_doi(_doc_porcelain(out) if rc == 0 else [], mh)
        ban = [h for h in pl["paths"] if h["class"] != NO_ACTION]

        ten_anh, image_id, nhan, co_anh, bam_cau_hinh = None, None, {}, False, None
        rc, out, err = self._goi(self._compose("config", "--images", DICH_VU))
        if rc != 0:
            loi.append("DOCKER_UNAVAILABLE" if rc == 127 else "COMPOSE_CONFIG_INVALID")
            self._in_duoi(err)
        else:
            ten_anh = _dong_dau(out)
        rc, out, _e = self._goi(self._compose("config", "--hash", DICH_VU))
        if rc == 0:
            for d in (out or "").splitlines():
                phan = d.split()
                if len(phan) == 2 and phan[0] == DICH_VU:
                    bam_cau_hinh = phan[1]
        if not bam_cau_hinh:
            loi.append("COMPOSE_CONFIG_HASH_UNAVAILABLE")
        if ten_anh:
            rc, out, err = self._goi(["docker", "image", "inspect", "--format", FMT_ID_ANH, ten_anh])
            if rc == 0:
                co_anh, image_id = True, _dong_dau(out)
            elif "no such image" not in (err or "").lower():
                loi.append("DOCKER_IMAGE_INSPECT_FAILED")
            if co_anh:
                rc, out, _e = self._goi(["docker", "image", "inspect", "--format", FMT_NHAN_ANH, ten_anh])
                try:
                    nhan = json.loads(_dong_dau(out) or "{}") if rc == 0 else {}
                except ValueError:
                    nhan = {}
                nhan = nhan or {}
        ct = self._doc_container(DICH_VU)
        db = self._doc_container(DICH_VU_DB)
        if db is None:
            loi.append("DB_CONTAINER_MISSING")
        elif db.get("status") != "running":
            loi.append("DB_NOT_RUNNING")
        elif db.get("health") not in ("healthy", "none", ""):
            loi.append("DB_NOT_HEALTHY")
        db_revs = []
        if db and db.get("status") == "running":
            rc, out, _e = self._goi(self._compose("exec", "-T", DICH_VU_DB, "sh", "-c", SQL_REVISION))
            if rc == 0:
                db_revs = [d.strip() for d in (out or "").splitlines() if d.strip()]
        chuoi = (doc_chuoi_migration(self.goc / mh.migrations_dir) if mh.migrations_dir
                 else {"revisions": [], "heads": [], "errors": ["MIGRATIONS_DIR_MISSING"]})
        quyet, ly_do = quyet_dinh({
            "config_errors": loi, "migration_chain": chuoi, "db_revisions": db_revs,
            "image_present": co_anh, "image_labels": nhan, "image_id": image_id,
            "host_inputs_sha256": dv["sha256"], "container": ct, "config_hash": bam_cau_hinh,
        })
        return {
            "decision": quyet, "reasons": ly_do,
            "IMAGE_GIT_SHA": nhan.get(NHAN_GIT), "HOST_SOURCE_HEAD": head,
            "IMAGE_INPUTS_SHA256": nhan.get(NHAN_INPUTS), "HOST_IMAGE_INPUTS_SHA256": dv["sha256"],
            "IMAGE_REQUIREMENTS_SHA256": nhan.get(NHAN_REQ),
            "HOST_REQUIREMENTS_SHA256": dv["requirements_sha256"],
            "IMAGE_BUILD_TIME": nhan.get(NHAN_BUILD_TIME), "IMAGE_INPUTS_FILE_COUNT": dv["file_count"],
            "CODE_MODE": "bind_mount" if any(_mount_che(mh, c["dest"]) for c in mh.copies) else "image",
            "BACKEND_SOURCE_DIRTY": bool(ban), "backend_dirty_paths": ban,
            "DB_REVISION": db_revs[0] if len(db_revs) == 1 else (db_revs or None),
            "SOURCE_MIGRATION_HEAD": chuoi["heads"][0] if len(chuoi["heads"]) == 1 else chuoi["heads"],
            "IMAGE_NAME": ten_anh, "IMAGE_ID": image_id, "COMPOSE_CONFIG_HASH": bam_cau_hinh,
            "CONTAINER": ct, "compose_files": [Path(f).name for f in self.tep_compose],
            "config_errors": loi,
        }

    def bao_cao(self, kq, day_du=False):
        c = kq.get("CONTAINER") or {}
        hang = [("DECISION", kq["decision"]),
                ("REASONS", ", ".join(kq["reasons"]) or "-"),
                ("IMAGE_GIT_SHA", kq["IMAGE_GIT_SHA"] or "-"),
                ("HOST_SOURCE_HEAD", kq["HOST_SOURCE_HEAD"] or "-"),
                ("IMAGE_INPUTS_SHA256", kq["IMAGE_INPUTS_SHA256"] or "-"),
                ("HOST_IMAGE_INPUTS_SHA256", kq["HOST_IMAGE_INPUTS_SHA256"] or "-"),
                ("IMAGE_INPUTS_FILE_COUNT", kq["IMAGE_INPUTS_FILE_COUNT"]),
                ("CODE_MODE", kq["CODE_MODE"]),
                ("BACKEND_SOURCE_DIRTY", kq["BACKEND_SOURCE_DIRTY"]),
                ("DB_REVISION", kq["DB_REVISION"] or "-"),
                ("SOURCE_MIGRATION_HEAD", kq["SOURCE_MIGRATION_HEAD"] or "-"),
                ("CONTAINER", (str(c.get("status")) + " · " + str(c.get("health")) + " · DEV_RELOAD="
                               + str(c.get("dev_reload"))) if c else "-")]
        if day_du:
            hang += [("IMAGE_NAME", kq["IMAGE_NAME"] or "-"),
                     ("IMAGE_ID", (kq["IMAGE_ID"] or "-")[:19]),
                     ("IMAGE_BUILD_TIME", kq["IMAGE_BUILD_TIME"] or "-"),
                     ("IMAGE_REQUIREMENTS_SHA256", kq["IMAGE_REQUIREMENTS_SHA256"] or "-"),
                     ("HOST_REQUIREMENTS_SHA256", kq["HOST_REQUIREMENTS_SHA256"] or "-"),
                     ("COMPOSE_FILES", " ".join(kq["compose_files"])),
                     ("COMPOSE_CONFIG_HASH", kq["COMPOSE_CONFIG_HASH"] or "-")]
        rong = max(len(k) for k, _ in hang)
        for k, v in hang:
            self._in(k.ljust(rong) + " = " + str(v))
        if day_du and kq["backend_dirty_paths"]:
            self._in("BACKEND_DIRTY_PATHS:")
            for h in kq["backend_dirty_paths"][:20]:
                self._in("  - " + h["path"] + " → " + h["class"] + " (" + h["reason"] + ")")

    # ── VIẾT: build tối đa MỘT lần, up tối đa MỘT lần, không bao giờ đụng db ──
    def _build_mot_lan(self, kq) -> int:
        them = {"GIT_SHA": kq["HOST_SOURCE_HEAD"] or "unknown",
                "BUILD_TIME": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "REQUIREMENTS_SHA256": kq["HOST_REQUIREMENTS_SHA256"] or "unknown",
                "IMAGE_INPUTS_SHA256": kq["HOST_IMAGE_INPUTS_SHA256"] or "unknown"}
        self._in("BUILD backend (một lần) — IMAGE_INPUTS_SHA256 = " + str(them["IMAGE_INPUTS_SHA256"]))
        rc, _out, err = self._goi(self._compose("build", DICH_VU), them)
        if rc != 0:
            self._in("BUILD HỎNG (mã " + str(rc) + ") — KHÔNG thử lại, KHÔNG start container.")
            self._in_duoi(err)
            return MA_BUILD_HONG
        rc, out, _e = self._goi(["docker", "image", "inspect", "--format", FMT_NHAN_ANH, kq["IMAGE_NAME"]])
        try:
            nhan = json.loads(_dong_dau(out) or "{}") if rc == 0 else {}
        except ValueError:
            nhan = {}
        if (nhan or {}).get(NHAN_INPUTS) != them["IMAGE_INPUTS_SHA256"]:
            self._in("NHÃN image KHÔNG mang dấu vân tay vừa truyền — Dockerfile hoặc build arg thiếu; "
                     "không start (nếu bỏ qua, mọi lượt sau đều build lại).")
            return MA_NHAN_SAI
        return 0

    def _cho_healthy(self) -> int:
        han = self.dong_ho() + HAN_CHO_HEALTHY_GIAY
        while True:
            rc, out, _e = self._goi(self._compose("ps", "-q", DICH_VU))
            cid = _dong_dau(out) if rc == 0 else None
            if cid:
                _rc, out, _e = self._goi(["docker", "inspect", "--format", FMT_SUC_KHOE, cid])
                tt, _, sk = (out or "").strip().partition("|")
                if not sk:
                    tt, sk = "running", tt
            else:
                tt, sk = "missing", ""
            if sk == "healthy":
                self._in("HEALTHCHECK_STATUS = healthy")
                return 0
            if sk in ("unhealthy", "none") or tt not in ("running", "created", "restarting"):
                self._in("HEALTHCHECK_STATUS = " + (sk or tt) + " — xem `docker compose logs backend`.")
                return MA_KHONG_HEALTHY
            if self.dong_ho() >= han:
                self._in("HEALTHCHECK_STATUS = timeout sau " + str(HAN_CHO_HEALTHY_GIAY) + "s")
                return MA_KHONG_HEALTHY
            self.ngu(NHIP_CHO_GIAY)

    def up(self) -> int:
        kq = self.kiem_tra()
        self.bao_cao(kq)
        quyet = kq["decision"]
        if quyet == CONFIGURATION_ERROR:
            self._in("DỪNG: cấu hình chưa dùng được — không build, không start.")
            return MA_THOAT[quyet]
        if quyet == MIGRATION_APPROVAL_REQUIRED:
            self._in("DỪNG TRƯỚC build/start: DB không ở đúng head của cây nguồn. Migration phải được "
                     "NGƯỜI duyệt (sao lưu trước) — launcher không dùng `alembic upgrade` lúc khởi động "
                     "để vượt cổng này.")
            return MA_THOAT[quyet]
        if quyet in (IMAGE_MISSING, REBUILD_IMAGE):
            ma = self._build_mot_lan(kq)
            if ma:
                return ma
        if quyet != REUSE_IMAGE:
            rc, _out, err = self._goi(self._compose("up", "-d", "--no-deps", "--no-build", DICH_VU))
            if rc != 0:
                self._in("UP HỎNG (mã " + str(rc) + ") — KHÔNG thử lại.")
                self._in_duoi(err)
                return MA_UP_HONG
        ma = self._cho_healthy()
        if ma:
            return ma
        if quyet == REUSE_IMAGE:
            return 0
        sau = self.kiem_tra()
        self._in("DECISION_AFTER_UP = " + sau["decision"] + " (" + ", ".join(sau["reasons"]) + ")")
        return 0 if sau["decision"] == REUSE_IMAGE else MA_SAU_UP_LECH


# ══ CLI ═══════════════════════════════════════════════════════════════════════
def main(argv=None) -> int:
    import argparse
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(prog="dev_backend.py", description="vòng phát triển backend Docker")
    sub = p.add_subparsers(dest="lenh", required=True)
    for ten in ("check", "status"):
        s = sub.add_parser(ten)
        s.add_argument("--json", action="store_true")
    sub.add_parser("up")
    c = sub.add_parser("classify")
    c.add_argument("duong_dan", nargs="*")
    c.add_argument("--json", action="store_true")
    f = sub.add_parser("fingerprint")
    f.add_argument("--files", action="store_true", help="chỉ in danh sách file đầu vào")
    a = p.parse_args(argv)

    if a.lenh == "fingerprint":
        dv = dau_van_anh(GOC)
        if a.files:
            for t in dv["files"]:
                print(t)
        else:
            print(che(json.dumps(dv, ensure_ascii=False, indent=2)))
        return 0
    if a.lenh == "classify":
        duong = list(a.duong_dan)
        if not duong:
            rc, out, _e = chay_that(["git", "-C", str(GOC), "status", "--porcelain=v1", "-z",
                                     "--untracked-files=all"])
            duong = _doc_porcelain(out) if rc == 0 else []
        kq = phan_loai_thay_doi(duong, doc_mo_hinh(GOC))
        if a.json:
            print(che(json.dumps(kq, ensure_ascii=False, indent=2)))
        else:
            for h in kq["paths"]:
                print(h["path"] + " → " + h["class"] + " (" + h["reason"] + ")")
            print("CHANGE_CLASS = " + kq["class"])
        return 0

    dk = DieuKhien(GOC)
    if a.lenh == "up":
        return dk.up()
    kq = dk.kiem_tra()
    if a.json:
        print(che(json.dumps(kq, ensure_ascii=False, indent=2)))
    else:
        dk.bao_cao(kq, day_du=(a.lenh == "status"))
    if a.lenh == "check":
        return MA_THOAT[kq["decision"]]
    return 2 if kq["decision"] == CONFIGURATION_ERROR else 0


if __name__ == "__main__":
    raise SystemExit(main())
