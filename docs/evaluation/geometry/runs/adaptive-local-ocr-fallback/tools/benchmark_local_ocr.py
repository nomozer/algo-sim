# -*- coding: utf-8 -*-
"""Benchmark local OCR engines for the photo → problem-text step (run `adaptive-local-ocr-fallback`).

Two processes, two interpreters (the shared backend venv is never pip-installed into):

* PARENT — backend venv, run from `backend/`. Builds the labelled image set, runs the PRODUCT
  preprocessing (`normalize_image` → `detect_problem_regions` → `prepared_image`, i.e. exactly the bytes
  the Vision provider would receive), spawns one child per engine, scores outputs against
  `ground_truth_text` (oracle = the rendering source text, independent of every OCR engine), evaluates the
  candidate local-only acceptance gate, and writes ONE JSON receipt. Tables are generated from that JSON.
* CHILD — scratch OCR venv (`rapidocr`, `onnxruntime`, `tesserocr`), stdlib-only top level.

    cd backend && PYTHONIOENCODING=utf-8 ALLOW_LIVE_AI=0 .venv/Scripts/python.exe \
      ../docs/evaluation/geometry/runs/adaptive-local-ocr-fallback/tools/benchmark_local_ocr.py \
      --ocr-python <scratch>/ocr-venv/Scripts/python.exe --tessdata-best <dir> --tessdata-fast <dir> \
      --work <scratch>/ocr-work --out ../docs/evaluation/geometry/runs/adaptive-local-ocr-fallback/ocr_benchmark.json

0 network calls to any model provider: no Vision call is made or mocked here.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

# ───────────────────────────── CHILD (OCR venv, stdlib top level) ─────────────────────────────

ENGINES = {
    # name: (family, config)
    "tesseract_vie_best": ("tesseract", {"tessdata": "best", "lang": "vie"}),
    "tesseract_vie_fast": ("tesseract", {"tessdata": "fast", "lang": "vie"}),
    "rapidocr_ppocrv6_small": ("rapidocr", {"det": "small", "rec": "small", "ver": "PP-OCRv6"}),
    "rapidocr_ppocrv6_medium": ("rapidocr", {"det": "medium", "rec": "medium", "ver": "PP-OCRv6"}),
    "rapidocr_ppocrv5_latin": ("rapidocr", {"det": "small", "rec": "mobile", "ver": "PP-OCRv5", "lang": "latin"}),
}


def _peak_rss_bytes() -> int | None:
    if os.name != "nt":
        try:
            import resource

            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        except Exception:  # noqa: BLE001
            return None
    import ctypes
    from ctypes import wintypes

    class PMC(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

    c = PMC()
    c.cb = ctypes.sizeof(PMC)
    k32 = ctypes.WinDLL("kernel32")
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL("psapi")
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
    if not psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb):
        return None
    return int(c.PeakWorkingSetSize)


def _child(engine: str, items_path: str, out_path: str, tess_best: str, tess_fast: str) -> None:
    family, cfg = ENGINES[engine]
    items = json.loads(Path(items_path).read_text(encoding="utf-8"))
    from PIL import Image

    rss_after_imports = _peak_rss_bytes()
    t_init0 = time.perf_counter()
    model_files: list[str] = []
    if family == "tesseract":
        import tesserocr
        from tesserocr import PSM, RIL

        td = tess_best if cfg["tessdata"] == "best" else tess_fast
        api = tesserocr.PyTessBaseAPI(path=td, lang=cfg["lang"])
        api2 = tesserocr.PyTessBaseAPI(path=td, lang=cfg["lang"], psm=PSM.SINGLE_BLOCK)
        model_files = [str(Path(td) / f"{cfg['lang']}.traineddata")]
        version = tesserocr.tesseract_version().splitlines()[0]

        def run(img):
            api.SetImage(img)
            api.Recognize()
            lines = []
            it = api.GetIterator()
            if it is None:
                return lines
            for w in tesserocr.iterate_level(it, RIL.TEXTLINE):
                try:
                    t = (w.GetUTF8Text(RIL.TEXTLINE) or "").strip()
                except RuntimeError:  # empty line element ("No text returned")
                    continue
                if t:
                    lines.append({"text": t, "conf": round(float(w.Confidence(RIL.TEXTLINE)), 2),
                                  "bbox": list(w.BoundingBox(RIL.TEXTLINE))})
            return lines

        def run_pass2(img):
            g = img.convert("L")
            g = g.resize((int(g.width * 1.5), int(g.height * 1.5)), Image.Resampling.LANCZOS)
            api2.SetImage(g)
            return api2.GetUTF8Text()
    else:
        from rapidocr import LangRec, ModelType, OCRVersion, RapidOCR
        import rapidocr

        params = {"Global.log_level": "error",
                  "Det.ocr_version": OCRVersion(cfg["ver"]) if cfg["ver"] == "PP-OCRv6" else OCRVersion.PPOCRV4,
                  "Det.model_type": ModelType(cfg["det"]) if cfg["ver"] == "PP-OCRv6" else ModelType.MOBILE,
                  "Rec.ocr_version": OCRVersion(cfg["ver"]), "Rec.model_type": ModelType(cfg["rec"])}
        if cfg["ver"] == "PP-OCRv5":
            params["Det.ocr_version"] = OCRVersion.PPOCRV6
            params["Det.model_type"] = ModelType.SMALL
            params["Rec.lang_type"] = LangRec(cfg["lang"])
        eng = RapidOCR(params=params)
        version = f"rapidocr {rapidocr.__version__ if hasattr(rapidocr, '__version__') else 'UNKNOWN'}"

        def run(img):
            r = eng(img)
            out = []
            for txt, sc, box in zip(r.txts or (), r.scores or (), r.boxes if r.boxes is not None else ()):
                xs = [float(p[0]) for p in box]
                ys = [float(p[1]) for p in box]
                out.append({"text": str(txt).strip(), "conf": round(float(sc) * 100.0, 2),
                            "bbox": [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]})
            return out

        run_pass2 = None

    results = []
    cold_ms = None
    for i, it in enumerate(items):
        img = Image.open(it["path"]).convert("RGB")
        t0 = time.perf_counter()
        lines = run(img)
        t1 = time.perf_counter()
        if i == 0:
            cold_ms = round((t1 - t_init0) * 1000.0, 1)
        t2 = time.perf_counter()
        run(img)
        warm_ms = round((time.perf_counter() - t2) * 1000.0, 1)
        p2 = run_pass2(img) if run_pass2 else None
        results.append({"item_id": it["item_id"], "lines": lines, "first_run_ms": round((t1 - t0) * 1000.0, 1),
                        "warm_ms": warm_ms, "pass2_text": p2})
    if family == "rapidocr":
        import rapidocr as _r

        mdir = Path(_r.__file__).parent / "models"
        used = {"small": ["PP-OCRv6_det_small.onnx", "PP-OCRv6_rec_small.onnx"],
                "medium": ["PP-OCRv6_det_medium.onnx", "PP-OCRv6_rec_medium.onnx"],
                "latin": ["PP-OCRv6_det_small.onnx", "latin_PP-OCRv5_rec_mobile.onnx"]}
        key = "latin" if cfg["ver"] == "PP-OCRv5" else cfg["rec"]
        model_files = [str(mdir / f) for f in used[key] + ["ch_ppocr_mobile_v2.0_cls_mobile.onnx"]]
    Path(out_path).write_text(json.dumps({
        "engine": engine, "family": family, "config": cfg, "engine_version": version,
        "cold_ms_init_plus_first_item": cold_ms, "peak_rss_bytes": _peak_rss_bytes(),
        "rss_after_imports_bytes": rss_after_imports, "model_files_all": model_files, "items": results,
    }, ensure_ascii=False), encoding="utf-8")


# ───────────────────────────── PARENT (backend venv) ─────────────────────────────

RUN_DIR = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[6]
CORPUS = ROOT / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene" / "CORPUS.json"
STRESS_FONT = Path("C:/Windows/Fonts/cambria.ttc")

#: Labelled symbol-stress set. Wording is generic Toán 11–12 phrasing; every math symbol class the task
#: names appears at least once. It is the CALIBRATION set together with the photo corpus (not held out).
STRESS_TEXTS = {
    "s01_vuong_goc_song_song": "Cho hình chóp S.ABCD có SA ⊥ (ABCD), AB ∥ CD và góc ∠SBA = 60°. Tính khoảng cách từ A đến mặt phẳng (SBC).",
    "s02_phay_can_phan_so": "Cho lăng trụ đứng ABC.A′B′C′ có AA′ = 2√3, AB = a/2 và BC = 3,5. Tính thể tích khối lăng trụ ABC.A′B′C′.",
    "s03_dau_tru_toa_do": "Trong không gian Oxyz, cho mặt phẳng (P): x − 2y + z − 1 = 0 và điểm A(1; −2; 3). Tính khoảng cách từ A đến (P).",
    "s04_luy_thua_chi_so": "Cho tứ diện ABCD có AB = a√2, AC = 2a và thể tích V = a³/6. Gọi M₁, M₂ lần lượt là trung điểm của BC và CD.",
    "s05_dau_tieng_viet": "Cho hình hộp chữ nhật ABCD.A′B′C′D′ có AB = 3, AD = 4, AA′ = 5. Gọi I là giao điểm của AC′ và mặt phẳng (A′BD). Tính độ dài đoạn thẳng AI.",
}

ALLOWED_MATH = set("⊥∥∠′'√αβγπ−-+=<>≤≥()[]{};:,./°²³₁₂₃·×÷%|")
VOWELS = set("aăâeêioôơuưyáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ")
#: Geometry vocabulary that is NEVER written without diacritics in a correct Vietnamese problem. A token
#: equal to one of these stripped forms means the engine dropped marks — the text is not reliable.
#: Only stripped forms that are NOT themselves valid Vietnamese syllables (`qua`, `tam`, `trung`, `giao`,
#: `xung`, `quanh`, `canh`, `tinh`, `thang`... are valid unaccented words and were removed after the first
#: run flagged correct text — recorded in the report as a calibration finding).
STRIPPED_LEXICON = {"hinh", "chop", "diem", "duong", "phang", "vuong", "goc", "thiet", "dien", "tich",
                    "cach", "tron", "giac", "tren", "luot", "doan", "mat"}
DIAGRAM_CUES = ("như hình vẽ", "hình vẽ bên", "hình bên", "hình dưới", "xem hình", "theo hình")


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def norm_strict(s: str) -> str:
    return re.sub(r"\s+", " ", _nfc(s)).strip()


_LENIENT = str.maketrans({"−": "-", "–": "-", "′": "'", "’": "'", "‘": "'", "“": '"', "”": '"'})


def norm_lenient(s: str) -> str:
    """Typographic equivalences that carry no math difference downstream (minus sign, prime)."""
    s = norm_strict(s).translate(_LENIENT)
    s = re.sub(r"\s*([;,():=+\-])\s*", r"\1", s)  # spacing around operators/punctuation is not a fact
    return s


def strip_marks(s: str) -> str:
    d = unicodedata.normalize("NFD", s)
    return unicodedata.normalize("NFC", "".join(c for c in d if unicodedata.category(c) != "Mn")).replace("đ", "d").replace("Đ", "D")


def lev(a, b) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


_MATH_TOKEN = re.compile(r"\d+(?:[.,]\d+)?|[A-Z](?:'|′|[₁₂₃])?|[⊥∥∠√αβγπ°²³=<>≤≥/+\-−;]")


def math_tokens(s: str) -> list[str]:
    return [t.translate(_LENIENT) for t in _MATH_TOKEN.findall(_nfc(s))]


def _words(s: str) -> list[str]:
    return re.findall(r"\w+", _nfc(s).lower())


def _multiset_recall(gt: list[str], got: list[str]) -> tuple[int, int]:
    pool: dict[str, int] = {}
    for w in got:
        pool[w] = pool.get(w, 0) + 1
    hit = 0
    for w in gt:
        if pool.get(w, 0) > 0:
            pool[w] -= 1
            hit += 1
    return hit, len(gt)


SYMBOLS = ["⊥", "∥", "∠", "′", "√", "α", "β", "−", "²", "³", "₁", "₂", "°", "/", ",", ";", "(", ")", "="]
_SYM_LENIENT = {"−": "-", "′": "'"}


def symbol_counts(gt: str, ocr: str) -> dict[str, dict[str, int]]:
    out = {}
    for s in SYMBOLS:
        n = gt.count(s)
        if not n:
            continue
        strict = min(n, ocr.count(s))
        alt = _SYM_LENIENT.get(s)
        lenient = min(n, ocr.count(s) + (ocr.count(alt) if alt else 0))
        out[s] = {"gt": n, "strict_found": strict, "lenient_found": lenient}
    return out


def _render_stress(text: str, *, degrade: bool):
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

    font = ImageFont.truetype(str(STRESS_FONT), 30)
    width, margin, line_h = 1120, 64, 46
    lines, cur = [], ""
    for w in text.split():
        t = f"{cur} {w}".strip()
        if font.getlength(t) <= width - 2 * margin:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    img = Image.new("RGB", (width, max(480, margin * 2 + (len(lines) + 1) * line_h + 40)), (250, 248, 242))
    d = ImageDraw.Draw(img)
    y = margin
    d.text((margin, y), "Câu 1.", font=font, fill=(28, 28, 30))
    for s in lines:
        y += line_h
        d.text((margin, y), s, font=font, fill=(28, 28, 30))
    if degrade:
        img = ImageEnhance.Brightness(img.filter(ImageFilter.GaussianBlur(0.9))).enhance(0.75)
    return img


def build_items(work: Path) -> list[dict]:
    import hashlib
    import io

    from app.ingestion.image import normalize_image
    from app.ingestion.region_detector import detect_problem_regions

    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    raw_items = []
    for it in corpus["items"]:
        raw = (CORPUS.parent / it["file"]).read_bytes()
        gt = it["ground_truth_text"]
        raw_items.append({"item_id": it["id"], "set": "photo_problem_corpus", "raw": raw,
                          "gt_problem_text": gt, "gt_rendered": f"Câu 1. {gt}" if gt else "",
                          "degradations": it["degradations"], "diagram": it["diagram"],
                          "expected_outcome": it["expected_outcome"]})
    for sid, txt in STRESS_TEXTS.items():
        for degrade in (False, True):
            buf = io.BytesIO()
            _render_stress(txt, degrade=degrade).save(buf, format="PNG")
            raw_items.append({"item_id": f"{sid}{'_degraded' if degrade else ''}", "set": "symbol_stress",
                              "raw": buf.getvalue(), "gt_problem_text": txt, "gt_rendered": f"Câu 1. {txt}",
                              "degradations": ["mo_nhe", "toi_nhe"] if degrade else [], "diagram": None,
                              "expected_outcome": "ACCEPT"})
    work.mkdir(parents=True, exist_ok=True)
    items = []
    for r in raw_items:
        norm = normalize_image(r["raw"])
        reg = detect_problem_regions(norm)
        prep = reg.prepared_image
        p = work / f"{r['item_id']}.jpg"
        p.write_bytes(prep.data)
        items.append({
            "item_id": r["item_id"], "set": r["set"], "path": str(p),
            "source_sha256": hashlib.sha256(r["raw"]).hexdigest(), "prepared_sha256": prep.sha256,
            "gt_problem_text": r["gt_problem_text"], "gt_rendered": r["gt_rendered"],
            "degradations": r["degradations"], "diagram": r["diagram"], "expected_outcome": r["expected_outcome"],
            "region": {"used_crop": reg.used_crop, "has_associated_figure": reg.has_associated_figure,
                       "is_blank_or_unreadable": reg.quality.is_blank_or_unreadable,
                       "figure_blocks": sum(1 for b in reg.blocks if b.kind == "figure"),
                       "prepared_w": prep.width, "prepared_h": prep.height},
        })
    return items


def _uncovered_ink_ratio(path: str, lines: list[dict]) -> float:
    """Share of dark pixels in the OCR input that no recognised line box explains (figure ink, missed text)."""
    from PIL import Image, ImageChops, ImageDraw

    g = Image.open(path).convert("L")
    hist = g.histogram()
    mean = sum(i * c for i, c in enumerate(hist)) / max(1, g.width * g.height)
    ink = g.point(lambda v: 255 if v < mean * 0.6 else 0)
    boxes = Image.new("L", g.size, 0)
    d = ImageDraw.Draw(boxes)
    for x0, y0, x1, y1 in (ln["bbox"] for ln in lines):
        d.rectangle([x0 - 3, y0 - 3, x1 + 3, y1 + 3], fill=255)
    n_ink = ink.histogram()[255]
    n_cov = ImageChops.multiply(ink, boxes).histogram()[255]
    return round(1.0 - n_cov / n_ink, 4) if n_ink else 0.0


def gate_features(item: dict, res: dict) -> dict:
    """Features computed from OCR OUTPUT + the image only — never from ground truth."""
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC, detect_domain

    lines = res["lines"]
    label_lines = [ln for ln in lines if len(ln["text"].replace(" ", "")) <= 3]
    body_lines = [ln for ln in lines if ln not in label_lines]
    body = " ".join(ln["text"] for ln in body_lines)
    reasons: list[str] = []
    if len(body.strip()) < 10:
        reasons.append("EMPTY_OR_SHORT_TEXT")
    bad_chars = sorted({c for c in body if not (c.isalnum() or c.isspace() or c in ALLOWED_MATH)})
    if bad_chars:
        reasons.append("UNRECOGNISED_SYMBOL")
    toks = re.findall(r"[^\W\d_]+", _nfc(body))
    no_vowel = [t for t in toks if t.islower() and len(t) >= 2 and not any(c in VOWELS for c in t)]
    stripped_hits = [t for t in toks if t.lower() in STRIPPED_LEXICON]
    if no_vowel or stripped_hits:
        reasons.append("VIETNAMESE_ORTHOGRAPHY")
    if body.count("(") != body.count(")"):
        reasons.append("RELATION_SYNTAX")
    # Coordinates: a point tuple uses ';' and has exactly 3 numeric/letter components (':' is a misread).
    for m in re.finditer(r"\b[A-Z]\s*\(([^()]*)\)", body):
        inner = m.group(1)
        if ";" in inner or ":" in inner:
            parts = [p.strip() for p in inner.split(";")]
            if ":" in inner or len(parts) != 3 or not all(re.fullmatch(r"[−-]?\d+(?:[.,]\d+)?|[a-z]", p) for p in parts):
                reasons.append("RELATION_SYNTAX")
                break
    # Object names: a plane/figure name in parentheses is uppercase or Greek, never a lowercase letter or digit;
    # an equation side is never empty; a glyph that only exists as a misread (`V3` for √3, `x°` for x², `II`
    # for ∥, a bare digit between two names for ⊥) is not a relation the text can carry.
    if (re.search(r"\((?:[a-z]|\d)\)", body) or re.search(r"=\s*=|=\s*$|^\s*=|[(;]\s*=", body)
            or re.search(r"\bV\d|[A-Za-z]°|\bII\b|[A-Z]{2,}\s+\d\s+\(", body)):
        reasons.append("RELATION_SYNTAX")
    # Vertex consistency: a primed vertex needs its unprimed base; a solid notation has no repeated letter;
    # a prism top face repeats the base letters primed; one apex/base names one notation only.
    primed = set(re.findall(r"([A-Z])[′']", body))
    plain = set(re.findall(r"([A-Z])(?![′'])", body))
    notations = re.findall(r"\b([A-Z]+)\.([A-Z][A-Z′']*)", body)
    bad_notation = any(len(set(a)) != len(a) for a, _ in notations)
    for a, b in notations:
        if ("′" in b or "'" in b) and re.sub(r"[′']", "", b) != a:
            bad_notation = True
    seen: dict[str, set[str]] = {}
    for a, b in notations:
        seen.setdefault(a, set()).add(b.translate(_LENIENT))
    if primed - plain or bad_notation or any(len(v) > 1 for v in seen.values()):
        reasons.append("VERTEX_INCONSISTENT")
    body_letters = set(re.findall(r"[A-Z]", body))
    unexplained = [ln["text"] for ln in label_lines if set(re.findall(r"[A-Z]", ln["text"])) - body_letters]
    low = body.lower()
    if unexplained or any(c in low for c in DIAGRAM_CUES):
        reasons.append("DIAGRAM_UNEXPLAINED")
    if detect_domain(body) != DOMAIN_HINH_HOC:
        reasons.append("DOMAIN_NOT_GEOMETRY")
    p2 = res.get("pass2_text")
    if p2 is not None and math_tokens(p2) != math_tokens(" ".join(ln["text"] for ln in lines)):
        reasons.append("PASS_DISAGREEMENT")
    confs = [ln["conf"] for ln in body_lines] or [0.0]
    return {"reasons": sorted(set(reasons)), "min_line_conf": min(confs), "mean_line_conf": round(statistics.fmean(confs), 2),
            "uncovered_ink_ratio": _uncovered_ink_ratio(item["path"], lines), "body_text": body,
            "bad_chars": bad_chars, "no_vowel_tokens": no_vowel[:10], "stripped_lexicon_hits": stripped_hits[:10],
            "unexplained_label_lines": unexplained}


def score(item: dict, res: dict) -> dict:
    ocr_full = "\n".join(ln["text"] for ln in res["lines"])
    body = " ".join(ln["text"] for ln in res["lines"] if len(ln["text"].replace(" ", "")) > 3)
    gt = item["gt_rendered"]
    if not gt:
        return {"has_gt": False, "ocr_chars": len(norm_strict(ocr_full))}
    g_s, o_s, b_s = norm_strict(gt), norm_strict(ocr_full), norm_strict(body)
    g_l, b_l = norm_lenient(gt), norm_lenient(body)
    gw, ow = _words(gt), _words(body)
    vi = [w for w in gw if any(ord(c) > 127 for c in w)]
    hit, n = _multiset_recall(vi, ow)
    hit_s, _ = _multiset_recall([strip_marks(w) for w in vi], [strip_marks(w) for w in ow])
    gtk, otk = math_tokens(gt), math_tokens(body)
    return {
        "has_gt": True,
        "cer_strict_full": round(lev(o_s, g_s) / max(1, len(g_s)), 4),
        "cer_strict_body": round(lev(b_s, g_s) / max(1, len(g_s)), 4),
        "cer_lenient_body": round(lev(b_l, g_l) / max(1, len(g_l)), 4),
        "vi_words_gt": n, "vi_words_exact": hit, "vi_words_base_letters_ok": hit_s,
        "symbols": symbol_counts(g_s, b_s),
        "math_tokens_gt": len(gtk), "math_token_edit_distance": lev(otk, gtk),
        "math_tokens_exact": otk == gtk,
        "text_exact_lenient": b_l.replace(" ", "") == g_l.replace(" ", ""),
    }


def calibrate(rows: list[dict]) -> dict:
    """Grid-search conf/uncovered-ink thresholds: maximise local accepts with ZERO unsafe accepts.

    Unsafe accept = gate says local-only but the OCR text is not exactly the ground truth (lenient), or the
    item has no problem text at all. Calibrated on the full labelled set — NOT held out.
    """
    best = None
    grid = []
    for t_conf in range(50, 100, 5):
        for t_unc in [x / 100 for x in range(0, 55, 5)]:
            acc = unsafe = 0
            for r in rows:
                ok_local = not r["gate"]["reasons"] and r["gate"]["min_line_conf"] >= t_conf and r["gate"]["uncovered_ink_ratio"] <= t_unc
                if ok_local:
                    acc += 1
                    if not (r["score"].get("has_gt") and r["score"]["text_exact_lenient"]):
                        unsafe += 1
            grid.append({"t_conf": t_conf, "t_uncovered": t_unc, "accepted": acc, "unsafe": unsafe})
            if unsafe == 0 and (best is None or acc > best["accepted"] or (acc == best["accepted"] and t_conf > best["t_conf"])):
                best = {"t_conf": t_conf, "t_uncovered": t_unc, "accepted": acc, "unsafe": 0}
    return {"selected": best, "grid": grid}


def _parent(args) -> int:
    os.environ["ALLOW_LIVE_AI"] = "0"
    work = Path(args.work)
    items = build_items(work)
    items_path = work / "items.json"
    items_path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    engines_out = {}
    for name in ENGINES:
        outp = work / f"out_{name}.json"
        if args.reuse and outp.exists():  # re-score existing raw OCR outputs (same prepared images) only
            engines_out[name] = json.loads(outp.read_text(encoding="utf-8"))
            engines_out[name]["wall_s"] = "REUSED"
            continue
        t0 = time.perf_counter()
        proc = subprocess.run([args.ocr_python, "-I", "-X", "utf8", str(Path(__file__).resolve()), "--child", name,
                               "--items", str(items_path), "--out", str(outp),
                               "--tessdata-best", args.tessdata_best, "--tessdata-fast", args.tessdata_fast],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            engines_out[name] = {"error": "CHILD_FAILED", "stderr_tail": proc.stderr[-600:]}
            continue
        engines_out[name] = json.loads(outp.read_text(encoding="utf-8"))
        engines_out[name]["wall_s"] = round(time.perf_counter() - t0, 1)

    by_id = {it["item_id"]: it for it in items}
    summary = {}
    per_item = {}
    for name, eo in engines_out.items():
        if "error" in eo:
            summary[name] = eo
            continue
        rows = []
        for res in eo["items"]:
            it = by_id[res["item_id"]]
            rows.append({"item_id": it["item_id"], "set": it["set"], "score": score(it, res), "gate": gate_features(it, res),
                         "warm_ms": res["warm_ms"], "first_run_ms": res["first_run_ms"]})
        per_item[name] = rows
        scored = [r["score"] for r in rows if r["score"].get("has_gt")]
        sym_tot: dict[str, dict[str, int]] = {}
        for s in scored:
            for k, v in s["symbols"].items():
                agg = sym_tot.setdefault(k, {"gt": 0, "strict_found": 0, "lenient_found": 0})
                for kk in agg:
                    agg[kk] += v[kk]
        vi_n = sum(s["vi_words_gt"] for s in scored)
        cal = calibrate(rows)
        sel = cal["selected"]
        sizes = {Path(p).name: os.path.getsize(p) for p in eo["model_files_all"] if os.path.exists(p)}
        summary[name] = {
            "engine_version": eo["engine_version"], "family": eo["family"], "config": eo["config"],
            "items_scored": len(scored),
            "cer_strict_full_median": round(statistics.median(s["cer_strict_full"] for s in scored), 4),
            "cer_strict_body_median": round(statistics.median(s["cer_strict_body"] for s in scored), 4),
            "cer_lenient_body_median": round(statistics.median(s["cer_lenient_body"] for s in scored), 4),
            "cer_lenient_body_max": max(s["cer_lenient_body"] for s in scored),
            "vi_word_exact_accuracy": round(sum(s["vi_words_exact"] for s in scored) / max(1, vi_n), 4),
            "vi_word_base_letter_accuracy": round(sum(s["vi_words_base_letters_ok"] for s in scored) / max(1, vi_n), 4),
            "vi_words_total": vi_n,
            "symbol_recall": {k: {**v, "strict_rate": round(v["strict_found"] / v["gt"], 3),
                                  "lenient_rate": round(v["lenient_found"] / v["gt"], 3)} for k, v in sym_tot.items()},
            "math_tokens_exact_items": sum(1 for s in scored if s["math_tokens_exact"]),
            "text_exact_lenient_items": sum(1 for s in scored if s["text_exact_lenient"]),
            "cold_ms_init_plus_first_item": eo["cold_ms_init_plus_first_item"],
            "warm_ms_median": statistics.median(r["warm_ms"] for r in rows),
            "warm_ms_max": max(r["warm_ms"] for r in rows),
            "peak_rss_mb": round(eo["peak_rss_bytes"] / 1048576, 1) if eo["peak_rss_bytes"] else "UNKNOWN",
            "rss_after_imports_mb": round(eo["rss_after_imports_bytes"] / 1048576, 1) if eo["rss_after_imports_bytes"] else "UNKNOWN",
            "model_files_bytes": sizes,
            "gate_calibration": {"selected": sel, "grid_size": len(cal["grid"])},
            "gate_rule_only_accepts": sum(1 for r in rows if not r["gate"]["reasons"]),
            "gate_rule_only_unsafe_accepts": sum(1 for r in rows if not r["gate"]["reasons"]
                                                 and not (r["score"].get("has_gt") and r["score"]["text_exact_lenient"])),
            "gate_rule_only_wrong_math_fact_accepts": sum(1 for r in rows if not r["gate"]["reasons"]
                                                          and r["score"].get("has_gt") and not r["score"]["math_tokens_exact"]),
            "gate_reason_counts": {k: sum(1 for r in rows if k in r["gate"]["reasons"]) for k in sorted({x for r in rows for x in r["gate"]["reasons"]})},
        }
        if sel:
            acc_ids = [r["item_id"] for r in rows if not r["gate"]["reasons"] and r["gate"]["min_line_conf"] >= sel["t_conf"]
                       and r["gate"]["uncovered_ink_ratio"] <= sel["t_uncovered"]]
            summary[name]["gate_local_accept_ids"] = acc_ids
    # Cross-engine variant: Tesseract supplies the Vietnamese text, a second engine must agree on EVERY
    # math-bearing token (numbers, vertex names, symbols). Evaluated only; nothing ships with two engines.
    cross = {}
    for text_eng in ("tesseract_vie_best", "tesseract_vie_fast"):
        for vote_eng in ("rapidocr_ppocrv6_small", "rapidocr_ppocrv6_medium", "rapidocr_ppocrv5_latin"):
            if text_eng not in per_item or vote_eng not in per_item:
                continue
            votes = {r["item_id"]: r["gate"]["body_text"] for r in per_item[vote_eng]}
            rows = []
            for r in per_item[text_eng]:
                g = dict(r["gate"])
                if math_tokens(g["body_text"]) != math_tokens(votes.get(r["item_id"], "")):
                    g["reasons"] = sorted(set(g["reasons"]) | {"CROSS_ENGINE_DISAGREEMENT"})
                rows.append({**r, "gate": g})
            cal = calibrate(rows)
            sel = cal["selected"]
            cross[f"{text_eng}+{vote_eng}"] = {
                "selected": sel,
                "accepted_ids": [r["item_id"] for r in rows if sel and not r["gate"]["reasons"]
                                 and r["gate"]["min_line_conf"] >= sel["t_conf"] and r["gate"]["uncovered_ink_ratio"] <= sel["t_uncovered"]],
                "rule_only_accepts": sum(1 for r in rows if not r["gate"]["reasons"]),
                "rule_only_unsafe": sum(1 for r in rows if not r["gate"]["reasons"]
                                        and not (r["score"].get("has_gt") and r["score"]["text_exact_lenient"])),
            }
    receipt = {
        "cross_engine_gate_variants": cross,
        "ocr_outputs_reused_from_previous_child_run": bool(args.reuse),
        "schema": "local-ocr-benchmark/1", "run_id": "adaptive-local-ocr-fallback", "date": "2026-11-09",
        "MEASUREMENT_CLASS": "OFFLINE_LOCAL_OCR_ON_SYNTHETIC_RENDERED_IMAGES",
        "CORPUS_KIND": "SYNTHETIC_RENDERED", "REAL_PHOTO_CORPUS": "NOT_ESTABLISHED", "HELD_OUT_CLAIM": "NONE",
        "CALIBRATION_SET": "ALL items below (photo_problem_corpus 12 + symbol_stress 10); thresholds are NOT held-out",
        "ORACLE": "ground_truth_text of the renderer (CORPUS.json / STRESS_TEXTS), independent of every OCR engine",
        "OCR_INPUT": "product prepared_image (normalize_image -> detect_problem_regions), i.e. the bytes Vision would get",
        "provider_network_calls": 0, "host": {"os": os.name, "cpu_count": os.cpu_count()},
        "items": [{k: v for k, v in it.items() if k != "path"} for it in items],
        "engines": summary, "per_item": per_item,
    }
    Path(args.out).write_text(json.dumps(receipt, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"receipt -> {args.out}")
    for name, s in summary.items():
        print(name, {k: s.get(k) for k in ("cer_lenient_body_median", "vi_word_exact_accuracy", "text_exact_lenient_items",
                                             "warm_ms_median", "peak_rss_mb", "gate_calibration")})
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--child")
    ap.add_argument("--items")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ocr-python")
    ap.add_argument("--tessdata-best", required=True)
    ap.add_argument("--tessdata-fast", required=True)
    ap.add_argument("--work")
    ap.add_argument("--reuse", action="store_true", help="re-score existing child outputs in --work")
    a = ap.parse_args()
    if a.child:
        _child(a.child, a.items, a.out, a.tessdata_best, a.tessdata_fast)
        return 0
    backend = ROOT / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))
    return _parent(a)


if __name__ == "__main__":
    raise SystemExit(main())
