# -*- coding: utf-8 -*-
"""W15 Task 3 — build the W15 assumption corpus from its hand labels (0 model calls).

`LABELS.json` is written by hand and committed BEFORE any certificate code exists; this
script only turns each label's `builder`/`arg` into a (contract, program) pair from
committed test fixtures (`backend/tests/geometry`). Contracts go through the product
boundary (`build_request_contract`) wherever the fixture exposes its analyze payload;
the rectangular-pyramid family keeps its payload inline in its test, so its rows reuse
that contract with a new problem text and re-run the product's own text-invariant
builders (`analyze_contract.gan_bat_bien_nguon`). The W14 corpus is referenced by sha,
never copied or edited. Refuses to overwrite. Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/assumption_corpus_w15/build_corpus.py
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[7]
LABELS = HERE.with_name("LABELS.json")
OUT = HERE.with_name("CORPUS.json")
sys.path.insert(0, str(ROOT / "backend"))

from app.simulation.semantic_program.analyze_contract import (  # noqa: E402
    build_request_contract,
    gan_bat_bien_nguon,
)
from app.simulation.semantic_program.validator import validate_semantic_program  # noqa: E402
from tests.geometry import test_assumption_certificate as X  # noqa: E402
from tests.geometry import test_cuboid_cube_production_route as CC  # noqa: E402
from tests.geometry import test_source_grounding_closure as T  # noqa: E402
from tests.geometry import w14_cases as W  # noqa: E402

CHOP = W.CHOP_TAM_GIAC_TEXT
CAU_CHOP = {
    "SA_KY_HIEU": CHOP.replace("Cạnh bên SA vuông góc với đáy, SA = 5.", "Cạnh bên SA ⊥ (ABC), SA = 5."),
    "SA_MAT_PHANG_TEN": CHOP.replace("vuông góc với đáy", "vuông góc với mặt phẳng (ABC)"),
    "TAM_GIAC_RIENG": ("Cho hình chóp S.ABC, tam giác ABC vuông tại A, AB = 3, AC = 4. Cạnh bên SA vuông "
                       "góc với đáy, SA = 5. Tính thể tích khối chóp S.ABC."),
    "GOC_90": ("Cho hình chóp S.ABC có AB = 3, AC = 4 và góc BAC = 90°. Cạnh bên SA vuông góc với đáy, "
               "SA = 5. Tính thể tích khối chóp S.ABC."),
    "KHOI_CHOP": CHOP.replace("Cho hình chóp", "Cho khối chóp"),
    "CHIEU_CAO": CHOP.replace("Cạnh bên SA vuông góc với đáy, SA = 5.",
                              "Cạnh bên SA vuông góc với đáy và chiều cao bằng 5."),
    "DUONG_CAO": CHOP.replace("Cạnh bên SA vuông góc với đáy, SA = 5.", "SA là đường cao của hình chóp và SA = 5."),
}
CHOP_CHU_NHAT = ("Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 3, AD = 4. Cạnh bên SA vuông góc "
                 "với mặt phẳng đáy, SA = 6. Tính thể tích khối chóp S.ABCD.")


def _doi_de(ct, text: str):
    """Same analyze payload, another problem text: the product's own text-invariant builders re-run."""
    return gan_bat_bien_nguon(ct.model_copy(update={"problem_text": text, "source_invariants": ()}), text)


def _bo_khai(raw: dict, *ten: str) -> dict:
    raw = copy.deepcopy(raw)
    raw["memory_declarations"] = [m for m in raw["memory_declarations"] if m["name"] not in ten]
    return raw


def _bo_fact(payload: dict, *nhan: str) -> dict:
    payload = copy.deepcopy(payload)
    payload["input_facts"] = [f for f in payload["input_facts"] if f["label"] not in nhan]
    return payload


def chop_cau(arg):
    _t, ct0 = W.chop_tam_giac()
    return W.hop_dong(CAU_CHOP[arg], W.chop_tam_giac_payload()), W.chuong_trinh(ct0)


