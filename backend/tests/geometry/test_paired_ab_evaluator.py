# -*- coding: utf-8 -*-
"""HỢP ĐỒNG BỘ CHẤM GHÉP CẶP v2. **0 request mạng, 0 request model.**

`BENCHMARK_MEASUREMENT_REPAIR` (2026-09-20).

Bản 1 dùng `arm` để đổi luật ở đúng một trục (`construction_trace_ok`), và vế
Gemini của trục ấy **luôn sai** vì `validate_semantic_program` nâng
`declare_point` ra khỏi `statements` (9 câu lệnh thô → 5 sau thẩm định, ngưỡng
`≥ 6` không thể đạt). Bộ test này khoá lại để chuyện đó không xảy ra lần nữa.
"""
from __future__ import annotations

import ast
import dataclasses
import inspect
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
if str(GOC / "scripts") not in sys.path:
    sys.path.insert(0, str(GOC / "scripts"))

import paired_ab_evaluator as E  # noqa: E402
import run_primitive_compiler_ab as R  # noqa: E402

BENCH = R.BENCH
COMPILER_ARM = BENCH / "COMPILER_ARM_RESULTS.json"
GEMINI_ARM = BENCH / "GEMINI_ARM_RESULTS_REDACTED.json"

DAY_DU = dict(validation_ok=True, route_servable=True, scene_non_empty=True,
              point_labels_ok=True, topology_ok=True, squared_lengths_ok=True,
              perpendicular_ok=True, non_collinear_ok=True,
              final_memory_ok=True, answer_ok=True, visual_gate="COVERED")


def qs(arm="COMPILER", case_id="X", **kw):
    return E.QuanSat(case_id=case_id, arm=arm, **{**DAY_DU, **kw})


# ══ A — AUDIT PHÁT HIỆN LỖI CỦA BẢN 1 ══════════════════════════════════════
def test_A_audit_phat_hien_construction_trace_co_HAI_dinh_nghia():
    """Bản 1 dùng `arm` để đổi luật — quét AST chính hàm `cham` của nó."""
    cay = ast.parse(inspect.getsource(R.cham))
    ifexp = [n for n in ast.walk(cay) if isinstance(n, ast.IfExp)]
    dung_arm = [n for n in ifexp
                if any(getattr(x, "id", None) == "arm" for x in ast.walk(n.test))]
    assert dung_arm, "không tìm thấy nhánh theo `arm` — audit sai chỗ"
    gan = [n for n in ast.walk(cay) if isinstance(n, ast.Assign)
           and any(getattr(t, "attr", None) == "construction_trace_ok"
                   for t in n.targets)]
    assert gan and isinstance(gan[0].value, ast.IfExp), \
        "`construction_trace_ok` phải là chỗ luật đổi theo arm"


def test_A_ve_GEMINI_cua_truc_cu_LUON_SAI_ke_ca_voi_chuong_trinh_dung():
    """Chứng minh trục cũ KHÔNG chỉ lệch ngưỡng — nó suy biến trên một nhánh.

    `validate_semantic_program` nâng `declare_point` ra khỏi `statements`, nên
    một chương trình ĐÚNG của họ này còn 5 câu lệnh sau thẩm định. Ngưỡng cũ
    `≥ 6` vì thế không thể đạt.
    """
    from app.simulation.geometry_compiler import compiler as C
    from app.simulation.geometry_compiler import contract_adapter as A
    from app.simulation.semantic_program import validator as V

    mf = json.loads(R.MANIFEST.read_text(encoding="utf-8"))
    hd, _ = R.dung_hop_dong(mf["cases"][0])
    bd = C.bien_dich(A.build_fact_graph(hd).graph)
    val = V.validate_semantic_program(bd.program)

    assert val.ok
    assert len(bd.program["statements"]) >= 9, "chương trình thô phải đủ bước"
    assert len(val.spec.statements) < 6, (
        "nếu số này ≥ 6 thì chẩn đoán 'suy biến' SAI và phải điều tra lại")


