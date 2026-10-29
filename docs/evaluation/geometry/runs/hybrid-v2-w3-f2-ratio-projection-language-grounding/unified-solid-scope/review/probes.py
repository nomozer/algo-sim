"""Independent adversarial solid-scope probes (development security probes, not a holdout). 0 provider calls.
Usage (from a backend/ dir): PYTHONPATH=. python -B probes.py <scratch_dir> [filter] -> JSON lines on stdout."""
import sys, json, copy
sys.path.insert(0, sys.argv[1])
from harness import RUNS, run3


def load(rel):
    return json.loads((RUNS / rel).read_text(encoding="utf-8"))


C1 = load("hybrid-v2-w3-f2-ratio-projection-language-grounding/inputs/recovery-supplementary.json")["control"]
SIM = load("simulation-coverage-visual-validation/corpus-dev.json")["cases"]
A3C = load("typedfact-next-adapter3-simulation/corpus-dev.json")["cases"]
SEC1 = SIM[0]["payload"]          # S.ABCD + section + derived s_top + ratio (A3 SERVED)
CONE = SIM[6]["payload"]          # cone + derived cone_upper + ratio/residual (A3 SERVED, curved)
CYL = SIM[5]["payload"]
SPH = SIM[7]["payload"]
BIND = A3C[1]["payload"]          # pyr1/pyr2 non-identity bindings (A3 legacy SERVED)

PROBES = []


def probe(name, base, kind="NEG"):
    def deco(fn):
        PROBES.append((name, base, fn, kind))
        return fn
    return deco


def rel(**kw):
    return {"relation_id": kw.pop("relation_id", "rx"), "quote": kw.pop("quote", "Cho hình chóp S.ABCD."), **kw}


Q1 = "Tính thể tích hình chóp S.ABCD."

# ---------- C1: two pyramids sharing ABCD (served on all three routes) ----------
@probe("C1.control", C1, "CTL")
def _(p): pass
@probe("C1.rel_perp_scope_s2_refs_s1_qualified", C1)
def _(p): p["relations"].append(rel(kind="perpendicular", solid_id="s2", entity_a=["s1::S", "s1::A"], entity_b=["s1::A", "s1::B", "s1::C", "s1::D"], quote="SA vuông góc với (ABCD)."))
@probe("C1.rel_perp_scope_s2_refs_unqualified_s1_only", C1)
def _(p): p["relations"].append(rel(kind="perpendicular", solid_id="s2", entity_a=["S", "A"], entity_b=["A", "B", "C", "D"], quote="SA vuông góc với (ABCD)."))
@probe("C1.rel_perp_solid_a_s2_refs_s1", C1)
def _(p): p["relations"].append(rel(kind="perpendicular", solid_a="s2", entity_a=["s1::S", "s1::A"], entity_b=["A", "B", "C", "D"], quote="SA vuông góc với (ABCD)."))
@probe("C1.rel_perp_foreign_scope", C1)
def _(p): p["relations"].append(rel(kind="perpendicular", solid_id="zz", entity_a=["S", "A"], entity_b=["A", "B", "C", "D"], quote="SA vuông góc với (ABCD)."))
@probe("C1.rel_perp_foreign_ns", C1)
def _(p): p["relations"].append(rel(kind="perpendicular", entity_a=["zz::S", "A"], entity_b=["A", "B", "C", "D"], quote="SA vuông góc với (ABCD)."))
@probe("C1.rel_perp_valid_control", C1, "CTL")
def _(p): p["relations"].append(rel(kind="perpendicular", solid_id="s1", entity_a=["S", "A"], entity_b=["A", "B", "C", "D"], quote="SA vuông góc với (ABCD)."))
@probe("C1.rel_shared_vertices_solid_a_contradicts_pairs", C1)
def _(p): p["relations"].append(rel(kind="shared_vertices", solid_a="s2", solid_b="s2", pairs=[["s1::A", "s1::A"]]))
@probe("C1.rel_mixed_valid_and_foreign_frame", C1)
def _(p): p["relations"] += [rel(relation_id="ok", kind="coordinate_frame", solid_id="s1", frame_id="root", anchor_refs=["A", "B", "C"]),
                             rel(relation_id="bad", kind="coordinate_frame", solid_id="s2", frame_id="root", anchor_refs=["S", "A", "B"])]
