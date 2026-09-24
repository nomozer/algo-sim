# -*- coding: utf-8 -*-
"""EVIDENCE IDENTITY COLLECTOR & HASH POLICY AUDITOR.

Cung cấp cơ chế tính toán và đối soát hash với chính sách rõ ràng (fail-closed):
- RAW_BYTES: băm SHA-256 trên byte thô.
- LF_NORMALIZED: băm SHA-256 sau khi chuẩn hóa CRLF -> LF.
- CANONICAL_JSON: băm SHA-256 trên JSON có thụt dòng 2 space, sort_keys=True, UTF-8.
- MIN_JSON: băm SHA-256 trên JSON tối giản (separators=(',', ':')), sort_keys=True, UTF-8.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

VALID_POLICIES = {
    "RAW_BYTES",
    "LF_NORMALIZED",
    "CANONICAL_JSON",
    "MIN_JSON",
}


def compute_hash(content: bytes, policy: str) -> str:
    """Tính SHA-256 theo chính sách khai báo tường minh. Fail-closed nếu policy lạ."""
    if policy not in VALID_POLICIES:
        raise ValueError(f"Chính sách hash không được hỗ trợ: {policy}. Hợp lệ: {sorted(VALID_POLICIES)}")

    if policy == "RAW_BYTES":
        return hashlib.sha256(content).hexdigest()
    elif policy == "LF_NORMALIZED":
        normalized = content.replace(b"\r\n", b"\n")
        return hashlib.sha256(normalized).hexdigest()
    elif policy == "CANONICAL_JSON":
        data = json.loads(content.decode("utf-8"))
        canonical_bytes = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(canonical_bytes).hexdigest()
    elif policy == "MIN_JSON":
        data = json.loads(content.decode("utf-8"))
        min_bytes = json.dumps(data, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(min_bytes).hexdigest()
    raise ValueError(f"Unhandled policy: {policy}")


def get_git_revision_bytes(repo_root: Path, revision: str, rel_path: str) -> bytes:
    """Đọc byte thô của file tại một git revision cụ thể."""
    norm_path = rel_path.replace("\\", "/")
    res = subprocess.run(
        ["git", "show", f"{revision}:{norm_path}"],
        cwd=repo_root,
        capture_output=True,
        check=True,
    )
    return res.stdout


def audit_file_identity(
    file_path: Path,
    expected_hashes: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Kiểm tra toàn diện danh tính của một file trên đĩa."""
    if not file_path.exists():
        return {
            "path": str(file_path),
            "exists": False,
            "error": "FILE_NOT_FOUND",
        }

    raw_bytes = file_path.read_bytes()
    byte_count = len(raw_bytes)
    raw_sha = compute_hash(raw_bytes, "RAW_BYTES")
    lf_sha = compute_hash(raw_bytes, "LF_NORMALIZED")

    is_json = False
    canonical_json_sha = None
    min_json_sha = None
    try:
        canonical_json_sha = compute_hash(raw_bytes, "CANONICAL_JSON")
        min_json_sha = compute_hash(raw_bytes, "MIN_JSON")
        is_json = True
    except Exception:
        pass

    results = {
        "path": str(file_path),
        "exists": True,
        "byte_count": byte_count,
        "raw_sha256": raw_sha,
        "lf_sha256": lf_sha,
        "is_json": is_json,
        "canonical_json_sha256": canonical_json_sha,
        "min_json_sha256": min_json_sha,
        "mtime": file_path.stat().st_mtime,
    }

    if expected_hashes:
        matches = {}
        for pol, exp in expected_hashes.items():
            calc = compute_hash(raw_bytes, pol)
            matches[pol] = (calc == exp)
        results["policy_matches"] = matches

    return results
