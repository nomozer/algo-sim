# -*- coding: utf-8 -*-
"""HỢP ĐỒNG cho công cụ chẩn đoán `ANALYZE_STRUCTURED_RELATION_PROMPT_DIAGNOSIS`.

Test ở đây canh **công cụ chẩn đoán**, không canh prompt sản phẩm — wave này
không được sửa prompt. Bốn thứ chúng giữ, và mỗi thứ đã có một phép tiêm lỗi
chứng minh nó đỏ được:

① Ranh giới ngữ nghĩa bốn lớp không chồng lấn, và *"tam giác vuông tại A"* nằm
   ở lớp `DEFINITIONAL_NORMALIZATION` — không phải `LOGICAL_DERIVATION`.
② Hệ quả của `line ⟂ plane` **chỉ** được kỳ vọng `DERIVED`.
③ Luật đề xuất TỔNG QUÁT: không nhắc nhãn của ca live.
④ Công cụ không đọc đầu ra thô, không mở mạng, không đụng prompt/schema thật.
"""
from __future__ import annotations

import ast
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

DIAG_SRC = GOC / "scripts" / "diagnose_structured_relation_prompt.py"


# ══ A — AUDIT PHÁT HIỆN ĐƯỢC CÓ / KHÔNG CÓ CHUẨN HOÁ THEO ĐỊNH NGHĨA ═══════
def test_A_audit_phat_hien_prompt_hien_tai_KHONG_co_chuan_hoa_theo_dinh_nghia():
    a = D.prompt_instruction_audit()
    # ⚠️ ĐÃ ĐẢO CHIỀU ở `ANALYZE_DEFINITIONAL_NORMALIZATION_PROMPT_FIX`
    # (2026-09-21). Trước lượt sửa, bộ audit phải phát hiện prompt KHÔNG có
    # luật; sau lượt sửa nó phải phát hiện prompt CÓ. Cùng một công cụ, hai
    # phán quyết — và đó chính là phép chứng minh công cụ đo thật.
    #
    # Lời khai LỊCH SỬ (`answer == "NO"`, 0 dòng khớp) vẫn nằm nguyên trong
    # `PROMPT_INSTRUCTION_AUDIT.json` đã đóng băng ở wave chẩn đoán; test này
    # mô tả HỆ ĐANG CHẠY, artifact mô tả lúc đo.
    assert a["TOM_TAT"]["PROMPT_EXPLICITLY_COVERS_DEFINITIONAL_NORMALIZATION"] is True
    assert a["KEYWORD_HITS"]["tam_giac_vuong"], "luật chuẩn hoá theo định nghĩa đã mất"
    assert a["KEYWORD_HITS"]["goc_90"], "dạng 'góc … bằng 90°' đã mất khỏi prompt"

    # Bản đóng băng của wave chẩn đoán KHÔNG được sửa để khớp hiện tại.
    if (D.RA / "PROMPT_INSTRUCTION_AUDIT.json").exists():
        cu = json.loads((D.RA / "PROMPT_INSTRUCTION_AUDIT.json")
                        .read_text(encoding="utf-8"))
        assert cu["A_YEU_CAU_CHUAN_HOA_TAM_GIAC_VUONG"]["answer"] == "NO"
        assert cu["SHA256_LF"] == (
            "5746c5e5804c9f3df0618602ad5b78c2c3d1f5f227b4e4cfa630d04d7c61e004")


def test_A_bis_audit_van_thay_duoc_luat_he_qua_VA_luat_toa_do():
    """Cửa sổ chứng cho bộ quét: nó PHẢI tìm thấy thứ chắc chắn có."""
    a = D.prompt_instruction_audit()
    assert a["KEYWORD_HITS"]["he_qua_duong_vuong_goc_mat"], "bộ quét mù thì kết luận vô giá trị"
    assert a["KEYWORD_HITS"]["model_assumption"]
    assert a["KEYWORD_HITS"]["perpendicular_lines"]
    assert a["TOM_TAT"]["PROMPT_COVERS_LINE_PLANE_CONSEQUENCES"] is True


