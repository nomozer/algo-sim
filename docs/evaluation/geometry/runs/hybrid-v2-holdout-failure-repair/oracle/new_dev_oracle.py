# -*- coding: utf-8 -*-
"""Independent exact rational (`Fraction`) oracle for the `HYBRID_V2_HOLDOUT_FAILURE_REPAIR` development corpus.

This module computes expected section areas and polygon vertex counts directly from elementary
analytic/vector formulas in `fractions.Fraction`, completely independent of `app.simulation`.
"""
from __future__ import annotations

from fractions import Fraction
import math
from typing import Any


def _radical_str(area_sq: Fraction) -> str:
    """Format exact `sqrt(area_sq)` for rational `area_sq >= 0` in canonical radical notation."""
    if area_sq < 0:
        raise ValueError("area_sq must be non-negative")
    if area_sq == 0:
        return "0"
    num = area_sq.numerator
    den = area_sq.denominator
    # sqrt(num / den) = sqrt(num * den) / den
    n = num * den
    out_int = 1
    rem = 1
    d = 2
    temp = n
    while d * d <= temp:
        cnt = 0
        while temp % d == 0:
            temp //= d
            cnt += 1
        if cnt:
            out_int *= d ** (cnt // 2)
            if cnt % 2 == 1:
                rem *= d
        d += 1
    if temp > 1:
        rem *= temp
    g = math.gcd(out_int, den)
    p = out_int // g
    q = den // g
    if rem == 1:
        return f"{p}/{q}" if q != 1 else f"{p}"
    rad = f"√{rem}" if p == 1 else f"{p}√{rem}"
    return f"{rad}/{q}" if q != 1 else rad


# Independent elementary exact derivations for each positive development case (D001..D016):
# All numeric parameters are freshly chosen and disjoint from the 84-case holdout.
ORACLE_TABLE: dict[str, dict[str, Any]] = {
    # D001 (M1 - Greek α, P2 through midpoint M of AB parallel to SA and BC; right pyramid S.ABC, AB=3, BC=4, SA⊥(ABC), SA=5)
    # Section is a rectangle of sides (1/2)*SA = 5/2 and (1/2)*BC = 2 -> Area = (5/2)*2 = 5, area_sq = 25
    "D001": {
        "expected_status": "SERVED",
        "defect_family": "M1",
        "polygon_vertices": 4,
        "area_sq": Fraction(25, 1),
        "expected_answer": "5",
        "plane_label": "α",
        "certificate_category": "ENGINE_DERIVED_SECTION",
        "source_has_H": False,
    },
    # D002 (M1 - Greek β, inline section definition + semicolon + "tính diện tích thiết diện đó"; right prism ABC.A'B'C',
    # right at B with AB=BC=6, AA'=4, M midpoint of A'B', plane (β) through M parallel to BC' and AC)
    # Coordinates: B=(0,0,0), A=(6,0,0), C=(0,6,0), B'=(0,0,4), M=(3,0,4).
    # u = BC' = (0,6,4), v = AC = (-6,6,0), normal n = u x v = (-24, -24, 36) ~ (2, 2, -3).
    # Plane: 2x + 2y - 3z = 2(3) + 0 - 12 = -6.
    # Cuts A'B' at M(3,0,4), B'C' at N(0,3,4), BB' at P(0,0,2).
    # Triangle MNP: M-P = (3,0,2), N-P = (0,3,2), (M-P)x(N-P) = (-6,-6,9), |(M-P)x(N-P)|^2 = 36+36+81 = 153,
    # area_sq = 153 / 4 -> Area = 3√17/2.
    "D002": {
        "expected_status": "SERVED",
        "defect_family": "M1",
        "polygon_vertices": 3,
        "area_sq": Fraction(153, 4),
        "expected_answer": "3√17/2",
        "plane_label": "β",
        "certificate_category": "ENGINE_DERIVED_SECTION",
        "source_has_H": False,
    },
    # D003 (M1 - Latin plane P on P2 with "song song với các đường thẳng", cuboid ABCD.A'B'C'D' AB=6, AD=4, AA'=4,
    # M midpoint of AA'(0,0,2), parallel to BD and AB')
    # Coordinates: A=(0,0,0), B=(6,0,0), D=(0,4,0), A'=(0,0,4), M=(0,0,2).
    # u = BD = (-6,4,0), v = AB' = (6,0,4), u x v = (16, 24, -24) ~ (2, 3, -3).
    # Plane: 2x + 3y - 3z = -6.
    # Cuts AA' at M(0,0,2), A'B' at E(3,0,4), A'D' at F(0,2,4).
    # Triangle MEF: M-E=(-3,0,-2), M-F=(0,-2,-2), cross=(-4,-6,6), |cross|^2 = 16+36+36 = 88, area_sq = 88/4 = 22 -> √22.
    "D003": {
        "expected_status": "SERVED",
        "defect_family": "M1",
        "polygon_vertices": 3,
        "area_sq": Fraction(22, 1),
        "expected_answer": "√22",
        "plane_label": "P",
        "certificate_category": "ENGINE_DERIVED_SECTION",
        "source_has_H": False,
    },
    # D004 (M2 - omitted solid on height + plural "có các cạnh đáy bằng 8", regular pyramid S.ABCD, side=8, height=3,
    # N midpoint of SD, plane (P) through N parallel to (SAB), section-only)
    "D004": {
        "expected_status": "SERVED",
        "defect_family": "M2",
        "polygon_vertices": 4,
        "area_sq": None,
        "expected_answer": None,
        "plane_label": "P",
        "certificate_category": "ENGINE_DERIVED_SECTION",
        "source_has_H": False,
    },
    # D005 (M2 - omitted solid on height + area goal, regular triangular pyramid S.ABC, base side=6, height=4,
    # M midpoint of SA, plane (α) through M parallel to (ABC), area of section = (1/4)*Area(ABC) = (1/4)*(9√3) = 9√3/4)
    "D005": {
        "expected_status": "SERVED",
        "defect_family": "M2",
        "polygon_vertices": 3,
        "area_sq": Fraction(243, 16),
        "expected_answer": "9√3/4",
        "plane_label": "α",
        "certificate_category": "ENGINE_DERIVED_SECTION",
        "source_has_H": False,
    },
    # D006 (M2 - omitted solid on altitude: "SA là đường cao của hình chóp", S.ABC right at B, AB=6, BC=8, SA=10,
    # M midpoint of SA, plane (α) through M parallel to (ABC), area = (1/4)*(1/2*6*8) = 6)
    "D006": {
        "expected_status": "SERVED",
        "defect_family": "M2",
        "polygon_vertices": 3,
        "area_sq": Fraction(36, 1),
        "expected_answer": "6",
        "plane_label": "α",
        "certificate_category": "ENGINE_DERIVED_SECTION",
        "source_has_H": False,
    },
    # D007 (M3 - "thiết diện tạo bởi hình chóp và mặt phẳng (β)" + inline definition, S.ABC SA⊥(ABC), SA=8,
    # AB=AC=5, BC=6, M midpoint of BC, (β) through M parallel to (SAB), section-only)
    "D007": {
        "expected_status": "SERVED",
        "defect_family": "M3",
        "polygon_vertices": 3,
        "area_sq": None,
        "expected_answer": None,
        "plane_label": "β",
        "certificate_category": "ENGINE_DERIVED_SECTION",
        "source_has_H": False,
    },
    # D008 (M3 - 4-vertex diagonal reference plane (ACC'A') + "có các kích thước" + "thiết diện của hình hộp",
    # cuboid ABCD.A'B'C'D' AB=8, AD=6, AA'=5, M midpoint of BC, plane (α) through M parallel to (ACC'A'), section-only)
    "D008": {
        "expected_status": "SERVED",
        "defect_family": "M3",
        "polygon_vertices": 4,
        "area_sq": None,
        "expected_answer": None,
        "plane_label": "α",
        "certificate_category": "ENGINE_DERIVED_SECTION",
        "source_has_H": False,
    },
    # D009 (M3 - "vuông góc với đường chéo A'C" + "khi cắt bởi mặt phẳng (P)", cuboid ABCD.A'B'C'D' AB=4, BC=4, AA'=2,
    # M midpoint of AB(2,0,0), A'=(0,0,2), C=(4,4,0), A'C=(4,4,-2) ~ (2,2,-1).
    # Plane through M(2,0,0) with normal (2,2,-1): 2x + 2y - z = 4.
    # Cuts AB at M(2,0,0), AD at N(0,2,0), DD' at P(0,4,4)? Wait: z<=2! At z=2: 2x+2y=6 -> x+y=3.
    # On A'B'(y=0,z=2): Q(3,0,2); on A'D'(x=0,z=2): R(0,3,2).
    # Pentagon? No: M(2,0,0) on AB, N(0,2,0) on AD, R(0,3,2) on A'D', Q(3,0,2) on A'B' -> trapezoid MNRQ!
    # Wait: MN = √8 = 2√2, QR = √18 = 3√2, height between parallel lines MN and QR:
    # midpoint of MN is (1,1,0), midpoint of QR is (3/2,3/2,2), vector = (1/2,1/2,2), length^2 = 1/4+1/4+4 = 9/2, h = 3/√2.
    # Area = (MN + QR)/2 * h = (5√2 / 2) * (3 / √2) = 15/2, area_sq = 225/4!)
    "D009": {
        "expected_status": "SERVED",
        "defect_family": "M3",
        "polygon_vertices": 4,
        "area_sq": Fraction(225, 4),
        "expected_answer": "15/2",
        "plane_label": "P",
        "certificate_category": "ENGINE_DERIVED_SECTION",
        "source_has_H": False,
    },
    # D010 (M3 - symbolic "Tính theo a diện tích thiết diện...", cube ABCD.A'B'C'D' side a, M midpoint of AA',
    # plane (P) through M parallel to (ABCD), area = a^2)
    "D010": {
        "expected_status": "SERVED",
        "defect_family": "M3",
        "polygon_vertices": 4,
        "area_sq": Fraction(1, 1),
        "expected_answer": "a²",
        "plane_label": "P",
        "certificate_category": "ENGINE_DERIVED_SECTION",
        "source_has_H": False,
    },
    # D011 (M3 - named section polygon "Xác định thiết diện MNP và tính diện tích của thiết diện này",
    # S.ABC with SA⊥(ABC), SA=6, ABC right at A with AB=6, AC=8, M midpoint of SA, plane (α) through M parallel to (ABC)
    # cutting SB, SC at N, P -> Category A DINH_CAT_CANH, area = (1/4)*(1/2*6*8) = 6)
    "D011": {
        "expected_status": "SERVED",
        "defect_family": "M3",
        "polygon_vertices": 3,
        "area_sq": Fraction(36, 1),
        "expected_answer": "6",
        "plane_label": "α",
        "certificate_category": "DINH_CAT_CANH",
        "source_has_H": False,
    },
    # D012 (M4 + R2 - compound premise "Cho hình chóp S.ABC có đáy là tam giác ABC vuông tại A với AB = 9, AC = 12"
    # + "Hình chiếu vuông góc của S lên mặt phẳng (ABC) trùng với trung điểm H của cạnh BC và SH = 6",
    # M midpoint of AB, plane (P) through M perpendicular to BC.
    # Note: H is explicitly in source! So H must keep notation="H", while H1..H4 must have notation=None!)
    # Let's compute exact area of D012:
    # A=(0,0,0), B=(9,0,0), C=(0,12,0), BC=(-9,12,0), length BC=15.
    # H = midpoint(BC) = (9/2, 6, 0), S = (9/2, 6, 6).
    # M = midpoint(AB) = (9/2, 0, 0).
    # Plane (P) through M(9/2, 0, 0) perpendicular to BC(-3, 4, 0): -3x + 4y = -27/2 -> 6x - 8y = 27.
    # Since SH ⊥ (ABC) and SH ⊥ BC, any plane ⊥ BC is parallel to SH!
    # Wait: does 6x - 8y = 27 pass through H(9/2, 6, 0)? At H: 6(9/2) - 8(6) = 27 - 48 = -21 != 27.
    # On base ABC: cuts AB at M(9/2, 0, 0) and BC at K where B + t(C-B) = (9-9t, 12t, 0):
    # 6(9-9t) - 8(12t) = 27 -> 54 - 150t = 27 -> t = 27/150 = 9/50.
    # Distance MK in right triangle ABC: BM = 9/2, cos B = AB/BC = 9/15 = 3/5, sin B = 4/5.
    # Since MK ⊥ BC in right triangle ABC, MK = BM * sin B = (9/2)*(4/5) = 18/5!
    # Wait: what about the cut on SB?
    # S = (9/2, 6, 6), B = (9, 0, 0). On SB: B + u(S-B) = (9 - 9u/2, 6u, 6u).
    # 6(9 - 9u/2) - 8(6u) = 27 -> 54 - 27u - 48u = 27 -> 75u = 27 -> u = 9/25.
    # Since plane (P) is parallel to SH (vertical), the section is a right triangle MKL where MK lies in (ABC) (length 18/5)
    # and ML is parallel to SH? Wait: M=(9/2,0,0), L on SB is (9 - 81/50, 54/25, 54/25) = (369/50, 108/50, 108/50),
    # and K on BC is (9 - 81/50, 108/50, 0) = (369/50, 108/50, 0)!
    # Aha! L - K = (0, 0, 54/25) is purely vertical (parallel to SH, perpendicular to (ABC) and therefore ⊥ MK)!
    # So triangle MKL is right-angled at K with legs MK = 18/5 and KL = 54/25!
    # Therefore Area(MKL) = (1/2) * (18/5) * (54/25) = 486 / 125!
    # And area_sq = (486 / 125)^2 = 236196 / 15625!
    "D012": {
        "expected_status": "SERVED",
        "defect_family": "M4",
        "polygon_vertices": 3,
        "area_sq": Fraction(236196, 15625),
        "expected_answer": "486/125",
        "plane_label": "P",
        "certificate_category": "ENGINE_DERIVED_SECTION",
        "source_has_H": True,
    },
    # D013 (M5 - anaphoric "Xác định thiết diện của lăng trụ cắt bởi (P) và tính diện tích của nó" + 4-vertex lateral face (BCC'B'),
    # right prism ABC.A'B'C' right-isosceles at B with AB=BC=6, AA'=3, M midpoint of AB, (P) through M parallel to (BCC'B').
    # Section is a rectangle of sides (1/2)*BC = 3 and AA' = 3 -> Area = 9, area_sq = 81)
    "D013": {
        "expected_status": "SERVED",
        "defect_family": "M5",
        "polygon_vertices": 4,
        "area_sq": Fraction(81, 1),
        "expected_answer": "9",
        "plane_label": "P",
        "certificate_category": "ENGINE_DERIVED_SECTION",
        "source_has_H": False,
    },
    # D014 (M5 - anaphoric with named section "Xác định thiết diện MNP và tính diện tích của nó",
    # right prism ABC.A'B'C' right at A with AB=6, AC=8, AA'=5, M midpoint of BB', plane (α) through M parallel to (ABC)
    # cutting AA', CC' at N, P -> Category A DINH_CAT_CANH, area = Area(ABC) = 1/2*6*8 = 24)
    "D014": {
        "expected_status": "SERVED",
        "defect_family": "M5",
        "polygon_vertices": 3,
        "area_sq": Fraction(576, 1),
        "expected_answer": "24",
        "plane_label": "α",
        "certificate_category": "DINH_CAT_CANH",
        "source_has_H": False,
    },
    # D015 (M5 - named triangle area "Tính diện tích tam giác MNP", S.ABC SA⊥(ABC), SA=5, ABC right at A with AB=8, AC=6,
    # M midpoint of SA, plane (α) through M parallel to (ABC) cutting SB, SC at N, P -> Category A DINH_CAT_CANH,
    # area = (1/4)*(1/2*8*6) = 6)
    "D015": {
        "expected_status": "SERVED",
        "defect_family": "M5",
        "polygon_vertices": 3,
        "area_sq": Fraction(36, 1),
        "expected_answer": "6",
        "plane_label": "α",
        "certificate_category": "DINH_CAT_CANH",
        "source_has_H": False,
    },
    # D016 (M2 + M5 - omitted solid on height + named quadrilateral area "Tính diện tích tứ giác AEFK",
    # regular pyramid S.ABCD with base side 6 and height 4, plane (P) through A perpendicular to SC cutting SB, SC, SD at E, F, K)
    # Let's compute exact area of AEFK in D016:
    # Center O=(0,0,0), S=(0,0,4), half-diagonal of square side 6 is OA = OC = 3√2.
    # In plane SAC: A=(-3√2, 0, 0), C=(3√2, 0, 0), S=(0, 0, 4).
    # SC vector from S to C: (3√2, 0, -4), |SC|^2 = 18 + 16 = 34.
    # Plane (P) through A(-3√2, 0, 0) perpendicular to SC(3√2, 0, -4):
    # 3√2 (x + 3√2) - 4z = 0 -> 3√2 x - 4z = -18.
    # On SC: S + t_F(C - S) = (3√2 t_F, 0, 4 - 4 t_F):
    # 18 t_F - 16(1 - t_F) = -18 -> 34 t_F = -2 -> Wait: if side=6 and height=4, angle ASC is obtuse so foot F has t_F = -1/17 < 0!
    # Wait: for F to lie strictly on segment SC (0 < t_F < 1), we need SA^2 > AC^2 - SC^2, i.e. h^2 > OA^2 = s^2 / 2!
    # Let's choose base side = 2 and height = 3 (or base side = 4 and height = 4)!
    # Let's check base side = 2, height = 2:
    # Square side s = 2 -> OA = √2, S = (0, 0, 2), A = (-√2, 0, 0), C = (√2, 0, 0), B = (0, -√2, 0), D = (0, √2, 0).
    # SC = (√2, 0, -2), |SC|^2 = 2 + 4 = 6.
    # Plane (P) through A(-√2, 0, 0) with normal (√2, 0, -2): √2 x - 2z = -2.
    # On SC: S + t_F(C - S) = (√2 t_F, 0, 2 - 2 t_F) -> 2 t_F - 4 + 4 t_F = -2 -> 6 t_F = 2 -> t_F = 1/3 (0 < 1/3 < 1)!
    # F = (√2/3, 0, 4/3). Vector AF = (4√2/3, 0, 4/3), |AF|^2 = 32/9 + 16/9 = 48/9 = 16/3.
    # On SB(0, -√2, 0) and SD(0, √2, 0): S + t_E(B - S) = (0, -√2 t_E, 2 - 2 t_E):
    # 0 - 2(2 - 2 t_E) = -2 -> 4 t_E = 2 -> t_E = 1/2!
    # So E is the midpoint of SB and K is the midpoint of SD!
    # Vector EK = K - E = (1/2)(D - B) = (0, √2, 0), |EK|^2 = 2.
    # Since AC ⊥ BD and SO ⊥ BD, plane (SAC) ⊥ BD, so AF ⊥ EK!
    # Thus quadrilateral AEFK has perpendicular diagonals AF and EK:
    # Area(AEFK) = (1/2) * |AF| * |EK| -> area_sq = (1/4) * |AF|^2 * |EK|^2 = (1/4) * (16/3) * 2 = 8/3 -> 2√6/3!
    "D016": {
        "expected_status": "SERVED",
        "defect_family": "M5",
        "polygon_vertices": 4,
        "area_sq": Fraction(8, 3),
        "expected_answer": "2√6/3",
        "plane_label": "P",
        "certificate_category": "DINH_CAT_CANH",
        "source_has_H": False,
    },
}
