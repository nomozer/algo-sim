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
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
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
    BoKhuBiMat, KenhIn, _chuoi_loi, _ghi_json, _sha, chi_so_token,
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
#: /3 (COMPLETION_MEASUREMENT_REPAIR_OFFLINE_POST_SAFETY): ràng buộc đủ 17 trường kiểm
#: fail closed trước transport (R1) · nhật ký bền theo từng ca, đặt chỗ TRƯỚC transport (R2)
#: · lỗi tầng chấm thành bản ghi `MEASUREMENT_ERROR` rồi dừng (R3). Thân request vẫn không đổi.
RUNNER_VERSION = "multicase-structured-benchmark/3"
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


def ghi_json_nguyen_tu(dich: Path, obj: Any) -> Path:
    """MỘT cách ghi bền cho mọi artifact của lượt: tệp tạm CÙNG thư mục → flush → fsync →
    `os.replace` → đọc lại xác minh. Không bao giờ để nửa JSON dưới tên thật; lỗi giữa chừng
    để nguyên bản cũ. Tệp tạm sót lại do tiến trình bị giết được lượt sau dọn (`mo_lai`).
    """
    dich.parent.mkdir(parents=True, exist_ok=True)
    tam = dich.with_name(dich.name + ".tmp")
    van = json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    try:
        with open(tam, "w", encoding="utf-8", newline="\n") as f:
            f.write(van)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tam, dich)
    except BaseException:
        tam.unlink(missing_ok=True)
        raise
    if dich.read_text(encoding="utf-8") != van:
        raise LoiNhatKy("JOURNAL_READBACK_MISMATCH")
    return dich


def ghi_envelope_nguyen_tu(thu_muc: Path, cid: str, env: Any) -> Path:
    """Ghi NGAY sau ca (G7): tiến trình chết ở ca sau không làm mất envelope của ca trước."""
    return ghi_json_nguyen_tu(thu_muc / f"{cid}.json", env)


# ══ R1 — RÀNG BUỘC ĐỦ 17 TRƯỜNG, KIỂM FAIL CLOSED TRƯỚC TRANSPORT ═══════════
#
# Bản /2 chỉ ghi phần NGỮ NGHĨA của registry (3/17 trường đặc tả đòi). Model, prompt,
# schema, thứ tự ca có được ghi — nhưng SAU vòng lặp, không phải trước request đầu.
TRUONG_RANG_BUOC: tuple[str, ...] = (
    "repository_identity", "branch", "execution_head", "cache_version", "manifest_sha256",
    "ground_truth_sha256", "registry_v1_sha256", "registry_v2_sha256", "candidate_sha256",
    "runner_sha256", "aggregator_sha256", "model", "prompt_sha256", "schema_sha256",
    "case_order", "request_budget", "created_at_utc")
#: Giá trị ĐĂNG KÝ TRƯỚC, commit cùng runner. Các băm còn lại KHÔNG chép ở đây: chúng
#: đọc từ registry v2 (ghim bằng băm dưới đây) và từ EXPECTED_REQUEST_HASHES — mỗi giá
#: trị một nguồn.
DANG_KY: dict[str, Any] = {
    "repository_identity": "git-root:0621910084d26b43de857f8dda230d4c8a2fe7a1",
    "branch": "feat/photo-problem-to-scene",
    "cache_version": "99",
    "model": "gemini-2.5-flash",
    "registry_v2_sha256": "03a87ba37a6df62604d33119f346101e1f9e6f10f8db63b6fdbff6ce40c07e81",
    "case_order": ["P06", "P07", "P08", "N02", "N03", "N04"],
    "request_budget": 6,
}
PHIEN_BAN_RANG_BUOC = "completion-binding/1 · sha256 trên byte chuẩn hoá LF"
CANDIDATE_FILE = REPO / "docs" / "evaluation" / "semantic-benchmark" / "EVALUATION_CANDIDATE.json"
MA_TRUONG_SAI: dict[str, str] = {
    "repository_identity": "BINDING_REPOSITORY_MISMATCH", "branch": "BINDING_BRANCH_MISMATCH",
    "execution_head": "BINDING_HEAD_MISMATCH", "cache_version": "BINDING_CACHE_VERSION_MISMATCH",
    "manifest_sha256": "BINDING_DATASET_HASH_MISMATCH",
    "ground_truth_sha256": "BINDING_DATASET_HASH_MISMATCH",
    "registry_v1_sha256": "BINDING_REGISTRY_DRIFT", "registry_v2_sha256": "BINDING_REGISTRY_DRIFT",
    "candidate_sha256": "BINDING_CANDIDATE_DRIFT", "runner_sha256": "BINDING_RUNNER_DRIFT",
    "aggregator_sha256": "BINDING_AGGREGATOR_DRIFT", "model": "BINDING_MODEL_MISMATCH",
    "prompt_sha256": "BINDING_PROMPT_MISMATCH", "schema_sha256": "BINDING_SCHEMA_MISMATCH",
    "case_order": "BINDING_CASE_ORDER_MISMATCH", "request_budget": "BINDING_BUDGET_MISMATCH",
}
#: registry v2 kiểm ĐẦU TIÊN: kỳ vọng của manifest/ground truth/v1/candidate đọc từ nó.
THU_TU_KIEM = ("registry_v2_sha256",) + tuple(
    t for t in TRUONG_RANG_BUOC if t not in ("registry_v2_sha256", "created_at_utc"))
_HEX = re.compile(r"[0-9a-f]+")
_MAU_GIO = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z")


def _la_hex(v: Any, n: int) -> bool:
    return isinstance(v, str) and len(v) == n and bool(_HEX.fullmatch(v))


