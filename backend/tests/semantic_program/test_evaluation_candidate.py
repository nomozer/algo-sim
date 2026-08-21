# -*- coding: utf-8 -*-
"""Khoá EVALUATION CANDIDATE — danh tính bản được đo (spec §7.3, §7.4).

Ý nghĩa của mốc này: SEALED chỉ có giá trị khi biết **đo bản nào**. Không có nó
thì sau khi thấy số, mọi câu "à lúc đó taxonomy còn khác" đều không kiểm chứng
được — và đó chính là cách một benchmark mất giá trị mà không ai nhận ra.

Test này ĐỎ khi taxonomy / tập primitive / schema / DEV đổi mà candidate không
được đóng băng lại. Nếu lệch **vì một kết quả SEALED** thì đó là vi phạm luật
con dấu: DEV được phép làm thay đổi hệ, SEALED chỉ được phép làm thay đổi KẾT
LUẬN của luận văn.
"""
import hashlib
import json
import typing
from pathlib import Path

import pytest

from app.main import CACHE_VERSION
from app.simulation.semantic_program.contract import (
    SPEC_VERSION,
    VisualContainerBinding,
)
from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

ROOT = Path(__file__).resolve().parents[3]
BENCH = ROOT / "docs" / "evaluation" / "semantic-benchmark"
CANDIDATE = BENCH / "EVALUATION_CANDIDATE.json"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def manifest() -> dict:
    assert CANDIDATE.exists(), (
        "Thiếu EVALUATION_CANDIDATE.json — chạy "
        "backend/scripts/freeze_evaluation_candidate.py"
    )
    return json.loads(CANDIDATE.read_text(encoding="utf-8"))


def test_cache_version_khop_nguon(manifest):
    assert manifest["cache_version"] == CACHE_VERSION


def test_spec_version_ir_khop_nguon(manifest):
    assert manifest["spec_version_ir"] == SPEC_VERSION


def test_taxonomy_khong_troi_khoi_ban_da_dong_bang(manifest):
    hien_tai = {k: sorted(v) for k, v in sorted(OBLIGATION_KINDS.items())}
    assert manifest["taxonomy"]["hash"] == _sha(
        json.dumps(hien_tai, ensure_ascii=False, sort_keys=True)
    ), (
        "Taxonomy đã đổi sau khi đóng băng candidate. Nếu đổi vì một case SEALED "
        "⇒ VI PHẠM luật con dấu (§7.4). Nếu đổi từ DEV trước khi seal ⇒ đóng băng "
        "lại candidate."
    )


def test_tap_primitive_khong_troi(manifest):
    hien_tai = sorted(
        typing.get_args(VisualContainerBinding.model_fields["primitive"].annotation)
    )
    assert manifest["visual_primitive_set"]["hash"] == _sha(
        json.dumps(hien_tai, ensure_ascii=False)
    )
    assert "graph_view" in manifest["visual_primitive_set"]["primitives"]


def test_schema_khong_troi(manifest):
    schema = ROOT / "docs" / "schemas" / "semantic_program.schema.json"
    assert manifest["schema_semantic_program"]["hash"] == _sha(
        schema.read_text(encoding="utf-8")
    )


def test_dev_fingerprint_khong_troi(manifest):
    dev = BENCH / "dev" / "cases.json"
    assert manifest["dev"]["fingerprint"] == hashlib.sha256(dev.read_bytes()).hexdigest()
    assert manifest["dev"]["so_case"] == 20


def test_candidate_ghi_dung_commit_va_cay_sach(manifest):
    """Cây bẩn ⇒ trường `commit` không định danh được bản đang đo."""
    assert manifest["cay_lam_viec_sach"] is True, (
        "Candidate được đóng băng trên cây làm việc BẨN — commit ghi trong đó "
        "không định danh được bản thật sự đem đo."
    )
    assert len(manifest["commit"]) == 40
