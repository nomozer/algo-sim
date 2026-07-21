"""M17 W2A — insufficient-structure gate cho tree.traversal (chống LLM bịa cây).

Vấn đề (phát hiện live W2A): prompt "duyệt cây preorder" KHÔNG cho cấu trúc cây,
nhưng classify vẫn route tree.traversal và simulate BỊA nguyên một cây → chạy
executor = false-positive simulation (vi phạm R0). classify.md 2f dặn từ chối
nhưng LLM phớt lờ.

Phòng thủ DETERMINISTIC (given analyze output — KHÔNG đọc text đề, KHÔNG
keyword-patch, cùng khuôn computation gate M13): chạy TRÊN route tree.traversal
TRƯỚC simulate. Nếu analyze KHÔNG thấy CẤU TRÚC CÂY nào (không quan hệ, không
node cụ thể) → refuse "thiếu dữ kiện", KHÔNG cho simulate bịa.

Bất đối xứng có chủ đích: CHỈ refuse khi TÍN HIỆU CẤU TRÚC HOÀN TOÀN VẮNG —
đề duyệt cây thật (mô tả nút + quan hệ trái/phải) luôn có relations/objects/data
cụ thể nên KHÔNG bị chặn oan; đề trống rỗng "duyệt cây preorder" mới bị chặn.
Giới hạn: nếu analyze TỰ hallucination cấu trúc (bịa cả ở analyze) thì gate
không thấy — đó là analyze-integrity (ghi backlog), ngoài phạm vi gate này.
"""
from __future__ import annotations

from app.simulation.error_codes import ErrorCode

# Từ chung chỉ "cây" nói chung — KHÔNG tính là node cụ thể.
_GENERIC_TREE_WORDS = {
    "cây", "cay", "tree", "cây nhị phân", "cay nhi phan", "binary tree",
    "cấu trúc cây", "cau truc cay", "node", "nút", "nut",
}


def _concrete(items: list, is_str: bool) -> int:
    """Đếm phần tử CỤ THỂ (loại từ chung 'cây/tree')."""
    n = 0
    for it in items:
        text = it if is_str else (it.get("description") if isinstance(it, dict) else None)
        if not isinstance(text, str) or not text.strip():
            continue
        if text.strip().lower() in _GENERIC_TREE_WORDS:
            continue
        n += 1
    return n


def tree_structure_present(analysis: dict) -> bool:
    """Deterministic: analyze có nêu CẤU TRÚC cây (nút cụ thể / quan hệ) không?

    Đề cây thật luôn thoả ÍT NHẤT một: có relations (quan hệ trái/phải), hoặc
    ≥2 object cụ thể (các nút), hoặc ≥2 data item cụ thể. Đề trống → 0 cả ba."""
    if not isinstance(analysis, dict):
        return False
    relations = analysis.get("relations") or []
    objects = analysis.get("objects") or []
    data = analysis.get("data") or []
    if isinstance(relations, list) and len(relations) >= 1:
        return True
    if _concrete(objects if isinstance(objects, list) else [], is_str=True) >= 2:
        return True
    if _concrete(data if isinstance(data, list) else [], is_str=False) >= 2:
        return True
    return False


def check_tree_structure_sufficiency(analysis: dict) -> tuple[ErrorCode, str] | None:
    """Trả (code, message học-sinh-thân-thiện) khi THIẾU cấu trúc cây; None khi đủ.
    Chỉ gọi khi route cuối == tree.traversal."""
    if tree_structure_present(analysis):
        return None
    return (
        ErrorCode.STRUCTURE_INSUFFICIENT,
        "Đề yêu cầu duyệt cây nhưng chưa cho cấu trúc cây cụ thể (các nút và "
        "quan hệ con trái/con phải). Hãy mô tả rõ cây (ví dụ: gốc A, A có con "
        "trái B và con phải C…) rồi thử lại — hệ không tự dựng cây thay bạn.",
    )
