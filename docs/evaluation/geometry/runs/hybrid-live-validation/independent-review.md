# Independent adversarial review — run `hybrid-live-validation`

Fresh-context, adversarial, read-only `research` subagent (`e3e72273-72ca-412d-abb6-62e3e740817c`). It modified no repo file;
its scratch scripts stayed outside the repository.

## Round 1 — product `55db50c3`: `READY` (0 BLOCKER, 0 MAJOR, 2 MINOR, 2 NIT)

Checked: the coverage certificate against a runtime no-op over all 144 Wave 3 cases (fires on A01–A18, all still served, and
on N54/N55 only; never on Category B); adversarial coverage inputs (through-point on a base edge, partial naming, plane = face,
vertex = solid vertex); altitude-foot binding under 13 point/image/plane/wording mutations (all refused except the exact
wording); `radical.py` termination (`d ≤ 10⁴`) and the square-free certificate on 20 000 random `k²·sf` inputs (0 wrong);
the two-line slice polygon word; clause-reader consistency.

| id | finding | resolution |
|---|---|---|
| MINOR-1 | `_C_CHIEU` accepted wider altitude-foot wordings than the binder `_chan_duong_cao_dung_nguon` (not fail-open: the binder refused them) | `57457fc4`: the sentence alternative is now exactly the binder's grammar; `test_both_readers_share_one_altitude_foot_grammar` |
| MINOR-2 | legitimate partial naming refused while the unnamed problem is served; docstring called it a contradiction | `57457fc4`: docstring says "unsupported partial naming"; limitation stated in the report §11 and logged `ISSUE-ARCH-PARTIAL-STATED-CUT-NAMING` |
| NIT-3 | radical docstring did not state the new input bound or the large-prime-square policy | `57457fc4` |
| NIT-4 | closed right-angle form lacked optional "đỉnh" | `57457fc4` |

## Round 2 — product `57457fc4`, refreeze `79bbc053`, report draft: product and refreeze `READY`; report `NOT_READY`

| id | finding | resolution |
|---|---|---|
| R-0 (NIT) | frozen copy rewritten in place | README states the superseded `d5c4098b` / `f4ed426a…` freeze; git keeps it |
| R-1 (MAJOR) | report cited a Full T3 receipt that did not exist | Full T3 attempt 2 run at `79bbc053`; `full-t3-79bbc053.json` records both attempts |
| R-2 (MAJOR) | §12 timings from the `d5c4098b` receipt; 208 vs 202 not explained | §12 quotes the `79bbc053` receipt, timings labelled machine-dependent; 208/202 stated |
| R-3 (MINOR) | 101 → 96 classified modules; shared lines 49 012 | fixed |
| R-4 (MINOR) | stale altitude grammar text, quote wording, test count 21, README C11 | fixed |
| R-5 (MINOR) | `SECTION_BOUNDARY_INCOMPLETE` shows the contradiction message for partial naming; §10 label | stated as a known limitation + open issue; §10 now `KERNEL_FAILURE` |
| R-6 (MINOR) | measurement probe receipt carries no identity | footnoted (run at `79bbc053`; the tool records no head) |
| R-7 (NIT) | `wave3-gold-replay.json` baseline path uses backslashes | recorded; the reused W4 tool writes it, left unchanged |

All other report claims were checked against the receipts and found supported (Wave 3 72/72 + 72/72, 65 exact reason, 8
transitions, locked 96/96, probes 0 served negatives, live preflight table, 0 live requests everywhere).

## Round 3 — receipt commit `e5c54324`: product `57457fc4` & freeze `79bbc053` `READY`; receipt commit `NOT_READY` (0 BLOCKER, 1 MAJOR, 0 MINOR, 1 NIT)

Fresh-context read-only `research` subagent (`61c7f72f-ad28-4be8-b109-8309036b3e5b`, launched after `e3e72273` hit provider 429 quota). Verified all scope guards (`frontend/**` untouched, defaults unchanged, 0 live Gemini calls, pilot templates `PENDING_OWNER_DECISION`), all Round 1 (`MINOR-1..NIT-4`) and Round 2 (`R-0..R-7`) closures, all product changes (`21/21` repair tests, `41/41` preview fixtures), and `271/271` governance/seal/candidate/telemetry/thesis tests. Caught two documentation issues:

| id | finding | resolution |
|---|---|---|
| R3-1 (MAJOR) | `full-t3-79bbc053.json` `attempt_1.product_commit` and `attempt_1.measured_system.tree_hash` had 8-char prefixes matching `55db50c3` / `f4ed426a` but unverified hex tails | replaced with exact Git / `d5c4098b:EVALUATION_CANDIDATE.json` hashes (`55db50c3654f114fb0691147bdd8a5c15bdd86dc`, `f4ed426a1c2f0a3b8cf24fea98d447094fa577bc91eae2405e36c5c83e50bf59`, `d5c4098b36bedb0ddad7a4fd44759554d0e36c81`) |
| R3-2 (NIT) | report §2 line 37 called `57457fc4…` the "candidate freeze commit … recorded in `79bbc053`" | clarified as product commit (`product_commit_sha` / `commit` at freeze time), frozen in candidate commit `79bbc0531df89d3757ae16a6d8c5c0388fdac84b` |

## Round 4

See below (appended after Round 4 verification).
