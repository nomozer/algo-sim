# -*- coding: utf-8 -*-
"""G05 REAL-MODEL PILOT — runner. `--live` **TIÊU QUOTA THẬT**; mọi đường khác 0 API call.

    cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \\
        scripts/run_g05_real_model_pilot.py --live --out-dir <thư mục run>/live

Lượt đo `DEVELOPMENT_G05_REAL_MODEL_PILOT` (`HELD_OUT_CLAIM = NO`, `EVALUATOR_INDEPENDENCE = PARTIAL`): 16 đề đăng ký
trước (`runs/g05-real-model-pilot/PILOT_CASES.json`, băm ghim ở `CORPUS_SHA256`) × `k = 1`.

─── G2 · KHÔNG MÁY ĐO THỨ HAI ─────────────────────────────────────────────────
Mỗi đề chạy `measure_geometry_stability.mot_luot` — tức `run_pipeline` THẬT (miền → phạm vi → route + metric khung →
Scene3D → cổng trực quan → envelope), cùng khuôn `run_holdout_pilot.py`: chỉ thay dữ liệu, thư mục ra, kỳ vọng và
oracle cấp module. File `{id}-lan1.json` do `mot_luot` ghi (hợp đồng + chương trình + final_memory); file
`{id}-lan1.pilot.json` là hạng kết cục (`g05_pilot_scoring.phan_loai`). Scene3D dựng lại OFFLINE:
`g05_pilot_scene_replay.py`.

─── NGÂN SÁCH: CHẶN TRƯỚC MỖI LƯỢT GỌI ───────────────────────────────────────
· lượt LOGIC và lần thử HTTP: `ApiBudget` của sản phẩm cho từng đề, trần = min(trần mỗi đề của `mot_luot`, PHẦN CÒN LẠI
  của trần toàn lượt) ⇒ tổng không vượt `CAPS_APPROVED` kể cả retry transport (ApiBudget kiểm TRƯỚC mỗi lần thử).
· token: `GacCong` chặn trước mỗi lượt gọi khi `đã dùng + TOKEN_RESERVE_PER_CALL > trần`; sau mỗi phản hồi cộng
  `usageMetadata` (vào / ra / suy luận / cache) — phản hồi KHÔNG có usage ⇒ DỪNG (không xác định được ngân sách).
· hai lỗi provider liên tiếp ⇒ DỪNG. Lượt đã dừng không bao giờ được tính là "từ chối đúng".

─── G5 · KHOÁ ─────────────────────────────────────────────────────────────────
Khoá đi trong query `?key=` của URL ⇒ logger `httpx`/`httpcore` về WARNING trước lượt gọi đầu; mọi thông điệp lỗi
provider bị che (`che`) TRƯỚC khi rời `GacCong`; sau mỗi đề quét toàn bộ thư mục ra (`quet_khoa`) — thấy khoá ⇒ DỪNG.
Không in, không ghi giá trị khoá ở bất kỳ đâu.

─── TIẾP TỤC ≠ CHẠY LẠI ───────────────────────────────────────────────────────
Có `{id}-lan1.pilot.json` ⇒ đề đã xong: không gọi lại, cộng lại lượt/token của nó vào ngân sách đã dùng.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import logging
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
RUN_DIR = ROOT / "docs" / "evaluation" / "geometry" / "runs" / "g05-real-model-pilot"
CORPUS = RUN_DIR / "PILOT_CASES.json"
#: Băm của corpus ĐĂNG KÝ TRƯỚC. Sửa corpus sau khi ghim ⇒ runner từ chối (test khoá cả hai phía).
CORPUS_SHA256 = "fda51779f2b79576472e0fd91f85e6a9161a53870ead3a0ad731eba9ddab8c6e"
MODEL_APPROVED = "gemini-2.5-flash"
CANDIDATE_EXPECTED = "93077b51d033c198bfb68504e3517f98cb2f9738886f058e687f3562d4520883"
CACHE_VERSION_EXPECTED = "125"
MEASUREMENT = {"MEASUREMENT_CLASS": "DEVELOPMENT_G05_REAL_MODEL_PILOT", "HELD_OUT_CLAIM": "NO",
               "EVALUATOR_INDEPENDENCE": "PARTIAL", "K": 1}
#: Dự trữ cho MỘT lượt gọi khi chặn token trước lượt gọi (lượt sinh chương trình lớn nhất đo được ~ 7–15k token).
TOKEN_RESERVE_PER_CALL = 20_000
PER_CASE_LOGIC, PER_CASE_HTTP = 8, 12          # trần mỗi đề của `mot_luot` (TRAN_LOGIC, TRAN_HTTP)


@dataclass(frozen=True)
class Caps:
    logical: int
    http: int
    tokens: int


CAPS_APPROVED = Caps(logical=64, http=96, tokens=400_000)


class DungPilot(RuntimeError):
    """Lượt pilot DỪNG (ngân sách, usage thiếu, lỗi provider liên tiếp, lộ khoá, kiểm trước live hỏng)."""


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(f"_g05p_{ten}", Path(__file__).resolve().parent / f"{ten}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m                 # dataclass cần module đã đăng ký
    spec.loader.exec_module(m)
    return m


SC = _nap("g05_pilot_scoring")


def nap_corpus(path: Path = CORPUS) -> list[dict]:
    bam = hashlib.sha256(path.read_bytes()).hexdigest()
    if bam != CORPUS_SHA256:
        raise DungPilot(f"corpus không khớp băm đã ghim ({bam[:16]}… ≠ {CORPUS_SHA256[:16]}…)")
    return json.loads(path.read_text(encoding="utf-8"))["cases"]


def che(text: str, key: str | None) -> str:
    return text.replace(key, "[REDACTED]") if key else text


def quet_khoa(thu_muc: Path, key: str) -> list[str]:
    """Tệp (đường dẫn tương đối) có chứa khoá. Rỗng ⇒ sạch."""
    return sorted(str(f.relative_to(thu_muc)).replace("\\", "/") for f in Path(thu_muc).rglob("*")
                  if f.is_file() and key in f.read_text(encoding="utf-8", errors="replace"))


def tat_log_url() -> None:
    for ten in ("httpx", "httpcore"):
        logging.getLogger(ten).setLevel(logging.WARNING)


def _token(rep: dict) -> int:
    """Tổng token của một usage_report: `max(total, vào + ra + suy luận)` — chặn trên khi provider bỏ trống `total`."""
    return sum(max(v.get("total_tokens", 0),
                   v.get("prompt_tokens", 0) + v.get("candidates_tokens", 0) + v.get("thoughts_tokens", 0))
               for v in rep.values())


def _so_luot(rep: dict) -> int:
    return sum(v.get("calls", 0) for v in rep.values())


class GacCong:
    """Bọc lượt gọi provider (`pipeline.call_gemini`): chặn trước, đếm sau, che lỗi."""

    def __init__(self, inner: Callable, caps: Caps, key: str | None, token_da_dung: int = 0) -> None:
        self.inner, self.caps, self.key = inner, caps, key
        self.token_da_dung = token_da_dung        # token của các đề đã xong
        self.goi = 0
        self.loi_lien_tiep = 0
        self.stop: str | None = None
        self.loi_ca: list[str] = []
        self.dung_ca: str | None = None

    def bat_dau_ca(self) -> None:
        self.loi_ca, self.dung_ca = [], None

    def _dung(self, ly_do: str) -> DungPilot:
        self.stop = self.stop or ly_do
        self.dung_ca = ly_do
        return DungPilot(ly_do)

    async def __call__(self, *a: Any, **k: Any) -> str:
        from app.ai import gemini, telemetry

        if self.stop:
            raise self._dung(self.stop)
        dang = self.token_da_dung + _token(telemetry.usage_report())
        if dang + TOKEN_RESERVE_PER_CALL > self.caps.tokens:
            raise self._dung(f"token: đã dùng {dang} + dự trữ {TOKEN_RESERVE_PER_CALL} > trần {self.caps.tokens}")
        truoc = _so_luot(telemetry.usage_report())
        self.goi += 1
        try:
            out = await self.inner(*a, **k)
        except gemini.BudgetExceeded as e:
            self.stop = self.stop or f"budget: {che(str(e), self.key)}"
            self.dung_ca = self.stop
            raise
        except DungPilot:
            raise
        except Exception as e:  # noqa: BLE001 — mọi lỗi provider: ghi (đã che) rồi ném tiếp, thông điệp đã che
            msg = che(f"{type(e).__name__}: {e}", self.key)
            self.loi_ca.append(msg)
            self.loi_lien_tiep += 1
            if self.loi_lien_tiep >= 2:
                self.stop = self.stop or "provider: hai lỗi provider liên tiếp"
            raise RuntimeError(msg) from None
        self.loi_lien_tiep = 0
        if _so_luot(telemetry.usage_report()) != truoc + 1:
            raise self._dung("usage: phản hồi provider không có usageMetadata — không xác định được ngân sách")
        return out


def _gia_tri_nhan_chung(fm: dict, hd: Any, kind: str = "volume") -> Any:
    """Giá trị máy của nghĩa vụ `kind` — tra qua witness HỢP ĐỒNG khai, không đoán tên biến."""
    ob = next((o for o in (hd.obligations if hd else []) if o.kind == kind), None)
    return fm.get(ob.witness) if ob and ob.witness else None


def _ghi_json(p: Path, d: Any, key: str | None) -> None:
    p.write_text(che(json.dumps(d, ensure_ascii=False, indent=1, default=str), key) + "\n", encoding="utf-8")


async def chay_pilot(cases: list[dict], out_dir: Path, inner: Callable, api_key: str, caps: Caps,
                     run_id: str, model: str = MODEL_APPROVED) -> dict:
    """Chạy (hoặc TIẾP TỤC) lượt pilot. `inner` = lượt gọi provider (`gemini.call_gemini` khi live, provider giả khi
    chứng nhận). Trả bản tóm tắt; ghi `SUMMARY.json`."""
    from app.ai import pipeline

    sys.path.insert(0, str(BACKEND / "scripts"))
    import api_usage_log as AU

    tat_log_url()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    M = _nap("measure_geometry_stability")
    M.RA, M.RUN_ID = out_dir, run_id
    M._ky_vong_cua = lambda _id: {"verification_obligations": [{"kind": "volume"}], "construction_obligations": []}
    bat: dict[str, Any] = {}

    def _oracle(expect: str, fm: dict, hd: Any):                  # mot_luot gọi; chỉ GHI LẠI để chấm ở sidecar
        bat.update(fm=fm, hd=hd)
        return None, "chấm ở {id}-lan1.pilot.json (g05_pilot_scoring)"

    M.cham_oracle = _oracle

    da_xong: dict[str, dict] = {}
    for c in cases:
        p = out_dir / f"{c['id']}-lan1.pilot.json"
        if p.exists():
            da_xong[c["id"]] = json.loads(p.read_text(encoding="utf-8"))
    dung = lambda f: sum(s.get(f, 0) or 0 for s in da_xong.values())  # noqa: E731
    gac = GacCong(inner, caps, api_key, token_da_dung=dung("token_total"))
    theo_hang: dict[str, str] = {}
    goc_call = pipeline.call_gemini
    try:
        for c in cases:
            if c["id"] in da_xong:
                theo_hang[c["id"]] = da_xong[c["id"]]["category"]
                continue
            if (out_dir / f"{c['id']}-lan1.json").exists():   # mot_luot ghi xong nhưng sidecar mất: KHÔNG chạy lại
                sc = {"case_id": c["id"], "category": "TOOL_ERROR", "detail": "sidecar thiếu — không chạy lại"}
                _ghi_json(out_dir / f"{c['id']}-lan1.pilot.json", sc, api_key)
                da_xong[c["id"]], theo_hang[c["id"]] = sc, "TOOL_ERROR"
                continue
            con_logic, con_http = caps.logical - dung("logical_calls"), caps.http - dung("http_attempts")
            if gac.stop or con_logic <= 0 or con_http <= 0:
                gac.stop = gac.stop or f"budget: còn {con_logic} lượt logic / {con_http} lần thử HTTP"
                theo_hang[c["id"]] = "NOT_RUN"
                continue
            M.TRAN_LOGIC, M.TRAN_HTTP = min(PER_CASE_LOGIC, con_logic), min(PER_CASE_HTTP, con_http)
            gac.bat_dau_ca()
            bat.clear()
            pipeline.call_gemini = gac
            try:
                bg = await M.mot_luot({"id": c["id"], "de": c["problem_text"], "oracle": c["expect"]}, 1, api_key)
            finally:
                pipeline.call_gemini = goc_call
            fm, hd = bat.get("fm") or {}, bat.get("hd")
            gia_tri = _gia_tri_nhan_chung(fm, hd)
            rec = {"envelope_status": bg.get("envelope_status"), "servable": bg.get("servable"),
                   "stage_reached": bg.get("stage_reached"), "error_code": bg.get("error_code"),
                   "su_co": bg.get("su_co"), "value": gia_tri, "provider_errors": list(gac.loi_ca),
                   "run_stop": gac.dung_ca}
            pl = SC.phan_loai(c["expect"], rec)
            tok = bg.get("token") or {}
            sc = {"case_id": c["id"], "expect": c["expect"], **pl, "value": None if gia_tri is None else str(gia_tri),
                  "envelope_status": rec["envelope_status"], "stage_reached": rec["stage_reached"],
                  "error_code": rec["error_code"], "su_co": rec["su_co"], "provider_errors": rec["provider_errors"],
                  "run_stop": rec["run_stop"], "logical_calls": bg.get("logical_calls", 0),
                  "http_attempts": bg.get("http_requests", 0), "retry_requests": bg.get("retry_requests", 0),
                  "program_attempts": bg.get("so_lan_thu_sinh"), "failed_attempts": bg.get("thu_that_bai"),
                  # lượt gọi CHẶNG SINH CHƯƠNG TRÌNH (1 = sinh một lần; 2–3 = có vòng sửa) — đếm từ usage, không từ sự kiện
                  "program_calls": (tok.get("semantic_program") or {}).get("calls", 0),
                  "tokens_by_stage": tok, "token_total": _token(tok), "co_scene3d": bg.get("co_scene3d")}
            _ghi_json(out_dir / f"{c['id']}-lan1.pilot.json", sc, api_key)
            da_xong[c["id"]], theo_hang[c["id"]] = sc, pl["category"]
            gac.token_da_dung = dung("token_total")
            if api_key and (lo := quet_khoa(out_dir, api_key)):
                gac.stop = f"leak: khoá xuất hiện trong {len(lo)} tệp"
    finally:
        pipeline.call_gemini = goc_call

    tong: dict[str, int] = {}
    for s in da_xong.values():
        for v in (s.get("tokens_by_stage") or {}).values():
            for k2, n in v.items():
                tong[k2] = tong.get(k2, 0) + n
    dem = {k: list(theo_hang.values()).count(k) for k in SC.CATEGORIES if k in theo_hang.values()}
    summary = {
        **MEASUREMENT, "run_id": run_id, "model": model, "corpus_sha256": CORPUS_SHA256, "caps": asdict(caps),
        "token_reserve_per_call": TOKEN_RESERVE_PER_CALL, "out_dir": str(out_dir), "theo_hang": theo_hang, "dem": dem,
        "chi_tiet": {k: {f: s.get(f) for f in ("category", "ground", "label_stage_match", "value", "stage_reached",
                                                "error_code", "program_calls", "logical_calls", "token_total")}
                     for k, s in da_xong.items()},
        "positives": sum(c["expect"].startswith("served:") for c in cases),
        "negatives": sum(not c["expect"].startswith("served:") for c in cases),
        "provider_calls": gac.goi, "logical_calls": dung("logical_calls"), "http_attempts": dung("http_attempts"),
        "retry_requests": dung("retry_requests"), "tokens": tong, "token_total": dung("token_total"),
        "cost_estimate": AU._tien(model, tong), "stop_reason": gac.stop,
    }
    _ghi_json(out_dir / "SUMMARY.json", summary, api_key)
    return summary


def _model_dang_dung() -> str:
    from app.ai import gemini

    return gemini.MODEL


def kiem_truoc_live(env: dict) -> dict:
    """Mọi điều kiện của lượt live, kiểm TRƯỚC lượt gọi đầu. Hỏng ⇒ `DungPilot`, 0 lượt gọi."""
    if env.get("ALLOW_LIVE_AI") != "1":
        raise DungPilot("thiếu ALLOW_LIVE_AI=1 trong tiến trình pilot")
    if not env.get("GEMINI_API_KEY"):
        raise DungPilot("thiếu GEMINI_API_KEY")
    if (m := _model_dang_dung()) != MODEL_APPROVED:
        raise DungPilot(f"model {m!r} ≠ model đã duyệt {MODEL_APPROVED!r}")
    sys.path.insert(0, str(BACKEND / "scripts"))
    import freeze_evaluation_candidate as F
    from app.main import CACHE_VERSION

    he, n = F.measured_system_hash()
    if he != CANDIDATE_EXPECTED:
        raise DungPilot(f"candidate {he[:16]}… ≠ {CANDIDATE_EXPECTED[:16]}…")
    if CACHE_VERSION != CACHE_VERSION_EXPECTED:
        raise DungPilot(f"CACHE_VERSION {CACHE_VERSION} ≠ {CACHE_VERSION_EXPECTED}")
    nap_corpus()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return {"model": MODEL_APPROVED, "candidate": he, "measured_files": n, "cache_version": CACHE_VERSION,
            "git_head": head, "corpus_sha256": CORPUS_SHA256, "caps": asdict(CAPS_APPROVED),
            "tools": "none (generateContent text + responseSchema only; no search grounding, maps, audio)"}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--live", action="store_true", help="TIÊU QUOTA THẬT — chỉ sau nghiệm thu độc lập PHASE B.")
    p.add_argument("--out-dir", required=True)
    a = p.parse_args()
    if not a.live:
        print("Không có --live: không làm gì. Chứng nhận 0 call: scripts/certify_g05_real_model_pilot.py")
        return 2
    try:
        from dotenv import dotenv_values

        env = {**{k: v for k, v in dotenv_values(BACKEND / ".env").items() if k == "GEMINI_API_KEY"}, **os.environ}
    except ImportError:
        env = dict(os.environ)
    key = env.get("GEMINI_API_KEY") or ""
    try:
        man = kiem_truoc_live(env)
    except DungPilot as e:
        print(f"DỪNG: {che(str(e), key)}", file=sys.stderr)
        return 2
    out = Path(a.out_dir)
    if (out / "MANIFEST.json").exists():
        old = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
        if {k: old.get(k) for k in ("candidate", "corpus_sha256", "model", "caps")} != \
                {k: man[k] for k in ("candidate", "corpus_sha256", "model", "caps")}:
            print("DỪNG: MANIFEST cũ khai hệ/corpus/model/trần khác — không tiếp tục lượt khác", file=sys.stderr)
            return 2
    else:
        out.mkdir(parents=True, exist_ok=True)
        _ghi_json(out / "MANIFEST.json", {**MEASUREMENT, **man,
                                           "written_before_first_call": datetime.now(timezone.utc).isoformat()}, key)
    from app.ai import gemini

    s = asyncio.run(chay_pilot(nap_corpus(), out, gemini.call_gemini, key, CAPS_APPROVED, run_id=out.name))
    print(che(json.dumps({k: s[k] for k in ("dem", "logical_calls", "http_attempts", "token_total", "stop_reason")},
                         ensure_ascii=False), key))
    return 0 if not s["stop_reason"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
