# -*- coding: utf-8 -*-
"""CHỨNG NHẬN BỘ ĐO — chạy TRỌN vòng đời một lượt đo, **0 lượt gọi model.**

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \\
        scripts/certify_acceptance_runner.py [--out-dir <thư mục>]

    `ACCEPTANCE_RUNNER_INTEGRITY` §25, 2026-09-04.

─── VÌ SAO CHỨNG NHẬN LẮP RÁP, KHÔNG PHẢI TỪNG MẢNH ───────────────────────

`tests/test_acceptance_runner_integrity.py` kiểm từng nguyên hàm. Nhưng bảy sự
cố lịch sử **không** nằm trong một nguyên hàm nào — chúng nằm ở chỗ ráp: runner
gọi đúng hàm ghi nhưng đọc sai trường; ghi đúng artifact nhưng tổng kết từ bộ
nhớ; phân loại đúng một ca nhưng ca âm thì không ai chấm. Nên ở đây chạy **trọn
vòng đời**: mở lượt → manifest → từng ca → artifact → tóm tắt → tự kiểm.

─── CÁI GÌ LÀ GIẢ, CÁI GÌ LÀ THẬT ─────────────────────────────────────────

**Giả đúng MỘT thứ: provider.** `RequestContract` và `SemanticProgramSpec` của
mỗi ca đóng sẵn trong file này (thay cho hai lượt gọi LLM).

**Mọi thứ sau đó là THẬT**: `verify_and_compile` thật, cổng phủ thật, checker
thật, `final_memory` thật. Nếu chỉ dựng `FakeOutcome` thì bài kiểm này chứng
minh bộ phân loại khớp với chính giả định của tôi về route — chứ không chứng
minh nó khớp với route.

Hai ca dưới đây là **lỗ đang có thật trong hệ**, không phải tình huống bịa:

    CA4  `angle` trên `vector3` — `KHONG_KIEM_DUOC` đã khai từ
         `VERIFICATION_CAPABILITY_IDENTITY`. Chạy được, không chứng thực được.
    CA5  nghĩa vụ `volume` gắn vào chủ thể `point3` — cổng phủ bác đúng.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any

_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND))               # gói `app`
sys.path.insert(0, str(_BACKEND / "scripts"))   # anh em cùng thư mục

from acceptance_integrity import (  # noqa: E402
    ARTIFACT_SCHEMA_VERSION,
    IntegrityError,
    chuan_hoa_telemetry,
    ghi_artifact,
    kiem_bo_ca,
    kiem_moi_truong,
    mo_run,
    tom_tat_tu_artifact,
    tu_kiem_tom_tat,
)
from acceptance_verdict import (  # noqa: E402
    cham_ca_am,
    co_giai_doan,
    phan_loai,
    sua_duoc,
    trich_ket_qua,
)


def _md(n, t, iv=None, fact=None, ass=None) -> dict:
    d: dict[str, Any] = {"name": n, "type": t}
    if iv is not None:
        d["initial_value"] = iv
    if fact:
        d["source_fact_id"] = fact
    if ass:
        d["model_assumption"] = ass
    return d


def _fact(fid, nhan, *gt) -> dict:
    return {"fact_id": fid, "label": nhan, "values": list(gt),
            "provenance": "confirmed"}


_VB = {"containers": [], "pointers": [], "value_boxes": []}

# ══════════════════════════════════════════════════════════════════════════
# NĂM KỊCH BẢN — mỗi ca khai TRƯỚC lớp nó phải rơi vào (§25)
# ══════════════════════════════════════════════════════════════════════════
CA: list[dict[str, Any]] = [
    {
        "id": "duong_1_dung", "loai": "duong",
        "de": "Cho mặt cầu (S) tâm I đi qua A, biết IA = 6. Tính bán kính và "
              "thể tích khối cầu (S).",
        "mong_lop": "CORRECT_SERVABLE_RESULT",
        "mong_dai_luong": {"R": "6", "V": "288π"},
        "facts": [_fact("tam", "Tâm (S)", "I"), _fact("qua", "(S) đi qua", "A"),
                  _fact("ia", "IA", "6")],
        "obligations": [{"kind": "radius", "container": "S",
                         "params": {"witness": "R"}},
                        {"kind": "volume", "container": "S",
                         "params": {"witness": "V"}}],
        "spec": {
            "spec_version": "1.0", "title": "Bán kính và thể tích khối cầu",
            "description": "Dựng mặt cầu từ tâm và một điểm, rồi đo.",
            "pedagogical_intent": "Thấy bán kính quyết định thể tích.",
            "memory_declarations": [
                _md("I", "point3", [0, 0, 0], "tam"),
                _md("A", "point3", [6, 0, 0], "qua",
                    "Đặt A trên Ox để IA = 6"),
                _md("S", "curved_solid"), _md("R", "float"), _md("V", "float")],
            "statements": [
                {"kind": "construct_curved_solid", "target_var": "S",
                 "curved_kind": "ball", "anchor": "I", "rim_point": "A",
                 "label": "(S)"},
                {"kind": "assign", "target_var": "R",
                 "expr": {"kind": "measure", "quantity": "radius", "of": "S"}},
                {"kind": "assign", "target_var": "V",
                 "expr": {"kind": "measure", "quantity": "volume", "of": "S"}}],
            "visual_bindings": _VB},
    },
    {
        # Lược đồ hỏng ⇒ `stage_semantic_program` trả `(None, err)`. Ca này
        # KHÔNG có `spec`: đó chính là hình dạng thất bại của nó.
        "id": "duong_2_schema_hong", "loai": "duong",
        "de": "Cho hình chóp S.ABCD. Tính thể tích khối chóp.",
        "mong_lop": "MODEL_SCHEMA_FAILURE", "mong_sua_duoc": True,
        "facts": [_fact("chop", "Hình chóp", "S.ABCD")],
        "obligations": [{"kind": "volume", "container": "K",
                         "params": {"witness": "V"}}],
        "spec": None,
        "loi_schema": "1 validation error for SemanticProgramSpec\n"
                      "statements.0.construct_point.expr.tra…",
    },
    {
        "id": "duong_3_bia_diem", "loai": "duong",
        "de": "Cho tứ diện ABCD. Tính bán kính mặt cầu ngoại tiếp.",
        "mong_lop": "MODEL_GROUNDING_FAILURE", "mong_sua_duoc": True,
        "facts": [_fact("td", "Tứ diện", "ABCD")],
        "obligations": [{"kind": "radius", "container": "cau",
                         "params": {"witness": "R"}}],
        "spec": {
            "spec_version": "1.0", "title": "Bán kính mặt cầu ngoại tiếp",
            "description": "Chương trình BỊA tâm rồi đo bán kính.",
            "pedagogical_intent": "Ca kiểm cổng xuất xứ.",
            "memory_declarations": [
                _md("A", "point3", [0, 0, 0], "td"),
                # Không `source_fact_id` — toạ độ không có nguồn. R0 phải bác.
                _md("I_bia", "point3", [1, 1, 1], None,
                    "tâm mặt cầu ngoại tiếp"),
                _md("cau", "curved_solid"), _md("R", "float")],
            "statements": [
                {"kind": "construct_curved_solid", "target_var": "cau",
                 "curved_kind": "ball", "anchor": "I_bia", "rim_point": "A"},
                {"kind": "assign", "target_var": "R",
                 "expr": {"kind": "measure", "quantity": "radius",
                          "of": "cau"}}],
            "visual_bindings": _VB},
    },
    {
        # LỖ THẬT, đang có: `check_angle` chỉ tính lại cos², không chứng thực
        # được nhân chứng của `angle_cos(vector3)`.
        "id": "duong_4_he_hut_verification", "loai": "duong",
        "de": "Cho O(0;0;0), A(1;0;0), B(0;1;0). Tính côsin góc giữa hai vectơ "
              "OA và OB.",
        "mong_lop": "SYSTEM_VERIFICATION_FAILURE", "mong_sua_duoc": False,
        "facts": [_fact("o", "O", "O(0;0;0)"), _fact("a", "A", "A(1;0;0)"),
                  _fact("b", "B", "B(0;1;0)")],
        "obligations": [{"kind": "angle", "container": "u",
                         "params": {"witness": "c", "wrt": "v"}}],
        "spec": {
            "spec_version": "1.0", "title": "Góc giữa hai vectơ",
            "description": "Dựng hai vectơ rồi đo côsin có dấu.",
            "pedagogical_intent": "Thấy dấu của côsin phụ thuộc chiều vectơ.",
            "memory_declarations": [
                _md("O", "point3", [0, 0, 0], "o"),
                _md("A", "point3", [1, 0, 0], "a"),
                _md("B", "point3", [0, 1, 0], "b"),
                _md("u", "vector3"), _md("v", "vector3"), _md("c", "float")],
            "statements": [
                {"kind": "assign", "target_var": "u",
                 "expr": {"kind": "vector_from_points", "from_point": "O",
                          "to_point": "A"}},
                {"kind": "assign", "target_var": "v",
                 "expr": {"kind": "vector_from_points", "from_point": "O",
                          "to_point": "B"}},
                {"kind": "assign", "target_var": "c",
                 "expr": {"kind": "measure", "quantity": "angle_cos",
                          "of": "u", "wrt": "v"}}],
            "visual_bindings": _VB},
    },
    {
        "id": "am_1_ngoai_pham_vi", "loai": "am",
        "de": "Cho A(0;0;0) và B(1;0;0). Tính thể tích khối tạo bởi hai điểm.",
        "mong_lop": "HONEST_UNSUPPORTED_REFUSAL",
        "target_boundary": "nghĩa vụ ĐO gắn vào chủ thể mà hợp đồng không cho",
        "expected_codes": ["requested_operation_uncovered"],
        "facts": [_fact("a", "A", "A(0;0;0)"), _fact("b", "B", "B(1;0;0)")],
        "obligations": [{"kind": "volume", "container": "A",
                         "params": {"witness": "d"}}],
        "spec": {
            "spec_version": "1.0", "title": "Đo trên chủ thể sai kiểu",
            "description": "Ca âm: nghĩa vụ thể tích gắn vào một ĐIỂM.",
            "pedagogical_intent": "Ca kiểm ranh giới phủ.",
            "memory_declarations": [
                _md("A", "point3", [0, 0, 0], "a"),
                _md("B", "point3", [1, 0, 0], "b"), _md("d", "float")],
            "statements": [
                {"kind": "assign", "target_var": "d",
                 "expr": {"kind": "measure", "quantity": "distance",
                          "of": "A", "wrt": "B"}}],
            "visual_bindings": _VB},
    },
]


def _chay_mot_ca(c: dict, thu_muc: Path, mt_goc: dict) -> dict[str, Any]:
    """Một ca đi trọn đường — provider giả, route THẬT."""
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.route import verify_and_compile

    # §17 — môi trường phải còn nguyên TRƯỚC mỗi "lượt gọi".
    kiem_moi_truong(mt_goc, nhan=f"ca {c['id']}")

    contract = RequestContract(
        problem_text=c["de"], input_facts=c["facts"],
        obligations=tuple(Obligation(**o) for o in c["obligations"]))

    # §4 — ghi TRƯỚC khi phán quyết, đủ để replay tất định về sau.
    ghi_artifact(thu_muc / "cases" / c["id"] / "analyze.json", {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION, "id": c["id"],
        "de": c["de"],
        "request_contract": {
            "problem_text": contract.problem_text,
            "input_facts": [f.model_dump(mode="json")
                            for f in contract.input_facts],
            "obligations": [o.model_dump(mode="json")
                            for o in contract.obligations]}})

    schema_ok = c["spec"] is not None
    outcome = None
    if schema_ok:
        spec = SemanticProgramSpec.model_validate(c["spec"])
        ghi_artifact(thu_muc / "cases" / c["id"] / "synthesis-one-shot.json", {
            "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
            "id": c["id"], "chuong_trinh": spec.model_dump(mode="json")})
        outcome = verify_and_compile(contract, spec)

    la_am = c["loai"] == "am"
    bien = cham_ca_am(c, outcome, schema_ok=schema_ok) if la_am else None
    lop = phan_loai(
        outcome, schema_ok=schema_ok, la_ca_am=la_am,
        boundary_ok=(bien or {}).get("target_boundary_demonstrated"))
    ok_sua, ly_do_sua = sua_duoc(
        outcome, schema_ok=schema_ok,
        error_code=None if schema_ok else "schema")

    # Telemetry GIẢ nhưng đúng HÌNH DẠNG của `usage_report()` — chứng nhận này
    # đo đường ráp, không đo provider. Hai "lượt gọi" = analyze + synthesis.
    tho = {"semantic_analyze": {
        "prompt_tokens": 900, "candidates_tokens": 120, "thoughts_tokens": 200,
        "cached_content_tokens": 0, "total_tokens": 1220, "calls": 1}}
    goi = {"analyze": 1, "synthesis": 0, "repair": 0}
    if schema_ok:
        tho["semantic_program"] = {
            "prompt_tokens": 1500, "candidates_tokens": 400,
            "thoughts_tokens": 700, "cached_content_tokens": 0,
            "total_tokens": 2600, "calls": 1}
        goi["synthesis"] = 1

    ra = {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "id": c["id"], "loai": c["loai"], "de": c["de"],
        "request_contract": {
            "problem_text": contract.problem_text,
            "input_facts": [f.model_dump(mode="json")
                            for f in contract.input_facts],
            "obligations": [o.model_dump(mode="json")
                            for o in contract.obligations]},
        "chuong_trinh": c["spec"],
        "loi_schema": c.get("loi_schema"),
        "giai_doan": co_giai_doan(outcome, schema_ok=schema_ok),
        "ket_qua": trich_ket_qua(outcome) if outcome else
                   {"nguon": "outcome.final_memory", "dai_luong": {}},
        "error_code": getattr(outcome, "error_code", None),
        "failure_category": getattr(outcome, "failure_category", None),
        "details": list(getattr(outcome, "details", None) or []),
        "phan_lop": lop,
        "repair_eligible": ok_sua, "repair_reason": ly_do_sua,
        "goi_provider": goi,
        "telemetry": chuan_hoa_telemetry(tho),
    }
    if bien is not None:
        ra.update(bien)
    ghi_artifact(thu_muc / "cases" / c["id"] / "final.json", ra)
    return ra


def chung_nhan(thu_muc: Path) -> tuple[bool, list[str]]:
    mt = None
    from acceptance_integrity import moi_truong_hien_tai

    mt = moi_truong_hien_tai()
    mf = mo_run(
        thu_muc, run_id=thu_muc.name,
        muc_dich="CHỨNG NHẬN BỘ ĐO — không phải một lượt đo năng lực",
        runner=str(Path(__file__).resolve()), ca=CA,
        model={"provider": "GIẢ (đóng sẵn trong file chứng nhận)",
               "application_llm_calls": 0},
        chinh_sach_sua="đọc từ `pipeline._sinh_chuong_trinh` qua `sua_duoc()`",
        ngan_sach_goi=0, bo_qua_dirty=True)

    sai: list[str] = []
    for c in CA:
        kiem_bo_ca(mf.seal, CA)               # §5, trước MỖI ca
        r = _chay_mot_ca(c, thu_muc, mt)
        if r["phan_lop"] != c["mong_lop"]:
            sai.append(f"{c['id']}: mong '{c['mong_lop']}', "
                       f"thực '{r['phan_lop']}'")
        if "mong_dai_luong" in c and r["ket_qua"]["dai_luong"] != \
                c["mong_dai_luong"]:
            sai.append(f"{c['id']}: đại lượng {r['ket_qua']['dai_luong']} "
                       f"≠ mong {c['mong_dai_luong']}")
        if "mong_sua_duoc" in c and r["repair_eligible"] != c["mong_sua_duoc"]:
            sai.append(f"{c['id']}: repair_eligible {r['repair_eligible']} "
                       f"≠ mong {c['mong_sua_duoc']}")
        print(f"  {c['id']:<28} {r['phan_lop']}")

    tt = tom_tat_tu_artifact(thu_muc)
    ghi_artifact(thu_muc / "summary.json", tt)
    try:
        tu_kiem_tom_tat(thu_muc)              # §23
    except IntegrityError as e:
        sai.append(f"tự kiểm tóm tắt: {e}")
    if tt["APPLICATION_LLM_CALLS"] != 9:
        sai.append(f"số lượt gọi ghi nhận {tt['APPLICATION_LLM_CALLS']} ≠ 9")
    return not sai, sai


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", default=None,
                   help="mặc định: một thư mục tạm, xoá sau khi chạy")
    a = p.parse_args()

    print("CHỨNG NHẬN BỘ ĐO — 0 lượt gọi model\n")
    with tempfile.TemporaryDirectory() as tam:
        goc = Path(a.out_dir) if a.out_dir else Path(tam)
        ok, sai = chung_nhan(goc / "cert-run")
    print()
    for s in sai:
        print(f"  ✗ {s}")
    print(f"\n  RUNNER_CERTIFICATION   {'PASS' if ok else 'FAIL'}")
    print(f"  APPLICATION_LLM_CALLS  0")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