@probe("C1.rel_valid_frames_both", C1, "CTL")
def _(p): p["relations"] += [rel(relation_id="f1", kind="coordinate_frame", solid_id="s1", frame_id="root", anchor_refs=["A", "B", "C"]),
                             rel(relation_id="f2", kind="coordinate_frame", solid_id="s2", frame_id="root", anchor_refs=["T", "A", "B"])]
@probe("C1.rel_valid_shared_face", C1, "CTL")
def _(p): p["relations"].append(rel(kind="shared_faces", solid_a="s1", solid_b="s2", face_a=["A", "B", "C", "D"], face_b=["A", "B", "C", "D"]))
@probe("C1.rel_shared_face_qualified_swap", C1)
def _(p): p["relations"].append(rel(kind="shared_faces", solid_a="s1", solid_b="s2", face_a=["s2::A", "s2::B", "s2::C"], face_b=["s1::A", "s1::B", "s1::C"]))
@probe("C1.highlight_scope_s2_ref_s1_qualified", C1)
def _(p): p["simulation_goals"].append({"goal_id": "h", "kind": "highlight_geometry", "target_solid_id": "s2", "target_refs": ["s1::S"], "quote": "Cho hình chóp S.ABCD."})
@probe("C1.highlight_scope_s2_ref_S_unqualified", C1)
def _(p): p["simulation_goals"].append({"goal_id": "h", "kind": "highlight_geometry", "target_solid_id": "s2", "target_refs": ["S"], "quote": "Cho hình chóp S.ABCD."})
@probe("C1.highlight_foreign_ns", C1)
def _(p): p["simulation_goals"].append({"goal_id": "h", "kind": "highlight_geometry", "target_refs": ["zz::S"], "quote": "Cho hình chóp S.ABCD."})
@probe("C1.highlight_valid_control", C1, "CTL")
def _(p): p["simulation_goals"].append({"goal_id": "h", "kind": "highlight_geometry", "target_solid_id": "s2", "target_refs": ["s2::T", "A"], "quote": "Cho hình chóp S.ABCD."})
@probe("C1.construct_object_parent_foreign", C1)
def _(p): p["simulation_goals"][0]["parent_solid_id"] = "zz"
@probe("C1.construct_object_parent_other", C1)
def _(p): p["simulation_goals"][0]["parent_solid_id"] = "s2"
@probe("C1.construct_object_apex_ref_foreign_ns", C1)
def _(p): p["simulation_goals"][0]["apex_ref"] = "zz::S"
@probe("C1.vol_goal_scope_s1_target_notation_T", C1)
def _(p): p["math_goals"][0]["target"] = {"solid": "T.ABCD"}
@probe("C1.vol_goal_target_notation_alias_noscope", C1, "CTL")
def _(p): p["math_goals"][0].pop("solid_id"); p["math_goals"][0]["target"] = {"solid": "S.ABCD"}
@probe("C1.vol_goal_target_solid_id_nested_s2", C1)
def _(p): p["math_goals"][0]["target"] = {"solid": "s1", "solid_id": "s2"}
@probe("C1.vol_goal_absent_scope_target_id", C1, "CTL")
def _(p): p["math_goals"][0].pop("solid_id")
@probe("C1.vol_goal_scope_only_extra_key", C1, "CTL")
def _(p): p["math_goals"][0]["target"] = {"solid": "s1", "note": "x"}
@probe("C1.premise_args_solid_alias_T_on_s2", C1, "CTL")
def _(p): p["premises"].append({"kind": "height", "args": {"value": "4", "solid": "T.ABCD"}, "quote": "TA = 4.", "solid_id": "s2"})
@probe("C1.premise_height_scope_s1_args_solid_T", C1)
def _(p): p["premises"].append({"kind": "height", "args": {"value": "4", "solid": "T.ABCD"}, "quote": "TA = 4.", "solid_id": "s1"})
@probe("C1.premise_scope_s1_operand_s2_qualified", C1)
def _(p): p["premises"][4]["solid_id"] = "s1"; p["premises"][4]["args"]["segment"] = ["s2::T", "s2::A"]
@probe("C1.premise_scope_s1_operand_T_unqualified", C1)
def _(p): p["premises"][4]["solid_id"] = "s1"
@probe("C1.premise_unscoped_cross_namespace", C1)
def _(p): p["premises"][4].pop("solid_id"); p["premises"][4]["args"]["segment"] = ["s1::A", "s2::T"]
@probe("C1.premise_unscoped_cross_solid_ST", C1)
def _(p): p["premises"][4].pop("solid_id"); p["premises"][4]["args"]["segment"] = ["s1::S", "s2::T"]
@probe("C1.premises_all_unscoped_shared_labels", C1, "CTL")
def _(p): [pr.pop("solid_id", None) for pr in p["premises"]]
@probe("C1.premise_unknown_kind_nested_foreign", C1)
def _(p): p["premises"].append({"kind": "weird_kind", "args": {"x": {"y": ["zz::A"]}}, "quote": "SA = 3."})
@probe("C1.premise_unknown_kind_args_solid_int", C1)
def _(p): p["premises"].append({"kind": "weird_kind", "args": {"solid": 7}, "quote": "SA = 3."})
@probe("C1.premise_unknown_kind_args_solid_dict", C1)
def _(p): p["premises"].append({"kind": "weird_kind", "args": {"solid": {"a": 1}}, "quote": "SA = 3."})
@probe("C1.ratio_with_solid_id", C1)
def _(p): p["math_goals"].append({"goal_id": "r", "kind": "volume_ratio", "numerator_solid_id": "s2", "denominator_solid_id": "s1", "solid_id": "s1", "quote": Q1})
@probe("C1.ratio_two_primary_noscope", C1, "INFO")
def _(p): p["math_goals"].append({"goal_id": "r", "kind": "volume_ratio", "numerator_solid_id": "s2", "denominator_solid_id": "s1", "quote": Q1})
@probe("C1.ratio_target_solid_foreign", C1)
def _(p): p["math_goals"].append({"goal_id": "r", "kind": "volume_ratio", "numerator_solid_id": "s2", "denominator_solid_id": "s1", "target": {"solid": "zz"}, "quote": Q1})
@probe("C1.residual_target_foreign_refs", C1)
def _(p): p["math_goals"].append({"goal_id": "r", "kind": "residual_volume", "parent_solid_id": "s1", "cut_solid_id": "s2", "target": {"solid_id": "zz", "segment": ["zz::A", "zz::B"]}, "quote": Q1})
@probe("C1.measure_nonstring_segment", C1)
def _(p): p["math_goals"].append({"goal_id": "d", "kind": "measurement", "goal_type": "distance", "solid_id": "s1", "target": {"segment": [1, "A"]}, "quote": Q1})
@probe("C1.measure_nonstring_point_dict", C1)
def _(p): p["math_goals"].append({"goal_id": "d", "kind": "measurement", "goal_type": "distance", "solid_id": "s1", "target": {"point": {"a": 1}, "plane": ["A", "B", "C"]}, "quote": Q1})
@probe("C1.measure_section_id_list", C1)
def _(p): p["math_goals"].append({"goal_id": "d", "kind": "measurement", "goal_type": "area", "target": {"section_id": ["x"]}, "quote": Q1})
@probe("C1.angle_plane1_plane2_scope_s2_ops_s1_only", C1)
def _(p): p["math_goals"].append({"goal_id": "ang", "kind": "measurement", "goal_type": "angle", "solid_id": "s2", "target": {"plane1": ["S", "B", "C"], "plane2": ["A", "B", "C"]}, "quote": Q1})
@probe("C1.angle_plane1_plane2_scope_s1_control", C1, "CTL")
def _(p): p["math_goals"].append({"goal_id": "ang", "kind": "measurement", "goal_type": "angle", "solid_id": "s1", "target": {"plane1": ["S", "B", "C"], "plane2": ["A", "B", "C"]}, "quote": Q1})
@probe("C1.dist_plane1_plane2_scope_s2_ops_s1_only", C1)
def _(p): p["math_goals"].append({"goal_id": "dd", "kind": "measurement", "goal_type": "distance", "solid_id": "s2", "target": {"plane1": ["S", "A", "B"], "plane2": ["S", "C", "D"]}, "quote": Q1})
@probe("C1.dist_segment_scope_s2_ops_s1_only", C1)
def _(p): p["math_goals"].append({"goal_id": "dd", "kind": "measurement", "goal_type": "distance", "solid_id": "s2", "target": {"segment": ["S", "C"]}, "quote": Q1})
@probe("C1.dist_point_line_scope_s2_point_S", C1)
def _(p): p["math_goals"].append({"goal_id": "dd", "kind": "measurement", "goal_type": "distance", "solid_id": "s2", "target": {"point": "S", "line": ["B", "C"]}, "quote": Q1})
@probe("C1.dist_segment_scope_s1_control", C1, "CTL")
def _(p): p["math_goals"].append({"goal_id": "dd", "kind": "measurement", "goal_type": "distance", "solid_id": "s1", "target": {"segment": ["S", "C"]}, "quote": Q1})


