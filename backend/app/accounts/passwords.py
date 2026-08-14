"""Băm mật khẩu — PBKDF2-HMAC-SHA256 từ THƯ VIỆN CHUẨN.

Vì sao KHÔNG thêm passlib/bcrypt/argon2 (`RULES.md §3` — công cụ phải phục vụ
đề tài, không phải tiện tay): `hashlib.pbkdf2_hmac` là primitive được NIST
khuyến nghị, có sẵn trong CPython, và `hmac.compare_digest` cho so sánh
constant-time. Thêm một dependency mật mã chỉ để có cùng thuật toán là tăng bề
mặt cài đặt mà không tăng an toàn.

Định dạng lưu: `pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>` — tự mô tả,
nên đổi số vòng lặp về sau KHÔNG làm hỏng hash cũ (mỗi bản ghi mang tham số của
chính nó).

Cái file này KHÔNG bao giờ được làm:
  - trả về/ghi log mật khẩu thô hoặc chuỗi hash;
  - so sánh hash bằng `==` (rò rỉ thời gian).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
# OWASP 2023 khuyến nghị ≥ 600.000 vòng cho PBKDF2-HMAC-SHA256.
DEFAULT_ITERATIONS = 600_000
_SALT_BYTES = 16

#: Mật khẩu ngắn hơn mức này bị từ chối ngay ở tầng miền, không đợi UI.
MIN_PASSWORD_LENGTH = 8


class WeakPasswordError(ValueError):
    """Mật khẩu không đạt chính sách tối thiểu."""


def check_password_policy(password: str) -> None:
    """Chính sách tối thiểu. Ném `WeakPasswordError` kèm câu tiếng Việt.

    Cố ý MỎNG: một chính sách phức tạp (bắt buộc ký tự đặc biệt, đổi mật khẩu
    định kỳ) đã được chứng minh là đẩy người dùng sang mật khẩu dễ đoán hơn.
    Độ dài là yếu tố có sức nặng thật.
    """
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise WeakPasswordError(f"Mật khẩu phải có ít nhất {MIN_PASSWORD_LENGTH} ký tự.")


def hash_password(password: str, *, iterations: int | None = None) -> str:
    """Băm mật khẩu kèm salt ngẫu nhiên RIÊNG cho từng tài khoản.

    Salt riêng là thứ khiến một bảng cầu vồng dựng sẵn vô dụng, và khiến hai
    người dùng đặt cùng mật khẩu vẫn cho hai chuỗi hash khác nhau.

    ⚠️ `iterations=None` đọc `DEFAULT_ITERATIONS` LÚC GỌI, không phải lúc định
    nghĩa hàm. Khác biệt nhỏ ấy là thứ cho phép test hạ chi phí KDF xuống mà
    KHÔNG đụng gì tới production: một giá trị mặc định gắn ở chữ ký hàm thì
    monkeypatch hằng số không có tác dụng.

    Vì sao được phép hạ trong test: số vòng được GHI VÀO chính chuỗi lưu
    (`pbkdf2_sha256$<iterations>$…`) và `verify_password` đọc lại từ đó, nên
    hash sinh ở bất kỳ số vòng nào cũng verify được. Thứ test cần chứng minh là
    CƠ CHẾ (có salt riêng, có KDF chậm, không lưu thô), không phải chờ 365ms
    mỗi lần tạo tài khoản. Mức production được khoá riêng bởi
    `test_kdf_cost_production_khong_bi_ha`.
    """
    if iterations is None:
        iterations = DEFAULT_ITERATIONS
    check_password_policy(password)
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{ALGORITHM}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """So mật khẩu với chuỗi đã lưu. Sai định dạng ⇒ `False`, KHÔNG ném lỗi.

    Fail-closed và im lặng có chủ đích: một exception khác nhau giữa "tài khoản
    không tồn tại" và "hash hỏng" là một kênh phân biệt tài khoản.
    """
    if not isinstance(stored, str):
        return False
    parts = stored.split("$")
    if len(parts) != 4 or parts[0] != ALGORITHM:
        return False
    try:
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected = bytes.fromhex(parts[3])
    except (ValueError, TypeError):
        return False
    if iterations <= 0:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    # constant-time: so bằng `==` rò rỉ độ dài tiền tố khớp qua thời gian chạy.
    return hmac.compare_digest(digest, expected)
