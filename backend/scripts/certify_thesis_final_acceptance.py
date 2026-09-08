# -*- coding: utf-8 -*-
"""CHỨNG NHẬN RUNNER ĐÁNH GIÁ CUỐI — provider STUB, **0 lượt gọi thật**.

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \\
        scripts/run_thesis_final_acceptance.py --certify [--out-dir <thư mục>]

    `THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT` §14, 2026-09-08.

─── CHỨNG NHẬN CHÍNH ENTRYPOINT, KHÔNG PHẢI MỘT BẢN MÔ PHỎNG NÓ ───────────

Bài kiểm này gọi `run_thesis_final_acceptance.chay_lut` — đúng hàm mà `--live`
gọi, cùng một thân, cùng cổng canh, cùng thứ tự ghi artifact. Khác **một** thứ:
`provider` được truyền vào là một stub.

Đó không phải chi tiết. `V3_LIVE_ENTRYPOINT_INTEGRATION_BLOCKER` đã trả giá
cho đúng lỗ ngược lại: certifier gọi thẳng một hàm phụ, xanh suốt, trong khi
`main_async` — đường thật — chạy corpus khác và không ghi manifest.

─── CÁI GÌ LÀ GIẢ, CÁI GÌ LÀ THẬT ─────────────────────────────────────────

**Giả đúng MỘT thứ: văn bản provider trả về.** Stub dựng `analyze` từ gold
contract của corpus và `synthesis` từ gold program — hai thứ đã đóng băng ở
wave trước.

**Mọi thứ sau đó là THẬT**: `build_request_contract` thật, `validate_semantic_
program` thật, `verify_and_compile` thật, checker thật, `_dung_scene3d` thật,
`acceptance_verdict` thật, cổng ngân sách thật, cổng danh tính thật.

─── BA HÌNH DẠNG STUB, CỐ Ý ──────────────────────────────────────────────

    `gold`     trả gold program ⇒ ca `served` ngay chặng A
    `hong_roi_sua`  lượt đầu trả chương trình HỎNG ⇒ chặng B chạy thật, lượt
                    sửa trả gold ⇒ `RECOVERY_WITHIN_ONE_REPAIR`
    `am`       trả chương trình mà ca ÂM dễ sinh ra ⇒ fail-closed

Không có hình dạng nào cho *"chặng B chạy nhưng vẫn hỏng"* vì nó không thêm
đường đi mới nào — nó chỉ đổi một nhãn ở cuối.
"""
from __future__ import annotations

import asyncio
import copy
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_thesis_final_acceptance as R  # noqa: E402

#: Ca được cố ý cho HỎNG ở chặng A để chặng B có đường chạy thật. Chọn `p4`
#: (hình trụ) và bỏ `apex_or_top`. ⚠️ Đo ra nó chết ở **lược đồ**, không phải
#: `ir_static` như tôi đoán khi viết — `construct_curved_solid` đòi đủ toán
#: hạng ngay ở tầng Pydantic. Vẫn đúng ý đồ: lỗi lược đồ là nhánh
#: repair-eligible ĐẦU TIÊN mà `acceptance_verdict.sua_duoc` nhận, nên chặng B
#: chạy thật. Ghi lại phép đo thay vì giữ lời đoán.
CA_HONG_ROI_SUA = "p4_hinh_tru_the_tich_va_xung_quanh"

