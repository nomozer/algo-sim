# -*- coding: utf-8 -*-
"""Tuyến OCR local cho ảnh đề (Route A: tự động khi đã xác minh; Route D: xác nhận từng chỗ).

Không gọi AI. Chỉ chạy khi `local_ocr_available()` (cấu hình `LOCAL_OCR_PYTHON`/`LOCAL_OCR_TESSDATA`).
Mọi dữ kiện dùng để giải phải đến từ (a) token được ≥ 2 bộ đọc thuộc 2 HỌ engine khác nhau cùng đọc ra,
hoặc (b) học sinh xác nhận. Không có văn bản chuẩn nào được nạp ngầm.
"""
from __future__ import annotations

import base64
import io
import re
import time
from typing import Any

from app.ingestion.local_ocr import local_ocr_available, reread_local_ocr_regions, run_local_ocr
from app.ingestion.ocr_reconcile import OCR_RECONCILE_VERSION, reconcile_with_adjudication

LOCAL_OCR_ROUTE_VERSION = "local-ocr-route/1"
#: Hai HỌ engine (Paddle + Tesseract) phải cùng đọc ra một token toán thì token mới được coi là đã xác minh.
#: Hiệu chuẩn trên tập phát triển External16: chỉ một họ đồng thuận để lọt token sai (`CC'` → `CC` khi khung
#: phát hiện chung cắt mất dấu phẩy trên) — xem `fidelity_false_rejection_analysis.json`.
MIN_AGREEING_FAMILIES = 2
MAX_REVIEW_ITEMS = 24
LOW_QUALITY_UNCERTAIN_RATIO = 0.35

REVIEW_REASON_VI = {
    "RADICAL_DISAGREEMENT": "Dấu căn (√) đọc chưa chắc",
    "DEGREE_SYMBOL_DISAGREEMENT": "Ký hiệu độ (°) đọc chưa chắc",
    "PRIME_DISAGREEMENT": "Dấu phẩy trên (′) đọc chưa chắc",
    "RELATION_SYMBOL_DISAGREEMENT": "Ký hiệu vuông góc/song song đọc chưa chắc",
    "DIGIT_DISAGREEMENT": "Chữ số đọc chưa chắc",
    "MATH_TOKEN_DISAGREEMENT": "Ký hiệu toán đọc chưa chắc",
    "SINGLE_READER_MATH_TOKEN": "Chỉ một bộ đọc nhận ra ký hiệu này",
    "SINGLE_READER_TOKEN": "Chỉ một bộ đọc nhận ra chỗ này",
    "SAME_FAMILY_AGREEMENT_ONLY": "Ký hiệu toán chưa được hai bộ đọc độc lập xác nhận",
    "SHARED_CORRUPTION_PATTERN": "Ký hiệu có dạng thường bị đọc sai",
    "FRACTION_STRUCTURE_LOSS": "Phân số viết hai tầng — kiểm tra tử số và mẫu số",
    "AMBIGUOUS_DIACRITIC_RESTORATION": "Chữ tiếng Việt đọc chưa rõ dấu",
    "NOT_IN_LEXICON": "Chữ tiếng Việt đọc chưa chắc",
    "MULTIWORD_SLOT_MISMATCH": "Cụm chữ đọc chưa chắc",
}


def _reflow(draft: str) -> str:
    """Nối dòng bị ngắt giữa câu (giữ nguyên độ dài để vị trí ký tự của các khoảng không đổi)."""
    lines = draft.split("\n")
    out = []
    for idx, ln in enumerate(lines):
        if idx == 0:
            out.append(ln)
            continue
        keep_break = bool(re.match(r"^\s*(?:(?:Câu|Bài)\s*\d|[a-dA-D]\s*[.)]|[A-D]\s*[.,:])", ln))
        out.append(("\n" if keep_break else " ") + ln)
    return "".join(out)


def _crop_data_url(image_bytes: bytes, bbox: list[int] | None, *, max_h: int = 72, pad: int = 6) -> str | None:
    if not bbox:
        return None
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        x0, y0, x1, y1 = (int(v) for v in bbox)
        crop = img.crop((max(0, x0 - pad), max(0, y0 - pad), min(img.width, x1 + pad), min(img.height, y1 + pad)))
        if crop.height > max_h:
            crop = crop.resize((max(1, int(crop.width * max_h / crop.height)), max_h))
        buf = io.BytesIO()
        crop.save(buf, format="JPEG", quality=80)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:  # noqa: BLE001 — ảnh xem trước không được làm hỏng tuyến
        return None


_HEADER_LINE_RE = re.compile(r"^\s*(?:Câu|Cau|Cu|Bài|Bai)\s*\d+\s*[.:)]", re.IGNORECASE)


def count_problem_headers_on_page(page_image_bytes: bytes) -> int | None:
    """Số tiêu đề "Câu N"/"Bài N" ở đầu dòng mà RapidOCR đọc được trên cả trang (`None` nếu OCR local tắt/hỏng).
    OCR được cache theo ảnh nên không tốn thêm lượt khi tuyến OCR local chạy tiếp trên cùng trang."""
    if not local_ocr_available():
        return None
    raw = run_local_ocr(page_image_bytes)
    if not raw.get("ok"):
        return None
    lines = ((raw.get("engines") or {}).get("rapidocr") or {}).get("lines") or []
    return sum(1 for ln in lines if _HEADER_LINE_RE.match(str(ln.get("text", ""))))


