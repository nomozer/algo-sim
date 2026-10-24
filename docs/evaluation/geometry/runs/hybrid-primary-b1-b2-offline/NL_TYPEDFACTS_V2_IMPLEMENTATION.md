# NL to TypedFacts V2 implementation

`backend/app/ai/typed_fact_next_extraction.py` implements `Extractor.extract(source_text)` and frozen `ExtractionResult(payload, code, diagnostics)`. ReplayExtractor receives only verbatim source and deep-copies its supplied mapping. TransportExtractor reuses existing request framing, schema lowering and provider response parsing, accepts an explicitly injected transport, and makes one attempt without fallback. No SDK, key, provider connection or default live transport was added.

The canonical schema is unchanged. The new extraction request offers that existing V2 schema; the global `fact_extraction.RESPONSE_CONTRACT` remains `flat`. Provider acceptance of the lowered schema, prompt behavior, quality, cost, tokens and provider latency are **UNKNOWN / NOT_MEASURED**. Fake transport tests do not establish these properties.

Validation checks raw embedded problem_text against original text before Pydantic strips whitespace, checks every raw quote against the original, parses strictly as `/2`, preserves verbatim source in the resulting model, and uses Registry role/negation helpers to reject a conditional, negated, question or proof clause presented as a premise. Coordinates, invented fields and `/1` input fail canonical validation. Missing replay, truncated/malformed provider output and technical exceptions retain distinct sanitized codes.

V2 does not express general negated/conditional premise semantics. Those are not silently converted into positive facts. Full-source coverage is checked by the existing Source Gate after bridge/planning; B1 diagnostics explicitly say semantic_gate NOT_EXECUTED. Tests append omitted proof, conditional, negative and additional question clauses and verify the full service refuses them. This closed grammar is not a universal semantic coverage oracle; historical coverage limits remain in the planner gap report.

Evidence: 21 extraction tests; 185 related extraction/V2/v3 regressions passed during B1. Three product-boundary suites were subsequently included in the 429-test integration selection. Status: `NL_EXTRACTION_V2_OFFLINE_INTERFACE_VERIFIED`; `LIVE_EXTRACTION_QUALITY_UNKNOWN`.