def hyphen(p):
    q = json.loads(json.dumps(p, ensure_ascii=False).replace('"s1"', '"pyr-1"').replace('"s2"', '"pyr-2"'))
    p.clear(); p.update(q)


@probe("C1.hyphen_ids_qualified_control", C1, "CTL")
def _(p): hyphen(p); p["premises"][2]["args"]["segment"] = ["pyr-1::S", "pyr-1::A"]
@probe("C1.hyphen_ids_unqualified_control", C1, "CTL")
def _(p): hyphen(p)


# ---------- SEC1: single pyramid + section + derived solid ----------
def two(p):
    """Add a second declared pyramid T.ABCD (stated in text) to SEC1."""
    p["problem_text"] += " Cho hình chóp T.ABCD có TA vuông góc với (ABCD) và TA = 3."
    p["solids"].append({"solid_id": "t_abcd", "solid_type": "pyramid", "notation": "T.ABCD", "quote": "Cho hình chóp T.ABCD"})
    p["premises"] += [{"kind": "line_perp_plane", "solid_id": "t_abcd", "args": {"line": ["T", "A"], "plane": ["A", "B", "C", "D"]}, "quote": "TA vuông góc với (ABCD)"},
                      {"kind": "segment_length", "solid_id": "t_abcd", "args": {"segment": ["T", "A"], "value": "3"}, "quote": "TA = 3"}]


