# -*- coding: utf-8 -*-
"""W15 Task 5 — census of the assumption certificate on the W14 + W15 corpora, then the
pre-registered SHIP/STOP decision (docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md §9).
DIAGNOSTICS code, not product. 0 model calls.

Per contract-bearing row: `assumption_gate.danh_gia_doc_lap` (the product module, NOT yet wired
into the route) and today's route outcome (`verify_and_compile`, for reference). Rows the
route refuses before the gate (W14 NOT_SERVED_TODAY, POLICY rows) are measured but kept out
of (a)–(d) exactly as W14 did; (e) asks the route-served GUARD rows to be PROVEN_SAFE too.
The claim this census supports is "0 violations on the measured corpus within the certificate
scope", never a general proof. Refuses to overwrite. Run from the repository root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/assumption_census_w15.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]
W14_CORPUS = ROOT / "docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/assumption_corpus/CORPUS.json"
W15_CORPUS = HERE.parent / "assumption_corpus_w15" / "CORPUS.json"
OUT_C = HERE.with_name("ASSUMPTION_CENSUS_W15.json")
OUT_D = HERE.with_name("ASSUMPTION_MECHANISM_DECISION_W15.json")
sys.path.insert(0, str(ROOT / "backend"))

from app.simulation.geometry.exact import Vec3  # noqa: E402
from app.simulation.geometry_compiler import compiler as C  # noqa: E402
from app.simulation.geometry_compiler.contract_adapter import build_fact_graph  # noqa: E402
from app.simulation.semantic_program import assumption_gate as G  # noqa: E402
from app.simulation.semantic_program.contract import SemanticProgramSpec  # noqa: E402
from app.simulation.semantic_program.formation import hoan_thien_dung_hinh  # noqa: E402
from app.simulation.semantic_program.request_contract import RequestContract  # noqa: E402
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402
from app.simulation.semantic_program.source_entities import dinh_danh_thuc_the  # noqa: E402

TRUOC_CONG = {"NOT_SERVED_TODAY", "W15_POLICY"}
GUARD = {f"ho:{h}" for h in ("chop_tam_giac", "lang_tru_tam_giac", "chop_chu_nhat", "hop_chu_nhat",
                             "lap_phuong", "lang_tru_day_vuong")} | {
    f"gold:{g}" for g in ("p1_chop_thiet_dien_khoang_cach", "p2_chop_day_ngu_giac_lom",
                          "p4_hinh_tru_the_tich_va_xung_quanh", "p5_hinh_non_the_tich_va_xung_quanh",
                          "p6_thiet_dien_elip_cua_hinh_tru", "p7_thiet_dien_elip_cua_hinh_non")} | {
    f"demo:{d}" for d in ("n1_thoi_dinh_thu_tu", "n2_lang_tru_xien_hai_vecto", "t3_hop_tinh_tien_day_chuyen",
                          "t4_mat_xich_trong_chuoi_sau")}
METAMORPHIC = ("test_chuyen_dong_cung_va_phep_quay_giu_phan_quyet_va_gia_tri or "
               "test_song_anh_ten_thuc_the_giu_phan_quyet or test_doi_kich_thuoc_de_khong_cho_bi_phat_hien")


def _sha_lf(b: bytes) -> str:
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def _diem(mem: dict) -> dict[str, Vec3]:
    return {dinh_danh_thuc_the(n)[0]: v for n, v in mem.items() if isinstance(v, Vec3)}


def doi_chieu_compiler(ct, sp) -> str:
    """Chẩn đoán (amendment §6.5, đính chính): mọi hàng C1 mà compiler NHẬN được — bình phương
    khoảng cách từng cặp điểm chung của ứng viên và chương trình tham chiếu `bien_dich`."""
    fg = build_fact_graph(ct)
    if fg.graph is None or C.danh_gia_eligibility(fg.graph).status != "SUPPORTED":
        return "NOT_RECOGNIZABLE"
    ref = C.bien_dich(fg.graph)
    if ref.program is None:
        return "NOT_RECOGNIZABLE"
    R = _diem(G._chay(SemanticProgramSpec.model_validate({"spec_version": "1.0", **ref.program})).final_memory)
    V = _diem(G._chay(hoan_thien_dung_hinh(sp, ct).spec).final_memory)
    chung = sorted(set(R) & set(V))
    lech = [(p, q) for i, p in enumerate(chung) for q in chung[i + 1:]
            if (V[p] - V[q]).dot(V[p] - V[q]) != (R[p] - R[q]).dot(R[p] - R[q])]
    return f"DISAGREES {lech[0]}" if lech else f"AGREES {len(chung)} points"


def do_hang(row: dict, corpus: str) -> dict:
    out = {"id": row["id"], "corpus": corpus, "group": row["group"], "label": row["label"],
           "expect": row.get("expect")}
    if row.get("contract") is None:
        return out | {"measured": False, "why": "NO_CONTRACT (offline sample, never routed)"}
    ct = RequestContract.model_validate(row["contract"])
    sp = SemanticProgramSpec.model_validate(row["program"])
    r = verify_and_compile(ct, sp)
    kq = G.danh_gia_doc_lap(ct, sp)
    return out | {
        "measured": True, "before_gate": row["group"] in TRUOC_CONG or row["label"] == "POLICY_5A",
        "route_today": {"stage": r.stage_reached, "servable": r.servable, "reason_code": r.reason_code},
        "status": kq.status, "certificate": kq.certificate, "reason_code": kq.reason_code,
        "subjects": list(kq.subjects), "details": list(kq.details)[:12],
        "witness": None if kq.witness is None else {"description": kq.witness["description"],
                                                    "changes": kq.witness["changes"]},
        "compiler_cross_check": doi_chieu_compiler(ct, sp) if kq.certificate == "C1" else None,
    }


def _du_doan_dung(r: dict) -> bool | None:
    e = r.get("expect")
    if not e or not r.get("measured"):
        return None
    if e.startswith("PROVEN_SAFE"):
        return r["status"] == "PROVEN_SAFE" and (":" not in e or r["certificate"] == e.split(":")[1])
    if e.startswith("DEPENDENT"):
        return r["status"] == G.DEPENDENT and (":" not in e or e.split(":")[1] in r["subjects"])
    return r["status"] == e


def quyet_dinh(rows: list[dict], census_sha: str, metamorphic_exit: int) -> dict:
    do = [r for r in rows if r.get("measured") and not r["before_gate"]]
    tu_choi = lambda r: r["status"] != "PROVEN_SAFE"  # noqa: E731
    a = [r["id"] for r in do if r["label"] in ("DEPENDS", "MUST_REFUSE") and r["status"] == "PROVEN_SAFE"]
    b = [r["id"] for r in do if (r["group"] in ("AC1", "ADVERSARIAL") or r["label"] in ("DEPENDS", "MUST_REFUSE"))
         and not tu_choi(r)]
    c = [r["id"] for r in do if r["label"] == "INVARIANT" and r["status"] == G.DEPENDENT]
    ac2 = [r for r in do if r["corpus"] == "W14" and r["group"] == "AC2"]
    d = [r["id"] for r in ac2 if r["status"] != "PROVEN_SAFE"]
    theo_id = {r["id"]: r for r in rows if r["corpus"] == "W14"}
    e = sorted(g for g in GUARD if not (theo_id[g]["route_today"]["servable"] and theo_id[g]["status"] == "PROVEN_SAFE"))
    f = metamorphic_exit == 0
    ship = not a and not b and not c and not d and not e and f
    return {
        "decision": "SHIP" if ship else "STOP",
        "final_decision_if_stop": None if ship else "ASSUMPTION_POLICY_INCOMPLETE",
        "rule": "docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md §9 (a)–(f), registered before this census",
        "census_sha256_lf": census_sha,
        "a_PROVEN_SAFE_on_DEPENDS_or_MUST_REFUSE": a,
        "b_must_refuse_not_refused": b,
        "c_DEPENDENT_on_INVARIANT": c,
        "d_ac2_rows": len(ac2), "d_ac2_proven_safe": len(ac2) - len(d), "d_ac2_not_proven": d,
        "e_guard_rows_not_served_or_not_proven": e,
        "f_metamorphic_tests_exit_code": metamorphic_exit,
        "report_w15_expectation_mismatches": {r["id"]: [r["expect"], r["status"], r["certificate"], r["subjects"]]
                                              for r in rows if r["corpus"] == "W15" and _du_doan_dung(r) is False},
        "report_compiler_cross_check": {
            "c1_rows": sum(1 for r in rows if r.get("certificate") == "C1"),
            "agrees": sum(1 for r in rows if (r.get("compiler_cross_check") or "").startswith("AGREES")),
            "not_recognizable": sum(1 for r in rows if r.get("compiler_cross_check") == "NOT_RECOGNIZABLE"),
            "disagrees": [r["id"] for r in rows if (r.get("compiler_cross_check") or "").startswith("DISAGREES")]},
        "verdicts_by_group": {g: {v: sum(1 for r in do if r["group"] == g and r["status"] == v)
                                  for v in (G.PROVEN_SAFE, G.DEPENDENT, G.UNDETERMINED, G.NOT_APPLICABLE)}
                              for g in sorted({r["group"] for r in do})},
        "claim_wording": "0 violations on the measured corpus within the certificate scope — not a general soundness proof",
    }


def main() -> None:
    for p in (OUT_C, OUT_D):
        if p.exists():
            raise SystemExit(f"refusing to overwrite {p}")
    rows = [do_hang(r, "W14") for r in json.loads(W14_CORPUS.read_text(encoding="utf-8"))["rows"]]
    rows += [do_hang(r, "W15") for r in json.loads(W15_CORPUS.read_text(encoding="utf-8"))["rows"]]
    census = {"census": "W15_ASSUMPTION_CENSUS", "model_calls": 0,
              "corpora": {"W14": {"path": str(W14_CORPUS.relative_to(ROOT)).replace("\\", "/"),
                                  "sha256_lf": _sha_lf(W14_CORPUS.read_bytes())},
                          "W15": {"path": str(W15_CORPUS.relative_to(ROOT)).replace("\\", "/"),
                                  "sha256_lf": _sha_lf(W15_CORPUS.read_bytes())}},
              "re_execution_budget": G.NGAN_SACH_CHAY_LAI, "rows": rows}
    raw = (json.dumps(census, ensure_ascii=False, indent=1, default=str) + "\n").encode("utf-8")
    OUT_C.write_bytes(raw)
    mm = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                         "tests/geometry/test_assumption_certificate.py", "-k", METAMORPHIC],
                        cwd=ROOT / "backend", capture_output=True, text=True,
                        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    dec = quyet_dinh(rows, _sha_lf(raw), mm.returncode)
    dec["f_metamorphic_tests_tail"] = mm.stdout.strip().splitlines()[-1:] if mm.stdout else []
    OUT_D.write_text(json.dumps(dec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: dec[k] for k in dec if k not in ("report_w15_expectation_mismatches",
                                                          "verdicts_by_group")}, ensure_ascii=False, indent=1))
    print("W15 expectation mismatches:", json.dumps(dec["report_w15_expectation_mismatches"], ensure_ascii=False))


if __name__ == "__main__":
    main()
