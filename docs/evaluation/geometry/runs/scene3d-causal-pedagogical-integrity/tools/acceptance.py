"""Text- and image-to-simulation acceptance of run `scene3d-causal-pedagogical-integrity` (tool copied from proof-soundness-generalized-angle-invariance) (tool copied from compositional-semantics-simulation-goals) on the 27 development-exposed
items: the semantic-to-scene3d harness unchanged (sign-aware independent scene checks of verified-section-intersection-
dihedral-local), receipts written to THIS run. One grading change, declared before measurement: a served item whose
response carries `source_goal_completion` (the source asks a trigonometric VALUE of the angle) is never counted as a
numeric answer — its grade becomes GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED whatever the dataset key comparison says.

Run from backend/:  python <tools>/acceptance.py text|image   (image needs measured_app on :8767)
"""
import importlib.util
import os
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RUN.parent / "semantic-to-scene3d-verified-simulation/tools")]
import simulation_acceptance as SA  # noqa: E402  (earlier run's harness)

_s = importlib.util.spec_from_file_location("vc_prev", RUN.parent / "verified-section-intersection-dihedral-local/tools/verify_constructions.py")
VC = importlib.util.module_from_spec(_s)
_s.loader.exec_module(VC)
SA.RUN = RUN
SA.check_scene = lambda _name, scene: VC.check("any", scene)

_write = SA.write


def _numeric_not_answered() -> set[str]:
    os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
    from app.ai.adaptive_input_router import route_text_input
    return {i["case_id"] for i in SA.corpus()
            if ((route_text_input(i["statement"], allow_live_ai=False).response or {}).get("route_d") or {}).get("source_goal_completion")}


def write(name, rows, extra):
    nna = _numeric_not_answered()
    for r in rows:
        if r["case_id"] in nna and r["outcome"] not in ("UNSUPPORTED", "SAFE_REFUSAL", "OUT_OF_SCOPE"):
            r["grade_dataset_key_comparison"] = r["grade"]
            r["grade"] = "GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED"
    out = {"text": "local_text_to_simulation_acceptance.json", "image": "local_image_to_simulation_acceptance.json"}[sys.argv[1]]
    _write(out, rows, {**extra, "grading_note": "source_goal_completion ⇒ GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED (never a numeric answer)",
                       "numeric_source_goal_not_answered": sorted(nna & {r["case_id"] for r in rows})})


SA.write = write
if __name__ == "__main__":
    {"text": SA.text, "image": SA.image}[sys.argv[1]]()