def _la_chuoi(v: Any) -> bool:
    return isinstance(v, str) and bool(v)


_KIEU: dict[str, Any] = {
    **{t: (lambda v: _la_hex(v, 64)) for t in (
        "manifest_sha256", "ground_truth_sha256", "registry_v1_sha256", "registry_v2_sha256",
        "candidate_sha256", "runner_sha256", "aggregator_sha256", "prompt_sha256", "schema_sha256")},
    "repository_identity": _la_chuoi, "branch": _la_chuoi, "model": _la_chuoi, "created_at_utc": _la_chuoi,
    "execution_head": lambda v: _la_hex(v, 40),
    "cache_version": lambda v: isinstance(v, str) and v.isdigit(),
    "case_order": lambda v: isinstance(v, list) and bool(v) and all(_la_chuoi(x) for x in v),
    "request_budget": lambda v: isinstance(v, int) and not isinstance(v, bool),
}


def _bam_lf(b: bytes) -> str:
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def _duong_trong_kho(p: Path) -> str:
    return Path(p).resolve().relative_to(TH.REPO.resolve()).as_posix()


#: Băm của tệp ĐANG CHẠY, chốt lúc nạp module. Tệp trên đĩa đổi sau đó là trôi.
_BAM_RUNNER_KHI_NAP = _bam_lf(Path(__file__).read_bytes())
_BAM_BO_TONG_HOP_KHI_NAP = _bam_lf(Path(TH.__file__).read_bytes())


def dong_ho() -> datetime:
    """Đồng hồ của ràng buộc — test thay bằng giờ cố định để tuần tự hoá tất định."""
    return datetime.now(timezone.utc)


def _bam_da_commit(head: str, rel: str) -> str | None:
    """Băm (LF) của `rel` ĐÚNG như đã commit ở `head` — đọc byte, không qua chế độ văn bản."""
    r = subprocess.run(["git", "show", f"{head}:{rel}"], cwd=TH.REPO, capture_output=True)
    return _bam_lf(r.stdout) if r.returncode == 0 else None


def _nhanh_quan_sat(head: str) -> str:
    """Nhánh đang gắn; worktree detached ⇒ nhánh đăng ký nếu và chỉ nếu nó CHỨA `head`."""
    dang_gan = TH._git("branch", "--show-current").stdout.strip()
    if dang_gan:
        return dang_gan
    ky = DANG_KY["branch"]
    chua = TH._git("merge-base", "--is-ancestor", head, f"refs/heads/{ky}").returncode == 0
    return ky if chua else f"DETACHED_NOT_ON:{ky}"


