# -*- coding: utf-8 -*-
"""CHUỖI SỰ KIỆN CỦA MỘT LƯỢT PHÂN TÍCH — chẩn đoán, thụ động, tắt được.

Khác `telemetry.py` (đếm token theo stage): file này ghi *chuyện gì đã xảy ra*
— route ngữ nghĩa có chạy không, tới đâu, chết vì gì.

─── VÌ SAO TỒN TẠI ────────────────────────────────────────────────────────────

Lượt live 2026-08-24: ba đề đi qua `/api/analyze` thật, cả ba rơi về đường
legacy và trả `unsupported`. Log container có đúng ba dòng `POST /api/analyze
200 OK` — không một chữ nào về route ngữ nghĩa. Không biết được nó có chạy
không, chạy tới đâu, chết vì gì.

`run_pipeline` VỐN ĐÃ phát sự kiện cho một observer thụ động (`_emit` trong
`ai/pipeline.py`) — hạ tầng có sẵn từ M14. Nhưng `main.py` gọi nó với
`observer=None`, nên trong sản phẩm mọi sự kiện rơi vào hư không. Đây là cùng
một lớp lỗi với bất biến #22 (`stage_semantic_program` không ai gọi) và với
chính `semantic_route` từng bị bỏ quên ở đúng lời gọi ấy: **mảnh nào cũng có,
chưa mảnh nào được ghép.**

Hệ quả đo được: mỗi lượt live tiêu quota thật rồi trả về một chữ "unsupported"
không chẩn đoán được — tức tiêu tiền để mua lại đúng câu hỏi cũ.

─── RANH GIỚI ────────────────────────────────────────────────────────────────

THỤ ĐỘNG tuyệt đối: observer chỉ ghi, không đổi một quyết định nào (cùng hợp
đồng với bất biến #22). Bật/tắt qua `SEMANTIC_TELEMETRY`, mặc định TẮT —
production không trả giá cho công cụ chẩn đoán.

KHÔNG BAO GIỜ ghi khoá API hay bí mật: chỉ nhận các trường mà `ai/pipeline.py`
đã chọn để phát, và những trường đó không mang credential.

Vòng đệm trong tiến trình, không chạm CSDL: công cụ của người sửa lỗi trong một
phiên, không phải nhật ký kiểm toán.

BẤT BIẾN CỦA VÒNG ĐỆM: **mọi thứ nằm trong `_kho` đều tuần tự hoá được thành
JSON.** Xem `_json_an_toan` để biết vì sao nó phải là một bất biến chứ không
phải một lời nhắc.
"""
from __future__ import annotations

import os
import time
import uuid
from collections import deque
from dataclasses import fields, is_dataclass
from fractions import Fraction
from typing import Any

#: Số lượt gần nhất giữ lại. Nhỏ có chủ đích — công cụ chẩn đoán, không phải kho.
SUC_CHUA = 20

_kho: deque[dict[str, Any]] = deque(maxlen=SUC_CHUA)


def bat_telemetry() -> bool:
    """Mặc định TẮT. Bật là một quyết định vận hành tường minh."""
    return os.getenv("SEMANTIC_TELEMETRY", "0") == "1"


