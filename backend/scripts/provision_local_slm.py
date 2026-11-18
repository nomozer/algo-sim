"""Provision and verify pinned local CPU SLM runtime and GGUF models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ai.local_slm_runtime import (  # noqa: E402
    COMPARATOR_LOCAL_SLM_MODEL_KEY,
    DEFAULT_LOCAL_SLM_MODEL_KEY,
    FINETUNED_LOCAL_SLM_MODEL_KEY,
    LocalSlmRuntime,
    LocalSlmRuntimeError,
    ensure_local_slm_provisioned,
)

_SMOKE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "solid_name": {"type": "string"},
        "goal": {"type": "string"},
    },
    "required": ["solid_name", "goal"],
}


def _resolve_model_keys(selector: str) -> list[str]:
    norm = selector.strip().lower()
    if norm == "all":
        return [DEFAULT_LOCAL_SLM_MODEL_KEY, COMPARATOR_LOCAL_SLM_MODEL_KEY]
    if norm == "all_with_v7":
        return [DEFAULT_LOCAL_SLM_MODEL_KEY, FINETUNED_LOCAL_SLM_MODEL_KEY, COMPARATOR_LOCAL_SLM_MODEL_KEY]
    if norm == "primary":
        return [DEFAULT_LOCAL_SLM_MODEL_KEY]
    if norm in {"finetuned", "v7", "axo-v7"}:
        return [FINETUNED_LOCAL_SLM_MODEL_KEY]
    if norm == "comparator":
        return [COMPARATOR_LOCAL_SLM_MODEL_KEY]
    return [selector.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Provision and verify local llama.cpp + GGUF models.")
    parser.add_argument(
        "--model",
        default="primary",
        help="Model key ('primary', 'comparator', 'all', or explicit model_key).",
    )
    parser.add_argument("--cache-dir", default=None, help="Override LOCAL_SLM_CACHE_DIR.")
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Verify local cache only; fail closed if files are missing.",
    )
    parser.add_argument(
        "--force-rehash",
        action="store_true",
        help="Recompute SHA-256 instead of using stat cache.",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run a local CPU JSON-schema smoke inference on each provisioned model.",
    )
    parser.add_argument(
        "--inspect-help",
        action="store_true",
        help="Include llama-server.exe --help flag grep in output.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args(argv)

    results: list[dict] = []
    help_flags: list[str] = []
    runtime = LocalSlmRuntime(cache_dir=args.cache_dir, allow_download=False) if args.smoke_test else None

    try:
        for key in _resolve_model_keys(args.model):
            prov = ensure_local_slm_provisioned(
                model_key=key,
                cache_dir=args.cache_dir,
                allow_download=not args.no_download,
                force_rehash=args.force_rehash,
            )
            entry = prov.to_manifest_dict()
            if args.inspect_help and not help_flags:
                proc = subprocess.run(
                    [str(prov.server_executable), "--help"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                )
                for line in (proc.stdout or "").splitlines():
                    low = line.lower()
                    if any(tok in low for tok in ("--reasoning", "--jinja", "--no-webui", "-np,", "--parallel", "-c,", "--ctx-size", "-t,", "--threads")):
                        help_flags.append(line.strip())
            if runtime is not None:
                res = runtime.chat_completion_json(
                    model_key=prov.model_spec.model_key,
                    messages=[
                        {
                            "role": "system",
                            "content": "Trích xuất thông tin đề toán hình học sang JSON đúng schema.",
                        },
                        {
                            "role": "user",
                            "content": "Cho hình chóp S.ABC có SA vuông góc với (ABC). Tính khoảng cách từ A đến (SBC).",
                        },
                    ],
                    json_schema=_SMOKE_SCHEMA,
                    schema_name="smoke_geometry",
                    max_tokens=128,
                    allow_download=False,
                )
                entry["smoke_test"] = {
                    "ok": True,
                    "parsed_json": res.parsed_json,
                    "server_load_time_ms": res.server_load_time_ms,
                    "inference_time_ms": res.inference_time_ms,
                    "prompt_tokens": res.prompt_tokens,
                    "completion_tokens": res.completion_tokens,
                    "thinking_stripped": res.thinking_stripped,
                    "python_rss_mib": res.python_rss_mib,
                    "server_rss_mib": res.server_rss_mib,
                    "combined_rss_mib": res.combined_rss_mib,
                    "server_peak_rss_mib": res.server_peak_rss_mib,
                }
            results.append(entry)
    except LocalSlmRuntimeError as exc:
        payload = {"ok": False, "reason_code": exc.reason_code, "detail": exc.detail, "results": results}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2
    finally:
        if runtime is not None:
            runtime.shutdown()

    payload = {"ok": True, "models": results}
    if help_flags:
        payload["llama_server_flags"] = help_flags
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for item in results:
            mspec = item["model_spec"]
            print(f"[OK] {mspec['model_key']} -> {item['model_path']}")
            if "smoke_test" in item:
                st = item["smoke_test"]
                print(
                    f"     smoke: load={st['server_load_time_ms']}ms infer={st['inference_time_ms']}ms "
                    f"combined_rss={st['combined_rss_mib']}MiB json={st['parsed_json']}"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
