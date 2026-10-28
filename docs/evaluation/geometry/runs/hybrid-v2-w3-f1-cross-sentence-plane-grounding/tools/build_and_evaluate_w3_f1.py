# -*- coding: utf-8 -*-
"""Build development corpus & exact Fraction oracle for W3-F1 Cross-Sentence Plane Grounding,
and evaluate RED (before) / GREEN (after) + locked Wave 3 post-feedback regression.

Offline only (`ALLOW_LIVE_AI = 0`). Does not modify Historical Holdout Wave 3.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"

RUN_DIR = Path(__file__).resolve().parents[1]
WORKTREE_ROOT = RUN_DIR.parents[4]
BACKEND_DIR = WORKTREE_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

WAVE3_WORKTREE = (
    WORKTREE_ROOT.parent
    / "independent-section-holdout-wave3"
    / "docs"
    / "evaluation"
    / "geometry"
    / "runs"
    / "hybrid-v2-independent-vietnamese-geometry-holdout-wave3"
)

if not WAVE3_WORKTREE.exists():
    # Fallback when running from a detached T3 worktree under .superpowers/worktrees/<tmp>
    WAVE3_WORKTREE = (
        Path(r"d:\Documents\projects\algo-sim\.superpowers\worktrees\independent-section-holdout-wave3")
        / "docs"
        / "evaluation"
        / "geometry"
        / "runs"
        / "hybrid-v2-independent-vietnamese-geometry-holdout-wave3"
    )

W3_F1_CASE_IDS = (
    "W3-B03", "W3-B06", "W3-B09", "W3-B12", "W3-B15", "W3-B18",
    "W3-B21", "W3-B24", "W3-B27", "W3-B30", "W3-B33", "W3-B36",
    "W3-B39", "W3-B42", "W3-B45", "W3-B48", "W3-B51", "W3-B54",
    "W3-A03", "W3-A06", "W3-A09", "W3-A12", "W3-A15", "W3-A18",
)

SECONDARY_DEFECT_MAP: dict[str, str | None] = {
    "W3-B03": None,
    "W3-B06": "W3-F2",
    "W3-B09": "W3-F3",
    "W3-B12": "W3-F2",
    "W3-B15": None,
    "W3-B18": "W3-F3",
    "W3-B21": None,
    "W3-B24": "W3-F2",
    "W3-B27": "W3-F3",
    "W3-B30": "W3-F2",
    "W3-B33": None,
    "W3-B36": "W3-F3",
    "W3-B39": None,
    "W3-B42": "W3-F2",
    "W3-B45": None,
    "W3-B48": "W3-F4",
    "W3-B51": "W3-F4",
    "W3-B54": "W3-F3",
    "W3-A03": None,
    "W3-A06": "W3-F2",
    "W3-A09": None,
    "W3-A12": "W3-F2",
    "W3-A15": None,
    "W3-A18": "W3-F3",
}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_non_plane_premises_for_isolated_f1(case: dict[str, Any]) -> dict[str, Any]:
    """Normalize ONLY non-plane premise wording (W3-F2/F3/F4) to Registry /19-supported premise wording
    while keeping the W3-F1 plane definition sentence, compound question sentence, geometry, and oracle 100% intact.
    """
    c = deepcopy(case)
    cid = c["id"]
    c["original_wave3_id"] = cid
    c["id"] = f"DEV-F1-{cid.split('-')[1]}"
    c["slice"] = "w3_f1_isolated_24"
    if SECONDARY_DEFECT_MAP[cid] is None:
        return c

    p = c["payload"]
    sec_q = p["derived_sections"][0]["quote"]
    req_q = p["simulation_goals"][-1]["quote"]

    def replace_quote(old_q: str, new_q: str) -> None:
        assert old_q in p["problem_text"], f"{cid}: {old_q!r} not in problem_text"
        p["problem_text"] = p["problem_text"].replace(old_q, new_q, 1)
        for prem in p["premises"]:
            if prem["quote"] == old_q:
                prem["quote"] = new_q
        for s in p["solids"]:
            if s["quote"] == old_q:
                s["quote"] = new_q

    # Strip "Trong không gian, cho " -> "Cho " if present at start of problem_text
    if p["problem_text"].startswith("Trong không gian, cho "):
        old_s = p["solids"][0]["quote"]
        new_s = re.sub(r"^Trong không gian,\s*cho\b", "Cho", old_s)
        replace_quote(old_s, new_s)

    for prem in p["premises"]:
        q = prem["quote"]
        new_q = q
        if prem["kind"] in ("rectangle", "right_angle", "perpendicular_line_plane", "segment_length"):
            if new_q.startswith("thỏa mãn đáy "):
                new_q = "có đáy " + new_q[len("thỏa mãn đáy "):]
            elif new_q.startswith("thỏa mãn "):
                new_q = "biết " + new_q[len("thỏa mãn "):]
            if "ở " in new_q and prem["kind"] == "right_angle":
                new_q = new_q.replace("ở ", "tại ")
            if new_q.startswith("biết tam giác đáy ") and prem["kind"] == "right_angle":
                verts = "".join(prem["args"]["vertices"])
                right_at = prem["args"]["right_at"]
                new_q = f"có đáy {verts} là tam giác vuông tại {right_at}"
            if new_q.startswith("với mặt đáy "):
                new_q = "có đáy " + new_q[len("với mặt đáy "):]
            if new_q.startswith("biết mặt đáy "):
                new_q = "có đáy " + new_q[len("biết mặt đáy "):]
            if new_q.startswith("với độ dài "):
                new_q = "biết " + new_q[len("với độ dài "):]
            if new_q.startswith("có số đo "):
                new_q = "biết " + new_q[len("có số đo "):]
            if new_q.startswith("đoạn "):
                new_q = new_q[len("đoạn "):]
            if new_q.startswith("chiều cao "):
                new_q = "và " + new_q[len("chiều cao "):]
            if new_q.startswith("độ dài "):
                new_q = "và " + new_q[len("độ dài "):]
        elif prem["kind"] == "orthogonal_projection":
            pt = prem["args"]["point"]
            img = prem["args"]["image"]
            pl = "".join(prem["args"]["plane"])
            new_q = f"hình chiếu vuông góc của {pt} trên mặt phẳng ({pl}) trùng với {img}"
        elif prem["kind"] == "divide_segment":
            pt = prem["args"]["point"]
            seg = "".join(prem["args"]["segment"])
            rat = prem["args"]["ratio"]
            a = prem["args"]["segment"][0]
            new_q = f"Lấy điểm {pt} trên cạnh {seg} sao cho {a}{pt} = {rat} {seg}"
        if new_q != q:
            replace_quote(q, new_q)

    if cid == "W3-A06":
        # W3-A06 also has an out-of-scope non-plane RADICAL_DOMAIN_OVERFLOW on (6a, 7a, 15a) where p*q = 1.12567e24 > 10^24.
        # In Slice B (isolated W3-F1), normalize lengths to (3a, 4a, 6a) while keeping W3-A06 verbatim in Slice A.
        replace_quote("biết EF = 6a", "biết EF = 3a")
        replace_quote("biết EH = 7a", "biết EH = 4a")
        replace_quote("và cạnh SE = 15a", "và cạnh SE = 6a")
        for x in p["premises"]:
            if x["kind"] == "segment_length":
                if x["args"]["segment"] == ["E", "F"]:
                    x["args"]["value"] = "3a"
                elif x["args"]["segment"] == ["E", "H"]:
                    x["args"]["value"] = "4a"
                elif x["args"]["segment"] == ["S", "E"]:
                    x["args"]["value"] = "6a"

    if cid in ("W3-B48", "W3-B51", "W3-B54", "W3-A18"):
        # Cube premise normalization (avoid W3-F4 while keeping identical cube & edge length)
        sol = p["solids"][0]
        sq_prem = next(x for x in p["premises"] if x["kind"] == "base_is_square")
        len_prem = next(x for x in p["premises"] if x["kind"] == "segment_length")
        div_prem = next(x for x in p["premises"] if x["kind"] == "divide_segment")
        side_val = sq_prem["args"]["side"]
        cube_sent = f"Cho hình lập phương {sol['notation']} có cạnh bằng {side_val}."
        div_sent = div_prem["quote"].rstrip(".") + "."
        sec_sent = sec_q.rstrip(".") + "."
        req_sent = req_q.rstrip(".") + "."
        p["problem_text"] = f"{cube_sent} {div_sent} {sec_sent} {req_sent}"
        sol["quote"] = cube_sent
        for x in p["simulation_goals"]:
            if x["kind"] == "construct_object":
                x["quote"] = cube_sent
        for x in p["premises"]:
            if x["kind"] in ("right_prism", "base_is_square", "segment_length"):
                x["quote"] = cube_sent

    c["problem_text"] = p["problem_text"]
    # Verify plane definition quote and question quote are 100% unchanged from Wave 3
    assert p["derived_sections"][0]["quote"] == sec_q
    assert p["simulation_goals"][-1]["quote"] == req_q
    assert sec_q in p["problem_text"] and req_q in p["problem_text"]
    return c


def _build_authored_positive_and_oracle(w3_cases: dict[str, dict], w3_oracles: dict[str, dict]) -> tuple[list[dict], dict[str, dict]]:
    """Build 24 newly authored positive development cases across all required Section 6 variations,
    plus their exact Fraction oracle entries."""
    authored: list[dict[str, Any]] = []
    oracles: dict[str, dict[str, Any]] = {}

    def clone_from(base_id: str, new_id: str, variation: str, question_type: str | None = None) -> dict[str, Any]:
        base = _normalize_non_plane_premises_for_isolated_f1(w3_cases[base_id])
        base["id"] = new_id
        base["slice"] = "authored_cross_sentence_positive"
        base["variation"] = variation
        if question_type is not None:
            base["question_type"] = question_type
        oracles[new_id] = deepcopy(w3_oracles[base_id])
        oracles[new_id]["id"] = new_id
        return base

    # 1-2: Same-sentence plane definition and question (Category B and Category A)
    c1 = clone_from("W3-B03", "DEV-POS-01", "same_sentence_def_and_question_cat_b")
    p1 = c1["payload"]
    old_def1 = p1["derived_sections"][0]["quote"]
    old_req1 = p1["simulation_goals"][-1]["quote"]
    combined1 = f"{old_def1}, hãy xác định thiết diện của hình chóp S.EFG khi cắt bởi mặt phẳng (P) và tính diện tích của thiết diện"
    p1["problem_text"] = p1["problem_text"].replace(f"{old_def1}. {old_req1}", combined1)
    p1["derived_sections"][0]["quote"] = combined1
    p1["simulation_goals"][-1]["quote"] = combined1
    p1["math_goals"][0]["quote"] = combined1
    authored.append(c1)

    c2 = clone_from("W3-A03", "DEV-POS-02", "same_sentence_def_and_question_cat_a")
    p2 = c2["payload"]
    old_def2 = p2["derived_sections"][0]["quote"]
    old_req2 = p2["simulation_goals"][-1]["quote"]
    combined2 = f"{old_def2}, hãy xác định thiết diện của hình chóp S.EFG khi cắt bởi mặt phẳng (P) và tính diện tích của thiết diện"
    p2["problem_text"] = p2["problem_text"].replace(f"{old_def2}. {old_req2}", combined2)
    p2["derived_sections"][0]["quote"] = combined2
    p2["simulation_goals"][-1]["quote"] = combined2
    p2["math_goals"][0]["quote"] = combined2
    authored.append(c2)

    # 3-4: Two separate sentences with explicit two-quote binding (Category B & Category A)
    c3 = clone_from("W3-B15", "DEV-POS-03", "two_separate_sentences_two_quote_cat_b")
    authored.append(c3)

    c4 = clone_from("W3-A09", "DEV-POS-04", "two_separate_sentences_two_quote_cat_a")
    authored.append(c4)

    # 5-8: Two separate sentences where derived_section.quote points ONLY to the question sentence! (Owner GO §4 core case)
    c5 = clone_from("W3-B03", "DEV-POS-05", "question_only_quote_perpendicular_line_cat_b")
    c5["payload"]["derived_sections"][0]["quote"] = c5["payload"]["simulation_goals"][-1]["quote"]
    authored.append(c5)

    c6 = clone_from("W3-B15", "DEV-POS-06", "question_only_quote_parallel_plane_cat_b")
    c6["payload"]["derived_sections"][0]["quote"] = c6["payload"]["simulation_goals"][-1]["quote"]
    authored.append(c6)

    c7 = clone_from("W3-B45", "DEV-POS-07", "question_only_quote_parallel_two_lines_cat_b")
    c7["payload"]["derived_sections"][0]["quote"] = c7["payload"]["simulation_goals"][-1]["quote"]
    authored.append(c7)

    c8 = clone_from("W3-B39", "DEV-POS-08", "question_only_quote_primed_vertex_cuboid_cat_b")
    c8["payload"]["derived_sections"][0]["quote"] = c8["payload"]["simulation_goals"][-1]["quote"]
    authored.append(c8)

    # 9-12: Multiple intermediate premise sentences between plane definition and question
    c9 = clone_from("W3-B03", "DEV-POS-09", "multi_intermediate_sentences_triangular_pyramid")
    p9 = c9["payload"]
    # Move plane definition right after solid + midpoint, before perpendicularity and 3 length sentences
    s_solid9 = "Cho hình chóp S.EFG có đáy EFG là tam giác vuông tại E."
    s_mid9 = "Gọi H là trung điểm của SE."
    s_def9 = "Mặt phẳng (P) đi qua H đồng thời vuông góc với cạnh SF."
    s_perp9 = "Đường thẳng SE vuông góc với mặt phẳng (EFG)."
    s_len9 = "Biết EF = 9, EG = 14, và SE = 19."
    s_req9 = "Hãy xác định thiết diện của hình chóp S.EFG khi cắt bởi mặt phẳng (P) và tính diện tích của thiết diện."
    p9["problem_text"] = f"{s_solid9} {s_mid9} {s_def9} {s_perp9} {s_len9} {s_req9}"
    p9["solids"][0]["quote"] = s_solid9
    p9["simulation_goals"][0]["quote"] = s_solid9
    p9["premises"][0]["quote"] = "có đáy EFG là tam giác vuông tại E"
    p9["premises"][1]["quote"] = s_perp9[:-1]
    p9["premises"][2]["quote"] = "Biết EF = 9"
    p9["premises"][3]["quote"] = "EG = 14"
    p9["premises"][4]["quote"] = "và SE = 19"
    p9["premises"][5]["quote"] = s_mid9[:-1]
    p9["derived_sections"][0]["quote"] = s_def9[:-1]
    p9["simulation_goals"][-1]["quote"] = s_req9[:-1]
    p9["math_goals"][0]["quote"] = s_req9[:-1]
    authored.append(c9)

    c10 = clone_from("W3-B21", "DEV-POS-10", "multi_intermediate_sentences_right_prism_question_quote")
    p10 = c10["payload"]
    s_sol10 = "Cho hình lăng trụ đứng DEF.D'E'F' có đáy DEF là tam giác vuông tại D."
    s_div10 = "Lấy điểm I trên cạnh DD' sao cho DI = 4/5 DD'."
    s_def10 = "Mặt phẳng (P) đi qua I đồng thời vuông góc với cạnh DF'."
    s_l1_10 = "Biết DE = 5, DF = 6, và DD' = 11."
    s_req10 = "Hãy xác định thiết diện của hình lăng trụ DEF.D'E'F' khi cắt bởi mặt phẳng (P) và tính diện tích của thiết diện."
    p10["problem_text"] = f"{s_sol10} {s_div10} {s_def10} {s_l1_10} {s_req10}"
    p10["solids"][0]["quote"] = "Cho hình lăng trụ đứng DEF.D'E'F'"
    p10["simulation_goals"][0]["quote"] = "Cho hình lăng trụ đứng DEF.D'E'F'"
    p10["premises"][0]["quote"] = "Cho hình lăng trụ đứng DEF.D'E'F'"
    p10["premises"][1]["quote"] = "có đáy DEF là tam giác vuông tại D"
    p10["premises"][2]["quote"] = "Biết DE = 5"
    p10["premises"][3]["quote"] = "DF = 6"
    p10["premises"][4]["quote"] = "và DD' = 11"
    p10["premises"][5]["quote"] = s_div10[:-1]
    # Also test question-only quote on derived_sections with intermediate sentences!
    p10["derived_sections"][0]["quote"] = s_req10[:-1]
    p10["simulation_goals"][-1]["quote"] = s_req10[:-1]
    p10["math_goals"][0]["quote"] = s_req10[:-1]
    authored.append(c10)

    c11 = clone_from("W3-A03", "DEV-POS-11", "multi_intermediate_sentences_cat_a_pyramid")
    p11 = c11["payload"]
    s_sol11 = "Cho hình chóp S.EFG có đáy EFG là tam giác vuông tại E."
    s_mid11 = "Cho M là trung điểm của SE."
    s_def11 = "Mặt phẳng (P) đi qua M đồng thời vuông góc với cạnh SF, cắt các cạnh bên SF, SG lần lượt tại N, P."
    s_perp11 = "Cạnh bên SE vuông góc với mặt phẳng (EFG)."
    s_len11 = "Biết EF = 5, EG = 11, và SE = 16."
    s_req11 = "Hãy xác định thiết diện của hình chóp S.EFG khi cắt bởi mặt phẳng (P) và tính diện tích của thiết diện."
    p11["problem_text"] = f"{s_sol11} {s_mid11} {s_def11} {s_perp11} {s_len11} {s_req11}"
    p11["solids"][0]["quote"] = "Cho hình chóp S.EFG"
    p11["simulation_goals"][0]["quote"] = "Cho hình chóp S.EFG"
    p11["premises"][0]["quote"] = "có đáy EFG là tam giác vuông tại E"
    p11["premises"][1]["quote"] = s_perp11[:-1]
    p11["premises"][2]["quote"] = "Biết EF = 5"
    p11["premises"][3]["quote"] = "EG = 11"
    p11["premises"][4]["quote"] = "và SE = 16"
    p11["premises"][5]["quote"] = s_mid11[:-1]
    p11["derived_sections"][0]["quote"] = s_def11[:-1]
    p11["simulation_goals"][-1]["quote"] = s_req11[:-1]
    p11["math_goals"][0]["quote"] = s_req11[:-1]
    authored.append(c11)

    c12 = clone_from("W3-A15", "DEV-POS-12", "multi_intermediate_sentences_cat_a_cuboid_parallel_two_lines")
    p12 = c12["payload"]
    s_div12 = "Lấy điểm K trên cạnh EE' sao cho EK = 4/15 EE'."
    s_def12 = "Mặt phẳng (P) chứa K và song song với cả hai đường thẳng EF, EH, cắt các cạnh bên FF', GG', HH' lần lượt tại I, J, L."
    s_len12 = "Cho hình hộp chữ nhật EFGH.E'F'G'H' có đáy EFGH là hình chữ nhật, biết EF = 7, EH = 9, và EE' = 20."
    s_req12 = "Hãy xác định thiết diện của hình hộp chữ nhật EFGH.E'F'G'H' khi cắt bởi mặt phẳng (P) và tính diện tích của thiết diện."
    p12["problem_text"] = f"{s_len12} {s_div12} {s_def12} {s_req12}"
    p12["solids"][0]["quote"] = "Cho hình hộp chữ nhật EFGH.E'F'G'H'"
    p12["simulation_goals"][0]["quote"] = "Cho hình hộp chữ nhật EFGH.E'F'G'H'"
    p12["premises"][0]["quote"] = "Cho hình hộp chữ nhật EFGH.E'F'G'H'"
    p12["premises"][1]["quote"] = "có đáy EFGH là hình chữ nhật"
    p12["premises"][2]["quote"] = "biết EF = 7"
    p12["premises"][3]["quote"] = "EH = 9"
    p12["premises"][4]["quote"] = "và EE' = 20"
    p12["premises"][5]["quote"] = s_div12[:-1]
    authored.append(c12)

    # 13-16: Renamed planes ((Q), (α), (β), (γ)) and point-first / introducer variations
    c13 = clone_from("W3-B03", "DEV-POS-13", "renamed_plane_alpha_point_first_definition")
    p13 = c13["payload"]
    old_def13 = p13["derived_sections"][0]["quote"]
    old_req13 = p13["simulation_goals"][-1]["quote"]
    new_def13 = "Qua H dựng mặt phẳng (α) đồng thời vuông góc với cạnh SF"
    new_req13 = old_req13.replace("(P)", "(α)")
    p13["problem_text"] = p13["problem_text"].replace(old_def13, new_def13).replace(old_req13, new_req13)
    p13["derived_sections"][0]["plane_name"] = "α"
    p13["derived_sections"][0]["quote"] = new_def13
    p13["simulation_goals"][-1]["quote"] = new_req13
    p13["math_goals"][0]["quote"] = new_req13
    authored.append(c13)

    c14 = clone_from("W3-B15", "DEV-POS-14", "renamed_plane_beta_thiet_lap_introducer")
    p14 = c14["payload"]
    old_def14 = p14["derived_sections"][0]["quote"]
    old_req14 = p14["simulation_goals"][-1]["quote"]
    new_def14 = "Thiết lập mặt phẳng (β) đi qua F đồng thời song song với mặt phẳng (ABC)"
    new_req14 = old_req14.replace("(P)", "(β)")
    p14["problem_text"] = p14["problem_text"].replace(old_def14, new_def14).replace(old_req14, new_req14)
    p14["derived_sections"][0]["plane_name"] = "β"
    p14["derived_sections"][0]["quote"] = new_def14
    p14["simulation_goals"][-1]["quote"] = new_req14
    p14["math_goals"][0]["quote"] = new_req14
    authored.append(c14)

    c15 = clone_from("W3-B33", "DEV-POS-15", "renamed_plane_gamma_xet_introducer_question_quote")
    p15 = c15["payload"]
    old_def15 = p15["derived_sections"][0]["quote"]
    old_req15 = p15["simulation_goals"][-1]["quote"]
    new_def15 = "Xét mặt phẳng (γ) đi qua L đồng thời song song với mặt phẳng (GHG')"
    new_req15 = old_req15.replace("(P)", "(γ)")
    p15["problem_text"] = p15["problem_text"].replace(old_def15, new_def15).replace(old_req15, new_req15)
    p15["derived_sections"][0]["plane_name"] = "γ"
    p15["derived_sections"][0]["quote"] = new_req15
    p15["simulation_goals"][-1]["quote"] = new_req15
    p15["math_goals"][0]["quote"] = new_req15
    authored.append(c15)

    c16 = clone_from("W3-B45", "DEV-POS-16", "renamed_plane_Q_goi_la_mat_phang_two_lines")
    p16 = c16["payload"]
    old_def16 = p16["derived_sections"][0]["quote"]
    old_req16 = p16["simulation_goals"][-1]["quote"]
    new_def16 = "Gọi (Q) là mặt phẳng chứa K đồng thời song song với cả hai đường thẳng CC', CD"
    new_req16 = old_req16.replace("(P)", "(Q)")
    p16["problem_text"] = p16["problem_text"].replace(old_def16, new_def16).replace(old_req16, new_req16)
    p16["derived_sections"][0]["plane_name"] = "Q"
    p16["derived_sections"][0]["quote"] = new_def16
    p16["simulation_goals"][-1]["quote"] = new_req16
    p16["math_goals"][0]["quote"] = new_req16
    authored.append(c16)

    # 17-18: Reordered premises (point and plane defined before base/height/length premises)
    c17 = clone_from("W3-B15", "DEV-POS-17", "reordered_premises_quadrilateral_pyramid")
    p17 = c17["payload"]
    s_sol17 = "Xét khối chóp A.BCDE."
    s_div17 = "Gọi F là điểm thuộc cạnh BE sao cho BF = 4/9 BE."
    s_def17 = "Mặt phẳng (P) đi qua F đồng thời song song với mặt phẳng (ABC)."
    s_rest17 = "Cho khối chóp A.BCDE có đáy BCDE là hình chữ nhật, đường thẳng AB vuông góc với mặt phẳng (BCDE), biết BC = 7a, BE = 10a, và AB = 19a."
    s_req17 = "Hãy xác định thiết diện của hình chóp A.BCDE khi cắt bởi mặt phẳng (P) và tính diện tích của thiết diện."
    p17["problem_text"] = f"{s_sol17} {s_div17} {s_def17} {s_rest17} {s_req17}"
    p17["solids"][0]["quote"] = s_sol17[:-1]
    p17["simulation_goals"][0]["quote"] = s_sol17[:-1]
    p17["premises"][0]["quote"] = "có đáy BCDE là hình chữ nhật"
    p17["premises"][1]["quote"] = "đường thẳng AB vuông góc với mặt phẳng (BCDE)"
    p17["premises"][2]["quote"] = "biết BC = 7a"
    p17["premises"][3]["quote"] = "BE = 10a"
    p17["premises"][4]["quote"] = "và AB = 19a"
    p17["premises"][5]["quote"] = s_div17[:-1]
    p17["derived_sections"][0]["quote"] = s_def17[:-1]
    p17["simulation_goals"][-1]["quote"] = s_req17[:-1]
    p17["math_goals"][0]["quote"] = s_req17[:-1]
    authored.append(c17)

    c18 = clone_from("W3-B51", "DEV-POS-18", "reordered_premises_cube_parallel_plane")
    p18 = c18["payload"]
    s_div18 = "Gọi I là điểm thuộc cạnh GL sao cho GI = 3/13 GL."
    s_def18 = "Mặt phẳng (P) đi qua I đồng thời song song với mặt phẳng (GHG')."
    s_cube18 = "Cho hình lập phương GHKL.G'H'K'L' có cạnh bằng 15a."
    s_req18 = "Hãy xác định thiết diện của hình lập phương GHKL.G'H'K'L' khi cắt bởi mặt phẳng (P) và tính diện tích của thiết diện."
    p18["problem_text"] = f"{s_cube18} {s_def18} {s_div18} {s_req18}"
    for x in p18["premises"]:
        if x["kind"] == "divide_segment":
            x["quote"] = s_div18[:-1]
    p18["derived_sections"][0]["quote"] = s_req18[:-1]
    authored.append(c18)

    # 19-22: section_only, area_only, and section_and_area (anaphoric "thiết diện đó" and "diện tích của nó")
    c19 = clone_from("W3-B03", "DEV-POS-19", "cross_sentence_section_only_question_quote", question_type="section_only")
    p19 = c19["payload"]
    old_req19 = p19["simulation_goals"][-1]["quote"]
    new_req19 = "Hãy xác định thiết diện của hình chóp S.EFG khi cắt bởi mặt phẳng (P)"
    p19["problem_text"] = p19["problem_text"].replace(old_req19, new_req19)
    p19["derived_sections"][0]["quote"] = new_req19
    p19["simulation_goals"][-1]["quote"] = new_req19
    p19["math_goals"] = []
    oracles["DEV-POS-19"]["question_type"] = "section_only"
    oracles["DEV-POS-19"]["area_goal_id"] = None
    authored.append(c19)

    c20 = clone_from("W3-B15", "DEV-POS-20", "cross_sentence_area_only_question_quote", question_type="area_only")
    p20 = c20["payload"]
    old_req20 = p20["simulation_goals"][-1]["quote"]
    new_req20 = "Hãy tính diện tích thiết diện của hình chóp A.BCDE khi cắt bởi mặt phẳng (P)"
    p20["problem_text"] = p20["problem_text"].replace(old_req20, new_req20)
    p20["derived_sections"][0]["quote"] = new_req20
    p20["simulation_goals"] = [
        {
            "goal_id": "sg1",
            "kind": "construct_object",
            "target_solid_id": "s1",
            "quote": p20["solids"][0]["quote"],
        }
    ]
    p20["math_goals"][0]["quote"] = new_req20
    oracles["DEV-POS-20"]["question_type"] = "area_only"
    authored.append(c20)

    c21 = clone_from("W3-B21", "DEV-POS-21", "cross_sentence_anaphoric_thiet_dien_do")
    p21 = c21["payload"]
    old_req21 = p21["simulation_goals"][-1]["quote"]
    new_req21 = "Hãy xác định thiết diện tạo bởi mặt phẳng (P) với hình lăng trụ DEF.D'E'F' và tính diện tích thiết diện đó"
    p21["problem_text"] = p21["problem_text"].replace(old_req21, new_req21)
    p21["derived_sections"][0]["quote"] = new_req21
    p21["simulation_goals"][-1]["quote"] = new_req21
    p21["math_goals"][0]["quote"] = new_req21
    authored.append(c21)

    c22 = clone_from("W3-B39", "DEV-POS-22", "cross_sentence_anaphoric_dien_tich_cua_no")
    p22 = c22["payload"]
    old_req22 = p22["simulation_goals"][-1]["quote"]
    new_req22 = "Hãy xác định thiết diện của hình hộp chữ nhật EFGH.E'F'G'H' cắt bởi mặt phẳng (P) và tính diện tích của nó"
    p22["problem_text"] = p22["problem_text"].replace(old_req22, new_req22)
    p22["derived_sections"][0]["quote"] = new_req22
    p22["simulation_goals"][-1]["quote"] = new_req22
    p22["math_goals"][0]["quote"] = new_req22
    authored.append(c22)

    # 23-24: Oblique triangular prism Category B & Category A primed-vertex cross-sentence grounding
    c23 = clone_from("W3-B30", "DEV-POS-23", "oblique_triangular_prism_perpendicular_line_cross_sentence")
    c23["payload"]["derived_sections"][0]["quote"] = c23["payload"]["simulation_goals"][-1]["quote"]
    authored.append(c23)

    c24 = clone_from("W3-A12", "DEV-POS-24", "oblique_triangular_prism_cat_a_primed_vertex_cross_sentence")
    authored.append(c24)

    for c_item in authored:
        c_item["problem_text"] = c_item["payload"]["problem_text"]

    assert len(authored) == 24
    return authored, oracles


def _build_mandatory_negative_tamper_cases(w3_cases: dict[str, dict]) -> list[dict[str, Any]]:
    """Build all 20 mandatory negative/tamper cases from Owner GO §7."""
    negatives: list[dict[str, Any]] = []

    def make_neg(
        neg_id: str,
        tamper_index: int,
        tamper_class: str,
        base_id: str,
        mutator,
        expected_codes: list[str],
        acceptable_categories: list[str],
    ) -> None:
        base = _normalize_non_plane_premises_for_isolated_f1(w3_cases[base_id])
        base["id"] = neg_id
        base["slice"] = "mandatory_negative_tamper"
        base["stratum"] = "N"
        base["tamper_index"] = tamper_index
        base["negative_class"] = tamper_class
        base["expected_disposition"] = "REFUSE"
        base["expected_codes"] = expected_codes
        base["acceptable_categories"] = acceptable_categories
        mutator(base["payload"])
        base["problem_text"] = base["payload"]["problem_text"]
        negatives.append(base)

    # 1. Câu hỏi nhắc (P) nhưng đề chưa định nghĩa (P).
    def m1(p: dict) -> None:
        old_def = p["derived_sections"][0]["quote"]
        p["problem_text"] = p["problem_text"].replace(old_def + ". ", "")
        p["derived_sections"][0]["quote"] = p["simulation_goals"][-1]["quote"]

    make_neg("DEV-NEG-01", 1, "question_references_undefined_plane", "W3-B03", m1,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 2. (P) được định nghĩa thiếu through-point bắt buộc.
    def m2(p: dict) -> None:
        old_def = p["derived_sections"][0]["quote"]
        new_def = "Mặt phẳng (P) vuông góc với cạnh SF"
        p["problem_text"] = p["problem_text"].replace(old_def, new_def)
        p["derived_sections"][0]["quote"] = new_def

    make_neg("DEV-NEG-02", 2, "plane_definition_missing_through_point", "W3-B03", m2,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 3. (P) được định nghĩa thiếu quan hệ hình học bắt buộc.
    def m3(p: dict) -> None:
        old_def = p["derived_sections"][0]["quote"]
        new_def = "Mặt phẳng (P) đi qua điểm H"
        p["problem_text"] = p["problem_text"].replace(old_def, new_def)
        p["derived_sections"][0]["quote"] = new_def

    make_neg("DEV-NEG-03", 3, "plane_definition_missing_relation", "W3-B03", m3,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 4. Hai định nghĩa (P) mâu thuẫn nhau.
    def m4(p: dict) -> None:
        old_def = p["derived_sections"][0]["quote"]
        conflict = "Mặt phẳng (P) đi qua H đồng thời vuông góc với cạnh SG."
        p["problem_text"] = p["problem_text"].replace(old_def + ".", f"{old_def}. {conflict}")

    make_neg("DEV-NEG-04", 4, "two_contradictory_definitions_of_same_plane", "W3-B03", m4,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 5. Hai mặt phẳng khác nhau cùng được gọi (P).
    def m5(p: dict) -> None:
        old_def = p["derived_sections"][0]["quote"]
        second_p = "Gọi (P) là mặt phẳng đi qua E và song song với mặt phẳng (SFG)."
        p["problem_text"] = p["problem_text"].replace(old_def + ".", f"{old_def}. {second_p}")

    make_neg("DEV-NEG-05", 5, "two_distinct_planes_sharing_name_P", "W3-B03", m5,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 6. Câu hỏi tham chiếu sai mặt phẳng.
    def m6(p: dict) -> None:
        old_req = p["simulation_goals"][-1]["quote"]
        new_req = old_req.replace("(P)", "(Q)")
        p["problem_text"] = p["problem_text"].replace(old_req, new_req)
        p["simulation_goals"][-1]["quote"] = new_req
        p["math_goals"][0]["quote"] = new_req

    make_neg("DEV-NEG-06", 6, "question_references_wrong_plane", "W3-B03", m6,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 7. Câu hỏi sử dụng (Q) nhưng payload trỏ đến (P).
    def m7(p: dict) -> None:
        old_def = p["derived_sections"][0]["quote"]
        old_req = p["simulation_goals"][-1]["quote"]
        new_def = old_def.replace("(P)", "(Q)")
        new_req = old_req.replace("(P)", "(Q)")
        p["problem_text"] = p["problem_text"].replace(old_def, new_def).replace(old_req, new_req)
        p["derived_sections"][0]["quote"] = new_def
        p["simulation_goals"][-1]["quote"] = new_req
        p["math_goals"][0]["quote"] = new_req
        # Payload keeps plane_name = "P" while source uses (Q)
        p["derived_sections"][0]["plane_name"] = "P"

    make_neg("DEV-NEG-07", 7, "source_uses_Q_payload_points_to_P", "W3-B03", m7,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 8. Plane definition thuộc solid A, câu hỏi lại dùng solid B.
    def m8(p: dict) -> None:
        old_req = p["simulation_goals"][-1]["quote"]
        new_req = old_req.replace("S.EFG", "T.MNP")
        p["problem_text"] = p["problem_text"].replace(old_req, new_req)
        p["simulation_goals"][-1]["quote"] = new_req
        p["math_goals"][0]["quote"] = new_req

    make_neg("DEV-NEG-08", 8, "plane_defined_on_solid_A_question_asks_solid_B", "W3-B03", m8,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 9. Source quote không có trong problem_text.
    def m9(p: dict) -> None:
        p["derived_sections"][0]["quote"] = "Mặt phẳng (P) đi qua H và vuông góc với đường thẳng SF không có trong đề"

    make_neg("DEV-NEG-09", 9, "source_quote_not_in_problem_text", "W3-B03", m9,
             ["QUOTE_NOT_IN_SOURCE", "SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 10. Payload tự tạo through-point không xuất hiện trong định nghĩa.
    def m10(p: dict) -> None:
        p["derived_sections"][0]["through_point"] = "E"

    make_neg("DEV-NEG-10", 10, "payload_fabricates_through_point", "W3-B03", m10,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 11. Payload thay đổi perpendicular_line thành parallel_plane.
    def m11(p: dict) -> None:
        sec = p["derived_sections"][0]
        sec["plane_kind"] = "through_point_parallel_plane"
        sec.pop("perpendicular_line", None)
        sec["parallel_plane"] = ["E", "F", "G"]

    make_neg("DEV-NEG-11", 11, "payload_changes_perpendicular_to_parallel_plane", "W3-B03", m11,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 12. Payload thay đổi reference line/plane.
    def m12(p: dict) -> None:
        p["derived_sections"][0]["perpendicular_line"] = ["S", "G"]

    make_neg("DEV-NEG-12", 12, "payload_changes_reference_line_or_plane", "W3-B03", m12,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 13. Câu hỏi chỉ yêu cầu thiết diện nhưng payload thêm ask_section_area.
    def m13(p: dict) -> None:
        old_req = p["simulation_goals"][-1]["quote"]
        new_req = "Hãy xác định thiết diện của hình chóp S.EFG khi cắt bởi mặt phẳng (P)"
        p["problem_text"] = p["problem_text"].replace(old_req, new_req)
        p["simulation_goals"][-1]["quote"] = new_req
        p["math_goals"][0]["quote"] = new_req

    make_neg("DEV-NEG-13", 13, "question_asks_section_only_payload_adds_area", "W3-B03", m13,
             ["NOT_ASKED_IN_SOURCE", "SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 14. Câu hỏi yêu cầu diện tích của một thiết diện khác.
    def m14(p: dict) -> None:
        old_req = p["simulation_goals"][-1]["quote"]
        new_req = "Hãy xác định thiết diện của hình chóp S.EFG khi cắt bởi mặt phẳng (P) và tính diện tích thiết diện của hình chóp S.EFG cắt bởi mặt phẳng (HEG)"
        p["problem_text"] = p["problem_text"].replace(old_req, new_req)
        p["simulation_goals"][-1]["quote"] = new_req
        p["math_goals"][0]["quote"] = new_req

    make_neg("DEV-NEG-14", 14, "question_asks_area_of_different_section", "W3-B03", m14,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 15. Tham chiếu mơ hồ qua đại từ “mặt phẳng đó”.
    def m15(p: dict) -> None:
        old_req = p["simulation_goals"][-1]["quote"]
        new_req = old_req.replace("mặt phẳng (P)", "mặt phẳng đó")
        p["problem_text"] = p["problem_text"].replace(old_req, new_req)
        p["simulation_goals"][-1]["quote"] = new_req
        p["math_goals"][0]["quote"] = new_req

    make_neg("DEV-NEG-15", 15, "ambiguous_pronoun_reference_mat_phang_do", "W3-B03", m15,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 16. Premise nằm trong câu phủ định hoặc giả thiết điều kiện không đủ hiệu lực.
    def m16(p: dict) -> None:
        old_def = p["derived_sections"][0]["quote"]
        new_def = "Nếu mặt phẳng (P) đi qua H đồng thời vuông góc với cạnh SF"
        p["problem_text"] = p["problem_text"].replace(old_def, new_def)
        p["derived_sections"][0]["quote"] = new_def

    make_neg("DEV-NEG-16", 16, "plane_premise_in_conditional_or_negated_clause", "W3-B03", m16,
             ["CONDITIONAL_CLAUSE", "NEGATED_CLAUSE"], ["SOURCE_GROUNDING"])

    # 17. Điểm hoặc đường tham chiếu thuộc khối không liên quan.
    def m17(p: dict) -> None:
        # Add a second unrelated solid T.ABC in payload and reference its edge TA in plane definition
        s2_q = "Cho hình chóp T.ABC."
        p["problem_text"] = s2_q + " " + p["problem_text"]
        p["solids"].append({
            "solid_id": "s2",
            "solid_type": "pyramid",
            "notation": "T.ABC",
            "quote": s2_q,
        })
        old_def = p["derived_sections"][0]["quote"]
        new_def = "Mặt phẳng (P) đi qua H đồng thời vuông góc với cạnh TA"
        p["problem_text"] = p["problem_text"].replace(old_def, new_def)
        p["derived_sections"][0]["quote"] = new_def
        p["derived_sections"][0]["perpendicular_line"] = ["T", "A"]

    make_neg("DEV-NEG-17", 17, "reference_point_or_line_from_unrelated_solid", "W3-B03", m17,
             ["SOURCE_OBJECT_MISMATCH", "UNSUPPORTED_CAPABILITY"], ["SOURCE_GROUNDING", "UNSUPPORTED_CAPABILITY"])

    # 18. Mâu thuẫn giữa ký hiệu nguồn và IR identity.
    def m18(p: dict) -> None:
        # Source defines and asks for (P), but payload IR declares plane_name = "R"
        p["derived_sections"][0]["plane_name"] = "R"

    make_neg("DEV-NEG-18", 18, "source_symbol_vs_ir_identity_conflict", "W3-B15", m18,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 19. Hoán đổi tên các đỉnh có dấu phẩy.
    def m19(p: dict) -> None:
        # Source says "đi qua E' đồng thời vuông góc với cạnh EG'", payload swaps E' -> E and G' -> G
        p["derived_sections"][0]["through_point"] = "E"
        p["derived_sections"][0]["perpendicular_line"] = ["E", "G"]

    make_neg("DEV-NEG-19", 19, "swapped_primed_vertex_labels", "W3-B39", m19,
             ["SOURCE_OBJECT_MISMATCH"], ["SOURCE_GROUNDING"])

    # 20. Thay đổi source span sau khi source binding đã được xác thực.
    def m20(p: dict) -> None:
        # Source sentence has an extra unverified continuation after the quoted definition span
        old_def = p["derived_sections"][0]["quote"]
        p["problem_text"] = p["problem_text"].replace(
            old_def + ".",
            old_def + " và đồng thời đi qua đỉnh E.",
        )

    make_neg("DEV-NEG-20", 20, "mutated_source_span_after_definition_quote", "W3-B03", m20,
             ["SOURCE_OBJECT_MISMATCH", "SOURCE_PREMISE_UNREAD"], ["SOURCE_GROUNDING"])

    assert len(negatives) == 20
    return negatives


def build_development_and_oracle() -> tuple[dict[str, Any], dict[str, Any]]:
    w3_corpus_path = WAVE3_WORKTREE / "inputs" / "holdout-wave3.json"
    w3_oracle_path = WAVE3_WORKTREE / "oracle" / "expected.json"
    w3_corpus = json.loads(w3_corpus_path.read_text(encoding="utf-8"))
    w3_oracle = json.loads(w3_oracle_path.read_text(encoding="utf-8"))

    w3_cases_by_id = {c["id"]: c for c in w3_corpus["cases"]}
    w3_oracles_by_id = w3_oracle["cases"]

    # Slice A: 24 verbatim historical W3-F1 cases
    slice_a: list[dict[str, Any]] = []
    oracle_cases: list[dict[str, Any]] = []
    for cid in W3_F1_CASE_IDS:
        c = deepcopy(w3_cases_by_id[cid])
        c["slice"] = "historical_w3_f1_verbatim"
        c["has_secondary_out_of_scope_defect"] = SECONDARY_DEFECT_MAP[cid] is not None
        c["secondary_defect_cluster"] = SECONDARY_DEFECT_MAP[cid]
        slice_a.append(c)
        oracle_cases.append(deepcopy(w3_oracles_by_id[cid]))

    # Slice B: 24 W3-F1 isolated cases (same 24 W3-F1 problems with secondary W3-F2/F3/F4 premise wording normalized)
    slice_b: list[dict[str, Any]] = []
    for cid in W3_F1_CASE_IDS:
        c_iso = _normalize_non_plane_premises_for_isolated_f1(w3_cases_by_id[cid])
        slice_b.append(c_iso)
        o_iso = deepcopy(w3_oracles_by_id[cid])
        o_iso["id"] = c_iso["id"]
        if cid == "W3-A06":
            o_iso["boundary"] = [
                {"edge": ["S", "E"], "t": "3/7"},
                {"edge": ["S", "H"], "t": "27/91"},
                {"edge": ["S", "G"], "t": "108/427"},
                {"edge": ["S", "F"], "t": "12/35"},
            ]
            o_iso["polygon_3d"] = [
                ["0", "0", "24/7"],
                ["0", "108/91", "384/91"],
                ["324/427", "432/427", "1914/427"],
                ["36/35", "0", "138/35"],
            ]
            o_iso["area_squared"] = "987719184/618797725"
            o_iso["plane_equation"] = {"normal": ["3", "4", "-6"], "d": "-144/7"}
        oracle_cases.append(o_iso)

    # Slice C: 24 newly authored positive cross-sentence plane grounding cases
    slice_c, authored_oracles = _build_authored_positive_and_oracle(w3_cases_by_id, w3_oracles_by_id)
    for c_auth in slice_c:
        oracle_cases.append(authored_oracles[c_auth["id"]])

    # Slice D: 20 mandatory negative / tamper cases
    slice_d = _build_mandatory_negative_tamper_cases(w3_cases_by_id)
    for c_neg in slice_d:
        oracle_cases.append({
            "id": c_neg["id"],
            "stratum": "N",
            "expected_disposition": "REFUSE",
            "expected_codes": c_neg["expected_codes"],
            "acceptable_categories": c_neg["acceptable_categories"],
            "negative_class": c_neg["negative_class"],
        })

    dev_doc = {
        "schema_version": "w3-f1-development-corpus/1",
        "task": "HYBRID_V2_W3_F1_CROSS_SENTENCE_PLANE_GROUNDING",
        "evidence_classification": "DEVELOPMENT_AND_POST_FEEDBACK_REGRESSION",
        "source_wave3_corpus_sha256": _sha256_file(w3_corpus_path),
        "source_wave3_oracle_sha256": _sha256_file(w3_oracle_path),
        "counts": {
            "total_cases": len(slice_a) + len(slice_b) + len(slice_c) + len(slice_d),
            "historical_w3_f1_verbatim": len(slice_a),
            "historical_w3_f1_pure": sum(1 for c in slice_a if not c["has_secondary_out_of_scope_defect"]),
            "historical_w3_f1_with_secondary_defect": sum(1 for c in slice_a if c["has_secondary_out_of_scope_defect"]),
            "w3_f1_isolated_24": len(slice_b),
            "authored_cross_sentence_positive": len(slice_c),
            "mandatory_negative_tamper": len(slice_d),
        },
        "cases": slice_a + slice_b + slice_c + slice_d,
    }
    oracle_doc = {
        "schema_version": "w3-f1-development-oracle/1",
        "task": "HYBRID_V2_W3_F1_CROSS_SENTENCE_PLANE_GROUNDING",
        "cases": oracle_cases,
    }
    return dev_doc, oracle_doc


def evaluate_corpus(dev_doc: dict[str, Any], oracle_doc: dict[str, Any], phase: str) -> dict[str, Any]:
    # Import evaluate_holdout_wave3's score_case so scoring is 100% identical to Wave 3
    w3_tools = WAVE3_WORKTREE / "tools"
    if str(w3_tools) not in sys.path:
        sys.path.insert(0, str(w3_tools))
    import evaluate_holdout_wave3 as EW3
    from app.simulation.geometry_functions import engine, planner, registry
    from app.ai.adapter4_route import (
        ADAPTER_V4_VERSION,
        build_adapter4_response,
        run_typed_fact_next_v2_route,
    )

    tax = json.loads((WAVE3_WORKTREE / "refusal-taxonomy.json").read_text(encoding="utf-8"))
    oracles_by_id = {o["id"]: o for o in oracle_doc["cases"]}
    results_by_slice: dict[str, list[dict[str, Any]]] = {}
    all_results: list[dict[str, Any]] = []

    for case in dev_doc["cases"]:
        cid = case["id"]
        sl = case["slice"]
        ora = oracles_by_id[cid]
        exp_arg = ora if "boundary" in ora else None
        scored = EW3.score_case(
            case,
            exp_arg,
            tax,
            route_fn=run_typed_fact_next_v2_route,
            adapter_fn=build_adapter4_response,
        )
        scored["slice"] = sl
        if "variation" in case:
            scored["variation"] = case["variation"]
        if "has_secondary_out_of_scope_defect" in case:
            scored["has_secondary_out_of_scope_defect"] = case["has_secondary_out_of_scope_defect"]
            scored["secondary_defect_cluster"] = case["secondary_defect_cluster"]
        if "expected_codes" in case:
            scored["expected_codes"] = case["expected_codes"]
            scored["exact_code_agreement"] = scored["code"] in case["expected_codes"]
        results_by_slice.setdefault(sl, []).append(scored)
        all_results.append(scored)

    def summarize_positive(items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total": len(items),
            "served_correct": sum(1 for x in items if x["outcome"] == "SERVED_CORRECT"),
            "false_refusal": sum(1 for x in items if x["outcome"] == "FALSE_REFUSAL"),
            "wrong_served": sum(1 for x in items if x["outcome"] == "WRONG_SERVED"),
            "source_object_mismatch_count": sum(1 for x in items if x.get("code") == "SOURCE_OBJECT_MISMATCH"),
            "by_stratum": {
                st: {
                    "total": sum(1 for x in items if x["stratum"] == st),
                    "served_correct": sum(1 for x in items if x["stratum"] == st and x["outcome"] == "SERVED_CORRECT"),
                    "false_refusal": sum(1 for x in items if x["stratum"] == st and x["outcome"] == "FALSE_REFUSAL"),
                    "wrong_served": sum(1 for x in items if x["stratum"] == st and x["outcome"] == "WRONG_SERVED"),
                }
                for st in ("P-B", "P-A")
            },
            "refusal_code_breakdown": {
                code: sum(1 for x in items if x.get("code") == code)
                for code in sorted({x.get("code") for x in items if x.get("code")})
            },
        }

    neg_items = results_by_slice.get("mandatory_negative_tamper", [])
    neg_summary = {
        "total": len(neg_items),
        "refused_total": sum(1 for x in neg_items if not x["served"]),
        "refused_correct_category": sum(1 for x in neg_items if x["outcome"] == "REFUSED_CORRECT_REASON"),
        "refused_exact_expected_code": sum(1 for x in neg_items if x.get("exact_code_agreement")),
        "wrong_served": sum(1 for x in neg_items if x["outcome"] == "WRONG_SERVED"),
        "refusal_code_breakdown": {
            code: sum(1 for x in neg_items if x.get("code") == code)
            for code in sorted({x.get("code") for x in neg_items if x.get("code")})
        },
    }

    hist_items = results_by_slice.get("historical_w3_f1_verbatim", [])
    hist_pure = [x for x in hist_items if not x.get("has_secondary_out_of_scope_defect")]
    hist_secondary = [x for x in hist_items if x.get("has_secondary_out_of_scope_defect")]

    return {
        "phase": phase,
        "task": "HYBRID_V2_W3_F1_CROSS_SENTENCE_PLANE_GROUNDING",
        "evidence_classification": "DEVELOPMENT_EVALUATION",
        "versions": {
            "registry_version": registry.REGISTRY_VERSION,
            "planner_version": planner.PLANNER_VERSION,
            "engine_version": engine.ENGINE_VERSION,
            "adapter_version": ADAPTER_V4_VERSION,
            "certificate_version": engine.PLANE_SECTION_CERTIFICATE_VERSION,
            "allow_live_ai": os.environ.get("ALLOW_LIVE_AI"),
        },
        "summary": {
            "historical_w3_f1_verbatim_all_24": summarize_positive(hist_items),
            "historical_w3_f1_pure_9": summarize_positive(hist_pure),
            "historical_w3_f1_with_secondary_defect_15": summarize_positive(hist_secondary),
            "w3_f1_isolated_24": summarize_positive(results_by_slice.get("w3_f1_isolated_24", [])),
            "authored_cross_sentence_positive_24": summarize_positive(
                results_by_slice.get("authored_cross_sentence_positive", [])
            ),
            "mandatory_negative_tamper_20": neg_summary,
            "total_wrong_served": sum(1 for x in all_results if x["outcome"] == "WRONG_SERVED"),
            "machine_id_leak_cases": [
                x["id"] for x in all_results if x.get("machine_id_leaks")
            ],
            "source_identity_leak_cases": [
                x["id"] for x in all_results if x.get("source_identity_leaks")
            ],
        },
        "cases": all_results,
    }


def evaluate_wave3_post_feedback_regression() -> dict[str, Any]:
    """Replay locked 144-case Wave 3 corpus strictly under POST_FEEDBACK_DEVELOPMENT_REGRESSION."""
    w3_tools = WAVE3_WORKTREE / "tools"
    if str(w3_tools) not in sys.path:
        sys.path.insert(0, str(w3_tools))
    import evaluate_holdout_wave3 as EW3
    from app.simulation.geometry_functions import engine, planner, registry
    from app.ai.adapter4_route import (
        ADAPTER_V4_VERSION,
        build_adapter4_response,
        run_typed_fact_next_v2_route,
    )

    w3_corpus_path = WAVE3_WORKTREE / "inputs" / "holdout-wave3.json"
    w3_oracle_path = WAVE3_WORKTREE / "oracle" / "expected.json"
    w3_hist_track_a_path = WAVE3_WORKTREE / "results" / "scored-run-1" / "track-a.json"
    tax = json.loads((WAVE3_WORKTREE / "refusal-taxonomy.json").read_text(encoding="utf-8"))

    w3_corpus = json.loads(w3_corpus_path.read_text(encoding="utf-8"))
    w3_oracle = json.loads(w3_oracle_path.read_text(encoding="utf-8"))
    w3_hist = json.loads(w3_hist_track_a_path.read_text(encoding="utf-8"))
    hist_by_id = {c["id"]: c for c in w3_hist["cases"]}
    oracles_by_id = w3_oracle["cases"]

    scored_cases = [
        EW3.score_case(
            c,
            oracles_by_id.get(c["id"]),
            tax,
            route_fn=run_typed_fact_next_v2_route,
            adapter_fn=build_adapter4_response,
        )
        for c in w3_corpus["cases"]
    ]
    pos = [x for x in scored_cases if x["expected"] == "SERVE"]
    neg = [x for x in scored_cases if x["expected"] == "REFUSE"]

    transitions = []
    for x in scored_cases:
        h = hist_by_id[x["id"]]
        if (h["outcome"], h["code"]) != (x["outcome"], x["code"]):
            transitions.append({
                "id": x["id"],
                "stratum": x["stratum"],
                "family": x["family"],
                "plane_relation": x["plane_relation"],
                "question_type": x["question_type"],
                "before_outcome": h["outcome"],
                "before_code": h["code"],
                "after_outcome": x["outcome"],
                "after_code": x["code"],
                "secondary_defect_cluster": SECONDARY_DEFECT_MAP.get(x["id"]),
            })

    return {
        "task": "HYBRID_V2_W3_F1_CROSS_SENTENCE_PLANE_GROUNDING",
        "evidence_classification": "POST_FEEDBACK_DEVELOPMENT_REGRESSION",
        "not_an_independent_blind_holdout": True,
        "locked_wave3_corpus_sha256": _sha256_file(w3_corpus_path),
        "locked_wave3_oracle_sha256": _sha256_file(w3_oracle_path),
        "versions": {
            "registry_version": registry.REGISTRY_VERSION,
            "planner_version": planner.PLANNER_VERSION,
            "engine_version": engine.ENGINE_VERSION,
            "adapter_version": ADAPTER_V4_VERSION,
            "certificate_version": engine.PLANE_SECTION_CERTIFICATE_VERSION,
            "allow_live_ai": os.environ.get("ALLOW_LIVE_AI"),
        },
        "historical_wave3_baseline": {
            "positive_served_correct": 20,
            "positive_false_refusal": 52,
            "negative_refused": 72,
            "negative_correct_reason": 60,
            "wrong_served": 0,
        },
        "post_feedback_regression_summary": {
            "total_cases": len(scored_cases),
            "positive_total": len(pos),
            "positive_served_correct": sum(1 for x in pos if x["outcome"] == "SERVED_CORRECT"),
            "positive_false_refusal": sum(1 for x in pos if x["outcome"] == "FALSE_REFUSAL"),
            "positive_wrong_served": sum(1 for x in pos if x["outcome"] == "WRONG_SERVED"),
            "positive_by_stratum": {
                st: {
                    "total": sum(1 for x in pos if x["stratum"] == st),
                    "served_correct": sum(1 for x in pos if x["stratum"] == st and x["outcome"] == "SERVED_CORRECT"),
                    "false_refusal": sum(1 for x in pos if x["stratum"] == st and x["outcome"] == "FALSE_REFUSAL"),
                }
                for st in ("P-B", "P-A")
            },
            "positive_by_question_type": {
                qt: {
                    "total": sum(1 for x in pos if x["question_type"] == qt),
                    "served_correct": sum(1 for x in pos if x["question_type"] == qt and x["outcome"] == "SERVED_CORRECT"),
                    "false_refusal": sum(1 for x in pos if x["question_type"] == qt and x["outcome"] == "FALSE_REFUSAL"),
                }
                for qt in ("section_only", "area_only", "section_and_area")
            },
            "w3_f1_remaining_source_object_mismatch": sum(
                1 for x in pos if x["id"] in W3_F1_CASE_IDS and x.get("code") == "SOURCE_OBJECT_MISMATCH"
            ),
            "negative_total": len(neg),
            "negative_refused": sum(1 for x in neg if not x["served"]),
            "negative_correct_reason": sum(1 for x in neg if x["outcome"] == "REFUSED_CORRECT_REASON"),
            "negative_reason_disagreement": sum(1 for x in neg if x["outcome"] == "REFUSED_REASON_DISAGREEMENT"),
            "negative_wrong_served": sum(1 for x in neg if x["outcome"] == "WRONG_SERVED"),
            "overall_wrong_served": sum(1 for x in scored_cases if x["outcome"] == "WRONG_SERVED"),
            "machine_id_leak_cases": [
                x["id"] for x in scored_cases if x.get("machine_id_leaks")
            ],
            "source_identity_leak_cases": [
                x["id"] for x in scored_cases if x.get("source_identity_leaks")
            ],
        },
        "transitions_from_historical_wave3": transitions,
        "cases": scored_cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("red", "green"), required=True)
    args = parser.parse_args()

    inputs_dir = RUN_DIR / "inputs"
    results_dir = RUN_DIR / "results"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    dev_path = inputs_dir / "development.json"
    oracle_path = inputs_dir / "oracle.json"

    if args.mode == "red" or not dev_path.exists() or not oracle_path.exists():
        dev_doc, oracle_doc = build_development_and_oracle()
        dev_path.write_text(json.dumps(dev_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        oracle_path.write_text(json.dumps(oracle_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        dev_doc = json.loads(dev_path.read_text(encoding="utf-8"))
        oracle_doc = json.loads(oracle_path.read_text(encoding="utf-8"))

    if args.mode == "red":
        red_res = evaluate_corpus(dev_doc, oracle_doc, phase="RED_BEFORE")
        (results_dir / "red-before.json").write_text(
            json.dumps(red_res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(red_res["summary"], ensure_ascii=False, indent=2))
    else:
        green_res = evaluate_corpus(dev_doc, oracle_doc, phase="GREEN_AFTER")
        (results_dir / "green-after.json").write_text(
            json.dumps(green_res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        w3_reg = evaluate_wave3_post_feedback_regression()
        (results_dir / "wave3-post-feedback-regression.json").write_text(
            json.dumps(w3_reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print("=== GREEN DEVELOPMENT SUMMARY ===")
        print(json.dumps(green_res["summary"], ensure_ascii=False, indent=2))
        print("=== WAVE 3 POST-FEEDBACK REGRESSION SUMMARY ===")
        print(json.dumps(w3_reg["post_feedback_regression_summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
