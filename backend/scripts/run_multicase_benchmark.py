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

⚠️ Từ /2 (COMPLETION_RUNNER_REPAIR_OFFLINE) trần tổng KHÔNG còn là hằng số 12
cho lượt đang chạy: nó bằng độ dài hàng đợi thật (`hang_doi_con_lai`), nên lượt
completion 6 ca có trần 6 ở transport. `TRAN_TONG` chỉ còn là số ca đăng ký.

─── GHÉP CA KHÔNG ĐƯỢC LỆCH ────────────────────────────────────────────────

Mỗi bản ghi request mang `case_id` do cổng đóng dấu lúc gửi. Token và độ trễ
của một ca **chỉ** lấy từ bản ghi mang đúng `case_id` ấy — không lấy "bản ghi
cuối cùng", vì đó đúng là cách một chỉ số nhảy sang ca khác mà không ai thấy.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
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
    BoKhuBiMat, KenhIn, _chuoi_loi, _ghi_json, _sha,
)
import run_structured_relation_analyze_live as L  # noqa: E402
import run_structured_relation_revalidation as V  # noqa: E402
import aggregate_multicase_completion as TH  # noqa: E402
from aggregate_multicase_completion import (  # noqa: E402,F401  (tên cũ giữ cho mọi chỗ đang gọi)
    DAU_HIEU_BO_DO, loai_su_co, quy_ket_that_bai, wilson as _wilson,
)

WAVE = "MULTICASE_STRUCTURED_ANALYZE_COMPILER_BENCHMARK"
#: /2 (COMPLETION_RUNNER_REPAIR_OFFLINE): quan sát request thật · trần transport dẫn
#: từ hàng đợi · ca âm chấm theo registry quan hệ đề nói · từ chối đúng khiếm khuyết ·
#: quy kết được GỌI · envelope ghi ngay sau từng ca · tổng hợp giao cho bộ tổng hợp.
#: Thân request gửi đi KHÔNG đổi một byte (test_G9).
RUNNER_VERSION = "multicase-structured-benchmark/2"
EVALUATOR_VERSION = "multicase-evaluator/2"

RA = (REPO / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene"
      / "multicase-benchmark")
REGISTRY = RA / "CASE_REGISTRY.json"
GROUND_TRUTH = RA / "GROUND_TRUTH.json"
#: Registry ĐĂNG KÝ TRƯỚC của lượt completion: quan hệ đề nói thẳng ở ca âm, từ
#: chối đúng khiếm khuyết, và băm request kỳ vọng của sáu ca còn thiếu.
REGISTRY_DIR = TH.REGISTRY_DIR
EXPECTED_REQUESTS = REGISTRY_DIR / "EXPECTED_REQUEST_HASHES.json"
#: Khoá GIẢ cho request kỳ vọng. Khoá nằm ở query của URL, không ở thân — và
#: quan sát chỉ giữ đường dẫn, nên chuỗi này không đi vào đâu cả.
KHOA_DU_KIEN = "khoa-du-kien-khong-phai-khoa-that"

TRAN_TONG = 12
TRAN_THEO_TANG = {"vision": 0, "analyze": TRAN_TONG, "synthesis": 0}
TRAN_MOI_CA = 1

