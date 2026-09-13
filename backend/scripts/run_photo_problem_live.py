# -*- coding: utf-8 -*-
"""LƯỢT PROVIDER THẬT cho đường ảnh → mô phỏng — ĐÚNG ba ca đã đăng ký TRƯỚC.

`PHOTO_PROBLEM_TO_SCENE_END_TO_END_IMPLEMENTATION §11`. **TIÊU QUOTA THẬT** khi
chạy không có `--gia-lap`.

─── NHÃN KHAI TRƯỚC KHI RÚT CA (CLAUDE.md §4) ─────────────────────────────

    MEASUREMENT_CLASS       = DEVELOPMENT_DIAGNOSTIC
    HELD_OUT_CLAIM          = NO — ảnh TỔNG HỢP; đề lấy từ corpus đã đo ở thesis-final
    EVALUATOR_INDEPENDENCE  = OPERATOR_IS_DEVELOPER
    CALL_CEILING_LOGICAL    = `TRAN_LUOT_LOGIC` (dẫn xuất bên dưới, có `ApiBudget` chặn)
    HUMAN_EDIT              = NONE — văn bản đi TẦNG B đúng là văn bản máy đọc;
                              cờ "cần xác nhận" được GHI LẠI, không chặn lượt đo

Ba ca, thứ tự cố định (§11):

    1. c01 — ảnh rõ có đề chữ                  → kỳ vọng dựng được cảnh
    2. c05 — ảnh nghiêng có công thức và hình   → kỳ vọng dựng được cảnh
    3. c11 — ảnh chỉ có hình, thiếu dữ kiện      → kỳ vọng TỪ CHỐI ở tầng A

─── KHÔNG CÓ CREDENTIAL ────────────────────────────────────────────────────

Thiếu `ALLOW_LIVE_AI=1` hoặc `GEMINI_API_KEY` ⇒ ghi
`REAL_PROVIDER_EVIDENCE = NOT_ESTABLISHED`, **0 lượt gọi**, thoát mã 3. Không
bao giờ thay bằng fixture rồi ghi PASS.

`--gia-lap`: provider GIẢ cho CẢ HAI tầng — tầng A trả ground truth, tầng B phát
lại byte đóng băng của `thesis-final` theo đúng thứ tự lượt gọi. Chỉ để CHỨNG
NHẬN runner chạy hết đường; nhãn `FIXTURE_DRY_RUN`, KHÔNG phải bằng chứng
provider. Có guard mạng: một lượt chạm mạng là NÉM.

Không ghi đè: mỗi lượt một thư mục có dấu thời gian dưới `.../photo-problem-to-scene/live/`.
"""

from __future__ import annotations

import argparse
import asyncio
import difflib
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BE))
sys.path.insert(0, str(BE / "scripts"))

import build_photo_problem_corpus as CORP  # noqa: E402
from app.ai import gemini, pipeline  # noqa: E402
from app.ai.telemetry import reset_usage, usage_report  # noqa: E402
from app.ingestion import image_extraction as ie  # noqa: E402
from app.ingestion.image import normalize_image  # noqa: E402

BANG_CHUNG = CORP.RA
RA = BANG_CHUNG / "live"

#: (id ảnh, ca thesis-final để phát lại khi `--gia-lap`, kỳ vọng, mô tả §11)
CA_DANG_KY = (
    ("c01_ro_chop_thiet_dien", "p1_chop_thiet_dien_khoang_cach", "ACCEPT",
     "ảnh rõ có đề chữ"),
    ("c05_nghieng_cong_thuc_hinh_tru", "p6_thiet_dien_elip_cua_hinh_tru", "ACCEPT",
     "ảnh nghiêng có công thức và hình minh hoạ"),
    ("c11_chi_co_hinh", None, "REJECT_AT_A:MISSING_PROBLEM_TEXT",
     "ảnh thiếu dữ kiện phải bị từ chối an toàn"),
)

