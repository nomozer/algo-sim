# Independent review — source gate hardening

- **Final verdict:** `INDEPENDENT_REVIEW_PASS` on candidate `1beeec0b` (product `b6b61061`, 112 files
  `663342b0df90c805291fcc057846b31fe5e62b0035eeac13dea785f984502ab9`)
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

**Still open (reported, not a regression of this run):** a premise inside a sentence a fact quotes WHOLE is counted as
read even when no call encodes it (K1/K2/K5: "mặt bên SAB là tam giác đều" next to SA ⊥ (ABC), SA = 2); `6973c4b6`
serves the same premise when the quote holds one number (K1′/K2′/K5′) — premise-coverage limit, recorded in
`docs/OPEN_ISSUES.md`.
