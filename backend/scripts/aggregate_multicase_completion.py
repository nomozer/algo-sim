# -*- coding: utf-8 -*-
"""BỘ TỔNG HỢP TẤT ĐỊNH cho benchmark 12 ca — lịch sử + completion.

`COMPLETION_RUNNER_REPAIR_OFFLINE` (2026-09-21). Thẩm quyền DUY NHẤT cho:
quy kết thất bại theo mã ổn định · đối chiếu từ chối ĐÚNG khiếm khuyết ở ca âm ·
token (UNKNOWN không bao giờ thành 0) · độ trễ (lỗi provider tách khỏi thành
công) · phân loại benchmark và nhãn NEXT_ACTION.

─── VÌ SAO TÁCH KHỎI RUNNER ────────────────────────────────────────────────

Runner đo MỘT lượt. Kết luận thì cần CẢ lịch sử: hai lượt live cũ (một lượt
void vì bộ đo, một lượt dừng ở timeout P06) cộng lượt completion. Tổng hợp viết
tay sau lượt live là "không tái tạo được phép tổng hợp" ⇒ `MEASUREMENT_INVALID`.
Module này đọc bằng chứng lịch sử QUA BĂM (`HISTORICAL_EVIDENCE_LINK.json`):
một byte lệch là dừng, không tổng hợp trên dữ liệu đã trôi.

─── BẤT BIẾN ───────────────────────────────────────────────────────────────

· Mỗi case ID đúng MỘT kết cục cuối: lượt hợp lệ MUỘN NHẤT. Lượt void và lượt
  lỗi provider ở lại trong lịch sử request, không tạo ca thứ hai.
· Đính chính N01 lấy từ lớp đính chính ĐÃ CÔNG BỐ, không chấm lại output lịch sử.
· Không timestamp trong output: hai lần chạy cùng đầu vào cho cùng byte.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

GOC = Path(__file__).resolve().parents[1]
REPO = GOC.parent
if str(GOC) not in sys.path:            # chạy CLI độc lập vẫn nhập được hằng số luật của sản phẩm
    sys.path.insert(0, str(GOC))
DGEO = REPO / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene"
HIST_DIR = DGEO / "multicase-benchmark"
LINK_FILE = DGEO / "multicase-benchmark-completion" / "HISTORICAL_EVIDENCE_LINK.json"
REGISTRY_DIR = DGEO / "completion-runner-repair-offline"
AGGREGATOR_VERSION = "multicase-aggregator/2"

#: Registry v2 — OVERLAY lên v1 (`N04_TARGETED_REJECTION_REGISTRY_V2_PREREGISTRATION`).
#: Đọc qua tên module lúc gọi (không bắt vào tham số mặc định) để test thay được.
REGISTRY_V2_PATH = (DGEO / "n04-targeted-rejection-registry-v2-preregistration"
                    / "NEGATIVE_TARGETED_REJECTION_REGISTRY_V2.json")
PHIEN_BAN_V1 = "negative-targeted-rejection/1"
PHIEN_BAN_V2 = "negative-targeted-rejection/2"
#: Chính sách ĐÓNG: overlay chỉ được ghi đè đúng các ca này.
CHO_PHEP_GHI_DE: tuple[str, ...] = ("N04",)
VAI_TRO_HOI_QUY = "DEVELOPMENT_REGRESSION_CASE"
#: Tuple hành vi mà overlay PHẢI khai — thiếu một trường là overlay hỏng.
TRUONG_TUPLE: tuple[str, ...] = (
    "adapter_status", "rejection_code", "rule_id", "rejection_phase", "compiler_reached",
    "program_created", "scene_created", "final_memory_created", "answer_created")


class LoiRegistry(Exception):
    """Registry v2 không dùng được. Mã ỔN ĐỊNH; không bao giờ âm thầm lùi về v1."""

    def __init__(self, ma: str, chi_tiet: str = "") -> None:
        super().__init__(f"{ma}: {chi_tiet}" if chi_tiet else ma)
        self.ma = ma

#: Mã quy kết ổn định. 17 mã đầu là bộ mã của đặc tả; hai mã cuối giữ hai phân
#: biệt đã được các wave trước chứng minh là đắt: "mô hình khai mà server chưa
#: neo được điểm" và "mô hình đọc ĐÚNG mà hệ vẫn chấp nhận đầu vào hỏng".
MA_QUY_KET = (
    "PROVIDER_ERROR", "JSON_PARSE_FAILURE", "PYDANTIC_FAILURE",
    "MODEL_MALFORMED_RELATION", "REQUIRED_RELATION_MISSING", "UNVERIFIED_RELATION",
    "MODEL_ASSUMPTION_USED", "FACT_GRAPH_REJECTION", "COMPILER_UNSUPPORTED",
    "PROGRAM_VALIDATION_FAILURE", "GROUNDING_REJECTION", "ROUTE_REJECTION",
    "VISUAL_GATE_REJECTION", "TOPOLOGY_FAILURE", "FINAL_MEMORY_FAILURE",
    "ANSWER_FAILURE", "SILENT_QUALITY_FAILURE",
    "SERVER_POINT_BINDING_GAP", "PRODUCT_ACCEPTED_DEFECTIVE_INPUT",
)

NEXT_ACTION = {
    "STRONG_PILOT_RESULT": "PRIMITIVE_COMPILER_OPT_IN_CANARY_ROUTING_DESIGN",
    "READY_FOR_CANARY_DESIGN": "PRIMITIVE_COMPILER_OPT_IN_CANARY_ROUTING_DESIGN",
    "MORE_EVIDENCE_NEEDED": "ANALYZE_FAILURE_CLUSTER_DIAGNOSIS",
    "NOT_READY": "STRUCTURED_ANALYZE_GENERALIZATION_DIAGNOSIS",
    "UNSAFE": "STRUCTURED_RELATION_SAFETY_REPAIR",
    "PROVIDER_INCOMPLETE": "RETRY_STILL_MISSING_CASES_LATER",
    "MEASUREMENT_INVALID": "MULTICASE_BENCHMARK_MEASUREMENT_REPAIR",
}

#: Lý do thiếu kết cục được tính là "do provider". Mọi lý do khác ⇒ phép đo hỏng.
LY_DO_PROVIDER = frozenset({"PROVIDER_ERROR", "NOT_RUN_AFTER_PROVIDER_ERROR"})

#: Dấu hiệu sự cố thuộc về BỘ ĐO, không thuộc nhà cung cấp. Danh sách ĐÓNG và
#: cố ý hẹp: chỉ những lỗi mà nguyên nhân nằm hẳn trong mã của ta.
DAU_HIEU_BO_DO = ("Event loop is closed", "RuntimeError: Event loop",
                  "AttributeError", "KeyError", "TypeError", "NameError")

MA_RELATION_INVALID = "STRUCTURED_RELATION_INVALID"
MA_REFERENCE_UNKNOWN = "STRUCTURED_RELATION_REFERENCE_UNKNOWN"


def _sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8") if isinstance(b, str) else b).hexdigest()


def _sha_lf(p: Path) -> str:
    return _sha(p.read_bytes().replace(b"\r\n", b"\n"))


def _doc(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def loai_su_co(kq: list[dict]) -> str | None:
    """`PROVIDER` · `APPARATUS` · `None`.

    ⚠️ Phân biệt này đắt. Lượt chạy đầu của benchmark chết vì `Event loop is
    closed` — khuyết tật của chính runner — và bị chấm `PROVIDER_INCOMPLETE`.
    Một sự cố của bộ đo luôn là `MEASUREMENT_INVALID`, không bao giờ là lỗi ngoài.
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


