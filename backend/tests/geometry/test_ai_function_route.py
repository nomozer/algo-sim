"""ai-function-route — diễn đạt nhiều dạng, mở rộng hình học, adapter Gemini function calling (PROVIDER GIẢ). 0 API call.

Fixture tiền đăng ký (`f47c56bb`, commit TRƯỚC khi sửa mã): `fixtures/paraphrase_cases.json`,
`fixtures/geometry_expansion_cases.json`. Lời gọi hàm trong fixture ĐÓNG VAI đầu ra AI (viết tay) ⇒ các test diễn đạt kiểm
đường lời gọi → engine, KHÔNG chứng minh mô hình hiểu câu. Oracle đọc Scene3D + `chart_metric`, không đọc nội bộ engine.
"""
from __future__ import annotations

import ast
import copy
import json
import re
from fractions import Fraction as F
from pathlib import Path

import pytest

from app.ai import function_calling as FC
from app.ai import function_route as FR
from app.simulation import geometry_functions as GF
from app.simulation.geometry_functions import engine as EN

FX = Path(__file__).parent / "fixtures"
PARA = {c["id"]: c for c in json.loads((FX / "paraphrase_cases.json").read_text(encoding="utf-8"))["cases"]}
EXP = {c["id"]: c for c in json.loads((FX / "geometry_expansion_cases.json").read_text(encoding="utf-8"))["cases"]}
OLD = {c["id"]: c for c in json.loads((FX / "text_to_functions_cases.json").read_text(encoding="utf-8"))["cases"]}
_SO = re.compile(r"^(?P<dau>-)?(?P<he>\d+(?:/\d+)?)?(?:√(?P<can>\d+))?(?:/(?P<mau>\d+))?$")


def _khoa(s: str) -> tuple[int, F]:
    m = _SO.match(s)
    assert m and (m["he"] or m["can"]), s
    he = F(m["he"] or 1) / F(m["mau"] or 1)
    return (-1 if m["dau"] else 1), he * he * int(m["can"] or 1)


def _chay(c):
    return FR.run_function_route(c["text"], {"calls": c["calls"]})


def _pts(scene):
    return {o["id"]: tuple(F(x) for x in o["xyz"]) for o in scene["objects"] if o["type"] == "point3" and "xyz" in o}


def _len_sq(scene, a, b):
    P, G = _pts(scene), [[F(x) for x in r] for r in scene["chart_metric"]]
    d = [P[EN.ir_name(b)][i] - P[EN.ir_name(a)][i] for i in range(3)]
    return sum(d[i] * G[i][j] * d[j] for i in range(3) for j in range(3))


#: Fixture labels stay historical. Run `source-gate-hardening` (SG-3) binds each number of "có cạnh đáy bằng 2, chiều cao
#: bằng 3" to its own role noun, so the height quote is no longer ambiguous: hexagonal prism, side 2, height 3 ⇒
#: V = (3√3/2 · 2²) · 3 = 18√3 (hand-derived). Both locked cases share that text and calls.
KET_CUC_HIEN_HANH = {cid: {"status": "SERVED", "answers": {"c4": "18√3"}}
                     for cid in ("N13_HEIGHT_QUOTE_TWO_NUMBERS_NO_LABEL", "G7_AMBIGUOUS_VALUE_QUOTE")}
#: Same verdict (REFUSED), one layer earlier: a sentence with a clause outside the closed role grammar ("AH là đường cao của
#: tam giác ABC", "SA không vuông góc với (ABC)") binds no role value, so the base side is refused at its value
#: (run `source-gate-hardening`, review rounds 3–4).
KET_CUC_HIEN_HANH |= {cid: {"status": "REFUSED", "code": "UNGROUNDED_VALUE"}
                      for cid in ("N03_TRIANGLE_ALTITUDE_NOT_PYRAMID", "N07_NEGATION_OUTSIDE_QUOTE")}


