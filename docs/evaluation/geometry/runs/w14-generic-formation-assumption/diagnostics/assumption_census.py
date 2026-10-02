# -*- coding: utf-8 -*-
"""W14 Task 5 Steps 3–4 — census of the assumption mechanisms on the hand-labelled corpus
(`assumption_corpus/CORPUS.json`, committed before this script existed), then the
pre-registered decision. DIAGNOSTICS code, not product. 0 model calls.

Per contract-bearing row, three-valued verdict (semantics fixed in the plan before any
measurement):
  PROVEN_SAFE   only from a typed certificate — C0 (no class-A/C literal in the answer's
                dependency closure) or C1 (source-determined configuration: compiler
                recognizer + PHEP_DO_C1 witness + inputs covered + reference grounded on the
                right entity/relation + exact congruence + nothing assumed outside);
  UNSAFE        only from a validated counterexample (one assumed coordinate perturbed,
                every source constraint still holds, some witness changes);
  UNDETERMINED  everything else — never "safe because nothing changed".
The R1 design (M2E, reconstructed from the R2 critique RC1–RC5) also runs, for the Step 1
comparison only. Closure here is a GENERIC walker over every name an IR statement mentions
(over-approximation: complete by construction for this census); the explicit TOAN_HANG table
plus its coverage test is a product-gate requirement, needed only if the decision is SHIP.

Run from the repository root (refuses to overwrite):
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/assumption_census.py \
    <ASSUMPTION_CENSUS.json> <ASSUMPTION_MECHANISM_DECISION.json>
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]
sys.path.insert(0, str(ROOT / "backend"))

from app.simulation.geometry_compiler import compiler as C  # noqa: E402
from app.simulation.geometry_compiler.contract_adapter import build_fact_graph  # noqa: E402
from app.simulation.semantic_program.contract import SemanticProgramSpec  # noqa: E402
from app.simulation.semantic_program.coverage_gate import check_structural_coverage  # noqa: E402
from app.simulation.semantic_program.formation import _dinh_nghia, _la, hoan_thien_dung_hinh  # noqa: E402
from app.simulation.semantic_program.grounding_gate import (  # noqa: E402
    _bang_chung_do_dai,
    bang_chung_doan,
    check_grounding,
)
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter  # noqa: E402
from app.simulation.semantic_program.pipeline_adapter import DEFAULT_EXECUTION_BUDGET  # noqa: E402
from app.simulation.semantic_program.postconditions import (  # noqa: E402
    check_postconditions,
    check_source_invariants,
)
from app.simulation.semantic_program.request_contract import RequestContract  # noqa: E402
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402
from app.simulation.semantic_program.source_entities import dinh_danh_thuc_the  # noqa: E402
from app.simulation.semantic_program.structured_relations import kiem_va_chuan_hoa  # noqa: E402

CORPUS = HERE.parent / "assumption_corpus" / "CORPUS.json"
NGAN_SACH_CHAY_LAI = 120
PHEP_DO_C1 = {"volume", "area", "distance"}
CERT_SCOPE = ("C0: the answer's dependency closure holds no class-A/C literal; C1: compiler-recognized "
              "configuration (danh_gia_eligibility SUPPORTED), every numeric witness a measure in "
              "PHEP_DO_C1 = {volume of the bound solid, area of a polygon on bound points, distance "
              "between bound points} reached through var assignments only, inputs covered by the bound "
              "points, every basis length entity-bound in the text, every relation source-confirmed, "
              "exact congruence with the compiler's reference layout. Everything else is UNDETERMINED "
              "by design.")


# ── helpers ──────────────────────────────────────────────────────────────────

def _id(x: Any) -> str:
    return dinh_danh_thuc_the(str(x))[0]


def _gia_tri(v: Any) -> str | None:
    """Comparable exact rendering of a numeric witness value, or None if not numeric."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, Fraction)):
        return str(Fraction(v))
    if type(v).__name__ == "Radical":
        return repr(v)
    return None


