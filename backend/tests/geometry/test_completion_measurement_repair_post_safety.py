"""COMPLETION_MEASUREMENT_REPAIR_OFFLINE_POST_SAFETY — ba lỗ đo đã chặn lượt live trước.

R1 · ràng buộc trước request đầu phải đủ 17 trường, được kiểm fail closed, ghi nguyên tử.
R2 · mọi trạng thái có giá trị ghi BỀN theo từng ca — request đã trả tiền không bao giờ mất.
R3 · lỗi ở tầng chấm tạo bản ghi `MEASUREMENT_ERROR` an toàn rồi dừng, không làm chết tiến trình.

Mọi test đi qua `main()` THẬT với transport giả ở biên (xem `test_completion_runner_repair`).
0 request mạng · không nạp `.env` · không có khoá thật.
"""
from __future__ import annotations

import ast
import json
import os
import re
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

GOC = Path(__file__).resolve().parents[2]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts"), str(Path(__file__).parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_multicase_benchmark as B  # noqa: E402
import test_completion_runner_repair as TR  # noqa: E402

#: Mười bảy trường bắt buộc — viết CỨNG theo đặc tả, không đọc từ runner.
TRUONG_17 = ["repository_identity", "branch", "execution_head", "cache_version", "manifest_sha256",
             "ground_truth_sha256", "registry_v1_sha256", "registry_v2_sha256", "candidate_sha256",
             "runner_sha256", "aggregator_sha256", "model", "prompt_sha256", "schema_sha256",
             "case_order", "request_budget", "created_at_utc"]
SHA_V1 = "52bc6379d2f01372513d5aa21bd25433ea27783edae416cc7a1ed95fa8bb7100"
SHA_V2 = "03a87ba37a6df62604d33119f346101e1f9e6f10f8db63b6fdbff6ce40c07e81"
SHA_MANIFEST = "e043903849ebd5799ac87e788bacea95e31277cbc528cff21060ff873e29b60a"
SHA_GT = "115c0518a1997fa719500415d876a0a864a7fcb695170e88369e9ba9177793af"
SHA_CANDIDATE = "077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1"
GIO = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)
BI_MAT_NGOAI_LE = "NOI_DUNG_NGOAI_LE_KHONG_DUOC_GHI_7f3a"


@pytest.fixture
def dong_ho(monkeypatch):
    monkeypatch.setattr(B, "dong_ho", lambda: GIO, raising=False)


def _head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
                          text=True).stdout.strip()


def _ca(ra: Path) -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((ra / "cases").glob("*.json"))}


def _moi_json_doc_duoc(ra: Path) -> list[str]:
    tep = sorted(p for p in ra.rglob("*.json"))
    for p in tep:
        json.loads(p.read_text(encoding="utf-8"))           # nửa JSON ⇒ ValueError
    return [p.relative_to(ra).as_posix() for p in tep]


def _toan_bo_van_ban(ra: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in ra.rglob("*") if p.is_file())


def _khong_co_dau_ra_tho(van: str) -> bool:
    """Dấu vết CHỈ đầu ra thô mới có: khoá `input_facts` và câu chữ nhãn dữ kiện của payload.
    (`source_fact_id` như `cao_vuong` là con trỏ mà bản ghi chấm ĐƯỢC giữ — không phải dấu vết.)"""
    return '"input_facts"' not in van and "vuông góc mặt phẳng" not in van


def _dang_ky() -> dict[str, str]:
    return {e["case_id"]: e["body_sha256"] for e in TR._doc(TR.REGD, "EXPECTED_REQUEST_HASHES.json")["EXPECTED"]}


def _chet(*_a, **_k):
    raise TR.SapNguon()


