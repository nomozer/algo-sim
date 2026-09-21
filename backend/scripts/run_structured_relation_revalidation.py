# -*- coding: utf-8 -*-
"""LƯỢT LIVE MỘT REQUEST — prompt mới có làm mô hình khai đủ quan hệ không.

`STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_REVALIDATION_WITH_BROWSER_CONTACT_SHEET`
(2026-09-21).

─── CÂU HỎI ────────────────────────────────────────────────────────────────

Lượt live 2026-09-21 (trước sửa) đo được mô hình khai `line(S,A) ⟂ plane(A,B,C)`
nhưng **bỏ sót** `line(A,B) ⟂ line(A,C)` cho đề *"ABC là tam giác vuông tại A"*.
`ANALYZE_DEFINITIONAL_NORMALIZATION_PROMPT_FIX` thêm luật chuẩn hoá theo định
nghĩa. Wave này tiêu **đúng một** request để hỏi: mô hình có khai đủ chưa.

─── KHÔNG CÓ ĐƯỜNG LÙI SANG SYNTHESIS ──────────────────────────────────────

Nếu Analyze vẫn thiếu quan hệ thì **dừng trước compiler**. Không gọi tổng hợp
làm phương án thay thế, không gửi request thứ hai, không nối dài prompt. Trần
theo tầng `{vision: 0, analyze: 1, synthesis: 0}` cưỡng chế điều đó ở transport,
không phải ở lời hứa.

─── TÁI DÙNG, KHÔNG DỰNG BẢN THỨ HAI ───────────────────────────────────────

Manifest, ground truth, cổng HTTP, bộ khử bí mật và phép so quan hệ đều lấy
nguyên của `run_structured_relation_analyze_live` — cùng ca kiểm soát, cùng bộ
đo. Dựng bản thứ hai là tự cho mình quyền đổi tiêu chí sau khi thấy kết quả.

─── PHÉP SO REQUEST ────────────────────────────────────────────────────────

`--equivalence` dựng LẠI thân request của lượt trước bằng chính prompt cũ (blob
`eeacd67`) và đòi nó băm đúng `e30f0ddd…` đã commit. Khớp ⇒ phép dựng lại trung
thực ⇒ phần chênh còn lại giữa hai thân là thứ đo được, không phải suy đoán.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

GOC = Path(__file__).resolve().parents[1]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import httpx  # noqa: E402

from app.ai import gemini  # noqa: E402

from run_photo_problem_live import (  # noqa: E402
    BoKhuBiMat, ChanMangThat, KenhIn, _bay_gio, _ghi_json, _sha,
)
from run_primitive_compiler_ab import cham  # noqa: E402
import run_structured_relation_analyze_live as L  # noqa: E402

WAVE = "STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_REVALIDATION_WITH_BROWSER_CONTACT_SHEET"
RUNNER_VERSION = "structured-relation-revalidation/1"

RA = (REPO / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene"
      / "structured-relation-revalidation")

#: Thân request của lượt live TRƯỚC, đã commit ở `REQUEST_IDENTITY.json`.
PRIOR_REQUEST_BODY_SHA = (
    "e30f0ddd0ffc76b14f4cc0602df118897ad9637b378f24012053df8410bd7e85")
#: Prompt TRƯỚC lượt sửa — blob `eeacd67:backend/app/ai/skills/geometry_analyze.md`.
PRIOR_PROMPT_SHA = (
    "5746c5e5804c9f3df0618602ad5b78c2c3d1f5f227b4e4cfa630d04d7c61e004")
PRIOR_ANALYZE_TOKENS = 2019

#: Trần theo tầng của wave — lấy NGUYÊN của lượt live trước, không khai lại.
#: `synthesis: 0` là chính sách *"không có đường lùi"* ở dạng kiểm được.
TRAN_THEO_TANG_LA = L.TRAN_THEO_TANG

#: Bảng phân loại — §9 của đặc tả. ĐÓNG.
KET_QUA = (
    "PASS",
    "MODEL_NONCOMPLIANCE_AFTER_EXPLICIT_PROMPT",
    "ANALYZE_OUTPUT_INVALID",
    "ANALYZE_RELATION_UNSAFE",
    "COMPILER_REGRESSION",
    "VISUAL_REGRESSION",
    "PROVIDER_ERROR",
    "MEASUREMENT_INVALID",
)
NEXT_THEO_KET_QUA = {
    "PASS": "USER_REVIEWS_CONTACT_SHEET_THEN_MULTICASE_STRUCTURED_ANALYZE_COMPILER_BENCHMARK",
    "MODEL_NONCOMPLIANCE_AFTER_EXPLICIT_PROMPT": "DEFINITIONAL_RELATION_DETERMINISTIC_NORMALIZER_DESIGN",
    "ANALYZE_OUTPUT_INVALID": "ANALYZE_STRUCTURED_OUTPUT_VALIDATION_DIAGNOSIS",
    "ANALYZE_RELATION_UNSAFE": "ANALYZE_STRUCTURED_RELATION_SAFETY_GUARD_DIAGNOSIS",
    "COMPILER_REGRESSION": "FACT_GRAPH_PRIMITIVE_COMPILER_LIVE_REGRESSION_DIAGNOSIS",
    "VISUAL_REGRESSION": "PRIMITIVE_COMPILER_VISUAL_OUTPUT_DIAGNOSIS",
    "PROVIDER_ERROR": "RETRY_LATER_WITHOUT_CODE_CHANGE",
    "MEASUREMENT_INVALID": "LIVE_REVALIDATION_MEASUREMENT_REPAIR",
}

EXIT_PASS, EXIT_FAIL, EXIT_PRECHECK = 0, 1, 2


def _git_blob_text(ref: str) -> str:
    r = subprocess.run(("git", "show", ref), capture_output=True, cwd=str(REPO))
    return (r.stdout or b"").decode("utf-8").replace("\r\n", "\n")


# ══ ANALYZE ĐẠT CHƯA — §6 ═══════════════════════════════════════════════════
def analyze_dat(ss: dict[str, Any]) -> bool:
    """Tiêu chí PASS của tầng Analyze. ĐỌC, không suy hộ mô hình."""
    return bool(
        ss["MISSING_RELATION_COUNT"] == 0
        and ss["ACTUAL_GIVEN_RELATION_COUNT"] == ss["EXPECTED_RELATION_COUNT"]
        and ss["CRITICAL_RELATION_ACCURACY"] == 1.0
        and ss["DUPLICATE_RELATION_COUNT"] == 0
        and ss["UNVERIFIED_EXTRA_RELATION_COUNT"] == 0
        and ss["EXTRA_DERIVED_AS_GIVEN_COUNT"] == 0
        and ss["MODEL_ASSUMPTION_COUNT"] == 0
        and ss["SOURCE_FACT_RESOLUTION"] == "PASS"
        and ss["POINT_REFERENCE_VALIDATION"] == "PASS"
        and not ss["REJECTED_RELATION_CODES"]
    )


def quan_he_khong_an_toan(ss: dict[str, Any]) -> bool:
    """Có quan hệ MÂU THUẪN / thừa không xác minh / giả định dùng như GIVEN."""
    return bool(
        ss["UNVERIFIED_EXTRA_RELATION_COUNT"] > 0
        or ss["EXTRA_DERIVED_AS_GIVEN_COUNT"] > 0
        or ss["MODEL_ASSUMPTION_COUNT"] > 0
        or ss["SOURCE_FACT_RESOLUTION"] != "PASS"
        or ss["POINT_REFERENCE_VALIDATION"] != "PASS"
        or bool(ss["REJECTED_RELATION_CODES"])
    )


# ══ TẦNG DỰNG + CHẤT LƯỢNG — §7. HOÀN TOÀN OFFLINE ═════════════════════════
def chay_compiler_va_chat_luong(contract: Any, mf: dict, gt: dict) -> dict[str, Any]:
    """`RequestContract` LIVE → FactGraph → compiler → envelope → mọi cổng.

    0 lượt gọi model. Ground truth chỉ vào ở `cham`, SAU khi chương trình đã
    được sinh — compiler không bao giờ thấy nó.
    """
    from app.ai.pipeline import _dung_scene3d, _envelope_tu_route_sinh
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.geometry_compiler import contract_adapter as A
    from app.simulation.semantic_program import validator as V
    from app.simulation.semantic_program.route import verify_and_compile

    t0 = time.perf_counter()
    ka = A.build_fact_graph(contract)
    ms_graph = (time.perf_counter() - t0) * 1000
    ra: dict[str, Any] = {
        "ADAPTER_STATUS": ka.status, "ADAPTER_VERSION": ka.adapter_version,
        "ADAPTER_REASON_CODE": ka.reason_code,
        "FACT_GRAPH_LATENCY_MS": round(ms_graph, 4),
    }
    if ka.graph is None:
        ra.update(COMPILER_ELIGIBILITY="NO_GRAPH", COMPILE_STATUS="NO_GRAPH")
        return ra

    g = ka.graph
    given = [f for f in g.facts if f.status == "GIVEN"]
    derived = [f for f in g.facts if f.status == "DERIVED"]
    perp_d = [f for f in derived if f.kind == "perpendicular_lines"]
    mong_suy = {(m["kind"], tuple(m["canonical_args"]))
                for m in gt["expected_derived_perpendicular"]["items"]}
    ra.update({
        "FACT_GRAPH_VERSION": g.version,
        "FACT_GRAPH_NODE_COUNT": len(g.nodes),
        "FACT_GRAPH_GIVEN_COUNT": len(given),
        "FACT_GRAPH_DERIVED_COUNT": len(derived),
        "DERIVED_PERPENDICULAR_COUNT": len(perp_d),
        "DERIVED_PERPENDICULAR_MATCHES_GROUND_TRUTH":
            {(f.kind, tuple(f.args)) for f in perp_d} == mong_suy,
        "EVERY_DERIVED_RELATION_HAS_PARENT_PROOF":
            all(bool(f.derived_from) for f in perp_d),
        "FACTS": [f.chinh_tac() for f in g.facts],
    })

    el = C.danh_gia_eligibility(g)
    ra["COMPILER_ELIGIBILITY"] = el.status
    ra["COMPILER_ELIGIBILITY_REASON"] = el.reason_code
    if el.binding is None:
        ra["COMPILE_STATUS"] = "NOT_ELIGIBLE"
        return ra
    b = el.binding
    ra["WITNESS_OBSERVED"], ra["CONTAINER_OBSERVED"] = b.witness, b.container

    t1 = time.perf_counter()
    bd = C.bien_dich(g)
    ms_compile = (time.perf_counter() - t1) * 1000
    ra.update({
        "COMPILE_STATUS": bd.status, "COMPILER_VERSION": bd.compiler_version,
        "COMPILE_REASON_CODE": bd.reason_code,
        "CONSTRUCTION_STEPS": len(bd.construction_steps),
        "PRIMITIVE_CALLS": len(bd.primitive_calls),
        "COMPILER_LATENCY_MS": round(ms_compile, 4),
        "COMPILER_MODEL_TOKENS": 0, "SYNTHESIS_REQUESTS": 0,
        "PROGRAM_SHA256": (_sha(json.dumps(bd.program, sort_keys=True,
                                           ensure_ascii=False))
                           if bd.program else None),
        "CONSTRUCTION_STEPS_SUMMARY": [
            {"index": s.index, "primitive_id": s.primitive_id, "mo_ta": s.mo_ta}
            for s in bd.construction_steps],
    })
    if bd.program is None:
        return ra

    # ── Mọi cổng của chương trình, đúng thứ tự đường sản phẩm ───────────────
    val = V.validate_semantic_program(bd.program)
    ra["PYDANTIC_PROGRAM_VALIDATION"] = "PASS" if val.ok else "FAIL"
    if not val.ok:
        return ra
    o = verify_and_compile(contract, val.spec)
    ra.update({
        "ROUTE_STAGE": o.stage_reached,
        "ROUTE_RESULT": "served" if o.servable else f"rejected/{o.error_code}",
        "TYPE_CHECK": "PASS", "IR_STATIC_CHECK": "PASS",
        "GROUNDING_GATE": "PASS" if o.servable else "SEE_ROUTE",
    })
    canh = _dung_scene3d(val.spec, contract)

    # ── Envelope ĐÚNG như đường sản phẩm dựng, để trình duyệt phát lại ──────
    o2 = o.model_copy(update={"scene3d": canh}) if canh else o
    env = _envelope_tu_route_sinh(o2, {}, {}, None)
    ra["ENVELOPE_SHA256"] = _sha(json.dumps(env, sort_keys=True, ensure_ascii=False))
    ra["_ENVELOPE"] = env

    ca = {**mf["structure"], "case_id": gt["case_id"],
          "witness": b.witness, "container": b.container}
    c = cham(gt["case_id"], "COMPILER", ca, contract, bd.program,
             {"point_count": gt["expected_topology"]["point_count"],
              "face_count": gt["expected_topology"]["face_count"],
              "squared_lengths": gt["expected_squared_lengths"],
              "volume": gt["expected_answer"]["volume"]},
             len(bd.construction_steps))
    ra["CHAM"] = asdict(c)
    ra["VISUAL_OBLIGATION_GATE"] = c.visual_gate
    ra["SCENE_NON_EMPTY"] = c.scene_non_empty
    ra["SCENE_TOPOLOGY_RESULT"] = "PASS" if (c.point_labels_ok and c.topology_ok) else "FAIL"
    ra["GEOMETRY_CHECKS"] = {
        "squared_lengths_ok": c.squared_lengths_ok,
        "perpendicular_ok": c.perpendicular_ok,
        "non_collinear_ok": c.non_collinear_ok,
    }
    ra["FINAL_MEMORY_RESULT"] = "PASS" if c.final_memory_ok else "FAIL"
    ra["ANSWER_RESULT"] = "PASS" if c.answer_ok else "FAIL"
    return ra


# ══ PHÂN LOẠI — §9 ═════════════════════════════════════════════════════════
def phan_loai(ss: dict | None, ds: dict | None, loi: str | None,
              http: dict, tuong_duong: bool) -> str:
    if not tuong_duong:
        return "MEASUREMENT_INVALID"
    if http.get("PROVIDER_ERROR"):
        return "PROVIDER_ERROR"
    if loi or ss is None:
        return "ANALYZE_OUTPUT_INVALID"
    if quan_he_khong_an_toan(ss):
        return "ANALYZE_RELATION_UNSAFE"
    if not analyze_dat(ss):
        # Prompt ĐÃ yêu cầu rõ (13/13 độ phủ chỉ dẫn), schema hỗ trợ, mục dữ
        # kiện có sẵn — nên thiếu quan hệ ở đây là một phát biểu về MÔ HÌNH.
        return "MODEL_NONCOMPLIANCE_AFTER_EXPLICIT_PROMPT"
    if ds is None or ds.get("COMPILER_ELIGIBILITY") != "SUPPORTED" \
            or ds.get("COMPILE_STATUS") != "COMPILED" \
            or ds.get("PYDANTIC_PROGRAM_VALIDATION") != "PASS" \
            or ds.get("ROUTE_RESULT") != "served":
        return "COMPILER_REGRESSION"
    c = ds.get("CHAM") or {}
    if not c.get("quality_pass") or ds.get("VISUAL_OBLIGATION_GATE") != "COVERED":
        return "VISUAL_REGRESSION"
    return "PASS"


# ══ §4 · TƯƠNG ĐƯƠNG REQUEST ═══════════════════════════════════════════════
def _diff_pointer(a: Any, b: Any, goc: str = "") -> list[str]:
    if type(a) is not type(b):
        return [goc or "/"]
    if isinstance(a, dict):
        ra: list[str] = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                ra.append(f"{goc}/{k}")
            else:
                ra += _diff_pointer(a[k], b[k], f"{goc}/{k}")
        return ra
    if isinstance(a, list):
        if len(a) != len(b):
            return [goc or "/"]
        ra = []
        for i, (x, y) in enumerate(zip(a, b)):
            ra += _diff_pointer(x, y, f"{goc}/{i}")
        return ra
    return [] if a == b else [goc or "/"]


def kiem_tuong_duong_request() -> dict[str, Any]:
    """Dựng lại thân request CŨ và MỚI offline rồi so từng con trỏ JSON."""
    from app.ai import pipeline as PL
    from app.simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC

    mf = L.doc_manifest()
    de = L.de_bai(mf)
    prompt_cu = _git_blob_text("eeacd67:backend/app/ai/skills/geometry_analyze.md")
    prompt_moi = gemini.load_skill("geometry_analyze")
    than: dict[str, bytes] = {}
    dau_muc: dict[str, str] = {}

    def chay(nhan: str, skill_text: str | None) -> None:
        # ⚠️ Vá ở `pipeline`, KHÔNG ở `gemini`. `pipeline.py` nhập `load_skill`
        # ở mức module (`from app.ai.gemini import call_gemini, load_skill`),
        # nên vá `gemini.load_skill` không tới nó — đo được: hai thân request
        # ra HỆT NHAU và `DIFFERING_JSON_POINTERS` rỗng, tức phép so tự vô hiệu
        # hoá chính nó mà vẫn trông như một kết quả.
        goc_load = PL.load_skill

        def load(name: str) -> str:
            return skill_text if (skill_text and name == "geometry_analyze") \
                else goc_load(name)

        def xu_ly(req: httpx.Request) -> httpx.Response:
            than[nhan] = req.content
            # Model nằm ở ĐƯỜNG DẪN, không ở thân — nên phải so riêng.
            dau_muc[nhan] = f"{req.url.scheme}://{req.url.host}{req.url.path}"
            return httpx.Response(200, json={"candidates": [
                {"content": {"parts": [{"text": "{}"}]}}]})

        cong = L.CongQuetCam(httpx.MockTransport(xu_ly), 1, BoKhuBiMat(()),
                             tran_theo_tang=L.TRAN_THEO_TANG, chuoi_cam=())
        cong.dat_ca("EQ")
        PL.load_skill = load
        try:
            with L.cai_cong_http(cong), L.dung_ngan_sach(
                    gemini.ApiBudget(max_api_calls=1, max_attempts=1,
                                     max_logical_calls=1)):
                asyncio.run(PL.stage_semantic_analyze(de, "KHOA_GIA",
                                                      domain=DOMAIN_HINH_HOC))
        finally:
            PL.load_skill = goc_load

    chay("cu", prompt_cu)
    chay("moi", None)
    a, b = json.loads(than["cu"]), json.loads(than["moi"])
    khac = _diff_pointer(a, b)
    chi_prompt = khac == ["/systemInstruction/parts/0/text"]
    dung_lai_khop = _sha(than["cu"]) == PRIOR_REQUEST_BODY_SHA

    gc = b.get("generationConfig") or {}
    return {
        "WAVE": WAVE,
        "_PHUONG_PHAP": "Dựng LẠI thân request cũ bằng chính prompt tại `eeacd67`, rồi "
                        "đòi nó băm đúng bản đã commit. Khớp ⇒ phép dựng lại trung thực.",
        "PRIOR_REQUEST_BODY_SHA256": PRIOR_REQUEST_BODY_SHA,
        "REBUILT_PRIOR_BODY_SHA256": _sha(than["cu"]),
        "REBUILD_MATCHES_COMMITTED_PRIOR": dung_lai_khop,
        "NEW_REQUEST_BODY_SHA256": _sha(than["moi"]),
        "DIFFERING_JSON_POINTERS": khac,
        "REQUEST_EQUALS_PRIOR_EXCEPT_PROMPT": bool(
            dung_lai_khop and chi_prompt and dau_muc["cu"] == dau_muc["moi"]),
        "PRIOR_PROMPT_SHA256": _sha(prompt_cu),
        "NEW_PROMPT_SHA256": _sha(prompt_moi),
        "PRIOR_PROMPT_SHA_MATCHES_EXPECTED": _sha(prompt_cu) == PRIOR_PROMPT_SHA,
        "PROMPT_DELTA_IS_REGISTERED_BLOCK":
            prompt_moi.replace("\n" + _KHOI().rstrip("\n"), "", 1) == prompt_cu,
        "ENDPOINT_PRIOR": dau_muc["cu"],
        "ENDPOINT_NEW": dau_muc["moi"],
        "ENDPOINT_IDENTICAL": dau_muc["cu"] == dau_muc["moi"],
        "GENERATION_CONFIG_KEYS": sorted(gc),
        "TEMPERATURE": gc.get("temperature"),
        "NO_THINKING_CONFIG": "thinkingConfig" not in gc,
        "NO_MAX_OUTPUT_TOKENS": "maxOutputTokens" not in gc,
        "USER_TEXT_IDENTICAL": _diff_pointer(a.get("contents"), b.get("contents")) == [],
    }


def _KHOI() -> str:
    import diagnose_structured_relation_prompt as D
    return D.LUAT_DE_XUAT


# ══ §8 · CONTACT SHEET ═════════════════════════════════════════════════════
#: Thêm SAU lượt live (2026-09-21). Nó chỉ ĐỌC artifact đã ghi và ghép ảnh —
#: không tính lại, không chấm lại, không chạm một phép đo nào.
_CS_RONG, _CS_LE, _CS_DONG = 1680, 28, 22


def dung_contact_sheet(thu_muc: Path) -> dict[str, Any]:
    from PIL import Image, ImageDraw, ImageFont

    def j(ten: str) -> dict:
        return json.loads((thu_muc / ten).read_text(encoding="utf-8"))

    mf, gt = L.doc_manifest(), L.doc_ground_truth()
    live, ss = j("ANALYZE_LIVE_RESULT_REDACTED.json"), j("STRUCTURED_RELATION_COMPARISON.json")
    fg, cq = j("FACT_GRAPH_RESULT.json"), j("COMPILER_AND_QUALITY_RESULT.json")
    br = json.loads((thu_muc / "browser" / "BROWSER_REPLAY_RESULT.json")
                    .read_text(encoding="utf-8"))
    u = live.get("USAGE") or {}
    c = cq.get("CHAM") or {}

    def ft(px: int, dam: bool = False):
        for ten in (("seguisb.ttf", "arialbd.ttf") if dam else ("segoeui.ttf", "arial.ttf")):
            try:
                return ImageFont.truetype(ten, px)
            except OSError:
                continue
        return ImageFont.load_default()

    F, FB, FS = ft(17), ft(19, True), ft(15)
    khoi: list[tuple[str, list[str]]] = [
        ("1. ĐỀ KIỂM SOÁT (R01) — không phải C01 lịch sử",
         [*L.de_bai(mf).split("\n"),
          f"input sha256 {live['INPUT_TEXT_SHA256'][:32]}…"]),
        ("2. HAI QUAN HỆ GIVEN DO ANALYZE KHAI",
         [f"{r['kind']}({', '.join(r['canonical_args'])})"
          f"  ← {r['source_fact_id']}  · model_assumption={r['model_assumption']}"
          for r in ss["RELATIONS"]]
         + [f"accuracy {ss['CRITICAL_RELATION_ACCURACY']} · thiếu "
            f"{ss['MISSING_RELATION_COUNT']} · thừa "
            f"{ss['UNVERIFIED_EXTRA_RELATION_COUNT']} · hệ quả khai thành GIVEN "
            f"{ss['EXTRA_DERIVED_AS_GIVEN_COUNT']}"]),
        ("3. FACT GRAPH (geometry-fact-graph/2)",
         [f"GIVEN {fg['FACT_GRAPH_GIVEN_COUNT']} · DERIVED {fg['FACT_GRAPH_DERIVED_COUNT']}"
          f" · nút {fg['FACT_GRAPH_NODE_COUNT']}",
          f"quan he vuong goc suy ra: {fg['DERIVED_PERPENDICULAR_COUNT']}/3 — khớp ground truth: "
          f"{fg['DERIVED_PERPENDICULAR_MATCHES_GROUND_TRUTH']}",
          f"mỗi quan hệ suy ra nêu được cha: {fg['EVERY_DERIVED_RELATION_HAS_PARENT_PROOF']}"]),
        ("4. COMPILER TẤT ĐỊNH (0 lượt gọi model)",
         [f"eligibility {cq['COMPILER_ELIGIBILITY']} · {cq['COMPILE_STATUS']}"
          f" · {cq['CONSTRUCTION_STEPS']} bước · {cq['PRIMITIVE_CALLS']} primitive",
          *[f"  {s['index']}. {s['primitive_id']}"
            for s in (cq.get("CONSTRUCTION_STEPS_SUMMARY") or [])[:6]],
          f"  … ({cq['CONSTRUCTION_STEPS']} bước) · model tokens "
          f"{cq['COMPILER_MODEL_TOKENS']} · synthesis {cq['SYNTHESIS_REQUESTS']}"]),
    ]
    khoi_phai: list[tuple[str, list[str]]] = [
        ("7. TOPOLOGY VÀ KIỂM HÌNH HỌC",
         [f"cảnh không rỗng {c.get('scene_non_empty')} · 4 đỉnh/4 mặt "
          f"{cq['SCENE_TOPOLOGY_RESULT']}",
          f"|AB|²=9 |AC|²=16 |SA|²=25 → {cq['GEOMETRY_CHECKS']['squared_lengths_ok']}",
          f"AB-AC, SA-AB, SA-AC vuong goc → {cq['GEOMETRY_CHECKS']['perpendicular_ok']}",
          f"A,B,C không thẳng hàng → {cq['GEOMETRY_CHECKS']['non_collinear_ok']}",
          f"cổng trực quan {cq['VISUAL_OBLIGATION_GATE']} · route {cq['ROUTE_RESULT']}"]),
        ("8. ĐÁP SỐ · TOKEN · ĐỘ TRỄ",
         [f"final_memory {cq['FINAL_MEMORY_RESULT']} · answer {cq['ANSWER_RESULT']}"
          f" (kỳ vọng {gt['expected_answer']['volume']})",
          f"tokens  in {u.get('promptTokenCount')} · out {u.get('candidatesTokenCount')}"
          f" · thought {u.get('thoughtsTokenCount')} · TỔNG {u.get('totalTokenCount')}",
          f"lượt trước {PRIOR_ANALYZE_TOKENS} → nay {u.get('totalTokenCount')}"
          f"  (HAI lượt ở HAI thời điểm, KHÔNG phải bằng chứng tiết kiệm)",
          f"analyze {live['LATENCY_MS']} ms · fact graph {fg['FACT_GRAPH_LATENCY_MS']} ms"
          f" · compiler {cq['COMPILER_LATENCY_MS']} ms",
          f"request: analyze {live['ANALYZE_HTTP_REQUESTS']} · vision "
          f"{live['VISION_HTTP_REQUESTS']} · synthesis {live['SYNTHESIS_HTTP_REQUESTS']}"
          f" · retry {live['RETRIES']}"]),
    ]

    anh_d = Image.open(thu_muc / "browser" / "1440x900.png")
    anh_m = Image.open(thu_muc / "browser" / "390x844.png")
    w_d = (_CS_RONG - _CS_LE * 3) * 2 // 3
    anh_d = anh_d.resize((w_d, round(anh_d.height * w_d / anh_d.width)))
    w_m = _CS_RONG - _CS_LE * 3 - w_d
    anh_m = anh_m.resize((w_m, round(anh_m.height * w_m / anh_m.width)))

    cao_van = 60 + sum(34 + _CS_DONG * len(d) for _, d in khoi)
    cao_phai = 60 + sum(34 + _CS_DONG * len(d) for _, d in khoi_phai)
    cao = 96 + cao_van + _CS_LE + max(anh_d.height, anh_m.height) + _CS_LE + cao_phai + _CS_LE
    im = Image.new("RGB", (_CS_RONG, cao), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, _CS_RONG, 76], fill=(17, 24, 39))
    d.text((_CS_LE, 16), "STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_REVALIDATION"
           " — CONTACT SHEET", font=FB, fill=(255, 255, 255))
    d.text((_CS_LE, 44), f"{live['RAN_AT']} · {mf['model']} · T={mf['temperature']}"
           f" · OUTCOME {live['OUTCOME']} · USER_VISUAL_APPROVAL = PENDING",
           font=FS, fill=(203, 213, 225))

    y = 96
    for tieu_de, dong in khoi:
        d.text((_CS_LE, y), tieu_de, font=FB, fill=(30, 41, 59))
        y += 30
        for t in dong:
            d.text((_CS_LE + 8, y), t, font=F, fill=(51, 65, 85))
            y += _CS_DONG
        y += 12
    y += 4
    d.text((_CS_LE, y - 26), "5. CẢNH — 1440x900", font=FB, fill=(30, 41, 59))
    d.text((_CS_LE * 2 + w_d, y - 26), "6. CẢNH — 390x844 (DPR 2)", font=FB, fill=(30, 41, 59))
    im.paste(anh_d, (_CS_LE, y))
    im.paste(anh_m, (_CS_LE * 2 + w_d, y))
    d.rectangle([_CS_LE, y, _CS_LE + anh_d.width, y + anh_d.height], outline=(203, 213, 225))
    d.rectangle([_CS_LE * 2 + w_d, y, _CS_LE * 2 + w_d + anh_m.width, y + anh_m.height],
                outline=(203, 213, 225))
    # Khối 7–8 nằm DƯỚI ảnh desktop, trong cột trái: ảnh mobile cao hơn hẳn nên
    # xếp chúng sau ảnh CAO NHẤT để lại một khoảng trắng bằng nửa trang.
    y_trai = y + anh_d.height + _CS_LE
    y_phai = y + anh_m.height
    for tieu_de, dong in khoi_phai:
        d.text((_CS_LE, y_trai), tieu_de, font=FB, fill=(30, 41, 59))
        y_trai += 30
        for t in dong:
            d.text((_CS_LE + 8, y_trai), t, font=F, fill=(51, 65, 85))
            y_trai += _CS_DONG
        y_trai += 12
    y = max(y_trai, y_phai)

    ra = thu_muc / "CONTACT_SHEET.png"
    im.crop((0, 0, _CS_RONG, min(y + 16, cao))).save(ra)
    return {
        "WAVE": WAVE, "FILE": ra.name,
        "SHA256": _sha(ra.read_bytes()),
        "BYTES": ra.stat().st_size,
        "BROWSER_ALL_PASS": br["dat"],
        "_KHONG_CHUA": ["API key", "raw response", "raw prompt",
                        "toàn bộ semantic program", "headers", "log dài"],
        "USER_VISUAL_APPROVAL": "PENDING",
    }


# ══ LƯỢT LIVE ══════════════════════════════════════════════════════════════
def main() -> int:
    ap = argparse.ArgumentParser(description=WAVE)
    ap.add_argument("--equivalence", action="store_true",
                    help="dựng request offline và so với lượt trước — 0 request thật")
    ap.add_argument("--live", action="store_true",
                    help="TIÊU QUOTA: gửi đúng 1 request Analyze thật")
    ap.add_argument("--contact-sheet", action="store_true",
                    help="ghép contact sheet từ artifact đã ghi — 0 request")
    ap.add_argument("--ra", default=str(RA))
    a = ap.parse_args()
    thu_muc = Path(a.ra)
    thu_muc.mkdir(parents=True, exist_ok=True)

    if a.contact_sheet:
        kq = dung_contact_sheet(thu_muc)
        (thu_muc / "CONTACT_SHEET_MANIFEST.json").write_text(
            json.dumps(kq, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"CONTACT_SHEET = {kq['FILE']} ({kq['BYTES']} byte) · "
              f"sha {kq['SHA256'][:16]}…")
        return EXIT_PASS

    if a.equivalence:
        with ChanMangThat() as chan:
            eq = kiem_tuong_duong_request()
        eq["REAL_NETWORK_ATTEMPTS"] = chan.attempts
        (thu_muc / "REQUEST_EQUIVALENCE.json").write_text(
            json.dumps(eq, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"REBUILD_MATCHES_COMMITTED_PRIOR = {eq['REBUILD_MATCHES_COMMITTED_PRIOR']}")
        print(f"REQUEST_EQUALS_PRIOR_EXCEPT_PROMPT = {eq['REQUEST_EQUALS_PRIOR_EXCEPT_PROMPT']}")
        print(f"DIFFERING_JSON_POINTERS = {eq['DIFFERING_JSON_POINTERS']}")
        return EXIT_PASS if eq["REQUEST_EQUALS_PRIOR_EXCEPT_PROMPT"] else EXIT_FAIL

    if not a.live:
        print("Chứng minh offline: tests/geometry/test_structured_relation_revalidation.py")
        print("So request:  --equivalence   ·  Gửi request thật:  --live")
        return EXIT_PRECHECK

    mf, gt = L.doc_manifest(), L.doc_ground_truth()
    de = L.de_bai(mf)
    key = L.doc_khoa()
    khu = BoKhuBiMat((key,) if key else ())
    kenh = KenhIn(khu)
    if not key:
        kenh.loi("GEMINI_API_KEY vắng mặt — dừng với 0 request.")
        return EXIT_PRECHECK

    # Tương đương request phải ĐẠT trước khi tiêu quota.
    eq = kiem_tuong_duong_request()
    if not eq["REQUEST_EQUALS_PRIOR_EXCEPT_PROMPT"]:
        kenh.loi(f"MEASUREMENT_INVALID: {eq['DIFFERING_JSON_POINTERS']} — 0 request.")
        _ghi_json(thu_muc, "REQUEST_EQUIVALENCE_FAILED.json", eq, khu)
        return EXIT_FAIL
    # Bản đã đăng ký trước live là BẤT BIẾN — `_ghi_json` từ chối ghi đè, đúng
    # luật. Thay vì tránh luật ấy, đối chiếu: phép so phải cho CÙNG kết quả lúc
    # chạy thật. Lệch ⇒ điều kiện đo đã đổi giữa preregistration và lượt chạy.
    cu = thu_muc / "REQUEST_EQUIVALENCE.json"
    if cu.exists():
        da_khai = json.loads(cu.read_text(encoding="utf-8"))
        for k in ("REBUILT_PRIOR_BODY_SHA256", "NEW_REQUEST_BODY_SHA256",
                  "DIFFERING_JSON_POINTERS", "REQUEST_EQUALS_PRIOR_EXCEPT_PROMPT"):
            if da_khai.get(k) != eq[k]:
                kenh.loi(f"MEASUREMENT_INVALID: `{k}` lệch bản đã đăng ký — 0 request.")
                return EXIT_FAIL
    else:
        _ghi_json(thu_muc, "REQUEST_EQUIVALENCE.json", eq, khu)

    cong = L.tao_cong(khu, gt, httpx.AsyncHTTPTransport())
    cong.dat_ca(gt["case_id"])
    t0 = time.perf_counter()
    hd, err, no = asyncio.run(L.mot_luot(de, key, cong))
    latency = round((time.perf_counter() - t0) * 1000, 1)

    http = cong.tong_hop()
    ss = L.so_sanh_quan_he(hd, gt) if hd is not None else None
    ds = (chay_compiler_va_chat_luong(hd, mf, gt)
          if (ss is not None and analyze_dat(ss)) else None)
    ket = phan_loai(ss, ds, err or no, http, True)

    env = (ds or {}).pop("_ENVELOPE", None)
    if env is not None:
        (thu_muc / "REPLAY_ENVELOPE.json").write_text(
            json.dumps({"envelope": env}, ensure_ascii=False, indent=2),
            encoding="utf-8")

    usage = next((r.get("usage_metadata") for r in cong.records
                  if r.get("usage_metadata")), None) or {}
    ban = {
        "WAVE": WAVE, "RUNNER_VERSION": RUNNER_VERSION, "RAN_AT": _bay_gio(),
        "CASE_ID": gt["case_id"], "DATASET_CLASS": mf["dataset_class"],
        "INPUT_TEXT_SHA256": L.bam_van_ban(de),
        "MODEL": mf["model"], "TEMPERATURE": mf["temperature"],
        "TIMEOUT_SECONDS": mf["timeout_seconds"], "LATENCY_MS": latency,
        "ANALYZE_ERROR": khu.chuoi(err) if err else None,
        "RUNNER_EXCEPTION": khu.chuoi(no) if no else None,
        "MODEL_OUTPUT_RECEIVED": hd is not None,
        "JSON_PARSE_RESULT": "FAIL" if (err and "JSON" in err) else (
            "PASS" if hd is not None else "UNKNOWN"),
        "PYDANTIC_VALIDATION_RESULT": "PASS" if hd is not None else "FAIL",
        "REQUEST_CONTRACT_VALIDATION": "PASS" if hd is not None else "FAIL",
        "ANALYZE_PASS": bool(ss and analyze_dat(ss)),
        "OUTCOME": ket, "NEXT_ACTION": NEXT_THEO_KET_QUA[ket],
        "PREVIOUS_ANALYZE_TOKENS": PRIOR_ANALYZE_TOKENS,
        "USAGE": usage,
        **http, **cong.bang_chung_danh_tinh(),
    }
    _ghi_json(thu_muc, "ANALYZE_LIVE_RESULT_REDACTED.json", ban, khu)
    _ghi_json(thu_muc, "REQUEST_IDENTITY.json",
              {"RECORDS": cong.records, **cong.bang_chung_danh_tinh()}, khu)
    if ss is not None:
        _ghi_json(thu_muc, "STRUCTURED_RELATION_COMPARISON.json", ss, khu)
    if ds is not None:
        _ghi_json(thu_muc, "FACT_GRAPH_RESULT.json",
                  {k: v for k, v in ds.items()
                   if k in ("ADAPTER_STATUS", "ADAPTER_VERSION", "FACT_GRAPH_VERSION",
                            "FACT_GRAPH_NODE_COUNT", "FACT_GRAPH_GIVEN_COUNT",
                            "FACT_GRAPH_DERIVED_COUNT", "DERIVED_PERPENDICULAR_COUNT",
                            "DERIVED_PERPENDICULAR_MATCHES_GROUND_TRUTH",
                            "EVERY_DERIVED_RELATION_HAS_PARENT_PROOF", "FACTS",
                            "FACT_GRAPH_LATENCY_MS")}, khu)
        _ghi_json(thu_muc, "COMPILER_AND_QUALITY_RESULT.json",
                  {k: v for k, v in ds.items() if k != "FACTS"}, khu)

    kenh.in_(f"OUTCOME = {ket}")
    kenh.in_(f"ANALYZE = {http['ANALYZE_HTTP_REQUESTS']} · VISION = "
             f"{http['VISION_HTTP_REQUESTS']} · SYNTHESIS = "
             f"{http['SYNTHESIS_HTTP_REQUESTS']} · RETRIES = {http['RETRIES']}")
    if ss:
        kenh.in_(f"RELATIONS = {ss['ACTUAL_GIVEN_RELATION_COUNT']}/"
                 f"{ss['EXPECTED_RELATION_COUNT']} · accuracy "
                 f"{ss['CRITICAL_RELATION_ACCURACY']}")
    kenh.in_(f"NEXT_ACTION = {NEXT_THEO_KET_QUA[ket]}")
    kenh.in_(f"→ {thu_muc}")
    return EXIT_PASS if ket == "PASS" else EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
