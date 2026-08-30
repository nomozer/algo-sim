# -*- coding: utf-8 -*-
"""Sinh BÀI MẪU HÌNH HỌC chạy offline — **0 API call**.

VÌ SAO CẦN: toàn bộ đường *không-cần-AI* của sản phẩm nằm ở `SAMPLES` (17 bài
Tin học). Hình học có **0 bài**, nên mở app mà không có khoá API thì không có
một bài hình học nào để chạy — kể cả để soát giao diện. Đó cũng là lý do
`CLAUDE.md` dặn "task UI/CSS chọn bài mẫu, không cần backend": lối ấy hiện chỉ
tồn tại cho miền đã bị thay.

RANH GIỚI R0 KHÔNG ĐỔI. Chương trình dưới đây do NGƯỜI viết, đúng như
`oracle_result` của tập DEV do người tính tay — nhưng **không một toạ độ kết
quả nào** được viết tay: trung điểm, giao tuyến, thiết diện, thể tích đều do
kernel tính. Người viết *các bước dựng*, engine dựng. Đó chính là việc LLM làm
ở đường sinh, nên bài mẫu và bài sinh ra cho cùng một hình dạng envelope.

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \\
        scripts/build_geometry_samples.py

Ghi ra `frontend/src/data/geometry-samples.json`. Khoá bởi
`frontend/src/data/geometry-samples.test.ts` — sửa chương trình mà quên chạy
lại script là ĐỎ.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

RA = ROOT / "frontend" / "src" / "data" / "geometry-samples.json"


def _diem(ten: str, xyz: list[int | str]) -> dict[str, Any]:
    return {"name": ten, "type": "point3", "initial_value": xyz,
            "model_assumption": "hệ trục do đề chọn"}


def _khai(ten: str, kieu: str) -> dict[str, Any]:
    return {"name": ten, "type": kieu}


#: Đáy vuông cạnh 2 trong `z = 0`, đỉnh S trên trục z — quy ước hình của tập
#: DEV (`hinh_quy_uoc`). Giữ cùng quy ước để bài mẫu và bài đo nói cùng thứ.
DAY = {"A": [0, 0, 0], "B": [2, 0, 0], "C": [2, 2, 0], "D": [0, 2, 0]}
MAT_CHOP = [["A", "B", "C", "D"], ["A", "B", "S"], ["B", "C", "S"],
            ["C", "D", "S"], ["D", "A", "S"]]


def chuong_trinh_thiet_dien() -> dict[str, Any]:
    """Thiết diện song song đáy — dạng bài tần suất cao nhất của chương này."""
    return {
        "spec_version": "1.0",
        "title": "Thiết diện của hình chóp cắt bởi mặt phẳng qua ba trung điểm",
        "description": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
            "góc với mặt phẳng đáy và SA = 4. Gọi M, N, P lần lượt là trung "
            "điểm của SA, SB, SC. Hãy dựng thiết diện của hình chóp khi cắt "
            "bởi mặt phẳng (MNP)."
        ),
        "memory_declarations": [
            *[_diem(n, v) for n, v in DAY.items()],
            _diem("S", [0, 0, 4]),
            _khai("M", "point3"), _khai("N", "point3"), _khai("P", "point3"),
            _khai("chop", "solid"), _khai("mp", "plane3"),
            _khai("thiet_dien", "section"),
        ],
        "statements": [
            {"kind": "construct_solid", "target_var": "chop", "label": "S.ABCD",
             "vertices": ["A", "B", "C", "D", "S"], "faces": MAT_CHOP},
            {"kind": "construct_point", "target_var": "M", "label": "M",
             "expr": {"kind": "midpoint", "a": "S", "b": "A"}},
            {"kind": "construct_point", "target_var": "N", "label": "N",
             "expr": {"kind": "midpoint", "a": "S", "b": "B"}},
            {"kind": "construct_point", "target_var": "P", "label": "P",
             "expr": {"kind": "midpoint", "a": "S", "b": "C"}},
            {"kind": "construct_plane", "target_var": "mp", "label": "(MNP)",
             "through": ["M", "N", "P"]},
            {"kind": "construct_section", "target_var": "thiet_dien",
             "label": "thiết diện", "solid": "chop", "plane": "mp"},
        ],
        "visual_bindings": {},
    }


def chuong_trinh_vuong_goc() -> dict[str, Any]:
    """Quan hệ vuông góc — trả `sin² = 1`, tức BC ⊥ (SAB)."""
    return {
        "spec_version": "1.0",
        "title": "Đường thẳng vuông góc với mặt phẳng trong hình chóp",
        "description": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
            "góc với mặt phẳng đáy và SA = 4. Xét đường thẳng BC và mặt phẳng "
            "(SAB): hãy dựng hình rồi cho biết góc giữa chúng."
        ),
        "memory_declarations": [
            *[_diem(n, v) for n, v in DAY.items()],
            _diem("S", [0, 0, 4]),
            _khai("chop", "solid"), _khai("sab", "plane3"),
            _khai("bc", "line3"), _khai("goc", "float"),
        ],
        "statements": [
            {"kind": "construct_solid", "target_var": "chop", "label": "S.ABCD",
             "vertices": ["A", "B", "C", "D", "S"], "faces": MAT_CHOP},
            {"kind": "construct_plane", "target_var": "sab", "label": "(SAB)",
             "through": ["S", "A", "B"]},
            {"kind": "construct_line", "target_var": "bc", "label": "BC",
             "through_a": "B", "through_b": "C"},
            {"kind": "assign", "target_var": "goc",
             "expr": {"kind": "measure", "quantity": "angle_cos_sq",
                      "of": "bc", "wrt": "sab"}},
        ],
        "visual_bindings": {},
    }


def chuong_trinh_the_tich() -> dict[str, Any]:
    """Thể tích + khoảng cách — hai đại lượng, cùng một hình."""
    return {
        "spec_version": "1.0",
        "title": "Thể tích khối chóp và khoảng cách từ đỉnh đến đáy",
        "description": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông "
            "góc với mặt phẳng đáy và SA = 4. Tính thể tích khối chóp và "
            "khoảng cách từ S đến mặt phẳng đáy."
        ),
        "memory_declarations": [
            *[_diem(n, v) for n, v in DAY.items()],
            _diem("S", [0, 0, 4]),
            _khai("chop", "solid"), _khai("day", "plane3"),
            _khai("V", "float"), _khai("d", "float"),
        ],
        "statements": [
            {"kind": "construct_solid", "target_var": "chop", "label": "S.ABCD",
             "vertices": ["A", "B", "C", "D", "S"], "faces": MAT_CHOP},
            {"kind": "construct_plane", "target_var": "day", "label": "(ABCD)",
             "through": ["A", "B", "C"]},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}},
            {"kind": "assign", "target_var": "d",
             "expr": {"kind": "measure", "quantity": "distance",
                      "of": "S", "wrt": "day"}},
        ],
        "visual_bindings": {},
    }


#: `id` là khoá ỔN ĐỊNH của bài mẫu — nó đi vào URL và vào lịch sử học, nên
#: đổi nó là làm mất tiến độ của học sinh. Thêm bài thì thêm khoá mới.
BAI_MAU = [
    ("thiet-dien-chop", "Dựng hình · thiết diện", chuong_trinh_thiet_dien),
    ("vuong-goc-chop", "Quan hệ song song – vuông góc", chuong_trinh_vuong_goc),
    ("the-tich-chop", "Khoảng cách · thể tích · góc", chuong_trinh_the_tich),
]


def main() -> int:
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.interpreter import (
        SemanticProgramInterpreter,
    )
    from app.simulation.semantic_program.pipeline_adapter import (
        compile_semantic_program_to_envelope,
    )
    from app.simulation.semantic_program.scene3d import build_scene3d
    from app.simulation.semantic_program.simulation_state import (
        build_simulation_state,
    )

    ra: list[dict[str, Any]] = []
    for ma, nhom, dung in BAI_MAU:
        spec = SemanticProgramSpec.model_validate(dung())
        env = compile_semantic_program_to_envelope(spec)
        # Cảnh 3D dựng đúng đường sản phẩm dựng (`pipeline._dung_scene3d`):
        # interpreter → simulation_state → scene3d. Không có đường tắt nào ở
        # đây, nếu không bài mẫu sẽ khác bài sinh ra ở một chỗ không ai ngờ.
        ket = SemanticProgramInterpreter().execute(spec)
        # `limit_reached` = cắt giữa chừng. Một bài mẫu cắt giữa chừng là bài
        # mẫu dạy sai, nên DỪNG chứ không ghi ra.
        if ket.status != "completed":
            print(f"DỪNG: {ma} không chạy trọn — {ket.status}", file=sys.stderr)
            return 2
        canh = build_scene3d(build_simulation_state(spec, ket))
        if not canh["objects"]:
            print(f"DỪNG: {ma} không dựng ra cảnh 3D nào", file=sys.stderr)
            return 2
        env["scene3d"] = canh
        # Cùng một luật với `pipeline._envelope_tu_route_sinh`: có cảnh 3D ⇒
        # envelope khai miền HÌNH HỌC. Lặp lại ở đây chứ không gọi lại hàm kia
        # vì hàm kia nhận `SemanticRouteOutcome` của đường LLM; nhưng nếu hai
        # chỗ lệch nhau thì bài mẫu hiện nhãn khác bài sinh ra —
        # `geometry-samples.test.ts` khoá cho chúng không lệch.
        env["domain"] = "geometry"
        env["source"] = "geometry_sample"
        ra.append({"id": ma, "group": nhom,
                   "problemText": spec.description or spec.title,
                   "envelope": env})
        so_do = sum(1 for o in canh["objects"] if o["type"] == "quantity")
        print(f"  {ma:20} {len(canh['objects']):3} vật · "
              f"{len(env['config']['frames']):3} khung · {so_do} số đo")

    RA.parent.mkdir(parents=True, exist_ok=True)
    RA.write_text(
        json.dumps({
            "khai": ("Bài mẫu hình học SINH RA, không viết tay. Sửa "
                     "`backend/scripts/build_geometry_samples.py` rồi chạy lại; "
                     "sửa thẳng file này sẽ bị ghi đè."),
            "samples": ra,
        }, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n")
    print(f"\n→ {RA.relative_to(ROOT)} · {len(ra)} bài")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
