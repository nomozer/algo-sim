# -*- coding: utf-8 -*-
"""HỢP ĐỒNG PHẢN HỒI TỪ CHỐI — `stage_reached` · `error_code` · lý do. 0 API call.

─── THỨ ĐO ĐƯỢC, VÀ VÌ SAO NÓ LÀ MỘT LỖI CHỨ KHÔNG PHẢI MỘT THIẾU SÓT ──────

`THESIS_DRAFT §1.6` và `§3.9` hứa nguyên văn một *"từ chối có cấu trúc — nêu
**giai đoạn dừng, loại thất bại, mã lỗi**"*. Lượt đo cuối giao `n1` với

    stage_reached = null      error_code = null

tức **hai trên bốn** trường đã hứa. Phát lại từng biên (`scripts/
replay_negative_boundaries.py`) cho thấy tín hiệu KHÔNG hề thiếu: ngay tại biên
4, pipeline đã phát `stage_reached="semantic_program"` và
`error_code="semantic_program_invalid"` cho observer. Nó chỉ không đi tiếp được
vì `_semantic_route_attempt` trả `None` — kiểu trả về ấy không chở nổi một phán
quyết, nên mọi thứ nó vừa biết bị bỏ lại ở telemetry.

Nghĩa là lỗi thuộc **biên chuyển kết quả**, không phải tầng phát hiện. Guard
dưới đây khoá đúng biên ấy: chúng đọc envelope mà *đường sản phẩm* dựng ra, chứ
không đọc telemetry — telemetry đã đúng từ đầu và sẽ xanh cả khi sản phẩm hỏng.

⚠️ **Không guard nào ở đây được phép suy trường từ `learner_reason`.** Câu tiếng
Việt là thứ đọc cho người; suy mã lỗi từ nó là dựng một thẩm quyền phân loại thứ
hai bằng khớp chuỗi — đúng lớp lỗi `ARCHITECTURE_MAP §8` liệt và đúng thứ
`error_codes.py` tồn tại để thay.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

from app.ai import pipeline
from app.learner_messages import attach_learner_reason, learner_reason
from app.simulation.error_codes import SEMANTIC_FAILURE_CATEGORY, ErrorCode

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import replay_negative_boundaries as R  # noqa: E402


# ══ NỀN — phát lại NGUYÊN BYTE hai ca âm của lượt đo cuối ═════════════════
@pytest.fixture(scope="module")
def de_bai() -> dict[str, str]:
    return R.doc_de_bai()


@pytest.fixture(scope="module")
def phan_hoi(de_bai) -> dict[str, dict]:
    """`{case_id: phản hồi SẢN PHẨM}` — qua `run_pipeline` thật, provider phát
    lại byte đã đóng băng, 0 lượt gọi."""
    ra = {}
    for cid in R.CA_AM:
        r = R.replay_case(cid, de_bai[cid])
        assert r["network_touch_attempts"] == [], r["network_touch_attempts"]
        ra[cid] = r["boundaries"]["7_product_response_adapter"]
    return ra


N1 = "n1_khoi_tron_xoay_tong_quat"
N2 = "n2_khoi_ghep_bu_can_boolean"

#: Trường bắt buộc của một lời từ chối mà hệ ĐÃ xác định được nguyên nhân.
TRUONG_CAU_TRUC = ("status", "stage_reached", "failure_category", "error_code")


# ══ ① HAI CA TRUNG TÂM ═══════════════════════════════════════════════════
def test_n1_co_du_giai_doan_dung_va_ma_loi(phan_hoi):
    """§9.1 — `n1` phải mang `stage_reached` và `error_code` KHÔNG rỗng."""
    e = phan_hoi[N1]
    assert e["status"] == "unsupported"
    assert e["stage_reached"], "giai đoạn dừng vẫn rỗng"
    assert e["error_code"], "mã lỗi vẫn rỗng"
    # Giá trị phải là thứ pipeline THẬT SỰ chạm, không phải một mã cho đủ ô.
    assert e["stage_reached"] == "semantic_program"
    assert e["error_code"] == ErrorCode.SEMANTIC_PROGRAM_INVALID.value


def test_n2_bon_truong_cau_truc_NHAT_QUAN(phan_hoi):
    """§9.2 — mã · tầng · loại · lý do phải cùng nói một kết luận."""
    e = phan_hoi[N2]
    for t in TRUONG_CAU_TRUC:
        assert e.get(t), f"{t} rỗng"
    assert e["error_code"] == ErrorCode.REQUESTED_OPERATION_UNCOVERED.value
    assert e["stage_reached"] == "structural_coverage"
    # `learner_reason` phải nói ĐÚNG chuyện "không có đường dựng", không phải
    # "diễn đạt lại đề" — viết lại đề bao nhiêu lần cũng không tạo ra một phép
    # IR chưa tồn tại.
    ly_do = e["learner_reason"]
    assert "diễn đạt lại" not in ly_do, ly_do
    assert "phép dựng" in ly_do or "chưa có" in ly_do, ly_do


def test_moi_ca_am_deu_du_bon_truong(phan_hoi):
    for cid, e in phan_hoi.items():
        for t in TRUONG_CAU_TRUC:
            assert e.get(t), f"{cid}: {t} rỗng"
        assert e.get("learner_reason"), f"{cid}: learner_reason rỗng"


# ══ ② KHÔNG HỨA LIỀU ═════════════════════════════════════════════════════
def test_KHONG_hua_he_mo_phong_duoc_dang_bai_nay(phan_hoi):
    """§9.10 — `n1`/`n2` nằm ngoài năng lực; một câu khẳng định "hệ có mô
    phỏng" ở đây là lời hứa sai đúng nghĩa."""
    for cid, e in phan_hoi.items():
        ly_do = e["learner_reason"]
        assert "hệ có mô phỏng" not in ly_do, (cid, ly_do)
        # Danh mục Tin học đã gỡ khỏi sản phẩm từ 2026-08-24; mời học sinh hình
        # học "thử một bài sắp xếp" là quảng bá một sản phẩm không tồn tại.
        for tu in ("sắp xếp", "nhị phân", "cổng logic", "định tuyến gói tin"):
            assert tu not in ly_do, (cid, tu, ly_do)


