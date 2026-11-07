"""Runs at startup of every Python CHILD of an offline pytest session (this folder is put on `PYTHONPATH` by
`backend/conftest.py`; `site` imports `sitecustomize` automatically). Test-only: no product code, no runtime flag.

1. `GEMINI_API_KEY` is set to empty BEFORE anything can import `app.persistence.db`: `load_dotenv` never overrides an
   existing variable, so the child cannot pick the real key back up from `backend/.env` — whatever env the parent built
   (inherited, `{**os.environ}`, or filtered of `GEMINI*`). A key a test sets on purpose (a fake one) is kept.
2. The loopback-only socket guard (`offline_socket_guard`), and the same httpx transport block as conftest.
"""
import os

os.environ.setdefault("GEMINI_API_KEY", "")

from offline_socket_guard import BLOCK_MESSAGE, install  # noqa: E402

install()

try:
    import httpx  # noqa: E402
except ImportError:  # a child without httpx cannot use it either
    httpx = None

if httpx is not None:
    def _refuse(*_a, **_k):
        raise RuntimeError(BLOCK_MESSAGE)

    async def _refuse_async(*_a, **_k):
        raise RuntimeError(BLOCK_MESSAGE)

    httpx.HTTPTransport.handle_request = _refuse
    httpx.AsyncHTTPTransport.handle_async_request = _refuse_async
