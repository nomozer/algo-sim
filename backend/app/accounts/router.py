"""HTTP cho tài khoản / lớp học / bài thực hành.

Router MỎNG có chủ đích: nó dịch HTTP ↔ miền và không chứa luật. Mọi phán quyết
quyền nằm ở `policy.py` (hàm thuần, test được không cần FastAPI); mọi truy vấn
nằm ở `service.py`.

Ba luật xuyên suốt file này:

1. **Vai trò do server sở hữu.** Không handler nào đọc `role` từ body để quyết
   quyền — nó đọc từ `User.role` tra bằng token phiên.
2. **Từ chối là 403/404 có chữ tiếng Việt**, không phải im lặng trả rỗng.
3. **Không rò dữ liệu ngoài lớp.** Giáo viên chỉ thấy lớp mình sở hữu; học sinh
   chỉ thấy lớp mình đã vào (`§23`).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..persistence.classroom_models import (
    Assignment,
    AuthSession,
    ClassMembership,
    Classroom,
    PracticeSession,
    User,
)
from ..persistence.db import SessionLocal
from .passwords import WeakPasswordError
from .policy import (
    Role,
    RoleEscalationError,
    can_observe_class,
    entitlement_for,
    resolve_signup_role,
)
from . import service

router = APIRouter(prefix="/api", tags=["accounts"])

#: Cookie phiên. `httponly` để JavaScript của trang không đọc được (giảm hậu quả
#: khi có XSS); `samesite=lax` chặn CSRF cho mọi request đổi trạng thái đến từ
#: site khác mà vẫn cho điều hướng thường hoạt động.
_COOKIE_KW = {"httponly": True, "samesite": "lax", "path": "/"}


# ── PHỤ THUỘC ────────────────────────────────────────────────────────────────

class Caller:
    """Ai đang gọi. `user is None` ⇒ khách."""

    def __init__(self, db, auth: AuthSession, user: User | None):
        self.db = db
        self.auth = auth
        self.user = user

    @property
    def role(self) -> Role | None:
        return Role(self.user.role) if self.user else None

    @property
    def user_id(self) -> int | None:
        return self.user.id if self.user else None

    def require_user(self) -> User:
        if self.user is None:
            raise HTTPException(401, "Em cần đăng nhập để dùng chức năng này.")
        return self.user

    def require_role(self, role: Role) -> User:
        user = self.require_user()
        if Role(user.role) is not role:
            # Câu chữ nói ĐÚNG việc bị chặn, không nói "bạn là ai" — không rò vai trò.
            raise HTTPException(403, "Tài khoản của bạn không có quyền thực hiện việc này.")
        return user


def get_caller(algosim_session: str | None = Cookie(default=None)):
    """Mở transaction + giải danh tính. Dùng làm dependency cho mọi endpoint.

    Phiên KHÔNG tự sinh ở đây: tạo phiên là việc của endpoint có `Response` để
    đặt cookie. Không có phiên ⇒ khách với 0 lượt đã dùng.
    """
    db = SessionLocal()
    try:
        auth = service.load_session(db, algosim_session)
        user = db.get(User, auth.user_id) if (auth and auth.user_id) else None
        yield Caller(db, auth, user)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _ensure_session(db, auth: AuthSession | None, response: Response) -> AuthSession:
    """Có phiên thì dùng lại, chưa có thì mở và đặt cookie."""
    if auth is not None:
        return auth
    fresh = service.new_session(db)
    response.set_cookie(service.SESSION_COOKIE, fresh.token,
                        max_age=int(service.SESSION_TTL.total_seconds()), **_COOKIE_KW)
    return fresh


def _user_public(user: User) -> dict:
    """Hình chiếu CÔNG KHAI của tài khoản. `password_hash` không có mặt ở đây,
    và `test_auth_api.py` khoá điều đó bằng cách quét toàn bộ response."""
    return {
        "id": user.id,
        "email": user.email,
        "displayName": user.display_name,
        "role": user.role,
        "mustChangePassword": bool(user.must_change_password),
    }


def _me_payload(caller: Caller, auth: AuthSession) -> dict:
    ent = entitlement_for(caller.role, guest_trials_used=auth.guest_trials_used)
    return {
        "user": _user_public(caller.user) if caller.user else None,
        "entitlement": {
            "canRunSimulation": ent.can_run_simulation,
            "canPersistHistory": ent.can_persist_history,
            "canJoinClass": ent.can_join_class,
            "canOwnClass": ent.can_own_class,
            "canReceiveAssignment": ent.can_receive_assignment,
            "trialsLeft": ent.trials_left,
        },
    }


# ── DANH TÍNH ────────────────────────────────────────────────────────────────

class RegisterBody(BaseModel):
    email: str
    displayName: str
    password: str
    #: Client GỬI ĐƯỢC, nhưng server KHÔNG TIN — xem `resolve_signup_role`.
    role: str | None = None
    teacherCode: str | None = None


class LoginBody(BaseModel):
    email: str
    password: str


class PasswordBody(BaseModel):
    currentPassword: str
    newPassword: str


@router.get("/auth/me")
def me(response: Response, caller: Caller = Depends(get_caller)):
    """Danh tính + quyền hiện tại. Luôn 200 — khách cũng là một câu trả lời hợp lệ.

    Đây cũng là nơi phiên KHÁCH ra đời, nên đếm lượt dùng thử có chỗ bám ngay từ
    lần đầu mở trang.
    """
    auth = _ensure_session(caller.db, caller.auth, response)
    return _me_payload(caller, auth)


@router.post("/auth/register")
def register(body: RegisterBody, response: Response, caller: Caller = Depends(get_caller)):
    try:
        role = resolve_signup_role(
            body.role,
            teacher_code=body.teacherCode,
            expected_teacher_code=service.teacher_signup_code(),
        )
    except RoleEscalationError as exc:
        raise HTTPException(403, str(exc)) from exc
    try:
        user = service.create_user(
            caller.db, email=body.email, display_name=body.displayName,
            password=body.password, role=role,
        )
    except WeakPasswordError as exc:
        raise HTTPException(400, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    auth = _ensure_session(caller.db, caller.auth, response)
    service.attach_user(caller.db, auth, user)
    caller.user = user
    return _me_payload(caller, auth)


@router.post("/auth/login")
def login(body: LoginBody, response: Response, caller: Caller = Depends(get_caller)):
    user = service.authenticate(caller.db, email=body.email, password=body.password)
    if user is None:
        # MỘT câu cho cả hai ca (email lạ / sai mật khẩu) — không cho dò tài khoản.
        raise HTTPException(401, "Email hoặc mật khẩu không đúng.")
    auth = _ensure_session(caller.db, caller.auth, response)
    service.attach_user(caller.db, auth, user)
    caller.user = user
    return _me_payload(caller, auth)


@router.post("/auth/logout")
def logout(response: Response, caller: Caller = Depends(get_caller)):
    service.end_session(caller.db, caller.auth.token if caller.auth else None)
    response.delete_cookie(service.SESSION_COOKIE, path="/")
    return {"ok": True}


@router.post("/auth/password")
def change_password(body: PasswordBody, caller: Caller = Depends(get_caller)):
    user = caller.require_user()
    if service.authenticate(caller.db, email=user.email, password=body.currentPassword) is None:
        raise HTTPException(400, "Mật khẩu hiện tại không đúng.")
    try:
        service.set_password(caller.db, user, body.newPassword)
    except WeakPasswordError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True}


# ── LỚP ──────────────────────────────────────────────────────────────────────

class CreateClassBody(BaseModel):
    name: str = Field(min_length=1, max_length=160)


class JoinClassBody(BaseModel):
    code: str


def _class_public(c: Classroom, *, include_code: bool) -> dict:
    """Mã lớp CHỈ hiện cho giáo viên sở hữu. Học sinh đã vào lớp không cần thấy
    mã, và không được thấy — mã là lời mời để phát tiếp, không phải thông tin lớp."""
    out = {
        "id": c.id, "name": c.name, "archived": bool(c.archived),
        "createdAt": c.created_at.isoformat(),
    }
    if include_code:
        out["joinCode"] = c.join_code if c.code_active else None
        out["codeActive"] = bool(c.code_active)
    return out


@router.get("/classes")
def list_classes(caller: Caller = Depends(get_caller)):
    """Lớp của TÔI. Giáo viên: lớp mình sở hữu. Học sinh: lớp mình đã vào."""
    user = caller.require_user()
    if Role(user.role) is Role.TEACHER:
        rows = caller.db.execute(
            select(Classroom).where(Classroom.teacher_id == user.id)
            .order_by(Classroom.created_at.desc())
        ).scalars().all()
        return {"classes": [_class_public(c, include_code=True) for c in rows]}
    rows = caller.db.execute(
        select(Classroom).join(ClassMembership, ClassMembership.classroom_id == Classroom.id)
        .where(ClassMembership.student_id == user.id)
        .order_by(Classroom.created_at.desc())
    ).scalars().all()
    return {"classes": [_class_public(c, include_code=False) for c in rows]}


@router.post("/classes")
def create_class(body: CreateClassBody, caller: Caller = Depends(get_caller)):
    teacher = caller.require_role(Role.TEACHER)
    c = Classroom(
        teacher_id=teacher.id,
        name=body.name.strip()[:160],
        join_code=service.generate_join_code(caller.db),
    )
    caller.db.add(c)
    caller.db.flush()
    return _class_public(c, include_code=True)


@router.post("/classes/{class_id}/code")
def regenerate_code(class_id: int, caller: Caller = Depends(get_caller)):
    """Sinh lại mã. Mã cũ chết ngay — đó là cách xử lý khi mã bị phát tán."""
    teacher = caller.require_role(Role.TEACHER)
    c = caller.db.get(Classroom, class_id)
    if c is None or c.teacher_id != teacher.id:
        raise HTTPException(404, "Không tìm thấy lớp.")
    c.join_code = service.generate_join_code(caller.db)
    c.code_active = True
    return _class_public(c, include_code=True)


@router.delete("/classes/{class_id}/code")
def revoke_code(class_id: int, caller: Caller = Depends(get_caller)):
    teacher = caller.require_role(Role.TEACHER)
    c = caller.db.get(Classroom, class_id)
    if c is None or c.teacher_id != teacher.id:
        raise HTTPException(404, "Không tìm thấy lớp.")
    c.code_active = False
    return _class_public(c, include_code=True)


@router.post("/classes/join")
def join_class(body: JoinClassBody, caller: Caller = Depends(get_caller)):
    """Học sinh vào lớp bằng mã. Bốn ca hỏng đều có câu trả lời riêng (`§14`)."""
    student = caller.require_role(Role.STUDENT)
    code = service.normalize_join_code(body.code)
    if not code:
        raise HTTPException(400, "Em chưa nhập mã lớp.")
    c = caller.db.execute(
        select(Classroom).where(Classroom.join_code == code)
    ).scalar_one_or_none()
    if c is None:
        raise HTTPException(404, "Mã lớp không đúng. Em kiểm tra lại giúp cô/thầy nhé.")
    if not c.code_active:
        raise HTTPException(410, "Mã lớp này đã ngừng sử dụng. Em hỏi giáo viên mã mới.")
    if c.archived:
        raise HTTPException(410, "Lớp này đã đóng.")
    already = caller.db.execute(
        select(ClassMembership).where(
            ClassMembership.classroom_id == c.id, ClassMembership.student_id == student.id)
    ).scalar_one_or_none()
    if already is not None:
        # KHÔNG phải lỗi: nói rõ đã ở trong lớp rồi và trả lớp về như thường.
        return {"classroom": _class_public(c, include_code=False), "alreadyMember": True}
    caller.db.add(ClassMembership(classroom_id=c.id, student_id=student.id))
    return {"classroom": _class_public(c, include_code=False), "alreadyMember": False}


@router.get("/classes/{class_id}/members")
def class_members(class_id: int, caller: Caller = Depends(get_caller)):
    """Danh sách học sinh — CHỈ giáo viên sở hữu lớp."""
    caller.require_user()
    c = caller.db.get(Classroom, class_id)
    if c is None:
        raise HTTPException(404, "Không tìm thấy lớp.")
    if not can_observe_class(viewer_role=caller.role, viewer_id=caller.user_id,
                             class_teacher_id=c.teacher_id):
        raise HTTPException(403, "Bạn không quản lý lớp này.")
    rows = caller.db.execute(
        select(User).join(ClassMembership, ClassMembership.student_id == User.id)
        .where(ClassMembership.classroom_id == class_id)
        .order_by(User.display_name)
    ).scalars().all()
    return {"members": [
        {"id": u.id, "displayName": u.display_name, "email": u.email} for u in rows]}
