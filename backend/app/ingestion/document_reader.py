"""Đọc và chọn nội dung bài toán từ PDF / DOCX / văn bản chỉ dẫn — tất định, 0 lượt gọi AI.

Bảo đảm (§4, §10.B–D, §13–§18):
- Xác thực loại tệp bằng magic bytes (PNG/JPEG/WebP, PDF, DOCX), chặn giả đuôi, macro VBA,
  zip-bomb, thực thể XML ngoài (XXE) và liên kết ngoài.
- Đọc DOCX có cấu trúc theo đúng thứ tự đọc: đoạn văn, hộp văn bản nổi (`w:txbxContent`),
  bảng (`w:tbl`), công thức toán OMML (`m:oMath` / `m:oMathPara`), chỉ số trên/dưới (`w:vertAlign`)
  và hình minh họa nhúng (`word/media/*`); báo giới hạn fail-closed khi gặp công thức nhị phân
  OLE cũ không có văn bản thay thế.
- Đọc PDF phân biệt trang có text layer sạch (0 lượt gọi VLM) và trang scan/lỗi font (chỉ
  rasterize đúng trang cần thiết ở độ phân giải đủ đọc).
- Tách nhiều bài toán độc lập (`Bài 1`, `Bài 2`, `Câu 1`...), đối chiếu chỉ dẫn của học sinh
  trong ô nhập đề và hợp nhất dữ kiện bổ sung tường minh mà không suy đoán.
"""

from __future__ import annotations

import base64
import binascii
import io
import posixpath
import re
import unicodedata
import zipfile
from dataclasses import dataclass
from typing import Literal

import pymupdf as fitz
from lxml import etree

from app.ingestion.image import (
    SUPPORTED_IMAGE_MIMES,
    NormalizedImage,
     normalize_image,
    sniff_image_mime,
)
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC, detect_domain

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 30
MAX_DOCX_ZIP_ENTRIES = 500
MAX_DOCX_UNCOMPRESSED_BYTES = 32 * 1024 * 1024
MAX_DOCX_COMPRESSION_RATIO = 60.0
PDF_SCAN_RENDER_DPI = 200

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_MIME = "application/pdf"

_NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_NS_M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
_NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
_NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS_V = "urn:schemas-microsoft-com:vml"
_NS_O = "urn:schemas-microsoft-com:office:office"
_NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

