# -*- coding: utf-8 -*-
"""AXO HYBRID /9 — Targeted LoRA Fine-Tuning (`AxoV9`) on GTX 1650 + FP16 Merge + Q4_K_M GGUF Export."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from peft import LoraConfig, PeftModel, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ["TOKENIZERS_PARALLELISM"] = "false"

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_PY = Path(r"D:\Documents\projects\algo-sim\backend\.venv\Scripts\python.exe")
TRAIN_PY = Path(r"C:\Users\Bunny\AppData\Local\axo-slm\training\.venv\Scripts\python.exe")
SCORE_SCRIPT = REPO_ROOT / "backend/scripts/score_slm_v9_predictions.py"
OUT_DIR = REPO_ROOT / "docs/evaluation/geometry/runs/axo-hybrid-local-ai-replacement-vietnamese-nlu-offline-cutover"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LOCAL_APPDATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
DATASET_DIR = LOCAL_APPDATA / "axo-slm/training/datasets_v9"
BASE_HF_DIR = LOCAL_APPDATA / "axo-slm/base_hf/Qwen3-0.6B"
ADAPTER_ROOT = LOCAL_APPDATA / "axo-slm/adapters/qwen3-0.6b-axo-v9-lora"
MERGED_HF_DIR = LOCAL_APPDATA / "axo-slm/merged_hf/qwen3-0.6b-axo-v9-fp16"
F16_GGUF_PATH = LOCAL_APPDATA / "axo-slm/gguf_build/Qwen3-0.6B-AxoV9-F16.gguf"
Q4_GGUF_PATH = LOCAL_APPDATA / "axo-slm/models/qwen3-0.6b-axo-v9-q4_k_m/Qwen3-0.6B-AxoV9-Q4_K_M.gguf"
V7_GGUF_PATH = LOCAL_APPDATA / "axo-slm/models/qwen3-0.6b-axo-v7-q4_k_m/Qwen3-0.6B-AxoV7-Q4_K_M.gguf"
ORIG_GGUF_PATH = LOCAL_APPDATA / "axo-slm/models/qwen3-0.6b-q4_k_m/Qwen3-0.6B-Q4_K_M.gguf"

EXPECTED_V7_SHA = "36e784d135627225e0b9c11b097c9a36222ee1e0e3f6f1d6116cc3060ac5e148"
EXPECTED_ORIG_SHA = "ac2d97712095a558e31573f62f466a3f9d93990898b0ec79d7c974c1780d524a"

CONVERTER_PY = LOCAL_APPDATA / "axo-slm/training/llama_cpp_b12470/convert_hf_to_gguf.py"
QUANTIZE_EXE = LOCAL_APPDATA / "axo-slm/runtime/llama.cpp-b12470-win-cpu-x64/llama-quantize.exe"
BASE_HF_REPO = "Qwen/Qwen3-0.6B"
BASE_HF_REV = "c1899de289a04d12100db370d81485cdf75e47ca"


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().lower()


def _tokenize_dataset(jsonl_path: Path, tok: Any) -> list[dict[str, Any]]:
    rows = [json.loads(ln) for ln in jsonl_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    out: list[dict[str, Any]] = []
    for r in rows:
        p_str = tok.apply_chat_template(r["messages"][:2], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        comp = r["gold_compact_json_str"] + tok.eos_token
        p_ids = tok(p_str, add_special_tokens=False).input_ids
        c_ids = tok(comp, add_special_tokens=False).input_ids
        out.append({
            "sample_id": r["sample_id"],
            "prompt_str": p_str,
            "input_ids": p_ids + c_ids,
            "labels": ([-100] * len(p_ids)) + c_ids,
        })
    return out


def _eval_hf_val(model: Any, tok: Any, val_items: list[dict[str, Any]], val_jsonl: Path, eval_dir: Path, tag: str, *, compute_loss: bool = True) -> tuple[float | None, dict[str, Any]]:
    eval_dir.mkdir(parents=True, exist_ok=True)
    if hasattr(model, "gradient_checkpointing_disable"):
        model.gradient_checkpointing_disable()
    model.eval()

    avg_loss = None
    if compute_loss:
        core = model.base_model.model if isinstance(model, PeftModel) else model
        core.config.use_cache = False
        loss_sum, tok_sum = 0.0, 0
        with torch.no_grad():
            for it in val_items:
                seq = torch.tensor([it["input_ids"]], dtype=torch.long, device="cuda:0")
                lbl = torch.tensor([it["labels"]], dtype=torch.long, device="cuda:0")
                out = core.model(input_ids=seq, use_cache=False)
                hidden = out.last_hidden_state[:, :-1, :]
                shift_lbl = lbl[:, 1:]
                mask = shift_lbl.ne(-100)
                logits = core.lm_head(hidden[mask])
                loss_sum += float(F.cross_entropy(logits, shift_lbl[mask], reduction="sum").item())
                tok_sum += int(mask.sum().item())
        avg_loss = loss_sum / max(1, tok_sum)

    core = model.base_model.model if isinstance(model, PeftModel) else model
    core.config.use_cache = True
    preds: dict[str, str] = {}
    t0 = time.perf_counter()
    with torch.no_grad():
        for idx, it in enumerate(val_items):
            p_ids = tok(it["prompt_str"], return_tensors="pt", add_special_tokens=False).input_ids.to("cuda:0")
            out = model(input_ids=p_ids, use_cache=True)
            pkv = out.past_key_values
            nxt = out.logits[:, -1, :].argmax(dim=-1, keepdim=True)
            toks = [int(nxt.item())]
            for _ in range(256):
                if toks[-1] == tok.eos_token_id:
                    break
                out = model(input_ids=nxt, past_key_values=pkv, use_cache=True)
                pkv = out.past_key_values
                nxt = out.logits[:, -1, :].argmax(dim=-1, keepdim=True)
                toks.append(int(nxt.item()))
            preds[it["sample_id"]] = tok.decode(toks, skip_special_tokens=True).strip()
            if (idx + 1) % 30 == 0 or (idx + 1) == len(val_items):
                print(f"  [VAL {tag}] decoded {idx+1}/{len(val_items)} ({time.perf_counter()-t0:.1f}s)", flush=True)

    preds_path = eval_dir / f"val_preds_{tag}.json"
    score_path = eval_dir / f"val_score_{tag}.json"
    preds_path.write_text(json.dumps(preds, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    env = dict(os.environ, ALLOW_LIVE_AI="0", GEMINI_API_KEY="")
    subprocess.run([str(BACKEND_PY), str(SCORE_SCRIPT), "--val-jsonl", str(val_jsonl), "--preds-json", str(preds_path), "--out-json", str(score_path)], check=True, env=env)
    sc = json.loads(score_path.read_text(encoding="utf-8"))
    if hasattr(model, "gradient_checkpointing_enable"):
        core.config.use_cache = False
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.train()
    return avg_loss, sc


def _cosine_lr(step: int, total_steps: int, warmup_steps: int, max_lr: float, min_lr: float) -> float:
    if step < warmup_steps:
        return max_lr * (step + 1) / max(1, warmup_steps)
    prog = min(1.0, max(0.0, (step - warmup_steps) / max(1, total_steps - warmup_steps)))
    return min_lr + 0.5 * (max_lr - min_lr) * (1.0 + math.cos(math.pi * prog))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--export-only", action="store_true", help="Reuse completed epoch checkpoints + merged HF FP16 from task-4598 and run FP16/F16/Q4_K_M export + verification.")
    ap.add_argument("--gguf-eval-only", action="store_true", help="Reuse already exported FP16 val score and Q4_K_M GGUF and run only the GGUF vs AxoV7 val comparison.")
    args = ap.parse_args()

    assert _sha256(V7_GGUF_PATH) == EXPECTED_V7_SHA, "Frozen AxoV7 GGUF modified unexpectedly!"
    assert _sha256(ORIG_GGUF_PATH) == EXPECTED_ORIG_SHA, "Frozen base GGUF modified unexpectedly!"

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)

    train_jsonl = DATASET_DIR / "train_v9.jsonl"
    val_jsonl = DATASET_DIR / "val_v9.jsonl"
    assert train_jsonl.exists() and val_jsonl.exists(), "Run build_slm_v9_training_dataset.py first"

    tok = AutoTokenizer.from_pretrained(str(BASE_HF_DIR))
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token

    train_items = _tokenize_dataset(train_jsonl, tok)
    val_items = _tokenize_dataset(val_jsonl, tok)
    print(f"[TRAIN V9] train={len(train_items)} val={len(val_items)} | gpu={torch.cuda.get_device_name(0)}", flush=True)

    ADAPTER_ROOT.mkdir(parents=True, exist_ok=True)
    eval_dir = ADAPTER_ROOT / "val_eval_logs"
    best_dst = ADAPTER_ROOT / "best"

    if args.export_only or args.gguf_eval_only:
        assert best_dst.is_dir() and (MERGED_HF_DIR / "model.safetensors").is_file(), "Missing best adapter or merged FP16"
        # Derive exact param counts & reuse observed val_score_epoch{0..3}.json from task-4598
        base_cpu_tmp = AutoModelForCausalLM.from_pretrained(str(BASE_HF_DIR), dtype=torch.float32)
        peft_tmp = PeftModel.from_pretrained(base_cpu_tmp, str(best_dst), is_trainable=True)
        trainable_params = sum(p.numel() for p in peft_tmp.parameters() if p.requires_grad)
        all_params = sum(p.numel() for p in peft_tmp.parameters())
        del peft_tmp, base_cpu_tmp
        obs_losses = {
            0: (None, 0.3277),
            1: (0.0429, 0.0205),
            2: (0.0025, 0.0251),
            3: (0.0002, 0.0203),
        }
        epoch_history = []
        for ep in range(4):
            sc_ep = json.loads((eval_dir / f"val_score_epoch{ep}.json").read_text(encoding="utf-8"))
            tl, vl = obs_losses[ep]
            row_ep: dict[str, Any] = {
                "epoch": ep,
                "train_loss": tl,
                "val_loss": vl,
                "val_metrics": {k: v for k, v in sc_ep.items() if k != "sample_results"},
            }
            if ep >= 1:
                row_ep["adapter_dir"] = str(ADAPTER_ROOT / f"epoch_{ep}")
            epoch_history.append(row_ep)
        best_epoch = 3
        peak_mib = "NOT_MEASURED_ON_EXPORT_ONLY_RESUME"
        train_wall = 9804.3
    else:
        torch.cuda.reset_peak_memory_stats()
        base_model = AutoModelForCausalLM.from_pretrained(str(BASE_HF_DIR), dtype=torch.float32).to("cuda:0")
        base_model.config.use_cache = False

        lora_cfg = LoraConfig(
            r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        )
        pm = get_peft_model(base_model, lora_cfg)
        pm.generation_config.do_sample = False
        pm.generation_config.temperature = None
        pm.generation_config.top_p = None
        pm.generation_config.top_k = None
        pm.enable_input_require_grads()
        pm.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        pm.train()

        trainable_params = sum(p.numel() for p in pm.parameters() if p.requires_grad)
        all_params = sum(p.numel() for p in pm.parameters())

        epoch_history: list[dict[str, Any]] = []
        t_start = time.perf_counter()

        # Epoch 0 val_loss baseline
        vl0, sc0 = _eval_hf_val(pm, tok, val_items, val_jsonl, eval_dir, "epoch0", compute_loss=True)
        epoch_history.append({
            "epoch": 0, "train_loss": None, "val_loss": round(float(vl0 or 0.0), 6),
            "val_metrics": {k: v for k, v in sc0.items() if k != "sample_results"},
        })
        print(f"  [EP 0] val_loss={vl0:.4f} pos={sc0['positives_oracle_exact']}/{sc0['positives_total']} neg={sc0['negatives_safe_refused']}/{sc0['negatives_total']} ws={sc0['wrong_served_count']}", flush=True)

        opt_params = [p for p in pm.parameters() if p.requires_grad]
        opt = torch.optim.AdamW(opt_params, lr=args.lr, weight_decay=0.01)
        steps_per_epoch = math.ceil(len(train_items) / args.grad_accum)
        total_opt_steps = steps_per_epoch * args.epochs
        warmup_steps = max(1, int(0.10 * total_opt_steps))
        rng = random.Random(args.seed)
        global_opt_step = 0

        for epoch in range(1, args.epochs + 1):
            ep_items = list(train_items)
            rng.shuffle(ep_items)
            pm.train()
            pm.base_model.model.config.use_cache = False
            opt.zero_grad(set_to_none=True)
            ep_loss_sum, ep_tok_sum = 0.0, 0
            ep_t0 = time.perf_counter()

            for step_idx, it in enumerate(ep_items):
                seq = torch.tensor([it["input_ids"]], dtype=torch.long, device="cuda:0")
                lbl = torch.tensor([it["labels"]], dtype=torch.long, device="cuda:0")
                out = pm.base_model.model.model(input_ids=seq, use_cache=False)
                hidden = out.last_hidden_state[:, :-1, :]
                shift_lbl = lbl[:, 1:]
                mask = shift_lbl.ne(-100)
                sel_lbl = shift_lbl[mask]
                logits = pm.base_model.model.lm_head(hidden[mask])
                n_tok = int(sel_lbl.numel())
                loss_sum = F.cross_entropy(logits, sel_lbl, reduction="sum")
                ep_loss_sum += float(loss_sum.item())
                ep_tok_sum += n_tok
                ((loss_sum / max(1, n_tok)) / args.grad_accum).backward()

                if (step_idx + 1) % args.grad_accum == 0 or (step_idx + 1) == len(ep_items):
                    cur_lr = _cosine_lr(global_opt_step, total_opt_steps, warmup_steps, args.lr, 1e-5)
                    for pg in opt.param_groups:
                        pg["lr"] = cur_lr
                    torch.nn.utils.clip_grad_norm_(opt_params, 1.0)
                    opt.step()
                    opt.zero_grad(set_to_none=True)
                    global_opt_step += 1

                if (step_idx + 1) % 80 == 0 or (step_idx + 1) == len(ep_items):
                    print(f"[EP {epoch}/{args.epochs}] {step_idx+1}/{len(ep_items)} avg_loss={ep_loss_sum/max(1,ep_tok_sum):.4f} elapsed={time.perf_counter()-ep_t0:.1f}s", flush=True)

            train_loss = ep_loss_sum / max(1, ep_tok_sum)
            ep_dir = ADAPTER_ROOT / f"epoch_{epoch}"
            ep_dir.mkdir(parents=True, exist_ok=True)
            pm.save_pretrained(str(ep_dir))
            vl, sc = _eval_hf_val(pm, tok, val_items, val_jsonl, eval_dir, f"epoch{epoch}", compute_loss=True)
            epoch_history.append({
                "epoch": epoch, "train_loss": round(train_loss, 6), "val_loss": round(float(vl or 0.0), 6),
                "adapter_dir": str(ep_dir),
                "val_metrics": {k: v for k, v in sc.items() if k != "sample_results"},
            })
            print(f"  [VAL EP {epoch}] val_loss={vl:.4f} pos={sc['positives_oracle_exact']}/{sc['positives_total']} neg={sc['negatives_safe_refused']}/{sc['negatives_total']} ws={sc['wrong_served_count']}", flush=True)

        best_epoch = -1
        best_key = (-1, -1, float("-inf"))
        for eh in epoch_history:
            if eh["epoch"] >= 1:
                vm = eh["val_metrics"]
                ck = (1 if vm["wrong_served_count"] == 0 else 0, vm["overall_correct"], -eh["val_loss"])
                if ck > best_key:
                    best_key = ck
                    best_epoch = int(eh["epoch"])

        if best_dst.exists():
            shutil.rmtree(best_dst)
        shutil.copytree(ADAPTER_ROOT / f"epoch_{best_epoch}", best_dst)

        del pm, base_model
        torch.cuda.empty_cache()
        peak_mib = round(torch.cuda.max_memory_allocated() / 1048576.0, 2)
        train_wall = round(time.perf_counter() - t_start, 2)

        # Merge FP16 HF
        base_cpu = AutoModelForCausalLM.from_pretrained(str(BASE_HF_DIR), dtype=torch.float32)
        peft_best = PeftModel.from_pretrained(base_cpu, str(best_dst))
        merged = peft_best.merge_and_unload().to(torch.float16)
        if MERGED_HF_DIR.exists():
            shutil.rmtree(MERGED_HF_DIR)
        MERGED_HF_DIR.mkdir(parents=True, exist_ok=True)
        merged.save_pretrained(str(MERGED_HF_DIR), safe_serialization=True)
        tok.save_pretrained(str(MERGED_HF_DIR))
        for fn in ("tokenizer_config.json", "tokenizer.json", "vocab.json", "merges.txt", "generation_config.json", "LICENSE"):
            sp = BASE_HF_DIR / fn
            if sp.is_file():
                shutil.copy2(sp, MERGED_HF_DIR / fn)
        del merged, peft_best, base_cpu

    if args.gguf_eval_only and (eval_dir / "val_score_merged_fp16.json").is_file() and Q4_GGUF_PATH.is_file():
        sc_fp16 = json.loads((eval_dir / "val_score_merged_fp16.json").read_text(encoding="utf-8"))
        q4_size = Q4_GGUF_PATH.stat().st_size
        q4_sha = _sha256(Q4_GGUF_PATH)
    else:
        # Evaluate Merged FP16 HF on val_v9
        m_fp = AutoModelForCausalLM.from_pretrained(str(MERGED_HF_DIR), dtype=torch.float32).to("cuda:0")
        _, sc_fp16 = _eval_hf_val(m_fp, tok, val_items, val_jsonl, eval_dir, "merged_fp16", compute_loss=False)
        del m_fp
        torch.cuda.empty_cache()

        # Convert to F16 GGUF -> Q4_K_M GGUF
        F16_GGUF_PATH.parent.mkdir(parents=True, exist_ok=True)
        if F16_GGUF_PATH.exists():
            F16_GGUF_PATH.unlink()
        subprocess.run([str(TRAIN_PY), str(CONVERTER_PY), str(MERGED_HF_DIR), "--outfile", str(F16_GGUF_PATH), "--outtype", "f16"], check=True)
        Q4_GGUF_PATH.parent.mkdir(parents=True, exist_ok=True)
        if Q4_GGUF_PATH.exists():
            Q4_GGUF_PATH.unlink()
        subprocess.run([str(QUANTIZE_EXE), str(F16_GGUF_PATH), str(Q4_GGUF_PATH), "Q4_K_M"], check=True)
        q4_size = Q4_GGUF_PATH.stat().st_size
        q4_sha = _sha256(Q4_GGUF_PATH)

    # Verify frozen V7 & ORIG models untouched
    assert _sha256(V7_GGUF_PATH) == EXPECTED_V7_SHA, "AxoV7 mutated!"
    assert _sha256(ORIG_GGUF_PATH) == EXPECTED_ORIG_SHA, "Base Q4_K_M mutated!"

    # Run GGUF parity evaluation on val_v9 via BACKEND_PY using llama-server for BOTH AxoV7 and AxoV9!
    gguf_cmp_path = eval_dir / "gguf_val_comparison.json"
    eval_code = f"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(r'{REPO_ROOT}') / 'backend'))
from app.ai import local_slm_runtime as LSR
from app.ai.local_slm_runtime import LocalSlmRuntime, LocalSlmModelSpec, FINETUNED_LOCAL_SLM_MODEL_KEY
from app.ai.local_slm_extractor import build_compact_clause_context, build_compact_grammar_for_context, _build_compact_clause_messages, V9_CLOSURE_MODE

val_rows = [json.loads(ln) for ln in Path(r'{val_jsonl}').read_text(encoding='utf-8').splitlines() if ln.strip()]
v9_spec = LocalSlmModelSpec(
    model_key='qwen3-0.6b-axo-v9-q4_k_m',
    role='finetuned',
    repo_id='local/Qwen3-0.6B-AxoV9-LoRA-Merged',
    revision='{BASE_HF_REV}+axo-v9-lora',
    filename='Qwen3-0.6B-AxoV9-Q4_K_M.gguf',
    url='',
    size_bytes={q4_size},
    sha256='{q4_sha}',
    license='Apache-2.0',
    family='qwen3',
    param_count_b=0.6,
    quantization='Q4_K_M',
    supports_thinking=True,
)
LSR.LOCAL_SLM_MODELS['qwen3-0.6b-axo-v9-q4_k_m'] = v9_spec
rt = LocalSlmRuntime()
out_paths = {{}}
try:
    for tag, mkey in (('axov7_q4km', FINETUNED_LOCAL_SLM_MODEL_KEY), ('axov9_q4km', 'qwen3-0.6b-axo-v9-q4_k_m')):
        preds = {{}}
        for r in val_rows:
            ctx = build_compact_clause_context(r['canonical_text'])
            msgs = _build_compact_clause_messages(ctx)
            g = build_compact_grammar_for_context(ctx, closure_mode=V9_CLOSURE_MODE)
            inf = rt.chat_completion_json(messages=msgs, grammar=g, cache_prompt=True, model_key=mkey, ctx_size=2048, max_tokens=256)
            preds[r['sample_id']] = inf.raw_content
        pp = Path(r'{eval_dir}') / f'val_preds_{{tag}}.json'
        pp.write_text(json.dumps(preds, indent=2, ensure_ascii=False) + '\\n', encoding='utf-8')
        out_paths[tag] = str(pp)
finally:
    rt.shutdown()
Path(r'{gguf_cmp_path}').write_text(json.dumps(out_paths), encoding='utf-8')
"""
    env = dict(os.environ, ALLOW_LIVE_AI="0", GEMINI_API_KEY="")
    subprocess.run([str(BACKEND_PY), "-c", eval_code], check=True, env=env)
    gguf_paths = json.loads(gguf_cmp_path.read_text(encoding="utf-8"))

    sc_gguf: dict[str, Any] = {}
    for tag, pp in gguf_paths.items():
        sp = eval_dir / f"val_score_{tag}.json"
        subprocess.run([str(BACKEND_PY), str(SCORE_SCRIPT), "--val-jsonl", str(val_jsonl), "--preds-json", pp, "--out-json", str(sp)], check=True, env=env)
        sc_gguf[tag] = json.loads(sp.read_text(encoding="utf-8"))

    v9_q4_sc = sc_gguf["axov9_q4km"]
    v7_q4_sc = sc_gguf["axov7_q4km"]
    promoted = bool(
        v9_q4_sc["wrong_served_count"] == 0
        and v9_q4_sc["overall_correct"] > v7_q4_sc["overall_correct"]
        and v9_q4_sc["positives_oracle_exact"] >= v7_q4_sc["positives_oracle_exact"]
    )

    run_meta = {
        "schema": "slm-v9-training-run/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "external_ai_calls": 0,
        "hardware": {"gpu_name": torch.cuda.get_device_name(0), "torch": torch.__version__, "cuda": torch.version.cuda},
        "dataset": {"train_count": len(train_items), "val_count": len(val_items)},
        "model_params": {"base_repo": BASE_HF_REPO, "base_revision": BASE_HF_REV, "trainable_params": trainable_params, "all_params": all_params},
        "epoch_history": epoch_history,
        "selected_epoch": best_epoch,
        "peak_cuda_memory_mib": peak_mib,
        "training_wall_time_s": train_wall,
        "frozen_v7_sha256_unchanged": EXPECTED_V7_SHA,
        "frozen_orig_sha256_unchanged": EXPECTED_ORIG_SHA,
    }
    (OUT_DIR / "SLM_V9_TRAINING_RUN.json").write_text(json.dumps(run_meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    quant_cmp = {
        "schema": "slm-v9-quantization-comparison/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "val_dataset": str(val_jsonl),
        "q4_k_m_gguf": {"path": str(Q4_GGUF_PATH), "size_bytes": q4_size, "sha256": q4_sha},
        "models": {
            "axov7_q4km_baseline_under_v9_closure": {k: v for k, v in v7_q4_sc.items() if k != "sample_results"},
            "axov9_merged_fp16_hf": {k: v for k, v in sc_fp16.items() if k != "sample_results"},
            "axov9_q4km_gguf": {k: v for k, v in v9_q4_sc.items() if k != "sample_results"},
        },
        "promotion_gate_passed": promoted,
        "decision": "PROMOTE_AXOV9_Q4_K_M_AS_V9_LOCAL_MODEL" if promoted else "KEEP_AXOV7_Q4_K_M",
    }
    (OUT_DIR / "SLM_V9_QUANTIZATION_COMPARISON.json").write_text(json.dumps(quant_cmp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(quant_cmp["models"], indent=2))
    print(f"[TRAIN V9 DONE] promoted={promoted} sha256={q4_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
