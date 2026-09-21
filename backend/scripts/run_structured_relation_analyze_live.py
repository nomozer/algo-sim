# -*- coding: utf-8 -*-
"""LƯỢT LIVE MỘT REQUEST — Gemini có khai đúng quan hệ CÓ CẤU TRÚC không.

`STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_VALIDATION` (2026-09-21).

─── CÂU HỎI DUY NHẤT ───────────────────────────────────────────────────────

`FACT_GRAPH_CONTRACT_EXTENSION` chứng minh hệ **đọc được** ô `geometric_relations`.
Nó KHÔNG chứng minh mô hình thật **khai đúng** ô ấy — mọi hợp đồng trong wave đó
do test dựng tay. Wave này tiêu đúng **một** request Analyze để hỏi câu còn lại.

─── VÌ SAO KHÔNG DỰNG REQUEST RIÊNG ────────────────────────────────────────

Launcher gọi thẳng `pipeline.stage_semantic_analyze` — ĐÚNG hàm đường sản phẩm.
Dựng request bằng tay là đo một hệ khác: prompt, schema, temperature, JSON mode
và timeout khi ấy là của launcher, không phải của sản phẩm. Bài học đã trả giá
hai lần ở kho này (`certifier gọi tắt nên không bao giờ chạm main_async`).

─── BA THỨ KHÔNG ĐƯỢC LẪN ──────────────────────────────────────────────────

① `LIVE_CASE_MANIFEST.json` — ĐỀ BÀI. Vào prompt.
② `GROUND_TRUTH_REGISTRATION.json` — ĐÁP ÁN. **Không bao giờ** vào prompt,
   request body, analyze context hay compiler. Chỉ vào bộ chấm, SAU khi
   Analyze đã trả lời. `CongQuetCam` quét thân request để chứng minh.
③ Cấu trúc ca (`structure`) — vai của từng đỉnh, để bộ chấm đọc được cảnh.
   Không phải đáp số. `witness` CỐ Ý không nằm ở đây: nó do hợp đồng LIVE quyết.

─── NGÂN SÁCH ĐẶT Ở TRANSPORT, KHÔNG Ở LOGIC ───────────────────────────────

`CongHttp` (tái dùng nguyên của `run_photo_problem_live`) chặn **trước** khi
`httpx` gửi, đếm theo TẦNG, và trần từng tầng là `{vision: 0, analyze: 1,
synthesis: 0}` — tầng vắng mặt ⇒ trần 0. Cộng thêm `ApiBudget(max_attempts=1,
max_logical_calls=1, max_api_calls=1)` nên retry và lượt gọi logic thứ hai đều
chết trước transport. Hai lớp, cố ý: một lớp đếm theo tầng, một lớp đếm tuyệt đối.
"""
from __future__ import annotations

import argparse
import asyncio
import json
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

from app.ai import gemini, pipeline  # noqa: E402
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC  # noqa: E402

# Tái dùng NGUYÊN cổng HTTP, bộ khử bí mật và bộ chặn mạng của runner ảnh —
# dựng bản thứ hai là dựng thẩm quyền thứ hai cho cùng một câu hỏi.
from run_photo_problem_live import (  # noqa: E402
    BoKhuBiMat, ChanMangThat, CongHttp, KenhIn,
    _bay_gio, _chuoi_loi, _ghi_json, _sha, cai_cong_http, dung_ngan_sach,
)
# Bộ chấm quan sát downstream — cùng bộ mà benchmark A/B dùng cho nhánh compiler.
from run_primitive_compiler_ab import cham  # noqa: E402

WAVE = "STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_VALIDATION"
RUNNER_VERSION = "structured-relation-analyze-live/1"

RA = (REPO / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene"
      / "structured-relation-analyze-live")
MANIFEST = RA / "LIVE_CASE_MANIFEST.json"
GROUND_TRUTH = RA / "GROUND_TRUTH_REGISTRATION.json"

