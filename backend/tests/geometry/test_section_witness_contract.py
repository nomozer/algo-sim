# -*- coding: utf-8 -*-
"""HỢP ĐỒNG WITNESS của `section_matches` — Stage 0. **0 API call.**

─── LỖI ĐÃ QUAN SÁT ĐƯỢC, lượt live `geo_03` 2026-08-30 ────────────────────

Mô hình phát `witness: "null"`, C₁a bác với *"witness 'null' chưa khai báo"*, và
người đọc đi tìm một biến không hề tồn tại.

Nguyên nhân KHÔNG phải mô hình. Schema `analyze` khai::

    "witness": {"type": "STRING"}          # không nullable
    "required": ["kind", "container", "witness"]

Structured output vì thế **không có đường hợp lệ nào để nói "nghĩa vụ này không
có witness"**. Câu trả lời đúng không biểu diễn được ⇒ mô hình viết chuỗi gần
nhất với ý nó muốn nói. Đây là lỗi HỢP ĐỒNG.

─── VÀ MỘT LỖ THỨ HAI, LỘ RA KHI VÁ LỖ THỨ NHẤT ────────────────────────────

`check_section_matches` đọc `params["solid"]` và `params["plane"]`, nhưng schema
`analyze` **không có hai trường ấy**. Nghĩa là checker mạnh nhất của miền hình
học đọc ra `None` và luôn trả `None` = mức yếu: nó **chưa từng chấm được lần nào
qua đường sản phẩm**. Cùng đúng lớp lỗi "kernel có, cầu nối không" đã bắt hai
lần trước ở `distance` và ở chính `section_matches`.

Ba phép sửa, ba tầng khác nhau — file này khoá cả ba.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from app.simulation.semantic_program.analyze_contract import (
    _THAM_SO_LA_TEN,
    analyze_schema_for,
    build_request_contract,
)
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.coverage_gate import (
    _CAU_TRUC_HINH_HOC,
    check_realized_coverage,
    check_structural_coverage,
)
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.obligations import (
    OBLIGATION_KINDS,
    WITNESS_FREE_KINDS,
    has_server_owned_checker,
)
from app.simulation.semantic_program.postconditions import check_postconditions

BACKEND = Path(__file__).resolve().parents[2]


def _chuong_trinh_thiet_dien() -> SemanticProgramSpec:
    """Chương trình thiết diện lấy từ CHÍNH bộ sinh bài mẫu.

    Không chép tay sang đây: chép là dựng nguồn thứ hai, và nguồn thứ hai sẽ
    trôi khỏi bản thật đúng lần sửa tiếp theo.
    """
    sp = importlib.util.spec_from_file_location(
        "build_geometry_samples", BACKEND / "scripts" / "build_geometry_samples.py")
    m = importlib.util.module_from_spec(sp)
    sys.modules["build_geometry_samples"] = m
    sp.loader.exec_module(m)
    return SemanticProgramSpec.model_validate(m.chuong_trinh_thiet_dien())


def _obligations() -> dict:
    """Schema NGHĨA VỤ mà mô hình miền hình học thật sự nhận được."""
    return analyze_schema_for(DOMAIN_HINH_HOC)["properties"]["obligations"]["items"]


# ══ ① SCHEMA — câu trả lời đúng phải BIỂU DIỄN ĐƯỢC ══════════════════════
def test_witness_NULLABLE_va_VAN_bat_buoc():
    """Hai điều kiện, mỗi cái chặn một kiểu hỏng ngược nhau.

    `nullable` — để "không có witness" nói được. Bỏ nó là bắt mô hình bịa.
    Vẫn trong `required` — để "quên witness" KHÔNG trở thành cùng hình dạng với
    "không có witness". Bỏ nó ra là mở lại đúng chỗ mù vừa dọn.
    """
    items = _obligations()
    assert items["properties"]["witness"]["nullable"] is True
    assert "witness" in items["required"]


def test_schema_CO_hai_toan_hang_cua_section_matches():
    """`check_section_matches` đọc `params[solid]`/`params[plane]` — analyze
    phải có đường phát ra chúng, nếu không checker không bao giờ chấm được."""
    props = _obligations()["properties"]
    assert "solid" in props and "plane" in props
    assert props["solid"]["nullable"] is True
    assert props["plane"]["nullable"] is True


def test_mo_ta_witness_NOI_RO_khi_nao_dat_null():
    from app.simulation.semantic_program.analyze_contract import (
        MO_TA_WITNESS_HINH_HOC,
    )

    assert "null" in MO_TA_WITNESS_HINH_HOC
    assert "section_matches" in MO_TA_WITNESS_HINH_HOC


# ══ ② BIÊN NHẬN — chuỗi rỗng nghĩa KHÔNG phải một cái tên ════════════════
@pytest.mark.parametrize("rac", ["null", "None", "NULL", "none", "nil",
                                 "undefined", "n/a", "-", "", "   "])
def test_witness_RONG_NGHIA_bi_bo_o_bien(rac):
    """HỒI QUY TRỰC TIẾP của `geo_03`.

    Không phải bản vá cho một ca: luật là **tham số trỏ tới một vật phải là một
    ĐỊNH DANH**. Không chương trình nào khai biến tên `null`, nên nhận chuỗi ấy
    làm tên là nhận một tên chắc chắn tra không ra — rồi bác ở tầng sau bằng
    thông điệp che mất nguyên nhân thật.
    """
    hd = build_request_contract(
        {"obligations": [{"kind": "coplanar", "container": "td", "witness": rac}],
         "input_facts": []}, "")
    assert hd.obligations[0].witness is None
    assert "witness" not in hd.obligations[0].params


def test_ten_THAT_thi_KHONG_bi_dong_cham():
    """Rỗng-là-hỏng theo chiều ngược: vá quá tay thì mọi witness đều biến mất."""
    hd = build_request_contract(
        {"obligations": [{"kind": "coplanar", "container": "td", "witness": "M"}],
         "input_facts": []}, "")
    assert hd.obligations[0].witness == "M"


def test_moi_tham_so_LA_TEN_deu_duoc_chuan_hoa():
    """`witness` không phải trường duy nhất bị tra như một cái tên."""
    raw = {"kind": "section_matches", "container": "td"}
    for k in _THAM_SO_LA_TEN:
        raw[k] = "null"
    hd = build_request_contract({"obligations": [raw], "input_facts": []}, "")
    assert dict(hd.obligations[0].params) == {}


def test_geo_03_KHONG_con_hong_vi_bien_ma():
    """Phát lại ĐÚNG payload analyze của lượt live, qua biên đã sửa.

    Chương trình vẫn KHÔNG qua C₁a — nhưng nay vì một lý do ngữ nghĩa THẬT
    (`coplanar` cần witness mà mô hình không cho), chứ không phải vì một biến
    tên `null` mà không ai đi tìm được.
    """
    spec = _chuong_trinh_thiet_dien()
    hd = build_request_contract(
        {"obligations": [{"kind": "coplanar", "container": "thiet_dien",
                          "witness": "null"}], "input_facts": []}, "")
    kq = check_structural_coverage(hd, spec)
    assert not kq.ok
    loi = " ".join(kq.missing)
    assert "thiếu witness" in loi
    assert "null" not in loi, "thông điệp vẫn còn nhắc tới biến ma"


# ══ ③ ĐƯỜNG ĐÚNG — section_matches đi trọn ba cổng ═══════════════════════
def test_section_matches_KHONG_witness_di_tron_ba_cong():
    spec = _chuong_trinh_thiet_dien()
    hd = build_request_contract(
        {"obligations": [{"kind": "section_matches", "container": "thiet_dien",
                          "witness": None, "solid": "chop", "plane": "mp"}],
         "input_facts": []}, "")
    ob = hd.obligations[0]
    assert ob.witness is None
    assert ob.params["solid"] == "chop" and ob.params["plane"] == "mp"

    c1a = check_structural_coverage(hd, spec)
    assert c1a.ok, c1a.missing
    kq = SemanticProgramInterpreter().execute(spec)
    c1b = check_realized_coverage(hd, spec, kq)
    assert c1b.ok, c1b.missing
    c2 = check_postconditions(hd, spec, kq, c1a.ten_da_hoa_giai)
    assert c2.ok, c2.violations


def test_section_matches_THIEU_toan_hang_thi_C1a_BAC():
    """Không có witness KHÔNG có nghĩa là không đòi gì — cổng đòi CẢ HAI
    toán hạng, chặt hơn đòi một witness."""
    spec = _chuong_trinh_thiet_dien()
    for thieu in ("solid", "plane"):
        raw = {"kind": "section_matches", "container": "thiet_dien",
               "witness": None, "solid": "chop", "plane": "mp"}
        del raw[thieu]
        hd = build_request_contract({"obligations": [raw], "input_facts": []}, "")
        kq = check_structural_coverage(hd, spec)
        assert not kq.ok and thieu in " ".join(kq.missing)


def test_section_matches_tro_toan_hang_CHUA_DUNG_thi_C1a_BAC():
    spec = _chuong_trinh_thiet_dien()
    hd = build_request_contract(
        {"obligations": [{"kind": "section_matches", "container": "thiet_dien",
                          "witness": None, "solid": "khong_ton_tai",
                          "plane": "mp"}], "input_facts": []}, "")
    kq = check_structural_coverage(hd, spec)
    assert not kq.ok and "khong_ton_tai" in " ".join(kq.missing)


# ══ ④ THẨM QUYỀN — các bảng phải ĐỒNG Ý với nhau ═════════════════════════
def test_nhom_CAU_TRUC_dan_tu_taxonomy_khong_chep_tay():
    """Ba bảng liệt kê kiểu đã trôi khỏi nhau một lần trong wave này. Ở đây
    dùng CHUNG một đối tượng, nên không có gì để trôi."""
    assert _CAU_TRUC_HINH_HOC is WITNESS_FREE_KINDS


def test_moi_kind_KHONG_WITNESS_deu_that_va_co_checker():
    assert WITNESS_FREE_KINDS <= set(OBLIGATION_KINDS)
    for kind in WITNESS_FREE_KINDS:
        assert has_server_owned_checker(kind), (
            f"`{kind}` được miễn witness nhưng không có checker — miễn đòi hỏi "
            "mà không có gì kiểm lại là mở một cửa trống"
        )


def test_kind_KHONG_WITNESS_thi_checker_KHONG_doc_witness():
    """Kiểm bằng HÀNH VI: đổi witness mà kết quả không đổi ⇒ checker không đọc."""
    from app.simulation.semantic_program.geometry_obligations import (
        GEOMETRY_CHECKERS,
    )
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.geometry.kernel import Plane3
    from app.simulation.geometry.section import cross_section
    from tests.geometry.test_section_capability import CHOP, NGANG

    sec = cross_section(CHOP, NGANG(1))
    snap = {"td": sec, "khoi": CHOP, "mp": NGANG(1)}
    for kind in WITNESS_FREE_KINDS:
        fn = GEOMETRY_CHECKERS[kind]
        goc = {"solid": "khoi", "plane": "mp"}
        a = fn(snap, Obligation(kind=kind, container="td", params=goc))
        b = fn(snap, Obligation(kind=kind, container="td",
                                params={**goc, "witness": "bat_ky"}))
        assert a == b, f"`{kind}` đọc witness dù được khai là không có"
