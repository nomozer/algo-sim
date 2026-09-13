# -*- coding: utf-8 -*-
"""NGHIỆM THU PROVIDER THẬT cho đường ẢNH ĐỀ BÀI → MÔ PHỎNG — từng ca, trần HTTP cứng.

`PHOTO_PROBLEM_LIVE_RUNNER_HARDENING` (2026-09-14). **TIÊU QUOTA THẬT** khi chạy
không có `--dry-run`. Thay bản của `PHOTO_PROBLEM_TO_SCENE_END_TO_END`, vốn chạy
liền ba ca tổng hợp ghi cứng trong mã, chỉ có trần LOGIC 11 (không trần HTTP —
trường hợp xấu nhất 3×2 + 8×4 = 38 request), không dừng khi ca trước hỏng, và đo
văn bản bằng `difflib.SequenceMatcher` chứ không phải CER.

─── CÁCH DÙNG ─────────────────────────────────────────────────────────────

    cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
      scripts/run_photo_problem_live.py --case C01 \
      --input-dir D:/anh-de --ground-truth D:/anh-de/GROUND_TRUTH.json \
      --output-dir D:/ket-qua/C01-lan-1

`--case all` chạy C01 → C02 → C03 và DỪNG ở ca đầu tiên không đạt. Không có
`--case` thì in hướng dẫn và thoát — không bao giờ tự chạy cả ba.

─── BA RANH GIỚI ───────────────────────────────────────────────────────────

① TRẦN HTTP ĐẶT Ở TRANSPORT. `CongHttp` là transport `httpx` bọc NGOÀI transport
  mạng. `call_gemini` dựng `httpx.AsyncClient` mới mỗi lượt gọi và đọc tên
  `httpx.AsyncClient` ngay lúc gọi, nên runner chèn cổng mà không đổi một dòng
  mã sản phẩm. Cổng được gọi SAU khi request đã dựng, TRƯỚC transport mạng, đúng
  một lần cho mỗi lần thử HTTP: xác định ca + tầng (`telemetry.current_stage`) →
  kiểm ngân sách → tăng bộ đếm → ghi metadata đã khử secret. Request vượt trần
  NÉM trước khi transport bên trong được chạm.

② MỘT LẦN THỬ MỖI LƯỢT GỌI LOGIC. Ép bằng cơ chế sản phẩm có sẵn:
  `ApiBudget(max_attempts=1)` ⇒ vision `min(1, VISION_MAX_ATTEMPTS)` = 1, đọc đề
  và tổng hợp = 1 (`gemini.py:212–214`). Không tin bằng lời: trước mỗi lượt
  chạy, runner gọi ĐÚNG ba hàm sản phẩm trên một transport giả luôn trả 503 và
  đếm request mỗi tầng. Khác 1/1/1 ⇒ `RETRY_POLICY_NOT_ENFORCEABLE`, thoát trước
  mọi request thật. Ngoài ra cổng tự CHẶN mọi request sau lỗi provider đầu tiên.

③ KHÔNG LỘ SECRET. Mọi chuỗi ra console và mọi JSON đi qua `BoKhuBiMat`: giá trị
  khoá thật, tham số `?key=` trong URL, và các đầu mục `Authorization`,
  `x-goog-api-key`, `Cookie`, `Set-Cookie`, `access_token`, `refresh_token`.
  Metadata request chỉ ghi scheme + host + path, không bao giờ ghi query.

Ngân sách `MAX_HTTP_REQUESTS = 11` là tổng của trường hợp xấu nhất KHI một lần
thử: C01 ≤ 1 vision + 1 analyze + 3 synthesis (vòng sửa `MAX_SEMANTIC_PROGRAM_
ATTEMPTS`) = 5 · C02 ≤ 5 · C03 = 1 vision (runner không bao giờ gọi tầng B cho
C03) ⇒ 11.

Ảnh nguồn KHÔNG bị sao chép. Artifact chỉ mang băm, kích thước, MIME, EXIF.
`--include-sanitized-images` + `--confirm-no-personal-data` mới cho ghi bản JPEG
đã gỡ metadata.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import io
import json
import logging
import os
import re
import socket
import sys
import time
import traceback
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

BE = Path(__file__).resolve().parents[1]
for _p in (str(BE), str(BE / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import httpx  # noqa: E402
from PIL import Image  # noqa: E402

from app.ai import gemini, pipeline  # noqa: E402
from app.ai.telemetry import current_stage  # noqa: E402
from app.ingestion import image_extraction as ie  # noqa: E402
from app.ingestion.image import ImageRejected, NormalizedImage, normalize_image, sniff_image_mime  # noqa: E402
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC  # noqa: E402

WAVE = "PHOTO_PROBLEM_LIVE_RUNNER_HARDENING"
CASE_IDS = ("C01", "C02", "C03")
STAGES = ("vision", "analyze", "synthesis")
#: Nhãn `telemetry.current_stage()` mà mã sản phẩm tự khai → tầng của runner.
STAGE_THEO_TELEMETRY = {
    "transcribe": "vision",
    "semantic_analyze": "analyze",
    "semantic_program": "synthesis",
}

MAX_HTTP_REQUESTS = 11
MAX_ATTEMPTS_PER_LOGICAL_CALL = 1
#: Ngưỡng CER đăng ký TRƯỚC — không đọc từ ground truth để không ai chỉnh sau khi thấy số.
NGUONG_CER = {"C01": 0.02, "C02": 0.05}
DUOI_ANH = (".jpg", ".jpeg", ".png", ".webp")

EXIT_PASS, EXIT_CASE_FAIL, EXIT_USAGE, EXIT_NO_KEY, EXIT_RETRY_POLICY = 0, 1, 2, 3, 4

NHAN_KHAI_TRUOC = {
    "MEASUREMENT_CLASS": "INTERNAL_ONE_SHOT_ACCEPTANCE",
    "HELD_OUT_CLAIM": "NO",
    "EVALUATOR_INDEPENDENCE": "OPERATOR_IS_DEVELOPER",
    "MAX_ATTEMPTS_PER_LOGICAL_CALL": MAX_ATTEMPTS_PER_LOGICAL_CALL,
    "HTTP_BUDGET_COMPOSITION": "C01 ≤ 1 vision + 1 analyze + 3 synthesis = 5 · C02 ≤ 5 · C03 = 1 vision ⇒ 11",
}

HUONG_DAN = """\
Thiếu --case. Runner KHÔNG tự chạy cả ba ca.

  --case C01|C02|C03|all        all = C01 → C02 → C03, dừng ở ca đầu tiên không đạt
  --input-dir <tuyệt đối>       thư mục chứa C01.jpg/.png/.webp … (hoặc `image_file` trong ground truth)
  --ground-truth <tuyệt đối>    JSON đăng ký TRƯỚC khi gọi model
  --output-dir <tuyệt đối>      thư mục MỚI hoặc rỗng
  --max-http-requests N         1…11, mặc định 11
  --dry-run                     provider giả ở ranh giới HTTP, 0 request mạng

