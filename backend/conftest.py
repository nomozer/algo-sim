# -*- coding: utf-8 -*-
"""Cấu hình pytest (M7.14T) — OFFLINE-FIRST.

Ba việc:
1. Giúp pytest import được package `app` khi chạy từ thư mục backend/.
2. HARD GUARD: pytest mặc định KHÔNG BAO GIỜ gọi Gemini thật.
3. MỖI LƯỢT PYTEST MỘT DATABASE RIÊNG (xem `duong_dan_db_test`).

Vì sao guard đặt Ở ĐÂY chứ không trong app/ai/gemini.py:
- Biên mạng thật là `httpx.AsyncClient.post` — chỉ gemini.py dùng httpx.
  Patch đúng biên đó thì test nào QUÊN MOCK sẽ chết TRƯỚC khi ra mạng.
- tests/test_gemini.py có quyền chính đáng gọi call_gemini với transport GIẢ
  (nó thay hẳn gemini.httpx.AsyncClient) — guard ở biên thật không đụng tới nó.
- Production code không phải mang logic test.

Hệ quả quan trọng: toàn bộ suite xanh ⇔ KHÔNG test nào chạm mạng (nếu có, nó
đã raise). Đây chính là bằng chứng cho "pytest = 0 real API call".

Thoát guard: chỉ khi ALLOW_LIVE_AI=1 (dùng cho live eval, không dùng trong CI).
"""

import os
import socket
import sys
import tempfile
from pathlib import Path

import httpx
import pytest


def duong_dan_db_test(pid: int | None = None) -> str:
    """URL SQLite RIÊNG cho MỘT lượt pytest, đặt tên theo PID.

    ─── VÌ SAO, ĐO ĐƯỢC 2026-08-25 ──────────────────────────────────────────

    Một lượt `pytest` full treo quá 600 giây trong khi lượt ngay trước đó mất
    27 giây. Không test nào chậm: có BỐN tiến trình pytest cùng chạy (hai phiên
    làm việc song song) và cả bốn tranh nhau đúng một file `backend/algosim.db`.
    CPU gần bằng không — chúng nằm chờ khoá SQLite.

    Cái đắt là HÌNH DẠNG của lỗi: nó trông y hệt một test treo, nên người ta đi
    tìm test có lỗi, không nghĩ tới tiến trình bên cạnh. Không thông báo, không
    timeout, không gì trỏ sang thủ phạm.

    File dùng chung còn đẻ lớp lỗi thứ hai đã cắn kho này: trạng thái RÒ RỈ giữa
    các lượt. `test_api.py` ghi lại một lỗi câm suốt nhiều lần bump
    `CACHE_VERSION` vì *"test luôn chạy trên DB sạch"*, chỉ lộ ở bump 36→37 khi
    DB test còn hàng của lượt trước.

    Đặt ở đây chứ không ở từng fixture: `app/persistence/db.py` đọc
    `DATABASE_URL` **lúc import module**, mà `conftest.py` được pytest nạp trước
    mọi file test — nên đây là chỗ duy nhất còn kịp. `conftest_classroom.py` giải
    quyết nửa khác của bài toán (đổi chỗ `SessionLocal` cho từng test cần DB
    trống); hai thứ không thay nhau được.
    """
    pid = os.getpid() if pid is None else pid
    return f"sqlite:///{Path(tempfile.gettempdir()) / f'algosim-test-{pid}.db'}"


# `setdefault`, KHÔNG gán đè: lượt chỉ định DATABASE_URL tường minh (smoke
# Postgres, CI trỏ DB khác) phải thắng. Test `-m postgres` truyền URL cho tiến
# trình con nên không đi qua đây.
os.environ.setdefault("DATABASE_URL", duong_dan_db_test())


