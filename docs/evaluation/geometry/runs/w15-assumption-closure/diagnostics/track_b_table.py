# -*- coding: utf-8 -*-
"""W15 Task 1 — Track B root-cause table (diagnostics, not product; 0 model calls).

Rows: the 18 AC2 rows, the 3 AC1 probes (2 served today) and the 5 CERT_LIMIT rows — a
superset of the 11 false counterexamples of the W14 census. For each row:
  · source text and requested quantities; the W14 verdict, C0/C1 reasons and CE witness
    (read from the reproduced W14 census, `w14_census_reproduction/ASSUMPTION_CENSUS.json`);
  · text invariants TODAY: the product's own builders (`analyze_contract.gan_bat_bien_nguon`)
    re-run on `problem_text` with the stored invariants removed — the stored demo contracts
    predate them;
  · a DRY RUN of the planned shape-constraint vocabulary (regexes in this file, NOT the
    Task 5 reader — Task 2's tests are the authority for the reader);
  · typed relations: the cited InputFact (exists? provenance?) and whether the dry run reads
    the same relation from the text;
  · the witness closure (W14 walker, on the formation-completed program the route runs),
    and which closure literals a text invariant pins — the rest are DOFs set only by
    layout/assumption;
  · numeric values the learner is shown (MEASUREMENT trace steps) that are NOT obligations;
  · each W14 counterexample re-applied and checked against every text constraint
    (fresh invariants + the text's shape constraints, hand-written per text below);
  · root-cause classes RC1–RC5 (plan §Context) assigned by explicit rules from the above.
Refuses to overwrite. Run from the repo root:
  backend/.venv/Scripts/python.exe docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/track_b_table.py
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]
W14 = ROOT / "docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics"
CENSUS = HERE.parent / "w14_census_reproduction" / "ASSUMPTION_CENSUS.json"
OUT_JSON = HERE.with_name("TRACK_B_ROOT_CAUSE_TABLE.json")
OUT_MD = HERE.with_name("TRACK_B_ROOT_CAUSE_TABLE.md")
sys.path.insert(0, str(ROOT / "backend"))

from app.simulation.semantic_program.analyze_contract import gan_bat_bien_nguon  # noqa: E402
from app.simulation.semantic_program.contract import SemanticProgramSpec  # noqa: E402
from app.simulation.semantic_program.plane_equation import bat_bien_mat_phang  # noqa: E402
from app.simulation.semantic_program.point_coordinate import bat_bien_toa_do  # noqa: E402
from app.simulation.semantic_program.segment_relation import bat_bien_chia_doan, bat_bien_do_dai  # noqa: E402
from app.simulation.semantic_program.coverage_gate import check_structural_coverage  # noqa: E402
from app.simulation.semantic_program.postconditions import (  # noqa: E402
    check_postconditions,
    check_source_invariants,
)
from app.simulation.semantic_program.request_contract import RequestContract  # noqa: E402


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = _load("w14census", W14 / "assumption_census.py")

# ── the text's shape constraints, written by hand from each text (point names = entity ids) ──

def _eq(mem, a, b, c, d):            # b − a == d − c
    return mem[b] - mem[a] == mem[d] - mem[c]


def _perp(mem, a, b, c, d):          # (b − a) · (d − c) == 0
    return (mem[b] - mem[a]).dot(mem[d] - mem[c]) == 0


def _len2(mem, a, b):
    return (mem[b] - mem[a]).dot(mem[b] - mem[a])


def _tinh_tien(top_of: dict):
    """Lateral edges are one translation: X' − X equal for every base vertex X."""
    goc = next(iter(top_of))
    return [(f"translation {x}{y} = {goc}{top_of[goc]}", lambda m, x=x, y=y: _eq(m, goc, top_of[goc], x, y))
            for x, y in top_of.items() if x != goc]


def _vuong_day(top_of: dict, a: str, b: str, c: str):
    x, y = next(iter(top_of.items()))
    return [(f"lateral {x}{y} ⊥ base", lambda m: _perp(m, x, y, a, b) and _perp(m, x, y, a, c))]


