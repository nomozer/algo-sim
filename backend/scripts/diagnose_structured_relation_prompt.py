# -*- coding: utf-8 -*-
"""CHẨN ĐOÁN OFFLINE: vì sao `analyze` không khai quan hệ vuông góc của ĐÁY.

`ANALYZE_STRUCTURED_RELATION_PROMPT_DIAGNOSIS` (2026-09-21).
**0 lượt gọi model · 0 request mạng.**

─── CÂU HỎI ────────────────────────────────────────────────────────────────

Lượt live `STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_VALIDATION` cho thấy mô
hình khai đúng `line(S,A) ⟂ plane(A,B,C)` nhưng **không** khai
`line(A,B) ⟂ line(A,C)`, trong khi đề viết *"ABC là tam giác vuông tại A"* và
chính mô hình đã tạo mục dữ kiện `abc_tam_giac_vuong_tai_a`.

Wave này phân loại nguyên nhân, KHÔNG sửa gì.

─── THỨ NÀY KHÔNG ĐƯỢC LÀM, VÀ CÓ TEST CANH ────────────────────────────────

① Không đọc, không phục hồi, không tái tạo **đầu ra thô** của mô hình. Chỉ đọc
   bản RÚT GỌN đã commit ở wave trước.
② Không sửa artifact live cũ. `LIVE_EVIDENCE_INTEGRITY` băm lại toàn bộ và so
   với blob trong Git.
③ Không sửa prompt/schema thật. Phép ghép luật đề xuất chạy **trong bộ nhớ**.
④ Không khẳng định nhân quả từ MỘT mẫu. Mọi phát biểu dùng đúng ba từ khoá:
   `ASSOCIATED_WITH` · `SUPPORTED_BY_CURRENT_EVIDENCE` · `NOT_CAUSALLY_ESTABLISHED`.

─── RANH GIỚI NGỮ NGHĨA LÀ SẢN PHẨM CHÍNH ──────────────────────────────────

Khoảng trống thật không nằm ở *"mô hình quên"* mà ở chỗ prompt hiện chỉ có HAI
ngăn — *đề NÓI* và *bạn TỰ SUY* — còn *"tam giác vuông tại A"* rơi vào giữa.
`SEMANTIC_NORMALIZATION_POLICY` dựng BỐN lớp không chồng lấn để câu hỏi ấy có
chỗ trả lời.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

GOC = Path(__file__).resolve().parents[1]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

WAVE = "ANALYZE_STRUCTURED_RELATION_PROMPT_DIAGNOSIS"
DIAG_VERSION = "structured-relation-prompt-diagnosis/1"

BASE = REPO / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene"
LIVE = BASE / "structured-relation-analyze-live"
RA = BASE / "structured-relation-prompt-diagnosis"

PROMPT_FILE = GOC / "app" / "ai" / "skills" / "geometry_analyze.md"
PROMPT_REL = "backend/app/ai/skills/geometry_analyze.md"

#: Artifact của lượt live phải BẤT BIẾN. Danh sách ĐÓNG — thiếu tệp là lỗi.
LIVE_ARTIFACTS = (
    "LIVE_CASE_MANIFEST.json", "GROUND_TRUTH_REGISTRATION.json",
    "PRECHECK.json", "LAUNCHER_OFFLINE_PROOF.json",
    "ANALYZE_LIVE_RESULT_REDACTED.json", "REQUEST_IDENTITY.json",
    "REQUEST_BUDGET_PROOF.json", "STRUCTURED_RELATION_COMPARISON.json",
    "PROVENANCE_RESOLUTION_PROOF.json", "FACT_GRAPH_RESULT_REDACTED.json",
    "COMPILER_DOWNSTREAM_RESULT.json", "TOKEN_USAGE.json", "SECRET_SCAN.json",
)
LIVE_REPORT = REPO / "docs" / "STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_VALIDATION.md"

#: Nhãn điểm của ca live. Luật đề xuất KHÔNG được nhắc tới chúng — nếu có, nó
#: đã vá một ca chứ không vá một lớp.
NHAN_CA_LIVE = ("S.ABC", "(ABC)", "ABC", "SA", "AB", "AC", "BC")


def _sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8") if isinstance(b, str) else b).hexdigest()


def _git(*a: str) -> str:
    """Chạy git và giải mã UTF-8 TƯỜNG MINH.

    `text=True` để Python chọn codec theo locale — trên Windows là `cp1252`, và
    một blob tiếng Việt làm nó ném `UnicodeDecodeError`. Đã cắn một lần ở đây.
    """
    r = subprocess.run(("git", *a), capture_output=True, cwd=str(REPO))
    return (r.stdout or b"").decode("utf-8", "replace").strip()


def _git_blob(sha: str) -> bytes:
    """Nội dung THÔ của một blob — không qua codec nào."""
    r = subprocess.run(("git", "cat-file", "blob", sha), capture_output=True,
                       cwd=str(REPO))
    return r.stdout or b""


# ══════════════════════════════════════════════════════════════════════════
# §2 · BẤT BIẾN BẰNG CHỨNG LIVE
# ══════════════════════════════════════════════════════════════════════════
def live_evidence_integrity() -> dict[str, Any]:
    """Băm lại artifact live và so với BLOB trong Git, không so với trí nhớ.

    So hai chiều có chủ đích: `sha256_worktree` bắt sửa tay trên đĩa;
    `blob_matches_head` bắt sửa đã commit. Một chiều thôi thì mất một nửa.
    """
    muc: list[dict[str, Any]] = []
    for ten in LIVE_ARTIFACTS:
        p = LIVE / ten
        rel = f"docs/evaluation/geometry/photo-problem-to-scene/structured-relation-analyze-live/{ten}"
        blob_head = _git("rev-parse", f"HEAD:{rel}")
        blob_now = _git("hash-object", "--", str(p)) if p.exists() else ""
        muc.append({
            "file": ten, "exists": p.exists(),
            "sha256_worktree": _sha(p.read_bytes()) if p.exists() else None,
            "sha256_blob_at_head": _sha(_git_blob(blob_head)) if blob_head else None,
            "git_blob_at_head": blob_head or None,
            "git_blob_worktree": blob_now or None,
            "blob_matches_head": bool(blob_head) and blob_head == blob_now,
        })
    rel_bc = "docs/STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_VALIDATION.md"
    bh, bn = _git("rev-parse", f"HEAD:{rel_bc}"), _git("hash-object", "--", str(LIVE_REPORT))
    muc.append({
        "file": rel_bc, "exists": LIVE_REPORT.exists(),
        "sha256_worktree": _sha(LIVE_REPORT.read_bytes()) if LIVE_REPORT.exists() else None,
        "sha256_blob_at_head": _sha(_git_blob(bh)) if bh else None,
        "git_blob_at_head": bh or None, "git_blob_worktree": bn or None,
        "blob_matches_head": bool(bh) and bh == bn,
    })
    return {
        "WAVE": WAVE,
        "_LUAT": "Wave chẩn đoán KHÔNG được sửa bằng chứng của wave đo.",
        "ARTIFACT_COUNT": len(muc),
        "ALL_PRESENT": all(m["exists"] for m in muc),
        "ALL_UNCHANGED_SINCE_HEAD": all(m["blob_matches_head"] for m in muc),
        "HISTORICAL_REPORT_CHANGED": not all(m["blob_matches_head"] for m in muc),
        "ITEMS": muc,
    }


# ══════════════════════════════════════════════════════════════════════════
# §3 · AUDIT PROMPT — chỉ vị trí và tóm tắt, KHÔNG chép nguyên văn
# ══════════════════════════════════════════════════════════════════════════
#: Nhóm từ khoá phải đi tìm. Khoá = chủ đề, giá trị = regex (không phân biệt hoa/thường).
NHOM_TU_KHOA: dict[str, str] = {
    "quan_he_phat_bieu_truc_tiep": r"quan hệ đề NÓI|đã ghi thành câu",
    "quan_he_GIVEN": r"đề cho|ĐỀ CHO|đề NÓI",
    "quan_he_DERIVED": r"hệ tự suy|tự suy",
    "cam_suy_dien": r"tự suy|đừng liệt kê|Chỉ khai quan hệ đề NÓI",
    "tam_giac_vuong": r"tam giác vuông|vuông tại",
    "goc_vuong": r"góc vuông",
    "goc_90": r"90\s*°|90 độ",
    "perpendicular_lines": r"perpendicular_lines",
    "perpendicular_line_plane": r"perpendicular_line_plane",
    "source_fact_id": r"source_fact_id",
    "model_assumption": r"model_assumption",
    "he_qua_duong_vuong_goc_mat": r"Hệ quả",
    "chuan_hoa_theo_dinh_nghia": r"chuẩn ho[áa] theo định nghĩa|theo định nghĩa|tương đương",
}


def prompt_instruction_audit() -> dict[str, Any]:
    raw = PROMPT_FILE.read_bytes()
    van = raw.decode("utf-8")
    # Băm theo bản LF — đúng thứ `load_skill` trả về và đúng thứ được gửi đi.
    lf = van.replace("\r\n", "\n")
    dong = lf.split("\n")

    hits: dict[str, list[dict[str, Any]]] = {}
    for chu_de, mau in NHOM_TU_KHOA.items():
        r = re.compile(mau, re.IGNORECASE)
        hits[chu_de] = [
            {"rule_id": f"{Path(PROMPT_REL).name}:L{i}",
             "line": i,
             # TÓM TẮT NGẮN, không chép cả dòng vào artifact ngoài 90 ký tự.
             "excerpt": d.strip()[:90]}
            for i, d in enumerate(dong, 1) if r.search(d)
        ]

    co_dinh_nghia = bool(hits["tam_giac_vuong"] or hits["goc_vuong"]
                         or hits["goc_90"] or hits["chuan_hoa_theo_dinh_nghia"])

    return {
        "WAVE": WAVE,
        "FILE": PROMPT_REL,
        "SHA256_LF": _sha(lf),
        "BYTES_LF": len(lf.encode("utf-8")),
        "LINE_COUNT": len(dong),
        "_KHONG_CHEP_NGUYEN_VAN": "Artifact chỉ giữ vị trí + trích ≤90 ký tự mỗi dòng khớp.",
        "MODEL_FACING_SURFACE_OF_ANALYZE": {
            "prompt": PROMPT_REL,
            "schema": "analyze_schema_for('hinh_hoc')",
            "grammar_card_attached": False,
            "_BANG_CHUNG": "grammar_card() chỉ được ghép trong stage_semantic_program "
                           "(pipeline.py ~L360); stage_semantic_analyze chỉ dùng "
                           "load_skill(...) + schema.",
        },
        "KEYWORD_HITS": hits,

        "A_YEU_CAU_CHUAN_HOA_TAM_GIAC_VUONG": {
            "answer": "NO",
            "evidence": "0 dòng khớp 'tam giác vuông|vuông tại|góc vuông|90°' "
                        "trong toàn bộ prompt.",
            "verdict": "PROMPT_KHONG_YEU_CAU",
        },
        "B_PHAN_BIET_CHUAN_HOA_VS_SUY_LUAN": {
            "answer": "NO",
            "evidence": "Prompt chỉ có HAI ngăn: 'quan hệ đề NÓI' (L36) và "
                        "'đề KHÔNG nói mà bạn tự suy ⇒ model_assumption=true' (L34). "
                        "Không có ngăn thứ ba cho phép viết lại một tính chất theo "
                        "định nghĩa mà vẫn là GIVEN.",
            "verdict": "PROMPT_KHONG_PHAN_BIET",
        },
        "C_VI_DU_CHI_DUNG_BIEU_THUC_TRUC_TIEP": {
            "answer": "YES",
            "evidence": "Ví dụ quan hệ ở L17 là `SA ⊥ (ABCD)`, `ABCD là hình vuông`, "
                        "`M là trung điểm AB`. Mục quan hệ (L26–37) chỉ nói tới "
                        "'quan hệ vuông góc ĐÃ GHI THÀNH CÂU ở trên' — không ví dụ nào "
                        "cho thấy một vị từ về LOẠI HÌNH được viết lại thành quan hệ.",
            "note": "`ABCD là hình vuông` XUẤT HIỆN như input_fact nhưng KHÔNG "
                    "xuất hiện như nguồn của một `perpendicular_lines`.",
            "verdict": "PROMPT_CHI_MINH_HOA_BIEU_THUC_TRUC_TIEP",
        },
        "D_CAM_SUY_DIEN_CO_THE_NUOT_CHUAN_HOA": {
            "answer": "AMBIGUOUS",
            "evidence": "L34 buộc `model_assumption=true` cho mọi thứ 'đề KHÔNG nói mà "
                        "bạn tự suy', và L36 nói 'Chỉ khai quan hệ đề NÓI'. Đề nói "
                        "'tam giác vuông tại A', KHÔNG nói 'AB ⟂ AC'. Đọc theo mặt chữ, "
                        "prompt CHO PHÉP xếp phép viết lại ấy vào ngăn 'tự suy'.",
            "he_qua_neu_doc_nhu_vay": "Quan hệ phải mang model_assumption=true ⇒ "
                                      "`dung_duoc_cho_tang_dung()` = false ⇒ vô dụng cho "
                                      "tầng dựng, mà L35 lại cảnh báo 'khai gian thì cả "
                                      "bài sai'. Cả hai lối đều dẫn tới KHÔNG khai.",
            "verdict": "PROMPT_MO_HO",
            "_KY_LUAT": "Đây là phát biểu về VĂN BẢN PROMPT, không phải về điều mô hình "
                        "'nghĩ'. Không có bằng chứng nào về trạng thái nội tại của mô hình.",
        },
        "TOM_TAT": {
            "PROMPT_EXPLICITLY_COVERS_DEFINITIONAL_NORMALIZATION": co_dinh_nghia,
            "PROMPT_GIVEN_DERIVED_BOUNDARY": "TWO_CLASS_ONLY (đề NÓI / tự suy)",
            "PROMPT_COVERS_LINE_PLANE_CONSEQUENCES": bool(hits["he_qua_duong_vuong_goc_mat"]),
        },
    }


# ══════════════════════════════════════════════════════════════════════════
# §4 · SCHEMA CÓ BIỂU DIỄN ĐƯỢC QUAN HỆ CÒN THIẾU KHÔNG
# ══════════════════════════════════════════════════════════════════════════
def schema_capability_audit() -> dict[str, Any]:
    """Không suy từ việc đọc schema — DỰNG THẬT một hợp đồng rồi chạy hết tầng."""
    from app.simulation.semantic_program.analyze_contract import (
        analyze_schema_for, build_request_contract,
    )
    from app.simulation.semantic_program.structured_relations import (
        RELATION_KINDS, chuan_hoa_duong, kiem_va_chuan_hoa,
    )
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.geometry_compiler import contract_adapter as A
    import run_structured_relation_analyze_live as LIVE_RUNNER

    de = LIVE_RUNNER.de_bai(LIVE_RUNNER.doc_manifest())
    schema = analyze_schema_for("hinh_hoc")

    # Payload tái dựng ĐÚNG hình dạng live, cộng thêm quan hệ còn thiếu — và
    # KHÔNG lấy từ đầu ra thô của mô hình: `source_fact_id` lấy từ bản rút gọn
    # đã commit, các mục còn lại dựng lại từ chính đề bài đã đóng băng.
    payload = {
        "input_facts": [
            {"id": "abc_tam_giac_vuong_tai_a", "label": "ABC là tam giác vuông tại A",
             "values": ["ABC là tam giác vuông tại A"]},
            {"id": "ab_bang_3", "label": "AB", "values": ["3"]},
            {"id": "ac_bang_4", "label": "AC", "values": ["4"]},
            {"id": "sa_vuong_goc_abc", "label": "SA vuông góc với mặt phẳng (ABC)",
             "values": ["SA ⊥ (ABC)"]},
            {"id": "sa_bang_5", "label": "SA", "values": ["5"]},
        ],
        "obligations": [{"kind": "volume", "container": "S.ABC",
                         "witness": "the_volume_of_s_abc"}],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "C"],
             "source_fact_id": "abc_tam_giac_vuong_tai_a", "model_assumption": False},
            {"kind": "perpendicular_line_plane", "line": ["S", "A"],
             "plane": ["A", "B", "C"], "source_fact_id": "sa_vuong_goc_abc",
             "model_assumption": False},
        ],
    }
    hd = build_request_contract(payload, problem_text=de, domain="hinh_hoc")
    kq = kiem_va_chuan_hoa(hd)
    thieu = next((q for q in kq.relations if q.kind == "perpendicular_lines"), None)

    ka = A.build_fact_graph(hd)
    el = C.danh_gia_eligibility(ka.graph) if ka.graph is not None else None

    # `AB ≡ BA` — chuẩn hoá hai chiều phải trùng.
    doi_xung = chuan_hoa_duong(("A", "B")) == chuan_hoa_duong(("B", "A"))

    kiem = {
        "RELATION_KIND_EXISTS": "perpendicular_lines" in RELATION_KINDS,
        "SCHEMA_ENUM_ALLOWS_KIND": "perpendicular_lines" in (
            schema["properties"]["geometric_relations"]["items"]
            ["properties"]["kind"]["enum"]),
        "ENDPOINT_ARITY_VALID": thieu is not None and len(thieu.args) == 4,
        "AB_EQUIV_BA": doi_xung,
        "SOURCE_FACT_ID_CAN_POINT_TO_TRIANGLE_FACT":
            thieu is not None and thieu.source_fact_id == "abc_tam_giac_vuong_tai_a"
            and hd.fact("abc_tam_giac_vuong_tai_a") is not None,
        "MODEL_ASSUMPTION_CAN_STAY_FALSE": thieu is not None and not thieu.model_assumption,
        "PYDANTIC_PARSE_PASS": hd is not None and len(hd.geometric_relations) == 2,
        "REQUEST_CONTRACT_VALIDATION_PASS": kq.hop_le,
        "FACT_GRAPH_ACCEPTS_RELATION": ka.status == "VALID" and any(
            f.kind == "perpendicular_lines" and f.status == "GIVEN"
            for f in (ka.graph.facts if ka.graph else ())),
        "COMPILER_PASSES_BASE_PERPENDICULAR_BRANCH":
            el is not None and el.status == "SUPPORTED",
    }
    return {
        "WAVE": WAVE,
        "_PHUONG_PHAP": "Dựng hợp đồng THẬT rồi chạy Pydantic → chuẩn hoá → FactGraph → "
                        "eligibility. Không đọc schema rồi suy.",
        "_KHONG_LAY_TU_DAU_RA_THO": "Payload dựng lại từ đề đã đóng băng; chỉ `source_fact_id` "
                                    "lấy từ bản RÚT GỌN đã commit của lượt live.",
        "CANONICAL_ARGS_OBSERVED": list(thieu.args) if thieu else None,
        "COMPILER_ELIGIBILITY_WITH_RELATION": el.status if el else None,
        "CHECKS": kiem,
        "SCHEMA_CAPABILITY_FOR_MISSING_RELATION":
            "PRESENT" if all(kiem.values()) else "ABSENT",
    }


# ══════════════════════════════════════════════════════════════════════════
# §5 · CHÍNH SÁCH NGỮ NGHĨA BỐN LỚP
# ══════════════════════════════════════════════════════════════════════════
LOP_NGU_NGHIA: dict[str, dict[str, Any]] = {
    "EXPLICIT_SURFACE_RELATION": {
        "dinh_nghia": "Đề phát biểu THẲNG quan hệ giữa hai đối tượng hình học.",
        "vi_du": ["AB vuông góc AC", "AB ⟂ AC", "góc BAC bằng 90°"],
        "phai_thanh": "relation GIVEN",
        "model_assumption": False,
    },
    "DEFINITIONAL_NORMALIZATION": {
        "dinh_nghia": "Đề phát biểu một TÍNH CHẤT/LOẠI HÌNH mà định nghĩa của nó CHỨA "
                      "quan hệ ấy. Viết lại là phép DỊCH tương đương, không thêm thông tin.",
        "vi_du": ["tam giác ABC vuông tại A", "ABC là tam giác vuông ở A",
                  "tam giác ABC có góc A vuông"],
        "phai_thanh": "relation GIVEN",
        "model_assumption": False,
        "_VI_SAO_VAN_LA_GIVEN": "Không dùng thêm một định lý nào. 'Vuông tại A' VÀ "
                                "'AB ⟂ AC' là hai cách viết của cùng một mệnh đề.",
    },
    "LOGICAL_DERIVATION": {
        "dinh_nghia": "Quan hệ chỉ có được khi ÁP một định lý lên một quan hệ khác.",
        "vi_du": ["SA ⟂ (ABC) ⇒ SA ⟂ AB", "⇒ SA ⟂ AC", "⇒ SA ⟂ BC"],
        "phai_thanh": "FactGraph sinh DERIVED, có parent proof",
        "model_khong_duoc_khai": True,
    },
    "LAYOUT_OR_CONSTRUCTION_ASSUMPTION": {
        "dinh_nghia": "Lựa chọn TRÌNH BÀY của tầng dựng, đề không nói.",
        "vi_du": ["A = (0,0,0)", "đặt AB trên trục Ox", "mặt phẳng đáy tại z = 0"],
        "phai_thanh": "LAYOUT_DERIVED, không bao giờ là dữ kiện đề bài",
        "model_khong_duoc_khai": True,
    },
}


def semantic_normalization_policy() -> dict[str, Any]:
    return {
        "WAVE": WAVE,
        "_MUC_DICH": "Prompt hiện có HAI ngăn; khoảng trống nằm đúng ở chỗ không có "
                     "ngăn thứ ba. Bốn lớp dưới đây KHÔNG chồng lấn.",
        "CLASSES": LOP_NGU_NGHIA,
        "GIVEN_CLASSES": ["EXPLICIT_SURFACE_RELATION", "DEFINITIONAL_NORMALIZATION"],
        "NOT_MODEL_DECLARED_CLASSES": ["LOGICAL_DERIVATION",
                                       "LAYOUT_OR_CONSTRUCTION_ASSUMPTION"],
        "RANH_GIOI_QUYET_DINH": (
            "Có phải áp một ĐỊNH LÝ để ra quan hệ không? Không ⇒ chuẩn hoá theo "
            "định nghĩa (GIVEN). Có ⇒ suy luận (DERIVED, của FactGraph)."),
    }


# ══════════════════════════════════════════════════════════════════════════
# §6 · MA TRẬN CÁCH DIỄN ĐẠT
# ══════════════════════════════════════════════════════════════════════════
#: `covered_by_current_prompt`: YES chỉ khi prompt có chỉ dẫn ÁP ĐƯỢC cho cách
#: viết ấy. AMBIGUOUS khi chỉ dẫn tồn tại nhưng điều kiện kích hoạt không rõ.
MA_TRAN_CACH_VIET: tuple[dict[str, Any], ...] = (
    {"id": "W01", "wording": "AB vuông góc AC", "ngon_ngu": "vi",
     "semantic_class": "EXPLICIT_SURFACE_RELATION",
     "expected_relation": {"kind": "perpendicular_lines", "args": ["A", "B", "A", "C"]},
     "expected_source_fact": "mục input_fact chở chính câu ấy",
     "given_or_derived": "GIVEN",
     "covered_by_current_prompt": "YES",
     "current_prompt_evidence": "L28 'Mỗi quan hệ vuông góc đã ghi thành câu ở trên'",
     "covered_by_proposed_delta": "YES"},
    {"id": "W02", "wording": "AB ⟂ AC", "ngon_ngu": "vi",
     "semantic_class": "EXPLICIT_SURFACE_RELATION",
     "expected_relation": {"kind": "perpendicular_lines", "args": ["A", "B", "A", "C"]},
     "expected_source_fact": "mục input_fact chở chính câu ấy",
     "given_or_derived": "GIVEN",
     "covered_by_current_prompt": "YES",
     "current_prompt_evidence": "L28; ký hiệu ⊥ dùng ngay trong ví dụ L17",
     "covered_by_proposed_delta": "YES"},
    {"id": "W03", "wording": "Góc BAC bằng 90°", "ngon_ngu": "vi",
     "semantic_class": "EXPLICIT_SURFACE_RELATION",
     "expected_relation": {"kind": "perpendicular_lines", "args": ["A", "B", "A", "C"]},
     "expected_source_fact": "mục input_fact chở chính câu ấy",
     "given_or_derived": "GIVEN",
     "covered_by_current_prompt": "AMBIGUOUS",
     "current_prompt_evidence": "L28 kích hoạt theo cụm 'quan hệ vuông góc'; "
                                "'bằng 90°' không chứa cụm ấy. 0 dòng nhắc '90'.",
     "covered_by_proposed_delta": "YES"},
    {"id": "W04", "wording": "Tam giác ABC vuông tại A", "ngon_ngu": "vi",
     "semantic_class": "DEFINITIONAL_NORMALIZATION",
     "expected_relation": {"kind": "perpendicular_lines", "args": ["A", "B", "A", "C"]},
     "expected_source_fact": "abc_tam_giac_vuong_tai_a",
     "given_or_derived": "GIVEN",
     "covered_by_current_prompt": "NO",
     "current_prompt_evidence": "0 dòng nhắc 'tam giác vuông|vuông tại'; L34/L36 đẩy "
                                "cách viết này về ngăn 'tự suy'.",
     "covered_by_proposed_delta": "YES",
     "la_ca_live": True},
    {"id": "W05", "wording": "ABC là tam giác vuông ở A", "ngon_ngu": "vi",
     "semantic_class": "DEFINITIONAL_NORMALIZATION",
     "expected_relation": {"kind": "perpendicular_lines", "args": ["A", "B", "A", "C"]},
     "expected_source_fact": "abc_tam_giac_vuong_tai_a",
     "given_or_derived": "GIVEN",
     "covered_by_current_prompt": "NO",
     "current_prompt_evidence": "như W04",
     "covered_by_proposed_delta": "YES"},
    {"id": "W06", "wording": "Tam giác ABC có góc A vuông", "ngon_ngu": "vi",
     "semantic_class": "DEFINITIONAL_NORMALIZATION",
     "expected_relation": {"kind": "perpendicular_lines", "args": ["A", "B", "A", "C"]},
     "expected_source_fact": "abc_tam_giac_vuong_tai_a",
     "given_or_derived": "GIVEN",
     "covered_by_current_prompt": "NO",
     "current_prompt_evidence": "như W04",
     "covered_by_proposed_delta": "YES"},
    {"id": "W07", "wording": "Hai cạnh góc vuông là AB và AC", "ngon_ngu": "vi",
     "semantic_class": "DEFINITIONAL_NORMALIZATION",
     "expected_relation": {"kind": "perpendicular_lines", "args": ["A", "B", "A", "C"]},
     "expected_source_fact": "mục input_fact chở câu ấy",
     "given_or_derived": "GIVEN",
     "covered_by_current_prompt": "NO",
     "current_prompt_evidence": "0 dòng nhắc 'góc vuông' như một nguồn quan hệ.",
     "covered_by_proposed_delta": "YES"},
    {"id": "W08", "wording": "Triangle ABC is right-angled at A", "ngon_ngu": "en",
     "semantic_class": "DEFINITIONAL_NORMALIZATION",
     "expected_relation": {"kind": "perpendicular_lines", "args": ["A", "B", "A", "C"]},
     "expected_source_fact": "mục input_fact chở câu ấy",
     "given_or_derived": "GIVEN",
     "covered_by_current_prompt": "NO",
     "current_prompt_evidence": "như W04; prompt cũng không nói gì về đề tiếng Anh.",
     "covered_by_proposed_delta": "YES",
     "_GHI_CHU": "Ngoài phạm vi sản phẩm (đề tiếng Việt) — giữ để kiểm tính TỔNG QUÁT "
                 "của luật, không phải để mở phạm vi."},
    {"id": "W09", "wording": "Tam giác PMN vuông tại P", "ngon_ngu": "vi",
     "semantic_class": "DEFINITIONAL_NORMALIZATION",
     "expected_relation": {"kind": "perpendicular_lines", "args": ["M", "P", "N", "P"]},
     "expected_source_fact": "mục input_fact chở câu ấy",
     "given_or_derived": "GIVEN",
     "covered_by_current_prompt": "NO",
     "current_prompt_evidence": "như W04",
     "covered_by_proposed_delta": "YES",
     "_GHI_CHU": "Đổi nhãn — luật nào chỉ đúng với A/B/C là luật vá một ca."},
    {"id": "W10", "wording": "Cho hình chóp S.ABC. Biết SA ⊥ (ABC) và SA = 5. "
                             "Đáy ABC vuông tại A với AB = 3, AC = 4.",
     "ngon_ngu": "vi",
     "semantic_class": "DEFINITIONAL_NORMALIZATION",
     "expected_relation": {"kind": "perpendicular_lines", "args": ["A", "B", "A", "C"]},
     "expected_source_fact": "mục input_fact chở mệnh đề đáy vuông",
     "given_or_derived": "GIVEN",
     "covered_by_current_prompt": "NO",
     "current_prompt_evidence": "như W04",
     "covered_by_proposed_delta": "YES",
     "_GHI_CHU": "Đảo thứ tự câu của ca live — kiểm luật không phụ thuộc vị trí câu."},
    {"id": "W11", "wording": "SA vuông góc với mặt phẳng (ABC)", "ngon_ngu": "vi",
     "semantic_class": "EXPLICIT_SURFACE_RELATION",
     "expected_relation": {"kind": "perpendicular_line_plane",
                           "args": ["A", "S", "A", "B", "C"]},
     "expected_source_fact": "sa_vuong_goc_abc",
     "given_or_derived": "GIVEN",
     "covered_by_current_prompt": "YES",
     "current_prompt_evidence": "L28–30; đây là cách viết mô hình ĐÃ khai đúng ở lượt live.",
     "covered_by_proposed_delta": "YES",
     "la_ca_live": True},
    {"id": "W12", "wording": "SA ⟂ BC (hệ quả của SA ⊥ (ABC))", "ngon_ngu": "vi",
     "semantic_class": "LOGICAL_DERIVATION",
     "expected_relation": {"kind": "perpendicular_lines", "args": ["A", "S", "B", "C"]},
     "expected_source_fact": None,
     "given_or_derived": "DERIVED",
     "covered_by_current_prompt": "YES",
     "current_prompt_evidence": "L36–37 'Hệ quả … hệ tự suy, đừng liệt kê'",
     "covered_by_proposed_delta": "YES",
     "_GHI_CHU": "Luật đề xuất PHẢI giữ nguyên hành vi này — mô hình đã tuân đúng."},
    {"id": "W13", "wording": "Chọn A = (0,0,0), AB trên trục Ox", "ngon_ngu": "vi",
     "semantic_class": "LAYOUT_OR_CONSTRUCTION_ASSUMPTION",
     "expected_relation": None,
     "expected_source_fact": None,
     "given_or_derived": "NOT_A_PROBLEM_FACT",
     "covered_by_current_prompt": "YES",
     "current_prompt_evidence": "L39–41 'Hệ toạ độ KHÔNG phải dữ kiện'",
     "covered_by_proposed_delta": "YES"},
)


def wording_coverage_matrix() -> dict[str, Any]:
    def dem(khoa: str, gia: str) -> int:
        return sum(1 for m in MA_TRAN_CACH_VIET if m[khoa] == gia)

    return {
        "WAVE": WAVE,
        "_MUC_DICH": "Audit ĐỘ PHỦ CỦA CHỈ DẪN. KHÔNG phải mô phỏng xác suất Gemini — "
                     "không một ô nào ở đây do model sinh ra.",
        "FIXTURE_COUNT": len(MA_TRAN_CACH_VIET),
        "BY_CLASS": {c: sum(1 for m in MA_TRAN_CACH_VIET if m["semantic_class"] == c)
                     for c in LOP_NGU_NGHIA},
        "COVERED_BY_CURRENT_PROMPT": dem("covered_by_current_prompt", "YES"),
        "AMBIGUOUS_IN_CURRENT_PROMPT": dem("covered_by_current_prompt", "AMBIGUOUS"),
        "NOT_COVERED_BY_CURRENT_PROMPT": dem("covered_by_current_prompt", "NO"),
        "COVERED_BY_PROPOSED_DELTA": dem("covered_by_proposed_delta", "YES"),
        "FIXTURES": list(MA_TRAN_CACH_VIET),
    }


# ══════════════════════════════════════════════════════════════════════════
# §7 · ĐỐI CHIẾU VỚI ĐẦU RA LIVE (chỉ bản RÚT GỌN)
# ══════════════════════════════════════════════════════════════════════════
def live_output_diagnostic_mapping() -> dict[str, Any]:
    ss = json.loads((LIVE / "STRUCTURED_RELATION_COMPARISON.json").read_text(encoding="utf-8"))
    ds = json.loads((LIVE / "FACT_GRAPH_RESULT_REDACTED.json").read_text(encoding="utf-8"))
    pv = json.loads((LIVE / "PROVENANCE_RESOLUTION_PROOF.json").read_text(encoding="utf-8"))

    khai = {(r["kind"], tuple(r["canonical_args"])) for r in ss["RELATIONS"]}
    thieu = [{"kind": m["kind"], "args": m["args"]} for m in ss["MISSING_RELATIONS"]]
    fact_tam_giac = next(
        (f for f in ds["FACTS"]
         if f["source_fact_id"] and "tam_giac_vuong" in f["source_fact_id"]), None)

    return {
        "WAVE": WAVE,
        "_NGUON": "Chỉ các artifact RÚT GỌN đã commit. Không đọc, không phục hồi đầu ra thô.",
        "MODEL_DECLARED_LINE_PLANE": ("perpendicular_line_plane",
                                      ("A", "S", "A", "B", "C")) in khai,
        "MODEL_MISSED_BASE_PERPENDICULAR": thieu == [
            {"kind": "perpendicular_lines", "args": ["A", "B", "A", "C"]}],
        "MISSING_RELATION": thieu[0] if thieu else None,
        "MISSING_RELATION_SEMANTIC_CLASS": "DEFINITIONAL_NORMALIZATION",
        "SOURCE_FACT_FOR_TRIANGLE_EXISTS": fact_tam_giac is not None,
        "SOURCE_FACT_ID_OBSERVED": fact_tam_giac["source_fact_id"] if fact_tam_giac else None,
        "_BANG_CHUNG_SOURCE_FACT": "Mục dữ kiện tam giác vuông ĐÃ tồn tại và đã được "
                                   "dùng làm xuất xứ cho các fact độ dài — tức có sẵn "
                                   "chỗ để `source_fact_id` của quan hệ còn thiếu trỏ về.",
        "MISSING_RELATION_COULD_POINT_TO_THAT_FACT": fact_tam_giac is not None,
        "NO_EXTRA_DERIVED_AS_GIVEN": ss["EXTRA_DERIVED_AS_GIVEN_COUNT"] == 0,
        "NO_MODEL_ASSUMPTION": ss["MODEL_ASSUMPTION_COUNT"] == 0,
        "NO_UNKNOWN_REFERENCE": ss["POINT_REFERENCE_VALIDATION"] == "PASS"
                                and not ss["REJECTED_RELATION_CODES"],
        "PROVENANCE_RESOLUTION": pv["SOURCE_FACT_RESOLUTION"],
        "EVALUATOR_SCORED_MISSING_CORRECTLY": (
            ss["MISSING_RELATION_COUNT"] == 1
            and ss["CRITICAL_RELATION_ACCURACY"] == 0.5
            and ss["EXPECTED_RELATION_COUNT"] == 2),
        "COMPILER_REFUSED_ON_CORRECT_BRANCH": (
            ds["COMPILER_ELIGIBILITY"] == "UNSUPPORTED_STRUCTURED_RELATION_MISSING"
            and ds["COMPILER_ELIGIBILITY_REASON"] == "BASE_PERPENDICULAR_RELATION_MISSING"),
        "MODEL_OBEYED_CONSEQUENCE_RULE": ds["DERIVED_PERPENDICULAR_COUNT"] == 3
                                         and ds["DERIVED_PERPENDICULAR_MATCHES_GROUND_TRUTH"],
    }


# ══════════════════════════════════════════════════════════════════════════
# §8 · PHÂN LOẠI NGUYÊN NHÂN GỐC
# ══════════════════════════════════════════════════════════════════════════
def root_cause_classification(audit: dict, schema: dict, mapping: dict) -> dict[str, Any]:
    schema_present = schema["SCHEMA_CAPABILITY_FOR_MISSING_RELATION"] == "PRESENT"
    gt_dung = mapping["EVALUATOR_SCORED_MISSING_CORRECTLY"]
    source_co = mapping["SOURCE_FACT_FOR_TRIANGLE_EXISTS"]
    prompt_khong_yeu_cau = not audit["TOM_TAT"][
        "PROMPT_EXPLICITLY_COVERS_DEFINITIONAL_NORMALIZATION"]
    prompt_mo_ho = audit["D_CAM_SUY_DIEN_CO_THE_NUOT_CHUAN_HOA"]["verdict"] == "PROMPT_MO_HO"
    hanh_vi_khop = mapping["MODEL_MISSED_BASE_PERPENDICULAR"] and mapping[
        "MODEL_DECLARED_LINE_PLANE"]

    dk_prompt_gap = {
        "schema_bieu_dien_duoc": schema_present,
        "ground_truth_dung": gt_dung,
        "evaluator_dung": gt_dung,
        "source_fact_ton_tai": source_co,
        "prompt_khong_yeu_cau_hoac_mo_ho": prompt_khong_yeu_cau or prompt_mo_ho,
        "hanh_vi_live_phu_hop_voi_khoang_trong": hanh_vi_khop,
    }
    dk_noncompliance = {
        "prompt_da_yeu_cau_ro_va_tong_quat": not prompt_khong_yeu_cau and not prompt_mo_ho,
        "schema_ho_tro": schema_present,
        "source_fact_ton_tai": source_co,
        "model_van_khong_xuat": hanh_vi_khop,
    }
    dk_schema_gap = {"schema_khong_bieu_dien_duoc": not schema_present}
    dk_do_sai = {"ground_truth_hoac_evaluator_sai": not gt_dung}

    if all(dk_schema_gap.values()):
        nhan = "SCHEMA_CAPABILITY_GAP"
    elif all(dk_do_sai.values()):
        nhan = "EVALUATOR_OR_GROUND_TRUTH_ERROR"
    elif all(dk_prompt_gap.values()):
        nhan = "PROMPT_INSTRUCTION_GAP"
    elif all(dk_noncompliance.values()):
        nhan = "MODEL_NONCOMPLIANCE"
    else:
        nhan = "INDETERMINATE"

    return {
        "WAVE": WAVE,
        "ROOT_CAUSE_CLASSIFICATION": nhan,
        "CONDITIONS_PROMPT_INSTRUCTION_GAP": dk_prompt_gap,
        "CONDITIONS_MODEL_NONCOMPLIANCE": dk_noncompliance,
        "CONDITIONS_SCHEMA_CAPABILITY_GAP": dk_schema_gap,
        "CONDITIONS_EVALUATOR_OR_GROUND_TRUTH_ERROR": dk_do_sai,

        "CAUSALITY_STATUS": "NOT_CAUSALLY_ESTABLISHED",
        "EVIDENCE_STRENGTH": "SUPPORTED_BY_CURRENT_EVIDENCE",
        "RELATION_TO_BEHAVIOUR": "ASSOCIATED_WITH",
        "ROOT_CAUSE_CONFIDENCE": "SINGLE_OBSERVATION",
        "_KY_LUAT_PHAT_BIEU": [
            "n = 1. Một request KHÔNG dựng được quan hệ nhân quả.",
            "Phát biểu đúng: khoảng trống chỉ dẫn ASSOCIATED_WITH hành vi quan sát được,",
            "SUPPORTED_BY_CURRENT_EVIDENCE, và NOT_CAUSALLY_ESTABLISHED.",
            "Không có bằng chứng nào về trạng thái nội tại của mô hình; mọi phát biểu ở",
            "đây nói về VĂN BẢN PROMPT và về ĐẦU RA quan sát được.",
        ],
        "_LOAI_TRU": {
            "SCHEMA_CAPABILITY_GAP": "LOẠI — fixture thật parse PASS và eligibility "
                                     "thành SUPPORTED khi có quan hệ.",
            "EVALUATOR_OR_GROUND_TRUTH_ERROR": "LOẠI — quan hệ kỳ vọng đúng theo chính "
                                               "định nghĩa tam giác vuông; bộ chấm ghi "
                                               "missing = 1, accuracy = 0.5, khớp.",
            "MODEL_NONCOMPLIANCE": "KHÔNG kết luận — điều kiện 'prompt đã yêu cầu rõ' "
                                   "KHÔNG đạt, nên không đủ cơ sở quy cho mô hình.",
        },
    }


# ══════════════════════════════════════════════════════════════════════════
# §9 · LUẬT ĐỀ XUẤT — KHÔNG ÁP DỤNG
# ══════════════════════════════════════════════════════════════════════════
#: Chèn NGAY SAU gạch đầu dòng "Chỉ khai quan hệ đề NÓI…" để hai luật đứng cạnh
#: nhau: một luật mở (chuẩn hoá theo định nghĩa), một luật đóng (đừng liệt kê hệ quả).
NEO_CHEN = "  đường trong mặt phẳng ấy — hệ tự suy, đừng liệt kê."

LUAT_DE_XUAT = (
    "- Tính chất phát biểu bằng LOẠI HÌNH cũng là quan hệ đề NÓI. Đề viết *tam\n"
    "  giác PQR vuông tại P* thì khai `perpendicular_lines` cho `PQ` và `PR`,\n"
    "  `model_assumption` để `false`: đó là viết lại đúng điều đề đã nói bằng tên\n"
    "  đỉnh, không phải bạn tự suy. Cùng cách với *góc PQR bằng 90°*.\n"
)


def da_ap_dung() -> bool:
    """Luật đã nằm trong prompt THẬT chưa.

    Thêm ở `ANALYZE_DEFINITIONAL_NORMALIZATION_PROMPT_FIX` (2026-09-21). Trước
    đó hàm dưới luôn chèn thêm một bản; sau khi luật được áp thật, phép chèn ấy
    sinh BẢN THỨ HAI và mọi con số byte thành vô nghĩa (đo được: 5672 → 6033).
    Công cụ chẩn đoán phải biết mình đứng trước hay sau lượt sửa.
    """
    raw = PROMPT_FILE.read_text(encoding="utf-8").replace("\r\n", "\n")
    return LUAT_DE_XUAT.rstrip("\n") in raw


def proposed_prompt_delta() -> dict[str, Any]:
    raw = PROMPT_FILE.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert NEO_CHEN in raw, "neo chèn không còn trong prompt — luật đề xuất phải viết lại"
    ap = da_ap_dung()
    # Đã áp rồi thì "bản mô phỏng" CHÍNH LÀ prompt hiện tại — không chèn lần hai.
    mo_phong = raw if ap else raw.replace(
        NEO_CHEN, NEO_CHEN + "\n" + LUAT_DE_XUAT.rstrip("\n"), 1)

    nhan_lot = [n for n in NHAN_CA_LIVE if n in LUAT_DE_XUAT]
    return {
        "WAVE": WAVE,
        "APPLIED": ap,
        "_LUAT": ("Luật ĐÃ được áp ở `ANALYZE_DEFINITIONAL_NORMALIZATION_PROMPT_FIX` "
                  "(2026-09-21); bản mô phỏng ở đây bằng chính prompt hiện tại."
                  if ap else
                  "Wave chẩn đoán KHÔNG sửa prompt. Phép ghép chỉ chạy trong bộ nhớ."),
        "TARGET_FILE": PROMPT_REL,
        "INSERTION_ANCHOR": "ngay sau gạch đầu dòng 'Hệ quả … đừng liệt kê' (L36–37)",
        "_VI_SAO_DAT_O_DO": "Hai luật phải đứng cạnh nhau: một luật MỞ (chuẩn hoá theo "
                            "định nghĩa vẫn là GIVEN) và một luật ĐÓNG (đừng liệt kê hệ "
                            "quả). Tách xa nhau là mời đọc nhầm luật này thành luật kia.",
        "RULE_TEXT": LUAT_DE_XUAT,
        "RULE_BYTES": len(LUAT_DE_XUAT.encode("utf-8")),
        "PROMPT_BYTES_CURRENT": len(raw.encode("utf-8")),
        "PROMPT_BYTES_SIMULATED": len(mo_phong.encode("utf-8")),
        "PROMPT_SHA256_CURRENT": _sha(raw),
        "PROMPT_SHA256_SIMULATED": _sha(mo_phong),
        "TOKEN_ESTIMATE": "UNAVAILABLE",
        "_TOKEN_ESTIMATE_VI_SAO": "Kho không có tokenizer chính thức của Gemini. Ước lượng "
                                  "bằng heuristic là bịa một con số trông như đo được.",
        "GENERALITY": {
            "HARDCODES_LIVE_CASE_LABELS": bool(nhan_lot),
            "LEAKED_LABELS": nhan_lot,
            "USES_GENERIC_PLACEHOLDER": "PQR" in LUAT_DE_XUAT,
            "MENTIONS_COORDINATES": any(k in LUAT_DE_XUAT for k in ("toạ độ", "tọa độ", "(0,0,0)")),
            # Không quét chữ "tính" trần: luật mở đầu bằng "Tính chất", nên phép
            # quét ấy đạt vì lý do HOA/THƯỜNG chứ không vì luật đúng — một cổng
            # xanh nhờ may mắn thì không phải cổng.
            "ASKS_MODEL_TO_COMPUTE": any(
                k in LUAT_DE_XUAT.lower()
                for k in ("hãy tính", "tính thể tích", "tính toán", "đáp số",
                          "kết quả bằng", "giải bài")),
            "WOULD_MAKE_LINE_PLANE_CONSEQUENCES_GIVEN": "hệ quả" in LUAT_DE_XUAT.lower(),
            "COPIES_SCHEMA": "enum" in LUAT_DE_XUAT or "properties" in LUAT_DE_XUAT,
        },
        "REQUIRED_CHANGES_ELSEWHERE": {
            "SCHEMA_CHANGE_REQUIRED": False,
            "FACT_GRAPH_CHANGE_REQUIRED": False,
            "ADAPTER_CHANGE_REQUIRED": False,
            "COMPILER_CHANGE_REQUIRED": False,
            "_BANG_CHUNG": "SCHEMA_CAPABILITY_AUDIT chứng minh mọi tầng đã nhận được "
                           "quan hệ ấy khi nó có mặt.",
        },
        "IMPACT_IF_APPLIED": {
            "MODEL_FACING_SURFACE_CHANGED": True,
            "CACHE_VERSION_BUMP_REQUIRED": True,
            "_VI_SAO_BUMP": "Prompt đổi ⇒ cùng một đề có thể cho hợp đồng khác; cache "
                            "analyze khoá theo text+CACHE_VERSION nên không bump là hồi quy câm.",
            "CANDIDATE_REFREEZE_REQUIRED": True,
            "_VI_SAO_REFREEZE": "`backend/app` nằm trong MEASURED_SYSTEM_PATHS.",
            "LIVE_REVALIDATION_REQUIRED": True,
        },
    }


def prompt_delta_simulation_proof() -> dict[str, Any]:
    """Chứng minh phép ghép KHÔNG chạm đĩa và luật cũ còn nguyên."""
    truoc_bytes = PROMPT_FILE.read_bytes()
    d = proposed_prompt_delta()
    sau_bytes = PROMPT_FILE.read_bytes()
    raw = truoc_bytes.decode("utf-8").replace("\r\n", "\n")
    mo_phong = raw if d["APPLIED"] else raw.replace(
        NEO_CHEN, NEO_CHEN + "\n" + LUAT_DE_XUAT.rstrip("\n"), 1)
    return {
        "WAVE": WAVE,
        "FILE_UNTOUCHED_ON_DISK": truoc_bytes == sau_bytes,
        "FILE_SHA256_BEFORE": _sha(truoc_bytes),
        "FILE_SHA256_AFTER": _sha(sau_bytes),
        "SIMULATION_IS_IN_MEMORY_ONLY": True,
        "ANCHOR_FOUND_EXACTLY_ONCE": raw.count(NEO_CHEN) == 1,
        "EXISTING_CONSEQUENCE_RULE_PRESERVED": NEO_CHEN in mo_phong,
        "EXISTING_COORDINATE_RULE_PRESERVED": "Hệ toạ độ KHÔNG phải dữ kiện" in mo_phong,
        "DELTA_BYTES": d["PROMPT_BYTES_SIMULATED"] - d["PROMPT_BYTES_CURRENT"],
        "SIMULATED_SHA256": d["PROMPT_SHA256_SIMULATED"],
        "_KHONG_GHI_NGUYEN_VAN_PROMPT": "Artifact giữ băm và số byte, không giữ thân prompt.",
    }


# ══════════════════════════════════════════════════════════════════════════
# §11 · TRUY NGUYÊN CHÊNH LỆCH SỐ TEST
# ══════════════════════════════════════════════════════════════════════════
#: Lệnh đã dùng để lấy hai danh sách, ghi vào artifact để tái lập được.
LENH_THU_THAP = ("cd <worktree>/backend && PYTHONIOENCODING=utf-8 "
                 "<venv>/python.exe -m pytest -q --collect-only | grep '::'")


def doc_collection(p: Path) -> list[str]:
    return [d.strip() for d in p.read_text(encoding="utf-8").splitlines() if "::" in d]


def _tach(node: str) -> tuple[str, str, str]:
    """`file::ten[param]` → (file, tên hàm, param id)."""
    tep, _, con = node.partition("::")
    ten, _, tham = con.partition("[")
    return tep, ten, tham.rstrip("]")


def classify_test_collection(truoc: list[str], sau: list[str]) -> dict[str, Any]:
    """So theo NODE ID, không so theo số đếm.

    So số đếm thì `+28` là một con số và không ai biết 28 cái đó là gì — đúng
    cách mà hai test lạ đi lọt qua báo cáo trước. Mỗi node mới ở đây phải rơi
    vào một lớp có tên; còn `UNCLASSIFIED` là còn nợ.
    """
    t, s = set(truoc), set(sau)
    them, bot = sorted(s - t), sorted(t - s)
    tep_truoc = {_tach(n)[0] for n in t}
    ham_truoc = {(_tach(n)[0], _tach(n)[1]) for n in t}

    phan: list[dict[str, str]] = []
    for n in them:
        tep, ten, tham = _tach(n)
        if tep not in tep_truoc:
            lop = "NEW_TEST_FILE"
        elif (tep, ten) in ham_truoc and tham:
            lop = "PARAMETRIZE_EXPANSION"
        elif (tep, ten) in ham_truoc:
            lop = "SAME_FUNCTION_NEW_NODE"
        else:
            lop = "NEW_FUNCTION_IN_EXISTING_FILE"
        phan.append({"node_id": n, "file": tep, "function": ten,
                     "param_id": tham, "classification": lop})

    theo_lop: dict[str, int] = {}
    for p in phan:
        theo_lop[p["classification"]] = theo_lop.get(p["classification"], 0) + 1
    chua_ro = [p for p in phan if p["classification"] == "UNCLASSIFIED"]
    return {
        "WAVE": WAVE,
        "COLLECTION_COMMAND": LENH_THU_THAP,
        "_LUAT": "So NODE ID. Chỉ so tổng số là cách một chênh lệch đi lọt.",
        "COUNT_BEFORE": len(truoc), "COUNT_AFTER": len(sau),
        "COUNT_DELTA": len(sau) - len(truoc),
        "ADDED_COUNT": len(them), "REMOVED_COUNT": len(bot),
        "REMOVED_NODES": bot,
        "BY_CLASSIFICATION": theo_lop,
        "ADDED_NODES": phan,
        "ALL_ADDED_CLASSIFIED": not chua_ro,
        "DELTA_FULLY_EXPLAINED": (not chua_ro) and len(them) == len(sau) - len(truoc)
                                 and not bot,
    }


def test_count_discrepancy_classification(diff: dict[str, Any]) -> dict[str, Any]:
    """Giải thích ĐÚNG hai test mà phép trừ của báo cáo trước để lại."""
    par = [p for p in diff["ADDED_NODES"]
           if p["classification"] == "PARAMETRIZE_EXPANSION"]
    moi = [p for p in diff["ADDED_NODES"] if p["classification"] == "NEW_TEST_FILE"]
    tep_par = sorted({p["file"] for p in par})
    return {
        "WAVE": WAVE,
        "REPORTED_BEFORE_PASSED": 5539,
        "REPORTED_AFTER_PASSED": 5567,
        "REPORTED_NEW_FILE_TESTS": 26,
        "UNEXPLAINED_BY_SUBTRACTION": 2,
        "COLLECTED_BEFORE": diff["COUNT_BEFORE"],
        "COLLECTED_AFTER": diff["COUNT_AFTER"],
        "_HOA_GIAI_PASSED_VS_COLLECTED": (
            "Lượt chạy đầy đủ báo `passed + 1 skipped`. 5539 + 1 = 5540 = số node "
            "thu thập ở b6ec81b; 5567 + 1 = 5568 = số node ở da6ad17. Hai sổ khớp "
            "nhau, không có sai lệch đo."),
        "NEW_FILE_TEST_COUNT": len(moi),
        "PARAMETRIZE_EXPANSION_COUNT": len(par),
        "PARAMETRIZE_EXPANSION_FILES": tep_par,
        "PARAMETRIZE_EXPANSION_NODES": [p["node_id"] for p in par],
        "MECHANISM": (
            "Hai test trong `tests/semantic_program/test_domain_string.py` khai "
            "`@pytest.mark.parametrize(\"f\", sorted(_SCRIPTS.glob(\"*.py\")))` — chúng "
            "duyệt MỌI tệp `.py` trong `backend/scripts/`. Wave trước thêm ĐÚNG MỘT "
            "script, nên mỗi test nở thêm một node: +2."),
        "TEST_COUNT_DELTA_EXPLAINED": diff["DELTA_FULLY_EXPLAINED"],
        "CLASSIFICATION": ("FULLY_EXPLAINED" if diff["DELTA_FULLY_EXPLAINED"]
                           else "NOT_REPRODUCIBLE"),
        "HISTORICAL_REPORT_CHANGED": False,
        "_LOP_DINH_CHINH": (
            "Báo cáo lịch sử KHÔNG được sửa. Số 5539/5567 trong nó ĐÚNG; thứ thiếu "
            "chỉ là lời giải thích cho +2, và lời giải thích ấy nằm ở đây."),
        "_DU_BAO_CHO_WAVE_NAY": (
            "Wave này thêm `scripts/diagnose_structured_relation_prompt.py`, nên cùng "
            "cơ chế sẽ lại cộng +2 node vào `test_domain_string.py`. Đó là hành vi "
            "đúng, không phải hồi quy."),
    }


# ══════════════════════════════════════════════════════════════════════════
# §15 · DANH TÍNH & CACHE
# ══════════════════════════════════════════════════════════════════════════
def doc_cache_version() -> str:
    """Đọc `CACHE_VERSION` bằng cách PHÂN TÍCH nguồn, KHÔNG `import app.main`.

    `app.main` kéo theo `app/persistence/db.py`, và tệp ấy gọi `load_dotenv` —
    tức chỉ cần nhập nó là `GEMINI_API_KEY` thật đã nằm trong `os.environ` của
    tiến trình chẩn đoán. Wave này khai *"khoá không được nạp"*, nên phải làm
    cho câu ấy ĐÚNG chứ không giải thích quanh nó. Đo được: nhập `app.main` ⇒
    khoá lọt; nhập `app.ai.gemini`, `app.ai.pipeline`, `analyze_contract`,
    `geometry_compiler.compiler` ⇒ sạch.
    """
    nguon = (GOC / "app" / "main.py").read_text(encoding="utf-8")
    m = re.search(r'^CACHE_VERSION\s*=\s*"([^"]+)"', nguon, re.MULTILINE)
    if not m:
        raise AssertionError("không tìm thấy CACHE_VERSION trong app/main.py")
    return m.group(1)


def identity_and_cache_decision() -> dict[str, Any]:
    cv = doc_cache_version()
    return {
        "WAVE": WAVE,
        "CACHE_VERSION_BEFORE": cv,
        "CACHE_VERSION_AFTER": cv,
        "CACHE_BUMP": False,
        "_VI_SAO_KHONG_BUMP": "Wave không chạm bề mặt mô hình: prompt, schema, thẻ văn "
                              "phạm, bảng năng lực đều không đổi một byte. Bump khi ấy "
                              "chỉ xoá cache của người dùng mà không sửa gì.",
        "MEASURED_SYSTEM_PATHS_TOUCHED": [],
        "CANDIDATE_REFREEZE_REQUIRED": False,
        "_VI_SAO_KHONG_DONG_BANG_LAI": "Thay đổi nằm ở `backend/scripts/` và "
                                       "`backend/tests/` — theo nguyên tắc ranh giới của "
                                       "`freeze_evaluation_candidate.py`, đó là BỘ ĐO, "
                                       "không phải hệ được đo.",
        "PRODUCT_CODE_CHANGED": False,
        "PROMPT_CHANGED": False,
        "SCHEMA_CHANGED": False,
    }


# ══════════════════════════════════════════════════════════════════════════
def main() -> int:
    ap = argparse.ArgumentParser(description=WAVE)
    ap.add_argument("--collect-before", help="danh sách node id tại b6ec81b")
    ap.add_argument("--collect-after", help="danh sách node id tại da6ad17")
    a = ap.parse_args()
    RA.mkdir(parents=True, exist_ok=True)
    audit = prompt_instruction_audit()
    schema = schema_capability_audit()
    mapping = live_output_diagnostic_mapping()
    ra: dict[str, Any] = {
        "LIVE_EVIDENCE_INTEGRITY.json": live_evidence_integrity(),
        "PROMPT_INSTRUCTION_AUDIT.json": audit,
        "SCHEMA_CAPABILITY_AUDIT.json": schema,
        "SEMANTIC_NORMALIZATION_POLICY.json": semantic_normalization_policy(),
        "WORDING_COVERAGE_MATRIX.json": wording_coverage_matrix(),
        "LIVE_OUTPUT_DIAGNOSTIC_MAPPING.json": mapping,
        "ROOT_CAUSE_CLASSIFICATION.json": root_cause_classification(audit, schema, mapping),
        "PROPOSED_PROMPT_DELTA.json": proposed_prompt_delta(),
        "PROMPT_DELTA_SIMULATION_PROOF.json": prompt_delta_simulation_proof(),
        "IDENTITY_AND_CACHE_DECISION.json": identity_and_cache_decision(),
    }
    if a.collect_before and a.collect_after:
        truoc = doc_collection(Path(a.collect_before))
        sau = doc_collection(Path(a.collect_after))
        diff = classify_test_collection(truoc, sau)
        ra["TEST_COLLECTION_BEFORE.json"] = {
            "WAVE": WAVE, "COMMIT": "b6ec81b0ca1b98701c79acffc7de70c7a5781def",
            "COLLECTION_COMMAND": LENH_THU_THAP, "COUNT": len(truoc), "NODES": truoc}
        ra["TEST_COLLECTION_AFTER.json"] = {
            "WAVE": WAVE, "COMMIT": "da6ad17de5eadf6eb1b9f238eafedad63d300dad",
            "COLLECTION_COMMAND": LENH_THU_THAP, "COUNT": len(sau), "NODES": sau}
        ra["TEST_COLLECTION_DIFF.json"] = diff
        ra["TEST_COUNT_DISCREPANCY_CLASSIFICATION.json"] =             test_count_discrepancy_classification(diff)
        print(f"TEST_COUNT_DELTA = {diff['COUNT_DELTA']} · "
              f"{diff['BY_CLASSIFICATION']} · "
              f"EXPLAINED = {diff['DELTA_FULLY_EXPLAINED']}")

    for ten, obj in ra.items():
        (RA / ten).write_text(json.dumps(obj, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    print(f"ROOT_CAUSE = {ra['ROOT_CAUSE_CLASSIFICATION.json']['ROOT_CAUSE_CLASSIFICATION']}")
    print(f"SCHEMA_CAPABILITY = {schema['SCHEMA_CAPABILITY_FOR_MISSING_RELATION']}")
    print(f"LIVE_EVIDENCE_UNCHANGED = "
          f"{ra['LIVE_EVIDENCE_INTEGRITY.json']['ALL_UNCHANGED_SINCE_HEAD']}")
    print(f"→ {RA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
