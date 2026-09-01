# -*- coding: utf-8 -*-
"""Chạy lại các chương trình LỒNG TOÁN HẠNG trong lịch sử — 0 lượt gọi model.

§18/§19 của `NAMED_GEOMETRY_OPERAND_ERGONOMICS`. Lấy nguyên chương trình THÔ
model từng phát ra (đã commit trong `docs/evaluation/geometry/**`), cho đi qua
lớp chuẩn hoá tiện dụng mới, rồi qua đúng chuỗi cổng tất định của sản phẩm:

    schema → thẩm định tĩnh → grounding + trung thực năng lực → thực thi → transport

**Không sửa một byte nào của artifact**, và **không đổi một điểm số lịch sử
nào**: điểm của một lượt là điểm của hệ TẠI LÚC ẤY. Cái đo ở đây là *hệ hôm nay
làm gì với đúng đầu vào hôm qua* — một câu hỏi khác, và phải được gọi bằng tên
khác.

    .venv/Scripts/python.exe scripts/replay_nested_operand_history.py
    .venv/Scripts/python.exe scripts/replay_nested_operand_history.py --json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.simulation.semantic_program.grounding_gate import check_grounding  # noqa: E402
from app.simulation.semantic_program.hoisting import TIEN_TO_TAM, kiem_nang  # noqa: E402
from app.simulation.semantic_program.interpreter import (  # noqa: E402
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.ir_static_check import kiem_tinh  # noqa: E402
from app.simulation.semantic_program.pipeline_adapter import (  # noqa: E402
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.request_contract import RequestContract  # noqa: E402
from app.simulation.semantic_program.transport import (  # noqa: E402
    check_envelope_transport,
)
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)

GOC = pathlib.Path(__file__).resolve().parents[2]
THU_MUC = GOC / "docs" / "evaluation" / "geometry"


def _duyet_ca(node, duong: str = ""):
    """Mọi nút có `programs` — kèm `problem_text` nếu artifact có ghi."""
    if isinstance(node, dict):
        if isinstance(node.get("programs"), list):
            yield duong, node
        for k, v in node.items():
            yield from _duyet_ca(v, f"{duong}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _duyet_ca(v, f"{duong}[{i}]")


def _qua_cong(raw: dict, de: str | None) -> dict:
    """Chuỗi cổng tất định. Dừng ở cổng đầu tiên nói không."""
    r: dict = {}
    v = validate_semantic_program(raw)
    r["schema"] = v.ok
    if not v.ok:
        return {**r, "executable": False, "loi": (v.error or "")[:160]}

    r["temps"] = [d.name for d in v.spec.memory_declarations
                  if d.name.startswith(TIEN_TO_TAM)]
    t = kiem_tinh(v.spec)
    r["static"] = t.ok
    if not t.ok:
        return {**r, "executable": False, "loi": t.phan_hoi()[:160]}

    if de:
        # `check_grounding` mang LUÔN cổng trung thực năng lực
        # (`UNANCHORED_DERIVED_ASSUMPTION`, `DERIVED_ENTITY_WITHOUT_PRODUCER`).
        g = check_grounding(RequestContract(problem_text=de), v.spec)
        r["grounding"] = r["honesty"] = g.ok
        if not g.ok:
            return {**r, "executable": False,
                    "loi": f"[{g.error_code}] " + "; ".join(g.unresolved[:3])}
    else:
        # Không có đề trong artifact ⇒ KHÔNG chấm grounding. Bịa một đề để cổng
        # chạy được là tự cấp cho mình một kết quả.
        r["grounding"] = r["honesty"] = None

    try:
        kq = SemanticProgramInterpreter().execute(v.spec)
    except Exception as e:  # noqa: BLE001
        return {**r, "executable": False, "loi": f"{type(e).__name__}: {e}"[:160]}
    r["trace_steps"] = kq.total_steps

    try:
        tr = check_envelope_transport(compile_semantic_program_to_envelope(v.spec))
    except Exception as e:  # noqa: BLE001
        tr = f"{type(e).__name__}: {e}"
    r["transport"] = tr is None
    return {**r, "executable": tr is None,
            "loi": None if tr is None else str(tr)[:160]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    ket: list[dict] = []
    for p in sorted(THU_MUC.rglob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        for duong, ca in _duyet_ca(d):
            for i, s in enumerate(ca["programs"]):
                if not isinstance(s, str):
                    continue
                try:
                    raw = json.loads(s)
                except ValueError:
                    continue
                if not isinstance(raw, dict):
                    continue
                hs = kiem_nang(raw)
                if not hs:
                    continue          # không lồng gì ⇒ ngoài câu hỏi của §18
                ket.append({
                    "artifact": str(p.relative_to(GOC)).replace("\\", "/"),
                    "case_id": ca.get("case_id") or duong,
                    "program_index": i,
                    "nested": len(hs),
                    "an_toan": sum(1 for x in hs if x["an_toan"]),
                    "kinds": sorted({x["kind_long"] for x in hs}),
                    **_qua_cong(raw, ca.get("problem_text")),
                })

    tong_long = sum(k["nested"] for k in ket)
    chay = [k for k in ket if k["executable"]]
    if ns.json:
        print(json.dumps({
            "HISTORICAL_NESTED_EXPR_ATTEMPTS": tong_long,
            "PROGRAMS_WITH_NESTED_OPERANDS": len(ket),
            "EXECUTABLE_AFTER_NORMALIZATION": len(chay),
            "ket": ket,
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"HISTORICAL_NESTED_EXPR_ATTEMPTS = {tong_long} "
          f"(trong {len(ket)} chương trình)")
    print(f"EXECUTABLE_AFTER_NORMALIZATION  = {len(chay)}/{len(ket)}\n")
    for k in ket:
        dau = "CHẠY  " if k["executable"] else "DỪNG  "
        print(f"{dau} {k['case_id'][:34]:34s} lồng {k['nested']:2d} "
              f"(an toàn {k['an_toan']:2d}) temp={len(k.get('temps') or [])} "
              f"{','.join(k['kinds'])[:28]}")
        if not k["executable"]:
            print(f"         ✗ {k['loi']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