def test_A_ter_analyze_khong_duoc_ghep_the_van_pham():
    a = D.prompt_instruction_audit()
    assert a["MODEL_FACING_SURFACE_OF_ANALYZE"]["grammar_card_attached"] is False
    nguon = (GOC / "app" / "ai" / "pipeline.py").read_text(encoding="utf-8")
    cay = ast.parse(nguon)
    ham = next(f for f in ast.walk(cay)
               if isinstance(f, (ast.AsyncFunctionDef, ast.FunctionDef))
               and f.name == "stage_semantic_analyze")
    assert "grammar_card" not in ast.unparse(ham)


# ══ B, C, D — SCHEMA BIỂU DIỄN ĐƯỢC QUAN HỆ CÒN THIẾU ══════════════════════
def test_B_fixture_perpendicular_lines_AB_AC_qua_duoc_pydantic():
    s = D.schema_capability_audit()
    assert s["CHECKS"]["PYDANTIC_PARSE_PASS"] is True
    assert s["CHECKS"]["REQUEST_CONTRACT_VALIDATION_PASS"] is True
    assert s["SCHEMA_CAPABILITY_FOR_MISSING_RELATION"] == "PRESENT"


def test_C_AB_va_BA_chuan_hoa_ve_cung_mot_duong():
    from app.simulation.semantic_program.structured_relations import chuan_hoa_duong
    assert chuan_hoa_duong(("A", "B")) == chuan_hoa_duong(("B", "A")) == ("A", "B")
    assert D.schema_capability_audit()["CHECKS"]["AB_EQUIV_BA"] is True


def test_D_source_fact_tam_giac_vuong_truy_duoc():
    s = D.schema_capability_audit()
    assert s["CHECKS"]["SOURCE_FACT_ID_CAN_POINT_TO_TRIANGLE_FACT"] is True
    assert s["CHECKS"]["MODEL_ASSUMPTION_CAN_STAY_FALSE"] is True
    m = D.live_output_diagnostic_mapping()
    assert m["SOURCE_FACT_ID_OBSERVED"] == "abc_tam_giac_vuong_tai_a"
    assert m["MISSING_RELATION_COULD_POINT_TO_THAT_FACT"] is True


def test_D_bis_co_quan_he_thi_compiler_qua_duoc_nhanh_base_perpendicular():
    s = D.schema_capability_audit()
    assert s["COMPILER_ELIGIBILITY_WITH_RELATION"] == "SUPPORTED"


# ══ E — MA TRẬN ĐỦ CÁCH VIẾT ĐÃ ĐĂNG KÝ ════════════════════════════════════
CACH_VIET_BAT_BUOC = (
    "AB vuông góc AC", "AB ⟂ AC", "Góc BAC bằng 90°",
    "Tam giác ABC vuông tại A", "ABC là tam giác vuông ở A",
    "Tam giác ABC có góc A vuông", "Hai cạnh góc vuông là AB và AC",
)


def test_E_ma_tran_phu_moi_cach_viet_bat_buoc():
    co = {m["wording"] for m in D.MA_TRAN_CACH_VIET}
    thieu = [w for w in CACH_VIET_BAT_BUOC if w not in co]
    assert thieu == [], f"thiếu cách viết đã đăng ký: {thieu}"
    assert any(m["ngon_ngu"] == "en" for m in D.MA_TRAN_CACH_VIET), "thiếu bản tiếng Anh"
    assert any("PMN" in m["wording"] for m in D.MA_TRAN_CACH_VIET), "thiếu ca đổi nhãn"
    assert len(D.MA_TRAN_CACH_VIET) >= 10


