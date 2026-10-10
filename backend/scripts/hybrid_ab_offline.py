# -*- coding: utf-8 -*-
"""A/B OFFLINE của run `hybrid-compiler-selection`: nhánh A (lời gọi hàm) vs nhánh B (dữ kiện có kiểu → planner). **0 API call.**

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/hybrid_ab_offline.py --out-dir <thư mục>

· 14 ca holdout tiền đăng ký (`tests/geometry/fixtures/hybrid_holdout_cases.json`): lời gọi A và dữ kiện B đều VIẾT TAY.
· 58 ca cũ (27 gốc + 23 diễn đạt + 8 mở rộng): dữ kiện B chuyển CƠ HỌC từ lời gọi A bằng `facts_from_calls` ⇒ chỉ kiểm PARITY
  (B tái lập A khi AI trích hoàn hảo), KHÔNG kiểm tổng quát hoá — đừng đọc số này như năng lực của B.
Mọi đầu vào đóng vai AI trích ĐÚNG; số ở đây không đo Gemini. Hạng: correct_served · wrong_served · correct_refusal ·
false_refusal · unsupported · infrastructure_failure.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
FX = BACKEND / "tests" / "geometry" / "fixtures"
LEGACY = ("text_to_functions_cases.json", "paraphrase_cases.json", "geometry_expansion_cases.json")
HOLDOUT = "hybrid_holdout_cases.json"
HA_TANG = ("ENGINE_IR_INVALID", "ENGINE_EXECUTION_FAILED", "SCENE_BUILD_FAILED", "PROVIDER_ERROR", "TOOL_ERROR",
           "ENGINE_SELF_CHECK_FAILED")
_SO = re.compile(r"^(?P<dau>-)?(?P<he>\d+(?:/\d+)?)?(?:√(?P<can>\d+))?(?:/(?P<mau>\d+))?$")


# ── so đáp số chính xác ──────────────────────────────────────────────────────
def khoa_dap_so(s: str) -> tuple:
    """Chuỗi đáp số → khoá chính xác (dấu, giá trị²) — `cos²=…` giữ nguyên; dạng ký hiệu `a³√2/3` → (bậc, giá trị² hệ số)."""
    if s.startswith("cos²="):
        return ("cos2", Fraction(s[5:]))
    m = re.fullmatch(r"(?P<tu>\d*)a(?P<mu>[²³]?)(?:√(?P<can>\d+))?(?:/(?P<mau>\d+))?", s)
    if m:
        he = Fraction(int(m["tu"] or 1), int(m["mau"] or 1))
        return ("a", {"": 1, "²": 2, "³": 3}[m["mu"]], he * he * int(m["can"] or 1))
    m = _SO.match(s)
    he = Fraction(m["he"] or 1) / Fraction(m["mau"] or 1)
    return ("so", -1 if m["dau"] else 1, he * he * int(m["can"] or 1))


def dap_so_khop(nhan: dict, r) -> bool:
    for cid, v in nhan.items():
        if isinstance(v, dict):
            ex = (r.answer_exact or {}).get(cid)
            if not ex or ex["dim"] != v["dim"] or khoa_dap_so(ex["coef"])[1:] != khoa_dap_so(v["coef"])[1:]:
                return False
        elif cid not in r.answers or khoa_dap_so(r.answers[cid]) != khoa_dap_so(v):
            return False
    return True


def phan_hang(ky_vong: dict, hang_ky_vong: str, r) -> str:
    """Hạng của MỘT kết cục so với kỳ vọng đăng ký trước."""
    if r.status == "SERVED":
        if ky_vong["status"] == "SERVED" and dap_so_khop(ky_vong["answers"], r):
            return "correct_served"
        return "wrong_served"
    if r.code in HA_TANG:
        return "infrastructure_failure"
    if ky_vong["status"] == "SERVED":
        return "false_refusal"
    return hang_ky_vong if hang_ky_vong in ("correct_refusal", "unsupported") else "correct_refusal"


# ── chuyển CƠ HỌC lời gọi A → dữ kiện B (parity) ─────────────────────────────
_KHUON = {3: "equilateral_triangle", 4: "square", 6: "regular_hexagon"}


def facts_from_calls(calls: list[dict]) -> list[dict]:
    """Giả định AI trích HOÀN HẢO đúng các mệnh đề mà lời gọi A dùng. Vai trò độ dài suy theo quote ('cạnh bên', 'cạnh đáy')
    khi quote không có nhãn đoạn — gần với cách một AI nhánh B sẽ điền. Vai trò mệnh đề luôn `premise` (như A khai)."""
    khoi = [c for c in calls if c["fn"] in ("pyramid", "regular_pyramid", "prism")]
    ten_khoi = lambda c: (c["args"]["apex"] + "." + "".join(c["args"]["base"]) if c["fn"] != "prism"  # noqa: E731
                          else "".join(c["args"]["base"]) + "." + "".join(c["args"]["top"]))
    out = []
    for c in calls:
        a, fn = c["args"], c["fn"]
        q = c["source"].get("quotes") or [c["source"]["quote"]]
        b = {"id": c["id"], "role": "question" if fn.startswith("ask_") else "premise", "negated": False,
             "ambiguous": False, "quotes": q}
        if fn in ("pyramid", "regular_pyramid"):
            b.update(kind="solid", solid=ten_khoi(c), solid_type="pyramid", regular=fn == "regular_pyramid")
        elif fn == "prism":
            b.update(kind="solid", solid=ten_khoi(c), solid_type="prism", right=a["right"])
        elif fn == "regular_polygon":
            b.update(kind="polygon_shape", points=a["vertices"], shape=_KHUON.get(len(a["vertices"]), "regular_polygon"),
                     value=a.get("side"))
        elif fn == "rectangle":
            b.update(kind="polygon_shape", points=a["vertices"], shape="rectangle")
        elif fn == "right_angle":
            b.update(kind="right_angle", at=a["vertex"], points=a["rays"])
        elif fn == "segment_length":
            seg, txt = a["segment"], " ".join(q).lower()
            co_nhan = any(seg[0] + seg[1] in x or seg[1] + seg[0] in x for x in q)
            if not co_nhan and "cạnh bên" in txt and len(khoi) == 1:
                b.update(kind="length", measure="lateral_edge", solid=ten_khoi(khoi[0]), value=a["value"])
            else:
                b.update(kind="length", measure="segment", points=seg, value=a["value"])
        elif fn == "height":
            b.update(kind="length", measure="height", solid=a["solid"], value=a["value"])
        elif fn == "equal_length":
            b.update(kind="equal_lengths", points_a=a["segment_a"], points_b=a["segment_b"])
        elif fn == "perpendicular_line_plane":
            b.update(kind="perpendicular", points_a=a["line"], points_b=a["plane"])
        elif fn == "perpendicular_lines":
            b.update(kind="perpendicular", points_a=a["line1"], points_b=a["line2"])
        elif fn == "face_perpendicular_base":
            b.update(kind="perpendicular", points_a=a["face"], points_b=a["base"])
        elif fn == "altitude":
            b.update(kind="altitude", points=[a["apex"], a["foot"]], solid=a["solid"])
        elif fn == "orthogonal_projection":
            b.update(kind="projection", point=a["point"], points=a["plane"], at=a["image"])
        elif fn in ("midpoint", "centroid"):
            b.update(kind="point_def", point=a["point"], point_kind=fn, points=a.get("segment") or a.get("polygon"))
        elif fn == "ask_volume":
            b.update(kind="question", quantity="volume", solid=a["solid"])
        elif fn == "ask_area":
            b.update(kind="question", quantity="area", points=a["polygon"])
        elif fn == "ask_length":
            b.update(kind="question", quantity="length", points=a["segment"])
        elif fn == "ask_distance_point_plane":
            b.update(kind="question", quantity="distance", points_a=[a["point"]], points_b=a["plane"])
        elif fn == "ask_distance_lines":
            b.update(kind="question", quantity="distance", points_a=a["line1"], points_b=a["line2"])
        elif fn == "ask_angle_line_plane":
            b.update(kind="question", quantity="angle", points_a=a["line"], points_b=a["plane"])
        elif fn == "ask_angle_plane_plane":
            b.update(kind="question", quantity="angle", points_a=a["plane1"], points_b=a["plane2"])
        elif fn == "unsupported":
            b.update(kind="unsupported", reason=a["reason"])
        else:
            b.update(kind=fn)                                        # hàm lạ (ca G5): để lược đồ dữ kiện từ chối
        # Ô mà lời gọi A mang nhưng ánh xạ trên không dùng (vd `apex_xyz` lén đưa toạ độ ở ca G6) đi NGUYÊN sang dữ kiện:
        # lược đồ đóng của nhánh B phải tự bác — bộ chuyển đổi không được "làm sạch" hộ.
        b.update({k: v for k, v in a.items() if k not in _DUNG.get(fn, set(a))})
        out.append(b)
    return out


_DUNG = {"pyramid": {"apex", "base"}, "regular_pyramid": {"apex", "base"}, "prism": {"base", "top", "right"},
         "regular_polygon": {"vertices", "side"}, "rectangle": {"vertices"}, "right_angle": {"vertex", "rays"},
         "segment_length": {"segment", "value"}, "height": {"solid", "value"}, "equal_length": {"segment_a", "segment_b"},
         "perpendicular_line_plane": {"line", "plane"}, "perpendicular_lines": {"line1", "line2"},
         "face_perpendicular_base": {"face", "base"}, "altitude": {"apex", "foot", "solid"},
         "orthogonal_projection": {"point", "plane", "image"}, "midpoint": {"point", "segment"},
         "centroid": {"point", "polygon"}, "ask_volume": {"solid"}, "ask_area": {"polygon"}, "ask_length": {"segment"},
         "ask_distance_point_plane": {"point", "plane"}, "ask_distance_lines": {"line1", "line2"},
         "ask_angle_line_plane": {"line", "plane"}, "ask_angle_plane_plane": {"plane1", "plane2"}, "unsupported": {"reason"}}


def chay(out: Path) -> dict:
    from app.ai.fact_extraction import surface_fingerprint as be_mat_b
    from app.ai.function_calling import surface_fingerprint as be_mat_a
    from app.ai.function_route import run_fact_route, run_function_route
    from app.simulation.geometry_functions.planner import PLANNER_VERSION

    (out / "scenes").mkdir(parents=True, exist_ok=True)
    hang: list[dict] = []
    for f in LEGACY:
        for c in json.loads((FX / f).read_text(encoding="utf-8"))["cases"]:
            ra = run_function_route(c["text"], {"calls": c["calls"]})
            rb = run_fact_route(c["text"], {"facts": facts_from_calls(c["calls"])})
            e = c["expect"]
            cl = "correct_refusal" if e["status"] == "REFUSED" else "correct_served"
            hang.append({"set": f.replace(".json", ""), "id": c["id"], "kind": "parity",
                         "A": {"status": ra.status, "code": ra.code, "answers": ra.answers, "class": phan_hang(e, cl, ra)},
                         "B": {"status": rb.status, "code": rb.code, "answers": rb.answers, "class": phan_hang(e, cl, rb),
                               "planner_calls": len(rb.planner.get("calls") or [])},
                         "parity": (ra.status, ra.code) == (rb.status, rb.code)})
    for c in json.loads((FX / HOLDOUT).read_text(encoding="utf-8"))["cases"]:
        ra = run_function_route(c["text"], {"calls": c["a_calls"]})
        rb = run_fact_route(c["text"], {"facts": c["b_facts"]})
        for nhanh, r in (("A", ra), ("B", rb)):
            if r.scene3d:
                (out / "scenes" / f"{c['id']}_{nhanh}.json").write_text(json.dumps(r.scene3d, ensure_ascii=False), encoding="utf-8")
        hang.append({"set": "hybrid_holdout", "id": c["id"], "kind": "holdout", "covers": c["covers"],
                     "A": {"status": ra.status, "code": ra.code, "answers": ra.answers,
                           "class": phan_hang(c["expect_a"], c["class_a"], ra), "expected_class": c["class_a"],
                           "n_ai_items": len(c["a_calls"])},
                     "B": {"status": rb.status, "code": rb.code, "answers": rb.answers,
                           "class": phan_hang(c["expect_b"], c["class_b"], rb), "expected_class": c["class_b"],
                           "n_ai_items": len(c["b_facts"]), "planner_calls": len(rb.planner.get("calls") or []),
                           "goal_checks": rb.planner.get("goal_checks"), "negated_checks": rb.planner.get("negated_checks")}})
    tong = {}
    for kind in ("parity", "holdout"):
        for nhanh in ("A", "B"):
            dem: dict[str, int] = {}
            for h in hang:
                if h["kind"] == kind:
                    dem[h[nhanh]["class"]] = dem.get(h[nhanh]["class"], 0) + 1
            tong[f"{kind}_{nhanh}"] = dem
    tong["parity_status_code_equal"] = f"{sum(h['parity'] for h in hang if h['kind'] == 'parity')}/{sum(h['kind'] == 'parity' for h in hang)}"
    tong["holdout_matches_expected"] = {n: f"{sum(h[n]['class'] == h[n]['expected_class'] for h in hang if h['kind'] == 'holdout')}/"
                                           f"{sum(h['kind'] == 'holdout' for h in hang)}" for n in ("A", "B")}
    kq = {"planner": PLANNER_VERSION, "surface_A": be_mat_a(), "surface_B": be_mat_b(), "model_calls": 0,
          "REAL_MODEL_TOKEN_USAGE": "NOT_MEASURED", "summary": tong, "rows": hang}
    (out / "ab_results.json").write_text(json.dumps(kq, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return tong


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out-dir", required=True)
    tong = chay(Path(p.parse_args().out_dir))
    print(json.dumps(tong, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
