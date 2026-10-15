import sys
p, which = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8", newline="").read()
B = "\\"
old = {"phu": ' and not re.search(r"(?i:' + B + 'b(?:bình' + B + 's+phương|nửa)' + B + 'b)", s[_bien_cau(s, dau)[0]:dau])',
       "rb": " or re.search(r'(?i:" + B + "b(?:bình" + B + "s+phương|nửa)" + B + "b)',de[_bien_cau(de,vt+m.start())[0]:vt+m.start()])"}[which]
assert s.count(old) == 1, which
open(p, "w", encoding="utf-8", newline="").write(s.replace(old, ""))
print("mutated", which)
