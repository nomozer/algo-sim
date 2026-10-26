# Hybrid V2 — architecture diff of this campaign

Target pipeline (Owner directive) and what serves each stage now:

| Stage | Component (existing unless marked NEW) | State after this campaign |
|---|---|---|
| Natural-language problem | `/api/analyze` → `ingest_to_text` | unchanged |
| → TypedFacts V2 | `typed_fact_next_extraction.extract_typed_fact_next_v2` + an `Extractor` | **offline only**: `ReplayExtractor` over an authored corpus. The provider extractor `TransportExtractor` exists but no live call is allowed (no Owner GO) |
| → Source / provenance gate | schema + source identity + verbatim quotes (`extract_typed_fact_next_v2`), then `registry.kiem_nguon` | unchanged |
| → Geometry Registry → bounded planner | `typed_fact_next_bridge.bridge_v2` → `planner` | **NEW: angle goals** (`{line, plane}`, `{line1, line2}`, `{plane1, plane2}` → existing `ask_angle_*`) |
| → exact geometry functions | `engine` + `semantic_program.interpreter` + kernel | unchanged |
| → verified results + trace → Scene3D envelope | `function_route.chay_sau_cau_noi` → `adapter4_route.build_adapter4_response` | unchanged; producer witness changes (`u_to`, right-angle witness) apply to every route that builds Scene3D through `quantity_annotations` |
| → learner-facing simulation | frontend `docPhanHoiHybrid` → `store.loadEnvelope` → `Scene3DExplorer` | **NEW: reachable from the normal input box** — `llm/client.ts::docPhanHoiPhanTich` reads a /4 response from `/api/analyze` |

## NEW: migration Stage 2 — Hybrid V2 opt-in local

- `main._hybrid_v2_local`: active only when the server sets `HYBRID_V2_LOCAL=offline-replay` **and** the client is
  loopback. Otherwise `None`: the default `LLM_ONLY` path runs unchanged (same code, same cache, same policy).
- `main._analyze_hybrid_v2_local`: domain gate (shared helper `_ngoai_pham_vi`, same behaviour) →
  `hybrid_offline.run_local_replay(text, HYBRID_V2_LOCAL_REPLAY_CORPUS)` → the /4 response as is, `Cache-Control:
  no-store`. It runs **before** the cache lookup: a cached `LLM_ONLY` envelope for the same text is never served under
  the Hybrid label. No fallback: a Hybrid refusal is the answer.
- Import-closure lock (`test_structured_geometry_relations.py::test_Y…`): one new declared, lazy edge
  `("main.py", "app.ai.hybrid_offline")`. Positive control: the gate module really reaches route D.
- Corpus: `scripts/export_hybrid_v2_local_corpus.py` → `local-replay-corpus.json` (43 texts from the 47 locked authored
  development cases; 2 texts with two different payloads each are excluded, not picked).

## Not changed

Default route (`LLM_ONLY`), `CACHE_VERSION` for this stage (the default policy and every cached envelope are
unchanged; Hybrid responses are neither read from nor written to the cache), the model surface (prompts, grammar card,
schemas, capability table), the operator preview endpoint, live provider transport (0 calls).
