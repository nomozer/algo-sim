# -*- coding: utf-8 -*-
"""Ghi CHI PHÍ của một lượt đo — HARNESS, không phải sản phẩm. **0 API call.**

VÌ SAO TỒN TẠI: lượt PHASE 5 (2026-08-24) chạy trọn 10 bài rồi **không ghi được
nó tiêu bao nhiêu**. Báo cáo phải viết *"ước lượng 20–34 lượt logic, không xác
nhận được"* — một lượt đo không tái lập được chi phí của chính nó. `telemetry.py`
vốn đã đếm đủ năm trường token theo từng stage, và docstring của nó nói thẳng
*"ai cần artifact thì gọi `usage_report()` rồi tự ghi ra `docs/evaluation/`"*.
Chưa runner nào gọi. Đây là chỗ trả nợ.

─── RANH GIỚI: BỌC, KHÔNG SỬA ────────────────────────────────────────────────

`GhiNhanApi.boc()` thay `pipeline.call_gemini` bằng một hàm gọi **thẳng hàm gốc**
rồi trả **nguyên giá trị gốc**. Nó không đọc, không sửa, không nuốt lỗi — ngoại
lệ bay qua nguyên vẹn và vẫn được tính giờ. Cùng khuôn proxy mà runner đã dùng
cho `load_skill`, và cùng lý do: `pipeline` là mã SẢN PHẨM, một nhu cầu quan
trắc không được đổi chữ ký của nó.

Đây là điều kiện để con số có nghĩa: nếu bộ ghi làm đổi hành vi pipeline thì thứ
đo được là *pipeline có bộ ghi*, không phải pipeline.

─── VÌ SAO BẢNG GIÁ NẰM TRONG ARTIFACT, KHÔNG CHỈ TRONG MÃ ───────────────────

Giá API đổi. Một con số USD nằm trong `docs/evaluation/` sẽ được đọc lại sau
nhiều tháng, có thể bị trích vào luận văn, và **không ai kiểm lại được nó tính
theo giá nào**. Nên `bao_cao()` ghi kèm ĐƠN GIÁ, NGÀY và NGUỒN đã dùng: con số
trở thành một phép tính tái lập được thay vì một khẳng định.

Model ngoài bảng ⇒ `uoc_tinh_duoc: False`, KHÔNG phải `0.0`. "Không biết giá" và
"miễn phí" là hai điều khác hẳn nhau.
"""
from __future__ import annotations

import time
from typing import Any, Callable

#: Đơn giá USD trên MỘT TRIỆU token, tra tay ngày 2026-08-25.
#:
#: `thoughts` tính theo giá OUTPUT: token suy luận của model thinking được tính
#: như token sinh ra. `cached` KHÔNG được chiết khấu ở đây — xem `_tien()`.
BANG_GIA_USD = {
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
}
NGAY_TRA_GIA = "2026-08-25"
NGUON_GIA = "ai.google.dev/gemini-api/docs/pricing (tra tay, bậc trả phí)"


def _tien(model: str, tok: dict[str, int]) -> dict[str, Any]:
    """Token → USD. Là ƯỚC TÍNH CHẶN TRÊN, và nói rõ vì sao.

    Hai chỗ ước tính cao hơn thực tế, cố ý — chặn trên thì an toàn khi lập ngân
    sách, còn chặn dưới thì dẫn tới tiêu lố:

    1. `cached_content_tokens` được tính đầy giá input. Thực tế Google chiết
       khấu mạnh phần cache. Không mô hình hoá chiết khấu vì bậc giá của nó phụ
       thuộc TTL và cách nạp, và đoán sai theo chiều thấp thì con số vô dụng.
    2. Không trừ bậc miễn phí.
    """
    gia = BANG_GIA_USD.get(model)
    if gia is None:
        return {
            "uoc_tinh_duoc": False,
            "ly_do": f"model '{model}' không có trong bảng giá tra ngày {NGAY_TRA_GIA}",
        }
    vao = tok.get("prompt_tokens", 0) + tok.get("cached_content_tokens", 0)
    ra = tok.get("candidates_tokens", 0) + tok.get("thoughts_tokens", 0)
    return {
        "uoc_tinh_duoc": True,
        "usd": round(vao / 1e6 * gia["input"] + ra / 1e6 * gia["output"], 6),
        "token_tinh_gia_vao": vao,
        "token_tinh_gia_ra": ra,
        "don_gia_usd_moi_trieu": dict(gia),
        "ngay_tra_gia": NGAY_TRA_GIA,
        "nguon_gia": NGUON_GIA,
        "khai": "CHẶN TRÊN — token cache tính đầy giá input, không trừ bậc miễn phí.",
    }


