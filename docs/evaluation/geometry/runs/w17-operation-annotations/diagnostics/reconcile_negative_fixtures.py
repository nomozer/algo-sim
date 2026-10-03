# -*- coding: utf-8 -*-
"""W17 Phase 2 — đối soát MỌI fixture âm: đề · chương trình/hợp đồng · envelope → loại nguyên nhân.

Câu hỏi của mỗi hàng: *lời từ chối này do chính dữ kiện của đề, hay do khâu dựng/bộ chạy?* Loại:
  missing_data                     — đề thiếu dữ kiện mà chương trình dùng (GIVEN bị gỡ khỏi đề);
  contradictory_or_degenerate_data — đề GHI một dữ kiện suy biến/mâu thuẫn (AB = 0, mặt phẳng ngoài khối);
  construction_mismatch            — đề đúng, phép dựng lệch thực thể đề nói (A′);
  runner_injected_wrong_program    — đề đúng, bộ chạy tiêm hợp đồng/chương trình sai;
  unknown_system_error             — không thuộc bốn loại trên.
`expected_cause` là nguyên nhân §15.3 mà loại ấy PHẢI cho (kèm ngoại lệ đã đăng ký); hàng lệch được
ghi `MISMATCH`, không được sửa cho khớp.

Sinh lại fixture bằng chính bộ sinh sản phẩm (`backend/scripts/generate_generic_tier_a_fixtures.py`)
vào thư mục tạm, 0 lượt gọi model. Fixture W16 (bất biến) được đọc nguyên trạng để truy ảnh lập phương.

Chạy từ backend/:
  .venv/Scripts/python.exe ../docs/evaluation/geometry/runs/w17-operation-annotations/diagnostics/reconcile_negative_fixtures.py --tmp <thư mục tạm>
Không ghi đè: tệp kết quả đã có thì dừng.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

DIAG = Path(__file__).resolve().parent
ROOT = DIAG.parents[5]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.learner_messages import attach_learner_reason  # noqa: E402
from app.simulation.semantic_program.validator import validate_semantic_program  # noqa: E402
from scripts import generate_generic_tier_a_fixtures as GEN  # noqa: E402

W16_CUBE = ROOT / "docs/evaluation/geometry/runs/w16-premerge-closure/inputs/fixtures/cube_negative.json"
TRUONG = ("status", "stage_reached", "error_code", "reason_code", "reason_subjects", "refusal_cause",
          "learner_reason")
BAO_SUA_DE = ("diễn đạt lại", "kiểm tra lại đề", "đối chiếu lại các số liệu trong đề", "sửa đề")


def _loai(ten: str, env: dict) -> tuple[str, str, str]:
    """→ (loại, nguyên nhân phải có, căn cứ) theo CÁCH fixture được dựng (bộ sinh), không theo envelope."""
    if ten.endswith("_system_cause.json"):
        return ("runner_injected_wrong_program", "CONSTRUCTION",
                "đề hợp lệ (cạnh bằng 4, V = 64); chỉ hợp đồng mang AB = 0 (`_tiem_ab_bang_0`)")
    if ten == "cross_section_negative.json":
        return ("contradictory_or_degenerate_data", "SOURCE",
                "đề ghi (α): z = 9 — mặt phẳng của đề nằm ngoài khối (kernel PLANE_DOES_NOT_CUT)")
    if ten.endswith("_negative.json"):
        return ("contradictory_or_degenerate_data", "SOURCE",
                "đề GHI độ dài ≤ 0 (`_zero_ab`: AB = 0 / cạnh bằng 0), hợp đồng theo đề")
    if ten.endswith("_ungrounded.json"):
        return ("missing_data", "SOURCE", "một GIVEN bị gỡ khỏi đề; analyze giả vẫn khai nó")
    if ten.endswith("_assumption.json"):
        if env.get("reason_code") == "ASSUMPTION_INVARIANCE_UNPROVEN":
            return ("missing_data", "UNKNOWN",
                    "đề mất dữ kiện, chương trình đặt bằng giả định; cổng không phân biệt được 'đề thiếu' với "
                    "'đề nói theo lối hệ chưa đọc' ⇒ UNKNOWN (§15.3, giữ lời W15)")
        return ("missing_data", "SOURCE", "đề mất một kích thước; chương trình giữ nó bằng bố cục")
    return ("unknown_system_error", "UNKNOWN", "không thuộc dạng nào của bộ sinh")


def _hang(ten: str, text: str, env: dict, loai: str, ky_vong: str, can_cu: str) -> dict:
    thuc = env.get("refusal_cause")
    loi = env.get("learner_reason") or ""
    return {"fixture": ten, "category": loai, "basis": can_cu, "problem_text": text,
            "envelope": {k: env.get(k) for k in TRUONG},
            "expected_cause": ky_vong, "actual_cause": thuc,
            "verdict": "MATCH" if thuc == ky_vong else "MISMATCH",
            "tells_learner_to_fix_text": any(c in loi for c in BAO_SUA_DE)}


def _a_phay() -> dict:
    from tests.geometry import test_assumption_certificate as AC

    contract, program = AC.PHEP_DUNG_SAI["O1_cat_bang_alpha_khi_de_noi_beta"]()
    spec = validate_semantic_program(program).spec
    env = attach_learner_reason(asyncio.run(GEN._run_frozen_program(contract.problem_text, contract, spec)))
    return _hang("A_prime_O1 (W17 corpus, frozen program)", contract.problem_text, env, "construction_mismatch",
                 "CONSTRUCTION", "đề nói (β) cắt khối; chương trình cắt bằng (α)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmp", type=Path, required=True)
    args = ap.parse_args()
    sha = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], capture_output=True, text=True,
                         cwd=ROOT).stdout.strip()
    ra = DIAG / f"NEGATIVE_FIXTURE_RECONCILIATION_{sha}.json"
    if ra.exists():
        raise SystemExit(f"{ra.name} đã có — không ghi đè")
    sys.argv = ["generate_generic_tier_a_fixtures", "--out", str(args.tmp)]
    GEN.main()
    rows = []
    for p in sorted((args.tmp / "fixtures").glob("*.json")):
        f = json.loads(p.read_text(encoding="utf-8"))
        env = f["envelope"]
        if env.get("status") != "unsupported":
            continue
        rows.append(_hang(p.name, f["problem_text"], env, *_loai(p.name, env)))
    rows.append(_a_phay())
    w16 = json.loads(W16_CUBE.read_text(encoding="utf-8"))
    lich_su = {"fixture": str(W16_CUBE.relative_to(ROOT)).replace("\\", "/"),
               "category": "runner_injected_wrong_program",
               "basis": "W16 `_zero_ab` chỉ thay chuỗi 'AB = 3' — đề lập phương ghi 'cạnh bằng 4' nên KHÔNG đổi "
                        "(đề hợp lệ, V = 64) trong khi hợp đồng mang AB = 0; sản phẩm từ chối đúng hợp đồng, nhưng "
                        "fixture được ghi là 'đề âm' và lời học sinh bảo diễn đạt lại đề",
               "problem_text": w16["problem_text"], "envelope": {k: w16["envelope"].get(k) for k in TRUONG},
               "expected_cause": "CONSTRUCTION", "actual_cause": w16["envelope"].get("refusal_cause"),
               "verdict": "HISTORICAL_DEFECT (W16 artifact, immutable; corrected in W17 by `cube_negative` "
                          "'cạnh bằng 0' + `cube_system_cause`)",
               "tells_learner_to_fix_text": any(c in (w16["envelope"].get("learner_reason") or "")
                                                for c in BAO_SUA_DE)}
    dem: dict[str, int] = {}
    for r in rows:
        dem[r["category"]] = dem.get(r["category"], 0) + 1
    out = {"probe": "W17_NEGATIVE_FIXTURE_RECONCILIATION", "measured_at_commit": sha, "model_calls": 0,
           "categories": dem, "mismatches": [r["fixture"] for r in rows if r["verdict"] != "MATCH"],
           "construction_or_unknown_rows_telling_learner_to_fix_text": [
               r["fixture"] for r in rows if r["expected_cause"] != "SOURCE" and r["tells_learner_to_fix_text"]],
           "rows": rows, "historical": [lich_su]}
    ra.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    for r in rows:
        print(f"{r['verdict']:8} {r['category']:34} {r['expected_cause']:12} {r['actual_cause']!s:12} {r['fixture']}")
    print("categories:", dem, "| mismatches:", out["mismatches"],
          "| non-SOURCE rows telling to fix text:", out["construction_or_unknown_rows_telling_learner_to_fix_text"])
    print("wrote", ra.name)


if __name__ == "__main__":
    main()
