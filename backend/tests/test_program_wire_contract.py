# -*- coding: utf-8 -*-
"""M17 — SYNC-LOCK hợp đồng dây dẫn `program-2.0` giữa backend và frontend.

Bối cảnh (audit 2026-08-03): backend `validate_program_config` CHUẨN HOÁ biểu
thức inline thành bảng `expressions[]` + tham chiếu id, và chính hình dạng đó đi
vào `ValidatedSimulationEnvelope`. Frontend lại luôn chuẩn hoá từ bề mặt inline
nên TỪ CHỐI mọi envelope backend phát ra: backend `status: ok` mà trình duyệt
không dựng được gì. Không test nào bắt được vì fixture frontend tự dựng bằng bề
mặt inline — tức frontend chưa bao giờ được kiểm với thứ backend thật sự gửi.

File JSON dùng chung được SINH TỪ chính validator này (không chép tay), theo
đúng khuôn `capability-descriptors.json`: artifact nằm ở cây frontend, test
backend đọc sang để khoá chống trôi.

  backend  →  test này: validator vẫn phát ĐÚNG hình dạng trong file
  frontend →  program-module.test.tsx: FE tiêu thụ được ĐÚNG hình dạng đó

Đổi normalizer backend mà quên file này ⇒ ĐỎ ở đây. Đổi file mà FE không theo
kịp ⇒ ĐỎ ở vitest.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.simulation.program_spec import FORBIDDEN_SPEC_KEYS, SPEC_VERSION
from app.validation.program import validate_program_config

WIRE = (
    Path(__file__).resolve().parents[2]
    / "frontend/src/simulations/domains/algorithm/program-normalized-envelope.json"
)


def _payload() -> dict:
    return json.loads(WIRE.read_text(encoding="utf-8"))


def test_file_hop_dong_ton_tai_va_du_hai_phan():
    p = _payload()
    assert "_source_candidate" in p, "thiếu candidate nguồn — không tái sinh được"
    assert "config" in p, "thiếu config đã chuẩn hoá"


def test_validator_van_phat_dung_hinh_dang_trong_file():
    """Sync-lock: chạy LẠI validator trên candidate nguồn, phải ra ĐÚNG file."""
    p = _payload()
    cfg, err = validate_program_config(p["_source_candidate"])
    assert cfg is not None, f"candidate nguồn không còn hợp lệ: {err}"
    assert cfg == p["config"], (
        "backend đã trôi khỏi hợp đồng dây dẫn. Sinh lại file bằng chính "
        "validate_program_config rồi chạy vitest để chắc frontend vẫn tiêu thụ được."
    )


def test_hinh_dang_day_dan_la_CANONICAL_da_chuan_hoa():
    """Khoá đúng tính chất khiến frontend từng vỡ: điều kiện là THAM CHIẾU id."""
    cfg = _payload()["config"]
    assert cfg["program_version"] == SPEC_VERSION
    assert isinstance(cfg.get("expressions"), list) and cfg["expressions"], (
        "dây dẫn phải mang bảng expressions"
    )
    while_st = next(s for s in cfg["statements"] if s["kind"] == "while")
    assert isinstance(while_st["condition"], str), (
        "điều kiện trên dây dẫn phải là tham chiếu id, không phải {atoms}"
    )
    assert while_st["condition"] in {e["id"] for e in cfg["expressions"]}


def test_config_day_dan_KHONG_mang_ket_qua():
    """R0: spec chỉ mô tả chương trình; số lượt lặp và dãy giá trị là của engine."""
    cfg = _payload()["config"]
    assert not (set(cfg) & FORBIDDEN_SPEC_KEYS)
    for k in ("trace", "steps", "environment", "result", "iterations", "timeline"):
        assert k not in cfg


def test_be_mat_UNG_VIEN_kieu_cu_van_bi_backend_tu_choi():
    """Bảo đảm W2C-C1 §L2 — ĐẶT ĐÚNG CHỖ.

    Trước audit, tính chất "bề mặt ứng viên kiểu cũ (bảng biểu thức + tham chiếu
    id) không còn được chấp nhận" bị khoá ở FRONTEND (`core/program.test.ts`).
    Đó là chỗ sai: frontend không nhận candidate của LLM, nó nhận envelope — mà
    envelope mang ĐÚNG dạng tham chiếu id. Khoá nhầm chỗ chính là nguyên nhân
    contract drift không ai thấy.

    LLM nộp bài cho BACKEND, nên bảo đảm sống ở đây. Tính chất KHÔNG bị mất đi,
    chỉ chuyển về đúng tầng.
    """
    old_surface = {
        "program_version": SPEC_VERSION,
        "variables": [{"name": "x", "type": "integer", "int_value": 1}],
        "expressions": [{"id": "e1", "kind": "int", "int_value": 2}],
        "statements": [{"id": "s1", "kind": "assign", "target": "x", "value": "e1"}],
        "main": ["s1"],
    }
    cfg, err = validate_program_config(old_surface)
    assert cfg is None, "backend phải từ chối bề mặt ứng viên kiểu cũ"
    assert "phải là một đối tượng" in err