def _cache_version_nguon() -> str | None:
    """Đọc MÃ NGUỒN `app/main.py` — import nó là nạp `.env`."""
    m = re.search(r'^CACHE_VERSION = "(\d+)"', (GOC / "app" / "main.py").read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def _duy_nhat(xs: Any) -> Any:
    tap = {json.dumps(x, sort_keys=True) for x in xs}
    return json.loads(next(iter(tap))) if len(tap) == 1 else "NOT_UNIQUE"


def dung_rang_buoc(hang_doi: list[str], du_kien: dict[str, dict], meta: dict[str, Any]) -> dict[str, Any]:
    """Ràng buộc QUAN SÁT. Mọi băm tính từ đúng byte runner dùng — không chép giá trị khai tay.

    Prompt, schema, model lấy từ request KỲ VỌNG đã dựng qua đúng `stage_semantic_analyze`,
    tức byte sẽ rời tiến trình. Khoá phần ngữ nghĩa registry (`meta`) giữ nguyên tên cũ.
    """
    import freeze_evaluation_candidate as F
    head = TH._git("rev-parse", "HEAD").stdout.strip()
    goc = sorted(TH._git("rev-list", "--max-parents=0", "HEAD").stdout.split())
    qs = [du_kien[c] for c in hang_doi]
    return {
        **meta,
        "binding_version": PHIEN_BAN_RANG_BUOC,
        "repository_identity": "git-root:" + ",".join(goc),
        "branch": _nhanh_quan_sat(head),
        "execution_head": head,
        "cache_version": _cache_version_nguon(),
        "manifest_sha256": TH._sha_lf(TH.HIST_DIR / "BENCHMARK_MANIFEST.json"),
        "ground_truth_sha256": TH._sha_lf(TH.HIST_DIR / "GROUND_TRUTH.json"),
        "registry_v1_sha256": TH._sha_lf(TH.REGISTRY_DIR / "NEGATIVE_TARGETED_REJECTION_REGISTRY.json"),
        "registry_v2_sha256": TH._sha_lf(Path(TH.REGISTRY_V2_PATH)),
        "candidate_sha256": F.measured_system_hash()[0],
        "runner_sha256": _bam_lf(Path(__file__).read_bytes()),
        "aggregator_sha256": _bam_lf(Path(TH.__file__).read_bytes()),
        "model": _duy_nhat(q["model"] for q in qs),
        "prompt_sha256": _duy_nhat(q["system_prompt_sha256"] for q in qs),
        "schema_sha256": _duy_nhat(q["response_schema_sha256"] for q in qs),
        "case_order": list(hang_doi),
        "request_budget": len(hang_doi),
        "created_at_utc": dong_ho().astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dataset_class": meta.get("EVIDENCE_CLASS"),
        "temperature": _duy_nhat(q["temperature"] for q in qs),
        "timeout_seconds": 120,
        "retries": 0,
    }


def _tap(*nguon: Any) -> set[str]:
    """Giao của các nguồn kỳ vọng độc lập; nguồn vắng (`None`) ⇒ tập rỗng ⇒ mọi giá trị đều sai."""
    kq: set[str] | None = None
    for n in nguon:
        s = {json.dumps(x, sort_keys=True) for x in n if x is not None}
        kq = s if kq is None else kq & s
    return kq or set()


def ky_vong_rang_buoc() -> dict[str, set[str]]:
    """Giá trị ĐƯỢC PHÉP của từng trường — dẫn ĐỘC LẬP với ràng buộc đang kiểm."""
    head = TH._git("rev-parse", "HEAD").stdout.strip()
    ov = json.loads(Path(TH.REGISTRY_V2_PATH).read_text(encoding="utf-8"))
    dk = json.loads(EXPECTED_REQUESTS.read_text(encoding="utf-8"))["EXPECTED"]
    ung_vien = (json.loads(CANDIDATE_FILE.read_text(encoding="utf-8")).get("measured_system") or {}).get("tree_hash")
    mot = lambda xs: set(xs) if len(set(xs)) == 1 else set()  # noqa: E731 — nhiều giá trị ⇒ không đăng ký được
    return {
        "repository_identity": _tap([DANG_KY["repository_identity"]]),
        "branch": _tap([DANG_KY["branch"]]),
        "execution_head": _tap([head or None]),
        "cache_version": _tap([DANG_KY["cache_version"]]),
        "manifest_sha256": _tap([ov.get("manifest_sha256")]),
        "ground_truth_sha256": _tap([ov.get("ground_truth_sha256")]),
        "registry_v1_sha256": _tap([ov.get("base_registry_sha256")]),
        "registry_v2_sha256": _tap([DANG_KY["registry_v2_sha256"]]),
        "candidate_sha256": _tap([ov.get("product_candidate_hash")], [ung_vien]),
        "runner_sha256": _tap([_BAM_RUNNER_KHI_NAP], [_bam_da_commit(head, _duong_trong_kho(Path(__file__)))]),
        "aggregator_sha256": _tap([_BAM_BO_TONG_HOP_KHI_NAP],
                                  [_bam_da_commit(head, _duong_trong_kho(Path(TH.__file__)))]),
        "model": _tap([DANG_KY["model"]], [gemini.MODEL]),
        "prompt_sha256": _tap(mot([e.get("system_prompt_sha256") for e in dk])),
        "schema_sha256": _tap(mot([e.get("response_schema_sha256") for e in dk])),
        "case_order": _tap([DANG_KY["case_order"]]),
        "request_budget": _tap([DANG_KY["request_budget"]]),
    }


def kiem_rang_buoc_day_du(b: dict[str, Any]) -> None:
    """Fail closed với mã ổn định. Không tự điền, không lùi về ràng buộc cũ, không lùi v2 → v1."""
    for t in TRUONG_RANG_BUOC:
        if t not in b:
            raise TH.LoiRegistry(f"BINDING_FIELD_MISSING:{t}")
    for t in TRUONG_RANG_BUOC:
        if not _KIEU[t](b[t]):
            raise TH.LoiRegistry(f"BINDING_FIELD_TYPE:{t}")
    if not _MAU_GIO.fullmatch(b["created_at_utc"]):
        raise TH.LoiRegistry("BINDING_TIMESTAMP_INVALID")
    ky = ky_vong_rang_buoc()
    for t in THU_TU_KIEM:
        if json.dumps(b[t], sort_keys=True) not in ky[t]:
            raise TH.LoiRegistry(MA_TRUONG_SAI[t])


def ghi_rang_buoc(thu_muc: Path, b: dict[str, Any], khu: BoKhuBiMat) -> dict[str, Any]:
    """Mới ⇒ ghi nguyên tử, nạp lại, kiểm lại. Đã có (lượt nối lại) ⇒ phải TRÙNG mọi trường
    trừ mốc giờ, và tệp cũ giữ nguyên — không bao giờ thay ràng buộc giữa chừng lượt đo."""
    p = thu_muc / "REGISTRY_BINDING.json"
    bo_gio = lambda x: {k: v for k, v in x.items() if k != "created_at_utc"}  # noqa: E731
    if p.exists():
        cu = json.loads(p.read_text(encoding="utf-8"))
        if bo_gio(cu) != bo_gio(json.loads(json.dumps(khu(b), default=str))):
            raise TH.LoiRegistry("BINDING_RESUME_MISMATCH")
        kiem_rang_buoc_day_du(cu)
        return cu
    ghi_json_nguyen_tu(p, khu(b))
    nap = json.loads(p.read_text(encoding="utf-8"))
    kiem_rang_buoc_day_du(nap)
    return nap


# ══ R2 — NHẬT KÝ BỀN THEO TỪNG CA ══════════════════════════════════════════
#
# Bản /2 giữ bản ghi ca, quan sát request và bằng chứng ngân sách TRONG BỘ NHỚ tới hết
# vòng lặp: tiến trình chết ở P07 làm mất bản ghi của P06 dù request P06 đã trả tiền.
TRANG_THAI_CA = ("PLANNED", "RESERVED", "TRANSPORT_COMPLETED", "PROVIDER_ERROR", "SCORED",
                 "MEASUREMENT_ERROR", "TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH")
KET_CUC_DO_HONG = ("MEASUREMENT_ERROR", "TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH")
PHIEN_BAN_NHAT_KY = "completion-journal/1"


class LoiNhatKy(BaseException):
    """Bộ đo không ghi hoặc không đọc lại được trạng thái bền. Mã ổn định trong `ma`.

    `BaseException` CÓ CHỦ Ý: `CongHttp` bắt `Exception` và sẽ quy nhầm nó thành lỗi
    PROVIDER; `chay_mot_ca` sẽ chấm nó như kết cục của ca. Lỗi của bộ đo phải dừng lượt
    đo — và vì đặt chỗ bền đứng TRƯỚC transport, request lúc ấy chưa rời tiến trình.
    """

    def __init__(self, ma: str) -> None:
        super().__init__(ma)
        self.ma = ma


def ly_do_dung_ca(r: dict[str, Any]) -> str | None:
    """Chính sách dừng — MỘT định nghĩa cho vòng lặp và cho lượt nối lại."""
    if r.get("OUTCOME") == "REQUEST_EQUIVALENCE_FAILURE":
        return "REQUEST_EQUIVALENCE_FAILURE"
    if r.get("OUTCOME") in KET_CUC_DO_HONG:
        return r["OUTCOME"]
    if r.get("PROVIDER_ERROR"):
        return "PROVIDER_ERROR"
    if r.get("KIND") == "negative" and r.get("UNSAFE_ACCEPTANCE"):
        return "UNSAFE_ACCEPTANCE"
    if (r.get("BUILD") or {}).get("SILENT_QUALITY_FAILURE"):
        return "SILENT_QUALITY_FAILURE"
    return None


class NhatKyHoanTat:
    """Nhật ký BỀN của lượt completion. Mỗi chuyển trạng thái ghi nguyên tử TRƯỚC bước sau.

    `PLANNED` (trước khi dựng request) → `RESERVED` (đặt chỗ + ngân sách, TRƯỚC khi byte
    rời tiến trình) → `TRANSPORT_COMPLETED` | `PROVIDER_ERROR` (ngay khi transport trả/ném)
    → `SCORED` | `MEASUREMENT_ERROR`. Tệp `cases/<ca>.json` là nguồn sự thật; chỉ mục chỉ là
    tóm tắt. Không giữ thân request, thân phản hồi hay nội dung ngoại lệ.
    """

    def __init__(self, thu_muc: Path, thu_tu: list[str], tran: int, khu: BoKhuBiMat,
                 du_kien: dict[str, dict], dau: dict[str, Any]) -> None:
        self.thu_muc, self.thu_tu, self.tran, self.khu = thu_muc, list(thu_tu), tran, khu
        self.du_kien, self.dau = du_kien, dau
        self.ca: dict[str, dict[str, Any]] = {}
        self.tmp_da_don: list[str] = []
        self.cong: Any = None                               # cổng quan sát — gắn khi dựng transport

    # ── ghi ──────────────────────────────────────────────────────────────
    def _ghi(self, *ten: str, obj: Any) -> None:
        ghi_json_nguyen_tu(self.thu_muc.joinpath(*ten), self.khu(obj))

    def da_dat(self) -> int:
        """Số lần thử ĐÃ ĐẶT CHỖ — không bao giờ hoàn lại, kể cả khi kết cục không rõ."""
        return sum(1 for c in self.ca.values() if c.get("RESERVED"))

    def _ghi_chi_muc(self) -> None:
        self._ghi("COMPLETION_INDEX.json", obj={
            "JOURNAL_VERSION": PHIEN_BAN_NHAT_KY, "CASE_ORDER": self.thu_tu,
            "MAX_HTTP_REQUESTS": self.tran, "RESERVED_TOTAL": self.da_dat(),
            "CASES": {c: self.ca[c]["STATE"] for c in self.thu_tu if c in self.ca},
            "TMP_FILES_CLEANED": self.tmp_da_don})

    def ngan_sach(self) -> dict[str, Any]:
        return {"SOURCE": "COMPLETION_JOURNAL", "QUEUE": self.thu_tu, "MAX_PER_CASE": TRAN_MOI_CA,
                "MAX_HTTP_REQUESTS": self.tran, "RESERVED_TOTAL": self.da_dat(),
                "RESERVED_BY_CASE": {c: bool(self.ca.get(c, {}).get("RESERVED")) for c in self.thu_tu}}

    def _ghi_ngan_sach(self, them: dict[str, Any] | None = None) -> None:
        # Phần nhật ký đè phần tiến trình: MAX/QUEUE là của CẢ lượt, kể cả tiến trình trước.
        self._ghi("REQUEST_BUDGET_PROOF.json", obj={**(them or {}), **self.ngan_sach(),
                                                     "FINAL": them is not None})

    def _ghi_quan_sat(self) -> None:
        self._ghi("REQUEST_OBSERVATIONS.json", obj={
            "LAYER": "completion",
            "OBSERVATIONS": [q for c in self.thu_tu if c in self.ca
                             for q in self.ca[c]["REQUEST"].get("observations", ())],
            "EXPECTED_REGISTRY_SHA256_LF": TH._sha_lf(EXPECTED_REQUESTS),
            "_KHONG_GHI": "thân request, prompt, đề, query string, khoá, phản hồi thô"})

    def ket_qua_theo_thu_tu(self) -> list[dict[str, Any]]:
        return [self.ca[c]["RESULT"] for c in self.thu_tu if (self.ca.get(c) or {}).get("RESULT") is not None]

    def _ghi_tich_luy(self, cuoi: dict[str, Any] | None = None) -> None:
        self._ghi("COMPLETION_CASE_RESULTS_REDACTED.json", obj={
            **self.dau, "COMPLETE": cuoi is not None,
            **(cuoi or {"STOPPED_EARLY": None, "STOP_REASON": None}),
            "CASES": self.ket_qua_theo_thu_tu()})
        self._ghi_quan_sat()

    def _chuyen(self, cid: str, trang_thai: str, **truong: Any) -> None:
        c = self.ca[cid]
        c.update(truong)
        c["STATE"] = trang_thai
        c["HISTORY"].append(trang_thai)
        self._ghi("cases", f"{cid}.json", obj=c)            # nguồn sự thật TRƯỚC, chỉ mục sau
        self._ghi_chi_muc()

    # ── chuyển trạng thái ────────────────────────────────────────────────
    def bat_dau(self, cid: str, kind: str) -> None:
        """`PLANNED` — bền TRƯỚC khi request được dựng."""
        if self.da_dat() >= self.tran:
            raise LoiNhatKy("BUDGET_EXHAUSTED")
        c = self.ca.setdefault(cid, {"CASE_ID": cid, "KIND": kind, "STATE": None, "HISTORY": []})
        if c["STATE"] not in (None, "PLANNED"):
            raise LoiNhatKy("CASE_ALREADY_STARTED")
        k = self.du_kien.get(cid) or {}
        self._chuyen(cid, "PLANNED", REQUEST={
            "planned_body_sha256": k.get("body_sha256"),
            "planned_request_fingerprint": k.get("request_fingerprint"), "observations": []})

    def dat_truoc(self, cid: str | None, quan_sat: dict[str, Any]) -> None:
        """`RESERVED` — đặt chỗ + quan sát + ngân sách, tất cả BỀN, rồi mới được gọi transport."""
        c = self.ca.get(cid) if cid else None
        if c is None or c["STATE"] != "PLANNED":           # cũng chặn request thứ hai của cùng một ca
            raise LoiNhatKy("RESERVE_WITHOUT_PLAN")
        if self.da_dat() >= self.tran:
            raise LoiNhatKy("BUDGET_EXHAUSTED")
        self._chuyen(cid, "RESERVED", RESERVED=True, REQUEST={
            **c["REQUEST"], "observed_body_sha256": quan_sat.get("body_sha256"),
            "observed_request_fingerprint": quan_sat.get("request_fingerprint"),
            "equivalence": quan_sat.get("equivalence"), "observations": [quan_sat]})
        self._ghi_ngan_sach()
        self._ghi_quan_sat()

    def ket_qua_transport(self, cid: str, *, http_status: int | None, latency_ms: float,
                          usage: dict | None, loi_lop: str | None) -> None:
        """`TRANSPORT_COMPLETED` | `PROVIDER_ERROR` — ngay khi transport trả hoặc ném."""
        self._chuyen(cid, "PROVIDER_ERROR" if loi_lop else "TRANSPORT_COMPLETED", TRANSPORT={
            "http_status": http_status, "transport_latency_ms": latency_ms,
            "usage": usage or "UNKNOWN", "provider_error_class": loi_lop})

    def phan_tich(self, cid: str, r: dict[str, Any]) -> None:
        """Kết quả đọc đề (đã nhận output hay chưa, token, độ trễ) — bền TRƯỚC khi chấm."""
        c = self.ca[cid]
        c["ANALYZE"] = {**r, "usage": r.get("USAGE") or "UNKNOWN"}
        self._ghi("cases", f"{cid}.json", obj=c)

    def ket_qua(self, cid: str, r: dict[str, Any]) -> str:
        """`SCORED` | `MEASUREMENT_ERROR` (| giữ `PROVIDER_ERROR`) + bản ghi tích luỹ. Trả trạng thái."""
        c = self.ca[cid]
        if r.get("OUTCOME") in KET_CUC_DO_HONG + ("REQUEST_EQUIVALENCE_FAILURE",) or c["STATE"] == "PLANNED":
            tt = "MEASUREMENT_ERROR"                        # chưa bao giờ đặt chỗ ⇒ không phải kết cục của ca
        elif c["STATE"] == "PROVIDER_ERROR":
            tt = "PROVIDER_ERROR"
        else:
            tt = "SCORED"
        if self.cong is not None:
            qs = [q for q in self.cong.quan_sat if q.get("case_id") == cid]
            if qs:
                c["REQUEST"] = {**c["REQUEST"], "observations": qs}
        self._chuyen(cid, tt, RESULT=r)
        self._ghi_tich_luy()
        self._ghi_ngan_sach()
        return tt

    # ── nối lại ──────────────────────────────────────────────────────────
    def _ban_ghi_do_hong(self, c: dict[str, Any], ket_cuc: str, ma: str | None = None) -> dict[str, Any]:
        a = {k: v for k, v in (c.get("ANALYZE") or {}).items() if k != "usage"}
        t = c.get("TRANSPORT") or {}
        r = {"CASE_ID": c["CASE_ID"], "KIND": c.get("KIND"), "HTTP_STATUS": t.get("http_status"),
             "LATENCY_MS": None, "MODEL_OUTPUT_RECEIVED": None,
             "USAGE": t["usage"] if isinstance(t.get("usage"), dict) else {}, **a,
             "HTTP_REQUESTS_FOR_CASE": 1, "TRANSPORT_LATENCY_MS": t.get("transport_latency_ms"),
             "OUTCOME": ket_cuc}
        if ma:
            r["MEASUREMENT_ERROR_CODE"] = ma
        if t.get("provider_error_class"):
            r.setdefault("PROVIDER_ERROR", t["provider_error_class"])
        r["ATTRIBUTION"] = quy_ket_that_bai(r)
        return r

    def mo_lai(self) -> str | None:
        """Nạp nhật ký của tiến trình trước. Trả mã dừng, hoặc `None` nếu được đi tiếp.

        `RESERVED` không kết cục ⇒ `TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH`, KHÔNG gửi lại,
        ngân sách không hoàn. `TRANSPORT_COMPLETED` chưa chấm ⇒ `MEASUREMENT_ERROR`
        (đầu ra thô không được lưu nên không chấm lại được), KHÔNG gửi lại. `PLANNED` ⇒ chứng
        minh được là CHƯA gửi (đặt chỗ đứng trước transport) ⇒ lập kế hoạch lại.
        """
        sot = sorted(self.thu_muc.rglob("*.tmp"))
        self.tmp_da_don = [p.relative_to(self.thu_muc).as_posix() for p in sot]
        for p in sot:
            p.unlink()
        thu_muc_ca = self.thu_muc / "cases"
        try:
            for p in sorted(thu_muc_ca.glob("*.json")) if thu_muc_ca.is_dir() else ():
                c = json.loads(p.read_text(encoding="utf-8"))
                if (p.stem not in self.thu_tu or c.get("CASE_ID") != p.stem
                        or c.get("STATE") not in TRANG_THAI_CA):
                    raise ValueError
                self.ca[p.stem] = c
        except (OSError, ValueError, AttributeError):
            raise LoiNhatKy("JOURNAL_CORRUPT") from None
        dung: str | None = None
        for cid in self.thu_tu:
            c = self.ca.get(cid)
            if c is None or c["STATE"] == "PLANNED":
                continue
            if c["STATE"] == "RESERVED":
                self._chuyen(cid, "TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH",
                             RESULT=self._ban_ghi_do_hong(c, "TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH"))
                dung = dung or "TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH"
            elif c["STATE"] == "TRANSPORT_COMPLETED" and c.get("RESULT") is None:
                self._chuyen(cid, "MEASUREMENT_ERROR", RESULT=self._ban_ghi_do_hong(
                    c, "MEASUREMENT_ERROR", "SCORING_NOT_COMPLETED_AFTER_CRASH"))
                dung = dung or "MEASUREMENT_ERROR"
            elif c["STATE"] == "PROVIDER_ERROR" and c.get("RESULT") is None:
                self._chuyen(cid, "PROVIDER_ERROR", RESULT=self._ban_ghi_do_hong(c, "ANALYZE_OUTPUT_INVALID"))
                dung = dung or "PROVIDER_ERROR"
            elif c["STATE"] != "SCORED" or ly_do_dung_ca(c.get("RESULT") or {}):
                dung = dung or "RESUME_BLOCKED_TERMINAL_STATE"
        if self.ca or self.tmp_da_don:
            self._ghi_chi_muc()
        if self.ca:
            self._ghi_tich_luy()
            self._ghi_ngan_sach()
        return dung

    def ghi_cuoi(self, cuoi: dict[str, Any], ngan_sach: dict[str, Any]) -> None:
        self._ghi_tich_luy(cuoi)
        self._ghi_ngan_sach(ngan_sach)


class CongBenVung(httpx.AsyncBaseTransport):
    """Nằm GIỮA cổng ngân sách (`CongHttp`) và transport thật.

    Chỉ tới được đây khi ngân sách đã cho phép và request đã khớp kỳ vọng. Đặt chỗ bền
    TRƯỚC khi byte rời tiến trình; kết cục transport bền NGAY khi có — trước khi
    `call_gemini` kịp phân tích phản hồi. Chỉ số đếm token và tên lớp lỗi, không nội dung.
    """

    def __init__(self, inner: httpx.AsyncBaseTransport, nhat_ky: NhatKyHoanTat) -> None:
        self.inner, self.nhat_ky = inner, nhat_ky
        self.cong: CongQuanSat | None = None

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        cid = self.cong.case_id if self.cong is not None else None
        q = next((x for x in reversed(self.cong.quan_sat) if x.get("case_id") == cid), None) \
            if self.cong is not None else None
        self.nhat_ky.dat_truoc(cid, q or quan_sat_request(request))
        t0 = time.perf_counter()
        try:
            res = await self.inner.handle_async_request(request)
        except Exception as e:
            self.nhat_ky.ket_qua_transport(cid, http_status=None, usage=None, loi_lop=type(e).__name__,
                                           latency_ms=round((time.perf_counter() - t0) * 1000, 1))
            raise
        usage = None
        if 200 <= res.status_code < 300:
            try:
                usage = chi_so_token(json.loads(await res.aread()).get("usageMetadata"))
            except (ValueError, AttributeError):
                usage = None
        self.nhat_ky.ket_qua_transport(
            cid, http_status=res.status_code, usage=usage,
            loi_lop=None if 200 <= res.status_code < 300 else f"HTTP_{res.status_code}",
            latency_ms=round((time.perf_counter() - t0) * 1000, 1))
        return res

    async def aclose(self) -> None:
        return None                                          # như CongHttp: transport thật sống cả lượt


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
#: Lớp ngoại lệ được phép XUẤT HIỆN (tên lớp, không bao giờ nội dung) trong mã lỗi chấm.
LOI_CHAM_CHO_PHEP = frozenset({
    "KeyError", "IndexError", "LookupError", "TypeError", "ValueError", "AttributeError",
    "ArithmeticError", "ZeroDivisionError", "OverflowError", "AssertionError", "RuntimeError",
    "NotImplementedError", "RecursionError"})


def ma_loi_cham(e: Exception) -> str:
    """Mã ỔN ĐỊNH cho lỗi ở tầng chấm. Không thông điệp, không traceback, không giá trị thô."""
    if isinstance(e, TH.LoiRegistry):
        return f"SCORING_REGISTRY:{e.ma}"
    ten = type(e).__name__
    return f"SCORING_EXCEPTION:{ten if ten in LOI_CHAM_CHO_PHEP else 'UNLISTED'}"


def _ban_ghi_van_chuyen(ca: dict, cong: Any, hd: Any, err: Any, no: Any, latency: float) -> dict[str, Any]:
    """Phần của bản ghi mà REQUEST quyết định — tồn tại dù tầng chấm có hỏng."""
    cid = ca["case_id"]
    # GHÉP CA theo `case_id` của chính bản ghi — không lấy "bản ghi cuối".
    ban_ghi = [x for x in cong.records if x["case_id"] == cid]
    usage = next((x.get("usage_metadata") for x in ban_ghi if x.get("usage_metadata")),
                 None) or {}
    qs = [q for q in getattr(cong, "quan_sat", ()) if q.get("case_id") == cid]
    return {
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
        "REQUEST_EQUIVALENCE": qs[-1]["equivalence"] if qs else "NOT_OBSERVED",
    }


async def chay_mot_ca(ca: dict, gt: dict, key: str, cong: Any,
                      nhat_ky: NhatKyHoanTat | None = None) -> dict[str, Any]:
    from app.ai import pipeline as PL
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC

    cid = ca["case_id"]
    if nhat_ky is not None:
        nhat_ky.bat_dau(cid, ca["kind"])                   # PLANNED — bền trước khi dựng request
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

    # R3: từ đây, request (nếu có) ĐÃ tiêu. Mọi lỗi của bộ đo thành một bản ghi an toàn —
    # quan sát, ngân sách, token, độ trễ còn nguyên — rồi lượt đo dừng. Bản chấm dở bị bỏ.
    r: dict[str, Any] = {"CASE_ID": cid, "KIND": ca["kind"], "LATENCY_MS": latency}
    try:
        r = _ban_ghi_van_chuyen(ca, cong, hd, err, no, latency)
        if nhat_ky is not None:
            nhat_ky.phan_tich(cid, r)                       # bền TRƯỚC khi chấm
        return _cham_ca(ca, gt, cong, hd, dict(r))
    except Exception as e:  # noqa: BLE001
        r = dict(r)
        r.setdefault("HTTP_REQUESTS_FOR_CASE", len([x for x in cong.records
                                                    if x["case_id"] == cid and x["sent"]]))
        r.update(OUTCOME="MEASUREMENT_ERROR", MEASUREMENT_ERROR_CODE=ma_loi_cham(e))
        r["ATTRIBUTION"] = quy_ket_that_bai(r)
        return r, None


def _cham_ca(ca: dict, gt: dict, cong: Any, hd: Any, r: dict[str, Any]) -> tuple:
    """Chấm MỘT ca trên bản ghi vận chuyển. Ném ⇒ `chay_mot_ca` biến thành `MEASUREMENT_ERROR`."""
    cid = ca["case_id"]
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

    def chan_rang_buoc(e: TH.LoiRegistry) -> int:
        ghi_json_nguyen_tu(thu_muc / "PRECHECK_REGISTRY_BINDING.json",
                           khu({"RESULT": e.ma, "MODEL_REQUESTS_USED": 0}))
        kenh.loi(f"Ràng buộc không đạt ({e.ma}) — dừng với 0 request.")
        return EXIT_PRECHECK

    # ── RÀNG BUỘC REGISTRY v2 (ngữ nghĩa) — 0 request ───────────────────────
    try:
        meta_registry = kiem_rang_buoc_registry()
    except TH.LoiRegistry as e:
        return chan_rang_buoc(e)

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

    # ── R1: RÀNG BUỘC ĐỦ 17 TRƯỜNG — dựng, kiểm, ghi nguyên tử, nạp lại, kiểm lại ─
    try:
        rang_buoc = dung_rang_buoc(hang_doi, du_kien, meta_registry)
        kiem_rang_buoc_day_du(rang_buoc)
        rang_buoc = ghi_rang_buoc(thu_muc, rang_buoc, khu)
    except TH.LoiRegistry as e:
        return chan_rang_buoc(e)

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

    # ── R2: NHẬT KÝ BỀN — mở, hoặc nối lại lượt trước KHÔNG gửi lại gì ─────
    nhat_ky = NhatKyHoanTat(thu_muc, hang_doi, len(hang_doi), khu, du_kien, dau={
        "WAVE": WAVE, "LAYER": "completion", "RUNNER_VERSION": RUNNER_VERSION,
        "EVALUATOR_VERSION": EVALUATOR_VERSION, "DATASET_SHA256": canonical_dataset_sha(reg, gt),
        "QUEUE": hang_doi, "TARGETED_REGISTRY": rang_buoc})
    try:
        dung_nhat_ky = nhat_ky.mo_lai()
    except LoiNhatKy as e:
        kenh.loi(f"Nhật ký lượt trước hỏng ({e.ma}) — dừng với 0 request.")
        return EXIT_PRECHECK
    da_co = nhat_ky.ket_qua_theo_thu_tu()
    kq += [{**r, "TU_TIEN_TRINH_TRUOC": True} for r in da_co]
    if dung_nhat_ky == "RESUME_BLOCKED_TERMINAL_STATE":
        kenh.loi("Lượt trước đã dừng ở trạng thái kết thúc — không chạy tiếp, không gửi lại.")
        return EXIT_PRECHECK
    if dung_nhat_ky:
        return _ket_thuc(thu_muc, nhat_ky, None, True, dung_nhat_ky, khu, kenh)
    hang_con = [c for c in hang_doi if (nhat_ky.ca.get(c) or {}).get("STATE") in (None, "PLANNED")]
    if len(hang_con) != nhat_ky.tran - nhat_ky.da_dat():
        kenh.loi("Sổ ngân sách của nhật ký lệch hàng đợi — dừng với 0 request.")
        return EXIT_PRECHECK
    if not hang_con:
        kenh.in_("Mọi ca đã có kết cục trong nhật ký.")
        return EXIT_PRECHECK

    ben = CongBenVung(httpx.AsyncHTTPTransport(), nhat_ky)
    cong = tao_cong_completion(ben, hang_con, khu, gt, du_kien=du_kien)
    ben.cong = nhat_ky.cong = cong
    dung_som, ly_do_dung = False, None

    async def chay_tat_ca() -> None:
        """MỘT vòng lặp asyncio cho CẢ lượt.

        ⚠️ Bản đầu gọi `asyncio.run` MỘT LẦN MỖI CA: `httpx.AsyncHTTPTransport` gắn
        vào vòng lặp của ca đầu, ca thứ hai chết bằng `Event loop is closed`.
        """
        nonlocal dung_som, ly_do_dung
        for giai_doan, ds in (("A", reg["stage_a_order"]), ("B", reg["stage_b_order"])):
            con = [c for c in ds if c in hang_con]
            if giai_doan == "B" and con:
                gate = cong_stage_a(kq)
                ghi_json_nguyen_tu(thu_muc / "STAGE_A_GATE.json", khu(gate))
                kenh.in_(f"— CỔNG GIAI ĐOẠN A: {'MỞ' if gate['MO_STAGE_B'] else 'ĐÓNG'}")
                if not gate["MO_STAGE_B"]:
                    dung_som, ly_do_dung = True, "STAGE_A_GATE_CLOSED"
                    break
            for cid in con:
                r, env = await chay_mot_ca(bang[cid], gt, key, cong, nhat_ky)
                r["STAGE"] = giai_doan
                if env is not None:
                    # G7: ghi NGAY, trước ca kế — không đợi hết vòng lặp.
                    ghi_envelope_nguyen_tu(thu_muc / "envelopes", cid, env)
                # R2: bản ghi rút gọn + chỉ mục + tổng hợp tích luỹ BỀN trước khi sang ca kế.
                trang_thai_ca = nhat_ky.ket_qua(cid, r)
                kq.append(r)
                kenh.in_(f"  {cid} [{giai_doan}] {r['OUTCOME']}"
                         + (f" · {r.get('REJECTION_CODE')}" if r["KIND"] == "negative" else ""))
                ld = ly_do_dung_ca(r) or ("MEASUREMENT_ERROR" if trang_thai_ca == "MEASUREMENT_ERROR" else None)
                if ld:
                    dung_som, ly_do_dung = True, ld
                    break
            if dung_som:
                break

    try:
        asyncio.run(chay_tat_ca())
    except LoiNhatKy as e:
        # Đặt chỗ bền đứng trước transport ⇒ request của ca đang dở CHƯA rời tiến trình.
        kenh.loi(f"Nhật ký không ghi bền được ({e.ma}) — dừng; trạng thái trên đĩa là nguồn sự thật.")
        return EXIT_FAIL
    return _ket_thuc(thu_muc, nhat_ky, cong, dung_som, ly_do_dung, khu, kenh)


def _ket_thuc(thu_muc: Path, nhat_ky: NhatKyHoanTat, cong: Any, dung_som: bool,
              ly_do_dung: str | None, khu: BoKhuBiMat, kenh: KenhIn) -> int:
    """Bản cuối của ba artifact tích luỹ + tổng hợp — đọc từ NHẬT KÝ, gồm cả tiến trình trước."""
    http = cong.tong_hop() if cong is not None else {}
    nhat_ky.ghi_cuoi(
        {"STOPPED_EARLY": dung_som, "STOP_REASON": ly_do_dung, **http,
         **(cong.bang_chung_danh_tinh() if cong is not None else {})},
        {**http, "PROCESS_SCOPE": "các số HTTP_* là của TIẾN TRÌNH này; RESERVED_* là của cả lượt",
         "TRAN_THEO_TANG": cong.tran_theo_tang if cong is not None else None,
         # Vòng sửa chỉ tồn tại ở tầng synthesis, mà trần synthesis là 0.
         "REPAIR_REQUESTS": http.get("SYNTHESIS_HTTP_REQUESTS", 0),
         "PER_CASE": {c: int(v) for c, v in nhat_ky.ngan_sach()["RESERVED_BY_CASE"].items()}})
    tk = TH.tong_hop(nhat_ky.ket_qua_theo_thu_tu(), completion_stop_reason=ly_do_dung)
    for ten, obj in (("AGGREGATE_12_CASE_RESULTS.json", tk),
                     ("ACCEPTANCE_STATISTICS.json", {k: tk.get(k) for k in (
                         "CLASSIFICATION", "NEXT_ACTION", "COUNTS", "METRICS", "TOKENS", "LATENCY",
                         "MEASUREMENT_INVALID_REASONS", "TOKEN_OPTIMIZATION")})):
        if not (thu_muc / ten).exists():
            _ghi_json(thu_muc, ten, obj, khu)
    kenh.in_(f"CLASSIFICATION = {tk['CLASSIFICATION']} · ĐẶT CHỖ {nhat_ky.da_dat()}/{nhat_ky.tran}"
             f" · ANALYZE (tiến trình này) {http.get('ANALYZE_HTTP_REQUESTS', 0)}"
             f" · VISION {http.get('VISION_HTTP_REQUESTS', 0)} · SYNTHESIS {http.get('SYNTHESIS_HTTP_REQUESTS', 0)}"
             f" · RETRIES {http.get('RETRIES', 0)}")
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