def wilson(k: int, n: int) -> list[float] | None:
    if n == 0:
        return None
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def _la_loi_provider(r: dict) -> bool:
    return bool(r.get("PROVIDER_ERROR")) and not r.get("MODEL_OUTPUT_RECEIVED")


def trang_thai(r: dict) -> str:
    """Trạng thái MỘT lần thử: `VALID` · `VOID` · `PROVIDER_ERROR` · `REQUEST_EQUIVALENCE_FAILURE`."""
    if r.get("REQUEST_EQUIVALENCE") == "MISMATCH" or r.get("OUTCOME") == "REQUEST_EQUIVALENCE_FAILURE":
        return "REQUEST_EQUIVALENCE_FAILURE"
    if loai_su_co([r]) == "APPARATUS":
        return "VOID"
    if _la_loi_provider(r):
        return "PROVIDER_ERROR"
    return "VALID"


# ══ G5 — QUY KẾT THẤT BẠI ═════════════════════════════════════════════════
def _the_phan_tich(r: dict) -> list[str]:
    rel = r.get("RELATION") or {}
    ma = {e.get("code") for e in rel.get("REJECTED_RELATION_CODES") or ()}
    the: list[str] = []
    if MA_RELATION_INVALID in ma or rel.get("DUPLICATE_RELATION_COUNT"):
        the.append("MODEL_MALFORMED_RELATION")
    if MA_REFERENCE_UNKNOWN in ma:
        # Điểm mô hình nhắc mà hợp đồng không có ⇒ server chưa neo được, không phải mô hình bịa.
        the.append("SERVER_POINT_BINDING_GAP" if rel.get("UNBOUND_POINTS") else "UNVERIFIED_RELATION")
    if (rel.get("UNVERIFIED_EXTRA_RELATION_COUNT") or rel.get("EXTRA_DERIVED_AS_GIVEN_COUNT")
            or rel.get("SOURCE_FACT_RESOLUTION") == "FAIL"):
        the.append("UNVERIFIED_RELATION")
    if rel.get("MODEL_ASSUMPTION_COUNT"):
        the.append("MODEL_ASSUMPTION_USED")
    if rel.get("MISSING_RELATION_COUNT"):
        the.append("REQUIRED_RELATION_MISSING")
    return list(dict.fromkeys(the))


def _the_dung(b: dict) -> list[str]:
    """Theo đúng thứ tự tầng của đường dựng — tầng hỏng ĐẦU TIÊN là quy kết chính."""
    the: list[str] = []
    if b.get("ADAPTER_STATUS") not in (None, "VALID") or b.get("COMPILER_ELIGIBILITY") == "NO_GRAPH":
        the.append("FACT_GRAPH_REJECTION")
    elif b.get("COMPILER_ELIGIBILITY") not in (None, "SUPPORTED"):
        the.append("COMPILER_UNSUPPORTED")
    if (b.get("COMPILE_STATUS") not in (None, "COMPILED", "NOT_ELIGIBLE", "NO_GRAPH")
            or b.get("PYDANTIC_PROGRAM_VALIDATION") == "FAIL" or b.get("DETERMINISTIC") is False):
        the.append("PROGRAM_VALIDATION_FAILURE")
    route = str(b.get("ROUTE_RESULT") or "")
    if route.startswith("rejected/"):
        the.append("GROUNDING_REJECTION" if "ground" in route.lower() else "ROUTE_REJECTION")
    if b.get("VISUAL_OBLIGATION_GATE") not in (None, "COVERED"):
        the.append("VISUAL_GATE_REJECTION")
    if (b.get("TOPOLOGY_RESULT") == "FAIL" or False in (
            b.get("SQUARED_LENGTHS_OK"), b.get("PERPENDICULAR_OK"), b.get("NON_COLLINEAR_OK"),
            b.get("DERIVED_PERPENDICULAR_MATCHES_GROUND_TRUTH"),
            b.get("EVERY_DERIVED_RELATION_HAS_PROVENANCE"))):
        the.append("TOPOLOGY_FAILURE")
    if b.get("FINAL_MEMORY_OK") is False:
        the.append("FINAL_MEMORY_FAILURE")
    if b.get("ANSWER_OK") is False:
        the.append("ANSWER_FAILURE")
    if b.get("SILENT_QUALITY_FAILURE"):
        the.append("SILENT_QUALITY_FAILURE")
    return the


def quy_ket_that_bai(r: dict) -> dict[str, Any]:
    """Quy kết MỘT bản ghi ca — chỉ đọc trường có cấu trúc, không đọc thông điệp tự do.

    Trả `{"PRIMARY": mã | None, "TAGS": [mã…]}`. `PRIMARY = None` ⇔ ca không trượt.
    Chạy được trên bản ghi lịch sử đã khử thô lẫn bản ghi completion: một định nghĩa.
    Request lệch byte và lượt void là PHÉP ĐO hỏng, không phải kết cục của ca ⇒ không quy kết.
    """
    tt = trang_thai(r)
    if tt in ("REQUEST_EQUIVALENCE_FAILURE", "VOID"):
        return {"PRIMARY": None, "TAGS": [], "MEASUREMENT_STATUS": tt}
    if _la_loi_provider(r):
        return {"PRIMARY": "PROVIDER_ERROR", "TAGS": ["PROVIDER_ERROR"]}
    if not r.get("MODEL_OUTPUT_RECEIVED"):
        ma = "JSON_PARSE_FAILURE" if r.get("JSON_PARSE_RESULT") == "FAIL" else "PYDANTIC_FAILURE"
        return {"PRIMARY": ma, "TAGS": [ma]}
    if r.get("KIND") == "negative":
        if not r.get("UNSAFE_ACCEPTANCE"):
            return {"PRIMARY": None, "TAGS": []}
        the = [t for t in _the_phan_tich(r) if t in ("UNVERIFIED_RELATION", "MODEL_ASSUMPTION_USED")]
        chinh = the[0] if the else "PRODUCT_ACCEPTED_DEFECTIVE_INPUT"
        return {"PRIMARY": chinh, "TAGS": list(dict.fromkeys([chinh, *the]))}
    if r.get("OUTCOME") == "FULL_PIPELINE_PASS":
        return {"PRIMARY": None, "TAGS": []}
    if r.get("ANALYZE_PASS") is False or "BUILD" not in r:
        the = _the_phan_tich(r) or ["REQUIRED_RELATION_MISSING"]
        return {"PRIMARY": the[0], "TAGS": the}
    the = _the_dung(r.get("BUILD") or {})
    if "SILENT_QUALITY_FAILURE" in the:
        return {"PRIMARY": "SILENT_QUALITY_FAILURE", "TAGS": the}
    return {"PRIMARY": the[0] if the else "PROGRAM_VALIDATION_FAILURE", "TAGS": the}


