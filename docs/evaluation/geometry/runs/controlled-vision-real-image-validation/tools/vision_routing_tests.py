"""Run the existing offline Vision-routing safety tests and record each test's outcome. No provider call:
the pytest network guard in backend/conftest.py stays active and ALLOW_LIVE_AI=0.  Run from backend/.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
FILES = ["tests/geometry/test_adaptive_input_router.py", "tests/geometry/test_correctness_ocr_performance.py",
         "tests/geometry/test_verified_image_to_3d_pipeline.py", "tests/test_image_first_local_ocr.py",
         "tests/geometry/test_independent_h1_real_world_acceptance.py"]
SELECT = "vision or Vision or live or LIVE or adaptive or fidelity or conflict or reread or fallback or route"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "junit.xml"
        done = subprocess.run([sys.executable, "-m", "pytest", *FILES, "-q", "-p", "no:cacheprovider", "-k", SELECT, f"--junitxml={xml}"],
                              capture_output=True, text=True, env={**os.environ, "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": ""})
        cases = []
        for case in ET.parse(xml).getroot().iter("testcase"):
            outcome = "failed" if case.find("failure") is not None or case.find("error") is not None else "skipped" if case.find("skipped") is not None else "passed"
            cases.append({"test": f"{case.get('classname')}::{case.get('name')}", "outcome": outcome})
    (RUN / "vision_routing_safety_tests.json").write_text(json.dumps({
        "run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "classification": "OFFLINE_ROUTING_TESTS_NOT_VISION_QUALITY",
        "command": f"python -m pytest {' '.join(FILES)} -k \"{SELECT}\"", "exit_code": done.returncode,
        "outcomes": dict(Counter(c["outcome"] for c in cases)), "provider_calls": 0,
        "what_these_prove": ["Vision is not called when ALLOW_LIVE_AI=0 or no key (fail-closed 503, not a silent fallback)",
                             "OCR/Vision fact conflicts (numbers, dimension binding, primes, planes) force student confirmation",
                             "verified local OCR routes with 0 AI calls; fidelity-gate failures do not auto-accept"],
        "what_they_do_not_prove": "how well a real Vision model reads these images (LIVE_VISION_NOT_MEASURED)",
        "tests": cases}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(dict(Counter(c["outcome"] for c in cases)), "exit", done.returncode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