def _chay(sp: SemanticProgramSpec):
    return SemanticProgramInterpreter(max_steps=DEFAULT_EXECUTION_BUDGET).execute(sp)


def _diem_literal(d: dict) -> dict[str, list]:
    """name -> literal coordinates, from point3 declarations with a value and declare_point."""
    ra = {m["name"]: m["initial_value"] for m in d["memory_declarations"]
          if m.get("type") == "point3" and isinstance(m.get("initial_value"), list)}
    for s in d["statements"]:
        if s.get("kind") == "declare_point" and isinstance(s.get("at"), list):
            ra[s["target_var"]] = s["at"]
    return ra


def _bao_dong(d: dict, goc: set[str]) -> set[str]:
    biet = {m["name"] for m in d["memory_declarations"]} | _dinh_nghia(d["statements"])
    sinh: dict[str, list[dict]] = {}
    for s in d["statements"]:
        for n in _dinh_nghia(s):
            sinh.setdefault(n, []).append(s)
    thay, ngan = set(), list(goc)
    while ngan:
        n = ngan.pop()
        if n in thay:
            continue
        thay.add(n)
        for s in sinh.get(n, ()):
            ngan.extend((_la(s) & biet) - _dinh_nghia(s))
        m = next((m for m in d["memory_declarations"] if m["name"] == n), None)
        if m is not None and m.get("initial_value") is not None:
            ngan.extend(_la(m.get("initial_value")) & biet)
    return thay


def _lop_literal(ground) -> dict[str, str]:
    ra = {}
    for x in ground.justified_literals:
        parts = x.split("|")
        if len(parts) >= 3:
            ra[parts[0]] = parts[2]
    return ra


def _nhan_chung(ct: RequestContract, sp: SemanticProgramSpec) -> dict[str, str]:
    ten = check_structural_coverage(ct, sp).ten_da_hoa_giai
    return {w: ten.get(w, w) for o in ct.obligations if (w := o.witness)}


# ── C0 / C1 ──────────────────────────────────────────────────────────────────

def _c0(closure: set[str], d: dict, lop: dict[str, str]) -> tuple[bool, str]:
    """Every literal-bearing name in the closure (declaration with a value, declare_point) must be
    class B (pinned to the source); class A/C or unclassified ⇒ no C0."""
    lit_all = ({m["name"] for m in d["memory_declarations"] if m.get("initial_value") is not None}
               | {s["target_var"] for s in d["statements"] if s.get("kind") == "declare_point"})
    xau = sorted(n for n in closure & lit_all if lop.get(n) != "B")
    return (not xau, "ok" if not xau else f"class-A/C or unclassified literals in closure: {xau}")


def _phep_do(d: dict, w: str, bound: set[str]) -> tuple[bool, str]:
    seen, n = set(), w
    while n not in seen:
        seen.add(n)
        s = next((s for s in d["statements"] if s.get("kind") == "assign" and s.get("target_var") == n), None)
        if s is None:
            return False, f"{w}: no assign producer"
        e = s.get("expr") or {}
        if e.get("kind") == "var":
            n = e.get("name")
            continue
        if e.get("kind") != "measure" or e.get("quantity") not in PHEP_DO_C1:
            return False, f"{w}: {e.get('kind')}/{e.get('quantity')} outside PHEP_DO_C1"
        q, of, wrt = e["quantity"], e.get("of"), e.get("wrt")
        if q == "distance":
            ok = of in bound and wrt in bound
        else:
            src = next((x for x in d["statements"] if x.get("target_var") == of), None)
            dinh = set((src or {}).get("vertices") or ())
            ok = bool(dinh) and dinh <= bound
        return ok, f"{w}: measure {q} of {of}{'/' + wrt if wrt else ''} {'on' if ok else 'NOT on'} bound points"
    return False, f"{w}: var cycle"


