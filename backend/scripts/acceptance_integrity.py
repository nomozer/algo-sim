# -*- coding: utf-8 -*-
"""TẦNG TOÀN VẸN CHO MỌI LƯỢT ĐO SỐNG — hạ tầng bộ đo, **0 lượt gọi model**.

    `ACCEPTANCE_RUNNER_INTEGRITY`, 2026-09-04.

Module này KHÔNG chạy lượt đo nào. Nó cung cấp những thứ mà mọi runner sống phải
đi qua, để bảy sự cố đã xảy ra không xảy ra lần nữa:

    ① runner in `input/output = 0`   telemetry Gemini dùng `promptTokenCount`
    ② artifact V1 mất RequestContract   ⇒ không replay tất định được
    ③ đọc kết quả từ `envelope["scene3d"]`   thay vì thẩm quyền kết quả
    ④ một artifact bị lệnh shell ghi đè   phải khôi phục bằng `git checkout`
    ⑤ nhân chứng "đủ đường" thiếu chính nghĩa vụ đang đo
    ⑥ ca âm chết sớm ở R0   ⇒ fail-closed NHƯNG không chứng minh ranh giới định đo
    ⑦ lỗi HỆ và lỗi MÔ HÌNH bị gộp cột

Ranh giới: đây là **bộ đo**, nằm ở `scripts/` nên KHÔNG thuộc
`MEASURED_SYSTEM_PATHS` — cứng cáp thêm ở đây không phá đóng băng candidate.
Nó **đọc** thẩm quyền sản phẩm (`app.ai.telemetry`, `app.runtime_identity`) và
tuyệt đối không sửa chúng.

─── VÌ SAO KHÔNG VÁ TỪNG RUNNER ───────────────────────────────────────────

Kho có ~20 script `run_*`/`probe_*`, mỗi cái tự viết lấy phần ghi artifact,
phần đếm token, phần phân loại lỗi. Bảy sự cố trên là bảy bản sao của cùng một
thiếu sót, và vá từng nơi là hẹn lần thứ tám ở nơi thứ hai mươi mốt. Runner
lịch sử **không** được viết lại (§21 — bằng chứng lịch sử giữ nguyên); runner
MỚI đi qua đây.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

__all__ = [
    "ARTIFACT_SCHEMA_VERSION",
    "IntegrityError",
    "RunManifest",
    "chuan_hoa_telemetry",
    "doc_artifact",
    "ghi_artifact",
    "kiem_moi_truong",
    "moi_truong_hien_tai",
    "mo_run",
    "phan_loai_dirty",
    "seal_bo_ca",
    "tom_tat_tu_artifact",
    "tu_kiem_tom_tat",
]

#: Phiên bản ĐỊNH DẠNG artifact đo. **KHÔNG** dùng `CACHE_VERSION` cho việc này
#: (§20): cache là chính sách sản phẩm, đây là hình dạng file bộ đo — trộn hai
#: thứ đó là buộc một lượt bump cache mỗi khi thêm một trường báo cáo.
ARTIFACT_SCHEMA_VERSION = "1.0"

#: Đường dẫn mà một thay đổi CHƯA COMMIT sẽ làm hỏng ý nghĩa của lượt đo (§18).
#: Không đòi `git clean` toàn kho: user có thể đang làm việc khác, và bắt họ
#: commit để một cổng xanh là bắt sai người trả giá.
DUONG_TRONG_YEU = (
    "backend/app",
    "backend/scripts",
    "frontend/src/simulations/domains/semantic",
)


class IntegrityError(RuntimeError):
    """Vi phạm toàn vẹn. **Luôn dừng lượt đo** — không có nhánh 'cảnh báo rồi
    chạy tiếp': một lượt đo chạy tiếp sau khi mất toàn vẹn sinh ra artifact
    trông như bằng chứng mà không phải."""


# ══════════════════════════════════════════════════════════════════════════
# §8–§9 · TELEMETRY — MỘT THẨM QUYỀN CHUẨN HOÁ
# ══════════════════════════════════════════════════════════════════════════
#: Tên cục bộ của `app.ai.telemetry` → tên trong báo cáo. Đây là ánh xạ DUY
#: NHẤT; runner không được tự đoán tên trường.
#:
#: ⚠️ SỰ CỐ ①: `usage_report()` trả khoá `prompt_tokens`/`candidates_tokens`
#: (đã chuẩn hoá từ `promptTokenCount` của Gemini), còn runner V1 đọc
#: `input`/`output` — hai tên không tồn tại. `dict.get(k, 0)` trả 0, nên báo cáo
#: in `INPUT_TOKENS 0` cho một lượt đã tiêu hàng chục nghìn token. Không gì đỏ:
#: 0 là một con số hợp lệ.
_TRUONG = {
    "prompt_tokens": "input_tokens",
    "candidates_tokens": "output_tokens",
    "thoughts_tokens": "thought_tokens",
    "cached_content_tokens": "cached_tokens",
    "total_tokens": "total_tokens",
}


def chuan_hoa_telemetry(bao_cao: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """`telemetry.usage_report()` → dạng chuẩn, GIỮ NGUYÊN bản thô.

    §8: hình dạng lạ **KÊU TO**, không bao giờ lặng lẽ báo 0.
    `MISSING_TELEMETRY != 0_TOKENS` — thiếu số đo và đo được số 0 là hai sự
    kiện khác nhau, và gộp chúng là cách sự cố ① sống sót qua cả một wave.

    Trả `{"raw": …, "theo_stage": …, "tong": …, "calls": …}`.
    """
    if not isinstance(bao_cao, dict):
        raise IntegrityError(
            f"telemetry không phải dict mà là {type(bao_cao).__name__} — "
            f"hình dạng lạ thì DỪNG, đừng báo 0")

    theo_stage: dict[str, dict[str, int]] = {}
    tong = {v: 0 for v in _TRUONG.values()}
    tong_calls = 0

    for stage, so in sorted(bao_cao.items()):
        if not isinstance(so, dict):
            raise IntegrityError(f"stage '{stage}': telemetry không phải dict")
        la = set(so) - set(_TRUONG) - {"calls"}
        if la:
            raise IntegrityError(
                f"stage '{stage}': trường telemetry KHÔNG BIẾT {sorted(la)}. "
                f"Provider đổi lược đồ, hoặc runner ghi nhầm — cả hai đều phải "
                f"dừng để người xem, không được im lặng bỏ qua.")
        hang: dict[str, int] = {}
        for cuc_bo, ten in _TRUONG.items():
            if cuc_bo not in so:
                # THIẾU ≠ 0. Ghi `None` để báo cáo in "UNKNOWN".
                hang[ten] = None            # type: ignore[assignment]
                continue
            gt = so[cuc_bo]
            if not isinstance(gt, int) or isinstance(gt, bool):
                raise IntegrityError(
                    f"stage '{stage}.{cuc_bo}': token phải là int, nhận "
                    f"{gt!r} ({type(gt).__name__})")
            hang[ten] = gt
            tong[ten] += gt
        calls = so.get("calls")
        if not isinstance(calls, int) or isinstance(calls, bool):
            raise IntegrityError(
                f"stage '{stage}': thiếu/sai `calls` — số lượt gọi phải ĐẾM "
                f"được từ bản ghi, không suy từ số stage của pipeline (§10)")
        hang["calls"] = calls
        tong_calls += calls
        theo_stage[stage] = hang

    thieu = sorted({t for h in theo_stage.values()
                    for t, v in h.items() if v is None})
    return {
        "raw": {k: dict(v) for k, v in sorted(bao_cao.items())},
        "theo_stage": theo_stage,
        "tong": tong,
        "calls": tong_calls,
        # Rỗng = đủ. Không rỗng = báo cáo phải in UNKNOWN ở đúng ô ấy.
        "truong_thieu": thieu,
    }


def kiem_bat_bien_token(chuan: dict[str, Any]) -> list[str]:
    """§9 — bất biến cộng dồn, chỉ áp ở nơi provider thật sự bảo đảm.

    Gemini: `totalTokenCount` bao gồm cả `thoughtsTokenCount`, nên
    `total >= input + output` **không** luôn đúng theo chiều ngược lại; điều
    chắc chắn là `total >= input` và `total >= thought`. Chỉ khẳng định thứ
    lược đồ thật sự bảo đảm — một bất biến bịa ra sẽ đỏ ở lượt đo thật rồi bị
    tắt đi, và khi ấy ta mất cả cái đúng lẫn cái sai.
    """
    loi: list[str] = []
    for stage, h in chuan["theo_stage"].items():
        tong, vao = h.get("total_tokens"), h.get("input_tokens")
        nghi, ra = h.get("thought_tokens"), h.get("output_tokens")
        if tong is None:
            continue
        for ten, gt in (("input", vao), ("thought", nghi), ("output", ra)):
            if gt is not None and tong < gt:
                loi.append(f"{stage}: total {tong} < {ten} {gt}")
        if None not in (vao, ra, nghi) and tong < vao + ra:
            loi.append(f"{stage}: total {tong} < input+output {vao + ra}")
    return loi


# ══════════════════════════════════════════════════════════════════════════
# §6–§7 · GHI ARTIFACT — KHÔNG ĐÈ, GHI NGUYÊN KHỐI
# ══════════════════════════════════════════════════════════════════════════
#: §7 — artifact ĐÃ ĐỌC trong tiến trình này. Không lệnh nào được dùng cùng một
#: file làm CẢ đầu vào lẫn đầu ra: đó chính xác là hình dạng sự cố ④, nơi một
#: glob nở ra hai đường và file thứ hai thành đầu ra của file thứ nhất.
_DA_DOC: set[str] = set()


def ghi_artifact(duong: Path, noi_dung: Any, *, cho_de: bool = False) -> Path:
    """Ghi JSON **nguyên khối**, mặc định TỪ CHỐI đè.

    ⚠️ SỰ CỐ ④: một lệnh `python -m json.tool a.json b.json` (glob nở ra hai
    file) coi file thứ hai là ĐẦU RA và ghi đè một artifact đã commit. Khôi
    phục được nhờ `git`, nhưng chỉ vì nó đã được commit — một artifact vừa sinh
    ra thì không có đường về.

    Hai lớp phòng:

    ① **Từ chối đè.** Đường dẫn đã tồn tại ⇒ `IntegrityError`, không truncate.
       Ghi đè một lượt đo cũ là xoá bằng chứng, và bộ đo hình học đã theo luật
       này từ đầu (*"từ chối ghi đè artifact lượt cũ — đó là tính năng"*).

    ② **Nguyên khối.** Ghi ra file tạm cùng thư mục → `flush` + `fsync` →
       `os.replace`. Tiến trình chết giữa chừng để lại **file cũ nguyên vẹn
       hoặc không có file**, không bao giờ để lại JSON cụt. Sự cố ⑧ (đọc phải
       artifact cụt) chỉ có thể xảy ra nếu ai đó ghi từng phần.
    """
    duong = Path(duong)
    if duong.exists() and not cho_de:
        raise IntegrityError(
            f"artifact ĐÃ TỒN TẠI: {duong}\n"
            f"Bộ đo không đè lượt cũ. Dùng `run_id` mới, hoặc nếu thật sự muốn "
            f"thay thì xoá tay và ghi lại lý do vào báo cáo.")
    if str(duong.resolve()) in _DA_DOC:
        raise IntegrityError(
            f"artifact này ĐÃ ĐƯỢC ĐỌC trong tiến trình rồi lại đem GHI: "
            f"{duong}\nMột lệnh không được dùng cùng một file làm cả đầu vào "
            f"lẫn đầu ra (§7) — đó đúng là hình dạng của sự cố ④.")
    duong.parent.mkdir(parents=True, exist_ok=True)
    van = json.dumps(noi_dung, ensure_ascii=False, indent=1, sort_keys=False)
    fd, tam = tempfile.mkstemp(dir=str(duong.parent), suffix=".tmp",
                               prefix=duong.name + ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(van)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tam, duong)
    except BaseException:
        Path(tam).unlink(missing_ok=True)
        raise
    return duong


def doc_artifact(duong: Path, *, doi_schema: bool = True) -> dict:
    """Đọc artifact đo. Hỏng/cụt/sai phiên bản ⇒ **NÉM**, không bỏ qua.

    §24H: một reader lặng lẽ `continue` khi gặp file hỏng sẽ báo cáo một tổng
    nhỏ hơn sự thật, và không ai biết. Thà đỏ.
    """
    duong = Path(duong)
    try:
        van = duong.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise IntegrityError(f"thiếu artifact: {duong}") from e
    try:
        d = json.loads(van)
    except json.JSONDecodeError as e:
        raise IntegrityError(
            f"artifact HỎNG (JSON không đọc được): {duong} — {e}") from e
    if not isinstance(d, dict):
        raise IntegrityError(f"artifact phải là object: {duong}")
    _DA_DOC.add(str(duong.resolve()))
    if doi_schema:
        v = d.get("artifact_schema_version")
        if v is None:
            raise IntegrityError(
                f"artifact không khai `artifact_schema_version`: {duong}")
        if str(v).split(".")[0] != ARTIFACT_SCHEMA_VERSION.split(".")[0]:
            raise IntegrityError(
                f"artifact phiên bản {v} KHÔNG tương thích với reader "
                f"{ARTIFACT_SCHEMA_VERSION}: {duong}")
    return d


# ══════════════════════════════════════════════════════════════════════════
# §5 · NIÊM PHONG BỘ CA
# ══════════════════════════════════════════════════════════════════════════
def _bam(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def seal_bo_ca(ca: Iterable[dict]) -> dict[str, Any]:
    """Niêm phong định nghĩa ca TRƯỚC lượt gọi đầu tiên.

    Băm từng ca **và** cả bộ. Sửa một chữ trong đề, đổi đáp số mong đợi, hay
    đổi ranh giới kỳ vọng sau khi đã thấy đầu ra — tất cả đều làm băm lệch, và
    `kiem_bo_ca` sẽ dừng lượt đo. Không có đường "sửa ca cho khớp kết quả".
    """
    ds = list(ca)
    ids = [c["id"] for c in ds]
    if len(set(ids)) != len(ids):
        raise IntegrityError(f"id ca trùng nhau: {ids}")
    return {"case_set_hash": _bam(ds), "per_case": {c["id"]: _bam(c) for c in ds},
            "ids": ids}


def kiem_bo_ca(seal: dict[str, Any], ca: Iterable[dict]) -> None:
    """Bộ ca có còn đúng bản đã niêm phong không? Lệch ⇒ DỪNG."""
    nay = seal_bo_ca(ca)
    if nay["case_set_hash"] == seal["case_set_hash"]:
        return
    doi = sorted(
        i for i in set(nay["per_case"]) | set(seal["per_case"])
        if nay["per_case"].get(i) != seal["per_case"].get(i))
    raise IntegrityError(
        f"BỘ CA ĐÃ ĐỔI giữa lượt đo — ca lệch: {doi}\n"
        f"Sửa ca sau khi thấy đầu ra là tự chọn kết quả. Mở `run_id` mới.")


# ══════════════════════════════════════════════════════════════════════════
# §3, §17, §18 · DANH TÍNH MÔI TRƯỜNG
# ══════════════════════════════════════════════════════════════════════════
def _git(*a: str) -> str:
    goc = Path(__file__).resolve().parents[2]
    return subprocess.run(["git", *a], cwd=str(goc), capture_output=True,
                          text=True, encoding="utf-8",
                          errors="replace").stdout.strip()


def phan_loai_dirty() -> dict[str, Any]:
    """§18 — tách thay đổi chưa commit thành TRỌNG YẾU và không.

    Không đòi cây sạch tuyệt đối: user có thể đang sửa một file frontend không
    liên quan, và bắt họ commit để cổng xanh là bắt sai người trả giá. Nhưng
    một thay đổi trong `backend/app` hay chính runner thì làm lượt đo mất nghĩa
    — nó đo một hệ không có trong lịch sử nào.
    """
    dong = [d for d in _git("status", "--porcelain").splitlines() if d.strip()]
    duong = [d[3:].strip().strip('"') for d in dong]
    trong_yeu = sorted(p for p in duong
                       if any(p.startswith(g) for g in DUONG_TRONG_YEU))
    return {
        "sach": not duong,
        "duong_ban": sorted(duong),
        "ban_trong_yeu": trong_yeu,
        "ban_khong_lien_quan": sorted(set(duong) - set(trong_yeu)),
    }


def moi_truong_hien_tai() -> dict[str, Any]:
    """Ảnh chụp danh tính hệ — đọc từ thẩm quyền sản phẩm, không chép."""
    from app.main import CACHE_VERSION
    from app.runtime_identity import (
        semantic_environment_fingerprint,
        semantic_environment_hash,
        stable_capability_hash,
    )

    return {
        "cache_version": CACHE_VERSION,
        "stable_capability_hash": stable_capability_hash(),
        "semantic_environment_hash": semantic_environment_hash(),
        "components": semantic_environment_fingerprint(),
    }


def kiem_moi_truong(goc: dict[str, Any], *, nhan: str = "") -> None:
    """§17 — môi trường có còn y như lúc mở lượt không? Lệch ⇒ DỪNG.

    Gọi TRƯỚC MỖI lượt gọi provider, không chỉ lúc mở. Sửa một prompt giữa
    chừng rồi chạy tiếp sinh ra artifact **trộn hai phiên bản hệ** — và không
    con số nào trong đó thuộc về một bản nào cả.
    """
    nay = moi_truong_hien_tai()
    doi = [k for k in ("cache_version", "stable_capability_hash",
                       "semantic_environment_hash") if goc.get(k) != nay[k]]
    tp = [k for k, v in nay["components"].items()
          if (goc.get("components") or {}).get(k) != v]
    if doi or tp:
        raise IntegrityError(
            f"MÔI TRƯỜNG ĐỔI GIỮA LƯỢT ĐO{' · ' + nhan if nhan else ''}.\n"
            f"  trường lệch: {doi or '(không)'}\n"
            f"  thành phần lệch: {tp or '(không)'}\n"
            f"Artifact trộn hai phiên bản hệ không thuộc về bản nào. DỪNG.")


@dataclass
class RunManifest:
    """§3 — danh tính BẤT BIẾN của một lượt đo, ghi TRƯỚC lượt gọi đầu tiên.

    Vì sao phải ghi trước: suy lại từ HEAD hiện tại sau khi chạy xong là mô tả
    **hệ bây giờ**, không phải hệ đã sinh ra lượt đo. Hai thứ đó khác nhau đúng
    vào lúc quan trọng nhất — khi ai đó sửa mã giữa chừng.
    """

    run_id: str
    muc_dich: str
    runner: str
    runner_hash: str
    model: dict[str, Any]
    chinh_sach_sua: str
    ngan_sach_goi: int
    seal: dict[str, Any]
    moi_truong: dict[str, Any]
    git: dict[str, Any]
    tao_luc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())
    artifact_schema_version: str = ARTIFACT_SCHEMA_VERSION

    def to_json(self) -> dict[str, Any]:
        return {
            "artifact_schema_version": self.artifact_schema_version,
            "run_id": self.run_id, "tao_luc": self.tao_luc,
            "muc_dich": self.muc_dich,
            "runner": self.runner, "runner_hash": self.runner_hash,
            "model": self.model, "chinh_sach_sua": self.chinh_sach_sua,
            "ngan_sach_goi": self.ngan_sach_goi,
            "seal": self.seal, "moi_truong": self.moi_truong, "git": self.git,
        }


def mo_run(thu_muc: Path, *, run_id: str, muc_dich: str, runner: str,
           ca: Iterable[dict], model: dict[str, Any], chinh_sach_sua: str,
           ngan_sach_goi: int, bo_qua_dirty: bool = False) -> RunManifest:
    """Mở một lượt đo: kiểm điều kiện, tạo thư mục MỚI, ghi manifest.

    Thư mục đã tồn tại ⇒ DỪNG (§6, §19: không resume ngầm). Muốn chạy lại thì
    `run_id` mới — nó rẻ, còn một artifact trộn hai lượt thì không cứu được.
    """
    thu_muc = Path(thu_muc)
    if thu_muc.exists():
        raise IntegrityError(
            f"thư mục lượt đo ĐÃ TỒN TẠI: {thu_muc}\n"
            f"Không resume ngầm (§19). Dùng `run_id` mới.")

    dirty = phan_loai_dirty()
    if dirty["ban_trong_yeu"] and not bo_qua_dirty:
        raise IntegrityError(
            "THAY ĐỔI CHƯA COMMIT ở đường TRỌNG YẾU:\n  "
            + "\n  ".join(dirty["ban_trong_yeu"])
            + "\nLượt đo sẽ đo một hệ không có trong lịch sử nào. Commit "
              "hoặc stash phần trọng yếu (đường không liên quan thì KHÔNG "
              "cần — chúng được ghi vào manifest).")

    duong_runner = Path(runner)
    mf = RunManifest(
        run_id=run_id, muc_dich=muc_dich, runner=duong_runner.name,
        runner_hash=hashlib.sha256(
            duong_runner.read_bytes()).hexdigest() if duong_runner.exists()
        else "khong_doc_duoc",
        model=model, chinh_sach_sua=chinh_sach_sua, ngan_sach_goi=ngan_sach_goi,
        seal=seal_bo_ca(ca), moi_truong=moi_truong_hien_tai(),
        git={"head": _git("rev-parse", "HEAD"), **dirty},
    )
    thu_muc.mkdir(parents=True)
    ghi_artifact(thu_muc / "manifest.json", mf.to_json())
    return mf


# ══════════════════════════════════════════════════════════════════════════
# §22–§23 · TÓM TẮT DẪN XUẤT + TỰ KIỂM
# ══════════════════════════════════════════════════════════════════════════
def tom_tat_tu_artifact(thu_muc: Path) -> dict[str, Any]:
    """§22 — mọi con số của báo cáo DẪN từ artifact từng ca trên đĩa.

    Không nhận số nào từ bộ nhớ tiến trình đang chạy: một biến còn sót từ vòng
    lặp trước, một lượt ghi trượt đường dẫn, một file cụt — cả ba đều cho một
    tổng "hợp lý" mà sai, và không cái nào tự khai ra.
    """
    thu_muc = Path(thu_muc)
    mf = doc_artifact(thu_muc / "manifest.json")
    ca_dir = thu_muc / "cases"
    ket: dict[str, dict] = {}
    for i in mf["seal"]["ids"]:
        f = ca_dir / i / "final.json"
        if f.exists():
            ket[i] = doc_artifact(f)

    tong = {"input_tokens": 0, "output_tokens": 0, "thought_tokens": 0,
            "total_tokens": 0}
    goi = {"analyze": 0, "synthesis": 0, "repair": 0, "khac": 0}
    thieu: list[str] = []
    for i, r in sorted(ket.items()):
        tl = r.get("telemetry") or {}
        for k in tong:
            v = (tl.get("tong") or {}).get(k)
            if v is None:
                thieu.append(f"{i}.{k}")
            else:
                tong[k] += v
        for k, v in (r.get("goi_provider") or {}).items():
            goi[k if k in goi else "khac"] += v

    phan_lop = {i: r.get("phan_lop") for i, r in sorted(ket.items())}
    return {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "run_id": mf["run_id"],
        "CASES_TOTAL": len(mf["seal"]["ids"]),
        "CASES_WITH_ARTIFACT": len(ket),
        "phan_lop": phan_lop,
        "dem_phan_lop": {k: sum(1 for v in phan_lop.values() if v == k)
                         for k in sorted({v for v in phan_lop.values() if v})},
        "CORRECT_SERVABLE_RESULT": sum(
            1 for r in ket.values() if r.get("phan_lop") == "CORRECT_SERVABLE_RESULT"),
        "BOUNDARY_DEMONSTRATED": sum(
            1 for r in ket.values() if r.get("target_boundary_demonstrated") is True),
        "SYSTEM_FAILURES": sum(
            1 for r in ket.values()
            if str(r.get("phan_lop", "")).startswith("SYSTEM_")),
        "APPLICATION_LLM_CALLS": sum(goi.values()),
        "goi_theo_loai": goi,
        "tokens": tong,
        "TELEMETRY_MISSING": sorted(thieu),
    }


def tu_kiem_tom_tat(thu_muc: Path) -> dict[str, Any]:
    """§23 — đọc LẠI từ đĩa, tính lại, so với bản đã ghi.

    Bắt đúng bốn thứ mà mắt không bắt được: ghi trượt đường dẫn · đối tượng còn
    sót trong bộ nhớ · file ghi dở · telemetry lệch. Nếu hai bản khác nhau thì
    báo cáo đang nói về một lượt đo không tồn tại.
    """
    da_ghi = doc_artifact(Path(thu_muc) / "summary.json")
    tinh_lai = tom_tat_tu_artifact(thu_muc)
    lech = sorted(k for k in set(da_ghi) | set(tinh_lai)
                  if da_ghi.get(k) != tinh_lai.get(k))
    if lech:
        raise IntegrityError(
            f"TÓM TẮT ĐÃ GHI ≠ TÍNH LẠI TỪ ĐĨA — trường lệch: {lech}\n"
            f"  đã ghi:  { {k: da_ghi.get(k) for k in lech} }\n"
            f"  tính lại:{ {k: tinh_lai.get(k) for k in lech} }")
    return tinh_lai
