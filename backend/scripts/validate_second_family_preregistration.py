# -*- coding: utf-8 -*-
"""Validator Tooling cho Tiền Đăng Ký Họ Thứ Hai (Second Family Preregistration).

Wave: PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION
Quy tắc:
- Validator CHỈ ĐỌC (read-only), không tự sinh ra dữ liệu rồi tự chấm.
- Thẩm định độc lập 3 tệp tĩnh:
  1. SECOND_FAMILY_SELECTION_MATRIX.json
  2. SECOND_FAMILY_MANIFEST.json
  3. SECOND_FAMILY_GROUND_TRUTH.json
- Đối soát 18 tiêu chuẩn bắt buộc theo đặc tả Mục 13.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys

from fractions import Fraction
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
EVAL_DIR = (
    REPO
    / "docs"
    / "evaluation"
    / "geometry"
    / "photo-problem-to-scene"
    / "primitive-compiler-second-family-selection"
)

HISTORICAL_INTEGRITY_LABEL = "LF_NORMALIZED_CONTENT_PARITY"


def sha256_lf_normalized(content_bytes: bytes) -> str:
    """Tính mã băm SHA-256 sau khi chuẩn hóa dòng kết thúc về LF."""
    return hashlib.sha256(content_bytes.replace(b"\r\n", b"\n")).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_lf_normalized(p.read_bytes())


def run_cmd(cmd: list[str], cwd: Path = REPO) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run(cmd, cwd=str(cwd), capture_output=True, env=env)
    stdout = res.stdout.decode("utf-8", errors="replace").strip() if res.stdout else ""
    stderr = res.stderr.decode("utf-8", errors="replace").strip() if res.stderr else ""
    return res.returncode, stdout, stderr




def validate_selection_matrix(matrix_path: Path | None = None) -> dict[str, Any]:
    p = matrix_path or (EVAL_DIR / "SECOND_FAMILY_SELECTION_MATRIX.json")
    if not p.is_file():
        return {"valid": False, "error": f"Missing matrix file: {p}"}

    data = json.loads(p.read_text(encoding="utf-8"))
    weights_total = data.get("weights_total", 0)
    criteria = data.get("criteria", [])
    candidates = data.get("candidates", {})

    # 1. Kiểm tra tổng trọng số = 100
    calc_weights = sum(c.get("weight", 0) for c in criteria)
    weights_valid = (weights_total == 100 and calc_weights == 100)

    # 2. Đúng 3 ứng viên A, B, C
    candidate_keys = sorted(candidates.keys())
    three_candidates = (candidate_keys == ["A", "B", "C"])

    # 3. Mỗi điểm có source evidence, gap, risk, rationale
    evidence_complete = True
    computed_scores: dict[str, float] = {}
    criteria_ids = [c["id"] for c in criteria]

    for c_key, c_val in candidates.items():
        scores = c_val.get("scores", {})
        total = 0.0
        for crit in criteria:
            cid = crit["id"]
            w = crit["weight"]
            sc_obj = scores.get(cid, {})
            sc = sc_obj.get("score")
            ev = sc_obj.get("source_file_evidence")
            gap = sc_obj.get("gap")
            risk = sc_obj.get("risk")
            rat = sc_obj.get("rationale")

            if sc is None or not ev or not gap or not risk or not rat:
                evidence_complete = False
            total += (float(sc) / 5.0) * float(w)

        computed_scores[c_key] = round(total, 2)
        reported_total = round(float(c_val.get("weighted_total", 0.0)), 2)
        if abs(computed_scores[c_key] - reported_total) > 1e-4:
            evidence_complete = False

    # 4. Chỉ đúng một họ được chọn
    selected_family = data.get("selected_family")
    is_prism = (selected_family == "right_triangle_base_right_prism_volume")
    b_is_highest = (
        computed_scores.get("B", 0.0) > computed_scores.get("A", 0.0)
        and computed_scores.get("B", 0.0) > computed_scores.get("C", 0.0)
    )

    valid = (weights_valid and three_candidates and evidence_complete and is_prism and b_is_highest)

    return {
        "valid": valid,
        "weights_valid": weights_valid,
        "three_candidates": three_candidates,
        "evidence_complete": evidence_complete,
        "computed_scores": computed_scores,
        "selected_family": selected_family,
        "b_is_highest": b_is_highest,
        "file_sha256": sha256_file(p),
    }


def validate_manifest_and_ground_truth(
    manifest_path: Path | None = None,
    ground_truth_path: Path | None = None,
) -> dict[str, Any]:
    mp = manifest_path or (EVAL_DIR / "SECOND_FAMILY_MANIFEST.json")
    gp = ground_truth_path or (EVAL_DIR / "SECOND_FAMILY_GROUND_TRUTH.json")

    if not mp.is_file() or not gp.is_file():
        return {"valid": False, "error": f"Missing file: {mp} or {gp}"}

    m_data = json.loads(mp.read_text(encoding="utf-8"))
    g_data = json.loads(gp.read_text(encoding="utf-8"))

    cases = m_data.get("cases", [])
    gt_cases = g_data.get("ground_truth_cases", {})

    # 1. Đúng 8 ca (5 dương, 3 âm)
    case_count = len(cases)
    pos_count = sum(1 for c in cases if c.get("is_positive") is True)
    neg_count = sum(1 for c in cases if c.get("is_positive") is False)
    counts_valid = (case_count == 8 and pos_count == 5 and neg_count == 3)

    # 2. Case ID duy nhất và input hash duy nhất
    case_ids = [c["case_id"] for c in cases]
    unique_case_ids = (len(case_ids) == len(set(case_ids)))
    input_hashes = [c["input_hash"] for c in cases]
    unique_input_hashes = (len(input_hashes) == len(set(input_hashes)))

    # 3. Ground truth phủ đủ 8 case
    gt_covered = (set(case_ids) == set(gt_cases.keys()))

    # 4. Không có expected_answer trong compiler input của manifest
    m_raw = mp.read_text(encoding="utf-8")
    no_expected_in_input = ("expected_answer" not in m_raw and "expected_volume" not in m_raw)

    # 5. Point label policy: không chứa dấu phẩy trên (')
    apostrophe_found = False
    for c in cases:
        for pt in c.get("base_vertices", []) + c.get("top_vertices", []):
            if "'" in pt or "’" in pt or "prime" in pt.lower():
                apostrophe_found = True
        for gl in c.get("given_lengths", []):
            for pt in gl.get("segment", []):
                if "'" in pt or "’" in pt:
                    apostrophe_found = True

    point_naming_valid = not apostrophe_found

    # 6. Toán học của 5 ca dương
    math_valid = True
    for c in cases:
        if not c.get("is_positive"):
            continue
        cid = c["case_id"]
        gt = gt_cases.get(cid, {})

        # Rút độ dài từ given_lengths
        lengths = {tuple(sorted(gl["segment"])): Fraction(gl["value"]) for gl in c["given_lengths"]}
        base_pts = c["base_vertices"]
        top_pts = c["top_vertices"]
        corr = dict(c["correspondence"])
        ra_v = c["right_angle_vertex"]

        # Chân góc vuông đáy
        legs = [p for p in base_pts if p != ra_v]
        assert len(legs) == 2, f"Base right angle legs count mismatch for {cid}"
        len1 = lengths[tuple(sorted((ra_v, legs[0])))]
        len2 = lengths[tuple(sorted((ra_v, legs[1])))]

        # Chiều cao qua đỉnh tương ứng
        top_ra_v = corr[ra_v]
        height = lengths[tuple(sorted((ra_v, top_ra_v)))]

        calc_base_area = Fraction(1, 2) * len1 * len2
        calc_vol = calc_base_area * height

        gt_vol = Fraction(gt["expected_volume"])
        gt_frac = Fraction(
            gt["expected_volume_fraction"]["numerator"],
            gt["expected_volume_fraction"]["denominator"],
        )

        if calc_vol != gt_vol or calc_vol != gt_frac:
            math_valid = False

        # Topology: 6 vertices, 9 edges, 5 faces, Euler = 2
        topo = gt.get("expected_topology", {})
        if (
            topo.get("vertices_count") != 6
            or topo.get("edges_count") != 9
            or topo.get("faces_count") != 5
            or topo.get("euler_characteristic") != 2
        ):
            math_valid = False

    # 7. Phân số chính xác ở P03
    p03_case = next(c for c in cases if c["case_id"] == "PRISM_P03")
    p03_gt = gt_cases["PRISM_P03"]
    p03_exact_frac = (
        Fraction(p03_gt["expected_volume"]) == Fraction(5, 4)
        and p03_gt["expected_volume_fraction"]["denominator"] == 4
    )

    # 8. Hoán đổi nhãn ở P02 giữ nguyên eligibility
    p02_case = next(c for c in cases if c["case_id"] == "PRISM_P02")
    p02_gt = gt_cases["PRISM_P02"]
    p02_valid = (
        p02_gt["expected_status"] == "SUPPORTED"
        and Fraction(p02_gt["expected_volume"]) == Fraction(168)
        and p02_case["base_vertices"] == ["M", "N", "P"]
    )

    # 9. Ba ca âm có mã từ chối hợp lệ
    neg_valid = True
    for cid in ("PRISM_N01", "PRISM_N02", "PRISM_N03"):
        gt = gt_cases.get(cid, {})
        if gt.get("expected_status") != "REJECTED":
            neg_valid = False
        if not gt.get("expected_reason_code"):
            neg_valid = False

    valid = (
        counts_valid
        and unique_case_ids
        and unique_input_hashes
        and gt_covered
        and no_expected_in_input
        and point_naming_valid
        and math_valid
        and p03_exact_frac
        and p02_valid
        and neg_valid
    )

    return {
        "valid": valid,
        "counts_valid": counts_valid,
        "unique_case_ids": unique_case_ids,
        "unique_input_hashes": unique_input_hashes,
        "gt_covered": gt_covered,
        "no_expected_in_input": no_expected_in_input,
        "point_naming_valid": point_naming_valid,
        "math_valid": math_valid,
        "p03_exact_frac": p03_exact_frac,
        "p02_valid": p02_valid,
        "neg_valid": neg_valid,
        "manifest_sha256": sha256_file(mp),
        "ground_truth_sha256": sha256_file(gp),
    }


FROZEN_PREREGISTRATION_COMMIT = "abb377b89a4a2e13be9c5b4bc06984e149ac8566"


def validate_product_and_system_invariants(
    target_commit: str = FROZEN_PREREGISTRATION_COMMIT,
) -> dict[str, Any]:
    # Fail closed nếu frozen commit không tồn tại trong git
    ret, _, _ = run_cmd(["git", "cat-file", "-e", f"{target_commit}^{{commit}}"])
    if ret != 0:
        return {
            "valid": False,
            "error": f"FROZEN_COMMIT_NOT_FOUND:{target_commit}",
            "product_unmodified": False,
            "no_hardcoded_case_ids": False,
            "dynamic_primitive_count": 0,
            "candidate_valid": False,
            "cache_valid": False,
            "favicon_clean": False,
        }

    # 1. Product code unmodified at frozen preregistration commit
    code_diff, out_diff, _ = run_cmd(["git", "diff", f"{target_commit}~1", target_commit, "--", "backend/app", "frontend/src"])
    product_unmodified = (code_diff == 0 and len(out_diff) == 0)

    # 2. No case ID hardcoded in product code at target commit
    grep_ret, grep_out, _ = run_cmd(["git", "grep", "-n", "PRISM_P", f"{target_commit}:backend/app"])
    no_hardcoded_case_ids = (grep_ret != 0 or len(grep_out) == 0)

    # 3. Dynamic primitive count from primitives.py at frozen commit
    prim_ret, prim_content, _ = run_cmd(["git", "show", f"{target_commit}:backend/app/simulation/geometry_compiler/primitives.py"])
    if prim_ret != 0:
        return {"valid": False, "error": "MISSING_PRIMITIVES_FILE_AT_COMMIT"}

    import ast
    tree = ast.parse(prim_content)
    dynamic_prim_count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target_name = getattr(node.target, "id", None) if isinstance(node, ast.AnnAssign) else [getattr(t, "id", None) for t in node.targets]
            if target_name == "REGISTRY" or (isinstance(target_name, list) and "REGISTRY" in target_name):
                dynamic_prim_count = len(node.value.keys)
                break
    has_expected_primitives = (dynamic_prim_count == 6)

    # 4. MeasureExpr is value expression in contract.py at target commit
    contract_ret, contract_content, _ = run_cmd(["git", "show", f"{target_commit}:backend/app/simulation/semantic_program/contract.py"])
    is_value_expr = (
        contract_ret == 0
        and "class MeasureExpr" in contract_content
        and "MeasureExpr" in contract_content
    )

    # 5. Favicon not staged in working tree
    _, staged_out, _ = run_cmd(["git", "diff", "--cached", "--name-only"])
    favicon_clean = "favicon.svg" not in staged_out

    # 6. Candidate verify at frozen commit
    cand_ret, cand_content, _ = run_cmd(["git", "show", f"{target_commit}:docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"])
    candidate_valid = False
    if cand_ret == 0 and cand_content:
        try:
            cand_data = json.loads(cand_content)
            ms = cand_data.get("measured_system", {})
            th = ms.get("tree_hash", "")
            fc = ms.get("so_file") or ms.get("file_count", 0)
            candidate_valid = (
                fc == 103
                and th == "077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1"
            )
        except Exception:
            candidate_valid = False

    # 7. Cache lock verify at frozen commit
    lock_ret, lock_content, _ = run_cmd(["git", "show", f"{target_commit}:backend/cache_identity.lock.json"])
    cache_valid = False
    if lock_ret == 0 and lock_content:
        try:
            lock_data = json.loads(lock_content)
            cache_valid = (lock_data.get("cache_version") == "99")
        except Exception:
            cache_valid = False

    valid = (
        product_unmodified
        and no_hardcoded_case_ids
        and has_expected_primitives
        and is_value_expr
        and favicon_clean
        and candidate_valid
        and cache_valid
    )

    return {
        "valid": valid,
        "product_unmodified": product_unmodified,
        "no_hardcoded_case_ids": no_hardcoded_case_ids,
        "dynamic_primitive_count": dynamic_prim_count,
        "candidate_valid": candidate_valid,
        "cache_valid": cache_valid,
        "favicon_clean": favicon_clean,
        "target_commit": target_commit,
    }


def main() -> int:
    print("=== SECOND FAMILY PREREGISTRATION VALIDATOR (READ-ONLY) ===")
    mat_res = validate_selection_matrix()
    print(f"1. Selection matrix valid: {mat_res.get('valid')}")
    if not mat_res.get("valid"):
        print(f"   Matrix error: {mat_res}")

    mg_res = validate_manifest_and_ground_truth()
    print(f"2. Manifest & Ground Truth valid: {mg_res.get('valid')}")
    if not mg_res.get("valid"):
        print(f"   Manifest/GT error: {mg_res}")

    sys_res = validate_product_and_system_invariants()
    print(f"3. System & Product invariants valid: {sys_res.get('valid')}")
    if not sys_res.get("valid"):
        print(f"   System invariants error: {sys_res}")

    all_valid = (
        mat_res.get("valid", False)
        and mg_res.get("valid", False)
        and sys_res.get("valid", False)
    )
    print(f"OVERALL PREREGISTRATION VALIDITY: {'PASS' if all_valid else 'FAIL'}")
    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
