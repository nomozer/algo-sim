# -*- coding: utf-8 -*-
"""TASK 4 — C₁a: đo trước, nới sau. **0 API call.**

⚠️ FILE NÀY CỐ Ý **KHÔNG** KHOÁ MỘT BỘ KHỚP NGỮ NGHĨA, và lý do phải đọc kèm.

Đặc tả TASK 4 đề nghị C₁a kiểm "semantic producer" thay cho so tên. Bằng chứng
dẫn tới đề nghị ấy là `geo_02`: nó tạo ra **mọi thứ nó khai** mà C₁a vẫn từ chối,
nên suy ra tên `witness` do `analyze` chọn không nằm trong chương trình.

**Suy ra — không đọc được.** Artifact PHASE 5 lượt 2 không lưu `RequestContract`
(§6 báo cáo), nên tên witness thật là ẩn số. Và ít nhất ba nguyên nhân khác nhau
cùng khớp dấu vết ấy:

  · model bỏ qua chỉ dẫn, dù `_obligations_for_prompt` ĐÃ truyền tên sang kèm
    câu "cả hai tên phải có mặt, đúng từng chữ";
  · `analyze` đặt một `witness` không dùng được làm định danh (từng xảy ra ở
    miền Tin học: `container` = một cụm tiếng Việt);
  · một lỗi khác hẳn, chưa ai nghĩ tới.

Ba nguyên nhân, ba cách sửa. Chọn bừa một là sửa nhầm bệnh — và ở đây "sửa" có
nghĩa là **làm yếu một cổng an toàn**, nên sửa nhầm thì mất luôn khả năng phát
hiện. Thứ tự đúng là: TASK 1 (lưu hợp đồng) → chạy Phase 5.5 → đọc tên thật →
mới thiết kế.

Cái wave này làm: C₁a phát ra **cả hai phía** vào `details`. Cổng không đổi một
milimét; chỉ lượt đo sau đọc được nguyên nhân thay vì suy.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.contract import (
    MemoryDeclaration,
    SemanticProgramSpec,
)
from app.simulation.semantic_program.coverage_gate import (
    _producers,
    check_structural_coverage,
)
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract


def _spec(decls: list[dict], stmts: list[dict]) -> SemanticProgramSpec:
    return SemanticProgramSpec(
        spec_version="1.0",
        title="Kiểm C1a",
        memory_declarations=[MemoryDeclaration(**d) for d in decls],
        statements=stmts,
    )


_DIEM = [{"name": n, "type": "point3"} for n in "ABCDS"]
_DUNG_KHOI = {
    "kind": "construct_solid", "target_var": "chop",
    "vertices": ["A", "B", "C", "D", "S"],
    "faces": [[0, 1, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]],
}
_DO = {"kind": "assign", "target_var": "V",
       "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}}


def _hd(witness: str) -> RequestContract:
    return RequestContract(obligations=(
        Obligation(kind="volume", container="chop", params={"witness": witness}),
    ))


# ══ CỔNG VẪN CHẶN ĐÚNG NHỮNG GÌ NÓ TỪNG CHẶN ═════════════════════════════
def test_co_producer_that_thi_PASS():
    spec = _spec(_DIEM + [{"name": "chop", "type": "solid"},
                          {"name": "V", "type": "float"}],
                 [_DUNG_KHOI, _DO])
    assert check_structural_coverage(_hd("V"), spec).ok


def test_KHONG_co_producer_that_thi_FAIL():
    """Witness được khai báo nhưng không câu lệnh nào ghi vào nó ⇒ chương trình
    KHÔNG có đường tạo ra thứ đề hỏi. Đây là ca C₁a sinh ra để bắt, và Wave 3
    không được làm nó yếu đi."""
    spec = _spec(_DIEM + [{"name": "chop", "type": "solid"},
                          {"name": "V", "type": "float"}],
                 [_DUNG_KHOI])          # thiếu phép đo
    kq = check_structural_coverage(_hd("V"), spec)
    assert not kq.ok and kq.error_code == "REQUESTED_OPERATION_UNCOVERED"


def test_TEN_KHAC_NHAU_van_FAIL_va_do_la_hanh_vi_HIEN_TAI():
    """Ca `geo_02`. Chương trình tạo ra `V`, hợp đồng đòi `the_tich`.

    Test này khoá **hành vi hiện tại**, không khoá một hành vi mong muốn. Nếu
    một wave sau đổi nó thành PASS, wave ấy phải sửa test này **và** nêu bằng
    chứng từ Phase 5.5 rằng đây đúng là nguyên nhân — không phải sửa vì nó tiện.
    """
    spec = _spec(_DIEM + [{"name": "chop", "type": "solid"},
                          {"name": "V", "type": "float"}],
                 [_DUNG_KHOI, _DO])
    kq = check_structural_coverage(_hd("the_tich"), spec)
    assert not kq.ok


# ══ PHẦN WAVE 3 LÀM: DETAILS NÓI ĐỦ HAI PHÍA ═════════════════════════════
def test_details_noi_ca_HAI_PHIA_khi_witness_chua_khai():
    spec = _spec(_DIEM + [{"name": "chop", "type": "solid"},
                          {"name": "V", "type": "float"}],
                 [_DUNG_KHOI, _DO])
    kq = check_structural_coverage(_hd("the_tich"), spec)
    txt = " ".join(kq.missing)
    assert "the_tich" in txt, "phải nói HỢP ĐỒNG đòi tên gì"
    assert "chương trình khai" in txt and "'V'" in txt, "phải nói CHƯƠNG TRÌNH có gì"


def test_details_noi_ca_HAI_PHIA_khi_witness_khai_ma_khong_ai_tao():
    """Phân biệt hai bệnh: *chưa khai báo* (lệch tên) vs *khai mà không ai tạo*
    (thiếu phép dựng). Cùng mã lỗi, khác cách chữa."""
    spec = _spec(_DIEM + [{"name": "chop", "type": "solid"},
                          {"name": "V", "type": "float"}],
                 [_DUNG_KHOI])
    kq = check_structural_coverage(_hd("V"), spec)
    txt = " ".join(kq.missing)
    assert "không có producer hợp lệ" in txt
    assert "được tạo ra" in txt and "chop" in txt


def test_details_noi_hai_phia_khi_CONTAINER_lech():
    """⚠️ TÊN CONTAINER ĐÃ ĐỔI (Phase 6.7.1), và lý do phải đọc kèm.

    Bản cũ dùng `khoi_chop` và nó XANH NHỜ CHÍNH CON BUG mà pha này sửa:
    lưới phụ tố của Phase 6.6 hoà giải `khoi_chop ≡ chop` (`khoi` là một phụ tố
    kiểu hợp lệ), nhưng phép kiểm dẫn xuất tra `ob.container` chứ không tra tên
    đã hoà giải — nên nó vẫn phát ra một thông điệp lệch. Sửa bug đi thì
    `khoi_chop` không còn là ca lệch nữa, và test mất đối tượng.

    Ý ĐỊNH của test không đổi: khi container thật sự KHÔNG phân giải được,
    thông điệp phải nói cả hai phía. Nên đổi sang một tên không lưới nào hoà
    giải nổi.
    """
    spec = _spec(_DIEM + [{"name": "chop", "type": "solid"},
                          {"name": "V", "type": "float"}],
                 [_DUNG_KHOI, _DO])
    hd = RequestContract(obligations=(
        Obligation(kind="volume", container="hinh_lang_tru",
                   params={"witness": "V"}),
    ))
    txt = " ".join(check_structural_coverage(hd, spec).missing)
    assert "hinh_lang_tru" in txt and "chương trình khai" in txt


def test_container_LECH_PHU_TO_nay_HOA_GIAI_duoc():
    """Vế còn lại của cùng một sự thật: `khoi_chop` ≡ `chop` là hoà giải ĐÚNG,
    và trước Phase 6.7.1 nó bị từ chối oan ở phép kiểm dẫn xuất."""
    spec = _spec(_DIEM + [{"name": "chop", "type": "solid"},
                          {"name": "V", "type": "float"}],
                 [_DUNG_KHOI, _DO])
    hd = RequestContract(obligations=(
        Obligation(kind="volume", container="khoi_chop", params={"witness": "V"}),
    ))
    kq = check_structural_coverage(hd, spec)
    assert kq.ok, kq.missing
    assert any("khoi_chop" in d and "chop" in d for d in kq.symbol_reconciled)


# ══ PRODUCER SET ĐÚNG — nền cho mọi thiết kế sau này ══════════════════════
def test_producers_bat_du_moi_phep_dung_hinh_hoc():
    """Bất kỳ bộ khớp "semantic producer" nào sau này cũng dựng trên tập này.
    Tập sai thì bộ khớp sai theo, và sai âm thầm."""
    spec = _spec(
        _DIEM + [{"name": n, "type": t} for n, t in
                 (("chop", "solid"), ("mp", "plane3"), ("d", "line3"),
                  ("M", "point3"), ("td", "polygon3"), ("V", "float"))],
        [_DUNG_KHOI, _DO,
         {"kind": "construct_plane", "target_var": "mp",
          "through": ["A", "B", "C"]},
         {"kind": "construct_line", "target_var": "d",
          "through_a": "A", "through_b": "B"},
         {"kind": "construct_point", "target_var": "M",
          "expr": {"kind": "midpoint", "a": "A", "b": "B"}},
         {"kind": "construct_section", "target_var": "td",
          "solid": "chop", "plane": "mp"}],
    )
    assert _producers(spec.statements) == {"chop", "V", "mp", "d", "M", "td"}


@pytest.mark.parametrize("thieu", ["container", "witness"])
def test_C1a_khong_bo_qua_khi_hop_dong_thieu_truong(thieu):
    spec = _spec(_DIEM + [{"name": "chop", "type": "solid"},
                          {"name": "V", "type": "float"}],
                 [_DUNG_KHOI, _DO])
    params = {} if thieu == "witness" else {"witness": "V"}
    hd = RequestContract(obligations=(
        Obligation(kind="volume",
                   container="chop" if thieu == "witness" else "khong_co",
                   params=params),
    ))
    assert not check_structural_coverage(hd, spec).ok
