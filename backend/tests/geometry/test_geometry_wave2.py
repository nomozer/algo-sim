# -*- coding: utf-8 -*-
"""Wave 2 — mỗi nguyên nhân thất bại của PHASE 5 có một test khoá. **0 API call.**

Bốn nguyên nhân đo được ngày 2026-08-24 trên 10 bài DEV, và **không cái nào là
"mô hình suy luận hình học sai"**:

    5 ca  `input_not_grounded`   hợp đồng mâu thuẫn với miền   → §2
    2 ca  `construct_plane` bịa   IR thiếu phép dựng            → §3
    3 ca  `type: "volume"`        lẫn hai taxonomy              → §4
    3 lệch obligation             `analyze` vẫn là prompt Tin học → §1

Nguyên nhân thứ NĂM lộ ra khi audit, chưa từng hiện trong Phase 5 vì bị che sau
lỗi schema: IR **không có phép ĐO**, nên `distance`/`angle`/`volume` — 3/8 nghĩa
vụ, phủ 4/10 bài — không có cách nào đưa một con số vào witness (§5).

Test ở đây kiểm HỢP ĐỒNG, không kiểm mô hình. Chúng không nói lượt đo sau sẽ
tốt hơn; chúng nói bốn cái bẫy ấy không còn nằm trên đường đi.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.simulation.geometry import Line3, Plane3, Vec3
from app.simulation.semantic_program import domain_profile as DP
from app.simulation.semantic_program.analyze_contract import (
    analyze_schema_for,
    build_request_contract,
)
from app.simulation.semantic_program.contract import (
    MemoryDeclaration,
    SemanticProgramSpec,
)
from app.simulation.semantic_program.coverage_gate import _phu_thuoc, _producers
from app.simulation.semantic_program.grounding_gate import (
    ERR_GIA_THIET_LA_DAP_AN,
    ERR_GIA_THIET_SAI_KIEU,
    check_grounding,
)
from app.simulation.semantic_program.obligations import OBLIGATION_KINDS, Obligation
from app.simulation.semantic_program.request_contract import InputFact, RequestContract

_GOC = Path(__file__).resolve().parents[3]
_DEV = _GOC / "docs" / "evaluation" / "geometry" / "dev" / "cases.json"

#: Ba nghĩa vụ TIN HỌC mà mô hình đã khai nhầm cho bài hình học ở Phase 5.
_NGHIA_VU_TIN_HOC_DA_LAN = ("derived_sequence", "structural_traversal",
                            "predicate_verdict")


# ══ §1. ĐỊNH TUYẾN ANALYZE THEO MIỀN ══════════════════════════════════════
def test_enum_nghia_vu_hinh_hoc_KHONG_chua_nghia_vu_tin_hoc():
    """Đây là ca hồi quy trực tiếp của `obligation_match` 3/6."""
    enum = analyze_schema_for(DP.DOMAIN_HINH_HOC)[
        "properties"]["obligations"]["items"]["properties"]["kind"]["enum"]
    lan = [k for k in _NGHIA_VU_TIN_HOC_DA_LAN if k in enum]
    assert not lan, f"nghĩa vụ Tin học lọt vào enum hình học: {lan}"
    # 8 → 9 ngày 2026-08-30: `section_matches`. Số này DẪN TỪ taxonomy chứ
    # không chép, nếu không thì nó chỉ đo được chính nó.
    assert len(enum) == len(DP.geometry_obligation_kinds()) == 9
    assert "section_matches" in enum


def test_server_LOC_nghia_vu_sai_mien_du_LLM_van_khai():
    """Enum là LỜI ĐỀ NGHỊ gửi cho model; bộ lọc này mới là thứ cưỡng chế.

    Cần cả hai: structured-output không đảm bảo model tôn trọng enum, và Phase 5
    cho thấy nó khai ra ngoài từ vựng thật (`construct_plane`, `type: volume`).
    """
    payload = {
        "input_facts": [],
        "obligations": [
            {"kind": "derived_sequence", "container": "day", "witness": "kq"},
            {"kind": "point_on_plane", "container": "day", "witness": "m"},
        ],
    }
    hd = build_request_contract(payload, domain=DP.DOMAIN_HINH_HOC)
    assert [o.kind for o in hd.obligations] == ["point_on_plane"]


def test_khong_truyen_domain_thi_KHONG_LOC_gi_ca():
    """Đường Tin học phải nguyên vẹn — `None` = hành vi trước Wave 2."""
    payload = {
        "input_facts": [],
        "obligations": [
            {"kind": "derived_sequence", "container": "day", "witness": "kq"}
        ],
    }
    assert len(build_request_contract(payload).obligations) == 1


def test_taxonomy_chia_DU_va_KHONG_CHONG_LAN():
    geo, tin = DP.geometry_obligation_kinds(), DP.tin_hoc_obligation_kinds()
    assert geo | tin == set(OBLIGATION_KINDS), "có nghĩa vụ rơi khỏi cả hai miền"
    assert not (geo & tin), f"nghĩa vụ nằm ở cả hai miền: {sorted(geo & tin)}"


def test_hai_mien_dung_HAI_SKILL_khac_nhau():
    assert DP.analyze_skill_for(DP.DOMAIN_HINH_HOC) == "geometry_analyze"
    assert DP.analyze_skill_for(DP.DOMAIN_TIN_HOC) == "semantic_analyze"
    for ten in ("geometry_analyze", "semantic_analyze"):
        assert (_GOC / "backend" / "app" / "ai" / "skills" / f"{ten}.md").exists()


def test_prescribed_procedure_VANG_MAT_o_mien_hinh_hoc():
    """Đề hình học không "ép thuật toán". Để trường ấy ở đó là mời model điền
    một cơ chế mà đề không hề đòi — đúng lỗi `prescribed_procedure` bịa."""
    assert "prescribed_procedure" not in analyze_schema_for(
        DP.DOMAIN_HINH_HOC)["properties"]
    assert "prescribed_procedure" in analyze_schema_for(
        DP.DOMAIN_TIN_HOC)["properties"]


@pytest.mark.parametrize("case", json.loads(_DEV.read_text(encoding="utf-8"))["cases"])
def test_moi_de_DEV_duoc_nhan_dung_mien(case):
    """Bộ nhận miền phải bắt được cả 10 bài — kể cả `geo_08` (hình vuông phẳng,
    không có cụm mạnh nào)."""
    assert DP.detect_domain(case["problem_text"]) == DP.DOMAIN_HINH_HOC, (
        f"{case['case_id']} bị nhận nhầm sang Tin học"
    )


@pytest.mark.parametrize("de", [
    "Cho dãy số nguyên A gồm n phần tử. Tìm phần tử lớn nhất của dãy.",
    "Viết chương trình kiểm tra một chuỗi dấu ngoặc {[()]} có cân bằng không "
    "bằng ngăn xếp.",
    "Cho một cây nhị phân. Hãy duyệt cây theo thứ tự giữa.",
    "Tính tổng S = 1 + 2 + ... + n với n nhập từ bàn phím.",
    "Sắp xếp dãy số bằng thuật toán sắp xếp nổi bọt và in ra từng bước.",
])
def test_de_TIN_HOC_khong_bi_keo_sang_hinh_hoc(de):
    """Bộ nhận miền fail-safe về phía Tin học. Cửa duy nhất nó mở là cửa đi
    sang hình học, nên 24 target Tin học không thể bị nó làm hỏng."""
    assert DP.detect_domain(de) == DP.DOMAIN_TIN_HOC


# ══ §2. GIẢ THIẾT MÔ HÌNH HOÁ vs DỮ KIỆN ĐỀ CHO ═══════════════════════════
def _spec(decls: list[dict], stmts: list[dict] | None = None) -> SemanticProgramSpec:
    return SemanticProgramSpec(
        spec_version="1.0",
        title="Chương trình kiểm thử Wave 2",
        description="d",
        pedagogical_intent="p",
        memory_declarations=[MemoryDeclaration(**d) for d in decls],
        statements=stmts or [],
    )


_HD_RONG = RequestContract()


def test_PASS_toa_do_do_mo_hinh_chon_co_ly_do():
    """Ca chặn 5/10 bài Phase 5. Đề hình học không cho toạ độ; prompt bảo mô
    hình tự đặt hệ trục; cổng cũ hỏi "lấy dữ liệu này ở đâu ra?"."""
    kq = check_grounding(_HD_RONG, _spec([
        {"name": "A", "type": "point3", "initial_value": [0, 0, 0],
         "model_assumption": "chọn A làm gốc vì SA vuông góc đáy"},
        {"name": "B", "type": "point3", "initial_value": [1, 0, 0],
         "model_assumption": "cạnh đáy dọc trục x"},
    ]))
    assert kq.ok, kq.unresolved
    assert len(kq.assumptions) == 2, "giả thiết phải ĐẾM ĐƯỢC, không lặng lẽ qua"


def test_FAIL_khai_DAP_AN_lam_gia_thiet():
    """Chốt cứng nhất của kênh. Không có nó thì `model_assumption` là một cái
    cửa để tuồn đáp án vào, và toàn bộ R0 ở miền này mất hiệu lực."""
    hd = RequestContract(obligations=(
        Obligation(kind="point_on_plane", container="day",
                   params={"witness": "H"}),
    ))
    kq = check_grounding(hd, _spec([
        {"name": "H", "type": "point3", "initial_value": [0, 0, 0],
         "model_assumption": "hình chiếu của S là A"},
    ]))
    assert not kq.ok
    assert kq.error_code == ERR_GIA_THIET_LA_DAP_AN
    assert not kq.assumptions


def test_FAIL_gia_thiet_tren_DAI_LUONG():
    """`float` là chỗ đáp án sống. Cho nó mang giả thiết là mở đúng cửa vừa
    đóng ở test trên, chỉ khác lối vào."""
    kq = check_grounding(_HD_RONG, _spec([
        {"name": "V", "type": "float", "initial_value": "2/3",
         "model_assumption": "thể tích khối chóp"},
    ]))
    assert not kq.ok and kq.error_code == ERR_GIA_THIET_SAI_KIEU


def test_FAIL_gia_thiet_tren_MAT_PHANG():
    """Mặt phẳng phải được DỰNG từ điểm. Khai thẳng toạ độ nó là có hai bản
    toạ độ cho cùng một hình, và bản thứ hai do LLM viết."""
    kq = check_grounding(_HD_RONG, _spec([
        {"name": "mp", "type": "plane3",
         "initial_value": {"through": [[0, 0, 0], [1, 0, 0], [0, 1, 0]]},
         "model_assumption": "mặt đáy"},
    ]))
    assert not kq.ok and kq.error_code == ERR_GIA_THIET_SAI_KIEU


def test_FAIL_gia_thiet_KHONG_CO_LY_DO():
    kq = check_grounding(_HD_RONG, _spec([
        {"name": "A", "type": "point3", "initial_value": [1, 2, 3],
         "model_assumption": "   "},
    ]))
    assert not kq.ok and not kq.assumptions


def test_source_fact_id_VAN_THANG_khi_khai_ca_hai():
    """Ghim được về đề thì đi đường CŨ, nghiêm ngặt như trước. Giả thiết không
    phải một lối tắt để né kiểm."""
    hd = RequestContract(input_facts=(
        InputFact(fact_id="sa", label="SA", values=(2,)),
    ))
    kq = check_grounding(hd, _spec([
        {"name": "h", "type": "int", "initial_value": 2, "source_fact_id": "sa",
         "model_assumption": "chiều cao"},
    ]))
    assert kq.ok and not kq.assumptions, "đã ghim được thì không tính là giả thiết"

    xau = check_grounding(hd, _spec([
        {"name": "h", "type": "int", "initial_value": 99, "source_fact_id": "sa",
         "model_assumption": "chiều cao"},
    ]))
    assert not xau.ok, "giả thiết KHÔNG được cứu một giá trị ghim sai"


def test_KHONG_khai_gia_thiet_thi_van_bi_tu_choi_nhu_cu():
    """Kênh này là OPT-IN. Im lặng bịa một toạ độ vẫn trượt — Wave 2 mở một cửa
    có khai báo, không tháo cổng."""
    kq = check_grounding(_HD_RONG, _spec([
        {"name": "A", "type": "point3", "initial_value": [0, 0, 0]},
    ]))
    assert not kq.ok and kq.error_code == "INPUT_NOT_GROUNDED"


# ══ §3. PRIMITIVE DỰNG MỚI ════════════════════════════════════════════════
_MP = {"kind": "construct_plane", "target_var": "mp",
       "through": ["A", "B", "C"]}
_KHOI = {"kind": "construct_solid", "target_var": "chop",
         "vertices": ["A", "B", "C", "D", "S"],
         "faces": [[0, 1, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]]}


def test_construct_plane_va_solid_DUOC_NHAN():
    """2/10 bài Phase 5 bịa đúng hai `kind` này — không phải sáng tác, mà là
    thiếu từ để nói `(SBC)`."""
    s = _spec([{"name": n, "type": "point3", "initial_value": [0, 0, 0],
                "model_assumption": "gốc"} for n in "ABCDS"], [_MP, _KHOI])
    assert {st.kind for st in s.statements} == {"construct_plane", "construct_solid"}


def test_construct_plane_dung_DUNG_BA_diem():
    for so in ([{"kind": "construct_plane", "target_var": "mp",
                 "through": ["A", "B"]}],
               [{"kind": "construct_plane", "target_var": "mp",
                 "through": ["A", "B", "C", "D"]}]):
        with pytest.raises(ValidationError):
            _spec([], so)


def test_phu_thuoc_va_producer_cua_hai_primitive_moi():
    """Thiếu nửa nào cũng từ chối oan: `_producers` thiếu ⇒ C₁a báo "witness
    không có producer"; `_phu_thuoc` thiếu ⇒ C₁b báo "khai đáp án chứ không
    tính nó". Đúng cặp lỗ đã vá cho ba primitive đầu."""
    stmts = _spec([{"name": n, "type": "point3"} for n in "ABCDS"],
                  [_MP, _KHOI]).statements
    assert _producers(stmts) == {"mp", "chop"}
    pt = _phu_thuoc(stmts, frozenset())
    assert pt["mp"] == {"A", "B", "C"}
    assert pt["chop"] == {"A", "B", "C", "D", "S"}


