# -*- coding: utf-8 -*-
"""G05 real-model pilot — DỰNG LẠI Scene3D OFFLINE từ artifact của lượt đo (G4). offline · **0 API call**.

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/g05_pilot_scene_replay.py <thư mục lượt>

`mot_luot` ghi hợp đồng + chương trình mô hình viết, không ghi envelope. Cảnh được dựng lại TẤT ĐỊNH bằng chính
`pipeline._dung_scene3d(spec, contract)` (metric khung dẫn xuất từ đề nằm trong đó), rồi kiểm — KHÔNG mặc định cảnh dựng
được là cảnh đúng:
· cấu trúc: một khối; số đỉnh/mặt/cạnh theo họ; Euler 2; mỗi cạnh đúng hai mặt; định hướng nhất quán được; không mặt
  suy biến;
· hình học CHÍNH XÁC trên toạ độ khung với metric `chart_metric` (đồng nhất nếu không có): cạnh đáy² = b², đáy đều
  (bán kính ngoại tiếp² theo k), chiều cao² = h² và vuông góc đáy (chóp: đỉnh trên pháp tuyến qua tâm; lăng trụ: mặt
  trên tịnh tiến, cạnh bên ⊥ mọi cạnh đáy); tứ diện đều: sáu cạnh² = b². b, h lấy từ KÍCH THƯỚC CỦA ĐỀ trong corpus.
Cảnh ghi ra `<thư mục lượt>/scenes/<id>.json` để kiểm biến đổi renderer bằng chính `veKhongGian` của frontend
(`runs/g05-real-model-pilot/scene_world_check.ts`).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from fractions import Fraction
from itertools import combinations
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

_spec = importlib.util.spec_from_file_location("_g05r_scoring", Path(__file__).resolve().parent / "g05_pilot_scoring.py")
SC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SC)

_SO_KHOI = {("prism", 3): (6, 5, 9), ("prism", 6): (12, 8, 18), ("pyramid", 3): (4, 4, 6), ("pyramid", 6): (7, 7, 12),
            ("tetrahedron", 3): (4, 4, 6)}


def _dinh_huong_duoc(faces: list[list[int]]) -> bool:
    """Lật mặt theo BFS sao cho mỗi cạnh chung được đi hai chiều ngược nhau; xung đột ⇒ không định hướng được."""
    def canh(f, lat):
        e = [(f[i], f[(i + 1) % len(f)]) for i in range(len(f))]
        return {(b, a) for a, b in e} if lat else set(e)
    lat, hang = {0: False}, [0]
    while hang:
        i = hang.pop()
        for j, g in enumerate(faces):
            if j == i or not ({frozenset(e) for e in canh(faces[i], False)} & {frozenset(e) for e in canh(g, False)}):
                continue
            can_lat = bool(canh(faces[i], lat[i]) & canh(g, False))
            if j not in lat:
                lat[j] = can_lat
                hang.append(j)
            elif lat[j] != can_lat:
                return False
    return len(lat) == len(faces)


def _sub(p, q):
    return tuple(a - b for a, b in zip(p, q))


def _dot(G, u, v):
    return sum(u[r] * G[r][c] * v[c] for r in range(3) for c in range(3))


def _kiem_hinh(case: dict, V: list, faces: list, G) -> dict[str, bool]:
    k, fam = case["k"], case["family"]
    b2 = SC.binh_phuong(case["base_side"])
    n2 = lambda u: _dot(G, u, u)  # noqa: E731
    if fam == "tetrahedron":
        return {"six_edges_b2": {n2(_sub(V[i], V[j])) for i, j in combinations(range(len(V)), 2)} == {b2}}
    h2 = SC.chieu_cao_binh_phuong(case)
    r2 = b2 if k == 6 else b2 / 3
    kq: dict[str, bool] = {}
    if fam == "prism":
        day = [f for f in faces if len(f) == k]
        if k == 4 or len(day) != 2:
            return {"two_k_faces": False}
        A, B = day
        canh_ben = {}
        for f in faces:
            if len(f) == 4:
                for i in range(4):
                    p, q = f[i], f[(i + 1) % 4]
                    if (p in A) != (q in A):
                        canh_ben[p if p in A else q] = q if p in A else p
        vec = {_sub(V[canh_ben[p]], V[p]) for p in A if p in canh_ben}
        kq["translation"] = len(canh_ben) == k and len(vec) == 1
        v = next(iter(vec)) if vec else (0, 0, 0)
        kq["sides_b2"] = all(n2(_sub(V[f[(i + 1) % k]], V[f[i]])) == b2 for f in (A, B) for i in range(k))
        kq["lateral_perp_base"] = all(_dot(G, v, _sub(V[A[(i + 1) % k]], V[A[i]])) == 0 for i in range(k))
        kq["height_h2"] = h2 is not None and n2(v) == h2
        O = tuple(sum(V[p][j] for p in A) / k for j in range(3))
        kq["regular_circumradius"] = all(n2(_sub(V[p], O)) == r2 for p in A)
        return kq
    # chóp: thử từng đỉnh làm đỉnh chóp (đáy tam giác: mọi mặt đều là tam giác)
    for s in range(len(V)):
        day = [f for f in faces if len(f) == k and s not in f]
        if len(day) != 1:
            continue
        A = day[0]
        O = tuple(sum(V[p][j] for p in A) / k for j in range(3))
        so = _sub(V[s], O)
        thu = {"sides_b2": all(n2(_sub(V[A[(i + 1) % k]], V[A[i]])) == b2 for i in range(k)),
               "regular_circumradius": all(n2(_sub(V[p], O)) == r2 for p in A),
               "apex_on_normal": all(_dot(G, so, _sub(V[A[(i + 1) % k]], V[A[i]])) == 0 for i in range(k)),
               "height_h2": h2 is not None and n2(so) == h2}
        if all(thu.values()):
            return thu
        kq = kq or thu
    return kq or {"apex_found": False}


def kiem_mot(out_dir: Path, case: dict) -> dict:
    """Dựng lại cảnh của một đề từ `{id}-lan1.json` và kiểm. Trả `{"id", "ok", "checks", "chart_metric", "reason"}`."""
    from app.ai.pipeline import _dung_scene3d
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.request_contract import RequestContract

    d = json.loads((Path(out_dir) / f"{case['id']}-lan1.json").read_text(encoding="utf-8"))
    ra = {"id": case["id"], "ok": False, "checks": {}, "chart_metric": None, "reason": None}
    if not d.get("request_contract") or not d.get("generated_program"):
        ra["reason"] = "artifact thiếu hợp đồng/chương trình"
        return ra
    scene = _dung_scene3d(SemanticProgramSpec.model_validate(d["generated_program"]),
                          RequestContract.model_validate(d["request_contract"]))
    (Path(out_dir) / "scenes").mkdir(exist_ok=True)
    (Path(out_dir) / "scenes" / f"{case['id']}.json").write_text(json.dumps(scene, ensure_ascii=False, default=str),
                                                                 encoding="utf-8")
    ra["chart_metric"] = "chart_metric" in scene
    khoi = [o for o in scene.get("objects", []) if o.get("type") == "solid"]
    if len(khoi) != 1:
        ra["reason"] = f"{len(khoi)} khối"
        return ra
    s = khoi[0]
    faces = s["faces"]
    try:
        V = [tuple(Fraction(str(x)) for x in p) for p in s["vertices"]]
        G = ([[Fraction(str(x)) for x in r] for r in scene["chart_metric"]] if "chart_metric" in scene
             else [[Fraction(int(i == j)) for j in range(3)] for i in range(3)])
    except (ValueError, ZeroDivisionError) as e:
        ra["reason"] = f"toạ độ/metric không hữu tỉ: {e}"
        return ra
    canh = Counter(frozenset((f[i], f[(i + 1) % len(f)])) for f in faces for i in range(len(f)))
    mong = _SO_KHOI.get((case["family"], case["k"]))
    c = {"counts": mong == (len(V), len(faces), len(canh)), "euler": len(V) - len(canh) + len(faces) == 2,
         "edge_two_faces": all(n == 2 for n in canh.values()), "orientable": _dinh_huong_duoc(faces),
         "non_degenerate": not any(len(set(f)) != len(f) or len(f) < 3 for f in faces)}
    c.update(_kiem_hinh(case, V, faces, G))
    ra["checks"], ra["ok"] = c, all(c.values())
    return ra


def kiem_tat_ca(out_dir: Path, cases: list[dict]) -> dict:
    """Mọi đề ĐƯỢC PHỤC VỤ (theo sidecar) của một lượt."""
    rows = []
    for c in cases:
        p = Path(out_dir) / f"{c['id']}-lan1.pilot.json"
        if p.exists() and json.loads(p.read_text(encoding="utf-8")).get("envelope_status") == "ok":
            rows.append(kiem_mot(out_dir, c))
    return {"checked": len(rows), "ok": sum(r["ok"] for r in rows), "rows": rows}


if __name__ == "__main__":
    _r = importlib.util.spec_from_file_location("_g05r_runner", Path(__file__).resolve().parent /
                                                "run_g05_real_model_pilot.py")
    R = importlib.util.module_from_spec(_r)
    _r.loader.exec_module(R)
    kq = kiem_tat_ca(Path(sys.argv[1]), R.nap_corpus())
    print(json.dumps(kq, ensure_ascii=False, indent=1, default=str))
    raise SystemExit(0 if kq["ok"] == kq["checked"] else 1)
