"""Derived JSON deliverables of /11 from raw evidence already on disk (no measurement happens here).

Writes SLM_RECOVERY_ABLATION.json, V17_POINTER_INTERACTION_RESULTS.json, PARSER_GENERALIZATION_TEST_RESULTS.json.
The parser/Source Gate/SLM contract test counts are produced by running pytest on the named test files (offline, 0 AI).
usage (from the run directory): python tools/write_v11_derived.py <backend_dir> <python_exe>
"""

import json
import re
import subprocess
import sys
from pathlib import Path

EV = Path("evidence")
rd = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
wr = lambda p, o: Path(p).write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")

abl = rd(EV / "slm20" / "slm_grammar_ablation.json")
arm = lambda f: {r["case_id"]: r["arm_A_product"] for r in rd(EV / "slm20" / f"slm20_audit_{f}.json")["rows"]}
base, after = arm("baseline"), arm("after_fix")
srv = lambda d, mode=None: sorted(k for k, a in d.items() if a.get("status") == "SERVED" and (mode is None or a.get("extraction_mode") == mode))
wr("SLM_RECOVERY_ABLATION.json", {
    "schema": "axo-v11-slm-recovery-ablation/1",
    "set": abl["set"], "model": abl["model"], "exposed": True,
    "grammar_variants": {"U": "SIM_ONLY_UNRESOLVED_WITHOUT_FACTS = False", "S": "SIM_ONLY_UNRESOLVED_WITHOUT_FACTS = True (product)"},
    "grammar_ablation_summary": abl["summary"],
    "slm20_product_route": {
        "baseline_code": "2f12b96b0 (/10)", "after_fix_code": "fcf68e91b",
        "baseline_served": srv(base), "after_fix_served": srv(after),
        "after_fix_served_by_parser": srv(after, "LOCAL_DETERMINISTIC_PARSER"),
        "after_fix_served_by_slm": srv(after, "LOCAL_SLM_GROUNDED"),
        "after_fix_oracle_valid": sorted(k for k, a in after.items() if (a.get("oracle") or {}).get("scene_validation") == "MATHEMATICALLY_VALID"),
        "control_cases": ["V13", "V18", "C24", "C20"]},
    "reading": "the contract fix makes SLM output valid far more often (slm_ok U 35 -> S 51) but on this exposed set the recovered "
               "cases are mostly served by the generalized parser before the SLM runs; SLM-pure contribution is measured on the "
               "blind SLM_REQUIRED stratum (V11_SLM_STRATUM_RESULTS.json)"})

tr = {t: rd(EV / "v17" / f"pointer_trace_{t}.json") for t in ("baseline_pre_fix_dist", "baseline", "after_fix")}
summ = lambda d: [{k: r.get(k) for k in ("where", "delay_ms", "rotated", "frame_pixel_diff", "labels_moved", "aria_pressed_after_click")}
                  | {"element_under_start": (r.get("element_under_start") or {}).get("cls")} for r in d["results"]]
wr("V17_POINTER_INTERACTION_RESULTS.json", {
    "schema": "axo-v11-v17-pointer/1", "text": tr["after_fix"]["text"], "browser": tr["after_fix"]["browser"],
    "root_cause": "the measurement chip .geo3d-so-do (role=button, pointer-events:auto) sits at the canvas centre and receives "
                  "pointerdown; OrbitControls listens on the canvas, so a drag starting on the chip never reached it",
    "fix": "b15fd9e92 scene3d-view.tsx: a drag that starts on an overlay and moves >= 4 px is forwarded to the canvas "
           "(synthetic pointerdown at the start point + pointermove); a click without movement stays on the chip",
    "traces": {k: summ(v) for k, v in tr.items()},
    "centre_drag_rotated": {k: f"{sum(bool(r.get('rotated')) for r in v['results'] if r.get('where') == 'centre')}/"
                               f"{sum(r.get('where') == 'centre' for r in v['results'])}" for k, v in tr.items()},
    "chip_click_aria_pressed_note": "false in both the pre-fix build and the fixed build: pre-existing, not a regression"})

backend, py = Path(sys.argv[1]), sys.argv[2]
suites = {"source_gate_simulation_request_nouns": "tests/geometry/test_source_gate_simulation_request_nouns.py",
          "local_parser_simulation_intent": "tests/geometry/test_local_parser_simulation_intent.py",
          "slm_simulation_only_contract": "tests/geometry/test_slm_simulation_only_contract.py"}
res = {}
for k, f in suites.items():
    out = subprocess.run([py, "-m", "pytest", f, "-q", "-p", "no:warnings"], cwd=backend, capture_output=True, text=True,
                         env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"}).stdout
    m = re.search(r"(\d+) passed", out); f_ = re.search(r"(\d+) failed", out)
    res[k] = {"file": f"backend/{f}", "passed": int(m.group(1)) if m else 0, "failed": int(f_.group(1)) if f_ else 0}
wr("PARSER_GENERALIZATION_TEST_RESULTS.json", {
    "schema": "axo-v11-parser-generalization-tests/1", "offline": True, "ai_calls": 0, "suites": res,
    "design": "SIMULATION_INTENT_GENERALIZATION_DESIGN.md",
    "known_limit": "a request ending in '!' is read by the parser but refused by the Source Gate sentence end (locked); "
                   "excluded from the metamorphic set and listed in OWNER_HANDOFF.md"})
print(json.dumps(res))
