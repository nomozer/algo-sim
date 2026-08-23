# -*- coding: utf-8 -*-
"""Biên chuẩn hoá `spec_version` — KHÁC BIỆT SERIALIZATION KHÔNG ĐƯỢC CHE MẤT
NĂNG LỰC NGỮ NGHĨA.

─── SỰ CỐ ĐO ĐƯỢC (SEALED 7e5df014…, OFFICIAL Task 12) ────────────────────

17/40 case chết ở `semantic_program_invalid` với **đúng một lỗi duy nhất**:

    spec_version
      Input should be '1.0' [type=literal_error, input_value=1.0, input_type=float]

LLM viết `"spec_version": 1.0` — JSON number. Contract khai `Literal["1.0"]` —
chuỗi. Pydantic fail-closed, vứt CẢ chương trình trước khi xét một chữ nào về
ngữ nghĩa. Hệ quả: A = 3/40 không đo được năng lực, mà đo một cổng cú pháp.

`1.0` và `"1.0"` là hai cách viết **cùng một phiên bản**. Từ chối vì kiểu JSON
không phải fail-closed đúng chỗ — nó là fail-closed nhầm tầng.

─── LUẬT, VÀ VẾ THỨ HAI KHÔNG ĐƯỢC BỎ ────────────────────────────────────

Nhận cả hai cách viết ở biên; ngay sau biên, biểu diễn nội bộ LUÔN là chuỗi
`"1.0"`, nên schema/interpreter phía dưới không bao giờ thấy float.

Nhưng **phiên bản khác 1.0 vẫn phải bị từ chối**. Nới lỏng kiểu KHÔNG được
biến thành nới lỏng phiên bản — nếu không, bản vá này tự tay mở đường cho một
IR sai phiên bản chạy tiếp, đúng thứ mà `Literal` sinh ra để chặn.
"""
import pytest
from pydantic import ValidationError

from app.simulation.semantic_program.contract import SPEC_VERSION, SemanticProgramSpec


def _spec(**ghi_de):
    """Chương trình hợp lệ tối thiểu — chỉ `spec_version` là biến số của test."""
    goc = {
        "title": "Tính tổng dãy số",
        "memory_declarations": [
            {"name": "s", "type": "int", "initial_value": 0},
        ],
        "statements": [
            {
                "kind": "assign",
                "target_var": "s",
                "expr": {"kind": "literal", "value": 1},
            }
        ],
    }
    goc.update(ghi_de)
    return goc


def test_fixture_nen_la_HOP_LE_khi_khong_dong_vao_spec_version():
    """Cọc chống test-âm-giả. Nếu fixture nền tự nó đã hỏng thì mọi
    `pytest.raises(ValidationError)` bên dưới đều xanh mà không chứng minh gì về
    `spec_version` cả — chúng chỉ đang bắt lỗi của chính fixture."""
    m = SemanticProgramSpec.model_validate(_spec())
    assert m.title == "Tính tổng dãy số"


class TestNhanCaHaiCachViet:
    def test_chuoi_1_0_qua(self):
        m = SemanticProgramSpec.model_validate(_spec(spec_version="1.0"))
        assert m.spec_version == "1.0"

    def test_so_float_1_0_duoc_chuan_hoa_thanh_chuoi(self):
        """Đây là đúng 17 case đã chết trên SEALED."""
        m = SemanticProgramSpec.model_validate(_spec(spec_version=1.0))
        assert m.spec_version == "1.0"
        assert isinstance(m.spec_version, str), "Phía dưới biên KHÔNG được thấy float"

    def test_so_int_1_cung_la_cach_viet_cua_cung_phien_ban(self):
        m = SemanticProgramSpec.model_validate(_spec(spec_version=1))
        assert m.spec_version == "1.0"
        assert isinstance(m.spec_version, str)

    def test_vang_mat_thi_dung_mac_dinh(self):
        m = SemanticProgramSpec.model_validate(_spec())
        assert m.spec_version == SPEC_VERSION


class TestPhienBanKhacVanBiTuChoi:
    """Nới kiểu KHÔNG được thành nới phiên bản."""

    @pytest.mark.parametrize(
        "gia_tri",
        [
            "2.0",  # chuỗi, phiên bản khác
            2.0,  # float, phiên bản khác
            2,  # int, phiên bản khác
            "1.1",
            1.1,
            0.9,
        ],
    )
    def test_phien_ban_khac_1_0_bi_tu_choi(self, gia_tri):
        with pytest.raises(ValidationError):
            SemanticProgramSpec.model_validate(_spec(spec_version=gia_tri))

    @pytest.mark.parametrize(
        "gia_tri",
        [
            "v1.0",  # có tiền tố
            "1.0.0",  # ba số
            "",  # rỗng
            "một",  # chữ
            None,  # null tường minh
            [],
            {},
            True,  # bool LÀ subclass của int trong Python — không được lọt qua
            False,
        ],
    )
    def test_gia_tri_di_dang_bi_tu_choi(self, gia_tri):
        with pytest.raises(ValidationError):
            SemanticProgramSpec.model_validate(_spec(spec_version=gia_tri))


def test_thong_bao_loi_van_neu_dung_gia_tri_da_nhan():
    """Từ chối thì phải nói giá trị nào bị từ chối — nếu không, người sửa prompt
    chỉ thấy 'sai phiên bản' mà không biết LLM đã phát ra cái gì."""
    with pytest.raises(ValidationError) as e:
        SemanticProgramSpec.model_validate(_spec(spec_version=2.0))
    assert "2.0" in str(e.value)
