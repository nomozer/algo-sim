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
import re
import subprocess
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


#: Cỡ mẫu và ngân sách MỖI LƯỢT — chốt ở `HOLDOUT_K_FINAL.md` (Phase 7A.3).
#: Con dấu ghi lại để lượt chạy không cãi được là nó đã đo với `k` khác.
K_CHOT = 3
LOGIC_MOI_LUOT, HTTP_MOI_LUOT = 6, 8

#: Điều kiện pool — `HOLDOUT_PROTOCOL §3①`: *"≥40 bài, phủ ĐỦ 20/20 ô"*.
#:
#: **Hai số, hai câu hỏi khác nhau.** ĐỘ PHỦ hỏi *mọi ô có bài chưa*; ĐỘ SÂU
#: hỏi *seed còn gì để chọn không*. Pool đúng một bài mỗi ô phủ đủ 20/20 mà
#: mọi seed cho ra CÙNG một tập — lúc ấy câu "seed quyết định bài nào" thành
#: lời khai suông, và tính held-out mất mà không cổng nào kêu.
#:
#: Trước 2026-08-28 cổng rút chỉ canh vế phủ, còn `report_holdout_readiness`
#: canh vế sâu bằng một số `40` viết tay — hai cổng đọc cùng một pool bằng hai
#: ngưỡng rời nhau. Gom về đây để chúng không trôi khỏi nhau được nữa.
MOI_O_TOI_THIEU = 1
TONG_TOI_THIEU = 40


def _git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=GOC,
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:  # noqa: BLE001 — thiếu git không được làm hỏng con dấu
        return "unknown"


