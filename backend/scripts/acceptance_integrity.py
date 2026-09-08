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
#: 1.0 → 1.1 (2026-09-04, `V3_THRESHOLD_AND_RUN_IDENTITY_POLICY`): manifest
#: ghi thêm danh tính SCORER, THRESHOLD POLICY, ATTRIBUTION RUBRIC và trọn bộ
#: tham số decoding. Trước đó nó ghi `runner_hash` mà **không** ghi scorer —
#: nên một lượt đo có thể đổi bộ chấm giữa reseal và live mà không cổng nào
#: thấy. Đây là version của BỘ ĐO, không phải `CACHE_VERSION`.
ARTIFACT_SCHEMA_VERSION = "1.2"

#: Mọi phiên bản artifact ĐỌC được, cũ nhất trước. Version dispatch phải RÕ
#: RÀNG: "đọc được" và "dùng để nghiệm thu được" là hai câu, và trộn chúng là
#: cách một artifact 1.0 lẳng lặng được chấm bằng thước 1.2.
PHIEN_BAN_DOC_DUOC = ("1.0", "1.1", "1.2")

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
        if str(v) not in PHIEN_BAN_DOC_DUOC:
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
def _git(*a: str, giu_le: bool = False) -> str:
    """Chạy `git`. `giu_le=True` ⇒ **không** `strip()`.

    ⚠️ `strip()` mặc định là đúng cho `rev-parse` nhưng SAI cho
    `status --porcelain`: định dạng ấy là `XY<space>path` với `X`/`Y` có thể là
    dấu cách, nên một file *đã sửa nhưng chưa stage* ra ` M path`. `strip()`
    toàn bộ output ăn mất dấu cách đầu của **dòng đầu tiên** — xem
    `phan_loai_dirty`.
    """
    goc = Path(__file__).resolve().parents[2]
    ra = subprocess.run(["git", *a], cwd=str(goc), capture_output=True,
                        text=True, encoding="utf-8", errors="replace").stdout
    return ra if giu_le else ra.strip()