# ══ G3 + G8 — REGISTRY CA ÂM VÀ ĐỐI CHIẾU TỪ CHỐI ĐÚNG KHIẾM KHUYẾT ═══════
def doc_registry_ca_am(registry_dir: Path = REGISTRY_DIR) -> tuple[dict, dict]:
    return (_doc(registry_dir / "NEGATIVE_EXPLICIT_RELATION_REGISTRY.json"),
            _doc(registry_dir / "NEGATIVE_TARGETED_REJECTION_REGISTRY.json"))


def _khop_cam(q: tuple[str, tuple[str, ...]], mau: dict) -> bool:
    if q[0] != mau["kind"]:
        return False
    tap = mau.get("points_subset_of")
    return tap is None or set(q[1]) <= set(tap)


def doi_chieu_tu_choi(r: dict, cid: str, rel_reg: dict, tgt_reg: dict) -> dict[str, Any]:
    """`TARGETED_REJECTION_MATCH`: từ chối vì ĐÚNG khiếm khuyết đã đăng ký, không chỉ "an toàn".

    Chỉ đo thứ MÔ HÌNH cung cấp (nghĩa vụ, quan hệ khai ở dạng dùng được). Độ dài
    trong FactGraph do server đọc từ đề, nên nó có mặt cả khi mô hình trả `{}`.
    Bản ghi thiếu trường cần (output lịch sử đã khử thô) ⇒ `NOT_MEASURED`, không đoán.
    """
    if "OBLIGATION_KINDS" not in r or "DECLARED_RELATIONS" not in r:
        return {"ANALYZE_INFORMATION_COMPLETENESS": "NOT_MEASURED",
                "TARGETED_REJECTION_MATCH": "NOT_MEASURED",
                "TARGETED_DETAIL": {"reason": "bản ghi không mang OBLIGATION_KINDS/DECLARED_RELATIONS"}}
    t = tgt_reg["CASES"][cid]
    can = {(q["kind"], tuple(q["canonical_args"])) for q in rel_reg["CASES"][cid]["relations"]}
    dung_duoc = {(q["kind"], tuple(q["canonical_args"])) for q in r["DECLARED_RELATIONS"]
                 if q.get("usable_by_construction") and not q.get("model_assumption")}
    du_nghia_vu = set(tgt_reg["MINIMUM_OBSERVED_FACTS"]["obligation_kinds"]) <= set(r["OBLIGATION_KINDS"])
    du_quan_he = can <= dung_duoc
    vi_pham = sorted([list(q[0:1]) + list(q[1]) for q in dung_duoc
                      if any(_khop_cam(q, m) for m in t["forbidden_usable_relations"])])
    ma = r.get("REJECTION_CODE")
    dung_ma = ma in t["allowed_exact_codes"]
    khong_canh = ((r.get("BUILD") or {}).get("COMPILE_STATUS") != "COMPILED"
                  and not r.get("UNSAFE_ACCEPTANCE"))
    day_du = "PASS" if (du_nghia_vu and du_quan_he) else "FAIL"
    dat = day_du == "PASS" and dung_ma and khong_canh and not vi_pham
    return {"ANALYZE_INFORMATION_COMPLETENESS": day_du,
            "TARGETED_REJECTION_MATCH": "YES" if dat else "NO",
            "TARGETED_DETAIL": {
                "intended_defect_class": t["intended_defect_class"],
                "obligations_observed": du_nghia_vu, "minimum_relations_observed": du_quan_he,
                "missing_minimum_relations": sorted([k, list(a)] for k, a in can - dung_duoc),
                "rejection_code": ma, "rejection_code_matches": dung_ma,
                "no_scene_built": khong_canh, "forbidden_usable_relations": vi_pham}}


# ══ REGISTRY V2 — OVERLAY, KHÔNG PHẢI NGUỒN SỰ THẬT CẠNH TRANH ═══════════
def _json_khong_trung_khoa(t: str) -> Any:
    def hook(cap):
        khoa = [k for k, _ in cap]
        trung = sorted({k for k in khoa if khoa.count(k) > 1})
        if trung:
            raise LoiRegistry("DUPLICATE_OVERRIDE" if set(trung) & {"N01", "N02", "N03", "N04"}
                              else "DUPLICATE_KEY", ",".join(trung))
        return dict(cap)
    return json.loads(t, object_pairs_hook=hook)


def _git(*a: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True, encoding="utf-8")


def _kiem_product_head(h: str) -> str:
    """Commit hành vi sản phẩm phải TỒN TẠI, là tổ tiên của HEAD, và MANG bản sửa an toàn."""
    from app.simulation.geometry_compiler.fact_graph import LUAT_NHIEU_DINH_VUONG
    r = _git("rev-parse", "--verify", "--quiet", f"{h}^{{commit}}")
    if r.returncode != 0:
        raise LoiRegistry("PRODUCT_HEAD_INVALID", "commit không tồn tại")
    full = r.stdout.strip()
    if _git("merge-base", "--is-ancestor", full, "HEAD").returncode != 0:
        raise LoiRegistry("PRODUCT_HEAD_INVALID", "không phải tổ tiên của HEAD")
    fg = _git("show", f"{full}:backend/app/simulation/geometry_compiler/fact_graph.py")
    if fg.returncode != 0 or LUAT_NHIEU_DINH_VUONG not in fg.stdout:
        raise LoiRegistry("PRODUCT_HEAD_INVALID", "commit không mang bản sửa an toàn")
    return full


