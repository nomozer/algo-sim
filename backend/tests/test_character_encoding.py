# -*- coding: utf-8 -*-
"""M17 W3 — hợp đồng + kiểm định `binary.character_encoding` (BACKEND).

RANH GIỚI: backend CHỈ kiểm định. Không engine, không chuyển nhị phân, không
trace — những thứ đó thuộc frontend (`encoding-module.tsx`, dùng lại `toBase()`
của base_conversion) và được khoá bằng vitest. Vì vậy file này KHÔNG có test nào
về giá trị nhị phân hay timeline.

Bất biến khoá ở đây:
- ngữ pháp ĐÓNG: đúng hai bảng mã, chỉ `text` + `encoding`;
- KHÔNG coercion: `7` ≠ `"7"`, `"utf8"` ≠ `unicode_codepoint`;
- đếm theo CODE POINT (Python lặp chuỗi theo code point);
- surrogate và ngoài BMP bị từ chối, KHÔNG thay thế ký tự;
- spec KHÔNG mang kết quả (R0);
- thiếu ký tự/bảng mã ⇒ cổng đủ-dữ-kiện chặn, hệ KHÔNG tự chọn.
"""
from __future__ import annotations

import pytest

from app.simulation.character_encoding import (
    ASCII_MAX,
    BMP_MAX,
    ENCODINGS,
    MAX_TEXT_CODE_POINTS,
    SPEC_VERSION,
    encoding_enum,
)
from app.simulation.error_codes import ErrorCode
from app.simulation.input_requirements import (
    APPLICABLE,
    INPUT_REQUIREMENTS,
    InputKind,
    applicability_of,
)
from app.simulation.sufficiency_gate import check_input_sufficiency
from app.validation.character_encoding import validate_character_encoding_config

TARGET = "binary.character_encoding"

# Fixture Unicode dùng ESCAPE SEQUENCE có chủ đích: viết ký tự literal thì
# editor/công cụ có thể lặng lẽ chuẩn hoá và test sẽ đo cái editor, không đo
# engine (đúng lớp artefact phép đo dự án đã dính ở VIS-003).
PRECOMPOSED = "ế"                     # ế — MỘT code point U+1EBF
DECOMPOSED = "ế"          # e + ◌̂ + ◌́ — BA code point
EMOJI = "\U0001F600"                       # 😀 — U+1F600, ngoài BMP
LONE_SURROGATE = "\ud83d"                  # nửa cặp surrogate


def spec(**over) -> dict:
    s = {"spec_version": SPEC_VERSION, "text": "A", "encoding": "ascii"}
    s.update(over)
    return s


def ok(raw) -> dict:
    cfg, err = validate_character_encoding_config(raw)
    assert cfg is not None, f"đáng lẽ hợp lệ nhưng bị từ chối: {err}"
    return cfg


def rejected(raw) -> str:
    cfg, err = validate_character_encoding_config(raw)
    assert cfg is None, "đáng lẽ bị từ chối nhưng lại qua"
    return err


# ══════════════ hợp đồng đóng ══════════════

def test_dung_hai_bang_ma_khong_hon():
    assert set(ENCODINGS) == {"ascii", "unicode_codepoint"}


def test_schema_gemini_dan_xuat_va_toi_gian():
    """Bề mặt LLM chỉ là MỘT chuỗi + MỘT enum — nhỏ nhất dự án từng có."""
    from app.simulation.catalog import CATALOG

    schema = CATALOG[TARGET].config_schema
    props = schema["properties"]
    assert set(schema["required"]) == {"text", "encoding"}
    assert props["encoding"]["enum"] == encoding_enum()
    # KHÔNG có chỗ nào cho LLM nhét kết quả
    for banned in ("code_points", "rows", "binary", "result", "trace"):
        assert banned not in props