#: Trần từng tầng. Tầng vắng mặt ⇒ trần 0 (xem `CongHttp.__init__`).
TRAN_THEO_TANG = {"vision": 0, "analyze": 1, "synthesis": 0}
MAX_HTTP = 1

#: Khoá `generationConfig` mà đường sản phẩm ĐƯỢC PHÉP đặt. Thừa một khoá là
#: launcher đã đổi cấu hình mô hình — tức đo một hệ khác.
KHOA_GEN_CONFIG_CHO_PHEP = frozenset(
    {"temperature", "responseMimeType", "responseSchema"})
KHOA_GEN_CONFIG_CAM = ("thinkingConfig", "maxOutputTokens", "topK", "topP",
                       "candidateCount", "stopSequences", "seed")

#: Phân loại kết quả — §8 của đặc tả wave. Bảng ĐÓNG.
KET_QUA = (
    "PASS",
    "ANALYZE_RELATION_INCOMPLETE",
    "ANALYZE_RELATION_UNGROUNDED",
    "EXTRA_DERIVED_RELATION_AS_GIVEN",
    "MODEL_OUTPUT_INVALID",
    "SCHEMA_REJECTED",
    "PROVIDER_ERROR",
    "DOWNSTREAM_COMPILER_UNSUPPORTED",
    "DOWNSTREAM_COMPILER_FAILURE",
)

NEXT_THEO_KET_QUA = {
    "PASS": "DETERMINISTIC_FIRST_ROUTING_SHADOW_INTEGRATION",
    "ANALYZE_RELATION_INCOMPLETE": "ANALYZE_STRUCTURED_RELATION_PROMPT_DIAGNOSIS",
    "ANALYZE_RELATION_UNGROUNDED": "STRUCTURED_RELATION_PROVENANCE_DIAGNOSIS",
    "EXTRA_DERIVED_RELATION_AS_GIVEN": "ANALYZE_GIVEN_DERIVED_SEPARATION_FIX",
    "MODEL_OUTPUT_INVALID": "ANALYZE_STRUCTURED_OUTPUT_VALIDATION_DIAGNOSIS",
    "SCHEMA_REJECTED": "ANALYZE_SCHEMA_COMPATIBILITY_FIX",
    "PROVIDER_ERROR": "RETRY_LATER_WITHOUT_CODE_CHANGE",
    "DOWNSTREAM_COMPILER_UNSUPPORTED": "COMPILER_ELIGIBILITY_LIVE_CONTRACT_DIAGNOSIS",
    "DOWNSTREAM_COMPILER_FAILURE": "COMPILER_LIVE_CONTRACT_DOWNSTREAM_DIAGNOSIS",
}

EXIT_PASS, EXIT_FAIL, EXIT_PRECHECK = 0, 1, 2


# ══ ĐỌC ĐẦU VÀO ĐÃ ĐÓNG BĂNG ════════════════════════════════════════════════
def doc_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def doc_ground_truth() -> dict[str, Any]:
    return json.loads(GROUND_TRUTH.read_text(encoding="utf-8"))


def de_bai(mf: dict[str, Any]) -> str:
    """Văn bản ĐÚNG NHƯ ĐÃ ĐÓNG BĂNG — không strip, không chuẩn hoá."""
    return mf["input_text"]


def bam_van_ban(s: str) -> str:
    return _sha(s.encode("utf-8"))


def doc_khoa() -> str:
    """Khoá từ môi trường, rồi tới `backend/.env`. KHÔNG bao giờ in ra."""
    import os

    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if k:
        return k
    env = GOC / ".env"
    if not env.exists():
        return ""
    for dong in env.read_text(encoding="utf-8").splitlines():
        if dong.startswith("GEMINI_API_KEY="):
            return dong.split("=", 1)[1].strip()
    return ""