def doc_registry_tu_choi_v2(v2_path: Path | None = None) -> dict[str, Any]:
    """v1 (xác minh băm) + overlay v2 (chỉ N04) ⇒ registry ĐÃ GIẢI, tất định. Fail closed."""
    p = Path(v2_path) if v2_path is not None else REGISTRY_V2_PATH
    if not p.exists():
        raise LoiRegistry("REGISTRY_V2_MISSING", p.name)
    ov = _json_khong_trung_khoa(p.read_text(encoding="utf-8"))
    if (ov.get("version") != PHIEN_BAN_V2 or ov.get("kind") != "OVERLAY"
            or ov.get("base_registry_version") != PHIEN_BAN_V1):
        raise LoiRegistry("OVERLAY_VERSION_INVALID")
    goc = REPO / str(ov.get("base_registry_path", ""))
    if not goc.is_file():
        raise LoiRegistry("BASE_REGISTRY_MISSING", str(ov.get("base_registry_path")))
    if _sha_lf(goc) != ov.get("base_registry_sha256"):
        raise LoiRegistry("BASE_REGISTRY_HASH_MISMATCH")
    v1 = _doc(goc)
    if v1.get("REGISTRY") != PHIEN_BAN_V1:
        raise LoiRegistry("OVERLAY_VERSION_INVALID", "base không phải v1")
    head = _kiem_product_head(str(ov.get("product_behavior_head", "")))
    if (_sha_lf(HIST_DIR / "BENCHMARK_MANIFEST.json") != ov.get("manifest_sha256")
            or _sha_lf(HIST_DIR / "GROUND_TRUTH.json") != ov.get("ground_truth_sha256")):
        raise LoiRegistry("DATASET_HASH_MISMATCH")

    ghi_de = ov.get("overrides") or {}
    for cid in ghi_de:
        if cid not in v1["CASES"]:
            raise LoiRegistry("OVERRIDE_CASE_NOT_IN_BASE", cid)
    if list(ov.get("allowed_override_case_ids") or ()) != list(CHO_PHEP_GHI_DE) \
            or not set(ghi_de) <= set(CHO_PHEP_GHI_DE):
        raise LoiRegistry("OVERRIDE_CASE_NOT_ALLOWED", ",".join(sorted(ghi_de)))
    reg = _doc(HIST_DIR / "CASE_REGISTRY.json")
    theo_ca = {c["case_id"]: c for c in reg["cases"]}
    giai = json.loads(json.dumps(v1))
    vai_tro = {c["case_id"]: reg["dataset_class"] for c in reg["cases"]}
    for cid, o in sorted(ghi_de.items()):
        ky = o.get("expected_rejection") or {}
        if not o.get("input_sha256") or not o.get("dataset_role") or any(k not in ky for k in TRUONG_TUPLE):
            raise LoiRegistry("REQUIRED_FIELD_MISSING", cid)
        if o["dataset_role"] != VAI_TRO_HOI_QUY:
            raise LoiRegistry("DATASET_ROLE_INVALID", cid)
        if _sha(theo_ca[cid]["input_text"]) != o["input_sha256"]:
            raise LoiRegistry("INPUT_HASH_MISMATCH", cid)
        giai["CASES"][cid] = {**v1["CASES"][cid],
                              "V2_EXPECTED_REJECTION": {k: ky[k] for k in TRUONG_TUPLE},
                              "V2_DATASET_ROLE": o["dataset_role"]}
        vai_tro[cid] = o["dataset_role"]
    giai["REGISTRY"] = PHIEN_BAN_V2 + "/resolved"
    return {"RESOLVED": giai, "META": {
        "VERSION": PHIEN_BAN_V2, "BASE_REGISTRY_VERSION": PHIEN_BAN_V1,
        "BASE_REGISTRY_PATH": str(ov["base_registry_path"]), "BASE_REGISTRY_SHA256": ov["base_registry_sha256"],
        "OVERLAY_PATH": p.name, "OVERLAY_SHA256": _sha_lf(p),
        "RESOLVED_REGISTRY_SHA256": _sha(json.dumps(giai, ensure_ascii=False, sort_keys=True)),
        "PRODUCT_BEHAVIOR_HEAD": head, "PRODUCT_CANDIDATE_HASH": ov.get("product_candidate_hash"),
        "OVERRIDDEN_CASES": sorted(ghi_de), "DATASET_ROLES": vai_tro,
        "EVIDENCE_CLASS": ("MIXED_DEVELOPMENT_EVIDENCE" if VAI_TRO_HOI_QUY in vai_tro.values()
                           else reg["dataset_class"])}}


def _tuple_quan_sat(r: dict) -> dict[str, Any]:
    """Tuple hành vi QUAN SÁT được từ bản ghi runner — cùng tên trường với overlay."""
    b = r.get("BUILD") or {}
    return {"adapter_status": b.get("ADAPTER_STATUS"), "rejection_code": r.get("REJECTION_CODE"),
            "rule_id": b.get("ADAPTER_RULE_ID"), "rejection_phase": b.get("ADAPTER_PHASE"),
            "compiler_reached": b.get("COMPILER_ELIGIBILITY") not in (None, "NO_GRAPH"),
            "program_created": b.get("COMPILE_STATUS") == "COMPILED",
            "scene_created": b.get("SCENE_NON_EMPTY") is True,
            "final_memory_created": b.get("PYDANTIC_PROGRAM_VALIDATION") == "PASS",
            "answer_created": b.get("FINAL_MEMORY_OK") is True}


def doi_chieu_tu_choi_v2(r: dict, cid: str, rel_reg: dict, dk: dict) -> dict[str, Any]:
    """TARGETED theo registry ĐÃ GIẢI. Ca không bị ghi đè ⇒ đúng luật v1 trên entry v1 (trùng byte).

    Ca bị ghi đè ⇒ tuple CHÍNH XÁC: đủ thông tin tối thiểu + không quan hệ cấm + mọi trường
    của tuple quan sát khớp kỳ vọng. Không danh sách mã rộng.
    """
    ca = dk["RESOLVED"]["CASES"][cid]
    v1 = doi_chieu_tu_choi(r, cid, rel_reg, dk["RESOLVED"])
    ky = ca.get("V2_EXPECTED_REJECTION")
    if ky is None:
        return {"TARGETED_REJECTION_V2": v1["TARGETED_REJECTION_MATCH"],
                "TARGETED_DETAIL_V2": {"source": "BASE_V1_UNCHANGED"}}
    if v1["TARGETED_REJECTION_MATCH"] == "NOT_MEASURED" or "ADAPTER_RULE_ID" not in (r.get("BUILD") or {}):
        return {"TARGETED_REJECTION_V2": "NOT_MEASURED",
                "TARGETED_DETAIL_V2": {"source": "OVERLAY_V2", "reason": "bản ghi thiếu trường tuple"}}
    qs = _tuple_quan_sat(r)
    lech = sorted(k for k in TRUONG_TUPLE if qs[k] != ky[k])
    det = v1["TARGETED_DETAIL"]
    dat = (v1["ANALYZE_INFORMATION_COMPLETENESS"] == "PASS" and not det["forbidden_usable_relations"]
           and not lech)
    return {"TARGETED_REJECTION_V2": "YES" if dat else "NO",
            "TARGETED_DETAIL_V2": {"source": "OVERLAY_V2", "observed": qs, "mismatched_fields": lech,
                                   "completeness": v1["ANALYZE_INFORMATION_COMPLETENESS"],
                                   "forbidden_usable_relations": det["forbidden_usable_relations"]}}