def _c1(ct, sp, d, closure, lit, lop, chung) -> tuple[bool, str]:
    fg = build_fact_graph(ct)
    if fg.graph is None:
        return False, f"recognized: fact graph {fg.status}"
    el = C.danh_gia_eligibility(fg.graph)
    if el.status != "SUPPORTED":
        return False, f"recognized: eligibility {el.status} {el.reason_code}"
    ref = C.bien_dich(fg.graph)
    if ref.program is None:
        return False, "recognized: reference layout not compiled"
    ref_sp = SemanticProgramSpec.model_validate({"spec_version": "1.0", **ref.program})
    bound = set(_diem_literal(ref_sp.model_dump(mode="json", exclude_none=True)))
    for w in chung.values():
        ok, why = _phep_do(d, w, bound)
        if not ok:
            return False, f"supported operation: {why}"
    ngoai = sorted(n for n in closure if n in lit and n not in bound)
    if ngoai:
        return False, f"inputs covered: assumed points outside the bound configuration: {ngoai}"
    text = ct.problem_text or ""
    for f in fg.graph.fact_theo_loai("length"):
        if not bang_chung_doan(text, tuple(f.args), Fraction(f.value)):
            return False, f"grounded: basis length {''.join(f.args)} = {f.value} has no entity-bound evidence"
    xac_nhan = {f.fact_id for f in ct.input_facts if f.provenance == "confirmed"}
    for q in kiem_va_chuan_hoa(ct).relations:
        if not q.dung_duoc_cho_tang_dung():
            return False, f"grounded: relation {q.kind}{q.args} not usable (no source / model assumption)"
        if q.source_fact_id not in xac_nhan:
            return False, (f"grounded: relation {q.kind}{q.args} cites '{q.source_fact_id}', "
                           "not a confirmed InputFact")
    mem_ref, mem = _chay(ref_sp).final_memory, _chay(sp).final_memory
    ten = sorted(bound)
    if any(t not in mem for t in ten):
        return False, "congruent: a bound point is not realised by the candidate"
    for i, a in enumerate(ten):
        for b in ten[i + 1:]:
            if (mem[a] - mem[b]).dot(mem[a] - mem[b]) != (mem_ref[a] - mem_ref[b]).dot(mem_ref[a] - mem_ref[b]):
                return False, f"congruent: |{a}{b}|² differs from the reference"
    return True, "ok"


# ── CE (counterexample) ─────────────────────────────────────────────────────

def _quan_he_dung(ct, mem) -> bool | None:
    """Every typed relation holds exactly (True/False), or None if a kind/point is uncheckable."""
    for r in ct.geometric_relations:
        L = [_id(x) for x in r.line]
        if any(p not in mem for p in L) or len(L) != 2:
            return None
        u = mem[L[1]] - mem[L[0]]
        if r.kind == "perpendicular_lines":
            K = [_id(x) for x in r.other_line]
            if len(K) != 2 or any(p not in mem for p in K):
                return None
            if u.dot(mem[K[1]] - mem[K[0]]) != 0:
                return False
        elif r.kind == "perpendicular_line_plane":
            P = [_id(x) for x in r.plane]
            if len(P) < 3 or any(p not in mem for p in P):
                return None
            if u.dot(mem[P[1]] - mem[P[0]]) != 0 or u.dot(mem[P[2]] - mem[P[0]]) != 0:
                return False
        else:
            return None
    return True


def _nhieu(d: dict, ten: str, k: int, phep) -> dict | None:
    d2 = copy.deepcopy(d)
    for m in d2["memory_declarations"]:
        if m["name"] == ten and isinstance(m.get("initial_value"), list):
            goc = Fraction(str(m["initial_value"][k]))
            moi = phep(goc)
            if moi == goc:
                return None
            m["initial_value"][k] = str(moi)
    for s in d2["statements"]:
        if s.get("kind") == "declare_point" and s.get("target_var") == ten and isinstance(s.get("at"), list):
            goc = Fraction(str(s["at"][k]))
            moi = phep(goc)
            if moi == goc:
                return None
            s["at"][k] = str(moi)
    return d2


