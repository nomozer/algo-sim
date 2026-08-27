# -*- coding: utf-8 -*-
"""PHASE 7A.2 — KỲ VỌNG NGHĨA VỤ, tách khỏi mã bộ đo. **0 API call.**

    from geometry_expectations import nap, khop_dung, khop_kiem

Trước pha này kỳ vọng nằm ngay trong `measure_geometry_stability.BAI`, tức
**người viết bộ đo sửa được thước ngay trong lượt đang đo**, và không ai tra
ngược được kỳ vọng đã đổi lúc nào. Nay chúng nằm ở
`docs/evaluation/geometry/expectations/*.json`, có lịch sử Git, có `ly_do` cho
từng nghĩa vụ, và có khai báo ai là người phán.

─── HAI TẬP RỜI NHAU, VÀ VÌ SAO GỘP CHÚNG LÀ MỘT LỖI ĐO ───────────────────

Đề hình học ra hai loại lệnh khác nhau, và trước pha này chúng bị nhét chung
một danh sách phẳng:

    "Hãy DỰNG mặt phẳng (PMN)"          → nghĩa vụ DỰNG   — sinh ra một VẬT
    "CHỈ RA RẰNG M nằm trên SA"         → nghĩa vụ KIỂM   — phán một MỆNH ĐỀ

Hậu quả đo được, không phải giả định: kỳ vọng của bài `3-pmn-giao-tuyen` từng
là `{point_on_line, point_on_plane}`, và **8 lượt liên tiếp** bác bỏ nó theo
cùng một hướng (`PHASE_7A_1_REPORT §5`). `point_on_plane` ở đó không phải nghĩa
vụ mô hình bỏ sót — nó là **mệnh lệnh dựng bị xếp nhầm vào tập kiểm**. Đề không
hỏi điểm nào thuộc `(PMN)`, nên nghĩa vụ ấy không có witness và không bao giờ
đúng được. Một chỉ số gộp hai tập sẽ mãi báo *"mô hình sai"* ở đúng chỗ mô hình
đọc đề đúng.

─── HAI PHÉP SO KHÁC NHAU, CÓ CHỦ ĐÍCH ────────────────────────────────────

Đây là chỗ dễ tưởng là bất nhất, nên ghi rõ:

    KIỂM   BẰNG ĐÚNG  (`m == k`)   — khai thừa CŨNG LÀ LỆCH
    DỰNG   CHỨA ĐỦ    (`m ⊆ k`)    — dựng thêm KHÔNG bị trừ điểm

Không đối xứng vì bản chất hai việc không đối xứng. Khai thừa một nghĩa vụ kiểm
nghĩa là mô hình trả lời một câu **không ai hỏi**, và ở bài đánh giá thì thừa
che mất chỗ nó thiếu. Còn dựng thêm là **bắt buộc**: muốn có giao tuyến `d` thì
phải dựng vài điểm trung gian mà đề không gọi tên. Trừ điểm ở đó là phạt mô
hình vì đã làm đúng phép dựng hình.

─── TÊN LÀ CỦA MÔ HÌNH, KHÔNG PHẢI CỦA BỘ ĐO ──────────────────────────────

Kỳ vọng dựng ghi tên **đề bài** gọi (`Q`, `(PMN)`, `d`), còn chương trình đặt
tên gì là quyền của mô hình (`Q_point`, `plane_PMN`). Nên phép so đi qua
`khop_ten_doi_tuong` — cùng lưới hoà giải mà bốn cổng sản phẩm đang dùng từ
Phase 6.7.1/7A.1, chứ không phải một lưới thứ hai của riêng bộ đo. Hai lưới sẽ
trôi khỏi nhau đúng lúc cần so hai lượt đo.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
GOC = BACKEND.parent
THU_MUC = GOC / "docs" / "evaluation" / "geometry" / "expectations"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

#: Tập nào được phép khai người đo là người phán.
#:
#: `pilot` được, vì nó chấm **bộ đo** chứ không chấm mô hình, và số của nó không
#: bao giờ là số luận văn. `holdout` thì KHÔNG: `PHASE_7A_1_REPORT §5` cho thấy
#: kỳ vọng do người đo đặt đã một lần ghi *"mô hình sai"* ở chỗ mô hình đúng, và
#: trên tập held-out thì không có lượt thứ hai để phát hiện ra điều đó.
TAP_CHO_PHEP_NGUOI_DO = frozenset({"pilot"})

_TRUONG_BAT_BUOC = ("dataset", "tap", "version", "nguoi_danh_gia",
                    "sinh_tu_model_output", "cases")


def _nap_module(ten: str):
    """Nạp một script anh em theo ĐƯỜNG DẪN — `scripts/` không phải package."""
    dd = Path(__file__).resolve().parent / f"{ten}.py"
    spec = importlib.util.spec_from_file_location(f"_ge_{ten}", dd)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ══ NẠP + KIỂM HÌNH DẠNG ═════════════════════════════════════════════════
def nap(tap: str, thu_muc: Path | None = None) -> dict[str, Any]:
    """Đọc một tập kỳ vọng, **fail-closed**: hình dạng sai ⇒ nổ, không đoán.

    Kiểm ngay lúc nạp chứ không lúc chấm, vì lúc chấm thì lượt đo đã tiêu call
    rồi — phát hiện kỳ vọng hỏng ở đó là phát hiện quá muộn.
    """
    f = (thu_muc or THU_MUC) / f"{tap}.json"
    if not f.exists():
        raise FileNotFoundError(f"không có tập kỳ vọng: {f}")
    d = json.loads(f.read_text(encoding="utf-8"))

    thieu = [t for t in _TRUONG_BAT_BUOC if t not in d]
    if thieu:
        raise ValueError(f"{f.name}: thiếu trường {thieu}")
    if d["tap"] != tap:
        raise ValueError(f"{f.name}: khai `tap`={d['tap']!r}, nạp bằng {tap!r}")
    if d["sinh_tu_model_output"] is not False:
        raise ValueError(
            f"{f.name}: `sinh_tu_model_output` phải là false. Kỳ vọng chép từ "
            "đầu ra mô hình thì chỉ số thành tautology.")

    loai = (d["nguoi_danh_gia"] or {}).get("loai")
    if loai == "nguoi_do" and tap not in TAP_CHO_PHEP_NGUOI_DO:
        raise ValueError(
            f"{f.name}: tập {tap!r} KHÔNG được dùng kỳ vọng do người đo tự đặt. "
            "Nguồn phải là đề/đáp án ngoài — xem HOLDOUT_PROTOCOL §1.")
    if not loai:
        raise ValueError(f"{f.name}: `nguoi_danh_gia.loai` bắt buộc")

    for c in d["cases"]:
        _kiem_case(f.name, c, doi_oracle=tap not in TAP_CHO_PHEP_NGUOI_DO)
    return d


def _kiem_case(ten_file: str, c: dict, doi_oracle: bool = False) -> None:
    ma = c.get("case_id")
    if not ma:
        raise ValueError(f"{ten_file}: một case thiếu `case_id`")
    for truong in ("construction_obligations", "verification_obligations"):
        if truong not in c:
            raise ValueError(f"{ten_file}/{ma}: thiếu `{truong}` "
                             "(rỗng thì khai `[]`, đừng bỏ trống)")
    for o in c["construction_obligations"]:
        for k in ("ten_trong_de", "kieu", "ly_do"):
            if not o.get(k):
                raise ValueError(f"{ten_file}/{ma}: nghĩa vụ dựng thiếu `{k}`")
    for o in c["verification_obligations"]:
        for k in ("kind", "ly_do"):
            if not o.get(k):
                raise ValueError(f"{ten_file}/{ma}: nghĩa vụ kiểm thiếu `{k}`")
    if doi_oracle:
        _kiem_oracle(ten_file, c, ma)


def _kiem_oracle(ten_file: str, c: dict, ma: str) -> None:
    """Nghĩa vụ phải NỐI ĐƯỢC tới một oracle — bằng CON TRỎ, không phải bản sao.

    VÌ SAO KHÔNG CHÉP ĐÁP ÁN VÀO ĐÂY: `holdout/pool.json` sở hữu
    `dap_an_chinh_thuc` + `phep_chuyen` + `oracle_result`, và nó là thứ được
    niêm phong. Chép giá trị sang file này là tạo bản thứ hai của đáp án, và
    hai bản sẽ trôi khỏi nhau đúng lúc cần tra *"số này ở đâu ra"*. Con trỏ thì
    không trôi được: sai `pool_case_id` là gãy ngay, sai `khoa` cũng gãy ngay.

    Chuỗi truy ngược mà Phase 7B đòi — `problem_text → … → metric` — nhờ vậy
    khép kín: kỳ vọng chỉ tới ô oracle, ô oracle chỉ tới `nguon.url`.

    Ô `B*` **cấm** có oracle: chúng chấm bằng *từ chối trung thực*, không bằng
    đáp án. Cùng luật `kiem_pool` áp cho `oracle_result`, chỉ là ở đầu kia.
    """
    o = str(c.get("slot") or "")
    if not o:
        raise ValueError(f"{ten_file}/{ma}: thiếu `slot` — không biết bài này "
                         "thuộc ô nào của BANG_O thì không đối chiếu được")
    ref = c.get("oracle_ref")
    if o.startswith("B"):
        if ref:
            raise ValueError(
                f"{ten_file}/{ma}: ô {o} NGOÀI phủ — không được có `oracle_ref` "
                "(chấm bằng 'từ chối trung thực', không bằng đáp án)")
        if not c.get("ghi_chu_kiem"):
            raise ValueError(f"{ten_file}/{ma}: ô B* phải ghi `ghi_chu_kiem` "
                             "— vì sao bài này chấm bằng thang khác")
        return
    if not ref:
        raise ValueError(
            f"{ten_file}/{ma}: tầng A phải có `oracle_ref` — nghĩa vụ không nối "
            "được tới đáp án thì `verification_match` đúng cũng không chứng "
            "minh được mô phỏng đúng")
    for k in ("pool_case_id", "khoa"):
        if not ref.get(k):
            raise ValueError(f"{ten_file}/{ma}: `oracle_ref` thiếu `{k}`")


def kiem_noi_oracle(d: dict, pool_cases: list[dict]) -> list[str]:
    """Con trỏ oracle có trỏ vào chỗ CÓ THẬT không. Trả danh sách lỗi.

    Tách khỏi `nap()` có chủ đích: `nap()` kiểm được một mình file kỳ vọng, còn
    hàm này cần pool. Gộp vào thì không nạp nổi kỳ vọng khi pool chưa soạn xong
    — mà thứ tự soạn đúng là pool trước, kỳ vọng sau.
    """
    theo_ma = {c.get("case_id"): c for c in pool_cases}
    loi: list[str] = []
    for c in d.get("cases") or []:
        ma, ref = c.get("case_id"), c.get("oracle_ref")
        if not ref:
            continue
        p = theo_ma.get(ref.get("pool_case_id"))
        if p is None:
            loi.append(f"{ma}: `oracle_ref` trỏ tới bài không có trong pool: "
                       f"{ref.get('pool_case_id')!r}")
            continue
        if ref.get("khoa") not in (p.get("oracle_result") or {}):
            loi.append(f"{ma}: pool/{p['case_id']}.oracle_result không có khoá "
                       f"{ref.get('khoa')!r} — có: "
                       f"{sorted((p.get('oracle_result') or {}))}")
        if (p.get("problem_text") or "") != (c.get("problem_text") or ""):
            # Hai file chép cùng một đề. Lệch một chữ nghĩa là một trong hai
            # bản đã bị sửa, và sau khi niêm phong thì không biết bản nào.
            loi.append(f"{ma}: `problem_text` LỆCH với pool/{p['case_id']}")
    return loi


def kinds_kiem(case: dict) -> list[str]:
    """Tập `kind` mà đề YÊU CẦU KIỂM — so trực tiếp với `RequestContract`."""
    return sorted({o["kind"] for o in case["verification_obligations"]})


def vat_phai_dung(case: dict) -> list[dict[str, str]]:
    """Vật mà đề RA LỆNH DỰNG, theo tên ĐỀ BÀI gọi."""
    return list(case["construction_obligations"])


# ══ ③b — NGHĨA VỤ KIỂM ═══════════════════════════════════════════════════
def khop_kiem(mong_doi: list[str] | None, khai: list[str] | None) -> dict:
    """So BẰNG ĐÚNG. Mượn thẳng `reliability_v2.obligation_match`.

    Không viết lại: phép so ấy đã có 25 test khoá hành vi (thứ tự không ảnh
    hưởng · thừa cũng là lệch · tập rỗng không tự khớp), và hai bản sao sẽ trôi
    khỏi nhau đúng lúc cần so hai vòng đo.
    """
    return _nap_module("reliability_v2").obligation_match(mong_doi, khai)


# ══ ③a — NGHĨA VỤ DỰNG ═══════════════════════════════════════════════════
def tap_da_dung(spec_raw: dict) -> set[str]:
    """Tên các vật chương trình THẬT SỰ DỰNG (không phải khai sẵn).

    Mượn `analyze_construction_dependency.phan_tich` — cùng định nghĩa
    *"được dựng"* mà chỉ số ④ dùng. Hai chỉ số hỏi hai câu khác nhau (④ hỏi
    *dựng thế nào*, ③a hỏi *có dựng thứ đề bảo dựng không*) nhưng phải đứng
    trên **cùng một** khái niệm nền, nếu không hai bảng sẽ mâu thuẫn nhau mà
    không ai chỉ ra được chỗ lệch.
    """
    pt = _nap_module("analyze_construction_dependency").phan_tich(spec_raw, None)
    return set(pt["dung_phu_thuoc"])


def khop_dung(mong_doi: list[dict], spec_raw: dict | None) -> dict:
    """So CHỨA ĐỦ, ba trạng thái như oracle: `True` · `False` · `None`.

    `None` ở hai chỗ khác nhau, và phân biệt được qua `vi_sao`:
      · đề KHÔNG ra lệnh dựng gì  ⇒ không áp dụng
      · chương trình không tồn tại ⇒ không chấm được
    Ghi cả hai thành `False` là ghi một lượt không đo được thành một lượt sai —
    đúng lỗi mà hợp đồng chỉ số đã cấm ở ②.
    """
    mong = [dict(o) for o in (mong_doi or [])]
    if not mong:
        return {"mong_doi": [], "da_dung": [], "thieu": [], "thua_dung": [],
                "khop_hoan_toan": None,
                "vi_sao": "đề không ra lệnh dựng vật nào — không áp dụng"}
    if not spec_raw:
        return {"mong_doi": [o["ten_trong_de"] for o in mong], "da_dung": [],
                "thieu": [], "thua_dung": [], "khop_hoan_toan": None,
                "vi_sao": "không có chương trình — không chấm được"}

    from app.simulation.semantic_program.domain_profile import khop_ten_doi_tuong

    da_dung = tap_da_dung(spec_raw)
    khop, thieu = {}, []
    for o in mong:
        ten_de = o["ten_trong_de"]
        # Hoà giải bằng LƯỚI SẢN PHẨM. Trùng lõi ⇒ `None` ⇒ tính là THIẾU:
        # cùng luật fail-closed của `khop_ten_doi_tuong`, vì đoán ở đó là dựng
        # một kết quả không tra lại được.
        ten_ct = ten_de if ten_de in da_dung else khop_ten_doi_tuong(ten_de, da_dung)
        if ten_ct:
            khop[ten_de] = ten_ct
        else:
            thieu.append(ten_de)

    return {
        "mong_doi": [o["ten_trong_de"] for o in mong],
        "da_dung": khop,
        "thieu": sorted(thieu),
        # Quan trắc, KHÔNG trừ điểm: điểm trung gian là phần bắt buộc của phép
        # dựng hình. Ghi ra để đọc `do_sau_max` của ④ cho có ngữ cảnh.
        "thua_dung": sorted(da_dung - set(khop.values())),
        "khop_hoan_toan": not thieu,
        "vi_sao": ("dựng đủ mọi vật đề yêu cầu" if not thieu
                   else f"chưa dựng: {sorted(thieu)}"),
    }


# ══ GỘP MỘT LƯỢT ═════════════════════════════════════════════════════════
def cham_mot_luot(case: dict, khai_kinds: list[str] | None,
                  spec_raw: dict | None) -> dict:
    """Hai chỉ số cho một lượt. **Không trả về một con số gộp** — có chủ đích.

    Gộp `dựng` và `kiểm` thành một tỉ lệ là dựng lại đúng cái vừa gỡ.
    """
    kiem = khop_kiem(kinds_kiem(case), khai_kinds)
    dung = khop_dung(vat_phai_dung(case), spec_raw)
    return {"verification_match": kiem, "construction_match": dung}
