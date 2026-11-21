"""Problem-region detection and diagram association on exposed real images (run `independent-geometry-plane-constraints`).

Three sets, never mixed in one rate:
  REAL_SINGLE   — the 25 controlled-vision VMMU crops (MIT, DEVELOPMENT_EXPOSED; one problem each, every one with a figure:
                  AGENT_ANNOTATED_UNVERIFIED from a contact sheet). Ground-truth problem box = bounding box of all ink.
  COMPOSITE     — 2 or 3 of those crops stacked on one white page (SYNTHETIC_COMPOSITE_OF_REAL_EXPOSED_CROPS): the box of
                  every problem is known by construction; measures separation, the chosen region per target and contamination.
  PERTURBED     — each real crop rotated 4°, darkened, or shaded (SYNTHETIC_PERTURBATION_OF_REAL_EXPOSED_CROPS).
No camera photograph of paper, no handwriting, no new image. The detector is the product's `detect_problem_regions`.
Run from backend/ with PYTHONPATH=. :  python <this> <out_json>
"""
from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parents[6]
os.environ.setdefault("LOCAL_OCR_PYTHON", str(ROOT / ".superpowers/ocr-venv/Scripts/python.exe"))
os.environ.setdefault("LOCAL_OCR_TESSDATA", str(ROOT / ".superpowers/tessdata_fast"))

from app.ingestion.image import normalize_image  # noqa: E402
from app.ingestion.local_ocr_route import count_problem_headers_on_page  # noqa: E402
from app.ingestion.region_detector import detect_problem_regions  # noqa: E402


def product_decision(im: Image.Image, r) -> dict:
    """What `prepare` does with a detector split (unified_input step 2): ≥ 2 candidates flagged ambiguous are offered for
    selection unless local OCR reads at most one "Câu/Bài N" header on the page, which keeps the whole page."""
    if not (r.ambiguous_multi_problem and len(r.candidates) >= 2):
        return {"decision": "SINGLE_REGION", "ocr_headers": None}
    n = count_problem_headers_on_page(r.full_image.data)
    return {"decision": "WHOLE_PAGE_KEPT" if n is not None and n <= 1 else "SELECTION_OFFERED", "ocr_headers": n}
MAN = ROOT / "docs/evaluation/geometry/runs/controlled-vision-real-image-validation/new_in_scope_image_manifest.json"
GAP = 80


def ink_box(im: Image.Image, thr: int = 170) -> tuple[int, int, int, int] | None:
    g = im.convert("L").point(lambda v: 255 if v < thr else 0)
    return g.getbbox()


def area(b):
    return max(0, b[2] - b[0]) * max(0, b[3] - b[1])


def inter(a, b):
    return (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))


def png(im: Image.Image) -> bytes:
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


def detect(im: Image.Image, k: int | None = None):
    r = detect_problem_regions(normalize_image(png(im)), target_problem_index=k)
    sel = r.selected_bbox
    return r, (sel.x0, sel.y0, sel.x1, sel.y1)


def row_single(cid, im, gt, kind):
    r, sel = detect(im)
    inter_a = area(inter(sel, gt))
    comparable = not (r.deskew_applied or r.desk_trimmed)       # the product crops the deskewed / trimmed image: other frame
    W, H = im.size
    best = max((area(inter((c.normalized_bbox[0] * W, c.normalized_bbox[1] * H, c.normalized_bbox[2] * W,
                             c.normalized_bbox[3] * H), gt)) / area(gt) for c in r.candidates), default=None) if comparable else None
    return {"case": cid, "set": kind, "frame_comparable": comparable,
            "best_single_candidate_containment": None if best is None else round(best, 4),
            "candidates": len(r.candidates), "ambiguous_multi_problem": r.ambiguous_multi_problem,
            "has_associated_figure": r.has_associated_figure, "used_crop": r.used_crop,
            "used_fallback_full_image": r.used_fallback_full_image, "deskew_applied": r.deskew_applied,
            "skew_angle_deg": r.skew_angle_deg, "low_light_enhanced": r.quality.enhanced_low_light,
            "shadow_enhanced": r.quality.enhanced_shadow,
            "containment": round(inter_a / area(gt), 4) if comparable else "NOT_COMPARABLE",
            "precision": round(inter_a / max(1, area(sel)), 4) if comparable else "NOT_COMPARABLE",
            "truncated": (inter_a < 0.98 * area(gt)) if comparable else None}


