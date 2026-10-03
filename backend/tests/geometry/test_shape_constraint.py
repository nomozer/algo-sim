# -*- coding: utf-8 -*-
"""W15 — bộ đọc ràng buộc HÌNH DẠNG từ đề (`shape_constraint.doc_rang_buoc`). 0 lượt gọi.

Cùng họ với `point_coordinate` / `plane_equation` / `segment_relation`: server đọc CÂU ĐỀ,
phát ràng buộc do server sở hữu, gắn đúng định danh thực thể. Chỉ dùng để XÁC NHẬN tiền
đề của chứng chỉ giả định và để kiểm phản ví dụ — không bao giờ đi vào fact graph.

Từ vựng ĐÓNG (quyết định U1, plan W15): lối viết ngoài từ vựng không phát gì — kết cục là
UNDETERMINED ở cổng (từ chối), không bao giờ là phục vụ sai.

Thứ tự `entities` theo từng kind (khoá ở đây, mô tả ở ASSUMPTION_CERTIFICATE_AMENDMENT):
  pyramid            (đỉnh, *đáy)               `S.ABC…`
  prism              (*đáy, *nắp)               `ABC.A'B'C'` — tương ứng theo VỊ TRÍ
  right_prism · oblique_prism · cuboid · cube   như `prism`, theo danh từ đứng trước
  cube_edge          như `cube`, value = cạnh   `hình lập phương X.Y có cạnh bằng N`
  base_rectangle · base_square · base_parallelogram · base_rhombus   (*đáy)
  right_triangle     (đỉnh góc vuông, hai đỉnh còn lại theo thứ tự đề)
  line_perp_plane    (P, Q, *mặt)               `PQ ⊥ (XYZ)` / `PQ vuông góc với đáy`
  line_perp_line     (P, Q, R, T)               `PQ ⊥ RT` / `góc YXZ = 90°` → (X, Y, X, Z)
  khối KHÔNG TÊN     entities = () — chỉ khi đề nhắc đúng MỘT khối và không ký hiệu khối nào
                     (right_prism, base_square value = cạnh, height value = chiều cao)
"""
from __future__ import annotations

import importlib
from fractions import Fraction

import pytest


def _doc(text: str):
    return importlib.import_module("app.simulation.semantic_program.shape_constraint").doc_rang_buoc(text)


def _bo(text: str) -> set[tuple]:
    return {(r.kind, tuple(r.entities), r.value) for r in _doc(text)}


def _kinds(text: str) -> set[str]:
    return {r.kind for r in _doc(text)}


# ── mỗi luật gắn ĐÚNG thực thể ──────────────────────────────────────────────

@pytest.mark.parametrize("text,ky_vong", [
    ("Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật.",
     {("pyramid", ("S", "A", "B", "C", "D"), None), ("base_rectangle", ("A", "B", "C", "D"), None)}),
    ("Cho khối chóp S.ABC có đáy ABC là tam giác vuông tại A.",
     {("pyramid", ("S", "A", "B", "C"), None), ("right_triangle", ("A", "B", "C"), None)}),
    ("Cho hình lăng trụ ABC.A'B'C'.",
     {("prism", ("A", "B", "C", "A_prime", "B_prime", "C_prime"), None)}),
    ("Cho hình lăng trụ đứng ABC.DEF có đáy ABC là tam giác vuông tại B.",
     {("prism", ("A", "B", "C", "D", "E", "F"), None), ("right_prism", ("A", "B", "C", "D", "E", "F"), None),
      ("right_triangle", ("B", "A", "C"), None)}),
    ("Cho hình lăng trụ xiên ABC.DEF.",
     {("prism", ("A", "B", "C", "D", "E", "F"), None), ("oblique_prism", ("A", "B", "C", "D", "E", "F"), None)}),
    ("Cho hình hộp chữ nhật ABCD.A'B'C'D'.",
     {("prism", ("A", "B", "C", "D", "A_prime", "B_prime", "C_prime", "D_prime"), None),
      ("cuboid", ("A", "B", "C", "D", "A_prime", "B_prime", "C_prime", "D_prime"), None)}),
    ("Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 4.",
     {("prism", ("A", "B", "C", "D", "A_prime", "B_prime", "C_prime", "D_prime"), None),
      ("cube", ("A", "B", "C", "D", "A_prime", "B_prime", "C_prime", "D_prime"), None),
      ("cube_edge", ("A", "B", "C", "D", "A_prime", "B_prime", "C_prime", "D_prime"), Fraction(4))}),
    ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông.",
     {("pyramid", ("S", "A", "B", "C", "D"), None), ("base_square", ("A", "B", "C", "D"), None)}),
    ("Cho hình chóp S.ABCD có đáy ABCD là hình bình hành.",
     {("pyramid", ("S", "A", "B", "C", "D"), None), ("base_parallelogram", ("A", "B", "C", "D"), None)}),
    ("Cho hình chóp S.ABCD có đáy ABCD là hình thoi.",
     {("pyramid", ("S", "A", "B", "C", "D"), None), ("base_rhombus", ("A", "B", "C", "D"), None)}),
])
def test_moi_luat_gan_dung_thuc_the(text, ky_vong):
    assert _bo(text) == ky_vong