def _ce(ct, d, closure, lit, lop, chung, goc_val) -> tuple[str, list]:
    tu_do = [n for n in sorted(closure) if n in lit and lop.get(n) != "B"]
    lan, mo = 0, False
    for p in tu_do:
        for k in range(3):
            for ten_phep, phep in (("x2", lambda v: v * 2), ("+1", lambda v: v + 1)):
                try:
                    d2 = _nhieu(d, p, k, phep)
                except (ValueError, ZeroDivisionError, TypeError):
                    mo = True
                    continue
                if d2 is None:
                    continue
                lan += 1
                if lan > NGAN_SACH_CHAY_LAI:
                    return "INCONCLUSIVE", ["BUDGET_EXHAUSTED"]
                try:
                    sp2 = SemanticProgramSpec.model_validate(d2)
                    res = _chay(sp2)
                except Exception as e:  # noqa: BLE001
                    mo = True
                    continue
                if res.status != "ok" and res.status != "completed":
                    pass
                ten_hg = check_structural_coverage(ct, sp2).ten_da_hoa_giai
                if not check_source_invariants(ct, res, ten_da_hoa_giai=ten_hg).ok:
                    continue
                qh = _quan_he_dung(ct, res.final_memory)
                if qh is None:
                    mo = True
                    continue
                if not qh or check_postconditions(ct, sp2, res, ten_da_hoa_giai=ten_hg).violations:
                    continue
                doi = [w for w in chung.values() if _gia_tri(res.final_memory.get(w)) != goc_val.get(w)]
                if doi:
                    return "UNSAFE", [f"{p}[{k}]{ten_phep}", *doi]
    return ("INCONCLUSIVE" if mo else "NO_VALID_COUNTEREXAMPLE"), []


# ── M2E (R1 design, comparison only) ────────────────────────────────────────

def _m2e(ct, d, closure, lit, lop, chung, goc_val) -> tuple[str, str]:
    text = ct.problem_text or ""
    if not text:
        return "OK", "RC5: empty problem text short-circuits to ok"
    gia_dinh = [n for n in sorted(closure) if n in lit and lop.get(n) != "B"]
    do_dai = {m["name"]: m["initial_value"] for m in d["memory_declarations"]
              if m["name"].endswith("_length") and m.get("initial_value") is not None}
    hop_le = 0
    for k in range(3):
        d2 = copy.deepcopy(d)
        for p in gia_dinh:
            for m in d2["memory_declarations"]:
                if m["name"] == p and isinstance(m.get("initial_value"), list):
                    m["initial_value"][k] = str(Fraction(str(m["initial_value"][k])) * 2)
            for s in d2["statements"]:
                if s.get("kind") == "declare_point" and s.get("target_var") == p:
                    s["at"][k] = str(Fraction(str(s["at"][k])) * 2)
        try:
            res = _chay(SemanticProgramSpec.model_validate(d2))
        except Exception:  # noqa: BLE001 — RC1: an invalid perturbation is silently skipped
            continue
        mem = res.final_memory
        # RC2: validity checked against the PROGRAM's own XY_length memories.
        hong = False
        for ten, v in do_dai.items():
            ab = ten.removesuffix("_length").replace("_prime", "′")
            pts = [x for x in mem if x in lit]
            cap = next(((a, b) for a in pts for b in pts if a != b
                        and dinh_danh_thuc_the(a)[1] + dinh_danh_thuc_the(b)[1] == ab), None)
            if cap and (mem[cap[0]] - mem[cap[1]]).dot(mem[cap[0]] - mem[cap[1]]) != Fraction(str(v)) ** 2:
                hong = True
        if hong:
            continue
        hop_le += 1
        doi = [w for w in chung.values() if _gia_tri(mem.get(w)) != goc_val.get(w)]
        if not doi:
            continue
        # RC3: ANY changed pair whose original length has evidence excuses the change.
        goc_mem = _chay(SemanticProgramSpec.model_validate(d)).final_memory
        pts = [x for x in goc_mem if x in lit]
        for a in pts:
            for b in pts:
                if a < b and (goc_mem[a] - goc_mem[b]).dot(goc_mem[a] - goc_mem[b]) != (mem[a] - mem[b]).dot(mem[a] - mem[b]):
                    L2 = (goc_mem[a] - goc_mem[b]).dot(goc_mem[a] - goc_mem[b])
                    for so in range(1, 101):
                        if Fraction(so) ** 2 == L2 and _bang_chung_do_dai(text, f"{a}{b}_length", Fraction(so), None)[0] is None:
                            return "OK", f"RC3: evidence for changed pair {a}{b} = {so} excused the change"
        return "REFUSE", f"axis {k} x2 changed {doi}"
    return "OK", f"RC1: no valid counterexample (valid perturbations: {hop_le})"


