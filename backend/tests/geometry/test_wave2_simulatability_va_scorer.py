# -*- coding: utf-8 -*-
"""WAVE 2 — cổng phạm vi có HAI vế, và bộ chấm mệnh đề phải hỏi checker.

Canary V2 (2026-08-29, live) để lộ hai lỗi mà test tất định của wave 1 không
bắt được, vì chúng dừng ở `detect_domain`:

① Bài A10 (góc đường–mặt) chết ở **vế thứ hai** của cổng phạm vi,
   `GATE_NOT_SIMULATION_SUITABLE`. Wave 1 chỉ miễn vế `domain_scope`.
   Cùng một bệnh: `REQUIRES_SIMULATION` = {INTERACTIVE_MODEL,
   INTERACTIVE_ARTIFACT, MEANINGFUL_TRACE} — không nhãn nào cho một bài hình
   học tĩnh, nên phán quyết của mô hình KHÔNG mang thông tin. Chỉ lộ ở A10
   chứ không ở A09: cùng dạng đề, mô hình khai hai nhãn khác nhau.

② Bộ chấm DEV tìm một giá trị `True` trong `final_memory` cho nghĩa vụ MỆNH
   ĐỀ. Sai hợp đồng: mệnh đề được chứng minh bằng **checker phía server**,
   quy ước `None` ⇒ thoả, và `final_memory` chỉ chứa `Vec3`/`Line3`/`Plane3`.
   Bài `w1-phay` bị chấm sai trong khi nó đã `served` với
   `verification_match = True` — lỗi của bộ đo, nghiêng đúng chiều nguy hiểm.

─── LUẬT MIỄN LÀ LUẬT DƯƠNG ──────────────────────────────────────────────

Không miễn theo *"là hình học ⇒ luôn mô phỏng được"*. Luật âm ấy miễn dựa
trên việc bài KHÔNG thuộc môn khác, nên nó thả đề ngoài năng lực đi sâu vào
tầng sinh rồi hỏng ở một cổng khó đọc hơn nhiều.

`co_duong_thuc_thi` đòi **bằng chứng dương**: đề ánh xạ được tới một nghĩa vụ
CÓ CHECKER thật. Khoá bảng manh mối dẫn từ `GEOMETRY_CHECKERS`, nên thêm một
manh mối cho nghĩa vụ không có checker là mở năng lực — và test dưới bắt.
"""
from __future__ import annotations

import pytest

from app.simulation.error_codes import ErrorCode
from app.simulation.semantic_program.domain_profile import (
    DOMAIN_HINH_HOC,
    DOMAIN_TIN_HOC,
    _MANH_MOI_NGHIA_VU,
    co_duong_thuc_thi,
    detect_domain,
    nghia_vu_ung_vien,
)
from app.simulation.semantic_program.geometry_obligations import (
    GEOMETRY_CHECKERS,
)

#: Đề DEV có năng lực — phải qua CẢ HAI vế cổng.
CO_NANG_LUC = (
    ("Cho hình lập phương ABCD.A'B'C'D' cạnh 2. Tính góc giữa hai đường thẳng "
     "AC và B'C'.", "angle"),
    ("Cho hình lập phương ABCD.A'B'C'D' cạnh 2. Tính góc giữa đường thẳng AC' "
     "và mặt phẳng (ABCD).", "angle"),
    ("Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2, SA vuông góc với đáy "
     "và SA = 2. Chứng minh BD vuông góc với SC.", "perpendicular"),
    ("Cho tứ diện ABCD. Gọi M, N là trung điểm AB, CD. Chứng minh MN song "
     "song với mặt phẳng (ACD).", "parallel"),
    ("Cho hình chóp S.ABC có SA vuông góc với đáy, SA = 3. Tính khoảng cách "
     "từ S đến mặt phẳng (ABC).", "distance"),
    ("Cho hình chóp S.ABC có đáy vuông tại A, AB = 3, AC = 4, SA = 2 và SA "
     "vuông góc với đáy. Tính thể tích khối chóp.", "volume"),
)

#: Đề Tin học mượn từ vựng hình học — KHÔNG được kéo sang hình học.
TIN_HOC = (
    "Viết chương trình tính thể tích hình chóp tam giác đều.",
    "Viết chương trình nhập vào toạ độ các đỉnh của một hình lập phương và "
    "tính khoảng cách giữa hai đỉnh xa nhau nhất.",
    "Cho mảng các điểm, viết thuật toán đếm số cặp vuông góc với gốc toạ độ.",
)


@pytest.mark.parametrize("de,kind", CO_NANG_LUC)
def test_de_CO_NANG_LUC_qua_ca_HAI_ve_cong(de, kind):
    assert detect_domain(de) == DOMAIN_HINH_HOC, de
    assert kind in nghia_vu_ung_vien(de), de
    assert co_duong_thuc_thi(de, DOMAIN_HINH_HOC), de
    # Cả hai mã lỗi của cổng đều phải được miễn.
    for ma in (ErrorCode.GATE_OUT_OF_SCOPE,
               ErrorCode.GATE_NOT_SIMULATION_SUITABLE):
        mien = (detect_domain(de) == DOMAIN_HINH_HOC
                and ma in (ErrorCode.GATE_OUT_OF_SCOPE,
                           ErrorCode.GATE_NOT_SIMULATION_SUITABLE)
                and co_duong_thuc_thi(de, DOMAIN_HINH_HOC))
        assert mien, f"{ma.value} vẫn phủ quyết: {de}"


