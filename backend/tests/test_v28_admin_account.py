# -*- coding: utf-8 -*-
"""AXO V2.8 — Kiểm thử tích hợp cho bảo mật Quên mật khẩu, Xuất dữ liệu Admin và thực thi cài đặt hệ thống."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.accounts import router as accounts_router
from tests.conftest_classroom import TEST_PASSWORD, api, login, new_client, register  # noqa: F401


@pytest.fixture(autouse=True)
def _reset_v28_in_memory_state():
    """Đảm bảo trạng thái bộ nhớ của router sạch giữa các bài kiểm thử."""
    orig_settings = dict(accounts_router._SYSTEM_SETTINGS)
    accounts_router._ADMIN_AUDIT_LOGS.clear()
    accounts_router._USER_EXTRA_META.clear()
    if hasattr(accounts_router, "_PASSWORD_RESET_TOKENS"):
        accounts_router._PASSWORD_RESET_TOKENS.clear()
    if hasattr(accounts_router, "set_password_reset_mail_sender"):
        accounts_router.set_password_reset_mail_sender(None)
    yield
    accounts_router._SYSTEM_SETTINGS.clear()
    accounts_router._SYSTEM_SETTINGS.update(orig_settings)
    if hasattr(accounts_router, "_PASSWORD_RESET_TOKENS"):
        accounts_router._PASSWORD_RESET_TOKENS.clear()
    if hasattr(accounts_router, "set_password_reset_mail_sender"):
        accounts_router.set_password_reset_mail_sender(None)


def _register_admin(api_root) -> object:
    c_admin = new_client(api_root)
    r = register(
        c_admin,
        email="quantri-v28@axo.edu.vn",
        name="Quản trị V2.8",
        role="admin",
        teacher_code="ADMIN2026",
    )
    assert r.status_code == 200
    assert r.json()["user"]["role"] == "admin"
    return c_admin


class TestQuenMatKhauAnToanV28:
    def test_khong_smtp_tra_trang_thai_trung_thuc_va_chan_chiem_tai_khoan_khong_token(self, api, monkeypatch):
        monkeypatch.delenv("ALGOSIM_SMTP_HOST", raising=False)
        monkeypatch.delenv("ALGOSIM_SMTP_FROM", raising=False)

        c_victim = new_client(api)
        register(c_victim, email="hocsinh@truong.edu.vn", name="Học sinh A")

        # Task 1 §8: endpoint trạng thái khôi phục công khai chỉ báo boolean khả dụng, không lộ bí mật
        r_status = c_victim.get("/api/auth/recovery-status")
        assert r_status.status_code == 200
        assert r_status.json() == {"emailRecoveryAvailable": False}

        # Kẻ tấn công biết email nạn nhân, gọi forgot-password rồi gọi thẳng reset-password mà không có token
        c_attacker = new_client(api)
        r_forgot_known = c_attacker.post(
            "/api/auth/forgot-password",
            json={"email": "hocsinh@truong.edu.vn"},
        )
        r_forgot_unknown = c_attacker.post(
            "/api/auth/forgot-password",
            json={"email": "khong-ton-tai@truong.edu.vn"},
        )
        assert r_forgot_known.status_code == 200
        assert r_forgot_unknown.status_code == 200

        body_known = r_forgot_known.json()
        body_unknown = r_forgot_unknown.json()
        assert body_known["smtpConfigured"] is False
        assert body_known["deliveryStatus"] == "BLOCKED_EXTERNAL_CONFIGURATION"
        assert "SMTP" not in body_known["message"]
        # Không làm lộ sự tồn tại của email và tuyệt đối không trả token thô ra HTTP
        assert body_known.keys() == body_unknown.keys()
        assert body_known["deliveryStatus"] == body_unknown["deliveryStatus"]
        assert "token" not in body_known
        assert "resetToken" not in body_known

        # Gọi reset-password không kèm token hợp lệ bắt buộc bị chặn 400
        r_takeover = c_attacker.post(
            "/api/auth/reset-password",
            json={"email": "hocsinh@truong.edu.vn", "newPassword": "mat-khau-ke-tan-cong-123"},
        )
        assert r_takeover.status_code == 400

        # Mật khẩu gốc của nạn nhân vẫn an toàn 100%
        c_check = new_client(api)
        assert login(c_check, email="hocsinh@truong.edu.vn", password=TEST_PASSWORD).status_code == 200

    def test_token_bam_sha256_dung_mot_lan_het_han_va_thu_hoi_phien_cu(self, api):
        delivered: list[dict[str, str]] = []
        accounts_router.set_password_reset_mail_sender(
            lambda email, token: delivered.append({"email": email, "token": token})
        )

        c_user = new_client(api)
        register(c_user, email="lan@truong.edu.vn", name="Lan")
        assert c_user.get("/api/auth/me").json()["user"] is not None

        # Email không tồn tại: trả cùng cấu trúc nhưng không gửi thư
        c_anon = new_client(api)
        r_status_ok = c_anon.get("/api/auth/recovery-status")
        assert r_status_ok.status_code == 200
        assert r_status_ok.json() == {"emailRecoveryAvailable": True}
        r_unknown = c_anon.post("/api/auth/forgot-password", json={"email": "nobody@truong.edu.vn"})
        assert r_unknown.status_code == 200
        assert r_unknown.json()["smtpConfigured"] is True
        assert r_unknown.json()["deliveryStatus"] == "SENT"
        assert len(delivered) == 0

        # Email tồn tại: sinh token ngẫu nhiên, chỉ lưu hash SHA-256 trong bộ nhớ
        r_known = c_anon.post("/api/auth/forgot-password", json={"email": "lan@truong.edu.vn"})
        assert r_known.status_code == 200
        assert r_known.json()["deliveryStatus"] == "SENT"
        assert "token" not in r_known.json()
        assert len(delivered) == 1
        raw_token = delivered[0]["token"]
        assert len(raw_token) >= 24
        assert raw_token not in str(accounts_router._PASSWORD_RESET_TOKENS)

        # Đặt lại mật khẩu thành công bằng token
        new_pw = "mat-khau-moi-hop-le-2026"
        r_reset = c_anon.post(
            "/api/auth/reset-password",
            json={"token": raw_token, "newPassword": new_pw},
        )
        assert r_reset.status_code == 200
        assert r_reset.json()["updated"] is True

        # Phiên đăng nhập cũ của Lan bị thu hồi ngay lập tức
        assert c_user.get("/api/auth/me").json()["user"] is None

        # Token chỉ được dùng đúng 1 lần — gửi lại phải bị từ chối 400
        r_replay = c_anon.post(
            "/api/auth/reset-password",
            json={"token": raw_token, "newPassword": "mat-khau-khac-99999"},
        )
        assert r_replay.status_code == 400

        # Đăng nhập bằng mật khẩu mới thành công
        c_fresh = new_client(api)
        assert login(c_fresh, email="lan@truong.edu.vn", password=new_pw).status_code == 200

        # Kiểm tra token hết hạn bị từ chối
        c_anon.post("/api/auth/forgot-password", json={"email": "lan@truong.edu.vn"})
        expired_raw = delivered[-1]["token"]
        for rec in accounts_router._PASSWORD_RESET_TOKENS.values():
            rec["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=5)
        r_expired = c_anon.post(
            "/api/auth/reset-password",
            json={"token": expired_raw, "newPassword": "mat-khau-het-han-1234"},
        )
        assert r_expired.status_code == 400


class TestAdminHoanThienVaXuatDuLieuV28:
    def test_xuat_csv_admin_phan_quyen_chat_khong_lo_hash_va_chong_csv_injection(self, api):
        c_admin = _register_admin(api)

        c_student = new_client(api)
        register(c_student, email="hs-export@axo.edu.vn", name="=CMD|' /C calc'!A0")

        c_guest = new_client(api)
        assert c_guest.get("/api/admin/export/users").status_code == 401
        assert c_guest.get("/api/admin/export/audit-logs").status_code == 401
        assert c_student.get("/api/admin/export/users").status_code == 403
        assert c_student.get("/api/admin/export/audit-logs").status_code == 403

        r_users_csv = c_admin.get("/api/admin/export/users")
        assert r_users_csv.status_code == 200
        assert "text/csv" in r_users_csv.headers["content-type"]
        assert "attachment;" in r_users_csv.headers.get("content-disposition", "")

        csv_text = r_users_csv.content.decode("utf-8-sig")
        assert "Email" in csv_text
        assert "hs-export@axo.edu.vn" in csv_text
        assert "pbkdf2_sha256" not in csv_text
        assert "password_hash" not in csv_text
        # Ký tự mở đầu công thức `=` phải được vô hiệu hóa bằng dấu nháy đơn dẫn đầu
        assert "'=CMD|" in csv_text

        r_audit_csv = c_admin.get("/api/admin/export/audit-logs")
        assert r_audit_csv.status_code == 200
        audit_csv_text = r_audit_csv.content.decode("utf-8-sig")
        assert "Xuất danh sách tài khoản" in audit_csv_text

        r_overview = c_admin.get("/api/admin/overview")
        assert r_overview.status_code == 200
        logs = r_overview.json()["auditLogs"]
        assert len(logs) >= 1
        assert all(isinstance(entry.get("timeTs"), int) and entry["timeTs"] > 0 for entry in logs)

    def test_tao_user_khong_mat_khau_dong_bo_settings_ui_va_khoa_phien_tuc_thi(self, api):
        c_admin = _register_admin(api)

        # 1. Tạo tài khoản từ giao diện Admin (không gửi password -> sinh mật khẩu tạm + chờ kích hoạt)
        r_create = c_admin.post(
            "/api/admin/users",
            json={
                "displayName": "Nguyễn Minh Khôi",
                "email": "khoi@truong.edu.vn",
                "role": "student",
                "school": "THPT Chu Văn An",
                "adminNote": "Lớp 11A1",
            },
        )
        assert r_create.status_code == 200
        u_created = r_create.json()["user"]
        assert u_created["mustChangePassword"] is True
        assert u_created["status"] == "pending_activation"
        assert u_created["adminNote"] == "Lớp 11A1"

        # 1b. Duyệt yêu cầu Giáo viên (`pending_teacher` -> `role="teacher"`) tự chuyển trạng thái sang `verified` và hạ quyền về `student` chuyển sang `active`
        r_pending_gv = c_admin.post(
            "/api/admin/users",
            json={
                "displayName": "Cô Trần Thu Hà",
                "email": "tranha@truong.edu.vn",
                "role": "student",
                "status": "pending_teacher",
                "school": "THPT Chu Văn An",
            },
        )
        assert r_pending_gv.status_code == 200
        gv_id = r_pending_gv.json()["user"]["id"]
        assert r_pending_gv.json()["user"]["status"] == "pending_teacher"

        r_approve_gv = c_admin.patch(f"/api/admin/users/{gv_id}", json={"role": "teacher"})
        assert r_approve_gv.status_code == 200
        assert r_approve_gv.json()["user"]["role"] == "teacher"
        assert r_approve_gv.json()["user"]["status"] == "verified"

        r_revert_stu = c_admin.patch(f"/api/admin/users/{gv_id}", json={"role": "student"})
        assert r_revert_stu.status_code == 200
        assert r_revert_stu.json()["user"]["role"] == "student"
        assert r_revert_stu.json()["user"]["status"] == "active"

        # 2. Học sinh đang đăng nhập bị Admin khóa -> thu hồi phiên ngay lập tức
        c_stu = new_client(api)
        r_stu = register(c_stu, email="active-stu@truong.edu.vn", name="Bình")
        stu_id = r_stu.json()["user"]["id"]
        assert c_stu.get("/api/auth/me").json()["user"] is not None

        r_patch = c_admin.patch(
            f"/api/admin/users/{stu_id}",
            json={"dailyLimit": 35, "isSuspended": True, "mustChangePassword": True},
        )
        assert r_patch.status_code == 200
        assert r_patch.json()["user"]["dailyLimit"] == 35
        assert r_patch.json()["user"]["status"] == "suspended"
        assert r_patch.json()["user"]["mustChangePassword"] is True

        # Phiên của Bình bị ngắt ngay, không cần chờ cookie hết hạn
        assert c_stu.get("/api/auth/me").json()["user"] is None
        assert login(new_client(api), email="active-stu@truong.edu.vn", password=TEST_PASSWORD).status_code == 403

        # 3. Lưu cài đặt theo đúng payload của UI Admin (`{ settings: quotaDraft }`) và thực thi allowNewRegistrations / maintenanceMode
        c_normal = new_client(api)
        register(c_normal, email="minh@truong.edu.vn", name="Minh")

        r_save = c_admin.put(
            "/api/admin/settings",
            json={
                "settings": {
                    "studentDailyRequests": 25,
                    "teacherDailyRequests": 75,
                    "studentDailyTokens": 35000,
                    "teacherDailyTokens": 160000,
                    "studentRatePerMin": 6,
                    "teacherRatePerMin": 18,
                    "vndBudgetRaw": "5.000.000",
                    "autoCutoffEnabled": False,
                    "allowNewRegistrations": False,
                    "maintenanceMode": True,
                }
            },
        )
        assert r_save.status_code == 200
        saved = r_save.json()["settings"]
        assert saved["studentDailyLimit"] == 25
        assert saved["teacherDailyLimit"] == 75
        assert saved["monthlyBudgetVnd"] == 5000000
        assert saved["autoCutoffEnabled"] is False

        # Đăng ký mới bị chặn khi allowNewRegistrations = False
        r_blocked_reg = register(new_client(api), email="blocked@truong.edu.vn", name="Blocked")
        assert r_blocked_reg.status_code == 403

        # Chế độ bảo trì chặn học sinh đăng nhập (503) nhưng vẫn cho Admin đăng nhập để tắt bảo trì
        assert login(new_client(api), email="minh@truong.edu.vn", password=TEST_PASSWORD).status_code == 503
        c_admin2 = new_client(api)
        assert login(c_admin2, email="quantri-v28@axo.edu.vn", password=TEST_PASSWORD).status_code == 200

    def test_ben_vung_sqlite_qua_xoa_bo_nho_va_thuc_thi_han_muc_telemetry(self, api):
        import json as _json

        c_admin = _register_admin(api)
        c_stu = new_client(api)
        r_stu = register(c_stu, email="hs-persist@axo.edu.vn", name="Học sinh Bền Vững")
        assert r_stu.status_code == 200
        stu_id = r_stu.json()["user"]["id"]
        stu_cookie = c_stu.cookies.get("algosim_session")
        assert stu_cookie

        # 1. Lưu cấu hình hệ thống + cập nhật hồ sơ & hạn mức riêng = 1 lượt/ngày
        assert (
            c_admin.put(
                "/api/admin/settings",
                json={
                    "settings": {
                        "studentDailyRequests": 12,
                        "teacherDailyRequests": 60,
                        "vndBudgetRaw": "2.500.000",
                    }
                },
            ).status_code
            == 200
        )
        assert (
            c_admin.patch(
                f"/api/admin/users/{stu_id}",
                json={"dailyLimit": 1, "school": "THPT Thực Nghiệm", "adminNote": "Kiểm tra restart"},
            ).status_code
            == 200
        )

        # 2. Ghi nhận 1 lượt phân tích thành công (có usage token SDK) + 1 lượt từ chối ngoài phạm vi
        accounts_router.record_analyze_telemetry(
            algosim_session=stu_cookie,
            status_code=200,
            body_bytes=_json.dumps({"status": "ok"}).encode("utf-8"),
            latency_ms=412,
            usage_before={"extract": {"calls": 0, "prompt_tokens": 0, "candidates_tokens": 0, "thoughts_tokens": 0, "total_tokens": 0}},
            usage_after={"extract": {"calls": 1, "prompt_tokens": 320, "candidates_tokens": 180, "thoughts_tokens": 90, "total_tokens": 590}},
        )
        accounts_router.record_analyze_telemetry(
            algosim_session=stu_cookie,
            status_code=200,
            body_bytes=_json.dumps({"status": "unsupported", "failure_category": "out_of_scope", "error_code": "OUT_OF_SCOPE"}).encode("utf-8"),
            latency_ms=88,
            usage_before={},
            usage_after={},
        )
        # The served analysis is charged by the usage ledger in the request itself (telemetry only observes).
        reservation = accounts_router.reserve_analysis_usage(stu_cookie, "a" + "d" * 32)
        assert not isinstance(reservation, tuple), reservation
        accounts_router.finalize_analysis_usage(reservation, served=True)

        # 3. Xóa sạch toàn bộ cache RAM để mô phỏng backend khởi động lại
        accounts_router._SYSTEM_SETTINGS.clear()
        accounts_router._ADMIN_AUDIT_LOGS.clear()
        accounts_router._USER_EXTRA_META.clear()

        # 4. Đọc lại từ SQLite qua /api/admin/overview -> toàn bộ cấu hình, hồ sơ, audit log và telemetry giữ nguyên
        r_ov = c_admin.get("/api/admin/overview")
        assert r_ov.status_code == 200
        ov = r_ov.json()
        assert ov["settings"]["studentDailyLimit"] == 12
        assert ov["settings"]["teacherDailyLimit"] == 60
        assert ov["settings"]["monthlyBudgetVnd"] == 2500000
        assert len(ov["auditLogs"]) >= 2

        stu_pub = next(u for u in ov["users"] if u["id"] == stu_id)
        assert stu_pub["dailyLimit"] == 1
        assert stu_pub["usedToday"] == 1
        assert stu_pub["school"] == "THPT Thực Nghiệm"
        assert stu_pub["adminNote"] == "Kiểm tra restart"

        stats = ov["stats"]
        assert stats["configuredModelId"] == "gemini-2.5-flash"
        assert stats["totalAnalyses"] == 2
        assert stats["succeededRequests"] == 1
        assert stats["refusedRequests"] == 1
        assert stats["failedRequests"] == 0
        assert stats["tokensMeasured"] is True
        assert stats["inputTokens7d"] == 320
        assert stats["outputTokens7d"] == 180
        assert stats["thoughtsTokens7d"] == 90
        assert stats["totalTokens7d"] == 590
        assert stats["estimatedCostVnd"] is None

        # 5. Học sinh đã dùng 1/1 lượt -> cổng hạn mức chặn 429 daily_quota_exceeded
        db = accounts_router.SessionLocal()
        try:
            gate_blocked = accounts_router.check_analyze_quota_and_maintenance(db, stu_cookie)
            assert gate_blocked is not None
            assert gate_blocked[0] == 429
            assert gate_blocked[1]["reason_code"] == "daily_quota_exceeded"
        finally:
            db.close()
        blocked = accounts_router.reserve_analysis_usage(stu_cookie, "a" + "c" * 32)
        assert isinstance(blocked, tuple) and blocked[0] == 429

        # 6. Admin cấp thêm +1 lượt hôm nay -> cổng hạn mức mở lại ngay
        assert c_admin.patch(f"/api/admin/users/{stu_id}", json={"bonusQuotaToday": 1}).status_code == 200
        db2 = accounts_router.SessionLocal()
        try:
            assert accounts_router.check_analyze_quota_and_maintenance(db2, stu_cookie) is None
        finally:
            db2.close()

    def test_seed_demo_accounts_tao_dung_3_tai_khoan_khong_hardcode_mat_khau(self, tmp_path):
        import subprocess
        import sys
        import json as _json
        from pathlib import Path

        db_file = tmp_path / "demo_isolated.db"
        receipt_1 = tmp_path / "receipt_1.json"
        receipt_2 = tmp_path / "receipt_2.json"
        script_path = Path(__file__).resolve().parents[1] / "scripts" / "seed_demo_accounts.py"

        res1 = subprocess.run(
            [sys.executable, "-X", "utf8", str(script_path), "--db-path", str(db_file), "--receipt-out", str(receipt_1)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        out1 = _json.loads(res1.stdout.strip())
        assert out1["ok"] is True
        assert out1["count"] == 3
        data1 = _json.loads(receipt_1.read_text(encoding="utf-8"))
        assert [a["role"] for a in data1["accounts"]] == ["admin", "teacher", "student"]
        assert all(len(a["password"]) >= 12 for a in data1["accounts"])

        res2 = subprocess.run(
            [sys.executable, "-X", "utf8", str(script_path), "--db-path", str(db_file), "--receipt-out", str(receipt_2)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        assert _json.loads(res2.stdout.strip())["count"] == 3
        data2 = _json.loads(receipt_2.read_text(encoding="utf-8"))
        # Mật khẩu sinh ngẫu nhiên mỗi lượt chạy, không cố định trong mã nguồn
        assert [a["password"] for a in data1["accounts"]] != [a["password"] for a in data2["accounts"]]