@pytest.mark.parametrize("cau,ky_vong", [
    ("SA vuông góc với mặt phẳng (ABC).", ("line_perp_plane", ("S", "A", "A", "B", "C"), None)),
    ("SA vuông góc với (ABC).", ("line_perp_plane", ("S", "A", "A", "B", "C"), None)),
    ("SA ⊥ (ABC).", ("line_perp_plane", ("S", "A", "A", "B", "C"), None)),
    ("AB vuông góc với AD.", ("line_perp_line", ("A", "B", "A", "D"), None)),
    ("AB ⊥ AD.", ("line_perp_line", ("A", "B", "A", "D"), None)),
    ("góc BAD = 90°.", ("line_perp_line", ("A", "B", "A", "D"), None)),
    ("Tam giác ABC vuông tại C.", ("right_triangle", ("C", "A", "B"), None)),
])
def test_quan_he_vuong_goc_gan_dung_thuc_the(cau, ky_vong):
    assert ky_vong in _bo("Cho hình chóp S.ABCD. " + cau)


def test_span_tro_dung_cum_tu_trong_de():
    text = "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A. Cạnh bên SA vuông góc với đáy."
    for r in _doc(text):
        a, b = r.span
        assert 0 <= a < b <= len(text), r
    vg = next(r for r in _doc(text) if r.kind == "line_perp_plane")
    assert "SA vuông góc với đáy" in text[vg.span[0]:vg.span[1]]


# ── sai thực thể với cùng từ ngữ: KHÔNG phát ──────────────────────────────

@pytest.mark.parametrize("text,kind_cam", [
    ("Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại D.", "right_triangle"),
    ("Cho hình chóp S.ABCD có đáy MNPQ là hình chữ nhật.", "base_rectangle"),
    ("Cho hình lăng trụ đứng ABC.DE.", "right_prism"),
    ("Cho hình lăng trụ đứng ABC.DE.", "prism"),
    ("Cạnh SA vuông góc với đáy.", "line_perp_plane"),
])
def test_sai_thuc_the_cung_tu_ngu_khong_phat(text, kind_cam):
    assert kind_cam not in _kinds(text), _bo(text)


# ── "đáy" gắn vào đáy của khối ĐÃ NÊU ───────────────────────────────────────

@pytest.mark.parametrize("text,mat", [
    ("Cho hình chóp S.ABC. Cạnh bên SA vuông góc với đáy.", ("A", "B", "C")),
    ("Cho hình chóp S.ABCD. Cạnh bên SA vuông góc với mặt phẳng đáy.", ("A", "B", "C", "D")),
    ("Cho hình lăng trụ ABC.DEF. Cạnh bên AD vuông góc với đáy.", ("A", "B", "C")),
])
def test_day_gan_vao_day_cua_khoi_da_neu(text, mat):
    vg = [r for r in _doc(text) if r.kind == "line_perp_plane"]
    assert len(vg) == 1, vg
    assert tuple(vg[0].entities[2:]) == mat