def test_validator_bat_ten_chua_khai_trong_phep_dung_moi():
    from app.simulation.semantic_program.validator import validate_semantic_program

    s = _spec([{"name": n, "type": "point3", "initial_value": [0, 0, 0],
                "model_assumption": "g"} for n in "AB"], [_MP])
    kq = validate_semantic_program(json.loads(s.model_dump_json()))
    assert not kq.ok and "C" in kq.error


def test_construct_solid_bat_chi_so_mat_NGOAI_BIEN():
    """`faces` là thứ LLM viết ra, nên chỉ số ngoài biên là ca THƯỜNG GẶP.
    `IndexError` trần thì không nói được đỉnh nào thiếu."""
    from app.simulation.geometry import GeometryError
    from app.simulation.semantic_program.geometry_exec import exec_construct_solid

    class N:
        target_var, label = "k", None
        vertices = ["A", "B", "C", "D"]
        faces = [[0, 1, 2], [0, 1, 9], [0, 2, 3], [1, 2, 3]]

    mem = {n: Vec3.of(i, 0, 0) for i, n in enumerate("ABCD")}
    with pytest.raises(GeometryError, match="ngoài khoảng"):
        exec_construct_solid(N(), mem)


# ══ §4. HAI TAXONOMY, HAI KHÔNG GIAN TÊN ══════════════════════════════════
@pytest.mark.parametrize("ten", sorted(OBLIGATION_KINDS))
def test_KHONG_nghia_vu_nao_dung_duoc_lam_MemoryType(ten):
    with pytest.raises(ValidationError) as e:
        MemoryDeclaration(name="x", type=ten)
    assert "NGHĨA VỤ" in str(e.value), "thông điệp phải DẠY LẠI, không chỉ từ chối"