def chop_chu_nhat_binh_hanh(_arg):
    _t, ct0 = W.chop_chu_nhat()
    text = CHOP_CHU_NHAT.replace("là hình chữ nhật, AB = 3, AD = 4.",
                                 "là hình bình hành, AB = 3, AD = 4 và AB vuông góc với AD.")
    return _doi_de(ct0, text), W.chuong_trinh(ct0)


def chop_chu_nhat_dien_dat(_arg):
    _t, ct0 = W.chop_chu_nhat()
    text = CHOP_CHU_NHAT.replace("là hình chữ nhật, AB = 3, AD = 4.",
                                 "là hình bình hành, AB = 3, AD = 4, AB và AD tạo với nhau một góc vuông.")
    return _doi_de(ct0, text), W.chuong_trinh(ct0)


def lang_tru_phay(_arg):
    text = ("Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4. "
            "Cạnh bên AA' = 5. Tính thể tích khối lăng trụ ABC.A'B'C'.")
    p = T._prism_payload()
    for f in p["input_facts"]:
        if f["label"] == "AD":
            f["label"] = "AA'"
    for r in p["geometric_relations"]:
        if r["kind"] == "perpendicular_line_plane":
            r["line"] = ["A", "A'"]
    p["solid_topology"] = {"solid_kind": "prism", "base_cycle": ["A", "B", "C"], "top_cycle": ["A'", "B'", "C'"],
                           "correspondence": [["A", "A'"], ["B", "B'"], ["C", "C'"]]}
    ct = W.hop_dong(text, p)
    return ct, W.chuong_trinh(ct)


def hop_khoi(_arg):
    text, p = CC._cuboid_p01_payload()
    ct = W.hop_dong(text.replace("Cho hình hộp chữ nhật", "Cho khối hộp chữ nhật"), p)
    return ct, W.chuong_trinh(W.hop_dong(text, p))


def lap_phuong_AB(_arg):
    text, p = CC._cube_p01_payload()
    ct = W.hop_dong("Cho hình lập phương ABCD.A'B'C'D' có AB = 4. Tính thể tích của hình lập phương đó.", p)
    return ct, W.chuong_trinh(W.hop_dong(text, p))


def lang_tru_dien_dat(_arg):
    text = ("Cho hình lăng trụ ABC.DEF có các cạnh bên vuông góc với mặt đáy, đáy ABC là tam giác vuông tại A, "
            "AB = 3, AC = 4. Cạnh bên AD = 5. Tính thể tích khối lăng trụ ABC.DEF.")
    return W.hop_dong(text, T._prism_payload()), T._program_with_height_5()


def thieu(arg):
    ho, canh = arg.split("/")
    if ho == "chop_tam_giac":
        payload = _bo_fact(W.chop_tam_giac_payload(), "SA")
        ct = W.hop_dong(CHOP.replace(", SA = 5", ""), payload)
        raw = _bo_khai(W.chuong_trinh(W.chop_tam_giac()[1]), "SA_length")
        X._dat_diem(raw, "S", [0, 0, 7])
        return ct, raw
    if ho == "chop_chu_nhat":
        _t, ct0 = W.chop_chu_nhat()
        return (_doi_de(ct0, CHOP_CHU_NHAT.replace(", AD = 4", "")),
                _bo_khai(W.chuong_trinh(ct0), "AD_length"))
    if ho == "lang_tru_tam_giac":
        return (W.hop_dong(T.PRISM_TEXT.replace(", AC = 4", ""), _bo_fact(T._prism_payload(), "AC")),
                _bo_khai(T._program_with_height_5(), "AC_length"))
    if ho == "hop_chu_nhat":
        text, p = CC._cuboid_p01_payload()
        raw = _bo_khai(W.chuong_trinh(W.hop_dong(text, p)), "AA_prime_length")
        return W.hop_dong(text.replace(", AA' = 5", ""), _bo_fact(p, "AA'")), raw
    raise KeyError(arg)


