# -*- coding: utf-8 -*-
"""Local OCR sidecar worker — chạy trong interpreter OCR riêng (`LOCAL_OCR_PYTHON`).

Tầng trên cùng chỉ dùng stdlib; engine (`tesserocr`, `rapidocr`) được nạp lười ở lần nhận
dạng đầu tiên, để backend sản phẩm không phải cài/nạp mô hình OCR nào trong tiến trình
FastAPI. Giao thức: mỗi dòng stdin là một JSON
`{"id", "image_b64", "engines": [...], "tessdata"?, "tess_lang"?}`; mỗi dòng stdout là một JSON
kết quả. Không ghi ảnh ra đĩa, không giữ ảnh sau khi trả lời.

Đầu ra mỗi engine: dòng (reading order của engine) kèm từng từ, hộp bao `[x0, y0, x1, y1]`
theo pixel ảnh gửi vào và độ tin cậy THÔ của engine (chưa hiệu chuẩn — không phải xác suất).
"""
from __future__ import annotations

import base64
import io
import json
import sys
import time

LOCAL_OCR_WORKER_VERSION = "local-ocr-worker/3"
_STATE: dict = {}


def _box4(points) -> list[int]:
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    return [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]


def _binarized_for_tesseract(img):
    """Ảnh chụp giấy xám/tối (nền không trắng): xám hoá + giãn tương phản + ngưỡng toàn cục theo trung vị."""
    from PIL import ImageOps

    g = ImageOps.autocontrast(img.convert("L"), cutoff=2)
    hist = g.histogram()
    total = sum(hist)
    acc, median = 0, 128
    for v, c in enumerate(hist):
        acc += c
        if acc >= total / 2:
            median = v
            break
    thr = max(40, int(median * 0.75))
    return g.point(lambda p: 255 if p > thr else 0).convert("RGB")


def _tesseract(img, tessdata: str, lang: str) -> dict:
    out = _tesseract_pass(img, tessdata, lang)
    if not out["lines"]:
        retry = _tesseract_pass(_binarized_for_tesseract(img), tessdata, lang)
        retry["preprocess"] = "autocontrast_median_threshold_retry"
        retry["ms"] = round(out["ms"] + retry["ms"], 2)
        return retry
    return out


def _tesseract_pass(img, tessdata: str, lang: str) -> dict:
    import tesserocr
    from tesserocr import PSM, RIL, iterate_level

    key = ("tess", tessdata, lang)
    api = _STATE.get(key)
    if api is None:
        api = tesserocr.PyTessBaseAPI(path=tessdata, lang=lang, psm=PSM.AUTO)
        _STATE[key] = api
    t0 = time.perf_counter()
    api.SetImage(img)
    api.Recognize()
    lines: list[dict] = []
    it = api.GetIterator()
    if it is not None:
        cur: dict | None = None
        for w in iterate_level(it, RIL.WORD):
            try:
                txt = (w.GetUTF8Text(RIL.WORD) or "").strip()
            except RuntimeError:
                continue
            if w.IsAtBeginningOf(RIL.TEXTLINE) or cur is None:
                try:
                    lb = list(w.BoundingBox(RIL.TEXTLINE))
                    lconf = round(float(w.Confidence(RIL.TEXTLINE)), 2)
                except RuntimeError:
                    lb, lconf = None, None
                cur = {"bbox": lb, "conf": lconf, "words": []}
                lines.append(cur)
            if not txt:
                continue
            cur["words"].append(
                {"text": txt, "conf": round(float(w.Confidence(RIL.WORD)), 2), "bbox": list(w.BoundingBox(RIL.WORD))}
            )
    out_lines = []
    for ln in lines:
        if not ln["words"]:
            continue
        if ln["bbox"] is None:
            ws = ln["words"]
            ln["bbox"] = [min(w["bbox"][0] for w in ws), min(w["bbox"][1] for w in ws),
                          max(w["bbox"][2] for w in ws), max(w["bbox"][3] for w in ws)]
        ln["text"] = " ".join(w["text"] for w in ln["words"])
        out_lines.append(ln)
    return {
        "engine": f"tesseract-{lang}",
        "engine_version": tesserocr.tesseract_version().splitlines()[0],
        "model": tessdata.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1],
        "lines": out_lines,
        "ms": round((time.perf_counter() - t0) * 1000.0, 2),
    }


