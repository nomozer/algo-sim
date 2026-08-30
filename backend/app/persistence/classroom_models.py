"""Bảng cho tầng TÀI KHOẢN + LỚP HỌC (M18).

Đặt cạnh `db.py` chứ không nhét vào nó: `db.py` sở hữu ngân hàng bài (cache /
pattern / metric) — một trách nhiệm đã đủ. Cả hai dùng CHUNG `Base` nên Alembic
vẫn thấy một metadata duy nhất; import ở đây chỉ đi MỘT chiều
(`classroom_models` → `db`), không có vòng.

Ranh giới của tầng này (bất biến #27): nó lưu DANH TÍNH, TƯ CÁCH THÀNH VIÊN và
BẰNG CHỨNG THỰC HÀNH CÓ CẤU TRÚC. Nó KHÔNG lưu kết quả đúng/sai do ai đó phán —
engine tất định vẫn là nơi duy nhất biết học sinh trả lời đúng hay chưa.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base, _now


class User(Base):
    """Tài khoản. `role` là cột SERVER sở hữu — client không bao giờ ghi được.

    `email` là định danh đăng nhập; lưu ở dạng đã chuẩn hoá (thường hoá, cắt
    khoảng trắng) để "An@Truong.edu.vn" và "an@truong.edu.vn" không thành hai
    tài khoản.

    `password_hash` KHÔNG BAO GIỜ rời khỏi tầng này: không lọt vào response,
    không lọt vào log. Khoá bằng `test_auth_api.py`.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), index=True)
    #: Tài khoản do giáo viên cấp và học sinh CHƯA đổi mật khẩu lần đầu.
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AuthSession(Base):
    """Phiên máy chủ — nguồn sự thật DUY NHẤT về "ai đang gọi".

    Cố ý KHÔNG dùng JWT: token đục (opaque) tra trong bảng thì **thu hồi được
    ngay** (đăng xuất là xoá dòng), còn JWT tự chứng thực thì phải dựng thêm
    danh sách đen mới huỷ được — nhiều bộ phận hơn cho cùng một việc.

    Hàng này cũng phục vụ KHÁCH: `user_id` để trống nghĩa là phiên ẩn danh, và
    `guest_trials_used` là nơi đếm lượt dùng thử. Đếm ở SERVER vì một cờ trong
    localStorage thì xoá cache là có lại (bài kiểm tiêm lỗi #1).
    """

    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    guest_trials_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class Classroom(Base):
    """Lớp học. `join_code` là LỜI MỜI, KHÔNG phải chứng chỉ đăng nhập.

    Vào lớp bằng mã vẫn phải đăng nhập trước — mã chỉ nói "cho tôi vào lớp
    này", không nói "tôi là ai". Nhờ vậy mã lộ ra ngoài thì hậu quả là một
    người lạ vào lớp, không phải một người lạ mạo danh học sinh.

    Mã REVOKE được (`code_active`) và sinh lại được, nên lộ mã không buộc phải
    xoá cả lớp.
    """

    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    join_code: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    code_active: Mapped[bool] = mapped_column(Boolean, default=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ClassMembership(Base):
    """Học sinh ↔ lớp. Ràng buộc duy nhất chặn vào lớp hai lần ở TẦNG DB,
    không chỉ ở tầng ứng dụng — hai request song song vẫn chỉ ra một dòng."""

    __tablename__ = "class_memberships"
    __table_args__ = (UniqueConstraint("classroom_id", "student_id", name="uq_class_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Assignment(Base):
    """Bài thực hành giáo viên giao cho lớp.

    `envelope_json` giữ **envelope ĐÃ VALIDATE**, không giữ đề bài dạng chữ để
    sinh lại lúc học sinh mở. Hai lý do, cả hai đều là bất biến của đề tài:
    (1) chữ của giáo viên KHÔNG được thành sự thật runtime — nó phải đi qua
    đúng cổng validate mà mọi mô phỏng khác đi (bất biến #28); (2) sinh lại
    bằng LLM lúc mở nghĩa là 30 học sinh mở ra 30 mô phỏng khác nhau, và giáo
    viên không giao được thứ mình đã xem.

    `instruction` là lời dặn của giáo viên — CHỮ, hiển thị cạnh mô phỏng, không
    bao giờ được đọc như tham số.
    """

    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    instruction: Mapped[str] = mapped_column(Text, default="")
    simulation_id: Mapped[str] = mapped_column(String(80), index=True)
    envelope_json: Mapped[str] = mapped_column(Text)
    closed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class PracticeSession(Base):
    """MỘT học sinh đang/đã làm MỘT bài thực hành.

    Đây là bản ghi mà giáo viên quan sát, và nó cố ý HẸP (`§19`, `§21`): các
    trường có cấu trúc, đủ để trả lời "em ấy đang ở đâu trong bài", KHÔNG phải
    ảnh chụp state của renderer và KHÔNG phải luồng màn hình.

    `cursor`/`step_count` là con số của TIMELINE do engine sở hữu; ở đây chỉ là
    BẢN SAO ĐỂ ĐỌC. Không ai được tính lại kết quả từ bảng này.
    """

    __tablename__ = "practice_sessions"
    __table_args__ = (UniqueConstraint("assignment_id", "student_id", name="uq_practice_once"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    simulation_id: Mapped[str] = mapped_column(String(80))
    #: Vị trí trên timeline của engine (bản sao để đọc).
    cursor: Mapped[int] = mapped_column(Integer, default=0)
    step_count: Mapped[int] = mapped_column(Integer, default=0)
    #: Cờ TRÌNH BÀY do học sinh bật (Khám phá / Thử thách đang mở).
    explore_open: Mapped[bool] = mapped_column(Boolean, default=False)
    challenge_open: Mapped[bool] = mapped_column(Boolean, default=False)
    #: Đếm sự kiện có nghĩa — KHÔNG phải một engine thứ hai (`§32`).
    action_count: Mapped[int] = mapped_column(Integer, default=0)
    #: Số lần học sinh đã CHỐT một cam kết; engine là bên phán đúng/sai, không phải cột này.
    commitment_count: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    # ── TIÊU ĐIỂM NGỮ NGHĨA + TRỢ GIÚP (2026-08-30) ─────────────────────────
    #
    # MỞ RỘNG bảng này thay vì dựng `StudentObservationState` riêng: nó đã là
    # bản ghi "một học sinh đang ở đâu trong một bài", và một bảng thứ hai cùng
    # khoá `(bài, học sinh)` sẽ có hai `updated_at` lệch nhau — giáo viên nhìn
    # bảng nào cũng không biết bảng kia nói gì.
    #
    # ⚠️ VẪN LÀ TRẠNG THÁI CÓ CẤU TRÚC. `selected_id` là một ID NGỮ NGHĨA của
    # Scene3D (`M`, `chop::face:1`), không phải toạ độ, không phải DOM, không
    # phải ảnh. Không cột nào ở đây suy ra được hình học.
    #: Vật học sinh đang chọn. `None` = chưa chọn gì — một trạng thái THẬT.
    selected_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    #: Hành động NGỮ NGHĨA gần nhất (`SELECT_ENTITY`, `ISOLATE_ENTITY`…).
    #: Enum khoá ở tầng HTTP, không phải chuỗi tự do từ client.
    last_action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    #: Học sinh giơ tay. Thời điểm do MÁY CHỦ đặt — máy phòng tin hay sai giờ,
    #: và "chờ bao lâu rồi" là con số giáo viên dùng để quyết định tới ai trước.
    help_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    help_requested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ClassroomSession(Base):
    """PHIÊN DẠY đang chạy của một lớp — trạng thái ĐIỀU PHỐI, server sở hữu.

    ─── VÌ SAO LÀ BẢNG RIÊNG, KHÔNG NHÉT VÀO `Classroom` ───────────────────

    `Classroom` là danh tính bền (tên lớp, mã vào lớp, ai dạy). Phiên dạy là
    thứ SỐNG TRONG MỘT TIẾT: đổi mode, đổi bước, gọi cả lớp về. Trộn hai vòng
    đời vào một hàng thì mỗi lần giáo viên bấm một nút là ghi lại chính danh
    tính lớp, và `Classroom.created_at` mất nghĩa.
    ─── BỐN TRƯỜNG CƠ CHẾ, mỗi trường chặn một lỗi ĐÃ QUAN SÁT ĐƯỢC ────────

    `round_id` — một đợt dạy. Tab trình duyệt mở từ tiết trước giữ lệnh cũ;
      không có round thì lệnh ấy vẫn "hợp lệ" và kéo lớp về bài hôm qua.
    `cmd_id` — tăng đơn điệu TRONG một round. Học sinh giữ `last_seen_cmd_id`
      và chỉ áp lệnh MỚI. Thiếu nó thì mỗi nhịp hỏi lại kéo học sinh về chỗ
      giáo viên — em nào đang xem lại bước cũ bị giật mỗi vài giây.
    `updated_at` — dùng để đọc độ tươi, KHÔNG dùng để sắp thứ tự lệnh. Sắp
      theo đồng hồ là sắp theo một thứ mỗi máy một khác.
    `mode` — `follow` | `free`. Là thuộc tính của LỚP, không phải của từng em.

    KHÔNG lưu `GeometryState` ở đây. Bảng này chở ID và số bước; hình học vẫn
    do kernel sở hữu, và một envelope đã validate là nơi duy nhất có toạ độ.
    """

    __tablename__ = "classroom_sessions"
    __table_args__ = (UniqueConstraint("classroom_id", name="uq_session_per_class"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    #: MỘT phiên sống cho mỗi lớp (`uq_session_per_class`). Bắt đầu phiên mới
    #: là ĐỔI round trên chính hàng này, không đẻ hàng thứ hai — hai phiên cùng
    #: sống thì không ai trả lời được "lớp đang ở đâu".
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    round_id: Mapped[str] = mapped_column(String(40), index=True)
    cmd_id: Mapped[int] = mapped_column(Integer, default=0)
    #: `follow` | `free`.
    mode: Mapped[str] = mapped_column(String(8), default="follow")
    #: Bài đang chiếu. `None` = phiên mở nhưng chưa chọn bài.
    assignment_id: Mapped[int | None] = mapped_column(
        ForeignKey("assignments.id"), nullable=True, index=True)
    simulation_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    #: Trạng thái TRÌNH BÀY chuẩn của giáo viên. Chỉ ID và số bước.
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    selected_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    #: JSON mảng ID ngữ nghĩa. Text vì SQLite lẫn Postgres đều chở được, và
    #: tầng này không truy vấn vào trong chúng.
    isolated_ids: Mapped[str] = mapped_column(Text, default="[]")
    exploded_groups: Mapped[str] = mapped_column(Text, default="[]")
    #: `cmd_id` của lệnh SYNC_CLASS gần nhất. Học sinh ở chế độ TỰ DO vẫn áp
    #: lệnh này ĐÚNG MỘT LẦN — đó là toàn bộ điểm của việc tách nó khỏi `mode`.
    sync_cmd_id: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