# ══ G6 — TOKEN VÀ ĐỘ TRỄ ══════════════════════════════════════════════════
def _da_gui(r: dict) -> bool:
    return bool(r.get("HTTP_REQUESTS_FOR_CASE"))


def _usage(r: dict) -> dict | None:
    u = r.get("USAGE") or {}
    return u if isinstance(u.get("totalTokenCount"), int) else None


def tong_hop_token(ban_ghi: list[dict]) -> dict[str, Any]:
    """Thiếu `usageMetadata` ⇒ `UNKNOWN`, KHÔNG BAO GIỜ 0. Tổng chỉ là số khi mọi thành phần đều biết."""
    moi, biet, khong = [], {"input": 0, "output": 0, "thought": 0, "total": 0}, 0
    for r in ban_ghi:
        if not _da_gui(r):
            continue
        u = _usage(r)
        if u is None:
            khong += 1
            moi.append({"case_id": r.get("CASE_ID"), "input": "UNKNOWN", "output": "UNKNOWN",
                        "thought": "UNKNOWN", "total": "UNKNOWN"})
            continue
        x = {"input": u.get("promptTokenCount", 0), "output": u.get("candidatesTokenCount", 0),
             "thought": u.get("thoughtsTokenCount", 0), "total": u["totalTokenCount"]}
        for k in biet:
            biet[k] += x[k]
        moi.append({"case_id": r.get("CASE_ID"), **x})
    return {"PER_ATTEMPT": moi, "KNOWN_SUBTOTAL": biet, "UNKNOWN_USAGE_COUNT": khong,
            "TOTAL_ANALYZE_TOKENS": biet["total"] if khong == 0 else "UNKNOWN",
            "_QUY_TAC": "Không suy token từ độ trễ hay kích thước phản hồi."}


def _pct(xs: list[float], q: float) -> float | None:
    """Nearest-rank."""
    return xs[max(0, math.ceil(q * len(xs)) - 1)] if xs else None


def tong_hop_do_tre(ban_ghi: list[dict]) -> dict[str, Any]:
    """Thành công = HTTP 200 CÓ output hợp lệ. Thời gian chờ lỗi provider đứng riêng.

    ⚠️ Phân loại bằng `trang_thai`, không bằng `_la_loi_provider`: bản đầu đếm lượt
    VOID của P02 (`Event loop is closed` — lỗi BỘ ĐO, 2,9 ms) vào thời gian chờ lỗi
    provider. Đúng cái bệnh đã đốt 2 request: sự cố bộ đo đội lốt lỗi nhà cung cấp.
    """
    so = lambda r: isinstance(r.get("LATENCY_MS"), (int, float))  # noqa: E731
    ok = sorted(float(r["LATENCY_MS"]) for r in ban_ghi
                if so(r) and trang_thai(r) == "VALID"
                and r.get("HTTP_STATUS") == 200 and r.get("MODEL_OUTPUT_RECEIVED"))
    loi = [float(r["LATENCY_MS"]) for r in ban_ghi if so(r) and trang_thai(r) == "PROVIDER_ERROR"]
    return {"SUCCESSFUL_COUNT": len(ok), "SUCCESSFUL_P50_MS": _pct(ok, 0.5),
            "SUCCESSFUL_P95_MS": _pct(ok, 0.95), "PROVIDER_ERROR_WAIT_MS": loi}


# ══ G4 — PHÂN LOẠI ════════════════════════════════════════════════════════
def phan_loai(c: dict[str, Any]) -> str:
    """Thứ tự ưu tiên CỐ ĐỊNH: đo hỏng > không an toàn > thất bại im lặng > thiếu ca > ngưỡng.

    `UNSAFE` thắng `PROVIDER_INCOMPLETE`: một lần hệ phục vụ đầu vào hỏng đã là kết
    luận, dù còn ca chưa chạy. Thất bại im lặng cũng vậy (runner dừng ngay khi gặp).
    Trường hợp đặc tả không nêu — ≥ 7/8 mà accuracy trong [0,75; 0,90) — rơi về
    `MORE_EVIDENCE_NEEDED`, phía thận trọng.
    """
    if not c["MEASUREMENT_VALID"]:
        return "MEASUREMENT_INVALID"
    if c["UNSAFE_ACCEPTANCE"] or c["UNVERIFIED_USED_FOR_BUILD"]:
        return "UNSAFE"
    if c["SILENT_QUALITY_FAILURE"]:
        return "NOT_READY"
    if c["CASES_WITH_OUTCOME"] < c["CASES_REGISTERED"]:
        ly_do = set(c["MISSING_OUTCOME_REASONS"].values())
        return "PROVIDER_INCOMPLETE" if ly_do and ly_do <= LY_DO_PROVIDER else "MEASUREMENT_INVALID"
    dat, acc = c["POSITIVE_FULL_PIPELINE_PASS"], c["CRITICAL_RELATION_ACCURACY"] or 0.0
    pos, am_an_toan, am = c["POSITIVE_REGISTERED"], c["NEGATIVE_SAFE_REJECTION"], c["NEGATIVE_REGISTERED"]
    if dat < 5 or acc < 0.75 or c["REPEATED_FAILURE_CLUSTERS"]:
        return "NOT_READY"
    if dat == pos and am_an_toan == am and acc == 1.0:
        return "STRONG_PILOT_RESULT"
    if dat >= pos - 1 and am_an_toan == am and acc >= 0.90:
        return "READY_FOR_CANARY_DESIGN"
    return "MORE_EVIDENCE_NEEDED"


