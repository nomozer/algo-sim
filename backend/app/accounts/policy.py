"""CHÍNH SÁCH QUYỀN — hàm THUẦN, không chạm DB, không chạm HTTP.

Vì sao tách khỏi router: quyền là thứ phải kiểm được mà không cần dựng
FastAPI, và là thứ dễ trôi nhất khi luật chỉ sống trong một chuỗi `if` giữa
handler. Cùng lý do `interaction-policy.ts` bên frontend là hàm thuần.

Ba luật ở đây, và cả ba đều đã có test tiêm lỗi:
  1. VAI TRÒ do SERVER sở hữu — client gửi `role` gì cũng không đổi được.
  2. Khách (chưa đăng nhập) có ĐÚNG MỘT lượt dùng thử, đếm ở phiên máy chủ.
  3. Giáo viên chỉ quan sát lớp MÌNH sở hữu; học sinh chỉ thấy lớp mình đã vào.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    """Vai trò ĐÓNG. Không có `admin` — hệ chưa có việc gì cho nó làm."""

    STUDENT = "student"
    TEACHER = "teacher"


#: Vai trò MẶC ĐỊNH của đăng ký thường. Một client gửi `role: "teacher"` vào
#: `/api/auth/register` KHÔNG được nâng cấp chính mình — xem `resolve_signup_role`.
DEFAULT_SIGNUP_ROLE = Role.STUDENT

#: Số lượt mô phỏng thử dành cho khách. Đếm ở PHIÊN MÁY CHỦ (bảng `auth_session`),
#: không ở localStorage: một biến boolean phía client thì xoá cache là lại có.
GUEST_TRIAL_LIMIT = 1


class RoleEscalationError(PermissionError):
    """Client cố tự nâng vai trò."""


def resolve_signup_role(requested: str | None, *, teacher_code: str | None,
                        expected_teacher_code: str | None) -> Role:
    """Vai trò khi đăng ký — SERVER quyết, không phải client.

    Đăng ký thường luôn ra HỌC SINH. Muốn tài khoản giáo viên thì phải trình
    đúng `teacher_code` mà người vận hành đặt qua biến môi trường
    `ALGOSIM_TEACHER_SIGNUP_CODE`.

    ⚠️ GIỚI HẠN CÓ CHỦ Ý, ghi rõ ở `docs/CLASSROOM_AUTH_CONTRACT.md`: đây là mã
    mời dùng chung, KHÔNG phải hệ xác minh danh tính giáo viên. Nó đủ để chặn
    việc tự nâng quyền bằng cách sửa một trường JSON, và KHÔNG đủ để chống một
    người đã biết mã. Hệ xác minh thật (trường học cấp, quản trị duyệt) là việc
    ngoài phạm vi đề tài — khai PARTIAL chứ không giả vờ đã có.

    Biến môi trường KHÔNG đặt ⇒ không ai đăng ký được vai trò giáo viên qua
    đường công khai. Fail-closed: thiếu cấu hình thì đóng, không mở.
    """
    if requested is None or requested == Role.STUDENT.value:
        return Role.STUDENT
    if requested != Role.TEACHER.value:
        # Vai trò lạ hoàn toàn ⇒ không đoán, không im lặng hạ về student.
        raise RoleEscalationError("Vai trò không hợp lệ.")
    if not expected_teacher_code:
        raise RoleEscalationError(
            "Hệ thống chưa mở đăng ký tài khoản giáo viên. Liên hệ người quản trị."
        )
    if not teacher_code or teacher_code != expected_teacher_code:
        raise RoleEscalationError("Mã giáo viên không đúng.")
    return Role.TEACHER


@dataclass(frozen=True)
class Entitlement:
    """Được làm gì — dẫn xuất từ danh tính, không lưu trong client."""

    can_run_simulation: bool
    can_persist_history: bool
    can_join_class: bool
    can_own_class: bool
    can_receive_assignment: bool
    #: Còn bao nhiêu lượt thử (chỉ có nghĩa với khách). `None` = không giới hạn.
    trials_left: int | None


def entitlement_for(role: Role | None, *, guest_trials_used: int = 0) -> Entitlement:
    """Quyền của một danh tính. `role is None` = khách chưa đăng nhập.

    Khách được chạy MỘT mô phỏng thật — cùng pipeline production, không phải
    renderer giả — vì không ai đánh giá được sản phẩm qua ảnh chụp màn hình.
    Nhưng khách KHÔNG có lớp, KHÔNG nhận bài, KHÔNG có lịch sử bền.
    """
    if role is None:
        left = max(0, GUEST_TRIAL_LIMIT - guest_trials_used)
        return Entitlement(
            can_run_simulation=left > 0,
            can_persist_history=False,
            can_join_class=False,
            can_own_class=False,
            can_receive_assignment=False,
            trials_left=left,
        )
    return Entitlement(
        can_run_simulation=True,
        can_persist_history=True,
        can_join_class=role is Role.STUDENT,
        can_own_class=role is Role.TEACHER,
        can_receive_assignment=role is Role.STUDENT,
        trials_left=None,
    )


def can_observe_class(*, viewer_role: Role | None, viewer_id: int | None,
                      class_teacher_id: int) -> bool:
    """Ai được xem bảng quan sát của một lớp: ĐÚNG giáo viên sở hữu lớp đó.

    Không có "giáo viên thì xem được mọi lớp" — đó chính là lỗ mà bài kiểm
    uỷ quyền #3 tiêm vào.
    """
    if viewer_role is not Role.TEACHER or viewer_id is None:
        return False
    return viewer_id == class_teacher_id


def can_read_class(*, viewer_role: Role | None, viewer_id: int | None,
                   class_teacher_id: int, member_ids: frozenset[int]) -> bool:
    """Ai được đọc thông tin lớp: giáo viên sở hữu, hoặc học sinh ĐÃ là thành viên."""
    if viewer_id is None:
        return False
    if can_observe_class(viewer_role=viewer_role, viewer_id=viewer_id,
                         class_teacher_id=class_teacher_id):
        return True
    return viewer_role is Role.STUDENT and viewer_id in member_ids