# ══ §2 · CỔNG: KHÔNG MẠNG, KHÔNG KHOÁ, KHÔNG .env ═════════════════════════
def test_cong_transport_that_bi_chan_o_bien():
    with pytest.raises(RuntimeError):                      # conftest: transport httpx thật bị chặn
        httpx.get("https://generativelanguage.googleapis.com/")
    with TR.ChanMangThat() as chan:                        # socket ngoài loopback bị chặn (IP, không DNS)
        s = socket.socket()
        try:
            with pytest.raises(RuntimeError):
                s.connect(("203.0.113.7", 443))
        finally:
            s.close()
    assert chan.attempts == ["socket:203.0.113.7"]


def test_cong_khoa_khong_co_trong_moi_truong_test():
    assert "GEMINI_API_KEY" not in os.environ
    assert os.environ.get("ALLOW_LIVE_AI") != "1"


def test_cong_runner_bo_tong_hop_va_module_test_khong_nap_duong_dotenv():
    ma = ("import sys; sys.path[:0] = ['.', 'scripts', 'tests/geometry'];"
          "import run_multicase_benchmark, aggregate_multicase_completion;"
          "print(sorted(m for m in ('app.persistence.db', 'dotenv', 'app.main') if m in sys.modules))")
    env = {k: v for k, v in os.environ.items() if k not in ("GEMINI_API_KEY", "ALLOW_LIVE_AI")}
    r = subprocess.run([sys.executable, "-c", ma], cwd=GOC, capture_output=True, text=True, env=env)
    assert r.returncode == 0 and r.stdout.strip() == "[]", r.stdout + r.stderr[-400:]
    cay = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    nhap = {n.module for n in ast.walk(cay) if isinstance(n, ast.ImportFrom) and n.module} | {
        a.name for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names}
    assert not {m for m in nhap if m and (m.startswith("dotenv") or m in ("app.main", "app.persistence.db"))}


def test_cong_luot_main_khong_phat_sinh_DNS_hay_socket_ngoai(tmp_path, monkeypatch, dong_ho):
    goi: list[str] = []
    that_connect = socket.socket.connect

    def dns(host, *a, **k):
        goi.append(f"dns:{host}")
        raise OSError("DNS bị chặn trong test")

    def connect(sock, address, *a, **k):
        host = address[0] if isinstance(address, tuple) else address
        if host not in ("127.0.0.1", "::1", "localhost"):
            goi.append(f"socket:{host}")
            raise OSError("socket ngoài bị chặn trong test")
        return that_connect(sock, address, *a, **k)
    monkeypatch.setattr(socket, "getaddrinfo", dns)
    monkeypatch.setattr(socket.socket, "connect", connect)
    _, thay = TR._chay_main(tmp_path, lambda req, cid: TR._tra_loi("{}"))
    assert thay == TR.CON_LAI and goi == []


# ══ R1 · RÀNG BUỘC ĐỦ 17 TRƯỜNG, TRƯỚC TRANSPORT ═══════════════════════════
def test_R1_A_rang_buoc_du_17_truong_ghi_TRUOC_request_dau_va_nap_lai_hop_le(tmp_path, dong_ho):
    luc_dau: list = []

    def xu_ly(req, cid):
        if not luc_dau:
            p = tmp_path / "REGISTRY_BINDING.json"
            luc_dau.append(json.loads(p.read_text(encoding="utf-8")) if p.exists() else None)
        return TR._tra_loi("{}")
    _, thay = TR._chay_main(tmp_path, xu_ly)
    assert thay == TR.CON_LAI
    b = luc_dau[0]
    assert b is not None, "ràng buộc chưa có khi request đầu rời tiến trình"
    assert [t for t in TRUONG_17 if t not in b] == []
    assert b["branch"] == "feat/photo-problem-to-scene" and b["execution_head"] == _head()
    assert b["cache_version"] == "99" and b["request_budget"] == 6 and b["model"] == "gemini-2.5-flash"
    assert b["case_order"] == TR.CON_LAI and b["created_at_utc"] == "2026-09-21T12:00:00Z"
    assert (b["registry_v1_sha256"], b["registry_v2_sha256"], b["manifest_sha256"], b["ground_truth_sha256"],
            b["candidate_sha256"]) == (SHA_V1, SHA_V2, SHA_MANIFEST, SHA_GT, SHA_CANDIDATE)
    assert b["runner_sha256"] == TR._sha_lf(Path(B.__file__))
    assert b["aggregator_sha256"] == TR._sha_lf(GOC / "scripts" / "aggregate_multicase_completion.py")
    dk = TR._doc(TR.REGD, "EXPECTED_REQUEST_HASHES.json")["EXPECTED"]
    assert b["prompt_sha256"] == dk[0]["system_prompt_sha256"]
    assert b["schema_sha256"] == dk[0]["response_schema_sha256"]
    with TR._boi_canh_lich_su():
        B.kiem_rang_buoc_day_du(TR._doc(tmp_path, "REGISTRY_BINDING.json"))      # nạp lại ⇒ vẫn hợp lệ