def _rapid(img_bytes: bytes) -> dict:
    eng = _STATE.get("rapid")
    if eng is None:
        from rapidocr import RapidOCR

        eng = RapidOCR(params={"Global.log_level": "error"})
        _STATE["rapid"] = eng
    import rapidocr

    t0 = time.perf_counter()
    r = eng(img_bytes, return_word_box=True)
    lines: list[dict] = []
    boxes = r.boxes if r.boxes is not None else ()
    words_all = getattr(r, "word_results", None) or ()
    for idx, (box, txt, sc) in enumerate(zip(boxes, r.txts or (), r.scores or ())):
        words = []
        if idx < len(words_all):
            for wt in words_all[idx] or ():
                try:
                    w_txt, w_sc, w_box = wt
                except (TypeError, ValueError):
                    continue
                if str(w_txt).strip():
                    words.append({"text": str(w_txt).strip(), "conf": round(float(w_sc) * 100.0, 2), "bbox": _box4(w_box)})
        lines.append({"text": str(txt).strip(), "conf": round(float(sc) * 100.0, 2), "bbox": _box4(box), "words": words})
    return {
        "engine": "rapidocr",
        "engine_version": f"rapidocr {getattr(rapidocr, '__version__', 'UNKNOWN')}",
        "model": "PP-OCRv6_det_small+PP-OCRv6_rec_small(default)",
        "lines": lines,
        "ms": round((time.perf_counter() - t0) * 1000.0, 2),
    }


def _estimate_crop_bg_and_mask(g_crop):
    """Nhị phân hoá cục bộ đơn giản trên ảnh xám crop để tách CC chữ và phân tích hình học ký tự."""
    w, h = g_crop.size
    raw = g_crop.tobytes()
    if not raw:
        return w, h, raw, 255, 255, []
    sorted_vals = sorted(raw)
    n = len(sorted_vals)
    fg_min = sorted_vals[0]
    bg = sorted_vals[min(n - 1, int(0.85 * n))]
    if bg - fg_min < 25:
        return w, h, raw, bg, fg_min, [False] * n
    thr = max(35, min(225, int(fg_min + 0.56 * (bg - fg_min))))
    return w, h, raw, bg, fg_min, [v < thr for v in raw]


def _extract_ccs(mask: list[bool], w: int, h: int) -> list[dict]:
    """Trích các thành phần liên thông 8-hướng cùng hộp bao và diện tích."""
    n = w * h
    if not mask or len(mask) != n:
        return []
    seen = bytearray(n)
    ccs: list[dict] = []
    for idx in range(n):
        if not mask[idx] or seen[idx]:
            continue
        stack = [idx]
        seen[idx] = 1
        pts: list[int] = []
        x0 = w
        y0 = h
        x1 = 0
        y1 = 0
        while stack:
            cur = stack.pop()
            pts.append(cur)
            y, x = divmod(cur, w)
            if x < x0:
                x0 = x
            if x + 1 > x1:
                x1 = x + 1
            if y < y0:
                y0 = y
            if y + 1 > y1:
                y1 = y + 1
            for dy in (-1, 0, 1):
                ny = y + dy
                if 0 <= ny < h:
                    base = ny * w
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx = x + dx
                        if 0 <= nx < w:
                            ni = base + nx
                            if mask[ni] and not seen[ni]:
                                seen[ni] = 1
                                stack.append(ni)
        ccs.append({
            "x0": x0, "y0": y0, "x1": x1, "y1": y1,
            "w": x1 - x0, "h": y1 - y0,
            "cx": (x0 + x1) / 2.0, "cy": (y0 + y1) / 2.0,
            "area": len(pts), "pts": pts,
        })
    return ccs


