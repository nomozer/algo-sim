# -*- coding: utf-8 -*-
"""§17 — ý định của các chương trình hỏng nay diễn đạt được? **0 API call.**

─── ĐIỀU SCRIPT NÀY KHÔNG LÀM ─────────────────────────────────────────────

Không sửa artifact. Không tính 9 quan sát hỏng của `SYNTHESIS_STABILITY_K3`
thành thành công. Chúng là **bằng chứng đã dẫn tới việc thêm primitive**, và
biến chúng thành điểm là xoá mất chính bằng chứng ấy.

─── NÓ LÀM GÌ ─────────────────────────────────────────────────────────────

Với mỗi câu lệnh hỏng có hình dạng

    construct_point X = arith(+, var(P), vector_from_points(A, B))

dựng một **fixture chuẩn tắc tương đương** bằng `translate`, rồi chạy qua đúng
chuỗi cổng sản phẩm. Câu trả lời là *"cùng một ý định dựng hình nay biểu diễn
được"* — KHÔNG phải *"mô hình đã đúng"*.

Phép dịch là cơ học và kiểm được: `arith(+, var(P), V)` → `translate(P, v)`
với `v` là một câu `assign` cho chính biểu thức `V`. Không đoán gì.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
GOC = BE.parent

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

K3 = GOC / "docs" / "evaluation" / "geometry" / "stability-k3" / "stability.json"
SEED = GOC / "docs" / "evaluation" / "geometry" / "stability-seed" / "seed.json"


def _cau_hong(prog: dict) -> list[dict]:
    """Câu lệnh `construct_point … = arith(+, var(P), <vectơ>)`."""
    ra = []
    for st in prog.get("statements") or []:
        if not isinstance(st, dict) or st.get("kind") != "construct_point":
            continue
        e = st.get("expr") or {}
        if e.get("kind") != "arith" or e.get("op") != "+":
            continue
        trai, phai = e.get("left") or {}, e.get("right") or {}
        if trai.get("kind") == "var":
            ra.append({"target": st.get("target_var"),
                       "point": trai.get("name"), "vector_expr": phai})
    return ra


def _dich(prog: dict, hong: list[dict]) -> dict:
    """Dịch CƠ HỌC sang `translate`. Không đoán, không sửa gì khác.

    `arith(+, var(P), V)` → hai câu: `assign __v_i = V` rồi
    `construct_point X = translate(P, __v_i)`. Tên vectơ mang tiền tố `__v_`
    để không đụng bất kỳ tên nào của chương trình gốc.
    """
    doi = {h["target"]: h for h in hong}
    moi = []
    for i, st in enumerate(prog.get("statements") or []):
        h = doi.get(st.get("target_var")) if isinstance(st, dict) else None
        if not h or st.get("kind") != "construct_point":
            moi.append(st)
            continue
        ten_v = f"__v_{i}"
        moi.append({"kind": "assign", "target_var": ten_v,
                    "expr": h["vector_expr"]})
        moi.append({"kind": "construct_point", "target_var": h["target"],
                    "expr": {"kind": "translate", "point": h["point"],
                             "vector": ten_v}})
    return {**prog, "statements": moi}


def _chay(spec: dict) -> dict:
    v = validate_semantic_program(spec)
    if not v.ok:
        return {"schema": False, "loi": (v.error or "")[:200]}
    t = kiem_tinh(v.spec)
    if not t.ok:
        return {"schema": True, "tinh": False, "loi": t.phan_hoi()[:200]}
    try:
        kq = SemanticProgramInterpreter().execute(v.spec)
    except Exception as e:  # noqa: BLE001
        return {"schema": True, "tinh": True, "runtime": False,
                "loi": f"{type(e).__name__}: {e}"[:200]}
    prov = _provenance(v.spec)
    return {"schema": True, "tinh": True, "runtime": True,
            "trace_steps": kq.total_steps,
            "producer_translate": sorted(
                k for k, p in prov.items()
                if str(p.get("producer", "")).endswith("translate"))}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", type=Path)
    a = p.parse_args()

    tho: list[tuple[str, str, str]] = []
    for f, khoa in ((K3, "cases"), (SEED, "cases")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for c in d[khoa]:
            for r in (c.get("repeats") or [{"repeat": "R1", **c.get("repeat_1", {})}]):
                raw = r.get("raw_output")
                if raw:
                    tho.append((c["case_id"], r.get("repeat", "R1"), raw))

    ket, tong_cau = [], 0
    for cid, nhan, raw in tho:
        try:
            prog = json.loads(raw)
        except Exception:  # noqa: BLE001
            continue
        hong = _cau_hong(prog)
        if not hong:
            continue
        tong_cau += len(hong)
        cu = _chay(prog)
        moi = _chay(_dich(prog, hong))
        ket.append({"case_id": cid, "repeat": nhan,
                    "so_cau_arith": len(hong),
                    "dich": [{"target": h["target"], "point": h["point"],
                              "vector_kind": (h["vector_expr"] or {}).get("kind")}
                             for h in hong],
                    "truoc": cu, "sau": moi,
                    "giai_thich_duoc": bool(moi.get("runtime"))})

    n = sum(1 for x in ket if x["giai_thich_duoc"])
    print("━━ §17 REPLAY Ý ĐỊNH — `arith(point, vector)` → `translate` ━━\n")
    print(f"{'ca':34s} {'lượt':5s} {'câu':>3s}  trước → sau")
    print("─" * 88)
    for x in ket:
        t_ = "schema✗" if not x["truoc"]["schema"] else "chạy"
        s_ = ("chạy ✓" if x["sau"].get("runtime")
              else f"✗ {x['sau'].get('loi', '')[:40]}")
        print(f"{x['case_id'][:34]:34s} {x['repeat']:5s} "
              f"{x['so_cau_arith']:3d}  {t_} → {s_}")
    print(f"\nHISTORICAL_FAILURES_EXPLAINED_BY_TRANSLATION: {n}/{len(ket)} "
          f"chương trình · {tong_cau} câu lệnh")
    print("\n⚠️ KHÔNG phải thành công hồi tố của mô hình. Điểm lịch sử của "
          "CLEAN_BASELINE_V2, hạt giống và k=3 giữ nguyên.")

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps({
            "khai": "§17 — dịch CƠ HỌC `arith(+, var(P), V)` → `translate(P, v)` "
                    "rồi chạy qua chuỗi cổng. Trả lời 'cùng ý định nay biểu "
                    "diễn được', KHÔNG phải 'mô hình đã đúng'. 0 API call.",
            "historical_scores_changed": False,
            "explained": f"{n}/{len(ket)}", "tong_cau_lenh": tong_cau,
            "cases": ket}, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")
        print(f"→ {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
