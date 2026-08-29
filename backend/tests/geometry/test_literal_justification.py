# -*- coding: utf-8 -*-
"""§6–§7 — MỌI LITERAL HÌNH HỌC PHẢI CÓ BIỆN MINH. 0 API call.

Bất biến bị BÁC BỎ ở wave trước: *"mọi đỉnh dẫn xuất phải do một primitive
dựng ra"*. IR không có phép tịnh tiến hay hoàn thành hình bình hành, nên
`C`, `D` của hình vuông `ABCD` cho trước `A`, `B` là không dựng được — áp luật
ấy sẽ buộc `unsupported` gần như mọi bài hình lập phương.

Bất biến ĐANG áp, và nó đúng hơn: một literal hình học đi qua được khi và chỉ
khi nó rơi vào một trong ba lớp biện minh —

    A  tự do hệ trục          B  ghim về nguồn          C  hiện thực mô hình

Không lớp nào ⇒ TỪ CHỐI. Test ở đây khoá cả ba lớp lẫn phép đếm, vì phép đếm
là thứ báo cáo sẽ trích: đếm sai một lớp thì tỉ lệ đẹp lên mà cổng không đổi.
"""
from __future__ import annotations

from app.simulation.semantic_program.grounding_gate import (
    check_grounding,
    ti_le_literal_hinh_hoc,
)
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import (
    InputFact,
    RequestContract,
)
from app.simulation.semantic_program.scale_normalization import chuan_hoa_thang
from app.simulation.semantic_program.validator import validate_semantic_program


def _spec(decls: list[dict], obligations=()):
    val = validate_semantic_program({
        "simulation_id": "geometry.demo",
        "title": "Demo", "description": "Demo", "pedagogical_intent": "Demo",
        "memory_declarations": decls, "statements": [],
        "obligations": list(obligations),
    })
    assert val.ok, val.error
    return val.spec


def _lop(kq, ten: str) -> str | None:
    for d in kq.justified_literals:
        p = d.split("|")
        if p[0] == ten:
            return p[2]
    return None


_QUAN_HE = RequestContract(input_facts=(
    InputFact(fact_id="abcd_vuong", label="ABCD là hình vuông",
              values=("ABCD là hình vuông",)),
))


def test_lop_A_tu_do_he_truc():
    kq = check_grounding(_QUAN_HE, _spec([
        {"name": "A", "type": "point3", "initial_value": [0, 0, 0],
         "model_assumption": "chọn A làm gốc"},
    ]))
    assert kq.ok and _lop(kq, "A") == "A"
    assert ti_le_literal_hinh_hoc(kq) == (1, 1)


def test_lop_C_hien_thuc_mo_hinh_theo_du_kien_quan_he():
    kq = check_grounding(_QUAN_HE, _spec([
        {"name": "C", "type": "point3", "initial_value": [1, 1, 0],
         "source_fact_id": "abcd_vuong",
         "model_assumption": "C suy ra từ ABCD là hình vuông"},
    ]))
    assert kq.ok and _lop(kq, "C") == "C"


def test_lop_B_ghim_ve_nguon():
    hd = RequestContract(input_facts=(
        InputFact(fact_id="canh", label="Cạnh", values=(2,)),))
    kq = check_grounding(hd, _spec([
        {"name": "B", "type": "point3", "initial_value": [2, 0, 0],
         "source_fact_id": "canh"},
    ]))
    assert kq.ok and _lop(kq, "B") == "B"


def test_literal_KHONG_bien_minh_duoc_thi_bi_TU_CHOI_va_bi_DEM():
    kq = check_grounding(_QUAN_HE, _spec([
        {"name": "H", "type": "point3", "initial_value": [5, 7, 9]},
    ]))
    assert not kq.ok
    assert ti_le_literal_hinh_hoc(kq) == (0, 1)
    assert kq.unjustified_literals and kq.unjustified_literals[0].startswith("H|")