_HEIC_BRANDS = frozenset({b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1", b"avif"})


class InputPrepareRejected(ValueError):
    """Tệp đính kèm hoặc yêu cầu chuẩn bị đầu vào bị từ chối fail-closed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class EmbeddedFigure:
    figure_id: str
    media_path: str
    raw_bytes: bytes
    anchor_block_index: int


@dataclass(frozen=True)
class DocxExtractionResult:
    full_text: str
    paragraphs: tuple[str, ...]
    table_Texts: tuple[str, ...]
    formula_count: int
    embedded_figures: tuple[EmbeddedFigure, ...]
    has_unreadable_ole_equation: bool


@dataclass(frozen=True)
class PdfPageContent:
    page_number: int
    kind: Literal["text", "scanned", "blank"]
    text: str
    has_figure: bool
    image_count: int
    drawing_count: int
    garbled_text_layer: bool


@dataclass(frozen=True)
class PdfExtractionResult:
    page_count: int
    pages: tuple[PdfPageContent, ...]
    inspected_pages: tuple[int, ...]


@dataclass(frozen=True)
class UserComposerDirective:
    raw_text: str
    target_page: int | None
    target_problem_number: int | None
    target_problem_index: int | None
    topic_keywords: tuple[str, ...]
    supplemental_text: str
    is_standalone_problem: bool


@dataclass(frozen=True)
class TextProblemCandidate:
    candidate_id: str
    index: int
    problem_number: int | None
    label: str
    problem_text: str
    preview_snippet: str
    page_number: int | None
    has_figure: bool
    is_geometry: bool


def _clean_text(s: str) -> str:
    norm = unicodedata.normalize("NFC", s)
    cleaned = "".join(
        ch for ch in norm if ch in "\n\t" or unicodedata.category(ch)[0] != "C"
    )
    return cleaned.replace("\u2212", "-")


def _ext_of(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ""
    return filename[filename.rfind(".") :].lower().strip()


def decode_attachment_base64(content: str) -> bytes:
    """Giải mã base64 có kiểm trần dung lượng trước và sau khi giải mã."""
    if not isinstance(content, str) or not content.strip():
        raise InputPrepareRejected("ATTACHMENT_EMPTY", "Tệp đính kèm rỗng.")
    if len(content) > (MAX_ATTACHMENT_BYTES * 4) // 3 + 16:
        raise InputPrepareRejected(
            "ATTACHMENT_TOO_LARGE",
            f"Tệp đính kèm quá lớn (tối đa {MAX_ATTACHMENT_BYTES // (1024 * 1024)}MB).",
        )
    try:
        raw = base64.b64decode(content, validate=True)
    except (binascii.Error, ValueError) as err:
        raise InputPrepareRejected(
            "ATTACHMENT_INVALID_ENCODING", "Dữ liệu tệp đính kèm không phải base64 hợp lệ."
        ) from err
    if not raw:
        raise InputPrepareRejected("ATTACHMENT_EMPTY", "Tệp đính kèm rỗng.")
    if len(raw) > MAX_ATTACHMENT_BYTES:
        raise InputPrepareRejected(
            "ATTACHMENT_TOO_LARGE",
            f"Tệp đính kèm quá lớn (tối đa {MAX_ATTACHMENT_BYTES // (1024 * 1024)}MB).",
        )
    return raw


def sniff_input_file_kind(
    raw: bytes,
    declared_mime: str | None = None,
    filename: str | None = None,
) -> tuple[Literal["image", "pdf", "docx"], str]:
    """Nhận diện loại tệp thực tế bằng magic bytes và cấu trúc nội bộ (§18)."""
    if not raw:
        raise InputPrepareRejected("ATTACHMENT_EMPTY", "Tệp đính kèm rỗng.")
    if len(raw) > MAX_ATTACHMENT_BYTES:
        raise InputPrepareRejected(
            "ATTACHMENT_TOO_LARGE",
            f"Tệp đính kèm quá lớn (tối đa {MAX_ATTACHMENT_BYTES // (1024 * 1024)}MB).",
        )

    ext = _ext_of(filename)
    mime = (declared_mime or "").strip().lower()

    # 1. HEIC/HEIF/AVIF: báo rõ chưa hỗ trợ trực tiếp thay vì tuyên bố giả hoặc báo lỗi mơ hồ.
    is_heic_magic = len(raw) >= 12 and raw[4:8] == b"ftyp" and raw[8:12] in _HEIC_BRANDS
    if is_heic_magic or ext in (".heic", ".heif") or mime in ("image/heic", "image/heif"):
        raise InputPrepareRejected(
            "UNSUPPORTED_HEIC_FORMAT",
            "Định dạng HEIC/HEIF chưa được hỗ trợ trực tiếp. Em hãy chuyển hoặc chụp lại dưới dạng JPG/PNG.",
        )

    # 2. Ảnh PNG / JPEG / WebP.
    img_mime = sniff_image_mime(raw)
    if img_mime is not None:
        if ext in (".pdf", ".docx", ".doc") or mime in (PDF_MIME, DOCX_MIME):
            raise InputPrepareRejected(
                "FILE_TYPE_MISMATCH",
                "Nội dung tệp là ảnh nhưng phần mở rộng hoặc định dạng khai báo không khớp.",
            )
        if mime and mime != "application/octet-stream" and mime in SUPPORTED_IMAGE_MIMES and mime != img_mime:
            raise InputPrepareRejected(
                "FILE_TYPE_MISMATCH",
                "Nội dung ảnh không khớp định dạng khai báo (tệp có thể bị đổi đuôi).",
            )
        if mime and mime not in SUPPORTED_IMAGE_MIMES and mime != "application/octet-stream":
            raise InputPrepareRejected(
                "UNSUPPORTED_FILE_TYPE",
                f'Định dạng khai báo "{mime}" không khớp với ảnh PNG/JPEG/WEBP.',
            )
        return "image", img_mime

    # 3. PDF (%PDF-).
    if raw.startswith(b"%PDF-"):
        if ext in (".png", ".jpg", ".jpeg", ".webp", ".docx", ".doc") or (
            mime and mime not in (PDF_MIME, "application/octet-stream")
        ):
            raise InputPrepareRejected(
                "FILE_TYPE_MISMATCH",
                "Nội dung tệp là PDF nhưng định dạng khai báo không khớp.",
            )
        return "pdf", PDF_MIME

    # 4. DOCX (gói ZIP OpenXML hợp lệ, không macro, không zip-bomb).
    if raw.startswith(b"PK\x03\x04"):
        if ext in (".png", ".jpg", ".jpeg", ".webp", ".pdf") or (
            mime and mime not in (DOCX_MIME, "application/octet-stream", "application/zip")
        ):
            raise InputPrepareRejected(
                "FILE_TYPE_MISMATCH",
                "Nội dung tệp nén không khớp với định dạng ảnh/PDF khai báo.",
            )
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                infos = zf.infolist()
                if len(infos) > MAX_DOCX_ZIP_ENTRIES:
                    raise InputPrepareRejected(
                        "ATTACHMENT_ZIP_BOMB",
                        "Tệp .docx chứa quá nhiều mục nén bất thường.",
                    )
                total_uncompressed = sum(max(0, info.file_size) for info in infos)
                if total_uncompressed > MAX_DOCX_UNCOMPRESSED_BYTES:
                    raise InputPrepareRejected(
                        "ATTACHMENT_ZIP_BOMB",
                        "Dung lượng giải nén của tệp .docx vượt ngưỡng an toàn.",
                    )
                if (
                    total_uncompressed > 1_048_576
                    and (total_uncompressed / float(max(1, len(raw)))) > MAX_DOCX_COMPRESSION_RATIO
                ):
                    raise InputPrepareRejected(
                        "ATTACHMENT_ZIP_BOMB",
                        "Tỷ lệ nén của tệp .docx bất thường, từ chối xử lý để bảo vệ tài nguyên.",
                    )
                names = {info.filename for info in infos}
                lower_names = {n.lower() for n in names}
                if any(n.endswith("vbaproject.bin") for n in lower_names):
                    raise InputPrepareRejected(
                        "DOCX_MACROS_FORBIDDEN",
                        "Tệp Word chứa macro (VBA) không được phép chạy. Em hãy lưu sang .docx chuẩn.",
                    )
                if "word/document.xml" not in names or "[Content_Types].xml" not in names:
                    raise InputPrepareRejected(
                        "FILE_TYPE_MISMATCH",
                        "Tệp không phải tài liệu Word (.docx) hợp lệ.",
                    )
        except InputPrepareRejected:
            raise
        except (zipfile.BadZipFile, OSError, ValueError) as err:
            raise InputPrepareRejected(
                "FILE_CORRUPT", "Không đọc được tệp .docx (tệp bị hỏng hoặc lỗi cấu trúc nén)."
            ) from err
        return "docx", DOCX_MIME

    # 5. Word .doc nhị phân cũ (OLE2).
    if raw.startswith(b"\xd0\xcf\x11\xe0"):
        raise InputPrepareRejected(
            "LEGACY_DOC_UNSUPPORTED",
            "Định dạng Word cũ (.doc) chưa được hỗ trợ. Em hãy lưu tệp dưới dạng .docx hoặc PDF.",
        )

    raise InputPrepareRejected(
        "UNSUPPORTED_FILE_TYPE",
        "Tệp không hợp lệ hoặc định dạng không được hỗ trợ. Chỉ nhận JPG, PNG, WebP, PDF hoặc DOCX.",
    )


def _xml_parser() -> etree.XMLParser:
    return etree.XMLParser(resolve_entities=False, no_network=True, recover=False, huge_tree=False)


def _local_tag(elem: etree._Element) -> str:
    tag = elem.tag
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _is_atomic_math(token: str) -> bool:
    t = token.strip()
    return bool(t) and len(t) <= 6 and bool(re.fullmatch(r"[A-Za-z0-9'′αβγπ°]+", t))


def omml_to_text(elem: etree._Element) -> str:
    """Chuyển cây công thức Word OMML (`m:oMath` / `m:oMathPara`) sang biểu thức toán học rõ ràng."""
    name = _local_tag(elem)

    if name == "t":
        return (elem.text or "").strip()

    if name == "f":
        num_el = elem.find(f"{{{_NS_M}}}num")
        den_el = elem.find(f"{{{_NS_M}}}den")
        num = omml_to_text(num_el).strip() if num_el is not None else ""
        den = omml_to_text(den_el).strip() if den_el is not None else ""
        if not num and not den:
            return ""
        lhs = num if _is_atomic_math(num) else f"({num})"
        rhs = den if _is_atomic_math(den) else f"({den})"
        return f"{lhs}/{rhs}"

    if name == "rad":
        deg_el = elem.find(f"{{{_NS_M}}}deg")
        base_el = elem.find(f"{{{_NS_M}}}e")
        deg = omml_to_text(deg_el).strip() if deg_el is not None else ""
        base = omml_to_text(base_el).strip() if base_el is not None else ""
        body = base if _is_atomic_math(base) else f"({base})"
        if not deg or deg == "2":
            return f"√{body}"
        if deg == "3":
            return f"∛{body}"
        return f"root({deg}, {base})"

    if name == "sSup":
        base_el = elem.find(f"{{{_NS_M}}}e")
        sup_el = elem.find(f"{{{_NS_M}}}sup")
        base = omml_to_text(base_el).strip() if base_el is not None else ""
        sup = omml_to_text(sup_el).strip() if sup_el is not None else ""
        if sup in ("'", "′", "\\prime"):
            return f"{base}'"
        if sup in ("''", "″"):
            return f"{base}''"
        if sup in ("°", "o", "0", "\\circ") and re.search(r"\d$", base):
            return f"{base}°" if sup in ("°", "\\circ") else f"{base}^{sup}"
        if sup in ("°", "\\circ"):
            return f"{base}°"
        exp = sup if _is_atomic_math(sup) else f"({sup})"
        return f"{base}^{exp}"

    if name == "sSub":
        base_el = elem.find(f"{{{_NS_M}}}e")
        sub_el = elem.find(f"{{{_NS_M}}}sub")
        base = omml_to_text(base_el).strip() if base_el is not None else ""
        sub = omml_to_text(sub_el).strip() if sub_el is not None else ""
        return f"{base}_{sub}" if _is_atomic_math(sub) else f"{base}_({sub})"

    if name == "sSubSup":
        base_el = elem.find(f"{{{_NS_M}}}e")
        sub_el = elem.find(f"{{{_NS_M}}}sub")
        sup_el = elem.find(f"{{{_NS_M}}}sup")
        base = omml_to_text(base_el).strip() if base_el is not None else ""
        sub = omml_to_text(sub_el).strip() if sub_el is not None else ""
        sup = omml_to_text(sup_el).strip() if sup_el is not None else ""
        if sup in ("'", "′"):
            return f"{base}'_{sub}"
        return f"{base}_{sub}^{sup}"

    if name == "d":
        beg = "("
        end = ")"
        sep = ", "
        dpr = elem.find(f"{{{_NS_M}}}dPr")
        if dpr is not None:
            b_el = dpr.find(f"{{{_NS_M}}}begChr")
            e_el = dpr.find(f"{{{_NS_M}}}endChr")
            s_el = dpr.find(f"{{{_NS_M}}}sepChr")
            if b_el is not None and f"{{{_NS_M}}}val" in b_el.attrib:
                beg = b_el.attrib[f"{{{_NS_M}}}val"]
            if e_el is not None and f"{{{_NS_M}}}val" in e_el.attrib:
                end = e_el.attrib[f"{{{_NS_M}}}val"]
            if s_el is not None and f"{{{_NS_M}}}val" in s_el.attrib:
                sep = s_el.attrib[f"{{{_NS_M}}}val"]
        parts = [omml_to_text(ch).strip() for ch in elem.findall(f"{{{_NS_M}}}e")]
        return f"{beg}{sep.join(p for p in parts if p)}{end}"

    if name == "func":
        fn_el = elem.find(f"{{{_NS_M}}}fName")
        arg_el = elem.find(f"{{{_NS_M}}}e")
        fn = omml_to_text(fn_el).strip() if fn_el is not None else ""
        arg = omml_to_text(arg_el).strip() if arg_el is not None else ""
        return f"{fn}({arg})" if arg and not arg.startswith("(") else f"{fn}{arg}"

    if name == "eqArr":
        rows = [omml_to_text(ch).strip() for ch in elem.findall(f"{{{_NS_M}}}e")]
        return "; ".join(r for r in rows if r)

    if name in ("oMathPara", "oMath", "e", "num", "den", "sup", "sub", "deg", "fName", "r", "box", "borderBox", "acc", "bar", "nary"):
        if name.endswith("Pr"):
            return ""
        chunks: list[str] = []
        for ch in elem:
            ch_name = _local_tag(ch)
            if ch_name.endswith("Pr"):
                continue
            piece = omml_to_text(ch)
            if piece:
                chunks.append(piece)
        return "".join(chunks)

    if name.endswith("Pr"):
        return ""

    return "".join(omml_to_text(ch) for ch in elem if not _local_tag(ch).endswith("Pr"))


def _load_docx_media_rels(zf: zipfile.ZipFile) -> dict[str, str]:
    rels_path = "word/_rels/document.xml.rels"
    if rels_path not in zf.namelist():
        return {}
    try:
        rel_root = etree.fromstring(zf.read(rels_path), parser=_xml_parser())
    except etree.XMLSyntaxError:
        return {}
    mapping: dict[str, str] = {}
    for rel in rel_root.findall(f"{{{_NS_PKG_REL}}}Relationship"):
        # Tuyệt đối bỏ qua liên kết ngoài (External) để tránh rò rỉ mạng / SSRF (§18).
        if rel.attrib.get("TargetMode", "").lower() == "external":
            continue
        rid = rel.attrib.get("Id", "")
        target = rel.attrib.get("Target", "")
        if not rid or not target:
            continue
        norm_target = posixpath.normpath(posixpath.join("word", target.lstrip("/")))
        if norm_target.startswith("word/media/"):
            mapping[rid] = norm_target
    return mapping


def extract_docx_structured(raw: bytes) -> DocxExtractionResult:
    """Trích xuất văn bản, bảng, công thức OMML, hộp nổi và hình nhúng từ `.docx` (§10.D)."""
    sniff_input_file_kind(raw, DOCX_MIME, "input.docx")

    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            media_rels = _load_docx_media_rels(zf)
            xml_bytes = zf.read("word/document.xml")
            root = etree.fromstring(xml_bytes, parser=_xml_parser())
            media_cache: dict[str, bytes] = {}
            for mpath in set(media_rels.values()):
                if mpath in zf.namelist():
                    media_cache[mpath] = zf.read(mpath)
    except InputPrepareRejected:
        raise
    except (KeyError, zipfile.BadZipFile, etree.XMLSyntaxError, OSError, ValueError) as err:
        raise InputPrepareRejected(
            "FILE_CORRUPT",
            "Không đọc được nội dung tệp .docx (cấu trúc XML bị hỏng).",
        ) from err

    body = root.find(f"{{{_NS_W}}}body")
    if body is None:
        raise InputPrepareRejected("FILE_CORRUPT", "Tệp .docx thiếu phần thân văn bản.")

    paragraphs_out: list[str] = []
    tables_out: list[str] = []
    ordered_lines: list[str] = []
    figures: list[EmbeddedFigure] = []
    seen_rids: set[str] = set()
    formula_count = 0
    unreadable_ole = False

    def collect_drawings(node: etree._Element, block_idx: int) -> None:
        nonlocal unreadable_ole
        for blip in node.findall(f".//{{{_NS_A}}}blip"):
            rid = blip.attrib.get(f"{{{_NS_R}}}embed")
            if rid and rid in media_rels and rid not in seen_rids:
                mpath = media_rels[rid]
                if mpath in media_cache:
                    seen_rids.add(rid)
                    figures.append(
                        EmbeddedFigure(
                            figure_id=f"docx-fig-{len(figures) + 1}",
                            media_path=mpath,
                            raw_bytes=media_cache[mpath],
                            anchor_block_index=block_idx,
                        )
                    )
        for imdata in node.findall(f".//{{{_NS_V}}}imagedata"):
            rid = imdata.attrib.get(f"{{{_NS_R}}}id")
            if rid and rid in media_rels and rid not in seen_rids:
                mpath = media_rels[rid]
                if mpath in media_cache:
                    seen_rids.add(rid)
                    figures.append(
                        EmbeddedFigure(
                            figure_id=f"docx-fig-{len(figures) + 1}",
                            media_path=mpath,
                            raw_bytes=media_cache[mpath],
                            anchor_block_index=block_idx,
                        )
                    )
        for ole in node.findall(f".//{{{_NS_O}}}OLEObject"):
            prog = (ole.attrib.get("ProgID") or "").lower()
            if "equation" in prog or "mathtype" in prog:
                unreadable_ole = True

    def read_paragraph(p_el: etree._Element, block_idx: int, *, allow_textbox: bool = True) -> list[str]:
        nonlocal formula_count
        collect_drawings(p_el, block_idx)
        parts: list[str] = []
        textbox_paras: list[str] = []

        for child in p_el:
            cname = _local_tag(child)
            if cname == "r":
                # Kiểm tra chỉ số trên/dưới trong run thường (`SA^2`, `A_1`).
                vert = ""
                rpr = child.find(f"{{{_NS_W}}}rPr")
                if rpr is not None:
                    va = rpr.find(f"{{{_NS_W}}}vertAlign")
                    if va is not None:
                        vert = va.attrib.get(f"{{{_NS_W}}}val", "")
                run_txt = "".join(t.text or "" for t in child.findall(f"{{{_NS_W}}}t"))
                if child.find(f"{{{_NS_W}}}tab") is not None:
                    run_txt += " "
                if run_txt:
                    if vert == "superscript" and run_txt.strip() not in ("'", "′", "°"):
                        parts.append(f"^{run_txt.strip()}")
                    elif vert == "subscript":
                        parts.append(f"_{run_txt.strip()}")
                    else:
                        parts.append(run_txt)
                if allow_textbox:
                    for txbx in child.findall(f".//{{{_NS_W}}}txbxContent"):
                        for sub_p in txbx.findall(f"{{{_NS_W}}}p"):
                            textbox_paras.extend(read_paragraph(sub_p, block_idx, allow_textbox=False))
            elif cname in ("oMath", "oMathPara"):
                m_txt = omml_to_text(child).strip()
                if m_txt:
                    formula_count += 1
                    parts.append(f" {m_txt} ")
            elif cname in ("hyperlink", "smartTag", "sdtContent"):
                for sub_r in child.findall(f".//{{{_NS_W}}}t"):
                    if sub_r.text:
                        parts.append(sub_r.text)
                for sub_m in child.findall(f".//{{{_NS_M}}}oMath"):
                    m_txt = omml_to_text(sub_m).strip()
                    if m_txt:
                        formula_count += 1
                        parts.append(f" {m_txt} ")

        joined = _clean_text(" ".join("".join(parts).split()))
        out = [joined] if joined else []
        out.extend(tp for tp in textbox_paras if tp)
        return out

    block_cursor = 0
    for child in body:
        cname = _local_tag(child)
        if cname == "p":
            p_lines = read_paragraph(child, block_cursor)
            for pl in p_lines:
                paragraphs_out.append(pl)
                ordered_lines.append(pl)
                block_cursor += 1
        elif cname == "tbl":
            for row in child.findall(f".//{{{_NS_W}}}tr"):
                cell_strs: list[str] = []
                for cell in row.findall(f"{{{_NS_W}}}tc"):
                    cell_parts: list[str] = []
                    for cp in cell.findall(f"{{{_NS_W}}}p"):
                        cell_parts.extend(read_paragraph(cp, block_cursor))
                    c_joined = " ".join(cell_parts).strip()
                    if c_joined:
                        cell_strs.append(c_joined)
                if cell_strs:
                    row_str = " | ".join(cell_strs)
                    tables_out.append(row_str)
                    ordered_lines.append(row_str)
                    block_cursor += 1

    full_text = "\n".join(ordered_lines).strip()
    return DocxExtractionResult(
        full_text=full_text,
        paragraphs=tuple(paragraphs_out),
        table_Texts=tuple(tables_out),
        formula_count=formula_count,
        embedded_figures=tuple(figures),
        has_unreadable_ole_equation=unreadable_ole,
    )


def _is_garbled_pdf_text(text: str) -> bool:
    if not text:
        return False
    if "(cid:" in text.lower():
        return True
    bad = 0
    visible = 0
    for ch in text:
        if ch.isspace():
            continue
        visible += 1
        cp = ord(ch)
        if ch == "\ufffd" or (0xE000 <= cp <= 0xF8FF):
            bad += 1
    return visible >= 8 and (bad / float(visible)) > 0.03


def _is_running_page_furniture(line: str, y0: float, y1: float, page_h: float) -> bool:
    if page_h <= 0:
        return False
    near_edge = y1 <= page_h * 0.055 or y0 >= page_h * 0.945
    if not near_edge:
        return False
    s = line.strip()
    if len(s) > 42:
        return False
    return bool(
        re.fullmatch(r"(?:trang|page)?\s*[-–—]?\s*\d{1,4}(?:\s*/\s*\d{1,4})?\s*[-–—]?", s, flags=re.IGNORECASE)
    )


def extract_pdf_structured(raw: bytes, *, target_page: int | None = None) -> PdfExtractionResult:
    """Đọc cấu trúc PDF theo từng trang, phân biệt text-layer sạch với trang scan (§10.B, §10.C)."""
    sniff_input_file_kind(raw, PDF_MIME, "input.pdf")

    try:
        doc = fitz.open(stream=raw, filetype="pdf")
    except Exception as err:  # noqa: BLE001
        raise InputPrepareRejected(
            "FILE_CORRUPT", "Không mở được tệp PDF (tệp bị hỏng hoặc sai cấu trúc)."
        ) from err

    try:
        if doc.needs_pass or doc.is_encrypted:
            raise InputPrepareRejected(
                "PDF_ENCRYPTED",
                "Tệp PDF đang đặt mật khẩu bảo vệ. Em hãy mở khoá tệp hoặc chụp ảnh phần đề bài.",
            )
        page_count = doc.page_count
        if page_count <= 0:
            raise InputPrepareRejected("FILE_CORRUPT", "Tệp PDF không có trang nào.")
        if page_count > MAX_PDF_PAGES:
            raise InputPrepareRejected(
                "PDF_TOO_MANY_PAGES",
                f"Tệp PDF quá dài ({page_count} trang; tối đa {MAX_PDF_PAGES} trang). "
                "Em hãy trích trang chứa đề bài hoặc gõ rõ số trang.",
            )
        if target_page is not None and (target_page < 1 or target_page > page_count):
            raise InputPrepareRejected(
                "PDF_PAGE_OUT_OF_RANGE",
                f"Em yêu cầu trang {target_page} nhưng tệp PDF chỉ có {page_count} trang.",
            )

        indices = [target_page - 1] if target_page is not None else list(range(page_count))
        pages_out: list[PdfPageContent] = []

        for idx in indices:
            page = doc.load_page(idx)
            rect = page.rect
            page_h = float(rect.height)
            raw_blocks = page.get_text("blocks")
            text_blocks = sorted(
                [b for b in raw_blocks if len(b) >= 7 and b[6] == 0],
                key=lambda b: (round(float(b[1]) / 6.0), float(b[0])),
            )
            cleaned_lines: list[str] = []
            for b in text_blocks:
                btxt = _clean_text(str(b[4] or ""))
                line = " ".join(btxt.split())
                if not line:
                    continue
                if _is_running_page_furniture(line, float(b[1]), float(b[3]), page_h):
                    continue
                cleaned_lines.append(line)

            joined = "\n".join(cleaned_lines).strip()
            garbled = _is_garbled_pdf_text(joined)
            img_count = len(page.get_images(full=False))
            drawings = page.get_drawings()
            draw_count = sum(max(1, len(d.get("items", ()))) for d in drawings)
            has_fig = img_count > 0 or draw_count >= 4

            if len(joined) >= 20 and not garbled:
                kind: Literal["text", "scanned", "blank"] = "text"
            elif img_count > 0 or draw_count >= 3 or garbled:
                kind = "scanned"
            else:
                kind = "blank"

            pages_out.append(
                PdfPageContent(
                    page_number=idx + 1,
                    kind=kind,
                    text="" if garbled else joined,
                    has_figure=has_fig,
                    image_count=img_count,
                    drawing_count=draw_count,
                    garbled_text_layer=garbled,
                )
            )

        return PdfExtractionResult(
            page_count=page_count,
            pages=tuple(pages_out),
            inspected_pages=tuple(i + 1 for i in indices),
        )
    finally:
        doc.close()


def render_pdf_page_normalized(raw: bytes, page_number: int) -> NormalizedImage:
    """Chỉ rasterize ĐÚNG MỘT trang PDF cần thiết sang `NormalizedImage` (200 DPI, chặn trần cạnh)."""
    try:
        doc = fitz.open(stream=raw, filetype="pdf")
    except Exception as err:  # noqa: BLE001
        raise InputPrepareRejected("FILE_CORRUPT", "Không mở được tệp PDF.") from err

    try:
        if page_number < 1 or page_number > doc.page_count:
            raise InputPrepareRejected(
                "PDF_PAGE_OUT_OF_RANGE",
                f"Trang {page_number} nằm ngoài phạm vi tệp PDF ({doc.page_count} trang).",
            )
        page = doc.load_page(page_number - 1)
        zoom = PDF_SCAN_RENDER_DPI / 72.0
        max_dim = max(float(page.rect.width), float(page.rect.height), 1.0)
        if max_dim * zoom > 2600.0:
            zoom = 2600.0 / max_dim
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        png_bytes = pix.tobytes("png")
    finally:
        doc.close()

    return normalize_image(png_bytes, "image/png")


_PROB_HEADING_RE = re.compile(
    r"^\s*(?:bài(?:\s+tập)?|câu(?:\s+hỏi)?|ví\s+dụ)\s*(?:số\s*)?(\d{1,3})\s*[:.)\-–]\s*(.*)$",
    flags=re.IGNORECASE,
)

_TOPIC_PHRASES: tuple[str, ...] = (
    "hình chóp cụt",
    "hình chóp",
    "khối chóp",
    "tứ diện",
    "lăng trụ",
    "hình lập phương",
    "hình hộp",
)


def parse_user_composer_instruction(user_text: str | None) -> UserComposerDirective:
    """Phân tích văn bản học sinh gõ kèm tệp đính kèm: chỉ dẫn chọn bài/trang + dữ kiện bổ sung (§4)."""
    raw = _clean_text((user_text or "").strip())
    if not raw:
        return UserComposerDirective(
            raw_text="",
            target_page=None,
            target_problem_number=None,
            target_problem_index=None,
            topic_keywords=(),
            supplemental_text="",
            is_standalone_problem=False,
        )

    low = raw.lower()
    page_m = re.search(r"\btrang\s*(?:số\s*)?(\d{1,3})\b", low)
    target_page = int(page_m.group(1)) if page_m else None

    prob_m = re.search(r"\b(?:bài|câu)\s*(?:tập\s*)?(?:số\s*)?(\d{1,2})\b", low)
    target_prob_num = int(prob_m.group(1)) if prob_m else None
    target_prob_idx = target_prob_num
    if target_prob_idx is None:
        if re.search(r"\b(?:bài|câu)\s+đầu(?:\s+tiên)?\b", low):
            target_prob_idx = 1
        elif re.search(r"\b(?:bài|câu)\s+cuối(?:\s+cùng)?\b", low):
            target_prob_idx = -1

    topics = [kw for kw in _TOPIC_PHRASES if kw in low]
    if "hình chóp cụt" in topics and "hình chóp" in topics:
        topics.remove("hình chóp")

    # Trích dữ kiện bổ sung tường minh (vd: "Hình vẽ nằm trong file, dữ kiện bổ sung là SA = 4.").
    supp = ""
    supp_m = re.search(
        r"(?:dữ\s*kiện\s*bổ\s*sung|giả\s*thiết\s*bổ\s*sung|bổ\s*sung(?:\s*thêm)?|biết\s*thêm|cho\s*thêm)"
        r"\s*(?:là|:)?\s*([^\n]+)",
        raw,
        flags=re.IGNORECASE,
    )
    if supp_m:
        supp = supp_m.group(1).strip().rstrip(".")
    else:
        # Nếu không có cụm "dữ kiện bổ sung" nhưng văn bản chứa đẳng thức/quan hệ toán học cụ thể (`=`, `⊥`, `∥`)
        # và KHÔNG phải cả bài độc lập, giữ phần mệnh đề toán học sau khi gỡ mệnh đề điều hướng tệp.
        has_math_relation = bool(
            re.search(r"(?:=|\bvuông\s+góc\b|\bsong\s+song\b|⊥|∥|\bgóc\s+giữa\b)", raw, flags=re.IGNORECASE)
        )
        is_full_problem = detect_domain(raw) == DOMAIN_HINH_HOC and len(raw) >= 45 and "cho " in low
        if has_math_relation and not is_full_problem:
            stripped = re.sub(
                r"^[^,.;:]*\b(?:trong\s+(?:ảnh|file|tệp|tài\s+liệu)|đính\s+kèm|ở\s+trang\s+\d+)\b[^,.;:]*[,.;:]\s*",
                "",
                raw,
                flags=re.IGNORECASE,
            ).strip().rstrip(".")
            if stripped:
                supp = stripped

    is_standalone = detect_domain(raw) == DOMAIN_HINH_HOC and len(raw) >= 35
    return UserComposerDirective(
        raw_text=raw,
        target_page=target_page,
        target_problem_number=target_prob_num,
        target_problem_index=target_prob_idx,
        topic_keywords=tuple(topics),
        supplemental_text=supp,
        is_standalone_problem=is_standalone,
    )


def merge_supplemental_text(base_problem_text: str, directive: UserComposerDirective) -> str:
    """Hợp nhất dữ kiện bổ sung tường minh của học sinh vào văn bản đề bài mà giữ nguyên mệnh đề gốc."""
    base = base_problem_text.strip()
    supp = directive.supplemental_text.strip()
    if not supp:
        return base
    if supp.lower() in base.lower():
        return base
    sep = "" if base.endswith((".", "?", "!")) else "."
    return f"{base}{sep} Biết {supp}."


def split_text_into_problems(
    text: str,
    *,
    page_number: int | None = None,
    has_figure: bool = False,
) -> list[TextProblemCandidate]:
    """Tách văn bản tài liệu thành danh sách các bài toán độc lập (giữ nguyên ý con `a)`, `b)` trong bài)."""
    lines = [ln.strip() for ln in _clean_text(text).splitlines() if ln.strip()]
    if not lines:
        return []

    raw_items: list[tuple[int | None, str, list[str]]] = []
    preamble_geometry: list[str] = []

    for ln in lines:
        m = _PROB_HEADING_RE.match(ln)
        if m:
            pnum = int(m.group(1))
            rest = m.group(2).strip()
            body_start = f"Bài {pnum}: {rest}".strip() if rest else f"Bài {pnum}:"
            raw_items.append((pnum, f"Bài {pnum}", [rest] if rest else [body_start]))
        else:
            if raw_items:
                raw_items[-1][2].append(ln)
            else:
                # Lọc tiêu đề chương/mục không phải đề toán trước `Bài 1:` nhưng giữ nếu không có đánh số `Bài`.
                if detect_domain(ln) == DOMAIN_HINH_HOC or len(ln) >= 35:
                    preamble_geometry.append(ln)

    candidates: list[TextProblemCandidate] = []
    if not raw_items:
        joined = " ".join(lines).strip()
        is_geo = detect_domain(joined) == DOMAIN_HINH_HOC
        page_tag = f" (Trang {page_number})" if page_number is not None else ""
        snippet = joined if len(joined) <= 140 else f"{joined[:137]}..."
        candidates.append(
            TextProblemCandidate(
                candidate_id=f"text-p{page_number or 1}-1",
                index=1,
                problem_number=None,
                label=f"Đề bài{page_tag}",
                problem_text=joined,
                preview_snippet=snippet,
                page_number=page_number,
                has_figure=has_figure,
                is_geometry=is_geo,
            )
        )
        return candidates

    # Nếu có một bài hình học đứng trước `Bài 2:` mà không ghi chữ `Bài 1:`, giữ nó làm ứng viên đầu.
    if preamble_geometry:
        pre_txt = " ".join(preamble_geometry).strip()
        if detect_domain(pre_txt) == DOMAIN_HINH_HOC:
            raw_items.insert(0, (None, "Đoạn mở đầu", [pre_txt]))

    for idx, (pnum, short_label, body_lines) in enumerate(raw_items, start=1):
        body = " ".join(body_lines).strip()
        if not body:
            continue
        is_geo = detect_domain(body) == DOMAIN_HINH_HOC
        page_tag = f" · Trang {page_number}" if page_number is not None else ""
        fig_tag = " · kèm hình" if has_figure else ""
        snippet = body if len(body) <= 140 else f"{body[:137]}..."
        cid = f"text-p{page_number or 1}-{idx}"
        candidates.append(
            TextProblemCandidate(
                candidate_id=cid,
                index=idx,
                problem_number=pnum,
                label=f"{short_label}{page_tag}{fig_tag}",
                problem_text=body,
                preview_snippet=snippet,
                page_number=page_number,
                has_figure=has_figure,
                is_geometry=is_geo,
            )
        )

    return candidates


def select_text_candidate(
    candidates: list[TextProblemCandidate],
    directive: UserComposerDirective,
    selected_candidate_id: str | None = None,
) -> tuple[TextProblemCandidate | None, list[TextProblemCandidate], str | None]:
    """Chọn bài toán từ danh sách ứng viên văn bản theo chỉ dẫn người dùng (§4, §14).

    Trả `(chosen, matching_pool, error_or_ambiguity_message)`.
    - Không bao giờ tự đoán bài đầu tiên khi có >= 2 bài hình học phù hợp.
    - Nếu người dùng chỉ định rõ `Bài k` hoặc chủ đề mà không khớp bài nào, trả danh sách để chọn.
    """
    if not candidates:
        return None, [], "Tài liệu không có nội dung bài toán nào đọc được."

    # 1. Người dùng vừa chạm chọn trực tiếp một ứng viên từ danh sách gợi ý.
    if selected_candidate_id:
        for c in candidates:
            if c.candidate_id == selected_candidate_id:
                return c, candidates, None

    geo_candidates = [c for c in candidates if c.is_geometry]
    pool = geo_candidates if geo_candidates else candidates

    # 2. Lọc theo trang nếu người dùng ghi rõ `trang X`.
    if directive.target_page is not None:
        page_pool = [c for c in pool if c.page_number == directive.target_page]
        if not page_pool:
            all_on_page = [c for c in candidates if c.page_number == directive.target_page]
            if not all_on_page:
                return (
                    None,
                    pool,
                    f"Không tìm thấy bài toán hình học ở trang {directive.target_page}. Em hãy chọn bài bên dưới.",
                )
            pool = all_on_page
        else:
            pool = page_pool

    # 3. Lọc theo số bài (`Bài 2`, `Câu 3`, `bài đầu`, `bài cuối`).
    if directive.target_problem_number is not None:
        exact_num = [c for c in pool if c.problem_number == directive.target_problem_number]
        if len(exact_num) == 1:
            return exact_num[0], pool, None
        if len(exact_num) > 1:
            pool = exact_num
        elif 1 <= directive.target_problem_number <= len(pool) and all(c.problem_number is None for c in pool):
            return pool[directive.target_problem_number - 1], pool, None
        else:
            return (
                None,
                pool,
                f"Không tìm thấy Bài {directive.target_problem_number} trong tài liệu. Em hãy chọn bài cần dựng.",
            )
    elif directive.target_problem_index == 1 and pool:
        return pool[0], pool, None
    elif directive.target_problem_index == -1 and pool:
        return pool[-1], pool, None

    # 4. Lọc theo từ khoá khối hình người dùng chỉ định (vd: "Chỉ lấy đề hình chóp ở trang 3").
    if directive.topic_keywords:
        kw_matches = [
            c
            for c in pool
            if all(kw in c.problem_text.lower() for kw in directive.topic_keywords)
        ]
        if len(kw_matches) == 1:
            return kw_matches[0], pool, None
        if len(kw_matches) > 1:
            pool = kw_matches
        else:
            return (
                None,
                pool,
                "Không xác định được duy nhất bài khớp mô tả của em. Em chạm chọn bài muốn dựng nhé.",
            )

    # 5. Nếu chỉ có đúng 1 bài hình học trong tài liệu (các mục khác là tiêu đề/mục lục), chọn tự động!
    if len(pool) == 1:
        return pool[0], pool, None

    return (
        None,
        pool,
        f"Tài liệu có {len(pool)} bài toán độc lập. Em chạm chọn bài muốn dựng hình nhé.",
    )
