# -*- coding: utf-8 -*-
"""M18 — DANH TÍNH VÀ QUYỀN DO MÁY CHỦ SỞ HỮU.

Đây là file khoá những thứ mà một lỗi ở đó không hiện ra trên màn hình: mật
khẩu rò ra response, client tự nâng vai trò, lượt dùng thử đếm ở sai chỗ.

Mọi bài trong file này chạy hoàn toàn offline (guard mạng của `conftest.py` vẫn
áp dụng) và trên một database trống của riêng nó.
"""

from __future__ import annotations

import os

import pytest

from app.accounts.passwords import (
    MIN_PASSWORD_LENGTH,
    WeakPasswordError,
    hash_password,
    verify_password,
)
from app.accounts.policy import (
    GUEST_TRIAL_LIMIT,
    Role,
    RoleEscalationError,
    entitlement_for,
    resolve_signup_role,
)
from tests.conftest_classroom import TEST_PASSWORD, api, login, new_client, register  # noqa: F401

# Mật khẩu mới cho ca đổi mật khẩu, dẫn xuất từ hằng kiểm thử (không viết literal mật khẩu — cổng publication safety).
NEW_TEST_PASSWORD = TEST_PASSWORD + "-moi"


# ── BĂM MẬT KHẨU ─────────────────────────────────────────────────────────────

class TestMatKhau:
    def test_hash_khong_bao_gio_chua_mat_khau_tho(self):
        pw = "mat-khau-rat-dai-12345"
        stored = hash_password(pw)
        assert pw not in stored
        assert stored.startswith("pbkdf2_sha256$")

    def test_hai_lan_bam_cung_mot_mat_khau_cho_hai_chuoi_khac_nhau(self):
        """Salt riêng cho từng lần — nếu hai chuỗi giống nhau thì salt đã bị bỏ,
        và một bảng cầu vồng dựng sẵn lại có tác dụng."""
        a, b = hash_password(TEST_PASSWORD), hash_password(TEST_PASSWORD)
        assert a != b
        assert verify_password(TEST_PASSWORD, a)
        assert verify_password(TEST_PASSWORD, b)

    def test_sai_mat_khau_bi_tu_choi(self):
        stored = hash_password(TEST_PASSWORD)
        assert not verify_password(TEST_PASSWORD + "x", stored)
        assert not verify_password("", stored)

    def test_chuoi_luu_hong_thi_tra_False_chu_khong_nem_loi(self):
        """Fail-closed và IM LẶNG: một exception riêng cho 'hash hỏng' là một
        kênh để phân biệt tài khoản có tồn tại hay không."""
        for bad in ["", "khong-phai-hash", "pbkdf2_sha256$abc$def", None, "a$b$c$d"]:
            assert verify_password("x", bad) is False

    def test_mat_khau_qua_ngan_bi_tu_choi_ngay_o_tang_mien(self):
        with pytest.raises(WeakPasswordError):
            hash_password("a" * (MIN_PASSWORD_LENGTH - 1))


# ── VAI TRÒ DO SERVER QUYẾT ──────────────────────────────────────────────────

class TestVaiTro:
    def test_dang_ky_thuong_luon_ra_hoc_sinh(self):
        assert resolve_signup_role(None, teacher_code=None, expected_teacher_code="X") is Role.STUDENT
        assert resolve_signup_role("student", teacher_code=None, expected_teacher_code="X") is Role.STUDENT

    def test_tu_khai_giao_vien_ma_khong_co_ma_thi_BI_CHAN(self):
        """Đây là §36.5: client sửa một trường JSON không được nâng quyền."""
        with pytest.raises(RoleEscalationError):
            resolve_signup_role("teacher", teacher_code=None, expected_teacher_code="MA")
        with pytest.raises(RoleEscalationError):
            resolve_signup_role("teacher", teacher_code="sai", expected_teacher_code="MA")

    def test_he_thong_chua_cau_hinh_ma_thi_DONG_chu_khong_mo(self):
        """Fail-closed: thiếu cấu hình không được thành 'cho qua'."""
        with pytest.raises(RoleEscalationError):
            resolve_signup_role("teacher", teacher_code="bat-ky", expected_teacher_code=None)

    def test_vai_tro_la_hoan_toan_thi_tu_choi_chu_khong_am_tham_ha_ve_student(self):
        with pytest.raises(RoleEscalationError):
            resolve_signup_role("admin", teacher_code=None, expected_teacher_code="MA")

    def test_dung_ma_thi_ra_giao_vien(self):
        assert resolve_signup_role("teacher", teacher_code="MA", expected_teacher_code="MA") is Role.TEACHER


