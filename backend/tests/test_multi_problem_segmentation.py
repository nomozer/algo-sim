# -*- coding: utf-8 -*-
"""Safe multi-problem image segmentation (run `semantic-failure-safe-image-segmentation`).

Pure layout evidence from OCR word boxes: multiple-choice option groups (one option A per problem) and the bands that
separate stacked problems. Then the prepare path with the evidence injected: a single detector region holding two option
groups is never sent on as one problem; a chosen band is cut deterministically; side-by-side problems ask for a tighter
photo instead of a merged page; a one-problem image with no or one option group is untouched.
"""
from __future__ import annotations

import asyncio
import base64
import io

from PIL import Image, ImageDraw

from app.ingestion import local_ocr_route as R


def _w(text, x, y, h=40):
    return {"text": text, "bbox": [x, y, x + 20 * max(1, len(text)), y + h]}


def _raw(rows, width=2000):
    """rows: [(y, [(text, x), ...]) or (y, [(text, x), ...], x_end), ...] → an OCR result of one engine (each row one
    line, spanning to x_end or the page width)."""
    lines = []
    for row in rows:
        y, words = row[0], row[1]
        x_end = row[2] if len(row) > 2 else width
        lines.append({"text": " ".join(t for t, _x in words), "bbox": [min(x for _t, x in words), y, x_end, y + 40],
                      "words": [_w(t, x, y) for t, x in words]})
    return {"ok": True, "height": 3000, "width": width, "engines": {"rapidocr": {"lines": lines}}}


OPTS_ONE_ROW = [("A.", 100), ("B.", 600), ("C.", 1100), ("D.", 1600)]


def test_one_option_row_is_one_problem():
    raw = _raw([(0, [("Cho", 100), ("hình", 200)]), (60, [("tại", 100), ("A.", 180)]), (400, OPTS_ONE_ROW)])
    assert len(R.option_groups(raw)) == 1 and R.problem_bands(raw, 3000) is None


def test_two_by_two_options_are_one_problem():
    raw = _raw([(0, [("Cho", 100)]), (400, [("A.", 100), ("B.", 900)]), (460, [("C.", 100), ("D.", 900)])])
    assert len(R.option_groups(raw)) == 1


def test_stacked_problems_give_one_band_each_cut_after_the_options():
    raw = _raw([(0, [("Cho", 100)]), (400, OPTS_ONE_ROW), (700, [("Cho", 100)]), (1100, OPTS_ONE_ROW)])
    groups = R.option_groups(raw)
    bands = R.problem_bands(raw, 3000)
    assert len(groups) == 2 and bands == [(0, 0, 2000, 570), (0, 570, 2000, 3000)]   # halfway between 440 and the next line at 700


def test_side_by_side_problems_are_cut_into_columns_never_across_them():
    left = [(0, [("Cho", 100)], 900), (300, [("A.", 100), ("B.", 300), ("C.", 500), ("D.", 700)], 900)]
    right = [(10, [("Cho", 1300)], 2100), (500, [("A.", 1300), ("B.", 1500), ("C.", 1700), ("D.", 1900)], 2100)]
    raw = _raw(left + right, width=2200)
    bands = R.problem_bands(raw, 3000)
    assert bands is not None and len(bands) == 2
    (l0, _t0, l1, _b0), (r0, _t1, r1, _b1) = bands
    assert l0 == 0 and 900 <= l1 <= 1300 and r0 == l1 and r1 == 2200          # one vertical cut in the free gutter


def test_columns_crossed_by_a_text_line_are_ambiguous():
    rows = [(0, [("Cho", 100)], 2100), (300, [("A.", 100), ("B.", 300), ("C.", 500), ("D.", 700)], 900),
            (500, [("A.", 1300), ("B.", 1500), ("C.", 1700), ("D.", 1900)], 2100)]
    assert R.problem_bands(_raw(rows, width=2200), 3000) is None


def test_no_options_is_no_evidence():
    raw = _raw([(0, [("Cho", 100)]), (60, [("Tính", 100)])])
    assert R.option_groups(raw) == [] and R.problem_bands(raw, 3000) is None


# ── the prepare path, evidence injected ──────────────────────────────────────────────────────────────────────────────
def _page():
    im = Image.new("RGB", (1200, 1400), "white")
    d = ImageDraw.Draw(im)
    for y0 in (80, 760):                                 # two stacked "problems": text lines, a figure, an option row
        for k in range(3):
            d.rectangle([80, y0 + k * 40, 1100, y0 + k * 40 + 18], fill="black")
        d.polygon([(300, y0 + 200), (600, y0 + 160), (700, y0 + 420), (350, y0 + 460)], outline="black", width=4)
        d.rectangle([80, y0 + 520, 1100, y0 + 540], fill="black")
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _prepare(monkeypatch, signals, sel=None):
    from app.ingestion import unified_input as U
    monkeypatch.setattr(R, "estimate_problem_signals", lambda _b: signals)
    monkeypatch.setattr(R, "run_local_ocr_route", lambda *_a, **_k: None)
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    return asyncio.run(U.prepare_unified_input(content=_page(), declared_mime="image/png", filename="p.png",
                                               selected_candidate_id=sel)).to_dict()


def test_two_option_groups_in_one_region_ask_the_learner_to_choose(monkeypatch):
    from app.ingestion import unified_input as U
    sig = {"headers": 0, "option_groups": 2, "groups": [], "bands": [(0, 0, 1200, 700), (0, 700, 1200, 1400)], "height": 1400}
    r = _prepare(monkeypatch, sig)
    # whether or not the detector split the page itself, stacked option groups are offered as one band per problem
    assert r["status"] == "needs_selection" and [c["candidate_id"] for c in r["candidates"]] == ["page~band-1", "page~band-2"]
    cut = []
    real = U._crop_to_band
    monkeypatch.setattr(U, "_crop_to_band", lambda res, band: cut.append(band) or real(res, band))
    try:
        chosen = _prepare(monkeypatch, sig, sel="page~band-2")
        assert chosen["status"] != "needs_selection"
    except U.LiveVisionDisabledError:
        pass                                   # the chosen band went on to reading (OCR stubbed off, live vision off)
    assert cut == [(0, 700, 1200, 1400)]       # exactly the chosen problem's band, nothing of the other


def test_side_by_side_groups_ask_for_a_tighter_photo_never_send_the_page(monkeypatch):
    sig = {"headers": 0, "option_groups": 2, "groups": [], "bands": None, "height": 1400}
    r = _prepare(monkeypatch, sig)
    assert r["status"] == "needs_selection"


def test_one_problem_with_one_option_group_is_not_interrupted(monkeypatch):
    from app.ingestion.unified_input import LiveVisionDisabledError
    sig = {"headers": 1, "option_groups": 1, "groups": [], "bands": None, "height": 1400}
    try:
        r = _prepare(monkeypatch, sig)
    except LiveVisionDisabledError:
        return                     # passed segmentation and reached the reading step (OCR stubbed off, live vision off)
    assert r["reason_code"] not in ("AMBIGUOUS_PROBLEM_BOUNDARIES",) and not any("~band-" in c["candidate_id"] for c in r["candidates"])


def test_a_stale_band_choice_is_refused_not_guessed(monkeypatch):
    sig = {"headers": 0, "option_groups": 2, "groups": [], "bands": [(0, 0, 1200, 700), (0, 700, 1200, 1400)], "height": 1400}
    r = _prepare(monkeypatch, sig, sel="page~band-5")
    assert r["status"] == "needs_selection" and r["reason_code"] == "AMBIGUOUS_PROBLEM_BOUNDARIES" and not r["candidates"]
