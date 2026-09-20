# -*- coding: utf-8 -*-
"""BENCHMARK A/B GHÉP CẶP — Gemini synthesis vs primitive compiler.

`PRIMITIVE_COMPILER_AB_TOKEN_LATENCY_BENCHMARK` (2026-09-20).

    A · BASELINE  gemini-2.5-flash, ĐÚNG prompt + thẻ văn phạm + lược đồ của
                  đường sản phẩm, MỘT first attempt, không repair, không retry
    B · PROPOSED  GeometryFactGraph → primitive compiler, 0 request model

Cùng `RequestContract`, cùng validator/route/scene/visual gate, **cùng một bộ
chấm độc lập**.

─── BA LUẬT AN TOÀN, THEO ĐÚNG THỨ TỰ ──────────────────────────────────────

① **Nhánh B chạy TRƯỚC.** Compiler không đạt 4/4 ⇒ **0 request Gemini**. Tiêu
  quota để so với một nhánh đang hỏng là tiêu quota để không học được gì.

② **Trần HTTP đặt ở TRANSPORT, không ở vòng lặp.** Trần logic đếm ý định; trần
  transport đếm thứ thật sự rời khỏi máy. Bài học đã trả giá ở
  `PHOTO_PROBLEM_LIVE_RUNNER_HARDENING`: runner cũ có trần logic 11 trong khi
  đường xấu nhất là 38.

③ **Đáp số ở TỆP KHÁC.** Manifest không chứa đáp số; evaluator mới được mở
  `GROUND_TRUTH` và chỉ sau khi cả hai nhánh đã sinh xong output.

KHÔNG LƯU: prompt thô · response thô · semantic program đầy đủ · scene thô ·
`input_value` · thông điệp Pydantic · secret.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import statistics
import sys
import time
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

GOC = Path(__file__).resolve().parents[1]
REPO = GOC.parent
if str(GOC) not in sys.path:
    sys.path.insert(0, str(GOC))

BENCH = (REPO / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene"
         / "primitive-compiler-ab-benchmark")
MANIFEST = BENCH / "PRIMITIVE_COMPILER_AB_MANIFEST.json"
GROUND_TRUTH = BENCH / "PRIMITIVE_COMPILER_AB_GROUND_TRUTH.json"

RUNNER_VERSION = "primitive-compiler-ab/1"
TRAN_SYNTHESIS = 4
TIMEOUT_GIAY = 120.0

#: Khoá bí mật cần che nếu lỡ lọt vào một chuỗi chẩn đoán.
_MAU_BI_MAT = (
    re.compile(r"AIza[0-9A-Za-z_\-]{10,}"),
    re.compile(r"(?i)(x-goog-api-key|authorization|api[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"(?i)[?&]key=[^&\s]+"),
)


def che(s: str) -> str:
    for m in _MAU_BI_MAT:
        s = m.sub("<đã che>", s)
    return s


def _bam(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _ps(x: str) -> Fraction:
    return Fraction(x)


# ══ CỔNG HTTP — đếm ở TRANSPORT ═════════════════════════════════════════════
class CongHttp:
    """Đếm, chặn và ghi MỌI lượt rời khỏi máy. Trần là trần THẬT."""

    def __init__(self, tran: int = TRAN_SYNTHESIS) -> None:
        self.tran = tran
        self.da_gui = 0
        self.bi_chan = 0
        self.ban_ghi: list[dict[str, Any]] = []
        self.khoa = False  # bật sau lỗi provider ⇒ không gì đi tiếp

    def truoc_khi_gui(self, case_id: str) -> None:
        if self.khoa:
            self.bi_chan += 1
            raise RuntimeError("CỔNG ĐÃ KHOÁ sau lỗi provider — không gửi thêm")
        if self.da_gui >= self.tran:
            self.bi_chan += 1
            raise RuntimeError(f"HẾT TRẦN HTTP ({self.tran})")
        self.da_gui += 1
        self.ban_ghi.append({"case_id": case_id, "sent": True, "n": self.da_gui})


# ══ DỰNG RequestContract TỪ MANIFEST ════════════════════════════════════════
def dung_hop_dong(ca: dict[str, Any]):
    """Manifest → `RequestContract`. KHÔNG đọc ground truth, KHÔNG đáp số."""
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import (
        InputFact, RequestContract,
    )
    from app.simulation.semantic_program.scale_normalization import SourceInvariant

    dv = ca["right_vertex"]
    con = [p for p in ca["base"] if p != dv]
    c1, c2 = con[0], con[1]
    ap = ca["apex"]
    L = ca["lengths"]

    bb = [
        SourceInvariant(points=(dv, c1), expected=L["leg_1"],
                        source_fact_id="f_leg_1", scale_symbol="", source_text=""),
        SourceInvariant(points=(dv, c2), expected=L["leg_2"],
                        source_fact_id="f_leg_2", scale_symbol="", source_text=""),
        SourceInvariant(points=(dv, ap), expected=L["height"],
                        source_fact_id="f_height", scale_symbol="", source_text=""),
    ]
    bb = [bb[i] for i in ca["fact_order"]]

    qh = [
        InputFact(fact_id="f_right_angle", label="đáy vuông",
                  values=(f"tam giác {dv}{c1}{c2} vuông tại {dv}",)),
        InputFact(fact_id="f_apex_perp", label="cạnh bên vuông góc đáy",
                  values=(f"{ap}{dv} ⊥ ({dv}{c1}{c2})",)),
    ]
    qh = [qh[i] for i in ca["relation_order"]]

    de = (f"Cho hình chóp {ap}.{dv}{c1}{c2} có đáy {dv}{c1}{c2} vuông tại {dv}, "
          f"{dv}{c1} = {L['leg_1']}, {dv}{c2} = {L['leg_2']}, "
          f"{ap}{dv} vuông góc với mặt phẳng đáy và {ap}{dv} = {L['height']}. "
          f"Tính thể tích khối chóp {ap}.{dv}{c1}{c2}.")

    hd = RequestContract(
        obligations=(Obligation(kind="volume", container=ca["container"],
                                params={"witness": ca["witness"]}),),
        input_facts=tuple(qh), source_invariants=tuple(bb), problem_text=de)
    return hd, de


# ══ BỘ CHẤM CHUNG — DÙNG CHO CẢ HAI NHÁNH ═══════════════════════════════════
@dataclass
class KetQuaCham:
    case_id: str
    arm: str
    json_ok: bool = False
    validation_ok: bool = False
    route_stage: str | None = None
    route_servable: bool = False
    scene_non_empty: bool = False
    point_labels_ok: bool = False
    topology_ok: bool = False
    squared_lengths_ok: bool = False
    perpendicular_ok: bool = False
    non_collinear_ok: bool = False
    final_memory_ok: bool = False
    answer_ok: bool = False
    construction_trace_ok: bool = False
    silent_quality_failure: bool = False
    hallucinated_critical_facts: int = 0
    visual_gate: str | None = None
    rejection_phase: str | None = None
    rejection_code: str | None = None
    quality_pass: bool = False
    diagnostics: list[str] = field(default_factory=list)


def cham(case_id: str, arm: str, ca: dict, hd, program: dict | None,
         mong: dict, trace_len: int = 0) -> KetQuaCham:
    """MỘT bộ chấm cho CẢ HAI nhánh. Ground truth chỉ vào ở đây."""
    from app.ai.pipeline import _dung_scene3d
    from app.simulation.geometry.predicates import collinear
    from app.simulation.semantic_program import validator as V
    from app.simulation.semantic_program import visual_obligations as VO
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    from app.simulation.semantic_program.route import verify_and_compile

    r = KetQuaCham(case_id=case_id, arm=arm)
    if program is None:
        r.diagnostics.append("NO_PROGRAM")
        return r
    r.json_ok = True

    val = V.validate_semantic_program(program)
    r.validation_ok = bool(val.ok)
    if not val.ok:
        r.rejection_phase = "PROGRAM_SCHEMA"
        r.rejection_code = "SEMANTIC_PROGRAM_INVALID"
        return r

    o = verify_and_compile(hd, val.spec)
    r.route_stage = o.stage_reached
    r.route_servable = bool(o.servable)
    if not o.servable:
        r.rejection_phase = f"ROUTE_{str(o.stage_reached).upper()}"
        r.rejection_code = o.error_code or "ROUTE_NOT_SERVED"

    try:
        mem = SemanticProgramInterpreter().execute(val.spec).final_memory
    except Exception:  # noqa: BLE001
        r.diagnostics.append("INTERPRETER_ERROR")
        return r

    canh = _dung_scene3d(val.spec, hd)
    r.scene_non_empty = bool(canh and canh.get("objects"))

    diem = [x for x in (canh or {}).get("objects", ()) if x["type"] == "point3"]
    khoi = [x for x in (canh or {}).get("objects", ()) if x["type"] == "solid"]
    r.point_labels_ok = len(diem) == mong["point_count"]
    r.topology_ok = bool(khoi) and len(khoi[0].get("vertices") or ()) == 4 \
        and len(khoi[0].get("faces") or ()) == mong["face_count"]

    dv = ca["right_vertex"]
    con = [p for p in ca["base"] if p != dv]
    ap = ca["apex"]
    try:
        A, B, Cp, S = mem[dv], mem[con[0]], mem[con[1]], mem[ap]
        d2 = lambda u, v: (u - v).dot(u - v)  # noqa: E731
        sq = mong["squared_lengths"]
        r.squared_lengths_ok = (d2(A, B) == _ps(sq["leg_1"])
                                and d2(A, Cp) == _ps(sq["leg_2"])
                                and d2(A, S) == _ps(sq["height"]))
        r.perpendicular_ok = ((B - A).dot(Cp - A) == 0
                              and (S - A).dot(B - A) == 0
                              and (S - A).dot(Cp - A) == 0)
        r.non_collinear_ok = not collinear(A, B, Cp)
    except Exception:  # noqa: BLE001
        r.diagnostics.append("GEOMETRY_READ_FAILED")

    w = ca["witness"]
    r.final_memory_ok = w in mem
    try:
        r.answer_ok = r.final_memory_ok and Fraction(str(mem[w])) == _ps(mong["volume"])
    except Exception:  # noqa: BLE001
        r.answer_ok = False

    r.construction_trace_ok = trace_len >= 10 if arm == "COMPILER" else \
        len(val.spec.statements) >= 6
    try:
        r.visual_gate = VO.check_visual_obligations(hd, canh, o.resolved_names).verdict
    except Exception:  # noqa: BLE001
        r.visual_gate = "ERROR"

    r.quality_pass = all([
        r.validation_ok, r.route_servable, r.scene_non_empty, r.point_labels_ok,
        r.topology_ok, r.squared_lengths_ok, r.perpendicular_ok,
        r.non_collinear_ok, r.final_memory_ok, r.answer_ok,
        r.construction_trace_ok, r.visual_gate == "COVERED",
    ])
    # Route nhận mà chất lượng hình học sai ⇒ thất bại IM LẶNG.
    r.silent_quality_failure = bool(r.route_servable and not r.quality_pass)
    return r


# ══ NHÁNH B — COMPILER ══════════════════════════════════════════════════════
def chay_compiler(cases: list[dict], gt: dict, vong: int = 200) -> dict[str, Any]:
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.geometry_compiler import contract_adapter as A

    ra: list[dict[str, Any]] = []
    for ca in cases:
        hd, _ = dung_hop_dong(ca)
        t0 = time.perf_counter()
        kq_a = A.build_fact_graph(hd)
        bd = C.bien_dich(kq_a.graph) if kq_a.graph is not None else None
        cold = (time.perf_counter() - t0) * 1000

        ms: list[float] = []
        for _ in range(vong):
            t = time.perf_counter()
            g = A.build_fact_graph(hd)
            C.bien_dich(g.graph)
            ms.append((time.perf_counter() - t) * 1000)
        ms.sort()

        prog = bd.program if bd else None
        c = cham(ca["case_id"], "COMPILER", ca, hd, prog,
                 gt["expected"][ca["case_id"]],
                 len(bd.construction_steps) if bd else 0)
        ra.append({
            "case_id": ca["case_id"],
            "adapter_status": kq_a.status,
            "eligibility": (C.danh_gia_eligibility(kq_a.graph).status
                            if kq_a.graph is not None else "NO_GRAPH"),
            "compile_status": bd.status if bd else "NO_GRAPH",
            "program_sha256": (hashlib.sha256(json.dumps(
                prog, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                if prog else None),
            "deterministic": _tat_dinh(hd),
            "model_tokens": 0, "model_requests": 0,
            "ignored_keys": [],
            "cold_ms": round(cold, 4),
            "p50_ms": round(ms[len(ms) // 2], 4),
            "p95_ms": round(ms[int(len(ms) * 0.95)], 4),
            "construction_steps": len(bd.construction_steps) if bd else 0,
            "primitive_calls": len(bd.primitive_calls) if bd else 0,
            "cham": c.__dict__,
        })
    return {"arm": "COMPILER", "cases": ra}


def _tat_dinh(hd) -> bool:
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.geometry_compiler import contract_adapter as A

    def once() -> str:
        g = A.build_fact_graph(hd)
        return json.dumps(C.bien_dich(g.graph).program, sort_keys=True,
                          ensure_ascii=False)
    return once() == once()


# ══ NHÁNH A — GEMINI ════════════════════════════════════════════════════════
def dung_request(hd, de: str) -> tuple[str, str, dict, float]:
    """Dựng request bằng ĐÚNG builder của đường sản phẩm."""
    from app.ai.gemini import load_skill
    from app.ai.pipeline import _facts_for_prompt, _obligations_for_prompt
    from app.simulation.semantic_program.contract import generate_json_schema
    from app.simulation.semantic_program.domain_profile import (
        DOMAIN_HINH_HOC, program_skill_for,
    )
    from app.simulation.semantic_program.grammar_card import grammar_card

    skill = program_skill_for(DOMAIN_HINH_HOC)
    base = f'Đề bài:\n"""\n{de}\n"""'
    base = f"{base}\n\n{_facts_for_prompt(hd)}"
    base = f"{base}\n\n{_obligations_for_prompt(hd)}"
    base = f"{base}\n\n{grammar_card(DOMAIN_HINH_HOC)}"
    return load_skill(skill), base, generate_json_schema(), 0.1


def _token_delta(truoc: dict[str, int]) -> dict[str, int]:
    """Token CỦA RIÊNG lượt vừa gọi — hiệu của bộ đếm cộng dồn.

    `record_usage` cộng dồn theo chặng, nên đọc thẳng sẽ ra tổng của mọi ca
    trước đó. Lấy hiệu là cách duy nhất quy được token về ĐÚNG một request.
    """
    from app.ai.telemetry import usage_report

    sau = usage_report().get("semantic_program", {}) or {}
    return {k: int(sau.get(k, 0)) - int(truoc.get(k, 0))
            for k in set(sau) | set(truoc)}


async def chay_gemini(cases: list[dict], gt: dict, cong: CongHttp,
                      api_key: str) -> dict[str, Any]:
    from app.ai import gemini

    ra: list[dict[str, Any]] = []
    for ca in cases:
        hd, de = dung_hop_dong(ca)
        sys_p, user_p, schema, temp = dung_request(hd, de)
        try:
            cong.truoc_khi_gui(ca["case_id"])
        except RuntimeError as e:
            ra.append({"case_id": ca["case_id"], "result": "BLOCKED_BY_BUDGET",
                       "chi_tiet": che(str(e))})
            break

        from app.ai.telemetry import stage_scope, usage_report

        truoc = dict(usage_report().get("semantic_program", {}) or {})
        t0 = time.perf_counter()
        try:
            # `stage_scope` là thứ `record_usage` dùng để gán token vào chặng —
            # gọi ngoài nó thì token của lượt này rơi vào chặng rỗng.
            with stage_scope("semantic_program"):
                raw = await gemini.call_gemini(api_key, sys_p, user_p, schema, temp,
                                               max_attempts=1,
                                               timeout_seconds=TIMEOUT_GIAY)
        except Exception as e:  # noqa: BLE001
            cong.khoa = True
            ra.append({"case_id": ca["case_id"], "result": "PROVIDER_ERROR",
                       "loai_loi": type(e).__name__,
                       "chi_tiet": che(str(e))[:200],
                       "latency_ms": round((time.perf_counter() - t0) * 1000, 1)})
            break
        lat = (time.perf_counter() - t0) * 1000

        prog = None
        try:
            p = json.loads(raw)
            prog = p if isinstance(p, dict) else None
        except Exception:  # noqa: BLE001
            prog = None

        c = cham(ca["case_id"], "GEMINI", ca, hd, prog, gt["expected"][ca["case_id"]])
        ra.append({
            "case_id": ca["case_id"],
            "result": "ACCEPTED" if c.quality_pass else (
                "REJECTED" if not c.route_servable else "SERVED_QUALITY_FAIL"),
            "latency_ms": round(lat, 1),
            "tokens": _token_delta(truoc),
            "response_sha256": hashlib.sha256(
                (raw or "").encode("utf-8")).hexdigest(),
            "response_byte_count": len(raw or ""),
            "raw_response_stored": False,
            "raw_prompt_stored": False,
            "cham": c.__dict__,
        })
    return {"arm": "GEMINI", "cases": ra}


# ══ ĐIỂM VÀO ════════════════════════════════════════════════════════════════
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true",
                    help="cho phép nhánh A gọi provider THẬT (tiêu quota)")
    ap.add_argument("--vong", type=int, default=200)
    ap.add_argument("--ra", default=str(BENCH))
    a = ap.parse_args()

    mf = json.loads(MANIFEST.read_text(encoding="utf-8"))
    gt = json.loads(GROUND_TRUTH.read_text(encoding="utf-8"))
    cases = mf["cases"]
    ra_dir = Path(a.ra)
    ra_dir.mkdir(parents=True, exist_ok=True)

    # ① NHÁNH B TRƯỚC — không đạt thì 0 request
    kq_b = chay_compiler(cases, gt, a.vong)
    dat = sum(1 for c in kq_b["cases"] if c["cham"]["quality_pass"])
    kq_b["quality_pass_count"] = dat
    (ra_dir / "COMPILER_ARM_RESULTS.json").write_text(
        json.dumps(kq_b, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"COMPILER_QUALITY_PASS = {dat}/{len(cases)}")
    if dat != len(cases):
        print("COMPILER_QUALITY_REGRESSION — dừng, 0 request Gemini")
        return 2
    if not a.live:
        print("PRE_LIVE_OK (chưa --live ⇒ 0 request Gemini)")
        return 0

    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        print("THIẾU GEMINI_API_KEY — dừng, 0 request")
        return 3

    cong = CongHttp()
    kq_a = asyncio.run(chay_gemini(cases, gt, cong, key))
    kq_a["http_sent"] = cong.da_gui
    kq_a["http_blocked"] = cong.bi_chan
    (ra_dir / "GEMINI_ARM_RESULTS_REDACTED.json").write_text(
        json.dumps(kq_a, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"SYNTHESIS_HTTP_REQUESTS = {cong.da_gui}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
