# -*- coding: utf-8 -*-
"""Chạy lại TẬP DEMO của khoá luận từ artifact đã lưu. **0 API call.**

`THESIS_SCOPE_FREEZE_AND_DEMO_READINESS §7`. Mỗi ca đi trọn chuỗi tất định:

    chương trình đã lưu → thẩm định → grounding + trung thực → thực thi
    → checker → transport → Scene3D

Không gọi model. Không sinh chương trình mới. Thứ được chứng minh ở đây là
**đường đi tất định**, tức đúng nửa hệ mà đề tài tuyên bố sở hữu.

─── VÌ SAO CHỈ HAI ARTIFACT ĐƯỢC DÙNG LÀM DEMO FULL-CHAIN ─────────────────

`clean-baseline-v2` **không lưu `RequestContract`** (lỗ đã ghi ở ledger, chính
nó đã chặn wave k=3). Không có hợp đồng thì không chạy được grounding, nên một
ca V2 chỉ đi được một phần chuỗi. Ca section của V2 vẫn được chạy ở chế độ
`--rut-gon` để chứng minh NĂNG LỰC, và nó được đếm riêng — gộp nó vào
`DEMO_REPLAY` là báo cáo một chuỗi đủ mà thực ra thiếu một cổng.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.simulation.semantic_program.grounding_gate import check_grounding  # noqa: E402
from app.simulation.semantic_program.interpreter import (  # noqa: E402
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.ir_static_check import kiem_tinh  # noqa: E402
from app.simulation.semantic_program.pipeline_adapter import (  # noqa: E402
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.request_contract import RequestContract  # noqa: E402
from app.simulation.semantic_program.scene3d import build_scene3d  # noqa: E402
from app.simulation.semantic_program.simulation_state import (  # noqa: E402
    build_simulation_state,
)
from app.simulation.semantic_program.transport import (  # noqa: E402
    check_envelope_transport,
)
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

GOC = pathlib.Path(__file__).resolve().parents[2]
DE = GOC / "docs" / "evaluation" / "geometry"

#: Tập demo — `(artifact, case_id, vai trò, kỳ vọng)`.
#:
#: `ky_vong="PASS"` = phải đi hết chuỗi. `ky_vong="REFUSAL"` = phải bị một cổng
#: TỪ CHỐI, và đó chính là thứ đem trình bày: hệ nói KHÔNG có địa chỉ, không
#: chết câm. Một demo chỉ có ca xanh là một demo giấu mất nửa luận điểm.
DEMO = [
    ("name-contract-probe", "n1_thoi_dinh_thu_tu",
     "dựng đỉnh thứ tư từ vectơ · đo tới đường · đáp số vô tỉ √3", "PASS"),
    ("name-contract-probe", "n2_lang_tru_xien_hai_vecto",
     "lăng trụ XIÊN · hai vectơ dẫn xuất · trung điểm · 3√3", "PASS"),
    ("translation-probe", "t3_hop_tinh_tien_day_chuyen",
     "dây chuyền tịnh tiến 4 đỉnh · chuỗi sâu · 3√89/5", "PASS"),
    ("translation-probe", "t4_mat_xich_trong_chuoi_sau",
     "hình chiếu trong chuỗi phụ thuộc · 2√2", "PASS"),
    ("name-contract-probe", "n4_giao_duong_mat_roi_do",
     "CỔNG TỪ CHỐI: trích dẫn dữ kiện không có trong hợp đồng", "REFUSAL"),
]

#: Ca chạy RÚT GỌN — artifact không lưu hợp đồng nên bỏ cổng grounding.
#: Đếm RIÊNG, không gộp vào `DEMO_REPLAY`.
RUT_GON = [
    ("clean-baseline-v2", "v2_04_thiet_dien_goc_va_the_tich",
     "THIẾT DIỆN · góc · thể tích"),
]


def _tim(thu_muc: str, case_id: str) -> dict | None:
    for f in (DE / thu_muc).glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        for c in (d.get("cases") or []):
            if isinstance(c, dict) and c.get("case_id") == case_id:
                return c
    return None


def _chay(c: dict, *, co_grounding: bool) -> dict:
    """Chuỗi cổng tất định. Dừng ở cổng đầu tiên nói không."""
    r: dict = {"stages": {}}
    prog = c.get("normalized_program")
    if not prog:
        return {**r, "ok": False, "dung_o": "NO_PROGRAM"}

    v = validate_semantic_program(prog)
    r["stages"]["schema"] = v.ok
    if not v.ok:
        return {**r, "ok": False, "dung_o": "SCHEMA", "loi": (v.error or "")[:200]}

    t = kiem_tinh(v.spec)
    r["stages"]["static"] = t.ok
    if not t.ok:
        return {**r, "ok": False, "dung_o": "STATIC", "loi": t.phan_hoi()[:200]}

    hd = None
    if co_grounding:
        raw = (c.get("analyze") or {}).get("raw_request_contract")
        if not raw:
            return {**r, "ok": False, "dung_o": "NO_CONTRACT"}
        hd = RequestContract.model_validate(raw)
        g = check_grounding(hd, v.spec)
        # `check_grounding` mang LUÔN cổng trung thực năng lực.
        r["stages"]["grounding"] = r["stages"]["honesty"] = g.ok
        if not g.ok:
            return {**r, "ok": False, "dung_o": "GROUNDING",
                    "ma": g.error_code, "loi": "; ".join(g.unresolved[:3])[:200]}

    try:
        kq = SemanticProgramInterpreter().execute(v.spec)
    except Exception as e:  # noqa: BLE001
        return {**r, "ok": False, "dung_o": "RUNTIME",
                "loi": f"{type(e).__name__}: {e}"[:200]}
    r["stages"]["runtime"] = True
    r["trace_steps"] = kq.total_steps

    if hd is not None:
        kr = verify_and_compile(hd, v.spec)
        r["stages"]["checker"] = bool(kr.executable)
        r["checker"] = {"checked": kr.constraints_checked,
                        "verified": kr.constraints_verified}

    try:
        env = compile_semantic_program_to_envelope(v.spec)
        tr = check_envelope_transport(env)
    except Exception as e:  # noqa: BLE001
        tr = f"{type(e).__name__}: {e}"
    r["stages"]["transport"] = tr is None
    if tr is not None:
        return {**r, "ok": False, "dung_o": "TRANSPORT", "loi": str(tr)[:200]}

    canh = build_scene3d(build_simulation_state(v.spec, kq))
    loai = sorted({o["type"] for o in canh["objects"]})
    r["stages"]["scene3d"] = bool(canh["objects"])
    r["scene"] = {"objects": len(canh["objects"]),
                  "events": len(canh["events"]), "types": loai,
                  # Xuất xứ tới được mặt học sinh hay không — đúng thứ phân
                  # biệt hệ này với một bộ vẽ hình.
                  "co_producer": sum(1 for o in canh["objects"]
                                     if o.get("producer")),
                  "co_depends": sum(1 for o in canh["objects"]
                                    if o.get("depends"))}
    return {**r, "ok": bool(canh["objects"])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    ra: list[dict] = []
    for thu_muc, cid, vai, ky_vong in DEMO:
        c = _tim(thu_muc, cid)
        if c is None:
            ra.append({"case_id": cid, "ok": False, "dung_o": "KHONG_TIM_THAY",
                       "ky_vong": ky_vong, "vai": vai})
            continue
        kq = _chay(c, co_grounding=True)
        # Ca TỪ CHỐI: "đạt" nghĩa là nó bị chặn ĐÚNG CHỖ, không phải nó chạy.
        dat = (not kq["ok"] and kq.get("dung_o") == "GROUNDING"
               if ky_vong == "REFUSAL" else kq["ok"])
        ra.append({"case_id": cid, "artifact": thu_muc, "vai": vai,
                   "ky_vong": ky_vong, "dat": dat, **kq})

    rg: list[dict] = []
    for thu_muc, cid, vai in RUT_GON:
        c = _tim(thu_muc, cid)
        kq = _chay(c, co_grounding=False) if c else {"ok": False,
                                                     "dung_o": "KHONG_TIM_THAY"}
        rg.append({"case_id": cid, "artifact": thu_muc, "vai": vai, **kq})

    tong = {
        "DEMO_CASES": len(DEMO),
        "DEMO_REPLAY_PASS": f"{sum(1 for x in ra if x.get('dat'))}/{len(ra)}",
        "REDUCED_CHAIN_CASES": f"{sum(1 for x in rg if x.get('ok'))}/{len(rg)}",
    }
    if ns.json:
        print(json.dumps({**tong, "demo": ra, "rut_gon": rg},
                         ensure_ascii=False, indent=2))
        return 0

    for x in ra:
        dau = "✔" if x.get("dat") else "✘"
        print(f"{dau} {x['case_id'][:34]:34s} [{x['ky_vong']:7s}] "
              f"dừng={x.get('dung_o') or '—'}  "
              f"bước={x.get('trace_steps')}  "
              f"cảnh={(x.get('scene') or {}).get('objects')}")
        print(f"    {x['vai']}")
        if x.get("scene"):
            s = x["scene"]
            print(f"    loại: {','.join(s['types'])} · producer {s['co_producer']}"
                  f"/{s['objects']} · depends {s['co_depends']}/{s['objects']}"
                  f" · sự kiện {s['events']}")
        if x.get("loi"):
            print(f"    {x.get('ma') or ''} {x['loi']}")
    print("\n── chạy RÚT GỌN (artifact không lưu hợp đồng ⇒ bỏ grounding) ──")
    for x in rg:
        print(f"{'✔' if x.get('ok') else '✘'} {x['case_id'][:34]:34s} "
              f"bước={x.get('trace_steps')} cảnh={(x.get('scene') or {}).get('objects')}"
              f"  {x['vai']}")
        if x.get("scene"):
            print(f"    loại: {','.join(x['scene']['types'])}")
    print()
    for k, v in tong.items():
        print(f"  {k:24s} {v}")
    return 0 if all(x.get("dat") for x in ra) else 1


if __name__ == "__main__":
    raise SystemExit(main())
