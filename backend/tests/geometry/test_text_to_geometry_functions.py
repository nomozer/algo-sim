"""Text → typed function calls → dựng tất định → kiểm hình → Scene3D (run `text-to-geometry-functions`). 0 API call.

Đầu ra AI được ĐÓNG VAI bằng fixture gán nhãn trước (`fixtures/text_to_functions_cases.json`); đáp số và độ dài² kỳ
vọng tính tay trước khi có engine. Oracle trong file này đọc Scene3D (toạ độ khung + `chart_metric`) — KHÔNG đọc toạ
độ nội bộ của engine — nên một engine dựng sai mà tự tin vẫn bị bắt.
"""
from __future__ import annotations

import ast
import copy
import json
import random
import re
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.ai import function_route as FR
from app.simulation import geometry_functions as GF
from app.simulation.geometry_functions import engine as EN

CASES = json.loads((Path(__file__).parent / "fixtures" / "text_to_functions_cases.json").read_text(encoding="utf-8"))
BY_ID = {c["id"]: c for c in CASES["cases"]}
_SO = re.compile(r"^(?P<dau>-)?(?P<he>\d+(?:/\d+)?)?(?:√(?P<can>\d+))?(?:/(?P<mau>\d+))?$")


def _khoa(s: str) -> tuple[int, F]:
    """Chuỗi số chính xác → (dấu, giá trị²). Cài riêng trong test — không dùng bộ định dạng của engine."""
    m = _SO.match(s)
    assert m and (m["he"] or m["can"]), s
    he = F(m["he"] or 1) / F(m["mau"] or 1)
    return (-1 if m["dau"] else 1), he * he * int(m["can"] or 1)


def _chay(case: dict):
    return FR.run_function_route(case["text"], {"calls": case["calls"]})


def _scene_points(scene: dict) -> dict[str, tuple[F, F, F]]:
    return {o["id"]: tuple(F(x) for x in o["xyz"]) for o in scene["objects"] if o["type"] == "point3" and "xyz" in o}


def _len_sq(scene: dict, a: str, b: str) -> F:
    P = _scene_points(scene)
    G = [[F(x) for x in r] for r in scene["chart_metric"]]
    d = [P[EN.ir_name(b)][i] - P[EN.ir_name(a)][i] for i in range(3)]
    return sum(d[i] * G[i][j] * d[j] for i in range(3) for j in range(3))


#: The fixture's labels are historical evidence and stay as recorded. Run source-grounding-completeness refuses NEG2
#: one layer earlier: its "có cạnh đáy bằng 2" is a premise no call reads. Same verdict (REFUSED), another code.
MA_HIEN_HANH = {"NEG2": "SOURCE_PREMISE_UNREAD"}
#: Run `source-gate-hardening` (SG-3): "có cạnh đáy bằng 2, chiều cao bằng 3" binds each number to its own role noun, so
#: G7's height quote is no longer ambiguous — side 2, height 3 ⇒ V = (3√3/2 · 2²) · 3 = 18√3 (hand-derived).
KET_CUC_HIEN_HANH = {"G7_AMBIGUOUS_VALUE_QUOTE": {"status": "SERVED", "answers": {"c4": "18√3"}}}


# ── mọi ca fixture: kết cục + mã + đáp số chính xác ─────────────────────────
@pytest.mark.parametrize("cid", sorted(BY_ID))
def test_ket_cuc_dung_nhan(cid):
    c = BY_ID[cid]
    e = KET_CUC_HIEN_HANH.get(cid, c["expect"])
    r = _chay(c)
    assert r.status == e["status"], (r.code, r.reason)
    if r.status == "REFUSED":
        assert r.code == MA_HIEN_HANH.get(cid, e["code"]), r.reason
        assert r.scene3d is None and not r.answers
        return
    for call_id, nhan in e["answers"].items():
        may = r.answers[call_id]
        if nhan.startswith("cos²="):
            assert may == nhan
        else:
            assert _khoa(may) == _khoa(nhan), (call_id, may, nhan)


@pytest.mark.parametrize("cid", sorted(k for k, c in BY_ID.items() if c["expect"].get("lengths_sq")))
def test_oracle_doc_lap_tren_scene3d(cid):
    """Độ dài² tính tay = độ dài² đọc từ Scene3D dưới `chart_metric` — kiểm cả bố cục lẫn cảnh xuất ra."""
    c = BY_ID[cid]
    r = _chay(c)
    assert r.status == "SERVED"
    for seg, nhan in c["expect"]["lengths_sq"].items():
        a, b = re.findall(r"[A-Z]'?", seg)
        assert _len_sq(r.scene3d, a, b) == F(nhan), seg