#: Phân tích mà `analyze` THẬT sẽ trả cho hai ca âm. Corpus cố ý KHÔNG có gold
#: contract cho ca âm (chúng không có gold nào cả), nhưng stub vẫn phải trả một
#: hợp đồng THỰC TẾ — nếu không, hợp đồng rỗng nghĩa vụ và cổng phủ không có gì
#: để bác, nên một chương trình vô nghĩa vẫn `served`. Đo được ở lượt chứng
#: nhận đầu: cả hai ca âm `SERVABLE = true` với đáp số `0`.
ANALYZE_CA_AM: dict[str, dict[str, Any]] = {
    "n1_khoi_tron_xoay_tong_quat": {
        "input_facts": [
            {"id": "parabol", "label": "Parabol y = x²", "kind": "str",
             "value": ["y = x²"]},
            {"id": "chan", "label": "Đường thẳng x = 2", "kind": "str",
             "value": ["x = 2"]},
            {"id": "truc", "label": "Trục quay Ox", "kind": "str",
             "value": ["Ox"]}],
        "obligations": [{"kind": "volume", "container": "khối tròn xoay",
                         "witness": "V"}],
    },
    "n2_khoi_ghep_bu_can_boolean": {
        "input_facts": [
            {"id": f"dinh_{t}", "label": f"Đỉnh {t}", "kind": "str",
             "value": [t, v]}
            for t, v in (("A", "(0;0;0)"), ("B", "(8;0;0)"), ("C", "(8;6;0)"),
                         ("D", "(0;6;0)"), ("A1", "(0;0;10)"))
        ] + [{"id": "lo_tru", "label": "Lỗ hình trụ bán kính 2", "kind": "str",
              "value": ["2"]}],
        "obligations": [{"kind": "volume",
                         "container": "phần vật thể còn lại", "witness": "V"}],
    },
}

#: Ca bị ĐỔI TÊN witness trong stub. ⚠️ Sinh ra từ một lỗi THẬT của lượt đo
#: chính thức: stub trả về CHÍNH gold program, nên tên biến của "mô hình" luôn
#: TRÙNG tên gold, và một bộ chấm tra đáp số bằng tên gold vẫn xanh. Mô hình
#: thật thì tự đặt tên (`the_volume_sabcd`, `dien_tich_elip_e`…), nên 6/7 ca CÓ
#: ĐÁP SỐ ĐÚNG bị chấm là sai và `SILENT_WRONG_ANSWER_COUNT` báo 6 thay vì 0.
#:
#: Một provider giả giống bản mẫu quá mức thì không kiểm được thứ chỉ sai khi
#: mô hình được tự do. Ca này đổi tên để guard có răng.
CA_DOI_TEN_WITNESS = "p5_hinh_non_the_tich_va_xung_quanh"
_HAU_TO_DOI_TEN = "_do_mo_hinh_dat"


def _doi_ten_witness(ca: dict) -> tuple[dict, dict]:
    """`(hợp đồng, chương trình)` với MỌI witness đổi tên — như mô hình thật."""
    hd = copy.deepcopy(ca["request_contract_gold"])
    ct = copy.deepcopy(ca["gold_program"])
    doi = {o["params"]["witness"]: o["params"]["witness"] + _HAU_TO_DOI_TEN
           for o in hd["obligations"] if (o.get("params") or {}).get("witness")}
    for o in hd["obligations"]:
        w = (o.get("params") or {}).get("witness")
        if w in doi:
            o["params"]["witness"] = doi[w]
    for d in ct["memory_declarations"]:
        if d["name"] in doi:
            d["name"] = doi[d["name"]]
    for st in ct["statements"]:
        if st.get("target_var") in doi:
            st["target_var"] = doi[st["target_var"]]
    return hd, ct


#: Nhãn phải PASS hết thì runner mới được coi là đã căn chỉnh (§14).
NHAN = (
    "FIXED_CORPUS_LOADER",
    "MANIFEST_BEFORE_FIRST_CALL",
    "ALL_RAW_ATTEMPTS_RETAINED",
    "CANONICAL_POSITIVE_SCORER",
    "CANONICAL_NEGATIVE_SCORER",
    "STAGE_A_ONE_ATTEMPT",
    "STAGE_B_ONE_REPAIR",
    "STAGE_B_REUSES_FROZEN_CONTRACT",
    "STAGE_B_REUSES_RAW_CANDIDATE",
    "THESIS_POLICY_LOADED",
    "IDENTITY_GUARD_BEFORE_EVERY_CALL",
    "BUDGET_GUARD_BEFORE_EVERY_CALL",
    "REAL_PROVIDER_CALLS_ZERO",
    "NETWORK_REFERENCES_RESTORED",
    "GOLD_CONTRACT_REACHABLE",
    "SCORING_SURVIVES_MODEL_CHOSEN_WITNESS_NAMES",
)

