# Closed Input Contract Implementation Plan

Goal: close N1–N7 across all mapped TypedFactNext routes within the three authorized product modules.
Spec: architecture-decision.md, allowed-fields.json, operand-grammar.md, ownership-preflight.md, preregistration.md; Owner GO prevails.
Execution: native implementation in the existing worktree; independent adversarial reviews at the required gates.

- [ ] Lock policy snapshot and fresh tests; run RED before product edits. Reuse the 203-probe baseline.
- [ ] Extend canonical schema registries/validators, preserving explicit presence and conversion provenance.
- [ ] Run ownership before capabilities, including qualified and section-derived points; keep valid legacy canonical bindings.
- [ ] Use canonical measurement scope and operand view; validate curved relations and restore derived highlight.
- [ ] GREEN, mandated mutants/metamorphic checks, introspection+AST+dynamic coverage and Gates A–D. Gate A fail stops.
- [ ] Independent read-only pre-freeze reviewer with fresh probes. BLOCKER/MAJOR stops without further product edits.
- [ ] Only after review PASS: replay with transitions/source identity, real T0/T1/T2 receipts, product/test commit, divergence, separate freeze commit.
- [ ] Fresh clean detached candidate: verify exact hash/freeze checks and Full T3; independent final review, handoff and clean research tree.

Review focus: absent/null/empty vs implicit defaults; nested target scope on non-identity fallback; qualified constructed ownership;
derived membership vs merely sharing a parent; curved relation existence/grounding before capability refusals.
No locked expectations may change. No merge/push/cleanup/live/model/default/cache/kernel/radical/UI change.