# ══ B · C · D — BẤT BIẾN THEO NHÃN NHÁNH ═══════════════════════════════════
def test_B_doi_nhan_arm_KHONG_doi_ket_qua():
    a = E.danh_gia(qs(arm="COMPILER"))
    b = E.danh_gia(qs(arm="GEMINI"))
    assert a.axes == b.axes
    assert a.quality_pass == b.quality_pass
    assert a.silent_quality_failure == b.silent_quality_failure


@pytest.mark.parametrize("truc", sorted(E.PAIRED_AXES))
def test_C_hoan_doi_quan_sat_giua_hai_nhan_khong_doi_predicate(truc):
    """Cùng một quan sát LỆCH, gán cho nhánh nào cũng cho cùng phán quyết."""
    xau = {truc: (False if truc != "visual_gate" else "UNCOVERED")}
    a = E.danh_gia(qs(arm="COMPILER", **xau))
    b = E.danh_gia(qs(arm="GEMINI", **xau))
    assert a.axes[truc] == b.axes[truc] == E.FAIL
    assert a.canonical() == b.canonical()


def test_D_cung_quan_sat_cho_canonical_JSON_TRUNG_BYTE():
    a = json.dumps(E.danh_gia(qs(arm="COMPILER")).canonical(), sort_keys=True)
    b = json.dumps(E.danh_gia(qs(arm="GEMINI")).canonical(), sort_keys=True)
    assert a == b


# ══ E · F — MỘT PREDICATE CHO CẢ HAI NHÁNH ═════════════════════════════════
def test_E_moi_truc_COMPARABLE_dung_CHUNG_mot_ham():
    for ten, f in E.PAIRED_AXES.items():
        assert callable(f)
        assert "arm" not in inspect.signature(f).parameters


def test_F_KHONG_co_dispatch_theo_arm_ben_trong_predicate():
    """Quét AST mọi hàm của module: không predicate nào đọc `.arm`."""
    src = inspect.getsource(E)
    cay = ast.parse(src)
    for n in ast.walk(cay):
        if not isinstance(n, ast.FunctionDef):
            continue
        if n.name in ("tu_ban_ghi", "danh_gia"):
            continue  # hai hàm này CHỈ chép nhãn, không phán quyết theo nó
        doc = {x.attr for x in ast.walk(n) if isinstance(x, ast.Attribute)}
        assert "arm" not in doc, f"{n.name} đọc `arm`"
    # `danh_gia` được phép chép nhãn vào kết quả, nhưng không được rẽ nhánh
    cay_dg = ast.parse(inspect.getsource(E.danh_gia))
    for n in ast.walk(cay_dg):
        if isinstance(n, (ast.If, ast.IfExp)):
            assert not any(getattr(x, "attr", None) == "arm"
                           for x in ast.walk(n.test)), "`danh_gia` rẽ theo arm"


# ══ G · H — TRỤC PHẢI CHỊU TẢI ═════════════════════════════════════════════
@pytest.mark.parametrize("truc", sorted(E.PAIRED_AXES))
def test_G_doi_mot_truc_PASS_sang_FAIL_lam_quality_pass_doi(truc):
    assert E.danh_gia(qs()).quality_pass is True
    xau = {truc: (False if truc != "visual_gate" else "UNCOVERED")}
    assert E.danh_gia(qs(**xau)).quality_pass is False, truc


def test_H_moi_truc_dang_ky_deu_vao_phan_quyet():
    """Trục được tính mà không được dùng là trục không tồn tại."""
    cay = ast.parse(inspect.getsource(E.danh_gia))
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Name)
           and n.id == "PAIRED_AXES"]
    assert goi, "`danh_gia` phải duyệt CHÍNH bảng đăng ký, không chép tay"
    q = E.danh_gia(qs())
    assert set(q.axes) == set(E.PAIRED_AXES)


# ══ I — THIẾU DỮ LIỆU KHÔNG PHẢI SAI ═══════════════════════════════════════
@pytest.mark.parametrize("truc", sorted(E.PAIRED_AXES))
def test_I_thieu_du_lieu_cho_NOT_MEASURED_chu_khong_FAIL(truc):
    q = E.danh_gia(qs(**{truc: None}))
    assert q.axes[truc] == E.NOT_MEASURED
    assert q.quality_pass is False, "không đủ bằng chứng thì không PASS"
    assert q.silent_quality_failure is False, \
        "không quan sát được KHÔNG được kết tội là thất bại im lặng"


