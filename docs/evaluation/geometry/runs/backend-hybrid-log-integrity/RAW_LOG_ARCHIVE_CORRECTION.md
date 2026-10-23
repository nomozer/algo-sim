# Raw log transport correction

`core.autocrlf=true` normalized CRLF to LF when the continuation's successful plain text logs were committed at `4fb1045f40a326f9d23e2fdad9fcd5b2290697f2`. Runtime logs are still byte-identical to their recorded receipts; Git blobs have different bytes. This is an evidence transport defect, not a product or test-result change. The first affected commit is retained; no original log, command receipt or prior artifact is rewritten.

`passed-command-raw-streams.zip` preserves the original bytes of completed PASS stdout/stderr streams. `archive-integrity.json` records original receipt hashes and byte counts, the normalized Git blob hashes where present, archive member names and archive SHA256. Every member was verified against its command's receipt before packaging. ZIP content is binary so Git CRLF text conversion does not alter it; stage-time Git blob equality is checked separately in the final integrity receipt.

Raw failed streams remain local/untracked because the repository forbids storing raw tracebacks. Their invocation/execution metadata includes original raw stream hashes; failures are described without raw traceback in T3_FAILURE_ROOT_CAUSE and final handoff. This packaging does not change a FAIL into PASS. Full T3 was still running when this archive was made and is excluded.
