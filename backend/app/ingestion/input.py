"""Lớp chuẩn hóa input (M4) — MỌI loại đầu vào quy về text rồi vào chung
pipeline analyze → classify → simulate → validate (M4 §1, §6).

Không loại input nào có pipeline riêng, không loại nào bypass validation.
Ảnh đi qua bước phiên dịch (Gemini Vision) thành text — Vision KHÔNG bao giờ
trả thẳng envelope (M4 §5). Code người dùng CHỈ được đọc, không execute (§8).
"""

from __future__ import annotations

import base64
import binascii

# ── Giới hạn ──────────────────────────────────────────────────
# Giới hạn và phép kiểm ẢNH không nằm ở đây nữa: thẩm quyền duy nhất là
# `app/ingestion/image.py` (PHOTO_PROBLEM_TO_SCENE_END_TO_END, 2026-09-13).
MAX_TEXT_CHARS = 8000
MAX_CODE_CHARS = 30_000
MAX_DOCX_BYTES = 10 * 1024 * 1024

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

# Ngôn ngữ code nhận diện từ đuôi (§4) — trước mắt ưu tiên .py
_CODE_LANGS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".c": "c",
    ".cpp": "cpp",
    ".java": "java",
    ".pas": "pascal",
}


class IngestError(Exception):
    """Lỗi chuẩn hóa input — main.py bắt và trả 400 với thông điệp tiếng Việt."""


def _decode_base64(content: str, limit: int, what: str) -> bytes:
    try:
        raw = base64.b64decode(content, validate=True)
    except (binascii.Error, ValueError):
        raise IngestError(f"{what} không phải dữ liệu base64 hợp lệ.")
    if len(raw) == 0:
        raise IngestError(f"{what} rỗng.")
    if len(raw) > limit:
        raise IngestError(f"{what} quá lớn (tối đa {limit // (1024 * 1024)}MB).")
    return raw


def _language_from_filename(filename: str | None) -> str:
    if not filename or "." not in filename:
        return "python"  # trước mắt mặc định .py
    ext = filename[filename.rindex(".") :].lower()
    return _CODE_LANGS.get(ext, "text")


def _extract_docx_text(raw: bytes) -> str:
    """Trích text từ .docx (§3 & Unified Input §10.D): paragraph + bảng + công thức OMML + hộp nổi."""
    from app.ingestion.document_reader import InputPrepareRejected, extract_docx_structured

    if not raw.startswith(b"PK"):
        raise IngestError("File .docx không hợp lệ (sai định dạng hoặc đã hỏng).")

    try:
        parsed = extract_docx_structured(raw)
    except InputPrepareRejected as err:
        raise IngestError(
            f"Không đọc được file .docx ({err})."
        ) from err

    if parsed.has_unreadable_ole_equation and parsed.formula_count == 0:
        raise IngestError(
            "File .docx chứa công thức nhị phân cũ (MathType/OLE) không đọc được chính xác."
        )

    result = parsed.full_text.strip()
    if not result:
        raise IngestError("File .docx không có nội dung văn bản nào đọc được.")
    return result[:MAX_TEXT_CHARS]


async def ingest_to_text(
    input_type: str,
    content: str,
    filename: str | None,
    mime_type: str | None,
    api_key: str | None,
) -> str:
    """Chuẩn hóa InputPayload về text để đưa vào pipeline.

    - text: dùng thẳng.
    - code: đọc trực tiếp, giữ nguyên xuống dòng/indent, bọc trong khối
      ```<lang>``` để analyze hiểu đây là code. KHÔNG execute (§4, §8).
    - document (.docx): trích xuất văn bản + bảng + công thức OMML (§3).
    - image: Gemini Vision phiên dịch thành text rồi mới vào pipeline (§5).

    Ném IngestError (→ 400) khi input sai; cần api_key riêng cho image.
    """
    if input_type == "text":
        text = content.strip()
        if len(text) > MAX_TEXT_CHARS:
            raise IngestError(f"Đề bài quá dài (tối đa {MAX_TEXT_CHARS} ký tự).")
        return text

    if input_type == "code":
        if len(content) > MAX_CODE_CHARS:
            raise IngestError(f"File code quá lớn (tối đa {MAX_CODE_CHARS} ký tự).")
        code = content.rstrip("\n")
        if not code.strip():
            raise IngestError("File code rỗng.")
        lang = _language_from_filename(filename)
        name = f" ({filename})" if filename else ""
        return f"Đoạn chương trình{name} cần phân tích:\n```{lang}\n{code}\n```"

    if input_type == "document":
        raw = _decode_base64(content, MAX_DOCX_BYTES, "File tài liệu")
        return _extract_docx_text(raw)

    if input_type == "image":
        # ĐƯỜNG CŨ, KHÔNG CÓ BƯỚC XEM LẠI. Sản phẩm nay đi `/api/input/prepare` (hoặc `/api/image/extract`)
        # → `/api/analyze` dạng `text`. Nhánh này được giữ cho hợp đồng `InputPayload` cũ,
        # nhưng đi qua ĐÚNG thẩm quyền chuẩn hoá và đọc ảnh của đường mới, và đóng chặt hơn nó:
        # bản trích xuất nào cần người xem lại thì ở đây bị TỪ CHỐI, vì không có ai để xem lại.
        from app.ingestion.image import ImageRejected, decode_image_base64, normalize_image
        from app.ingestion.image_extraction import (
            REJECTION_MESSAGES,
            VisionBusy,
            VisionContractError,
            VisionUnavailable,
            extract_problem_from_image,
        )

        try:
            anh = normalize_image(decode_image_base64(content), mime_type)
        except ImageRejected as err:
            raise IngestError(str(err)) from err
        if not api_key:
            raise IngestError("__NEED_KEY__")  # main.py chuyển thành 503
        try:
            kq = await extract_problem_from_image(anh, api_key, cache_version=None)
        except (VisionBusy, VisionUnavailable, VisionContractError) as err:
            raise IngestError(
                "Chưa đọc được đề trong ảnh lúc này. Hãy thử lại hoặc gõ tay đề."
            ) from err
        danh_gia = kq.assessment
        if danh_gia.status == "rejected":
            raise IngestError(REJECTION_MESSAGES[danh_gia.rejection_code or "IMAGE_NOT_READABLE"])
        if danh_gia.requires_confirmation:
            raise IngestError(
                "Ảnh có chỗ đọc chưa chắc chắn. Hãy dùng nút Tải ảnh để xem lại và "
                "sửa nội dung trước khi dựng mô phỏng."
            )
        return danh_gia.problem_text[:MAX_TEXT_CHARS]

    raise IngestError(f'Loại đầu vào "{input_type}" không được hỗ trợ.')