def _kiem(c, r):
    e = KET_CUC_HIEN_HANH.get(c["id"], c["expect"])
    assert r.status == e["status"], (c["id"], r.code, r.reason)
    if r.status == "REFUSED":
        assert r.code == e["code"], (c["id"], r.code, r.reason)
        assert r.scene3d is None and not r.answers
        return
    for cid, nhan in e["answers"].items():
        if isinstance(nhan, dict):                                   # đáp số ký hiệu: coef · a^dim
            ex = r.answer_exact[cid]
            assert ex["dim"] == nhan["dim"] and _khoa(ex["coef"]) == _khoa(nhan["coef"]), (cid, ex, nhan)
        elif nhan.startswith("cos²="):
            assert r.answers[cid] == nhan, (cid, r.answers[cid])
        else:
            assert _khoa(r.answers[cid]) == _khoa(nhan), (cid, r.answers[cid], nhan)
    for seg, v in {**e.get("lengths_sq", {}), **e.get("lengths_sq_in_a2", {})}.items():
        a, b = re.findall(r"[A-Z]'?", seg)
        assert _len_sq(r.scene3d, a, b) == F(v), (c["id"], seg)


# ── E · diễn đạt ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("cid", sorted(PARA))
def test_dien_dat_tien_dang_ky(cid):
    _kiem(PARA[cid], _chay(PARA[cid]))


def test_muoi_cach_viet_cung_mot_quan_he_cho_cung_mot_hinh():
    rs = [_chay(PARA[k]) for k in sorted(PARA) if PARA[k]["group"] == "perpendicular_paraphrase"]
    assert len(rs) == 10 and all(r.status == "SERVED" for r in rs)
    cap = [(a, b) for i, a in enumerate("SABC") for b in "SABC"[i + 1:]]
    assert len({tuple(_len_sq(r.scene3d, a, b) for a, b in cap) for r in rs}) == 1


def test_chuan_hoa_ghi_ro_luat_va_tien_dieu_kien_trong_trace():
    luat = {k: next(s["rule"] for s in _chay(PARA[k]).trace if s.get("object") == "S")
            for k in ("P04_ALTITUDE", "P05_PROJECTION", "P06_TWO_PERPENDICULAR_LINES")}
    assert luat["P04_ALTITUDE"].startswith("altitude")
    assert luat["P05_PROJECTION"].startswith("orthogonal_projection")
    assert luat["P06_TWO_PERPENDICULAR_LINES"].startswith("line_perpendicular_to_two_intersecting_lines")


def test_tien_dieu_kien_chuan_hoa_hong_thi_tu_choi_co_ma():
    """Đường cao phải hạ từ ĐỈNH của chính khối chóp; hình chiếu không trùng điểm — ngữ cảnh không chứng minh ⇒ không chuẩn hoá."""
    c = copy.deepcopy(PARA["P04_ALTITUDE"])
    c["calls"][1]["args"] = {"apex": "A", "foot": "S", "solid": "S.ABC"}
    r = _chay(c)
    assert (r.status, r.code) == ("REFUSED", "PRECONDITION_FAILED"), r.reason
    c = copy.deepcopy(PARA["P05_PROJECTION"])
    c["calls"][1]["args"]["image"] = "S"
    r = _chay(c)
    assert (r.status, r.code) == ("REFUSED", "PRECONDITION_FAILED"), r.reason


# ── F · mở rộng hình học ─────────────────────────────────────────────────────
@pytest.mark.parametrize("cid", sorted(EXP))
def test_mo_rong_tien_dang_ky(cid):
    _kiem(EXP[cid], _chay(EXP[cid]))


