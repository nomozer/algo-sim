# -*- coding: utf-8 -*-
"""Cổng TĨNH chặn prompt phình — hard-fail build (spec §6.4).

Vì sao cổng nằm ở tầng tĩnh chứ không ở số live: số live nhiễu và tốn tiền, để
nó gác cổng mặc định là vừa đắt vừa hay đỏ oan. Live token regression chỉ BÁO
CÁO. Còn kích thước prompt thì tất định, không tốn call, và đo đúng thứ đang
trôi: mỗi lần vá lỗi bằng cách nhồi thêm một dòng vào prompt.

Chi phí thật của một bản vá prompt gồm HAI phần: prompt to hơn vĩnh viễn, CỘNG
một đợt gọi lại toàn bộ vì sửa `skills/*.md` buộc bump `CACHE_VERSION` (xoá sạch
exact-cache). Cổng này chặn phần thứ nhất.

NGƯỠNG: chốt 2026-08-20 ở mức ~5% trên kích thước hiện tại. Hạ được thì hạ.
TĂNG ngưỡng phải kèm lý do trong commit message — và trước khi tăng, hãy hỏi
luật vừa thêm có mã hoá được xuống schema/validator không (spec §6.3.1).
"""
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parents[1] / "app" / "ai" / "skills"

BUDGET_BYTES: dict[str, int] = {
    "adapt.md": 1500,
    # MIỀN HÌNH HỌC KHÔNG GIAN (2026-08-24). Ngân sách LỚN HƠN
    # `semantic_program.md` (2500) có lý do, không phải vì viết dài tay:
    #
    #   1. Đề hình học **không cho toạ độ**. Prompt phải dạy cách ĐẶT HỆ TOẠ ĐỘ
    #      — thứ không mã hoá được vào schema, và không có nó thì mô hình chọn
    #      hệ tuỳ tiện rồi ra số vô tỉ mà `Fraction` không nhận.
    #   2. Ranh giới R0 ở miền này cần VÍ DỤ ĐỐI CHIẾU đúng/sai, vì cám dỗ tự
    #      điền toạ độ kết quả mạnh hơn hẳn miền thuật toán: model *biết* giao
    #      tuyến là gì và rất muốn nói ra.
    #   3. Bảng "đề hỏi gì → nghĩa vụ nào" cho 8 nghĩa vụ.
    #
    # ⚠️ Ngân sách này KHÔNG phải chỗ để thêm luật mỗi lần một ca hỏng. Luật nào
    # mã hoá được thì để validator/kernel giữ — đó là bài học `RULES §3c`
    # (DEEP_HARDENING) và bằng chứng lượt SEALED #1: 30/40 thất bại là do hợp
    # đồng cứng nhắc, KHÔNG phải do prompt.
    "geometry_program_generator.md": 4800,
    "analyze.md": 6900,
    "classify.md": 4550,
    "edit.md": 3550,
    "explain.md": 1550,
    # Bề mặt `analyze` RIÊNG của route ngữ nghĩa (2026-08-21). Tách khỏi
    # `analyze.md` có chủ đích — trộn vào đó thì mọi đề đi đường module cũng
    # phải trả tiền cho từ vựng nghĩa vụ mà chúng không dùng.
    # 1950 → 2200 (2026-08-23): luật "tham số phân biệt BẮT BUỘC". Đo được trên
    # DEV `dev_01` (tìm max): nghĩa vụ `extremum` phát ra KHÔNG có `cmp`, checker
    # âm thầm hiểu thành `min` rồi báo *"witness = 35, đúng phải là 27"* — kết
    # tội một chương trình ĐÚNG. `cmp` vốn đã có trong schema (nullable) nhưng
    # prompt chưa bao giờ nhắc, nên model không có lý do gì để điền.
    "semantic_analyze.md": 2200,
    # HẠ 2100 → 1800 (2026-08-20). Bản viết lại bỏ phần schema đã cưỡng chế
    # (danh sách statement/expression/primitive) và còn 1.675B, nhỏ hơn bản gốc
    # 1.998B. Ghi lại vì bản nháp đầu của chính lượt này lại PHÌNH lên 2.131B —
    # gỡ enum xong rồi nhồi thêm văn xuôi. Cổng này bắt được, nên nó có ích.
    # NÂNG 1800 → 2500 (2026-08-23). KHÔNG phải nới để nhồi văn xuôi — đúng thứ
    # comment trên cảnh báo. Bốn lượt probe E2E trên đề "kiểm tra chuỗi ngoặc
    # bằng ngăn xếp" (route `serve`, API thật) đo được mỗi luật gỡ đúng một lớp
    # lỗi, số lỗi cú pháp đi 4 → 2 → 1 → 0:
    #   · `container` là TÊN đã khai (literal đặt thẳng ⇒ trỏ vùng nhớ không có)
    #   · `pop`/`dequeue` là CÂU LỆNH có `dest_var`; chỉ `peek` là biểu thức
    #   · chuỗi ĐƯỢC DUYỆT khai `array` ký tự, không khai `str`
    # Đã thử chỗ rẻ hơn trước: thẻ văn phạm (`grammar_card`) VỐN ĐÃ in
    # `pop: container:tên dest_var?:tên` và `container:tên` — tức dữ kiện dẫn
    # xuất có sẵn mà model vẫn viết sai. Thiếu là GỢI Ý CÁCH DÙNG, thứ docstring
    # của chính thẻ xếp về `skills/*.md`. Nên trần đổi, không phải chỗ đặt đổi.
    # 2500 → 2850 (cùng lượt): luật thứ tư — `visual_bindings` phải phủ container
    # BIẾN ĐỘNG và witness của mỗi nghĩa vụ. Đề "đảo dãy bằng ngăn xếp" chạy
    # được (executable, 8 bước) rồi bị `learner_surface` chặn với đúng câu
    # "mô phỏng chạy xong mà học sinh không thấy đáp án". Đây là luật SƯ PHẠM,
    # không mã hoá thành canonicalization được: cổng biết đòi gì, nhưng model
    # chỉ biết sau khi đã trượt.
    "semantic_program.md": 2850,
    "simulate.md": 1450,
    "transcribe.md": 1050,
}


@pytest.mark.parametrize("name,budget", sorted(BUDGET_BYTES.items()))
def test_prompt_khong_vuot_ngan_sach_byte(name, budget):
    actual = (SKILLS / name).stat().st_size
    assert actual <= budget, (
        f"{name} = {actual} byte, vượt ngân sách {budget}. "
        "Luật nào mã hoá được thì chuyển sang schema/validator, đừng nhồi prompt: "
        "luật trong prompt là GỢI Ý, luật trong validator là RÀNG BUỘC."
    )


def test_moi_skill_deu_co_ngan_sach():
    """Thêm skill mới mà quên khai ngân sách ⇒ nó phình tự do, không ai biết."""
    tren_dia = {p.name for p in SKILLS.glob("*.md")}
    thieu = tren_dia - set(BUDGET_BYTES)
    assert not thieu, f"Skill chưa khai ngân sách byte: {sorted(thieu)}"


def test_khong_khai_ngan_sach_cho_skill_da_bien_mat():
    tren_dia = {p.name for p in SKILLS.glob("*.md")}
    thua = set(BUDGET_BYTES) - tren_dia
    assert not thua, f"Ngân sách khai cho skill không còn tồn tại: {sorted(thua)}"