@pytest.mark.parametrize("bad", ["utf8", "utf-8", "UTF8", "unicode", "ASCII", "base64", None, 2])
def test_bang_ma_ngoai_enum_bi_tu_choi(bad):
    """KHÔNG coercion: 'utf8' không tự thành unicode_codepoint."""
    err = rejected(spec(encoding=bad))
    assert "ascii" in err and "unicode_codepoint" in err


@pytest.mark.parametrize("bad", [7, None, ["A"], {"ch": "A"}, True])
def test_text_khong_phai_chuoi_bi_tu_choi(bad):
    """Số 7 KHÁC ký tự '7' — đây là điểm nhầm kinh điển của học sinh."""
    err = rejected(spec(text=bad))
    assert "chuỗi" in err


def test_text_rong_bi_tu_choi():
    assert "rỗng" in rejected(spec(text=""))


def test_truong_ngoai_hop_dong_bi_tu_choi():
    err = rejected(spec(bit_width=8))
    assert "không thuộc hợp đồng" in err


# ══════════════ đếm theo CODE POINT ══════════════

def test_qua_gioi_han_ky_tu_bi_tu_choi():
    err = rejected(spec(text="A" * (MAX_TEXT_CODE_POINTS + 1)))
    assert str(MAX_TEXT_CODE_POINTS) in err


def test_dem_theo_code_point_khong_theo_byte():
    """12 ký tự tiếng Việt có dấu vẫn là 12 code point — không tính theo byte."""
    ok(spec(text=PRECOMPOSED * MAX_TEXT_CODE_POINTS, encoding="unicode_codepoint"))


# ══════════════ ASCII ══════════════

@pytest.mark.parametrize("text", ["A", "Tin", "7", " ", "~"])
def test_ascii_hop_le(text):
    cfg = ok(spec(text=text, encoding="ascii"))
    assert cfg["text"] == text, "text bị đổi — hệ không được sửa đề"


def test_ascii_tu_choi_ky_tu_ngoai_bang_KHONG_thay_the():
    """ENC-6: 'ế' ở chế độ ASCII → từ chối; KHÔNG hạ thành 'e', KHÔNG thành '?'."""
    err = rejected(spec(text=PRECOMPOSED, encoding="ascii"))
    assert str(ASCII_MAX) in err
    assert "Unicode" in err, "nên gợi ý chế độ đúng cho học sinh"


# ══════════════ Unicode BMP ══════════════

def test_unicode_precomposed_la_MOT_code_point():
    """ENC-4: U+1EBF = 7871 — một code point, KHÔNG normalize."""
    cfg = ok(spec(text=PRECOMPOSED, encoding="unicode_codepoint"))
    assert cfg["text"] == PRECOMPOSED
    assert len(cfg["text"]) == 1
    assert ord(cfg["text"]) == 0x1EBF == 7871


def test_unicode_decomposed_giu_nguyen_BA_code_point():
    """ENC-5: hệ KHÔNG được tự gộp 3 code point thành U+1EBF."""
    cfg = ok(spec(text=DECOMPOSED, encoding="unicode_codepoint"))
    assert cfg["text"] == DECOMPOSED
    assert [ord(c) for c in cfg["text"]] == [0x0065, 0x0302, 0x0301]
    assert cfg["text"] != PRECOMPOSED, "đã bị normalize — vi phạm hợp đồng"


def test_emoji_ngoai_BMP_bi_tu_choi():
    """ENC-7. Python đếm 1 code point; JS đếm 2 UTF-16 unit — cả hai phía đều
    phải TỪ CHỐI (phía FE khoá riêng ở vitest)."""
    assert len(EMOJI) == 1 and ord(EMOJI) > BMP_MAX
    err = rejected(spec(text=EMOJI, encoding="unicode_codepoint"))
    assert "emoji" in err.lower() or str(BMP_MAX) in err


def test_surrogate_don_le_bi_tu_choi():
    err = rejected(spec(text=LONE_SURROGATE, encoding="unicode_codepoint"))
    assert "surrogate" in err.lower() or "hoàn chỉnh" in err