PRISM_RT = (_tinh_tien({"A": "D", "B": "E", "C": "F"}) + _vuong_day({"A": "D"}, "A", "B", "C")
            + [("right angle at A", lambda m: _perp(m, "A", "B", "A", "C"))])
PYR_RT = [("right angle at A", lambda m: _perp(m, "A", "B", "A", "C")),
          ("SA ⊥ (ABC)", lambda m: _perp(m, "A", "S", "A", "B") and _perp(m, "A", "S", "A", "C"))]
RECT = [("ABCD parallelogram", lambda m: _eq(m, "A", "B", "D", "C")),
        ("AB ⊥ AD", lambda m: _perp(m, "A", "B", "A", "D"))]
PYR_RECT = RECT + [("SA ⊥ (ABCD)", lambda m: _perp(m, "A", "S", "A", "B") and _perp(m, "A", "S", "A", "D"))]
HOP = {"A": "A_prime", "B": "B_prime", "C": "C_prime", "D": "D_prime"}
CUBOID = RECT + _tinh_tien(HOP) + _vuong_day(HOP, "A", "B", "D")
CUBE = CUBOID + [("cube: |AB| = |AD| = |AA'|",
                  lambda m: _len2(m, "A", "B") == _len2(m, "A", "D") == _len2(m, "A", "A_prime"))]
SQ_PRISM = CUBOID + [("square side 3", lambda m: _len2(m, "A", "B") == _len2(m, "A", "D") == 9),
                     ("height 7", lambda m: _len2(m, "A", "A_prime") == 49)]
N1 = [("rhombus MNPQ: M + P = N + Q", lambda m: _eq(m, "N", "M", "P", "Q")),
      ("rhombus MNPQ: |MN| = |NP|", lambda m: _len2(m, "M", "N") == _len2(m, "N", "P"))]
N2 = _tinh_tien({"A": "A_prime", "B": "B_prime", "C": "C_prime"})
T4 = PYR_RECT
SHAPE = {
    "ho:chop_tam_giac": PYR_RT, "rot:chop_tam_giac_xoay": PYR_RT, "ho:chop_chu_nhat": PYR_RECT,
    "ho:lang_tru_tam_giac": PRISM_RT, "rigid:prism_text_translate_swap": PRISM_RT,
    "ho:hop_chu_nhat": CUBOID, "ho:lap_phuong": CUBE, "ho:lang_tru_day_vuong": SQ_PRISM,
    "demo:n1_thoi_dinh_thu_tu": N1, "demo:n2_lang_tru_xien_hai_vecto": N2,
    "demo:t3_hop_tinh_tien_day_chuyen": CUBOID, "demo:t4_mat_xich_trong_chuoi_sau": T4,
    "ac1_given_length": PRISM_RT, "ac1_layout_derived": PRISM_RT, "ac1_model_assumption": PRISM_RT,
    "adv10_quan_he_claimed": PRISM_RT, "adv10_quan_he_gia_dinh": PRISM_RT,
    "adv10_quan_he_khong_nguon": PRISM_RT, "adv11_hai_dap_so_mot_ngoai_pham_vi": PRISM_RT,
    "adv8_nhan_vo_huong_gia_dinh": PRISM_RT,
}

# ── dry run of the planned vocabulary (NOT product code) ─────────────────────────────────

_P = r"[A-Z](?:['′]|_prime)?"
VOCAB = [
    ("pyramid_notation", re.compile(r"(?:hình|khối) chóp ([A-Z])\.([A-Z]{3,})")),
    ("prism_notation", re.compile(r"(lăng trụ(?: đứng| xiên)?|hình hộp(?: chữ nhật)?|hình lập phương) "
                                  r"([A-Z]{3,4})\.((?:[A-Z]['′]?){3,4})")),
    ("solid_type", re.compile(r"lăng trụ đứng|lăng trụ xiên|hình hộp chữ nhật|hình lập phương")),
    ("base_type", re.compile(r"đáy(?: ([A-Z]{3,5}))? là (hình chữ nhật|hình vuông|hình bình hành|hình thoi"
                             r"|tam giác vuông tại ([A-Z]))")),
    ("line_perp_plane", re.compile(rf"({_P}{_P}) vuông góc với (?:mặt phẳng )?(đáy|\(([A-Z]{{3,}})\))")),
    ("line_perp_line", re.compile(rf"({_P}{_P}) vuông góc với ({_P}{_P})(?![A-Za-zÀ-ỹ(])")),
    ("unnamed_square_prism", re.compile(r"lăng trụ đứng có đáy là hình vuông cạnh (\d+)")),
]