def test_E_bis_moi_muc_khai_du_truong_va_khong_lop_nao_chong_lan():
    truong = ("id", "wording", "semantic_class", "expected_relation",
              "expected_source_fact", "given_or_derived",
              "covered_by_current_prompt", "covered_by_proposed_delta")
    for m in D.MA_TRAN_CACH_VIET:
        assert all(k in m for k in truong), m["id"]
        assert m["semantic_class"] in D.LOP_NGU_NGHIA, m["id"]
        assert m["covered_by_current_prompt"] in ("YES", "NO", "AMBIGUOUS")
    assert len({m["id"] for m in D.MA_TRAN_CACH_VIET}) == len(D.MA_TRAN_CACH_VIET)
    # Bốn lớp phải PHÂN HOẠCH: mỗi mục đúng một lớp, hai tập GIVEN/không-GIVEN rời nhau.
    p = D.semantic_normalization_policy()
    assert set(p["GIVEN_CLASSES"]) & set(p["NOT_MODEL_DECLARED_CLASSES"]) == set()
    assert set(p["GIVEN_CLASSES"]) | set(p["NOT_MODEL_DECLARED_CLASSES"]) == set(D.LOP_NGU_NGHIA)


# ══ F, G — RANH GIỚI GIVEN / DERIVED ═══════════════════════════════════════
def test_F_EXPLICIT_va_DEFINITIONAL_deu_ky_vong_GIVEN():
    for m in D.MA_TRAN_CACH_VIET:
        if m["semantic_class"] in ("EXPLICIT_SURFACE_RELATION",
                                   "DEFINITIONAL_NORMALIZATION"):
            assert m["given_or_derived"] == "GIVEN", m["id"]


def test_G_he_qua_line_plane_chi_ky_vong_DERIVED():
    suy = [m for m in D.MA_TRAN_CACH_VIET
           if m["semantic_class"] == "LOGICAL_DERIVATION"]
    assert suy, "ma trận phải có ít nhất một hệ quả để canh ranh giới"
    for m in suy:
        assert m["given_or_derived"] == "DERIVED", m["id"]
        assert m["expected_source_fact"] is None, m["id"]


def test_G_bis_tam_giac_vuong_KHONG_duoc_xep_vao_logical_derivation():
    """Đây là ranh giới cả wave xoay quanh — xếp sai là chẩn đoán sai."""
    ca = [m for m in D.MA_TRAN_CACH_VIET if "vuông tại A" in m["wording"]
          or "vuông ở A" in m["wording"] or "góc A vuông" in m["wording"]]
    assert ca, "mất ca 'tam giác vuông tại A'"
    for m in ca:
        assert m["semantic_class"] == "DEFINITIONAL_NORMALIZATION", m["id"]
        assert m["given_or_derived"] == "GIVEN", m["id"]
    assert D.live_output_diagnostic_mapping()[
        "MISSING_RELATION_SEMANTIC_CLASS"] == "DEFINITIONAL_NORMALIZATION"


# ══ H, I, J, K — LUẬT ĐỀ XUẤT ══════════════════════════════════════════════
def test_H_luat_de_xuat_phu_toan_bo_fixture_definitional():
    dn = [m for m in D.MA_TRAN_CACH_VIET
          if m["semantic_class"] == "DEFINITIONAL_NORMALIZATION"]
    assert dn
    assert all(m["covered_by_proposed_delta"] == "YES" for m in dn)
    # Và chúng PHẢI đang không được phủ bởi prompt hiện tại — nếu đã phủ thì
    # chẩn đoán `PROMPT_INSTRUCTION_GAP` không còn cơ sở.
    assert all(m["covered_by_current_prompt"] == "NO" for m in dn)


def test_I_luat_de_xuat_KHONG_bien_he_qua_line_plane_thanh_GIVEN():
    d = D.proposed_prompt_delta()
    assert d["GENERALITY"]["WOULD_MAKE_LINE_PLANE_CONSEQUENCES_GIVEN"] is False
    for k in ("SA", "⟂ BC", "mọi đường trong mặt phẳng"):
        assert k not in D.LUAT_DE_XUAT
    # Luật cũ cấm liệt kê hệ quả phải SỐNG SÓT qua phép ghép.
    assert D.prompt_delta_simulation_proof()["EXISTING_CONSEQUENCE_RULE_PRESERVED"] is True