def test_do_dai_ky_hieu_khong_bien_a_thanh_du_kien():
    r = _chay(EXP["X01_SYMBOLIC_SQUARE_PYRAMID"])
    assert r.answers["c5"] == "a³√2/3"
    assert r.scene3d["length_unit"]["symbol"] == "a"
    buoc = next(s for s in r.trace if s["step"] == "choose_unit")
    assert buoc["provenance"] == "LAYOUT_DERIVED" and buoc["object"] == "a"
    assert "GIVEN" not in json.dumps(r.program)                         # a = 1 là ĐƠN VỊ dựng, không phải dữ kiện


def test_mat_ben_vuong_goc_day_chan_duong_cao_duoc_DAN_XUAT():
    r2 = _chay(EXP["X02_FACE_PERPENDICULAR_EQUILATERAL"])
    P = r2.points
    assert P["S"][:2] == tuple((P["A"][i] + P["B"][i]) / 2 for i in range(2))   # trung điểm AB: từ SA = SB
    r3 = _chay(EXP["X03_FACE_PERPENDICULAR_FOOT_AT_VERTEX"])
    assert r3.points["S"][:2] == r3.points["A"][:2]                              # 3-4-5: chân tại A, không phải trung điểm
    assert next(s for s in r3.trace if s.get("object") == "S")["rule"].startswith("face_perpendicular_base")


def test_mau_thuan_do_dai_neu_du_hai_menh_de():
    """Hai nguồn độ dài lệch nhau (SAB đều ⇒ SA = AB = a, nhưng đề nói SA = 2a): từ chối nêu CẢ HAI lời gọi."""
    r = _chay(EXP["X08_FACE_PERPENDICULAR_CONTRADICTION"])
    assert r.code == "INCONSISTENT_FACTS" and {"c2", "c3"} <= set(r.failed_calls), r.failed_calls


def test_cu_27_fixture_van_dung_nguyen():
    # labels stay historical; NEG2 is now refused one layer earlier (unread premise) — see test_text_to_geometry_functions
    # run source-gate-hardening: the roles after NEG2's negated clause bind to nothing (see test_text_to_geometry_functions)
    ma_hien_hanh = {"NEG2": "UNGROUNDED_VALUE"}
    for c in OLD.values():
        r = _chay(c)
        e = KET_CUC_HIEN_HANH.get(c["id"], c["expect"])
        ma = ma_hien_hanh.get(c["id"], e.get("code"))
        assert r.status == e["status"] and (r.code == ma if r.status == "REFUSED" else True), c["id"]
        if c["id"] in KET_CUC_HIEN_HANH:
            assert r.answers == e["answers"], (c["id"], r.answers)


# ── D · adapter Gemini function calling (provider giả) ───────────────────────
def _phan_hoi(calls, finish="STOP", usage=None, them=None):
    """Thân phản hồi `generateContent` thật: mọi lời gọi là phần `functionCall` song song trong MỘT ứng viên."""
    parts = [{"functionCall": {"name": c["fn"], "args": {**c["args"], "call_id": c["id"],
                                                         "quotes": c["source"].get("quotes") or [c["source"]["quote"]],
                                                         **({"depends_on": c["depends_on"]} if c.get("depends_on") else {})}}}
             for c in calls]
    body = {"candidates": [{"content": {"role": "model", "parts": parts + (them or [])}, "finishReason": finish}],
            "usageMetadata": usage or {"promptTokenCount": 1200, "candidatesTokenCount": 300, "thoughtsTokenCount": 500,
                                       "totalTokenCount": 2000}}
    return body


class _Gia:
    def __init__(self, body):
        self.body, self.goi, self.payload = body, 0, None

    def __call__(self, payload):
        self.goi += 1
        self.payload = payload
        return copy.deepcopy(self.body)