def test_thong_diep_chi_ro_kieu_DUNG_de_vong_sua_lam_duoc_gi():
    """Vòng sửa ≤3 lượt chỉ hữu ích nếu lỗi nói được phải sửa thành gì. Đây là
    lý do từ chối tại biên tốt hơn đổi tên nghĩa vụ: đổi tên chỉ dời đích va
    chạm, còn thông điệp này đóng hẳn."""
    with pytest.raises(ValidationError) as e:
        MemoryDeclaration(name="V", type="volume")
    txt = str(e.value)
    assert "float" in txt and "bool" in txt and "solid" in txt


def test_KHONG_ep_kieu_am_tham():
    """`volume` → `float` nghe tiện nhưng là ĐOÁN. Mỗi lần đoán đúng là một lần
    che mất việc mô hình đang hiểu sai cấu trúc."""
    with pytest.raises(ValidationError):
        MemoryDeclaration(name="V", type="volume")


def test_kieu_hop_le_KHONG_bi_cham():
    for t in ("float", "bool", "point3", "solid", "array", "plane3"):
        assert MemoryDeclaration(name="x", type=t).type == t


# ══ §5. PHÉP ĐO — nguyên nhân thứ NĂM, audit lộ ra ════════════════════════
def _do(quantity: str, of: str, wrt: str | None, mem: dict):
    from app.simulation.semantic_program.geometry_exec import eval_geometry_expr

    class N:
        pass

    n = N()
    n.quantity, n.of, n.wrt = quantity, of, wrt
    return eval_geometry_expr("measure", n, mem)


