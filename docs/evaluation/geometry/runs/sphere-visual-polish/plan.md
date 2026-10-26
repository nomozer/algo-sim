# Final sphere visual polish

Continuation from d1ee4f0d; Owner request 2026-10-26. Same candidate branch; main stays unchanged.

1. RED: presentation tests for a continuous sphere outline thinner than ordinary solid edges at desktop/mobile; visible equator clearer than hidden equator, still subordinate to a real intersection rim.
2. GREEN: sphere-only stroke hierarchy. Keep perspective tangent placement, visibility classifier, circle geometry, labels, section fill/plane, camera, UI, other shapes, backend, Hybrid and cache unchanged.
3. Targeted presentation regressions and unchanged five-case sphere-plane product-path mathematical oracle. Capture existing four scenes, seven named angles, 24-step orbit and section selection at 1440/DPR1 and 390/DPR2. Retain before/after and original silhouette-scan thresholds.
4. Diagnose remaining flagged rays separately from the locked measurement. Do not alter old evidence or report zero errors without evidence.
5. Commit product; refreeze; one authoritative Full T3 in a fresh clean detached worktree once stable. Record receipt and scope/hash checks. No provider calls.
6. Publish 4–6 final review images and handoff. Stop at OWNER_VISUAL_APPROVAL_PENDING; no merge, cleanup, push or backend development.

Reuse: buildObject3D, dongBoNetDayManHinh, curved-rim classification, sphere-final-closure capture/oracle/scan scripts, full-gate.mjs. No new product module or dependency.