def test_J_luat_de_xuat_khong_hard_code_nhan_diem_cua_ca_live():
    d = D.proposed_prompt_delta()
    assert d["GENERALITY"]["HARDCODES_LIVE_CASE_LABELS"] is False
    assert d["GENERALITY"]["LEAKED_LABELS"] == []
    assert d["GENERALITY"]["USES_GENERIC_PLACEHOLDER"] is True
    assert d["GENERALITY"]["ASKS_MODEL_TO_COMPUTE"] is False
    assert d["GENERALITY"]["MENTIONS_COORDINATES"] is False
    assert d["GENERALITY"]["COPIES_SCHEMA"] is False


def test_K_luat_de_xuat_khong_doi_schema_factgraph_adapter_compiler():
    r = D.proposed_prompt_delta()["REQUIRED_CHANGES_ELSEWHERE"]
    assert r["SCHEMA_CHANGE_REQUIRED"] is False
    assert r["FACT_GRAPH_CHANGE_REQUIRED"] is False
    assert r["ADAPTER_CHANGE_REQUIRED"] is False
    assert r["COMPILER_CHANGE_REQUIRED"] is False


def test_K_bis_luat_DA_duoc_ap_va_cong_cu_van_khong_cham_dia():
    """Luật đã áp ở wave sau; công cụ chẩn đoán vẫn phải chỉ ĐỌC.

    Hai điều tách bạch: *"prompt đã có luật chưa"* đổi theo thời gian, còn
    *"công cụ có ghi vào prompt không"* thì không bao giờ được đổi.
    """
    p = D.prompt_delta_simulation_proof()
    assert D.proposed_prompt_delta()["APPLIED"] is True
    assert p["FILE_UNTOUCHED_ON_DISK"] is True
    assert p["SIMULATION_IS_IN_MEMORY_ONLY"] is True
    assert p["ANCHOR_FOUND_EXACTLY_ONCE"] is True
    # Đã áp ⇒ bản mô phỏng BẰNG prompt hiện tại, không chèn lần hai.
    assert p["DELTA_BYTES"] == 0
    assert D.prompt_instruction_audit()["SHA256_LF"] == (
        "50a076e15ed9189ab1e664d7d26f3a4b3450178802bc3826a3b4164e52d63500")
    # Và bản đóng băng của wave chẩn đoán vẫn ghi con số CŨ.
    if (D.RA / "PROPOSED_PROMPT_DELTA.json").exists():
        cu = json.loads((D.RA / "PROPOSED_PROMPT_DELTA.json")
                        .read_text(encoding="utf-8"))
        assert cu["APPLIED"] is False
        assert cu["PROMPT_BYTES_CURRENT"] == 5311
        assert cu["PROMPT_BYTES_SIMULATED"] == 5672


# ══ L — KHÔNG GEMINI, KHÔNG MẠNG ═══════════════════════════════════════════
def test_L_cong_cu_chan_doan_khong_co_mot_loi_goi_model_nao():
    """Quét LỜI GỌI bằng AST, không quét chuỗi.

    Bản đầu cấm *tên* xuất hiện ở bất kỳ đâu và vì thế đỏ ở một câu CHÚ THÍCH
    giải thích rằng `stage_semantic_analyze` KHÔNG ghép thẻ văn phạm — tức nó
    phạt đúng phần tài liệu làm cho công cụ dễ kiểm hơn. Thứ cần cấm là lời
    gọi; một cái tên nằm trong chuỗi thì không chạy được.
    """
    nguon = DIAG_SRC.read_text(encoding="utf-8")
    cay = ast.parse(nguon)

    nhap = {n.module or "" for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)}
    nhap |= {a.name for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names}
    cam_nhap = {"httpx", "requests", "urllib", "urllib.request", "socket", "aiohttp"}
    assert not (nhap & cam_nhap), f"công cụ chẩn đoán nhập mạng: {nhap & cam_nhap}"

    def ten_goi(n: ast.Call) -> str:
        f = n.func
        return f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")

    goi = {ten_goi(n) for n in ast.walk(cay) if isinstance(n, ast.Call)}
    # `get` KHÔNG nằm trong danh sách: `dict.get` là lời gọi hợp lệ và phổ biến,
    # nên cấm nó là phạt mã đúng. Lối ra mạng đã bị chặn ở phép kiểm IMPORT —
    # không có client nào thì không có `.get()` nào gọi ra ngoài được.
    cam_goi = {"call_gemini", "stage_semantic_analyze", "stage_semantic_program",
               "run_pipeline", "post", "urlopen", "connect", "send"}
    assert not (goi & cam_goi), f"công cụ chẩn đoán GỌI: {goi & cam_goi}"

    # Những chuỗi này thì thật sự không được có mặt ở bất kỳ dạng nào.
    for k in ("ALLOW_LIVE_AI", "generativelanguage"):
        assert k not in nguon, f"công cụ chẩn đoán nhắc tới {k}"


