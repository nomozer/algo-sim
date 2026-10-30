# Proposed workflow after W3-F2

Proposal only, 2026-10-30. No new global publication permission or security reduction is applied here.

For an Owner-authorized task, automate RED/GREEN, Gates A–D, replay and T0–T3 according to the affected scope;
commit/checkpoint with explicit path allowlists; obtain independent review against a pinned commit. Reuse valid
full-gate evidence only when candidate, product and relevant harness identity still match; never treat unrun gates
as passing. Keep provider work separately budgeted and opt-in.

| State | Required evidence |
|---|---|
| TECHNICAL_READY | Required technical gates pass, identity matches, independent review has no unresolved unauthorized major findings |
| PUBLICATION_READY | Applicable publication policy is satisfied, scanners run on the exact tip, baseline/regression comparison retained, real secrets resolved |
| REMOTE_VERIFIED | Authorized non-force push completed; actual remote SHA read back equals local main |

Within the task's existing authorization, commit and checkpoint without asking again. Automate merge/push only
when that task explicitly grants integration authority, required gates pass, the working tree is clean and remote
ancestry is unchanged. A concurrent remote update stops the operation. Never force-push or rewrite history.

Separate historical baseline debt from new findings by exact metadata identity (rule, path, blob, line, exception),
retaining the scanner's actual verdict. Unrelated historical debt should use an explicit applicable Owner policy,
not repeated per-entry approval requests or invented exceptions. W3-F2's scoped supersession does not supply
that policy to future tasks; a global change needs a separate Owner decision.

After remote verification, inventory tracked/untracked/ignored files and junctions. Preserve unique evidence and
backups; remove only proven safe worktrees with Git, without force. Retain uncertain worktrees with a reason.
