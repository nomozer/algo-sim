# Historical Wave 2 documentation correction layer

This new-wave layer corrects three historical explanations without changing any byte of the Wave 2 package at `ecdc26b012c8ce80d53524a98dc75cdcb020079d`. Machine verification and complete historical-byte hashes are in [results/historical-integrity.json](results/historical-integrity.json).

The adjudicated baseline remains **5/48 SERVED_CORRECT, 43/48 FALSE_REFUSAL, 48/48 negatives refused, 33/48 correct refusal category, 0/96 genuine WRONG_SERVED, 5/5 served exact-oracle agreement**. Raw scored-run-1 and harness-corrected scored-run-2 remain separate historical records. These corrections do not change either record or any expected outcome.

1. **Track B counts (HIST-DOC-1).** Historical `report.md` section 5.2 and `handoff.md` section 6 state 75 representable_without_loss, 9 representable_with_explicit_gap, and 12 intentionally_outside_v2. Both actual immutable `track-b.json` files instead record **61 representable_without_loss (48 positive + 13 negative), 10 contradictory, 6 ambiguous, 6 not_representable_by_current_contract, 5 unsupported_topology, and 8 missing_required_information**. Use the machine values. Historical CRLF `track-b.json` SHA-256 in both scored runs: `53fee45e31b19ee5a25993412d7674e7c05ad2f9a01ee9df315d64f2a31748b8`.

2. **Pre-correction scorer identity (HIST-DOC-2).** Historical `handoff.md` section 13 gives incorrect byte counts and SHA suffixes for the two pre-correction files. The authoritative pre-execution manifest, Git blobs at `7e5c3ddde78710f4ea174956302d11e711b51635`, and adjudication receipt agree on:
   - `tools/evaluate_holdout_wave2.py`: **30,730 bytes**, SHA-256 `1a053c4ef4caaa22f2618d6d89e34adf9d024cd35f2d77c4c01759af3c96aa44`.
   - `tools/test_evaluate_holdout_wave2.py`: **19,475 bytes**, SHA-256 `33da058c0ac23cfde529cb3a9641a55009f12fa55cd38d162349f8cc745f62a1`.
   The intentional post-correction versions match the adjudication receipt exactly: scorer `e9c36a177c2f43cb8af59f361a78421b6f253a5c642e980ad98939793ae51e12`; test `07330fca6bed5e58cd07d0eb9dfa3e526d322083d7e97b75907eb4c3435e5cd2`.

3. **W2-M4 factorization (HIST-DOC-3).** Historical `report.md` section 7 and `results/diagnostics.json` state `122970403125000 = 2^3 * 3^2 * 5^7 * 148^2`. The expression on the right is **123210000000**. The observed radicand **122970403125000** still exceeds the unchanged ceiling `10^12`; the rejection and its exclusion from this Source Gate repair remain valid. This layer corrects the arithmetic explanation only.

The original manifest contains mixed LF/CRLF byte identities. All 17 unchanged manifest entries match the original historical worktree bytes directly; all 34 historical files match their committed content after line-ending normalization. Git LF blob hashes must not be compared to historical CRLF hashes without recording that distinction. The two scorer deltas are explicitly adjudicated, not silent changes.

The independent oracle `--check` re-execution passed self-tests and all 48 expected entries without writing files. Baseline freeze verification independently returned MATCH (118 files, `84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f`). No product modification or live provider call was made by this audit. Repaired-product reruns use `POST_FEEDBACK_DEVELOPMENT_REGRESSION`; the historical in-memory 48/48 diagnostic is not a repaired-product PASS receipt.