def _strip_edge_bleed(g_crop, pad_x: int, _pad_right: int | None = None):
    """Loại mảnh mực rò từ ô hàng xóm dính sát mép trái/phải trong vùng đệm `pad_x` (giữ dấu phẩy trên nhỏ ở góc trên phải)."""
    w, h, raw, bg, _fg_min, mask = _estimate_crop_bg_and_mask(g_crop)
    ccs = _extract_ccs(mask, w, h)
    if len(ccs) <= 1 or w < 6:
        return g_crop
    bleed_limit = max(2, pad_x + 2)
    cand_left = [c for c in ccs if c["x0"] <= 1 and c["x1"] <= bleed_limit and c["w"] < 0.25 * w]
    cand_right = [c for c in ccs if c["x1"] >= w - 1 and c["x0"] >= w - 1 - bleed_limit and c["w"] < 0.25 * w]
    cand_set = {id(c) for c in cand_left + cand_right}
    core_ccs = [c for c in ccs if id(c) not in cand_set] or ccs
    core_x1 = max(c["x1"] for c in core_ccs)
    bleed_ccs = list(cand_left)
    for c in cand_right:
        is_upper_prime = (
            c["y1"] <= int(0.55 * h)
            and c["w"] <= max(4, int(0.16 * w))
            and (c["x0"] - core_x1) <= max(2, int(0.10 * h))
        )
        if not is_upper_prime:
            bleed_ccs.append(c)
    if not bleed_ccs or len(bleed_ccs) >= len(ccs):
        return g_crop
    buf = bytearray(raw)
    bg_byte = max(0, min(255, int(bg)))
    for c in bleed_ccs:
        for p_idx in c["pts"]:
            buf[p_idx] = bg_byte
    from PIL import Image

    return Image.frombytes("L", (w, h), bytes(buf))