def test_day_khong_gan_khi_de_neu_hai_khoi():
    text = "Cho hình chóp S.ABC và hình chóp T.MNP. Cạnh bên SA vuông góc với đáy."
    assert "line_perp_plane" not in _kinds(text)


def test_day_khong_ten_gan_vao_khoi_da_neu():
    text = "Cho hình chóp S.ABC có đáy là tam giác vuông tại A."
    assert ("right_triangle", ("A", "B", "C"), None) in _bo(text)


# ── khối KHÔNG TÊN: chỉ gắn khi duy nhất ───────────────────────────────────

def test_khoi_khong_ten_duy_nhat_duoc_gan():
    text = "Cho hình lăng trụ đứng có đáy là hình vuông cạnh 3, chiều cao bằng 7."
    assert _bo(text) == {("right_prism", (), None), ("base_square", (), Fraction(3)),
                         ("height", (), Fraction(7))}


def test_khoi_khong_ten_khong_duy_nhat_khong_gan():
    text = ("Cho hình lăng trụ đứng có đáy là hình vuông cạnh 3, chiều cao bằng 7 và một hình chóp "
            "có cùng đáy.")
    assert not {"right_prism", "base_square", "height"} & _kinds(text), _bo(text)


def test_khoi_khong_ten_khong_gan_khi_co_khoi_co_ten():
    text = "Cho hình lăng trụ đứng ABC.DEF và một hình lăng trụ đứng có chiều cao bằng 7."
    assert ("height", (), Fraction(7)) not in _bo(text)


# ── lối viết NGOÀI từ vựng: không phát gì ──────────────────────────────────

@pytest.mark.parametrize("text,kind_cam", [
    ("Cho hình chóp S.ABC, SA là đường cao của hình chóp.", "line_perp_plane"),
    ("Cho hình chóp S.ABCD có AB và AD tạo với nhau một góc vuông.", "line_perp_line"),
    ("Cho hình chóp S.ABCD có đáy ABCD có bốn góc vuông.", "base_rectangle"),
    ("Cho hình lăng trụ có cạnh bên vuông góc với đáy.", "line_perp_plane"),
    ("Cho hình lăng trụ ABC.DEF có các cạnh bên vuông góc với mặt đáy.", "right_prism"),
])
def test_dien_dat_ngoai_tu_vung_khong_phat(text, kind_cam):
    assert kind_cam not in _kinds(text), _bo(text)


def test_de_rong_khong_phat():
    assert _doc("") == ()


# ── phần dữ kiện CHƯA ĐỌC TRỌN (§7, đính chính Task 6) ──────────────────────
#
# DEPENDENT nói "đề không cho kích thước này" — chỉ nói được khi bộ đọc đã đọc TRỌN phần
# dữ kiện: một câu ngoài từ vựng (góc, `SA = AB`, độ dài có căn…) có thể chính là câu cho
# kích thước ấy. `phan_chua_doc` trả các mảnh không bộ đọc nào đọc trọn; rỗng = đọc trọn.

def _chua_doc(text: str) -> tuple[str, ...]:
    return importlib.import_module("app.simulation.semantic_program.shape_constraint").phan_chua_doc(text)


CHOP_KHONG_SA = ("Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4. "
                 "Cạnh bên SA vuông góc với đáy. Tính thể tích khối chóp S.ABC.")


@pytest.mark.parametrize("text", [
    CHOP_KHONG_SA,
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3. Cạnh bên SA vuông góc với mặt phẳng đáy. "
    "Tính thể tích khối chóp S.ABCD.",
    "Cho hình lăng trụ đứng có đáy là hình vuông cạnh 3. Tính thể tích khối lăng trụ đứng đó.",
])
def test_phan_chua_doc_rong_khi_moi_cau_duoc_doc(text):
    """Mọi mảnh nằm trong span của bộ đọc hoặc là một độ dài số đọc được; còn lại chỉ từ
    nối không mang số đo. Phần câu hỏi (từ `Tính`) không tính."""
    assert _chua_doc(text) == ()


