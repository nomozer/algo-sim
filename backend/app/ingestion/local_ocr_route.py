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

LOCAL_OCR_ROUTE_VERSION = "local-ocr-route/3"
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
    "LOWERCASE_VERTEX_LABEL": "Tên đỉnh hình học có thể bị đọc nhầm thành chữ thường",
    "LOW_CONFIDENCE_STEM_TOKEN": "Chữ trong đề có độ tin cậy thấp — cần kiểm tra",
}


def _reflow(draft: str) -> str:
    """Nối dòng bị ngắt giữa câu (giữ nguyên độ dài để vị trí ký tự của các khoảng không đổi)."""
    lines = draft.split("\n")
    out = []
    for idx, ln in enumerate(lines):
        if idx == 0:
            out.append(ln)
            continue
        keep_break = bool(
            re.match(r"^\s*(?:(?:Câu|Bài)\s*\d|[a-dA-D]\s*[.)]|[A-D]\s*[.,:])", ln)
            or re.search(r"(?<![\w'])B\s*[.)]\s*\S.*(?<![\w'])C\s*[.)]\s*\S", ln)
        )
        out.append(("\n" if keep_break else " ") + ln)
    return "".join(out)


def _crop_data_url_img(img, bbox: list[int] | None, *, max_h: int = 72, pad: int = 6) -> str | None:
    if img is None or not bbox:
        return None
    try:
        x0, y0, x1, y1 = (int(v) for v in bbox)
        crop = img.crop((max(0, x0 - pad), max(0, y0 - pad), min(img.width, x1 + pad), min(img.height, y1 + pad)))
        if crop.height > max_h:
            crop = crop.resize((max(1, int(crop.width * max_h / crop.height)), max_h))
        buf = io.BytesIO()
        crop.save(buf, format="JPEG", quality=80)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:  # noqa: BLE001 — ảnh xem trước không được làm hỏng tuyến
        return None


def _crop_data_url(image_bytes: bytes, bbox: list[int] | None, *, max_h: int = 72, pad: int = 6) -> str | None:
    if not bbox:
        return None
    try:
        from PIL import Image

        with Image.open(io.BytesIO(image_bytes)) as opened:
            img = opened.convert("RGB")
        return _crop_data_url_img(img, bbox, max_h=max_h, pad=pad)
    except Exception:  # noqa: BLE001 — ảnh xem trước không được làm hỏng tuyến
        return None


_HEADER_LINE_RE = re.compile(r"^\s*(?:Câu|Cau|Cu|Bài|Bai)\s*\d+\s*[.:)]", re.IGNORECASE)


#: An answer-option marker at the start of an OCR word: "A.", "B)", "(C)", "D.a³√3" (run `semantic-failure-safe-image-segmentation`).
_OPTION_MARK_RE = re.compile(r"^\(?([A-D])\s*[.)]")