def test_toa_do_bia_ghim_vao_muc_CO_SO_van_bi_tu_choi():
    """Lớp B không được biến thành cửa sau: `{5,7,9}` không có trong `{1}`."""
    hd = RequestContract(input_facts=(
        InputFact(fact_id="canh", label="Cạnh", values=(1,)),))
    kq = check_grounding(hd, _spec([
        {"name": "H", "type": "point3", "initial_value": [5, 7, 9],
         "source_fact_id": "canh", "model_assumption": "đặt H"},
    ]))
    assert not kq.ok and ti_le_literal_hinh_hoc(kq) == (0, 1)


def test_witness_khai_lam_gia_thiet_van_bi_tu_choi_va_dem_la_vo_can():
    hd = RequestContract(
        obligations=(Obligation(kind="distance", container="ABC",
                                params={"witness": "d"}),),
        input_facts=(InputFact(fact_id="canh", label="Cạnh", values=(1,)),))
    kq = check_grounding(hd, _spec([
        {"name": "d", "type": "point3", "initial_value": [1, 0, 0],
         "model_assumption": "đặt sẵn đáp án"},
    ]))
    assert not kq.ok
    assert kq.error_code == "MODEL_ASSUMPTION_IS_ANSWER"
    assert ti_le_literal_hinh_hoc(kq) == (0, 1)


# ── §7 · buộc thang KHÔNG phải một giả thiết tuỳ tiện ───────────────────────
def test_buoc_thang_di_loi_B_chu_khong_phai_gia_thiet():
    """`SA = 4a/5` → `4/5`; chương trình khai `0.8` và ghim về đúng mục.

    Nếu con số ấy phải đi qua `model_assumption` thì nó sẽ bị đếm như một giá
    trị vô căn cứ — trong khi nó do SERVER chốt, tất định, và truy ngược được
    tới nguyên văn của đề.
    """
    hd = chuan_hoa_thang(
        RequestContract(input_facts=(
            InputFact(fact_id="sa_length", label="Độ dài SA", values=("4a/5",)),
        )),
        "Cho hình chóp S.ABC có SA = 4a/5.")
    assert hd.scale_binding is not None

    kq = check_grounding(hd, _spec([
        {"name": "S", "type": "point3", "initial_value": [0, 0, 0.8],
         "source_fact_id": "sa_length"},
    ]))
    assert kq.ok, kq.unresolved
    assert _lop(kq, "S") == "B"
    assert kq.assumptions == [], "buộc thang không được tính là giả thiết"


def test_khong_buoc_thang_thi_muc_ky_hieu_khong_kiem_duoc_gi_ca():
    """Trạng thái TRƯỚC phép sửa, viết ra để thấy nó KÉM hơn — không phải hơn.

    Mục còn giữ ký hiệu `'a'` thì không có số nào để đối chiếu, nên mọi toạ độ
    ghim vào đó rơi vào lớp C: nhận theo hiện thực mô hình, và ràng buộc đẩy
    xuống hậu điều kiện. `0.8` hay `7` đều qua như nhau ở CỔNG NÀY.
    """
    hd = RequestContract(input_facts=(
        InputFact(fact_id="sa_length", label="Độ dài SA", values=("a",)),))
    for z in (0.8, 7):
        kq = check_grounding(hd, _spec([
            {"name": "S", "type": "point3", "initial_value": [0, 0, z],
             "source_fact_id": "sa_length"},
        ]))
        assert kq.ok and _lop(kq, "S") == "C"


def test_sau_buoc_thang_toa_do_SAI_bi_TU_CHOI_ngay_tai_cong():
    """Đây mới là cái phép chuẩn hoá thang mua được.

    Mục thành `4/5`, tức có một con số thật để đối chiếu, nên `z = 7` không
    còn lọt lớp C nữa — nó bị bác ngay ở P2 thay vì phải chờ oracle.
    """
    hd = chuan_hoa_thang(
        RequestContract(input_facts=(
            InputFact(fact_id="sa_length", label="Độ dài SA", values=("4a/5",)),
        )),
        "Cho hình chóp S.ABC có SA = 4a/5.")
    kq = check_grounding(hd, _spec([
        {"name": "S", "type": "point3", "initial_value": [0, 0, 7],
         "source_fact_id": "sa_length"},
    ]))
    assert not kq.ok and ti_le_literal_hinh_hoc(kq) == (0, 1)
