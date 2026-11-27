# -*- coding: utf-8 -*-
"""Kiểm thử hardening triển khai & bảo mật production (Phase 6–8).

100% offline, dùng DB cô lập theo fixture `conftest_classroom.api`.
"""
from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from starlette.requests import Request

import app.accounts.router as accounts_router
import app.main as main_mod
from tests.conftest_classroom import TEST_PASSWORD, api, login, new_client, register  # noqa: F401


@pytest.fixture(autouse=True)
def _clear_auth_rate_buckets():
    with accounts_router._AUTH_RATE_LOCK:
        accounts_router._AUTH_RATE_BUCKETS.clear()
    yield
    with accounts_router._AUTH_RATE_LOCK:
        accounts_router._AUTH_RATE_BUCKETS.clear()


def _fake_request(scheme: str = "http", client_host: str = "203.0.113.10", headers: dict[str, str] | None = None) -> Request:
    raw_headers = [
        (k.lower().encode("latin-1"), v.encode("latin-1"))
        for k, v in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "method": "POST",
        "scheme": scheme,
        "path": "/api/auth/login",
        "headers": raw_headers,
        "client": (client_host, 44321),
    }
    return Request(scope)


class TestCookieAndSecurityHeaders:
    def test_cookie_secure_auto_follows_https_and_cookie_secure_env(self, monkeypatch):
        monkeypatch.delenv("COOKIE_SECURE", raising=False)
        monkeypatch.delenv("COOKIE_SAMESITE", raising=False)
        monkeypatch.delenv("ALGOSIM_PUBLIC_APP_URL", raising=False)
        monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)

        assert accounts_router._cookie_settings(_fake_request(scheme="http")) == {
            "httponly": True,
            "samesite": "lax",
            "secure": False,
            "path": "/",
        }
        assert accounts_router._cookie_settings(_fake_request(scheme="https"))["secure"] is True

        monkeypatch.setenv("ALGOSIM_PUBLIC_APP_URL", "https://hoclieu.tech")
        assert accounts_router._cookie_settings(_fake_request(scheme="http"))["secure"] is True

        monkeypatch.delenv("ALGOSIM_PUBLIC_APP_URL", raising=False)
        monkeypatch.setenv("COOKIE_SECURE", "1")
        assert accounts_router._cookie_settings(_fake_request(scheme="http"))["secure"] is True

        monkeypatch.setenv("COOKIE_SECURE", "0")
        assert accounts_router._cookie_settings(_fake_request(scheme="https"))["secure"] is False

        monkeypatch.setenv("COOKIE_SAMESITE", "none")
        assert accounts_router._cookie_settings(_fake_request(scheme="http"))["secure"] is True
        assert accounts_router._cookie_settings(_fake_request(scheme="http"))["samesite"] == "none"

    def test_x_forwarded_proto_only_trusted_when_enabled_and_peer_trusted(self, monkeypatch):
        monkeypatch.delenv("COOKIE_SECURE", raising=False)
        monkeypatch.delenv("ALGOSIM_PUBLIC_APP_URL", raising=False)
        monkeypatch.delenv("UVICORN_FORWARDED_ALLOW_IPS", raising=False)

        untrusted_req = _fake_request(
            scheme="http",
            client_host="203.0.113.10",
            headers={"X-Forwarded-Proto": "https", "X-Forwarded-For": "198.51.100.7"},
        )
        trusted_req = _fake_request(
            scheme="http",
            client_host="127.0.0.1",
            headers={"X-Forwarded-Proto": "https", "X-Forwarded-For": "1.2.3.4, 198.51.100.7"},
        )

        monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
        assert accounts_router._cookie_settings(untrusted_req)["secure"] is False
        assert accounts_router._client_ip(untrusted_req) == "203.0.113.10"
        assert accounts_router._cookie_settings(trusted_req)["secure"] is False
        assert accounts_router._client_ip(trusted_req) == "127.0.0.1"

        # Even with TRUST_PROXY_HEADERS=1, an untrusted TCP peer CANNOT spoof X-Forwarded-For / X-Forwarded-Proto
        monkeypatch.setenv("TRUST_PROXY_HEADERS", "1")
        assert accounts_router._cookie_settings(untrusted_req)["secure"] is False
        assert accounts_router._client_ip(untrusted_req) == "203.0.113.10"

        # Trusted peer (127.0.0.1) uses rightmost untrusted hop, defeating client-prepended spoofed XFF
        assert accounts_router._cookie_settings(trusted_req)["secure"] is True
        assert accounts_router._client_ip(trusted_req) == "198.51.100.7"

        # Multi-proxy chain with CIDR trust skips trusted Docker bridge hop and returns real client IP
        monkeypatch.setenv("UVICORN_FORWARDED_ALLOW_IPS", "127.0.0.1,172.18.0.0/16")
        bridge_req = _fake_request(
            scheme="http",
            client_host="172.18.0.5",
            headers={
                "X-Forwarded-Proto": "https",
                "X-Forwarded-For": "bad-token, 198.0.2.99, 198.51.100.42, 172.18.0.2",
            },
        )
        assert accounts_router._cookie_settings(bridge_req)["secure"] is True
        assert accounts_router._client_ip(bridge_req) == "198.51.100.42"

    def test_cookie_secure_header_emitted_on_me_login_and_logout(self, api, monkeypatch):
        monkeypatch.setenv("COOKIE_SECURE", "1")
        monkeypatch.setenv("ALGOSIM_PUBLIC_APP_URL", "https://hoclieu.tech")
        r_reg = register(api, email="cookie.sec@axo.edu.vn", name="Bảo mật Cookie")
        assert r_reg.status_code == 200
        set_cookie_hdr = "; ".join(r_reg.headers.get_list("set-cookie")).lower()
        assert "httponly" in set_cookie_hdr
        assert "samesite=lax" in set_cookie_hdr
        assert "secure" in set_cookie_hdr
        assert r_reg.headers.get("x-content-type-options") == "nosniff"

        r_logout = api.post("/api/auth/logout")
        assert r_logout.status_code == 200
        del_cookie_hdr = "; ".join(r_logout.headers.get_list("set-cookie")).lower()
        assert "secure" in del_cookie_hdr
        assert "samesite=lax" in del_cookie_hdr


