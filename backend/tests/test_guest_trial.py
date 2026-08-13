# -*- coding: utf-8 -*-
"""M18 — LƯỢT DÙNG THỬ CỦA KHÁCH DO MÁY CHỦ ĐẾM.

§37 nói thẳng cái phải chặn: "khách có lượt vô hạn chỉ bằng cách xoá state phía
client". Đó chính xác là điều xảy ra nếu cờ nằm ở localStorage — nên nó nằm ở
`auth_sessions.guest_trials_used`, và bài kiểm dưới đây mô phỏng đúng thao tác
xoá sạch trình duyệt để chứng minh nó không đủ.

Suite chạy offline: `/api/analyze` bị chặn ở cổng lượt thử TRƯỚC khi chạm tới
ingestion hay LLM, nên không bài nào ở đây cần mạng.
"""

from __future__ import annotations

import pytest

from app.accounts.policy import GUEST_TRIAL_LIMIT
from tests.conftest_classroom import TEST_PASSWORD, api, new_client, register  # noqa: F401

BODY = {"input": {"type": "text", "content": "Mô phỏng cổng AND với hai đầu vào."}}


def analyze(client):
    return client.post("/api/analyze", json=BODY)


class TestLuotDungThu:
    def test_khach_moi_mo_trang_co_dung_mot_luot(self, api):
        me = api.get("/api/auth/me").json()
        assert me["user"] is None
        assert me["entitlement"]["trialsLeft"] == GUEST_TRIAL_LIMIT
        assert me["entitlement"]["canRunSimulation"] is True

    def test_khach_KHONG_co_quyen_lop_hoc(self, api):
        ent = api.get("/api/auth/me").json()["entitlement"]
        assert ent["canJoinClass"] is False
        assert ent["canOwnClass"] is False
        assert ent["canReceiveAssignment"] is False
        assert ent["canPersistHistory"] is False

    def test_de_bi_TU_CHOI_khong_an_mat_luot_duy_nhat(self, api):
        """Lượt chỉ tính khi RA ĐƯỢC mô phỏng.

        Ở đây không có GEMINI_API_KEY (guard offline gỡ nó), nên analyze trả
        503 — tức chưa có mô phỏng nào. Lượt phải còn nguyên, nếu không một đề
        hỏng vì lỗi máy chủ lại tiêu mất cơ hội duy nhất của người dùng.
        """
        r = analyze(api)
        assert r.status_code == 503
        assert api.get("/api/auth/me").json()["entitlement"]["trialsLeft"] == GUEST_TRIAL_LIMIT

    def test_het_luot_thi_analyze_BI_CHAN_truoc_khi_cham_pipeline(self, api, monkeypatch):
        """Tiêu hết lượt bằng đúng đường mà một lượt thành công đi qua."""
        _use_up_trial(api)
        r = analyze(api)
        assert r.status_code == 402
        assert r.json()["reason_code"] == "guest_trial_exhausted"

    def test_XOA_STATE_PHIA_CLIENT_van_khong_co_them_luot(self, api):
        """§37.1 — bài kiểm trung tâm của file này.

        Mô phỏng đúng thao tác mà một cờ localStorage không chống nổi: client
        vứt sạch state của CHÍNH NÓ rồi hỏi lại máy chủ. Cổng vẫn đóng, vì con
        số nằm ở `auth_sessions.guest_trials_used` chứ không ở trình duyệt.

        Cái này KHÔNG chứng minh "không thể có lượt thứ hai" — xoá cookie thì
        được một phiên mới, và đó là giới hạn cố hữu của phiên ẩn danh, khai ở
        `test_dang_xuat_KHONG_tra_lai_luot_cho_khach` bên dưới. Nó chứng minh
        đúng điều §37.1 đòi: chính sách KHÔNG sống ở client.
        """
        _use_up_trial(api)
        assert analyze(api).status_code == 402
        # "Xoá state phía client" — giữ đúng cookie phiên, bỏ mọi thứ khác.
        token = api.cookies.get("algosim_session")
        api.cookies.clear()
        api.cookies.set("algosim_session", token)
        assert analyze(api).status_code == 402
        assert api.get("/api/auth/me").json()["entitlement"]["trialsLeft"] == 0

    def test_dang_nhap_thi_HET_gioi_han_va_KHONG_mat_phien_cu(self, api):
        """§5 — chuyển sang tài khoản không được vứt bỏ phiên đang có."""
        _use_up_trial(api)
        assert analyze(api).status_code == 402
        register(api, email="an@lop.test", name="An")
        me = api.get("/api/auth/me").json()
        assert me["user"]["role"] == "student"
        assert me["entitlement"]["trialsLeft"] is None  # không còn giới hạn khách
        # Không còn bị cổng 402 chặn (503 = thiếu key, tức đã đi qua cổng).
        assert analyze(api).status_code == 503

    def test_dang_xuat_KHONG_tra_lai_luot_cho_khach(self, api):
        """Nếu đăng xuất cấp lại lượt thì 'một lượt' chỉ là gợi ý."""
        _use_up_trial(api)
        register(api, email="an@lop.test", name="An")
        api.post("/api/auth/logout")
        # Phiên cũ đã bị xoá; client nhận phiên KHÁCH mới ⇒ có lượt mới.
        # Đây là GIỚI HẠN ĐÃ BIẾT, khai ở CLASSROOM_AUTH_CONTRACT §Giới hạn:
        # chống được việc xoá localStorage, KHÔNG chống được người cố tình xoá
        # cookie. Bài kiểm này khoá HÀNH VI ĐÓ lại để nó không âm thầm đổi.
        me = api.get("/api/auth/me").json()
        assert me["user"] is None
        assert me["entitlement"]["trialsLeft"] == GUEST_TRIAL_LIMIT


def _use_up_trial(client):
    """Tiêu một lượt qua ĐÚNG đường máy chủ dùng, không sửa DB tay."""
    import app.main as main_mod

    client.get("/api/auth/me")  # đảm bảo có phiên
    token = client.cookies.get("algosim_session")
    assert token, "chưa cấp cookie phiên"
    with main_mod.SessionLocal() as session:
        main_mod._consume_guest_trial(session, token)
        session.commit()
