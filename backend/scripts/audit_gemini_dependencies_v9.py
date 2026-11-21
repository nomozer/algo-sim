# -*- coding: utf-8 -*-
"""AXO HYBRID /9 — Phase G (P6 / Gate G6): Exhaustive Gemini Dependency Audit & Replacement Map.

Inspects all production Gemini / external cloud AI entry points, triggers, callers, callees,
contracts, cache behavior, error behavior, ownership, local equivalents, and migration
classifications across `backend/app/**` and `frontend/src/**`.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RUN_DIR = ROOT / "docs/evaluation/geometry/runs/axo-hybrid-local-ai-replacement-vietnamese-nlu-offline-cutover"
RUN_DIR.mkdir(parents=True, exist_ok=True)


def _scan_files_for_gemini_tokens() -> dict[str, list[dict[str, Any]]]:
    pat = re.compile(r"GEMINI_API_KEY|GEMINI_MODEL|generativelanguage|call_gemini|live_transport|ALLOW_LIVE_AI|prepare_live_hybrid|hasKey|aiServiceConfigured")
    findings: dict[str, list[dict[str, Any]]] = {"backend_app": [], "frontend_src": []}
    for bucket, base in [("backend_app", ROOT / "backend/app"), ("frontend_src", ROOT / "frontend/src")]:
        for fp in sorted(base.rglob("*")):
            if not fp.is_file() or fp.suffix not in (".py", ".ts", ".tsx"):
                continue
            if ".test." in fp.name or fp.name in ("test-setup.ts", "test-source.ts"):
                continue
            text = fp.read_text(encoding="utf-8", errors="replace")
            hits = []
            for lineno, line in enumerate(text.splitlines(), 1):
                if pat.search(line):
                    hits.append({"line": lineno, "text": line.strip()[:180]})
            if hits:
                findings[bucket].append({
                    "file": fp.relative_to(ROOT).as_posix(),
                    "hit_count": len(hits),
                    "sample_lines": hits[:12],
                })
    return findings


DEPENDENCY_ENTRIES: list[dict[str, Any]] = [
    {
        "id": "GEM-01",
        "surface": "POST /api/analyze (default HYBRID_ROUTE_MODE=live)",
        "entry_point": "backend/app/main.py::analyze -> _analyze_hybrid_route -> prepare_live_hybrid",
        "trigger_condition": "HYBRID_ROUTE_MODE unset or 'live' (and HYBRID_LOCAL_FIRST != '1')",
        "caller": "frontend/src/llm/client.ts::analyzeProblem",
        "callee": "app.ai.hybrid_offline.LiveHybridRun.run -> _live_provider_transport -> app.ai.function_calling.live_transport",
        "input_contract": "AnalyzeBody(input={type:'text'|'code'|'document', content, source_provenance})",
        "output_contract": "ValidatedSimulationEnvelope + hybrid-route-d-simulation/4 (`route_d`)",
        "cache_behavior": "SQLite SimulationCache keyed by ROUTE_D_CACHE_POLICY (`145:route-d`) + prepare_live_hybrid hash",
        "error_behavior": "503 MISSING_API_KEY / LIVE_AI_DISABLED / HYBRID_DEADLINE_EXCEEDED; 502 PROVIDER_*; no legacy fallback",
        "ownership": "OWNED_FOR_LOCAL_ONLY_OPT_IN (default 'live' flip requires owner cutover approval)",
        "local_replacement_equivalent": "HYBRID_ROUTE_MODE=local-only-scoped / local-first-slm (`LocalSlmHybridRun` -> Local Parser -> slm-verified-normalizer/3 -> local-slm-extractor/4 -> Source Gate -> Planner /26 -> Kernel /24)",
        "migration_status": "REPLACE_WITH_LOCAL",
        "p7_status_in_v9": "Implemented behind explicit `HYBRID_ROUTE_MODE=local-only-scoped` (`0` cloud calls); default remains `live` pending owner cutover patch.",
    },
    {
        "id": "GEM-02",
        "surface": "POST /api/analyze (HYBRID_ROUTE_MODE=local-first with Gemini fallback)",
        "entry_point": "backend/app/main.py::_analyze_hybrid_route -> prepare_local_first_hybrid",
        "trigger_condition": "Local Geometry Parser /2 incomplete AND allow_live_ai and GEMINI_API_KEY",
        "caller": "backend/app/ai/hybrid_offline.py::LocalFirstHybridRun.run -> adaptive_input_router.route_text_input",
        "callee": "_live_provider_transport -> gemini-2.5-flash TypedFactNext /2",
        "input_contract": "problem_text + fallback_extractor",
        "output_contract": "AdaptiveRouteOutcome(route_d + telemetry)",
        "cache_behavior": "prepare_local_first_hybrid identity in SimulationCache",
        "error_behavior": "503 LIVE_AI_DISABLED / MISSING_API_KEY (enriched with local_understanding)",
        "ownership": "OWNED_EDITABLE",
        "local_replacement_equivalent": "Local Parser + slm-verified-normalizer/3 + Local Qwen3 SLM + slm-grounding-validator/4 (`local-only-scoped` / `offline-lab`, zero Gemini fallback)",
        "migration_status": "REPLACE_WITH_LOCAL",
        "p7_status_in_v9": "Replaced cleanly in `local-only-scoped` / `offline-lab` (`cloud_fallback_allowed = False`).",
    },
    {
        "id": "GEM-03",
        "surface": "POST /api/analyze legacy `input.type == 'image'` handler inside `ingest_to_text`",
        "entry_point": "backend/app/main.py::_analyze_once -> app.ingestion.input.ingest_to_text",
        "trigger_condition": "Only unreachable legacy call if `_analyze_once` image guard were removed",
        "caller": "backend/app/main.py::_analyze_once (now returns HTTP 400 IMAGE_DIRECT_UNSUPPORTED before `ingest_to_text`)",
        "callee": "app.ingestion.image_extraction.extract_problem_from_image -> call_gemini",
        "input_contract": "base64 image -> NormalizedImage",
        "output_contract": "problem_text string",
        "cache_behavior": "extract_problem_from_image LRU cache",
        "error_behavior": "400 IMAGE_DIRECT_UNSUPPORTED at `_analyze_once` line 1522",
        "ownership": "OWNED_FOR_LOCAL_ONLY_OPT_IN",
        "local_replacement_equivalent": "Already blocked at `_analyze_once`; local-only modes force `api_key=None` into `ingest_to_text` as defense-in-depth.",
        "migration_status": "DISABLE_AS_UNSUPPORTED",
        "p7_status_in_v9": "Hardened so `ingest_to_text(..., api_key=None if local_only else api_key)` never receives an API key in local-only mode.",
    },
    {
        "id": "GEM-04",
        "surface": "POST /api/input/prepare (Unified Photo/PDF/DOCX -> Vision Fallback)",
        "entry_point": "backend/app/main.py::input_prepare -> app.ingestion.unified_input.prepare_unified_input",
        "trigger_condition": "Scanned PDF or photo when Local OCR (`run_local_ocr_route`) is not auto-verified AND `vision_allowed = (ALLOW_LIVE_AI != '0' and bool(api_key))`",
        "caller": "frontend/src/llm/client.ts::prepareInput",
        "callee": "app.ingestion.image_extraction.extract_problem_from_image -> app.ai.gemini.call_gemini",
        "input_contract": "InputPrepareBody (images/PDF/DOCX + user_text + selected_candidate_id)",
        "output_contract": "UnifiedPrepareOutcome (`ready` | `needs_confirmation` | `needs_selection` | `rejected`)",
        "cache_behavior": "extract_problem_from_image LRU cache (`VISION_SCHEMA_IDENTITY` + `cache_version`)",
        "error_behavior": "503 MISSING_API_KEY / LIVE_AI_DISABLED; 502 VISION_OUTPUT_VALIDATION_FAILED",
        "ownership": "OWNED_FOR_LOCAL_ONLY_OPT_IN",
        "local_replacement_equivalent": "Local deterministic CV cropper + `run_local_ocr_route` (Paddle/RapidOCR + Tesseract/VietOCR + span confirmation); PDF/DOCX text+OMML are 100% deterministic.",
        "migration_status": "REPLACE_WITH_DETERMINISTIC",
        "p7_status_in_v9": "Hardened in `local-only-*` / `offline-lab`: `prepare_unified_input` receives `api_key=None` and `vision_allowed=False` even if `GEMINI_API_KEY` is in env (`0` Vision calls); scanned images go to Local OCR span confirmation or fail closed cleanly.",
    },
    {
        "id": "GEM-05",
        "surface": "POST /api/image/extract (Legacy Tier-A Vision Endpoint)",
        "entry_point": "backend/app/main.py::image_extract -> extract_problem_from_image",
        "trigger_condition": "Direct HTTP call to `/api/image/extract` (superseded by `/api/input/prepare` in frontend composer)",
        "caller": "Legacy tests / direct API clients (`frontend/src/llm/client.ts::extractImageProblem`)",
        "callee": "app.ingestion.image_extraction.extract_problem_from_image -> app.ai.gemini.call_gemini",
        "input_contract": "ImageExtractBody",
        "output_contract": "ImageProblemExtraction (`photo-problem-extraction/1`)",
        "cache_behavior": "LRU 64 entries in image_extraction.py",
        "error_behavior": "503 MISSING_API_KEY / LIVE_AI_DISABLED; 429/502/503",
        "ownership": "OWNED_FOR_LOCAL_ONLY_OPT_IN",
        "local_replacement_equivalent": "Disable cloud VLM in local-only modes (HTTP `503 LOCAL_ONLY_CLOUD_VISION_DISABLED`, directing callers to `/api/input/prepare` local OCR).",
        "migration_status": "DISABLE_AS_UNSUPPORTED",
        "p7_status_in_v9": "Blocked fail-closed (`503 LOCAL_ONLY_CLOUD_VISION_DISABLED`) whenever local-only route mode is active.",
    },
    {
        "id": "GEM-06",
        "surface": "Locked Gemini Extraction Surface Modules (`gemini.py`, `function_calling.py`, `fact_extraction.py`, `typed_fact_next_extraction.py`)",
        "entry_point": "backend/app/ai/typed_fact_next_extraction.py::typed_fact_next_surface_fingerprint, function_calling.py::live_transport, gemini.py::call_gemini",
        "trigger_condition": "Imported by Hybrid live route & telemetry identity; NOT invoked in `local-only-scoped` / `offline-lab`",
        "caller": "hybrid_offline.py (only when mode == 'live' or mode == 'local-first')",
        "callee": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent (x-goog-api-key)",
        "input_contract": "Locked SHA-256 extraction schemas (`33197a45…`, `7ea511a6…`, `485d3834…`, `4bff35bb…`)",
        "output_contract": "JSON `typed-fact-next/2` wire payload",
        "cache_behavior": "N/A (locked transport layer)",
        "error_behavior": "LiveAIDisabled when ALLOW_LIVE_AI=0; ProviderHTTPError on non-200",
        "ownership": "LOCKED_SURFACE (`BLOCKED_OWNERSHIP`)",
        "local_replacement_equivalent": "Retained untouched in codebase (`RETAIN_CODE_DISABLED` when local-only active) so rollback to `live` remains instant and locked hashes stay invariant.",
        "migration_status": "RETAIN_CODE_DISABLED",
        "p7_status_in_v9": "Preserved bit-identical (`0` bytes changed); zero imports/invocations reached on `local-only-*` runtime paths.",
    },
    {
        "id": "GEM-07",
        "surface": "Gemini Skills (`backend/app/ai/skills/*.md` — `transcribe.md`, `typed_fact_next*`, etc.)",
        "entry_point": "backend/app/ai/gemini.py::load_skill, runtime_identity.py::skill_fingerprint",
        "trigger_condition": "Gemini live prompt loading & `cache_identity.lock.json` fingerprinting",
        "caller": "fact_extraction.py, image_extraction.py, runtime_identity.py",
        "callee": "Local `.md` files read from disk",
        "input_contract": "Markdown skill prompts",
        "output_contract": "System prompt strings + SHA-256 hashes",
        "cache_behavior": "process-local `_skill_cache` dict",
        "error_behavior": "FileNotFoundError if missing",
        "ownership": "LOCKED_SURFACE (`cache_identity.lock.json` depends on skill hashes)",
        "local_replacement_equivalent": "Compact Chinese/Vietnamese system prompt in `local_slm_extractor.py` for Local Qwen3 SLM.",
        "migration_status": "RETAIN_CODE_DISABLED",
        "p7_status_in_v9": "Kept untouched so `semantic_environment_hash` and live rollback integrity remain intact.",
    },
    {
        "id": "GEM-08",
        "surface": "Health & Runtime Diagnostics (`GET /api/health`, `GET /api/diagnostics/runtime`, `accounts/router.py` admin overview)",
        "entry_point": "backend/app/main.py::health, diagnostics_runtime; backend/app/accounts/router.py",
        "trigger_condition": "Every frontend initial load (`checkHealth`) and admin overview fetch",
        "caller": "frontend/src/llm/client.ts::checkHealth, ProblemInput.tsx, AuthGate.tsx",
        "callee": "os.getenv('GEMINI_API_KEY'), os.getenv('GEMINI_MODEL')",
        "input_contract": "HTTP GET",
        "output_contract": "JSON `{ok, hasKey, ...}` + additive local-only fields",
        "cache_behavior": "Uncached live status snapshot",
        "error_behavior": "Always HTTP 200",
        "ownership": "Backend owned (`main.py`), `frontend/**` (`AuthGate.tsx`, `ProblemInput.tsx`) BLOCKED_OWNERSHIP",
        "local_replacement_equivalent": "Expose `localOnlyMode`, `localSlmReady`, `localSlmModel`, `extractionBackend`, `aiAvailable` in `/api/health` while keeping `hasKey` truthful (`bool(GEMINI_API_KEY)`) and delivering frontend UX patch via `handoff/`.",
        "migration_status": "REPLACE_WITH_LOCAL",
        "p7_status_in_v9": "Backend metadata implemented cleanly; frontend keyless banner update handed off in `handoff/frontend_local_ai_status_and_keyless_ux.patch`.",
    },
    {
        "id": "GEM-09",
        "surface": "Frontend Composer & AuthGate (`hasKey` / `MISSING_API_KEY` UX)",
        "entry_point": "frontend/src/components/ProblemInput.tsx:210,292,1004; frontend/src/components/AuthGate.tsx:7236; frontend/src/components/photo-problem-flow.ts",
        "trigger_condition": "health.hasKey === false when GEMINI_API_KEY unset on backend",
        "caller": "React UI on mount & on analyze errors",
        "callee": "Displays 'Máy chủ chưa bật kết nối AI cho đề tự nhập' or 'Chưa cấu hình GEMINI_API_KEY'",
        "input_contract": "ServerHealth & HTTP 503 error payloads",
        "output_contract": "User-facing Vietnamese status notices (hiding API key env var names in student UI)",
        "cache_behavior": "Browser memory",
        "error_behavior": "Shows offline/missing-key banner if health.hasKey == false",
        "ownership": "BLOCKED_OWNERSHIP (separate `axo-geometry-library` worktree `0fe3873a4`)",
        "local_replacement_equivalent": "Respect `health.aiAvailable` / `health.localOnlyMode && health.localSlmReady` and handle local SLM 503 states (`MODEL_RUNTIME_UNAVAILABLE`, `LOCAL_SLM_BUSY`, `LOCAL_SLM_TIMEOUT`).",
        "migration_status": "OUTSIDE_APPROVED_SCOPE",
        "p7_status_in_v9": "Verified `git apply --check` handoff patch generated (`frontend_local_ai_status_and_keyless_ux.patch`), zero direct edit to `frontend/**`.",
    },
]


def main() -> int:
    scan = _scan_files_for_gemini_tokens()
    counts = Counter(e["migration_status"] for e in DEPENDENCY_ENTRIES)
    inventory = {
        "schema": "gemini-dependency-inventory/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "external_ai_calls": 0,
        "summary": {
            "total_dependency_surfaces_mapped": len(DEPENDENCY_ENTRIES),
            "by_migration_status": dict(counts),
            "backend_files_matching_gemini_tokens": len(scan["backend_app"]),
            "frontend_files_matching_gemini_tokens": len(scan["frontend_src"]),
        },
        "dependencies": DEPENDENCY_ENTRIES,
        "static_token_scan": scan,
    }
    (RUN_DIR / "GEMINI_DEPENDENCY_INVENTORY.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    md_lines = [
        "# AXO HYBRID /9 — Gemini Dependency Audit & Replacement Coverage Report",
        "",
        f"- **Surfaces Audited:** `{len(DEPENDENCY_ENTRIES)}` across `backend/app/**` (`{len(scan['backend_app'])}` token-matching files) & `frontend/src/**` (`{len(scan['frontend_src'])}` token-matching files)",
        f"- **Migration Distribution:** `{dict(counts)}`",
        "- **Rule Followed (§18 & §23):** Locked Gemini modules (`gemini.py`, `function_calling.py`, `fact_extraction.py`, `typed_fact_next_extraction.py`, `skills/*.md`) are kept `RETAIN_CODE_DISABLED` on local-only paths rather than deleted prematurely, preserving locked extraction surface hashes (`33197a45…`) and instant rollback.",
        "",
        "## Replacement Map",
        "",
        "| ID | Surface | Ownership | Classification | Local Replacement / Disposition |",
        "|---|---|---|---|---|",
    ]
    for e in DEPENDENCY_ENTRIES:
        md_lines.append(
            f"| `{e['id']}` | {e['surface']} | `{e['ownership']}` | `{e['migration_status']}` | {e['local_replacement_equivalent']} |"
        )
    (RUN_DIR / "GEMINI_REPLACEMENT_COVERAGE_REPORT.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print("Gemini inventory written:", inventory["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
