# -*- coding: utf-8 -*-
"""Xác minh email, quên/đặt lại mật khẩu, thư giao dịch và Admin duy nhất (run `authentication-account-recovery`).

Mọi thư đi qua kênh gửi GIẢ (`mailer.set_email_transport`) hoặc `httpx.post` giả — không test nào gọi Resend thật.
Mật khẩu và khoá đều sinh ngẫu nhiên lúc chạy; không có giá trị bí mật cố định trong mã.
"""

from __future__ import annotations

import logging
import re
import secrets
import threading
from datetime import timedelta
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.accounts import email_templates, mailer, service, tokens
from app.accounts import router as accounts_router
from app.accounts.policy import Role
from app.persistence.classroom_models import AuthSession, AuthToken, EmailVerification, User
from app.persistence.db import Base
from tests.conftest_classroom import TEST_PASSWORD, api, login, new_client, register  # noqa: F401

NEW_PASSWORD = "Moi-" + secrets.token_urlsafe(12)
FAKE_KEY = "test-" + secrets.token_hex(12)
SENDER = "Axo <noreply@mail.example.test>"


class Outbox:
    def __init__(self) -> None:
        self.messages: list[mailer.OutgoingEmail] = []

    def __call__(self, msg: mailer.OutgoingEmail) -> mailer.SendResult:
        self.messages.append(msg)
        return mailer.SendResult("accepted", provider_id=f"fake-{len(self.messages)}")

    def of(self, category: str) -> list[mailer.OutgoingEmail]:
        return [m for m in self.messages if m.category == category]


def link_of(msg: mailer.OutgoingEmail) -> str:
    urls = re.findall(r"https?://\S+", msg.text)
    assert urls, "thư không có liên kết"
    return urls[0]


def param(msg: mailer.OutgoingEmail, name: str) -> str:
    return parse_qs(urlsplit(link_of(msg)).query)[name][0]


@pytest.fixture(autouse=True)
def _clean_state():
    accounts_router._AUTH_RATE_BUCKETS.clear()
    yield
    accounts_router._AUTH_RATE_BUCKETS.clear()


@pytest.fixture()
def outbox(monkeypatch):
    box = Outbox()
    monkeypatch.setenv("ALGOSIM_PUBLIC_APP_URL", "http://app.example.test")
    mailer.set_email_transport(box)
    return box


def make_admin(email: str = "quantri@example.test", password: str = TEST_PASSWORD) -> int:
    with accounts_router.SessionLocal() as db:
        user, _, _ = service.upsert_or_rotate_admin_credentials(
            db, password=password, email=email, display_name="Quản trị", create_if_missing=True
        )
        db.commit()
        return user.id


def age_tokens() -> None:
    """Bỏ qua khoảng chờ 60 giây giữa hai thư cùng mục đích."""
    with accounts_router.SessionLocal() as db:
        for row in db.execute(select(AuthToken)).scalars():
            row.created_at = row.created_at - timedelta(minutes=5)
        db.commit()


# ── Cấu hình ─────────────────────────────────────────────────────────────────────────────────────────────────────────