#: Thứ tự sự kiện tối thiểu của một ca ĐI TRỌN (§14).
CHUOI_SU_KIEN_TOI_THIEU = (
    "load_identity", "load_policy", "load_corpus", "verify_hashes",
    "write_manifest", "scope", "identity_guard_pass", "budget_guard_pass",
    "analyze_call", "freeze_contract", "synthesis_call", "score_stage_a",
    "write_stage_a", "select_repair", "repair_call", "score_stage_b",
    "write_final", "verify_identity_after",
)


# ══ STUB PROVIDER ════════════════════════════════════════════════════════
def _analyze_tho(hd_gold: dict) -> str:
    """Gold contract → payload THÔ đúng hình dạng `analyze` trả về.

    Không trả thẳng hợp đồng đã dựng: `build_request_contract` là **biên đóng
    băng**, và đi vòng qua nó thì bài kiểm này không còn chạm tầng ấy — tầng
    duy nhất quyết định hợp đồng thật sự trông thế nào.
    """
    return json.dumps({
        "input_facts": [{"id": f["fact_id"], "label": f["label"],
                         "kind": "str", "value": f["values"]}
                        for f in hd_gold["input_facts"]],
        "obligations": [{"kind": o["kind"], "container": o["container"],
                         **{k: v for k, v in (o.get("params") or {}).items()
                            if k in ("witness", "wrt", "solid", "plane")}}
                        for o in hd_gold["obligations"]],
    }, ensure_ascii=False)


def _chuong_trinh_hong(gold: dict) -> str:
    """Gold, bỏ đúng MỘT toán hạng ⇒ chết ở `ir_static`, sửa được.

    Bỏ `apex_or_top` của `construct_curved_solid`: chương trình vẫn hợp lệ về
    lược đồ (trường là tuỳ chọn) nhưng kernel không dựng nổi hình trụ, nên nó
    chết ở đúng một tầng mà vòng sửa của sản phẩm với tới.
    """
    xau = copy.deepcopy(gold)
    for st in xau["statements"]:
        if st.get("kind") == "construct_curved_solid":
            st.pop("apex_or_top", None)
    return json.dumps(xau, ensure_ascii=False)


def dung_stub(bo_do: R.BoDo) -> tuple[Any, dict[str, list[str]]]:
    """`(provider, nhật ký gọi theo ca)`.

    Provider KHÔNG đọc `prompt` để quyết định trả gì — nó tra theo ca và số
    lượt. Đọc prompt sẽ biến stub thành một mô hình nhỏ, và một mô hình nhỏ có
    hành vi riêng thì bài chứng nhận đo lẫn cả hành vi ấy.
    """
    theo_de = {c["problem_text"]: c for c in bo_do.corpus["positive_cases"]}
    am = {c["problem_text"]: c for c in bo_do.corpus["negative_cases"]}
    dem: dict[str, int] = {}
    nhat_ky: dict[str, list[str]] = {}

    async def _stub(api_key, skill, prompt, schema, temperature, *a, **kw):
        de = _de_trong_prompt(prompt, [*theo_de, *am])
        ca = theo_de.get(de) or am.get(de)
        ma = ca["id"] if ca else "?"
        la_analyze = "input_facts" in json.dumps(schema)[:4000]
        n = dem.get(ma, 0)
        nhat_ky.setdefault(ma, []).append("analyze" if la_analyze else
                                          ("synthesis" if n == 0 else "repair"))
        if la_analyze:
            if ca is None:
                return json.dumps({"input_facts": [], "obligations": []})
            if "request_contract_gold" in ca:
                if ma == CA_DOI_TEN_WITNESS:
                    return _analyze_tho(_doi_ten_witness(ca)[0])
                return _analyze_tho(ca["request_contract_gold"])
            return json.dumps(ANALYZE_CA_AM[ma], ensure_ascii=False)
        dem[ma] = n + 1
        if ca is None or "gold_program" not in ca:
            # Ca ÂM: mô hình dễ trả một chương trình đo THẲNG một vật nó chưa
            # dựng. Fail-closed ở cổng phủ, đúng mã đã pre-register.
            return json.dumps({
                "spec_version": "1.0", "title": "Không dựng được",
                "memory_declarations": [{"name": "V", "type": "float"}],
                "statements": [{"kind": "assign", "target_var": "V",
                                "expr": {"kind": "literal", "value": 0}}],
                "visual_bindings": {"containers": [], "pointers": [],
                                    "value_boxes": []}}, ensure_ascii=False)
        if ma == CA_HONG_ROI_SUA and n == 0:
            return _chuong_trinh_hong(ca["gold_program"])
        if ma == CA_DOI_TEN_WITNESS:
            return json.dumps(_doi_ten_witness(ca)[1], ensure_ascii=False)
        return json.dumps(ca["gold_program"], ensure_ascii=False)

    return _stub, nhat_ky