# ── per row ──────────────────────────────────────────────────────────────────

def do_hang(row: dict) -> dict:
    out = {"id": row["id"], "group": row["group"], "label": row["label"]}
    if row["contract"] is None:
        return out | {"measured": False, "why": "NO_CONTRACT (offline sample, never routed)"}
    ct = RequestContract.model_validate(row["contract"])
    sp0 = SemanticProgramSpec.model_validate(row["program"])
    r = verify_and_compile(ct, sp0)
    out |= {"route_today": {"stage": r.stage_reached, "servable": r.servable, "reason_code": r.reason_code}}
    if row["group"] == "NOT_SERVED_TODAY" or row["label"] == "POLICY_5A":
        return out | {"measured": False, "why": row["group"] if row["label"] != "POLICY_5A" else "POLICY_5A"}
    sp = hoan_thien_dung_hinh(sp0, ct).spec
    d = sp.model_dump(mode="json", exclude_none=True)
    try:
        res = _chay(sp)
    except Exception as e:  # noqa: BLE001
        return out | {"measured": True, "verdict": "UNDETERMINED", "why": f"execution failed: {type(e).__name__}"}
    chung = _nhan_chung(ct, sp)
    goc_val = {w: _gia_tri(res.final_memory.get(w)) for w in chung.values()}
    so = {w: v for w, v in goc_val.items() if v is not None}
    if not so:
        return out | {"measured": True, "verdict": "NOT_APPLICABLE_NO_NUMERIC_ANSWER"}
    ground = check_grounding(ct, sp)
    lop = _lop_literal(ground)
    lit = _diem_literal(d)
    closure = _bao_dong(d, set(so))
    c0, why0 = _c0(closure, d, lop)
    c1, why1 = (False, "not evaluated (C0 holds)") if c0 else _c1(ct, sp, d, closure, lit, lop,
                                                                 {k: v for k, v in chung.items() if v in so})
    ce, ce_why = _ce(ct, d, closure, lit, lop, {k: v for k, v in chung.items() if v in so}, goc_val)
    m2e, m2e_why = _m2e(ct, d, closure, lit, lop, {k: v for k, v in chung.items() if v in so}, goc_val)
    verdict = "PROVEN_SAFE" if (c0 or c1) else ("UNSAFE" if ce == "UNSAFE" else "UNDETERMINED")
    return out | {"measured": True, "verdict": verdict, "certificate": "C0" if c0 else ("C1" if c1 else None),
                  "c0": why0, "c1": why1, "ce": ce, "ce_detail": ce_why, "m2e": m2e, "m2e_detail": m2e_why,
                  "numeric_witnesses": sorted(so)}