def main(out: Path) -> int:
    items = json.loads(MAN.read_text(encoding="utf-8"))["items"]
    ims = {it["case_id"]: Image.open(ROOT / it["cache_path"]).convert("RGB") for it in items}
    ids = sorted(ims)
    rows = []
    for cid in ids:
        row = row_single(cid, ims[cid], ink_box(ims[cid]), "REAL_SINGLE")
        row.update(product_decision(ims[cid], detect(ims[cid])[0]))
        rows.append(row)
    # perturbations (real crop, synthetic transform); the ground-truth box is the ink box of the transformed image
    for cid in ids:
        im = ims[cid]
        rot = im.rotate(4, expand=True, fillcolor=(255, 255, 255))
        rows.append(row_single(cid, rot, ink_box(rot), "PERTURBED_ROTATED_4DEG"))
        dark = ImageEnhance.Brightness(im).enhance(0.45)
        rows.append(row_single(cid, dark, ink_box(dark, thr=75), "PERTURBED_LOW_LIGHT"))
        w, h = im.size
        grad = Image.linear_gradient("L").rotate(90, expand=True).resize((w, h))      # dark on the left → light on the right
        shade = Image.composite(im, ImageEnhance.Brightness(im).enhance(0.55), grad)
        rows.append(row_single(cid, shade, ink_box(im), "PERTURBED_SHADOW"))
    # composites: consecutive pairs and triples of crops on one page, every target asked
    comps = [ids[i:i + 2] for i in range(0, len(ids) - 1, 2)] + [ids[i:i + 3] for i in range(0, len(ids) - 2, 3)]
    for grp in comps:
        W = max(ims[c].width for c in grp)
        H = sum(ims[c].height for c in grp) + GAP * (len(grp) + 1)
        page = Image.new("RGB", (W, H), (255, 255, 255))
        gts, y = [], GAP
        for c in grp:
            page.paste(ims[c], (0, y))
            b = ink_box(ims[c])
            gts.append((b[0], b[1] + y, b[2], b[3] + y))
            y += ims[c].height + GAP
        r0, _ = detect(page)
        page_decision = product_decision(page, r0)
        for k in range(1, len(grp) + 1):
            r, sel = detect(page, k)
            gt = gts[k - 1]
            ia = area(inter(sel, gt))
            others = [area(inter(sel, g)) / area(g) for j, g in enumerate(gts) if j != k - 1]
            cand = next((c for c in r.candidates if c.index == k), None)
            rows.append({"case": "+".join(grp), "set": f"COMPOSITE_{len(grp)}", "target": k, "candidates": len(r.candidates),
                         "separation_ok": len(r.candidates) == len(grp), "ambiguous_multi_problem": r.ambiguous_multi_problem,
                         "containment": round(ia / area(gt), 4), "precision": round(ia / max(1, area(sel)), 4),
                         "truncated": ia < 0.98 * area(gt), "max_neighbour_overlap": round(max(others), 4),
                         "contaminated": max(others) > 0.05,
                         "target_candidate_has_figure": bool(cand and cand.has_figure),
                         "product_decision_without_target": page_decision["decision"], "ocr_headers": page_decision["ocr_headers"]})
    summary = {}
    for s in sorted({r["set"] for r in rows}):
        rs = [r for r in rows if r["set"] == s]
        cmp_ = [r for r in rs if r.get("frame_comparable", True)]
        d = {"rows": len(rs), "frame_comparable": len(cmp_), "containment_ge_0_98": sum(r["truncated"] is False for r in cmp_),
             "median_precision": sorted(r["precision"] for r in cmp_)[len(cmp_) // 2] if cmp_ else "NOT_COMPARABLE"}
        if s.startswith("COMPOSITE"):
            pages = {r["case"]: r for r in rs}.values()
            d.update(separation_ok=sum(r["separation_ok"] for r in rs), contaminated=sum(r["contaminated"] for r in rs),
                     target_has_figure=sum(r["target_candidate_has_figure"] for r in rs),
                     pages=len(pages), pages_whole_page_kept_mixing_problems=sum(r["product_decision_without_target"] == "WHOLE_PAGE_KEPT" for r in pages),
                     pages_selection_offered=sum(r["product_decision_without_target"] == "SELECTION_OFFERED" for r in pages))
        else:
            flag = [r for r in cmp_ if r["ambiguous_multi_problem"]]
            d.update(single_candidate=sum(r["candidates"] == 1 for r in rs), figure_detected=sum(r["has_associated_figure"] for r in rs),
                     flagged_multi_problem=sum(r["ambiguous_multi_problem"] for r in rs),
                     flagged_with_one_candidate_holding_whole_problem=sum((r["best_single_candidate_containment"] or 0) >= 0.98 for r in flag),
                     flagged_rows_frame_comparable=len(flag))
            if s == "REAL_SINGLE":
                d.update(product_whole_page_kept=sum(r.get("decision") == "WHOLE_PAGE_KEPT" for r in rs),
                         product_selection_offered=sum(r.get("decision") == "SELECTION_OFFERED" for r in rs),
                         product_single_region=sum(r.get("decision") == "SINGLE_REGION" for r in rs))
        summary[s] = d
    out.write_text(json.dumps({"generated_at_utc": datetime.now(timezone.utc).isoformat(), "summary": summary, "rows": rows},
                              ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
