# Independent review round 4

Reviewer: separate read-only agent. Scope: product `36dfccef..24e1a9dbe24a5abf965ae268ce89097b67060a53`, harness/validator changes after round 3, arms `before`, `survey-A/B/C`, `final-v2`, `final-v3`, survey-validity register. No vitest/build rerun by reviewer (read-only).

Verdict: no Critical, no Important. I1 and I2 fixed. Five Minor.

Verified: backend tags every polygon3 BASE_REGION or AUXILIARY_SURFACE (`backend/app/simulation/semantic_program/scene3d.py` 280–294), so 24e1a9db changes only metadata-free polygon3; selection/causal `nen()`/`net()` overrides and hit proxies unaffected. Before arm: built CSS `--geo3d-vai-tro-dich: #2563eb`, JS `dich:2450411`, source hashes equal `git show f9559671:<file>`, substitutions once each; valid before for JS/WebGL and CSS (normal and Mode A; no orbit data). survey-B and final-v3 probe sha `91d9a368…` equal; A/C differ and match their overrides. `is_section` covers the legacy `td`; secondary shells observed in family04/07/08/10. 1540 checks, 0 failures.

Minor findings and dispositions:
- M-a: legacy section polygon got section color/opacity but not section depth/X-ray semantics (`toXuyenKhoi` required explicit AUXILIARY_SURFACE; final-v3 `polygon_fill:td` renderOrder 0, depth-tested in X-ray). Pre-existing. **Fixed** in `34a57d3540f82a78701b0f0caa8dbae746f266d1` (polygon branch uses the same section role); RED `[legacy, 0, true, true]` → GREEN `[legacy, 7, true, false]`. Arms re-measured at this commit (`*-r2`).
- M-b: metadata-free faces carrying a `parent` solid in old envelopes (e.g. `scene3d-circumsphere-fixture.json`, history restored from localStorage) now render as section amber; the backend would tag them BASE_REGION. Before 24e1a9db they were lilac; before the campaign amber — wrong both ways. Correct classification needs the backend's edge-topology rule in the frontend. **Not fixed; disclosed as a known limit / backlog.** Commit message "matches the backend" holds only for parentless polygon3.
- M-c: pool-growth discriminator proves no re-allocation of an already-seen style, not bounded key growth (keys include fade and dash size). Wording corrected in validate.py; report must say so.
- M-d: `expected_roles` / `is_section` are re-statements of product rules; they prove tokens reach the right object, not that the rules are correct. Wording corrected.
- M-e: compared arms used different harness versions (before 7d5e59f4, surveys/final-v2 e4322774, final-v3 c34ec0c6). Differences: CRLF normalization (baseline path only) and poolSize instrumentation. All versions archived with verified hashes; validate.py now requires one harness across survey/final arms and archived bytes for every arm.
- Register: final-v2 still marked authoritative and final-v3 missing — updated.

Orbit amendment: sound for its claim; never exercised on a non-zero case (final-v3 all zero; final-v2 had no pool data). The `[3,0]` family07 event in final-v2 is unexplained; "first-seen hidden-span style" is a hypothesis, not a finding.

Declined: aesthetics, human approval, vitest/build execution, T3. No merge authorization.
