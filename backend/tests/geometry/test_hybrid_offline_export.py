"""The evaluator must consume the real text-first product boundary, preserve locks and refuse overwrite."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))


def test_offline_export_is_available_and_writes_real_linked_wrappers(tmp_path):
    import export_hybrid_offline as export
    summary = export.export_offline(tmp_path / 'new')
    assert summary['cases'] == 47
    assert summary['wrong_served'] == []
    assert summary['oracle_mismatches'] == []
    assert summary['served'] > 0 and summary['refused'] > 0
    assert (tmp_path / 'new' / 'fixtures.json').is_file()
    with pytest.raises(FileExistsError):
        export.export_offline(tmp_path / 'new')
