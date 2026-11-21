"""NEW_DIAGNOSTIC_DEVELOPMENT probes of run `independent-geometry-plane-constraints` (agent-written, development from
birth). Each probe: (category, expectation, text). Expectation: ("SERVED", n) — a closed section of n vertices (or an
intersection line when n == "line"); ("REFUSED", None) — anything but served. Written from the geometry, before any rule.
"""
from __future__ import annotations

P = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
REN = "Cho hình chóp T.MNPQ có đáy MNPQ là hình vuông cạnh a, TM vuông góc với mặt phẳng đáy và TM = a. "
T = "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) và SA = a. "
CUBE = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. "
MID_SA = "Gọi M là trung điểm của SA. "
MID_SC = "Gọi M là trung điểm của SC. "
MID_AD = "Gọi M là trung điểm của AD. "
SEC = "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P)."

PROBES: dict[str, tuple[str, tuple, str]] = {
    # ── through a point, parallel to a plane ────────────────────────────────────────────────────────────────────────
    "par_plane_named": ("parallel_plane", ("SERVED", 4), P + MID_SA + "Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD). " + SEC),
    "par_plane_base_word": ("parallel_plane", ("SERVED", 4), P + MID_SA + "Mặt phẳng (P) qua M và song song với mặt đáy. Tìm thiết diện của hình chóp với mặt phẳng (P)."),
    "par_plane_base_word2": ("parallel_plane", ("SERVED", 4), P + MID_SA + "Mặt phẳng (P) qua M và song song với mặt phẳng đáy. " + SEC),
    "par_plane_qua_dung": ("parallel_plane", ("SERVED", 4), P + MID_SA + "Qua M dựng mặt phẳng (α) song song với (ABCD). Tìm thiết diện của hình chóp cắt bởi (α)."),
    "par_plane_goi": ("parallel_plane", ("SERVED", 4), P + MID_SA + "Gọi (P) là mặt phẳng qua M và song song với (ABCD). " + SEC),
    "par_plane_lateral": ("parallel_plane", ("SERVED", 4), P + MID_AD + "Mặt phẳng (P) đi qua M và song song với mặt phẳng (SAB). " + SEC),
    "par_plane_renamed": ("parallel_plane", ("SERVED", 4), REN + "Gọi K là trung điểm của TM. Mặt phẳng (P) đi qua K và song song với mặt phẳng (MNPQ). " + SEC),
    "par_plane_cube": ("parallel_plane", ("SERVED", 3), CUBE + "Gọi M là trung điểm của AA'. Mặt phẳng (P) qua M và song song với mặt phẳng (A'BD). Tìm thiết diện của hình lập phương cắt bởi (P)."),
    "par_plane_area": ("parallel_plane", ("SERVED", 4), P + MID_SA + "Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD). Tính diện tích thiết diện của hình chóp cắt bởi (P)."),
    "par_plane_point_on_plane": ("parallel_plane_degenerate", ("REFUSED", None), P + "Mặt phẳng (P) đi qua A và song song với mặt phẳng (ABCD). " + SEC),
    "par_plane_triangle": ("parallel_plane", ("SERVED", 3), T + "Gọi M là trung điểm của SB. Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABC). Xác định thiết diện của hình chóp cắt bởi (P)."),
    # ── through a point, perpendicular to a line ────────────────────────────────────────────────────────────────────
    "perp_line_SA": ("perpendicular_line", ("SERVED", 4), P + MID_SA + "Mặt phẳng (P) qua M và vuông góc với SA. " + SEC),
    "perp_line_word": ("perpendicular_line", ("SERVED", 4), P + MID_SA + "Mặt phẳng (P) đi qua M và vuông góc với đường thẳng SA. " + SEC),
    "perp_line_cube_edge": ("perpendicular_line", ("SERVED", 4), CUBE + "Gọi M là trung điểm của AA'. Mặt phẳng (P) đi qua M và vuông góc với AA'. Tìm thiết diện của hình lập phương cắt bởi (P)."),
    "perp_line_cube_diagonal": ("perpendicular_line", ("SERVED", 3), CUBE + "Mặt phẳng (P) đi qua B và vuông góc với đường thẳng AC'. Tìm thiết diện của hình lập phương cắt bởi (P)."),
    "perp_bisector_plane": ("perpendicular_line", ("SERVED", 4), P + "Gọi (P) là mặt phẳng trung trực của đoạn thẳng SA. " + SEC),
    "perp_line_degenerate": ("perpendicular_line_degenerate", ("REFUSED", None), P + MID_SA + "Mặt phẳng (P) đi qua M và vuông góc với đường thẳng AA. " + SEC),
    # ── a line and a point not on it ────────────────────────────────────────────────────────────────────────────────
    "line_point_contains_first": ("line_and_point", ("SERVED", 4), P + MID_SC + "Mặt phẳng (P) chứa AB và đi qua M. " + SEC),
    "line_point_through_first": ("line_and_point", ("SERVED", 4), P + MID_SC + "Mặt phẳng (P) đi qua M và chứa đường thẳng AB. " + SEC),
    "line_point_on_line": ("line_and_point_degenerate", ("REFUSED", None), P + "Gọi M là trung điểm của AB. Mặt phẳng (P) chứa AB và đi qua M. " + SEC),
    # ── two lines ───────────────────────────────────────────────────────────────────────────────────────────────────
    "two_intersecting_lines": ("two_lines", ("SERVED", 3), CUBE + "Mặt phẳng (P) chứa hai đường thẳng cắt nhau AB' và AD'. Tìm thiết diện của hình lập phương cắt bởi (P)."),
    "two_parallel_lines": ("two_lines", ("SERVED", 4), CUBE + "Mặt phẳng (P) chứa hai đường thẳng song song AB và C'D'. Tìm thiết diện của hình lập phương cắt bởi (P)."),
    "two_lines_skew": ("two_lines_degenerate", ("REFUSED", None), CUBE + "Mặt phẳng (P) chứa hai đường thẳng AB và CC'. Tìm thiết diện của hình lập phương cắt bởi (P)."),
    "two_lines_same": ("two_lines_degenerate", ("REFUSED", None), CUBE + "Mặt phẳng (P) chứa hai đường thẳng AB và BA. Tìm thiết diện của hình lập phương cắt bởi (P)."),
    "through_point_parallel_two_lines": ("parallel_two_lines", ("SERVED", 4), P + MID_SA + "Mặt phẳng (P) qua M và song song với hai đường thẳng AB và AD. " + SEC),
    # ── underconstrained (must not serve) ───────────────────────────────────────────────────────────────────────────
    "under_parallel_one_line": ("underconstrained", ("REFUSED", None), P + MID_SA + "Mặt phẳng (P) đi qua M và song song với AB. " + SEC),
    "under_perpendicular_plane": ("underconstrained", ("REFUSED", None), P + MID_SA + "Mặt phẳng (P) đi qua M và vuông góc với mặt phẳng (ABCD). " + SEC),
    "under_contains_one_line": ("underconstrained", ("REFUSED", None), P + "Mặt phẳng (P) chứa AB. " + SEC),
    "under_any_plane": ("underconstrained", ("REFUSED", None), P + "Một mặt phẳng (P) bất kỳ cắt hình chóp. " + SEC),
    # ── compound constraints ────────────────────────────────────────────────────────────────────────────────────────
    "compound_contains_parallel": ("compound", ("SERVED", 3), P + "Mặt phẳng (P) chứa BD và song song với SC. " + SEC),
    "compound_contains_parallel_not_unique": ("compound_degenerate", ("REFUSED", None), P + "Mặt phẳng (P) chứa AB và song song với CD. " + SEC),
    "compound_contains_perpendicular_face": ("compound_degenerate", ("REFUSED", None), P + "Mặt phẳng (P) chứa AB và vuông góc với mặt phẳng (SAB). " + SEC),
    "compound_contains_perpendicular": ("compound", ("SERVED", 4), P + "Mặt phẳng (P) chứa AB và vuông góc với mặt phẳng (SCD). " + SEC),
    # ── wording, order, goal ────────────────────────────────────────────────────────────────────────────────────────
    "reordered_question_first": ("reordered", ("SERVED", 4), P + MID_SA + "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P), biết (P) đi qua M và song song với mặt phẳng (ABCD)."),
    "unicode_prime": ("unicode", ("SERVED", 4), "Cho hình lập phương ABCD.A′B′C′D′ có cạnh bằng a. Gọi M là trung điểm của AA′. Mặt phẳng (P) đi qua M và vuông góc với AA′. Tìm thiết diện của hình lập phương cắt bởi (P)."),
    "diagram_dependent": ("diagram", ("REFUSED", None), P + MID_SA + "Mặt phẳng (P) đi qua M như hình vẽ. " + SEC),
    "goal_as_premise": ("goal_vs_premise", ("REFUSED", None), P + MID_SA + "Chứng minh mặt phẳng (P) đi qua M và song song với (ABCD) cắt hình chóp theo một hình vuông."),
    "multiple_goals": ("multiple_goals", ("SERVED", 4), P + MID_SA + "Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD). Xác định thiết diện của hình chóp cắt bởi (P) và tính diện tích thiết diện đó."),
    "intersection_with_derived_plane": ("intersection_derived", ("SERVED", "line"), P + MID_SA + "Mặt phẳng (P) đi qua M và vuông góc với SA. Tìm giao tuyến của (P) và (SAB)."),
}