class TestAuthRateLimiting:
    def test_login_rate_limit_blocks_bruteforce_and_resets_after_success(self, api, monkeypatch):
        register(api, email="victim@axo.edu.vn", name="Nạn nhân")
        monkeypatch.setenv("AUTH_RATE_LIMIT_MAX_ATTEMPTS", "3")
        monkeypatch.setenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60")

        c = new_client(api)
        for _ in range(3):
            r = login(c, email="victim@axo.edu.vn", password=TEST_PASSWORD + "-wrong")
            assert r.status_code == 401

        blocked = login(c, email="victim@axo.edu.vn", password=TEST_PASSWORD)
        assert blocked.status_code == 429
        assert int(blocked.headers.get("retry-after", "0")) >= 1

        # Tài khoản khác vẫn đăng nhập bình thường (chống lock chéo tài khoản cùng IP trong ngưỡng IP tổng)
        register(api, email="other@axo.edu.vn", name="Người khác")
        c2 = new_client(api)
        assert login(c2, email="other@axo.edu.vn", password=TEST_PASSWORD).status_code == 200

        # Khi hết cửa sổ thời gian, tài khoản từng bị chặn phục hồi bình thường
        real_monotonic = accounts_router.time.monotonic
        monkeypatch.setattr(accounts_router.time, "monotonic", lambda: real_monotonic() + 65.0)
        assert login(c, email="victim@axo.edu.vn", password=TEST_PASSWORD).status_code == 200

    def test_school_shared_nat_many_distinct_students_login_without_false_lockout(self, api, monkeypatch):
        emails = [f"hs{idx}@truong.edu.vn" for idx in range(30)]
        for idx, em in enumerate(emails):
            c_reg = new_client(api)
            assert register(c_reg, email=em, name=f"Học sinh {idx}").status_code == 200

        # Đặt trần IP chung thấp (20) nhưng 30 học sinh hợp lệ cùng IP NAT trường học vẫn đăng nhập 200 toàn bộ
        monkeypatch.setenv("AUTH_RATE_LIMIT_MAX_ATTEMPTS", "3")
        monkeypatch.setenv("AUTH_RATE_LIMIT_IP_MAX_ATTEMPTS", "20")
        monkeypatch.setenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60")
        for em in emails:
            c_stu = new_client(api)
            res = login(c_stu, email=em, password=TEST_PASSWORD)
            assert res.status_code == 200, (em, res.text)

    def test_spoofed_x_forwarded_for_cannot_bypass_rate_limit_without_proxy_trust(self, api, monkeypatch):
        register(api, email="spoof.victim@axo.edu.vn", name="Nạn nhân IP giả")
        monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
        monkeypatch.setenv("AUTH_RATE_LIMIT_MAX_ATTEMPTS", "2")
        monkeypatch.setenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60")

        c = new_client(api)
        for idx in range(2):
            r = c.post(
                "/api/auth/login",
                json={"email": "spoof.victim@axo.edu.vn", "password": TEST_PASSWORD + "-wrong"},
                headers={"X-Forwarded-For": f"198.51.100.{idx + 10}"},
            )
            assert r.status_code == 401

        blocked = c.post(
            "/api/auth/login",
            json={"email": "spoof.victim@axo.edu.vn", "password": TEST_PASSWORD + "-wrong"},
            headers={"X-Forwarded-For": "198.51.100.99"},
        )
        assert blocked.status_code == 429

    def test_register_forgot_and_reset_password_rate_limits(self, api, monkeypatch):
        monkeypatch.setenv("AUTH_RATE_LIMIT_MAX_ATTEMPTS", "2")
        monkeypatch.setenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60")

        c_reg = new_client(api)
        for idx in range(2):
            res = c_reg.post(
                "/api/auth/register",
                json={"email": "same.reg@axo.edu.vn", "displayName": f"Thử {idx}", "password": TEST_PASSWORD},
            )
            assert res.status_code in (200, 400)
        assert c_reg.post(
            "/api/auth/register",
            json={"email": "same.reg@axo.edu.vn", "displayName": "Thử 3", "password": TEST_PASSWORD},
        ).status_code == 429

        c_forgot = new_client(api)
        for _ in range(2):
            assert c_forgot.post("/api/auth/forgot-password", json={"email": "reset@axo.edu.vn"}).status_code == 200
        assert c_forgot.post("/api/auth/forgot-password", json={"email": "reset@axo.edu.vn"}).status_code == 429

        c_reset = new_client(api)
        for _ in range(2):
            assert c_reset.post(
                "/api/auth/reset-password",
                json={"token": "tok-invalid", "newPassword": TEST_PASSWORD},
            ).status_code == 400
        assert c_reset.post(
            "/api/auth/reset-password",
            json={"token": "tok-invalid", "newPassword": TEST_PASSWORD},
        ).status_code == 429


