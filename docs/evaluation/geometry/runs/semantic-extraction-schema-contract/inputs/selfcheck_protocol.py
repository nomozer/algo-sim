"""Offline checks: assembly cannot rewrite annotations; lock rejects missing/stale reviews and repeat locks."""
import importlib.util
import json
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    spec = importlib.util.spec_from_file_location("prepare_protocol", HERE / "prepare_protocol.py")
    p = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(p)
    corpus, gold, corrections = p.assemble()
    assert len(corpus["cases"]) == 36
    assert [c["split"] for c in corpus["cases"]] == ["dev"] * 12 + ["heldout"] * 24
    original = p.read(p.OLD / "corpus.json")
    dev = [c for c in original["cases"] if c["split"] == "dev"]
    held = p.read(HERE / "heldout/corpus.json")["cases"]
    assert corpus["cases"] == dev + held
    old_gold = p.read(p.OLD / "gold_facts.json")["cases"]
    held_gold = p.read(HERE / "heldout/gold_facts.json")["cases"]
    raw = {**{c["id"]: old_gold[c["id"]] for c in dev}, **held_gold}
    # The only difference from the raw gold is the declared correction: base_edge facts gain one equivalent alternative.
    changed = {(c["case_id"], c["fact_id"]) for c in corrections["changes"]}
    for cid, case in raw.items():
        for f, g in zip(case["facts"], gold["cases"][cid]["facts"], strict=True):
            if (cid, f["id"]) not in changed:
                assert f == g
                continue
            assert f["measure"] == "base_edge" and {k: v for k, v in g.items() if k != "alternatives"} == f
            (alt,) = g["alternatives"][len(f.get("alternatives", [])):]
            assert set(alt) == {"points"} and (alt["points"] is None) != (f.get("points") is None)
    # Rule injection: a base_edge whose points name something other than the base is never "corrected".
    probe = {"x": {"facts": [{"id": "f", "kind": "length", "measure": "base_edge", "solid": "S.ABC", "points": ["A", "B"]}]}}
    assert p.correct_gold(probe)[1] == []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "target.txt"
        target.write_text("reviewed\n", encoding="utf-8")
        gate = root / "gate.json"
        gate.write_text(json.dumps({"status": "PASS", "reviewer": "independent-reviewer",
                                   "reviewed_sha256": {"target.txt": p.lf_sha(target)}}), encoding="utf-8")
        assert p.check_gate(gate, {"target.txt"}, root)["status"] == "PASS"
        target.write_text("changed\n", encoding="utf-8")
        assert p.check_gate(gate, {"target.txt"}, root)["status"] == "STALE_REVIEW"
        assert p.check_gate(root / "missing.json", set(), root)["status"] == "MISSING"
        gate.write_text(json.dumps({"status": "PASS", "reviewer": "independent-reviewer", "reviewed_sha256": {}}), encoding="utf-8")
        assert p.check_gate(gate, {"target.txt"}, root)["status"] == "INCOMPLETE_COVERAGE"
        p.require_unlocked({"lock_status": "NOT_LOCKED"})
        try:
            p.require_unlocked({"lock_status": "LOCKED"})
        except SystemExit as exc:
            assert str(exc) == "ALREADY_LOCKED"
        else:
            raise AssertionError("repeat lock allowed")
    print(json.dumps({"status": "PASS", "cases": 36, "checks": ["lossless_assembly", "stale_review", "missing_review", "review_coverage", "one_time_lock"]}))


if __name__ == "__main__":
    main()