def _json_an_toan(gt: Any) -> Any:
    """Hạ một giá trị bất kỳ về thứ `json.dumps` nuốt được.

    ─── VÌ SAO CẦN, ĐO ĐƯỢC Ở LƯỢT LIVE 2026-08-25 ────────────────────────

    `semantic_route` phát kèm `final_memory` — bộ nhớ cuối của interpreter, và
    chỗ phát ghi rõ nó là thứ DUY NHẤT đem so được với ground truth độc lập.
    Với miền hình học, bộ nhớ ấy chứa `Fraction` và các dataclass `Vec3`/
    `Line3`/`Plane3`. `jsonable_encoder` của FastAPI thử `dict(obj)` rồi
    `vars(obj)`, cả hai hỏng trên `Fraction`, và endpoint trả **500**.

    Hình dạng của lỗi mới là chỗ đắt: `final_memory` chỉ có mặt khi route đi đủ
    xa, nên công cụ chẩn đoán **mù đúng vào lúc hình học chạy được**. Lượt hỏng
    đọc được vết, lượt chạy được thì không — ngược hẳn thứ ta cần.

    Hai lựa chọn có chủ đích:

    - `Fraction` → **chuỗi phân số**, không hoá float. Cùng quy ước với
      `scene3d` (*"mọi số là chuỗi phân số CHÍNH XÁC"*); hoá `2.5` là ném đi
      đúng tính chính xác hữu tỉ mà lõi hình học tồn tại để giữ.
    - Kiểu chưa ai lường → `repr`, **không ném**. Một vòng đệm chẩn đoán tự
      giết mình vì dữ liệu nó được giao là một công cụ hỏng; `repr` xấu vẫn đọc
      được, còn 500 thì không nói gì cả.
    """
    if gt is None or isinstance(gt, (str, bool, int, float)):
        return gt
    if isinstance(gt, Fraction):
        return str(gt)
    # `is_dataclass` đúng cả với LỚP, nên phải loại lớp ra — ta chỉ hạ THỰC THỂ.
    if is_dataclass(gt) and not isinstance(gt, type):
        return {f.name: _json_an_toan(getattr(gt, f.name)) for f in fields(gt)}
    if isinstance(gt, dict):
        return {str(k): _json_an_toan(v) for k, v in gt.items()}
    if isinstance(gt, (list, tuple, set, frozenset)):
        return [_json_an_toan(v) for v in gt]
    return repr(gt)


class DiagnosticObserver:
    """Observer THỤ ĐỘNG — chỉ thu, không đổi gì.

    `emit(name, data)` là TOÀN BỘ giao diện mà `ai/pipeline.py::_emit` gọi tới.
    Cố ý không thêm phương thức nào khác, để observer không bao giờ trở thành
    chỗ cho một nhánh logic lén chen vào.
    """

    def __init__(self, de_bai: str):
        self.request_id = uuid.uuid4().hex[:12]
        self.bat_dau = time.time()
        self.de_bai = de_bai[:300]
        self.su_kien: list[dict[str, Any]] = []

    def emit(self, name: str, data: dict[str, Any]) -> None:
        self.su_kien.append(
            {
                "stage": name,
                "ms": int((time.time() - self.bat_dau) * 1000),
                # `data` do pipeline chọn; KHÔNG lọc lại ở đây, để tránh hai nơi
                # cùng quyết định cái gì được ghi rồi lệch nhau.
                "data": data,
            }
        )

    def ket_thuc(self, envelope: dict[str, Any] | None) -> dict[str, Any]:
        ban_ghi = {
            "request_id": self.request_id,
            "de_bai": self.de_bai,
            "tong_ms": int((time.time() - self.bat_dau) * 1000),
            "so_su_kien": len(self.su_kien),
            "su_kien": self.su_kien,
            # Kết cục CUỐI, đọc được ngay mà không phải lần lại chuỗi.
            "ket_cuc": {
                "status": (envelope or {}).get("status"),
                "simulation_id": (envelope or {}).get("simulation_id"),
                "source": (envelope or {}).get("source"),
                "failure_category": (envelope or {}).get("failure_category"),
            },
            # Chặng CUỐI của route ngữ nghĩa — đúng câu hỏi mà lượt live
            # 2026-08-24 không trả lời được: nó có chạy không, và chết ở đâu.
            "semantic_route": next(
                (e["data"] for e in reversed(self.su_kien)
                 if e["stage"] == "semantic_route"),
                None,
            ),
        }
        # HẠ MỘT LẦN, Ở ĐÂY. Đặt phép hạ tại `emit` thì `ket_cuc` (đọc thẳng từ
        # envelope) vẫn lọt; đặt tại endpoint thì mỗi người đọc `_kho` lại phải
        # tự nhớ. Bản ghi chỉ vào kho qua đúng cửa này, nên đây là chỗ duy nhất
        # giữ được bất biến "mọi thứ trong `_kho` đều dumps được".
        ban_ghi = _json_an_toan(ban_ghi)
        _kho.append(ban_ghi)
        return ban_ghi


def lan_gan_nhat(n: int = 5) -> list[dict[str, Any]]:
    return list(_kho)[-n:]


def theo_id(request_id: str) -> dict[str, Any] | None:
    for b in reversed(_kho):
        if b["request_id"] == request_id:
            return b
    return None


def xoa_het() -> None:
    _kho.clear()
