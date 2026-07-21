"""M17 W2A — insufficient-structure gate cho tree.traversal (chống LLM bịa cây).

Vấn đề (live W2A run 1): prompt "duyệt cây preorder" KHÔNG cho cấu trúc, nhưng
classify route tree.traversal và simulate BỊA nguyên một cây → false-positive
simulation (vi phạm R0).

Bản v1 (đếm số lượng object/relation) ĐÃ BỊ CHỨNG MINH KHÔNG ĐỦ ở live run 2:
analyze cho đề trống vẫn trả relations=["quan hệ cha-con giữa các nút trong
cây"] + objects=["nút (đỉnh) của cây", ...] → đếm ra rel=1/obj=2 → "có cấu
trúc" → gate SẼ CHO QUA. Mô tả TRỪU TƯỢNG bị tính như cấu trúc CỤ THỂ.

Bản v2 (đây) — TÍN HIỆU ĐỊNH DANH NÚT (grounded-ish):
CHỈ tính là có cấu trúc khi TỒN TẠI MỘT item (relation/data/object) nêu **≥2
ĐỊNH DANH NÚT phân biệt** — tức một QUAN HỆ giữa hai nút CÓ TÊN, vd "B là con
trái của A", "A has left child B". Hệ quả:
- "quan hệ cha-con giữa các nút trong cây" → 0 định danh → THIẾU (chặn đúng);
- hai nhãn RỜI RẠC ở hai item khác nhau → KHÔNG đủ (đúng chỉ đạo: danh sách
  hai nhãn không quan hệ ≠ cây);
- đề cây thật (mọi case live 1–4) luôn có ≥1 quan hệ hai-định-danh → KHÔNG bị
  chặn oan (đã đối chiếu output analyze THẬT).

Deterministic given analyze output — KHÔNG đọc text đề, KHÔNG keyword-patch
tên thuật toán (cùng khuôn computation gate M13).

Giới hạn còn lại: nếu analyze TỰ bịa cả định danh cụ thể ("nút A", "B là con
của A") cho đề trống thì gate không phân biệt được — cần provenance/source-span
validation (backlog analyze-integrity).
"""
from __future__ import annotations

import re

from app.simulation.error_codes import ErrorCode

# Token định danh nút: NGẮN (≤2 ký tự ASCII alnum) và bắt đầu bằng chữ HOA
# hoặc chữ số — "A", "B", "C1", "10". Từ tiếng Việt ("nút", "cây", "của") tách
# ra thành mảnh chữ thường → không khớp; từ tiếng Anh dài ("has", "child",
# "The") cũng không khớp.
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_MAX_ID_LEN = 2


def _identifiers(text: str) -> set[str]:
    out: set[str] = set()
    for tok in _TOKEN_RE.findall(text or ""):
        if len(tok) > _MAX_ID_LEN:
            continue
        head = tok[0]
        if head.isdigit() or (head.isascii() and head.isupper()):
            out.add(tok)
    return out


def _item_texts(analysis: dict) -> list[str]:
    """Gom text của MỖI item analyze (relations là chỗ chính; quét cả data/objects
    để không phụ thuộc field — normalization adapter).

    QUAN TRỌNG: item dạng DICT được GỘP các giá trị chuỗi thành MỘT text. Analyze
    có thể trả quan hệ dạng prose ("B là con trái của A") HOẶC có cấu trúc
    ({"type":"left_child","from":"A","to":"B"}) — cả hai đều là MỘT quan hệ nêu
    hai nút có tên, nên phải đọc như một item (không tách rời từng field, vì
    tách ra thì mỗi mảnh chỉ còn một định danh)."""
    texts: list[str] = []
    for key in ("relations", "data", "objects"):
        items = analysis.get(key) or []
        if not isinstance(items, list):
            continue
        for it in items:
            if isinstance(it, str):
                texts.append(it)
            elif isinstance(it, dict):
                joined = " ".join(v for v in it.values() if isinstance(v, str))
                if joined:
                    texts.append(joined)
    return texts


def linked_node_items(analysis: dict) -> list[dict]:
    """Các item nêu ≥2 định danh nút phân biệt (bằng chứng QUAN HỆ có tên)."""
    if not isinstance(analysis, dict):
        return []
    out = []
    for text in _item_texts(analysis):
        ids = _identifiers(text)
        if len(ids) >= 2:
            out.append({"text": text, "identifiers": sorted(ids)})
    return out


def tree_structure_present(analysis: dict) -> bool:
    """Có cấu trúc cây ⟺ tồn tại ÍT NHẤT MỘT item nêu quan hệ giữa ≥2 nút CÓ TÊN."""
    return len(linked_node_items(analysis)) >= 1


def structure_evidence(analysis: dict) -> dict:
    """Bằng chứng máy-đọc mà gate dựa vào (artifact/eval). Không đổi phán quyết."""
    if not isinstance(analysis, dict):
        return {"relations": 0, "linked_items": 0, "identifiers": [], "present": False}
    relations = analysis.get("relations") or []
    linked = linked_node_items(analysis)
    ids: set[str] = set()
    for item in linked:
        ids.update(item["identifiers"])
    return {
        "relations": len(relations) if isinstance(relations, list) else 0,
        "linked_items": len(linked),
        "linked_examples": [i["text"] for i in linked[:3]],
        "identifiers": sorted(ids),
        "present": len(linked) >= 1,
    }


def check_tree_structure_sufficiency(analysis: dict) -> tuple[ErrorCode, str] | None:
    """Trả (code, message học-sinh-thân-thiện) khi THIẾU cấu trúc cây; None khi đủ.
    Chỉ gọi khi route cuối == tree.traversal."""
    if tree_structure_present(analysis):
        return None
    return (
        ErrorCode.STRUCTURE_INSUFFICIENT,
        "Đề yêu cầu duyệt cây nhưng chưa cho cấu trúc cây cụ thể (các nút có tên "
        "và quan hệ con trái/con phải giữa chúng). Hãy mô tả rõ cây (ví dụ: gốc "
        "A, A có con trái B và con phải C…) rồi thử lại — hệ không tự dựng cây "
        "thay bạn.",
    )
