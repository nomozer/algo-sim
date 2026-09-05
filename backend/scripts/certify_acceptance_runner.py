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
import contextlib
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
    doc_artifact,
    ghi_artifact,
    kiem_bo_ca,
    kiem_ghim_bo_do,
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


def chung_nhan(thu_muc: Path) -> tuple[bool, list[str], list[str]]:
    """`(bộ đo có đúng không, lỗi, còn thiếu gì trước khi được chạy live)`.

    Ba giá trị chứ không hai: phần tử thứ ba KHÔNG phải lỗi của bộ đo, nên nó
    không được kéo verdict xuống FAIL — xem §G ở cuối hàm.
    """
    mt = None
    from acceptance_integrity import (
        ARTIFACT_SCHEMA_VERSION, moi_truong_hien_tai)

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

    # ─── §F · DANH TÍNH BỘ ĐO ĐÃ GHIM CHƯA, VÀ CÓ TRÔI KHÔNG ────────────
    #
    # Trước 2026-09-04 certifier chỉ khoá `runner_hash`. Hệ quả: bộ CHẤM,
    # NGƯỠNG và RUBRIC đổi được giữa reseal và lượt live mà không cổng nào
    # thấy — và đổi ngưỡng sau khi biết kết quả là cách rẻ nhất để một phép đo
    # nói bất cứ điều gì ta muốn.
    import measurement_policy as MP

    # Đọc manifest TỪ ĐĨA, không dùng `mf` trong bộ nhớ: đây là đúng hình thù
    # phép kiểm mà lượt live cần — so bản ĐÃ GHI với thực tế hiện tại. Trong
    # chính lượt chứng nhận này nó luôn khớp (không có gì kịp đổi), nên giá
    # trị của nó ở đây là chứng minh ĐƯỜNG ĐI chạy được, không phải bắt trôi.
    nguong, _bn = MP.nap_nguong()
    sai += kiem_ghim_bo_do(doc_artifact(thu_muc / "manifest.json"))
    if mf.artifact_schema_version != ARTIFACT_SCHEMA_VERSION:
        sai.append(f"artifact_schema_version {mf.artifact_schema_version} ≠ "
                   f"{ARTIFACT_SCHEMA_VERSION}")

    # Chính sách có đủ trường và có trỏ đúng hệ đang đo không?
    import freeze_evaluation_candidate as _F
    import seal_curved_v3 as _S
    import json as _json

    he, _n = _F.measured_system_hash()
    _bai = _json.loads(_S.POOL.read_text(encoding="utf-8"))["bai"]
    sai += MP.kiem_chinh_sach(nguong, candidate_hash=he,
                              pool_hash=_S._bam(_bai))

    tt = tom_tat_tu_artifact(thu_muc)
    ghi_artifact(thu_muc / "summary.json", tt)
    try:
        tu_kiem_tom_tat(thu_muc)              # §23
    except IntegrityError as e:
        sai.append(f"tự kiểm tóm tắt: {e}")
    if tt["APPLICATION_LLM_CALLS"] != 9:
        sai.append(f"số lượt gọi ghi nhận {tt['APPLICATION_LLM_CALLS']} ≠ 9")

    # ─── §G · SẴN SÀNG LIVE — CÂU HỎI KHÁC, VERDICT KHÁC ────────────────
    #
    # Lượt chứng nhận này chạy trên ca TỔNG HỢP với `model={"provider":
    # "gia"}`. Bắt nó ghim snapshot model là bắt một ca giả khai danh tính
    # thật, và cách duy nhất để nó xanh là nói dối. Nên readiness đo trên
    # CẤU HÌNH THẬT của kho, và trả về RIÊNG — không trộn vào PASS/FAIL.
    return (not sai, sai) + (MP.san_sang_live_tu_cau_hinh(nguong),)