QS = "tỉ số thể tích khối chóp cắt bởi (α) so với S.ABCD"
@probe("SEC1.control", SEC1, "CTL")
def _(p): pass
@probe("SEC1.two_solids_control", SEC1, "CTL")
def _(p): two(p)
@probe("SEC1.plane_section_goal_target_solid_other", SEC1)
def _(p): two(p); p["simulation_goals"][1]["target_solid_id"] = "t_abcd"
@probe("SEC1.plane_section_goal_parent_other", SEC1)
def _(p): two(p); p["simulation_goals"][1]["parent_solid_id"] = "t_abcd"
@probe("SEC1.derived_parent_other", SEC1)
def _(p): two(p); p["simulation_goals"][2]["parent_solid_id"] = "t_abcd"
@probe("SEC1.derived_target_solid_other", SEC1)
def _(p): two(p); p["simulation_goals"][2]["target_solid_id"] = "t_abcd"
@probe("SEC1.derived_apex_qualified_other", SEC1)
def _(p): two(p); p["simulation_goals"][2]["apex_ref"] = "t_abcd::A"
@probe("SEC1.derived_apex_unqualified_T", SEC1)
def _(p): two(p); p["simulation_goals"][2]["apex_ref"] = "T"
@probe("SEC1.derived_parent_is_derived_self", SEC1)
def _(p): p["simulation_goals"][2]["parent_solid_id"] = "s_top"
@probe("SEC1.section_plane_qualified_other", SEC1)
def _(p): two(p); p["derived_sections"][0]["parallel_plane"] = ["t_abcd::A", "B", "C"]
@probe("SEC1.named_intersection_key_foreign_ns", SEC1)
def _(p): p["derived_sections"][0]["cut_edges"] = [["S", "B"], ["S", "C"], ["S", "D"], ["S", "A"]]; p["derived_sections"][0]["named_intersections"] = {"zz::S-zz::B": "N"}
@probe("SEC1.named_intersection_key_other_ns", SEC1)
def _(p): two(p); p["derived_sections"][0]["cut_edges"] = [["S", "B"], ["S", "C"], ["S", "D"], ["S", "A"]]; p["derived_sections"][0]["named_intersections"] = {"t_abcd::A-t_abcd::B": "N"}
@probe("SEC1.ratio_den_other_solid", SEC1)
def _(p): two(p); p["math_goals"][1]["denominator_solid_id"] = "t_abcd"
@probe("SEC1.ratio_num_den_swapped", SEC1, "INFO")
def _(p): g = p["math_goals"][1]; g["numerator_solid_id"], g["denominator_solid_id"] = g["denominator_solid_id"], g["numerator_solid_id"]
@probe("SEC1.residual_parent_other", SEC1)
def _(p): two(p); p["math_goals"].append({"goal_id": "res", "kind": "residual_volume", "parent_solid_id": "t_abcd", "cut_solid_id": "s_top", "quote": QS})
@probe("SEC1.residual_valid_control", SEC1, "CTL")
def _(p): p["math_goals"].append({"goal_id": "res", "kind": "residual_volume", "parent_solid_id": "s_abcd", "cut_solid_id": "s_top", "quote": QS})
@probe("SEC1.area_goal_scope_other", SEC1)
def _(p): two(p); p["math_goals"][0]["solid_id"] = "t_abcd"
@probe("SEC1.area_goal_target_solid_other", SEC1)
def _(p): two(p); p["math_goals"][0]["target"]["solid"] = "T.ABCD"
@probe("SEC1.area_goal_target_solid_alias_ok", SEC1, "CTL")
def _(p): p["math_goals"][0]["target"]["solid"] = "S.ABCD"
@probe("SEC1.area_goal_scope_ok", SEC1, "CTL")
def _(p): p["math_goals"][0]["solid_id"] = "s_abcd"
@probe("SEC1.vol_goal_on_derived_ok", SEC1, "CTL")
def _(p): p["math_goals"].append({"goal_id": "vt", "kind": "measurement", "goal_type": "volume", "target": {"solid": "s_top"}, "quote": QS})
@probe("SEC1.vol_goal_on_derived_scope_parent", SEC1)
def _(p): p["math_goals"].append({"goal_id": "vt", "kind": "measurement", "goal_type": "volume", "solid_id": "s_abcd", "target": {"solid": "s_top"}, "quote": QS})
@probe("SEC1.highlight_derived_and_section_ok", SEC1, "CTL")
def _(p): p["simulation_goals"].append({"goal_id": "h", "kind": "highlight_geometry", "target_solid_id": "s_abcd", "target_refs": ["sec_alpha", "s_top", "s_abcd::M"], "quote": "Gọi M là trung điểm của SA"})
@probe("SEC1.highlight_derived_solid_qualified_ns", SEC1)
def _(p): p["simulation_goals"].append({"goal_id": "h", "kind": "highlight_geometry", "target_refs": ["s_top::S"], "quote": "Gọi M là trung điểm của SA"})
@probe("SEC1.premise_scope_derived_solid", SEC1)
def _(p): p["premises"][3]["solid_id"] = "s_top"

