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


def _reread(img, boxes: list, tessdata: str) -> dict:
    """Đọc lại từng vùng tranh chấp bằng hai bộ nhận dạng KHÁC lượt đọc chính:
    RapidOCR rec Latin PP-OCRv5 (chỉ nhận dạng, không phát hiện) và Tesseract `eng` một dòng phóng to ×3."""
    import io as _io

    import tesserocr
    from PIL import Image
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
    t0 = time.perf_counter()
    out = []
    for b in boxes:
        x0, y0, x1, y1 = (int(v) for v in b)
        pad = max(2, int(0.15 * (y1 - y0)))
        crop = img.crop((max(0, x0 - pad), max(0, y0 - pad), min(img.width, x1 + pad), min(img.height, y1 + pad)))
        buf = _io.BytesIO()
        crop.save(buf, format="PNG")
        readings = {}
        try:
            r = lat(buf.getvalue(), use_det=False, use_cls=False, use_rec=True)
            txts = list(getattr(r, "txts", None) or ())
            readings["rapidocr_latin_rec"] = str(txts[0]).strip() if txts else ""
        except Exception as exc:  # noqa: BLE001
            readings["rapidocr_latin_rec_error"] = f"{type(exc).__name__}"
        try:
            g = crop.convert("L")
            g = g.resize((max(1, g.width * 3), max(1, g.height * 3)), Image.Resampling.LANCZOS)
            api.SetImage(g)
            readings["tesseract_eng_line"] = (api.GetUTF8Text() or "").strip()
        except Exception as exc:  # noqa: BLE001
            readings["tesseract_eng_line_error"] = f"{type(exc).__name__}"
        out.append(readings)
    return {"readings": out, "ms": round((time.perf_counter() - t0) * 1000.0, 2)}


def _handle(req: dict) -> dict:
    from PIL import Image

    raw = base64.b64decode(req["image_b64"])
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    if req.get("op") == "reread":
        return {"id": req.get("id"), "ok": True, **_reread(img, req.get("boxes") or [], req["tessdata"])}
    out: dict = {"id": req.get("id"), "ok": True, "width": img.width, "height": img.height, "engines": {}}
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
