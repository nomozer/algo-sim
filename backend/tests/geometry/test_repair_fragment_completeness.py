# -*- coding: utf-8 -*-
"""NGỮ CẢNH SỬA PHẢI CHỨA HỢP ĐỒNG CẦN ĐỂ SỬA. **0 lượt gọi model.**

    `REPAIR_FRAGMENT_COMPLETENESS`, 2026-09-04.

─── LỖ ĐO ĐƯỢC BẰNG QUOTA THẬT ────────────────────────────────────────────

`cylinder_2` (probe V2): mô hình viết `intersect_plane_curved` như một CÂU
LỆNH. Validator nói đúng — nó không phải tag câu lệnh nào. Nhưng mảnh hợp đồng
gửi kèm lượt sửa **bỏ hẳn mục biểu thức**, tức chỗ phép ấy thật sự được định
nghĩa. Mô hình nhận được *"sai ở đâu"* mà không nhận được *"dạng đúng nằm chỗ
nào"*. Chín lượt sửa cứu 0 ca.

Cơ chế chính xác: lời từ chối liệt kê **mọi** tag câu lệnh hợp lệ, nên phép
khớp định danh giữ cả chín dòng ấy trước; dòng định nghĩa
`intersect_plane_curved` đứng thứ **14/15** và bị trần `toi_da=12` cắt mất.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from app.simulation.semantic_program.grammar_card import (
    _TIEU_DE_BIEU_THUC,
    _TIEU_DE_LENH,
    grammar_card,
    manh_hop_dong,
)

RUN2 = (Path(__file__).resolve().parents[3]
        / "docs/evaluation/geometry/curved-ergonomics-v2-run2/cases")


def _loi(cid: str) -> str:
    return str(json.loads(
        (RUN2 / cid / "final.json").read_text(encoding="utf-8")
    )["loi_schema"] or "")


# ══ §26 · CYLINDER_2 — CÂU LỆNH ↔ BIỂU THỨC ══════════════════════════════
def test_cylinder_2_manh_nay_CO_hop_dong_bieu_thuc():
    """Ca chấp nhận chính. Mảnh phải trả lời được cả ba câu:
    sai gì · phép ấy thuộc nhóm nào · dùng nó thế nào cho đúng."""
    m = manh_hop_dong(_loi("cylinder_2"), "hinh_hoc")
    assert "intersect_plane_curved:" in m, "thiếu chữ ký của chính phép bị từ chối"
    assert _TIEU_DE_BIEU_THUC in m, "thiếu tiêu đề nhóm — mô hình không biết nó là biểu thức"
    assert "assign:" in m, "thiếu cửa tiêu thụ biểu thức"


def test_cylinder_2_DO_duoc_duoi_bo_chon_CU():
    """Bản cũ: khớp định danh phẳng rồi cắt ở 12 dòng. Dựng lại đúng nó và
    chứng minh mảnh khi ấy THIẾU — nếu không, ca trên không chứng minh gì."""
    import re

    from app.simulation.semantic_program.grammar_card import _TU_CHUNG

    loi = _loi("cylinder_2")
    the = grammar_card("hinh_hoc")
    dinh_danh = {t for t in re.findall(r"[a-z][a-z0-9_]{3,}", loi)
                 if t not in _TU_CHUNG}
    cu = "\n".join([d for d in the.splitlines()
                    if any(t in d for t in dinh_danh) and d.strip()][:12])

    assert "intersect_plane_curved:" not in cu, (
        "bộ chọn CŨ lẽ ra phải thiếu dòng ấy — nếu nó có thì ca chấp nhận ở "
        "trên không chứng minh được điều gì")
    assert _TIEU_DE_BIEU_THUC not in cu


# ══ §27 · CIRCUMSPHERE — TÊN TOÁN HẠNG ═══════════════════════════════════
def test_circumsphere_manh_CO_ten_toan_hang_that():
    m = manh_hop_dong(_loi("circumsphere"), "hinh_hoc")
    assert "vector_from_points:" in m
    assert "from_point" in m and "to_point" in m


def test_ten_toan_hang_DAN_TU_THAM_QUYEN_chu_khong_chep():
    """`SIGNATURE_AUTHORITIES = 1`.

    Thẩm quyền tên toán hạng là **model Pydantic** (`contract.py`); thẻ sinh ra
    từ đó, và mảnh sửa cắt ra từ thẻ. Ca này so tên trong mảnh với tên đọc
    THẲNG từ model — nếu ở đâu đó có một bảng chép tay thì hai bên sẽ lệch.
    """
    from app.simulation.semantic_program.contract import VectorFromPointsExpr

    truong = [t for t in VectorFromPointsExpr.model_fields if t != "kind"]
    assert truong, "model không còn trường nào — ca thử mất nghĩa"

    from app.simulation.semantic_program.grammar_card import _ten_phep

    m = manh_hop_dong(_loi("circumsphere"), "hinh_hoc")
    # Đọc tên phép qua `_ten_phep`: từ `CARD_CATEGORY_AFFORDANCE` mỗi dòng mở
    # đầu bằng nhãn loại, nên so tiền tố sẽ trượt.
    dong = next(d for d in m.splitlines() if _ten_phep(d) == "vector_from_points")
    for t in truong:
        assert t in dong, f"mảnh thiếu toán hạng '{t}' mà model đang khai"


# ══ §8 · KHÔNG RIÊNG MỘT PHÉP — MỖI NHÓM MỘT ĐẠI DIỆN ════════════════════
@pytest.mark.parametrize("phep,tieu_de", [
    ("intersect_plane_plane", _TIEU_DE_BIEU_THUC),
    ("midpoint", _TIEU_DE_BIEU_THUC),
    ("measure", _TIEU_DE_BIEU_THUC),
    ("construct_section", _TIEU_DE_LENH),
    ("construct_polygon", _TIEU_DE_LENH),
])
def test_moi_nhom_deu_duoc_chi_dung_muc(phep, tieu_de):
    """Lỗi tag sai cho phép bất kỳ ⇒ mảnh nêu ĐÚNG nhóm của nó."""
    loi = (f"Lỗi cú pháp schema SemanticProgramSpec: 1 validation error\n"
           f"statements.0\n  Input tag '{phep}' found using 'kind' does not "
           f"match any of the expected tags: 'assign', 'declare_point'")
    m = manh_hop_dong(loi, "hinh_hoc")
    assert f"{phep}:" in m, phep
    assert tieu_de in m, phep


def test_bieu_thuc_luon_kem_cua_tieu_thu_con_cau_lenh_thi_khong():
    """`assign` chỉ có nghĩa khi phép sai là BIỂU THỨC. Kèm nó vào một lỗi câu
    lệnh là thêm nhiễu vào đúng chỗ cần hẹp."""
    bt = manh_hop_dong("statements.0\n  Input tag 'midpoint' found using 'kind'",
                       "hinh_hoc")
    assert "assign:" in bt
    lenh = manh_hop_dong(
        "statements.0.construct_polygon.vertices\n  Input should be a valid list",
        "hinh_hoc")
    assert "construct_polygon:" in lenh
    assert _TIEU_DE_LENH in lenh


# ══ §28 · KHÔNG ĐỔ CẢ LƯỢC ĐỒ ════════════════════════════════════════════
@pytest.mark.parametrize("cid", ["cylinder_2", "circumsphere", "ball_2"])
def test_manh_van_NHAM_DICH_khong_phai_ca_the(cid):
    """`REPAIR_FRAGMENT_TARGETED` — mảnh phải nhỏ hơn hẳn cả thẻ, và tuyệt đối
    không phải bản đổ nguyên lược đồ 111 KB."""
    m = manh_hop_dong(_loi(cid), "hinh_hoc")
    the = grammar_card("hinh_hoc")
    assert m and m.strip() != the.strip()
    assert len(m.encode()) < len(the.encode()) * 0.6, len(m.encode())


def test_loi_KHONG_neu_phep_nao_thi_khong_bia_manh():
    """Không khớp được gì ⇒ rỗng. Một mảnh SAI dẫn mô hình đi sửa nhầm chỗ."""
    assert manh_hop_dong("", "hinh_hoc") == ""
    # Chuỗi KHÔNG chứa một chạy `[a-z]{4,}` nào — tiếng Việt có dấu không lọt
    # bộ rút định danh, và đó là hành vi có sẵn của bộ chọn.
    assert manh_hop_dong("lỗi ở đâu đó, ??? !!!", "hinh_hoc") == ""


def test_phep_LA_khong_keo_theo_hop_dong_cong(monkeypatch):
    """§21 ca C — một phép không liên quan không được kéo theo hợp đồng hình
    cong."""
    m = manh_hop_dong(
        "statements.0\n  Input tag 'midpoint' found using 'kind'", "hinh_hoc")
    assert "construct_curved_solid" not in m
    assert "curved_kind" not in m


# ══ §19 · KHÔNG ĐỔI CHÍNH SÁCH REPAIR-ELIGIBLE ═══════════════════════════
def test_chinh_sach_repair_eligible_KHONG_doi():
    """Wave này chỉ làm ĐẦY ngữ cảnh cho lỗi VỐN ĐÃ sửa được; không kéo R0,
    runtime, postconditions hay learner_surface vào vòng sửa."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from acceptance_verdict import _STAGE_SUA_DUOC, sua_duoc

    assert set(_STAGE_SUA_DUOC) == {"ir_static", "grounding"}

    class OC:
        stage_reached = "learner_surface"
        servable = False
        error_code = "learner_surface_incomplete"

    ok, ly_do = sua_duoc(OC(), schema_ok=True)
    assert not ok and "NGOÀI vòng sửa" in ly_do