# ---------- Adapter3 legacy (non-identity bindings): the bridge defers on a capability code ----------
@probe("BIND.control", BIND, "CTL")
def _(p): pass
@probe("BIND.measure_scope_pyr2_operand_S_only_pyr1", BIND)
def _(p): p["math_goals"].append({"goal_id": "len", "kind": "measurement", "goal_type": "distance", "solid_id": "pyr2", "target": {"segment": ["S", "B"]}, "quote": "tính tỉ số thể tích"})
@probe("BIND.highlight_scope_pyr1_ref_pyr2", BIND)
def _(p): p["simulation_goals"].append({"goal_id": "h2", "kind": "highlight_geometry", "target_solid_id": "pyr1", "target_refs": ["pyr2::D"], "quote": "Dựng hai khối chóp"})
@probe("BIND.rel_perp_scope_pyr2_refs_pyr1", BIND)
def _(p): p["relations"].append(rel(kind="perpendicular", solid_id="pyr2", entity_a=["pyr1::S", "pyr1::A"], entity_b=["A", "B"], quote="SA vuông góc với mặt phẳng (ABC)"))
@probe("BIND.vol_goal_alias_canonical_D1", BIND, "CTL")
def _(p): p["math_goals"][1]["target"] = {"solid": "D1.ABC"}
@probe("BIND.vol_goal_alias_local_D", BIND, "CTL")
def _(p): p["math_goals"][1]["target"] = {"solid": "D.ABC"}
@probe("BIND.vol_goal_scope_pyr1_target_D1", BIND)
def _(p): p["math_goals"][1]["solid_id"] = "pyr1"; p["math_goals"][1]["target"] = {"solid": "D1.ABC"}
@probe("BIND.vol_goal_scope_pyr2_target_S_ABC", BIND)
def _(p): p["math_goals"][1]["solid_id"] = "pyr2"
@probe("BIND.premise_unscoped_operand_D_ambiguous", BIND)
def _(p): p["premises"][7].pop("solid_id"); p["premises"][7]["args"]["segment"] = ["D", "A"]
@probe("BIND.frame_anchor_other_solid", BIND)
def _(p): p["relations"][3]["anchor_refs"] = ["S", "B", "C"]


