"""Author development cases from exact horizontal-section geometry, without importing product or Wave2."""
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
SOURCE_CODES = ["SOURCE_OBJECT_MISMATCH", "SOURCE_PREMISE_UNREAD", "UNGROUNDED_VALUE",
                "UNKNOWN_ENTITY", "UNGROUNDED_LABEL", "SOURCE_ROLE_MISMATCH",
                "SOURCE_REQUEST_COVERAGE_MISMATCH", "QUESTION_CONTEXT_UNSUPPORTED",
                "UNSUPPORTED_CAPABILITY", "SOURCE_TEXT_MISMATCH", "QUOTE_NOT_IN_SOURCE",
                "UNKNOWN_DERIVED_REFERENCE", "FACT_CONFLICT", "INCONSISTENT_PREMISES",
                "SOURCE_CONTRADICTION", "AMBIGUOUS_ENTITY", "BRIDGE_UNSUPPORTED_REFERENCE"]
families = ["triangular_pyramid", "quadrilateral_pyramid", "right_triangular_prism",
            "oblique_triangular_prism", "cuboid", "cube"]


def make(family, variant):
    # New dimensions/ratios and relabelings are authored before any product execution.
    tri = "triangular" in family
    pyramid = "pyramid" in family
    oblique = family == "oblique_triangular_prism"
    square = family == "cube"
    labels = list("EFG" if tri else "EFGH") if variant == 2 else list("ABC" if tri else "ABCD")
    a, b, c = labels[:3]
    apex = "T" if variant == 2 else "S"
    m = "J" if variant == 2 else "M"
    u, v, h = (11 + variant, 17 + variant, 9 + variant)
    if square:
        v = h = u
    t = [F(3, 8), F(4, 9), F(5, 11), F(2, 5)][variant]
    name = "".join(labels)
    top = [x + "'" for x in labels]
    solid = apex + "." + name if pyramid else name + "." + "".join(top)
    noun = ("hình chóp" if pyramid else "lăng trụ" if oblique else
            "lăng trụ đứng" if tri else "hình lập phương" if square else "hình hộp chữ nhật")
    sq = f"{noun} {solid}"
    sentences = [f"Cho {sq}."]
    premises = []

    def fact(kind, args, quote):
        premises.append(dict(kind=kind, args=args, quote=quote))

    def say(s):
        sentences.append(s + ".")
        return s

    if not pyramid and not oblique:
        fact("right_prism", dict(base=labels, top=top), sq)
    if square:
        # The square and height are independently source-stated, in addition to the cube identity.
        q = say(f"Đáy {name} là hình vuông cạnh {u}")
        fact("base_is_square", dict(vertices=labels, side=str(u)), q)
    elif tri:
        q = say(f"Tam giác {name} vuông tại {a}")
        fact("right_angle", dict(vertices=labels, right_at=a), q)
    else:
        q = say(f"Đáy {name} là hình chữ nhật")
        fact("base_is_rectangle", dict(vertices=labels), q)
    def length(x, y, value):
        q = say(f"{x}{y} = {value}")
        fact("segment_length", dict(segment=[x, y], value=str(value)), q)

    if not square:
        length(a, b, u)
        length(a, c if tri else labels[-1], v)
    if pyramid:
        q = say(f"{apex}{a} vuông góc với mặt phẳng ({''.join(labels[:3])})")
        fact("perpendicular_line_plane", dict(line=[apex, a], plane=labels[:3]), q)
        length(apex, a, h)
        edge = [apex, a]
    else:
        edge = [a, top[0]]
        if oblique:
            target_noun = "điểm" if variant == 0 else "đỉnh"
            verb = "là" if variant % 2 == 0 else "trùng với"
            q = say(f"Hình chiếu vuông góc của {top[0]} trên mặt phẳng ({name}) {verb} {target_noun} {b}")
            fact("orthogonal_projection", dict(point=top[0], image=b, plane=labels), q)
            length(top[0], b, h)
        else:
            length(a, top[0], h)
    x, y = edge
    eq = f"{x}{m} = {t} {x}{y}"
    if variant == 0:
        q = say(f"Điểm {m} thuộc cạnh {x}{y} sao cho {eq}")
    elif variant == 1:
        q = say(f"Trên cạnh {x}{y} lấy điểm {m} sao cho {eq}")
    elif variant == 2:
        q = say(f"Trên đoạn thẳng {y}{x} lấy điểm {m} sao cho {m}{x} = {t} {y}{x}")
    else:
        # XP = k*PY, exercising the same exact solver rather than literal coefficient comparison.
        q = say(f"Trên cạnh {x}{y} lấy điểm {m} sao cho {x}{m} = {t / (1-t)} {m}{y}")
    ratio_args = dict(point=m, segment=edge[::-1] if variant == 2 else edge,
                      ratio=str(1-t if variant == 2 else t))
    fact("divide_segment", ratio_args, q)
    two_lines = variant in (1, 3)
    if two_lines:
        line2 = [a, c if tri else labels[-1]]
        plane_q = say(f"Mặt phẳng (α) đi qua {m}, song song với hai đường thẳng {a}{b} và {''.join(line2)}")
    else:
        plane_q = say(f"Mặt phẳng (α) đi qua {m} và song song với mặt phẳng ({''.join(labels[:3])})")
    section = dict(section_id="sec", plane_name="α", target_solid_id="s1",
                   plane_kind="through_point_parallel_two_lines" if two_lines else "through_point_parallel_plane",
                   quote=plane_q, through_point=m)
    if two_lines:
        section.update(parallel_line_a=[a, b], parallel_line_b=line2)
    else:
        section["parallel_plane"] = labels[:3]
    boundary = [dict(edge=[apex, z] if pyramid else [z, z+"'"], t=str(t)) for z in labels]
    area = F(u*v, 2) if tri else F(u*v)
    if pyramid:
        area *= t*t
    ask = say(f"Tính diện tích thiết diện của {sq} cắt bởi mặt phẳng (α)")
    payload = dict(schema_version="typed-fact-next/2", problem_text=" ".join(sentences), length_unit="1",
                   solids=[dict(solid_id="s1", solid_type="pyramid" if pyramid else "prism", notation=solid, quote=sq)],
                   premises=premises, derived_sections=[section], relations=[],
                   simulation_goals=[dict(goal_id="g1", kind="construct_object", quote=sq, target_solid_id="s1",
                                          style_role="primary")],
                   math_goals=[dict(goal_id="area", kind="measurement", goal_type="area", quote=ask,
                                    target=dict(section_id="sec"))])
    if variant == 2:
        payload["premises"].reverse()
    return dict(id=f"DEV-{families.index(family)+1}-{variant+1}", family=family,
                plane_relation="parallel_two_lines" if two_lines else "parallel_plane",
                variant=variant, expected_status="SERVED", payload=payload,
                oracle=dict(method="horizontal homothety" if pyramid else "horizontal translation",
                            area_squared=str(area*area), vertex_count=len(labels),
                            boundary=boundary, solid=solid, section_id="sec", area_goal_id="area",
                            expected_certificate_category="ENGINE_DERIVED_SECTION"))


