# -*- coding: utf-8 -*-
"""TẦNG TOÀN VẸN CỦA BỘ ĐO — tám sự cố lịch sử, dựng lại. **0 lượt gọi model.**

    `ACCEPTANCE_RUNNER_INTEGRITY` §24, 2026-09-04.

Mỗi ca dưới đây **tiêm lại một sự cố đã xảy ra thật** rồi đòi tầng toàn vẹn đỏ.
Một cổng chưa bao giờ đỏ là một cổng chưa được chứng minh — và bảy trong tám sự
cố này đã lọt qua vì không có cổng nào cả.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from acceptance_integrity import (  # noqa: E402
    ARTIFACT_SCHEMA_VERSION,
    IntegrityError,
    chuan_hoa_telemetry,
    doc_artifact,
    ghi_artifact,
    kiem_bat_bien_token,
    kiem_bo_ca,
    kiem_moi_truong,
    moi_truong_hien_tai,
    seal_bo_ca,
    tom_tat_tu_artifact,
    tu_kiem_tom_tat,
)
from acceptance_verdict import (  # noqa: E402
    cham_ca_am,
    co_giai_doan,
    phan_loai,
    sua_duoc,
    trich_ket_qua,
)


class FakeOutcome:
    """Phán quyết route giả — chỉ mang đúng các trường bộ đo đọc."""

    def __init__(self, **kw):
        self.stage_reached = kw.get("stage_reached", "served")
        self.executable = kw.get("executable", True)
        self.servable = kw.get("servable", True)
        self.error_code = kw.get("error_code")
        self.failure_category = kw.get("failure_category")
        self.reason = kw.get("reason")
        self.details = kw.get("details", [])
        self.final_memory = kw.get("final_memory")
        self.envelope = kw.get("envelope")


# ══ A · TELEMETRY — `prompt_tokens`, KHÔNG được in 0 ══════════════════════
def test_A_telemetry_ten_truong_gemini_KHONG_ra_0():
    """SỰ CỐ ①: runner V1 đọc `input`/`output`; `usage_report()` trả
    `prompt_tokens`/`candidates_tokens`. `.get(k, 0)` cho 0, và 0 là một con số
    hợp lệ nên không gì đỏ."""
    tho = {"semantic_analyze": {
        "prompt_tokens": 1200, "candidates_tokens": 340, "thoughts_tokens": 900,
        "cached_content_tokens": 0, "total_tokens": 2440, "calls": 1}}
    c = chuan_hoa_telemetry(tho)
    assert c["tong"]["input_tokens"] == 1200
    assert c["tong"]["output_tokens"] == 340
    assert c["tong"]["thought_tokens"] == 900
    assert c["calls"] == 1
    assert c["truong_thieu"] == []
    assert c["raw"] == tho, "bản THÔ phải giữ nguyên để soát lại được"


def test_A2_truong_LA_lam_DUNG_luot_do_chu_khong_bao_0():
    """Provider đổi lược đồ ⇒ KÊU TO. Im lặng bỏ qua là cách sự cố ① tái diễn
    dưới một cái tên khác."""
    with pytest.raises(IntegrityError, match="KHÔNG BIẾT"):
        chuan_hoa_telemetry({"s": {"promptTokenCount": 5, "calls": 1}})


def test_A3_THIEU_telemetry_khac_han_0_token():
    """`MISSING_TELEMETRY != 0_TOKENS`."""
    c = chuan_hoa_telemetry({"s": {"prompt_tokens": 10, "calls": 1}})
    assert c["theo_stage"]["s"]["input_tokens"] == 10
    assert c["theo_stage"]["s"]["total_tokens"] is None
    assert "total_tokens" in c["truong_thieu"]


def test_A4_thieu_calls_la_loi_vi_so_goi_phai_DEM_duoc():
    """§10 — `APPLICATION_LLM_CALLS` đếm từ bản ghi, không suy từ số stage."""
    with pytest.raises(IntegrityError, match="calls"):
        chuan_hoa_telemetry({"s": {"prompt_tokens": 1}})


def test_A5_bat_bien_token_bat_duoc_tong_nho_hon_thanh_phan():
    xau = {"theo_stage": {"s": {"total_tokens": 100, "input_tokens": 900,
                                "output_tokens": 10, "thought_tokens": 0}}}
    assert kiem_bat_bien_token(xau), "tổng < input mà không ai kêu"
    tot = {"theo_stage": {"s": {"total_tokens": 1000, "input_tokens": 900,
                                "output_tokens": 10, "thought_tokens": 50}}}
    assert kiem_bat_bien_token(tot) == []


# ══ B · THIẾU RequestContract ⇒ TOÀN VẸN ĐỎ ═══════════════════════════════
def test_B_thieu_request_contract_lam_hong_kiem_toan_ven(tmp_path):
    """SỰ CỐ ②: artifact V1 không lưu `RequestContract`, nên `cylinder_1` không
    tái dựng được — replay tất định phải suy lại `InputFact` từ trí nhớ."""
    from acceptance_verdict import __all__ as _  # noqa: F401

    day_du = {"artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
              "id": "c1", "de": "…", "request_contract": {"problem_text": "…"},
              "chuong_trinh": {}, "phan_lop": "CORRECT_SERVABLE_RESULT"}
    thieu = {k: v for k, v in day_du.items() if k != "request_contract"}

    assert _du_de_replay(day_du) is True
    assert _du_de_replay(thieu) is False


def _du_de_replay(r: dict) -> bool:
    """§4 — replay tất định cần đủ bốn thứ, không được thiếu cái nào."""
    return all(r.get(k) is not None
               for k in ("de", "request_contract", "chuong_trinh", "phan_lop"))


# ══ C · KẾT QUẢ LẤY TỪ final_memory, KHÔNG TỪ scene3d ═════════════════════
def test_C_ket_qua_trich_tu_THAM_QUYEN_chu_khong_tu_scene3d():
    """SỰ CỐ ③, và đây là ca `ball_1` của probe §18 nguyên hình dạng:
    `final_memory` có `R = 6`, `V = 288π`; `scene3d` **rỗng** vì ca bị chặn ở
    `postconditions` nên không dựng cảnh. Runner cũ đọc `scene3d` ⇒ thấy rỗng ⇒
    kết luận mô hình sai."""
    from fractions import Fraction as F

    from app.simulation.geometry.radical import radical

    oc = FakeOutcome(
        stage_reached="postconditions", executable=True, servable=False,
        final_memory={"R": F(6), "V": radical(288, 1, mu=1)},
        envelope={"scene3d": {"objects": []}})

    kq = trich_ket_qua(oc)
    assert kq["dai_luong"] == {"R": "6", "V": "288π"}
    assert kq["nguon"] == "outcome.final_memory"


def test_C2_runner_moi_KHONG_duoc_doc_scene3d_lam_ket_qua():
    """Cấm bằng máy: quét mã bộ đo mới. `RESULT_EXTRACTION_FROM_SCENE3D = 0`."""
    import acceptance_verdict

    src = Path(acceptance_verdict.__file__).read_text(encoding="utf-8")
    than = src.split("def trich_ket_qua")[1].split("\ndef ")[0]
    than = than.split('"""')[2]                    # bỏ docstring
    for cam in ("scene3d", "envelope", "objects"):
        assert cam not in than, f"trích kết quả chạm `{cam}`"