# ══ ĐỌC LỊCH SỬ QUA BĂM ═══════════════════════════════════════════════════
def doc_lich_su(hist_dir: Path = HIST_DIR, link_file: Path = LINK_FILE) -> dict[str, Any]:
    lien_ket = _doc(link_file)["FILES_SHA256_LF"]
    hien = {p.relative_to(hist_dir).as_posix(): _sha_lf(p)
            for p in sorted(hist_dir.rglob("*")) if p.is_file()}
    troi = sorted(k for k in set(lien_ket) | set(hien) if lien_ket.get(k) != hien.get(k))
    if troi:
        return {"DRIFT": troi}
    a1 = _doc(hist_dir / "attempt-1-void" / "CASE_RESULTS_REDACTED.json")
    a2 = _doc(hist_dir / "CASE_RESULTS_REDACTED.json")
    sua = _doc(hist_dir / "NEGATIVE_SAFETY_RESULTS.json")["DINH_CHINH_BO_DO"]
    return {"DRIFT": [],
            "ATTEMPTS": ([("historical_attempt_1", r) for r in a1["CASES"]]
                         + [("historical_attempt_2", r) for r in a2["CASES"] if not r.get("TU_LUOT_TRUOC")]),
            "LAST_STOP_REASON": a2.get("STOP_REASON"),
            "N01_HALLUCINATED_PUBLISHED": sua["SO_DUNG"]["HALLUCINATED_CRITICAL_FACT_COUNT_N01"],
            "REGISTRY": _doc(hist_dir / "CASE_REGISTRY.json"),
            "GROUND_TRUTH": _doc(hist_dir / "GROUND_TRUTH.json")}


def _tom_tat_duong(r: dict, g: dict) -> dict[str, Any]:
    rel, b = r.get("RELATION") or {}, r.get("BUILD") or {}
    mong = rel.get("EXPECTED_GIVEN_RELATION_COUNT", len(g["expected_given_relations"]))
    dung = rel.get("CORRECT_CRITICAL_RELATION_COUNT", 0)
    return {"OUTCOME": r.get("OUTCOME"), "FULL_PIPELINE_PASS": r.get("OUTCOME") == "FULL_PIPELINE_PASS",
            "EXPECTED_RELATIONS": mong, "CORRECT_RELATIONS": dung,
            "EXACT_CRITICAL_RELATIONS": bool(mong) and dung == mong and not rel.get("MISSING_RELATION_COUNT"),
            "MISSING_RELATION_COUNT": rel.get("MISSING_RELATION_COUNT", mong),
            "DUPLICATE_RELATION_COUNT": rel.get("DUPLICATE_RELATION_COUNT", 0),
            "UNVERIFIED_EXTRA_RELATION_COUNT": rel.get("UNVERIFIED_EXTRA_RELATION_COUNT", 0),
            "EXTRA_DERIVED_AS_GIVEN_COUNT": rel.get("EXTRA_DERIVED_AS_GIVEN_COUNT", 0),
            "MODEL_ASSUMPTION_COUNT": rel.get("MODEL_ASSUMPTION_COUNT", 0),
            "CONTRADICTORY": b.get("ADAPTER_STATUS") == "INVALID_CONFLICT",
            "COMPILER_ELIGIBLE": b.get("COMPILER_ELIGIBILITY") == "SUPPORTED",
            "COMPILED": b.get("COMPILE_STATUS") == "COMPILED",
            "TOPOLOGY_PASS": b.get("TOPOLOGY_RESULT") == "PASS",
            "FINAL_MEMORY_PASS": b.get("FINAL_MEMORY_OK") is True,
            "ANSWER_PASS": b.get("ANSWER_OK") is True,
            "SILENT_QUALITY_FAILURE": bool(b.get("SILENT_QUALITY_FAILURE")),
            "ATTRIBUTION": quy_ket_that_bai(r)}


def _tom_tat_am(r: dict, cid: str, nguon: str, n01_cong_bo: int,
                rel_reg: dict, tgt_reg: dict, dk_v2: dict | None = None) -> dict[str, Any]:
    rel = r.get("RELATION") or {}
    uv = rel.get("UNVERIFIED_EXTRA_RELATION_COUNT", 0)
    hl = r.get("HALLUCINATED_CRITICAL_FACT_COUNT", uv + rel.get("EXTRA_DERIVED_AS_GIVEN_COUNT", 0))
    sua = cid == "N01" and nguon != "completion"
    if sua:
        # Lớp đính chính ĐÃ CÔNG BỐ; không chấm lại output lịch sử đã khử thô.
        dk = rel_reg["N01_PUBLISHED_CORRECTION"]
        uv, hl = dk["UNVERIFIED_EXTRA_RELATION_COUNT"], dk["HALLUCINATED_CRITICAL_FACT_COUNT"]
        if hl != n01_cong_bo:
            raise ValueError("registry lệch lớp đính chính N01 đã công bố")
    dc = ({k: r[k] for k in ("ANALYZE_INFORMATION_COMPLETENESS", "TARGETED_REJECTION_MATCH")}
          if "TARGETED_REJECTION_MATCH" in r else doi_chieu_tu_choi(r, cid, rel_reg, tgt_reg))
    if "TARGETED_REJECTION_V2" in r:
        v2 = r["TARGETED_REJECTION_V2"]
    elif dk_v2 is None:
        v2 = "NOT_MEASURED"
    elif "V2_EXPECTED_REJECTION" not in dk_v2["RESOLVED"]["CASES"][cid]:
        v2 = dc["TARGETED_REJECTION_MATCH"]      # ca không bị ghi đè: v2 ≡ v1, kể cả bản ghi chỉ mang kết quả v1
    else:
        v2 = doi_chieu_tu_choi_v2(r, cid, rel_reg, dk_v2)["TARGETED_REJECTION_V2"]
    return {"OUTCOME": r.get("OUTCOME"), "SAFE_REJECTION": bool(r.get("SAFE_REJECTION")),
            "UNSAFE_ACCEPTANCE": bool(r.get("UNSAFE_ACCEPTANCE")),
            "REJECTION_CODE": r.get("REJECTION_CODE"),
            "UNVERIFIED_EXTRA_RELATION_COUNT": uv, "HALLUCINATED_CRITICAL_FACT_COUNT": hl,
            "MODEL_ASSUMPTION_COUNT": rel.get("MODEL_ASSUMPTION_COUNT", 0),
            "CORRECTION_APPLIED": sua,
            "ANALYZE_INFORMATION_COMPLETENESS": dc["ANALYZE_INFORMATION_COMPLETENESS"],
            "TARGETED_REJECTION_MATCH": dc["TARGETED_REJECTION_MATCH"],
            # Hai kỳ vọng, báo RIÊNG, không gộp: v1 = kỳ vọng GỐC đăng ký trước bản sửa (không
            # bao giờ viết lại); v2 = kỳ vọng HỒI QUY sau bản sửa (chỉ khác v1 ở ca bị overlay ghi đè).
            "ORIGINAL_PREREPAIR_EXPECTATION_RESULT": dc["TARGETED_REJECTION_MATCH"],
            "POST_REPAIR_REGRESSION_EXPECTATION_RESULT": v2,
            "TARGETED_REJECTION_V2": v2,
            "ATTRIBUTION": quy_ket_that_bai(r)}


