"""Read-only wrapper: lossless corpus/gold provenance plus the two original exact oracles.

No author modes and no product, provider, or scorer import. --author is rejected.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
OLD = HERE.parents[1] / "hybrid-semantic-extraction-v2/inputs"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def module(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    if len(sys.argv) != 1:
        raise SystemExit("READ_ONLY_ORACLE_NO_ARGUMENTS")
    corpus, gold, provenance = read(HERE / "corpus.json"), read(HERE / "gold_facts.json"), read(HERE / "provenance.json")
    for path, want in provenance["source_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest() == want, "SOURCE_MUTATION"
    dev = [c for c in read(OLD / "corpus.json")["cases"] if c["split"] == "dev"]
    held = read(HERE / "heldout/corpus.json")["cases"]
    assert corpus["cases"] == dev + held, "CORPUS_MUTATION"
    old_gold = read(OLD / "gold_facts.json")["cases"]
    expected = {**{c["id"]: old_gold[c["id"]] for c in dev}, **read(HERE / "heldout/gold_facts.json")["cases"]}
    # Replay the declared pre-lock encoding correction: each change must start from the original fact and may only append alternatives.
    for ch in read(HERE / "gold_corrections.json")["changes"]:
        facts = expected[ch["case_id"]]["facts"]
        i = next(i for i, f in enumerate(facts) if f["id"] == ch["fact_id"])
        before, after = ch["before"], ch["after"]
        assert facts[i] == before, "CORRECTION_BEFORE_MISMATCH"
        assert {k: v for k, v in after.items() if k != "alternatives"} == {k: v for k, v in before.items() if k != "alternatives"}
        assert after["alternatives"][:len(before.get("alternatives", []))] == before.get("alternatives", []), "CORRECTION_NOT_APPEND_ONLY"
        facts[i] = after
    assert gold["cases"] == expected, "GOLD_MUTATION"
    prefix = (OLD / "oracle.py").read_text(encoding="utf-8").split("# Heldout family H1:")[0].rstrip("\n") + "\n"
    assert (HERE / "exposed_dev_oracle.py").read_text(encoding="utf-8") == prefix
    expected_dev = module(HERE / "exposed_dev_oracle.py").EXPECTED
    observed_dev = {(c["id"], r["rid"]): r["oracle"] for c in dev for r in c["requests"] if r["oracle"] is not None}
    assert observed_dev == expected_dev, "DEV_ORACLE_MISMATCH"
    with contextlib.redirect_stdout(io.StringIO()):
        module(HERE / "heldout/oracle.py").main()
    families = {}
    for c in corpus["cases"]:
        assert families.setdefault(c["structure_id"], c["split"]) == c["split"]
    print(json.dumps({"status": "PASS", "dev": len(dev), "heldout": len(held), "families": len(families),
                      "requests": sum(c["n_source_requests"] for c in corpus["cases"]), "semantic_mutations": 0}))


if __name__ == "__main__":
    main()
