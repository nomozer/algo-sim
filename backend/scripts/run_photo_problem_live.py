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

`--vision-checkpoint <tuyệt đối>` (`C01_DOWNSTREAM_CHECKPOINT_ACCEPTANCE`, 2026-09-14): TIẾP TỤC
từ một lượt đọc ảnh THẬT đã lưu và chỉ đo tầng B. Một ca C01/C02. Checkpoint phải khớp ảnh ·
ground truth · model · prompt · hai lược đồ và qua lại Pydantic ĐẦY ĐỦ hiện tại, không thì
`CHECKPOINT_PROVENANCE_FAILED` trước mọi request. Cổng chặn tầng vision với trần 0 (analyze 1 ·
synthesis 3 · tổng ≤ 4). Văn bản gửi analyze là bản xem lại CỦA CHECKPOINT, không phải ground
truth; nhãn duyệt là `AUTOMATED_CHECKPOINT_REPLAY`, không bao giờ `HUMAN`. Lượt này KHÔNG phải
một lượt end-to-end nguyên khối (`SINGLE_RUN_END_TO_END = NOT_RUN`).

`--synthesis-repair-trace` (`SYNTHESIS_REPAIR_OBSERVABILITY_HARDENING`, 2026-09-14, opt-in, mặc định TẮT):
gắn `QuanTracVongSua` — observer THỤ ĐỘNG mà `run_pipeline` vốn nhận — rồi ghi
`{ca}_SYNTHESIS_REPAIR_TRACE.json`: mỗi lượt synthesis một mục (kết quả · tầng từ chối · mã ổn định ·
tóm tắt đã che · băm ứng viên/feedback · lượt sửa liên kết · token · độ trễ). Chỉ băm, mã và số
đếm; không đầu ra thô, không prompt. Không bật cờ ⇒ `observer=None`, y như trước.

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
import ast
import asyncio
import difflib
import hashlib
import inspect
import io
import json
import logging
import os
import re
import socket
import sys
import textwrap
import time
import traceback
import unicodedata
import uuid
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
#: Tiếp tục từ checkpoint đọc ảnh: 0 vision + 1 analyze + `MAX_SEMANTIC_PROGRAM_ATTEMPTS` synthesis.
TRAN_THEO_TANG_CHECKPOINT = {"vision": 0, "analyze": 1, "synthesis": pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS}
MAX_HTTP_REQUESTS_CHECKPOINT = sum(TRAN_THEO_TANG_CHECKPOINT.values())
STAGES_TANG_B = ("analyze", "synthesis")
#: Trường `usageMetadata` được ghi — CHỈ số đếm. Không bao giờ ghi `responseId`, nội dung hay đầu mục.
TRUONG_TOKEN_SO = ("promptTokenCount", "candidatesTokenCount", "thoughtsTokenCount",
                   "cachedContentTokenCount", "toolUsePromptTokenCount", "totalTokenCount")
TRUONG_TOKEN_CHI_TIET = ("promptTokensDetails", "candidatesTokensDetails", "cacheTokensDetails",
                         "toolUsePromptTokensDetails")
#: Băm văn bản xem lại / văn bản gửi analyze: UTF-8 của chuỗi NGUYÊN DẠNG. Không NFC, không gộp
#: khoảng trắng — chuẩn hoá ở đây sẽ che đúng thứ phép so ngang bằng sinh ra để bắt.
CHUAN_BAM_VAN_BAN = "UTF-8 của chuỗi nguyên dạng — không chuẩn hoá"
#: Hợp đồng trace vòng sửa synthesis. Đổi hình dạng ⇒ đổi phiên bản.
TRACE_VERSION = "synthesis-repair-trace/1"
#: Tầng từ chối TRONG vòng sửa — mỗi tên là một chỗ có thật trong `stage_semantic_program`, theo đúng
#: thứ tự chạy: `json.loads` · `validate_semantic_program` (khoá bị bỏ im lặng + Pydantic | kiểu
#: `SemanticTypeChecker`) · `kiem_tinh` · `check_grounding`. Ngoài vòng sửa: `ROUTE_<stage_reached>` của
#: `route.verify_and_compile` (không bao giờ được sửa), `PROVIDER`, và `HTTP_GATE` của chính runner.
PHASE_VONG_SUA = ("JSON_PARSE", "PROGRAM_SCHEMA", "PROGRAM_TYPE_CHECK", "IR_STATIC_CHECK", "GROUNDING_GATE")
TOM_TAT_TOI_DA = 500
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
  --max-http-requests N         1…11, mặc định 11 (4 với --vision-checkpoint, và không được vượt 4)
  --dry-run                     provider giả ở ranh giới HTTP, 0 request mạng
  --vision-checkpoint <tuyệt đối>  tiếp tục từ lượt đọc ảnh THẬT đã lưu — 0 vision, chỉ tầng B
  --synthesis-repair-trace      ghi trace vòng sửa synthesis (opt-in; chỉ băm, mã, số đếm)

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