# ── QUYỀN ────────────────────────────────────────────────────────────────────

class TestQuyen:
    def test_khach_co_dung_mot_luot_va_khong_luu_lich_su_ben(self):
        e = entitlement_for(None, guest_trials_used=0)
        assert e.can_run_simulation and e.trials_left == GUEST_TRIAL_LIMIT
        assert not e.can_persist_history
        assert not hasattr(e, "can_join_class")
        assert not hasattr(e, "can_own_class")
        assert not hasattr(e, "can_receive_assignment")

    def test_khach_dung_het_luot_thi_khong_chay_duoc_nua(self):
        e = entitlement_for(None, guest_trials_used=GUEST_TRIAL_LIMIT)
        assert not e.can_run_simulation and e.trials_left == 0

    def test_hoc_sinh_va_giao_vien_co_quyen_mo_phong_va_luu_lich_su(self):
        for role in (Role.STUDENT, Role.TEACHER):
            e = entitlement_for(role)
            assert e.can_run_simulation and e.can_persist_history and e.trials_left is None
            assert not hasattr(e, "can_join_class")
            assert not hasattr(e, "can_own_class")
            assert not hasattr(e, "can_receive_assignment")

    def test_endpoints_lop_hoc_bai_thuc_hanh_va_phien_truc_tiep_da_go_tra_404(self, api):
        """Các tuyến lớp học, giao bài và điều phối trực tiếp đã gỡ hoàn toàn phải trả 404."""
        for path in (
            "/api/classes",
            "/api/classes/join",
            "/api/assignments",
            "/api/practice-sessions",
            "/api/live-session",
        ):
            assert api.get(path).status_code == 404
            assert api.post(path, json={}).status_code == 404


# ── HTTP ─────────────────────────────────────────────────────────────────────

