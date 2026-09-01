# -*- coding: utf-8 -*-
"""WAVE 1 sau Phase 7B — họ GÓC chết ở cổng phạm vi.

Phase 7B chính thức: hai ô A09 (góc đường–đường) và A10 (góc đường–mặt) dừng
ở `stage_reached = "scope"` với **0 nghĩa vụ**, 3/3 lượt mỗi ô — đề bị loại
TRƯỚC khi tầng sinh có cơ hội nào.

─── VÌ SAO ĐỀ Ở ĐÂY LÀ DEV TỰ SOẠN ───────────────────────────────────────

Taxonomy của lượt chính thức được phép **dẫn đường** (*"họ GÓC hỏng"*),
nhưng bằng chứng sửa phải độc lập: lấy chính 20 đề held-out làm ca hồi quy
thì tập đo biến thành tập DEV **không hoàn tác được**, và mọi lượt đo sau
trên chúng sẽ đo một hệ đã được vá theo chúng. Nên mọi đề dưới đây do wave
này viết ra, và `test_phase7b_baseline_immutable` khoá điều đó.

─── NGUYÊN NHÂN GỐC ──────────────────────────────────────────────────────

Cổng phạm vi (`pipeline._semantic_route`) CÓ ngoại lệ cho hình học, nhưng nó
chỉ áp khi bộ dò tất định `detect_domain` nói `hinh_hoc`. Bộ dò xếp bằng
chứng làm ba mức: cụm MẠNH ⇒ hình học ngay · dấu hiệu Tin học ⇒ phủ quyết ·
≥3 cụm YẾU ⇒ hình học.

**`hình lập phương` không có trong danh sách cụm MẠNH** — khối phổ biến nhất
của hình học không gian THPT, và là khối mà bốn ô `BANG_O` (A06 · A08 · A09 ·
A10) dùng. Một đề góc trên hình lập phương chỉ gom được hai cụm yếu
(`góc giữa`, `đường thẳng`), dưới ngưỡng ba ⇒ `tin_hoc` ⇒ ngoại lệ không áp ⇒
cổng phán `gate_out_of_scope` và trả về học sinh tấm thẻ *"bài này thuộc môn
khác"*, cho một đề nằm đúng giữa chương trình Toán 11.

Đây **không phải nới năng lực**: nó sửa chỗ lệch giữa năng lực đã đóng băng
và đường nhận diện. Cả bốn ô ấy vốn đã nằm trong `BANG_O`.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.domain_profile import (
    DOMAIN_HINH_HOC,
    DOMAIN_TIN_HOC,
    detect_domain,
)

#: Đề DEV, wave này tự viết. Nhiều cách diễn đạt tiếng Việt cho CÙNG một năng
#: lực đã có: `cos²` cho đường–đường, `sin²` cho đường–mặt.
GOC_DUONG_DUONG = (
    "Cho hình lập phương ABCD.A1B1C1D1 cạnh a. Tính góc giữa hai đường thẳng "
    "AC và B1C1.",
    "Cho hình lập phương ABCD.A1B1C1D1. Tính côsin của góc giữa AB1 và BC1.",
    "Cho khối lập phương ABCD.A1B1C1D1. Số đo góc giữa AD1 và BC bằng bao nhiêu?",
    "Cho hình lập phương ABCD.A1B1C1D1 cạnh 2. Hai đường thẳng AC và DC1 hợp "
    "với nhau một góc bằng bao nhiêu?",
)
GOC_DUONG_MAT = (
    "Cho hình lập phương ABCD.A1B1C1D1. Tính sin của góc giữa đường thẳng AC1 "
    "và mặt phẳng (ABCD).",
    "Cho hình lập phương ABCD.A1B1C1D1 cạnh 2. Góc giữa CD1 và mặt đáy bằng "
    "bao nhiêu?",
    "Cho khối lập phương ABCD.A1B1C1D1. Tính góc giữa A1C và mặt (BCC1B1).",
)
#: Đề Tin học có mượn từ vựng hình học — PHẢI ở nguyên `tin_hoc`. Chúng là
#: nửa kia của phép sửa: thêm cụm mạnh mà kéo nhầm nhóm này thì đổi một lỗi
#: lấy một lỗi khác, và lỗi mới giáng xuống đề Tin học hợp lệ.
TIN_HOC = (
    "Viết chương trình nhập vào toạ độ các đỉnh của một hình lập phương và "
    "tính thể tích của nó.",
    "Cho mảng toạ độ các điểm. Viết thuật toán tìm hai điểm tạo với gốc toạ độ "
    "một góc lớn nhất.",
    "Viết chương trình duyệt đồ thị hình khối lập phương bằng BFS và in ra số "
    "đỉnh thăm được.",
)


@pytest.mark.parametrize("de", GOC_DUONG_DUONG + GOC_DUONG_MAT)
def test_de_GOC_tren_hinh_lap_phuong_phai_vao_mien_hinh_hoc(de):
    """Đo được ở Phase 7B: 3/6 đề dạng này rơi `tin_hoc` ⇒ chết ở cổng phạm vi."""
    assert detect_domain(de) == DOMAIN_HINH_HOC, de


@pytest.mark.parametrize("de", TIN_HOC)
def test_de_TIN_HOC_muon_tu_vung_hinh_hoc_van_o_nguyen_tin_hoc(de):
    assert detect_domain(de) == DOMAIN_TIN_HOC, de


#: Lỗ CÓ TỪ TRƯỚC đợt bổ sung `hình lập phương`, đo được 2026-08-29: cụm MẠNH
#: kiểm trước phủ quyết Tin học, nên một danh từ khối kéo được cả đề Tin học
#: hợp lệ sang hình học. Đợt bổ sung chỉ làm nó dễ trúng hơn.
TIN_HOC_CO_DANH_TU_KHOI = (
    "Viết chương trình tính thể tích hình chóp tam giác đều.",
    "Viết chương trình duyệt đồ thị lăng trụ bằng BFS.",
    "Cho mảng các mặt cầu, viết thuật toán đếm số cặp giao nhau.",
)


@pytest.mark.parametrize("de", TIN_HOC_CO_DANH_TU_KHOI)
def test_DANH_TU_KHOI_khong_keo_noi_de_TIN_HOC_sang_hinh_hoc(de):
    """Cụm mạnh gọi tên một VẬT; dấu hiệu Tin học gọi tên một VIỆC. Đề hỏi
    *làm gì*, nên bằng chứng về việc phải thắng bằng chứng về vật."""
    assert detect_domain(de) == DOMAIN_TIN_HOC, de


def test_HINH_LAP_PHUONG_la_cum_MANH_khong_phai_cum_yeu():
    """Một mình tên khối đã đủ, không cần gom thêm hai cụm yếu.

    Ngưỡng ba cụm yếu là chỗ hỏng: nó bắt một đề hình học **ngắn** phải nhắc
    tới ba khái niệm mới được nhận, mà đề góc thì thường chỉ có hai.
    """
    from app.simulation.semantic_program.domain_profile import _DAU_HIEU_MANH
    for cum in ("hình lập phương", "khối lập phương"):
        assert cum in _DAU_HIEU_MANH, cum
    assert detect_domain("Cho hình lập phương ABCD.A1B1C1D1.") == DOMAIN_HINH_HOC


def test_cum_MANH_khong_bo_sot_ten_goi_KHAC_cua_khoi_da_co():
    """`hình hộp`/`lăng trụ`/`nón`/`trụ`/`cầu` đã có; biến thể `khối …` thì
    chưa. Cùng một vật, hai cách gọi trong SGK — thiếu một cách là để lại đúng
    cái lỗ vừa vá."""
    from app.simulation.semantic_program.domain_profile import _DAU_HIEU_MANH
    for cum in ("khối hộp", "khối đa diện", "khối cầu", "khối nón", "khối trụ"):
        assert cum in _DAU_HIEU_MANH, cum


def test_cong_pham_vi_KHONG_con_phu_quyet_de_goc(monkeypatch):
    """Cổng thật, không chỉ bộ dò: đề góc phải ĐI QUA được cổng phạm vi.

    ─── VIẾT LẠI SAU LEGACY_INFORMATICS_REMOVAL ───────────────────────────

    Bản cũ dựng một `analysis` Tin học mang `OUT_OF_SCOPE` rồi khẳng định cổng
    `check_scope_and_simulatability` THA cho hình học. Cổng ấy đã gỡ cùng
    đường Tin học — và đó là lý do nó tồn tại: nó chỉ có nhãn cho môn khác.

    Cổng phạm vi của miền hình học nay là `co_duong_thuc_thi`, tất định và 0
    lượt gọi. Mệnh đề cần khoá không đổi: **đề góc phải đi qua được**, dù là
    góc đường–đường hay góc đường–mặt.
    """
    from app.simulation.semantic_program.domain_profile import co_duong_thuc_thi

    for de in GOC_DUONG_DUONG + GOC_DUONG_MAT:
        assert detect_domain(de) == DOMAIN_HINH_HOC, de
        assert co_duong_thuc_thi(de, DOMAIN_HINH_HOC), (
            f"cổng phạm vi vẫn phủ quyết một đề GÓC trong năng lực: {de}")