def phan_loai_dirty() -> dict[str, Any]:
    """§18 — tách thay đổi chưa commit thành TRỌNG YẾU và không.

    Không đòi cây sạch tuyệt đối: user có thể đang sửa một file frontend không
    liên quan, và bắt họ commit để cổng xanh là bắt sai người trả giá. Nhưng
    một thay đổi trong `backend/app` hay chính runner thì làm lượt đo mất nghĩa
    — nó đo một hệ không có trong lịch sử nào.
    """
    # ⚠️ `giu_le=True` — BẮT BUỘC. Đo được 2026-09-08
    # (`THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT`): định dạng porcelain là
    # `XY<space>path`, và một file đã sửa mà chưa stage ra ` M path`. Bản trước
    # gọi `_git(...)` có `strip()`, nên **dòng đầu tiên** mất dấu cách đầu và
    # `d[3:]` ăn luôn ký tự đầu của đường dẫn:
    #
    #     ' M backend/app/…/plane_equation.py'  →  'ackend/app/…'
    #
    # Hậu quả KHÔNG cosmetic: `startswith("backend/app")` khi ấy là False, nên
    # file ấy rơi khỏi `ban_trong_yeu` và `mo_run` KHÔNG chặn một lượt đo mở
    # trên mã sản phẩm đang dirty — đúng thứ `DUONG_TRONG_YEU` sinh ra để chặn.
    # Bịt lặng lẽ ở đúng file đứng đầu danh sách, tức không đoán trước được cái
    # nào lọt.
    dong = [d for d in _git("status", "--porcelain", giu_le=True).splitlines()
            if d.strip()]
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
    #: ─── DANH TÍNH BỘ CHẤM VÀ CHÍNH SÁCH (1.1) ──────────────────────────
    #:
    #: Con dấu khoá *"đo CÁI GÌ"*; manifest khoá *"đo NHƯ THẾ NÀO"*. Thiếu ba
    #: băm dưới đây thì vế thứ hai hở đúng chỗ dễ trôi nhất: bộ chấm và ngưỡng
    #: đổi được sau khi thấy kết quả mà không để lại dấu.
    scorer_path: str | None = None
    scorer_hash: str | None = None
    threshold_policy_path: str | None = None
    threshold_policy_hash: str | None = None
    attribution_rubric_hash: str | None = None
    #: Cả ba băm trên đều do `measurement_policy` TÍNH RA. Không ghim chính nó
    #: thì còn một nước đi: đổi phép băm TRƯỚC khi mở lượt đo — manifest và
    #: certifier sẽ nhất trí với nhau, và cùng sai.
    policy_loader_hash: str | None = None
    #: ─── DANH TÍNH MODEL, CÓ KIỂU (1.1) ─────────────────────────────────
    #:
    #: `model` ở trên là dict tự do, và chính vì tự do mà
    #: `run_curved_ergonomics_v2.py:297` ghi được `"repair_attempts": "mặc
    #: định sản phẩm"` — đọc như đã khai, không nói con số nào. Bảy trường
    #: dưới đây có kiểu và có guard đọc; `None` nghĩa là **chưa ghim**, và
    #: `None` phải được ghi thật chứ không được lấp bằng văn xuôi.
    model_provider: str | None = None
    model_name: str | None = None
    model_version_or_snapshot: str | None = None
    #: ─── 1.2: THAM SỐ GIẢI MÃ CÓ KIỂU ────────────────────────────────
    #:
    #: 1.1 dùng ba trường phẳng `temperature`/`top_p`/`max_output_tokens`, và
    #: `None` ở đó gộp hai chuyện khác hẳn nhau: *"không gửi"* với *"provider
    #: có mặc định mà ta không quan sát được"*. Cái đầu ta biết hết, cái sau ta
    #: chỉ biết là mình không biết — và một phép đo phải nói được sự khác nhau
    #: ấy. `MP.CHE_DO_THAM_SO` là thẩm quyền của ba trạng thái.
    decoding_parameters: dict[str, Any] | None = None
    model_reproducibility: str | None = None
    response_model_version: str | None = None
    sdk: dict[str, Any] | None = None
    api_endpoint_class: str | None = None
    repair_limit: int | None = None
    transport_retry_policy: dict[str, Any] | None = None
    application_call_budget: int | None = None
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
            "scorer_path": self.scorer_path, "scorer_hash": self.scorer_hash,
            "threshold_policy_path": self.threshold_policy_path,
            "threshold_policy_hash": self.threshold_policy_hash,
            "attribution_rubric_hash": self.attribution_rubric_hash,
            "policy_loader_hash": self.policy_loader_hash,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "model_version_or_snapshot": self.model_version_or_snapshot,
            "decoding_parameters": self.decoding_parameters,
            "model_reproducibility": self.model_reproducibility,
            "response_model_version": self.response_model_version,
            "sdk": self.sdk, "api_endpoint_class": self.api_endpoint_class,
            "repair_limit": self.repair_limit,
            "transport_retry_policy": self.transport_retry_policy,
            "application_call_budget": self.application_call_budget,
        }