class TestApiDangKyDangNhap:
    def test_dang_ky_roi_dang_nhap_duoc(self, api):
        r = register(api, email="an@lop.test", name="An")
        assert r.status_code == 200, r.text
        assert r.json()["user"]["role"] == "student"
        api.post("/api/auth/logout")
        assert login(api, email="an@lop.test").status_code == 200

    def test_response_KHONG_BAO_GIO_chua_hash_mat_khau(self, api):
        """Quét TOÀN BỘ chuỗi response, không chỉ các khoá đã biết — thêm một
        trường mới vô ý chở hash vào cũng bị bắt."""
        r = register(api, email="an@lop.test", name="An")
        for probe in [r, api.get("/api/auth/me"), login(api, email="an@lop.test")]:
            body = probe.text
            assert "pbkdf2_sha256" not in body
            assert "password" not in body.lower() or "mustChangePassword" in body
            assert TEST_PASSWORD not in body

    def test_email_khong_phan_biet_hoa_thuong(self, api):
        register(api, email="An@Lop.Test", name="An")
        api.post("/api/auth/logout")
        assert login(api, email="an@lop.test").status_code == 200

    def test_dang_ky_trung_email_bi_tu_choi(self, api):
        register(api, email="an@lop.test", name="An")
        r = register(new_client(api), email="an@lop.test", name="An hai")
        assert r.status_code == 400

    def test_sai_email_va_sai_mat_khau_cho_CUNG_MOT_cau_tra_loi(self, api):
        """Không cho dò xem email nào đã có tài khoản."""
        register(api, email="an@lop.test", name="An")
        c = new_client(api)
        r1 = c.post("/api/auth/login", json={"email": "khong-co@lop.test", "password": TEST_PASSWORD})
        r2 = c.post("/api/auth/login", json={"email": "an@lop.test", "password": "sai-mat-khau-dai"})
        assert r1.status_code == r2.status_code == 401
        assert r1.json()["detail"] == r2.json()["detail"]

    def test_client_gui_role_teacher_KHONG_thanh_giao_vien(self, api):
        """§36.5 ở tầng HTTP."""
        r = register(api, email="gian@lop.test", name="Giả", role="teacher")
        assert r.status_code == 403
        # và không có tài khoản nào được tạo ra
        assert login(new_client(api), email="gian@lop.test").status_code == 401

    def test_dung_ma_giao_vien_thi_tao_duoc_tai_khoan_giao_vien(self, api):
        r = register(api, email="co@lop.test", name="Cô Lan",
                     role="teacher", teacher_code="MA-GIAO-VIEN-TEST")
        assert r.status_code == 200, r.text
        assert r.json()["user"]["role"] == "teacher"

    def test_dang_xuat_thi_phien_chet_ngay(self, api):
        register(api, email="an@lop.test", name="An")
        assert api.get("/api/auth/me").json()["user"] is not None
        api.post("/api/auth/logout")
        assert api.get("/api/auth/me").json()["user"] is None

    def test_doi_mat_khau_can_mat_khau_hien_tai(self, api):
        register(api, email="an@lop.test", name="An")
        bad = api.post("/api/auth/password",
                       json={"currentPassword": TEST_PASSWORD + "-sai", "newPassword": NEW_TEST_PASSWORD})
        assert bad.status_code == 400
        ok = api.post("/api/auth/password",
                      json={"currentPassword": TEST_PASSWORD, "newPassword": NEW_TEST_PASSWORD})
        assert ok.status_code == 200
        api.post("/api/auth/logout")
        assert login(api, email="an@lop.test", password=NEW_TEST_PASSWORD).status_code == 200

    def test_khach_chua_dang_nhap_van_goi_duoc_me(self, api):
        r = api.get("/api/auth/me")
        assert r.status_code == 200
        assert r.json()["user"] is None
        assert r.json()["entitlement"]["trialsLeft"] == GUEST_TRIAL_LIMIT