Chạy thật cần ALLOW_LIVE_AI=1 và GEMINI_API_KEY trong môi trường."""


# ══════════════════════════════════════════════════════════════════════════
# §1 · KHỬ SECRET
# ══════════════════════════════════════════════════════════════════════════
REDACTED = "[REDACTED]"
#: Tên đầu mục/trường bí mật. `set-cookie` đứng TRƯỚC `cookie` trong phép hoặc.
TEN_BI_MAT = (
    "gemini_api_key",
    "authorization",
    "x-goog-api-key",
    "set-cookie",
    "cookie",
    "access_token",
    "refresh_token",
)
_MAU_DAU_MUC = re.compile(
    r"(?i)\b(" + "|".join(re.escape(t) for t in TEN_BI_MAT) + r")"
    r"(\"?\s*[:=]\s*\"?)(?:bearer\s+)?[^\s,;\"'&}\]]+"
)
_MAU_QUERY = re.compile(r"(?i)([?&](?:key|access_token|refresh_token)=)[^&\s\"'<>]+")


class BoKhuBiMat:
    """Khử secret khỏi chuỗi và cấu trúc JSON. Không bao giờ giả định "hiện không có khoá"."""

    def __init__(self, gia_tri: tuple[str, ...] = ()) -> None:
        self.gia_tri = tuple(sorted(
            {v for v in gia_tri if isinstance(v, str) and len(v) >= 6}, key=len, reverse=True))

    def chuoi(self, s: str) -> str:
        for v in self.gia_tri:
            s = s.replace(v, REDACTED)
        s = _MAU_QUERY.sub(lambda m: m.group(1) + REDACTED, s)
        return _MAU_DAU_MUC.sub(lambda m: m.group(1) + m.group(2) + REDACTED, s)

    def __call__(self, obj: Any) -> Any:
        if isinstance(obj, str):
            return self.chuoi(obj)
        if isinstance(obj, dict):
            return {k: (REDACTED if str(k).lower() in TEN_BI_MAT else self(v)) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self(v) for v in obj]
        return obj


class KenhIn:
    def __init__(self, khu: BoKhuBiMat, out=None, err=None) -> None:
        self.khu, self.out, self.err = khu, out, err

    def in_(self, s: str = "") -> None:
        print(self.khu(str(s)), file=self.out or sys.stdout)

    def loi(self, s: str) -> None:
        print(self.khu(str(s)), file=self.err or sys.stderr)


def _ghi_json(thu_muc: Path, ten: str, obj: Any, khu: BoKhuBiMat) -> Path:
    p = thu_muc / ten
    if p.exists():
        raise FileExistsError(f"không ghi đè {p.name}")
    p.write_text(json.dumps(khu(obj), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return p


def _chuoi_loi(err: BaseException) -> str:
    """Lỗi kèm chuỗi nguyên nhân — chính chỗ thân phản hồi provider có thể chở secret."""
    phan, e, n = [], err, 0
    while e is not None and n < 4:
        phan.append(f"{type(e).__name__}: {e}")
        e, n = e.__cause__, n + 1
    return " ← ".join(phan)


def _bay_gio() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8") if isinstance(b, str) else b).hexdigest()


# ══════════════════════════════════════════════════════════════════════════
# §2 · CỔNG HTTP — ranh giới gửi provider
# ══════════════════════════════════════════════════════════════════════════
class HttpBudgetExceeded(gemini.BudgetExceeded):
    """Request bị chặn TRƯỚC transport.

    Kế thừa `BudgetExceeded` có chủ đích: `image_extraction._goi_provider` nuốt mọi
    lỗi provider thành `VisionUnavailable` NGOẠI TRỪ `BudgetExceeded` — nên lời chặn
    đi thẳng lên runner với đúng tên của nó.
    """


class CongHttp(httpx.AsyncBaseTransport):
    """Đếm, chặn và ghi metadata cho MỖI lần thử HTTP tới provider."""

    def __init__(self, inner: httpx.AsyncBaseTransport | None, max_http_requests: int,
                 khu: BoKhuBiMat, *, dung_sau_loi: bool = True) -> None:
        if max_http_requests < 1:
            raise ValueError("max_http_requests phải ≥ 1")
        self.inner = inner
        self.max_http_requests = max_http_requests
        self.khu = khu
        self.dung_sau_loi = dung_sau_loi
        self.case_id: str | None = None
        self.sent = 0
        self.blocked = 0
        self.sent_by_stage = dict.fromkeys(STAGES, 0)
        self.blocked_by_stage = {**dict.fromkeys(STAGES, 0), "unknown": 0}
        self.retries_attempted = 0
        self.retries_sent = 0
        self.inner_invocations = 0
        self.records: list[dict] = []
        self.provider_error: str | None = None
        self._budget_da_thay: int | None = None
        self._retry_da_thay = 0
        #: Văn bản người dùng trong request ĐỌC ĐỀ, theo ca — CHỈ trong bộ nhớ, để
        #: kiểm tính ngang bằng của bản đã xác nhận. Không bao giờ ghi ra artifact.
        self.van_ban_analyze: dict[str, list[str]] = {}

    @property
    def attempted(self) -> int:
        return self.sent + self.blocked

    def dat_ca(self, case_id: str) -> None:
        self.case_id = case_id

    def theo_ca(self, case_id: str) -> dict:
        r = [x for x in self.records if x["case_id"] == case_id]
        return {
            "sent": sum(1 for x in r if x["sent"]),
            "blocked": sum(1 for x in r if x["blocked"]),
            **{f"{s}_sent": sum(1 for x in r if x["sent"] and x["stage"] == s) for s in STAGES},
        }

    def tong_hop(self) -> dict:
        return {
            "MAX_HTTP_REQUESTS": self.max_http_requests,
            "HTTP_REQUESTS_ATTEMPTED": self.attempted,
            "HTTP_REQUESTS_SENT": self.sent,
            "HTTP_REQUESTS_BLOCKED": self.blocked,
            "VISION_HTTP_REQUESTS": self.sent_by_stage["vision"],
            "ANALYZE_HTTP_REQUESTS": self.sent_by_stage["analyze"],
            "SYNTHESIS_HTTP_REQUESTS": self.sent_by_stage["synthesis"],
            "BLOCKED_BY_STAGE": dict(self.blocked_by_stage),
            "RETRIES": self.retries_attempted,
            "RETRIES_SENT": self.retries_sent,
            "STAGE_SUM_EQUALS_SENT": sum(self.sent_by_stage.values()) == self.sent,
            "SENT_WITHIN_BUDGET": self.sent <= self.max_http_requests,
            "PROVIDER_ERROR": self.provider_error,
        }

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        nhan_tang = current_stage()
        stage = STAGE_THEO_TELEMETRY.get(nhan_tang)
        than = request.content
        bam = _sha(than)
        # Lần thử lại do CHÍNH `call_gemini` khai — `budget.note_request(is_retry=attempt > 0)`
        # chạy ngay trước `client.post` — chứ không đoán theo thân request. Bản đầu đoán theo
        # băm thân, và `prove_photo_live_runner.py` bắt được nó đếm SAI: vòng sửa của tổng hợp
        # gửi hai thân Y HỆT nhau (cùng đầu ra hỏng, cùng lời báo lỗi) cho hai lượt gọi LOGIC.
        b = gemini.BUDGET
        la_retry = (b is not None and id(b) == self._budget_da_thay
                    and b.retry_requests > self._retry_da_thay)
        self._budget_da_thay = None if b is None else id(b)
        self._retry_da_thay = 0 if b is None else b.retry_requests
        rec: dict = {
            "provider_call_number": self.attempted + 1,
            "case_id": self.case_id,
            "stage": stage or "unknown",
            "telemetry_stage": nhan_tang,
            "method": request.method,
            "endpoint": f"{request.url.scheme}://{request.url.host}{request.url.path}",
            "body_sha256": bam,
            "retry": la_retry,
            "started_at": _bay_gio(),
        }
        if stage is None:
            ly_do = "STAGE_UNKNOWN"
        elif self.case_id is None:
            ly_do = "CASE_UNSET"
        elif self.dung_sau_loi and self.provider_error is not None:
            ly_do = "STOPPED_AFTER_PROVIDER_ERROR"
        elif self.sent >= self.max_http_requests:
            ly_do = "HTTP_BUDGET_EXHAUSTED"
        else:
            ly_do = None
        if la_retry:
            self.retries_attempted += 1
        if ly_do is not None:
            self.blocked += 1
            self.blocked_by_stage[stage or "unknown"] += 1
            rec.update(sent=False, blocked=True, block_reason=ly_do, http_status=None)
            self.records.append(rec)
            raise HttpBudgetExceeded(
                f"request #{rec['provider_call_number']} ({rec['stage']}) bị chặn trước transport: {ly_do}")

        self.sent += 1
        self.sent_by_stage[stage] += 1
        if la_retry:
            self.retries_sent += 1
        if stage == "analyze":
            try:
                tin = json.loads(than)["contents"][0]["parts"][-1]["text"]
            except (ValueError, KeyError, IndexError, TypeError):
                tin = ""
            self.van_ban_analyze.setdefault(self.case_id, []).append(tin)

        t0 = time.perf_counter()
        self.inner_invocations += 1
        try:
            res = await self.inner.handle_async_request(request)
        except Exception as err:
            loi = self.khu(f"{type(err).__name__}: {err}")
            rec.update(sent=True, blocked=False, http_status=None, error=loi,
                       latency_ms=round((time.perf_counter() - t0) * 1000, 1), finished_at=_bay_gio())
            self.provider_error = loi
            self.records.append(rec)
            raise
        rec.update(sent=True, blocked=False, http_status=res.status_code,
                   latency_ms=round((time.perf_counter() - t0) * 1000, 1), finished_at=_bay_gio())
        if not 200 <= res.status_code < 300:
            self.provider_error = f"HTTP {res.status_code}"
        self.records.append(rec)
        return res

    async def aclose(self) -> None:
        # KHÔNG đóng transport bên trong: `call_gemini` mở và đóng một client mỗi
        # lượt gọi, còn transport mạng phải sống suốt lượt chạy.
        return None


@contextmanager
def cai_cong_http(cong: CongHttp):
    """Mọi `httpx.AsyncClient` dựng trong khối này đi qua `cong`."""
    goc = httpx.AsyncClient

    def tao_client(*args, **kwargs):
        # Truyền `transport` thì `httpx` bỏ proxy của môi trường — không lối vòng nào quanh cổng.
        kwargs["transport"] = cong
        return goc(*args, **kwargs)

    gemini.httpx.AsyncClient = tao_client
    try:
        yield cong
    finally:
        gemini.httpx.AsyncClient = goc


@contextmanager
def dung_ngan_sach(budget: gemini.ApiBudget):
    cu = gemini.BUDGET
    gemini.set_budget(budget)
    try:
        yield budget
    finally:
        gemini.set_budget(cu)


def tao_ngan_sach_nghiem_thu(max_attempts: int = MAX_ATTEMPTS_PER_LOGICAL_CALL) -> gemini.ApiBudget:
    if max_attempts != 1:
        raise ValueError("RETRY_POLICY_NOT_ENFORCEABLE: nghiệm thu chỉ cho MỘT lần thử mỗi lượt gọi logic")
    return gemini.ApiBudget(max_attempts=max_attempts)


class ChanMangThat:
    """Đếm và CHẶN lối ra mạng thật: transport `httpx` thật + socket ngoài loopback."""

    def __init__(self) -> None:
        self.attempts: list[str] = []

    def __enter__(self) -> "ChanMangThat":
        self._t = httpx.AsyncHTTPTransport.handle_async_request
        self._s = socket.socket.connect
        goc_s = self._s

        async def chan_transport(_self, request):
            self.attempts.append(f"httpx:{request.url.host}")
            raise RuntimeError("NETWORK_BLOCKED")

        def chan_socket(sock, address, *a, **k):
            host = address[0] if isinstance(address, tuple) else address
            if host in ("127.0.0.1", "::1", "localhost"):
                return goc_s(sock, address, *a, **k)
            self.attempts.append(f"socket:{host}")
            raise RuntimeError("NETWORK_BLOCKED")

        httpx.AsyncHTTPTransport.handle_async_request = chan_transport
        socket.socket.connect = chan_socket
        return self

    def __exit__(self, *_e) -> None:
        httpx.AsyncHTTPTransport.handle_async_request = self._t
        socket.socket.connect = self._s


# ══════════════════════════════════════════════════════════════════════════
# §3 · CHÍNH SÁCH THỬ LẠI — đo trên ĐÚNG ba hàm sản phẩm
# ══════════════════════════════════════════════════════════════════════════
DE_THAM_DO = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2. Tính thể tích khối chóp S.ABCD."


def _png_nho() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (255, 255, 255)).save(buf, format="PNG")
    return buf.getvalue()


async def do_so_lan_thu_moi_tang() -> dict[str, int]:
    """Số request mỗi tầng khi provider LUÔN trả 503 — dưới đúng ngân sách nghiệm thu."""
    dem = {**dict.fromkeys(STAGES, 0), "unknown": 0}

    def tra_503(_request: httpx.Request) -> httpx.Response:
        dem[STAGE_THEO_TELEMETRY.get(current_stage(), "unknown")] += 1
        return httpx.Response(503, json={"error": {"message": "tham do chinh sach thu lai"}})

    cong = CongHttp(httpx.MockTransport(tra_503), 1000, BoKhuBiMat(), dung_sau_loi=False)
    cong.dat_ca("PROBE")
    anh = normalize_image(_png_nho())
    with dung_ngan_sach(gemini.ApiBudget(max_attempts=MAX_ATTEMPTS_PER_LOGICAL_CALL)), cai_cong_http(cong):
        for goi in (
            lambda: ie.extract_problem_from_image(anh, "PROBE", cache_version=None),
            lambda: pipeline.stage_semantic_analyze(DE_THAM_DO, "PROBE", DOMAIN_HINH_HOC),
            lambda: pipeline.stage_semantic_program(DE_THAM_DO, {}, "PROBE", None, domain=DOMAIN_HINH_HOC),
        ):
            try:
                await goi()
            except Exception:  # noqa: BLE001 — 503 là CHỦ Ý; chỉ đếm số request
                pass
    return {s: dem[s] for s in STAGES}


# ══════════════════════════════════════════════════════════════════════════
# §4 · CER VÀ DỮ KIỆN QUAN TRỌNG
# ══════════════════════════════════════════════════════════════════════════
def chuan_hoa_cer(s: str) -> str:
    """CHỈ ba phép: NFC · CRLF/CR → LF · bỏ khoảng trắng cuối dòng."""
    s = unicodedata.normalize("NFC", s).replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(dong.rstrip() for dong in s.split("\n"))


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    truoc = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        nay = [i]
        for j, cb in enumerate(b, 1):
            nay.append(min(truoc[j] + 1, nay[j - 1] + 1, truoc[j - 1] + (ca != cb)))
        truoc = nay
    return truoc[-1]


def cer(reference: str, prediction: str) -> float:
    r, p = chuan_hoa_cer(reference), chuan_hoa_cer(prediction)
    return levenshtein(r, p) / max(1, len(r))


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s).strip()


def _gon(s: str) -> str:
    """Luật KHỚP dữ kiện (không phải chuẩn hoá CER): NFC + gộp khoảng trắng."""
    return " ".join(unicodedata.normalize("NFC", s).split())


def _cac_dang(muc: str | list[str]) -> list[str]:
    return [muc] if isinstance(muc, str) else list(muc)


_MAU_CUM_NHAN = re.compile(r"(?<![^\W\d_])((?:[A-Z][₀-₉0-9']*)+)(?![^\W\d_])")
_MAU_MOT_NHAN = re.compile(r"[A-Z][₀-₉0-9']*")


def nhan_diem_trong_van_ban(s: str) -> set[str]:
    """Nhãn điểm xuất hiện như KÝ HIỆU: `S.ABCD` → S A B C D; `Cho`, `Oxyz` → không."""
    ra: set[str] = set()
    for m in _MAU_CUM_NHAN.finditer(unicodedata.normalize("NFC", s)):
        ra.update(_MAU_MOT_NHAN.findall(m.group(1)))
    return ra


_MAU_SO = re.compile(r"\d+(?:[.,]\d+)?")


def ky_hieu_va_so(s: str) -> set[str]:
    """Nhãn điểm (như KÝ HIỆU) và con số trong một chuỗi — hai thứ một dữ kiện có thể bịa ra."""
    s = unicodedata.normalize("NFC", s)
    return nhan_diem_trong_van_ban(s) | set(_MAU_SO.findall(s))


def cham_du_kien(cf: dict, x: ie.ImageProblemExtraction, van_ban_nguon: str) -> dict:
    van_ban = x.problem_text_verbatim + "\n" + x.problem_text_normalized
    gon_vb = _gon(van_ban)
    nhan_vb = nhan_diem_trong_van_ban(van_ban)
    nguon = ky_hieu_va_so(van_ban_nguon)

    def bia(muc: str) -> bool:
        # BỊA = mang một nhãn hay con số KHÔNG có trong ĐỀ GỐC (ground truth). Mục THỪA mà
        # mọi nhãn và con số đều có trong đề thì không bịa: `transcribe.md` dặn chép "những
        # gì VIẾT trong đề chữ", nên vision sẽ kê cả quan hệ, công thức, nhãn thiết diện `(T)`
        # mà ground truth không liệt kê. Bản đầu đếm MỌI mục thừa là bịa — một lượt đọc
        # trung thành sẽ bị đánh trượt, và lượt thật chỉ có một lần.
        return not ky_hieu_va_so(muc) <= nguon

    gt_diem = [_nfc(p) for p in cf["point_labels"]]
    du_doan_diem = {_nfc(p) for p in x.named_points}
    diem_dung = [p for p in gt_diem if p in du_doan_diem and p in nhan_vb]
    diem_thua = sorted(du_doan_diem - set(gt_diem))

    bieu_thuc = {_gon(e.normalized) for e in x.math_expressions} | {_gon(e.verbatim) for e in x.math_expressions}
    cong_thuc_dung = [f for f in cf["formulas"]
                      if any(_gon(d) in bieu_thuc or _gon(d) in gon_vb for d in _cac_dang(f))]
    gt_cong_thuc = {_gon(d) for f in cf["formulas"] for d in _cac_dang(f)}
    cong_thuc_thua = sorted({_gon(e.verbatim) + " ⇔ " + _gon(e.normalized) for e in x.math_expressions
                             if _gon(e.verbatim) not in gt_cong_thuc and _gon(e.normalized) not in gt_cong_thuc})

    khoi = {_gon(s) for s in x.named_solids}
    gt_khoi = {_gon(d) for o in cf["objects"] for d in _cac_dang(o)}
    vat_dung = [o for o in cf["objects"] if any(_gon(d) in khoi or _gon(d) in gon_vb for d in _cac_dang(o))]
    khoi_thua = sorted(khoi - gt_khoi)

    quan_he = {_gon(r) for r in x.given_relations}
    gt_quan_he = {_gon(d) for r in cf["relations"] for d in _cac_dang(r)}
    quan_he_dung = [r for r in cf["relations"]
                    if any(_gon(d) in quan_he or _gon(d) in gon_vb for d in _cac_dang(r))]
    quan_he_thua = sorted(quan_he - gt_quan_he)

    yeu_cau = cf["request"]
    yeu_cau_dung = None if not yeu_cau.strip() else _gon(yeu_cau) in gon_vb

    def ti_le(dung: list, tong: list) -> float | None:
        return None if not tong else round(len(dung) / len(tong), 4)

    bia_theo_nhom = {
        "point_labels": [p for p in diem_thua if bia(p)],
        "formulas": [f for f in cong_thuc_thua if bia(f)],
        "objects": [o for o in khoi_thua if bia(o)],
        "relations": [r for r in quan_he_thua if bia(r)],
    }
    return {
        "POINT_LABEL_ACCURACY": ti_le(diem_dung, gt_diem),
        "FORMULA_ACCURACY": ti_le(cong_thuc_dung, cf["formulas"]),
        "OBJECT_ACCURACY": ti_le(vat_dung, cf["objects"]),
        "RELATION_ACCURACY": ti_le(quan_he_dung, cf["relations"]),
        "REQUEST_ACCURACY": None if yeu_cau_dung is None else (1.0 if yeu_cau_dung else 0.0),
        "HALLUCINATED_CRITICAL_FACTS": sum(len(v) for v in bia_theo_nhom.values()),
        "details": {
            "point_labels_missing": [p for p in gt_diem if p not in diem_dung],
            "point_labels_extra": diem_thua,
            "point_labels_hallucinated": bia_theo_nhom["point_labels"],
            "formulas_missing": [f for f in cf["formulas"] if f not in cong_thuc_dung],
            "formulas_extra": cong_thuc_thua,
            "formulas_hallucinated": bia_theo_nhom["formulas"],
            "objects_missing": [o for o in cf["objects"] if o not in vat_dung],
            "objects_extra": khoi_thua,
            "objects_hallucinated": bia_theo_nhom["objects"],
            "relations_missing": [r for r in cf["relations"] if r not in quan_he_dung],
            "relations_extra": quan_he_thua,
            "relations_hallucinated": bia_theo_nhom["relations"],
        },
    }


def cham_doc_anh(case_id: str, g: dict, x: ie.ImageProblemExtraction, van_ban_xac_nhan: str) -> dict:
    ref = g["expected_text"]
    nguong = NGUONG_CER[case_id]
    ket = {
        "CER_THRESHOLD": nguong,
        "RAW_TEXT_CER": round(cer(ref, x.problem_text_verbatim), 6),
        "RAW_NORMALIZED_TEXT_CER": round(cer(ref, x.problem_text_normalized), 6),
        "CONFIRMED_TEXT_CER": round(cer(ref, van_ban_xac_nhan), 6),
        **cham_du_kien(g["critical_facts"], x, ref),
    }
    ly_do: list[str] = []
    if ket["RAW_TEXT_CER"] > nguong:
        ly_do.append(f"RAW_TEXT_CER {ket['RAW_TEXT_CER']} > {nguong}")
    for nhom in ("POINT_LABEL_ACCURACY", "FORMULA_ACCURACY", "OBJECT_ACCURACY",
                 "RELATION_ACCURACY", "REQUEST_ACCURACY"):
        if ket[nhom] is not None and ket[nhom] < 1.0:
            ly_do.append(f"{nhom} {ket[nhom]} < 1.0")
    if ket["HALLUCINATED_CRITICAL_FACTS"]:
        ly_do.append(f"HALLUCINATED_CRITICAL_FACTS {ket['HALLUCINATED_CRITICAL_FACTS']}")
    ket["fail_reasons"] = ly_do
    return ket


# ══════════════════════════════════════════════════════════════════════════
# §5 · ĐẦU VÀO — kiểm TRƯỚC mọi request
# ══════════════════════════════════════════════════════════════════════════
class LoiDauVao(ValueError):
    pass


@dataclass
class CaDaChuan:
    case_id: str
    anh_nguon: Path
    anh: NormalizedImage
    mo_ta_anh: dict


@dataclass
class CauHinh:
    cases: list[CaDaChuan]
    ground_truth: dict[str, dict]
    ground_truth_path: Path
    output_dir: Path
    max_http_requests: int
    dry_run: bool
    confirmed_text: dict[str, str]
    include_images: bool
    danh_tinh: dict = field(default_factory=dict)


def _tuyet_doi(gia_tri: str | None, ten: str) -> Path:
    if not gia_tri:
        raise LoiDauVao(f"thiếu {ten}")
    p = Path(gia_tri)
    if not p.is_absolute():
        raise LoiDauVao(f"{ten} phải là đường dẫn TUYỆT ĐỐI, nhận {gia_tri!r}")
    return p


def _kiem_danh_sach(v: Any, ten: str, *, cho_phep_luan_phien: bool) -> None:
    if not isinstance(v, list):
        raise LoiDauVao(f"`{ten}` phải là mảng")
    for muc in v:
        if isinstance(muc, str) and muc.strip():
            continue
        if cho_phep_luan_phien and isinstance(muc, list) and muc and all(isinstance(d, str) and d.strip() for d in muc):
            continue
        raise LoiDauVao(f"`{ten}` có mục không hợp lệ: {muc!r}")


def doc_ground_truth(p: Path, can: list[str]) -> dict[str, dict]:
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        raise LoiDauVao(f"không đọc được ground truth: {type(err).__name__}")
    ds = d.get("cases") if isinstance(d, dict) else d
    if not isinstance(ds, list):
        raise LoiDauVao("ground truth phải có mảng `cases`")
    theo: dict[str, dict] = {}
    for c in ds:
        if not isinstance(c, dict) or c.get("case_id") not in CASE_IDS:
            raise LoiDauVao(f"mục ground truth không hợp lệ: {str(c)[:80]!r}")
        if c["case_id"] in theo:
            raise LoiDauVao(f"ground truth trùng {c['case_id']}")
        theo[c["case_id"]] = c
    for cid in can:
        g = theo.get(cid)
        if g is None:
            raise LoiDauVao(f"ground truth thiếu {cid}")
        if cid == "C03":
            if g.get("expected_outcome") != "SAFE_REJECTION":
                raise LoiDauVao("C03 phải khai expected_outcome = SAFE_REJECTION")
            continue
        if not isinstance(g.get("expected_text"), str) or not g["expected_text"].strip():
            raise LoiDauVao(f"{cid} thiếu expected_text")
        cf = g.get("critical_facts")
        if not isinstance(cf, dict):
            raise LoiDauVao(f"{cid} thiếu critical_facts")
        _kiem_danh_sach(cf.get("point_labels"), f"{cid}.point_labels", cho_phep_luan_phien=False)
        if not cf["point_labels"]:
            raise LoiDauVao(f"{cid}.point_labels không được rỗng")
        for ten in ("formulas", "objects", "relations"):
            _kiem_danh_sach(cf.get(ten), f"{cid}.{ten}", cho_phep_luan_phien=True)
        if not isinstance(cf.get("request"), str):
            raise LoiDauVao(f"{cid}.request phải là chuỗi")
    return theo


def tim_anh(thu_muc: Path, cid: str, g: dict) -> Path:
    ten = g.get("image_file")
    if ten is not None:
        if not isinstance(ten, str) or Path(ten).name != ten:
            raise LoiDauVao(f"{cid}.image_file chỉ được là TÊN tệp trong --input-dir")
        p = thu_muc / ten
        if not p.is_file():
            raise LoiDauVao(f"không thấy {ten} trong --input-dir")
        return p
    ung = [f for f in thu_muc.iterdir()
           if f.is_file() and f.stem.upper() == cid and f.suffix.lower() in DUOI_ANH]
    if len(ung) != 1:
        raise LoiDauVao(f"cần đúng MỘT ảnh {cid}.jpg/.jpeg/.png/.webp trong --input-dir, thấy {len(ung)}")
    return ung[0]


def mo_ta_anh(p: Path, cid: str, nguon: str) -> tuple[dict, NormalizedImage]:
    raw = p.read_bytes()
    try:
        anh = normalize_image(raw)
    except ImageRejected as err:
        raise LoiDauVao(f"{cid}: ảnh bị từ chối ({err.code})")
    with Image.open(io.BytesIO(raw)) as im:
        rong, cao = im.size
    return {
        "CASE_ID": cid,
        "SOURCE": nguon,
        "IMAGE_SHA256": _sha(raw),
        "NORMALIZED_IMAGE_SHA256": anh.sha256,
        "MIME_TYPE": sniff_image_mime(raw),
        "FILE_SIZE": len(raw),
        "PIXEL_DIMENSIONS": [rong, cao],
        "NORMALIZED_PIXEL_DIMENSIONS": [anh.width, anh.height],
        "EXIF_ORIENTATION": anh.exif_orientation,
        "SOURCE_HAD_GPS": anh.source_had_gps,
    }, anh


def danh_tinh_mo_hinh() -> dict:
    return {
        "MODEL_ID": gemini.MODEL,
        "PROMPT_SHA256": _sha(gemini.load_skill(ie.VISION_PROMPT_SKILL)),
        "SCHEMA_SHA256": _sha(json.dumps(ie.VISION_RESPONSE_SCHEMA, sort_keys=True, ensure_ascii=False)),
        "VISION_SCHEMA_VERSION": ie.VISION_SCHEMA_VERSION,
    }


def chuan_bi(ns: argparse.Namespace) -> CauHinh:
    thu_muc_anh = _tuyet_doi(ns.input_dir, "--input-dir")
    if not thu_muc_anh.is_dir():
        raise LoiDauVao(f"--input-dir không tồn tại: {thu_muc_anh}")
    gt_path = _tuyet_doi(ns.ground_truth, "--ground-truth")
    if not gt_path.is_file():
        raise LoiDauVao(f"--ground-truth không tồn tại: {gt_path}")
    ra = _tuyet_doi(ns.output_dir, "--output-dir")
    if ra.exists() and (not ra.is_dir() or any(ra.iterdir())):
        raise LoiDauVao("--output-dir phải là thư mục MỚI hoặc RỖNG — không ghi đè lượt cũ")
    if not 1 <= ns.max_http_requests <= MAX_HTTP_REQUESTS:
        raise LoiDauVao(f"--max-http-requests phải trong 1…{MAX_HTTP_REQUESTS}")
    if ns.include_sanitized_images and not ns.confirm_no_personal_data:
        raise LoiDauVao("--include-sanitized-images cần kèm --confirm-no-personal-data")

    can = list(CASE_IDS) if ns.case == "all" else [ns.case]
    gt = doc_ground_truth(gt_path, can)
    xac_nhan: dict[str, str] = {}
    if ns.confirmed_text:
        p = _tuyet_doi(ns.confirmed_text, "--confirmed-text")
        try:
            xac_nhan = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as err:
            raise LoiDauVao(f"không đọc được --confirmed-text: {type(err).__name__}")
        if not isinstance(xac_nhan, dict) or any(
                k not in ("C01", "C02") or not isinstance(v, str) or not v.strip() for k, v in xac_nhan.items()):
            raise LoiDauVao("--confirmed-text phải là object {C01|C02: văn bản không rỗng}")

    nguon = "FIXTURE_DRY_RUN" if ns.dry_run else "REAL_PHOTO"
    cases = []
    for cid in can:
        p = tim_anh(thu_muc_anh, cid, gt[cid])
        mo_ta, anh = mo_ta_anh(p, cid, nguon)
        cases.append(CaDaChuan(cid, p, anh, mo_ta))
    return CauHinh(cases, gt, gt_path, ra, ns.max_http_requests, ns.dry_run, xac_nhan,
                   bool(ns.include_sanitized_images), danh_tinh_mo_hinh())


# ══════════════════════════════════════════════════════════════════════════
# §6 · PROVIDER GIẢ CHO --dry-run (không bao giờ dùng khi chạy thật)
# ══════════════════════════════════════════════════════════════════════════
def _phan_hoi_gemini(text: str) -> httpx.Response:
    return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}}]})


def ban_ghi_gia_lap(g: dict) -> dict:
    if g.get("expected_outcome") == "SAFE_REJECTION":
        return {"problem_text_verbatim": "", "problem_text_normalized": "", "math_expressions": [],
                "named_points": [], "named_lines": [], "named_planes": [], "named_solids": [],
                "given_relations": [], "has_diagram": True,
                "diagram_observations": ["Chỉ có hình vẽ, không có đề bài bằng chữ."],
                "text_diagram_conflicts": [], "uncertain_tokens": [], "missing_regions": [], "confidence": 0.9}
    cf = g["critical_facts"]
    dau = [_cac_dang(f)[0] for f in cf["formulas"]]
    return {"problem_text_verbatim": g["expected_text"], "problem_text_normalized": g["expected_text"],
            "math_expressions": [{"verbatim": f, "normalized": f} for f in dau],
            "named_points": list(cf["point_labels"]), "named_lines": [], "named_planes": [],
            "named_solids": [_cac_dang(o)[0] for o in cf["objects"]],
            "given_relations": [_cac_dang(r)[0] for r in cf["relations"]],
            "has_diagram": True, "diagram_observations": [], "text_diagram_conflicts": [],
            "uncertain_tokens": [], "missing_regions": [], "confidence": 0.95}


class TransportGiaGemini(httpx.AsyncBaseTransport):
    """Vision trả ground truth; analyze/synthesis phát lại byte đóng băng `dry_run_replay_case`."""

    def __init__(self, cong: CongHttp, ground_truth: dict[str, dict]) -> None:
        import replay_negative_boundaries as RNB

        self._rnb = RNB
        self.cong = cong
        self.gt = ground_truth
        self.invocations = 0
        self._hang: dict[str, dict[str, list[str]]] = {}

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.invocations += 1
        cid = self.cong.case_id
        stage = STAGE_THEO_TELEMETRY.get(current_stage())
        g = self.gt[cid]
        if stage == "vision":
            return _phan_hoi_gemini(json.dumps(ban_ghi_gia_lap(g), ensure_ascii=False))
        phat_lai = g.get("dry_run_replay_case")
        if not phat_lai:
            return httpx.Response(400, json={"error": "DRY_RUN_KHONG_CO_BAN_PHAT_LAI"})
        hang = self._hang.setdefault(cid, self._rnb.doc_raw_theo_thu_tu(phat_lai))
        ds = hang["semantic_analyze" if stage == "analyze" else "semantic_program"]
        if not ds:
            return httpx.Response(400, json={"error": "DRY_RUN_HET_BAN_PHAT_LAI"})
        return _phan_hoi_gemini(ds.pop(0))


class TransportKichBan(httpx.AsyncBaseTransport):
    """Provider giả theo KỊCH BẢN `(ca, tầng) → [phản hồi…]` — cho test và script bằng chứng.

    Mỗi mục là chuỗi (văn bản Gemini trả về), `httpx.Response`, một ngoại lệ để ném,
    hoặc hàm `request → một trong ba thứ ấy`. Hết kịch bản ⇒ HTTP 599: pipeline đi
    lệch đường đã định thì lộ ra thành một ca hỏng, không lặng lẽ được phục vụ.
    """

    def __init__(self, cong: CongHttp, kich_ban: dict[tuple[str, str], list]) -> None:
        self.cong = cong
        self.kich_ban = {k: list(v) for k, v in kich_ban.items()}
        self.calls: list[tuple[str | None, str]] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        khoa = (self.cong.case_id, STAGE_THEO_TELEMETRY.get(current_stage(), "unknown"))
        self.calls.append(khoa)
        ds = self.kich_ban.get(khoa)
        if not ds:
            return httpx.Response(599, json={"error": f"KICH_BAN_HET {khoa}"})
        muc = ds.pop(0)
        if callable(muc):
            muc = muc(request)
        if isinstance(muc, BaseException):
            raise muc
        return muc if isinstance(muc, httpx.Response) else _phan_hoi_gemini(muc)


# ══════════════════════════════════════════════════════════════════════════
# §7 · MỘT CA
# ══════════════════════════════════════════════════════════════════════════
def _dong_ca(kq: dict, cong: CongHttp) -> dict:
    kq["http"] = cong.theo_ca(kq["case_id"])
    kq["result"] = "PASS" if not kq["fail_reasons"] else "FAIL"
    kq["finished_at"] = _bay_gio()
    return kq


async def chay_mot_ca(ca: CaDaChuan, ch: CauHinh, cong: CongHttp, khu: BoKhuBiMat, api_key: str) -> dict:
    cid = ca.case_id
    cong.dat_ca(cid)
    ra = ch.output_dir
    kq: dict = {"case_id": cid, "started_at": _bay_gio(), "fail_reasons": []}
    tho: dict = {"case_id": cid, "image": ca.mo_ta_anh, **ch.danh_tinh}

    t0 = time.perf_counter()
    ex = None
    try:
        ex = await ie.extract_problem_from_image(ca.anh, api_key, cache_version=None)
    except gemini.BudgetExceeded as err:
        kq["fail_reasons"].append(f"VISION_HTTP_BLOCKED: {err}")
    except (ie.VisionUnavailable, ie.VisionContractError, ie.VisionBusy) as err:
        kq["fail_reasons"].append(f"VISION_PROVIDER_OR_CONTRACT_ERROR: {_chuoi_loi(err)}")
    tho.update(latency_ms=round((time.perf_counter() - t0) * 1000, 1),
               http=[r for r in cong.records if r["case_id"] == cid and r["stage"] == "vision"])
    if ch.include_images:
        (ra / f"{cid}_SANITIZED.jpg").write_bytes(ca.anh.data)
    if ex is None:
        tho["error"] = kq["fail_reasons"][-1]
        _ghi_json(ra, f"{cid}_RAW_EXTRACTION.json", tho, khu)
        return _dong_ca(kq, cong)
    tho.update(extraction=ex.extraction.model_dump(), assessment=ex.assessment.to_dict())
    _ghi_json(ra, f"{cid}_RAW_EXTRACTION.json", tho, khu)
    x, a = ex.extraction, ex.assessment

    if cid == "C03":
        an_toan = a.status == "rejected"
        kq.update(C03_SAFE_REJECTION=an_toan, REJECTION_CODE=a.rejection_code,
                  REJECTED_BEFORE_SCENE=an_toan, SILENT_HALLUCINATION=0 if an_toan else 1,
                  EMPTY_SCENE_SHOWN_AS_SUCCESS="NO")
        if not an_toan:
            kq["fail_reasons"].append("C03_NOT_REJECTED: tầng đọc ảnh cho qua một ảnh thiếu dữ kiện")
        return _dong_ca(kq, cong)

    g = ch.ground_truth[cid]
    van_ban_mo_hinh = a.problem_text
    van_ban_dung = ch.confirmed_text.get(cid, van_ban_mo_hinh)
    diem = cham_doc_anh(cid, g, x, van_ban_dung)
    kq["vision_scoring"] = diem
    if a.status == "rejected":
        kq["fail_reasons"].append(f"VISION_REJECTED: {a.rejection_code}")
    kq["fail_reasons"] += diem["fail_reasons"]
    _ghi_json(ra, f"{cid}_CONFIRMED_INPUT.json", {
        "case_id": cid,
        "MODEL_RAW_TEXT": van_ban_mo_hinh,
        "USER_CONFIRMED_TEXT": van_ban_dung,
        "CONFIRMATION_SOURCE": "CONFIRMED_TEXT_FILE" if cid in ch.confirmed_text else "HUMAN_EDIT_NONE_MODEL_TEXT",
        "EDITED": van_ban_dung != van_ban_mo_hinh,
        "requires_confirmation": a.requires_confirmation,
        "review_flags": list(a.review_flags),
    }, khu)
    if kq["fail_reasons"]:
        kq["analyze_skipped"] = "VISION_NOT_PASSED — không tiêu quota tầng B"
        return _dong_ca(kq, cong)

    env = None
    try:
        env = await pipeline.run_pipeline(van_ban_dung, api_key, semantic_route="serve")
    except gemini.BudgetExceeded as err:
        kq["fail_reasons"].append(f"ANALYZE_OR_SYNTHESIS_HTTP_BLOCKED: {err}")
    except Exception as err:  # noqa: BLE001 — lỗi provider thoát khỏi run_pipeline nguyên dạng
        kq["fail_reasons"].append(f"ANALYZE_OR_SYNTHESIS_PROVIDER_ERROR: {_chuoi_loi(err)}")

    than = cong.van_ban_analyze.get(cid, [])
    rao_dung = f'"""\n{van_ban_dung}\n"""'
    rao_mo_hinh = f'"""\n{van_ban_mo_hinh}\n"""'
    kq["USER_EDIT_PAYLOAD_PARITY"] = bool(than) and all(rao_dung in t for t in than) and (
        van_ban_dung == van_ban_mo_hinh or all(rao_mo_hinh not in t for t in than))
    if than and not kq["USER_EDIT_PAYLOAD_PARITY"]:
        kq["fail_reasons"].append("USER_EDIT_PAYLOAD_PARITY_BROKEN")

    ket_analyze: dict = {"case_id": cid, "analyze_input_sha256": _sha(van_ban_dung)}
    if env is None:
        ket_analyze["error"] = kq["fail_reasons"][-1]
        _ghi_json(ra, f"{cid}_ANALYZE_RESULT.json", ket_analyze, khu)
        return _dong_ca(kq, cong)
    ket_analyze.update({k: env.get(k) for k in (
        "status", "simulation_id", "stage_reached", "error_code", "failure_category", "learner_reason")})
    _ghi_json(ra, f"{cid}_ANALYZE_RESULT.json", ket_analyze, khu)

    canh = env.get("scene3d") or {}
    vat = canh.get("objects") or []
    loai = sorted({str(o.get("type")) for o in vat})
    mong = g.get("expected_scene_kinds")
    khop = None if not mong else loai == sorted(mong)
    _ghi_json(ra, f"{cid}_SCENE_RESULT.json", {
        "case_id": cid,
        "scene_object_count": len(vat),
        "scene_event_count": len(canh.get("events") or []),
        "scene_kinds": loai,
        "expected_scene_kinds": mong,
        "scene_kinds_match": khop if khop is not None else "NOT_DECLARED",
        "objects": [{k: o.get(k) for k in ("id", "type", "label", "name")} for o in vat],
    }, khu)
    kq.update(scene_object_count=len(vat), scene_kinds=loai,
              EMPTY_SCENE=env.get("status") == "ok" and not vat)
    if env.get("status") != "ok":
        kq["fail_reasons"].append(f"ANALYZE_NOT_OK: {env.get('error_code')}")
    elif not vat:
        kq["fail_reasons"].append("EMPTY_SCENE")
    elif khop is False:
        kq["fail_reasons"].append(f"SCENE_KINDS_MISMATCH: {loai} ≠ {sorted(mong)}")
    return _dong_ca(kq, cong)


async def chay_cac_ca(ch: CauHinh, cong: CongHttp, khu: BoKhuBiMat, api_key: str,
                      kenh: KenhIn) -> tuple[list[dict], list[str]]:
    ket: list[dict] = []
    chua_chay: list[str] = []
    try:
        for i, ca in enumerate(ch.cases):
            r = await chay_mot_ca(ca, ch, cong, khu, api_key)
            ket.append(r)
            chi_tiet = f" — {'; '.join(r['fail_reasons'])}" if r["fail_reasons"] else ""
            kenh.in_(f"  {ca.case_id}: {r['result']}{chi_tiet}")
            if r["result"] != "PASS":
                chua_chay = [c.case_id for c in ch.cases[i + 1:]]
                break
    finally:
        dong = getattr(cong.inner, "aclose", None)
        if dong is not None:
            try:
                await dong()
            except Exception:  # noqa: BLE001
                pass
    return ket, chua_chay


# ══════════════════════════════════════════════════════════════════════════
# §8 · CLI
# ══════════════════════════════════════════════════════════════════════════
def tao_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="run_photo_problem_live.py", add_help=True)
    ap.add_argument("--case", choices=[*CASE_IDS, "all"])
    ap.add_argument("--input-dir")
    ap.add_argument("--ground-truth")
    ap.add_argument("--output-dir")
    ap.add_argument("--max-http-requests", type=int, default=MAX_HTTP_REQUESTS)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--confirmed-text")
    ap.add_argument("--include-sanitized-images", action="store_true")
    ap.add_argument("--confirm-no-personal-data", action="store_true")
    return ap


def main(argv: list[str] | None = None, *,
         inner_transport_factory: Callable[[CongHttp], httpx.AsyncBaseTransport] | None = None,
         env: dict[str, str] | None = None, stdout=None, stderr=None) -> int:
    moi_truong = dict(os.environ if env is None else env)
    khoa = moi_truong.get("GEMINI_API_KEY") or ""
    khu = BoKhuBiMat((khoa,))
    kenh = KenhIn(khu, stdout, stderr)
    for ten in ("httpx", "httpcore"):
        logging.getLogger(ten).setLevel(logging.WARNING)

    try:
        ns = tao_parser().parse_args(argv)
    except SystemExit as e:
        return EXIT_USAGE if e.code else EXIT_PASS
    if ns.case is None:
        kenh.loi(HUONG_DAN)
        return EXIT_USAGE
    try:
        ch = chuan_bi(ns)
    except LoiDauVao as err:
        kenh.loi(f"TỪ CHỐI TRƯỚC KHI GỌI PROVIDER: {err}")
        return EXIT_USAGE

    if not ch.dry_run and (moi_truong.get("ALLOW_LIVE_AI") != "1" or not khoa):
        thieu = [t for t, ok in (("ALLOW_LIVE_AI=1", moi_truong.get("ALLOW_LIVE_AI") == "1"),
                                 ("GEMINI_API_KEY", bool(khoa))) if not ok]
        kenh.loi(f"REAL_PROVIDER_EVIDENCE = NOT_ESTABLISHED — thiếu {', '.join(thieu)}. 0 request.")
        return EXIT_NO_KEY

    with ChanMangThat() as chan_tham_do:
        so_lan = asyncio.run(do_so_lan_thu_moi_tang())
    if so_lan != {s: 1 for s in STAGES} or chan_tham_do.attempts:
        kenh.loi(f"RETRY_POLICY_NOT_ENFORCEABLE — request mỗi tầng khi provider trả 503: {so_lan}. 0 request thật.")
        return EXIT_RETRY_POLICY
    try:
        budget = tao_ngan_sach_nghiem_thu()
    except ValueError as err:
        kenh.loi(str(err))
        return EXIT_RETRY_POLICY

    # Ba chế độ, và chỉ MỘT được gọi là provider thật. Transport tiêm vào (test,
    # script bằng chứng) đi đúng các cổng như lượt thật — kể cả đòi khoá ở trên —
    # nhưng KHÔNG BAO GIỜ được ghi thành bằng chứng provider, và vẫn bị chặn mạng.
    that = inner_transport_factory is None and not ch.dry_run
    che_do = "REAL_PROVIDER" if that else "DRY_RUN" if ch.dry_run else "INJECTED_TRANSPORT"
    nguon = {"REAL_PROVIDER": "REAL_PHOTO", "DRY_RUN": "FIXTURE_DRY_RUN",
             "INJECTED_TRANSPORT": "INJECTED_TRANSPORT_FIXTURE"}[che_do]
    for ca in ch.cases:
        ca.mo_ta_anh["SOURCE"] = nguon

    ch.output_dir.mkdir(parents=True, exist_ok=True)
    _ghi_json(ch.output_dir, "GROUND_TRUTH.json",
              json.loads(ch.ground_truth_path.read_text(encoding="utf-8")), khu)
    cong = CongHttp(None, ch.max_http_requests, khu)
    if inner_transport_factory is not None:
        cong.inner = inner_transport_factory(cong)
    elif ch.dry_run:
        cong.inner = TransportGiaGemini(cong, ch.ground_truth)
    else:
        cong.inner = httpx.AsyncHTTPTransport()
    api_key = "DRY_RUN_KHONG_PHAI_KHOA" if ch.dry_run else khoa

    kenh.in_(f"{WAVE} · {che_do} · ca {[c.case_id for c in ch.cases]} · trần HTTP {ch.max_http_requests}")
    ket: list[dict] = []
    chua_chay: list[str] = []
    loi_runner = None
    chan_mang = None if that else ChanMangThat()
    try:
        with dung_ngan_sach(budget), cai_cong_http(cong):
            if chan_mang is not None:
                with chan_mang:
                    ket, chua_chay = asyncio.run(chay_cac_ca(ch, cong, khu, api_key, kenh))
            else:
                ket, chua_chay = asyncio.run(chay_cac_ca(ch, cong, khu, api_key, kenh))
    except Exception as err:  # noqa: BLE001 — lỗi bất ngờ vẫn phải ra artifact đã khử secret
        loi_runner = "".join(traceback.format_exception_only(type(err), err)).strip()
        kenh.loi(f"RUNNER_ERROR: {loi_runner}")

    tong = cong.tong_hop()
    tat_ca_dat = not loi_runner and len(ket) == len(ch.cases) and all(r["result"] == "PASS" for r in ket)
    tom_tat = {
        "wave": WAVE,
        "run_mode": che_do,
        "SOURCE": nguon,
        **NHAN_KHAI_TRUOC,
        **ch.danh_tinh,
        "GROUND_TRUTH_SHA256": _sha(ch.ground_truth_path.read_bytes()),
        "cases_requested": [c.case_id for c in ch.cases],
        "cases_run": [r["case_id"] for r in ket],
        "cases_not_run": [{"case_id": c, "status": "NOT_RUN_PREVIOUS_CASE_FAILED"} for c in chua_chay],
        "RETRY_POLICY_PROBE": so_lan,
        **tong,
        "FAKE_OR_INNER_TRANSPORT_INVOCATIONS": cong.inner_invocations,
        "APIBUDGET_HTTP_COUNT": budget.http_requests,
        "APIBUDGET_MATCHES_GATE": budget.http_requests == cong.attempted,
        "APIBUDGET_RETRY_REQUESTS": budget.retry_requests,
        "APPLICATION_LLM_CALLS": budget.logical_calls if that else 0,
        "FIXTURE_LOGICAL_CALLS": 0 if that else budget.logical_calls,
        "REAL_PROVIDER_CALLS": cong.sent if that else 0,
        "NETWORK_REQUESTS": "NOT_BLOCKED_REAL_RUN" if chan_mang is None else len(chan_mang.attempts),
        # Bằng chứng provider = provider THẬT đã trả ít nhất một 2xx. Gửi đi rồi nhận 403
        # thì chưa phải bằng chứng gì cả; còn ĐẠT hay không là việc của `ACCEPTANCE`.
        "REAL_PROVIDER_EVIDENCE": (f"NOT_APPLICABLE_{che_do}" if not that
                                   else "ESTABLISHED" if any(200 <= (r.get("http_status") or 0) < 300
                                                             for r in cong.records)
                                   else "NOT_ESTABLISHED"),
        "RAW_PHOTOS_COPIED": 0,
        "SANITIZED_IMAGES_WRITTEN": len(ket) if ch.include_images else 0,
        "RUNNER_ERROR": loi_runner,
        "cases": ket,
        "ACCEPTANCE": "PASS" if tat_ca_dat else "FAIL",
    }
    _ghi_json(ch.output_dir, "PROVIDER_CALLS.json", {"records": cong.records, **tong}, khu)
    _ghi_json(ch.output_dir, "RUN_SUMMARY.json", tom_tat, khu)
    kenh.in_(f"HTTP gửi {tong['HTTP_REQUESTS_SENT']}/{ch.max_http_requests} · chặn {tong['HTTP_REQUESTS_BLOCKED']} "
             f"· vision {tong['VISION_HTTP_REQUESTS']} · analyze {tong['ANALYZE_HTTP_REQUESTS']} "
             f"· synthesis {tong['SYNTHESIS_HTTP_REQUESTS']} · retry {tong['RETRIES']} · {tom_tat['ACCEPTANCE']}")
    kenh.in_(f"→ {ch.output_dir / 'RUN_SUMMARY.json'}")
    return EXIT_PASS if tat_ca_dat else EXIT_CASE_FAIL


if __name__ == "__main__":
    sys.exit(main())
