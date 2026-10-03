# -*- coding: utf-8 -*-
"""Contact sheets and hidden-edge crops from the authoritative PNGs (w10 → w11 → w12).

w12: the step bar walks GEOMETRY steps; each sheet adds the solution panel
(element captures, used whole) and the grounding refusal of the family.

w11 layout (review W10-H8: the formation appendix was too small to read):
``images/<family>/SHEET.png`` holds ONE family at NATIVE resolution — desktop
neutral · causal · rotated, mobile neutral, then every formation step with its
narration as a large label — under a legend band. ``images/overview/`` is only
an index of the six family sheets. Source screenshots stay full-resolution in
the family folder; diagnostics never enter an acceptance sheet.

Every crop contains BOTH endpoints of its edge (projected by the independent
oracle from the recorded camera) and is listed in ``results/HIDDEN_EDGE_CROPS.json``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from measure_scene3d_occlusion import _camera
from scene3d_occlusion_oracle import _project

REPO_ROOT = Path(__file__).resolve().parents[2]
FAMILY_ORDER = ("triangular_pyramid", "triangular_prism", "rectangular_pyramid",
                "cuboid", "cube", "cross_section")
SHEET_STATES = (("desktop", "neutral_final"), ("desktop", "causal_selected"),
                ("desktop", "rotated_neutral"), ("mobile", "neutral_final"))
# W12: ảnh PHẦN TỬ của bảng lời giải — dùng nguyên, không cắt theo canvas.
PANEL_STATES = (("desktop", "solution_neutral_final"), ("desktop", "solution_causal_selected"),
                ("mobile", "solution_neutral_final"), ("mobile", "solution_expanded"))
STATE_TITLES = {"neutral_final": "trung tính, bước cuối",
                "causal_selected": "causal — đã chọn đáp số",
                "rotated_neutral": "đã xoay (qua cổng không suy biến)",
                "solution_neutral_final": "bảng lời giải, bước cuối",
                "solution_causal_selected": "bảng lời giải — đã chọn đáp số (vai trò + chú giải)",
                "solution_expanded": "bảng lời giải — mở dữ kiện và các bước tính",
                "annotations_off": "tắt Số đo và Kết quả — chỉ nhãn đổi",
                "causal_restored": "bỏ chọn — cùng camera, cùng vị trí cuộn"}
#: W16 §14.5 — tên NGƯỜI XEM của từng loại âm mà bộ chạy ghi (`negative[kind][viewport]`).
#: Bảng ĐÓNG: loại lạ ⇒ `KeyError`, không in token máy lên ảnh.
TEN_TU_CHOI = {"ungrounded_source": "dữ kiện không có trong đề — từ chối, không dựng hình",
               "assumption": "đáp số phụ thuộc kích thước đề không cho — từ chối",
               "topology_kernel": "bảng mặt / hình học không dựng được — từ chối"}
#: W17 §15.5 — loại từ chối THÊM, chỉ ở họ khai nó (bắt buộc đủ hai viewport khi có mặt).
TEN_TU_CHOI_W17 = {"construction_mismatch": "đề cắt bằng (β), hệ cắt bằng (α) — từ chối, đề không cần sửa",
                   "system_cause": "đề hợp lệ, số liệu của hệ sai — từ chối, lỗi của hệ"}
#: W17 — ca PHỤC VỤ thêm (`served[kind][viewport]`). Bảng đóng như `TEN_TU_CHOI`.
TEN_PHUC_VU = {"correct_plane": "cắt đúng mặt phẳng đề nói — được phục vụ"}
#: W17 — ảnh của trang dương chỉ có khi bộ chạy đã ĐO điều tương ứng: (khoá bản ghi, trạng thái).
W17_STATES = (("annotation_toggle", "annotations_off"), ("causal_restore", "causal_restored"))
#: Ô từ chối ĐỌC ĐƯỢC ⇔ hộp đoạn lời (`refusal_message_box`) có ít nhất tỉ lệ này điểm ảnh
#: mực (độ sáng < `DO_SANG_MUC`). Ảnh chụp trắng có 0; vài dòng chữ có cỡ vài phần trăm.
MUC_TOI_THIEU, DO_SANG_MUC = 0.005, 100


class ThieuAnhBangChung(ValueError):
    """Một ô bắt buộc của sheet thiếu ảnh hoặc không đọc được — bộ dựng THẤT BẠI, không bao
    giờ thay bằng ô trắng (W16 §14.5)."""
# Hai dòng: một dòng cũ bị cắt ở mép phải sheet. Vật đã dựng giữ MÀU KIỂU ở
# khung trung tính — chú giải không được hứa "trung tính" cho chúng (w12).
LEGEND = ("XANH = đang xét (vật vừa dựng ở bước đang phát, hoặc vật được chọn) · vật đã dựng giữ MÀU KIỂU: "
          "khối xám, mặt phẳng tím, thiết diện hổ phách, đường xanh két, điểm dựng đỏ · NÉT ĐỨT = cạnh khuất.\n"
          "Causal (bấm một dòng của bảng lời giải): xanh = đích · cam đậm = dữ kiện số · cam nhạt = trung gian số "
          "· xám = mọi hình trong chuỗi (ngữ cảnh) · mờ = ngoài chuỗi.")
LABEL_PX = 28
HEADER_CSS = 44   # hàng tiêu đề + chip ngay trên canvas: giữ, bỏ thanh điều hướng
STATES = ("neutral_final", "rotated_neutral")
#: W14 — tên NGƯỜI XEM của từng vai trò dựng hình, theo thứ tự kế hoạch. Token máy
#: (`CONSTRUCT_BASE`…) không bao giờ lên ảnh: vai trò lạ ⇒ `KeyError`, không in thô.
TEN_VAI_TRO = {
    "DECLARE_ENTITIES": "các điểm dữ kiện", "CONSTRUCT_BASE": "đáy", "CONSTRUCT_HEIGHT": "đường cao",
    "CONSTRUCT_TRANSLATED_FACE": "đáy trên", "CONSTRUCT_LATERAL_BOUNDARY": "cạnh bên",
    "CLOSE_SOLID": "khép khối", "CONSTRUCT_CUTTING_OBJECT": "mặt cắt",
    "CONSTRUCT_INTERSECTION": "cạnh thiết diện", "CLOSE_SECTION": "khép thiết diện",
    "CONSTRUCT_AUXILIARY_GEOMETRY": "dựng phụ",
}
FILM_CELL_W = 640


def chu_thich_buoc(step: dict[str, Any], k: int, n: int) -> str:
    """`Bước dựng 2/5 · đường cao, cạnh bên — <lời kể>` (bước thiếu vai trò: không có đoạn giữa)."""
    vai = set(step.get("formation_roles") or ())
    if vai - TEN_VAI_TRO.keys():
        raise KeyError(f"vai trò chưa có tên người xem: {sorted(vai - TEN_VAI_TRO.keys())}")
    ten = [v for r, v in TEN_VAI_TRO.items() if r in vai]
    giua = f" · {', '.join(ten)}" if ten else ""
    return f"Bước dựng {k + 1}/{n}{giua} — {str(step.get('learner_text', '')).strip()}"


def _xuong_dong(text: str, font: Any, width: int) -> list[str]:
    """Gói chữ theo bề ngang đo bằng CHÍNH phông vẽ — dòng nào cũng nằm trọn trong ô."""
    dong: list[str] = []
    for tu in text.split():
        thu = f"{dong[-1]} {tu}" if dong else tu
        if dong and font.getlength(thu) <= width:
            dong[-1] = thu
        else:
            dong.append(tu)
    return dong


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


def image_scale(record: dict[str, Any], image_width: int) -> float:
    """Điểm ảnh của ẢNH chụp trên một CSS px. Không lấy dpr của renderer: ảnh
    mobile 780 px cho khung 390 CSS px trong khi renderer khai dpr 1 — dùng dpr
    ấy thì crop mobile cắt sai vùng (w10)."""
    width = (record.get("viewport") or {}).get("width")
    return image_width / width if width else 1.0


def to_image_px(box: dict[str, float], screen: tuple[float, float], render_dpr: float,
                scale: float) -> tuple[float, float]:
    """Điểm oracle (px vật lý của canvas theo dpr renderer) → px của ẢNH."""
    return ((box["x"] + screen[0] / render_dpr) * scale, (box["y"] + screen[1] / render_dpr) * scale)


def stage_box(record: dict[str, Any], state: str, size: tuple[int, int],
              readout_css: int = 80) -> tuple[int, int, int, int] | None:
    """Vùng SÂN KHẤU của một ảnh: hộp canvas lúc chụp + dải số đo ngay dưới.
    Sheet chính cắt vùng này thay vì thu cả trang — nếu không hình chỉ còn
    một góc nhỏ của mỗi ô."""
    box = (record.get("canvas_boxes") or {}).get(state) or record.get("canvas_box")
    if not box:
        return None
    s = image_scale(record, size[0])
    x0, y0 = max(0, int(box["x"] * s)), max(0, int(box["y"] * s))
    x1 = min(size[0], int((box["x"] + box["w"]) * s))
    y1 = min(size[1], int((box["y"] + box["h"] + readout_css) * s))
    return (x0, y0, x1, y1) if x1 > x0 and y1 > y0 else None


def family_dir(family: str) -> str:
    return family.replace("_", "-")


def _font(size: int) -> tuple[Any, str]:
    """Phông có dấu tiếng Việt; phông bitmap mặc định chỉ cao ~10 px."""
    for name in ("arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size), name
        except OSError:
            continue
    return ImageFont.load_default(size=size), "pillow-default"


def page_box(record: dict[str, Any], state: str, size: tuple[int, int]) -> tuple[int, int, int, int]:
    """Cả trang từ hàng tiêu đề ngay trên canvas tới đáy (số đo, điều khiển,
    "Đang dựng/Dựa trên", lời kể) — bỏ thanh điều hướng. KHÔNG thu nhỏ."""
    box = (record.get("canvas_boxes") or {}).get(state) or record.get("canvas_box") or {"y": 0}
    top = max(0, int((box["y"] - HEADER_CSS) * image_scale(record, size[0])))
    return 0, min(top, size[1] - 1), size[0], size[1]


def _save_png(image: Image.Image, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, optimize=True)


def _loi_tu_choi(record: dict[str, Any], path: Path | None, fam: str, kind: str, vp: str) -> str | None:
    """Lý do một ô từ chối KHÔNG dùng được, hoặc None: đúng tệp của loại × viewport, bản ghi là
    một lời từ chối không canvas có lời cho người học, và hộp đoạn lời trong ảnh có chữ."""
    if path is None or not path.exists():
        return "image missing"
    if not path.as_posix().endswith(f"{fam}/negative/{kind}/{vp}/refusal.png"):
        return f"image {path.as_posix()} is not {fam}/negative/{kind}/{vp}/refusal.png"
    obs = record.get("observed") or {}
    if not (record.get("pass") and obs.get("canvas") is False and (obs.get("unsupported") or {}).get("learner_reason")):
        return "record is not a passing no-canvas refusal with a learner message"
    hop = record.get("refusal_message_box")
    if not hop:
        return "no refusal_message_box recorded"
    image = Image.open(path).convert("L")
    s = image_scale(record, image.width)
    x0, y0, x1, y1 = (int(hop["x"] * s), int(hop["y"] * s), int((hop["x"] + hop["w"]) * s),
                      int((hop["y"] + hop["h"]) * s))
    if x0 < 0 or y0 < 0 or x1 > image.width or y1 > image.height or x1 <= x0 or y1 <= y0:
        return "refusal message box outside the capture"
    vung = image.crop((x0, y0, x1, y1))
    muc = sum(vung.histogram()[:DO_SANG_MUC]) / (vung.width * vung.height)
    return None if muc >= MUC_TOI_THIEU else f"refusal message unreadable (ink {muc:.4f} < {MUC_TOI_THIEU})"


def family_sheet(family: str, scenario: dict[str, Any], images_root: Path) -> dict[str, Any]:
    """Sheet của MỘT họ, độ phân giải gốc: 4 trạng thái, bảng lời giải, lời từ
    chối (W12; W16: ba loại × hai viewport), rồi mọi BƯỚC DỰNG của thanh bước.
    Thiếu ảnh hoặc ô từ chối không đọc được ⇒ `ThieuAnhBangChung` (W16 §14.5)."""
    records = scenario.get("positive", {})
    cells: list[dict[str, Any]] = []
    loi: list[str] = []
    for vp, state in SHEET_STATES:
        record = records.get(vp, {})
        cells.append({"state": f"{vp}/{state}", "label": f"{vp.capitalize()} · {STATE_TITLES[state]}",
                      "path": _path(record.get("screenshots", {}).get(state)), "record": record,
                      "box_state": state, "crop": True})
    for vp, state in PANEL_STATES + tuple((vp, s) for vp in ("desktop", "mobile") for khoa, s in W17_STATES
                                          if khoa in records.get(vp, {})):
        record = records.get(vp, {})
        cells.append({"state": f"{vp}/{state}", "label": f"{vp.capitalize()} · {STATE_TITLES[state]}",
                      "path": _path(record.get("screenshots", {}).get(state)), "record": record,
                      "box_state": state, "crop": False})
    am = scenario.get("negative", {})
    if la := sorted(set(am) - TEN_TU_CHOI.keys() - TEN_TU_CHOI_W17.keys()):
        raise KeyError(f"loại từ chối chưa có tên người xem: {la}")
    for kind, ten in {**TEN_TU_CHOI, **{k: v for k, v in TEN_TU_CHOI_W17.items() if k in am}}.items():
        for vp in ("desktop", "mobile"):
            record, state = (am.get(kind) or {}).get(vp), f"negative/{kind}/{vp}"
            ly_do = "no record" if record is None else _loi_tu_choi(
                record, _path(record.get("screenshot")), family_dir(family), kind, vp)
            if ly_do:
                loi.append(f"{state}: {ly_do}")
                continue
            cells.append({"state": state, "label": f"{vp.capitalize()} · {ten}",
                          "path": _path(record.get("screenshot")), "record": record,
                          "box_state": "refusal", "crop": False})
    pv = scenario.get("served", {})
    if la := sorted(set(pv) - TEN_PHUC_VU.keys()):
        raise KeyError(f"ca phục vụ chưa có tên người xem: {la}")
    for kind in pv:
        for vp in ("desktop", "mobile"):
            record, state = pv[kind].get(vp), f"served/{kind}/{vp}"
            if not (record or {}).get("pass"):
                loi.append(f"{state}: {'no record' if record is None else 'record is not a passing served case'}")
                continue
            cells.append({"state": state, "label": f"{vp.capitalize()} · {TEN_PHUC_VU[kind]}",
                          "path": _path(record.get("screenshot")), "record": record,
                          "box_state": "served", "crop": False})
    steps = [s for s in records.get("desktop", {}).get("formation", {}).get("steps", []) if s.get("screenshot")]
    for s in steps:
        cells.append({"state": f"desktop/geometry_step/{s['index']}",
                      "label": chu_thich_buoc(s, s["index"], len(steps)),
                      "path": _path(s.get("screenshot")), "record": records.get("desktop", {}),
                      "box_state": "neutral_final", "crop": True})
    loi += [f"{c['state']}: image missing" for c in cells if not (c["path"] and c["path"].exists())]
    if loi:
        raise ThieuAnhBangChung(f"{family}: " + "; ".join(loi))
    font, font_name = _font(LABEL_PX)
    band = LABEL_PX * 2
    images = []
    for c in cells:
        image = Image.open(c["path"]).convert("RGB")
        c["crop_box_px"] = (list(page_box(c["record"], c["box_state"], image.size)) if c["crop"]
                            else [0, 0, image.width, image.height])
        images.append(image.crop(tuple(c["crop_box_px"])))
    col_w = max(i.width for i in images)
    heights = [i.height + band for i in images]
    rows = [max(heights[k:k + 2]) for k in range(0, len(cells), 2)]
    legend_font, _ = _font(LABEL_PX - 2)
    legend_h = LABEL_PX * 4
    sheet = Image.new("RGB", (2 * col_w, legend_h + sum(rows)), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 12), f"{family_dir(family)} — chú giải", fill="black", font=font)
    draw.text((16, 12 + LABEL_PX + 12), LEGEND, fill="black", font=legend_font)
    y = legend_h
    for r, h in enumerate(rows):
        for k in (2 * r, 2 * r + 1):
            if k >= len(cells):
                continue
            x = (k % 2) * col_w
            draw.text((x + 12, y + 10), cells[k]["label"], fill="black", font=font)
            sheet.paste(images[k], (x, y + band))
        y += h
    out = images_root / family_dir(family) / "SHEET.png"
    _save_png(sheet, out)
    return {
        "family": family, "sheet": out, "legend": LEGEND, "label_font_px": LABEL_PX, "font": font_name,
        "cells": [{"state": c["state"], "label": c["label"], "scale": 1.0, "crop_box_px": c["crop_box_px"],
                   "source": c["path"].as_posix() if c["path"] else None} for c in cells],
    }


def filmstrip(family: str, scenario: dict[str, Any], images_root: Path) -> dict[str, Any] | None:
    """W14: mọi bước dựng desktop từ trái sang phải, mỗi ô = sân khấu canvas + chú
    thích (tên vai trò + lời kể) gói dòng trong bề ngang ô. Đọc liền một mạch
    được: đáy → đường cao/đáy trên → cạnh bên → khép khối."""
    record = scenario.get("positive", {}).get("desktop", {})
    steps = [s for s in record.get("formation", {}).get("steps", []) if s.get("screenshot")]
    if not steps:
        return None
    font, font_name = _font(LABEL_PX - 4)
    dong_cao = int((LABEL_PX - 4) * 1.35)
    o: list[tuple[Image.Image, list[str], str]] = []
    thieu = [f"desktop/geometry_step/{s.get('index', k)}" for k, s in enumerate(steps)
             if not ((p := _path(s.get("screenshot"))) and p.exists())]
    if thieu:
        raise ThieuAnhBangChung(f"{family} filmstrip: image missing for " + ", ".join(thieu))
    for k, s in enumerate(steps):
        image = Image.open(_path(s.get("screenshot"))).convert("RGB")
        box = stage_box(record, "neutral_final", image.size)
        image = image.crop(box) if box else image
        image.thumbnail((FILM_CELL_W, 10_000))
        cau = chu_thich_buoc(s, k, len(steps))
        o.append((image, _xuong_dong(cau, font, FILM_CELL_W - 24), cau))
    anh_cao = max(i.height for i, _, _ in o)
    chu_cao = max(len(d) for _, d, _ in o) * dong_cao + 16
    strip = Image.new("RGB", (len(o) * FILM_CELL_W, anh_cao + chu_cao), "white")
    draw = ImageDraw.Draw(strip)
    for k, (image, dong, _) in enumerate(o):
        x = k * FILM_CELL_W
        strip.paste(image, (x, 0))
        for d, chu in enumerate(dong):
            draw.text((x + 12, anh_cao + 8 + d * dong_cao), chu, fill="black", font=font)
        if k:
            draw.line([(x, 0), (x, strip.height)], fill="#bbbbbb", width=2)
    out = images_root / family_dir(family) / "FILMSTRIP.png"
    _save_png(strip, out)
    return {"filmstrip": out, "cell_width_px": FILM_CELL_W, "font": font_name, "font_px": LABEL_PX - 4,
            "captions": [c for _, _, c in o], "caption_lines": [d for _, d, _ in o]}


def overview_index(families: dict[str, dict[str, Any]], images_root: Path) -> dict[str, Any]:
    """Mục lục sáu họ — ảnh nhỏ + đường dẫn sheet. KHÔNG thay sheet của họ."""
    font, _ = _font(LABEL_PX)
    rows = [{"family": f, "family_dir": family_dir(f), "sheet": families[f]["sheet"]}
            for f in FAMILY_ORDER if f in families]
    cell = (720, 520)
    sheet = Image.new("RGB", (3 * cell[0], 2 * cell[1]), "white")
    draw = ImageDraw.Draw(sheet)
    for k, row in enumerate(rows):
        x, y = (k % 3) * cell[0], (k // 3) * cell[1]
        draw.text((x + 12, y + 8), row["family_dir"], fill="black", font=font)
        draw.text((x + 12, y + cell[1] - LABEL_PX - 12), f"→ {row['sheet']}", fill="black", font=font)
        thumb = families[row["family"]].get("thumbnail")
        if thumb and Path(thumb).exists():
            image = Image.open(thumb).convert("RGB")
            image.thumbnail((cell[0] - 24, cell[1] - 3 * LABEL_PX - 24))
            sheet.paste(image, (x + 12, y + LABEL_PX + 20))
    _save_png(sheet, images_root / "overview" / "INDEX.png")
    index = {"schema_version": "scene3d-evidence-overview/1", "role": "INDEX_ONLY",
             "families": rows, "legend": LEGEND}
    (images_root / "overview" / "INDEX.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index


def build(run_dir: Path, browser: dict[str, Any], measurement: dict[str, Any], fixture_root: Path,
          expectations: dict[str, Any] | None, playback: dict[str, Any] | None) -> dict[str, Any]:
    images = run_dir / "images"
    crops, sheets = [], {}
    for family, scenario in browser.get("scenarios", {}).items():
        scene = json.loads((fixture_root / "fixtures" / f"{family}_positive.json")
                           .read_text(encoding="utf-8"))["envelope"]["scene3d"]
        positive = scenario.get("positive", {})
        meta = family_sheet(family, scenario, images)
        meta["thumbnail"] = _path(positive.get("desktop", {}).get("screenshots", {}).get("neutral_final"))
        meta["sheet"] = meta["sheet"].relative_to(run_dir).as_posix()
        film = filmstrip(family, scenario, images)
        if film is not None:
            film["filmstrip"] = film["filmstrip"].relative_to(run_dir).as_posix()
        meta["filmstrip"] = film
        sheets[family] = meta
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
                scale = image_scale(record, image.width)
                for rec in edge_records(scene, snap, product, oracle, expected):
                    pts = [to_image_px(box, (x, y), dpr, scale) for x, y in rec["endpoints_px"]]
                    crop = crop_box(pts[0], pts[1], image.size, int(24 * scale), int(96 * scale))
                    rec["endpoints_inside_image"] = all(0 <= x <= image.width and 0 <= y <= image.height
                                                        for x, y in pts)
                    name = f"{state}__{rec['display_label']}__{rec['observed_visibility'].lower()}.png"
                    target = images / family_dir(family) / "hidden-edges" / viewport / name
                    _save_png(image.crop(crop), target)
                    crops.append({"family": family, "viewport": viewport, "state": state, **rec,
                                  "crop_box_px": list(crop), "source": shot.relative_to(REPO_ROOT).as_posix(),
                                  "path": target.relative_to(run_dir).as_posix(), "sha256": _sha(target)})
    overview = overview_index(sheets, images)
    for meta in sheets.values():
        meta.pop("thumbnail", None)
    # Phim playback người học: nguồn tham khảo cạnh sheet, không vào sheet.
    films: dict[str, list[str]] = {}
    for run in (playback or {}).get("runs", []):
        films.setdefault(run["family"], []).extend(str(f.get("path")) for f in run.get("film", []))
    index = {"schema_version": "scene3d-hidden-edge-crops/2",
             "rule": "each crop contains both endpoints projected by the independent oracle from the recorded camera",
             "family_sheets": sheets, "overview": overview, "playback_films": films,
             "crops": crops,
             "all_endpoints_inside": all(c["endpoints_inside_image"] for c in crops),
             "oracle_disagreements": [c for c in crops if not c["oracle_agreement"]],
             "duplicate_owner_edges": [c for c in crops if c["visual_owner_count"] != 1]}
    (run_dir / "results").mkdir(parents=True, exist_ok=True)
    (run_dir / "results" / "HIDDEN_EDGE_CROPS.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
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
