# -*- coding: utf-8 -*-
"""W14 Task 4 Step 0 — kiểm kê S4: mọi chương trình ĐÃ LƯU có `construct_solid`.

0 lượt gọi model, chỉ đọc. Nguồn: sáu họ compiler, corpus gold khoá luận (chương
trình LLM thô đã lưu; P1 cũng là kịch bản thiết diện tier-A), tập demo của
`replay_demo_cases.py`, bài mẫu offline (tĩnh, không qua route — chỉ báo cáo).

Trước khi có bước bổ sung: số khung hôm nay + CẬN TRÊN số bước sẽ chèn (≤ 3 mỗi khối
đa diện phân loại được: đáy, chiều cao hoặc đáy trên, một nhóm cạnh bên). Khi
`semantic_program.formation` đã có: số bước chèn THẬT, khung sau, trạng thái từng khối,
tiến độ thiết diện và đáp số trước/sau. Luật dừng (preregistration §6.4): một chương
trình phục vụ được mà vượt ngân sách trình bày, hoặc tiến độ thiết diện đổi ⇒ STOP.

Chạy từ `backend/` (không ghi đè):
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
    ../docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/s4_inventory.py <out.json>
"""
from __future__ import annotations

import contextlib
import importlib
import json
import sys
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve()
BACKEND = HERE.parents[6] / "backend"
sys.path.insert(0, str(BACKEND))

from app.ai.pipeline import _dung_scene3d  # noqa: E402
from app.simulation.semantic_program.display_names import _phan_loai_khoi  # noqa: E402
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter  # noqa: E402
from app.simulation.semantic_program.pacer import DEFAULT_PRESENTATION_BUDGET  # noqa: E402
from app.simulation.semantic_program.request_contract import RequestContract  # noqa: E402
from app.simulation.semantic_program.scene3d import build_scene3d  # noqa: E402
from app.simulation.semantic_program.simulation_state import build_simulation_state  # noqa: E402
from app.simulation.semantic_program.validator import validate_semantic_program  # noqa: E402
from scripts import replay_demo_cases as RD  # noqa: E402
from scripts import replay_negative_boundaries as RNB  # noqa: E402
from tests.geometry import w14_cases as W  # noqa: E402

CHEN_TOI_DA_MOI_KHOI = 3

#: Producer dựng cảnh KHÔNG qua `_dung_scene3d` — cảnh của chúng không nhận bước bổ
#: sung; không cái nào là bằng chứng dựng hình của W14 (Task 4 Step 3).
PRODUCER_TRUC_TIEP = {
    "backend/scripts/replay_demo_cases.py": "T3 demo replay: ok = cảnh có vật; không phải bằng chứng dựng hình",
    "backend/scripts/build_geometry_samples.py": "bài mẫu offline tĩnh (không qua route); chỉ báo cáo",
    "backend/scripts/build_geometry_demo_artifact.py": "artifact demo lịch sử; không phải bằng chứng W14",
    "backend/scripts/probe_dihedral_synthesis.py": "probe lịch sử; không phải bằng chứng W14",
    "backend/scripts/reanalyze_matrix_offline.py": "phân tích lại ma trận lịch sử; không phải bằng chứng W14",
    "backend/scripts/run_generalization_matrix.py": "đo lịch sử; không phải bằng chứng W14",
    "backend/scripts/run_rectangular_pyramid_live_analyze.py": "lượt live lịch sử; không phải bằng chứng W14",
}


def _formation():
    try:
        return importlib.import_module("app.simulation.semantic_program.formation")
    except ModuleNotFoundError:
        return None


def _nguon() -> list[dict]:
    ra = []
    for ten, f in W.HO.items():
        _t, ct = f()
        ra.append({"source": "compiler_family", "id": ten, "contract": ct,
                   "program": W.chuong_trinh(ct)})
    for cid in sorted(RNB.doc_de_bai()):
        _t, ct, raw = W.gold(cid)
        ra.append({"source": "thesis_gold" + ("+tier_a_cross_section" if cid.startswith("p1_") else ""),
                   "id": cid, "contract": ct, "program": raw})
    for art, cid, _vai, ky in RD.DEMO:
        c = RD._tim(art, cid) or {}
        hd = (c.get("analyze") or {}).get("raw_request_contract")
        ra.append({"source": f"demo_replay:{ky}", "id": cid,
                   "contract": RequestContract.model_validate(hd) if hd else None,
                   "program": c.get("normalized_program")})
    for art, cid, _vai in RD.RUT_GON:
        c = RD._tim(art, cid) or {}
        ra.append({"source": "demo_replay:REDUCED_NO_CONTRACT", "id": cid, "contract": None,
                   "program": c.get("normalized_program")})
    for sid, prog in W.mau_offline_co_khoi():
        ra.append({"source": "offline_sample", "id": sid, "contract": None, "program": prog})
    return ra


def _khoi(sp) -> list[dict]:
    mem = SemanticProgramInterpreter().execute(sp).final_memory
    ra = []
    for s in sp.statements:
        if getattr(s, "kind", None) != "construct_solid":
            continue
        gt = mem.get(s.target_var)
        k = (_phan_loai_khoi(list(gt.vertices), [list(f) for f in gt.faces])
             if type(gt).__name__ == "Polyhedron" else None)
        ra.append({"target_var": s.target_var, "vertices": len(s.vertices), "faces": len(s.faces),
                   "face_table_class_before": None if k is None else k[0]})
    return ra


def _tien_do(sc: dict) -> list:
    return [[(g["object_id"], tuple(g["visible_edge_ids"]), g["closed"], g["fill_visible"])
             for g in s["geometry_progress"]]
            for s in sc["formation"]["steps"] if s["geometry_progress"]]