def run_local_ocr_route(prepared_image_bytes: bytes, figure_bboxes) -> dict[str, Any] | None:
    """Chạy OCR local + đối chiếu + đọc lại vùng tranh chấp. `None` khi OCR local không được cấu hình."""
    if not local_ocr_available():
        return None
    t0 = time.perf_counter()
    raw = run_local_ocr(prepared_image_bytes)
    t_ocr = time.perf_counter()
    if not raw.get("ok"):
        return {"ok": False, "reason": raw.get("reason"), "ocr_ms": round((t_ocr - t0) * 1000.0, 2)}
    rec = reconcile_with_adjudication(
        raw,
        lambda boxes: reread_local_ocr_regions(prepared_image_bytes, boxes),
        figure_bboxes=figure_bboxes,
        min_agreeing_families=MIN_AGREEING_FAMILIES,
    )
    t_rec = time.perf_counter()
    rec["ok"] = True
    rec["solve_text"] = _reflow(rec["draft_text"])
    rec["raw_ocr"] = raw
    n_content = sum(1 for s in rec["spans"] if s["status"] != "dropped" and s["kind"] not in ("punct",))
    n_block = sum(1 for s in rec["uncertain_spans"] if s.get("blocking"))
    rec["uncertain_ratio"] = round(n_block / float(max(1, n_content)), 4)
    rec["low_quality"] = rec["uncertain_ratio"] > LOW_QUALITY_UNCERTAIN_RATIO
    rec["timing"] = {
        "ocr_ms": round((t_ocr - t0) * 1000.0, 2),
        "ocr_cached": bool(raw.get("cached")),
        "cold_worker": bool(raw.get("cold_worker")),
        "reconcile_and_reread_ms": round((t_rec - t_ocr) * 1000.0, 2),
        "reread_ms": (rec.get("adjudication") or {}).get("ms"),
        "total_ms": round((t_rec - t0) * 1000.0, 2),
    }
    return rec


def review_items(rec: dict[str, Any], image_bytes: bytes, *, base_offset: int = 0, text_len: int | None = None) -> list[dict[str, Any]]:
    """Các chỗ học sinh cần kiểm tra: vị trí ký tự trong văn bản đề, ảnh cắt nguồn, phương án thay thế."""
    items: list[dict[str, Any]] = []
    for s in rec.get("uncertain_spans") or []:
        if not s.get("blocking"):
            continue
        start, end = int(s.get("start", -1)), int(s.get("end", -1))
        if start >= 0:
            start -= base_offset
            end -= base_offset
            if start < 0 or (text_len is not None and end > text_len):
                continue
        alts = [a for a in (s.get("alternatives") or []) if a and a != s.get("text")][:4]
        items.append({
            "token": s.get("text") or "",
            "alternatives": alts,
            "location": f"dòng {str(s.get('line_id', '')).lstrip('L')}",
            "reason": REVIEW_REASON_VI.get(s.get("reason") or "", "Chỗ này đọc chưa chắc"),
            "reason_code": s.get("reason"),
            "kind": s.get("kind"),
            "span_id": s.get("span_id"),
            "span_start": start,
            "span_end": end,
            "crop_data_url": _crop_data_url(image_bytes, s.get("bbox")),
            "source": "local_ocr",
        })
        if len(items) >= MAX_REVIEW_ITEMS:
            break
    diag = rec.get("diagram") or {}
    if diag.get("blocking"):
        fig = (diag.get("figure_bboxes") or [None])[0]
        items.append({
            "token": "",
            "alternatives": [],
            "location": "hình vẽ",
            "reason": (
                "Đề nhắc tới hình vẽ — em xác nhận hình không ghi thêm số đo, góc hay quan hệ nào ngoài lời đề "
                "(nếu có, em ghi bổ sung vào đề)."
                if diag.get("classification") == "DIAGRAM_REFERENCED_BY_TEXT"
                else "Hình vẽ có thể chứa dữ kiện chưa đọc được — em xác nhận hoặc ghi bổ sung vào đề."
            ),
            "reason_code": "DIAGRAM_FACTS_UNVERIFIED:" + str(diag.get("classification")),
            "kind": "diagram",
            "span_id": "diagram",
            "span_start": -1,
            "span_end": -1,
            "crop_data_url": _crop_data_url(image_bytes, fig, max_h=160) if fig else None,
            "source": "local_ocr",
        })
    return items


def summarize_for_provenance(rec: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_version": LOCAL_OCR_ROUTE_VERSION,
        "reconcile_version": OCR_RECONCILE_VERSION,
        "extraction_verified": bool(rec.get("extraction_verified")),
        "blocking_reasons": list(rec.get("blocking_reasons") or []),
        "uncertain_blocking_count": sum(1 for s in rec.get("uncertain_spans") or [] if s.get("blocking")),
        "uncertain_ratio": rec.get("uncertain_ratio"),
        "low_quality": bool(rec.get("low_quality")),
        "diagram_classification": (rec.get("diagram") or {}).get("classification"),
        "layout_flags": [f.get("flag") for f in rec.get("layout_flags") or []],
        "min_agreeing_families": MIN_AGREEING_FAMILIES,
        "readers": rec.get("readers"),
        "adjudication": rec.get("adjudication"),
        "timing": rec.get("timing"),
        "used_ground_truth": False,
    }
