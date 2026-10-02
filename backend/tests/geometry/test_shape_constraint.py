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
