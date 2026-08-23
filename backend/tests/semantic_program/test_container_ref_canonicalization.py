# -*- coding: utf-8 -*-
"""BIÊN CHUẨN HOÁ THAM CHIẾU CONTAINER — cùng luật với `spec_version`.

─── SỰ CỐ ĐO ĐƯỢC (probe E2E sản phẩm, 2026-08-23) ────────────────────────

Đề "kiểm tra chuỗi ngoặc hợp lệ bằng ngăn xếp" đi qua route sinh ngữ nghĩa THẬT
(`semantic_route=serve`), dựng được nghĩa vụ `membership(chuoi_ngoac,
witness=is_valid)`, rồi chết ở schema với **4 lỗi cùng MỘT lớp**:

    statements.1.for_each.body.0.if.condition.contains.container
      Input should be a valid string
      input_value = {'kind': 'var', 'name': 'opening_brackets'}

LLM viết `container: {"kind": "var", "name": "stack"}`; schema đòi
`container: "stack"`. Hai cách viết CÙNG MỘT tham chiếu.

Lớp lỗi này cũng có mặt trong dữ liệu SEALED `7e5df014…` (nhóm
`container_nhận_biểu_thức`), đứng ngay sau `spec_version` về số case bị giết.

─── LUẬT, VÀ RANH GIỚI KHÔNG ĐƯỢC VƯỢT ────────────────────────────────────

Nhận `{"kind": "var", "name": X}` ở biên, chuẩn hoá thành `X`. **Chỉ `var`.**

Mọi biểu thức khác — `index`, `arith`, `length`, `map_get`… — vẫn phải bị TỪ
CHỐI. Container là một TÊN, không phải một biểu thức cần tính; nếu nới tới mức
nhận biểu thức thì interpreter sẽ phải đánh giá nó để biết đang thao tác trên
vùng nhớ nào, và đó là một ngữ nghĩa khác hẳn — không phải thứ bản vá này được
phép mở.
"""
import pytest
from pydantic import ValidationError

from app.simulation.semantic_program.contract import (
    ContainsCond,
    IndexRefExpr,
    IsEmptyCond,
    LengthExpr,
    MapGetExpr,
    PeekExpr,
    PopStmt,
    PushStmt,
    SwapStmt,
)

VAR = {"kind": "var", "name": "stack"}


class TestNhanCaHaiCachViet:
    def test_chuoi_tran_van_qua(self):
        assert IsEmptyCond(kind="is_empty", container="stack").container == "stack"

    @pytest.mark.parametrize(
        "dung",
        [
            lambda c: IsEmptyCond(kind="is_empty", container=c),
            lambda c: LengthExpr(kind="length", container=c),
            lambda c: PeekExpr(kind="peek", container=c),
            lambda c: PopStmt(kind="pop", container=c),
        ],
    )
    def test_tham_chieu_bien_duoc_chuan_hoa_thanh_ten(self, dung):
        m = dung(VAR)
        assert m.container == "stack"
        assert isinstance(m.container, str)

    def test_contains_dung_hinh_dang_da_giet_bai_stack(self):
        m = ContainsCond(
            kind="contains",
            container={"kind": "var", "name": "opening_brackets"},
            item={"kind": "literal", "value": "("},
        )
        assert m.container == "opening_brackets"

    def test_map_get_va_index_cung_luat(self):
        assert MapGetExpr(kind="map_get", container=VAR,
                          key={"kind": "literal", "value": 1}).container == "stack"
        assert IndexRefExpr(kind="index", container=VAR,
                            index={"kind": "literal", "value": 0}).container == "stack"

    def test_push_va_swap_cung_luat(self):
        assert PushStmt(kind="push", container=VAR,
                        val={"kind": "literal", "value": 1}).container == "stack"
        assert SwapStmt(kind="swap", container=VAR,
                        idx_a={"kind": "literal", "value": 0},
                        idx_b={"kind": "literal", "value": 1}).container == "stack"


class TestKHONGDuocNoiThanhNhanBieuThuc:
    """Ranh giới. Container là TÊN, không phải biểu thức cần tính."""

    @pytest.mark.parametrize(
        "bieu_thuc",
        [
            {"kind": "index", "container": "a", "index": {"kind": "literal", "value": 0}},
            {"kind": "length", "container": "a"},
            {"kind": "arith", "op": "add", "left": {"kind": "literal", "value": 1},
             "right": {"kind": "literal", "value": 2}},
            {"kind": "map_get", "container": "m", "key": {"kind": "literal", "value": 1}},
            {"kind": "literal", "value": "stack"},
        ],
    )
    def test_bieu_thuc_khac_var_van_bi_tu_choi(self, bieu_thuc):
        with pytest.raises(ValidationError):
            IsEmptyCond(kind="is_empty", container=bieu_thuc)

    @pytest.mark.parametrize(
        "rac",
        [
            {"kind": "var"},          # thiếu name
            {"name": "stack"},        # thiếu kind
            {"kind": "var", "name": 5},  # name không phải chuỗi
            {"kind": "var", "name": ""},  # tên rỗng
            [],
            42,
            None,
        ],
    )
    def test_rac_van_bi_tu_choi(self, rac):
        with pytest.raises(ValidationError):
            IsEmptyCond(kind="is_empty", container=rac)
