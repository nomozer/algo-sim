# -*- coding: utf-8 -*-
"""TEST EVIDENCE IDENTITY RECONCILIATION & HASH POLICY AUDITOR.

Kiểm tra:
1. RAW_BYTES vs LF_NORMALIZED phân biệt đúng khi có CRLF.
2. CANONICAL_JSON chuẩn hóa đúng dù formatting gốc khác biệt.
3. Hai nội dung cùng byte count nhưng khác byte thì hash khác nhau (không xung đột).
4. Kiểm tra revision git qua get_git_revision_bytes.
5. Hash policy không khai báo -> ValueError (fail-closed).
6. Danh tính SECOND_FAMILY_MANIFEST.json và SECOND_FAMILY_GROUND_TRUTH.json bất biến từ abb377b8 tới HEAD.
7. Danh tính raw response D:/tmp/live_retry_evidence khớp chính xác 2322 bytes và hash đã đăng ký.
"""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from scripts.evidence_identity_collector import (
    compute_hash,
    get_git_revision_bytes,
    audit_file_identity,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_fail_closed_unknown_policy():
    """Policy lạ phải fail closed với ValueError."""
    with pytest.raises(ValueError, match="Chính sách hash không được hỗ trợ"):
        compute_hash(b"hello world", "UNKNOWN_POLICY")


def test_raw_bytes_vs_lf_normalized():
    """Nội dung CRLF phải cho raw_sha khác lf_sha."""
    crlf_content = b'{"key": "value"}\r\n'
    raw_sha = compute_hash(crlf_content, "RAW_BYTES")
    lf_sha = compute_hash(crlf_content, "LF_NORMALIZED")
    assert raw_sha != lf_sha

    lf_content = b'{"key": "value"}\n'
    assert compute_hash(lf_content, "RAW_BYTES") == lf_sha


def test_canonical_json_vs_raw_json():
    """Hai JSON khác formatting nhưng cùng nội dung phải cho canonical_json_sha giống nhau."""
    unformatted = b'{"b":2,   "a":1}'
    formatted = b'{\n  "a": 1,\n  "b": 2\n}'

    # Raw bytes khác nhau
    assert compute_hash(unformatted, "RAW_BYTES") != compute_hash(formatted, "RAW_BYTES")

    # Canonical JSON giống nhau
    assert compute_hash(unformatted, "CANONICAL_JSON") == compute_hash(formatted, "CANONICAL_JSON")


def test_same_byte_count_different_hash():
    """Hai file cùng kích thước byte nhưng khác nội dung phải có SHA-256 khác nhau."""
    b1 = b"abcde12345"
    b2 = b"12345abcde"
    assert len(b1) == len(b2)
    assert compute_hash(b1, "RAW_BYTES") != compute_hash(b2, "RAW_BYTES")


def test_git_revision_bytes_integrity():
    """Kiểm tra đọc byte qua git show và so sánh revision."""
    rel = "docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/SECOND_FAMILY_MANIFEST.json"
    bytes_prereg = get_git_revision_bytes(REPO_ROOT, "abb377b8", rel)
    bytes_head = get_git_revision_bytes(REPO_ROOT, "HEAD", rel)

    assert bytes_prereg == bytes_head
    assert len(bytes_prereg) == 12911
    assert compute_hash(bytes_prereg, "RAW_BYTES") == "f5978eb5f76b72808a02791dadc96f3b001b3bd288fc84e6656307ac4d0fefe5"


def test_preregistration_files_no_drift():
    """Manifest và ground truth trên đĩa phải khớp 100% commit tiền đăng ký abb377b8."""
    manifest_p = REPO_ROOT / "docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/SECOND_FAMILY_MANIFEST.json"
    gt_p = REPO_ROOT / "docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/SECOND_FAMILY_GROUND_TRUTH.json"

    assert manifest_p.exists()
    assert gt_p.exists()

    manifest_bytes = manifest_p.read_bytes()
    gt_bytes = gt_p.read_bytes()

    manifest_lf = manifest_bytes.replace(b"\r\n", b"\n")
    gt_lf = gt_bytes.replace(b"\r\n", b"\n")

    assert len(manifest_lf) == 12911
    assert len(gt_lf) == 5002

    assert compute_hash(manifest_bytes, "LF_NORMALIZED") == "f5978eb5f76b72808a02791dadc96f3b001b3bd288fc84e6656307ac4d0fefe5"
    assert compute_hash(gt_bytes, "LF_NORMALIZED") == "faf42e894fb9f69c8b61aba06f84767ec9806d1231633d2975516ec5367e18ce"


def test_raw_response_identity_reproduced():
    """Raw response ngoại vi tại D:/tmp/live_retry_evidence phải khớp chính xác 2322 bytes và hash live report."""
    raw_p = Path("D:/tmp/live_retry_evidence/PRISM_SCHEMA_LIVE_P01_raw_response.json")
    assert raw_p.exists(), f"Không tìm thấy file tại {raw_p}"

    raw_bytes = raw_p.read_bytes()
    assert len(raw_bytes) == 2322
    expected_sha = "f1bd804584bfe18f5a3ead539a2eb8043696d53465a7f852c2f1cf92920d91b0"

    assert compute_hash(raw_bytes, "RAW_BYTES") == expected_sha
    assert compute_hash(raw_bytes, "LF_NORMALIZED") == expected_sha