# ══ ③ BIÊN ADAPTER GIỮ NGUYÊN MÃ CỦA BACKEND ═════════════════════════════
def test_adapter_KHONG_dung_den_ma_va_tang(phan_hoi, de_bai):
    """§9.3 — `attach_learner_reason` chỉ ĐƯỢC thêm câu tiếng Việt."""
    for cid in R.CA_AM:
        r = R.replay_case(cid, de_bai[cid])
        truoc = r["boundaries"]["6_envelope_backend"]
        sau = r["boundaries"]["7_product_response_adapter"]
        for t in TRUONG_CAU_TRUC:
            assert truoc.get(t) == sau.get(t), (cid, t)
        assert set(sau) - set(truoc) == {"learner_reason"}, cid


def test_doi_learner_reason_KHONG_doi_ma_hay_loai():
    """§9.4 — câu cho người học không được là nguồn của phân loại."""
    env = {"status": "unsupported", "stage_reached": "structural_coverage",
           "failure_category": "geometry_generation_failed",
           "error_code": ErrorCode.REQUESTED_OPERATION_UNCOVERED.value,
           "reason": "bất kỳ"}
    a = attach_learner_reason(env)
    b = attach_learner_reason({**env, "reason": "một câu HOÀN TOÀN khác"})
    for t in TRUONG_CAU_TRUC:
        assert a[t] == b[t] == env[t], t
    assert a["learner_reason"] == b["learner_reason"], \
        "thông điệp đổi theo `reason` ⇒ nó đang đọc văn xuôi thay vì đọc mã"


