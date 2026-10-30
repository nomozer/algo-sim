# Read-only publication risk report — BLOCKED_PENDING_OWNER_DECISION

Both exact historical blobs were read directly with Git cat-file and checked against the proposal. No history, blob, registry or approval was changed. Credential-pattern findings: zero; this is a bounded scan plus contextual review, not a proof that arbitrary secret encodings cannot exist.

| historical path | SHA-256 | size | finding |
|---|---|---:|---|
| `docs/evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding/closed-input-contract/source-grammar-adjudication/gate-d-full-backend-pytest.log` | `1f9bb9a8c9054df6e500e8dd227d3c33b99b01ba07fc1819404dc626acc2205e` | 24497 | standard-library reader-thread decoding traceback; private local paths/profile identifier present |
| `docs/evaluation/geometry/runs/hybrid-v2-w3-f2-ratio-projection-language-grounding/closed-input-contract/source-grammar-adjudication/gate-d-pre-patch-5e44d5da-identity-12.log` | `c17f5fa89524ab4b778a1bff5b8f11885e8f21a6c7a486918edcfc871185dac5` | 2981 | standard-library reader-thread decoding traceback; private local paths/profile identifier present |

Both were first committed in `1490e3cd7d15363efce9b55319dce623cd0e23f4`. Exact Git blob IDs, scanner line numbers and contextual fields are in publication-risk.json. Each produces five PY_TRACEBACK hits: the opening line and four frame lines. The warning originates from a pytest subprocess reader thread and the Windows cp1252 decoder (UnicodeDecodeError), with threading/subprocess/codec frames; no product exception stack or provider raw output was observed in these two blobs.

Private absolute Windows installation, profile and repository paths occur in both logs (10 and 7 occurrences respectively). A local account identifier is therefore disclosed. No token, credential, private key, email or separate personal payload was observed; actual path values and diagnostic bodies are intentionally not copied here.

The proposed path/blob/content-hash/rule exception is cryptographically narrow, and the traceback itself is a low-sensitivity environment diagnostic. However, approving it under a claim of no private paths would be inaccurate. Recommendation for each entry: keep PENDING; if the Owner wishes to publish this history, first explicitly accept the path/profile disclosure and then consider only the exact proposed blob/rule exception through the authorized process. No automatic approval is recorded.

A forward commit cannot remove these blobs from branch history. A separately authorized sanitized source export could omit history without rewriting it, but would not establish publication safety for this branch range. An Owner-authorized exception can resolve the scanner gate while retaining disclosure; it is not redaction. Until that separate decision, publication remains blocked and no release, integration, freeze or Full T3 is performed.