def pytest_sessionfinish(session, exitstatus):
    """Dọn file DB của lượt này — thư mục tạm không phải chỗ để rác tích lại."""
    duong_dan = os.environ.get("DATABASE_URL", "")
    if duong_dan != duong_dan_db_test():
        return  # DB do người khác chỉ định — không phải của ta, không đụng
    try:
        Path(duong_dan.removeprefix("sqlite:///")).unlink(missing_ok=True)
    except OSError:
        pass  # Windows còn giữ handle là chuyện thường; rác trong temp vô hại


# Fix WinError 10013 on Windows ephemeral port bind in asyncio self-pipe
if sys.platform == "win32":
    _orig_socketpair = getattr(socket, "socketpair", None)
    def _windows_fixed_socketpair(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0):
        for port in range(49152, 49999):
            lsock = socket.socket(family, type, proto)
            lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                lsock.bind(("127.0.0.1", port))
                lsock.listen(1)
                csock = socket.socket(family, type, proto)
                csock.connect(("127.0.0.1", port))
                ssock, _ = lsock.accept()
                lsock.close()
                return ssock, csock
            except OSError:
                lsock.close()
                continue
        if _orig_socketpair:
            return _orig_socketpair(family, type, proto)
        raise OSError("No available port found for socketpair")
    socket.socketpair = _windows_fixed_socketpair

BLOCK_MESSAGE = "Real Gemini API call blocked during offline tests."


def live_allowed() -> bool:
    return os.getenv("ALLOW_LIVE_AI") == "1"


@pytest.fixture(autouse=True)
def block_real_network(monkeypatch):
    """Chặn MỌI HTTP POST thật qua httpx + gỡ key thật khỏi môi trường.

    Lớp 2 (gỡ key): backend/.env được load_dotenv nạp lúc import db.py, nên
    GEMINI_API_KEY THẬT nằm trong os.environ suốt phiên pytest. Test nào cần
    key giả vẫn tự monkeypatch.setenv (chạy sau fixture này).
    """
    if live_allowed():
        return

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # Chặn ở TRANSPORT MẠNG THẬT, không phải ở client: TestClient của FastAPI
    # dùng ASGITransport (in-process, không ra mạng) nên vẫn chạy bình thường.
    async def blocked_async(self, *args, **kwargs):
        raise RuntimeError(BLOCK_MESSAGE)

    def blocked_sync(self, *args, **kwargs):
        raise RuntimeError(BLOCK_MESSAGE)

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", blocked_async)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked_sync)

# ── W8 §17/§18 — CHI PHÍ KDF TRONG TEST ─────────────────────────────────────
#
# ĐO ĐƯỢC ở HEAD b7ca150: `pytest` đầy đủ mất 57s, trong đó
# `test_classroom_api.py` 27,9s + `test_auth_api.py` 10,3s + `test_guest_trial.py`
# 2,0s = **40s/50s**. Không phải vài test chậm — là 365ms mỗi lần băm mật khẩu
# (PBKDF2 600.000 vòng theo khuyến nghị OWASP) nhân với mỗi lượt đăng ký/đăng
# nhập trong fixture.
#
# 600.000 vòng là ĐÚNG cho production và KHÔNG đổi. Trong test nó là
# EXPENSIVE_FIXTURE: thứ các test ấy chứng minh là CƠ CHẾ (salt riêng, KDF có
# tham số, không lưu thô, phiên hết hạn, phân quyền), không phải độ chậm.
#
# An toàn vì số vòng được ghi vào chính chuỗi lưu và `verify_password` đọc lại
# từ đó — hash sinh ở số vòng nào cũng verify được, kể cả hash production cũ.
#
# Mức production được khoá RIÊNG bởi `tests/test_kdf_cost.py`, và test đó KHÔNG
# đi qua fixture này.


@pytest.fixture(autouse=True)
def cheap_kdf(monkeypatch, request):
    """Hạ số vòng PBKDF2 cho mọi test, TRỪ test khoá mức production."""
    if request.node.get_closest_marker("real_kdf_cost"):
        return
    from app.accounts import passwords

    monkeypatch.setattr(passwords, "DEFAULT_ITERATIONS", 1_000)
