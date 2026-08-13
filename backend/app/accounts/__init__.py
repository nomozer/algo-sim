"""Tài khoản, phiên đăng nhập và quyền — tầng lớp học của AlgoSim.

Ranh giới của gói này (giữ đúng `RULES.md §3a`): nó KHÔNG biết gì về mô phỏng.
Nó trả lời "ai đang gọi" và "được làm gì", rồi dừng lại. Engine tất định vẫn là
nơi duy nhất sở hữu state/timeline/kết quả, và tầng lớp học chỉ ĐỌC bằng chứng
có cấu trúc — nó không bao giờ phán học sinh đúng hay sai (bất biến #27).
"""

from .passwords import hash_password, verify_password, check_password_policy, WeakPasswordError
from .policy import (
    DEFAULT_SIGNUP_ROLE,
    GUEST_TRIAL_LIMIT,
    Entitlement,
    Role,
    RoleEscalationError,
    can_observe_class,
    can_read_class,
    entitlement_for,
    resolve_signup_role,
)

__all__ = [
    "hash_password", "verify_password", "check_password_policy", "WeakPasswordError",
    "DEFAULT_SIGNUP_ROLE", "GUEST_TRIAL_LIMIT", "Entitlement", "Role", "RoleEscalationError",
    "can_observe_class", "can_read_class", "entitlement_for", "resolve_signup_role",
]