def _analyze_crop_glyph_topology(g_clean) -> dict:
    """Phân tích cấu trúc hình học điểm ảnh thuần trên crop đã khử rò biên (KHÔNG phụ thuộc ngôn ngữ OCR)."""
    w, h, raw, bg, fg_min, mask = _estimate_crop_bg_and_mask(g_clean)
    contrast = int(bg - fg_min)
    ccs_all = _extract_ccs(mask, w, h)
    big_exists = any(c["area"] >= 4 for c in ccs_all)
    ccs = [c for c in ccs_all if (c["area"] >= 2 if big_exists else c["area"] >= 1)]
    ccs.sort(key=lambda c: (c["x0"], c["y0"]))

    sharp_steps: list[int] = []
    for y in range(h):
        base = y * w
        for x in range(w):
            i = base + x
            if not mask[i]:
                continue
            max_step = 0
            is_edge = False
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    ni = ny * w + nx
                    if not mask[ni]:
                        is_edge = True
                        diff = abs(raw[ni] - raw[i])
                        if diff > max_step:
                            max_step = diff
            if is_edge:
                sharp_steps.append(max_step)
    sharp_frac = (
        sum(1 for st in sharp_steps if st >= max(24, int(0.38 * max(1, contrast)))) / float(max(1, len(sharp_steps)))
        if sharp_steps else 0.0
    )
    blurry = contrast < 40 or not ccs or sharp_frac < 0.32

    has_superscript_cc = False
    superscript_aspect: float | None = None
    superscript_digit_hint: str | None = None
    max_cc_h = max((c["h"] for c in ccs), default=0)
    for idx, c_sup in enumerate(ccs):
        if c_sup["w"] < 3 or c_sup["h"] < 3 or (c_sup["w"] / float(c_sup["h"])) < 0.40:
            continue
        prior = [
            c for j, c in enumerate(ccs)
            if j != idx and c["x0"] < c_sup["x0"] and c["h"] >= max(6, int(0.45 * max_cc_h)) and c["cx"] < c_sup["cx"]
            and c_sup["x0"] >= c["x1"] - max(2, int(0.25 * c["w"]))
        ]
        for c_base in prior:
            if (
                c_sup["h"] <= 0.92 * c_base["h"]
                and c_sup["y0"] <= c_base["y0"] + max(1, int(0.15 * c_base["h"]))
                and (c_base["y1"] - c_sup["y1"]) >= max(4, int(0.35 * c_base["h"]))
            ):
                has_superscript_cc = True
                superscript_aspect = round(c_sup["w"] / float(max(1, c_sup["h"])), 3)
                if c_sup["h"] >= 5 and c_sup["w"] >= 4:
                    sup_pts = {(p % w, p // w) for p in c_sup["pts"]}
                    bot_y = max(c_sup["y0"], c_sup["y1"] - max(1, int(0.28 * c_sup["h"])))
                    bot_xs = {px for px, py in sup_pts if py >= bot_y}
                    left_bot = any(px <= c_sup["x0"] + max(0, c_sup["w"] // 3) for px in bot_xs)
                    if len(bot_xs) >= 0.65 * c_sup["w"] and left_bot:
                        superscript_digit_hint = "2"
                break
        if has_superscript_cc:
            break

    has_radical_stroke = False
    for idx, c in enumerate(ccs):
        if c["h"] < 12 or c["w"] < 7:
            continue
        pts = {(p % w, p // w) for p in c["pts"]}
        top_cut = c["y0"] + max(2, int(0.24 * c["h"]))
        top_left_limit = c["x0"] + int(0.35 * c["w"])
        top_right_start = c["x0"] + int(0.45 * c["w"])
        top_left_pts = [1 for px, py in pts if py <= top_cut and px < top_left_limit]
        top_right_pts = [1 for px, py in pts if py <= top_cut and px >= top_right_start]
        mid_left_pts = [
            1 for px, py in pts
            if c["y0"] + int(0.30 * c["h"]) <= py <= c["y0"] + int(0.80 * c["h"])
            and px <= c["x0"] + int(0.30 * c["w"])
        ]
        bot_pts = [
            1 for px, py in pts
            if py >= c["y0"] + int(0.74 * c["h"])
            and c["x0"] + int(0.15 * c["w"]) <= px <= c["x0"] + int(0.75 * c["w"])
        ]
        mid_row_spans = []
        for ry in range(c["y0"] + int(0.45 * c["h"]), c["y0"] + int(0.82 * c["h"]) + 1):
            rxs = [px for px, py in pts if py == ry]
            if rxs:
                mid_row_spans.append(len(rxs) / float(max(1, c["w"])))
        max_mid_span = max(mid_row_spans, default=1.0)
        others = [o for j, o in enumerate(ccs) if j != idx and o["h"] >= 6]
        taller_than_neighbor = (not others) or any(
            c["h"] >= 1.22 * o["h"] and c["y0"] <= o["y0"] - 2 for o in others
        )
        if not top_left_pts and top_right_pts and mid_left_pts and bot_pts and max_mid_span <= 0.58 and taller_than_neighbor:
            has_radical_stroke = True
            break

    has_perp_t_junction = False
    for c in ccs:
        if c["w"] < 5 or c["h"] < 5:
            continue
        pts = {(p % w, p // w) for p in c["pts"]}
        bot_start = c["y1"] - max(1, int(0.28 * c["h"]))
        stem_end = c["y0"] + max(2, int(0.66 * c["h"]))
        bot_xs = {px for px, py in pts if py >= bot_start}
        stem_pts = [(px, py) for px, py in pts if c["y0"] <= py < stem_end]
        if not bot_xs or not stem_pts:
            continue
        bot_span = (max(bot_xs) - min(bot_xs) + 1) / float(max(1, c["w"]))
        row_spans = []
        for ry in range(c["y0"], stem_end):
            rxs = [px for px, py in stem_pts if py == ry]
            if rxs:
                row_spans.append((max(rxs) - min(rxs) + 1) / float(max(1, c["w"])))
        avg_stem_span = sum(row_spans) / float(len(row_spans)) if row_spans else 1.0
        stem_cx = sum(px for px, _ in stem_pts) / float(len(stem_pts))
        rel_stem_x = (stem_cx - c["x0"]) / float(max(1, c["w"]))
        has_left_arm = any(px < stem_cx - max(1.0, 0.15 * c["w"]) for px in bot_xs)
        has_right_arm = any(px > stem_cx + max(1.0, 0.15 * c["w"]) for px in bot_xs)
        if bot_span >= 0.65 and avg_stem_span <= 0.42 and 0.28 <= rel_stem_x <= 0.72 and has_left_arm and has_right_arm:
            has_perp_t_junction = True
            break

    has_parallel_bars = False
    tall_bars = [
        c for c in ccs
        if c["h"] >= max(7, int(0.65 * max_cc_h)) and c["w"] <= 0.50 * c["h"]
    ]
    for a, b in zip(tall_bars, tall_bars[1:]):
        min_h, max_h = min(a["h"], b["h"]), max(a["h"], b["h"])
        gap = b["x0"] - a["x1"]
        if (
            gap >= 1
            and gap <= max_h
            and (min_h / float(max(1, max_h))) >= 0.75
            and abs(a["y0"] - b["y0"]) <= 0.25 * max_h
            and abs(a["y1"] - b["y1"]) <= 0.25 * max_h
        ):
            has_parallel_bars = True
            break

    has_equals_bars = False
    eq_ccs = [c for c in ccs if c["area"] >= 3]
    if len(eq_ccs) == 2:
        a_cc, b_cc = sorted(eq_ccs, key=lambda c: c["cy"])
        ah_bar, aw_bar = max(1, a_cc["h"]), a_cc["w"]
        bh_bar, bw_bar = max(1, b_cc["h"]), b_cc["w"]
        ov_x = max(0, min(a_cc["x1"], b_cc["x1"]) - max(a_cc["x0"], b_cc["x0"]))
        v_gap = b_cc["y0"] - a_cc["y1"]
        if (
            aw_bar >= max(4, int(1.8 * ah_bar))
            and bw_bar >= max(4, int(1.8 * bh_bar))
            and 1 <= v_gap <= max(3, int(0.55 * h))
            and ov_x / float(max(1, min(aw_bar, bw_bar))) >= 0.65
            and min(aw_bar, bw_bar) / float(max(1, max(aw_bar, bw_bar))) >= 0.60
        ):
            has_equals_bars = True

    return {
        "blurry": blurry,
        "contrast": contrast,
        "sharp_frac": round(sharp_frac, 3),
        "cc_count": len(ccs),
        "has_superscript_cc": has_superscript_cc,
        "superscript_aspect": superscript_aspect,
        "superscript_digit_hint": superscript_digit_hint,
        "has_radical_stroke": has_radical_stroke,
        "has_perp_t_junction": has_perp_t_junction,
        "has_parallel_bars": has_parallel_bars,
        "has_equals_bars": has_equals_bars,
    }


def _reread(img, boxes: list, tessdata: str) -> dict:
    """Đọc lại từng vùng tranh chấp bằng hai bộ nhận dạng KHÁC lượt đọc chính:
    RapidOCR rec Latin PP-OCRv5 (chỉ nhận dạng, không phát hiện) và Tesseract `eng`/`vie` một dòng phóng to ×3."""
    import io as _io
    import os as _os

    import tesserocr
    from PIL import Image, ImageOps
    from rapidocr import LangRec, ModelType, OCRVersion, RapidOCR
    from tesserocr import PSM

    lat = _STATE.get("rapid_latin")
    if lat is None:
        lat = RapidOCR(params={
            "Global.log_level": "error",
            "Rec.lang_type": LangRec.LATIN,
            "Rec.ocr_version": OCRVersion.PPOCRV5,
            "Rec.model_type": ModelType.MOBILE,
        })
        _STATE["rapid_latin"] = lat
    key = ("tess_line", tessdata)
    api = _STATE.get(key)
    if api is None:
        api = tesserocr.PyTessBaseAPI(path=tessdata, lang="eng", psm=PSM.SINGLE_LINE)
        _STATE[key] = api
    api_vie = None
    if _os.path.isfile(_os.path.join(tessdata, "vie.traineddata")):
        key_vie = ("tess_line_vie", tessdata)
        api_vie = _STATE.get(key_vie)
        if api_vie is None:
            api_vie = tesserocr.PyTessBaseAPI(path=tessdata, lang="vie", psm=PSM.SINGLE_LINE)
            _STATE[key_vie] = api_vie

    t0 = time.perf_counter()
    crop_s = topo_s = lat_s = eng_s = vie_s = 0.0
    out = []
    for b in boxes:
        tc0 = time.perf_counter()
        x0, y0, x1, y1 = (int(v) for v in b)
        h_box = max(1, y1 - y0)
        pad_x = max(2, min(6, int(0.06 * h_box)))
        pad_top = max(3, int(0.24 * h_box))
        pad_bot = max(3, int(0.18 * h_box))
        crop = img.crop((
            max(0, x0 - pad_x),
            max(0, y0 - pad_top),
            min(img.width, x1 + pad_x),
            min(img.height, y1 + pad_bot),
        ))
        g_clean = _strip_edge_bleed(crop.convert("L"), pad_x)
        tc1 = time.perf_counter()
        crop_s += tc1 - tc0
        topo = _analyze_crop_glyph_topology(g_clean)
        tc2 = time.perf_counter()
        topo_s += tc2 - tc1
        g_rapid = ImageOps.expand(g_clean, border=6, fill=255).convert("RGB")
        buf = _io.BytesIO()
        g_rapid.save(buf, format="PNG")
        readings: dict = {"glyph_topology": topo}
        tl0 = time.perf_counter()
        try:
            r = lat(buf.getvalue(), use_det=False, use_cls=False, use_rec=True)
            txts = list(getattr(r, "txts", None) or ())
            readings["rapidocr_latin_rec"] = str(txts[0]).strip() if txts else ""
        except Exception as exc:  # noqa: BLE001
            readings["rapidocr_latin_rec_error"] = f"{type(exc).__name__}"
        lat_s += time.perf_counter() - tl0
        try:
            g_pad = ImageOps.expand(g_clean, border=16, fill=255)
            g = g_pad.resize((max(1, g_pad.width * 3), max(1, g_pad.height * 3)), Image.Resampling.LANCZOS)
            te0 = time.perf_counter()
            api.SetImage(g)
            readings["tesseract_eng_line"] = (api.GetUTF8Text() or "").strip()
            readings["tesseract_eng_line_conf"] = int(api.MeanTextConf())
            eng_s += time.perf_counter() - te0
            if api_vie is not None:
                tv0 = time.perf_counter()
                api_vie.SetImage(g)
                readings["tesseract_vie_line"] = (api_vie.GetUTF8Text() or "").strip()
                readings["tesseract_vie_line_conf"] = int(api_vie.MeanTextConf())
                vie_s += time.perf_counter() - tv0
        except Exception as exc:  # noqa: BLE001
            readings["tesseract_eng_line_error"] = f"{type(exc).__name__}"
        out.append(readings)
    return {
        "worker_version": LOCAL_OCR_WORKER_VERSION,
        "readings": out,
        "ms": round((time.perf_counter() - t0) * 1000.0, 2),
        "timings": {
            "crop_ms": round(crop_s * 1000.0, 2),
            "topology_ms": round(topo_s * 1000.0, 2),
            "latin_rec_ms": round(lat_s * 1000.0, 2),
            "tess_eng_ms": round(eng_s * 1000.0, 2),
            "tess_vie_ms": round(vie_s * 1000.0, 2),
        },
    }


def _handle(req: dict) -> dict:
    from PIL import Image

    td0 = time.perf_counter()
    raw = base64.b64decode(req["image_b64"])
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    decode_ms = round((time.perf_counter() - td0) * 1000.0, 2)
    if req.get("op") == "reread":
        return {"id": req.get("id"), "ok": True, "decode_ms": decode_ms, **_reread(img, req.get("boxes") or [], req["tessdata"])}
    out: dict = {
        "id": req.get("id"),
        "ok": True,
        "worker_version": LOCAL_OCR_WORKER_VERSION,
        "decode_ms": decode_ms,
        "width": img.width,
        "height": img.height,
        "engines": {},
    }
    for name in req.get("engines") or ("tesseract", "rapidocr"):
        try:
            if name == "tesseract":
                out["engines"][name] = _tesseract(img, req["tessdata"], req.get("tess_lang") or "vie")
            elif name == "rapidocr":
                out["engines"][name] = _rapid(raw)
        except Exception as exc:  # noqa: BLE001 — một engine hỏng không được làm chết worker
            out["engines"][name] = {"engine": name, "error": f"{type(exc).__name__}: {exc}"[:300], "lines": []}
    return out


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            if req.get("op") == "ping":
                resp = {"id": req.get("id"), "ok": True, "pong": True}
            else:
                resp = _handle(req)
        except Exception as exc:  # noqa: BLE001
            resp = {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:300]}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