class TestCorsHealthAndDatabaseHardening:
    def test_cors_settings_default_and_explicit_override(self, monkeypatch):
        monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
        origins, allow_creds = main_mod._resolve_cors_settings()
        assert "*" not in origins
        assert "https://hoclieu.tech" in origins
        assert "http://localhost:3000" in origins
        assert allow_creds is True

        monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://hoclieu.tech/")
        origins2, allow_creds2 = main_mod._resolve_cors_settings()
        assert origins2 == ["https://hoclieu.tech"]
        assert allow_creds2 is True

        monkeypatch.setenv("CORS_ALLOW_ORIGINS", "*")
        origins3, allow_creds3 = main_mod._resolve_cors_settings()
        assert origins3 == ["*"]
        assert allow_creds3 is False

    def test_cors_middleware_allows_hoclieu_and_rejects_evil_origin(self, api):
        ok_resp = api.get("/api/health", headers={"Origin": "https://hoclieu.tech"})
        assert ok_resp.status_code == 200
        assert ok_resp.headers.get("access-control-allow-origin") == "https://hoclieu.tech"
        assert ok_resp.headers.get("access-control-allow-credentials") == "true"
        assert ok_resp.headers.get("x-content-type-options") == "nosniff"
        assert ok_resp.json()["dbConnected"] is True

        evil_resp = api.get("/api/health", headers={"Origin": "https://evil.example"})
        assert evil_resp.status_code == 200
        assert evil_resp.headers.get("access-control-allow-origin") is None

    def test_health_returns_503_without_traceback_when_db_fails(self, api, monkeypatch):
        class _BrokenSession:
            def __enter__(self):
                raise RuntimeError("simulated db outage")

            def __exit__(self, *args):
                return False

        monkeypatch.setattr(main_mod, "SessionLocal", lambda: _BrokenSession())
        res = api.get("/api/health")
        assert res.status_code == 503
        body = res.json()
        assert body["ok"] is False
        assert body["dbConnected"] is False
        assert "Traceback" not in res.text
        assert "simulated db outage" not in res.text

    def test_postgres_scheme_normalization_in_db_module(self):
        db_src = (Path(__file__).resolve().parents[1] / "app" / "persistence" / "db.py").read_text(encoding="utf-8")
        assert 'startswith("postgres://")' in db_src
        assert 'startswith("postgresql://")' in db_src
        assert '"postgresql+psycopg2://"' in db_src

    def test_diagnostics_runtime_stays_200_during_db_outage_without_secrets(self, api, monkeypatch):
        class _BrokenSession:
            def __enter__(self):
                raise RuntimeError("simulated db outage")

            def __exit__(self, *args):
                return False

        monkeypatch.setattr(main_mod, "SessionLocal", lambda: _BrokenSession())
        assert api.get("/api/health").status_code == 503
        diag = api.get("/api/diagnostics/runtime")
        assert diag.status_code == 200
        body = diag.json()
        assert body["cache_version"]
        assert "GEMINI_API_KEY" not in diag.text