# ---------- curved ----------
def cone2(p):
    p["problem_text"] += " Cho hình nón đỉnh T, tâm đáy K, điểm B thuộc đường tròn đáy, bán kính đáy R = 3, chiều cao h = 4."
    p["solids"].append({"solid_id": "cone2", "solid_type": "cone", "notation": "T.K", "center": "K", "apex_or_top": "T", "rim_point": "B",
                        "radius": "3", "height": "4", "quote": "Cho hình nón đỉnh T, tâm đáy K, điểm B thuộc đường tròn đáy, bán kính đáy R = 3, chiều cao h = 4"})


QC = "Cho hình nón tròn xoay đỉnh S, tâm đáy O"
@probe("CONE.control", CONE, "CTL")
def _(p): pass
@probe("CONE.two_cones_control", CONE, "CTL")
def _(p): cone2(p)
@probe("CONE.derived_parent_other_cone", CONE)
def _(p): cone2(p); p["simulation_goals"][2]["parent_solid_id"] = "cone2"
@probe("CONE.derived_parent_absent_ok", CONE, "CTL")
def _(p): p["simulation_goals"][2].pop("parent_solid_id")
@probe("CONE.ratio_den_other_cone", CONE)
def _(p): cone2(p); p["math_goals"][3]["denominator_solid_id"] = "cone2"
@probe("CONE.residual_parent_other_cone", CONE)
def _(p): cone2(p); p["math_goals"][4]["parent_solid_id"] = "cone2"
@probe("CONE.residual_with_solid_id", CONE)
def _(p): p["math_goals"][4]["solid_id"] = "cone_main"
@probe("CONE.vol_target_other_cone_scope_main", CONE)
def _(p): cone2(p); p["math_goals"][0]["solid_id"] = "cone_main"; p["math_goals"][0]["target"] = {"solid": "cone2"}
@probe("CONE.vol_target_foreign", CONE)
def _(p): p["math_goals"][0]["target"] = {"solid": "zz"}
@probe("CONE.vol_target_notation_alias", CONE, "CTL")
def _(p): p["math_goals"][0]["target"] = {"solid": "S.O"}
@probe("CONE.vol_target_derived", CONE, "CTL")
def _(p): p["math_goals"][0]["target"] = {"solid": "cone_upper"}
@probe("CONE.vol_scope_only_no_target_solid", CONE, "CTL")
def _(p): p["math_goals"][0]["solid_id"] = "cone_main"
@probe("CONE.axial_area_target_solid_other", CONE)
def _(p): cone2(p); p["math_goals"][2]["target"]["solid"] = "cone2"
@probe("CONE.axial_area_scope_other", CONE)
def _(p): cone2(p); p["math_goals"][2]["solid_id"] = "cone2"
@probe("CONE.lateral_target_solid_id_nested_other", CONE)
def _(p): cone2(p); p["math_goals"][1]["target"] = {"solid": "cone_main", "solid_id": "cone2"}
@probe("CONE.lateral_target_solid_on_two_cones_unscoped", CONE, "INFO")
def _(p): cone2(p); p["math_goals"][1]["target"] = {"solid": "cone2"}
@probe("CONE.premise_scope_foreign", CONE)
def _(p): p["premises"] = [{"kind": "segment_length", "args": {"segment": ["S", "O"], "value": "4"}, "quote": "chiều cao h = 4", "solid_id": "zz"}]
@probe("CONE.premise_qualified_other_cone", CONE)
def _(p): cone2(p); p["premises"] = [{"kind": "segment_length", "args": {"segment": ["cone2::T", "cone2::K"], "value": "4"}, "quote": "chiều cao h = 4", "solid_id": "cone_main"}]
@probe("CONE.premise_unscoped_operands_other_cone_only", CONE)
def _(p): cone2(p); p["premises"] = [{"kind": "segment_length", "args": {"segment": ["T", "K"], "value": "4"}, "quote": "chiều cao h = 4", "solid_id": "cone_main"}]
@probe("CONE.relation_foreign", CONE)
def _(p): p["relations"] = [rel(kind="coordinate_frame", solid_id="zz", frame_id="root", anchor_refs=["S", "O", "A"], quote=QC)]
@probe("CONE.relation_perp_scope_other_refs_main", CONE)
def _(p): cone2(p); p["relations"] = [rel(kind="perpendicular", solid_id="cone2", entity_a=["cone_main::S", "cone_main::O"], entity_b=["cone_main::O", "cone_main::A"], quote=QC)]
@probe("CONE.relation_perp_scope_other_unqualified_refs_main", CONE)
def _(p): cone2(p); p["relations"] = [rel(kind="perpendicular", solid_id="cone2", entity_a=["S", "O"], entity_b=["O", "A"], quote=QC)]
@probe("CONE.highlight_scope_main_ref_cone2", CONE)
def _(p): cone2(p); p["simulation_goals"].append({"goal_id": "h", "kind": "highlight_geometry", "target_solid_id": "cone_main", "target_refs": ["cone2::T"], "quote": QC})
@probe("CONE.highlight_scope_main_ref_T_unqualified", CONE)
def _(p): cone2(p); p["simulation_goals"].append({"goal_id": "h", "kind": "highlight_geometry", "target_solid_id": "cone_main", "target_refs": ["T"], "quote": QC})
@probe("CONE.derived_apex_other_cone", CONE)
def _(p): cone2(p); p["simulation_goals"][2]["apex_ref"] = "T"
@probe("CONE.derived_apex_qualified_other", CONE)
def _(p): cone2(p); p["simulation_goals"][2]["apex_ref"] = "cone2::T"
@probe("CONE.target_nonstring_solid", CONE)
def _(p): p["math_goals"][0]["target"] = {"solid": 5}
@probe("CONE.target_section_id_nonstring", CONE)
def _(p): p["math_goals"][2]["target"] = {"section_id": 5}
@probe("CONE.target_section_id_unknown", CONE)
def _(p): p["math_goals"][2]["target"] = {"section_id": "nope"}
@probe("CYL.control", CYL, "CTL")
def _(p): pass
@probe("CYL.vol_scope_foreign", CYL)
def _(p): next(g for g in p["math_goals"] if g["kind"] == "measurement")["solid_id"] = "zz"
@probe("SPH.control", SPH, "CTL")
def _(p): pass
@probe("SPH.highlight_foreign_ns", SPH)
def _(p): p["simulation_goals"].append({"goal_id": "h", "kind": "highlight_geometry", "target_refs": ["zz::S"], "quote": p["solids"][0]["quote"]})

if __name__ == "__main__":
    only = sys.argv[2] if len(sys.argv) > 2 else None
    for name, base, fn, kind in PROBES:
        if only and only not in name:
            continue
        p = copy.deepcopy(base)
        fn(p)
        print(json.dumps({"probe": name, "kind": kind, **run3(p)}, ensure_ascii=False), flush=True)
