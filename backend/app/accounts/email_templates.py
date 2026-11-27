"""Ba mẫu thư giao dịch (HTML + văn bản thuần). Không ảnh theo dõi, không tài nguyên ngoài, không đính kèm.

HTML dùng bảng + style nội tuyến để hiển thị ổn định trên các trình đọc thư phổ biến; màu chính lấy từ design token
`--primary` (#0075de). Mọi giá trị chèn vào HTML đều được escape.
"""

from __future__ import annotations

from html import escape

from .mailer import OutgoingEmail

_PRIMARY = "#0075de"
_INK = "#1f1f1f"
_MUTED = "#5f5f5f"
_CANVAS = "#f6f5f4"


def _ttl_label(minutes: int) -> str:
    if minutes % 1440 == 0:
        days = minutes // 1440
        return f"{days} ngày" if days != 1 else "24 giờ"
    if minutes % 60 == 0:
        return f"{minutes // 60} giờ"
    return f"{minutes} phút"


def _layout(*, heading: str, paragraphs: list[str], button: tuple[str, str] | None, footer: str) -> str:
    body = "".join(
        f'<p style="margin:0 0 14px;font-size:15px;line-height:1.6;color:{_INK};">{escape(p)}</p>' for p in paragraphs
    )
    cta = ""
    if button is not None:
        label, url = button
        cta = (
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:6px 0 18px;"><tr>'
            f'<td style="border-radius:8px;background:{_PRIMARY};">'
            f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer" '
            f'style="display:inline-block;padding:12px 22px;font-size:15px;font-weight:600;color:#ffffff;'
            f'text-decoration:none;border-radius:8px;">{escape(label)}</a></td></tr></table>'
            f'<p style="margin:0 0 14px;font-size:13px;line-height:1.5;color:{_MUTED};">'
            "Nếu nút không hoạt động, sao chép liên kết sau vào trình duyệt:<br>"
            f'<span style="word-break:break-all;color:{_PRIMARY};">{escape(url)}</span></p>'
        )
    return (
        '<!doctype html><html lang="vi"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="referrer" content="no-referrer">'
        f"<title>{escape(heading)}</title></head>"
        f'<body style="margin:0;padding:0;background:{_CANVAS};">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{_CANVAS};">'
        '<tr><td align="center" style="padding:28px 12px;">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        'style="max-width:520px;background:#ffffff;border:1px solid #e6e6e6;border-radius:12px;">'
        '<tr><td style="padding:28px 28px 8px;font-family:Inter,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">'
        f'<p style="margin:0 0 18px;font-size:18px;font-weight:700;color:{_INK};">Axo</p>'
        f'<h1 style="margin:0 0 16px;font-size:20px;line-height:1.35;font-weight:700;color:{_INK};">{escape(heading)}</h1>'
        f"{body}{cta}"
        "</td></tr>"
        '<tr><td style="padding:0 28px 26px;font-family:Inter,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">'
        f'<p style="margin:0;font-size:12px;line-height:1.5;color:{_MUTED};">{escape(footer)}</p>'
        "</td></tr></table></td></tr></table></body></html>"
    )


def verification_email(*, to: str, display_name: str, link: str, ttl_minutes: int) -> OutgoingEmail:
    ttl = _ttl_label(ttl_minutes)
    greeting = f"Chào {display_name.strip()}," if display_name.strip() else "Chào bạn,"
    paragraphs = [
        greeting,
        "Vui lòng xác minh địa chỉ email này để hoàn tất tài khoản và có thể khôi phục mật khẩu khi cần.",
        f"Liên kết có hiệu lực trong {ttl} và chỉ dùng được một lần.",
    ]
    footer = "Nếu bạn không tạo tài khoản, hãy bỏ qua thư này. Tài khoản sẽ không được xác minh."
    subject = "Xác minh địa chỉ email tài khoản Axo"
    text = "\n\n".join([*paragraphs, f"Xác minh email: {link}", footer])
    return OutgoingEmail(
        to=to,
        subject=subject,
        html=_layout(heading="Xác minh địa chỉ email", paragraphs=paragraphs, button=("Xác minh email", link),
                     footer=footer),
        text=text,
        category="verify_email",
    )


def password_reset_email(*, to: str, link: str, ttl_minutes: int) -> OutgoingEmail:
    ttl = _ttl_label(ttl_minutes)
    paragraphs = [
        "Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản gắn với địa chỉ email này.",
        f"Liên kết có hiệu lực trong {ttl} và chỉ dùng được một lần. Sau khi đặt lại, các phiên đăng nhập cũ sẽ bị đăng xuất.",
    ]
    footer = "Nếu bạn không yêu cầu, hãy bỏ qua thư này. Mật khẩu hiện tại vẫn giữ nguyên."
    subject = "Đặt lại mật khẩu tài khoản Axo"
    text = "\n\n".join([*paragraphs, f"Đặt lại mật khẩu: {link}", footer])
    return OutgoingEmail(
        to=to,
        subject=subject,
        html=_layout(heading="Đặt lại mật khẩu", paragraphs=paragraphs, button=("Đặt lại mật khẩu", link),
                     footer=footer),
        text=text,
        category="password_reset",
    )


def password_changed_email(*, to: str, login_url: str) -> OutgoingEmail:
    paragraphs = [
        "Mật khẩu tài khoản gắn với địa chỉ email này vừa được thay đổi thành công.",
        "Nếu chính bạn thực hiện, bạn không cần làm gì thêm.",
        "Nếu không phải bạn, hãy dùng chức năng Quên mật khẩu ngay để đặt mật khẩu mới, "
        "hoặc liên hệ giáo viên/quản trị viên để được hỗ trợ.",
    ]
    footer = "Đây là thư thông báo bảo mật tự động. Thư không chứa mật khẩu của bạn."
    subject = "Mật khẩu tài khoản Axo đã được thay đổi"
    text = "\n\n".join([*paragraphs, f"Đăng nhập: {login_url}", footer])
    return OutgoingEmail(
        to=to,
        subject=subject,
        html=_layout(heading="Mật khẩu đã được thay đổi", paragraphs=paragraphs, button=("Mở trang đăng nhập", login_url),
                     footer=footer),
        text=text,
        category="password_changed",
    )
