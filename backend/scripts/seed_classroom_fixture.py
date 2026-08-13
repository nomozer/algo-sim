# -*- coding: utf-8 -*-
"""Dựng dữ liệu DEV/TEST cho nghiệm thu trình duyệt (M18, `§34`).

Chạy từ `backend/`:
    .venv/Scripts/python.exe scripts/seed_classroom_fixture.py

Tạo: 1 giáo viên · 2 học sinh · 1 lớp · 1 bài thực hành đã giao.

CHÍNH SÁCH MẬT KHẨU CỦA FIXTURE (`§34` — không nhét mật khẩu production vào mã):
mật khẩu đọc từ biến môi trường `ALGOSIM_FIXTURE_PASSWORD`; không đặt thì script
SINH NGẪU NHIÊN và in ra một lần. Không có giá trị mặc định nào nằm trong file
này, nên kể cả khi script bị chạy nhầm trên máy chủ thật thì cũng không tạo ra
một tài khoản mà mọi người đọc mã đều biết mật khẩu.

Script IDEMPOTENT: chạy lại không nhân đôi lớp/bài.
"""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json  # noqa: E402

from sqlalchemy import select  # noqa: E402

from app.accounts import service  # noqa: E402
from app.accounts.policy import Role  # noqa: E402
from app.persistence.classroom_models import (  # noqa: E402
    Assignment, ClassMembership, Classroom, User,
)
from app.persistence.db import Base, SessionLocal, engine  # noqa: E402

TEACHER_EMAIL = "gv.demo@algosim.test"
STUDENT_A_EMAIL = "hs.an@algosim.test"
STUDENT_B_EMAIL = "hs.binh@algosim.test"
CLASS_NAME = "10A1 — Tin học"

#: Envelope demo: đi qua ĐÚNG cổng validate mà mọi bài giao khác đi.
DEMO_ENVELOPE = {
    "status": "ok",
    "simulation_id": "logic.and_gate",
    "domain": "logic",
    "visual_mode": "2d",
    "title": "Cổng AND: khi nào đèn sáng?",
    "config": {"inputA": 1, "inputB": 0, "notes": None},
}


def _password() -> str:
    pw = os.getenv("ALGOSIM_FIXTURE_PASSWORD", "").strip()
    if pw:
        return pw
    generated = "dev-" + secrets.token_urlsafe(12)
    print(f"  (sinh mật khẩu ngẫu nhiên: {generated})")
    return generated


def _get_or_create(session, email: str, name: str, role: Role, password: str) -> User:
    row = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if row is not None:
        return row
    return service.create_user(session, email=email, display_name=name,
                               password=password, role=role)


def main() -> int:
    Base.metadata.create_all(engine)  # SQLite dev; Postgres do Alembic sở hữu
    password = _password()
    with SessionLocal() as session:
        teacher = _get_or_create(session, TEACHER_EMAIL, "Cô Lan (demo)", Role.TEACHER, password)
        an = _get_or_create(session, STUDENT_A_EMAIL, "Nguyễn Văn An", Role.STUDENT, password)
        binh = _get_or_create(session, STUDENT_B_EMAIL, "Trần Thị Bình", Role.STUDENT, password)
        session.flush()

        cls = session.execute(
            select(Classroom).where(Classroom.teacher_id == teacher.id,
                                    Classroom.name == CLASS_NAME)
        ).scalar_one_or_none()
        if cls is None:
            cls = Classroom(teacher_id=teacher.id, name=CLASS_NAME,
                            join_code=service.generate_join_code(session))
            session.add(cls)
            session.flush()

        for student in (an, binh):
            exists = session.execute(
                select(ClassMembership).where(
                    ClassMembership.classroom_id == cls.id,
                    ClassMembership.student_id == student.id)
            ).scalar_one_or_none()
            if exists is None:
                session.add(ClassMembership(classroom_id=cls.id, student_id=student.id))

        assignment = session.execute(
            select(Assignment).where(Assignment.classroom_id == cls.id)
        ).scalar_one_or_none()
        if assignment is None:
            session.add(Assignment(
                classroom_id=cls.id, created_by=teacher.id,
                title="Bảng chân trị của cổng AND",
                instruction="Bật/tắt hai đầu vào rồi ghi lại khi nào đầu ra bằng 1.",
                simulation_id=DEMO_ENVELOPE["simulation_id"],
                envelope_json=json.dumps(DEMO_ENVELOPE, ensure_ascii=False)))

        session.commit()
        print(f"  giáo viên : {TEACHER_EMAIL}")
        print(f"  học sinh  : {STUDENT_A_EMAIL} · {STUDENT_B_EMAIL}")
        print(f"  lớp       : {cls.name}  ·  mã {cls.join_code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
