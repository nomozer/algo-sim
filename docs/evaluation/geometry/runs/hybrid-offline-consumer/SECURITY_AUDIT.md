# Preserved-log audit

**REMOTE_PUSH_SECURITY_BLOCKED**. No remote operation performed; Git history and all inherited evidence blobs remain intact.

Audited the 22 `.log` blobs introduced by preservation commit `77f7aaf7`, as reachable from verified main `3f6d737529af6fc79494fc3baeb340a7ca663b10`. `results/preflight.json` records path, exact byte size, SHA-256 and finding line numbers for every blob. Scan covers credential/private-key patterns, sensitive assignment patterns, raw model field markers and raw Python traceback markers. No credential/raw-model-field pattern hit was found; this is a bounded content audit, not a guarantee against every possible encoding of a secret. Logs are offline test/T3 diagnostics, not new provider outputs.

One policy violation was confirmed manually and by an independent reviewer: `backend-hybrid-contract-unification/verification/geometry-dir-first-run-before-fixes.log`, line 561, contains a Python raw traceback from a subprocess decoding/thread warning, including local filesystem paths. AGENTS.md §4 forbids raw traceback in the Git tree. The earlier statement “no secret found” does not imply compliance with this broader repository rule.

Reviewer independently rehashed all 22 blobs: byte sizes/hashes match P0 and preservation commit exactly. Four working-tree copies use CRLF conversion, so authoritative values here are Git blob hashes; line-ending conversion is not an evidence-blob change.

This finding blocks remote publication, not the authorized offline development campaign. No in-place evidence sanitization, history rewrite, force push or secret rotation was attempted. Owner must decide a compliant preservation/redaction/publication strategy separately. A correction layer points here from the new run; original GO-main evidence is unchanged.
