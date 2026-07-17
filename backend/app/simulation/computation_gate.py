"""M13 gate B lớp (a): computation-ownership — SERVER quyết, tất định, sau classify,
CHỈ trên đường generic (giữ carve-out chuyên biệt E7). Không đọc text đề."""
from app.simulation.dsl.manifest import known_gap_roles


def check_computation_ownership(analysis: dict, plan: dict) -> str | None:
    """Trả reason (tiếng Việt) khi yêu cầu đòi CƠ CHẾ TÍNH KẾT QUẢ mà không engine
    nào sở hữu → capability_gap; None khi generic được phép tiếp tục."""
    # unsupported_capabilities ⊆ known_gap_roles theo construction (required_roles lọc r in SEMANTIC_ROLES — representation.py) → phép giao là tương đương hành vi cũ, giữ làm phòng thủ tường minh.
    gaps = sorted(set(plan.get("unsupported_capabilities", [])) & known_gap_roles())
    if gaps:
        return (
            f"Bài cần cơ chế chưa có engine tất định sở hữu ({', '.join(gaps)}) — "
            "hệ từ chối trung thực thay vì dựng cảnh xấp xỉ."
        )
    ownership = analysis.get("result_ownership")
    if ownership not in ("provided", "rule_derivable"):
        # Fail-closed (ràng buộc duyệt lần 3): "algorithmic" → gap có chủ đích;
        # thiếu/ngoài enum → CŨNG từ chối, không default sang giá trị nào.
        if ownership == "algorithmic":
            return (
                "Kết quả của bài phải được TÍNH qua cơ chế thuật toán riêng mà không "
                "engine tất định nào của hệ sở hữu — hệ từ chối trung thực thay vì để "
                "AI tự giải rồi dựng cảnh minh hoạ đáp án."
            )
        return (
            "Phân tích không xác định được nguồn kết quả của bài (result_ownership "
            f"= {ownership!r}) — hệ từ chối an toàn thay vì đoán."
        )
    return None
