"""Fault injection, named-plane slice after the witness/identity fix: one textual fault at a time, run the slice tests,
restore, verify the file bytes are identical."""
import hashlib, json, os, pathlib, re, subprocess, sys

WT = pathlib.Path(r"D:\Documents\projects\algo-sim\.superpowers\worktrees\hybrid-v2-backend-generalization\backend")
PY = r"D:\Documents\projects\algo-sim\backend\.venv\Scripts\python.exe"
G = "app/simulation/geometry_functions/"
TESTS = ["tests/geometry/test_typed_fact_next_v2_named_plane.py", "tests/geometry/test_typed_fact_next_v2_angle_bridge.py",
         "tests/geometry/test_typed_fact_next_v2_distance_bridge.py"]
NL = "\n"
FAULTS = [
    ("F1 planner forgets the full distance plane", G + "planner.py",
     '                k.named_planes.append({"call": f.id, "labels": list(b)})' + NL, "                pass" + NL),
    ("F2 route drops named_planes", "app/ai/function_route.py", ', "named_planes": k.named_planes}', "}"),
    ("F3 engine ignores named planes", G + "engine.py",
     'named = plan.get("named_planes") or [] if isinstance(plan, dict) else []', "named = []"),
    ("F4 witness selection disabled", G + "engine.py", "        dung.chon_ba_mat(named)" + NL, ""),
    ("F5 witness is always the first three labels", G + "engine.py",
     "for a, b, c in combinations(nhan, 3)", "for a, b, c in [tuple(nhan[:3])]"),
    ("F6 witness ignores collinearity", G + "engine.py",
     "if not (Vec3(*self.pts[b]) - Vec3(*self.pts[a]))", "if True or not (Vec3(*self.pts[b]) - Vec3(*self.pts[a]))"),
    ("F7 distance witness taken from the truncated call", G + "engine.py",
     'g = day_du.get(c.id, g) if c.fn == "ask_distance_point_plane" else list(g)', "g = list(g)"),
    ("F8 IR plane loses its written name", G + "engine.py", "if g := self.ten_mat_hoi.get((c.id, key)):", "if False:"),
    ("F9 coplanarity check skips named groups", G + "engine.py", "for g in [*nhom, *named, *goi]:", "for g in [*nhom, *goi]:"),
    ("F10 bridge back to exactly three plane labels", G + "typed_fact_next_bridge.py",
     "(len(v) >= n if n == 3 else len(v) == n)", "len(v) == n"),
    ("F11 bridge accepts repeated labels", G + "typed_fact_next_bridge.py", "len(set(refs)) == len(refs)", "True"),
    ("F12 bridge truncates the distance plane", G + "typed_fact_next_bridge.py",
     '"points_a": [_ref(t["point"])], "points_b": pl}', '"points_a": [_ref(t["point"])], "points_b": pl[:3]}'),
    ("F13 bridge truncates the angle plane", G + "typed_fact_next_bridge.py",
     '"points_a": ln, "points_b": pl}', '"points_a": ln, "points_b": pl[:3]}'),
    ("F14 bridge accepts lines longer than two labels", G + "typed_fact_next_bridge.py",
     "(len(v) >= n if n == 3 else len(v) == n)", "len(v) >= n"),
    ("F15 line-plane angle returns sin2 (wrong convention)", G + "engine.py",
     "        return Fraction(1) - sin2" + NL, "        return sin2" + NL),
    ("F16 Source Gate accepts any plane quote", G + "registry.py",
     "return tap is not None and len(tap & target) >= 3 and (tap <= target or target <= tap)", "return tap is not None"),
]
rows = []
env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
for name, rel, old, new in FAULTS:
    f = WT / rel
    raw = f.read_bytes()
    before = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8")
    if "\r\n" in text:
        old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
    assert text.count(old) == 1, f"{name}: anchor occurs {text.count(old)} times"
    f.write_bytes(text.replace(old, new).encode("utf-8"))
    try:
        r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", *TESTS], cwd=WT, capture_output=True, env=env)
        out = r.stdout.decode("utf-8", "replace")
        summary = out.strip().splitlines()[-1]
        failed = sorted({m.split("::", 1)[1] for m in re.findall(r"^FAILED (\S+)", out, re.M)})
    finally:
        f.write_bytes(raw)
    after = hashlib.sha256(f.read_bytes()).hexdigest()
    rows.append({"fault": name, "file": rel, "summary": summary, "failed": failed, "restored_identical": before == after})
    print(f"{name}: {summary} restored={before == after}")
json.dump(rows, open(sys.argv[1], "w", encoding="utf-8"), indent=2, ensure_ascii=False)
