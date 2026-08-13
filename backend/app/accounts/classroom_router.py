"""HTTP cho BÀI THỰC HÀNH + QUAN SÁT LỚP.

Tách khỏi `router.py` (danh tính/lớp) vì đây là chỗ tầng lớp học chạm vào tầng
mô phỏng, và ranh giới đó đáng có một file riêng để đọc.

Bất biến trung tâm của file này (#28): **chữ của giáo viên không bao giờ thành
sự thật runtime**. Giao bài = giao một envelope ĐÃ ĐI QUA `SimSpec.validate` —
đúng cổng mà pipeline LLM đi. Lời dặn của giáo viên là chữ hiển thị cạnh mô
phỏng, không phải tham số.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..persistence.classroom_models import (
    Assignment,
    ClassMembership,
    Classroom,
    PracticeSession,
    User,
)
from ..simulation.catalog import CATALOG
from .policy import Role, can_observe_class
from .router import Caller, get_caller

router = APIRouter(prefix="/api", tags=["classroom"])

#: Trần kích thước envelope nhận từ client. Bài thực hành là một mô phỏng đã
#: validate, không phải kho chứa — chặn ở biên thay vì để DB nuốt bất cứ thứ gì.
MAX_ENVELOPE_BYTES = 64_000


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validated_envelope(raw: dict) -> tuple[str, str]:
    """Kiểm envelope giáo viên giao. Trả `(simulation_id, envelope_json)`.

    Đây là CỔNG, không phải phép làm sạch: config phải qua đúng
    `SimSpec.validate` của target. Nếu bỏ cổng này thì giáo viên (hoặc bất kỳ ai
    gọi được endpoint) giao được một config mà engine không chạy nổi, và lỗi sẽ
    nổ trên màn hình học sinh giữa tiết — đúng ca mà bài tiêm lỗi #4 dựng lại.
    """
    if not isinstance(raw, dict):
        raise HTTPException(400, "Dữ liệu mô phỏng không hợp lệ.")
    sim_id = raw.get("simulation_id")
    if not isinstance(sim_id, str) or sim_id not in CATALOG:
        raise HTTPException(400, "Mô phỏng này không nằm trong danh mục hỗ trợ.")
    if raw.get("status") != "ok":
        raise HTTPException(400, "Chỉ giao được mô phỏng đã phân tích thành công.")
    config, err = CATALOG[sim_id].validate(raw.get("config"))
    if config is None:
        raise HTTPException(400, f"Cấu hình mô phỏng không hợp lệ: {err}")
    # Lưu envelope với config ĐÃ CHUẨN HOÁ, không lưu bản thô của client.
    safe = dict(raw)
    safe["config"] = config
    blob = json.dumps(safe, ensure_ascii=False)
    if len(blob.encode("utf-8")) > MAX_ENVELOPE_BYTES:
        raise HTTPException(413, "Mô phỏng quá lớn để giao cho lớp.")
    return sim_id, blob


def _require_membership(caller: Caller, classroom_id: int) -> None:
    """Học sinh phải LÀ thành viên. Không phải thành viên ⇒ 404, không phải 403:
    người ngoài không cần biết lớp đó có tồn tại hay không."""
    row = caller.db.execute(
        select(ClassMembership).where(
            ClassMembership.classroom_id == classroom_id,
            ClassMembership.student_id == caller.user_id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Không tìm thấy bài thực hành.")


def _assignment_public(a: Assignment, *, with_envelope: bool) -> dict:
    out = {
        "id": a.id, "classroomId": a.classroom_id, "title": a.title,
        "instruction": a.instruction, "simulationId": a.simulation_id,
        "closed": bool(a.closed), "createdAt": a.created_at.isoformat(),
    }
    if with_envelope:
        out["envelope"] = json.loads(a.envelope_json)
    return out


# ── GIAO BÀI ─────────────────────────────────────────────────────────────────

class AssignBody(BaseModel):
    classroomId: int
    title: str = Field(min_length=1, max_length=200)
    instruction: str = ""
    envelope: dict


@router.post("/assignments")
def create_assignment(body: AssignBody, caller: Caller = Depends(get_caller)):
    teacher = caller.require_role(Role.TEACHER)
    c = caller.db.get(Classroom, body.classroomId)
    if c is None or c.teacher_id != teacher.id:
        raise HTTPException(404, "Không tìm thấy lớp.")
    sim_id, blob = _validated_envelope(body.envelope)
    a = Assignment(
        classroom_id=c.id, created_by=teacher.id,
        title=body.title.strip()[:200], instruction=(body.instruction or "").strip()[:4000],
        simulation_id=sim_id, envelope_json=blob,
    )
    caller.db.add(a)
    caller.db.flush()
    return _assignment_public(a, with_envelope=False)


@router.get("/assignments")
def list_assignments(caller: Caller = Depends(get_caller)):
    """Bài của TÔI. Giáo viên: bài mình giao. Học sinh: bài của lớp mình đã vào.

    Đây là chỗ bài tiêm lỗi #5 canh: học sinh KHÔNG được thấy bài của lớp mình
    không thuộc về, kể cả khi đoán đúng id.
    """
    user = caller.require_user()
    if Role(user.role) is Role.TEACHER:
        rows = caller.db.execute(
            select(Assignment).join(Classroom, Classroom.id == Assignment.classroom_id)
            .where(Classroom.teacher_id == user.id)
            .order_by(Assignment.created_at.desc())
        ).scalars().all()
    else:
        rows = caller.db.execute(
            select(Assignment)
            .join(ClassMembership, ClassMembership.classroom_id == Assignment.classroom_id)
            .where(ClassMembership.student_id == user.id, Assignment.closed == False)  # noqa: E712
            .order_by(Assignment.created_at.desc())
        ).scalars().all()
    # Trạng thái thực hành của CHÍNH học sinh này, để "tiếp tục ở nhà" có chỗ bám.
    mine = {
        p.assignment_id: p for p in caller.db.execute(
            select(PracticeSession).where(PracticeSession.student_id == user.id)
        ).scalars().all()
    }
    out = []
    for a in rows:
        item = _assignment_public(a, with_envelope=False)
        p = mine.get(a.id)
        item["myPractice"] = None if p is None else {
            "cursor": p.cursor, "stepCount": p.step_count,
            "completed": bool(p.completed), "updatedAt": p.updated_at.isoformat(),
        }
        out.append(item)
    return {"assignments": out}


@router.get("/assignments/{assignment_id}")
def open_assignment(assignment_id: int, caller: Caller = Depends(get_caller)):
    """Mở bài — trả envelope ĐÃ VALIDATE để frontend nạp thẳng, KHÔNG gọi LLM."""
    user = caller.require_user()
    a = caller.db.get(Assignment, assignment_id)
    if a is None:
        raise HTTPException(404, "Không tìm thấy bài thực hành.")
    c = caller.db.get(Classroom, a.classroom_id)
    if Role(user.role) is Role.TEACHER:
        if c is None or c.teacher_id != user.id:
            raise HTTPException(404, "Không tìm thấy bài thực hành.")
    else:
        _require_membership(caller, a.classroom_id)
        if a.closed:
            raise HTTPException(410, "Bài thực hành này đã đóng.")
    return _assignment_public(a, with_envelope=True)


# ── THỰC HÀNH ────────────────────────────────────────────────────────────────

class ProgressBody(BaseModel):
    """Bằng chứng thực hành CÓ CẤU TRÚC — `§19`/`§21`.

    Không có chỗ nào nhận ảnh màn hình, DOM, hay state của renderer. Các trường
    ở đây là bản sao ĐỂ ĐỌC của những gì engine đã sở hữu.
    """

    cursor: int = 0
    stepCount: int = 0
    exploreOpen: bool = False
    challengeOpen: bool = False
    actionCount: int = 0
    commitmentCount: int = 0
    completed: bool = False


@router.post("/assignments/{assignment_id}/progress")
def report_progress(assignment_id: int, body: ProgressBody,
                    caller: Caller = Depends(get_caller)):
    """Học sinh báo tiến độ. Idempotent theo (bài, học sinh).

    Các con số bị KẸP về miền hợp lệ thay vì tin client: một trình duyệt bị sửa
    có thể gửi `cursor: 999999`, và bảng quan sát của giáo viên không được phép
    hiển thị một con số mà timeline không có.
    """
    student = caller.require_role(Role.STUDENT)
    a = caller.db.get(Assignment, assignment_id)
    if a is None:
        raise HTTPException(404, "Không tìm thấy bài thực hành.")
    _require_membership(caller, a.classroom_id)

    row = caller.db.execute(
        select(PracticeSession).where(
            PracticeSession.assignment_id == assignment_id,
            PracticeSession.student_id == student.id)
    ).scalar_one_or_none()
    if row is None:
        # Đặt số 0 TƯỜNG MINH: `default=` của SQLAlchemy chỉ chạy lúc INSERT,
        # nên đọc `row.action_count` trước khi flush sẽ ra `None` và phép
        # `max()` ngay dưới nổ TypeError. Bug này do test bắt được, không phải
        # phòng xa.
        row = PracticeSession(
            assignment_id=assignment_id, student_id=student.id,
            simulation_id=a.simulation_id, cursor=0, step_count=0,
            action_count=0, commitment_count=0,
            explore_open=False, challenge_open=False, completed=False)
        caller.db.add(row)

    steps = max(0, min(int(body.stepCount), 100_000))
    row.step_count = steps
    row.cursor = max(0, min(int(body.cursor), steps if steps else 100_000))
    row.explore_open = bool(body.exploreOpen)
    row.challenge_open = bool(body.challengeOpen)
    # Đếm chỉ TĂNG: một lượt tải lại trang không được xoá bằng chứng đã có.
    row.action_count = max(row.action_count, max(0, min(int(body.actionCount), 1_000_000)))
    row.commitment_count = max(
        row.commitment_count, max(0, min(int(body.commitmentCount), 100_000)))
    row.completed = bool(body.completed) or row.completed
    row.updated_at = _now()
    caller.db.flush()
    return {"ok": True, "cursor": row.cursor, "completed": bool(row.completed)}


# ── QUAN SÁT ─────────────────────────────────────────────────────────────────

@router.get("/classes/{class_id}/observe")
def observe_class(class_id: int, caller: Caller = Depends(get_caller)):
    """Bảng quan sát lớp — CHỈ giáo viên sở hữu lớp (`§23`).

    Trả về TRẠNG THÁI CÓ CẤU TRÚC, không phải màn hình học sinh (`§21`). Không
    trường nào ở đây nói học sinh đúng hay sai: engine tất định là nơi duy nhất
    phán điều đó (bất biến #27), còn bảng này chỉ nói em ấy đang ở đâu.

    Cũng không rò dữ liệu ngoài lớp: chỉ đọc `PracticeSession` của các bài THUỘC
    lớp này, không đọc lịch sử tự luyện của học sinh (bài tiêm lỗi #7).
    """
    caller.require_user()
    c = caller.db.get(Classroom, class_id)
    if c is None:
        raise HTTPException(404, "Không tìm thấy lớp.")
    if not can_observe_class(viewer_role=caller.role, viewer_id=caller.user_id,
                             class_teacher_id=c.teacher_id):
        raise HTTPException(403, "Bạn không quản lý lớp này.")

    assignments = caller.db.execute(
        select(Assignment).where(Assignment.classroom_id == class_id)
        .order_by(Assignment.created_at.desc())
    ).scalars().all()
    students = caller.db.execute(
        select(User).join(ClassMembership, ClassMembership.student_id == User.id)
        .where(ClassMembership.classroom_id == class_id).order_by(User.display_name)
    ).scalars().all()
    assignment_ids = [a.id for a in assignments]
    practices = [] if not assignment_ids else caller.db.execute(
        select(PracticeSession).where(PracticeSession.assignment_id.in_(assignment_ids))
    ).scalars().all()
    by_key = {(p.student_id, p.assignment_id): p for p in practices}

    rows = []
    for s in students:
        for a in assignments:
            p = by_key.get((s.id, a.id))
            rows.append({
                "studentId": s.id,
                "studentName": s.display_name,
                "assignmentId": a.id,
                "assignmentTitle": a.title,
                "simulationId": a.simulation_id,
                # "chưa bắt đầu" là một trạng thái THẬT, không phải dữ liệu thiếu.
                "status": "not_started" if p is None
                          else ("completed" if p.completed else "practicing"),
                "cursor": None if p is None else p.cursor,
                "stepCount": None if p is None else p.step_count,
                "exploreOpen": None if p is None else bool(p.explore_open),
                "challengeOpen": None if p is None else bool(p.challenge_open),
                "actionCount": None if p is None else p.action_count,
                "commitmentCount": None if p is None else p.commitment_count,
                "updatedAt": None if p is None else p.updated_at.isoformat(),
            })
    return {
        "classroom": {"id": c.id, "name": c.name},
        "assignments": [_assignment_public(a, with_envelope=False) for a in assignments],
        "rows": rows,
        "observedAt": _now().isoformat(),
    }
