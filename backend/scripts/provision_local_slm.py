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
    V9_LOCAL_SLM_MODEL_KEY,
    LocalSlmRuntime,
    LocalSlmRuntimeError,
    ensure_local_slm_provisioned,
    read_active_local_slm_model_key,
    resolve_local_slm_cache_dir,
    resolve_local_slm_model_spec,
    write_active_local_slm_model_key,
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
    if norm in {"all_with_v9", "all_v9"}:
        return [DEFAULT_LOCAL_SLM_MODEL_KEY, FINETUNED_LOCAL_SLM_MODEL_KEY, V9_LOCAL_SLM_MODEL_KEY, COMPARATOR_LOCAL_SLM_MODEL_KEY]
    if norm == "primary":
        return [DEFAULT_LOCAL_SLM_MODEL_KEY]
    if norm in {"finetuned", "v7", "axo-v7"}:
        return [FINETUNED_LOCAL_SLM_MODEL_KEY]
    if norm in {"v9", "axo-v9", "v9-default"}:
        return [V9_LOCAL_SLM_MODEL_KEY]
    if norm in {"active", "v9-active"}:
        return [read_active_local_slm_model_key() or V9_LOCAL_SLM_MODEL_KEY]
    if norm == "comparator":
        return [COMPARATOR_LOCAL_SLM_MODEL_KEY]
    return [selector.strip()]


def _collect_status(*, cache_dir: str | None, verify_hashes: bool) -> dict:
    root = resolve_local_slm_cache_dir(cache_dir)
    active_key = read_active_local_slm_model_key(cache_dir) or V9_LOCAL_SLM_MODEL_KEY
    models_status: dict[str, dict] = {}
    all_core_ok = True
    for key in (DEFAULT_LOCAL_SLM_MODEL_KEY, FINETUNED_LOCAL_SLM_MODEL_KEY, V9_LOCAL_SLM_MODEL_KEY):
        try:
            prov = ensure_local_slm_provisioned(
                model_key=key,
                cache_dir=cache_dir,
                allow_download=False,
                force_rehash=verify_hashes,
            )
            models_status[key] = {
                "provisioned": True,
                "sha256": prov.model_spec.sha256,
                "model_path": str(prov.model_path),
                "server_executable": str(prov.server_executable),
            }
        except LocalSlmRuntimeError as exc:
            models_status[key] = {
                "provisioned": False,
                "reason_code": exc.reason_code,
                "detail": exc.detail,
            }
            if key in (active_key, V9_LOCAL_SLM_MODEL_KEY):
                all_core_ok = False
    return {
        "ok": all_core_ok,
        "cache_dir": str(root),
        "active_model_key": active_key,
        "explicit_active_override": read_active_local_slm_model_key(cache_dir),
        "models": models_status,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Provision and verify local llama.cpp + GGUF models.")
    parser.add_argument(
        "--model",
        default="primary",
        help="Model key ('primary', 'v7', 'v9', 'active', 'comparator', 'all', 'all_v9', or explicit model_key).",
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
    parser.add_argument("--status", action="store_true", help="Report current active model and local cache readiness.")
    parser.add_argument("--verify", action="store_true", help="Strictly rehash and verify active + frozen local models.")
    parser.add_argument("--activate", default=None, help="Verify and activate a local SLM model key (e.g., 'v9', 'v7').")
    parser.add_argument(
        "--rollback",
        nargs="?",
        const=FINETUNED_LOCAL_SLM_MODEL_KEY,
        default=None,
        help="Verify and roll back the active local model (default: qwen3-0.6b-axo-v7-q4_k_m).",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args(argv)

    if args.activate is not None or args.rollback is not None:
        target_sel = args.activate if args.activate is not None else args.rollback
        action = "activate" if args.activate is not None else "rollback"
        try:
            spec = resolve_local_slm_model_spec(target_sel)
            prov = ensure_local_slm_provisioned(
                model_key=spec.model_key,
                cache_dir=args.cache_dir,
                allow_download=False,
                force_rehash=True,
            )
            state_path = write_active_local_slm_model_key(
                spec.model_key,
                reason=f"cli_{action}",
                cache_dir=args.cache_dir,
            )
            payload = {
                "ok": True,
                "action": action,
                "active_model_key": spec.model_key,
                "sha256": spec.sha256,
                "model_path": str(prov.model_path),
                "state_file": str(state_path),
            }
            if args.json:
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print(f"[OK] {action}: active={spec.model_key} sha256={spec.sha256[:16]}... state={state_path}")
            return 0
        except LocalSlmRuntimeError as exc:
            payload = {"ok": False, "action": action, "reason_code": exc.reason_code, "detail": exc.detail}
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 2

    if args.status or args.verify:
        status_payload = _collect_status(cache_dir=args.cache_dir, verify_hashes=bool(args.verify or args.force_rehash))
        if args.json:
            print(json.dumps(status_payload, indent=2, ensure_ascii=False))
        else:
            print(
                f"[{'OK' if status_payload['ok'] else 'FAIL'}] active={status_payload['active_model_key']} "
                f"cache={status_payload['cache_dir']}"
            )
            for mk, info in status_payload["models"].items():
                if info.get("provisioned"):
                    print(f"  - {mk}: READY sha256={str(info['sha256'])[:16]}...")
                else:
                    print(f"  - {mk}: MISSING ({info.get('reason_code')})")
        return 0 if status_payload["ok"] else 2

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
