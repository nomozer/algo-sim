# -*- coding: utf-8 -*-
"""M17-RC1 §B — sinh ma trận catalog + báo cáo conformance.

Ma trận đọc TỪ REGISTRY (không viết tay danh sách target). Nếu chỉ được URL
runtime thì so thêm parity source↔runtime.

    python scripts/catalog_runtime_matrix.py --json <out.json> [--md <out.md>]
                                             [--url http://localhost:8000]
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.catalog_conformance import (  # noqa: E402
    build_matrix,
    mechanism_ownership,
    source_runtime_parity,
    target_conformance,
)
from app.runtime_identity import runtime_identity  # noqa: E402


def _runtime(url: str | None) -> dict | None:
    if not url:
        return None
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/api/diagnostics/runtime", timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def build_report(rows, conformance, ownership, parity) -> str:
    ok = not (conformance or ownership or parity)
    lines = [
        "# M17-RC1 §B — Catalog Runtime Conformance",
        "",
        "Ma trận **sinh từ registry** (`CATALOG` + `FAMILY_SELECTORS` +",
        "`AUTHENTICITY_CONTRACTS` + fixture audit) — KHÔNG viết tay danh sách target.",
        "",
        f"- Target AI-reachable: **{len(rows)}**",
        f"- Vi phạm conformance: **{len(conformance)}**",
        f"- Vi phạm ownership: **{len(ownership)}**",
        f"- Lệch source↔runtime: **{len(parity)}**",
        f"- Kết luận: **{'PASS' if ok else 'FAIL'}**",
        "",
        "| Target | Family | Variants | Validator | Executor | Renderer | analyze-exposed | fixture |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['target_id']}` | {', '.join(r['family_ids'])} | "
            f"{', '.join(r['supported_variants']) or '—'} | `{r['validator_id']}` | "
            f"`{r['executor_id']}` | {r['renderer_id']} | "
            f"{len(r['analyze_exposed_mechanisms'])} | {'✓' if r['has_audit_fixture'] else '✗'} |"
        )
    for title, items in (("Conformance", conformance), ("Ownership", ownership),
                         ("Source↔Runtime", parity)):
        lines += ["", f"## {title}", ""]
        lines.append("Không vi phạm." if not items
                     else "\n".join(f"- `{i.get('code')}` — {json.dumps(i, ensure_ascii=False)}"
                                    for i in items))
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", default=None)
    p.add_argument("--md", default=None)
    p.add_argument("--url", default=None, help="Có URL thì so parity source↔runtime")
    args = p.parse_args()

    rows = build_matrix()
    conformance = target_conformance(rows)
    ownership = mechanism_ownership()
    rt = _runtime(args.url)
    parity = source_runtime_parity(rt) if args.url else []

    payload = {
        "schema_version": "1", "run_label": "rc1-catalog-conformance",
        "source_identity": runtime_identity(),
        "target_count": len(rows),
        "matrix": rows,
        "violations": {
            "target_conformance": conformance,
            "mechanism_ownership": ownership,
            "source_runtime_parity": parity,
        },
        "ok": not (conformance or ownership or parity),
    }
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
        print(f"Artifact: {args.json}")
    if args.md:
        Path(args.md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.md).write_text(build_report(rows, conformance, ownership, parity),
                                 encoding="utf-8")
        print(f"Report:   {args.md}")

    print(f"Target: {len(rows)} · conformance {len(conformance)} · "
          f"ownership {len(ownership)} · parity {len(parity)} · "
          f"{'PASS' if payload['ok'] else 'FAIL'}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