#: Mỗi ảnh MỘT lượt đọc; mỗi ca kỳ vọng dựng: 1 lượt đọc đề + tối đa
#: `MAX_SEMANTIC_PROGRAM_ATTEMPTS` lượt tổng hợp. Thử lại HTTP tạm thời không
#: tính vào trần LOGIC (`ApiBudget` đếm riêng).
TRAN_LUOT_LOGIC = len(CA_DANG_KY) + sum(
    1 + pipeline.MAX_SEMANTIC_PROGRAM_ATTEMPTS for c in CA_DANG_KY if c[2] == "ACCEPT")

NHAN = {
    "MEASUREMENT_CLASS": "DEVELOPMENT_DIAGNOSTIC",
    "HELD_OUT_CLAIM": "NO",
    "EVALUATOR_INDEPENDENCE": "OPERATOR_IS_DEVELOPER",
    "CALL_CEILING_LOGICAL": TRAN_LUOT_LOGIC,
    "HUMAN_EDIT": "NONE",
}


def _sha(x: str) -> str:
    return hashlib.sha256(x.encode("utf-8")).hexdigest()


def _ban_ghi_dung(m: dict) -> str:
    """Ground truth dưới dạng output tầng A — CHỈ dùng khi `--gia-lap`."""
    text = m["ground_truth_text"] or ""
    return json.dumps({
        "problem_text_verbatim": text, "problem_text_normalized": text, "math_expressions": [],
        "named_points": m["expected_named_points"], "named_lines": [], "named_planes": [],
        "named_solids": [], "given_relations": [], "has_diagram": bool(m["diagram"]),
        "diagram_observations": ["Có hình minh hoạ."] if m["diagram"] else [],
        "text_diagram_conflicts": [], "uncertain_tokens": [], "missing_regions": [],
        "confidence": 0.9,
    }, ensure_ascii=False)


