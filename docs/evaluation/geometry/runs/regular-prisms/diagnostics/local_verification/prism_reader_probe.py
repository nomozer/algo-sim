"""LOCAL: reader claims + unread spans for phrasings around the T12 slice (xiên/đứng, tứ giác đều pin, no "hình",
negation, goal clause, pyramid "đáy là lục giác đều"). Run from backend/ on each tree; 0 model calls."""
import json, os, sys
sys.path.insert(0, os.getcwd())
from app.simulation.semantic_program.shape_constraint import doc_rang_buoc, phan_chua_doc

CAU = {
    "square_prism_pin": "Cho hình lăng trụ đứng tứ giác đều ABCD.EFGH có AB = 3. Tính thể tích khối lăng trụ ABCD.EFGH.",
    "square_prism_regular": "Cho hình lăng trụ tứ giác đều ABCD.A'B'C'D' có cạnh đáy bằng 2, chiều cao bằng 3. Tính thể tích khối lăng trụ ABCD.A'B'C'D'.",
    "oblique_tri_regular_noun": "Cho hình lăng trụ xiên tam giác đều ABC.DEF có AB = 3. Tính thể tích khối lăng trụ ABC.DEF.",
    "oblique_hex_regular_noun": "Cho hình lăng trụ xiên lục giác đều ABCDEF.A'B'C'D'E'F' có cạnh đáy bằng 2, cạnh bên bằng 3. Tính thể tích khối lăng trụ ABCDEF.A'B'C'D'E'F'.",
    "oblique_equilateral_base": "Cho hình lăng trụ xiên ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2, cạnh bên bằng 3. Tính thể tích khối lăng trụ ABC.A'B'C'.",
    "right_tri_regular_noun": "Cho hình lăng trụ đứng tam giác đều ABC.A'B'C' có cạnh đáy bằng 2, chiều cao bằng 3. Tính thể tích khối lăng trụ ABC.A'B'C'.",
    "right_hex_regular_noun": "Cho hình lăng trụ đứng lục giác đều ABCDEF.A'B'C'D'E'F' có cạnh đáy bằng 2, chiều cao bằng 3. Tính thể tích khối lăng trụ ABCDEF.A'B'C'D'E'F'.",
    "no_hinh_tri": "Cho lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng 2, chiều cao bằng 3. Tính thể tích khối lăng trụ ABC.A'B'C'.",
    "plain_prism_equilateral_base": "Cho hình lăng trụ ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2, chiều cao bằng 3. Tính thể tích khối lăng trụ ABC.A'B'C'.",
    "wrong_vertex_count_tri": "Cho hình lăng trụ tam giác đều ABCD.A'B'C'D' có cạnh đáy bằng 2, chiều cao bằng 3. Tính thể tích khối lăng trụ ABCD.A'B'C'D'.",
    "negation_after": "Cho hình lăng trụ ABC.A'B'C' có cạnh đáy bằng 2, chiều cao bằng 3, lăng trụ này không phải lăng trụ tam giác đều. Tính thể tích khối lăng trụ ABC.A'B'C'.",
    "goal_clause_tri": "Cho hình lăng trụ ABC.A'B'C' có chiều cao bằng 3. Chứng minh ABC.A'B'C' là hình lăng trụ tam giác đều. Tính thể tích khối lăng trụ ABC.A'B'C'.",
    "pyramid_hex_base": "Cho hình chóp S.ABCDEF có đáy là lục giác đều cạnh 2, SA vuông góc với đáy, SA = 3. Tính thể tích khối chóp S.ABCDEF.",
}
for k, de in CAU.items():
    rb = doc_rang_buoc(de)
    print(json.dumps({"case": k, "claims": sorted({(r.kind, "".join(r.entities), str(r.value)) for r in rb}),
                      "unread": list(phan_chua_doc(de))}, ensure_ascii=False))
