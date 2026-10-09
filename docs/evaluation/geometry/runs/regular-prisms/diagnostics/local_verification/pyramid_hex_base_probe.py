"""LOCAL: the branch now READS "hình chóp S.ABCDEF có đáy là lục giác đều" (base_regular_hexagon on a pyramid — a
side effect of the prism reader). Route outcome on each tree for a model-style lattice program (C1 path) and for
rational coordinates stated in the text (C0 path: consistent / base side contradicts / base not regular).
Run from backend/ on each tree; 0 model calls."""
import json, os, sys
sys.path.insert(0, os.getcwd())
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.route import verify_and_compile

DAY = list("ABCDEF")
LATTICE = [(2, 1, 0), (1, 2, 0), (0, 2, 0), (0, 1, 0), (1, 0, 0), (2, 0, 0)]      # affine 60° chart
PLANE = [(1, -1, 0), (1, 0, -1), (0, 1, -1), (-1, 1, 0), (-1, 0, 1), (0, -1, 1)]  # Euclidean regular, side √2
BENT = [(1, -1, 0), (1, 0, -1), (0, 1, -1), (-1, 1, 0), (-1, 0, 1), (0, -2, 2)]    # F moved: not regular


def run(text, base, apex):
    payload = {"input_facts": [{"id": "f_khoi", "kind": "str", "label": "Khối chóp", "value": ["S.ABCDEF"]}],
               "obligations": [{"kind": "volume", "container": "khoi", "witness": "V"}],
               "solid_topology": {"solid_kind": "pyramid", "apex": "S", "base_cycle": DAY}}
    c = build_request_contract(payload, problem_text=text, domain="hinh_hoc")
    mem = [{"name": p, "type": "point3", "provenance": "LAYOUT_DERIVED"} for p in ("S", *DAY)]
    mem += [{"name": "khoi", "type": "solid"}, {"name": "V", "type": "float"}]
    st = [{"kind": "declare_point", "target_var": p, "at": [str(x) for x in xyz]} for p, xyz in zip(DAY, base)]
    st += [{"kind": "declare_point", "target_var": "S", "at": [str(x) for x in apex]},
           {"kind": "construct_solid", "target_var": "khoi", "vertices": ["S", *DAY],
            "faces": [DAY] + [["S", DAY[i], DAY[(i + 1) % 6]] for i in range(6)], "label": "S.ABCDEF"},
           {"kind": "assign", "target_var": "V", "expr": {"kind": "measure", "quantity": "volume", "of": "khoi"}}]
    sp = SemanticProgramSpec.model_validate({"spec_version": "1.0", "title": "Chóp S.ABCDEF", "memory_declarations": mem,
                                             "statements": st})
    o = verify_and_compile(c, sp)
    v = str(SemanticProgramInterpreter().execute(sp).final_memory["V"]) if o.servable else None
    return {"servable": o.servable, "stage": o.stage_reached, "reason": o.reason_code,
            "certificate": o.assumption_certificate, "value": v}


def coords(base, apex):
    return ", ".join(f"{p}({';'.join(str(x) for x in xyz)})" for p, xyz in zip(["S", *DAY], [apex, *base]))


CASES = {
    # C1: lattice chart, apex over A (SA ⊥ base in the chart); text V = (1/3)(3√3/2·4)(3) = 6√3
    "C1_lattice_SA_perp": ("Cho hình chóp S.ABCDEF có đáy là lục giác đều cạnh 2, SA vuông góc với đáy, SA = 3. "
                           "Tính thể tích khối chóp S.ABCDEF.", LATTICE, (2, 1, 3)),
    # C0: S = A + (1,1,1) ⊥ plane x+y+z=0; base area (3√3/2)·2 = 3√3, height √3 ⇒ V = 3
    "C0_consistent": ("Trong không gian Oxyz, cho hình chóp S.ABCDEF với {c}, đáy là lục giác đều. "
                      "Tính thể tích khối chóp S.ABCDEF.", PLANE, (2, 0, 1)),
    "C0_side_contradicts": ("Trong không gian Oxyz, cho hình chóp S.ABCDEF với {c}, đáy là lục giác đều cạnh 2. "
                            "Tính thể tích khối chóp S.ABCDEF.", PLANE, (2, 0, 1)),
    "C0_base_not_regular": ("Trong không gian Oxyz, cho hình chóp S.ABCDEF với {c}, đáy là lục giác đều. "
                            "Tính thể tích khối chóp S.ABCDEF.", BENT, (2, 0, 1)),
}
for k, (text, base, apex) in CASES.items():
    print(json.dumps({"case": k, **run(text.replace("{c}", coords(base, apex)), base, apex)}, ensure_ascii=False))
