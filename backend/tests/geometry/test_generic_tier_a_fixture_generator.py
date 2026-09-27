from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "backend" / "scripts" / "generate_generic_tier_a_fixtures.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_cross_section_fixture_preserves_verifiable_measurement_provenance(tmp_path: Path):
    subprocess.run(
        [sys.executable, str(GENERATOR), "--out", str(tmp_path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    fixture = json.loads(
        (tmp_path / "fixtures" / "cross_section_positive.json").read_text(encoding="utf-8")
    )

    source_path = ROOT / fixture["source_artifact_path"]
    canonical_path = ROOT / fixture["canonical_fixture_path"]
    assert source_path.is_file()
    assert fixture["source_sha256"] == _sha256(source_path)
    assert canonical_path.is_file()
    assert fixture["canonical_fixture_sha256"] == _sha256(canonical_path)
    assert fixture["application_llm_calls"] == 0