# ══ CỔNG QUÉT CẤM — ground truth không được lọt vào thân request ════════════
class CongQuetCam(CongHttp):
    """`CongHttp` + phép quét thân request tìm dấu vết ground truth.

    Quét ở ĐÂY chứ không ở chỗ dựng request, vì đây là chỗ cuối cùng trước khi
    byte rời tiến trình: mọi đường vòng (prompt, schema, context, retry) đều
    phải đi qua nó. Thân request KHÔNG được giữ lại — chỉ số đếm và cờ.
    """

    def __init__(self, *a: Any, chuoi_cam: tuple[str, ...] = (), **kw: Any) -> None:
        super().__init__(*a, **kw)
        self.chuoi_cam = tuple(chuoi_cam)
        #: Mỗi phần tử: chuỗi cấm nào bị tìm thấy ở request thứ mấy. Rỗng = sạch.
        self.va_cham_cam: list[dict[str, Any]] = []
        #: Khoá `generationConfig` quan sát được — KHOÁ, không phải giá trị.
        self.gen_config_keys: list[list[str]] = []
        self.temperature_quan_sat: list[Any] = []
        self.system_prompt_sha256: list[str] = []
        self.user_text_sha256: list[str] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        than = request.content
        try:
            obj = json.loads(than)
        except (ValueError, TypeError):
            obj = None
        if isinstance(obj, dict):
            gc = obj.get("generationConfig") or {}
            self.gen_config_keys.append(sorted(gc))
            self.temperature_quan_sat.append(gc.get("temperature"))
            try:
                self.system_prompt_sha256.append(
                    _sha(obj["systemInstruction"]["parts"][0]["text"]))
            except (KeyError, IndexError, TypeError):
                self.system_prompt_sha256.append("")
            try:
                self.user_text_sha256.append(
                    _sha(obj["contents"][0]["parts"][-1]["text"]))
            except (KeyError, IndexError, TypeError):
                self.user_text_sha256.append("")
        van = than.decode("utf-8", "replace")
        for c in self.chuoi_cam:
            if c and c in van:
                self.va_cham_cam.append(
                    {"request_index": self.attempted + 1, "needle_sha256": _sha(c)})
        return await super().handle_async_request(request)

    def bang_chung_danh_tinh(self) -> dict[str, Any]:
        thua = sorted({k for ks in self.gen_config_keys for k in ks}
                      - KHOA_GEN_CONFIG_CHO_PHEP)
        return {
            "GENERATION_CONFIG_KEYS": self.gen_config_keys,
            "GENERATION_CONFIG_UNEXPECTED_KEYS": thua,
            "FORBIDDEN_CONFIG_KEYS_PRESENT": sorted(
                {k for ks in self.gen_config_keys for k in ks
                 if k in KHOA_GEN_CONFIG_CAM}),
            "TEMPERATURE_OBSERVED": self.temperature_quan_sat,
            "SYSTEM_PROMPT_SHA256": self.system_prompt_sha256,
            "USER_TEXT_SHA256": self.user_text_sha256,
            "GROUND_TRUTH_NEEDLES_FOUND": self.va_cham_cam,
            "GROUND_TRUTH_ABSENT_FROM_REQUEST": not self.va_cham_cam,
        }


def chuoi_cam_tu_ground_truth(gt: dict[str, Any]) -> tuple[str, ...]:
    """Dấu vết ĐẶC TRƯNG của ground truth — không phải con số trần.

    Quét `"10"` là vô nghĩa: schema và prompt đầy chữ số. Thứ quét được là
    những chuỗi CHỈ tồn tại trong tệp đáp án: tên khoá và câu chú thích.
    """
    ra: set[str] = {
        json.dumps(gt, ensure_ascii=False, sort_keys=True),
        "expected_answer", "expected_squared_lengths",
        "expected_derived_perpendicular", "expected_topology",
        "canonical_args", "base_area",
    }
    for muc in gt.get("expected_derived_perpendicular", {}).get("items", ()):
        if muc.get("doc"):
            ra.add(str(muc["doc"]))
    for muc in gt.get("expected_relations", {}).get("items", ()):
        if muc.get("doc"):
            ra.add(str(muc["doc"]))
    return tuple(sorted(ra))


