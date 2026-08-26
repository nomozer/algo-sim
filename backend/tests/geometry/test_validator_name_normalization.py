# -*- coding: utf-8 -*-
"""PHASE 6.7.1 — cổng phải dùng TÊN ĐÃ PHÂN GIẢI. **0 API call.**

─── LỖI ĐÃ ĐO ĐƯỢC (Phase 6.7, 2/15 lượt) ─────────────────────────────────

Hợp đồng khai `volume(container="S.ABCD", witness="V_S_ABCD")`. Chương trình
**CÓ TÍNH** thể tích:

    assign V_S_ABCD = measure(volume, of="S_ABCD_solid")

Cổng vẫn từ chối, và lời từ chối **vu oan**:

    "witness 'V_S_ABCD' không dẫn xuất từ 'S.ABCD'
     — chương trình khai đáp án chứ không tính nó"

Lưới hoà giải ĐÃ trả lời xong `S.ABCD ≡ S_ABCD_solid` và gán vào `con`; phép
kiểm dẫn xuất ngay dòng dưới lại tra `ob.container`, tức tra TÊN HỢP ĐỒNG trong
một bao đóng chỉ chứa TÊN CHƯƠNG TRÌNH.

─── VÌ SAO CÓ MỘT TEST BẤT BIẾN, KHÔNG CHỈ HAI TEST HIỆN TRƯỜNG ──────────

Đây là lần THỨ BA cùng một lớp lỗi: lưới áp ở cổng này mà không áp ở cổng kia
(C₁a có, C₂ không → sửa; `_semantic_shadow` có, cổng phạm vi đường module không
→ sửa; nay C₁a nửa trong nửa ngoài, và C₁b cũng thiếu).

Hai test hiện trường chỉ chặn đúng hai chỗ đã biết. `test_DOI_TEN_KHONG_DOI_PHAN_
QUYET` chặn CẢ LỚP: đổi tên mọi vật dựng mà giữ nguyên topology thì phán quyết
phải y hệt — bất kể có bao nhiêu cổng và cổng nào đọc tên gì.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import RequestContract
from app.simulation.semantic_program.route import verify_and_compile

GOC = Path(__file__).resolve().parents[3]
DO = GOC / "docs" / "evaluation" / "geometry" / "stability-6.7"


def _hd(rc: dict) -> RequestContract:
    return RequestContract(
        obligations=tuple(
            Obligation(kind=o["kind"], container=o["container"],
                       params=o.get("params") or {})
            for o in rc["obligations"]),
        input_facts=(),
    )


def _luot(ten: str) -> tuple[RequestContract, SemanticProgramSpec]:
    d = json.loads((DO / f"{ten}.json").read_text(encoding="utf-8"))
    return _hd(d["request_contract"]), \
        SemanticProgramSpec.model_validate(d["generated_program"])


# ══ HIỆN TRƯỜNG THẬT — hai lượt Phase 6.7 đã trượt oan ═══════════════════
@pytest.mark.parametrize("ten", ["2-the-tich-lan2", "2-the-tich-lan3"])
def test_luot_tung_TRUOT_OAN_nay_PHAI_QUA(ten):
    """IR thật của lượt đo, không phải spec viết cho vừa test.

    Cả hai lượt: `construct_solid` vào một tên khác `S.ABCD`, rồi
    `measure(volume, of=<tên ấy>)`. Đó là cách làm ĐÚNG.
    """
    hd, spec = _luot(ten)
    kq = verify_and_compile(hd, spec)
    assert kq.executable, f"{kq.stage_reached}: {kq.details}"
    assert kq.servable, kq.details


@pytest.mark.parametrize("ten", ["2-the-tich-lan2", "2-the-tich-lan3"])
def test_dap_an_dung_12_chu_khong_chi_QUA_CONG(ten):
    """Qua cổng mà ra số sai thì bản vá này chỉ mở đường cho một lỗi khác.
    `1/3 · 3² · 4 = 12`, kiểm tay."""
    hd, spec = _luot(ten)
    assert str((verify_and_compile(hd, spec).final_memory or {})
               .get("V_S_ABCD")) == "12"


# ══ BẤT BIẾN: ĐỔI TÊN KHÔNG ĐƯỢC ĐỔI PHÁN QUYẾT ═════════════════════════
#: Hậu tố dùng để đổi tên. Mỗi cái phải NẰM TRONG `_PHU_TO_KIEU` — và có test
#: khẳng định điều đó.
#:
#: ─── VÌ SAO KHÔNG BỊA HẬU TỐ ────────────────────────────────────────────
#:
#: Bản nháp dùng `_pt` cho `point3`, và bất biến đỏ. Đọc kỹ thì ĐỎ OAN: `pt`
#: không nằm trong danh sách phụ tố đã quan sát được, nên không lưới nào hoà
#: giải nổi — và thêm nó vào danh sách là "alias thủ công theo lỗi", đúng thứ
#: Phase 6.6 cấm và một test đang ghim độ dài danh sách để chặn.
#:
#: Bất biến này kiểm **CÁC CỔNG CÓ NHẤT QUÁN VỚI NHAU KHÔNG**, không kiểm lưới
#: phủ được bao nhiêu cách viết. Hai câu hỏi khác nhau: câu sau bị chặn bởi bằng
#: chứng (chỉ thêm phụ tố khi quan sát được mô hình dùng nó), câu trước thì
#: không — mọi cổng phải nhất quán, luôn luôn.
_HAU_TO = {"line3": "_line", "plane3": "_plane", "solid": "_solid",
           "polygon3": "_mat", "point3": "_point", "vector3": "_vector"}


def _doi_ten(spec: SemanticProgramSpec) -> SemanticProgramSpec:
    """Đổi tên MỌI vật DỰNG RA, giữ nguyên topology và mọi thứ khác.

    Chỉ đụng `target_var` của các câu lệnh dựng và khai báo tương ứng — điểm gốc
    giữ nguyên tên, vì chúng là thứ hợp đồng dùng để nói về topology.
    """
    kieu = {d.name: d.type for d in spec.memory_declarations}
    # ─── ĐỔI TÊN VẬT DỰNG, KHÔNG ĐỔI TÊN ĐẠI LƯỢNG VÔ HƯỚNG ────────────────
    #
    # Chỉ vật dựng bằng `construct_*` mới có TOPOLOGY, tức mới có đường phân
    # giải nguyên tắc. Một `float` sinh bằng `assign` thì danh tính CHÍNH LÀ cái
    # tên — đòi hệ hoà giải `V_S_ABCD ≡ V_total` là đòi khớp mờ, đúng thứ Phase
    # 6.6 đã cấm. Bất biến phải mạnh đúng mức, mạnh quá thì nó đòi một thứ sai.
    tao_ra = {st.target_var for st in spec.statements
              if getattr(st, "kind", "").startswith("construct")}
    doi = {t: t + _HAU_TO.get(kieu.get(t, ""), "_x") for t in tao_ra}

    raw = spec.model_dump(mode="json")
    van = json.dumps(raw, ensure_ascii=False)
    for cu, moi in sorted(doi.items(), key=lambda x: -len(x[0])):
        van = van.replace(f'"{cu}"', f'"{moi}"')
    return SemanticProgramSpec.model_validate(json.loads(van))


def _moi_luot_da_served() -> list[str]:
    """MỌI artifact từng `served`, gom từ mọi vòng đo.

    ⚠️ Đây là chỗ bất biến này TỪNG THỦNG, và nó thủng vì CORPUS chứ không vì
    logic. Bản đầu chỉ chạy trên hai lượt bài thể tích, nơi witness (`V_S_ABCD`)
    sinh bằng `assign` nên không bao giờ bị đổi tên — tức tên witness trong test
    không bao giờ khác tên hợp đồng.

    Bài thiết diện thì khác: witness `Q` sinh bằng `construct_point`, tức nó CÓ
    bị đổi tên. Đúng ca ấy đã lộ ra `check_learner_surface` là cổng THỨ TƯ chưa
    nhận ánh xạ — và bất biến cũ không thấy vì nó chưa từng đọc bài thiết diện.
    Nay nó đọc MỌI lượt đã served, nên corpus không tự thu hẹp được nữa.
    """
    ra = []
    for f in sorted(GOC.glob("docs/evaluation/geometry/*/[0-9]*-lan*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d["ban_ghi"].get("servable") and d.get("generated_program"):
            ra.append(str(f))
    return ra


@pytest.mark.parametrize("duong", _moi_luot_da_served(),
                         ids=lambda p: Path(p).stem)
def test_DOI_TEN_KHONG_DOI_PHAN_QUYET(duong):
    """BẤT BIẾN chặn CẢ LỚP lỗi, không chặn từng ca.

    Đổi tên mọi vật dựng mà giữ nguyên topology ⇒ mọi cổng phải cho cùng một
    phán quyết. Cổng nào còn đọc tên gốc của hợp đồng sẽ lệch ở đây, bất kể nó
    nằm ở C₁a, C₁b, C₂, `learner_surface` hay một cổng chưa ai viết.
    """
    d = json.loads(Path(duong).read_text(encoding="utf-8"))
    hd = RequestContract.model_validate(d["request_contract"])
    spec = SemanticProgramSpec.model_validate(d["generated_program"])
    goc = verify_and_compile(hd, spec)
    moi = verify_and_compile(hd, _doi_ten(spec))
    assert (moi.executable, moi.servable) == (goc.executable, goc.servable), (
        f"đổi tên làm đổi phán quyết: {goc.stage_reached} → {moi.stage_reached} "
        f"· {moi.details}"
    )


def test_HAU_TO_deu_DAN_TU_danh_sach_phu_to_that():
    """Nếu test tự bịa hậu tố thì nó đo lưới, không đo cổng — và sẽ đỏ oan."""
    from app.simulation.semantic_program.domain_profile import _PHU_TO_KIEU

    for kieu, h in _HAU_TO.items():
        assert h.lstrip("_") in _PHU_TO_KIEU, f"{kieu} → {h} không phải phụ tố thật"


@pytest.mark.parametrize("ten", ["2-the-tich-lan2", "2-the-tich-lan3"])
def test_DOI_TEN_van_ra_dung_dap_so(ten):
    hd, spec = _luot(ten)
    moi = verify_and_compile(hd, _doi_ten(spec))
    assert str((moi.final_memory or {}).get("V_S_ABCD")) == "12"


def test_C1b_cung_nhan_anh_xa():
    """C₁b tra `realized` — một tập TÊN CHƯƠNG TRÌNH. Không đổi tên trước khi
    tra thì mọi nghĩa vụ từng phải hoà giải bị báo "chưa hiện thực hoá" dù biến
    ấy có giá trị thật trong mọi bước."""
    import inspect

    from app.simulation.semantic_program.coverage_gate import (
        check_realized_coverage,
    )

    assert "ten_da_hoa_giai" in inspect.signature(
        check_realized_coverage).parameters
    from app.simulation.semantic_program import route

    assert "ten_da_hoa_giai=c1a.ten_da_hoa_giai" in inspect.getsource(
        route.verify_and_compile) or "ten_da_hoa_giai=c1a" in inspect.getsource(
        route)


# ══ R0 KHÔNG ĐƯỢC YẾU ĐI ═══════════════════════════════════════════════
def _spec_khai_dap_an() -> SemanticProgramSpec:
    """Chương trình KHAI THẲNG thể tích thay vì đo — đúng thứ cổng sinh ra để
    chặn, và bản vá này KHÔNG được mở đường cho nó."""
    return SemanticProgramSpec.model_validate({
        "title": "khai thang dap an",
        # `model_assumption` cho ĐIỂM GỐC — nếu không, grounding chặn trước và
        # test này không bao giờ tới được cổng phủ, tức nó xanh vì lý do sai.
        "memory_declarations": [
            {"name": n, "type": "point3", "initial_value": v,
             "model_assumption": "chọn hệ trục"} for n, v in
            [("A", [0, 0, 0]), ("B", [3, 0, 0]), ("C", [3, 3, 0]),
             ("D", [0, 3, 0]), ("S", [0, 0, 4])]
        ] + [{"name": "S_ABCD_solid", "type": "solid"},
             {"name": "V_S_ABCD", "type": "float"}],
        "statements": [
            {"kind": "construct_solid", "target_var": "S_ABCD_solid",
             "vertices": ["S", "A", "B", "C", "D"],
             "faces": [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]]},
            {"kind": "assign", "target_var": "V_S_ABCD",
             "expr": {"kind": "literal", "value": 12}},
        ],
    })


def test_KHAI_THANG_DAP_AN_van_bi_chan():
    """Vế thứ hai của bản vá, và là vế quan trọng hơn: cổng vẫn phải từ chối
    một chương trình gán thẳng đáp số — kể cả khi đáp số ấy ĐÚNG (12).

    ⚠️ Đọc kèm `test_GROUNDING_khong_bi_dung_toi`: bản nháp đầu của test này
    KHÔNG khai `model_assumption`, và nó "xanh" vì grounding chặn trước — tức
    xanh vì một lý do KHÁC với lý do nó được viết ra. Một test chặn đúng chỗ
    nhưng vì lý do sai là một test sẽ mất hiệu lực lặng lẽ."""
    hd = RequestContract(obligations=(
        Obligation(kind="volume", container="S.ABCD",
                   params={"witness": "V_S_ABCD"}),))
    kq = verify_and_compile(hd, _spec_khai_dap_an())
    assert not kq.servable
    assert any("khai đáp án" in d for d in kq.details), kq.details


def test_loi_tu_choi_NEU_CA_HAI_TEN_khi_da_hoa_giai():
    """Wave 3 đã học một lần: thông điệp chỉ nói tên một phía thì lượt phân tích
    sau phải chạy forensics. Nay nó nói `'S.ABCD' (≡ 'S_ABCD_solid')`."""
    hd = RequestContract(obligations=(
        Obligation(kind="volume", container="S.ABCD",
                   params={"witness": "V_S_ABCD"}),))
    d = verify_and_compile(hd, _spec_khai_dap_an()).details
    assert any("S.ABCD" in x and "S_ABCD_solid" in x for x in d), d


def test_GROUNDING_khong_bi_dung_toi():
    """Bản vá chỉ chạm cổng PHỦ. Grounding (P2) phải nguyên vẹn: một khai báo có
    `initial_value` mà thiếu cả `source_fact_id` lẫn `model_assumption` vẫn phải
    bị chặn."""
    from app.simulation.semantic_program.grounding_gate import check_grounding

    spec = SemanticProgramSpec.model_validate({
        "title": "thieu xuat xu",
        "memory_declarations": [
            {"name": "A", "type": "point3", "initial_value": [0, 0, 0]}],
        "statements": [],
    })
    hd = RequestContract(obligations=(), input_facts=())
    assert not check_grounding(hd, spec).ok


def test_model_assumption_KHONG_duoc_mang_dap_an():
    """Khoá riêng điều Phase 6.7.1 nêu: `model_assumption` là kênh cho GIẢ THIẾT
    MÔ HÌNH HOÁ (chọn hệ trục), không phải cửa sau cho đáp số."""
    from app.simulation.semantic_program.grounding_gate import check_grounding

    spec = SemanticProgramSpec.model_validate({
        "title": "gia thiet mang dap an",
        "memory_declarations": [
            {"name": "A", "type": "point3", "initial_value": [0, 0, 0],
             "model_assumption": "chọn A làm gốc"},
            {"name": "V", "type": "float", "initial_value": 12,
             "model_assumption": "giả thiết thể tích"},
        ],
        "statements": [],
    })
    hd = RequestContract(obligations=(
        Obligation(kind="volume", container="S", params={"witness": "V"}),),
        input_facts=())
    assert not check_grounding(hd, spec).ok
