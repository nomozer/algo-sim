import sys, types
from pathlib import Path
sys.path.insert(0, ".")
from app.ai.function_route import run_fact_route
from app.simulation.geometry_functions import registry as RG, engine as EN
from tests.geometry import hybrid_compiler_benchmark as HB
MUT = {
 "asserted-value": ("if (so := _GIA_TRI.search(gan)) and not _HOI_SAU.search(gan[:so.start()]):", "if False:"),
 "object-blocker": ("qua_dong_tu = bool(dong_tu) and not _CHAN_TAN_NGU.search(", "qua_dong_tu = bool(dong_tu) or not _CHAN_TAN_NGU.search("),
 "yes-no": ("    if _CO_KHONG.search(gan) and not", "    if False and not"),
 "gan-gia-tri": (" and not _GAN_GIA_TRI.match(de[m.end():])", ""),
}
def routes(sent):
    out = {}
    for name, fact in [("line", lambda q: HB._ask("q", q, "distance", points_a=["S"], points_b=["B","D"])),
                       ("plane", lambda q: HB._ask("q", q, "distance", points_a=["S"], points_b=list("ABCD")))]:
        s = sent.replace("{O}", "khoảng cách từ S đến BD" if name == "line" else "khoảng cách từ S đến (ABCD)")
        q, f = HB._with(HB._square(), fact(s))
        try:
            r = run_fact_route(" ".join(q), {"facts": f}); out[name] = (r.status, r.code)
        except Exception as e:
            out[name] = ("EXC", type(e).__name__)
    return out
SENT = ["Tính {O}.", "{O} bằng bao nhiêu?", "Khoảng cách: {O}.", "{O}.",
        "Tính {O} (kết quả bằng 3).", "Tính {O} (làm tròn đến 3).", "Tính {O} (kết quả là 3).", "Tính {O} (kết quả 3).",
        "Tính {O} (kết quả có lớn hơn 3 không).", "Tính {O} (làm tròn, có không).",
        "Tính {O} biết = 3.", "Tính {O} biết bằng 3.", "Tính {O} rồi cộng 3.", "Tính {O} theo a bằng 3.",
        "{O} có giá trị 3 không?", "{O} bằng 3 không?", "Tính SC theo {O}.", "Hỏi {O} bằng bao nhiêu?",
        "{O} là bao nhiêu (kết quả bằng 3)?", "Tính {O} và cho biết nó bằng 3.", "Tính {O} đã cho bằng 3."]
base = {s: routes(s) for s in SENT}
src = Path(RG.__file__).read_text(encoding="utf-8")
for name, (old, new) in MUT.items():
    assert src.count(old) == 1, name
    m = types.ModuleType(RG.__name__ + "_mutant"); m.__package__ = RG.__package__
    sys.modules[m.__name__] = m
    exec(compile(src.replace(old, new), RG.__file__, "exec"), m.__dict__); m.TuChoi = RG.TuChoi
    orig = EN.kiem_nguon; EN.kiem_nguon = m.kiem_nguon
    kills = []
    for s in SENT:
        mr = routes(s)
        for k in mr:
            if mr[k] != base[s][k] and (mr[k][0] == "SERVED") != (base[s][k][0] == "SERVED"):
                kills.append((s, k, base[s][k], mr[k]))
    EN.kiem_nguon = orig
    print(name, "KILLS:", kills or "NONE")
print("BASE served:", [(s, k) for s in SENT for k, v in base[s].items() if v[0] == "SERVED"])
