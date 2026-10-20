# Independent review — source gate hardening

- **Final verdict:** `INDEPENDENT_REVIEW_PASS` on candidate `c5a83b74` (product `602316ed`, 112 files
  `0512dbc53e09696dfecee4cec8ed360af4ad66d8816c782c2993c3617a0d2583`; initial SG-1..SG-6 candidate `1beeec0b` / `b6b61061`,
  `663342b0df90c805291fcc057846b31fe5e62b0035eeac13dea785f984502ab9`, also passed before Full T3 follow-up)
- **Reviewer:** separate read-only agent (no repo edits; probes and a `git archive` copy of `6973c4b6` only in the session
  scratchpad), offline, 0 model calls; same reviewer across rounds, each round on the frozen candidate of that round
- **Scope:** SG-1..SG-6 value binding and source reading in `geometry_functions/registry.py` / `planner.py`

| Round | Candidate (product) | Verdict | Reproduced false serves | Fix |
|---|---|---|---|---|
| 1 | `c228bf4e` (`ee50e87b`) | FAIL | role noun bound without its owner: another triangle's height, another square's side, "cạnh SA" as the base side, "cạnh bên SB" as SA, "cạnh bên" on a non-regular pyramid | owner-aware binding (`aded2fbf`) |
| 2 | `d0cb122b` (`aded2fbf`) | FAIL | owner inferred from free prose: "SAB là tam giác cân có chiều cao …", "khối hộp có chiều cao …", "của mặt bên …" | closed clause grammar replaces owner inference (`0cefe720`) |
| 3 | `bef2c13f` (`0cefe720`) | FAIL | "chiều cao của <another solid>"; a later clause re-attributing an earlier role | "của <solid>" checked; opaque clauses unbind (`6c910a51`) |
| 4 | `707b0538` (`6c910a51`) | FAIL | the point-definition exemption and the labelled-binding survival were word lists ("H là chân của nó …", "…, nhưng đó là cạnh của tam giác khác"); "tứ diện" for a 4-gon | any out-of-grammar clause unbinds its sentence; closed point / face clauses (`85e6dd86`) |
| 5 | `cbb23016` (`85e6dd86`) | FAIL | a role after a closed face/triangle clause ("… là tam giác cân và có chiều cao …"); an unencoded shape premise hiding a contradiction | face / triangle / altitude / projection clauses unbind the sentence's unlabelled roles (`b3c850e2`) |
| 6 | `2f12ea11` (`b3c850e2`) | **PASS** | none non-debatable; N1/N2 ("G là trọng tâm … và có đường cao …") debatable | hardened anyway (`b6b61061`) |
| delta | `1beeec0b` (`b6b61061`) | **PASS** | none; the delta can only unbind | — |

Every reproduced probe of every round is a negative test in `backend/tests/geometry/test_source_gate_hardening.py`
(118 tests; 56 RED on `6973c4b6`). Suites the reviewer ran in the final rounds: source gate, Wave 1 certificates, Wave 2A
composition, Wave 2B capabilities, route A, text→functions, premise coverage, Adapter `/2` fixtures — 0 failed.

## Full T3 follow-up (Antigravity session, same reviewer type: separate read-only agent, 0 model calls)

Full T3 on `72d1595f` (candidate `1beeec0b`) failed 5 backend tests (`t3-fail-72d1595f.log`): a one-sentence problem
ending with its request, and "Tam giác ABC đều cạnh 2.", were unread. The fix (`81e91ebb`) was reviewed as a delta; the
review then reproduced a pre-existing class — a shape noun naming another vertex count than its polygon / the solid's
base ("Hình vuông ABC cạnh 2", "Đáy là hình tứ giác đều" on S.ABC) served — closed over eleven rounds:

| Round | Candidate (product) | Verdict | Reproduced false serves (new / pre-existing) | Fix |
|---|---|---|---|---|
| T3-1 | `a6671e9f` (`81e91ebb`) | FAIL | shape noun vs label count (`_C_DAGIAC`, `_C_DAY`) | `b6a9fcc6` |
| T3-2 | `948f6980` (`b6a9fcc6`) | FAIL | legacy unlabelled base, cube cue, later mention (pre-existing) | `08bad12f` |
| T3-3 | `5ba30b85` (`08bad12f`) | FAIL | unlabelled "đáy là …" in a quoted sentence (pre-existing) | `6f58c0f5` |
| T3-4 | `67cae953` (`6f58c0f5`) | FAIL | values grounded outside role binding (pre-existing) | `57701200` (source-level gate) |
| T3-5 | `6c833d75` (`57701200`) | FAIL | wordings outside the phrase list (pre-existing) | `c6592ac2` |
| T3-6 | `79713e1b` (`c6592ac2`) | FAIL | **regression**: labelled base bypass; valid "tam giác ABD." refused | `c3b1f905` (fail-closed attribution) |
| T3-7 | `72753afc` (`c3b1f905`) | FAIL | "… làm đáy", "mặt dưới …"; over-refusal of common wordings | `c7b79cce` |
| T3-8 | `7b83cb17` (`c7b79cce`) | FAIL | **regression**: unresolved owners passed silently | `26e1040a` (declared-solid ownership) |
| T3-9 | `f9e012d0` (`26e1040a`) | FAIL | "mặt bên dưới" read as lateral (pre-existing); "Mặt (SBC) là" refused | `07da444c` |
| T3-10 | `4629760e` (`07da444c`) | **PASS** | none in the vertex-count class (Full T3 on `15782e84` hit 1 `ΔSHD` test) | `602316ed` (`Δ/∆/△` prefix) |
| T3-11 | `c5a83b74` (`602316ed`) | **PASS (delta)** | none; `Δ/∆/△` requires 3-vertex label and 3-vertex noun | — |

Every reproduced probe is a test in `test_source_gate_hardening.py` (226 tests total; `test_t3_*`, `test_review_t3*` RED on
the predecessor product). Debatable, left open: "mặt bên ở/nằm dưới là …" whose count matches the lateral-face reading.

**Still open (reported, not a regression of this run):** a premise inside a sentence a fact quotes WHOLE is counted as
read even when no call encodes it (K1/K2/K5: "mặt bên SAB là tam giác đều" next to SA ⊥ (ABC), SA = 2); `6973c4b6`
serves the same premise when the quote holds one number (K1′/K2′/K5′) — premise-coverage limit, recorded in
`docs/OPEN_ISSUES.md`.
