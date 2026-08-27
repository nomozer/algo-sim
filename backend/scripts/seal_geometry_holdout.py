# -*- coding: utf-8 -*-
"""Rút + NIÊM PHONG tập held-out hình học. **0 API call.**

    python scripts/seal_geometry_holdout.py --seed <SỐ CỦA GVHD>

Giao thức đầy đủ: `docs/evaluation/geometry/HOLDOUT_PROTOCOL.md`.

─── VÌ SAO SEED PHẢI ĐẾN TỪ NGƯỜI NGOÀI ────────────────────────────────────

Rút tất định từ một seed nghe rất khách quan, nhưng nếu **tôi** chọn seed thì
tôi chọn được cả tập: chạy thử vài seed rồi lấy cái cho điểm đẹp nhất. Seed do
GVHD cho là thứ duy nhất làm phép rút trở nên độc lập, và script này **không có
seed mặc định** — thiếu là dừng, không tự sinh.

─── PHÂN TẦNG THEO Ô, KHÔNG THEO TỈ LỆ ────────────────────────────────────

Bản trước rút `70% / 30%` từ hai rổ. Tỉ lệ **không** bảo đảm đa dạng: 14 bài
"trong phủ" có thể ra 14 bài thể tích, và điểm cao ấy không nói được gì.

Nên tập held-out khai **20 Ô ĐÍCH DANH** (`BANG_O`), mỗi ô một loại hình học, và
phép rút chọn **một bài cho mỗi ô**. Seed quyết định *bài nào trong ô*, không
quyết định *ô nào có mặt* — đa dạng thành tính chất của thiết kế, không phải may
rủi của seed.

Ô thiếu bài trong pool ⇒ **DỪNG**, không rút bù từ ô khác: rút bù là lặng lẽ đổi
tập đo thành tập dễ hơn.

─── TẦNG B KHÔNG PHẢI ĐỂ LẤY ĐIỂM ─────────────────────────────────────────

Sáu ô `B*` nằm NGOÀI (hoặc chỉ MỘT PHẦN trong) phủ hợp đồng. Chúng kiểm một thứ
khác hẳn: gặp đề ngoài khả năng, hệ **nói thẳng là không diễn đạt được** hay
**bịa một hình gần giống**? Hai tầng chấm bằng hai thang, không gộp.

─── CON DẤU KHOÁ CẢ HỆ THỐNG, KHÔNG CHỈ TẬP ĐỀ ────────────────────────────

Con dấu ghi thêm `measured_system_hash`. *"Không sửa hợp đồng theo từng bài"* mà
chỉ là lời hứa thì không kiểm được; ghi băm hệ vào con dấu biến nó thành thứ máy
đối chiếu được — hệ đổi sau khi niêm phong thì runner từ chối chạy.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from random import Random

GOC = Path(__file__).resolve().parents[2]
GEO = GOC / "docs" / "evaluation" / "geometry"
POOL = GEO / "holdout" / "pool.json"
SEAL = GEO / "holdout" / "HOLDOUT_SEAL.json"

#: 20 ô đích danh. `slot → (nghĩa vụ mong đợi, mô tả)`.
#:
#: Tầng A phủ **cả tám** nghĩa vụ hình học, đánh trọng số theo tần suất đề thi
#: (song song / vuông góc ba ô mỗi loại vì chúng có ba biến thể đường–đường,
#: đường–mặt, mặt–mặt — ba bài toán khác nhau chứ không phải một bài ba lần).
BANG_O: dict[str, tuple[str | None, str]] = {
    "A01": ("point_on_line", "Giao tuyến hai mặt phẳng — điểm thuộc giao tuyến"),
    "A02": ("point_on_plane", "Điểm thuộc mặt phẳng"),
    "A03": ("parallel", "Hai đường thẳng song song"),
    "A04": ("parallel", "Đường thẳng song song mặt phẳng"),
    "A05": ("parallel", "Hai mặt phẳng song song"),
    "A06": ("perpendicular", "Hai đường thẳng vuông góc"),
    "A07": ("perpendicular", "Đường thẳng vuông góc mặt phẳng"),
    "A08": ("perpendicular", "Hai mặt phẳng vuông góc"),
    "A09": ("angle", "Góc giữa hai đường thẳng"),
    "A10": ("angle", "Góc giữa đường thẳng và mặt phẳng"),
    "A11": ("distance", "Khoảng cách từ điểm đến mặt phẳng"),
    "A12": ("distance", "Khoảng cách từ điểm đến đường thẳng"),
    "A13": ("coplanar", "Thiết diện / bốn điểm đồng phẳng"),
    "A14": ("volume", "Thể tích khối chóp hoặc lăng trụ"),
    # ── NGOÀI / MỘT PHẦN trong phủ — chấm bằng thang KHÁC ────────────────
    "B01": (None, "Khoảng cách giữa hai đường thẳng chéo nhau"),
    "B02": (None, "Khoảng cách đường ∥ mặt, hoặc mặt ∥ mặt"),
    "B03": (None, "Góc nhị diện có miền (có thể tù)"),
    "B04": (None, "Oxyz: viết phương trình mặt phẳng / đường / mặt cầu"),
    "B05": (None, "Mặt cầu · mặt nón · mặt trụ"),
    "B06": (None, "Phép toán vectơ, hoặc phép chiếu song song"),
}

O_TANG_A = tuple(k for k in BANG_O if k.startswith("A"))
O_TANG_B = tuple(k for k in BANG_O if k.startswith("B"))


def _bam(x) -> str:
    """Băm NỘI DUNG, chuẩn hoá CRLF→LF.

    Cùng lý do `freeze_evaluation_candidate.bam_noi_dung`: con dấu phải giống
    nhau trên mọi máy, và Windows sẽ lặng lẽ đổi cách xuống dòng khi Git chạm
    file — làm con dấu lệch mà nội dung không đổi một chữ.
    """
    s = json.dumps(x, ensure_ascii=False, sort_keys=True).replace("\r\n", "\n")
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _bam_he_thong() -> tuple[str, int]:
    """Băm mã sản phẩm, mượn thẳng `freeze_evaluation_candidate`.

    Nạp bằng đường dẫn chứ không `import` theo tên vì `scripts/` không phải
    package — và quan trọng hơn: dùng **đúng** hàm mà cổng đóng băng dùng, để
    hai con số không bao giờ trôi khỏi nhau.
    """
    dd = Path(__file__).resolve().parent / "freeze_evaluation_candidate.py"
    spec = importlib.util.spec_from_file_location("_fz_holdout", dd)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.measured_system_hash()


def _chuan_de(s: str) -> str:
    """Gom khoảng trắng + bỏ hoa/thường, để so hai bản chép cùng một đề."""
    return " ".join(str(s).split()).lower()


def _de_cua_dev() -> set[str]:
    f = GEO / "dev" / "cases.json"
    if not f.exists():
        return set()
    return {_chuan_de(c["problem_text"])
            for c in json.loads(f.read_text(encoding="utf-8"))["cases"]}


def kiem_pool(cases: list[dict]) -> list[str]:
    """Trả danh sách lỗi. Rỗng ⇒ pool hợp lệ.

    Kiểm ở đây chứ không ở lúc chạy: một bài thiếu `nguon` phát hiện sau khi đã
    niêm phong thì **không sửa được nữa** mà không phá con dấu.
    """
    loi: list[str] = []
    dev = _de_cua_dev()
    for i, c in enumerate(cases):
        cid = c.get("case_id") or f"#{i}"
        o = c.get("slot")
        if _chuan_de(c.get("problem_text") or "") in dev:
            # Bốn wave đã sửa hệ theo đúng những đề này. Để lọt một bài DEV vào
            # held-out là tự cho điểm ở chỗ mình đã ôn.
            loi.append(f"{cid}: đề TRÙNG tập DEV — held-out không được chứa DEV")
        if o not in BANG_O:
            loi.append(f"{cid}: slot {o!r} không có trong BANG_O")
            continue
        for truong in ("problem_text", "nguon", "dap_an_chinh_thuc"):
            if not c.get(truong):
                loi.append(f"{cid}: thiếu {truong}")
        if not (c.get("nguon") or {}).get("url"):
            loi.append(f"{cid}: nguồn không có url — không tra ngược được")
        if c.get("chua_chay_he") is not True:
            # Soạn đáp án SAU khi thấy hệ chạy là chép bài của chính mình.
            loi.append(f"{cid}: chua_chay_he phải là true tại thời điểm soạn")
        if c.get("can_kiem_tay") is True:
            # NỢ ĐỐI CHIẾU, thêm 2026-08-27. Đề thu thập bằng công cụ đọc web
            # đi qua một mô hình tóm tắt, nên `problem_text` là bản chép LẠI
            # chứ không phải chép NGUYÊN VĂN — mà giao thức đòi nguyên văn, và
            # một chữ sai trong đề làm bài toán thành bài khác.
            #
            # Cờ mặc định VẮNG MẶT ⇒ không ảnh hưởng bài soạn tay. Chỉ bài nào
            # TỰ KHAI còn nợ mới bị chặn, và cách trả nợ là mở url đối chiếu
            # bằng mắt rồi xoá cờ — không phải xoá cờ rồi thôi.
            loi.append(f"{cid}: can_kiem_tay còn true — chưa ai đối chiếu "
                       f"problem_text với nguồn. Niêm phong một đề chép sai là "
                       f"niêm phong một bài toán KHÁC.")
        if o.startswith("A"):
            mong = BANG_O[o][0]
            if mong not in (c.get("expected_obligations") or []):
                loi.append(f"{cid}: ô {o} đòi nghĩa vụ {mong!r}")
            if not c.get("oracle_result"):
                loi.append(f"{cid}: tầng A phải có oracle_result")
            if not c.get("phep_chuyen"):
                # Đáp án chính thức viết `a√3/3`; checker so phân số. Phép
                # chuyển phải HIỆN RA để người khác kiểm được — giấu nó đi thì
                # "oracle độc lập" chỉ còn là lời khai.
                loi.append(f"{cid}: tầng A phải ghi phep_chuyen")
        else:
            if c.get("oracle_result"):
                loi.append(f"{cid}: ô {o} NGOÀI phủ — không được có oracle_result "
                           f"(chấm bằng 'từ chối trung thực', không bằng đáp án)")
            if not c.get("ly_do_ngoai_phu"):
                loi.append(f"{cid}: thiếu ly_do_ngoai_phu")
    return loi


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, required=True,
                   help="SỐ NGUYÊN DO GVHD CHO. Không có mặc định — cố ý.")
    p.add_argument("--chi-kiem-pool", action="store_true",
                   help="Chỉ soi pool rồi thoát, KHÔNG niêm phong.")
    a = p.parse_args()

    if not POOL.exists():
        print(f"Chưa có pool: {POOL}")
        print("Soạn pool trước — xem HOLDOUT_PROTOCOL.md §3①. Pool phải trích")
        print("từ NGUỒN CÔNG KHAI và mang ĐÁP ÁN CHÍNH THỨC, không phải đáp án")
        print("do hệ tính ra.")
        return 2

    cases = json.loads(POOL.read_text(encoding="utf-8"))["cases"]
    if loi := kiem_pool(cases):
        print(f"POOL KHÔNG HỢP LỆ — {len(loi)} lỗi:")
        for d in loi[:40]:
            print("  ·", d)
        return 2

    theo_o: dict[str, list[dict]] = {}
    for c in cases:
        theo_o.setdefault(c["slot"], []).append(c)
    thieu = [o for o in BANG_O if not theo_o.get(o)]
    if thieu:
        print(f"Pool KHÔNG phủ {len(thieu)}/20 ô: {thieu}")
        print("KHÔNG rút bù từ ô khác — rút bù là lặng lẽ đổi tập đo.")
        return 2

    if a.chi_kiem_pool:
        print(f"Pool hợp lệ · {len(cases)} bài · phủ đủ 20/20 ô")
        for o in BANG_O:
            print(f"  {o}  {len(theo_o[o]):>2} bài   {BANG_O[o][1]}")
        return 0

    if SEAL.exists():
        # Niêm phong lại là làm hỏng chính thứ con dấu bảo đảm. Muốn đổi tập
        # thì phải nói ra, không được lặng lẽ ghi đè.
        print(f"ĐÃ NIÊM PHONG rồi: {SEAL}")
        print("Rút lại tập held-out sau khi đã thấy kết quả là VI PHẠM giao thức.")
        return 1

    # Một Random RIÊNG cho mỗi ô, gieo từ (seed, tên ô): thêm bài vào ô A11
    # không được làm đổi bài đã rút ở ô A12. Một Random dùng chung thì thứ tự
    # tiêu số làm mọi ô sau nó trượt hết.
    chon = [Random(f"{a.seed}:{o}").choice(sorted(theo_o[o],
                                                  key=lambda c: c["case_id"]))
            for o in BANG_O]

    he_hash, he_so_file = _bam_he_thong()
    seal = {
        "khai": "Tập HELD-OUT đã niêm phong. Chạy MỘT LƯỢT. Sửa hệ rồi chạy "
                "lại trên chính tập này thì nó THÀNH DEV — và phải nói ra.",
        "seed": a.seed,
        "nguon_seed": "GVHD",
        "niem_phong_luc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pool_hash": _bam(cases),
        "pool_size": len(cases),
        "n": len(chon),
        "o_tang_a": len(O_TANG_A),
        "o_tang_b": len(O_TANG_B),
        # Băm hệ ĐANG được đo, để lượt chạy sau chứng minh được là cùng một hệ.
        "measured_system_hash": he_hash,
        "measured_system_files": he_so_file,
        "case_ids": [c["case_id"] for c in chon],
        "theo_o": {c["slot"]: c["case_id"] for c in chon},
        "seal_hash": _bam(chon),
    }
    SEAL.parent.mkdir(parents=True, exist_ok=True)
    SEAL.write_text(json.dumps(seal, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    (SEAL.parent / "cases.json").write_text(
        json.dumps({"khai": seal["khai"], "seal_hash": seal["seal_hash"],
                    "cases": chon}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    print(f"Đã niêm phong {len(chon)} bài · seed {a.seed}")
    print(f"  seal_hash  {seal['seal_hash'][:16]}…")
    print(f"  hệ đo      {he_hash[:16]}… ({he_so_file} file)")
    for o in BANG_O:
        print(f"  {o}  {seal['theo_o'][o]}")
    print("\nBƯỚC TIẾP: COMMIT con dấu TRƯỚC khi chạy. Không có con dấu trong")
    print("lịch sử thì không chứng minh được tập không bị sửa sau khi thấy kết quả.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