def test_R1_A_tuan_tu_hoa_tat_dinh_voi_dong_ho_co_dinh(tmp_path, dong_ho):
    for d in ("mot", "hai"):
        TR._chay_main(tmp_path / d, lambda req, cid: TR._tra_loi("{}"))
    a, b = ((tmp_path / d / "REGISTRY_BINDING.json").read_bytes() for d in ("mot", "hai"))
    assert a == b and b"2026-09-21T12:00:00Z" in a


def _chay_voi_rang_buoc_sua(tmp_path, monkeypatch, sua) -> tuple:
    goc = B.dung_rang_buoc

    def gia(*a, **k):
        b = goc(*a, **k)
        sua(b)
        return b
    monkeypatch.setattr(B, "dung_rang_buoc", gia)
    return TR._chay_main(tmp_path, lambda req, cid: TR._tra_loi("{}"))


@pytest.mark.parametrize("truong", TRUONG_17)
def test_R1_B_thieu_bat_ky_truong_bat_buoc_nao_thi_chan_truoc_transport(tmp_path, monkeypatch, dong_ho, truong):
    ma, thay = _chay_voi_rang_buoc_sua(tmp_path, monkeypatch, lambda b: b.pop(truong))
    assert thay == [] and ma == B.EXIT_PRECHECK
    assert TR._doc(tmp_path, "PRECHECK_REGISTRY_BINDING.json")["RESULT"] == f"BINDING_FIELD_MISSING:{truong}"
    assert not (tmp_path / "REGISTRY_BINDING.json").exists()


SAI = [
    ("manifest_sha256", "0" * 64, "BINDING_DATASET_HASH_MISMATCH"),
    ("ground_truth_sha256", "0" * 64, "BINDING_DATASET_HASH_MISMATCH"),
    ("registry_v1_sha256", "0" * 64, "BINDING_REGISTRY_DRIFT"),
    ("registry_v2_sha256", "0" * 64, "BINDING_REGISTRY_DRIFT"),
    ("candidate_sha256", "0" * 64, "BINDING_CANDIDATE_DRIFT"),
    ("runner_sha256", "0" * 64, "BINDING_RUNNER_DRIFT"),
    ("aggregator_sha256", "0" * 64, "BINDING_AGGREGATOR_DRIFT"),
    ("prompt_sha256", "0" * 64, "BINDING_PROMPT_MISMATCH"),
    ("schema_sha256", "0" * 64, "BINDING_SCHEMA_MISMATCH"),
    ("execution_head", "0" * 40, "BINDING_HEAD_MISMATCH"),
    ("branch", "main", "BINDING_BRANCH_MISMATCH"),
    ("repository_identity", "git-root:" + "0" * 40, "BINDING_REPOSITORY_MISMATCH"),
    ("cache_version", "100", "BINDING_CACHE_VERSION_MISMATCH"),
    ("model", "gemini-2.5-pro", "BINDING_MODEL_MISMATCH"),
    ("case_order", ["P07", "P06", "P08", "N02", "N03", "N04"], "BINDING_CASE_ORDER_MISMATCH"),
    ("request_budget", 7, "BINDING_BUDGET_MISMATCH"),
    ("request_budget", "6", "BINDING_FIELD_TYPE:request_budget"),
    ("created_at_utc", "hôm qua", "BINDING_TIMESTAMP_INVALID"),
]