def test_thong_diep_chon_theo_MA_truoc_roi_moi_den_loai():
    """Mã chi tiết hơn loại. Hai envelope cùng `failure_category` nhưng khác
    `error_code` phải cho hai lời khuyên khác nhau — nếu không thì mã lỗi
    không được dùng và `n2` lại nhận câu "diễn đạt lại đề"."""
    chung = {"status": "unsupported",
             "failure_category": "geometry_generation_failed"}
    ngoai_bao_dong = learner_reason(
        {**chung, "error_code": ErrorCode.REQUESTED_OPERATION_UNCOVERED.value,
         "stage_reached": "structural_coverage"})
    trong_bao_dong = learner_reason(
        {**chung, "error_code": ErrorCode.SEMANTIC_PROGRAM_INVALID.value,
         "stage_reached": "semantic_program"})
    assert ngoai_bao_dong != trong_bao_dong


# ══ ④ CÁC TẦNG LỖI KHÁC KHÔNG HỒI QUY ════════════════════════════════════
def _chay(monkeypatch, text: str, tra: list[str]) -> dict:
    async def gia(api_key, system_prompt, user_text, response_schema=None,
                  temperature=0.2, image=None):
        return tra.pop(0) if tra else "{}"

    monkeypatch.setattr(pipeline, "call_gemini", gia)
    return asyncio.run(pipeline.run_pipeline(text, "khoa-gia"))


def test_ngoai_mien_giu_nguyen_ma_va_tang(monkeypatch):
    env = _chay(monkeypatch,
                "Cân bằng phương trình NaOH + HCl rồi mô phỏng phản ứng.", [])
    assert env["failure_category"] == "out_of_scope"
    assert env["error_code"] == ErrorCode.GATE_OUT_OF_SCOPE.value
    assert env["stage_reached"] == "domain"


def test_khong_anh_xa_nghia_vu_giu_nguyen_ma_va_tang(monkeypatch):
    """Đề hình học nhưng không hỏi đại lượng nào kiểm chứng được ⇒ cổng
    `scope`, và cổng ấy vốn đã có mã — bản vá không được làm nó nhoè."""
    env = _chay(monkeypatch,
                "Cho hình chóp S.ABCD. Hãy nêu định nghĩa hình chóp đều.", [])
    assert env["error_code"] == ErrorCode.GATE_NOT_SIMULATION_SUITABLE.value
    assert env["stage_reached"] == "scope"


def test_analyze_hong_van_co_tang_va_ma(monkeypatch):
    """Lượt đọc đề trả JSON hỏng — tầng dừng là `semantic_analyze`. Đây là
    nhánh `return None` THỨ HAI, và nó hỏng cùng một kiểu với nhánh của `n1`."""
    env = _chay(monkeypatch,
                "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 3, SA vuông "
                "góc đáy, SA = 4. Tính thể tích khối chóp S.ABCD.",
                ["KHÔNG-PHẢI-JSON"])
    assert env["status"] == "unsupported"
    assert env["stage_reached"] == "semantic_analyze"
    assert env["error_code"] == ErrorCode.SEMANTIC_PROGRAM_INVALID.value


# ══ ⑤ CA DƯƠNG KHÔNG BỊ TRÌNH BÀY THÀNH TỪ CHỐI ══════════════════════════
def test_ca_duong_khong_mang_truong_tu_choi(de_bai):
    """§9.8 — một ca phục vụ được phải đi qua adapter NGUYÊN VẸN."""
    r = R.replay_case("p1_chop_thiet_dien_khoang_cach",
                      de_bai["p1_chop_thiet_dien_khoang_cach"])
    e = r["boundaries"]["7_product_response_adapter"]
    assert e["status"] == "ok"
    assert "learner_reason" not in e
    assert e.get("error_code") in (None, "")


# ══ ⑥ TAXONOMY — mã lỗi phải TRA ĐƯỢC loại, không ai chép bảng thứ hai ════
def test_moi_ma_route_deu_tra_duoc_loai():
    """`error_code` chở nhiều thông tin hơn `failure_category`: loại là một HÀM
    của mã. Guard này giữ điều đó đúng, nên frontend không cần chép bảng."""
    for ma in (ErrorCode.REQUESTED_OPERATION_UNCOVERED,
               ErrorCode.SEMANTIC_PROGRAM_INVALID,
               ErrorCode.INPUT_NOT_GROUNDED,
               ErrorCode.POSTCONDITION_VIOLATED):
        assert SEMANTIC_FAILURE_CATEGORY[ma.value]


