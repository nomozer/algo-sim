# -*- coding: utf-8 -*-
"""Kiểm tra cấu hình và gửi MỘT thư thử qua kênh email giao dịch của Axo (Resend).

An toàn:
- KHÔNG BAO GIỜ in khoá API, nội dung thư hay token; chỉ in trạng thái và mã lỗi máy.
- Mặc định chỉ đọc (`--check`). Gửi thư thật CHỈ khi truyền tường minh `--send --to <địa chỉ>`.
- `--status <id>` hỏi Resend trạng thái giao thư của một email đã gửi (yêu cầu khóa `Full access`; khóa `Sending access` được xử lý êm và hướng dẫn kiểm tra trên Resend Dashboard, không nâng quyền khóa).

Cách dùng (trong thư mục backend/, hoặc `docker compose exec backend python scripts/email_smoke_test.py …`):
    python scripts/email_smoke_test.py --check
    python scripts/email_smoke_test.py --send --to ban@vidu.vn
    python scripts/email_smoke_test.py --status <email-id>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _load_env(env_file: str | None) -> None:
    from dotenv import load_dotenv

    load_dotenv(Path(env_file) if env_file else BACKEND_ROOT / ".env", override=False)


def _check() -> dict:
    from app.accounts import mailer

    state = mailer.readiness()
    state["resendApiKeyPresent"] = bool(os.getenv("RESEND_API_KEY", "").strip())
    return state


def _send(to: str) -> dict:
    from app.accounts import mailer

    if not mailer.email_available():
        return {"status": "unavailable", "readiness": _check()}
    app_url = mailer.public_app_url() or ""
    text = (
        "Đây là thư kiểm tra kênh gửi email của Axo. Không cần trả lời thư này.\n\n"
        f"Ứng dụng: {app_url}"
    )
    html = (
        "<p>Đây là thư kiểm tra kênh gửi email của Axo. Không cần trả lời thư này.</p>"
        f"<p>Ứng dụng: {app_url}</p>"
    )
    msg = mailer.OutgoingEmail(
        to=to.strip(),
        subject="Kiểm tra gửi email Axo",
        html=html,
        text=text,
        category="smoke_test",
        idempotency_key=f"axo-smoke-{uuid.uuid4().hex}",
    )
    result = mailer.send_email(msg)
    out = {
        "status": result.status,
        "providerId": result.provider_id,
        "reason": result.reason,
        "recipientDomain": to.rsplit("@", 1)[-1].lower() if "@" in to else None,
        "deliveryVerified": False,
    }
    if result.status == "accepted":
        out["deliveryNote"] = (
            "Trạng thái 'accepted' chỉ xác nhận Resend đã tiếp nhận yêu cầu gửi, không đồng nghĩa "
            "người nhận đã nhận thư; kiểm tra trạng thái giao thư thực tế trên Resend Dashboard (mục Emails)."
        )
    return out


def _status(email_id: str) -> dict:
    import httpx

    key = os.getenv("RESEND_API_KEY", "").strip()
    if not key:
        return {"status": "unavailable", "reason": "RESEND_API_KEY_MISSING"}
    try:
        resp = httpx.get(
            f"https://api.resend.com/emails/{email_id.strip()}",
            headers={"Authorization": f"Bearer {key}", "User-Agent": "axo-backend"},
            timeout=httpx.Timeout(10.0, connect=5.0),
        )
    except httpx.HTTPError:
        return {"status": "failed", "reason": "PROVIDER_NETWORK_ERROR"}
    if resp.status_code in (401, 403):
        err_name = ""
        err_msg = ""
        try:
            err_body = resp.json()
            if isinstance(err_body, dict):
                err_name = str(err_body.get("name") or "").strip().lower()
                err_msg = str(err_body.get("message") or "").strip().lower()
        except ValueError:
            pass
        if err_name == "restricted_api_key" or "restricted to only send" in err_msg or "sending access" in err_msg:
            return {
                "status": "unsupported_by_key_scope",
                "reason": "SENDING_ACCESS_KEY_ONLY",
                "httpStatus": resp.status_code,
                "message": (
                    "Khóa Resend chỉ có quyền Sending access (đúng nguyên tắc tối thiểu đặc quyền) "
                    "nên không gọi được GET /emails/{id}. Không nâng khóa lên Full access; kiểm tra "
                    "trạng thái giao thư (Delivered/Bounced) trực tiếp trên Resend Dashboard (mục Emails)."
                ),
            }
        return {"status": "failed", "reason": f"PROVIDER_HTTP_{resp.status_code}"}
    if resp.status_code != 200:
        return {"status": "failed", "reason": f"PROVIDER_HTTP_{resp.status_code}"}
    body = resp.json()
    return {"status": "ok", "id": body.get("id"), "lastEvent": body.get("last_event"), "createdAt": body.get("created_at")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kiểm tra/gửi thử email giao dịch Axo (không in bí mật).")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Chỉ đọc cấu hình email (mặc định an toàn).")
    mode.add_argument("--send", action="store_true", help="Gửi MỘT thư thử thật (cần --to).")
    mode.add_argument("--status", metavar="EMAIL_ID", help="Hỏi trạng thái giao thư của một email đã gửi.")
    parser.add_argument("--to", help="Địa chỉ nhận thư thử (bắt buộc với --send).")
    parser.add_argument("--env-file", help="Tệp .env thay cho backend/.env.")
    args = parser.parse_args(argv)

    _load_env(args.env_file)
    if args.check:
        out = _check()
    elif args.send:
        if not args.to or "@" not in args.to:
            print("LỖI: --send cần --to <địa chỉ email hợp lệ>.", file=sys.stderr)
            return 2
        out = _send(args.to)
    else:
        out = _status(args.status)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    ok = out.get("available", True) if args.check else out.get("status") in ("accepted", "ok", "unsupported_by_key_scope")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
