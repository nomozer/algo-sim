"""Spec do AI sinh có diễn đạt được BÀI HỌC PHÂN CẤP không — chứng minh HÀNH VI.

─── VÌ SAO TEST NÀY KHÁC `test_web_contract_sync.py` ──────────────────────

File kia hỏi "trường có MẶT ở cả ba tầng không". Câu ấy cần nhưng chưa đủ: một
trường có mặt vẫn có thể bị validator nuốt, bị chuẩn hoá về mặc định, hoặc bị
gộp chung với thuộc tính đoạn văn — và lúc đó bài học vẫn mất.

Nên ở đây dựng một ứng viên ĐÚNG HÌNH DẠNG AI SINH RA, cho chạy qua **đúng
validator production**, rồi hỏi câu thật:

    tiêu đề và đoạn văn có còn là HAI phạm vi kiểu độc lập không?

Đó mới là bài học mà `.trang h1` ≠ `.trang p` tồn tại để dạy, và là thứ đường
sinh đặc tả không nói được cho tới bump 30.
"""
from __future__ import annotations

import pytest

from app.validation.simulation import validate_web_style_config

# Ứng viên AI-shaped: tiêu đề TO và MÀU KHÁC hẳn đoạn văn — nếu hai phạm vi bị
# gộp thì một trong hai cặp giá trị sẽ biến mất sau validate.
AI_CANDIDATE = {
    "heading": "Trang của em",
    "paragraph": "Đoạn văn giới thiệu ngắn.",
    "style": {
        "backgroundColor": "#bfdbfe",
        "headingColor": "#b91c1c",   # đỏ
        "headingSize": 40,           # to
        "color": "#1f2937",          # xám đậm — KHÁC headingColor
        "fontSize": 16,              # nhỏ — KHÁC headingSize
        "padding": 24,
        "borderRadius": 12,
    },
}


@pytest.fixture()
def validated() -> dict:
    cfg, err = validate_web_style_config(AI_CANDIDATE)
    assert err is None, f"ứng viên AI-shaped bị từ chối: {err}"
    assert cfg, "CONTRACT_SOURCE_EMPTY: validator trả config rỗng"
    return cfg


def test_hai_thuoc_tinh_tieu_de_song_sot_qua_validate(validated):
    """Trước bump 30, LLM không khai được hai trường này — nay phải sống sót."""
    style = validated["style"]
    assert style["headingSize"] == 40, "headingSize bị nuốt hoặc bị đặt về mặc định"
    assert style["headingColor"] == "#b91c1c", "headingColor bị nuốt hoặc bị đặt về mặc định"


def test_tieu_de_va_doan_van_la_HAI_pham_vi_doc_lap(validated):
    """Bài học phân cấp: đổi kiểu tiêu đề KHÔNG kéo theo đoạn văn.

    Nếu hai phạm vi bị gộp thì hai khẳng định dưới sẽ bằng nhau — và lúc ấy
    `.trang h1` với `.trang p` chỉ còn là một, tức mất sạch nội dung bài.
    """
    style = validated["style"]
    assert style["headingSize"] != style["fontSize"], "cỡ chữ tiêu đề và đoạn văn bị gộp"
    assert style["headingColor"] != style["color"], "màu chữ tiêu đề và đoạn văn bị gộp"


def test_doi_rieng_kieu_tieu_de_khong_dong_cham_doan_van():
    """Chứng minh ĐỘC LẬP bằng phép thử vi sai, không bằng một lần chụp."""
    base, err = validate_web_style_config(AI_CANDIDATE)
    assert err is None

    doi_tieu_de = {**AI_CANDIDATE, "style": {**AI_CANDIDATE["style"], "headingSize": 24}}
    sau, err = validate_web_style_config(doi_tieu_de)
    assert err is None

    assert sau["style"]["headingSize"] == 24, "đổi headingSize không có tác dụng"
    assert sau["style"]["fontSize"] == base["style"]["fontSize"], (
        "đổi cỡ chữ TIÊU ĐỀ lại làm đổi cỡ chữ ĐOẠN VĂN ⇒ hai phạm vi bị gộp"
    )
    assert sau["style"]["color"] == base["style"]["color"], "đổi tiêu đề làm đổi màu đoạn văn"


def test_doi_rieng_kieu_doan_van_khong_dong_cham_tieu_de():
    """Chiều ngược lại — một phía đúng chưa chứng minh được độc lập."""
    base, _ = validate_web_style_config(AI_CANDIDATE)
    doi_doan, err = validate_web_style_config(
        {**AI_CANDIDATE, "style": {**AI_CANDIDATE["style"], "fontSize": 32}}
    )
    assert err is None
    assert doi_doan["style"]["fontSize"] == 32
    assert doi_doan["style"]["headingSize"] == base["style"]["headingSize"], (
        "đổi cỡ chữ ĐOẠN VĂN lại làm đổi cỡ chữ TIÊU ĐỀ"
    )


def test_van_FAIL_CLOSED_voi_gia_tri_ngoai_mien():
    """Mở rộng bề mặt LLM KHÔNG được nới lỏng cổng kiểm.

    `headingSize` miền [16, 56] — 999 phải bị TỪ CHỐI, không được kẹp im lặng
    về biên (kẹp im lặng dạy học sinh rằng em đã đặt được giá trị đó).
    """
    _, err = validate_web_style_config(
        {**AI_CANDIDATE, "style": {**AI_CANDIDATE["style"], "headingSize": 999}}
    )
    assert err is not None, "headingSize ngoài miền vẫn lọt ⇒ cổng đã bị nới"


def test_van_FAIL_CLOSED_voi_khoa_la():
    """Thêm hai trường hợp lệ không được mở đường cho trường tự do."""
    _, err = validate_web_style_config(
        {**AI_CANDIDATE, "style": {**AI_CANDIDATE["style"], "letterSpacing": 4}}
    )
    assert err is not None, "khoá lạ vẫn lọt ⇒ hợp đồng không còn đóng"