@contextlib.contextmanager
def _con_dau_tong_hop(thu_muc: Path):
    """Trỏ `seal_curved_v3` sang một con dấu TỔNG HỢP mang băm hệ HIỆN TẠI.

    ⚠️ Vì sao bài chứng nhận không được dùng con dấu THẬT. Từ 2026-09-05
    (`CURVED_CONSTRUCTION_GROUNDING_FOUNDATION`) V3 đã **tiêu**: pool đã rút,
    và candidate mà nó niêm phong (`a696200e…`) không còn là hệ đang chạy. Nên
    `_kiem_con_dau_va_candidate` — đúng đắn — từ chối mọi lượt mở trên con dấu
    ấy. Một bài chứng nhận neo vào đó sẽ đỏ vĩnh viễn vì một lý do không liên
    quan gì tới thứ nó đang chứng nhận: **đường dây**, không phải pool nào.
    """
    import seal_curved_v3 as SC

    pool, dau, chon, bam = _pool_gia(thu_muc)
    goc_pool, goc_dau = SC.POOL, SC.DAU
    SC.POOL, SC.DAU = pool, dau
    try:
        yield pool, dau, chon, bam
    finally:
        SC.POOL, SC.DAU = goc_pool, goc_dau


def chung_nhan_runner_v3(thu_muc: Path) -> tuple[bool, list[str]]:
    """Runner V3 THẬT có đi qua tầng toàn vẹn không — 12 phép kiểm, §I.

    ⚠️ Vì sao cần một bài riêng, chứ không dựa vào `chung_nhan` ở trên:
    `chung_nhan` chạy **bài kiểm tổng hợp của chính nó**. Nó xanh cả trong
    suốt quãng `run_curved_acceptance.py` chưa chạm `mo_run` một lần nào —
    tức "chứng nhận PASS" và "runner V3 đã lắp" là hai câu, và trước
    2026-09-05 câu thứ hai là SAI trong khi câu thứ nhất vẫn xanh.

    Provider ở đây là **giả** và không bao giờ được gọi thật: bài này chứng
    minh *thứ tự* và *cổng*, không đo mô hình. `APPLICATION_LLM_CALLS = 0`.
    """
    import json as _json

    import measurement_policy as MP
    import run_curved_acceptance as R
    from acceptance_integrity import (
        ARTIFACT_SCHEMA_VERSION as ASV,
    )
    from acceptance_integrity import (
        IntegrityError as IE,
    )
    from acceptance_integrity import (
        kiem_ghim_bo_do,
        kiem_manifest_du_truong,
    )

    sai: list[str] = []
    ca = [{"id": f"CERT{i}", "loai": "duong", "de": f"đề tổng hợp {i}",
           "mong": ["1"]} for i in (1, 2)]
    # Con dấu THẬT của V3 niêm phong một candidate không còn tồn tại; xem
    # `_con_dau_tong_hop`. Bài này chứng nhận ĐƯỜNG DÂY, không chứng nhận pool.
    _ngan_xep = contextlib.ExitStack()
    _ngan_xep.enter_context(_con_dau_tong_hop(thu_muc.parent / "v3-dau-gia"))
    goi: list[str] = []                 # nhật ký thứ tự, do provider giả ghi
    duong = thu_muc / "manifest.json"

    def provider_gia(nhan: str) -> None:
        """Mỗi lượt gọi giả PHẢI đi sau `canh_gac_truoc_luot_goi`."""
        goi.append(nhan)

    # ① manifest tồn tại TRƯỚC lượt gọi giả đầu tiên
    R.mo_luot_do_v3(thu_muc, run_id=thu_muc.name, ca=ca,
                    bo_qua_dirty=True, gia_lap=True)
    if goi:
        sai.append("đã có lượt gọi TRƯỚC khi manifest được ghi")
    if not duong.exists():
        # DỪNG SẠCH, không để `FileNotFoundError` bay ra: một bài chứng nhận
        # ném stack trace đọc như lỗi hạ tầng, và lỗi hạ tầng thì người ta
        # chạy lại chứ không đọc. Đây là FAIL, và phải nói thành FAIL.
        sai.append(f"KHÔNG có manifest ở {duong} — runner V3 không đi qua "
                   f"`mo_run`, tầng toàn vẹn không nằm trên đường chạy")
        return False, sai
    d = _json.loads(duong.read_text(encoding="utf-8"))

    # ② schema version · ③ bốn băm · ④ version + băm chính sách
    if d.get("artifact_schema_version") != ASV:
        sai.append(f"artifact_schema_version {d.get('artifact_schema_version')}"
                   f" ≠ {ASV}")
    sai += kiem_manifest_du_truong(d) + kiem_ghim_bo_do(d)
    nguong, bam_nguong = MP.nap_nguong()
    if d.get("threshold_policy_hash") != bam_nguong:
        sai.append("băm chính sách ngưỡng trong manifest lệch")
    if nguong.get("policy_version") != "1.1.0":
        sai.append(f"policy_version {nguong.get('policy_version')} ≠ 1.1.0")

    # ⑤ LIMITED ghi đúng, KHÔNG bị gọi là PINNED
    if d.get("model_reproducibility") != "LIMITED_ACCEPTED":
        sai.append(f"model_reproducibility {d.get('model_reproducibility')} "
                   f"≠ LIMITED_ACCEPTED")
    if d.get("model_version_or_snapshot") is not None:
        sai.append("alias được ghi như thể có snapshot")

    # ⑥ + ⑦ ba tham số giải mã đúng trạng thái
    ts = d.get("decoding_parameters") or {}
    if ts.get("temperature") != {"mode": "explicit", "value": 0.2}:
        sai.append(f"temperature không ở trạng thái explicit: {ts.get('temperature')}")
    for t in ("top_p", "max_output_tokens"):
        if ts.get(t) != {"mode": "not_sent", "value": None}:
            sai.append(f"`{t}` phải là NOT_SENT, đang là {ts.get(t)}")

    # ⑧ trần ghi TRƯỚC lượt gọi đầu
    tran = d.get("application_call_budget")
    if tran != R.tran_luot_goi_v3(len(ca)):
        sai.append(f"trần {tran} ≠ trần dẫn xuất {R.tran_luot_goi_v3(len(ca))}")

    # ⑨ mọi lượt gọi giả đều đi qua cổng, và đều được đếm
    con = tran
    for i in range(3):
        R.canh_gac_truoc_luot_goi(thu_muc, con_lai=con)
        provider_gia(f"luot-{i}")
        con -= 1
    if len(goi) != 3:
        sai.append(f"đếm lượt gọi sai: {len(goi)} ≠ 3")

    # ⑩ trôi TRƯỚC lượt thứ hai ⇒ guard ĐỎ
    cu = duong.read_bytes()
    hong = dict(d, scorer_hash="0" * 64)
    duong.write_text(_json.dumps(hong, ensure_ascii=False), encoding="utf-8")
    try:
        R.canh_gac_truoc_luot_goi(thu_muc, con_lai=con)
        sai.append("TRÔI scorer giữa hai lượt gọi mà guard KHÔNG đỏ")
    except IE:
        pass
    if not (thu_muc / "integrity_stop.json").exists():
        sai.append("trôi mà không để lại artifact chẩn đoán")
    duong.write_bytes(cu)              # khôi phục bản chuẩn

    # ⑪ tóm tắt dẫn từ ĐĨA — manifest đọc lại phải khớp bản vừa khôi phục
    if _json.loads(duong.read_text(encoding="utf-8")) != d:
        sai.append("manifest trên đĩa không khôi phục được về bản đã ghi")

    # ⑫ thư mục cũ bị từ chối
    try:
        R.mo_luot_do_v3(thu_muc, run_id=thu_muc.name, ca=ca,
                        bo_qua_dirty=True, gia_lap=True)
        sai.append("chạy lại vào thư mục CŨ mà không bị chặn")
    except IE:
        pass

    # §J14 — corpus phát triển đi vào chỗ pool V3
    try:
        R.kiem_bo_ca_la_pool_v3(R.CA)
        sai.append("corpus V1/V2 lọt vào chỗ pool V3 mà không bị chặn")
    except IE:
        pass

    # §J13 — artifact không được mang khoá
    if R.quet_bi_mat(duong.read_text(encoding="utf-8")):
        sai.append("manifest chứa thứ trông như credential")

    _ngan_xep.close()
    print(f"  runner V3         mo_run ✓ · {len(goi)} lượt giả · trần {tran}")
    return not sai, sai