class TestQuanTriHeThongRBAC:
    def test_hoc_sinh_va_giao_vien_bi_chan_o_admin_api(self, api):
        # Học sinh bị chặn 403
        c_student = new_client(api)
        register(c_student, email="hs@lop.test", name="Học sinh An")
        r_hs = c_student.get("/api/admin/overview")
        assert r_hs.status_code == 403

        # Giáo viên cũng bị chặn 403 (chỉ admin thật mới có quyền quản trị hệ thống)
        c_teacher = new_client(api)
        register(
            c_teacher,
            email="gv@lop.test",
            name="Cô Lan",
            role="teacher",
            teacher_code="MA-GIAO-VIEN-TEST",
        )
        r_gv = c_teacher.get("/api/admin/overview")
        assert r_gv.status_code == 403

    def test_admin_truy_cap_duoc_overview_va_ghi_nhat_ky_that(self, api):
        from app.accounts import router as accounts_router
        from app.accounts import service as accounts_service

        with accounts_router.SessionLocal() as db:
            accounts_service.upsert_or_rotate_admin_credentials(
                db,
                password=TEST_PASSWORD,
                email="admin@axo.edu.vn",
                display_name="Quản trị hệ thống",
                create_if_missing=True,
            )
            db.commit()

        c_admin = new_client(api)
        r_login = login(c_admin, email="admin@axo.edu.vn", password=TEST_PASSWORD)
        assert r_login.status_code == 200
        assert r_login.json()["user"]["role"] == "admin"

        r_ov = c_admin.get("/api/admin/overview")
        assert r_ov.status_code == 200
        data = r_ov.json()
        assert data["stats"]["totalUsers"] >= 1
        assert isinstance(data["auditLogs"], list)

        # Tạo tài khoản mới qua Admin API và kiểm tra nhật ký quản trị
        r_create = c_admin.post(
            "/api/admin/users",
            json={
                "email": "newstudent@axo.edu.vn",
                "displayName": "Trần Minh",
                "password": TEST_PASSWORD,
                "role": "student",
                "school": "THPT Thực nghiệm",
            },
        )
        assert r_create.status_code == 200
        created_id = r_create.json()["user"]["id"]

        # Điều chỉnh hạn mức + trạng thái
        r_patch = c_admin.patch(
            f"/api/admin/users/{created_id}",
            json={"customDailyLimit": 25, "bonusQuotaToday": 10, "status": "suspended"},
        )
        assert r_patch.status_code == 200
        assert r_patch.json()["user"]["dailyLimit"] == 25
        assert r_patch.json()["user"]["bonusQuotaToday"] == 10
        assert r_patch.json()["user"]["status"] == "suspended"

        # Lưu cài đặt hệ thống
        r_settings = c_admin.put(
            "/api/admin/settings",
            json={
                "studentDailyLimit": 20,
                "teacherDailyLimit": 90,
                "studentTokenLimit": 50000,
                "teacherTokenLimit": 250000,
                "studentRpmLimit": 5,
                "teacherRpmLimit": 12,
                "monthlyBudgetVnd": 4500000,
                "budgetCapMode": "chặn yêu cầu mới & thông báo Quản trị viên",
                "guestTrialLimit": 3,
                "teacherVerifyMode": "cần Quản trị viên duyệt trước khi kích hoạt",
                "maintenanceMode": False,
                "allowNewRegistrations": True,
            },
        )
        assert r_settings.status_code == 200
        assert r_settings.json()["settings"]["studentDailyLimit"] == 20

        # Kiểm tra nhật ký quản trị có ghi nhận các thao tác thật
        r_ov2 = c_admin.get("/api/admin/overview").json()
        assert len(r_ov2["auditLogs"]) >= 3


