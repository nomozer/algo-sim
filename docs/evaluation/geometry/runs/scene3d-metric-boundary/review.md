# Independent boundary review

Reviewer: `/root/metric_review`, separate agent requested by owner; read-only inspection of final product diff vs
`5f77bfce`, code/tests/callers and `git diff --check`. No test execution by reviewer; automated receipts are separate.

Verdict: **PASS for F2 and M2 #7**, no must-fix findings.

- The semantic module validates declared scene/metric and actual chart conversion before config/init/history.
- Invalid metric cannot use malformed scene / 2D fallback to reach accepted active or new history.
- Numeric/nonfinite/scientific-notation overflow is rejected before rendering.
- Store imports no geometry/domain module or metric knowledge; delegates/catches the opaque module result.
- Every rejected load clears active/history ID/playing and returns home, making the error visible; rejected history
  cannot restore cursor/mode into the previously active simulation. Stored records are retained.
- Absent/null scene keeps legacy config validation; no history migration or deletion.

F4 containment: the contract puts `route_d` beside the envelope; `SimulationWorkspace` only reads the nested field.
The browser has no preview caller; the server rejects Origin and `/api/analyze` uses `preview=False` policy.
This establishes inactivity on the current contract-conformant product path, not safety of arbitrary injected nested
`route_d`. Before GO HYBRID, explicit transport, relation/step binding and proof semantics need offline integration.

Limitations: `hopLeScene3D` remains an existing shallow scene-shape guard, not a full hostile-payload schema validator.
Chart validation does not prove semantic geometry correctness. Clean T3/freeze/orbit/fixture gates required separately.
No Product E2E PASS or human visual acceptance is implied.

Final test-only follow-up (`216bbf84`): reviewer inspected the lifecycle test's switch from spying `validateConfig`
to the authoritative `validateEnvelope` hook; active-restoration and real no-network checks remain. Verdict unchanged:
PASS F2/M2 #7, no must-fix. No product change after `cb1f4954`.
