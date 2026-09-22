# -*- coding: utf-8 -*-
"""HỢP ĐỒNG PROMPT: chuẩn hoá theo ĐỊNH NGHĨA phải là một lớp riêng.

`ANALYZE_DEFINITIONAL_NORMALIZATION_PROMPT_FIX` (2026-09-21).
**0 lượt gọi model · 0 request mạng.**

─── HỢP ĐỒNG NÀY CANH GÌ ───────────────────────────────────────────────────

Lượt live `STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_VALIDATION` bỏ sót
`line(A,B) ⟂ line(A,C)` cho đề *"ABC là tam giác vuông tại A"*, và wave chẩn
đoán quy về `PROMPT_INSTRUCTION_GAP`: prompt chỉ có HAI ngăn — *đề NÓI* và
*bạn tự suy* — nên một tính chất phát biểu bằng LOẠI HÌNH không có chỗ.

Test ở đây kiểm **nội dung canonical của prompt**, không kiểm tên hàm và không
kiểm câu chú thích. Bốn lớp ngữ nghĩa, mỗi lớp buộc prompt phải mang một luật
kiểm được.

─── VÌ SAO KHÔNG CHỈ `parametrize` TRÊN DANH SÁCH FIXTURE ──────────────────

Một bộ test chỉ `parametrize` theo chính danh sách cần kiểm thì **xoá một
fixture làm ít test đi mà vẫn xanh** — nó đo chính nó. Nên sổ đăng ký 13 cách
viết bị khoá hai lớp: danh sách ID đóng băng **và** băm nội dung chính tắc.
Xoá, thêm hay sửa một mục đều ĐỎ.

─── RANH GIỚI CỦA WAVE ─────────────────────────────────────────────────────

Wave chỉ đổi prompt. Test canh luôn điều đó: prompt mới phải bằng ĐÚNG prompt
cũ cộng ĐÚNG khối luật đã đăng ký ở artifact chẩn đoán — không một byte khác.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import diagnose_structured_relation_prompt as D  # noqa: E402

PROMPT_FILE = GOC / "app" / "ai" / "skills" / "geometry_analyze.md"

#: Prompt TRƯỚC wave này — đo tại `eeacd675ce…`. Không được đổi.
SHA_TRUOC = "5746c5e5804c9f3df0618602ad5b78c2c3d1f5f227b4e4cfa630d04d7c61e004"
BYTES_TRUOC = 5311

#: Sổ đăng ký 13 cách viết, khoá bằng ID **và** băm nội dung chính tắc.
FIXTURE_IDS = ("W01", "W02", "W03", "W04", "W05", "W06", "W07",
               "W08", "W09", "W10", "W11", "W12", "W13")
FIXTURE_REGISTRY_SHA = (
    "615c590a34c2c5026d4630bcf678cf6b2518705293b55f42c6db257740fae946")

#: Nhãn của ca live. Khối luật MỚI không được nhắc tới chúng.
NHAN_CA_LIVE = ("S.ABC", "(ABC)", "ABC", "SA", "AB", "AC", "BC",
                "C01", "C02", "C03")


def prompt(base_wave_only: bool = True) -> str:
    """Prompt canonical — bản LF, đúng thứ `load_skill` trả về."""
    txt = PROMPT_FILE.read_text(encoding="utf-8").replace("\r\n", "\n")
    if base_wave_only:
        # Lớp lăng trụ đứng (wave PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE)
        # nối thêm mục solid_topology ở cuối file prompt.
        if "\n## solid_topology — tô-pô khối lăng trụ đứng\n" in txt:
            txt = txt.split("\n## solid_topology — tô-pô khối lăng trụ đứng\n")[0].rstrip() + "\n"
    return txt


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ── LUẬT PROMPT PHẢI CÓ, theo LỚP NGỮ NGHĨA ────────────────────────────────
#: `lớp → (id luật, regex trên prompt canonical, vì sao)`. Đây là chỗ DUY NHẤT
#: nói "lớp này được phủ bởi luật nào" — không lặp lại ở nơi khác.
LUAT_THEO_LOP: dict[str, tuple[tuple[str, str, str], ...]] = {
    "EXPLICIT_SURFACE_RELATION": (
        ("R_KHAI_LAI", r"khai\s+LẠI\s+bằng\s+tên\s+đỉnh|đã ghi thành câu",
         "quan hệ viết thẳng phải được khai lại bằng tên đỉnh"),
        ("R_GOC_90", r"90\s*°",
         "dạng 'góc … bằng 90°' phải được nêu, nếu không nó rơi ngoài cụm "
         "'quan hệ vuông góc'"),
    ),
    "DEFINITIONAL_NORMALIZATION": (
        ("R_DINH_NGHIA_KICH_HOAT", r"vuông tại",
         "phải nêu được cách viết 'tam giác … vuông tại …'"),
        ("R_DINH_NGHIA_LA_GIVEN", r"`model_assumption`\s*để\s*`false`",
         "chuẩn hoá theo định nghĩa vẫn là dữ kiện đề cho"),
        ("R_KHONG_PHAI_SUY", r"không phải bạn tự suy",
         "phải nói rõ đây là VIẾT LẠI, không phải suy luận — nếu không, luật "
         "cấm suy diễn sẽ nuốt nó"),
    ),
    "LOGICAL_DERIVATION": (
        ("R_HE_QUA", r"hệ tự suy, đừng liệt kê",
         "hệ quả của đường ⟂ mặt do FactGraph sinh, mô hình không khai"),
    ),
    "LAYOUT_OR_CONSTRUCTION_ASSUMPTION": (
        ("R_TOA_DO", r"Hệ toạ độ KHÔNG phải dữ kiện",
         "lựa chọn bố cục không bao giờ là dữ kiện đề"),
    ),
}

#: Prompt KHÔNG được mang những thứ này — mở rộng ngoài phạm vi wave.
#:
#: ⚠️ Mẫu phải bắt **mệnh lệnh**, không bắt từ khoá. Bản đầu dùng
#: `tính thể tích` và `(0,0,0)`, rồi đỏ ở hai chỗ VỐN ĐÚNG: dòng 65 là một
#: hàng trong BẢNG DỊCH câu hỏi của đề sang nghĩa vụ, còn `(0,0,0)` nằm trong
#: chính luật CẤM khai toạ độ. Một cổng phạt đúng phần prompt làm điều nó đòi
#: thì không phải cổng.
#: ⚠️ CHỈ những mẫu mà sự xuất hiện của chúng ở BẤT KỲ đâu đều sai.
CAM_TRONG_PROMPT: tuple[tuple[str, str], ...] = (
    (r'"type"\s*:\s*"OBJECT"', "nhét schema vào prompt"),
    (r'"enum"\s*:', "chép enum của schema"),
    (r"scene3d|scene_3d|dựng cảnh", "bắt mô hình tạo cảnh"),
    (r"primitive compiler|geometry_compiler", "mô tả thuật toán compiler"),
    (r"suy ra MỌI|liệt kê mọi hệ quả", "bắt suy mọi hệ quả hình học"),
)

#: Hai lệnh cấm này chỉ có nghĩa khi soi KHỐI WAVE NÀY THÊM.
#:
#: Prompt vốn đã nói *"Không đặt hệ toạ độ, không dựng hình, không tính toán"*
#: (L4) và *"Đừng khai `A = (0,0,0)`"* (L40) — quét cả prompt thì mẫu khớp vào
#: chính câu CẤM, tức phạt phần prompt đang làm điều test đòi. Đã cắn hai lần
#: trong wave này, nên ghi lại cho rõ: ban theo từ khoá không phân biệt được
#: *"hãy làm X"* với *"đừng làm X"*; muốn phân biệt thì phải thu hẹp phạm vi.
CAM_TRONG_KHOI_MOI: tuple[tuple[str, str], ...] = (
    (r"hãy tính|bạn tính|tự tính|đáp số|kết quả bằng|thể tích",
     "khối luật mới bắt mô hình tính đáp số"),
    (r"toạ độ|tọa độ|trục O[xyz]|\(\s*0\s*,\s*0\s*,\s*0\s*\)",
     "khối luật mới hướng dẫn dựng toạ độ"),
)


def _khoi_moi() -> str:
    """Phần văn bản wave này THÊM vào prompt — không có gì khác.

    Suy ra bằng cách gỡ khối luật đã đăng ký khỏi prompt hiện tại rồi đòi phần
    còn lại băm đúng bản trước. Nhờ vậy phép kiểm 'chỉ đổi đúng khối ấy' không
    cần đọc Git và không cần tin một con số byte.
    """
    return D.LUAT_DE_XUAT


# ══ HỢP ĐỒNG CHÍNH — prompt = prompt cũ + ĐÚNG khối luật đã đăng ký ════════
def test_prompt_moi_bang_prompt_cu_cong_DUNG_khoi_luat_da_dang_ky():
    p = prompt()
    khoi = "\n" + _khoi_moi().rstrip("\n")
    assert khoi in p, "khối luật đã đăng ký không có trong prompt"
    goc = p.replace(khoi, "", 1)
    assert _sha(goc) == SHA_TRUOC, (
        "gỡ khối luật ra KHÔNG trả về đúng prompt trước wave — wave đã đổi "
        "thêm chỗ khác ngoài khối đã chẩn đoán")
    assert len(goc.encode("utf-8")) == BYTES_TRUOC


def test_khoi_luat_dat_ngay_canh_luat_cam_liet_ke_he_qua():
    """Một luật MỞ và một luật ĐÓNG phải đứng cạnh nhau, không tách xa."""
    p = prompt()
    neo = D.NEO_CHEN
    assert p.count(neo) == 1
    sau_neo = p.index(neo) + len(neo)
    assert p[sau_neo:sau_neo + len("\n" + _khoi_moi().rstrip("\n"))] == (
        "\n" + _khoi_moi().rstrip("\n")), "khối luật không nằm ngay sau neo"


def test_delta_dung_361_byte_va_prompt_sau_la_5672():
    p = prompt()
    assert len(_khoi_moi().encode("utf-8")) == 361
    assert len(p.encode("utf-8")) == 5672


# ══ A — BỐN LỚP NGỮ NGHĨA ĐỀU CÓ LUẬT ═════════════════════════════════════
@pytest.mark.parametrize("lop", sorted(LUAT_THEO_LOP))
def test_A_moi_lop_ngu_nghia_deu_co_luat_trong_prompt(lop):
    p = prompt()
    thieu = [rid for rid, mau, _ in LUAT_THEO_LOP[lop]
             if not re.search(mau, p, re.IGNORECASE)]
    assert thieu == [], f"lớp {lop} thiếu luật: {thieu}"


def test_A_bis_du_DUNG_bon_lop_khong_thua_khong_thieu():
    assert set(LUAT_THEO_LOP) == set(D.LOP_NGU_NGHIA)
    assert len(LUAT_THEO_LOP) == 4


# ══ B — 13 CÁCH VIẾT, SỔ ĐĂNG KÝ BỊ KHOÁ ══════════════════════════════════
def _registry_sha() -> str:
    can = json.dumps(
        [{k: m[k] for k in ("id", "wording", "semantic_class",
                            "expected_relation", "given_or_derived")}
         for m in D.MA_TRAN_CACH_VIET],
        sort_keys=True, ensure_ascii=False)
    return _sha(can)


def test_B_so_dang_ky_13_cach_viet_khong_bi_them_bot_hay_sua():
    """Khoá HAI lớp: danh sách ID và băm nội dung.

    Không có phép kiểm này thì xoá một fixture chỉ làm số test giảm đi — bộ
    test tự đo chính nó và vẫn xanh.
    """
    assert tuple(m["id"] for m in D.MA_TRAN_CACH_VIET) == FIXTURE_IDS
    assert len(D.MA_TRAN_CACH_VIET) == 13
    assert _registry_sha() == FIXTURE_REGISTRY_SHA, (
        "sổ đăng ký 13 cách viết đã đổi — đóng băng từ wave chẩn đoán")


@pytest.mark.parametrize("fx", D.MA_TRAN_CACH_VIET, ids=lambda m: m["id"])
def test_B_moi_cach_viet_duoc_mot_luat_trong_prompt_phu(fx):
    p = prompt()
    thieu = [rid for rid, mau, _ in LUAT_THEO_LOP[fx["semantic_class"]]
             if not re.search(mau, p, re.IGNORECASE)]
    assert thieu == [], f"{fx['id']} ({fx['semantic_class']}) chưa được phủ: {thieu}"


def test_B_do_phu_la_13_tren_13_va_la_DO_PHU_CHI_DAN():
    p = prompt()
    phu = [m["id"] for m in D.MA_TRAN_CACH_VIET
           if all(re.search(mau, p, re.IGNORECASE)
                  for _, mau, _ in LUAT_THEO_LOP[m["semantic_class"]])]
    assert len(phu) == 13, f"mới phủ {len(phu)}/13: thiếu " \
                           f"{set(FIXTURE_IDS) - set(phu)}"
    # ⚠️ Đây là PROMPT_INSTRUCTION_COVERAGE — prompt có NÓI hay không.
    # Nó KHÔNG phải độ chính xác của mô hình và không dự đoán gì về lượt live.


def test_B_fixture_tieng_Anh_chi_de_kiem_tinh_TONG_QUAT():
    en = [m for m in D.MA_TRAN_CACH_VIET if m["ngon_ngu"] == "en"]
    assert len(en) == 1 and en[0]["id"] == "W08"
    # Prompt KHÔNG được mở phạm vi sang đề tiếng Anh.
    assert "tiếng Anh" not in prompt() and "English" not in prompt()


# ══ C — KHÔNG HARDCODE CA LIVE ════════════════════════════════════════════
def test_C_khoi_luat_moi_khong_nhac_nhan_diem_cua_ca_live():
    khoi = _khoi_moi()
    lot = [n for n in NHAN_CA_LIVE if n in khoi]
    assert lot == [], f"khối luật hard-code ca live: {lot}"
    assert "PQR" in khoi, "phải dùng nhãn tổng quát"
    assert "10" not in khoi, "không được nhắc đáp số của ca live"


def test_C_bis_khoi_luat_khong_gan_voi_mot_ho_hinh_cu_the():
    khoi = _khoi_moi().lower()
    for k in ("hình chóp", "s.abc", "khối chóp", "thể tích"):
        assert k not in khoi, f"khối luật gắn với một họ hình: {k}"


def test_C_ter_test_nay_cung_khong_duoc_hardcode_ca_live_vao_luat():
    """Chính bộ kiểm cũng phải tổng quát: luật đọc từ sổ đăng ký, không chép tay."""
    nguon = Path(__file__).read_text(encoding="utf-8")
    than_luat = nguon[nguon.index("LUAT_THEO_LOP"):nguon.index("CAM_TRONG_PROMPT")]
    for n in ("S.ABC", "C01", "C02", "C03"):
        assert n not in than_luat


# ══ D — BIÊN GIVEN / DERIVED ══════════════════════════════════════════════
def test_D_tam_giac_vuong_la_GIVEN_va_KHONG_mang_model_assumption():
    p = prompt()
    assert re.search(r"vuông tại", p)
    assert re.search(r"`model_assumption`\s*để\s*`false`", p)
    # Và phải nói rõ vì sao nó KHÔNG phải suy luận.
    assert "không phải bạn tự suy" in p
    for m in D.MA_TRAN_CACH_VIET:
        if m["semantic_class"] == "DEFINITIONAL_NORMALIZATION":
            assert m["given_or_derived"] == "GIVEN", m["id"]


def test_D_he_qua_line_plane_VAN_khong_duoc_nang_thanh_GIVEN():
    p = prompt()
    assert "hệ tự suy, đừng liệt kê" in p, "luật cấm liệt kê hệ quả đã mất"
    assert "Chỉ khai quan hệ đề NÓI" in p
    # Khối luật mới KHÔNG được nhắc tới hệ quả hay đường-trong-mặt-phẳng.
    khoi = _khoi_moi().lower()
    assert "hệ quả" not in khoi
    assert "mọi đường trong mặt phẳng" not in khoi
    suy = [m for m in D.MA_TRAN_CACH_VIET
           if m["semantic_class"] == "LOGICAL_DERIVATION"]
    assert suy and all(m["given_or_derived"] == "DERIVED" for m in suy)


def test_D_luat_van_doi_source_fact_id_va_cam_khai_khi_khong_co_nguon():
    p = prompt()
    assert "`source_fact_id` trỏ về `id` của mục `input_facts`" in p
    assert "Không có mục" in p and "đừng khai quan hệ" in p


def test_D_bis_giả_dinh_cua_mo_hinh_van_phai_mang_co_rieng():
    p = prompt()
    assert re.search(r"tự suy ⇒ `model_assumption` là `true`", p), \
        "luật phân biệt giả định của mô hình đã mất"


# ══ E — KHÔNG MỞ RỘNG NGOÀI PHẠM VI ═══════════════════════════════════════
@pytest.mark.parametrize("mau,vi_sao", CAM_TRONG_PROMPT,
                         ids=[v for _, v in CAM_TRONG_PROMPT])
def test_E_prompt_khong_mo_rong_ngoai_pham_vi(mau, vi_sao):
    assert not re.search(mau, prompt(), re.IGNORECASE), vi_sao


@pytest.mark.parametrize("mau,vi_sao", CAM_TRONG_KHOI_MOI,
                         ids=[v for _, v in CAM_TRONG_KHOI_MOI])
def test_E_khoi_luat_moi_khong_mo_rong_ngoai_pham_vi(mau, vi_sao):
    assert not re.search(mau, _khoi_moi(), re.IGNORECASE), vi_sao


def test_E_bis_prompt_van_cam_mo_hinh_giai_bai():
    p = prompt()
    assert "Bạn KHÔNG giải bài" in p
    assert "Không đặt hệ toạ độ, không dựng hình, không tính toán" in p


# ══ F — PARITY ════════════════════════════════════════════════════════════
def test_F_schema_KHONG_doi_mot_byte():
    from app.simulation.semantic_program.analyze_contract import analyze_schema_for
    sch = analyze_schema_for("hinh_hoc")
    # Lớp lăng trụ đứng (wave PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE) thêm trường solid_topology
    if "solid_topology" in sch.get("properties", {}):
        sch = dict(sch)
        sch["properties"] = {k: v for k, v in sch["properties"].items() if k != "solid_topology"}
    s = json.dumps(sch, sort_keys=True, ensure_ascii=False)
    assert _sha(s) == (
        "0542161e56ecca5e224964200208be93a648af93a14f6e733c94dedef99c2b7b")
    assert len(s.encode("utf-8")) == 3246


def test_F_schema_keyset_khong_doi():
    from app.simulation.semantic_program.analyze_contract import analyze_schema_for
    s = analyze_schema_for("hinh_hoc")
    props = [k for k in s["properties"] if k != "solid_topology"]
    assert sorted(props) == ["geometric_relations", "input_facts",
                             "obligations"]
    assert sorted(s.get("required", [])) == ["input_facts", "obligations"]
    it = s["properties"]["geometric_relations"]["items"]
    assert sorted(it["properties"]) == ["kind", "line", "model_assumption",
                                        "other_line", "plane", "source_fact_id"]
    assert sorted(it["required"]) == ["kind", "line", "source_fact_id"]
    assert it["properties"]["kind"]["enum"] == ["perpendicular_lines",
                                                "perpendicular_line_plane"]


def test_F_prompt_schema_parity_moi_ten_truong_nhac_trong_prompt_co_that():
    """Prompt nhắc tên trường nào thì schema phải có đúng tên ấy."""
    from app.simulation.semantic_program.analyze_contract import analyze_schema_for
    s = analyze_schema_for("hinh_hoc")
    it = s["properties"]["geometric_relations"]["items"]["properties"]
    p = prompt()
    for ten in ("perpendicular_lines", "perpendicular_line_plane",
                "source_fact_id", "model_assumption"):
        assert ten in p
    for ten in ("source_fact_id", "model_assumption", "line", "other_line",
                "plane", "kind"):
        assert ten in it


def test_F_mien_khac_KHONG_doi():
    """Chỉ skill hình học đổi. Tin học và bản mặc định nguyên vẹn."""
    from app.ai.gemini import load_skill
    from app.simulation.semantic_program.analyze_contract import (
        SEMANTIC_ANALYZE_SCHEMA, analyze_schema_for,
    )
    from app.simulation.semantic_program.domain_profile import analyze_skill_for
    assert analyze_skill_for("hinh_hoc") == "geometry_analyze"
    # Skill Tin học không mang luật hình học mới.
    tin = load_skill("semantic_analyze")
    assert "vuông tại" not in tin and "perpendicular_lines" not in tin
    assert json.dumps(SEMANTIC_ANALYZE_SCHEMA, sort_keys=True) != \
        json.dumps(analyze_schema_for("hinh_hoc"), sort_keys=True)


def test_F_compiler_VAN_khong_doc_problem_text():
    """Wave không được đưa bộ đọc câu chữ trở lại tầng dựng.

    ⚠️ Kiểm phép ĐỌC, không kiểm chuỗi. Bản đầu quét mọi `ast.Constant` và vì
    thế đỏ ở bốn **docstring** nói rõ *"KHÔNG BAO GIỜ đọc `problem_text`"* —
    tức phạt đúng phần tài liệu khẳng định điều test muốn. Đường đọc thật chỉ
    có hai dạng: `x.problem_text` và `x["problem_text"]`.
    """
    import ast
    for ten in ("compiler.py", "contract_adapter.py", "fact_graph.py",
                "routing.py", "primitives.py"):
        p = GOC / "app" / "simulation" / "geometry_compiler" / ten
        cay = ast.parse(p.read_text(encoding="utf-8"))
        thuoc = {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)}
        assert "problem_text" not in thuoc, f"{ten} đọc .problem_text"
        chi_so = {n.slice.value for n in ast.walk(cay)
                  if isinstance(n, ast.Subscript)
                  and isinstance(n.slice, ast.Constant)
                  and isinstance(n.slice.value, str)}
        assert "problem_text" not in chi_so, f"{ten} đọc ['problem_text']"
        # `getattr(x, "problem_text")` cũng là một đường đọc.
        for n in ast.walk(cay):
            if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "getattr":
                lit = [a.value for a in n.args
                       if isinstance(a, ast.Constant) and isinstance(a.value, str)]
                assert "problem_text" not in lit, f"{ten} getattr problem_text"


def test_F_legacy_hop_dong_quan_he_truc_tiep_van_chay_y_cu():
    """Hợp đồng khai quan hệ theo đường TRỰC TIẾP không đổi hành vi."""
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.geometry_compiler import contract_adapter as A
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import (
        InputFact, RequestContract,
    )
    from app.simulation.semantic_program.scale_normalization import SourceInvariant
    from app.simulation.semantic_program.structured_relations import (
        GeometricRelation,
    )
    hd = RequestContract(
        obligations=(Obligation(kind="volume", container="khoi",
                                params={"witness": "v"}),),
        input_facts=(InputFact(fact_id="f_vuong", label="đáy vuông",
                               values=("tam giác PQR vuông tại P",)),
                     InputFact(fact_id="f_perp", label="SP ⊥ đáy",
                               values=("SP ⊥ (PQR)",))),
        source_invariants=(
            SourceInvariant(points=("P", "Q"), expected="3",
                            source_fact_id="f_vuong", scale_symbol="",
                            source_text=""),
            SourceInvariant(points=("P", "R"), expected="4",
                            source_fact_id="f_vuong", scale_symbol="",
                            source_text=""),
            SourceInvariant(points=("P", "S"), expected="5",
                            source_fact_id="f_perp", scale_symbol="",
                            source_text="")),
        geometric_relations=(
            GeometricRelation(kind="perpendicular_lines", line=("P", "Q"),
                              other_line=("P", "R"), source_fact_id="f_vuong"),
            GeometricRelation(kind="perpendicular_line_plane", line=("S", "P"),
                              plane=("P", "Q", "R"), source_fact_id="f_perp")),
        problem_text="")
    ka = A.build_fact_graph(hd)
    assert ka.status == "VALID" and ka.adapter_version == "contract-to-fact-graph/2"
    assert ka.graph.version == "geometry-fact-graph/2"
    assert C.danh_gia_eligibility(ka.graph).status == "SUPPORTED"
    assert C.bien_dich(ka.graph).status == "COMPILED"


def test_F_bo_quan_he_day_thi_VAN_tu_choi_dung_ma():
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.geometry_compiler import contract_adapter as A
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import (
        InputFact, RequestContract,
    )
    from app.simulation.semantic_program.scale_normalization import SourceInvariant
    from app.simulation.semantic_program.structured_relations import (
        GeometricRelation,
    )
    hd = RequestContract(
        obligations=(Obligation(kind="volume", container="khoi",
                                params={"witness": "v"}),),
        input_facts=(InputFact(fact_id="f_perp", label="SP ⊥ đáy",
                               values=("SP ⊥ (PQR)",)),),
        source_invariants=(
            SourceInvariant(points=("P", "Q"), expected="3",
                            source_fact_id="f_perp", scale_symbol="", source_text=""),
            SourceInvariant(points=("P", "R"), expected="4",
                            source_fact_id="f_perp", scale_symbol="", source_text=""),
            SourceInvariant(points=("P", "S"), expected="5",
                            source_fact_id="f_perp", scale_symbol="", source_text="")),
        geometric_relations=(
            GeometricRelation(kind="perpendicular_line_plane", line=("S", "P"),
                              plane=("P", "Q", "R"), source_fact_id="f_perp"),),
        problem_text="tam giác PQR vuông tại P")
    ka = A.build_fact_graph(hd)
    el = C.danh_gia_eligibility(ka.graph)
    assert el.status == "UNSUPPORTED_STRUCTURED_RELATION_MISSING"
    assert el.reason_code == "BASE_PERPENDICULAR_RELATION_MISSING"
    # `problem_text` CÓ chứa cấu trúc định nghĩa — và tầng dựng vẫn từ chối.
    # Đó là bằng chứng nó không đọc câu chữ.


def test_F_compiler_deterministic():
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.geometry_compiler import contract_adapter as A
    from app.simulation.semantic_program.obligations import Obligation
    from app.simulation.semantic_program.request_contract import (
        InputFact, RequestContract,
    )
    from app.simulation.semantic_program.scale_normalization import SourceInvariant
    from app.simulation.semantic_program.structured_relations import (
        GeometricRelation,
    )

    def mot_luot() -> str:
        hd = RequestContract(
            obligations=(Obligation(kind="volume", container="khoi",
                                    params={"witness": "v"}),),
            input_facts=(InputFact(fact_id="f_vuong", label="đáy vuông",
                                   values=("tam giác PQR vuông tại P",)),),
            source_invariants=(
                SourceInvariant(points=("P", "Q"), expected="3",
                                source_fact_id="f_vuong", scale_symbol="", source_text=""),
                SourceInvariant(points=("P", "R"), expected="4",
                                source_fact_id="f_vuong", scale_symbol="", source_text=""),
                SourceInvariant(points=("P", "S"), expected="5",
                                source_fact_id="f_vuong", scale_symbol="", source_text="")),
            geometric_relations=(
                GeometricRelation(kind="perpendicular_lines", line=("P", "Q"),
                                  other_line=("P", "R"), source_fact_id="f_vuong"),
                GeometricRelation(kind="perpendicular_line_plane", line=("S", "P"),
                                  plane=("P", "Q", "R"), source_fact_id="f_vuong")),
            problem_text="")
        g = A.build_fact_graph(hd).graph
        return json.dumps(C.bien_dich(g).program, sort_keys=True, ensure_ascii=False)

    assert mot_luot() == mot_luot()


# ══ KHÔNG GỌI MODEL, KHÔNG MẠNG ═══════════════════════════════════════════
def test_khong_co_loi_goi_model_va_khong_nap_khoa():
    """Kiểm IMPORT và LỜI GỌI bằng AST, không kiểm chuỗi.

    ⚠️ Bản đầu khẳng định `"call_gemini" not in nguồn` — và đỏ vì chính danh
    sách cấm ấy nằm trong nguồn. Một cổng tự khớp chính nó thì không đo được gì.
    """
    import ast
    import os
    assert "GEMINI_API_KEY" not in os.environ
    cay = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    nhap = {n.module or "" for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)}
    nhap |= {a.name for n in ast.walk(cay) if isinstance(n, ast.Import)
             for a in n.names}
    assert not (nhap & {"httpx", "requests", "socket", "urllib", "aiohttp"})

    def ten_goi(n: ast.Call) -> str:
        f = n.func
        return f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")

    goi = {ten_goi(n) for n in ast.walk(cay) if isinstance(n, ast.Call)}
    assert not (goi & {"call_gemini", "stage_semantic_analyze",
                       "stage_semantic_program", "run_pipeline", "post",
                       "urlopen"})