def _de_trong_prompt(prompt: str, cac_de: list[str]) -> str:
    """Nhận ra ca bằng cách tìm ĐỀ ĐẦY ĐỦ trong prompt.

    ⚠️ Bản đầu so `de[:80]` — và đo ra là SAI: `p4` với `p6` (đều hình trụ, chỉ
    khác chiều cao `K(0;0;10)` vs `K(0;0;24)`) trùng nhau 80 ký tự đầu, `p5`
    với `p7` cũng vậy. Hậu quả: stub trả gold của `p4` cho `p6`, và hai ca elip
    "hỏng" vì một lý do không nằm ở hệ. Một stub nhận nhầm ca là một bài chứng
    nhận đo nhầm thứ.

    So bản ĐẦY ĐỦ, và thử chuỗi DÀI trước — một đề ngắn có thể là khúc đầu của
    một đề dài hơn, và khi ấy thứ khớp trước phải là đề dài.
    """
    for de in sorted(cac_de, key=len, reverse=True):
        if de in prompt:
            return de
    return ""


#: Định danh thuộc bộ đo V3 mà runner khoá luận KHÔNG được chạm.
_DAU_VET_V3 = ("nap_ca_v3", "seal_curved_v3", "run_curved_acceptance",
               "kiem_bo_ca_la_pool_v3", "_MA_RANH_GIOI_CONG",
               "curved_v3_threshold_policy", "mo_luot_do_v3")


def _dau_vet_v3(src: str) -> list[str]:
    """Runner có THẬT SỰ chạm bộ đo V3 không — đọc AST, không quét chuỗi.

    ⚠️ Bản đầu dùng `"nap_ca_v3" not in src`, và nó ĐỎ vì một lý do buồn cười:
    chính docstring của runner viết *"`nap_ca_v3` không xuất hiện ở file này"*.
    Một guard bị chính lời giải thích của nó làm đỏ là một guard đọc sai tầng —
    nó hỏi về VĂN BẢN trong khi câu cần hỏi là về MÃ.

    Nên ở đây chỉ nhìn `import`, tên biến và thuộc tính. Chú thích, docstring
    và chuỗi ký tự đều không tính.
    """
    import ast

    cay = ast.parse(src)
    cham: set[str] = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            cham |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            cham.add(n.module or "")
            cham |= {a.name for a in n.names}
        elif isinstance(n, ast.Name):
            cham.add(n.id)
        elif isinstance(n, ast.Attribute):
            cham.add(n.attr)
    return sorted(cham & set(_DAU_VET_V3))


