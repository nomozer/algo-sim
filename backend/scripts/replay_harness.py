# -*- coding: utf-8 -*-
"""MULTI-INPUT REPLAY — chạy MỘT chương trình trên NHIỀU đầu vào. **0 API call.**

VÌ SAO TỒN TẠI: tới hôm nay, một `SemanticProgram` chỉ được chạy đúng **một**
lần, trên đúng cái `initial_value` mà LLM viết ra cùng nó. Với một mẫu duy nhất,
*"chương trình tính ra đáp án"* và *"chương trình biết trước đáp án"* cho cùng
một kết quả — và không cổng nào phân biệt được.

RANH GIỚI VỚI THỨ ĐÃ CÓ, đọc trước khi thêm detector:

- `coverage_gate` (C₁b, `3e0d67c`) đã bịt **"gán thẳng đáp án"** bằng kiểm
  **TĨNH**: witness phải có đường phụ thuộc — kể cả qua nhánh — về container đầu
  vào. File này **không** làm lại việc đó.
- Cái tĩnh ấy không với tới được: một chương trình *có* đọc container mà vẫn
  không tính đúng. `ket_qua = a[0]` phụ thuộc `a` hợp lệ về mặt đồ thị, nhưng nó
  không phải `max(a)`. Chỉ có **chạy lại với đầu vào khác** mới lộ.
- `evaluation/metamorphic.py` biến đổi **văn bản đề** để đo độ ổn định của
  classifier. Khác trách nhiệm: ở đây ta giữ nguyên chương trình và đổi **dữ
  liệu**.

BA DETECTOR, đều KHÔNG cần oracle — đó là điểm mấu chốt: chúng chạy được trên
BẤT KỲ chương trình sinh nào mà không cần ai biết đáp án đúng.

    HARD_CODED     witness y hệt nhau qua mọi biến thể
    INPUT_IGNORED  chuỗi hành động y hệt nhau qua mọi biến thể
    DEAD_STATE     một container khai ra nhưng không lượt nào đụng tới

Có oracle thì truyền `oracle=` để so thêm; không có vẫn dùng được.

⚠️ HARD_CODED là **NGHI VẤN, không phải phán quyết**. Một nghĩa vụ có thể hằng
một cách chính đáng (đếm phần tử của một dãy không đổi). Harness **báo**, người
đọc quyết. Biến nó thành fail-closed là đẻ ra false rejection ở chỗ khó cãi.

    python backend/scripts/replay_harness.py --demo
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.simulation.semantic_program.contract import SemanticProgramSpec  # noqa: E402
from app.simulation.semantic_program.interpreter import (  # noqa: E402
    SemanticProgramInterpreter,
)

#: Số biến thể mặc định. 4 chứ không phải 2: với phán quyết nhị phân, hai mẫu
#: còn 25% khả năng trùng nhau do may rủi; bốn mẫu hạ xuống ~6%. Đây là ngưỡng
#: thực dụng, không phải một tuyên bố thống kê.
SO_BIEN_THE = 4


def _bien_the_gia_tri(v: Any) -> list[Any]:
    """Sinh biến thể GIỮ NGUYÊN KIỂU. Đổi kiểu là đổi bài, không phải đổi đầu vào.

    Cố ý gồm cả ca biên (dãy rỗng, chuỗi rỗng, số 0): chúng vừa dò được
    `INPUT_IGNORED`, vừa là phép tiêm lỗi cho tính fail-closed của interpreter.
    """
    if isinstance(v, bool):
        return [not v, v, not v, v]
    if isinstance(v, int):
        return [0, v + 7, -abs(v) - 1, 1]
    if isinstance(v, float):
        return [0.0, v + 1.5, -abs(v) - 0.5, 1.0]
    if isinstance(v, str):
        return ["", v[::-1], v * 2 if v else "x", "Z"]
    if isinstance(v, list):
        if not v:
            return [[], [1], [1, 2], [3]]
        return [list(reversed(v)), v[:1], v + v, []]
    if isinstance(v, dict):
        if not v:
            return [{}, {"k": 1}, {}, {"k": 2}]
        k = next(iter(v))
        return [{}, dict(v), {k: v[k]}, dict(v)]
    return [v, v, v, v]


@dataclass
class LuotChay:
    ten: str
    dau_vao: dict[str, Any]
    loi: str | None = None
    tong_buoc: int = 0
    chu_ky_hanh_dong: tuple = ()
    bo_nho_cuoi: dict[str, Any] = field(default_factory=dict)


@dataclass
class KetQuaReplay:
    so_luot: int
    phat_hien: list[str]
    chi_tiet: dict[str, Any]
    luot: list[LuotChay]

    @property
    def ok(self) -> bool:
        """Chỉ hai detector CHẮC CHẮN mới quyết PASS/FAIL.

        `HARD_CODED` là nghi vấn (xem docstring module) nên không vào đây —
        gộp nó vào là biến một cảnh báo thành lời buộc tội.
        """
        return not any(p.startswith(("INPUT_IGNORED", "DEAD_STATE")) for p in self.phat_hien)


def _chu_ky(trace) -> tuple:
    """Chữ ký hành động của một lượt — `(action, target)` theo thứ tự.

    Cố ý BỎ giá trị: giữ giá trị thì hai lượt luôn khác nhau và
    `INPUT_IGNORED` không bao giờ bắt được gì. Ta hỏi *"chương trình có RẼ
    NHÁNH khác đi không"*, không hỏi *"số có khác không"*.
    """
    return tuple((s.action, s.target) for s in trace)


def _chay_mot(spec: SemanticProgramSpec, ten: str, dau_vao: dict[str, Any]) -> LuotChay:
    ban_sao = spec.model_copy(deep=True)
    for md in ban_sao.memory_declarations:
        if md.name in dau_vao:
            md.initial_value = dau_vao[md.name]
    lc = LuotChay(ten=ten, dau_vao=dau_vao)
    try:
        kq = SemanticProgramInterpreter().execute(ban_sao)
        lc.tong_buoc = len(kq.trace)
        lc.chu_ky_hanh_dong = _chu_ky(kq.trace)
        lc.bo_nho_cuoi = dict(kq.final_memory)
    except Exception as e:  # noqa: BLE001
        # Lỗi ở ĐÂY là dữ liệu, không phải sự cố: một interpreter fail-closed
        # ĐƯỢC PHÉP ném lỗi trên đầu vào biên. Ghi lại rồi đi tiếp.
        lc.loi = f"{type(e).__name__}: {e}"
    return lc


def replay(
    spec: SemanticProgramSpec,
    input_names: list[str],
    witness: str | None = None,
    so_bien_the: int = SO_BIEN_THE,
    oracle: Callable[[dict[str, Any]], Any] | None = None,
) -> KetQuaReplay:
    """Chạy `spec` trên lượt gốc + `so_bien_the` biến thể đầu vào."""
    goc = {
        md.name: md.initial_value
        for md in spec.memory_declarations
        if md.name in input_names
    }
    luot = [_chay_mot(spec, "goc", goc)]

    bang = {ten: _bien_the_gia_tri(goc.get(ten)) for ten in input_names}
    for i in range(so_bien_the):
        luot.append(_chay_mot(spec, f"bt{i + 1}",
                              {ten: bang[ten][i % len(bang[ten])] for ten in input_names}))

    chay_duoc = [l for l in luot if l.loi is None]
    phat_hien: list[str] = []
    chi_tiet: dict[str, Any] = {
        "so_luot_chay_duoc": len(chay_duoc),
        "so_luot_loi": len(luot) - len(chay_duoc),
    }

    # ── INPUT_IGNORED ────────────────────────────────────────────────────
    chu_ky = {l.chu_ky_hanh_dong for l in chay_duoc}
    chi_tiet["so_chu_ky_khac_nhau"] = len(chu_ky)
    if len(chay_duoc) >= 2 and len(chu_ky) == 1:
        phat_hien.append(
            "INPUT_IGNORED: mọi đầu vào cho CÙNG một chuỗi hành động — "
            "chương trình không rẽ nhánh theo dữ liệu"
        )

    # ── DEAD_STATE ───────────────────────────────────────────────────────
    khai = {md.name for md in spec.memory_declarations}
    dung_toi: set[str] = set()
    for lc in chay_duoc:
        dung_toi |= {t for _, t in lc.chu_ky_hanh_dong if t}
    chet = sorted(khai - dung_toi - set(input_names))
    chi_tiet["container_khong_ai_dung"] = chet
    if chet:
        phat_hien.append(
            f"DEAD_STATE: khai {chet} nhưng không lượt nào đụng tới — "
            "trạng thái trang trí, học sinh thấy ô không bao giờ đổi"
        )

    # ── HARD_CODED (nghi vấn) ────────────────────────────────────────────
    if witness:
        gia_tri = [l.bo_nho_cuoi.get(witness) for l in chay_duoc]
        chi_tiet["witness_qua_cac_luot"] = gia_tri
        if len(chay_duoc) >= 3 and len({json.dumps(g, sort_keys=True, default=str)
                                        for g in gia_tri}) == 1:
            phat_hien.append(
                f"HARD_CODED?: witness '{witness}' = {gia_tri[0]!r} ở MỌI đầu vào. "
                "NGHI VẤN, không phải phán quyết — nghĩa vụ có thể hằng chính đáng."
            )

    # ── oracle (tuỳ chọn) ────────────────────────────────────────────────
    if oracle and witness:
        lech = [
            {"luot": l.ten, "dau_vao": l.dau_vao,
             "may": l.bo_nho_cuoi.get(witness), "oracle": oracle(l.dau_vao)}
            for l in chay_duoc
            if l.bo_nho_cuoi.get(witness) != oracle(l.dau_vao)
        ]
        chi_tiet["oracle_lech"] = lech
        if lech:
            phat_hien.append(
                f"ORACLE_MISMATCH: {len(lech)}/{len(chay_duoc)} lượt lệch ground truth"
            )

    return KetQuaReplay(len(luot), phat_hien, chi_tiet, luot)


def _khung(statements: list[dict]) -> dict:
    """Khung chương trình tối thiểu — chỉ `statements` là khác nhau giữa hai ca."""
    return {
        "spec_version": "1.0",
        "title": "Tìm giá trị lớn nhất",
        "description": "Quét dãy, giữ giá trị lớn nhất.",
        "pedagogical_intent": "Thấy biến tích luỹ đổi qua từng bước.",
        "memory_declarations": [
            {"name": "a", "type": "array", "element_type": "int",
             "initial_value": [3, 9, 2]},
            {"name": "m", "type": "int", "initial_value": 0},
        ],
        "statements": statements,
        "visual_bindings": {
            "containers": [{"semantic_id": "a", "primitive": "array_strip", "label": "Dãy"}],
            "pointers": [],
            "value_boxes": [{"box_id": "b", "var_ref": "m", "label": "Lớn nhất"}],
        },
    }


#: TÍNH THẬT — quét dãy, cập nhật `m` khi gặp phần tử lớn hơn.
TIM_MAX = _khung([
    {"kind": "for_each", "item_var": "x", "container_or_expr": "a", "body": [
        {"kind": "if",
         "condition": {"kind": "compare", "op": ">",
                       "left": {"kind": "var", "name": "x"},
                       "right": {"kind": "var", "name": "m"}},
         "then_body": [{"kind": "assign", "target_var": "m",
                        "expr": {"kind": "var", "name": "x"}}],
         "else_body": []},
    ]},
])

#: GÁN CỨNG — đọc `a` cho có (qua `length`) rồi khai thẳng đáp án của dãy gốc.
#: Kiểm TĨNH của C₁b có thể cho qua vì `m` phụ thuộc `a` về mặt đồ thị.
GAN_CUNG = _khung([
    {"kind": "assign", "target_var": "m",
     "expr": {"kind": "arith", "op": "+",
              "left": {"kind": "literal", "value": 9},
              "right": {"kind": "arith", "op": "*",
                        "left": {"kind": "literal", "value": 0},
                        "right": {"kind": "length", "container": "a"}}}},
])


def _demo() -> int:
    """Chạy hai chương trình đối chứng: một cái TÍNH, một cái GÁN CỨNG."""
    for ten, spec_raw, inp, w in (
        ("TÌM MAX (tính thật)", TIM_MAX, ["a"], "m"),
        ("GÁN CỨNG (giả tạo)", GAN_CUNG, ["a"], "m"),
    ):
        r = replay(SemanticProgramSpec.model_validate(spec_raw), inp, witness=w)
        print(f"\n=== {ten} ===")
        print(f"  ok={r.ok} · {r.so_luot} lượt · {json.dumps(r.chi_tiet, ensure_ascii=False)}")
        for p in r.phat_hien:
            print(f"  ⚠ {p}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--demo", action="store_true")
    a = p.parse_args()
    return _demo() if a.demo else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(main())
