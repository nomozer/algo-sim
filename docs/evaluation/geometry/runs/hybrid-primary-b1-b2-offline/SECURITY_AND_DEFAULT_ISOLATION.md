# Security and default isolation

Unchanged: LLM_ONLY default, flat response contract, Hybrid product NO-GO, live0, cache127, memory32, REMOTE_SECURITY_BLOCKED and 27 publication exceptions PENDING_OWNER_DECISION. No key or provider was used; no push, history rewrite, ACL modification, publication approval or main merge was performed.

The internal service requires an explicitly enabled existing research policy. `/api/analyze` and its default import closure stay unchanged. Import-boundary tests declare the two additional lazy research validator imports explicitly and retain both static closure checks and clean subprocess default-route probes; no hidden dynamic import bypass was added.

Existing operator HTTP preview authorization is preserved. It remains blocked by default, requires server token/loopback and rejects Origin. There is no new `/4` public/operator HTTP endpoint. Injected extractors are trusted local Python dependencies, not untrusted request data; this service is not a sandbox for arbitrary plugins.

Cache is excluded from the new route. Policy-disable/default tests verify no extractor invocation, and existing route-aware cache tests still protect cache127 and rollback identity. Deployment rollback and a cached/public Hybrid route are not demonstrated by this scope.

New receipts contain hashes, codes, durations and validated authored fixture output; technical exception strings and provider bodies are excluded. Raw test logs, if retained, belong in ignored local scratch. Browser evidence is offline fixture injection, not a frontend connection to a live product endpoint. The CLI exporter denies socket connection/name-resolution attempts.

Git mutations used official sandbox permission requests to create the isolated branch and save allowlisted checkpoint files. They did not alter ACLs. No unrelated worktree was removed or repurposed; frontend dependencies are a junction to existing installed packages, with no package install or dependency change.
