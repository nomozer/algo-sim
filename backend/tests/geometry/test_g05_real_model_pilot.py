"""G05 real-model pilot tooling (run `g05-real-model-pilot`) — 0 lượt gọi model.

Khoá: bộ chấm chính xác (G1), đường `run_pipeline` thật qua `mot_luot` (G2), phân loại kết cục (G3), dựng lại Scene3D
offline (G4), an toàn khoá (G5), ngân sách, usage, tiếp tục ≠ chạy lại. Provider GIẢ trả chương trình corpus viết tay.
"""
from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import logging
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.simulation.geometry.radical import radical

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "backend" / "scripts"
RUN = ROOT / "docs" / "evaluation" / "geometry" / "runs" / "g05-real-model-pilot"
KHOA_GIA = "FAKEKEY-PILOT-SENTINEL-7f3a9c"


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(f"_t_{ten}", SCRIPTS / f"{ten}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m                 # dataclass cần module đã đăng ký
    spec.loader.exec_module(m)
    return m


SC = _nap("g05_pilot_scoring")
R = _nap("run_g05_real_model_pilot")
C = _nap("certify_g05_real_model_pilot")
SR = _nap("g05_pilot_scene_replay")


# ── G1 · chấm chính xác ────────────────────────────────────────────────────
@pytest.mark.parametrize("may,nhan", [
    (radical(F(18), 3), "18√3"), (radical(F(3, 4), 3), "3√3/4"), (radical(F(1), 3), "√3"),
    (F(12), "12"), (12, "12"), (radical(F(3), 39), "3√39"), (radical(F(18), 2), "18√2"),
    (F(2, 3), "2/3"), ("18√3", "18√3"), ("6√12", "12√3"), (radical(F(18), 3), "√972"),
])
def test_bang_nhau_chinh_xac(may, nhan):
    assert SC.bang_nhau(may, nhan) is True


@pytest.mark.parametrize("may,nhan", [
    (radical(F(18), 3), "18√2"), (radical(F(18), 3), "18"), (radical(F(18), 3), "-18√3"),
    (radical(F(1), 3, 1), "√3"), (F(12), "12√1/2"), (radical(F(3, 4), 3), "3√3/2"), (F(31), "31"[:1]),
])
def test_khong_bang_nhau(may, nhan):
    assert SC.bang_nhau(may, nhan) is False


@pytest.mark.parametrize("may", [31.176914536239792, None, "abc", [1, 2]])
def test_gia_tri_khong_chinh_xac_khong_cham_duoc(may):
    assert SC.bang_nhau(may, "18√3") is None


def test_nhan_khong_hop_le_la_loi_cong_cu():
    with pytest.raises(ValueError):
        SC.gia_tri_nhan("18 can 3")


# ── G3 · phân loại kết cục ─────────────────────────────────────────────────
def _rec(**k):
    base = {"envelope_status": "ok", "servable": True, "stage_reached": "served", "error_code": None,
            "su_co": None, "value": radical(F(18), 3), "provider_errors": [], "run_stop": None}
    return {**base, **k}


@pytest.mark.parametrize("expect,rec,cat", [
    ("served:18√3", _rec(), "SERVED_CORRECT"),
    ("served:18√3", _rec(value=radical(F(9), 3)), "SERVED_WRONG"),
    ("served:18√3", _rec(value=None), "UNGRADABLE"),
    ("served:18√3", _rec(value=31.18), "UNGRADABLE"),
    ("served:18√3", _rec(envelope_status="unsupported", servable=False, stage_reached="assumption",
                         error_code="ASSUMPTION_DETERMINES_ANSWER", value=None), "REFUSED_WRONG"),
    ("refused", _rec(), "SERVED_WRONG"),
    ("refused", _rec(envelope_status="unsupported", servable=False, stage_reached="assumption", value=None),
     "REFUSED_CORRECT"),
    ("refused", _rec(envelope_status="unsupported", servable=False, stage_reached="semantic_analyze", value=None),
     "PARSER_SCHEMA_ERROR"),
    ("refused", _rec(envelope_status="unsupported", servable=False, stage_reached="semantic_program", value=None),
     "PARSER_SCHEMA_ERROR"),
    ("refused", _rec(envelope_status="EXCEPTION", servable=None, stage_reached=None, value=None,
                     su_co="RuntimeError: Gemini API lỗi HTTP 400", provider_errors=["HTTP 400"]), "PROVIDER_ERROR"),
    ("refused", _rec(envelope_status="unsupported", servable=False, stage_reached="assumption", value=None,
                     provider_errors=["timeout"]), "PROVIDER_ERROR"),
    ("refused", _rec(envelope_status="EXCEPTION", servable=None, stage_reached=None, value=None,
                     su_co="DungPilot: budget", run_stop="budget"), "RUN_STOPPED"),
    ("served:18√3", _rec(envelope_status="EXCEPTION", servable=None, stage_reached=None, value=None,
                         su_co="KeyError: 'x'"), "TOOL_ERROR"),
])
def test_phan_loai(expect, rec, cat):
    assert SC.phan_loai(expect, rec)["category"] == cat


def test_tu_choi_dung_ghi_khop_chang_nhan():
    r = SC.phan_loai("refused:assumption", _rec(envelope_status="unsupported", servable=False,
                                                 stage_reached="source_invariant", value=None))
    assert r["category"] == "REFUSED_CORRECT" and r["ground"] == "source_invariant"
    assert r["label_stage_match"] is False


# ── corpus đăng ký trước ───────────────────────────────────────────────────
def test_corpus_ghim_bam_va_chep_dung_nhan_nguon():
    p = RUN / "PILOT_CASES.json"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == R.CORPUS_SHA256
    cases = R.nap_corpus()
    assert len(cases) == 16 and sum(c["expect"].startswith("served:") for c in cases) == 10
    for c in cases:
        src = json.loads((RUN.parent / c["source"]["run"] / "labels.json").read_text(encoding="utf-8"))["rows"]
        hang = src[c["source"]["row"]]
        assert (c["problem_text"], c["expect"]) == (hang["text"], hang["expect"])


def test_oracle_cong_thuc_sach_khop_nhan_duong():
    """Độc lập với sản phẩm: V từ kích thước của đề (lăng trụ, chóp, tứ diện đều) = nhãn, so CHÍNH XÁC qua bình phương."""
    for c in R.nap_corpus():
        if c["expect"].startswith("served:"):
            assert SC.bang_nhau_binh_phuong(SC.v2_cong_thuc(c), c["expect"].split(":", 1)[1]), c["id"]


# ── G2 + G3 + G4 · chứng nhận 16 hàng với provider giả ────────────────────
@pytest.fixture(scope="module")
def chung_nhan(tmp_path_factory):
    return C.chung_nhan(tmp_path_factory.mktemp("cert"))


def test_chung_nhan_16_hang_dung_ky_vong(chung_nhan):
    kq = chung_nhan["pilot"]["summary"]["theo_hang"]
    assert {k for k, v in kq.items() if v == "SERVED_CORRECT"} == {"X1", "X4", "X6", "T2", "T5", "H1", "H2", "H8",
                                                                  "P09", "P06"}
    assert {k for k, v in kq.items() if v == "REFUSED_CORRECT"} == {"NX1", "NT2", "NT4", "NX7", "N8", "N02"}


def test_chung_nhan_di_duong_run_pipeline_va_dem_token(chung_nhan):
    s = chung_nhan["pilot"]["summary"]
    assert s["provider_calls"] == s["logical_calls"] >= 32          # analyze + program cho mỗi đề
    t = s["tokens"]
    n = s["provider_calls"]
    assert (t["prompt_tokens"], t["candidates_tokens"], t["thoughts_tokens"], t["cached_content_tokens"]) == (
        1000 * n, 200 * n, 300 * n, 50 * n)
    assert s["cost_estimate"]["uoc_tinh_duoc"] is True
    assert {v["program_calls"] for v in s["chi_tiet"].values()} == {1}    # mô hình hoàn hảo: sinh đúng một lần


def test_chung_nhan_scene_replay_offline(chung_nhan):
    sc = chung_nhan["scene_replay"]
    assert sc["checked"] == 10 and sc["ok"] == 10


def test_chung_nhan_tiem_loi(chung_nhan):
    t = chung_nhan["fault_injection"]
    assert t["provider_error_on_negative"] == "PROVIDER_ERROR"
    assert t["schema_invalid_on_negative"] == "PARSER_SCHEMA_ERROR"
    assert t["resume_provider_calls"] == 0
    assert t["leak_in_artifacts"] is False


# ── ngân sách, usage, lỗi provider liên tiếp, khoá ────────────────────────
def _hai_bai():
    return [c for c in R.nap_corpus() if c["id"] in ("X1", "T2")]


def _chay(tmp, cases, caps, **fake_kw):
    fake = C.ProviderGia(C.dap_an_corpus(cases), **fake_kw)
    return asyncio.run(R.chay_pilot(cases, tmp, fake, KHOA_GIA, caps, run_id="test")), fake


def test_tran_luot_logic_khong_bi_vuot(tmp_path):
    s, fake = _chay(tmp_path, _hai_bai(), R.Caps(logical=3, http=96, tokens=400_000))
    assert fake.goi <= 3 and s["logical_calls"] <= 3
    assert s["theo_hang"]["T2"] == "RUN_STOPPED" and s["stop_reason"]


def test_tran_lan_thu_http_khong_bi_vuot(tmp_path):
    s, fake = _chay(tmp_path, _hai_bai(), R.Caps(logical=64, http=2, tokens=400_000))
    assert s["http_attempts"] <= 2 and s["stop_reason"]


def test_tran_token_chan_truoc_luot_goi(tmp_path):
    # lượt 1 dùng 1500 token ⇒ lượt 2: 1500 + dự trữ > dự trữ + 1000 ⇒ chặn TRƯỚC khi gọi
    s, fake = _chay(tmp_path, _hai_bai(), R.Caps(logical=64, http=96, tokens=R.TOKEN_RESERVE_PER_CALL + 1000))
    assert fake.goi == 1 and s["stop_reason"].startswith("token")


def test_usage_thieu_thi_dung(tmp_path):
    s, fake = _chay(tmp_path, _hai_bai(), R.CAPS_APPROVED, usage=None)
    assert fake.goi == 1 and s["stop_reason"].startswith("usage")


def test_hai_loi_provider_lien_tiep_thi_dung_va_khong_tinh_la_tu_choi(tmp_path):
    s, fake = _chay(tmp_path, _hai_bai(), R.CAPS_APPROVED, loi_moi_luot=True)
    assert s["theo_hang"]["X1"] == "PROVIDER_ERROR" and fake.goi == 2
    assert s["stop_reason"].startswith("provider")
    assert "REFUSED_CORRECT" not in s["theo_hang"].values()


def test_khoa_khong_lot_vao_artifact_va_log_httpx_tat(tmp_path):
    s, _ = _chay(tmp_path, _hai_bai(), R.CAPS_APPROVED, loi_moi_luot=True, chen_khoa=KHOA_GIA)
    for f in tmp_path.rglob("*"):
        if f.is_file():
            assert KHOA_GIA not in f.read_text(encoding="utf-8", errors="replace"), f.name
    assert logging.getLogger("httpx").level >= logging.WARNING
    assert logging.getLogger("httpcore").level >= logging.WARNING


def test_quet_khoa_bat_duoc_khoa_bi_cai(tmp_path):
    (tmp_path / "x.json").write_text(f'{{"url": "...?key={KHOA_GIA}"}}', encoding="utf-8")
    assert R.quet_khoa(tmp_path, KHOA_GIA) == ["x.json"]


def test_tiep_tuc_khong_goi_lai_bai_da_xong(tmp_path):
    cases = _hai_bai()
    s1, f1 = _chay(tmp_path, cases, R.CAPS_APPROVED)
    s2, f2 = _chay(tmp_path, cases, R.CAPS_APPROVED)
    assert f1.goi == 4 and f2.goi == 0
    assert s2["theo_hang"] == s1["theo_hang"] and s2["logical_calls"] == s1["logical_calls"]


# ── cổng live ──────────────────────────────────────────────────────────────
def test_live_tu_choi_khi_thieu_allow_live_ai(monkeypatch):
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    with pytest.raises(R.DungPilot, match="ALLOW_LIVE_AI"):
        R.kiem_truoc_live({"GEMINI_API_KEY": KHOA_GIA})


def test_live_tu_choi_model_khac(monkeypatch):
    monkeypatch.setattr(R, "_model_dang_dung", lambda: "gemini-2.5-pro")
    with pytest.raises(R.DungPilot, match="model"):
        R.kiem_truoc_live({"ALLOW_LIVE_AI": "1", "GEMINI_API_KEY": KHOA_GIA})


def test_tran_da_duyet_dung_so_nguoi_dung_duyet():
    assert (R.CAPS_APPROVED.logical, R.CAPS_APPROVED.http, R.CAPS_APPROVED.tokens) == (64, 96, 400_000)
    assert R.MODEL_APPROVED == "gemini-2.5-flash"


# ── G4 · dựng lại cảnh: kiểm bắt được hình sai ─────────────────────────────
def test_scene_replay_bat_duoc_kich_thuoc_sai(chung_nhan):
    d = Path(chung_nhan["pilot"]["out_dir"])
    x1 = next(c for c in R.nap_corpus() if c["id"] == "X1")
    sai = {**x1, "base_side": "3"}
    assert SR.kiem_mot(d, x1)["ok"] is True
    assert SR.kiem_mot(d, sai)["ok"] is False
