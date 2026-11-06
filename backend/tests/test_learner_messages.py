# -*- coding: utf-8 -*-
"""M17-Lite W0 — lock learner-facing error mapping (app/learner_messages.py).

Yêu cầu M17: học sinh KHÔNG thấy JSON path, internal id, schema error hay
exception thô — chỉ thấy tiếng Việt thân thiện. Chi tiết kỹ thuật vẫn sống
cho developer (field error_detail / reason kỹ thuật của pipeline giữ nguyên).
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.learner_messages import (
    attach_learner_reason,
    learner_error_message,
    learner_reason,
)
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _signed_in():
    """`/api/analyze` runs nothing without a server-issued session (`session_required`)."""
    from tests.route_client import sign_in
    client.cookies.clear()
    sign_in(client)

# Token kỹ thuật CẤM xuất hiện trong văn bản học sinh: snake_case id, JSON
# path, dấu ngoặc nhọn schema, tên exception. (Cho phép chữ thường có gạch
# dưới trong… không — cấm hẳn snake_case.)
_FORBIDDEN = re.compile(r"[a-z]+_[a-z_]+|\$\.|\{|\}|Traceback|Error\b|__")


def _sach(text: str) -> bool:
    return _FORBIDDEN.search(text) is None


# ── unit: learner_reason chọn theo failure_category CÓ CẤU TRÚC ──
def test_learner_reason_capability_gap_sach_token():
    env = {
        "status": "unsupported",
        "reason": "Bài cần cơ chế chưa có engine tất định sở hữu (optimal_pathfinding, numeric_threshold).",
        "failure_category": "capability_gap",
        "error_code": "gate_mechanism_ownership",
    }
    msg = learner_reason(env)
    assert _sach(msg), f"lộ token kỹ thuật: {msg}"
    assert "từ chối trung thực" in msg


def test_learner_reason_ngoai_danh_muc_sach_token():
    env = {"status": "unsupported", "reason": "LLM tự viết lý do kỹ thuật simulation_id=x"}
    msg = learner_reason(env)
    assert _sach(msg), f"lộ token kỹ thuật: {msg}"
    assert "danh mục" in msg


def test_M20W3_ba_hang_muc_tu_choi_cho_BA_thong_diep_khac_nhau():
    """Cổng phạm vi sinh hai hạng mục mới, và gộp chúng vào "ngoài danh mục" là
    nói sai theo hai hướng ngược nhau: đề môn khác thì "danh mục sẽ mở rộng dần"
    là lời hứa sai (hệ không bao giờ thêm hoá học); đề chỉ-giải-thích thì chủ đề
    VẪN thuộc chương trình, nói "ngoài danh mục" khiến học sinh ngồi chờ một thứ
    không có gì để thêm."""
    msgs = {
        cat: learner_reason({"status": "unsupported", "reason": "kỹ thuật", "failure_category": cat})
        for cat in ("out_of_scope", "not_simulation_suitable", None)
    }
    assert len(set(msgs.values())) == 3, "ba hạng mục đang dùng chung thông điệp"
    for cat, msg in msgs.items():
        assert _sach(msg), f"{cat} lộ token kỹ thuật: {msg}"

    assert "môn học khác" in msgs["out_of_scope"]
    # Lời hứa "danh mục sẽ được mở rộng" KHÔNG được xuất hiện ở hai ca này.
    assert "mở rộng" not in msgs["out_of_scope"]
    assert "mở rộng" not in msgs["not_simulation_suitable"]
    # Thứ PHẢI đúng là SỰ PHÂN BIỆT giữa hai lời từ chối, không phải chữ của
    # đề cũ. Bản trước ghim nguyên câu "thuộc chương trình Tin học", nên dọn
    # phạm vi sản phẩm làm nó đỏ dù ý định vẫn nguyên vẹn.
    #
    #   out_of_scope            — SAI CHỦ ĐỀ  ⇒ được nói "môn học khác"
    #   not_simulation_suitable — ĐÚNG chủ đề, nhưng không có cơ chế để diễn
    #
    # Lẫn hai cái này là bug thật: học sinh sẽ đi tìm bài khác trong khi bài
    # của em vốn đúng chủ đề (đúng lỗi `tests/geometry/test_refusal_truthful.py`
    # ghi lại ở lượt smoke 2026-08-25).
    assert "môn học khác" not in msgs["not_simulation_suitable"], \
        "lời từ chối đổ lỗi cho đề bài cái lỗi thuộc về hệ"
    assert "đúng chủ đề" in msgs["not_simulation_suitable"], \
        "không còn khẳng định đề bài ĐÚNG chủ đề — hai lời từ chối hoá giống nhau"
    assert "không có cơ chế" in msgs["not_simulation_suitable"]


def test_attach_khong_dung_den_envelope_ok():
    ok_env = {"status": "ok", "simulation_id": "algorithm.find_max", "config": {}}
    assert attach_learner_reason(ok_env) is ok_env  # nguyên vẹn, không copy thừa


def test_attach_gan_learner_reason_khong_mutate_goc():
    env = {"status": "unsupported", "reason": "kỹ thuật", "failure_category": "capability_gap"}
    out = attach_learner_reason(env)
    assert "learner_reason" in out and _sach(out["learner_reason"])
    assert "learner_reason" not in env  # bản sao — envelope pipeline không đổi


def test_learner_error_message_khong_nhung_chi_tiet():
    msg = learner_error_message()
    assert _sach(msg), f"lộ token kỹ thuật: {msg}"
    assert "thử lại" in msg


# ── integration qua /api/analyze (Hybrid `/4`, 0 network) ──
@pytest.fixture()
def co_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")


def _analyze(text: str):
    return client.post("/api/analyze", json={"input": {"type": "text", "content": text}})


def test_api_unsupported_mang_learner_reason(monkeypatch, tmp_path):
    import json as _json
    from copy import deepcopy
    from app.ai import hybrid_offline as HO
    from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism

    bad = deepcopy(_prism())
    bad["problem_text"] = bad["problem_text"].replace("AA' = 12.", "AA' = 12. BC = 11.")
    bad["premises"].append({"kind": "segment_length", "args": {"segment": ["B", "C"], "value": "11"}, "quote": "BC = 11."})
    corpus_file = tmp_path / "replay.json"
    corpus_file.write_text(
        _json.dumps({"schema": HO.LOCAL_REPLAY_SCHEMA, "outputs": {bad["problem_text"]: bad}}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "staging-replay")
    monkeypatch.setenv("HYBRID_REPLAY_CORPUS", str(corpus_file))
    res = _analyze(bad["problem_text"])
    assert res.status_code == 200
    body = res.json()
    assert body["route_d"]["status"] == "REFUSED"
    env = body["envelope"]
    assert env["status"] == "unsupported"
    assert _sach(env["learner_reason"])


def test_api_provider_error_than_thien_khong_lo_traceback(monkeypatch, co_key):
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "live")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    res = _analyze("Cho hình chóp S.ABCD có đáy là hình vuông cạnh 4, SA = 6. Tính thể tích khối chóp S.ABCD.")
    assert res.status_code == 503
    body = res.json()
    assert _sach(body["error"]), f"lộ token kỹ thuật: {body['error']}"
    assert body["reason_code"] == "LIVE_AI_DISABLED"


# ── W17 · §15.3 · lời từ chối theo NGUYÊN NHÂN có cấu trúc ───────────────────────────────
#
# Đề hợp lệ (nguyên nhân CONSTRUCTION) hay chưa rõ (UNKNOWN) ⇒ KHÔNG bảo người học sửa đề.

_BAO_SUA_DE = ("diễn đạt lại", "kiểm tra lại đề", "đối chiếu lại các số liệu trong đề", "sửa đề")


def _tu_choi(**kw) -> dict:
    return {"status": "unsupported", "failure_category": "geometry_generation_failed", **kw}


def _khong_bao_sua_de(msg: str) -> bool:
    return not any(cum in msg for cum in _BAO_SUA_DE)


def test_do_dai_khong_duong_do_de_ghi_noi_dung_doan_va_suy_bien():
    msg = learner_reason(_tu_choi(error_code="semantic_program_invalid", reason_code="NON_POSITIVE_LENGTH",
                                  reason_subjects=["AB"], refusal_cause="SOURCE"))
    assert "AB" in msg and "suy biến" in msg and _sach(msg), msg


def test_do_dai_khong_duong_de_khong_ghi_la_loi_he_khong_bao_sua_de():
    msg = learner_reason(_tu_choi(error_code="semantic_program_invalid", reason_code="NON_POSITIVE_LENGTH",
                                  reason_subjects=["AB"], refusal_cause="CONSTRUCTION"))
    assert "AB" in msg and _khong_bao_sua_de(msg) and "đề không cần sửa" in msg and _sach(msg), msg


def test_mat_phang_de_cho_khong_cat_khoi():
    msg = learner_reason(_tu_choi(error_code="semantic_program_invalid", reason_code="PLANE_DOES_NOT_CUT",
                                  reason_subjects=["(α)"], refusal_cause="SOURCE"))
    assert "(α)" in msg and "không cắt" in msg and "thiết diện" in msg and _sach(msg), msg


def test_lech_phep_dung_noi_ten_mat_phang_va_khong_bao_sua_de():
    msg = learner_reason(_tu_choi(error_code="input_not_grounded", reason_code="CONSTRUCTION_NOT_TEXT_BOUND",
                                  reason_subjects=["(β)", "(α)"], refusal_cause="CONSTRUCTION"))
    assert "(β)" in msg and "(α)" in msg and _khong_bao_sua_de(msg) and _sach(msg), msg


def test_gia_tri_chi_trong_yeu_cau_chung_minh():
    msg = learner_reason(_tu_choi(error_code="input_not_grounded", reason_code="GIVEN_ONLY_IN_GOAL_CLAUSE",
                                  reason_subjects=["SA"], refusal_cause="SOURCE"))
    assert "SA" in msg and "chứng minh" in msg and _sach(msg), msg


@pytest.mark.parametrize("ma", ["SOURCE_EVIDENCE_CONFLICT", "SOURCE_SPAN_MISMATCH"])
def test_so_lieu_he_doc_lech_de_la_loi_he(ma):
    """Đính chính §15.3: số liệu HỆ dùng lệch câu chữ của đề — đề là thẩm quyền, không bảo sửa đề."""
    msg = learner_reason(_tu_choi(error_code="input_not_grounded", reason_code=ma,
                                  reason_subjects=["AB"], refusal_cause="CONSTRUCTION"))
    assert "AB" in msg and _khong_bao_sua_de(msg) and _sach(msg), msg


def test_nguyen_nhan_chua_ro_khong_bao_sua_de():
    msg = learner_reason(_tu_choi(error_code="semantic_program_invalid", refusal_cause="UNKNOWN"))
    assert _khong_bao_sua_de(msg) and _sach(msg), msg


def test_tu_choi_khong_phan_xu_mang_nguyen_nhan_UNKNOWN_khong_phai_SOURCE():
    """Tiêm lỗi FM2 (W17): mặc định `SOURCE` thì giao diện bảo người học sửa dữ kiện của một đề
    có thể hợp lệ. Nơi từ chối không phân xử ⇒ `UNKNOWN`; nguyên nhân đã có thì giữ nguyên."""
    assert attach_learner_reason(_tu_choi(error_code="semantic_program_invalid"))["refusal_cause"] == "UNKNOWN"
    assert attach_learner_reason(_tu_choi(refusal_cause="CONSTRUCTION"))["refusal_cause"] == "CONSTRUCTION"