def negative(base, label, mutate):
    c = deepcopy(base)
    c.update(id="NEG-"+label, expected_status="REFUSED", negative_class=label,
             expected_codes=SOURCE_CODES)
    c.pop("oracle")
    mutate(c["payload"])
    return c


def ratio_fact(p):
    return next(f for f in p["premises"] if f["kind"] == "divide_segment")


def replace_source(p, old, new):
    # Keep all quote spans in source so the intended relationship, rather than a missing quotation, is tested.
    p["problem_text"] = p["problem_text"].replace(old, new)
    for f in p["premises"]:
        f["quote"] = f["quote"].replace(old, new)


def main():
    cases = [make(fam, v) for fam in families for v in range(4)]
    neg = []
    for i, base in enumerate(cases[:12]):
        neg.append(negative(base, f"{i+1:02}-endpoint-order",
                            lambda p: ratio_fact(p)["args"]["segment"].reverse()))
        neg.append(negative(base, f"{i+1:02}-wrong-ratio",
                            lambda p: ratio_fact(p)["args"].update(ratio="1/7")))
    base = cases[1]
    neg.append(negative(base, "changed-source-edge",
                        lambda p: replace_source(p, "cạnh SA", "cạnh SB")))
    neg.append(negative(base, "changed-solid-notation",
                        lambda p: p["problem_text"].replace("S.ABC", "T.ABC")))
    # Fix string mutation explicitly; this deliberately leaves the gold identity stale.
    neg[-1]["payload"]["problem_text"] = neg[-1]["payload"]["problem_text"].replace("S.ABC", "T.ABC")
    neg.append(negative(base, "kind-symbol-contradiction",
                        lambda p: replace_source(p, "hình chóp", "hình lập phương")))
    neg.append(negative(base, "unread-premise",
                        lambda p: p.update(problem_text=p["problem_text"]+" Biết SB = SC.")))
    neg.append(negative(base, "ratio-extra-tail",
                        lambda p: replace_source(p, ratio_fact(p)["quote"],
                                                 ratio_fact(p)["quote"]+", với SB = SC")))
    ob = cases[13]
    def projection(p):
        return next(f for f in p["premises"] if f["kind"] == "orthogonal_projection")
    neg.append(negative(ob, "oblique-called-right",
                        lambda p: replace_source(p, "lăng trụ", "lăng trụ đứng")))
    neg.append(negative(ob, "projection-unknown-label",
                        lambda p: projection(p)["args"].update(image="Z")))
    neg.append(negative(ob, "vertex-noun-wrong-entity",
                        lambda p: replace_source(p, "đỉnh B", "đỉnh C")))
    neg.append(negative(ob, "projection-primed-target-wrong",
                        lambda p: replace_source(p, "đỉnh B", "đỉnh B'")))
    neg.append(negative(ob, "unproven-two-line-premise",
                        lambda p: p.update(problem_text=p["problem_text"]+" Biết AC vuông góc với AB.")))
    neg.append(negative(base, "two-solids-wrong-section-owner",
                        lambda p: p.update(problem_text="Cho hình chóp T.DEF. "+p["problem_text"].replace(
                            "Tính diện tích thiết diện của hình chóp S.ABC",
                            "Tính diện tích thiết diện của hình chóp T.DEF"))))
    neg.append(negative(ob, "vertex-from-other-solid",
                        lambda p: p.update(problem_text="Cho hình chóp T.XYZ. "+p["problem_text"].replace(
                            "đỉnh B", "đỉnh X"))))
    # Names in an inverted definition must belong to that same clause, not a neighboring one.
    neg.append(negative(base, "point-from-other-definition",
                        lambda p: replace_source(p, "lấy điểm M sao cho SM", "lấy điểm N sao cho SM")))
    data = dict(schema="source-gate-language-development/1",
                classification="AUTHORED_DEVELOPMENT_NOT_INDEPENDENT_HOLDOUT",
                independent_of="Wave2 cases and oracle (not imported by this builder)",
                oracle_policy="Fraction-only formulas from horizontal cross-section mathematics; no product imports",
                cases=cases+neg)
    out = RUN/"inputs/development.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    with out.open("xb") as f:
        f.write(raw)
    print(json.dumps(dict(positive=len(cases),negative=len(neg),sha256=hashlib.sha256(raw).hexdigest())))


if __name__ == "__main__":
    main()