def test_R0_van_KHONG_duoc_sua():
    """§20 — ngữ cảnh sửa tốt hơn không được dùng để nới grounding."""
    from app.ai.pipeline import KHONG_DUOC_SUA

    assert "unanchored_derived_assumption" in {m.lower() for m in KHONG_DUOC_SUA}


# ══ §16 · §17 · §29 — VĂN BẢN THÔ SỐNG SÓT QUA MỌI KIỂU HỎNG ═════════════
class _ThuTho:
    """Observer thụ động tối thiểu — đúng giao diện `emit(name, data)`."""

    def __init__(self) -> None:
        self.su_kien: list[tuple[str, dict]] = []

    def emit(self, ten, data):
        self.su_kien.append((ten, dict(data)))

    def tho(self) -> list[str]:
        return [d["raw"] for t, d in self.su_kien
                if t == "semantic_program_candidate"]


async def _chay_synth_gia(monkeypatch, tra_ve: str):
    """Chạy `_sinh_chuong_trinh` với provider GIẢ trả đúng chuỗi ấy."""
    import app.ai.pipeline as PL
    from app.simulation.semantic_program.request_contract import RequestContract

    async def gia(*a, **k):
        return tra_ve

    monkeypatch.setattr(PL, "call_gemini", gia)
    monkeypatch.setattr(PL, "MAX_SEMANTIC_PROGRAM_ATTEMPTS", 1)
    obs = _ThuTho()
    spec, loi = await PL.stage_semantic_program(
        "Cho A(0;0;0) và B(1;0;0). Tính khoảng cách AB.", {}, "khoa-gia",
        RequestContract(problem_text="Cho A(0;0;0) và B(1;0;0)."),
        observer=obs, domain="hinh_hoc")
    return spec, loi, obs


