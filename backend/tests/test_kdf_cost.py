# -*- coding: utf-8 -*-
"""W8 §18 — MỨC KDF CỦA PRODUCTION KHÔNG ĐƯỢC HẠ.

`conftest.py` hạ số vòng PBKDF2 xuống 1.000 cho mọi test để suite không phải
trả 365ms mỗi lần băm. Đó là tối ưu HẠ TẦNG TEST, và nó chỉ an toàn khi có một
chỗ khoá lại mức thật — nếu không, một ngày nào đó ai đó hạ luôn hằng số
production và không test nào kêu.

File này là chỗ khoá ấy. Nó mang marker `real_kdf_cost` nên KHÔNG đi qua fixture
hạ chi phí.
"""

import pytest

from app.accounts.passwords import DEFAULT_ITERATIONS, hash_password, verify_password

pytestmark = pytest.mark.real_kdf_cost


def test_kdf_cost_production_khong_bi_ha():
    """OWASP 2023 khuyến nghị ≥ 600.000 vòng cho PBKDF2-HMAC-SHA256."""
    assert DEFAULT_ITERATIONS >= 600_000, (
        "Số vòng PBKDF2 của production đã bị hạ. Nếu đây là tối ưu tốc độ TEST "
        "thì chỗ đúng là fixture `cheap_kdf` trong conftest, không phải hằng số này."
    )


def test_hash_thuc_te_dung_dung_so_vong_da_khai():
    """Chuỗi lưu phải TỰ MÔ TẢ số vòng — đó là thứ khiến hạ vòng trong test an toàn."""
    stored = hash_password("Admin@123")
    algo, iterations, salt, digest = stored.split("$")
    assert algo == "pbkdf2_sha256"
    assert int(iterations) == DEFAULT_ITERATIONS
    assert len(salt) == 32 and len(digest) == 64
    assert verify_password("Admin@123", stored)


def test_hash_so_vong_THAP_van_verify_duoc():
    """Hash cũ (hoặc hash sinh trong test) phải verify được ở mọi số vòng.

    Đây chính là tính chất cho phép fixture `cheap_kdf` tồn tại mà không làm
    hỏng dữ liệu thật: `verify_password` đọc số vòng TỪ CHUỖI LƯU.
    """
    cheap = hash_password("Admin@123", iterations=1_000)
    assert verify_password("Admin@123", cheap)
    assert not verify_password("sai-mat-khau", cheap)
    assert int(cheap.split("$")[1]) == 1_000
