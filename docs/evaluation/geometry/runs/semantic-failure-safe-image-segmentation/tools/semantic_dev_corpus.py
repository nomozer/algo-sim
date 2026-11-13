"""SEMANTIC DEVELOPMENT CORPUS of run `semantic-failure-safe-image-segmentation` — development from birth, never called
blind or unseen. Agent-written from geometric concepts (not from any locked W2/W3 row, which stay unread), grouped by
the linguistic cause they probe, with minimal pairs and metamorphic variants.

Each item: group, text, expect = ("SERVED", goal) | ("REFUSED", root_cause), and for a metamorphic variant the id of
the item it must agree with (`same_as`). A refused item's root cause is what a correct diagnosis must say.
"""
from __future__ import annotations

P = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
P1 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a"
R = "Cho hình chóp T.MNPQ có đáy MNPQ là hình vuông cạnh a, TM vuông góc với mặt phẳng đáy và TM = a. "
C = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. "
MSA = "Gọi M là trung điểm của SA. "

CORPUS: dict[str, dict] = {
    # ── goal extraction: question wording of supported measurements ───────────────────────────────────────────────
    "goal_volume_tinh": {"group": "goal_extraction", "text": P + "Tính thể tích khối chóp S.ABCD.", "expect": ("SERVED", "volume")},
    "goal_volume_stem": {"group": "goal_extraction", "text": P + "Thể tích khối chóp S.ABCD bằng", "expect": ("SERVED", "volume"), "same_as": "goal_volume_tinh"},
    "goal_volume_da_cho": {"group": "goal_extraction", "text": P + "Thể tích của khối chóp đã cho bằng", "expect": ("SERVED", "volume"), "same_as": "goal_volume_tinh"},
    "goal_volume_theo_a": {"group": "goal_extraction", "text": P + "Tính theo a thể tích khối chóp S.ABCD.", "expect": ("SERVED", "volume"), "same_as": "goal_volume_tinh"},
    "goal_distance_tinh": {"group": "goal_extraction", "text": P + "Tính khoảng cách từ A đến mặt phẳng (SBC).", "expect": ("SERVED", "distance")},
    "goal_distance_stem": {"group": "goal_extraction", "text": P + "Khoảng cách từ A đến mặt phẳng (SBC) bằng", "expect": ("SERVED", "distance"), "same_as": "goal_distance_tinh"},
    "goal_angle_tinh": {"group": "goal_extraction", "text": P + "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).", "expect": ("SERVED", "angle")},
    "goal_angle_stem": {"group": "goal_extraction", "text": P + "Góc giữa đường thẳng SC và mặt phẳng (ABCD) bằng", "expect": ("SERVED", "angle"), "same_as": "goal_angle_tinh"},
    "goal_angle_stem_day": {"group": "goal_extraction", "text": P + "Góc giữa đường thẳng SC và mặt phẳng đáy bằng", "expect": ("SERVED", "angle"), "same_as": "goal_angle_tinh"},
    "goal_cos_unsupported": {"group": "goal_extraction", "text": P + "Tính côsin của góc giữa đường thẳng SC và mặt phẳng (ABCD).", "expect": ("REFUSED", "UNSUPPORTED_GOAL_FUNCTION")},
    "goal_tan_unsupported": {"group": "goal_extraction", "text": P + "Tang của góc giữa đường thẳng SC và mặt phẳng (ABCD) bằng", "expect": ("REFUSED", "UNSUPPORTED_GOAL_FUNCTION")},
    "goal_proof_only": {"group": "goal_extraction", "text": P + "Chứng minh rằng BC vuông góc với mặt phẳng (SAB).", "expect": ("REFUSED", "UNRECOGNIZED_GOAL")},
    # ── minimal pairs: definition vs goal; determined vs underdetermined plane ─────────────────────────────────────────
    "pair_point_definition": {"group": "minimal_pair", "text": P + MSA + "Tính khoảng cách từ M đến mặt phẳng (SBC).", "expect": ("SERVED", "distance")},
    "pair_point_as_goal": {"group": "minimal_pair", "text": P + "Xác định trung điểm của SA.", "expect": ("REFUSED", "UNRECOGNIZED_GOAL")},
    "pair_plane_determined": {"group": "minimal_pair", "text": P + MSA + "Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABC). Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P).", "expect": ("SERVED", "section")},
    "pair_plane_underdetermined": {"group": "minimal_pair", "text": P + MSA + "Mặt phẳng (P) đi qua M và song song với đường thẳng AB. Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P).", "expect": ("REFUSED", "UNRECOGNIZED_GEOMETRIC_ENTITY")},
    # ── named / unnamed planes and references ───────────────────────────────────────────────────────────────────────
    "ref_undefined_plane": {"group": "entity_reference", "text": P + "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (Q).", "expect": ("REFUSED", "UNRESOLVED_REFERENCE")},
    "ref_mp_abbrev": {"group": "entity_naming", "text": P + MSA + "Mặt phẳng (P) đi qua M và song song với mp(ABCD). Xác định thiết diện của hình chóp cắt bởi mp(P).", "expect": ("SERVED", "section"), "same_as": "pair_plane_determined"},
    "ref_relative_clause_point": {"group": "relative_clause", "text": P + "Mặt phẳng (P) đi qua trung điểm M của SA và song song với mặt phẳng (ABCD). Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P).", "expect": ("SERVED", "section"), "same_as": "pair_plane_determined"},
    "ref_unnamed_point_in_plane": {"group": "named_unnamed_points", "text": P + "Mặt phẳng (P) đi qua trung điểm của SA và song song với mặt phẳng (ABCD). Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P).", "expect": ("SERVED", "section"), "same_as": "pair_plane_determined"},
    "ref_goi_plane": {"group": "named_unnamed_planes", "text": P + MSA + "Gọi (α) là mặt phẳng qua M và song song với mặt phẳng (ABCD). Xác định thiết diện của hình chóp cắt bởi (α).", "expect": ("SERVED", "section"), "same_as": "pair_plane_determined"},
    # ── clause ordering / one long sentence / punctuation ───────────────────────────────────────────────────────────
    "order_one_sentence": {"group": "clause_ordering", "text": P1 + ", gọi M là trung điểm của SA, mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD). Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P).", "expect": ("SERVED", "section"), "same_as": "pair_plane_determined"},
    "order_semicolon": {"group": "clause_ordering", "text": P + MSA + "Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD); xác định thiết diện của hình chóp cắt bởi mặt phẳng (P).", "expect": ("SERVED", "section"), "same_as": "pair_plane_determined"},
    "order_goal_first": {"group": "clause_ordering", "text": P + "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P), biết (P) đi qua trung điểm M của SA và song song với mặt phẳng (ABCD).", "expect": ("REFUSED", "UNRESOLVED_REFERENCE")},
    "order_renamed": {"group": "metamorphic_rename", "text": R + "Gọi K là trung điểm của TM. Mặt phẳng (P) đi qua K và song song với mặt phẳng (MNPQ). Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P).", "expect": ("SERVED", "section"), "same_as": "pair_plane_determined"},
    # ── section / intersection goal wording ─────────────────────────────────────────────────────────────────────────
    "sec_hinh_gi_question": {"group": "section_goal", "text": P + MSA + "Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD). Thiết diện của hình chóp cắt bởi mặt phẳng (P) là hình gì?", "expect": ("SERVED", "section"), "same_as": "pair_plane_determined"},
    "sec_do_P_cat": {"group": "section_goal", "text": P + MSA + "Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD). Xác định thiết diện do mặt phẳng (P) cắt hình chóp.", "expect": ("SERVED", "section"), "same_as": "pair_plane_determined"},
    "sec_area_stem": {"group": "section_goal", "text": P + MSA + "Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD). Diện tích thiết diện của hình chóp cắt bởi mặt phẳng (P) bằng", "expect": ("SERVED", "area")},
    "int_goal": {"group": "intersection_goal", "text": P + "Tìm giao tuyến của hai mặt phẳng (SAB) và (SCD).", "expect": ("SERVED", "intersection")},
    "int_goal_mp": {"group": "intersection_goal", "text": P + "Tìm giao tuyến của mp(SAB) và mp(SCD).", "expect": ("SERVED", "intersection"), "same_as": "int_goal"},
    "multi_goals": {"group": "multiple_goals", "text": P + "Tính thể tích khối chóp S.ABCD và khoảng cách từ A đến mặt phẳng (SBC).", "expect": ("SERVED", "volume")},
    # ── diagram references, missing dimensions, inconsistent premises ───────────────────────────────────────────────
    "diagram_benign": {"group": "diagram_reference", "text": P + "Tính thể tích khối chóp S.ABCD (tham khảo hình vẽ).", "expect": ("SERVED", "volume"), "same_as": "goal_volume_tinh"},
    "diagram_dependent": {"group": "diagram_reference", "text": "Cho hình chóp S.ABCD như hình vẽ. Tính thể tích khối chóp S.ABCD.", "expect": ("REFUSED", "INSUFFICIENT_CONSTRAINTS")},
    "missing_dimension": {"group": "missing_dimensions", "text": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông, SA vuông góc với mặt phẳng đáy. Tính thể tích khối chóp S.ABCD.", "expect": ("REFUSED", "INSUFFICIENT_CONSTRAINTS")},
    "inconsistent": {"group": "inconsistent_premises", "text": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, AB = 2a, SA vuông góc với mặt phẳng đáy và SA = a. Tính thể tích khối chóp S.ABCD.", "expect": ("REFUSED", "SOURCE_CONFLICT")},
    "elliptical_role": {"group": "elliptical_statement", "text": "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a và cạnh bên bằng 2a. Góc giữa cạnh bên và mặt đáy bằng", "expect": ("REFUSED", "UNRECOGNIZED_GOAL")},
    "cube_stem_distance": {"group": "goal_extraction", "text": C + "Khoảng cách giữa hai đường thẳng AB và C'D' bằng", "expect": ("SERVED", "distance")},
}