@pytest.mark.parametrize("cau", [
    "Góc giữa SB và mặt phẳng đáy bằng 45°",
    "SA = AB",
    "Tam giác SAB vuông cân tại A",
    "SB = 3√2",
    "Thể tích khối chóp bằng 6",
    "Chiều cao gấp đôi cạnh đáy",
])
def test_cau_ngoai_tu_vung_de_lai_phan_chua_doc(cau):
    text = CHOP_KHONG_SA.replace("vuông góc với đáy.", f"vuông góc với đáy. {cau}.")
    assert _chua_doc(text) != (), text


@pytest.mark.parametrize("text", [
    # "cân": bộ đọc chỉ phát right_triangle, bỏ AB = AC
    "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại A, AB = 3. Cạnh bên SA vuông góc với đáy. "
    "Tính thể tích khối chóp S.ABC.",
    # "đều": danh từ khối được đọc, tính đều bị bỏ
    "Cho hình lăng trụ đứng tam giác đều ABC.DEF có AB = 3. Tính thể tích khối lăng trụ ABC.DEF.",
    # cạnh của đáy KHÔNG vuông: span nuốt "cạnh 3" nhưng không phát giá trị
    "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật cạnh 3. Cạnh bên SA vuông góc với đáy, SA = 4. "
    "Tính thể tích khối chóp S.ABCD.",
])
def test_thong_tin_bi_bo_trong_span_tinh_la_chua_doc(text):
    assert _chua_doc(text) != (), text


# ── vùng khối ĐA DIỆN (quyết định U3): route chỉ từ chối theo cổng giả định trong vùng này ──

def _da_dien(text: str) -> bool:
    return importlib.import_module("app.simulation.semantic_program.shape_constraint").neu_khoi_da_dien(text)


@pytest.mark.parametrize("text", [
    "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A. Tính thể tích khối chóp S.ABC.",
    "Cho hình lăng trụ ABC.A'B'C' có đáy là tam giác đều. Tính thể tích.",
    "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 4. Tính thể tích.",
    "Cho hình lăng trụ đứng có đáy là hình vuông cạnh 3, chiều cao 7. Tính thể tích.",
    "Trong không gian Oxyz, cho hình chóp S.ABCD với A(0;0;0), B(6;0;0). Tính thể tích.",
])
def test_vung_da_dien_theo_tu_vung_dong(text):
    assert _da_dien(text), text


@pytest.mark.parametrize("text", [
    "Cho đoạn thẳng EF có độ dài 10. Điểm P nằm trên đoạn EF sao cho FP = 4·PE. Tính độ dài PF.",
    "Hình nón có đỉnh P và tâm đáy Q, bán kính đáy bằng 21, chiều cao PQ bằng 28. Tính bán kính.",
    "Cho tứ diện ABCD có AB, AC, AD đôi một vuông góc. Tính thể tích.",
    "Trong không gian Oxyz, cho ba điểm M(1;0;2), N(4;0;2), P(5;2;4). Tính diện tích tam giác MNP.",
    "",
])
def test_ngoai_vung_da_dien(text):
    assert not _da_dien(text), text


# ── góc vuông của đáy: các lối viết thường gặp (quyết định U4 · G1) ──────────

@pytest.mark.parametrize("text,ky_vong", [
    ("Cho hình chóp S.ABC có đáy ABC vuông tại A, AB = 3.", ("A", "B", "C")),
    ("Cho hình chóp H.UVW có đáy UVW vuông tại U, UV = 2.", ("U", "V", "W")),
    ("Cho hình chóp F.GKL có đáy GKL là tam giác vuông đỉnh G.", ("G", "K", "L")),
    ("Hình chóp D.EFG có đáy EFG là tam giác vuông ở đỉnh E.", ("E", "F", "G")),
    ("Cho hình chóp S.ABC có tam giác ABC vuông ở B.", ("B", "A", "C")),
    ("Cho hình chóp S.ABC có đáy ABC vuông cân tại C.", ("C", "A", "B")),
])
def test_goc_vuong_cua_day_moi_loi_viet_gan_dung_dinh(text, ky_vong):
    assert ("right_triangle", ky_vong, None) in _bo(text), _bo(text)


