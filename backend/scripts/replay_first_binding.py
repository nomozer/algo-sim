# -*- coding: utf-8 -*-
"""§11 — replay 6 chương trình CLEAN_BASELINE_V1 dưới hợp đồng MỚI. 0 call.

─── ĐIỀU SCRIPT NÀY KHÔNG LÀM ─────────────────────────────────────────────

Không sửa chương trình bằng tay. Không đổi điểm live: `probe.json` giữ nguyên
2/6, và bốn ca `SYSTEM_FAILURE` vẫn là `SYSTEM_FAILURE` trong lịch sử.

Câu duy nhất nó trả lời:

    Nếu hợp đồng ràng buộc-lần-đầu này có mặt LÚC ĐO, bao nhiêu chương trình
    đã có một đường tất định hợp lệ?

Kết quả ghi dưới tên riêng `OFFLINE_EXECUTABLE_AFTER_FIX` — **không** phải một
lượt live thành công, và không được đọc như thế.

─── §13 TÁC ĐỘNG TOKEN, CHỈ TỪ ARTIFACT THẬT ─────────────────────────────

Đếm lượt gọi và token đã tiêu cho những ca chết vì đúng tiền điều kiện này.
Không ngoại suy sang bài chưa chạy: một con số ngoại suy trông giống một phép
đo và không phải một phép đo.
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
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.simulation_state import (  # noqa: E402
    _provenance,
)
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)
from scripts.clean_baseline_cases import CASES  # noqa: E402
from scripts.verify_baseline_expressibility import bang, mong_doi  # noqa: E402

PROBE = GOC / "docs" / "evaluation" / "geometry" / "clean-baseline-v1" / "probe.json"
_ORACLE = {c["id"]: c for c in CASES}


def mot_ca(c: dict) -> dict:
    ra = {"case_id": c["case_id"], "lop_live_GIU_NGUYEN": c.get("class"),
          "stage_live": c.get("stage"), "loi_live": (c.get("error") or "")[:110]}
    raws = c.get("programs") or []
    if not raws:
        return {**ra, "offline": "KHÔNG CÓ CHƯƠNG TRÌNH"}

    # Chương trình THÔ của mô hình, không sửa một byte.
    v = validate_semantic_program(json.loads(raws[-1]))
    ra["schema"] = v.ok
    if not v.ok:
        return {**ra, "offline": "SCHEMA_FAIL", "chi_tiet": (v.error or "")[:140]}

    t = kiem_tinh(v.spec)
    ra["tinh"] = t.ok
    if not t.ok:
        return {**ra, "offline": "STATIC_FAIL", "chi_tiet": t.phan_hoi()[:140]}

    # ─── GROUNDING Ở ĐÂY CHỈ SO ĐƯỢC MỘT NỬA ────────────────────────────
    #
    # `probe.json` chỉ lưu TÓM TẮT hợp đồng (số `input_facts`, tập nghĩa vụ),
    # không lưu chính các dữ kiện. Hợp đồng dựng lại vì thế RỖNG, nên mọi
    # `source_fact_id` mô hình trích dẫn đều không giải được và grounding trả
    # `INPUT_NOT_GROUNDED` — kể cả cho `cb_02`, ca ĐÃ QUA grounding ở lượt
    # live. Đọc con số ấy như một hồi quy là đọc lỗi của bộ đo thành lỗi của hệ.
    #
    # Hai mã tách hẳn nhau, và chỉ một trong hai so được:
    #
    #   INPUT_NOT_GROUNDED  — phụ thuộc `input_facts` ⇒ KHÔNG so được ở đây
    #   mã TRUNG THỰC       — chỉ phụ thuộc `problem_text`, thứ ta CÓ ⇒ so được
    #
    # Nên ca thứ hai vẫn dừng (nó là một phán quyết thật), còn ca thứ nhất chỉ
    # được GHI rồi đi tiếp — vì câu hỏi của §11 là *"còn chết ở runtime vì tiền
    # điều kiện khai báo không"*, và grounding không trả lời câu đó.
    from app.simulation.semantic_program.grounding_gate import (
        ERR_RUA_NANG_LUC,
        ERR_THIEU_NGUOI_DUNG,
    )

    de = _ORACLE[c["case_id"]]["de"]
    g = check_grounding(RequestContract(problem_text=de), v.spec)
    ra["grounding"] = g.ok
    ra["grounding_ma"] = g.error_code
    if not g.ok and g.error_code in {ERR_RUA_NANG_LUC, ERR_THIEU_NGUOI_DUNG}:
        return {**ra, "offline": "HONESTY_FAIL", "ma": g.error_code}
    if not g.ok:
        ra["grounding_khong_so_duoc"] = (
            "hợp đồng replay không có `input_facts` — artifact chỉ lưu tóm tắt")

    try:
        kq = SemanticProgramInterpreter().execute(v.spec)
    except Exception as e:  # noqa: BLE001
        return {**ra, "offline": "RUNTIME_FAIL",
                "ma": getattr(e, "code", None) or type(e).__name__,
                "chi_tiet": str(e)[:140]}

    # §5 — vật dựng ra phải giữ producer.
    prov = _provenance(v.spec)
    hh = {d.name for d in v.spec.memory_declarations
          if d.type in ("point3", "vector3", "line3", "plane3", "polygon3",
                        "solid", "section")}
    tao_ra = {getattr(s, "target_var", None) for s in v.spec.statements
              if getattr(s, "kind", "").startswith("construct")
              or getattr(s, "kind", "") == "assign"}
    mat_prov = sorted(x for x in (hh & tao_ra)
                      if x and not prov.get(x)
                      and not any(d.name == x and d.initial_value is not None
                                  for d in v.spec.memory_declarations))
    ra["provenance_thieu"] = mat_prov

    oc = _ORACLE[c["case_id"]]
    dung = True
    for khoa, nhan in (("dap_so", "oracle"), ("dap_so_phu", "oracle_phu")):
        if khoa not in oc:
            continue
        mong = mong_doi(oc[khoa])
        khop = [k for k, val in kq.final_memory.items() if bang(val, mong)]
        ra[nhan] = str(mong)
        ra[f"{nhan}_khop"] = khop
        dung = dung and bool(khop)
    return {**ra, "offline": "EXECUTABLE_CORRECT" if dung
            else "EXECUTABLE_WRONG_ANSWER"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", type=Path)
    a = p.parse_args()

    d = json.loads(PROBE.read_text(encoding="utf-8"))
    ket = [mot_ca(c) for c in d["cases"]]

    print("━━ §11 REPLAY — 6 chương trình THÔ, hợp đồng ràng buộc-lần-đầu ━━\n")
    print(f"{'đề':34s} {'live (GIỮ NGUYÊN)':24s} → offline")
    print("─" * 96)
    for r in ket:
        print(f"{r['case_id']:34s} {str(r['lop_live_GIU_NGUYEN']):24s} → "
              f"{r['offline']}"
              + (f"  [{r.get('ma')}]" if r.get("ma") else "")
              + (f"  provenance thiếu: {r['provenance_thieu']}"
                 if r.get("provenance_thieu") else ""))

    chay = sum(1 for r in ket if r["offline"].startswith("EXECUTABLE"))
    dung = sum(1 for r in ket if r["offline"] == "EXECUTABLE_CORRECT")
    runtime_hong = sum(1 for r in ket if r["offline"] == "RUNTIME_FAIL")

    # §13 — token đã tiêu cho ca chết vì đúng tiền điều kiện này.
    cu = {c["case_id"]: c for c in d["cases"]}
    tranh_duoc = [r["case_id"] for r in ket
                  if r["lop_live_GIU_NGUYEN"] == "SYSTEM_FAILURE"
                  and r["offline"].startswith("EXECUTABLE")]
    tok = sum(cu[x].get("total_tokens", 0) for x in tranh_duoc)
    goi = sum(cu[x].get("logical_calls", 0) for x in tranh_duoc)

    print(f"\n  chạy được offline        {chay}/6")
    print(f"  OFFLINE_EXECUTABLE_AFTER_FIX (đúng oracle)  {dung}/6")
    print(f"  còn chết ở runtime       {runtime_hong}/6")
    print(f"  ca live SYSTEM_FAILURE nay có đường chạy: {len(tranh_duoc)}")
    print(f"  AVOIDABLE_REPAIR_CALLS   {goi}")
    print(f"  AVOIDABLE_TOKENS         {tok}")
    print("\n⚠️ Đây KHÔNG phải điểm live. `probe.json` giữ nguyên 2/6.")

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps({
            "khai": "§11 replay — chương trình THÔ của CLEAN_BASELINE_V1 chạy "
                    "dưới hợp đồng ràng buộc-lần-đầu. KHÔNG sửa chương trình, "
                    "KHÔNG đổi điểm live. 0 API call.",
            "historical_score_changed": False,
            "offline_executable_after_fix": f"{dung}/6",
            "con_chet_runtime": runtime_hong,
            "avoidable_repair_calls": goi, "avoidable_tokens": tok,
            "cases": ket}, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")
        print(f"→ {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