class TestCauHinhEmail:
    def test_mac_dinh_tat_va_khong_kha_dung(self, api):
        state = mailer.readiness()
        assert state["available"] is False
        assert "EMAIL_DISABLED" in state["issues"] and "RESEND_API_KEY_MISSING" in state["issues"]
        assert api.get("/api/auth/recovery-status").json() == {"emailRecoveryAvailable": False}

    def test_resend_day_du_thi_kha_dung_va_khong_lo_khoa(self, api, monkeypatch):
        monkeypatch.setenv("EMAIL_ENABLED", "true")
        monkeypatch.setenv("RESEND_API_KEY", FAKE_KEY)
        monkeypatch.setenv("EMAIL_FROM", SENDER)
        state = mailer.readiness()
        assert state["available"] is True and state["provider"] == "resend"
        assert state["senderDomain"] == "mail.example.test"
        assert FAKE_KEY not in repr(state)
        assert api.get("/api/auth/recovery-status").json() == {"emailRecoveryAvailable": True}

    @pytest.mark.parametrize(
        "env, issue",
        [
            ({"EMAIL_FROM": "khong-phai-email"}, "EMAIL_FROM_INVALID"),
            ({"ALGOSIM_PUBLIC_APP_URL": "http://app.example.test/duong-dan"}, "PUBLIC_APP_URL_INVALID"),
            ({"ALGOSIM_PUBLIC_APP_URL": "javascript:alert(1)"}, "PUBLIC_APP_URL_INVALID"),
            ({"EMAIL_PROVIDER": "khac"}, "EMAIL_PROVIDER_UNSUPPORTED"),
        ],
    )
    def test_cau_hinh_sai_bi_tu_choi(self, monkeypatch, env, issue):
        monkeypatch.setenv("EMAIL_ENABLED", "true")
        monkeypatch.setenv("RESEND_API_KEY", FAKE_KEY)
        monkeypatch.setenv("EMAIL_FROM", SENDER)
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        state = mailer.readiness()
        assert state["available"] is False and issue in state["issues"]

    def test_ttl_doc_tu_moi_truong_va_bi_kep(self, monkeypatch):
        assert tokens.token_ttl(tokens.PURPOSE_PASSWORD_RESET) == timedelta(minutes=15)
        assert tokens.token_ttl(tokens.PURPOSE_EMAIL_VERIFICATION) == timedelta(minutes=1440)
        monkeypatch.setenv("PASSWORD_RESET_TOKEN_TTL_MINUTES", "100000")
        assert tokens.token_ttl(tokens.PURPOSE_PASSWORD_RESET) == timedelta(minutes=60)
        monkeypatch.setenv("PASSWORD_RESET_TOKEN_TTL_MINUTES", "abc")
        assert tokens.token_ttl(tokens.PURPOSE_PASSWORD_RESET) == timedelta(minutes=15)


class TestMauThu:
    def test_tieu_de_va_noi_dung_thoat_html(self):
        link = "http://app.example.test/reset?reset_token=abc&x=<b>"
        reset = email_templates.password_reset_email(to="a@example.test", link=link, ttl_minutes=15)
        assert reset.subject == "Đặt lại mật khẩu tài khoản Axo"
        assert "<b>" not in reset.html and "&lt;b&gt;" in reset.html
        assert link in reset.text and "15 phút" in reset.text
        verify = email_templates.verification_email(
            to="a@example.test", display_name="<script>", link="http://app.example.test/verify-email?token=t",
            ttl_minutes=1440,
        )
        assert verify.subject == "Xác minh địa chỉ email tài khoản Axo"
        assert "<script>" not in verify.html
        changed = email_templates.password_changed_email(to="a@example.test", login_url="http://app.example.test/login")
        assert changed.subject == "Mật khẩu tài khoản Axo đã được thay đổi"
        for msg in (reset, verify, changed):
            assert "token" not in msg.subject.lower()


# ── Kênh gửi Resend (httpx giả) ──────────────────────────────────────────────────────────────────────────────────────

