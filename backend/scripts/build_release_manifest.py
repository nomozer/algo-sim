# -*- coding: utf-8 -*-
"""Manifest RELEASE của bản dùng cho khoá luận. 0 lượt gọi model.

─── HAI DANH TÍNH, KHÔNG ĐƯỢC GỘP ──────────────────────────────────────────

Một bản release đóng băng sau lượt nghiệm thu cuối mang **hai** candidate khác
nhau, và gộp chúng là cách im lặng nhất để một con số của lượt đo cũ bị đọc như
số của mã hiện tại:

    historical_candidate  — hệ mà lượt live ĐÃ đo (`IDENTITY_LOCK.json`)
    current_candidate     — hệ đang được đóng gói lúc này

Cũng vậy với bằng chứng: `live_evidence` là artifact BẤT BIẾN của lượt live;
`replay_evidence` là thứ dựng lại được hôm nay, 0 lượt gọi. Chúng trả lời hai
câu khác nhau và không thay nhau được.

⚠️ Mọi băm ở đây **đọc từ nguồn**, không gõ tay. Một manifest chép tay là một
tài liệu sẽ trôi, và nó trôi đúng vào lúc không ai kiểm lại nữa.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
sys.path.insert(0, str(BE / "scripts"))
GOC = BE.parent
RA = GOC / "docs" / "evaluation" / "geometry" / "thesis-final-acceptance"
OUT_MAC_DINH = GOC / "docs" / "evaluation" / "geometry" / "final-system-release"


def _bam_tep(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _bam_thu_muc(d: Path, loc=lambda p: True) -> tuple[str, int]:
    """Băm CÂY tệp: tên tương đối + nội dung, sắp xếp ổn định."""
    h = hashlib.sha256()
    n = 0
    for p in sorted(x for x in d.rglob("*") if x.is_file() and loc(x)):
        h.update(p.relative_to(d).as_posix().encode("utf-8"))
        h.update(p.read_bytes())
        n += 1
    return h.hexdigest(), n


def _git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=GOC, capture_output=True,
                          text=True, encoding="utf-8").stdout.strip()


def dung_manifest() -> dict:
    from acceptance_integrity import moi_truong_hien_tai
    import freeze_evaluation_candidate as F
    import thesis_acceptance_corpus as C
    import app.main as M

    mt = moi_truong_hien_tai()
    hien_tai, so_file = F.measured_system_hash()
    lock = json.loads((RA / "IDENTITY_LOCK.json").read_text(encoding="utf-8"))
    khai_lech = json.loads(
        (GOC / "docs" / "evaluation" / "geometry"
         / "product-response-contract-alignment"
         / "CANDIDATE_DIVERGENCE.json").read_text(encoding="utf-8"))

    dist = GOC / "frontend" / "dist"
    fe_hash, fe_n = _bam_thu_muc(dist) if dist.exists() else ("KHONG_CO_BAN_DUNG", 0)

    # Hợp đồng API = lược đồ chương trình ngữ nghĩa + enum mã lỗi. Hai thứ này
    # quyết định hình dạng thứ frontend nhận, nên chúng là "API contract" thật.
    api = hashlib.sha256()
    api.update((GOC / "docs" / "schemas" / "semantic_program.schema.json").read_bytes())
    api.update((BE / "app" / "simulation" / "error_codes.py").read_bytes())

    corpus = json.loads((RA / "CORPUS.json").read_text(encoding="utf-8"))

    return {
        "release_name": "algosim-thesis-2026-09-09",
        "khai": "Bản đóng băng dùng cho khoá luận và demo. Đóng phát triển "
                "tính năng; mọi đề xuất mới thuộc mục Hướng phát triển.",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": _git("rev-parse", "HEAD"),
        "git_branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "working_tree_clean": _git("status", "--porcelain") == "",

        # ── HAI DANH TÍNH, ghi thành hai trường ──────────────────────────
        "candidate_hash": hien_tai,
        "candidate_file_count": so_file,
        "historical_candidate_hash": lock["CANDIDATE_HASH"],
        "candidate_diverged_from_final_acceptance": hien_tai != lock["CANDIDATE_HASH"],
        "candidate_divergence_declaration":
            "docs/evaluation/geometry/product-response-contract-alignment/"
            "CANDIDATE_DIVERGENCE.json",
        "candidate_divergence_reason": khai_lech.get("reason"),

        "cache_version": int(M.CACHE_VERSION),
        "model_facing_hashes": {
            "PROMPT_HASH": mt["components"]["prompts"],
            "GRAMMAR_CARD_HASH": mt["components"]["grammar_card"],
            "ANALYZE_SCHEMA_HASH": mt["components"]["analyze_schema"],
            "SYNTHESIS_SCHEMA_HASH": mt["components"]["synthesis_schema"],
            "CAPABILITY_HASH": mt["stable_capability_hash"],
        },
        "model_facing_changed_since_final_acceptance": {
            k: (mt_v != lock.get(k))
            for k, mt_v in (
                ("PROMPT_HASH", mt["components"]["prompts"]),
                ("GRAMMAR_CARD_HASH", mt["components"]["grammar_card"]),
                ("ANALYZE_SCHEMA_HASH", mt["components"]["analyze_schema"]),
                ("SYNTHESIS_SCHEMA_HASH", mt["components"]["synthesis_schema"]),
                ("CAPABILITY_HASH", mt["stable_capability_hash"]),
            )
        },
        "api_contract_hash": api.hexdigest(),
        "frontend_build_hash": fe_hash,
        "frontend_build_file_count": fe_n,

        "corpus_hash": C.CORPUS_HASH,
        "expected_results_hash": C.EXPECTED_RESULTS_HASH,
        "final_acceptance_run_id": "thesis-final-20260908T160224Z",

        # ── HAI LOẠI BẰNG CHỨNG, cũng không gộp ──────────────────────────
        "live_evidence": {
            "khai": "Artifact BẤT BIẾN của lượt live cuối. Mô tả candidate "
                    f"{lock['CANDIDATE_HASH'][:16]}…, KHÔNG mô tả mã hiện tại.",
            "path": "docs/evaluation/geometry/thesis-final-acceptance/",
            "positive_cases": len(corpus["positive_cases"]),
            "negative_cases": len(corpus["negative_cases"]),
        },
        "replay_evidence": {
            "khai": "Dựng lại được hôm nay trên mã hiện tại, 0 lượt gọi model.",
            "paths": [
                "docs/evaluation/geometry/product-ui-result-rendering/",
                "docs/evaluation/geometry/product-response-contract-alignment/",
                "docs/evaluation/geometry/final-system-release/",
            ],
        },

        "supported_scope": [
            "Khối đa diện: chóp, lăng trụ, hộp — kể cả đáy LÕM (thể tích chính xác)",
            "Mặt cầu và thiết diện tròn",
            "Hình trụ, hình nón — thể tích, diện tích xung quanh",
            "Thiết diện elip của trụ và của nón (phân xử conic hữu tỉ)",
            "Thiết diện qua ba điểm, giao tuyến, khoảng cách, góc",
            "Mặt phẳng cho bằng phương trình",
            "Số học CHÍNH XÁC trong ℚ(√, π) — không float trong miền hình học",
            "Từ chối CÓ CẤU TRÚC: giai đoạn dừng · loại · mã lỗi · lý do",
        ],
        "out_of_scope": [
            "Khối tròn xoay TỔNG QUÁT (cần tích phân ký hiệu; `Radical` không đóng)",
            "Khối ghép/bù cần boolean (không có thẩm quyền boolean; điều kiện TOÀN CỤC)",
            "Kéo–thả kiểu GeoGebra (liên tục — phá song ánh `frame k ⇔ trace[k]`)",
            "Miền ngoài hình học không gian (fail-closed tại `detect_domain`)",
        ],
        "known_limitations": [
            "STABILITY chưa đo (`ANALYZE_STABILITY = NOT_MEASURED_BY_SCOPE_DECISION`)",
            "DISPLAY_NAME 10/12 — `OPTIONAL_POLISH`, không sửa vì chạm candidate đăng ký",
            "`TARGET_BOUNDARY_PASS = 1/2` — `n1` dừng TRƯỚC cổng phủ nên không "
            "chứng minh được ranh giới định đo",
            "Năng lực SẢN PHẨM của khối cong vẫn `foundation_only` (n = 1)",
            "Cổng trình duyệt chạy trên Vite dev có ~13–25% phiên Chrome không tải "
            "nổi module (lỗi transport, KHÔNG phải sản phẩm); bản dựng sản phẩm "
            "đo 0/15 lỗi — xem `PAGE_BOOT_MEASUREMENT.json`",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(OUT_MAC_DINH))
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    mf = dung_manifest()

    # Băm mọi artifact của release + băm nguồn lượt live (phải BẤT BIẾN).
    mf["artifact_hashes"] = {
        "final_acceptance_source": {
            p.relative_to(GOC).as_posix(): _bam_tep(p)
            for p in sorted(RA.rglob("*")) if p.is_file()
        },
        "release": {
            p.relative_to(out).as_posix(): _bam_tep(p)
            for p in sorted(out.rglob("*")) if p.is_file()
            and p.name != "RELEASE_MANIFEST.json"
        },
    }

    # Kết quả test đọc từ artifact ĐÃ GHI, không gõ tay.
    tk: dict = {}
    for ten, p in (
        ("targeted_refusal_surface", out / "REPEAT_refusal-surface-AFTER.json"),
        ("targeted_refusal_surface_before", out / "REPEAT_refusal-surface-BEFORE.json"),
        ("browser_product_ui", out / "REPEAT_product-ui-rendering.json"),
        ("visual_oracle", out / "REPEAT_scene3d-world-oracles.json"),
        ("hidden_lines", out / "REPEAT_hidden-lines.json"),
    ):
        if p.exists():
            j = json.loads(p.read_text(encoding="utf-8"))
            tk[ten] = {k: j.get(k) for k in
                       ("EXECUTIONS", "ASSERTIONS_PER_EXECUTION", "PASS_COUNTS",
                        "FAIL_COUNTS", "RETRY_COUNTS", "LUOT_SACH_HOAN_TOAN",
                        "FLAKE_RATE")}
    mf["test_results"] = tk

    p = out / "RELEASE_MANIFEST.json"
    p.write_text(json.dumps(mf, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"release      : {mf['release_name']}")
    print(f"commit       : {mf['git_commit'][:12]} · cây sạch: {mf['working_tree_clean']}")
    print(f"candidate    : {mf['candidate_hash'][:16]}… ({mf['candidate_file_count']} file)")
    print(f"  lịch sử    : {mf['historical_candidate_hash'][:16]}… "
          f"(lệch: {mf['candidate_diverged_from_final_acceptance']})")
    print(f"cache_version: {mf['cache_version']}")
    print(f"frontend dist: {mf['frontend_build_hash'][:16]}… ({mf['frontend_build_file_count']} file)")
    print(f"api contract : {mf['api_contract_hash'][:16]}…")
    print(f"model-facing đổi: "
          f"{any(mf['model_facing_changed_since_final_acceptance'].values())}")
    print(f"ghi: {p.relative_to(GOC).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