def _bam_tai_lieu(ten: str) -> str:
    """Băm một tài liệu trong `docs/evaluation/geometry/`. Vắng ⇒ `THIEU_FILE`,
    khai thẳng chứ không im: con dấu thiếu một băm là con dấu không chứng minh
    được thứ nó hứa chứng minh."""
    f = GEO / ten
    if not f.exists():
        return "THIEU_FILE"
    return hashlib.sha256(
        f.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()


def _chuan_de(s: str) -> str:
    """Gom khoảng trắng + bỏ hoa/thường, để so hai bản chép cùng một đề."""
    return " ".join(str(s).split()).lower()


def _de_cua_dev() -> set[str]:
    f = GEO / "dev" / "cases.json"
    if not f.exists():
        return set()
    return {_chuan_de(c["problem_text"])
            for c in json.loads(f.read_text(encoding="utf-8"))["cases"]}


#: Trạng thái một bài trong pool (Phase 7A.5). VẮNG MẶT ⇒ `accepted`, để bài
#: soạn tay trước đó không phải sửa.
#:
#: VÌ SAO GIỮ BÀI BỊ LOẠI TRONG FILE thay vì xoá: xoá là **loại im lặng**, và
#: loại im lặng là một dạng chọn tập. Giữ lại kèm lý do thì người sau kiểm được
#: rằng bài bị loại vì *nằm ngoài ranh giới năng lực*, không phải vì *hệ làm
#: sai nó* — hai câu khác hẳn nhau khi đọc một benchmark.
TRANG_THAI = ("accepted", "rejected_capability_boundary", "needs_manual_review",
              # Phase 7B-prep: đề chưa đối chiếu được NGUYÊN VĂN với nguồn.
              # Khác `needs_manual_review` ở chỗ đây là **không xác minh được
              # bằng kênh đang có**, không phải "chưa ai xem".
              "rejected_unverified")

#: Hình dạng đáp án — tập ĐÓNG. Mỗi giá trị nói oracle chấm bằng cách nào.
#:
#: KHÔNG có `float`, KHÔNG có "giá trị làm tròn", KHÔNG có "quan sát bằng mắt":
#: cả ba đều đưa sai số hoặc phán đoán người vào chỗ đang cần một phép so chính
#: xác, sau khi cả kernel đã dựng bằng `Fraction` để tránh đúng thứ đó.
ANSWER_SHAPE = ("exact_fraction", "predicate_boolean", "invariant_relation",
                "rejection_expected")

#: `capability_tag` → (ô hợp lệ · hình dạng đáp án · trong ranh giới?).
#: Dẫn từ `docs/evaluation/geometry/CAPABILITY_BOUNDARY.md`, đóng băng ở 7A.5.
NANG_LUC: dict[str, tuple[tuple[str, ...], str, bool]] = {
    "intersection_point": (("A01",), "invariant_relation", True),
    "incidence": (("A02",), "predicate_boolean", True),
    "parallel_relation": (("A03", "A04", "A05"), "predicate_boolean", True),
    "perpendicular_relation": (("A06", "A07", "A08"), "predicate_boolean", True),
    "angle_cos_sq": (("A09",), "exact_fraction", True),
    "angle_sin_sq": (("A10",), "exact_fraction", True),
    "rational_distance": (("A11", "A12"), "exact_fraction", True),
    "coplanar_section": (("A13",), "predicate_boolean", True),
    "rational_volume": (("A14",), "exact_fraction", True),
    "out_of_capability": (O_TANG_B, "rejection_expected", False),
}

#: Thẻ nào bắt buộc khai `domain_condition` — vì thẻ ấy CHỈ đúng dưới một điều
#: kiện, và điều kiện ấy không suy ra được từ `slot`.
DOI_DOMAIN_CONDITION = ("rational_distance", "coplanar_section",
                        "angle_sin_sq")


def check_capability_boundary(c: dict) -> list[str]:
    """Bài này có nằm trong ranh giới năng lực không? Trả LÝ DO FAIL, rỗng = pass.

    ─── VÌ SAO LÀ MỘT HÀM CHỨ KHÔNG PHẢI MỘT ĐOẠN VĂN ────────────────────

    Ranh giới đã ghi ở `CAPABILITY_BOUNDARY.md` từ 7A.5, nhưng tài liệu không
    chặn được ai cả. Bài `hp_a11_001` lọt vào ô A11 **sau khi** ranh giới ấy
    tồn tại trong đầu người soạn — nó chỉ lộ ra khi có người đi tra `_do`.

    ─── ÁP CHO AI ────────────────────────────────────────────────────────

    Chỉ cho bài **khai schema 7A.5+** (`capability_tag` có mặt, hoặc `status`
    khai tường minh). Bài cũ không mang hai trường ấy đi qua như trước — đổi
    luật dưới chân một tập đã soạn là cách chắc chắn nhất để không ai soạn tiếp.
    """
    tag, o = c.get("capability_tag"), c.get("slot")
    cid = c.get("case_id") or "?"
    if tag not in NANG_LUC:
        return [f"{cid}: capability_tag {tag!r} không có trong bảng — "
                f"{sorted(NANG_LUC)}"]

    o_hop_le, dang_can, trong_ranh_gioi = NANG_LUC[tag]
    loi: list[str] = []
    if o not in o_hop_le:
        loi.append(f"{cid}: thẻ {tag!r} không dùng cho ô {o!r} — chỉ {list(o_hop_le)}")

    dang = c.get("answer_shape")
    if dang not in ANSWER_SHAPE:
        loi.append(f"{cid}: answer_shape {dang!r} ngoài tập đóng {list(ANSWER_SHAPE)}")
    elif dang != dang_can:
        loi.append(f"{cid}: thẻ {tag!r} đòi answer_shape {dang_can!r}, khai {dang!r}")

    # Tầng A phải chấm được bằng đáp án; tầng B chấm bằng TỪ CHỐI TRUNG THỰC.
    # Trộn hai thang là gộp hai câu hỏi khác nhau vào một cột.
    if str(o).startswith("A") and dang == "rejection_expected":
        loi.append(f"{cid}: ô tầng A không được chấm bằng `rejection_expected`")
    if str(o).startswith("B") and trong_ranh_gioi:
        loi.append(f"{cid}: ô tầng B phải mang thẻ ngoài ranh giới")

    if tag in DOI_DOMAIN_CONDITION and not c.get("domain_condition"):
        loi.append(f"{cid}: thẻ {tag!r} CHỈ đúng dưới một điều kiện miền — "
                   "phải khai `domain_condition`")

    loi += _kiem_don_vi_oracle(cid, tag, c.get("oracle_result") or {})
    return loi


def _kiem_nguoi_xac_minh(cid: str, c: dict) -> list[str]:
    """`human_verifier` và `oracle_ref` phải là TRƯỜNG, không phải văn xuôi.

    Hai câu này phải trả lời được **bằng máy**: *ai đã xác minh đề nguyên văn*
    và *khoá nào trong `oracle_result` là oracle*. Câu thứ hai từng chỉ được
    dặn bằng văn xuôi trong `dev/cases.json §luat_soan` (*"khoá văn xuôi KHÔNG
    dùng để chấm"*) — mà bộ chấm thì không đọc văn xuôi.
    """
    loi: list[str] = []
    if c.get("problem_text_verified") is True and not c.get("human_verifier"):
        loi.append(f"{cid}: `problem_text_verified` là true mà không có "
                   "`human_verifier` — không ai chịu trách nhiệm cho chữ ký ấy")
    oracle = c.get("oracle_result") or {}
    if oracle:
        ref = c.get("oracle_ref")
        if not ref:
            loi.append(f"{cid}: có `oracle_result` mà thiếu `oracle_ref` — "
                       f"không biết khoá nào là oracle (có: {sorted(oracle)})")
        elif ref not in oracle:
            loi.append(f"{cid}: `oracle_ref` = {ref!r} không có trong "
                       f"`oracle_result` (có: {sorted(oracle)})")
    return loi


def _kiem_don_vi_oracle(cid: str, tag: str, oracle: dict) -> list[str]:
    """Đơn vị oracle phải khớp `geometry_exec._do`. Lỗi ở đây là **im lặng**:
    oracle đúng về giá trị mà sai về đơn vị vẫn chấm ra một con số."""
    from fractions import Fraction

    loi: list[str] = []
    if tag == "out_of_capability":
        if oracle:
            loi.append(f"{cid}: ô ngoài phủ KHÔNG được mang oracle_result")
        return loi

    if tag in ("rational_distance", "angle_cos_sq", "angle_sin_sq",
               "rational_volume"):
        khoa = {"rational_distance": "distance", "rational_volume": "volume",
                "angle_cos_sq": "angle", "angle_sin_sq": "angle"}[tag]
        gt = oracle.get(khoa)
        if gt is None:
            return [f"{cid}: thiếu `oracle_result.{khoa}`"]
        s = str(gt)
        # ── BA CHẨN ĐOÁN KHÁC NHAU, và trước bản này chúng bị gộp ──────────
        #
        # `2a³/3` và `2a^3/3` từng bị báo là "CĂN THỨC — ngoài ranh giới". SAI
        # HẲN: bài ấy hoàn toàn trong ranh giới, chỉ là đáp án còn **tham số**
        # `a` chưa gán. Thông báo cũ bảo người soạn vứt một bài tốt đi — đúng
        # lớp lỗi "đổ cho dữ liệu cái lỗi thuộc về bộ đo" mà cả wave này đi sửa.
        #
        # Căn thức: hệ KHÔNG biểu diễn được ⇒ loại thật.
        if any(k in s for k in ("√", "sqrt", "\\sqrt")):
            return [f"{cid}: `{khoa}` khai dạng CĂN THỨC ({s!r}) — ngoài ranh "
                    "giới, không phải chuyện đổi cách viết"]
        # Còn tham số (`a`, `a³`, `a^3`) ⇒ CHƯA GÁN, không phải ngoài phủ.
        if re.search(r"[A-Za-zÀ-ỹ]|\^|³|²", s):
            return [f"{cid}: `{khoa}` = {s!r} còn THAM SỐ chưa gán — không "
                    "phải bài ngoài phủ. Gán `a = 1` rồi rút gọn "
                    "(`2a³/3` → `2/3`), và ghi phép gán ấy vào `phep_chuyen` "
                    "để người khác kiểm lại."]
        # THẬP PHÂN bị cấm dù `Fraction("1.3333")` parse được.
        #
        # Đây đúng là lỗ đã suýt lọt: đáp án nguồn của `hp_a11_001` là `7,35`,
        # một số ĐÃ LÀM TRÒN theo yêu cầu của đề. Nhận nó thì oracle mang sẵn
        # sai số, ngay sau khi cả kernel dựng bằng `Fraction` để tránh. Viết
        # `1/2` thay `0.5` không mất gì; viết `0.577` thay `√3/3` thì mất tất.
        if any(k in s for k in (".", ",")):
            return [f"{cid}: `{khoa}` = {s!r} viết dạng THẬP PHÂN — khai bằng "
                    "phân số (`4/3`, không phải `1.3333`). Thập phân hoặc là "
                    "làm tròn, hoặc là một phân số viết khó kiểm hơn"]
        try:
            Fraction(s)
        except (ValueError, ZeroDivisionError):
            loi.append(f"{cid}: `{khoa}` = {s!r} không phải phân số chính xác "
                       "— float và số làm tròn đều bị cấm làm oracle")
    return loi

#: Chỉ `accepted` mới được đếm vào độ phủ và được rút.
def duoc_rut(c: dict) -> bool:
    return c.get("status", "accepted") == "accepted"


def kiem_pool(cases: list[dict]) -> list[str]:
    """Trả danh sách lỗi. Rỗng ⇒ pool hợp lệ.

    Kiểm ở đây chứ không ở lúc chạy: một bài thiếu `nguon` phát hiện sau khi đã
    niêm phong thì **không sửa được nữa** mà không phá con dấu.

    Bài **không** `accepted` chỉ bị kiểm hai thứ: trạng thái hợp lệ và **có
    lý do**. Kiểm chúng như bài thật là đòi `oracle_result` cho một bài vừa bị
    loại **vì** không có oracle biểu diễn được.
    """
    loi: list[str] = []
    dev = _de_cua_dev()
    for i, c in enumerate(cases):
        cid = c.get("case_id") or f"#{i}"
        tt = c.get("status", "accepted")
        if tt not in TRANG_THAI:
            loi.append(f"{cid}: status {tt!r} không hợp lệ — {list(TRANG_THAI)}")
            continue
        if tt != "accepted":
            if not (c.get("reason") or c.get("ly_do_loai")):
                loi.append(f"{cid}: status={tt} mà không nêu `reason` — "
                           "loại im lặng là một dạng chọn tập")
            if not (c.get("nguon") or {}).get("url"):
                loi.append(f"{cid}: bài bị loại vẫn phải giữ `nguon.url` "
                           "để người sau tra ngược được")
            continue
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
        # Ranh giới năng lực — chỉ áp cho bài khai schema 7A.5+.
        if c.get("capability_tag") is not None or "status" in c:
            loi += check_capability_boundary(c)
            # NGUYÊN VĂN: `problem_text` phải đối chiếu được với nguồn. Bản
            # tóm tắt của một mô hình đọc web KHÔNG tính — nó rơi mất đúng
            # những ký hiệu mang hình học (đo được: `⊥` xuất hiện 0 lần trong
            # một tài liệu 217 trang về quan hệ vuông góc).
            if c.get("problem_text_verified") is not True:
                loi.append(
                    f"{cid}: `problem_text_verified` chưa true — chưa ai đối "
                    "chiếu NGUYÊN VĂN với nguồn. Đề chép sai một ký hiệu là "
                    "một bài toán KHÁC, và nó vẫn đọc trôi chảy.")
            # XUẤT XỨ, không phải NĂNG LỰC — nên kiểm ở đây chứ không nhét vào
            # `check_capability_boundary`. Hai câu hỏi khác nhau: cái kia hỏi
            # *"hệ làm được bài này không"*, cái này hỏi *"ai chịu trách nhiệm
            # cho dữ liệu này"*.
            loi += _kiem_nguoi_xac_minh(cid, c)
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


def kiem_du_dieu_kien_rut(
        cases: list[dict]) -> tuple[dict[str, list[dict]], list[str]]:
    """Rổ rút theo ô + lý do CHƯA rút được. Danh sách rỗng ⇒ rút được.

    Tách khỏi `main()` để **đỏ được từ test**: hai ngưỡng ở đây chỉ chạy một
    lần trong đời, ngay trước lượt held-out duy nhất, nên chúng phải chứng
    minh được là chặn thật trước ngày ấy chứ không phải trong ngày ấy.
    """
    theo_o: dict[str, list[dict]] = {}
    for c in cases:
        # Chỉ `accepted` mới vào rổ rút. Bài bị loại nằm trong file để tra
        # ngược, KHÔNG để lấp ô — lấp ô bằng một bài hệ không phục vụ được là
        # dựng một ô chắc chắn trượt.
        if duoc_rut(c):
            theo_o.setdefault(c["slot"], []).append(c)

    loi: list[str] = []
    if thieu := [o for o in BANG_O if len(theo_o.get(o, [])) < MOI_O_TOI_THIEU]:
        loi.append(f"Pool KHÔNG phủ {len(thieu)}/{len(BANG_O)} ô: {thieu}")
        loi.append("KHÔNG rút bù từ ô khác — rút bù là lặng lẽ đổi tập đo.")
    if (n := sum(len(v) for v in theo_o.values())) < TONG_TOI_THIEU:
        loi.append(f"Pool chỉ {n}/{TONG_TOI_THIEU} bài rút được — "
                   f"thiếu {TONG_TOI_THIEU - n}.")
        loi.append("Đủ ô mà thiếu bài thì mọi seed cho ra CÙNG một tập: "
                   "seed hết quyết định được gì, tập hết là held-out.")
    return theo_o, loi


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

    theo_o, chua_du = kiem_du_dieu_kien_rut(cases)
    if chua_du:
        for d in chua_du:
            print(d)
        return 2

    if a.chi_kiem_pool:
        n = sum(len(v) for v in theo_o.values())
        # ĐẾM BÀI RÚT ĐƯỢC, không đếm dòng trong file: bài đã loại vẫn nằm
        # trong pool để tra ngược, và in `len(cases)` ở đây là tự khai đủ
        # bằng chính những bài vừa bị loại.
        print(f"Pool hợp lệ · {n} bài rút được · phủ đủ {len(BANG_O)}/"
              f"{len(BANG_O)} ô")
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
        # ── Danh tính ĐẦY ĐỦ của lượt đo (Phase 7B-prep) ─────────────────
        #
        # Băm hệ thôi thì chưa đủ: `HOLDOUT_SEAL` phải trả lời được *"đo bản
        # nào, bằng thước nào, với kỳ vọng nào, cỡ mẫu bao nhiêu"*. Thiếu một
        # trong bốn thì sau khi thấy số, mọi câu "lúc ấy thước còn khác" đều
        # không kiểm chứng được — đúng lý do `freeze_evaluation_candidate` ra đời.
        "commit": _git_sha(),
        "metric_contract_hash": _bam_tai_lieu("PHASE7_METRIC_CONTRACT.md"),
        "capability_boundary_hash": _bam_tai_lieu("CAPABILITY_BOUNDARY.md"),
        "expectation_hash": _bam_tai_lieu("expectations/holdout.json"),
        "pool_hash": _bam(cases),
        "k": K_CHOT,
        "budget": {"logic": len(chon) * K_CHOT * LOGIC_MOI_LUOT,
                   "http": len(chon) * K_CHOT * HTTP_MOI_LUOT,
                   "dan_xuat": f"{len(chon)} bài × {K_CHOT} lượt × "
                               f"{LOGIC_MOI_LUOT} logic / {HTTP_MOI_LUOT} HTTP"},
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