class GhiNhanApi:
    """Bọc `call_gemini` để đo GIỜ và giữ ĐẦU RA THÔ. Không đổi hành vi.

    ─── VÌ SAO GIỮ ĐẦU RA THÔ ───────────────────────────────────────────────

    Khi IR trượt schema, `stage_semantic_program` trả `(None, "…lỗi…")` và **đầu
    ra thô bị vứt**. Phân tích PHASE 5 phải dựng lại *"mô hình bịa `kind:
    construct_plane`"* từ chuỗi lỗi của Pydantic — tức đọc dấu vết thay vì đọc
    vật chứng. Bốn bài trượt G1 và không bài nào để lại thứ mô hình thật sự viết.

    Giữ ở đây, không sửa `pipeline`: đây là nhu cầu của phép đo, không phải của
    sản phẩm. Cắt `GIOI_HAN_THO` ký tự vì artifact phải đọc được bằng mắt.
    """

    GIOI_HAN_THO = 12_000

    def __init__(self) -> None:
        self.luot: list[dict[str, Any]] = []

    def boc(self, goc: Callable) -> Callable:
        async def _bọc(*a, **kw):
            from app.ai.telemetry import current_stage

            stage = current_stage()
            t0 = time.perf_counter()
            try:
                raw = await goc(*a, **kw)
            except BaseException as e:
                # Lượt HỎNG vẫn tốn tiền và vẫn tốn giờ. Không ghi nó là báo
                # thiếu chi phí đúng ở những lượt đắt nhất (timeout, 429).
                self.luot.append({
                    "stage": stage,
                    "giay": round(time.perf_counter() - t0, 3),
                    "loi": f"{type(e).__name__}: {e}"[:300],
                    "raw": None,
                })
                raise
            self.luot.append({
                "stage": stage,
                "giay": round(time.perf_counter() - t0, 3),
                "loi": None,
                "raw": (raw or "")[: self.GIOI_HAN_THO],
            })
            return raw

        return _bọc

    # ── đọc lại ──────────────────────────────────────────────────────────
    def tho_cuoi(self, stage: str) -> str | None:
        """Đầu ra thô CUỐI CÙNG của một stage — thứ đã bị từ chối."""
        for l in reversed(self.luot):
            if l["stage"] == stage and l["raw"] is not None:
                return l["raw"]
        return None

    def do_tre(self) -> dict[str, Any]:
        giay = [l["giay"] for l in self.luot]
        if not giay:
            return {"so_luot": 0}
        return {
            "so_luot": len(giay),
            "tong_giay": round(sum(giay), 3),
            "cham_nhat_giay": round(max(giay), 3),
            "theo_stage": {
                s: round(sum(l["giay"] for l in self.luot if l["stage"] == s), 3)
                for s in sorted({l["stage"] for l in self.luot})
            },
        }


def bao_cao(model: str, budget: Any, ghi: GhiNhanApi | None = None) -> dict[str, Any]:
    """Chi phí toàn lượt. `budget=None` ⇒ nói thẳng là KHÔNG ĐO ĐƯỢC.

    Không bịa số 0: "không đo" và "không tốn gì" là hai điều khác hẳn nhau, và
    nhầm chúng chính là cách một báo cáo chi phí trở thành hư cấu.
    """
    from app.ai.telemetry import total_tokens, usage_report

    if budget is None:
        return {"do_duoc": False,
                "ly_do": "runner chạy không có ApiBudget — không đếm được"}

    theo_stage = usage_report()
    gop: dict[str, int] = {}
    for vals in theo_stage.values():
        for k, v in vals.items():
            gop[k] = gop.get(k, 0) + v

    return {
        "do_duoc": True,
        "model": model,
        "luot_logic": budget.logical_calls,
        "request_http": budget.http_requests,
        "request_do_retry": budget.retry_requests,
        "lan_gap_429_5xx": budget.transient_hits,
        "tran_logic": budget.max_logical_calls,
        "tran_http": budget.max_api_calls,
        "token_theo_stage": theo_stage,
        "token_gop": gop,
        "tong_token": total_tokens(),
        "do_tre": ghi.do_tre() if ghi else {"so_luot": 0},
        "uoc_tinh_chi_phi": _tien(model, gop),
    }