@pytest.mark.parametrize("truong,gia_tri,ma", SAI, ids=[f"{t}-{m}" for t, _, m in SAI])
def test_R1_B_truong_co_mat_nhung_sai_gia_tri_thi_chan(tmp_path, monkeypatch, dong_ho, truong, gia_tri, ma):
    ma_ra, thay = _chay_voi_rang_buoc_sua(tmp_path, monkeypatch, lambda b: b.update({truong: gia_tri}))
    assert thay == [] and ma_ra == B.EXIT_PRECHECK
    assert TR._doc(tmp_path, "PRECHECK_REGISTRY_BINDING.json")["RESULT"] == ma


@pytest.mark.parametrize("ca", ["nhanh_khac", "runner_troi_sau_khi_nap", "bo_tong_hop_khac_ban_commit"])
def test_R1_B_troi_THAT_chan_truoc_transport(tmp_path, monkeypatch, dong_ho, ca):
    if ca == "nhanh_khac":
        monkeypatch.setitem(B.DANG_KY, "branch", "nhanh-khong-ton-tai")
        ma = "BINDING_BRANCH_MISMATCH"
    elif ca == "runner_troi_sau_khi_nap":
        monkeypatch.setattr(B, "_BAM_RUNNER_KHI_NAP", "0" * 64)
        ma = "BINDING_RUNNER_DRIFT"
    else:
        goc = B._bam_da_commit
        monkeypatch.setattr(B, "_bam_da_commit", lambda head, rel: "0" * 64
                            if rel.endswith("aggregate_multicase_completion.py") else goc(head, rel))
        ma = "BINDING_AGGREGATOR_DRIFT"
    ma_ra, thay = TR._chay_main(tmp_path, lambda req, cid: TR._tra_loi("{}"))
    assert thay == [] and ma_ra == B.EXIT_PRECHECK
    assert TR._doc(tmp_path, "PRECHECK_REGISTRY_BINDING.json")["RESULT"] == ma


# ══ R2 · BỀN VỮNG THEO TỪNG CA ═════════════════════════════════════════════
def test_R2_truoc_transport_dat_cho_va_ngan_sach_DA_BEN_tren_dia(tmp_path, dong_ho):
    tren_dia: dict = {}

    def xu_ly(req, cid):
        c = json.loads((tmp_path / "cases" / f"{cid}.json").read_text(encoding="utf-8"))
        bp = json.loads((tmp_path / "REQUEST_BUDGET_PROOF.json").read_text(encoding="utf-8"))
        tren_dia[cid] = (c["STATE"], c["REQUEST"]["observed_body_sha256"], bp["RESERVED_TOTAL"])
        return TR._tra_loi("{}")
    TR._chay_main(tmp_path, xu_ly)
    ky = _dang_ky()
    assert tren_dia == {cid: ("RESERVED", ky[cid], i + 1) for i, cid in enumerate(TR.CON_LAI)}


