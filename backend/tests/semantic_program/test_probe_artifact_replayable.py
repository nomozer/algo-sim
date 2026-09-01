# -*- coding: utf-8 -*-
"""ARTIFACT PHẢI CHẠY LẠI ĐƯỢC, không chỉ ĐỌC ĐƯỢC. **0 API call.**

─── LỖ NÓ BỊT ─────────────────────────────────────────────────────────────

Wave đo độ ổn định `CLEAN_BASELINE_V2` phải **DỪNG TRƯỚC KHI GỌI API**: nó đòi
ba lượt sinh trên CÙNG một đầu vào, và `probe.json` không dựng lại nổi đầu vào
của lượt một.

Bản ghi hợp đồng khi ấy là một bản TÓM TẮT:

    {"hash": …, "input_facts": 7, "obligations": ["distance"]}

Đủ để đọc báo cáo. Không đủ để chạy lại — prompt tổng hợp nhúng `id`, `nhãn`
và `giá trị` của từng dữ kiện (`pipeline._facts_for_prompt`), nên thiếu chúng
thì lượt lặp nhận một prompt KHÁC lượt gốc.

Gom `source_fact_id` từ chương trình cũng không cứu được: `v2_02` có hợp đồng
**6** dữ kiện mà mô hình chỉ trích dẫn **4**.

⇒ Một lượt đo đã tiêu 13 lượt provider trở thành **không kiểm lại được** vì một
trường bị lược. Test này biến điều đó thành ĐỎ thay vì một phát hiện muộn.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import (
    InputFact,
    RequestContract,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

GOC = Path(__file__).resolve().parents[3]
_ARTIFACT = (GOC / "docs" / "evaluation" / "geometry" / "clean-baseline-v2"
             / "probe.json")


def _hop_dong_mau() -> RequestContract:
    """Hợp đồng có ĐỦ hình dạng thật: dữ kiện có nhãn và giá trị, có nghĩa vụ.

    Dùng một hợp đồng RỖNG ở đây thì test xanh mà không chứng minh gì — đúng
    thứ đã để lọt bản tóm tắt.
    """
    return RequestContract(
        problem_text="Cho hình chóp S.ABCD có đáy là hình vuông cạnh 4.",
        input_facts=(
            InputFact(fact_id="canh_day", label="cạnh đáy", values=("4",)),
            InputFact(fact_id="chieu_cao", label="SA", values=("4",)),
        ),
        obligations=(Obligation(kind="distance", container="I",
                                params={"wrt": "SBC"}),),
    )


def test_ban_ghi_hop_dong_TAI_TAO_DUOC_nguyen_ven():
    """Bản ghi phải round-trip: ghi ra rồi dựng lại phải bằng bản gốc.

    Đây là phép kiểm THẬT, không phải kiểm "có trường `raw` không": một trường
    `raw` sai hình dạng vẫn có mặt.
    """
    from run_clean_baseline_v2 import ghi_hop_dong

    goc = _hop_dong_mau()
    ban_ghi = ghi_hop_dong(goc)
    assert "raw" in ban_ghi, "bản ghi chỉ TÓM TẮT — không chạy lại được"

    dung_lai = RequestContract.model_validate(ban_ghi["raw"])
    assert dung_lai.model_dump_json() == goc.model_dump_json(), (
        "dựng lại KHÔNG bằng bản gốc — lượt lặp sẽ nhận prompt khác")


def test_ban_ghi_giu_DU_du_kien_khong_chi_dem():
    """Đếm không thay được nội dung. `v2_02` có 6 dữ kiện, mô hình trích dẫn
    4 — nên gom từ chương trình dựng lại sẽ thiếu hai mục."""
    from run_clean_baseline_v2 import ghi_hop_dong

    r = ghi_hop_dong(_hop_dong_mau())["raw"]
    ids = {f["fact_id"] for f in r["input_facts"]}
    assert ids == {"canh_day", "chieu_cao"}
    for f in r["input_facts"]:
        assert f.get("label"), f"{f['fact_id']} mất nhãn — prompt nhúng nhãn"
        assert f.get("values"), f"{f['fact_id']} mất giá trị"


def test_ban_ghi_giu_PROBLEM_TEXT():
    """`problem_text` nuôi cổng trung thực năng lực. Mất nó thì lượt lặp chạy
    dưới một cổng KHÁC lượt gốc, và phép so không còn nghĩa."""
    from run_clean_baseline_v2 import ghi_hop_dong

    assert ghi_hop_dong(_hop_dong_mau())["raw"]["problem_text"]


_SEED = (GOC / "docs" / "evaluation" / "geometry" / "stability-seed"
         / "seed.json")


@pytest.mark.skipif(not _SEED.exists(), reason="chưa chụp hạt giống")
def test_hat_giong_do_on_dinh_CHAY_LAI_DUOC_that():
    """Khoá THÀNH QUẢ, không khoá lời khai.

    Không đọc cờ `input_equivalence` trong artifact — cờ ấy do chính lượt chạy
    tự ghi, nên tin nó là tin bị cáo. Chạy lại phép kiểm TỪ ĐĨA, trong tiến
    trình test, không provider nào.

    Hai chiều, và cần cả hai: `tự-chứa` chứng minh artifact đứng vững khi mã
    đã refactor; `dựng-lại` chứng minh mã hiện tại thật sự tái tạo được. Chỉ
    một chiều thì hoặc ta tin một bản sao, hoặc ta tin một công thức có thể đã
    đổi.
    """
    from capture_stability_seed import tu_kiem

    k = tu_kiem(_SEED)
    assert k["cases"], "artifact rỗng"
    hong = [x["case_id"] for x in k["cases"]
            if not (x["raw_captured"] and x["roundtrip"]
                    and x["payload_captured"] and x["self_contained"]
                    and x["hash_replay"])]
    assert not hong, f"hạt giống KHÔNG chạy lại được: {hong}"
    assert k["input_equivalence"]


@pytest.mark.skipif(not _SEED.exists(), reason="chưa chụp hạt giống")
def test_hat_giong_giu_DU_SAU_de_va_KHONG_lo_khoa():
    seed = json.loads(_SEED.read_text(encoding="utf-8"))
    assert len(seed["cases"]) == 6
    van = json.dumps(seed, ensure_ascii=False)
    for cam in ("api_key", "GEMINI_API_KEY", "Authorization"):
        assert cam not in van, f"artifact lộ {cam}"


@pytest.mark.skipif(not _ARTIFACT.exists(), reason="chưa có artifact V2")
def test_artifact_V2_hien_tai_KHONG_du_de_chay_lai():
    """GHI LẠI hiện trạng, không phải một lời than.

    Artifact V2 đã chạy (13 lượt provider) mang bản TÓM TẮT, nên wave đo độ
    ổn định phải dừng trước API. Test này khẳng định điều đó là SỰ THẬT ĐÃ
    BIẾT — nếu một ngày nó đỏ, nghĩa là artifact đã được sinh lại bằng bản ghi
    mới và wave ổn định chạy được.
    """
    d = json.loads(_ARTIFACT.read_text(encoding="utf-8"))
    thieu = [c["case_id"] for c in d["cases"]
             if "raw" not in (c.get("request_contract") or {})]
    assert len(thieu) == len(d["cases"]), (
        "artifact V2 nay CÓ hợp đồng đầy đủ — chạy được wave độ ổn định, "
        f"gỡ test này. Ca còn thiếu: {thieu}")
