# -*- coding: utf-8 -*-
"""Chứng nhận công cụ G05 real-model pilot bằng PROVIDER GIẢ. offline · **0 API call**.

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/certify_g05_real_model_pilot.py --out <tệp>

Provider giả ĐÓNG VAI mô hình hoàn hảo: với mỗi đề, chặng `semantic_analyze` trả đúng payload `analyze` và chặng
`semantic_program` trả đúng chương trình mà corpus VIẾT TAY của run gốc đã dùng (`regular-prisms`,
`regular-hexagonal-pyramid` qua `diagnostics/cases.py`; `exact-dimensions` qua `tests/geometry/test_exact_dimensions`).
Nó đi qua ĐÚNG đường live: `GacCong` → `stage_semantic_*` thật → `run_pipeline` thật, ghi `ApiBudget` (lượt logic +
lần thử HTTP) và `usageMetadata` giả như provider thật. Mọi thứ sau provider — hợp đồng, cổng, kernel, Scene3D — là THẬT.

Chứng nhận KHÔNG nói gì về Gemini thật: nó chỉ chứng minh bộ đo chấm đúng khi mô hình đúng, và phân biệt được lỗi
provider / lỗi lược đồ / dừng ngân sách với từ chối đúng (tiêm lỗi).
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
RUNS = ROOT / "docs" / "evaluation" / "geometry" / "runs"
USAGE_GIA = {"promptTokenCount": 1000, "candidatesTokenCount": 200, "thoughtsTokenCount": 300,
             "cachedContentTokenCount": 50, "totalTokenCount": 1500}


def _nap(ten: str, duong: Path):
    spec = importlib.util.spec_from_file_location(ten, duong)
    m = importlib.util.module_from_spec(spec)
    sys.modules[ten] = m                       # dataclass cần module đã đăng ký
    spec.loader.exec_module(m)
    return m


R = _nap("_g05c_runner", Path(__file__).resolve().parent / "run_g05_real_model_pilot.py")
SR = _nap("_g05c_replay", Path(__file__).resolve().parent / "g05_pilot_scene_replay.py")


def dap_an_corpus(cases: list[dict]) -> dict[str, dict[str, str]]:
    """Đề → {"analyze": JSON payload, "program": JSON chương trình} lấy từ corpus viết tay của run gốc."""
    from app.simulation.semantic_program import analyze_contract as AC
    from app.simulation.semantic_program.contract import SemanticProgramSpec

    goc = AC.build_request_contract
    bat: dict[str, Any] = {}

    def _bat(payload, *a, **k):
        bat["payload"] = json.loads(json.dumps(payload))
        return goc(payload, *a, **k)

    ra: dict[str, dict[str, str]] = {}
    AC.build_request_contract = _bat
    try:
        from tests.geometry import route_cases as W
        from tests.geometry import test_exact_dimensions as ED

        goc_w = W.build_request_contract
        W.build_request_contract = _bat
        try:
            mod: dict[str, Any] = {}
            for c in cases:
                run, row = c["source"]["run"], c["source"]["row"]
                bat.clear()
                if run == "exact-dimensions":
                    _ct, prog = ED.chuong_trinh(row)
                    spec = SemanticProgramSpec.model_validate(prog)
                else:
                    if run not in mod:
                        mod[run] = _nap(f"_g05c_cases_{run.replace('-', '_')}", RUNS / run / "diagnostics" / "cases.py")
                    _ct, spec = mod[run].hop_dong_va_chuong_trinh(row)
                ra[c["problem_text"]] = {"analyze": json.dumps(bat["payload"], ensure_ascii=False),
                                         "program": json.dumps(spec.model_dump(mode="json", exclude_none=True),
                                                               ensure_ascii=False)}
        finally:
            W.build_request_contract = goc_w
    finally:
        AC.build_request_contract = goc
    return ra


class ProviderGia:
    """Thay `gemini.call_gemini`. Ghi ngân sách + usage như provider thật; tiêm lỗi theo tham số."""

    def __init__(self, dap_an: dict[str, dict[str, str]], usage: dict | None = USAGE_GIA, loi_moi_luot: bool = False,
                 chen_khoa: str | None = None, loi_cho: set[str] = frozenset(),
                 hong_chuong_trinh_cho: set[str] = frozenset()) -> None:
        self.dap_an, self.usage, self.loi_moi_luot, self.chen_khoa = dap_an, usage, loi_moi_luot, chen_khoa
        self.loi_cho, self.hong = set(loi_cho), set(hong_chuong_trinh_cho)
        self.goi = 0

    async def __call__(self, api_key: str, system_prompt: str, user_text: str, response_schema: dict | None = None,
                       temperature: float = 0.2, image: dict | None = None, max_attempts: int | None = None,
                       timeout_seconds: float | None = None) -> str:
        from app.ai import gemini, telemetry

        if gemini.BUDGET:
            gemini.BUDGET.note_call()
            gemini.BUDGET.note_request(is_retry=False)
        self.goi += 1
        de = max((t for t in self.dap_an if t in user_text), key=len)
        if self.loi_moi_luot or de in self.loi_cho:
            them = f" (POST …:generateContent?key={self.chen_khoa})" if self.chen_khoa else ""
            raise RuntimeError(f"Gemini API lỗi HTTP 400: INVALID_ARGUMENT{them}")
        telemetry.record_usage(telemetry.current_stage(), self.usage)
        if telemetry.current_stage() == "semantic_analyze":
            return self.dap_an[de]["analyze"]
        return "{chương trình hỏng" if de in self.hong else self.dap_an[de]["program"]


def chung_nhan(thu_muc: Path) -> dict:
    """16 hàng + tiêm lỗi + dựng lại cảnh. Trả bản ghi chứng nhận (không có khoá thật nào được dùng)."""
    khoa = "FAKEKEY-CERTIFY-SENTINEL-41d2"
    cases = R.nap_corpus()
    dap_an = dap_an_corpus(cases)
    out = Path(thu_muc) / "pilot"
    fake = ProviderGia(dap_an)
    s = asyncio.run(R.chay_pilot(cases, out, fake, khoa, R.CAPS_APPROVED, run_id="certify"))
    replay = SR.kiem_tat_ca(out, cases)

    am = next(c for c in cases if c["id"] == "NX1")
    t1 = asyncio.run(R.chay_pilot([am], Path(thu_muc) / "loi_provider",
                                  ProviderGia(dap_an, loi_cho={am["problem_text"]}, chen_khoa=khoa), khoa,
                                  R.CAPS_APPROVED, run_id="certify-provider-error"))
    t2 = asyncio.run(R.chay_pilot([am], Path(thu_muc) / "hong_schema",
                                  ProviderGia(dap_an, hong_chuong_trinh_cho={am["problem_text"]}), khoa,
                                  R.CAPS_APPROVED, run_id="certify-schema"))
    lai = ProviderGia(dap_an)
    asyncio.run(R.chay_pilot(cases, out, lai, khoa, R.CAPS_APPROVED, run_id="certify"))
    return {
        **R.MEASUREMENT, "provider": "FAKE (corpus hand-written programs) — 0 Gemini calls",
        "pilot": {"summary": s, "out_dir": str(out)},
        "scene_replay": replay,
        "fault_injection": {
            "provider_error_on_negative": t1["theo_hang"]["NX1"],
            "schema_invalid_on_negative": t2["theo_hang"]["NX1"],
            "resume_provider_calls": lai.goi,
            "leak_in_artifacts": bool(R.quet_khoa(Path(thu_muc), khoa)),
        },
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", required=True, help="tệp CERTIFICATION.json")
    p.add_argument("--scenes", default=None, help="chép cảnh đã dựng lại tới đây (cho kiểm biến đổi renderer)")
    a = p.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="g05cert_"))
    try:
        kq = chung_nhan(tmp)
        if a.scenes:
            shutil.copytree(tmp / "pilot" / "scenes", a.scenes, dirs_exist_ok=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    kq["pilot"]["out_dir"] = kq["pilot"]["summary"]["out_dir"] = "<thư mục tạm, đã xoá>"
    Path(a.out).write_text(json.dumps(kq, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    s = kq["pilot"]["summary"]
    print(json.dumps({"dem": s["dem"], "scene_replay": {k: kq["scene_replay"][k] for k in ("checked", "ok")},
                      "fault_injection": kq["fault_injection"]}, ensure_ascii=False))
    ok = (s["dem"] == {"SERVED_CORRECT": 10, "REFUSED_CORRECT": 6} and kq["scene_replay"]["ok"] == 10
          and kq["fault_injection"] == {"provider_error_on_negative": "PROVIDER_ERROR",
                                        "schema_invalid_on_negative": "PARSER_SCHEMA_ERROR",
                                        "resume_provider_calls": 0, "leak_in_artifacts": False})
    print("CERTIFIED" if ok else "CERTIFICATION_FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