# ══ D · KHÔNG ĐÈ ARTIFACT ═════════════════════════════════════════════════
def test_D_ghi_de_bi_TU_CHOI_truoc_khi_truncate(tmp_path):
    """SỰ CỐ ④: một lệnh shell coi artifact đã commit là ĐẦU RA và ghi đè nó."""
    f = tmp_path / "stage.json"
    ghi_artifact(f, {"artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
                     "so": 1})
    with pytest.raises(IntegrityError, match="ĐÃ TỒN TẠI"):
        ghi_artifact(f, {"so": 2})
    # Quan trọng nhất: nội dung CŨ còn nguyên, không bị truncate.
    assert doc_artifact(f)["so"] == 1


def test_D2_ghi_nguyen_khoi_khong_de_lai_JSON_cut(tmp_path, monkeypatch):
    """Tiến trình chết giữa lúc ghi ⇒ file cũ nguyên vẹn HOẶC không có file —
    không bao giờ là JSON cụt."""
    import acceptance_integrity as ai

    f = tmp_path / "a.json"
    ghi_artifact(f, {"artifact_schema_version": ARTIFACT_SCHEMA_VERSION, "v": 1})

    def no(*a, **k):
        raise OSError("đĩa đầy giữa chừng")

    monkeypatch.setattr(ai.os, "replace", no)
    with pytest.raises(OSError):
        ghi_artifact(f, {"v": 2}, cho_de=True)
    assert doc_artifact(f)["v"] == 1
    assert list(tmp_path.glob("*.tmp")) == [], "còn sót file tạm"


