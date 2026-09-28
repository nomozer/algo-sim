# Final handoff

```text
PRODUCT_COMMIT_SHA = 50a31e0b7124cb038ff5c56dd9c856778a263725
ORACLE_HARNESS_COMMIT_SHA = 1dab0f7db516e8ce8eee1280ded4d220a10018d5
EXPECTATION_REGISTRATION_COMMIT_SHA = 80766b909d09fc71d6ff05f79b29bd1091ea7d40
CANDIDATE_COMMIT_SHA = e115c31df24efc35fe1d5590e3cab6737b5b13d8
MEASUREMENT_COMMIT_SHA = e115c31df24efc35fe1d5590e3cab6737b5b13d8
EVIDENCE_COMMIT_SHA = 09934eb7d0850d3f1f6d5c4f4c79f93b33bb92d9
FINAL_DOCS_COMMIT_SHA = SELF_EXCLUDED_RESOLVE_FROM_GIT

CURRENT_BRANCH = fix/cuboid-visual-semantic-closure
DEFAULT_MODE = LLM_ONLY
CACHE_VERSION = 102
LIVE_GEMINI_REQUESTS = 0
PUSH_EXECUTED = NO
MERGE_EXECUTED = NO
COMMITS_SQUASHED = NO
HISTORY_REWRITTEN = NO
USER_FAVICON_DELETION_PRESERVED = YES

TEMP_WORKTREES_FOUND = 5
TEMP_WORKTREES_REMOVED = 5
TEMP_WORKTREES_RETAINED = 0
REQUIRED_EVIDENCE_NOT_CANONICALIZED = 0
UNKNOWN_ARTIFACT_COUNT = 0
UNIQUE_COMMITS_AT_RISK = 0

FINAL_DECISION = VERIFICATION_NOT_CLEAN
```

The final docs commit cannot embed its own SHA without changing that SHA. Resolve
`FINAL_DOCS_COMMIT_SHA` from the commit containing this file; the user-facing
handoff reports that full value after commit creation.

Blocking verification evidence is in `results/VERIFICATION_SUMMARY.json`:
unstable raw camera snapshot hashes after damping, five mobile immutable-frame
assertion failures, one legacy frontend regex failure, and 35 backend full-suite
failures. Exact product/oracle IDs and spans, the perspective reference, formation
semantics, section identity, and worktree recovery all passed.