# ══ SO QUAN HỆ ══════════════════════════════════════════════════════════════
def _khoa(kind: str, args: Any) -> tuple[str, tuple[str, ...]]:
    return (str(kind), tuple(str(x) for x in args))


def so_sanh_quan_he(contract: Any, gt: dict[str, Any]) -> dict[str, Any]:
    """Hợp đồng LIVE ↔ ground truth. Chỉ bản RÚT GỌN, không nguyên văn đề."""
    from app.simulation.semantic_program.structured_relations import (
        MA_REFERENCE_UNKNOWN, diem_hop_dong, kiem_va_chuan_hoa,
    )

    tho = tuple(getattr(contract, "geometric_relations", None) or ())
    kq = kiem_va_chuan_hoa(contract)
    biet = diem_hop_dong(contract)

    mong = {_khoa(m["kind"], m["canonical_args"])
            for m in gt["expected_relations"]["items"]}
    suy = {_khoa(m["kind"], m["canonical_args"])
           for m in gt["expected_derived_perpendicular"]["items"]}

    thuc = {q.khoa for q in kq.relations}
    thieu = sorted(mong - thuc)
    thua = sorted(thuc - mong)
    thua_suy_dien = [k for k in thua if k in suy]
    thua_khong_can_cu = [k for k in thua if k not in suy]

    # Trùng lặp đo trên bản THÔ: `kiem_va_chuan_hoa` đã khử trùng, nên đếm ở đó
    # thì mọi lượt đều 0 và phép đo mất nghĩa.
    tho_khoa: list[tuple[str, tuple[str, ...]]] = []
    for q in kq.relations:
        tho_khoa.append(q.khoa)
    trung = max(0, len(tho) - len(kq.loi) - len(set(tho_khoa)))

    gia_dinh = sum(1 for r in tho if bool(getattr(r, "model_assumption", False)))
    khong_can_cu = [e for e in kq.loi if e.ma == MA_REFERENCE_UNKNOWN]

    # Truy `source_fact_id` về đúng mục dữ kiện — `kiem_va_chuan_hoa` KHÔNG làm
    # việc này (nó chỉ kiểm nhãn điểm), nên đây là cổng riêng.
    chua_truy_duoc = [
        {"kind": q.kind, "args": list(q.args), "source_fact_id": q.source_fact_id}
        for q in kq.relations
        if not q.source_fact_id or contract.fact(q.source_fact_id) is None
    ]

    ban_ghi = [{
        "kind": q.kind,
        "canonical_args": list(q.args),
        "source_fact_id": q.source_fact_id,
        "source_fact_resolves": bool(
            q.source_fact_id and contract.fact(q.source_fact_id) is not None),
        "model_assumption": q.model_assumption,
        "usable_by_construction": q.dung_duoc_cho_tang_dung(),
        "matches_ground_truth": q.khoa in mong,
        "is_derivable_relation": q.khoa in suy,
    } for q in kq.relations]

    return {
        "CASE_ID": gt["case_id"],
        "CONTRACT_POINT_LABELS": sorted(biet),
        "RAW_RELATION_COUNT": len(tho),
        "NORMALIZED_RELATION_COUNT": len(kq.relations),
        "EXPECTED_RELATION_COUNT": gt["expected_relations"]["required_count"],
        "ACTUAL_GIVEN_RELATION_COUNT": sum(
            1 for q in kq.relations if q.dung_duoc_cho_tang_dung()),
        "MISSING_RELATION_COUNT": len(thieu),
        "MISSING_RELATIONS": [list(k[1]) and {"kind": k[0], "args": list(k[1])}
                              for k in thieu],
        "DUPLICATE_RELATION_COUNT": trung,
        "UNVERIFIED_EXTRA_RELATION_COUNT": len(thua_khong_can_cu),
        "UNVERIFIED_EXTRA_RELATIONS": [{"kind": k[0], "args": list(k[1])}
                                       for k in thua_khong_can_cu],
        "EXTRA_DERIVED_AS_GIVEN_COUNT": len(thua_suy_dien),
        "EXTRA_DERIVED_AS_GIVEN": [{"kind": k[0], "args": list(k[1])}
                                   for k in thua_suy_dien],
        "MODEL_ASSUMPTION_COUNT": gia_dinh,
        "REJECTED_RELATION_CODES": [
            {"code": e.ma, "kind": e.kind, "index": e.chi_so} for e in kq.loi],
        "POINT_REFERENCE_VALIDATION": "FAIL" if khong_can_cu else "PASS",
        "SOURCE_FACT_RESOLUTION": "FAIL" if chua_truy_duoc else "PASS",
        "SOURCE_FACT_UNRESOLVED": chua_truy_duoc,
        "CRITICAL_RELATION_ACCURACY": round(
            len(mong & thuc) / len(mong), 4) if mong else 0.0,
        "RELATIONS": ban_ghi,
    }