def test_L_ter_chay_cong_cu_KHONG_lam_khoa_that_lot_vao_moi_truong():
    """`import app.main` kéo `load_dotenv` — khoá thật vào thẳng `os.environ`.

    Đo được trong chính wave này: bản đầu của `identity_and_cache_decision`
    nhập `app.main` để đọc `CACHE_VERSION`, và `PRECHECK` khai
    `GEMINI_API_KEY_LOADED = true` trong khi đặc tả đòi khoá KHÔNG được nạp.
    Đã đổi sang phân tích nguồn `app/main.py`.
    """
    import ast as _ast
    cay = _ast.parse(DIAG_SRC.read_text(encoding="utf-8"))
    nhap = {n.module or "" for n in _ast.walk(cay) if isinstance(n, _ast.ImportFrom)}
    nhap |= {a.name for n in _ast.walk(cay) if isinstance(n, _ast.Import)
             for a in n.names}
    assert "app.main" not in nhap, "nhập app.main là nạp .env vào tiến trình"
    # Giá trị đọc được theo NGUỒN, không viết cứng — bump là chuyện bình thường.
    assert re.fullmatch(r"\d+", D.doc_cache_version())


def test_L_bis_chay_ca_cong_cu_ma_khong_cham_mang():
    """Chạy THẬT mọi hàm với biên mạng bị chặn — `conftest` đã chặn sẵn."""
    for f in (D.live_evidence_integrity, D.prompt_instruction_audit,
              D.schema_capability_audit, D.semantic_normalization_policy,
              D.wording_coverage_matrix, D.live_output_diagnostic_mapping,
              D.proposed_prompt_delta, D.prompt_delta_simulation_proof,
              D.identity_and_cache_decision):
        assert isinstance(f(), dict), f.__name__


# ══ M — ARTIFACT LIVE BẤT BIẾN ═════════════════════════════════════════════
def test_M_artifact_live_cu_khong_doi_mot_byte():
    g = D.live_evidence_integrity()
    assert g["ALL_PRESENT"] is True
    assert g["ALL_UNCHANGED_SINCE_HEAD"] is True
    assert g["HISTORICAL_REPORT_CHANGED"] is False
    lech = [m["file"] for m in g["ITEMS"] if not m["blob_matches_head"]]
    assert lech == [], f"artifact live đã bị sửa: {lech}"


# ══ N — KHÔNG LƯU PROMPT THÔ HAY ĐẦU RA THÔ ════════════════════════════════
def test_N_cong_cu_khong_doc_dau_ra_tho_cua_model():
    nguon = DIAG_SRC.read_text(encoding="utf-8")
    for k in ("candidates[", "systemInstruction", "raw_output", "RAW_OUTPUT",
              "response_text", "parts[0]"):
        assert k not in nguon, f"công cụ chẩn đoán chạm đầu ra thô: {k}"