def _ids(s: str) -> list[str]:
    return [M._id(x) for x in re.findall(r"[A-Z](?:['′])?", s)]


def doc_tu_vung(text: str) -> tuple[list[dict], set]:
    """Matches + the relations they imply, as frozensets: ('perp_lines', {l1}, {l2}) / ('perp_plane', {l}, base)."""
    hits, rel = [], set()
    base_of = {}
    for name, rx in VOCAB:
        for m in rx.finditer(text):
            hits.append({"rule": name, "match": m.group(0), "span": [m.start(), m.end()]})
            if name == "pyramid_notation":
                base_of["day"] = tuple(_ids(m.group(2)))
            elif name == "prism_notation":
                day, tren = _ids(m.group(2)), _ids(m.group(3))
                base_of["day"] = tuple(day)
                if len(day) == len(tren) and m.group(1) in ("lăng trụ đứng", "hình hộp chữ nhật", "hình lập phương"):
                    for x, y in zip(day, tren):
                        rel.add(("perp_plane", frozenset((x, y)), frozenset(day)))
                if len(day) == 4 and m.group(1) in ("hình hộp chữ nhật", "hình lập phương"):
                    a, b, _c, d = day                    # rectangle/square base by type
                    rel.add(("perp_lines", frozenset((a, b)), frozenset((a, d))))
            elif name == "base_type" and m.group(3):
                tam = m.group(3)
                day = base_of.get("day", ())
                chan = [p for p in day if p != tam]
                if len(chan) == 2:
                    rel.add(("perp_lines", frozenset((tam, chan[0])), frozenset((tam, chan[1]))))
            elif name == "base_type" and m.group(2) in ("hình chữ nhật", "hình vuông"):
                day = base_of.get("day", ())
                if len(day) == 4:
                    a, b, c, d = day
                    rel.add(("perp_lines", frozenset((a, b)), frozenset((a, d))))
            elif name == "line_perp_plane":
                l = frozenset(_ids(m.group(1)))
                mp = frozenset(_ids(m.group(3))) if m.group(3) else frozenset(base_of.get("day", ()))
                if mp:
                    rel.add(("perp_plane", l, mp))
            elif name == "line_perp_line":
                rel.add(("perp_lines", frozenset(_ids(m.group(1))), frozenset(_ids(m.group(2)))))
            elif name == "unnamed_square_prism":
                rel.add(("UNNAMED_SINGLE_SOLID", frozenset(), frozenset()))
    return hits, rel


def _quan_he_doc_duoc(r, rel: set) -> bool | str:
    """True/False for a named reading; 'UNNAMED_BINDING' when only the unnamed single-solid rule
    could bind it (entities then come from the program's classified solid, not from the text)."""
    if ("UNNAMED_SINGLE_SOLID", frozenset(), frozenset()) in rel:
        return "UNNAMED_BINDING"
    if r.kind == "perpendicular_lines":
        a, b = frozenset(map(M._id, r.line)), frozenset(map(M._id, r.other_line))
        return ("perp_lines", a, b) in rel or ("perp_lines", b, a) in rel
    if r.kind == "perpendicular_line_plane":
        l, mp = frozenset(map(M._id, r.line)), frozenset(map(M._id, r.plane))
        return any(k == "perp_plane" and x == l and mp <= y for k, x, y in rel)
    return False


# ── per row ───────────────────────────────────────────────────────────────────────────────

def _bat_bien_moi(ct):
    return tuple(gan_bat_bien_nguon(ct.model_copy(update={"source_invariants": ()}), ct.problem_text)
                 .source_invariants or ())


def _bat_bien_chi_de(text: str) -> tuple:
    """The same four builders with NO contract: `_van_ban(None, text)` reads the text alone, so no
    entity binding can come from a model-written InputFact label."""
    return (bat_bien_do_dai(None, text) + bat_bien_chia_doan(None, text)
            + bat_bien_mat_phang(None, text) + bat_bien_toa_do(None, text))


