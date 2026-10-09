"""Run from a backend/ directory: python <path>/probe_c1_equivalence.py — C1 (no coordinates) outcome of every row of the
regular-square- and regular-triangular-pyramid corpora whose givens say 'hình chóp tứ/tam giác đều X.Y', on the
canonical text and on rewrites (labels.json `c1_rule`): apex_base = 'có đỉnh X và đáy Y', regular_notation = 'chóp đều
X.Y'; and, to measure the unnamed gap only: unnamed = 'hình chóp tứ/tam giác đều' with no notation in the givens,
unnamed_everywhere = also no notation in the question. Same LLM-style program per row; 0 model calls."""
import json, os, re, sys
sys.path.insert(0, os.getcwd())
from app.simulation.semantic_program.shape_constraint import doc_rang_buoc
from tests.geometry import test_regular_square_pyramid as SQ, test_regular_triangular_pyramid as TR

CANON = re.compile(r"(?P<noun>[Hh]ình|[Kk]hối) chóp (?P<g>tứ|tam) giác đều (?P<S>[A-Z])\.(?P<b>[A-Z]{3,4})(?![A-Za-z'])")
VARIANTS = {
    "apex_base": lambda m: f"{m['noun']} chóp {m['g']} giác đều có đỉnh {m['S']} và đáy {m['b']}",
    "regular_notation": lambda m: f"{m['noun']} chóp đều {m['S']}.{m['b']}",
    "unnamed": lambda m: f"{m['noun']} chóp {m['g']} giác đều",
}


def outcome(mod, ca):
    try:
        k = mod.ket_qua(ca)
    except Exception as e:  # noqa: BLE001
        return f"error:{type(e).__name__}"
    return f"served:{k['served']}" if "served" in k else f"refused:{k['stage']}:{k['reason_code']}"


def kinds(text):
    return sorted({(r.kind, r.entities, r.value) for r in doc_rang_buoc(text)}, key=str)


for name, mod in (("square", SQ), ("triangular", TR)):
    for ca in sorted(mod.NHAN):
        goc = dict(mod.NHAN[ca])
        m = CANON.search(goc["text"])
        if not m:
            continue
        texts = {"canonical": goc["text"]}
        for v, f in VARIANTS.items():
            texts[v] = goc["text"][:m.start()] + f(m) + goc["text"][m.end():]
        texts["unnamed_everywhere"] = re.sub(r"\s+[A-Z]\.[A-Z]{3,4}(?![A-Za-z'])", "", texts["unnamed"])
        for v, t in texts.items():
            mod.NHAN[ca] = {**goc, "text": t}
            print(json.dumps({"corpus": name, "row": ca, "variant": v, "outcome": outcome(mod, ca),
                              "reader_equals_canonical": [(k, e, str(x)) for k, e, x in kinds(t)] ==
                              [(k, e, str(x)) for k, e, x in kinds(goc["text"])]}, ensure_ascii=False))
        mod.NHAN[ca] = goc
