# -*- coding: utf-8 -*-
"""regular-triangular-pyramid-w01 · E — chính sách lưu ảnh (`scripts/prune_evidence_images.py`) trên một run giả.

Bốn lý do giữ (đầu vào oracle, đầu ra bộ dựng, tập duyệt chọn trước, họ thất bại) và một ảnh bỏ được ghi sha256.
"""
from __future__ import annotations

import json
import struct
import subprocess
import sys
import zlib
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prune_evidence_images.py"


def _png(p: Path, w: int = 4, h: int = 3) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)

    def chunk(t: bytes, d: bytes) -> bytes:
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * w for _ in range(h))
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                  + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def _json(p: Path, d: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d), encoding="utf-8")


def test_giu_bon_ly_do_va_bo_phan_con_lai(tmp_path):
    run = tmp_path / "run"
    anh = {k: run / "images" / v for k, v in {
        "oracle": "cube/desktop/neutral_final.png", "sheet": "cube/SHEET.png",
        "duyet": "regular-triangular-pyramid/desktop/selected_area.png",
        "hong": "cross-section/desktop/steps_panel_open.png", "bo": "cube/desktop/grid_on.png"}.items()}
    for p in anh.values():
        _png(p)
    _json(run / "results" / "EVIDENCE_IMAGE_INPUTS.json", {"images": ["images/cube/desktop/neutral_final.png"]})
    _json(run / "results" / "HIDDEN_EDGE_CROPS.json", {"crops": [], "family_sheets": {"cube": {"sheet": "images/cube/SHEET.png"}}})
    _json(run / "inputs" / "REVIEW_SET.json", {"items": [
        {"path": "images/regular-triangular-pyramid/*/selected_*.png", "requirement": "D2 chọn diện tích đáy"}]})
    _json(run / "results" / "BROWSER_EVIDENCE.json", {"scenarios": {"cube": {"pass": True}, "cross_section": {"pass": False}}})
    kq = subprocess.run([sys.executable, str(SCRIPT), "--run-dir", str(run), "--commit", "c0ffee",
                         "--candidate", "abc"], capture_output=True, text=True)
    assert kq.returncode == 0, kq.stderr
    pol = json.loads((run / "results" / "IMAGE_POLICY.json").read_text(encoding="utf-8"))
    ly_do = {m["path"]: m["reason"] for m in pol["kept"]}
    assert ly_do == {"images/cube/desktop/neutral_final.png": "oracle_input", "images/cube/SHEET.png": "builder_output",
                     "images/regular-triangular-pyramid/desktop/selected_area.png": "review",
                     "images/cross-section/desktop/steps_panel_open.png": "failure"}
    assert pol["failed_families"] == ["cross_section"]
    assert [m["path"] for m in pol["pruned"]] == ["images/cube/desktop/grid_on.png"]
    assert pol["pruned"][0]["sha256"] and pol["kept"][0]["image_px"] == [4, 3]
    assert not anh["bo"].exists() and all(anh[k].exists() for k in ("oracle", "sheet", "duyet", "hong"))


def test_loi_moi_truong_khong_giu_ca_ho(tmp_path):
    """exact-dimensions: một lượt hết giờ tải trang (POLL_TIMEOUT) là lỗi MÔI TRƯỜNG — không giữ trọn ảnh của cả họ;
    một phép kiểm sản phẩm đỏ vẫn giữ."""
    run = tmp_path / "run"
    for p in ("cube/desktop/grid_on.png", "cuboid/desktop/grid_on.png"):
        _png(run / "images" / p)
    _json(run / "results" / "BROWSER_EVIDENCE.json", {"scenarios": {
        "cube": {"pass": False, "positive": {"mobile": {"pass": False, "run_error": "Error: POLL_TIMEOUT:false"}}},
        "cuboid": {"pass": False, "positive": {"desktop": {"pass": False}}}}})
    kq = subprocess.run([sys.executable, str(SCRIPT), "--run-dir", str(run), "--commit", "c", "--candidate", "a"],
                        capture_output=True, text=True)
    assert kq.returncode == 0, kq.stderr
    pol = json.loads((run / "results" / "IMAGE_POLICY.json").read_text(encoding="utf-8"))
    assert pol["failed_families"] == ["cuboid"]
    assert not (run / "images" / "cube" / "desktop" / "grid_on.png").exists()


def test_dry_run_khong_xoa(tmp_path):
    run = tmp_path / "run"
    _png(run / "images" / "cube" / "desktop" / "grid_on.png")
    kq = subprocess.run([sys.executable, str(SCRIPT), "--run-dir", str(run), "--commit", "c", "--candidate", "a",
                         "--dry-run"], capture_output=True, text=True)
    assert kq.returncode == 0, kq.stderr
    assert (run / "images" / "cube" / "desktop" / "grid_on.png").exists()
    assert json.loads((run / "results" / "IMAGE_POLICY.json").read_text(encoding="utf-8"))["pruned_count"] == 1