def _ghim_mat_phang(stmt: dict, fresh) -> bool:
    """construct_plane_from_equation coefficients proportional to a text plane_equation invariant."""
    he = [F(str(stmt[k])) for k in ("a", "b", "c", "d")]
    for i in fresh:
        if i.kind == "plane_equation" and i.coefficients:
            g = [F(str(c)) for c in i.coefficients]
            k = next((g[j] / he[j] for j in range(4) if he[j] != 0), None)
            if k and all(g[j] == k * he[j] for j in range(4)):
                return True
    return False


def _inv(i) -> dict:
    return {"kind": i.kind, "points": list(i.points), "expected": i.expected,
            **({"coefficients": [str(c) for c in i.coefficients]} if i.coefficients else {})}


def _ghim(name: str, value, fresh) -> bool:
    """Is this declared point literal pinned by a text point_coordinate invariant for the SAME entity?"""
    for i in fresh:
        if i.kind == "point_coordinate" and [M._id(p) for p in i.points] == [M._id(name)]:
            return [F(str(c)) for c in i.coefficients] == [F(str(c)) for c in value]
    return False


def _kiem_nhan_chung(ct, ctf, sp2, chung, goc_val, shape) -> dict:
    try:
        res = M._chay(sp2)
    except Exception as e:  # noqa: BLE001
        return {"executed": False, "error": type(e).__name__}
    ten = check_structural_coverage(ct, sp2).ten_da_hoa_giai
    inv = check_source_invariants(ctf, res, ten_da_hoa_giai=ten)
    hinh = []
    for name, f in shape:
        try:
            ok = bool(f(res.final_memory))
        except KeyError as e:
            ok = None
            name = f"{name} (UNCHECKABLE: {e} not in memory)"
        hinh.append({"constraint": name, "holds": ok})
    post = check_postconditions(ct, sp2, res, ten_da_hoa_giai=ten)
    doi = {w: [goc_val.get(w), M._gia_tri(res.final_memory.get(w))] for w in chung.values()
           if M._gia_tri(res.final_memory.get(w)) != goc_val.get(w)}
    hong = ([f"text invariant: {v}" for v in inv.violated + inv.unresolved]
            + [h["constraint"] for h in hinh if h["holds"] is False]
            + [f"postcondition: {v}" for v in post.violations])
    return {"executed": True, "status": res.status, "text_invariants_ok": inv.ok,
            "text_invariants_checked": inv.checked, "text_invariants_not_checkable": inv.not_checkable,
            "shape_constraints": hinh, "postcondition_violations": [str(v) for v in post.violations],
            "witness_changes": doi, "broken_text_constraints": [str(h) for h in hong],
            "valid_witness": inv.ok and not any(h["holds"] is False for h in hinh) and not post.violations
            and all(h["holds"] is not None for h in hinh)}


def _ap_nhieu(d: dict, ten: str, k: int, phep: str) -> dict | None:
    return M._nhieu(d, ten, k, (lambda v: v * 2) if phep == "x2" else (lambda v: v + 1))