def lap_phuong_thieu_canh(_arg):
    """Cube text with no edge length. The compiled program keeps its `XY_length` declarations
    (the other edges are derived from `AB_length`; they are not on the volume's slice)."""
    text, p = CC._cube_p01_payload()
    return (W.hop_dong("Cho hình lập phương ABCD.A'B'C'D'. Tính thể tích của hình lập phương đó.",
                       _bo_fact(p, "AB")), W.chuong_trinh(W.hop_dong(text, p)))


def lang_tru_vuong_thieu_cao(_arg):
    text, p = CC._square_prism_control_payload()
    raw = _bo_khai(W.chuong_trinh(W.hop_dong(text, p)), "AA_prime_length")
    return (W.hop_dong("Cho hình lăng trụ đứng có đáy là hình vuông cạnh 3. Tính thể tích khối lăng trụ đứng đó.",
                       _bo_fact(p, "AA'")), raw)


def so_sai_thuc_the(arg):
    if arg == "chop":
        payload = W.chop_tam_giac_payload()
        for f in payload["input_facts"]:
            if f["label"] == "AC":
                f["value"] = ["5"]
        du = CHOP.replace("AC = 4", "AC = 5")
        raw = _bo_khai(W.chuong_trinh(W.hop_dong(du, payload)), "SA_length")
        return W.hop_dong(du.replace(", SA = 5", ""), _bo_fact(payload, "SA")), raw
    text = ("Cho hình lăng trụ đứng ABC.DEF có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4, BC = 5. "
            "Tính thể tích khối lăng trụ ABC.DEF.")
    return W.hop_dong(text, _bo_fact(T._prism_payload(), "AD")), _bo_khai(T._program_with_height_5(), "AD_length")


def chop_vuong(_arg):
    _t, ct = W.chop_vuong()
    return ct, W.chuong_trinh(ct)


def lang_tru_vuong_co_ten(_arg):
    text, p = CC._square_prism_control_payload()
    de = ("Cho hình lăng trụ đứng ABCD.A'B'C'D' có đáy ABCD là hình vuông cạnh 3, cạnh bên AA' = 7. "
          "Tính thể tích khối lăng trụ ABCD.A'B'C'D'.")
    return W.hop_dong(de, p), W.chuong_trinh(W.hop_dong(text, p))


def lang_tru_vuong_khong_ten(_arg):
    text, p = CC._square_prism_control_payload()
    de = text.replace("chiều cao bằng 7", "chiều cao 7")
    return W.hop_dong(de, p), W.chuong_trinh(W.hop_dong(text, p))


def doi_ten(_arg):
    doi = {"A": "M", "B": "N", "C": "P", "S": "Q"}
    payload = W.chop_tam_giac_payload()
    for f in payload["input_facts"]:
        f["label"] = "".join(doi.get(c, c) for c in f["label"])
        f["id"] = f"fact_len_{f['label']}"
    for r in payload["geometric_relations"]:
        for k in ("line", "other_line", "plane"):
            if k in r:
                r[k] = [doi[x] for x in r[k]]
    ct = W.hop_dong(X.CHOP_DOI_TEN, payload)
    return ct, W.chuong_trinh(ct)


def chuyen_dong(arg):
    ho, phep = arg.split("/")
    _t, ct = W.HO[ho]()
    f = X._tinh_tien_doi_truc if phep == "tinh_tien_doi_truc" else W._xoay
    return ct, W.doi_toa_do(W.chuong_trinh(ct), f)


def ti_so(arg):
    de, r = arg.split("_")
    text = {"THIEU": X.THIEU_TI_SO, "DU": X.DU_TI_SO, "CANH": X.CANH_TI_SO}[de]
    return X._chop_voi_M(text, r)


def mat_phang_tu_chon(_arg):
    text = CHOP.replace("Tính thể tích khối chóp S.ABC.", "Một mặt phẳng song song với đáy cắt khối chóp theo "
                        "thiết diện (T). Tính diện tích thiết diện (T).")
    payload = W.chop_tam_giac_payload()
    payload["obligations"] = [{"kind": "area", "container": "T", "witness": "area_T"}]
    raw = W.chuong_trinh(W.chop_tam_giac()[1])
    raw["memory_declarations"] += [{"name": "alpha", "type": "plane3"}, {"name": "T", "type": "section"},
                                   {"name": "area_T", "type": "float"}]
    raw["statements"] += [
        {"kind": "construct_plane_from_equation", "target_var": "alpha", "a": 0, "b": 0, "c": 1, "d": -2},
        {"kind": "construct_section", "target_var": "T", "solid": "khoi_chop", "plane": "alpha"},
        {"kind": "assign", "target_var": "area_T", "expr": {"kind": "measure", "quantity": "area", "of": "T"}}]
    return W.hop_dong(text, payload), raw


