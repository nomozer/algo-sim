# Architecture decision and preregistered acceptance

This is a product repair, not an independent holdout. The source text and TypedFactNext must agree;
grammar parsing creates no facts, coordinates or answers. Registry validates source bindings before
the existing Planner and Engine consume them. Unknown, ambiguous, negative, conditional, contradictory
or incompletely read premises remain refused.

W2-M1: extend the same ratio syntax reader to “Trên cạnh XY lấy điểm P sao cho …”.
Use its existing exact linear equation solver for XP/XY=t, also [Y,X],1-t; require all three labels distinct,
the actual point, segment and both equation operands from the same clause. No keyword-only admission.
Align construction/number ownership with this reader; unchanged solid-scoping/contradiction checks apply.

W2-M2: accept the noun “đỉnh” in a projection target only when that label identifies a vertex of
the relevant source solid; neither an arbitrary midpoint nor another solid's point can become a vertex.
Retain explicit midpoint/centroid obligations and primed-label boundaries.

W2-M3: whole standalone ratio premise is read by W2-M1's reader, with no unread suffix;
generic “lăng trụ” expresses prism class, not rightness. Existing solid notation/kind checks and I-1
remain mandatory. Unknown extra premise must still fail SOURCE_PREMISE_UNREAD.

Affected Registry functions: _TY_SO/_ty_so_khop; construction_source_bound;
_CUM_DINH_NGHIA_DIEM; _kiem_nguon_dong (plus existing helpers only if needed by those responsibilities).
Intended version Registry18->19; Planner17/Engine14/Adapter4/certificate1 unchanged.
Cache policy: research route runtime identity contains registry version; no default-route consumer/output changes.
Keep CACHE_VERSION130 if existing cache identity and fixture checks confirm isolation. Revisit on contrary evidence.

Development corpus authored here from mathematical configurations, without copying Wave2 cases or using its oracle.
24+ positives and 24+ negatives, with old syntax controls, renaming and fact order permutations.
All positive geometry: exact rational rectangular/right-triangle bases, horizontal sections at an internal
lateral-edge parameter. Independent oracle: homothety area for pyramids and translation-invariant base area
for prisms; exact boundary edge fractions. Values and outcome groups frozen before product execution.
Expected refusal groups: source mismatch/incomplete reading/grounding for false source claims;
contradictory or insufficient geometry may use existing exact geometry refusal codes.
No internal/validation exception counts as an accepted negative.
For a positive only actual route SERVED + Adapter4 SERVED + envelope ok with oracle agreement counts.
T0/T1/T2 and Full T3 required. No readiness label until receipts and independent review are complete.