def _chop_vuong(canh=1, cao=2):
    """Chóp S.ABCD đáy vuông cạnh `canh`, SA ⊥ đáy, SA = `cao`. V = c²·h/3."""
    from app.simulation.geometry.section import Polyhedron

    v = (Vec3.of(0, 0, 0), Vec3.of(canh, 0, 0), Vec3.of(canh, canh, 0),
         Vec3.of(0, canh, 0), Vec3.of(0, 0, cao))
    return Polyhedron(vertices=v,
                      faces=((0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4),
                             (3, 0, 4)))


def test_do_THE_TICH_chinh_xac_bang_phan_so():
    """`geo_09`: đáy vuông cạnh 1, SA = 2 ⇒ V = 2/3. Trước Wave 2 không có
    cách nào đưa con số này vào witness."""
    assert _do("volume", "k", None, {"k": _chop_vuong()}) == Fraction(2, 3)


def test_do_KHOANG_CACH_diem_den_mat_phang():
    """`geo_07`: SA ⊥ đáy, SA = 2 ⇒ d(S, (ABCD)) = 2."""
    day = Plane3.through(Vec3.of(0, 0, 0), Vec3.of(1, 0, 0), Vec3.of(0, 1, 0))
    kq = _do("distance", "S", "day", {"S": Vec3.of(0, 0, 2), "day": day})
    assert kq == Fraction(2)


