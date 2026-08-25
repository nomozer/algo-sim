# -*- coding: utf-8 -*-
"""M17-RC1 §A — RUNTIME DOCTOR: source ↔ container có khớp không?

BỆNH ĐÃ CHÁY: container backend chạy `CACHE_VERSION "7"` (thời M10) suốt nhiều
milestone. Mọi năng lực từ M14 trở đi (selector sắp xếp, 4 target Wave 1,
tree_traversal Wave 2A) KHÔNG tồn tại ở runtime, nhưng không gì báo — người
dùng chỉ phát hiện khi một đề duyệt cây rơi xuống generic và validator DSL ném
lỗi khó hiểu. Công cụ này biến "im lặng nhiều tháng" thành "đỏ trong 2 giây".

Chạy:
    python scripts/runtime_doctor.py                     # mặc định :8000
    python scripts/runtime_doctor.py --url http://localhost:8000
    python scripts/runtime_doctor.py --json out.json     # ghi artifact

Thoát 0 = khớp; khác 0 = có mismatch (in hướng dẫn sửa).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.runtime_identity import runtime_identity  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

# Phân loại lỗi (đóng) — mỗi mã kèm cách sửa.
FIX_REBUILD = (
    "docker compose up -d --build --force-recreate backend\n"
    "      (kèm danh tính build:  GIT_SHA=$(git rev-parse HEAD) "
    "BUILD_TIME=$(date -u +%FT%TZ) docker compose up -d --build --force-recreate backend)"
)
FIX_RESTART_SKILL = (
    "Nếu chỉ sửa prompt trong backend/app/ai/skills/*.md: prompt được CACHE THEO "
    "TIẾN TRÌNH → phải restart container/process, không đủ nếu chỉ lưu file."
)
FIX_PROMPT = (
    "docker compose restart backend\n"
    "      (prompt cache theo TIẾN TRÌNH — lưu file là chưa đủ, và ba phép so "
    "phía trên đều KHỚP trong đúng ca này)"
)
CATEGORY_FIX = {
    "RUNTIME_STALE_IMAGE": FIX_REBUILD,
    "CACHE_VERSION_MISMATCH": FIX_REBUILD,
    "CATALOG_HASH_MISMATCH": FIX_REBUILD + "\n      " + FIX_RESTART_SKILL,
    "MISSING_RUNTIME_FAMILY": FIX_REBUILD,
    "MISSING_RUNTIME_TARGET": FIX_REBUILD,
    "MISSING_RUNTIME_EXECUTOR": FIX_REBUILD,
    "MISSING_RUNTIME_RENDERER": FIX_REBUILD,
    "PROMPT_STALE_IN_PROCESS": FIX_PROMPT,
    "SKILL_FILE_MISMATCH": FIX_REBUILD,
    "GRAMMAR_CARD_MISMATCH": FIX_REBUILD,
    "PROMPT_FINGERPRINT_MISSING": FIX_PROMPT,
}


def _source_git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, cwd=ROOT
        ).stdout.strip()
    except Exception:
        return "unknown"


def fetch_runtime(url: str) -> tuple[dict | None, str | None]:
    endpoint = url.rstrip("/") + "/api/diagnostics/runtime"
    try:
        with urllib.request.urlopen(endpoint, timeout=10) as r:
            return json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, (
                "Endpoint /api/diagnostics/runtime KHÔNG tồn tại (404) — gần như chắc "
                "chắn container đang chạy image CŨ (trước M17-RC1)."
            )
        return None, f"HTTP {e.code} khi gọi {endpoint}"
    except Exception as err:
        return None, f"Không gọi được {endpoint}: {err}"


def diagnose(source: dict, runtime: dict, source_sha: str) -> list[dict]:
    """So sánh source ↔ runtime. Trả danh sách finding (rỗng = khớp)."""
    findings: list[dict] = []

    def add(category: str, detail: str, expected=None, actual=None):
        findings.append({
            "category": category, "detail": detail,
            "expected": expected, "actual": actual,
            "fix": CATEGORY_FIX.get(category, FIX_REBUILD),
        })

    # 1. Git SHA (chỉ so khi CẢ HAI biết — không bịa kết luận từ "unknown")
    rt_sha = runtime.get("git_sha", "unknown")
    if rt_sha != "unknown" and source_sha != "unknown" and rt_sha != source_sha:
        add("RUNTIME_STALE_IMAGE",
            "Image được build từ commit khác với source hiện tại.",
            source_sha, rt_sha)

    # 2. CACHE_VERSION
    if source["cache_version"] != runtime.get("cache_version"):
        add("CACHE_VERSION_MISMATCH",
            "CACHE_VERSION ở runtime khác source — container chắc chắn chạy code cũ.",
            source["cache_version"], runtime.get("cache_version"))

    # 3. Catalog hash (bao trùm mọi thay đổi target/family/mechanism/contract)
    if source["stable_catalog_hash"] != runtime.get("stable_catalog_hash"):
        add("CATALOG_HASH_MISMATCH",
            "Nội dung catalog ở runtime khác source (target/family/cơ chế/hợp đồng).",
            source["stable_catalog_hash"][:16] + "…",
            str(runtime.get("stable_catalog_hash"))[:16] + "…")

    # 3b. VÂN TAY PROMPT — ba phép so phía trên đều KHỚP khi một prompt cũ đang
    #     được gửi đi, vì không phép nào trong chúng đọc một file `.md`.
    rt_sk = runtime.get("skills") or {}
    src_sk = source.get("skills") or {}
    if src_sk and not rt_sk:
        # Runtime KHÔNG khai vân tay prompt trong khi source có ⇒ tiến trình đang
        # chạy một bản `runtime_identity` cũ hơn source. Bỏ qua im lặng ở đây là
        # đúng cái lỗi cả module này sinh ra để chặn: một cổng không đo được thì
        # phải nói "không đo được", không được nói "khớp".
        add("PROMPT_FINGERPRINT_MISSING",
            "Runtime không khai vân tay prompt — tiến trình chạy bản cũ hơn "
            "source, nên KHÔNG kiểm được prompt.",
            "có vân tay", "không có")
    elif rt_sk and src_sk:
        # (a) TIẾN TRÌNH đang giữ bản cũ — ca nguy hiểm nhất, vì file trên đĩa
        #     đã đúng nên mọi phép so theo đĩa đều nói "khớp".
        if cu := rt_sk.get("cu"):
            add("PROMPT_STALE_IN_PROCESS",
                f"Tiến trình đang giữ prompt CŨ cho: {', '.join(cu)} — "
                "LLM đang đọc bản khác với file trên đĩa.",
                "prompt trên đĩa", "bản đã cache trong tiến trình")

        # (b) File skill trong image khác file trong source.
        sd, rd = src_sk.get("tren_dia", {}), rt_sk.get("tren_dia", {})
        lech = sorted(t for t in set(sd) | set(rd) if sd.get(t) != rd.get(t))
        if lech:
            add("SKILL_FILE_MISMATCH",
                f"File skill ở runtime khác source: {', '.join(lech)}",
                f"{len(sd)} skill", f"{len(rd)} skill")

        # (c) Thẻ văn phạm SINH TỪ `contract.py` và ghép vào user message, nên
        #     đổi một model Pydantic là đổi thứ LLM đọc — mà không file `.md`
        #     nào bị sửa. Ca dễ quên nhất.
        if src_sk.get("grammar_card") != rt_sk.get("grammar_card"):
            add("GRAMMAR_CARD_MISMATCH",
                "Thẻ văn phạm ở runtime khác source (đổi ở contract.py?).",
                str(src_sk.get("grammar_card"))[:16] + "…",
                str(rt_sk.get("grammar_card"))[:16] + "…")

    # 4–7. Thiếu THÀNH PHẦN cụ thể — chỉ đúng tên cái thiếu, không đoán
    for key, category, label in (
        ("family_ids", "MISSING_RUNTIME_FAMILY", "family"),
        ("registered_target_ids", "MISSING_RUNTIME_TARGET", "target"),
        ("registered_executor_ids", "MISSING_RUNTIME_EXECUTOR", "executor"),
        ("registered_renderer_ids", "MISSING_RUNTIME_RENDERER", "renderer"),
    ):
        missing = sorted(set(source.get(key, [])) - set(runtime.get(key, [])))
        if missing:
            add(category,
                f"Runtime THIẾU {len(missing)} {label}: {', '.join(missing)}",
                source.get(key), runtime.get(key))
    return findings


def main() -> int:
    p = argparse.ArgumentParser(description="So khớp danh tính source ↔ runtime.")
    p.add_argument("--url", default="http://localhost:8000")
    p.add_argument("--json", default=None, help="Ghi artifact runtime_identity.json")
    p.add_argument("--doi-mode", default=None, choices=("off", "shadow", "serve"),
                   help="KHAI KỲ VỌNG cho SEMANTIC_ROUTE_MODE. Lệch ⇒ FAIL. "
                        "Dùng trước một lượt ĐO; không khai thì chỉ in ra.")
    p.add_argument("--doi-model", default=None,
                   help="KHAI KỲ VỌNG cho GEMINI_MODEL. Lệch ⇒ FAIL.")
    args = p.parse_args()

    source = runtime_identity()
    source_sha = _source_git_sha()
    source["git_sha"] = source_sha  # source luôn biết SHA của chính nó

    runtime, err = fetch_runtime(args.url)
    print("=== RUNTIME DOCTOR (M17-RC1 §A) ===")
    _sk = source.get("skills") or {}
    print(f"source : sha={source_sha[:12]} cache={source['cache_version']} "
          f"family={source['family_count']} target={source['target_count']} "
          f"hash={source['stable_catalog_hash'][:12]} "
          f"skill={len(_sk.get('tren_dia', {}))}/{str(_sk.get('tong'))[:8]} "
          f"card={str(_sk.get('grammar_card'))[:8]}")

    if runtime is None:
        print(f"runtime: KHÔNG ĐỌC ĐƯỢC — {err}")
        print("\nKẾT LUẬN: RUNTIME_UNREACHABLE_OR_STALE")
        print(f"  Sửa: {FIX_REBUILD}")
        payload = {"source": source, "runtime": None, "error": err,
                   "findings": [{"category": "RUNTIME_STALE_IMAGE", "detail": err,
                                 "fix": FIX_REBUILD}], "ok": False}
    else:
        _rk = runtime.get("skills") or {}
        print(f"runtime: sha={str(runtime.get('git_sha'))[:12]} "
              f"cache={runtime.get('cache_version')} "
              f"family={runtime.get('family_count')} target={runtime.get('target_count')} "
              f"hash={str(runtime.get('stable_catalog_hash'))[:12]} "
              f"skill={len(_rk.get('tren_dia', {}))}/{str(_rk.get('tong'))[:8]} "
              f"card={str(_rk.get('grammar_card'))[:8]}")
        # `da_nap` rỗng ở tiến trình vừa khởi động là ĐÚNG — chưa lượt nào chạy
        # thì chưa prompt nào bị giữ. Nói ra để không ai đọc nhầm thành "hỏng".
        print(f"         prompt đã nạp trong tiến trình: "
              f"{len(_rk.get('da_nap', {}))} · cũ: {_rk.get('cu') or 'không'}")
        # CỜ VẬN HÀNH — in RIÊNG một dòng, vì chúng không phải danh tính mã
        # nhưng quyết định hành vi. Doctor từng PASS trọn vẹn trong khi
        # `SEMANTIC_ROUTE_MODE=off`, tức route sinh không chạy.
        print(f"cờ     : route={runtime.get('semantic_route_mode')} "
              f"model={runtime.get('gemini_model')} "
              f"telemetry={runtime.get('semantic_telemetry')} "
              f"reload={runtime.get('dev_reload')}")
        findings = diagnose(source, runtime, source_sha)
        # Kỳ vọng vận hành: chỉ kiểm khi người chạy KHAI ra. Doctor không tự
        # phán `off` là sai — nó là lựa chọn hợp lệ cho bản chạy thật.
        for co, mong, ma in (
            ("semantic_route_mode", args.doi_mode, "ROUTE_MODE_MISMATCH"),
            ("gemini_model", args.doi_model, "MODEL_MISMATCH"),
        ):
            if mong is not None and runtime.get(co) != mong:
                findings.append({
                    "category": ma,
                    "detail": f"{co} ở runtime là {runtime.get(co)!r}, "
                              f"lượt này khai kỳ vọng {mong!r}.",
                    "expected": mong, "actual": runtime.get(co),
                    "fix": f"{co.upper()}={mong} docker compose up -d backend",
                })
        payload = {"source": source, "runtime": runtime, "findings": findings,
                   "ok": not findings}
        if not findings:
            print("\nKẾT LUẬN: PASS — runtime khớp source.")
        else:
            print(f"\nKẾT LUẬN: FAIL — {len(findings)} mismatch")
            for f in findings:
                print(f"\n  [{f['category']}] {f['detail']}")
                if f.get("expected") is not None and not isinstance(f["expected"], list):
                    print(f"      source : {f['expected']}")
                    print(f"      runtime: {f['actual']}")
                print(f"      Sửa: {f['fix']}")

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nArtifact: {args.json}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
