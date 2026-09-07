# -*- coding: utf-8 -*-
"""§11 — replay NGUYÊN BYTE ba ứng viên của wave elip, 0 lượt gọi model.

Câu hỏi đo: **phép dựng mới có làm ứng viên mà mô hình ĐÃ VIẾT chạy được
không** — không phải *"mô hình có viết lại được không"*, đó là câu của một lượt
live khác.

─── VÌ SAO ĐỌC RAW CHỨ KHÔNG ĐỌC `semantic_program_cuoi` ──────────────────

`ung_vien_tho[i]["raw"]` là **chuỗi mô hình trả về**, chưa qua một phép chuẩn
hoá nào của hệ. Đọc bản đã chuẩn hoá thì mọi kết luận về *"ứng viên có hợp lệ
không"* sẽ đo phép chuẩn hoá thay vì đo ứng viên.

─── HỢP ĐỒNG DỰNG LẠI TỪ RAW ANALYZE, KHÔNG DÙNG GOLD ────────────────────

Ứng viên được viết dưới hợp đồng do `analyze` THẬT phát ra, nên phải chấm dưới
đúng hợp đồng ấy. Dùng `REQUEST_CONTRACT_GOLD` sẽ là chấm ứng viên của mô hình
bằng một đề khác — hợp đồng gold có `fact_id` khác (`tam_day_duoi` vs
`tam_day_duoi_O`), và mọi `source_fact_id` của mô hình sẽ trượt.

Artifact nguồn BẤT BIẾN: script chỉ đọc, và ghi kết quả sang file riêng.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
for _p in (str(BACKEND), str(BACKEND / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.simulation.geometry.radical import display, is_exact_number  # noqa: E402
from app.simulation.semantic_program.analyze_contract import (  # noqa: E402
    build_request_contract,
)
from app.simulation.semantic_program.contract import (  # noqa: E402
    SemanticProgramSpec,
)
from app.simulation.semantic_program.domain_profile import (  # noqa: E402
    DOMAIN_HINH_HOC,
)
from app.simulation.semantic_program.ir_static_check import (  # noqa: E402
    kiem_tinh,
)
from app.simulation.semantic_program.route import verify_and_compile  # noqa: E402

from gold_oblique_ellipse_fresh import (  # noqa: E402
    CONTAINER, PROBLEM_TEXT, WITNESS,
)

ART = (BACKEND.parent / "docs" / "evaluation" / "geometry"
       / "oblique-ellipse-fresh-confirmation"
       / "e2e_oblique-ellipse-after-scope-repair-20260907T050244Z.json")

#: Đáp số đúng, viết theo cách `radical.display` in ra.
DAP_SO = "16π√5"


def _bam(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def nap() -> tuple[list[str], str]:
    d = json.loads(ART.read_text(encoding="utf-8"))
    tho = [u["raw"] for u in d["ung_vien_tho"]]
    phan_tich = d["raw_theo_tang"]["semantic_analyze"][0]
    return tho, phan_tich


def hop_dong(raw_analyze: str):
    """Hợp đồng của LƯỢT CHẠY THẬT, dựng lại từ raw `analyze`.

    Đi qua `build_request_contract` với `domain="hinh_hoc"` nên nó cũng phát
    `SourceInvariant` y như đường sản phẩm — gồm bất biến `plane_equation` mà
    wave này thêm. Đó là điểm chính: ứng viên được chấm dưới **đúng bộ luật
    hôm nay**, không phải dưới một hợp đồng dựng tay cho dễ.
    """
    return build_request_contract(
        json.loads(raw_analyze), PROBLEM_TEXT, DOMAIN_HINH_HOC)


def cham(raw: str, hd) -> dict:
    """Một ứng viên → mười chiều của §11. Không ném: mọi hỏng đều là dữ liệu."""
    ra: dict[str, object] = {
        "SCHEMA_VALID": False, "STATIC_VALID": "NOT_REACHED",
        "GROUNDING_PASS": "NOT_REACHED", "SOURCE_INVARIANT": "NOT_REACHED",
        "RUNTIME": "NOT_REACHED", "EXACT_AREA": "NOT_REACHED",
        "POSTCONDITIONS": "NOT_REACHED", "TRACE": "NOT_REACHED",
        "SCENE3D": "NOT_REACHED", "SERVABLE": False,
        "stage": None, "error_code": None, "chi_tiet": None,
    }
    try:
        spec = SemanticProgramSpec.model_validate(json.loads(raw))
    except Exception as e:  # noqa: BLE001 — mọi lỗi lược đồ đều là kết quả
        ra["stage"] = "schema"
        ra["chi_tiet"] = str(e).splitlines()[0][:200]
        return ra
    ra["SCHEMA_VALID"] = True

    # ⚠️ HỎI `ir_static` RIÊNG, không đọc nó qua `verify_and_compile`.
    # `verify_and_compile` chạy grounding TRƯỚC, nên một ứng viên chết ở
    # grounding sẽ để `STATIC_VALID = NOT_REACHED` — và với wave này đó đúng là
    # ô người đọc tới để xem, vì tầng phép mới gỡ tắc CHÍNH LÀ `ir_static`.
    # Báo `NOT_REACHED` cho thứ đo được là giấu kết quả sau một thứ tự gọi.
    tinh = kiem_tinh(spec)
    ra["STATIC_VALID"] = "PASS" if tinh.ok else "FAIL"
    ra["static_issues"] = [f"{i.error_code}: {i.object_id} — {i.actual}"
                           for i in tinh.issues]

    kq = verify_and_compile(hd, spec)
    ra["SERVABLE"] = bool(kq.servable)
    ra["error_code"] = kq.error_code
    ra["stage"] = kq.stage_reached
    nguon = kq.source_invariant_stats or {}
    ra["SOURCE_INVARIANT"] = (
        f"checked={nguon.get('checked', 0)} passed={nguon.get('passed', 0)} "
        f"violated={nguon.get('violated', 0)}" if nguon else "NOT_REACHED")

    dl = {k: display(x) for k, x in (kq.final_memory or {}).items()
          if is_exact_number(x)}
    if kq.servable:
        ra["GROUNDING_PASS"] = "PASS"
        ra["RUNTIME"] = ra["POSTCONDITIONS"] = "PASS"
        ra["EXACT_AREA"] = dl.get(WITNESS, "KHÔNG CÓ")
    else:
        ra["chi_tiet"] = str(kq.reason or kq.details or "")[:260]
    return ra


def canh_va_trace(raw: str, hd) -> dict:
    """Trace + Scene3D — chỉ hỏi khi ứng viên đã `servable`."""
    from app.ai.pipeline import _dung_scene3d

    spec = SemanticProgramSpec.model_validate(json.loads(raw))
    canh = _dung_scene3d(spec, hd) or {}
    vat = {str(o.get("id")): o for o in canh.get("objects", [])}
    mp = [o for o in vat.values() if o.get("type") == "plane3"]
    # TRACE — §10 đòi ĐÚNG MỘT bước dựng cho câu lệnh mặt phẳng, và lời kể
    # của nó phải nói phương trình chứ không nói điểm neo canonical (điểm ấy
    # là chi tiết thực thi, không phải một điểm hình học của đề).
    su_kien = canh.get("events", [])
    buoc_mp = [e for e in su_kien
               if e.get("object") in {o["id"] for o in mp}]
    ke = " ".join(str(e.get("explanation") or "") for e in buoc_mp)
    return {
        "SCENE3D": "PASS" if vat else "FAIL",
        # `"-5" not in ke` — điểm neo canonical KHÔNG được lọt vào lời kể.
        # Nó là chi tiết thực thi, và gọi tên nó cho học sinh là dạy một điểm
        # hình học mà đề không có.
        "TRACE": ("PASS" if len(buoc_mp) == 1 and "phương trình" in ke
                  and "-5" not in ke else "FAIL"),
        "action_buoc_mat_phang": [e.get("action") for e in buoc_mp],
        "depends_buoc_mat_phang": [e.get("depends") for e in buoc_mp],
        "buoc_dung_mat_phang": len(buoc_mp),
        "loi_ke_mat_phang": ke,
        "so_vat": len(vat),
        "so_su_kien": len(su_kien),
        "mat_phang_trong_canh": [
            {"id": o["id"], "point": o.get("point"), "normal": o.get("normal"),
             "role": o.get("role"), "producer": o.get("producer")}
            for o in mp],
        "co_elip": any(o.get("type") == "ellipse3" for o in vat.values()),
    }


def minimal_delta(raw: str) -> tuple[str, list[str]]:
    """Bản sửa NHỎ NHẤT làm ứng viên attempt 1 đi trọn đường — và nó KHÔNG
    chạm mặt phẳng.

    ⚠️ Đọc kỹ chỗ này trước khi trích số. Sau khi thêm phép dựng, ứng viên
    attempt 1 qua `ir_static` nhưng vẫn chết ở `grounding` vì một chỗ **khác
    hẳn**, có sẵn từ trước và không liên quan tới wave: mô hình bịa một điểm
    vành `P_rim = [4,0,0]` cho hình trụ, khai bằng `model_assumption`.

    Đó đúng lớp lỗi mà `ConstructCurvedSolidStmt` đã ghi (`curved-acceptance`,
    ca `ball_2`) và đã có đường đi đúng: ô `radius` nhận TÊN một vô hướng.
    Mô hình **đã khai sẵn** `R` với `source_fact_id: "ban_kinh_day"` rồi dùng
    nó cho... không gì cả — nó khai `R` xong vẫn bịa thêm một điểm vành.

    Nên delta là: bỏ khai báo `P_rim`, đổi `rim_point: "P_rim"` →
    `radius: "R"`. **Hai trường, không đụng một byte nào của câu lệnh mặt
    phẳng** — và đó chính là điều làm phép đo này nói được điều nó nói.
    """
    o = json.loads(raw)
    ly_do: list[str] = []
    o["memory_declarations"] = [
        d for d in o["memory_declarations"] if d.get("name") != "P_rim"]
    ly_do.append("bỏ khai báo `P_rim` — điểm vành mô hình tự bịa, "
                 "`model_assumption` không neo được nó về đề")
    for st in o["statements"]:
        if st.get("kind") == "construct_curved_solid":
            st.pop("rim_point", None)
            st["radius"] = "R"
            ly_do.append("`rim_point: \"P_rim\"` → `radius: \"R\"` — `R` đã "
                         "được CHÍNH mô hình khai với `source_fact_id: "
                         "\"ban_kinh_day\"`")
    return json.dumps(o, ensure_ascii=False, indent=2), ly_do


def main() -> int:
    tho, phan_tich = nap()
    hd = hop_dong(phan_tich)
    bb = [{"kind": b.kind, "coefficients": list(b.coefficients),
           "source_text": b.source_text, "source_fact_id": b.source_fact_id}
          for b in (hd.source_invariants or ())]

    ra = {
        "khai": "Replay NGUYÊN BYTE, 0 lượt gọi model.",
        "wave": "PLANE_FROM_EQUATION_REPRESENTATION",
        "artifact_nguon": ART.name,
        "sha256_artifact": _bam(ART.read_text(encoding="utf-8")),
        "source_invariants_phat_ra": bb,
        "attempts": [],
    }
    for i, raw in enumerate(tho):
        muc = {"attempt": i, "raw_sha256": _bam(raw),
               "raw_bytes": len(raw.encode("utf-8")),
               "kinds": [s.get("kind") for s
                         in json.loads(raw).get("statements", [])]}
        muc.update(cham(raw, hd))
        if muc["SERVABLE"]:
            muc.update(canh_va_trace(raw, hd))
        ra["attempts"].append(muc)

    # ─── MINIMAL DELTA cho attempt 1 ─────────────────────────────────────
    delta, ly_do = minimal_delta(tho[1])
    goc = json.loads(tho[1])
    md = {"nguon": "attempt 1", "so_truong_doi": 2, "ly_do": ly_do,
          "byte_goc": len(tho[1].encode("utf-8")),
          "byte_delta": len(delta.encode("utf-8")),
          "cau_lenh_mat_phang_KHONG_DOI": (
              [s for s in goc["statements"]
               if s.get("kind") == "construct_plane_from_equation"]
              == [s for s in json.loads(delta)["statements"]
                  if s.get("kind") == "construct_plane_from_equation"])}
    md.update(cham(delta, hd))
    if md["SERVABLE"]:
        md.update(canh_va_trace(delta, hd))
        md["DAP_SO_DUNG"] = md["EXACT_AREA"] == DAP_SO
    ra["minimal_delta"] = md

    print(json.dumps(ra, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