class TestKenhResend:
    @pytest.fixture(autouse=True)
    def _enable(self, monkeypatch):
        monkeypatch.setenv("EMAIL_ENABLED", "true")
        monkeypatch.setenv("RESEND_API_KEY", FAKE_KEY)
        monkeypatch.setenv("EMAIL_FROM", SENDER)

    def _msg(self, to: str = "nguoi.nhan@example.test") -> mailer.OutgoingEmail:
        return mailer.OutgoingEmail(to=to, subject="S", html="<p>h</p>", text="t", category="smoke_test",
                                    idempotency_key="idem-1")

    def test_thanh_cong_gui_dung_hop_dong_api(self, monkeypatch, caplog):
        seen = {}

        def fake_post(url, json=None, headers=None, timeout=None):
            seen.update(url=url, json=json, headers=headers, timeout=timeout)
            return httpx.Response(200, json={"id": "email-123"})

        monkeypatch.setattr(mailer.httpx, "post", fake_post)
        with caplog.at_level(logging.DEBUG):
            result = mailer.send_email(self._msg())
        assert result == mailer.SendResult("accepted", provider_id="email-123")
        assert seen["url"] == "https://api.resend.com/emails"
        assert seen["json"]["to"] == ["nguoi.nhan@example.test"] and seen["json"]["from"] == SENDER
        assert seen["headers"]["Authorization"] == f"Bearer {FAKE_KEY}"
        assert seen["headers"]["Idempotency-Key"] == "idem-1"
        assert FAKE_KEY not in caplog.text and "nguoi.nhan" not in caplog.text
        assert "recipient_domain=example.test" in caplog.text

    @pytest.mark.parametrize(
        "behaviour, reason",
        [
            ("timeout", "PROVIDER_TIMEOUT"),
            ("network", "PROVIDER_NETWORK_ERROR"),
            (429, "PROVIDER_RATE_LIMITED"),
            (500, "PROVIDER_HTTP_500"),
            (403, "PROVIDER_HTTP_403"),
        ],
    )
    def test_loi_nha_cung_cap_khong_nem_va_tra_ma(self, monkeypatch, behaviour, reason):
        def fake_post(*_a, **_k):
            if behaviour == "timeout":
                raise httpx.ReadTimeout("t")
            if behaviour == "network":
                raise httpx.ConnectError("c")
            return httpx.Response(behaviour, json={"message": "x"})

        monkeypatch.setattr(mailer.httpx, "post", fake_post)
        result = mailer.send_email(self._msg())
        assert result.status == "failed" and result.reason == reason

    def test_thieu_khoa_thi_khong_goi_mang(self, monkeypatch):
        monkeypatch.delenv("RESEND_API_KEY")
        monkeypatch.setattr(mailer.httpx, "post", lambda *a, **k: pytest.fail("không được gọi mạng"))
        assert mailer.send_email(self._msg()).status == "unavailable"

    def test_gioi_han_khoi_luong_theo_nguoi_nhan(self, monkeypatch):
        monkeypatch.setenv("EMAIL_MAX_PER_RECIPIENT_PER_HOUR", "2")
        monkeypatch.setattr(mailer.httpx, "post", lambda *a, **k: httpx.Response(200, json={"id": "x"}))
        assert [mailer.send_email(self._msg()).status for _ in range(3)] == ["accepted", "accepted", "throttled"]
        assert mailer.send_email(self._msg("khac@example.test")).status == "accepted"


# ── Token ────────────────────────────────────────────────────────────────────────────────────────────────────────────