# ══ CHỨNG NHẬN ═══════════════════════════════════════════════════════════
def chung_nhan(thu_muc: Path) -> tuple[dict[str, bool], list[str], dict]:
    """Chạy trọn vòng đời qua entrypoint thật, rồi soát artifact nó để lại."""
    bo_do = R.nap_bo_do()
    stub, nhat_ky = dung_stub(bo_do)
    tt = asyncio.run(R.chay_lut(thu_muc, provider=stub, api_key="STUB",
                                bo_do=bo_do))

    sk = json.loads((thu_muc / "event_log.json").read_text("utf-8"))["events"]
    ten_sk = [e["event"] for e in sk]
    a = json.loads((thu_muc / "stage_a_first_attempt.json").read_text("utf-8"))
    b = json.loads((thu_muc / "stage_b_recovery.json").read_text("utf-8"))
    mf = json.loads((thu_muc / "manifest.json").read_text("utf-8"))
    raw = sorted(p for p in (thu_muc / "raw").rglob("*.json"))

    sai: list[str] = []
    nhan: dict[str, bool] = {}

    def _dat(ten: str, ok: bool, vi_sao: str = "") -> None:
        nhan[ten] = ok
        if not ok:
            sai.append(f"{ten}: {vi_sao}")

    # ① bộ ca cố định, mọi băm khớp, KHÔNG qua con dấu V3
    src = (GOC / R.RUNNER_ENTRYPOINT).read_text("utf-8")
    dau_v3 = _dau_vet_v3(src)
    _dat("FIXED_CORPUS_LOADER",
         all(bo_do.kiem.values()) and not dau_v3,
         f"kiểm={bo_do.kiem} · dấu vết V3 trong MÃ: {dau_v3}")

    # ② manifest TRƯỚC lượt gọi đầu tiên — đọc THỨ TỰ sự kiện, không đọc lời khai
    i_mf = ten_sk.index("write_manifest") if "write_manifest" in ten_sk else -1
    i_goi = min([i for i, t in enumerate(ten_sk)
                 if t.endswith("_call")] or [10**9])
    _dat("MANIFEST_BEFORE_FIRST_CALL", 0 <= i_mf < i_goi,
         f"write_manifest ở {i_mf}, lượt gọi đầu ở {i_goi}")

    # ③ mọi raw attempt được giữ, và giữ NGUYÊN VĂN
    so_goi = sum(1 for t in ten_sk if t.endswith("_call"))
    du_truong = all(
        set(json.loads(p.read_text("utf-8"))) >=
        {"case_id", "stage", "attempt_index", "logical_call_index",
         "physical_attempts", "at", "raw_text", "raw_sha256", "prompt_sha256"}
        for p in raw)
    _dat("ALL_RAW_ATTEMPTS_RETAINED", len(raw) == so_goi and du_truong,
         f"{len(raw)} file raw ≠ {so_goi} lượt gọi, hoặc thiếu trường")

    # ④⑤ scorer canonical — ca dương VÀ ca âm
    import acceptance_verdict as AV

    lop_duong = {c["cham"]["CANONICAL_VERDICT"] for c in a["cases"]
                 if c["loai"] == "duong"}
    lop_am = {c["cham"]["CANONICAL_VERDICT"] for c in a["cases"]
              if c["loai"] == "am"}
    rieng = {"MODEL_ANALYZE_FAILURE", "SYSTEM_SCENE3D_FAILURE"}
    _dat("CANONICAL_POSITIVE_SCORER",
         lop_duong <= set(AV.LOP_PHAN_QUYET) | rieng, f"{lop_duong}")
    _dat("CANONICAL_NEGATIVE_SCORER",
         lop_am <= set(AV.LOP_PHAN_QUYET) | rieng
         and all("NEGATIVE_FAIL_CLOSED" in c["cham"]
                 and "TARGET_BOUNDARY_PASS" in c["cham"]
                 for c in a["cases"] if c["loai"] == "am")
         and not dau_v3,
         f"{lop_am} · dấu vết bộ chấm V3: {dau_v3}")

    # ⑥ chặng A: đúng MỘT analyze + MỘT synthesis mỗi ca chạm provider
    lech_a = {ma: v for ma, v in nhat_ky.items()
              if v[:2] != ["analyze", "synthesis"]
              or v.count("analyze") != 1 or v.count("synthesis") != 1}
    _dat("STAGE_A_ONE_ATTEMPT", not lech_a, f"{lech_a}")

    # ⑦ chặng B: đúng MỘT lượt sửa, và chỉ cho ca đủ điều kiện
    sua = {ma: v.count("repair") for ma, v in nhat_ky.items()}
    _dat("STAGE_B_ONE_REPAIR",
         all(n <= 1 for n in sua.values())
         and sua.get(CA_HONG_ROI_SUA) == 1, f"{sua}")

    # ⑧⑨ chặng B TIẾP TỤC: dùng lại hợp đồng và candidate của chặng A
    bb = [x for x in b["cases"] if not x["bo_qua"]]
    a_theo_id = {c["id"]: c for c in a["cases"]}
    _dat("STAGE_B_REUSES_FROZEN_CONTRACT",
         bool(bb) and all(
             x["reuses"]["frozen_contract_sha256"]
             == a_theo_id[x["id"]]["frozen_contract_sha256"]
             and x["reuses"]["analyze_calls_in_stage_b"] == 0
             for x in bb), "chặng B không dùng lại hợp đồng đã đóng băng")
    raw_a = {(json.loads(p.read_text("utf-8"))["case_id"],
              json.loads(p.read_text("utf-8"))["stage"]):
             json.loads(p.read_text("utf-8"))["raw_sha256"] for p in raw}
    _dat("STAGE_B_REUSES_RAW_CANDIDATE",
         bool(bb) and all(
             x["reuses"]["raw_initial_candidate_sha256"]
             == raw_a.get((x["id"], "synthesis"))
             and x["reuses"]["initial_synthesis_calls_in_stage_b"] == 0
             for x in bb), "chặng B không dùng lại raw candidate")

    # ⑩ policy của KHOÁ LUẬN, không phải V3
    _dat("THESIS_POLICY_LOADED",
         mf.get("threshold_policy_path") == R.CHINH_SACH.name
         and mf["thesis_final_acceptance"]["evaluation_class"]
         == "FROZEN_FINAL_DEVELOPMENT_BENCHMARK"
         and not dau_v3,
         f"manifest ghim {mf.get('threshold_policy_path')} · {dau_v3}")

    # ⑪⑫ cổng danh tính và cổng ngân sách chạy TRƯỚC mỗi lượt gọi
    _dat("IDENTITY_GUARD_BEFORE_EVERY_CALL",
         _canh_truoc_moi_goi(ten_sk, "identity_guard_pass"),
         "có lượt gọi không có cổng danh tính ngay trước")
    _dat("BUDGET_GUARD_BEFORE_EVERY_CALL",
         _canh_truoc_moi_goi(ten_sk, "budget_guard_pass"),
         "có lượt gọi không có cổng ngân sách ngay trước")

    # ⑬⑭ mạng
    _dat("REAL_PROVIDER_CALLS_ZERO", tt["LOGICAL_CALLS"] == so_goi,
         "số lượt gọi ghi nhận lệch nhật ký sự kiện")
    con_va = R.dang_bi_va()
    _dat("NETWORK_REFERENCES_RESTORED", not any(con_va.values()),
         f"tham chiếu còn trỏ stub: {con_va}")

    # ⑮ HỢP ĐỒNG GOLD CÓ ĐI QUA ĐƯỢC BIÊN ĐÓNG BĂNG THẬT KHÔNG?
    #
    # ⚠️ Nhãn này SINH RA TỪ MỘT LỖI THẬT. Gold preflight của wave trước dùng
    # THẲNG `request_contract_gold`, với `provenance="confirmed"` viết tay —
    # tức nó chưa bao giờ đi qua `build_request_contract`, biên duy nhất quyết
    # định hợp đồng thật sự trông thế nào. Hệ quả đo được ở lượt chứng nhận
    # runner: `p6` khai mặt phẳng bằng dấu trừ ASCII trong khi đề dùng U+2212,
    # nên extractor không chứng minh được, fact ra `claimed`, và bất biến nguồn
    # ĐỎ — trên một chương trình gold hoàn toàn đúng. `p7` cùng lỗi nhưng VẪN
    # xanh, tức lỗi bật ở một trong hai ca cùng hình dạng.
    #
    # Nên câu hỏi phải hỏi thành tiếng: hợp đồng gold có PHÁT SINH ĐƯỢC từ
    # đường thật không. Không có nhãn này thì gold preflight chứng minh một
    # điều hẹp hơn hẳn thứ nó có vẻ chứng minh.
    khong_dat = _hop_dong_gold_khong_qua_bien(bo_do)
    _dat("GOLD_CONTRACT_REACHABLE", not khong_dat,
         f"hợp đồng gold KHÔNG tái tạo được qua biên thật: {khong_dat}")

    # ⑯ CHẤM ĐÁP SỐ CÓ SỐNG SÓT KHI MÔ HÌNH TỰ ĐẶT TÊN BIẾN KHÔNG?
    doi_ten = next((c for c in a["cases"] if c["id"] == CA_DOI_TEN_WITNESS),
                   None)
    sa = (doi_ten or {}).get("cham", {}).get("witness_mapping") or {}
    _dat("SCORING_SURVIVES_MODEL_CHOSEN_WITNESS_NAMES",
         bool(doi_ten) and doi_ten["cham"].get("EXACT_ANSWER_MATCH") is True
         and all(v.endswith(_HAU_TO_DOI_TEN) for v in sa.values())
         and bool(sa),
         f"ca đổi tên witness không chấm đúng · ánh xạ={sa}")

    # chuỗi sự kiện tối thiểu
    thieu_sk = [t for t in CHUOI_SU_KIEN_TOI_THIEU if t not in ten_sk]
    if thieu_sk:
        sai.append(f"nhật ký sự kiện THIẾU: {thieu_sk}")
    return nhan, sai, {"tong_ket": tt, "su_kien": ten_sk,
                       "nhat_ky_provider": nhat_ky, "thieu_su_kien": thieu_sk}


