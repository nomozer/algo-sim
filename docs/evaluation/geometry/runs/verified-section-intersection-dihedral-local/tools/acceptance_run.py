"""Text- and image-to-simulation acceptance for this run: the previous run's harness, unchanged, with (1) receipts written
here and (2) the scene checks replaced by this run's sign-aware independent checks (verify_constructions.check).
Same 27-item corpus (25 controlled-vision images/transcriptions, development-exposed, + the 2 previous fresh items).
Run from backend/:  python <tools>/acceptance_run.py text|image   (image needs measured_app on :8767)
"""
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(Path(__file__).resolve().parent), str(RUN.parent / "semantic-to-scene3d-verified-simulation/tools")]
import simulation_acceptance as SA  # noqa: E402  (previous run's harness)
import verify_constructions as VC  # noqa: E402

SA.RUN = RUN


def _check_scene(_name, scene):
    return VC.check("any", scene)


SA.check_scene = _check_scene
if __name__ == "__main__":
    {"text": SA.text, "image": SA.image}[sys.argv[1]]()
