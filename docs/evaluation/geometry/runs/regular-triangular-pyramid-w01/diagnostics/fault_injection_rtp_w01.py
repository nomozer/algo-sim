# -*- coding: utf-8 -*-
"""Tiêm lỗi cho lát cắt backend regular-triangular-pyramid-w01 — mỗi phép tiêm phải làm ĐỎ đúng ca nhãn nó gác.
Chạy từ `backend/`: `python ../docs/evaluation/geometry/runs/regular-triangular-pyramid-w01/diagnostics/fault_injection_rtp_w01.py`.
0 lượt gọi model; vá trong tiến trình (monkeypatch), không sửa tệp nào.
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from app.simulation.semantic_program import assumption_gate as AG  # noqa: E402
from app.simulation.semantic_program import construction_binding as CB  # noqa: E402
from app.simulation.semantic_program import segment_relation as SR  # noqa: E402
from app.simulation.semantic_program import shape_constraint as SC  # noqa: E402
from tests.geometry import test_regular_triangular_pyramid as T  # noqa: E402


@contextmanager
def va(mod, ten, gia_tri):
    cu = getattr(mod, ten)
    setattr(mod, ten, gia_tri)
    try:
        yield
    finally:
        setattr(mod, ten, cu)


def khop(ca: str) -> bool:
    try:
        T._khop(ca, T.ket_qua(ca))
        return True
    except AssertionError:
        return False


def ly_do_dinh_tren_trong_tam(_ca: str) -> bool:
    """Gác của ràng buộc: lý do từ chối nêu đúng nó (route vẫn từ chối nhờ đối chiếu chính tắc khi bỏ ràng buộc)."""
    try:
        T.test_dinh_lech_phap_tuyen_bi_chan_boi_rang_buoc_dinh_tren_trong_tam()
        return khop("N5b_apex_off_normal")
    except AssertionError:
        return False


def ly_do_ngoai_mien(ca: str) -> bool:
    """Gác của luật miền: `test_ngoai_mien_bieu_dien_tu_choi_dung_ly_do` (lý do TEMPLATE_NOT_REPRESENTABLE T8)."""
    try:
        T.test_ngoai_mien_bieu_dien_tu_choi_dung_ly_do(ca)
        return True
    except AssertionError:
        return False


def bo_rang_buoc(ten_rang_buoc: str):
    goc = AG._khuon_chop_tam_giac_deu

    def moi(*a, **k):
        kq = goc(*a, **k)
        if isinstance(kq, AG._Khuon):
            kq.rang_buoc = [(n, f) for n, f in kq.rang_buoc if n != ten_rang_buoc]
        return kq
    return moi


#: (tên, phép tiêm, ca gác, phép kiểm). Lượt chạy đầu (3/6) cho thấy ba gác nói dối: N5 bị chặn bởi ràng buộc chiều
#: cao chứ không bởi "đỉnh trên trọng tâm" (thêm N5b); N6 lệch dù không nhận trung tuyến (gác thật là P9 MATCHED);
#: U4 trượt ràng buộc cạnh trước luật miền (đổi sang tam giác hữu tỉ cạnh² 14; gác lý do là test lý do ngoài miền).
TIEM = [
    ("FL1 T8 never matches", lambda: va(AG, "la_chop_tam_giac_deu", lambda *a, **k: False), "P1_side_height", khop),
    ("FL2 no apex-above-centroid constraint", lambda: va(AG, "_khuon_chop_tam_giac_deu",
                                                         bo_rang_buoc("apex above the centroid")),
     "N5b_apex_off_normal", ly_do_dinh_tren_trong_tam),
    ("FL3 radical lengths unread", lambda: va(SR, "_phan_do_dai", SR._phan), "P5_equal_chains", khop),
    ("FL4 no centroid by medians", lambda: va(CB, "phep_trong_tam", lambda cau: {}), "P9_named_centroid", khop),
    ("FL5 representability check skipped", lambda: va(AG, "_can_huu_ti", lambda q: AG.Fraction(1)),
     "U4_side_outside_frames", ly_do_ngoai_mien),
    ("FL6 base equilateral derived from three laterals alone", lambda: va(
        SC, "_bang_nhau", lambda do_dai, cap: True), "N8_equal_laterals_base_not_stated", khop),
]


def main() -> int:
    hong = 0
    for ten, tiem, ca, kiem in TIEM:
        truoc = kiem(ca)
        with tiem():
            sau = kiem(ca)
        bat = truoc and not sau
        hong += not bat
        print(f"{'CAUGHT' if bat else 'MISSED'}  {ten}: {ca} before={'pass' if truoc else 'FAIL'} "
              f"injected={'pass' if sau else 'FAIL'}")
    print(f"fault_injection_rtp_w01: {len(TIEM) - hong}/{len(TIEM)} caught")
    return 1 if hong else 0


if __name__ == "__main__":
    sys.exit(main())
