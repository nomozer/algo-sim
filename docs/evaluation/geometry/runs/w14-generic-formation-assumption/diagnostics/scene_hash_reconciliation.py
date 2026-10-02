# -*- coding: utf-8 -*-
"""W14 — đối soát băm cảnh/bộ nhớ cuối của p1/p6 (`test_memory_declaration_contract_alignment`).

0 lượt gọi model (provider phát lại + NetworkGuard). Chứng minh diff CHỈ là phần W14 đã khai:
với bước bổ sung dựng hình thay bằng hàm đồng nhất VÀ bỏ ba trường vai trò
(`formation_roles`, `shape_class`, `formation_requirements`), cảnh băm đúng hằng đã ghim; bộ
nhớ cuối W14, chỉ xét các khoá có trước, băm đúng hằng đã ghim. Chạy từ `backend/` (không ghi đè):
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
    ../docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/scene_hash_reconciliation.py <out.json>
"""
from __future__ import annotations

import asyncio
import contextlib
import copy
import json
import sys
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[6] / "backend"))

from app.ai import pipeline as PL  # noqa: E402
from app.simulation.semantic_program import formation as F  # noqa: E402
from app.simulation.semantic_program import route as R  # noqa: E402
from app.simulation.semantic_program import validator as V  # noqa: E402
from tests.semantic_program import test_memory_declaration_contract_alignment as M  # noqa: E402

TRUONG_W14 = ("formation_roles", "shape_class", "formation_requirements")


def _bo_w14(sc: dict) -> dict:
    sc = copy.deepcopy(sc)
    for o in sc["objects"]:
        for k in TRUONG_W14:
            o.pop(k, None)
    for s in sc["formation"]["steps"]:
        s.pop("formation_roles", None)
    return sc


@contextlib.contextmanager
def _khong_bo_sung():
    def dong_nhat(spec, contract=None):
        return F.KetQuaHoanThien(spec, (), F._sha(spec), F._sha(spec))

    with mock.patch.object(R, "hoan_thien_dung_hinh", dong_nhat), \
            mock.patch.object(F, "hoan_thien_dung_hinh", dong_nhat):
        yield


def _envelope(cid: str) -> dict:
    raw = {**M.RNB.doc_raw_theo_thu_tu(cid), "semantic_program": [json.dumps(M._prog(cid), ensure_ascii=False)]}
    with mock.patch.object(PL, "call_gemini", M.RNB.ProviderPhatLaiTheoThuTu(raw)), M.RNB.NetworkGuard() as g:
        env = asyncio.run(PL.run_pipeline(M.RNB.doc_de_bai()[cid], "REPLAY_KHONG_PHAI_KEY", semantic_route="serve"))
    assert not g.attempts
    return env


def _bo_nho(cid: str) -> dict:
    v = V.validate_semantic_program(M._prog(cid))
    o = R.verify_and_compile(M._hd(cid), v.spec)
    assert o.servable
    return o.final_memory


def run() -> dict:
    ket = {}
    for cid in (M.CA_P1, M.CA_P6):
        with _khong_bo_sung():
            tat, mem_tat = _envelope(cid), _bo_nho(cid)
        bat, mem_bat = _envelope(cid), _bo_nho(cid)
        goc = {o["id"] for o in tat["scene3d"]["objects"]}
        ket[cid] = {
            "status_without_completion": tat["status"], "status_w14": bat["status"],
            "scene_hash_pinned": M.SCENE_START[cid],
            "scene_hash_without_completion_and_role_fields": M._bam(_bo_w14(tat["scene3d"])),
            "scene_hash_w14": M._bam(bat["scene3d"]),
            "objects_pinned": M.SO_VAT_START[cid],
            "objects_w14": len(bat["scene3d"]["objects"]),
            "objects_added_by_completion": [
                {"id": o["id"], "type": o["type"],
                 "vertices": sorted(o.get("endpoint_ids") or o.get("vertex_ids") or []),
                 "formation_roles": o.get("formation_roles")}
                for o in bat["scene3d"]["objects"] if o["id"] not in goc],
            "formation_steps": [len(tat["scene3d"]["formation"]["steps"]),
                                len(bat["scene3d"]["formation"]["steps"])],
            "final_memory_hash_pinned": M.FINAL_MEMORY_START[cid],
            "final_memory_hash_without_completion": M._bam(mem_tat),
            "final_memory_hash_w14": M._bam(mem_bat),
            "final_memory_hash_w14_original_keys": M._bam({k: v for k, v in mem_bat.items() if k in mem_tat}),
            "final_memory_keys_added": sorted(set(mem_bat) - set(mem_tat)),
        }
        r = ket[cid]
        r["diff_is_only_declared_w14_change"] = (
            r["scene_hash_without_completion_and_role_fields"] == r["scene_hash_pinned"]
            and r["final_memory_hash_without_completion"] == r["final_memory_hash_pinned"]
            and r["final_memory_hash_w14_original_keys"] == r["final_memory_hash_pinned"])
    return {"reconciliation": "W14_SCENE_HASH_RECONCILIATION", "model_calls": 0,
            "test": "backend/tests/semantic_program/test_memory_declaration_contract_alignment.py",
            "cases": ket}


if __name__ == "__main__":
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}; pass a new output path")
    out.write_text(json.dumps(run(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(out)