def quyet_dinh(rows: list[dict], census_sha: str) -> dict:
    do = [r for r in rows if r.get("measured") and "verdict" in r]
    vi_pham = [r["id"] for r in do if r["label"] == "DEPENDS" and r["verdict"] == "PROVEN_SAFE"]
    ac1_adv_lot = [r["id"] for r in do if r["group"] in ("AC1", "ADVERSARIAL") and r["label"] == "DEPENDS"
                   and r["verdict"] == "PROVEN_SAFE"]
    cert_lot = [r["id"] for r in do if r["group"] == "CERT_LIMIT" and r["verdict"] == "PROVEN_SAFE"]
    ac2 = [r for r in do if r["group"] == "AC2"]
    ac2_tu_choi = [r["id"] for r in ac2 if r["verdict"] != "PROVEN_SAFE"]
    ship = not vi_pham and not ac1_adv_lot and not cert_lot and not ac2_tu_choi
    return {
        "decision": "SHIP" if ship else "STOP",
        "final_decision_if_stop": None if ship else "ASSUMPTION_POLICY_INCOMPLETE",
        "rule": ("SHIP iff (a) 0 PROVEN_SAFE on DEPENDS rows of the measured corpus, (b) every AC1/adversarial "
                 "DEPENDS row refused and every certificate-limit row refused, (c) every contract-bearing AC2 "
                 "row PROVEN_SAFE (no user-approved defect exists); otherwise STOP Track B "
                 "(ASSUMPTION_POLICY_INCOMPLETE; Tracks A and C continue per Q4)"),
        "census_sha256": census_sha,
        "violations_PROVEN_SAFE_on_DEPENDS": vi_pham,
        "ac1_adversarial_not_refused": ac1_adv_lot,
        "certificate_limit_not_refused": cert_lot,
        "ac2_rows": len(ac2),
        "ac2_proven_safe": len(ac2) - len(ac2_tu_choi),
        "ac2_refused": ac2_tu_choi,
        # Soundness of CE itself: UNSAFE must come only from a VALID counterexample, so an UNSAFE
        # on an INVARIANT row means the validity check missed a source constraint.
        "ce_false_counterexamples_on_INVARIANT": [
            {"id": r["id"], "perturbation": r["ce_detail"]} for r in do
            if r["label"] == "INVARIANT" and r["ce"] == "UNSAFE"],
        "m2e_served_DEPENDS": [r["id"] for r in do if r["label"] == "DEPENDS" and r["m2e"] == "OK"],
        "c1_first_failing_condition": {r["id"]: r["c1"] for r in do if r.get("certificate") is None},
        "verdicts_by_group": {g: {v: sum(1 for r in do if r["group"] == g and r["verdict"] == v)
                                  for v in ("PROVEN_SAFE", "UNSAFE", "UNDETERMINED",
                                            "NOT_APPLICABLE_NO_NUMERIC_ANSWER")}
                              for g in sorted({r["group"] for r in do})},
        "certificate_scope": CERT_SCOPE,
        "claim_wording": "0 violations on the measured corpus within the certificate scope — not a general soundness proof",
    }


def main() -> None:
    out_c, out_d = Path(sys.argv[1]), Path(sys.argv[2])
    for p in (out_c, out_d):
        if p.exists():
            raise SystemExit(f"refusing to overwrite {p}")
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    rows = [do_hang(r) for r in corpus["rows"]]
    census = {"census": "W14_ASSUMPTION_CENSUS", "model_calls": 0,
              "corpus_labels_sha256": corpus["labels_sha256"],
              "corpus_sha256": hashlib.sha256(CORPUS.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
              "re_execution_budget": NGAN_SACH_CHAY_LAI, "certificate_scope": CERT_SCOPE, "rows": rows}
    text = json.dumps(census, ensure_ascii=False, indent=1) + "\n"
    out_c.write_text(text, encoding="utf-8", newline="\n")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    out_d.write_text(json.dumps(quyet_dinh(rows, sha), ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8", newline="\n")
    print(out_c, out_d)


if __name__ == "__main__":
    main()