def test_ma_loi_trong_envelope_deu_thuoc_enum(phan_hoi):
    hop_le = {m.value for m in ErrorCode}
    for cid, e in phan_hoi.items():
        assert e["error_code"] in hop_le, (cid, e["error_code"])


# ══ ⑦ BẢNG NHÃN FRONTEND KHÔNG ĐƯỢC TỤT LẠI SAU TAXONOMY BACKEND ═════════
def _bang_nhan(ten_bang: str) -> set[str]:
    """Đọc khoá của một bảng nhãn trong `SimulationWorkspace.tsx`.

    Đọc THẲNG tệp nguồn thay vì dựng một bản sao trong Python: bản sao là thứ
    sẽ trôi. Cùng cách `code-index-sync.test.ts` giữ chỉ mục khỏi trôi.
    """
    import re
    from pathlib import Path

    goc = Path(__file__).resolve().parents[3]
    src = (goc / "frontend" / "src" / "components"
           / "SimulationWorkspace.tsx").read_text(encoding="utf-8")
    than = src.split(f"{ten_bang}: Record<string, string> = {{", 1)[1]
    than = than.split("\n};", 1)[0]
    return set(re.findall(r"^\s{2}([a-z_0-9]+):", than, re.M))


def test_nhan_giai_doan_phu_het_taxonomy_backend():
    """Mọi giai đoạn mà đường sản phẩm có thể phát ra đều phải có nhãn tiếng
    Việt. Thiếu một nhãn thì học sinh đọc "Không xác định được" cho một ca hệ
    biết rõ — im lặng, và chỉ lộ ra khi có người nhìn đúng ca ấy."""
    import re
    from pathlib import Path

    goc = Path(__file__).resolve().parents[3]
    nguon = {
        goc / "backend" / "app" / "simulation" / "semantic_program" / "route.py",
        goc / "backend" / "app" / "ai" / "pipeline.py",
    }
    phat_ra: set[str] = set()
    for p in nguon:
        t = p.read_text(encoding="utf-8")
        phat_ra |= set(re.findall(r'stage_reached\s*=\s*"([a-z_]+)"', t))
        phat_ra |= set(re.findall(r'_hong\(\s*\n?\s*"([a-z_]+)"', t))
        phat_ra |= set(re.findall(r'"stage_reached":\s*"([a-z_]+)"', t))
    assert phat_ra, "không đọc được giai đoạn nào — phép quét đã hỏng"
    thieu = phat_ra - _bang_nhan("NHAN_GIAI_DOAN")
    assert not thieu, f"bảng nhãn frontend thiếu giai đoạn: {sorted(thieu)}"


def test_nhan_loai_phu_het_ma_route_co_the_phat():
    """Mọi `error_code` có mặt trong bảng `mã → loại` đều phải có nhãn."""
    thieu = set(SEMANTIC_FAILURE_CATEGORY) - _bang_nhan("NHAN_LOAI_VAN_DE")
    assert not thieu, f"bảng nhãn frontend thiếu mã: {sorted(thieu)}"


# ══ ⑧ FIXTURE UI PHẢI ĐI THEO — không để bề mặt học sinh đo hệ đã cũ ═════
def test_fixture_ui_khop_voi_phan_hoi_hien_tai(phan_hoi):
    """Fixture trình duyệt là bản sao đóng băng của phản hồi sản phẩm. Nếu nó
    không đi theo bản vá thì ảnh chụp sau đây chứng minh cho một hệ đã chết."""
    from pathlib import Path

    goc = Path(__file__).resolve().parents[3]
    thu_muc = (goc / "docs" / "evaluation" / "geometry"
               / "product-ui-result-rendering" / "fixtures")
    for cid, e in phan_hoi.items():
        p = thu_muc / f"{cid}.json"
        if not p.exists():                       # pragma: no cover
            pytest.skip(f"chưa có fixture {p.name}")
        fx = json.loads(p.read_text(encoding="utf-8"))
        for t in TRUONG_CAU_TRUC:
            assert fx["envelope"].get(t) == e.get(t), (cid, t)
