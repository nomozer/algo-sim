"""HTTP cho PHIÊN DẠY TRỰC TIẾP — điều phối lớp, server sở hữu.

Tách khỏi `classroom_router.py` vì hai file trả lời hai câu khác nhau về vòng
đời: ở đó là *"bài này giao cho ai, em ấy làm tới đâu"* (bền, còn lại sau tiết
học); ở đây là *"lớp đang ở đâu NGAY BÂY GIỜ"* (sống trong một tiết).

─── BỐN BẤT BIẾN, VÀ MỖI CÁI CHẶN MỘT LỖI THẬT ────────────────────────────

**① Máy chủ là thẩm quyền.** Không endpoint nào ở đây tin `role`/`teacher_id`
do client gửi. Vai trò đọc từ cột `users.role`; quyền sửa phiên hỏi
`policy.can_observe_class` — cùng hàm mà bảng quan sát đã dùng, không phải một
luật thứ hai.

**② Lệnh có DANH TÍNH, trạng thái thì không.** Học sinh giữ `lastSeenCmdId` và
chỉ áp lệnh MỚI. Không có `cmd_id` thì mỗi nhịp hỏi lại kéo học sinh về chỗ
giáo viên — em nào đang xem lại bước cũ bị giật vài giây một lần. (Cơ chế này
học từ một trang dạy học có thật, chỗ tác giả đã phải tự phát hiện ra nó.)

**③ `round_id` cắt quá khứ.** Tab mở từ tiết trước mang lệnh cũ; không có
round thì lệnh ấy vẫn "hợp lệ" và kéo lớp về bài hôm qua.

**④ Giờ của MÁY CHỦ.** Mọi response mang `serverNow`. Máy phòng tin hay sai
giờ, và "em này chờ bao lâu rồi" là con số giáo viên dùng để quyết định tới ai
trước — tính bằng đồng hồ máy học sinh thì mỗi em một kết quả.

─── CÁI FILE NÀY KHÔNG LÀM ────────────────────────────────────────────────

Không chiếu màn hình. Không chụp DOM. Không nhận toạ độ. Mọi trường đi qua đây
là **ID NGỮ NGHĨA** (`M`, `chop::face:1`) và **số bước** — không cột nào suy ra
được hình học, và `GeometryState` vẫn do kernel sở hữu.
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..persistence.classroom_models import (
    Assignment,
    ClassMembership,
    Classroom,
    ClassroomSession,
    PracticeSession,
    User,
)
from .policy import Role, can_observe_class, can_read_class
from .router import Caller, get_caller

router = APIRouter(prefix="/api", tags=["live-session"])

#: Hai chế độ, và đây là thuộc tính của LỚP chứ không của từng em. Một lớp nửa
#: bám nửa tự do thì giáo viên không nói được câu "cả lớp nhìn lên đây".
MODES = ("follow", "free")

#: Lệnh CANON. Chuỗi tự do ở đây nghĩa là client đặt tên được cho hành vi máy
#: chủ, và một tên gõ sai sẽ im lặng không làm gì thay vì báo lỗi.
COMMANDS = ("STATE_UPDATE", "SET_MODE", "SYNC_CLASS")

#: Hành động NGỮ NGHĨA học sinh báo lên. Enum, không phải chuỗi tự do — bảng
#: theo dõi của giáo viên phải đọc được, và "một chuỗi bất kỳ" thì không.
#: KHÔNG có sự kiện chuột/khung hình: chúng không trả lời được câu hỏi sư phạm
#: nào, và gom chúng lại là dựng một máy theo dõi thay vì một lớp học.
ACTIONS = ("SELECT_ENTITY", "INSPECT_ENTITY", "ISOLATE_ENTITY", "EXPLODE_SOLID",
           "COLLAPSE_SOLID", "STEP_CHANGE", "REQUEST_HELP", "CANCEL_HELP")

#: Trần cho danh sách ID gửi lên. Cô lập vài chục vật là thao tác thật; vài
#: nghìn thì không phải người dùng, và bảng không phải chỗ chứa.
MAX_IDS = 64
#: Trần độ dài một ID ngữ nghĩa (`chop::face:12` còn xa mới tới).
MAX_ID_LEN = 160


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _utc(dt: datetime) -> datetime:
    """Về UTC CÓ MÚI GIỜ. SQLite lưu `DateTime` là NAIVE.

    ĐO ĐƯỢC: response ngay sau khi ghi trả `…+00:00` (giá trị còn trong bộ
    nhớ), còn response đọc lại từ DB trả cùng một khoảnh khắc mà KHÔNG có múi
    giờ. Client thấy dấu thời gian "đổi" giữa hai lần hỏi cùng một thứ, và một
    phép trừ trộn hai dạng thì nổ `TypeError`.

    Chuẩn hoá tại BIÊN SERIALIZE — một chỗ — thay vì mỗi chỗ dùng lại
    `.replace(tzinfo=…)`; bản đầu của `helpWaitingSeconds` đã vá cục bộ đúng
    kiểu đó, và vá cục bộ nghĩa là chỗ thứ hai sẽ quên.
    """
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    return None if dt is None else _utc(dt).isoformat()


def _ids(raw: list[str] | None) -> list[str]:
    """Danh sách ID ngữ nghĩa, đã kẹp. Bỏ thứ không thể là một ID.

    KHÔNG kiểm ID có tồn tại trong cảnh hay không ở đây: cảnh sống ở envelope
    phía client, còn tầng này cố ý không mở envelope ra. Việc bỏ ID lạc do
    `§21` giao cho biên nhận phía client (fail-safe, không sập phiên).
    """
    if not raw:
        return []
    ra: list[str] = []
    for x in raw:
        if isinstance(x, str) and 0 < len(x) <= MAX_ID_LEN and x not in ra:
            ra.append(x)
        if len(ra) >= MAX_IDS:
            break
    return ra


def _lop(caller: Caller, class_id: int) -> Classroom:
    c = caller.db.get(Classroom, class_id)
    if c is None:
        raise HTTPException(404, "Không tìm thấy lớp.")
    return c


def _thanh_vien_ids(caller: Caller, class_id: int) -> frozenset[int]:
    return frozenset(caller.db.execute(
        select(ClassMembership.student_id)
        .where(ClassMembership.classroom_id == class_id)).scalars().all())


def _doc_duoc(caller: Caller, c: Classroom) -> None:
    """Giáo viên sở hữu, hoặc học sinh ĐÃ vào lớp. Dùng lại `can_read_class`."""
    caller.require_user()
    if not can_read_class(viewer_role=caller.role, viewer_id=caller.user_id,
                          class_teacher_id=c.teacher_id,
                          member_ids=_thanh_vien_ids(caller, c.id)):
        raise HTTPException(404, "Không tìm thấy lớp.")


def _sua_duoc(caller: Caller, c: Classroom) -> None:
    """SỬA phiên: chỉ ĐÚNG giáo viên sở hữu lớp.

    Không có "là giáo viên thì điều khiển được mọi lớp" — cùng luật mà bảng
    quan sát đã áp, cùng một hàm, nên không có chỗ để hai bên lệch nhau.
    """
    caller.require_user()
    if not can_observe_class(viewer_role=caller.role, viewer_id=caller.user_id,
                             class_teacher_id=c.teacher_id):
        raise HTTPException(403, "Bạn không dạy lớp này.")


def _phien(caller: Caller, class_id: int) -> ClassroomSession | None:
    return caller.db.execute(
        select(ClassroomSession).where(ClassroomSession.classroom_id == class_id)
    ).scalar_one_or_none()


def _phien_public(s: ClassroomSession | None) -> dict | None:
    if s is None or not s.active:
        return None
    return {
        "sessionId": s.id,
        "roundId": s.round_id,
        "cmdId": s.cmd_id,
        "syncCmdId": s.sync_cmd_id,
        "mode": s.mode,
        "assignmentId": s.assignment_id,
        "simulationId": s.simulation_id,
        "currentStep": s.current_step,
        "selectedId": s.selected_id,
        "isolatedIds": json.loads(s.isolated_ids or "[]"),
        "explodedGroups": json.loads(s.exploded_groups or "[]"),
        "updatedAt": _iso(s.updated_at),
    }


# ══ PHIÊN DẠY ═══════════════════════════════════════════════════════════════

class StartBody(BaseModel):
    assignmentId: int | None = None
    mode: str = "follow"


@router.post("/classes/{class_id}/session")
def start_session(class_id: int, body: StartBody,
                  caller: Caller = Depends(get_caller)):
    """Bắt đầu (hoặc bắt đầu LẠI) phiên dạy. Luôn cấp `round_id` MỚI.

    Một lớp có tối đa MỘT phiên sống (`uq_session_per_class`) — bắt đầu lại là
    đổi round trên chính hàng ấy, không đẻ hàng thứ hai. Hai phiên cùng sống
    thì không ai trả lời được *"lớp đang ở đâu"*.

    Round mới ⇒ mọi lệnh của round cũ thành quá khứ, và yêu cầu trợ giúp của
    round cũ được dọn: một cánh tay giơ từ tiết trước không phải là một cánh
    tay đang giơ.
    """
    c = _lop(caller, class_id)
    _sua_duoc(caller, c)
    if body.mode not in MODES:
        raise HTTPException(400, "Chế độ lớp không hợp lệ.")

    a: Assignment | None = None
    if body.assignmentId is not None:
        a = caller.db.get(Assignment, body.assignmentId)
        if a is None or a.classroom_id != class_id:
            raise HTTPException(404, "Không tìm thấy bài thực hành của lớp này.")

    s = _phien(caller, class_id)
    if s is None:
        s = ClassroomSession(classroom_id=class_id, teacher_id=caller.user_id,
                             round_id="", cmd_id=0, sync_cmd_id=0)
        caller.db.add(s)
    s.teacher_id = caller.user_id
    s.round_id = secrets.token_hex(8)
    s.cmd_id = 0
    s.sync_cmd_id = 0
    s.mode = body.mode
    s.assignment_id = a.id if a else None
    s.simulation_id = a.simulation_id if a else None
    s.current_step = 0
    s.selected_id = None
    s.isolated_ids = "[]"
    s.exploded_groups = "[]"
    s.active = True
    s.started_at = _now()
    s.updated_at = _now()
    _don_tro_giup(caller, class_id)
    caller.db.flush()
    return {"session": _phien_public(s), "serverNow": _iso(_now())}


@router.get("/classes/{class_id}/session")
def read_session(class_id: int, caller: Caller = Depends(get_caller)):
    """Đọc phiên. Giáo viên sở hữu HOẶC học sinh trong lớp.

    `session: null` là câu trả lời HỢP LỆ (chưa có tiết nào đang chạy) — không
    phải lỗi, và client không được dựng màn hình lỗi cho nó.
    """
    c = _lop(caller, class_id)
    _doc_duoc(caller, c)
    return {"session": _phien_public(_phien(caller, class_id)),
            "serverNow": _iso(_now())}


@router.delete("/classes/{class_id}/session")
def end_session(class_id: int, caller: Caller = Depends(get_caller)):
    """Kết thúc tiết. Phiên thành `active=False` và tay giơ được dọn.

    KHÔNG xoá hàng: `round_id` cũ còn đó để một lệnh đến muộn vẫn đối chiếu
    được và bị từ chối đúng lý do, thay vì trúng một phiên mới.
    """
    c = _lop(caller, class_id)
    _sua_duoc(caller, c)
    s = _phien(caller, class_id)
    if s is not None:
        s.active = False
        s.updated_at = _now()
    _don_tro_giup(caller, class_id)
    caller.db.flush()
    return {"session": None, "serverNow": _iso(_now())}


# ══ LỆNH CỦA GIÁO VIÊN ══════════════════════════════════════════════════════

class CommandBody(BaseModel):
    kind: str
    roundId: str
    mode: str | None = None
    assignmentId: int | None = None
    currentStep: int | None = None
    selectedId: str | None = None
    isolatedIds: list[str] | None = None
    explodedGroups: list[str] | None = None


@router.post("/classes/{class_id}/session/command")
def issue_command(class_id: int, body: CommandBody,
                  caller: Caller = Depends(get_caller)):
    """Giáo viên phát một lệnh. Mỗi lệnh làm `cmd_id` TĂNG đúng một.

    `roundId` bắt buộc và phải khớp: một tab mở từ tiết trước gửi lệnh lên sẽ
    bị từ chối bằng 409 thay vì lặng lẽ kéo cả lớp về bài cũ.

    `SYNC_CLASS` KHÔNG đổi `mode`. Đó là toàn bộ điểm của nó: gọi cả lớp về một
    lần rồi trả các em lại quyền tự khám phá. Ép đổi mode để sync là buộc giáo
    viên phải nhớ bật lại — và quên bật lại thì cả lớp bị khoá mà không ai
    hiểu vì sao.
    """
    c = _lop(caller, class_id)
    _sua_duoc(caller, c)
    if body.kind not in COMMANDS:
        raise HTTPException(400, "Lệnh không hợp lệ.")

    s = _phien(caller, class_id)
    if s is None or not s.active:
        raise HTTPException(409, "Lớp chưa có tiết học nào đang chạy.")
    if body.roundId != s.round_id:
        raise HTTPException(409, "Lệnh thuộc một tiết học đã kết thúc.")

    if body.kind == "SET_MODE":
        if body.mode not in MODES:
            raise HTTPException(400, "Chế độ lớp không hợp lệ.")
        s.mode = body.mode

    if body.kind in ("STATE_UPDATE", "SYNC_CLASS"):
        if body.assignmentId is not None:
            a = caller.db.get(Assignment, body.assignmentId)
            if a is None or a.classroom_id != class_id:
                raise HTTPException(404, "Không tìm thấy bài thực hành của lớp này.")
            s.assignment_id = a.id
            s.simulation_id = a.simulation_id
        if body.currentStep is not None:
            s.current_step = max(0, min(int(body.currentStep), 100_000))
        # `selectedId` CÓ THỂ là null một cách hợp lệ (bỏ chọn), nên phân biệt
        # "không gửi trường" với "gửi null" bằng chính có mặt trong payload.
        if "selectedId" in body.model_fields_set:
            sid = body.selectedId
            s.selected_id = sid if (isinstance(sid, str) and 0 < len(sid) <= MAX_ID_LEN) else None
        if body.isolatedIds is not None:
            s.isolated_ids = json.dumps(_ids(body.isolatedIds), ensure_ascii=False)
        if body.explodedGroups is not None:
            s.exploded_groups = json.dumps(_ids(body.explodedGroups), ensure_ascii=False)

    s.cmd_id += 1
    if body.kind == "SYNC_CLASS":
        s.sync_cmd_id = s.cmd_id
    s.updated_at = _now()
    caller.db.flush()
    return {"session": _phien_public(s), "serverNow": _iso(_now())}


# ══ TRỢ GIÚP ════════════════════════════════════════════════════════════════

class HelpBody(BaseModel):
    requested: bool = True


def _don_tro_giup(caller: Caller, class_id: int) -> None:
    """Hạ mọi cánh tay của lớp. Dùng khi mở round mới hoặc đóng tiết."""
    ids = [a.id for a in caller.db.execute(
        select(Assignment).where(Assignment.classroom_id == class_id)).scalars()]
    if not ids:
        return
    for p in caller.db.execute(
            select(PracticeSession)
            .where(PracticeSession.assignment_id.in_(ids),
                   PracticeSession.help_requested.is_(True))).scalars():
        p.help_requested = False
        p.help_requested_at = None


def _ban_ghi_thuc_hanh(caller: Caller, a: Assignment, student_id: int) -> PracticeSession:
    row = caller.db.execute(
        select(PracticeSession).where(
            PracticeSession.assignment_id == a.id,
            PracticeSession.student_id == student_id)).scalar_one_or_none()
    if row is None:
        row = PracticeSession(
            assignment_id=a.id, student_id=student_id,
            simulation_id=a.simulation_id, cursor=0, step_count=0,
            action_count=0, commitment_count=0, explore_open=False,
            challenge_open=False, completed=False, help_requested=False)
        caller.db.add(row)
    return row


@router.post("/assignments/{assignment_id}/help")
def request_help(assignment_id: int, body: HelpBody,
                 caller: Caller = Depends(get_caller)):
    """Học sinh giơ tay — hoặc hạ tay. CHỈ cho chính mình.

    Không có `student_id` trong body: danh tính lấy từ phiên đăng nhập. Nhận id
    từ client là mở đường cho một em giơ tay hộ em khác.

    Giơ tay hai lần KHÔNG làm mới đồng hồ chờ: nếu làm mới thì em nào bấm nhiều
    lần sẽ luôn đứng cuối hàng đợi của giáo viên — phạt đúng em đang sốt ruột.
    """
    student = caller.require_role(Role.STUDENT)
    a = caller.db.get(Assignment, assignment_id)
    if a is None:
        raise HTTPException(404, "Không tìm thấy bài thực hành.")
    if not _thanh_vien_ids(caller, a.classroom_id).issuperset({student.id}):
        raise HTTPException(404, "Không tìm thấy bài thực hành.")

    row = _ban_ghi_thuc_hanh(caller, a, student.id)
    if body.requested:
        if not row.help_requested:
            row.help_requested = True
            row.help_requested_at = _now()
        row.last_action = "REQUEST_HELP"
    else:
        row.help_requested = False
        row.help_requested_at = None
        row.last_action = "CANCEL_HELP"
    row.updated_at = _now()
    caller.db.flush()
    return {"helpRequested": bool(row.help_requested),
            "helpRequestedAt": _iso(row.help_requested_at),
            "serverNow": _iso(_now())}


@router.post("/classes/{class_id}/help/{student_id}/clear")
def clear_help(class_id: int, student_id: int,
               caller: Caller = Depends(get_caller)):
    """Giáo viên đánh dấu ĐÃ HỖ TRỢ. Chỉ giáo viên sở hữu lớp."""
    c = _lop(caller, class_id)
    _sua_duoc(caller, c)
    ids = [a.id for a in caller.db.execute(
        select(Assignment).where(Assignment.classroom_id == class_id)).scalars()]
    n = 0
    if ids:
        for p in caller.db.execute(
                select(PracticeSession).where(
                    PracticeSession.assignment_id.in_(ids),
                    PracticeSession.student_id == student_id)).scalars():
            if p.help_requested:
                p.help_requested = False
                p.help_requested_at = None
                p.updated_at = _now()
                n += 1
    caller.db.flush()
    return {"cleared": n, "serverNow": _iso(_now())}


# ══ THEO DÕI ════════════════════════════════════════════════════════════════

@router.get("/classes/{class_id}/monitor")
def monitor_class(class_id: int, caller: Caller = Depends(get_caller)):
    """Bảng theo dõi TIÊU ĐIỂM NGỮ NGHĨA — chỉ giáo viên sở hữu lớp.

    Khác `observe` (một dòng cho MỖI CẶP học sinh × bài, để chấm tiến độ cả
    quá trình): ở đây một dòng cho MỖI HỌC SINH, nói em ấy đang ở đâu **ngay
    lúc này** — bài nào, bước nào, đang xem vật nào, có giơ tay không.

    KHÔNG trường nào nói học sinh đúng hay sai, và KHÔNG suy "em này đang bí"
    từ việc đứng lâu: đứng lâu có thể là đang nghĩ. Giáo viên nhìn con số rồi
    tự quyết định; máy không thay việc ấy.
    """
    c = _lop(caller, class_id)
    _sua_duoc(caller, c)

    assignments = {a.id: a for a in caller.db.execute(
        select(Assignment).where(Assignment.classroom_id == class_id)).scalars()}
    students = caller.db.execute(
        select(User).join(ClassMembership, ClassMembership.student_id == User.id)
        .where(ClassMembership.classroom_id == class_id)
        .order_by(User.display_name)).scalars().all()

    moi_nhat: dict[int, PracticeSession] = {}
    if assignments:
        for p in caller.db.execute(
                select(PracticeSession).where(
                    PracticeSession.assignment_id.in_(list(assignments)))).scalars():
            cu = moi_nhat.get(p.student_id)
            if cu is None or (p.updated_at or _now()) >= (cu.updated_at or _now()):
                moi_nhat[p.student_id] = p

    now = _now()
    rows = []
    for s in students:
        p = moi_nhat.get(s.id)
        a = assignments.get(p.assignment_id) if p else None
        cho = None
        if p is not None and p.help_requested and p.help_requested_at is not None:
            # Tính bằng giờ MÁY CHỦ: hai đầu của phép trừ phải cùng một đồng hồ.
            cho = max(0, int((now - _utc(p.help_requested_at)).total_seconds()))
        rows.append({
            "studentId": s.id,
            "studentName": s.display_name,
            "assignmentId": None if a is None else a.id,
            "assignmentTitle": None if a is None else a.title,
            "currentStep": None if p is None else p.cursor,
            "stepCount": None if p is None else p.step_count,
            "selectedId": None if p is None else p.selected_id,
            "lastAction": None if p is None else p.last_action,
            "helpRequested": bool(p.help_requested) if p else False,
            "helpWaitingSeconds": cho,
            "updatedAt": None if p is None else _iso(p.updated_at),
        })
    return {
        "classroom": {"id": c.id, "name": c.name},
        "session": _phien_public(_phien(caller, class_id)),
        "rows": rows,
        "serverNow": _iso(now),
    }