def test_N_bis_artifact_khong_chua_than_prompt():
    a = D.prompt_instruction_audit()
    # Chỉ băm + số byte + trích ngắn. Không trường nào chở cả thân prompt.
    assert "SHA256_LF" in a and "BYTES_LF" in a
    for nhom in a["KEYWORD_HITS"].values():
        for h in nhom:
            assert len(h["excerpt"]) <= 90
    than = D.PROMPT_FILE.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert than not in json.dumps(a, ensure_ascii=False)
    assert than not in json.dumps(D.proposed_prompt_delta(), ensure_ascii=False)


def test_N_ter_artifact_ghi_ra_dia_cung_khong_chua_than_prompt():
    if not D.RA.exists():
        pytest.skip("chưa sinh artifact — chạy scripts/diagnose_structured_relation_prompt.py")
    than = D.PROMPT_FILE.read_text(encoding="utf-8").replace("\r\n", "\n")
    for p in sorted(D.RA.glob("*.json")):
        van = p.read_text(encoding="utf-8")
        assert than not in van, p.name
        assert "systemInstruction" not in van, p.name


# ══ PHÂN LOẠI NGUYÊN NHÂN — KỶ LUẬT PHÁT BIỂU ══════════════════════════════
def test_phan_loai_nguyen_nhan_va_KHONG_khang_dinh_nhan_qua():
    a, s = D.prompt_instruction_audit(), D.schema_capability_audit()
    r = D.root_cause_classification(a, s, D.live_output_diagnostic_mapping())
    assert r["ROOT_CAUSE_CLASSIFICATION"] in (
        "PROMPT_INSTRUCTION_GAP", "MODEL_NONCOMPLIANCE", "SCHEMA_CAPABILITY_GAP",
        "EVALUATOR_OR_GROUND_TRUTH_ERROR", "INDETERMINATE")
    assert r["CAUSALITY_STATUS"] == "NOT_CAUSALLY_ESTABLISHED"
    assert r["EVIDENCE_STRENGTH"] == "SUPPORTED_BY_CURRENT_EVIDENCE"
    assert r["RELATION_TO_BEHAVIOUR"] == "ASSOCIATED_WITH"
    assert r["ROOT_CAUSE_CONFIDENCE"] == "SINGLE_OBSERVATION"


def test_khong_ket_luan_schema_gap_khi_fixture_parse_PASS():
    a, s = D.prompt_instruction_audit(), D.schema_capability_audit()
    r = D.root_cause_classification(a, s, D.live_output_diagnostic_mapping())
    if s["SCHEMA_CAPABILITY_FOR_MISSING_RELATION"] == "PRESENT":
        assert r["ROOT_CAUSE_CLASSIFICATION"] != "SCHEMA_CAPABILITY_GAP"


def test_evaluator_va_ground_truth_duoc_xac_minh_chu_khong_gia_dinh():
    m = D.live_output_diagnostic_mapping()
    assert m["EVALUATOR_SCORED_MISSING_CORRECTLY"] is True
    assert m["COMPILER_REFUSED_ON_CORRECT_BRANCH"] is True
    assert m["MODEL_OBEYED_CONSEQUENCE_RULE"] is True
    assert m["NO_EXTRA_DERIVED_AS_GIVEN"] is True
    assert m["NO_MODEL_ASSUMPTION"] is True


# ══ §11 — CHÊNH LỆCH SỐ TEST PHẢI GIẢI THÍCH THEO NODE, KHÔNG THEO TỔNG ════
TRUOC_GIA = [
    "tests/x/test_a.py::test_one",
    "tests/x/test_a.py::test_two",
    "tests/semantic_program/test_domain_string.py::test_quet[f1]",
]
SAU_GIA = TRUOC_GIA + [
    "tests/x/test_moi.py::test_alpha",
    "tests/x/test_moi.py::test_beta",
    "tests/semantic_program/test_domain_string.py::test_quet[f2]",
]


