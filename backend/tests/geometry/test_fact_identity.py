# -*- coding: utf-8 -*-
"""TASK 2 — giải `source_fact_id` khi hai lượt LLM gọi tên khác nhau. **0 API.**

ĐO ĐƯỢC Ở PHASE 5 LƯỢT 2 (`027c9e1`): 6/10 bài chết vì `source_fact_id` không
giải được. Mô hình trích dẫn `canh_day`, `abcd_hinh_vuong`, `sa_vuong_goc_day` —
những id **hợp lý** mà lượt `analyze` không đặt.

Hai bậc nới, và ranh giới giữa chúng là toàn bộ thiết kế:

  ① CHUẨN HOÁ ID — tất định, không đoán nghĩa. `CANH-DAY` ≡ `cạnh_đáy`.
  ② HẠ CẤP TRÍCH DẪN HỎNG — chỉ khi khai báo đã tự đứng vững bằng kênh giả
    thiết mô hình hoá, tức đã qua ba khoá độc lập.

Cái KHÔNG làm, và vì sao: khớp theo `semantic_type`/`entities`/`attributes`.
Cả hai phía của phép khớp ấy đều do cùng một model đặt tên, nên nó là model tự
đối chiếu nhãn của chính nó — đúng chế độ hỏng mà `RequestContract` sinh ra để
chặn. Hệ quả cụ thể: một `float` giữ `2/3` sẽ khớp fact `semantic_type: volume`.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.contract import (
    MemoryDeclaration,
    SemanticProgramSpec,
)
from app.simulation.semantic_program.grounding_gate import (
    ERR_GIA_THIET_LA_DAP_AN,
    ERR_GIA_THIET_SAI_KIEU,
    check_grounding,
)
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import (
    InputFact,
    RequestContract,
    _chuan_hoa_id,
)


def _spec(*decls: dict) -> SemanticProgramSpec:
    return SemanticProgramSpec(
        spec_version="1.0",
        title="Kiểm định danh dữ kiện",
        memory_declarations=[MemoryDeclaration(**d) for d in decls],
        statements=[],
    )


_HD = RequestContract(input_facts=(
    InputFact(fact_id="canh_day", label="cạnh đáy", values=(1,)),
))


# ══ ① CHUẨN HOÁ — tất định ════════════════════════════════════════════════
@pytest.mark.parametrize("a,b", [
    ("canh_day", "CANH_DAY"),
    ("canh_day", "canh-day"),
    ("canh_day", "cạnh_đáy"),
    ("canh_day", "Cạnh Đáy"),
    ("abcd_hinh_vuong", "ABCD-Hình-Vuông"),
    ("sa_vuong_goc_day", "SA vuông góc đáy"),
])
def test_cung_mot_id_sau_chuan_hoa(a, b):
    assert _chuan_hoa_id(a) == _chuan_hoa_id(b)


@pytest.mark.parametrize("a,b", [
    ("canh_day", "canh_ben"),
    ("volume", "distance"),
    ("abcd_hinh_vuong", "abcd_hinh_chu_nhat"),
])
def test_id_KHAC_NGHIA_khong_bi_gop(a, b):
    """Chuẩn hoá chỉ bỏ dấu và dấu phân cách. Nó KHÔNG được đoán nghĩa — gộp
    `canh_day` với `canh_ben` là bịa ra một quan hệ không ai kiểm được."""
    assert _chuan_hoa_id(a) != _chuan_hoa_id(b)


def test_fact_noi_long_bao_dung_CACH_KHOP():
    """Người đọc artifact phải phân biệt được "khớp thẳng" với "khớp sau chuẩn
    hoá" — cái sau là bằng chứng rằng hai lượt LLM đang lệch danh xưng."""
    assert _HD.fact_noi_long("canh_day")[1] == "exact"
    assert _HD.fact_noi_long("CANH-DAY")[1] == "chuan_hoa"
    assert _HD.fact_noi_long("khong_ton_tai") == (None, "khong_khop")


def test_khop_sau_chuan_hoa_VAN_kiem_gia_tri():
    """Nới ĐỊNH DANH không được kéo theo nới GIÁ TRỊ. Ghim đúng mục mà khai sai
    số thì vẫn phải chết — nếu không, bậc chuẩn hoá thành cửa hậu."""
    ok = check_grounding(_HD, _spec(
        {"name": "n", "type": "int", "initial_value": 1,
         "source_fact_id": "CANH-DAY"}))
    assert ok.ok
    assert ok.unresolved_citations, "khớp sau chuẩn hoá phải được GHI LẠI"

    xau = check_grounding(_HD, _spec(
        {"name": "n", "type": "int", "initial_value": 99,
         "source_fact_id": "CANH-DAY"}))
    assert not xau.ok


# ══ ② HẠ CẤP TRÍCH DẪN HỎNG — hẹp có chủ đích ════════════════════════════
def test_trich_dan_hong_KHONG_giet_khai_bao_co_gia_thiet():
    """Ca `geo_09` của PHASE 5: `B point3 [1,0,0]` có `model_assumption` hợp lệ
    VÀ `source_fact_id='canh_day'` không giải được. Luật Wave 2 giết nó; mô hình
    bị phạt vì nói THÊM thông tin."""
    kq = check_grounding(RequestContract(), _spec(
        {"name": "B", "type": "point3", "initial_value": [1, 0, 0],
         "source_fact_id": "canh_day",
         "model_assumption": "cạnh đáy dọc trục x"}))
    assert kq.ok, kq.unresolved
    assert kq.assumptions == ["B: cạnh đáy dọc trục x"]
    assert len(kq.unresolved_citations) == 1