# ══ E · CA ÂM DỪNG SỚM ⇒ KHÔNG PHẢI CHỨNG MINH RANH GIỚI ══════════════════
def test_E_ca_am_chet_som_o_R0_KHONG_duoc_tinh_la_chung_minh():
    """SỰ CỐ ⑥, nguyên văn ví dụ của đề bài: ca nhắm *"thiết diện cong xiên
    chưa hỗ trợ"* nhưng chết ở `input_not_grounded` (R0)."""
    ca = {"id": "am_1", "loai": "am",
          "target_boundary": "thiết diện cong xiên chưa hỗ trợ",
          "expected_codes": ["requested_operation_uncovered"]}
    oc = FakeOutcome(stage_reached="grounding", executable=False,
                     servable=False, error_code="input_not_grounded")

    d = cham_ca_am(ca, oc, schema_ok=True)
    assert d["fail_closed"] is True
    assert d["target_boundary_demonstrated"] is False
    assert "DỪNG SỚM" in d["ghi_chu"]
    assert phan_loai(oc, schema_ok=True, la_ca_am=True,
                     boundary_ok=False) == "UNRELATED_FAIL_CLOSED"


def test_E2_ca_am_cham_DUNG_ranh_gioi_thi_moi_la_HONEST_REFUSAL():
    ca = {"id": "am_1", "loai": "am",
          "target_boundary": "phép chưa phủ",
          "expected_codes": ["requested_operation_uncovered"]}
    oc = FakeOutcome(stage_reached="structural_coverage", executable=False,
                     servable=False, error_code="requested_operation_uncovered")
    d = cham_ca_am(ca, oc, schema_ok=True)
    assert d["target_boundary_demonstrated"] is True
    assert phan_loai(oc, schema_ok=True, la_ca_am=True,
                     boundary_ok=True) == "HONEST_UNSUPPORTED_REFUSAL"


def test_E3_ca_am_KHONG_khai_ranh_gioi_thi_TU_CHOI_cham():
    """Không khai thì mọi lượt chết đều trông như thành công."""
    with pytest.raises(ValueError, match="expected_codes"):
        cham_ca_am({"id": "x", "loai": "am"}, FakeOutcome(servable=False),
                   schema_ok=True)


