# Test mechanism adaptation (no expected outcome changes)

The kind registry now owns S4. Removed redundant old schema branches rather than leaving two policies.
Old D-A and ratio-residual mutants now remove the corresponding registry restriction in memory; their payloads and expected codes are unchanged.
The S8 mutant targets the consolidated qualified/unqualified ownership predicate rather than the removed unqualified-only predicate.
The existing census gate now reads the append-only v3 inventory (187 fields), which adds the two previously missed indirect reads; v2 is untouched.
No original corpus, oracle, refusal expectation, historical result or audit file changed. The additional census self-test has an independently literal key set;
it was observed RED (missing analyzer function) before the census tooling edit. It implements the already preregistered N6 helper/partial/key-set requirement.
