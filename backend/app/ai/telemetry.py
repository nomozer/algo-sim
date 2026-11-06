# -*- coding: utf-8 -*-
"""Ghi token usage theo TỪNG STAGE.

VÌ SAO TỒN TẠI: trước 2026-08-20, `usageMetadata` không được ghi ở bất kỳ đâu
trong backend (spec E12) — nên "tốn ít token" là mong muốn, không phải số. Không
có baseline thì mọi tối ưu đều là cảm tính, và cũng không có gì để báo cáo.

Lấy ĐỦ năm trường: prompt · candidates · cached · total · thoughts. Thiếu
`thoughts` (model không trả) thì đếm 0, KHÔNG được làm hỏng pipeline — telemetry
không bao giờ được là lý do một lượt phân tích thất bại.

Đây là bộ đếm TRONG TIẾN TRÌNH, không bền. Ai cần artifact thì gọi
`usage_report()` rồi tự ghi ra `docs/evaluation/`.
"""
from __future__ import annotations

import contextvars
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Iterator

#: khoá cục bộ → khoá trong `usageMetadata` của Gemini
_FIELDS: dict[str, str] = {
    "prompt_tokens": "promptTokenCount",
    "candidates_tokens": "candidatesTokenCount",
    "cached_content_tokens": "cachedContentTokenCount",
    "total_tokens": "totalTokenCount",
    "thoughts_tokens": "thoughtsTokenCount",
}

_usage: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

#: Stage đang chạy. Dùng ContextVar thay vì tham số của `call_gemini` vì có 13
#: test double của hàm đó — thêm một tham số QUAN TRẮC vào chữ ký làm gãy hết,
#: mà một double gãy vì lý do quan trắc là mùi thiết kế. ContextVar cũng an toàn
#: với async: mỗi task giữ bản sao riêng, và retry bên trong `call_gemini` vẫn
#: nằm đúng stage.
_current_stage: contextvars.ContextVar[str] = contextvars.ContextVar(
    "gemini_stage", default="unknown"
)


@contextmanager
def stage_scope(name: str) -> Iterator[None]:
    """Đánh dấu mọi lượt gọi Gemini bên trong khối này thuộc `name`."""
    token = _current_stage.set(name)
    try:
        yield
    finally:
        _current_stage.reset(token)


def current_stage() -> str:
    return _current_stage.get()


def reset_usage() -> None:
    """Xoá bộ đếm. Gọi ở đầu mỗi lượt đo, và trong test."""
    _usage.clear()


def _as_int(value: Any) -> int:
    """Số lạ/None/chuỗi → 0. Telemetry không được ném lỗi giữa pipeline."""
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


#: Bộ đếm CỦA MỘT REQUEST (middleware `/api/analyze` mở). contextvars đi theo task con và `run_in_threadpool`, nên
#: lượt gọi provider trong luồng worker cộng đúng vào request của nó; hai request chồng nhau không tính token của nhau.
_request_usage: contextvars.ContextVar[dict[str, dict[str, int]] | None] = contextvars.ContextVar(
    "request_usage", default=None)


def begin_request_usage() -> dict[str, dict[str, int]]:
    """Mở bộ đếm riêng cho request hiện tại và trả nó (đọc sau khi request xong)."""
    acc: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    _request_usage.set(acc)
    return acc


def record_usage(stage: str, usage: dict[str, Any] | None) -> None:
    """Cộng dồn `usageMetadata` của một lượt gọi vào bộ đếm của `stage` (toàn tiến trình và của request, nếu có)."""
    if not usage:
        return
    for buckets in (_usage, _request_usage.get()):
        if buckets is None:
            continue
        bucket = buckets[stage]
        for local, remote in _FIELDS.items():
            bucket[local] += _as_int(usage.get(remote))
        bucket["calls"] += 1


def usage_report() -> dict[str, dict[str, int]]:
    """Bản chụp bộ đếm hiện tại, an toàn để ghi ra JSON."""
    return {stage: dict(vals) for stage, vals in _usage.items()}


def total_tokens() -> int:
    """Tổng token toàn lượt — con số duy nhất để so baseline nhanh."""
    return sum(v.get("total_tokens", 0) for v in _usage.values())
