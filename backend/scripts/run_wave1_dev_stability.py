# -*- coding: utf-8 -*-
"""WAVE 1 sau Phase 7B — ĐO ỔN ĐỊNH TRÊN DEV. **TIÊU QUOTA THẬT.**

    ALLOW_LIVE_AI=1 python scripts/run_wave1_dev_stability.py --k 3

Ba đề DEV **mới**, viết cho đúng hai họ mà wave này vừa sửa, cộng năm đề
pilot đã đăng ký để thấy phép sửa không làm hỏng thứ đang chạy được.

─── ĐỀ Ở ĐÂY LÀ DEV, KHÔNG PHẢI HELD-OUT ─────────────────────────────────

Taxonomy của lượt chính thức chỉ **dẫn đường** (*"họ GÓC hỏng"*, *"grounding
6 lượt"*). Ba đề dưới đây do wave này viết ra: khác số, khác cách hỏi, khác
khối. Lấy chính 20 đề held-out làm ca sửa thì tập đo biến thành tập DEV
không hoàn tác được — `test_phase7b_baseline_immutable` khoá điều đó.

─── VÌ SAO ĐÚNG BA ĐỀ NÀY ────────────────────────────────────────────────

`w1-goc-dd`  góc đường–đường trên hình lập phương. Trước phép sửa, đề dạng
             này chết ở cổng phạm vi vì `hình lập phương` không nằm trong
             cụm MẠNH và đề quá ngắn để gom đủ ba cụm yếu.

`w1-goc-dm`  góc đường–MẶT, cùng khối. Tách khỏi đề trên có chủ đích: đơn vị
             checker là **sin²**, không phải cos², và một đề 45° sẽ không
             phân biệt được hai quy ước. Chọn góc mà hai quy ước cho hai số
             khác nhau.

`w1-phay`    vuông góc giữa hai đường mang KÝ HIỆU PHẨY (`A'C'`). Trước phép
             sửa, `geometry_symbol_key("A'")` trả `None` nên witness của hợp
             đồng không nối được biến nào của chương trình.

Đáp án tính tay, hữu tỉ, trong ranh giới kernel — xem từng `oracle`.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import sys
from fractions import Fraction
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))


def _nap(ten: str):
    spec = importlib.util.spec_from_file_location(
        ten, BACKEND / "scripts" / f"{ten}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[ten] = m
    spec.loader.exec_module(m)
    return m


M = _nap("measure_geometry_stability")
PILOT = _nap("run_phase7a_pilot")

#: Hình lập phương cạnh 2, đặt `A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0)`, tầng
#: trên `z = 2`. Ba đáp án tính tay:
#:
#:   w1-goc-dd  AC = (2,2,0), B'C' = C'−B' = (0,2,0)
#:              cos² = |4|² / (8 · 4) = 16/32 = 1/2          (45°)
#:   w1-goc-dm  AC' = (2,2,2) với mặt (ABCD) pháp tuyến (0,0,1)
#:              sin² = |2|² / (12 · 1) = 4/12 = 1/3          (≠ 45° ⇒ phân
#:              biệt được sin² với cos² = 2/3)
#:   w1-phay    AC ⊥ B'D' : AC = (2,2,0), B'D' = D'−B' = (−2,2,0), tích vô
#:              hướng = −4+4 = 0 ⇒ true
#: Canary HẬU-SỬA (§12). Bốn họ, mỗi họ một đề DEV **mới**, k=1.
#:
#:   w3-hbh    diễn đạt TƯƠNG ĐƯƠNG — "hình bình hành" thay cho "song song".
#:             Trước sửa, `hp_a03_007` chết ở cổng phạm vi 2/2 vì đúng chỗ này.
#:   w3-thang  ràng buộc HỮU TỈ có thang tự do. `AB = a`, `SA = 3a/5` ⇒
#:             d = 12a/25. Nếu một phân số bị nuốt hay đổi giữa đường thì kết
#:             quả vẫn "hợp lý" mà sai — đúng lớp lỗi §5 đòi thử.
#:   w3-phay   ký hiệu phẩy + hoà giải tên ghép.
#:   w3-nhieu  nhiều bước phụ thuộc.
BAI_W3 = [
    {
        "id": "w3-hbh",
        "de": ("Cho tứ diện ABCD. Gọi M, N, P, Q lần lượt là trung điểm của "
               "AB, CD, BC, AD. Chứng minh MPNQ là hình bình hành."),
        "oracle": "w3_parallel_true",
    },
    {
        "id": "w3-thang",
        "de": ("Cho hình chóp S.ABC có mặt phẳng (SAB) vuông góc với mặt đáy, "
               "tam giác SAB vuông tại S, AB = a, SA = 4a/5. Tính khoảng cách "
               "từ điểm S đến mặt phẳng (ABC)."),
        "oracle": "w3_distance_12_25",
    },
    {
        "id": "w3-phay",
        "de": ("Cho hình lập phương ABCD.A'B'C'D' cạnh 2. Chứng minh rằng "
               "B'D' vuông góc với AC."),
        "oracle": "w3_vuong_goc_true",
    },
    {
        "id": "w3-nhieu",
        "de": ("Cho hình chóp S.ABCD có đáy ABCD là hình bình hành. Gọi M là "
               "trung điểm SA, N là trung điểm SB. Chứng minh MN song song "
               "với mặt phẳng (ABCD)."),
        "oracle": "w3_parallel_true",
    },
]

BAI_W1 = [
    {
        "id": "w1-goc-dd",
        "de": ("Cho hình lập phương ABCD.A'B'C'D' cạnh 2. Tính góc giữa hai "
               "đường thẳng AC và B'C'."),
        "oracle": "w1_cos_sq_1_2",
    },
    {
        "id": "w1-goc-dm",
        "de": ("Cho hình lập phương ABCD.A'B'C'D' cạnh 2. Tính góc giữa "
               "đường thẳng AC' và mặt phẳng (ABCD)."),
        "oracle": "w1_sin_sq_1_3",
    },
    {
        "id": "w1-phay",
        "de": ("Cho hình lập phương ABCD.A'B'C'D' cạnh 2. Chứng minh rằng "
               "AC vuông góc với B'D'."),
        "oracle": "w1_vuong_goc_true",
    },
]

_ORACLE_PILOT = PILOT.cham_oracle


def cham_oracle(ten: str, fm: dict, hd=None):
    if ten == "w3_parallel_true":
        return M.cham_predicate(fm, hd, "parallel")
    if ten == "w3_vuong_goc_true":
        return M.cham_predicate(fm, hd, "perpendicular")
    if ten == "w3_distance_12_25":
        # `SA = 4a/5` ⇒ SB = 3a/5 ⇒ d = SA·SB/AB = 12a/25. Chấm BẤT BIẾN
        # THANG qua `DEV.cham_oracle`: đề để `a` tự do, nên so tuyệt đối là
        # chấm *mô hình có tình cờ chọn a = 1 không*.
        DEV = _nap("run_geometry_dev_evaluation")
        r = DEV.cham_oracle({"oracle_result": {"distance": "12/25"}}, hd, fm)
        return ({"PASS": True, "FAIL": False}.get(r["verdict"]),
                f"{r['verdict']}: {r.get('ly_do') or r.get('lech')}")
    if ten == "w1_cos_sq_1_2":
        return PILOT._tim_so(fm, Fraction(1, 2))
    if ten == "w1_sin_sq_1_3":
        return PILOT._tim_so(fm, Fraction(1, 3))
    if ten == "w1_vuong_goc_true":
        # Chấm bằng CHÍNH checker server-owned, quy ước `None` ⇒ thoả.
        # Bản trước tìm một `True` trong `final_memory` — sai hợp đồng, và
        # sai theo chiều báo mô hình hỏng ở chỗ nó đúng. Xem `cham_predicate`.
        return M.cham_predicate(fm, hd, "perpendicular")
    return _ORACLE_PILOT(ten, fm, hd)


#: TRẦN CỨNG của wave này. Mục tiêu KHÔNG phải benchmark rộng — nó là phép
#: chứng minh end-to-end sau khi sửa, nên trần đặt sát: canary 3×1 và bộ ổn
#: định nhỏ 4×3, cộng đệm.
TRAN_LOGIC_WAVE, TRAN_HTTP_WAVE = 90, 120

#: Bốn đề của BỘ ỔN ĐỊNH NHỎ. Ba canary cộng một đề nhiều bước đã đăng ký
#: (`3-pmn-giao-tuyen` — dựng thiết diện rồi suy vị trí một điểm, chuỗi phụ
#: thuộc dài nhất trong tập pilot).
TEN_MINI = ("w1-goc-dd", "w1-goc-dm", "w1-phay", "3-pmn-giao-tuyen")

#: BA đề của bộ ổn định wave CHUẨN HOÁ THANG (§11 — 3 ca × k=3 = 9 lượt).
#:
#: Luật chọn viết ra ở đây thay vì quyết lúc chạy, vì chọn sau khi thấy canary
#: là bỏ mất đúng thứ một tập ổn định dùng để chứng minh. Ba ô, mỗi ô một rủi
#: ro mà wave này ĐỘNG VÀO:
#:
#:   w3-thang  ca DUY NHẤT có thang tự do — chính cơ chế vừa thêm.
#:   w3-nhieu  ca mà vòng phản hồi grounding gỡ được ở wave 4; §9 đòi nó
#:             không được hỏng lại.
#:   w3-phay   ký hiệu phẩy + tên ghép — lượt đắt nhất và dao động nhất
#:             (120s ở canary), tức chỗ dễ lộ bất ổn nhất.
#:
#: `w3-hbh` bị loại vì nó xanh liên tục qua ba wave: giữ nó lại là mua thêm
#: một lượt xác nhận điều đã biết, thay vì một lượt có thể ĐỎ.
TEN_STAB3 = ("w3-thang", "w3-nhieu", "w3-phay")


def _bang_token(ket: list[dict]) -> dict:
    """Cộng token theo bốn trường, và theo BA mẫu số khác nhau.

    Một con số *tổng token* không trả lời được câu hỏi về hạn chế token. Ba
    mẫu số dưới đây trả lời ba câu khác nhau: mỗi LƯỢT tốn bao nhiêu · mỗi IR
    **chạy được** tốn bao nhiêu (lượt hỏng vẫn tiêu token) · mỗi IR **đúng**
    tốn bao nhiêu. Con số thứ ba mới là giá thật của một kết quả dùng được.
    """
    tong = {"prompt_tokens": 0, "candidates_tokens": 0,
            "thoughts_tokens": 0, "total_tokens": 0}
    for r in ket:
        for chang in (r.get("token") or {}).values():
            for k in tong:
                tong[k] += int(chang.get(k) or 0)
    chay_duoc = sum(1 for r in ket if r.get("servable"))
    dung = sum(1 for r in ket if r.get("oracle_dat") is True)
    tt = tong["total_tokens"]
    return {**tong, "so_luot": len(ket),
            "executable_ir": chay_duoc, "correct_ir": dung,
            "tokens_moi_luot": round(tt / len(ket)) if ket else 0,
            "tokens_moi_executable_ir": round(tt / chay_duoc) if chay_duoc else None,
            "tokens_moi_correct_ir": round(tt / dung) if dung else None}


#: Kiểu mang toạ độ — cùng tập mà `grounding_gate._KIEU_HINH_HOC` đếm. Chép ở
#: đây thì hai bên sẽ trôi; nên bộ đo HỎI hệ được đo, không tự định nghĩa.
def _kieu_hinh_hoc() -> frozenset[str]:
    from app.simulation.semantic_program.grounding_gate import _KIEU_HINH_HOC
    return _KIEU_HINH_HOC


def _do_luong_7(ket: list[dict]) -> dict:
    """Ba con số §7. Cộng theo LƯỢT, không trung bình hoá tỉ lệ từng lượt.

    Trung bình các tỉ lệ cho một lượt khai 1 literal cùng trọng số với một lượt
    khai 12 — và lượt 12 literal mới là chỗ mô hình dễ bỏ sót xuất xứ nhất.
    """
    kieu = _kieu_hinh_hoc()

    def dem(ds) -> int:
        return sum(1 for d in (ds or []) if d.split("|")[1] in kieu)

    dat = sum(dem(r.get("justified_literals")) for r in ket)
    vo_can = sum(dem(r.get("unjustified_literals")) for r in ket)
    kiem = sum(len(r.get("constraints_checked") or []) for r in ket)
    thoa = sum(len(r.get("constraints_verified") or []) for r in ket)
    tong = dat + vo_can
    return {
        "literal_co_can_cu": dat, "literal_vo_can": vo_can, "literal_tong": tong,
        "ti_le_literal": f"{dat / tong:.0%}" if tong else "—",
        "rang_buoc_kiem": kiem, "rang_buoc_dat": thoa,
        "ti_le_rang_buoc": f"{thoa / kiem:.0%}" if kiem else "—",
        "co_buoc_thang": sum(1 for r in ket if r.get("scale_binding")),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stab3", action="store_true",
                   help="Bộ ổn định §11: 3 đề TEN_STAB3 × k=3. Chỉ sau canary 4/4.")
    p.add_argument("--canary3", action="store_true",
                   help="Canary HẬU-SỬA §12: 4 đề DEV mới × 1 lượt.")
    p.add_argument("--canary", action="store_true",
                   help="3 đề × 1 lượt. Chứng minh end-to-end trước, dừng sớm.")
    p.add_argument("--mini", action="store_true",
                   help="Bộ ổn định NHỎ 4 đề × k. Chỉ chạy SAU canary PASS.")
    p.add_argument("--k", type=int, default=3)
    p.add_argument("--out-dir",
                   default="docs/evaluation/geometry/wave1-dev-stability")
    p.add_argument("--chi-moi", action="store_true",
                   help="Chỉ ba đề MỚI, bỏ năm đề pilot. Rẻ hơn.")
    a = p.parse_args()

    if a.stab3:
        theo = {b["id"]: b for b in BAI_W3}
        bai, a.k = [theo[x] for x in TEN_STAB3], 3
    elif a.canary3:
        bai, a.k = BAI_W3, 1
    elif a.canary:
        bai, a.k = BAI_W1, 1
    elif a.mini:
        moi = {b["id"]: b for b in list(PILOT.BAI_PILOT) + BAI_W1}
        bai = [moi[x] for x in TEN_MINI]
    else:
        bai = BAI_W1 if a.chi_moi else list(PILOT.BAI_PILOT) + BAI_W1
    d = Path(a.out_dir)
    M.RA = d if d.is_absolute() else ROOT / d
    M.RUN_ID = "wave1-dev-stability"
    M.TRAN_LOGIC, M.TRAN_HTTP = 6, 8
    M.BAI = bai
    M.cham_oracle = cham_oracle
    M.TAP_KY_VONG = "wave1"
    M._KY_VONG_CACHE.clear()

    if os.environ.get("ALLOW_LIVE_AI") != "1":
        print(f"Thiếu ALLOW_LIVE_AI=1 — {len(bai)}×{a.k} lượt tiêu quota thật.")
        return 2
    try:
        from dotenv import load_dotenv
        load_dotenv(BACKEND / ".env")
    except ImportError:
        pass
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("Thiếu GEMINI_API_KEY.")
        return 2

    from app.runtime_identity import runtime_identity
    from app.ai import gemini
    r = runtime_identity()
    print(f"sha={r['git_sha'][:12]} cache={r['cache_version']} "
          f"model={gemini.MODEL}")
    print(f"{len(bai)} đề × {a.k} lượt · DEV, KHÔNG phải held-out\n")

    async def chay():
        out = []
        tl = th = 0
        for b in bai:
            for lan in range(1, a.k + 1):
                f = M.RA / f"{b['id']}-lan{lan}.json"
                if f.exists():
                    out.append(json.loads(f.read_text(encoding="utf-8"))["ban_ghi"])
                    continue
                if tl + 6 > TRAN_LOGIC_WAVE or th + 8 > TRAN_HTTP_WAVE:
                    print(f"⛔ CHẠM TRẦN WAVE: {tl}/{TRAN_LOGIC_WAVE} logic · "
                          f"{th}/{TRAN_HTTP_WAVE} HTTP — dừng TRƯỚC khi vượt.")
                    return out
                rr = await M.mot_luot(b, lan, key)
                out.append(rr)
                tl += rr.get("logical_calls") or 0
                th += rr.get("http_requests") or 0
                print(f"{'✅' if rr['servable'] else '❌'} {b['id']:<16} "
                      f"{lan}/{a.k} · {rr['do_tre_giay']:>5}s · "
                      f"{str(rr['stage_reached']):<20} oracle={rr['oracle_dat']} "
                      f"kiểm={rr['verification_match']} "
                      f"dựng={rr['construction_match']}", flush=True)
        return out

    ket = asyncio.run(chay())

    # DỪNG SỚM (§3): hỏng vì NHÀ CUNG CẤP thì không được đọc như hỏng vì hệ.
    # Phân biệt này là toàn bộ giá trị của trường `su_co` vừa thêm — trước đó
    # lời nhắn 429 bị rơi mất, và một lượt hết quota đọc y hệt một lượt hệ
    # ném lỗi.
    nha_cc = [r for r in ket
              if "429" in str(r.get("su_co") or "")
              or "RESOURCE_EXHAUSTED" in str(r.get("su_co") or "")]
    if nha_cc:
        print(f"\n⛔ PROVIDER_BLOCKED — {len(nha_cc)}/{len(ket)} lượt hỏng vì "
              "nhà cung cấp, không phải vì hệ:")
        print("   ", str(nha_cc[0].get("su_co"))[:160])
        print("   KHÔNG đọc lượt này như tín hiệu ngữ nghĩa.")

    print("\n── ỔN ĐỊNH DEV (x/k, không trung bình hoá) ──")
    for b in bai:
        x = [t for t in ket if t["case_id"] == b["id"]]
        print(f"  {b['id']:<16} served={sum(1 for t in x if t['servable'])}/{a.k}"
              f" oracle={sum(1 for t in x if t['oracle_dat'] is True)}/{a.k}"
              f" kiểm={sum(1 for t in x if t['verification_match'])}/{a.k}"
              f" dựng={sum(1 for t in x if t['construction_match'])}/{a.k}"
              f" nv={sorted({t['so_nghia_vu'] for t in x})}"
              f" stage={sorted({str(t['stage_reached']) for t in x})}")
    do = _do_luong_7(ket)
    print("\n── §7 · LITERAL & RÀNG BUỘC NGUỒN ──")
    print(f"  JUSTIFIED_GEOMETRY_LITERAL_RATE  {do['literal_co_can_cu']}/"
          f"{do['literal_tong']} = {do['ti_le_literal']}")
    print(f"  UNJUSTIFIED_LITERAL_COUNT        {do['literal_vo_can']}")
    print(f"  SOURCE_CONSTRAINT_PRESERVATION   {do['rang_buoc_dat']}/"
          f"{do['rang_buoc_kiem']} = {do['ti_le_rang_buoc']}")
    print(f"  buộc thang đã áp               {do['co_buoc_thang']}/{len(ket)} lượt")
    tok = _bang_token(ket)
    print("\n── TOKEN ──")
    for k2, v in tok.items():
        print(f"  {k2:<26} {v}")
    (M.RA / "tong_hop.json").write_text(
        json.dumps({"k": a.k, "token": tok, "do_luong_7": do, "runs": ket},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 2 if nha_cc else 0


if __name__ == "__main__":
    raise SystemExit(main())
