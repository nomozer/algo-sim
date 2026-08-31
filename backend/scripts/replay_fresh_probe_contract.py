# -*- coding: utf-8 -*-
"""REPLAY §13/§16 — `fp_5` và `fp_6` dưới hợp đồng ĐÃ SỬA. **0 API call.**

─── ĐIỀU SCRIPT NÀY KHÔNG LÀM ─────────────────────────────────────────────

Không đổi điểm live. `fresh-probe/probe.json` giữ nguyên `4/6`, `fp_5` vẫn là
`EXECUTABLE_BUT_INCORRECT`, `fp_6` vẫn là `FAIL_AFTER_REPAIR`. Chạy lại một
chương trình đã lưu dưới luật mới **không** biến nó thành một lượt live thành
công — nó chỉ trả lời một câu hẹp hơn:

    lỗi HÔM QUA có phải lỗi của MÔ HÌNH, hay của HỢP ĐỒNG ta đưa nó?

─── `fp_5` — chương trình KHÔNG đổi một byte ──────────────────────────────

Cùng JSON, cùng biến `cos_angle_SC_ABC_sq`, cùng opcode `angle_cos_sq` trên
cặp (đường, mặt). Trước: `1/3`. Sau: `2/3`. Chương trình luôn đúng; runtime
trước đó trả sai đại lượng.

⚠️ Đây CHÍNH LÀ ca §8 cảnh báo: *cùng JSON, runtime cho hai giá trị khác nhau*.
Nên nó phải được ghi thành một migration có tên, không được lặng lẽ. Xem
`ANGLE_SEMANTICS_ERRATUM.md`.

─── `fp_6` — chương trình VẪN hỏng, và đó là câu trả lời ──────────────────

Chương trình cũ phát `{"kind": "perpendicular"}`. Nó vẫn không validate được —
đúng như thế. Điều wave này sửa không phải là nhận token ấy, mà là **thôi
quảng cáo** nó ở bề mặt mô hình. Nên phép kiểm đúng cho `fp_6` không phải
"chương trình cũ nay chạy được" mà là "bề mặt mô hình không còn dạy nó nữa".
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
GOC = BE.parent

from app.ai.gemini import load_skill  # noqa: E402
from app.simulation.semantic_program.grammar_card import grammar_card  # noqa: E402
from app.simulation.semantic_program.interpreter import (  # noqa: E402
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)

PROBE = GOC / "docs" / "evaluation" / "geometry" / "fresh-probe" / "probe.json"
NGHIA_VU = ("perpendicular", "parallel", "coplanar", "point_on_line",
            "point_on_plane", "obligations")


def _ca(cid: str) -> dict:
    d = json.loads(PROBE.read_text(encoding="utf-8"))
    return next(c for c in d["cases"] if c["case_id"] == cid)


def replay_fp5() -> dict:
    c = _ca("fp_5_goc_va_khoang_cach")
    raw = c["programs"][-1]
    v = validate_semantic_program(json.loads(raw))
    assert v.ok, v.error
    kq = SemanticProgramInterpreter().execute(v.spec)
    mem = kq.final_memory

    # Opcode + kiểu toán hạng, đọc TỪ CHƯƠNG TRÌNH chứ không từ trí nhớ.
    do = None
    for st in v.spec.statements:
        e = getattr(st, "expr", None)
        if getattr(e, "kind", "") == "measure" and "angle" in e.quantity:
            do = {"bien": st.target_var, "opcode": e.quantity,
                  "of": e.of, "wrt": e.wrt}
    return {
        "case_id": c["case_id"],
        "chuong_trinh_doi_khong": False,
        "opcode": do["opcode"], "of": do["of"], "wrt": do["wrt"],
        "ten_bien_mo_hinh_dat": do["bien"],
        "gia_tri_CU": c.get("bien_khop_oracle_phu") and "?" or "1/3",
        "gia_tri_MOI": str(mem.get(do["bien"])),
        "oracle": c.get("oracle_phu"),
        "khop_oracle": str(mem.get(do["bien"])) == str(c.get("oracle_phu")),
        "lop_live_GIU_NGUYEN": c["class"],
    }


def replay_fp6() -> dict:
    c = _ca("fp_6_nhieu_nghia_vu_sau")
    ket = []
    for i, raw in enumerate(c.get("programs") or []):
        try:
            v = validate_semantic_program(json.loads(raw))
            ket.append({"luot": i, "ok": v.ok,
                        "loi": (v.error or "")[:160] if not v.ok else None})
        except Exception as e:  # noqa: BLE001
            ket.append({"luot": i, "ok": False, "loi": f"{type(e).__name__}"})

    be_mat = load_skill("geometry_program_generator") + grammar_card("hinh_hoc")
    con_lai = [t for t in NGHIA_VU if t in be_mat]
    return {
        "case_id": c["case_id"],
        "chuong_trinh_van_khong_validate": all(not k["ok"] for k in ket),
        "luot": ket,
        "tu_vung_nghia_vu_con_tren_be_mat": con_lai,
        "drift_da_het": not con_lai,
        "lop_live_GIU_NGUYEN": c["class"],
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", type=Path)
    a = p.parse_args()

    r5, r6 = replay_fp5(), replay_fp6()
    print("━━ §13 REPLAY `fp_5` — chương trình KHÔNG đổi một byte ━━")
    print(f"  opcode      {r5['opcode']}({r5['of']}, {r5['wrt']})")
    print(f"  biến        {r5['ten_bien_mo_hinh_dat']}  ← tên nói 'cos'")
    print(f"  CŨ          1/3   (runtime trả sin²)")
    print(f"  MỚI         {r5['gia_tri_MOI']}   · oracle {r5['oracle']} · "
          f"khớp {r5['khop_oracle']}")
    print(f"  lớp live    {r5['lop_live_GIU_NGUYEN']}  ← KHÔNG đổi")

    print("\n━━ §16 REPLAY `fp_6` — drift từ vựng ━━")
    for k in r6["luot"]:
        print(f"  lượt{k['luot']} validate={k['ok']}  {k['loi'] or ''}")
    print(f"  chương trình cũ vẫn không validate: "
          f"{r6['chuong_trinh_van_khong_validate']}  ← ĐÚNG như thế")
    print(f"  từ vựng nghĩa vụ còn trên bề mặt mô hình: "
          f"{r6['tu_vung_nghia_vu_con_tren_be_mat'] or 'KHÔNG CÒN'}")
    print(f"  drift đã hết: {r6['drift_da_het']}")

    ok = r5["khop_oracle"] and r6["drift_da_het"]
    print(f"\n{'✓' if ok else '✗'} REPLAY "
          f"{'XANH' if ok else 'ĐỎ'} — 0 API call, điểm live không đổi")
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(
            {"khai": "Replay §13/§16 — chương trình đã lưu chạy dưới hợp đồng "
                     "ĐÃ SỬA. KHÔNG đổi điểm live, KHÔNG gọi model.",
             "fp_5": r5, "fp_6": r6, "pass": ok},
            ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"→ {a.json}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
