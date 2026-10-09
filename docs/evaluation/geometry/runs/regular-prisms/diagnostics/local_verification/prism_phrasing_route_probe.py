"""LOCAL: route outcome for phrasings outside the 25 labels, on the corpus lattice program of T1 / X1 (0 model calls).
Run from backend/ on each tree: python prism_phrasing_route_probe.py <run dir>"""
import json, os, sys
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(sys.argv[1], "diagnostics"))
import cases
from app.ai.pipeline import _dung_scene3d
from app.simulation.semantic_program.route import verify_and_compile

Q3, Q6 = "Tính thể tích khối lăng trụ ABC.A'B'C'.", "Tính thể tích khối lăng trụ ABCDEF.A'B'C'D'E'F'."
CAU = {
    "no_hinh_tri": ("T1_side_height", f"Cho lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng 2, chiều cao bằng 3. {Q3}"),
    "right_tri_regular_noun": ("T1_side_height",
                               f"Cho hình lăng trụ đứng tam giác đều ABC.A'B'C' có cạnh đáy bằng 2, chiều cao bằng 3. {Q3}"),
    "oblique_tri_regular_noun": ("T1_side_height",
                                 f"Cho hình lăng trụ xiên tam giác đều ABC.A'B'C' có cạnh đáy bằng 2, cạnh bên bằng 3. {Q3}"),
    "oblique_hex_regular_noun": ("X1_side_height", "Cho hình lăng trụ xiên lục giác đều ABCDEF.A'B'C'D'E'F' có cạnh đáy bằng "
                                 f"2, cạnh bên bằng 3. {Q6}"),
    "negation_after": ("T1_side_height", "Cho hình lăng trụ ABC.A'B'C' có cạnh đáy bằng 2, chiều cao bằng 3, lăng trụ này "
                       f"không phải lăng trụ tam giác đều. {Q3}"),
}
for k, (row, text) in CAU.items():
    cases.LABELS[k] = {**cases.LABELS[row], "text": text}
    c, sp = cases.hop_dong_va_chuong_trinh(k)
    o = verify_and_compile(c, sp)
    v = next(x.get("value") for x in _dung_scene3d(sp, c)["objects"] if x["id"] == "V") if o.servable else None
    print(json.dumps({"case": k, "servable": o.servable, "stage": o.stage_reached, "reason": o.reason_code,
                      "certificate": o.assumption_certificate, "value": v}, ensure_ascii=False))