async def mot_ca(m: dict, ky_vong: str, mo_ta: str, api_key: str, cache_version: str) -> dict:
    anh = normalize_image((BANG_CHUNG / m["file"]).read_bytes())
    ident = ie.vision_identity(cache_version)
    kq: dict = {
        "id": m["id"], "mo_ta": mo_ta, "expected_outcome": ky_vong,
        "normalized_image_sha256": anh.sha256,
        "request_hash": _sha(json.dumps({"image": anh.sha256, **ident}, sort_keys=True)),
        "ground_truth_text": m["ground_truth_text"],
    }
    reset_usage()
    try:
        ex = await ie.extract_problem_from_image(anh, api_key, cache_version=None)
    except (ie.VisionBusy, ie.VisionUnavailable, ie.VisionContractError) as err:
        kq.update(tang_A={"loi": type(err).__name__, "chi_tiet": str(err)[:300]},
                  tang_B=None, dat=False, token_usage=usage_report())
        return kq

    x, a = ex.extraction, ex.assessment
    gt = m["ground_truth_text"] or ""
    diem_gt = m["expected_named_points"]
    diem_doc = CORP._diem_co_ten(a.problem_text)
    kq["response_hash"] = _sha(json.dumps(x.model_dump(), ensure_ascii=False, sort_keys=True))
    kq["tang_A"] = {
        "assessment": a.to_dict(),
        "confidence": x.confidence,
        "problem_text_normalized": x.problem_text_normalized,
        "uncertain_tokens": [t.model_dump() for t in x.uncertain_tokens],
        "missing_regions": x.missing_regions,
        "text_diagram_conflicts": x.text_diagram_conflicts,
        "diagram_observations": x.diagram_observations,
        "exact_text_match": (a.problem_text == gt) if gt else None,
        "text_similarity_vs_ground_truth":
            round(difflib.SequenceMatcher(None, gt, a.problem_text).ratio(), 4) if gt else None,
        "named_points_recall":
            round(sum(1 for p in diem_gt if p in diem_doc) / len(diem_gt), 4) if diem_gt else None,
        "named_points_missing": [p for p in diem_gt if p not in diem_doc],
    }
    if a.status == "rejected":
        kq.update(tang_B=None, dat=ky_vong == f"REJECT_AT_A:{a.rejection_code}",
                  token_usage=usage_report())
        return kq
    # Ca PHẢI bị từ chối mà tầng A cho qua là bịa im lặng — ghi tên, rồi vẫn đi
    # tầng B để thấy hệ có chặn được ở đó không.
    kq["silent_hallucination_at_A"] = ky_vong.startswith("REJECT_AT_A")

    env = await pipeline.run_pipeline(a.problem_text, api_key, semantic_route="serve")
    canh = env.get("scene3d") or {}
    vat = canh.get("objects") or []
    loai = sorted({o.get("type") for o in vat})
    kq["tang_B"] = {
        "status": env.get("status"), "stage_reached": env.get("stage_reached"),
        "error_code": env.get("error_code"), "failure_category": env.get("failure_category"),
        "scene_object_count": len(vat), "scene_event_count": len(canh.get("events") or []),
        "scene_kinds": loai, "expected_scene_kinds": sorted(m["expected_scene_kinds"]),
        "scene_kinds_match": loai == sorted(m["expected_scene_kinds"]),
    }
    kq["dat"] = ky_vong == "ACCEPT" and env.get("status") == "ok" and bool(vat)
    kq["token_usage"] = usage_report()
    return kq


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gia-lap", action="store_true",
                    help="provider GIẢ cho cả hai tầng — chứng nhận runner, KHÔNG phải bằng chứng")
    ns = ap.parse_args()

    corpus = json.loads((BANG_CHUNG / "CORPUS.json").read_text(encoding="utf-8"))
    theo_id = {m["id"]: m for m in corpus["items"]}
    che_do = "FIXTURE_DRY_RUN" if ns.gia_lap else "REAL_PROVIDER"
    luc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    thu_muc = RA / f"{luc}_{che_do.lower()}"
    if thu_muc.exists():
        print(f"TỪ CHỐI: {thu_muc} đã tồn tại — không ghi đè lượt cũ.")
        return 2
    cv = CORP._cache_version()
    ket: dict = {
        "wave": "PHOTO_PROBLEM_TO_SCENE_END_TO_END_IMPLEMENTATION",
        "run_id": thu_muc.name, "mode": che_do, **NHAN,
        # Ground truth là đề của lượt đo cuối ⇒ artifact DẪN XUẤT, khai kiểm được (`test_A5`).
        "source_artifact_path": "docs/evaluation/geometry/thesis-final-acceptance/CORPUS.json",
        "CORPUS_KIND": corpus["CORPUS_KIND"], "REAL_PHOTO_CORPUS": corpus["REAL_PHOTO_CORPUS"],
        "MODEL_IDENTITY": gemini.MODEL, "cache_version": cv,
        "vision_identity": ie.vision_identity(cv),
        "cases_registered": [c[0] for c in CA_DANG_KY],
    }

    api_key = os.getenv("GEMINI_API_KEY")
    if not ns.gia_lap and (os.getenv("ALLOW_LIVE_AI") != "1" or not api_key):
        thieu = [t for t, ok in (("ALLOW_LIVE_AI=1", os.getenv("ALLOW_LIVE_AI") == "1"),
                                 ("GEMINI_API_KEY", bool(api_key))) if not ok]
        ket.update(REAL_PROVIDER_EVIDENCE="NOT_ESTABLISHED", thieu=thieu,
                   APPLICATION_LLM_CALLS=0, REAL_PROVIDER_CALLS=0, cases=[])
        thu_muc.mkdir(parents=True)
        (thu_muc / "RESULT.json").write_text(json.dumps(ket, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"REAL_PROVIDER_EVIDENCE = NOT_ESTABLISHED (thiếu {', '.join(thieu)}) · 0 lượt gọi")
        print(f"→ {thu_muc / 'RESULT.json'}")
        return 3

    ca_ket: list[dict] = []
    goi_gia = 0
    if ns.gia_lap:
        import replay_negative_boundaries as RNB

        cu_a, cu_b = ie.call_gemini, pipeline.call_gemini
        with RNB.NetworkGuard() as guard:
            try:
                for cid, nguon, ky_vong, mo_ta in CA_DANG_KY:
                    m = theo_id[cid]

                    async def gia_a(*a, _m=m, **k):
                        nonlocal goi_gia
                        goi_gia += 1
                        return _ban_ghi_dung(_m)

                    ie.call_gemini = gia_a
                    prov = RNB.ProviderPhatLaiTheoThuTu(RNB.doc_raw_theo_thu_tu(nguon)) if nguon else None
                    if prov:
                        pipeline.call_gemini = prov
                    r = asyncio.run(mot_ca(m, ky_vong, mo_ta, "KHOA_GIA_LAP", cv))
                    if prov:
                        goi_gia += len(prov.calls)
                        r["replay_con_lai"] = prov.con_lai()
                    ca_ket.append(r)
            finally:
                ie.call_gemini, pipeline.call_gemini = cu_a, cu_b
        ket.update(REAL_PROVIDER_EVIDENCE="NOT_APPLICABLE_FIXTURE_DRY_RUN",
                   APPLICATION_LLM_CALLS_FIXTURE=goi_gia, APPLICATION_LLM_CALLS=0,
                   REAL_PROVIDER_CALLS=0, network_touch_attempts=list(guard.attempts))
    else:
        budget = gemini.ApiBudget(max_logical_calls=TRAN_LUOT_LOGIC)
        gemini.set_budget(budget)
        try:
            for cid, _nguon, ky_vong, mo_ta in CA_DANG_KY:
                ca_ket.append(asyncio.run(mot_ca(theo_id[cid], ky_vong, mo_ta, api_key, cv)))
        except gemini.BudgetExceeded as err:
            ket["budget_aborted"] = str(err)
        finally:
            gemini.set_budget(None)
        ket.update(REAL_PROVIDER_EVIDENCE="ESTABLISHED" if budget.http_requests else "NOT_ESTABLISHED",
                   APPLICATION_LLM_CALLS=budget.logical_calls, REAL_PROVIDER_CALLS=budget.http_requests,
                   RETRY_REQUESTS=budget.retry_requests, TRANSIENT_HITS=budget.transient_hits)

    ket["cases"] = ca_ket
    ket["SUPPORTED_CASES_BUILT"] = sum(
        1 for r in ca_ket if r["expected_outcome"] == "ACCEPT" and r.get("dat"))
    ket["SAFE_REJECTIONS"] = sum(
        1 for r in ca_ket if r["expected_outcome"].startswith("REJECT") and r.get("dat"))
    ket["SILENT_HALLUCINATION_COUNT"] = sum(1 for r in ca_ket if r.get("silent_hallucination_at_A"))
    ket["EMPTY_SCENE_COUNT"] = sum(
        1 for r in ca_ket if r["expected_outcome"] == "ACCEPT" and r.get("tang_B")
        and r["tang_B"]["status"] == "ok" and r["tang_B"]["scene_object_count"] == 0)
    ket["dat"] = all(r.get("dat") for r in ca_ket) and len(ca_ket) == len(CA_DANG_KY)
    thu_muc.mkdir(parents=True)
    (thu_muc / "RESULT.json").write_text(json.dumps(ket, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in ca_ket:
        print(f"  {r['id']:34s} {'ĐẠT' if r.get('dat') else 'KHÔNG ĐẠT'}  kỳ vọng={r['expected_outcome']}")
    print(f"{che_do} · lượt gọi ứng dụng={ket.get('APPLICATION_LLM_CALLS')} · "
          f"provider thật={ket.get('REAL_PROVIDER_CALLS')} · {'ĐẠT' if ket['dat'] else 'KHÔNG ĐẠT'}")
    print(f"→ {thu_muc / 'RESULT.json'}")
    return 0 if ket["dat"] else 1


if __name__ == "__main__":
    sys.exit(main())