#: Ngưỡng mở giai đoạn B — đăng ký TRƯỚC, không đổi sau khi thấy kết quả.
NGUONG_STAGE_A = {"positive_full_pipeline_min": 2, "positive_run": 3,
                  "negative_safe_required": 1}

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
    # Điểm mô hình NHẮC trong quan hệ mà hợp đồng không có — thứ phân biệt "server
    # chưa neo được điểm" với "mô hình bịa". Ghi ra để quy kết chạy được trên bản ghi.
    nhac = {p for r in tho for p in (*(getattr(r, "line", None) or ()),
                                     *(getattr(r, "other_line", None) or ()),
                                     *(getattr(r, "plane", None) or ()))}
    return {
        "CONTRACT_POINT_LABELS": sorted(diem_hop_dong(contract)),
        "UNBOUND_POINTS": sorted(nhac - diem_hop_dong(contract)),
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


#: Quy kết thất bại sống ở `aggregate_multicase_completion.quy_ket_that_bai` (nhập ở
#: đầu tệp): MỘT định nghĩa cho bản ghi completion lẫn bản ghi lịch sử. Bản cũ ở đây
#: được định nghĩa mà không nơi nào gọi, và không bao giờ trả `MODEL_MALFORMED_RELATION`
#: — chính mã mà P03/P05 phải mang.


# ══ G1 — QUAN SÁT REQUEST THẬT ═════════════════════════════════════════════
class LoiTuongDuongRequest(gemini.BudgetExceeded):
    """Request lệch byte so với kỳ vọng — chặn TRƯỚC transport, không tiêu quota.

    Kế thừa `BudgetExceeded` có chủ đích: `call_gemini` chỉ bọc timeout/lỗi mạng,
    nên lỗi này đi thẳng ra tới `chay_mot_ca` mà không bị nuốt.
    """


def quan_sat_request(req: httpx.Request) -> dict[str, Any]:
    """Dấu vân tay của ĐÚNG byte rời tiến trình. Không giữ thân, prompt, đề hay query."""
    than = req.content
    try:
        obj = json.loads(than)
    except (ValueError, TypeError):
        obj = {}
    gc = obj.get("generationConfig") or {}
    duong = req.url.path                                   # đường dẫn — query (chứa khoá) bị bỏ

    def bam(lay):
        try:
            return _sha(lay())
        except (KeyError, IndexError, TypeError):
            return None
    q = {"method": req.method, "endpoint_path": duong,
         "model": duong.rsplit("/", 1)[-1].split(":")[0] if "/models/" in duong else None,
         "body_sha256": _sha(than), "body_size_bytes": len(than),
         "system_prompt_sha256": bam(lambda: obj["systemInstruction"]["parts"][0]["text"]),
         "user_text_sha256": bam(lambda: obj["contents"][0]["parts"][-1]["text"]),
         # Dạng chuẩn ĐÃ ĐĂNG KÝ: json.dumps(sort_keys=True, ensure_ascii=False).
         "response_schema_sha256": (_sha(json.dumps(gc["responseSchema"], ensure_ascii=False,
                                                    sort_keys=True))
                                    if "responseSchema" in gc else None),
         "temperature": gc.get("temperature"), "response_mime_type": gc.get("responseMimeType"),
         "has_response_schema": "responseSchema" in gc,
         "has_thinking_config": "thinkingConfig" in gc,
         "generation_config_keys": sorted(gc)}
    # Model nằm ở URL, không ở thân: dấu vân tay gộp cả hai.
    q["request_fingerprint"] = _sha(f"{q['method']} {duong} {q['body_sha256']}")
    return q


class CongQuanSat(L.CongQuetCam):
    """`CongQuetCam` + quan sát từng request theo `case_id` + đối chiếu với kỳ vọng.

    Đối chiếu đứng TRƯỚC mọi cổng khác: request lệch byte không được gửi, không
    được đếm là đã gửi, và dừng lượt đo.
    """

    def __init__(self, *a: Any, du_kien: dict[str, dict] | None = None, **kw: Any) -> None:
        super().__init__(*a, **kw)
        self.du_kien = dict(du_kien or {})
        self.quan_sat: list[dict[str, Any]] = []
        self.tuong_duong_loi: dict[str, Any] | None = None
        self._lan: dict[str | None, int] = {}

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        q = quan_sat_request(request)
        cid = self.case_id
        self._lan[cid] = self._lan.get(cid, 0) + 1
        q.update(case_id=cid, attempt_index=self._lan[cid])
        k = self.du_kien.get(cid) if cid is not None else None
        if k is None:
            q["equivalence"] = "NOT_CHECKED"
        else:
            lech = [t for t in ("request_fingerprint", "body_sha256") if t in k and k[t] != q[t]]
            q["equivalence"] = "MISMATCH" if lech else "MATCH"
            if lech:
                q["mismatched_fields"] = lech
                self.quan_sat.append(q)
                self.tuong_duong_loi = {"case_id": cid, "fields": lech}
                raise LoiTuongDuongRequest(f"request {cid} lệch kỳ vọng ở {lech}")
        self.quan_sat.append(q)
        return await super().handle_async_request(request)


def tao_cong_completion(inner: httpx.AsyncBaseTransport, hang_doi: list[str], khu: BoKhuBiMat,
                        gt: dict, du_kien: dict[str, dict] | None = None) -> CongQuanSat:
    """Trần transport = ĐỘ DÀI HÀNG ĐỢI THẬT, không phải hằng số 12 (G2)."""
    n = len(hang_doi)
    return CongQuanSat(inner, n, khu, dung_sau_loi=True,
                       tran_theo_tang={"vision": 0, "analyze": n, "synthesis": 0},
                       chuoi_cam=_chuoi_cam(gt), du_kien=du_kien)


def dung_request_du_kien(ca: dict) -> dict[str, Any]:
    """Request KỲ VỌNG của một ca: chạy ĐÚNG `stage_semantic_analyze` qua transport giả.

    Thân request không phụ thuộc phản hồi (mỗi ca một request) và không chứa khoá,
    nên đây là đúng byte lượt live sẽ gửi. 0 request mạng.
    """
    from app.ai import pipeline as PL
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC

    cong = CongQuanSat(httpx.MockTransport(lambda _r: httpx.Response(200, json={
        "candidates": [{"content": {"parts": [{"text": "{}"}]}}]})), 1, BoKhuBiMat(),
        tran_theo_tang={"vision": 0, "analyze": 1, "synthesis": 0})
    cong.dat_ca(ca["case_id"])

    async def mot() -> None:
        with L.cai_cong_http(cong), L.dung_ngan_sach(gemini.ApiBudget(
                max_api_calls=1, max_attempts=1, max_logical_calls=1)):
            await PL.stage_semantic_analyze(ca["input_text"], KHOA_DU_KIEN, domain=DOMAIN_HINH_HOC)
    asyncio.run(mot())
    q = {k: v for k, v in cong.quan_sat[0].items() if k not in ("attempt_index", "equivalence")}
    return q


def hang_doi_con_lai(reg: dict, cu: list[dict]) -> list[str]:
    """Ca đã ĐĂNG KÝ trừ ca đã có kết cục hợp lệ trong lịch sử — theo thứ tự đóng băng."""
    da_do = {r["CASE_ID"] for r in cu
             if r.get("MODEL_OUTPUT_RECEIVED") and loai_su_co([r]) is None}
    return [c for c in thu_tu_chay(reg) if c not in da_do]


def ghi_envelope_nguyen_tu(thu_muc: Path, cid: str, env: Any) -> Path:
    """Ghi NGAY sau ca, nguyên tử: tệp tạm → flush → fsync → replace (G7).

    Tiến trình chết ở ca sau không làm mất envelope của ca trước, và không bao giờ
    để lại một envelope ghi dở dưới tên thật.
    """
    thu_muc.mkdir(parents=True, exist_ok=True)
    dich, tam = thu_muc / f"{cid}.json", thu_muc / f"{cid}.json.tmp"
    try:
        with open(tam, "w", encoding="utf-8", newline="\n") as f:
            json.dump(env, f, ensure_ascii=False, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tam, dich)
    except BaseException:
        tam.unlink(missing_ok=True)
        raise
    return dich


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
                         # tuple registry v2: luật nào bác, ở pha nào — từ vựng đóng của adapter
                         "ADAPTER_RULE_ID": ka.rule_id,
                         "ADAPTER_PHASE": dict(ka.evidence).get("PHASE"),
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
    qs = [q for q in getattr(cong, "quan_sat", ()) if q.get("case_id") == cid]
    r["REQUEST_EQUIVALENCE"] = qs[-1]["equivalence"] if qs else "NOT_OBSERVED"
    loi_td = getattr(cong, "tuong_duong_loi", None)
    if loi_td and loi_td.get("case_id") == cid:
        # Request lệch byte đã bị chặn trước transport: không phải kết cục của ca,
        # mà là phép đo hỏng — không chấm gì thêm.
        r.update(OUTCOME="REQUEST_EQUIVALENCE_FAILURE", REQUEST_EQUIVALENCE="MISMATCH")
        r["ATTRIBUTION"] = quy_ket_that_bai(r)
        return r, None
    if hd is None:
        r["OUTCOME"] = "ANALYZE_OUTPUT_INVALID"
        r["ATTRIBUTION"] = quy_ket_that_bai(r)
        return r, None
    r["OBLIGATION_KINDS"] = sorted(o.kind for o in (hd.obligations or ()))

    if ca["kind"] == "positive":
        g = gt["positive"][cid]
        ss = so_quan_he(hd, g["expected_given_relations"],
                        g["expected_derived_perpendicular"])
        r["RELATION"] = ss
        r["ANALYZE_PASS"] = analyze_dat(ss)
        if not r["ANALYZE_PASS"]:
            r["OUTCOME"] = "ANALYZE_INCOMPLETE_OR_UNSAFE"
            r["ATTRIBUTION"] = quy_ket_that_bai(r)
            return r, None
        ds = chay_tang_dung(hd, ca, g)
        env = ds.pop("_ENVELOPE", None)
        r["BUILD"] = ds
        r["OUTCOME"] = "FULL_PIPELINE_PASS" if ds.get("FULL_PIPELINE_PASS") else "BUILD_FAILED"
        r["ATTRIBUTION"] = quy_ket_that_bai(r)
        return r, env

    # ── NEGATIVE: chấm theo registry quan hệ ĐỀ NÓI THẲNG (G3), đo AN TOÀN ─
    #
    # Bản /1 chấm với tập kỳ vọng RỖNG, nên mọi quan hệ mô hình khai — kể cả
    # quan hệ đề viết nguyên văn — đều thành "bịa". Registry đăng ký trước, dẫn
    # CHỈ từ đề đóng băng; quan hệ khai ngoài nó vẫn là unverified extra.
    rel_reg, tgt_reg = TH.doc_registry_ca_am()
    dk2 = TH.doc_registry_tu_choi_v2()          # hỏng ⇒ LoiRegistry, KHÔNG lùi về v1
    ss = so_quan_he(hd, rel_reg["CASES"][cid]["relations"], [])
    r["RELATION"] = {k: v for k, v in ss.items() if k != "RELATIONS"}
    r["DECLARED_RELATIONS"] = ss["RELATIONS"]
    r["HALLUCINATED_CRITICAL_FACT_COUNT"] = (ss["UNVERIFIED_EXTRA_RELATION_COUNT"]
                                            + ss["EXTRA_DERIVED_AS_GIVEN_COUNT"])
    ds = chay_tang_dung(hd, ca, {"expected_derived_perpendicular": [],
                                 "point_count": 4, "face_count": 4, "edge_count": 6,
                                 "squared_lengths": {"leg_1": "0", "leg_2": "0",
                                                     "height": "0"},
                                 "volume": "0"})
    ds.pop("_ENVELOPE", None)
    r["BUILD"] = {k: v for k, v in ds.items()
                  if k in ("ADAPTER_STATUS", "ADAPTER_REASON_CODE",
                           "ADAPTER_RULE_ID", "ADAPTER_PHASE",
                           "COMPILER_ELIGIBILITY", "COMPILER_ELIGIBILITY_REASON",
                           "COMPILE_STATUS", "REJECTION_CODE", "ROUTE_RESULT",
                           "PYDANTIC_PROGRAM_VALIDATION", "SCENE_NON_EMPTY", "FINAL_MEMORY_OK",
                           "SYNTHESIS_REQUESTS", "COMPILER_MODEL_TOKENS")}
    xay_duoc = ds.get("COMPILE_STATUS") == "COMPILED"
    r["SAFE_REJECTION"] = not xay_duoc
    r["UNSAFE_ACCEPTANCE"] = xay_duoc
    r["REJECTION_CODE"] = ds.get("REJECTION_CODE")
    ng = gt["negative"][cid]
    r["REJECTION_CODE_REGISTERED"] = r["REJECTION_CODE"] in ng["acceptable_rejection_codes"]
    r["OUTCOME"] = "SAFE_REJECTION" if r["SAFE_REJECTION"] else "UNSAFE_ACCEPTANCE"
    # G8: an toàn ≠ đúng khiếm khuyết. `{}` có thể an toàn mà không chứng minh gì.
    r.update(TH.doi_chieu_tu_choi(r, cid, rel_reg, tgt_reg))
    # Hai kỳ vọng, RIÊNG: v1 (gốc, trước bản sửa) ở trên; v2 (hồi quy, chỉ N04 khác) ở đây.
    r.update(TH.doi_chieu_tu_choi_v2(r, cid, rel_reg, dk2))
    r["DATASET_ROLE"] = dk2["META"]["DATASET_ROLES"][cid]
    r["TARGETED_REGISTRY_RESOLVED_SHA256"] = dk2["META"]["RESOLVED_REGISTRY_SHA256"]
    r["ATTRIBUTION"] = quy_ket_that_bai(r)
    return r, None


def kiem_rang_buoc_registry() -> dict[str, Any]:
    """Ràng buộc registry v2 TRƯỚC request đầu tiên. Hỏng ⇒ `LoiRegistry`, 0 request.

    Bộ nạp đã soát: v1 trùng băm, overlay đúng hợp đồng, commit hành vi mang bản sửa,
    N04 là ca hồi quy. Ở đây thêm hai điều chỉ runner cần: overlay ĐÃ COMMIT (đăng ký
    trước ⇔ có trong HEAD, không sửa dở) và mã sản phẩm đang chạy khớp candidate đã khai.
    """
    import freeze_evaluation_candidate as F
    dk = TH.doc_registry_tu_choi_v2()
    p = Path(TH.REGISTRY_V2_PATH).resolve()
    try:
        rel = p.relative_to(TH.REPO.resolve()).as_posix()
    except ValueError:
        raise TH.LoiRegistry("REGISTRY_V2_NOT_COMMITTED", "overlay nằm ngoài kho") from None
    if (TH._git("ls-files", "--error-unmatch", "--", rel).returncode != 0
            or TH._git("diff", "--quiet", "HEAD", "--", rel).returncode != 0):
        raise TH.LoiRegistry("REGISTRY_V2_NOT_COMMITTED", rel)
    if F.measured_system_hash()[0] != dk["META"]["PRODUCT_CANDIDATE_HASH"]:
        raise TH.LoiRegistry("PRODUCT_CANDIDATE_DRIFT")
    return {**dk["META"], "REGISTRY_V2_COMMITTED": True, "LOADED_BEFORE_FIRST_REQUEST": True}


# ══ MAIN ══════════════════════════════════════════════════════════════════
#
# Thống kê và phân loại KHÔNG còn ở đây: chúng sống ở `aggregate_multicase_completion`
# (một thẩm quyền, đọc CẢ lịch sử qua băm). Bản /1 cộng token thiếu như 0, tính
# timeout vào p95, gộp UNSAFE vào NOT_READY — xem RUNNER_READINESS_GAPS G4/G6.
def main() -> int:
    ap = argparse.ArgumentParser(description=WAVE)
    ap.add_argument("--live", action="store_true",
                    help="TIÊU QUOTA: tối đa len(hàng đợi còn lại) request Analyze")
    ap.add_argument("--tiep-tuc", metavar="TEP",
                    help="CASE_RESULTS_REDACTED lịch sử: gộp ca đã đo HỢP LỆ, chỉ chạy ca còn thiếu")
    ap.add_argument("--contact-sheet", action="store_true",
                    help="ghép contact sheet từ artifact đã ghi — 0 request")
    ap.add_argument("--ra", default=str(RA))
    a = ap.parse_args()
    thu_muc = Path(a.ra)
    if a.contact_sheet:
        kq = dung_contact_sheet(thu_muc)
        (thu_muc / "CONTACT_SHEET_MANIFEST.json").write_text(
            json.dumps(kq, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"CONTACT_SHEET = {kq['FILE']} ({kq['BYTES']} byte) · "
              f"{kq['ROWS']} hàng · sha {kq['SHA256'][:16]}…")
        return EXIT_PASS

    if not a.live:
        print("Chứng minh offline: tests/geometry/test_completion_runner_repair.py")
        print("Chạy thật: --live --tiep-tuc <CASE_RESULTS_REDACTED lịch sử> --ra <thư mục MỚI>")
        return EXIT_PRECHECK
    if not a.tiep_tuc:
        # Lịch sử đo ĐÃ tồn tại. Chạy 12 ca từ đầu là gửi lại ca đã có kết quả.
        print("Thiếu --tiep-tuc: chạy lại ca đã có kết quả bị cấm — dừng với 0 request.")
        return EXIT_PRECHECK
    thu_muc.mkdir(parents=True, exist_ok=True)

    reg, gt = doc_registry(), doc_ground_truth()
    bang = ca_theo_id(reg)
    key = L.doc_khoa()
    khu = BoKhuBiMat((key,) if key else ())
    kenh = KenhIn(khu)
    if not key:
        kenh.loi("GEMINI_API_KEY vắng mặt — dừng với 0 request.")
        return EXIT_PRECHECK

    # ── RÀNG BUỘC REGISTRY v2 TRƯỚC REQUEST ĐẦU TIÊN — 0 request ───────────
    try:
        rang_buoc = kiem_rang_buoc_registry()
    except TH.LoiRegistry as e:
        _ghi_json(thu_muc, "PRECHECK_REGISTRY_BINDING.json",
                  {"RESULT": e.ma, "MODEL_REQUESTS_USED": 0}, khu)
        kenh.loi(f"Registry v2 không ràng buộc được ({e.ma}) — dừng với 0 request.")
        return EXIT_PRECHECK
    _ghi_json(thu_muc, "REGISTRY_BINDING.json", rang_buoc, khu)

    # ── HÀNG ĐỢI: ca đăng ký trừ ca đã có kết cục hợp lệ (G2) ───────────────
    cu = json.loads(Path(a.tiep_tuc).read_text(encoding="utf-8")).get("CASES", [])
    hang_doi = hang_doi_con_lai(reg, cu)
    kq: list[dict] = [{**r, "TU_LUOT_TRUOC": True} for r in cu
                      if r.get("CASE_ID") not in hang_doi and r.get("MODEL_OUTPUT_RECEIVED")
                      and loai_su_co([r]) is None]
    kenh.in_(f"— GỘP {len(kq)} ca đã đo hợp lệ · HÀNG ĐỢI {hang_doi}")
    if not hang_doi:
        kenh.in_("Không còn ca nào để chạy.")
        return EXIT_PRECHECK

    # ── TƯƠNG ĐƯƠNG REQUEST TRƯỚC LIVE — 0 request (G1) ────────────────────
    du_kien = {cid: dung_request_du_kien(bang[cid]) for cid in hang_doi}
    dang_ky = ({e["case_id"]: e for e in json.loads(
        EXPECTED_REQUESTS.read_text(encoding="utf-8"))["EXPECTED"]}
        if EXPECTED_REQUESTS.exists() else {})
    lech = sorted(cid for cid in hang_doi if cid not in dang_ky or any(
        dang_ky[cid][t] != du_kien[cid][t] for t in ("body_sha256", "request_fingerprint")))
    if lech:
        _ghi_json(thu_muc, "PRECHECK_REQUEST_EQUIVALENCE.json",
                  {"RESULT": "REQUEST_EQUIVALENCE_FAILURE", "CASES": lech,
                   "MODEL_REQUESTS_USED": 0}, khu)
        kenh.loi(f"REQUEST_EQUIVALENCE_FAILURE trước live ở {lech} — dừng với 0 request.")
        return EXIT_PRECHECK

    cong = tao_cong_completion(httpx.AsyncHTTPTransport(), hang_doi, khu, gt, du_kien=du_kien)
    moi: list[dict] = []
    dung_som, ly_do_dung = False, None

    async def chay_tat_ca() -> None:
        """MỘT vòng lặp asyncio cho CẢ lượt.

        ⚠️ Bản đầu gọi `asyncio.run` MỘT LẦN MỖI CA: `httpx.AsyncHTTPTransport` gắn
        vào vòng lặp của ca đầu, ca thứ hai chết bằng `Event loop is closed`.
        """
        nonlocal dung_som, ly_do_dung
        for giai_doan, ds in (("A", reg["stage_a_order"]), ("B", reg["stage_b_order"])):
            con = [c for c in ds if c in hang_doi]
            if giai_doan == "B" and con:
                gate = cong_stage_a(kq)
                _ghi_json(thu_muc, "STAGE_A_GATE.json", gate, khu)
                kenh.in_(f"— CỔNG GIAI ĐOẠN A: {'MỞ' if gate['MO_STAGE_B'] else 'ĐÓNG'}")
                if not gate["MO_STAGE_B"]:
                    dung_som, ly_do_dung = True, "STAGE_A_GATE_CLOSED"
                    break
            for cid in con:
                r, env = await chay_mot_ca(bang[cid], gt, key, cong)
                r["STAGE"] = giai_doan
                kq.append(r)
                moi.append(r)
                if env is not None:
                    # G7: ghi NGAY, trước ca kế — không đợi hết vòng lặp.
                    ghi_envelope_nguyen_tu(thu_muc / "envelopes", cid, env)
                kenh.in_(f"  {cid} [{giai_doan}] {r['OUTCOME']}"
                         + (f" · {r.get('REJECTION_CODE')}" if r["KIND"] == "negative" else ""))
                if cong.tuong_duong_loi:
                    dung_som, ly_do_dung = True, "REQUEST_EQUIVALENCE_FAILURE"
                    break
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

    http = cong.tong_hop()
    _ghi_json(thu_muc, "COMPLETION_CASE_RESULTS_REDACTED.json",
              {"WAVE": WAVE, "LAYER": "completion", "RUNNER_VERSION": RUNNER_VERSION,
               "EVALUATOR_VERSION": EVALUATOR_VERSION,
               "DATASET_SHA256": canonical_dataset_sha(reg, gt), "QUEUE": hang_doi,
               "STOPPED_EARLY": dung_som, "STOP_REASON": ly_do_dung,
               "TARGETED_REGISTRY": rang_buoc, "CASES": moi,
               **http, **cong.bang_chung_danh_tinh()}, khu)
    _ghi_json(thu_muc, "REQUEST_OBSERVATIONS.json",
              {"LAYER": "completion", "OBSERVATIONS": cong.quan_sat,
               "EXPECTED_REGISTRY_SHA256_LF": TH._sha_lf(EXPECTED_REQUESTS),
               "_KHONG_GHI": "thân request, prompt, đề, query string, khoá, phản hồi thô"}, khu)
    _ghi_json(thu_muc, "REQUEST_BUDGET_PROOF.json",
              {"QUEUE": hang_doi, "MAX_PER_CASE": TRAN_MOI_CA,
               "TRAN_THEO_TANG": cong.tran_theo_tang,
               # Vòng sửa chỉ tồn tại ở tầng synthesis, mà trần synthesis là 0.
               "REPAIR_REQUESTS": http["SYNTHESIS_HTTP_REQUESTS"], **http,
               "PER_CASE": {c: len([x for x in cong.records if x["case_id"] == c and x["sent"]])
                            for c in hang_doi}}, khu)
    tk = TH.tong_hop(moi, completion_stop_reason=ly_do_dung)
    _ghi_json(thu_muc, "AGGREGATE_12_CASE_RESULTS.json", tk, khu)
    _ghi_json(thu_muc, "ACCEPTANCE_STATISTICS.json",
              {k: tk.get(k) for k in ("CLASSIFICATION", "NEXT_ACTION", "COUNTS", "METRICS",
                                      "TOKENS", "LATENCY", "MEASUREMENT_INVALID_REASONS",
                                      "TOKEN_OPTIMIZATION")}, khu)
    kenh.in_(f"CLASSIFICATION = {tk['CLASSIFICATION']} · ANALYZE {http['ANALYZE_HTTP_REQUESTS']}"
             f" · VISION {http['VISION_HTTP_REQUESTS']} · SYNTHESIS {http['SYNTHESIS_HTTP_REQUESTS']}"
             f" · RETRIES {http['RETRIES']}")
    kenh.in_(f"NEXT_ACTION = {tk['NEXT_ACTION']}")
    return EXIT_PASS if tk["CLASSIFICATION"] in ("READY_FOR_CANARY_DESIGN",
                                                 "STRONG_PILOT_RESULT") else EXIT_FAIL


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




# ══ §10 · CONTACT SHEET — MỘT HÀNG MỖI CA ══════════════════════════════════
#: Thêm SAU lượt live. Chỉ ĐỌC artifact đã ghi và ghép ảnh — không tính lại,
#: không chấm lại, không chạm một phép đo nào.
def dung_contact_sheet(thu_muc: Path) -> dict[str, Any]:
    from PIL import Image, ImageDraw, ImageFont

    reg, gt = doc_registry(), doc_ground_truth()
    bang = ca_theo_id(reg)
    kq = json.loads((thu_muc / "CASE_RESULTS_REDACTED.json").read_text(encoding="utf-8"))
    theo_ca = {r["CASE_ID"]: r for r in kq["CASES"]}

    def ft(px: int, dam: bool = False):
        for ten in (("seguisb.ttf", "arialbd.ttf") if dam else ("segoeui.ttf", "arial.ttf")):
            try:
                return ImageFont.truetype(ten, px)
            except OSError:
                continue
        return ImageFont.load_default()

    F, FB, FS = ft(15), ft(17, True), ft(13)
    RONG, LE, H_HANG, W_ANH = 1820, 24, 150, 190
    hang = thu_tu_chay(reg)
    cao = 108 + H_HANG * len(hang) + 64
    im = Image.new("RGB", (RONG, cao), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, RONG, 84], fill=(17, 24, 39))
    d.text((LE, 14), "MULTICASE_STRUCTURED_ANALYZE_COMPILER_BENCHMARK — CONTACT SHEET",
           font=ft(19, True), fill=(255, 255, 255))
    d.text((LE, 42), f"{kq['RAN_AT']} · gemini-2.5-flash · T=0.1 · "
                     f"DEVELOPMENT_HOLDOUT_PILOT · dataset {kq['DATASET_SHA256'][:16]}…",
           font=FS, fill=(203, 213, 225))
    d.text((LE, 62), "Gemini CHỈ đọc đề thành dữ liệu có cấu trúc. Cảnh do primitive "
                     "compiler tất định dựng — 0 token model, 0 request tổng hợp.",
           font=FS, fill=(148, 163, 184))

    y = 100
    for cid in hang:
        ca = bang[cid]
        r = theo_ca.get(cid)
        nen = (248, 250, 252) if r else (254, 249, 240)
        d.rectangle([LE, y, RONG - LE, y + H_HANG - 8], fill=nen,
                    outline=(226, 232, 240))
        d.text((LE + 10, y + 8), cid, font=FB, fill=(30, 41, 59))
        d.text((LE + 10, y + 30), ca["kind"], font=FS, fill=(100, 116, 139))
        d.text((LE + 10, y + 48), (ca.get("wording_class") or ca.get("defect", ""))[:22],
               font=FS, fill=(100, 116, 139))
        de = " ".join(ca["input_text"].split())
        for i, doan in enumerate([de[i:i + 62] for i in range(0, min(len(de), 248), 62)]):
            d.text((LE + 128, y + 8 + i * 17), doan, font=FS, fill=(51, 65, 85))
        x = LE + 560
        if r is None:
            d.text((x, y + 30), "CHƯA CHẠY — dừng theo chính sách sau lỗi provider",
                   font=F, fill=(180, 83, 9))
            y += H_HANG
            continue
        rel = r.get("RELATION") or {}
        dong = [f"Analyze: {r['OUTCOME']}",
                (f"acc {rel.get('CRITICAL_RELATION_ACCURACY')} · thiếu "
                 f"{rel.get('MISSING_RELATION_COUNT')} · giả định "
                 f"{rel.get('MODEL_ASSUMPTION_COUNT')} · hệ quả→GIVEN "
                 f"{rel.get('EXTRA_DERIVED_AS_GIVEN_COUNT')}")]
        qk = (r.get("ATTRIBUTION") or {}).get("PRIMARY") or r.get("FAILURE_ATTRIBUTION")
        if qk:
            dong.append(f"quy kết: {qk}")
        b = r.get("BUILD") or {}
        if ca["kind"] == "negative":
            dong.append(f"TỪ CHỐI AN TOÀN: {r.get('SAFE_REJECTION')} · "
                        f"{r.get('REJECTION_CODE')}")
        elif b:
            dong.append(f"compiler {b.get('COMPILER_ELIGIBILITY')}/{b.get('COMPILE_STATUS')}"
                        f" · route {b.get('ROUTE_RESULT')} · đáp số "
                        f"{'ĐÚNG' if b.get('ANSWER_OK') else 'SAI'}"
                        f" ({gt['positive'][cid]['volume']})")
        u = r.get("USAGE") or {}
        dong.append(f"token {u.get('totalTokenCount', '—')} · {r.get('LATENCY_MS')} ms"
                    f" · compiler tokens 0")
        for i, s in enumerate(dong):
            d.text((x, y + 8 + i * 17), s[:96], font=F, fill=(51, 65, 85))

        xa = RONG - LE - 2 * W_ANH - 20
        for k, khung in enumerate(("1440x900", "390x844")):
            p = thu_muc / "browser" / cid / f"{khung}.png"
            ox = xa + k * (W_ANH + 10)
            if p.exists():
                a = Image.open(p)
                a = a.resize((W_ANH, min(H_HANG - 22, round(a.height * W_ANH / a.width))))
                im.paste(a, (ox, y + 6))
                d.rectangle([ox, y + 6, ox + a.width, y + 6 + a.height],
                            outline=(203, 213, 225))
            else:
                d.rectangle([ox, y + 6, ox + W_ANH, y + H_HANG - 16],
                            outline=(226, 232, 240))
                lb = ("an toàn: không dựng cảnh" if ca["kind"] == "negative"
                      else "không có envelope")
                d.text((ox + 8, y + H_HANG // 2 - 10), lb, font=FS, fill=(148, 163, 184))
            d.text((ox, y + H_HANG - 14), khung, font=FS, fill=(148, 163, 184))
        y += H_HANG

    d.text((LE, y + 8), "USER_VISUAL_APPROVAL = PENDING · "
                        "STATISTICAL_SIGNIFICANCE = NOT_ESTABLISHED · "
                        "TOKEN_OPTIMIZATION = NOT_PRODUCTION_ESTABLISHED",
           font=F, fill=(100, 116, 139))
    ra = thu_muc / "CONTACT_SHEET.png"
    im.save(ra)
    return {"WAVE": WAVE, "FILE": ra.name, "SHA256": _sha(ra.read_bytes()),
            "BYTES": ra.stat().st_size, "ROWS": len(hang),
            "_KHONG_CHUA": ["API key", "raw response", "raw prompt",
                            "toàn bộ semantic program", "headers"],
            "USER_VISUAL_APPROVAL": "PENDING"}


if __name__ == "__main__":
    sys.exit(main())
