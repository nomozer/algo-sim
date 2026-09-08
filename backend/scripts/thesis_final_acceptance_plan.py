# -*- coding: utf-8 -*-
"""KẾ HOẠCH ĐÁNH GIÁ CUỐI của khoá luận — dựng và KIỂM. **0 lượt gọi model.**

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \\
        scripts/thesis_final_acceptance_plan.py [--out-dir <thư mục>]

    `THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION`, 2026-09-08.

Bộ đo, ở `scripts/` — ngoài `MEASURED_SYSTEM_PATHS`. Nó **đọc** thẩm quyền sản
phẩm và không sửa gì trong `app/`.

─── WAVE NÀY LÀM GÌ, VÀ KHÔNG LÀM GÌ ──────────────────────────────────────

LÀM: khoá phạm vi · ma trận tuyên bố · bộ ca · tiêu chí · ngân sách · danh tính.
KHÔNG: gọi model. Lượt đo cuối chạy ở công đoạn sau, trên đúng
`IDENTITY_LOCK.json` mà file này ghi ra.

Chín chặng, mỗi chặng trả một `(ok, artifact)` và **không** chặng nào được phép
sửa `app/`:

    ① danh tính đo lại từ cây hiện tại        ⑥ chứng nhận bộ chấm
    ② trạng thái dự kiến có đúng không        ⑦ đánh giá runner sẵn sàng chưa
    ③ ma trận năng lực 12 họ × 4 chiều        ⑧ khoá danh tính + kế hoạch chạy
    ④ ma trận tuyên bố C1–C9                  ⑨ ghi artifact + tự kiểm
    ⑤ gold preflight + ca âm

─── VÌ SAO GOLD PREFLIGHT CHẠY ROUTE THẬT, KHÔNG DỰNG `FakeOutcome` ───────

Cùng lý do `certify_acceptance_runner.py` đã ghi: giả provider thì được, giả
route thì bài kiểm chỉ chứng minh bộ chấm khớp với **giả định của tôi** về
route. Ở đây provider được thay bằng gold contract + gold program đóng sẵn
trong corpus; từ `verify_and_compile` trở đi mọi thứ là thật — cổng phủ thật,
checker thật, `final_memory` thật, `pipeline._dung_scene3d` thật.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

RA = GOC / "docs" / "evaluation" / "geometry" / "thesis-final-acceptance"
CHINH_SACH = BACKEND / "scripts" / "policies" / "thesis_final_acceptance_policy.json"
MA_TRAN_GOC = (GOC / "docs" / "evaluation" / "geometry"
               / "missing-family-roadmap-refresh" / "CAPABILITY_MATRIX.json")

WAVE = "THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION"
EVALUATION_VERSION = "1.0.0"


def _bam_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "KHONG_CO"


def _ghi(p: Path, d: Any) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                 encoding="utf-8")
    return p


# ══ ① DANH TÍNH — đo lại từ cây, không chép từ tài liệu ══════════════════
def do_danh_tinh() -> dict[str, Any]:
    """Mười ba giá trị của §1, mỗi cái đọc từ THẨM QUYỀN của nó.

    Không giá trị nào ở đây được gõ tay. Bảng danh tính trong `CURRENT_STATE.md`
    đã trôi ba lần; một kế hoạch đo chép số từ tài liệu sẽ thừa hưởng đúng chỗ
    trôi ấy, và thừa hưởng lặng lẽ.
    """
    import freeze_evaluation_candidate as F
    import measurement_policy as MP
    from acceptance_integrity import _git, moi_truong_hien_tai, phan_loai_dirty

    he, so_file = F.measured_system_hash()
    mt = moi_truong_hien_tai()
    dirty = phan_loai_dirty()
    nguong, bam_nguong = MP.doc_chinh_sach(CHINH_SACH)
    _rubric, bam_rubric = MP.nap_rubric()
    scorer = BACKEND / "scripts" / "acceptance_verdict.py"
    return {
        "HEAD": _git("rev-parse", "HEAD"),
        "HEAD_ngan": _git("rev-parse", "--short", "HEAD"),
        "WORKING_TREE": ("SACH" if not (dirty["ban_trong_yeu"]
                                        or dirty["ban_khac"]) else "DIRTY"),
        "WORKING_TREE_chi_tiet": dirty,
        "CACHE_VERSION": mt["cache_version"],
        "CANDIDATE_HASH": he,
        "CANDIDATE_FILE_COUNT": so_file,
        "PROMPT_HASH": mt["components"]["prompts"],
        "GRAMMAR_CARD_HASH": mt["components"]["grammar_card"],
        "ANALYZE_SCHEMA_HASH": mt["components"]["analyze_schema"],
        "SYNTHESIS_SCHEMA_HASH": mt["components"]["synthesis_schema"],
        "CAPABILITY_HASH": mt["stable_capability_hash"],
        "SEMANTIC_ENVIRONMENT_HASH": mt["semantic_environment_hash"],
        # `RUNNER_HASH` cố ý là `null`: runner của lượt cuối CHƯA TỒN TẠI
        # (xem ⑦). Điền tạm băm của một runner khác sẽ khoá danh tính vào một
        # thứ không chạy lượt đo — đúng lớp lỗi `V3_LIVE_ENTRYPOINT` đã trả giá.
        "RUNNER_HASH": None,
        "RUNNER_HASH_khai": "runner lượt cuối chưa tồn tại — xem RUN_PLAN.json",
        "SCORER_HASH": _bam_file(scorer),
        "SCORER_PATH": "scripts/acceptance_verdict.py",
        "POLICY_HASH": bam_nguong,
        "POLICY_PATH": "scripts/policies/thesis_final_acceptance_policy.json",
        "ATTRIBUTION_RUBRIC_HASH": bam_rubric,
        "POLICY_LOADER_HASH": _bam_file(Path(MP.__file__)),
        "ORACLE_HASH": _bam_file(BACKEND / "scripts"
                                 / "thesis_acceptance_oracle.py"),
        "CORPUS_MODULE_HASH": _bam_file(BACKEND / "scripts"
                                        / "thesis_acceptance_corpus.py"),
        "PLAN_HASH": _bam_file(Path(__file__)),
    }


# ══ ② TRẠNG THÁI DỰ KIẾN — xác minh, không giả định ══════════════════════
def kiem_trang_thai_du_kien() -> tuple[bool, dict[str, Any]]:
    """Bốn khẳng định §1 phải ĐÚNG trước khi kế hoạch có nghĩa."""
    from app.simulation.product_capability import NANG_LUC_SAN_PHAM

    goc = json.loads(MA_TRAN_GOC.read_text(encoding="utf-8"))
    ho = {h["FAMILY"]: h for h in goc["families"]}
    kq = {
        "FEATURE_SCOPE_COMPLETE": goc["QUYET_DINH"].get("FEATURE_SCOPE_COMPLETE"),
        "solid_of_revolution_general": ho["solid_of_revolution_general"]["CURRENT_STATUS"],
        "composite_boolean": ho["composite_boolean"]["CURRENT_STATUS"],
        "oblique_cone_section": ho["oblique_cone_section"]["CURRENT_STATUS"],
        "product_capability_curved_oblique_section":
            NANG_LUC_SAN_PHAM["curved_oblique_section"].trang_thai,
    }
    mong = {
        "FEATURE_SCOPE_COMPLETE": "YES",
        "solid_of_revolution_general": "OUT_OF_SCOPE",
        "composite_boolean": "OUT_OF_SCOPE",
        "oblique_cone_section": "FOUNDATION_ONLY",
        "product_capability_curved_oblique_section": "foundation_only",
    }
    lech = {k: {"mong": v, "thuc": kq[k]} for k, v in mong.items() if kq[k] != v}
    return not lech, {"do_duoc": kq, "mong_doi": mong, "lech": lech}


# ══ ③ MA TRẬN NĂNG LỰC ═══════════════════════════════════════════════════
def dung_capability_matrix(danh_tinh: dict) -> tuple[bool, dict[str, Any]]:
    """12 họ × 4 chiều, DẪN từ ma trận `MISSING_FAMILY_ROADMAP_REFRESH`.

    ⚠️ Vì sao KHÔNG dẫn lại từ đầu: ma trận ấy đã đọc mã nguồn cho từng ô và
    có **26 test soát cả hai chiều** (thứ khai *"sẵn sàng"* phải có mặt, thứ
    khai *"chưa có"* phải thật sự vắng). Viết bản thứ hai là dựng một thẩm
    quyền song song, và bản thứ hai sẽ trôi — đúng thứ `RULES.md §2b` cấm.

    Cái wave này THÊM là hai cột mà bản gốc không có, và chỉ hai cột ấy:
    ca nào của bộ đánh giá cuối phủ họ này, và lượt cuối sẽ đo được gì cho nó.
    """
    import thesis_acceptance_corpus as C

    goc = json.loads(MA_TRAN_GOC.read_text(encoding="utf-8"))
    ho_am = {c["target_boundary"]: c["id"] for c in C.CA_AM}
    hang = []
    for h in goc["families"]:
        ten = h["FAMILY"]
        ca = C.PHU_THEO_HO.get(ten, [])
        hang.append({
            **h,
            "CORPUS_CASES": ca or ([ho_am[ten]] if ten in ho_am else []),
            "CORPUS_ROLE": ("POSITIVE" if ca else
                            "NEGATIVE" if ten in ho_am else "KHONG_PHU"),
            "FINAL_RUN_WILL_MEASURE": (
                ["MODEL_DISCOVERABLE"] if ca else
                ["NEGATIVE_FAIL_CLOSED"] if ten in ho_am else []),
            # ⚠️ Một ca một họ, chạy một lần. Không ô nào được đổi khỏi
            # `NOT_MEASURED` sau lượt cuối, và ghi ra đây để lượt sau khỏi
            # phải suy lại.
            "STABILITY_AFTER_FINAL_RUN": "NOT_MEASURED",
        })
    thieu = [h["FAMILY"] for h in hang if h["CORPUS_ROLE"] == "KHONG_PHU"]
    tk: dict[str, list[str]] = {}
    for h in hang:
        tk.setdefault(h["CURRENT_STATUS"], []).append(h["FAMILY"])
    return not thieu, {
        "khai": "Ma trận năng lực cho BỘ ĐÁNH GIÁ CUỐI. Nền dẫn từ "
                "MISSING_FAMILY_ROADMAP_REFRESH (đã có 26 test soát hai "
                "chiều); wave này chỉ thêm cột phủ corpus và cột lượt cuối "
                "sẽ đo gì. 0 lượt gọi model.",
        "wave": WAVE, "ngay": "2026-09-08",
        "dan_tu": "docs/evaluation/geometry/missing-family-roadmap-refresh/"
                  "CAPABILITY_MATRIX.json",
        "dan_tu_hash": _bam_file(MA_TRAN_GOC),
        "HEAD": danh_tinh["HEAD_ngan"],
        "cache_version": danh_tinh["CACHE_VERSION"],
        "candidate": danh_tinh["CANDIDATE_HASH"][:16],
        "muc_bang_chung": goc["muc_bang_chung"],
        "families": hang,
        "TONG_KET": tk,
        "HO_KHONG_DUOC_PHU": thieu,
        "FEATURE_SCOPE_COMPLETE": goc["QUYET_DINH"]["FEATURE_SCOPE_COMPLETE"],
    }


# ══ ④ MA TRẬN TUYÊN BỐ C1–C9 ═════════════════════════════════════════════
_NGUON = {
    "ir_static": "backend/app/simulation/semantic_program/ir_static_check.py",
    "route": "backend/app/simulation/semantic_program/route.py",
    "coverage": "backend/app/simulation/semantic_program/coverage_gate.py",
    "grounding": "backend/app/simulation/semantic_program/grounding_gate.py",
    "post": "backend/app/simulation/semantic_program/postconditions.py",
    "scene3d": "backend/app/simulation/semantic_program/scene3d.py",
    "radical": "backend/app/simulation/geometry/radical.py",
    "curved": "backend/app/simulation/geometry/curved.py",
    "section": "backend/app/simulation/geometry/section.py",
    "point_src": "backend/app/simulation/semantic_program/point_coordinate.py",
    "plane_eq": "backend/app/simulation/semantic_program/plane_equation.py",
    "seg_rel": "backend/app/simulation/semantic_program/segment_relation.py",
    "capability": "backend/app/simulation/product_capability.py",
    "scorer": "backend/scripts/acceptance_verdict.py",
    "oracle": "backend/scripts/thesis_acceptance_oracle.py",
    "corpus": "backend/scripts/thesis_acceptance_corpus.py",
}

_CLAIMS: list[dict[str, Any]] = [
    {
        "CLAIM_ID": "C1",
        "THESIS_CLAIM": "Bài toán mới được phục vụ bằng cách GHÉP các phép IR "
                        "tổng quát, không cần viết module theo từng bài.",
        "SCOPE": "Trong IR hình học hiện có. Bài ngoài IR bị TỪ CHỐI, không "
                 "được xấp xỉ.",
        "EVIDENCE_LEVEL": "SUPPORTED",
        "CURRENT_EVIDENCE": "PROBLEM_FAMILY_SPECIAL_CASES = 0 (quét AST mã "
                            "sản phẩm) · `registerAllSimulations()` gọi đúng "
                            "một dòng · runtime đóng băng qua hơn mười wave đề mới",
        "SOURCE_KEYS": ["ir_static", "route"],
        "FINAL_MEASUREMENT_REQUIRED": "YES",
        "METRIC": "NEW_PER_PROBLEM_MODULES · NEW_IR_OPERATIONS · "
                  "NEW_MEMORY_TYPES trong suốt lượt đo",
        "DENOMINATOR": "7 ca dương",
        "DECISION_RULE": "cả ba = 0",
        "LIMITATION": "Mệnh đề CÓ ĐIỀU KIỆN. Nó không nói hệ làm được mọi bài "
                      "hình học, chỉ nói bài BIỂU DIỄN ĐƯỢC không cần mã mới.",
        "THESIS_CHAPTER_TARGET": "Kiến trúc · Kết quả",
    },
    {
        "CLAIM_ID": "C2",
        "THESIS_CLAIM": "Mọi đại lượng được tính trong miền số CHÍNH XÁC "
                        "(hữu tỉ + căn + π), không làm tròn ở bất kỳ đâu.",
        "SCOPE": "Bao đóng ℚ(√, π) đã công bố. Ngoài bao đóng ⇒ từ chối.",
        "EVIDENCE_LEVEL": "SUPPORTED",
        "CURRENT_EVIDENCE": "suite hình học · `geometry_oracle.py` cài ĐỘC LẬP "
                            "với kernel · `replay_demo_cases.py` 5/5",
        "SOURCE_KEYS": ["radical", "curved", "section", "oracle"],
        "FINAL_MEASUREMENT_REQUIRED": "YES",
        "METRIC": "EXACT_ANSWER_MATCH (chuỗi hiển thị) VÀ "
                  "ORACLE_NUMERIC_AGREEMENT (oracle độc lập) — HAI cột",
        "DENOMINATOR": "11 đại lượng trên 7 ca dương",
        "DECISION_RULE": "SERVED_EXACT_MISMATCH_COUNT = 0",
        "LIMITATION": "Hai cột đo hai điều khác nhau: cột một kiểm CHÍNH TẢ "
                      "hiển thị, cột hai kiểm SỐ. Gộp chúng là mất khả năng "
                      "phân biệt lỗi quy ước với lỗi toán.",
        "THESIS_CHAPTER_TARGET": "Nhân hình học · Kết quả",
    },
    {
        "CLAIM_ID": "C3",
        "THESIS_CLAIM": "Toạ độ, phương trình mặt phẳng, độ dài và quan hệ "
                        "chia đoạn mà chương trình dùng đều được ĐỐI CHIẾU "
                        "ngược với đề bài.",
        "SCOPE": "Bất biến nguồn đã thi hành; dữ kiện đề KHÔNG nêu thì không "
                 "có gì để đối chiếu.",
        "EVIDENCE_LEVEL": "SUPPORTED",
        "CURRENT_EVIDENCE": "POINT_COORDINATE_SOURCE_INVARIANT · "
                            "PLANE_FROM_EQUATION_REPRESENTATION · "
                            "SEGMENT_RELATION_COVERAGE_HARDENING",
        "SOURCE_KEYS": ["point_src", "plane_eq", "seg_rel", "grounding"],
        "FINAL_MEASUREMENT_REQUIRED": "YES",
        "METRIC": "SOURCE_INVARIANTS_PASS",
        "DENOMINATOR": "ca dương có dữ kiện toạ độ/mặt phẳng (7/7)",
        "DECISION_RULE": "SERVED_SOURCE_INVARIANT_VIOLATION_COUNT = 0",
        "LIMITATION": "Bất biến kiểm thứ chương trình KHAI so với thứ đề NÊU; "
                      "nó không kiểm được dữ kiện đề không nêu.",
        "THESIS_CHAPTER_TARGET": "Ranh giới R0 · Kết quả",
    },
    {
        "CLAIM_ID": "C4",
        "THESIS_CLAIM": "Dòng thời gian và cảnh 3D được DẪN XUẤT từ trạng "
                        "thái tất định, phản ánh đúng các bước dựng và quan "
                        "hệ phụ thuộc.",
        "SCOPE": "Song ánh `frame k ⇔ trace[k]` (bất biến #31). Tương tác là "
                 "CHỌN và TUA, không kéo–thả liên tục.",
        "EVIDENCE_LEVEL": "SUPPORTED",
        "CURRENT_EVIDENCE": "`replay_demo_cases.py` `producer`/`depends` trên "
                            "mọi vật dựng · GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE",
        "SOURCE_KEYS": ["scene3d", "route"],
        "FINAL_MEASUREMENT_REQUIRED": "YES",
        "METRIC": "TRACE_PASS · SCENE3D_PASS · số loại vẽ khớp "
                  "`expected_scene3d_kinds`",
        "DENOMINATOR": "7 ca dương",
        "DECISION_RULE": "SERVED_SCENE3D_MISMATCH_COUNT = 0",
        "LIMITATION": "Đo CẤU TRÚC cảnh (có đúng loại vật không), không đo "
                      "chất lượng thị giác.",
        "THESIS_CHAPTER_TARGET": "Mô phỏng · Kết quả",
    },
    {
        "CLAIM_ID": "C5",
        "THESIS_CLAIM": "«Đáp số đúng» và «hình dựng đúng» là HAI chiều độc "
                        "lập; một mô phỏng chỉ đúng khi cả hai cùng đúng.",
        "SCOPE": "Ba cột EXACT_ANSWER_MATCH · SCENE3D_PASS · SERVABLE tách rời.",
        "EVIDENCE_LEVEL": "SUPPORTED",
        "CURRENT_EVIDENCE": "V3_PRODUCT_PATH_PARITY_CORRECTION — ca `c7a` "
                            "đúng ba cột đầu, hỏng hai cột sau; gộp cột là "
                            "cách nó bị quy sai trách nhiệm lần đầu",
        "SOURCE_KEYS": ["scorer"],
        "FINAL_MEASUREMENT_REQUIRED": "YES",
        "METRIC": "ba cột báo cáo RIÊNG cho từng ca",
        "DENOMINATOR": "7 ca dương",
        "DECISION_RULE": "không cột nào được suy ra từ cột khác trong artifact",
        "LIMITATION": "Đây là tuyên bố về PHƯƠNG PHÁP ĐO, không phải về năng "
                      "lực; nó đúng nhờ hình dạng artifact, không nhờ kết quả.",
        "THESIS_CHAPTER_TARGET": "Phương pháp đánh giá",
    },
    {
        "CLAIM_ID": "C6",
        "THESIS_CLAIM": "Mô hình ngôn ngữ TỰ phân tích đề và ghép đúng các "
                        "phép IR tổng quát để dựng chương trình.",
        "SCOPE": "Đo trên 7 ca dương, mỗi ca một lượt. KHÔNG phải ước lượng "
                 "tổng thể, KHÔNG phải độ ổn định.",
        "EVIDENCE_LEVEL": "PARTIAL",
        "CURRENT_EVIDENCE": "clean-baseline-v2 6/6 · nonconvex "
                            "discoverability 1/1 attempt 0 · ⚠️ CURVED V3 "
                            "held-out **FAIL 0/9 servable** (1/9 đáp số đúng "
                            "sau đính chính); nút thắt = CONSTRUCTION-GROUNDING",
        "SOURCE_KEYS": ["corpus", "scorer"],
        "FINAL_MEASUREMENT_REQUIRED": "YES",
        "METRIC": "FIRST_ATTEMPT_SERVABLE_RATE · "
                  "RECOVERY_WITHIN_ONE_REPAIR_RATE · ANALYZE_CORRECT_RATE · "
                  "PROGRAM_VALID_RATE · PER_FAMILY_SERVABLE_RATE",
        "DENOMINATOR": "7 ca dương (per-family: 1 ca/họ)",
        "DECISION_RULE": "KHÔNG CÓ NGƯỠNG — báo cáo mô tả kèm mẫu số. Khoá "
                         "luận chưa quy định ngưỡng học thuật và bộ đo không "
                         "tự đặt hộ.",
        "LIMITATION": "n = 1 mỗi họ ⇒ không nói được gì về độ ổn định. "
                      "`STABILITY_UNDER_ACCEPTANCE` giữ `NOT_MEASURED` cho "
                      "MỌI họ sau lượt này.",
        "THESIS_CHAPTER_TARGET": "Kết quả · Bàn luận",
    },
    {
        "CLAIM_ID": "C7",
        "THESIS_CLAIM": "Bài hoặc chương trình ngoài bao đóng bị TỪ CHỐI bằng "
                        "một mã ổn định, chứ không được phục vụ một kết quả sai.",
        "SCOPE": "Fail-closed toàn tuyến. Đây là tuyên bố về AN TOÀN, không "
                 "phải về độ phủ.",
        "EVIDENCE_LEVEL": "SUPPORTED",
        "CURRENT_EVIDENCE": "`audit_demo_crash_surface.py` 6/6 biên, 0 đường "
                            "ném · ca demo `n4` chặn đúng ở grounding · V3 "
                            "ca âm 4/4 fail-closed",
        "SOURCE_KEYS": ["coverage", "grounding", "post"],
        "FINAL_MEASUREMENT_REQUIRED": "YES",
        "METRIC": "NEGATIVE_FAIL_CLOSED_RATE · SILENT_WRONG_ANSWER_COUNT · "
                  "UNHANDLED_EXCEPTION_COUNT",
        "DENOMINATOR": "2 ca âm (+ 7 ca dương cho SILENT_WRONG_ANSWER)",
        "DECISION_RULE": "NEGATIVE_FAIL_CLOSED = 2/2 · "
                         "SILENT_WRONG_ANSWER_COUNT = 0",
        "LIMITATION": "Fail-closed CHƯA phải chứng minh ranh giới. "
                      "`TARGET_BOUNDARY_DEMONSTRATED` được đo riêng và KHÔNG "
                      "đặt thành ngưỡng — hệ không có mã lỗi nào mang tên hai "
                      "họ ngoài phạm vi.",
        "THESIS_CHAPTER_TARGET": "Ranh giới R0 · Kết quả",
    },
    {
        "CLAIM_ID": "C8",
        "THESIS_CLAIM": "Chi phí để phục vụ MỘT mô phỏng đúng đo được, và đo "
                        "bằng lượt gọi logic · lần thử vật lý · token.",
        "SCOPE": "Ba bộ đếm TÁCH RIÊNG. Retry transport KHÔNG được đếm thành "
                 "lượt gọi logic.",
        "EVIDENCE_LEVEL": "SUPPORTED",
        "CURRENT_EVIDENCE": "telemetry 6 lượt lịch sử (trung vị analyze 2382 · "
                            "synthesis 5925 token/lượt)",
        "SOURCE_KEYS": [],
        "FINAL_MEASUREMENT_REQUIRED": "YES",
        "METRIC": "TOKENS_PER_CORRECT_SERVABLE · CALLS_PER_CORRECT_SERVABLE · "
                  "phân rã input/output/thought/cached",
        "DENOMINATOR": "số ca dương ĐẠT `servable` (mẫu số thay đổi ⇒ phải in ra)",
        "DECISION_RULE": "KHÔNG CÓ NGƯỠNG — báo cáo mô tả",
        "LIMITATION": "Mẫu số là số ca ĐẠT, nên tỉ số này không so được giữa "
                      "hai lượt có tỉ lệ đạt khác nhau. Phải in kèm mẫu số.",
        "THESIS_CHAPTER_TARGET": "Kết quả · Bàn luận",
    },
    {
        "CLAIM_ID": "C9",
        "THESIS_CLAIM": "Hai họ hình nằm NGOÀI phạm vi vì lý do KIẾN TRÚC đo "
                        "được, không phải vì «chưa kịp làm».",
        "SCOPE": "`solid_of_revolution_general` và `composite_boolean`.",
        "EVIDENCE_LEVEL": "SUPPORTED",
        "CURRENT_EVIDENCE": "MISSING_FAMILY_ROADMAP_REFRESH — ma trận 12 họ "
                            "kiểm được bằng máy, 26 test soát CẢ HAI CHIỀU",
        "SOURCE_KEYS": ["curved", "capability"],
        "FINAL_MEASUREMENT_REQUIRED": "PARTIAL",
        "METRIC": "ABSENCE_PROOF_PASS (tất định, 0 lượt gọi) · "
                  "NEGATIVE_FAIL_CLOSED (live)",
        "DENOMINATOR": "2 ca âm",
        "DECISION_RULE": "ABSENCE_PROOF_PASS = 2/2 VÀ "
                         "NEGATIVE_FAIL_CLOSED = 2/2",
        "LIMITATION": "Bằng chứng thuộc lớp BOUNDARY_BY_ABSENCE_PROOF, KHÔNG "
                      "phải BOUNDARY_BY_NAMED_ERROR_CODE. Hệ từ chối vì "
                      "không có đường, chứ không vì nó nhận ra tên họ hình.",
        "THESIS_CHAPTER_TARGET": "Phạm vi · Giới hạn",
    },
]


def dung_claims_matrix(danh_tinh: dict) -> tuple[bool, dict[str, Any]]:
    cot = ("CLAIM_ID", "THESIS_CLAIM", "SCOPE", "EVIDENCE_LEVEL",
           "CURRENT_EVIDENCE", "SOURCE_FILES", "SOURCE_HASHES",
           "FINAL_MEASUREMENT_REQUIRED", "METRIC", "DENOMINATOR",
           "DECISION_RULE", "LIMITATION", "THESIS_CHAPTER_TARGET")
    hang = []
    for c in _CLAIMS:
        tep = [_NGUON[k] for k in c["SOURCE_KEYS"]]
        hang.append({**{k: v for k, v in c.items() if k != "SOURCE_KEYS"},
                     "SOURCE_FILES": tep,
                     "SOURCE_HASHES": {t: _bam_file(GOC / t) for t in tep}})
    thieu = [h["CLAIM_ID"] for h in hang if set(cot) - set(h)]
    return not thieu, {
        "khai": "Ma trận tuyên bố ↔ bằng chứng ↔ giới hạn cho lượt đo cuối. "
                "Mỗi hàng nói RÕ điều gì đã chứng minh, điều gì lượt cuối mới "
                "trả lời, và điều gì nó KHÔNG trả lời được.",
        "wave": WAVE, "ngay": "2026-09-08",
        "HEAD": danh_tinh["HEAD_ngan"],
        "candidate": danh_tinh["CANDIDATE_HASH"][:16],
        "columns": list(cot),
        "claims": hang,
        "CLAIMS_TOTAL": len(hang),
        "CLAIMS_ALREADY_PROVED": sum(
            1 for h in hang if h["FINAL_MEASUREMENT_REQUIRED"] == "NO"),
        "CLAIMS_REQUIRING_FINAL_RUN": sum(
            1 for h in hang if h["FINAL_MEASUREMENT_REQUIRED"] in
            ("YES", "PARTIAL")),
        "CLAIMS_WITHOUT_THRESHOLD": [
            h["CLAIM_ID"] for h in hang if "KHÔNG CÓ NGƯỠNG" in h["DECISION_RULE"]],
        "RQ_MAPPING": {
            "RQ1_do_phu": ["C1", "C9"],
            "RQ2_tinh_dung": ["C2", "C3", "C4", "C5"],
            "RQ3_kha_nang_tu_sinh": ["C6"],
            "RQ4_an_toan": ["C7", "C9"],
            "RQ5_hieu_qua": ["C8"],
        },
        "THIEU_COT": thieu,
    }


# ══ ④b PHÂN LOẠI BẰNG CHỨNG LỊCH SỬ ══════════════════════════════════════
#
# ⚠️ Luật cứng: **artifact lịch sử giữ NGUYÊN BYTE.** Hàm này chỉ ĐỌC và dán
# nhãn; nó không sửa, không di chuyển, không xoá. Một artifact chạy trên
# candidate cũ vẫn có giá trị lịch sử — nó chỉ không đại diện cho candidate
# cuối, và hai điều đó phải nói riêng.
_LOP_BANG_CHUNG = (
    "DETERMINISTIC_FOUNDATION",
    "DEVELOPMENT_REPLAY",
    "DEVELOPMENT_LIVE",
    "HISTORICAL_ACCEPTANCE",
    "CURRENT_CANDIDATE_ACCEPTANCE",
)
_KHOA_DANH_TINH = ("candidate_hash", "measured_system_hash", "cache_version",
                   "measurement_class", "moi_truong", "manifest")


def _dao(o: Any, khoa: str, sau: int = 0):
    """Tìm `khoa` ở bất kỳ độ sâu nào — hình dạng artifact khác nhau theo wave,
    và một bộ đọc chỉ biết MỘT hình dạng sẽ im lặng bỏ qua phần còn lại."""
    if sau > 6:
        return None
    if isinstance(o, dict):
        if khoa in o:
            return o[khoa]
        for v in o.values():
            if (r := _dao(v, khoa, sau + 1)) is not None:
                return r
    elif isinstance(o, list):
        for v in o[:60]:
            if (r := _dao(v, khoa, sau + 1)) is not None:
                return r
    return None


def phan_loai_bang_chung_lich_su(candidate: str) -> tuple[bool, dict[str, Any]]:
    goc = GOC / "docs" / "evaluation"
    hang: list[dict[str, Any]] = []
    for p in sorted(goc.rglob("*.json")):
        # Artifact CỦA CHÍNH wave này không phải "bằng chứng lịch sử". Để nó
        # lọt vào thì con số đổi mỗi lần chạy lại, và bảng sẽ tự kể mình là
        # bằng chứng cho chính kế hoạch nó vừa viết ra.
        if RA in p.parents:
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(d, dict):
            continue
        if not any(_dao(d, k) is not None for k in _KHOA_DANH_TINH):
            continue
        # Chỉ nhận một chuỗi HEX. `_dao` đi sâu nên nó cũng bắt được một
        # `{"candidate": {"hash_do_lai": …}}` của wave khác, và một dict lọt
        # vào cột CANDIDATE sẽ đọc như một băm lạ chứ không như một chỗ thiếu.
        cand = next((c for c in (_dao(d, "candidate_hash"),
                                 _dao(d, "measured_system_hash"),
                                 _dao(d, "candidate"))
                     if isinstance(c, str) and len(c) >= 16
                     and all(x in "0123456789abcdef" for x in c.lower())),
                    None)
        mc = _dao(d, "measurement_class") or _dao(d, "MEASUREMENT_CLASS")
        goi = (_dao(d, "TOTAL_APPLICATION_LLM_CALLS")
               if _dao(d, "TOTAL_APPLICATION_LLM_CALLS") is not None
               else _dao(d, "logical_application_calls"))
        ten = p.name.lower()
        khop = bool(cand) and str(cand)[:16] == candidate[:16]

        if goi in (0, None) and any(
                k in ten for k in ("preflight", "gold", "boundary", "seal",
                                   "capability", "registration", "matrix")):
            lop = "DETERMINISTIC_FOUNDATION"
        elif "replay" in ten or "demo" in ten:
            lop = "DEVELOPMENT_REPLAY"
        elif mc and "ACCEPTANCE" in str(mc).upper():
            lop = ("CURRENT_CANDIDATE_ACCEPTANCE" if khop
                   else "HISTORICAL_ACCEPTANCE")
        elif "acceptance" in str(p.parent.name).lower():
            lop = ("CURRENT_CANDIDATE_ACCEPTANCE" if khop
                   else "HISTORICAL_ACCEPTANCE")
        else:
            lop = "DEVELOPMENT_LIVE"

        hop_le = (
            "YES" if lop == "DETERMINISTIC_FOUNDATION" and khop else
            "YES" if khop else
            "HISTORICAL_ONLY")
        hang.append({
            "ARTIFACT": str(p.relative_to(GOC)).replace("\\", "/"),
            "CANDIDATE": (str(cand)[:16] if cand else None),
            "CAPABILITY_MEASURED": _dao(d, "wave") or _dao(d, "run_id")
            or p.parent.name,
            "VALID_FOR_CURRENT_CLAIM": hop_le,
            "VALIDITY_REASON": (
                "candidate KHỚP hệ hiện tại" if khop else
                "candidate KHÁC hệ hiện tại — giá trị LỊCH SỬ, không đại diện "
                "cho bản đang đo" if cand else
                "không ghi candidate — không truy được về bản nào"),
            "REQUIRES_RERUN": ("NO" if khop else "KHONG_AP_DUNG"),
            "EVIDENCE_CLASS": lop,
            "MEASUREMENT_CLASS": mc,
            "APPLICATION_LLM_CALLS": goi,
        })
    tk: dict[str, int] = {}
    for h in hang:
        tk[h["EVIDENCE_CLASS"]] = tk.get(h["EVIDENCE_CLASS"], 0) + 1
    return True, {
        "khai": "Phân loại bằng chứng đã có. CHỈ dán nhãn — artifact lịch sử "
                "giữ nguyên byte, không sửa, không di chuyển.",
        "candidate_hien_tai": candidate[:16],
        "lop_hop_le": list(_LOP_BANG_CHUNG),
        "TONG_ARTIFACT_CO_DANH_TINH": len(hang),
        "TONG_KET_THEO_LOP": tk,
        "KHOP_CANDIDATE_HIEN_TAI": sum(
            1 for h in hang if h["VALID_FOR_CURRENT_CLAIM"] == "YES"),
        "khai_them": "Không hàng nào mang `REQUIRES_RERUN = YES`: lượt đo cuối "
                     "KHÔNG chạy lại bằng chứng cũ, nó chạy một bộ ca MỚI. "
                     "Artifact cũ vẫn là bằng chứng cho tuyên bố của CHÍNH "
                     "chúng, trên candidate của chúng.",
        "artifacts": hang,
    }


# ══ ⑤ GOLD PREFLIGHT ═════════════════════════════════════════════════════
def _chay_gold(ca: dict) -> dict[str, Any]:
    """Một ca dương đi TRỌN đường sản phẩm. Provider giả, route THẬT."""
    import acceptance_verdict as AV
    from app.ai import pipeline
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.route import verify_and_compile
    from app.simulation.semantic_program.validator import validate_semantic_program

    v = validate_semantic_program(ca["gold_program"])
    if not v.ok:
        return {"id": ca["id"], "schema_valid": False,
                "loi": (v.error or "")[:2000], "servable": False}
    hd = ca["request_contract_gold"]
    contract = RequestContract(
        problem_text=ca["problem_text"], input_facts=hd["input_facts"],
        obligations=tuple(Obligation(**o) for o in hd["obligations"]))
    out = verify_and_compile(contract, v.spec)
    gd = AV.co_giai_doan(out, schema_ok=True)
    kq = AV.trich_ket_qua(out)

    canh = pipeline._dung_scene3d(v.spec, contract) \
        if gd["runtime_executable"] else None
    loai_canh = sorted({o.get("type") for o in (canh or {}).get("objects", [])})

    that = kq["dai_luong"]
    mong = ca["expected"]
    dai_luong = {}
    for ten, m in mong.items():
        hien = that.get(ten)
        o = _cham_oracle(hien, m)
        dai_luong[ten] = {"expected_display": m["display"], "actual_display": hien,
                          "exact_answer_match": hien == m["display"], **o}
    return {
        "id": ca["id"], "families": ca["families"], "schema_valid": True,
        "stage_reached": gd["stage_reached"],
        "grounding_pass": gd["grounding_pass"],
        "coverage_pass": gd["coverage_pass"],
        "static_valid": gd["static_valid"],
        "runtime_executable": gd["runtime_executable"],
        "postconditions_pass": gd["postconditions_pass"],
        "servable": gd["servable"],
        "error_code": getattr(out, "error_code", None),
        "failure_category": getattr(out, "failure_category", None),
        "details": [str(x)[:400] for x in (getattr(out, "details", None) or [])],
        "exact_result_authority": kq["nguon"],
        "final_memory": that,
        "quantities": dai_luong,
        "EXACT_ANSWER_MATCH": all(q["exact_answer_match"]
                                  for q in dai_luong.values()),
        "ORACLE_NUMERIC_AGREEMENT": all(q["oracle_numeric_agreement"]
                                        for q in dai_luong.values()),
        "scene3d_kinds": loai_canh,
        "scene3d_quantities": sorted(
            o.get("value") for o in (canh or {}).get("objects", [])
            if o.get("type") == "quantity"),
        "SCENE3D_PASS": set(ca["expected_scene3d_kinds"]) <= set(loai_canh),
        "scene3d_kinds_missing": sorted(
            set(ca["expected_scene3d_kinds"]) - set(loai_canh)),
        "verdict": AV.phan_loai(out, schema_ok=True, contract=contract,
                                spec=v.spec),
    }


def _cham_oracle(hien: str | None, mong: dict) -> dict[str, Any]:
    """Cột thứ HAI: chuỗi hiển thị ấy có chỉ đúng CON SỐ oracle dẫn ra không?"""
    import thesis_acceptance_oracle as O

    dung_sai = {"CLOSED_FORM": 1e-12, "SAMPLED": 1e-8}[mong["oracle_method"]]
    if hien is None:
        return {"oracle_numeric_agreement": False, "oracle_value":
                mong["oracle_value"], "oracle_method": mong["oracle_method"],
                "relative_error": None, "tolerance": dung_sai,
                "ghi_chu": "không có đại lượng để so"}
    try:
        sai = O.sai_so_tuong_doi(hien, mong["oracle_value"])
        ghi = ""
    except O.OracleError as e:
        return {"oracle_numeric_agreement": False,
                "oracle_value": mong["oracle_value"],
                "oracle_method": mong["oracle_method"], "relative_error": None,
                "tolerance": dung_sai, "ghi_chu": str(e)[:300]}
    return {"oracle_numeric_agreement": sai <= dung_sai,
            "oracle_value": mong["oracle_value"],
            "oracle_method": mong["oracle_method"],
            "relative_error": sai, "tolerance": dung_sai, "ghi_chu": ghi}


def _oracle_doc_lap_tu_dan() -> dict[str, Any]:
    """Chạy LẠI oracle từ `oracle_call` — không tin con số đã ghi trong corpus.

    Bản đầu chỉ so đáp số với `oracle_value` chép sẵn. Nhưng một con số chép
    sẵn thì cũng chỉ là một con số ai đó gõ vào: nếu tôi gõ nhầm, cả bảy ca
    xanh và cái sai đi thẳng vào khoá luận. Nên ở đây oracle được GỌI LẠI.
    """
    import thesis_acceptance_corpus as C
    import thesis_acceptance_oracle as O

    ra = {}
    for ca in C.CA_DUONG:
        for ten, m in ca["expected"].items():
            goi = m["oracle_call"]
            ham = getattr(O, goi[0])
            if len(goi) == 2 and isinstance(goi[1], dict):
                gt = ham(**{k: (tuple(v) if isinstance(v, list) else v)
                            for k, v in goi[1].items()})
            else:
                gt = ham(*[tuple(x) if isinstance(x, list) and
                           len(x) == 3 and all(isinstance(y, (int, float))
                                               for y in x) else x
                           for x in goi[1:]])
            so = gt if isinstance(gt, float) else gt.get(
                _luong_tu_witness(ca, ten))
            khop = so is not None and abs(so - m["oracle_value"]) <= \
                1e-9 * max(abs(m["oracle_value"]), 1.0)
            ra[f"{ca['id']}.{ten}"] = {
                "oracle_call": goi[0], "tinh_lai": so,
                "gia_tri_ghi_trong_corpus": m["oracle_value"], "khop": khop}
    return ra


def _luong_tu_witness(ca: dict, ten: str) -> str:
    """Witness `V` đo `volume`, `S_C`/`S_T`/`S_E` đo `area`, `Sxq` đo
    `lateral_area`, `d` đo `distance`. Đọc từ GOLD PROGRAM, không đoán."""
    for st in ca["gold_program"]["statements"]:
        if st.get("target_var") == ten and \
                (st.get("expr") or {}).get("kind") == "measure":
            return st["expr"]["quantity"]
    return "area"


def gold_preflight() -> tuple[bool, dict[str, Any]]:
    import thesis_acceptance_corpus as C

    ca = [_chay_gold(c) for c in C.CA_DUONG]
    tu_dan = _oracle_doc_lap_tu_dan()
    dat = {
        "GOLD_POSITIVE_SERVABLE": f"{sum(1 for r in ca if r['servable'])}/{len(ca)}",
        "GOLD_EXACT_MATCH": f"{sum(1 for r in ca if r['EXACT_ANSWER_MATCH'])}/{len(ca)}",
        "GOLD_ORACLE_AGREEMENT":
            f"{sum(1 for r in ca if r['ORACLE_NUMERIC_AGREEMENT'])}/{len(ca)}",
        "GOLD_POSTCONDITIONS":
            f"{sum(1 for r in ca if r['postconditions_pass'])}/{len(ca)}",
        "GOLD_SCENE3D": f"{sum(1 for r in ca if r['SCENE3D_PASS'])}/{len(ca)}",
        "GOLD_WEAK_KINDS": sum(1 for r in ca
                               if r["failure_category"] == "verification_gap"),
        "ORACLE_SELF_CHECK":
            f"{sum(1 for v in tu_dan.values() if v['khop'])}/{len(tu_dan)}",
    }
    ok = (all(r["servable"] and r["EXACT_ANSWER_MATCH"]
              and r["ORACLE_NUMERIC_AGREEMENT"] and r["postconditions_pass"]
              and r["SCENE3D_PASS"] for r in ca)
          and all(v["khop"] for v in tu_dan.values()))
    return ok, {"khai": "Gold preflight — provider GIẢ, route THẬT. "
                        "0 lượt gọi model.",
                "wave": WAVE, "tong_ket": dat, "GOLD_PREFLIGHT_PASS": ok,
                "oracle_tu_dan_lai": tu_dan, "cases": ca}


# ══ ⑥ CA ÂM — chứng minh VẮNG MẶT + dò tất định ══════════════════════════
def _quet_vang_mat(thu_muc: str, mau: list[str]) -> dict[str, Any]:
    """Mẫu nào xuất hiện trong cây mã ấy? Rỗng là điều ma trận khai."""
    goc = GOC / thu_muc
    tep = sorted(goc.rglob("*.py"))
    trung: dict[str, list[str]] = {}
    for p in tep:
        try:
            t = p.read_text(encoding="utf-8")
        except OSError:
            continue
        for m in mau:
            if m in t:
                trung.setdefault(m, []).append(str(p.relative_to(GOC)))
    return {"thu_muc": thu_muc, "so_file_da_doc": len(tep),
            "mau": mau, "trung": trung, "so_ket_qua": sum(
                len(v) for v in trung.values())}


def _kieu_bo_nho() -> list[str]:
    from app.simulation.semantic_program.contract import MemoryType

    return sorted(MemoryType.__args__)


def _curved_kind_cho_phep() -> list[str]:
    src = (BACKEND / "app" / "simulation" / "semantic_program"
           / "contract.py").read_text(encoding="utf-8")
    m = re.search(r"curved_kind\s*:\s*Literal\[([^\]]+)\]", src)
    return sorted(re.findall(r'"([a-z_]+)"', m.group(1))) if m else []


def negative_preflight() -> tuple[bool, dict[str, Any]]:
    import acceptance_verdict as AV
    import thesis_acceptance_corpus as C

    kieu = _kieu_bo_nho()
    ra = []
    for ca in C.CA_AM:
        ap = ca["absence_proof"]
        chung: dict[str, Any] = {}
        for ten, dk in ap.items():
            if "quet" in dk:
                q = _quet_vang_mat(dk["quet"], dk["mau"])
                chung[ten] = {**q, "dat": q["so_ket_qua"] == dk["mong_so_ket_qua"]}
            elif "mong_vang" in dk:
                # ⚠️ So theo ĐOẠN TÊN, không theo chuỗi con. Bản đầu dùng
                # `k in t` và `curved_solid` khớp mẫu `"curve"` — một dương
                # tính giả nói *"hệ có kiểu đường cong"* trong khi thứ nó tìm
                # thấy là một khối. Tách tên kiểu ở `_` rồi so đúng đoạn thì
                # `function_expr` vẫn bị bắt bởi mẫu `"function"`, còn
                # `curved_solid` thì không.
                doan = {s for t in kieu for s in t.split("_")}
                co = sorted(set(dk["mong_vang"]) & (doan | set(kieu)))
                chung[ten] = {"kieu_bo_nho": kieu, "doan_ten": sorted(doan),
                              "tim_thay": co, "dat": not co}
            elif "mong_dung_bang" in dk:
                that = _curved_kind_cho_phep()
                chung[ten] = {"curved_kind": that,
                              "dat": that == sorted(dk["mong_dung_bang"])}
            else:
                chung[ten] = {"dat": True, "khai": "khẳng định tài liệu, "
                                                   "không kiểm được bằng máy"}
        # Bộ chấm ca âm có NHẬN được lời khai ranh giới của ca này không?
        # (`cham_ca_am` NÉM nếu ca không khai `expected_codes`/`expected_stages`)
        try:
            AV.cham_ca_am(ca, None, schema_ok=True)
            scorer_nhan = True
            scorer_loi = None
        except ValueError as e:
            scorer_nhan, scorer_loi = False, str(e)[:300]
        ra.append({
            "id": ca["id"], "target_boundary": ca["target_boundary"],
            "absence_proof": chung,
            "ABSENCE_PROOF_PASS": all(v["dat"] for v in chung.values()),
            "expected_codes": ca["expected_codes"],
            "expected_stages": ca["expected_stages"],
            "scorer_chap_nhan_khai_bao": scorer_nhan,
            "scorer_loi": scorer_loi,
        })
    ok = all(r["ABSENCE_PROOF_PASS"] and r["scorer_chap_nhan_khai_bao"]
             for r in ra)
    return ok, {"khai": "Ranh giới của ca âm chứng minh bằng VẮNG MẶT, kiểm "
                        "được bằng máy. 0 lượt gọi model.",
                "boundary_evidence_class": "BOUNDARY_BY_ABSENCE_PROOF",
                "NEGATIVE_PREFLIGHT_PASS": ok, "cases": ra}


# ══ ⑦ CHỨNG NHẬN BỘ CHẤM — mỗi lớp có ít nhất một fixture ════════════════
_FIXTURE_NGUON = {
    "SYSTEM_COVERAGE_FAILURE":
        "gold p4, đổi DUY NHẤT tên `container` của nghĩa vụ — chương trình "
        "không đổi một byte. Cổng phủ bác, `nghia_vu_du_noi_dung_hut_ten` "
        "xác nhận nội dung ĐÚNG và chỉ hụt TÊN ⇒ lỗi HỢP ĐỒNG, tức lỗi HỆ.",
    "SYSTEM_EXPRESSIVENESS_GAP":
        "đề cho ĐƯỜNG KÍNH: `r = d//2` đúng toán, `arith` cho kiểu tĩnh "
        "`unknown`, ô `radius` chỉ nhận `scalar|float|int` ⇒ không có đường.",
    "ATTRIBUTION_UNRESOLVED":
        "CÙNG chương trình ấy, nhưng KHÔNG kèm `YeuCauNangLuc` — bộ chấm "
        "không có bằng chứng năng lực nên từ chối kết luận.",
    "MODEL_STATIC_FAILURE":
        "CÙNG chương trình ấy, kèm bằng chứng đề cho THẲNG bán kính ⇒ đường "
        "hợp lệ TỒN TẠI, mô hình tự chọn đường mơ hồ.",
    "MODEL_GROUNDING_FAILURE":
        "chương trình khai `initial_value` cho ba điểm mà đề không nêu ⇒ R0.",
}


def _fixture_that() -> dict[str, tuple]:
    """Năm fixture đi qua `verify_and_compile` THẬT.

    ⚠️ Ba fixture giữa dùng CHUNG một chương trình và chỉ khác ở **bằng chứng
    năng lực** kèm theo. Đó không phải tiết kiệm: nó là chính luận điểm của bộ
    chấm — cùng một cái chết ở `ir_static` phải cho ba phán quyết khác nhau tuỳ
    theo hệ có đường hay không, và tuỳ theo ta có biết điều đó hay không. Ba
    fixture riêng biệt sẽ che mất chỗ ấy.
    """
    import copy

    import acceptance_verdict as AV
    import thesis_acceptance_corpus as C
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.ir_static_check import _TOAN_HANG_LENH
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.route import verify_and_compile

    def _chay(hd, spec_raw, de):
        sp = SemanticProgramSpec.model_validate(spec_raw)
        ct = RequestContract(
            problem_text=de, input_facts=hd["input_facts"],
            obligations=tuple(Obligation(**o) for o in hd["obligations"]))
        return verify_and_compile(ct, sp), ct, sp

    ra: dict[str, tuple] = {}

    # ① cổng phủ bác vì TÊN, chương trình đúng nội dung
    p4 = C.theo_id("p4_hinh_tru_the_tich_va_xung_quanh")
    hd = copy.deepcopy(p4["request_contract_gold"])
    hd["obligations"] = [{"kind": "volume", "container": "khối trụ tròn xoay",
                          "params": {"witness": "V"}}]
    sp = copy.deepcopy(p4["gold_program"])
    sp["memory_declarations"] = [d for d in sp["memory_declarations"]
                                 if d["name"] != "Sxq"]
    sp["statements"] = [s for s in sp["statements"]
                        if s.get("target_var") != "Sxq"]
    ra["SYSTEM_COVERAGE_FAILURE"] = (*_chay(hd, sp, p4["problem_text"]), None)

    # ②③④ một chương trình, ba bằng chứng năng lực
    kieu_radius = frozenset(
        next(k for n, k, _l in _TOAN_HANG_LENH["construct_curved_solid"]
             if n == "radius"))
    hd_dk = {
        "input_facts": [
            {"fact_id": "tam", "label": "tâm O", "values": ["O"],
             "provenance": "confirmed"},
            {"fact_id": "dk", "label": "số đo", "values": [26],
             "provenance": "confirmed"}],
        "obligations": [{"kind": "volume", "container": "S",
                         "params": {"witness": "V"}}]}
    sp_dk = {
        "spec_version": "1.0", "title": "Mặt cầu từ đường kính",
        "memory_declarations": [
            {"name": "O", "type": "point3", "initial_value": [0, 0, 0],
             "source_fact_id": "tam"},
            {"name": "d", "type": "float", "initial_value": 26,
             "source_fact_id": "dk"},
            {"name": "r", "type": "float"},
            {"name": "S", "type": "curved_solid"},
            {"name": "V", "type": "float"}],
        "statements": [
            {"kind": "assign", "target_var": "r",
             "expr": {"kind": "arith", "op": "//",
                      "left": {"kind": "var", "name": "d"},
                      "right": {"kind": "literal", "value": 2}}},
            {"kind": "construct_curved_solid", "target_var": "S",
             "curved_kind": "ball", "anchor": "O", "radius": "r"},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "S"}}],
        "visual_bindings": {"containers": [], "pointers": [],
                            "value_boxes": []}}
    ba = _chay(hd_dk, sp_dk, "Cho mặt cầu tâm O, đường kính 26. Tính thể tích.")
    ra["SYSTEM_EXPRESSIVENESS_GAP"] = (*ba, AV.YeuCauNangLuc(
        o_dich="radius", kieu_o_dich=kieu_radius,
        kieu_nguon=frozenset({"float"}), can_bien_doi=True,
        phep_can="r = d/2"))
    ra["ATTRIBUTION_UNRESOLVED"] = (*ba, None)
    ra["MODEL_STATIC_FAILURE"] = (*ba, AV.YeuCauNangLuc(
        o_dich="radius", kieu_o_dich=kieu_radius,
        kieu_nguon=frozenset({"float"}), can_bien_doi=False,
        phep_can="dùng thẳng bán kính"))

    # ⑤ R0: toạ độ tự bịa
    hd_r0 = {
        "input_facts": [{"fact_id": "parabol", "label": "Parabol y = x²",
                         "values": ["y = x²"], "provenance": "confirmed"}],
        "obligations": [{"kind": "volume", "container": "khoi",
                         "params": {"witness": "V"}}]}
    sp_r0 = {
        "spec_version": "1.0", "title": "Khối bịa",
        "memory_declarations": [
            {"name": "T", "type": "point3", "initial_value": [2, 0, 0]},
            {"name": "O", "type": "point3", "initial_value": [0, 0, 0]},
            {"name": "A", "type": "point3", "initial_value": [2, 4, 0]},
            {"name": "khoi", "type": "curved_solid"},
            {"name": "V", "type": "float"}],
        "statements": [
            {"kind": "construct_curved_solid", "target_var": "khoi",
             "curved_kind": "cone", "anchor": "T", "apex_or_top": "O",
             "rim_point": "A"},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "khoi"}}],
        "visual_bindings": {"containers": [], "pointers": [],
                            "value_boxes": []}}
    ra["MODEL_GROUNDING_FAILURE"] = (
        *_chay(hd_r0, sp_r0, "Quay hình phẳng quanh Ox. Tính thể tích."), None)
    return ra



def scorer_preflight() -> tuple[bool, dict[str, Any]]:
    """Mỗi lớp trong `LOP_PHAN_QUYET` có SINH RA được không, và bằng đường nào?

    ⚠️ Phân biệt hai mức bằng chứng, và không được gộp:

        REAL_PATH          một `(contract, spec)` thật đi qua `verify_and_compile`
        SYNTHETIC_OUTCOME  một outcome dựng tay, chỉ chứng minh NHÁNH phân loại

    Mức hai yếu hơn hẳn — nó nói bộ chấm đọc đúng một trường, không nói hệ có
    bao giờ phát ra tình huống ấy. Ghi rõ mức, thay vì đếm gộp thành «13/13».
    """
    import acceptance_verdict as AV
    import thesis_acceptance_corpus as C
    from app.simulation.error_codes import ErrorCode

    class _Gia:
        def __init__(self, **kw):
            self.executable = kw.get("executable", False)
            self.servable = kw.get("servable", False)
            self.stage_reached = kw.get("stage_reached")
            self.error_code = kw.get("error_code")
            self.failure_category = kw.get("failure_category")
            self.details = kw.get("details", [])
            self.reason = kw.get("reason")
            self.final_memory = kw.get("final_memory", {})

    thu: dict[str, dict[str, Any]] = {}

    # ── REAL_PATH ①: gold ca p1 đi trọn tuyến ───────────────────────────
    r = _chay_gold(C.CA_DUONG[0])
    thu[r["verdict"]] = {"muc": "REAL_PATH", "nguon": f"gold {r['id']}"}

    # ── REAL_PATH ②–⑥: bốn biến thể chạy qua `verify_and_compile` thật ──
    for lop, (oc, ct, sp, yc) in _fixture_that().items():
        that = AV.phan_loai(oc, schema_ok=True, contract=ct, spec=sp,
                            yeu_cau=yc)
        if that == lop and lop not in thu:
            thu[lop] = {"muc": "REAL_PATH", "nguon": _FIXTURE_NGUON[lop]}

    # ── SYNTHETIC_OUTCOME cho phần còn lại ──────────────────────────────
    gia = {
        "CORRECT_EXECUTABLE_IR": _Gia(executable=True, stage_reached="served"),
        "HONEST_UNSUPPORTED_REFUSAL": None,   # đi qua `la_ca_am` + boundary_ok
        "UNRELATED_FAIL_CLOSED": None,
        "SYSTEM_VERIFICATION_FAILURE": _Gia(
            stage_reached="postconditions",
            error_code=ErrorCode.SEMANTIC_VERIFICATION_UNAVAILABLE.value),
        "SYSTEM_RUNTIME_FAILURE": _Gia(
            stage_reached="execution",
            error_code=ErrorCode.INTERPRETER_BUDGET_EXHAUSTED.value),
        "SYSTEM_TRANSPORT_FAILURE": _Gia(stage_reached="transport"),
        "MODEL_SCHEMA_FAILURE": _Gia(stage_reached="ir_static"),
        "MODEL_STATIC_FAILURE": _Gia(stage_reached="ir_static"),
        "MODEL_GROUNDING_FAILURE": _Gia(
            stage_reached="grounding",
            error_code=ErrorCode.INPUT_NOT_GROUNDED.value),
        "MODEL_FIRST_BINDING_FAILURE": _Gia(
            stage_reached="binding",
            error_code=ErrorCode.LEARNER_SURFACE_INCOMPLETE.value),
        "MODEL_COMPOSITION_FAILURE": _Gia(
            stage_reached="execution",
            error_code=ErrorCode.OBLIGATION_WITNESS_UNREALIZED.value),
        "SYSTEM_COVERAGE_FAILURE": None,      # cần đo hai thẩm quyền
        "SYSTEM_EXPRESSIVENESS_GAP": None,    # cần `YeuCauNangLuc`
        "ATTRIBUTION_UNRESOLVED": None,
    }
    for lop, oc in gia.items():
        if lop in thu or oc is None:
            continue
        that = AV.phan_loai(oc, schema_ok=(lop != "MODEL_SCHEMA_FAILURE"))
        if that == lop:
            thu[lop] = {"muc": "SYNTHETIC_OUTCOME", "nguon": "outcome dựng tay"}

    # Ba lớp cần đường riêng.
    if AV.phan_loai(_Gia(), schema_ok=True, la_ca_am=True,
                    boundary_ok=True) == "HONEST_UNSUPPORTED_REFUSAL":
        thu["HONEST_UNSUPPORTED_REFUSAL"] = {
            "muc": "SYNTHETIC_OUTCOME", "nguon": "la_ca_am + boundary_ok=True"}
    if AV.phan_loai(_Gia(), schema_ok=True, la_ca_am=True,
                    boundary_ok=False) == "UNRELATED_FAIL_CLOSED":
        thu["UNRELATED_FAIL_CLOSED"] = {
            "muc": "SYNTHETIC_OUTCOME", "nguon": "la_ca_am + boundary_ok=False"}
    yc_khong = AV.YeuCauNangLuc(
        o_dich="radius", kieu_o_dich=frozenset({"scalar"}),
        kieu_nguon=frozenset({"unknown"}), can_bien_doi=True,
        phep_can="chia đôi đường kính")
    if AV.duong_hop_le_ton_tai(yc_khong) == "NO":
        oc = _Gia(stage_reached="ir_static")
        if AV.phan_loai(oc, schema_ok=True,
                        yeu_cau=yc_khong) == "SYSTEM_EXPRESSIVENESS_GAP":
            thu["SYSTEM_EXPRESSIVENESS_GAP"] = {
                "muc": "SYNTHETIC_OUTCOME",
                "nguon": "YeuCauNangLuc không có đường biến đổi"}

    thieu = [l for l in AV.LOP_PHAN_QUYET if l not in thu]
    return not thieu, {
        "khai": "Mỗi lớp phán quyết có sinh ra được không, và bằng MỨC BẰNG "
                "CHỨNG nào. 0 lượt gọi model.",
        "taxonomy_authority": "acceptance_verdict.LOP_PHAN_QUYET",
        "LOP_TONG": len(AV.LOP_PHAN_QUYET),
        "co_fixture": thu,
        "REAL_PATH": sorted(k for k, v in thu.items()
                            if v["muc"] == "REAL_PATH"),
        "SYNTHETIC_OUTCOME": sorted(k for k, v in thu.items()
                                    if v["muc"] == "SYNTHETIC_OUTCOME"),
        "THIEU_FIXTURE": thieu,
        "SCORER_PREFLIGHT_PASS": not thieu,
        "lop_ngoai_scorer_canonical": {
            "MODEL_ANALYZE_FAILURE": "analyze hỏng ⇒ không có contract ⇒ "
                                     "`phan_loai` chưa từng được gọi",
            "SYSTEM_SCENE3D_FAILURE": "`servable` ⇒ CORRECT_SERVABLE_RESULT, "
                                      "nhãn không hạ khi cảnh hỏng",
        },
    }


# ══ ⑧ RUNNER SẴN SÀNG CHƯA — đo, không đoán ══════════════════════════════
_YEU_CAU_RUNNER = (
    ("doc_fixed_corpus", "đọc bộ ca CỐ ĐỊNH (không seed, không rút)"),
    ("mot_analyze_contract_moi_ca", "giữ một analyze contract cho từng ca"),
    ("manifest_truoc_provider_call", "ghi manifest TRƯỚC lượt gọi đầu"),
    ("giu_raw_analyze", "giữ raw analyze"),
    ("giu_moi_raw_candidate", "giữ MỌI raw synthesis/repair candidate"),
    ("scorer_canonical", "áp `acceptance_verdict` cho ca dương VÀ ca âm"),
    ("exact_result_authority", "đọc đáp số từ `final_memory`"),
    ("scene3d_san_pham", "dựng cảnh bằng `pipeline._dung_scene3d`"),
    ("dem_logic_va_vat_ly_rieng", "đếm lượt gọi logic ≠ lần thử vật lý"),
    ("dem_token_bon_loai", "đếm input/output/thought/cached"),
    ("dung_theo_ngan_sach", "dừng theo ngân sách"),
    ("xuat_per_case_va_aggregate", "xuất per-case và aggregate"),
    ("kiem_identity_truoc_moi_call", "kiểm danh tính trước MỖI lượt gọi"),
    ("hai_chang_A_B", "hai chặng A/B với repair limit 1"),
    ("nap_chinh_sach_khoa_luan", "nạp policy của khoá luận, không phải V3"),
)


def runner_readiness() -> tuple[bool, dict[str, Any]]:
    """Runner V3 có dùng lại được cho lượt cuối không? ĐỌC MÃ, không đoán.

    Câu trả lời quyết định `NEXT_ACTION`, nên nó phải dẫn từ mã nguồn — và mỗi
    dòng «không» phải chỉ đúng chỗ trong mã.
    """
    import thesis_acceptance_corpus as C

    p = BACKEND / "scripts" / "run_curved_acceptance.py"
    src = p.read_text(encoding="utf-8")
    cay = ast.parse(src)
    ten_ham = {n.name for n in ast.walk(cay)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    # Runner V3 chặn được corpus lạ tới đâu? ĐO cả hai cổng, đừng suy từ tên.
    #
    # ⚠️ ĐO ĐƯỢC 2026-09-08, và nó bác điều tôi đoán: `kiem_bo_ca_la_pool_v3`
    # là một **DANH SÁCH CẤM**, không phải danh sách cho phép — nó chỉ ném khi
    # id TRÙNG corpus phát triển V1/V2 (`ball_1`, `circumsphere`…). Một bộ ca
    # LẠ đi qua nó im lặng. Thứ thật sự chặn là `nap_ca_v3`: pool V3 đã rút và
    # `da_rut`/băm không còn khớp, nên nó ném trước khi tới bộ ca.
    #
    # Ghi ra vì đó là một khoảng trống có thật của bộ đo: nếu ai đó hồi sinh
    # một con dấu V3 hợp lệ, cổng còn lại sẽ KHÔNG phát hiện corpus bị đánh
    # tráo. Việc ấy thuộc `THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT`.
    import run_curved_acceptance as R
    from acceptance_integrity import IntegrityError

    try:
        R.kiem_bo_ca_la_pool_v3([{"id": c["id"]} for c in C.CA_DUONG])
        chan_bang_denylist = False
    except IntegrityError:
        chan_bang_denylist = True
    try:
        _c, _t, _h = R.nap_ca_v3()
        nguon_ghim_cung = [x["id"] for x in _c]
    except (IntegrityError, OSError, KeyError, ValueError):
        nguon_ghim_cung = []

    dat = {
        "doc_fixed_corpus": ("nap_ca_v3" not in ten_ham),
        "mot_analyze_contract_moi_ca": "request_contract" in src,
        "manifest_truoc_provider_call": "mo_luot_do_v3" in ten_ham,
        "giu_raw_analyze": '"request_contract"' in src,
        "giu_moi_raw_candidate": "raw_theo_tang" in src,
        "scorer_canonical": "cham_ca_am" in src,
        "exact_result_authority": "trich_ket_qua" in src,
        "scene3d_san_pham": "_dung_scene3d" in src,
        "dem_logic_va_vat_ly_rieng": "max_logical_calls" in src,
        "dem_token_bon_loai": "thoughts_tokens" in src,
        "dung_theo_ngan_sach": "BudgetExceeded" in src,
        "xuat_per_case_va_aggregate": "tom_tat" in src,
        "kiem_identity_truoc_moi_call": "canh_gac_truoc_luot_goi" in src,
        "hai_chang_A_B": "_TRAN_SUA = 1" in src,
        "nap_chinh_sach_khoa_luan": "thesis_final_acceptance_policy" in src,
    }
    khoang_trong = [
        {"yeu_cau": k, "mo_ta": m, "bang_chung": _bang_chung_gap(k, src)}
        for k, m in _YEU_CAU_RUNNER if not dat[k]]
    san_sang = not khoang_trong
    return san_sang, {
        "khai": "Runner cho lượt đo cuối — ĐO trên mã nguồn, không tự khai.",
        "runner_ung_vien": "scripts/run_curved_acceptance.py",
        "runner_ung_vien_hash": _bam_file(p),
        "danh_gia": dat,
        "V3_DENYLIST_BAC_CORPUS_KHOA_LUAN": chan_bang_denylist,
        "V3_NGUON_BO_CA_GHIM_CUNG": nguon_ghim_cung,
        "V3_CORPUS_GUARD_LA_DENYLIST_KHONG_PHAI_ALLOWLIST": True,
        "V3_CORPUS_GUARD_KHAI": (
            "Hai phép đo, và cùng nói một điều. ① `kiem_bo_ca_la_pool_v3` chỉ "
            "ném khi id TRÙNG corpus phát triển V1/V2 — một DANH SÁCH CẤM; bộ "
            "ca khoá luận đi qua nó im lặng. ② `main_async` lấy bộ ca DUY NHẤT "
            "từ `nap_ca_v3()`, và hàm ấy hiện vẫn trả về 13 ca V3 đã rút "
            "(`case_set_hash eb1c402a…`). Nên runner V3 không phải *"
            "'từ chối'* bộ ca khoá luận — nó KHÔNG CÓ ĐƯỜNG NÀO để nhận, và "
            "chạy nó lên sẽ lặng lẽ đo lại pool V3 ĐÃ TIÊU. Đó là hỏng theo "
            "kiểu đắt nhất: tiêu quota thật cho một câu hỏi đã trả lời."),
        "KHOANG_TRONG": khoang_trong,
        "FINAL_ACCEPTANCE_RUNNER_READY": "YES" if san_sang else "NO",
        "NEXT_ACTION": ("THESIS_FINAL_ACCEPTANCE_EXECUTION" if san_sang
                        else "THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT"),
    }


_BANG_CHUNG = {
    "doc_fixed_corpus":
        "`nap_ca_v3()` ĐÒI con dấu V3 đã rút; `kiem_bo_ca_la_pool_v3()` NÉM "
        "khi id không phải `C1`–`N4`. Bộ ca cố định không đi qua được.",
    "giu_moi_raw_candidate":
        "runner ghi `spec.model_dump()` của candidate CUỐI mỗi chặng; các "
        "attempt bên trong `stage_semantic_program` không được giữ.",
    "scorer_canonical":
        "ca âm chấm bằng `_cham_am`/`cham_ranh_gioi` của riêng runner, với "
        "danh sách mã `_MA_RANH_GIOI_CONG` ghim cứng cho hình cong — không "
        "phải `acceptance_verdict.cham_ca_am`.",
    "hai_chang_A_B":
        "chặng 8B khôi phục `MAX_SEMANTIC_PROGRAM_ATTEMPTS` về 3, không phải 2.",
    "nap_chinh_sach_khoa_luan":
        "`mo_luot_do_v3` gọi `MP.nap_nguong()` — hằng số trỏ "
        "`curved_v3_threshold_policy.json`; `acceptance_integrity.mo_run` "
        "cũng ghim `MP.CHINH_SACH_NGUONG` vào manifest.",
}


def _bang_chung_gap(khoa: str, _src: str) -> str:
    return _BANG_CHUNG.get(khoa, "không tìm thấy dấu hiệu trong mã runner")


# ══ ⑨ KHOÁ DANH TÍNH + KẾ HOẠCH CHẠY ═════════════════════════════════════
def dung_identity_lock(danh_tinh: dict, san_sang: bool) -> dict[str, Any]:
    import measurement_policy as MP
    import thesis_acceptance_corpus as C

    nguong, bam = MP.doc_chinh_sach(CHINH_SACH)
    model = MP.cau_hinh_model_hien_tai()
    verdict, thieu = MP.kiem_danh_tinh_model(model, nguong)
    return {
        "khai": "Danh tính BẤT BIẾN của lượt đo cuối, ghi TRƯỚC lượt gọi đầu "
                "tiên. Trường nào chưa quan sát được thì mang trạng thái CÓ "
                "KIỂU, không được lấp bằng văn xuôi.",
        "EVALUATION_VERSION": EVALUATION_VERSION,
        "EVALUATION_CLASS": nguong["evaluation_class"]["EVALUATION_CLASS"],
        "HELD_OUT_CLAIM": nguong["evaluation_class"]["HELD_OUT_CLAIM"],
        "OPERATOR_INDEPENDENCE_REQUIRED":
            nguong["evaluation_class"]["OPERATOR_INDEPENDENCE_REQUIRED"],
        "CREATED_BEFORE_LIVE_RUN": True,
        "tao_luc": datetime.now(timezone.utc).isoformat(),
        **{k: danh_tinh[k] for k in (
            "HEAD", "WORKING_TREE", "CACHE_VERSION", "CANDIDATE_HASH",
            "PROMPT_HASH", "GRAMMAR_CARD_HASH", "ANALYZE_SCHEMA_HASH",
            "SYNTHESIS_SCHEMA_HASH", "CAPABILITY_HASH",
            "SEMANTIC_ENVIRONMENT_HASH", "RUNNER_HASH", "SCORER_HASH",
            "POLICY_HASH", "POLICY_LOADER_HASH", "ATTRIBUTION_RUBRIC_HASH",
            "ORACLE_HASH", "CORPUS_MODULE_HASH")},
        "CORPUS_HASH": C.CORPUS_HASH,
        "EXPECTED_RESULTS_HASH": C.EXPECTED_RESULTS_HASH,
        "GOLD_PREFLIGHT_HASH": "GHI_SAU_KHI_CHAY",
        "MODEL_PROVIDER": model["provider"],
        "MODEL_NAME": model["model_name"],
        "MODEL_VERSION_OR_SNAPSHOT": model["model_version_or_snapshot"],
        "MODEL_REPRODUCIBILITY": verdict,
        "MODEL_LIMITATIONS_DECLARED": thieu,
        "RESPONSE_MODEL_VERSION": model["response_model_version"],
        "SDK": model["sdk"],
        "API_ENDPOINT_CLASS": model["api_endpoint_class"],
        "TEMPERATURE": model["decoding_parameters"]["temperature"],
        "TOP_P": model["decoding_parameters"]["top_p"],
        "MAX_OUTPUT_TOKENS": model["decoding_parameters"]["max_output_tokens"],
        "PRODUCT_REPAIR_LIMIT": model["repair_limit"],
        "REPAIR_LIMIT_FOR_THIS_RUN": nguong["run_plan"]["stage_b"]["repair"],
        "LOGICAL_CALL_BUDGET": nguong["budget"]["MAX_LOGICAL_CALLS"],
        "PHYSICAL_ATTEMPT_BUDGET": nguong["budget"]["MAX_PHYSICAL_ATTEMPTS"],
        "TOKEN_BUDGET": nguong["budget"]["HARD_TOKEN_BUDGET"],
        "TRANSPORT_RETRY_POLICY": model["transport_retry_policy"],
        "POLICY_HASH_recompute": bam,
        "RUNNER_READY": "YES" if san_sang else "NO",
        "LOCK_STATE": ("READY_TO_EXECUTE" if san_sang
                       else "LOCKED_PENDING_RUNNER_ALIGNMENT"),
    }


def dung_run_plan(nguong: dict, sansang: dict) -> dict[str, Any]:
    import measurement_policy as MP

    a = MP.derive_application_call_budget(
        selected_cases=9, analyze_calls_per_case=1,
        synthesis_attempt_limit=1, calls_per_attempt=1)
    b = MP.derive_application_call_budget(
        selected_cases=7, analyze_calls_per_case=1,
        synthesis_attempt_limit=2, calls_per_attempt=1)
    return {
        "khai": "Kế hoạch chạy lượt đo cuối. Ngân sách DẪN từ call graph.",
        "wave": WAVE,
        "stage_a": nguong["run_plan"]["stage_a"],
        "stage_b": nguong["run_plan"]["stage_b"],
        "budget": nguong["budget"],
        "budget_dan_lai_tu_call_graph": {
            "stage_a": a, "stage_b": b, "tong": a + b,
            "khop_policy": (a + b) == nguong["budget"]["MAX_LOGICAL_CALLS"]},
        "scoring_dimensions": [
            "SCOPE_PASS", "ANALYZE_CONTRACT_CORRECT", "PROGRAM_SCHEMA_VALID",
            "IR_STATIC_PASS", "GROUNDING_PASS", "COVERAGE_PASS",
            "SOURCE_INVARIANTS_PASS", "RUNTIME_PASS", "POSTCONDITIONS_PASS",
            "EXACT_ANSWER_MATCH", "ORACLE_NUMERIC_AGREEMENT", "TRACE_PASS",
            "SCENE3D_PASS", "FIRST_ATTEMPT_SERVABLE", "RECOVERY_SERVABLE",
            "NEGATIVE_FAIL_CLOSED", "TARGET_BOUNDARY_PASS"],
        "cot_doc_lap_khong_duoc_suy_lan_nhau": [
            "EXACT_ANSWER_MATCH", "SCENE3D_PASS", "FIRST_ATTEMPT_SERVABLE"],
        "FINAL_ACCEPTANCE_RUNNER_READY":
            sansang["FINAL_ACCEPTANCE_RUNNER_READY"],
        "RUNNER_GAPS": sansang["KHOANG_TRONG"],
        "NEXT_ACTION": sansang["NEXT_ACTION"],
    }


# ══ MAIN ═════════════════════════════════════════════════════════════════
def main() -> int:
    import measurement_policy as MP
    import thesis_acceptance_corpus as C

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", default=str(RA))
    a = p.parse_args()
    out = Path(a.out_dir)

    print(f"{WAVE} — 0 lượt gọi model\n")
    dt = do_danh_tinh()
    print(f"  HEAD {dt['HEAD_ngan']} · cache {dt['CACHE_VERSION']} · "
          f"candidate {dt['CANDIDATE_HASH'][:16]}… ({dt['CANDIDATE_FILE_COUNT']} file)")
    print(f"  working tree {dt['WORKING_TREE']}\n")

    ok2, tt = kiem_trang_thai_du_kien()
    print(f"  ② trạng thái dự kiến      {'PASS' if ok2 else 'FAIL'}")
    ok3, mtx = dung_capability_matrix(dt)
    print(f"  ③ ma trận năng lực        {'PASS' if ok3 else 'FAIL'}  "
          f"({len(mtx['families'])} họ)")
    ok4, claims = dung_claims_matrix(dt)
    print(f"  ④ ma trận tuyên bố        {'PASS' if ok4 else 'FAIL'}  "
          f"({claims['CLAIMS_TOTAL']} tuyên bố)")
    ok4b, lich_su = phan_loai_bang_chung_lich_su(dt["CANDIDATE_HASH"])
    print(f"  ④b bằng chứng lịch sử     "
          f"{lich_su['TONG_ARTIFACT_CO_DANH_TINH']} artifact · "
          f"{lich_su['KHOP_CANDIDATE_HIEN_TAI']} khớp candidate hiện tại")
    ok5, gold = gold_preflight()
    print(f"  ⑤ gold preflight          {'PASS' if ok5 else 'FAIL'}")
    for k, v in gold["tong_ket"].items():
        print(f"       {k:26} {v}")
    ok6, am = negative_preflight()
    print(f"  ⑥ ca âm (vắng mặt)        {'PASS' if ok6 else 'FAIL'}")
    ok7, sc = scorer_preflight()
    print(f"  ⑦ bộ chấm                 {'PASS' if ok7 else 'FAIL'}  "
          f"({len(sc['co_fixture'])}/{sc['LOP_TONG']} lớp có fixture)")
    ready, rn = runner_readiness()
    print(f"  ⑧ runner sẵn sàng         {rn['FINAL_ACCEPTANCE_RUNNER_READY']}"
          f"  ({len(rn['KHOANG_TRONG'])} khoảng trống)")

    nguong, _b = MP.doc_chinh_sach(CHINH_SACH)
    loi_cs = MP.kiem_chinh_sach(nguong, candidate_hash=dt["CANDIDATE_HASH"],
                                pool_hash=C.CORPUS_HASH)
    print(f"  ⑨ chính sách              {'PASS' if not loi_cs else 'FAIL'}")
    for l in loi_cs:
        print(f"       ✗ {l}")

    khoa = dung_identity_lock(dt, ready)
    ke_hoach = dung_run_plan(nguong, rn)

    out.mkdir(parents=True, exist_ok=True)
    _ghi(out / "CAPABILITY_MATRIX.json", mtx)
    _ghi(out / "CLAIMS_MATRIX.json", claims)
    _ghi(out / "CORPUS.json", C.corpus_json())
    _ghi(out / "EXPECTED_RESULTS.json", C.expected_results_json())
    _ghi(out / "GOLD_PREFLIGHT.json", {**gold, "ca_am": am,
                                       "scorer": sc, "trang_thai_dau_vao": tt})
    _ghi(out / "EVIDENCE_CLASSIFICATION.json", lich_su)
    _ghi(out / "EVALUATION_POLICY.json", nguong)
    gph = hashlib.sha256(
        (out / "GOLD_PREFLIGHT.json").read_bytes()).hexdigest()
    _ghi(out / "IDENTITY_LOCK.json", {**khoa, "GOLD_PREFLIGHT_HASH": gph})
    _ghi(out / "RUN_PLAN.json", ke_hoach)

    tat_ca = (ok2 and ok3 and ok4 and ok4b and ok5 and ok6 and ok7
              and not loi_cs)
    print(f"\n  THESIS_ACCEPTANCE_MATRIX  {'PASS' if tat_ca else 'FAIL'}")
    print(f"  FEATURE_SCOPE_COMPLETE    {mtx['FEATURE_SCOPE_COMPLETE']}")
    print(f"  APPLICATION_LLM_CALLS     0")
    print(f"  CORPUS_HASH               {C.CORPUS_HASH[:16]}…")
    print(f"  POLICY_HASH               {dt['POLICY_HASH'][:16]}…")
    print(f"  IDENTITY_LOCK             {khoa['LOCK_STATE']}")
    print(f"  NEXT_ACTION               {ke_hoach['NEXT_ACTION']}")
    print(f"\n→ {out}")
    return 0 if tat_ca else 1


if __name__ == "__main__":
    raise SystemExit(main())