def test_khai_bao_ham_gemini_dung_tap_con_openapi():
    decl = FC.gemini_function_declarations()
    # the provider sees the library minus planner-only auxiliaries — and exactly these (a new one is a decision)
    # Wave 2A / 2B decisions: `ask_angle_lines`, `divide_segment` are route B only (planner), not offered to route A.
    assert {d["name"] for d in decl} == set(GF.PROVIDER_FUNCTIONS) == set(GF.REGISTRY) - {"translate_point", "ask_angle_lines",
                                                                                         "divide_segment"}
    txt = json.dumps(decl)
    for cam in ('"$ref"', '"$defs"', '"anyOf"', '"title"', '"additionalProperties"', '"xyz"', '"coord'):
        assert cam not in txt, cam
    for d in decl:
        p = d["parameters"]
        assert p["type"] == "OBJECT" and {"call_id", "quotes"} <= set(p["required"]), d["name"]
        loai = re.findall(r'"type": "([^"]+)"', json.dumps(p))
        assert loai and all(t.isupper() for t in loai), (d["name"], loai)


def test_payload_ep_goi_ham_trong_registry_mot_luot_goi():
    p = FC.build_request("đề", mode="ANY")
    cfg = p["toolConfig"]["functionCallingConfig"]
    assert cfg["mode"] == "ANY" and sorted(cfg["allowedFunctionNames"]) == sorted(GF.PROVIDER_FUNCTIONS)
    assert "translate_point" not in cfg["allowedFunctionNames"]
    assert p["generationConfig"]["maxOutputTokens"] == FC.MAX_OUTPUT_TOKENS
    assert len(p["tools"]) == 1 and p["tools"][0]["functionDeclarations"]
    assert FC.build_request("đề", mode="VALIDATED")["toolConfig"]["functionCallingConfig"]["mode"] == "VALIDATED"
    for xau in ("AUTO", "NONE", "any"):
        with pytest.raises(ValueError):
            FC.build_request("đề", mode=xau)


@pytest.mark.parametrize("cid", ["P05_PROJECTION", "N10_MULTI_NUMBER_LABEL_ALIGNED"])
def test_adapter_dau_cuoi_text_den_scene3d(cid):
    c = PARA[cid]
    gia = _Gia(_phan_hoi(c["calls"]))
    r = FC.run_ai_function_route(c["text"], gia)
    assert gia.goi == 1                                                  # MỘT lượt gọi cho cả đề
    _kiem(c, r)
    assert r.ai["n_calls"] == len(c["calls"]) and r.ai["usage"]["totalTokenCount"] == 2000


def test_adapter_dau_cuoi_mo_rong_ky_hieu():
    c = EXP["X02_FACE_PERPENDICULAR_EQUILATERAL"]
    r = FC.run_ai_function_route(c["text"], _Gia(_phan_hoi(c["calls"])))
    _kiem(c, r)


def _ca(cid="P01_CANONICAL"):
    return copy.deepcopy(PARA[cid])


def _ma(body, text=None):
    return FC.run_ai_function_route(text or _ca()["text"], _Gia(body))


def test_adapter_tu_choi_phan_hoi_hong_khong_thuc_thi():
    c = _ca()
    calls = c["calls"]
    assert _ma(_phan_hoi(calls[:2], finish="MAX_TOKENS")).code == "RESPONSE_TRUNCATED"
    assert _ma(_phan_hoi([], finish="MALFORMED_FUNCTION_CALL")).code == "MALFORMED_FUNCTION_CALL"
    assert _ma(_phan_hoi([], them=[{"text": "Thể tích là 4√3"}])).code == "NO_FUNCTION_CALL"
    assert _ma(_phan_hoi(calls, finish="SAFETY")).code == "PROVIDER_REFUSED"
    assert _ma({"promptFeedback": {"blockReason": "SAFETY"}}).code == "PROVIDER_BLOCKED"
    assert _ma({"candidates": []}).code == "NO_CANDIDATE"
    la = copy.deepcopy(calls)
    la[0]["fn"] = "place_point"
    assert _ma(_phan_hoi(la)).code == "SCHEMA_INVALID"
    toa_do = copy.deepcopy(calls)
    toa_do[3]["args"]["apex_xyz"] = [0, 0, 3]
    assert _ma(_phan_hoi(toa_do)).code == "SCHEMA_INVALID"
    body = _phan_hoi(calls)
    del body["candidates"][0]["content"]["parts"][0]["functionCall"]["args"]["quotes"]
    assert _ma(body).code == "SCHEMA_INVALID"
    body = _phan_hoi(calls)
    del body["candidates"][0]["content"]["parts"][0]["functionCall"]["args"]["call_id"]
    assert _ma(body).code == "CALL_ID_MISSING"
    body = _phan_hoi(calls)
    body["candidates"][0]["content"]["parts"][0]["functionCall"].pop("args")
    assert _ma(body).code in ("CALL_ID_MISSING", "SCHEMA_INVALID")