def test_khong_suy_chan_duong_cao_thanh_tam_day():
    """`SA ⊥ (ABC)` ⇒ chân là A (đỉnh đáy), KHÔNG phải tâm — dù thể tích trùng với chóp đều cùng kích thước."""
    r = _chay(BY_ID["PYR1"])
    P = r.points
    assert P["S"][:2] == P["A"][:2] and P["S"][2] != 0
    reg = FR.run_function_route(
        "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 4, chiều cao bằng 3. Tính thể tích khối chóp S.ABC.",
        {"calls": [
            {"id": "c1", "fn": "regular_pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]},
             "source": {"quote": "hình chóp tam giác đều S.ABC"}},
            {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C"], "side": "4"},
             "source": {"quote": "tam giác đều S.ABC có cạnh đáy bằng 4"}},
            {"id": "c3", "fn": "height", "args": {"solid": "S.ABC", "value": "3"}, "source": {"quote": "chiều cao bằng 3"}},
            {"id": "c4", "fn": "ask_volume", "args": {"solid": "S.ABC"}, "source": {"quote": "Tính thể tích khối chóp S.ABC"}},
        ]})
    assert reg.status == "SERVED" and _khoa(reg.answers["c4"]) == _khoa("4√3")
    assert _len_sq(r.scene3d, "S", "B") == 25
    assert _len_sq(reg.scene3d, "S", "B") == 9 + F(16, 3)       # h² + R², R² = b²/3


# ── thứ tự dựng: phụ thuộc, không phụ thuộc thứ tự lời gọi ───────────────────
def _thu_tu(r) -> list[str]:
    return [s["object"] for s in r.trace if s["step"] == "place_point"]


def test_thu_tu_dung_theo_phu_thuoc():
    t = _thu_tu(_chay(BY_ID["COMP3"]))
    assert t.index("H") > max(t.index(x) for x in "AB") and t.index("S") > t.index("H")
    t = _thu_tu(_chay(BY_ID["COMP1"]))
    assert t.index("M") > t.index("S") > max(t.index(x) for x in "ABC")


@pytest.mark.parametrize("cid", ["PYR1", "COMP1", "COMP3", "PRISM1"])
def test_xao_thu_tu_loi_goi_khong_doi_ket_qua(cid):
    goc = _chay(BY_ID[cid])
    for seed in range(5):
        c = copy.deepcopy(BY_ID[cid])
        random.Random(seed).shuffle(c["calls"])
        r = _chay(c)
        assert (r.answers, r.trace, r.program) == (goc.answers, goc.trace, goc.program)


def test_dien_dat_khac_nhau_cung_hinh_cung_dap_so():
    rs = [_chay(BY_ID[k]) for k in ("PYR1", "PYR1_P2", "PYR1_P3")]
    assert len({_khoa(next(iter(r.answers.values()))) for r in rs}) == 1
    cap = [(a, b) for i, a in enumerate("SABC") for b in "SABC"[i + 1:]]
    assert len({tuple(_len_sq(r.scene3d, a, b) for a, b in cap) for r in rs}) == 1


# ── Scene3D ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("cid", sorted(k for k, c in BY_ID.items() if c["expect"]["status"] == "SERVED"))
def test_scene3d_co_khoi_dung_cau_truc_va_metric(cid):
    r = _chay(BY_ID[cid])
    s = r.scene3d
    assert "chart_metric" in s
    khoi = [o for o in s["objects"] if o["type"] == "solid"]
    assert khoi
    for o in khoi:
        n_v, n_f = len(o["vertices"]), len(o["faces"])
        canh = {frozenset((f[i], f[(i + 1) % len(f)])) for f in o["faces"] for i in range(len(f))}
        assert n_v - len(canh) + n_f == 2                       # Euler
    assert r.kernel_check is True                               # điểm kernel thực thi = bố cục engine


