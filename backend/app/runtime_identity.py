# -*- coding: utf-8 -*-
"""M17-RC1 §A — DANH TÍNH RUNTIME máy-đọc (chống "container chạy code cũ").

Vì sao cần: container backend từng chạy CACHE_VERSION "7" (thời M10) suốt nhiều
milestone mà KHÔNG gì báo — người dùng chỉ phát hiện khi thử một đề duyệt cây và
nó rơi xuống generic. Không có cách nào biết "runtime ≠ source" ngoài việc đọc
lỗi lạ. Module này phơi bày danh tính runtime để `runtime_doctor` so khớp.

Nguyên tắc: MỌI giá trị DẪN XUẤT từ registry sống — KHÔNG hard-code target/
family nào (thêm target thứ 20 tự vào hash, không phải sửa file này).
"""

from __future__ import annotations

import hashlib
import json
import os

from app.simulation.catalog import CATALOG, llm_choices
from app.simulation.descriptor import FamilyId, ReachabilityLevel
from app.simulation.families import FAMILY_SELECTORS


def _ai_reachable() -> list[str]:
    return sorted(
        sid for sid, spec in CATALOG.items()
        if ReachabilityLevel.AI_REACHABLE_PUBLIC in spec.reachability
    )


def catalog_fingerprint() -> dict:
    """Ảnh chụp NỘI DUNG catalog dùng để băm — ổn định, không phụ thuộc thứ tự
    dict hay chi tiết trình bày. Đổi bất kỳ target/family/mechanism/contract nào
    đều làm hash đổi."""
    targets = {}
    for sid in sorted(CATALOG):
        spec = CATALOG[sid]
        targets[sid] = {
            "domain": spec.domain,
            "executor_id": spec.executor_id,
            "config_contract_version": spec.config_contract_version,
            "reachability": sorted(r.value for r in spec.reachability),
            "families": sorted({m.family_id.value for m in spec.family_memberships}),
            "owned_mechanisms": sorted(
                {m for mb in spec.family_memberships for m in mb.owned_mechanisms}
            ),
        }
    selectors = {
        fid: {
            "token": sel.selector_token,
            "version": sel.family_spec_version,
            "owned": sorted(sel.owned_mechanisms),
            "variants": sorted(v.variant_id for v in sel.variants),
        }
        for fid, sel in sorted(FAMILY_SELECTORS.items())
    }
    return {
        "families": sorted(f.value for f in FamilyId),
        "targets": targets,
        "selectors": selectors,
        "llm_choices": sorted(llm_choices()),
    }


def stable_catalog_hash() -> str:
    payload = json.dumps(catalog_fingerprint(), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def runtime_identity() -> dict:
    """Danh tính runtime máy-đọc. `git_sha`/`build_timestamp` được BAKE lúc build
    image (build-arg → env); ngoài Docker thì báo "unknown" trung thực thay vì
    đoán — doctor sẽ xử lý riêng trường hợp đó."""
    # Nhập muộn: main.py import module này, tránh vòng import.
    from app.main import CACHE_VERSION

    ai_targets = _ai_reachable()
    return {
        "git_sha": os.getenv("ALGOSIM_GIT_SHA", "unknown"),
        "build_timestamp": os.getenv("ALGOSIM_BUILD_TIME", "unknown"),
        "cache_version": CACHE_VERSION,
        "family_count": len(FamilyId),
        "target_count": len(CATALOG),
        "ai_reachable_target_count": len(ai_targets),
        "stable_catalog_hash": stable_catalog_hash(),
        "registered_target_ids": sorted(CATALOG),
        "registered_ai_reachable_ids": ai_targets,
        # executor_id là danh tính engine FE mà target trỏ tới (contract M14 §C1)
        "registered_executor_ids": sorted({s.executor_id for s in CATALOG.values()}),
        # renderer = domain FE chịu trách nhiệm vẽ (một domain có thể nhiều target)
        "registered_renderer_ids": sorted({s.domain for s in CATALOG.values()}),
        "family_ids": sorted(f.value for f in FamilyId),
        "selector_tokens": sorted(s.selector_token for s in FAMILY_SELECTORS.values()),
    }