def do_hang(row: dict, w14: dict) -> dict:
    ct = RequestContract.model_validate(row["contract"])
    sp = M.hoan_thien_dung_hinh(SemanticProgramSpec.model_validate(row["program"]), ct).spec
    d = sp.model_dump(mode="json", exclude_none=True)
    res = M._chay(sp)
    chung = {k: v for k, v in M._nhan_chung(ct, sp).items()
             if M._gia_tri(res.final_memory.get(v)) is not None}
    goc_val = {w: M._gia_tri(res.final_memory.get(w)) for w in chung.values()}
    fresh = _bat_bien_moi(ct)
    ctf = ct.model_copy(update={"source_invariants": fresh})
    hits, rel = doc_tu_vung(ct.problem_text or "")
    facts = {f.fact_id: f for f in ct.input_facts}
    quan_he = [{"kind": r.kind, "line": list(r.line), "other_line": list(r.other_line), "plane": list(r.plane),
                "cites": r.source_fact_id, "cited_fact_exists": r.source_fact_id in facts,
                "cited_fact_provenance": facts[r.source_fact_id].provenance if r.source_fact_id in facts else None,
                "model_assumption": r.model_assumption, "text_states_it_dry_run": _quan_he_doc_duoc(r, rel)}
               for r in ct.geometric_relations]
    closure = M._bao_dong(d, set(chung.values()))
    lit = M._diem_literal(d)
    chi_de = _bat_bien_chi_de(ct.problem_text or "")
    ghim = {n: _ghim(n, lit[n], chi_de) for n in sorted(closure & set(lit))}
    mat = {s["target_var"]: _ghim_mat_phang(s, chi_de) for s in d["statements"]
           if s.get("kind") == "construct_plane_from_equation" and s.get("target_var") in closure}
    tu_nhan = sorted({json.dumps(_inv(i), ensure_ascii=False) for i in fresh}
                     - {json.dumps(_inv(i), ensure_ascii=False) for i in chi_de})
    do_hien = [{"target": s.target, "value": M._gia_tri(s.memory_snapshot.get(s.target))}
               for s in res.trace if s.semantic_kind == "MEASUREMENT"]
    shape = SHAPE.get(row["id"], [])
    out = {
        "id": row["id"], "group": row["group"], "label": row["label"], "text": ct.problem_text,
        "requested": [{"kind": o.kind, "witness": o.witness} for o in ct.obligations],
        "route_today": w14.get("route_today"),
        "w14": {k: w14.get(k) for k in ("verdict", "certificate", "c0", "c1", "ce", "ce_detail")},
        "stored_source_invariants": [_inv(i) for i in ct.source_invariants or ()],
        "text_invariants_today": [_inv(i) for i in fresh],
        "text_only_invariants": [_inv(i) for i in chi_de],
        "invariants_bound_only_through_inputfact_labels": [json.loads(x) for x in tu_nhan],
        "vocabulary_dry_run": hits,
        "typed_relations": quan_he,
        "text_shape_constraints": [n for n, _f in shape],
        "witness_closure": sorted(closure),
        "closure_point_literals_pinned_by_text": ghim,
        "closure_plane_equations_pinned_by_text": mat,
        "unpinned_dofs": sorted([n for n, ok in ghim.items() if not ok] + [n for n, ok in mat.items() if not ok]),
        "shown_numeric_values": do_hien,
        "shown_numeric_not_an_obligation": sorted({x["target"] for x in do_hien if x["value"] is not None}
                                                   - set(chung.values())),
        "original_values": goc_val,
        "original_shape_constraints_hold": all(f(res.final_memory) for _n, f in shape) if shape else None,
    }
    if w14.get("ce") == "UNSAFE":
        m = re.fullmatch(r"(\w+)\[(\d)\](x2|\+1)", w14["ce_detail"][0])
        d2 = _ap_nhieu(d, m.group(1), int(m.group(2)), m.group(3))
        out["w14_counterexample_recheck"] = {"perturbation": w14["ce_detail"][0],
                                             **_kiem_nhan_chung(ct, ctf, SemanticProgramSpec.model_validate(d2),
                                                                chung, goc_val, shape)}
    if row["group"] == "AC1" or row["id"] == "adv8_nhan_vo_huong_gia_dinh":
        d2 = d
        tu_do = ["D", "E", "F"] if row["group"] == "AC1" else ["M"]
        for p in tu_do:
            d2 = _ap_nhieu(d2, p, 2 if row["group"] == "AC1" else 0, "x2") or d2
        out["valid_witness_example"] = {
            "perturbation": f"{'+'.join(tu_do)} axis {'z' if row['group'] == 'AC1' else 'x'} ×2 together",
            **_kiem_nhan_chung(ct, ctf, SemanticProgramSpec.model_validate(d2), chung, goc_val, shape)}
    out["root_causes"] = nguyen_nhan(out)
    return out


RC_CLASS = {"RC1": "certificate", "RC2": "certificate (product provenance semantics)", "RC3": "certificate",
            "RC4": "validator", "RC5": "validator", "STALE_CONTRACT": "corpus/product (stored contract "
            "predates the text-invariant builders)"}


