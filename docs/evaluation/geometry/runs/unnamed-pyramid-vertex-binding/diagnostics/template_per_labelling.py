"""Run from backend/: feasibility probe for option (b) built ONLY from the product's reader + T7/T8 templates.
For each of the 21 rows and EACH injective labelling of its named vertices onto the pyramid's positions (unused
positions get fresh letters), the text is rewritten with the canonical notation for that labelling
('hình chóp tứ giác đều S.ABCD') and read by the product (`_doc_de`, `_khuon_chop`). A template-only decision then is:
contradiction ⇒ labelling excluded; dimensions fixed ⇒ volume known; otherwise open. Compared with oracle.py."""
import itertools, json, os, re, sys
from pathlib import Path
sys.path.insert(0, os.getcwd())
from app.simulation.geometry.radical import square
from app.simulation.semantic_program.assumption_gate import _Khuon, _doc_de, _khuon_chop
ROWS = json.loads((Path(__file__).resolve().parents[1] / "labels.json").read_text(encoding="utf-8"))["rows"]
CHOP = re.compile(r"(?P<n>[Hh]ình|[Kk]hối) chóp (?P<g>tứ|tam) giác đều")
out = {}
for rid, r in ROWS.items():
    f, text = r["facts"], r["text"]
    k = 5 if f["kind"] == "square" else 4
    spare = [c for c in "PQRTUVXYZ" if c not in text]
    tally, vols, opened = {}, set(), 0
    for perm in itertools.permutations(range(k), len(f["names"])):
        slot = [None] * k
        for nm, i in zip(f["names"], perm):
            slot[i] = nm
        free = iter(spare)
        slot = [s or next(free) for s in slot]
        apex, base = slot[-1], slot[:-1]
        m = CHOP.search(text)
        t2 = text[:m.end()] + f" {apex}.{''.join(base)}" + text[m.end():]
        _gt, rb, _inv, do_dai = _doc_de(t2)
        kh = _khuon_chop(rb, apex, tuple(base), (apex, *base), do_dai)
        if isinstance(kh, _Khuon):
            dims = [kt.gia_tri for kt in kh.kich_thuoc]
            if all(x is not None for x in dims) and f["ask"] == "volume":
                s2, h2 = square(dims[0]), square(dims[1])
                vols.add(str(s2 * s2 * h2 / (9 if k == 5 else 48)))
                key = "template: dimensions fixed"
            else:
                opened += 1
                key = "template: matched, answer open (missing dimension or asked length not produced)"
        else:
            key = "template: " + kh.split(":")[0]
        tally[key] = tally.get(key, 0) + 1
    tmpl = ("contradiction" if not vols and not opened else "ambiguous" if len(vols) > 1
            else "open" if opened else "determined V²=" + next(iter(vols)))
    out[rid] = {"oracle": r["text_verdict"], "template_only": tmpl, "labellings": tally}
    print(json.dumps({"row": rid, **out[rid]}, ensure_ascii=False))
