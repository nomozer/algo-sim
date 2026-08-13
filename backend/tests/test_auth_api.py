# -*- coding: utf-8 -*-
"""M18 — DANH TÍNH VÀ QUYỀN DO MÁY CHỦ SỞ HỮU.

Đây là file khoá những thứ mà một lỗi ở đó không hiện ra trên màn hình: mật
khẩu rò ra response, client tự nâng vai trò, lượt dùng thử đếm ở sai chỗ.

Mọi bài trong file này chạy hoàn toàn offline (guard mạng của `conftest.py` vẫn
áp dụng) và trên một database trống của riêng nó.
"""

from __future__ import annotations

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
    can_observe_class,
    can_read_class,
    entitlement_for,
    resolve_signup_role,
)
from tests.conftest_classroom import TEST_PASSWORD, api, login, new_client, register  # noqa: F401


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
    def test_khach_co_dung_mot_luot_va_khong_co_lop(self):
        e = entitlement_for(None, guest_trials_used=0)
        assert e.can_run_simulation and e.trials_left == GUEST_TRIAL_LIMIT
        assert not e.can_join_class and not e.can_own_class
        assert not e.can_receive_assignment and not e.can_persist_history

    def test_khach_dung_het_luot_thi_khong_chay_duoc_nua(self):
        e = entitlement_for(None, guest_trials_used=GUEST_TRIAL_LIMIT)
        assert not e.can_run_simulation and e.trials_left == 0

    def test_hoc_sinh_vao_lop_duoc_nhung_khong_so_huu_lop(self):
        e = entitlement_for(Role.STUDENT)
        assert e.can_join_class and not e.can_own_class and e.can_receive_assignment

    def test_giao_vien_so_huu_lop_nhung_khong_nhan_bai(self):
        e = entitlement_for(Role.TEACHER)
        assert e.can_own_class and not e.can_join_class and not e.can_receive_assignment

    def test_giao_vien_KHAC_khong_quan_sat_duoc_lop_khong_phai_cua_minh(self):
        """§36.3 — 'là giáo viên' không đủ; phải là giáo viên CỦA LỚP ĐÓ."""
        assert can_observe_class(viewer_role=Role.TEACHER, viewer_id=7, class_teacher_id=7)
        assert not can_observe_class(viewer_role=Role.TEACHER, viewer_id=8, class_teacher_id=7)

    def test_hoc_sinh_khong_bao_gio_quan_sat_duoc_lop(self):
        assert not can_observe_class(viewer_role=Role.STUDENT, viewer_id=7, class_teacher_id=7)
        assert not can_observe_class(viewer_role=None, viewer_id=None, class_teacher_id=7)

    def test_hoc_sinh_doc_duoc_lop_MINH_DA_VAO_va_chi_lop_do(self):
        assert can_read_class(viewer_role=Role.STUDENT, viewer_id=3,
                              class_teacher_id=1, member_ids=frozenset({3, 4}))
        assert not can_read_class(viewer_role=Role.STUDENT, viewer_id=9,
                                  class_teacher_id=1, member_ids=frozenset({3, 4}))


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
                       json={"currentPassword": "sai-mat-khau-dai", "newPassword": "moi-dai-12345"})
        assert bad.status_code == 400
        ok = api.post("/api/auth/password",
                      json={"currentPassword": TEST_PASSWORD, "newPassword": "moi-dai-12345"})
        assert ok.status_code == 200
        api.post("/api/auth/logout")
        assert login(api, email="an@lop.test", password="moi-dai-12345").status_code == 200

    def test_khach_chua_dang_nhap_van_goi_duoc_me(self, api):
        r = api.get("/api/auth/me")
        assert r.status_code == 200
        assert r.json()["user"] is None
        assert r.json()["entitlement"]["trialsLeft"] == GUEST_TRIAL_LIMIT
