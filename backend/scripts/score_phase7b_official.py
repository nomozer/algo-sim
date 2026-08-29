# -*- coding: utf-8 -*-
"""PHASE 7B — CHẤM lượt chính thức. **0 API call.**

    python scripts/score_phase7b_official.py [--md docs/.../PHASE7B_OFFICIAL_RESULT.md]

Đọc artifact đã ghi, chấm bằng **kỳ vọng + hợp đồng metric đã đóng băng**.
Không gọi model, không đọc lại đề, không đổi định nghĩa chỉ số.

─── MỖI CHỈ SỐ MỘT MẪU SỐ, KHÔNG ÉP VỀ MẪU CHUNG ─────────────────────────

`PHASE7_METRIC_CONTRACT §4` cấm gộp `None` vào `False` và cấm gộp ③a với ③b.
Lý do không phải thẩm mỹ: `construction_match = None` nghĩa *đề không ra
lệnh dựng gì*, còn `False` nghĩa *đề ra lệnh mà chương trình không dựng*.
Ép chúng về một mẫu số thì mọi bài "chỉ tính, không dựng" bị đếm thành lỗi,
và con số đi ra **thấp hơn thực tế** ở đúng chỗ hệ không hề sai.

Nên mọi chỉ số ở đây báo bốn số TRƯỚC tỉ lệ: tử · mẫu áp dụng · N/A · trượt.

─── HAI TẬP, VÀ VÌ SAO PHẢI CÓ CẢ HAI ────────────────────────────────────

`ALL_20` và `PUBLIC_SOURCE_19` (bỏ ô A12 — bài `curated_preseal`). Một bài
tự soạn nằm lẫn trong 20 mà không tách ra thì nó lặng lẽ thổi phồng đúng cái
tuyên bố *"đề từ nguồn ngoài"*. Cả hai đều là 20/20 ô về ĐỘ PHỦ; chỉ khác ở
chỗ 19 bài kia có nguồn công khai tra ngược được.

⚠️ **KHÔNG** gọi 19/20 là *"held-out thật"*: cả 20 bài đều chưa từng đi qua
hệ, và tính held-out không mất đi vì một bài do người đo soạn — cái mất là
tính *độc lập của nguồn đề*, một tính chất khác.

─── KHÔNG BỊA NGƯỠNG SAU KHI THẤY SỐ ─────────────────────────────────────

Đã soát `PHASE7_METRIC_CONTRACT`, `HOLDOUT_PROTOCOL`, `HOLDOUT_K_FINAL`:
**không có ngưỡng chấp nhận số nào được đăng ký trước**. Nên file này không
in `PASS`/`FAIL` cho câu hỏi nghiên cứu. Nó in
`EVIDENCE_SUPPORTS_3D_NEXT ∈ {STRONG, MIXED, WEAK}` và **tự khai đó là diễn
giải**, không phải một phép kiểm giả thuyết đã đăng ký.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
GEO = ROOT / "docs" / "evaluation" / "geometry"
RA = GEO / "phase7b-official"


def _tap(rs: list[dict], khoa: str) -> dict:
    """Bốn con số TRƯỚC tỉ lệ. `None` là hạng riêng, không phải `False`."""
    v = [r.get(khoa) for r in rs]
    dat = sum(1 for x in v if x is True)
    truot = sum(1 for x in v if x is False)
    na = sum(1 for x in v if x is None)
    return {"tu_so": dat, "mau_ap_dung": dat + truot, "na": na,
            "truot": truot, "tong_luot": len(v)}


def _dong(ten: str, d: dict) -> str:
    m = d["mau_ap_dung"]
    ti = f" ({d['tu_so'] / m:.0%})" if m >= 20 else "  ⟨mẫu <20 ⇒ ĐẾM THÔ⟩"
    return (f"{ten:<20} {d['tu_so']}/{m} áp dụng · N/A={d['na']} · "
            f"trượt={d['truot']}{ti}")


def _on_dinh(rs: list[dict], ids: list[str], k: int) -> dict:
    """⑤ — `x/k` mỗi bài, KHÔNG phải pass/fail, kèm phân bố."""
    theo = {}
    for cid in ids:
        x = [r for r in rs if r["case_id"] == cid]
        theo[cid] = {
            "so_luot": len(x),
            "served": sum(1 for r in x if r.get("servable")),
            "oracle": sum(1 for r in x if r.get("oracle_dat") is True),
            "verification": sum(1 for r in x if r.get("verification_match")),
            "construction": sum(1 for r in x if r.get("construction_match")),
            "so_nghia_vu": sorted({r.get("so_nghia_vu") for r in x}),
            "stage": sorted({str(r.get("stage_reached")) for r in x}),
        }
    # Bài ỔN ĐỊNH = ba lượt cho CÙNG kết cục trên cả bốn trục.
    on = [c for c, v in theo.items()
          if v["so_luot"] == k
          and v["served"] in (0, k) and v["oracle"] in (0, k)
          and v["verification"] in (0, k) and v["construction"] in (0, k)
          and len(v["so_nghia_vu"]) == 1]
    return {"theo_bai": theo, "on_dinh": on,
            "tu_so": len(on), "mau_ap_dung": len(ids)}


def _tang_b(rs: list[dict], ids: set[str]) -> dict:
    """Tầng B chấm NHỊ PHÂN: *từ chối trung thực* | *bịa hình*.

    `HOLDOUT_PROTOCOL §3`: **"Hai thang không được gộp thành một cột."** Bản
    chấm đầu vi phạm đúng câu ấy — nó đọc `servable = False` của sáu ô B như
    38 lượt TRƯỢT, trong khi ở tầng B `servable = False` chính là **kết cục
    đúng**: đề nằm ngoài khả năng, và hệ nói ra điều đó.

    Ba trạng thái, không phải hai. `EXCEPTION` không nằm ở đâu trong hai
    trạng thái của giao thức: hệ **ném lỗi** chứ không *nói* là không diễn
    đạt được. Nhét nó vào "từ chối trung thực" là khen một cú sập; nhét vào
    "bịa hình" là kết tội sai. Nên nó có ô riêng, và ô ấy phải nhìn thấy được.
    """
    x = [r for r in rs if r["case_id"] in ids]
    tu_choi = [r for r in x if r.get("servable") is False
               and r.get("envelope_status") != "EXCEPTION"]
    bia = [r for r in x if r.get("servable") is True]
    su_co = [r for r in x if r.get("envelope_status") == "EXCEPTION"
             or (r.get("servable") is None
                 and r.get("envelope_status") != "EXCEPTION")]
    return {"tu_choi_trung_thuc": len(tu_choi), "bia_hinh": len(bia),
            "su_co_khong_khai": len(su_co), "tong_luot": len(x),
            "chi_tiet_bia": [f"{r['case_id']}-lan{r.get('replicate_index')}"
                             for r in bia],
            "chi_tiet_su_co": [f"{r['case_id']}-lan{r.get('replicate_index')}"
                               for r in su_co]}


#: Sáu nhóm của §18. Ánh xạ từ `stage_reached`/`error_code`/`failure_category`
#: — KHÔNG suy từ điểm số, vì một bài trượt oracle có thể trượt vì bất kỳ
#: nhóm nào và gán bừa là làm hỏng đúng thứ quyết định wave sau.
def _taxonomy(rs: list[dict], tang_b: set[str]) -> dict:
    d: Counter = Counter()
    chi_tiet: dict[str, list[str]] = {}

    def ghi(nhom: str, r: dict, vi_sao: str) -> None:
        d[nhom] += 1
        chi_tiet.setdefault(nhom, []).append(
            f"{r['case_id']}-lan{r.get('replicate_index')}: {vi_sao}")

    for r in rs:
        st, ec = str(r.get("stage_reached")), str(r.get("error_code") or "")
        if r.get("budget_aborted"):
            ghi("F_transport_provider", r, "chạm trần ngân sách lượt")
        elif r["case_id"] in tang_b:
            # TẦNG B: không-served là KẾT CỤC ĐÚNG, không phải lỗi. Bản chấm
            # đầu xếp 38 lượt B vào `A_llm_synthesis` — kết tội mô hình ở
            # đúng chỗ nó làm đúng, đúng lớp sai lệch mà
            # `METRIC_CONTRACT §3` đã ghi là đã xảy ra một lần (Phase 6.7).
            if r.get("envelope_status") == "EXCEPTION":
                ghi("E_metric_tooling", r,
                    "ngoài phủ mà NÉM LỖI thay vì nói không diễn đạt được")
            elif r.get("servable"):
                ghi("A_llm_synthesis", r, "BỊA HÌNH cho đề ngoài phủ")
            else:
                ghi("C_capability_refusal", r, f"từ chối đúng ({st})")
        elif r.get("envelope_status") == "EXCEPTION":
            ghi("D_deterministic_exec", r, str(r.get("reason") or st)[:80])
        elif not r.get("servable"):
            if st == "grounding":
                ghi("B_grounding", r, "dừng ở grounding")
            elif "SCHEMA" in ec or "VALIDATION" in ec:
                ghi("A_llm_synthesis", r, f"schema/validation: {ec}")
            elif st in ("routing", "classify"):
                ghi("A_llm_synthesis", r, f"không tới được route sinh ({st})")
            elif r.get("failure_category"):
                ghi("A_llm_synthesis", r, str(r["failure_category"]))
            else:
                ghi("D_deterministic_exec", r, f"{st} · {ec}")
        elif r.get("oracle_dat") is False:
            ghi("A_llm_synthesis", r, f"oracle sai: {str(r.get('oracle_vi_sao'))[:70]}")
        elif r.get("oracle_dat") is None and r.get("servable"):
            ghi("E_metric_tooling", r,
                f"không chấm được: {str(r.get('oracle_vi_sao'))[:70]}")
    return {"dem": dict(d.most_common()), "chi_tiet": chi_tiet}


def cham(rs: list[dict], cases: list[dict], k: int) -> dict:
    ids = [c["case_id"] for c in cases]
    tu_soan = {c["case_id"] for c in cases if c.get("curated_preseal")}
    cong_khai = [c for c in cases if c["case_id"] not in tu_soan]

    tang_b = {c["case_id"] for c in cases if str(c["slot"]).startswith("B")}
    tang_a = {c["case_id"] for c in cases if str(c["slot"]).startswith("A")}

    def bo(tap_ids: set[str]) -> dict:
        x = [r for r in rs if r["case_id"] in tap_ids]
        return {
            "so_luot": len(x),
            "served": _tap(x, "servable"),
            "oracle": _tap(x, "oracle_dat"),
            "construction_match": _tap(x, "construction_match"),
            "verification_match": _tap(x, "verification_match"),
            "stability": _on_dinh(x, sorted(tap_ids), k),
        }

    return {
        # HAI THANG, KHÔNG GỘP (`HOLDOUT_PROTOCOL §3`). Tầng A chấm A·O·③;
        # tầng B chấm nhị phân từ-chối-trung-thực. Gộp chúng vào một cột
        # `served` là đọc 18 lượt TỪ CHỐI ĐÚNG thành 18 lượt trượt.
        "TIER_A_14": bo(tang_a),
        "TIER_A_14_PUBLIC_13": bo(tang_a - tu_soan),
        "TIER_B_6": _tang_b(rs, tang_b),
        "ALL_20_gop_de_tham_khao": bo(set(ids)),
        "PUBLIC_SOURCE_19": bo({c["case_id"] for c in cong_khai}),
        "CURATED_PRESEAL": sorted(tu_soan),
        "taxonomy": _taxonomy(rs, tang_b),
        "chi_phi": {
            "logical_calls": sum(r.get("logical_calls") or 0 for r in rs),
            "http_requests": sum(r.get("http_requests") or 0 for r in rs),
            "retry_requests": sum(r.get("retry_requests") or 0 for r in rs),
            "transient_hits": sum(r.get("transient_hits") or 0 for r in rs),
        },
    }


def hoan_chinh(rs: list[dict], ids: list[str], k: int) -> list[str]:
    """§12 — kiểm TRỌN VẸN trước khi chấm. Thiếu mà vẫn chấm là báo một tỉ lệ
    trên mẫu số ngầm nhỏ hơn mẫu số đã đăng ký."""
    loi = []
    dem = Counter(r["case_id"] for r in rs)
    for cid in ids:
        if dem[cid] != k:
            loi.append(f"{cid}: {dem[cid]}/{k} lượt")
    thua = set(dem) - set(ids)
    if thua:
        loi.append(f"bản ghi LẠ không thuộc tập niêm phong: {sorted(thua)}")
    cap = Counter((r["case_id"], r.get("replicate_index")) for r in rs)
    if trung := [c for c, n in cap.items() if n > 1]:
        loi.append(f"TRÙNG lượt: {trung}")
    tl = sum(r.get("logical_calls") or 0 for r in rs)
    th = sum(r.get("http_requests") or 0 for r in rs)
    if tl > 360:
        loi.append(f"VƯỢT trần logic: {tl}/360")
    if th > 480:
        loi.append(f"VƯỢT trần HTTP: {th}/480")
    return loi


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--md", default=None)
    p.add_argument("--in-dir", default=None)
    a = p.parse_args()
    ra = Path(a.in_dir) if a.in_dir else RA

    seal = json.loads((GEO / "holdout" / "HOLDOUT_SEAL.json").read_text(encoding="utf-8"))
    cj = json.loads((GEO / "holdout" / "cases.json").read_text(encoding="utf-8"))
    cases = cj["cases"] if isinstance(cj, dict) else cj
    k = seal["k"]
    rs = [json.loads(f.read_text(encoding="utf-8"))["ban_ghi"]
          for f in sorted(ra.glob("*-lan*.json"))]
    if not rs:
        print(f"Chưa có bản ghi nào ở {ra}")
        return 1

    ids = [c["case_id"] for c in cases]
    thieu = hoan_chinh(rs, ids, k)
    print(f"RUN_COMPLETENESS: {'FAIL' if thieu else 'PASS'}")
    for x in thieu:
        print("  ⛔", x)
    print()

    r = cham(rs, cases, k)
    b = r["TIER_B_6"]
    print(f"── TIER_B_6 · {b['tong_luot']} lượt · thang TỪ CHỐI TRUNG THỰC ──")
    print(f"  từ chối trung thực   {b['tu_choi_trung_thuc']}/{b['tong_luot']}")
    print(f"  BỊA HÌNH             {b['bia_hinh']}/{b['tong_luot']}"
          + (f"  {b['chi_tiet_bia']}" if b['bia_hinh'] else ""))
    print(f"  sự cố (ném lỗi)      {b['su_co_khong_khai']}/{b['tong_luot']}"
          + (f"  {b['chi_tiet_su_co']}" if b['su_co_khong_khai'] else ""))
    print()
    for ten in ("TIER_A_14", "TIER_A_14_PUBLIC_13", "ALL_20_gop_de_tham_khao"):
        b = r[ten]
        print(f"── {ten} · {b['so_luot']} lượt ──")
        for m in ("served", "oracle", "construction_match", "verification_match"):
            print("  " + _dong(m, b[m]))
        s = b["stability"]
        print(f"  {'stability':<20} {s['tu_so']}/{s['mau_ap_dung']} bài "
              f"ỔN ĐỊNH trên cả {k} lượt")
        print()

    print("── ỔN ĐỊNH TỪNG BÀI (không trung bình hoá bất đồng) ──")
    ad = r["ALL_20_gop_de_tham_khao"]["stability"]
    for cid, v in ad["theo_bai"].items():
        cd = "  " if cid in ad["on_dinh"] else "⚠️"
        print(f"  {cd} {cid:<14} served={v['served']}/{v['so_luot']} "
              f"oracle={v['oracle']}/{v['so_luot']} "
              f"kiểm={v['verification']}/{v['so_luot']} "
              f"dựng={v['construction']}/{v['so_luot']} "
              f"nv={v['so_nghia_vu']} stage={v['stage']}")
    print()
    print("── TAXONOMY (§18) ──")
    for nhom, n in r["taxonomy"]["dem"].items():
        print(f"  {nhom:<24} {n}")
    print()
    cp = r["chi_phi"]
    print(f"CHI PHÍ: {cp['logical_calls']}/360 logic · "
          f"{cp['http_requests']}/480 HTTP · retry={cp['retry_requests']} "
          f"· transient={cp['transient_hits']}")

    if a.md:
        f = Path(a.md) if Path(a.md).is_absolute() else ROOT / a.md
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(
            {"seal": {k2: seal[k2] for k2 in
                      ("seed", "seal_hash", "measured_system_hash",
                       "expectation_hash", "k", "nguon_seed")},
             "run_completeness": "FAIL" if thieu else "PASS",
             "thieu": thieu, **r},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nĐã ghi {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