def option_groups(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Multiple-choice option groups on a page, from OCR word positions only (no text is trusted as a fact).

    Option markers are grouped into rows by vertical centre, rows into one group while they follow each other closely —
    a group may be one row (A B C D), two rows (A B / C D) or four rows. A row carrying "A" starts a NEW group when the
    current group already has an "A": every multiple-choice problem has exactly one option A. A group needs ≥ 3 distinct
    letters. Returns [{top, bottom, left, right, letters}] in the image's pixel coordinates, top to bottom."""
    lines = ((raw.get("engines") or {}).get("rapidocr") or {}).get("lines") or []
    toks = []
    for ln in lines:
        for w in ln.get("words") or [ln]:
            m = _OPTION_MARK_RE.match(str(w.get("text", "")).strip())
            if m and w.get("bbox"):
                x0, y0, x1, y1 = w["bbox"]
                toks.append((m.group(1), (y0 + y1) / 2, max(1, y1 - y0), x0, y0, x1, y1))
    toks.sort(key=lambda t: t[1])
    rows: list[list[tuple]] = []
    for t in toks:
        if rows and abs(rows[-1][-1][1] - t[1]) < 0.6 * max(t[2], rows[-1][-1][2]):
            rows[-1].append(t)
        else:
            rows.append([t])
    groups: list[list[list[tuple]]] = []
    for r in rows:
        h = max(t[2] for t in r)
        seen = {t[0] for rr in groups[-1] for t in rr} if groups else set()
        if groups and r[0][1] - groups[-1][-1][0][1] < 3.2 * h and not ("A" in {t[0] for t in r} and "A" in seen):
            groups[-1].append(r)
        else:
            groups.append([r])
    out = []
    for g in groups:
        ts = [t for r in g for t in r]
        letters = sorted({t[0] for t in ts})
        if len(letters) >= 3:
            out.append({"top": min(t[4] for t in ts), "bottom": max(t[6] for t in ts), "left": min(t[3] for t in ts),
                        "right": max(t[5] for t in ts), "letters": letters})
    return out


def problem_bands(raw: dict[str, Any], height: int, width: int | None = None) -> list[tuple[int, int, int, int]] | None:
    """One rectangle (x0, y0, x1, y1) per option group = per problem, in the image's pixels.

    Columns first: option groups whose x-ranges are disjoint sit in different columns; the column cut is a vertical line
    between them that NO OCR line crosses (else the layout is ambiguous → None). Inside a column, problems are stacked:
    the cut is halfway between a group's last option row and the next OCR line of that column below it. Groups of one
    column that overlap vertically → None. Never a band that crosses a column."""
    groups = option_groups(raw)
    if len(groups) < 2:
        return None
    lines = [ln["bbox"] for ln in ((raw.get("engines") or {}).get("rapidocr") or {}).get("lines") or [] if ln.get("bbox")]
    width = int(width or raw.get("width") or max([b[2] for b in lines] + [g["right"] for g in groups]))

    def overlap(a, b):
        return min(a["right"], b["right"]) - max(a["left"], b["left"])

    cols: list[list[dict]] = []
    for g in sorted(groups, key=lambda g: g["left"]):
        col = next((c for c in cols if any(overlap(g, h) > 0.3 * min(g["right"] - g["left"], h["right"] - h["left"]) for h in c)), None)
        (col.append(g) if col is not None else cols.append([g]))
    cols.sort(key=lambda c: min(g["left"] for g in c))
    xcuts = []
    for left, right in zip(cols, cols[1:]):
        lo, hi = max(g["right"] for g in left), min(g["left"] for g in right)
        if hi <= lo:
            return None
        free = [x for x in range(int(lo), int(hi) + 1, 4) if not any(b[0] < x < b[2] for b in lines)]
        if not free:
            return None                               # a text line crosses every candidate cut: columns not separable
        runs, run = [], [free[0]]
        for x in free[1:]:
            if x - run[-1] <= 4:
                run.append(x)
            else:
                runs.append(run)
                run = [x]
        runs.append(run)
        best = max(runs, key=len)
        xcuts.append((best[0] + best[-1]) // 2)
    xedges = [0, *xcuts, width]
    out: list[tuple[int, int, int, int]] = []
    for ci, col in enumerate(cols):
        x0, x1 = xedges[ci], xedges[ci + 1]
        col = sorted(col, key=lambda g: g["top"])
        if any(b["top"] < a["bottom"] for a, b in zip(col, col[1:])):
            return None
        tops = sorted(int(b[1]) for b in lines if b[0] < x1 and b[2] > x0)
        cuts = []
        for g in col[:-1]:
            nxt = next((t for t in tops if t > g["bottom"]), None)
            cuts.append(int((g["bottom"] + nxt) / 2) if nxt is not None else int(g["bottom"]))
        edges = [0, *cuts, height]
        out += [(x0, edges[i], x1, edges[i + 1]) for i in range(len(edges) - 1)]
    return out


def estimate_problem_signals(page_image_bytes: bytes) -> dict[str, Any] | None:
    """Layout evidence of how many problems an image holds, from ONE local OCR pass (cached per image): "Câu/Bài N"
    headers and multiple-choice option groups. `None` when local OCR is off or failed — the caller then keeps its
    previous behaviour. Evidence only: nothing read here becomes a fact."""
    if not local_ocr_available():
        return None
    raw = run_local_ocr(page_image_bytes)
    if not raw.get("ok"):
        return None
    lines = ((raw.get("engines") or {}).get("rapidocr") or {}).get("lines") or []
    groups = option_groups(raw)
    if not lines and not groups:
        return None
    return {"headers": sum(1 for ln in lines if _HEADER_LINE_RE.match(str(ln.get("text", "")))),
            "option_groups": len(groups), "groups": groups,
            "bands": problem_bands(raw, int(raw.get("height") or 0), int(raw.get("width") or 0) or None) if len(groups) >= 2 else None,
            "height": int(raw.get("height") or 0)}


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
    adj_info = rec.get("adjudication") or {}
    reread_ms = float(adj_info.get("ms") or 0.0)
    reconcile_total_ms = (t_rec - t_ocr) * 1000.0
    raw_engines = raw.get("engines") or {}
    rec["timing"] = {
        "worker_version": raw.get("worker_version"),
        "ocr_ms": round((t_ocr - t0) * 1000.0, 2),
        "ocr_cached": bool(raw.get("cached")),
        "cold_worker": bool(raw.get("cold_worker")),
        "decode_ms": raw.get("decode_ms"),
        "tesseract_ms": (raw_engines.get("tesseract") or {}).get("ms"),
        "rapidocr_ms": (raw_engines.get("rapidocr") or {}).get("ms"),
        "reconcile_and_reread_ms": round(reconcile_total_ms, 2),
        "reconcile_only_ms": round(max(0.0, reconcile_total_ms - reread_ms), 2),
        "reread_ms": adj_info.get("ms"),
        "reread_breakdown": adj_info.get("timings"),
        "total_ms": round((t_rec - t0) * 1000.0, 2),
    }
    return rec


def review_items(rec: dict[str, Any], image_bytes: bytes, *, base_offset: int = 0, text_len: int | None = None) -> list[dict[str, Any]]:
    """Các chỗ học sinh cần kiểm tra: vị trí ký tự trong văn bản đề, ảnh cắt nguồn, phương án thay thế."""
    items: list[dict[str, Any]] = []
    diag = rec.get("diagram") or {}
    need_crops = bool(diag.get("blocking")) or any(s.get("blocking") for s in rec.get("uncertain_spans") or ())
    decoded_img = None
    if need_crops and image_bytes:
        try:
            from PIL import Image

            with Image.open(io.BytesIO(image_bytes)) as opened:
                decoded_img = opened.convert("RGB")
        except Exception:  # noqa: BLE001 — ảnh xem trước không được làm hỏng tuyến
            decoded_img = None

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
            "crop_data_url": _crop_data_url_img(decoded_img, s.get("bbox")) if decoded_img is not None else _crop_data_url(image_bytes, s.get("bbox")),
            "source": "local_ocr",
        })
        if len(items) >= MAX_REVIEW_ITEMS:
            break
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
            "crop_data_url": (_crop_data_url_img(decoded_img, fig, max_h=160) if decoded_img is not None else _crop_data_url(image_bytes, fig, max_h=160)) if fig else None,
            "source": "local_ocr",
        })
    return items


def summarize_for_provenance(rec: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_version": LOCAL_OCR_ROUTE_VERSION,
        "reconcile_version": OCR_RECONCILE_VERSION,
        "extraction_verified": bool(rec.get("extraction_verified")),
        "ocr_decision": rec.get("ocr_decision") or (
            "LOCAL_OCR_ACCEPT" if rec.get("extraction_verified") else "LOCAL_OCR_REVIEW_REQUIRED"
        ),
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