def test_do_GOC_tra_ve_COS_BINH_khong_tra_ve_do():
    """`geo_08`: góc giữa cạnh và đường chéo hình vuông = 45°, cos² = 1/2.
    Trả về độ là ép một phép làm tròn vào giữa chuỗi tất định."""
    ab = Line3.through(Vec3.of(0, 0, 0), Vec3.of(1, 0, 0))
    ac = Line3.through(Vec3.of(0, 0, 0), Vec3.of(1, 1, 0))
    assert _do("angle_cos_sq", "ab", "ac", {"ab": ab, "ac": ac}) == Fraction(1, 2)


def test_khoang_cach_VO_TI_ra_CAN_THUC_khong_lam_tron():
    """Một `√2` lặng lẽ thành `1.414…` là đúng cách sai số float quay lại qua
    cửa sau, sau khi cả kernel đã dựng bằng `Fraction` để tránh nó.

    2026-08-31 — điều ĐỔI là hệ thôi TỪ CHỐI; điều KHÔNG đổi là nó vẫn không
    làm tròn. Hai chuyện khác nhau, và bản cũ gộp chúng làm một.
    """
    from app.simulation.geometry.radical import Radical, radical, square

    mem = {"a": Vec3.of(0, 0, 0), "b": Vec3.of(1, 1, 0)}
    d = _do("distance", "a", "b", mem)
    assert d == radical(1, 2)
    assert isinstance(d, Radical) and square(d) == 2