# ══ DOWNSTREAM — HOÀN TOÀN OFFLINE ══════════════════════════════════════════
def chay_downstream(contract: Any, mf: dict[str, Any], gt: dict[str, Any]
                    ) -> dict[str, Any]:
    """`RequestContract` LIVE → adapter → FactGraph → compiler → cảnh → đáp số.

    0 lượt gọi model. Ground truth chỉ vào ở `cham`, sau khi chương trình đã
    được sinh — compiler không bao giờ thấy nó.
    """
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.geometry_compiler import contract_adapter as A

    t0 = time.perf_counter()
    ka = A.build_fact_graph(contract)
    ms_adapter = (time.perf_counter() - t0) * 1000

    ra: dict[str, Any] = {
        "ADAPTER_STATUS": ka.status,
        "ADAPTER_VERSION": ka.adapter_version,
        "ADAPTER_REASON_CODE": ka.reason_code,
        "ADAPTER_DIAGNOSTICS": list(ka.diagnostics),
        "FACT_GRAPH_LATENCY_MS": round(ms_adapter, 4),
    }
    if ka.graph is None:
        ra.update(FACT_GRAPH_VERSION=None, COMPILER_ELIGIBILITY="NO_GRAPH",
                  COMPILE_STATUS="NO_GRAPH")
        return ra

    g = ka.graph
    given = [f for f in g.facts if f.status == "GIVEN"]
    derived = [f for f in g.facts if f.status == "DERIVED"]
    perp_derived = [f for f in derived if f.kind == "perpendicular_lines"]
    mong_suy = {_khoa(m["kind"], m["canonical_args"])
                for m in gt["expected_derived_perpendicular"]["items"]}
    thuc_suy = {_khoa(f.kind, f.args) for f in perp_derived}

    ra.update({
        "FACT_GRAPH_VERSION": g.version,
        "FACT_GRAPH_NODE_COUNT": len(g.nodes),
        "FACT_GRAPH_GIVEN_COUNT": len(given),
        "FACT_GRAPH_DERIVED_COUNT": len(derived),
        "DERIVED_PERPENDICULAR_COUNT": len(perp_derived),
        "DERIVED_PERPENDICULAR_MATCHES_GROUND_TRUTH": thuc_suy == mong_suy,
        "DERIVED_PERPENDICULAR_MISSING": [
            {"kind": k[0], "args": list(k[1])} for k in sorted(mong_suy - thuc_suy)],
        # ⚠️ PHẠM VI CỐ Ý HẸP — theo ĐÚNG luật của sản phẩm.
        #
        # `fact_graph.kiem_xuat_xu` chỉ ép `derived_from` với quan hệ VUÔNG GÓC,
        # và nêu rõ vì sao: đó là loại fact mà một lời khai và một suy diễn có
        # cùng hình dạng. `lies_in_plane` là bằng chứng tham chiếu điểm, cố ý
        # không mang cha.
        #
        # Bản đầu của bộ đo này ép CẢ `lies_in_plane` và vì thế chấm ca ĐÚNG
        # thành `DOWNSTREAM_COMPILER_FAILURE` — một bộ đo đỏ vì định nghĩa của
        # chính nó, đúng chế độ hỏng `CLAUDE.md §2b·3b` mô tả. Giữ nguyên hai
        # trường tách bạch để lần sau không ai gộp lại.
        "EVERY_DERIVED_RELATION_HAS_PARENT_PROOF": all(
            bool(f.derived_from) for f in perp_derived),
        "DERIVED_RELATION_WITHOUT_PARENT": [
            {"kind": f.kind, "args": list(f.args)}
            for f in perp_derived if not f.derived_from],
        "DERIVED_NON_RELATION_WITHOUT_PARENT": [
            {"kind": f.kind, "args": list(f.args)}
            for f in derived
            if f.kind != "perpendicular_lines" and not f.derived_from],
        "FACTS": [f.chinh_tac() for f in g.facts],
    })

    el = C.danh_gia_eligibility(g)
    ra["COMPILER_ELIGIBILITY"] = el.status
    ra["COMPILER_ELIGIBILITY_REASON"] = el.reason_code
    ra["COMPILER_ELIGIBILITY_DIAGNOSTICS"] = list(el.diagnostics)
    if el.binding is None:
        ra["COMPILE_STATUS"] = "NOT_ELIGIBLE"
        return ra

    b = el.binding
    # `witness`/`container` do HỢP ĐỒNG LIVE quyết, không do manifest áp vào.
    ra["WITNESS_OBSERVED"] = b.witness
    ra["CONTAINER_OBSERVED"] = b.container

    t1 = time.perf_counter()
    bd = C.bien_dich(g)
    ms_compile = (time.perf_counter() - t1) * 1000
    ra.update({
        "COMPILE_STATUS": bd.status,
        "COMPILER_VERSION": bd.compiler_version,
        "COMPILE_REASON_CODE": bd.reason_code,
        "COMPILE_DIAGNOSTICS": list(bd.diagnostics),
        "CONSTRUCTION_STEPS": len(bd.construction_steps),
        "PRIMITIVE_CALLS": len(bd.primitive_calls),
        "COMPILER_LATENCY_MS": round(ms_compile, 4),
        "PROGRAM_SHA256": (_sha(json.dumps(bd.program, sort_keys=True,
                                           ensure_ascii=False))
                           if bd.program else None),
    })
    if bd.program is None:
        return ra

    # ── Bộ chấm: CHỖ DUY NHẤT ground truth được đọc ─────────────────────────
    ca = {**mf["structure"], "case_id": gt["case_id"], "witness": b.witness,
          "container": b.container}
    c = cham(gt["case_id"], "COMPILER", ca, contract, bd.program,
             {"point_count": gt["expected_topology"]["point_count"],
              "face_count": gt["expected_topology"]["face_count"],
              "squared_lengths": gt["expected_squared_lengths"],
              "volume": gt["expected_answer"]["volume"]},
             len(bd.construction_steps))
    ra["CHAM"] = asdict(c)
    return ra


