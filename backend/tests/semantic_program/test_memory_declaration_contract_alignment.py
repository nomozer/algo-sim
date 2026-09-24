# -*- coding: utf-8 -*-
"""Hợp đồng `memory_declarations[]` — Pydantic · lược đồ xuất · thẻ văn phạm · validator · phản hồi sửa. 0 lượt gọi mạng.

SYNTHESIS_MEMORY_DECLARATION_SCHEMA_PROMPT_ALIGNMENT (2026-09-15). Lượt C02 thật: synthesis lượt đầu đặt `at` trong
`memory_declarations[0]` → `PROGRAM_SCHEMA` / `SCHEMA_SILENTLY_DROPPED_KEY` → lượt sửa được nhận (5434 + 4586 token).
Cổng đã chặn đúng; thứ thiếu là hợp đồng nói chưa đủ rõ và phản hồi chưa máy-đọc-được.

⚠️ FIXTURE DẪN XUẤT, KHÔNG PHẢI CANDIDATE THẬT (quyết định của user). Runner chỉ lưu BĂM của candidate synthesis,
nên ca bị loại được DỰNG từ chương trình synthesis đóng băng p6 (đề của C02, byte replay thesis-final) bằng đúng
phép nhầm ô mà trace thật ghi: `memory_declarations[0].initial_value` → `memory_declarations[0].at`. Băm canonical
của bản dẫn xuất KHÁC bản thật (`12f3b31d…`) — test không tuyên bố điều ngược lại.

Chính sách validator GIỮ detector trước Pydantic (không `extra="forbid"`): phép đo bác-mọi-khoá-lạ làm đỏ 11 test
(replay đóng băng p4/p5, mọi chương trình AI lịch sử mang `label`). Khoá mang dữ liệu bị BÁC; khoá trang trí không bác
nhưng được BÁO (`ValidationResult.ignored_keys` + sự kiện observer) — không khoá nào còn bị bỏ im lặng.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from pathlib import Path

import pytest

from app.ai import pipeline as PL
from app.simulation.semantic_program import contract as C
from app.simulation.semantic_program import validator as V
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC
from app.simulation.semantic_program.grammar_card import grammar_card, manh_hop_dong
from app.simulation.semantic_program.route import verify_and_compile
from tests.test_photo_problem_live_runner import (  # noqa: F401 — kho/de/_khong_cho_backoff là fixture
    CA_P1,
    CA_P6,
    RNB,
    R,
    _chay,
    _json,
    _khong_cho_backoff,
    _kich_ban,
    de,
    kho,
)

GOC = Path(__file__).resolve().parents[3]
SCHEMA = GOC / "docs" / "schemas" / "semantic_program.schema.json"
SKILLS = GOC / "backend" / "app" / "ai" / "skills"
MA = "SCHEMA_SILENTLY_DROPPED_KEY"
CON_TRO = "/memory_declarations/0/at"
AN_O_HINH_HOC = {"element_type", "key_type", "val_type"}
CAU_KHOA_DUNG = "mỗi mục có ĐÚNG các khoá này"

#: Đo tại START_HEAD e51901d trên fixture dẫn xuất: lời từ chối cũ 331 byte, mảnh hợp đồng 1587 byte.
LOI_CU_BYTE, MANH_CU_BYTE = 331, 1587
#: Hành vi tại START_HEAD e51901d (không đổi sau wave): băm final_memory (verify_and_compile) và scene3d (run_pipeline).
FINAL_MEMORY_START = {CA_P1: "c934b0233a05aec912717254b8c21c9ac3a50923ecd01d522fabd748cdc3cbc0",
                      CA_P6: "79cf15e958f71915d648df38cbd4bed1f5d3b6356a3cfe8776d852106112c69b"}
SCENE_START = {CA_P1: "829f70b2da93d2bd4ab2467d70c58b4b9f01e69d83a5b429bb053233872c9f01",
               CA_P6: "db1e31ec772147ff0df7a886cfc8982bd55ac2a51f588b4d4ed078ec3a66bf0f"}
SO_VAT_START = {CA_P1: 13, CA_P6: 7}


def _bam(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                                     default=str).encode("utf-8")).hexdigest()


def _prog(cid: str) -> dict:
    return json.loads(RNB.doc_raw_theo_thu_tu(cid)["semantic_program"][0])


def _hd(cid: str):
    raw = RNB.doc_raw_theo_thu_tu(cid)
    return build_request_contract(json.loads(raw["semantic_analyze"][0]), problem_text=RNB.doc_de_bai()[cid],
                                  domain=DOMAIN_HINH_HOC)


def _c02_bi_loai_dan_xuat() -> dict:
    d = _prog(CA_P6)
    d["memory_declarations"][0]["at"] = d["memory_declarations"][0].pop("initial_value")
    return d


def _final_memory(cid: str, prog: dict) -> str:
    v = V.validate_semantic_program(prog)
    assert v.ok, v.error
    o = verify_and_compile(_hd(cid), v.spec)
    assert o.servable
    return _bam(o.final_memory)


def _envelope(monkeypatch, cid: str, synthesis: list[str]) -> dict:
    raw = {**RNB.doc_raw_theo_thu_tu(cid), "semantic_program": list(synthesis)}
    monkeypatch.setattr(PL, "call_gemini", RNB.ProviderPhatLaiTheoThuTu(raw))
    with RNB.NetworkGuard() as g:
        env = asyncio.run(PL.run_pipeline(RNB.doc_de_bai()[cid], "REPLAY_KHONG_PHAI_KEY", semantic_route="serve"))
    assert not g.attempts
    return env


def _dong_the_khai_bao() -> str:
    return next(x for x in grammar_card(DOMAIN_HINH_HOC).splitlines() if x.startswith("memory_declarations[]: "))


def _khoa_trong_dong_the(dong: str) -> list[str]:
    phan = dong.split(": ", 1)[1].split(" — ")[0]
    return re.findall(r"(?:(?<=\s)|^)([a-z][a-z_]*)\??(?=[:\s(]|$)", phan)


# ── A ───────────────────────────────────────────────────────────────────────
def test_A_C02_dan_xuat__at_trong_khai_bao_BI_TU_CHOI_dung_pha_va_ma_on_dinh():
    hong = _c02_bi_loai_dan_xuat()
    v = V.validate_semantic_program(hong)
    assert v.ok is False
    pl = R.phan_loai_ung_vien(json.dumps(hong, ensure_ascii=False), _hd(CA_P6))
    assert (pl["phase"], pl["code"]) == ("PROGRAM_SCHEMA", MA)
    assert pl["message"] == v.error
    assert v.error.startswith(f"Lỗi cú pháp schema SemanticProgramSpec: [{MA}] ")


# ── B ───────────────────────────────────────────────────────────────────────
def _ignored(v) -> list[dict]:
    return list(getattr(v, "ignored_keys", None) or [])


@pytest.mark.parametrize("ten, sua, chan", [
    ("at_mang_toa_do", lambda d: d.__setitem__("at", d.pop("initial_value")), True),
    ("khoa_bia_nuot_du_kien", lambda d: (d.pop("initial_value"), d.__setitem__("toa_do_bia", [1, 2, 3])), True),
    ("label_trang_tri", lambda d: d.__setitem__("label", "điểm gốc"), False),
    ("ghi_chu_khi_da_co_gia_tri", lambda d: d.__setitem__("ghi_chu_rieng", "abc"), False),
])
def test_B_KHONG_khoa_la_nao_bi_bo_IM_LANG__bac_hoac_bao(ten, sua, chan):
    d = _prog(CA_P6)
    truoc = set(d["memory_declarations"][0])
    sua(d["memory_declarations"][0])
    khoa = sorted(set(d["memory_declarations"][0]) - truoc - set(C.MemoryDeclaration.model_fields))
    assert khoa, "tiền đề: có khoá lạ"
    v = V.validate_semantic_program(d)
    for k in khoa:
        con_tro = f"/memory_declarations/0/{k}"
        if chan:
            assert v.ok is False and con_tro in v.error
        else:
            assert v.ok is True
            assert {"pointer": con_tro, "key": k} in _ignored(v)


def test_B2_moi_chuong_trinh_replay_DUOC_NHAN__moi_khoa_la_deu_duoc_BAO():
    da_xet = 0
    for cid in RNB.doc_de_bai():
        try:
            raws = RNB.doc_raw_theo_thu_tu(cid).get("semantic_program") or []
        except Exception:  # noqa: BLE001 — ca không có bản ghi synthesis
            continue
        for raw in raws:
            try:
                d = json.loads(raw)
            except ValueError:
                continue
            v = V.validate_semantic_program(d)
            if not v.ok:
                continue
            la = {(f"/memory_declarations/{i}/{k}", k) for i, m in enumerate(d.get("memory_declarations") or [])
                  if isinstance(m, dict) for k in set(m) - set(C.MemoryDeclaration.model_fields)}
            assert la == {(x["pointer"], x["key"]) for x in _ignored(v)}, cid
            da_xet += 1
    assert da_xet >= 3


# ── C ───────────────────────────────────────────────────────────────────────
def test_C_loi_neu_MA_CON_TRO_KHOA_SAI_va_KHOA_HOP_LE__khong_mang_noi_dung_ung_vien():
    hong = _c02_bi_loai_dan_xuat()
    e = V.validate_semantic_program(hong).error
    assert f"[{MA}] {CON_TRO}: `at`" in e
    assert "Khoá hợp lệ: " + ", ".join(C.MemoryDeclaration.model_fields) in e
    toa_do = hong["memory_declarations"][0]["at"]
    assert json.dumps(toa_do, ensure_ascii=False) not in e and json.dumps(toa_do, separators=(",", ":")) not in e
    assert "$defs" not in e and "properties" not in e and "statements" not in e


# ── D ───────────────────────────────────────────────────────────────────────
def test_D_chuong_trinh_C02_duoc_nhan__VAN_HOP_LE__khong_khoa_nao_bi_bo():
    v = V.validate_semantic_program(_prog(CA_P6))
    assert v.ok is True
    assert getattr(v, "ignored_keys", None) == ()


# ── E ───────────────────────────────────────────────────────────────────────
def test_E_tap_khoa_PYDANTIC__LUOC_DO_XUAT__THE__VALIDATOR_nhat_quan():
    mo_hinh = list(C.MemoryDeclaration.model_fields)
    luoc_do = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]["MemoryDeclaration"]["properties"]
    assert list(luoc_do) == [k for k in mo_hinh if k != "provenance"] or list(luoc_do) == mo_hinh
    dong = _dong_the_khai_bao()
    assert _khoa_trong_dong_the(dong) == [k for k in mo_hinh if k not in AN_O_HINH_HOC]
    assert dong.rstrip().endswith(CAU_KHOA_DUNG)
    e = V.validate_semantic_program(_c02_bi_loai_dan_xuat()).error
    assert e.split("Khoá hợp lệ: ", 1)[1].split(", ") == mo_hinh


# ── F ───────────────────────────────────────────────────────────────────────
def test_F_the_va_prompt_KHONG_dat_at_trong_memory_declarations():
    assert "at" not in _khoa_trong_dong_the(_dong_the_khai_bao())
    the = grammar_card(DOMAIN_HINH_HOC)
    dong_at = [x for x in the.splitlines() if re.search(r"(?:^|\s)at\??:", x)]
    assert dong_at and all("declare_point" in x for x in dong_at)
    for md in SKILLS.glob("*.md"):
        assert "memory_declarations" not in md.read_text(encoding="utf-8"), md.name


# ── G ───────────────────────────────────────────────────────────────────────
def test_G_at_o_CAU_LENH_declare_point_van_hop_le__cung_hanh_vi():
    d = _prog(CA_P6)
    d0 = d["memory_declarations"].pop(0)
    d["statements"].insert(0, {"kind": "declare_point", "target_var": d0["name"], "at": d0["initial_value"],
                               **{k: d0[k] for k in ("source_fact_id", "model_assumption") if d0.get(k)}})
    v = V.validate_semantic_program(d)
    assert v.ok is True, v.error
    assert _final_memory(CA_P6, d) == FINAL_MEMORY_START[CA_P6]


# ── H ───────────────────────────────────────────────────────────────────────
def test_H_sua_dung_o__TRUNG_chuong_trinh_duoc_nhan__cung_final_memory_va_canh(monkeypatch):
    hong = _c02_bi_loai_dan_xuat()
    sua = json.loads(json.dumps(hong))
    sua["memory_declarations"][0]["initial_value"] = sua["memory_declarations"][0].pop("at")
    nhan = _prog(CA_P6)
    assert _bam(sua) == _bam(nhan)
    assert _final_memory(CA_P6, sua) == FINAL_MEMORY_START[CA_P6]
    env = _envelope(monkeypatch, CA_P6, [json.dumps(hong, ensure_ascii=False), json.dumps(sua, ensure_ascii=False)])
    assert env["status"] == "ok"
    assert _bam(env["scene3d"]) == SCENE_START[CA_P6]
    assert len(env["scene3d"]["objects"]) == SO_VAT_START[CA_P6]


# ── I ───────────────────────────────────────────────────────────────────────
def test_I_C01_p1_hanh_vi_KHONG_DOI(monkeypatch):
    p1 = _prog(CA_P1)
    assert _final_memory(CA_P1, p1) == FINAL_MEMORY_START[CA_P1]
    env = _envelope(monkeypatch, CA_P1, [json.dumps(p1, ensure_ascii=False)])
    assert env["status"] == "ok" and _bam(env["scene3d"]) == SCENE_START[CA_P1]
    assert len(env["scene3d"]["objects"]) == SO_VAT_START[CA_P1]


# ── J ───────────────────────────────────────────────────────────────────────
def test_J_trace_vong_sua_C02_LIEN_KET_dung__ma_on_dinh(kho, de):
    hong = json.dumps(_c02_bi_loai_dan_xuat(), ensure_ascii=False)
    nhan = RNB.doc_raw_theo_thu_tu(CA_P6)["semantic_program"][0]
    r = _chay(kho, "C02", "--synthesis-repair-trace", kich_ban=_kich_ban(de, {("C02", "synthesis"): [hong, nhan]}))
    t = _json(r, "C02_SYNTHESIS_REPAIR_TRACE.json")
    a0, a1 = t["attempts"]
    assert (a0["result"], a0["rejection_phase"], a0["rejection_code"]) == ("REJECTED", "PROGRAM_SCHEMA", MA)
    assert a0["classification_matches_emitted_message"] is True and a0["feedback_delivered_in_next_request"] is True
    assert a1["result"] == "ACCEPTED" and a1["repairs_logical_call"] == a0["logical_call"]
    assert t["links"] == [{"rejected_logical_call": a0["logical_call"], "repaired_by_logical_call": a1["logical_call"],
                           "feedback_sha256": a0["feedback_sha256"]}]


# ── K ───────────────────────────────────────────────────────────────────────
def test_K_phan_hoi_sua_KHONG_DAI_HON__mang_ma_va_con_tro__khong_luoc_do():
    hong = _c02_bi_loai_dan_xuat()
    loi = V.validate_semantic_program(hong).error
    manh = manh_hop_dong(loi, DOMAIN_HINH_HOC)
    assert len(loi.encode("utf-8")) + len(manh.encode("utf-8")) <= LOI_CU_BYTE + MANH_CU_BYTE
    sua = PL._prompt_sua("BASE", json.dumps(hong, ensure_ascii=False), loi, de=RNB.doc_de_bai()[CA_P6],
                         domain=DOMAIN_HINH_HOC)
    assert f"[{MA}] {CON_TRO}" in sua and "$defs" not in sua and "Traceback" not in sua


# ── M · danh tính: băm thẻ đổi CHỈ vì mệnh đề khoá khai báo ────────────────────
def test_M_bam_the_truoc_wave_DUNG_LAI_duoc_chi_bang_bo_menh_de(monkeypatch):
    from app.runtime_identity import semantic_environment_fingerprint
    from app.simulation.semantic_program import grammar_card as G
    from tests.grammar_card_identity import GRAMMAR_CARD_TRUOC_WAVE, grammar_card_neu_chua_them_menh_de

    # Tại commit 5a5534fe (vertical slice lăng trụ), thẻ văn phạm mang thêm trường provenance
    # trong memory_declarations và point declarations.
    hien_tai = grammar_card_neu_chua_them_menh_de()
    assert hien_tai in (GRAMMAR_CARD_TRUOC_WAVE, "9e3b7f0af3b22c60f30ab72971ba8a57e5a31a4073c940b9a014f95d2a45b860")
    assert semantic_environment_fingerprint()["grammar_card"] != GRAMMAR_CARD_TRUOC_WAVE
    # TIÊM: đổi thêm MỘT dòng khác của thẻ ⇒ phép dựng lại không còn khớp.
    goc = G.grammar_card
    monkeypatch.setattr(G, "grammar_card",
                        lambda d=None: goc(d).replace("  type nhận đúng một trong:", "  type nhận một trong:"))
    assert grammar_card_neu_chua_them_menh_de() not in (GRAMMAR_CARD_TRUOC_WAVE, "9e3b7f0af3b22c60f30ab72971ba8a57e5a31a4073c940b9a014f95d2a45b860")


# ── L ───────────────────────────────────────────────────────────────────────
def test_L_khoa_trang_tri_duoc_BAO_qua_observer__chi_con_tro_khong_gia_tri(monkeypatch):
    d = _prog(CA_P6)
    d["memory_declarations"][0]["label"] = "NHAN-KHONG-DUOC-LOT"
    goi: list[str] = []

    async def stub(api_key, system_prompt, user_text, schema=None, temperature=0.2, image=None, **kw):
        goi.append(user_text)
        return json.dumps(d, ensure_ascii=False)

    class Obs:
        def __init__(self):
            self.su_kien: list[tuple[str, dict]] = []

        def emit(self, t, data):
            self.su_kien.append((t, data))

    obs = Obs()
    monkeypatch.setattr(PL, "call_gemini", stub)
    spec, err = asyncio.run(PL.stage_semantic_program("đề", {}, "stub-key", _hd(CA_P6), observer=obs, domain=DOMAIN_HINH_HOC))
    assert err is None and spec is not None and len(goi) == 1
    ev = [data for t, data in obs.su_kien if t == "semantic_program_ignored_keys"]
    assert ev == [{"n": 0, "keys": [{"pointer": "/memory_declarations/0/label", "key": "label"}]}]
    assert "NHAN-KHONG-DUOC-LOT" not in json.dumps(ev, ensure_ascii=False)
