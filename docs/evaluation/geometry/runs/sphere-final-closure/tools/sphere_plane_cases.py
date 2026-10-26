"""Sphere ∩ plane acceptance cases through the PRODUCT path of `build_geometry_samples.py` (spec → interpreter →
simulation_state → scene3d), 0 provider calls, plus an independent oracle on the served circle.

    cd backend && python ../docs/evaluation/geometry/runs/sphere-final-closure/tools/sphere_plane_cases.py <out.json>

Oracle (independent of the product): dist(I, P) = |a·x0 + b·y0 + c·z0 + d| / √(a²+b²+c²);
dist < R ⇒ circle with r² = R² − dist², centre = I − ((a·I + d)/|n|²)·n; dist = R tangent, dist > R no cut ⇒ the product
must NOT serve a circle (no fake section).
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, ".")
sys.path.insert(0, "scripts")
import build_geometry_samples as B  # noqa: E402

R = 5
#: name → plane coefficients (a, b, c, d) of a·x + b·y + c·z + d = 0, sphere centre I = origin, radius 5.
CASES = {
    "above-centre": (0, 0, 1, -3),
    "through-centre": (0, 0, 1, 0),
    "tilted": (1, 2, 2, -6),          # dist = 6/3 = 2 ⇒ r² = 21
    "tangent": (0, 0, 1, -5),
    "no-cut": (0, 0, 1, -6),
}


def program(a: int, b: int, c: int, d: int) -> dict:
    p = B.chuong_trinh_cau_cat_mp(3)
    for st in p["statements"]:
        if st["kind"] == "construct_plane_from_equation":
            st.update(a=a, b=b, c=c, d=d)
    p["description"] = (f"Cho mặt cầu tâm I bán kính 5 và mặt phẳng (P): {a}x + {b}y + {c}z + {d} = 0. "
                        "Tính bán kính và diện tích hình tròn giao tuyến (nếu có).")
    return p


def oracle(a: int, b: int, c: int, d: int) -> dict:
    n2 = F(a * a + b * b + c * c)
    dist2 = F(d * d) / n2
    if dist2 >= R * R:
        return {"kind": "tangent" if dist2 == R * R else "no_cut", "dist_sq": str(dist2)}
    t = F(d) / n2
    return {"kind": "circle", "dist_sq": str(dist2), "radius_sq": str(R * R - dist2),
            "centre": [str(-t * a), str(-t * b), str(-t * c)]}


def main(out: Path) -> int:
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.pipeline_adapter import compile_semantic_program_to_envelope
    from app.simulation.semantic_program.request_contract import InputFact, RequestContract
    from app.simulation.semantic_program.scene3d import build_scene3d
    from app.simulation.semantic_program.simulation_state import build_simulation_state

    rows, envelopes = [], {}
    for name, coef in CASES.items():
        from app.simulation.geometry.exact import GeometryError

        spec = SemanticProgramSpec.model_validate(program(*coef))
        want = oracle(*coef)
        try:
            ket = SemanticProgramInterpreter().execute(spec)
            row = {"case": name, "plane": coef, "oracle": want, "interpreter_status": ket.status}
        except GeometryError as e:      # the pipeline turns this into a typed refusal; no scene is built
            ket, row = None, {"case": name, "plane": coef, "oracle": want, "interpreter_status": "refused",
                              "refusal_code": str(e).split(":")[0]}
        if ket is None or ket.status != "completed":
            row["served_circle"] = False
        else:
            env = compile_semantic_program_to_envelope(spec)
            hop_dong = RequestContract(problem_text=spec.description, obligations=tuple(
                Obligation(kind=k, container=cc, params={"witness": w}) for k, cc, w in B.DE_HOI["cau-cat-mat-phang"]),
                input_facts=tuple(InputFact(fact_id=f, label=n, values=v) for f, n, v in B.DU_KIEN["cau-cat-mat-phang"]))
            canh = build_scene3d(build_simulation_state(spec, ket, hop_dong))
            env.update(scene3d=canh, domain="geometry", source="geometry_sample")
            vong = next((o for o in canh["objects"] if o["type"] == "circle3"), None)
            row["served_circle"] = vong is not None
            if vong is not None:
                row["served"] = {"radius_sq": vong["radius_sq"], "centre": vong["center"]}
                row["matches_oracle"] = (want["kind"] == "circle" and F(vong["radius_sq"]) == F(want["radius_sq"])
                                         and [F(x) for x in vong["center"]] == [F(x) for x in want["centre"]])
            envelopes[name] = env
        row["ok"] = row.get("matches_oracle", False) if want["kind"] == "circle" else not row["served_circle"]
        rows.append(row)
        print(json.dumps({k: row[k] for k in ("case", "ok", "interpreter_status", "served_circle")}, ensure_ascii=False))
    out.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    out.with_name(out.stem + "-envelopes.json").write_text(json.dumps(envelopes, ensure_ascii=False), encoding="utf-8")
    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