#: 13 ô của pool V3, và họ hình của từng ô. Chỉ HÌNH DẠNG — nội dung ca thật
#: không đọc ở đây, và không cần đọc: cái đang chứng nhận là **đường dây**.
_O_GIA = {"C1": "ball", "C2": "ball", "C3": "ball",
          "C4": "cylinder", "C5": "cylinder", "C6": "cylinder",
          "C7": "cone", "C8": "cone", "C9": "cone",
          "N1": "ball", "N2": "cylinder", "N3": "cone", "N4": "ball"}


def _pool_gia(thu_muc: Path) -> tuple[Path, Path, list[str], str]:
    """Pool/seal TỔNG HỢP ở trạng thái ĐÃ RÚT — 26 bài / 13 ô / mỗi ô 2."""
    import json as _json

    import freeze_evaluation_candidate as F
    import seal_curved_v3 as SC

    bai = [{"id": f"{o}_{k}", "o": o, "hinh": h,
            "loai": "duong" if o.startswith("C") else "am",
            "de": f"đề tổng hợp {o}_{k}",
            "mong": ["2", "3"] if o.startswith("C") else [],
            "cong_thuc": {}}
           for o, h in _O_GIA.items() for k in (1, 2)]
    chon = [f"{o}_1" for o in _O_GIA]
    da_chon = [b for b in bai if b["id"] in set(chon)]
    he, n = F.measured_system_hash()

    thu_muc.mkdir(parents=True, exist_ok=True)
    pool, dau = thu_muc / "POOL.json", thu_muc / "V3_SEAL.json"
    pool.write_text(_json.dumps({"khai": "giả", "bai": bai},
                                ensure_ascii=False), encoding="utf-8")
    dau.write_text(_json.dumps({
        "pool_hash": SC._bam(bai), "pool_size": len(bai),
        "o": list(_O_GIA), "o_duong": [o for o in _O_GIA if o[0] == "C"],
        "o_am": [o for o in _O_GIA if o[0] == "N"],
        "measured_system_hash": he, "measured_system_files": n,
        "seed": 987654321, "da_rut": chon,
        "case_set_hash": SC._bam(da_chon),
    }, ensure_ascii=False), encoding="utf-8")
    return pool, dau, chon, SC._bam(da_chon)


