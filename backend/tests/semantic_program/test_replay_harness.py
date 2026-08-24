# -*- coding: utf-8 -*-
"""Replay đa đầu vào — phải phân biệt được TÍNH THẬT với GÁN CỨNG. 0 API call.

Nửa quan trọng của file này là các ca ÂM TÍNH: một detector chỉ biết kêu thì vô
dụng. Nếu chương trình tính thật cũng bị gắn cờ thì `ok` luôn `False`, và người
đọc học cách bỏ qua nó.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec

_H = Path(__file__).resolve().parents[2] / "scripts" / "replay_harness.py"


@pytest.fixture(scope="module")
def rh():
    """Nạp harness từ `scripts/`.

    Phải ĐĂNG KÝ vào `sys.modules` TRƯỚC `exec_module`: `@dataclass` tra
    `sys.modules[cls.__module__]` lúc dựng lớp, và không có mặt ở đó thì nổ
    `'NoneType' object has no attribute '__dict__'` — một thông báo không hề
    gợi ý nguyên nhân.
    """
    import sys

    spec = importlib.util.spec_from_file_location("replay_harness", _H)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["replay_harness"] = mod
    spec.loader.exec_module(mod)
    return mod


def _replay(rh, raw, witness="m"):
    return rh.replay(SemanticProgramSpec.model_validate(raw), ["a"], witness=witness)


# ── dương tính: bắt được chương trình giả ─────────────────────────────────
def test_gan_cung_bi_BAT(rh):
    """Ca này cố ý QUA ĐƯỢC kiểm tĩnh C₁b: `m` phụ thuộc `a` qua `length`,
    nên đồ thị phụ thuộc sạch. Chỉ chạy lại với đầu vào khác mới lộ."""
    r = _replay(rh, rh.GAN_CUNG)
    assert r.ok is False
    assert any(p.startswith("INPUT_IGNORED") for p in r.phat_hien)
    assert r.chi_tiet["so_chu_ky_khac_nhau"] == 1


def test_gan_cung_bi_NGHI_hard_coded(rh):
    r = _replay(rh, rh.GAN_CUNG)
    assert any(p.startswith("HARD_CODED?") for p in r.phat_hien)
    assert len(set(r.chi_tiet["witness_qua_cac_luot"])) == 1


# ── âm tính: KHÔNG được gắn cờ chương trình thật ──────────────────────────
def test_tinh_that_KHONG_bi_bat(rh):
    r = _replay(rh, rh.TIM_MAX)
    assert r.ok is True, r.phat_hien
    assert not any(p.startswith("INPUT_IGNORED") for p in r.phat_hien)


def test_tinh_that_co_witness_BIEN_THIEN(rh):
    """Bằng chứng dương của replay: đổi đầu vào thì đáp án đổi theo."""
    r = _replay(rh, rh.TIM_MAX)
    assert len(set(r.chi_tiet["witness_qua_cac_luot"])) > 1


# ── HARD_CODED là NGHI VẤN, không được quyết PASS/FAIL ────────────────────
def test_hard_coded_mot_minh_KHONG_lam_FAIL(rh):
    """Một nghĩa vụ có thể hằng chính đáng. Biến nghi vấn thành phán quyết là
    đẻ ra false rejection ở đúng chỗ khó cãi nhất."""
    kq = rh.KetQuaReplay(
        so_luot=5,
        phat_hien=["HARD_CODED?: witness 'm' = 1 ở MỌI đầu vào."],
        chi_tiet={}, luot=[],
    )
    assert kq.ok is True


def test_input_ignored_thi_LAM_FAIL(rh):
    kq = rh.KetQuaReplay(5, ["INPUT_IGNORED: ..."], {}, [])
    assert kq.ok is False


def test_dead_state_thi_LAM_FAIL(rh):
    kq = rh.KetQuaReplay(5, ["DEAD_STATE: ..."], {}, [])
    assert kq.ok is False


# ── chữ ký hành động phải BỎ giá trị ──────────────────────────────────────
def test_chu_ky_bo_gia_tri_neu_khong_INPUT_IGNORED_vo_dung(rh):
    """Giữ giá trị trong chữ ký thì hai lượt LUÔN khác nhau, và detector
    `INPUT_IGNORED` không bao giờ bắt được gì — xanh vĩnh viễn, vô nghĩa."""
    r = _replay(rh, rh.GAN_CUNG)
    # Chương trình gán cứng vẫn ĐỌC `a` (qua `length`) nên giá trị trung gian
    # khác nhau giữa các lượt; chữ ký vẫn phải thu về đúng MỘT.
    assert r.chi_tiet["so_chu_ky_khac_nhau"] == 1


# ── lỗi thực thi là DỮ LIỆU, không phải sự cố của harness ─────────────────
def test_luot_nem_loi_van_duoc_ghi_nhan_khong_lam_vo_harness(rh):
    """Biến thể có dãy RỖNG: interpreter nay fail-closed nên một số lượt sẽ
    ném lỗi. Harness phải ghi lại rồi đi tiếp — nếu không, chính phép tiêm lỗi
    hữu ích nhất lại làm hỏng công cụ đo."""
    raw = rh._khung([
        {"kind": "assign", "target_var": "m",
         "expr": {"kind": "index", "container": "a",
                  "index": {"kind": "literal", "value": 0}}},
    ])
    r = _replay(rh, raw)
    assert r.chi_tiet["so_luot_loi"] >= 1, "biến thể dãy rỗng phải ném lỗi"
    assert r.chi_tiet["so_luot_chay_duoc"] >= 1, "không được hỏng hết"
    assert len(r.luot) == 1 + rh.SO_BIEN_THE