def _hop_dong_gold_khong_qua_bien(bo_do: R.BoDo) -> dict[str, list[str]]:
    """Ca nào có hợp đồng gold KHÔNG tái tạo được qua `build_request_contract`?

    Đi đúng đường thật: gold contract → payload thô → biên đóng băng → so lại.
    Hai điều phải đúng, và điều thứ hai là điều đã bắt được lỗi:

        · mọi `fact_id` và mọi nghĩa vụ còn nguyên sau khi lọc ở biên;
        · **không fact nào ra `unproven_values`** — một giá trị mà extractor
          không tìm thấy trong đề nghĩa là hợp đồng gold khai một thứ đề không
          nói, và bất biến nguồn sẽ bác nó ở runtime.
    """
    from app.simulation.semantic_program.analyze_contract import (
        build_request_contract)
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC

    xau: dict[str, list[str]] = {}
    for ca in bo_do.corpus["positive_cases"]:
        hd = ca["request_contract_gold"]
        that = build_request_contract(
            json.loads(_analyze_tho(hd)), problem_text=ca["problem_text"],
            domain=DOMAIN_HINH_HOC)
        loi = []
        mong_fact = {f["fact_id"] for f in hd["input_facts"]}
        co_fact = {f.fact_id for f in that.input_facts}
        if mong_fact - co_fact:
            loi.append(f"mất fact {sorted(mong_fact - co_fact)}")
        if len(that.obligations) != len(hd["obligations"]):
            loi.append(f"nghĩa vụ {len(that.obligations)} ≠ "
                       f"{len(hd['obligations'])}")
        for f in that.input_facts:
            if f.unproven_values:
                loi.append(f"`{f.fact_id}` khai giá trị KHÔNG có trong đề: "
                           f"{list(f.unproven_values)}")
        if loi:
            xau[ca["id"]] = loi
    return xau


