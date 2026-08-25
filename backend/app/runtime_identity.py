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


def _bam(x: str) -> str:
    """Băm nội dung, chuẩn hoá CRLF→LF.

    Bắt buộc: file skill nằm trên bind mount từ host Windows, nên Git đổi cách
    xuống dòng khi chạm file. Không chuẩn hoá thì vân tay lệch giữa host và
    container **mà nội dung không đổi một chữ** — một báo động giả, và báo động
    giả là cách nhanh nhất để một cổng bị tắt.
    """
    return hashlib.sha256(
        x.replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()


def skill_fingerprint() -> dict:
    """Vân tay prompt — ĐO THỨ TIẾN TRÌNH ĐANG GIỮ, không phải thứ trên đĩa.

    ─── VÌ SAO PHÂN BIỆT NÀY LÀ TOÀN BỘ GIÁ TRỊ CỦA HÀM ────────────────────

    `gemini.load_skill()` cache nội dung `.md` **trong tiến trình**. Sửa một
    prompt rồi gửi đề mà quên restart thì backend vẫn gửi cho LLM bản CŨ, và
    không gì báo. `runtime_doctor` trước bản này chỉ *cảnh báo bằng lời* về ca
    ấy — nó so `git_sha`, `CACHE_VERSION`, catalog hash, và cả ba đều KHỚP khi
    prompt cũ đang được dùng, vì cả ba đều không đọc file `.md` nào.

    Nếu hàm này đọc lại file trên đĩa để băm, nó sẽ báo "khớp" trong đúng cái ca
    nó sinh ra để bắt. Nên:

        tren_dia    băm MỌI file `skills/*.md` hiện có
        da_nap      băm nội dung `_skill_cache` — thứ THẬT SỰ gửi đi
        cu          skill nào đã nạp mà khác đĩa  ⇒ CẦN RESTART

    `da_nap` rỗng ở một tiến trình vừa khởi động là ĐÚNG, không phải lỗi: chưa
    lượt nào chạy thì chưa prompt nào bị giữ, và khi ấy không có gì cũ được.

    `grammar_card` đi kèm vì nó cũng là bề mặt prompt: nó SINH TỪ `contract.py`
    và ghép vào user message, nên đổi một model Pydantic là đổi thứ LLM đọc —
    mà không file `.md` nào bị sửa. Đó là ca dễ quên nhất.
    """
    from app.ai import gemini

    tren_dia = {
        f.stem: _bam(f.read_text(encoding="utf-8"))
        for f in sorted(gemini.SKILLS_DIR.glob("*.md"))
    }
    da_nap = {ten: _bam(noi_dung)
              for ten, noi_dung in sorted(gemini._skill_cache.items())}
    cu = sorted(t for t, h in da_nap.items() if tren_dia.get(t) != h)

    try:
        from app.simulation.semantic_program.grammar_card import grammar_card

        the = _bam(grammar_card())
    except Exception:  # noqa: BLE001 — chẩn đoán không được giết tiến trình
        the = "unavailable"

    return {
        "tren_dia": tren_dia,
        "da_nap": da_nap,
        "cu": cu,
        "grammar_card": the,
        # Một con số để so nhanh. KHÔNG dùng nó thay `cu`: hai vân tay tổng thể
        # khớp nhau vẫn có thể che một skill đã nạp bị cũ, vì `da_nap` là tập con.
        "tong": _bam(json.dumps(tren_dia, sort_keys=True)),
    }


def runtime_identity() -> dict:
    """Danh tính runtime máy-đọc. `git_sha`/`build_timestamp` được BAKE lúc build
    image (build-arg → env); ngoài Docker thì báo "unknown" trung thực thay vì
    đoán — doctor sẽ xử lý riêng trường hợp đó."""
    # Nhập muộn: main.py import module này, tránh vòng import.
    from app.main import CACHE_VERSION, semantic_route_mode

    ai_targets = _ai_reachable()
    return {
        "git_sha": os.getenv("ALGOSIM_GIT_SHA", "unknown"),
        "build_timestamp": os.getenv("ALGOSIM_BUILD_TIME", "unknown"),
        "cache_version": CACHE_VERSION,
        "family_count": len(FamilyId),
        "target_count": len(CATALOG),
        "ai_reachable_target_count": len(ai_targets),
        "stable_catalog_hash": stable_catalog_hash(),
        # Vân tay PROMPT. Ba trường trước đó (`git_sha`, `cache_version`,
        # `stable_catalog_hash`) đều KHỚP khi một prompt cũ đang được gửi đi,
        # vì không trường nào trong chúng đọc một file `.md`.
        "skills": skill_fingerprint(),
        # ─── CỜ VẬN HÀNH — KHÔNG phải danh tính mã, nhưng quyết định HÀNH VI ──
        #
        # `runtime_doctor` từng báo PASS trọn vẹn trong khi `SEMANTIC_ROUTE_MODE`
        # là `off`, tức route sinh KHÔNG CHẠY và mọi đề hình học rơi xuống
        # classifier. Mã khớp từng bit, hành vi thì khác hẳn — và "PASS" đọc
        # thành "mọi thứ đúng".
        #
        # Đo được 2026-08-25: một lượt `docker compose up -d --build` không kèm
        # env kéo cờ về mặc định `off` mà không gì báo. Chúng phải HIỆN RA.
        # Doctor không phán chúng đúng/sai — `off` là lựa chọn hợp lệ cho bản
        # chạy thật — nhưng người đọc phải thấy, và `--doi-mode` cho phép khai
        # kỳ vọng khi lượt này là một lượt ĐO.
        "semantic_route_mode": semantic_route_mode(),
        "semantic_telemetry": os.getenv("SEMANTIC_TELEMETRY", "0"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "dev_reload": os.getenv("DEV_RELOAD", "0"),
        "registered_target_ids": sorted(CATALOG),
        "registered_ai_reachable_ids": ai_targets,
        # executor_id là danh tính engine FE mà target trỏ tới (contract M14 §C1)
        "registered_executor_ids": sorted({s.executor_id for s in CATALOG.values()}),
        # renderer = domain FE chịu trách nhiệm vẽ (một domain có thể nhiều target)
        "registered_renderer_ids": sorted({s.domain for s in CATALOG.values()}),
        "family_ids": sorted(f.value for f in FamilyId),
        "selector_tokens": sorted(s.selector_token for s in FAMILY_SELECTORS.values()),
    }