class TestCsrfAndProxyTrustDefense:
    def test_csrf_guard_allows_hoclieu_cross_origin_and_blocks_evil_origin_referer_null_and_cross_site(self, api):
        r_reg = register(api, email="csrf.user@axo.edu.vn", name="Người dùng CSRF")
        assert r_reg.status_code == 200

        # Untrusted Origin cannot mutate state even with an active session cookie (bodyless POST /api/auth/logout)
        r_evil_orig = api.post("/api/auth/logout", headers={"Origin": "https://evil.example"})
        assert r_evil_orig.status_code == 403
        assert r_evil_orig.headers.get("access-control-allow-origin") is None
        assert r_evil_orig.headers.get("x-content-type-options") == "nosniff"
        assert api.get("/api/auth/me").json()["user"]["email"] == "csrf.user@axo.edu.vn"

        # Null Origin (e.g. sandboxed iframe) rejected on state-changing endpoint
        assert api.post("/api/auth/logout", headers={"Origin": "null"}).status_code == 403

        # Untrusted Referer without Origin rejected
        assert api.post("/api/auth/logout", headers={"Referer": "https://evil.example/form.html"}).status_code == 403

        # Cross-site Sec-Fetch-Site without Origin/Referer rejected
        assert api.post("/api/auth/logout", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403

        # Form-encoded POST rejected both by CSRF when cross-origin and by JSON schema when missing Origin
        r_form_evil = api.post(
            "/api/auth/login",
            data={"email": "csrf.user@axo.edu.vn", "password": TEST_PASSWORD},
            headers={"Origin": "https://evil.example"},
        )
        assert r_form_evil.status_code == 403
        r_form_no_orig = api.post(
            "/api/auth/login",
            data={"email": "csrf.user@axo.edu.vn", "password": TEST_PASSWORD},
        )
        assert r_form_no_orig.status_code == 422

        # Trusted same-site cross-origin https://hoclieu.tech allowed on preflight & bodyless logout
        r_preflight = api.options(
            "/api/auth/logout",
            headers={"Origin": "https://hoclieu.tech", "Access-Control-Request-Method": "POST"},
        )
        assert r_preflight.status_code == 200
        assert r_preflight.headers.get("access-control-allow-origin") == "https://hoclieu.tech"

        r_ok_logout = api.post(
            "/api/auth/logout",
            headers={"Origin": "https://hoclieu.tech", "Sec-Fetch-Site": "same-site"},
        )
        assert r_ok_logout.status_code == 200
        assert r_ok_logout.headers.get("access-control-allow-origin") == "https://hoclieu.tech"
        assert api.get("/api/auth/me").json()["user"] is None

    def test_csrf_guard_wildcard_cors_env_never_whitelists_evil_origin(self, api, monkeypatch):
        monkeypatch.setenv("CORS_ALLOW_ORIGINS", "*")
        r = api.post("/api/auth/logout", headers={"Origin": "https://evil.example"})
        assert r.status_code == 403

    def test_rate_limiter_rightmost_xff_anti_spoofing_and_concurrent_bucket_eviction(self, monkeypatch):
        from concurrent.futures import ThreadPoolExecutor

        monkeypatch.setenv("TRUST_PROXY_HEADERS", "1")
        monkeypatch.setenv("UVICORN_FORWARDED_ALLOW_IPS", "127.0.0.1")
        monkeypatch.setenv("AUTH_RATE_LIMIT_MAX_ATTEMPTS", "3")
        monkeypatch.setenv("AUTH_RATE_LIMIT_IP_MAX_ATTEMPTS", "20")
        monkeypatch.setenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60")

        # Client sends fake leftmost X-Forwarded-For behind trusted proxy appending real IP 198.51.100.88
        for idx in range(3):
            req = _fake_request(
                client_host="127.0.0.1",
                headers={"X-Forwarded-For": f"10.0.0.{idx + 1}, 198.51.100.88"},
            )
            accounts_router._consume_auth_rate_limit("login", req, "spoof-target@axo.edu.vn")

        spoofed_next = _fake_request(
            client_host="127.0.0.1",
            headers={"X-Forwarded-For": "10.0.0.99, 198.51.100.88"},
        )
        with pytest.raises(accounts_router.HTTPException) as exc_info:
            accounts_router._consume_auth_rate_limit("login", spoofed_next, "spoof-target@axo.edu.vn")
        assert exc_info.value.status_code == 429

        # Concurrency & bounded bucket eviction preserve active attacker counter
        monkeypatch.setattr(accounts_router, "_AUTH_RATE_MAX_BUCKETS", 12)
        with ThreadPoolExecutor(max_workers=6) as pool:
            list(
                pool.map(
                    lambda i: accounts_router._consume_auth_rate_limit(
                        "login",
                        _fake_request(client_host="127.0.0.1", headers={"X-Forwarded-For": f"198.51.100.{100 + i}"}),
                        f"burst{i}@axo.edu.vn",
                    ),
                    range(25),
                )
            )
        assert len(accounts_router._AUTH_RATE_BUCKETS) <= 12

