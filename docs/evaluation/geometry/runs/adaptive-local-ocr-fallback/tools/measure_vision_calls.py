# -*- coding: utf-8 -*-
"""Vision provider calls before/after on the SAME image set, through the real `prepare_unified_input`.

The provider boundary `image_extraction._goi_provider` is replaced by an OFFLINE MOCK that returns the
ground-truth transcription (oracle) — so the in-process `EXTRACTION_CACHE`, the region detector, the crop
retry and the multi-image dedup all run for real. Counted: mock provider calls (would-be network calls),
cache hits, real network calls (0 — `ALLOW_LIVE_AI=0` guard + mock).

"before" = base behaviour, reproduced exactly by forcing `crop_holds_all_content=False` (with that flag False
the new retry predicate is literally the base predicate). "after" = current code.

    cd backend && PYTHONIOENCODING=utf-8 ALLOW_LIVE_AI=0 .venv/Scripts/python.exe \
      ../docs/evaluation/geometry/runs/adaptive-local-ocr-fallback/tools/measure_vision_calls.py --out <json>
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import io
import json
import os
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["ALLOW_LIVE_AI"] = "0"  # kill switch stays ON; `_require_vision_key` is patched below instead
os.environ.pop("GEMINI_API_KEY", None)

from app.ingestion import image_extraction as IE  # noqa: E402
from app.ingestion import unified_input as UI  # noqa: E402
from app.ingestion.image import normalize_image  # noqa: E402
from app.ingestion.image_extraction import ImageProblemExtraction  # noqa: E402
from benchmark_local_ocr import CORPUS, STRESS_TEXTS, _render_stress  # noqa: E402

CACHE_VERSION = "132"


def _image_set() -> list[dict]:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    out = [{"item_id": it["id"], "raw": (CORPUS.parent / it["file"]).read_bytes(), "gt": it["ground_truth_text"] or "",
            "has_diagram": bool(it["diagram"])} for it in corpus["items"]]
    for sid, txt in STRESS_TEXTS.items():
        for deg in (False, True):
            buf = io.BytesIO()
            _render_stress(txt, degrade=deg).save(buf, format="PNG")
            out.append({"item_id": f"{sid}{'_degraded' if deg else ''}", "raw": buf.getvalue(), "gt": txt, "has_diagram": False})
    return out


def _measure(mode: str, items: list[dict]) -> dict:
    by_sha: dict[str, dict] = {}
    for it in items:
        by_sha[normalize_image(it["raw"]).sha256] = it
    calls: list[str] = []
    gt_of_page: dict[str, dict] = {}

    async def fake_provider(image, api_key):
        calls.append(image.sha256)
        it = gt_of_page.get("current")
        return ImageProblemExtraction(
            problem_text_verbatim=it["gt"], problem_text_normalized=it["gt"], math_expressions=[], named_points=[],
            named_lines=[], named_planes=[], named_solids=[], given_relations=[], has_diagram=it["has_diagram"],
            diagram_observations=[], text_diagram_conflicts=[], uncertain_tokens=[], missing_regions=[], confidence=0.95)

    real_detect = UI.detect_problem_regions

    def detect(*a, **kw):
        r = real_detect(*a, **kw)
        return replace(r, crop_holds_all_content=False) if mode == "before" else r

    rows = []
    IE.EXTRACTION_CACHE.clear()
    with patch.object(IE, "_goi_provider", side_effect=fake_provider), patch.object(UI, "detect_problem_regions", side_effect=detect), \
            patch.object(UI, "_require_vision_key", side_effect=lambda k: k):
        for pass_no in (1, 2):
            for it in items:
                gt_of_page["current"] = it
                before = len(calls)
                out = asyncio.run(UI.prepare_unified_input(content=base64.b64encode(it["raw"]).decode(),
                                                           api_key="offline-mock", cache_version=CACHE_VERSION))
                rows.append({"pass": pass_no, "item_id": it["item_id"], "status": out.status, "reason_code": out.reason_code,
                             "mock_provider_calls": len(calls) - before, "reported_vlm_calls": out.metrics.get("vlm_calls"),
                             "vision_cached": out.provenance.get("vision_cached"),
                             "text_equals_gt": (out.problem_text or "").strip() == it["gt"].strip() if it["gt"] else None})
        # Multi-image journey: same problem photographed twice + a diagram-only photo (ordered, deduplicated).
        IE.EXTRACTION_CACHE.clear()
        a, c = items[0], next(i for i in items if i["item_id"] == "c11_chi_co_hinh")
        seq = {"att-1": a, "att-2": a, "att-3": c}

        async def fake_multi(image, api_key):
            calls.append(image.sha256)
            it = c if image.sha256 in _shas(c["raw"]) else a
            return ImageProblemExtraction(
                problem_text_verbatim=it["gt"], problem_text_normalized=it["gt"], math_expressions=[], named_points=[],
                named_lines=[], named_planes=[], named_solids=[], given_relations=[], has_diagram=it["has_diagram"],
                diagram_observations=[], text_diagram_conflicts=[], uncertain_tokens=[], missing_regions=[], confidence=0.95)

        with patch.object(IE, "_goi_provider", side_effect=fake_multi):
            before = len(calls)
            out = asyncio.run(UI.prepare_unified_input(
                attachments=[{"attachment_id": k, "order_index": i, "content": base64.b64encode(v["raw"]).decode()}
                             for i, (k, v) in enumerate(seq.items())], api_key="offline-mock", cache_version=CACHE_VERSION))
            multi = {"attachments": list(seq), "status": out.status, "mock_provider_calls": len(calls) - before,
                     "deduplicated_attachment_ids": out.provenance.get("deduplicated_attachment_ids"),
                     "source_attachment_ids": out.provenance.get("source_attachment_ids")}
    p1 = [r for r in rows if r["pass"] == 1]
    p2 = [r for r in rows if r["pass"] == 2]
    return {"mode": mode, "items": len(items), "pass1_mock_provider_calls": sum(r["mock_provider_calls"] for r in p1),
            "pass2_mock_provider_calls_same_images": sum(r["mock_provider_calls"] for r in p2),
            "pass2_cache_hits": sum(1 for r in p2 if r["vision_cached"]),
            "pass1_text_equals_gt": sum(1 for r in p1 if r["text_equals_gt"]),
            "multi_image_journey": multi, "rows": rows}


def _shas(raw: bytes) -> set[str]:
    n = normalize_image(raw)
    r = UI.detect_problem_regions(n)
    return {n.sha256, r.prepared_image.sha256, r.full_image.sha256}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    items = _image_set()
    res = {"schema": "vision-calls-before-after/1", "run_id": "adaptive-local-ocr-fallback", "date": "2026-11-09",
           "MEASUREMENT_CLASS": "OFFLINE_MOCK_PROVIDER_CALL_COUNT", "real_network_calls": 0,
           "provider": "MOCK (returns oracle transcription; not Gemini)", "cache_version": CACHE_VERSION,
           "before": _measure("before", items), "after": _measure("after", items)}
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for m in ("before", "after"):
        r = res[m]
        print(m, {k: r[k] for k in ("pass1_mock_provider_calls", "pass2_mock_provider_calls_same_images", "pass2_cache_hits",
                                    "pass1_text_equals_gt")}, r["multi_image_journey"]["mock_provider_calls"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