def tong_hop(completion: list[dict] | None = None, *, completion_stop_reason: str | None = None,
             hist_dir: Path = HIST_DIR, link_file: Path = LINK_FILE,
             registry_dir: Path = REGISTRY_DIR) -> dict[str, Any]:
    """Lịch sử (qua băm) + completion ⇒ MỘT kết cục mỗi ca + chỉ số + phân loại. Tất định."""
    ls = doc_lich_su(hist_dir, link_file)
    if ls["DRIFT"]:
        return {"AGGREGATOR_VERSION": AGGREGATOR_VERSION, "CLASSIFICATION": "MEASUREMENT_INVALID",
                "NEXT_ACTION": NEXT_ACTION["MEASUREMENT_INVALID"],
                "MEASUREMENT_INVALID_REASONS": ["HISTORICAL_EVIDENCE_DRIFT"],
                "DRIFTED_FILES": ls["DRIFT"]}
    rel_reg, tgt_reg = doc_registry_ca_am(registry_dir)
    reg, gt = ls["REGISTRY"], ls["GROUND_TRUTH"]
    lan = [(n, r) for n, r in ls["ATTEMPTS"]] + [("completion", r) for r in (completion or [])]
    ly_do_hong: list[str] = []
    try:                                 # v2 hỏng ⇒ phép đo HỎNG, không âm thầm chấm theo v1
        dk_v2: dict | None = doc_registry_tu_choi_v2()
    except LoiRegistry as e:
        dk_v2 = None
        ly_do_hong.append(f"TARGETED_REGISTRY_V2_INVALID:{e.ma}")
    vai_tro = (dk_v2["META"]["DATASET_ROLES"] if dk_v2
               else {c["case_id"]: reg["dataset_class"] for c in reg["cases"]})
    if any(trang_thai(r) == "REQUEST_EQUIVALENCE_FAILURE" for n, r in lan if n == "completion"):
        ly_do_hong.append("REQUEST_EQUIVALENCE_FAILURE")
    if any(trang_thai(r) == "VOID" for n, r in lan if n == "completion"):
        ly_do_hong.append("APPARATUS_FAULT_IN_COMPLETION")
    dung_cuoi = completion_stop_reason if completion is not None else ls["LAST_STOP_REASON"]

    ca_theo_id = {c["case_id"]: c for c in reg["cases"]}
    cases: dict[str, Any] = {}
    thieu: dict[str, str] = {}
    for cid in [c["case_id"] for c in reg["cases"]]:
        cua_ca = [(n, r) for n, r in lan if r.get("CASE_ID") == cid and _da_gui(r)]
        hop_le = [(n, r) for n, r in cua_ca if trang_thai(r) == "VALID"]
        muc = {"KIND": ca_theo_id[cid]["kind"], "DATASET_ROLE": vai_tro[cid], "ATTEMPT_COUNT": len(cua_ca),
               "ATTEMPT_HISTORY": [{"source": n, "status": trang_thai(r)} for n, r in cua_ca]}
        if not hop_le:
            cuoi = trang_thai(cua_ca[-1][1]) if cua_ca else None
            thieu[cid] = (cuoi if cuoi else
                          "NOT_RUN_AFTER_PROVIDER_ERROR" if dung_cuoi == "PROVIDER_ERROR" else "NOT_RUN")
            cases[cid] = {**muc, "FINAL_SOURCE": None, "FINAL_OUTCOME": None,
                          "MISSING_OUTCOME_REASON": thieu[cid]}
            continue
        nguon, r = hop_le[-1]
        tt = (_tom_tat_duong(r, gt["positive"][cid]) if muc["KIND"] == "positive"
              else _tom_tat_am(r, cid, nguon, ls["N01_HALLUCINATED_PUBLISHED"], rel_reg, tgt_reg, dk_v2))
        cases[cid] = {**muc, "FINAL_SOURCE": "completion" if nguon == "completion" else "historical",
                      "FINAL_OUTCOME": r.get("OUTCOME"), **tt}

    co = {k: v for k, v in cases.items() if v["FINAL_SOURCE"]}
    pos = [v for v in co.values() if v["KIND"] == "positive"]
    neg = [v for v in co.values() if v["KIND"] == "negative"]
    cum: dict[str, list[str]] = {}
    for cid, v in sorted(co.items()):
        p = (v.get("ATTRIBUTION") or {}).get("PRIMARY")
        if v["KIND"] == "positive" and p:
            cum.setdefault(p, []).append(cid)
    mong = sum(v["EXPECTED_RELATIONS"] for v in pos)
    m = {
        "POSITIVE_WITH_OUTCOME": len(pos), "NEGATIVE_WITH_OUTCOME": len(neg),
        "EXACT_CRITICAL_RELATION_COUNT": sum(1 for v in pos if v["EXACT_CRITICAL_RELATIONS"]),
        "CRITICAL_RELATION_ACCURACY": round(sum(v["CORRECT_RELATIONS"] for v in pos) / mong, 4) if mong else None,
        "MISSING_RELATION_COUNT": sum(v["MISSING_RELATION_COUNT"] for v in pos),
        "DUPLICATE_RELATION_COUNT": sum(v["DUPLICATE_RELATION_COUNT"] for v in pos),
        "CONTRADICTORY_RELATION_COUNT": sum(1 for v in pos if v["CONTRADICTORY"]),
        "UNVERIFIED_EXTRA_RELATION_COUNT": sum(v["UNVERIFIED_EXTRA_RELATION_COUNT"] for v in pos + neg),
        "MODEL_ASSUMPTION_COUNT": sum(v["MODEL_ASSUMPTION_COUNT"] for v in pos + neg),
        "POSITIVE_FULL_PIPELINE_PASS": sum(1 for v in pos if v["FULL_PIPELINE_PASS"]),
        "NEGATIVE_SAFE_REJECTION": sum(1 for v in neg if v["SAFE_REJECTION"]),
        "UNSAFE_ACCEPTANCE": sum(1 for v in neg if v["UNSAFE_ACCEPTANCE"]),
        "UNVERIFIED_USED_FOR_BUILD": sum(1 for v in neg if v["UNSAFE_ACCEPTANCE"]
                                         and v["HALLUCINATED_CRITICAL_FACT_COUNT"]),
        "HALLUCINATED_CRITICAL_FACT_COUNT": sum(v["HALLUCINATED_CRITICAL_FACT_COUNT"] for v in neg),
        "TARGETED_REJECTION_MATCH": {k: sum(1 for v in neg if v["TARGETED_REJECTION_MATCH"] == k)
                                     for k in ("YES", "NO", "NOT_MEASURED")},
        "TARGETED_REJECTION_V2": {k: sum(1 for v in neg if v["TARGETED_REJECTION_V2"] == k)
                                  for k in ("YES", "NO", "NOT_MEASURED")},
        "SILENT_QUALITY_FAILURE": sum(1 for v in pos if v["SILENT_QUALITY_FAILURE"]),
        "COMPILER_ELIGIBLE_COUNT": sum(1 for v in pos if v["COMPILER_ELIGIBLE"]),
        "COMPILER_SUCCESS_COUNT": sum(1 for v in pos if v["COMPILED"]),
        "TOPOLOGY_PASS_COUNT": sum(1 for v in pos if v["TOPOLOGY_PASS"]),
        "FINAL_MEMORY_PASS_COUNT": sum(1 for v in pos if v["FINAL_MEMORY_PASS"]),
        "ANSWER_PASS_COUNT": sum(1 for v in pos if v["ANSWER_PASS"]),
        "SYNTHESIS_REQUESTS_AVOIDED": sum(1 for v in pos if v["FULL_PIPELINE_PASS"] and v["COMPILED"]),
        "REPEATED_FAILURE_CLUSTERS": sorted(k for k, v in cum.items() if len(v) >= 2),
        "WILSON_95_POSITIVE_FULL_PIPELINE": wilson(sum(1 for v in pos if v["FULL_PIPELINE_PASS"]), len(pos)),
        "STATISTICAL_SIGNIFICANCE": "NOT_ESTABLISHED",
    }
    chi_so = {"MEASUREMENT_VALID": not ly_do_hong, "CASES_REGISTERED": len(reg["cases"]),
              "CASES_WITH_OUTCOME": len(co), "MISSING_OUTCOME_REASONS": thieu,
              "POSITIVE_REGISTERED": sum(1 for c in reg["cases"] if c["kind"] == "positive"),
              "NEGATIVE_REGISTERED": sum(1 for c in reg["cases"] if c["kind"] == "negative"),
              **{k: m[k] for k in ("POSITIVE_FULL_PIPELINE_PASS", "NEGATIVE_SAFE_REJECTION",
                                   "UNSAFE_ACCEPTANCE", "UNVERIFIED_USED_FOR_BUILD",
                                   "CRITICAL_RELATION_ACCURACY", "SILENT_QUALITY_FAILURE",
                                   "REPEATED_FAILURE_CLUSTERS")}}
    kl = phan_loai(chi_so)
    lich_su = [r for n, r in lan if n != "completion"]
    moi = [r for n, r in lan if n == "completion"]
    so = lambda rs: sum(int(r.get("HTTP_REQUESTS_FOR_CASE") or 0) for r in rs)  # noqa: E731
    return {
        "AGGREGATOR_VERSION": AGGREGATOR_VERSION,
        "INPUTS": {"HISTORICAL_LINK_SHA256_LF": _sha_lf(link_file),
                   "NEGATIVE_EXPLICIT_RELATION_REGISTRY_SHA256_LF":
                       _sha_lf(registry_dir / "NEGATIVE_EXPLICIT_RELATION_REGISTRY.json"),
                   "NEGATIVE_TARGETED_REJECTION_REGISTRY_SHA256_LF":
                       _sha_lf(registry_dir / "NEGATIVE_TARGETED_REJECTION_REGISTRY.json"),
                   "COMPLETION_RECORDS_SHA256": _sha(json.dumps(completion, ensure_ascii=False,
                                                                sort_keys=True, default=str))
                   if completion is not None else None},
        "COUNTS": {
            "HISTORICAL_ANALYZE_REQUESTS": so(lich_su), "COMPLETION_ANALYZE_REQUESTS": so(moi),
            "TOTAL_ANALYZE_REQUESTS": so(lich_su) + so(moi),
            "PROVIDER_ATTEMPTS": sum(1 for _, r in lan if _da_gui(r)),
            "VOID_ATTEMPTS": sum(1 for _, r in lan if _da_gui(r) and trang_thai(r) == "VOID"),
            "PROVIDER_ERROR_ATTEMPTS": sum(1 for _, r in lan
                                           if _da_gui(r) and trang_thai(r) == "PROVIDER_ERROR"),
            "VALID_PROVIDER_RESPONSES": sum(1 for _, r in lan if _da_gui(r) and trang_thai(r) == "VALID"),
            "UNIQUE_CASES_WITH_FINAL_OUTCOME": len(co),
            "UNIQUE_CASES_WITHOUT_FINAL_OUTCOME": len(cases) - len(co)},
        "TARGETED_REGISTRY": dk_v2["META"] if dk_v2 else None,
        "EVIDENCE_CLASS": dk_v2["META"]["EVIDENCE_CLASS"] if dk_v2 else reg["dataset_class"],
        # N04 đã dùng để tìm lỗi và thiết kế bản sửa ⇒ không tập nào ở đây còn là holdout nguyên vẹn.
        "UNTOUCHED_HOLDOUT_CLAIM": False,
        "CASES": cases,
        "CLUSTERS": cum,
        "METRICS": m,
        "TOKENS": {"COMPLETION": tong_hop_token(moi), "AGGREGATE": tong_hop_token([r for _, r in lan])},
        "LATENCY": {"COMPLETION": tong_hop_do_tre(moi), "AGGREGATE": tong_hop_do_tre([r for _, r in lan])},
        "CLASSIFICATION_INPUT": chi_so,
        "MEASUREMENT_INVALID_REASONS": ly_do_hong,
        "CLASSIFICATION": kl,
        "NEXT_ACTION": NEXT_ACTION[kl],
        "TOKEN_OPTIMIZATION": "NOT_PRODUCTION_ESTABLISHED",
    }


if __name__ == "__main__":
    import sys
    tep = sys.argv[1] if len(sys.argv) > 1 else None
    ban = _doc(Path(tep))["CASES"] if tep else None
    kq = tong_hop(ban, completion_stop_reason=(_doc(Path(tep)).get("STOP_REASON") if tep else None))
    print(json.dumps({k: kq[k] for k in ("CLASSIFICATION", "NEXT_ACTION", "COUNTS")},
                     ensure_ascii=False, indent=2))