# ══ J — TELEMETRY KHÔNG ẢNH HƯỞNG PHÁN QUYẾT ═══════════════════════════════
def test_J_construction_telemetry_KHONG_vao_phan_quyet():
    a = E.danh_gia(qs(construction_step_count=11))
    b = E.danh_gia(qs(construction_step_count=0))
    c = E.danh_gia(qs(semantic_statement_count=5))
    assert a.canonical() == b.canonical() == c.canonical()
    assert a.quality_pass == b.quality_pass == c.quality_pass is True
    assert a.diagnostics["compiler_construction_step_count"] == 11
    assert not (set(E.DIAGNOSTIC_AXES) & set(E.PAIRED_AXES))


def test_J_hai_telemetry_co_HAI_TEN_khac_nhau():
    assert "compiler_construction_step_count" in E.DIAGNOSTIC_AXES
    assert "gemini_semantic_statement_count" in E.DIAGNOSTIC_AXES
    assert "construction_trace_ok" not in E.PAIRED_AXES


# ══ K · L · M — TÁCH NGUỒN ═════════════════════════════════════════════════
def test_K_khong_the_dung_output_compiler_lam_quan_sat_nhanh_Gemini():
    """`tu_ban_ghi` chỉ đọc bản ghi được đưa vào — không có đường nào lấy
    chương trình của nhánh kia."""
    cay = ast.parse(inspect.getsource(E))
    nhap = {n.module or "" for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)}
    nhap |= {a.name for n in ast.walk(cay) if isinstance(n, ast.Import)
             for a in n.names}
    assert not any("geometry_compiler" in m for m in nhap)


def test_L_M_hai_nhanh_cua_runner_van_tach_nguon():
    cay_g = ast.parse(inspect.getsource(R.chay_gemini))
    nhap_g = {n.module or "" for n in ast.walk(cay_g) if isinstance(n, ast.ImportFrom)}
    assert not any("geometry_compiler" in m for m in nhap_g)
    cay_c = ast.parse(inspect.getsource(R.chay_compiler))
    goi_c = {getattr(n.func, "attr", None) for n in ast.walk(cay_c)
             if isinstance(n, ast.Call)}
    assert "call_gemini" not in goi_c


# ══ N — KHÔNG RÒ RỈ ════════════════════════════════════════════════════════
_CAM = ("statements", "memory_declarations", "raw", "prompt", "scene",
        "objects", "input_value", "vertices", "faces")


def test_N_phan_quyet_khong_cho_du_lieu_tho():
    q = E.danh_gia(qs(construction_step_count=11))
    tho = json.dumps({"canonical": q.canonical(), "diagnostics": q.diagnostics})
    for cam in _CAM:
        assert f'"{cam}"' not in tho, cam


# ══ O · P · Q — TOÀN VẸN DỮ LIỆU LỊCH SỬ ═══════════════════════════════════
def test_O_token_latency_lay_NGUYEN_tu_artifact_da_commit():
    d = json.loads(GEMINI_ARM.read_text(encoding="utf-8"))
    for c in d["cases"]:
        assert "tokens" in c and "latency_ms" in c
        assert isinstance(c["tokens"].get("total_tokens"), int)


def test_P_tong_token_Gemini_khop_bao_cao():
    d = json.loads(GEMINI_ARM.read_text(encoding="utf-8"))
    t = [c["tokens"] for c in d["cases"]]
    assert sum(x["prompt_tokens"] for x in t) == 15129
    assert sum(x["candidates_tokens"] for x in t) == 3405
    assert sum(x["thoughts_tokens"] for x in t) == 4550
    assert sum(x["total_tokens"] for x in t) == 23084