def test_R2_C_chet_o_P07_P06_van_du_bang_chung(tmp_path, dong_ho):
    with pytest.raises(TR.SapNguon):
        TR._chay_main(tmp_path, TR._p06_dung_roi(_chet))
    ca = _ca(tmp_path)
    assert set(ca) == {"P06", "P07"}, "P08–N04 không được bắt đầu"
    p06 = ca["P06"]
    assert p06["STATE"] == "SCORED" and p06["RESULT"]["OUTCOME"] == "FULL_PIPELINE_PASS"
    assert p06["RESULT"]["USAGE"]["totalTokenCount"] == 21 and p06["RESULT"]["LATENCY_MS"] is not None
    assert p06["TRANSPORT"]["http_status"] == 200 and p06["TRANSPORT"]["usage"]["totalTokenCount"] == 21
    assert ca["P07"]["STATE"] == "RESERVED" and "TRANSPORT" not in ca["P07"]
    idx = TR._doc(tmp_path, "COMPLETION_INDEX.json")
    assert idx["CASES"] == {"P06": "SCORED", "P07": "RESERVED"} and idx["RESERVED_TOTAL"] == 2
    assert [o["case_id"] for o in TR._doc(tmp_path, "REQUEST_OBSERVATIONS.json")["OBSERVATIONS"]] == ["P06", "P07"]
    bp = TR._doc(tmp_path, "REQUEST_BUDGET_PROOF.json")
    assert bp["RESERVED_TOTAL"] == 2 and bp["MAX_HTTP_REQUESTS"] == 6
    assert [r["CASE_ID"] for r in TR._doc(tmp_path, "COMPLETION_CASE_RESULTS_REDACTED.json")["CASES"]] == ["P06"]
    _moi_json_doc_duoc(tmp_path)
    assert not list(tmp_path.rglob("*.tmp"))
    assert _khong_co_dau_ra_tho(_toan_bo_van_ban(tmp_path)), "đầu ra thô của mô hình lọt vào artifact"


def test_R2_E_loi_provider_ghi_ngay_khong_retry_token_UNKNOWN(tmp_path, dong_ho):
    def to(req, cid):
        raise httpx.ReadTimeout("timeout giả lập", request=req)
    ma, thay = TR._chay_main(tmp_path, to)
    assert thay == ["P06"] and ma == B.EXIT_FAIL
    p06 = _ca(tmp_path)["P06"]
    assert p06["STATE"] == "PROVIDER_ERROR"
    assert p06["TRANSPORT"]["provider_error_class"] == "ReadTimeout" and p06["TRANSPORT"]["http_status"] is None
    assert p06["TRANSPORT"]["usage"] == "UNKNOWN" and p06["ANALYZE"]["usage"] == "UNKNOWN"
    assert p06["RESULT"]["HTTP_REQUESTS_FOR_CASE"] == 1
    assert not any(v == 0 for v in (p06["RESULT"].get("USAGE") or {}).values())
    assert TR._doc(tmp_path, "REQUEST_BUDGET_PROOF.json")["RESERVED_TOTAL"] == 1
    assert TR._doc(tmp_path, "COMPLETION_CASE_RESULTS_REDACTED.json")["STOP_REASON"] == "PROVIDER_ERROR"
    assert TR._doc(tmp_path, "AGGREGATE_12_CASE_RESULTS.json")["TOKENS"]["COMPLETION"]["UNKNOWN_USAGE_COUNT"] == 1


def test_R2_F_RESERVED_khong_bao_gio_tu_gui_lai(tmp_path, dong_ho):
    with pytest.raises(TR.SapNguon):
        TR._chay_main(tmp_path, TR._p06_dung_roi(_chet))
    ma, thay = TR._chay_main(tmp_path, lambda req, cid: TR._tra_loi("{}"))      # khởi động lại
    assert thay == [] and ma == B.EXIT_FAIL
    ca = _ca(tmp_path)
    assert ca["P06"]["STATE"] == "SCORED"
    assert ca["P07"]["STATE"] == "TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH"
    assert TR._doc(tmp_path, "COMPLETION_INDEX.json")["RESERVED_TOTAL"] == 2       # không hoàn ngân sách
    kq = TR._doc(tmp_path, "COMPLETION_CASE_RESULTS_REDACTED.json")
    assert kq["STOP_REASON"] == "TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH"
    p07 = next(r for r in kq["CASES"] if r["CASE_ID"] == "P07")
    assert p07["OUTCOME"] == "TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH" and p07["HTTP_REQUESTS_FOR_CASE"] == 1
    assert TR._doc(tmp_path, "AGGREGATE_12_CASE_RESULTS.json")["CLASSIFICATION"] == "MEASUREMENT_INVALID"


