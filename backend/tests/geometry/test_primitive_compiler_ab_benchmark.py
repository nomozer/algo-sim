# -*- coding: utf-8 -*-
"""CỔNG TRƯỚC-LIVE của benchmark A/B. **0 request mạng trong toàn bộ tệp này.**

`PRIMITIVE_COMPILER_AB_TOKEN_LATENCY_BENCHMARK` (2026-09-20).

Bộ test này chạy TRƯỚC mọi lượt gọi provider. Nó không chấm chất lượng mô hình;
nó chấm **bộ đo** — vì một benchmark sai là một lượt tiêu quota không học được gì.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
if str(GOC / "scripts") not in sys.path:
    sys.path.insert(0, str(GOC / "scripts"))

import run_primitive_compiler_ab as R  # noqa: E402

MF = json.loads(R.MANIFEST.read_text(encoding="utf-8"))
GT = json.loads(R.GROUND_TRUTH.read_text(encoding="utf-8"))
CASES = MF["cases"]


# ══ MANIFEST ════════════════════════════════════════════════════════════════
def test_manifest_dang_ky_DUNG_bon_ca_khac_nhan_khac_so_lieu():
    assert len(CASES) == 4
    assert len({c["case_id"] for c in CASES}) == 4
    nhan = [tuple([c["apex"], *c["base"]]) for c in CASES]
    assert len(set(nhan)) == 4, "bốn ca phải khác nhãn"
    so = [tuple(c["lengths"].values()) for c in CASES]
    assert len(set(so)) == 4, "bốn ca phải khác số liệu"


def test_manifest_co_hoan_doi_thu_tu_facts_CO_KIEM_SOAT():
    thu_tu = {tuple(c["fact_order"]) for c in CASES}
    assert len(thu_tu) > 1, "thứ tự facts phải được hoán đổi giữa các ca"
    for c in CASES:
        assert sorted(c["fact_order"]) == [0, 1, 2]
        assert sorted(c["relation_order"]) == [0, 1]


def test_manifest_va_ground_truth_DONG_BANG_truoc_live():
    """Băm chốt TRƯỚC mọi request. Đổi sau khi live là `MEASUREMENT_INVALID`."""
    assert R._bam(R.MANIFEST) == (
        "8c2ad993139b90c447fcff40a338ac6740105f3079b2555c978c1d476284a8c0")
    assert R._bam(R.GROUND_TRUTH) == (
        "7c5e4af6f1fe3da7156d0a1a071a1772f924521095c745ca67dc457469956ca9")


def test_ground_truth_dung_theo_du_kien():
    """Đáp số phải DẪN từ dữ kiện, không phải con số ai đó chép tay."""
    for c in CASES:
        L = c["lengths"]
        mong = Fraction(L["leg_1"]) * Fraction(L["leg_2"]) / 2 * Fraction(L["height"]) / 3
        assert Fraction(GT["expected"][c["case_id"]]["volume"]) == mong, c["case_id"]


# ══ TÁCH BIỆT ĐÁP ÁN ════════════════════════════════════════════════════════
def test_manifest_KHONG_chua_dap_so():
    tho = R.MANIFEST.read_text(encoding="utf-8")
    for c in CASES:
        v = GT["expected"][c["case_id"]]["volume"]
        assert f'"{v}"' not in tho, f"đáp số {v} lọt vào manifest"


def test_compiler_KHONG_import_ground_truth():
    """Quét AST gói compiler — không quét văn bản, để một chữ trong docstring
    không làm test đỏ (và cũng không che được một lượt đọc thật)."""
    goc = GOC / "app" / "simulation" / "geometry_compiler"
    for f in goc.glob("*.py"):
        cay = ast.parse(f.read_text(encoding="utf-8"))
        ten = {n.id for n in ast.walk(cay) if isinstance(n, ast.Name)}
        thuoc = {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)}
        nhap = {a.name for n in ast.walk(cay) if isinstance(n, ast.Import)
                for a in n.names} | {n.module or "" for n in ast.walk(cay)
                                     if isinstance(n, ast.ImportFrom)}
        assert "GROUND_TRUTH" not in (ten | thuoc), f.name
        assert not any("ground_truth" in m for m in nhap), f.name
        assert not any("ab_benchmark" in m or "primitive_compiler_ab" in m
                       for m in nhap), f.name


def test_hop_dong_gui_cho_hai_nhanh_KHONG_chua_dap_so():
    """RequestContract và prompt đều không được mang đáp số."""
    for c in CASES:
        hd, de = R.dung_hop_dong(c)
        v = GT["expected"][c["case_id"]]["volume"]
        tho = json.dumps(hd.model_dump(mode="json"), ensure_ascii=False)
        assert v not in tho or Fraction(v) in (
            Fraction(x) for x in c["lengths"].values()), c["case_id"]
        assert v not in de or Fraction(v) in (
            Fraction(x) for x in c["lengths"].values()), c["case_id"]


def test_evaluator_la_noi_DUY_NHAT_doc_ground_truth():
    src = inspect.getsource(R)
    cay = ast.parse(src)
    ham = {n.name for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)
           and "GROUND_TRUTH" in ast.get_source_segment(src, n or "") or ""}
    # `GROUND_TRUTH` chỉ được mở ở `main`; `cham` nhận `mong` như THAM SỐ.
    assert "mong" in inspect.signature(R.cham).parameters


# ══ NGÂN SÁCH VÀ STOP RULE ══════════════════════════════════════════════════
def test_tran_HTTP_dat_o_TRANSPORT_va_chan_that():
    cong = R.CongHttp(tran=4)
    for i in range(4):
        cong.truoc_khi_gui(f"C{i}")
    assert cong.da_gui == 4
    with pytest.raises(RuntimeError, match="HẾT TRẦN"):
        cong.truoc_khi_gui("C5")
    assert cong.bi_chan == 1


def test_loi_provider_KHOA_cong_khong_gui_them():
    cong = R.CongHttp(tran=4)
    cong.truoc_khi_gui("C0")
    cong.khoa = True
    with pytest.raises(RuntimeError, match="KHOÁ"):
        cong.truoc_khi_gui("C1")
    assert cong.da_gui == 1


def test_ngan_sach_khai_dung_trong_manifest():
    assert MF["max_total_synthesis_requests"] == 4
    caps = MF["per_case_caps"]
    assert caps == {"vision": 0, "analyze": 0, "synthesis": 1,
                    "repair": 0, "retries": 0}


def test_runner_KHONG_co_nhanh_repair_hay_retry():
    """Quét AST lời gọi `call_gemini`: phải ép `max_attempts=1` và không có
    vòng lặp gửi lại. Không quét văn bản — chữ `repair` trong docstring không
    phải một nhánh repair."""
    src = inspect.getsource(R)
    cay = ast.parse(src)
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call)
           and getattr(n.func, "attr", None) == "call_gemini"]
    assert len(goi) == 1, "phải có ĐÚNG MỘT nơi gọi provider"
    kw = {k.arg: k.value for k in goi[0].keywords}
    assert "max_attempts" in kw and getattr(kw["max_attempts"], "value", None) == 1
    assert "timeout_seconds" in kw
    ten_ham = {n.name for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)}
    assert not any("repair" in t.lower() or "retry" in t.lower() for t in ten_ham)


# ══ CÙNG MỘT BỘ CHẤM ════════════════════════════════════════════════════════
def test_hai_nhanh_dung_CUNG_MOT_evaluator():
    src = inspect.getsource(R)
    cay = ast.parse(src)
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call)
           and getattr(n.func, "id", None) == "cham"]
    assert len(goi) == 2, "phải có đúng hai nơi gọi `cham` — một cho mỗi nhánh"


def test_evaluator_CHO_MOI_TRUC_vao_phan_quyet_quality_pass():
    """⚠️ Test này sinh ra vì phép tiêm FB8 ĐI LỌT.

    Bỏ `topology_ok` khỏi biểu thức `quality_pass` mà 22/22 vẫn xanh — vì
    compiler vốn đúng topology nên phán quyết không đổi. Một trục được TÍNH mà
    không được DÙNG là một trục không tồn tại. Quét AST chính biểu thức ấy.
    """
    src = inspect.getsource(R.cham)
    cay = ast.parse(src.strip())
    gan = [n for n in ast.walk(cay) if isinstance(n, ast.Assign)
           and any(getattr(t, "attr", None) == "quality_pass" for t in n.targets)]
    assert len(gan) == 1, "phải có đúng một chỗ quyết `quality_pass`"
    dung = {n.attr for n in ast.walk(gan[0].value) if isinstance(n, ast.Attribute)}
    for truc in ("validation_ok", "route_servable", "scene_non_empty",
                 "point_labels_ok", "topology_ok", "squared_lengths_ok",
                 "perpendicular_ok", "non_collinear_ok", "final_memory_ok",
                 "answer_ok"):
        assert truc in dung, f"`{truc}` bị tính nhưng KHÔNG vào phán quyết"


def test_HAI_NHANH_khong_lay_output_cua_nhau():
    """⚠️ Test này sinh ra vì phép tiêm FB2 ĐI LỌT.

    Đưa chương trình của COMPILER vào chỗ chấm nhánh GEMINI mà 25/25 vẫn xanh —
    benchmark khi ấy chấm compiler hai lần và gọi một nửa là 'baseline'. Phép
    đếm chỗ gọi `cham` không bắt được, vì số chỗ gọi không đổi.

    Quét AST từng nhánh: nhánh Gemini KHÔNG được nhắc tới gói compiler, nhánh
    compiler KHÔNG được gọi provider.
    """
    cay_g = ast.parse(inspect.getsource(R.chay_gemini))
    ten_g = {n.id for n in ast.walk(cay_g) if isinstance(n, ast.Name)}
    nhap_g = {n.module or "" for n in ast.walk(cay_g) if isinstance(n, ast.ImportFrom)}
    assert not any("geometry_compiler" in m for m in nhap_g), \
        "nhánh GEMINI nhập gói compiler — nguy cơ chấm nhầm output"
    assert not ({"bien_dich", "build_fact_graph"} & ten_g), \
        "nhánh GEMINI gọi compiler"

    cay_c = ast.parse(inspect.getsource(R.chay_compiler))
    goi_c = {getattr(n.func, "attr", None) for n in ast.walk(cay_c)
             if isinstance(n, ast.Call)}
    assert "call_gemini" not in goi_c, "nhánh COMPILER gọi provider"


def test_evaluator_kiem_du_cac_truc_bat_buoc():
    truc = set(R.KetQuaCham.__dataclass_fields__)
    for t in ("topology_ok", "squared_lengths_ok", "perpendicular_ok",
              "non_collinear_ok", "final_memory_ok", "answer_ok",
              "silent_quality_failure", "hallucinated_critical_facts",
              "construction_trace_ok", "point_labels_ok"):
        assert t in truc, t


# ══ NHÁNH B OFFLINE — 4/4 ══════════════════════════════════════════════════
@pytest.fixture(scope="module")
def compiler_arm():
    return R.chay_compiler(CASES, GT, vong=5)


def test_compiler_dat_4_tren_4_truoc_khi_duoc_phep_goi_provider(compiler_arm):
    dat = [c for c in compiler_arm["cases"] if c["cham"]["quality_pass"]]
    assert len(dat) == 4, [
        (c["case_id"], c["cham"]["diagnostics"], c["cham"]["visual_gate"])
        for c in compiler_arm["cases"] if not c["cham"]["quality_pass"]]


def test_compiler_moi_ca_dat_tung_truc(compiler_arm):
    for c in compiler_arm["cases"]:
        k = c["cham"]
        assert c["adapter_status"] == "VALID", c["case_id"]
        assert c["eligibility"] == "SUPPORTED", c["case_id"]
        assert c["compile_status"] == "COMPILED", c["case_id"]
        assert c["model_tokens"] == 0 and c["model_requests"] == 0
        assert c["ignored_keys"] == []
        assert k["scene_non_empty"] and k["point_labels_ok"], c["case_id"]
        assert k["topology_ok"] and k["squared_lengths_ok"], c["case_id"]
        assert k["perpendicular_ok"] and k["non_collinear_ok"], c["case_id"]
        assert k["final_memory_ok"] and k["answer_ok"], c["case_id"]
        assert k["visual_gate"] == "COVERED", c["case_id"]
        assert not k["silent_quality_failure"], c["case_id"]
        assert c["construction_steps"] >= 10, c["case_id"]


def test_compiler_tat_dinh_tren_moi_ca(compiler_arm):
    for c in compiler_arm["cases"]:
        assert c["deterministic"] is True, c["case_id"]


# ══ REQUEST EQUIVALENCE ════════════════════════════════════════════════════
def test_request_dung_builder_san_pham_va_chi_khac_o_du_kien():
    dung = [R.dung_request(*R.dung_hop_dong(c)) for c in CASES]
    sys_p = {d[0] for d in dung}
    schema = {json.dumps(d[2], sort_keys=True) for d in dung}
    temp = {d[3] for d in dung}
    assert len(sys_p) == 1, "system prompt phải GIỐNG NHAU giữa bốn ca"
    assert len(schema) == 1, "lược đồ phải GIỐNG NHAU"
    assert temp == {0.1}
    assert len({d[1] for d in dung}) == 4, "user prompt phải khác theo dữ kiện"


def test_prompt_KHONG_noi_day_la_benchmark():
    for c in CASES:
        _, user, _, _ = R.dung_request(*R.dung_hop_dong(c))
        thap = user.lower()
        for cam in ("benchmark", "a/b", "so sánh", "compiler", "đáp số là"):
            assert cam not in thap, cam


def test_model_va_temperature_dung_manifest():
    assert MF["model"] == "gemini-2.5-flash"
    assert MF["temperature"] == 0.1


# ══ KHÔNG RÒ RỈ ════════════════════════════════════════════════════════════
def test_ket_qua_KHONG_luu_raw_prompt_response_hay_program(compiler_arm):
    tho = json.dumps(compiler_arm, ensure_ascii=False)
    for cam in ("statements", "memory_declarations", "vertices", "faces",
                "problem_text", "input_value"):
        assert f'"{cam}"' not in tho, cam


_KHOA_CAM = ("statements", "memory_declarations", "raw", "response_text",
             "prompt", "input_value", "msg", "ctx", "scene", "objects")


def test_ban_ghi_nhanh_GEMINI_khong_co_khoa_tho():
    """⚠️ Test này sinh ra vì phép tiêm FB10 ĐI LỌT.

    Nhét `statements` (chương trình thô của mô hình) vào bản ghi nhánh Gemini mà
    23/23 vẫn xanh — vì test rò rỉ cũ chỉ soi nhánh COMPILER, còn bản ghi Gemini
    chỉ sinh ra trong một lượt LIVE mà bộ test không chạy. Quét AST chính chỗ
    dựng bản ghi ấy, nên lỗi lộ ra TRƯỚC khi tiêu quota.
    """
    cay = ast.parse(inspect.getsource(R.chay_gemini))
    for d in [n for n in ast.walk(cay) if isinstance(n, ast.Dict)]:
        khoa = {k.value for k in d.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        xau = khoa & set(_KHOA_CAM)
        assert not xau, f"bản ghi nhánh Gemini chở khoá thô: {sorted(xau)}"


def test_artifact_GEMINI_da_ghi_khong_co_du_lieu_tho():
    """Nếu đã có kết quả live, chính TỆP ấy phải sạch."""
    p = R.BENCH / "GEMINI_ARM_RESULTS_REDACTED.json"
    if not p.exists():
        pytest.skip("chưa có kết quả live")
    d = json.loads(p.read_text(encoding="utf-8"))

    def moi_khoa(o):
        if isinstance(o, dict):
            for k, v in o.items():
                yield k
                yield from moi_khoa(v)
        elif isinstance(o, list):
            for v in o:
                yield from moi_khoa(v)

    xau = set(moi_khoa(d)) & set(_KHOA_CAM)
    assert not xau, f"artifact chở khoá thô: {sorted(xau)}"
    tho = json.dumps(d, ensure_ascii=False)
    assert "AIza" not in tho and "x-goog-api-key" not in tho


_TUYEN_BO_CAM = (
    "END_TO_END_TOKEN_REDUCTION = 100",
    "END_TO_END_TOKEN_REDUCTION = 100%",
    "TOKEN_OPTIMIZATION = PASS",
    "FULL_PIPELINE_AI_FREE = YES",
    "ANALYZE_ELIMINATED = YES",
    "PRODUCTION_DEFAULT_CHANGED = YES",
    "MERGE_ALLOWED = YES",
)


def test_KHONG_suy_end_to_end_tu_token_tang_synthesis():
    """Token đo được chỉ thuộc TẦNG SYNTHESIS. Suy ra mức tiết kiệm end-to-end
    từ đó là nhân một tỉ lệ của một tầng lên cả pipeline — vision và analyze
    vẫn tiêu token."""
    p = R.BENCH / "TOKEN_COMPARISON.json"
    if not p.exists():
        pytest.skip("chưa có TOKEN_COMPARISON")
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["END_TO_END_TOKEN_REDUCTION"] == "NOT_MEASURED"
    assert d["TOKEN_OPTIMIZATION"] == "NOT_PRODUCTION_ESTABLISHED"
    assert any("vision và analyze" in s for s in d["PHAI_KHAI_KEM"])
    tho = p.read_text(encoding="utf-8")
    for cam in _TUYEN_BO_CAM:
        assert cam not in tho, cam


def test_bao_cao_KHONG_chua_tuyen_bo_bi_cam():
    bc = R.REPO / "docs" / "PRIMITIVE_COMPILER_AB_TOKEN_LATENCY_BENCHMARK.md"
    if not bc.exists():
        pytest.skip("chưa có báo cáo")
    tho = bc.read_text(encoding="utf-8")
    for cam in _TUYEN_BO_CAM:
        assert cam not in tho, cam


def test_bo_che_bi_mat_hoat_dong():
    assert "AIza" not in R.che("key=AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123")
    assert "<đã che>" in R.che("x-goog-api-key: abc123xyz")
