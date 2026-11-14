"""Agent-written DEVELOPMENT corpus of run `compositional-semantics-simulation-goals` (never a locked W2/W3 row, never H-1).

Each item: text, group, expect ("SERVE" | "REFUSE"), goal (the simulation objective a served item must construct), numeric
("NOT_ANSWERED" when the source asks a trigonometric value of an angle), pair (minimal-pair partner differing in ONE semantic
property) and same_as (a metamorphic variant that must behave like that item). Expectations are written from geometry and
the product's documented scope before measurement.
"""
from __future__ import annotations

B4 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a"
B3 = "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) và SA = a"

CORPUS: dict[str, dict] = {
    # ── multi-clause definitions in ONE sentence ────────────────────────────────────────────────────────────────────
    "mc_section_one_sentence": {"group": "multi_clause", "expect": "SERVE", "goal": "section",
        "text": f"{B4}, M là trung điểm của SA, mặt phẳng (P) đi qua M và song song với mặt đáy. Xác định thiết diện của hình chóp bởi (P)."},
    "mc_section_split": {"group": "multi_clause", "expect": "SERVE", "goal": "section", "same_as": "mc_section_one_sentence",
        "text": f"{B4}. Gọi M là trung điểm của SA. Mặt phẳng (P) đi qua M và song song với mặt đáy. Xác định thiết diện của hình chóp bởi (P)."},
    "mc_section_renamed": {"group": "metamorphic", "expect": "SERVE", "goal": "section", "same_as": "mc_section_one_sentence",
        "text": "Cho hình chóp T.EFGH có đáy EFGH là hình vuông cạnh a, TE vuông góc với mặt phẳng đáy và TE = a, K là trung điểm của TE, mặt phẳng (Q) đi qua K và song song với mặt đáy. Xác định thiết diện của hình chóp bởi (Q)."},
    "mc_section_greek": {"group": "metamorphic", "expect": "SERVE", "goal": "section", "same_as": "mc_section_one_sentence",
        "text": f"{B4}, M là trung điểm của SA, mặt phẳng (α) đi qua M và song song với mặt đáy. Xác định thiết diện của hình chóp bởi (α)."},
    "mc_extra_unread": {"group": "silent_loss_negative", "expect": "REFUSE", "pair": "mc_section_one_sentence",
        "text": f"{B4}, M là trung điểm của SA, mặt phẳng (P) đi qua M và song song với mặt đáy, N thuộc cạnh SB. Xác định thiết diện của hình chóp bởi (P)."},
    "mc_extra_unread2": {"group": "silent_loss_negative", "expect": "REFUSE", "pair": "mc_section_one_sentence",
        "text": f"{B4}, M là trung điểm của SA, các cạnh bên bằng nhau, mặt phẳng (P) đi qua M và song song với mặt đáy. Xác định thiết diện của hình chóp bởi (P)."},
    "mc_distance_extra_unread": {"group": "silent_loss_negative", "expect": "REFUSE", "pair": "mc_distance",
        "text": f"{B4}, tam giác SBC có diện tích lớn nhất. Tính khoảng cách từ A đến mặt phẳng (SBC)."},
    "mc_distance": {"group": "multi_clause", "expect": "SERVE", "goal": "distance",
        "text": f"{B4}. Tính khoảng cách từ A đến mặt phẳng (SBC)."},
    "mc_decimal_value": {"group": "multi_clause", "expect": "SERVE", "goal": "distance",
        "text": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng đáy và SA = 3,5. Tính khoảng cách từ A đến mặt phẳng (SBC)."},
    "mc_label_list": {"group": "multi_clause", "expect": "SERVE", "goal": "distance",
        "text": f"{B4}. Gọi M, N lần lượt là trung điểm của SB, SD. Tính khoảng cách từ M đến mặt phẳng (ABCD)."},
    # ── clause order: the plane is defined AFTER the question uses it ───────────────────────────────────────────────
    "order_plane_after_goal": {"group": "clause_order", "expect": "SERVE", "goal": "section", "same_as": "mc_section_split",
        "text": f"{B4}. Gọi M là trung điểm của SA. Xác định thiết diện của hình chóp bởi mặt phẳng (P), biết (P) đi qua M và song song với mặt đáy."},
    "order_plane_after_goal_sep": {"group": "clause_order", "expect": "SERVE", "goal": "section", "same_as": "mc_section_split",
        "text": f"{B4}. Gọi M là trung điểm của SA. Xác định thiết diện của hình chóp bởi mặt phẳng (P). Biết (P) đi qua M và song song với mặt đáy."},
    "order_plane_never_defined": {"group": "clause_order_negative", "expect": "REFUSE", "pair": "order_plane_after_goal",
        "text": f"{B4}. Gọi M là trung điểm của SA. Xác định thiết diện của hình chóp bởi mặt phẳng (P)."},
    "order_premises_swapped": {"group": "metamorphic", "expect": "SERVE", "goal": "distance", "same_as": "mc_distance",
        "text": "Cho hình chóp S.ABCD có SA = a, SA vuông góc với mặt phẳng đáy và đáy ABCD là hình vuông cạnh a. Tính khoảng cách từ A đến mặt phẳng (SBC)."},
    # ── described points: named / unnamed / free ────────────────────────────────────────────────────────────────────
    "dp_named_midpoint_goal": {"group": "described_point", "expect": "SERVE", "goal": "distance",
        "text": f"{B4}. Gọi M là trung điểm của SC. Tính khoảng cách từ M đến mặt phẳng (ABCD)."},
    "dp_unnamed_midpoint_goal": {"group": "described_point", "expect": "SERVE", "goal": "distance", "pair": "dp_named_midpoint_goal",
        "text": f"{B4}. Tính khoảng cách từ trung điểm của SC đến mặt phẳng (ABCD)."},
    "dp_unnamed_centroid_goal": {"group": "described_point", "expect": "SERVE", "goal": "distance",
        "text": f"{B4}. Tính khoảng cách từ trọng tâm của tam giác SBC đến mặt phẳng (ABCD)."},
    "dp_unnamed_through_point": {"group": "described_point", "expect": "SERVE", "goal": "section",
        "text": f"{B4}. Xác định thiết diện của hình chóp cắt bởi mặt phẳng đi qua trung điểm của SA và song song với mặt đáy."},
    "dp_free_point": {"group": "described_point_negative", "expect": "REFUSE", "pair": "dp_named_midpoint_goal",
        "text": f"{B4}. Điểm M thuộc cạnh SC. Tính khoảng cách từ M đến mặt phẳng (ABCD)."},
    "dp_free_point_goi": {"group": "described_point_negative", "expect": "REFUSE", "pair": "dp_named_midpoint_goal",
        "text": f"{B4}. Gọi M là một điểm thuộc cạnh SC. Tính khoảng cách từ M đến mặt phẳng (ABCD)."},
    "dp_midpoint_as_goal": {"group": "premise_vs_goal", "expect": "REFUSE", "pair": "dp_named_midpoint_goal",
        "text": f"{B4}. Hãy xác định trung điểm của SC."},
    "dp_reflection": {"group": "described_point_unsupported", "expect": "REFUSE",
        "text": f"{B4}. Gọi E là điểm đối xứng của A qua C. Tính khoảng cách từ E đến mặt phẳng (SBC)."},
    "dp_projection_unnamed_image": {"group": "described_point_unsupported", "expect": "REFUSE",
        "text": "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA = a và hình chiếu vuông góc của S lên mặt phẳng (ABC) trùng với trọng tâm của tam giác ABC. Tính khoảng cách từ S đến mặt phẳng (ABC)."},
    "dp_redefined_conflict": {"group": "contradiction", "expect": "REFUSE",
        "text": f"{B4}. Gọi M là trung điểm của SA. Gọi M là trung điểm của SB. Tính khoảng cách từ M đến mặt phẳng (ABCD)."},
    # ── simulation-oriented goals: cos / tan / sin of an angle ──────────────────────────────────────────────────────
    "goal_angle_line_plane": {"group": "goal_angle", "expect": "SERVE", "goal": "angle",
        "text": f"{B3}. Tính góc giữa SB và mặt phẳng (ABC)."},
    "goal_cos_line_plane": {"group": "goal_trig", "expect": "SERVE", "goal": "angle", "numeric": "NOT_ANSWERED", "pair": "goal_angle_line_plane",
        "text": f"{B3}. Tính cosin của góc giữa SB và mặt phẳng (ABC)."},
    "goal_cos_spelled": {"group": "goal_trig", "expect": "SERVE", "goal": "angle", "numeric": "NOT_ANSWERED", "same_as": "goal_cos_line_plane",
        "text": f"{B3}. Tính côsin của góc giữa SB và mặt phẳng (ABC)."},
    "goal_tan_line_plane": {"group": "goal_trig", "expect": "SERVE", "goal": "angle", "numeric": "NOT_ANSWERED",
        "text": f"{B3}. Tính tang của góc giữa SB và mặt phẳng (ABC)."},
    "goal_sin_mc_stem": {"group": "goal_trig", "expect": "SERVE", "goal": "angle", "numeric": "NOT_ANSWERED",
        "text": f"{B3}. Sin của góc giữa SB và mặt phẳng (ABC) bằng"},
    "goal_cos_planes": {"group": "goal_trig", "expect": "SERVE", "goal": "angle", "numeric": "NOT_ANSWERED",
        "text": "Cho hình lăng trụ tứ giác đều ABCD.A'B'C'D' có cạnh đáy bằng a, cạnh bên bằng a√3. Tính cosin của góc giữa hai mặt phẳng (ABCD) và (ABC')."},
    "goal_cos_lines": {"group": "goal_trig", "expect": "SERVE", "goal": "angle", "numeric": "NOT_ANSWERED",
        "text": "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. Tính cosin của góc giữa hai đường thẳng AC và A'B."},
    "goal_tan_right_angle": {"group": "goal_trig", "expect": "SERVE", "goal": "angle", "numeric": "NOT_ANSWERED",
        "text": f"{B4}. Tính tang của góc giữa SA và mặt phẳng (ABCD)."},
    "goal_cos_scale_free": {"group": "goal_trig_underdetermined", "expect": "REFUSE",
        "text": "Cho tứ diện đều ABCD. Gọi M là trung điểm của CD. Côsin của góc giữa hai đường thẳng AC và BM bằng"},
    "goal_cos_of_length_neg": {"group": "goal_trig_negative", "expect": "REFUSE",
        "text": f"{B3}. Tính cosin của độ dài SB."},
    "goal_cos_squared_neg": {"group": "goal_trig_negative", "expect": "REFUSE",
        "text": f"{B3}. Tính bình phương cosin của góc giữa SB và mặt phẳng (ABC)."},
    "goal_cos_given_premise_neg": {"group": "premise_vs_goal", "expect": "REFUSE",
        "text": "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) và cosin của góc giữa SB và mặt phẳng (ABC) bằng 1/2. Tính độ dài SA."},
    "goal_cos_wrong_object_neg": {"group": "goal_trig_negative", "expect": "REFUSE",
        "text": f"{B3}. Tính cosin của góc giữa SB và mặt phẳng (SAC) và độ dài SC."},
    # ── proof-only requests ─────────────────────────────────────────────────────────────────────────────────────────
    "proof_only": {"group": "proof", "expect": "REFUSE",
        "text": f"{B4}. Chứng minh BC vuông góc với mặt phẳng (SAB)."},
    "proof_premise_not_given": {"group": "premise_vs_goal", "expect": "REFUSE",
        "text": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a và SA = a. Chứng minh SA vuông góc với mặt đáy. Tính khoảng cách từ A đến mặt phẳng (SBC)."},
    # ── ambiguity / contradiction ───────────────────────────────────────────────────────────────────────────────────
    "amb_plane_not_unique": {"group": "ambiguity", "expect": "REFUSE",
        "text": f"{B4}. Mặt phẳng (P) đi qua A. Xác định thiết diện của hình chóp bởi (P)."},
    "contra_two_lengths": {"group": "contradiction", "expect": "REFUSE",
        "text": f"{B4}, SA = 2a. Tính khoảng cách từ A đến mặt phẳng (SBC)."},
    "contra_skew_intersection": {"group": "contradiction", "expect": "REFUSE",
        "text": f"{B4}. Gọi I là giao điểm của SA và BC. Tính khoảng cách từ I đến mặt phẳng (SCD)."},
    "diagram_fact": {"group": "diagram_dependent", "expect": "REFUSE",
        "text": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA = a (tham khảo hình vẽ, SA vuông góc với đáy như trên hình). Tính khoảng cách từ A đến mặt phẳng (SBC)."},
}

# ── run `target-invariant-regular-solid-semantics`: similarity-scale normalisation (agent-written, development) ─────────────────
_ISO = "Cho hình chóp S.ABC có đáy là tam giác vuông cân tại A, SA vuông góc với đáy và SA = AB. "
CORPUS.update({
    "scale_iso_planes": {"group": "scale_certified", "expect": "SERVE", "goal": "angle",
        "text": _ISO + "Tính góc giữa hai mặt phẳng (SBC) và (SBA)."},
    "scale_iso_tan": {"group": "scale_certified", "expect": "SERVE", "goal": "angle", "numeric": "NOT_ANSWERED",
        "text": _ISO + "Tang của góc giữa hai mặt phẳng (SBC) và (SBA) bằng"},
    "scale_iso_line_plane": {"group": "scale_certified", "expect": "SERVE", "goal": "angle",
        "text": _ISO + "Tính góc giữa đường thẳng SB và mặt phẳng (ABC)."},
    "scale_iso_renamed": {"group": "metamorphic", "expect": "SERVE", "goal": "angle", "same_as": "scale_iso_planes",
        "text": "Cho hình chóp T.XYZ có đáy là tam giác vuông cân tại X, TX vuông góc với đáy và TX = XY. Tính góc giữa hai mặt phẳng (TYZ) và (TYX)."},
    "scale_iso_with_length": {"group": "scale_negative", "expect": "SERVE", "goal": "angle", "same_as": "scale_iso_planes",
        "text": "Cho hình chóp S.ABC có đáy là tam giác vuông cân tại A, AB = 2, SA vuông góc với đáy và SA = AB. Tính góc giữa hai mặt phẳng (SBC) và (SBA)."},
    "scale_shape_free": {"group": "scale_negative", "expect": "REFUSE",
        "text": "Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB. Tính góc giữa hai mặt phẳng (SBC) và (ABC)."},
    "scale_height_free": {"group": "scale_negative", "expect": "REFUSE",
        "text": "Cho hình chóp S.ABC có đáy là tam giác vuông cân tại A và SA vuông góc với đáy. Tính góc giữa hai mặt phẳng (SBC) và (SBA)."},
    "scale_absolute_volume": {"group": "scale_negative", "expect": "REFUSE",
        "text": _ISO + "Tính thể tích khối chóp S.ABC."},
    "scale_regular_tetra_no_side": {"group": "scale_negative", "expect": "REFUSE",
        "text": "Cho tứ diện đều ABCD. Gọi M là trung điểm của CD. Tính góc giữa hai đường thẳng AC và BM."},
})

# ── run `target-invariant-regular-solid-semantics`: free shape + target invariance, regular tetrahedron ────────────
_RB = "Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB. "
CORPUS.update({
    "ti_right_b_planes": {"group": "target_invariant", "expect": "SERVE", "goal": "angle",
        "text": _RB + "Tính góc giữa hai mặt phẳng (SBC) và (ABC)."},
    "ti_right_b_tan": {"group": "target_invariant", "expect": "SERVE", "goal": "angle", "numeric": "NOT_ANSWERED",
        "text": _RB + "Tang của góc giữa hai mặt phẳng (SBC) và (ABC) bằng"},
    "ti_renamed": {"group": "metamorphic", "expect": "SERVE", "goal": "angle", "same_as": "ti_right_b_planes",
        "text": "Cho hình chóp T.XYZ có đáy là tam giác vuông tại Y, TX vuông góc với đáy và TX = XY. Tính góc giữa hai mặt phẳng (TYZ) và (XYZ)."},
    "ti_varying_line_plane": {"group": "target_invariant_negative", "expect": "REFUSE",
        "text": _RB + "Tính góc giữa đường thẳng SC và mặt phẳng (ABC)."},
    "ti_height_free": {"group": "target_invariant_negative", "expect": "REFUSE",
        "text": "Cho hình chóp S.ABC có đáy là tam giác vuông tại B và SA vuông góc với đáy. Tính góc giữa hai mặt phẳng (SBC) và (ABC)."},
    "ti_absolute_volume": {"group": "target_invariant_negative", "expect": "REFUSE",
        "text": _RB + "Tính thể tích khối chóp S.ABC."},
    "tet_lines": {"group": "regular_tetrahedron", "expect": "SERVE", "goal": "angle",
        "text": "Cho tứ diện đều ABCD. Gọi M là trung điểm của CD. Tính góc giữa hai đường thẳng AC và BM."},
    "tet_cos_mc": {"group": "regular_tetrahedron", "expect": "SERVE", "goal": "angle", "numeric": "NOT_ANSWERED",
        "text": "Cho tứ diện đều ABCD. Gọi M là trung điểm của CD. Côsin của góc giữa hai đường thẳng AC và BM bằng"},
    "tet_renamed": {"group": "metamorphic", "expect": "SERVE", "goal": "angle", "same_as": "tet_lines",
        "text": "Cho tứ diện đều PQRS. Gọi K là trung điểm của RS. Tính góc giữa hai đường thẳng PR và QK."},
    "tet_with_side": {"group": "metamorphic", "expect": "SERVE", "goal": "angle", "same_as": "tet_lines",
        "text": "Cho tứ diện đều ABCD cạnh a. Gọi M là trung điểm của CD. Tính góc giữa hai đường thẳng AC và BM."},
    "tet_edge_face": {"group": "regular_tetrahedron", "expect": "SERVE", "goal": "angle",
        "text": "Cho tứ diện đều ABCD. Tính góc giữa đường thẳng AB và mặt phẳng (BCD)."},
    "tet_not_regular": {"group": "regular_tetrahedron_negative", "expect": "REFUSE",
        "text": "Cho tứ diện ABCD. Gọi M là trung điểm của CD. Tính góc giữa hai đường thẳng AC và BM."},
    "tet_regular_pyramid_only": {"group": "regular_tetrahedron_negative", "expect": "REFUSE",
        "text": "Cho hình chóp tam giác đều S.ABC. Gọi M là trung điểm của BC. Tính góc giữa hai đường thẳng SA và BM."},
    "tet_conflict": {"group": "regular_tetrahedron_negative", "expect": "REFUSE",
        "text": "Cho tứ diện đều ABCD cạnh 2 và AB = 3. Tính góc giữa hai đường thẳng AC và BD."},
})


# ── run `proof-soundness-generalized-angle-invariance`: non-isosceles ratio, perpendicular planes, line–plane, line–line ──
_RB2 = "Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = 2AB. "
CORPUS.update({
    "pa_ratio2_planes": {"group": "proof_angle", "expect": "SERVE", "goal": "angle",
        "text": _RB2 + "Tính góc giữa hai mặt phẳng (SBC) và (ABC)."},
    "pa_ratio2_tan": {"group": "proof_angle", "expect": "SERVE", "goal": "angle", "numeric": "NOT_ANSWERED",
        "text": _RB2 + "Tang của góc giữa hai mặt phẳng (SBC) và (ABC) bằng"},
    "pa_source_perp_lines": {"group": "proof_angle", "expect": "SERVE", "goal": "angle",
        "text": "Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), AB vuông góc với BC và SA = AB. Tính góc giữa hai mặt phẳng (SBC) và (ABC)."},
    "pp_base": {"group": "perp_planes", "expect": "SERVE", "goal": "angle",
        "text": _RB + "Tính góc giữa hai mặt phẳng (SAC) và (ABC)."},
    "pp_lateral": {"group": "perp_planes", "expect": "SERVE", "goal": "angle",
        "text": _RB + "Tính góc giữa hai mặt phẳng (SBC) và (SAB)."},
    "lp_isosceles": {"group": "line_plane", "expect": "SERVE", "goal": "angle",
        "text": _RB + "Tính góc giữa đường thẳng SB và mặt phẳng (ABC)."},
    "lp_ratio2": {"group": "line_plane", "expect": "SERVE", "goal": "angle",
        "text": _RB2 + "Tính góc giữa đường thẳng SB và mặt phẳng (ABC)."},
    "lp_perpendicular": {"group": "line_plane", "expect": "SERVE", "goal": "angle",
        "text": _RB + "Tính góc giữa đường thẳng SA và mặt phẳng (ABC)."},
    "lp_renamed": {"group": "metamorphic", "expect": "SERVE", "goal": "angle", "same_as": "lp_ratio2",
        "text": "Cho hình chóp T.XYZ có đáy là tam giác vuông tại Y, TX vuông góc với đáy và TX = 2XY. Tính góc giữa đường thẳng TY và mặt phẳng (XYZ)."},
    "ll_meeting": {"group": "line_line", "expect": "SERVE", "goal": "angle",
        "text": _RB + "Tính góc giữa hai đường thẳng SB và SA."},
    "ll_perpendicular": {"group": "line_line", "expect": "SERVE", "goal": "angle",
        "text": _RB + "Tính góc giữa hai đường thẳng SB và BC."},
    "ll_skew_perpendicular": {"group": "line_line", "expect": "SERVE", "goal": "angle",
        "text": _RB + "Tính góc giữa hai đường thẳng SA và BC."},
    "ll_skew_varying": {"group": "proof_angle_negative", "expect": "REFUSE",
        "text": _RB + "Tính góc giữa hai đường thẳng SC và AB."},
    "lp_varying_lateral": {"group": "proof_angle_negative", "expect": "REFUSE",
        "text": _RB + "Tính góc giữa đường thẳng SC và mặt phẳng (SAB)."},
    "lp_no_ratio": {"group": "proof_angle_negative", "expect": "REFUSE",
        "text": "Cho hình chóp S.ABC có đáy là tam giác vuông tại B và SA vuông góc với đáy. Tính góc giữa đường thẳng SB và mặt phẳng (ABC)."},
    "pa_prism_out_of_domain": {"group": "proof_angle_negative", "expect": "REFUSE",
        "text": "Cho hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác vuông tại B và AA' = AB. Tính góc giữa hai mặt phẳng (A'BC) và (ABC)."},
})

# Expectations superseded by THIS run's capabilities (recorded in the report; the earlier runs' receipts are unchanged):
# a plane angle fixed by a fixed triangle under a free shape, and a regular tetrahedron without side, are now served.
CORPUS["scale_shape_free"].update(expect="SERVE", goal="angle", superseded="REFUSE (certified-scale-cache-safety)")
CORPUS["scale_regular_tetra_no_side"].update(expect="SERVE", goal="angle", superseded="REFUSE (certified-scale-cache-safety)")
CORPUS["goal_cos_scale_free"].update(expect="SERVE", goal="angle", numeric="NOT_ANSWERED",
                                     superseded="REFUSE (compositional-semantics-simulation-goals)")
