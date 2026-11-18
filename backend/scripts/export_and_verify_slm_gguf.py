"""Merge best LoRA adapter -> FP16 HF -> convert to F16.gguf -> quantize Q4_K_M and verify merge parity."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning"
BACKEND_PY = Path(r"D:\Documents\projects\algo-sim\backend\.venv\Scripts\python.exe")
TRAIN_PY = Path(r"C:\Users\Bunny\AppData\Local\axo-slm\training\.venv\Scripts\python.exe")
SCORE_SCRIPT = REPO_ROOT / "backend/scripts/score_slm_val_predictions.py"

BASE_HF_DIR = Path(r"C:\Users\Bunny\AppData\Local\axo-slm\base_hf\Qwen3-0.6B")
VAL_JSONL = Path(r"C:\Users\Bunny\AppData\Local\axo-slm\training\datasets\val.jsonl")
BEST_ADAPTER_DIR = Path(r"C:\Users\Bunny\AppData\Local\axo-slm\adapters\qwen3-0.6b-axo-v7-lora\best")
MERGED_HF_DIR = Path(r"C:\Users\Bunny\AppData\Local\axo-slm\merged_hf\qwen3-0.6b-axo-v7-fp16")
F16_GGUF_PATH = Path(r"C:\Users\Bunny\AppData\Local\axo-slm\gguf_build\Qwen3-0.6B-AxoV7-F16.gguf")
Q4_GGUF_PATH = Path(r"C:\Users\Bunny\AppData\Local\axo-slm\models\qwen3-0.6b-axo-v7-q4_k_m\Qwen3-0.6B-AxoV7-Q4_K_M.gguf")
ORIG_Q4_GGUF_PATH = Path(r"C:\Users\Bunny\AppData\Local\axo-slm\models\qwen3-0.6b-q4_k_m\Qwen3-0.6B-Q4_K_M.gguf")
ORIG_Q4_EXPECTED_SHA = "ac2d97712095a558e31573f62f466a3f9d93990898b0ec79d7c974c1780d524a"

CONVERTER_PY = Path(r"C:\Users\Bunny\AppData\Local\axo-slm\training\llama_cpp_b12470\convert_hf_to_gguf.py")
QUANTIZE_EXE = Path(r"C:\Users\Bunny\AppData\Local\axo-slm\runtime\llama.cpp-b12470-win-cpu-x64\llama-quantize.exe")


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().lower()


def _dir_manifest(root: Path) -> dict[str, dict[str, Any]]:
    meta: dict[str, dict[str, Any]] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and ".cache" not in p.parts:
            rel = str(p.relative_to(root)).replace("\\", "/")
            meta[rel] = {"size_bytes": p.stat().st_size, "sha256": _sha256(p)}
    return meta


@torch.no_grad()
def _eval_merged_hf_val(merged_dir: Path, tok: Any) -> dict[str, Any]:
    val_rows = [json.loads(ln) for ln in VAL_JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
    model = AutoModelForCausalLM.from_pretrained(str(merged_dir), dtype=torch.float32).to("cuda:0")
    model.eval()
    model.config.use_cache = True
    model.generation_config.do_sample = False
    model.generation_config.temperature = None
    model.generation_config.top_p = None
    model.generation_config.top_k = None

    preds: dict[str, str] = {}
    t0 = time.perf_counter()
    for idx, row in enumerate(val_rows):
        p_str = tok.apply_chat_template(row["messages"][:2], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        ids = tok(p_str, return_tensors="pt", add_special_tokens=False).input_ids.to("cuda:0")
        out = model(input_ids=ids, use_cache=True)
        pkv = out.past_key_values
        nxt = out.logits[:, -1, :].argmax(dim=-1, keepdim=True)
        toks = [int(nxt.item())]
        for _ in range(180):
            if toks[-1] == tok.eos_token_id:
                break
            out = model(input_ids=nxt, past_key_values=pkv, use_cache=True)
            pkv = out.past_key_values
            nxt = out.logits[:, -1, :].argmax(dim=-1, keepdim=True)
            toks.append(int(nxt.item()))
        preds[row["sample_id"]] = tok.decode(toks, skip_special_tokens=True).strip()
        if (idx + 1) % 23 == 0 or (idx + 1) == len(val_rows):
            print(f"  [MERGED-HF VAL] decoded {idx+1}/{len(val_rows)} ({time.perf_counter()-t0:.1f}s)", flush=True)

    del model
    torch.cuda.empty_cache()

    eval_dir = MERGED_HF_DIR.parent / "eval_logs"
    eval_dir.mkdir(parents=True, exist_ok=True)
    preds_path = eval_dir / "merged_hf_val_preds.json"
    score_path = eval_dir / "merged_hf_val_score.json"
    preds_path.write_text(json.dumps(preds, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    env = dict(os.environ, ALLOW_LIVE_AI="0", GEMINI_API_KEY="")
    subprocess.run(
        [str(BACKEND_PY), str(SCORE_SCRIPT), "--val-jsonl", str(VAL_JSONL), "--preds-json", str(preds_path), "--out-json", str(score_path)],
        check=True,
        env=env,
    )
    return json.loads(score_path.read_text(encoding="utf-8"))


def main() -> int:
    assert BEST_ADAPTER_DIR.is_dir(), f"Missing best adapter dir: {BEST_ADAPTER_DIR}"
    assert CONVERTER_PY.is_file(), f"Missing converter: {CONVERTER_PY}"
    assert QUANTIZE_EXE.is_file(), f"Missing llama-quantize.exe: {QUANTIZE_EXE}"
    assert ORIG_Q4_GGUF_PATH.is_file(), f"Missing baseline GGUF: {ORIG_Q4_GGUF_PATH}"

    orig_sha = _sha256(ORIG_Q4_GGUF_PATH)
    assert orig_sha == ORIG_Q4_EXPECTED_SHA, f"Original GGUF altered: {orig_sha} != {ORIG_Q4_EXPECTED_SHA}"

    print("[P5] Merging best LoRA onto FP32 CPU base -> saving standalone FP16 HF...", flush=True)
    tok = AutoTokenizer.from_pretrained(str(BASE_HF_DIR))
    base = AutoModelForCausalLM.from_pretrained(str(BASE_HF_DIR), dtype=torch.float32)
    peft_model = PeftModel.from_pretrained(base, str(BEST_ADAPTER_DIR))
    merged = peft_model.merge_and_unload()
    merged = merged.to(torch.float16)

    if MERGED_HF_DIR.exists():
        shutil.rmtree(MERGED_HF_DIR)
    MERGED_HF_DIR.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(str(MERGED_HF_DIR), safe_serialization=True)
    tok.save_pretrained(str(MERGED_HF_DIR))
    for fname in ("tokenizer_config.json", "tokenizer.json", "vocab.json", "merges.txt", "generation_config.json", "LICENSE"):
        src = BASE_HF_DIR / fname
        if src.is_file():
            shutil.copy2(src, MERGED_HF_DIR / fname)
    del merged, peft_model, base

    print("[P5] Evaluating reloaded standalone merged HF model strictly on val.jsonl...", flush=True)
    merged_score = _eval_merged_hf_val(MERGED_HF_DIR, tok)

    print("[P5] Converting standalone HF FP16 -> F16 GGUF via llama.cpp b12470...", flush=True)
    F16_GGUF_PATH.parent.mkdir(parents=True, exist_ok=True)
    if F16_GGUF_PATH.exists():
        F16_GGUF_PATH.unlink()
    subprocess.run(
        [str(TRAIN_PY), str(CONVERTER_PY), str(MERGED_HF_DIR), "--outfile", str(F16_GGUF_PATH), "--outtype", "f16"],
        check=True,
    )
    f16_size = F16_GGUF_PATH.stat().st_size
    f16_sha = _sha256(F16_GGUF_PATH)
    print(f"[P5] F16 GGUF: size={f16_size} sha256={f16_sha}", flush=True)

    print("[P5] Quantizing F16 GGUF -> Q4_K_M via llama-quantize.exe...", flush=True)
    Q4_GGUF_PATH.parent.mkdir(parents=True, exist_ok=True)
    if Q4_GGUF_PATH.exists():
        Q4_GGUF_PATH.unlink()
    subprocess.run([str(QUANTIZE_EXE), str(F16_GGUF_PATH), str(Q4_GGUF_PATH), "Q4_K_M"], check=True)
    q4_size = Q4_GGUF_PATH.stat().st_size
    q4_sha = _sha256(Q4_GGUF_PATH)
    print(f"[P5] Q4_K_M GGUF: size={q4_size} sha256={q4_sha}", flush=True)

    orig_sha_after = _sha256(ORIG_Q4_GGUF_PATH)
    assert orig_sha_after == ORIG_Q4_EXPECTED_SHA, "Original Q4_K_M GGUF mutated unexpectedly!"

    stage = {
        "schema": "slm-quantization-merge-stage/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "original_q4_k_m_path": str(ORIG_Q4_GGUF_PATH),
        "original_q4_k_m_sha256_verified": orig_sha_after,
        "merged_hf_fp16": {
            "path": str(MERGED_HF_DIR),
            "files": _dir_manifest(MERGED_HF_DIR),
            "val_metrics": {k: v for k, v in merged_score.items() if k != "samples"},
        },
        "f16_gguf": {"path": str(F16_GGUF_PATH), "size_bytes": f16_size, "sha256": f16_sha},
        "q4_k_m_gguf": {"path": str(Q4_GGUF_PATH), "size_bytes": q4_size, "sha256": q4_sha},
    }
    stage_path = MERGED_HF_DIR.parent / "SLM_QUANTIZATION_MERGE_STAGE.json"
    stage_path.write_text(json.dumps(stage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    man_path = OUT_DIR / "SLM_ADAPTER_MODEL_MANIFEST.json"
    if man_path.is_file():
        man = json.loads(man_path.read_text(encoding="utf-8"))
        man["exports"] = {
            "merged_hf_fp16": {"dir": str(MERGED_HF_DIR), "files": stage["merged_hf_fp16"]["files"]},
            "f16_gguf": stage["f16_gguf"],
            "q4_k_m_gguf": stage["q4_k_m_gguf"],
        }
        man_path.write_text(json.dumps(man, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[P5 STAGE DONE] Wrote {stage_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
