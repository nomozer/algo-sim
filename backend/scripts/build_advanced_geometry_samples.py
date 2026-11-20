# -*- coding: utf-8 -*-
"""Sinh 11 bài mẫu Hình học không gian THPT nâng cao cho Thư viện Axo.

Mọi bài mẫu đều đi qua đúng một đường thực thi tất định của nhân:

    SemanticProgramSpec
      → hoan_thien_dung_hinh (formation.py)
      → compile_semantic_program_to_envelope (pipeline_adapter.py)
      → SemanticProgramInterpreter (exact Fraction / Radical kernel)
      → build_simulation_state (prefer_declared_plane_names=True, common_perpendicular_witness=True)
      → build_scene3d

Script đồng thời thực hiện kiểm chứng toán học độc lập bằng nhân `geometry.kernel`
và `geometry.measure` cho từng bài trước khi xuất `frontend/src/data/advanced-geometry-samples.json`.
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.simulation.geometry import (  # noqa: E402
    Vec3,
    circumscribed_sphere,
    kernel as K,
    metric as _m,
)
from app.simulation.semantic_program.contract import SemanticProgramSpec  # noqa: E402
from app.simulation.semantic_program.formation import hoan_thien_dung_hinh  # noqa: E402
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter  # noqa: E402
from app.simulation.semantic_program.obligations import Obligation  # noqa: E402
from app.simulation.semantic_program.pipeline_adapter import (  # noqa: E402
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.request_contract import (  # noqa: E402
    InputFact,
    PrismTopologySpec,
    PyramidTopologySpec,
    RequestContract,
)
from app.simulation.semantic_program.scene3d import build_scene3d  # noqa: E402
from app.simulation.semantic_program.simulation_state import build_simulation_state  # noqa: E402
from app.simulation.semantic_program.structured_relations import GeometricRelation  # noqa: E402

RA = REPO_DIR / "frontend" / "src" / "data" / "advanced-geometry-samples.json"


def _diem(ten: str, xyz: list[int | str]) -> dict[str, Any]:
    return {
        "name": ten,
        "type": "point3",
        "initial_value": xyz,
        "model_assumption": "hệ trục do đề chọn",
    }


def _khai(ten: str, kieu: str) -> dict[str, Any]:
    return {"name": ten, "type": kieu}


def _do(ten: str, q: str, of: str, wrt: str | None = None, label: str | None = None) -> dict[str, Any]:
    e: dict[str, Any] = {"kind": "measure", "quantity": q, "of": of}
    if wrt:
        e["wrt"] = wrt
    st: dict[str, Any] = {"kind": "assign", "target_var": ten, "expr": e}
    if label:
        st["label"] = label
    return st


# ── Bài 1. Thiết diện hình chóp bởi mặt phẳng qua ba điểm ─────────────────────
def bai_1_chop_thiet_dien_ba_diem() -> tuple[dict[str, Any], RequestContract]:
    desc = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông tâm O cạnh bằng 4, cạnh bên SA "
        "vuông góc với mặt phẳng đáy (ABCD) và SA = 6. Gọi M là trung điểm của cạnh SA, "
        "N là trung điểm của cạnh BC và P là trung điểm của cạnh CD. Mặt phẳng (MNP) cắt "
        "cạnh SB tại E và cắt cạnh SD tại F. Xác định các giao tuyến của mặt phẳng (MNP) "
        "với các mặt của hình chóp, dựng thiết diện ngũ giác MENPF và tính diện tích thiết diện."
    )
    spec = {
        "spec_version": "1.0",
        "title": "Thiết diện hình chóp S.ABCD cắt bởi mặt phẳng (MNP)",
        "description": desc,
        "memory_declarations": [
            _diem("A", [0, 0, 0]),
            _diem("B", [4, 0, 0]),
            _diem("C", [4, 4, 0]),
            _diem("D", [0, 4, 0]),
            _diem("S", [0, 0, 6]),
            _khai("O", "point3"),
            _khai("M", "point3"),
            _khai("N", "point3"),
            _khai("P", "point3"),
            _khai("E", "point3"),
            _khai("F", "point3"),
            _khai("chop", "solid"),
            _khai("day", "plane3"),
            _khai("mp_MNP", "plane3"),
            _khai("sb", "line3"),
            _khai("sd", "line3"),
            _khai("thiet_dien", "section"),
            _khai("S_td", "float"),
            _khai("V_chop", "float"),
        ],
        "statements": [
            {
                "kind": "construct_solid",
                "target_var": "chop",
                "label": "S.ABCD",
                "vertices": ["A", "B", "C", "D", "S"],
                "faces": [
                    ["A", "B", "C", "D"],
                    ["A", "B", "S"],
                    ["B", "C", "S"],
                    ["C", "D", "S"],
                    ["D", "A", "S"],
                ],
            },
            {"kind": "construct_plane", "target_var": "day", "label": "(ABCD)", "through": ["A", "B", "C"]},
            {
                "kind": "construct_point",
                "target_var": "O",
                "label": "O",
                "expr": {"kind": "midpoint", "a": "A", "b": "C"},
            },
            {
                "kind": "construct_point",
                "target_var": "M",
                "label": "M",
                "expr": {"kind": "midpoint", "a": "S", "b": "A"},
            },
            {
                "kind": "construct_point",
                "target_var": "N",
                "label": "N",
                "expr": {"kind": "midpoint", "a": "B", "b": "C"},
            },
            {
                "kind": "construct_point",
                "target_var": "P",
                "label": "P",
                "expr": {"kind": "midpoint", "a": "C", "b": "D"},
            },
            {"kind": "construct_plane", "target_var": "mp_MNP", "label": "(MNP)", "through": ["M", "N", "P"]},
            {"kind": "construct_line", "target_var": "sb", "label": "SB", "through_a": "S", "through_b": "B"},
            {"kind": "construct_line", "target_var": "sd", "label": "SD", "through_a": "S", "through_b": "D"},
            {
                "kind": "construct_point",
                "target_var": "E",
                "label": "E",
                "expr": {"kind": "intersect_line_plane", "line": "sb", "plane": "mp_MNP"},
            },
            {
                "kind": "construct_point",
                "target_var": "F",
                "label": "F",
                "expr": {"kind": "intersect_line_plane", "line": "sd", "plane": "mp_MNP"},
            },
            {
                "kind": "construct_section",
                "target_var": "thiet_dien",
                "label": "Thiết diện MENPF",
                "solid": "chop",
                "plane": "mp_MNP",
            },
            _do("S_td", "area", "thiet_dien"),
            _do("V_chop", "volume", "chop"),
        ],
        "visual_bindings": {},
    }
    contract = RequestContract(
        problem_text=desc,
        obligations=(
            Obligation(kind="area", container="thiet_dien", params={"witness": "S_td"}),
            Obligation(kind="volume", container="chop", params={"witness": "V_chop"}),
        ),
        input_facts=(InputFact(fact_id="f_sa_vuong_day", label="SA vuông góc với mặt phẳng đáy", values=()),),
        solid_topology=PyramidTopologySpec(apex="S", base_cycle=("A", "B", "C", "D"), base_shape="square"),
        geometric_relations=(
            GeometricRelation(
                kind="perpendicular_line_plane",
                line=("S", "A"),
                plane=("A", "B", "C"),
                source_fact_id="f_sa_vuong_day",
                model_assumption=False,
            ),
        ),
    )
    return spec, contract


# ── Bài 2. Thiết diện hình lập phương bởi mặt phẳng bất kỳ ────────────────────
def bai_2_lap_phuong_thiet_dien_bat_ky() -> tuple[dict[str, Any], RequestContract]:
    desc = (
        "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 4. Gọi M là trung điểm cạnh AD, "
        "N là trung điểm cạnh CD và P là trung điểm cạnh B'C'. Mặt phẳng (MNP) cắt các cạnh "
        "CC', A'B', AA' lần lượt tại các trung điểm E, F, Q tạo thành thiết diện lục giác đều "
        "MNEPFQ. Xác định các giao điểm trên 6 cạnh của hình lập phương, dựng thiết diện "
        "MNEPFQ và tính diện tích thiết diện."
    )
    spec = {
        "spec_version": "1.0",
        "title": "Thiết diện lục giác đều của hình lập phương ABCD.A'B'C'D'",
        "description": desc,
        "memory_declarations": [
            _diem("A", [0, 0, 0]),
            _diem("B", [4, 0, 0]),
            _diem("C", [4, 4, 0]),
            _diem("D", [0, 4, 0]),
            _diem("A_prime", [0, 0, 4]),
            _diem("B_prime", [4, 0, 4]),
            _diem("C_prime", [4, 4, 4]),
            _diem("D_prime", [0, 4, 4]),
            _khai("M", "point3"),
            _khai("N", "point3"),
            _khai("P", "point3"),
            _khai("E", "point3"),
            _khai("F", "point3"),
            _khai("Q", "point3"),
            _khai("lap_phuong", "solid"),
            _khai("mp_MNP", "plane3"),
            _khai("cc_prime", "line3"),
            _khai("ab_prime", "line3"),
            _khai("aa_prime", "line3"),
            _khai("thiet_dien", "section"),
            _khai("canh_MN", "float"),
            _khai("S_td", "float"),
        ],
        "statements": [
            {
                "kind": "construct_solid",
                "target_var": "lap_phuong",
                "label": "ABCD.A'B'C'D'",
                "vertices": ["A", "B", "C", "D", "A_prime", "B_prime", "C_prime", "D_prime"],
                "faces": [
                    ["A", "B", "C", "D"],
                    ["A_prime", "B_prime", "C_prime", "D_prime"],
                    ["A", "B", "B_prime", "A_prime"],
                    ["B", "C", "C_prime", "B_prime"],
                    ["C", "D", "D_prime", "C_prime"],
                    ["D", "A", "A_prime", "D_prime"],
                ],
            },
            {
                "kind": "construct_point",
                "target_var": "M",
                "label": "M",
                "expr": {"kind": "midpoint", "a": "A", "b": "D"},
            },
            {
                "kind": "construct_point",
                "target_var": "N",
                "label": "N",
                "expr": {"kind": "midpoint", "a": "C", "b": "D"},
            },
            {
                "kind": "construct_point",
                "target_var": "P",
                "label": "P",
                "expr": {"kind": "midpoint", "a": "B_prime", "b": "C_prime"},
            },
            {"kind": "construct_plane", "target_var": "mp_MNP", "label": "(MNP)", "through": ["M", "N", "P"]},
            {"kind": "construct_line", "target_var": "cc_prime", "label": "CC'", "through_a": "C", "through_b": "C_prime"},
            {"kind": "construct_line", "target_var": "ab_prime", "label": "A'B'", "through_a": "A_prime", "through_b": "B_prime"},
            {"kind": "construct_line", "target_var": "aa_prime", "label": "AA'", "through_a": "A", "through_b": "A_prime"},
            {
                "kind": "construct_point",
                "target_var": "E",
                "label": "E",
                "expr": {"kind": "intersect_line_plane", "line": "cc_prime", "plane": "mp_MNP"},
            },
            {
                "kind": "construct_point",
                "target_var": "F",
                "label": "F",
                "expr": {"kind": "intersect_line_plane", "line": "ab_prime", "plane": "mp_MNP"},
            },
            {
                "kind": "construct_point",
                "target_var": "Q",
                "label": "Q",
                "expr": {"kind": "intersect_line_plane", "line": "aa_prime", "plane": "mp_MNP"},
            },
            {
                "kind": "construct_section",
                "target_var": "thiet_dien",
                "label": "Thiết diện MNEPFQ",
                "solid": "lap_phuong",
                "plane": "mp_MNP",
            },
            _do("canh_MN", "distance", "M", "N"),
            _do("S_td", "area", "thiet_dien"),
        ],
        "visual_bindings": {},
    }
    contract = RequestContract(
        problem_text=desc,
        obligations=(
            Obligation(kind="distance", container="M", params={"witness": "canh_MN"}),
            Obligation(kind="area", container="thiet_dien", params={"witness": "S_td"}),
        ),
        input_facts=(InputFact(fact_id="f_aa_vuong_day", label="AA' vuông góc với mặt phẳng đáy", values=()),),
        solid_topology=PrismTopologySpec(
            base_cycle=("A", "B", "C", "D"),
            top_cycle=("A_prime", "B_prime", "C_prime", "D_prime"),
            correspondence=(("A", "A_prime"), ("B", "B_prime"), ("C", "C_prime"), ("D", "D_prime")),
            base_shape="square",
            solid_subkind="cube",
        ),
        geometric_relations=(
            GeometricRelation(
                kind="perpendicular_line_plane",
                line=("A", "A_prime"),
                plane=("A", "B", "C"),
                source_fact_id="f_aa_vuong_day",
                model_assumption=False,
            ),
        ),
    )
    return spec, contract


# ── Bài 3. Khoảng cách từ một điểm đến mặt phẳng nghiêng ──────────────────────
def bai_3_khoang_cach_diem_mat_phang_nghieng() -> tuple[dict[str, Any], RequestContract]:
    desc = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = 3, BC = 4, cạnh bên "
        "SA vuông góc với mặt phẳng đáy (ABC) và SA = 6. Từ chân đường cao A, hạ AH vuông góc "
        "với mặt phẳng nghiêng (SBC) tại H (H thuộc cạnh SB vì BC ⊥ (SAB)). Xác định hình chiếu "
        "vuông góc H, kiểm chứng AH ⊥ (SBC) và tính khoảng cách d(A, (SBC)) = AH."
    )
    spec = {
        "spec_version": "1.0",
        "title": "Khoảng cách từ điểm A đến mặt phẳng nghiêng (SBC)",
        "description": desc,
        "memory_declarations": [
            _diem("A", [0, 0, 0]),
            _diem("B", [3, 0, 0]),
            _diem("C", [3, 4, 0]),
            _diem("S", [0, 0, 6]),
            _khai("H", "point3"),
            _khai("chop", "solid"),
            _khai("day", "plane3"),
            _khai("sbc", "plane3"),
            _khai("ah", "line3"),
            _khai("sb", "line3"),
            _khai("bc", "line3"),
            _khai("doan_AH", "segment3"),
            _khai("doan_HC", "segment3"),
            _khai("goc_AH_SB", "float"),
            _khai("goc_AH_BC", "float"),
            _khai("kc_A_SBC", "float"),
        ],
        "statements": [
            {
                "kind": "construct_solid",
                "target_var": "chop",
                "label": "S.ABC",
                "vertices": ["A", "B", "C", "S"],
                "faces": [
                    ["A", "B", "C"],
                    ["A", "B", "S"],
                    ["B", "C", "S"],
                    ["C", "A", "S"],
                ],
            },
            {"kind": "construct_plane", "target_var": "day", "label": "(ABC)", "through": ["A", "B", "C"]},
            {"kind": "construct_plane", "target_var": "sbc", "label": "(SBC)", "through": ["S", "B", "C"]},
            {
                "kind": "construct_point",
                "target_var": "H",
                "label": "H",
                "expr": {"kind": "project_onto", "point": "A", "target": "sbc"},
            },
            {"kind": "construct_segment", "target_var": "doan_AH", "label": "AH", "endpoint_a": "A", "endpoint_b": "H"},
            {"kind": "construct_segment", "target_var": "doan_HC", "label": "HC", "endpoint_a": "H", "endpoint_b": "C"},
            {"kind": "construct_line", "target_var": "ah", "label": "AH", "through_a": "A", "through_b": "H"},
            {"kind": "construct_line", "target_var": "sb", "label": "SB", "through_a": "S", "through_b": "B"},
            {"kind": "construct_line", "target_var": "bc", "label": "BC", "through_a": "B", "through_b": "C"},
            _do("goc_AH_SB", "angle_cos_sq", "ah", "sb"),
            _do("goc_AH_BC", "angle_cos_sq", "ah", "bc"),
            _do("kc_A_SBC", "distance", "A", "sbc"),
        ],
        "visual_bindings": {},
    }
    contract = RequestContract(
        problem_text=desc,
        obligations=(Obligation(kind="distance", container="A", params={"witness": "kc_A_SBC"}),),
        input_facts=(InputFact(fact_id="f_sa_vuong_day", label="SA vuông góc với mặt phẳng đáy", values=()),),
        solid_topology=PyramidTopologySpec(apex="S", base_cycle=("A", "B", "C")),
        geometric_relations=(
            GeometricRelation(
                kind="perpendicular_line_plane",
                line=("S", "A"),
                plane=("A", "B", "C"),
                source_fact_id="f_sa_vuong_day",
                model_assumption=False,
            ),
        ),
    )
    return spec, contract


# ── Bài 4. Góc nhị diện giữa hai mặt phẳng ────────────────────────────────────
def bai_4_goc_nhi_dien_hai_mat_phang() -> tuple[dict[str, Any], RequestContract]:
    desc = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác cân tại A với AB = AC = 5, BC = 6, "
        "cạnh bên SA vuông góc với mặt phẳng đáy (ABC) và SA = 4. Xác định giao tuyến BC "
        "của hai mặt phẳng (SBC) và (ABC), dựng trung điểm H của BC sao cho AH ⊥ BC và SH ⊥ BC, "
        "dựng mặt phẳng (SAH) vuông góc với giao tuyến BC tại H và tính cosin của góc phẳng nhị diện "
        "SHA của góc nhị diện [S, BC, A]."
    )
    spec = {
        "spec_version": "1.0",
        "title": "Góc nhị diện [S, BC, A] giữa hai mặt phẳng (SBC) và (ABC)",
        "description": desc,
        "memory_declarations": [
            _diem("A", [0, 0, 0]),
            _diem("B", [4, -3, 0]),
            _diem("C", [4, 3, 0]),
            _diem("S", [0, 0, 4]),
            _khai("H", "point3"),
            _khai("chop", "solid"),
            _khai("day", "plane3"),
            _khai("sbc", "plane3"),
            _khai("mp_SAH", "plane3"),
            _khai("bc", "line3"),
            _khai("ah", "line3"),
            _khai("sh", "line3"),
            _khai("doan_AH", "segment3"),
            _khai("doan_SH", "segment3"),
            _khai("len_AH", "float"),
            _khai("len_SH", "float"),
            _khai("goc_AH_BC", "float"),
            _khai("goc_SH_BC", "float"),
            _khai("cos_nhi_dien", "float"),
        ],
        "statements": [
            {
                "kind": "construct_solid",
                "target_var": "chop",
                "label": "S.ABC",
                "vertices": ["A", "B", "C", "S"],
                "faces": [
                    ["A", "B", "C"],
                    ["A", "B", "S"],
                    ["B", "C", "S"],
                    ["C", "A", "S"],
                ],
            },
            {"kind": "construct_plane", "target_var": "day", "label": "(ABC)", "through": ["A", "B", "C"]},
            {"kind": "construct_plane", "target_var": "sbc", "label": "(SBC)", "through": ["S", "B", "C"]},
            {"kind": "construct_line", "target_var": "bc", "label": "BC", "through_a": "B", "through_b": "C"},
            {
                "kind": "construct_point",
                "target_var": "H",
                "label": "H",
                "expr": {"kind": "project_onto", "point": "A", "target": "bc"},
            },
            {"kind": "construct_plane", "target_var": "mp_SAH", "label": "(SAH)", "through": ["S", "A", "H"]},
            {"kind": "construct_segment", "target_var": "doan_AH", "label": "AH", "endpoint_a": "A", "endpoint_b": "H"},
            {"kind": "construct_segment", "target_var": "doan_SH", "label": "SH", "endpoint_a": "S", "endpoint_b": "H"},
            {"kind": "construct_line", "target_var": "ah", "label": "AH", "through_a": "A", "through_b": "H"},
            {"kind": "construct_line", "target_var": "sh", "label": "SH", "through_a": "S", "through_b": "H"},
            _do("len_AH", "distance", "A", "H"),
            _do("len_SH", "distance", "S", "H"),
            _do("goc_AH_BC", "angle_cos_sq", "ah", "bc"),
            _do("goc_SH_BC", "angle_cos_sq", "sh", "bc"),
            _do("cos_nhi_dien", "angle_cos_sq", "sbc", "day"),
        ],
        "visual_bindings": {},
    }
    contract = RequestContract(
        problem_text=desc,
        obligations=(
            Obligation(kind="distance", container="S", params={"witness": "len_SH"}),
            Obligation(kind="angle", container="sbc", params={"witness": "cos_nhi_dien"}),
        ),
        input_facts=(InputFact(fact_id="f_sa_vuong_day", label="SA vuông góc với mặt phẳng đáy", values=()),),
        solid_topology=PyramidTopologySpec(apex="S", base_cycle=("A", "B", "C")),
        geometric_relations=(
            GeometricRelation(
                kind="perpendicular_line_plane",
                line=("S", "A"),
                plane=("A", "B", "C"),
                source_fact_id="f_sa_vuong_day",
                model_assumption=False,
            ),
        ),
    )
    return spec, contract


# ── Bài 5. Khoảng cách giữa hai đường thẳng chéo nhau ─────────────────────────
def bai_5_khoang_cach_hai_duong_cheo_nhau() -> tuple[dict[str, Any], RequestContract]:
    desc = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh bằng 4, cạnh bên SA vuông góc "
        "với mặt phẳng đáy (ABCD) và SA = 4. Hai đường thẳng SC và BD chéo nhau. Gọi Q là "
        "giao điểm hai đường chéo AC và BD (trung điểm của BD), từ Q kẻ QP vuông góc với SC "
        "tại P. Chứng minh PQ là đoạn vuông góc chung của hai đường thẳng chéo nhau SC và BD, "
        "và tính khoảng cách d(SC, BD) = PQ."
    )
    spec = {
        "spec_version": "1.0",
        "title": "Đoạn vuông góc chung và khoảng cách giữa hai đường chéo nhau SC và BD",
        "description": desc,
        "memory_declarations": [
            _diem("A", [0, 0, 0]),
            _diem("B", [4, 0, 0]),
            _diem("C", [4, 4, 0]),
            _diem("D", [0, 4, 0]),
            _diem("S", [0, 0, 4]),
            _khai("Q", "point3"),
            _khai("P", "point3"),
            _khai("chop", "solid"),
            _khai("day", "plane3"),
            _khai("sac", "plane3"),
            _khai("sc", "line3"),
            _khai("bd", "line3"),
            _khai("pq", "line3"),
            _khai("doan_AC", "segment3"),
            _khai("doan_BD", "segment3"),
            _khai("doan_PQ", "segment3"),
            _khai("goc_PQ_SC", "float"),
            _khai("goc_PQ_BD", "float"),
            _khai("kc_SC_BD", "float"),
        ],
        "statements": [
            {
                "kind": "construct_solid",
                "target_var": "chop",
                "label": "S.ABCD",
                "vertices": ["A", "B", "C", "D", "S"],
                "faces": [
                    ["A", "B", "C", "D"],
                    ["A", "B", "S"],
                    ["B", "C", "S"],
                    ["C", "D", "S"],
                    ["D", "A", "S"],
                ],
            },
            {"kind": "construct_plane", "target_var": "day", "label": "(ABCD)", "through": ["A", "B", "C"]},
            {"kind": "construct_segment", "target_var": "doan_AC", "label": "AC", "endpoint_a": "A", "endpoint_b": "C"},
            {"kind": "construct_segment", "target_var": "doan_BD", "label": "BD", "endpoint_a": "B", "endpoint_b": "D"},
            {"kind": "construct_line", "target_var": "sc", "label": "SC", "through_a": "S", "through_b": "C"},
            {"kind": "construct_line", "target_var": "bd", "label": "BD", "through_a": "B", "through_b": "D"},
            {
                "kind": "construct_point",
                "target_var": "Q",
                "label": "Q",
                "expr": {"kind": "midpoint", "a": "B", "b": "D"},
            },
            {"kind": "construct_plane", "target_var": "sac", "label": "(SAC)", "through": ["S", "A", "C"]},
            {
                "kind": "construct_point",
                "target_var": "P",
                "label": "P",
                "expr": {"kind": "project_onto", "point": "Q", "target": "sc"},
            },
            {"kind": "construct_segment", "target_var": "doan_PQ", "label": "PQ", "endpoint_a": "P", "endpoint_b": "Q"},
            {"kind": "construct_line", "target_var": "pq", "label": "PQ", "through_a": "P", "through_b": "Q"},
            _do("goc_PQ_SC", "angle_cos_sq", "pq", "sc"),
            _do("goc_PQ_BD", "angle_cos_sq", "pq", "bd"),
            _do("kc_SC_BD", "distance", "sc", "bd"),
        ],
        "visual_bindings": {},
    }
    contract = RequestContract(
        problem_text=desc,
        obligations=(Obligation(kind="distance", container="sc", params={"witness": "kc_SC_BD"}),),
        input_facts=(InputFact(fact_id="f_sa_vuong_day", label="SA vuông góc với mặt phẳng đáy", values=()),),
        solid_topology=PyramidTopologySpec(apex="S", base_cycle=("A", "B", "C", "D"), base_shape="square"),
        geometric_relations=(
            GeometricRelation(
                kind="perpendicular_line_plane",
                line=("S", "A"),
                plane=("A", "B", "C"),
                source_fact_id="f_sa_vuong_day",
                model_assumption=False,
            ),
        ),
    )
    return spec, contract


# ── Bài 6. Thiết diện lăng trụ tam giác bởi mặt phẳng ─────────────────────────
def bai_6_lang_tru_tam_giac_thiet_dien() -> tuple[dict[str, Any], RequestContract]:
    desc = (
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại A với "
        "AB = AC = 4, cạnh bên AA' = 4. Gọi N là trung điểm cạnh BC, P là trung điểm cạnh CC' "
        "và Q là trung điểm cạnh A'C'. Mặt phẳng (NPQ) cắt cạnh AB tại M (AM = 3/4 AB) và cắt "
        "cạnh A'B' tại E (A'E = 1/4 A'B'). Xác định các giao tuyến trên cả 5 mặt của lăng trụ, "
        "dựng thiết diện ngũ giác MNPQE và tính diện tích thiết diện."
    )
    spec = {
        "spec_version": "1.0",
        "title": "Thiết diện ngũ giác của lăng trụ đứng ABC.A'B'C' cắt bởi mặt phẳng (NPQ)",
        "description": desc,
        "memory_declarations": [
            _diem("A", [0, 0, 0]),
            _diem("B", [4, 0, 0]),
            _diem("C", [0, 4, 0]),
            _diem("A_prime", [0, 0, 4]),
            _diem("B_prime", [4, 0, 4]),
            _diem("C_prime", [0, 4, 4]),
            _khai("N", "point3"),
            _khai("P", "point3"),
            _khai("Q", "point3"),
            _khai("M", "point3"),
            _khai("E", "point3"),
            _khai("lang_tru", "solid"),
            _khai("mp_NPQ", "plane3"),
            _khai("ab", "line3"),
            _khai("ab_prime", "line3"),
            _khai("thiet_dien", "section"),
            _khai("S_td", "float"),
            _khai("V_lt", "float"),
        ],
        "statements": [
            {
                "kind": "construct_solid",
                "target_var": "lang_tru",
                "label": "ABC.A'B'C'",
                "vertices": ["A", "B", "C", "A_prime", "B_prime", "C_prime"],
                "faces": [
                    ["A", "B", "C"],
                    ["A_prime", "B_prime", "C_prime"],
                    ["A", "B", "B_prime", "A_prime"],
                    ["B", "C", "C_prime", "B_prime"],
                    ["C", "A", "A_prime", "C_prime"],
                ],
            },
            {
                "kind": "construct_point",
                "target_var": "N",
                "label": "N",
                "expr": {"kind": "midpoint", "a": "B", "b": "C"},
            },
            {
                "kind": "construct_point",
                "target_var": "P",
                "label": "P",
                "expr": {"kind": "midpoint", "a": "C", "b": "C_prime"},
            },
            {
                "kind": "construct_point",
                "target_var": "Q",
                "label": "Q",
                "expr": {"kind": "midpoint", "a": "A_prime", "b": "C_prime"},
            },
            {"kind": "construct_plane", "target_var": "mp_NPQ", "label": "(NPQ)", "through": ["N", "P", "Q"]},
            {"kind": "construct_line", "target_var": "ab", "label": "AB", "through_a": "A", "through_b": "B"},
            {"kind": "construct_line", "target_var": "ab_prime", "label": "A'B'", "through_a": "A_prime", "through_b": "B_prime"},
            {
                "kind": "construct_point",
                "target_var": "M",
                "label": "M",
                "expr": {"kind": "intersect_line_plane", "line": "ab", "plane": "mp_NPQ"},
            },
            {
                "kind": "construct_point",
                "target_var": "E",
                "label": "E",
                "expr": {"kind": "intersect_line_plane", "line": "ab_prime", "plane": "mp_NPQ"},
            },
            {
                "kind": "construct_section",
                "target_var": "thiet_dien",
                "label": "Thiết diện MNPQE",
                "solid": "lang_tru",
                "plane": "mp_NPQ",
            },
            _do("S_td", "area", "thiet_dien"),
            _do("V_lt", "volume", "lang_tru"),
        ],
        "visual_bindings": {},
    }
    contract = RequestContract(
        problem_text=desc,
        obligations=(
            Obligation(kind="area", container="thiet_dien", params={"witness": "S_td"}),
            Obligation(kind="volume", container="lang_tru", params={"witness": "V_lt"}),
        ),
        input_facts=(InputFact(fact_id="f_aa_vuong_day", label="AA' vuông góc với mặt phẳng đáy", values=()),),
        solid_topology=PrismTopologySpec(
            base_cycle=("A", "B", "C"),
            top_cycle=("A_prime", "B_prime", "C_prime"),
            correspondence=(("A", "A_prime"), ("B", "B_prime"), ("C", "C_prime")),
        ),
        geometric_relations=(
            GeometricRelation(
                kind="perpendicular_line_plane",
                line=("A", "A_prime"),
                plane=("A", "B", "C"),
                source_fact_id="f_aa_vuong_day",
                model_assumption=False,
            ),
        ),
    )
    return spec, contract


# ── Bài 7. Mặt cầu và mặt phẳng cắt ───────────────────────────────────────────
def bai_7_mat_cau_cat_mat_phang() -> tuple[dict[str, Any], RequestContract]:
    desc = (
        "Trong không gian, cho mặt cầu (S) có tâm I(0; 0; 0) và bán kính R = 5. Mặt phẳng (P) "
        "song song với mặt phẳng Oxy, đi qua ba điểm M(4; 0; 3), N(0; 4; 3), K(-4; 0; 3) "
        "(có phương trình z - 3 = 0). Hạ IH vuông góc với mặt phẳng (P) tại H(0; 0; 3). "
        "Chứng minh d = IH = 3 < R = 5 nên mặt phẳng (P) cắt mặt cầu (S) theo đường tròn "
        "giao tuyến (C) tâm H, kiểm chứng IH ⊥ HM và tính bán kính r = √(R² - d²) = 4 cùng "
        "diện tích hình tròn thiết diện."
    )
    spec = {
        "spec_version": "1.0",
        "title": "Mặt cầu (S) cắt bởi mặt phẳng (P) theo giao tuyến đường tròn",
        "description": desc,
        "memory_declarations": [
            _diem("I", [0, 0, 0]),
            _diem("A", [0, 0, 5]),
            _diem("M", [4, 0, 3]),
            _diem("N", [0, 4, 3]),
            _diem("K", [-4, 0, 3]),
            {"name": "R", "type": "float", "initial_value": 5, "provenance": "GIVEN", "source_fact_id": "f_ban_kinh"},
            _khai("H", "point3"),
            _khai("cau", "curved_solid"),
            _khai("mp_P", "plane3"),
            _khai("C", "circle3"),
            _khai("ih", "line3"),
            _khai("hm", "line3"),
            _khai("doan_IH", "segment3"),
            _khai("doan_HM", "segment3"),
            _khai("doan_IM", "segment3"),
            _khai("goc_IH_HM", "float"),
            _khai("d_I_P", "float"),
            _khai("r", "float"),
            _khai("S", "float"),
        ],
        "statements": [
            {
                "kind": "construct_curved_solid",
                "target_var": "cau",
                "curved_kind": "ball",
                "anchor": "I",
                "radius": "R",
                "label": "(S)",
            },
            {"kind": "construct_plane", "target_var": "mp_P", "label": "(P)", "through": ["M", "N", "K"]},
            {
                "kind": "construct_point",
                "target_var": "H",
                "label": "H",
                "expr": {"kind": "project_onto", "point": "I", "target": "mp_P"},
            },
            {
                "kind": "assign",
                "target_var": "C",
                "label": "(C)",
                "expr": {"kind": "intersect_plane_curved", "solid": "cau", "plane": "mp_P"},
            },
            {"kind": "construct_segment", "target_var": "doan_IH", "label": "IH", "endpoint_a": "I", "endpoint_b": "H"},
            {"kind": "construct_segment", "target_var": "doan_HM", "label": "HM", "endpoint_a": "H", "endpoint_b": "M"},
            {"kind": "construct_segment", "target_var": "doan_IM", "label": "IM", "endpoint_a": "I", "endpoint_b": "M"},
            {"kind": "construct_line", "target_var": "ih", "label": "IH", "through_a": "I", "through_b": "H"},
            {"kind": "construct_line", "target_var": "hm", "label": "HM", "through_a": "H", "through_b": "M"},
            _do("goc_IH_HM", "angle_cos_sq", "ih", "hm"),
            _do("d_I_P", "distance", "I", "mp_P"),
            _do("r", "radius", "C"),
            _do("S", "area", "C"),
        ],
        "visual_bindings": {},
    }
    contract = RequestContract(
        problem_text=desc,
        obligations=(
            Obligation(kind="radius", container="C", params={"witness": "r"}),
            Obligation(kind="area", container="C", params={"witness": "S"}),
        ),
        input_facts=(InputFact(fact_id="f_ban_kinh", label="bán kính mặt cầu", values=(5,)),),
    )
    return spec, contract


# ── Bài 8. Giao điểm của đường thẳng và mặt phẳng trong Oxyz ──────────────────
def bai_8_oxyz_giao_diem_duong_mat() -> tuple[dict[str, Any], RequestContract]:
    desc = (
        "Trong không gian Oxyz, cho mặt phẳng (P) đi qua ba điểm A(6; 0; 0), B(0; 6; 0), "
        "C(0; 0; 6) có phương trình x + y + z - 6 = 0 và đường thẳng d đi qua hai điểm "
        "D(1; 1; 0), E(3; 3; 6). Xác định giao điểm duy nhất M = d ∩ (P), dựng hình chiếu "
        "vuông góc H của điểm E lên mặt phẳng (P) để biểu diễn góc cắt giữa d và (P), và tính "
        "khoảng cách từ gốc tọa độ O đến giao điểm M."
    )
    spec = {
        "spec_version": "1.0",
        "title": "Giao điểm M của đường thẳng d và mặt phẳng (P) trong Oxyz",
        "description": desc,
        "memory_declarations": [
            _diem("O", [0, 0, 0]),
            _diem("A", [6, 0, 0]),
            _diem("B", [0, 6, 0]),
            _diem("C", [0, 0, 6]),
            _diem("D", [1, 1, 0]),
            _diem("E", [3, 3, 6]),
            _khai("M", "point3"),
            _khai("H", "point3"),
            _khai("mp_P", "plane3"),
            _khai("tam_giac_ABC", "polygon3"),
            _khai("duong_d", "line3"),
            _khai("eh", "line3"),
            _khai("hm", "line3"),
            _khai("doan_DE", "segment3"),
            _khai("doan_EH", "segment3"),
            _khai("doan_HM", "segment3"),
            _khai("doan_OM", "segment3"),
            _khai("goc_EH_HM", "float"),
            _khai("kc_E_P", "float"),
            _khai("do_dai_OM", "float"),
        ],
        "statements": [
            {"kind": "construct_plane", "target_var": "mp_P", "label": "(P)", "through": ["A", "B", "C"]},
            {"kind": "construct_polygon", "target_var": "tam_giac_ABC", "label": "ABC", "vertices": ["A", "B", "C"]},
            {"kind": "construct_line", "target_var": "duong_d", "label": "d", "through_a": "D", "through_b": "E"},
            {"kind": "construct_segment", "target_var": "doan_DE", "label": "DE", "endpoint_a": "D", "endpoint_b": "E"},
            {
                "kind": "construct_point",
                "target_var": "M",
                "label": "M",
                "expr": {"kind": "intersect_line_plane", "line": "duong_d", "plane": "mp_P"},
            },
            {
                "kind": "construct_point",
                "target_var": "H",
                "label": "H",
                "expr": {"kind": "project_onto", "point": "E", "target": "mp_P"},
            },
            {"kind": "construct_segment", "target_var": "doan_EH", "label": "EH", "endpoint_a": "E", "endpoint_b": "H"},
            {"kind": "construct_segment", "target_var": "doan_HM", "label": "HM", "endpoint_a": "H", "endpoint_b": "M"},
            {"kind": "construct_segment", "target_var": "doan_OM", "label": "OM", "endpoint_a": "O", "endpoint_b": "M"},
            {"kind": "construct_line", "target_var": "eh", "label": "EH", "through_a": "E", "through_b": "H"},
            {"kind": "construct_line", "target_var": "hm", "label": "HM", "through_a": "H", "through_b": "M"},
            _do("goc_EH_HM", "angle_cos_sq", "eh", "hm"),
            _do("kc_E_P", "distance", "E", "mp_P"),
            _do("do_dai_OM", "distance", "O", "M"),
        ],
        "visual_bindings": {},
    }
    contract = RequestContract(
        problem_text=desc,
        obligations=(
            Obligation(kind="distance", container="E", params={"witness": "kc_E_P"}),
            Obligation(kind="distance", container="O", params={"witness": "do_dai_OM"}),
        ),
    )
    return spec, contract


# ── Bài 9. Mặt phẳng tiếp xúc với mặt cầu ─────────────────────────────────────
def bai_9_mat_phang_tiep_xuc_mat_cau() -> tuple[dict[str, Any], RequestContract]:
    desc = (
        "Trong không gian Oxyz, cho mặt cầu (S) có tâm I(0; 0; 0), bán kính R = 5 và điểm "
        "A(3; 0; 4) thuộc mặt cầu (S). Dựng bán kính IA và mặt phẳng tiếp diện (P) đi qua A, "
        "vuông góc với bán kính IA (có phương trình 3x + 4z - 25 = 0). Lấy hai điểm B(3; 4; 4) "
        "và C(-1; 0; 7) trên tiếp diện (P), kiểm chứng IA ⊥ AB, IA ⊥ AC và d(I, (P)) = IA = R = 5 "
        "để khẳng định (P) tiếp xúc với mặt cầu (S) tại duy nhất tiếp điểm A."
    )
    spec = {
        "spec_version": "1.0",
        "title": "Mặt phẳng tiếp diện (P) tiếp xúc với mặt cầu (S) tại tiếp điểm A",
        "description": desc,
        "memory_declarations": [
            _diem("I", [0, 0, 0]),
            _diem("A", [3, 0, 4]),
            _diem("B", [3, 4, 4]),
            _diem("C", [-1, 0, 7]),
            {"name": "R", "type": "float", "initial_value": 5, "provenance": "GIVEN", "source_fact_id": "f_ban_kinh"},
            _khai("cau", "curved_solid"),
            _khai("ia", "line3"),
            _khai("ab", "line3"),
            _khai("ac", "line3"),
            _khai("mp_tiep_dien", "plane3"),
            _khai("doan_IA", "segment3"),
            _khai("doan_AB", "segment3"),
            _khai("doan_AC", "segment3"),
            _khai("doan_IB", "segment3"),
            _khai("goc_IA_AB", "float"),
            _khai("goc_IA_AC", "float"),
            _khai("d_I_P", "float"),
            _khai("do_dai_IB", "float"),
        ],
        "statements": [
            {
                "kind": "construct_curved_solid",
                "target_var": "cau",
                "curved_kind": "ball",
                "anchor": "I",
                "rim_point": "A",
                "label": "(S)",
            },
            {"kind": "construct_line", "target_var": "ia", "label": "IA", "through_a": "I", "through_b": "A"},
            {"kind": "construct_segment", "target_var": "doan_IA", "label": "IA", "endpoint_a": "I", "endpoint_b": "A"},
            {
                "kind": "assign",
                "target_var": "mp_tiep_dien",
                "label": "(P)",
                "expr": {"kind": "plane_perpendicular_to_line", "point": "A", "line": "ia"},
            },
            {"kind": "construct_segment", "target_var": "doan_AB", "label": "AB", "endpoint_a": "A", "endpoint_b": "B"},
            {"kind": "construct_segment", "target_var": "doan_AC", "label": "AC", "endpoint_a": "A", "endpoint_b": "C"},
            {"kind": "construct_segment", "target_var": "doan_IB", "label": "IB", "endpoint_a": "I", "endpoint_b": "B"},
            {"kind": "construct_line", "target_var": "ab", "label": "AB", "through_a": "A", "through_b": "B"},
            {"kind": "construct_line", "target_var": "ac", "label": "AC", "through_a": "A", "through_b": "C"},
            _do("goc_IA_AB", "angle_cos_sq", "ia", "ab"),
            _do("goc_IA_AC", "angle_cos_sq", "ia", "ac"),
            _do("d_I_P", "distance", "I", "mp_tiep_dien"),
            _do("do_dai_IB", "distance", "I", "B"),
        ],
        "visual_bindings": {},
    }
    contract = RequestContract(
        problem_text=desc,
        obligations=(
            Obligation(kind="distance", container="I", params={"witness": "d_I_P"}),
            Obligation(kind="distance", container="I", params={"witness": "do_dai_IB"}),
        ),
        input_facts=(InputFact(fact_id="f_ban_kinh", label="bán kính mặt cầu", values=(5,)),),
    )
    return spec, contract


# ── Bài 10. Hình nón cắt bởi mặt phẳng song song đáy ──────────────────────────
def bai_10_hinh_non_cat_song_song_day() -> tuple[dict[str, Any], RequestContract]:
    desc = (
        "Cho hình nón đỉnh S, tâm đáy O, bán kính đáy OA = R = 6 và chiều cao SO = h = 8. "
        "Mặt phẳng (P) đi qua trung điểm I của trục SO và song song với mặt phẳng đáy, cắt "
        "các đường sinh SA, SB lần lượt tại M, N và cắt hình nón theo đường tròn thiết diện "
        "(C) tâm I. Xác định tâm thiết diện I, điểm M trên đường sinh SA, dựng đường tròn "
        "thiết diện (C) và tính bán kính thiết diện r' = (SI/SO)·R = 3 cùng diện tích thiết diện."
    )
    spec = {
        "spec_version": "1.0",
        "title": "Hình nón cắt bởi mặt phẳng (P) song song với mặt phẳng đáy",
        "description": desc,
        "memory_declarations": [
            _diem("O", [0, 0, 0]),
            _diem("S", [0, 0, 8]),
            _diem("A", [6, 0, 0]),
            _diem("B", [0, 6, 0]),
            _khai("I", "point3"),
            _khai("M", "point3"),
            _khai("N", "point3"),
            _khai("non", "curved_solid"),
            _khai("truc_SO", "line3"),
            _khai("sa", "line3"),
            _khai("sb", "line3"),
            _khai("im", "line3"),
            _khai("mp_P", "plane3"),
            _khai("C", "circle3"),
            _khai("doan_SO", "segment3"),
            _khai("doan_OA", "segment3"),
            _khai("doan_SA", "segment3"),
            _khai("doan_SB", "segment3"),
            _khai("doan_IM", "segment3"),
            _khai("doan_IN", "segment3"),
            _khai("goc_SO_IM", "float"),
            _khai("r_prime", "float"),
            _khai("S_td", "float"),
            _khai("V_non", "float"),
        ],
        "statements": [
            {
                "kind": "construct_curved_solid",
                "target_var": "non",
                "curved_kind": "cone",
                "anchor": "O",
                "apex_or_top": "S",
                "rim_point": "A",
                "label": "Hình nón",
            },
            {"kind": "construct_segment", "target_var": "doan_SO", "label": "SO", "endpoint_a": "S", "endpoint_b": "O"},
            {"kind": "construct_segment", "target_var": "doan_OA", "label": "OA", "endpoint_a": "O", "endpoint_b": "A"},
            {"kind": "construct_segment", "target_var": "doan_SA", "label": "SA", "endpoint_a": "S", "endpoint_b": "A"},
            {"kind": "construct_segment", "target_var": "doan_SB", "label": "SB", "endpoint_a": "S", "endpoint_b": "B"},
            {"kind": "construct_line", "target_var": "truc_SO", "label": "SO", "through_a": "S", "through_b": "O"},
            {"kind": "construct_line", "target_var": "sa", "label": "SA", "through_a": "S", "through_b": "A"},
            {"kind": "construct_line", "target_var": "sb", "label": "SB", "through_a": "S", "through_b": "B"},
            {
                "kind": "construct_point",
                "target_var": "I",
                "label": "I",
                "expr": {"kind": "midpoint", "a": "S", "b": "O"},
            },
            {
                "kind": "assign",
                "target_var": "mp_P",
                "label": "(P)",
                "expr": {"kind": "plane_perpendicular_to_line", "point": "I", "line": "truc_SO"},
            },
            {
                "kind": "construct_point",
                "target_var": "M",
                "label": "M",
                "expr": {"kind": "intersect_line_plane", "line": "sa", "plane": "mp_P"},
            },
            {
                "kind": "construct_point",
                "target_var": "N",
                "label": "N",
                "expr": {"kind": "intersect_line_plane", "line": "sb", "plane": "mp_P"},
            },
            {
                "kind": "assign",
                "target_var": "C",
                "label": "(C)",
                "expr": {"kind": "intersect_plane_curved", "solid": "non", "plane": "mp_P"},
            },
            {"kind": "construct_segment", "target_var": "doan_IM", "label": "IM", "endpoint_a": "I", "endpoint_b": "M"},
            {"kind": "construct_segment", "target_var": "doan_IN", "label": "IN", "endpoint_a": "I", "endpoint_b": "N"},
            {"kind": "construct_line", "target_var": "im", "label": "IM", "through_a": "I", "through_b": "M"},
            _do("goc_SO_IM", "angle_cos_sq", "truc_SO", "im"),
            _do("r_prime", "radius", "C"),
            _do("S_td", "area", "C"),
            _do("V_non", "volume", "non"),
        ],
        "visual_bindings": {},
    }
    contract = RequestContract(
        problem_text=desc,
        obligations=(
            Obligation(kind="radius", container="C", params={"witness": "r_prime"}),
            Obligation(kind="area", container="C", params={"witness": "S_td"}),
            Obligation(kind="volume", container="non", params={"witness": "V_non"}),
        ),
    )
    return spec, contract


# ── Bài 11. Hình chóp kết hợp mặt cầu ngoại tiếp ──────────────────────────────
def bai_11_chop_mat_cau_ngoai_tiep() -> tuple[dict[str, Any], RequestContract]:
    desc = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông tâm O cạnh bằng 4, cạnh bên SA "
        "vuông góc với mặt phẳng đáy (ABCD) và SA = 4. Dựng trục đường tròn ngoại tiếp đáy "
        "đi qua tâm O, dựng mặt phẳng trung trực của cạnh bên SA qua trung điểm M của SA để "
        "xác định tâm I của mặt cầu ngoại tiếp hình chóp S.ABCD. Kiểm chứng IA = IB = IC = ID = IS "
        "và tính bán kính R cùng thể tích khối cầu ngoại tiếp."
    )
    spec = {
        "spec_version": "1.0",
        "title": "Hình chóp S.ABCD và mặt cầu ngoại tiếp (S) tâm I",
        "description": desc,
        "memory_declarations": [
            _diem("A", [0, 0, 0]),
            _diem("B", [4, 0, 0]),
            _diem("C", [4, 4, 0]),
            _diem("D", [0, 4, 0]),
            _diem("S", [0, 0, 4]),
            _khai("O", "point3"),
            _khai("M", "point3"),
            _khai("M_AB", "point3"),
            _khai("M_AD", "point3"),
            _khai("I", "point3"),
            _khai("chop", "solid"),
            _khai("day", "plane3"),
            _khai("ab", "line3"),
            _khai("ad", "line3"),
            _khai("sa", "line3"),
            _khai("mp_tt_AB", "plane3"),
            _khai("mp_tt_AD", "plane3"),
            _khai("mp_tt_SA", "plane3"),
            _khai("truc_day", "line3"),
            _khai("doan_AC", "segment3"),
            _khai("doan_OI", "segment3"),
            _khai("doan_MI", "segment3"),
            _khai("doan_IS", "segment3"),
            _khai("doan_IA", "segment3"),
            _khai("cau_ngoai_tiep", "curved_solid"),
            _khai("R", "float"),
            _khai("V_cau", "float"),
        ],
        "statements": [
            {
                "kind": "construct_solid",
                "target_var": "chop",
                "label": "S.ABCD",
                "vertices": ["A", "B", "C", "D", "S"],
                "faces": [
                    ["A", "B", "C", "D"],
                    ["A", "B", "S"],
                    ["B", "C", "S"],
                    ["C", "D", "S"],
                    ["D", "A", "S"],
                ],
            },
            {"kind": "construct_plane", "target_var": "day", "label": "(ABCD)", "through": ["A", "B", "C"]},
            {"kind": "construct_segment", "target_var": "doan_AC", "label": "AC", "endpoint_a": "A", "endpoint_b": "C"},
            {
                "kind": "construct_point",
                "target_var": "O",
                "label": "O",
                "expr": {"kind": "midpoint", "a": "A", "b": "C"},
            },
            {
                "kind": "construct_point",
                "target_var": "M",
                "label": "M",
                "expr": {"kind": "midpoint", "a": "S", "b": "A"},
            },
            {
                "kind": "construct_point",
                "target_var": "M_AB",
                "label": "M_AB",
                "expr": {"kind": "midpoint", "a": "A", "b": "B"},
            },
            {
                "kind": "construct_point",
                "target_var": "M_AD",
                "label": "M_AD",
                "expr": {"kind": "midpoint", "a": "A", "b": "D"},
            },
            {"kind": "construct_line", "target_var": "ab", "label": "AB", "through_a": "A", "through_b": "B"},
            {"kind": "construct_line", "target_var": "ad", "label": "AD", "through_a": "A", "through_b": "D"},
            {"kind": "construct_line", "target_var": "sa", "label": "SA", "through_a": "S", "through_b": "A"},
            {
                "kind": "assign",
                "target_var": "mp_tt_AB",
                "label": "Trung trực AB",
                "expr": {"kind": "plane_perpendicular_to_line", "point": "M_AB", "line": "ab"},
            },
            {
                "kind": "assign",
                "target_var": "mp_tt_AD",
                "label": "Trung trực AD",
                "expr": {"kind": "plane_perpendicular_to_line", "point": "M_AD", "line": "ad"},
            },
            {
                "kind": "assign",
                "target_var": "mp_tt_SA",
                "label": "Trung trực SA",
                "expr": {"kind": "plane_perpendicular_to_line", "point": "M", "line": "sa"},
            },
            {
                "kind": "assign",
                "target_var": "truc_day",
                "label": "Trục ngoại tiếp đáy",
                "expr": {"kind": "intersect_plane_plane", "plane_a": "mp_tt_AB", "plane_b": "mp_tt_AD"},
            },
            {
                "kind": "construct_point",
                "target_var": "I",
                "label": "I",
                "expr": {"kind": "intersect_line_plane", "line": "truc_day", "plane": "mp_tt_SA"},
            },
            {"kind": "construct_segment", "target_var": "doan_OI", "label": "OI", "endpoint_a": "O", "endpoint_b": "I"},
            {"kind": "construct_segment", "target_var": "doan_MI", "label": "MI", "endpoint_a": "M", "endpoint_b": "I"},
            {"kind": "construct_segment", "target_var": "doan_IS", "label": "IS", "endpoint_a": "I", "endpoint_b": "S"},
            {"kind": "construct_segment", "target_var": "doan_IA", "label": "IA", "endpoint_a": "I", "endpoint_b": "A"},
            {
                "kind": "construct_curved_solid",
                "target_var": "cau_ngoai_tiep",
                "curved_kind": "ball",
                "anchor": "I",
                "rim_point": "S",
                "label": "(S)",
            },
            _do("R", "radius", "cau_ngoai_tiep"),
            _do("V_cau", "volume", "cau_ngoai_tiep"),
        ],
        "visual_bindings": {},
    }
    contract = RequestContract(
        problem_text=desc,
        obligations=(
            Obligation(kind="radius", container="cau_ngoai_tiep", params={"witness": "R"}),
            Obligation(kind="volume", container="cau_ngoai_tiep", params={"witness": "V_cau"}),
        ),
        input_facts=(InputFact(fact_id="f_sa_vuong_day", label="SA vuông góc với mặt phẳng đáy", values=()),),
        solid_topology=PyramidTopologySpec(apex="S", base_cycle=("A", "B", "C", "D"), base_shape="square"),
        geometric_relations=(
            GeometricRelation(
                kind="perpendicular_line_plane",
                line=("S", "A"),
                plane=("A", "B", "C"),
                source_fact_id="f_sa_vuong_day",
                model_assumption=False,
            ),
        ),
    )
    return spec, contract


BAI_MAU_NANG_CAO = [
    ("chop-thiet-dien-ba-diem", "Dựng hình · thiết diện", bai_1_chop_thiet_dien_ba_diem),
    ("lap-phuong-thiet-dien-bat-ky", "Dựng hình · thiết diện", bai_2_lap_phuong_thiet_dien_bat_ky),
    ("khoang-cach-diem-mat-phang-nghieng", "Khoảng cách · thể tích · góc", bai_3_khoang_cach_diem_mat_phang_nghieng),
    ("goc-nhi-dien-hai-mat-phang", "Khoảng cách · thể tích · góc", bai_4_goc_nhi_dien_hai_mat_phang),
    ("khoang-cach-hai-duong-cheo-nhau", "Khoảng cách · thể tích · góc", bai_5_khoang_cach_hai_duong_cheo_nhau),
    ("lang-tru-tam-giac-thiet-dien", "Dựng hình · thiết diện", bai_6_lang_tru_tam_giac_thiet_dien),
    ("mat-cau-cat-mat-phang", "Khối cong · cầu, trụ, nón", bai_7_mat_cau_cat_mat_phang),
    ("oxyz-giao-diem-duong-mat", "Quan hệ song song – vuông góc", bai_8_oxyz_giao_diem_duong_mat),
    ("mat-phang-tiep-xuc-mat-cau", "Khối cong · cầu, trụ, nón", bai_9_mat_phang_tiep_xuc_mat_cau),
    ("hinh-non-cat-song-song-day", "Khối cong · cầu, trụ, nón", bai_10_hinh_non_cat_song_song_day),
    ("chop-mat-cau-ngoai-tiep", "Khối cong · cầu, trụ, nón", bai_11_chop_mat_cau_ngoai_tiep),
]


def _dist_sq(a: Vec3, b: Vec3) -> Fraction:
    return _m.norm_sq(b - a)


def _verify_independent_math(sample_id: str, mem: dict[str, Any], scene3d: dict[str, Any]) -> None:
    """Kiểm chứng toán học độc lập trên kết quả thực thi của từng bài."""
    if sample_id == "chop-thiet-dien-ba-diem":
        sec = mem["thiet_dien"]
        pl = mem["mp_MNP"]
        assert sec.is_closed, "Thiết diện hình chóp phải khép kín"
        assert len(sec.polygon) == 5, f"Thiết diện MENPF phải là ngũ giác (5 đỉnh), nhận {len(sec.polygon)}"
        for v in sec.polygon:
            assert pl.signed_eval(v) == 0, f"Đỉnh {v} không thuộc mặt phẳng (MNP)"
        assert mem["E"] == Vec3.of(3, 0, Fraction(3, 2))
        assert mem["F"] == Vec3.of(0, 3, Fraction(3, 2))

    elif sample_id == "lap-phuong-thiet-dien-bat-ky":
        sec = mem["thiet_dien"]
        pl = mem["mp_MNP"]
        assert sec.is_closed, "Thiết diện hình lập phương phải khép kín"
        assert len(sec.polygon) == 6, f"Thiết diện lục giác đều phải có 6 đỉnh, nhận {len(sec.polygon)}"
        for i in range(6):
            u = sec.polygon[i]
            v = sec.polygon[(i + 1) % 6]
            assert pl.signed_eval(u) == 0
            assert _dist_sq(u, v) == Fraction(8, 1), "Các cạnh lục giác đều phải có bình phương độ dài bằng 8"

    elif sample_id == "khoang-cach-diem-mat-phang-nghieng":
        a, h, pl = mem["A"], mem["H"], mem["sbc"]
        assert pl.signed_eval(h) == 0, "Hình chiếu H phải thuộc mặt phẳng (SBC)"
        assert h == Vec3.of(Fraction(12, 5), 0, Fraction(6, 5))
        ah = h - a
        assert ah.dot(mem["B"] - mem["S"]) == 0
        assert ah.dot(mem["C"] - mem["B"]) == 0
        assert _dist_sq(a, h) == Fraction(36, 5)

    elif sample_id == "goc-nhi-dien-hai-mat-phang":
        a, b, c, s, h = mem["A"], mem["B"], mem["C"], mem["S"], mem["H"]
        bc = c - b
        assert (h - a).dot(bc) == 0, "AH phải vuông góc với giao tuyến BC"
        assert (h - s).dot(bc) == 0, "SH phải vuông góc với giao tuyến BC"
        assert mem["cos_nhi_dien"] == Fraction(1, 2), "cos² góc nhị diện [S, BC, A] phải bằng 1/2"

    elif sample_id == "khoang-cach-hai-duong-cheo-nhau":
        ln_sc, ln_bd = mem["sc"], mem["bd"]
        p_foot, q_foot = K.common_perpendicular_feet(ln_sc, ln_bd)
        assert mem["P"] == p_foot == Vec3.of(Fraction(8, 3), Fraction(8, 3), Fraction(4, 3))
        assert mem["Q"] == q_foot == Vec3.of(2, 2, 0)
        pq = q_foot - p_foot
        assert pq.dot(ln_sc.direction) == 0
        assert pq.dot(ln_bd.direction) == 0
        assert _dist_sq(p_foot, q_foot) == Fraction(8, 3)

    elif sample_id == "lang-tru-tam-giac-thiet-dien":
        sec = mem["thiet_dien"]
        pl = mem["mp_NPQ"]
        assert sec.is_closed, "Thiết diện lăng trụ phải khép kín"
        assert len(sec.polygon) == 5, f"Thiết diện MNPQE phải có 5 đỉnh, nhận {len(sec.polygon)}"
        for v in sec.polygon:
            assert pl.signed_eval(v) == 0
        assert mem["M"] == Vec3.of(3, 0, 0)
        assert mem["E"] == Vec3.of(1, 0, 4)

    elif sample_id == "mat-cau-cat-mat-phang":
        c = mem["C"]
        assert c.center == Vec3.of(0, 0, 3)
        assert c.radius_sq == Fraction(16, 1)
        assert _dist_sq(mem["I"], mem["H"]) + c.radius_sq == Fraction(25, 1)

    elif sample_id == "oxyz-giao-diem-duong-mat":
        m = mem["M"]
        pl = mem["mp_P"]
        ln = mem["duong_d"]
        assert m == Vec3.of(Fraction(9, 5), Fraction(9, 5), Fraction(12, 5))
        assert pl.signed_eval(m) == 0
        assert (m - ln.point).cross(ln.direction).is_zero()

    elif sample_id == "mat-phang-tiep-xuc-mat-cau":
        i_pt, a_pt = mem["I"], mem["A"]
        pl = mem["mp_tiep_dien"]
        assert pl.signed_eval(a_pt) == 0, "Tiếp điểm A phải thuộc mặt phẳng tiếp diện (P)"
        assert K.project_point_onto_plane(i_pt, pl) == a_pt, "Hình chiếu của tâm I lên (P) phải trùng tiếp điểm A"
        assert _dist_sq(i_pt, a_pt) == Fraction(25, 1)
        circles = [o for o in scene3d["objects"] if o.get("type") == "circle3"]
        assert len(circles) == 0, "Mặt phẳng tiếp xúc không được sinh đường tròn giao tuyến có bán kính dương"

    elif sample_id == "hinh-non-cat-song-song-day":
        c = mem["C"]
        assert c.center == Vec3.of(0, 0, 4)
        assert c.radius_sq == Fraction(9, 1)
        assert mem["M"] == Vec3.of(3, 0, 4)

    elif sample_id == "chop-mat-cau-ngoai-tiep":
        pts = [mem["A"], mem["B"], mem["C"], mem["D"], mem["S"]]
        center, r_sq = circumscribed_sphere(pts)
        assert mem["I"] == center == Vec3.of(2, 2, 2)
        assert r_sq == Fraction(12, 1)
        for v in pts:
            assert _dist_sq(mem["I"], v) == Fraction(12, 1)


def build_all_advanced_samples() -> list[dict[str, Any]]:
    ra: list[dict[str, Any]] = []
    for ma, nhom, dung in BAI_MAU_NANG_CAO:
        raw_spec, hop_dong = dung()
        spec = SemanticProgramSpec.model_validate(raw_spec)
        spec = hoan_thien_dung_hinh(spec, hop_dong).spec
        env = compile_semantic_program_to_envelope(spec)
        ket = SemanticProgramInterpreter().execute(spec)
        if ket.status != "completed":
            raise RuntimeError(f"DỪNG: {ma} không chạy trọn — {ket.status}")
        sim = build_simulation_state(
            spec,
            ket,
            hop_dong,
            prefer_declared_plane_names=True,
            common_perpendicular_witness=True,
        )
        canh = build_scene3d(sim)
        if not canh["objects"]:
            raise RuntimeError(f"DỪNG: {ma} không dựng ra cảnh 3D nào")
        _verify_independent_math(ma, ket.final_memory, canh)
        env["scene3d"] = canh
        env["domain"] = "geometry"
        env["source"] = "geometry_sample"
        ra.append(
            {
                "id": ma,
                "group": nhom,
                "problemText": spec.description or spec.title,
                "envelope": env,
            }
        )
    return ra


def zero_measure_audit(ra: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every MEASURE event whose exact value is 0 (a certified perpendicularity read as cos² = 0).

    Derived from the built scenes so the sample file stays fully generated; it used to be pasted into the JSON by hand
    (`b5810dcc3`) and was lost on every regeneration. Read by `backend-geometry-contracts.test.ts`.
    """
    audit: list[dict[str, Any]] = []
    for item in ra:
        for ev in item["envelope"]["scene3d"].get("events", []):
            mq = ev.get("measured_quantity")
            if ev.get("action") != "MEASURE" or not isinstance(mq, dict) or mq.get("value") != "0":
                continue
            audit.append({
                "sample_id": item["id"],
                "step_index": ev["step_index"],
                "object": ev["object"],
                "measured_quantity": mq,
                "explanation": ev.get("explanation"),
                "learner_text": ev.get("learner_text"),
            })
    return audit


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ra = build_all_advanced_samples()
    for item in ra:
        canh = item["envelope"]["scene3d"]
        so_do = sum(1 for o in canh["objects"] if o["type"] == "quantity")
        steps = len(canh.get("formation", {}).get("steps", []))
        print(
            f"  {item['id']:36} {len(canh['objects']):3} vật · "
            f"{steps:2} bước dựng · {so_do} số đo"
        )
    RA.parent.mkdir(parents=True, exist_ok=True)
    RA.write_text(
        json.dumps(
            {
                "khai": (
                    "11 bài mẫu hình học không gian THPT nâng cao SINH RA TẤT ĐỊNH từ nhân, "
                    "không viết tay toạ độ kết quả. Sửa `backend/scripts/build_advanced_geometry_samples.py` "
                    "rồi chạy lại."
                ),
                "samples": ra,
                "zero_measure_audit": zero_measure_audit(ra),
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"\n→ {RA.relative_to(REPO_DIR)} · {len(ra)} bài")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