def mo_run(thu_muc: Path, *, run_id: str, muc_dich: str, runner: str,
           ca: Iterable[dict], model: dict[str, Any], chinh_sach_sua: str,
           ngan_sach_goi: int, bo_qua_dirty: bool = False,
           duong_chinh_sach: Path | None = None,
           bo_sung: dict[str, Any] | None = None) -> RunManifest:
    """Mở một lượt đo: kiểm điều kiện, tạo thư mục MỚI, ghi manifest.

    Thư mục đã tồn tại ⇒ DỪNG (§6, §19: không resume ngầm). Muốn chạy lại thì
    `run_id` mới — nó rẻ, còn một artifact trộn hai lượt thì không cứu được.

    ─── HAI THAM SỐ THÊM 2026-09-08 (`THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT`)

    `duong_chinh_sach` — **`None` giữ nguyên hành vi cũ** (`MP.nap_nguong()`,
    tức chính sách V3). Trước bản này đường dẫn ấy là HẰNG SỐ trong thân hàm,
    nên mọi lượt đo mở qua đây đều ghim ngưỡng V3 vào manifest — kể cả một lượt
    đo của khoá luận chạy trên bộ ca khác và ngưỡng khác. Đó là một khoảng
    trống ĐO ĐƯỢC (`RUN_PLAN.json` → `KHOANG_TRONG.nap_chinh_sach_khoa_luan`),
    và cách đóng nó rẻ nhất là để người gọi nói ra chính sách của mình.

    `bo_sung` — trường phụ của riêng một lượt đo, gộp vào JSON manifest. Cố ý
    KHÔNG nâng `ARTIFACT_SCHEMA_VERSION`: 1.2 là hợp đồng về **trường bắt
    buộc**, và thêm một khối tuỳ chọn không phá hợp đồng ấy. Người gọi tự khoá
    khối của mình bằng guard riêng — trộn nó vào `TRUONG_MANIFEST_1_1` sẽ bắt
    mọi runner cũ khai một thứ chúng không có.
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
    # ─── GHIM BỘ CHẤM VÀ CHÍNH SÁCH (1.1) ────────────────────────────────
    #
    # Băm ở ĐÂY, lúc mở lượt đo — không phải lúc chấm. Băm lúc chấm là băm thứ
    # đang chạy, và nó sẽ khớp chính nó dù ai đó vừa sửa bộ chấm giữa chừng.
    import measurement_policy as MP

    scorer = Path(__file__).resolve().parent / "acceptance_verdict.py"
    duong_cs = duong_chinh_sach or MP.CHINH_SACH_NGUONG
    nguong, bam_nguong = MP.doc_chinh_sach(duong_cs)
    _rubric, bam_rubric = MP.nap_rubric()
    mf = RunManifest(
        run_id=run_id, muc_dich=muc_dich, runner=duong_runner.name,
        runner_hash=hashlib.sha256(
            duong_runner.read_bytes()).hexdigest() if duong_runner.exists()
        else "khong_doc_duoc",
        model=model, chinh_sach_sua=chinh_sach_sua, ngan_sach_goi=ngan_sach_goi,
        seal=seal_bo_ca(ca), moi_truong=moi_truong_hien_tai(),
        git={"head": _git("rev-parse", "HEAD"), **dirty},
        scorer_path=scorer.name,
        scorer_hash=hashlib.sha256(scorer.read_bytes()).hexdigest(),
        threshold_policy_path=duong_cs.name,
        threshold_policy_hash=bam_nguong,
        attribution_rubric_hash=bam_rubric,
        policy_loader_hash=hashlib.sha256(
            Path(MP.__file__).read_bytes()).hexdigest(),
        # Rút từ `model` để callers cũ không phải đổi chữ ký. Khoá vắng mặt ⇒
        # `None` ⇒ guard đọc là CHƯA GHIM — đúng thứ nó phải nói.
        model_provider=model.get("provider"),
        model_name=model.get("model_name"),
        model_version_or_snapshot=model.get("model_version_or_snapshot"),
        decoding_parameters=model.get("decoding_parameters"),
        model_reproducibility=MP.kiem_danh_tinh_model(model, nguong)[0],
        response_model_version=model.get("response_model_version"),
        sdk=model.get("sdk"),
        api_endpoint_class=model.get("api_endpoint_class"),
        repair_limit=model.get("repair_limit"),
        transport_retry_policy=model.get("transport_retry_policy"),
        application_call_budget=ngan_sach_goi,
    )
    thu_muc.mkdir(parents=True)
    ghi_artifact(thu_muc / "manifest.json", {**mf.to_json(), **(bo_sung or {})})
    return mf


def kiem_ghim_bo_do(mf_json: dict[str, Any]) -> list[str]:
    """Bốn băm bộ đo trong manifest ĐÃ GHI có còn khớp thực tế không?

    Nhận **dict đọc từ đĩa**, không nhận `RunManifest` trong bộ nhớ — và đó là
    toàn bộ điểm của hàm này. Ghim rồi recompute trong cùng một tiến trình là
    phép so luôn đúng: không có gì kịp đổi giữa hai lần đọc file. Trôi chỉ
    thành quan sát được khi so bản ĐÃ GHI của lượt trước với hiện tại.

    Trả danh sách lỗi — rỗng là khớp. Manifest 1.0 (thiếu bốn trường) trả về
    lỗi "THIẾU", không phải im lặng: một lượt đo không ghim được danh tính bộ
    đo của chính nó thì không dùng để nghiệm thu được.

    ⚠️ **Chính sách đọc TỪ MANIFEST, không từ một hằng số** (2026-09-08). Bản
    trước gọi thẳng `MP.nap_nguong()` — tức luôn so với chính sách V3, kể cả
    khi manifest tự khai nó ghim một chính sách khác. Hệ quả: mọi lượt đo
    không-V3 báo `threshold_policy_hash TRÔI` vĩnh viễn, vì một lý do không
    liên quan gì tới việc có trôi hay không. Câu hàm này phải hỏi là *"chính
    sách mà lượt đo NÀY ghim có còn nguyên không"*, và câu ấy chỉ trả lời được
    khi đọc `threshold_policy_path` của chính manifest.
    """
    import measurement_policy as MP

    goc = Path(__file__).resolve().parent
    ten_cs = mf_json.get("threshold_policy_path")
    duong_cs = (MP.THU_MUC / ten_cs) if ten_cs else MP.CHINH_SACH_NGUONG
    if not duong_cs.exists():
        return [f"chính sách `{ten_cs}` mà manifest ghim KHÔNG còn trên đĩa"]
    _n, bam_nguong = MP.doc_chinh_sach(duong_cs)
    _r, bam_rubric = MP.nap_rubric()

    def _tep(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    loi = []
    for ten, thuc in (
            ("scorer_hash", _tep(goc / "acceptance_verdict.py")),
            ("threshold_policy_hash", bam_nguong),
            ("attribution_rubric_hash", bam_rubric),
            ("policy_loader_hash", _tep(Path(MP.__file__)))):
        trong_mf = mf_json.get(ten)
        if not trong_mf:
            loi.append(f"manifest THIẾU `{ten}` — bộ đo không ghim được "
                       f"danh tính của chính nó")
        elif trong_mf != thuc:
            loi.append(f"`{ten}` TRÔI: manifest {trong_mf[:16]}… ≠ "
                       f"thực tế {thuc[:16]}…")
    return loi


#: Trường manifest 1.1 BẮT BUỘC phải CÓ MẶT (giá trị có thể `None` — vắng mặt
#: và "khai là chưa biết" là hai chuyện khác nhau, và guard phân biệt được).
TRUONG_MANIFEST_1_1 = (
    "scorer_path", "scorer_hash", "threshold_policy_path",
    "threshold_policy_hash", "attribution_rubric_hash", "policy_loader_hash",
    "model_provider", "model_name", "model_version_or_snapshot",
    "decoding_parameters", "model_reproducibility", "response_model_version",
    "sdk", "api_endpoint_class", "repair_limit",
    "transport_retry_policy", "application_call_budget",
)


def kiem_manifest_du_truong(mf_json: dict[str, Any]) -> list[str]:
    """Manifest 1.2 có đủ trường không. Bản 1.0/1.1 được MIỄN, có chủ đích.

    Version dispatch rõ ràng thay cho "đọc được thì thôi": artifact lịch sử
    phải đọc được nguyên vẹn, nhưng nó **không** vì thế mà dùng để nghiệm thu
    được. Hai câu khác nhau, và cả hai đều phải nói thành tiếng.
    """
    if mf_json.get("artifact_schema_version") != ARTIFACT_SCHEMA_VERSION:
        return []
    return [f"manifest {ARTIFACT_SCHEMA_VERSION} THIẾU trường `{t}`"
            for t in TRUONG_MANIFEST_1_1 if t not in mf_json]


def kiem_san_sang_live(mf_json: dict[str, Any], nguong: dict) -> list[str]:
    """Lượt đo này ĐƯỢC PHÉP bắt đầu chưa — khác câu "bộ đo có đúng không".

    Tách khỏi `chung_nhan` có chủ đích. Chứng nhận hỏi *bộ đo có chấm đúng
    không* và trả lời được bằng ca tổng hợp; câu hỏi ở đây là *lượt LIVE này
    có tái lập được không*, và một ca tổng hợp không trả lời hộ được. Gộp hai
    câu vào một verdict thì hoặc chứng nhận đỏ oan, hoặc readiness xanh oan.
    """
    import measurement_policy as MP

    loi = kiem_manifest_du_truong(mf_json) + kiem_ghim_bo_do(mf_json)
    _v, thieu = MP.kiem_danh_tinh_model(mf_json, nguong)
    loi += thieu
    if mf_json.get("transport_retry_policy") is None:
        loi.append("`transport_retry_policy` chưa khoá trước lượt chạy — "
                   "retry hạ tầng quyết định sau sẽ quyết định theo kết quả")
    if not MP._la_so(mf_json.get("application_call_budget")):
        loi.append("`application_call_budget` chưa phải một số — trần gọi "
                   "không đếm được thì lượt đo không dừng đúng chỗ")
    return loi


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