class TestAdminUsernameEmailVaBaoMat:
    def test_dang_ky_cong_khai_khong_bao_gio_cap_quyen_admin_ke_ca_khi_co_bien_moi_truong(self, api, monkeypatch):
        """Bảo mật §IV: API đăng ký công khai tuyệt đối không cấp quyền Admin — kể cả khi đặt ALGOSIM_ADMIN_SIGNUP_CODE hoặc gửi payload dị biệt."""
        from sqlalchemy import select
        from app.accounts import router as accounts_router
        from app.persistence.classroom_models import User

        # 1) Không cấu hình mã + mã cũ ADMIN2026
        monkeypatch.delenv("ALGOSIM_ADMIN_SIGNUP_CODE", raising=False)
        for code in (None, "", "ADMIN2026"):
            c = new_client(api)
            r = register(
                c,
                email=f"fake-admin-{code or 'none'}@lop.test",
                name="Giả danh Admin",
                role="admin",
                teacher_code=code,
            )
            assert r.status_code == 403

        # 2) Ngay cả khi biến môi trường ALGOSIM_ADMIN_SIGNUP_CODE ĐƯỢC cấu hình, public registration VẪN phải chặn 403
        monkeypatch.setenv("ALGOSIM_ADMIN_SIGNUP_CODE", "ROTATED-SECRET-CODE-99")
        c_env = new_client(api)
        r_env = register(
            c_env,
            email="fake-admin-env@lop.test",
            name="Bypass Env Admin",
            role="admin",
            teacher_code="ROTATED-SECRET-CODE-99",
        )
        assert r_env.status_code == 403

        # 3) Direct bypass với các biến thể role chuỗi khác thường (hoa/thường, khoảng trắng, tên đặc quyền) -> 403
        for weird_role in ("ADMIN", "Admin", " admin ", "superadmin", "root", ""):
            c_w = new_client(api)
            r_w = c_w.post(
                "/api/auth/register",
                json={
                    "email": f"weird-{abs(hash(weird_role))}@lop.test",
                    "displayName": "Role Probe",
                    "password": TEST_PASSWORD,
                    "role": weird_role,
                    "teacherCode": "ROTATED-SECRET-CODE-99",
                },
            )
            assert r_w.status_code == 403

        # 4) Kiểu dữ liệu role dị biệt (list / int / dict / bool) -> 422, không tạo tài khoản
        for malformed_role in (["admin"], 123, {"role": "admin"}, True):
            c_m = new_client(api)
            r_m = c_m.post(
                "/api/auth/register",
                json={
                    "email": f"malformed-{type(malformed_role).__name__}@lop.test",
                    "displayName": "Malformed Role",
                    "password": TEST_PASSWORD,
                    "role": malformed_role,
                },
            )
            assert r_m.status_code == 422

        # Xác nhận DB có 0 tài khoản admin được tạo qua đăng ký công khai
        with accounts_router.SessionLocal() as db:
            assert db.execute(select(User).where(User.role == "admin")).scalars().all() == []

        # 5) Luồng đăng ký Giáo viên hợp lệ vẫn hoạt động nguyên vẹn (không bị xóa nhầm)
        monkeypatch.setenv("ALGOSIM_TEACHER_SIGNUP_CODE", "GV-INVITE-VALID")
        c_gv = new_client(api)
        r_gv = register(
            c_gv,
            email="gv.hop.le@axo.edu.vn",
            name="Cô Lan",
            role="teacher",
            teacher_code="GV-INVITE-VALID",
        )
        assert r_gv.status_code == 200
        assert r_gv.json()["user"]["role"] == "teacher"
        # Giáo viên vẫn bị chặn 403 ở toàn bộ API Admin
        assert c_gv.get("/api/admin/overview").status_code == 403
        assert c_gv.put("/api/admin/settings", json={"studentDailyLimit": 99}).status_code == 403

    def test_admin_dang_nhap_bang_username_hoac_email_cung_mot_tai_khoan_va_phan_quyen_that(self, api, monkeypatch):
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import select
        from app.accounts import router as accounts_router
        from app.accounts import service as accounts_service
        from app.persistence.classroom_models import AuthSession, User

        monkeypatch.setenv("ADMIN_USERNAME", "admin")
        monkeypatch.delenv("ADMIN_EMAIL", raising=False)

        with accounts_router.SessionLocal() as db:
            admin_row, action, _ = accounts_service.upsert_or_rotate_admin_credentials(
                db,
                password=TEST_PASSWORD,
                email="owner.admin@axo.edu.vn",
                display_name="Quản trị Axo",
                create_if_missing=True,
            )
            db.commit()
            expected_id = admin_row.id
            assert action == "created"

        # Học sinh thường cùng hệ thống không bị ảnh hưởng và không dùng được username 'admin'
        c_student = new_client(api)
        r_stu = register(c_student, email="student.norm@axo.edu.vn", name="Học sinh A")
        assert r_stu.status_code == 200
        assert c_student.get("/api/admin/overview").status_code == 403

        # Đăng nhập Admin bằng username "admin" (không phân biệt hoa/thường)
        c_by_user = new_client(api)
        r_u = c_by_user.post("/api/auth/login", json={"identifier": "ADMIN", "password": TEST_PASSWORD})
        assert r_u.status_code == 200
        assert r_u.json()["user"]["id"] == expected_id
        assert r_u.json()["user"]["email"] == "owner.admin@axo.edu.vn"
        assert r_u.json()["user"]["username"] == "admin"
        assert r_u.json()["user"]["role"] == "admin"
        assert c_by_user.get("/api/admin/overview").status_code == 200

        # Đăng nhập Admin bằng email hiện có → CÙNG MỘT bản ghi id
        c_by_email = new_client(api)
        r_e = c_by_email.post("/api/auth/login", json={"email": "owner.admin@axo.edu.vn", "password": TEST_PASSWORD})
        assert r_e.status_code == 200
        assert r_e.json()["user"]["id"] == expected_id
        assert r_e.json()["user"]["role"] == "admin"
        assert c_by_email.get("/api/admin/overview").status_code == 200

        # Kiểm chứng phiên Admin hết hạn bị từ chối 401 ngay lập tức
        with accounts_router.SessionLocal() as db:
            sessions = db.execute(select(AuthSession).where(AuthSession.user_id == expected_id)).scalars().all()
            assert len(sessions) >= 1
            for s in sessions:
                s.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
            db.commit()
        assert c_by_email.get("/api/admin/overview").status_code == 401
        assert c_by_email.get("/api/auth/me").json()["user"] is None

        # Kiểm chứng DB chỉ có đúng 1 bản ghi admin (không nhân bản)
        with accounts_router.SessionLocal() as db:
            admins = db.execute(select(User).where(User.role == "admin")).scalars().all()
            assert len(admins) == 1 and admins[0].id == expected_id

        # Sai mật khẩu hoặc username không tồn tại trả CÙNG 401 thống nhất (chống dò tài khoản)
        c_bad = new_client(api)
        r_bad_pw = c_bad.post("/api/auth/login", json={"identifier": "admin", "password": "sai-mat-khau-dai"})
        r_bad_id = c_bad.post("/api/auth/login", json={"identifier": "unknown_user", "password": TEST_PASSWORD})
        assert r_bad_pw.status_code == r_bad_id.status_code == 401
        assert r_bad_pw.json()["detail"] == r_bad_id.json()["detail"]

        # Guest chưa đăng nhập & Admin sau logout đều bị chặn 401 ở API Admin
        assert new_client(api).get("/api/admin/overview").status_code == 401
        c_by_user.post("/api/auth/login", json={"identifier": "admin", "password": TEST_PASSWORD})
        assert c_by_user.get("/api/admin/overview").status_code == 200
        c_by_user.post("/api/auth/logout")
        assert c_by_user.get("/api/admin/overview").status_code == 401

    def test_cli_manage_admin_cap_nhat_lap_lai_an_toan_thu_hoi_phien_cu_va_khong_lo_mat_khau(self, tmp_path, monkeypatch):
        import json as _json
        import subprocess
        import sys
        from pathlib import Path
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker
        from app.accounts import service as accounts_service
        from app.accounts.policy import Role
        from app.persistence.classroom_models import AuthSession, User
        from app.persistence.db import Base

        script = Path(__file__).resolve().parents[1] / "scripts" / "manage_admin.py"

        # Case A: DB hoàn toàn trống (0 admin) -> --check trả adminCount=0; --apply thiếu --create-if-missing phải fail-closed
        empty_db = tmp_path / "admin-empty.db"
        empty_url = f"sqlite:///{empty_db.as_posix()}"
        env_base = {**dict(os.environ), "ADMIN_USERNAME": "admin", "ADMIN_PASSWORD": NEW_TEST_PASSWORD + "-init"}
        env_base.pop("ADMIN_EMAIL", None)
        chk0 = subprocess.run(
            [sys.executable, "-X", "utf8", str(script), "--database-url", empty_url, "--check", "--json"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env_base, check=False,
        )
        assert chk0.returncode == 0, chk0.stderr
        assert _json.loads(chk0.stdout)["adminCount"] == 0
        fail_no_create = subprocess.run(
            [sys.executable, "-X", "utf8", str(script), "--database-url", empty_url, "--apply", "--json"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env_base, check=False,
        )
        assert fail_no_create.returncode != 0
        assert (NEW_TEST_PASSWORD + "-init") not in (fail_no_create.stdout + fail_no_create.stderr)

        # Case B: Thiếu ADMIN_PASSWORD ở chế độ non-interactive -> mã lỗi 2
        env_nopw = {**env_base}
        env_nopw.pop("ADMIN_PASSWORD", None)
        fail_nopw = subprocess.run(
            [sys.executable, "-X", "utf8", str(script), "--database-url", empty_url, "--apply", "--create-if-missing"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env_nopw, check=False,
        )
        assert fail_nopw.returncode == 2

        # Case C: Mật khẩu yếu -> từ chối với mã lỗi != 0 và không in mật khẩu yếu
        env_weak = {**env_base, "ADMIN_PASSWORD": "123"}
        fail_weak = subprocess.run(
            [sys.executable, "-X", "utf8", str(script), "--database-url", empty_url, "--apply", "--create-if-missing"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env_weak, check=False,
        )
        assert fail_weak.returncode != 0

        # Case D: DB có sẵn 1 học sinh + 1 admin cũ kèm phiên đang hoạt động -> xoay khóa idempotent, giữ nguyên id & học sinh, thu hồi phiên cũ
        db_path = tmp_path / "admin-cli-isolated.db"
        db_url = f"sqlite:///{db_path.as_posix()}"
        eng = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(eng)
        Session = sessionmaker(bind=eng, autoflush=False)

        with Session() as db:
            stu = accounts_service.create_user(
                db, email="hs.keep@axo.edu.vn", display_name="Giữ nguyên", password=TEST_PASSWORD, role=Role.STUDENT
            )
            stu_sess = accounts_service.new_session(db, user_id=stu.id)
            old_admin, _, _ = accounts_service.upsert_or_rotate_admin_credentials(
                db,
                password=TEST_PASSWORD,
                email="existing.admin@axo.edu.vn",
                display_name="Admin Cũ",
                create_if_missing=True,
            )
            accounts_service.new_session(db, user_id=old_admin.id)
            db.commit()
            orig_admin_id = old_admin.id
            orig_stu_id = stu.id
            orig_stu_sess_token = stu_sess.token

        rotated_pw = NEW_TEST_PASSWORD + "-rot1"
        env = {**dict(os.environ), "ADMIN_USERNAME": "admin", "ADMIN_PASSWORD": rotated_pw}
        env.pop("ADMIN_EMAIL", None)

        res1 = subprocess.run(
            [sys.executable, "-X", "utf8", str(script), "--database-url", db_url, "--apply", "--json"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env, check=False,
        )
        assert res1.returncode == 0, res1.stderr
        assert rotated_pw not in (res1.stdout + res1.stderr)
        assert "pbkdf2_sha256" not in (res1.stdout + res1.stderr)
        out1 = _json.loads(res1.stdout)
        assert out1["action"] == "updated"
        assert out1["adminId"] == orig_admin_id
        assert out1["email"] == "existing.admin@axo.edu.vn"
        assert out1["revokedSessions"] == 1

        # Chạy --apply lần 2 (idempotent, không tạo bản ghi thứ hai)
        res2 = subprocess.run(
            [sys.executable, "-X", "utf8", str(script), "--database-url", db_url, "--apply", "--json"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env, check=False,
        )
        assert res2.returncode == 0, res2.stderr
        out2 = _json.loads(res2.stdout)
        assert out2["adminId"] == orig_admin_id

        with Session() as db:
            admins = db.execute(select(User).where(User.role == "admin")).scalars().all()
            assert len(admins) == 1 and admins[0].id == orig_admin_id
            assert db.get(User, orig_stu_id) is not None
            assert accounts_service.load_session(db, orig_stu_sess_token) is not None  # phiên học sinh giữ nguyên
            assert db.execute(select(AuthSession).where(AuthSession.user_id == orig_admin_id)).scalars().all() == []
            assert accounts_service.authenticate(db, identifier="admin", password=TEST_PASSWORD) is None
            assert accounts_service.authenticate(db, identifier="admin", password=rotated_pw).id == orig_admin_id
            assert accounts_service.authenticate(db, identifier="existing.admin@axo.edu.vn", password=rotated_pw).id == orig_admin_id

            # Case E: Nhiều tài khoản Admin mơ hồ -> --check báo ambiguous=True, --apply thiếu --email phải fail-closed (kể cả khi truyền --create-if-missing)
            second_admin = accounts_service.create_user(
                db, email="second.admin@axo.edu.vn", display_name="Admin 2", password=TEST_PASSWORD, role=Role.TEACHER
            )
            second_admin.role = "admin"
            db.commit()
            second_admin_id = second_admin.id

        chk_multi = subprocess.run(
            [sys.executable, "-X", "utf8", str(script), "--database-url", db_url, "--check", "--json"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env, check=False,
        )
        assert chk_multi.returncode == 0
        multi_state = _json.loads(chk_multi.stdout)
        assert multi_state["adminCount"] == 2
        assert multi_state["ambiguous"] is True
        assert multi_state["resolvedAdmin"] is None

        fail_ambig = subprocess.run(
            [sys.executable, "-X", "utf8", str(script), "--database-url", db_url, "--apply", "--create-if-missing", "--json"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env, check=False,
        )
        assert fail_ambig.returncode != 0
        assert rotated_pw not in (fail_ambig.stdout + fail_ambig.stderr)

        # Chỉ định rõ --email gỡ nhập nhằng -> cập nhật ĐÚNG tài khoản đích, không tạo Admin thứ 3
        ok_targeted = subprocess.run(
            [sys.executable, "-X", "utf8", str(script), "--database-url", db_url, "--apply", "--email", "second.admin@axo.edu.vn", "--json"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env, check=False,
        )
        assert ok_targeted.returncode == 0, ok_targeted.stderr
        assert _json.loads(ok_targeted.stdout)["adminId"] == second_admin_id
        with Session() as db:
            assert len(db.execute(select(User).where(User.role == "admin")).scalars().all()) == 2

        # Case F: Không cho phép nâng quyền tự động khi email đã thuộc về học sinh hiện có
        clash_db = tmp_path / "admin-clash.db"
        clash_url = f"sqlite:///{clash_db.as_posix()}"
        clash_eng = create_engine(clash_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(clash_eng)
        ClashSession = sessionmaker(bind=clash_eng, autoflush=False)
        with ClashSession() as db:
            accounts_service.create_user(
                db, email="student.only@axo.edu.vn", display_name="Học sinh", password=TEST_PASSWORD, role=Role.STUDENT
            )
            db.commit()
        fail_clash = subprocess.run(
            [
                sys.executable, "-X", "utf8", str(script),
                "--database-url", clash_url, "--apply", "--create-if-missing",
                "--email", "student.only@axo.edu.vn",
            ],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env, check=False,
        )
        assert fail_clash.returncode != 0
        with ClashSession() as db:
            u = db.execute(select(User).where(User.email == "student.only@axo.edu.vn")).scalar_one()
            assert u.role == "student"
        clash_eng.dispose()
        eng.dispose()

    def test_khoi_dong_backend_khong_tu_dong_tao_hoac_sua_admin(self, api, monkeypatch):
        """§5.1: Khởi động/gọi health/auth trên backend KHÔNG BAO GIỜ tự tạo hoặc tự đổi mật khẩu Admin từ env."""
        from sqlalchemy import select
        from app.accounts import router as accounts_router
        from app.persistence.classroom_models import User

        monkeypatch.setenv("ADMIN_USERNAME", "admin")
        monkeypatch.setenv("ADMIN_EMAIL", "should.not.autoseed@axo.edu.vn")
        monkeypatch.setenv("ADMIN_PASSWORD", NEW_TEST_PASSWORD + "-never-auto")

        c = new_client(api)
        assert c.get("/api/auth/me").status_code == 200
        assert c.post("/api/auth/login", json={"identifier": "admin", "password": NEW_TEST_PASSWORD + "-never-auto"}).status_code == 401
        with accounts_router.SessionLocal() as db:
            assert db.execute(select(User).where(User.role == "admin")).scalars().all() == []