# ══ PHÂN LOẠI ═══════════════════════════════════════════════════════════════
def phan_loai(ss: dict[str, Any] | None, ds: dict[str, Any] | None,
              loi_analyze: str | None, http: dict[str, Any]) -> str:
    """§8 — MỘT nhãn, theo thứ tự ưu tiên đã khai. Không tự sửa nguyên nhân."""
    if http.get("PROVIDER_ERROR"):
        loi = str(http["PROVIDER_ERROR"])
        return "SCHEMA_REJECTED" if "400" in loi else "PROVIDER_ERROR"
    if loi_analyze or ss is None:
        return "MODEL_OUTPUT_INVALID"

    if ss["EXTRA_DERIVED_AS_GIVEN_COUNT"] > 0:
        # Đứng TRƯỚC mọi nhãn khác: ghi một hệ quả thành dữ kiện đề cho là lỗi
        # RIÊNG, và bỏ qua nó để output trông hợp lệ chính là điều §3 cấm.
        return "EXTRA_DERIVED_RELATION_AS_GIVEN"
    if ss["MISSING_RELATION_COUNT"] > 0:
        return "ANALYZE_RELATION_INCOMPLETE"
    if (ss["POINT_REFERENCE_VALIDATION"] != "PASS"
            or ss["SOURCE_FACT_RESOLUTION"] != "PASS"
            or ss["MODEL_ASSUMPTION_COUNT"] > 0
            or ss["REJECTED_RELATION_CODES"]):
        return "ANALYZE_RELATION_UNGROUNDED"
    if ss["UNVERIFIED_EXTRA_RELATION_COUNT"] > 0 or ss["DUPLICATE_RELATION_COUNT"] > 0:
        return "ANALYZE_RELATION_UNGROUNDED"

    if ds is None:
        return "DOWNSTREAM_COMPILER_UNSUPPORTED"
    if ds.get("COMPILER_ELIGIBILITY") != "SUPPORTED":
        return "DOWNSTREAM_COMPILER_UNSUPPORTED"
    c = ds.get("CHAM") or {}
    if ds.get("COMPILE_STATUS") != "COMPILED" or not c.get("quality_pass"):
        return "DOWNSTREAM_COMPILER_FAILURE"
    if not ds.get("DERIVED_PERPENDICULAR_MATCHES_GROUND_TRUTH") \
            or not ds.get("EVERY_DERIVED_RELATION_HAS_PARENT_PROOF"):
        return "DOWNSTREAM_COMPILER_FAILURE"
    return "PASS"