# ══ F · LỖI HỆ KHÔNG ĐƯỢC TÍNH VÀO CỘT MÔ HÌNH ════════════════════════════
def test_F_ball_1_cua_probe_18_la_SYSTEM_VERIFICATION_FAILURE():
    """SỰ CỐ ⑦ + §14. Chương trình ĐÚNG, engine ra `288π`, checker không nhận
    `curved_solid` ⇒ lỗi HỆ. Runner cũ xếp `MODEL_COMPOSITION_FAILURE`."""
    oc = FakeOutcome(
        stage_reached="postconditions", executable=True, servable=False,
        error_code="postcondition_violated", failure_category="verification_gap",
        details=["cần một `solid`"], reason="Chương trình tự mâu thuẫn…")
    assert phan_loai(oc, schema_ok=True) == "SYSTEM_VERIFICATION_FAILURE"


def _bac_o_cong_phu():
    return FakeOutcome(stage_reached="structural_coverage", executable=False,
                       servable=False,
                       error_code="requested_operation_uncovered")


def test_F2_hai_bang_KHOP_thi_cong_phu_bac_la_loi_MO_HINH():
    """ĐÍNH CHÍNH 2026-09-04, đo bằng quota thật (`probe-contract-waves`).

    `REQUESTED_OPERATION_UNCOVERED` TỪNG được xếp thẳng `SYSTEM_COVERAGE_FAILURE`
    vì sự cố sinh ra nhánh này (`CURVED_MODEL_ACCEPTANCE_V1`) đúng là lỗi hệ.
    Nhưng ca `cylinder_2` phát cùng mã ấy vì lý do ngược hẳn: thẻ ghi rõ
    `construct_section: solid:tên<solid>` và `radius(of:tên<circle3|curved_solid>)`,
    mô hình vẫn cắt khối CONG bằng `construct_section` rồi đo `radius` trên
    `section`. Đường đúng (`intersect_plane_curved` → `circle3`) có sẵn trên thẻ.

    Nhãn sai ấy làm luật DỪNG-KHI-LỖI-HỆ nổ nhầm và giết lượt đo trước ca thứ
    hai — cùng cái giá mà `test_F3b` đã ghi một lần cho `LEARNER_SURFACE_INCOMPLETE`.
    """
    assert phan_loai(_bac_o_cong_phu(), schema_ok=True) == \
        "MODEL_COMPOSITION_FAILURE"


def test_F2b_cay_hien_tai_KHONG_co_lech_bang_nen_tien_de_cua_F2_la_THAT():
    """F2 chỉ đúng khi hai bảng thật sự khớp. Kiểm tiền đề, đừng giả định nó.

    Rỗng được là nhờ `OBLIGATION_KINDS` DẪN XUẤT từ `BANG_PHEP_DO` (2026-09-03)
    thay vì chép tay — trước đó `volume` thiếu `curved_solid` ở đây.
    """
    from acceptance_verdict import _cong_phu_hep_hon_bo_kiem

    assert _cong_phu_hep_hon_bo_kiem() == []


def test_F2c_LECH_BANG_that_thi_nhan_TU_LAT_ve_SYSTEM(monkeypatch):
    """TIÊM LỖI — guard chưa từng đỏ là guard chưa được chứng minh.

    Dựng lại đúng hình dạng V1: cổng phủ hẹp hơn thứ bộ kiểm chứng thực được.
    Nếu nhãn không lật về HỆ, bộ đo đã mất khả năng bắt lại chính sự cố đã tốn
    26 lượt model.
    """
    from acceptance_verdict import _cong_phu_hep_hon_bo_kiem
    from app.simulation.semantic_program.obligations import OBLIGATION_KINDS

    hep = OBLIGATION_KINDS["volume"] - {"curved_solid"}
    assert hep != OBLIGATION_KINDS["volume"], "tiền đề tiêm hỏng"
    monkeypatch.setitem(OBLIGATION_KINDS, "volume", hep)

    assert _cong_phu_hep_hon_bo_kiem() == ["volume:curved_solid"]
    assert phan_loai(_bac_o_cong_phu(), schema_ok=True) == \
        "SYSTEM_COVERAGE_FAILURE"


