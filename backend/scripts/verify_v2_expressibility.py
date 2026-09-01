# -*- coding: utf-8 -*-
"""§5 — `CANONICAL_EXECUTABLE` cho bộ V2, đo qua TOÀN BỘ chuỗi cổng. 0 call.

    validator → thẩm định tĩnh → grounding + trung thực → thực thi
              → hậu điều kiện → envelope + vận chuyển → oracle tính tay

Chạy TRƯỚC seal. Đề nào không đạt phải THAY, và thay trước seal — sau seal thì
không đổi nữa.

─── VÌ SAO ĐO CẢ TRANSPORT ────────────────────────────────────────────────

V1 dừng ở oracle. Nhưng một envelope không `json.dumps` được vẫn là một ca
hỏng với học sinh, và nó từng lọt qua mọi cổng khác đúng một wave. Đo ở đây
thì một đề mang bug ấy bị loại TRƯỚC khi tiêu call, không phải sau.

─── §6 — BỘ ĐỀ PHẢI THẬT SỰ CHẠM HỢP ĐỒNG MỚI ─────────────────────────────

Đếm điểm dẫn xuất trong lời giải chuẩn tắc. Dưới 3/6 thì bộ đề không kiểm
được `IR_FIRST_BINDING_CONTRACT`, tức wave đo một thứ khác thứ nó khai.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
GOC = BE.parent

from app.simulation.semantic_program.grounding_gate import (  # noqa: E402
    check_grounding,
)
from app.simulation.semantic_program.interpreter import (  # noqa: E402
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.ir_static_check import kiem_tinh  # noqa: E402
from app.simulation.semantic_program.pipeline_adapter import (  # noqa: E402
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.transport import (  # noqa: E402
    check_envelope_transport,
)
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)
from scripts.clean_baseline_v2_cases import CASES, check_contamination  # noqa: E402
from scripts.verify_baseline_expressibility import bang, mong_doi  # noqa: E402


def kiem_mot(case: dict) -> dict:
    r = {"id": case["id"], "topology": case["topology"],
         "capability_mix": case["capability_mix"],
         "derived_entity_count": case["derived_entity_count"],
         "expected_dependency_depth": case["expected_dependency_depth"],
         "obligation_count": case["obligation_count"]}
    v = validate_semantic_program(case["chuan_tac"])
    r["validator"] = v.ok
    if not v.ok:
        return {**r, "canonical_executable": False, "loi": (v.error or "")[:150]}

    # §6 — điểm DẪN XUẤT trong lời giải chuẩn tắc.
    r["diem_dan_xuat"] = [s.target_var for s in v.spec.statements
                          if s.kind == "construct_point"]

    t = kiem_tinh(v.spec)
    r["tinh"] = t.ok
    if not t.ok:
        return {**r, "canonical_executable": False,
                "loi": t.phan_hoi()[:150]}

    g = check_grounding(RequestContract(problem_text=case["de"]), v.spec)
    r["grounding"] = g.ok
    if not g.ok:
        return {**r, "canonical_executable": False,
                "loi": f"[{g.error_code}] " + "; ".join(g.unresolved[:3])}

    try:
        kq = SemanticProgramInterpreter().execute(v.spec)
    except Exception as e:  # noqa: BLE001
        return {**r, "canonical_executable": False,
                "loi": f"{type(e).__name__}: {e}"}
    r["trace_steps"] = kq.total_steps

    try:
        env = compile_semantic_program_to_envelope(v.spec)
        tr = check_envelope_transport(env)
    except Exception as e:  # noqa: BLE001
        tr = f"{type(e).__name__}: {e}"
    r["transport"] = tr is None
    if tr is not None:
        return {**r, "canonical_executable": False, "loi": str(tr)[:150]}

    ok = True
    for khoa, nhan in (("dap_so", "oracle"), ("dap_so_phu", "oracle_phu")):
        if khoa not in case:
            continue
        mong = mong_doi(case[khoa])
        khop = [k for k, val in kq.final_memory.items() if bang(val, mong)]
        r[nhan] = str(mong)
        r[f"{nhan}_khop"] = khop
        ok = ok and bool(khop)
    return {**r, "canonical_executable": ok,
            "loi": None if ok else "chạy được nhưng KHÔNG khớp oracle tính tay"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", type=Path)
    p.add_argument("--tiem-de-cu", action="store_true",
                   help="§8 tiêm lỗi: nhét một đề development cũ vào set")
    a = p.parse_args()

    them = []
    if a.tiem_de_cu:
        from scripts.clean_baseline_cases import CASES as V1

        them = [{"id": "TIEM_de_V1", "de": V1[0]["de"]}]

    nhiem = check_contamination(them)
    print("━━ NHIỄM CHÉO ━━")
    print(f"  {'SẠCH' if not nhiem else 'CÓ TRÙNG:'}")
    for x in nhiem:
        print(f"    · {x}")
    if a.tiem_de_cu:
        ok = any("TIEM_de_V1" in x for x in nhiem)
        print(f"\n{'✓' if ok else '✗'} TIÊM LỖI: guard "
              f"{'ĐỎ được — đã chứng minh' if ok else 'KHÔNG bắt — vô dụng'}")
        return 0 if ok else 1

    ket = [kiem_mot(c) for c in CASES]
    print("\n━━ §5 CANONICAL_EXECUTABLE — chạy TOÀN BỘ chuỗi cổng ━━\n")
    print(f"{'đề':36s} {'val':>4s} {'tĩnh':>5s} {'grnd':>5s} {'tran':>5s} "
          f"{'bước':>5s}  oracle")
    print("─" * 100)
    for r in ket:
        print(f"{r['id']:36s} {str(r.get('validator')):>4s} "
              f"{str(r.get('tinh')):>5s} {str(r.get('grounding')):>5s} "
              f"{str(r.get('transport')):>5s} "
              f"{str(r.get('trace_steps', '')):>5s}  {r.get('oracle', '')}"
              + (f" + {r['oracle_phu']}" if r.get("oracle_phu") else "")
              + ("" if r["canonical_executable"] else f"   ✗ {r['loi']}"))

    n = sum(1 for r in ket if r["canonical_executable"])
    co_diem = sum(1 for r in ket if r.get("diem_dan_xuat"))
    print(f"\nCANONICAL_EXECUTABLE: {n}/{len(ket)}")
    print(f"§6 ca có điểm DẪN XUẤT: {co_diem}/{len(ket)} "
          f"(cần ≥ 3 để bộ đề thật sự chạm hợp đồng ràng buộc lần đầu)")
    ok = n == len(ket) and not nhiem and co_diem >= 3

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(
            {"khai": "§5 — lời giải chuẩn tắc do NGƯỜI viết, chạy qua đúng "
                     "chuỗi cổng sản phẩm kể cả vận chuyển, đối chiếu oracle "
                     "tính tay. KHÔNG gửi cho model. 0 API call.",
             "nhiem_cheo": nhiem,
             "canonical_executable": f"{n}/{len(ket)}",
             "ca_co_diem_dan_xuat": co_diem, "cases": ket},
            ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"→ {a.json}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
