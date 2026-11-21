"""Runtime provisioning, checksum fail-closed, and live CPU smoke tests for AXO /7 fine-tuned Q4_K_M SLM."""

from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from app.ai.adaptive_input_router import route_text_input_local_slm
from app.ai.local_geometry_parser import clear_local_geometry_parser_cache
from app.ai.local_slm_runtime import (
    DEFAULT_LOCAL_SLM_MODEL_KEY,
    FINETUNED_LOCAL_SLM_MODEL_KEY,
    LOCAL_SLM_MODELS,
    LocalSlmRuntime,
    LocalSlmRuntimeError,
    ensure_local_slm_provisioned,
    resolve_local_slm_model_spec,
)


def _runtime_and_model_cached() -> bool:
    try:
        ensure_local_slm_provisioned(model_key=FINETUNED_LOCAL_SLM_MODEL_KEY, allow_download=False)
        return True
    except LocalSlmRuntimeError:
        return False


def test_finetuned_model_spec_is_pinned_without_url_fallback():
    spec = resolve_local_slm_model_spec("finetuned")
    assert spec.model_key == FINETUNED_LOCAL_SLM_MODEL_KEY
    assert spec.size_bytes > 100_000_000
    assert spec.sha256 != "0" * 64 and len(spec.sha256) == 64
    assert resolve_local_slm_model_spec("v7").model_key == FINETUNED_LOCAL_SLM_MODEL_KEY
    # Ensure original /5 /6 model pin remains intact
    assert LOCAL_SLM_MODELS[DEFAULT_LOCAL_SLM_MODEL_KEY].sha256 == "ac2d97712095a558e31573f62f466a3f9d93990898b0ec79d7c974c1780d524a"


def test_finetuned_missing_model_fails_closed_when_offline(tmp_path: Path):
    cache_dir = tmp_path / "axo-slm-empty"
    rt_dir = cache_dir / "runtime" / "llama.cpp-b12470-win-cpu-x64"
    rt_dir.mkdir(parents=True)
    # Create valid runtime manifest pointing at dummy server binary so we reach model check cleanly
    exe = rt_dir / "llama-server.exe"
    exe.write_bytes(b"stub")
    from app.ai.local_slm_runtime import LLAMA_CPP_RUNTIME_SPEC
    import json
    (rt_dir / ".provision_manifest.json").write_text(
        json.dumps({
            "release_tag": LLAMA_CPP_RUNTIME_SPEC.release_tag,
            "size_bytes": LLAMA_CPP_RUNTIME_SPEC.size_bytes,
            "sha256": LLAMA_CPP_RUNTIME_SPEC.sha256,
            "server_rel_path": "llama-server.exe",
        }),
        encoding="utf-8",
    )
    with pytest.raises(LocalSlmRuntimeError) as exc_info:
        ensure_local_slm_provisioned(model_key=FINETUNED_LOCAL_SLM_MODEL_KEY, cache_dir=cache_dir, allow_download=False)
    assert exc_info.value.reason_code == "MODEL_RUNTIME_UNAVAILABLE"


def test_finetuned_corrupted_gguf_checksum_fails_closed(tmp_path: Path):
    cache_dir = tmp_path / "axo-slm-corrupt"
    rt_dir = cache_dir / "runtime" / "llama.cpp-b12470-win-cpu-x64"
    rt_dir.mkdir(parents=True)
    exe = rt_dir / "llama-server.exe"
    exe.write_bytes(b"stub")
    from app.ai.local_slm_runtime import LLAMA_CPP_RUNTIME_SPEC
    import json
    (rt_dir / ".provision_manifest.json").write_text(
        json.dumps({
            "release_tag": LLAMA_CPP_RUNTIME_SPEC.release_tag,
            "size_bytes": LLAMA_CPP_RUNTIME_SPEC.size_bytes,
            "sha256": LLAMA_CPP_RUNTIME_SPEC.sha256,
            "server_rel_path": "llama-server.exe",
        }),
        encoding="utf-8",
    )
    spec = resolve_local_slm_model_spec(FINETUNED_LOCAL_SLM_MODEL_KEY)
    m_path = cache_dir / "models" / spec.model_key / spec.filename
    m_path.parent.mkdir(parents=True, exist_ok=True)
    m_path.write_bytes(b"corrupted-weights")
    with pytest.raises(LocalSlmRuntimeError) as exc_info:
        ensure_local_slm_provisioned(
            model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
            cache_dir=cache_dir,
            allow_download=False,
            force_rehash=True,
        )
    assert exc_info.value.reason_code == "MODEL_CHECKSUM_MISMATCH"


@pytest.mark.skipif(not _runtime_and_model_cached(), reason="Fine-tuned Q4_K_M GGUF not provisioned locally")
def test_finetuned_runtime_provision_and_live_cpu_served_smoke(tmp_path: Path):
    prov = ensure_local_slm_provisioned(
        model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
        allow_download=False,
        force_rehash=True,
    )
    assert prov.model_path.is_file()
    assert prov.downloaded_model is False

    rt = LocalSlmRuntime(threads=6, allow_download=False)
    try:
        clear_local_geometry_parser_cache()
        text = (
            "Xét khối chóp K.UVWX có UVWX là hình bình hành với UV=2a, UX=a và góc VUX=60°. "
            "Cạnh KU vuông góc với đáy (UVWX) và KU=a√3. Tính thể tích khối chóp K.UVWX."
        )
        res = route_text_input_local_slm(
            text,
            runtime=rt,
            model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
            use_verified_normalizer=True,
            closure_mode="v7",
            normalizer_version="v2",
            threads=6,
        )
        assert res.status == "SERVED"
        assert (res.response.get("route_d") or {}).get("answers", {}).get("q1") == "a³"
    finally:
        rt.shutdown()