def test_F3_postcondition_vi_GIA_TRI_LECH_van_la_loi_MO_HINH():
    """Chiều ngược lại của §14, và đây là chỗ dễ vá quá tay: nếu mọi
    `postcondition_violated` đều thành SYSTEM thì bộ đo hết khả năng bắt một
    chương trình khai sai đáp số.

    Ranh giới đọc từ chính lời checker — *"giá trị không khớp"* nghĩa là nó ĐÃ
    tính lại được từ hình rồi thấy lệch.
    """
    from app.simulation.semantic_program.geometry_obligations import _LECH

    oc = FakeOutcome(
        stage_reached="postconditions", executable=True, servable=False,
        error_code="postcondition_violated",
        details=[f"{_LECH}: chương trình khai V = 100, khối cho V = 30"])
    assert phan_loai(oc, schema_ok=True) == "MODEL_COMPOSITION_FAILURE"


def test_F3b_learner_surface_thieu_binding_la_loi_MO_HINH():
    """ĐÍNH CHÍNH đo được bằng quota thật (probe V2 lượt 1).

    `LEARNER_SURFACE_INCOMPLETE` từng bị xếp `SYSTEM_VERIFICATION_FAILURE` vì
    `failure_category` của nó là `verification_gap` — đọc NHÃN thay vì đọc
    CỔNG. `ball_1` phơi ra: chương trình chạy đúng, `postconditions_pass=True`,
    `R = 6`, `V = 288π`, nhưng `visual_bindings` RỖNG nên biến mang dữ kiện đề
    không có đường lên màn hình. Cổng phán đúng; mô hình mới là bên thiếu.

    Hậu quả thật: luật DỪNG-KHI-LỖI-HỆ nổ nhầm và lượt đo chết giữa chừng.
    """
    oc = FakeOutcome(
        stage_reached="learner_surface", executable=True, servable=False,
        error_code="learner_surface_incomplete",
        failure_category="verification_gap",
        details=["'IA_dist' mang dữ liệu đề nhưng không có binding"])
    assert phan_loai(oc, schema_ok=True) == "MODEL_FIRST_BINDING_FAILURE"


def test_F3c_KHONG_checker_thi_van_la_loi_HE():
    """Vế phải giữ: nghĩa vụ KHÔNG có checker server-owned là hệ hụt thật."""
    oc = FakeOutcome(stage_reached="verification", executable=True,
                     servable=False,
                     error_code="semantic_verification_unavailable",
                     failure_category="verification_gap")
    assert phan_loai(oc, schema_ok=True) == "SYSTEM_VERIFICATION_FAILURE"


def test_F4_diem_BIA_van_la_loi_MO_HINH_vi_R0_dang_chay_dung():
    """Chiều còn lại: R0 bác một điểm bịa ⇒ mô hình sai, hệ đúng."""
    oc = FakeOutcome(stage_reached="grounding", executable=False,
                     servable=False, error_code="input_not_grounded")
    assert phan_loai(oc, schema_ok=True) == "MODEL_GROUNDING_FAILURE"


def test_F5_moi_lop_deu_nam_trong_bang_da_khai():
    """Phân loại không được đẻ ra một nhãn ngoài danh sách — báo cáo đếm theo
    danh sách ấy, nhãn lạ sẽ rơi vào khoảng trống mà không ai thấy."""
    from acceptance_verdict import LOP_PHAN_QUYET

    mau = [
        (FakeOutcome(), True, None),
        (FakeOutcome(stage_reached="ir_static", executable=False,
                     servable=False, error_code="semantic_program_invalid"),
         True, None),
        (FakeOutcome(stage_reached="execution", executable=False,
                     servable=False, error_code="interpreter_budget_exhausted"),
         True, None),
        (FakeOutcome(stage_reached="transport", executable=True,
                     servable=False, error_code="semantic_program_invalid"),
         True, None),
        (None, False, None),
    ]
    for oc, ok, b in mau:
        assert phan_loai(oc, schema_ok=ok, boundary_ok=b) in LOP_PHAN_QUYET


