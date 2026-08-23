# -*- coding: utf-8 -*-
"""`map_view` — primitive thị giác cho `MemoryType` đã được admit (2026-08-23).

VÌ SAO NÓ ĐƯỢC THÊM, và vì sao đó KHÔNG phải "cứu fixture #18":
`map` là một `MemoryType` hệ thống đã thừa nhận từ lâu — `MapGetExpr`,
`MapSetStmt`, `key_type`/`val_type` đều đã có. Nhưng hợp đồng THỊ GIÁC không có
cách nào biểu diễn nó, nên **cả một lớp bài** mà ĐÁP ÁN là một bảng — đếm tần
suất, gom nhóm, dựng bảng tra — chạy được mà không xem được. Cổng
`learner_surface` chụp được hậu quả trên fixture #18: chương trình dựng bảng tần
suất suốt lượt chạy, màn hình hiện chuỗi vào và một số đếm, còn bảng thì không
bao giờ xuất hiện.

Đó là khoảng trống của HỢP ĐỒNG, không phải nhu cầu của một bài — cùng khuôn và
cùng tiền lệ với `graph_view` (2026-08-21). Nguồn phát hiện: DEV.

RANH GIỚI v1: đọc thẳng từ `memory_snapshot` · thứ tự trình bày TẤT ĐỊNH theo
khoá · KHÔNG sắp theo giá trị · KHÔNG gộp/lọc · KHÔNG thêm statement kind,
MemoryType hay checker nào.
"""
import typing

import pytest

from app.simulation.semantic_program.contract import VisualContainerBinding
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.pipeline_adapter import (
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.visual_adapter import VisualTraceAdapter

from .fixtures_coverage_18 import ALL_18_COVERAGE_FIXTURES

P18_FREQUENCY = ALL_18_COVERAGE_FIXTURES[17]


def _map_qua_cac_khung(spec, oid: str = "freq"):
    exec_res = SemanticProgramInterpreter(max_steps=300).execute(spec)
    frames = VisualTraceAdapter(spec).adapt(exec_res)
    return [
        next(o for o in f.objects if o.get("id") == oid)["entries"] for f in frames
    ]


# ── Hợp đồng: sáu nơi phải đồng bộ ─────────────────────────────────────────


def test_map_view_co_trong_enum_va_co_nhanh_adapter():
    """Bất biến #33, hai chiều — thiếu một vế là object rỗng, lỗi CÂM."""
    trong_enum = set(
        typing.get_args(VisualContainerBinding.model_fields["primitive"].annotation)
    )
    assert "map_view" in trong_enum
    assert "map_view" in VisualTraceAdapter.HANDLED_PRIMITIVES


def test_schema_mirror_hai_ban_deu_co_map_view():
    """`export_semantic_program_schema.py` ghi HAI bản; quên chạy là lệch."""
    import json
    from pathlib import Path

    goc = Path(__file__).resolve().parents[3]
    ban = [
        goc / "docs/schemas/semantic_program.schema.json",
        goc / "frontend/src/simulations/domains/generic/semantic_program.schema.json",
    ]
    noi_dung = [p.read_text(encoding="utf-8") for p in ban]
    assert noi_dung[0] == noi_dung[1], "hai bản schema lệch nhau"
    assert "map_view" in json.dumps(json.loads(noi_dung[0]), ensure_ascii=False)


# ── Ngữ nghĩa: bảng phải dựng dần và TẤT ĐỊNH ──────────────────────────────


def test_bang_rong_that_van_la_bang_rong():
    """`{}` ⇒ không mục nào. KHÔNG dựng mục giả để hình đỡ trống."""
    assert _map_qua_cac_khung(P18_FREQUENCY)[0] == []


def test_bang_dung_dan_qua_cac_khung():
    day = _map_qua_cac_khung(P18_FREQUENCY)
    assert day[-1] == [["a", 3], ["b", 2], ["c", 1]]
    # Phải ĐỔI, không đứng yên — đây là triệu chứng gốc của cả wave.
    assert len({repr(x) for x in day}) > 1


def test_thu_tu_TAT_DINH_theo_khoa_khong_theo_thu_tu_chen():
    """Hai lượt chạy cùng một bài phải cho CÙNG một hình.

    Thứ tự chèn phụ thuộc dữ liệu vào, nên nếu adapter giữ nguyên thứ tự chèn
    thì hai lần chụp cùng bài cho hai hình khác nhau và ảnh chụp hết so được với
    nhau. Cùng luật đã áp cho `nodes`/`edges` của `graph_view`.
    """
    a = _map_qua_cac_khung(P18_FREQUENCY)
    b = _map_qua_cac_khung(P18_FREQUENCY)
    assert a == b
    for khung in a:
        khoa = [k for k, _ in khung]
        assert khoa == sorted(khoa), f"thứ tự khoá không tất định: {khoa}"


def test_map_view_di_het_duong_toi_envelope():
    env = compile_semantic_program_to_envelope(P18_FREQUENCY)
    objs = [
        o
        for f in env["config"]["frames"]
        for o in f["objects"]
        if o.get("type") == "map_view"
    ]
    assert objs, "map_view không tới được envelope"
    assert all("entries" in o for o in objs)


# ── Tiêm lỗi: hình LỆCH bộ nhớ phải bị bắt ─────────────────────────────────


def test_hinh_lech_snapshot_cua_interpreter_thi_DO():
    """Khung nào cũng phải BẰNG bộ nhớ tại đúng bước đó, không phải 'gần giống'.

    Đây là bất biến bắc qua hai tầng — thứ duy nhất phát hiện được 'engine chạy
    một đằng, màn hình vẽ một nẻo'.
    """
    exec_res = SemanticProgramInterpreter(max_steps=300).execute(P18_FREQUENCY)
    frames = VisualTraceAdapter(P18_FREQUENCY).adapt(exec_res)

    def hinh(f):
        return next(o for o in f.objects if o.get("id") == "freq")["entries"]

    def bo_nho(step):
        d = step.memory_snapshot.get("freq") or {}
        return [[str(k), d[k]] for k in sorted(d, key=str)]

    for f, step in zip(frames, exec_res.trace):
        assert hinh(f) == bo_nho(step), f"khung {f.step_index} lệch bộ nhớ"

    # …và guard phải ĐỎ ĐƯỢC: sửa một khung rồi đòi nó vẫn khớp.
    hong = frames[-1].model_copy(deep=True)
    next(o for o in hong.objects if o["id"] == "freq")["entries"] = [["z", 99]]
    assert hinh(hong) != bo_nho(exec_res.trace[-1])


@pytest.mark.parametrize("gia_tri", [0, ""])
def test_gia_tri_rong_THAT_trong_bang_khong_bi_nuot(gia_tri):
    """Đếm được 0 lần là một kết quả, không phải 'chưa có dữ liệu'."""
    from app.simulation.semantic_program.learner_surface import _ro_ri

    env = {
        "config": {
            "frames": [
                {
                    "step_index": 0,
                    "narration": "x",
                    "objects": [
                        {"id": "m", "type": "map_view", "entries": [["a", gia_tri]]}
                    ],
                }
            ]
        }
    }
    assert _ro_ri(env) == []