def nguyen_nhan(r: dict) -> list[dict]:
    ra = []
    w = r["w14"]
    if w["certificate"] is None and (w["c0"] or "").startswith("class-A/C") and r["closure_point_literals_pinned_by_text"] \
            and not r["unpinned_dofs"]:
        ra.append({"rc": "RC1", "why": "every closure literal (points, plane equations) is pinned by a text-only "
                                       "invariant of the same entity, yet W14 C0 rejected it as class A/C"})
    c1 = w["c1"] or ""
    if "not a confirmed InputFact" in c1 or "STRUCTURED_RELATION" in c1:
        stated = [q for q in r["typed_relations"] if q["text_states_it_dry_run"]]
        missing = [q["cites"] for q in r["typed_relations"] if not q["cited_fact_exists"]]
        ra.append({"rc": "RC2", "why": (f"W14 C1 judged relations by their annotation (cited InputFact provenance "
                                        f"/ source_fact_id / model_assumption); {len(stated)}/"
                                        f"{len(r['typed_relations'])} relations are read from the text by the "
                                        f"dry run; cited fact ids that do not exist: {missing}")})
    if "fact graph UNSUPPORTED_INCOMPLETE" in (w["c1"] or "") and r["unpinned_dofs"]:
        ra.append({"rc": "RC3", "why": ("template configuration with unpinned DOFs, but the stored contract "
                                        "carries no typed relations/solid_topology for the compiler recognizer")})
    if not r["stored_source_invariants"] and r["text_invariants_today"]:
        ra.append({"rc": "STALE_CONTRACT", "why": f"stored contract has 0 source invariants; today's builders "
                                                  f"emit {len(r['text_invariants_today'])}"})
    ce = r.get("w14_counterexample_recheck")
    if ce and not ce.get("valid_witness"):
        rc = "RC4" if r["label"] == "INVARIANT" else "RC5"
        ra.append({"rc": rc, "why": f"W14 witness {ce['perturbation']} breaks: {ce.get('broken_text_constraints')}"})
    return [{**x, "class": RC_CLASS[x["rc"]]} for x in ra]