def test_R2_G_chet_sau_ket_cuc_transport_truoc_khi_cham(tmp_path, monkeypatch, dong_ho):
    goc = B.chay_tang_dung
    monkeypatch.setattr(B, "chay_tang_dung", _chet)
    with pytest.raises(TR.SapNguon):
        TR._chay_main(tmp_path, TR._p06_dung_roi(lambda req: TR._tra_loi("{}")))
    p06 = _ca(tmp_path)["P06"]
    assert p06["STATE"] == "TRANSPORT_COMPLETED" and p06.get("RESULT") is None
    assert p06["TRANSPORT"]["usage"]["totalTokenCount"] == 21 and p06["ANALYZE"]["MODEL_OUTPUT_RECEIVED"] is True
    monkeypatch.setattr(B, "chay_tang_dung", goc)
    ma, thay = TR._chay_main(tmp_path, lambda req, cid: TR._tra_loi("{}"))
    assert thay == [] and ma == B.EXIT_FAIL
    p06 = _ca(tmp_path)["P06"]
    assert p06["STATE"] == "MEASUREMENT_ERROR"
    assert p06["RESULT"]["MEASUREMENT_ERROR_CODE"] == "SCORING_NOT_COMPLETED_AFTER_CRASH"
    assert p06["RESULT"]["USAGE"]["totalTokenCount"] == 21
    assert TR._doc(tmp_path, "COMPLETION_INDEX.json")["RESERVED_TOTAL"] == 1
    assert _khong_co_dau_ra_tho(_toan_bo_van_ban(tmp_path))


def test_R2_noi_lai_sau_ca_SCORED_khong_gui_lai_ca_da_cham(tmp_path, monkeypatch, dong_ho):
    goc = B.NhatKyHoanTat.bat_dau

    def chet_truoc_P07(self, cid, *a, **k):
        if cid == "P07":
            raise TR.SapNguon()
        return goc(self, cid, *a, **k)
    monkeypatch.setattr(B.NhatKyHoanTat, "bat_dau", chet_truoc_P07)
    with pytest.raises(TR.SapNguon):
        TR._chay_main(tmp_path, TR._p06_dung_roi(lambda req: TR._tra_loi("{}")))
    monkeypatch.setattr(B.NhatKyHoanTat, "bat_dau", goc)
    truoc = (tmp_path / "cases" / "P06.json").read_bytes()
    _, thay = TR._chay_main(tmp_path, lambda req, cid: TR._tra_loi("{}"))
    assert thay == ["P07", "P08", "N02", "N03", "N04"]
    assert (tmp_path / "cases" / "P06.json").read_bytes() == truoc
    assert TR._doc(tmp_path, "COMPLETION_INDEX.json")["RESERVED_TOTAL"] == 6
    assert [r["CASE_ID"] for r in TR._doc(tmp_path, "COMPLETION_CASE_RESULTS_REDACTED.json")["CASES"]] == TR.CON_LAI


def test_R2_H_ghi_nguyen_tu_loi_truoc_replace_giu_nguyen_ban_cu(tmp_path, monkeypatch):
    dich = tmp_path / "X.json"
    B.ghi_json_nguyen_tu(dich, {"v": 1})

    def hong(*_a, **_k):
        raise OSError("đĩa đầy giả lập")
    monkeypatch.setattr(B.os, "replace", hong)
    with pytest.raises(OSError):
        B.ghi_json_nguyen_tu(dich, {"v": 2})
    monkeypatch.undo()
    assert json.loads(dich.read_text(encoding="utf-8")) == {"v": 1}
    assert not list(tmp_path.glob("*.tmp"))


