# -*- coding: utf-8 -*-
"""WAVE 4 — TASK 2: toạ độ KHÔNG phải dữ kiện đề cho. **0 API call.**

ĐO ĐƯỢC Ở PHASE 5.5: 5/10 bài chết ở P2, và chúng chết vì P2 **hỏi sai câu**.

    B: giá trị [0, 0] không có trong mục 'canh_day' (cạnh đáy)
    C: giá trị [1, 1, 0] không có trong mục 'abcd_hinh_vuong'

Mô hình khai `B = (1,0,0)` rồi ghim về `canh_day` (values = `1`). P2 phẳng hoá
toạ độ thành `1, 0, 0` rồi đòi TỪNG nguyên tử có trong mục. `1` có; `0` không.

Nhưng `0` là **số không cấu trúc của hệ trục** — "không dịch theo y, không dịch
theo z". Còn `abcd_hinh_vuong` là một fact QUAN HỆ (`values` = một mệnh đề, không
có số nào): mô hình đang nói *"vị trí C suy ra từ ABCD là hình vuông"*, một lập
luận đúng mà phép kiểm theo giá trị không diễn đạt được.

Luật mới hẹp, và ranh giới của nó là toàn bộ nội dung file này.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.contract import (
    MemoryDeclaration,
    SemanticProgramSpec,
)
from app.simulation.semantic_program.grounding_gate import (
    ERR_GIA_THIET_LA_DAP_AN,
    check_grounding,
)
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import (
    InputFact,
    RequestContract,
)


def _spec(*decls: dict) -> SemanticProgramSpec:
    return SemanticProgramSpec(
        spec_version="1.0",
        title="Kiểm grounding toạ độ",
        memory_declarations=[MemoryDeclaration(**d) for d in decls],
        statements=[],
    )


#: Hợp đồng dựng lại từ `geo_09` THẬT của Phase 5.5.
_HD = RequestContract(input_facts=(
    InputFact(fact_id="canh_day", label="cạnh đáy", values=(1,)),
    InputFact(fact_id="chieu_cao_sa", label="chiều cao SA", values=(2,)),
    InputFact(fact_id="abcd_hinh_vuong", label="ABCD là hình vuông",
              values=("ABCD là hình vuông",)),
))


# ══ CA DƯƠNG — đúng những khai báo Phase 5.5 từ chối oan ═════════════════
@pytest.mark.parametrize("ten,toa_do,fid", [
    ("B", [1, 0, 0], "canh_day"),
    ("D", [0, 1, 0], "canh_day"),
    ("S", [0, 0, 2], "chieu_cao_sa"),
])
def test_so_KHONG_cau_truc_khong_can_truy_ve_de(ten, toa_do, fid):
    kq = check_grounding(_HD, _spec(
        {"name": ten, "type": "point3", "initial_value": toa_do,
         "source_fact_id": fid, "model_assumption": "hệ trục đã chọn"}))
    assert kq.ok, kq.unresolved


def test_fact_QUAN_HE_chap_nhan_va_GHI_LAI():
    """`abcd_hinh_vuong` có `values`, nhưng không có SỐ nào. Bản nháp đầu kiểm
    `not values` nên trượt ngay ở lượt thử — mệnh đề không phải chỗ trống."""
    kq = check_grounding(_HD, _spec(
        {"name": "C", "type": "point3", "initial_value": [1, 1, 0],
         "source_fact_id": "abcd_hinh_vuong",
         "model_assumption": "ABCD là hình vuông nên C ở (1,1,0)"}))
    assert kq.ok, kq.unresolved
    assert any("QUAN HỆ" in u for u in kq.unresolved_citations)


def test_KHONG_can_model_assumption_van_qua():
    """Điều kiện dựa trên KIỂU, không dựa trên trí nhớ của model.

    Bản đầu đòi cả `model_assumption`, và đo lại trên Phase 5.5 cho thấy nó chỉ
    gỡ được 1/5 bài — bốn bài kia model gắn `source_fact_id` mà QUÊN gắn giả
    thiết. Ở miền này **đề không bao giờ cho toạ độ**: một `point3` có toạ độ
    thì đó là hệ trục do người giải chọn, dù bản khai có nhớ nói ra hay không.
    """
    kq = check_grounding(_HD, _spec(
        {"name": "B", "type": "point3", "initial_value": [1, 0, 0],
         "source_fact_id": "canh_day"}))
    assert kq.ok, kq.unresolved


# ══ CA ÂM — ranh giới, và đây mới là phần quan trọng ═════════════════════
def test_toa_do_BIA_van_bi_chan():
    """`H = (5,7,9)` ghim về `canh_day` (values = `1`). Không nguyên tử khác 0
    nào khớp ⇒ vẫn chết. Nới `0` KHÔNG kéo theo nới mọi số."""
    kq = check_grounding(_HD, _spec(
        {"name": "H", "type": "point3", "initial_value": [5, 7, 9],
         "source_fact_id": "canh_day", "model_assumption": "chọn hệ trục"}))
    assert not kq.ok
    assert any("5" in u for u in kq.unresolved)


def test_MOT_nguyen_tu_sai_la_du_de_chan():
    """Không phải "khớp một cái là qua" — MỌI nguyên tử khác 0 đều phải khớp."""
    kq = check_grounding(_HD, _spec(
        {"name": "X", "type": "point3", "initial_value": [1, 99, 0],
         "source_fact_id": "canh_day", "model_assumption": "chọn hệ trục"}))
    assert not kq.ok and any("99" in u for u in kq.unresolved)


def test_WITNESS_khong_bao_gio_di_loi_toa_do():
    """Khoá R0 thay chỗ cho `model_assumption`. Đáp án không bao giờ là hệ trục.

    Không có khoá này thì bỏ điều kiện `model_assumption` sẽ mở đúng cửa mà
    Wave 2/3 đã đóng.
    """
    hd = RequestContract(
        input_facts=_HD.input_facts,
        obligations=(Obligation(kind="point_on_plane", container="day",
                                params={"witness": "H"}),),
    )
    kq = check_grounding(hd, _spec(
        {"name": "H", "type": "point3", "initial_value": [9, 9, 9],
         "source_fact_id": "abcd_hinh_vuong",
         "model_assumption": "hình chiếu"}))
    assert not kq.ok


def test_DAI_LUONG_khong_di_loi_toa_do():
    """`float` không phải `point3`/`vector3`, nên `V = 2/3` ghim về một fact
    quan hệ vẫn chết. Đây là đường tuồn đáp án, và nó vẫn đóng."""
    kq = check_grounding(_HD, _spec(
        {"name": "V", "type": "float", "initial_value": "2/3",
         "source_fact_id": "abcd_hinh_vuong"}))
    assert not kq.ok


@pytest.mark.parametrize("kieu", ["line3", "plane3", "solid", "polygon3"])
def test_doi_tuong_DAN_XUAT_khong_di_loi_toa_do(kieu):
    """Đường, mặt, khối phải được DỰNG từ điểm. Cho chúng đi lối toạ độ là mở
    cửa khai thẳng toạ độ kết quả."""
    gt = {"line3": {"through": [[0, 0, 0], [9, 9, 9]]},
          "plane3": {"through": [[0, 0, 0], [9, 9, 9], [8, 8, 8]]},
          "solid": {"vertices": [[9, 9, 9]], "faces": [[0]]},
          "polygon3": [[9, 9, 9], [8, 8, 8], [7, 7, 7]]}[kieu]
    kq = check_grounding(_HD, _spec(
        {"name": "x", "type": kieu, "initial_value": gt,
         "source_fact_id": "abcd_hinh_vuong"}))
    assert not kq.ok


def test_TIN_HOC_khong_bi_anh_huong():
    """Một `array` ghim về fact vẫn phải khớp TỪNG giá trị, kể cả `0`. Luật
    toạ độ chỉ mở cho `point3`/`vector3`."""
    hd = RequestContract(input_facts=(
        InputFact(fact_id="day", label="dãy", values=(1, 2, 3)),
    ))
    assert check_grounding(hd, _spec(
        {"name": "a", "type": "array", "initial_value": [1, 2, 3],
         "source_fact_id": "day"})).ok
    assert not check_grounding(hd, _spec(
        {"name": "a", "type": "array", "initial_value": [1, 0, 3],
         "source_fact_id": "day"})).ok


# ══ ĐỐI CHỨNG TRÊN 5 CA THẬT CỦA PHASE 5.5 ══════════════════════════════
def test_nam_ca_PHASE55_nay_di_qua():
    """Ca `geo_09` dựng lại nguyên vẹn từ artifact."""
    kq = check_grounding(_HD, _spec(
        {"name": "A", "type": "point3", "initial_value": [0, 0, 0],
         "model_assumption": "gốc toạ độ"},
        {"name": "B", "type": "point3", "initial_value": [1, 0, 0],
         "source_fact_id": "canh_day", "model_assumption": "cạnh đáy"},
        {"name": "D", "type": "point3", "initial_value": [0, 1, 0],
         "source_fact_id": "canh_day", "model_assumption": "cạnh đáy"},
        {"name": "C", "type": "point3", "initial_value": [1, 1, 0],
         "source_fact_id": "abcd_hinh_vuong", "model_assumption": "hình vuông"},
        {"name": "S", "type": "point3", "initial_value": [0, 0, 2],
         "source_fact_id": "chieu_cao_sa", "model_assumption": "SA = 2"},
    ))
    assert kq.ok, kq.unresolved
    # `assumptions` chỉ đếm khai báo đi qua KÊNH GIẢ THIẾT — `A` (không ghim gì)
    # và `C` (ghim về fact quan hệ). `B`/`D`/`S` ghim THẬT vào fact có số, nên
    # chúng là dữ liệu **đã truy được về đề**, không phải giả thiết. Phân biệt
    # này là thứ làm con số quan trắc có nghĩa: nó đếm phần KHÔNG chứng minh
    # được, và đếm thừa thì nó thôi cảnh báo.
    assert sorted(kq.assumptions) == ["A: gốc toạ độ", "C: hình vuông"]
    assert len(kq.unresolved_citations) == 1
