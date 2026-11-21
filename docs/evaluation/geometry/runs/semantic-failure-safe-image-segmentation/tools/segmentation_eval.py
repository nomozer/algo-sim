"""Multi-problem image segmentation on the PRODUCT prepare path (run `semantic-failure-safe-image-segmentation`).

  python segmentation_eval.py <before_backend_dir> <out_json>     # from the worktree root, backend interpreter
  python segmentation_eval.py --child <backend_dir>                # internal

Sets (never mixed in one rate):
  REAL_SINGLE  — the 25 controlled-vision VMMU crops (MIT, DEVELOPMENT_EXPOSED; one problem each, each with a figure).
  COMPOSITE    — 12 two-problem and 8 three-problem pages stacked from those crops (SYNTHETIC_COMPOSITE_OF_REAL_EXPOSED_CROPS).
  SIDE_BY_SIDE — 6 pages with two crops side by side (two columns), same provenance.
For every page: `prepare_unified_input` (local OCR, ALLOW_LIVE_AI=0). A composite that comes back `needs_selection` with
candidates is then prepared once per candidate (the learner's choice); the OCR text of the chosen problem is compared with
every crop's agent transcription by 5-gram containment (target vs neighbours). No image is written to Git.
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
MAN = ROOT / "docs/evaluation/geometry/runs/controlled-vision-real-image-validation/new_in_scope_image_manifest.json"
GAP = 80


def pages() -> list[dict]:
    from PIL import Image
    items = json.loads(MAN.read_text(encoding="utf-8"))["items"]
    ims = {it["case_id"]: Image.open(ROOT / it["cache_path"]).convert("RGB") for it in items}
    ids = sorted(ims)
    out = [{"set": "REAL_SINGLE", "id": c, "members": [c], "img": ims[c]} for c in ids]
    for grp in [ids[i:i + 2] for i in range(0, len(ids) - 1, 2)] + [ids[i:i + 3] for i in range(0, len(ids) - 2, 3)]:
        W = max(ims[c].width for c in grp)
        H = sum(ims[c].height for c in grp) + GAP * (len(grp) + 1)
        page = Image.new("RGB", (W, H), (255, 255, 255))
        y = GAP
        for c in grp:
            page.paste(ims[c], (0, y))
            y += ims[c].height + GAP
        out.append({"set": f"COMPOSITE_{len(grp)}", "id": "+".join(grp), "members": grp, "img": page})
    for grp in [ids[i:i + 2] for i in range(0, 12, 2)]:
        a, b = (ims[c].resize((ims[c].width // 2, ims[c].height // 2)) for c in grp)
        page = Image.new("RGB", (a.width + b.width + 3 * GAP, max(a.height, b.height) + 2 * GAP), (255, 255, 255))
        page.paste(a, (GAP, GAP))
        page.paste(b, (2 * GAP + a.width, GAP))
        out.append({"set": "SIDE_BY_SIDE", "id": "|".join(grp), "members": grp, "img": page})
    return out


def grams(t: str, n: int = 5) -> set:
    t = "".join(ch for ch in t.lower() if ch.isalnum())
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


def child() -> None:
    os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
    os.environ.setdefault("LOCAL_OCR_PYTHON", str(ROOT / ".superpowers/ocr-venv/Scripts/python.exe"))
    os.environ.setdefault("LOCAL_OCR_TESSDATA", str(ROOT / ".superpowers/tessdata_fast"))
    from app.ingestion.unified_input import prepare_unified_input
    stmts = {it["case_id"]: it["statement"] for it in json.loads(MAN.read_text(encoding="utf-8"))["items"]}

    async def prep(b64: str, sel: str | None = None):
        o = await prepare_unified_input(content=b64, declared_mime="image/png", filename="page.png", selected_candidate_id=sel)
        return o.to_dict()

    rows = []
    for pg in pages():
        buf = io.BytesIO()
        pg["img"].save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        r = asyncio.run(prep(b64))
        row = {"set": pg["set"], "id": pg["id"], "members": pg["members"], "status": r["status"], "reason": r.get("reason_code"),
               "candidates": [c["candidate_id"] for c in r.get("candidates") or []],
               "region_state": (r.get("provenance") or {}).get("region_state"),
               "headers_overrule": (r.get("provenance") or {}).get("region_split_overruled_by_ocr_headers")}
        if r["status"] != "needs_selection":
            g = grams(r.get("problem_text") or "")
            row["text_containment"] = {m: round(len(grams(stmts[m]) & g) / max(1, len(grams(stmts[m]))), 3) for m in pg["members"]}
        else:
            picks = []
            for k, cid in enumerate(row["candidates"]):
                rr = asyncio.run(prep(b64, cid))
                g = grams(rr.get("problem_text") or "")
                cont = {m: round(len(grams(stmts[m]) & g) / max(1, len(grams(stmts[m]))), 3) for m in pg["members"]}
                best = max(cont, key=cont.get)
                nb = max([v for m, v in cont.items() if m != best], default=0.0)
                picks.append({"candidate": cid, "status": rr["status"], "containment": cont, "best_member": best,
                              "best_containment": cont[best], "neighbour_max": nb,
                              "clean": cont[best] >= 0.4 and nb <= cont[best] / 2})
            row["picks"] = picks
        rows.append(row)
        print(json.dumps({k: row[k] for k in ("set", "id", "status", "candidates")}), file=sys.stderr)
    print(json.dumps(rows, ensure_ascii=False))


def run(backend: Path) -> list[dict]:
    env = {**os.environ, "PYTHONPATH": str(backend), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": ""}
    res = subprocess.run([sys.executable, __file__, "--child", str(backend)], capture_output=True, text=True, cwd=backend, env=env,
                         encoding="utf-8", check=True)
    return json.loads(res.stdout.strip().splitlines()[-1])


def summarise(rows: list[dict]) -> dict:
    out = {}
    for s in sorted({r["set"] for r in rows}):
        rs = [r for r in rows if r["set"] == s]
        d = {"pages": len(rs), "status": {}}
        for r in rs:
            d["status"][r["status"]] = d["status"].get(r["status"], 0) + 1
        if s == "REAL_SINGLE":
            d["unnecessary_selection_prompts"] = sum(r["status"] == "needs_selection" for r in rs)
            d["whole_problem_text_kept"] = sum(1 for r in rs if (r.get("text_containment") or {}).get(r["members"][0], 0) >= 0.5)
        else:
            merged = [r for r in rs if r["status"] != "needs_selection"]
            d["merged_without_prompt"] = len(merged)
            d["selection_offered"] = sum(r["status"] == "needs_selection" for r in rs)
            d["selection_without_candidates"] = sum(r["status"] == "needs_selection" and not r["candidates"] for r in rs)
            picks = [p for r in rs for p in r.get("picks") or []]
            d["picks"] = len(picks)
            d["picks_distinct_problems_cover_all"] = sum(
                1 for r in rs if r.get("picks") and sorted({p["best_member"] for p in r["picks"]}) == sorted(r["members"]))
            d["picks_with_neighbour_containment_ge_0_2"] = sum(p["neighbour_max"] >= 0.2 for p in picks)
            d["picks_clean"] = sum(p["clean"] for p in picks)
            d["pages_every_problem_cleanly_selectable"] = sum(
                1 for r in rs if r.get("picks") and {p["best_member"] for p in r["picks"] if p["clean"]} == set(r["members"]))
            d["merged_pages_neighbour_text_present"] = sum(
                1 for r in merged if sum(v >= 0.3 for v in (r.get("text_containment") or {}).values()) >= 2)
        out[s] = d
    return out


def main(before: Path, out: Path) -> int:
    after_rows, before_rows = run(ROOT / "backend"), run(before)
    data = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
            "environment": {"ALLOW_LIVE_AI": "0", "local_ocr": "RapidOCR + Tesseract (unchanged engines)"},
            "command": "python docs/evaluation/geometry/runs/semantic-failure-safe-image-segmentation/tools/segmentation_eval.py <before_backend> <out>",
            "dataset_partition": "DEVELOPMENT_EXPOSED crops; composites and side-by-side pages are synthetic layouts of those crops",
            "oracle_status": "BY_CONSTRUCTION page layout; text containment against AGENT_TRANSCRIBED_UNVERIFIED statements",
            "summary_before": summarise(before_rows), "summary_after": summarise(after_rows),
            "rows_before": before_rows, "rows_after": after_rows}
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"before": data["summary_before"], "after": data["summary_after"]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        child()
        raise SystemExit(0)
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))