def chi_so_token(usage: Any) -> dict | None:
    """`usageMetadata` → CHỈ các số đếm token (và chi tiết theo modality). Lạ/thiếu ⇒ `None`."""
    if not isinstance(usage, dict):
        return None
    ra: dict = {k: usage[k] for k in TRUONG_TOKEN_SO
                if isinstance(usage.get(k), int) and not isinstance(usage.get(k), bool)}
    for k in TRUONG_TOKEN_CHI_TIET:
        if isinstance(usage.get(k), list):
            ra[k] = [{"modality": str(d.get("modality")), "tokenCount": d["tokenCount"]}
                     for d in usage[k] if isinstance(d, dict) and isinstance(d.get("tokenCount"), int)]
    return ra or None


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
                 khu: BoKhuBiMat, *, dung_sau_loi: bool = True,
                 tran_theo_tang: dict[str, int] | None = None,
                 giu_van_ban_tang_b: bool = False) -> None:
        if max_http_requests < 1:
            raise ValueError("max_http_requests phải ≥ 1")
        if tran_theo_tang is not None and (set(tran_theo_tang) - set(STAGES) or any(
                not isinstance(v, int) or v < 0 for v in tran_theo_tang.values())):
            raise ValueError(f"tran_theo_tang chỉ nhận tầng {STAGES} với trần nguyên ≥ 0")
        self.inner = inner
        self.max_http_requests = max_http_requests
        #: Trần RIÊNG từng tầng (chế độ checkpoint: vision 0). Tầng vắng mặt ⇒ trần 0.
        self.tran_theo_tang = None if tran_theo_tang is None else dict(tran_theo_tang)
        self._lan_thu: dict = {}
        #: Chỉ khi quan trắc vòng sửa (opt-in): giữ TRONG BỘ NHỚ đầu ra đọc đề (để dựng lại RequestContract
        #: cho phép phân loại) và văn bản request synthesis (để kiểm feedback thật sự đã gửi). Không ghi ra.
        self.giu_van_ban_tang_b = giu_van_ban_tang_b
        self.phan_hoi_analyze: dict[str, list[str | None]] = {}
        self.yeu_cau_synthesis: dict[str, list[str]] = {}
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
        khoa_luot = None if b is None else (id(b), b.logical_calls)
        self._lan_thu[khoa_luot] = self._lan_thu.get(khoa_luot, 0) + 1
        rec: dict = {
            "provider_call_number": self.attempted + 1,
            "case_id": self.case_id,
            "stage": stage or "unknown",
            "telemetry_stage": nhan_tang,
            "method": request.method,
            "endpoint": f"{request.url.scheme}://{request.url.host}{request.url.path}",
            "body_sha256": bam,
            "retry": la_retry,
            # Lượt gọi LOGIC (`ApiBudget.logical_calls`, đếm trước request) và lần thử thứ mấy trong lượt ấy.
            "logical_call": None if b is None else b.logical_calls,
            "attempt": self._lan_thu[khoa_luot],
            "started_at": _bay_gio(),
        }
        if stage is None:
            ly_do = "STAGE_UNKNOWN"
        elif self.case_id is None:
            ly_do = "CASE_UNSET"
        elif self.tran_theo_tang is not None and self.sent_by_stage[stage] >= self.tran_theo_tang.get(stage, 0):
            ly_do = "STAGE_BUDGET_EXHAUSTED"
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
        if stage == "analyze" or (self.giu_van_ban_tang_b and stage == "synthesis"):
            try:
                tin = json.loads(than)["contents"][0]["parts"][-1]["text"]
            except (ValueError, KeyError, IndexError, TypeError):
                tin = ""
            if stage == "analyze":
                self.van_ban_analyze.setdefault(self.case_id, []).append(tin)
            else:
                self.yeu_cau_synthesis.setdefault(self.case_id, []).append(tin)

        t0 = time.perf_counter()
        self.inner_invocations += 1
        try:
            res = await self.inner.handle_async_request(request)
            if 200 <= res.status_code < 300:
                # Đọc thân NGAY ở cổng để lấy số token. `aread` giữ nội dung trong response nên
                # `call_gemini` đọc lại y nguyên; chỉ SỐ ĐẾM được ghi, không một mẩu nội dung nào.
                try:
                    than_tra = json.loads(await res.aread())
                    rec["usage_metadata"] = chi_so_token(than_tra.get("usageMetadata"))
                except (ValueError, AttributeError):
                    than_tra, rec["usage_metadata"] = None, None
                if self.giu_van_ban_tang_b and stage == "analyze":
                    try:
                        tra_loi = than_tra["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError, TypeError):
                        tra_loi = None
                    self.phan_hoi_analyze.setdefault(self.case_id, []).append(tra_loi)
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


async def do_so_lan_thu_moi_tang(tang: tuple[str, ...] = STAGES) -> dict[str, int]:
    """Số request mỗi tầng khi provider LUÔN trả 503 — dưới đúng ngân sách nghiệm thu.

    `tang` = các tầng lượt chạy SẼ gọi. Chế độ checkpoint không dò vision: hàm đọc ảnh không
    được chạm tới dù chỉ trên transport giả.
    """
    dem = {**dict.fromkeys(STAGES, 0), "unknown": 0}

    def tra_503(_request: httpx.Request) -> httpx.Response:
        dem[STAGE_THEO_TELEMETRY.get(current_stage(), "unknown")] += 1
        return httpx.Response(503, json={"error": {"message": "tham do chinh sach thu lai"}})

    cong = CongHttp(httpx.MockTransport(tra_503), 1000, BoKhuBiMat(), dung_sau_loi=False)
    cong.dat_ca("PROBE")
    cac_goi = {
        "vision": lambda: ie.extract_problem_from_image(normalize_image(_png_nho()), "PROBE", cache_version=None),
        "analyze": lambda: pipeline.stage_semantic_analyze(DE_THAM_DO, "PROBE", DOMAIN_HINH_HOC),
        "synthesis": lambda: pipeline.stage_semantic_program(DE_THAM_DO, {}, "PROBE", None, domain=DOMAIN_HINH_HOC),
    }
    with dung_ngan_sach(gemini.ApiBudget(max_attempts=MAX_ATTEMPTS_PER_LOGICAL_CALL)), cai_cong_http(cong):
        for s in tang:
            try:
                await cac_goi[s]()
            except Exception:  # noqa: BLE001 — 503 là CHỦ Ý; chỉ đếm số request
                pass
    return {s: dem[s] for s in tang}


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


# ── Khớp dữ kiện theo TOKEN, không theo chuỗi con ──────────────────────────
#
# `PHOTO_PROBLEM_ACCEPTANCE_SCORER_CORRECTION` (2026-09-14). Bản trước khớp chuỗi con
# sau gộp khoảng trắng — `z = 3` lọt trong `z = 30`, `z = 3.1`, `z = 3 + x`; `A′` đọc
# thành nhãn `A`; và một dữ kiện có trong `math_expressions` được tính là ĐỌC ĐÚNG dù
# văn bản — thứ DUY NHẤT đi xuống tầng B — ghi khác. Nay: văn bản tách thành token,
# dữ kiện phải xuất hiện như một BIỂU THỨC HOÀN CHỈNH (hai bên là ranh giới), và chỉ
# văn bản được tính. Không có đại số, không có suy luận: ký hiệu ngoài bảng token ⇒
# `UNVERIFIABLE_AUTOMATICALLY`, chuyển người xem, không tự coi là đúng hay sai.
MATCH, NO_MATCH, UNVERIFIABLE = "MATCH", "NO_MATCH", "UNVERIFIABLE_AUTOMATICALLY"
CONFIRMED, CONTRADICTED, UNVERIFIED = "CONFIRMED", "CONTRADICTED", "UNVERIFIED"
KHONG_RO = "UNKNOWN_PENDING_HUMAN_REVIEW"

#: Tương đương ký hiệu ĐÃ KHAI. Ngoài bảng này hai ký hiệu khác nhau là khác nhau: dấu âm,
#: toán tử, tên điểm, chỉ số và dấu phẩy trên đều được giữ.
TUONG_DUONG_DA_KHAI = {
    "khoảng trắng": "bỏ qua giữa hai token (z=3 ≡ z = 3)",
    "− (U+2212)": "-",
    "′ ’": "'",
    "″": "''",
    "⟂": "⊥",
    "‖ //": "∥",
    "≦ <=": "≤",
    "≧ >=": "≥",
    "!=": "≠",
    "chỉ số dưới ₀–₉": "chữ số liền sau nhãn (A₁ ≡ A1)",
    "số mũ trên ⁰–⁹": "^ + chữ số (x² ≡ x^2)",
    "dấu thập phân ,": ". (3,5 ≡ 3.5)",
    "hoa/thường của TỪ (≥ 2 chữ cái)": "không phân biệt — nhãn điểm VẪN phân biệt",
}
_THAY_KY_TU = str.maketrans({**{chr(0x2080 + i): str(i) for i in range(10)},
                             "−": "-", "′": "'", "’": "'", "″": "''", "⟂": "⊥", "‖": "∥", "≦": "≤", "≧": "≥"})
_MU = dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789"))
_MAU_MU = re.compile("[⁰¹²³⁴⁵⁶⁷⁸⁹]+")
_MAU_TOKEN = re.compile(r"""
    (?P<NHAN>(?<![^\W\d_])(?:[A-Z]\d*'*)+(?![^\W\d_]))
  | (?P<SO>\d+(?:[.,]\d+)?)
  | (?P<CHU>[^\W\d_]+)
  | (?P<TOAN_TU>[=+\-*/^<>≤≥≠⊥∥∈∉⊂⊄∩∪])
  | (?P<MO>[(\[{])
  | (?P<DONG>[)\]}])
  | (?P<CHAM_NOI>(?<=[A-Z0-9'])\.(?=[A-Z]))
  | (?P<NGAT>[.,;:!?…])
  | (?P<KHOANG>\s+)
  | (?P<LA>.)
""", re.VERBOSE)
_TOAN_TU_QUAN_HE = frozenset("=≠⊥∥∈∉<>≤≥⊂⊄")


def tach_token(s: str) -> list[tuple[str, str]]:
    """`(loại, giá trị)`. `S.ABCD` → S · A B C D; `Oxyz`, `Cho` → một TỪ; `x`, `α` → BIẾN."""
    s = unicodedata.normalize("NFC", s).translate(_THAY_KY_TU)
    s = _MAU_MU.sub(lambda m: "^" + "".join(_MU[c] for c in m.group()), s)
    s = s.replace("//", "∥").replace("<=", "≤").replace(">=", "≥").replace("!=", "≠")
    ra: list[tuple[str, str]] = []
    for m in _MAU_TOKEN.finditer(s):
        loai, v = m.lastgroup, m.group()
        if loai == "KHOANG":
            continue
        if loai == "NHAN":
            ra += [("NHAN", n) for n in re.findall(r"[A-Z]\d*'*", v)]
        elif loai == "SO":
            ra.append(("SO", v.replace(",", ".")))
        elif loai == "CHU":
            ra.append(("BIEN", v) if len(v) == 1 else ("CHU", v.casefold()))
        else:
            ra.append((loai, v))
    return ra


def nhan_diem_trong_van_ban(s: str) -> set[str]:
    """Nhãn điểm xuất hiện như KÝ HIỆU: `S.ABCD` → S A B C D; `A′` → `A'`, KHÔNG phải `A`."""
    return {v for loai, v in tach_token(s) if loai == "NHAN"}


def _nhan_chuan(p: str) -> str | None:
    t = tach_token(p)
    return t[0][1] if len(t) == 1 and t[0][0] == "NHAN" else None


def _ben(tok: tuple[str, str] | None, phia: str) -> str:
    """Token kề một lần khớp có phải RANH GIỚI của biểu thức không."""
    if tok is None or tok[0] in ("CHU", "NGAT"):
        return "RANH"
    if tok[0] == "MO":  # `(z = 3)` là ranh giới; `z = 3(x + 1)` thì không
        return "RANH" if phia == "trai" else "NOI"
    if tok[0] == "DONG":
        return "NOI" if phia == "trai" else "RANH"
    return "LA" if tok[0] == "LA" else "NOI"


def khop_trong_token(mau: list[tuple[str, str]], ds: list[tuple[str, str]]) -> str:
    n, co_la = len(mau), False
    for i in range(len(ds) - n + 1):
        if ds[i:i + n] != mau:
            continue
        ben = (_ben(ds[i - 1] if i else None, "trai"), _ben(ds[i + n] if i + n < len(ds) else None, "phai"))
        if ben == ("RANH", "RANH"):
            return MATCH
        co_la = co_la or "LA" in ben
    return UNVERIFIABLE if co_la else NO_MATCH


def khop_du_kien(du_kien: str | list[str], van_ban: str) -> str:
    """Một dữ kiện (hoặc các cách viết đăng ký sẵn) trong MỘT văn bản."""
    ds = tach_token(van_ban)
    ket = []
    for dang in _cac_dang(du_kien):
        mau = tach_token(dang)
        ket.append(UNVERIFIABLE if not mau or any(l == "LA" for l, _ in mau) else khop_trong_token(mau, ds))
    return MATCH if MATCH in ket else UNVERIFIABLE if UNVERIFIABLE in ket else NO_MATCH


def khop_moi_van_ban(du_kien: str | list[str], van_ban: list[str]) -> str:
    """Phải đúng ở MỌI văn bản: bản chuẩn hoá đi xuống tầng B, bản nguyên văn là thứ CER khoá."""
    ket = [khop_du_kien(du_kien, t) for t in van_ban]
    return NO_MATCH if NO_MATCH in ket else UNVERIFIABLE if UNVERIFIABLE in ket else MATCH


def phan_loai_muc_them(muc: str, nguon: str) -> tuple[str, str]:
    """Mục model kê THÊM, xét trên NGUỒN ĐỘC LẬP (ground truth) — không trên trường nào khác của model.

    Bỏ suy luận cũ *"chỉ dùng nhãn và số có trong đề ⇒ không bịa"*: đề có S, A, B, D không
    làm `SA ⊥ BD` đúng. Chỉ hai trường hợp là MÂU THUẪN RÕ — mang nhãn/số nguồn không có,
    hoặc trùng một đoạn nguồn mà khác đúng MỘT con số hay MỘT toán tử quan hệ. Còn lại là
    CHƯA ĐỦ CĂN CỨ, chờ người.
    """
    tk, tn = tach_token(muc), tach_token(nguon)
    if tk and not any(l == "LA" for l, _ in tk) and khop_trong_token(tk, tn) == MATCH:
        return CONFIRMED, "có nguyên biểu thức trong ground truth"
    la = {(l, v) for l, v in tk if l in ("NHAN", "SO")} - {(l, v) for l, v in tn if l in ("NHAN", "SO")}
    if la:
        return CONTRADICTED, "nhãn/số không có trong ground truth: " + ", ".join(sorted(v for _, v in la))
    for i in range(len(tn) - len(tk) + 1):
        khac = [j for j in range(len(tk)) if tn[i + j] != tk[j]]
        if len(khac) == 1:
            a, b = tk[khac[0]], tn[i + khac[0]]
            if a[0] == b[0] == "SO" or (a[0] == b[0] == "TOAN_TU" and {a[1], b[1]} <= _TOAN_TU_QUAN_HE):
                return CONTRADICTED, f"ground truth ghi {b[1]!r} đúng chỗ bản đọc ghi {a[1]!r}"
    return UNVERIFIED, "chưa đủ căn cứ trong ground truth — cần người xem lại"


_NANG_NHE = {CONTRADICTED: 2, UNVERIFIED: 1, CONFIRMED: 0}


def cham_du_kien(cf: dict, x: ie.ImageProblemExtraction, van_ban_nguon: str) -> dict:
    """Dữ kiện quan trọng. CHỈ văn bản được tính — `named_points` là điều kiện THÊM cho nhãn,
    còn `math_expressions`/`named_solids`/`given_relations` chỉ là nơi lấy MỤC THÊM để phân loại."""
    van_ban = list(dict.fromkeys([x.problem_text_verbatim, x.problem_text_normalized]))
    nhan_vb = [nhan_diem_trong_van_ban(t) for t in van_ban]
    nhan_nguon = nhan_diem_trong_van_ban(van_ban_nguon)
    xem_lai: list[dict] = []

    # ── dữ kiện ĐĂNG KÝ ─────────────────────────────────────────────────────
    doc_diem = {_nhan_chuan(p) or _nfc(p) for p in x.named_points}
    cap: dict[str, list[tuple[Any, str]]] = {"point_labels": []}
    for p in cf["point_labels"]:
        n = _nhan_chuan(p)
        tt = UNVERIFIABLE if n is None else MATCH if n in doc_diem and all(n in s for s in nhan_vb) else NO_MATCH
        cap["point_labels"].append((p, tt))
    for nhom in ("formulas", "objects", "relations"):
        cap[nhom] = [(f, khop_moi_van_ban(f, van_ban)) for f in cf[nhom]]
    yeu_cau = cf["request"]
    tt_yeu_cau = None if not yeu_cau.strip() else khop_moi_van_ban(yeu_cau, van_ban)
    if tt_yeu_cau is not None:
        cap["request"] = [(yeu_cau, tt_yeu_cau)]
    for nhom, ds in cap.items():
        xem_lai += [{"group": nhom, "item": f, "status": UNVERIFIABLE,
                     "reason": "ký hiệu ngoài phạm vi bộ chấm hoặc sát ký hiệu lạ — người đối chiếu với ảnh"}
                    for f, tt in ds if tt == UNVERIFIABLE]

    # ── mục THÊM, xét trên ground truth ─────────────────────────────────────
    gt_nhan = {_nhan_chuan(p) or _nfc(p) for p in cf["point_labels"]}
    them: dict[str, list[tuple[str, str, str]]] = {"point_labels": [
        (p, CONFIRMED, "nhãn có trong ground truth") if p in nhan_nguon else
        (p, CONTRADICTED, "nhãn không có trong ground truth") for p in sorted(doc_diem - gt_nhan)]}

    def mau_gt(nhom: str) -> set[tuple]:
        return {tuple(tach_token(d)) for f in cf[nhom] for d in _cac_dang(f)}

    ct_gt, ds_ct = mau_gt("formulas"), []
    for e in x.math_expressions:
        if tuple(tach_token(e.verbatim)) in ct_gt or tuple(tach_token(e.normalized)) in ct_gt:
            continue
        loai, ly_do = max((phan_loai_muc_them(e.verbatim, van_ban_nguon),
                           phan_loai_muc_them(e.normalized, van_ban_nguon)), key=lambda t: _NANG_NHE[t[0]])
        ds_ct.append((_gon(e.verbatim) + " ⇔ " + _gon(e.normalized), loai, ly_do))
    them["formulas"] = ds_ct
    for nhom, doc in (("objects", x.named_solids), ("relations", x.given_relations)):
        gt = mau_gt(nhom)
        them[nhom] = [(_gon(m), *phan_loai_muc_them(m, van_ban_nguon))
                      for m in dict.fromkeys(doc) if tuple(tach_token(m)) not in gt]
    for nhom, ds in them.items():
        them[nhom] = list({m: (m, l, r) for m, l, r in ds}.values())
        xem_lai += [{"group": nhom, "item": m, "status": UNVERIFIED, "reason": r}
                    for m, l, r in them[nhom] if l == UNVERIFIED]

    def ti_le(ds: list[tuple[Any, str]]) -> float | None:
        xet = [tt for _, tt in ds if tt != UNVERIFIABLE]
        return None if not xet else round(sum(tt == MATCH for tt in xet) / len(xet), 4)

    ao_giac = sum(l == CONTRADICTED for ds in them.values() for _, l, _ in ds)
    chua_ro = sum(l == UNVERIFIED for ds in them.values() for _, l, _ in ds)
    khong_kiem_duoc = sum(tt == UNVERIFIABLE for ds in cap.values() for _, tt in ds)
    details: dict = {}
    for nhom in ("point_labels", "formulas", "objects", "relations"):
        details[f"{nhom}_missing"] = [f for f, tt in cap[nhom] if tt == NO_MATCH]
        details[f"{nhom}_unverifiable"] = [f for f, tt in cap[nhom] if tt == UNVERIFIABLE]
        details[f"{nhom}_extra"] = [m for m, _, _ in them[nhom]]
        details[f"{nhom}_confirmed"] = [m for m, l, _ in them[nhom] if l == CONFIRMED]
        details[f"{nhom}_hallucinated"] = [m for m, l, _ in them[nhom] if l == CONTRADICTED]
        details[f"{nhom}_unverified"] = [m for m, l, _ in them[nhom] if l == UNVERIFIED]
    details["fact_status"] = {nhom: [{"item": f, "status": tt} for f, tt in ds] for nhom, ds in cap.items()}
    details["extra_classification"] = {nhom: [{"item": m, "class": l, "reason": r} for m, l, r in ds]
                                       for nhom, ds in them.items()}
    return {
        "POINT_LABEL_ACCURACY": ti_le(cap["point_labels"]),
        "FORMULA_ACCURACY": ti_le(cap["formulas"]),
        "OBJECT_ACCURACY": ti_le(cap["objects"]),
        "RELATION_ACCURACY": ti_le(cap["relations"]),
        "REQUEST_ACCURACY": None if tt_yeu_cau in (None, UNVERIFIABLE) else (1.0 if tt_yeu_cau == MATCH else 0.0),
        "HALLUCINATED_CRITICAL_FACTS": ao_giac,
        "UNVERIFIED_EXTRA_FACTS": chua_ro,
        "UNVERIFIABLE_FACTS": khong_kiem_duoc,
        # Chưa xác minh KHÔNG được làm căn cứ báo 0 — chỉ ra con số khi không còn gì chờ người.
        "SILENT_HALLUCINATION_COUNT": ao_giac if not xem_lai else KHONG_RO,
        "review_items": xem_lai,
        "details": details,
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
    #: `doc_vision_checkpoint(...)` khi tiếp tục từ lượt đọc ảnh đã lưu; `None` = gọi tầng vision.
    vision_checkpoint: dict | None = None
    #: `--synthesis-repair-trace` — opt-in; `False` ⇒ `run_pipeline(observer=None)` như trước.
    synthesis_repair_trace: bool = False
    run_id: str = ""


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


def ma_tu_choi_san_pham() -> frozenset[str]:
    """Mã từ chối `assess_extraction` THẬT SỰ phát — đọc AST, không đọc `REJECTION_MESSAGES`.

    `REJECTION_MESSAGES` có cả `AMBIGUOUS_DIAGRAM` và `INSUFFICIENT_GEOMETRIC_CONSTRAINTS`: có câu
    thông báo, nhưng không nhánh nào của tầng đọc ảnh trả ra. Đăng ký một mã như thế thì C03 không
    bao giờ đạt, và lỗi ấy chỉ lộ ra SAU khi đã tiêu quota.
    """
    cay = ast.parse(textwrap.dedent(inspect.getsource(ie.assess_extraction)))
    return frozenset(n.value for c in ast.walk(cay)
                     if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "tu_choi"
                     for n in ast.walk(c) if isinstance(n, ast.Constant) and isinstance(n.value, str))


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
            ma, hop_le = g.get("expected_rejection_codes"), ma_tu_choi_san_pham()
            if not isinstance(ma, list) or not ma or any(not isinstance(m, str) for m in ma):
                raise LoiDauVao("C03 phải đăng ký TRƯỚC `expected_rejection_codes` — mảng mã không rỗng")
            if set(ma) - hop_le:
                raise LoiDauVao(f"C03.expected_rejection_codes có mã tầng đọc ảnh không phát: "
                                f"{sorted(set(ma) - hop_le)} — hợp lệ: {sorted(hop_le)}")
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


# ── CHECKPOINT ĐỌC ẢNH — tiếp tục tầng B từ một lượt vision THẬT đã lưu ─────────
class LoiCheckpoint(LoiDauVao):
    """Checkpoint không chứng minh được nguồn gốc ⇒ dừng TRƯỚC mọi request, nêu đúng trường."""

    code = "CHECKPOINT_PROVENANCE_FAILED"

    def __init__(self, truong: str, chi_tiet: str) -> None:
        self.truong = truong
        super().__init__(f"{self.code}: {truong}: {chi_tiet}")


def doc_vision_checkpoint(p: Path, ca: CaDaChuan, gt_path: Path) -> dict:
    """Đọc + kiểm một checkpoint đọc ảnh. Trả `result` (ExtractionResult dựng lại) · `provenance` · `prior_usage`.

    Không tin nhãn nào của checkpoint mà dựng lại được từ mã hiện tại: bản ghi qua lại Pydantic
    ĐẦY ĐỦ, phán quyết tính lại bằng `assess_extraction` và phải TRÙNG phán quyết đã lưu — nên
    một checkpoint bị sửa tay (vd thay văn bản bằng ground truth) không lọt qua được.
    """
    try:
        tho = p.read_bytes()
        cp = json.loads(tho)
    except (OSError, ValueError) as err:
        raise LoiCheckpoint("file", f"không đọc được checkpoint ({type(err).__name__})")
    if not isinstance(cp, dict):
        raise LoiCheckpoint("file", "checkpoint phải là object JSON")
    dt = danh_tinh_mo_hinh()
    mong = [
        ("VISION_HTTP_STATUS", 200),
        ("VISION_HTTP_REQUESTS", 1),
        ("RETRIES", 0),
        ("JSON_PARSE_RESULT", "PASS"),
        ("PYDANTIC_VALIDATION_RESULT", "PASS"),
        ("VISION_RESULT", "PASS"),
        ("VISION_MODEL", dt["MODEL_ID"]),
        ("PROMPT_SHA256", dt["PROMPT_SHA256"]),
        ("FULL_SCHEMA_SHA256", ie.VISION_RESPONSE_SCHEMA_SHA256),
        ("TRANSPORT_SCHEMA_SHA256", ie.VISION_TRANSPORT_SCHEMA_SHA256),
        ("VISION_SCHEMA_IDENTITY", ie.VISION_SCHEMA_IDENTITY),
        (f"{ca.case_id.lower()}_sha256_at_request", ca.mo_ta_anh["IMAGE_SHA256"]),
        ("normalized_image_sha256", ca.anh.sha256),
    ]
    for truong, gia_tri in mong:
        if truong not in cp:
            raise LoiCheckpoint(truong, "thiếu trường bắt buộc")
        if type(cp[truong]) is not type(gia_tri) or cp[truong] != gia_tri:
            raise LoiCheckpoint(truong, f"lệch — checkpoint {str(cp[truong])[:24]!r} ≠ hiện tại {str(gia_tri)[:24]!r}")

    gt_tep = _sha(gt_path.read_bytes())
    try:
        gt_khai = json.loads(gt_path.read_text(encoding="utf-8")).get("derived_from_ground_truth_sha256")
    except (OSError, ValueError, AttributeError):
        gt_khai = None
    gt_cp = cp.get("gt_file_sha256_at_request")
    if gt_cp is None:
        raise LoiCheckpoint("gt_file_sha256_at_request", "thiếu trường bắt buộc")
    if gt_cp == gt_tep:
        rang_buoc_gt = "DIRECT"
    elif isinstance(gt_khai, str) and gt_cp == gt_khai:
        rang_buoc_gt = "DERIVED_FROM_DECLARED"
    else:
        raise LoiCheckpoint("gt_file_sha256_at_request",
                            "không khớp tệp --ground-truth, cũng không khớp `derived_from_ground_truth_sha256` nó khai")

    ex = cp.get("extraction")
    if not isinstance(ex, dict):
        raise LoiCheckpoint("extraction", "thiếu hoặc không phải object")
    try:
        x = ie.parse_extraction(json.dumps(ex, ensure_ascii=False))
    except ie.VisionContractError as err:
        raise LoiCheckpoint("extraction", f"không qua Pydantic ĐẦY ĐỦ hiện tại ({err.code}): {str(err)[:160]}")
    if x.model_dump() != ex:
        raise LoiCheckpoint("extraction", "bản ghi đổi khi thẩm định lại — không phải đầu ra đã chuẩn hoá")
    a = ie.assess_extraction(x)
    if "assessment" not in cp:
        raise LoiCheckpoint("assessment", "thiếu trường bắt buộc")
    if cp["assessment"] != a.to_dict():
        raise LoiCheckpoint("assessment", "phán quyết lưu trong checkpoint KHÁC phán quyết tất định dựng lại từ bản ghi")

    truoc = chi_so_token(cp.get("usage_metadata"))
    return {
        "result": ie.ExtractionResult(x, a, ca.anh, ie.vision_identity(None), cached=False),
        "prior_usage": truoc,
        "provenance": {
            "CHECKPOINT_PROVENANCE": "PASS",
            "CHECKPOINT_FILE_NAME": p.name,
            "CHECKPOINT_FILE_SHA256": _sha(tho),
            "CHECKPOINT_EXTRACTION_SHA256": _sha(ie.canonical_json_bytes(ex)),
            "CHECKPOINT_EXTRACTION_CANONICALIZATION": "image_extraction.canonical_json_bytes",
            "CHECKPOINT_WAVE": cp.get("wave"),
            "CHECKPOINT_GIT_HEAD": cp.get("git_head"),
            "CHECKPOINT_STARTED_AT": cp.get("started_at"),
            "GROUND_TRUTH_BINDING": rang_buoc_gt,
            "VERIFIED_FIELDS": [t for t, _ in mong] + ["gt_file_sha256_at_request", "extraction", "assessment"],
            "EXTRACTION_REVALIDATED": "ImageProblemExtraction.model_validate — Pydantic đầy đủ hiện tại",
            "ASSESSMENT_RECOMPUTED_EQUALS_STORED": True,
            "PRIOR_VISION_USAGE": truoc,
        },
    }


_DAU_DE, _CUOI_DE = 'Đề bài:\n"""\n', '\n"""'


def van_ban_trong_than_analyze(tin: Any) -> str | None:
    """Văn bản đề ĐÚNG như lượt analyze gửi đi (`stage_semantic_analyze` bọc `Đề bài:\\n\"\"\"…\"\"\"`)."""
    if (isinstance(tin, str) and tin.startswith(_DAU_DE) and tin.endswith(_CUOI_DE)
            and len(tin) >= len(_DAU_DE) + len(_CUOI_DE)):
        return tin[len(_DAU_DE):len(tin) - len(_CUOI_DE)]
    return None


def kiem_ngang_bang_payload(van_ban_xem_lai: str, van_ban_xac_nhan: str, than_analyze: list[str]) -> dict:
    """Băm bản xem lại · bản xác nhận · văn bản trong MỖI request analyze. Ngang bằng ⇔ mọi payload = bản xác nhận."""
    payload = [van_ban_trong_than_analyze(t) for t in than_analyze]
    bam_payload = [None if v is None else _sha(v) for v in payload]
    bam_xn = _sha(van_ban_xac_nhan)
    return {
        "REVIEW_TEXT_SHA256": _sha(van_ban_xem_lai),
        "CONFIRMED_TEXT_SHA256": bam_xn,
        "ANALYZE_PAYLOAD_TEXT_SHA256": bam_payload,
        "REVIEW_EDITED": van_ban_xac_nhan != van_ban_xem_lai,
        "REVIEW_PAYLOAD_PARITY": bool(bam_payload) and all(h == bam_xn for h in bam_payload),
    }


def phan_loai_loi_tang_b(loi: BaseException | None, env: dict | None, cong: CongHttp, cid: str) -> str | None:
    """Tên lỗi TẦNG ĐẦU TIÊN hỏng. Lỗi provider không bao giờ là lời từ chối an toàn của đề."""
    ban = [r for r in cong.records if r["case_id"] == cid and r["stage"] in STAGES_TANG_B]
    if isinstance(loi, gemini.BudgetExceeded):
        return "HTTP_BUDGET_EXCEEDED"
    if loi is not None:
        hong = next((r for r in reversed(ban) if r.get("sent") and (
            r.get("error") or not 200 <= (r.get("http_status") or 0) < 300)), None)
        tang = (hong or (ban[-1] if ban else {"stage": "analyze"}))["stage"]
        return f"{tang.upper()}_PROVIDER_ERROR"
    if env is None or env.get("status") == "ok":
        return None
    if env.get("stage_reached") == "semantic_analyze":
        return "ANALYZE_OUTPUT_INVALID"
    if env.get("stage_reached") == "semantic_program":
        n = sum(1 for r in ban if r.get("sent") and r["stage"] == "synthesis")
        return "SYNTHESIS_REPAIR_EXHAUSTED" if n >= pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS else "SYNTHESIS_OUTPUT_INVALID"
    return f"DOWNSTREAM_REJECTED_AT_{str(env.get('stage_reached')).upper()}"


def tong_hop_token(records: list[dict]) -> dict:
    """Token THEO TỪNG REQUEST đã gửi và cộng theo tầng — chỉ số đếm."""
    theo_req = [{k: r.get(k) for k in ("provider_call_number", "case_id", "stage", "logical_call", "attempt",
                                        "http_status", "latency_ms", "usage_metadata")}
                for r in records if r.get("sent")]
    theo_tang = {}
    for s in STAGES:
        ds = [x for x in theo_req if x["stage"] == s]
        theo_tang[s] = {"requests": len(ds), "requests_with_usage": sum(1 for x in ds if x["usage_metadata"]),
                        **{k: sum((x["usage_metadata"] or {}).get(k, 0) for x in ds) for k in TRUONG_TOKEN_SO}}
    return {"TOKENS_BY_REQUEST": theo_req, "TOKENS_BY_STAGE": theo_tang}


def token_checkpoint(cp: dict, token: dict) -> dict:
    truoc = (cp.get("prior_usage") or {}).get("totalTokenCount")
    a = token["TOKENS_BY_STAGE"]["analyze"]["totalTokenCount"]
    s = token["TOKENS_BY_STAGE"]["synthesis"]["totalTokenCount"]
    return {
        "PRIOR_VISION_TOKENS": truoc,
        "NEW_ANALYZE_TOKENS": a,
        "NEW_SYNTHESIS_TOKENS": s,
        "NEW_DOWNSTREAM_TOKENS": a + s,
        "COMPOSITE_PIPELINE_TOKENS": None if truoc is None else truoc + a + s,
        "REFERENCE_VISION_TOKENS_NOT_RESPENT": truoc,
        "TOKEN_NOTE": ("PRIOR_VISION_TOKENS lấy từ checkpoint (lượt trước). REFERENCE_VISION_TOKENS_NOT_RESPENT "
                       "là số token checkpoint giúp không phải tiêu lại TRONG CA NÀY — không phải mức tiết "
                       "kiệm bảo đảm cho mọi lượt."),
    }


# ── QUAN TRẮC VÒNG SỬA SYNTHESIS (opt-in `--synthesis-repair-trace`) ─────────────
class QuanTracVongSua:
    """Observer THỤ ĐỘNG cho `run_pipeline(observer=…)` — một thực thể MỖI ca, không trạng thái chung.

    Chỉ GOM bốn loại sự kiện pipeline vốn phát (`_emit`, bất biến #22). Không trả gì và không bao giờ
    ném: một observer ném lỗi sẽ làm `_emit` phá pipeline — tức đổi hành vi. Đầu ra thô của mô hình
    chỉ nằm trong bộ nhớ của thực thể này; trace chỉ lấy băm.
    """

    SU_KIEN = ("semantic_contract", "semantic_program_candidate", "semantic_program_attempt", "semantic_route")

    def __init__(self) -> None:
        self.su_kien: list[tuple[str, dict]] = []
        self.loi_quan_trac = 0

    def emit(self, event_type: str, data: dict) -> None:
        try:
            if event_type in self.SU_KIEN:
                self.su_kien.append((event_type, dict(data)))
        except Exception:  # noqa: BLE001 — quan trắc không bao giờ được phá pipeline
            self.loi_quan_trac += 1


def lien_ket_sua(q: QuanTracVongSua) -> list[tuple[int, int]]:
    """`(lượt bị loại, lượt sửa nó)` từ sự kiện: lượt n bị loại, lời từ chối sửa được, và CÓ ứng viên n+1."""
    ung = {d["n"] for t, d in q.su_kien if t == "semantic_program_candidate"}
    return [(d["n"], d["n"] + 1) for t, d in q.su_kien
            if t == "semantic_program_attempt" and d.get("repairable", True) and d["n"] + 1 in ung]


_MAU_TRICH = re.compile(r"'[^']*'")
_MAU_SO = re.compile(r"\d+")


def _ma_khuon(thong_diep: str) -> str:
    """Mã ổn định cho lời nhắn KHÔNG có mã cấu trúc: băm KHUÔN câu (tên trong '…' và chữ số đã che)."""
    khuon = _MAU_SO.sub("#", _MAU_TRICH.sub("'…'", thong_diep or ""))
    return hashlib.sha256(khuon.encode("utf-8")).hexdigest()[:10].upper()


def phan_loai_ung_vien(raw: Any, contract: Any, *, la_luot_cuoi: bool = False) -> dict:
    """Chạy LẠI đúng các cổng tất định của vòng sửa, ĐÚNG thứ tự `stage_semantic_program`, trên một ứng viên.

    Trả `phase` · `code` · `detail_codes` · `message` — lời nhắn mà pipeline dựng cho CÙNG cổng ấy. Runner
    so `message` với lời nhắn pipeline thật sự phát: trùng ⇒ phân loại đã kiểm; lệch ⇒ khuôn lời nhắn trong
    pipeline đã đổi, và phân loại rơi về sự kiện, không đoán. `phase = None` ⇒ qua mọi cổng của vòng sửa.
    `la_luot_cuoi`: ở lượt cuối pipeline KHÔNG từ chối vì thẩm định tĩnh hay grounding sửa được.
    """
    from pydantic import ValidationError

    from app.simulation.semantic_program import validator as V
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.grounding_gate import check_grounding
    from app.simulation.semantic_program.ir_static_check import kiem_tinh

    def kq(phase, code, message, chi_tiet=()):
        return {"phase": phase, "code": code, "detail_codes": list(chi_tiet), "message": message}

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as e:
        return kq("JSON_PARSE", "JSON_DECODE_ERROR", f"JSON không parse được ({e})")
    if not isinstance(payload, dict):
        return kq("JSON_PARSE", "JSON_NOT_OBJECT",
                  f"đầu ra không phải một đối tượng JSON (nhận {type(payload).__name__})")
    val = V.validate_semantic_program(payload)
    if not val.ok:
        if V._khoa_bi_bo_im_lang(payload):
            return kq("PROGRAM_SCHEMA", "SCHEMA_SILENTLY_DROPPED_KEY", val.error)
        try:
            SemanticProgramSpec.model_validate(payload)
        except ValidationError as e:
            loai = [f"SCHEMA_{str(x.get('type', 'unknown')).upper()}" for x in e.errors()]
            return kq("PROGRAM_SCHEMA", loai[0], val.error, loai)
        return kq("PROGRAM_TYPE_CHECK", f"TYPE_CHECK_{_ma_khuon(val.error)}", val.error)
    t = kiem_tinh(val.spec)
    if not t.ok and not la_luot_cuoi:
        return kq("IR_STATIC_CHECK", t.issues[0].error_code, "chương trình không thực thi được — " + t.phan_hoi(),
                  [i.error_code for i in t.issues])
    if contract is not None:
        g = check_grounding(contract, val.spec)
        if not g.ok and g.error_code in pipeline.KHONG_DUOC_SUA:
            return kq("GROUNDING_GATE", g.error_code, f"[{g.error_code}] " + "; ".join(g.unresolved[:4]),
                      [g.error_code])
        if not g.ok and not la_luot_cuoi:
            return kq("GROUNDING_GATE", g.error_code, "xuất xứ dữ liệu chưa đủ — " + "; ".join(g.unresolved[:4]),
                      [g.error_code])
    return kq(None, None, None)


def _phan_loai_tu_su_kien(ev: dict) -> tuple[str, str, list[str]]:
    """Dự phòng khi phép chạy lại không tái hiện được lời nhắn: đọc `gate` và mã in sẵn trong lời nhắn."""
    m = str(ev.get("message") or "")
    if ev.get("gate") == "ir_static":
        ma = re.findall(r"#\d+ ([A-Z_]+):", m)
        return "IR_STATIC_CHECK", (ma[0] if ma else "IR_STATIC_UNCLASSIFIED"), ma
    if ev.get("gate") == "grounding":
        ma = re.match(r"\[([A-Z_]+)\]", m)
        return "GROUNDING_GATE", (ma.group(1) if ma else "GROUNDING_UNCLASSIFIED"), []
    if m.startswith("JSON không parse được"):
        return "JSON_PARSE", "JSON_DECODE_ERROR", []
    if m.startswith("đầu ra không phải một đối tượng JSON"):
        return "JSON_PARSE", "JSON_NOT_OBJECT", []
    if m.startswith("Lỗi cú pháp schema"):
        return "PROGRAM_SCHEMA", "SCHEMA_UNCLASSIFIED", []
    return "PROGRAM_TYPE_CHECK", f"TYPE_CHECK_{_ma_khuon(m)}", []


def _tom_tat_che(khu: BoKhuBiMat, s: Any) -> str | None:
    """Che bí mật TRƯỚC rồi mới cắt — cắt trước có thể để lại nửa khoá ở mép."""
    return None if s is None else khu.chuoi(str(s))[:TOM_TAT_TOI_DA]


def _duy_nhat(ds: list[str]) -> list[str]:
    return list(dict.fromkeys(x for x in ds if x))


def dung_trace_vong_sua(q: QuanTracVongSua, cong: CongHttp, cid: str, run_id: str, van_ban_de: str,
                        khu: BoKhuBiMat) -> dict:
    """Trace vòng sửa synthesis của MỘT ca: sự kiện observer ⨝ bản ghi cổng HTTP. Chỉ băm, mã, số đếm."""
    from app.simulation.semantic_program.analyze_contract import build_request_contract

    ban_ghi = [r for r in cong.records if r["case_id"] == cid and r["stage"] == "synthesis"]
    da_gui = [r for r in ban_ghi if r.get("sent")]
    van_ban_yc = cong.yeu_cau_synthesis.get(cid, [])
    ung_vien = {d["n"]: d.get("raw") for t, d in q.su_kien if t == "semantic_program_candidate"}
    tu_choi = {d["n"]: d for t, d in q.su_kien if t == "semantic_program_attempt"}
    route = next((d for t, d in reversed(q.su_kien) if t == "semantic_route"), None)
    su_kien_hd = next((d for t, d in q.su_kien if t == "semantic_contract"), None)

    contract, hd_khop = None, None
    tra_loi = [x for x in cong.phan_hoi_analyze.get(cid, []) if x]
    if tra_loi:
        try:
            contract = build_request_contract(json.loads(tra_loi[-1]), problem_text=van_ban_de, domain=DOMAIN_HINH_HOC)
        except Exception:  # noqa: BLE001 — không dựng lại được thì phân loại rơi về sự kiện
            contract = None
    if contract is not None and su_kien_hd is not None:
        hd_khop = (len(contract.input_facts) == su_kien_hd.get("so_fact")
                   and [{"kind": o.kind, "container": o.container, "witness": o.witness}
                        for o in contract.obligations] == su_kien_hd.get("obligations"))

    tran = pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS
    luot: list[dict] = []
    for i, r in enumerate(ban_ghi):
        u = r.get("usage_metadata") or {}
        a: dict = {
            "trace_version": TRACE_VERSION, "run_id": run_id, "case_id": cid, "stage": "synthesis",
            "attempt_index": i, "logical_call": r.get("logical_call"), "attempt": r.get("attempt"),
            "http_status": r.get("http_status"), "latency_ms": r.get("latency_ms"),
            "result": None, "synthesis_loop_verdict": None,
            "rejection_phase": None, "rejection_code": None, "rejection_summary_redacted": None,
            "classification_source": None, "classification_matches_emitted_message": None,
            "candidate_sha256": None, "candidate_byte_count": None, "candidate_json_canonical_sha256": None,
            "feedback_sha256": None, "feedback_codes": [], "feedback_delivered_in_next_request": None,
            "repair_prompt_sha256": None, "repair_attempted": False,
            "repaired_by_logical_call": None, "repairs_logical_call": None,
            "usage": {k: u.get(k) for k in ("promptTokenCount", "candidatesTokenCount", "thoughtsTokenCount",
                                            "cachedContentTokenCount", "totalTokenCount")},
        }
        if not r.get("sent"):
            a.update(result="PROVIDER_ERROR", synthesis_loop_verdict="NOT_REACHED", rejection_phase="HTTP_GATE",
                     rejection_code=f"HTTP_GATE_{r.get('block_reason')}", classification_source="HTTP_GATE_RECORD")
        elif r.get("error") or not 200 <= (r.get("http_status") or 0) < 300:
            a.update(result="PROVIDER_ERROR", synthesis_loop_verdict="NOT_REACHED", rejection_phase="PROVIDER",
                     rejection_code=(f"PROVIDER_HTTP_{r['http_status']}" if r.get("http_status")
                                     else "PROVIDER_TRANSPORT_ERROR"),
                     rejection_summary_redacted=_tom_tat_che(khu, r.get("error") or f"HTTP {r.get('http_status')}"),
                     classification_source="HTTP_GATE_RECORD")
        elif (n := da_gui.index(r)) not in ung_vien or not isinstance(ung_vien[n], str):
            a.update(result="PROVIDER_ERROR", synthesis_loop_verdict="NOT_REACHED", rejection_phase="PROVIDER",
                     rejection_code="PROVIDER_EMPTY_CONTENT", classification_source="HTTP_GATE_RECORD")
        else:
            tho = ung_vien[n].encode("utf-8")
            a.update(candidate_sha256=_sha(tho), candidate_byte_count=len(tho))
            try:
                p = json.loads(tho)
                if isinstance(p, dict):
                    a["candidate_json_canonical_sha256"] = _sha(
                        json.dumps(p, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
            except ValueError:
                pass
            if n in tu_choi:
                ev = tu_choi[n]
                thong_diep = str(ev.get("message") or "")
                pl = phan_loai_ung_vien(ung_vien[n], contract, la_luot_cuoi=n == tran - 1)
                khop = pl["phase"] is not None and pl["message"] == thong_diep
                if khop:
                    phase, code, chi_tiet, nguon = pl["phase"], pl["code"], pl["detail_codes"], "RECOMPUTED_LOOP_GATES"
                else:
                    (phase, code, chi_tiet), nguon = _phan_loai_tu_su_kien(ev), "EMITTED_EVENT_ONLY"
                sua_duoc = ev.get("repairable", True) is not False
                a.update(result="REJECTED",
                         synthesis_loop_verdict="REJECTED_REPAIRABLE" if sua_duoc else "REJECTED_NOT_REPAIRABLE",
                         rejection_phase=phase, rejection_code=code,
                         rejection_summary_redacted=_tom_tat_che(khu, thong_diep),
                         classification_source=nguon, classification_matches_emitted_message=khop)
                ke = ban_ghi[i + 1] if sua_duoc and i + 1 < len(ban_ghi) else None
                if ke is not None:
                    tin = van_ban_yc[da_gui.index(ke)] if ke.get("sent") and da_gui.index(ke) < len(van_ban_yc) else ""
                    a.update(repair_attempted=True, repaired_by_logical_call=ke.get("logical_call"),
                             feedback_sha256=_sha(thong_diep), feedback_codes=_duy_nhat([code, *chi_tiet]),
                             feedback_delivered_in_next_request=bool(thong_diep) and thong_diep in tin,
                             repair_prompt_sha256=_sha(tin) if tin else None)
            else:
                # Qua mọi cổng của vòng sửa ⇒ số phận do route quyết; route không bao giờ gửi đi sửa.
                a["synthesis_loop_verdict"] = "PASSED"
                if route is not None and route.get("servable"):
                    a.update(result="ACCEPTED", classification_source="SEMANTIC_ROUTE_EVENT")
                else:
                    st = (route or {}).get("stage_reached")
                    a.update(result="REJECTED", rejection_phase=f"ROUTE_{str(st).upper()}",
                             rejection_code=(route or {}).get("error_code") or "ROUTE_NOT_SERVED",
                             rejection_summary_redacted=_tom_tat_che(khu, (route or {}).get("reason") or ""),
                             classification_source="SEMANTIC_ROUTE_EVENT")
        luot.append(a)
    for a in luot:
        if a["repaired_by_logical_call"] is not None:
            for b in luot:
                if b["logical_call"] == a["repaired_by_logical_call"]:
                    b["repairs_logical_call"] = a["logical_call"]
    lien_ket = [{"rejected_logical_call": a["logical_call"], "repaired_by_logical_call": a["repaired_by_logical_call"],
                 "feedback_sha256": a["feedback_sha256"]} for a in luot if a["repair_attempted"]]
    khong_nhan = [a for a in luot if a["result"] != "ACCEPTED"]
    return {
        "trace_version": TRACE_VERSION, "run_id": run_id, "case_id": cid, "stage": "synthesis",
        "max_semantic_program_attempts": tran,
        "attempts": luot,
        "links": lien_ket,
        "summary": {
            "attempt_count": len(luot),
            "accepted_logical_call": next((a["logical_call"] for a in luot if a["result"] == "ACCEPTED"), None),
            "rejected": sum(1 for a in luot if a["result"] == "REJECTED"),
            "provider_errors": sum(1 for a in luot if a["result"] == "PROVIDER_ERROR"),
            "repairs": len(lien_ket),
            "every_non_accepted_attempt_has_phase_and_code": all(a["rejection_phase"] and a["rejection_code"]
                                                                 for a in khong_nhan),
            "every_rejection_classification_verified": all(a["classification_matches_emitted_message"] is not False
                                                           for a in luot),
            "contract_recomputed_from_analyze_response": contract is not None,
            "contract_matches_semantic_contract_event": hd_khop,
            "route": None if route is None else {k: route.get(k) for k in (
                "stage_reached", "executable", "servable", "error_code")},
            "observer_errors": q.loi_quan_trac,
            "raw_model_output_stored": False,
            "raw_prompt_stored": False,
        },
        "privacy": f"chỉ SHA-256, mã, số đếm và tóm tắt đã che ≤ {TOM_TAT_TOI_DA} ký tự",
    }


def trace_chuan_hoa(trace: dict) -> str:
    """JSON chính tắc của trace, bỏ các trường đổi theo lượt chạy (`run_id`, `latency_ms`)."""
    def bo(x):
        if isinstance(x, dict):
            return {k: bo(v) for k, v in x.items() if k not in ("run_id", "latency_ms")}
        if isinstance(x, list):
            return [bo(v) for v in x]
        return x
    return json.dumps(bo(trace), sort_keys=True, ensure_ascii=False, separators=(",", ":"))


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
    cp_path = _tuyet_doi(ns.vision_checkpoint, "--vision-checkpoint") if ns.vision_checkpoint else None
    tran = ns.max_http_requests
    if tran is None:
        tran = MAX_HTTP_REQUESTS if cp_path is None else MAX_HTTP_REQUESTS_CHECKPOINT
    if not 1 <= tran <= MAX_HTTP_REQUESTS:
        raise LoiDauVao(f"--max-http-requests phải trong 1…{MAX_HTTP_REQUESTS}")
    if cp_path is not None:
        if ns.case not in ("C01", "C02"):
            raise LoiDauVao("--vision-checkpoint chỉ dùng cho MỘT ca C01 hoặc C02 — không `all`, không C03")
        if ns.dry_run:
            raise LoiDauVao("--vision-checkpoint không đi cùng --dry-run")
        if tran > MAX_HTTP_REQUESTS_CHECKPOINT:
            raise LoiDauVao(f"--max-http-requests không được vượt {MAX_HTTP_REQUESTS_CHECKPOINT} khi tiếp tục "
                            f"từ checkpoint (1 analyze + {pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS} synthesis)")
        if not cp_path.is_file():
            raise LoiCheckpoint("file", "không tồn tại")
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
    cp = None if cp_path is None else doc_vision_checkpoint(cp_path, cases[0], gt_path)
    return CauHinh(cases, gt, gt_path, ra, tran, ns.dry_run, xac_nhan,
                   bool(ns.include_sanitized_images), danh_tinh_mo_hinh(), cp,
                   bool(ns.synthesis_repair_trace))


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
#: PASS · FAIL = model đã trả lời và sai (kể cả sai lược đồ) · ERROR = provider/hạ tầng không cho ra
#: câu trả lời · BLOCKED = cổng của runner chặn request. Mọi thứ khác PASS đều không cho nghiệm thu.
_UU_TIEN = {"PASS": 0, "FAIL": 1, "ERROR": 2, "BLOCKED": 3}


def _loi(kq: dict, trang_thai: str, ly_do: str) -> None:
    kq["fail_reasons"].append(ly_do)
    if _UU_TIEN[trang_thai] > _UU_TIEN[kq["status"]]:
        kq["status"] = trang_thai


def _dong_ca(kq: dict, cong: CongHttp) -> dict:
    cid = kq["case_id"]
    kq["http"] = cong.theo_ca(cid)
    if cid == "C03":
        # Bằng chứng tầng B không được gọi đo ở CỔNG, không lấy từ việc runner tự bỏ qua.
        kq["STAGE_B_HTTP_ATTEMPTS"] = sum(1 for r in cong.records
                                          if r["case_id"] == cid and r["stage"] in ("analyze", "synthesis"))
        if kq["STAGE_B_HTTP_ATTEMPTS"]:
            kq["C03_SAFE_REJECTION"] = False
            _loi(kq, "FAIL", f"C03_REACHED_STAGE_B: {kq['STAGE_B_HTTP_ATTEMPTS']} request")
    if kq["fail_reasons"] and kq["status"] == "PASS":
        kq["status"] = "FAIL"
    kq["result"] = "PASS" if kq["status"] == "PASS" else "FAIL"
    kq["finished_at"] = _bay_gio()
    return kq


async def chay_mot_ca(ca: CaDaChuan, ch: CauHinh, cong: CongHttp, khu: BoKhuBiMat, api_key: str) -> dict:
    cid = ca.case_id
    cong.dat_ca(cid)
    ra = ch.output_dir
    kq: dict = {"case_id": cid, "started_at": _bay_gio(), "status": "PASS", "fail_reasons": []}
    tho: dict = {"case_id": cid, "image": ca.mo_ta_anh, **ch.danh_tinh}
    if cid == "C03":
        # Mặc định KHÔNG an toàn: chỉ một phản hồi hợp lệ mang mã đã đăng ký mới lật được cờ này.
        kq.update(C03_SAFE_REJECTION=False, VISION_SCHEMA_VALID=False, PRODUCT_REJECTED=False,
                  REJECTION_CODE=None, EXPECTED_REJECTION_CODES=ch.ground_truth[cid]["expected_rejection_codes"],
                  ANALYZE_SKIPPED_BY_RUNNER_POLICY=True)

    t0 = time.perf_counter()
    ex = None
    cp = ch.vision_checkpoint
    if cp is not None:
        # KHÔNG có lượt đọc ảnh nào ở đây: bản ghi là của lượt đọc THẬT trước đó, nguồn gốc đã kiểm
        # ở `chuan_bi` (`doc_vision_checkpoint`). Cổng còn chặn tầng vision với trần 0.
        ex = cp["result"]
        tho.update(VISION_SOURCE="CHECKPOINT", vision_checkpoint=cp["provenance"])
        kq["VISION_SOURCE"] = "CHECKPOINT"
    else:
        tho["VISION_SOURCE"] = "PROVIDER"
        try:
            ex = await ie.extract_problem_from_image(ca.anh, api_key, cache_version=None)
        except gemini.BudgetExceeded as err:
            _loi(kq, "BLOCKED", f"VISION_HTTP_BLOCKED: {err}")
        except (ie.VisionUnavailable, ie.VisionBusy) as err:
            _loi(kq, "ERROR", f"VISION_PROVIDER_ERROR: {_chuoi_loi(err)}")
        except ie.VisionContractError as err:
            _loi(kq, "FAIL", f"VISION_CONTRACT_ERROR: {_chuoi_loi(err)}")
        except Exception as err:  # noqa: BLE001 — chưa phân loại thì là ERROR, không bao giờ là từ chối an toàn
            _loi(kq, "ERROR", f"VISION_UNCLASSIFIED_EXCEPTION: {_chuoi_loi(err)}")
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
        ma = kq["EXPECTED_REJECTION_CODES"]
        tu_choi = a.status == "rejected"
        dung_ma = tu_choi and a.rejection_code in ma
        kq.update(VISION_SCHEMA_VALID=True, PRODUCT_REJECTED=tu_choi, REJECTION_CODE=a.rejection_code,
                  C03_SAFE_REJECTION=dung_ma, REJECTED_BEFORE_SCENE=dung_ma,
                  SILENT_HALLUCINATION=0 if tu_choi else 1, EMPTY_SCENE_SHOWN_AS_SUCCESS="NO")
        if not tu_choi:
            _loi(kq, "FAIL", "C03_NOT_REJECTED: tầng đọc ảnh cho qua một ảnh thiếu dữ kiện")
        elif not dung_ma:
            _loi(kq, "FAIL", f"C03_REJECTION_CODE_NOT_REGISTERED: {a.rejection_code} ∉ {ma}")
        return _dong_ca(kq, cong)

    g = ch.ground_truth[cid]
    van_ban_mo_hinh = a.problem_text
    co_ban_xac_nhan = cid in ch.confirmed_text
    van_ban_dung = ch.confirmed_text.get(cid, van_ban_mo_hinh)
    diem = cham_doc_anh(cid, g, x, van_ban_dung)
    kq["vision_scoring"] = diem
    kq["REVIEW_ITEMS"] = len(diem["review_items"])
    kq["SILENT_HALLUCINATION_COUNT"] = diem["SILENT_HALLUCINATION_COUNT"]
    if a.status == "rejected":
        _loi(kq, "FAIL", f"VISION_REJECTED: {a.rejection_code}")
    for ly_do in diem["fail_reasons"]:
        _loi(kq, "FAIL", ly_do)
    # Nhãn của lượt MÁY gửi bản xem lại — không bao giờ là duyệt của người
    # (`HUMAN_CRITICAL_FACT_REVIEW` vẫn PENDING).
    if cp is not None:
        loai_duyet = ("AUTOMATED_CHECKPOINT_REPLAY_WITH_CONFIRMED_TEXT_FILE" if co_ban_xac_nhan
                      else "AUTOMATED_CHECKPOINT_REPLAY")
        nguon_xac_nhan = "CONFIRMED_TEXT_FILE" if co_ban_xac_nhan else loai_duyet
    else:
        # Trước C01_SINGLE_RUN_END_TO_END_WITH_REPAIR_TRACE: không nhãn duyệt, và nguồn xác nhận ghi
        # `HUMAN_EDIT_NONE_MODEL_TEXT` — một chữ HUMAN cho một lượt không có người nào.
        loai_duyet = ("AUTOMATED_SINGLE_RUN_WITH_CONFIRMED_TEXT_FILE" if co_ban_xac_nhan
                      else "AUTOMATED_SINGLE_RUN_UNEDITED")
        nguon_xac_nhan = "CONFIRMED_TEXT_FILE" if co_ban_xac_nhan else "MODEL_TEXT_UNEDITED"
    kq["REVIEW_KIND"] = loai_duyet
    if a.requires_confirmation and not co_ban_xac_nhan:
        # Sản phẩm khoá nút dựng tới khi người học đánh dấu xác nhận; lượt tự động không được đánh dấu
        # thay người. Trước đây chỉ chế độ checkpoint dừng ở đây — lượt nguyên khối đi thẳng vào analyze.
        _loi(kq, "FAIL", "REVIEW_CONFIRMATION_REQUIRED")
    _ghi_json(ra, f"{cid}_CONFIRMED_INPUT.json", {
        "case_id": cid,
        "MODEL_RAW_TEXT": van_ban_mo_hinh,
        "USER_CONFIRMED_TEXT": van_ban_dung,
        "CONFIRMATION_SOURCE": nguon_xac_nhan,
        **({"REVIEW_KIND": loai_duyet} if loai_duyet else {}),
        "EDITED": van_ban_dung != van_ban_mo_hinh,
        "REVIEW_TEXT_SHA256": _sha(van_ban_mo_hinh),
        "CONFIRMED_TEXT_SHA256": _sha(van_ban_dung),
        "TEXT_SHA256_CANONICALIZATION": CHUAN_BAM_VAN_BAN,
        "requires_confirmation": a.requires_confirmation,
        "review_flags": list(a.review_flags),
    }, khu)
    if kq["fail_reasons"]:
        kq["analyze_skipped"] = "VISION_NOT_PASSED — không tiêu quota tầng B"
        return _dong_ca(kq, cong)

    env = None
    loi_b: BaseException | None = None
    quan_trac = QuanTracVongSua() if ch.synthesis_repair_trace else None
    try:
        env = await pipeline.run_pipeline(van_ban_dung, api_key, semantic_route="serve", observer=quan_trac)
    except gemini.BudgetExceeded as err:
        loi_b = err
        _loi(kq, "BLOCKED", f"ANALYZE_OR_SYNTHESIS_HTTP_BLOCKED: {err}")
    except Exception as err:  # noqa: BLE001 — lỗi provider thoát khỏi run_pipeline nguyên dạng
        loi_b = err
        _loi(kq, "ERROR", f"ANALYZE_OR_SYNTHESIS_PROVIDER_ERROR: {_chuoi_loi(err)}")

    than = cong.van_ban_analyze.get(cid, [])
    rao_dung = f'"""\n{van_ban_dung}\n"""'
    rao_mo_hinh = f'"""\n{van_ban_mo_hinh}\n"""'
    kq["USER_EDIT_PAYLOAD_PARITY"] = bool(than) and all(rao_dung in t for t in than) and (
        van_ban_dung == van_ban_mo_hinh or all(rao_mo_hinh not in t for t in than))
    if than and not kq["USER_EDIT_PAYLOAD_PARITY"]:
        _loi(kq, "FAIL", "USER_EDIT_PAYLOAD_PARITY_BROKEN")
    ngang = kiem_ngang_bang_payload(van_ban_mo_hinh, van_ban_dung, than)
    kq.update(ANALYZE_PAYLOAD_TEXT_SHA256=ngang["ANALYZE_PAYLOAD_TEXT_SHA256"],
              REVIEW_PAYLOAD_PARITY=ngang["REVIEW_PAYLOAD_PARITY"])
    if than and not ngang["REVIEW_PAYLOAD_PARITY"]:
        _loi(kq, "FAIL", "REVIEW_PAYLOAD_PARITY_BROKEN")
    kq["DOWNSTREAM_FAILURE_CLASS"] = phan_loai_loi_tang_b(loi_b, env, cong, cid)
    if quan_trac is not None:
        trace = dung_trace_vong_sua(quan_trac, cong, cid, ch.run_id, van_ban_dung, khu)
        _ghi_json(ra, f"{cid}_SYNTHESIS_REPAIR_TRACE.json", trace, khu)
        kq["SYNTHESIS_REPAIR_TRACE_SUMMARY"] = {k: trace["summary"][k] for k in (
            "attempt_count", "accepted_logical_call", "rejected", "provider_errors", "repairs",
            "every_non_accepted_attempt_has_phase_and_code", "every_rejection_classification_verified")}

    ket_analyze: dict = {"case_id": cid, "analyze_input_sha256": _sha(van_ban_dung),
                         "DOWNSTREAM_FAILURE_CLASS": kq["DOWNSTREAM_FAILURE_CLASS"]}
    if env is None:
        ket_analyze["error"] = kq["fail_reasons"][-1]
        _ghi_json(ra, f"{cid}_ANALYZE_RESULT.json", ket_analyze, khu)
        return _dong_ca(kq, cong)
    ket_analyze.update({k: env.get(k) for k in (
        "status", "simulation_id", "stage_reached", "error_code", "failure_category", "learner_reason")})
    _ghi_json(ra, f"{cid}_ANALYZE_RESULT.json", ket_analyze, khu)
    # Envelope NGUYÊN DẠNG (đã khử secret): đủ để phát lại trên trình duyệt và chấm cảnh/đáp số
    # mà không gọi lại provider.
    _ghi_json(ra, f"{cid}_ENVELOPE.json", env, khu)

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
        _loi(kq, "FAIL", f"ANALYZE_NOT_OK: {env.get('error_code')}")
    elif not vat:
        _loi(kq, "FAIL", "EMPTY_SCENE")
    elif khop is False:
        _loi(kq, "FAIL", f"SCENE_KINDS_MISMATCH: {loai} ≠ {sorted(mong)}")
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
            cho = f" · {r['REVIEW_ITEMS']} mục chờ người xem" if r.get("REVIEW_ITEMS") else ""
            kenh.in_(f"  {ca.case_id}: {r['status']}{cho}{chi_tiet}")
            # Mục chờ người KHÔNG dừng lượt: người duyệt xem trên artifact, sau lượt chạy.
            if r["status"] != "PASS":
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
# §7b · DUYỆT THỦ CÔNG — gói cho người, và kiểm bản duyệt người gửi lại
# ══════════════════════════════════════════════════════════════════════════
BAN_DUYET_LOAI = ("HUMAN", "SIMULATED_REVIEW")
NGUOI_DUYET_PHAI_XEM = [
    "facts_missing_or_misread — dữ kiện đăng ký bị thiếu hoặc đọc sai",
    "extra_facts_unverified — quan hệ/biểu thức thêm chưa có căn cứ trong ground truth",
    "model_vs_confirmed_text — khác biệt giữa bản model đọc và bản người dùng sửa",
    "scene — kết quả cảnh nếu đã dựng",
]


def _sha_tep(p: Path) -> str | None:
    return _sha(p.read_bytes()) if p.is_file() else None


def rang_buoc_luot(ra: Path, tom_tat: dict) -> dict:
    """Băm gắn bản duyệt với ĐÚNG lượt — đọc lại từ tệp mỗi lần, không tin số đã ghi."""
    ca = []
    for cid in tom_tat.get("cases_run", []):
        tho = ra / f"{cid}_RAW_EXTRACTION.json"
        try:
            anh = json.loads(tho.read_text(encoding="utf-8"))["image"]["IMAGE_SHA256"]
        except (OSError, ValueError, KeyError, TypeError):
            anh = None
        ca.append({"case_id": cid, "image_sha256": anh, "raw_extraction_sha256": _sha_tep(tho),
                   "confirmed_input_sha256": _sha_tep(ra / f"{cid}_CONFIRMED_INPUT.json")})
    return {"run_id": tom_tat.get("run_id"), "ground_truth_sha256": tom_tat.get("GROUND_TRUTH_SHA256"), "cases": ca}


def _doc_tep(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def goi_duyet(ra: Path, tom_tat: dict, ket: list[dict]) -> dict:
    rb = rang_buoc_luot(ra, tom_tat)
    ca_goi = []
    for r in ket:
        cid, s = r["case_id"], r.get("vision_scoring") or {}
        d, muc = s.get("details") or {}, s.get("review_items") or []
        thieu = [{"group": g, "item": f} for g in ("point_labels", "formulas", "objects", "relations")
                 for f in d.get(f"{g}_missing", [])]
        if s.get("REQUEST_ACCURACY") == 0.0:
            thieu.append({"group": "request", "item": r.get("request")})
        xn, canh = _doc_tep(ra / f"{cid}_CONFIRMED_INPUT.json"), _doc_tep(ra / f"{cid}_SCENE_RESULT.json")
        so_sanh = None
        if xn is not None:
            a, b = xn["MODEL_RAW_TEXT"], xn["USER_CONFIRMED_TEXT"]
            so_sanh = {"EDITED": xn["EDITED"], "MODEL_RAW_TEXT": a, "USER_CONFIRMED_TEXT": b,
                       "diff": [f"{op}: {a[i1:i2]!r} → {b[j1:j2]!r}" for op, i1, i2, j1, j2
                                in difflib.SequenceMatcher(None, a, b).get_opcodes() if op != "equal"]}
        ca_goi.append({
            "case_id": cid,
            "automated_status": r["status"],
            "fail_reasons": r["fail_reasons"],
            "facts_missing_or_misread": thieu,
            "extra_facts_hallucinated": [x for g in (d.get("extra_classification") or {}).values()
                                         for x in g if x["class"] == CONTRADICTED],
            "extra_facts_unverified": [x for x in muc if x["status"] == UNVERIFIED],
            "unverifiable_facts": [x for x in muc if x["status"] == UNVERIFIABLE],
            "model_vs_confirmed_text": so_sanh,
            "scene": None if canh is None else {k: canh.get(k) for k in (
                "scene_object_count", "scene_kinds", "expected_scene_kinds", "scene_kinds_match")},
            **({k: r.get(k) for k in ("REJECTION_CODE", "EXPECTED_REJECTION_CODES", "C03_SAFE_REJECTION")}
               if cid == "C03" else {}),
        })
    return {
        "wave": WAVE,
        "artifact": "HUMAN_REVIEW_PACKET",
        "run_mode": tom_tat.get("run_mode"),
        "AUTOMATED_CHECKS": tom_tat.get("AUTOMATED_CHECKS"),
        "HUMAN_CRITICAL_FACT_REVIEW": "PENDING",
        "reviewer_must_check": NGUOI_DUYET_PHAI_XEM,
        "binding": rb,
        "cases": ca_goi,
        "review_template": {"run_id": rb["run_id"], "ground_truth_sha256": rb["ground_truth_sha256"],
                            "review_kind": "HUMAN", "reviewer": "", "reviewed_at": "", "decision": "PENDING",
                            "notes": "", "cases": [{**c, "decision": "PENDING", "notes": ""} for c in rb["cases"]]},
        "how_to_verify": "run_photo_problem_live.py --verify-review --run-dir <tuyệt đối> --human-review <tuyệt đối>",
        "RULE": "Chỉ NGƯỜI dùng được điền và ký bản duyệt. Thay ảnh, ground truth hay đầu ra model ⇒ bản cũ hết hiệu lực.",
    }


def phan_quyet_duyet(tom_tat: dict, rang_buoc: dict, ban: Any) -> dict:
    """Phán quyết bản duyệt. `PASS` chỉ khi: bản NGƯỜI · lượt provider THẬT · ràng buộc khớp · mọi ca PASS."""
    that = tom_tat.get("run_mode") == "REAL_PROVIDER"
    tu_dong = tom_tat.get("AUTOMATED_CHECKS")
    goc = {"run_id": tom_tat.get("run_id"), "run_mode": tom_tat.get("run_mode"), "AUTOMATED_CHECKS": tu_dong}

    def ket(duyet: str, nghiem_thu: str | None = None, *, rang_buoc_dung: bool = False,
            van_de: list[str] | None = None) -> dict:
        if nghiem_thu is None:
            nghiem_thu = "NOT_RUN" if not that else "FAIL" if tu_dong != "PASS" else "PENDING_HUMAN_REVIEW"
        return {**goc, "BINDING_VALID": rang_buoc_dung, "HUMAN_CRITICAL_FACT_REVIEW": duyet,
                "REAL_PHOTO_ACCEPTANCE": nghiem_thu, "problems": van_de or []}

    if ban is None:
        return ket("PENDING")
    if not isinstance(ban, dict):
        return ket("INVALID_REVIEW", van_de=["bản duyệt không phải object"])
    loi = []
    if ban.get("review_kind") not in BAN_DUYET_LOAI:
        loi.append(f"review_kind phải thuộc {list(BAN_DUYET_LOAI)}")
    elif ban["review_kind"] == "HUMAN" and not that:
        loi.append(f"bản duyệt NGƯỜI chỉ dành cho lượt REAL_PROVIDER — lượt này là {tom_tat.get('run_mode')}")
    if not isinstance(ban.get("reviewer"), str) or not ban["reviewer"].strip():
        loi.append("thiếu reviewer")
    try:
        datetime.fromisoformat(ban.get("reviewed_at"))
    except (TypeError, ValueError):
        loi.append("reviewed_at phải là thời điểm ISO 8601")
    if ban.get("decision") not in ("PASS", "FAIL"):
        loi.append("decision phải là PASS hoặc FAIL")
    ca_ban = ban.get("cases")
    ca_rb = {c["case_id"]: c for c in rang_buoc["cases"]}
    if (not isinstance(ca_ban, list) or not all(isinstance(c, dict) for c in ca_ban)
            or sorted(str(c.get("case_id")) for c in ca_ban) != sorted(ca_rb)
            or any(c.get("decision") not in ("PASS", "FAIL") for c in ca_ban)):
        loi.append(f"cases phải phủ ĐÚNG các ca đã chạy {sorted(ca_rb)}, mỗi ca decision PASS/FAIL")
    if loi:
        return ket("INVALID_REVIEW", van_de=loi)

    lech = [k for k in ("run_id", "ground_truth_sha256") if ban.get(k) != rang_buoc[k]]
    lech += [f"{c['case_id']}.{k}" for c in ca_ban
             for k in ("image_sha256", "raw_extraction_sha256", "confirmed_input_sha256")
             if c.get(k) != ca_rb[c["case_id"]][k]]
    if lech:
        return ket("STALE_REVIEW", van_de=[f"bản duyệt gắn với lượt/tệp KHÁC: {x}" for x in lech])
    if ban["review_kind"] == "SIMULATED_REVIEW":
        return ket("SIMULATED_REVIEW", rang_buoc_dung=True, van_de=["bản duyệt GIẢ — chỉ kiểm cơ chế"])
    if ban["decision"] != "PASS" or any(c["decision"] != "PASS" for c in ca_ban):
        return ket("FAIL", "FAIL", rang_buoc_dung=True)
    dat = tu_dong == "PASS" and tom_tat.get("REAL_PROVIDER_EVIDENCE") == "ESTABLISHED"
    return ket("PASS", "PASS" if dat else "FAIL", rang_buoc_dung=True,
               van_de=[] if dat else ["người duyệt PASS nhưng kiểm tự động hoặc bằng chứng provider chưa đạt"])


def kiem_duyet_cli(ns: argparse.Namespace, kenh: KenhIn) -> int:
    try:
        ra = _tuyet_doi(ns.run_dir, "--run-dir")
        ban = None if not ns.human_review else json.loads(
            _tuyet_doi(ns.human_review, "--human-review").read_text(encoding="utf-8"))
        tom_tat = json.loads((ra / "RUN_SUMMARY.json").read_text(encoding="utf-8"))
        goi = json.loads((ra / "HUMAN_REVIEW_PACKET.json").read_text(encoding="utf-8"))
    except LoiDauVao as err:
        kenh.loi(f"TỪ CHỐI: {err}")
        return EXIT_USAGE
    except (OSError, ValueError) as err:
        kenh.loi(f"không đọc được lượt chạy hoặc bản duyệt: {type(err).__name__}")
        return EXIT_USAGE
    hien_tai = rang_buoc_luot(ra, tom_tat)
    kq = phan_quyet_duyet(tom_tat, hien_tai, ban)
    if hien_tai != goi.get("binding"):
        kq["problems"].append("RUN_ARTIFACTS_CHANGED_AFTER_RUN: tệp của lượt khác lúc đóng gói duyệt")
        if kq["HUMAN_CRITICAL_FACT_REVIEW"] in ("PASS", "SIMULATED_REVIEW"):
            kq.update(HUMAN_CRITICAL_FACT_REVIEW="STALE_REVIEW", BINDING_VALID=False,
                      REAL_PHOTO_ACCEPTANCE="FAIL" if kq["REAL_PHOTO_ACCEPTANCE"] == "PASS" else kq[
                          "REAL_PHOTO_ACCEPTANCE"])
    kenh.in_(json.dumps(kq, ensure_ascii=False, indent=2))
    return EXIT_PASS if (kq["HUMAN_CRITICAL_FACT_REVIEW"], kq["REAL_PHOTO_ACCEPTANCE"]) == ("PASS", "PASS") \
        else EXIT_CASE_FAIL


# ══════════════════════════════════════════════════════════════════════════
# §8 · CLI
# ══════════════════════════════════════════════════════════════════════════
def tao_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="run_photo_problem_live.py", add_help=True)
    ap.add_argument("--case", choices=[*CASE_IDS, "all"])
    ap.add_argument("--input-dir")
    ap.add_argument("--ground-truth")
    ap.add_argument("--output-dir")
    ap.add_argument("--max-http-requests", type=int, default=None,
                    help=f"mặc định {MAX_HTTP_REQUESTS}; {MAX_HTTP_REQUESTS_CHECKPOINT} với --vision-checkpoint")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--vision-checkpoint",
                    help="tiếp tục từ một lượt đọc ảnh THẬT đã lưu; 0 request vision, chỉ tầng B")
    ap.add_argument("--synthesis-repair-trace", action="store_true",
                    help="ghi trace vòng sửa synthesis (opt-in; chỉ băm, mã, số đếm)")
    ap.add_argument("--confirmed-text")
    ap.add_argument("--include-sanitized-images", action="store_true")
    ap.add_argument("--confirm-no-personal-data", action="store_true")
    ap.add_argument("--verify-review", action="store_true",
                    help="kiểm một bản duyệt thủ công với một lượt đã chạy; 0 request")
    ap.add_argument("--run-dir")
    ap.add_argument("--human-review")
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
    if ns.verify_review:
        return kiem_duyet_cli(ns, kenh)
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

    tang_do = STAGES if ch.vision_checkpoint is None else STAGES_TANG_B
    with ChanMangThat() as chan_tham_do:
        so_lan = asyncio.run(do_so_lan_thu_moi_tang(tang_do))
    if so_lan != {s: 1 for s in tang_do} or chan_tham_do.attempts:
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
    cp = ch.vision_checkpoint
    if cp is not None and che_do == "REAL_PROVIDER":
        nguon = "PROVIDER_IMAGE_READ_VIA_VISION_CHECKPOINT"
    for ca in ch.cases:
        ca.mo_ta_anh["SOURCE"] = nguon

    ch.output_dir.mkdir(parents=True, exist_ok=True)
    _ghi_json(ch.output_dir, "GROUND_TRUTH.json",
              json.loads(ch.ground_truth_path.read_text(encoding="utf-8")), khu)
    cong = CongHttp(None, ch.max_http_requests, khu,
                    tran_theo_tang=None if cp is None else dict(TRAN_THEO_TANG_CHECKPOINT),
                    giu_van_ban_tang_b=ch.synthesis_repair_trace)
    # Sinh TRƯỚC lượt chạy: trace từng ca mang cùng `run_id` với RUN_SUMMARY.
    ch.run_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"
    if inner_transport_factory is not None:
        cong.inner = inner_transport_factory(cong)
    elif ch.dry_run:
        cong.inner = TransportGiaGemini(cong, ch.ground_truth)
    else:
        cong.inner = httpx.AsyncHTTPTransport()
    api_key = "DRY_RUN_KHONG_PHAI_KHOA" if ch.dry_run else khoa

    kenh.in_(f"{WAVE} · {che_do} · ca {[c.case_id for c in ch.cases]} · trần HTTP {ch.max_http_requests}"
             f" · vision {'CHECKPOINT' if cp is not None else 'PROVIDER'}")
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
    token = tong_hop_token(cong.records)
    if loi_runner or not ket:
        tu_dong = "ERROR"
    elif len(ket) == len(ch.cases) and all(r["status"] == "PASS" for r in ket):
        tu_dong = "PASS"
    else:
        tu_dong = max((r["status"] for r in ket), key=_UU_TIEN.__getitem__)
    tom_tat = {
        "wave": WAVE,
        "run_id": ch.run_id,
        "run_mode": che_do,
        "SOURCE": nguon,
        **NHAN_KHAI_TRUOC,
        **ch.danh_tinh,
        "GROUND_TRUTH_SHA256": _sha(ch.ground_truth_path.read_bytes()),
        "cases_requested": [c.case_id for c in ch.cases],
        "cases_run": [r["case_id"] for r in ket],
        "cases_not_run": [{"case_id": c, "status": "NOT_RUN_PREVIOUS_CASE_FAILED"} for c in chua_chay],
        "RETRY_POLICY_PROBE": so_lan,
        "RUN_KIND": "SINGLE_RUN" if cp is None else "DOWNSTREAM_FROM_VISION_CHECKPOINT",
        "VISION_SOURCE": "PROVIDER" if cp is None else "CHECKPOINT",
        **({} if cp is None else {
            "SINGLE_RUN_END_TO_END": "NOT_RUN",
            "HTTP_BUDGET_COMPOSITION": (f"checkpoint: 0 vision + 1 analyze + {pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS}"
                                        f" synthesis = {MAX_HTTP_REQUESTS_CHECKPOINT}"),
        }),
        "STAGE_HTTP_CAPS": cong.tran_theo_tang,
        "SYNTHESIS_REPAIR_TRACE": "ENABLED" if ch.synthesis_repair_trace else "DISABLED",
        **({"TRACE_VERSION": TRACE_VERSION} if ch.synthesis_repair_trace else {}),
        "VISION_CHECKPOINT": None if cp is None else cp["provenance"],
        "REVIEW_KIND": next((r["REVIEW_KIND"] for r in ket if r.get("REVIEW_KIND")), None),
        **tong,
        **token,
        **({} if cp is None else token_checkpoint(cp, token)),
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
        "FACT_MATCHING_EQUIVALENCES": TUONG_DUONG_DA_KHAI,
        "REVIEW_ITEMS_TOTAL": sum(r.get("REVIEW_ITEMS", 0) for r in ket),
        "cases": ket,
        # Ba nhãn TÁCH RỜI. Runner không bao giờ tự ghi gì khác PENDING cho người duyệt: test
        # xanh, không thấy số lạ hay model tự khai chắc chắn đều không phải là người đã xem.
        "AUTOMATED_CHECKS": tu_dong,
        "HUMAN_CRITICAL_FACT_REVIEW": "PENDING",
        "REAL_PHOTO_ACCEPTANCE": ("NOT_RUN" if not that
                                  else "NOT_APPLICABLE_VISION_CHECKPOINT" if cp is not None
                                  else "PENDING_HUMAN_REVIEW" if tu_dong == "PASS" else "FAIL"),
        "ACCEPTANCE": "PENDING_HUMAN_REVIEW" if tu_dong == "PASS" else "FAIL",
    }
    _ghi_json(ch.output_dir, "PROVIDER_CALLS.json", {"records": cong.records, **tong}, khu)
    _ghi_json(ch.output_dir, "RUN_SUMMARY.json", tom_tat, khu)
    _ghi_json(ch.output_dir, "HUMAN_REVIEW_PACKET.json", goi_duyet(ch.output_dir, tom_tat, ket), khu)
    kenh.in_(f"HTTP gửi {tong['HTTP_REQUESTS_SENT']}/{ch.max_http_requests} · chặn {tong['HTTP_REQUESTS_BLOCKED']} "
             f"· vision {tong['VISION_HTTP_REQUESTS']} · analyze {tong['ANALYZE_HTTP_REQUESTS']} "
             f"· synthesis {tong['SYNTHESIS_HTTP_REQUESTS']} · retry {tong['RETRIES']} "
             f"· tự động {tu_dong} · người duyệt PENDING · nghiệm thu {tom_tat['ACCEPTANCE']}")
    kenh.in_(f"→ {ch.output_dir / 'RUN_SUMMARY.json'}")
    # 0 = kiểm TỰ ĐỘNG đạt. Nghiệm thu vẫn chờ người — xem `--verify-review`.
    return EXIT_PASS if tu_dong == "PASS" else EXIT_CASE_FAIL


if __name__ == "__main__":
    sys.exit(main())
