# W3-F2 conditional publication closure

2026-10-30. This continuation records the Owner's autonomous integration decision. Historical research evidence is
unchanged. State at preparation: `TECHNICAL_READY`; source-tip publication conditions verified. Final committed-tip
publication and remote status require the checks below.

## Policy supersession

Owner's direct request replaces the old mandatory head PASS condition only for this W3-F2 integration. The full
conditions and old/new table are committed in
`docs/evaluation/geometry/runs/publication-safety-remediation/REMOTE_PUBLICATION_SECURITY_DECISION.md` §4.
Range must PASS; head must run and remain honestly BLOCKED if the unchanged historical baseline findings remain.
No new global policy, scanner change or registry approval is made.

## Identities and verification

- Remote main before: `996f114b3480efe1b0d075dd4342530aaa12ddae`, confirmed with live ls-remote and fetch.
- Local integration before policy: `15a8e1ac327e7ec5197ebe5d08330afb444b9571`; existing fast-forward preserved.
- Frozen candidate: `4e7fe91d8990d4ef2856204d2b8aaa652f41ea24`.
- Product: `dd17fbfb8616c9b7ac325aa91c4dfec92577c64a`.
- Measured-system hash: `c4fb8613800585ddd68a13f410e5c84755e64a8562c1604ed4b43b6e03c2fb8c` (118 files).
- Clean detached verification at `15a8e1ac`: freeze verifier MATCH; no backend/frontend changes since candidate.
- Existing Full T3 receipt: 15,780 backend passed; 1,417 frontend passed; build PASS; demos 5/5; crash surface 6/6.
  Its 23,655-byte raw log hashes to `a7322abcf44a5171159a4637470c2b23f80d809ffb6618ca91c026310e828c3b`, matching
  the receipt. T3 is reused by identity, not described as newly executed in this documentation-only continuation.
- Existing post-integration receipt: 3,378 passed and 41/41 fixtures; independent final review READY. Fresh affected
  suites: 54 passed in 21.16s in the clean detached verification tree, before the policy/docs edits were copied in.
  After copying policy/docs, two handoff line-limit checks initially failed (303/300); the status replaced the old
  line rather than adding lines. Fresh docs recheck: 42 passed in 4.38s, handoff exactly 300 lines.
- `LLM_ONLY`, cache130, no provider requests. Remaining product limitations stay as recorded in final-handoff.md.

## Publication and security

Exact metadata comparison is in `publication-comparison.json`; static key-vector provenance is in
`key-vector-verification.json`. All five GOOGLE_API_KEY findings are synthetic test vectors, unchanged from remote
baseline: one explicit local fault-injection sentinel, three KEY_GIA constants with explicit testing markers used
by mock-transport/network-guard tests, and one deterministic sequence interleaving alphabetic characters and
cycling digits, passed to a local secret-scanner assertion in a simulated test. Their raw values are not copied
here. The first audit helper incorrectly expected only one Google-key finding; the actual scanner output was
preserved, all five were checked, and the helper's assumption was corrected without changing the scanner.

HEAD at `15a8e1ac`: 26,346 blobs, 105 findings, 104 pending, BLOCKED due to historical baseline debt. Baseline
`996f114b`: 25,772 blobs, exactly the same finding tuples (rule/path/blob/line/exception); 0 new, 0 removed.
Range `origin/main..15a8e1ac`: 681 blobs, 59 messages, 0 violations, PASS. Rule totals: 95 PY_TRACEBACK,
5 GOOGLE_API_KEY, 2 HARDCODED_PASSWORD, 2 BEARER_TOKEN, 1 SECRET_ASSIGNMENT. Thus “104 pending” does not mean
104 traceback findings or 104 registry entries: the registry has 27 pending entries and 2 existing Owner-approved
W3-F2 entries. All pending decisions remain unchanged. No untreated real secret was identified in the new range;
the scanner and registry are unchanged. Regex coverage is a lower bound; no live credential validation is performed.

## Remote and cleanup

At preparation, no push or cleanup has yet occurred in this continuation. Final committed-tip scans, remote
read-back, exact remote SHA and cleanup disposition will be recorded after the authorized operation. Keep backups,
historical receipts and referenced baseline evidence. Uncertain worktrees are retained.

## Process

Reused: publication scanner, freeze verifier, existing T3/review/post-integration receipts and affected test suites.
Created product modules: none. Duplicate implementation and dependency-cycle risk: none; no product code changed.
Future workflow proposal is `workflow-proposal.md`, not an applied global security change.

## Closure after first verified push

`REMOTE_VERIFIED`: non-force `git push origin main:main` advanced remote from `996f114b` to
`4d304992397793d0aa8062809d0249d046b6a058`. Independent live ls-remote, local main and origin/main all matched.
The exact committed tip was scanned: range 697 blobs / 60 messages / 0 violations PASS; head 26,356 blobs /
105 findings / 104 pending BLOCKED, exact baseline metadata match. Post-push freeze verifier MATCH.
Machine receipt and worktree dispositions: `closure.json`.

Cleanup inventoried eight existing W3-F2 worktrees plus this session's detached verifier. Six node_modules junctions
all target the main checkout and were left untouched. The pre-CIC worktree contained only 58 Python cache files
and one generated database; its database was backed up and hash-verified before successful official Git removal,
without force. The session's verifier had its own copied documentation and generated database backed up and
hash-verified, its own tracked changes restored and copied untracked files removed only after preservation.
Git worktree remove then unregistered it but reported Invalid argument while deleting the directory; the residual
directory was retained. The seven other original worktrees were retained for evidence, baseline or uncertain
ignored content (including unreadable cache directories). No branch, backup or historical receipt was deleted.
Backups and preservation manifest are under `.superpowers/backups/w3-f2-publication-closure/`.

This final documentation commit is part of the same Owner-authorized integration closure, with no product change.
Before publishing it, repeat range/head and exact-baseline comparison; remote must still equal this task's own
verified first-push SHA above. Any unrelated update stops publication. The original comparison baseline stays
`996f114b`. Final documentation-tip SHA is read back after its non-force push and recorded locally in
`.superpowers/backups/w3-f2-publication-closure/final-remote-verification.json` to avoid a self-referencing commit.

Final integration verdict: W3-F2 integrated and remote verified; historical publication debt remains open;
cleanup complete for proven-safe removals, with the disclosed retained worktrees/residual. No global security
reduction or Hybrid enablement. The workflow proposal remains a proposal.
