# -*- coding: utf-8 -*-
"""HÌNH DẠNG THẤT BẠI của chương trình sinh ra — đo TẤT ĐỊNH. **0 API call.**

    `CURVED_ERGONOMICS_PROBE_V2`, 2026-09-04.

Wave ecgônômi hỏi *"hình dạng lỗi có dịch chuyển đúng hướng không"*, không hỏi
*"đúng hay sai"*. Muốn trả lời được thì phải đếm được từng lớp — và đếm bằng
MÁY, trên chính chương trình sinh ra.

⚠️ Bản §18 phân lớp bằng cách **đọc tay** 4 chương trình. Đọc tay không lặp lại
được: lượt sau người khác đọc sẽ ra số khác, và không ai biết vì sao. Ba trong
bốn lớp dưới đây nay có định nghĩa chạy được; lớp thứ tư thì KHÔNG, và nó được
khai thẳng là không tất định thay vì cho một con số trông như đo được.

Cùng bộ dò này chấm CẢ artifact §18 (để có BEFORE) lẫn lượt mới (AFTER) — một
định nghĩa, hai lượt. Chép số từ bảng viết tay của §18 sang bảng mới là so hai
thước đo khác nhau rồi gọi hiệu số là tiến bộ.
"""
from __future__ import annotations

from typing import Any

__all__ = ["KHONG_TAT_DINH", "do_hinh_dang", "gop_hinh_dang"]

#: Lớp KHÔNG đo được bằng máy — khai thẳng thay vì cho một con số giả.
#:
#: `MISSED_EXISTING_COMPOSITION` hỏi *"mô hình có bỏ lỡ một phép hợp thành ĐÃ
#: CÓ không"*. Trả lời được câu ấy đòi biết **lời giải đúng lẽ ra là gì** cho
#: từng đề — tức một oracle ở mức chương trình, không phải ở mức đáp số. Kho
#: chưa có thứ đó. Một hàm đoán bằng heuristic (“có `declare_vector` thì chắc
#: là bỏ lỡ”) sẽ đếm sai theo một hướng cố định và không ai kiểm được.
KHONG_TAT_DINH = ("MISSED_EXISTING_COMPOSITION",)

#: Kiểu hình học mang TOẠ ĐỘ. Chỉ những kiểu này mới có chuyện “khai toạ độ mà
#: không có nguồn”.
_KIEU_TOA_DO = ("point3", "vector3")


def _decls(spec: dict[str, Any]) -> list[dict]:
    return list(spec.get("memory_declarations") or [])


def _target_vars(spec: dict[str, Any]) -> set[str]:
    return {s.get("target_var") for s in (spec.get("statements") or [])
            if s.get("target_var")}


def do_hinh_dang(spec: dict[str, Any] | None) -> dict[str, Any]:
    """Bốn lớp hình dạng lỗi trên MỘT chương trình.

    `spec is None` = mô hình không sinh nổi một chương trình hợp lược đồ.
    """
    if spec is None:
        return {"SCHEMA_MISUSE": 1, "INVENTED_HELPER_POINT": 0,
                "DECLARED_NOT_CONSTRUCTED": 0,
                "INVENTED_HELPER_NAMES": [], "DECLARED_NOT_CONSTRUCTED_NAMES": [],
                "MISSED_EXISTING_COMPOSITION": None}

    dung = _target_vars(spec)

    # ① TOẠ ĐỘ KHÔNG CÓ NGUỒN — đúng thứ R0 bác. Một điểm phụ bịa ra luôn mang
    #    hình dạng này: có `initial_value`, không trỏ được về dữ kiện nào.
    bia = [d.get("name") for d in _decls(spec)
           if d.get("type") in _KIEU_TOA_DO
           and d.get("initial_value") is not None
           and not d.get("source_fact_id")]

    # ② KHAI MÀ KHÔNG DỰNG — biến không có giá trị đầu và cũng không bao giờ là
    #    `target_var` của câu lệnh nào. Chương trình nhắc tới một vật chưa tồn
    #    tại; interpreter sẽ không có gì để đọc.
    treo = [d.get("name") for d in _decls(spec)
            if d.get("initial_value") is None and d.get("name") not in dung]

    return {
        "SCHEMA_MISUSE": 0,
        "INVENTED_HELPER_POINT": len(bia),
        "INVENTED_HELPER_NAMES": bia,
        "DECLARED_NOT_CONSTRUCTED": len(treo),
        "DECLARED_NOT_CONSTRUCTED_NAMES": treo,
        # Khai `None`, KHÔNG khai 0: “chưa đo được” và “đo được, bằng 0” là hai
        # sự kiện khác nhau — cùng luật với `MISSING_TELEMETRY != 0_TOKENS`.
        "MISSED_EXISTING_COMPOSITION": None,
    }


def gop_hinh_dang(theo_ca: dict[str, dict]) -> dict[str, Any]:
    """Cộng dồn nhiều ca. Lớp không tất định giữ nguyên `None`."""
    tong = {k: 0 for k in ("SCHEMA_MISUSE", "INVENTED_HELPER_POINT",
                           "DECLARED_NOT_CONSTRUCTED")}
    for h in theo_ca.values():
        for k in tong:
            tong[k] += h.get(k) or 0
    tong["MISSED_EXISTING_COMPOSITION"] = None
    tong["_ghi_chu"] = (
        "MISSED_EXISTING_COMPOSITION không đo được bằng máy — cần một oracle ở "
        "mức CHƯƠNG TRÌNH, kho chưa có. Khai None thay vì 0.")
    return tong
