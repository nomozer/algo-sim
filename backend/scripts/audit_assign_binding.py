# -*- coding: utf-8 -*-
"""§1 — BẢNG SỰ THẬT của `assign`: ai ràng buộc tên, ở đâu, và ai thấy. 0 call.

─── CÂU HỎI ───────────────────────────────────────────────────────────────

`CLEAN_BASELINE_V1` mất 4/6 ca vì `assign M = midpoint(B,C)` với `M` chưa khai:
schema ✓, thẩm định tĩnh ✓, **runtime NÉM**. Trước khi sửa phải biết CHÍNH XÁC
mỗi tầng làm gì — sửa theo trí nhớ là cách đẻ ra bản vá thứ hai lệch bản đầu.

Script ĐO, không đọc mã: đo mới phân biệt được *"tài liệu nói gì"* với *"máy
làm gì"*, và cả wave này sinh ra từ chỗ hai thứ đó lệch nhau.

─── BỐN CÂU HỎI CHO MỖI DẠNG ──────────────────────────────────────────────

    schema      · hợp đồng có nhận không
    tĩnh        · `kiem_tinh` có cho qua không
    runtime     · chạy được không, và giá trị nằm ở ĐÂU (memory hay scope)
    provenance  · `_provenance` có thấy producer không

Ô cuối là ô hay bị quên, và nó là ô §5 cấm mất: một điểm dựng ra mà
`producer: null` thì cảnh 3D thôi kể *nó được tạo ra thế nào* — tức mất đúng
đóng góp của đề tài.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))

from app.simulation.semantic_program.interpreter import (  # noqa: E402
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.ir_static_check import kiem_tinh  # noqa: E402
from app.simulation.semantic_program.simulation_state import (  # noqa: E402
    _provenance,
)
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)

_DIEM = [
    {"kind": "declare_point", "target_var": "A", "at": [0, 0, 0],
     "model_assumption": "gốc"},
    {"kind": "declare_point", "target_var": "B", "at": [2, 0, 0],
     "model_assumption": "trục x"},
    {"kind": "declare_point", "target_var": "C", "at": [0, 2, 0],
     "model_assumption": "trục y"},
    {"kind": "declare_point", "target_var": "D", "at": [0, 0, 2],
     "model_assumption": "trục z"},
]

#: (nhãn, câu lệnh ràng buộc `X`, khai báo kèm, câu lệnh DÙNG `X` sau đó)
BO: list[tuple[str, dict, list, list]] = [
    ("assign X = midpoint          (chưa khai)",
     {"kind": "assign", "target_var": "X",
      "expr": {"kind": "midpoint", "a": "B", "b": "C"}}, [], []),
    ("assign X = midpoint          (ĐÃ khai)",
     {"kind": "assign", "target_var": "X",
      "expr": {"kind": "midpoint", "a": "B", "b": "C"}},
     [{"name": "X", "type": "point3"}], []),
    ("construct_point X = midpoint (chưa khai)",
     {"kind": "construct_point", "target_var": "X",
      "expr": {"kind": "midpoint", "a": "B", "b": "C"}}, [], []),
    ("assign X = midpoint, RỒI DÙNG X",
     {"kind": "assign", "target_var": "X",
      "expr": {"kind": "midpoint", "a": "B", "b": "C"}}, [],
     [{"kind": "construct_line", "target_var": "L",
       "through_a": "A", "through_b": "X"}]),
    ("assign X = vector_from_points (chưa khai)",
     {"kind": "assign", "target_var": "X",
      "expr": {"kind": "vector_from_points", "from_point": "A",
               "to_point": "B"}}, [], []),
    ("assign X = intersect_plane_plane (chưa khai)",
     {"kind": "assign", "target_var": "X",
      "expr": {"kind": "intersect_plane_plane", "plane_a": "P1",
               "plane_b": "P2"}}, [], []),
    ("assign X = measure distance  (chưa khai)",
     {"kind": "assign", "target_var": "X",
      "expr": {"kind": "measure", "quantity": "distance", "of": "A",
               "wrt": "B"}}, [], []),
    ("assign X = literal 5         (chưa khai)",
     {"kind": "assign", "target_var": "X",
      "expr": {"kind": "literal", "value": 5}}, [], []),
]

_MAT = [
    {"kind": "construct_plane", "target_var": "P1", "through": ["A", "B", "C"]},
    {"kind": "construct_plane", "target_var": "P2", "through": ["A", "B", "D"]},
]


def _dung(rang_buoc: dict, decls: list, sau: list) -> dict:
    can_mat = "plane_a" in json.dumps(rang_buoc)
    return {
        "spec_version": "1.0", "title": "Bảng sự thật ràng buộc lần đầu",
        "description": "Đo bốn tầng cho một dạng assign.",
        "pedagogical_intent": "Ai ràng buộc tên, ở đâu, và ai thấy.",
        "memory_declarations": [{"name": "P1", "type": "plane3"},
                                {"name": "P2", "type": "plane3"}] + decls
        if can_mat else decls,
        "statements": _DIEM + (_MAT if can_mat else []) + [rang_buoc] + sau,
    }


def mot_hang(nhan: str, rang_buoc: dict, decls: list, sau: list) -> dict:
    ct = _dung(rang_buoc, decls, sau)
    v = validate_semantic_program(ct)
    r = {"dang": nhan, "schema": v.ok}
    if not v.ok:
        return {**r, "tinh": None, "runtime": "—", "o_dau": "—",
                "provenance": "—", "loi": (v.error or "")[:90]}
    t = kiem_tinh(v.spec)
    r["tinh"] = t.ok
    try:
        kq = SemanticProgramInterpreter().execute(v.spec)
        r["runtime"] = "OK"
        # Giá trị nằm ở ĐÂU — đây là ô giải thích cả con bug.
        r["o_dau"] = "memory" if "X" in kq.final_memory else "scope"
    except Exception as e:  # noqa: BLE001
        r["runtime"] = getattr(e, "code", None) or type(e).__name__
        r["o_dau"] = "—"
    prov = _provenance(v.spec).get("X")
    r["provenance"] = prov["producer"] if prov else None
    return r


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", type=Path)
    a = p.parse_args()

    hang = [mot_hang(*x) for x in BO]
    print("━━ §1 BẢNG SỰ THẬT — `assign` ràng buộc tên ở đâu ━━\n")
    print(f"{'dạng':44s} {'schema':>6s} {'tĩnh':>5s} {'runtime':>22s} "
          f"{'ở đâu':>7s}  provenance")
    print("─" * 108)
    for h in hang:
        print(f"{h['dang']:44s} {str(h['schema']):>6s} {str(h['tinh']):>5s} "
              f"{str(h['runtime']):>22s} {str(h['o_dau']):>7s}  "
              f"{h['provenance']}")
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(
            {"khai": "§1 bảng sự thật `assign` — ĐO trên chương trình thật, "
                     "không đọc mã. 0 API call.", "hang": hang},
            ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"\n→ {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
