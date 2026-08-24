# -*- coding: utf-8 -*-
"""Gộp `renderer_V` của pha B — bốn cổng TỪ CHỐI phải thật sự chặn. 0 API call.

Gộp bừa còn tệ hơn không gộp: nó **tạo ra một con số**, và con số ấy đi thẳng
vào bảng luận văn. Nên mỗi cổng có một test chứng minh nó chặn được, và một
test chứng minh nó KHÔNG chặn nhầm.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_M = Path(__file__).resolve().parents[2] / "scripts" / "merge_render_v.py"


@pytest.fixture(scope="module")
def mv():
    spec = importlib.util.spec_from_file_location("merge_render_v", _M)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["merge_render_v"] = mod
    spec.loader.exec_module(mod)
    return mod


_SEM_OK = {"stage_reached": "served", "executable": True, "servable": True}


def _dung_thu_muc(tmp_path: Path, *, prov_sua=None, phab_sua=None) -> Path:
    bao_cao = {
        "measured_system_candidate": "abc1234",
        "sealed_fingerprint": "7e5df014",
        "chay_luc": "2026-08-24T00:00:00Z",
        "dataset": "sealed",
    }
    cases = [{"case_id": "C1", "semantic": _SEM_OK, "cham": {"verdict": "PASS"},
              "v2": {"source_id": "C1", "replay_R": True, "renderer_V": None}}]
    prov = {**bao_cao, "so_envelope": 1, "case_ids": ["C1"]}
    prov.update(prov_sua or {})
    phab = {"faultcheck_red": True,
            "viewports": list(mv_viewports()), "ket_qua": {"C1": True}}
    phab.update(phab_sua or {})

    (tmp_path / "envelopes").mkdir()
    (tmp_path / "sealed_summary.json").write_text(json.dumps(bao_cao), encoding="utf-8")
    (tmp_path / "sealed_cases.json").write_text(json.dumps(cases), encoding="utf-8")
    (tmp_path / "envelopes" / "PROVENANCE.json").write_text(json.dumps(prov), encoding="utf-8")
    (tmp_path / "renderer_v.json").write_text(json.dumps(phab), encoding="utf-8")
    return tmp_path


def _nap_mv():
    spec = importlib.util.spec_from_file_location("_mv_helper", _M)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def mv_viewports():
    return _nap_mv().VIEWPORT_BAT_BUOC


def mv_chi_so_case(cid, semantic):
    return _nap_mv().chi_so_case(cid, semantic)


# ── đường hạnh phúc ───────────────────────────────────────────────────────
def test_du_dieu_kien_thi_GOP_duoc(mv, tmp_path):
    d = _dung_thu_muc(tmp_path)
    r = mv.gop(d)
    assert r["da_gop"] == 1
    cases = json.loads((d / "sealed_cases.json").read_text(encoding="utf-8"))
    assert cases[0]["v2"]["renderer_V"] is True
    bao = json.loads((d / "sealed_summary.json").read_text(encoding="utf-8"))
    assert bao["reliability_v2"]["pha_b"]["da_gop"] == 1


# ── cổng 1: thiếu provenance ──────────────────────────────────────────────
def test_thieu_PROVENANCE_thi_TU_CHOI(mv, tmp_path):
    d = _dung_thu_muc(tmp_path)
    (d / "envelopes" / "PROVENANCE.json").unlink()
    with pytest.raises(mv.TuChoi, match="PROVENANCE"):
        mv.gop(d)


# ── cổng 2: provenance lệch ───────────────────────────────────────────────
def test_candidate_lech_thi_TU_CHOI(mv, tmp_path):
    """Gộp kết quả render của một lượt đo KHÁC vào đây."""
    d = _dung_thu_muc(tmp_path, prov_sua={"measured_system_candidate": "KHAC"})
    with pytest.raises(mv.TuChoi, match="measured_system_candidate"):
        mv.gop(d)


def test_sealed_fingerprint_lech_thi_TU_CHOI(mv, tmp_path):
    d = _dung_thu_muc(tmp_path, prov_sua={"sealed_fingerprint": "KHAC"})
    with pytest.raises(mv.TuChoi, match="sealed_fingerprint"):
        mv.gop(d)


def test_chay_luc_lech_thi_TU_CHOI(mv, tmp_path):
    """Cùng candidate, cùng con dấu, nhưng là LƯỢT CHẠY khác."""
    d = _dung_thu_muc(tmp_path, prov_sua={"chay_luc": "2026-01-01T00:00:00Z"})
    with pytest.raises(mv.TuChoi, match="chay_luc"):
        mv.gop(d)


# ── cổng 3: faultcheck chưa đỏ ────────────────────────────────────────────
def test_faultcheck_chua_do_thi_TU_CHOI(mv, tmp_path):
    """Cổng đắt nhất khi bỏ qua — bài học `status=ok không phải bằng chứng`."""
    d = _dung_thu_muc(tmp_path, phab_sua={"faultcheck_red": False})
    with pytest.raises(mv.TuChoi, match="faultcheck"):
        mv.gop(d)


def test_faultcheck_VANG_MAT_cung_TU_CHOI(mv, tmp_path):
    """Thiếu cờ ≠ cờ true. Mặc định phải là từ chối."""
    d = _dung_thu_muc(tmp_path, phab_sua={"faultcheck_red": None})
    with pytest.raises(mv.TuChoi, match="faultcheck"):
        mv.gop(d)


# ── cổng 4: thiếu viewport ────────────────────────────────────────────────
def test_thieu_viewport_thi_TU_CHOI(mv, tmp_path):
    d = _dung_thu_muc(tmp_path, phab_sua={"viewports": ["desktop_1920x1080"]})
    with pytest.raises(mv.TuChoi, match="viewport"):
        mv.gop(d)


def test_bon_be_rong_khop_ban_nghiem_thu_truoc(mv):
    assert mv.VIEWPORT_BAT_BUOC == (
        "desktop_1920x1080", "laptop_1536x864", "school_1366x768", "tablet_768x900")


# ── mẫu số của V ──────────────────────────────────────────────────────────
def test_ca_KHONG_co_envelope_thi_V_van_None(mv, tmp_path):
    """Mẫu số của `V` là số ca CÓ `B`, không phải N. Điền `False` cho ca không
    phát được là kéo mẫu số lên và làm `V` trông tệ hơn sự thật."""
    d = _dung_thu_muc(tmp_path)
    cases = json.loads((d / "sealed_cases.json").read_text(encoding="utf-8"))
    # Dựng `v2` bằng CHÍNH hàm runner dùng — bịa một dict rút gọn thì test
    # xanh/đỏ vì hình dạng fixture, không vì hành vi của bước gộp.
    sem_hong = {"stage_reached": "semantic_program", "executable": False,
                "servable": False, "reason": "push tham chiếu container lạ"}
    cases.append({"case_id": "C2", "semantic": sem_hong,
                  "cham": {"verdict": "NO_RESULT"},
                  "v2": mv_chi_so_case("C2", sem_hong)})
    (d / "sealed_cases.json").write_text(json.dumps(cases), encoding="utf-8")
    mv.gop(d)
    sau = json.loads((d / "sealed_cases.json").read_text(encoding="utf-8"))
    assert sau[1]["v2"]["renderer_V"] is None
    bao = json.loads((d / "sealed_summary.json").read_text(encoding="utf-8"))
    assert bao["reliability_v2"]["V_renderer"]["mau_so"] == 1