def cong_thuc(arg):
    if arg == "(S*h)//3":
        _t, ct = W.chop_tam_giac()
        raw = W.chuong_trinh(ct)
        raw["memory_declarations"] += [{"name": "mp_day", "type": "plane3"}, {"name": "h", "type": "float"}]
        raw["statements"] = [s for s in raw["statements"] if s.get("target_var") != "the_tich_khoi"]
        raw["statements"] += [
            {"kind": "construct_plane", "target_var": "mp_day", "through": ["A", "B", "C"]},
            X._do("h", "S", "mp_day"),
            {"kind": "assign", "target_var": "the_tich_khoi",
             "expr": X._arith("//", X._arith("*", X._var("dien_tich_day_ABC"), X._var("h")), X._lit(3))}]
        return ct, raw
    expr = {"S*5": X._arith("*", X._var("dien_tich_day_ABC"), X._lit(5)), "S*h": X.S_NHAN_H,
            "S*AD_length": X._arith("*", X._var("dien_tich_day_ABC"), X._var("AD_length"))}[arg]
    return X._lang_tru_cong_thuc(expr)


def ghi_de(arg):
    ct, raw, _ten = X.GHI_DE[arg]()
    return ct, raw


def doi_chung_C0(_arg):
    ct, raw, _ten = X._c0_vo_huong(ghi_de=False)
    return ct, raw


def im_lang(arg):
    return X._p01_im_lang(arg)


def xien_bac(_arg):
    return (W.hop_dong(T.PRISM_TEXT.replace("lăng trụ đứng", "lăng trụ xiên"), T._prism_payload()),
            T._program_with_height_5())


def de_rong_tin_cay_gia(_arg):
    payload = W.chop_tam_giac_payload() | {"nguon": "FIXTURE_TIN_CAY", "trusted": True,
                                           "source_check": "UNCHECKED_TRUSTED_FIXTURE", "problem_text": ""}
    ct = build_request_contract(payload, problem_text="", domain="hinh_hoc")
    return ct, W.chuong_trinh(W.chop_tam_giac()[1])


def _chuong_trinh(raw: dict) -> tuple[dict, bool]:
    v = validate_semantic_program(raw)
    if v.ok and v.spec is not None:
        return v.spec.model_dump(mode="json", exclude_none=True), True
    return json.loads(json.dumps(raw, default=str)), False


def _sha_lf(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    nhan = json.loads(LABELS.read_text(encoding="utf-8"))
    ref = nhan["w14_reference"]
    for k, f in (("corpus_sha256_lf", "corpus"), ("labels_sha256_lf", "labels")):
        if _sha_lf(ROOT / ref[f]) != ref[k]:
            raise SystemExit(f"W14 {f} changed since the W15 labels were written")
    rows = []
    for cid, l in nhan["rows"].items():
        ct, raw = globals()[l["builder"]](l.get("arg"))
        prog, ok = _chuong_trinh(raw)
        rows.append({"id": cid, "group": l["group"], "label": l["label"], "expect": l["expect"],
                     "reason": l["reason"], "contract": ct.model_dump(mode="json"), "program": prog,
                     "program_schema_ok": ok})
    OUT.write_text(json.dumps({"corpus": "W15_ASSUMPTION_CORPUS", "model_calls": 0,
                               "labels_sha256_lf": _sha_lf(LABELS), "w14_reference": ref, "rows": rows},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    bad = [r["id"] for r in rows if not r["program_schema_ok"]]
    print(f"{OUT.name}: {len(rows)} rows; schema-invalid programs: {bad}")


if __name__ == "__main__":
    main()
