import sys, os, json
sys.path.insert(0, os.getcwd())
from app.ai.local_geometry_parser import parse_geometry_problem_locally as P
cases = [
    "Cho tứ diện NPRV. Các cạnh NP, NR, NV đôi một vuông góc. Độ dài NP = 5, NR = 8, NV = 12. Tính thể tích khối tứ diện NPRV.",
    "Cho tứ diện NPRV. Các cạnh NP, NR, NV đôi một vuông góc. NP = 5, NR = 8, NV = 12. Tính thể tích khối tứ diện NPRV.",
    "Cho tứ diện NPRV có NP, NR, NV đôi một vuông góc, NP = 5, NR = 8, NV = 12. Tính thể tích khối tứ diện NPRV.",
    "Cho hình chóp E.KLMN với đáy KLMN là hình vuông. Độ dài KL = 7. Cạnh bên EK vuông góc với (KLMN) và EK = 9. Tính thể tích khối chóp E.KLMN.",
    "Cho hình chóp E.KLMN với đáy KLMN là hình vuông. KL = 7. Cạnh bên EK vuông góc với (KLMN) và EK = 9. Tính thể tích khối chóp E.KLMN.",
    "Cho tứ diện DEGK có DE, DG, DK vuông góc với nhau từng đôi một và DE = 5, DG = 6, DK = 11. Vẽ hình.",
    "Cho tứ diện DEGK có DE, DG, DK đôi một vuông góc và DE = 5, DG = 6, DK = 11. Vẽ hình.",
    "Tứ diện EFHL có ba cạnh EF, EH, EL đôi một vuông góc, EF = 4, EH = 9, EL = 10. Tính thể tích khối tứ diện EFHL.",
]
for t in cases:
    p = P(t, use_cache=False)
    print(p.status, p.reason_code, "|", t)
    if p.status != "LOCAL_PARSE_COMPLETE":
        for cl in p.source_coverage.clauses:
            if cl.get("role") not in ("fact", "goal", "benign") or not cl.get("mapped", True):
                print("     ", json.dumps(cl, ensure_ascii=False)[:300])