@pytest.mark.parametrize("ten,bam", [
    ("PRIMITIVE_COMPILER_AB_MANIFEST.json", "8c2ad993139b90c447fcff40a338ac6740105f3079b2555c978c1d476284a8c0"),
    ("PRIMITIVE_COMPILER_AB_GROUND_TRUTH.json", "7c5e4af6f1fe3da7156d0a1a071a1772f924521095c745ca67dc457469956ca9"),
    ("GEMINI_ARM_RESULTS_REDACTED.json", "c3ed8b5f6946c3a2e8a9bf28a8f8d13baa2feb7736c46c6e6f070c1d4521c243"),
    ("COMPILER_ARM_RESULTS.json", "800b5cb12a31535489eb1f3ebe4803129b38c620621629b91be7e170c18379f4"),
    ("PAIRED_QUALITY_COMPARISON.json", "5676fca364ea565089ffec7501990d41d386543b1b67124bcd73d726ef125397"),
    ("TOKEN_COMPARISON.json", "931a7bc5eaea0fed10189372a8d74b326ca4ade036c6467b7b7ef38884cc3c61"),
    ("LATENCY_COMPARISON.json", "e6a26a68974c229f852335dbdaf06b613815b8b09f31acdca5af2d9a3034fd7a"),
    ("ACCEPTANCE_STATISTICS.json", "ea8425a4e1260cea1e090a08810f0ac72e22cd33ed048e9ecf3f37429acca097"),
])
def test_Q_artifact_live_GOC_bat_bien(ten, bam):
    """Wave sửa PHÉP ĐO, không được chạm một byte bằng chứng live nào."""
    import hashlib

    p = BENCH / ten
    tho = p.read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(tho).hexdigest() == bam, f"{ten} đã bị sửa"


# ══ R — KHÔNG MẠNG ═════════════════════════════════════════════════════════
def test_R_module_cham_khong_co_duong_ra_mang():
    src = inspect.getsource(E)
    cay = ast.parse(src)
    nhap = {n.module or "" for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)}
    nhap |= {a.name for n in ast.walk(cay) if isinstance(n, ast.Import)
             for a in n.names}
    for cam in ("httpx", "requests", "urllib", "socket", "gemini"):
        assert not any(cam in m for m in nhap), cam


# ══ S · T — MUTATION ═══════════════════════════════════════════════════════
def test_S_nguong_rieng_theo_arm_bi_bat():
    """Tiêm một predicate rẽ theo arm ⇒ bất biến nhãn nhánh phải ĐỎ."""
    that = E.PAIRED_AXES["topology_ok"]
    try:
        E.PAIRED_AXES["topology_ok"] = (
            lambda q: E.PASS if (q.arm == "COMPILER" or q.topology_ok) else E.FAIL)
        a = E.danh_gia(qs(arm="COMPILER", topology_ok=False))
        b = E.danh_gia(qs(arm="GEMINI", topology_ok=False))
        assert a.axes["topology_ok"] != b.axes["topology_ok"], \
            "phép tiêm không tạo ra bất tương xứng — test này vô nghĩa"
    finally:
        E.PAIRED_AXES["topology_ok"] = that
    assert E.danh_gia(qs(arm="COMPILER", topology_ok=False)).axes["topology_ok"] \
        == E.danh_gia(qs(arm="GEMINI", topology_ok=False)).axes["topology_ok"]


@pytest.mark.parametrize("truc", ["topology_ok", "answer_ok"])
def test_T_bo_truc_khoi_phan_quyet_bi_bat(truc):
    that = dict(E.PAIRED_AXES)
    try:
        del E.PAIRED_AXES[truc]
        assert set(E.danh_gia(qs()).axes) != set(that), "bỏ trục không lộ ra"
        assert E.danh_gia(qs(**{truc: False})).quality_pass is True, \
            "phép tiêm không làm phán quyết mù — test này vô nghĩa"
    finally:
        E.PAIRED_AXES.clear()
        E.PAIRED_AXES.update(that)
    assert E.danh_gia(qs(**{truc: False})).quality_pass is False


def test_dataclass_QuanSat_khong_mat_truc_nao():
    truong = {f.name for f in dataclasses.fields(E.QuanSat)}
    assert set(E.PAIRED_AXES) <= truong | {"visual_gate"}