def test_R2_H_tep_tam_sot_lai_sau_khi_chet_duoc_don_o_luot_sau(tmp_path, dong_ho):
    with pytest.raises(TR.SapNguon):
        TR._chay_main(tmp_path, TR._p06_dung_roi(_chet))
    (tmp_path / "cases" / "P06.json.tmp").write_text('{"CASE_ID": "P0', encoding="utf-8")
    TR._chay_main(tmp_path, lambda req, cid: TR._tra_loi("{}"))
    assert not list(tmp_path.rglob("*.tmp"))
    assert TR._doc(tmp_path, "COMPLETION_INDEX.json")["TMP_FILES_CLEANED"] == ["cases/P06.json.tmp"]
    assert _ca(tmp_path)["P06"]["STATE"] == "SCORED"
    _moi_json_doc_duoc(tmp_path)


# ══ R3 · LỖI Ở TẦNG CHẤM ════════════════════════════════════════════════════
def test_R3_D_loi_cham_o_P06_thanh_MEASUREMENT_ERROR_giu_du_bang_chung(tmp_path, monkeypatch, dong_ho):
    def hong(*_a, **_k):
        raise RuntimeError(BI_MAT_NGOAI_LE)
    monkeypatch.setattr(B, "chay_tang_dung", hong)
    ma, thay = TR._chay_main(tmp_path, TR._p06_dung_roi(lambda req: TR._tra_loi("{}")))
    assert thay == ["P06"] and ma == B.EXIT_FAIL
    p06 = _ca(tmp_path)["P06"]
    assert p06["STATE"] == "MEASUREMENT_ERROR"
    r = p06["RESULT"]
    assert r["OUTCOME"] == "MEASUREMENT_ERROR" and r["MEASUREMENT_ERROR_CODE"] == "SCORING_EXCEPTION:RuntimeError"
    assert r["USAGE"]["totalTokenCount"] == 21 and r["LATENCY_MS"] is not None
    assert r["HTTP_STATUS"] == 200 and r["MODEL_OUTPUT_RECEIVED"] is True and r["HTTP_REQUESTS_FOR_CASE"] == 1
    assert "RELATION" not in r and "BUILD" not in r, "bản ghi chấm dở không được giữ"
    assert p06["TRANSPORT"]["http_status"] == 200
    assert TR._doc(tmp_path, "REQUEST_BUDGET_PROOF.json")["RESERVED_TOTAL"] == 1
    assert [o["case_id"] for o in TR._doc(tmp_path, "REQUEST_OBSERVATIONS.json")["OBSERVATIONS"]] == ["P06"]
    assert TR._doc(tmp_path, "COMPLETION_CASE_RESULTS_REDACTED.json")["STOP_REASON"] == "MEASUREMENT_ERROR"
    agg = TR._doc(tmp_path, "AGGREGATE_12_CASE_RESULTS.json")
    assert agg["CLASSIFICATION"] == "MEASUREMENT_INVALID"
    assert "MEASUREMENT_ERROR_IN_COMPLETION" in agg["MEASUREMENT_INVALID_REASONS"]
    van = _toan_bo_van_ban(tmp_path)
    assert BI_MAT_NGOAI_LE not in van and "Traceback" not in van and _khong_co_dau_ra_tho(van)


def test_R3_ma_loi_cham_la_tu_vung_dong():
    import aggregate_multicase_completion as TH
    assert B.ma_loi_cham(KeyError("x")) == "SCORING_EXCEPTION:KeyError"
    assert B.ma_loi_cham(TH.LoiRegistry("REGISTRY_V2_MISSING", "chi tiết")) == "SCORING_REGISTRY:REGISTRY_V2_MISSING"

    class LoiLa(Exception):
        pass
    assert B.ma_loi_cham(LoiLa(BI_MAT_NGOAI_LE)) == "SCORING_EXCEPTION:UNLISTED"
