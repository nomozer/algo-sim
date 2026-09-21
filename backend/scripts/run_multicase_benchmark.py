# -*- coding: utf-8 -*-
"""BENCHMARK 12 CA — kiến trúc `đề → Analyze → FactGraph → compiler → cảnh`.

`MULTICASE_STRUCTURED_ANALYZE_COMPILER_BENCHMARK` (2026-09-21).

─── CÂU HỎI ────────────────────────────────────────────────────────────────

Lượt tái kiểm trước đạt trên **một** ca — và là chính ca đã dùng để chẩn đoán.
Wave này hỏi câu còn lại: kiến trúc có tổng quát không, trên 12 ca chưa từng
dùng để chẩn đoán hay sửa prompt.

Gemini chỉ làm MỘT việc: đọc đề thành dữ liệu có cấu trúc. Nó **không** viết
chương trình, không chọn toạ độ, không dựng cảnh, không tính đáp số, không được
gọi làm phương án thay thế khi compiler từ chối.

─── HAI GIAI ĐOẠN, CÓ CỔNG DỪNG ────────────────────────────────────────────

Giai đoạn A chạy 4 ca (3 positive + 1 negative). Giai đoạn B chỉ mở khi A đạt
ngưỡng đã đăng ký TRƯỚC. Mục đích không phải tiết kiệm quota mà là **không
tiêu 12 request cho một hệ đã hỏng ở ca thứ hai**.

─── HAI TẦNG NGÂN SÁCH, CỐ Ý ───────────────────────────────────────────────

Một `CongQuetCam` cho CẢ wave (trần 12, `{vision: 0, analyze: 12, synthesis: 0}`)
— nó là sổ kế toán duy nhất, và nó chặn request thứ 13. Cộng thêm một
`ApiBudget` MỚI cho mỗi ca (trần 1) — nó chặn request thứ hai của cùng một ca.
Một tầng không thay được tầng kia: trần tổng không biết ca nào đang chạy, còn
trần ca không biết tổng đã tiêu bao nhiêu.

─── GHÉP CA KHÔNG ĐƯỢC LỆCH ────────────────────────────────────────────────

Mỗi bản ghi request mang `case_id` do cổng đóng dấu lúc gửi. Token và độ trễ
của một ca **chỉ** lấy từ bản ghi mang đúng `case_id` ấy — không lấy "bản ghi
cuối cùng", vì đó đúng là cách một chỉ số nhảy sang ca khác mà không ai thấy.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path
from typing import Any

GOC = Path(__file__).resolve().parents[1]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import httpx  # noqa: E402

from app.ai import gemini  # noqa: E402

from run_photo_problem_live import (  # noqa: E402
    BoKhuBiMat, KenhIn, _bay_gio, _chuoi_loi, _ghi_json, _sha,
)
import run_structured_relation_analyze_live as L  # noqa: E402
import run_structured_relation_revalidation as V  # noqa: E402

WAVE = "MULTICASE_STRUCTURED_ANALYZE_COMPILER_BENCHMARK"
RUNNER_VERSION = "multicase-structured-benchmark/1"
EVALUATOR_VERSION = "multicase-evaluator/1"

RA = (REPO / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene"
      / "multicase-benchmark")
REGISTRY = RA / "CASE_REGISTRY.json"
GROUND_TRUTH = RA / "GROUND_TRUTH.json"

TRAN_TONG = 12
TRAN_THEO_TANG = {"vision": 0, "analyze": TRAN_TONG, "synthesis": 0}
TRAN_MOI_CA = 1

#: Ngưỡng mở giai đoạn B — đăng ký TRƯỚC, không đổi sau khi thấy kết quả.
NGUONG_STAGE_A = {"positive_full_pipeline_min": 2, "positive_run": 3,
                  "negative_safe_required": 1}

KET_QUA = ("READY_FOR_CANARY_DESIGN", "STRONG_PILOT_RESULT", "MORE_EVIDENCE_NEEDED",
           "NOT_READY", "PROVIDER_INCOMPLETE", "MEASUREMENT_INVALID")
NEXT_THEO_KET_QUA = {
    "READY_FOR_CANARY_DESIGN": "PRIMITIVE_COMPILER_OPT_IN_CANARY_ROUTING_DESIGN",
    "STRONG_PILOT_RESULT": "PRIMITIVE_COMPILER_OPT_IN_CANARY_ROUTING_DESIGN",
    "MORE_EVIDENCE_NEEDED": "DEFINITIONAL_RELATION_DETERMINISTIC_NORMALIZER_DESIGN",
    "NOT_READY": "STRUCTURED_RELATION_SAFETY_GATE_HARDENING",
    "PROVIDER_INCOMPLETE": "RETRY_REMAINING_PREREGISTERED_CASES_LATER",
    "MEASUREMENT_INVALID": "MULTICASE_BENCHMARK_MEASUREMENT_REPAIR",
}
EXIT_PASS, EXIT_FAIL, EXIT_PRECHECK = 0, 1, 2


def doc_registry() -> dict[str, Any]:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def doc_ground_truth() -> dict[str, Any]:
    return json.loads(GROUND_TRUTH.read_text(encoding="utf-8"))


def ca_theo_id(reg: dict) -> dict[str, dict]:
    return {c["case_id"]: c for c in reg["cases"]}


def thu_tu_chay(reg: dict) -> list[str]:
    return list(reg["stage_a_order"]) + list(reg["stage_b_order"])


def canonical_dataset_sha(reg: dict, gt: dict) -> str:
    """Băm CHÍNH TẮC của toàn bộ dataset — đề + đáp án + thứ tự."""
    can = json.dumps({"order": thu_tu_chay(reg),
                      "cases": [{"id": c["case_id"], "kind": c["kind"],
                                 "input": c["input_text"]} for c in reg["cases"]],
                      "ground_truth": gt}, sort_keys=True, ensure_ascii=False)
    return _sha(can)


# ══ CHẤM ANALYZE — §8 ══════════════════════════════════════════════════════
def so_quan_he(contract: Any, mong_given: list[dict], mong_suy: list[dict]
               ) -> dict[str, Any]:
    """So quan hệ của MỘT ca. Dùng lại bộ chuẩn hoá của sản phẩm."""
    from app.simulation.semantic_program.structured_relations import (
        MA_REFERENCE_UNKNOWN, diem_hop_dong, kiem_va_chuan_hoa,
    )
    tho = tuple(getattr(contract, "geometric_relations", None) or ())
    kq = kiem_va_chuan_hoa(contract)
    mong = {(m["kind"], tuple(m["canonical_args"])) for m in mong_given}
    suy = {(m["kind"], tuple(m["canonical_args"])) for m in mong_suy}
    thuc = {q.khoa for q in kq.relations}
    thieu = sorted(mong - thuc)
    thua = sorted(thuc - mong)
    thua_suy = [k for k in thua if k in suy]
    thua_khong = [k for k in thua if k not in suy]
    trung = max(0, len(tho) - len(kq.loi) - len({q.khoa for q in kq.relations}))
    chua_truy = [{"kind": q.kind, "args": list(q.args),
                  "source_fact_id": q.source_fact_id}
                 for q in kq.relations
                 if not q.source_fact_id or contract.fact(q.source_fact_id) is None]
    return {
        "CONTRACT_POINT_LABELS": sorted(diem_hop_dong(contract)),
        "RAW_RELATION_COUNT": len(tho),
        "EXPECTED_GIVEN_RELATION_COUNT": len(mong),
        "ACTUAL_GIVEN_RELATION_COUNT": sum(
            1 for q in kq.relations if q.dung_duoc_cho_tang_dung()),
        "CORRECT_CRITICAL_RELATION_COUNT": len(mong & thuc),
        "CRITICAL_RELATION_ACCURACY": round(len(mong & thuc) / len(mong), 4) if mong else 0.0,
        "MISSING_RELATION_COUNT": len(thieu),
        "MISSING_RELATIONS": [{"kind": k[0], "args": list(k[1])} for k in thieu],
        "DUPLICATE_RELATION_COUNT": trung,
        "UNVERIFIED_EXTRA_RELATION_COUNT": len(thua_khong),
        "UNVERIFIED_EXTRA_RELATIONS": [{"kind": k[0], "args": list(k[1])}
                                       for k in thua_khong],
        "EXTRA_DERIVED_AS_GIVEN_COUNT": len(thua_suy),
        "EXTRA_DERIVED_AS_GIVEN": [{"kind": k[0], "args": list(k[1])} for k in thua_suy],
        "MODEL_ASSUMPTION_COUNT": sum(
            1 for r in tho if bool(getattr(r, "model_assumption", False))),
        "REJECTED_RELATION_CODES": [{"code": e.ma, "kind": e.kind, "index": e.chi_so}
                                    for e in kq.loi],
        "POINT_REFERENCE_VALIDATION": "FAIL" if any(
            e.ma == MA_REFERENCE_UNKNOWN for e in kq.loi) else "PASS",
        "SOURCE_FACT_RESOLUTION": "FAIL" if chua_truy else "PASS",
        "SOURCE_FACT_UNRESOLVED": chua_truy,
        "RELATIONS": [{"kind": q.kind, "canonical_args": list(q.args),
                       "source_fact_id": q.source_fact_id,
                       "model_assumption": q.model_assumption,
                       "usable_by_construction": q.dung_duoc_cho_tang_dung(),
                       "matches_ground_truth": q.khoa in mong,
                       "is_derivable_relation": q.khoa in suy}
                      for q in kq.relations],
    }


#: Quy kết TẦNG nào làm một ca positive trượt. Không có nó thì mọi thất bại
#: đều đọc thành "mô hình sai", và đó là kết luận sai với ít nhất một ca đã
#: biết trước (xem `LIVE_RUN_MANIFEST.known_stressors`).
QUY_KET = (
    "MODEL_UNDER_DECLARED",        # mô hình không khai quan hệ đáng lẽ phải khai
    "MODEL_UNSAFE_DECLARATION",    # khai thừa / giả định / hệ quả thành GIVEN
    "SERVER_POINT_BINDING_GAP",    # quan hệ ĐÃ khai nhưng điểm không vào hợp đồng
    "COMPILER_UNSUPPORTED",        # Analyze đủ, họ bài ngoài phạm vi compiler
    "BUILD_GATE_FAILED",           # compiler chạy nhưng một cổng chất lượng đỏ
    "ANALYZE_OUTPUT_INVALID",
)


def quy_ket_that_bai(ss: dict[str, Any], contract: Any) -> str:
    """Tầng nào chịu trách nhiệm — ĐỌC bằng chứng, không đoán.

    Phân biệt đắt nhất ở đây: *"mô hình không khai"* với *"mô hình có khai mà
    server không nhận vì một điểm chưa vào `source_invariants`"*. Hai thứ ấy
    trông giống nhau trên bảng số (`MISSING_RELATION_COUNT = 1`) nhưng đòi hai
    bản sửa ở hai tầng khác nhau.
    """
    from app.simulation.semantic_program.structured_relations import (
        MA_REFERENCE_UNKNOWN, diem_hop_dong,
    )
    if ss["MODEL_ASSUMPTION_COUNT"] or ss["EXTRA_DERIVED_AS_GIVEN_COUNT"] \
            or ss["UNVERIFIED_EXTRA_RELATION_COUNT"] \
            or ss["SOURCE_FACT_RESOLUTION"] != "PASS":
        return "MODEL_UNSAFE_DECLARATION"
    if any(e["code"] == MA_REFERENCE_UNKNOWN for e in ss["REJECTED_RELATION_CODES"]):
        # Mô hình ĐÃ khai quan hệ; nó bị bác vì một nhãn điểm chưa có trong
        # `source_invariants` — tức server chưa neo được độ dài của điểm ấy.
        biet = diem_hop_dong(contract)
        nhac = {p for r in (getattr(contract, "geometric_relations", None) or ())
                for p in (*(r.line or ()), *(r.other_line or ()), *(r.plane or ()))}
        return "SERVER_POINT_BINDING_GAP" if (nhac - biet) else "MODEL_UNSAFE_DECLARATION"
    if ss["MISSING_RELATION_COUNT"]:
        return "MODEL_UNDER_DECLARED"
    return "MODEL_UNSAFE_DECLARATION"


def analyze_dat(ss: dict[str, Any]) -> bool:
    return bool(
        ss["MISSING_RELATION_COUNT"] == 0
        and ss["ACTUAL_GIVEN_RELATION_COUNT"] == ss["EXPECTED_GIVEN_RELATION_COUNT"]
        and ss["CRITICAL_RELATION_ACCURACY"] == 1.0
        and ss["DUPLICATE_RELATION_COUNT"] == 0
        and ss["UNVERIFIED_EXTRA_RELATION_COUNT"] == 0
        and ss["EXTRA_DERIVED_AS_GIVEN_COUNT"] == 0
        and ss["MODEL_ASSUMPTION_COUNT"] == 0
        and ss["SOURCE_FACT_RESOLUTION"] == "PASS"
        and ss["POINT_REFERENCE_VALIDATION"] == "PASS"
        and not ss["REJECTED_RELATION_CODES"])


# ══ TẦNG DỰNG — §9. HOÀN TOÀN OFFLINE ══════════════════════════════════════
def chay_tang_dung(contract: Any, ca: dict, g: dict) -> dict[str, Any]:
    """FactGraph → compiler → mọi cổng → cảnh → đáp số. 0 lượt gọi model."""
    from app.ai.pipeline import _dung_scene3d, _envelope_tu_route_sinh
    from app.simulation.geometry.predicates import collinear
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.geometry_compiler import contract_adapter as A
    from app.simulation.semantic_program import validator as Va
    from app.simulation.semantic_program import visual_obligations as VO
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    from app.simulation.semantic_program.route import verify_and_compile

    t0 = time.perf_counter()
    ka = A.build_fact_graph(contract)
    ms_graph = (time.perf_counter() - t0) * 1000
    r: dict[str, Any] = {"ADAPTER_STATUS": ka.status,
                         "ADAPTER_REASON_CODE": ka.reason_code,
                         "FACT_GRAPH_LATENCY_MS": round(ms_graph, 4),
                         "COMPILER_MODEL_TOKENS": 0, "SYNTHESIS_REQUESTS": 0}
    if ka.graph is None:
        r.update(COMPILER_ELIGIBILITY="NO_GRAPH", COMPILE_STATUS="NO_GRAPH",
                 REJECTION_CODE=ka.reason_code or ka.status)
        return r
    gr = ka.graph
    derived = [f for f in gr.facts if f.status == "DERIVED"]
    perp_d = [f for f in derived if f.kind == "perpendicular_lines"]
    mong_suy = {(m["kind"], tuple(m["canonical_args"]))
                for m in g.get("expected_derived_perpendicular", [])}
    r.update({
        "FACT_GRAPH_GIVEN_COUNT": sum(1 for f in gr.facts if f.status == "GIVEN"),
        "FACT_GRAPH_DERIVED_COUNT": len(derived),
        "DERIVED_PERPENDICULAR_COUNT": len(perp_d),
        "DERIVED_PERPENDICULAR_MATCHES_GROUND_TRUTH":
            {(f.kind, tuple(f.args)) for f in perp_d} == mong_suy,
        "EVERY_DERIVED_RELATION_HAS_PROVENANCE":
            all(bool(f.derived_from) for f in perp_d),
    })
    el = C.danh_gia_eligibility(gr)
    r["COMPILER_ELIGIBILITY"] = el.status
    r["COMPILER_ELIGIBILITY_REASON"] = el.reason_code
    if el.binding is None:
        r.update(COMPILE_STATUS="NOT_ELIGIBLE",
                 REJECTION_CODE=el.reason_code or el.status)
        return r
    b = el.binding
    t1 = time.perf_counter()
    bd = C.bien_dich(gr)
    r["COMPILER_LATENCY_MS"] = round((time.perf_counter() - t1) * 1000, 4)
    r.update({"COMPILE_STATUS": bd.status, "COMPILE_REASON_CODE": bd.reason_code,
              "CONSTRUCTION_STEPS": len(bd.construction_steps),
              "PRIMITIVE_CALLS": len(bd.primitive_calls),
              "WITNESS_OBSERVED": b.witness, "CONTAINER_OBSERVED": b.container,
              "PROGRAM_SHA256": (_sha(json.dumps(bd.program, sort_keys=True,
                                                 ensure_ascii=False))
                                 if bd.program else None)})
    if bd.program is None:
        r["REJECTION_CODE"] = bd.reason_code or bd.status
        return r
    # tất định: biên dịch hai lần phải trùng byte
    r["DETERMINISTIC"] = (json.dumps(C.bien_dich(A.build_fact_graph(contract).graph)
                                     .program, sort_keys=True, ensure_ascii=False)
                          == json.dumps(bd.program, sort_keys=True, ensure_ascii=False))

    val = Va.validate_semantic_program(bd.program)
    r["PYDANTIC_PROGRAM_VALIDATION"] = "PASS" if val.ok else "FAIL"
    if not val.ok:
        r["REJECTION_CODE"] = "SEMANTIC_PROGRAM_INVALID"
        return r
    o = verify_and_compile(contract, val.spec)
    r.update({"TYPE_CHECK": "PASS", "IR_STATIC_CHECK": "PASS",
              "GROUNDING_GATE": "PASS" if o.servable else "SEE_ROUTE",
              "ROUTE_RESULT": "served" if o.servable else f"rejected/{o.error_code}"})
    mem = SemanticProgramInterpreter().execute(val.spec).final_memory
    canh = _dung_scene3d(val.spec, contract)
    o2 = o.model_copy(update={"scene3d": canh}) if canh else o
    env = _envelope_tu_route_sinh(o2, {}, {}, None)
    r["ENVELOPE_SHA256"] = _sha(json.dumps(env, sort_keys=True, ensure_ascii=False))
    r["_ENVELOPE"] = env
    try:
        r["VISUAL_OBLIGATION_GATE"] = VO.check_visual_obligations(
            contract, canh, o.resolved_names).verdict
    except Exception:  # noqa: BLE001
        r["VISUAL_OBLIGATION_GATE"] = "ERROR"

    vat = (canh or {}).get("objects", ())
    diem = [x for x in vat if x["type"] == "point3"]
    khoi = [x for x in vat if x["type"] == "solid"]
    r["SCENE_NON_EMPTY"] = bool(vat)
    r["SCENE_POINT_COUNT"] = len(diem)
    r["SCENE_SOLID_VERTEX_COUNT"] = len(khoi[0].get("vertices") or ()) if khoi else 0
    r["SCENE_SOLID_FACE_COUNT"] = len(khoi[0].get("faces") or ()) if khoi else 0
    r["SCENE_SOLID_EDGE_COUNT"] = (
        len({tuple(sorted((m[i], m[(i + 1) % len(m)])))
             for m in (khoi[0].get("faces") or ()) for i in range(len(m))})
        if khoi else 0)
    r["TOPOLOGY_RESULT"] = "PASS" if (
        len(diem) == g["point_count"] and khoi
        and r["SCENE_SOLID_VERTEX_COUNT"] == g["point_count"]
        and r["SCENE_SOLID_FACE_COUNT"] == g["face_count"]
        and r["SCENE_SOLID_EDGE_COUNT"] == g["edge_count"]) else "FAIL"

    rv, a, bb, ap = (ca["labels"]["right_vertex"], ca["labels"]["leg_1_end"],
                     ca["labels"]["leg_2_end"], ca["labels"]["apex"])
    try:
        P, Qa, Qb, S = mem[rv], mem[a], mem[bb], mem[ap]
        d2 = lambda u, v: (u - v).dot(u - v)  # noqa: E731
        sq = g["squared_lengths"]
        r["SQUARED_LENGTHS_OK"] = (d2(P, Qa) == Fraction(sq["leg_1"])
                                   and d2(P, Qb) == Fraction(sq["leg_2"])
                                   and d2(P, S) == Fraction(sq["height"]))
        r["PERPENDICULAR_OK"] = ((Qa - P).dot(Qb - P) == 0
                                 and (S - P).dot(Qa - P) == 0
                                 and (S - P).dot(Qb - P) == 0)
        r["NON_COLLINEAR_OK"] = not collinear(P, Qa, Qb)
    except Exception:  # noqa: BLE001
        r["SQUARED_LENGTHS_OK"] = r["PERPENDICULAR_OK"] = r["NON_COLLINEAR_OK"] = False
    w = b.witness
    r["FINAL_MEMORY_OK"] = w in mem
    try:
        r["ANSWER_OK"] = r["FINAL_MEMORY_OK"] and Fraction(str(mem[w])) == Fraction(g["volume"])
    except Exception:  # noqa: BLE001
        r["ANSWER_OK"] = False
    r["FULL_PIPELINE_PASS"] = all([
        r["COMPILER_ELIGIBILITY"] == "SUPPORTED", r["COMPILE_STATUS"] == "COMPILED",
        r.get("DETERMINISTIC"), r["PYDANTIC_PROGRAM_VALIDATION"] == "PASS",
        r["ROUTE_RESULT"] == "served", r["VISUAL_OBLIGATION_GATE"] == "COVERED",
        r["SCENE_NON_EMPTY"], r["TOPOLOGY_RESULT"] == "PASS",
        r["SQUARED_LENGTHS_OK"], r["PERPENDICULAR_OK"], r["NON_COLLINEAR_OK"],
        r["FINAL_MEMORY_OK"], r["ANSWER_OK"],
        r["DERIVED_PERPENDICULAR_MATCHES_GROUND_TRUTH"],
        r["EVERY_DERIVED_RELATION_HAS_PROVENANCE"]])
    r["SILENT_QUALITY_FAILURE"] = bool(
        r["ROUTE_RESULT"] == "served" and not r["FULL_PIPELINE_PASS"])
    return r


# ══ MỘT CA ═════════════════════════════════════════════════════════════════
async def chay_mot_ca(ca: dict, gt: dict, key: str, cong: Any) -> dict[str, Any]:
    from app.ai import pipeline as PL
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC

    cid = ca["case_id"]
    cong.dat_ca(cid)
    budget = gemini.ApiBudget(max_api_calls=TRAN_MOI_CA, max_attempts=1,
                              max_logical_calls=1)
    t0 = time.perf_counter()
    hd, err, no = None, None, None
    with L.cai_cong_http(cong), L.dung_ngan_sach(budget):
        try:
            hd, err = await PL.stage_semantic_analyze(ca["input_text"], key,
                                                      domain=DOMAIN_HINH_HOC)
        except Exception as e:  # noqa: BLE001
            no = _chuoi_loi(e)
    latency = round((time.perf_counter() - t0) * 1000, 1)

    # GHÉP CA theo `case_id` của chính bản ghi — không lấy "bản ghi cuối".
    ban_ghi = [x for x in cong.records if x["case_id"] == cid]
    usage = next((x.get("usage_metadata") for x in ban_ghi if x.get("usage_metadata")),
                 None) or {}
    r: dict[str, Any] = {
        "CASE_ID": cid, "KIND": ca["kind"],
        "WORDING_CLASS": ca.get("wording_class") or ca.get("defect"),
        "HTTP_REQUESTS_FOR_CASE": len([x for x in ban_ghi if x["sent"]]),
        "HTTP_STATUS": ban_ghi[-1]["http_status"] if ban_ghi else None,
        "LATENCY_MS": latency,
        "ANALYZE_ERROR": err, "RUNNER_EXCEPTION": no,
        "MODEL_OUTPUT_RECEIVED": hd is not None,
        "JSON_PARSE_RESULT": "FAIL" if (err and "JSON" in err) else (
            "PASS" if hd is not None else "UNKNOWN"),
        "PYDANTIC_VALIDATION_RESULT": "PASS" if hd is not None else "FAIL",
        "REQUEST_CONTRACT_VALIDATION": "PASS" if hd is not None else "FAIL",
        "USAGE": usage,
        "PROVIDER_ERROR": cong.provider_error,
    }
    if hd is None:
        r["OUTCOME"] = "ANALYZE_OUTPUT_INVALID"
        r["FAILURE_ATTRIBUTION"] = "ANALYZE_OUTPUT_INVALID"
        return r, None

    if ca["kind"] == "positive":
        g = gt["positive"][cid]
        ss = so_quan_he(hd, g["expected_given_relations"],
                        g["expected_derived_perpendicular"])
        r["RELATION"] = ss
        r["ANALYZE_PASS"] = analyze_dat(ss)
        if not r["ANALYZE_PASS"]:
            r["OUTCOME"] = "ANALYZE_INCOMPLETE_OR_UNSAFE"
            return r, None
        ds = chay_tang_dung(hd, ca, g)
        env = ds.pop("_ENVELOPE", None)
        r["BUILD"] = ds
        r["OUTCOME"] = "FULL_PIPELINE_PASS" if ds.get("FULL_PIPELINE_PASS") \
            else "BUILD_FAILED"
        return r, env

    # ── NEGATIVE: không có ground truth quan hệ; đo AN TOÀN ────────────────
    ss = so_quan_he(hd, [], [])
    r["RELATION"] = {k: v for k, v in ss.items() if k != "RELATIONS"}
    r["DECLARED_RELATIONS"] = ss["RELATIONS"]
    ds = chay_tang_dung(hd, ca, {"expected_derived_perpendicular": [],
                                 "point_count": 4, "face_count": 4, "edge_count": 6,
                                 "squared_lengths": {"leg_1": "0", "leg_2": "0",
                                                     "height": "0"},
                                 "volume": "0"})
    ds.pop("_ENVELOPE", None)
    r["BUILD"] = {k: v for k, v in ds.items()
                  if k in ("ADAPTER_STATUS", "ADAPTER_REASON_CODE",
                           "COMPILER_ELIGIBILITY", "COMPILER_ELIGIBILITY_REASON",
                           "COMPILE_STATUS", "REJECTION_CODE", "ROUTE_RESULT",
                           "SYNTHESIS_REQUESTS", "COMPILER_MODEL_TOKENS")}
    xay_duoc = ds.get("COMPILE_STATUS") == "COMPILED"
    r["SAFE_REJECTION"] = not xay_duoc
    r["UNSAFE_ACCEPTANCE"] = xay_duoc
    r["REJECTION_CODE"] = ds.get("REJECTION_CODE")
    ng = gt["negative"][cid]
    r["REJECTION_CODE_REGISTERED"] = r["REJECTION_CODE"] in ng["acceptable_rejection_codes"]
    r["OUTCOME"] = "SAFE_REJECTION" if r["SAFE_REJECTION"] else "UNSAFE_ACCEPTANCE"
    return r, None


# ══ THỐNG KÊ ═══════════════════════════════════════════════════════════════
def _wilson(k: int, n: int) -> list[float] | None:
    if n == 0:
        return None
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def thong_ke(kq: list[dict], reg: dict) -> dict[str, Any]:
    pos = [r for r in kq if r["KIND"] == "positive"]
    neg = [r for r in kq if r["KIND"] == "negative"]
    rel = [r["RELATION"] for r in pos if "RELATION" in r]
    dat = [r for r in pos if r.get("OUTCOME") == "FULL_PIPELINE_PASS"]
    bd = [r["BUILD"] for r in pos if "BUILD" in r]
    tok = [r["USAGE"].get("totalTokenCount") for r in kq
           if r.get("USAGE", {}).get("totalTokenCount")]
    lat = sorted(r["LATENCY_MS"] for r in kq if r.get("LATENCY_MS"))
    clat = sorted(b["COMPILER_LATENCY_MS"] for b in bd if b.get("COMPILER_LATENCY_MS"))

    def pct(xs: list[float], q: float) -> float | None:
        return round(xs[min(len(xs) - 1, int(len(xs) * q))], 4) if xs else None

    dung = sum(r["CORRECT_CRITICAL_RELATION_COUNT"] for r in rel)
    mong = sum(r["EXPECTED_GIVEN_RELATION_COUNT"] for r in rel)
    return {
        "CASES_REGISTERED": len(reg["cases"]), "CASES_RUN": len(kq),
        "POSITIVE_RUN": len(pos), "NEGATIVE_RUN": len(neg),
        "ANALYZE": {
            "VALID_CONTRACT_COUNT": sum(1 for r in kq if r["MODEL_OUTPUT_RECEIVED"]),
            "VALID_CONTRACT_RATE": round(
                sum(1 for r in kq if r["MODEL_OUTPUT_RECEIVED"]) / len(kq), 4) if kq else None,
            "EXACT_CRITICAL_RELATION_COUNT": sum(
                1 for r in rel if r["CRITICAL_RELATION_ACCURACY"] == 1.0
                and r["MISSING_RELATION_COUNT"] == 0),
            "CRITICAL_RELATION_ACCURACY": round(dung / mong, 4) if mong else None,
            "MISSING_RELATION_COUNT": sum(r["MISSING_RELATION_COUNT"] for r in rel),
            "DUPLICATE_RELATION_COUNT": sum(r["DUPLICATE_RELATION_COUNT"] for r in rel),
            "CONTRADICTORY_RELATION_COUNT": sum(
                1 for r in kq if (r.get("BUILD") or {}).get("ADAPTER_STATUS") == "INVALID_CONFLICT"),
            "UNVERIFIED_EXTRA_RELATION_COUNT": sum(
                r["UNVERIFIED_EXTRA_RELATION_COUNT"] for r in rel),
            "EXTRA_DERIVED_AS_GIVEN_COUNT": sum(
                r["EXTRA_DERIVED_AS_GIVEN_COUNT"] for r in rel),
            "MODEL_ASSUMPTION_COUNT": sum(r["MODEL_ASSUMPTION_COUNT"] for r in rel),
        },
        "COMPILER": {
            "ELIGIBLE_COUNT": sum(1 for b in bd if b.get("COMPILER_ELIGIBILITY") == "SUPPORTED"),
            "COMPILATION_COUNT": sum(1 for b in bd if b.get("COMPILE_STATUS") == "COMPILED"),
            "TOPOLOGY_PASS_COUNT": sum(1 for b in bd if b.get("TOPOLOGY_RESULT") == "PASS"),
            "FINAL_MEMORY_PASS_COUNT": sum(1 for b in bd if b.get("FINAL_MEMORY_OK")),
            "ANSWER_PASS_COUNT": sum(1 for b in bd if b.get("ANSWER_OK")),
            "FULL_PIPELINE_PASS_COUNT": len(dat),
            "SILENT_QUALITY_FAILURE_COUNT": sum(
                1 for b in bd if b.get("SILENT_QUALITY_FAILURE")),
            "DETERMINISTIC_ALL": all(b.get("DETERMINISTIC", True) for b in bd),
        },
        "SAFETY": {
            "NEGATIVE_SAFE_REJECTION_COUNT": sum(1 for r in neg if r.get("SAFE_REJECTION")),
            "NEGATIVE_REJECTION_CODE_REGISTERED_COUNT": sum(
                1 for r in neg if r.get("REJECTION_CODE_REGISTERED")),
            "UNSAFE_ACCEPTANCE_COUNT": sum(1 for r in neg if r.get("UNSAFE_ACCEPTANCE")),
            "HALLUCINATED_CRITICAL_FACT_COUNT": sum(
                r["RELATION"].get("UNVERIFIED_EXTRA_RELATION_COUNT", 0)
                + r["RELATION"].get("EXTRA_DERIVED_AS_GIVEN_COUNT", 0)
                for r in kq if "RELATION" in r),
            "SYNTHESIS_FALLBACK_COUNT": 0,
        },
        "TOKEN": {
            "TOTAL_INPUT": sum(r["USAGE"].get("promptTokenCount", 0) for r in kq),
            "TOTAL_OUTPUT": sum(r["USAGE"].get("candidatesTokenCount", 0) for r in kq),
            "TOTAL_THOUGHT": sum(r["USAGE"].get("thoughtsTokenCount", 0) for r in kq),
            "TOTAL_ANALYZE": sum(tok),
            "MEDIAN_PER_CASE": round(statistics.median(tok), 1) if tok else None,
            "MIN": min(tok) if tok else None, "MAX": max(tok) if tok else None,
            "COMPILER_MODEL_TOKENS": 0, "SYNTHESIS_MODEL_TOKENS": 0,
        },
        "LATENCY": {"ANALYZE_P50": pct(lat, 0.5), "ANALYZE_P95": pct(lat, 0.95),
                    "COMPILER_P50": pct(clat, 0.5), "COMPILER_P95": pct(clat, 0.95)},
        "FAILURE_ATTRIBUTION": {
            q: sum(1 for r in pos if r.get("FAILURE_ATTRIBUTION") == q)
            for q in QUY_KET if any(r.get("FAILURE_ATTRIBUTION") == q for r in pos)},
        "WILSON_95_POSITIVE_FULL_PIPELINE": _wilson(len(dat), len(pos)),
        "STATISTICAL_SIGNIFICANCE": "NOT_ESTABLISHED",
    }


#: Dấu hiệu sự cố thuộc về BỘ ĐO, không thuộc nhà cung cấp. Danh sách ĐÓNG và
#: cố ý hẹp: chỉ những lỗi mà nguyên nhân nằm hẳn trong mã của ta.
DAU_HIEU_BO_DO = ("Event loop is closed", "RuntimeError: Event loop",
                  "AttributeError", "KeyError", "TypeError", "NameError")


def loai_su_co(kq: list[dict]) -> str | None:
    """`PROVIDER` · `APPARATUS` · `None`.

    ⚠️ Phân biệt này đắt. Lượt chạy đầu của wave chết vì `Event loop is closed`
    — một khuyết tật của chính runner — và bị chấm `PROVIDER_INCOMPLETE`. Nhãn
    ấy chỉ người đọc đi chờ nhà cung cấp, trong khi thứ hỏng nằm ở bộ đo. Một
    sự cố của bộ đo luôn là `MEASUREMENT_INVALID`, không bao giờ là lỗi ngoài.
    """
    co_provider = False
    for r in kq:
        loi = " ".join(str(r.get(k) or "") for k in
                       ("RUNNER_EXCEPTION", "PROVIDER_ERROR", "ANALYZE_ERROR"))
        if any(d in loi for d in DAU_HIEU_BO_DO):
            return "APPARATUS"
        if r.get("PROVIDER_ERROR"):
            co_provider = True
    return "PROVIDER" if co_provider else None


def phan_loai(st: dict, pos_n: int, neg_n: int, provider_loi: bool,
              du_12: bool, su_co: str | None = None) -> str:
    if su_co == "APPARATUS":
        return "MEASUREMENT_INVALID"
    if provider_loi or su_co == "PROVIDER":
        return "PROVIDER_INCOMPLETE"
    if not du_12:
        return "MORE_EVIDENCE_NEEDED"
    c, s = st["COMPILER"], st["SAFETY"]
    if s["UNSAFE_ACCEPTANCE_COUNT"] or c["SILENT_QUALITY_FAILURE_COUNT"] \
            or s["NEGATIVE_SAFE_REJECTION_COUNT"] < neg_n:
        return "NOT_READY"
    dat = c["FULL_PIPELINE_PASS_COUNT"]
    if dat < 5:
        return "NOT_READY"
    if dat == pos_n and s["NEGATIVE_SAFE_REJECTION_COUNT"] == neg_n \
            and s["HALLUCINATED_CRITICAL_FACT_COUNT"] == 0:
        return "STRONG_PILOT_RESULT"
    if dat >= pos_n - 1 and (st["ANALYZE"]["CRITICAL_RELATION_ACCURACY"] or 0) >= 0.90 \
            and s["HALLUCINATED_CRITICAL_FACT_COUNT"] == 0:
        return "READY_FOR_CANARY_DESIGN"
    return "MORE_EVIDENCE_NEEDED"


# ══ MAIN ═══════════════════════════════════════════════════════════════════
def main() -> int:
    ap = argparse.ArgumentParser(description=WAVE)
    ap.add_argument("--live", action="store_true", help="TIÊU QUOTA: tối đa 12 request")
    ap.add_argument("--tiep-tuc", metavar="TEP",
                    help="gộp kết quả HỢP LỆ của một lượt trước và chỉ chạy các ca "
                         "CHƯA đo được; dùng sau khi một lượt hỏng vì lỗi BỘ ĐO")
    ap.add_argument("--ra", default=str(RA))
    a = ap.parse_args()
    thu_muc = Path(a.ra)
    thu_muc.mkdir(parents=True, exist_ok=True)
    if not a.live:
        print("Chứng minh offline: tests/geometry/test_multicase_benchmark.py")
        print("Chạy thật: --live  (tối đa 12 request Analyze)")
        return EXIT_PRECHECK

    reg, gt = doc_registry(), doc_ground_truth()
    bang = ca_theo_id(reg)
    key = L.doc_khoa()
    khu = BoKhuBiMat((key,) if key else ())
    kenh = KenhIn(khu)
    if not key:
        kenh.loi("GEMINI_API_KEY vắng mặt — dừng với 0 request.")
        return EXIT_PRECHECK

    cong = L.CongQuetCam(httpx.AsyncHTTPTransport(), TRAN_TONG, khu,
                         dung_sau_loi=True, tran_theo_tang=TRAN_THEO_TANG,
                         chuoi_cam=_chuoi_cam(gt))
    kq: list[dict] = []
    env_theo_ca: dict[str, Any] = {}
    dung_som, ly_do_dung = False, None

    # ── TIẾP TỤC MỘT LƯỢT HỎNG VÌ BỘ ĐO ────────────────────────────────────
    #
    # Chỉ gộp ca có phép đo HỢP LỆ: nhận được phản hồi model VÀ không dính dấu
    # hiệu sự cố bộ đo. Ca void bị bỏ và CHẠY LẠI — nó chưa từng cho một kết
    # quả nào, nên đây không phải "gửi lại để lấy mẫu đẹp".
    da_do: set[str] = set()
    if a.tiep_tuc:
        cu = json.loads(Path(a.tiep_tuc).read_text(encoding="utf-8"))
        for r in cu.get("CASES", []):
            if r.get("MODEL_OUTPUT_RECEIVED") and loai_su_co([r]) is None:
                kq.append({**r, "TU_LUOT_TRUOC": True})
                da_do.add(r["CASE_ID"])
        kenh.in_(f"— GỘP {len(da_do)} ca đã đo hợp lệ: {sorted(da_do)}")

    async def chay_tat_ca() -> None:
        """MỘT vòng lặp asyncio cho CẢ wave.

        ⚠️ Bản đầu gọi `asyncio.run` MỘT LẦN MỖI CA. `httpx.AsyncHTTPTransport`
        dựng ở ngoài gắn vào vòng lặp của ca ĐẦU TIÊN, nên ca thứ hai chết bằng
        `RuntimeError: Event loop is closed` — và runner chấm nó thành
        `PROVIDER_ERROR`. Một khuyết tật của BỘ ĐO đội lốt lỗi nhà cung cấp là
        loại sai đắt nhất: nó làm người đọc đi sửa nhầm chỗ.
        """
        nonlocal dung_som, ly_do_dung
        for giai_doan, ds in (("A", reg["stage_a_order"]), ("B", reg["stage_b_order"])):
            if giai_doan == "B":
                gate = cong_stage_a(kq)
                _ghi_json(thu_muc, "STAGE_A_GATE.json", gate, khu)
                kenh.in_(f"— CỔNG GIAI ĐOẠN A: {'MỞ' if gate['MO_STAGE_B'] else 'ĐÓNG'}")
                if not gate["MO_STAGE_B"]:
                    dung_som, ly_do_dung = True, "STAGE_A_GATE_CLOSED"
                    break
            for cid in ds:
                if cid in da_do:
                    continue
                r, env = await chay_mot_ca(bang[cid], gt, key, cong)
                r["STAGE"] = giai_doan
                kq.append(r)
                if env is not None:
                    env_theo_ca[cid] = env
                kenh.in_(f"  {cid} [{giai_doan}] {r['OUTCOME']}"
                         + (f" · acc {r['RELATION']['CRITICAL_RELATION_ACCURACY']}"
                            if r.get("KIND") == "positive" and "RELATION" in r else "")
                         + (f" · {r.get('REJECTION_CODE')}" if r["KIND"] == "negative" else ""))
                if cong.provider_error:
                    dung_som, ly_do_dung = True, "PROVIDER_ERROR"
                    break
                if r["KIND"] == "negative" and r.get("UNSAFE_ACCEPTANCE"):
                    dung_som, ly_do_dung = True, "UNSAFE_ACCEPTANCE"
                    break
                if (r.get("BUILD") or {}).get("SILENT_QUALITY_FAILURE"):
                    dung_som, ly_do_dung = True, "SILENT_QUALITY_FAILURE"
                    break
            if dung_som:
                break

    asyncio.run(chay_tat_ca())

    pos_n = sum(1 for c in reg["cases"] if c["kind"] == "positive")
    neg_n = sum(1 for c in reg["cases"] if c["kind"] == "negative")
    st = thong_ke(kq, reg)
    thu_tu = {c: i for i, c in enumerate(thu_tu_chay(reg))}
    kq.sort(key=lambda r: thu_tu.get(r["CASE_ID"], 99))
    su_co = loai_su_co(kq)
    ket = phan_loai(st, pos_n, neg_n, bool(cong.provider_error),
                    len(kq) == len(reg["cases"]), su_co)

    http = cong.tong_hop()
    (thu_muc / "REPLAY_ENVELOPES.json").write_text(
        json.dumps({"envelopes": env_theo_ca}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    _ghi_json(thu_muc, "CASE_RESULTS_REDACTED.json",
              {"WAVE": WAVE, "RAN_AT": _bay_gio(), "EVALUATOR_VERSION": EVALUATOR_VERSION,
               "DATASET_SHA256": canonical_dataset_sha(reg, gt),
               "STOPPED_EARLY": dung_som, "STOP_REASON": ly_do_dung,
               "CASES": kq, **http, **cong.bang_chung_danh_tinh()}, khu)
    _ghi_json(thu_muc, "ACCEPTANCE_STATISTICS.json",
              {"WAVE": WAVE, "OUTCOME": ket, "NEXT_ACTION": NEXT_THEO_KET_QUA[ket],
               "STOPPED_EARLY": dung_som, "STOP_REASON": ly_do_dung,
               "SU_CO": su_co, **st}, khu)
    _ghi_json(thu_muc, "REQUEST_BUDGET_PROOF.json",
              {"MAX_TOTAL": TRAN_TONG, "MAX_PER_CASE": TRAN_MOI_CA,
               "TRAN_THEO_TANG": TRAN_THEO_TANG, **http,
               "PER_CASE": {c: len([x for x in cong.records
                                    if x["case_id"] == c and x["sent"]])
                            for c in [r["CASE_ID"] for r in kq]}}, khu)
    kenh.in_(f"OUTCOME = {ket} · {st['COMPILER']['FULL_PIPELINE_PASS_COUNT']}/{len([r for r in kq if r['KIND']=='positive'])} positive"
             f" · {st['SAFETY']['NEGATIVE_SAFE_REJECTION_COUNT']}/{len([r for r in kq if r['KIND']=='negative'])} negative an toàn")
    kenh.in_(f"ANALYZE {http['ANALYZE_HTTP_REQUESTS']} · VISION {http['VISION_HTTP_REQUESTS']}"
             f" · SYNTHESIS {http['SYNTHESIS_HTTP_REQUESTS']} · RETRIES {http['RETRIES']}")
    kenh.in_(f"NEXT_ACTION = {NEXT_THEO_KET_QUA[ket]}")
    return EXIT_PASS if ket in ("READY_FOR_CANARY_DESIGN", "STRONG_PILOT_RESULT") else EXIT_FAIL


def cong_stage_a(kq: list[dict]) -> dict[str, Any]:
    """Cổng mở giai đoạn B — NGƯỠNG ĐÃ ĐĂNG KÝ TRƯỚC, không đọc lại sau."""
    pos = [r for r in kq if r["KIND"] == "positive"]
    neg = [r for r in kq if r["KIND"] == "negative"]
    dat = sum(1 for r in pos if r.get("OUTCOME") == "FULL_PIPELINE_PASS")
    an_toan = sum(1 for r in neg if r.get("SAFE_REJECTION"))
    khong_an_toan = any(r.get("UNSAFE_ACCEPTANCE") for r in neg)
    im_lang = any((r.get("BUILD") or {}).get("SILENT_QUALITY_FAILURE") for r in kq)
    loi_do = any(r.get("PROVIDER_ERROR") for r in kq)
    dk = {
        "positive_full_pipeline": dat >= NGUONG_STAGE_A["positive_full_pipeline_min"],
        "negative_safe": an_toan >= NGUONG_STAGE_A["negative_safe_required"],
        "khong_co_quan_he_khong_an_toan": not khong_an_toan,
        "khong_co_that_bai_im_lang": not im_lang,
        "khong_co_loi_provider": not loi_do,
    }
    return {"NGUONG": NGUONG_STAGE_A, "DAT": {"positive_full_pipeline": dat,
                                              "negative_safe": an_toan},
            "DIEU_KIEN": dk, "MO_STAGE_B": all(dk.values())}


def _chuoi_cam(gt: dict) -> tuple[str, ...]:
    """Dấu vết ĐẶC TRƯNG của ground truth — không phải con số trần."""
    ra = {json.dumps(gt, ensure_ascii=False, sort_keys=True),
          "expected_given_relations", "expected_derived_perpendicular",
          "squared_lengths", "acceptable_rejection_codes", "unsafe_if",
          "base_area"}
    return tuple(sorted(ra))


if __name__ == "__main__":
    sys.exit(main())