@pytest.mark.parametrize("de", TIN_HOC)
def test_de_TIN_HOC_KHONG_bi_keo_sang_hinh_hoc(de):
    """Phủ quyết Tin học đứng trước danh từ khối — bảo vệ ở tầng miền, nên
    `co_duong_thuc_thi` không bao giờ được gọi tới cho nhóm này."""
    assert detect_domain(de) == DOMAIN_TIN_HOC, de
    assert not co_duong_thuc_thi(de, detect_domain(de)), de


#: Đề HÌNH HỌC nhưng NGOÀI năng lực — phải fail-closed ở cổng, không đi sâu.
NGOAI_NANG_LUC = (
    "Cho hình nón có bán kính đáy 3 và đường sinh 5. Tính diện tích xung "
    "quanh của hình nón.",
    "Trong không gian Oxyz, viết phương trình mặt phẳng đi qua ba điểm "
    "A(1;0;0), B(0;2;0), C(0;0;3).",
    "Cho hình lập phương ABCD.A'B'C'D'. Hãy vẽ hình chiếu của nó lên một mặt "
    "phẳng theo phương chiếu AC'.",
)


@pytest.mark.parametrize("de", NGOAI_NANG_LUC)
def test_de_HINH_HOC_NGOAI_nang_luc_van_bi_chan(de):
    """Fail-closed giữ nguyên. Đây là chỗ luật DƯƠNG khác luật ÂM: *"là hình
    học ⇒ luôn mô phỏng được"* sẽ thả cả ba đề này đi sâu vào tầng sinh."""
    assert not co_duong_thuc_thi(de, detect_domain(de)), de


def test_bang_manh_moi_KHONG_mo_nang_luc():
    """Mọi khoá phải có checker thật. Thêm khoá không checker = mở năng lực."""
    assert set(_MANH_MOI_NGHIA_VU) <= set(GEOMETRY_CHECKERS), \
        set(_MANH_MOI_NGHIA_VU) - set(GEOMETRY_CHECKERS)


def test_khong_manh_moi_thi_KHONG_mien():
    """Fail-closed ở cả ba chỗ: sai miền · không manh mối · rỗng."""
    assert not co_duong_thuc_thi("", DOMAIN_HINH_HOC)
    assert not co_duong_thuc_thi("Cho hình lập phương ABCD.A'B'C'D'.",
                                 DOMAIN_HINH_HOC)
    assert not co_duong_thuc_thi(
        "Cho hình chóp S.ABC. Tính thể tích.", DOMAIN_TIN_HOC)


# ══ BỘ CHẤM MỆNH ĐỀ: HỎI CHECKER, KHÔNG TÌM `True` ═══════════════════════
def _hd(kind: str, container: str, witness: str):
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import RequestContract
    return RequestContract(
        obligations=(Obligation(kind=kind, container=container,
                                params={"witness": witness}),))


def _cube(canh: int = 2) -> dict:
    from app.simulation.geometry.exact import Line3, Vec3
    V = Vec3.of
    p = {"A": V(0, 0, 0), "B": V(canh, 0, 0), "C": V(canh, canh, 0),
         "D": V(0, canh, 0)}
    p |= {f"{k}'": V(v.x, v.y, canh) for k, v in list(p.items())}
    p["AC"] = Line3.through(p["A"], p["C"])
    p["B'D'"] = Line3.through(p["B'"], p["D'"])
    p["AB"] = Line3.through(p["A"], p["B"])
    return p


def _mgs():
    """Nạp bộ đo một lần, dùng chung cho ba ca."""
    import importlib.util
    import sys
    from pathlib import Path
    if "_mgs" in sys.modules:
        return sys.modules["_mgs"]
    d = Path(__file__).resolve().parents[2] / "scripts" / "measure_geometry_stability.py"
    spec = importlib.util.spec_from_file_location("_mgs", d)
    m = importlib.util.module_from_spec(spec)
    sys.modules["_mgs"] = m
    spec.loader.exec_module(m)
    return m


def test_predicate_THOA_thi_True():
    M = _mgs()
    fm = _cube()
    dat, vi_sao = M.cham_predicate(fm, _hd("perpendicular", "AC", "B'D'"),
                                   "perpendicular")
    assert dat is True, vi_sao
    # `final_memory` KHÔNG chứa một `True` nào — đó là toàn bộ lý do bản cũ sai.
    assert not any(v is True for v in fm.values())


def test_predicate_VI_PHAM_thi_False():
    M = _mgs()
    fm = _cube()
    dat, vi_sao = M.cham_predicate(fm, _hd("perpendicular", "AC", "AB"),
                                   "perpendicular")
    assert dat is False, vi_sao


def test_predicate_HOP_DONG_khong_khai_thi_None_khong_phai_False():
    """Không chấm được ≠ sai. Gộp hai cái là ghi một lượt không đo được thành
    một lượt mô hình hỏng."""
    M = _mgs()
    dat, _ = M.cham_predicate(_cube(), _hd("parallel", "AC", "B'D'"),
                              "perpendicular")
    assert dat is None
    dat2, _ = M.cham_predicate(_cube(), None, "perpendicular")
    assert dat2 is None
