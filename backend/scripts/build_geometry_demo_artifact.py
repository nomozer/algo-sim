# -*- coding: utf-8 -*-
"""Sinh DEMO ARTIFACT của miền hình học từ một lượt đo đã chạy. **0 API call.**

    python scripts/build_geometry_demo_artifact.py \
        --from ../docs/evaluation/geometry/dev-results-w4 \
        --out  ../docs/evaluation/geometry/demo

VÌ SAO ĐỌC LẠI ARTIFACT THAY VÌ CHẠY MỚI: câu hỏi của Phase 5G là *"AI có sinh
được quá trình hình thành hình học không"*, và câu ấy chỉ trả lời được bằng thứ
**AI thật sự đã viết**. Lượt `8b4025e` đã lưu nguyên IR; chạy lại chỉ tốn quota
để lấy một bộ IR khác, rồi phải chọn giữa hai bộ — mà chọn bộ nào cũng là
cherry-pick.

Script này KHÔNG chấm lại và KHÔNG sửa gì: nó ghép `scene3d` vào bên cạnh dữ
liệu đã có, để một người đọc thấy trọn chuỗi trong một file.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

#: Năm loại bài mà Phase 5G yêu cầu phủ → case DEV tương ứng.
#:
#: Ánh xạ sang tập DEV có sẵn thay vì dựng bộ mới: `oracle_result` của nó đã
#: tính TAY, đã đóng băng, đã dùng qua ba lượt đo. Bộ mới nghĩa là năm đáp án
#: tính tay mới — một nguồn sai mới cho một câu hỏi đã có dữ liệu.
NAM_LOAI = {
    "geo_01": "midpoint / điểm thuộc mặt phẳng",
    "geo_05": "perpendicular / đường ⊥ mặt",
    "geo_03": "plane & section / thiết diện",
    "geo_09": "solid construction / dựng khối",
    "geo_07": "measurement / khoảng cách",
}


def _canh(gp: dict) -> dict | None:
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.interpreter import (
        SemanticProgramInterpreter,
    )
    from app.simulation.semantic_program.scene3d import build_scene3d
    from app.simulation.semantic_program.simulation_state import (
        build_simulation_state,
    )

    try:
        spec = SemanticProgramSpec.model_validate(gp)
        return build_scene3d(
            build_simulation_state(spec, SemanticProgramInterpreter().execute(spec)))
    except Exception as e:  # noqa: BLE001 — bài trượt thì KHÔNG có cảnh, đúng vậy
        return {"loi": f"{type(e).__name__}: {e}"[:200]}


def _phan_loai(c: dict) -> str:
    """MODEL · CONTRACT · VALIDATOR · INTERPRETER — TASK 3.

    Phân loại theo **tầng chặn**, không theo cảm tính. Ranh giới then chốt:
    `input_not_grounded` có thể là CẢ HAI — mô hình khai đáp án (MODEL) hoặc
    hợp đồng đòi thứ đề không cho (CONTRACT) — nên nó đọc `failure_details`
    thay vì đoán từ mã lỗi.
    """
    if c["executable"]:
        return "PASS"
    ma = c.get("failure_code") or ""
    ct = " ".join(c.get("failure_details") or [])
    if ma == "semantic_program_invalid":
        ly = str(c.get("failure_reason") or "")
        # ─── PHÂN BIỆT HAI THỨ RẤT DỄ GỘP NHẦM ────────────────────────────
        #
        # "IR trượt schema" KHÔNG tự động là lỗi mô hình. Ở lượt W4, **3/4 ca
        # trượt schema là CÙNG MỘT lỗi**: `construct_solid.faces` nhận tên đỉnh
        # thay vì chỉ số. `faces: list[list[int]]` là mã hoá thân thiện với máy
        # và thù địch với người, và mô hình vừa được dặn *"giữ nguyên ký hiệu
        # điểm"* — nên đó là lỗi HỢP ĐỒNG, và Phase 5A đã vá nó.
        #
        # Gộp cả bốn thành "MODEL" sẽ đọc thành *"AI viết sai IR 4 lần"*, trong
        # khi sự thật là *"hợp đồng có một trường khó dùng, và nó cắn 3 lần"*.
        # Hai câu ấy dẫn tới hai wave sửa hoàn toàn khác nhau.
        if "faces" in ly and "valid integer" in ly:
            return "CONTRACT (faces bằng tên đỉnh — đã vá ở 5A)"
        return "MODEL (hình dạng IR)"
    if ma == "input_not_grounded":
        if "MODEL_ASSUMPTION_IS_ANSWER" in ct or "thiếu source_fact_id" in ct:
            return "MODEL (khai đáp án)"
        return "CONTRACT (grounding)"
    if ma == "requested_operation_uncovered":
        return "CONTRACT (danh xưng/phủ nghĩa vụ)"
    if c.get("stage_reached") == "execution":
        return "INTERPRETER"
    return f"KHÁC ({ma})"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from", dest="nguon", required=True)
    p.add_argument("--out", dest="ra", required=True)
    a = p.parse_args()

    goc = json.loads(
        (Path(a.nguon) / "geometry_dev_results.json").read_text(encoding="utf-8"))
    cases = []
    for c in goc["cases"]:
        sc = _canh(c["generated_program"]) if c.get("generated_program") else None
        cases.append({
            "case_id": c["case_id"],
            "loai_dai_dien": NAM_LOAI.get(c["case_id"]),
            "input_text": c["problem"],
            "semantic_program": c.get("generated_program"),
            "validation": {
                "G1_schema": c["schema_pass"],
                "G2_semantic": c["semantic_pass"],
                "executable": c["executable"],
                "stage_reached": c.get("stage_reached"),
                "failure_code": c.get("failure_code"),
                "failure_details": c.get("failure_details", []),
                "phan_loai_that_bai": _phan_loai(c),
            },
            "simulation_steps": (sc or {}).get("events", []),
            "scene3d_objects": (sc or {}).get("objects", []),
            "oracle_result": c.get("oracle"),
            "obligation_match": c.get("obligation_match"),
        })

    ra = Path(a.ra)
    ra.mkdir(parents=True, exist_ok=True)
    (ra / "geometry_demo.json").write_text(
        json.dumps({
            "khai": "Dẫn xuất từ artifact lượt đo đã chạy — KHÔNG chấm lại, "
                    "KHÔNG sửa gì. Tập DEV, không phải benchmark.",
            "nguon": str(Path(a.nguon).name),
            "neo": goc["tom_tat"].get("neo"),
            "tom_tat": {k: goc["tom_tat"][k] for k in
                        ("G1_schema", "G2_semantic", "A_executable", "O_oracle",
                         "obligation_match", "model")},
            "cases": cases,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    print(f"Đã ghi {ra / 'geometry_demo.json'}")
    print(f"  {len(cases)} case · {sum(1 for c in cases if c['validation']['executable'])} đi trọn đường")
    for c in cases:
        print(f"   {c['case_id']:8} {c['validation']['phan_loai_that_bai']:32}"
              f" {len(c['scene3d_objects'])} đối tượng"
              f" · {len(c['simulation_steps'])} bước")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