# ══ G · MÔI TRƯỜNG ĐỔI GIỮA LƯỢT ⇒ DỪNG ═══════════════════════════════════
def test_G_moi_truong_doi_giua_hai_luot_goi_thi_ABORT():
    goc = moi_truong_hien_tai()
    kiem_moi_truong(goc)                      # không đổi ⇒ im lặng đi qua

    lech = json.loads(json.dumps(goc))
    lech["components"]["prompts"] = "0" * 64
    with pytest.raises(IntegrityError, match="MÔI TRƯỜNG ĐỔI"):
        kiem_moi_truong(lech)


def test_G2_bo_ca_doi_giua_luot_thi_ABORT():
    """§5 — không có đường 'sửa ca cho khớp kết quả'."""
    ca = [{"id": "a", "de": "đề A"}, {"id": "b", "de": "đề B"}]
    seal = seal_bo_ca(ca)
    kiem_bo_ca(seal, ca)

    ca[1] = {"id": "b", "de": "đề B đã sửa sau khi thấy đầu ra"}
    with pytest.raises(IntegrityError, match="BỘ CA ĐÃ ĐỔI"):
        kiem_bo_ca(seal, ca)


# ══ H · ARTIFACT HỎNG ⇒ READER ĐỎ, KHÔNG BỎ QUA ═══════════════════════════
def test_H_artifact_cut_lam_reader_NEM(tmp_path):
    f = tmp_path / "cut.json"
    f.write_text('{"artifact_schema_version": "1.0", "a": [1, 2', "utf-8")
    with pytest.raises(IntegrityError, match="HỎNG"):
        doc_artifact(f)


def test_H2_artifact_phien_ban_LA_bi_tu_choi(tmp_path):
    """§20 — reader phải từ chối định dạng không tương thích."""
    f = tmp_path / "moi.json"
    f.write_text(json.dumps({"artifact_schema_version": "9.0"}), "utf-8")
    with pytest.raises(IntegrityError, match="KHÔNG tương thích"):
        doc_artifact(f)


def test_H3_artifact_khong_khai_phien_ban_bi_tu_choi(tmp_path):
    f = tmp_path / "cu.json"
    f.write_text(json.dumps({"a": 1}), "utf-8")
    with pytest.raises(IntegrityError, match="không khai"):
        doc_artifact(f)


# ══ §12 · CỜ GIAI ĐOẠN KHÔNG ĐƯỢC RÚT THÀNH `correct` ═════════════════════
def test_executable_va_servable_KHONG_bi_gop():
    """Kết quả toán học ĐÚNG mà `servable=False` **không** là thành công sản
    phẩm — và cũng không phải lỗi mô hình."""
    oc = FakeOutcome(stage_reached="postconditions", executable=True,
                     servable=False, error_code="postcondition_violated",
                     details=["cần một `solid`"])
    c = co_giai_doan(oc, schema_ok=True)
    assert c["runtime_executable"] is True
    assert c["servable"] is False
    assert c["postconditions_pass"] is False
    assert c["grounding_pass"] is True and c["static_valid"] is True


def test_co_giai_doan_ca_di_tron_duong():
    c = co_giai_doan(FakeOutcome(), schema_ok=True)
    assert all(c[k] for k in ("schema_valid", "grounding_pass", "coverage_pass",
                              "static_valid", "runtime_executable",
                              "postconditions_pass", "servable"))


