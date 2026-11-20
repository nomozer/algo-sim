from __future__ import annotations

from app.simulation.semantic_program.domain_profile import (
    DOMAIN_HINH_HOC,
    DOMAIN_NGOAI_PHAM_VI,
    detect_domain,
)


def test_diacritic_free_valid_geometry_prompts_route_to_hinh_hoc():
    in_domain = [
        "Mo phong hinh lap phuong ABCD.A'B'C'D' canh 2.",
        "Hay dung hinh chop S.ABC co day ABC la tam giac deu canh a, SA vuong goc voi day, SA = 2a.",
        "Hinh chop S.ABCD co day ABCD la hinh vuong canh 2, SA vuong goc voi day, SA = 3. Tinh the tich khoi chop.",
        "Cho lang tru dung ABC.A'B'C' co day la tam giac vuong tai A, AB = 3, AC = 4, AA' = 5. Tinh the tich.",
        "Dung tu dien deu EFGH co tat ca cac canh bang 3.",
    ]
    for txt in in_domain:
        assert detect_domain(txt) == DOMAIN_HINH_HOC, txt


def test_diacritic_free_out_of_domain_and_bare_word_decoys_remain_tin_hoc():
    out_of_domain_decoys = [
        "hinh",
        "canh",
        "goc",
        "hinh anh canh dep va goc chup toi uu",
        "Cho mang hinh chu nhat kich thuoc 3x4, tim duong di ngan nhat qua cac o.",
        "Tim canh nho nhat trong do thi co huong 5 dinh bang thuat toan Kruskal.",
        "Tinh goc quay con lac lo xo co bien do 4cm sau 2 giay.",
        "Viet chuong trinh python tinh the tich hinh chop S.ABCD bang cong thuc.",
        "Giai phuong trinh bac hai x^2 - 5x + 6 = 0 va tim nghiem.",
        "Calculate bounding box area and edge length in CSS layout.",
        "Toi muon xem hinh minh hoa mot con meo.",
    ]
    for txt in out_of_domain_decoys:
        assert detect_domain(txt) == DOMAIN_NGOAI_PHAM_VI, f"False positive on decoy: {txt}"