# ══ MỘT LƯỢT — dùng chung cho offline proof và live ═════════════════════════
async def mot_luot(de: str, key: str, cong: CongHttp) -> tuple[Any, str | None, str | None]:
    """Gọi ĐÚNG hàm Analyze của sản phẩm, đúng một lượt logic."""
    budget = gemini.ApiBudget(max_api_calls=MAX_HTTP, max_attempts=1,
                              max_logical_calls=1)
    with cai_cong_http(cong), dung_ngan_sach(budget):
        try:
            hd, err = await pipeline.stage_semantic_analyze(
                de, key, domain=DOMAIN_HINH_HOC)
            return hd, err, None
        except Exception as e:  # noqa: BLE001
            return None, None, _chuoi_loi(e)


def tao_cong(khu: BoKhuBiMat, gt: dict[str, Any],
             inner: httpx.AsyncBaseTransport | None) -> CongQuetCam:
    return CongQuetCam(inner, MAX_HTTP, khu, dung_sau_loi=True,
                       tran_theo_tang=TRAN_THEO_TANG,
                       chuoi_cam=chuoi_cam_tu_ground_truth(gt))


def main() -> int:
    ap = argparse.ArgumentParser(description=WAVE)
    ap.add_argument("--live", action="store_true",
                    help="TIÊU QUOTA: gửi đúng 1 request Analyze thật.")
    ap.add_argument("--ra", default=str(RA), help="thư mục artifact")
    a = ap.parse_args()

    if not a.live:
        print("Chế độ chứng minh offline nằm ở "
              "tests/geometry/test_structured_relation_analyze_live_runner.py")
        print("Gửi request thật: --live")
        return EXIT_PRECHECK

    mf, gt = doc_manifest(), doc_ground_truth()
    de = de_bai(mf)
    key = doc_khoa()
    # Bộ khử dựng TỪ chính khoá, TRƯỚC mọi lượt in hay ghi — không có đường nào
    # để một chuỗi chẩn đoán đi ra ngoài trước khi bộ khử tồn tại.
    khu = BoKhuBiMat((key,) if key else ())
    kenh = KenhIn(khu)
    if not key:
        kenh.loi("GEMINI_API_KEY vắng mặt — dừng với 0 request.")
        return EXIT_PRECHECK

    thu_muc = Path(a.ra)
    thu_muc.mkdir(parents=True, exist_ok=True)

    cong = tao_cong(khu, gt, httpx.AsyncHTTPTransport())
    cong.dat_ca(gt["case_id"])

    t0 = time.perf_counter()
    hd, err, no = asyncio.run(mot_luot(de, key, cong))
    latency = round((time.perf_counter() - t0) * 1000, 1)

    http = cong.tong_hop()
    ss = so_sanh_quan_he(hd, gt) if hd is not None else None
    ds = chay_downstream(hd, mf, gt) if hd is not None else None
    ket = phan_loai(ss, ds, err or no, http)

    ban = {
        "WAVE": WAVE, "RUNNER_VERSION": RUNNER_VERSION,
        "RAN_AT": _bay_gio(),
        "CASE_ID": gt["case_id"],
        "DATASET_CLASS": mf["dataset_class"],
        "INPUT_TEXT_SHA256": bam_van_ban(de),
        "MODEL": mf["model"], "TEMPERATURE": mf["temperature"],
        "TIMEOUT_SECONDS": mf["timeout_seconds"],
        "LATENCY_MS": latency,
        "ANALYZE_ERROR": khu.chuoi(err) if err else None,
        "RUNNER_EXCEPTION": khu.chuoi(no) if no else None,
        "MODEL_OUTPUT_RECEIVED": hd is not None,
        "JSON_PARSE_RESULT": "FAIL" if (err and "JSON" in err) else (
            "PASS" if hd is not None else "UNKNOWN"),
        "PYDANTIC_VALIDATION_RESULT": "PASS" if hd is not None else "FAIL",
        "OUTCOME": ket,
        "NEXT_ACTION": NEXT_THEO_KET_QUA[ket],
        **http,
        **cong.bang_chung_danh_tinh(),
    }
    _ghi_json(thu_muc, "ANALYZE_LIVE_RESULT_REDACTED.json", ban, khu)
    _ghi_json(thu_muc, "REQUEST_IDENTITY.json",
              {"RECORDS": cong.records, **cong.bang_chung_danh_tinh()}, khu)
    _ghi_json(thu_muc, "REQUEST_BUDGET_PROOF.json", http, khu)
    if ss is not None:
        _ghi_json(thu_muc, "STRUCTURED_RELATION_COMPARISON.json", ss, khu)
        _ghi_json(thu_muc, "PROVENANCE_RESOLUTION_PROOF.json", {
            "SOURCE_FACT_RESOLUTION": ss["SOURCE_FACT_RESOLUTION"],
            "POINT_REFERENCE_VALIDATION": ss["POINT_REFERENCE_VALIDATION"],
            "CONTRACT_POINT_LABELS": ss["CONTRACT_POINT_LABELS"],
            "SOURCE_FACT_UNRESOLVED": ss["SOURCE_FACT_UNRESOLVED"],
            "RELATIONS": ss["RELATIONS"],
        }, khu)
    if ds is not None:
        _ghi_json(thu_muc, "FACT_GRAPH_RESULT_REDACTED.json",
                  {k: v for k, v in ds.items() if k != "CHAM"}, khu)
        _ghi_json(thu_muc, "COMPILER_DOWNSTREAM_RESULT.json", ds, khu)

    kenh.in_(f"OUTCOME = {ket}")
    kenh.in_(f"ANALYZE_HTTP_REQUESTS = {http['ANALYZE_HTTP_REQUESTS']} · "
             f"VISION = {http['VISION_HTTP_REQUESTS']} · "
             f"SYNTHESIS = {http['SYNTHESIS_HTTP_REQUESTS']} · "
             f"RETRIES = {http['RETRIES']}")
    kenh.in_(f"NEXT_ACTION = {NEXT_THEO_KET_QUA[ket]}")
    kenh.in_(f"→ {thu_muc}")
    return EXIT_PASS if ket == "PASS" else EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