def test_KHONG_co_gia_thiet_thi_NGHIEM_NGAT_nhu_cu():
    """Đây là điều kiện để bậc ② không phải là nới cổng: trích dẫn hỏng mà
    không có gì đỡ thì vẫn chết đúng như trước Wave 3."""
    kq = check_grounding(RequestContract(), _spec(
        {"name": "n", "type": "int", "initial_value": 5,
         "source_fact_id": "khong_ton_tai"}))
    assert not kq.ok and kq.error_code == "INPUT_NOT_GROUNDED"


def test_DAP_AN_khong_thoat_duoc_bang_duong_trich_dan_hong():
    """Chốt cứng nhất. Một `float` giữ `2/3`, gắn nhãn giả thiết, kèm một
    `source_fact_id` bịa — cả ba lối vào cùng lúc. Vẫn phải chết."""
    kq = check_grounding(RequestContract(), _spec(
        {"name": "V", "type": "float", "initial_value": "2/3",
         "source_fact_id": "the_tich_khoi_chop",
         "model_assumption": "thể tích tính được"}))
    assert not kq.ok and kq.error_code == ERR_GIA_THIET_SAI_KIEU


def test_WITNESS_khong_thoat_duoc_bang_duong_trich_dan_hong():
    hd = RequestContract(obligations=(
        Obligation(kind="point_on_plane", container="day",
                   params={"witness": "H"}),
    ))
    kq = check_grounding(hd, _spec(
        {"name": "H", "type": "point3", "initial_value": [0, 0, 0],
         "source_fact_id": "hinh_chieu", "model_assumption": "hình chiếu của S"}))
    assert not kq.ok and kq.error_code == ERR_GIA_THIET_LA_DAP_AN


# ══ ③ RANH GIỚI ÂM — KHÔNG có khớp mờ, và điều đó phải KIỂM ĐƯỢC ═════════
def test_fact_id_KHONG_khop_theo_GIA_TRI():
    """Ca TASK 2 nêu: fact `volume`, chương trình trích dẫn `2/3`. Phải TRƯỢT.

    Nếu một ngày phép khớp nhìn vào GIÁ TRỊ thay vì ĐỊNH DANH, đây là ca đầu
    tiên vỡ — và nó vỡ theo hướng tệ nhất: đáp số tự khớp với nghĩa vụ hỏi nó.
    """
    hd = RequestContract(input_facts=(
        InputFact(fact_id="volume", label="thể tích", values=("2/3",)),
    ))
    assert hd.fact_noi_long("2/3") == (None, "khong_khop")
    kq = check_grounding(hd, _spec(
        {"name": "V", "type": "float", "initial_value": "2/3",
         "source_fact_id": "2/3"}))
    assert not kq.ok


def test_KHONG_co_khop_MO_trong_ma_nguon():
    """Guard CẤU TRÚC, không phải guard hành vi.

    Test hành vi chỉ bắt được ca ta nghĩ ra. Cấm ở tầng import thì bắt cả thứ
    chưa ai viết: một `difflib`, một embedding, một `rapidfuzz` lẻn vào sau này
    sẽ ĐỎ ngay, kể cả khi tác giả của nó tin là mình đang cải thiện.

    Vì sao cấm: cả hai phía của phép khớp ngữ nghĩa đều do CÙNG MỘT model đặt
    tên. Cho nó khớp mờ là để model tự chứng minh chính nó.
    """
    import ast
    from pathlib import Path

    p = (Path(__file__).resolve().parents[2] / "app" / "simulation"
         / "semantic_program" / "request_contract.py")
    cay = ast.parse(p.read_text(encoding="utf-8"))
    goc: list[str] = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            goc += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module:
            goc.append(n.module)
    cam = ("difflib", "rapidfuzz", "fuzzywuzzy", "Levenshtein", "numpy",
           "sklearn", "sentence_transformers", "openai", "torch")
    lo = [g for g in goc for c in cam if c in g]
    assert not lo, f"khớp mờ/embedding lọt vào biên grounding: {lo}"


def test_chuan_hoa_KHONG_dung_cho_GIA_TRI():
    """Chuẩn hoá là phép của ĐỊNH DANH. Đem nó sang so giá trị thì `"2/3"` và
    `"23"` thành một — nên phải chứng minh hai đường đó tách nhau."""
    from app.simulation.semantic_program.request_contract import norm_value

    assert _chuan_hoa_id("2/3") == _chuan_hoa_id("23")
    assert norm_value("2/3") != norm_value("23")


# ══ ĐỐI CHỨNG TRÊN DỮ LIỆU THẬT CỦA PHASE 5 ══════════════════════════════
def test_ba_bai_PHASE5_van_bi_chan_va_chan_DUNG():
    """Không phải mọi ca grounding của lượt 2 đều nên đi qua, và test này khoá
    lại vì sao ba ca còn lại VẪN phải chết:

      geo_05  `perpendicular: bool = True`, không giả thiết
              ⇒ mô hình khai THẲNG ĐÁP ÁN. R0 chặn đúng.
      geo_03  `C: point3` có `source_fact_id` mà KHÔNG có `model_assumption`.
      geo_07  bốn khai báo cùng dạng ấy.

    Nếu một bản vá sau này làm ba ca này xanh lên, nó đã mở đường tuồn đáp án.
    """
    # geo_05 rút gọn
    kq = check_grounding(RequestContract(), _spec(
        {"name": "perpendicular", "type": "bool", "initial_value": True,
         "source_fact_id": "sa_vuong_goc_day"}))
    assert not kq.ok, "bool khai sẵn True phải bị chặn"

    # geo_03 / geo_07 rút gọn
    kq2 = check_grounding(RequestContract(), _spec(
        {"name": "C", "type": "point3", "initial_value": [1, 1, 0],
         "source_fact_id": "abcd_is_square"}))
    assert not kq2.ok, "point3 không có model_assumption phải bị chặn"