def main() -> None:
    for p in (OUT_JSON, OUT_MD):
        if p.exists():
            raise SystemExit(f"refusing to overwrite {p}")
    corpus = json.loads((W14 / "assumption_corpus" / "CORPUS.json").read_text(encoding="utf-8"))
    census = {r["id"]: r for r in json.loads(CENSUS.read_text(encoding="utf-8"))["rows"]}
    rows = [do_hang(r, census[r["id"]]) for r in corpus["rows"] if r["group"] in ("AC2", "AC1", "CERT_LIMIT")]
    false_ce = [r["id"] for r in rows if r["label"] == "INVARIANT" and r["w14"]["ce"] == "UNSAFE"]
    summary = {
        "rows": len(rows),
        "w14_false_counterexamples": false_ce,
        "false_counterexamples_whose_witness_breaks_a_text_constraint": [
            i for i in false_ce if not next(r for r in rows if r["id"] == i)["w14_counterexample_recheck"]["valid_witness"]],
        "ac1_served_today": [r["id"] for r in rows if r["group"] == "AC1" and (r["route_today"] or {}).get("servable")],
        "ac1_w14_witness_valid": {r["id"]: r["w14_counterexample_recheck"]["valid_witness"]
                                  for r in rows if r["group"] == "AC1"},
        "ac1_valid_witness_example": {r["id"]: [r["valid_witness_example"]["valid_witness"],
                                                r["valid_witness_example"]["witness_changes"]]
                                      for r in rows if r["group"] == "AC1"},
        "rows_by_root_cause": {rc: [r["id"] for r in rows if any(x["rc"] == rc for x in r["root_causes"])]
                               for rc in RC_CLASS},
        "ac2_rows_without_root_cause": [r["id"] for r in rows if r["group"] == "AC2" and not r["root_causes"]],
        "rows_showing_numeric_values_outside_obligations": {r["id"]: r["shown_numeric_not_an_obligation"]
                                                            for r in rows if r["shown_numeric_not_an_obligation"]},
        "rows_with_invariants_bound_only_through_inputfact_labels": {
            r["id"]: r["invariants_bound_only_through_inputfact_labels"]
            for r in rows if r["invariants_bound_only_through_inputfact_labels"]},
        "corpus_corrections": "none — GOLD_ROW_VERIFICATION.json: 18/18 rows determined, 18/18 oracle == served",
        "findings_for_the_design": [
            "F1 RC1: the 8 coordinate rows pin every closure literal (points; plane equations in p1/p6/p7) by a "
            "text-only invariant of the same entity — see closure_*_pinned_by_text.",
            "F2 RC2: W14 C1 judged typed relations by their annotation; the dry run reads every typed relation of "
            "the template rows from the text (ho:lang_tru_day_vuong only through the unnamed single-solid rule); "
            "the six-family fixtures cite InputFact ids that do not exist — see typed_relations.",
            "F3 RC3: the demo contracts t3/t4 carry no typed relations or solid_topology — see typed_relations.",
            "F4 RC4: all 11 W14 counterexamples on INVARIANT rows break a text constraint — see "
            "w14_counterexample_recheck.broken_text_constraints.",
            "F5 RC5: the AC1 witnesses move one top vertex (prism broken); moving D, E, F together keeps every "
            "text constraint and changes V 30 → 60 — a valid DEPENDENT witness exists.",
            "F6 STALE_CONTRACT: the 4 demo contracts store 0 source invariants; the gate must re-read the text.",
            "F7 the bat_bien_* builders read InputFact labels too (_van_ban): ho:lap_phuong AB = 4 and "
            "ho:lang_tru_day_vuong AA' = 7 / AB = 3 are entity-bound only through model labels. Certificate "
            "premises must come from the text alone (builders called with contract=None), and the shape reader "
            "must bind 'cạnh bằng N' of a named cube and the unnamed single solid itself.",
            "F8 the section T of p1 is written by 4 section_edge sub-steps + 1 construct_section step of ONE "
            "statement (GOLD_ROW_VERIFICATION closure_names_written_more_than_once); a reaching-definition rule "
            "that counts trace writes per name must group a statement's sub-steps or p1 becomes UNDETERMINED.",
            "F9 every template row shows intermediate numeric values (base area, solid volume, lengths) that are "
            "not obligations; adv11 shows g = cos² and adv8 shows k = |AM|. W14 fixture (11) asks for cos² but its "
            "obligation kind 'angle_cos_sq' is not in OBLIGATION_KINDS, so build_request_contract drops it: the "
            "substance of test (11) holds only if the certificate covers every numeric value the learner is "
            "shown, not only obligation witnesses.",
            "F10 adv8: moving the arbitrary M breaks the volume postcondition (V·|AM| ≠ solid volume), so no valid "
            "witness exists ⇒ UNDETERMINED (refused), never PROVEN_SAFE (M's literal has no role).",
            "F11 the W14 corpus reason for adv10_* ('C1 must not be granted') conflated the annotation with the "
            "source: their text states 'lăng trụ đứng'. Per R2 the W15 corpus restates the expectation in a new "
            "layer (text-silent variants refused; annotation never a premise).",
        ],
    }
    OUT_JSON.write_text(json.dumps({"table": "W15_TRACK_B_ROOT_CAUSE_TABLE", "model_calls": 0,
                                    "w14_census_reproduced": "w14_census_reproduction/ASSUMPTION_CENSUS.json",
                                    "rows": rows, "summary": summary},
                                   ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8", newline="\n")
    md = ["# W15 Track B — root-cause table (generated by `track_b_table.py`; 0 model calls)", "",
          "| row | label | W14 verdict | W14 CE witness | witness valid? | unpinned DOFs | root causes |",
          "|---|---|---|---|---|---|---|"]
    for r in rows:
        ce = r.get("w14_counterexample_recheck")
        md.append(f"| `{r['id']}` | {r['label']} | {r['w14']['verdict']} | {(ce or {}).get('perturbation', '—')} | "
                  f"{'—' if not ce else ce['valid_witness']} | {', '.join(r['unpinned_dofs']) or '—'} | "
                  f"{', '.join(x['rc'] for x in r['root_causes']) or '—'} |")
    md += ["", "Summary: see `summary` in the JSON. RC classes: " +
           "; ".join(f"{k} = {v}" for k, v in RC_CLASS.items()), ""]
    OUT_MD.write_text("\n".join(md), encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