def _canh_truc_tiep(sp) -> dict:
    return build_scene3d(build_simulation_state(sp, SemanticProgramInterpreter().execute(sp)))


@contextlib.contextmanager
def _khong_bo_sung(F):
    """Route + `_dung_scene3d` như TRƯỚC W14: bước bổ sung thay bằng hàm đồng nhất.
    Chỉ trong phép đo này (chẩn đoán), để trước/sau đo được trong cùng một lượt."""
    from app.simulation.semantic_program import route as R

    def dong_nhat(spec, contract=None):
        return F.KetQuaHoanThien(spec, (), F._sha(spec), F._sha(spec))

    with mock.patch.object(R, "hoan_thien_dung_hinh", dong_nhat), \
            mock.patch.object(F, "hoan_thien_dung_hinh", dong_nhat):
        yield


def _dong(n: dict, F) -> dict:
    row = {"source": n["source"], "id": n["id"], "routed": n["contract"] is not None}
    if not n["program"]:
        return row | {"status": "NO_PROGRAM"}
    v = validate_semantic_program(n["program"])
    if not v.ok:
        return row | {"status": "SCHEMA_INVALID"}
    sp = v.spec
    kinds = [getattr(s, "kind", None) for s in sp.statements]
    if "construct_solid" not in kinds:
        return row | {"status": "NO_POLYHEDRAL_SOLID"}
    try:
        row["solids"] = _khoi(sp)
    except Exception as e:  # noqa: BLE001 — chương trình không chạy nổi vẫn qua route (bị từ chối)
        row["solids"] = [{"target_var": s.target_var, "vertices": len(s.vertices), "faces": len(s.faces),
                          "face_table_class_before": f"UNAVAILABLE_EXECUTION_ERROR:{type(e).__name__}"}
                         for s in sp.statements if getattr(s, "kind", None) == "construct_solid"]
    row["has_section"] = "construct_section" in kinds
    phan_loai = sum(1 for k in row["solids"] if k["face_table_class_before"])
    row["upper_bound_inserted_steps"] = CHEN_TOI_DA_MOI_KHOI * phan_loai
    if n["contract"] is not None:
        with (_khong_bo_sung(F) if F else contextlib.nullcontext()):
            sp_, out, sc = W.chay(n["contract"], n["program"])
        row |= {"served_before": out.servable, "stage_before": out.stage_reached,
                "reason_before": out.reason_code, "frames_before": out.frame_count}
        canh = sc if sc is not None else None
    else:
        canh = _canh_truc_tiep(sp)
        row["frames_before"] = len(canh["formation"]["steps"])
    fb = row.get("frames_before")
    row["within_budget_upper_bound"] = (None if fb is None
                                        else fb + row["upper_bound_inserted_steps"] <= DEFAULT_PRESENTATION_BUDGET)
    if F is None:
        return row | {"after": "PENDING_COMPLETION_PASS"}
    kq = F.hoan_thien_dung_hinh(sp, n["contract"])
    row["completion_statuses"] = dict(kq.trang_thai_theo_khoi)
    if n["contract"] is None:
        return row | {"after": "NOT_ROUTED (production never completes this program)"}
    _sp2, out2, sc2 = W.chay(n["contract"], n["program"])
    row |= {"served_after": out2.servable, "stage_after": out2.stage_reached,
            "frames_after": out2.frame_count,
            "inserted_steps": (None if out2.frame_count is None or fb is None else out2.frame_count - fb),
            "within_budget": (None if out2.frame_count is None
                              else out2.frame_count <= DEFAULT_PRESENTATION_BUDGET)}
    if out.final_memory is not None and out2.final_memory is not None:
        row["answers_unchanged"] = {k: str(v) for k, v in out.final_memory.items()} == \
                                   {k: str(out2.final_memory[k]) for k in out.final_memory}
    if canh is not None and sc2 is not None and row["has_section"]:
        row["section_progress_unchanged"] = _tien_do(canh) == _tien_do(sc2)
    return row


def run() -> dict:
    F = _formation()
    rows = [_dong(n, F) for n in _nguon()]
    stop = [r["id"] for r in rows if r.get("served_after") and (
        r.get("within_budget") is False or r.get("section_progress_unchanged") is False
        or r.get("answers_unchanged") is False)]
    stop_truoc = [r["id"] for r in rows if r.get("served_before") and r.get("within_budget_upper_bound") is False]
    return {
        "inventory": "W14_S4_INVENTORY",
        "measurement_class": "OFFLINE_STORED_PROGRAM_INVENTORY",
        "model_calls": 0,
        "presentation_budget": DEFAULT_PRESENTATION_BUDGET,
        "phase": "AFTER_COMPLETION_PASS" if F else "BEFORE_COMPLETION_PASS",
        "before_definition": (
            "the SAME stored program through the route with the completion pass replaced by the "
            "identity, in-process; for compiler families that is the W14 compiler output without "
            "completion (pre-W14 parity is the job of test_formation_plan_parity and "
            "S4_INVENTORY_BEFORE.json)") if F else "the route as it was before W14 product edits",
        "direct_scene_producers": PRODUCER_TRUC_TIEP,
        "rows": rows,
        "upper_bound_budget_risk": stop_truoc,
        "stop_rows": stop,
        "verdict": "STOP" if stop else ("OK" if F else "OK_UPPER_BOUND" if not stop_truoc else "BUDGET_RISK"),
    }


if __name__ == "__main__":
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}; pass a new output path")
    out.write_text(json.dumps(run(), ensure_ascii=False, indent=2, default=str) + "\n",
                   encoding="utf-8", newline="\n")
    print(out)