def chung_nhan_duong_hau_model(thu_muc: Path) -> tuple[bool, list[str]]:
    """§G — runner chấm bằng ĐÚNG ba thẩm quyền của sản phẩm.

    Chứng minh trọn đường, không chỉ một mảnh:

        verify_and_compile
        → trích đáp số từ `final_memory`   (KHÔNG từ scene3d)
        → ghép Scene3D bằng chính hàm pipeline dùng
        → đọc postconditions / servable RIÊNG
        → phán quyết bằng scorer canonical
        → artifact ba nhóm

    Provider giả phải đi tới một chương trình **executable**, nếu không bài
    này không chạm tầng hậu-model và chỉ chứng nhận chính nó — đúng lỗi mà
    `V3_PRODUCT_PATH_PARITY_CORRECTION` đã trả giá.
    """
    import json as _json

    import run_curved_acceptance as R
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import RequestContract
    from app.simulation.semantic_program.route import verify_and_compile

    sai: list[str] = []
    thu_muc = Path(thu_muc)
    thu_muc.mkdir(parents=True, exist_ok=True)

    # Ca ĐÚNG TRỌN của bài chứng nhận: nó servable, nên nó chạm mọi tầng.
    ca = {c["id"]: c for c in CA}["duong_1_dung"]
    contract = RequestContract(
        problem_text=ca["de"], input_facts=ca["facts"],
        obligations=tuple(Obligation(**o) for o in ca["obligations"]))
    spec = SemanticProgramSpec.model_validate(ca["spec"])
    out = verify_and_compile(contract, spec)
    if not out.executable:
        return False, ["provider giả KHÔNG tới được chương trình executable — "
                       "bài chứng nhận không chạm tầng hậu-model"]

    kq = R.cham_ca_theo_duong_san_pham(
        {"id": ca["id"], "loai": "duong", "hinh": "ball",
         "mong": set(ca["mong_dai_luong"].values())},
        contract, spec, out, schema_ok=True)

    # ① ba nhóm, đủ trường, JSON-hoá được
    for nhom, truong in (
            ("execution", ("runtime_executable", "postconditions_pass",
                           "servable")),
            ("results", ("final_memory", "exact_answer_match", "scene3d_pass",
                         "exact_result_authority")),
            ("classification", ("canonical", "legacy"))):
        if nhom not in kq:
            sai.append(f"artifact thiếu nhóm `{nhom}`")
            continue
        for t in truong:
            if t not in kq[nhom]:
                sai.append(f"`{nhom}` thiếu `{t}`")
    try:
        _json.dumps(kq, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        sai.append(f"kết quả chấm không JSON-hoá được: {e}")

    # ② ĐÁP SỐ đọc từ `final_memory`, KHÔNG từ scene3d
    if kq.get("results", {}).get("exact_result_authority") !=             "outcome.final_memory":
        sai.append(
            f"thẩm quyền đáp số sai: "
            f"{kq.get('results', {}).get('exact_result_authority')!r} — phải "
            f"là `outcome.final_memory`")
    if not kq["results"]["exact_answer_match"]:
        sai.append("ca ĐÚNG TRỌN mà `exact_answer_match` False — runner vẫn "
                   "đang đọc một phép chiếu rỗng")

    # ③ Scene3D dựng được, và bằng đúng hàm của pipeline
    if not kq["results"]["scene3d_pass"]:
        sai.append("`scene3d_pass` False cho ca servable — runner không gọi "
                   "`pipeline._dung_scene3d`")

    # ④ bốn cột TÁCH RỜI — ca này qua hết, nên bốn cột cùng True
    ex = kq["execution"]
    if not (ex["runtime_executable"] and ex["postconditions_pass"]
            and ex["servable"]):
        sai.append(f"ca servable mà cột thực thi không xanh: {ex}")

    # ⑤ verdict lấy từ scorer canonical
    if kq["classification"]["canonical"] != "CORRECT_SERVABLE_RESULT":
        sai.append(f"verdict canonical sai: "
                   f"{kq['classification']['canonical']}")

    # ⑥ ca VERIFICATION GAP — bốn cột phải tách được thật
    ca4 = {c["id"]: c for c in CA}["duong_4_he_hut_verification"]
    c4 = RequestContract(
        problem_text=ca4["de"], input_facts=ca4["facts"],
        obligations=tuple(Obligation(**o) for o in ca4["obligations"]))
    s4 = SemanticProgramSpec.model_validate(ca4["spec"])
    o4 = verify_and_compile(c4, s4)
    k4 = R.cham_ca_theo_duong_san_pham(
        {"id": ca4["id"], "loai": "duong", "hinh": "ball", "mong": set()},
        c4, s4, o4, schema_ok=True)
    if not k4["execution"]["runtime_executable"]:
        sai.append("ca verification-gap phải executable")
    if k4["execution"]["servable"]:
        sai.append("ca verification-gap KHÔNG được servable")
    if k4["classification"]["canonical"] != "SYSTEM_VERIFICATION_FAILURE":
        sai.append(f"verification gap phân lớp sai: "
                   f"{k4['classification']['canonical']}")

    ghi_artifact(thu_muc / "post_model_path.json", {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "servable_case": kq, "verification_gap_case": k4})
    print(f"  hậu-model         final_memory ✓ · scene3d ✓ · 4 cột tách ✓ · "
          f"scorer canonical ✓")
    return not sai, sai


def chung_nhan_live_entrypoint(thu_muc: Path) -> tuple[bool, list[str]]:
    """§F — chạy **CHÍNH `main_async`**, không phải một bản mô phỏng của nó.

    Vì sao cần bài riêng: `chung_nhan_runner_v3` gọi THẲNG `mo_luot_do_v3`
    bằng hai ca tổng hợp của chính nó. Nó chứng minh **hàm** đúng — và nó xanh
    suốt quãng `main_async` chạy corpus phát triển, không ghi manifest, không
    qua cổng canh. Một bài chứng nhận không đi qua đường chạy thật thì nó
    chứng nhận chính nó.

    0 lượt gọi model: provider bị thay bằng stub ghi nhật ký.
    """
    import asyncio
    import contextlib
    import io
    import json as _json
    import os
    import tempfile

    import acceptance_integrity as AI
    import run_curved_acceptance as R
    import seal_curved_v3 as SC
    from app.ai import gemini, pipeline

    sai: list[str] = []
    thu_muc = Path(thu_muc)
    with tempfile.TemporaryDirectory() as tam:
        _cm = _con_dau_tong_hop(Path(tam) / "v3-gia")
        pool, dau, chon, bam_ca = _cm.__enter__()
        su_kien: list[str] = []
        goi: list[str] = []

        async def provider_gia(*a, **kw):
            su_kien.append("provider_call")
            goi.append("x")
            return "khong-phai-json"

        goc = {"pool": SC.POOL, "dau": SC.DAU, "call": pipeline.call_gemini,
               "dirty": AI.phan_loai_dirty, "canh": R.canh_gac_truoc_luot_goi,
               "budget": None}
        moi_truong_cu = {k: os.environ.get(k)
                         for k in ("ALLOW_LIVE_AI", "GEMINI_API_KEY")}

        def canh_ghi(td, **kw):
            su_kien.append("identity_guard")
            return goc["canh"](td, **kw)

        try:
            SC.POOL, SC.DAU = pool, dau
            pipeline.call_gemini = provider_gia
            AI.phan_loai_dirty = lambda: {
                "sach": True, "duong_ban": [], "ban_trong_yeu": [],
                "ban_khong_lien_quan": []}
            R.canh_gac_truoc_luot_goi = canh_ghi
            os.environ["ALLOW_LIVE_AI"] = "1"
            os.environ["GEMINI_API_KEY"] = "khoa-gia-chung-nhan"

            # Nuốt stdout của lượt diễn tập: bài chứng nhận phải đọc được:
            # 13 ca × mấy chục dòng nhật ký sẽ đẩy chính verdict ra khỏi màn.
            # Nuốt hiển thị, KHÔNG nuốt lỗi — ngoại lệ vẫn bay lên `except`.
            with contextlib.redirect_stdout(io.StringIO()):
                ma = asyncio.run(R.main_async(argparse.Namespace(
                    out_dir=str(thu_muc), chi_8a=False, ca=None)))
            # Đọc kiểu `mong` NGAY ĐÂY, khi pool tổng hợp còn hiệu lực. Hỏi
            # sau `finally` là hỏi con dấu THẬT — thứ chưa rút, nên nó ném, và
            # bài chứng nhận sẽ báo một lỗi không phải lỗi nó đang tìm.
            _cv3, _tho, _b = R.nap_ca_v3()
            kieu = ({type(c["mong"]).__name__ for c in _cv3},
                    {type(c["mong"]).__name__ for c in _tho})
        except Exception as e:                       # noqa: BLE001
            sai.append(f"`main_async` NÉM {type(e).__name__}: {e}")
            ma = -1
        finally:
            _cm.__exit__(None, None, None)
            pipeline.call_gemini = goc["call"]
            AI.phan_loai_dirty = goc["dirty"]
            R.canh_gac_truoc_luot_goi = goc["canh"]
            gemini.set_budget(None)
            for k, v in moi_truong_cu.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

        if sai:
            return False, sai
        if ma != 0:
            sai.append(f"`main_async` thoát {ma}, không phải 0")

        # ① manifest có mặt, và có TRƯỚC lượt gọi provider đầu tiên
        mf_duong = thu_muc / "manifest.json"
        if not mf_duong.exists():
            sai.append("KHÔNG có manifest — `main_async` không gọi `mo_run`")
            return False, sai
        if "provider_call" not in su_kien:
            sai.append("không lượt gọi provider nào — bài kiểm không đo được gì")
            return False, sai
        if su_kien.index("identity_guard") > su_kien.index("provider_call"):
            sai.append("lượt gọi provider đi TRƯỚC cổng canh danh tính")

        # ② mỗi lượt gọi provider có đúng một guard đi trước
        du = 0
        for sk in su_kien:
            if sk == "identity_guard":
                du += 1
            elif sk == "provider_call":
                if du <= 0:
                    sai.append("có lượt gọi provider KHÔNG có guard đi trước")
                    break
                du -= 1

        mf = _json.loads(mf_duong.read_text(encoding="utf-8"))
        a8 = _json.loads((thu_muc / "stage_8a_one_shot.json")
                         .read_text(encoding="utf-8"))
        cuoi = _json.loads((thu_muc / "curved_acceptance.json")
                           .read_text(encoding="utf-8"))

        # ③ bộ ca đến từ con dấu, không từ corpus phát triển
        ids = [c["id"] for c in a8["ca"]]
        if set(ids) != set(chon):
            sai.append(f"bộ ca chạy {sorted(ids)} ≠ bộ đã rút {sorted(chon)}")
        if set(ids) & {c["id"] for c in R.CA}:
            sai.append("corpus phát triển lọt vào đường chạy live")
        if len(ids) != 13:
            sai.append(f"chạy {len(ids)} ca, pool V3 rút 13")

        # ④ băm bộ ca V3 ở mọi artifact, và KHÔNG có băm corpus phát triển
        for ten, co in (("stage_8a.case_set_hash", a8.get("case_set_hash")),
                        ("moi_truong.case_set_hash",
                         a8.get("moi_truong", {}).get("case_set_hash")),
                        ("tom_tat.CASE_SET_HASH",
                         cuoi.get("tom_tat", {}).get("CASE_SET_HASH")),
                        ("manifest.seal.case_set_hash",
                         mf.get("seal", {}).get("case_set_hash"))):
            if co != bam_ca:
                sai.append(f"`{ten}` = {str(co)[:16]}… ≠ băm bộ ca V3")
        if R.CA_HASH in _json.dumps({"a": a8, "c": cuoi, "m": mf},
                                    ensure_ascii=False):
            sai.append("băm corpus phát triển lọt vào artifact")

        # ⑤ trần 78, ghi trong manifest
        if mf.get("application_call_budget") != 78:
            sai.append(f"trần {mf.get('application_call_budget')} ≠ 78")

        # ⑥ `mong` tương thích: loader trả set, bộ thô giữ list
        if kieu[0] != {"set"}:
            sai.append(f"`mong` chưa chuẩn hoá thành set ở loader: {kieu[0]}")
        if kieu[1] != {"list"}:
            sai.append(f"bộ THÔ phải giữ `mong` dạng list: {kieu[1]}")

        # ⑦ 0 lượt gọi thật — mọi lượt đều đi qua stub
        if len(goi) != len(ids):
            sai.append(f"{len(goi)} lượt gọi ≠ {len(ids)} ca × 1 analyze")

    print(f"  live entrypoint   main_async ✓ · {len(goi)} lượt giả · "
          f"{len(ids)} ca từ con dấu · trần {mf.get('application_call_budget')}")
    return not sai, sai


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", default=None,
                   help="mặc định: một thư mục tạm, xoá sau khi chạy")
    a = p.parse_args()

    print("CHỨNG NHẬN BỘ ĐO — 0 lượt gọi model\n")
    with tempfile.TemporaryDirectory() as tam:
        goc = Path(a.out_dir) if a.out_dir else Path(tam)
        ok, sai, chua = chung_nhan(goc / "cert-run")
        ok3, sai3 = chung_nhan_runner_v3(goc / "cert-v3")
        ok4, sai4 = chung_nhan_live_entrypoint(goc / "cert-live")
        ok5, sai5 = chung_nhan_duong_hau_model(goc / "cert-post")
        ok, sai = ok and ok3 and ok4 and ok5, sai + sai3 + sai4 + sai5
    print()
    for s in sai:
        print(f"  ✗ {s}")
    print(f"\n  RUNNER_CERTIFICATION   {'PASS' if ok else 'FAIL'}")
    # Hai nhãn, cố ý tách. `V3_RUNNER_INTEGRATION` nói về **hàm**
    # `mo_luot_do_v3`; nó từng được đọc như thể nói về đường chạy thật, và
    # chính chỗ hiểu rộng đó để lọt wave trước. Nhãn dưới mới là nhãn mạnh.
    print(f"  V3_RUNNER_INTEGRATION  {'PASS' if ok3 else 'FAIL'}"
          f"   (phạm vi: hàm `mo_luot_do_v3`)")
    print(f"  V3_LIVE_ENTRYPOINT_INTEGRATION  {'PASS' if ok4 else 'FAIL'}"
          f"   (phạm vi: `main_async` — đường chạy THẬT)")
    print(f"  ACCEPTANCE_POST_MODEL_PATH_INTEGRATION  "
          f"{'PASS' if ok5 else 'FAIL'}   (phạm vi: đáp số · cảnh · phán quyết)")
    print(f"  APPLICATION_LLM_CALLS  0")

    # Readiness KHÔNG đổi mã thoát: bộ đo đúng là một chuyện, lượt live được
    # phép chạy là chuyện khác. Hai danh sách tách riêng — CHẶN là việc chưa
    # làm, GIỚI HẠN ĐÃ KHAI là thứ sẽ đi vào báo cáo và ở lại đó.
    chan, gioi_han = chua
    # `YES` chỉ được phát khi verdict MẠNH xanh. Trước wave này readiness chỉ
    # hỏi cấu hình model, nên nó nói YES suốt quãng entrypoint chạy corpus
    # phát triển — một lời mời đi thẳng vào chỗ tiêu pool held-out.
    if not ok4:
        chan = list(chan) + [
            "V3_LIVE_ENTRYPOINT_INTEGRATION FAIL — `main_async` chưa chứng "
            "minh được là dùng pool đã niêm phong"]
    print(f"\n  READY_FOR_INDEPENDENT_V3_LIVE  "
          f"{'YES' if not chan else 'CONDITIONAL'}")
    # Nhãn cho lượt đo TƯƠNG LAI: đòi CẢ HAI tầng đã chứng minh. Một lượt đo
    # đi đúng pool mà chấm sai tầng vẫn cho ra con số sai — V3 đã trả giá.
    print(f"  READY_FOR_FUTURE_CURVED_ACCEPTANCE  "
          f"{'YES' if (ok4 and ok5) else 'NO'}")
    for c in chan:
        print(f"    ✗ {c}")
    for c in gioi_han:
        print(f"    · giới hạn đã khai: {c}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