class TestVongDoiToken:
    @pytest.fixture()
    def db(self, tmp_path):
        eng = create_engine(f"sqlite:///{(tmp_path / 't.db').as_posix()}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(eng)
        Session = sessionmaker(bind=eng, autoflush=False)
        session = Session()
        session.info["factory"] = Session
        yield session
        session.close()
        eng.dispose()

    def _user(self, db, email="hs@example.test") -> User:
        user = service.create_user(db, email=email, display_name="HS", password=TEST_PASSWORD, role=Role.STUDENT)
        db.commit()
        return user

    def test_luu_bam_dung_mot_lan_dung_muc_dich(self, db):
        user = self._user(db)
        raw = tokens.issue_token(db, user=user, purpose=tokens.PURPOSE_PASSWORD_RESET)
        db.commit()
        assert len(raw) >= 40
        row = db.execute(select(AuthToken)).scalar_one()
        assert row.token_hash == tokens.digest(raw) and raw not in (row.token_hash, row.email)
        assert tokens.consume_token(db, raw, purpose=tokens.PURPOSE_EMAIL_VERIFICATION) is None
        assert tokens.consume_token(db, raw, purpose=tokens.PURPOSE_PASSWORD_RESET).user_id == user.id
        assert tokens.consume_token(db, raw, purpose=tokens.PURPOSE_PASSWORD_RESET) is None
        assert tokens.consume_token(db, "", purpose=tokens.PURPOSE_PASSWORD_RESET) is None
        assert tokens.consume_token(db, "x" * 300, purpose=tokens.PURPOSE_PASSWORD_RESET) is None

    def test_het_han_va_thu_hoi_va_phat_hanh_lai(self, db):
        user = self._user(db)
        first = tokens.issue_token(db, user=user, purpose=tokens.PURPOSE_PASSWORD_RESET)
        second = tokens.issue_token(db, user=user, purpose=tokens.PURPOSE_PASSWORD_RESET)
        db.commit()
        assert tokens.consume_token(db, first, purpose=tokens.PURPOSE_PASSWORD_RESET) is None  # bị thay thế
        row = db.execute(select(AuthToken).where(AuthToken.token_hash == tokens.digest(second))).scalar_one()
        row.expires_at = tokens.utcnow() - timedelta(seconds=1)
        db.commit()
        assert tokens.consume_token(db, second, purpose=tokens.PURPOSE_PASSWORD_RESET) is None
        third = tokens.issue_token(db, user=user, purpose=tokens.PURPOSE_PASSWORD_RESET)
        assert tokens.revoke_user_tokens(db, user.id) == 1
        assert tokens.consume_token(db, third, purpose=tokens.PURPOSE_PASSWORD_RESET) is None

    def test_doi_email_lam_mat_xac_minh(self, db):
        user = self._user(db)
        tokens.mark_email_verified(db, user, method="email_link")
        assert tokens.is_email_verified(db, user) is True
        user.email = "moi@example.test"
        db.flush()
        assert tokens.is_email_verified(db, user) is False

    def test_tieu_thu_dong_thoi_chi_mot_yeu_cau_thang(self, db):
        user = self._user(db)
        raw = tokens.issue_token(db, user=user, purpose=tokens.PURPOSE_PASSWORD_RESET)
        db.commit()
        factory = db.info["factory"]
        wins: list[bool] = []
        barrier = threading.Barrier(8)

        def worker():
            session = factory()
            try:
                barrier.wait()
                rec = tokens.consume_token(session, raw, purpose=tokens.PURPOSE_PASSWORD_RESET)
                session.commit()
                wins.append(rec is not None)
            finally:
                session.close()

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        assert sorted(wins) == [False] * 7 + [True]


# ── Admin duy nhất ───────────────────────────────────────────────────────────────────────────────────────────────────

class TestAdminDuyNhat:
    def test_dang_nhap_bang_ten_hoac_email_cung_mot_danh_tinh(self, api, monkeypatch):
        monkeypatch.setenv("ADMIN_USERNAME", "admin")
        monkeypatch.delenv("ADMIN_EMAIL", raising=False)
        admin_id = make_admin()
        for ident in ("admin", "ADMIN", "quantri@example.test"):
            c = new_client(api)
            r = c.post("/api/auth/login", json={"identifier": ident, "password": TEST_PASSWORD})
            assert r.status_code == 200, ident
            assert r.json()["user"]["id"] == admin_id and r.json()["user"]["role"] == "admin"
            assert c.get("/api/admin/overview").status_code == 200

    def test_admin_email_lech_van_dang_nhap_bang_ten(self, api, monkeypatch):
        monkeypatch.setenv("ADMIN_USERNAME", "admin")
        monkeypatch.setenv("ADMIN_EMAIL", "email.cu.trong.env@example.test")
        admin_id = make_admin("quantri.that@example.test")
        r = new_client(api).post("/api/auth/login", json={"identifier": "admin", "password": TEST_PASSWORD})
        assert r.status_code == 200 and r.json()["user"]["id"] == admin_id

    def test_nhieu_admin_thi_ten_dang_nhap_fail_closed(self, api, monkeypatch):
        monkeypatch.setenv("ADMIN_USERNAME", "admin")
        monkeypatch.delenv("ADMIN_EMAIL", raising=False)
        make_admin("a1@example.test")
        with accounts_router.SessionLocal() as db:
            second = service.create_user(db, email="a2@example.test", display_name="A2", password=TEST_PASSWORD,
                                         role=Role.TEACHER)
            second.role = "admin"
            db.commit()
        r = new_client(api).post("/api/auth/login", json={"identifier": "admin", "password": TEST_PASSWORD})
        assert r.status_code == 401

    def test_dang_ky_cong_khai_khong_bao_gio_tao_admin(self, api):
        r = register(new_client(api), email="muon.lam.admin@example.test", name="X", role="admin")
        assert r.status_code in (200, 403)
        if r.status_code == 200:
            assert r.json()["user"]["role"] != "admin"


class TestChanDoanManageAdmin:
    """`manage_admin.py --check` chỉ đọc, che email, và gọi đúng tên nguyên nhân."""

    @staticmethod
    def _inspect(db_url: str) -> dict:
        import importlib.util
        from pathlib import Path

        path = Path(__file__).resolve().parents[1] / "scripts" / "manage_admin.py"
        spec = importlib.util.spec_from_file_location("_manage_admin_under_test", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.inspect_admin_state(db_url)

    def test_chan_doan_cac_trang_thai(self, tmp_path, monkeypatch):
        missing = tmp_path / "chua-co.db"
        state = self._inspect(f"sqlite:///{missing.as_posix()}")
        assert state["diagnosis"] == "SCHEMA_MISSING" and not missing.exists()  # không tạo tệp

        url = f"sqlite:///{(tmp_path / 'a.db').as_posix()}"
        eng = create_engine(url)
        Base.metadata.create_all(eng)
        Session = sessionmaker(bind=eng)
        monkeypatch.setenv("ADMIN_USERNAME", "admin")
        monkeypatch.setenv("ADMIN_PASSWORD", TEST_PASSWORD)
        monkeypatch.setenv("ADMIN_EMAIL", "quantri@example.test")
        assert self._inspect(url)["diagnosis"] == "ADMIN_NOT_CREATED"

        with Session() as db:
            service.upsert_or_rotate_admin_credentials(db, password=TEST_PASSWORD, email="quantri@example.test",
                                                       create_if_missing=True)
            db.commit()
        ok = self._inspect(url)
        assert ok["diagnosis"] == "OK" and ok["adminCount"] == 1 and ok["configuredPasswordMatchesStoredHash"] is True
        assert "quantri@example.test" not in repr(ok) and ok["resolvedAdmin"]["email"] == "qu***@example.test"

        monkeypatch.setenv("ADMIN_PASSWORD", NEW_PASSWORD)
        assert self._inspect(url)["diagnosis"] == "ADMIN_PASSWORD_NOT_SYNCHRONIZED"
        monkeypatch.setenv("ADMIN_PASSWORD", TEST_PASSWORD)
        monkeypatch.setenv("ADMIN_EMAIL", "email.khac@example.test")
        assert self._inspect(url)["diagnosis"] == "ADMIN_CONFIGURATION_MISMATCH"
        eng.dispose()


# ── Quên / đặt lại mật khẩu ──────────────────────────────────────────────────────────────────────────────────────────

class TestKhoiPhucMatKhau:
    def test_phan_hoi_trung_tinh_admin_va_email_la_khong_nhan_thu(self, api, outbox):
        make_admin()
        register(new_client(api), email="hs@example.test", name="HS")
        c = new_client(api)
        bodies = [c.post("/api/auth/forgot-password", json={"email": e}).json()
                  for e in ("quantri@example.test", "khong.co@example.test", "hs@example.test")]
        assert bodies[0] == bodies[1] == bodies[2]
        assert bodies[0]["message"] == accounts_router.RECOVERY_NEUTRAL_MESSAGE
        assert [m.to for m in outbox.of("password_reset")] == ["hs@example.test"]

    def test_khoang_cho_chong_doi_thu(self, api, outbox):
        register(new_client(api), email="hs@example.test", name="HS")
        c = new_client(api)
        for _ in range(3):
            assert c.post("/api/auth/forgot-password", json={"email": "hs@example.test"}).status_code == 200
        assert len(outbox.of("password_reset")) == 1
        age_tokens()
        c.post("/api/auth/forgot-password", json={"email": "hs@example.test"})
        assert len(outbox.of("password_reset")) == 2

    def test_lien_ket_dung_url_cau_hinh_khong_dung_host_header(self, api, outbox):
        register(new_client(api), email="hs@example.test", name="HS")
        r = new_client(api).post(
            "/api/auth/forgot-password", json={"email": "hs@example.test"},
            headers={"Host": "evil.example", "X-Forwarded-Host": "evil.example"},
        )
        assert r.status_code in (200, 400)
        if r.status_code == 200:
            msg = outbox.of("password_reset")[0]
            assert link_of(msg).startswith("http://app.example.test/reset?reset_token=")
            assert "evil" not in msg.html + msg.text

    def test_dat_lai_thu_hoi_phien_cu_gui_thong_bao_va_xac_minh_email(self, api, outbox, caplog):
        victim = new_client(api)
        register(victim, email="hs@example.test", name="HS")
        assert victim.get("/api/auth/me").json()["user"]["emailVerified"] is False
        anon = new_client(api)
        with caplog.at_level(logging.DEBUG):
            anon.post("/api/auth/forgot-password", json={"email": "hs@example.test"})
            raw = param(outbox.of("password_reset")[0], "reset_token")
            weak = anon.post("/api/auth/reset-password", json={"token": raw, "newPassword": "123"})
            assert weak.status_code == 400  # mật khẩu yếu KHÔNG tiêu thụ token
            ok = anon.post("/api/auth/reset-password", json={"token": raw, "newPassword": NEW_PASSWORD})
        assert ok.status_code == 200 and ok.json() == {"ok": True, "updated": True}
        assert raw not in caplog.text and raw not in ok.text
        assert victim.get("/api/auth/me").json()["user"] is None
        assert anon.get("/api/auth/me").json()["user"] is None  # đặt lại KHÔNG tự đăng nhập
        assert login(new_client(api), email="hs@example.test", password=TEST_PASSWORD).status_code == 401
        fresh = new_client(api)
        assert login(fresh, email="hs@example.test", password=NEW_PASSWORD).status_code == 200
        assert fresh.get("/api/auth/me").json()["user"]["emailVerified"] is True
        changed = outbox.of("password_changed")
        assert len(changed) == 1 and changed[0].to == "hs@example.test"
        assert link_of(changed[0]) == "http://app.example.test/login"
        assert anon.post("/api/auth/reset-password", json={"token": raw, "newPassword": NEW_PASSWORD}).status_code == 400

    def test_token_khong_dung_cho_tai_khoan_da_doi_email(self, api, outbox):
        register(new_client(api), email="hs@example.test", name="HS")
        anon = new_client(api)
        anon.post("/api/auth/forgot-password", json={"email": "hs@example.test"})
        raw = param(outbox.of("password_reset")[0], "reset_token")
        with accounts_router.SessionLocal() as db:
            db.execute(select(User).where(User.email == "hs@example.test")).scalar_one().email = "doi@example.test"
            db.commit()
        assert anon.post("/api/auth/reset-password", json={"token": raw, "newPassword": NEW_PASSWORD}).status_code == 400

    def test_tai_khoan_bi_khoa_khong_nhan_thu(self, api, outbox):
        make_admin()
        stu = register(new_client(api), email="hs@example.test", name="HS").json()["user"]
        admin = new_client(api)
        assert login(admin, email="quantri@example.test", password=TEST_PASSWORD).status_code == 200
        assert admin.patch(f"/api/admin/users/{stu['id']}", json={"isSuspended": True}).status_code == 200
        new_client(api).post("/api/auth/forgot-password", json={"email": "hs@example.test"})
        assert outbox.of("password_reset") == []

    def test_khong_co_kenh_thu_thi_bao_khong_kha_dung(self, api):
        r = new_client(api).post("/api/auth/forgot-password", json={"email": "hs@example.test"})
        assert r.status_code == 200
        assert r.json()["deliveryStatus"] == "BLOCKED_EXTERNAL_CONFIGURATION"
        assert r.json()["smtpConfigured"] is False

    def test_gioi_han_toc_do_quen_mat_khau(self, api, outbox, monkeypatch):
        monkeypatch.setenv("AUTH_RATE_LIMIT_MAX_ATTEMPTS", "3")
        c = new_client(api)
        codes = [c.post("/api/auth/forgot-password", json={"email": "x@example.test"}).status_code for _ in range(5)]
        assert codes[:3] == [200, 200, 200] and 429 in codes[3:]


# ── Đổi mật khẩu khi đã đăng nhập ────────────────────────────────────────────────────────────────────────────────────

class TestDoiMatKhau:
    def test_giu_phien_hien_tai_dang_xuat_phien_khac_va_thong_bao(self, api, outbox):
        a = new_client(api)
        register(a, email="hs@example.test", name="HS")
        b = new_client(api)
        assert login(b, email="hs@example.test", password=TEST_PASSWORD).status_code == 200
        new_client(api).post("/api/auth/forgot-password", json={"email": "hs@example.test"})
        pending = param(outbox.of("password_reset")[0], "reset_token")
        r = a.post("/api/auth/password", json={"currentPassword": TEST_PASSWORD, "newPassword": NEW_PASSWORD})
        assert r.status_code == 200
        assert a.get("/api/auth/me").json()["user"] is not None
        assert b.get("/api/auth/me").json()["user"] is None
        assert [m.to for m in outbox.of("password_changed")] == ["hs@example.test"]
        anon = new_client(api)
        assert anon.post("/api/auth/reset-password", json={"token": pending, "newPassword": NEW_PASSWORD + "x"}).status_code == 400


# ── Xác minh email khi đăng ký ───────────────────────────────────────────────────────────────────────────────────────

class TestXacMinhEmail:
    def test_dang_ky_gui_thu_xac_minh_va_xac_minh_bang_post(self, api, outbox):
        c = new_client(api)
        r = register(c, email="hs@example.test", name="HS")
        assert r.status_code == 200 and r.json()["verification"] == {"status": "queued"}
        msg = outbox.of("verify_email")[0]
        assert msg.to == "hs@example.test"
        assert link_of(msg).startswith("http://app.example.test/verify-email?token=")
        raw = param(msg, "token")
        assert raw not in r.text
        assert c.get("/api/auth/verify-email").status_code == 405  # GET không tiêu thụ token
        assert c.post("/api/auth/verify-email", json={"token": raw}).json() == {"ok": True, "verified": True}
        assert c.get("/api/auth/me").json()["user"]["emailVerified"] is True
        assert c.post("/api/auth/verify-email", json={"token": raw}).status_code == 400
        assert c.post("/api/auth/verify-email/resend").json()["status"] == "already_verified"

    def test_token_xac_minh_khong_dat_lai_duoc_mat_khau(self, api, outbox):
        register(new_client(api), email="hs@example.test", name="HS")
        raw = param(outbox.of("verify_email")[0], "token")
        r = new_client(api).post("/api/auth/reset-password", json={"token": raw, "newPassword": NEW_PASSWORD})
        assert r.status_code == 400

    def test_gui_lai_co_khoang_cho_va_retry_after(self, api, outbox):
        c = new_client(api)
        register(c, email="hs@example.test", name="HS")
        r = c.post("/api/auth/verify-email/resend")
        assert r.status_code == 429 and int(r.headers["Retry-After"]) > 0
        age_tokens()
        assert c.post("/api/auth/verify-email/resend").json() == {"ok": True, "status": "queued"}
        first, second = outbox.of("verify_email")
        old = param(first, "token")
        assert new_client(api).post("/api/auth/verify-email", json={"token": old}).status_code == 400
        assert c.post("/api/auth/verify-email", json={"token": param(second, "token")}).status_code == 200

    def test_gui_lai_can_dang_nhap(self, api, outbox):
        assert new_client(api).post("/api/auth/verify-email/resend").status_code == 401

    def test_khong_co_kenh_thu_dang_ky_van_thanh_cong(self, api):
        c = new_client(api)
        r = register(c, email="hs@example.test", name="HS")
        assert r.status_code == 200 and r.json()["verification"] == {"status": "unavailable"}
        assert c.post("/api/auth/verify-email/resend").json() == {"ok": False, "status": "unavailable"}
        assert login(new_client(api), email="hs@example.test", password=TEST_PASSWORD).status_code == 200


class TestXoaTaiKhoan:
    def test_admin_xoa_tai_khoan_co_token_va_xac_minh(self, api, outbox):
        make_admin()
        c = new_client(api)
        stu = register(c, email="hs@example.test", name="HS").json()["user"]
        c.post("/api/auth/verify-email", json={"token": param(outbox.of("verify_email")[0], "token")})
        new_client(api).post("/api/auth/forgot-password", json={"email": "hs@example.test"})
        admin = new_client(api)
        login(admin, email="quantri@example.test", password=TEST_PASSWORD)
        assert admin.delete(f"/api/admin/users/{stu['id']}").status_code == 200
        with accounts_router.SessionLocal() as db:
            assert db.execute(select(AuthToken).where(AuthToken.user_id == stu["id"])).first() is None
            assert db.execute(select(EmailVerification).where(EmailVerification.user_id == stu["id"])).first() is None
            assert db.execute(select(AuthSession).where(AuthSession.user_id == stu["id"])).first() is None
