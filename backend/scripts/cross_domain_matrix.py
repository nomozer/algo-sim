# -*- coding: utf-8 -*-
"""MA TRẬN CHẤT LƯỢNG XUYÊN MIỀN — bảy lớp trạng thái, MỘT bộ cổng.

VÌ SAO TỒN TẠI: bằng chứng cho một bài không chứng minh được gì về bài kế. Cả
wave vNext trước đó dựa vào đúng một case (chuỗi ngoặc bằng ngăn xếp), và chính
vì thế hai lỗi sản phẩm sống sót — `queue_view` đọc spec tĩnh, `pop` áp LIFO lên
FIFO — cả hai vô hình với bằng chứng chỉ-có-Stack.

Bảy lớp dưới đây đi qua **cùng một** đường và **cùng một** bộ cổng. Không nhánh
riêng cho miền nào; thêm nhánh riêng là tự huỷ giá trị của ma trận.

ĐÁP ÁN MONG ĐỢI ĐƯỢC KIỂM TAY, không chép từ đầu ra của chính hệ:
    21 = 10101₂ ⇒ bit thứ 2 = 1        · max([12,45,67,23,89,34]) = 89
    "radar" đối xứng                    · "{[()]}" cân bằng
    prefix([2,4,1,7,3]) = [2,6,7,14,17] · preorder A(B,C) = A,B,C
    BFS từ 1 trên {1:[2,3],2:[4],3:[4,5]} = 1,2,3,4,5

Chạy:  cd backend && python scripts/cross_domain_matrix.py [--json <f>] [--md <f>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "tests"))

from app.simulation.semantic_program.interpreter import (  # noqa: E402
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.learner_surface import (  # noqa: E402
    _ro_ri,
    check_learner_surface,
)
from app.simulation.semantic_program.obligations import Obligation  # noqa: E402
from app.simulation.semantic_program.pipeline_adapter import (  # noqa: E402
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    RequestContract,
)
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)
from semantic_program.fixtures_coverage_18 import (  # noqa: E402
    ALL_18_COVERAGE_FIXTURES as F,
)

#: (lớp, fixture, witness, đáp án kiểm tay)
CASES: list[tuple[str, Any, str, dict[str, Any]]] = [
    ("scalar", F[13], "bit_is_set", {"bit_is_set": True}),
    ("array", F[1], "max_val", {"max_val": 89, "max_idx": 4}),
    ("string", F[7], "is_pal", {"is_pal": True}),
    ("stack", F[0], "result", {"result": "HỢP LỆ", "stack": []}),
    ("derived_sequence", F[16], "pref", {"pref": [2, 6, 7, 14, 17]}),
    ("tree", F[10], "order", {"order": ["A", "B", "C"]}),
    ("graph", F[8], "order", {"order": ["1", "2", "3", "4", "5"]}),
]

GATES = [
    "PROGRAM_VALID",
    "INTERPRETER_COMPLETE",
    "EXPECTED_RESULT",
    "INPUT_PRESERVED",
    "TRACE_FRAME_CONSISTENT",
    "DYNAMIC_STATE_VISIBLE",
    "WITNESS_VISIBLE",
    "PLACEHOLDER_LEAK_FREE",
    "NARRATION_CONSISTENT",
    "PRESENTATION_INDEPENDENT",
    "TRANSPORT_CONTROLS_VALID",
]


def _chay_mot_case(lop: str, spec, witness: str, mong_doi: dict) -> dict:
    g: dict[str, bool] = {}
    ghi_chu: list[str] = []

    rep = validate_semantic_program(spec.model_dump(mode="json", exclude_none=True))
    g["PROGRAM_VALID"] = bool(getattr(rep, "ok", False))
    if not g["PROGRAM_VALID"]:
        ghi_chu.append(str(getattr(rep, "errors", rep))[:160])

    res = SemanticProgramInterpreter(max_steps=300).execute(spec)
    g["INTERPRETER_COMPLETE"] = res.status in ("completed", "returned")

    g["EXPECTED_RESULT"] = all(
        res.final_memory.get(k) == v for k, v in mong_doi.items()
    )
    if not g["EXPECTED_RESULT"]:
        ghi_chu.append(
            f"đáp án lệch: {({k: res.final_memory.get(k) for k in mong_doi})}"
        )

    env = compile_semantic_program_to_envelope(spec)
    frames = env["config"]["frames"]

    # INPUT_PRESERVED — dữ liệu đề cho phải còn nguyên VÀ CÒN THẤY ĐƯỢC ở khung
    # cuối. Bản đầu chỉ hỏi "còn trong bộ nhớ không", và câu đó gần như luôn
    # đúng nên cổng rỗng: gỡ binding của dãy đầu vào mà nó vẫn xanh.
    # Chỉ tính container ĐÃ ĐƯỢC BIND: bảng tra HẰNG (`pairs` của bài ngoặc)
    # cũng có `initial_value` mà không phải dữ liệu đề, và đòi nó hiện là kêu
    # oan — đúng lằn ranh mà `learner_surface` đã cân nhắc và không vượt.
    duoc_bind = {c.semantic_id for c in (spec.visual_bindings.containers or [])}
    dau_vao = [
        d.name
        for d in spec.memory_declarations
        if d.initial_value not in (None, [], {}, "")
        and d.type in ("array", "graph", "map", "matrix", "set")
        and d.name in duoc_bind
    ]
    hien_o_khung_cuoi = {o.get("id") for o in frames[-1]["objects"]} if frames else set()
    thieu_dau_vao = [
        k for k in dau_vao
        if k not in res.final_memory or k not in hien_o_khung_cuoi
    ]
    g["INPUT_PRESERVED"] = not thieu_dau_vao
    if thieu_dau_vao:
        ghi_chu.append(f"đầu vào không còn thấy được: {thieu_dau_vao}")

    # TRACE_FRAME_CONSISTENT — mỗi khung phải BẰNG bộ nhớ tại đúng bước đó.
    lech: list[str] = []
    for fr, step in zip(frames, res.trace):
        for o in fr["objects"]:
            oid = o.get("id")
            if oid not in step.memory_snapshot:
                continue
            snap = step.memory_snapshot[oid]
            if "items" in o and isinstance(snap, (list, tuple, set)):
                if list(o["items"]) != list(snap):
                    lech.append(f"khung{fr['step_index']}.{oid}")
    g["TRACE_FRAME_CONSISTENT"] = not lech
    if lech:
        ghi_chu.append("lệch khung/bộ nhớ: " + ", ".join(lech[:3]))

    contract = RequestContract(
        obligations=(
            Obligation(kind="membership", container=witness, params={"witness": witness}),
        )
    )
    surf = check_learner_surface(contract, spec, res, env)
    g["DYNAMIC_STATE_VISIBLE"] = not any("đổi giá trị" in u for u in surf.invisible)
    g["WITNESS_VISIBLE"] = not any("witness" in u for u in surf.invisible)
    g["PLACEHOLDER_LEAK_FREE"] = not _ro_ri(env)
    if not surf.ok:
        ghi_chu.extend(surf.invisible[:2])

    g["NARRATION_CONSISTENT"] = all(
        isinstance(fr.get("narration"), str) and fr["narration"].strip()
        for fr in frames
    )

    # PRESENTATION_INDEPENDENT — TẤT ĐỊNH: chạy lại phải cho hình y hệt. Hình
    # phụ thuộc lượt chạy thì không có "phép chiếu ngữ nghĩa" nào ổn định để so.
    env2 = compile_semantic_program_to_envelope(spec)
    g["PRESENTATION_INDEPENDENT"] = env2["config"]["frames"] == frames

    # TRANSPORT_CONTROLS_VALID — chỉ số khung tăng đều từ 0, đi tới khung k
    # phải dựng được đúng khung k (frames đánh chỉ số nên scrub là tra bảng).
    idx = [fr["step_index"] for fr in frames]
    g["TRANSPORT_CONTROLS_VALID"] = len(frames) > 1 and idx == sorted(idx)

    return {
        "lop": lop,
        "title": spec.title,
        "steps": res.total_steps,
        "frames": len(frames),
        "gates": g,
        "pass": all(g.values()),
        "ghi_chu": ghi_chu,
    }


def run_matrix() -> dict:
    rows = [_chay_mot_case(*c) for c in CASES]
    return {
        "cases": rows,
        "pass_count": sum(1 for r in rows if r["pass"]),
        "total": len(rows),
        "gates": GATES,
    }


def _md(kq: dict) -> str:
    d = ["# CROSS-DOMAIN QUALITY MATRIX — vNext", ""]
    d.append(f"**{kq['pass_count']}/{kq['total']} lớp PASS.** Mỗi lớp đi qua CÙNG "
             "một bộ cổng; không nhánh riêng cho miền nào.\n")
    d.append("| lớp | bài | bước | khung | " + " | ".join(
        g.replace("_", " ").lower() for g in kq["gates"]) + " |")
    d.append("|" + "---|" * (4 + len(kq["gates"])))
    for r in kq["cases"]:
        o = [r["lop"], r["title"][:30], str(r["steps"]), str(r["frames"])]
        o += ["✅" if r["gates"].get(g) else "❌" for g in kq["gates"]]
        d.append("| " + " | ".join(o) + " |")
    d.append("")
    for r in kq["cases"]:
        if r["ghi_chu"]:
            d.append(f"- **{r['lop']}**: " + " · ".join(r["ghi_chu"]))
    return "\n".join(d) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--md")
    a = ap.parse_args()
    kq = run_matrix()
    if a.json:
        Path(a.json).write_text(
            json.dumps(kq, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    if a.md:
        Path(a.md).write_text(_md(kq), encoding="utf-8")
    for r in kq["cases"]:
        xau = [g for g, v in r["gates"].items() if not v]
        print(f"{'PASS' if r['pass'] else 'FAIL'}  {r['lop']:18} {r['title'][:34]:36}"
              + ("" if r["pass"] else "  ← " + ", ".join(xau)))
    print(f"\nCROSS_DOMAIN_OFFLINE = {kq['pass_count']}/{kq['total']}")
    return 0 if kq["pass_count"] == kq["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