def test_adapter_trung_va_phu_thuoc():
    c = _ca()
    calls = c["calls"]
    trung_id = copy.deepcopy(calls)
    trung_id[1]["id"] = trung_id[0]["id"]
    assert _ma(_phan_hoi(trung_id)).code == "DUPLICATE_CALL_ID"
    y_het = copy.deepcopy(calls) + [copy.deepcopy(calls[2])]
    r = _ma(_phan_hoi(y_het))
    assert r.status == "SERVED" and r.ai["dropped_identical_duplicates"] == 1
    treo = copy.deepcopy(calls)
    treo[3]["depends_on"] = ["c99"]
    assert _ma(_phan_hoi(treo)).code == "DANGLING_DEPENDENCY"
    vong = copy.deepcopy(calls)
    vong[0]["depends_on"], vong[1]["depends_on"] = ["c2"], ["c1"]
    assert _ma(_phan_hoi(vong)).code == "DEPENDENCY_CYCLE"
    dung = copy.deepcopy(calls)
    dung[3]["depends_on"] = ["c1", "c2", "c3"]
    assert _ma(_phan_hoi(dung)).status == "SERVED"


def test_adapter_khong_du_du_kien_va_ngoai_pham_vi_la_tu_choi_co_ma():
    c = _ca()
    # the provider dropped two facts: their premise text is now caught as unread before the engine runs
    # (run source-grounding-completeness; was UNDERDETERMINED_POINT from the engine)
    assert _ma(_phan_hoi(c["calls"][:1] + c["calls"][3:])).code == "SOURCE_PREMISE_UNREAD"
    oos = OLD["OOS1"]
    assert FC.run_ai_function_route(oos["text"], _Gia(_phan_hoi(oos["calls"]))).code == "OUT_OF_SCOPE"


def test_transport_live_bi_khoa_khi_khong_bat_cong(monkeypatch):
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    with pytest.raises(FC.LiveAIDisabled):
        FC.live_transport("FAKEKEY-NOT-USED")(FC.build_request("đề"))


def test_adapter_khong_nhap_pipeline_hay_provider_o_dau_module():
    cay = ast.parse(Path(FC.__file__).read_text(encoding="utf-8"))
    dau = {n.module for n in cay.body if isinstance(n, ast.ImportFrom)} | \
          {a.name for n in cay.body if isinstance(n, ast.Import) for a in n.names}
    assert not {m for m in dau if m and (m.startswith("app.ai.pipeline") or m.startswith("app.ai.gemini") or m == "httpx")}, dau


def test_adapter_khong_lui_ve_llm_only(monkeypatch):
    from app.ai import gemini, pipeline

    def cam(*a, **k):
        raise AssertionError("đã chạm đường LLM_ONLY/provider")

    monkeypatch.setattr(gemini, "call_gemini", cam)
    monkeypatch.setattr(pipeline, "run_pipeline", cam)
    monkeypatch.setattr(pipeline, "stage_semantic_program", cam)
    for c in list(PARA.values()) + list(EXP.values()):
        FC.run_ai_function_route(c["text"], _Gia(_phan_hoi(c["calls"])))
        FC.run_ai_function_route(c["text"], _Gia({"candidates": []}))
