# -*- coding: utf-8 -*-
"""Sáu biên từng gây lỗi NẶNG — có ca nào còn ném ra ngoài không? **0 API call.**

`THESIS_SCOPE_FREEZE_AND_DEMO_READINESS §8`. Câu hỏi hẹp và đúng một câu:

    trên luồng demo, có đầu vào xấu nào làm hệ CHẾT thay vì TỪ CHỐI không?

"Từ chối" = một kết quả có kiểu, mang mã lỗi, đọc được. "Chết" = một exception
đi xuyên qua mọi tầng, tức một 500 nếu nó xảy ra sau HTTP.

⚠️ **KHÔNG phải fuzzing.** Sáu ca dưới đây là sáu biên ĐÃ từng hỏng thật trong
kho này, mỗi ca kèm nơi nó hỏng. Thêm ca thứ bảy chỉ vì "cho chắc" là mở một
bề mặt kiểm thử mới, và §8 cấm.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.simulation.semantic_program.interpreter import (  # noqa: E402
    SemanticProgramInterpreter,
)
from app.simulation.semantic_program.ir_static_check import kiem_tinh  # noqa: E402
from app.simulation.semantic_program.pipeline_adapter import (  # noqa: E402
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.transport import (  # noqa: E402
    check_envelope_transport,
)
from app.simulation.semantic_program.validator import (  # noqa: E402
    validate_semantic_program,
)


def _khung(stmts, khai=None):
    return {"title": "Ca soát biên", "memory_declarations": khai or [
        {"name": "A", "type": "point3", "initial_value": [0, 0, 0]},
        {"name": "B", "type": "point3", "initial_value": [2, 0, 0]},
        {"name": "C", "type": "point3", "initial_value": [0, 2, 0]}],
        "statements": stmts}


#: `(tên biên, chương trình xấu, tầng PHẢI chặn nó, vì sao biên này có mặt)`
CA = [
    ("toạ độ ký hiệu tới kernel",
     _khung([{"kind": "construct_point", "target_var": "M",
              "expr": {"kind": "midpoint", "a": "A", "b": "B"}}],
            [{"name": "A", "type": "point3",
              "initial_value": [{"kind": "var", "name": "a"}, 0, 0]},
             {"name": "B", "type": "point3", "initial_value": [2, 0, 0]}]),
     "STATIC",
     "lộ ra khi chạy lại lịch sử 2026-09-01: `at: list[Any]` nhận một cạnh KÝ "
     "HIỆU, kernel ném `ZERO_VECTOR` ở runtime nơi vòng sửa không với tới"),

    # ⚠️ `d` PHẢI được khai. Bản đầu của ca này không khai, nên nó bị chặn vì
    # *"tên chưa khai"* chứ không vì *"sai kiểu"* — tức nó xanh mà không kiểm
    # thứ nó nói mình kiểm. Lỗi của bộ đo, không của hệ.
    ("toán hạng SAI KIỂU tới kernel",
     _khung([{"kind": "construct_line", "target_var": "d",
              "through_a": "A", "through_b": "B"},
             {"kind": "assign", "target_var": "x",
              "expr": {"kind": "measure", "quantity": "angle_cos",
                       "of": "d", "wrt": "d"}}],
            [{"name": "A", "type": "point3", "initial_value": [0, 0, 0]},
             {"name": "B", "type": "point3", "initial_value": [2, 0, 0]},
             {"name": "C", "type": "point3", "initial_value": [0, 2, 0]},
             {"name": "d", "type": "line3"},
             {"name": "x", "type": "float"}]),
     "SCHEMA",
     "`angle_cos` đòi `vector3`; `line3` vô hướng nên không cho được dấu. Hai "
     "chương trình lịch sử chết đúng đây. Chặn ở SCHEMA vì `validator` là một "
     "trong bốn người đọc `measure_contract.BANG_PHEP_DO` — sớm hơn một tầng "
     "so với thẩm định tĩnh, và sớm hơn thì tốt hơn"),

    ("ràng buộc LẦN ĐẦU không khai",
     _khung([{"kind": "assign", "target_var": "M",
              "expr": {"kind": "midpoint", "a": "A", "b": "B"}},
             {"kind": "construct_line", "target_var": "d",
              "through_a": "M", "through_b": "C"}]),
     "OK_SAU_CHUAN_HOA",
     "giết 4/6 ca của CLEAN_BASELINE_V1; nay `_rang_buoc_lan_dau` đưa về dạng "
     "chuẩn tắc nên nó phải CHẠY ĐƯỢC, không phải bị từ chối"),

    ("ràng buộc lần đầu TRONG NHÁNH",
     _khung([{"kind": "if",
              "condition": {"kind": "compare", "op": "==",
                            "left": {"kind": "literal", "value": 1},
                            "right": {"kind": "literal", "value": 1}},
              "then_body": [{"kind": "assign", "target_var": "M",
                             "expr": {"kind": "midpoint", "a": "A", "b": "B"}}]},
             {"kind": "construct_line", "target_var": "d",
              "through_a": "M", "through_b": "C"}]),
     "STATIC",
     "nâng nó ra scope ngoài là để `None` tới kernel khi nhánh không chạy — "
     "món nợ `CONTROL_FLOW_DEFINITE_ASSIGNMENT`, cố ý không nới"),

    ("toạ độ THÔ ở một ô TÊN",
     _khung([{"kind": "construct_point", "target_var": "Q",
              "expr": {"kind": "translate", "point": "A",
                       "vector": [1, 2, 3]}}]),
     "SCHEMA",
     "R0: nhận cấu trúc ở ô toán hạng là mở đường cho toạ độ đi thẳng từ LLM "
     "vào bộ nhớ hình học"),

    ("rửa năng lực qua biểu thức lồng",
     _khung([{"kind": "construct_point", "target_var": "Q",
              "expr": {"kind": "translate", "point": "A",
                       "vector": {"kind": "vector_from_points",
                                  "from_point": "B", "to_point": "C",
                                  "model_assumption": "lấy BC = 3 cho gọn"}}}]),
     "SCHEMA",
     "một giả định mô hình tự đặt phải khai ở điểm gốc nơi `grounding_gate` "
     "hỏi nó; chở lậu trong biểu thức lồng rồi để phép nâng hợp thức hoá là "
     "đúng định nghĩa rửa năng lực"),
]


def _chay(spec: dict) -> tuple[str, str]:
    """`(tầng chặn, thông điệp)` — hoặc ném, và ném chính là thứ đang tìm."""
    v = validate_semantic_program(spec)
    if not v.ok:
        return "SCHEMA", (v.error or "")[:120]
    t = kiem_tinh(v.spec)
    if not t.ok:
        return "STATIC", t.phan_hoi()[:120]
    kq = SemanticProgramInterpreter().execute(v.spec)
    tr = check_envelope_transport(compile_semantic_program_to_envelope(v.spec))
    if tr is not None:
        return "TRANSPORT", str(tr)[:120]
    return "OK_SAU_CHUAN_HOA", f"chạy được, {kq.total_steps} bước"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    ra = []
    for ten, spec, mong, vi_sao in CA:
        try:
            tang, tin = _chay(spec)
            nem = None
        except Exception as e:  # noqa: BLE001
            tang, tin, nem = "NEM_RA_NGOAI", f"{type(e).__name__}: {e}"[:160], True
        ra.append({"bien": ten, "mong_doi": mong, "thuc_te": tang,
                   "khop": tang == mong, "nem": bool(nem), "tin": tin,
                   "vi_sao": vi_sao})

    if ns.json:
        print(json.dumps(ra, ensure_ascii=False, indent=2))
    else:
        for x in ra:
            print(f"{'✔' if x['khop'] else '✘'} {x['bien'][:36]:36s} "
                  f"mong={x['mong_doi']:18s} thực={x['thuc_te']}")
            print(f"    {x['tin']}")
        n = sum(1 for x in ra if x["khop"])
        nem = sum(1 for x in ra if x["nem"])
        print(f"\n  BIÊN ĐÚNG KỲ VỌNG      {n}/{len(ra)}")
        print(f"  NÉM RA NGOÀI (=500)    {nem}")
    return 0 if all(x["khop"] for x in ra) else 1


if __name__ == "__main__":
    raise SystemExit(main())