def test_measure_KHONG_nhan_duoc_mot_con_so_nao_tu_IR():
    """R0 ở miền này: mọi trường của `measure` là TÊN. Thêm một trường `value`
    để "cho nhanh" là LLM sở hữu kết quả, và luận điểm đề tài mất hiệu lực."""
    from app.simulation.semantic_program.contract import MeasureExpr

    truong = {t for t in MeasureExpr.model_fields if t != "kind"}
    assert truong == {"quantity", "of", "wrt"}
    for t in ("of", "wrt"):
        assert MeasureExpr.model_fields[t].annotation in (str, str | None)


def test_assign_tu_MEASURE_ghi_nhan_PHU_THUOC():
    """Trường của `measure` là CHUỖI TRẦN nên `_doc` không thấy. Bỏ sót thì mọi
    đại lượng đo được đều bị C₁b kết tội "khai đáp án chứ không tính nó" —
    đúng thứ nó vừa tính xong."""
    s = _spec(
        [{"name": "chop", "type": "solid"}, {"name": "V", "type": "float"}],
        [{"kind": "assign", "target_var": "V",
          "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}}],
    )
    assert _phu_thuoc(s.statements, frozenset())["V"] == {"chop"}


def test_C2_TINH_LAI_the_tich_va_bat_witness_khai_sai():
    """Hình dạng witness MỚI mạnh hơn hình dạng cũ: cổng tính lại đại lượng từ
    HÌNH rồi so với con số chương trình khai. Hình dạng cũ chỉ so được với con
    số do `analyze` khai — tức so lời một model với lời chính model ấy."""
    from app.simulation.semantic_program.geometry_obligations import check_volume

    ob = Obligation(kind="volume", container="k", params={"witness": "V"})
    assert check_volume({"k": _chop_vuong(), "V": Fraction(2, 3)}, ob) is None
    loi = check_volume({"k": _chop_vuong(), "V": Fraction(1)}, ob)
    assert loi and "khai V = 1" in loi


def test_C2_giu_nguyen_hinh_dang_WITNESS_CU():
    """Không hồi quy: witness là ĐỐI TƯỢNG thì đi đường cũ, so với `params`."""
    from app.simulation.semantic_program.geometry_obligations import check_distance

    day = Plane3.through(Vec3.of(0, 0, 0), Vec3.of(1, 0, 0), Vec3.of(0, 1, 0))
    ob = Obligation(kind="distance", container="day",
                    params={"witness": "S", "value": "2"})
    assert check_distance({"day": day, "S": Vec3.of(0, 0, 2)}, ob) is None
    assert check_distance({"day": day, "S": Vec3.of(0, 0, 5)}, ob)


def test_MOT_nguon_su_that_cho_the_tich():
    """`measure` và `check_volume` dùng CHUNG hàm. Hai bản rời nhau sẽ lệch, và
    lệch CÂM vì cả hai đều "chạy ra một con số"."""
    import ast

    p = (_GOC / "backend" / "app" / "simulation" / "semantic_program"
         / "geometry_obligations.py")
    than = next(
        n for n in ast.walk(ast.parse(p.read_text(encoding="utf-8")))
        if isinstance(n, ast.FunctionDef) and n.name == "check_volume"
    )
    goi = {n.func.id for n in ast.walk(than)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "volume_polyhedron" in goi, "check_volume cài lại phép tính thể tích"


# ══ §6. ĐI TRỌN ĐƯỜNG — bằng chứng OFFLINE, không phải dự đoán ════════════
#
# Test dưới đây là thứ duy nhất ở file này trả lời được câu *"bốn cái bẫy có
# thật sự đã rời khỏi đường đi chưa"*. Năm test nhóm trên kiểm từng mảnh; test
# này dựng một chương trình `geo_09` viết TAY (không có LLM) rồi thả qua đúng
# chuỗi cổng của sản phẩm.
#
# NÓ KHÔNG NÓI GÌ VỀ MÔ HÌNH. Chương trình này do người viết, nên nó chứng minh
# **đường đi thông**, không chứng minh **LLM đi được**. Câu sau chỉ có lượt đo
# Phase 5 kế tiếp mới trả lời được.
def _chuong_trinh_geo_09() -> dict:
    """`geo_09`: chóp S.ABCD đáy vuông cạnh 1, SA ⊥ đáy, SA = 2. Tính V.

    Trước Wave 2 chương trình này **không viết ra được**: không có
    `model_assumption` cho toạ độ, không có `construct_solid`, không có
    `measure`. Ba thứ thiếu, mỗi thứ chặn ở một tầng khác nhau.
    """
    diem = {
        "A": ([0, 0, 0], "gốc toạ độ đặt ở chân đường cao SA"),
        "B": ([1, 0, 0], "cạnh đáy AB dọc trục x, độ dài 1"),
        "C": ([1, 1, 0], "đáy là hình vuông cạnh 1"),
        "D": ([0, 1, 0], "đáy là hình vuông cạnh 1"),
        "S": ([0, 0, 2], "SA vuông góc đáy nên S nằm trên trục z, SA = 2"),
    }
    return {
        "spec_version": "1.0",
        "title": "Thể tích khối chóp S.ABCD",
        "description": "Dựng khối chóp rồi đo thể tích.",
        "pedagogical_intent": "Cho thấy thể tích phụ thuộc đáy và chiều cao.",
        "memory_declarations": [
            {"name": n, "type": "point3", "initial_value": v,
             "model_assumption": ly_do}
            for n, (v, ly_do) in diem.items()
        ] + [
            {"name": "chop", "type": "solid"},
            {"name": "V", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_solid", "target_var": "chop",
             "vertices": ["A", "B", "C", "D", "S"],
             "faces": [[0, 1, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]],
             "label": "S.ABCD"},
            {"kind": "assign", "target_var": "V",
             "expr": {"kind": "measure", "quantity": "volume", "of": "chop"}},
        ],
        "visual_bindings": {
            "value_boxes": [
                {"box_id": "kq", "var_ref": "V", "label": "Thể tích"}
            ]
        },
    }


def _hop_dong_geo_09() -> RequestContract:
    return RequestContract(
        obligations=(
            Obligation(kind="volume", container="chop",
                       params={"witness": "V"}),
        ),
        input_facts=(
            InputFact(fact_id="canh_day", label="cạnh đáy", values=(1,)),
            InputFact(fact_id="sa", label="SA", values=(2,)),
        ),
    )


def test_geo_09_CHAY_TRON_qua_grounding_C1a_C1b_C2():
    """A (executable) — mục tiêu của Wave 2. Bốn cổng đầu đều thông."""
    from app.simulation.semantic_program.route import verify_and_compile

    spec = SemanticProgramSpec.model_validate(_chuong_trinh_geo_09())
    kq = verify_and_compile(_hop_dong_geo_09(), spec)

    assert kq.executable, f"{kq.stage_reached}: {kq.reason} · {kq.details}"
    assert not kq.weak_kinds, "`volume` phải có checker server-owned"
    assert kq.stage_reached != "grounding"


def test_B_NAY_DA_XANH_vi_man_hinh_co_them_nua_thu_hai():
    """⚠️ TEST NÀY ĐÃ BỊ LẬT NGƯỢC (2026-08-25). Đọc kèm lý do.

    Bản Wave 2 khẳng định `servable` **VẪN False**, và chặn ở đúng một chỗ:
    `chop` là một `solid` đổi giá trị mà tập nguyên thuỷ thị giác đóng băng
    không có nguyên thuỷ 3D nào để bày. Nó tự dặn:

        "B tự nhiên xanh lên ⇒ ai đó đã thêm nguyên thuỷ 3D, hãy SỬA TEST và
         cập nhật ledger thay vì để nó âm thầm đúng."

    Đúng điều đó đã xảy ra, chỉ khác đường: **không** ai thêm nguyên thuỷ 3D vào
    `visual_bindings`. Thay vào đó Phase 5C–5F dựng một **màn hình thứ hai** —
    `Scene3D` — nơi mọi đối tượng hình học được chiếu ra tất định, không ai phải
    khai binding. `learner_surface` nay đọc **cả hai nửa** màn hình.

    Đó là lý do bản vá này không phải nới cổng: câu hỏi của cổng không đổi một
    chữ (*"thứ này có hiện trên màn hình không?"*), chỉ là trước đây nó nhìn sót
    một nửa và vì thế từ chối **mọi** chương trình hình học — kể cả bốn bài đã
    qua oracle độc lập ở Wave 4.

    Giá của việc nhìn sót ấy đo được ở phía học sinh: đề hình chóp dán vào sản
    phẩm nhận "NGOÀI DANH MỤC MÔ PHỎNG" sau ~7 lượt LLM, vì `executable=True`
    mà `servable=False` thì envelope rơi xuống classifier.
    """
    from app.simulation.semantic_program.route import verify_and_compile

    spec = SemanticProgramSpec.model_validate(_chuong_trinh_geo_09())
    kq = verify_and_compile(_hop_dong_geo_09(), spec)

    assert kq.servable, f"{kq.stage_reached}: {kq.details}"
    assert kq.stage_reached == "served"
    assert not kq.details


def test_KHONG_co_nguyen_thuy_thi_giac_3D_nao():
    """Nói thẳng thứ `test_B_VAN_CHAN…` đang phụ thuộc vào, để lời giải thích
    của nó không phải một suy đoán."""
    from app.simulation.semantic_program.contract import VisualContainerBinding
    import typing

    prim = typing.get_args(
        VisualContainerBinding.model_fields["primitive"].annotation
    )
    assert not [p for p in prim if "3d" in p.lower() or "scene" in p.lower()], prim


def test_geo_09_ORACLE_cham_duoc_witness():
    """Điều kiện để lượt đo sau có Ý NGHĨA: oracle đọc `final_memory[witness]`
    và so với `oracle_result["volume"]` của tập DEV. Trước Wave 2 chỗ ấy không
    bao giờ chứa một con số, nên 4/10 bài **không chấm được về mặt cấu trúc** —
    và điều đó chưa từng hiện ra ở Phase 5 vì chúng trượt schema trước."""
    from app.simulation.semantic_program.interpreter import (
        SemanticProgramInterpreter,
    )

    spec = SemanticProgramSpec.model_validate(_chuong_trinh_geo_09())
    kq = SemanticProgramInterpreter().execute(spec)
    assert kq.final_memory["V"] == Fraction(2, 3)

    dev = json.loads(_DEV.read_text(encoding="utf-8"))
    mong = next(c for c in dev["cases"] if c["case_id"] == "geo_09")
    assert Fraction(str(kq.final_memory["V"])) == Fraction(
        mong["oracle_result"]["volume"]
    )


def test_CHUONG_TRINH_KHAI_DAP_AN_bi_chan_o_dung_tang_dau():
    """Đối chứng ÂM cho test trên. Cùng bài, nhưng thay `measure` bằng một
    hằng `2/3` khai thẳng — đúng thứ R0 cấm. Không có test này thì
    `test_geo_09_DI_TRON_DUONG` chỉ chứng minh cổng cho qua, chưa chứng minh nó
    còn chặn được gì."""
    from app.simulation.semantic_program.route import verify_and_compile

    ct = _chuong_trinh_geo_09()
    ct["statements"] = ct["statements"][:1]  # bỏ phép đo
    ct["memory_declarations"] = [
        d if d["name"] != "V"
        else {"name": "V", "type": "float", "initial_value": "2/3",
              "model_assumption": "thể tích tính được"}
        for d in ct["memory_declarations"]
    ]
    hd = RequestContract(obligations=(
        Obligation(kind="volume", container="chop", params={"witness": "V"}),
    ))
    kq = verify_and_compile(hd, SemanticProgramSpec.model_validate(ct))
    assert not kq.executable
    assert kq.stage_reached == "grounding"
    assert any(ERR_GIA_THIET_LA_DAP_AN in d for d in kq.details), kq.details


def test_ba_nghia_vu_DAI_LUONG_nay_deu_khai_duoc_gia_tri_mong_doi():
    """`check_distance`/`check_angle`/`check_volume` đọc `params["value"]` và
    `params["cos_sq"]`. Thiếu hai trường ấy trong schema `analyze` thì chúng
    LUÔN `None` — ba nghĩa vụ có checker mà checker chưa từng so gì."""
    props = analyze_schema_for(DP.DOMAIN_HINH_HOC)[
        "properties"]["obligations"]["items"]["properties"]
    assert {"value", "cos_sq", "wrt"} <= set(props)
