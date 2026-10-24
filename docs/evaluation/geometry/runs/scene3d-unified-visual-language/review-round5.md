# Independent review round 5

Reviewer: separate read-only agent. Scope: product `34a57d3540f82a78701b0f0caa8dbae746f266d1` (round-4 M-a fix), arms `survey-A-r2`, `survey-B-r2`, `survey-C-r2`, `final-r2`, validate.py lineage checks, survey-validity v3.

Verdict: no Critical, no Important. Three Minor (non-blocking).

Verified: backend tags polygon3 only BASE_REGION or AUXILIARY_SURFACE (`scene3d.py` 288–294); old and new predicates agree for every backend-tagged polygon3 and differ only for metadata-free polygon3. `type==="section"` path, border order (`thuTuVien`, 8) and `ownsBoundary` unchanged; fill order 7 sits after back depth prepass 5 and before curved front prepass 7.5, per the occlusion contract. r2 arms share harness `c34ec0c6`, fixture `c6dcd1c8`, source `34a57d35`; overrides 0 (final) / 1 (surveys); B = final probe `91d9a368`. Deterministic final-v3 → final-r2 receipt diff: only `polygon_fill:td` renderOrder 0 → 7 and X-ray depthTest true → false; edges, dash, panel bounds, roles, depth/X-ray probes unchanged; orbit repeat allocations and pool growth zero. 1542/1542 checks. Vitest file 9/9 at HEAD. Product scope = `scene3d-roles.ts`, `scene3d-view.tsx`, `tokens.css`.

Minor:
1. M-b widened: metadata-free polygon3 faces with a `parent` (e.g. `scene3d-circumsphere-fixture.json`, localStorage-restored envelopes) now also take section depth order and X-ray reveal, though the backend would tag them BASE_REGION. Disclosed limit; backlog.
2. validate.py does not gate section renderOrder/depthTest (effect proved by receipts and unit test only); "every harness version archived" checks file existence — reviewer hand-verified all five archive hashes against their prefixes.
3. X-ray own pixels for `td` barely change (28392 vs 28348): the effect is visible in the material probe, not as a pixel difference, for an axial section inside a cone.

RED state: reviewer could not reproduce read-only. Observed in this session before the fix: vitest `expected [ 'legacy', +0, true, true ] to deeply equal [ 'legacy', 7, true, false ]`.

Declined: aesthetics, approval, full re-review of rounds 1–4. No merge authorization.
