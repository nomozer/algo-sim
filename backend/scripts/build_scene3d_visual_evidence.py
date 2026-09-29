# -*- coding: utf-8 -*-
"""Contact sheets and hidden-edge crops from the authoritative PNGs (w10).

Main sheet: one row per family, LARGE cells — desktop neutral_final ·
causal_selected · rotated_neutral · mobile neutral_final. Formation and
playback filmstrips go to an appendix sheet. Every crop contains BOTH
endpoints of its edge (projected by the independent oracle from the recorded
camera) and is listed in ``crops/CROPS_INDEX.json`` with its review metadata.
The w09 crops were 128 px around one witness point; a reviewer could not see
where the hidden edge started or ended.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from measure_scene3d_occlusion import _camera
from scene3d_occlusion_oracle import _project

REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_COLUMNS = (("desktop", "neutral_final"), ("desktop", "causal_selected"),
                ("desktop", "rotated_neutral"), ("mobile", "neutral_final"))
CELL = (640, 420)
STATES = ("neutral_final", "rotated_neutral")


def crop_box(a: tuple[float, float], b: tuple[float, float], size: tuple[int, int],
             margin: int = 24, min_size: int = 96) -> tuple[int, int, int, int]:
    """Smallest box holding both endpoints + margin, at least `min_size`, inside the image."""
    x0, x1 = min(a[0], b[0]) - margin, max(a[0], b[0]) + margin
    y0, y1 = min(a[1], b[1]) - margin, max(a[1], b[1]) + margin
    for lo, hi, limit, axis in ((x0, x1, size[0], 0), (y0, y1, size[1], 1)):
        grow = max(0.0, min_size - (hi - lo)) / 2
        lo, hi = lo - grow, hi + grow
        # Chạm mép ảnh: dồn phần thiếu sang phía còn chỗ, không co hộp lại.
        if lo < 0:
            lo, hi = 0.0, hi - lo
        if hi > limit:
            lo, hi = max(0.0, lo - (hi - limit)), float(limit)
        if axis == 0:
            x0, x1 = lo, hi
        else:
            y0, y1 = lo, hi
    return int(x0), int(y0), int(round(x1)), int(round(y1))


def _visibility(edge_id: str, sets: dict[str, Any]) -> str:
    for key, name in (("hidden_edge_ids", "HIDDEN"), ("mixed_edge_ids", "MIXED"),
                      ("visible_edge_ids", "VISIBLE")):
        if edge_id in sets.get(key, []):
            return name
    return "ABSENT"


def _labels(scene: dict[str, Any]) -> dict[str, str]:
    return {o["id"]: (o.get("notation") or o.get("label") or o["id"])
            for o in scene.get("objects", []) if o.get("type") == "point3"}


def edge_records(scene: dict[str, Any], snapshot: dict[str, Any], product: dict[str, Any],
                 oracle: dict[str, Any], expected: dict[str, str]) -> list[dict[str, Any]]:
    """Every edge a reviewer must check: hidden/mixed per product or oracle, or registered."""
    camera = _camera(snapshot)
    labels = _labels(scene)
    solids = {o["id"]: o for o in scene.get("objects", []) if o.get("type") == "solid"}
    ids = sorted({*product.get("hidden_edge_ids", []), *product.get("mixed_edge_ids", []),
                  *oracle.get("hidden_edge_ids", []), *oracle.get("mixed_edge_ids", []), *expected})
    duplicates = set(product.get("duplicate_visual_owner_ids", []))
    out = []
    for edge_id in ids:
        solid_id, _, pair = edge_id.partition("::edge:")
        solid = solids.get(solid_id)
        if solid is None:
            continue
        a_id, b_id = pair.split("-", 1)
        index = {v: i for i, v in enumerate(solid["vertex_ids"])}
        points = [tuple(float(Fraction(str(c))) for c in solid["vertices"][index[v]]) for v in (a_id, b_id)]
        observed, oracle_vis = _visibility(edge_id, product), _visibility(edge_id, oracle)
        out.append({
            "machine_edge_id": edge_id,
            "display_label": labels.get(a_id, a_id) + labels.get(b_id, b_id),
            "expected_visibility": expected.get(edge_id),
            "observed_visibility": observed,
            "oracle_visibility": oracle_vis,
            "oracle_agreement": observed == oracle_vis,
            "visual_owner_count": ">=2" if edge_id in duplicates else 1,
            "dash_signature": product.get("dash_signature", {}).get(edge_id),
            "endpoints_px": [list(_project(p, camera).screen) for p in points],
        })
    return out


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _path(value: Any) -> Path | None:
    raw = value.get("path") if isinstance(value, dict) else value
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def _sheet(cells: list[list[tuple[str, Path | None]]], out: Path, cell=CELL) -> None:
    rows, cols = len(cells), max((len(r) for r in cells), default=1)
    sheet = Image.new("RGB", (cols * cell[0], rows * (cell[1] + 24)), "white")
    draw = ImageDraw.Draw(sheet)
    for r, row in enumerate(cells):
        for c, (label, path) in enumerate(row):
            x, y = c * cell[0], r * (cell[1] + 24)
            draw.text((x + 8, y + 6), label, fill="black")
            if path and path.exists():
                image = Image.open(path).convert("RGB")
                image.thumbnail(cell)
                sheet.paste(image, (x, y + 24))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def build(run_dir: Path, browser: dict[str, Any], measurement: dict[str, Any], fixture_root: Path,
          expectations: dict[str, Any] | None, playback: dict[str, Any] | None) -> dict[str, Any]:
    images = run_dir / "images"
    main_rows, appendix_rows, crops = [], [], []
    for family, scenario in browser.get("scenarios", {}).items():
        scene = json.loads((fixture_root / "fixtures" / f"{family}_positive.json")
                           .read_text(encoding="utf-8"))["envelope"]["scene3d"]
        positive = scenario.get("positive", {})
        main_rows.append([(f"{family} · {vp} · {state}",
                           _path(positive.get(vp, {}).get("screenshots", {}).get(state)))
                          for vp, state in MAIN_COLUMNS])
        formation = positive.get("desktop", {}).get("formation", {}).get("steps", [])
        appendix_rows.append([(f"{family} · formation {s.get('index')}", _path(s.get("screenshot")))
                              for s in formation if s.get("screenshot")])
        for viewport, record in positive.items():
            for state in STATES:
                # Hộp canvas lúc chụp CHÍNH ảnh ấy; `canvas_box` chung chỉ là dự phòng.
                box = ((record.get("canvas_boxes") or {}).get(state)
                       or record.get("canvas_box") or {"x": 0, "y": 0})
                shot = _path(record.get("screenshots", {}).get(state))
                snap = record.get("camera_snapshots", {}).get(state, {}).get("snapshot")
                product = record.get(f"edge_semantics_{state}")
                oracle = measurement.get("scenarios", {}).get(family, {}).get(viewport, {}).get(state, {}).get("oracle")
                if not (shot and shot.exists() and snap and product and oracle is not None):
                    continue
                expected = {}
                for item in (expectations or {}).get("scenarios", []):
                    if (item["scenario_id"], item["viewport"], item["state"]) == (family, viewport, state):
                        expected = {**{e: "VISIBLE" for e in item["expected_visible_ids"]},
                                    **{e: "HIDDEN" for e in item["expected_hidden_ids"]},
                                    **{e: "MIXED" for e in item["expected_mixed_ids"]}}
                        expected = {k: v for k, v in expected.items() if v != "VISIBLE"}
                image = Image.open(shot).convert("RGB")
                dpr = float(snap.get("device_pixel_ratio", 1))
                for rec in edge_records(scene, snap, product, oracle, expected):
                    pts = [(box["x"] * dpr + x, box["y"] * dpr + y) for x, y in rec["endpoints_px"]]
                    crop = crop_box(pts[0], pts[1], image.size, int(24 * dpr), int(96 * dpr))
                    rec["endpoints_inside_image"] = all(0 <= x <= image.width and 0 <= y <= image.height
                                                        for x, y in pts)
                    name = f"{state}__{rec['display_label']}__{rec['observed_visibility'].lower()}.png"
                    target = images / "crops" / family / viewport / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    image.crop(crop).save(target)
                    crops.append({"family": family, "viewport": viewport, "state": state, **rec,
                                  "crop_box_px": list(crop), "source": shot.relative_to(REPO_ROOT).as_posix(),
                                  "path": target.relative_to(run_dir).as_posix(), "sha256": _sha(target)})
    for run in (playback or {}).get("runs", []):
        appendix_rows.append([(f"{run['family']} · {run['viewport']} · playback {f.get('step')}",
                               _path(f.get("path"))) for f in run.get("film", [])])
    _sheet(main_rows, images / "contact-sheet.png")
    _sheet([r for r in appendix_rows if r], images / "contact-sheet-appendix-formation.png", (360, 240))
    index = {"schema_version": "scene3d-hidden-edge-crops/1",
             "rule": "each crop contains both endpoints projected by the independent oracle from the recorded camera",
             "crops": crops,
             "all_endpoints_inside": all(c["endpoints_inside_image"] for c in crops),
             "oracle_disagreements": [c for c in crops if not c["oracle_agreement"]],
             "duplicate_owner_edges": [c for c in crops if c["visual_owner_count"] != 1]}
    (images / "crops").mkdir(parents=True, exist_ok=True)
    (images / "crops" / "CROPS_INDEX.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--browser", required=True, type=Path)
    parser.add_argument("--measurement", required=True, type=Path)
    parser.add_argument("--fixture-root", required=True, type=Path)
    parser.add_argument("--expectations", type=Path)
    parser.add_argument("--playback", type=Path)
    args = parser.parse_args()
    load = lambda p: json.loads(p.read_text(encoding="utf-8")) if p else None  # noqa: E731
    index = build(args.run_dir, load(args.browser), load(args.measurement), args.fixture_root,
                  load(args.expectations), load(args.playback))
    print(f"{len(index['crops'])} crops · endpoints inside: {index['all_endpoints_inside']} · "
          f"oracle disagreements: {len(index['oracle_disagreements'])} · "
          f"duplicate owners: {len(index['duplicate_owner_edges'])}")
    return 0 if index["all_endpoints_inside"] and not index["oracle_disagreements"] \
        and not index["duplicate_owner_edges"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
