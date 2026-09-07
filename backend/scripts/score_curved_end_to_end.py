# -*- coding: utf-8 -*-
"""Chấm lại artifact `CURVED_END_TO_END_FRESH_CONFIRMATION`. **0 lượt gọi.**

    cd backend && .venv/Scripts/python.exe scripts/score_curved_end_to_end.py

Artifact lượt chạy **giữ nguyên từng byte**; kết quả chấm ghi ra `SCORING.json`
bên cạnh — đúng lệ repo (đính chính là artifact riêng, không đè lên bản gốc).

⚠️ **Đính chính bộ chấm, khai trước khi dùng số.** Bản chấm inline của lượt
chạy đầu ghi `ANALYZE_CONTRACT_CORRECT = FAIL` trong khi runner **chưa hề giữ**
raw của tầng `analyze` — tức chấm trượt một tầng nó không quan sát được. Cùng
họ với lỗi mà `PROVENANCE_AFFORDANCE_AB_4_LUOT §6` đã đính chính một lần
(`GROUNDING = PASS` cho tầng chưa chạy). Bộ chấm này phân biệt ba giá trị:

    PASS / FAIL      khi CÓ dữ liệu để phán
    NOT_CAPTURED     khi bộ đo không giữ lại thứ cần để phán
    NOT_REACHED      khi tầng ấy chưa từng chạy

Runner đã được sửa để giữ raw analyze (`test_C5`), nên lượt sau chấm được đủ.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_curved_end_to_end as R  # noqa: E402
from gold_curved_end_to_end import CASE_ID, ORACLE, RA  # noqa: E402

NR = "NOT_REACHED"


def _dap_so(final_memory_str: str) -> dict[str, str]:
    """Đọc đại lượng hữu tỉ từ repr của `final_memory`.

    Cố ý đọc `Fraction(a, b)` chứ không đọc chuỗi đã format: bộ đo không được
    so bằng một con số đã làm tròn ở đâu đó trên đường đi.
    """
    ra = {}
    for m in re.finditer(r"'([A-Za-z_0-9]+)': Fraction\((-?\d+), (\d+)\)",
                         final_memory_str or ""):
        ten, tu, mau = m.group(1), m.group(2), m.group(3)
        ra[ten] = tu if mau == "1" else f"{tu}/{mau}"
    return ra


def main() -> int:
    arts = sorted(RA.glob("e2e_*.json"))
    if not arts:
        print("Không tìm thấy artifact lượt chạy.")
        return 2
    art = arts[-1]
    raw = art.read_bytes()
    d = json.loads(raw.decode("utf-8"))

    mf = d["manifest"]
    cham_cu = d.get("cham") or {}
    ct = d.get("request_contract")
    nguon = d.get("nguon_hop_dong") or "SU_KIEN_DEM"
    sk_hd = [e for e in d["su_kien"] if e["loai"] == "semantic_contract"]
    so_fact = sk_hd[-1].get("so_fact") if sk_hd else None

    analyze = R.cham_analyze(ct, nguon, so_fact_quan_sat=so_fact)
    synth = cham_cu.get("synthesis") or {}
    kq = cham_cu.get("ket_qua") or {}

    dap = _dap_so(str(kq.get("FINAL_MEMORY")))
    wit = (analyze.get("WITNESS_KHAI") or [None])[0]
    quan_sat = dap.get(wit) if wit else None
    exact = ("PASS" if quan_sat == ORACLE["radius_c"]
             else (NR if not kq.get("SERVABLE") else "FAIL"))

    # ── Trace / Scene3D đọc từ envelope THẬT của lượt chạy ──────────────
    sc = ((d.get("envelope") or {}).get("scene3d") or {})
    vat = {str(o.get("id")): o for o in (sc.get("objects") or [])}
    ten_c = synth.get("MEASURE_OF")
    ten_T = synth.get("DIEM_CHIA_TEN")
    ten_non = next((t for t, o in vat.items()
                    if str(o.get("producer") or "").startswith(
                        "construct_curved_solid")), None)
    trace_ok = all([
        ten_T and vat.get(ten_T, {}).get("producer")
        == "construct_point.divide_segment",
        ten_non is not None,
        ten_c and vat.get(ten_c, {}).get("producer") == "intersect_plane_curved",
        ten_c and vat.get(ten_c, {}).get("type") == "circle3",
    ])

    # ── Token ───────────────────────────────────────────────────────────
    ts = (d.get("tokens") or {}).get("theo_stage") or {}
    an = ts.get("semantic_analyze") or {}
    sp = ts.get("semantic_program") or {}
    n_ung_vien = cham_cu.get("CANDIDATE_ATTEMPTS_QUAN_SAT") or 0
    tb_sp = (sp.get("total_tokens", 0) / sp["calls"]) if sp.get("calls") else 0
    token = {
        "analyze": an.get("total_tokens"),
        "synthesis_va_repair_gop": sp.get("total_tokens"),
        "so_luot_synthesis_va_repair": sp.get("calls"),
        "trung_binh_moi_luot_synthesis": round(tb_sp) if tb_sp else None,
        "den_first_attempt_UOC_LUONG": (
            round((an.get("total_tokens") or 0) + tb_sp) if tb_sp else None),
        "den_eventual_result": (d.get("tokens") or {}).get("tong"),
        "tren_mot_mo_phong_served_dung": (
            (d.get("tokens") or {}).get("tong") if exact == "PASS"
            else f"UNDEFINED (0 ca dung; tong {(d.get('tokens') or {}).get('tong')})"),
        "cached_content": {"analyze": an.get("cached_content_tokens"),
                           "synthesis": sp.get("cached_content_tokens")},
        "⚠️": ("`synthesis_va_repair_gop` là TỔNG ba lượt — telemetry gộp theo "
               "TẦNG, không tách theo attempt. Nên token của riêng lượt đầu "
               "chỉ ƯỚC LƯỢNG được bằng trung bình, và nó được ghi là ước "
               "lượng chứ không ghi như số đo."),
    }

    ra: dict[str, Any] = {
        "khai": "Cham lai artifact bat bien, 0 luot goi them. Ba gia tri phan "
                "biet: PASS/FAIL · NOT_CAPTURED · NOT_REACHED.",
        "wave": "CURVED_END_TO_END_FRESH_CONFIRMATION",
        "case_id": CASE_ID,
        "artifact": art.name,
        "sha256_artifact": hashlib.sha256(raw).hexdigest(),
        "dinh_chinh": {
            "truong": "ANALYZE_CONTRACT_CORRECT",
            "ban_inline_cua_luot_chay": (cham_cu.get("analyze") or {}).get(
                "ANALYZE_CONTRACT_CORRECT"),
            "ban_dung": analyze.get("ANALYZE_CONTRACT_CORRECT"),
            "vi_sao": "Runner luot chay dau KHONG giu raw cua tang analyze, nen "
                      "bo cham doc rong roi ket luan FAIL — cham truot mot tang "
                      "no khong quan sat duoc. Da sua runner (test_C5) va bo "
                      "cham (test_C6/C7).",
            "gi_KHONG_doi": "Moi ket luan khac cua luot chay: served, dap so 4, "
                            "synthesis, trace, Scene3D, token.",
        },
        "analyze": analyze,
        "synthesis": synth,
        "ket_qua": {
            "STAGE": kq.get("STAGE"),
            "SERVABLE": kq.get("SERVABLE"),
            "ENVELOPE_STATUS": kq.get("ENVELOPE_STATUS"),
            "EXACT_ANSWER": exact,
            "ANSWER_OBSERVED": quan_sat,
            "ANSWER_EXPECTED": ORACLE["radius_c"],
            "WITNESS": wit,
            "TRACE_CONSTRUCTION": "PASS" if trace_ok else "FAIL",
            "SCENE3D": "PASS" if vat else NR,
            "SCENE_OBJS": len(vat),
            "GROUNDING": "PASS" if kq.get("SERVABLE") else NR,
            "SOURCE_INVARIANTS": "PASS" if kq.get("SERVABLE") else NR,
            "STATIC": "PASS" if kq.get("SERVABLE") else NR,
            "COVERAGE": "PASS" if kq.get("SERVABLE") else NR,
            "RUNTIME": "PASS" if kq.get("SERVABLE") else NR,
            "POSTCONDITIONS": "PASS" if kq.get("SERVABLE") else NR,
        },
        "attempts": {
            "FIRST_ATTEMPT_SERVABLE": cham_cu.get("FIRST_ATTEMPT_SERVABLE"),
            "EVENTUAL_SERVABLE": cham_cu.get("EVENTUAL_SERVABLE"),
            "CANDIDATE_ATTEMPTS": n_ung_vien,
            "REPAIR_ATTEMPTS": cham_cu.get("REPAIR_ATTEMPTS"),
            "loi_tung_attempt": [
                {"n": a.get("n"), "gate": a.get("gate"),
                 "message": a.get("message")}
                for a in (d.get("attempts") or [])],
        },
        "bo_dem": mf.get("bo_dem"),
        # Artifact lượt chạy ghi `bo_dem` theo hình dạng LÚC ẤY — chưa có phân
        # rã theo tầng. Suy lại từ telemetry (nguồn ĐỘC LẬP với bộ đếm), vì
        # tổng `candidate_attempts = 4` đọc một mình sẽ bị hiểu là 4 ứng viên
        # CHƯƠNG TRÌNH, trong khi có 1 lượt là `analyze` trả HỢP ĐỒNG.
        "bo_dem_phan_ra_theo_tang": {
            tang: v.get("calls") for tang, v in ts.items()
        },
        "token": token,
        "danh_tinh": {
            "card_C_sha256": mf.get("card_C_sha256"),
            "cache_version": "86",
            "candidate": "138db7b1650dec32",
            "runner_sha256_luc_chay": mf.get("runner_sha256"),
            "⚠️_runner_da_sua_sau_luot_chay": (
                "Runner duoc sua SAU luot chay de giu raw analyze. Hash trong "
                "manifest la hash LUC CHAY va la hash dung cho luot do; hash "
                "hien tai khac, va do la dieu duoc mong doi."),
        },
    }
    p = RA / "SCORING.json"
    p.write_text(json.dumps(ra, ensure_ascii=False, indent=2),
                 encoding="utf-8", newline="\n")
    print(f"→ {p}")
    print(f"  stage={ra['ket_qua']['STAGE']} servable={ra['ket_qua']['SERVABLE']}"
          f" exact={ra['ket_qua']['EXACT_ANSWER']}"
          f" ({ra['ket_qua']['ANSWER_OBSERVED']}/{ORACLE['radius_c']})")
    print(f"  analyze: obligation={analyze.get('ANALYZE_OBLIGATION_CORRECT')}"
          f" facts={analyze.get('ANALYZE_FACTS_CORRECT', R.NOT_CAPTURED)}"
          f" (nguồn {nguon}, so_fact={analyze.get('SO_FACT')})")
    print(f"  attempts: {n_ung_vien} ứng viên · "
          f"{ra['attempts']['REPAIR_ATTEMPTS']} lượt sửa · "
          f"first_servable={ra['attempts']['FIRST_ATTEMPT_SERVABLE']}")
    print(f"  trace={ra['ket_qua']['TRACE_CONSTRUCTION']}"
          f" scene={ra['ket_qua']['SCENE3D']} ({ra['ket_qua']['SCENE_OBJS']} vật)")
    print(f"  token: analyze {token['analyze']} · synthesis+repair "
          f"{token['synthesis_va_repair_gop']} · tổng {token['den_eventual_result']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
