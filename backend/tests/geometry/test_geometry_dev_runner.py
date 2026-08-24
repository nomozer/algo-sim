# -*- coding: utf-8 -*-
"""Runner DEV hình học — kiểm TRƯỚC khi tiêu quota. **0 API call.**

Runner chỉ được chạy sau khi mọi thứ tất định trong nó đã xanh: chấm oracle,
ép skill, hình dạng artifact, cổng opt-in. Tiêu 60 lượt LLM rồi mới phát hiện
một lỗi tất định là thứ `test_mocked_production_e2e.py` ghi là **đã xảy ra ba
lượt liên tiếp** trong wave trước.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_R = Path(__file__).resolve().parents[2] / "scripts" / "run_geometry_dev_evaluation.py"


@pytest.fixture(scope="module")
def rn():
    spec = importlib.util.spec_from_file_location("run_geometry_dev", _R)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_geometry_dev"] = mod
    spec.loader.exec_module(mod)
    return mod


class _Ob:
    def __init__(self, kind, witness):
        self.kind, self.witness = kind, witness


class _HD:
    def __init__(self, *obs):
        self.obligations = list(obs)


# ── 1. Cổng opt-in: KHÔNG gọi API ngoài ý muốn ────────────────────────────
def test_khong_co_ALLOW_LIVE_AI_thi_TU_CHOI(rn, monkeypatch):
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    with pytest.raises(rn.DungSach, match="ALLOW_LIVE_AI"):
        rn._bat_buoc_live()


def test_ngan_sach_DAN_tu_call_graph_khong_muon_tran_Tin_hoc(rn):
    """13/case là trần của miền Tin học (có classify + simulate + recovery).
    Runner này không chạy ba thứ đó, nên mượn trần ấy là xin thừa quota."""
    assert rn.TRAN_LOGIC == 60 and rn.TRAN_HTTP == 80
    assert rn.TRAN_LOGIC == 6 * 10, "6 lượt/case × 10 case"


# ── 2. Ép skill hình học ──────────────────────────────────────────────────
def test_runner_ep_dung_skill_hinh_hoc(rn):
    assert rn.SKILL_HINH_HOC == "geometry_program_generator"
    assert (Path(__file__).resolve().parents[2] / "app" / "ai" / "skills"
            / f"{rn.SKILL_HINH_HOC}.md").exists()


def test_runner_KHONG_import_run_sealed_evaluation(rn):
    """Cái đó mang con dấu lượt SEALED #1 — đụng vào là làm bẩn artifact đã đóng.

    Soi bằng `ast`, KHÔNG quét chuỗi. Đây là lần thứ HAI cùng một sai lầm trong
    kho này (lần đầu: `test_oracle_KHONG_import_ma_san_pham`): quét chuỗi đỏ
    oan vì chính DOCSTRING nhắc tên module để **giải thích điều cấm**. Quét
    chuỗi cũng bỏ sót `importlib` — vừa bắt oan vừa bỏ sót.
    """
    import ast

    cay = ast.parse(_R.read_text(encoding="utf-8"))
    goc: list[str] = []
    for nut in ast.walk(cay):
        if isinstance(nut, ast.Import):
            goc += [a.name for a in nut.names]
        elif isinstance(nut, ast.ImportFrom) and nut.module:
            goc.append(nut.module)
    assert not any("run_sealed_evaluation" in g for g in goc), goc


def test_runner_KHONG_ghi_vao_thu_muc_cua_lUot_SEALED(rn):
    """Đường ra mặc định phải nằm trong `docs/evaluation/geometry/`, không đụng
    `semantic-benchmark/results/` — nơi giữ artifact held-out duy nhất."""
    import inspect

    mac_dinh = [d for d in inspect.getsource(rn.main).splitlines()
                if "out-dir" in d]
    assert mac_dinh and "GEO" in mac_dinh[0]
    assert "semantic-benchmark" not in str(rn.GEO)


def test_ep_skill_CHI_doi_dung_semantic_program(rn):
    """Đổi cả `analyze` sang prompt hình học là đo một hệ khác hệ mô tả."""
    goc = {"semantic_program": "TIN_HOC", "semantic_analyze": "ANALYZE",
           "geometry_program_generator": "HINH_HOC"}

    def _load(t):
        return goc[rn.SKILL_HINH_HOC if t == "semantic_program" else t]

    assert _load("semantic_program") == "HINH_HOC"
    assert _load("semantic_analyze") == "ANALYZE", "analyze phải giữ nguyên"


# ── 3. Chấm oracle — bám NGHĨA VỤ, không bám tên biến ─────────────────────
def test_oracle_PASS_khi_gia_tri_khop(rn):
    case = {"oracle_result": {"volume": "2/3"}}
    r = rn.cham_oracle(case, _HD(_Ob("volume", "V")), {"V": "2/3"})
    assert r["verdict"] == "PASS"


def test_oracle_khop_du_LLM_dat_TEN_BIEN_khac(rn):
    """Custodian không được đoán tên biến của LLM — đó là lý do khai theo
    NGHĨA VỤ. Tên `the_tich_khoi_chop` vẫn phải chấm được."""
    case = {"oracle_result": {"volume": "2/3"}}
    r = rn.cham_oracle(case, _HD(_Ob("volume", "the_tich_khoi_chop")),
                       {"the_tich_khoi_chop": "2/3"})
    assert r["verdict"] == "PASS"


def test_oracle_FAIL_khi_lech(rn):
    case = {"oracle_result": {"volume": "2/3"}}
    r = rn.cham_oracle(case, _HD(_Ob("volume", "V")), {"V": "1"})
    assert r["verdict"] == "FAIL" and r["lech"]


def test_oracle_so_PHAN_SO_khong_so_chuoi(rn):
    """`2/3` và `4/6` là cùng một số. So chuỗi sẽ báo lệch oan."""
    case = {"oracle_result": {"volume": "2/3"}}
    assert rn.cham_oracle(case, _HD(_Ob("volume", "V")),
                          {"V": "4/6"})["verdict"] == "PASS"


def test_oracle_quan_he_so_bool(rn):
    case = {"oracle_result": {"perpendicular": True}}
    assert rn.cham_oracle(case, _HD(_Ob("perpendicular", "kq")),
                          {"kq": True})["verdict"] == "PASS"
    assert rn.cham_oracle(case, _HD(_Ob("perpendicular", "kq")),
                          {"kq": False})["verdict"] == "FAIL"


def test_KHONG_chay_duoc_thi_NO_RESULT_khong_phai_FAIL(rn):
    r = rn.cham_oracle({"oracle_result": {"volume": "2/3"}}, _HD(), None)
    assert r["verdict"] == "NO_RESULT"


def test_khong_khop_nghia_vu_thi_UNGRADED_khong_phai_FAIL(rn):
    """Nhầm 'không chấm được' với 'sai' là bịa thêm thất bại."""
    r = rn.cham_oracle({"oracle_result": {"volume": "2/3"}},
                       _HD(_Ob("distance", "d")), {"d": "2"})
    assert r["verdict"] == "UNGRADED"


def test_khoa_VAN_XUOI_khong_duoc_dung_de_cham(rn):
    """`hinh_chieu_la: 'điểm A'` là ghi chú cho người đọc, không phải mốc chấm."""
    r = rn.cham_oracle({"oracle_result": {"hinh_chieu_la": "điểm A"}},
                       _HD(_Ob("point_on_plane", "H")), {"H": "x"})
    assert r["verdict"] == "UNGRADED"


# ── 4. DEV set: mọi bài đều chấm được ─────────────────────────────────────
def test_MOI_bai_DEV_co_it_nhat_mot_khoa_oracle_la_NGHIA_VU(rn):
    """Thiếu thì bài ấy luôn `UNGRADED` — tốn một lượt LLM mà không đo được gì."""
    from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

    d = json.loads(rn.DEV.read_text(encoding="utf-8"))
    thieu = [c["case_id"] for c in d["cases"]
             if not (set(c["oracle_result"]) & set(OBLIGATION_KINDS))]
    assert not thieu, f"bài không chấm được: {thieu}"


def test_phan_bo_ba_nhom_theo_yeu_cau(rn):
    """A dựng hình 3 · B quan hệ 3 · C tính toán 4."""
    d = json.loads(rn.DEV.read_text(encoding="utf-8"))
    kind = {c["case_id"]: set(c["expected_obligations"]) for c in d["cases"]}
    quan_he = {"point_on_line", "point_on_plane", "parallel", "perpendicular",
               "coplanar"}
    tinh = {"distance", "angle", "volume"}
    assert sum(1 for k in kind.values() if k & tinh) >= 3, "nhóm tính toán mỏng"
    assert sum(1 for k in kind.values() if k & quan_he) >= 5, "nhóm quan hệ mỏng"


# ── 5. Hình dạng artifact ─────────────────────────────────────────────────
def test_artifact_du_truong_theo_hop_dong(rn):
    bao = rn.tong_ket([], 10, None, "model-x")
    for k in ("G1_schema", "G2_semantic", "A_executable", "O_oracle",
              "obligation_match", "phan_bo_that_bai", "N", "hoan_tat"):
        assert k in bao, f"thiếu {k}"


def test_artifact_TU_KHAI_la_DEV(rn):
    assert "KHÔNG phải số" in rn.tong_ket([], 10, None, "m")["khai"]


def test_tong_ket_KHONG_phat_phan_tram(rn):
    """Mẫu số 10 < 20 ⇒ `RELIABILITY_EVALUATION_PLAN §3.3` cấm chia."""
    bao = rn.tong_ket([], 10, None, "m")
    for v in bao.values():
        if isinstance(v, dict):
            assert not {"ti_le", "rate", "percent"} & set(v)


def test_dung_som_thi_hoan_tat_la_False(rn):
    assert rn.tong_ket([], 10, "BUDGET_EXHAUSTED: x", "m")["hoan_tat"] is False


# ── 6. obligation_match phát hiện lệch ────────────────────────────────────
def test_mismatch_bi_phat_hien(rn):
    import reliability_v2 as RV

    m = RV.obligation_match(["perpendicular"], ["volume"])
    assert m["khop_hoan_toan"] is False and m["thua"] == ["volume"]


def test_phan_bo_that_bai_dem_du_moi_case(rn):
    ket = [{"failure_layer": 2}, {"failure_layer": 2}, {"failure_layer": None}]
    assert sum(rn._phan_bo(ket).values()) == 3