@pytest.mark.parametrize("text", [
    "Cho hình chóp S.ABC có đáy ABC vuông tại D.",           # D không thuộc tam giác
    "Cho hình chóp S.ABCD có đáy ABCD vuông tại A.",         # đáy tứ giác: "vuông tại" vô nghĩa
])
def test_goc_vuong_sai_thuc_the_khong_phat(text):
    assert "right_triangle" not in _kinds(text), _bo(text)


def test_loi_viet_moi_duoc_doc_tron():
    assert _chua_doc("Cho hình chóp S.ABC có đáy ABC vuông tại A, AB = 3, AC = 4. Cạnh bên SA vuông góc "
                     "với đáy. Tính thể tích khối chóp S.ABC.") == ()


# ══ W16 · §14.2 · span MỤC TIÊU — quan hệ phải chứng minh không bao giờ là tiền đề ═══════

def _sc():
    return importlib.import_module("app.simulation.semantic_program.shape_constraint")


@pytest.mark.parametrize("text,manh", [
    ("Cho hình chóp S.ABC có SA = 5. Chứng minh rằng SA vuông góc với đáy. Tính thể tích.",
     ["Chứng minh rằng SA vuông góc với đáy"]),
    ("Cho hình chóp S.ABC. CMR: SA ⊥ (ABC). Tính thể tích.", ["CMR: SA ⊥ (ABC)"]),
    ("Biết SA ⊥ (ABC), chứng minh rằng tam giác ABC vuông tại A.", ["chứng minh rằng tam giác ABC vuông tại A"]),
    ("Cho hình chóp S.ABC có SA = 5. SA ⊥ (ABC) hay không? Tính thể tích.", ["SA ⊥ (ABC) hay không"]),
    ("Cho hình chóp S.ABC có SA ⊥ (ABC), SA có vuông góc với BC không?", ["SA có vuông góc với BC không"]),
    ("Hãy kiểm tra xem SA có vuông góc với BC không.", ["kiểm tra xem SA có vuông góc với BC không"]),
    ("Hỏi SA có vuông góc với đáy không? Tính thể tích.", ["Hỏi SA có vuông góc với đáy không"]),
    ("Chứng tỏ rằng S.ABC là hình chóp đều; tính thể tích.", ["Chứng tỏ rằng S.ABC là hình chóp đều"]),
])
def test_w16_khoang_muc_tieu(text, manh):
    assert [text[a:b] for a, b in _sc().khoang_muc_tieu(text)] == manh


@pytest.mark.parametrize("text", [
    "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A. Tính thể tích khối chóp S.ABC.",
    "Tính thể tích khối chóp S.ABC, biết SA vuông góc với đáy và SA = 5.",     # `Tính` không là mục tiêu
    "Lấy điểm M thuộc SA sao cho M không rời khỏi cạnh SA.",                  # `hỏi` nằm TRONG `khỏi`
    "",
])
def test_w16_khong_co_muc_tieu(text):
    assert _sc().khoang_muc_tieu(text) == ()


def test_w16_che_muc_tieu_giu_do_dai_va_giu_gia_thiet_dung_truoc():
    """Câu ghép: giả thiết đứng TRƯỚC yêu cầu vẫn đọc được; quan hệ phải chứng minh thì không."""
    text = ("Cho hình chóp S.ABC có AB = 3, AC = 4, SA = 5. Biết SA vuông góc với đáy, chứng minh rằng tam "
            "giác ABC vuông tại A. Tính thể tích khối chóp S.ABC.")
    che = _sc().che_muc_tieu(text)
    assert len(che) == len(text)
    kinds = {r.kind for r in _doc(che)}
    assert "line_perp_plane" in kinds and "right_triangle" not in kinds, kinds
    assert "right_triangle" in _kinds(text)          # bộ đọc trên đề GỐC vẫn thấy nó (dùng để chặn CE)
