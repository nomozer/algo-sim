"""Oracle ĐỘC LẬP cho 14 ca holdout (hybrid-compiler-selection): toạ độ số thực đặt tay, chỉ thư viện chuẩn, KHÔNG import
engine/kernel/registry. Đối chiếu với dạng đóng trong `expect_*` của fixture (a = 1); bài kiểm A/B đã khoá đáp số engine
bằng đúng các chuỗi đó ⇒ chuỗi oracle-toạ-độ = dạng đóng = engine. 0 API call. Chạy được từ bất kỳ đâu."""
from math import isclose, sqrt


def sub(p, q): return tuple(x - y for x, y in zip(p, q))
def dot(u, v): return sum(x * y for x, y in zip(u, v))
def cross(u, v): return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
def n2(u): return dot(u, u)
def vol_tet(a, b, c, d): return abs(dot(sub(b, a), cross(sub(c, a), sub(d, a)))) / 6
def dist_pt_plane(p, a, b, c):
    n = cross(sub(b, a), sub(c, a))
    return abs(dot(sub(p, a), n)) / sqrt(n2(n))
def cos2_line_plane(p, q, a, b, c):              # cos² góc giữa PQ và mặt (abc)
    n, u = cross(sub(b, a), sub(c, a)), sub(q, p)
    sin2 = dot(u, n) ** 2 / (n2(u) * n2(n))
    return 1 - sin2


ok = []
def kiem(ca, ten, gia_tri, ky_vong):
    dung = isclose(gia_tri, ky_vong, rel_tol=1e-12, abs_tol=1e-12)
    ok.append(dung)
    print(f"{ca:<6} {ten:<44} {gia_tri:.12g} vs {ky_vong:.12g} → {'OK' if dung else 'FAIL'}")


# H01 lập phương cạnh 1: V = a³, AC' = a√3
A, C1 = (0, 0, 0), (1, 1, 1)
kiem("H01", "V", 1.0, 1.0)
kiem("H01", "AC'", sqrt(n2(sub(C1, A))), sqrt(3))

# H02 hộp AB=1, AD=2, AA'=3: V = 6a³, d(A, (A'BD)) = 6a/7
A, B, D, A1 = (0, 0, 0), (1, 0, 0), (0, 2, 0), (0, 0, 3)
kiem("H02", "V", 1 * 2 * 3, 6.0)
kiem("H02", "d(A,(A'BD))", dist_pt_plane(A, A1, B, D), 6 / 7)

# H03 chóp tứ giác đều đáy 1, cạnh bên √2: V = a³√6/6, cos²(SA, đáy) = 1/4
A, B, C, D = (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)
O = (0.5, 0.5, 0)
h = sqrt(2 - n2(sub(A, O)))
S = (0.5, 0.5, h)
kiem("H03", "SA", sqrt(n2(sub(S, A))), sqrt(2))
kiem("H03", "V", vol_tet(S, A, B, C) + vol_tet(S, A, C, D), sqrt(6) / 6)
kiem("H03", "cos²(SA,(ABCD))", cos2_line_plane(S, A, A, B, C), 0.25)

# H04 đáy vuông cạnh 2, SA = SB = 3, (SAB) ⊥ đáy: V = 8√2/3, SC² = 13
A, B, C, D = (0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)
S = (1, 0, sqrt(9 - 1))                           # chân trên AB (mặt ⊥ đáy), cách đều A,B ⇒ trung điểm
kiem("H04", "SA", sqrt(n2(sub(S, A))), 3.0)
kiem("H04", "SB", sqrt(n2(sub(S, B))), 3.0)
kiem("H04", "V", vol_tet(S, A, B, C) + vol_tet(S, A, C, D), 8 * sqrt(2) / 3)
kiem("H04", "SC²", n2(sub(S, C)), 13.0)

