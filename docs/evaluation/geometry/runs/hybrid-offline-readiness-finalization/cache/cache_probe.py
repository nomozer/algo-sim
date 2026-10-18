# Cache-impact probe: same inputs, run once per tree (sys.path[0] = <tree>/backend). Prints the GIVEN-length evidence
# verdict of the default route's grounding gate (`_bang_chung_do_dai`) — the served/refused hinge for a GIVEN length.
import json, sys
from fractions import Fraction
from app.simulation.semantic_program.grounding_gate import _bang_chung_do_dai

CASES = [
    # (problem text, segment the program declares GIVEN, value)
    ("Cho tứ diện ABCD có AB = 3 và AB + CD = 5. Tính thể tích.", "CD", Fraction(5)),
    ("Cho hình chóp S.ABC có SA = 2 và SA.BC = 6. Tính SB.", "BC", Fraction(6)),
    ("Cho tam giác ABC có trọng tâm G, GA + GB + GC = 0 và AB = 3.", "GC", Fraction(0)),
    ("Cho hình chóp S.ABCD có đáy vuông cạnh 2, SA = 3. Tính lại khi SA = 5.", "SA", Fraction(5)),
    # controls: unaffected texts must keep their verdict
    ("Cho tam giác ABC có AB = 3, AC = 4. Tính BC.", "AB", Fraction(3)),
    ("Cho hình chóp S.ABCD có SA = SB = SC = SD = 2.", "SC", Fraction(2)),
    ("Cho hình chóp S.ABCD. SA = 3. Tính thể tích.", "SA", Fraction(3)),
]
out = []
for de, seg, v in CASES:
    ma, bc, ly_do = _bang_chung_do_dai(de, f"{seg}_length", v, None)
    out.append({"text": de, "given": f"{seg} = {v}", "verdict": "EVIDENCED" if ma is None else ma, "reason": ly_do})
print(json.dumps(out, ensure_ascii=False, indent=1))