# ── hợp đồng: registry đóng, không toạ độ, có nguồn ─────────────────────────
def test_registry_dong_va_khai_bao_ham_khong_co_toa_do():
    decl = GF.function_declarations()
    # planner-only, never declared: the auxiliary, and `ask_angle_lines` (route B only, goal-directed-function-composition)
    assert {d["name"] for d in decl} == set(GF.REGISTRY) - {"translate_point", "ask_angle_lines", "divide_segment"}
    txt = json.dumps(decl, ensure_ascii=False).lower()
    for cam in ("xyz", "coord", "toạ độ", "tọa độ", "\"x\"", "position"):
        assert cam not in txt, cam
    for d in decl:
        assert d["parameters"]["type"] == "object" and d["description"]


def test_moi_ham_co_tu_khoa_vi_tu_hoac_la_ham_so_lieu():
    for ten, spec in GF.REGISTRY.items():
        # a planner-only auxiliary is bound by its declared decomposition (`_kiem_phu`), not by a predicate keyword
        assert spec.keywords or spec.value_fields or ten == "unsupported" or spec.auxiliary_only, ten


# ── không lùi ngầm về LLM_ONLY, không gọi provider ─────────────────────────
def test_khong_goi_provider_khong_lui_ve_llm_only(monkeypatch):
    from app.ai import gemini, pipeline

    def cam(*a, **k):
        raise AssertionError("đường mới đã gọi provider")

    monkeypatch.setattr(gemini, "call_gemini", cam)
    monkeypatch.setattr(pipeline, "call_gemini", cam)
    monkeypatch.setattr(pipeline, "run_pipeline", cam)
    for c in CASES["cases"]:
        _chay(c)


def _nhap(f: Path) -> set[str]:
    ra = set()
    for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
        if isinstance(n, ast.ImportFrom):
            ra.add(n.module or "")
        elif isinstance(n, ast.Import):
            ra |= {a.name for a in n.names}
    return ra


def test_goi_geometry_functions_khong_import_tang_ai_hay_canh():
    for f in Path(GF.__file__).parent.glob("*.py"):
        for ten in _nhap(f):
            assert not ten.startswith(("app.ai", "app.main")), (f.name, ten)
            assert "scene3d" not in ten and "simulation_state" not in ten, (f.name, ten)


def test_diem_vao_khong_nhap_provider_hay_pipeline_va_mac_dinh_khong_tham_chieu_no():
    nhap = _nhap(Path(FR.__file__))
    assert not {m for m in nhap if m.startswith(("app.ai.gemini", "app.ai.pipeline", "app.main"))}, nhap
    app = Path(FR.__file__).resolve().parents[1]
    for f in (app / "ai" / "pipeline.py", app / "main.py"):
        txt = f.read_text(encoding="utf-8")
        assert "function_route" not in txt and "geometry_functions" not in txt, f.name


# ── primitive bố cục ────────────────────────────────────────────────────────
@pytest.mark.parametrize("k", [3, 4, 6])
def test_da_giac_deu_trong_khung_affine_co_canh_deu(k):
    pts, G2 = EN.regular_polygon_chart(k, F(9))
    d = lambda u, v: sum((u[i] - v[i]) * G2[i][j] * (u[j] - v[j]) for i in range(2) for j in range(2))  # noqa: E731
    assert {d(pts[i], pts[(i + 1) % k]) for i in range(k)} == {F(9)}
    O = tuple(sum(p[i] for p in pts) / k for i in range(2))
    assert len({d(p, O) for p in pts}) == 1                     # nội tiếp đường tròn tâm O


def test_ngu_giac_deu_bi_tu_choi_co_ma():
    with pytest.raises(EN.TuChoi) as e:
        EN.regular_polygon_chart(5, F(4))
    assert e.value.code == "UNSUPPORTED_REGULAR_POLYGON"


def test_tiem_loi_bo_cuc_bi_tu_kiem_bat(monkeypatch):
    """Engine dựng SAI một dữ kiện nó đã dùng để dựng ⇒ ENGINE_SELF_CHECK_FAILED, không phục vụ."""
    goc = EN.regular_polygon_chart

    def sai(k, s2):
        pts, G2 = goc(k, s2)
        return pts, ((G2[0][0] * 2, G2[0][1]), (G2[1][0], G2[1][1]))

    monkeypatch.setattr(EN, "regular_polygon_chart", sai)
    r = _chay(BY_ID["PYR1"])
    assert r.status == "REFUSED" and r.code == "ENGINE_SELF_CHECK_FAILED"
