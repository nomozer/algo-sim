"""M14 §F2 — observer THỤ ĐỘNG cho run_pipeline (bất biến #22).

Thu event có cấu trúc trong lúc production orchestration chạy — KHÔNG đổi routing/
retry/gate/output. Một observer MỚI cho MỖI case (không tích luỹ xuyên case).
Harness dựng ItemResult TỪ log này + envelope (thay _simulate_with_metrics).
"""

from __future__ import annotations


class AttemptObserver:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def emit(self, event_type: str, data: dict) -> None:
        # THU thuần — không side effect, không trả giá trị ảnh hưởng pipeline.
        self.events.append((event_type, dict(data)))

    # ── accessors (harness dùng) ──────────────────────────────
    def _first(self, t: str) -> dict | None:
        return next((d for (et, d) in self.events if et == t), None)

    def analyze(self) -> dict | None:
        return self._first("analyze_done")

    def plan(self) -> dict | None:
        return self._first("plan_built")

    def classify(self) -> dict | None:
        return self._first("classify_done")

    def envelope(self) -> dict | None:
        return self._first("envelope")

    def family_resolved(self) -> dict | None:
        return self._first("family_resolved")

    def simulate_attempts(self) -> list[dict]:
        return [d for (et, d) in self.events if et == "simulate_attempt"]

    def gates(self) -> list[dict]:
        return [d for (et, d) in self.events if et == "gate_checked"]

    def gap_gate_fired(self) -> bool:
        p = self.plan()
        return bool(p and p.get("unsupported_capabilities"))