# ══ §16 · REPAIR ELIGIBILITY ĐỌC TỪ LUẬT SẢN PHẨM ═════════════════════════
def test_sua_duoc_doc_MA_LOI_chu_khong_khop_chuoi():
    """Probe §18 ghi: *"bộ đo chạy 2; LUẬT SẢN PHẨM cho 3"* — chênh lệch sinh
    ra vì bộ đo khớp chuỗi tiếng Việt trong thông báo lỗi."""
    ok, ly_do = sua_duoc(
        FakeOutcome(stage_reached="grounding", executable=False, servable=False,
                    error_code="input_not_grounded"), schema_ok=True)
    assert ok and "input_not_grounded" in ly_do

    ok2, ly_do2 = sua_duoc(
        FakeOutcome(stage_reached="postconditions", executable=True,
                    servable=False, error_code="postcondition_violated"),
        schema_ok=True)
    assert not ok2 and "NGOÀI vòng sửa" in ly_do2

    ok3, _ = sua_duoc(None, schema_ok=False)
    assert ok3, "lược đồ hỏng thì pipeline CÓ gửi ngược"


# ══ §22–§23 · TÓM TẮT DẪN XUẤT VÀ TỰ KIỂM ═════════════════════════════════
def _dung_run(tmp_path: Path, *, pha_summary: bool = False) -> Path:
    run = tmp_path / "run"
    (run / "cases").mkdir(parents=True)
    ghi_artifact(run / "manifest.json", {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION, "run_id": "r1",
        "seal": {"ids": ["a", "b"]}})
    for i, (lop, tok) in enumerate((("CORRECT_SERVABLE_RESULT", 100),
                                    ("SYSTEM_VERIFICATION_FAILURE", 50))):
        ten = "ab"[i]
        ghi_artifact(run / "cases" / ten / "final.json", {
            "artifact_schema_version": ARTIFACT_SCHEMA_VERSION, "id": ten,
            "phan_lop": lop,
            "goi_provider": {"analyze": 1, "synthesis": 1},
            "telemetry": {"tong": {"input_tokens": tok, "output_tokens": 10,
                                   "thought_tokens": 5, "total_tokens": tok + 15}}})
    tt = tom_tat_tu_artifact(run)
    if pha_summary:
        tt["APPLICATION_LLM_CALLS"] = 999          # con số "nhập tay"
    ghi_artifact(run / "summary.json", tt)
    return run


def test_tom_tat_DAN_tu_artifact_tren_dia(tmp_path):
    tt = tom_tat_tu_artifact(_dung_run(tmp_path))
    assert tt["CASES_TOTAL"] == 2 and tt["CASES_WITH_ARTIFACT"] == 2
    assert tt["APPLICATION_LLM_CALLS"] == 4
    assert tt["tokens"]["input_tokens"] == 150
    assert tt["SYSTEM_FAILURES"] == 1
    assert tt["CORRECT_SERVABLE_RESULT"] == 1


def test_tu_kiem_bat_duoc_so_NHAP_TAY(tmp_path):
    """§23 — chính là phép bắt 'ghi trượt đường dẫn / đối tượng còn sót / ghi
    dở / telemetry lệch'."""
    run = _dung_run(tmp_path, pha_summary=True)
    with pytest.raises(IntegrityError, match="APPLICATION_LLM_CALLS"):
        tu_kiem_tom_tat(run)


def test_tu_kiem_XANH_khi_bao_cao_trung_thuc(tmp_path):
    assert tu_kiem_tom_tat(_dung_run(tmp_path))["CASES_TOTAL"] == 2


def test_tu_kiem_bat_duoc_ca_bi_MAT_artifact(tmp_path):
    """Ghi trượt đường dẫn: summary nói 2 ca, trên đĩa còn 1."""
    run = _dung_run(tmp_path)
    (run / "cases" / "b" / "final.json").unlink()
    with pytest.raises(IntegrityError, match="CASES_WITH_ARTIFACT"):
        tu_kiem_tom_tat(run)