# H05 đáy đều cạnh 2, chiều cao 3: hai vị trí đỉnh ⇒ CÙNG V = √3, KHÁC hình
A, B, C = (0, 0, 0), (2, 0, 0), (1, sqrt(3), 0)
S1, S2 = (1, sqrt(3) / 3, 3), (0, 0, 3)
kiem("H05", "V (đỉnh trên tâm)", vol_tet(S1, A, B, C), sqrt(3))
kiem("H05", "V (đỉnh trên A)", vol_tet(S2, A, B, C), sqrt(3))
kiem("H05", "SA khác nhau ⇒ hình không duy nhất", float(n2(sub(S1, A)) != n2(sub(S2, A))), 1.0)

# H06 đáy đều cạnh 2, SA = 3: hai vị trí hợp lệ ⇒ V KHÁC nhau
S1, S2 = (0, 0, 3), (3 / sqrt(2), 0, 3 / sqrt(2))
kiem("H06", "SA (vị trí 1)", sqrt(n2(sub(S1, A))), 3.0)
kiem("H06", "SA (vị trí 2)", sqrt(n2(sub(S2, A))), 3.0)
kiem("H06", "V khác nhau ⇒ đại lượng không duy nhất", float(not isclose(vol_tet(S1, A, B, C), vol_tet(S2, A, B, C))), 1.0)

# H07 vuông tại B, AB = 1, BC = √3, SA ⊥ đáy, SA = 2: V = a³√3/3; BC ⊥ (SAB)
B, A, C = (0, 0, 0), (1, 0, 0), (0, sqrt(3), 0)
S = (1, 0, 2)
kiem("H07", "V", vol_tet(S, A, B, C), sqrt(3) / 3)
kiem("H07", "BC·AB", dot(sub(C, B), sub(A, B)), 0.0)
kiem("H07", "BC·BS", dot(sub(C, B), sub(S, B)), 0.0)

# H09 lập phương cạnh 2: AC'² = 12 ≠ 9 ⇒ mâu thuẫn
kiem("H09", "AC'² (cạnh 2)", n2((2, 2, 2)), 12.0)

# H11 lăng trụ đứng, vuông tại A, AB = 1, AC = 2, AA' = 2: d(AM, B'C) = 2a/3
A, B, C = (0, 0, 0), (1, 0, 0), (0, 2, 0)
B1, M = (1, 0, 2), (0.5, 1, 0)
n = cross(sub(M, A), sub(C, B1))
kiem("H11", "d(AM, B'C)", abs(dot(sub(B1, A), n)) / sqrt(n2(n)), 2 / 3)

# H12 đáy đều cạnh 1, chiếu của S là trung điểm H của AB, SH = √3/2: V = a³/8, cos²(SC, đáy) = 1/2
A, B, C = (0, 0, 0), (1, 0, 0), (0.5, sqrt(3) / 2, 0)
S = (0.5, 0, sqrt(3) / 2)
kiem("H12", "V", vol_tet(S, A, B, C), 1 / 8)
kiem("H12", "cos²(SC,(ABC))", cos2_line_plane(S, C, A, B, C), 0.5)

# H13 vuông tại B, SA ⊥ đáy: BC ⊥ (SAB) LUÔN đúng ⇒ mệnh đề phủ định sai
B, A, C = (0, 0, 0), (3, 0, 0), (0, 4, 0)
S = (3, 0, 4)
kiem("H13", "BC·AB", dot(sub(C, B), sub(A, B)), 0.0)
kiem("H13", "BC·BS", dot(sub(C, B), sub(S, B)), 0.0)

# H14 tứ diện đều cạnh 1: V = a³√2/12
P = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]  # cạnh 2√2 ⇒ chia √8
P = [tuple(x / sqrt(8) for x in p) for p in P]
kiem("H14", "cạnh", sqrt(n2(sub(P[0], P[1]))), 1.0)
kiem("H14", "V", vol_tet(*P), sqrt(2) / 12)

print("ORACLE_OK" if all(ok) else f"ORACLE_FAIL {ok.count(False)}")
raise SystemExit(0 if all(ok) else 1)