# ══════════════ R0 ══════════════

@pytest.mark.parametrize("key", ["code_points", "binary_values", "rows", "result", "trace"])
def test_spec_mang_ket_qua_bi_tu_choi(key):
    err = rejected(spec(**{key: [65]}))
    assert "KHÔNG được chứa kết quả" in err


def test_ca_hop_le_tra_config_sach():
    cfg = ok(spec())
    assert set(cfg) == {"spec_version", "text", "encoding"}
    assert cfg["spec_version"] == SPEC_VERSION


# ══════════════ cổng đủ dữ kiện ══════════════

def test_target_khai_hop_dong_du_kien():
    req = INPUT_REQUIREMENTS[TARGET]
    assert req.required_grounded_inputs == (InputKind.TEXT_AND_ENCODING,)
    assert applicability_of(TARGET)[0] == APPLICABLE


def test_de_khong_neu_ky_tu_va_bang_ma_thi_bi_chan():
    """"Hãy mô phỏng mã hoá ký tự." — nêu chủ đề nhưng KHÔNG nêu ký tự nào."""
    analysis = {"objects": ["mã hoá ký tự"], "data": [], "relations": [],
                "constraints": [], "goal": "Mô phỏng mã hoá ký tự"}
    verdict = check_input_sufficiency(analysis, TARGET)
    assert verdict is not None, "đề trống mà vẫn qua ⇒ nguy cơ hệ tự chọn ký tự"
    assert verdict[0] == ErrorCode.INPUT_INSUFFICIENT
    assert InputKind.TEXT_AND_ENCODING.value in verdict[2]["missing_inputs"]


def test_de_neu_du_ky_tu_va_bang_ma_thi_qua_cong():
    analysis = {"objects": ["ký tự 'A'", "bảng mã ASCII"], "data": [],
                "relations": [], "constraints": [], "goal": "Tra mã ASCII của ký tự 'A'"}
    assert check_input_sufficiency(analysis, TARGET) is None


def test_thong_diep_hoc_sinh_doi_du_hai_thu_va_khong_lo_ky_thuat():
    msg = INPUT_REQUIREMENTS[TARGET].learner_prompt_template
    assert "ký tự" in msg and "bảng mã" in msg
    assert "không tự chọn" in msg
    for token in ("InputKind", "TEXT_AND_ENCODING", TARGET, "insufficient", "None"):
        assert token not in msg


# ══════════════ ownership ══════════════

def test_target_thuoc_family_cu_va_so_huu_dung_co_che_moi():
    """Không tạo family thứ 12; cơ chế đổi cơ số vẫn thuộc base_conversion."""
    from app.simulation.catalog import CATALOG
    from app.simulation.descriptor import FamilyId

    spec_ = CATALOG[TARGET]
    fams = {m.family_id.value for m in spec_.family_memberships}
    assert fams == {FamilyId.POSITIONAL_REPRESENTATION.value}
    owned = {m for mb in spec_.family_memberships for m in mb.owned_mechanisms}
    assert owned == {"positional_representation.character_code_mapping"}
    assert "positional_representation.non_binary_base" not in owned, (
        "không được giành quyền sở hữu cơ chế đổi cơ số của base_conversion")


def test_backend_KHONG_co_engine_ma_hoa():
    """Ranh giới kiến trúc W3: backend chỉ kiểm định. Nếu ai đó thêm hàm chuyển
    số sang nhị phân ở backend thì đó là bộ chuyển đổi THỨ HAI — test này đỏ."""
    import app.simulation.character_encoding as ce
    import app.validation.character_encoding as vce

    for mod in (ce, vce):
        src = open(mod.__file__, encoding="utf-8").read()
        for banned in ("def to_base", "def to_binary", "bin(", "format(", "% 2"):
            assert banned not in src, f"{mod.__name__} có dấu hiệu tự chuyển đổi: {banned}"
