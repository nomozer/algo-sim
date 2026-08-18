"""Independent Algorithmic Reference Oracles (Ground Truth).

Cung cấp kết quả chuẩn xác tuyệt đối từ các thuật toán tham chiếu Python độc lập,
dùng để đối chiếu với kết quả cuối cùng (end state) của mô phỏng mà không phụ thuộc
vào tính tự khớp nội bộ của LLM.
"""

from __future__ import annotations
from typing import Any


def oracle_temperature_scan(days: list[float]) -> dict[str, Any]:
    """C01: Tìm ngày đầu tiên có nhiệt độ > trung bình tuần.
    
    Returns:
        {
            "average": float,
            "first_day_index": int (1-based index),
            "first_day_temp": float
        }
    """
    if not days:
        return {"average": 0.0, "first_day_index": -1, "first_day_temp": None}
    avg = sum(days) / len(days)
    for i, t in enumerate(days):
        if t > avg:
            return {
                "average": round(avg, 2),
                "first_day_index": i + 1,
                "first_day_temp": t,
            }
    return {"average": round(avg, 2), "first_day_index": -1, "first_day_temp": None}


def oracle_bracket_validator(s: str) -> dict[str, Any]:
    """C02: Kiểm tra tính hợp lệ của chuỗi dấu ngoặc bằng Stack.
    
    Returns:
        {
            "is_valid": bool,
            "error_at_index": int | None,
            "stack_trace": list[list[str]]
        }
    """
    matching = {')': '(', ']': '[', '}': '{'}
    stack: list[str] = []
    trace: list[list[str]] = [[]]
    
    for i, ch in enumerate(s):
        if ch in "([{":
            stack.append(ch)
            trace.append(list(stack))
        elif ch in ")]}":
            if not stack or stack[-1] != matching[ch]:
                return {"is_valid": False, "error_at_index": i, "stack_trace": trace}
            stack.pop()
            trace.append(list(stack))
    
    is_valid = len(stack) == 0
    return {
        "is_valid": is_valid,
        "error_at_index": None if is_valid else len(s) - 1,
        "stack_trace": trace,
    }


def oracle_count_in_range(orders: list[int], lo: int, hi: int) -> dict[str, Any]:
    """C03: Đếm số đơn hàng có giá trị trong khoảng [lo, hi].
    
    Returns:
        {
            "count": int,
            "matching_indices": list[int],
            "matching_values": list[int]
        }
    """
    matching_idx = [i for i, val in enumerate(orders) if lo <= val <= hi]
    matching_vals = [orders[i] for i in matching_idx]
    return {
        "count": len(matching_idx),
        "matching_indices": matching_idx,
        "matching_values": matching_vals,
    }


def oracle_sort_athletes(times: list[float]) -> dict[str, Any]:
    """C04: Sắp xếp thời gian chạy của vận động viên (tăng dần).
    
    Returns:
        {
            "sorted_times": list[float],
            "fastest": float,
            "slowest": float
        }
    """
    sorted_arr = sorted(times)
    return {
        "sorted_times": sorted_arr,
        "fastest": sorted_arr[0] if sorted_arr else None,
        "slowest": sorted_arr[-1] if sorted_arr else None,
    }


def oracle_last_occurrence(arr: list[int], target: int) -> dict[str, Any]:
    """C05: Tìm vị trí cuối cùng của phần tử target trong mảng.
    
    Returns:
        {
            "target": target,
            "last_index": int (0-based, -1 if not found)
        }
    """
    last_idx = -1
    for i, val in enumerate(arr):
        if val == target:
            last_idx = i
    return {
        "target": target,
        "last_index": last_idx,
    }


def oracle_table_filter(
    headers: list[str],
    rows: list[list[Any]],
    col_name: str,
    min_val: float,
) -> dict[str, Any]:
    """C06: Lọc các dòng trong bảng 2 chiều có giá trị cột >= min_val.
    
    Returns:
        {
            "matching_row_indices": list[int],
            "matching_count": int
        }
    """
    try:
        col_idx = headers.index(col_name)
    except ValueError:
        return {"matching_row_indices": [], "matching_count": 0}
        
    matching_rows: list[int] = []
    for r_idx, row in enumerate(rows):
        if r_idx < len(rows) and col_idx < len(row):
            try:
                val = float(row[col_idx])
                if val >= min_val:
                    matching_rows.append(r_idx)
            except (ValueError, TypeError):
                continue
                
    return {
        "matching_row_indices": matching_rows,
        "matching_count": len(matching_rows),
    }


def oracle_find_max(arr: list[float | int]) -> dict[str, Any]:
    """P01: Tìm giá trị lớn nhất trong mảng."""
    if not arr:
        return {"max_val": None, "max_index": -1}
    max_val = arr[0]
    max_idx = 0
    for i, v in enumerate(arr):
        if v > max_val:
            max_val = v
            max_idx = i
    return {"max_val": max_val, "max_index": max_idx}


def oracle_even_count(arr: list[int]) -> dict[str, Any]:
    """P03: Đếm số lượng số chẵn trong mảng."""
    even_indices = [i for i, v in enumerate(arr) if v % 2 == 0]
    return {
        "count": len(even_indices),
        "even_indices": even_indices,
    }

