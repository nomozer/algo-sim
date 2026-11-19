"""A keep-alive socket that llama-server closed while idle is a stale connection, not a crashed server.

Live acceptance (run axo-hybrid-local-only-3d-simulation-live-acceptance-cutover) reproduced it on Windows: after an idle
gap longer than the server keep-alive (~5 s) the reused socket fails with WinError 10053; the runtime reported
LOCAL_SLM_PROCESS_CRASHED (HTTP 503) and stopped a healthy server, so every other request after a pause failed.
"""

import http.client

import pytest

from app.ai import local_slm_runtime as rt


class _Resp:
    status = 200
    will_close = False

    def read(self):
        return b'{"ok": true}'


class _Conn:
    """Fresh loopback connection that answers normally."""

    made = 0

    def __init__(self, *_a, **_k):
        type(self).made += 1
        self.sock = None
        self.timeout = None

    def request(self, *_a, **_k):
        pass

    def getresponse(self):
        return _Resp()

    def close(self):
        pass


class _StaleConn(_Conn):
    def __init__(self, exc):
        super().__init__()
        self.exc = exc

    def request(self, *_a, **_k):
        raise self.exc


class _AliveProc:
    def poll(self):
        return None


@pytest.mark.parametrize("exc", [
    ConnectionAbortedError(10053, "An established connection was aborted by the software in your host machine"),
    ConnectionResetError(10054, "An existing connection was forcibly closed by the remote host"),
    BrokenPipeError(32, "Broken pipe"),
    http.client.RemoteDisconnected("Remote end closed connection without response"),
])
def test_stale_keepalive_socket_reconnects_instead_of_reporting_a_crash(monkeypatch, exc):
    r = rt.LocalSlmRuntime()
    r._proc = _AliveProc()
    r._http_conn, r._http_port = _StaleConn(exc), 4242
    _Conn.made = 0
    monkeypatch.setattr(rt.http.client, "HTTPConnection", _Conn)
    status, body = r._post_completion_keepalive(4242, b"{}", 5.0)
    assert (status, body) == (200, b'{"ok": true}')
    assert _Conn.made == 1          # exactly one fresh reconnect


def test_a_fresh_connection_failure_is_still_raised(monkeypatch):
    """No reused socket ⇒ nothing stale to blame: the error propagates (the caller then reports the crash)."""

    class _Refused(_Conn):
        def request(self, *_a, **_k):
            raise ConnectionRefusedError(10061, "refused")

    r = rt.LocalSlmRuntime()
    r._proc = _AliveProc()
    monkeypatch.setattr(rt.http.client, "HTTPConnection", _Refused)
    with pytest.raises(ConnectionRefusedError):
        r._post_completion_keepalive(4242, b"{}", 5.0)
