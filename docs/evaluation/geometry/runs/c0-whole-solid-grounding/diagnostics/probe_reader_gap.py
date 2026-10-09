"""Run from backend/: whole-solid claims the reader does NOT emit, so C0 has nothing to check (left OPEN:
ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ). Coordinates of RSP_C_apex_over_vertex (apex over vertex A). 0 model calls."""
import json, os, sys
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c0_whole_solid_cases as M
from app.simulation.semantic_program.assumption_gate import _doc_de
from app.simulation.semantic_program.route import verify_and_compile
for t in ["Cho hình chóp tứ giác đều có đỉnh S và đáy ABCD với {coords}. Tính thể tích khối chóp.",
          "Cho hình chóp tứ giác đều với {coords}. Tính thể tích khối chóp.",
          "Cho hình chóp đều S.ABCD với {coords}. Tính thể tích khối chóp S.ABCD."]:
    M.LABELS["_gap"] = dict(M.LABELS["RSP_C_apex_over_vertex"], text=t)
    de, c, sp = M.hop_dong_va_chuong_trinh("_gap")
    o = verify_and_compile(c, sp)
    print(json.dumps({"text": t, "read": sorted({r.kind for r in _doc_de(de)[1]}), "servable": o.servable,
                      "stage": o.stage_reached}, ensure_ascii=False))