def test_RAW_song_sot_khi_KHONG_parse_duoc_JSON(monkeypatch):
    """§16 — đầu ra không phải JSON là đúng loại đáng xem nhất."""
    tho = "{đây không phải JSON, mô hình trả văn xuôi"
    spec, loi, obs = asyncio.run(_chay_synth_gia(monkeypatch, tho))
    assert spec is None and loi
    assert obs.tho() == [tho], "văn bản thô mất khi parse hỏng"


def test_RAW_song_sot_khi_JSON_dung_ma_LUOC_DO_hong(monkeypatch):
    """§17 — JSON hợp lệ nhưng không phải `SemanticProgramSpec`."""
    tho = json.dumps({"bad": True, "statements": []}, ensure_ascii=False)
    spec, loi, obs = asyncio.run(_chay_synth_gia(monkeypatch, tho))
    assert spec is None and loi
    assert obs.tho() == [tho], "văn bản thô mất khi lược đồ hỏng"


def test_RAW_phat_TRUOC_khi_parse_va_KHONG_bi_sua(monkeypatch):
    """§13 — dữ liệu quan trắc, byte y nguyên, không ai chỉnh."""
    tho = '  {"statements": [ ] }  \n'
    _, _, obs = asyncio.run(_chay_synth_gia(monkeypatch, tho))
    assert obs.tho() == [tho]
    assert obs.su_kien[0][0] == "semantic_program_candidate", (
        "văn bản thô phải là sự kiện ĐẦU TIÊN của lượt — trước mọi phán quyết")


def test_observer_None_thi_khong_doi_gi(monkeypatch):
    """Đường sản phẩm truyền `observer=None`; `_emit` là no-op."""
    import app.ai.pipeline as PL
    from app.simulation.semantic_program.request_contract import RequestContract

    async def gia(*a, **k):
        return "{"

    monkeypatch.setattr(PL, "call_gemini", gia)
    monkeypatch.setattr(PL, "MAX_SEMANTIC_PROGRAM_ATTEMPTS", 1)
    spec, loi = asyncio.run(PL.stage_semantic_program(
        "đề", {}, "khoa-gia", RequestContract(problem_text="đề"),
        observer=None, domain="hinh_hoc"))
    assert spec is None and loi          # hành vi y như trước


# ══ §30 · RUNNER GIỮ ĐƯỢC THỨ MÔ HÌNH VIẾT ═══════════════════════════════
def test_runner_luu_van_ban_tho_cua_luot_hong_luoc_do():
    """`SCHEMA_FAILURE_RAW_CANDIDATE_PERSISTED` — bộ đo nay giữ được văn bản
    thô, thay vì chỉ giữ `message`."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import run_curved_ergonomics_v2 as R

    qt = R.ThuVanBanTho()
    qt.emit("semantic_program_candidate", {"n": 0, "raw": '{"bad": 1}'})
    qt.emit("semantic_program_attempt", {"n": 0, "message": "hỏng"})
    assert qt.tho == [{"lan": 0, "raw": '{"bad": 1}'}]

    src = (Path(R.__file__)).read_text(encoding="utf-8")
    assert src.count("raw_candidates") >= 2, (
        "cả pass A lẫn pass B đều phải ghi văn bản thô")
