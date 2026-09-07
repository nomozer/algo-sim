# -*- coding: utf-8 -*-
"""§4 + §5 + §8 — tiền kiểm GOLD, tiền kiểm BỘ CHẤM, và đăng ký lượt đo.

`APPLICATION_LLM_CALLS = 0`. File này là **CỔNG**: `main()` thoát khác 0 nếu
một trong hai tiền kiểm chưa đạt, nên không ai rút được ca khi bộ đo còn đỏ.

Cùng khuôn với `register_oblique_ellipse_final_rerun.py`; khác ở sáu phản ví
dụ, vì wave này đo **bảng mặt** chứ không đo phép chọn toán tử.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.ai import gemini as G  # noqa: E402
from app.ai.pipeline import _dung_scene3d  # noqa: E402
from app.main import CACHE_VERSION  # noqa: E402
from app.runtime_identity import (  # noqa: E402
    semantic_environment_fingerprint, semantic_environment_hash,
)
from app.simulation.geometry.radical import display, is_exact_number  # noqa: E402
from app.simulation.product_capability import NANG_LUC_SAN_PHAM  # noqa: E402
from app.simulation.semantic_program.contract import (  # noqa: E402
    SemanticProgramSpec,
)
from app.simulation.semantic_program.grammar_card import grammar_card  # noqa: E402
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

from gold_nonconvex_polyhedron import (  # noqa: E402
    CASE_ID, CONTAINER, CONTRACT_GOLD_HASH, DINH, DINH_DAY, GOLD, GOLD_HASH,
    ORACLE, ORACLE_HASH, PROBLEM_HASH, PROBLEM_TEXT, REQUEST_CONTRACT_GOLD,
    WITNESS,
)
from score_nonconvex_polyhedron import cham_synthesis  # noqa: E402

RUN_ID_PREFIX = "nonconvex-polyhedron-model-discoverability"
RA = BACKEND.parent / "docs" / "evaluation" / "geometry" / RUN_ID_PREFIX
DAP_SO = "45"


def _h(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _hf(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _hd() -> RequestContract:
    return RequestContract.model_validate(REQUEST_CONTRACT_GOLD)


def _chay(p: dict):
    return verify_and_compile(_hd(), SemanticProgramSpec.model_validate(p))


def _dap_so(kq):
    return {k: display(x) for k, x in (kq.final_memory or {}).items()
            if is_exact_number(x)}.get(WITNESS)


def _canh(p: dict) -> dict:
    return _dung_scene3d(SemanticProgramSpec.model_validate(p), _hd()) or {}


def _voi_mat(mat) -> dict:
    """Gold, thay đúng bảng mặt. Mọi thứ khác giữ nguyên."""
    g = copy.deepcopy(GOLD)
    for s in g["statements"]:
        if s.get("kind") == "construct_solid":
            s["faces"] = mat
    return g


#: Chu trình đáy → bảng mặt chóp đầy đủ (đáy + 5 mặt bên khớp chu trình ấy).
def _chop(chu: list[str]) -> list[list[str]]:
    return [list(reversed(chu))] + [
        [chu[i], chu[(i + 1) % 5], "S"] for i in range(5)]


# ── SÁU PHẢN VÍ DỤ, §4 ───────────────────────────────────────────────────
#
# ① Đáy khai bằng QUẠT TAM GIÁC. Biên vẫn KÍN (mỗi cạnh chéo `A-C`, `A-D`
#    thuộc đúng hai tam giác đáy), và tổng CÓ DẤU vẫn cho 45 — đó là toàn bộ
#    điểm của công thức có dấu. Nhưng ba tam giác ấy là thứ renderer sẽ VẼ, và
#    `A-C-D` nằm ngoài đáy ⇒ phần lõm bị lấp. Ô này phải đỏ ở **bảng mặt và
#    Scene3D**, KHÔNG đỏ ở thể tích — và nó tồn tại để chứng minh bộ chấm
#    phân biệt được ba chiều ấy thay vì gộp làm một.
MAT_QUAT = ([["A", "B", "C"], ["A", "C", "D"], ["A", "D", "E"]]
            + [[DINH_DAY[i], DINH_DAY[(i + 1) % 5], "S"] for i in range(5)])
# ② Thiếu một mặt bên.
MAT_THIEU = _chop(DINH_DAY)[:-1]
# ③ Chu trình đáy khác ⇒ HÌNH khác ⇒ đáp số khác (đo được: 12·9/3 = 36).
MAT_DOI_HINH = _chop(["A", "B", "D", "C", "E"])
# ④ Đáy TỰ CẮT — `A-C` cắt `D-E`.
MAT_TU_CAT = _chop(["A", "C", "B", "D", "E"])
# ⑥ Khối LỒI control: bỏ đỉnh lõm, chóp tứ giác `A B C E`.
#
# ⚠️ Nó cần HỢP ĐỒNG RIÊNG, và lý do đáng ghi: cổng phủ nối nghĩa vụ với vật
# qua **nhãn** (`label`), nên `container = "S.ABCDE"` của đề gốc không bind
# nổi một khối nhãn `S.ABCE`. Đo được: `structural_coverage` ·
# `requested_operation_uncovered` · `THIEU_KHAI_BAO`. Dùng chung hợp đồng ở
# đây sẽ làm ô ⑥ đỏ vì một lý do **chẳng liên quan** tới điều nó bảo vệ.
CT_LOI = {
    "problem_text": "Control: chóp đáy tứ giác lồi ABCE.",
    "input_facts": [f for f in REQUEST_CONTRACT_GOLD["input_facts"]
                    if f["fact_id"] != "dinh_D"],
    "obligations": [{"kind": "volume", "container": "S.ABCE",
                     "params": {"witness": WITNESS}}],
}
LOI = {
    "spec_version": "1.0", "title": "Chóp đáy tứ giác LỒI (control)",
    "memory_declarations": [d for d in GOLD["memory_declarations"]
                            if d.get("name") != "D"],
    "statements": [
        {"kind": "construct_solid", "target_var": "chop",
         "vertices": ["A", "B", "C", "E", "S"],
         "faces": [["E", "C", "B", "A"], ["A", "B", "S"], ["B", "C", "S"],
                   ["C", "E", "S"], ["E", "A", "S"]], "label": "S.ABCE"},
        {"kind": "assign", "target_var": WITNESS,
         "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}},
    ],
}


def _duong_tat() -> dict:
    """⑤ Bảng mặt HỢP LỆ nhưng đáp số khai thẳng, không đo."""
    g = copy.deepcopy(GOLD)
    g["statements"] = [s for s in g["statements"]
                       if s.get("kind") == "construct_solid"]
    g["statements"].append({
        "kind": "assign", "target_var": WITNESS,
        "expr": {"kind": "literal", "value": 45}})
    return g


def _lom_con_nguyen(canh: dict) -> bool:
    """Đáy trong cảnh có còn là MỘT ngũ giác lõm không.

    Đây là `SCENE3D_CONCAVITY_PRESERVED`, và nó phải đo trên **cảnh đã dựng**,
    không đo trên chương trình: chương trình đúng mà cảnh làm phẳng chỗ lõm thì
    thứ học sinh nhìn thấy vẫn sai.
    """
    from fractions import Fraction as F

    khoi = next((o for o in canh.get("objects", [])
                 if o.get("render") == "mesh" and o.get("faces")), None)
    if not khoi:
        return False
    day = [f for f in khoi["faces"] if len(f) == 5]
    if len(day) != 1:
        return False
    xy = [(F(khoi["vertices"][j][0]), F(khoi["vertices"][j][1]))
          for j in day[0]]
    cheo = []
    for i in range(5):
        p, q, r = xy[i], xy[(i + 1) % 5], xy[(i + 2) % 5]
        cheo.append((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]))
    # Đúng MỘT đỉnh phản xạ, không đỉnh nào thẳng hàng.
    return 0 not in cheo and min(sum(1 for c in cheo if c > 0),
                                 sum(1 for c in cheo if c < 0)) == 1


def tien_kiem_gold() -> dict:
    """§4 — gold đi trọn đường + sáu phản ví dụ."""
    kq = _chay(GOLD)
    canh = _canh(GOLD)
    su_kien = canh.get("events", [])

    pv: dict[str, str] = {}

    # ① quạt lấp lõm: thể tích VẪN đúng, bảng mặt và Scene3D SAI.
    k1 = _chay(_voi_mat(MAT_QUAT))
    c1 = cham_synthesis(_voi_mat(MAT_QUAT))
    pv["①_quat_lap_lom__the_tich_dung_nhung_HINH_sai"] = (
        "PASS" if (k1.servable and _dap_so(k1) == DAP_SO
                   and c1["FACE_TABLE_VALID"] == "FAIL"
                   and not _lom_con_nguyen(_canh(_voi_mat(MAT_QUAT))))
        else "FAIL")

    # ② thiếu một mặt bên ⇒ biên hở.
    k2 = _chay(_voi_mat(MAT_THIEU))
    pv["②_thieu_mat_ben__BOUNDARY_OPEN"] = (
        "PASS" if (not k2.servable
                   and any("POLYHEDRON_BOUNDARY_OPEN" in d for d in k2.details))
        else "FAIL")

    # ③ chu trình đáy khác ⇒ hình khác ⇒ đáp số khác.
    k3 = _chay(_voi_mat(MAT_DOI_HINH))
    pv["③_doi_chu_trinh_day__DAP_SO_KHAC"] = (
        "PASS" if (k3.servable and _dap_so(k3) not in (None, DAP_SO))
        else "FAIL")

    # ④ mặt tự cắt.
    k4 = _chay(_voi_mat(MAT_TU_CAT))
    pv["④_mat_tu_cat__FACE_NOT_SIMPLE"] = (
        "PASS" if (not k4.servable
                   and any("POLYHEDRON_FACE_NOT_SIMPLE" in d for d in k4.details))
        else "FAIL")

    # ⑤ bảng mặt hợp lệ nhưng khai thẳng đáp số.
    dt = _duong_tat()
    k5 = _chay(dt)
    c5 = cham_synthesis(dt)
    pv["⑤_khai_thang_dap_so__bo_cham_BAT_duoc"] = (
        "PASS" if (c5["KHONG_DUONG_TAT"] is False
                   and c5["SYNTHESIS_STRUCTURE_CORRECT"] == "FAIL")
        else "FAIL")

    # ⑥ control LỒI vẫn chạy đúng — phép soát mặt của wave trước không được
    #    rộng tay, và đường khối đa diện không hỏng cho hình lồi.
    k6 = verify_and_compile(RequestContract.model_validate(CT_LOI),
                            SemanticProgramSpec.model_validate(LOI))
    pv["⑥_control_LOI_van_chay"] = (
        "PASS" if (k6.servable and _dap_so(k6) == "72") else "FAIL")

    cg = cham_synthesis(GOLD)
    ra = {
        "scope": "PASS",
        "servable": kq.servable,
        "stage_reached": kq.stage_reached,
        "error_code": kq.error_code,
        "EXACT_VOLUME": _dap_so(kq),
        "weak_kinds": list(kq.weak_kinds),
        "CHECKER_THAT_SU_CHAY": "volume" not in kq.weak_kinds,
        "postconditions": "PASS" if kq.servable else "FAIL",
        "trace": ("PASS" if any(e.get("object") == "chop" for e in su_kien)
                  and any(DAP_SO in str(e.get("explanation")) for e in su_kien)
                  else "FAIL"),
        "Scene3D": "PASS" if _lom_con_nguyen(canh) else "FAIL",
        "SCENE3D_CONCAVITY_PRESERVED": _lom_con_nguyen(canh),
        "so_vat": len(canh.get("objects", [])),
        "so_su_kien": len(su_kien),
        "FACE_TABLE_VALID_tren_gold": cg["FACE_TABLE_VALID"],
        "phan_vi_du": pv,
        "phan_vi_du_do_duoc": {
            "①_dap_so_quat": _dap_so(k1),
            "②_error": k2.error_code,
            "③_dap_so_doi_hinh": _dap_so(k3),
            "④_error": k4.error_code,
            "⑥_dap_so_loi": _dap_so(k6),
        },
    }
    ra["GOLD_PREFLIGHT"] = (
        "PASS" if all(v == "PASS" for v in pv.values())
        and kq.servable and ra["EXACT_VOLUME"] == DAP_SO
        and ra["CHECKER_THAT_SU_CHAY"]
        and ra["trace"] == ra["Scene3D"] == "PASS"
        and ra["FACE_TABLE_VALID_tren_gold"] == "PASS" else "FAIL")
    return ra


def tien_kiem_scorer() -> dict:
    """§5 — bộ chấm chạy trên fixture tổng hợp, TRƯỚC provider."""
    g = cham_synthesis(GOLD)
    quat = cham_synthesis(_voi_mat(MAT_QUAT))
    thieu = cham_synthesis(_voi_mat(MAT_THIEU))
    tu_cat = cham_synthesis(_voi_mat(MAT_TU_CAT))
    tat = cham_synthesis(_duong_tat())
    loi = cham_synthesis(LOI)

    # Bảng mặt viết bằng CHỈ SỐ thay vì tên — cùng khối, phải cùng phán quyết.
    chi_so = copy.deepcopy(GOLD)
    idx = {t: i for i, t in enumerate(DINH)}
    for s in chi_so["statements"]:
        if s.get("kind") == "construct_solid":
            s["faces"] = [[idx[x] for x in m] for m in s["faces"]]
    cs = cham_synthesis(chi_so)

    # Tên biến KHÁC đề — cùng toạ độ, phải cùng phán quyết.
    doi_ten = copy.deepcopy(GOLD)
    m = {"A": "P", "B": "Q", "C": "R", "D": "T", "E": "U", "S": "X"}
    for d in doi_ten["memory_declarations"]:
        if d["name"] in m:
            d["name"] = m[d["name"]]
    for s in doi_ten["statements"]:
        if s.get("kind") == "construct_solid":
            s["vertices"] = [m[x] for x in s["vertices"]]
            s["faces"] = [[m[x] for x in f] for f in s["faces"]]
    dt_ = cham_synthesis(doi_ten)

    # Đảo chiều MỌI mặt — cùng khối, phải cùng phán quyết.
    dao = _voi_mat([list(reversed(f)) for f in
                    next(s for s in GOLD["statements"]
                         if s["kind"] == "construct_solid")["faces"]])
    dao_ = cham_synthesis(dao)

    ra = {
        "① gold": {"FACE_TABLE_VALID": g["FACE_TABLE_VALID"],
                   "SYNTHESIS_STRUCTURE_CORRECT": g["SYNTHESIS_STRUCTURE_CORRECT"],
                   "TEN_TRUNG_DE": g["TEN_TRUNG_DE"]},
        "② quạt lấp lõm": {"FACE_TABLE_VALID": quat["FACE_TABLE_VALID"],
                            "CO_DUNG_MOT_MAT_DAY": quat["CO_DUNG_MOT_MAT_DAY"]},
        "③ thiếu mặt bên": {"FACE_TABLE_VALID": thieu["FACE_TABLE_VALID"],
                             "BIEN_KIN": thieu["BIEN_KIN"],
                             "CANH_LECH": thieu["CANH_LECH"]},
        "④ mặt tự cắt": {"FACE_TABLE_VALID": tu_cat["FACE_TABLE_VALID"],
                          "CHU_TRINH_DAY_DUNG": tu_cat["CHU_TRINH_DAY_DUNG"]},
        "⑤ khai thẳng đáp số": {
            "KHONG_DUONG_TAT": tat["KHONG_DUONG_TAT"],
            "USES_MEASURE_VOLUME": tat["USES_MEASURE_VOLUME"],
            "SYNTHESIS_STRUCTURE_CORRECT": tat["SYNTHESIS_STRUCTURE_CORRECT"]},
        "⑥ control lồi": {"FACE_TABLE_VALID": loi["FACE_TABLE_VALID"]},
        "⑦ bảng mặt bằng CHỈ SỐ": {
            "FACE_TABLE_VALID": cs["FACE_TABLE_VALID"]},
        "⑧ tên biến KHÁC đề": {
            "FACE_TABLE_VALID": dt_["FACE_TABLE_VALID"],
            "TEN_TRUNG_DE": dt_["TEN_TRUNG_DE"],
            "CO_DU_SAU_DINH": dt_["CO_DU_SAU_DINH"]},
        "⑨ đảo chiều MỌI mặt": {
            "FACE_TABLE_VALID": dao_["FACE_TABLE_VALID"]},
    }
    ra["SCORER_ACCEPTS_GOLD"] = (
        "YES" if g["FACE_TABLE_VALID"] == "PASS"
        and g["SYNTHESIS_STRUCTURE_CORRECT"] == "PASS" else "NO")
    # Điều QUAN TRỌNG NHẤT của tiền kiểm này: bộ chấm không ghim chính tả.
    ra["SCORER_INVARIANT_TO_NOTATION"] = (
        "YES" if (cs["FACE_TABLE_VALID"] == "PASS"
                  and dt_["FACE_TABLE_VALID"] == "PASS"
                  and dt_["TEN_TRUNG_DE"] is False
                  and dt_["CO_DU_SAU_DINH"] is True
                  and dao_["FACE_TABLE_VALID"] == "PASS") else "NO")
    ra["SCORER_REJECTS_WRONG_TABLE"] = (
        "YES" if all(x["FACE_TABLE_VALID"] == "FAIL"
                     for x in (quat, thieu, tu_cat)) else "NO")
    ra["SCORER_CATCHES_SHORTCUT"] = (
        "YES" if tat["KHONG_DUONG_TAT"] is False else "NO")
    # ⚠️ Bộ chấm này CỐ Ý bám một ca: nó biết đáy phải là ngũ giác `ABCDE`.
    # Nên chóp LỒI `S.ABCE` bị nó gọi `FAIL`, và điều đó ĐÚNG — nó không phải
    # bài đang đo. Ghi ra để không ai đọc nhầm thành "hệ từ chối khối lồi";
    # câu ấy do phản ví dụ ⑥ của tiền kiểm GOLD trả lời (`V = 72`, `served`).
    ra["SCORER_LA_RIENG_MOT_CA"] = (
        "YES" if loi["FACE_TABLE_VALID"] == "FAIL" else "NO")
    ra["SCORER_PREFLIGHT"] = (
        "PASS" if (ra["SCORER_ACCEPTS_GOLD"] == "YES"
                   and ra["SCORER_INVARIANT_TO_NOTATION"] == "YES"
                   and ra["SCORER_REJECTS_WRONG_TABLE"] == "YES"
                   and ra["SCORER_CATCHES_SHORTCUT"] == "YES") else "FAIL")
    return ra


def dang_ky() -> dict:
    the = grammar_card("hinh_hoc")
    fp = semantic_environment_fingerprint()
    import subprocess
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              cwd=BACKEND.parent, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:                                             # noqa: BLE001
        head = "unknown"
    return {
        "wave": "NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY",
        "dang_ky_luc": datetime.now(timezone.utc).isoformat(),
        "RUN_CLASS": "DEVELOPMENT_DISCOVERABILITY_PROBE",
        "measurement_class": "DEVELOPMENT_DIAGNOSTIC",
        "held_out_claim": False,
        "evaluator_independence": "OPERATOR_WAIVED",
        "cau_hoi": (
            "Voi mot de khoi chop day LOM hoan toan moi, mo hinh co tu phan "
            "tich de, khai cac dinh, viet BANG MAT kin bang `construct_solid`, "
            "tinh dung the tich va sinh Scene3D giu nguyen phan lom khong?"),
        "pham_vi_ket_luan": {
            "loai": "DEVELOPMENT_DIAGNOSTIC",
            "khai": ("De MOI, chua tung dung trong phat trien. Mot ca KHONG "
                     "noi duoc gi ve on dinh; ket qua chi dong o muc "
                     "development confirmation."),
            "STABILITY_UNDER_ACCEPTANCE": "NOT_MEASURED",
            "NONCONVEX_POLYHEDRON": "foundation_only",
            "PRODUCT_PROMOTION_ELIGIBLE": "NO",
        },
        "cases": 1,
        "gold_module": "gold_nonconvex_polyhedron",
        "scorer_module": "score_nonconvex_polyhedron",
        "run_id_prefix": RUN_ID_PREFIX,
        "ca": {"case_id": CASE_ID, "container": CONTAINER, "witness": WITNESS,
               "problem_sha256": PROBLEM_HASH, "problem_text": PROBLEM_TEXT,
               "oracle_sha256": ORACLE_HASH, "oracle": ORACLE},
        "ngan_sach": {
            "ANALYZE_CALL_BUDGET": 1,
            "INITIAL_SYNTHESIS_CALL_BUDGET": 1,
            "REPAIR_CALL_BUDGET": 1,
            "logical_application_call_limit": 3,
            "OBSERVED_TOKEN_CEILING": 25000,
            "token_reservation_per_call": 8000,
            "token_ceiling_observed": 25000,
            "transport_retry_limit": G.MAX_ATTEMPTS,
            "transport_retry_nguon": "gemini.MAX_ATTEMPTS (gia tri san pham)",
            "cuong_che": ("ApiBudget(max_logical_calls=3) — chan o BIEN THAT "
                          "cua `call_gemini`. San pham cho 3 luot sua; tran "
                          "logic 3 khien luot sua THU HAI khong bao gio ton "
                          "tai, dung theo §5 cua brief."),
        },
        "tieu_chi_thanh_cong": {
            "SUCCESS": ("served + V = 45 + FACE_TABLE_VALID + weak_kinds rong "
                        "+ postconditions + trace + Scene3D giu phan lom"),
            "FIRST_ATTEMPT_DISCOVERABLE": "attempt 0 dat TOAN BO SUCCESS",
            "REPAIR_ASSISTED_DISCOVERABLE": "dat SUCCESS sau dung mot repair",
        },
        "bay_da_biet": {
            "quat_lap_lom": "V van 45 nhung HINH sai — 63 neu do bang quat",
            "bao_loi": "bo han dinh D ⇒ V = 72",
            "doi_chu_trinh_day": "hinh khac ⇒ dap so khac",
        },
        "danh_tinh_he_duoc_do": {
            "HEAD": head,
            "cache_version": CACHE_VERSION,
            "NONCONVEX_POLYHEDRON_CAPABILITY":
                NANG_LUC_SAN_PHAM["nonconvex_polyhedron"].trang_thai,
            "card_C_sha256": _h(the),
            "card_C_bytes": len(the.encode("utf-8")),
            "card_day_du_sha256": _h(grammar_card()),
            "model_facing": {k: fp[k] for k in sorted(fp)
                             if isinstance(fp[k], str) and len(fp[k]) == 64},
            "semantic_environment_hash": semantic_environment_hash(),
        },
        "hash_bo_do": {
            "contract_gold_sha256": CONTRACT_GOLD_HASH,
            "gold_sha256": GOLD_HASH,
            "gold_module_sha256": _hf(
                BACKEND / "scripts" / "gold_nonconvex_polyhedron.py"),
            "scorer_module_sha256": _hf(
                BACKEND / "scripts" / "score_nonconvex_polyhedron.py"),
            "runner_sha256": _hf(
                BACKEND / "scripts" / "run_curved_end_to_end.py"),
            "register_sha256": _hf(Path(__file__)),
        },
        "model": {
            "provider": "google-generativelanguage-v1beta",
            "name": G.MODEL, "version_or_snapshot": "",
            "reproducibility": "LIMITED — alias, khong phai snapshot",
            "product_repair_limit_unchanged": 3,
        },
        "muc_giu_nguyen": {
            "PRODUCT_CODE_CHANGED": "NO",
            "PRODUCT_CAPABILITY_CHANGED": "NO",
            "model_facing_contract": "KHONG doi trong luot do",
        },
    }


def main() -> int:
    gold, scorer = tien_kiem_gold(), tien_kiem_scorer()
    dk = dang_ky()
    dk["GOLD_PREFLIGHT"] = gold["GOLD_PREFLIGHT"]
    dk["SCORER_PREFLIGHT"] = scorer["SCORER_PREFLIGHT"]
    dk["registration_sha256"] = _h(
        json.dumps(dk, ensure_ascii=False, sort_keys=True))

    RA.mkdir(parents=True, exist_ok=True)
    for ten, o in (("registration.json", dk), ("PREFLIGHT_GOLD.json", gold),
                   ("PREFLIGHT_SCORER.json", scorer)):
        p = RA / ten
        if p.exists():
            print(f"⚠️  {ten} da ton tai — KHONG ghi de artifact luot cu.")
            continue
        p.write_text(json.dumps(o, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        print("→", p)

    print(json.dumps(gold, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in scorer.items() if k.isupper()},
                     ensure_ascii=False, indent=1))
    if gold["GOLD_PREFLIGHT"] != "PASS" or scorer["SCORER_PREFLIGHT"] != "PASS":
        print("\n⛔ TIEN KIEM CHUA DAT — KHONG duoc goi provider.")
        return 1
    print("\n✅ CA HAI TIEN KIEM DAT — provider duoc phep goi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
