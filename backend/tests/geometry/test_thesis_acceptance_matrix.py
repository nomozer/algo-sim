# -*- coding: utf-8 -*-
"""`THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION` — kế hoạch đo phải KIỂM ĐƯỢC.

**0 lượt gọi model.**

Một kế hoạch đánh giá không kiểm được là một lời hứa: nó đúng đúng một lần, vào
hôm viết ra. Bộ test này đối chiếu **từng khẳng định** của kế hoạch với mã nguồn
và với artifact đang có.

⚠️ Nó cố ý kiểm CẢ HAI CHIỀU, và chiều thứ hai quan trọng hơn:
· thứ kế hoạch nói **đã sẵn sàng** thì phải thật sự chạy được;
· thứ kế hoạch nói **chưa có** thì phải thật sự VẮNG — vì một kế hoạch tự khen
  sẽ dẫn thẳng tới một lượt đo tiêu quota rồi mới phát hiện runner không tồn tại.

Nhóm `H` là **phép tiêm lỗi**: mỗi guard ở trên phải ĐỎ được khi bị phá. Guard
chưa từng đỏ là guard chưa được chứng minh (`ARCHITECTURE_MAP §8` #14).
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[3]
BACKEND = GOC / "backend"
SCRIPTS = BACKEND / "scripts"
RA = GOC / "docs" / "evaluation" / "geometry" / "thesis-final-acceptance"
CHINH_SACH = SCRIPTS / "policies" / "thesis_final_acceptance_policy.json"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import measurement_policy as MP  # noqa: E402
import thesis_acceptance_corpus as C  # noqa: E402
import thesis_acceptance_oracle as O  # noqa: E402
import thesis_final_acceptance_plan as P  # noqa: E402


@pytest.fixture(scope="module")
def nguong() -> dict:
    return MP.doc_chinh_sach(CHINH_SACH)[0]


@pytest.fixture(scope="module")
def gold() -> dict:
    p = RA / "GOLD_PREFLIGHT.json"
    assert p.exists(), "thiếu GOLD_PREFLIGHT.json — chạy plan script trước"
    return json.loads(p.read_text(encoding="utf-8"))


# ══ A · BỘ CA ═════════════════════════════════════════════════════════════
def test_A1_bo_ca_dung_kich_thuoc():
    assert len(C.CA_DUONG) == 7, "§6: POSITIVE_CASES_TARGET = 7, MAX = 8"
    assert len(C.CA_AM) == 2, "§6: NEGATIVE_CASES_TARGET = 2"


def test_A2_set_cover_phu_MOI_ho_trong_pham_vi():
    trong = [h for h, v in C.PHU_THEO_HO.items() if not v]
    assert not trong, f"họ không ca nào phủ: {trong}"


def test_A3_khong_ca_nao_THUA():
    """Chiều ngược: bỏ một ca đi thì phải MẤT ít nhất một họ. Một ca không phủ
    thêm gì là một lượt gọi model tiêu vô ích."""
    for ca in C.CA_DUONG:
        con_lai = {h for c in C.CA_DUONG if c["id"] != ca["id"]
                   for h in c["families"]}
        mat = set(ca["families"]) - con_lai
        assert mat, f"ca '{ca['id']}' không phủ riêng họ nào — thừa"


def test_A4_payload_gui_model_CHI_co_de_bai():
    """Gold program, oracle hay đáp số lọt vào prompt sẽ biến phép đo thành một
    phép đo dễ hơn hẳn — và con số vẫn ra, nên hỏng im lặng."""
    for ca in (*C.CA_DUONG, *C.CA_AM):
        pl = C.payload_gui_model(ca)
        assert set(pl) == {"problem_text"}, (ca["id"], sorted(pl))
        van = json.dumps(pl, ensure_ascii=False)
        for cam in ("gold_program", "oracle", "expected", "families",
                    "target_boundary", "witness", "construct_"):
            assert cam not in van, (ca["id"], cam)


def test_A5_de_bai_MOI__khong_trung_corpus_phat_trien():
    """Chấm trên bài đã dùng khi phát triển là chấm sai theo chiều LUÔN ĐẸP
    LÊN. So bằng băm, không bằng mắt."""
    import run_curved_acceptance as RCA

    cu = {hashlib.sha256(c["de"].encode("utf-8")).hexdigest()
          for c in RCA.CA}
    for p in (GOC / "docs" / "evaluation" / "geometry").rglob("*.json"):
        # Artifact CỦA CHÍNH bộ này không phải "corpus phát triển". Bỏ sót
        # điều đó thì guard tự bắt chính nó ngay lần chạy thứ hai — và một
        # guard luôn đỏ sẽ bị tắt, tức mất hẳn phép kiểm.
        if RA in p.parents:
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        # …và artifact DẪN XUẤT từ lượt đo ấy cũng vậy. Fixture hiển thị
        # (`build_product_ui_fixtures.py`) chở lại `problem_text` để gõ vào ô
        # nhập thật, nên nếu tính chúng là "corpus phát triển" thì guard kết
        # luận lượt đo cuối đã chấm trên bài cũ — sai, và sai theo hướng
        # nghiêm trọng nhất có thể.
        #
        # ⚠️ Loại trừ theo LỜI KHAI KIỂM ĐƯỢC, không theo danh sách đường dẫn:
        # danh sách đường dẫn mục nào cũng phải nhớ thêm tay, còn lời khai đi
        # theo file. Và lời khai chỉ có giá trị khi nó trỏ tới một artifact CÓ
        # THẬT dưới `RA` — một chuỗi đặt bừa không mua được quyền miễn trừ.
        if _dan_xuat_tu_luot_do(d):
            continue
        for t in _moi_de(d):
            cu.add(hashlib.sha256(t.encode("utf-8")).hexdigest())
    for ca in (*C.CA_DUONG, *C.CA_AM):
        b = hashlib.sha256(ca["problem_text"].encode("utf-8")).hexdigest()
        assert b not in cu, f"đề của '{ca['id']}' đã xuất hiện trong artifact cũ"


def test_A5b_quyen_mien_tru_KHONG_mua_duoc_bang_mot_chuoi_dat_bua():
    """Chiều ngược của A5. Không có phép tiêm này thì lối miễn trừ mới trở
    thành một cửa sau: khai một `source_artifact_path` bất kỳ là thoát guard."""
    that = {"source_artifact_path":
            _RA_TUONG_DOI + "thesis-final-20260908T160224Z/stage_a_first_attempt.json"}
    assert _dan_xuat_tu_luot_do(that), "artifact CÓ THẬT phải được miễn trừ"

    for bua in (
        {"source_artifact_path": _RA_TUONG_DOI + "khong-he-ton-tai.json"},
        {"source_artifact_path": "docs/evaluation/geometry/clean-baseline-v2/probe.json"},
        {"source_artifact_path": "/etc/passwd"},
        {"nguon": _RA_TUONG_DOI + "thesis-final-20260908T160224Z/manifest.json"},
        {},
    ):
        assert not _dan_xuat_tu_luot_do(bua), f"lời khai bịa vẫn thoát: {bua}"


def test_A5c_fixture_hien_thi_thuc_su_duoc_mien_tru():
    """Và lối miễn trừ phải trúng ĐÚNG thứ nó sinh ra để miễn trừ — không thì
    A5 lại đỏ ở lần chạy sau mà không ai nhớ vì sao."""
    thu_muc = (GOC / "docs" / "evaluation" / "geometry"
               / "product-ui-result-rendering" / "fixtures")
    if not thu_muc.is_dir():
        pytest.skip("chưa sinh fixture hiển thị")
    fx = sorted(thu_muc.glob("*.json"))
    assert fx, "thư mục fixture rỗng"
    for p in fx:
        d = json.loads(p.read_text(encoding="utf-8"))
        assert _dan_xuat_tu_luot_do(d), p.name


#: `RA` viết theo lối tương đối gốc kho — đúng lối fixture ghi `source_artifact_path`.
_RA_TUONG_DOI = "docs/evaluation/geometry/thesis-final-acceptance/"


def _moi_gia_tri(o, ten, sau=0):
    """Mọi giá trị chuỗi nằm dưới khoá `ten`, đào tối đa 6 tầng."""
    if sau > 5:
        return
    if isinstance(o, dict):
        for k, v in o.items():
            if k == ten and isinstance(v, str):
                yield v
            else:
                yield from _moi_gia_tri(v, ten, sau + 1)
    elif isinstance(o, list):
        for v in o[:80]:
            yield from _moi_gia_tri(v, ten, sau + 1)


def _dan_xuat_tu_luot_do(d) -> bool:
    """File có TỰ KHAI nó dẫn xuất từ lượt đo cuối không — và lời khai ấy có
    kiểm được không.

    Chỉ khai thôi thì chưa đủ: đường dẫn phải trỏ tới một artifact **có thật**
    dưới `RA`. Nếu không, bất cứ file nào cũng mua được quyền miễn trừ bằng một
    chuỗi đặt bừa, và guard A5 hết tác dụng theo đúng hướng nó tồn tại để chặn.
    """
    for duong in _moi_gia_tri(d, "source_artifact_path"):
        if duong.startswith(_RA_TUONG_DOI) and (GOC / duong).is_file():
            return True
    return False


def _moi_de(o, sau=0):
    if sau > 5:
        return
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("de", "problem_text") and isinstance(v, str):
                yield v
            else:
                yield from _moi_de(v, sau + 1)
    elif isinstance(o, list):
        for v in o[:80]:
            yield from _moi_de(v, sau + 1)


def test_A6_ca_am_KHONG_co_gold_program():
    """Một ca âm có gold program là một ca âm phục vụ được — tức không còn âm."""
    for ca in C.CA_AM:
        assert "gold_program" not in ca, ca["id"]
        assert "expected" not in ca, ca["id"]


# ══ B · ORACLE ĐỘC LẬP ════════════════════════════════════════════════════
def test_B1_oracle_KHONG_import_gi_tu_app():
    """Oracle gọi lại kernel thì nó chỉ chứng minh kernel nhất quán với chính
    mình. Quét AST, không quét chuỗi — một `importlib` sẽ lọt qua grep."""
    cay = ast.parse((SCRIPTS / "thesis_acceptance_oracle.py")
                    .read_text(encoding="utf-8"))
    xau = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            xau += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            xau.append(n.module or "")
    for m in xau:
        for cam in O.ORACLE_KHONG_DUOC_IMPORT:
            assert not (m == cam or m.startswith(cam + ".")), \
                f"oracle import '{m}' — mất tính độc lập"


def test_B2_oracle_tu_dan_lai_khop_gia_tri_ghi_trong_corpus(gold):
    """Một `oracle_value` chép sẵn cũng chỉ là một con số ai đó gõ vào."""
    lech = {k: v for k, v in gold["oracle_tu_dan_lai"].items() if not v["khop"]}
    assert not lech, lech


def test_B3_moi_dap_so_mong_doi_doc_duoc_bang_NGU_PHAP_oracle():
    for ca in C.CA_DUONG:
        for ten, m in ca["expected"].items():
            gt = O.doc_chuoi_hien_thi(m["display"])
            assert abs(gt - m["oracle_value"]) <= 1e-8 * max(
                abs(m["oracle_value"]), 1.0), (ca["id"], ten)


def test_B4_ngu_phap_oracle_TU_CHOI_dang_la():
    """Bộ phân tích nhận nhiều hơn thứ nó được kiểm sẽ đọc sai lặng lẽ."""
    for xau in ("1+√2", "√(2+3)", "2πe", "abc", "", "π√"):
        with pytest.raises(O.OracleError):
            O.doc_chuoi_hien_thi(xau)


def test_B5_oracle_lay_mau_TU_KIEM_diem_nam_tren_mat_phang():
    """Guard nội bộ của oracle phải đỏ khi chính đại số của nó sai."""
    with pytest.raises(O.OracleError):
        O.elip_lay_mau_tru(tam_day=(0, 0, 0), tam_day_kia=(0, 0, 24),
                           ban_kinh=5, mat_phang=(2, 0, 0, 12), n=64)


# ══ C · CHÍNH SÁCH ════════════════════════════════════════════════════════
def test_C1_policy_du_truong_bat_buoc(nguong):
    import freeze_evaluation_candidate as F

    he, _n = F.measured_system_hash()
    loi = MP.kiem_chinh_sach(nguong, candidate_hash=he,
                             pool_hash=C.CORPUS_HASH)
    assert not loi, loi


def test_C2_policy_tro_dung_corpus_va_candidate(nguong):
    import freeze_evaluation_candidate as F

    assert nguong["pool_hash"] == C.CORPUS_HASH
    assert nguong["expected_results_hash"] == C.EXPECTED_RESULTS_HASH
    assert nguong["candidate_hash"] == F.measured_system_hash()[0]


def test_C3_ngan_sach_DAN_tu_call_graph(nguong):
    a = MP.derive_application_call_budget(
        selected_cases=9, analyze_calls_per_case=1,
        synthesis_attempt_limit=1, calls_per_attempt=1)
    # ⚠️ Chặng B nay TIẾP TỤC, không chạy lại: 0 analyze, 1 lượt sửa
    # (amendment 1.1.0, `THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT`).
    b = MP.derive_application_call_budget(
        selected_cases=7, analyze_calls_per_case=0,
        synthesis_attempt_limit=1, calls_per_attempt=1)
    assert b == 7
    assert nguong["budget"]["EXPECTED_LOGICAL_CALLS"] == a
    assert nguong["budget"]["MAX_LOGICAL_CALLS"] == a + b == 25


def test_C4_metric_hanh_vi_KHONG_co_nguong(nguong):
    """Đặt một ngưỡng học thuật mà khoá luận chưa quy định là bịa ra một tiêu
    chuẩn. Guard này giữ chỗ ấy trống."""
    bh = nguong["behavioural_metrics"]
    assert bh["no_threshold_by_design"] is True
    assert bh["report_with_denominator"] is True
    for m in bh["metrics"]:
        assert not isinstance(bh.get(m), (int, float)), \
            f"'{m}' bị gán một ngưỡng — nhóm này chỉ được MÔ TẢ"


def test_C5_nhom_bat_buoc_toan_so_KHONG(nguong):
    bb = nguong["mandatory_correctness_and_safety"]
    for k in ("SILENT_WRONG_ANSWER_COUNT", "SERVED_EXACT_MISMATCH_COUNT",
              "SERVED_SOURCE_INVARIANT_VIOLATION_COUNT",
              "SERVED_SCENE3D_MISMATCH_COUNT", "UNHANDLED_EXCEPTION_COUNT"):
        assert bb[k] == 0, k
    assert bb["GOLD_PREFLIGHT_PASS_RATE"] == 1.0
    assert bb["NEGATIVE_FAIL_CLOSED_RATE"] == 1.0


def test_C6_khai_dung_LOAI_phep_do(nguong):
    ec = nguong["evaluation_class"]
    assert ec["EVALUATION_CLASS"] == "FROZEN_FINAL_DEVELOPMENT_BENCHMARK"
    assert ec["HELD_OUT_CLAIM"] == "NO"
    assert ec["OPERATOR_INDEPENDENCE_REQUIRED"] == "NO"


def test_C7_product_promotion_TU_KHAI_la_khong_the_dat(nguong):
    """Một lượt đo xanh KHÔNG phải lời cho phép bật nút. Policy phải nói điều
    ấy TRƯỚC, không phải sau khi thấy kết quả."""
    pp = nguong["product_promotion"]
    assert pp["requires_stability_measured"] is True
    assert "PRODUCT_PROMOTION_ELIGIBLE = NO" in pp["canh_bao"]


def test_C8_dung_LAI_rubric_khong_de_ban_thu_hai(nguong):
    assert nguong["attribution_policy"]["rubric_id"] == "CURVED_V3_ATTRIBUTION"
    assert MP.RUBRIC_QUY_TRACH_NHIEM.exists()


# ══ D · GOLD PREFLIGHT ════════════════════════════════════════════════════
def test_D1_gold_preflight_dat_TOAN_BO(gold):
    tk = gold["tong_ket"]
    n = len(C.CA_DUONG)
    for k in ("GOLD_POSITIVE_SERVABLE", "GOLD_EXACT_MATCH",
              "GOLD_ORACLE_AGREEMENT", "GOLD_POSTCONDITIONS", "GOLD_SCENE3D"):
        assert tk[k] == f"{n}/{n}", (k, tk[k])
    assert tk["GOLD_WEAK_KINDS"] == 0
    assert gold["GOLD_PREFLIGHT_PASS"] is True


def test_D2_ba_cot_DOC_LAP_deu_co_mat_rieng(gold):
    """`EXACT` · `SCENE3D` · `SERVABLE` phải là ba trường RIÊNG trong artifact.
    Gộp bất kỳ cặp nào là xoá đúng thông tin đã cứu `c7a` khỏi bị quy sai."""
    for c in gold["cases"]:
        for k in ("EXACT_ANSWER_MATCH", "SCENE3D_PASS", "servable",
                  "ORACLE_NUMERIC_AGREEMENT"):
            assert k in c, (c["id"], k)


def test_D3_gold_chay_LAI_van_ra_dung_the(gold):
    """Tất định: chạy lại phải cho cùng kết quả. Không thì mọi con số sau đó
    nói về một lượt chạy cụ thể chứ không về hệ."""
    lai = {r["id"]: r for r in P.gold_preflight()[1]["cases"]}
    for c in gold["cases"]:
        r = lai[c["id"]]
        assert (r["servable"], r["EXACT_ANSWER_MATCH"], r["SCENE3D_PASS"]) == \
            (c["servable"], c["EXACT_ANSWER_MATCH"], c["SCENE3D_PASS"]), c["id"]


def test_D4_moi_ca_duong_dat_dung_NGHIA_VU_de_khai(gold):
    theo_id = {c["id"]: c for c in C.CA_DUONG}
    for r in gold["cases"]:
        can = {o["params"]["witness"]
               for o in theo_id[r["id"]]["request_contract_gold"]["obligations"]}
        assert can <= set(r["final_memory"]), (r["id"], can,
                                               sorted(r["final_memory"]))


# ══ E · CA ÂM ═════════════════════════════════════════════════════════════
def test_E1_absence_proof_dat_ca_hai(gold):
    for c in gold["ca_am"]["cases"]:
        assert c["ABSENCE_PROOF_PASS"], (c["id"], c["absence_proof"])


def test_E2_scorer_CHAP_NHAN_khai_bao_ranh_gioi(gold):
    for c in gold["ca_am"]["cases"]:
        assert c["scorer_chap_nhan_khai_bao"], (c["id"], c["scorer_loi"])


def test_E3_ranh_gioi_khai_dung_LOP_bang_chung(gold, nguong):
    """Ranh giới chứng minh bằng VẮNG MẶT, không bằng một mã lỗi mang tên họ
    hình — hệ không có mã như thế, và hứa có là hứa quá."""
    assert gold["ca_am"]["boundary_evidence_class"] == "BOUNDARY_BY_ABSENCE_PROOF"
    nt = nguong["negative_thresholds"]
    assert nt["boundary_evidence_class"] == "BOUNDARY_BY_ABSENCE_PROOF"
    assert nt["target_boundary_demonstrated_expected"] == "MEASURED_NOT_REQUIRED"
    assert nt["correct_fail_closed"] == "2/2"


def test_E4_hai_ho_ngoai_pham_vi_dung_la_hai_ho_ma_tran_khai():
    from app.simulation.product_capability import NANG_LUC_SAN_PHAM

    khai = {c["target_boundary"] for c in C.CA_AM}
    assert khai == {"solid_of_revolution_general", "composite_boolean"}
    assert NANG_LUC_SAN_PHAM["solid_of_revolution"].trang_thai == "unsupported"
    assert NANG_LUC_SAN_PHAM["composite_subtractive"].trang_thai == "unsupported"


# ══ F · BỘ CHẤM ═══════════════════════════════════════════════════════════
def test_F1_moi_lop_phan_quyet_co_it_nhat_mot_fixture(gold):
    from acceptance_verdict import LOP_PHAN_QUYET

    sc = gold["scorer"]
    assert sc["THIEU_FIXTURE"] == [], sc["THIEU_FIXTURE"]
    assert set(sc["co_fixture"]) == set(LOP_PHAN_QUYET)


def test_F2_it_nhat_nam_lop_co_fixture_DUONG_CHAY_THAT(gold):
    """`SYNTHETIC_OUTCOME` chỉ chứng minh bộ chấm đọc đúng một trường; nó không
    chứng minh hệ có bao giờ phát ra tình huống ấy. Phân biệt hai mức, và đòi
    mức mạnh cho những lớp quyết định trách nhiệm."""
    sc = gold["scorer"]
    assert len(sc["REAL_PATH"]) >= 5, sc["REAL_PATH"]
    for lop in ("CORRECT_SERVABLE_RESULT", "SYSTEM_COVERAGE_FAILURE",
                "ATTRIBUTION_UNRESOLVED", "MODEL_GROUNDING_FAILURE"):
        assert lop in sc["REAL_PATH"], lop


def test_F3_hai_lop_NGOAI_scorer_duoc_khai_ro(gold, nguong):
    """`MODEL_ANALYZE_FAILURE` và `SYSTEM_SCENE3D_FAILURE` KHÔNG sinh ra được
    từ `phan_loai`. Im lặng về điều đó là để runner tự phát minh cách đếm."""
    ngoai = gold["scorer"]["lop_ngoai_scorer_canonical"]
    assert set(ngoai) == {"MODEL_ANALYZE_FAILURE", "SYSTEM_SCENE3D_FAILURE"}
    assert set(nguong["error_accounting"]["khong_co_trong_scorer_canonical"]) \
        == set(ngoai)


# ══ G · RUNNER · DANH TÍNH · ARTIFACT ═════════════════════════════════════
def test_G1_runner_readiness_DO_tren_ma_nguon():
    ok, rn = P.runner_readiness()
    assert rn["FINAL_ACCEPTANCE_RUNNER_READY"] in ("YES", "NO")
    assert (rn["NEXT_ACTION"] == "THESIS_FINAL_ACCEPTANCE_EXECUTION") is ok
    assert (not rn["KHOANG_TRONG"]) is ok


def test_G2_runner_cuoi_KHONG_cham_bo_do_V3():
    """⚠️ ĐỔI CHỦ THỂ 2026-09-08. Bản trước hỏi *"guard corpus của V3 có bác bộ
    ca khoá luận không"* và đo ra KHÔNG — `kiem_bo_ca_la_pool_v3` là một danh
    sách CẤM, còn `main_async` thì không có đường nào nhận bộ ca mới.

    Phát hiện ấy giữ nguyên trong báo cáo wave trước; nó không còn là câu hỏi
    vận hành vì lượt cuối nay có entrypoint RIÊNG. Câu hỏi thay thế: entrypoint
    ấy có sạch dấu vết V3 không — đọc AST, không quét chuỗi.
    """
    import certify_thesis_final_acceptance as CT
    import run_thesis_final_acceptance as RT

    src = (GOC / RT.RUNNER_ENTRYPOINT).read_text(encoding="utf-8")
    assert CT._dau_vet_v3(src) == [], "runner cuối còn chạm bộ đo V3"
    _ok, rn = P.runner_readiness()
    assert rn["runner"] == RT.RUNNER_ENTRYPOINT


def test_G3_identity_lock_ghi_du_truong():
    d = json.loads((RA / "IDENTITY_LOCK.json").read_text(encoding="utf-8"))
    for k in ("EVALUATION_VERSION", "EVALUATION_CLASS", "HELD_OUT_CLAIM",
              "CREATED_BEFORE_LIVE_RUN", "CANDIDATE_HASH", "CACHE_VERSION",
              "PROMPT_HASH", "GRAMMAR_CARD_HASH", "ANALYZE_SCHEMA_HASH",
              "SYNTHESIS_SCHEMA_HASH", "CAPABILITY_HASH", "SCORER_HASH",
              "POLICY_HASH", "CORPUS_HASH", "EXPECTED_RESULTS_HASH",
              "GOLD_PREFLIGHT_HASH", "MODEL_PROVIDER", "MODEL_NAME",
              "MODEL_VERSION_OR_SNAPSHOT", "TEMPERATURE", "TOP_P",
              "MAX_OUTPUT_TOKENS", "REPAIR_LIMIT_FOR_THIS_RUN",
              "LOGICAL_CALL_BUDGET", "PHYSICAL_ATTEMPT_BUDGET", "TOKEN_BUDGET"):
        assert k in d, k
    assert d["CREATED_BEFORE_LIVE_RUN"] is True
    # ⚠️ Bản trước đòi `RUNNER_HASH is None` — đúng khi runner CHƯA tồn tại.
    # Nay nó tồn tại và đã chứng nhận, nên khoá phải mang băm THẬT và
    # `LOCK_STATE` phải lật. Một khoá vẫn `None` sau khi runner xong nghĩa là
    # bước `--lock-runner` chưa chạy.
    import run_thesis_final_acceptance as RT

    assert d["RUNNER_HASH"] == RT.bam_runner()["RUNNER_HASH"]
    assert d["RUNNER_ENTRYPOINT"] == RT.RUNNER_ENTRYPOINT
    assert d["LOCK_STATE"] == "LOCKED_READY_FOR_FINAL_EXECUTION"
    # Vòng danh tính bị cắt bằng TẬP FILE: không artifact `.json` nào nằm
    # trong băm runner, nên khoá hai lần cho cùng một băm.
    assert not any(t.endswith(".json") for t in
                   [d["RUNNER_ENTRYPOINT"], *d["RUNNER_MODULE_HASHES"]])


def test_G3b_do_danh_tinh_chay_duoc_tren_CA_HAI_trang_thai_cay(monkeypatch):
    """⚠️ Hồi quy cho một lỗi ẩn sau `or` đoản mạch.

    `do_danh_tinh` từng ghép `dirty["ban_trong_yeu"] or dirty["ban_khac"]`, mà
    `ban_khac` KHÔNG tồn tại (khoá thật là `ban_khong_lien_quan`). Trên cây BẨN
    vế trái luôn truthy nên vế phải không bao giờ chạy — lỗi ẩn suốt quá trình
    dựng, rồi nổ `KeyError` đúng lượt chạy trên cây SẠCH, tức đúng lượt duy
    nhất mà artifact được sinh ra để dùng thật.

    Nên test này ép **cả hai** nhánh, không chỉ nhánh đang gặp.
    """
    import acceptance_integrity as AI

    for gia in ({"sach": True, "duong_ban": [], "ban_trong_yeu": [],
                 "ban_khong_lien_quan": []},
                {"sach": False, "duong_ban": ["x"], "ban_trong_yeu": [],
                 "ban_khong_lien_quan": ["x"]},
                {"sach": False, "duong_ban": ["backend/app/y"],
                 "ban_trong_yeu": ["backend/app/y"],
                 "ban_khong_lien_quan": []}):
        monkeypatch.setattr(AI, "phan_loai_dirty", lambda g=gia: g)
        d = P.do_danh_tinh()
        assert d["WORKING_TREE"] == ("SACH" if gia["sach"] else "DIRTY")


def test_G4_tham_so_giai_ma_CO_KIEU_khong_phai_van_xuoi(nguong):
    d = json.loads((RA / "IDENTITY_LOCK.json").read_text(encoding="utf-8"))
    ts = {"temperature": d["TEMPERATURE"], "top_p": d["TOP_P"],
          "max_output_tokens": d["MAX_OUTPUT_TOKENS"]}
    assert not MP.kiem_tham_so_giai_ma(ts, nguong)
    assert d["MODEL_VERSION_OR_SNAPSHOT"] is None
    assert d["MODEL_REPRODUCIBILITY"] == "LIMITED_ACCEPTED"


def test_G5_artifact_tren_dia_KHOP_ban_sinh_lai():
    """Artifact trôi khỏi mã sinh ra nó là im lặng — tới lần chạy sau mới bị
    ghi đè, và khi ấy không ai biết bản nào đúng."""
    assert json.loads((RA / "CORPUS.json").read_text(encoding="utf-8")) == \
        C.corpus_json()
    assert json.loads(
        (RA / "EXPECTED_RESULTS.json").read_text(encoding="utf-8")) == \
        C.expected_results_json()


def test_G6_EVALUATION_POLICY_khop_chinh_sach_nguon(nguong):
    """Hai bản sao, khoá bằng băm CHÍNH TẮC — cùng khuôn `test_schema_sync`."""
    ban = json.loads((RA / "EVALUATION_POLICY.json").read_text(encoding="utf-8"))
    assert MP.bam_chinh_tac(ban) == MP.bam_chinh_tac(nguong)


def test_G7_bang_chung_lich_su_khong_hang_nao_doi_CHAY_LAI():
    d = json.loads(
        (RA / "EVIDENCE_CLASSIFICATION.json").read_text(encoding="utf-8"))
    assert set(d["TONG_KET_THEO_LOP"]) <= set(P._LOP_BANG_CHUNG)
    assert all(a["REQUIRES_RERUN"] != "YES" for a in d["artifacts"])
    assert all(a["CANDIDATE"] is None or
               all(c in "0123456789abcdef" for c in a["CANDIDATE"])
               for a in d["artifacts"]), "cột CANDIDATE lẫn một thứ không phải băm"


def test_G8_ma_tran_tuyen_bo_du_cot_va_du_RQ():
    d = json.loads((RA / "CLAIMS_MATRIX.json").read_text(encoding="utf-8"))
    assert d["THIEU_COT"] == []
    assert d["CLAIMS_TOTAL"] == 9
    assert len(d["RQ_MAPPING"]) == 5
    phu = {c for v in d["RQ_MAPPING"].values() for c in v}
    assert phu == {c["CLAIM_ID"] for c in d["claims"]}, \
        "có tuyên bố không thuộc câu hỏi nghiên cứu nào"
    for c in d["claims"]:
        assert c["LIMITATION"].strip(), c["CLAIM_ID"]
        assert c["SOURCE_HASHES"] is not None


def test_G9_ma_tran_nang_luc_phu_het_12_ho():
    d = json.loads((RA / "CAPABILITY_MATRIX.json").read_text(encoding="utf-8"))
    assert len(d["families"]) == 12
    assert d["HO_KHONG_DUOC_PHU"] == []
    assert d["FEATURE_SCOPE_COMPLETE"] == "YES"
    for h in d["families"]:
        assert h["STABILITY_AFTER_FINAL_RUN"] == "NOT_MEASURED", h["FAMILY"]


# ══ H · TIÊM LỖI — mỗi guard phải ĐỎ được ═════════════════════════════════
def test_H1_bo_mot_ho_khoi_corpus_lam_DO_set_cover(monkeypatch):
    it = [c for c in C.CA_DUONG if c["id"] != C.CA_DUONG[-1]["id"]]
    monkeypatch.setattr(C, "CA_DUONG", it)
    phu = {h: [c["id"] for c in it if h in c["families"]]
           for h in C.HO_TRONG_PHAM_VI}
    assert [h for h, v in phu.items() if not v], \
        "bỏ một ca mà không họ nào trống ⇒ test_A2 đang xanh vì lý do khác"


def test_H2_doi_mot_chu_trong_dap_so_lam_DO_gold():
    ca = copy.deepcopy(C.theo_id("p3_mat_cau_va_thiet_dien_tron"))
    ca["expected"]["V"]["display"] = "4501π"
    r = P._chay_gold(ca)
    assert r["servable"] is True
    assert r["EXACT_ANSWER_MATCH"] is False, \
        "đổi đáp số mong đợi mà vẫn khớp ⇒ phép so không ăn"


def test_H3_doi_ORACLE_lam_DO_cot_so_ma_KHONG_dong_cot_chuoi():
    """Hai cột phải hỏng ĐỘC LẬP — đó là toàn bộ lý do có hai cột."""
    ca = copy.deepcopy(C.theo_id("p5_hinh_non_the_tich_va_xung_quanh"))
    ca["expected"]["V"]["oracle_value"] = 999.0
    r = P._chay_gold(ca)
    assert r["EXACT_ANSWER_MATCH"] is True
    assert r["ORACLE_NUMERIC_AGREEMENT"] is False


def test_H4_ha_dung_sai_ve_KHONG_lam_DO_ca_lay_mau():
    ca = copy.deepcopy(C.theo_id("p6_thiet_dien_elip_cua_hinh_tru"))
    ca["expected"]["S_E"]["oracle_method"] = "CLOSED_FORM"   # dung sai 1e-12
    r = P._chay_gold(ca)
    assert r["ORACLE_NUMERIC_AGREEMENT"] is False, \
        "oracle LẤY MẪU khớp tới 1e-12 ⇒ nó không thật sự lấy mẫu"


def test_H5_oracle_import_app_lam_DO_guard_doc_lap(tmp_path):
    gia = tmp_path / "oracle_gia.py"
    gia.write_text("from app.simulation.geometry import radical\n",
                   encoding="utf-8")
    cay = ast.parse(gia.read_text(encoding="utf-8"))
    xau = [n.module for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)]
    assert any(m.startswith("app") for m in xau if m), \
        "phép tiêm không ăn ⇒ test_B1 chưa chứng minh được gì"


def test_H6_go_mot_lop_khoi_taxonomy_lam_DO_chung_nhan_bo_cham(monkeypatch):
    import acceptance_verdict as AV

    monkeypatch.setattr(AV, "LOP_PHAN_QUYET",
                        AV.LOP_PHAN_QUYET + ("LOP_BIA_RA",))
    ok, sc = P.scorer_preflight()
    assert not ok and sc["THIEU_FIXTURE"] == ["LOP_BIA_RA"]


def test_H7_go_mot_nhan_chung_nhan_lam_DO_readiness(monkeypatch):
    """Chiều NGƯỢC của G1: readiness `YES` phải MẤT khi chứng nhận thiếu một
    nhãn. Không có phép tiêm này thì `YES` có thể đang đúng vì một lý do cố
    định — ví dụ vì hàm chưa bao giờ đọc tới chứng nhận."""
    goc = P.runner_readiness
    _ok, rn = goc()
    assert rn["FINAL_ACCEPTANCE_RUNNER_READY"] == "YES"

    import json as _json

    that = _json.loads
    xau = dict(rn["CHUNG_NHAN_NHAN"])
    xau["FIXED_CORPUS_LOADER"] = False

    def _doc(txt, *a, **kw):
        d = that(txt, *a, **kw)
        if isinstance(d, dict) and "nhan" in d and "wave" in d:
            d = {**d, "nhan": xau}
        return d

    monkeypatch.setattr(_json, "loads", _doc)
    ok2, rn2 = goc()
    assert not ok2
    assert rn2["FINAL_ACCEPTANCE_RUNNER_READY"] == "NO"
    assert rn2["CHUNG_NHAN_THIEU"] == ["FIXED_CORPUS_LOADER"]


def test_H8_them_gold_program_cho_ca_am_lam_DO_guard():
    xau = {**copy.deepcopy(C.CA_AM[0]), "gold_program": {"title": "x"}}
    assert "gold_program" in xau, \
        "phép tiêm không ăn ⇒ test_A6 chưa chứng minh được gì"


def test_H9_policy_tro_candidate_KHAC_lam_DO_kiem_chinh_sach(nguong):
    xau = {**nguong, "candidate_hash": "0" * 64}
    loi = MP.kiem_chinh_sach(xau, candidate_hash="f" * 64,
                             pool_hash=C.CORPUS_HASH)
    assert any("candidate" in l for l in loi), loi
