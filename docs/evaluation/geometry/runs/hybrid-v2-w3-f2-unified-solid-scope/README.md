# W3-F2 unified solid-scope validation — divergence declaration only

This directory exists because the candidate-divergence chain
(`backend/tests/geometry/test_thesis_acceptance_matrix.py::_khai_lech_hien_hanh`) only reads
`runs/*/candidate_divergence.json` and `runs/*/inputs/candidate_divergence.json`, and both slots of the W3-F2 run are
already used by earlier, immutable declarations. All evidence of this task lives in
[`../hybrid-v2-w3-f2-ratio-projection-language-grounding/unified-solid-scope/`](../hybrid-v2-w3-f2-ratio-projection-language-grounding/unified-solid-scope/).
