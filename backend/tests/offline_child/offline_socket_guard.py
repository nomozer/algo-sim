"""Offline boundary BELOW every HTTP client: a socket may connect only to loopback (run `gemini-credential-transport`).

Why a second layer under the httpx transport block of `backend/conftest.py`: an offline reliability tool once removed
`GEMINI_API_KEY`, then imported `app` — `app/persistence/db.py` ran `load_dotenv` and put the REAL key back — and a
path that ignored `ALLOW_LIVE_AI=0` reached the real provider. Deleting a variable is not a boundary. This module is the
single source used by the pytest process (conftest) and by every Python child a test spawns (`sitecustomize.py` here,
put on `PYTHONPATH` by conftest).

Allowed: AF_UNIX / non-IP families, `localhost`, loopback IPs (Postgres on 127.0.0.1, asyncio's socketpair, local
servers). Refused before any packet: every other IP and every other hostname. Limitation: on Windows the asyncio
Proactor loop connects with `ConnectEx`, not `socket.connect`; async HTTP stays covered by conftest's httpx block.
"""
from __future__ import annotations

import ipaddress
import socket

BLOCK_MESSAGE = (
    "OFFLINE TEST: kết nối mạng ra ngoài loopback bị chặn ở tầng socket. Test offline không được chạm mạng — "
    "dùng transport/provider giả; lượt live chỉ chạy ở lối riêng ALLOW_LIVE_AI=1 có phê duyệt."
)


class OfflineNetworkBlocked(RuntimeError):
    """Not an OSError on purpose: HTTP clients must not read it as a transient network error and retry around it."""


def _allowed(sock: socket.socket, address) -> bool:
    if sock.family not in (socket.AF_INET, socket.AF_INET6):
        return True
    host = address[0] if isinstance(address, tuple) else address
    if not isinstance(host, str):
        return False
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.split("%", 1)[0]).is_loopback
    except ValueError:
        return False                     # any other hostname would resolve outward


def install() -> None:
    """Idempotent: patch `socket.socket.connect` / `connect_ex` once per process."""
    if getattr(socket.socket.connect, "_offline_guard", False):
        return
    orig_connect, orig_connect_ex = socket.socket.connect, socket.socket.connect_ex

    def connect(self, address):
        if not _allowed(self, address):
            raise OfflineNetworkBlocked(BLOCK_MESSAGE)
        return orig_connect(self, address)

    def connect_ex(self, address):
        if not _allowed(self, address):
            raise OfflineNetworkBlocked(BLOCK_MESSAGE)
        return orig_connect_ex(self, address)

    connect._offline_guard = connect_ex._offline_guard = True
    socket.socket.connect, socket.socket.connect_ex = connect, connect_ex