def test_so_sanh_thu_thap_phan_loai_TUNG_NODE_chu_khong_chi_tong_so():
    d = D.classify_test_collection(TRUOC_GIA, SAU_GIA)
    assert d["COUNT_DELTA"] == 3 and d["ADDED_COUNT"] == 3
    # Phải có DANH SÁCH node, không chỉ con số — đây là chỗ chênh lệch từng lọt.
    assert isinstance(d.get("ADDED_NODES"), list) and len(d["ADDED_NODES"]) == 3
    assert all("node_id" in p and "classification" in p for p in d["ADDED_NODES"])
    assert d["BY_CLASSIFICATION"] == {"NEW_TEST_FILE": 2, "PARAMETRIZE_EXPANSION": 1}
    assert d["ALL_ADDED_CLASSIFIED"] is True
    assert d["DELTA_FULLY_EXPLAINED"] is True


def test_node_bi_xoa_lam_delta_KHONG_con_duoc_coi_la_giai_thich_het():
    d = D.classify_test_collection(TRUOC_GIA, SAU_GIA[1:])
    assert d["REMOVED_COUNT"] == 1
    assert d["DELTA_FULLY_EXPLAINED"] is False


def _artifact(ten: str):
    p = D.RA / ten
    if not p.exists():
        pytest.skip(f"chưa sinh {ten} — chạy diagnose với --collect-before/--collect-after")
    return json.loads(p.read_text(encoding="utf-8"))


def test_hai_test_chua_giai_thich_da_duoc_truy_ra_dung_co_che():
    c = _artifact("TEST_COUNT_DISCREPANCY_CLASSIFICATION.json")
    assert c["UNEXPLAINED_BY_SUBTRACTION"] == 2
    assert c["PARAMETRIZE_EXPANSION_COUNT"] == 2
    assert c["NEW_FILE_TEST_COUNT"] == 26
    assert c["PARAMETRIZE_EXPANSION_FILES"] == [
        "tests/semantic_program/test_domain_string.py"]
    assert c["TEST_COUNT_DELTA_EXPLAINED"] is True
    assert c["CLASSIFICATION"] == "FULLY_EXPLAINED"
    assert c["HISTORICAL_REPORT_CHANGED"] is False


def test_co_che_parametrize_duoc_kiem_tren_MA_NGUON_that():
    """Đừng tin lời giải thích — đọc chính dòng `parametrize` trong tệp ấy."""
    p = GOC / "tests" / "semantic_program" / "test_domain_string.py"
    nguon = p.read_text(encoding="utf-8")
    assert nguon.count('parametrize("f", sorted(_SCRIPTS.glob("*.py")))') == 2
    assert '_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"' in nguon


# ══ CACHE / CANDIDATE ══════════════════════════════════════════════════════
def test_quyet_dinh_cache_cua_wave_chan_doan_van_la_KHONG_BUMP():
    """Quyết định *của wave chẩn đoán* là lịch sử — nó nằm ở artifact.

    `identity_and_cache_decision()` đọc `CACHE_VERSION` SỐNG, nên sau lượt sửa
    prompt nó trả `99`. Đừng đọc con số ấy như lời khai của wave chẩn đoán:
    wave ấy khai `98 / 98`, và bản đóng băng phải giữ nguyên.
    """
    d = D.identity_and_cache_decision()
    assert d["CACHE_VERSION_BEFORE"] == d["CACHE_VERSION_AFTER"] == D.doc_cache_version()
    assert d["CACHE_BUMP"] is False, "hàm này mô tả wave chẩn đoán, không mô tả wave sửa"
    if (D.RA / "IDENTITY_AND_CACHE_DECISION.json").exists():
        cu = json.loads((D.RA / "IDENTITY_AND_CACHE_DECISION.json")
                        .read_text(encoding="utf-8"))
        assert cu["CACHE_VERSION_BEFORE"] == cu["CACHE_VERSION_AFTER"] == "98"
        assert cu["CACHE_BUMP"] is False
        assert cu["PROMPT_CHANGED"] is False and cu["SCHEMA_CHANGED"] is False
        assert cu["MEASURED_SYSTEM_PATHS_TOUCHED"] == []
