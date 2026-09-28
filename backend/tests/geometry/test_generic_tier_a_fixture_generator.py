from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "backend" / "scripts" / "generate_generic_tier_a_fixtures.py"


def _sha256(path: Path) -> str:
    # Blob content: recorded hashes are LF; a core.autocrlf checkout writes CRLF.
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


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

    manifest = json.loads((tmp_path / "FIXTURE_MANIFEST.json").read_text(encoding="utf-8"))
    assert len(manifest["fixtures"]) == 12
    assert {
        name.removesuffix("_positive.json").removesuffix("_negative.json")
        for name in manifest["fixtures"]
    } == {
        "triangular_pyramid", "triangular_prism", "rectangular_pyramid",
        "cuboid", "cube", "cross_section",
    }