# ══ §7 · MỘT FILE KHÔNG ĐƯỢC VỪA LÀ ĐẦU VÀO VỪA LÀ ĐẦU RA ═════════════════
def test_doc_roi_GHI_LAI_cung_mot_duong_bi_tu_choi(tmp_path):
    """Hình dạng chính xác của sự cố ④: một glob nở ra hai đường và file thứ
    hai — vốn là đầu vào — trở thành đầu ra."""
    f = tmp_path / "a.json"
    ghi_artifact(f, {"artifact_schema_version": ARTIFACT_SCHEMA_VERSION, "v": 1})
    doc_artifact(f)
    with pytest.raises(IntegrityError, match="ĐÃ ĐƯỢC ĐỌC"):
        ghi_artifact(f, {"v": 2}, cho_de=True)
    assert doc_artifact(f)["v"] == 1


# ══ §25 · CHỨNG NHẬN BỘ ĐO — LẮP RÁP, KHÔNG PHẢI TỪNG MẢNH ════════════════
def test_chung_nhan_bo_do_PASS(tmp_path):
    """Năm kịch bản đi TRỌN vòng đời; chỉ provider là giả, route là THẬT."""
    import certify_acceptance_runner as cert

    ok, sai = cert.chung_nhan(tmp_path / "run")
    assert ok, sai


def test_chung_nhan_CO_RANG_khi_phan_loai_sai(tmp_path, monkeypatch):
    """Chứng nhận phải đỏ được. Tiêm: bộ phân loại gộp mọi thứ thành một lớp —
    đúng nết mà runner cũ có (`dap_so_khop: bool`)."""
    import certify_acceptance_runner as cert

    monkeypatch.setattr(cert, "phan_loai",
                        lambda *a, **k: "CORRECT_SERVABLE_RESULT")
    ok, sai = cert.chung_nhan(tmp_path / "run")
    assert not ok and len(sai) >= 3, sai


def test_chung_nhan_CO_RANG_khi_ket_qua_lay_tu_scene3d(tmp_path, monkeypatch):
    """Tiêm lại SỰ CỐ ③ vào chính đường ráp: trích kết quả từ `scene3d`.

    `duong_1_dung` phục vụ được nên `scene3d` CÓ tồn tại — nhưng nó chở nhãn
    hiển thị, không chở `{R, V}` của `final_memory`. Chứng nhận phải bắt được.
    """
    import certify_acceptance_runner as cert

    def tu_scene3d(outcome):
        env = getattr(outcome, "envelope", None) or {}
        canh = (env.get("scene3d") or {}).get("objects") or []
        return {"nguon": "envelope.scene3d",
                "dai_luong": {str(i): o.get("value")
                              for i, o in enumerate(canh)
                              if o.get("type") == "quantity"}}

    monkeypatch.setattr(cert, "trich_ket_qua", tu_scene3d)
    ok, sai = cert.chung_nhan(tmp_path / "run")
    assert not ok and any("đại lượng" in s for s in sai), sai


def test_chung_nhan_KHONG_chay_lai_duoc_len_thu_muc_cu(tmp_path):
    """§6/§19 — không resume ngầm, không đè."""
    import certify_acceptance_runner as cert

    cert.chung_nhan(tmp_path / "run")
    with pytest.raises(IntegrityError, match="ĐÃ TỒN TẠI"):
        cert.chung_nhan(tmp_path / "run")


def test_chung_nhan_ghi_du_artifact_de_REPLAY(tmp_path):
    """§4 — mỗi ca phải để lại đủ thứ cho một lượt replay tất định."""
    import certify_acceptance_runner as cert

    run = tmp_path / "run"
    cert.chung_nhan(run)
    for c in cert.CA:
        f = run / "cases" / c["id"] / "final.json"
        r = doc_artifact(f)
        assert r["request_contract"]["input_facts"], c["id"]
        assert r["request_contract"]["obligations"], c["id"]
        assert r["de"] and r["phan_lop"], c["id"]
        assert r["ket_qua"]["nguon"] == "outcome.final_memory", c["id"]
        assert _du_de_replay({**r, "chuong_trinh": r["chuong_trinh"] or {}})