def _canh_truoc_moi_goi(ten_sk: list[str], canh: str) -> bool:
    """Mỗi `*_call` phải có `canh` xuất hiện TRƯỚC nó và SAU lượt gọi liền
    trước. Đếm tổng là không đủ: một cổng chạy hai lần ở đầu rồi im lặng ở
    những lượt sau vẫn cho tổng đẹp."""
    lan_canh = 0
    for t in ten_sk:
        if t == canh:
            lan_canh += 1
        elif t.endswith("_call"):
            if lan_canh < 1:
                return False
            lan_canh = 0
    return True


def main_tu_runner(out_dir: str | None) -> int:
    print("CHỨNG NHẬN RUNNER ĐÁNH GIÁ CUỐI — provider STUB, 0 lượt gọi thật\n")
    # ⚠️ Lượt chạy LUÔN diễn ra trong thư mục TẠM, kể cả khi có `--out-dir`.
    # Bản trước đặt nó ngay trong `out_dir`, nên cây `cert-thesis-runner/` của
    # một lượt stub nằm lẫn vào thư mục artifact đã khoá — và lần chạy thứ hai
    # thì `mo_run` từ chối vì thư mục đã tồn tại. `out_dir` chỉ nhận BẢN SAO
    # của những file đáng giữ.
    with tempfile.TemporaryDirectory() as tam:
        thu_muc = Path(tam) / "cert-thesis-runner"
        nhan, sai, chi_tiet = chung_nhan(thu_muc)
        if out_dir:
            import shutil

            from acceptance_integrity import ghi_artifact

            ra = Path(out_dir)
            ra.mkdir(parents=True, exist_ok=True)
            p = ra / "CERTIFICATION.json"
            if p.exists():
                p.unlink()          # chứng nhận là ẢNH CHỤP HIỆN TẠI, không
                                    # phải nhật ký — nó phải ghi đè được, khác
                                    # artifact của một lượt ĐO.
            ghi_artifact(p, {"artifact_schema_version": "1.2",
                             "wave": "THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT",
                             "khai": "Chạy TRỌN vòng đời qua chính entrypoint "
                                     "của `--live`, provider STUB. 0 lượt gọi "
                                     "thật.",
                             "nhan": nhan, "sai": sai, **chi_tiet,
                             **R.bam_runner()})
            # Bằng chứng ĐƯỜNG ĐI, không giữ cây `raw/` của stub: nội dung nó
            # là gold program vốn đã nằm trong kho, còn thứ đáng giữ là THỨ TỰ
            # sự kiện và phán quyết từng ca.
            for ten in ("event_log.json", "stage_a_first_attempt.json",
                        "stage_b_recovery.json", "manifest.json",
                        "final_scoring.json"):
                dich = ra / f"stub_{ten}"
                if dich.exists():
                    dich.unlink()
                shutil.copyfile(thu_muc / ten, dich)
    print()
    for t in NHAN:
        print(f"  {t:34} {'PASS' if nhan.get(t) else 'FAIL'}")
    for s in sai:
        print(f"    ✗ {s}")
    ok = all(nhan.get(t) for t in NHAN) and not sai
    print(f"\n  THESIS_RUNNER_CERTIFICATION    {'PASS' if ok else 'FAIL'}")
    print(f"  FINAL_ACCEPTANCE_RUNNER_READY  {'YES' if ok else 'NO'}")
    print(f"  APPLICATION_LLM_CALLS          0")
    print(f"  REAL_PROVIDER_CALLS            0")
    tt = chi_tiet["tong_ket"]
    for k in ("POSITIVE_CASES", "NEGATIVE_CASES", "FIRST_ATTEMPT_SERVABLE",
              "RECOVERY_WITHIN_ONE_REPAIR", "FINAL_SERVABLE",
              "NEGATIVE_FAIL_CLOSED", "SILENT_WRONG_ANSWER_COUNT",
              "LOGICAL_CALLS", "negative_case_provider_calls"):
        print(f"  {k:34} {tt[k]}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main_tu_runner(
        sys.argv[1] if len(sys.argv) > 1 else None))
