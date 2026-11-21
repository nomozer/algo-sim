"""Text- and image-to-simulation acceptance on the same 27 development-exposed items (25 controlled-vision images and
transcriptions + 2 earlier fresh items): the semantic-to-scene3d harness unchanged, receipts written to this run, scene
checks = the sign-aware independent checks of verified-section-intersection-dihedral-local. Renamed afterwards to
local_text_to_simulation_acceptance.json / local_image_to_simulation_acceptance.json.
Run from backend/:  python <tools>/acceptance_run.py text|image   (image needs measured_app on :8767)
"""
import importlib.util
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
if __name__ == "__main__":
    {"text": SA.text, "image": SA.image}[sys.argv[1]]()
